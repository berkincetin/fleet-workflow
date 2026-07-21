"""Grounding guardrail (task 3.3, TRD §9 structural check):

Every RAG answer must carry >=1 citation, and every citation must resolve to
a chunk actually retrieved in that run. A first-pass answer failing this is
regenerated once; if the retry still fails, the answer degrades to a fixed
"I don't know" response rather than ever returning an ungrounded claim.

Citations from the generator are 1-indexed positions into the retrieved hits
list (see answer.py's module docstring for why).
"""

from __future__ import annotations

from fleet_rag.query.answer import DEGRADED_ANSWER, Answer, Citation, build_answer
from fleet_rag.query.retrieve import Hit


def _hit(chunk_ref: str, content: str = "some text") -> Hit:
    return Hit(
        id=f"pt-{chunk_ref}", score=0.9, document_id=1, chunk_ref=chunk_ref,
        content=content, redacted=False,
    )


class _FakeGenerator:
    """Returns queued (text, citation_positions) pairs, one per call."""

    def __init__(self, responses: list[tuple[str, list[int]]]) -> None:
        self._responses = list(responses)
        self.calls = 0

    async def __call__(self, *, question, hits):  # type: ignore[no-untyped-def]
        self.calls += 1
        text, positions = self._responses.pop(0)
        return text, positions


async def test_valid_first_pass_answer_is_returned_as_is() -> None:
    hits = [_hit("sha-1"), _hit("sha-2")]
    gen = _FakeGenerator([("Answer citing chunk 1.", [1])])
    answer = await build_answer(question="q?", hits=hits, generate=gen)
    assert isinstance(answer, Answer)
    assert answer.text == "Answer citing chunk 1."
    assert answer.citations == [Citation(chunk_ref="sha-1", document_id=1)]
    assert gen.calls == 1


async def test_answer_with_no_citations_is_regenerated_once() -> None:
    hits = [_hit("sha-1")]
    gen = _FakeGenerator([
        ("No citation here.", []),
        ("Retry with citation.", [1]),
    ])
    answer = await build_answer(question="q?", hits=hits, generate=gen)
    assert answer.text == "Retry with citation."
    assert gen.calls == 2


async def test_citation_to_out_of_range_position_triggers_regeneration() -> None:
    hits = [_hit("sha-1")]
    gen = _FakeGenerator([
        ("Cites a position never retrieved.", [999]),
        ("Cites the real chunk.", [1]),
    ])
    answer = await build_answer(question="q?", hits=hits, generate=gen)
    assert answer.text == "Cites the real chunk."
    assert answer.degraded is False


async def test_second_failure_degrades_to_i_dont_know() -> None:
    hits = [_hit("sha-1")]
    gen = _FakeGenerator([
        ("First try, no citation.", []),
        ("Second try, still no citation.", []),
    ])
    answer = await build_answer(question="q?", hits=hits, generate=gen)
    assert answer.text == DEGRADED_ANSWER
    assert answer.degraded is True
    assert answer.citations == []
    assert gen.calls == 2


async def test_no_hits_at_all_degrades_without_calling_generate() -> None:
    gen = _FakeGenerator([])
    answer = await build_answer(question="q?", hits=[], generate=gen)
    assert answer.degraded is True
    assert answer.text == DEGRADED_ANSWER
    assert gen.calls == 0
