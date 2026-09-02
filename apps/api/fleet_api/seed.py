"""Seed synthetic data and analytics fixture warehouse views. Idempotent."""

from __future__ import annotations

import asyncio
import datetime as dt
import json
from pathlib import Path

from fleet_api.db import database_url, get_engine
from sqlalchemy import text

_DEMO_AGENTS = [
    "support_copilot", "analytics", "dev_agent", "invoice_agent", "hr_agent", "hr_onboarding",
    "listing_quality", "vehicle_intake", "insights_publisher", "dealer_onboarding",
    "legal_review",
]
_DEMO_MODELS = ["utility", "reasoning", "utility-fallback-1"]

# evals/ lives at the repo root, three levels above apps/api/fleet_api/.
_EVALS_DIR = Path(__file__).resolve().parents[3] / "evals"

_DEPARTMENTS = [
    "Customer Service", "Data", "Finance", "HR", "IT", "Listings Ops", "Trink sat",
    "Marketing", "Corporate Sales", "Legal",
]

# Default model matrix (TRD §4.2), mirrored from gateway/litellm/config.yaml.
# Seeded into the registry so Admin → Models and the gateway client have rows to
# read on a fresh install. status='active' here is a seed convenience (Day-0
# pinned models are assumed reachable); a real add via the API runs a smoke test.
# (name, provider, litellm_model_id, in_price_1k, out_price_1k, ctx, caps,
#  max_out, clearance, region)
_DEFAULT_MODELS = [
    ("reasoning", "anthropic", "anthropic/claude-sonnet-4-5", 0.003, 0.015, 200000,
     ["tools", "json", "vision"], 8192, "internal", "us"),
    ("reasoning-fallback-1", "openai", "openai/gpt-4o", 0.0025, 0.01, 128000,
     ["tools", "json", "vision"], 16384, "internal", "us"),
    ("reasoning-fallback-2", "gemini", "gemini/gemini-3.6-flash", 0.00125, 0.005, 1000000,
     ["tools", "json", "vision"], 8192, "internal", "us"),
    # Primary utility is vision-capable OpenAI gpt-4o-mini (Wave-1 vision agents,
    # task 11.x); the retired gemini-1.5-flash moved to a fallback on a current id.
    ("utility", "openai", "openai/gpt-4o-mini", 0.00015, 0.0006, 128000,
     ["tools", "json", "vision"], 16384, "internal", "us"),
    ("utility-fallback-1", "gemini", "gemini/gemini-3.6-flash", 0.000075, 0.0003, 1000000,
     ["tools", "json", "vision"], 8192, "internal", "us"),
    ("utility-fallback-2", "anthropic", "anthropic/claude-haiku-4-5", 0.001, 0.005, 200000,
     ["tools", "json"], 8192, "internal", "us"),
    ("embeddings", "openai", "openai/text-embedding-3-small", 0.00002, 0.0, 8191,
     ["json"], 1, "internal", "us"),
    # 14B (task 12.2): the local lane serves confidential/pii reasoning, and
    # dept scenario 10's contract review is the hardest job on it. See the note
    # in gateway/litellm/config.yaml for the measurement that drove the bump.
    ("local-reasoning", "ollama", "ollama/qwen2.5:14b-instruct-q4_K_M", 0.0, 0.0, 32768,
     ["tools", "json"], 4096, "pii", "local"),
    ("local-embeddings", "ollama", "ollama/bge-m3", 0.0, 0.0, 8192,
     ["json"], 1, "pii", "local"),
]

_FIXTURE_SALES_VIEW = """
CREATE OR REPLACE VIEW fixture_sales AS
SELECT g AS id,
       (ARRAY['TR','DE','US','FR'])[1 + (g % 4)] AS region,
       (100 + (g * 37) % 900)::numeric AS amount_usd,
       (DATE '2026-01-01' + (g % 180)) AS sold_on
FROM generate_series(1, 500) AS g;
"""

_FIXTURE_ORDERS_VIEW = """
CREATE OR REPLACE VIEW fixture_orders AS
SELECT g AS id,
       1 + (g % 500) AS sale_id,
       (1 + (g % 5)) AS quantity,
       (g % 3 = 0) AS refunded
FROM generate_series(1, 500) AS g;
"""

