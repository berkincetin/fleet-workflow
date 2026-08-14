"""fleet_mcp.servers.ocr: MCP wrapper around fleet_rag.ingest.ocr (task 5.1).

Thin adapter — the actual vision-LLM/tesseract logic already exists and is
tested in tests/unit/test_rag_ocr.py (Sprint 3); this module just exposes it
as a `read` MCP tool contract (base64 image in, extracted text out).
"""

from __future__ import annotations

from fleet_mcp.servers.ocr import build_ocr_tool


class _StubVisionClient:
    async def reasoning(self, messages: list[dict[str, object]], **kwargs: object) -> object:
        class _Resp:
            content = "extracted text"

        return _Resp()


async def test_ocr_tool_extracts_text_from_base64_image() -> None:
    import base64

    tool = build_ocr_tool(vision_client=_StubVisionClient(), tesseract_fn=lambda b: "")
    result = await tool(image_base64=base64.b64encode(b"fake-image-bytes").decode("ascii"))
    assert result["text"] == "extracted text"
    assert result["source"] == "vision-llm"


async def test_ocr_tool_falls_back_to_tesseract_on_vision_failure() -> None:
    import base64

    class _FailingVisionClient:
        async def reasoning(self, messages: list[dict[str, object]], **kwargs: object) -> object:
            raise RuntimeError("gateway down")

    tool = build_ocr_tool(
        vision_client=_FailingVisionClient(), tesseract_fn=lambda b: "tesseract text"
    )
    result = await tool(image_base64=base64.b64encode(b"fake").decode("ascii"))
    assert result["text"] == "tesseract text"
    assert result["source"] == "tesseract"


async def test_ocr_tool_skips_cloud_vision_for_confidential_sensitivity() -> None:
    """Invoice/CV OCR (dept scenarios 04/05) must bind sensitivity="confidential"/
    "pii" and never let a raw sensitive image reach the cloud vision-LLM."""
    import base64

    class _ShouldNotBeCalledVisionClient:
        async def reasoning(self, messages: list[dict[str, object]], **kwargs: object) -> object:
            raise AssertionError("vision-LLM must not be called for confidential sensitivity")

    tool = build_ocr_tool(
        vision_client=_ShouldNotBeCalledVisionClient(),
        tesseract_fn=lambda b: "tesseract text",
        sensitivity="confidential",
    )
    result = await tool(image_base64=base64.b64encode(b"fake").decode("ascii"))
    assert result["text"] == "tesseract text"
    assert result["source"] == "tesseract"
