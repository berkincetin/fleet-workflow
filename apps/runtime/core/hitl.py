"""Tool risk_class -> approval-queue decision (TRD §9).

Pure decision logic, no I/O: `read` tools always run autonomously;
`write:internal` runs autonomously only once the agent has both cleared its
eval pass-rate threshold and had autonomy explicitly enabled by a dept_admin;
`write:external` (customer email, PR, financial entry) always goes to the
approval queue, with no threshold that can waive it.
"""

from __future__ import annotations

_AUTONOMY_PASS_RATE_THRESHOLD = 0.9


def requires_approval(
    *, risk_class: str, eval_pass_rate: float, autonomy_enabled: bool
) -> bool:
    """Return True if a tool call of this risk_class must go through HITL."""
    if risk_class == "read":
        return False
    if risk_class == "write:external":
        return True
    if risk_class == "write:internal":
        return not (autonomy_enabled and eval_pass_rate >= _AUTONOMY_PASS_RATE_THRESHOLD)
    raise ValueError(f"unknown risk_class: {risk_class!r}")