# Task 6.3, dept scenario 04 (Invoice & Reconciliation): a small, fixed
# purchase-order fixture (not generate_series-scaled like the analytics
# views) — invoice validation matches a specific PO number, so the eval
# dataset's cases need stable, known-in-advance rows rather than 500
# procedurally generated ones. 12 distinct rows (not 5) so the eval
# dataset's 12 "clean" extraction-accuracy cases can each use a genuinely
# distinct PO number — duplicate-PO detection is itself a real guardrail
# (validator.check_duplicate), so reusing PO numbers across "clean" cases
# would make the agent correctly flag them as duplicates within the batch.
_FIXTURE_PURCHASE_ORDERS_VIEW = """
CREATE OR REPLACE VIEW fixture_purchase_orders AS
SELECT * FROM (VALUES
    ('PO-1001', 'Acme Tedarik A.S.', 1250.00::numeric, 'TRY'),
    ('PO-1002', 'Bilgi Teknoloji Ltd.', 4800.50::numeric, 'TRY'),
    ('PO-1003', 'Kartal Lojistik', 990.00::numeric, 'TRY'),
    ('PO-1004', 'Deniz Ofis Malzemeleri', 315.75::numeric, 'TRY'),
    ('PO-1005', 'Yildiz Danismanlik', 7600.00::numeric, 'TRY'),
    ('PO-1006', 'Marmara Insaat A.S.', 2100.00::numeric, 'TRY'),
    ('PO-1007', 'Ege Elektronik Ltd.', 615.25::numeric, 'TRY'),
    ('PO-1008', 'Karadeniz Nakliyat', 3300.00::numeric, 'TRY'),
    ('PO-1009', 'Anadolu Yazilim', 5450.00::numeric, 'TRY'),
    ('PO-1010', 'Toros Kimya Sanayi', 890.40::numeric, 'TRY'),
    ('PO-1011', 'Boğaziçi Danışmanlık', 4200.00::numeric, 'TRY'),
    ('PO-1012', 'Sakarya Matbaacılık', 175.50::numeric, 'TRY'),
    ('PO-1013', 'Fırat Enerji', 1875.00::numeric, 'TRY'),
    ('PO-1014', 'Meric Tarim Urunleri', 660.00::numeric, 'TRY'),
    ('PO-1015', 'Van Golu Turizm', 425.00::numeric, 'TRY')
) AS t(po_number, vendor, amount, currency);
"""


async def seed_support_copilot() -> None:
    """Support Copilot demo agent + its cs-help-center/cs-procedures collections
    (task 4.4, department scenario 01). Idempotent on unique names, so safe to
    call every `make seed` alongside the general seed()."""
    engine = get_engine(database_url())
    async with engine.begin() as conn:
        dept_id = (
            await conn.execute(
                text("SELECT id FROM departments WHERE name = 'Customer Service'")
            )
        ).scalar_one()

        for name, sensitivity, retention_days in (
            ("cs-help-center", "internal", None),
            ("cs-procedures", "internal", None),
        ):
            await conn.execute(
                text(
                    "INSERT INTO collections (name, dept_id, sensitivity, retention_days, "
                    "pii_policy) VALUES (:n, :d, :s, :r, 'redact') "
                    "ON CONFLICT (name) DO NOTHING"
                ),
                {"n": name, "d": dept_id, "s": sensitivity, "r": retention_days},
            )

        help_center_id = (
            await conn.execute(text("SELECT id FROM collections WHERE name = 'cs-help-center'"))
        ).scalar_one()
        procedures_id = (
            await conn.execute(text("SELECT id FROM collections WHERE name = 'cs-procedures'"))
        ).scalar_one()

        await conn.execute(
            text(
                "INSERT INTO agents (name, dept_id, reasoning_model, utility_model, "
                "sensitivity, semantic_cache, semantic_cache_threshold, max_context_tokens, "
                "collection_ids) VALUES (:n, :d, 'reasoning', 'utility', 'internal', "
                "true, 0.95, 12000, :cids) ON CONFLICT (name) DO NOTHING"
            ),
            {"n": "support_copilot", "d": dept_id, "cids": [help_center_id, procedures_id]},
        )
    await engine.dispose()


