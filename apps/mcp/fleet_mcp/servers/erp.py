"""erp MCP tool: create_draft_entry (task 6.3, dept scenario 04 Invoice &
Reconciliation).

# INTEGRATION-POINT (CLAUDE.md rule 2): no real ERP system is wired in this
environment (dept scenario 04 names this explicitly — "mock ERP in MVP") —
draft entries are recorded in-memory and returned with a synthetic entry id,
same fixture-backed-standing-in-for-a-real-system pattern as internal_mock.py.
Always write:external per TRD §9: a draft accounting entry is exactly the
kind of external-system side effect that must never execute without a human
approval, regardless of how confident the extraction/validation upstream was
— rollout is "approval-gated forever" per the department scenario, not just
until eval pass-rate clears a bar (unlike write:internal tools elsewhere).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

from fleet_mcp.base import ToolContract

CREATE_DRAFT_ENTRY_SCHEMA = {
    "type": "object",
    "properties": {
        "vendor": {"type": "string"},
        "po_number": {"type": "string"},
        "amount": {"type": "number"},
        "currency": {"type": "string"},
    },
    "required": ["vendor", "po_number", "amount", "currency"],
    "additionalProperties": False,
}


@dataclass
class ErpTool:
    created_entries: list[dict[str, Any]] = field(default_factory=list)

    async def create_draft_entry(
        self, *, vendor: str, po_number: str, amount: float, currency: str
    ) -> dict[str, Any]:
        entry = {
            "entry_id": f"DRAFT-{uuid.uuid4().hex[:10]}",
            "vendor": vendor,
            "po_number": po_number,
            "amount": amount,
            "currency": currency,
            "status": "draft",
        }
        self.created_entries.append(entry)
        return entry

    def as_contract(self) -> ToolContract:
        return ToolContract(
            name="erp.create_draft_entry",
            risk_class="write:external",
            description=(
                "# INTEGRATION-POINT: mock ERP — records a draft accounting "
                "entry in memory; a real ERP integration replaces this."
            ),
            input_schema=CREATE_DRAFT_ENTRY_SCHEMA,
            fn=self.create_draft_entry,
        )
