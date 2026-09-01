"""agents.hr_agent.match: hr.match_role scoring (task 8.5, dept scenario 05
"match reasoning must reference only job-relevant criteria").
"""

from __future__ import annotations

from agents.hr_agent.extractor import CvProfile
from agents.hr_agent.match import score_role_match


def _profile(**overrides: object) -> CvProfile:
    base = {
        "full_name": "Ayse Yilmaz",
        "email": "ayse@example.com",
        "phone": "+90 555 111 2233",
        "education": ["BSc Computer Engineering, ODTU, 2019"],
        "experience": ["Software Engineer, Acme A.S., 2019-2022"],
        "skills": ["Python", "SQL", "Docker"],
    }
    base.update(overrides)
    return CvProfile(**base)  # type: ignore[arg-type]


def test_score_role_match_all_criteria_matched() -> None:
    result = score_role_match(_profile(), criteria=["Python", "SQL"])
    assert result.score == 1.0
    assert result.matched_criteria == ["Python", "SQL"]
    assert result.missing_criteria == []


def test_score_role_match_partial() -> None:
    result = score_role_match(_profile(), criteria=["Python", "Kubernetes"])
    assert result.score == 0.5
    assert result.matched_criteria == ["Python"]
    assert result.missing_criteria == ["Kubernetes"]


def test_score_role_match_none_matched() -> None:
    result = score_role_match(_profile(), criteria=["Rust", "Kubernetes"])
    assert result.score == 0.0
    assert result.matched_criteria == []


def test_score_role_match_matches_experience_and_education_too() -> None:
    result = score_role_match(_profile(), criteria=["ODTU", "Acme"])
    assert result.score == 1.0


def test_score_role_match_no_criteria_returns_zero() -> None:
    result = score_role_match(_profile(), criteria=[])
    assert result.score == 0.0


def test_score_role_match_case_and_diacritic_insensitive() -> None:
    result = score_role_match(
        _profile(skills=["Makine Ogrenmesi"]), criteria=["makine öğrenmesi"]
    )
    assert result.score == 1.0


def test_reasoning_never_mentions_protected_attributes() -> None:
    """Guardrail: reasoning is built exclusively from the caller-supplied
    criteria list — never from anything on CvProfile that could carry a
    protected attribute (which the schema doesn't even have, task 8.2)."""
    result = score_role_match(_profile(), criteria=["Python", "SQL"])
    for term in ("age", "gender", "photo", "birthdate", "marital"):
        assert term not in result.reasoning.lower()
