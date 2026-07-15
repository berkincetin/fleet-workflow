# Implementation Plan · Sprint 0 — Prerequisites

<!-- Derived from docs/IMPLEMENTATION_PLAN.md. The original is canonical.
     Any change here must also be applied to docs/IMPLEMENTATION_PLAN.md in the same PR. -->

## Sprint 0 — Prerequisites (user-assisted)

These items require the user (API keys, hardware, external accounts). They do **not** all need to be ready up front: Claude Code requests each one **at the moment the depending task needs it** (per the Task Execution Protocol) and pauses until provided.

- **0.1** API keys in `.env` (never committed): **Anthropic + OpenAI + Gemini**; pin exact model IDs in `gateway/litellm/config.yaml` per TRD §4.2. *(first needed: 2.1)*
- **0.2** Ollama installed **host-native with NVIDIA GPU**: `nvidia-smi` OK → `ollama pull qwen2.5:7b-instruct-q4_K_M` (pull 14b variant if VRAM ≥12 GB) → `ollama pull bge-m3` (local embeddings for pii lane). *(first needed: 2.3 live test; hard requirement in Sprint 8)*
- **0.3** Sandbox GitHub repo + PAT with repo scope (target of the **Dev Agent**, distinct from this project's own repo created in 1.0); Slack incoming webhook. *(first needed: 5.3)*
  *(The SMTP sandbox — mailpit — is a compose service added in 1.1, not a user-provided prerequisite; the email MCP server first needs it in 5.1.)*
- **0.4** Containers reach host Ollama via host gateway (compose `extra_hosts: host.docker.internal:host-gateway`; k3d equivalent in values-dev). *(verified with a LiteLLM test call in 2.3)*
