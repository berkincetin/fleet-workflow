"""Contract test: all Sprint-5.1 servers registered on one MCPServer (task 5.1
AC — "each server passes contract tests; risk_class declared per tool").

Each server contributes ToolContract(s) built with fakes/fixtures (no network,
no DB) so this test proves the *shape* every server conforms to: risk_class
present and valid, auth enforced uniformly, schema validated uniformly. Live
behavior of pg_ro/email against the real stack is in tests/integration.
"""

from __future__ import annotations

import base64

import pytest
from fleet_mcp.base import MCPAuthError, MCPServer
from fleet_mcp.servers.email import EmailSendTool
from fleet_mcp.servers.internal_mock import InternalMockTool
from fleet_mcp.servers.ocr import build_ocr_contract


class _FakeSender:
    async def send(self, *, to: str, subject: str, body: str) -> None:
        pass


class _StubVisionClient:
    async def reasoning(self, messages: list[dict[str, object]], **kwargs: object) -> object:
        class _Resp:
            content = "hello from image"

        return _Resp()


@pytest.fixture
def server() -> MCPServer:
    mcp = MCPServer(name="fleet-mcp-internal", api_key="test-key")
    mcp.register(build_ocr_contract(vision_client=_StubVisionClient(), tesseract_fn=lambda b: ""))
    mcp.register(EmailSendTool(sender=_FakeSender(), allowed_domains={"example.com"}).as_contract())
    mcp.register(InternalMockTool(fixtures={"rec-1": {"ok": True}}).as_contract())
    return mcp


def test_all_registered_tools_declare_a_valid_risk_class(server: MCPServer) -> None:
    tools = server.list_tools()
    names = {t["name"] for t in tools}
    assert names == {"ocr.extract_text", "email.send", "internal.lookup"}
    risk_classes = {t["name"]: t["risk_class"] for t in tools}
    assert risk_classes["ocr.extract_text"] == "read"
    assert risk_classes["email.send"] == "write:external"
    assert risk_classes["internal.lookup"] == "read"


async def test_each_tool_callable_through_the_shared_dispatcher(server: MCPServer) -> None:
    ocr_result = await server.call_tool(
        "ocr.extract_text",
        {"image_base64": base64.b64encode(b"x").decode("ascii")},
        api_key="test-key",
    )
    assert ocr_result["text"] == "hello from image"

    await server.call_tool(
        "email.send",
        {"to": "a@example.com", "subject": "s", "body": "b"},
        api_key="test-key",
    )

    lookup_result = await server.call_tool(
        "internal.lookup", {"record_id": "rec-1"}, api_key="test-key"
    )
    assert lookup_result == {"ok": True}


async def test_wrong_api_key_blocks_every_server_uniformly(server: MCPServer) -> None:
    for tool_name, payload in [
        ("ocr.extract_text", {"image_base64": "eA=="}),
        ("email.send", {"to": "a@example.com", "subject": "s", "body": "b"}),
        ("internal.lookup", {"record_id": "rec-1"}),
    ]:
        with pytest.raises(MCPAuthError):
            await server.call_tool(tool_name, payload, api_key="wrong")
