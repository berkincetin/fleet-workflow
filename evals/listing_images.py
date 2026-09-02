"""Synthetic listing-photo rendering for listing_quality evals (task 11.1,
dept scenario 06).

A real vision model cannot judge "the photo shows a blue car but the text says
red" from an abstract fixture — the signal has to be *in the image*. So each
fixture renders a stylised "listing photo" whose visible content encodes the
axis under test: the car's model/colour as drawn text on a coloured banner, and
a plate box that is either legible ("34 ABC 123") or masked ("[BLURRED]"). The
real gateway vision model reads these exactly as it would read a real photo's
salient features, so the eval exercises the real check_listing path
deterministically rather than mocking the model.
"""

from __future__ import annotations

import base64
import io

from PIL import Image, ImageDraw, ImageFont

_FONT_PATHS = [
    "C:/Windows/Fonts/arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
]

_COLOR_RGB = {
    "red": (200, 40, 40),
    "blue": (40, 70, 200),
    "black": (30, 30, 30),
    "white": (235, 235, 235),
    "silver": (170, 170, 175),
}


def _font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for p in _FONT_PATHS:
        try:
            return ImageFont.truetype(p, size)
        except OSError:
            continue
    return ImageFont.load_default(size=size)


def render_listing_photo_base64(
    *,
    model: str,
    color: str,
    plate_visible: bool,
    prohibited_banner: str | None = None,
) -> str:
    """Render a stylised listing photo, base64 PNG.

    - A coloured body banner + the model/colour drawn on it (what the vision
      model 'sees' the car as).
    - A plate box that is either a legible plate string or a masked box.
    - An optional prohibited-content banner (e.g. a phone number / spam).
    """
    w, h = 640, 400
    img = Image.new("RGB", (w, h), color=(245, 245, 245))
    draw = ImageDraw.Draw(img)

    # Car body: a big rounded rectangle in the actual colour.
    body_rgb = _COLOR_RGB.get(color.lower(), (120, 120, 120))
    draw.rounded_rectangle([40, 90, 600, 300], radius=40, fill=body_rgb)
    draw.text((60, 110), f"{color.upper()} {model.upper()}", fill="white", font=_font(34))

    # Plate box.
    draw.rectangle([240, 250, 400, 290], fill=(255, 255, 255), outline=(0, 0, 0), width=2)
    plate_text = "34 ABC 123" if plate_visible else "[BLURRED]"
    draw.text((250, 258), plate_text, fill="black", font=_font(22))

    if prohibited_banner:
        draw.rectangle([0, 320, w, 380], fill=(255, 230, 120))
        draw.text((20, 335), prohibited_banner, fill="black", font=_font(22))

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("ascii")
