"""slack MCP tool: slack.post via incoming webhook (task 5.3, dept scenario 03).

write:internal per TRD §9 — a Slack post to an internal channel is autonomous
once the calling agent clears the eval-pass-rate + dept_admin-autonomy bar,
unlike email.send/github.open_pr which are always write:external. The channel
allowlist is a second, independent guard the department scenario calls out
explicitly ("allowlisted channels") — enforced here regardless of risk_class,
same pattern as email.py's domain allowlist.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Protocol

import httpx
from fleet_mcp.base import ToolContract

SLACK_POST_SCHEMA = {
    "type": "object",
    "properties": {"channel": {"type": "string"}, "text": {"type": "string"}},
    "required": ["channel", "text"],
    "additionalProperties": False,
}


class DisallowedChannelError(Exception):
    """Target channel is outside the server's allowlist."""


class WebhookSender(Protocol):
    async def post(self, *, channel: str, text: str) -> None: ...


@dataclass
class SlackWebhookSender:
    """Real transport: one incoming-webhook URL per Fleet deployment. Slack
    incoming webhooks are bound to a single channel at creation time, but the
    payload's `channel` field can still override it for workspaces that allow
    that — kept here so SlackPostTool's channel allowlist stays meaningful."""

    webhook_url: str

    async def post(self, *, channel: str, text: str) -> None:
        async with httpx.AsyncClient() as client:
            resp = await client.post(self.webhook_url, json={"channel": channel, "text": text})
            resp.raise_for_status()


@dataclass
class SlackPostTool:
    sender: WebhookSender
    allowed_channels: set[str]

    async def post(self, channel: str, text: str) -> None:
        if channel not in self.allowed_channels:
            raise DisallowedChannelError(f"channel not allowed: {channel!r}")
        await self.sender.post(channel=channel, text=text)

    def as_contract(self) -> ToolContract:
        return ToolContract(
            name="slack.post",
            risk_class="write:internal",
            description="Post a message to an allowlisted internal Slack channel.",
            input_schema=SLACK_POST_SCHEMA,
            fn=self.post,
        )


def build_default_sender() -> SlackWebhookSender:
    webhook_url = os.environ.get("FLEET_SLACK_WEBHOOK_URL", "")
    return SlackWebhookSender(webhook_url=webhook_url)
