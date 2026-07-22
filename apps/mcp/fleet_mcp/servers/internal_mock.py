"""internal-mock MCP tool: fixture-backed stand-in for an internal API (task 5.1).

# INTEGRATION-POINT (CLAUDE.md rule 2): the real internal system this will
call isn't wired yet, so this reads from an in-memory fixture dict instead.
read risk_class only — a mock never performs a real write, so it can't be
promoted to write:* until a real backend replaces it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from fleet_mcp.base import ToolContract

INTERNAL_LOOKUP_SCHEMA = {
    "type": "object",
    "properties": {"record_id": {"type": "string"}},
    "required": ["record_id"],
    "additionalProperties": False,
}


class RecordNotFoundError(Exception):
    """No fixture record exists for the given id."""


@dataclass
class InternalMockTool:
    fixtures: dict[str, dict[str, Any]] = field(default_factory=dict)

    def lookup(self, record_id: str) -> dict[str, Any]:
        if record_id not in self.fixtures:
            raise RecordNotFoundError(f"no record: {record_id!r}")
        return self.fixtures[record_id]

    async def _lookup_async(self, record_id: str) -> dict[str, Any]:
        return self.lookup(record_id=record_id)

    def as_contract(self) -> ToolContract:
        return ToolContract(
            name="internal.lookup",
            risk_class="read",
            description=(
                "# INTEGRATION-POINT: fixture-backed lookup standing in for a real internal API."
            ),
            input_schema=INTERNAL_LOOKUP_SCHEMA,
            fn=self._lookup_async,
        )
