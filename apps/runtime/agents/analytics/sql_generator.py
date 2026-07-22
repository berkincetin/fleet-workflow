"""NL question -> SQL (task 5.2, dept scenario 02 "SQL gen" call-site, TRD
§4.3 reasoning tier).

The model is instructed to answer with exactly one JSON object of shape
{"sql": "<SELECT ...>"} or {"clarify": "<question>"} — never both, never
neither — so an ambiguous request produces one clarifying question instead of
a guessed query (the department scenario's explicit AC). Table-allowlist and
DML enforcement happen downstream in fleet_mcp.servers.pg_ro; this module's
only guardrail responsibility is refusing to silently guess.
"""

from __future__ import annotations

import json
import re
from typing import Any, Protocol

from agents.analytics.semantic_layer import SemanticLayer

_SYSTEM_PROMPT_TEMPLATE = """You translate natural-language business questions into read-only \
PostgreSQL SELECT queries over the views described below. Only use these views and columns \
— never invent a table or column name.

{glossary}

Respond with exactly one JSON object and nothing else — no markdown code fences, no commentary:
- If the question is answerable: {{"sql": "SELECT ..."}}
- If the question is ambiguous or missing information you need to write a correct query: \
{{"clarify": "<one specific clarifying question>"}}
"""

_CODE_FENCE_RE = re.compile(r"^```(?:json)?\s*(.*?)\s*```$", re.DOTALL)


def _strip_code_fence(text: str) -> str:
    """Some models wrap JSON in a ```json ... ``` fence despite being told not
    to; strip it before parsing rather than failing the whole eval case on a
    cosmetic formatting choice (caught live: make eval AGENT=analytics failed
    on every case until this was added)."""
    match = _CODE_FENCE_RE.match(text.strip())
    return match.group(1) if match else text


class ClarificationNeeded(Exception):
    """The model needs one clarifying question before it can write SQL."""


class ReasoningClient(Protocol):
    async def reasoning(self, messages: list[dict[str, Any]], **kwargs: Any) -> Any: ...


def _build_system_prompt(semantic_layer: SemanticLayer) -> str:
    return _SYSTEM_PROMPT_TEMPLATE.format(glossary=semantic_layer.describe())


async def generate_sql(
    *,
    question: str,
    semantic_layer: SemanticLayer,
    llm_client: ReasoningClient,
    sensitivity: str = "internal",
    **meta: Any,
) -> str:
    """Return a SELECT statement, or raise ClarificationNeeded/ValueError."""
    messages = [
        {"role": "system", "content": _build_system_prompt(semantic_layer)},
        {"role": "user", "content": question},
    ]
    response = await llm_client.reasoning(messages, sensitivity=sensitivity, **meta)

    try:
        parsed = json.loads(_strip_code_fence(response.content))
    except json.JSONDecodeError as exc:
        raise ValueError(f"model did not return valid JSON: {response.content!r}") from exc

    if "clarify" in parsed:
        raise ClarificationNeeded(parsed["clarify"])
    if "sql" in parsed:
        return str(parsed["sql"])
    raise ValueError(f"model response missing both 'sql' and 'clarify': {parsed!r}")
