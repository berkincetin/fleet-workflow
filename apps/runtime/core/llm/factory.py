"""Build a production LLMClient from settings + the model registry (task 2.3).

Loads model rows from the registry DB, annotates each with a `fleet_role` (the
registry schema §4.1 has no role column — roles are per-agent references in the
TRD; for the default matrix we derive the tier from the canonical model name),
and wires the real ProxyTransport + SpendLedger sink. This is the single entry
point agents use; nothing else constructs an LLMClient.
"""

from __future__ import annotations

import os
from typing import Any

from core.llm.budget import DbBudgetChecker
from core.llm.client import LLMClient
from core.llm.ledger import SpendLedger
from core.llm.transport import ProxyTransport
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine


def derive_role(model_name: str) -> str:
    """Map a default-matrix model name to its tier role for routing."""
    if "embeddings" in model_name:
        return "embeddings"
    if "utility" in model_name:
        return "utility"
    if "reasoning" in model_name:
        return "reasoning"
    return "reasoning"


def annotate_roles(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Attach a derived ``fleet_role`` to each registry row (idempotent)."""
    out: list[dict[str, Any]] = []
    for row in rows:
        row = dict(row)
        row.setdefault("fleet_role", derive_role(row["name"]))
        out.append(row)
    return out


async def load_active_models(session_factory: async_sessionmaker[Any]) -> list[dict[str, Any]]:
    """Read active/degraded registry rows the gateway may route to."""
    query = text(
        "SELECT name, provider, litellm_model_id, sensitivity_clearance, "
        "input_price_per_1k, output_price_per_1k, cached_input_price "
        "FROM models WHERE status IN ('active', 'degraded')"
    )
    async with session_factory() as session:
        result = await session.execute(query)
        rows = [dict(m._mapping) for m in result]
    return annotate_roles(rows)


async def build_client(
    *,
    database_url: str | None = None,
    litellm_base_url: str | None = None,
    litellm_master_key: str | None = None,
) -> LLMClient:
    """Assemble an LLMClient over the real proxy + registry-backed model list."""
    database_url = database_url or os.environ.get(
        "FLEET_DATABASE_URL",
        "postgresql+asyncpg://fleet:fleet_dev_pw@localhost:5432/fleet",
    )
    base_url = litellm_base_url or os.environ.get(
        "FLEET_LITELLM_BASE_URL", "http://localhost:4000/v1"
    )
    master_key = litellm_master_key or os.environ.get(
        "FLEET_LITELLM_MASTER_KEY", "sk-fleet-dev-master"
    )
    # CPU-only local-lane inference (no GPU — task 8.1's rehearsal finding) can
    # take well over the 60s default for a 7B model's full JSON response;
    # overridable per-environment rather than raising the default outright,
    # since a genuinely stuck cloud call shouldn't hang this long either.
    timeout = float(os.environ.get("FLEET_LITELLM_TIMEOUT", "60"))

    engine = create_async_engine(database_url, pool_pre_ping=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    models = await load_active_models(session_factory)
    transport = ProxyTransport(base_url=base_url, master_key=master_key, timeout=timeout)
    ledger = SpendLedger(session_factory)
    budget_checker = DbBudgetChecker(session_factory)
    return LLMClient(
        models=models,
        transport=transport,
        ledger=ledger,
        budget_checker=budget_checker,
    )
