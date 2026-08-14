"""Structured JSON logging with PII scrubbing (CLAUDE.md conventions: "structured
JSON via core.logging.get_logger; never log payloads with credentials/PII —
logger applies scrubber, but don't rely on it"; task 8.4 AC: detected
identifiers masked in Loki for a seeded PII conversation).

`get_logger(name)` returns a stdlib `logging.Logger` emitting one JSON object
per line to stdout (picked up by any container log collector) and, best-effort,
pushed directly to Loki's HTTP push API — direct push rather than relying on a
Docker-log-scraping sidecar (no promtail service exists in this repo, and
`fleet-api` commonly runs host-native via `make api`, not as a compose
container, so there is nothing to scrape its stdout in that mode). A
`PiiScrubFilter` masks every record's message through `core.pii_scrub.scrub`
before it is formatted, so masking cannot be bypassed by a call site that
forgets to scrub first — the "don't rely on it" callers still should scrub
sensitive fields explicitly, this is the defense-in-depth backstop.

Loki push failures never raise — logging must never be able to break request
handling; if Loki is unreachable the JSON line is still written to stdout.
"""

from __future__ import annotations

import json
import logging
import os
import sys
import threading
import time
import urllib.request
from typing import Any

from core.pii_scrub import scrub

_DEFAULT_LOKI_URL = "http://localhost:3100"


class PiiScrubFilter(logging.Filter):
    """Masks detected identifiers in every record's rendered message."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = scrub(record.getMessage()).text
        record.args = ()
        return True


class _JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        extra = getattr(record, "fields", None)
        if isinstance(extra, dict):
            payload.update(extra)
        return json.dumps(payload, ensure_ascii=False)


class LokiPushHandler(logging.Handler):
    """Best-effort direct push to Loki's `/loki/api/v1/push` HTTP API. Never
    raises out of `emit` — a Loki outage must never break the caller's request."""

    def __init__(self, *, loki_url: str, service: str, timeout: float = 2.0) -> None:
        super().__init__()
        self._url = f"{loki_url.rstrip('/')}/loki/api/v1/push"
        self._service = service
        self._timeout = timeout

    def emit(self, record: logging.LogRecord) -> None:
        try:
            line = self.format(record)
            body = json.dumps(
                {
                    "streams": [
                        {
                            "stream": {"service": self._service, "level": record.levelname.lower()},
                            "values": [[str(int(time.time() * 1_000_000_000)), line]],
                        }
                    ]
                }
            ).encode("utf-8")
            req = urllib.request.Request(
                self._url, data=body, headers={"Content-Type": "application/json"}, method="POST"
            )
            # Fire-and-forget on a daemon thread: Loki push must never add
            # request-handling latency to the caller emitting the log line.
            threading.Thread(
                target=self._send, args=(req,), daemon=True
            ).start()
        except Exception:  # noqa: BLE001 — logging must never raise
            pass

    def _send(self, req: urllib.request.Request) -> None:
        try:
            urllib.request.urlopen(req, timeout=self._timeout)
        except Exception:  # noqa: BLE001 — best-effort; stdout already has the line
            pass


_configured: set[str] = set()


def get_logger(name: str) -> logging.Logger:
    """Structured JSON logger: stdout always, Loki push best-effort (set
    FLEET_LOKI_URL to override, FLEET_DISABLE_LOKI_LOGGING=1 to skip Loki
    entirely, e.g. in unit tests)."""
    logger = logging.getLogger(name)
    if name in _configured:
        return logger

    logger.setLevel(logging.INFO)
    logger.addFilter(PiiScrubFilter())

    formatter = _JsonFormatter()

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    if not os.environ.get("FLEET_DISABLE_LOKI_LOGGING"):
        loki_url = os.environ.get("FLEET_LOKI_URL", _DEFAULT_LOKI_URL)
        loki_handler = LokiPushHandler(loki_url=loki_url, service="fleet-api")
        loki_handler.setFormatter(formatter)
        logger.addHandler(loki_handler)

    logger.propagate = False
    _configured.add(name)
    return logger
