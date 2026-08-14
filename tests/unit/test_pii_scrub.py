"""core.pii_scrub: lightweight regex PII masking for logs/traces (task 8.4,
TRD §8 "detected identifiers masked in logs/traces always").
"""

from __future__ import annotations

from core.pii_scrub import has_pii, scrub


def test_scrub_masks_email() -> None:
    result = scrub("Contact me at jane@example.com for details.")
    assert result.found is True
    assert "jane@example.com" not in result.text
    assert "[EMAIL]" in result.text


def test_scrub_masks_tr_iban() -> None:
    result = scrub("Please pay to TR330006100519786457841326.")
    assert result.found is True
    assert "TR330006100519786457841326" not in result.text
    assert "[TR_IBAN]" in result.text


def test_scrub_masks_tr_phone() -> None:
    result = scrub("Call me at +90 555 111 2233.")
    assert result.found is True
    assert "[TR_PHONE]" in result.text


def test_scrub_masks_valid_tckn() -> None:
    result = scrub("Kimlik no: 10000000146")
    assert result.found is True
    assert "10000000146" not in result.text
    assert "[TR_TCKN]" in result.text


def test_scrub_does_not_mask_invalid_tckn_checksum() -> None:
    result = scrub("Order number: 12345678900")
    assert "12345678900" in result.text


def test_scrub_no_pii_returns_unchanged_text() -> None:
    result = scrub("Please review the attached document before the meeting.")
    assert result.found is False
    assert result.text == "Please review the attached document before the meeting."


def test_has_pii_true_and_false() -> None:
    assert has_pii("email me at a@b.com") is True
    assert has_pii("no identifiers here") is False
