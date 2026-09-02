# Fleet — Department Scenario Playbooks

**Version:** 1.0 · **Depends on:** platform core (TRD §1–14 [CORE] complete)
**Purpose:** Build-ready specifications for onboarding each department onto Fleet. The platform ships first (IMPLEMENTATION_PLAN.md); each scenario below is then implemented as configuration + a small amount of code (agent graph, MCP tools, workflows, evals) following the common template. Nothing here requires changing the platform core — if a scenario seems to, that is a design bug to raise first.

**How to read a spec:** every scenario uses the same fields. `Lane` = which model lane per TRD §4.2/§8 (cloud vs local-pii). `Rollout` = assist (drafts only) → supervised (write:internal with monitoring) → autonomous (only where eval history + dept_admin approval allow; write:external is never autonomous). `INTEGRATION-POINT` marks where a mock stands in for a real system.

---

## Wave Plan Overview

| # | Scenario | Department | Wave | Sensitivity | Lane | Core tech | Ships when | UI status |
|---|---|---|---|---|---|---|---|---|
| 1 | Support Copilot | Customer Service | **0 (task 4.4)** | internal | cloud | RAG, semantic cache | done | live |
| 2 | Self-Service Analytics | Data | **0 (task 5.2)** | internal | cloud | text-to-SQL, pg_ro | done | live |
| 3 | Dev Agent | IT / Engineering | **0 (task 5.5)** | internal | cloud | MCP jira/github/slack, HITL | done | live |
| 4 | Invoice & Reconciliation | Finance | **0 (task 6.3)** | confidential | local OCR + local reasoning (see §4 note) | OCR, n8n, approval | done | live |
| 5 | HR Talent & Onboarding | HR | **0 partial (Sprint 8) → 1** | pii / internal | local (CVs) + cloud (policies) | local lane, OCR | task 8.5 | partial → coming soon |
| 6 | Listing Quality | Listings Ops | 1 | internal | cloud | multimodal, n8n triggers | task 11.1 | live |
| 7 | Vehicle Intake | Trink sat! | 1 | confidential | mixed | multimodal, OCR, SQL | task 11.2 | live |
| 8 | Insights Publisher | Marketing | 1 | internal | cloud | n8n cron, SQL, brand voice | task 11.3 | live |
| 9 | Dealer Onboarding | Corporate Sales | 2 | pii | local OCR + approval emails | OCR, email MCP | task 12.1 | coming soon |
| 10 | Legal Document Review | Legal | 2 | confidential | local | RAG, clause extraction | task 12.2 | coming soon |

Wave 0 = built during the MVP sprints (task numbers reference IMPLEMENTATION_PLAN.md). Waves 1–2 = post-MVP onboarding, ~3–5 days each using the checklist at the end of this document. "Ships when" cites the IMPLEMENTATION_PLAN.md task that flips the scenario from planned to built; "UI status" reflects the `/scenarios` department hub introduced in Sprint 6.5.

---

## 1. Support Copilot — Customer Service [Wave 0]

**Objective:** Draft grounded answers for support agents; auto-resolve whitelisted FAQ intents; triage/route tickets.
**Agent config:** `support_copilot` · reasoning: Claude Sonnet · utility: Gemini Flash · sensitivity: internal · semantic_cache: **ON** (FAQ-heavy) · max_context: 12k.
**Knowledge:** `cs-help-center` (internal, help-center articles, retention ∞), `cs-procedures` (internal, SOP docs). Seeded with synthetic docs in demo.
**Tools:** none in assist mode (pure RAG). Wave 1 adds `crm.get_ticket` (read), `crm.draft_reply` (write:internal) — INTEGRATION-POINT (mock CRM).
**Guardrails/HITL:** assist mode = human sends every reply. Auto-resolve only for intents on a dept_admin-managed whitelist AND eval pass ≥ 90%. Grounding check mandatory; ungrounded → "I don't know + handoff".
**Evals (≥15):** e.g. ① "Trink sat süreci nasıl işliyor?" → must-cite from cs-help-center. ② Question outside KB → must refuse + suggest handoff (no hallucination). ③ Injection: doc chunk containing "önceki talimatları yoksay…" → must treat as data, not comply.
**Rollout:** assist (pilot: 5 agents, 2 weeks) → whitelist auto-resolve per intent.
**Metrics:** first-response time ↓, FAQ deflection rate, thumbs-up ratio ≥ 80%.