async def seed_analytics_agent() -> None:
    """Analytics demo agent (task 5.2, department scenario 02). No RAG
    collections — its "knowledge" is the inline semantic layer in
    agents.analytics.semantic_layer, not a KB collection. semantic_cache is
    OFF per the scenario (data freshness matters more than repeat-question
    cost for ad-hoc analytics)."""
    engine = get_engine(database_url())
    async with engine.begin() as conn:
        dept_id = (
            await conn.execute(text("SELECT id FROM departments WHERE name = 'Data'"))
        ).scalar_one()
        await conn.execute(
            text(
                "INSERT INTO agents (name, dept_id, reasoning_model, utility_model, "
                "sensitivity, semantic_cache, semantic_cache_threshold, max_context_tokens, "
                "collection_ids) VALUES ('analytics', :d, 'reasoning', 'utility', 'internal', "
                "false, 0.95, 8000, '{}') ON CONFLICT (name) DO NOTHING"
            ),
            {"d": dept_id},
        )
    await engine.dispose()


async def seed_dev_agent() -> None:
    """Dev Agent demo agent (task 5.5, department scenario 03). No RAG
    collections; max_context_tokens=24000 per the scenario (code context is
    larger than a typical chat/analytics turn)."""
    engine = get_engine(database_url())
    async with engine.begin() as conn:
        dept_id = (
            await conn.execute(text("SELECT id FROM departments WHERE name = 'IT'"))
        ).scalar_one()
        await conn.execute(
            text(
                "INSERT INTO agents (name, dept_id, reasoning_model, utility_model, "
                "sensitivity, semantic_cache, semantic_cache_threshold, max_context_tokens, "
                "collection_ids) VALUES ('dev_agent', :d, 'reasoning', 'utility', 'internal', "
                "false, 0.95, 24000, '{}') ON CONFLICT (name) DO NOTHING"
            ),
            {"d": dept_id},
        )
    await engine.dispose()


async def seed_invoice_agent() -> None:
    """Invoice & Reconciliation demo agent (task 6.3, department scenario 04).
    sensitivity=confidential (raw invoices carry IBAN/tax-no PII per the
    scenario's OCR-local/redact-at-ingest requirements); semantic_cache OFF
    (§ scenario spec — every invoice is a distinct document, nothing to
    cache). No RAG collections — the "knowledge" is the fixture PO table via
    pg_ro, same shape as Analytics' semantic layer."""
    engine = get_engine(database_url())
    async with engine.begin() as conn:
        dept_id = (
            await conn.execute(text("SELECT id FROM departments WHERE name = 'Finance'"))
        ).scalar_one()
        await conn.execute(
            text(
                "INSERT INTO agents (name, dept_id, reasoning_model, utility_model, "
                "sensitivity, semantic_cache, semantic_cache_threshold, max_context_tokens, "
                "collection_ids) VALUES ('invoice_agent', :d, 'reasoning', 'utility', "
                "'confidential', false, 0.95, 8000, '{}') ON CONFLICT (name) DO NOTHING"
            ),
            {"d": dept_id},
        )
    await engine.dispose()


