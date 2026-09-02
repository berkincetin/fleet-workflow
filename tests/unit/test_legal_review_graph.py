"""agents.legal_review — the playbook-citation guardrail (task 12.2, dept
scenario 10).

Proves: a finding whose playbook_ref resolves to a retrieved excerpt is
reported with that excerpt's real chunk_ref; a finding citing an excerpt that
was never retrieved is moved to `uncited` instead of being surfaced as advice;
a risk level outside the closed vocabulary is rejected the same way; an empty
retrieval blocks rather than reporting a clean review; the review call runs on
the confidential (local) lane and the contract is quarantined, not concatenated.
"""

from __future__ import annotations

import json
from typing import Any

import pytest
from agents.legal_review.findings import (
    FindingsParseError,
    build_review,
    parse_findings,
)
from agents.legal_review.graph import build_legal_review_graph
from langgraph.checkpoint.memory import InMemorySaver

_EXCERPTS = [
    {
        "content": "Sorumluluk son 12 ayda ödenen bedelle sınırlandırılmalıdır.",
        "chunk_ref": "sha-a",
    },
    {"content": "Kişisel veri işlenen sözleşmelerde KVKK eki zorunludur.", "chunk_ref": "sha-b"},
]

_CONTRACT = "Madde 3 - Sorumluluk: Müşteri sınırsız olarak sorumludur."


class _FakeReasoning:
    def __init__(self, payload: Any) -> None:
        self._content = json.dumps(payload, ensure_ascii=False)
        self.sensitivities: list[str] = []
        self.messages: list[list[dict[str, Any]]] = []

    async def reasoning(self, messages: list[dict[str, Any]], **kwargs: Any) -> Any:
        self.sensitivities.append(kwargs.get("sensitivity", ""))
        self.messages.append(messages)

        class _Resp:
            content = self._content

        return _Resp()


class _FakePlaybooks:
    def __init__(self, excerpts: list[dict[str, str]]) -> None:
        self._excerpts = excerpts

    async def retrieve(self, *, query: str) -> list[dict[str, str]]:
        return list(self._excerpts)


def _build(payload: Any, *, excerpts: list[dict[str, str]] | None = None) -> tuple[Any, Any]:
    reasoning = _FakeReasoning(payload)
    graph = build_legal_review_graph(
        llm_client=reasoning,
        playbooks=_FakePlaybooks(_EXCERPTS if excerpts is None else excerpts),
        checkpointer=InMemorySaver(),
    )
    return graph, reasoning


_QUOTE = "Müşteri sınırsız olarak sorumludur"


async def test_cited_finding_carries_the_retrieved_chunk_ref() -> None:
    graph, _ = _build(
        {
            "findings": [
                {
                    "clause": "Sorumluluk",
                    "risk_level": "high",
                    "playbook_ref": 1,
                    "contract_excerpt": _QUOTE,
                    "rationale": "Sınırsız sorumluluk playbook'a aykırı.",
                }
            ]
        }
    )
    result = await graph.ainvoke(
        {"contract_text": _CONTRACT}, {"configurable": {"thread_id": "1"}}
    )
    assert result["findings"] == [
        {
            "clause": "Sorumluluk",
            "risk_level": "high",
            "playbook_ref": "sha-a",
            "contract_excerpt": _QUOTE,
            "rationale": "Sınırsız sorumluluk playbook'a aykırı.",
        }
    ]
    assert result["uncited"] == []


async def test_finding_citing_an_unretrieved_excerpt_is_not_surfaced_as_advice() -> None:
    graph, _ = _build(
        {
            "findings": [
                {
                    "clause": "Sorumluluk",
                    "risk_level": "high",
                    "playbook_ref": 1,
                    "contract_excerpt": _QUOTE,
                },
                # [playbook:9] was never shown — an invented citation.
                {
                    "clause": "Rekabet yasağı",
                    "risk_level": "high",
                    "playbook_ref": 9,
                    "contract_excerpt": _QUOTE,
                },
            ]
        }
    )
    result = await graph.ainvoke(
        {"contract_text": _CONTRACT}, {"configurable": {"thread_id": "2"}}
    )
    assert [f["clause"] for f in result["findings"]] == ["Sorumluluk"]
    assert [u["clause"] for u in result["uncited"]] == ["Rekabet yasağı"]


async def test_finding_quoting_text_absent_from_the_contract_is_not_surfaced() -> None:
    """The measured failure mode: the model restates a playbook prohibition as
    if it were a contract clause. The quote check catches exactly that."""
    graph, _ = _build(
        {
            "findings": [
                {
                    "clause": "Sorumluluk",
                    "risk_level": "high",
                    "playbook_ref": 1,
                    "contract_excerpt": "Sorumluluk sınırsızdır ve hiçbir üst limit yoktur",
                }
            ]
        }
    )
    result = await graph.ainvoke(
        {"contract_text": _CONTRACT}, {"configurable": {"thread_id": "2b"}}
    )
    assert result["findings"] == []
    assert result["uncited"][0]["reason"] == (
        "quoted clause does not appear in the contract under review"
    )


async def test_quote_matching_tolerates_line_wrapping_and_turkish_case() -> None:
    """A re-cased or re-wrapped quote still matches. Turkish case is the reason
    this needs its own fold: casefold("İ") is "i" plus a combining dot and
    casefold("I") is "i", not "ı", so a Turkish-uppercased quote would fail a
    plain casefold comparison and a valid finding would be dropped."""
    graph, _ = _build(
        {
            "findings": [
                {
                    "clause": "Sorumluluk",
                    "risk_level": "high",
                    "playbook_ref": 1,
                    "contract_excerpt": "MÜŞTERİ   sınırsız\n  olarak SORUMLUDUR",
                }
            ]
        }
    )
    result = await graph.ainvoke(
        {"contract_text": _CONTRACT}, {"configurable": {"thread_id": "2c"}}
    )
    assert len(result["findings"]) == 1


