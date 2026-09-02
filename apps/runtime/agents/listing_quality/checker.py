"""Listing quality vision check -> machine-readable flags (task 11.1, dept
scenario 06).

A listing (photo + description + price, plus a price-index reference band) is
sent to the gateway's vision model, which returns a structured verdict: a set
of flag reason codes with per-flag explanations, or an empty set for a clean
listing. The agent is **flag-only** (dept scenario 06 guardrail): it never
unpublishes or rejects — it only routes flags into the human review queue, so
this module returns flags, never an enforcement action.

Reason codes are a fixed, closed vocabulary so reviewers can sort/filter and so
the eval set can assert on them deterministically. The model is told to use only
these codes; any code it invents is dropped (a model that flags for an unknown
reason is treated as not flagging on that axis, never as a new enforcement
path).
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Protocol

# Closed vocabulary of flag reason codes (dept scenario 06: "machine-readable
# reason codes for reviewer sorting").
REASON_CODES = frozenset(
    {
        "photo_description_mismatch",  # photo shows a different model/color than described
        "blurred_plate_missing",  # a visible license plate is NOT blurred (compliance)
        "prohibited_content",  # content not allowed in a listing
        "price_anomaly",  # price far outside the reference band for the segment
    }
)

_CODE_FENCE_RE = re.compile(r"^```(?:json)?\s*(.*?)\s*```$", re.DOTALL)


def _strip_code_fence(text: str) -> str:
    match = _CODE_FENCE_RE.match(text.strip())
    return match.group(1) if match else text


_SYSTEM_PROMPT = """You are a used-vehicle listing quality checker. You are given a \
listing photo, its text description, its asking price, and a reference price band \
for the segment. Check the listing on these axes and report problems ONLY.

You can NEVER approve, reject, unpublish, or edit a listing — you only report flags \
for a human reviewer.

Use ONLY these flag reason codes:
- "photo_description_mismatch": the photo clearly shows a different vehicle model or \
color than the description claims.
- "blurred_plate_missing": a license plate is visible AND readable (not blurred/masked) \
in the photo.
- "prohibited_content": the description or photo contains prohibited content \
(contact-info spam, offensive text, unrelated advertising).
- "price_anomaly": the asking price is far outside the given reference band \
(roughly <60% of the band low, or >160% of the band high).

Respond with exactly one JSON object and nothing else — no markdown, no commentary:
{
  "flags": [
    {"code": "<one of the codes above>", "reason": "<short human-readable explanation>"}
  ]
}
A clean listing has an empty "flags" array. Do not invent codes outside the list.
"""


class VisionClient(Protocol):
    async def utility(self, messages: list[dict[str, Any]], **kwargs: Any) -> Any: ...


class CheckParseError(Exception):
    """The model's listing-check response was malformed."""


@dataclass(frozen=True)
class Flag:
    code: str
    reason: str


@dataclass(frozen=True)
class ListingVerdict:
    flags: list[Flag] = field(default_factory=list)

    @property
    def codes(self) -> set[str]:
        return {f.code for f in self.flags}

    @property
    def is_clean(self) -> bool:
        return not self.flags


def _reference_band_text(band: dict[str, Any] | None) -> str:
    if not band:
        return "Reference price band: unavailable."
    return (
        f"Reference price band for this segment: "
        f"{band.get('low')}–{band.get('high')} {band.get('currency', 'TRY')} "
        f"(median {band.get('median')})."
    )


async def check_listing(
    *,
    image_base64: str,
    description: str,
    price: float,
    currency: str,
    reference_band: dict[str, Any] | None,
    vision_client: VisionClient,
    sensitivity: str = "internal",
    **meta: Any,
) -> ListingVerdict:
    """Run the vision check and return a structured, closed-vocabulary verdict.

    Public listing data is `internal` sensitivity (dept scenario 06), so this
    routes through the cloud vision (utility) lane by default.
    """
    user_content: list[dict[str, Any]] = [
        {
            "type": "text",
            "text": (
                f"Description: {description}\n"
                f"Asking price: {price} {currency}\n"
                f"{_reference_band_text(reference_band)}"
            ),
        },
        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_base64}"}},
    ]
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]
    response = await vision_client.utility(messages, sensitivity=sensitivity, **meta)

    try:
        parsed = json.loads(_strip_code_fence(response.content))
    except json.JSONDecodeError as exc:
        raise CheckParseError(f"model did not return valid JSON: {response.content!r}") from exc

    raw_flags = parsed.get("flags", [])
    if not isinstance(raw_flags, list):
        raise CheckParseError(f"'flags' is not a list: {raw_flags!r}")

    flags: list[Flag] = []
    for item in raw_flags:
        code = str(item.get("code", "")).strip()
        # Drop any code outside the closed vocabulary — an invented code never
        # becomes a new flag axis (flag-only, fixed-vocabulary guardrail).
        if code in REASON_CODES:
            flags.append(Flag(code=code, reason=str(item.get("reason", "")).strip()))

    return ListingVerdict(flags=flags)
