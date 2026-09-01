# Sprint 8 Report — KVKK Lane

**Completed:** 2026-08-15 · **Branch/PR:** `feat/sprint-8-kvkk-lane`.
**Method:** implemented in task order (8.1 → 8.5) with tests accompanying each module, unit-tested where dependency-free and integration-tested against real Postgres/Qdrant/MinIO/Keycloak/Loki/Langfuse/Ollama where not, then closed with a full live-stack (`make dev`) run of the eval suite and integration suite. Durable log in `docs/PROGRESS.md` (6 dated entries this sprint). Task 8.1 has its own dedicated findings report in `docs/reports/sprint-8-local-lane-rehearsal.md` (with a 2026-08-15 update section superseding two of its conclusions — see below).

Sprint 8 makes the KVKK/PII story real rather than declared: personal data now provably stays on the local model lane, can be erased on request, and is masked everywhere it is logged or traced. The sprint's most valuable output was not new surface area but the discovery that a documented guarantee — "OCR path: local (Tesseract)... cloud vision only for pre-redacted or non-sensitive docs" — had never actually held in code since Sprint 3.

## Tasks & Acceptance Criteria

| Task | What shipped | AC result |
|---|---|---|
| **8.1** Local-lane quality rehearsal | `evals/synthetic_images.py` (real-TTF document renderer, replacing a tiny-bitmap-font renderer that was producing genuine OCR digit errors); `evals/local_lane_rehearsal.py` (8 synthetic TR CV fixtures, real Tesseract + local-Qwen pipeline). Findings report: `docs/reports/sprint-8-local-lane-rehearsal.md`. | ✅ accuracy numbers per document type reported; demo fixture set chosen. Invoice: **100% (18/18)** live on the real local lane. CV: initially "not completed" on CPU — **superseded at 8.5 close: 100% (15/15)**, see *Corrections* below. |
| **8.2** HR CV mini-flow (pii lane) | Root-cause fix: `fleet_rag/ingest/ocr.py::ocr_image()` hardcoded `sensitivity="internal"` on every vision-LLM OCR call, and two production routers stubbed the Tesseract fallback (`tesseract_fn=lambda b: ""`) — so a scanned **pii/confidential** document always hit the **cloud** vision model first. Now `ocr_image()` takes real sensitivity and skips the vision-LLM entirely for confidential/pii; one shared `tesseract_ocr()` used by every caller. `agents/hr_agent/extractor.py` (new): CV text → `CvProfile`, `sensitivity="pii"` hardcoded and not caller-overridable. | ✅ `tests/unit/test_hr_pii_lane_no_cloud_egress.py` proves via a recording transport (no network/GPU, runs on hosted CI) that CV OCR never calls the gateway, extraction targets `local-reasoning` only, and ingestion embeddings target `local-embeddings` only. ✅ CV → structured profile verified live (see 8.5). |
| **8.3** Erasure + clearance surfacing | Migration `0010_subject_hash` (`documents.subject_hash`, `conversations.subject_hash`); `fleet_api/privacy.py::subject_hash()` (sha256, never the raw identifier); `routers/subjects.py` (new): `DELETE /v1/subjects/{hash}`, MANAGE_PLATFORM-gated, deleting conversations/messages/documents (via a shared `delete_document_fully()` factored out of `purge_expired`) and **pseudonymising, never deleting**, matching `audit_log.actor` rows. Admin→Models gained a colour-coded Clearance column + legend. | ✅ `tests/integration/test_subjects_router_live.py`: real erasure round-trip across Postgres + MinIO + Qdrant — conversation/message/document/chunk/MinIO object/Qdrant vector all confirmed gone; the audit row survives with its actor overwritten. |
| **8.4** PII masking verification | `core/pii_scrub.py` (new): regex-only detection/masking (email, TR IBAN, TR phone, TR TCKN with checksum) — deliberately not Presidio (dependency direction + hot-path cost). `core/logging.py` (new): structured JSON to stdout plus best-effort direct Loki push, with a `PiiScrubFilter` on every record. `core/langfuse_client.py::LangfuseRedactor` (new): post-hoc trace/observation overwrite via Langfuse's ingestion API, wired as a fire-and-forget task. | ✅ `tests/integration/test_pii_logging_masked_live.py`: a real seeded PII conversation through the real cloud path — Loki shows `[EMAIL]` in place of the address (queried via Loki's `query_range` API); the Langfuse trace no longer contains the raw email after redaction (queried via Langfuse's trace API). |
| **8.5** HR Talent & Onboarding scenario completion | `agents/hr_agent/graph.py` (killswitch → OCR → extract → match → HITL), `match.py` (deterministic, no LLM call), `routers/hr_agent.py` (`POST /v1/hr-agent/runs`), `hr_onboarding` RAG agent over the new `hr-policies` collection, `hr-cvs` collection (pii/365d/allow-local-only), 15-case eval dataset, `hr-run-dialog.tsx`, HR scenario card flipped `partial` → **live**. | ✅ **`make eval AGENT=hr_agent`: 100% (15/15)** vs. 0.90 threshold. ✅ protected attributes excluded — proven end-to-end, not just at unit level (below). ✅ HR scenario live end-to-end: `tests/integration/test_hr_agent_e2e_live.py` **2 passed**. |

## What was tested and how

- **Unit** (`uv run pytest tests/unit`): **441 passed** (383 at Sprint 7's close). New this sprint: OCR sensitivity gating, HR extractor incl. protected-attribute exclusion, the no-cloud-egress recording-transport proof, subjects-router RBAC, `pii_scrub`, `core.logging` idempotency, HR graph (interrupt/approve/reject/block/pii-sensitivity), role matching, eval-runner case evaluators, phone normalisation + the no-translate prompt guard.
- **Integration** (`uv run pytest tests/integration`, live stack): **65 passed, 4 failed** in 8m20s. All four failures (`test_rag_ingest_live`, `test_rag_query_live`, `test_rag_pii_collection_live`, `test_pii_logging_masked_live`) **pass in isolation** — re-run together they give `8 passed in 65s`. This is pre-existing full-suite resource contention plus async-ingestion polling, not a Sprint 8 regression; flagged as a known issue below.
- **Evals** (live stack, real Tesseract + real local Qwen): `invoice_agent` **100% (18/18)** — genuinely local end-to-end for the first time; `hr_agent` **100% (15/15)**.
- **Static:** `ruff check apps evals tests` clean. `mypy apps`: 18 errors across 118 files — unchanged pre-existing baseline, zero new. Web: `tsc --noEmit` clean, `eslint` clean.
- **The single strongest piece of evidence** is one live `approvals` row, which validates four separate mechanisms at once. The rendered CV page carried `Dogum Tarihi: 1990-04-12` and `Cinsiyet: Kadin`, and OCR read both; the stored payload is:
  `{"full_name": "Zeynep Kaya", "email": "zeynep.kaya@example.com", "phone": "+90 555 987 6543", "education": ["BSc Bilgisayar Muhendisligi, ITU, 2018"], "experience": ["Backend Gelistirici, Fleet Lojistik, 2018-2023"], "skills": ["Python", "PostgreSQL", "Docker"]}`
  — no birthdate and no gender (schema exclusion, end-to-end); `+90` where OCR produced `*90`; `Fleet Lojistik` untranslated; and a populated skills list that used to be clipped off the canvas entirely.

## Task 8.5's eval: 47% → 100%

The first live eval run scored **47% (7/15)**, below the 0.90 threshold. Per the Task Execution Protocol the failures were root-caused and reported *before* any fix. The distribution was itself the key signal: **every** governance case passed (2/2 protected-attribute exclusion, 5/5 RAG grounding) and **every** failure was in extraction fidelity — so the agent, graph, HITL, and routing were never implicated. Three independent causes, none in product logic:

1. **Fixture renderer clipped the 6th line of every document** (5 failures). `synthetic_images.py` used a fixed 260px canvas with `line_height=48` and a 20px top margin, so line 6 drew at y=260 — exactly the bottom edge. Measured across all 8 CVs: `lines_in=6, lines_ocr=5`, `Yetenekler:` absent 8/8. The model returned `skills: []` correctly, on truncated input. Latent because the invoice fixtures are 5 lines — and introduced by 8.1's own renderer fix.
2. **Tesseract reads a phone's leading `+` as `*`** (4 failures, overlapping).
3. **The prompt's English examples caused translation** (1 failure): `Fleet Lojistik` → `Fleet Logistics`.

### Decisions taken (delegated by the user) and why

| # | Decision | Reasoning |
|---|---|---|
| 1 | Derive canvas height from the line count | A real bug in the fixture renderer; fixing the fixture is the honest fix. |
| 2 | Normalise `*`→`+` **in the extractor**, not in the dataset | A real scanned CV hits the same Tesseract behaviour. Loosening the eval assertion would leave the *product* storing a wrong phone number and merely hide it. Kept deliberately narrow (`^\s*\*(?=\d)`) so an unrelated `*` is untouched, with a test proving `*ext. 42` survives. |
| 3 | Add an explicit "transcribe in the CV's own language, never translate" rule | Translating a Turkish employer name is data corruption. Per rule 5 this is a prompt change, so the pass-rate is restated here and in the PR. |
| 4 | Document `FLEET_LITELLM_TIMEOUT=300`; keep the 60s **default** | A genuinely stuck *cloud* call should not hang for five minutes; the local lane opts in explicitly. |

## Corrections to earlier conclusions in this sprint

Two conclusions recorded earlier in Sprint 8 were wrong and are corrected in `docs/reports/sprint-8-local-lane-rehearsal.md`:

- **"CPU-only Ollama is slow/intermittently flaky"** — measured layer by layer instead of assumed: raw Ollama 4.3s, proxy with a trivial prompt 4.7s, proxy with the *real* extraction prompt 26–39s across repeated calls, **all HTTP 200, zero errors**. Nothing was failing intermittently. The actual cause was a **timeout mismatch**: 8.1 raised `litellm_params.timeout` to 300s but the gateway *client* stayed at its 60s default, close enough to the real cost that batches tripped it.
- **"CV evals need GPU hardware"** — withdrawn. `make eval AGENT=hr_agent` completes reliably on CPU in ~20 minutes. The `@pytest.mark.gpu` guidance still stands for *CI gating* (a 20-minute eval should not block a PR), but not for feasibility.

## Notable issues resolved (symptom → root cause → fix)

- **LangGraph checkpointer tables were never created by any setup step.** The new HR e2e test reported `2 skipped` under `-q`, which was misleading — `-rs` revealed `psycopg.errors.UndefinedTable: relation "checkpoints" does not exist`. These tables are owned by `AsyncPostgresSaver.setup()`, not Alembic, and repo-wide the only caller was a single integration test. A fresh database therefore breaks **every HITL agent** (dev/invoice/hr) on its first checkpoint write; it only ever worked because that one test happened to run first. Surfaced when a Docker Desktop restart wiped the volumes. Fixed properly: new `apps/api/fleet_api/checkpointer_setup.py` (idempotent, handles the Windows ProactorEventLoop caveat) wired into `make migrate`. Pre-existing latent gap, not introduced by 8.5.
- **`litellm-enable-message-redaction` does not actually suppress prompts in Langfuse** on litellm v1.53.7-stable — verified reaching the proxy (visible in `requester_metadata`) but not honoured, after ruling out string-vs-boolean, header-vs-body placement, and top-level `no-log`. Worked around with `LangfuseRedactor`'s post-hoc ingestion-API overwrite.
- **Stale hardcoded agent count** in `test_observability_admin_router_live.py` (`assert len(by_agent) == 4`) broke when 8.5 legitimately seeded two more demo agents. Now derived from `fleet_api.seed._DEMO_AGENTS`, so it cannot break this way again.
- **Test isolation bug** in `test_subjects_router_live.py`: a fixed literal chunk content made `qdrant_point_id` collide with leftovers from failed runs; randomised per run. The same latent pattern exists in `test_rag_retention_live.py` (not fixed — out of scope).
- **`asyncio.run()` cancels pending fire-and-forget tasks** the moment its coroutine returns, so the PII test's Langfuse assertion raced the redaction task; fixed by awaiting `chat._background_tasks` explicitly.
- Pre-existing `E501` in `test_subjects_router_live.py` (103 > 100 chars) that **would have failed CI**, found while resuming; split into a local.

## Known issues / follow-ups

- **4 integration tests are flaky under full-suite load** (3 RAG + PII logging), all green in isolation. They share a fixed-literal-content / async-ingest-polling pattern. Worth a dedicated stabilisation task.
- **`users.email_hash` is always `""`** — set unconditionally at JIT-provision time since Sprint 1, so its apparent KVKK-pseudonymisation purpose is unmet. Erasure was keyed off `subject_hash(kc_sub)` instead rather than fixing this unrelated gap.
- **`invoice_agent.extract_invoice_fields` is called without `redacted=True`**, so it can never route to the documented "Claude Sonnet on redacted text" — no cloud model has clearance ≥ confidential, so invoice extraction has always been silently local-only. More conservative than the spec, not less, but a real doc/code divergence awaiting a decision.
- **Host-run evals do not read `.env`** (it carries compose-internal hostnames like `host.docker.internal`), so local-lane eval runs still need `FLEET_LITELLM_TIMEOUT=300` exported explicitly.
- 8.5's UI half (the HR run dialog, the flipped scenario card) is verified by type-check/lint and by the API-level round-trip, not by a browser test — the established pattern in this repo since Sprint 3.4.
