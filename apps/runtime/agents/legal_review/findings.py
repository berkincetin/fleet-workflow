"""Clause-review output schema + the playbook-citation guardrail (task 12.2,
dept scenario 10 Legal Document Review).

The scenario's output contract is three fields per finding — clause, risk level,
playbook reference — and its eval bar is "planted risky-clause fixtures must be
caught **with a citation**". So a finding is only a finding if its playbook
reference resolves to a playbook excerpt that was actually retrieved on this
run. That is the same structural grounding check RAG answers get
(fleet_rag.query.answer._resolve_citations): the model cites by 1-indexed
position into the excerpts it was shown, and the position is resolved here
rather than trusted.

An uncited or unresolvable finding is **not** silently dropped — it is moved to
`uncited` and reported alongside. Counsel reading the review needs to know the
agent saw something it could not tie to a playbook; hiding it would turn a
citation guardrail into a recall bug. Only `findings` carries the advisory
claims, and every one of them is citable.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any

RISK_LEVELS = ("high", "medium", "low")

_CODE_FENCE_RE = re.compile(r"^```(?:json)?\s*(.*?)\s*```$", re.DOTALL)


def strip_code_fence(text: str) -> str:
    match = _CODE_FENCE_RE.match(text.strip())
    return match.group(1) if match else text


class FindingsParseError(Exception):
    """The model's review response was malformed."""


@dataclass(frozen=True)
class Finding:
    clause: str
    risk_level: str  # one of RISK_LEVELS
    playbook_ref: str  # chunk_ref of the playbook excerpt this rests on
    contract_excerpt: str = ""  # verbatim text from the contract under review
    rationale: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "clause": self.clause,
            "risk_level": self.risk_level,
            "playbook_ref": self.playbook_ref,
            "contract_excerpt": self.contract_excerpt,
            "rationale": self.rationale,
        }


@dataclass(frozen=True)
class Review:
    findings: list[Finding] = field(default_factory=list)
    uncited: list[dict[str, Any]] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "findings": [f.as_dict() for f in self.findings],
            "uncited": list(self.uncited),
        }


def parse_findings(content: str) -> list[dict[str, Any]]:
    """Parse the model's JSON response into raw finding dicts.

    Accepts either a bare list or `{"findings": [...]}` — a 7B local model is
    inconsistent about which of the two it emits, and both are unambiguous.
    """
    try:
        parsed = json.loads(strip_code_fence(content))
    except json.JSONDecodeError as exc:
        raise FindingsParseError(f"model did not return valid JSON: {content!r}") from exc

    if isinstance(parsed, dict):
        parsed = parsed.get("findings", [])
    if not isinstance(parsed, list):
        raise FindingsParseError(f"expected a list of findings, got {parsed!r}")
    return [item for item in parsed if isinstance(item, dict)]


def _normalize_risk(value: Any) -> str | None:
    """Map the model's risk word onto the closed vocabulary, or None."""
    if value is None:
        return None
    text = str(value).strip().lower()
    # TR synonyms the local model reaches for even when prompted in English.
    aliases = {
        "yüksek": "high", "yuksek": "high", "critical": "high", "severe": "high",
        "orta": "medium", "moderate": "medium",
        "düşük": "low", "dusuk": "low", "minor": "low",
    }
    text = aliases.get(text, text)
    return text if text in RISK_LEVELS else None


# Turkish letters folded to ASCII before casefolding. Python's casefold is not
# Turkish-aware ("İ" -> "i̇" with a combining dot, "I" -> "i" not "ı"), so a
# quote the model re-cased would silently fail to match its own contract and a
# valid finding would be dropped as ungrounded. Folding both sides first makes
# the containment check case-safe in Turkish.
_TR_FOLD = str.maketrans(
    {
        "ı": "i", "İ": "i", "I": "i", "i": "i",
        "ş": "s", "Ş": "s", "ğ": "g", "Ğ": "g",
        "ü": "u", "Ü": "u", "ö": "o", "Ö": "o", "ç": "c", "Ç": "c",
    }
)