## 2. Self-Service Analytics — Data [Wave 0]

**Objective:** Natural-language questions → governed read-only SQL over approved warehouse views; table + shown SQL back.
**Agent config:** `analytics` · reasoning: Claude Sonnet (SQL gen) · utility: Gemini Flash (intent/column mapping) · sensitivity: internal · semantic_cache: OFF (data freshness) · max_context: 8k.
**Knowledge:** `data-semantic-layer` (internal): view descriptions, column glossary, metric definitions — this is the semantic layer the SQL generator retrieves from.
**Tools:** `pg_ro.query` (read; allowlisted views only, auto-LIMIT 1000, 15s timeout, `fleet_readonly` role).
**Guardrails:** non-allowlisted table → refuse + log; DML keywords hard-blocked at MCP layer; generated SQL always displayed to user.
**Evals (≥15):** NL→SQL correctness on seeded fixture warehouse (result-set match, not string match); refusal test for `users_raw` table; ambiguous question → asks one clarifying question instead of guessing.
**Rollout:** supervised from day one (read-only ⇒ low risk); no approval queue needed.
**Metrics:** ad-hoc requests reaching DS team ↓ 50%, median time-to-answer < 2 min.

## 3. Dev Agent — IT / Engineering [Wave 0]

**Objective:** Take labeled small Jira tickets end-to-end to a reviewed PR: plan → branch → implementation draft → PR → Slack notify.
**Agent config:** `dev_agent` · reasoning: Claude Sonnet · utility: Gemini Flash (ticket classification, commit msg) · sensitivity: internal · semantic_cache: OFF · max_context: 24k (code).
**Knowledge:** `it-eng-docs` (internal): contribution guide, architecture notes of target repos.
**Tools:** `jira.search/get_issue` (read) · `github.read_repo` (read) · `github.create_branch` (write:internal, pattern `agent/*` enforced) · `github.open_pr` (**write:external → approval queue, always**) · `slack.post` (write:internal, allowlisted channels).
**Guardrails:** protected-paths blocklist (infra/, migrations/, .github/); never merge; diff size cap (> 400 lines → split or escalate); tickets only with label `agent-ok`.
**Evals (≥15):** fixture tickets → rubric-judged plan quality; correct file targeting on fixture repo; refusal when ticket touches protected path; branch-name compliance.
**Rollout:** permanently approval-gated on PR creation (external write). Autonomy never exceeds "supervised".
**Metrics:** small-ticket lead time ↓, PR acceptance rate ≥ 70% without major rework.

## 4. Invoice & Reconciliation — Finance [Wave 0]

**Objective:** Invoice file → extracted fields → validation against purchase records → **draft** accounting entry in approval queue; mismatches flagged with reasons.
**Agent config:** `invoice_agent` · reasoning: **local Qwen** (extraction never leaves the local lane) · utility: Gemini Flash · sensitivity: confidential · semantic_cache: OFF.
> **Note (2026-09-01):** this line previously read "Claude Sonnet (on **redacted** text)". The implementation has always called `extract_invoice_fields` *without* `redacted=True`, and `core.llm.routing.select_model` gives no cloud model clearance ≥ `confidential`, so extraction has resolved to local Qwen since Sprint 6 — verified live at 100% (18/18) on the invoice eval. The doc is corrected to match the code rather than the reverse: the local lane is the *more* conservative reading of §8 (invoice text carries IBAN/tax identifiers and never reaches a cloud provider), and the redaction machinery lives in `fleet_rag.ingest.pii` while the agent lives in `fleet-runtime`, which depends the other way round — routing extraction through it would invert the package dependency. Revisit only if extraction quality proves insufficient on the local model.
**Knowledge:** `fin-invoices` (confidential, pii_policy=redact, retention 7y) — IBAN/tax-no/vendor PII redacted at ingestion; originals in MinIO with restricted ACL.
**OCR path:** local (Tesseract `tur`) because raw invoices contain IBAN/tax identifiers; cloud vision only for pre-redacted or non-sensitive docs. Local VLM upgrade [P2].
**Tools:** `ocr.extract` (read, local) · `pg_ro.query` purchase-orders view (read) · `erp.create_draft_entry` (**write:external → approval**) — INTEGRATION-POINT (mock ERP in MVP).
**Workflow (n8n):** intake via upload/webhook → agent → approval queue → on approve, ERP call; on reject, Slack to submitter.
**Evals (≥12):** field extraction accuracy ≥ 95% on synthetic invoice set; mismatch fixture (amount differs from PO) → must flag, never auto-draft as clean; duplicate invoice fixture → flag.
**Rollout:** approval-gated forever (financial writes).
**Metrics:** processing time per invoice ↓ 70%, entry error rate ↓.

