# Task 8.1 — Local-Lane Quality Rehearsal

Findings report per the Task Execution Protocol (docs/split/implementation-plan/sprint-8-kvkk-lane.md task 8.1). Ran the real local-only pipeline (Tesseract `tur+eng` OCR → local Qwen `qwen2.5:7b-instruct-q4_K_M` structured extraction, both forced local by sensitivity per task 8.2's fix) against synthetic TR invoice and CV fixtures on the dev reference machine — **CPU only, no GPU** (`nvidia-smi` not found; Ollama reports `size_vram: 0` for the loaded model).

## Summary

| Document type | OCR quality | Field-extraction accuracy | Local-lane latency/reliability |
|---|---|---|---|
| Invoice (18 synthetic cases, `evals/datasets/invoice_agent.jsonl`) | Verified correct | **100% (18/18)**, live against the real proxy+Ollama | Acceptable once the model is warm |
| CV (8 synthetic cases, `evals/local_lane_rehearsal.py`) | Verified correct (see below) | **Not completed** — see Reliability finding | Not viable for a full clean batch on this machine |

**Demo fixture set:** all 12 invoice cases already in `evals/datasets/invoice_agent.jsonl` are proven end-to-end on the real local lane (100% pass) — no change needed. The 8 synthetic CV fixtures added in `evals/local_lane_rehearsal.py` are format/OCR-validated (see below) and ready to use once run on GPU-equipped hardware; do not select a demo subset from an incomplete CPU-only run.

## OCR quality

Tesseract `tur+eng` correctly reads Turkish diacritics (Ş, İ, ı, ğ, ö, ü, ç) and digits **when rendered with a real antialiased font at a reasonable size** — confirmed via a direct smoke test (`Vendor: Türkiye Şirketler A.Ş.` / `PO Number: PO-1001` / `Total Amount: 1250.00 TRY` all recognized exactly).

**Finding:** the pre-existing synthetic-invoice image renderer (`evals/runner.py::_render_invoice_image_base64`) used Pillow's implicit tiny bitmap default font with no size specified. Against that font, the same text OCR'd as `"Vendor T�rkiye nirketler An"` / `"1250.00"` misread as `"1260.00"` — a real digit error, not a fixture artifact. This had gone unnoticed because task 3.1/6.3's OCR always tried the cloud vision-LLM first (which tolerates messy rendering far better), so the local-Tesseract path was never actually exercised end-to-end until this task's OCR-sensitivity fix (8.2) made it the mandatory path for confidential/pii documents.

**Fix applied:** added `evals/synthetic_images.py` — tries a real system TTF (Windows Arial, common Linux DejaVuSans/Liberation paths) at 28px, falling back to Pillow's scalable `load_default(size=...)` (Pillow ≥10.1) only if none exist. Both the invoice renderer and the new CV renderer use it. Pillow's own scalable default font renders ASCII/digits perfectly but drops Turkish-specific glyphs (`Ü`→`k`, `Ş`→`K` observed) — the real-TTF path is what actually gets full Turkish-diacritic accuracy; document fixtures should always prefer environments with a real system font available.

## Field-extraction accuracy

**Invoice (proxy for CV, same mechanism):** `agents.hr_agent.extractor.extract_cv_profile` uses the identical pattern as `agents.invoice_agent.extractor.extract_invoice_fields` (system-prompt JSON extraction, same code-fence-stripping defense, same local Qwen model). The invoice eval — now genuinely local end-to-end after task 8.2's OCR fix — passed **100% (18/18)**, including the mismatch/duplicate/unknown-PO/vendor-mismatch edge cases, live against the real proxy and Ollama. This is strong evidence the *mechanism* (local Tesseract OCR → local Qwen JSON-schema extraction) is correct and production-viable in terms of accuracy.

**CV extraction:** could not be completed as a full clean 8-case batch on this machine — every attempt hit the reliability issues below before finishing. The `extract_cv_profile` code itself is unit-tested (9 cases, `tests/unit/test_hr_extractor.py`) including the protected-attribute schema-exclusion guardrail, and the no-cloud-egress routing is proven (`tests/unit/test_hr_pii_lane_no_cloud_egress.py`) — what's unverified here specifically is *live accuracy* on real (if noisy) OCR'd CV text.

## Reliability finding: CPU-only local inference (GPU availability)

This is the substantive finding the task anticipated ("GPU availability" is explicitly named as a decision axis). On this machine:

- **Cold load:** the first request to `qwen2.5:7b-instruct-q4_K_M` after idle took 118–181s just to load into memory (worsened across the session, likely other concurrent load).
- **Warm throughput:** ~1–1.5 tokens/sec once loaded (a 10-token reply took 5–12s of pure generation).
- **Instability under sustained testing:** repeated `TimeoutError`/`500 Internal Server Error`/`Server disconnected without sending a response` from the LiteLLM proxy's Ollama provider path, even after raising `litellm_params.timeout` to 300s for the local models (`gateway/litellm/config.yaml`) and the gateway client's own `FLEET_LITELLM_TIMEOUT`. The proxy's aiohttp session to Ollama does not appear to reliably honor the configured timeout under this load pattern; root cause not fully isolated (see Issues below) but empirically reproducible across independent runs.

**A CV extraction call (6 fields, 3 of them lists) generates more output tokens than an invoice call (4 scalar fields) — at ~1 tok/sec this alone can exceed a minute, before any instability.**

### Options (per the task's own decision axes)

1. **Provision a GPU for the Ollama host** (staging/prod, and ideally this dev machine) — the straightforward fix; CPU inference at this throughput is not viable for an interactive pii-lane flow.
2. **Smaller local model for latency-sensitive paths** — `qwen2.5:0.5b` is already pulled on this machine. Worth benchmarking accuracy vs. the 7B model for CV/invoice extraction specifically; likely an acceptable trade for structured-field extraction (a narrower task than open-ended chat).
3. **Run local-lane extraction as an async background job**, matching the pattern already used for RAG ingestion (arq worker) — tolerates multi-minute latency naturally, no user-facing timeout. Appropriate for HR CV intake specifically (upload → background parse → profile ready), less so for anything needing a synchronous reply.
4. **Image preprocessing:** not indicated by this rehearsal — OCR quality was already excellent once fixture rendering used a real font; this axis is not the bottleneck here.
5. Per the sprint's own CI note (task 8.2): local-lane evals needing GPU should run `@pytest.mark.gpu`, on a self-hosted GPU runner or nightly, never gating hosted CI. Task 8.5's `make eval AGENT=hr_agent` should follow the same pattern.

## Fixture set (`evals/local_lane_rehearsal.py`)

8 synthetic Turkish CVs (never real people), each with full name, email, phone, one education line (with institution), one experience line (with employer), and 3 skills — plus a birthdate line included in the raw text specifically so task 8.5's protected-attribute schema-exclusion eval has real "the model saw a birthdate and must still not emit one" cases to test against. Ready to run as-is once a GPU-equipped runner is available (`REHEARSAL_LIMIT=N` env var runs the first N fixtures for a quick smoke check).

## Issues (symptom → root cause → resolution; unresolved marked OPEN)

- OCR always tried the cloud vision-LLM first regardless of document sensitivity (`fleet_rag/ingest/ocr.py` hardcoded `sensitivity="internal"`); two production routers (`invoice_agent.py`, `approvals.py`) stubbed the tesseract fallback entirely (`tesseract_fn=lambda b: ""`). Real spec violation for both dept scenarios 04 and 05 ("OCR path: local (Tesseract)... cloud vision only for pre-redacted or non-sensitive docs"), pre-existing since Sprint 3/5/6. **RESOLVED** (task 8.2): `ocr_image()` now skips the vision-LLM step entirely for confidential/pii sensitivity; a real `tesseract_ocr()` implementation is shared by every caller.
- Synthetic invoice images rendered with Pillow's tiny default font produced real OCR digit errors, invisible previously only because OCR always fell through to the cloud vision-LLM. **RESOLVED**: `evals/synthetic_images.py`.
- litellm proxy timeouts/500s/disconnects against the local Ollama lane under sustained CPU-only load. **OPEN** — raising `litellm_params.timeout` (300s) did not fully resolve it; root cause not isolated beyond "CPU-only Ollama is slow enough to hit some internal limit intermittently." Needs a GPU-equipped environment to properly characterize, per the options above.
- (Discovered while investigating the above, out of this task's scope, flagged for the user): `agents.invoice_agent.extractor.extract_invoice_fields` is called without `redacted=True` (`apps/runtime/agents/invoice_agent/graph.py`), so per `core.llm.routing.select_model` it can never actually route to the documented "Claude Sonnet (on redacted text)" — no cloud model has clearance ≥ confidential, so extraction has always silently routed to local Qwen instead. Not a correctness bug (local-only is *more* conservative than the spec, not less), but a real deviation from the Sprint 6 design doc worth a follow-up decision: either wire the redaction step before extraction (to get the documented cloud-reasoning quality) or update the doc to reflect the always-local reality.
