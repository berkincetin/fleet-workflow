"""Gateway client orchestration (task 2.3).

The client is the ONLY place LLM calls are made (CLAUDE.md rule 1). Unit-level:
it enforces sensitivity BEFORE any transport call, records spend on success, and
raises a clean domain error when the transport (after LiteLLM's own retries +
fallback chain) still fails. Transport and ledger sink are injected, so no
network/DB is needed here.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

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
    {"name": "embeddings", "fleet_role": "embeddings", "sensitivity_clearance": "internal",
     "input_price_per_1k": 0.00002, "output_price_per_1k": 0.0},
    {"name": "local-embeddings", "fleet_role": "embeddings", "sensitivity_clearance": "pii",
     "input_price_per_1k": 0.0, "output_price_per_1k": 0.0},
]


class FakeTransport:
    """Records calls; returns a canned OpenAI-style body, or raises to simulate
    an exhausted fallback chain."""

    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        self.calls: list[dict] = []
        self.embed_calls: list[dict] = []

    async def complete(self, *, model: str, messages: list[dict], **kw: object) -> dict:
        self.calls.append({"model": model, "messages": messages, **kw})
        if self.fail:
            raise RuntimeError("all fallbacks exhausted")
        return {
            "model": model,
            "choices": [{"message": {"role": "assistant", "content": "pong"}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5},
        }

    async def embed(self, *, model: str, input: list[str], **kw: object) -> dict:
        self.embed_calls.append({"model": model, "input": input, **kw})
        if self.fail:
            raise RuntimeError("all fallbacks exhausted")
        return {
            "model": model,
            "data": [{"embedding": [0.1, 0.2, 0.3], "index": i} for i in range(len(input))],
            "usage": {"prompt_tokens": 10, "completion_tokens": 0},
        }

    async def stream_complete(
        self, *, model: str, messages: list[dict], **kw: object
    ) -> AsyncIterator[dict]:
        self.calls.append({"model": model, "messages": messages, **kw})
        if self.fail:
            raise RuntimeError("all fallbacks exhausted")

        async def _gen() -> AsyncIterator[dict]:
            for word in ["pong", " two", " three"]:
                yield {"model": model, "delta": word}
            yield {
                "model": model,
                "delta": "",
                "usage": {"prompt_tokens": 10, "completion_tokens": 5},
            }

        return _gen()


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


async def test_reasoning_forwards_trace_and_agent_id_to_transport() -> None:
    """§6 trace correlation: the proxy's Langfuse callback must tag the trace
    with the SAME id spend_ledger.trace_id records, or Langfuse mints its own
    random trace id and the two never correlate (breaks feedback scoring)."""
    t, led = FakeTransport(), FakeLedger()
    await _client(t, led).reasoning(
        [{"role": "user", "content": "hi"}],
        sensitivity="internal",
        trace_id="trace-xyz",
        agent_id="support-copilot",
        user_id="u-1",
        dept_id="cs",
    )
    assert t.calls[0]["trace_id"] == "trace-xyz"
    assert t.calls[0]["agent_id"] == "support-copilot"
    assert t.calls[0]["user_id"] == "u-1"
    assert t.calls[0]["dept_id"] == "cs"


async def test_embeddings_forwards_trace_id_to_transport() -> None:
    t, led = FakeTransport(), FakeLedger()
    await _client(t, led).embeddings(["x"], sensitivity="internal", trace_id="trace-e")
    assert t.embed_calls[0]["trace_id"] == "trace-e"


async def test_transport_failure_raises_gateway_error_and_records_nothing() -> None:
    t, led = FakeTransport(fail=True), FakeLedger()
    with pytest.raises(GatewayError):
        await _client(t, led).reasoning(
            [{"role": "user", "content": "hi"}], sensitivity="internal"
        )
    assert led.rows == []


async def test_embeddings_routes_to_embeddings_model() -> None:
    t, led = FakeTransport(), FakeLedger()
    resp = await _client(t, led).embeddings(["chunk one", "chunk two"], sensitivity="internal")
    assert t.embed_calls[0]["model"] == "embeddings"
    assert t.embed_calls[0]["input"] == ["chunk one", "chunk two"]
    assert len(resp.vectors) == 2
    assert resp.model == "embeddings"


async def test_embeddings_pii_routes_to_local_model() -> None:
    t, led = FakeTransport(), FakeLedger()
    resp = await _client(t, led).embeddings(["secret"], sensitivity="pii")
    assert resp.model == "local-embeddings"


async def test_embeddings_records_spend_row() -> None:
    t, led = FakeTransport(), FakeLedger()
    await _client(t, led).embeddings(["x"], sensitivity="internal", trace_id="trace-e")
    assert len(led.rows) == 1
    assert led.rows[0]["trace_id"] == "trace-e"


async def test_reasoning_stream_yields_text_deltas_in_order() -> None:
    t, led = FakeTransport(), FakeLedger()
    deltas = [d async for d in _client(t, led).reasoning_stream(
        [{"role": "user", "content": "hi"}], sensitivity="internal"
    )]
    assert deltas == ["pong", " two", " three"]


async def test_reasoning_stream_enforces_sensitivity_before_any_chunk() -> None:
    cloud_only = [m for m in _MODELS if m["sensitivity_clearance"] == "internal"]
    t, led = FakeTransport(), FakeLedger()
    client = LLMClient(models=cloud_only, transport=t, ledger=led)
    with pytest.raises(SensitivityRefusal):
        async for _ in client.reasoning_stream(
            [{"role": "user", "content": "x"}], sensitivity="pii"
        ):
            pass
    assert t.calls == []
    assert led.rows == []


async def test_reasoning_stream_forwards_trace_id_to_transport() -> None:
    t, led = FakeTransport(), FakeLedger()
    async for _ in _client(t, led).reasoning_stream(
        [{"role": "user", "content": "hi"}], sensitivity="internal", trace_id="trace-s"
    ):
        pass
    assert t.calls[0]["trace_id"] == "trace-s"


async def test_reasoning_stream_records_spend_after_stream_completes() -> None:
    t, led = FakeTransport(), FakeLedger()
    stream = _client(t, led).reasoning_stream(
        [{"role": "user", "content": "hi"}], sensitivity="internal", trace_id="trace-s"
    )
    async for _ in stream:
        pass
    assert len(led.rows) == 1
    assert led.rows[0]["tok_in"] == 10
    assert led.rows[0]["tok_out"] == 5
    assert led.rows[0]["trace_id"] == "trace-s"


async def test_reasoning_stream_transport_failure_raises_gateway_error() -> None:
    t, led = FakeTransport(fail=True), FakeLedger()
    with pytest.raises(GatewayError):
        async for _ in _client(t, led).reasoning_stream(
            [{"role": "user", "content": "hi"}], sensitivity="internal"
        ):
            pass
    assert led.rows == []
