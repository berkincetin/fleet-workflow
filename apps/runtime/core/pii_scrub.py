"""Lightweight PII detection/masking for logs and chat-input scanning (TRD §8:
"Chat inputs scanned lightweight; detected identifiers masked in logs/traces
always").

Deliberately NOT `fleet_rag.ingest.pii` (Presidio + spaCy) — that module lives
in fleet-rag, which depends on fleet-runtime, not the reverse (apps/runtime
has no fleet-rag dependency, same boundary agents.dev_agent.graph/
agents.analytics.service already established for fleet-mcp), and Presidio's
NLP-backed analysis is too heavy to run synchronously on every log line and
every outgoing chat message. This is a cheap, regex-only pass covering the
same entity classes ingestion's Presidio recognizers cover (email, TR IBAN,
TR phone, TR TCKN with checksum) — good enough to catch the common cases for
logs/traces, not a replacement for the ingestion pipeline's full scan.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

_EMAIL_RE = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")
_TR_IBAN_RE = re.compile(r"\bTR\d{2}\d{5}\d{17}\b")
_TR_PHONE_RE = re.compile(r"\b(?:\+90|0)?5\d{2}[\s.-]?\d{3}[\s.-]?\d{2}[\s.-]?\d{2}\b")
_TCKN_CANDIDATE_RE = re.compile(r"\b\d{11}\b")


def _tckn_checksum_valid(digits: str) -> bool:
    if len(digits) != 11 or digits[0] == "0":
        return False
    nums = [int(c) for c in digits]
    odd_sum = sum(nums[0:9:2])
    even_sum = sum(nums[1:9:2])
    d10 = ((odd_sum * 7) - even_sum) % 10
    d11 = (sum(nums[:9]) + d10) % 10
    return nums[9] == d10 and nums[10] == d11


@dataclass(frozen=True)
class ScrubResult:
    text: str
    found: bool


def scrub(text: str) -> ScrubResult:
    """Mask every detected identifier in `text`; report whether anything was found."""
    found = False

    out = _EMAIL_RE.sub(lambda m: "[EMAIL]", text)
    if out != text:
        found = True
    text = out

    out = _TR_IBAN_RE.sub(lambda m: "[TR_IBAN]", text)
    if out != text:
        found = True
    text = out

    out = _TR_PHONE_RE.sub(lambda m: "[TR_PHONE]", text)
    if out != text:
        found = True
    text = out

    def _mask_tckn(m: re.Match[str]) -> str:
        nonlocal found
        if _tckn_checksum_valid(m.group(0)):
            found = True
            return "[TR_TCKN]"
        return m.group(0)

    text = _TCKN_CANDIDATE_RE.sub(_mask_tckn, text)

    return ScrubResult(text=text, found=found)


def has_pii(text: str) -> bool:
    return scrub(text).found
