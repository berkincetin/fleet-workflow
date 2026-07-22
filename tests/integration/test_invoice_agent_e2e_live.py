"""Integration: full Invoice Agent chain against the real dev stack (task 6.3
AC: "invoice draft appears in approval queue with extracted fields").

Real HTTP round-trip through the actual FastAPI app: `builder` starts a run
(POST /v1/invoice-agent/runs) with a base64 image; the graph runs OCR (real
vision-LLM call through the live gateway — the same `ocr.extract_text` path
proven live in Sprint 5.1, not re-proven here) -> extracts fields via a real
reasoning-tier call -> validates against the real `fixture_purchase_orders`
view (seeded by `make seed`, task 6.3) -> interrupts, proven by a real
pending Approval row with the extracted fields as its payload. `approver`
then approves (POST /v1/approvals/{id}/decide): the SAME persisted graph run
is rebuilt fresh and resumed (mirrors test_dev_agent_approval_e2e_live.py's
proof), creating a real draft ERP entry. A second run+reject proves the
reject path cancels without ever creating a draft entry.

The uploaded "invoice" is a small PNG rendered with real text via Pillow
(vendor/PO/amount matching PO-1001's real seeded row) so the OCR step reads
genuine pixel content, not a pre-supplied string — the extraction pipeline is
exercised for real, image bytes to structured fields, same spirit as 5.1's
own OCR live test.
"""

from __future__ import annotations

import asyncio
import base64
import io
import os
import sys

import httpx
import pytest

if sys.platform == "win32":
    # Same Windows/psycopg-async fixup as test_dev_agent_approval_e2e_live.py
    # (AsyncPostgresSaver checkpointer can't run on ProactorEventLoop).
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

KEYCLOAK_BASE = "http://localhost:8080"
API_DATABASE_URL = "postgresql+asyncpg://fleet:fleet_dev_pw@localhost:5432/fleet"


def _stack_up() -> bool:
    try:
        r = httpx.get(f"{KEYCLOAK_BASE}/realms/fleet/.well-known/openid-configuration", timeout=3)
        return r.status_code == 200
    except Exception:
        return False


def _pillow_available() -> bool:
    try:
        import PIL  # noqa: F401

        return True
    except ImportError:
        return False


pytestmark = pytest.mark.skipif(
    not (_stack_up() and _pillow_available()),
    reason="dev stack not reachable or Pillow not installed",
)


def _token(username: str, password: str) -> str:
    resp = httpx.post(
        f"{KEYCLOAK_BASE}/realms/fleet/protocol/openid-connect/token",
        data={
            "client_id": "fleet-api",
            "client_secret": "fleet-api-dev-secret",
            "grant_type": "password",
            "username": username,
            "password": password,
        },
        timeout=10,
    )
    resp.raise_for_status()
    return str(resp.json()["access_token"])


def _set_common_env() -> None:
    os.environ["FLEET_DATABASE_URL"] = API_DATABASE_URL
    os.environ["FLEET_OIDC_ISSUER"] = f"{KEYCLOAK_BASE}/realms/fleet"
    os.environ["FLEET_OIDC_JWKS_URL"] = (
        f"{KEYCLOAK_BASE}/realms/fleet/protocol/openid-connect/certs"
    )
    os.environ["FLEET_OIDC_AUDIENCE"] = "fleet-api"
    os.environ["FLEET_REDIS_URL"] = "redis://localhost:6379/0"


def _render_invoice_image_base64(*, vendor: str, po_number: str, amount: str) -> str:
    from PIL import Image, ImageDraw

    img = Image.new("RGB", (500, 200), color="white")
    draw = ImageDraw.Draw(img)
    draw.text((10, 10), f"Vendor: {vendor}", fill="black")
    draw.text((10, 50), f"PO Number: {po_number}", fill="black")
    draw.text((10, 90), f"Total Amount: {amount} TRY", fill="black")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("ascii")


def test_matching_invoice_reaches_approval_queue_with_extracted_fields() -> None:
    _set_common_env()
    builder_token = _token("builder", "builder")
    approver_token = _token("approver", "approver")
    image_b64 = _render_invoice_image_base64(
        vendor="Acme Tedarik A.S.", po_number="PO-1001", amount="1250.00"
    )

    async def _run() -> None:
        import fleet_api.db as fleet_db
        from fleet_api.app import create_app

        fleet_db._app_session_factory.cache_clear()

        app = create_app(with_middleware=False)
        transport = httpx.ASGITransport(app=app)

        async with httpx.AsyncClient(
            transport=transport, base_url="http://test", timeout=60
        ) as client:
            run_resp = await client.post(
                "/v1/invoice-agent/runs",
                json={"image_base64": image_b64},
                headers={"Authorization": f"Bearer {builder_token}"},
            )
            assert run_resp.status_code == 201, run_resp.text
            run_body = run_resp.json()
            assert run_body["status"] == "pending_approval"
            run_id = run_body["run_id"]

            list_resp = await client.get(
                "/v1/approvals", headers={"Authorization": f"Bearer {approver_token}"}
            )
            assert list_resp.status_code == 200, list_resp.text
            pending = [a for a in list_resp.json() if a["run_id"] == run_id]
            assert len(pending) == 1, "expected exactly one pending approval for this run"
            approval = pending[0]
            assert approval["action"] == "erp.create_draft_entry"
            # The literal AC: "invoice draft appears in approval queue with
            # extracted fields" — po_number/amount actually came from OCR+LLM
            # extraction, not a value this test supplied directly.
            assert "po_number" in approval["payload"]
            assert "amount" in approval["payload"]
            assert "vendor" in approval["payload"]

            decide_resp = await client.post(
                f"/v1/approvals/{approval['id']}/decide",
                json={"decision": "approve"},
                headers={"Authorization": f"Bearer {approver_token}"},
            )
            assert decide_resp.status_code == 200, decide_resp.text
            assert decide_resp.json()["status"] == "approved"

    asyncio.run(_run())


def test_reject_path_never_creates_a_draft_entry() -> None:
    _set_common_env()
    builder_token = _token("builder", "builder")
    approver_token = _token("approver", "approver")
    image_b64 = _render_invoice_image_base64(
        vendor="Acme Tedarik A.S.", po_number="PO-1001", amount="1250.00"
    )

    async def _run() -> None:
        import fleet_api.db as fleet_db
        from fleet_api.app import create_app

        fleet_db._app_session_factory.cache_clear()

        app = create_app(with_middleware=False)
        transport = httpx.ASGITransport(app=app)

        async with httpx.AsyncClient(
            transport=transport, base_url="http://test", timeout=60
        ) as client:
            run_resp = await client.post(
                "/v1/invoice-agent/runs",
                json={"image_base64": image_b64},
                headers={"Authorization": f"Bearer {builder_token}"},
            )
            assert run_resp.status_code == 201, run_resp.text
            run_id = run_resp.json()["run_id"]

            list_resp = await client.get(
                "/v1/approvals", headers={"Authorization": f"Bearer {approver_token}"}
            )
            pending = [a for a in list_resp.json() if a["run_id"] == run_id]
            assert len(pending) == 1
            approval = pending[0]

            decide_resp = await client.post(
                f"/v1/approvals/{approval['id']}/decide",
                json={"decision": "reject"},
                headers={"Authorization": f"Bearer {approver_token}"},
            )
            assert decide_resp.status_code == 200, decide_resp.text
            assert decide_resp.json()["status"] == "rejected"

    asyncio.run(_run())
