"""Seed synthetic data and analytics fixture warehouse views. Idempotent."""

from __future__ import annotations

import asyncio

from fleet_api.db import database_url, get_engine
from sqlalchemy import text

_DEPARTMENTS = ["Customer Service", "Data", "Finance", "HR", "IT"]

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
        # Analytics fixture views consumed by 5.2 evals (read via fleet_readonly).
        await conn.execute(text(_FIXTURE_SALES_VIEW))
        await conn.execute(text(_FIXTURE_ORDERS_VIEW))
        await conn.execute(
            text("GRANT SELECT ON fixture_sales, fixture_orders TO fleet_readonly")
        )
    await engine.dispose()


def main() -> None:
    asyncio.run(seed())


if __name__ == "__main__":
    main()
