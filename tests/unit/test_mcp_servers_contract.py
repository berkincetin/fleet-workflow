"""Contract test: all Sprint-5.1/5.3/6.3 servers registered on one MCPServer
(AC — "each server passes contract tests; risk_class declared per tool").

Each server contributes ToolContract(s) built with fakes/fixtures (no network,
no DB) so this test proves the *shape* every server conforms to: risk_class
present and valid, auth enforced uniformly, schema validated uniformly. Live
behavior of pg_ro/email/github against the real stack/sandbox is in
tests/integration.
"""

from __future__ import annotations

import base64

import pytest
from fleet_mcp.base import MCPAuthError, MCPServer
from fleet_mcp.servers.email import EmailSendTool
from fleet_mcp.servers.erp import ErpTool
from fleet_mcp.servers.github import GitHubTool
from fleet_mcp.servers.internal_mock import InternalMockTool
from fleet_mcp.servers.jira import FixtureJiraBackend, JiraTool
from fleet_mcp.servers.ocr import build_ocr_contract
from fleet_mcp.servers.slack import SlackPostTool


class _FakeSender:
    async def send(self, *, to: str, subject: str, body: str) -> None:
        pass


class _StubVisionClient:
    async def reasoning(self, messages: list[dict[str, object]], **kwargs: object) -> object:
        class _Resp:
            content = "hello from image"

        return _Resp()


class _FakeSlackSender:
    async def post(self, *, channel: str, text: str) -> None:
        pass


class _FakeGitHubBackend:
    async def read_repo(self) -> dict[str, object]:
        return {"full_name": "org/repo"}

    async def create_branch(self, branch_name: str, from_ref: str) -> dict[str, object]:
        return {"ref": f"refs/heads/{branch_name}"}

    async def commit_file(
        self, *, branch_name: str, path: str, content: str, message: str
    ) -> dict[str, object]:
        return {"commit": {"sha": "abc123"}}

    async def open_pr(self, *, branch_name: str, title: str, body: str) -> dict[str, object]:
        return {"number": 1}


@pytest.fixture
def server() -> MCPServer:
    mcp = MCPServer(name="fleet-mcp-internal", api_key="test-key")
    mcp.register(build_ocr_contract(vision_client=_StubVisionClient(), tesseract_fn=lambda b: ""))
    mcp.register(EmailSendTool(sender=_FakeSender(), allowed_domains={"example.com"}).as_contract())
    mcp.register(InternalMockTool(fixtures={"rec-1": {"ok": True}}).as_contract())
    for contract in JiraTool(backend=FixtureJiraBackend(issues={})).as_contracts():
        mcp.register(contract)
    for contract in GitHubTool(backend=_FakeGitHubBackend()).as_contracts():
        mcp.register(contract)
    mcp.register(
        SlackPostTool(sender=_FakeSlackSender(), allowed_channels={"#dev-agent"}).as_contract()
    )
    mcp.register(ErpTool().as_contract())
    return mcp


def test_all_registered_tools_declare_a_valid_risk_class(server: MCPServer) -> None:
    tools = server.list_tools()
    risk_classes = {t["name"]: t["risk_class"] for t in tools}
    assert risk_classes == {
        "ocr.extract_text": "read",
        "email.send": "write:external",
        "internal.lookup": "read",
        "jira.search": "read",
        "jira.get_issue": "read",
        "github.read_repo": "read",
        "github.create_branch": "write:internal",
        "github.commit_file": "write:internal",
        "github.open_pr": "write:external",
        "slack.post": "write:internal",
        "erp.create_draft_entry": "write:external",
    }


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

    search_result = await server.call_tool("jira.search", {"jql": "x"}, api_key="test-key")
    assert search_result == []

    branch_result = await server.call_tool(
        "github.create_branch",
        {"branch_name": "agent/x", "from_ref": "main"},
        api_key="test-key",
    )
    assert branch_result["ref"] == "refs/heads/agent/x"

    await server.call_tool(
        "slack.post", {"channel": "#dev-agent", "text": "hi"}, api_key="test-key"
    )

    entry_result = await server.call_tool(
        "erp.create_draft_entry",
        {"vendor": "Acme", "po_number": "PO-1001", "amount": 100.0, "currency": "TRY"},
        api_key="test-key",
    )
    assert entry_result["status"] == "draft"


async def test_wrong_api_key_blocks_every_server_uniformly(server: MCPServer) -> None:
    for tool_name, payload in [
        ("ocr.extract_text", {"image_base64": "eA=="}),
        ("email.send", {"to": "a@example.com", "subject": "s", "body": "b"}),
        ("internal.lookup", {"record_id": "rec-1"}),
        ("jira.search", {"jql": "x"}),
        ("github.read_repo", {}),
        ("slack.post", {"channel": "#dev-agent", "text": "hi"}),
        (
            "erp.create_draft_entry",
            {"vendor": "Acme", "po_number": "PO-1001", "amount": 100.0, "currency": "TRY"},
        ),
    ]:
        with pytest.raises(MCPAuthError):
            await server.call_tool(tool_name, payload, api_key="wrong")
