# Sprint 10 — Demo Assembly & Docs — Findings Report

Branch `feat/sprint-10-demo-docs`. Tasks 10.1 (Fresh-install rehearsal) and 10.2
(Docs + release). No application-logic changes — this sprint is documentation,
one Make convenience target, and the release pipeline.

## Tasks & AC

| Task | What was built | AC result |
|---|---|---|
| **10.1 Fresh-install rehearsal** | Finalized `README.md` from the 15-line bootstrap stub into a full guide: prerequisites (incl. Windows `winget` package ids), compose quick-start, k3d path, **model-lane guidance** (local vs cloud + the embedding-dimension gotcha), seed logins, service map, and a demo walkthrough mapped to the 15-min script. Added `make seed-demo` (migrate + seed + seed-docs one-shot). | ✅ The README's compose path is exactly the fresh install performed on a clean new machine this session (tools installed, `make dev`, `seed-demo`, `make api`/`make web`, app reachable) — well within the ≤30-min target. |
| **10.2 Docs + release** | `.github/workflows/release.yml` — tag-triggered (`v*`) pipeline: lint→unit→integration→security, then `release-image` (build → trivy scan → push to GHCR, `<version>` + `latest`). `docs/runbooks/on-call.md` (health checks, common symptoms, kill switch, approvals, escalation). Demo-script dry-run. | ◑ **Demo dry-run: 16s** (Support Copilot RAG streamed+cited, Analytics text-to-SQL) — far under the ≤15-min AC. **The `v0.1.0` tag was intentionally not pushed** (user decision), so the "tag pipeline all-green" half of the AC is deferred until the tag is cut; the workflow is authored and YAML-valid. |

## What was tested and how

- **`make seed-demo`** — runs green and idempotent against the live stack
  (migrate + checkpointer + seed + KB ingest; re-run embeds 0 new chunks).
- **README** — every relative link resolves; content is grounded in the actual
  install steps and gotchas hit on this machine.
- **Demo dry-run (timed, live stack):** 16 seconds end to end —
  - Support Copilot: `agent_id=1` → streamed answer with a `chunk_ref` citation.
  - Analytics: `agent_id=2` → generated and executed
    `SELECT COUNT(*) FROM fixture_sales`.
  - RBAC on `/v1/approvals`: **403** for `user1` (member), **200** for
    `approver` — the approval queue is correctly gated.
- **Static:** `ruff` clean; `release.yml` + `ci.yml` valid YAML; unit + security
  **494 passed**. No app-logic changed, so integration is unaffected (and was
  green with cloud keys earlier this session).

## Deviations / open items

- **`v0.1.0` tag deferred** (user chose to skip). `release.yml` is ready; cutting
  the tag later triggers the full check suite + GHCR image publish and completes
  the 10.2 AC. Tagging pushes an image (outward-facing), which is why it waits on
  an explicit go.
- **Screenshots/GIFs for the deck** are not auto-generated headlessly; the web UI
  is live on `:3000` for capture when building the deck.
- The k3d fresh-install path is documented and its components were exercised in
  Sprint 9's 9.4 drill (cluster up, CNPG operator, chart install); a full
  timed clean-machine k3d run from the README alone is the natural next
  rehearsal when a truly clean environment is available.
