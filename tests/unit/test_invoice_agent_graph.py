"""agents.invoice_agent.graph: image -> OCR -> extract -> validate -> HITL ->
draft ERP entry (task 6.3, dept scenario 04).

erp.create_draft_entry is write:external, so core.hitl.requires_approval
always returns True for it (TRD §9 "no exception") AND the department
scenario marks the whole rollout "approval-gated forever" — proven here by
the interrupt firing unconditionally, on both a clean and a mismatched
invoice (a validation failure does not skip the approval step; it still
reaches HITL, just carrying reasons for the approver to see).
"""

from __future__ import annotations

from typing import Any

from agents.invoice_agent.graph import build_invoice_agent_graph
from agents.invoice_agent.validator import PurchaseOrder
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command


class _FakeOcr:
    def __init__(self, text: str) -> None:
        self.text = text
        self.calls: list[str] = []

    async def extract_text(self, image_base64: str) -> dict[str, Any]:
        self.calls.append(image_base64)
        return {"text": self.text, "source": "vision-llm"}


class _FakeErp:
    def __init__(self) -> None:
        self.created: list[dict[str, Any]] = []

    async def create_draft_entry(
        self, *, vendor: str, po_number: str, amount: float, currency: str
    ) -> dict[str, Any]:
        entry = {
            "entry_id": "DRAFT-test", "vendor": vendor, "po_number": po_number,
            "amount": amount, "currency": currency, "status": "draft",
        }
        self.created.append(entry)
        return entry


class _FakePoLookup:
    def __init__(self, pos: dict[str, PurchaseOrder]) -> None:
        self.pos = pos

    async def lookup(self, po_number: str) -> PurchaseOrder | None:
        return self.pos.get(po_number)


_VALID_EXTRACTION_JSON = (
    '{"vendor": "Acme Tedarik A.S.", "po_number": "PO-1001", '
    '"amount": 1250.0, "currency": "TRY"}'
)


class _FakeLLM:
    def __init__(self, content: str = _VALID_EXTRACTION_JSON) -> None:
        self.content = content

    async def reasoning(self, messages: list[dict[str, Any]], **kwargs: Any) -> Any:
        class _Resp:
            content = self.content

        return _Resp()

    async def utility(self, messages: list[dict[str, Any]], **kwargs: Any) -> Any:
        raise AssertionError("invoice_agent graph must not call utility() for extraction")


def _matching_po_lookup() -> _FakePoLookup:
    return _FakePoLookup(
        {"PO-1001": PurchaseOrder(
            po_number="PO-1001", vendor="Acme Tedarik A.S.", amount=1250.0, currency="TRY",
        )}
    )


async def test_run_reaches_interrupt_before_creating_draft_entry() -> None:
    ocr = _FakeOcr("invoice text")
    erp = _FakeErp()
    graph = build_invoice_agent_graph(
        llm_client=_FakeLLM(), ocr=ocr, erp=erp, po_lookup=_matching_po_lookup(),
        checkpointer=InMemorySaver(),
    )
    config = {"configurable": {"thread_id": "i1"}}
    result = await graph.ainvoke({"image_base64": "eA=="}, config)

    assert "__interrupt__" in result
    assert ocr.calls == ["eA=="]
    assert erp.created == []  # not yet — waiting on approval


async def test_approve_resumes_and_creates_draft_entry() -> None:
    ocr = _FakeOcr("invoice text")
    erp = _FakeErp()
    checkpointer = InMemorySaver()
    config = {"configurable": {"thread_id": "i2"}}

    graph = build_invoice_agent_graph(
        llm_client=_FakeLLM(), ocr=ocr, erp=erp, po_lookup=_matching_po_lookup(),
        checkpointer=checkpointer,
    )
    await graph.ainvoke({"image_base64": "eA=="}, config)

    graph2 = build_invoice_agent_graph(
        llm_client=_FakeLLM(), ocr=ocr, erp=erp, po_lookup=_matching_po_lookup(),
        checkpointer=checkpointer,
    )
    result = await graph2.ainvoke(Command(resume={"approved": True}), config)

    assert "__interrupt__" not in result
    assert len(erp.created) == 1
    assert erp.created[0]["po_number"] == "PO-1001"
    assert erp.created[0]["status"] == "draft"


