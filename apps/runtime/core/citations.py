"""Generic citation carrier for the graph's citation-attach node (TRD §9, §11 messages.tool_trace).

Agent-specific grounding (e.g. RAG's structural check that every citation
resolves to a chunk actually retrieved that run) lives with the producing
tool — see fleet_rag.query.answer.build_answer. This module only carries
whatever citations a KB/tool node already produced onto the final response,
independent of which agent or tool produced them.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class Citation:
    source_id: str
    title: str
    chunk_ref: str


def attach_citations(response: dict[str, Any], citations: list[Citation]) -> dict[str, Any]:
    """Return a copy of response with a serialized citations list attached."""
    return {**response, "citations": [asdict(c) for c in citations]}
