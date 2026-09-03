# Production / Release Checklist

Things that are intentionally deferred during local development and **must** be done
before the platform is moved to the `test` / `demo` / `prod` server environments
(TRD §14). This is an operational record, not a sprint backlog — it is separate from
`docs/IMPLEMENTATION_PLAN.md` and is not mirrored under `docs/split/`.

Each item: what, why it was deferred, and how to do it when the time comes.

## Must do before production

### 1. Enable branch protection on `main` (GitHub side of task 1.0) — REQUIRED
- **What:** Protect the `main` branch so (a) no direct pushes are allowed — all changes land via PR, and (b) a PR can only merge after the required GitHub Actions checks are green (`lint`, `unit`, `integration`, `security`, `build-image`).
- **Why deferred:** GitHub branch protection on a **private** repo requires a paid **GitHub Pro** plan (or the repo being public). During local development the repo is private on the free plan, so the API returns `403 "Upgrade to GitHub Pro or make this repository public"`. The team has followed the feature-branch → PR → CI-green → merge flow by discipline throughout Sprints 1–…, but it is **not yet enforced by a rule**.
- **How, when eligible (Pro acquired, or repo made public):**
  ```bash
  gh api -X PUT repos/berkincetin/fleet-workflow/branches/main/protection \
    -H "Accept: application/vnd.github+json" \
    -f "required_status_checks[strict]=true" \
    -f "required_status_checks[checks][][context]=lint" \
    -f "required_status_checks[checks][][context]=unit" \
    -f "required_status_checks[checks][][context]=integration" \
    -f "required_status_checks[checks][][context]=security" \
    -f "required_status_checks[checks][][context]=build-image" \
    -F "enforce_admins=true" \
    -F "required_pull_request_reviews=null" \
    -F "restrictions=null"
  ```
  (Or via the GitHub UI: Settings → Branches → Add branch ruleset → require a PR + require the five status checks to pass + block direct pushes.) After enabling, verify a direct `git push origin main` is rejected and that a PR with a red check cannot be merged.
- **Priority:** REQUIRED before `prod`. This is the enforcement point for "no commit ships without passing CI" (CLAUDE.md § Commit & Branch Convention). Until then, CI is a gate only by convention.

### 2. Re-scope Admin → Services before it leaves dev (task 13.3) — REQUIRED
- **What:** `/v1/admin/services` (`apps/api/fleet_api/services_catalog.py`) enumerates the *local compose stack* — its `localhost` URLs and its dev credentials — and `POST /v1/admin/services/{name}/reveal` returns those credentials in plaintext to a `platform_admin`. Before a server environment: (a) point the catalog at that environment's real endpoints (or drive it from the Helm values, not a hard-coded list), and (b) decide whether the reveal endpoint ships at all.
- **Why deferred:** the screen exists to make a *local* stack legible — "is Postgres up, what is the MinIO console password" is a question a developer asks on their own machine and nobody asks in prod, where those values live in a secret manager. The credentials it surfaces today are the compose defaults already documented in this repo (`fleet_dev_pw`, `admin`/`admin`), so nothing secret is exposed by it in dev.
- **How:** the safe default for a server environment is to **drop the reveal endpoint entirely** (delete `reveal_credentials` and the `credentials` field from `ServiceOut`) and keep only the health board, which is the part that stays useful. If a reveal is genuinely wanted, it must read from the secret manager rather than the process environment, be re-authenticated (step-up auth), and emit an explicit audit event per reveal rather than relying on `AuditMiddleware`'s generic request record.
- **Priority:** REQUIRED before `demo`/`prod`. A dev-only screen that prints credentials is exactly the thing that gets forgotten in a deploy.

### 3. Review the automation-builder action allowlist per environment (task 13.4) — RECOMMENDED
- **What:** the recipe compiler (`apps/api/fleet_api/recipes/compiler.py`) may emit only five n8n node types and only `httpRequest`s aimed at Fleet's own `/v1/service/*` surface, chosen from `SERVICE_PATHS` by action name. Before production, confirm the action allowlist is still the set you want any `builder`-role user to be able to schedule unattended, and that each backing endpoint's own guards (SQL allowlist, Slack channel allowlist, email domain allowlist) match the environment.
- **Why deferred:** in dev the backing tools are sandboxed — Slack posts go to an allowlisted channel, email goes to Mailpit, `pg.query` is confined to fixture views. In production those become real destinations.
- **How:** narrow `SERVICE_PATHS`/`ActionName` to the actions the environment should allow, tighten `_ALLOWED_EMAIL_DOMAINS` and `_ALLOWLISTED_CHANNELS` in `routers/service.py`, and keep `tests/security/test_recipe_compiler_injection.py` green — it is the regression test for "a crafted recipe cannot reach anything else".
- **Priority:** RECOMMENDED before `demo`, REQUIRED before `prod`.
