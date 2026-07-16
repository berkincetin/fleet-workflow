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
