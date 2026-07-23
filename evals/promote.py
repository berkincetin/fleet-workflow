"""Promote UI-created examples (eval_cases.source='user') into the versioned
jsonl datasets (task 6.5.2). `evals/runner.py` and CI only ever read the
jsonl files — this script is a manual, builder-run step to fold a
demonstrated-useful example into the real dataset; it never runs
automatically and the runner never reads the `eval_cases` table directly.

Usage: `uv run python -m evals.promote --agent support_copilot`
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
from pathlib import Path

EVALS_DIR = Path(__file__).resolve().parent


async def promote(agent_name: str) -> int:
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import create_async_engine

    database_url = os.environ.get(
        "FLEET_DATABASE_URL", "postgresql+asyncpg://fleet:fleet_dev_pw@localhost:5432/fleet"
    )
    engine = create_async_engine(database_url)
    async with engine.connect() as conn:
        rows = (
            await conn.execute(
                text(
                    "SELECT case_id, payload FROM eval_cases "
                    "WHERE agent_name = :agent AND source = 'user' ORDER BY id"
                ),
                {"agent": agent_name},
            )
        ).all()
    await engine.dispose()

    if not rows:
        return 0

    dataset_path = EVALS_DIR / "datasets" / f"{agent_name}.jsonl"
    existing_ids = set()
    if dataset_path.exists():
        for line in dataset_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                existing_ids.add(json.loads(line)["id"])

    new_lines = []
    for case_id, payload in rows:
        if case_id in existing_ids:
            continue
        new_lines.append(json.dumps(payload, ensure_ascii=False))

    if not new_lines:
        return 0

    with dataset_path.open("a", encoding="utf-8") as f:
        for line in new_lines:
            f.write(line + "\n")

    return len(new_lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--agent", required=True)
    args = parser.parse_args()

    count = asyncio.run(promote(args.agent))
    print(f"{args.agent}: promoted {count} example(s) into evals/datasets/{args.agent}.jsonl")


if __name__ == "__main__":
    main()
