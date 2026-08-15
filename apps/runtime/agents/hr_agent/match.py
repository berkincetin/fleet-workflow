"""hr.match_role: score a CvProfile against job-relevant criteria (task 8.5,
dept scenario 05 "Tools: hr.match_role (read — scoring service over structured
profiles)").

Pure, no I/O — deterministic keyword overlap between the candidate's skills/
experience/education and the role's required criteria. No LLM call: the
guardrail "match reasoning must reference only job-relevant criteria" is
enforced structurally here too, the same way task 8.2's protected-attribute
exclusion is — `MatchResult.reasoning` is built exclusively from the
`criteria` list and the matched/missing subsets of it, so there is no code
path through which an age/gender/photo/birthdate reference (which `CvProfile`
doesn't even carry, per task 8.2) could end up in it.
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass, field

from agents.hr_agent.extractor import CvProfile


def _fold(text: str) -> str:
    lowered = text.lower()
    return "".join(
        c for c in unicodedata.normalize("NFD", lowered) if unicodedata.category(c) != "Mn"
    )


@dataclass(frozen=True)
class MatchResult:
    score: float  # 0.0-1.0: fraction of criteria matched
    matched_criteria: list[str] = field(default_factory=list)
    missing_criteria: list[str] = field(default_factory=list)
    reasoning: str = ""


def score_role_match(profile: CvProfile, *, criteria: list[str]) -> MatchResult:
    """`criteria` is the role's required skills/qualifications (dept scenario
    05's "job-relevant criteria" — e.g. ["Python", "SQL", "5+ years"]).
    A criterion counts as matched if it appears (case/diacritic-insensitive
    substring) in the candidate's skills, experience, or education text."""
    if not criteria:
        return MatchResult(score=0.0, reasoning="no criteria provided")

    candidate_text = _fold(
        " ".join(profile.skills) + " " + " ".join(profile.experience) + " "
        + " ".join(profile.education)
    )

    matched = [c for c in criteria if _fold(c) in candidate_text]
    missing = [c for c in criteria if c not in matched]
    score = len(matched) / len(criteria)

    if matched and missing:
        reasoning = f"Matches {', '.join(matched)}; missing {', '.join(missing)}."
    elif matched:
        reasoning = f"Matches all required criteria: {', '.join(matched)}."
    else:
        reasoning = f"Matches none of the required criteria: {', '.join(criteria)}."

    return MatchResult(
        score=score, matched_criteria=matched, missing_criteria=missing, reasoning=reasoning
    )
