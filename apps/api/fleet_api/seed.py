"""Seed synthetic data and analytics fixture warehouse views. Idempotent."""

from __future__ import annotations

import asyncio

from fleet_api.db import database_url, get_engine
from sqlalchemy import text

_DEPARTMENTS = ["Customer Service", "Data", "Finance", "HR", "IT"]

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
    ("reasoning-fallback-2", "gemini", "gemini/gemini-1.5-pro", 0.00125, 0.005, 2000000,
     ["tools", "json", "vision"], 8192, "internal", "us"),
    ("utility", "gemini", "gemini/gemini-1.5-flash", 0.000075, 0.0003, 1000000,
     ["tools", "json", "vision"], 8192, "internal", "us"),
    ("utility-fallback-1", "openai", "openai/gpt-4o-mini", 0.00015, 0.0006, 128000,
     ["tools", "json"], 16384, "internal", "us"),
    ("utility-fallback-2", "anthropic", "anthropic/claude-haiku-4-5", 0.001, 0.005, 200000,
     ["tools", "json"], 8192, "internal", "us"),
    ("embeddings", "openai", "openai/text-embedding-3-small", 0.00002, 0.0, 8191,
     ["json"], 1, "internal", "us"),
    ("local-reasoning", "ollama", "ollama/qwen2.5:7b-instruct-q4_K_M", 0.0, 0.0, 32768,
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
        await conn.execute(
            text(
                "GRANT SELECT ON fixture_sales, fixture_orders, "
                "fixture_purchase_orders TO fleet_readonly"
            )
        )
    await engine.dispose()


def main() -> None:
    asyncio.run(seed())
    asyncio.run(seed_support_copilot())
    asyncio.run(seed_analytics_agent())
    asyncio.run(seed_dev_agent())
    asyncio.run(seed_invoice_agent())


if __name__ == "__main__":
    main()