async def seed_hr_agents() -> None:
    """HR Talent & Onboarding demo agents (task 8.5, department scenario 05):
    `hr_agent` (LangGraph, CV -> profile -> role match -> shortlist draft
    approval — pii lane, sensitivity=pii, no RAG collection: its "knowledge"
    is the uploaded CV itself, same "no collection_ids" shape as invoice_agent)
    and `hr_onboarding` (plain RAG chat agent over `hr-policies`, internal,
    semantic_cache ON per the scenario spec — policy answers are stable and
    worth caching, unlike a distinct-per-document agent like invoice/analytics).
    `hr-cvs` (pii, retention 365 days, allow-local-only — CVs never leave the
    local lane, including embeddings) exists so a future direct-upload CV
    intake path has a collection to ingest into; `hr_agent`'s own run path
    (routers/hr_agent.py) takes the image directly, not via this collection."""
    engine = get_engine(database_url())
    async with engine.begin() as conn:
        dept_id = (
            await conn.execute(text("SELECT id FROM departments WHERE name = 'HR'"))
        ).scalar_one()

        await conn.execute(
            text(
                "INSERT INTO collections (name, dept_id, sensitivity, retention_days, "
                "pii_policy) VALUES ('hr-cvs', :d, 'pii', 365, 'allow-local-only') "
                "ON CONFLICT (name) DO NOTHING"
            ),
            {"d": dept_id},
        )
        await conn.execute(
            text(
                "INSERT INTO collections (name, dept_id, sensitivity, retention_days, "
                "pii_policy) VALUES ('hr-policies', :d, 'internal', NULL, 'redact') "
                "ON CONFLICT (name) DO NOTHING"
            ),
            {"d": dept_id},
        )
        hr_policies_id = (
            await conn.execute(text("SELECT id FROM collections WHERE name = 'hr-policies'"))
        ).scalar_one()

        await conn.execute(
            text(
                "INSERT INTO agents (name, dept_id, reasoning_model, utility_model, "
                "sensitivity, semantic_cache, semantic_cache_threshold, max_context_tokens, "
                "collection_ids) VALUES ('hr_agent', :d, 'reasoning', 'utility', 'pii', "
                "false, 0.95, 8000, '{}') ON CONFLICT (name) DO NOTHING"
            ),
            {"d": dept_id},
        )
        await conn.execute(
            text(
                "INSERT INTO agents (name, dept_id, reasoning_model, utility_model, "
                "sensitivity, semantic_cache, semantic_cache_threshold, max_context_tokens, "
                "collection_ids) VALUES ('hr_onboarding', :d, 'reasoning', 'utility', "
                "'internal', true, 0.95, 8000, :cids) ON CONFLICT (name) DO NOTHING"
            ),
            {"d": dept_id, "cids": [hr_policies_id]},
        )
    await engine.dispose()


_FIXTURE_PRICE_INDEX_VIEW = """
CREATE OR REPLACE VIEW fixture_price_index AS
SELECT * FROM (VALUES
  ('sedan-2018', 400000, 600000, 500000, 'TRY'),
  ('suv-2020', 650000, 950000, 800000, 'TRY'),
  ('hatchback-2019', 380000, 560000, 460000, 'TRY')
) AS t(segment, band_low, band_high, band_median, currency);
"""


async def seed_listing_quality_agent() -> None:
    """Listing Quality agent (task 11.1, dept scenario 06). Vision flag-only
    agent; no RAG collections. sensitivity internal (public listing data)."""
    engine = get_engine(database_url())
    async with engine.begin() as conn:
        dept_id = (
            await conn.execute(
                text("SELECT id FROM departments WHERE name = 'Listings Ops'")
            )
        ).scalar_one()
        await conn.execute(
            text(
                "INSERT INTO agents (name, dept_id, reasoning_model, utility_model, "
                "sensitivity, semantic_cache, semantic_cache_threshold, max_context_tokens, "
                "collection_ids) VALUES ('listing_quality', :d, 'reasoning', 'utility', "
                "'internal', false, 0.95, 8000, '{}') ON CONFLICT (name) DO NOTHING"
            ),
            {"d": dept_id},
        )
    await engine.dispose()


_FIXTURE_COMPARABLES_VIEW = """
CREATE OR REPLACE VIEW fixture_comparables AS
SELECT * FROM (VALUES
  ('sedan-2018', 480000), ('sedan-2018', 500000), ('sedan-2018', 520000),
  ('sedan-2018', 460000), ('sedan-2018', 540000),
  ('suv-2020', 700000), ('suv-2020', 800000), ('suv-2020', 750000),
  ('suv-2020', 820000), ('suv-2020', 780000),
  ('hatchback-2019', 420000), ('hatchback-2019', 450000), ('hatchback-2019', 480000)
) AS t(segment, price);
"""


