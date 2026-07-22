"""fleet_mcp.base: MCP server base — tool registry, risk_class, schema validation,
bearer-token auth (task 5.1, TRD §7.1/§7.3/§9).

Every MCP server is a thin wrapper around MCPServer: register ToolContracts
(each with a declared risk_class and JSON-schema-ish input validation), then
dispatch calls through call_tool(), which enforces auth + schema before the
tool function ever runs. This is the contract every server (pg_ro, ocr, email,
internal-mock, and later jira/github/slack) is tested against identically.
"""

from __future__ import annotations

import pytest
from fleet_mcp.base import MCPAuthError, MCPServer, MCPValidationError, ToolContract


def _make_server(**tools: ToolContract) -> MCPServer:
    server = MCPServer(name="test-server", api_key="secret-key")
    for tool in tools.values():
        server.register(tool)
    return server


async def _echo(**kwargs: object) -> dict[str, object]:
    return {"echo": kwargs}


def test_register_and_list_tools_exposes_risk_class() -> None:
    tool = ToolContract(
        name="echo",
        risk_class="read",
        description="Echoes input",
        input_schema={"type": "object", "properties": {"x": {"type": "string"}}, "required": ["x"]},
        fn=_echo,
    )
    server = _make_server(echo=tool)
    listed = server.list_tools()
    assert len(listed) == 1
    assert listed[0]["name"] == "echo"
    assert listed[0]["risk_class"] == "read"


def test_register_rejects_invalid_risk_class() -> None:
    tool = ToolContract(
        name="bad", risk_class="not-a-real-class", description="", input_schema={}, fn=_echo
    )
    server = MCPServer(name="test-server", api_key="secret-key")
    with pytest.raises(ValueError, match="risk_class"):
        server.register(tool)


async def test_call_tool_success_returns_result() -> None:
    tool = ToolContract(
        name="echo",
        risk_class="read",
        description="",
        input_schema={"type": "object", "properties": {"x": {"type": "string"}}, "required": ["x"]},
        fn=_echo,
    )
    server = _make_server(echo=tool)
    result = await server.call_tool("echo", {"x": "hi"}, api_key="secret-key")
    assert result == {"echo": {"x": "hi"}}


async def test_call_tool_wrong_api_key_raises_auth_error() -> None:
    tool = ToolContract(
        name="echo", risk_class="read", description="", input_schema={}, fn=_echo
    )
    server = _make_server(echo=tool)
    with pytest.raises(MCPAuthError):
        await server.call_tool("echo", {}, api_key="wrong-key")


async def test_call_tool_missing_required_field_raises_validation_error() -> None:
    tool = ToolContract(
        name="echo",
        risk_class="read",
        description="",
        input_schema={"type": "object", "properties": {"x": {"type": "string"}}, "required": ["x"]},
        fn=_echo,
    )
    server = _make_server(echo=tool)
    with pytest.raises(MCPValidationError):
        await server.call_tool("echo", {}, api_key="secret-key")


async def test_call_tool_unknown_tool_raises_key_error() -> None:
    server = MCPServer(name="test-server", api_key="secret-key")
    with pytest.raises(KeyError):
        await server.call_tool("nonexistent", {}, api_key="secret-key")


async def test_call_tool_rejects_extra_unschematized_field() -> None:
    tool = ToolContract(
        name="echo",
        risk_class="read",
        description="",
        input_schema={
            "type": "object",
            "properties": {"x": {"type": "string"}},
            "required": ["x"],
            "additionalProperties": False,
        },
        fn=_echo,
    )
    server = _make_server(echo=tool)
    with pytest.raises(MCPValidationError):
        await server.call_tool("echo", {"x": "hi", "y": "unexpected"}, api_key="secret-key")


def test_list_tools_does_not_leak_fn_or_api_key() -> None:
    tool = ToolContract(
        name="echo", risk_class="read", description="d", input_schema={}, fn=_echo
    )
    server = _make_server(echo=tool)
    listed = server.list_tools()
    assert "fn" not in listed[0]
    assert "api_key" not in listed[0]
