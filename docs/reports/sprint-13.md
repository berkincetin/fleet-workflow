# Sprint 13 — UI Usability & Automation Builder

**Branch:** `feat/sprint-13-ui-automation-builder` · **Closed:** 2026-09-03
**Scope:** 13.1–13.6, all non-deferrable. Also closes the long-deferred **7.3** (System health).

The first sprint driven by hands-on use of the finished platform rather than the backlog.
Every capability already existed; the web shell exposed them as eight unlabelled links, and
n8n automations could only be *run* from Fleet, never *defined*. This sprint closes both.

---

## 1. Tasks and acceptance criteria

| Task | Built | AC result |
|---|---|---|
| **13.1** Design system + app shell | Full light/dark token system (surfaces, semantic triples, accent, link, radius/shadow); system/light/dark switch persisted in a cookie so the *server* render carries it; grouped role-filtered sidebar (Work · Automation · Knowledge · Admin) + top bar with breadcrumb and role chip; Home rebuilt as a role-aware dashboard | ✅ **all four.** Nav filtering proven per role by 4 Playwright cases; theme switch proven across a reload; no bare Tailwind palette class or `dark:` variant remains; **Lighthouse a11y 100 on Home and 100 on Automations**, in dark *and* explicit light |
| **13.2** Explanatory layer + empty states | `PageHeader` (title + purpose + expandable how-to) on all 9 screens; directive `EmptyState` on 12 lists incl. the 6 admin tables that previously rendered an empty `<table>`; inline + block glossary for `write:external`, `sensitivity: pii`, `risk_class`, HITL; "why is this waiting" on every approval row | ✅ **all three.** TR/EN parity and key resolution are now enforced by `tests/unit/test_i18n_messages.py` (5 cases over 316 referenced keys), not by inspection |
| **13.3** Admin → Services (closes 7.3) | `services_catalog.py` (17 services, probe kind, env-var *names* only) + `GET /v1/admin/services` probing concurrently at request time + a separate `platform_admin`-only reveal; grouped board UI; n8n-worker health surface; **promtail** added so Loki finally has an input | ✅ **all four.** `healthy=16, down=0`; `docker stop mailpit` → 200 with one red card and all 17 still rendered; 403 for member/builder/approver/dept_admin; no plaintext secret in any list response, proven by test — including for a synthetic role holding MANAGE_PLATFORM without the `platform_admin` role |
| **13.4** Recipe model, compiler, deploy API | `automation_recipes` (migration 0011) + Pydantic v2 recipe schema with a 5-action allowlist and one level of `if/then/else`; compiler → n8n workflow JSON; `/v1/recipes` CRUD + preview + activate/run; three new `/v1/service/*` action endpoints; an `automation_recipe` approval resumer | ✅ **all four**, live against real n8n: a schedule recipe deploys, activates, fires, and calls back into Fleet; `email.send` queues an approval and Mailpit stays empty until it is approved; both-branch-writes still gated; 18 injection cases + a live 422 that leaves no workflow behind |
| **13.5** Builder UI + reworked Automations page | Four-section wizard with server-rendered plain-language preview; Automations page split into built-in catalog + user recipes with run/activate/edit/delete | ✅ **all three.** A `builder` defines → saves → activates → runs → sees the n8n execution, entirely from the browser (Playwright); a `member` gets no entry point *and* is refused the route; the n8n-down state renders |
| **13.6** Tests, e2e, docs | 51 new unit/security cases, 6 live integration cases, 7 e2e cases; TRD §11 + §12 updated in both layers; 3 new production-checklist items | ✅ lint/unit/security green, e2e green except one pre-existing failure (below), docs updated original + split together |

---

## 2. What was tested, and how

**Static gate**

```
uv run ruff check .            → All checks passed
uv run mypy apps               → 18 errors (the documented pre-existing baseline, 0 new)
pnpm -r --if-present lint      → clean
pnpm --filter web exec tsc --noEmit → clean
```

**Python suites**

