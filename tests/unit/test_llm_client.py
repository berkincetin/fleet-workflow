"""Gateway client orchestration (task 2.3).

The client is the ONLY place LLM calls are made (CLAUDE.md rule 1). Unit-level:
it enforces sensitivity BEFORE any transport call, records spend on success, and
raises a clean domain error when the transport (after LiteLLM's own retries +
fallback chain) still fails. Transport and ledger sink are injected, so no
network/DB is needed here.
"""

from __future__ import annotations

import pytest
from core.llm.client import GatewayError, LLMClient, LLMResponse
from core.llm.routing import SensitivityRefusal

_MODELS = [
    {"name": "reasoning", "fleet_role": "reasoning", "sensitivity_clearance": "internal",
     "input_price_per_1k": 0.003, "output_price_per_1k": 0.015},
    {"name": "utility", "fleet_role": "utility", "sensitivity_clearance": "internal",
     "input_price_per_1k": 0.000075, "output_price_per_1k": 0.0003},
    {"name": "local-reasoning", "fleet_role": "reasoning", "sensitivity_clearance": "pii",
     "input_price_per_1k": 0.0, "output_price_per_1k": 0.0},
]


class FakeTransport:
    """Records calls; returns a canned OpenAI-style body, or raises to simulate
    an exhausted fallback chain."""

    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        self.calls: list[dict] = []

    async def complete(self, *, model: str, messages: list[dict], **kw: object) -> dict:
        self.calls.append({"model": model, "messages": messages, **kw})
        if self.fail:
            raise RuntimeError("all fallbacks exhausted")
        return {
            "model": model,
            "choices": [{"message": {"role": "assistant", "content": "pong"}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5},
        }


class FakeLedger:
    def __init__(self) -> None:
        self.rows: list[dict] = []

    async def record(self, row: dict) -> None:
        self.rows.append(row)


def _client(transport: FakeTransport, ledger: FakeLedger) -> LLMClient:
    return LLMClient(models=_MODELS, transport=transport, ledger=ledger)


async def test_reasoning_calls_cloud_model_for_internal_request() -> None:
    t, led = FakeTransport(), FakeLedger()
    resp = await _client(t, led).reasoning(
        [{"role": "user", "content": "hi"}], sensitivity="internal"
    )
    assert isinstance(resp, LLMResponse)
    assert resp.model == "reasoning"
    assert resp.content == "pong"
    assert t.calls[0]["model"] == "reasoning"


async def test_utility_helper_routes_to_utility_model() -> None:
    t, led = FakeTransport(), FakeLedger()
    await _client(t, led).utility([{"role": "user", "content": "classify"}])
    assert t.calls[0]["model"] == "utility"


async def test_pii_request_never_hits_transport_when_no_local_model() -> None:
    cloud_only = [m for m in _MODELS if m["sensitivity_clearance"] == "internal"]
    t, led = FakeTransport(), FakeLedger()
    client = LLMClient(models=cloud_only, transport=t, ledger=led)
    with pytest.raises(SensitivityRefusal):
        await client.reasoning([{"role": "user", "content": "x"}], sensitivity="pii")
    assert t.calls == []  # refused before any call
    assert led.rows == []  # nothing billed


async def test_pii_request_routes_to_local_model() -> None:
    t, led = FakeTransport(), FakeLedger()
    resp = await _client(t, led).reasoning(
        [{"role": "user", "content": "x"}], sensitivity="pii"
    )
    assert resp.model == "local-reasoning"


async def test_successful_call_records_spend_row() -> None:
    t, led = FakeTransport(), FakeLedger()
    await _client(t, led).reasoning(
        [{"role": "user", "content": "hi"}],
        sensitivity="internal",
        agent_id="support-copilot",
        user_id="u-1",
        dept_id="cs",
        trace_id="trace-xyz",
    )
    assert len(led.rows) == 1
    row = led.rows[0]
    assert row["model"] == "reasoning"
    assert row["tok_in"] == 10
    assert row["tok_out"] == 5
    assert row["trace_id"] == "trace-xyz"
    assert row["agent_id"] == "support-copilot"
    # 10/1000*0.003 + 5/1000*0.015
    assert round(row["cost_usd"], 8) == round(10 / 1000 * 0.003 + 5 / 1000 * 0.015, 8)


async def test_transport_failure_raises_gateway_error_and_records_nothing() -> None:
    t, led = FakeTransport(fail=True), FakeLedger()
    with pytest.raises(GatewayError):
        await _client(t, led).reasoning(
            [{"role": "user", "content": "hi"}], sensitivity="internal"
        )
    assert led.rows == []
