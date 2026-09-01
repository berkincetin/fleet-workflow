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


_MARGIN = 20


def render_document_image_base64(
    lines: list[str], *, size: tuple[int, int] | None = None, font_size: int = 28
) -> str:
    """Render `lines` as a simple white-background "document scan" PNG, base64-encoded.

    `size` defaults to a canvas grown to fit `lines`. It used to default to a
    fixed (900, 260), which silently clipped any document past its 5th line:
    with line_height = font_size + 20 = 48 and a top margin of 20, line 6 drew
    at y=260 — exactly the canvas bottom edge, i.e. off-image entirely. The
    invoice fixtures are 5 lines so they fit, which is why this stayed latent
    until task 8.5's 6-line CV fixtures lost their `Yetenekler:` (skills) line
    in 8/8 cases and every skills assertion failed. Callers may still pass an
    explicit `size`; it is honoured as-is.
    """
    font = _load_readable_font(font_size)
    line_height = font_size + 20
    if size is None:
        height = _MARGIN * 2 + max(len(lines), 1) * line_height
        size = (900, height)
    img = Image.new("RGB", size, color="white")
    draw = ImageDraw.Draw(img)
    for i, line in enumerate(lines):
        draw.text((_MARGIN, _MARGIN + i * line_height), line, fill="black", font=font)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("ascii")
