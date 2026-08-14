"""core.logging: structured JSON logger with PII scrubbing (task 8.4).

FLEET_DISABLE_LOKI_LOGGING is set for every test here — these assert the
stdout JSON line (always present) is correctly masked; Loki push itself is a
fire-and-forget background thread covered by the live integration test
(tests/integration/test_pii_logging_masked_live.py), not unit-testable
without a real Loki instance.
"""

from __future__ import annotations

import json
import logging

import pytest


@pytest.fixture(autouse=True)
def _disable_loki(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FLEET_DISABLE_LOKI_LOGGING", "1")


def _fresh_logger(name: str) -> logging.Logger:
    """core.logging.get_logger caches by name (module-level _configured set) —
    each test needs its own unique logger name to get a fresh configuration."""
    import core.logging as core_logging

    core_logging._configured.discard(name)
    logger = logging.getLogger(name)
    logger.handlers.clear()
    return core_logging.get_logger(name)


def test_get_logger_masks_email_in_stdout_json(capsys: pytest.CaptureFixture[str]) -> None:
    logger = _fresh_logger("test.pii.email")
    logger.info("user message: contact me at jane@example.com")
    out = capsys.readouterr().out.strip()
    record = json.loads(out)
    assert "jane@example.com" not in record["message"]
    assert "[EMAIL]" in record["message"]


def test_get_logger_masks_tr_iban_in_stdout_json(capsys: pytest.CaptureFixture[str]) -> None:
    logger = _fresh_logger("test.pii.iban")
    logger.info("payment to TR330006100519786457841326")
    out = capsys.readouterr().out.strip()
    record = json.loads(out)
    assert "TR330006100519786457841326" not in record["message"]
    assert "[TR_IBAN]" in record["message"]


def test_get_logger_output_is_valid_json_with_expected_fields(
    capsys: pytest.CaptureFixture[str],
) -> None:
    logger = _fresh_logger("test.pii.shape")
    logger.info("no identifiers here")
    out = capsys.readouterr().out.strip()
    record = json.loads(out)
    assert record["level"] == "INFO"
    assert record["logger"] == "test.pii.shape"
    assert record["message"] == "no identifiers here"
    assert "ts" in record


def test_get_logger_is_idempotent_per_name(capsys: pytest.CaptureFixture[str]) -> None:
    """Calling get_logger twice for the same name must not double-attach
    handlers (which would print every message twice)."""
    import core.logging as core_logging

    core_logging._configured.discard("test.pii.idempotent")
    logging.getLogger("test.pii.idempotent").handlers.clear()

    logger1 = core_logging.get_logger("test.pii.idempotent")
    logger2 = core_logging.get_logger("test.pii.idempotent")
    assert logger1 is logger2

    logger1.info("hello")
    lines = [ln for ln in capsys.readouterr().out.strip().splitlines() if ln]
    assert len(lines) == 1
