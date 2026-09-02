"""listings MCP server: get_new (read) + flag (write:internal), and the
flag-only guardrail is enforced by the tool surface (task 11.1, dept scenario
06). There is no unpublish/reject tool — asserting its absence is the test.
"""

from __future__ import annotations

import pytest
from fleet_mcp.servers.listings import build_listings_server


async def test_get_new_returns_synthetic_listings() -> None:
    server, _ = build_listings_server(api_key="k")
    result = await server.call_tool("listings.get_new", {"limit": 3}, api_key="k")
    listings = result["listings"]
    assert len(listings) == 3
    for item in listings:
        assert {"listing_id", "segment", "description", "price", "image_base64"} <= set(item)


async def test_flag_records_and_acks() -> None:
    server, tool = build_listings_server(api_key="k")
    result = await server.call_tool(
        "listings.flag",
        {"listing_id": "L-0001", "codes": ["price_anomaly"], "reasons": ["too high"]},
        api_key="k",
    )
    assert result["status"] == "queued_for_review"
    assert tool.flagged[0]["listing_id"] == "L-0001"


def test_flag_is_write_internal_not_external() -> None:
    server, _ = build_listings_server(api_key="k")
    tools = {t["name"]: t for t in server.list_tools()}
    assert tools["listings.flag"]["risk_class"] == "write:internal"
    assert tools["listings.get_new"]["risk_class"] == "read"


def test_no_unpublish_or_reject_tool_exists() -> None:
    """Flag-only guardrail: the mutating surface is flag only — no way to
    unpublish/reject a listing exists at all."""
    server, _ = build_listings_server(api_key="k")
    names = {t["name"] for t in server.list_tools()}
    assert names == {"listings.get_new", "listings.flag"}
    for forbidden in ("listings.unpublish", "listings.reject", "listings.delete"):
        assert forbidden not in names


async def test_auth_is_enforced() -> None:
    from fleet_mcp.base import MCPAuthError

    server, _ = build_listings_server(api_key="right")
    with pytest.raises(MCPAuthError):
        await server.call_tool("listings.get_new", {}, api_key="wrong")
