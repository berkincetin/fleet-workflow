"""agents.dev_agent.guardrails: pure guardrail checks (task 5.5, dept scenario
03 Dev Agent).

Guardrails per the department scenario: protected-paths blocklist
(infra/, migrations/, .github/), diff size cap (>400 lines -> split or
escalate), tickets only with label `agent-ok`. All pure predicates — no I/O,
no LLM calls — so the graph node just calls these and branches.
"""

from __future__ import annotations

from agents.dev_agent.guardrails import (
    DiffTooLargeError,
    ProtectedPathError,
    TicketNotLabeledError,
    assert_diff_size_ok,
    assert_no_protected_paths,
    assert_ticket_labeled,
)


def test_ticket_with_agent_ok_label_passes() -> None:
    assert_ticket_labeled({"labels": ["agent-ok", "bug"]})  # no raise


def test_ticket_without_agent_ok_label_raises() -> None:
    import pytest

    with pytest.raises(TicketNotLabeledError):
        assert_ticket_labeled({"labels": ["bug"]})


def test_ticket_with_no_labels_field_raises() -> None:
    import pytest

    with pytest.raises(TicketNotLabeledError):
        assert_ticket_labeled({})


def test_plan_touching_only_safe_paths_passes() -> None:
    assert_no_protected_paths(["apps/web/components/foo.tsx", "docs/notes.md"])


def test_plan_touching_infra_path_raises() -> None:
    import pytest

    with pytest.raises(ProtectedPathError):
        assert_no_protected_paths(["infra/compose/docker-compose.dev.yml"])


def test_plan_touching_migrations_path_raises() -> None:
    import pytest

    with pytest.raises(ProtectedPathError):
        assert_no_protected_paths(["infra/migrations/versions/0099_x.py"])


def test_plan_touching_github_workflows_path_raises() -> None:
    import pytest

    with pytest.raises(ProtectedPathError):
        assert_no_protected_paths([".github/workflows/ci.yml"])


def test_diff_under_cap_passes() -> None:
    assert_diff_size_ok(399)
    assert_diff_size_ok(400)


def test_diff_over_cap_raises() -> None:
    import pytest

    with pytest.raises(DiffTooLargeError):
        assert_diff_size_ok(401)
