"""Budget decision logic (task 2.4, TRD §5).

Pure evaluation of spend against a budget: under the soft limit → allow; at/above
the soft % but under 100% → allow with a soft-limit flag; at/over 100% → hard
stop. These drive the pre-check that runs before every LLM call (CLAUDE.md rule
6) and the soft flag surfaced in response metadata.
"""

from __future__ import annotations

from core.llm.budget import BudgetExceeded, evaluate_budget


def test_under_soft_limit_is_allowed_and_not_flagged() -> None:
    status = evaluate_budget(spent_usd=10.0, limit_usd=100.0, soft_pct=80)
    assert status.allowed is True
    assert status.soft_exceeded is False
    assert status.hard_exceeded is False


def test_at_soft_limit_sets_soft_flag_but_still_allowed() -> None:
    status = evaluate_budget(spent_usd=80.0, limit_usd=100.0, soft_pct=80)
    assert status.allowed is True
    assert status.soft_exceeded is True
    assert status.hard_exceeded is False


def test_between_soft_and_hard_is_allowed_and_flagged() -> None:
    status = evaluate_budget(spent_usd=95.0, limit_usd=100.0, soft_pct=80)
    assert status.allowed is True
    assert status.soft_exceeded is True


def test_at_hard_limit_is_blocked() -> None:
    status = evaluate_budget(spent_usd=100.0, limit_usd=100.0, soft_pct=80)
    assert status.allowed is False
    assert status.hard_exceeded is True


def test_over_hard_limit_is_blocked() -> None:
    status = evaluate_budget(spent_usd=140.0, limit_usd=100.0, soft_pct=80)
    assert status.allowed is False
    assert status.hard_exceeded is True


def test_no_budget_row_is_unlimited() -> None:
    # limit_usd None → no budget configured for the scope → always allowed.
    status = evaluate_budget(spent_usd=1_000.0, limit_usd=None, soft_pct=80)
    assert status.allowed is True
    assert status.soft_exceeded is False


def test_utilization_reported() -> None:
    status = evaluate_budget(spent_usd=25.0, limit_usd=100.0, soft_pct=80)
    assert round(status.utilization, 4) == 0.25


def test_raise_for_status_hard_stop_raises() -> None:
    status = evaluate_budget(spent_usd=100.0, limit_usd=100.0, soft_pct=80)
    try:
        status.raise_if_exceeded(scope="dept:cs")
    except BudgetExceeded as exc:
        assert "dept:cs" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("expected BudgetExceeded")


def test_raise_for_status_allowed_does_not_raise() -> None:
    status = evaluate_budget(spent_usd=10.0, limit_usd=100.0, soft_pct=80)
    status.raise_if_exceeded(scope="dept:cs")  # must not raise
