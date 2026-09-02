"""Integration: Legal Document Review against the real dev stack (task 12.2 AC
— "planted-clause fixtures are all caught with a playbook citation").

The eval (`make eval AGENT=legal_review`) feeds the whole playbook as a fixed
excerpt list so a case's result depends only on the review. This test covers
what that deliberately leaves out: the RETRIEVAL half. It embeds a real contract
through the live gateway, searches the real `legal-playbooks` Qdrant collection,
and checks that the citation on each finding resolves to a chunk_ref that was
genuinely retrieved this run — the guardrail's whole premise.

It also pins the two lane properties the scenario is built on: the collection
is embedded and queried on the LOCAL lane (confidential ⇒ no cloud model is
cleared), and an empty retrieval blocks rather than reporting a clean review.
"""

from __future__ import annotations

import httpx
import pytest

KEYCLOAK_BASE = "http://localhost:8080"
API_DATABASE_URL = "postgresql+asyncpg://fleet:fleet_dev_pw@localhost:5432/fleet"

_PLANTED_CONTRACT = (
    "HIZMET SOZLESMESI\n\n"
    "Madde 1 - Konu: Tedarikci, Musteri'ye filo bakim hizmeti saglar.\n\n"
    "Madde 2 - Sure: Sozlesme 1 yil sureyle gecerlidir. Taraflar 30 gun once "
    "yazili bildirimle feshedebilir.\n\n"
    "Madde 3 - Sorumluluk: Musteri, Tedarikci'nin ugrayacagi her turlu zarardan "
    "sinirsiz olarak sorumludur. Bu sorumluluk icin herhangi bir ust limit "
    "uygulanmaz.\n\n"
    "Madde 4 - Uygulanacak Hukuk: Turk hukuku uygulanir, Istanbul mahkemeleri "
    "yetkilidir."
)


def _stack_up() -> bool:
    try:
        r = httpx.get(f"{KEYCLOAK_BASE}/realms/fleet/.well-known/openid-configuration", timeout=3)
        return r.status_code == 200
    except Exception:
        return False


pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(not _stack_up(), reason="dev stack not reachable — start with `make dev`"),
]


async def _collection_id(name: str) -> int:
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import create_async_engine

    engine = create_async_engine(API_DATABASE_URL)
    async with engine.connect() as conn:
        row = (
            await conn.execute(text("SELECT id FROM collections WHERE name = :n"), {"n": name})
        ).first()
    await engine.dispose()
    if row is None:
        raise AssertionError(f"{name} not seeded — run `make seed && make seed-docs`")
    return int(row[0])


async def test_planted_clause_is_caught_with_a_citation_that_really_was_retrieved() -> None:
    from agents.legal_review.graph import build_legal_review_graph
    from core.llm.factory import build_client
    from fleet_api.routers.legal_review import QdrantPlaybookRetriever
    from langgraph.checkpoint.memory import InMemorySaver

    llm_client = await build_client()
    playbooks = QdrantPlaybookRetriever(
        llm_client=llm_client, collection_id=await _collection_id("legal-playbooks"), top_k=15
    )

    # Retrieval must actually return playbook rules for this contract.
    excerpts = await playbooks.retrieve(query=_PLANTED_CONTRACT)
    assert excerpts, "legal-playbooks retrieval came back empty — run `make seed-docs`"
    retrieved_refs = {e["chunk_ref"] for e in excerpts}

    graph = build_legal_review_graph(
        llm_client=llm_client, playbooks=playbooks, checkpointer=InMemorySaver()
    )
    result = await graph.ainvoke(
        {"contract_text": _PLANTED_CONTRACT}, {"configurable": {"thread_id": "lr-e2e-1"}}
    )

    assert not result.get("blocked_reason"), result.get("blocked_reason")
    findings = result["findings"]
    assert findings, "the planted unlimited-liability clause was not caught"

    # Every surfaced finding is grounded in BOTH sources: a playbook excerpt
    # that was retrieved this run, and text that is really in the contract.
    for finding in findings:
        assert finding["playbook_ref"] in retrieved_refs
        assert finding["risk_level"] in ("high", "medium", "low")
        assert finding["contract_excerpt"]
        normalized = " ".join(finding["contract_excerpt"].split()).casefold()
        assert normalized in " ".join(_PLANTED_CONTRACT.split()).casefold()

    haystack = " ".join(
        f"{f['clause']} {f['contract_excerpt']} {f['rationale']}" for f in findings
    ).casefold()
    assert "sorumluluk" in haystack or "sinirsiz" in haystack


async def test_playbooks_are_embedded_and_queried_on_the_local_lane() -> None:
    """`legal-playbooks` is confidential/allow-local-only: both the ingest
    embedding and the query embedding must resolve to the local model, or the
    two would not even share a vector space."""
    from core.llm.factory import build_client
    from core.llm.routing import select_model

    llm_client = await build_client()
    embed_model = select_model(llm_client._models, role="embeddings", sensitivity="confidential")
    review_model = select_model(llm_client._models, role="reasoning", sensitivity="confidential")
    assert embed_model["provider"] == "ollama"
    assert review_model["provider"] == "ollama"


async def test_empty_retrieval_blocks_rather_than_reporting_a_clean_contract() -> None:
    """The dangerous failure mode for a legal first pass is a confident empty
    review. With no playbook retrieved there is nothing to compare against, so
    the run must block."""
    from agents.legal_review.graph import build_legal_review_graph
    from core.llm.factory import build_client
    from langgraph.checkpoint.memory import InMemorySaver

    class _EmptyPlaybooks:
        async def retrieve(self, *, query: str) -> list[dict[str, object]]:
            return []

    llm_client = await build_client()
    graph = build_legal_review_graph(
        llm_client=llm_client, playbooks=_EmptyPlaybooks(), checkpointer=InMemorySaver()
    )
    result = await graph.ainvoke(
        {"contract_text": _PLANTED_CONTRACT}, {"configurable": {"thread_id": "lr-e2e-2"}}
    )
    assert result["findings"] == []
    assert "no legal-playbooks excerpts" in result["blocked_reason"]
