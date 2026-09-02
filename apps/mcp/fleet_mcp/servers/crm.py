"""crm MCP tools: get_application (read) + update_status (write:internal) —
task 12.1, dept scenario 09 (Dealer Onboarding).

# INTEGRATION-POINT (CLAUDE.md rule 2): no real CRM is wired in this
environment (dept scenario 09 names `crm.get_application` as the integration
point). `get_application` serves deterministic synthetic dealer applications
from an in-memory store; `update_status` records the transition and returns a
synthetic ack — the same fixture-backed pattern as erp.py / listings.py.

`update_status` is write:internal (supervised): moving a dealer application
between internal pipeline states is an internal side effect. The outbound
missing-document email is the external one, and it does NOT live here — it goes
through email.send (write:external, always approval-gated). Keeping the two on
separate tools is what lets the agent hand a clean dossier to a sales rep
without a human in the loop while every dealer-facing email still stops at the
approval queue.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

from fleet_mcp.base import ToolContract

GET_APPLICATION_SCHEMA = {
    "type": "object",
    "properties": {"application_id": {"type": "string"}},
    "required": ["application_id"],
    "additionalProperties": False,
}

UPDATE_STATUS_SCHEMA = {
    "type": "object",
    "properties": {
        "application_id": {"type": "string"},
        "status": {"type": "string"},
        "note": {"type": "string"},
    },
    "required": ["application_id", "status"],
    "additionalProperties": False,
}

# The pipeline states this scenario can move an application into. A closed
# vocabulary (same idea as listing_quality's reason codes): the agent cannot
# invent a status the CRM does not know about.
APPLICATION_STATUSES = frozenset(
    {"awaiting_documents", "manual_review", "ready_for_sales"}
)


class UnknownStatusError(Exception):
    """A status outside the CRM's known application pipeline states."""


class UnknownApplicationError(Exception):
    """No dealer application with that id."""


def _synthetic_application(application_id: str) -> dict[str, Any]:
    """Deterministic synthetic dealer application for the mock CRM.

    The contact address stays on the sandbox domain the email MCP allowlists,
    so an approved missing-document send lands in mailpit rather than being
    rejected as an out-of-domain recipient.
    """
    return {
        "application_id": application_id,
        "company_name": "Anadolu Otomotiv Ticaret A.S.",
        "contact_name": "Mehmet Yilmaz",
        "contact_email": "dealer@fleet.local",
        "city": "Ankara",
        "status": "submitted",
    }


@dataclass
class CrmTool:
    """In-memory mock of the corporate-sales CRM (get_application + update_status)."""

    applications: dict[str, dict[str, Any]] = field(default_factory=dict)
    status_updates: list[dict[str, Any]] = field(default_factory=list)

    async def get_application(self, *, application_id: str) -> dict[str, Any]:
        record = self.applications.get(application_id)
        if record is None:
            record = _synthetic_application(application_id)
        return dict(record)

    async def update_status(
        self, *, application_id: str, status: str, note: str | None = None
    ) -> dict[str, Any]:
        if status not in APPLICATION_STATUSES:
            raise UnknownStatusError(
                f"unknown application status {status!r}; "
                f"allowed: {sorted(APPLICATION_STATUSES)}"
            )
        record = {
            "update_id": f"CRMU-{uuid.uuid4().hex[:10]}",
            "application_id": application_id,
            "status": status,
            "note": note or "",
        }
        self.status_updates.append(record)
        return record


def build_crm_server(*, api_key: str) -> Any:
    from fleet_mcp.base import MCPServer

    tool = CrmTool()
    server = MCPServer(name="crm", api_key=api_key)
    server.register(
        ToolContract(
            name="crm.get_application",
            risk_class="read",
            description="Fetch a dealer application dossier from the CRM (mock).",
            input_schema=GET_APPLICATION_SCHEMA,
            fn=tool.get_application,
        )
    )
    server.register(
        ToolContract(
            name="crm.update_status",
            risk_class="write:internal",
            description="Move a dealer application to a known pipeline status.",
            input_schema=UPDATE_STATUS_SCHEMA,
            fn=tool.update_status,
        )
    )
    return server, tool
