"""Unit tests for the model registry service (task 2.2).

The registry stores rows of the TRD §4.1 `models` schema and, crucially, runs a
connectivity/capability smoke test when a model is added, storing the result on
the row. The smoke test's transport (a call through the LiteLLM proxy) is
injected, so these tests run without Docker: a fake prober stands in for the
real HTTP probe.
"""

from __future__ import annotations

import pytest
from fleet_api.registry import (
    ModelDraft,
    SmokeResult,
    build_model_row,
    evaluate_smoke,
)


def _draft(**over: object) -> ModelDraft:
    base = dict(
        name="reasoning",
        provider="anthropic",
        litellm_model_id="anthropic/claude-sonnet-4-5",
        endpoint=None,
        input_price_per_1k=0.003,
        output_price_per_1k=0.015,
        cached_input_price=0.0003,
        context_window=200000,
        capabilities=["tools", "json", "vision"],
        max_output_tokens=8192,
        sensitivity_clearance="internal",
        region="us",
    )
    base.update(over)
    return ModelDraft(**base)  # type: ignore[arg-type]


def test_build_row_defaults_status_pending_before_smoke() -> None:
    row = build_model_row(_draft())
    assert row["name"] == "reasoning"
    assert row["litellm_model_id"] == "anthropic/claude-sonnet-4-5"
    assert row["status"] == "pending"
    assert row["smoke_status"] == "pending"


def test_pii_clearance_rejected_for_cloud_model() -> None:
    # TRD §4.2: no cloud model may be cleared for pii.
    with pytest.raises(ValueError, match="pii"):
        build_model_row(_draft(sensitivity_clearance="pii"))


def test_pii_clearance_allowed_for_ollama_model() -> None:
    row = build_model_row(
        _draft(
            name="local-reasoning",
            provider="ollama",
            litellm_model_id="ollama/qwen2.5:7b-instruct-q4_K_M",
            sensitivity_clearance="pii",
        )
    )
    assert row["sensitivity_clearance"] == "pii"


def test_smoke_ok_marks_model_active() -> None:
    probe = SmokeResult(reachable=True, latency_ms=42, detail="ok", capabilities_ok=True)
    status, fields = evaluate_smoke(_draft(), probe)
    assert status == "active"
    assert fields["smoke_status"] == "ok"
    assert fields["smoke_detail"] == "ok"
    assert fields["smoke_latency_ms"] == 42


def test_smoke_unreachable_marks_model_error_not_active() -> None:
    probe = SmokeResult(reachable=False, latency_ms=None, detail="connection refused",
                        capabilities_ok=False)
    status, fields = evaluate_smoke(_draft(), probe)
    assert status == "error"
    assert fields["smoke_status"] == "failed"
    assert "connection refused" in fields["smoke_detail"]


def test_smoke_capability_mismatch_is_degraded() -> None:
    # Reachable, but declared capabilities not confirmed by the probe.
    probe = SmokeResult(reachable=True, latency_ms=30, detail="no tool support",
                        capabilities_ok=False)
    status, fields = evaluate_smoke(_draft(), probe)
    assert status == "degraded"
    assert fields["smoke_status"] == "degraded"
