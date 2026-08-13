"""Prometheus metrics emitted by the gateway client's budget check (task 7.4).

`fleet_budget_soft_limit_total` feeds the Alertmanager rule that fires a
Slack notification when a scope crosses its soft limit — this proves the
client-side half of that AC (the counter itself increments); the alert rule
and Slack routing are proven separately by `promtool test rules` and
tests/integration/test_metrics_endpoint_live.py.
"""

from __future__ import annotations

from core.llm.budget import evaluate_budget
from core.llm.client import LLMClient
from core.metrics import BUDGET_SOFT_LIMIT_TOTAL

_MODELS = [
    {"name": "reasoning", "fleet_role": "reasoning", "sensitivity_clearance": "internal",
     "input_price_per_1k": 0.003, "output_price_per_1k": 0.015},
]


class FakeTransport:
    async def complete(self, *, model: str, messages: list[dict], **kw: object) -> dict:
        return {
            "model": model,
            "choices": [{"message": {"role": "assistant", "content": "ok"}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5},
        }


class FakeLedger:
    async def record(self, row: dict) -> None:
        pass


def _checker(status):
    async def check(meta: dict):
        return status

    return check


def _counter_value(scope: str) -> float:
    return BUDGET_SOFT_LIMIT_TOTAL.labels(scope=scope)._value.get()


async def test_soft_limit_call_increments_the_counter() -> None:
    scope = "dept:metrics-test-soft"
    before = _counter_value(scope)
    soft = evaluate_budget(spent_usd=90.0, limit_usd=100.0, soft_pct=80, scope=scope)
    client = LLMClient(
        models=_MODELS, transport=FakeTransport(), ledger=FakeLedger(),
        budget_checker=_checker(soft),
    )

    await client.reasoning([{"role": "user", "content": "x"}], sensitivity="internal")

    assert _counter_value(scope) == before + 1


async def test_under_budget_call_does_not_increment_the_counter() -> None:
    scope = "dept:metrics-test-under"
    before = _counter_value(scope)
    under = evaluate_budget(spent_usd=5.0, limit_usd=100.0, soft_pct=80, scope=scope)
    client = LLMClient(
        models=_MODELS, transport=FakeTransport(), ledger=FakeLedger(),
        budget_checker=_checker(under),
    )

    await client.reasoning([{"role": "user", "content": "x"}], sensitivity="internal")

    assert _counter_value(scope) == before
