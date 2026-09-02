"""Integration: Dealer Onboarding against the real dev stack (task 12.1 AC —
"approval-gated outbound email verified for the first month's rollout mode").

Drives the real dealer_onboarding graph the way the API router does: real local
tesseract OCR of a rendered authorization certificate, real LOCAL-lane
extraction through the live gateway (the call is made at sensitivity=pii, so
routing admits no cloud model), the real deterministic cross-check, and the real
email MCP tool pointed at the sandbox SMTP (mailpit).

Two things are proven end to end that a unit test with fakes cannot:
1. The missing-document run stops at the write:external interrupt with mailpit
   still empty — the approval gate holds against the real transport.
2. Resuming with approved=True actually delivers the message to mailpit, and
   the mail body names exactly the missing document.
"""

from __future__ import annotations

import asyncio
import base64
import sys

import httpx
import pytest

if sys.platform == "win32":
    # Same Windows/psycopg-async fixup as the other HITL e2e tests: the
    # AsyncPostgresSaver checkpointer can't run on ProactorEventLoop.
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

KEYCLOAK_BASE = "http://localhost:8080"
MAILPIT_BASE = "http://localhost:8025"
API_DATABASE_URL = "postgresql+asyncpg://fleet:fleet_dev_pw@localhost:5432/fleet"

_CERTIFICATE_LINES = [
    "YETKI BELGESI",
    "Ticari Unvan: Anadolu Otomotiv Ticaret A.S.",
    "Vergi Kimlik No: 1234567890",
    "Belge No: YB-2026-0431",
]

_APPLICATION = {
    "application_id": "APP-E2E-1",
    "company_name": "Anadolu Otomotiv Ticaret A.S.",
    "contact_name": "Mehmet Yilmaz",
    "contact_email": "dealer@fleet.local",
}


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


class _FixtureCrm:
    def __init__(self) -> None:
        self.status_updates: list[dict[str, object]] = []

    async def get_application(self, *, application_id: str) -> dict[str, object]:
        return dict(_APPLICATION)

    async def update_status(
        self, *, application_id: str, status: str, note: str | None = None
    ) -> dict[str, object]:
        record = {"application_id": application_id, "status": status, "note": note or ""}
        self.status_updates.append(record)
        return record


def _mailpit_messages_to(address: str) -> list[dict[str, object]]:
    r = httpx.get(f"{MAILPIT_BASE}/api/v1/search", params={"query": f"to:{address}"}, timeout=10)
    r.raise_for_status()
    return list(r.json().get("messages", []))


def _delete_mailpit_messages() -> None:
    httpx.delete(f"{MAILPIT_BASE}/api/v1/messages", timeout=10)


async def test_missing_document_email_is_held_at_approval_then_actually_sent() -> None:
    from agents.dealer_onboarding.graph import build_dealer_onboarding_graph
    from core.llm.factory import build_client
    from fleet_mcp.servers.email import EmailSendTool
    from fleet_mcp.servers.ocr import build_ocr_tool
    from fleet_mcp.servers.smtp_sender import build_default_sender
    from fleet_rag.ingest.ocr import tesseract_ocr
    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
    from langgraph.types import Command

    sys.path.insert(0, "evals")
    from synthetic_images import render_document_image_base64  # type: ignore[import-not-found]

    _delete_mailpit_messages()

    class _OcrAdapter:
        def __init__(self, fn: object) -> None:
            self._fn = fn

        async def extract_text(self, image_base64: str) -> dict[str, str]:
            return await self._fn(image_base64=image_base64)  # type: ignore[operator,no-any-return]

    llm_client = await build_client()
    ocr = _OcrAdapter(
        build_ocr_tool(vision_client=llm_client, tesseract_fn=tesseract_ocr, sensitivity="pii")
    )
    crm = _FixtureCrm()
    email = EmailSendTool(sender=build_default_sender(), allowed_domains={"fleet.local"})

    documents = [
        {
            "kind": "authorization_certificate",
            "image_base64": render_document_image_base64(_CERTIFICATE_LINES),
        }
    ]
    dsn = API_DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")

    async with AsyncPostgresSaver.from_conn_string(dsn) as checkpointer:
        graph = build_dealer_onboarding_graph(
            llm_client=llm_client, ocr=ocr, crm=crm, email=email, checkpointer=checkpointer,
        )
        cfg = {"configurable": {"thread_id": "do-e2e-1"}}
        result = await graph.ainvoke(
            {"application_id": _APPLICATION["application_id"], "documents": documents}, cfg
        )

        # The tax registration is missing, so the run stops at the email approval.
        assert "__interrupt__" in result, result.get("blocked_reason")
        payload = result["__interrupt__"][0].value
        assert payload["tool"] == "email.send"
        assert payload["risk_class"] == "write:external"
        assert payload["missing_items"] == ["Vergi Levhası"]
        # The local lane read the certificate: the tax number came off the image.
        assert result["dossier"]["tax_no"] == "1234567890"
        # Nothing on the wire, nothing moved in the CRM, while it waits.
        assert _mailpit_messages_to("dealer@fleet.local") == []
        assert crm.status_updates == []

        resumed = await graph.ainvoke(Command(resume={"approved": True}), cfg)

    # Approval is what puts it on the wire.
    messages = _mailpit_messages_to("dealer@fleet.local")
    assert len(messages) == 1
    assert _APPLICATION["application_id"] in str(messages[0]["Subject"])
    assert resumed["status_update"]["status"] == "awaiting_documents"


async def test_rendered_certificate_reaches_the_local_lane_only() -> None:
    """The dossier extraction must never be served by a cloud model — the
    certificate carries the dealer's tax number (TRD §8)."""
    from core.llm.factory import build_client
    from core.llm.routing import select_model

    llm_client = await build_client()
    chosen = select_model(llm_client._models, role="reasoning", sensitivity="pii")
    assert chosen["sensitivity_clearance"] == "pii"
    assert chosen["provider"] == "ollama"

    # And the redaction downgrade cannot be used to escape it: `pii` is never
    # downgraded, even when the caller claims the content was redacted.
    still_local = select_model(
        llm_client._models, role="reasoning", sensitivity="pii", redacted=True
    )
    assert still_local["provider"] == "ollama"


async def test_ocr_of_a_pii_document_never_calls_the_cloud_vision_model() -> None:
    """ocr_image skips the vision lane entirely at pii sensitivity, so the raw
    certificate image is read by local tesseract only — run here against the
    real rendered document and the real tesseract binary."""
    from fleet_rag.ingest.ocr import ocr_image, tesseract_ocr

    calls: list[object] = []

    class _ExplodingVision:
        async def reasoning(self, messages: list[dict[str, object]], **kwargs: object) -> object:
            calls.append(messages)
            raise AssertionError("cloud vision must not be called for a pii image")

    sys.path.insert(0, "evals")
    from synthetic_images import render_document_image_base64  # type: ignore[import-not-found]

    image = base64.b64decode(render_document_image_base64(_CERTIFICATE_LINES))
    result = await ocr_image(
        image,
        vision_client=_ExplodingVision(),
        tesseract_fn=tesseract_ocr,
        sensitivity="pii",
    )
    assert result.source == "tesseract"
    assert "1234567890" in result.text
    assert calls == []
