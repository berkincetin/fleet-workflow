"""fleet_mcp.servers.email: SMTP sandbox tool (task 5.1).

write:external risk_class — an actual outbound email always needs approval
per TRD §9 (customer email is the canonical write:external example). The SMTP
transport is injected (a Sender protocol) so this is testable without a real
SMTP server; live wiring against mailpit is exercised in tests/integration.
"""

from __future__ import annotations

import pytest
from fleet_mcp.servers.email import EMAIL_INPUT_SCHEMA, EmailSendTool, InvalidRecipientError


class _FakeSender:
    def __init__(self) -> None:
        self.sent: list[dict[str, str]] = []

    async def send(self, *, to: str, subject: str, body: str) -> None:
        self.sent.append({"to": to, "subject": subject, "body": body})


async def test_send_email_dispatches_to_sender() -> None:
    sender = _FakeSender()
    tool = EmailSendTool(sender=sender, allowed_domains={"example.com"})
    await tool.send(to="user@example.com", subject="Hi", body="Hello there")
    assert sender.sent == [{"to": "user@example.com", "subject": "Hi", "body": "Hello there"}]


async def test_send_email_rejects_disallowed_domain() -> None:
    sender = _FakeSender()
    tool = EmailSendTool(sender=sender, allowed_domains={"example.com"})
    with pytest.raises(InvalidRecipientError):
        await tool.send(to="user@other.com", subject="Hi", body="Hello")
    assert sender.sent == []


async def test_send_email_rejects_malformed_address() -> None:
    sender = _FakeSender()
    tool = EmailSendTool(sender=sender, allowed_domains={"example.com"})
    with pytest.raises(InvalidRecipientError):
        await tool.send(to="not-an-email", subject="Hi", body="Hello")


def test_email_tool_contract_declares_write_external() -> None:
    sender = _FakeSender()
    tool = EmailSendTool(sender=sender, allowed_domains={"example.com"})
    contract = tool.as_contract()
    assert contract.risk_class == "write:external"
    assert contract.input_schema == EMAIL_INPUT_SCHEMA
