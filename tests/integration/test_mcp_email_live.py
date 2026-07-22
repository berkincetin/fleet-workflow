"""Integration: email MCP tool against the real mailpit SMTP sandbox (task 5.1
AC — "each server passes contract tests"). Sends through the real SmtpSender
(aiosmtplib -> mailpit:1025) and confirms the message actually landed via
mailpit's HTTP API (localhost:8025), not just that send() didn't raise.
"""

from __future__ import annotations

import uuid

import httpx
import pytest
from fleet_mcp.servers.email import EmailSendTool
from fleet_mcp.servers.smtp_sender import SmtpSender

MAILPIT_HTTP = "http://localhost:8025"


def _mailpit_up() -> bool:
    try:
        httpx.get(f"{MAILPIT_HTTP}/api/v1/info", timeout=2.0)
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not _mailpit_up(), reason="mailpit not reachable — start with `make dev`"
)


async def test_live_send_lands_in_mailpit() -> None:
    sender = SmtpSender(host="localhost", port=1025, from_addr="fleet-agent@fleet.local")
    tool = EmailSendTool(sender=sender, allowed_domains={"example.com"})
    marker = f"fleet-test-{uuid.uuid4().hex[:8]}"

    await tool.send(to="user@example.com", subject=marker, body="MCP email server live test")

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{MAILPIT_HTTP}/api/v1/search", params={"query": f"subject:{marker}"}
        )
    resp.raise_for_status()
    results = resp.json()
    assert results["total"] >= 1
    assert results["messages"][0]["Subject"] == marker
