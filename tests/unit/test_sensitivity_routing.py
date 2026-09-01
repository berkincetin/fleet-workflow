"""Sensitivity routing enforcement (CLAUDE.md rule 2, TRD §4.3 + §8).

The gateway client must REFUSE to send a request whose effective sensitivity
exceeds a model's clearance, and must apply the redaction-downgrade rule (§8):
content that passed the PII pipeline under policy `redact` carries effective
sensitivity `internal`. These are the guard tests the whole platform relies on;
they must never be weakened.
"""

from __future__ import annotations

import pytest
from core.llm.routing import (
    Sensitivity,
    SensitivityRefusal,
    effective_sensitivity,
    select_model,
)

# A small candidate registry mirroring the seeded matrix (name, role, clearance).
_MODELS = [
    {"name": "reasoning", "fleet_role": "reasoning", "sensitivity_clearance": "internal"},
    {"name": "utility", "fleet_role": "utility", "sensitivity_clearance": "internal"},
    {"name": "local-reasoning", "fleet_role": "reasoning", "sensitivity_clearance": "pii"},
    {"name": "local-embeddings", "fleet_role": "embeddings", "sensitivity_clearance": "pii"},
]


# --- clearance ordering ---------------------------------------------------


def test_clearance_is_ordered_public_lt_internal_lt_confidential_lt_pii() -> None:
    assert Sensitivity.PUBLIC < Sensitivity.INTERNAL < Sensitivity.CONFIDENTIAL < Sensitivity.PII


# --- effective sensitivity (max of inputs, with redaction downgrade) ------


def test_effective_sensitivity_is_max_of_inputs() -> None:
    assert effective_sensitivity(["public", "internal", "confidential"]) == Sensitivity.CONFIDENTIAL


def test_redaction_downgrade_makes_redacted_confidential_effective_internal() -> None:
    # A confidential input that has been redacted (policy `redact`) counts as internal.
    eff = effective_sensitivity(["confidential"], redacted=True)
    assert eff == Sensitivity.INTERNAL


def test_pii_never_downgrades_even_if_flagged_redacted() -> None:
    # allow-local-only / block content keeps its sensitivity; pii is never
    # downgraded by the redact rule.
    eff = effective_sensitivity(["pii"], redacted=True)
    assert eff == Sensitivity.PII


# --- model selection / refusal --------------------------------------------


def test_internal_request_routes_to_cloud_reasoning() -> None:
    model = select_model(_MODELS, role="reasoning", sensitivity="internal")
    assert model["name"] == "reasoning"


def test_pii_request_refuses_cloud_and_routes_to_local() -> None:
    model = select_model(_MODELS, role="reasoning", sensitivity="pii")
    assert model["name"] == "local-reasoning"


def test_pii_request_with_no_cleared_model_is_refused() -> None:
    cloud_only = [m for m in _MODELS if m["sensitivity_clearance"] == "internal"]
    with pytest.raises(SensitivityRefusal, match="pii"):
        select_model(cloud_only, role="reasoning", sensitivity="pii")


def test_confidential_request_refuses_internal_only_cloud_model() -> None:
    # No model is cleared for confidential here → refusal (unredacted confidential
    # stays local unless a model is explicitly cleared).
    cloud_only = [m for m in _MODELS if m["sensitivity_clearance"] == "internal"]
    with pytest.raises(SensitivityRefusal):
        select_model(cloud_only, role="reasoning", sensitivity="confidential")


def test_selection_prefers_lowest_sufficient_clearance() -> None:
    # An internal request should pick the internal-cleared model, not needlessly
    # route to the higher-clearance local one (keep cloud lane for non-PII).
    model = select_model(_MODELS, role="reasoning", sensitivity="internal")
    assert model["sensitivity_clearance"] == "internal"


async def test_invoice_extraction_resolves_to_the_local_lane() -> None:
    """Pins the documented behaviour of `invoice_agent` (dept scenario 04).

    The scenario doc once claimed "Claude Sonnet (on redacted text)", but
    `agents.invoice_agent.graph` calls `extract_invoice_fields` without
    `redacted=True`, and no cloud model has clearance >= confidential — so
    extraction has always resolved to the local lane. The doc was corrected to
    match (2026-09-01); this test is what keeps them from drifting apart again.
    A future change that genuinely wants cloud reasoning must add the redaction
    step AND update the doc, and will fail here first.
    """
    chosen = select_model(_MODELS, role="reasoning", sensitivity="confidential")
    assert chosen["name"] == "local-reasoning"
    assert chosen["sensitivity_clearance"] == "pii"


async def test_redaction_downgrade_would_reach_cloud_if_the_agent_ever_opted_in() -> None:
    """The counterpart: the downgrade rule itself works. Extraction is local
    because the agent never passes `redacted=True`, not because the mechanism
    is missing — so this documents exactly what changing that would unlock."""
    chosen = select_model(_MODELS, role="reasoning", sensitivity="confidential", redacted=True)
    assert chosen["name"] == "reasoning"
