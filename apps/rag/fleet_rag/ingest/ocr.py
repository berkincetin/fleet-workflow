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
import os
import shutil
import sys
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


_WINDOWS_TESSERACT_DEFAULT = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


def _resolve_tesseract_cmd() -> str | None:
    """Locate the tesseract binary when it is installed but not on PATH.

    The Windows installer does not add itself to PATH, so every shell that
    forgets to export it fails the local-OCR evals with a bare
    `TesseractNotFoundError` — hit in Sprint 11 and twice more in Sprint 12.
    `FLEET_TESSERACT_CMD` wins if set; otherwise the standard Windows install
    location is used when it exists. Returns None on a PATH-based install, in
    which case pytesseract's own default is left alone.
    """
    explicit = os.environ.get("FLEET_TESSERACT_CMD")
    if explicit:
        return explicit
    if sys.platform == "win32" and os.path.exists(_WINDOWS_TESSERACT_DEFAULT):
        return _WINDOWS_TESSERACT_DEFAULT
    return None


def tesseract_ocr(image_bytes: bytes) -> str:
    """Real local OCR (pytesseract, tur+eng) — the local-lane implementation
    every caller should pass as `tesseract_fn` in production."""
    import pytesseract
    from PIL import Image

    if shutil.which("tesseract") is None:
        resolved = _resolve_tesseract_cmd()
        if resolved is not None:
            pytesseract.pytesseract.tesseract_cmd = resolved

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
