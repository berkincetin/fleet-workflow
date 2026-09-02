"""agents.dealer_onboarding — approval-gated outbound email, mismatch flagging,
and the deterministic cross-check (task 12.1, dept scenario 09).

Proves: a dossier with a missing document reaches the write:external HITL
interrupt and sends NOTHING (and moves no CRM status) until approved; a
rejected approval sends nothing at all; a certificate/application name mismatch
goes to manual_review with no email composed; a clean dossier is handed to
sales without an interrupt; the extractor refuses malformed identifiers rather
than passing them through; the TR template lists exactly the missing items.
"""

from __future__ import annotations

import json
from typing import Any

import pytest
from agents.dealer_onboarding.crosscheck import (
    CrossCheck,
    cross_check,
    normalize_company_name,
)
from agents.dealer_onboarding.email_template import render_missing_docs_email
from agents.dealer_onboarding.extractor import (
    ExtractionParseError,
    extract_dealer_dossier,
)
from agents.dealer_onboarding.graph import build_dealer_onboarding_graph
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

_APPLICATION = {
    "application_id": "APP-1",
    "company_name": "Anadolu Otomotiv Ticaret A.Ş.",
    "contact_name": "Mehmet Yılmaz",
    "contact_email": "dealer@fleet.local",
}


class _FakeReasoning:
    def __init__(self, dossier: dict[str, Any]) -> None:
        self._content = json.dumps(dossier, ensure_ascii=False)
        self.sensitivities: list[str] = []

    async def reasoning(self, messages: list[dict[str, Any]], **kwargs: Any) -> Any:
        self.sensitivities.append(kwargs.get("sensitivity", ""))

        class _Resp:
            content = self._content

        return _Resp()


class _FakeOcr:
    async def extract_text(self, image_base64: str) -> dict[str, str]:
        return {"text": f"belge:{image_base64}", "source": "tesseract"}


class _FakeCrm:
    def __init__(self, application: dict[str, Any]) -> None:
        self._application = application
        self.status_updates: list[dict[str, Any]] = []

    async def get_application(self, *, application_id: str) -> dict[str, Any]:
        return dict(self._application)

    async def update_status(
        self, *, application_id: str, status: str, note: str | None = None
    ) -> dict[str, Any]:
        record = {"application_id": application_id, "status": status, "note": note or ""}
        self.status_updates.append(record)
        return record


class _FakeEmail:
    def __init__(self) -> None:
        self.sent: list[dict[str, str]] = []

    async def send(self, to: str, subject: str, body: str) -> None:
        self.sent.append({"to": to, "subject": subject, "body": body})


_CERTIFICATE_DOSSIER = {
    "company_name": "Anadolu Otomotiv Ticaret A.Ş.",
    "tax_no": "1234567890",
    "iban": "TR330006100519786457841326",
    "certificate_no": "YB-2026-0431",
}


def _build(
    dossier: dict[str, Any],
    *,
    application: dict[str, Any] | None = None,
    killswitch: Any = None,
) -> tuple[Any, _FakeCrm, _FakeEmail, _FakeReasoning]:
    reasoning = _FakeReasoning(dossier)
    crm = _FakeCrm(application or _APPLICATION)
    email = _FakeEmail()
    graph = build_dealer_onboarding_graph(
        llm_client=reasoning, ocr=_FakeOcr(), crm=crm, email=email,
        checkpointer=InMemorySaver(), killswitch=killswitch,
    )
    return graph, crm, email, reasoning


def _documents(*kinds: str) -> list[dict[str, str]]:
    return [{"kind": k, "image_base64": f"img-{k}"} for k in kinds]


async def test_missing_document_reaches_approval_and_sends_nothing() -> None:
    graph, crm, email, _ = _build(_CERTIFICATE_DOSSIER)
    cfg = {"configurable": {"thread_id": "1"}}
    result = await graph.ainvoke(
        {"application_id": "APP-1", "documents": _documents("authorization_certificate")},
        cfg,
    )

    assert "__interrupt__" in result
    payload = result["__interrupt__"][0].value
    assert payload["tool"] == "email.send"
    assert payload["risk_class"] == "write:external"
    assert payload["missing_items"] == ["Vergi Levhası"]
    # Nothing left the building and the application did not move.
    assert email.sent == []
    assert crm.status_updates == []


async def test_approval_sends_the_email_and_moves_the_application() -> None:
    graph, crm, email, _ = _build(_CERTIFICATE_DOSSIER)
    cfg = {"configurable": {"thread_id": "2"}}
    await graph.ainvoke(
        {"application_id": "APP-1", "documents": _documents("authorization_certificate")},
        cfg,
    )
    resumed = await graph.ainvoke(Command(resume={"approved": True}), cfg)

    assert len(email.sent) == 1
    assert email.sent[0]["to"] == "dealer@fleet.local"
    assert "Vergi Levhası" in email.sent[0]["body"]
    assert resumed["status_update"]["status"] == "awaiting_documents"


async def test_rejected_approval_sends_nothing() -> None:
    graph, crm, email, _ = _build(_CERTIFICATE_DOSSIER)
    cfg = {"configurable": {"thread_id": "3"}}
    await graph.ainvoke(
        {"application_id": "APP-1", "documents": _documents("authorization_certificate")},
        cfg,
    )
    resumed = await graph.ainvoke(Command(resume={"approved": False}), cfg)

    assert resumed.get("rejected") is True
    assert email.sent == []
    assert crm.status_updates == []


