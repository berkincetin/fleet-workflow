"""fleet_mcp.servers.slack: slack.post via webhook (task 5.3, dept scenario 03).

write:internal (posting to an internal Slack channel isn't customer-facing,
so it's autonomous once an agent clears the eval-pass-rate/dept_admin-autonomy
bar per TRD §9 — unlike email/github.open_pr which are always write:external).
Channel allowlist is enforced here, independent of risk_class, since the
department scenario specifically calls out "allowlisted channels" as its own
guardrail.
"""

from __future__ import annotations

import pytest
from fleet_mcp.servers.slack import DisallowedChannelError, SlackPostTool


class _FakeWebhookSender:
    def __init__(self) -> None:
        self.posted: list[dict[str, str]] = []

    async def post(self, *, channel: str, text: str) -> None:
        self.posted.append({"channel": channel, "text": text})


async def test_post_to_allowlisted_channel_dispatches() -> None:
    sender = _FakeWebhookSender()
    tool = SlackPostTool(sender=sender, allowed_channels={"#dev-agent"})
    await tool.post(channel="#dev-agent", text="PR opened")
    assert sender.posted == [{"channel": "#dev-agent", "text": "PR opened"}]


async def test_post_to_non_allowlisted_channel_is_refused() -> None:
    sender = _FakeWebhookSender()
    tool = SlackPostTool(sender=sender, allowed_channels={"#dev-agent"})
    with pytest.raises(DisallowedChannelError):
        await tool.post(channel="#random", text="oops")
    assert sender.posted == []


def test_contract_declares_write_internal() -> None:
    sender = _FakeWebhookSender()
    tool = SlackPostTool(sender=sender, allowed_channels={"#dev-agent"})
    contract = tool.as_contract()
    assert contract.risk_class == "write:internal"
    assert contract.name == "slack.post"
