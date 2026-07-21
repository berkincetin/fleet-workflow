"""Budget enforcement inside the gateway client (task 2.4).

The client runs a budget pre-check BEFORE the transport call: a hard-stop blocks
the call (BudgetExceeded, nothing billed) and a soft-limit is surfaced on the
response metadata. The checker is injected, so no DB is needed.
"""

from __future__ import annotations

import pytest
from core.llm.budget import BudgetExceeded, BudgetStatus, evaluate_budget
from core.llm.client import LLMClient, LLMResponse

_MODELS = [
    {"name": "reasoning", "fleet_role": "reasoning", "sensitivity_clearance": "internal",
     "input_price_per_1k": 0.003, "output_price_per_1k": 0.015},
]


class FakeTransport:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    async def complete(self, *, model: str, messages: list[dict], **kw: object) -> dict:
        self.calls.append({"model": model})
        return {
            "model": model,
            "choices": [{"message": {"role": "assistant", "content": "ok"}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5},
        }


class FakeLedger:
    def __init__(self) -> None:
        self.rows: list[dict] = []

    async def record(self, row: dict) -> None:
        self.rows.append(row)


def _checker(status: BudgetStatus):
    async def check(meta: dict) -> BudgetStatus:
        return status

    return check


async def test_hard_stop_blocks_call_and_bills_nothing() -> None:
    t, led = FakeTransport(), FakeLedger()
    over = evaluate_budget(spent_usd=100.0, limit_usd=100.0, soft_pct=80, scope="dept:cs")
    client = LLMClient(models=_MODELS, transport=t, ledger=led, budget_checker=_checker(over))

    with pytest.raises(BudgetExceeded):
        await client.reasoning([{"role": "user", "content": "x"}], sensitivity="internal")
    assert t.calls == []  # blocked before transport
    assert led.rows == []  # nothing billed


async def test_soft_limit_allows_call_and_flags_response() -> None:
    t, led = FakeTransport(), FakeLedger()
    soft = evaluate_budget(spent_usd=90.0, limit_usd=100.0, soft_pct=80, scope="dept:cs")
    client = LLMClient(models=_MODELS, transport=t, ledger=led, budget_checker=_checker(soft))

    resp = await client.reasoning([{"role": "user", "content": "x"}], sensitivity="internal")
    assert isinstance(resp, LLMResponse)
    assert resp.budget_soft_exceeded is True
    assert len(t.calls) == 1  # call went through


async def test_under_budget_is_not_flagged() -> None:
    t, led = FakeTransport(), FakeLedger()
    under = evaluate_budget(spent_usd=5.0, limit_usd=100.0, soft_pct=80, scope="dept:cs")
    client = LLMClient(models=_MODELS, transport=t, ledger=led, budget_checker=_checker(under))

    resp = await client.reasoning([{"role": "user", "content": "x"}], sensitivity="internal")
    assert resp.budget_soft_exceeded is False


async def test_no_checker_means_no_enforcement() -> None:
    # Backwards-compatible: a client built without a budget checker just calls.
    t, led = FakeTransport(), FakeLedger()
    client = LLMClient(models=_MODELS, transport=t, ledger=led)
    resp = await client.reasoning([{"role": "user", "content": "x"}], sensitivity="internal")
    assert resp.budget_soft_exceeded is False
    assert len(t.calls) == 1
