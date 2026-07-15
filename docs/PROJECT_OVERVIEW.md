# Fleet — AI Operations Platform

**Internal AI Super App | Agentic Transformation Demo Proposal**

> Prepared as a demo concept for the Forward Deployed AI Engineer role.
> Department map below is an outside-in hypothesis based on public information;
> it will be validated and re-prioritized through structured discovery sessions in the first weeks.

---

## 1. Vision

The company employs ~600 white-collar professionals across business, operations, and technology teams. A significant share of their daily work consists of repetitive, rule-based, document-heavy, or communication-heavy tasks.

**Fleet** is a single internal platform where any department can:

1. **Chat with AI agents** that know company data and can take real actions,
2. **Run automated workflows** that connect existing tools (Jira, GitHub, Slack, email, internal APIs),
3. **Upload documents** into a shared, permission-aware knowledge base,
4. **Build new agents and connect new APIs** without waiting for a full engineering cycle.

One platform, many agents — instead of many disconnected point solutions. Every new integration, prompt, and guardrail built for one department becomes reusable for all others. This is how a single Forward Deployed AI Engineer scales across an entire organization.

## 2. Problem Statement

| Observation | Consequence |
|---|---|
| Manual, repetitive workflows in every department (ticket triage, invoice entry, CV screening, listing moderation, report writing) | Skilled people spend hours on low-leverage work |
| Knowledge trapped in PDFs, emails, and people's heads | Slow onboarding, inconsistent answers, repeated questions |
| Integrations require engineering tickets | Business teams wait weeks for simple automations |
| AI experiments happen in isolation | No shared guardrails, no evaluation, no reuse |

## 3. Solution: The Fleet Platform

Fleet is composed of five core modules:

### 3.1 Agent Hub
A registry of specialized AI agents. Each agent = system prompt + selected tools (via MCP) + selected knowledge collections + guardrail policy. New agents are created through a builder UI — no code required for standard patterns.

### 3.2 Workflow Studio (n8n)
Embedded n8n instance for scheduled and event-driven automations (e.g., "every Monday 09:00, generate the weekly listings quality report and post it to Slack"). Workflows can call Fleet agents as steps, and agents can trigger workflows as tools.

### 3.3 Knowledge Base (RAG)
Drag-and-drop document ingestion (PDF, DOCX, images with OCR) → chunking → embeddings → vector database. Collections are permission-scoped per department. Every agent answer cites its sources.

### 3.4 Integration Layer (MCP)
All external and internal systems are exposed to agents as **MCP tools**: Jira, GitHub, Slack, Gmail/SMTP, and internal APIs. Adding a new REST API = registering it on the MCP server with a description; the LLM discovers and calls it via tool calling. No per-integration glue code in the agent layer.

### 3.5 Control Plane
- **Guardrails:** input filtering, output validation, tool permission scoping (read-only vs. write), rate limits
- **Human-in-the-loop:** approval queue for irreversible or high-risk actions (sending external emails, writing to production systems, financial records)
- **Evaluation:** golden test sets per agent, automatic regression runs on prompt changes, response quality dashboards
- **Audit:** every agent action logged with full trace (who, what, which tool, which data)

## 4. Department Use Cases

Each use case below is one agent (or agent + workflow) running on the same platform.

### 4.1 Customer Service — Support Copilot
- **Pain:** High ticket volume; agents repeatedly answer the same questions about listings, memberships, payments, Trink sat process.
- **Solution:** RAG agent grounded in help-center content and internal procedure docs. Drafts replies for human agents (assist mode), auto-resolves whitelisted simple intents, triages and routes tickets by topic/urgency.
- **Tech:** RAG, vector DB, prompt engineering, guardrails, human-in-the-loop.
- **Metric:** First-response time ↓, tickets resolved per agent ↑, deflection rate on FAQ intents.

### 4.2 Listings Operations — Listing Quality Agent
- **Pain:** Manual review of listings: photo quality, photo-description consistency, prohibited content, suspicious pricing.
- **Solution:** Multimodal agent that checks each new listing — do photos match the declared model/color/condition? Are plates blurred? Is the description consistent with images? Flags anomalies with reasons to a human review queue.
- **Tech:** Multimodal VLM, tool calling (internal listing API), n8n event trigger on new listings.
- **Metric:** Moderation throughput ↑, fake/low-quality listing rate ↓, review backlog ↓.

