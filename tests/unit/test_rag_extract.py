"""Text extraction from pdf/docx/txt (task 3.1). Extraction is dispatched by
file extension; OCR (vision-LLM/tesseract) is a separate fallback path for
scanned images, tested in test_rag_ocr.py.
"""

from __future__ import annotations

import io

import pytest
from docx import Document as DocxDocument
from fleet_rag.ingest.extract import UnsupportedFileType, extract_text
from pypdf import PdfWriter


def _make_pdf_bytes(text: str) -> bytes:
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()


def _make_docx_bytes(paragraphs: list[str]) -> bytes:
    doc = DocxDocument()
    for p in paragraphs:
        doc.add_paragraph(p)
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def test_extract_txt_returns_decoded_text() -> None:
    result = extract_text(b"hello world", filename="notes.txt")
    assert result.text == "hello world"
    assert result.needs_ocr is False


def test_extract_docx_returns_paragraph_text() -> None:
    data = _make_docx_bytes(["First paragraph.", "Second paragraph."])
    result = extract_text(data, filename="report.docx")
    assert "First paragraph." in result.text
    assert "Second paragraph." in result.text
    assert result.needs_ocr is False


def test_extract_pdf_with_no_text_layer_flags_needs_ocr() -> None:
    # A blank page has no extractable text layer -> OCR fallback is required.
    data = _make_pdf_bytes("")
    result = extract_text(data, filename="scan.pdf")
    assert result.needs_ocr is True


def test_extract_image_always_flags_needs_ocr() -> None:
    result = extract_text(b"\x89PNG\r\n", filename="photo.png")
    assert result.needs_ocr is True
    assert result.text == ""


def test_extract_unsupported_extension_raises() -> None:
    with pytest.raises(UnsupportedFileType, match="xyz"):
        extract_text(b"data", filename="file.xyz")
