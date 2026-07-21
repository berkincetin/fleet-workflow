"""PII scan + per-collection policy (TRD §8 privacy/KVKK pipeline, task 3.1/3.2).

Runs Presidio (English generic recognizers) plus custom Turkish recognizers
(TCKN with checksum validation, TR IBAN, TR phone) against extracted text,
then applies the collection's `pii_policy`:

- ``redact``  — mask every finding in place, mark the chunk ``redacted=True``
  (the redaction-downgrade rule that lets it route to cloud models lives in
  ``core.llm.routing.effective_sensitivity`` — this module only produces the
  ``redacted`` flag it consumes).
- ``block``   — any finding drops the chunk entirely (empty text, ``blocked``).
- ``allow-local-only`` — text passes through unchanged, flagged
  ``local_only=True`` so the pipeline never lets it near a cloud embed/LLM call.

The Presidio ``AnalyzerEngine`` is built once at import time with an explicit
spacy model config — the default config wants to auto-download
``en_core_web_lg`` via spacy's pip-based downloader, which has no ``pip`` in a
uv-managed venv and hangs the process; ``en_core_web_sm`` is vendored as a
direct dependency instead (see apps/rag/pyproject.toml).
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Any

from presidio_analyzer import (
    AnalyzerEngine,
    EntityRecognizer,
    Pattern,
    PatternRecognizer,
    RecognizerResult,
)
from presidio_analyzer.nlp_engine import NlpEngineProvider

_TR_IBAN_PATTERN = Pattern(name="tr_iban", regex=r"\bTR\d{2}\d{5}\d{17}\b", score=0.9)
_TR_PHONE_PATTERN = Pattern(
    name="tr_phone", regex=r"\b(?:\+90|0)?5\d{2}[\s.-]?\d{3}[\s.-]?\d{2}[\s.-]?\d{2}\b", score=0.6
)
# Bare 11-digit run — checksum-validated in TckncRecognizer.analyze below.
_TCKN_CANDIDATE_PATTERN = Pattern(name="tr_tckn_candidate", regex=r"\b\d{11}\b", score=0.3)


def _tckn_checksum_valid(digits: str) -> bool:
    if len(digits) != 11 or digits[0] == "0":
        return False
    nums = [int(c) for c in digits]
    odd_sum = sum(nums[0:9:2])
    even_sum = sum(nums[1:9:2])
    d10 = ((odd_sum * 7) - even_sum) % 10
    d11 = (sum(nums[:9]) + d10) % 10
    return nums[9] == d10 and nums[10] == d11


class TckncRecognizer(PatternRecognizer):
    """TR national ID (TCKN) — 11 digits with a valid checksum (TRD §8)."""

    def __init__(self) -> None:
        super().__init__(
            supported_entity="TR_TCKN",
            patterns=[_TCKN_CANDIDATE_PATTERN],
            supported_language="en",
        )

    def analyze(
        self,
        text: str,
        entities: list[str],
        nlp_artifacts: Any | None = None,
        regex_flags: int | None = None,
    ) -> list[RecognizerResult]:
        results = super().analyze(text, entities, nlp_artifacts, regex_flags)
        return [r for r in results if _tckn_checksum_valid(text[r.start : r.end])]


@lru_cache(maxsize=1)
def _analyzer() -> AnalyzerEngine:
    config = {
        "nlp_engine_name": "spacy",
        "models": [{"lang_code": "en", "model_name": "en_core_web_sm"}],
    }
    nlp_engine = NlpEngineProvider(nlp_configuration=config).create_engine()
    engine = AnalyzerEngine(nlp_engine=nlp_engine, supported_languages=["en"])
    engine.registry.add_recognizer(
        PatternRecognizer(
            supported_entity="TR_IBAN", patterns=[_TR_IBAN_PATTERN], supported_language="en"
        )
    )
    engine.registry.add_recognizer(
        PatternRecognizer(
            supported_entity="TR_PHONE", patterns=[_TR_PHONE_PATTERN], supported_language="en"
        )
    )
    engine.registry.add_recognizer(TckncRecognizer())
    return engine


@dataclass(frozen=True)
class PiiFinding:
    entity_type: str
    start: int
    end: int
    score: float


def scan_text(text: str) -> list[PiiFinding]:
    """Run Presidio (generic + TR recognizers) and return every finding."""
    results = _analyzer().analyze(text=text, language="en")
    return [
        PiiFinding(entity_type=r.entity_type, start=r.start, end=r.end, score=r.score)
        for r in results
    ]


class PiiPolicyError(ValueError):
    def __init__(self, policy: str) -> None:
        super().__init__(f"unknown pii_policy: {policy}")


_KNOWN_POLICIES = {"redact", "block", "allow-local-only"}


@dataclass(frozen=True)
class PolicyResult:
    text: str
    redacted: bool
    blocked: bool
    local_only: bool = False


def _redact(text: str, findings: list[PiiFinding]) -> str:
    # Replace right-to-left so earlier offsets stay valid.
    for f in sorted(findings, key=lambda f: f.start, reverse=True):
        text = text[: f.start] + f"[{f.entity_type}]" + text[f.end :]
    return text


def apply_pii_policy(text: str, *, policy: str) -> PolicyResult:
    """Scan `text` and apply the collection's pii_policy (TRD §8)."""
    if policy not in _KNOWN_POLICIES:
        raise PiiPolicyError(policy)

    findings = scan_text(text)

    if policy == "allow-local-only":
        return PolicyResult(text=text, redacted=False, blocked=False, local_only=True)

    if policy == "block":
        if findings:
            return PolicyResult(text="", redacted=False, blocked=True)
        return PolicyResult(text=text, redacted=False, blocked=False)

    # redact (default)
    if not findings:
        return PolicyResult(text=text, redacted=False, blocked=False)
    return PolicyResult(text=_redact(text, findings), redacted=True, blocked=False)


__all__ = [
    "EntityRecognizer",
    "PiiFinding",
    "PiiPolicyError",
    "PolicyResult",
    "apply_pii_policy",
    "scan_text",
]