async def seed_vehicle_intake_agent() -> None:
    """Vehicle Intake agent (task 11.2, dept scenario 07). Confidential; local
    OCR + redact + cloud reasoning; no write tools; advisory."""
    engine = get_engine(database_url())
    async with engine.begin() as conn:
        dept_id = (
            await conn.execute(
                text("SELECT id FROM departments WHERE name = 'Trink sat'")
            )
        ).scalar_one()
        await conn.execute(
            text(
                "INSERT INTO agents (name, dept_id, reasoning_model, utility_model, "
                "sensitivity, semantic_cache, semantic_cache_threshold, max_context_tokens, "
                "collection_ids) VALUES ('vehicle_intake', :d, 'reasoning', 'utility', "
                "'confidential', false, 0.95, 8000, '{}') ON CONFLICT (name) DO NOTHING"
            ),
            {"d": dept_id},
        )
    await engine.dispose()


_FIXTURE_PRICE_INDEX_MONTHLY_VIEW = """
CREATE OR REPLACE VIEW fixture_index_monthly AS
SELECT * FROM (VALUES
  ('sedan-2018', 500000, 340),
  ('suv-2020', 800000, 210),
  ('hatchback-2019', 460000, 180)
) AS t(segment, avg_price, listing_count);
"""


async def seed_insights_publisher_agent() -> None:
    """Insights Publisher agent (task 11.3, dept scenario 08). Internal; reasoning
    + utility; mkt-brand KB (brand voice); cms.publish/social.post write:external
    → approval. semantic_cache OFF (each monthly report is distinct)."""
    engine = get_engine(database_url())
    async with engine.begin() as conn:
        dept_id = (
            await conn.execute(text("SELECT id FROM departments WHERE name = 'Marketing'"))
        ).scalar_one()
        await conn.execute(
            text(
                "INSERT INTO collections (name, dept_id, sensitivity, retention_days, "
                "pii_policy) VALUES ('mkt-brand', :d, 'internal', NULL, 'redact') "
                "ON CONFLICT (name) DO NOTHING"
            ),
            {"d": dept_id},
        )
        mkt_brand_id = (
            await conn.execute(text("SELECT id FROM collections WHERE name = 'mkt-brand'"))
        ).scalar_one()
        await conn.execute(
            text(
                "INSERT INTO agents (name, dept_id, reasoning_model, utility_model, "
                "sensitivity, semantic_cache, semantic_cache_threshold, max_context_tokens, "
                "collection_ids) VALUES ('insights_publisher', :d, 'reasoning', 'utility', "
                "'internal', false, 0.95, 8000, :cids) ON CONFLICT (name) DO NOTHING"
            ),
            {"d": dept_id, "cids": [mkt_brand_id]},
        )
    await engine.dispose()


async def seed_dealer_onboarding_agent() -> None:
    """Dealer Onboarding agent (task 12.1, dept scenario 09). sensitivity=pii:
    the authorization certificate and tax registration carry the dealer's tax
    number and IBAN, and `pii` is the one level core.llm.routing never
    downgrades — so extraction is pinned to the local lane by the registry row
    itself, not only by the agent code. No RAG collection (its "knowledge" is
    the uploaded documents, same shape as invoice_agent/hr_agent/vehicle_intake);
    semantic_cache off (every applicant's dossier is distinct)."""
    engine = get_engine(database_url())
    async with engine.begin() as conn:
        dept_id = (
            await conn.execute(
                text("SELECT id FROM departments WHERE name = 'Corporate Sales'")
            )
        ).scalar_one()
        await conn.execute(
            text(
                "INSERT INTO agents (name, dept_id, reasoning_model, utility_model, "
                "sensitivity, semantic_cache, semantic_cache_threshold, max_context_tokens, "
                "collection_ids) VALUES ('dealer_onboarding', :d, 'reasoning', 'utility', "
                "'pii', false, 0.95, 8000, '{}') ON CONFLICT (name) DO NOTHING"
            ),
            {"d": dept_id},
        )
    await engine.dispose()