async def test_clause_the_model_marked_conforming_is_dropped_silently() -> None:
    """The measured failure mode this filter exists for: the model writes a
    rationale saying the clause does NOT meet the deviation criterion, then
    emits it as a high-risk finding anyway."""
    graph, _ = _build(
        {
            "findings": [
                {
                    "clause": "Fesih Hakkı",
                    "matches": "STANDART",
                    "risk_level": "high",
                    "playbook_ref": 1,
                    "contract_excerpt": _QUOTE,
                    "rationale": "Bu cümle SAPMA kriterini karşılamaz.",
                },
                {
                    "clause": "Sorumluluk",
                    "matches": "SAPMA",
                    "risk_level": "high",
                    "playbook_ref": 1,
                    "contract_excerpt": _QUOTE,
                },
            ]
        }
    )
    result = await graph.ainvoke(
        {"contract_text": _CONTRACT}, {"configurable": {"thread_id": "2d"}}
    )
    assert [f["clause"] for f in result["findings"]] == ["Sorumluluk"]
    # A conforming clause is not an error — it must not show up as uncited.
    assert result["uncited"] == []


async def test_missing_or_garbled_verdict_fails_toward_reporting() -> None:
    """A dropped finding is worse than a noisy one for a legal first pass, so
    anything that is not an explicit STANDART is kept."""
    for verdict in ({}, {"matches": ""}, {"matches": "sapma"}, {"matches": "belirsiz"}):
        review = build_review(
            [
                {
                    "clause": "Sorumluluk",
                    "risk_level": "high",
                    "playbook_ref": 1,
                    **verdict,
                }
            ],
            playbook_refs=["sha-a"],
        )
        assert len(review.findings) == 1, verdict


async def test_risk_level_outside_the_vocabulary_is_rejected() -> None:
    graph, _ = _build(
        {
            "findings": [
                {
                    "clause": "Fesih",
                    "risk_level": "catastrophic",
                    "playbook_ref": 1,
                    "contract_excerpt": _QUOTE,
                }
            ]
        }
    )
    result = await graph.ainvoke(
        {"contract_text": _CONTRACT}, {"configurable": {"thread_id": "3"}}
    )
    assert result["findings"] == []
    assert result["uncited"][0]["reason"] == "risk level outside the vocabulary"


async def test_empty_retrieval_blocks_instead_of_reporting_a_clean_contract() -> None:
    graph, reasoning = _build({"findings": []}, excerpts=[])
    result = await graph.ainvoke(
        {"contract_text": _CONTRACT}, {"configurable": {"thread_id": "4"}}
    )
    assert result["findings"] == []
    assert "no legal-playbooks excerpts" in result["blocked_reason"]
    # The model was never called: there was nothing to compare against.
    assert reasoning.sensitivities == []


async def test_review_runs_on_the_local_lane_with_quarantined_inputs() -> None:
    graph, reasoning = _build({"findings": []})
    await graph.ainvoke({"contract_text": _CONTRACT}, {"configurable": {"thread_id": "5"}})

    assert reasoning.sensitivities == ["confidential"]
    user_content = reasoning.messages[0][1]["content"]
    assert "<untrusted_context" in user_content
    # The contract text appears only inside a quarantine block.
    assert user_content.index(_CONTRACT) > user_content.index("<untrusted_context")


async def test_paused_agent_short_circuits() -> None:
    class _Paused:
        async def is_agent_paused(self, name: str) -> bool:
            return True

        async def blocks_tool(self, *, risk_class: str) -> bool:
            return False

    reasoning = _FakeReasoning({"findings": []})
    graph = build_legal_review_graph(
        llm_client=reasoning, playbooks=_FakePlaybooks(_EXCERPTS),
        checkpointer=InMemorySaver(), killswitch=_Paused(),
    )
    result = await graph.ainvoke(
        {"contract_text": _CONTRACT}, {"configurable": {"thread_id": "6"}}
    )
    assert result.get("paused") is True
    assert reasoning.sensitivities == []


# --- findings parsing / normalisation ----------------------------------------


def test_parse_accepts_a_bare_list_or_a_findings_object() -> None:
    payload = [{"clause": "A", "risk_level": "low", "playbook_ref": 1}]
    assert parse_findings(json.dumps(payload)) == payload
    assert parse_findings(json.dumps({"findings": payload})) == payload
    assert parse_findings(f"```json\n{json.dumps(payload)}\n```") == payload


def test_parse_rejects_non_json() -> None:
    with pytest.raises(FindingsParseError):
        parse_findings("I could not review this contract.")


def test_turkish_risk_words_map_onto_the_closed_vocabulary() -> None:
    review = build_review(
        [{"clause": "Sorumluluk", "risk_level": "Yüksek", "playbook_ref": "[playbook:1]"}],
        playbook_refs=["sha-a"],
    )
    assert review.findings[0].risk_level == "high"
    assert review.findings[0].playbook_ref == "sha-a"


def test_finding_without_a_clause_is_dropped_entirely() -> None:
    review = build_review(
        [{"clause": "  ", "risk_level": "high", "playbook_ref": 1}], playbook_refs=["sha-a"]
    )
    assert review.findings == []
    assert review.uncited == []