```
uv run pytest tests/unit      -q  → 560 passed   (was 510)
uv run pytest tests/security  -q  → 85 passed    (was 67)
uv run pytest tests/integration -q → 70 passed / 8 failed / 8 skipped
                                     …all 8 pass on a quiet re-run, no code change
```

The 8 integration failures were `test_rag_ingest_live`, `test_rag_query_live`,
`test_rag_pii_collection_live`, `test_vehicle_intake_e2e_live` (×2),
`test_insights_publisher_e2e_live`, `test_pii_logging_masked_live` and
`test_services_admin_live` — every one a testcontainers connect/timeout while the full suite
ran alongside the compose stack, none an assertion. Re-run in three groups: **78 passed**.
This is the same contention recorded at the Sprint 12 close.

**Evals**

`make eval AGENT=support_copilot` → **100%** (15/15, threshold 0.90). No agent changed this
sprint, so this is a regression check only — and see §4 for why it passing is itself a finding.

**End-to-end (Playwright, production build against the live stack)**

```
shell-roles.spec.ts        5 passed   (role nav ×4, theme switch)
automation-builder.spec.ts 2 passed   (builder end-to-end, member refused)
chat-demo-path.spec.ts     1 failed   (pre-existing — §4)
```

**Accessibility (Lighthouse, authenticated)**

An unauthenticated Lighthouse run would only score the sign-in prompt, so the session cookie
was captured with Playwright and passed through `--extra-headers`:

| Screen | dark | explicit light |
|---|---|---|
| Home | **100** | **100** |
| Automations | **100** | **100** |
| Admin → Services | 100 | 100 |
| Approvals | 100 | 100 |
| Knowledge · Chat · Scenarios · Examples · Builder | 100 | — |
| Admin → Agents | 100 (one 0-weight `td-has-header`) | — |
| Admin → Cost | 99 (`svg-img-alt`, Sprint 7 sparkline) | — |

**Live AC probes** (Fleet API + n8n + Postgres + Mailpit, no mocks)

```
GET  /v1/admin/services                 → healthy=16 down=0
docker stop mailpit; GET again          → 200, down=1, mailpit ConnectError, 17 cards
GET  /v1/admin/services (builder)       → 403, no credential in body
POST /v1/admin/services/keycloak/reveal → 403 builder · 200 platform_admin
POST /v1/service/email-send             → queued_for_approval, Mailpit 0 messages
POST /v1/approvals/{id}/decide approve  → Mailpit 1 message (ops@fleet.local)
recipe create→activate→run              → n8n execution success; Fleet logged the pg-query
```

---

## 3. Issues hit and how they were resolved

Full symptom → root cause → resolution detail is in `docs/PROGRESS.md`. The ones worth
carrying forward:

1. **Loki has never had a log source.** Its `/ready` was permanently 503 ("Ingester not
   ready") on a healthy stack — not a probe bug: Loki has been in the compose stack since
   Sprint 1 with nothing pushing to it, so TRD §6's log lane was hollow and the Services
   screen was simply the first thing to ask. Fixed at the source: a **promtail** service
   discovering containers over the Docker API (a `/var/lib/docker/containers` bind mount
   silently scrapes nothing on Docker Desktop) plus a DaemonSet in the Helm chart. Loki went
   ready in 4s and now holds real log lines labelled by container/service.
2. **A compiled recipe deployed, activated — and never ran.** Two of my own defects stacked:
   n8n registers a production webhook by the node's `webhookId`, not by `path` (a node
   deployed over the REST API without one activates and then 404s its own URL); and
   `POST /run` reported success over that 404 because `N8nResult.reachable` only means "n8n
   answered". Both fixed, both regression-tested. *The same reachable-but-failed shape exists
   in the Sprint 6.5 `run_weekly_summary` and was left alone as out of scope.*
3. **Every condition took its false branch.** The compiler had copied
   `responseFormat: "text"` from the weekly-summary export, which hides the response body
   inside `json.data` as a string, so `{{steps.q1.row_count}}` resolved to undefined. `text`
   now applies only to `slack.post` — the one endpoint that answers 204 with no body, which
   is why the export needed it.
