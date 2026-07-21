"""RAG query test harness (task 3.3): `/v1/rag/query`.

A chat-less endpoint that runs the full retrieval + grounded-answer pipeline
over a collection so the RAG stack can be exercised at the API level, ahead
of the chat UI (Sprint 4). Requires UPLOAD (same population that can browse
Knowledge). fleet_rag internals are wired here rather than imported at
module scope in fleet-api broadly, to keep the same avoid-circular-dependency
boundary used by routers/documents.py.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fleet_api.config import Settings, get_settings
from fleet_api.db import get_session
from fleet_api.models import Collection
from fleet_api.rbac import Permission, require_permission
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/v1/rag", tags=["rag"])


class CitationOut(BaseModel):
    chunk_ref: str
    document_id: int


class QueryIn(BaseModel):
    collection_id: int
    question: str
    top_k: int = Field(default=5, gt=0, le=50)
    keyword: str | None = None


class QueryOut(BaseModel):
    answer: str
    citations: list[CitationOut]
    degraded: bool


@router.post("/query")
async def query(
    body: QueryIn,
    _: object = Depends(require_permission(Permission.UPLOAD)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
    settings: Settings = Depends(get_settings),  # noqa: B008
) -> QueryOut:
    from core.llm.factory import build_client
    from fleet_rag.query.retrieve import Hit
    from fleet_rag.query.service import AgentQueryConfig, answer_query
    from fleet_rag.store.qdrant_store import collection_name, qdrant_client_from_env, search_hybrid

    collection = await session.get(Collection, body.collection_id)
    if collection is None:
        raise HTTPException(status_code=404, detail="collection not found")

    llm_client = await build_client()
    qdrant = qdrant_client_from_env()
    qname = collection_name(body.collection_id)

    def _searcher(
        *, query_vector: list[float], top_k: int, keyword: str | None = None
    ) -> list[Hit]:
        points = search_hybrid(
            qdrant, qname, query_vector=query_vector, top_k=top_k, keyword=keyword
        )
        return [
            Hit(
                id=str(p.id),
                score=p.score,
                document_id=p.payload["document_id"],
                chunk_ref=p.payload["content_sha256"],
                content=p.payload["content"],
                redacted=p.payload.get("redacted", False),
            )
            for p in points
        ]

    answer = await answer_query(
        question=body.question,
        searcher=_searcher,
        embed_client=llm_client,
        reasoning_client=llm_client,
        config=AgentQueryConfig(top_k=body.top_k),
        sensitivity=collection.sensitivity,
        keyword=body.keyword,
    )

    return QueryOut(
        answer=answer.text,
        citations=[
            CitationOut(chunk_ref=c.chunk_ref, document_id=c.document_id)
            for c in answer.citations
        ],
        degraded=answer.degraded,
    )
