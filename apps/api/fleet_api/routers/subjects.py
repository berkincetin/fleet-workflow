"""Right to erasure (task 8.3, TRD §8: "DELETE /v1/subjects/{hash} erases a
person's conversations/uploads (right to erasure); audit rows are kept but
pseudonymized").

`{hash}` is a `fleet_api.privacy.subject_hash(...)` value, never a raw
identifier — callers compute it themselves from whatever stable identifier
they hold (a Keycloak `kc_sub` for a platform user, a candidate's email for
an HR CV subject who is never a Keycloak user at all, task 8.5) and pass the
hash, so this endpoint (and its URL, which lands in access logs) never
receives or stores PII directly.

Erasure covers two independent, non-exclusive matches:
- `conversations.subject_hash == hash` (+ their messages) — a platform user's
  chat history.
- `documents.subject_hash == hash` (+ chunks/MinIO object/Qdrant vectors, via
  the same `delete_document_fully` the retention purge job uses, task 3.2) —
  person-linked uploads such as HR CVs.

`audit_log` rows are never deleted (append-only, TRD §8) — any row whose
`actor` is the erased user's `kc_sub` has `actor` overwritten with a fixed
pseudonym, keeping the row (and its trace_id/action/entity) for audit
continuity without retaining an identifier for that person. There is no
`kc_sub_hash` column to look this up by SQL directly, so the (small,
infrequently-queried) `users` table is scanned in Python — acceptable for an
admin-triggered, low-traffic endpoint, not a hot path. MANAGE_PLATFORM-gated,
the same tier as the other admin-only destructive/PII-adjacent endpoints
(users_admin, budgets_admin).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from fleet_api.config import Settings, get_settings
from fleet_api.db import get_engine, get_session
from fleet_api.db import session_factory as make_session_factory
from fleet_api.models import AuditLog, Conversation, Document, User
from fleet_api.privacy import subject_hash
from fleet_api.rbac import Permission, require_permission
from minio import Minio
from pydantic import BaseModel
from sqlalchemy import select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/v1/subjects", tags=["subjects"])

_PSEUDONYM_PREFIX = "erased-subject:"


class ErasureResult(BaseModel):
    subject_hash: str
    conversations_deleted: int
    messages_deleted: int
    documents_deleted: int
    audit_rows_pseudonymized: int


def _minio_client(settings: Settings) -> Minio:
    return Minio(
        settings.minio_endpoint,
        access_key=settings.minio_root_user,
        secret_key=settings.minio_root_password,
        secure=settings.minio_secure,
    )


async def _delete_conversations(session: AsyncSession, *, hash_: str) -> tuple[int, int]:
    conv_ids = (
        await session.execute(select(Conversation.id).where(Conversation.subject_hash == hash_))
    ).scalars().all()
    messages_deleted = 0
    for conv_id in conv_ids:
        result = await session.execute(
            text("DELETE FROM messages WHERE conv_id = :c"), {"c": conv_id}
        )
        # CursorResult.rowcount exists at runtime for a DELETE; mypy's Result[Any]
        # stub (from a raw text() execute) doesn't expose it.
        messages_deleted += result.rowcount or 0  # type: ignore[attr-defined]
    if conv_ids:
        await session.execute(
            text("DELETE FROM conversations WHERE subject_hash = :h"), {"h": hash_}
        )
    await session.commit()
    return len(conv_ids), messages_deleted


async def _delete_documents(
    session: AsyncSession, *, hash_: str, minio: Minio, bucket: str
) -> int:
    from fleet_rag.ingest.retention import delete_document_fully
    from fleet_rag.store.qdrant_store import delete_by_document, qdrant_client_from_env

    class _VectorAdapter:
        def delete_by_document(self, collection_name: str, *, document_id: int) -> None:
            delete_by_document(qdrant_client_from_env(), collection_name, document_id=document_id)

    doc_rows = (
        await session.execute(
            select(Document.id, Document.collection_id, Document.uri).where(
                Document.subject_hash == hash_
            )
        )
    ).all()
    session_factory = make_session_factory(get_engine())
    for document_id, collection_id, uri in doc_rows:
        await delete_document_fully(
            session_factory,
            document_id=document_id, collection_id=collection_id, uri=uri,
            object_store=minio, vector_store=_VectorAdapter(), bucket=bucket,
        )
    return len(doc_rows)


async def _pseudonymize_audit_rows(session: AsyncSession, *, hash_: str) -> int:
    users = (await session.execute(select(User).where(User.kc_sub != ""))).scalars().all()
    matching_kc_sub = next((u.kc_sub for u in users if subject_hash(u.kc_sub) == hash_), None)
    if matching_kc_sub is None:
        return 0
    result = await session.execute(
        update(AuditLog)
        .where(AuditLog.actor == matching_kc_sub)
        .values(actor=f"{_PSEUDONYM_PREFIX}{hash_[:16]}")
    )
    await session.commit()
    return result.rowcount or 0  # type: ignore[attr-defined]


@router.delete("/{hash_}")
async def erase_subject(
    hash_: str,
    _: object = Depends(require_permission(Permission.MANAGE_PLATFORM)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
    settings: Settings = Depends(get_settings),  # noqa: B008
) -> ErasureResult:
    conversations_deleted, messages_deleted = await _delete_conversations(session, hash_=hash_)
    documents_deleted = await _delete_documents(
        session, hash_=hash_, minio=_minio_client(settings), bucket=settings.minio_bucket
    )
    audit_rows_pseudonymized = await _pseudonymize_audit_rows(session, hash_=hash_)

    return ErasureResult(
        subject_hash=hash_,
        conversations_deleted=conversations_deleted,
        messages_deleted=messages_deleted,
        documents_deleted=documents_deleted,
        audit_rows_pseudonymized=audit_rows_pseudonymized,
    )
