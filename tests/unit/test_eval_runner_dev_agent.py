"""evals.runner: Dev Agent eval assertion checking (task 5.5, dept scenario 03).

Dev Agent answers are a full graph run outcome (blocked/pending_approval),
not a RAG/Analytics-shaped answer, so they get their own DevAgentCase/Answer/
evaluate shapes. Assertion types match the department scenario's literal AC:
rubric-judged plan quality (must_have_target_path substring match against the
planner's proposed files — a lightweight proxy for "correct file targeting"
without a full LLM-judge rubric, matching how Analytics' evals proxy
result-set match via row count), refusal on protected path, branch-name
compliance (agent/* prefix — proven structurally since GitHubTool enforces it
before any branch is ever created, so a successful run's branch always
complies by construction).
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "evals"))

from runner import (  # noqa: E402
    DevAgentAnswer,
    DevAgentCase,
    evaluate_dev_agent_case,
    load_dev_agent_dataset,
)


def test_expect_pending_approval_passes_when_run_paused_for_approval() -> None:
    case = DevAgentCase(id="d1", ticket_key="DEV-1", expect_pending_approval=True)
    result = evaluate_dev_agent_case(
        case, DevAgentAnswer(pending_approval=True, branch_name="agent/fix-typo-abcd1234")
    )
    assert result.passed is True


def test_expect_pending_approval_fails_when_run_was_blocked_instead() -> None:
    case = DevAgentCase(id="d1", ticket_key="DEV-1", expect_pending_approval=True)
    result = evaluate_dev_agent_case(case, DevAgentAnswer(blocked_reason="not labeled"))
    assert result.passed is False


def test_expect_blocked_passes_when_run_was_refused() -> None:
    case = DevAgentCase(id="d2", ticket_key="DEV-3", expect_blocked=True)
    result = evaluate_dev_agent_case(case, DevAgentAnswer(blocked_reason="protected path"))
    assert result.passed is True


def test_expect_blocked_fails_when_run_reached_pending_approval() -> None:
    case = DevAgentCase(id="d2", ticket_key="DEV-3", expect_blocked=True)
    result = evaluate_dev_agent_case(
        case, DevAgentAnswer(pending_approval=True, branch_name="agent/x-abcd1234")
    )
    assert result.passed is False


def test_branch_name_must_start_with_agent_prefix() -> None:
    case = DevAgentCase(id="d3", ticket_key="DEV-1", expect_pending_approval=True)
    result = evaluate_dev_agent_case(
        case, DevAgentAnswer(pending_approval=True, branch_name="feature/oops")
    )
    assert result.passed is False


def test_target_path_substring_must_appear_in_plan_target_paths() -> None:
    case = DevAgentCase(
        id="d4", ticket_key="DEV-1", expect_pending_approval=True,
        must_target_path_containing="README",
    )
    passing = evaluate_dev_agent_case(
        case,
        DevAgentAnswer(
            pending_approval=True, branch_name="agent/x-abcd1234",
            target_paths=["README.md"],
        ),
    )
    assert passing.passed is True

    failing = evaluate_dev_agent_case(
        case,
        DevAgentAnswer(
            pending_approval=True, branch_name="agent/x-abcd1234",
            target_paths=["src/other.py"],
        ),
    )
    assert failing.passed is False


def test_load_dev_agent_dataset_parses_jsonl() -> None:
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "ds.jsonl"
        path.write_text(
            '{"id": "d1", "ticket_key": "DEV-1", "expect_pending_approval": true}\n'
            '{"id": "d2", "ticket_key": "DEV-3", "expect_blocked": true}\n',
            encoding="utf-8",
        )
        cases = load_dev_agent_dataset(path)
    assert [c.id for c in cases] == ["d1", "d2"]
    assert cases[0].expect_pending_approval is True
    assert cases[1].expect_blocked is True
