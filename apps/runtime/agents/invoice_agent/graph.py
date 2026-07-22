"""Invoice Agent graph: invoice image -> OCR -> extract fields -> validate
against PO -> approval queue -> draft ERP entry (task 6.3, dept scenario 04).

A dedicated LangGraph graph rather than core.graph.build_graph() — same
reasoning as Support Copilot (4.4) and Dev Agent (5.5): this is a fixed
linear pipeline, not the general single-tool-call ReAct loop core.graph is
built for.

Node order: killswitch_gate -> ocr (image bytes -> text, `read`) ->
extract_fields (reasoning call -> InvoiceFields) -> validate (mismatch/
duplicate/not-found against the PO fixture, never silently passes either) ->
hitl (interrupt() carrying the draft-entry payload; erp.create_draft_entry is
always write:external per TRD §9 AND "approval-gated forever" per the
department scenario's rollout note, so this fires unconditionally regardless
of the validation outcome — a clean-looking invoice still needs a human) ->
[rejected: END] / [approved: create_draft_entry].

Tool objects (OcrLike/ErpLike) are referenced only via local Protocols, not
imported from fleet_mcp — apps/runtime has no fleet-mcp workspace dependency
(same boundary agents.dev_agent.graph/agents.analytics.service already
established). The caller in apps/api passes the real fleet_mcp instances in.
"""

from __future__ import annotations

from typing import Any, Protocol, TypedDict

from agents.invoice_agent.extractor import (
    ExtractionParseError,
    InvoiceFields,
    ReasoningClient,
    extract_invoice_fields,
)
from agents.invoice_agent.validator import (
    GovernedPoLookup,
    ValidationResult,
    validate_invoice,
)
from core.hitl import requires_approval
from core.killswitch import KillSwitch
from langgraph.graph import END, StateGraph
from langgraph.types import interrupt


class OcrLike(Protocol):
    async def extract_text(self, image_base64: str) -> dict[str, Any]: ...


class ErpLike(Protocol):
    async def create_draft_entry(
        self, *, vendor: str, po_number: str, amount: float, currency: str
    ) -> dict[str, Any]: ...


class InvoiceAgentState(TypedDict, total=False):
    image_base64: str
    ocr_text: str
    fields: dict[str, Any]
    validation: dict[str, Any]
    blocked_reason: str | None
    rejected: bool
    paused: bool
    draft_entry: dict[str, Any]


_ERP_CREATE_DRAFT_ENTRY_RISK_CLASS = "write:external"


def build_invoice_agent_graph(
    *,
    llm_client: ReasoningClient,
    ocr: OcrLike,
    erp: ErpLike,
    po_lookup: GovernedPoLookup,
    checkpointer: Any,
    seen_po_numbers: set[str] | None = None,
    killswitch: KillSwitch | None = None,
    agent_name: str = "invoice_agent",
) -> Any:
    # A fresh, empty set per graph build unless the caller passes a shared one
    # (evals/live runs across a batch want duplicates detected across the
    # whole run; a single ad hoc invocation is fine starting empty).
    seen: set[str] = seen_po_numbers if seen_po_numbers is not None else set()

    async def killswitch_gate(state: InvoiceAgentState) -> dict[str, Any]:
        if killswitch is not None and await killswitch.is_agent_paused(agent_name):
            return {"paused": True}
        return {}

    def route_after_killswitch(state: InvoiceAgentState) -> str:
        return END if state.get("paused") else "ocr"

    async def ocr_node(state: InvoiceAgentState) -> dict[str, Any]:
        result = await ocr.extract_text(image_base64=state["image_base64"])
        return {"ocr_text": result["text"]}

    async def extract_fields(state: InvoiceAgentState) -> dict[str, Any]:
        try:
            fields = await extract_invoice_fields(
                ocr_text=state["ocr_text"], llm_client=llm_client
            )
        except ExtractionParseError as exc:
            return {"blocked_reason": f"field extraction failed: {exc}"}
        return {
            "fields": {
                "vendor": fields.vendor,
                "po_number": fields.po_number,
                "amount": fields.amount,
                "currency": fields.currency,
            }
        }

    def route_after_extract(state: InvoiceAgentState) -> str:
        return "end" if state.get("blocked_reason") else "validate"

    async def validate(state: InvoiceAgentState) -> dict[str, Any]:
        f = state["fields"]
        fields = InvoiceFields(
            vendor=f["vendor"], po_number=f["po_number"], amount=f["amount"],
            currency=f["currency"],
        )
        result: ValidationResult = await validate_invoice(
            fields, po_lookup=po_lookup, seen_po_numbers=seen
        )
        seen.add(fields.po_number)
        po = result.purchase_order
        return {
            "validation": {
                "ok": result.ok,
                "reasons": result.reasons,
                "purchase_order": (
                    {
                        "po_number": po.po_number, "vendor": po.vendor,
                        "amount": po.amount, "currency": po.currency,
                    }
                    if po is not None
                    else None
                ),
            }
        }

    async def hitl(state: InvoiceAgentState) -> dict[str, Any]:
        # erp.create_draft_entry is always write:external (TRD §9) AND the
        # department scenario marks the whole rollout "approval-gated
        # forever" — requires_approval is called for symmetry/auditability
        # with the rest of the codebase's HITL decision points, but for this
        # risk_class there is no autonomy path to short-circuit into, same
        # as agents.dev_agent.graph's hitl node.
        assert requires_approval(
            risk_class=_ERP_CREATE_DRAFT_ENTRY_RISK_CLASS, eval_pass_rate=0.0,
            autonomy_enabled=False,
        )
        decision = interrupt(
            {
                "tool": "erp.create_draft_entry",
                "risk_class": _ERP_CREATE_DRAFT_ENTRY_RISK_CLASS,
                "args": state["fields"],
                "validation": state["validation"],
            }
        )
        if not decision.get("approved"):
            return {"rejected": True}
        return {}

    def route_after_hitl(state: InvoiceAgentState) -> str:
        return "end" if state.get("rejected") else "create_draft_entry"

    async def create_draft_entry(state: InvoiceAgentState) -> dict[str, Any]:
        f = state["fields"]
        entry = await erp.create_draft_entry(
            vendor=f["vendor"], po_number=f["po_number"], amount=f["amount"],
            currency=f["currency"],
        )
        return {"draft_entry": entry}

    async def end_node(state: InvoiceAgentState) -> dict[str, Any]:
        return {}

    graph = StateGraph(InvoiceAgentState)
    graph.add_node("killswitch_gate", killswitch_gate)
    graph.add_node("ocr", ocr_node)
    graph.add_node("extract_fields", extract_fields)
    graph.add_node("validate", validate)
    graph.add_node("hitl", hitl)
    graph.add_node("create_draft_entry", create_draft_entry)
    graph.add_node("end", end_node)

    graph.set_entry_point("killswitch_gate")
    graph.add_conditional_edges(
        "killswitch_gate", route_after_killswitch, {END: END, "ocr": "ocr"}
    )
    graph.add_edge("ocr", "extract_fields")
    graph.add_conditional_edges(
        "extract_fields", route_after_extract, {"validate": "validate", "end": "end"}
    )
    graph.add_edge("validate", "hitl")
    graph.add_conditional_edges(
        "hitl", route_after_hitl,
        {"create_draft_entry": "create_draft_entry", "end": "end"},
    )
    graph.add_edge("create_draft_entry", "end")
    graph.add_edge("end", END)

    return graph.compile(checkpointer=checkpointer)
