"""Prometheus metrics shared across the runtime (task 7.4, TRD §6/§13.5).

Registers into prometheus_client's process-global `REGISTRY` — a single
`/metrics` route in fleet_api (apps/api/fleet_api/routers/metrics.py) exposes
whatever has been imported into the process, this module included, without
either side needing to know about the other's collector instances.
"""

from __future__ import annotations

from prometheus_client import Counter

BUDGET_SOFT_LIMIT_TOTAL = Counter(
    "fleet_budget_soft_limit_total",
    "LLM calls whose budget scope crossed its soft limit (TRD §5).",
    ["scope"],
)