4. **next-intl silently rendered raw key paths.** It resolves a key by splitting on `.`, and
   every action id contains one, so `"pg.query"` stored as a literal JSON key was
   unreachable. Nested the block, and added a structural test that walks the nesting the way
   next-intl does — proven to fail against the old flat shape.
5. **`--primary` is a background token.** Used as link text it scored 3.58:1 in dark mode.
   Added a separate `--link` token that is contrast-checked as text.
6. **n8n 1.71's executions list carries no `status`.** Passing the missing field through
   painted every finished automation run red on the Home dashboard; success/failure is now
   derived from `finished`/`stoppedAt`, matching what n8n's own `?status=` filter concludes.

---

## 4. Open items

**`chat-demo-path` e2e fails — pre-existing, needs a decision.**
`support_copilot`'s row carries `sensitivity = 'pii'` while `seed.py` declares `'internal'`
(and `ON CONFLICT DO NOTHING` means `make seed` will not repair it). The chat router passes
the *agent's* sensitivity into the RAG query, which admits only `local-embeddings` (bge-m3,
1024 dims), while `cs-help-center`/`cs-procedures` were ingested with the cloud model (1536)
at the Sprint 12 close — so Qdrant refuses the query vector. The drift predates the audit
log's window; it is most likely a leftover of the Sprint 8 local-lane rehearsal. Nothing in
Sprint 13 touches this path.

Two things follow from it:

- The fix is a one-field change to dev data (`UPDATE agents SET sensitivity='internal' WHERE
  name='support_copilot'`, or a click in Admin → Agents). Left for the user.
- **The eval did not catch it because `evals/runner.py` hard-codes `sensitivity="internal"`
  for the RAG path.** `support_copilot` scores 100% while live chat is broken. That gap
  between the eval harness and the real call path is worth its own fix.

**Also noted, not acted on**

- 7 leftover `live-chat-agent-*` rows from integration runs inflate the Home dashboard's
  "active agents" count. Environment noise; wants a teardown in the chat live test.
- `FLEET_SLACK_WEBHOOK_URL` is still empty, so the built-in weekly-summary workflow's final
  Slack node still fails (the standing issue from the previous session). The user chose to
  skip `slack.post` verification for this sprint; the action ships with unit coverage and its
  compiler output is pinned, but no end-to-end Slack post was made.
- The **superpowers** plugin is enabled in `.claude/settings.json` but is not installed on
  this machine, so its skills were unavailable; the Task Execution Protocol was followed
  directly.

---

## 5. Deviations from the plan

- **Branching is one level and not nestable.** The plan asked for `if / then / else`; a
  builder that can nest arbitrarily is a programming language, and every safety rule in the
  compiler would then have to hold recursively. One level covers "post only when the query
  returned something", which is what the feature is for.
- **Every recipe gets a webhook node**, even a scheduled one, so "Run now" works without
  waiting for the cron — the same shape the hand-written weekly-summary export uses.
- **`http.notify` writes an audit-log entry** rather than calling out. It is deliberately the
  one action with no outward effect: what a builder reaches for when the automation should
  leave a trace rather than message a person.
- **promtail was added** (compose + Helm). Not in the plan, but 13.3's AC could not be met
  honestly without it — see §3.1.
- **Two pre-existing a11y label defects** on Knowledge and Chat were fixed even though the AC
  names only Home and Automations, since the sprint is overhauling those screens anyway.

---

## 6. Docs updated

Both layers, in the same change:

- `docs/TECHNICAL_REQUIREMENTS.md` + `docs/split/technical-requirements/12-screens.md` —
  a new "Shell & explanatory layer" paragraph, the Automation Builder under Builder screens
  (including why the compiler's constraints keep Non-Negotiable Rule 3 intact), and
  Services/system health under Admin CORE marked as closing the deferred 7.3.
- `docs/TECHNICAL_REQUIREMENTS.md` + `docs/split/technical-requirements/11-data-model.md` —
  `automation_recipes`.
- `docs/PRODUCTION_CHECKLIST.md` — two new REQUIRED/RECOMMENDED items: re-scope (or drop)
  Admin → Services before it leaves dev, and review the recipe action allowlist per
  environment.
