# TRD · Model Management & LLM Gateway (§4)

<!-- Derived from docs/TECHNICAL_REQUIREMENTS.md. The original is canonical.
     Any change here must also be applied to docs/TECHNICAL_REQUIREMENTS.md in the same PR. -->

## 4. Model Management & LLM Gateway

### 4.1 Model Registry [CORE]
Table `models` (mirrored into LiteLLM config): `name, provider, litellm_model_id, endpoint, input_price_per_1k, output_price_per_1k, cached_input_price, context_window, capabilities[vision,tools,json], max_output_tokens, sensitivity_clearance[public|internal|confidential|pii], region, status`.

**Add-a-model flow (admin UI):** fill form → row inserted → LiteLLM config regenerated & hot-reloaded → model instantly selectable in Agent Builder. Any OpenAI-compatible endpoint (including a colleague's experimental vLLM box) can be added the same way. Connectivity + capability smoke test runs automatically on add.

### 4.2 Default Model Matrix [CORE]
Seeded into the registry on `make seed` (exact provider model IDs pinned at Day 0 in `gateway/litellm/config.yaml`; all editable in Admin → Models):

| Role | Default | Fallback chain | Clearance | Notes |
|---|---|---|---|---|
| Reasoning | Claude Sonnet (Anthropic) | GPT-4o → Gemini Pro | `internal` | prompt caching on system+tools+KB blocks |
| Utility | Gemini Flash | GPT-4o-mini → Claude Haiku | `internal` | classification, extraction, routing, summaries |
| Vision/OCR (cloud, non-PII) | Gemini Flash | GPT-4o | `internal` | listing photos, non-sensitive invoice OCR |
| Embeddings (cloud) | OpenAI text-embedding-3-small | Gemini embedding | `internal` | 1536-dim |
| Local LLM (pii lane) | Ollama `qwen2.5:14b-instruct-q4_K_M` (7b only where RAM/VRAM cannot hold 14b) | — | `pii` | GPU host-native |
| Local embeddings (pii lane) | Ollama `bge-m3` | — | `pii` | 1024-dim; **pii collections never embed via cloud** |

**Clearance rules:** `sensitivity_clearance` is ordered `public < internal < confidential < pii`; a model may serve requests whose effective sensitivity is at or below its clearance. Cloud models default to `internal`. Raising a cloud model to `confidential` is an explicit platform_admin action (in-region / DPA-cleared providers only) recorded in audit; no cloud model is ever cleared for `pii`. `confidential`/`pii` **content** reaches cloud models only via the redaction-downgrade rule (§8) — i.e., after the PII pipeline has produced a redacted variant whose effective sensitivity is `internal`.

Embedding model is fixed per collection at creation time (model + dimension recorded in collection metadata; one Qdrant collection per embedding space).

### 4.3 Routing & Tiering [CORE]
- Each agent declares `reasoning_model` and `utility_model`. Framework helpers (`llm.utility()`, `llm.reasoning()`) choose per call-site: classification, extraction, routing, summarization → utility; planning, generation, judgment → reasoning.
- **Sensitivity routing (KVKK):** the gateway client refuses to send a request whose **effective sensitivity** (max of inputs, after the redaction-downgrade rule in §8) exceeds a model's `sensitivity_clearance`. PII-tagged traffic can only reach `local` or explicitly cleared in-region models; unredacted `confidential` likewise stays local unless a model is explicitly cleared (§4.2 clearance rules). Enforced in code (`core/llm/client.py`) + tested; not a convention.
- **Fallbacks:** per-model fallback chains in LiteLLM (e.g., primary → same-tier alternate → local) with circuit breaking on provider errors.

### 4.4 Failure behavior [CORE]
Provider 5xx/timeout → retry w/ backoff (2 attempts) → fallback chain → if all fail, graceful agent error with trace link. Budget-exceeded → HTTP 402-style domain error surfaced in UI with "request increase" action.