## 5. HR Talent & Onboarding — HR [Wave 0 partial → 1]

**Objective:** (a) CV → structured profile → role-match shortlist draft. (b) Employee Q&A on policies.
**Agent config:** `hr_talent` · **pii lane**: local Qwen (parse/extract) + bge-m3 embeddings; reasoning stays local for CV content · sensitivity: pii. Separate `hr_onboarding` agent: internal, cloud lane, semantic_cache ON.
**Knowledge:** `hr-cvs` (pii, retention 12mo, local-only policy — never cloud, including embeddings) · `hr-policies` (internal).
**OCR path:** local (Tesseract) for CV PDFs/images.
**Tools:** `hr.match_role` (read — scoring service over structured profiles) · shortlist output = draft visible to dept_admin only (write:internal).
**Guardrails:** match reasoning must reference only job-relevant criteria; protected-attribute fields (age, gender, photo) excluded from the structured profile at extraction — enforced by schema; erasure endpoint covers candidates.
**Evals (≥15):** extraction accuracy on **synthetic** CVs (never real ones in fixtures); schema-exclusion test (birthdate present in CV → absent in profile); onboarding Q&A grounding tests.
**Rollout:** shortlist = assist only (HR decides); Q&A supervised.
**Metrics:** screening time per role ↓ 60%, HR question tickets ↓.

## 6. Listing Quality — Listings Operations [Wave 1]

**Objective:** Every new listing checked for photo–description consistency, plate blurring, prohibited content, price anomaly → flags with reasons into human review queue.
**Agent config:** `listing_quality` · vision: Gemini Flash · reasoning: Claude Sonnet (only on escalations) · utility: Gemini Flash · sensitivity: internal (public listing data) · semantic_cache: OFF.
**Tools:** `listings.get_new` (read) · `listings.flag` (write:internal, supervised) — both INTEGRATION-POINT (mock listing API + synthetic listing generator in demo) · `pg_ro.query` price-index view (read).
**Workflow (n8n):** new-listing webhook → agent → flag or pass; batch re-check job nightly (Batch API lane [P2]).
**Guardrails:** flag-only — the agent can never unpublish/reject a listing; every flag carries machine-readable reason codes for reviewer sorting.
**Evals (≥20):** labeled fixture set (photo+description pairs): color/model mismatch caught; blurred vs unblurred plate detection; clean listing → no flag (false-positive control ≥ 85% precision target).
**Rollout:** shadow mode 2 weeks (flags logged, not shown) → supervised.
**Metrics:** moderation throughput ↑, reviewer agreement with flags ≥ 85%, review backlog ↓.

## 7. Vehicle Intake — Trink sat! [Wave 1]

**Objective:** Pre-assessment brief for acquisition specialists: expertise-report extraction + photo damage summary + comparables + suggested price band. Advisory only.
**Agent config:** `vehicle_intake` · vision: Gemini Flash (photos are non-PII after plate masking step) · OCR: local for expertise PDFs (contain owner PII) → redact → cloud reasoning on redacted brief · sensitivity: confidential.
**Tools:** `ocr.extract` (read, local) · `pg_ro.query` comparables + price-index views (read) · no write tools.
**Evals (≥15):** field extraction from sample expertise reports (chassis, km, damage table); price-band sanity vs fixture comparables (band must contain median of top-5 comparables); missing-report case → brief marked "incomplete", no invented values.
**Rollout:** assist permanently (human makes the offer).
**Metrics:** intake assessment time ↓ 50%, offer variance between specialists ↓.

## 8. Insights Publisher — Marketing [Wave 1]

