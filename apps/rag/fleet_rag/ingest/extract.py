"""Text extraction from uploaded documents (task 3.1: extract step).

Dispatches by file extension. PDFs/docx/txt with a real text layer are
extracted directly; PDFs without one and all raw images are flagged
`needs_ocr` so the pipeline routes them to the OCR step (vision-LLM primary,
tesseract fallback — ocr.py).
"""

from __future__ import annotations

import io
from dataclasses import dataclass

from docx import Document as DocxDocument
from pypdf import PdfReader

_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".gif", ".webp"}


class UnsupportedFileType(ValueError):
    def __init__(self, extension: str) -> None:
        super().__init__(f"unsupported file type: {extension}")


@dataclass(frozen=True)
class ExtractResult:
    text: str
    needs_ocr: bool


def _extension(filename: str) -> str:
    dot = filename.rfind(".")
    return filename[dot:].lower() if dot != -1 else ""


def _extract_pdf(data: bytes) -> ExtractResult:
    reader = PdfReader(io.BytesIO(data))
    pages_text = [page.extract_text() or "" for page in reader.pages]
    text = "\n\n".join(t.strip() for t in pages_text if t.strip())
    return ExtractResult(text=text, needs_ocr=not text.strip())


def _extract_docx(data: bytes) -> ExtractResult:
    doc = DocxDocument(io.BytesIO(data))
    text = "\n\n".join(p.text for p in doc.paragraphs if p.text.strip())
    return ExtractResult(text=text, needs_ocr=False)


def _extract_txt(data: bytes) -> ExtractResult:
    return ExtractResult(text=data.decode("utf-8", errors="replace"), needs_ocr=False)


def extract_text(data: bytes, *, filename: str) -> ExtractResult:
    """Extract plain text from an uploaded file. Raises UnsupportedFileType."""
    ext = _extension(filename)
    if ext == ".pdf":
        return _extract_pdf(data)
    if ext == ".docx":
        return _extract_docx(data)
    if ext == ".txt":
        return _extract_txt(data)
    if ext in _IMAGE_EXTENSIONS:
        return ExtractResult(text="", needs_ocr=True)
    raise UnsupportedFileType(ext)
