"""Shared synthetic document image rendering for evals/rehearsals that need a
realistic-enough "scanned page" to exercise the real OCR pipeline (task 8.1
local-lane rehearsal; also used by invoice_agent's eval fixtures, task 6.3).

Pillow's `ImageFont.load_default()` (the implicit choice before this module
existed) is a tiny, low-fidelity bitmap font — real tesseract OCR against it
reliably misreads digits and drops Turkish diacritics entirely (confirmed
empirically during task 8.1's rehearsal: "1250.00" -> "1260.00", "Şirketler"
-> "nirketler"). This module tries a real antialiased system TTF with proper
Turkish glyph coverage first (Windows' Arial, common Linux DejaVuSans/Liberation
paths), falling back to Pillow's scalable `load_default(size=...)` (available
since Pillow 10.1) only if none exist — correct ASCII/numeric OCR either way,
better Turkish-diacritic OCR when a real system font is found.
"""

from __future__ import annotations

import base64
import io

from PIL import Image, ImageDraw, ImageFont

_CANDIDATE_FONT_PATHS = [
    "C:/Windows/Fonts/arial.ttf",  # Windows
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # Debian/Ubuntu (fonts-dejavu-core)
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",  # RHEL/Fedora
    "/System/Library/Fonts/Supplemental/Arial.ttf",  # macOS
]


def _load_readable_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for path in _CANDIDATE_FONT_PATHS:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default(size=size)


def render_document_image_base64(
    lines: list[str], *, size: tuple[int, int] = (900, 260), font_size: int = 28
) -> str:
    """Render `lines` as a simple white-background "document scan" PNG, base64-encoded."""
    font = _load_readable_font(font_size)
    img = Image.new("RGB", size, color="white")
    draw = ImageDraw.Draw(img)
    line_height = font_size + 20
    for i, line in enumerate(lines):
        draw.text((20, 20 + i * line_height), line, fill="black", font=font)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("ascii")
