# Implementation Plan · Sprint 13 — UI Usability & Automation Builder

<!-- Derived from docs/IMPLEMENTATION_PLAN.md. The original is canonical.
     Any change here must also be applied to docs/IMPLEMENTATION_PLAN.md in the same PR. -->

## Sprint 13 — UI Usability & Automation Builder

First sprint driven by hands-on use of the finished platform rather than the backlog: the
capabilities are all built, but the web shell exposes them as eight unlabelled links, and n8n
automations can only be *run*, never *defined*, from Fleet. This sprint closes both gaps and
finally lands the System-health screen TRD §12 lists as Admin CORE (the long-deferred 7.3).

**Design decision — recipes compile to n8n, they do not replace it.** A recipe is stored in
Fleet (`automation_recipes`) as the source of truth and compiled into an n8n workflow that is
deployed over n8n's REST API. The compiler may only emit `scheduleTrigger`, `webhook`, `if`,
`set`, and `httpRequest` nodes **whose URL is Fleet's own `/v1/service/*` surface** — no free-form
URLs, no `code` nodes. That constraint is what keeps Non-Negotiable Rule 3 intact: every external
side effect still leaves through an MCP server with a declared `risk_class`, and `write:external`
steps still land in the HITL approval queue instead of executing. n8n stays the executor; the
n8n editor stays admin-only behind SSO for anything the builder deliberately cannot express.

- **13.1 Design system + app shell refresh.** Expand the 8-variable token set into a real
  light/dark system (success/warning/info/accent, surface layers, focus ring, radius/shadow
  scale — `Badge`'s `success`/`pending` variants currently reference colors that were never
  defined). Group the sidebar (Work · Automation · Knowledge · Admin) with icons and active
  state; add a top bar with page title, breadcrumb and a user/role chip. Rebuild Home from a
  flat card grid into a role-aware dashboard: pending approvals, recent automation runs, active
  agents, today's spend.
  **AC:** nav filters correctly for each of `user1`/`approver`/`builder`/`admin`; light and dark
  both legible; no color referenced that is not a defined token; all copy from i18n (TR authored
  first); Lighthouse a11y ≥ 90 on Home and Automations.
- **13.2 Explanatory layer + empty states.** A shared `PageHeader` (title + one-sentence "what
  this screen is for" + expandable "how to use it") on all eight pages; a directive empty state
  on every list (what the thing is + the first action); inline glossary for `write:external`,
  `sensitivity: pii`, `risk_class` and HITL; a "why is this waiting" line on each approval row.
  **AC:** every page has a header and an empty state; no user-facing string leaves an unexplained
  platform term; TR/EN complete with no missing-key warnings.
- **13.3 Admin → Services (closes the deferred 7.3).** New `/admin/services` over
  `GET /v1/admin/services` (MANAGE_PLATFORM): per compose service, live health probed from the
  API, its local URL, a one-sentence "what it is for", and its dev credentials — masked by
  default and revealed only on an explicit action by a `platform_admin`. Values are read from
  the environment, never committed. Also surfaces queue/worker state (arq, n8n-worker) and
  provider reachability (LiteLLM, Ollama).
  **AC:** all stack services report healthy with the stack up, and a stopped container turns its
  own card red without breaking the page; non-platform-admin roles get 403; credential values are
  **absent from the API response body** for a non-`platform_admin` caller, proven by a test.
- **13.4 Automation recipes — model, compiler, deploy API.** `automation_recipes` table
  (Alembic) + Pydantic v2 recipe schema: trigger (`schedule` cron | `manual`), an ordered step
  list, and conditional branching (`if / then / else`). Steps are drawn from a fixed action
  allowlist, each backed by a `/v1/service/*` endpoint: `pg.query` (read-only), `agent.run`,
  `slack.post`, `email.send`, `http.notify`. Compiler renders the recipe to n8n workflow JSON
  (`if` → `n8n-nodes-base.if`) and deploys it via n8n's REST API, storing the returned workflow
  id on the recipe. CRUD is MANAGE_AGENTS.
  **AC:** a schedule-triggered recipe defined through the API exists and fires in n8n; a recipe
  containing `email.send` produces an approval-queue entry instead of sending; a recipe whose
  branches both write is still gated; a crafted recipe attempting a non-Fleet URL or an unlisted
  action is rejected by the compiler (security test).
- **13.5 Builder UI + reworked Automations page.** Form-driven wizard: pick a trigger → add steps
  (fields generated from each action's schema) → add a condition → preview the compiled flow in
  plain language → save and activate. The Automations page merges the static catalog with
  user-defined recipes; each card carries run history, last status, and edit/delete.
  **AC:** a `builder` defines, saves and runs an automation end to end from the browser and sees
  the run in n8n and Langfuse; with n8n stopped the page still renders its down-state; a
  `member` can view but not edit.
- **13.6 Tests, e2e, docs, sprint close.** Unit tests for the recipe schema, compiler and RBAC;
  a testcontainers integration test covering recipe → n8n deploy → trigger; a Playwright e2e for
  the builder flow; a compiler security test against URL/action injection. TRD §12 updated in
  both layers for the Services screen and the builder.
  **AC:** `make lint && make test` green; e2e green against the compose stack; docs updated in
  original and split part together.
