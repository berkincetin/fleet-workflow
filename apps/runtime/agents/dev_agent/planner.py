"""Ticket -> plan (task 5.5, dept scenario 03 "plan" step, TRD §4.3 reasoning
tier — plan quality is a judgment/generation call-site per CLAUDE.md rule 10).

The model answers with one JSON object describing the change it proposes:
branch name suffix, PR title/body, the files it would touch, and a rough
diff-size estimate. agents.dev_agent.guardrails checks target_paths/
diff_line_estimate against the protected-paths blocklist and diff cap; this
module only parses the model's structured proposal, same code-fence-stripping
defense as agents.analytics.sql_generator (the same class of model behavior
was caught live there).
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Protocol

_SYSTEM_PROMPT = """You are a software engineering planning assistant. Given a Jira ticket, \
propose a minimal, reviewable change that resolves it.

Respond with exactly one JSON object and nothing else — no markdown code fences, no commentary:
{
  "branch_suffix": "<short-kebab-case-slug, no 'agent/' prefix>",
  "pr_title": "<concise PR title>",
  "pr_body": "<PR description, reference the ticket key>",
  "target_paths": ["<file path the change would touch>", ...],
  "diff_line_estimate": <integer, rough estimated lines changed>
}
"""

_CODE_FENCE_RE = re.compile(r"^```(?:json)?\s*(.*?)\s*```$", re.DOTALL)


def _strip_code_fence(text: str) -> str:
    match = _CODE_FENCE_RE.match(text.strip())
    return match.group(1) if match else text


class PlanParseError(Exception):
    """The model's plan response was malformed or missing a required field."""


class ReasoningClient(Protocol):
    async def reasoning(self, messages: list[dict[str, Any]], **kwargs: Any) -> Any: ...


@dataclass(frozen=True)
class DevAgentPlan:
    branch_suffix: str
    pr_title: str
    pr_body: str
    target_paths: list[str]
    diff_line_estimate: int


_REQUIRED_FIELDS = ("branch_suffix", "pr_title", "pr_body", "target_paths", "diff_line_estimate")


async def plan_ticket(
    *,
    ticket: dict[str, Any],
    llm_client: ReasoningClient,
    sensitivity: str = "internal",
    **meta: Any,
) -> DevAgentPlan:
    messages = [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"Ticket {ticket.get('key', '?')}: {ticket.get('summary', '')}",
        },
    ]
    response = await llm_client.reasoning(messages, sensitivity=sensitivity, **meta)

    try:
        parsed = json.loads(_strip_code_fence(response.content))
    except json.JSONDecodeError as exc:
        raise PlanParseError(f"model did not return valid JSON: {response.content!r}") from exc

    missing = [f for f in _REQUIRED_FIELDS if f not in parsed]
    if missing:
        raise PlanParseError(f"plan response missing field(s): {missing}")

    return DevAgentPlan(
        branch_suffix=str(parsed["branch_suffix"]),
        pr_title=str(parsed["pr_title"]),
        pr_body=str(parsed["pr_body"]),
        target_paths=[str(p) for p in parsed["target_paths"]],
        diff_line_estimate=int(parsed["diff_line_estimate"]),
    )
