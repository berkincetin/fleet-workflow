"""Dev Agent guardrails: pure predicates, no I/O (task 5.5, dept scenario 03).

- Tickets only with label `agent-ok` — the Dev Agent must never pick up a
  ticket a human hasn't explicitly cleared for autonomous handling.
- Protected-paths blocklist (infra/, migrations/, .github/) — never touch
  infrastructure, DB schema, or CI config.
- Diff size cap (>400 lines -> split or escalate) — keeps a single agent PR
  reviewable; a run whose plan implies a bigger diff must not proceed.
"""

from __future__ import annotations

from typing import Any

PROTECTED_PATH_PREFIXES = ("infra/", ".github/")
MAX_DIFF_LINES = 400


class TicketNotLabeledError(Exception):
    """Ticket lacks the required `agent-ok` label."""


class ProtectedPathError(Exception):
    """Plan touches a path under a protected prefix."""


class DiffTooLargeError(Exception):
    """Planned diff exceeds the line cap."""


def assert_ticket_labeled(ticket: dict[str, Any]) -> None:
    if "agent-ok" not in ticket.get("labels", []):
        raise TicketNotLabeledError(
            f"ticket {ticket.get('key', '?')!r} is missing the required 'agent-ok' label"
        )


def assert_no_protected_paths(paths: list[str]) -> None:
    for path in paths:
        if any(path.startswith(prefix) for prefix in PROTECTED_PATH_PREFIXES):
            raise ProtectedPathError(f"plan touches protected path: {path!r}")


def assert_diff_size_ok(line_count: int) -> None:
    if line_count > MAX_DIFF_LINES:
        raise DiffTooLargeError(
            f"planned diff is {line_count} lines, exceeds the {MAX_DIFF_LINES}-line cap"
        )
