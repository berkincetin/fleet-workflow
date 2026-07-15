# Project Overview · Tech Coverage, Rollout, Metrics

<!-- Derived from docs/PROJECT_OVERVIEW.md. The original is canonical.
     Any change here must also be applied to docs/PROJECT_OVERVIEW.md in the same PR. -->

## 5. Technology Coverage Map

| Required by role | Where it lives in Fleet |
|---|---|
| Python | Agent runtime, MCP servers, RAG pipeline (FastAPI) |
| TypeScript | Web UI (Next.js), workflow custom nodes |
| SQL | App DB, analytics agent, finance reconciliation |
| APIs | FastAPI backend + internal API integrations |
| LLMs | Agent runtime (provider-agnostic gateway) |
| Prompt engineering | Versioned prompt library per agent |
| Tool calling | MCP tool invocation layer |
| RAG | Knowledge Base module |
| Agentic frameworks | LangGraph-based orchestration in Agent Hub |
| MCP | Entire Integration Layer |
| Vector databases | Qdrant (Knowledge Base) |
| n8n | Workflow Studio |
| OCR | Invoice, CV, expertise report, dealer document pipelines |
| Multimodal | Listing Quality + Vehicle Intake agents |

## 6. Rollout Strategy

**Phase 0 — Discovery (Weeks 1–3):** Structured interviews with each department; map processes; score opportunities by (impact × feasibility × risk). Re-prioritize this document with real data.

**Phase 1 — Foundation + First Win (Weeks 4–8):** Deploy platform core (Agent Hub, Knowledge Base, MCP layer, Control Plane). Ship ONE high-visibility, low-risk agent end-to-end (recommended: Support Copilot in assist mode or Self-Service Analytics).

**Phase 2 — Expansion (Months 3–6):** Onboard 3–4 more departments using the now-proven platform. Introduce n8n workflows and the approval queue. Start internal enablement sessions ("build your own agent").

**Phase 3 — Scale (Months 6–12):** Remaining departments, deeper autonomy where evaluation data supports it, reusable component library, adoption metrics reported to leadership.

## 7. Success Metrics (Platform-Level)

- Hours of manual work automated per month (per department and total)
- Number of active agents / workflows / weekly active internal users
- Human-approval override rate (quality proxy — should trend down)
- Evaluation pass rate per agent release
- Time from "department request" to "working agent" (target: days, not months)

## 8. Why This Approach Wins

- **One engineer, organizational reach:** platform reuse means every department after the first costs less to onboard.
- **Trust by design:** guardrails, approvals, and evaluation are platform features, not afterthoughts — this is what makes AI adoption *sustainable and responsible*, matching the company's stated goal.
- **AI-first workflow:** the platform itself is developed with AI coding assistants (see CLAUDE.md), demonstrating the mindset the role asks to spread.
