"""OCR step: vision-LLM primary, tesseract fallback (TRD §3 tech stack, task 3.1);
sensitivity-gated local-only lane for confidential/pii raw documents (TRD §8,
task 8.2 fix).

Layout-aware extraction via the gateway's reasoning model is tried first for
public/internal-sensitivity images; any failure (gateway error, refusal, empty
result) falls back to local Tesseract (`tur` + `eng`) so ingestion never
hard-fails on a scanned page. For `confidential`/`pii` images (raw invoices,
CVs — dept scenarios 04/05 both spell out "OCR path: local (Tesseract)... cloud
vision only for pre-redacted or non-sensitive docs"), the vision-LLM step is
skipped entirely: no cloud model in the registry is cleared above `internal`
(gateway/litellm/config.yaml), and the raw image predates any PII redaction
(redaction runs on the *extracted text*, in pii.py, downstream of OCR), so
attempting a cloud vision call here would leak unredacted PII/financial
identifiers before the pipeline ever gets a chance to redact them.

Both the vision client and the tesseract call are injected, keeping this
module unit-testable without network or a local tesseract binary; `tesseract_ocr`
below is the one real pytesseract implementation, shared by every caller
(worker.py, fleet_mcp.servers.ocr, the invoice_agent API routers) instead of
each defining or stubbing its own.
"""

from __future__ import annotations

import base64
import io
from dataclasses import dataclass
from typing import Any, Protocol

from core.llm.routing import Sensitivity


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

# confidential and pii raw images never reach the cloud vision-LLM (TRD §8).
_LOCAL_ONLY_FLOOR = Sensitivity.CONFIDENTIAL


def tesseract_ocr(image_bytes: bytes) -> str:
    """Real local OCR (pytesseract, tur+eng) — the local-lane implementation
    every caller should pass as `tesseract_fn` in production."""
    import pytesseract
    from PIL import Image

    image = Image.open(io.BytesIO(image_bytes))
    text: str = pytesseract.image_to_string(image, lang="tur+eng")
    return text


async def _try_vision(image_bytes: bytes, vision_client: VisionClient, *, sensitivity: str) -> str:
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
    response = await vision_client.reasoning(messages, sensitivity=sensitivity)
    return (response.content or "").strip()


async def ocr_image(
    image_bytes: bytes,
    *,
    vision_client: VisionClient,
    tesseract_fn: Any,
    sensitivity: str = "internal",
) -> OcrResult:
    """Run vision-LLM OCR (skipped for confidential/pii); fall back to (or, for
    confidential/pii, go straight to) `tesseract_fn(image_bytes)`."""
    local_only = Sensitivity.parse(sensitivity) >= _LOCAL_ONLY_FLOOR

    if not local_only:
        try:
            text = await _try_vision(image_bytes, vision_client, sensitivity=sensitivity)
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
