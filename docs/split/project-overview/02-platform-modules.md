# Project Overview · Solution: The Five Core Modules

<!-- Derived from docs/PROJECT_OVERVIEW.md. The original is canonical.
     Any change here must also be applied to docs/PROJECT_OVERVIEW.md in the same PR. -->

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
