"""Integration: the model registry smoke-test-on-add path against the LIVE
LiteLLM proxy (task 2.2 AC).

Exercises the real probe (`probe_model` → proxy `/chat/completions`) plus the
pure fold into a row (`evaluate_smoke`), proving that adding a model runs a
connectivity/capability smoke test whose result is stored. Requires the compose
proxy on :4000 (skipped if unreachable) — provider auth is irrelevant here: the
probe targets `utility`, whose fallback chain lands on a working cloud model.
"""

from __future__ import annotations

import asyncio
import os

import httpx
import pytest
from fleet_api.registry import ModelDraft, build_model_row, evaluate_smoke
from fleet_api.registry_probe import probe_model

PROXY = os.environ.get("FLEET_LITELLM_BASE_URL", "http://localhost:4000/v1")
KEY = os.environ.get("FLEET_LITELLM_MASTER_KEY", "sk-fleet-dev-master")


def _proxy_up() -> bool:
    try:
        httpx.get(f"{PROXY.rstrip('/')}/models", headers={"Authorization": f"Bearer {KEY}"},
                  timeout=5)
        return True
    except httpx.HTTPError:
        return False


@pytest.mark.skipif(not _proxy_up(), reason="LiteLLM proxy not reachable on :4000")
def test_smoke_on_add_marks_reachable_model_active() -> None:
    draft = ModelDraft(
        name="utility",
        provider="gemini",
        litellm_model_id="utility",
        input_price_per_1k=0.000075,
        output_price_per_1k=0.0003,
        context_window=1000000,
        capabilities=["json"],
        max_output_tokens=8,
        sensitivity_clearance="internal",
    )

    async def _run() -> None:
        # 1. build the pending row (what the POST handler does first)
        row = build_model_row(draft)
        assert row["status"] == "pending"
        assert row["smoke_status"] == "pending"

        # 2. run the smoke test against the live proxy
        probe = await probe_model(draft, proxy_base_url=PROXY, master_key=KEY)
        assert probe.reachable is True, probe.detail

        # 3. fold the result into the row (what the handler stores)
        status, fields = evaluate_smoke(draft, probe)
        assert status == "active"
        assert fields["smoke_status"] == "ok"
        assert fields["smoke_latency_ms"] is not None

    asyncio.run(_run())


@pytest.mark.skipif(not _proxy_up(), reason="LiteLLM proxy not reachable on :4000")
def test_smoke_on_add_marks_unknown_model_error() -> None:
    # A model id the proxy does not know → probe unreachable → row lands 'error'.
    draft = ModelDraft(
        name="does-not-exist",
        provider="openai",
        litellm_model_id="no-such-model-xyz",
        input_price_per_1k=0.0,
        output_price_per_1k=0.0,
        context_window=1000,
        capabilities=[],
        max_output_tokens=1,
        sensitivity_clearance="internal",
    )

    async def _run() -> None:
        probe = await probe_model(draft, proxy_base_url=PROXY, master_key=KEY)
        status, fields = evaluate_smoke(draft, probe)
        assert status == "error"
        assert fields["smoke_status"] == "failed"

    asyncio.run(_run())
