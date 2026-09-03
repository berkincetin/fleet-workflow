# Sprint 13 — UI Usability & Automation Builder

**Branch:** `feat/sprint-13-ui-automation-builder` · **Closed:** 2026-09-03
**Scope:** 13.1–13.7, all non-deferrable. Also closes the long-deferred **7.3** (System health).
**Reopened 2026-09-03** to add **13.7** — a colour pass and the in-app examples — after using the shipped shell; 13.7 also resolves the one open item this report closed with.

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
| **13.7** Colour pass + in-app examples | Palette rebuilt on indigo-tinted neutrals with a per-section accent (Work indigo · Automation violet · Knowledge teal · Admin amber) derived from the nav and applied via `data-section`; gradient headers and accent rails; a **Guide** screen of four walkthroughs; four **ready-made automation templates** seeding the builder; per-agent **chat starters**; the `support_copilot` seed drift repaired | ✅ **all five.** WCAG AA holds on 8 screens in both themes measured against the *rendered* DOM (audit mutation-tested to prove it fails when it should); no untokenised colour remains; every template deploys to n8n unedited and is fenced by the server's own allowlists (also mutation-tested); TR/EN parity exact; **`chat-demo-path` passes again** |

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

> **Resolved in 13.7 (2026-09-03).** The `chat-demo-path` failure below is fixed: the
> `support_copilot` insert in `seed.py` now re-asserts `sensitivity` on conflict
> (`ON CONFLICT … DO UPDATE SET sensitivity`), so `make seed` repairs the drift instead of
> skipping the row. Verified live — the row read `pii` before the seed and `internal` after,
> and the e2e went green. **The second point below still stands**: `evals/runner.py` hard-codes
> `sensitivity="internal"` for the RAG path, so the eval still cannot catch this class of bug.
> The original diagnosis is kept verbatim for the record.

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

> **Update (2026-09-03, after the sprint close).** Two of the items below are now fixed,
> outside Sprint 13 task scope:
> - **The eval/live-path sensitivity gap is closed.** `evals/runner.py` now reads the agent's
>   real `sensitivity` from the DB in both agent-derived RAG paths (`run_agent_eval` and the
>   HR `qa_grounding` branch) instead of hard-coding `"internal"`. Mutation-tested: with the
>   row set back to `pii` the eval fails on `local-embeddings` exactly as live chat did, where
>   it previously still scored 100%.
> - **The `live-chat-agent-*` leak is fixed.** `test_chat_live.py` unwinds the FK chain in a
>   `finally`; a run now ends with 0 such agents and 0 orphaned conversations/messages/feedback,
>   including when the test fails mid-way.
>
> `make api` also gained `--host 0.0.0.0`. Note that the IPv6/`::1` explanation recorded for
> that e2e failure **did not reproduce** when measured afterwards — Node's `fetch` reaches the
> default `127.0.0.1` bind fine — so the flag is kept for reachability, not for that mechanism.
> Still open: no live `slack.post` verification (`FLEET_SLACK_WEBHOOK_URL` empty), superpowers
> not installed, and `make eval AGENT=hr_agent` needing `PROFILE=ollama`.

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

## 4b. Task 13.7 — colour pass and in-app examples

Added after the sprint's first close, driven by using the finished shell rather than by the
backlog. Two gaps: the token system was correct but nearly monochrome (zinc plus one blue,
colour reaching the screen only through badges), and while every screen explained *itself*,
nothing explained how the screens fit *together*.

**The colour work.** The palette is now indigo-tinted throughout — light on `#f6f7fc`, dark on
a `#0b1020` navy rather than near-black — with four section accents (Work indigo, Automation
violet, Knowledge teal, Admin amber). The accents are *derived*, not maintained by hand:
`sectionFor(pathname)` maps any route to the sidebar group that owns it, `AppShell` stamps
`data-section`, and CSS rebinds `--section*` beneath it. A screen therefore cannot be amber in
the sidebar and teal in its own header. Colour is never load-bearing: every accent sits beside
a label or icon that already carries the meaning, and amber-as-Admin is kept apart from
amber-as-warning by role — section amber only ever appears as a rail or an icon, never as a
badge fill.

**How the contrast AC was proven.** Lighthouse is not installed on this machine, so the colour
half of the a11y AC is checked directly instead: `tests/e2e/specs/contrast.spec.ts` walks the
rendered DOM of 8 screens in pinned light and pinned dark, resolves each text node's real
painted background (flattening translucency up the ancestor chain) and applies the WCAG AA
split of 4.5:1, or 3:1 for large text. Zero failures. **The audit itself was mutation-tested** —
lightening `--muted-foreground` to `#b8bfd0`, rebuilding and re-running made it report 1.8:1
across every screen — so a green run means something. One real defect was caught this way
before shipping: the first draft's dark-mode `--primary` (`#6366f1`) gave white button labels
4.47:1, just under AA; `#585ae8` clears it at 5.19:1.

