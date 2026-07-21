"""Model registry domain logic (task 2.2).

Pure, transport-free helpers for the `models` registry (TRD §4.1/§4.2): validate
a draft into a persistable row, and fold a connectivity/capability smoke-test
result into the row's status. The actual probe (an HTTP call through the LiteLLM
proxy) lives in the router and is injected, keeping this module unit-testable.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

_CLEARANCES = ("public", "internal", "confidential", "pii")
_LOCAL_PROVIDERS = ("ollama", "vllm")


@dataclass
class ModelDraft:
    """An admin-submitted model definition (Admin → Models add form, §4.1)."""

    name: str
    provider: str
    litellm_model_id: str
    input_price_per_1k: float
    output_price_per_1k: float
    context_window: int
    capabilities: list[str]
    max_output_tokens: int
    sensitivity_clearance: str
    endpoint: str | None = None
    cached_input_price: float | None = None
    region: str | None = None


@dataclass
class SmokeResult:
    """Outcome of the connectivity/capability probe run on add."""

    reachable: bool
    capabilities_ok: bool
    detail: str
    latency_ms: int | None = None


def _is_local(draft: ModelDraft) -> bool:
    return draft.provider.lower() in _LOCAL_PROVIDERS or draft.litellm_model_id.startswith(
        tuple(f"{p}/" for p in _LOCAL_PROVIDERS)
    )


def build_model_row(draft: ModelDraft) -> dict[str, Any]:
    """Validate a draft and return the row to persist (status `pending` pre-smoke).

    Enforces the TRD §4.2 clearance rule that no cloud model may be cleared for
    `pii`; only local-lane (ollama/vllm) models may carry `pii`.
    """
    if draft.sensitivity_clearance not in _CLEARANCES:
        raise ValueError(f"unknown sensitivity_clearance: {draft.sensitivity_clearance}")
    if draft.sensitivity_clearance == "pii" and not _is_local(draft):
        raise ValueError(
            "no cloud model may be cleared for pii (TRD §4.2); "
            f"provider={draft.provider!r} is not a local lane"
        )
    if draft.input_price_per_1k < 0 or draft.output_price_per_1k < 0:
        raise ValueError("prices must be non-negative")

    return {
        "name": draft.name,
        "provider": draft.provider,
        "litellm_model_id": draft.litellm_model_id,
        "endpoint": draft.endpoint,
        "input_price_per_1k": draft.input_price_per_1k,
        "output_price_per_1k": draft.output_price_per_1k,
        "cached_input_price": draft.cached_input_price,
        "context_window": draft.context_window,
        "capabilities": list(draft.capabilities),
        "max_output_tokens": draft.max_output_tokens,
        "sensitivity_clearance": draft.sensitivity_clearance,
        "region": draft.region,
        "status": "pending",
        "smoke_status": "pending",
        "smoke_detail": None,
        "smoke_latency_ms": None,
    }


def evaluate_smoke(
    draft: ModelDraft, probe: SmokeResult
) -> tuple[str, dict[str, Any]]:
    """Fold a probe result into (row status, smoke_* fields).

    - unreachable → status ``error`` / smoke ``failed``
    - reachable but declared capabilities unconfirmed → ``degraded``
    - reachable and capabilities confirmed → ``active`` / smoke ``ok``
    """
    if not probe.reachable:
        status, smoke = "error", "failed"
    elif not probe.capabilities_ok:
        status, smoke = "degraded", "degraded"
    else:
        status, smoke = "active", "ok"

    return status, {
        "status": status,
        "smoke_status": smoke,
        "smoke_detail": probe.detail,
        "smoke_latency_ms": probe.latency_ms,
    }
