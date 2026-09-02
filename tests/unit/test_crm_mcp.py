"""fleet_mcp.servers.crm — risk classes + the closed status vocabulary
(task 12.1, dept scenario 09).

The two tools sit on opposite sides of the approval line on purpose:
`get_application` is `read` and `update_status` is `write:internal`, while the
dealer-facing email lives on the separate `email.send` (write:external) tool.
This test pins that split, and pins that a status the CRM does not know about
is refused rather than recorded.
"""

from __future__ import annotations

import pytest
from fleet_mcp.base import MCPAuthError, MCPValidationError
from fleet_mcp.servers.crm import UnknownStatusError, build_crm_server


def test_risk_classes_put_only_internal_writes_on_this_server() -> None:
    server, _ = build_crm_server(api_key="k")
    assert {t["name"]: t["risk_class"] for t in server.list_tools()} == {
        "crm.get_application": "read",
        "crm.update_status": "write:internal",
    }


async def test_get_application_returns_a_dossier_with_a_sandbox_contact() -> None:
    server, _ = build_crm_server(api_key="k")
    application = await server.call_tool(
        "crm.get_application", {"application_id": "APP-1"}, api_key="k"
    )
    assert application["application_id"] == "APP-1"
    assert application["contact_email"].endswith("@fleet.local")


async def test_update_status_records_a_known_transition() -> None:
    server, tool = build_crm_server(api_key="k")
    result = await server.call_tool(
        "crm.update_status",
        {"application_id": "APP-1", "status": "ready_for_sales", "note": "temiz"},
        api_key="k",
    )
    assert result["status"] == "ready_for_sales"
    assert tool.status_updates == [result]
    assert result["note"] == "temiz"


async def test_unknown_status_is_refused() -> None:
    server, tool = build_crm_server(api_key="k")
    with pytest.raises(UnknownStatusError):
        await server.call_tool(
            "crm.update_status",
            {"application_id": "APP-1", "status": "approved_and_paid"},
            api_key="k",
        )
    assert tool.status_updates == []


async def test_schema_and_auth_are_enforced_like_every_other_server() -> None:
    server, _ = build_crm_server(api_key="k")
    with pytest.raises(MCPValidationError):
        await server.call_tool("crm.update_status", {"application_id": "APP-1"}, api_key="k")
    with pytest.raises(MCPAuthError):
        await server.call_tool(
            "crm.get_application", {"application_id": "APP-1"}, api_key="wrong"
        )
