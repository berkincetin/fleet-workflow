"""Dealer Onboarding agent graph (task 12.1, dept scenario 09).

Node order: killswitch_gate -> fetch_application (crm.get_application, read,
INTEGRATION-POINT) -> ocr (LOCAL OCR of every supplied document) -> extract
(LOCAL pii-lane extraction of company name / tax no / IBAN — never redacted,
never cloud) -> crosscheck (deterministic: missing documents, unreadable
required fields, certificate-vs-application name mismatch) -> one of three
terminal paths:

* **mismatch** -> `flag`: crm.update_status("manual_review"), write:internal,
  and **no email at all**. A dossier whose certificate names a different company
  than the application is a fraud/typo signal; the applicant is never written to
  on the agent's own initiative, a human looks first.
* **incomplete** -> `compose_email` -> `hitl` -> `send_email` + `flag_awaiting`:
  the missing-document request is email.send, **write:external**, so it stops at
  the approval interrupt. Nothing is sent, and the application's status is not
  touched, unless a human approves. This is the scenario's first-month rollout
  mode ("approval on all outbound email"); the supervised template auto-send it
  graduates to is a later autonomy decision, not a branch that exists here.
* **clean** -> `handoff`: crm.update_status("ready_for_sales"), write:internal.

Sensitivity is `pii` end to end: the OCR is local, and the extraction call is
made at sensitivity="pii", which core.llm.routing never downgrades — so no cloud
model is eligible for the document text. The only cloud-eligible content in the
scenario would be orchestration prose, and the outbound email is rendered from a
fixed template instead (see email_template.py), so this agent makes exactly one
LLM call and it is on the local lane.

Tools are referenced via local Protocols; apps/runtime has no fleet-mcp
dependency (same boundary as invoice_agent/vehicle_intake).
"""

from __future__ import annotations

from typing import Any, Protocol, TypedDict

from agents.dealer_onboarding.crosscheck import CrossCheck, cross_check
from agents.dealer_onboarding.email_template import render_missing_docs_email
from agents.dealer_onboarding.extractor import (
    DealerDossier,
    ExtractionParseError,
    ReasoningClient,
    extract_dealer_dossier,
)
from core.hitl import requires_approval
from core.killswitch import KillSwitch
from langgraph.graph import END, StateGraph
from langgraph.types import interrupt


class OcrLike(Protocol):
    async def extract_text(self, image_base64: str) -> dict[str, Any]: ...


class CrmLike(Protocol):
    async def get_application(self, *, application_id: str) -> dict[str, Any]: ...
    async def update_status(
        self, *, application_id: str, status: str, note: str | None = None
    ) -> dict[str, Any]: ...


class EmailLike(Protocol):
    async def send(self, to: str, subject: str, body: str) -> Any: ...


class DealerOnboardingState(TypedDict, total=False):
    application_id: str
    # [{"kind": "authorization_certificate", "image_base64": "..."}, ...]
    documents: list[dict[str, str]]
    application: dict[str, Any]
    ocr_text: str
    dossier: dict[str, Any]
    check: dict[str, Any]
    email: dict[str, Any]
    email_sent: dict[str, Any] | None
    status_update: dict[str, Any] | None
    blocked_reason: str | None
    rejected: bool
    paused: bool


_EMAIL_RISK_CLASS = "write:external"


