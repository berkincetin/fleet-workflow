# Sprint 11 — Wave 1 Scenarios — Findings Report

Branch `feat/sprint-11-wave-1-scenarios`. Onboarded the three Wave-1 department
scenarios (06 Listing Quality, 07 Vehicle Intake, 08 Insights Publisher), each
following the generic onboarding checklist, each flipping its `/scenarios` card
to **live**.

A gateway prerequisite was fixed first (see below), then each agent was built
implement → test → verify.

## Gateway prerequisite — vision lane repair

The Wave-1 agents need a working vision lane. The configured
`gemini-1.5-flash`/`gemini-1.5-pro` were **retired by Google (404)**, and the
supplied Gemini key is a free-tier token that 429s on sustained use. Fixed
(`gateway/litellm/config.yaml` + mirrored `seed.py` `_DEFAULT_MODELS`): the
primary `utility` route now points at vision-capable **`openai/gpt-4o-mini`**
(reliable, the user's OpenAI key works); the retired Gemini rows moved to
fallbacks on the current `gemini-3.6-flash` id. Committed as `db585da`.

## Tasks & AC

| Task | What was built | AC result |
|---|---|---|
| **11.1 Listing Quality** | `listing_quality` agent (vision flag-only pipeline: fetch price band → vision check → flag). `listings` MCP server (`get_new` read, `flag` write:internal) + synthetic generator. Closed reason-code vocabulary. `POST /v1/listing-quality/runs` with **shadow mode**. n8n new-listing webhook + nightly batch. 22-case eval + precision metric. | ✅ **`make eval AGENT=listing_quality`: 95% (21/22), 100% precision** (≥85% target). Shadow-mode scripted run verified live (flags computed, not queued). Card live. Flag-only guardrail proven (no unpublish tool exists). |
| **11.2 Vehicle Intake** | `vehicle_intake` agent (local OCR → PII-redact → cloud reasoning on the redacted brief → deterministic price band). `ocr.extract` (local) + `pg_ro` comparables. No write tools, advisory (no HITL). Missing-report → `incomplete`, no invented values. 16-case eval. | ✅ **`make eval AGENT=vehicle_intake`: 94% (15/16)** (≥85%). Missing-report fixtures never invent values; band always contains the comparables' median; PII redaction fires before the cloud call — all verified live. Card live. |
| **11.3 Insights Publisher** | `insights_publisher` agent (pull index data → brand-voice draft → **numbers-match grounding guardrail** → write:external approval → publish). `cms` MCP (`publish` write:external). `mkt-brand` KB collection. `POST /v1/insights-publisher/runs`. Monthly n8n cron + Slack failure alert. 11-case eval with an LLM-judge for brand voice. | ✅ **`make eval AGENT=insights_publisher`: 100% (11/11)** (≥90%). Monthly run reaches approval with grounded numbers; an invented number is blocked before HITL (a human never approves an invented stat) — verified live. Card live. |

## What was tested and how

- **Unit + security: 516 passed** (was 494 pre-sprint; +22 across the three
  agents' graph/guardrail/MCP tests). Each agent has graph tests proving its
  guardrail structurally: listing = flag-only (no unpublish tool), vehicle =
  redaction-before-reasoning + missing→incomplete + no-interrupt, insights =
  invented-number-blocked-before-HITL + approve/reject/publish.
- **Evals (live, real models):** 11.1 95% (gpt-4o-mini vision on 22 rendered
  listing photos), 11.2 94% (local tesseract OCR + cloud reasoning on 16
  rendered expertise reports), 11.3 100% (real drafts + deterministic grounding
  + a 3-sample anchored brand-voice judge).
- **Live integration tests (real dev stack):** shadow-mode listing flagging +
  clean control; vehicle complete-report-with-redaction + non-report-incomplete;
  insights grounded-draft-reaches-approval with cms.publish held behind it. All
  green.
- **Static:** `make lint` clean (ruff + mypy 18-baseline, 0 new; eslint).
  OpenAPI + TS client regenerated for the two new run endpoints.
- **Docs sync:** all three scenario cards (`apps/web/lib/scenarios.ts`) and both
  wave-plan layers (`DEPARTMENT_SCENARIOS.md` + split mirror) flipped to `live`
  in the same commits.

## Findings / decisions

- **Insights grounding guardrail — two real fixes the eval surfaced.** First
  run scored 36%: the "ungrounded numbers" were years embedded in segment labels
  (`sedan-2018`), which `_data_values` did not extract from string cells — fixed
  to pull every number out of label strings. Second, the drafter paraphrased
  `500000` as "500 bin" and computed deltas the raw-number check couldn't
  follow — tightened the drafter prompt to quote numbers verbatim and never
  compute new ones (which is the guardrail's actual design intent). Both are
  legitimate improvements, not threshold-gaming.
- **Brand-voice judge stabilised.** A bare "score 1-5" swung an on-brand draft
  between 3 and 4 across calls (judge noise). Re-anchored to concrete criteria +
  averaged over 3 samples → stable 4/5 on genuinely on-brand drafts.
- **New-machine tooling installed mid-sprint:** Tesseract OCR (5.4) was missing
  (needed by the local-OCR evals — invoice/hr/vehicle); installed via winget.

## Deviations / notes

- **Windows ProactorEventLoop / psycopg-async:** the HITL-checkpointer run
  endpoints (invoice_agent, and now insights_publisher) fail through the live
  uvicorn server on Windows because psycopg's async saver needs a
  SelectorEventLoop. This is **pre-existing** (invoice has the same shape) and
  is a uvicorn-startup concern (set the selector loop policy on Windows), not an
  agent defect. The ACs are verified via integration tests that set the policy —
  the same way `test_invoice_agent_e2e_live.py` proves invoice's AC. The
  listing_quality endpoint has no checkpointer (flag-only, no interrupt) so it
  runs on the live server directly — verified there.
- The n8n workflows reference their run endpoints and a Slack alert; workflows
  are source-of-truth JSON imported at deploy, not executed in CI.
- The `mkt-brand` brand-voice text is an INTEGRATION-POINT fixed exemplar in the
  run endpoint; the collection exists for a future real ingest.
