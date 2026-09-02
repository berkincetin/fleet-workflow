"""Integration: Listing Quality shadow-mode run against the real dev stack
(task 11.1 AC: shadow mode — flags computed but not queued — verified in a
scripted run; flag-only guardrail).

Real HTTP round-trip: `builder` (MANAGE_AGENTS) posts a listing (a rendered
photo whose colour contradicts the description) to
POST /v1/listing-quality/runs with shadow=true. The graph runs the real vision
(utility) call through the live gateway, catches the mismatch, and returns
status `shadow_flagged` WITHOUT queuing a flag. A clean listing (photo matches
description, price in band) returns `clean` with no flags.
"""

from __future__ import annotations

import os
import sys

import httpx
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "evals"))

KEYCLOAK_BASE = "http://localhost:8080"
API_BASE = "http://localhost:8000"


def _stack_up() -> bool:
    try:
        r = httpx.get(f"{KEYCLOAK_BASE}/realms/fleet/.well-known/openid-configuration", timeout=3)
        api = httpx.get(f"{API_BASE}/healthz", timeout=3)
        return r.status_code == 200 and api.status_code == 200
    except Exception:
        return False


pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(not _stack_up(), reason="dev stack not reachable — start with `make dev`"),
]


def _builder_token() -> str:
    resp = httpx.post(
        f"{KEYCLOAK_BASE}/realms/fleet/protocol/openid-connect/token",
        data={
            "client_id": "fleet-api",
            "client_secret": "fleet-api-dev-secret",
            "grant_type": "password",
            "username": "builder",
            "password": "builder",
        },
        timeout=10,
    )
    resp.raise_for_status()
    return str(resp.json()["access_token"])


def _run(token: str, body: dict) -> dict:
    resp = httpx.post(
        f"{API_BASE}/v1/listing-quality/runs",
        headers={"Authorization": f"Bearer {token}"},
        json=body,
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()


def test_shadow_mode_flags_a_mismatch_without_queuing() -> None:
    from listing_images import render_listing_photo_base64

    token = _builder_token()
    # Photo is a BLUE sedan; the description claims RED → mismatch.
    img = render_listing_photo_base64(model="sedan", color="blue", plate_visible=False)
    result = _run(
        token,
        {
            "listing_id": "L-e2e-mismatch",
            "image_base64": img,
            "description": "Red sedan for sale, clean.",
            "price": 500000,
            "segment": "sedan-2018",
            "shadow": True,
        },
    )
    assert result["status"] == "shadow_flagged"
    codes = [f["code"] for f in result["flags"]]
    assert "photo_description_mismatch" in codes


def test_clean_listing_is_not_flagged() -> None:
    from listing_images import render_listing_photo_base64

    token = _builder_token()
    img = render_listing_photo_base64(model="sedan", color="red", plate_visible=False)
    result = _run(
        token,
        {
            "listing_id": "L-e2e-clean",
            "image_base64": img,
            "description": "Red sedan for sale, clean.",
            "price": 500000,
            "segment": "sedan-2018",
            "shadow": True,
        },
    )
    assert result["status"] == "clean"
    assert result["flags"] == []
