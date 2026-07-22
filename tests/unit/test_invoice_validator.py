"""agents.invoice_agent.validator: extracted fields -> validation against
purchase records (task 6.3, dept scenario 04). Both required eval fixtures
from the department scenario spec are covered directly:
"mismatch fixture (amount differs from PO) -> must flag, never auto-draft as
clean" and "duplicate invoice fixture -> flag".
"""

from __future__ import annotations

from agents.invoice_agent.extractor import InvoiceFields
from agents.invoice_agent.validator import PurchaseOrder, validate_invoice


class _FakePoLookup:
    def __init__(self, pos: dict[str, PurchaseOrder]) -> None:
        self.pos = pos

    async def lookup(self, po_number: str) -> PurchaseOrder | None:
        return self.pos.get(po_number)


def _po(**over: object) -> PurchaseOrder:
    base: dict[str, object] = dict(
        po_number="PO-1001", vendor="Acme Tedarik A.S.", amount=1250.0, currency="TRY"
    )
    base.update(over)
    return PurchaseOrder(**base)  # type: ignore[arg-type]


def _fields(**over: object) -> InvoiceFields:
    base: dict[str, object] = dict(
        vendor="Acme Tedarik A.S.", po_number="PO-1001", amount=1250.0, currency="TRY"
    )
    base.update(over)
    return InvoiceFields(**base)  # type: ignore[arg-type]


async def test_matching_invoice_validates_ok() -> None:
    lookup = _FakePoLookup({"PO-1001": _po()})
    result = await validate_invoice(_fields(), po_lookup=lookup, seen_po_numbers=set())
    assert result.ok is True
    assert result.reasons == []
    assert result.purchase_order is not None


async def test_amount_mismatch_is_flagged_never_silently_ok() -> None:
    lookup = _FakePoLookup({"PO-1001": _po(amount=1250.0)})
    result = await validate_invoice(
        _fields(amount=5000.0), po_lookup=lookup, seen_po_numbers=set()
    )
    assert result.ok is False
    assert any("amount mismatch" in r for r in result.reasons)


async def test_small_rounding_difference_is_not_flagged_as_mismatch() -> None:
    lookup = _FakePoLookup({"PO-1001": _po(amount=1250.0)})
    result = await validate_invoice(
        _fields(amount=1250.05), po_lookup=lookup, seen_po_numbers=set()
    )
    assert result.ok is True


async def test_duplicate_po_number_is_flagged() -> None:
    lookup = _FakePoLookup({"PO-1001": _po()})
    result = await validate_invoice(
        _fields(), po_lookup=lookup, seen_po_numbers={"PO-1001"}
    )
    assert result.ok is False
    assert any("duplicate" in r for r in result.reasons)


async def test_unknown_po_number_is_flagged_not_found() -> None:
    lookup = _FakePoLookup({})
    result = await validate_invoice(_fields(), po_lookup=lookup, seen_po_numbers=set())
    assert result.ok is False
    assert result.purchase_order is None
    assert any("not found" in r for r in result.reasons)


async def test_vendor_mismatch_is_flagged() -> None:
    lookup = _FakePoLookup({"PO-1001": _po(vendor="Bilgi Teknoloji Ltd.")})
    result = await validate_invoice(_fields(), po_lookup=lookup, seen_po_numbers=set())
    assert result.ok is False
    assert any("vendor mismatch" in r for r in result.reasons)


async def test_vendor_comparison_is_case_and_whitespace_insensitive() -> None:
    lookup = _FakePoLookup({"PO-1001": _po(vendor="  acme tedarik a.s.  ")})
    result = await validate_invoice(_fields(), po_lookup=lookup, seen_po_numbers=set())
    assert result.ok is True
