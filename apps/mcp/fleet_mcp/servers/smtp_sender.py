"""Real SMTP transport for email.EmailSendTool (task 5.1).

Talks to the sandbox SMTP server (mailpit in dev, infra/compose) via
aiosmtplib. Kept separate from email.py so the pure send-logic module has no
network dependency and stays trivially unit-testable.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from email.message import EmailMessage

import aiosmtplib


@dataclass
class SmtpSender:
    host: str
    port: int
    from_addr: str

    async def send(self, *, to: str, subject: str, body: str) -> None:
        message = EmailMessage()
        message["From"] = self.from_addr
        message["To"] = to
        message["Subject"] = subject
        message.set_content(body)
        await aiosmtplib.send(message, hostname=self.host, port=self.port)


def build_default_sender() -> SmtpSender:
    return SmtpSender(
        host=os.environ.get("FLEET_SMTP_HOST", "localhost"),
        port=int(os.environ.get("FLEET_SMTP_PORT", "1025")),
        from_addr=os.environ.get("FLEET_SMTP_FROM", "fleet-agent@fleet.local"),
    )
