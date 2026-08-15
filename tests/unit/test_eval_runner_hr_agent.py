"""evals.runner: HR Agent eval assertion checking (task 8.5, dept scenario 05).
Three case types in one dataset: extraction (field accuracy), schema_exclusion
(protected attributes must never leak into the extracted profile even though
they're on the raw CV text), qa_grounding (reuses the generic RAG
EvalCase/evaluate_case path, tested separately in test_eval_runner.py).
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "evals"))

from runner import (  # noqa: E402
    HrAgentCase,
    _evaluate_hr_extraction_case,
    _evaluate_hr_schema_exclusion_case,
    load_hr_agent_dataset,
)


@dataclass
class _FakeProfile:
    full_name: str = "Ayse Yilmaz"
    email: str = "ayse.yilmaz@example.com"
    phone: str = "+90 555 111 2233"
    education: list[str] = field(default_factory=lambda: ["BSc Computer Engineering, ODTU"])
    experience: list[str] = field(default_factory=lambda: ["Software Engineer, Acme A.S."])
    skills: list[str] = field(default_factory=lambda: ["Python", "SQL"])


def _case(**over: object) -> HrAgentCase:
    base: dict[str, object] = dict(id="hr1", case_type="extraction")
    base.update(over)
    return HrAgentCase(**base)  # type: ignore[arg-type]


def test_extraction_case_passes_when_fields_match() -> None:
    case = _case(
        expect_full_name="Ayse Yilmaz", expect_email="ayse.yilmaz@example.com",
        expect_phone="+90 555 111 2233", expect_education_contains="ODTU",
        expect_experience_contains="Acme", expect_skill="Python",
    )
    assert _evaluate_hr_extraction_case(case, _FakeProfile()).passed is True


def test_extraction_case_fails_on_name_mismatch() -> None:
    case = _case(expect_full_name="Someone Else")
    assert _evaluate_hr_extraction_case(case, _FakeProfile()).passed is False


def test_extraction_case_tolerates_turkish_diacritic_ocr_noise() -> None:
    """Same class of real OCR noise the invoice eval hit — small local vision/
    OCR reads of Turkish text produce minor diacritic slips."""
    case = _case(expect_full_name="Ayşe Yılmaz")
    assert _evaluate_hr_extraction_case(case, _FakeProfile()).passed is True


def test_extraction_case_only_checks_fields_with_an_expectation() -> None:
    case = _case(expect_skill="Python")  # everything else left None
    assert _evaluate_hr_extraction_case(case, _FakeProfile()).passed is True


def test_schema_exclusion_case_passes_when_profile_has_no_protected_data() -> None:
    case = _case(
        case_type="schema_exclusion", birthdate_value="1990-04-12", gender_value="Kadin",
    )
    assert _evaluate_hr_schema_exclusion_case(case, _FakeProfile()).passed is True


def test_schema_exclusion_case_fails_if_birthdate_leaked_into_a_field() -> None:
    """Guards against a future extractor regression that starts stuffing a
    protected value into e.g. the skills list — the check scans every field,
    not just a dedicated (nonexistent) birthdate attribute."""
    case = _case(case_type="schema_exclusion", birthdate_value="1990-04-12")
    leaky_profile = _FakeProfile(skills=["Python", "born 1990-04-12"])
    result = _evaluate_hr_schema_exclusion_case(case, leaky_profile)
    assert result.passed is False
    assert "1990-04-12" in result.reason


def test_load_hr_agent_dataset_parses_all_three_case_types() -> None:
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "ds.jsonl"
        path.write_text(
            '{"id": "e1", "case_type": "extraction", "cv_lines": ["Ayse Yilmaz"], '
            '"expect_full_name": "Ayse Yilmaz"}\n'
            '{"id": "s1", "case_type": "schema_exclusion", "cv_lines": ["X"], '
            '"birthdate_value": "1990-01-01"}\n'
            '{"id": "q1", "case_type": "qa_grounding", "question": "How many days?", '
            '"must_contain": ["14"], "must_cite": true}\n',
            encoding="utf-8",
        )
        cases = load_hr_agent_dataset(path)
    assert [c.id for c in cases] == ["e1", "s1", "q1"]
    assert cases[0].expect_full_name == "Ayse Yilmaz"
    assert cases[1].birthdate_value == "1990-01-01"
    assert cases[2].must_contain == ["14"]
    assert cases[2].must_cite is True
