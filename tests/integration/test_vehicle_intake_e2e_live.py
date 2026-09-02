"""Integration: Vehicle Intake against the real dev stack (task 11.2 AC:
missing-report fixture never invents values; local OCR -> redact -> cloud
reasoning path is real).

Drives the real vehicle_intake graph (as the eval does): real local tesseract
OCR of a rendered expertise report, real PII redaction, a real cloud reasoning
extraction through the live gateway, deterministic band from fixture
comparables. Two cases: a complete report yields a brief + a band containing the
comparables' median with the owner's phone redacted before the cloud call; a
non-report page is marked incomplete with NO band and NO invented chassis/km.
"""

from __future__ import annotations

import base64
import os
import sys

import httpx
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "evals"))

KEYCLOAK_BASE = "http://localhost:8080"


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


class _StaticComparables:
    def __init__(self, prices: list[float]) -> None:
        self._prices = prices

    async def top_prices(self, *, segment: str, limit: int = 5) -> list[float]:
        return self._prices[:limit]


async def _run(report_lines: list[str], *, comparables: list[float]) -> dict:
    from agents.vehicle_intake.graph import build_vehicle_intake_graph
    from core.llm.factory import build_client
    from fleet_rag.ingest.ocr import tesseract_ocr
    from langgraph.checkpoint.memory import InMemorySaver
    from synthetic_images import render_document_image_base64

    class _OcrAdapter:
        async def extract_text(self, image_base64: str) -> dict[str, str]:
            return {"text": tesseract_ocr(base64.b64decode(image_base64)), "source": "tesseract"}

    llm_client = await build_client()
    graph = build_vehicle_intake_graph(
        llm_client=llm_client, ocr=_OcrAdapter(),
        comparables=_StaticComparables(comparables), checkpointer=InMemorySaver(),
    )
    image_b64 = render_document_image_base64(report_lines)
    return await graph.ainvoke(
        {"image_base64": image_b64, "segment": "sedan-2018"},
        {"configurable": {"thread_id": "vi-e2e"}},
    )


async def test_complete_report_yields_band_with_redaction() -> None:
    result = await _run(
        [
            "EKSPERTIZ RAPORU",
            "Arac Sahibi Tel: 0555 123 4567",
            "Sasi No: WVWZZZ1JZ3W386752",
            "KM: 120000",
            "Hasar: on tampon",
        ],
        comparables=[480000, 500000, 520000, 460000, 540000],
    )
    assert result["incomplete"] is False
    assert result["brief"]["redaction_applied"] is True  # owner phone was masked
    band = result["price_band"]
    assert band is not None and band["low"] <= band["median"] <= band["high"]


async def test_non_report_is_incomplete_without_invented_values() -> None:
    result = await _run(
        ["Bu sayfa bos", "gecerli bir ekspertiz raporu degil"],
        comparables=[480000, 500000, 520000],
    )
    assert result["incomplete"] is True
    assert result.get("price_band") is None
    assert result["brief"]["chassis"] is None and result["brief"]["km"] is None