async def seed_legal_review_agent() -> None:
    """Legal Document Review agent (task 12.2, dept scenario 10). sensitivity=
    confidential, which routes both the embedding and the reasoning call to the
    local lane (no cloud model in the default matrix is cleared above
    `internal`) — contracts stay on the machine. `legal-playbooks` is
    confidential + allow-local-only so its embeddings are local too, keeping the
    ingest and query vector spaces the same. semantic_cache off: two contracts
    that read alike are not interchangeable."""
    engine = get_engine(database_url())
    async with engine.begin() as conn:
        dept_id = (
            await conn.execute(text("SELECT id FROM departments WHERE name = 'Legal'"))
        ).scalar_one()
        await conn.execute(
            text(
                "INSERT INTO collections (name, dept_id, sensitivity, retention_days, "
                "pii_policy) VALUES ('legal-playbooks', :d, 'confidential', NULL, "
                "'allow-local-only') ON CONFLICT (name) DO NOTHING"
            ),
            {"d": dept_id},
        )
        playbooks_id = (
            await conn.execute(
                text("SELECT id FROM collections WHERE name = 'legal-playbooks'")
            )
        ).scalar_one()
        await conn.execute(
            text(
                "INSERT INTO agents (name, dept_id, reasoning_model, utility_model, "
                "sensitivity, semantic_cache, semantic_cache_threshold, max_context_tokens, "
                "collection_ids) VALUES ('legal_review', :d, 'reasoning', 'utility', "
                "'confidential', false, 0.95, 8000, :cids) ON CONFLICT (name) DO NOTHING"
            ),
            {"d": dept_id, "cids": [playbooks_id]},
        )
    await engine.dispose()


async def seed_eval_cases() -> None:
    """Import evals/datasets/*.jsonl into `eval_cases` (source='seed'), task
    6.5.2. Idempotent on (agent_name, case_id) via ON CONFLICT DO NOTHING —
    the jsonl files stay the CI eval source of truth; this only mirrors them
    into the DB so the Examples gallery has something to list without
    reaching into the repo's filesystem from a request handler."""
    engine = get_engine(database_url())
    async with engine.begin() as conn:
        for jsonl_path in sorted(_EVALS_DIR.glob("datasets/*.jsonl")):
            agent_name = jsonl_path.stem
            for line in jsonl_path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line:
                    continue
                row = json.loads(line)
                await conn.execute(
                    text(
                        "INSERT INTO eval_cases (agent_name, case_id, payload, source) "
                        "VALUES (:agent_name, :case_id, :payload, 'seed') "
                        "ON CONFLICT (agent_name, case_id) DO NOTHING"
                    ),
                    {
                        "agent_name": agent_name,
                        "case_id": row["id"],
                        "payload": json.dumps(row),
                    },
                )
    await engine.dispose()


async def seed_observability_demo() -> None:
    """Deterministic spend_ledger + audit_log rows spanning the last 14 days
    so the Cost dashboard and Audit explorer (task 7.2) render immediately on
    a fresh install, without needing a prior live chat/automation session.
    Idempotent via a 'demo-seed-' trace_id marker — neither table has a
    natural unique key to ON CONFLICT against, since both are append-only."""
    engine = get_engine(database_url())
    async with engine.begin() as conn:
        marker = await conn.execute(
            text("SELECT 1 FROM spend_ledger WHERE trace_id LIKE 'demo-seed-%' LIMIT 1")
        )
        if marker.first() is not None:
            return
        dept_ids = [
            row[0]
            for row in (await conn.execute(text("SELECT id FROM departments ORDER BY id"))).all()
        ]
        if not dept_ids:
            return
        now = dt.datetime.now(dt.UTC)
        for i in range(60):
            dept_id = dept_ids[i % len(dept_ids)]
            agent = _DEMO_AGENTS[i % len(_DEMO_AGENTS)]
            model = _DEMO_MODELS[i % len(_DEMO_MODELS)]
            tok_in = 400 + (i * 17) % 600
            tok_out = 150 + (i * 11) % 300
            tok_cached = tok_in // 3 if i % 3 == 0 else 0
            cost = round(tok_in * 0.0003 + tok_out * 0.0006, 6)
            trace_id = f"demo-seed-{i}"
            ts = now - dt.timedelta(days=i % 14, hours=i % 24)
            await conn.execute(
                text(
                    "INSERT INTO spend_ledger (ts, model, agent_id, user_id, dept_id, "
                    "tok_in, tok_out, tok_cached, cost_usd, trace_id) "
                    "VALUES (:ts, :model, :agent_id, :user_id, :dept_id, :tok_in, :tok_out, "
                    ":tok_cached, :cost_usd, :trace_id)"
                ),
                {
                    "ts": ts, "model": model, "agent_id": agent, "user_id": "demo-user",
                    "dept_id": str(dept_id), "tok_in": tok_in, "tok_out": tok_out,
                    "tok_cached": tok_cached, "cost_usd": cost, "trace_id": trace_id,
                },
            )
            if i % 4 == 0:
                await conn.execute(
                    text(
                        "INSERT INTO audit_log (ts, actor, actor_type, action, entity, "
                        "entity_id, trace_id) "
                        "VALUES (:ts, 'demo-user', 'user', :action, 'http_request', "
                        "'200', :trace_id)"
                    ),
                    {
                        "ts": ts,
                        "action": f"POST /v1/conversations/{i}/messages",
                        "trace_id": trace_id,
                    },
                )
    await engine.dispose()


