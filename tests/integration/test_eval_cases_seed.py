"""Integration: eval_cases seeding (task 6.5.2) is idempotent and matches
evals/datasets/*.jsonl line counts per agent; evals/promote.py round-trips a
UI-created (source='user') case back into the jsonl without disturbing
evals/runner.py's load_dataset() contract.
"""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from fleet_api.db import get_engine
from fleet_api.seed import seed_eval_cases
from sqlalchemy import text
from testcontainers.postgres import PostgresContainer

EVALS_DIR = Path(__file__).resolve().parents[2] / "evals"

# evals/ is a plain directory, not an installed package (same convention as
# tests/unit/test_eval_runner*.py) — add it to sys.path and import its
# top-level modules by bare name, not as `evals.promote`/`evals.runner`.
if str(EVALS_DIR) not in sys.path:
    sys.path.insert(0, str(EVALS_DIR))


@pytest.fixture(scope="module")
def migrated_pg() -> str:
    with PostgresContainer("postgres:16") as pg:
        raw = pg.get_connection_url()
        os.environ["FLEET_DATABASE_URL"] = raw
        subprocess.run(
            [sys.executable, "-m", "alembic", "-c",
             "infra/migrations/alembic.ini", "upgrade", "head"],
            check=True,
            env={**os.environ},
        )
        os.environ["FLEET_DATABASE_URL"] = raw.replace("+psycopg2", "+asyncpg")
        yield os.environ["FLEET_DATABASE_URL"]


def _jsonl_line_count(agent_name: str) -> int:
    path = EVALS_DIR / "datasets" / f"{agent_name}.jsonl"
    return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())


def test_seed_eval_cases_is_idempotent_and_matches_jsonl_counts(migrated_pg: str) -> None:
    asyncio.run(seed_eval_cases())
    asyncio.run(seed_eval_cases())  # second run must not duplicate or error

    async def _check() -> None:
        engine = get_engine(migrated_pg)
        async with engine.connect() as conn:
            for agent_name in ("support_copilot", "analytics", "dev_agent", "invoice_agent"):
                count = (
                    await conn.execute(
                        text("SELECT count(*) FROM eval_cases WHERE agent_name = :a"),
                        {"a": agent_name},
                    )
                ).scalar_one()
                assert count == _jsonl_line_count(agent_name), (
                    f"{agent_name}: DB has {count} rows, jsonl has "
                    f"{_jsonl_line_count(agent_name)} lines"
                )
                source = (
                    await conn.execute(
                        text(
                            "SELECT DISTINCT source FROM eval_cases WHERE agent_name = :a"
                        ),
                        {"a": agent_name},
                    )
                ).scalars().all()
                assert source == ["seed"]
        await engine.dispose()

    asyncio.run(_check())


def test_promote_round_trips_a_user_case_into_jsonl_and_load_dataset(
    migrated_pg: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import promote as promote_module
    from runner import load_dataset

    # Isolate this test's write from the real evals/datasets/support_copilot.jsonl.
    fake_evals_dir = tmp_path / "evals"
    (fake_evals_dir / "datasets").mkdir(parents=True)
    dataset_path = fake_evals_dir / "datasets" / "support_copilot.jsonl"
    dataset_path.write_text(
        json.dumps({"id": "seed-1", "question": "Existing seeded question?"}) + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(promote_module, "EVALS_DIR", fake_evals_dir)

    async def _insert_user_case() -> None:
        engine = get_engine(migrated_pg)
        async with engine.begin() as conn:
            await conn.execute(
                text(
                    "INSERT INTO eval_cases (agent_name, case_id, payload, source) "
                    "VALUES ('support_copilot', 'user-1', :payload, 'user') "
                    "ON CONFLICT (agent_name, case_id) DO NOTHING"
                ),
                {"payload": json.dumps({"id": "user-1", "question": "Yeni örnek soru?"})},
            )
        await engine.dispose()

    asyncio.run(_insert_user_case())
    promoted_count = asyncio.run(promote_module.promote("support_copilot"))
    assert promoted_count == 1

    cases = load_dataset(dataset_path)
    ids = {c.id for c in cases}
    assert ids == {"seed-1", "user-1"}

    # Promoting again must not duplicate the already-promoted case.
    promoted_again = asyncio.run(promote_module.promote("support_copilot"))
    assert promoted_again == 0
    assert len(load_dataset(dataset_path)) == 2
