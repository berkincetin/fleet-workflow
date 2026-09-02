"""Legal Document Review run trigger (task 12.2, dept scenario 10).

`POST /v1/legal-review/runs` runs a first-pass contract review: retrieve the
`legal-playbooks` excerpts most relevant to the contract (local embeddings —
the collection is confidential/allow-local-only), then extract deviating
clauses on the local lane and return only findings whose playbook reference
resolves to a retrieved excerpt.

Advisory only: the agent has no tools and no approval interrupt (dept scenario
10's rollout is "assist permanently"), so a run either `completed` with a cited
review or `blocked` — there is no external side effect either way and no
checkpointer-resumable state.

Requires MANAGE_AGENTS (Legal's own reviewers are dept_admins on this agent);
there is no service-scope path because nothing automates contract intake yet.
"""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fleet_api.db import get_session
from fleet_api.models import Agent, Collection
from fleet_api.rbac import Permission, require_permission
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/v1/legal-review", tags=["legal-review"])

LEGAL_REVIEW_AGENT_NAME = "legal_review"
LEGAL_PLAYBOOKS_COLLECTION = "legal-playbooks"


class RunIn(BaseModel):
    contract_text: str = Field(min_length=1)
    # Default 15, not the usual 5: `legal-playbooks` is one document per rule,
    # and a contract routinely breaches rules from several of them at once
    # (liability + KVKK + jurisdiction). Retrieving only the top 5 would decide
    # in advance which kinds of risk the review is allowed to find. The rule
    # set is small enough that pulling all of it stays well inside the context
    # budget.
    top_k: int = Field(default=15, gt=0, le=50)


class FindingOut(BaseModel):
    clause: str
    risk_level: str
    playbook_ref: str
    contract_excerpt: str = ""
    rationale: str = ""


class RunOut(BaseModel):
    run_id: str
    status: str  # "completed" | "blocked"
    findings: list[FindingOut] = []
    uncited: list[dict[str, Any]] = []
    detail: dict[str, Any] = {}


class QdrantPlaybookRetriever:
    """`legal-playbooks` retrieval on the local lane.

    Embeds the contract at `confidential`, which routing resolves to the local
    embedding model — the same model the collection was ingested with, so the
    vectors are dimensionally compatible and the contract text never leaves the
    machine on its way to becoming a query vector.
    """

    def __init__(self, *, llm_client: Any, collection_id: int, top_k: int = 15) -> None:
        self._llm_client = llm_client
        self._collection_id = collection_id
        self._top_k = top_k

    async def retrieve(self, *, query: str) -> list[dict[str, Any]]:
        from fleet_rag.query.retrieve import Hit, RetrievalConfig, retrieve
        from fleet_rag.store.qdrant_store import (
            collection_name,
            qdrant_client_from_env,
            search_hybrid,
        )

        embed_response = await self._llm_client.embeddings(
            [query], sensitivity="confidential"
        )
        query_vector = embed_response.vectors[0]

        qdrant = qdrant_client_from_env()
        qname = collection_name(self._collection_id)

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

        hits = await retrieve(
            _searcher,
            query_vector=query_vector,
            config=RetrievalConfig(top_k=self._top_k),
        )
        return [{"content": h.content, "chunk_ref": h.chunk_ref} for h in hits]


@router.post("/runs", status_code=201)
async def start_run(
    body: RunIn,
    _: object = Depends(require_permission(Permission.MANAGE_AGENTS)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> RunOut:
    from agents.legal_review.graph import build_legal_review_graph
    from core.llm.factory import build_client
    from langgraph.checkpoint.memory import InMemorySaver

    agent_row = (
        await session.execute(select(Agent).where(Agent.name == LEGAL_REVIEW_AGENT_NAME))
    ).scalar_one_or_none()
    if agent_row is None:
        raise HTTPException(
            status_code=500, detail="legal_review not seeded — run `make seed`"
        )
    collection_row = (
        await session.execute(
            select(Collection).where(Collection.name == LEGAL_PLAYBOOKS_COLLECTION)
        )
    ).scalar_one_or_none()
    if collection_row is None:
        raise HTTPException(
            status_code=500,
            detail=f"{LEGAL_PLAYBOOKS_COLLECTION} collection not seeded — run `make seed`",
        )

    llm_client = await build_client()
    playbooks = QdrantPlaybookRetriever(
        llm_client=llm_client, collection_id=collection_row.id, top_k=body.top_k
    )

    run_id = str(uuid.uuid4())
    # InMemorySaver, not the Postgres checkpointer: this graph has no interrupt,
    # so there is no run to resume later and nothing to persist between calls.
    graph = build_legal_review_graph(
        llm_client=llm_client, playbooks=playbooks, checkpointer=InMemorySaver()
    )
    result = await graph.ainvoke(
        {"contract_text": body.contract_text}, {"configurable": {"thread_id": run_id}}
    )

    if result.get("blocked_reason"):
        return RunOut(
            run_id=run_id, status="blocked", detail={"reason": result["blocked_reason"]}
        )

    return RunOut(
        run_id=run_id,
        status="completed",
        findings=[FindingOut(**f) for f in result.get("findings", [])],
        uncited=result.get("uncited", []),
        detail={"excerpts_retrieved": len(result.get("excerpts", []))},
    )
