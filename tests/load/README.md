# Load tests (k6) — task 9.1

k6 scenarios that assert the TRD §10 SLOs as **thresholds**, so a run exits
non-zero on an SLO breach (CI/pre-release gate).

| Script | Shape | Purpose |
|---|---|---|
| `chat_smoke.js` | 50 VU / 5m steady | Baseline chat latency under sustained interactive load |
| `mixed_day.js` | ramp chat (→80 VU) + steady automation arrival | Chat SLOs **under** background automation contention (n8n-style runs) |

SLO thresholds (from TRD §10, encoded in each script's `options.thresholds`):

- chat **first token** p50 < 2s, p95 < 6s
- full stream p95 < 10s (smoke)
- errors < 1% (smoke) / < 2% (mixed_day, deliberately higher contention)

## Running

```bash
make load TEST=chat_smoke        # writes tests/load/reports/chat_smoke.json
make load TEST=mixed_day
```

The `make load` target writes a machine-readable summary to
`tests/load/reports/<TEST>.json` — **the report is committed to the repo** (the
9.1 AC: "SLO thresholds pass in k6 report stored in repo").

### Targeting

Defaults point at the `make dev` compose stack (`localhost:8000` API,
`localhost:8080` Keycloak). To run against the k3d cluster, point the env at the
ingress:

```bash
FLEET_API_BASE=http://fleet.localhost \
FLEET_KEYCLOAK_BASE=http://keycloak.fleet.localhost \
  make load TEST=chat_smoke
```

Overridable env: `FLEET_API_BASE`, `FLEET_KEYCLOAK_BASE`, `FLEET_AGENT_SLUG`,
`VUS`, `DURATION`, `AUTOMATION_RATE`.

### Prerequisites

- **k6** installed (`winget install k6` / `brew install k6` / [k6.io/docs](https://k6.io/docs/get-started/installation/)).
- A running stack (compose or k3d) with the synthetic seed users
  (`builder`/`user1`/`user2`) and at least one agent — `make dev && make seed`.

## How first-token latency is measured

k6's HTTP client buffers the full response, so `sendMessage` uses
`res.timings.waiting` (time-to-first-byte) as the first-token proxy and locates
the first `event: token` SSE frame to confirm streaming happened. The absolute
first-token number is therefore slightly pessimistic (TTFB ≈ first token for a
streamed response), which is fine for catching SLO **regressions** — the purpose
of the gate.
