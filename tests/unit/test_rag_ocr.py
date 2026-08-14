"""OCR step: vision-LLM primary, tesseract fallback (task 3.1).

The vision-LLM call goes through the Sprint-2 gateway client (injected here as
a fake so this test needs no network); the tesseract fallback is also
injected so the test needs no local tesseract binary. Only ocr_image's own
dispatch/fallback logic is under test.
"""

from __future__ import annotations

import pytest
from fleet_rag.ingest.ocr import OcrResult, ocr_image


class _FakeLLMResponse:
    def __init__(self, content: str) -> None:
        self.content = content


class _FakeVisionClient:
    def __init__(self, *, text: str | None = None, error: Exception | None = None) -> None:
        self._text = text
        self._error = error
        self.calls: list[list[dict]] = []
        self.call_kwargs: list[dict] = []

    async def reasoning(self, messages, **kwargs):  # type: ignore[no-untyped-def]
        self.calls.append(messages)
        self.call_kwargs.append(kwargs)
        if self._error:
            raise self._error
        return _FakeLLMResponse(self._text or "")


@pytest.mark.asyncio
async def test_ocr_uses_vision_llm_when_it_succeeds() -> None:
    vision = _FakeVisionClient(text="extracted invoice text")
    result = await ocr_image(b"\x89PNG", vision_client=vision, tesseract_fn=lambda _b: "unused")
    assert isinstance(result, OcrResult)
    assert result.text == "extracted invoice text"
    assert result.source == "vision-llm"
    assert len(vision.calls) == 1


@pytest.mark.asyncio
async def test_ocr_falls_back_to_tesseract_when_vision_llm_errors() -> None:
    vision = _FakeVisionClient(error=RuntimeError("gateway down"))
    result = await ocr_image(
        b"\x89PNG", vision_client=vision, tesseract_fn=lambda _b: "tesseract text"
    )
    assert result.text == "tesseract text"
    assert result.source == "tesseract"


@pytest.mark.asyncio
async def test_ocr_falls_back_to_tesseract_when_vision_llm_returns_empty() -> None:
    vision = _FakeVisionClient(text="")
    result = await ocr_image(
        b"\x89PNG", vision_client=vision, tesseract_fn=lambda _b: "tesseract text"
    )
    assert result.text == "tesseract text"
    assert result.source == "tesseract"


@pytest.mark.asyncio
async def test_ocr_both_fail_returns_empty_result_not_raise() -> None:
    vision = _FakeVisionClient(error=RuntimeError("gateway down"))

    def _boom(_b: bytes) -> str:
        raise RuntimeError("tesseract not installed")

    result = await ocr_image(b"\x89PNG", vision_client=vision, tesseract_fn=_boom)
    assert result.text == ""
    assert result.source == "none"


@pytest.mark.asyncio
async def test_ocr_defaults_to_internal_and_still_tries_vision_llm() -> None:
    """No sensitivity passed -> same as pre-task-8.2 behavior (internal)."""
    vision = _FakeVisionClient(text="extracted text")
    result = await ocr_image(b"\x89PNG", vision_client=vision, tesseract_fn=lambda _b: "unused")
    assert result.source == "vision-llm"
    assert len(vision.calls) == 1


@pytest.mark.asyncio
async def test_ocr_skips_vision_llm_entirely_for_confidential_sensitivity() -> None:
    """TRD §8 / dept scenarios 04+05: raw confidential/pii images (invoices,
    CVs) must never reach the cloud vision-LLM, even if it would succeed —
    the vision client must not be called at all."""
    vision = _FakeVisionClient(text="this would leak PII to the cloud")
    result = await ocr_image(
        b"\x89PNG",
        vision_client=vision,
        tesseract_fn=lambda _b: "tesseract text",
        sensitivity="confidential",
    )
    assert result.text == "tesseract text"
    assert result.source == "tesseract"
    assert vision.calls == []


@pytest.mark.asyncio
async def test_ocr_skips_vision_llm_entirely_for_pii_sensitivity() -> None:
    vision = _FakeVisionClient(text="this would leak PII to the cloud")
    result = await ocr_image(
        b"\x89PNG",
        vision_client=vision,
        tesseract_fn=lambda _b: "tesseract text",
        sensitivity="pii",
    )
    assert result.source == "tesseract"
    assert vision.calls == []


@pytest.mark.asyncio
async def test_ocr_confidential_with_no_local_fallback_returns_empty_not_cloud() -> None:
    """Even if the local tesseract fallback fails/is unavailable, a
    confidential/pii request must never fall through to the cloud vision-LLM."""
    vision = _FakeVisionClient(text="this would leak PII to the cloud")

    def _boom(_b: bytes) -> str:
        raise RuntimeError("tesseract not installed")

    result = await ocr_image(
        b"\x89PNG", vision_client=vision, tesseract_fn=_boom, sensitivity="confidential"
    )
    assert result.text == ""
    assert result.source == "none"
    assert vision.calls == []


@pytest.mark.asyncio
async def test_ocr_passes_real_sensitivity_to_vision_client_not_hardcoded_internal() -> None:
    """Sprint-3 code hardcoded sensitivity='internal' on every vision-LLM call
    regardless of the caller's real sensitivity; the gateway's own routing
    (core.llm.routing.select_model) is the actual enforcement point, but it can
    only enforce what it's told — this asserts ocr_image tells it the truth."""
    vision = _FakeVisionClient(text="extracted text")
    await ocr_image(
        b"\x89PNG", vision_client=vision, tesseract_fn=lambda _b: "unused", sensitivity="public"
    )
    assert vision.call_kwargs[0]["sensitivity"] == "public"

