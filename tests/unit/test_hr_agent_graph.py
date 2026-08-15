"""agents.hr_agent.graph: image -> OCR -> extract profile -> match role ->
HITL shortlist draft (task 8.5, dept scenario 05).

hr.shortlist_draft is write:internal with autonomy hardcoded off (dept
scenario 05's rollout note: "shortlist = assist only (HR decides)") — proven
here by the interrupt firing unconditionally, on both a strong and a weak
match (a low match score does not skip the approval step; the approver sees
the reasoning and decides, same shape as invoice_agent's mismatch case).
"""

from __future__ import annotations

from typing import Any

from agents.hr_agent.graph import build_hr_agent_graph
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command


class _FakeOcr:
    def __init__(self, text: str) -> None:
        self.text = text
        self.calls: list[str] = []

    async def extract_text(self, image_base64: str) -> dict[str, Any]:
        self.calls.append(image_base64)
        return {"text": self.text, "source": "tesseract"}


_VALID_PROFILE_JSON = (
    '{"full_name": "Ayse Yilmaz", "email": "ayse@example.com", "phone": "555", '
    '"education": ["BSc Computer Engineering, ODTU"], '
    '"experience": ["Software Engineer, Acme A.S."], '
    '"skills": ["Python", "SQL"]}'
)


class _FakeLLM:
    def __init__(self, content: str = _VALID_PROFILE_JSON) -> None:
        self.content = content
        self.calls: list[dict[str, object]] = []

    async def reasoning(self, messages: list[dict[str, Any]], **kwargs: Any) -> Any:
        self.calls.append(kwargs)

        class _Resp:
            content = self.content

        return _Resp()


async def test_run_reaches_interrupt_with_match_result() -> None:
    ocr = _FakeOcr("cv text")
    graph = build_hr_agent_graph(llm_client=_FakeLLM(), ocr=ocr, checkpointer=InMemorySaver())
    config = {"configurable": {"thread_id": "h1"}}
    result = await graph.ainvoke(
        {"image_base64": "eA==", "criteria": ["Python", "SQL"]}, config
    )

    assert "__interrupt__" in result
    assert ocr.calls == ["eA=="]
    payload = result["__interrupt__"][0].value
    assert payload["tool"] == "hr.shortlist_draft"
    assert payload["risk_class"] == "write:internal"
    assert payload["match"]["score"] == 1.0
    assert payload["args"]["full_name"] == "Ayse Yilmaz"


async def test_weak_match_still_reaches_interrupt_carrying_the_reason() -> None:
    """A candidate missing most criteria still routes to the SAME approval
    queue, not a silent auto-reject — HR sees the reasoning and decides."""
    ocr = _FakeOcr("cv text")
    graph = build_hr_agent_graph(llm_client=_FakeLLM(), ocr=ocr, checkpointer=InMemorySaver())
    config = {"configurable": {"thread_id": "h2"}}
    result = await graph.ainvoke(
        {"image_base64": "eA==", "criteria": ["Rust", "Kubernetes", "Go"]}, config
    )

    assert "__interrupt__" in result
    match = result["__interrupt__"][0].value["match"]
    assert match["score"] == 0.0
    assert "Rust" in match["missing_criteria"]


async def test_approve_resumes_cleanly() -> None:
    ocr = _FakeOcr("cv text")
    checkpointer = InMemorySaver()
    config = {"configurable": {"thread_id": "h3"}}

    graph = build_hr_agent_graph(llm_client=_FakeLLM(), ocr=ocr, checkpointer=checkpointer)
    await graph.ainvoke({"image_base64": "eA==", "criteria": ["Python"]}, config)

    graph2 = build_hr_agent_graph(llm_client=_FakeLLM(), ocr=ocr, checkpointer=checkpointer)
    result = await graph2.ainvoke(Command(resume={"approved": True}), config)

    assert "__interrupt__" not in result
    assert result.get("rejected") is not True


async def test_reject_cancels_cleanly() -> None:
    ocr = _FakeOcr("cv text")
    checkpointer = InMemorySaver()
    config = {"configurable": {"thread_id": "h4"}}

    graph = build_hr_agent_graph(llm_client=_FakeLLM(), ocr=ocr, checkpointer=checkpointer)
    await graph.ainvoke({"image_base64": "eA==", "criteria": ["Python"]}, config)

    graph2 = build_hr_agent_graph(llm_client=_FakeLLM(), ocr=ocr, checkpointer=checkpointer)
    result = await graph2.ainvoke(Command(resume={"approved": False}), config)

    assert "__interrupt__" not in result
    assert result["rejected"] is True


async def test_extraction_failure_blocks_before_reaching_hitl() -> None:
    ocr = _FakeOcr("garbled cv text")
    graph = build_hr_agent_graph(
        llm_client=_FakeLLM(content="not json"), ocr=ocr, checkpointer=InMemorySaver()
    )
    config = {"configurable": {"thread_id": "h5"}}
    result = await graph.ainvoke({"image_base64": "eA==", "criteria": ["Python"]}, config)

    assert "__interrupt__" not in result
    assert result.get("blocked_reason") is not None


async def test_extraction_call_always_uses_pii_sensitivity() -> None:
    """dept scenario 05: pii lane, reasoning stays local for CV content —
    reasserted at the graph level, not just the extractor's own unit test."""
    ocr = _FakeOcr("cv text")
    llm = _FakeLLM()
    graph = build_hr_agent_graph(llm_client=llm, ocr=ocr, checkpointer=InMemorySaver())
    config = {"configurable": {"thread_id": "h6"}}
    await graph.ainvoke({"image_base64": "eA==", "criteria": ["Python"]}, config)

    assert llm.calls[0]["sensitivity"] == "pii"
