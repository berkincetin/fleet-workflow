# Implementation Plan · Sprint 4 — Runtime, Chat, First Agent

<!-- Derived from docs/IMPLEMENTATION_PLAN.md. The original is canonical.
     Any change here must also be applied to docs/IMPLEMENTATION_PLAN.md in the same PR. -->

## Sprint 4 — Agent Runtime, Chat, First Agent

- **4.1 Runtime core.** LangGraph base graph + Postgres checkpointer; core nodes: context builder (KB + memory w/ rolling summary), guardrails (wrap_untrusted, injection heuristics, output schema check, **structural grounding check per TRD §9**), HITL interrupt node, citation attach.
  **AC:** unit with FakeLLM: routing utility-vs-reasoning, interrupt fires on write:external tool, resume completes. *(The approval UI ships in 5.4; until then interrupt/resume is exercised at the API/fixture level — no agent has a `write:external` tool before Sprint 5, so the missing UI blocks nothing.)*
- **4.2 Agent registry + semantic cache + kill switches.** Agent registry/config API; semantic cache (opt-in) in Redis, threshold per TRD §5; **kill switches per TRD §9 — per-agent `status=paused` (instant, cached 5s) enforced in the runtime before any node runs, and a global read-only mode flag.** The Admin UI buttons for these land in 7.1; the enforcement mechanism is built here.
  **AC:** cached answer path returns with badge flag; cache invalidates on KB collection update; a paused agent stops accepting runs within 5s (unit + integration); global read-only mode blocks all `write:*` tool execution.
- **4.3 Chat UI.** SSE chat with streaming, citations, feedback buttons.
  **AC:** streamed answer renders with citations; 👍/👎 lands in Langfuse.
- **4.4 Support Copilot (agent #1, cloud lane).** Configured over seeded help-center docs; eval dataset (15 cases) + runner + CI gate wiring; Playwright E2E suite bootstrapped (login → chat → cited answer) and wired to nightly CI per TRD §13.3 — later flows (upload, approvals, admin) extend this suite in their own tasks.
  **AC:** demo path: login → chat → grounded cited answer; `make eval AGENT=support_copilot` ≥ threshold; `make e2e` green on the demo path.
- **4.5 [DEFERRABLE] Agent Builder v1.** Prompt editor + versions, model pickers, KB selection, tool allowlist, sensitivity, sandbox chat. Until built, agents are configured via seed/config API — this does not block any later task.
  **AC:** create + edit an agent end-to-end from the UI; prompt version diff visible.
