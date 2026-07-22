"""evals.runner: Invoice Agent eval assertion checking (task 6.3, dept
scenario 04). Invoice answers are a full graph run outcome (blocked/
pending_approval + extracted fields + validation result), not a RAG/
Analytics/DevAgent-shaped answer, so they get their own InvoiceCase/Answer/
evaluate shapes. Assertion types match the department scenario's literal
evals: field extraction accuracy (vendor/po_number/amount must match
exactly, amount within a small float tolerance), and validation outcome
(mismatch/duplicate/unknown-PO fixtures must flag — never silently pass —
optionally checking the flagged reason mentions the right thing).
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "evals"))

from runner import (  # noqa: E402
    InvoiceAnswer,
    InvoiceCase,
    _vendor_reasonably_matches,
    evaluate_invoice_case,
    load_invoice_dataset,
)


def _case(**over: object) -> InvoiceCase:
    base: dict[str, object] = dict(
        id="i1", vendor="Acme Tedarik A.S.", po_number="PO-1001", amount="1250.00",
        expect_vendor="Acme Tedarik A.S.", expect_po_number="PO-1001",
        expect_amount=1250.0, expect_validation_ok=True,
    )
    base.update(over)
    return InvoiceCase(**base)  # type: ignore[arg-type]


def test_matching_invoice_passes_when_fields_and_validation_are_correct() -> None:
    case = _case()
    answer = InvoiceAnswer(
        pending_approval=True, extracted_vendor="Acme Tedarik A.S.",
        extracted_po_number="PO-1001", extracted_amount=1250.0, validation_ok=True,
    )
    assert evaluate_invoice_case(case, answer).passed is True


def test_fails_when_run_never_reached_pending_approval() -> None:
    case = _case()
    answer = InvoiceAnswer(blocked_reason="field extraction failed: bad json")
    assert evaluate_invoice_case(case, answer).passed is False


def test_fails_on_vendor_extraction_mismatch() -> None:
    case = _case()
    answer = InvoiceAnswer(
        pending_approval=True, extracted_vendor="Wrong Vendor",
        extracted_po_number="PO-1001", extracted_amount=1250.0, validation_ok=True,
    )
    assert evaluate_invoice_case(case, answer).passed is False


def test_fails_on_po_number_extraction_mismatch() -> None:
    case = _case()
    answer = InvoiceAnswer(
        pending_approval=True, extracted_vendor="Acme Tedarik A.S.",
        extracted_po_number="PO-9999", extracted_amount=1250.0, validation_ok=True,
    )
    assert evaluate_invoice_case(case, answer).passed is False


def test_fails_on_amount_extraction_mismatch_beyond_tolerance() -> None:
    case = _case()
    answer = InvoiceAnswer(
        pending_approval=True, extracted_vendor="Acme Tedarik A.S.",
        extracted_po_number="PO-1001", extracted_amount=9999.0, validation_ok=True,
    )
    assert evaluate_invoice_case(case, answer).passed is False


def test_small_amount_extraction_rounding_within_tolerance_passes() -> None:
    case = _case()
    answer = InvoiceAnswer(
        pending_approval=True, extracted_vendor="Acme Tedarik A.S.",
        extracted_po_number="PO-1001", extracted_amount=1250.005, validation_ok=True,
    )
    assert evaluate_invoice_case(case, answer).passed is True


def test_mismatch_fixture_passes_only_when_flagged_never_when_clean() -> None:
    case = _case(
        amount="9999.00", expect_amount=9999.0, expect_validation_ok=False,
        expect_reason_contains="amount mismatch",
    )
    flagged = InvoiceAnswer(
        pending_approval=True, extracted_vendor="Acme Tedarik A.S.",
        extracted_po_number="PO-1001", extracted_amount=9999.0, validation_ok=False,
        validation_reasons=["amount mismatch: invoice 9999.0 TRY vs PO 1250.0 TRY"],
    )
    assert evaluate_invoice_case(case, flagged).passed is True

    silently_clean = InvoiceAnswer(
        pending_approval=True, extracted_vendor="Acme Tedarik A.S.",
        extracted_po_number="PO-1001", extracted_amount=9999.0, validation_ok=True,
    )
    assert evaluate_invoice_case(case, silently_clean).passed is False


def test_duplicate_fixture_passes_only_when_flagged() -> None:
    case = _case(expect_validation_ok=False, expect_reason_contains="duplicate")
    flagged = InvoiceAnswer(
        pending_approval=True, extracted_vendor="Acme Tedarik A.S.",
        extracted_po_number="PO-1001", extracted_amount=1250.0, validation_ok=False,
        validation_reasons=["duplicate: PO 'PO-1001' already processed"],
    )
    assert evaluate_invoice_case(case, flagged).passed is True


def test_vendor_fuzzy_match_tolerates_turkish_diacritic_ocr_noise() -> None:
    """Caught live: a small local vision model reading small rendered Turkish
    text produces real, minor diacritic slips (ı/i, ş/s, ç/c) — this is OCR
    noise, not an extraction failure, and byte-identical matching was
    keeping a correct agent's eval pass rate under threshold on spelling
    alone (docs/PROGRESS.md 6.3)."""
    assert _vendor_reasonably_matches("Yildiz Danismanlik", "Yıldız Danışmanlık") is True
    assert _vendor_reasonably_matches("Sakarya Matbaacilik", "Sakarya Matbaacılık") is True
    assert _vendor_reasonably_matches("Firat Enerji", "Fırat Enerji") is True
    assert _vendor_reasonably_matches("Acme Tedarik A.S", "Acme Tedarik A.S.") is True


def test_vendor_fuzzy_match_rejects_a_genuinely_different_vendor() -> None:
    assert _vendor_reasonably_matches("Wrong Vendor Name", "Acme Tedarik A.S.") is False


def test_vendor_fuzzy_match_rejects_real_ocr_garbling_beyond_noise() -> None:
    """A genuinely mangled read (missing/extra word, unrecognizable
    substitution) must still fail — fuzzy matching tolerates spelling noise,
    not a wrong extraction."""
    assert _vendor_reasonably_matches("Boğaziçi Danna Demanlık", "Boğaziçi Danışmanlık") is False


def test_vendor_fuzzy_match_requires_same_word_count() -> None:
    assert _vendor_reasonably_matches("Acme", "Acme Tedarik A.S.") is False


def test_load_invoice_dataset_parses_jsonl() -> None:
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "ds.jsonl"
        path.write_text(
            '{"id": "i1", "vendor": "Acme", "po_number": "PO-1001", "amount": "1250.00", '
            '"expect_vendor": "Acme", "expect_po_number": "PO-1001", "expect_amount": 1250.0, '
            '"expect_validation_ok": true}\n'
            '{"id": "i2", "vendor": "Acme", "po_number": "PO-1001", "amount": "9999.00", '
            '"expect_vendor": "Acme", "expect_po_number": "PO-1001", "expect_amount": 9999.0, '
            '"expect_validation_ok": false, "expect_reason_contains": "amount mismatch"}\n',
            encoding="utf-8",
        )
        cases = load_invoice_dataset(path)
    assert [c.id for c in cases] == ["i1", "i2"]
    assert cases[0].expect_validation_ok is True
    assert cases[1].expect_reason_contains == "amount mismatch"