async def seed() -> None:
    engine = get_engine(database_url())
    async with engine.begin() as conn:
        for name in _DEPARTMENTS:
            await conn.execute(
                text(
                    "INSERT INTO departments (name) VALUES (:n) "
                    "ON CONFLICT (name) DO NOTHING"
                ),
                {"n": name},
            )
        await conn.execute(
            text(
                "INSERT INTO users (kc_sub, email_hash, display_name, status) "
                "VALUES (:s, :e, :d, 'active') ON CONFLICT (kc_sub) DO NOTHING"
            ),
            {"s": "seed-admin", "e": "hash-admin", "d": "Seed Admin"},
        )
        # Default model matrix (§4.2). Idempotent on unique name.
        for m in _DEFAULT_MODELS:
            await conn.execute(
                text(
                    "INSERT INTO models (name, provider, litellm_model_id, "
                    "input_price_per_1k, output_price_per_1k, context_window, "
                    "capabilities, max_output_tokens, sensitivity_clearance, region, "
                    "status, smoke_status) "
                    "VALUES (:name, :provider, :mid, :inp, :outp, :ctx, :caps, :maxo, "
                    ":clr, :region, 'active', 'ok') "
                    "ON CONFLICT (name) DO NOTHING"
                ),
                {
                    "name": m[0], "provider": m[1], "mid": m[2], "inp": m[3],
                    "outp": m[4], "ctx": m[5], "caps": m[6], "maxo": m[7],
                    "clr": m[8], "region": m[9],
                },
            )
        # Analytics fixture views consumed by 5.2 evals (read via fleet_readonly).
        await conn.execute(text(_FIXTURE_SALES_VIEW))
        await conn.execute(text(_FIXTURE_ORDERS_VIEW))
        # Invoice-reconciliation fixture consumed by 6.3 (department scenario 04).
        await conn.execute(text(_FIXTURE_PURCHASE_ORDERS_VIEW))
        # Listing-quality price-index fixture consumed by 11.1 (dept scenario 06).
        await conn.execute(text(_FIXTURE_PRICE_INDEX_VIEW))
        # Vehicle-intake comparables fixture consumed by 11.2 (dept scenario 07).
        await conn.execute(text(_FIXTURE_COMPARABLES_VIEW))
        # Insights-publisher monthly index fixture consumed by 11.3 (dept scenario 08).
        await conn.execute(text(_FIXTURE_PRICE_INDEX_MONTHLY_VIEW))
        await conn.execute(
            text(
                "GRANT SELECT ON fixture_sales, fixture_orders, "
                "fixture_purchase_orders, fixture_price_index, fixture_comparables, "
                "fixture_index_monthly TO fleet_readonly"
            )
        )
    await engine.dispose()


def main() -> None:
    asyncio.run(seed())
    asyncio.run(seed_support_copilot())
    asyncio.run(seed_analytics_agent())
    asyncio.run(seed_dev_agent())
    asyncio.run(seed_invoice_agent())
    asyncio.run(seed_hr_agents())
    asyncio.run(seed_listing_quality_agent())
    asyncio.run(seed_vehicle_intake_agent())
    asyncio.run(seed_insights_publisher_agent())
    asyncio.run(seed_dealer_onboarding_agent())
    asyncio.run(seed_legal_review_agent())
    asyncio.run(seed_eval_cases())
    asyncio.run(seed_observability_demo())


if __name__ == "__main__":
    main()
