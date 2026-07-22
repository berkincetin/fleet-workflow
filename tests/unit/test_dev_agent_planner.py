"""agents.dev_agent.planner: ticket -> plan (task 5.5, dept scenario 03
"plan" step, TRD §4.3 reasoning tier).

The model answers with one JSON object: branch_suffix, pr_title, pr_body,
target_paths (files the plan would touch), diff_line_estimate. Guardrails
(protected paths, diff cap, ticket label) are applied by the caller using
agents.dev_agent.guardrails against this plan's fields — planner itself only
parses the model's structured proposal.
"""

from __future__ import annotations

import pytest
from agents.dev_agent.planner import PlanParseError, plan_ticket


class _FakeLLM:
    def __init__(self, content: str) -> None:
        self.content = content
        self.calls: list[list[dict[str, object]]] = []

    async def reasoning(self, messages: list[dict[str, object]], **kwargs: object) -> object:
        self.calls.append(messages)

        class _Resp:
            content = self.content

        return _Resp()


_VALID_PLAN_JSON = (
    '{"branch_suffix": "fix-typo", "pr_title": "Fix typo in README", '
    '"pr_body": "Closes DEV-1", "target_paths": ["README.md"], '
    '"diff_line_estimate": 3}'
)


async def test_plan_ticket_parses_valid_response() -> None:
    llm = _FakeLLM(_VALID_PLAN_JSON)
    ticket = {"key": "DEV-1", "summary": "Fix typo", "labels": ["agent-ok"]}
    plan = await plan_ticket(ticket=ticket, llm_client=llm)
    assert plan.branch_suffix == "fix-typo"
    assert plan.pr_title == "Fix typo in README"
    assert plan.target_paths == ["README.md"]
    assert plan.diff_line_estimate == 3


async def test_plan_ticket_uses_reasoning_tier() -> None:
    calls = {"reasoning": False, "utility": False}

    class _TierLLM:
        async def reasoning(self, messages: list[dict[str, object]], **kwargs: object) -> object:
            calls["reasoning"] = True

            class _Resp:
                content = _VALID_PLAN_JSON

            return _Resp()

        async def utility(self, messages: list[dict[str, object]], **kwargs: object) -> object:
            calls["utility"] = True
            raise AssertionError("planner must not call utility()")

    await plan_ticket(
        ticket={"key": "DEV-1", "summary": "x", "labels": []}, llm_client=_TierLLM()
    )
    assert calls["reasoning"] is True
    assert calls["utility"] is False


async def test_plan_ticket_strips_markdown_code_fence() -> None:
    llm = _FakeLLM(f"```json\n{_VALID_PLAN_JSON}\n```")
    plan = await plan_ticket(
        ticket={"key": "DEV-1", "summary": "x", "labels": []}, llm_client=llm
    )
    assert plan.pr_title == "Fix typo in README"


async def test_plan_ticket_raises_on_malformed_json() -> None:
    llm = _FakeLLM("not json")
    with pytest.raises(PlanParseError):
        await plan_ticket(ticket={"key": "DEV-1", "summary": "x", "labels": []}, llm_client=llm)


async def test_plan_ticket_raises_on_missing_field() -> None:
    llm = _FakeLLM('{"branch_suffix": "x"}')
    with pytest.raises(PlanParseError):
        await plan_ticket(ticket={"key": "DEV-1", "summary": "x", "labels": []}, llm_client=llm)


async def test_plan_ticket_prompt_includes_ticket_summary() -> None:
    llm = _FakeLLM(_VALID_PLAN_JSON)
    await plan_ticket(
        ticket={"key": "DEV-1", "summary": "Fix the login bug", "labels": []}, llm_client=llm
    )
    user_message = llm.calls[0][-1]["content"]
    assert "Fix the login bug" in user_message