async def test_name_mismatch_flags_for_review_and_never_emails() -> None:
    graph, crm, email, _ = _build(
        {**_CERTIFICATE_DOSSIER, "company_name": "Trakya Nakliyat Ltd. Şti."}
    )
    result = await graph.ainvoke(
        {
            "application_id": "APP-1",
            "documents": _documents("authorization_certificate", "tax_registration"),
        },
        {"configurable": {"thread_id": "4"}},
    )

    assert "__interrupt__" not in result
    assert result["check"]["name_mismatch"] is True
    assert email.sent == []
    assert crm.status_updates[-1]["status"] == "manual_review"


async def test_clean_dossier_is_handed_to_sales_without_approval() -> None:
    graph, crm, email, _ = _build(_CERTIFICATE_DOSSIER)
    result = await graph.ainvoke(
        {
            "application_id": "APP-1",
            "documents": _documents("authorization_certificate", "tax_registration"),
        },
        {"configurable": {"thread_id": "5"}},
    )

    assert "__interrupt__" not in result
    assert result["check"]["clean"] is True
    assert email.sent == []
    assert crm.status_updates[-1]["status"] == "ready_for_sales"


async def test_extraction_runs_on_the_pii_lane() -> None:
    """The dossier call must be made at sensitivity=pii — the one level
    core.llm.routing never downgrades, so no cloud model is eligible."""
    graph, _, _, reasoning = _build(_CERTIFICATE_DOSSIER)
    await graph.ainvoke(
        {"application_id": "APP-1", "documents": _documents("authorization_certificate")},
        {"configurable": {"thread_id": "6"}},
    )
    assert reasoning.sensitivities == ["pii"]


async def test_paused_agent_short_circuits() -> None:
    class _Paused:
        async def is_agent_paused(self, name: str) -> bool:
            return True

        async def blocks_tool(self, *, risk_class: str) -> bool:
            return False

    graph, crm, email, _ = _build(_CERTIFICATE_DOSSIER, killswitch=_Paused())
    result = await graph.ainvoke(
        {"application_id": "APP-1", "documents": _documents("authorization_certificate")},
        {"configurable": {"thread_id": "7"}},
    )
    assert result.get("paused") is True
    assert email.sent == []
    assert crm.status_updates == []


# --- extractor: never-invent normalisation -----------------------------------


class _Responder:
    def __init__(self, content: str) -> None:
        self._content = content

    async def reasoning(self, messages: list[dict[str, Any]], **kwargs: Any) -> Any:
        class _Resp:
            content = self._content

        return _Resp()


async def test_malformed_tax_no_becomes_missing_not_padded() -> None:
    dossier = await extract_dealer_dossier(
        ocr_text="...",
        llm_client=_Responder(json.dumps({"company_name": "X A.Ş.", "tax_no": "12345"})),
    )
    assert dossier.tax_no is None
    assert dossier.missing_fields == ["tax_no"]


async def test_ocr_spaced_tax_no_and_iban_are_normalised() -> None:
    dossier = await extract_dealer_dossier(
        ocr_text="...",
        llm_client=_Responder(
            json.dumps(
                {
                    "company_name": "X A.Ş.",
                    "tax_no": "123 456 7890",
                    "iban": "TR33 0006 1005 1978 6457 8413 26",
                }
            )
        ),
    )
    assert dossier.tax_no == "1234567890"
    assert dossier.iban == "TR330006100519786457841326"
    assert dossier.missing_fields == []


async def test_non_json_response_raises() -> None:
    with pytest.raises(ExtractionParseError):
        await extract_dealer_dossier(ocr_text="...", llm_client=_Responder("sorry, no"))


# --- cross-check + template --------------------------------------------------


def test_legal_form_and_diacritics_do_not_count_as_a_mismatch() -> None:
    assert normalize_company_name("Anadolu Otomotiv Ticaret A.Ş.") == normalize_company_name(
        "ANADOLU OTOMOTIV TICARET AS"
    )


def test_missing_certificate_name_is_not_reported_as_a_mismatch() -> None:
    check = cross_check(
        application=_APPLICATION,
        provided_documents=["authorization_certificate"],
        certificate_name=None,
        missing_fields=["company_name"],
    )
    assert check.name_mismatch is False
    assert "tax_registration" in check.missing_documents


def test_email_lists_exactly_the_missing_items_in_a_formal_register() -> None:
    check = CrossCheck(missing_documents=["tax_registration"], missing_fields=["tax_no"])
    message = render_missing_docs_email(application=_APPLICATION, check=check)

    assert message.missing_items == ["Vergi Levhası", "Vergi Kimlik Numarası"]
    assert "Yetki Belgesi" not in message.body  # not missing → not asked for
    assert message.body.startswith("Sayın")
    assert "rica ederiz" in message.body
    assert message.body.rstrip().endswith("Kurumsal Satış Ekibi")
    assert "APP-1" in message.subject


def test_rendering_an_email_with_nothing_missing_is_a_bug_not_an_empty_mail() -> None:
    with pytest.raises(ValueError):
        render_missing_docs_email(application=_APPLICATION, check=CrossCheck())
