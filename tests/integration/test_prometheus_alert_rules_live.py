"""Integration: infra/compose/prometheus/alerts.yml's rules actually fire (or
don't) given synthetic time series, verified against the real Prometheus
binary via `promtool test rules` (task 7.4) — not hand-reasoning about
PromQL. Covers all 5 rules: BudgetSoftLimitExceeded (task 7.4's literal AC —
the client-side counter increment is proven separately in
tests/unit/test_llm_client_metrics.py; this proves the rule fires given that
counter shape), HighErrorRate, HighLatencyP95, IngestQueueBacklog, and
DeptCostAnomaly (including a negative case: a negligible-baseline dept must
not page anyone even at an anomalous ratio).

Also proves the Slack half end to end via the real `amtool` binary: given
BudgetSoftLimitExceeded's labels, Alertmanager's routing tree resolves to the
"slack" receiver — real Slack delivery is an INTEGRATION-POINT (same
convention as Jira/GitHub: no live third-party call in tests), but the
routing decision itself is real, not asserted by reading YAML.

`infra/compose/prometheus/alerts_test.yml` is the actual promtool test file
— source of truth for what each rule is asserted to do; this module just
runs it via the real binary and fails loudly if Docker/the image is
unavailable, rather than silently skipping (an alert-rule regression should
break CI, not go quiet).
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

_PROMETHEUS_DIR = Path(__file__).resolve().parents[2] / "infra" / "compose" / "prometheus"
_ALERTMANAGER_DIR = Path(__file__).resolve().parents[2] / "infra" / "compose" / "alertmanager"


def test_alert_rules_pass_promtool_test_rules() -> None:
    if shutil.which("docker") is None:
        pytest.fail("docker is required to run `promtool test rules` for the alert rules suite")

    result = subprocess.run(
        [
            "docker", "run", "--rm",
            "-v", f"{_PROMETHEUS_DIR}:/etc/prometheus:ro",
            "--entrypoint", "/bin/promtool",
            "prom/prometheus:v3.0.1",
            "test", "rules", "/etc/prometheus/alerts_test.yml",
        ],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, (
        f"promtool test rules failed:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    )


def test_prometheus_config_is_valid() -> None:
    if shutil.which("docker") is None:
        pytest.fail("docker is required to run `promtool check config`")

    result = subprocess.run(
        [
            "docker", "run", "--rm",
            "-v", f"{_PROMETHEUS_DIR}:/etc/prometheus:ro",
            "--entrypoint", "/bin/promtool",
            "prom/prometheus:v3.0.1",
            "check", "config", "/etc/prometheus/prometheus.yml",
        ],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, (
        f"promtool check config failed:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    )


def test_budget_soft_limit_alert_routes_to_slack_receiver() -> None:
    """Real amtool routing resolution against the same config template +
    substitution docker-compose.dev.yml's alertmanager entrypoint applies —
    proves BudgetSoftLimitExceeded's labels resolve to the "slack" receiver,
    not just that the YAML happens to name a receiver "slack"."""
    if shutil.which("docker") is None:
        pytest.fail("docker is required to run `amtool config routes test`")

    shell_cmd = (
        'sed "s#__SLACK_WEBHOOK_URL__#https://hooks.slack.com/services/TEST#" '
        "/etc/alertmanager/alertmanager.yml > /tmp/am.yml && "
        "amtool config routes test --config.file=/tmp/am.yml "
        'alertname=BudgetSoftLimitExceeded severity=warning scope="dept:finance"'
    )
    result = subprocess.run(
        [
            "docker", "run", "--rm",
            "-v", f"{_ALERTMANAGER_DIR}:/etc/alertmanager:ro",
            "--entrypoint", "/bin/sh",
            "prom/alertmanager:v0.28.0",
            "-c", shell_cmd,
        ],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, (
        f"amtool config routes test failed:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    )
    assert result.stdout.strip() == "slack"
