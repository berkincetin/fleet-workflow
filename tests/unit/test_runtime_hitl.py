"""core.hitl: tool risk_class -> autonomous vs approval-queue decision (TRD §9).

Pure decision logic only: read -> autonomous; write:internal -> autonomous iff
the agent's eval pass-rate clears the threshold AND dept_admin has enabled
autonomy; write:external -> always the approval queue, no exception. The
runtime graph's HITL node calls requires_approval() before executing any tool
and interrupts when it returns True; actually blocking on / resuming from that
interrupt is exercised in test_runtime_graph.py against a real LangGraph
checkpoint, not here.
"""

from __future__ import annotations

from core.hitl import requires_approval


def test_read_tool_never_requires_approval() -> None:
    assert requires_approval(risk_class="read", eval_pass_rate=0.0, autonomy_enabled=False) is False


def test_write_external_always_requires_approval() -> None:
    assert requires_approval(
        risk_class="write:external", eval_pass_rate=1.0, autonomy_enabled=True
    ) is True


def test_write_internal_requires_approval_when_autonomy_disabled() -> None:
    assert requires_approval(
        risk_class="write:internal", eval_pass_rate=0.95, autonomy_enabled=False
    ) is True


def test_write_internal_requires_approval_when_pass_rate_below_threshold() -> None:
    assert requires_approval(
        risk_class="write:internal", eval_pass_rate=0.5, autonomy_enabled=True
    ) is True


def test_write_internal_autonomous_when_pass_rate_and_autonomy_both_clear() -> None:
    assert requires_approval(
        risk_class="write:internal", eval_pass_rate=0.95, autonomy_enabled=True
    ) is False
