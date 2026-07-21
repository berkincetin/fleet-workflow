"""PII pipeline: scan + per-collection policy (TRD §8).

Policy `redact` masks findings and marks the chunk `redacted=True` (which
downstream routing treats as effective sensitivity `internal`, tested in
test_sensitivity_routing.py — this module only owns the scan+policy step).
Policy `block` drops the chunk entirely. Policy `allow-local-only` keeps the
original text untouched but flags the chunk for the local-model lane.
"""

from __future__ import annotations

from fleet_rag.ingest.pii import PiiPolicyError, apply_pii_policy, scan_text


def test_scan_text_finds_turkish_iban() -> None:
    findings = scan_text("Please pay to TR330006100519786457841326.")
    assert any(f.entity_type == "TR_IBAN" for f in findings)


def test_scan_text_finds_turkish_tckn() -> None:
    # A validity-checksum-passing TCKN (test fixture number).
    findings = scan_text("Kimlik no: 10000000146")
    assert any(f.entity_type == "TR_TCKN" for f in findings)


def test_scan_text_rejects_invalid_tckn_checksum() -> None:
    findings = scan_text("Kimlik no: 12345678900")
    assert not any(f.entity_type == "TR_TCKN" for f in findings)


def test_scan_text_finds_email() -> None:
    findings = scan_text("Contact me at jane@example.com for details.")
    assert any(f.entity_type == "EMAIL_ADDRESS" for f in findings)


def test_scan_text_no_pii_returns_empty() -> None:
    assert scan_text("Please review the attached document before the meeting.") == []


def test_redact_policy_masks_findings_and_marks_redacted() -> None:
    result = apply_pii_policy(
        "Contact me at jane@example.com please.", policy="redact"
    )
    assert "jane@example.com" not in result.text
    assert result.redacted is True
    assert result.blocked is False


def test_redact_policy_with_no_findings_leaves_text_unchanged_and_not_redacted() -> None:
    result = apply_pii_policy("No sensitive content here.", policy="redact")
    assert result.text == "No sensitive content here."
    assert result.redacted is False


def test_block_policy_with_findings_blocks_the_chunk() -> None:
    result = apply_pii_policy("Email: jane@example.com", policy="block")
    assert result.blocked is True
    assert result.text == ""


def test_block_policy_with_no_findings_passes_through() -> None:
    result = apply_pii_policy("Nothing sensitive.", policy="block")
    assert result.blocked is False
    assert result.text == "Nothing sensitive."


def test_allow_local_only_policy_keeps_original_text() -> None:
    result = apply_pii_policy("Email: jane@example.com", policy="allow-local-only")
    assert result.text == "Email: jane@example.com"
    assert result.redacted is False
    assert result.blocked is False
    assert result.local_only is True


def test_unknown_policy_raises() -> None:
    try:
        apply_pii_policy("text", policy="bogus")
    except PiiPolicyError as exc:
        assert "bogus" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("expected PiiPolicyError")