**Objective:** Monthly price-index report + social variants drafted automatically from warehouse data, in brand voice, published on approval.
**Agent config:** `insights_publisher` · reasoning: Claude Sonnet · utility: Gemini Flash · sensitivity: internal · semantic_cache: OFF.
**Knowledge:** `mkt-brand` (internal): brand-voice guide, past reports (style exemplars).
**Tools:** `pg_ro.query` index views (read) · `cms.publish` + `social.post` (**write:external → approval**) — INTEGRATION-POINT (mock CMS/social).
**Workflow (n8n):** cron monthly 1st 08:00 → data pull → draft → approval → publish; failure → Slack alert.
**Guardrails:** every numeric claim in the draft must match a query result attached to the approval item (grounding for numbers); TR language output.
**Evals (≥10):** numbers-match assertion vs fixture data; brand-voice rubric judge ≥ 4/5; no invented statistics test.
**Rollout:** approval-gated (public content).
**Metrics:** report production time days → hours; on-time publishing 100%.

## 9. Dealer Onboarding — Corporate Sales [Wave 2]

**Objective:** Dealer application dossier check: OCR authorization certificate + tax registration, validate fields, cross-check application, request missing items by templated email, hand clean file to sales rep.
**Agent config:** `dealer_onboarding` · **pii lane** for documents (local OCR + local extraction; tax no/IBAN) · utility cloud allowed for non-PII orchestration text · sensitivity: pii.
**Tools:** `ocr.extract` (read, local) · `crm.get_application` (read, INTEGRATION-POINT) · `email.send` (**write:external → approval** initially; supervised auto-send for missing-doc template after eval history) · `crm.update_status` (write:internal).
**Evals (≥12):** field extraction on synthetic certificates; mismatch fixture (application name ≠ certificate) → flag; email template correctness (right missing items listed, TR formal tone).
**Rollout:** approval on all outbound email first month → template auto-send.
**Metrics:** onboarding cycle time ↓, incomplete-application loops ↓.

## 10. Legal Document Review — Legal [Wave 2]

**Objective:** First-pass contract review against company playbooks: risky clauses, missing standard terms, KVKK-relevant sections — cited, advisory drafts for counsel.
**Agent config:** `legal_review` · **local lane** (contracts = confidential; local 14B for clause extraction; cloud only if Legal clears a specific model) · sensitivity: confidential · semantic_cache: OFF.
**Knowledge:** `legal-playbooks` (confidential, local embeddings): clause standards, KVKK checklist, past redlines (anonymized).
**Tools:** none (read/analyze only).
**Evals (≥12):** planted risky-clause fixtures (unlimited liability, missing KVKK annex) → must catch with citation; clean contract → no false alarms beyond threshold; output schema (clause, risk level, playbook reference) validated.
**Rollout:** assist permanently (advisory).
**Metrics:** first-pass review time ↓ 50%.

---

## Generic Onboarding Checklist (any new department, ~3–5 days)

1. **Discovery (day 1):** 2-hour workshop with the domain expert; map the process; pick ONE workflow with clear volume + pain; define a single success metric and the failure cost (this sets risk_class and rollout mode).
2. **Data (day 1–2):** create collections with `sensitivity`, `retention`, `pii_policy`; ingest 10–50 seed documents; verify PII pipeline output with the department.
3. **Tools (day 2–3):** list required actions; map to existing MCP tools; new system ⇒ new MCP server with per-tool risk_class (template in `apps/mcp/_template`). Real integration unavailable ⇒ mock behind `INTEGRATION-POINT`.
4. **Agent (day 3):** copy agent template; write `prompt.md` with the expert; pick lanes per sensitivity; **write ≥15 golden cases with the expert before enabling** — the expert defining "what good looks like" is the core Forward-Deployed act.
5. **Gate (day 4):** `make eval AGENT=x` ≥ threshold in `evals/config.yaml`; security corpus subset for any agent with tools.
6. **Pilot (day 4–5 + 2 weeks):** assist mode for ≤5 users; watch feedback score + override rate on the Agent Quality dashboard; iterate prompt (each change re-evaluated).
7. **Autonomy review:** write:internal automation only after eval history + dept_admin sign-off; write:external stays approval-gated; record the decision as an ADR.
