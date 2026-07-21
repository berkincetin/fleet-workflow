"""Seed the Support Copilot demo KB (task 4.4): upload evals/fixtures/support_copilot/*
into the cs-help-center / cs-procedures collections and ingest them for real
(the same MinIO -> pipeline -> Qdrant path a real upload takes), so the demo
path and the eval dataset both have real grounded content to cite.

Run via `make seed-docs` after `make seed` and `make migrate` (needs the
support_copilot agent's collections to already exist) and the dev stack up.
"""

from __future__ import annotations

import asyncio
import hashlib
import io
from pathlib import Path
from typing import Any

from core.llm.factory import build_client
from fleet_api.db import get_engine
from fleet_api.db import session_factory as make_session_factory
from fleet_rag.ingest.worker import _QdrantSinkAdapter, ingest_document
from fleet_rag.store.minio_store import ensure_bucket, minio_client_from_env
from fleet_rag.store.qdrant_store import qdrant_client_from_env
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker

FIXTURES_DIR = Path(__file__).resolve().parents[2].parent / "evals" / "fixtures" / "support_copilot"
BUCKET = "fleet-documents"


async def _collection_id(session_factory: async_sessionmaker[Any], name: str) -> int:
    async with session_factory() as session:
        row = (
            await session.execute(text("SELECT id FROM collections WHERE name = :n"), {"n": name})
        ).first()
        if row is None:
            raise RuntimeError(f"collection {name!r} not seeded — run `make seed` first")
        return int(row[0])


async def _upsert_document(
    session_factory: async_sessionmaker[Any], *, collection_id: int, uri: str, sha256: str
) -> int:
    async with session_factory() as session:
        existing = (
            await session.execute(
                text(
                    "SELECT id FROM documents WHERE collection_id = :c AND sha256 = :s"
                ),
                {"c": collection_id, "s": sha256},
            )
        ).first()
        if existing is not None:
            return int(existing[0])

        row = (
            await session.execute(
                text(
                    "INSERT INTO documents (collection_id, uri, sha256, status) "
                    "VALUES (:c, :u, :s, 'queued') RETURNING id"
                ),
                {"c": collection_id, "u": uri, "s": sha256},
            )
        ).first()
        await session.commit()
        assert row is not None
        return int(row[0])


async def seed_docs() -> None:
    session_factory = make_session_factory(get_engine())
    llm_client = await build_client()
    minio = minio_client_from_env()
    ensure_bucket(minio, BUCKET)
    qdrant_sink = _QdrantSinkAdapter(qdrant_client_from_env())

    # cs-help-center: general FAQ content. cs-procedures: internal SOP docs
    # (matches the department scenario's two-collection KB split).
    targets = {
        "trink-sat-process.txt": "cs-help-center",
        "membership-and-payments.txt": "cs-help-center",
        "listing-quality-sop.txt": "cs-procedures",
    }

    for filename, collection_name in targets.items():
        path = FIXTURES_DIR / filename
        data = path.read_bytes()
        sha256 = hashlib.sha256(data).hexdigest()
        collection_id = await _collection_id(session_factory, collection_name)
        object_key = f"{collection_id}/{filename}"

        minio.put_object(BUCKET, object_key, io.BytesIO(data), length=len(data))
        document_id = await _upsert_document(
            session_factory, collection_id=collection_id, uri=object_key, sha256=sha256
        )

        outcome = await ingest_document(
            {
                "session_factory": session_factory,
                "llm_client": llm_client,
                "minio_client": minio,
                "minio_bucket": BUCKET,
                "qdrant_sink": qdrant_sink,
            },
            document_id=document_id,
            collection_id=collection_id,
            object_key=object_key,
            filename=filename,
            sensitivity="internal",
            pii_policy="redact",
        )
        print(f"{filename} -> {collection_name}: {outcome['chunks_embedded']} chunks embedded")


def main() -> None:
    asyncio.run(seed_docs())


if __name__ == "__main__":
    main()
