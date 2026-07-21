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

    async def reasoning(self, messages, **_kwargs):  # type: ignore[no-untyped-def]
        self.calls.append(messages)
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
