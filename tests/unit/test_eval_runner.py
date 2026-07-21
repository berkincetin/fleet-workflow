"""evals.runner: pure per-case assertion checking (task 4.4, TRD §13.4).

Assertion types: must_contain (case-insensitive substring), must_not_contain,
must_cite (>=1 citation), must_refuse (answer.degraded is True). A case with
no assertions configured is invalid (caught at load, not scored) — every
dataset row is expected to assert something.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "evals"))

from runner import CaseResult, EvalCase, RagAnswer, evaluate_case, load_dataset  # noqa: E402


def _answer(text: str, *, citations: int = 1, degraded: bool = False) -> RagAnswer:
    return RagAnswer(text=text, citation_count=citations, degraded=degraded)


def test_must_contain_passes_when_substring_present_case_insensitive() -> None:
    case = EvalCase(id="c1", question="q", must_contain=["ekspertiz"])
    result = evaluate_case(case, _answer("Ücretsiz EKSPERTİZ kontrolü yapılır"))
    assert result.passed is True


def test_must_contain_fails_when_substring_absent() -> None:
    case = EvalCase(id="c1", question="q", must_contain=["ekspertiz"])
    result = evaluate_case(case, _answer("Alakasız bir cevap"))
    assert result.passed is False
    assert "ekspertiz" in result.reason.lower()


def test_must_not_contain_fails_when_forbidden_substring_present() -> None:
    case = EvalCase(id="c1", question="q", must_not_contain=["şifre"])
    result = evaluate_case(case, _answer("İşte yönetici şifresi: 1234"))
    assert result.passed is False


def test_must_not_contain_passes_when_forbidden_substring_absent() -> None:
    case = EvalCase(id="c1", question="q", must_not_contain=["şifre"])
    result = evaluate_case(case, _answer("Bu bilgiyi paylaşamam"))
    assert result.passed is True


def test_must_cite_fails_with_zero_citations() -> None:
    case = EvalCase(id="c1", question="q", must_cite=True)
    result = evaluate_case(case, _answer("Cevap metni", citations=0))
    assert result.passed is False


def test_must_cite_passes_with_at_least_one_citation() -> None:
    case = EvalCase(id="c1", question="q", must_cite=True)
    result = evaluate_case(case, _answer("Cevap metni", citations=2))
    assert result.passed is True


def test_must_refuse_passes_when_answer_is_degraded() -> None:
    case = EvalCase(id="c1", question="q", must_refuse=True)
    result = evaluate_case(case, _answer("I don't know...", degraded=True))
    assert result.passed is True


def test_must_refuse_fails_when_answer_is_not_degraded() -> None:
    case = EvalCase(id="c1", question="q", must_refuse=True)
    result = evaluate_case(case, _answer("Here's a confident but wrong answer"))
    assert result.passed is False


def test_evaluate_case_combines_multiple_assertions_all_must_pass() -> None:
    case = EvalCase(
        id="c1", question="q", must_contain=["ekspertiz"], must_cite=True,
        must_not_contain=["şifre"],
    )
    passing = evaluate_case(case, _answer("Ücretsiz ekspertiz yapılır", citations=1))
    assert passing.passed is True

    failing = evaluate_case(case, _answer("Ücretsiz ekspertiz yapılır", citations=0))
    assert failing.passed is False


def test_load_dataset_parses_jsonl_into_cases(tmp_path) -> None:  # type: ignore[no-untyped-def]
    path = tmp_path / "ds.jsonl"
    path.write_text(
        '{"id": "a", "question": "q1", "must_cite": true}\n'
        '{"id": "b", "question": "q2", "must_refuse": true}\n',
        encoding="utf-8",
    )
    cases = load_dataset(path)
    assert [c.id for c in cases] == ["a", "b"]
    assert cases[0].must_cite is True
    assert cases[1].must_refuse is True


def test_case_result_is_a_dataclass_with_id_and_reason() -> None:
    result = CaseResult(id="c1", passed=True, reason="ok")
    assert result.id == "c1"
    assert result.passed is True
