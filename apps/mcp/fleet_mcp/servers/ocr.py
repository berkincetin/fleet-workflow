"""ocr MCP tool: wraps fleet_rag.ingest.ocr for tool-calling agents (task 5.1).

The vision-LLM/tesseract-fallback logic already exists (Sprint 3, task 3.1)
and stays there — this module only adapts it to the MCP call shape (base64
image bytes in, {text, source} out) and declares it `read` risk_class (it
extracts text, it never writes anything).
"""

from __future__ import annotations

import base64
from collections.abc import Callable
from typing import Any

from fleet_mcp.base import ToolContract
from fleet_rag.ingest.ocr import VisionClient, ocr_image

OCR_INPUT_SCHEMA = {
    "type": "object",
    "properties": {"image_base64": {"type": "string"}},
    "required": ["image_base64"],
    "additionalProperties": False,
}


def build_ocr_tool(
    *,
    vision_client: VisionClient,
    tesseract_fn: Callable[[bytes], str],
    sensitivity: str = "internal",
) -> Callable[..., Any]:
    async def _ocr(image_base64: str) -> dict[str, str]:
        image_bytes = base64.b64decode(image_base64)
        result = await ocr_image(
            image_bytes,
            vision_client=vision_client,
            tesseract_fn=tesseract_fn,
            sensitivity=sensitivity,
        )
        return {"text": result.text, "source": result.source}

    return _ocr


def build_ocr_contract(
    *,
    vision_client: VisionClient,
    tesseract_fn: Callable[[bytes], str],
    sensitivity: str = "internal",
) -> ToolContract:
    return ToolContract(
        name="ocr.extract_text",
        risk_class="read",
        description="Extract text from an image (vision-LLM primary, tesseract fallback).",
        input_schema=OCR_INPUT_SCHEMA,
        fn=build_ocr_tool(
            vision_client=vision_client, tesseract_fn=tesseract_fn, sensitivity=sensitivity
        ),
    )
