"""Prometheus HTTP metrics for the API layer (task 7.4, TRD §6/§13.5).

Labeled by the matched route's *path template* (e.g. `/v1/widgets/{id}`),
never the raw resolved path — using resolved paths would create one label
series per distinct id ever requested, an unbounded-cardinality footgun
Prometheus users hit constantly with path-based APIs.
"""

from __future__ import annotations

from prometheus_client import Counter, Gauge, Histogram

HTTP_REQUESTS_TOTAL = Counter(
    "fleet_http_requests_total",
    "HTTP requests handled, by method/route template/status.",
    ["method", "path", "status"],
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "fleet_http_request_duration_seconds",
    "HTTP request latency in seconds, by method/route template.",
    ["method", "path"],
)

# Computed at scrape time in routers/metrics.py, not pushed incrementally —
# both are cheap aggregate reads (dept-scoped spend_ledger sums, a Redis
# ZCARD) recomputed fresh on every /metrics poll rather than kept live.
DEPT_DAILY_SPEND_USD = Gauge(
    "fleet_dept_daily_spend_usd",
    "Today's spend so far for the department (TRD §5 cost anomaly alert).",
    ["dept_id"],
)

DEPT_AVG_DAILY_SPEND_7D_USD = Gauge(
    "fleet_dept_avg_daily_spend_7d_usd",
    "Department's average daily spend over the trailing 7 days.",
    ["dept_id"],
)

QUEUE_DEPTH = Gauge(
    "fleet_queue_depth",
    "Pending jobs in an arq queue (ZCARD of arq's default sorted-set key).",
    ["queue"],
)
