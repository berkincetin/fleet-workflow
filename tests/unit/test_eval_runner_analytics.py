"""evals.runner: Analytics eval assertion checking (task 5.2, dept scenario 02).

Analytics answers are SQL + a result set, not a RAG citation-grounded answer,
so they get their own EvalCase/Answer/evaluate shapes (AnalyticsCase,
AnalyticsAnswer, evaluate_analytics_case) rather than overloading the
RAG-specific evaluate_case. Assertion types match the department scenario's
literal AC: result-set match (row count, since the fixture warehouse is
deterministic and seeded once — exact-row-count is a real result-set
assertion, not a string match on the SQL text), refusal (non-allowlisted
table), and must_clarify (ambiguous question).
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "evals"))

from runner import (  # noqa: E402
    AnalyticsAnswer,
    AnalyticsCase,
    evaluate_analytics_case,
    load_analytics_dataset,
)


def test_expect_row_count_passes_on_exact_match() -> None:
    case = AnalyticsCase(id="a1", question="q", expect_row_count=500)
    result = evaluate_analytics_case(
        case, AnalyticsAnswer(sql="SELECT * FROM fixture_sales", row_count=500)
    )
    assert result.passed is True


def test_expect_row_count_fails_on_mismatch() -> None:
    case = AnalyticsCase(id="a1", question="q", expect_row_count=500)
    result = evaluate_analytics_case(
        case, AnalyticsAnswer(sql="SELECT * FROM fixture_sales", row_count=10)
    )
    assert result.passed is False


def test_must_refuse_passes_when_answer_was_refused() -> None:
    case = AnalyticsCase(id="a2", question="q", must_refuse=True)
    result = evaluate_analytics_case(case, AnalyticsAnswer(refused=True))
    assert result.passed is True


def test_must_refuse_fails_when_answer_was_not_refused() -> None:
    case = AnalyticsCase(id="a2", question="q", must_refuse=True)
    result = evaluate_analytics_case(case, AnalyticsAnswer(sql="SELECT 1", row_count=1))
    assert result.passed is False


def test_must_refuse_or_clarify_passes_on_either_outcome() -> None:
    case = AnalyticsCase(id="a5", question="q", must_refuse_or_clarify=True)
    assert evaluate_analytics_case(case, AnalyticsAnswer(refused=True)).passed is True
    assert evaluate_analytics_case(
        case, AnalyticsAnswer(clarification="which table?")
    ).passed is True


def test_must_refuse_or_clarify_fails_when_sql_was_generated() -> None:
    case = AnalyticsCase(id="a5", question="q", must_refuse_or_clarify=True)
    result = evaluate_analytics_case(case, AnalyticsAnswer(sql="SELECT 1", row_count=1))
    assert result.passed is False


def test_must_clarify_passes_when_answer_asked_to_clarify() -> None:
    case = AnalyticsCase(id="a3", question="q", must_clarify=True)
    result = evaluate_analytics_case(case, AnalyticsAnswer(clarification="Which region?"))
    assert result.passed is True


def test_must_clarify_fails_when_answer_guessed_instead() -> None:
    case = AnalyticsCase(id="a3", question="q", must_clarify=True)
    result = evaluate_analytics_case(case, AnalyticsAnswer(sql="SELECT 1", row_count=1))
    assert result.passed is False


def test_sql_must_reference_table_passes_when_present() -> None:
    case = AnalyticsCase(id="a4", question="q", sql_must_reference_table="fixture_orders")
    result = evaluate_analytics_case(
        case, AnalyticsAnswer(sql="SELECT * FROM fixture_orders", row_count=500)
    )
    assert result.passed is True


def test_sql_must_reference_table_fails_when_absent() -> None:
    case = AnalyticsCase(id="a4", question="q", sql_must_reference_table="fixture_orders")
    result = evaluate_analytics_case(
        case, AnalyticsAnswer(sql="SELECT * FROM fixture_sales", row_count=500)
    )
    assert result.passed is False


def test_load_analytics_dataset_parses_jsonl() -> None:
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "ds.jsonl"
        path.write_text(
            '{"id": "a1", "question": "q1", "expect_row_count": 500}\n'
            '{"id": "a2", "question": "q2", "must_refuse": true}\n',
            encoding="utf-8",
        )
        cases = load_analytics_dataset(path)
    assert [c.id for c in cases] == ["a1", "a2"]
    assert cases[0].expect_row_count == 500
    assert cases[1].must_refuse is True
