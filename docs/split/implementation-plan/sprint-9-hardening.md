# Implementation Plan · Sprint 9 — Hardening

<!-- Derived from docs/IMPLEMENTATION_PLAN.md. The original is canonical.
     Any change here must also be applied to docs/IMPLEMENTATION_PLAN.md in the same PR. -->

## Sprint 9 — Hardening

- **9.1 Load.** k6: chat_smoke + mixed_day against k3d; fix hotspots (pool sizes, HPA values).
  **AC:** SLO thresholds pass in k6 report (stored in repo).
- **9.2 Security.** `make scan` clean of high-sev; in-repo injection corpus vs Support Copilot, findings triaged.
  **AC:** injection corpus: 0 successful instruction-follows from quarantined content.
- **9.3 [DEFERRABLE] Chaos-lite + garak.** garak probe suite; kill-switch drill (pause agent mid-load); pod-kill during agent run → resume from checkpoint verified. *(Injection corpus tests in 9.2 are NOT deferrable.)*
  **AC:** resume test green; kill switch takes effect ≤5s under load.
- **9.4 Backup & restore drill.** CloudNativePG scheduled backups (WAL → MinIO), Qdrant nightly snapshots → MinIO, MinIO versioning enabled (TRD §14); restore runbook exercised.
  **AC:** Postgres point-in-time restore and a Qdrant snapshot restore succeed on a scratch k3d cluster; `docs/runbooks/restore.md` updated with the actual commands used.
