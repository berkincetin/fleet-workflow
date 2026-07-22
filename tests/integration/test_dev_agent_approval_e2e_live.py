"""Integration: full Dev Agent chain against the real dev stack + sandbox
GitHub repo (task 5.5 AC: "labeled mock ticket -> pending approval -> approve
-> PR exists on sandbox repo -> Slack message; reject path cleanly cancels").

Real HTTP round-trip through the actual FastAPI app: `builder` starts a run
(POST /v1/dev-agent/runs) against a fixture ticket (DEV-1, agent-ok labeled),
the graph plans+creates a real branch on the sandbox repo and interrupts —
proven by a real pending Approval row. `approver` then decides it
(POST /v1/approvals/{id}/decide): the approve path resumes the SAME
persisted graph run (rebuilt fresh, same as test_runtime_graph_live.py) and
opens a REAL PR on the sandbox repo, confirmed by fetching the PR back from
GitHub's API — not just trusting the response body. A second run+reject
proves the reject path cancels without ever calling github.open_pr.

No real Slack workspace exists in this environment (see PROGRESS.md 5.3) —
FLEET_SLACK_WEBHOOK_URL is unset, so slack_notify's real send fails silently
past the graph's own success path (the PR/approval assertions below are what
prove the AC live; Slack's own dispatch is covered by 5.3's unit-level
SlackPostTool tests, same scope split already used for Jira/Slack there).
"""

from __future__ import annotations

import asyncio
import os
import re
import sys
from pathlib import Path

import httpx
import pytest

if sys.platform == "win32":
    # psycopg's async mode (used by the Dev Agent graph's AsyncPostgresSaver
    # checkpointer) cannot run on Windows' default ProactorEventLoop — same
    # test-infra-only fixup as test_runtime_graph_live.py; production runs
    # under uvicorn on Linux and is unaffected.
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

KEYCLOAK_BASE = "http://localhost:8080"
API_DATABASE_URL = "postgresql+asyncpg://fleet:fleet_dev_pw@localhost:5432/fleet"

_ENV_LINE_RE = re.compile(r"^([A-Z_][A-Z0-9_]*)=(.*)$")


def _load_dotenv_fallback() -> None:
    env_path = Path(__file__).resolve().parents[2] / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        match = _ENV_LINE_RE.match(line.strip())
        if match and match.group(1) not in os.environ:
            os.environ[match.group(1)] = match.group(2)


_load_dotenv_fallback()

SANDBOX_REPO = os.environ.get("FLEET_GITHUB_SANDBOX_REPO", "")
SANDBOX_TOKEN = os.environ.get("FLEET_GITHUB_SANDBOX_TOKEN", "")


def _stack_up() -> bool:
    try:
        r = httpx.get(f"{KEYCLOAK_BASE}/realms/fleet/.well-known/openid-configuration", timeout=3)
        return r.status_code == 200
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not (_stack_up() and SANDBOX_REPO and SANDBOX_TOKEN),
    reason="dev stack or FLEET_GITHUB_SANDBOX_REPO/TOKEN not available",
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


def _sandbox_pr_state(pr_number: int) -> str:
    resp = httpx.get(
        f"https://api.github.com/repos/{SANDBOX_REPO}/pulls/{pr_number}",
        headers={
            "Authorization": f"Bearer {SANDBOX_TOKEN}",
            "Accept": "application/vnd.github+json",
        },
    )
    resp.raise_for_status()
    return str(resp.json()["state"])


def _set_common_env() -> None:
    os.environ["FLEET_DATABASE_URL"] = API_DATABASE_URL
    os.environ["FLEET_OIDC_ISSUER"] = f"{KEYCLOAK_BASE}/realms/fleet"
    os.environ["FLEET_OIDC_JWKS_URL"] = (
        f"{KEYCLOAK_BASE}/realms/fleet/protocol/openid-connect/certs"
    )
    os.environ["FLEET_OIDC_AUDIENCE"] = "fleet-api"
    os.environ["FLEET_REDIS_URL"] = "redis://localhost:6379/0"


def test_approve_path_opens_real_pr_on_sandbox() -> None:
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
            transport=transport, base_url="http://test", timeout=30
        ) as client:
            run_resp = await client.post(
                "/v1/dev-agent/runs",
                json={"ticket_key": "DEV-1"},
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
            assert approval["action"] == "github.open_pr"
            assert "branch_name" in approval["payload"]

            decide_resp = await client.post(
                f"/v1/approvals/{approval['id']}/decide",
                json={"decision": "approve"},
                headers={"Authorization": f"Bearer {approver_token}"},
            )
            assert decide_resp.status_code == 200, decide_resp.text
            assert decide_resp.json()["status"] == "approved"

        pr_number_holder: dict[str, int] = {}

        branch_name = approval["payload"]["branch_name"]
        owner = SANDBOX_REPO.split("/")[0]
        async with httpx.AsyncClient() as gh_client:
            resp = await gh_client.get(
                f"https://api.github.com/repos/{SANDBOX_REPO}/pulls",
                headers={
                    "Authorization": f"Bearer {SANDBOX_TOKEN}",
                    "Accept": "application/vnd.github+json",
                },
                params={"head": f"{owner}:{branch_name}"},
            )
            resp.raise_for_status()
            prs = resp.json()
            assert len(prs) == 1, f"expected exactly one PR for the branch, found {len(prs)}"
            pr_number_holder["number"] = prs[0]["number"]

        assert pr_number_holder["number"] > 0

    import asyncio

    asyncio.run(_run())


def test_reject_path_never_opens_a_pr() -> None:
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
            transport=transport, base_url="http://test", timeout=30
        ) as client:
            run_resp = await client.post(
                "/v1/dev-agent/runs",
                json={"ticket_key": "DEV-2"},
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
            branch_name = approval["payload"]["branch_name"]

            decide_resp = await client.post(
                f"/v1/approvals/{approval['id']}/decide",
                json={"decision": "reject"},
                headers={"Authorization": f"Bearer {approver_token}"},
            )
            assert decide_resp.status_code == 200, decide_resp.text
            assert decide_resp.json()["status"] == "rejected"

        async with httpx.AsyncClient() as gh_client:
            resp = await gh_client.get(
                f"https://api.github.com/repos/{SANDBOX_REPO}/pulls",
                headers={
                    "Authorization": f"Bearer {SANDBOX_TOKEN}",
                    "Accept": "application/vnd.github+json",
                },
                params={"head": f"{SANDBOX_REPO.split('/')[0]}:{branch_name}"},
            )
            resp.raise_for_status()
            assert resp.json() == []  # no PR opened for the rejected run's branch

    import asyncio

    asyncio.run(_run())


def test_unlabeled_ticket_is_blocked_before_any_branch_creation() -> None:
    _set_common_env()
    builder_token = _token("builder", "builder")

    async def _run() -> None:
        import fleet_api.db as fleet_db
        from fleet_api.app import create_app

        fleet_db._app_session_factory.cache_clear()

        app = create_app(with_middleware=False)
        transport = httpx.ASGITransport(app=app)

        async with httpx.AsyncClient(
            transport=transport, base_url="http://test", timeout=30
        ) as client:
            run_resp = await client.post(
                "/v1/dev-agent/runs",
                json={"ticket_key": "DEV-3"},  # unlabeled fixture ticket
                headers={"Authorization": f"Bearer {builder_token}"},
            )
            assert run_resp.status_code == 201, run_resp.text
            body = run_resp.json()
            assert body["status"] == "blocked"
            assert "agent-ok" in body["detail"]["reason"]

    import asyncio

    asyncio.run(_run())
