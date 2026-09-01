"""Integration: full HR Agent chain against the real dev stack (task 8.5, dept
scenario 05 "HR Talent & Onboarding").

Real HTTP round-trip through the actual FastAPI app: `builder` starts a run
(POST /v1/hr-agent/runs) with a base64 CV image and the role's criteria; the
graph runs OCR (real Tesseract — the pii lane never touches the cloud vision
model, task 8.2) -> extracts a CvProfile via a real local-Qwen reasoning call
-> scores the role match -> interrupts, proven by a real pending Approval row
whose payload is the shortlist draft. `approver` then approves; a second
run+reject proves the reject path closes without approving anything.

Mirrors test_invoice_agent_e2e_live.py's shape. Two HR-specific assertions it
does not have:
  - the approval payload must NOT carry protected attributes (birthdate/age/
    gender), even though the rendered CV puts them on the page — the dept
    scenario's schema-exclusion guardrail, proven end-to-end here rather than
    only at the extractor unit level;
  - the action is `hr.shortlist_draft` (write:internal), and every run reaches
    the queue because autonomy is never enabled for this scenario.

The CV image is rendered with the shared evals renderer so the OCR step reads
genuine pixel content, exercising image bytes -> structured fields for real.
"""

from __future__ import annotations

import asyncio
import os
import sys

import httpx
import pytest

if sys.platform == "win32":
    # Same Windows/psycopg-async fixup as test_invoice_agent_e2e_live.py
    # (AsyncPostgresSaver checkpointer can't run on ProactorEventLoop).
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

KEYCLOAK_BASE = "http://localhost:8080"
API_DATABASE_URL = "postgresql+asyncpg://fleet:fleet_dev_pw@localhost:5432/fleet"

# On the raw CV page but never allowed into the extracted profile.
_BIRTHDATE = "1990-04-12"
_GENDER = "Kadin"

_CV_LINES = [
    "Zeynep Kaya",
    "E-posta: zeynep.kaya@example.com",
    "Telefon: +90 555 987 6543",
    f"Dogum Tarihi: {_BIRTHDATE}",
    f"Cinsiyet: {_GENDER}",
    "Egitim: BSc Bilgisayar Muhendisligi, ITU, 2018",
    "Deneyim: Backend Gelistirici, Fleet Lojistik, 2018-2023",
    "Yetenekler: Python, PostgreSQL, Docker",
]


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


def _tesseract_available() -> bool:
    try:
        import pytesseract

        pytesseract.get_tesseract_version()
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not (_stack_up() and _pillow_available() and _tesseract_available()),
    reason="dev stack not reachable, or Pillow/Tesseract not installed",
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
    # CPU-only local-lane extraction runs 26-39s (task 8.5); the 60s default
    # is too tight to be reliable under test load.
    os.environ.setdefault("FLEET_LITELLM_TIMEOUT", "300")


def _render_cv_image_base64() -> str:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "evals"))
    from synthetic_images import render_document_image_base64

    return render_document_image_base64(_CV_LINES)


def _start_run(client: httpx.AsyncClient, token: str) -> object:
    return client.post(
        "/v1/hr-agent/runs",
        json={
            "image_base64": _render_cv_image_base64(),
            "criteria": ["Python", "PostgreSQL", "Docker"],
        },
        headers={"Authorization": f"Bearer {token}"},
    )


def test_cv_run_reaches_approval_queue_without_protected_attributes() -> None:
    _set_common_env()
    builder_token = _token("builder", "builder")
    approver_token = _token("approver", "approver")

    async def _run() -> None:
        import fleet_api.db as fleet_db
        from fleet_api.app import create_app

        fleet_db._app_session_factory.cache_clear()

        app = create_app(with_middleware=False)
        transport = httpx.ASGITransport(app=app)

        async with httpx.AsyncClient(
            transport=transport, base_url="http://test", timeout=300
        ) as client:
            run_resp = await _start_run(client, builder_token)
            assert run_resp.status_code == 201, run_resp.text
            run_body = run_resp.json()
            assert run_body["status"] == "pending_approval", run_body
            run_id = run_body["run_id"]

            list_resp = await client.get(
                "/v1/approvals", headers={"Authorization": f"Bearer {approver_token}"}
            )
            assert list_resp.status_code == 200, list_resp.text
            pending = [a for a in list_resp.json() if a["run_id"] == run_id]
            assert len(pending) == 1, "expected exactly one pending approval for this run"
            approval = pending[0]

            # write:internal shortlist draft, always queued (autonomy off).
            assert approval["action"] == "hr.shortlist_draft"

            payload = approval["payload"]
            # Extracted for real from the rendered pixels, not supplied here.
            assert payload["full_name"], payload
            assert "zeynep.kaya@example.com" in payload["email"].lower()

            # The guardrail, proven end-to-end: the birthdate and gender are
            # on the CV page the OCR read, yet cannot reach the approval row.
            dumped = str(payload).lower()
            assert _BIRTHDATE not in dumped, f"birthdate leaked into approval payload: {payload}"
            assert _GENDER.lower() not in dumped, f"gender leaked into approval payload: {payload}"
            for forbidden in ("birthdate", "age", "gender", "photo"):
                assert forbidden not in payload, f"{forbidden} key present: {payload}"

            decide_resp = await client.post(
                f"/v1/approvals/{approval['id']}/decide",
                json={"decision": "approve"},
                headers={"Authorization": f"Bearer {approver_token}"},
            )
            assert decide_resp.status_code == 200, decide_resp.text
            assert decide_resp.json()["status"] == "approved"

    asyncio.run(_run())


def test_reject_path_closes_the_shortlist_draft() -> None:
    _set_common_env()
    builder_token = _token("builder", "builder")
    approver_token = _token("approver", "approver")

    async def _run() -> None:
        import fleet_api.db as fleet_db
        from fleet_api.app import create_app

        fleet_db._app_session_factory.cache_clear()

        app = create_app(with_middleware=False)
        transport = httpx.ASGITransport(app=app)

        async with httpx.AsyncClient(
            transport=transport, base_url="http://test", timeout=300
        ) as client:
            run_resp = await _start_run(client, builder_token)
            assert run_resp.status_code == 201, run_resp.text
            run_id = run_resp.json()["run_id"]

            list_resp = await client.get(
                "/v1/approvals", headers={"Authorization": f"Bearer {approver_token}"}
            )
            approval = next(a for a in list_resp.json() if a["run_id"] == run_id)

            decide_resp = await client.post(
                f"/v1/approvals/{approval['id']}/decide",
                json={"decision": "reject"},
                headers={"Authorization": f"Bearer {approver_token}"},
            )
            assert decide_resp.status_code == 200, decide_resp.text
            assert decide_resp.json()["status"] == "rejected"

            after = await client.get(
                "/v1/approvals", headers={"Authorization": f"Bearer {approver_token}"}
            )
            still_pending = [
                a for a in after.json() if a["run_id"] == run_id and a["status"] == "pending"
            ]
            assert not still_pending, "rejected run must not leave a pending approval"

    asyncio.run(_run())
