"""Invoice text -> structured fields (task 6.3, dept scenario 04 "extracted
fields" step, TRD §4.3 reasoning tier — field extraction from unstructured
OCR text is a judgment/generation call-site per CLAUDE.md rule 10).

The model reads OCR'd invoice text (already extracted by `ocr.extract_text`,
Sprint 3/5.1 — this module never touches an image) and answers with the
fields dept scenario 04's evals need: vendor, PO number, amount, currency.
Same markdown-code-fence-stripping defense as agents.dev_agent.planner /
agents.analytics.sql_generator — the same class of model behavior recurred a
third time in this codebase, always caught live rather than anticipated.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Protocol

_SYSTEM_PROMPT = """You are an invoice field extraction assistant. Given OCR'd \
invoice text (which may contain OCR noise/errors), extract the following fields.

Respond with exactly one JSON object and nothing else — no markdown code fences, no commentary:
{
  "vendor": "<vendor/supplier name as written on the invoice>",
  "po_number": "<purchase order number referenced on the invoice, e.g. 'PO-1001'>",
  "amount": <total amount as a number, no currency symbol or thousands separators>,
  "currency": "<3-letter currency code, e.g. 'TRY', 'USD'>"
}

If a field cannot be determined from the text, use an empty string (or 0 for amount).
"""

_CODE_FENCE_RE = re.compile(r"^```(?:json)?\s*(.*?)\s*```$", re.DOTALL)


def _strip_code_fence(text: str) -> str:
    match = _CODE_FENCE_RE.match(text.strip())
    return match.group(1) if match else text


class ExtractionParseError(Exception):
    """The model's field-extraction response was malformed or missing a field."""


class ReasoningClient(Protocol):
    async def reasoning(self, messages: list[dict[str, Any]], **kwargs: Any) -> Any: ...


@dataclass(frozen=True)
class InvoiceFields:
    vendor: str
    po_number: str
    amount: float
    currency: str


_REQUIRED_FIELDS = ("vendor", "po_number", "amount", "currency")


async def extract_invoice_fields(
    *,
    ocr_text: str,
    llm_client: ReasoningClient,
    sensitivity: str = "confidential",
    **meta: Any,
) -> InvoiceFields:
    messages = [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {"role": "user", "content": ocr_text},
    ]
    response = await llm_client.reasoning(messages, sensitivity=sensitivity, **meta)

    try:
        parsed = json.loads(_strip_code_fence(response.content))
    except json.JSONDecodeError as exc:
        raise ExtractionParseError(
            f"model did not return valid JSON: {response.content!r}"
        ) from exc

    missing = [f for f in _REQUIRED_FIELDS if f not in parsed]
    if missing:
        raise ExtractionParseError(f"extraction response missing field(s): {missing}")

    try:
        amount = float(parsed["amount"])
    except (TypeError, ValueError) as exc:
        raise ExtractionParseError(f"amount is not numeric: {parsed['amount']!r}") from exc

    return InvoiceFields(
        vendor=str(parsed["vendor"]),
        po_number=str(parsed["po_number"]),
        amount=amount,
        currency=str(parsed["currency"]),
    )
