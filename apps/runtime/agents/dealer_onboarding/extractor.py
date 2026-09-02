"""Dealer-document OCR text -> structured dossier fields (task 12.1, dept
scenario 09 Dealer Onboarding).

**pii lane, no redaction, no downgrade.** An authorization certificate and a tax
registration carry exactly the identifiers the extraction is *for* — tax number
and IBAN — so unlike vehicle_intake (which scrubs the OCR text and sends a
redacted brief to the cloud) this extraction cannot redact its own payload. The
call is therefore made at `sensitivity="pii"`, which per core.llm.routing is
never downgraded even with `redacted=True`: only a model whose clearance covers
`pii` is eligible, i.e. the local lane. The raw certificate text never leaves
the machine.

Never-invent guardrail: a field the model cannot find must come back null. This
module enforces that structurally — an unparseable/empty value becomes `None`
and the dossier reports which required fields are missing, rather than trusting
the model to admit it guessed. A hallucinated tax number on a dealer file would
propagate into the CRM and into an outbound email, so the format validators
below reject anything that does not look like the real identifier.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Protocol

_CODE_FENCE_RE = re.compile(r"^```(?:json)?\s*(.*?)\s*```$", re.DOTALL)

# TR vergi kimlik numarası: 10 digits. TR IBAN: TR + 24 digits.
_TAX_NO_RE = re.compile(r"^\d{10}$")
_IBAN_RE = re.compile(r"^TR\d{24}$")


def _strip_code_fence(text: str) -> str:
    match = _CODE_FENCE_RE.match(text.strip())
    return match.group(1) if match else text


_SYSTEM_PROMPT = """You extract fields from a Turkish dealer application \
document (an authorization certificate "Yetki Belgesi" or a tax registration \
"Vergi Levhası"). The text comes from OCR, so it may contain noise.

Respond with exactly one JSON object and nothing else — no markdown, no commentary:
{
  "company_name": "<the company / trade name on the document, or null>",
  "tax_no": "<the 10-digit tax number (vergi kimlik no), digits only, or null>",
  "iban": "<the IBAN, e.g. TR000000000000000000000000, or null>",
  "certificate_no": "<the certificate/document number, or null>"
}

Use null for any field that is not clearly present in the text. NEVER invent or \
complete a company name, tax number, IBAN, or certificate number. Copy digits \
exactly as they appear; do not reformat, pad, or correct them."""


class ReasoningClient(Protocol):
    async def reasoning(self, messages: list[dict[str, Any]], **kwargs: Any) -> Any: ...


class ExtractionParseError(Exception):
    """The model's dossier response was malformed."""


@dataclass(frozen=True)
class DealerDossier:
    company_name: str | None
    tax_no: str | None
    iban: str | None
    certificate_no: str | None

    @property
    def missing_fields(self) -> list[str]:
        """Required identity fields the documents did not yield."""
        return [
            name
            for name, value in (
                ("company_name", self.company_name),
                ("tax_no", self.tax_no),
            )
            if value is None
        ]


def _clean(value: Any) -> str | None:
    if value in (None, "", "null", "None"):
        return None
    text = str(value).strip()
    return text or None


def _normalize_tax_no(value: Any) -> str | None:
    """Digits-only 10-char tax number, or None. OCR spaces/dots are dropped;
    anything that is still not 10 digits is rejected rather than padded."""
    raw = _clean(value)
    if raw is None:
        return None
    digits = re.sub(r"\D", "", raw)
    return digits if _TAX_NO_RE.match(digits) else None


def _normalize_iban(value: Any) -> str | None:
    raw = _clean(value)
    if raw is None:
        return None
    compact = re.sub(r"\s", "", raw).upper()
    return compact if _IBAN_RE.match(compact) else None


async def extract_dealer_dossier(
    *,
    ocr_text: str,
    llm_client: ReasoningClient,
    sensitivity: str = "pii",
    temperature: float = 0.0,
    **meta: Any,
) -> DealerDossier:
    """Extract dealer dossier fields from local-OCR text on the local lane.

    `sensitivity="pii"` is the whole point: routing refuses every cloud model
    for this call, so the certificate's tax number and IBAN are only ever seen
    by the local model. `temperature=0` because copying a tax number off a
    document is transcription, not generation — the same certificate must
    always yield the same digits.
    """
    messages = [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {"role": "user", "content": ocr_text},
    ]
    response = await llm_client.reasoning(
        messages, sensitivity=sensitivity, temperature=temperature, **meta
    )

    try:
        parsed = json.loads(_strip_code_fence(response.content))
    except json.JSONDecodeError as exc:
        raise ExtractionParseError(
            f"model did not return valid JSON: {response.content!r}"
        ) from exc
    if not isinstance(parsed, dict):
        raise ExtractionParseError(f"expected a JSON object, got {parsed!r}")

    return DealerDossier(
        company_name=_clean(parsed.get("company_name")),
        tax_no=_normalize_tax_no(parsed.get("tax_no")),
        iban=_normalize_iban(parsed.get("iban")),
        certificate_no=_clean(parsed.get("certificate_no")),
    )