**The examples.** A `/guide` screen at the top of Work carries four walkthroughs — ask an
agent, add knowledge, build an automation, see the approval gate — each with numbered steps, a
time estimate and a button into the screen it describes. The builder now opens on four
ready-made templates that seed the form (through the existing `fromRecipe` path, so a template
cannot produce a draft the editor fails to round-trip), and Chat offers per-agent starter
questions on an empty thread.

The templates are the part that could most easily have been decorative, so they are fenced
twice. `tests/unit/test_recipe_templates.py` reads `_ALLOWLISTED_TABLES`,
`_ALLOWLISTED_CHANNELS` and `_ALLOWED_EMAIL_DOMAINS` **out of `routers/service.py` itself** and
checks every template against them, plus read-only SQL, slug validity, seeded agent names, and
`needsApproval` tracking the actual `write:external` action rather than a hand-kept flag — so a
change to the server's allowlists breaks the templates loudly. Mutation-tested: pointing a
template at `users`, `#random` and `evil.com` failed exactly the three relevant cases. The live
half is an e2e that picks the digest template, previews it through the *server's* compiler and
saves it — the workflow appears in n8n unedited, then is deleted again. One template
(`monthlyReport`) deliberately contains `email.send`, so the approval gate is demonstrated
rather than described.

**Gate.** ruff clean · mypy `apps` 18 (documented baseline, 0 new) · eslint + `tsc --noEmit`
clean · `next build` clean (21 routes) · unit **578** (was 560) · security **85** ·
integration **78 passed / 8 skipped** (the same 8 testcontainers contention failures as the
Sprint 12 and 13 closes: all 8 pass on re-run in groups, none an assertion) · e2e **13 passed**,
up from 7 passed / 1 failed.

**One environmental finding worth carrying.** The builder e2e failed mid-run with a Next.js
server-side exception on `/automations`. Not a regression: the API had been started as plain
`uvicorn … --port 8000`, which binds `127.0.0.1` only, and restarting it with `--host 0.0.0.0`
fixed it. **`make api` also omits `--host`**, so the same failure was reproducible there — since
addressed (see the §4 update).

> **Correction (2026-09-03).** The mechanism first recorded here — that Node 18+ resolves
> `localhost` to `::1` and so gets `ECONNREFUSED` against a `127.0.0.1`-only bind — **did not
> reproduce when it was actually measured.** `0.0.0.0` is IPv4-only (nothing answers on
> `[::1]`), and Node's `fetch('http://localhost:…')` succeeded against the *default* bind too,
> because undici tries every resolved address and falls back to IPv4. So the `ECONNREFUSED`
> had some other trigger, and the IPv6 story should not be carried forward as the cause.
> `--host 0.0.0.0` is kept for reachability (containers, other hosts on the LAN), not for that
> mechanism.

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

Added for 13.7, both layers again:

- `docs/TECHNICAL_REQUIREMENTS.md` + `docs/split/technical-requirements/12-screens.md` — the
  section-accent palette and the rule that colour is never the sole carrier of meaning; the
  Guide screen, chat starters and the builder's template gallery; and the note that template
  values sit inside the compiler's own server-side allowlists.
- `docs/IMPLEMENTATION_PLAN.md` + `docs/split/implementation-plan/sprint-13-ui-automation-builder.md`
  — task **13.7** with its AC.

---

## 7. Knowledge graph refreshed

`/graphify . --update` after 13.7, per the Definition of Done.

- **50 changed files re-extracted** (20 code, 30 docs). AST gave 142 nodes / 367 edges; two
  parallel semantic subagents produced 195 nodes / 246 edges / 6 hyperedges over the changed
  docs and the Turkish legal/HR eval fixtures. ~233k input / ~26k output tokens.
- **Merged into the existing graph rather than replacing it**: 141 nodes were replaced in
  place for the re-extracted sources and 9 exact duplicates collapsed, leaving
  **4,939 nodes / 9,003 edges / 401 communities**. No import cycles.
- **Community labelling was scripted, not hand-written.** At 401 communities hand-naming is
  not honest work, so labels are derived from each community's dominant module path against a
  table of known Fleet subsystems. One defect was worth fixing: Louvain places a module and
  its tests in the same community, and the tests frequently outnumber the module, so ranking
  by raw count named the largest communities "Unit Tests". Test/fixture prefixes are now only
  used when nothing else is present, which is why community 0 reads *n8n REST Client* rather
  than the tests that exercise it.
- `compile_recipe()` now ranks among the graph's god nodes (29 edges), alongside `CurrentUser`,
  `KillSwitch`, `LLMClient` and `N8nClient` — the recipe compiler has become a core abstraction
  rather than a leaf, which matches what Sprint 13 actually built.
- Two nodes carry an extraction warning (`missing required field 'source_file'`, e.g.
  `concept_sensitivity_routing`). Pre-existing, harmless to traversal, noted rather than hidden.
