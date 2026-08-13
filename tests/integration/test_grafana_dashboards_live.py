"""Integration: Grafana actually provisions both Fleet dashboards (task 7.4)
from infra/compose/grafana/provisioning against a real Grafana container —
not just "the JSON parses". Also guards the datasource-uid gotcha this task
hit once already: dashboards.json referencing `"uid": "Prometheus"` (the
datasource's *name*) instead of the uid datasources.yml actually assigns
loads cleanly (Grafana doesn't fail provisioning on a dangling datasource
ref, it just silently renders broken panels), so this asserts against the
real /api/search response, not just "no errors in the logs".
"""

from __future__ import annotations

from pathlib import Path

import httpx
import pytest
from testcontainers.core.container import DockerContainer
from testcontainers.core.waiting_utils import wait_for_logs

_PROVISIONING_DIR = (
    Path(__file__).resolve().parents[2] / "infra" / "compose" / "grafana" / "provisioning"
)


@pytest.fixture(scope="module")
def grafana() -> str:
    container = (
        DockerContainer("grafana/grafana:11.4.0")
        .with_env("GF_SECURITY_ADMIN_PASSWORD", "admin")
        .with_volume_mapping(str(_PROVISIONING_DIR), "/etc/grafana/provisioning", mode="ro")
        .with_exposed_ports(3000)
    )
    with container:
        wait_for_logs(container, "HTTP Server Listen", timeout=60)
        host = container.get_container_host_ip()
        port = container.get_exposed_port(3000)
        yield f"http://{host}:{port}"


def test_both_fleet_dashboards_are_provisioned(grafana: str) -> None:
    resp = httpx.get(
        f"{grafana}/api/search", params={"type": "dash-db"}, auth=("admin", "admin"), timeout=10
    )
    resp.raise_for_status()
    dashboards = {d["uid"]: d for d in resp.json()}

    assert "fleet-api-health" in dashboards
    assert dashboards["fleet-api-health"]["title"] == "Fleet API Health"
    assert "fleet-cost-budgets" in dashboards
    assert dashboards["fleet-cost-budgets"]["title"] == "Fleet Cost & Budgets"


def test_dashboard_panels_resolve_the_real_prometheus_datasource_uid(grafana: str) -> None:
    resp = httpx.get(
        f"{grafana}/api/dashboards/uid/fleet-api-health", auth=("admin", "admin"), timeout=10
    )
    resp.raise_for_status()
    panels = resp.json()["dashboard"]["panels"]
    assert len(panels) > 0

    ds_resp = httpx.get(
        f"{grafana}/api/datasources/name/Prometheus", auth=("admin", "admin"), timeout=10
    )
    ds_resp.raise_for_status()
    real_uid = ds_resp.json()["uid"]

    for panel in panels:
        assert panel["datasource"]["uid"] == real_uid
