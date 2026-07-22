"""agents.invoice_agent.extractor: OCR text -> structured invoice fields
(task 6.3, dept scenario 04 "extracted fields" step).
"""

from __future__ import annotations

import pytest
from agents.invoice_agent.extractor import ExtractionParseError, extract_invoice_fields


class _FakeLLM:
    def __init__(self, content: str) -> None:
        self.content = content
        self.calls: list[list[dict[str, object]]] = []

    async def reasoning(self, messages: list[dict[str, object]], **kwargs: object) -> object:
        self.calls.append(messages)

        class _Resp:
            content = self.content

        return _Resp()


_VALID_JSON = (
    '{"vendor": "Acme Tedarik A.S.", "po_number": "PO-1001", '
    '"amount": 1250.0, "currency": "TRY"}'
)


async def test_extract_invoice_fields_parses_valid_response() -> None:
    llm = _FakeLLM(_VALID_JSON)
    fields = await extract_invoice_fields(ocr_text="invoice text", llm_client=llm)
    assert fields.vendor == "Acme Tedarik A.S."
    assert fields.po_number == "PO-1001"
    assert fields.amount == 1250.0
    assert fields.currency == "TRY"


async def test_extract_invoice_fields_uses_reasoning_tier() -> None:
    calls = {"reasoning": False}

    class _TierLLM:
        async def reasoning(self, messages: list[dict[str, object]], **kwargs: object) -> object:
            calls["reasoning"] = True

            class _Resp:
                content = _VALID_JSON

            return _Resp()

        async def utility(self, messages: list[dict[str, object]], **kwargs: object) -> object:
            raise AssertionError("extractor must not call utility()")

    await extract_invoice_fields(ocr_text="x", llm_client=_TierLLM())
    assert calls["reasoning"] is True


async def test_extract_invoice_fields_strips_markdown_code_fence() -> None:
    llm = _FakeLLM(f"```json\n{_VALID_JSON}\n```")
    fields = await extract_invoice_fields(ocr_text="x", llm_client=llm)
    assert fields.po_number == "PO-1001"


async def test_extract_invoice_fields_raises_on_malformed_json() -> None:
    llm = _FakeLLM("not json")
    with pytest.raises(ExtractionParseError):
        await extract_invoice_fields(ocr_text="x", llm_client=llm)


async def test_extract_invoice_fields_raises_on_missing_field() -> None:
    llm = _FakeLLM('{"vendor": "x"}')
    with pytest.raises(ExtractionParseError):
        await extract_invoice_fields(ocr_text="x", llm_client=llm)


async def test_extract_invoice_fields_raises_on_non_numeric_amount() -> None:
    llm = _FakeLLM(
        '{"vendor": "x", "po_number": "PO-1001", "amount": "not a number", "currency": "TRY"}'
    )
    with pytest.raises(ExtractionParseError):
        await extract_invoice_fields(ocr_text="x", llm_client=llm)


async def test_extract_invoice_fields_prompt_includes_ocr_text() -> None:
    llm = _FakeLLM(_VALID_JSON)
    await extract_invoice_fields(ocr_text="Invoice #4471 from Acme", llm_client=llm)
    user_message = llm.calls[0][-1]["content"]
    assert "Invoice #4471 from Acme" in user_message