### 4.3 Trink sat! — Vehicle Intake Agent
- **Pain:** Vehicle acquisition specialists manually review seller photos, expertise reports, and market data before making offers.
- **Solution:** Agent performs pre-assessment: extracts structured data from expertise report PDFs (OCR), analyzes vehicle photos for visible damage (multimodal), pulls comparable listings and price index data (SQL/API), and produces a structured intake brief with a suggested price band. Specialist makes the final call.
- **Tech:** OCR, multimodal, RAG over historical purchases, SQL, human-in-the-loop.
- **Metric:** Intake assessment time ↓, offer consistency ↑.

### 4.4 Human Resources — Talent & Onboarding Agent
- **Pain:** CV screening across hundreds of applications; new-hire questions consume HR time.
- **Solution:** (a) CV pipeline: OCR/parse incoming CVs → structured profile → match score against role requirements → shortlist with reasoning. (b) Onboarding Q&A agent grounded in HR policies (leave, benefits, procedures).
- **Tech:** OCR, RAG, prompt engineering, SQL (candidate store).
- **Metric:** Screening time per role ↓, HR ticket volume ↓.

### 4.5 Finance — Invoice & Reconciliation Agent
- **Pain:** Manual invoice entry and month-end reconciliation support across departments.
- **Solution:** OCR extracts invoice fields → agent validates against purchase records (SQL) → prepares accounting entries as **drafts** → human approves in the approval queue. Flags mismatches with explanations.
- **Tech:** OCR, tool calling, SQL, strict human-in-the-loop (no autonomous writes to financial systems).
- **Metric:** Invoice processing time ↓, entry error rate ↓.

### 4.6 Marketing & Content — Insights Publisher
- **Pain:** Recurring content (monthly price index reports, market analyses, social posts) is assembled manually from data science outputs.
- **Solution:** Scheduled n8n workflow queries the data warehouse (SQL), agent drafts the monthly market report and social variants in brand voice, routes to marketing for approval, publishes on approval.
- **Tech:** n8n, SQL, LLM, prompt engineering (brand-voice prompt library), human-in-the-loop.
- **Metric:** Report production time from days to hours; publishing cadence consistency.

### 4.7 Corporate Sales — Dealer Onboarding Agent
- **Pain:** Corporate/dealer membership applications require document checks (authorization certificates, tax registration) and back-and-forth.
- **Solution:** Agent OCRs submitted documents, validates required fields, cross-checks with application data, requests missing items via templated email, and hands a clean file to the sales rep.
- **Tech:** OCR, tool calling (email via MCP), guardrails on outbound communication.
- **Metric:** Onboarding cycle time ↓, incomplete-application loops ↓.

### 4.8 IT / Engineering — Dev Agent
- **Pain:** Small, well-defined tickets (config changes, minor fixes, boilerplate) queue behind larger work.
- **Solution:** Agent picks labeled Jira tickets → reads the linked GitHub repo → drafts implementation on a branch → opens a PR with description and test notes → notifies the team on Slack. Engineers review and merge; the agent never merges.
- **Tech:** MCP (Jira, GitHub, Slack), agentic framework (multi-step planning), guardrails (branch-only writes, protected paths).
- **Metric:** Small-ticket lead time ↓, engineer time freed for complex work.

### 4.9 Data & Analytics — Self-Service Analytics Agent
- **Pain:** The 5–6 person data science team receives constant ad-hoc query requests from business teams.
- **Solution:** Text-to-SQL agent over a governed semantic layer: business users ask questions in natural language, agent generates and executes **read-only** SQL against approved views, returns tables/charts with the SQL shown for transparency.
- **Tech:** SQL, LLM, prompt engineering, hard guardrails (read-only role, table allowlist, row limits).
- **Metric:** Ad-hoc request load on DS team ↓, time-to-answer for business questions ↓.

### 4.10 Legal & Compliance — Document Review Assistant
- **Pain:** Contract and policy review (vendor agreements, KVKK/data-protection checks) is slow and repetitive.
- **Solution:** RAG agent grounded in company legal playbooks; highlights risky clauses, missing standard terms, and KVKK-relevant sections with citations. Advisory only — outputs are drafts for counsel review.
- **Tech:** RAG, vector DB, prompt engineering.
- **Metric:** First-pass review time ↓.

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