async def test_reject_cancels_cleanly_without_creating_draft_entry() -> None:
    ocr = _FakeOcr("invoice text")
    erp = _FakeErp()
    checkpointer = InMemorySaver()
    config = {"configurable": {"thread_id": "i3"}}

    graph = build_invoice_agent_graph(
        llm_client=_FakeLLM(), ocr=ocr, erp=erp, po_lookup=_matching_po_lookup(),
        checkpointer=checkpointer,
    )
    await graph.ainvoke({"image_base64": "eA=="}, config)

    graph2 = build_invoice_agent_graph(
        llm_client=_FakeLLM(), ocr=ocr, erp=erp, po_lookup=_matching_po_lookup(),
        checkpointer=checkpointer,
    )
    result = await graph2.ainvoke(Command(resume={"approved": False}), config)

    assert "__interrupt__" not in result
    assert result["rejected"] is True
    assert erp.created == []


async def test_amount_mismatch_still_reaches_interrupt_carrying_the_reason() -> None:
    """Dept scenario 04: mismatch must flag, never auto-draft as clean — but
    a mismatch still routes to the SAME approval queue, not a silent auto-
    reject; the approver sees the reason and decides."""
    ocr = _FakeOcr("invoice text")
    erp = _FakeErp()
    mismatched_po_lookup = _FakePoLookup(
        {"PO-1001": PurchaseOrder(
            po_number="PO-1001", vendor="Acme Tedarik A.S.", amount=99999.0, currency="TRY",
        )}
    )
    graph = build_invoice_agent_graph(
        llm_client=_FakeLLM(), ocr=ocr, erp=erp, po_lookup=mismatched_po_lookup,
        checkpointer=InMemorySaver(),
    )
    config = {"configurable": {"thread_id": "i4"}}
    result = await graph.ainvoke({"image_base64": "eA=="}, config)

    assert "__interrupt__" in result
    interrupt_payload = result["__interrupt__"][0].value
    assert interrupt_payload["validation"]["ok"] is False
    assert any("amount mismatch" in r for r in interrupt_payload["validation"]["reasons"])
    assert erp.created == []


async def test_duplicate_po_across_two_runs_in_the_same_batch_is_flagged() -> None:
    """Dept scenario 04's "duplicate invoice fixture -> flag" — proven across
    two separate graph invocations sharing one seen_po_numbers set, matching
    how a batch of invoices would be processed together (evals/live runs)."""
    ocr = _FakeOcr("invoice text")
    erp = _FakeErp()
    seen: set[str] = set()

    graph1 = build_invoice_agent_graph(
        llm_client=_FakeLLM(), ocr=ocr, erp=erp, po_lookup=_matching_po_lookup(),
        checkpointer=InMemorySaver(), seen_po_numbers=seen,
    )
    first = await graph1.ainvoke(
        {"image_base64": "eA=="}, {"configurable": {"thread_id": "i5a"}}
    )
    assert first["__interrupt__"][0].value["validation"]["ok"] is True

    graph2 = build_invoice_agent_graph(
        llm_client=_FakeLLM(), ocr=ocr, erp=erp, po_lookup=_matching_po_lookup(),
        checkpointer=InMemorySaver(), seen_po_numbers=seen,
    )
    second = await graph2.ainvoke(
        {"image_base64": "eA=="}, {"configurable": {"thread_id": "i5b"}}
    )
    validation = second["__interrupt__"][0].value["validation"]
    assert validation["ok"] is False
    assert any("duplicate" in r for r in validation["reasons"])


async def test_extraction_failure_blocks_before_reaching_hitl() -> None:
    ocr = _FakeOcr("garbled invoice text")
    erp = _FakeErp()
    graph = build_invoice_agent_graph(
        llm_client=_FakeLLM(content="not json"), ocr=ocr, erp=erp,
        po_lookup=_matching_po_lookup(), checkpointer=InMemorySaver(),
    )
    config = {"configurable": {"thread_id": "i6"}}
    result = await graph.ainvoke({"image_base64": "eA=="}, config)

    assert "__interrupt__" not in result
    assert result.get("blocked_reason") is not None
    assert erp.created == []
