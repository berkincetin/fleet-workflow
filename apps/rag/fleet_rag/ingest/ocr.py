"""OCR step: vision-LLM primary, tesseract fallback (TRD §3 tech stack, task 3.1).

Layout-aware extraction via the gateway's reasoning model is tried first;
any failure (gateway error, refusal, empty result) falls back to local
Tesseract (`tur` + `eng`) so ingestion never hard-fails on a scanned page.
Both the vision client and the tesseract call are injected, keeping this
module unit-testable without network or a local tesseract binary — the real
wiring (LLMClient, pytesseract) lives in the caller (pipeline.py).
"""

from __future__ import annotations

import base64
from dataclasses import dataclass
from typing import Any, Protocol


class VisionClient(Protocol):
    async def reasoning(
        self, messages: list[dict[str, Any]], **kwargs: Any
    ) -> Any: ...


@dataclass(frozen=True)
class OcrResult:
    text: str
    source: str  # "vision-llm" | "tesseract" | "none"


_PROMPT = (
    "Extract all text from this image exactly as it appears, preserving "
    "reading order. Reply with only the extracted text, no commentary."
)


async def _try_vision(image_bytes: bytes, vision_client: VisionClient) -> str:
    b64 = base64.b64encode(image_bytes).decode("ascii")
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": _PROMPT},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
            ],
        }
    ]
    response = await vision_client.reasoning(messages, sensitivity="internal")
    return (response.content or "").strip()


async def ocr_image(
    image_bytes: bytes,
    *,
    vision_client: VisionClient,
    tesseract_fn: Any,
) -> OcrResult:
    """Run vision-LLM OCR; fall back to `tesseract_fn(image_bytes)` on failure/empty."""
    try:
        text = await _try_vision(image_bytes, vision_client)
        if text:
            return OcrResult(text=text, source="vision-llm")
    except Exception:
        pass

    try:
        text = tesseract_fn(image_bytes)
        if text:
            return OcrResult(text=text, source="tesseract")
    except Exception:
        pass

    return OcrResult(text="", source="none")
