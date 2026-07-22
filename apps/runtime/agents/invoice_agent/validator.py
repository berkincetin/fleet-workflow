"""Extracted fields -> validation against purchase records (task 6.3, dept
scenario 04 "validation against purchase records" step).

Pure, DB-free decision logic — the PO lookup itself is an injected Protocol
(GovernedPoLookup), same "depends on the shape, not the package" boundary
agents.analytics.service established for pg_ro (apps/runtime has no fleet-mcp
workspace dependency; the real pg_ro-backed lookup is wired in by the caller
in apps/api). A mismatch or duplicate always blocks straight-to-draft — the
department scenario's evals are explicit that these must "flag, never
auto-draft as clean," so `validate_invoice` never silently accepts either
case; a human still decides via the approval queue either way (erp writes are
"approval-gated forever" regardless of validation outcome), but the *reason*
surfaced to the approver differs.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from agents.invoice_agent.extractor import InvoiceFields

# Amounts rarely match a PO to the cent after tax/rounding differences in real
# invoices; a small relative tolerance avoids flagging every invoice as a
# mismatch over rounding noise while still catching genuine discrepancies.
_AMOUNT_TOLERANCE_PCT = 0.01


class PoNotFoundError(Exception):
    """No purchase order exists for the extracted po_number."""


@dataclass(frozen=True)
class PurchaseOrder:
    po_number: str
    vendor: str
    amount: float
    currency: str


class GovernedPoLookup(Protocol):
    async def lookup(self, po_number: str) -> PurchaseOrder | None: ...


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    reasons: list[str]
    purchase_order: PurchaseOrder | None


def _amount_mismatches(invoice_amount: float, po_amount: float) -> bool:
    if po_amount == 0:
        return invoice_amount != 0
    return abs(invoice_amount - po_amount) / po_amount > _AMOUNT_TOLERANCE_PCT


def check_duplicate(fields: InvoiceFields, *, seen_po_numbers: set[str]) -> bool:
    """True if this PO number has already been processed this run/session —
    the department scenario's "duplicate invoice fixture -> flag" case."""
    return fields.po_number in seen_po_numbers


async def validate_invoice(
    fields: InvoiceFields, *, po_lookup: GovernedPoLookup, seen_po_numbers: set[str]
) -> ValidationResult:
    reasons: list[str] = []

    if check_duplicate(fields, seen_po_numbers=seen_po_numbers):
        reasons.append(f"duplicate: PO {fields.po_number!r} already processed")

    po = await po_lookup.lookup(fields.po_number)
    if po is None:
        reasons.append(f"purchase order not found: {fields.po_number!r}")
        return ValidationResult(ok=False, reasons=reasons, purchase_order=None)

    if _amount_mismatches(fields.amount, po.amount):
        reasons.append(
            f"amount mismatch: invoice {fields.amount} {fields.currency} vs "
            f"PO {po.amount} {po.currency}"
        )
    if fields.vendor.strip().lower() != po.vendor.strip().lower():
        reasons.append(f"vendor mismatch: invoice {fields.vendor!r} vs PO {po.vendor!r}")

    return ValidationResult(ok=not reasons, reasons=reasons, purchase_order=po)
