"""Document upload API (task 3.1).

Uploads go straight to MinIO under a content-addressed key
(`{collection_id}/{sha256}{ext}`), the `documents` row is inserted (or
resolved if the exact same file was already uploaded into this collection —
the unique (collection_id, sha256) index makes re-upload idempotent, AC:
0 new embeddings), and an arq job is enqueued to run the ingestion pipeline
asynchronously. RBAC: UPLOAD permission (member and above, §7.1).
"""

from __future__ import annotations

import hashlib
import io

from arq import create_pool
from arq.connections import RedisSettings
from fastapi import APIRouter, Depends, HTTPException, UploadFile
from fleet_api.config import Settings, get_settings
from fleet_api.db import get_session
from fleet_api.models import Collection, Document
from fleet_api.rbac import Permission, require_permission
from minio import Minio
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/v1/documents", tags=["documents"])


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _object_key(*, collection_id: int, sha256: str, filename: str) -> str:
    # Mirrors fleet_rag.store.minio_store.object_key — kept in fleet-api to avoid a
    # circular workspace dependency (fleet-rag already depends on fleet-api).
    dot = filename.rfind(".")
    ext = filename[dot:].lower() if dot != -1 else ""
    return f"{collection_id}/{sha256}{ext}"


class DocumentOut(BaseModel):
    id: int
    collection_id: int
    uri: str
    sha256: str
    ocr_status: str
    status: str

    model_config = {"from_attributes": True}


def _minio_client(settings: Settings) -> Minio:
    return Minio(
        settings.minio_endpoint,
        access_key=settings.minio_root_user,
        secret_key=settings.minio_root_password,
        secure=settings.minio_secure,
    )


@router.post("", status_code=201)
async def upload_document(
    collection_id: int,
    file: UploadFile,
    _: object = Depends(require_permission(Permission.UPLOAD)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
    settings: Settings = Depends(get_settings),  # noqa: B008
) -> DocumentOut:
    collection = await session.get(Collection, collection_id)
    if collection is None:
        raise HTTPException(status_code=404, detail="collection not found")

    data = await file.read()
    digest = _sha256_bytes(data)
    filename = file.filename or "upload.bin"

    existing = (
        await session.execute(
            select(Document).where(
                Document.collection_id == collection_id, Document.sha256 == digest
            )
        )
    ).scalar_one_or_none()
    if existing is not None:
        # Re-upload of an already-ingested doc: 0 new embeddings (AC 3.1).
        return DocumentOut.model_validate(existing)

    key = _object_key(collection_id=collection_id, sha256=digest, filename=filename)
    client = _minio_client(settings)
    if not client.bucket_exists(settings.minio_bucket):
        client.make_bucket(settings.minio_bucket)
    client.put_object(settings.minio_bucket, key, io.BytesIO(data), length=len(data))

    row = Document(collection_id=collection_id, uri=key, sha256=digest, status="queued")
    session.add(row)
    await session.commit()
    await session.refresh(row)

    redis = await create_pool(RedisSettings.from_dsn(settings.ingest_redis_url))
    try:
        await redis.enqueue_job(
            "ingest_document",
            document_id=row.id,
            collection_id=collection_id,
            object_key=key,
            filename=filename,
            sensitivity=collection.sensitivity,
            pii_policy=collection.pii_policy,
        )
    finally:
        await redis.aclose()

    return DocumentOut.model_validate(row)


@router.get("")
async def list_documents(
    collection_id: int | None = None,
    _: object = Depends(require_permission(Permission.UPLOAD)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> list[DocumentOut]:
    query = select(Document).order_by(Document.id)
    if collection_id is not None:
        query = query.where(Document.collection_id == collection_id)
    rows = (await session.execute(query)).scalars().all()
    return [DocumentOut.model_validate(r) for r in rows]


@router.get("/{document_id}")
async def get_document(
    document_id: int,
    _: object = Depends(require_permission(Permission.UPLOAD)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> DocumentOut:
    row = await session.get(Document, document_id)
    if row is None:
        raise HTTPException(status_code=404, detail="document not found")
    return DocumentOut.model_validate(row)
