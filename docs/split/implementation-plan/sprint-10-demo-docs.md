# Implementation Plan · Sprint 10 — Demo Assembly & Docs

<!-- Derived from docs/IMPLEMENTATION_PLAN.md. The original is canonical.
     Any change here must also be applied to docs/IMPLEMENTATION_PLAN.md in the same PR. -->

## Sprint 10 — Demo Assembly & Docs

- **10.1 Fresh-install rehearsal.** Finalize README (install steps, demo walkthrough — bootstrapped in 1.1); `make k3d-up` from README alone on a clean machine; demo seed scenario data.
  **AC:** clean machine → running demo in ≤30 min following README.
- **10.2 Docs + release.** Runbooks (restore, on-call basics); demo script (below) dry-run; screenshots/GIFs for the deck; tag v0.1.0. A tag-triggered GitHub Actions release pipeline (TRD §14) runs the full check suite and builds the release images.
  **AC:** the tag pipeline runs all CI jobs green on the `v0.1.0` tag; dry-run completes within 15 min.

---
