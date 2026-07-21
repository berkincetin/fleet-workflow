"""core.citations: generic citation shape + attach helper (task 4.1).

Agent-specific grounding logic (the structural check that every citation
resolves to a chunk actually retrieved) lives in fleet_rag.query.answer for
the RAG case; this module is the generic carrier the graph's citation-attach
node uses to put whatever citations a KB/tool node produced onto the final
response, regardless of which agent or tool produced them.
"""

from __future__ import annotations

from core.citations import Citation, attach_citations


def test_attach_citations_adds_list_to_response() -> None:
    citations = [Citation(source_id="doc-1", title="Trink sat! SOP", chunk_ref="sha-abc")]
    response = attach_citations({"text": "answer text"}, citations)
    assert response["citations"] == [
        {"source_id": "doc-1", "title": "Trink sat! SOP", "chunk_ref": "sha-abc"}
    ]
    assert response["text"] == "answer text"


def test_attach_citations_empty_list_yields_empty_key() -> None:
    response = attach_citations({"text": "no sources"}, [])
    assert response["citations"] == []


def test_attach_citations_does_not_mutate_input_dict() -> None:
    original = {"text": "answer"}
    attach_citations(original, [Citation(source_id="x", title="y", chunk_ref="z")])
    assert "citations" not in original
