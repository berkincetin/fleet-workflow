"""Sensitivity routing — the KVKK guardrail (CLAUDE.md rule 2, TRD §4.3 + §8).

Pure decision logic: compute a request's effective sensitivity (max of inputs,
after the §8 redaction-downgrade rule) and select a model whose clearance covers
it, refusing when none does. No I/O — enforced in code and guarded by
tests/unit/test_sensitivity_routing.py. Never weaken these rules.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from enum import IntEnum
from typing import Any


class Sensitivity(IntEnum):
    """Ordered classification: public < internal < confidential < pii (§4.2)."""

    PUBLIC = 0
    INTERNAL = 1
    CONFIDENTIAL = 2
    PII = 3

    @classmethod
    def parse(cls, value: str | Sensitivity) -> Sensitivity:
        if isinstance(value, Sensitivity):
            return value
        try:
            return cls[value.upper()]
        except KeyError as exc:
            raise ValueError(f"unknown sensitivity: {value!r}") from exc


class SensitivityRefusal(Exception):
    """Raised when no model's clearance covers the request's effective sensitivity."""


def effective_sensitivity(
    inputs: Iterable[str | Sensitivity], *, redacted: bool = False
) -> Sensitivity:
    """Return max(inputs), applying the §8 redaction-downgrade rule.

    Content that passed the PII pipeline under policy `redact` (``redacted=True``)
    carries effective sensitivity `internal` — the mechanism that lets cloud
    models reason over redacted invoices/briefs. `pii` is NEVER downgraded (its
    policy is allow-local-only/block, not redact), so redacted+pii stays pii.
    """
    levels = [Sensitivity.parse(i) for i in inputs]
    top = max(levels) if levels else Sensitivity.PUBLIC
    if redacted and top == Sensitivity.CONFIDENTIAL:
        return Sensitivity.INTERNAL
    return top


def _clearance(model: dict[str, Any]) -> Sensitivity:
    return Sensitivity.parse(model["sensitivity_clearance"])


def select_model(
    models: Sequence[dict[str, Any]],
    *,
    role: str,
    sensitivity: str | Sensitivity,
    redacted: bool = False,
) -> dict[str, Any]:
    """Pick the eligible model of `role` with the lowest sufficient clearance.

    Eligibility: fleet_role matches AND clearance >= effective sensitivity. Among
    eligible models, prefer the lowest clearance (keep the cloud lane for non-PII
    rather than needlessly routing to a higher-clearance local model). Refuse if
    none qualifies.
    """
    eff = effective_sensitivity([sensitivity], redacted=redacted)
    candidates = [
        m for m in models if m.get("fleet_role") == role and _clearance(m) >= eff
    ]
    if not candidates:
        raise SensitivityRefusal(
            f"no {role} model cleared for effective sensitivity "
            f"{eff.name.lower()}; request refused (CLAUDE.md rule 2)"
        )
    return min(candidates, key=_clearance)
