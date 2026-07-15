# Project Overview · Department Use Cases

<!-- Derived from docs/PROJECT_OVERVIEW.md. The original is canonical.
     Any change here must also be applied to docs/PROJECT_OVERVIEW.md in the same PR. -->

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
