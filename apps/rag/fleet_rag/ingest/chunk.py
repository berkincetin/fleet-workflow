"""Structure-aware chunking + content-hash dedup (TRD Sprint 3 task 3.1).

Splits extracted text on paragraph boundaries, packing paragraphs into chunks
up to a token budget (approximated by whitespace-split word count — good
enough for chunk sizing without pulling in a tokenizer here). Each chunk
carries a stable sha256 of its content so the pipeline can dedup against
already-embedded chunks and skip re-embedding on re-upload.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass


@dataclass(frozen=True)
class Chunk:
    content: str
    content_sha256: str


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def chunk_text(text: str, *, max_tokens: int = 400) -> list[Chunk]:
    """Pack paragraphs into chunks of at most `max_tokens` words each."""
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    if not paragraphs:
        return []

    chunks: list[Chunk] = []
    current: list[str] = []
    current_len = 0

    def _flush() -> None:
        if current:
            content = "\n\n".join(current)
            chunks.append(Chunk(content=content, content_sha256=_sha256(content)))

    for para in paragraphs:
        words = para.split()
        # A single paragraph longer than the budget gets split on its own.
        if len(words) > max_tokens:
            _flush()
            current = []
            current_len = 0
            for i in range(0, len(words), max_tokens):
                piece = " ".join(words[i : i + max_tokens])
                chunks.append(Chunk(content=piece, content_sha256=_sha256(piece)))
            continue

        if current_len + len(words) > max_tokens and current:
            _flush()
            current = []
            current_len = 0

        current.append(para)
        current_len += len(words)

    _flush()
    return chunks


def dedup_chunks(chunks: list[Chunk], *, existing_hashes: set[str]) -> list[Chunk]:
    """Drop chunks whose content hash is already embedded (0 new-embedding re-upload)."""
    return [c for c in chunks if c.content_sha256 not in existing_hashes]