def build_dealer_onboarding_graph(
    *,
    llm_client: ReasoningClient,
    ocr: OcrLike,
    crm: CrmLike,
    email: EmailLike,
    checkpointer: Any,
    killswitch: KillSwitch | None = None,
    agent_name: str = "dealer_onboarding",
) -> Any:
    async def killswitch_gate(state: DealerOnboardingState) -> dict[str, Any]:
        if killswitch is not None and await killswitch.is_agent_paused(agent_name):
            return {"paused": True}
        return {}

    def route_after_killswitch(state: DealerOnboardingState) -> str:
        return END if state.get("paused") else "fetch_application"

    async def fetch_application(state: DealerOnboardingState) -> dict[str, Any]:
        application = await crm.get_application(application_id=state["application_id"])
        return {"application": application}

    async def ocr_node(state: DealerOnboardingState) -> dict[str, Any]:
        # LOCAL OCR: the certificate and the tax registration carry the dealer's
        # tax number and IBAN (TRD §8), so the images never reach a cloud model.
        texts: list[str] = []
        for document in state.get("documents", []):
            result = await ocr.extract_text(image_base64=document["image_base64"])
            texts.append(f"[{document['kind']}]\n{result['text']}")
        return {"ocr_text": "\n\n".join(texts)}

    async def extract(state: DealerOnboardingState) -> dict[str, Any]:
        if not state.get("ocr_text", "").strip():
            # No readable document at all — nothing to extract; the crosscheck
            # will report every required document as missing.
            return {
                "dossier": {
                    "company_name": None, "tax_no": None, "iban": None,
                    "certificate_no": None, "missing_fields": ["company_name", "tax_no"],
                }
            }
        try:
            dossier: DealerDossier = await extract_dealer_dossier(
                ocr_text=state["ocr_text"], llm_client=llm_client
            )
        except ExtractionParseError as exc:
            return {"blocked_reason": f"dealer dossier extraction failed: {exc}"}
        return {
            "dossier": {
                "company_name": dossier.company_name,
                "tax_no": dossier.tax_no,
                "iban": dossier.iban,
                "certificate_no": dossier.certificate_no,
                "missing_fields": dossier.missing_fields,
            }
        }

    def route_after_extract(state: DealerOnboardingState) -> str:
        return "end" if state.get("blocked_reason") else "crosscheck"

    async def crosscheck_node(state: DealerOnboardingState) -> dict[str, Any]:
        dossier = state["dossier"]
        check = cross_check(
            application=state.get("application", {}),
            provided_documents=[d["kind"] for d in state.get("documents", [])],
            certificate_name=dossier.get("company_name"),
            missing_fields=list(dossier.get("missing_fields", [])),
        )
        return {
            "check": {
                "missing_documents": check.missing_documents,
                "missing_fields": check.missing_fields,
                "name_mismatch": check.name_mismatch,
                "certificate_name": check.certificate_name,
                "application_name": check.application_name,
                "complete": check.complete,
                "clean": check.clean,
            }
        }

    def route_after_crosscheck(state: DealerOnboardingState) -> str:
        check = state["check"]
        if check["name_mismatch"]:
            return "flag"
        if not check["complete"]:
            return "compose_email"
        return "handoff"

    async def flag(state: DealerOnboardingState) -> dict[str, Any]:
        check = state["check"]
        update = await crm.update_status(
            application_id=state["application_id"],
            status="manual_review",
            note=(
                "Unvan uyuşmazlığı: belge "
                f"{check['certificate_name']!r}, başvuru {check['application_name']!r}"
            ),
        )
        return {"status_update": update}

    async def compose_email(state: DealerOnboardingState) -> dict[str, Any]:
        check_state = state["check"]
        check = CrossCheck(
            missing_documents=list(check_state["missing_documents"]),
            missing_fields=list(check_state["missing_fields"]),
            name_mismatch=check_state["name_mismatch"],
            certificate_name=check_state["certificate_name"],
            application_name=check_state["application_name"],
        )
        message = render_missing_docs_email(
            application=state.get("application", {}), check=check
        )
        return {
            "email": {
                "to": message.to,
                "subject": message.subject,
                "body": message.body,
                "missing_items": message.missing_items,
            }
        }

    async def hitl(state: DealerOnboardingState) -> dict[str, Any]:
        # email.send is write:external — TRD §9 names customer email as the
        # canonical always-approved write, and dept scenario 09's rollout puts
        # the first month's outbound mail behind approval unconditionally.
        assert requires_approval(
            risk_class=_EMAIL_RISK_CLASS, eval_pass_rate=0.0, autonomy_enabled=False
        )
        decision = interrupt(
            {
                "tool": "email.send",
                "risk_class": _EMAIL_RISK_CLASS,
                "args": {
                    "to": state["email"]["to"],
                    "subject": state["email"]["subject"],
                    "body": state["email"]["body"],
                },
                # What the applicant is being asked for, alongside the message —
                # the approver can check the ask against the dossier without
                # re-reading the body.
                "missing_items": state["email"]["missing_items"],
                "dossier": state["dossier"],
            }
        )
        if not decision.get("approved"):
            return {"rejected": True}
        return {}

    def route_after_hitl(state: DealerOnboardingState) -> str:
        return "end" if state.get("rejected") else "send_email"

    async def send_email(state: DealerOnboardingState) -> dict[str, Any]:
        message = state["email"]
        await email.send(
            to=message["to"], subject=message["subject"], body=message["body"]
        )
        update = await crm.update_status(
            application_id=state["application_id"],
            status="awaiting_documents",
            note=f"Eksik belge talebi gönderildi: {', '.join(message['missing_items'])}",
        )
        return {
            "email_sent": {"to": message["to"], "subject": message["subject"]},
            "status_update": update,
        }

    async def handoff(state: DealerOnboardingState) -> dict[str, Any]:
        # crm.update_status is write:internal and runs supervised (audited, not
        # interrupted) — dept scenario 09 puts only the *outbound email* behind
        # approval. The pipeline move is reversible inside our own CRM; the
        # email is not reversible once it reaches the applicant.
        update = await crm.update_status(
            application_id=state["application_id"],
            status="ready_for_sales",
            note="Dosya eksiksiz; kurumsal satış temsilcisine devredildi.",
        )
        return {"status_update": update}

    async def end_node(state: DealerOnboardingState) -> dict[str, Any]:
        return {}

    graph = StateGraph(DealerOnboardingState)
    graph.add_node("killswitch_gate", killswitch_gate)
    graph.add_node("fetch_application", fetch_application)
    graph.add_node("ocr", ocr_node)
    graph.add_node("extract", extract)
    graph.add_node("crosscheck", crosscheck_node)
    graph.add_node("flag", flag)
    graph.add_node("compose_email", compose_email)
    graph.add_node("hitl", hitl)
    graph.add_node("send_email", send_email)
    graph.add_node("handoff", handoff)
    graph.add_node("end", end_node)

    graph.set_entry_point("killswitch_gate")
    graph.add_conditional_edges(
        "killswitch_gate",
        route_after_killswitch,
        {END: END, "fetch_application": "fetch_application"},
    )
    graph.add_edge("fetch_application", "ocr")
    graph.add_edge("ocr", "extract")
    graph.add_conditional_edges(
        "extract", route_after_extract, {"crosscheck": "crosscheck", "end": "end"}
    )
    graph.add_conditional_edges(
        "crosscheck",
        route_after_crosscheck,
        {"flag": "flag", "compose_email": "compose_email", "handoff": "handoff"},
    )
    graph.add_edge("flag", "end")
    graph.add_edge("compose_email", "hitl")
    graph.add_conditional_edges(
        "hitl", route_after_hitl, {"send_email": "send_email", "end": "end"}
    )
    graph.add_edge("send_email", "end")
    graph.add_edge("handoff", "end")
    graph.add_edge("end", END)

    return graph.compile(checkpointer=checkpointer)