def _normalize_for_match(text: str) -> str:
    """Collapse whitespace, Turkish case and diacritics for quote matching."""
    return " ".join(text.translate(_TR_FOLD).split()).casefold()


def _is_conforming(raw: dict[str, Any]) -> bool:
    """True when the model classified this clause as matching the STANDART.

    The `matches` verdict exists because the local model turned out to be good
    at the judgement and bad at acting on it: on a clean contract it would write
    a rationale literally saying *"bu cümle SAPMA kriterini karşılamaz"* (this
    sentence does not meet the deviation criterion) — and then emit the entry as
    a high-risk finding anyway. Asking for the verdict as its own field lets the
    model do the classification it is good at and lets code do the filtering it
    is bad at, which is the same division of labour as every other guardrail
    here. Anything other than an explicit "standart" is treated as a deviation,
    so a missing or garbled verdict fails toward *reporting* the clause.
    """
    return str(raw.get("matches", "") or "").strip().casefold() == "standart"


def build_review(
    raw_findings: list[dict[str, Any]],
    *,
    playbook_refs: list[str],
    contract_text: str | None = None,
) -> Review:
    """Validate the schema and ground every finding in both sources.

    `playbook_refs` is the ordered list of chunk_refs for the excerpts the model
    was shown; the model cites 1-indexed positions into it. A finding survives
    only if it has a clause, a risk level inside the closed vocabulary, a
    position that resolves, and — when `contract_text` is supplied — a
    `contract_excerpt` that actually appears in the contract.

    The contract-quote check exists because of a measured failure mode, not a
    hypothetical one: the local model would read a *conforming* clause, then
    restate the playbook's prohibition as its rationale and rate the clause
    high ("the contract says liability is capped at 12 months' fees, but per the
    playbook unlimited liability is high risk"). Making it quote the offending
    contract text verbatim forces the comparison to happen against the contract
    rather than against the rule alone, and gives counsel the clause to look at.
    """
    findings: list[Finding] = []
    uncited: list[dict[str, Any]] = []
    haystack = _normalize_for_match(contract_text) if contract_text is not None else None

    for raw in raw_findings:
        clause = str(raw.get("clause", "") or "").strip()
        risk = _normalize_risk(raw.get("risk_level"))
        position = _citation_position(raw.get("playbook_ref"))
        excerpt = str(raw.get("contract_excerpt", "") or "").strip()

        if not clause:
            continue  # nothing to report — not a dropped finding, an empty one
        if _is_conforming(raw):
            # The model classified this clause as matching the playbook's
            # STANDART. It is not a finding, and it is dropped silently rather
            # than reported as uncited — nothing went wrong here.
            continue

        reason: str | None = None
        if risk is None:
            reason = "risk level outside the vocabulary"
        elif position is None or not (1 <= position <= len(playbook_refs)):
            reason = "playbook reference does not resolve to a retrieved excerpt"
        elif haystack is not None and (
            not excerpt or _normalize_for_match(excerpt) not in haystack
        ):
            reason = "quoted clause does not appear in the contract under review"

        if reason is not None:
            uncited.append({"clause": clause, "risk_level": risk, "reason": reason})
            continue

        assert position is not None and risk is not None
        findings.append(
            Finding(
                clause=clause,
                risk_level=risk,
                playbook_ref=playbook_refs[position - 1],
                contract_excerpt=excerpt,
                rationale=str(raw.get("rationale", "") or "").strip(),
            )
        )

    return Review(findings=findings, uncited=uncited)


_POSITION_RE = re.compile(r"(\d+)")


def _citation_position(value: Any) -> int | None:
    """Read a 1-indexed excerpt position out of `3`, `"3"`, or `"[playbook:3]"`."""
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    match = _POSITION_RE.search(str(value))
    return int(match.group(1)) if match else None
