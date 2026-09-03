"""email MCP tool: SMTP sandbox send (task 5.1).

Always write:external (TRD §9 names customer email as the canonical example
of a write that always goes through the approval queue, no exception) — this
tool never decides autonomy, it just sends once approved/resumed. The domain
allowlist is a second guard beyond risk_class: even an approved send can't
target an address outside the sandbox's expected domain(s), catching a
malformed/hallucinated recipient before an SMTP attempt.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Protocol

from fleet_mcp.base import ToolContract

_EMAIL_RE = re.compile(r"^[^@\s]+@([^@\s]+)$")

EMAIL_INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "to": {"type": "string"},
        "subject": {"type": "string"},
        "body": {"type": "string"},
    },
    "required": ["to", "subject", "body"],
    "additionalProperties": False,
}


class InvalidRecipientError(Exception):
    """Recipient address is malformed or outside the allowed domain set."""


def is_allowed_recipient(to: str, allowed_domains: set[str]) -> bool:
    """The domain-allowlist check on its own, for callers that need to reject a
    recipient *before* an email is queued for approval (task 13.4's
    `/v1/service/email-send`) rather than at send time."""
    match = _EMAIL_RE.match(to)
    return bool(match and match.group(1) in allowed_domains)


class EmailSender(Protocol):
    async def send(self, *, to: str, subject: str, body: str) -> None: ...


@dataclass
class EmailSendTool:
    sender: EmailSender
    allowed_domains: set[str]

    def _validate(self, to: str) -> None:
        if not is_allowed_recipient(to, self.allowed_domains):
            raise InvalidRecipientError(f"recipient not allowed: {to!r}")

    async def send(self, to: str, subject: str, body: str) -> None:
        self._validate(to)
        await self.sender.send(to=to, subject=subject, body=body)

    def as_contract(self) -> ToolContract:
        return ToolContract(
            name="email.send",
            risk_class="write:external",
            description="Send an email via the SMTP sandbox (always approval-gated).",
            input_schema=EMAIL_INPUT_SCHEMA,
            fn=self.send,
        )
