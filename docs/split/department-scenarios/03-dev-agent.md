# Department Scenarios · Dev Agent — IT/Engineering [Wave 0]

<!-- Derived from docs/DEPARTMENT_SCENARIOS.md. The original is canonical.
     Any change here must also be applied to docs/DEPARTMENT_SCENARIOS.md in the same PR. -->

## 3. Dev Agent — IT / Engineering [Wave 0]

**Objective:** Take labeled small Jira tickets end-to-end to a reviewed PR: plan → branch → implementation draft → PR → Slack notify.
**Agent config:** `dev_agent` · reasoning: Claude Sonnet · utility: Gemini Flash (ticket classification, commit msg) · sensitivity: internal · semantic_cache: OFF · max_context: 24k (code).
**Knowledge:** `it-eng-docs` (internal): contribution guide, architecture notes of target repos.
**Tools:** `jira.search/get_issue` (read) · `github.read_repo` (read) · `github.create_branch` (write:internal, pattern `agent/*` enforced) · `github.open_pr` (**write:external → approval queue, always**) · `slack.post` (write:internal, allowlisted channels).
**Guardrails:** protected-paths blocklist (infra/, migrations/, .github/); never merge; diff size cap (> 400 lines → split or escalate); tickets only with label `agent-ok`.
**Evals (≥15):** fixture tickets → rubric-judged plan quality; correct file targeting on fixture repo; refusal when ticket touches protected path; branch-name compliance.
**Rollout:** permanently approval-gated on PR creation (external write). Autonomy never exceeds "supervised".
**Metrics:** small-ticket lead time ↓, PR acceptance rate ≥ 70% without major rework.
