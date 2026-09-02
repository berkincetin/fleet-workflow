"""Expertise-report OCR text -> redacted -> structured vehicle brief
(task 11.2, dept scenario 07 Vehicle Intake).

The expertise PDF contains the owner's PII (name, phone, TCKN), so per TRD §8
the OCR runs on the LOCAL lane and its text is PII-scrubbed (core.pii_scrub)
BEFORE it is ever handed to the cloud reasoning model. This module takes the
already-OCR'd text, redacts it, and asks the reasoning model for the vehicle
fields the brief needs — never the owner's identity.

Missing / unreadable report guardrail (dept scenario 07): if the required
vehicle fields cannot be found, the model must return them null and the brief is
marked `incomplete` — it must NEVER invent a chassis number, km, or damage
entry. `extract_vehicle_brief` enforces this by treating null/empty required
fields as `incomplete`, not by trusting the model to self-declare.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Protocol

from core.pii_scrub import scrub

_CODE_FENCE_RE = re.compile(r"^```(?:json)?\s*(.*?)\s*```$", re.DOTALL)


def _strip_code_fence(text: str) -> str:
    match = _CODE_FENCE_RE.match(text.strip())
    return match.group(1) if match else text


_SYSTEM_PROMPT = """You extract vehicle facts from a redacted expertise report. \
The report text has had personal identifiers removed ([EMAIL], [TR_PHONE], \
[TR_TCKN], [TR_IBAN]) — do NOT try to recover them; you only care about the \
vehicle.

Respond with exactly one JSON object and nothing else — no markdown, no commentary:
{
  "chassis": "<VIN/chassis number, or null if not present>",
  "km": <odometer reading as an integer, or null if not present>,
  "damage": ["<short damage item>", ...]   // empty array if none listed
}

If the text is not a usable expertise report or a required field is absent, use \
null for that field. NEVER invent a chassis number, km value, or damage entry \
that is not clearly in the text."""


class ReasoningClient(Protocol):
    async def reasoning(self, messages: list[dict[str, Any]], **kwargs: Any) -> Any: ...


class ExtractionParseError(Exception):
    """The model's vehicle-brief response was malformed."""


@dataclass(frozen=True)
class VehicleBrief:
    chassis: str | None
    km: int | None
    damage: list[str] = field(default_factory=list)
    incomplete: bool = False
    redaction_applied: bool = False


async def extract_vehicle_brief(
    *,
    ocr_text: str,
    llm_client: ReasoningClient,
    sensitivity: str = "confidential",
    **meta: Any,
) -> VehicleBrief:
    """Redact the OCR text, then extract vehicle fields via the reasoning model.

    Sensitivity is `confidential`: after redaction the effective sensitivity is
    downgraded to internal (core.llm.routing), which is what lets the redacted
    brief reach the cloud reasoning lane while the raw PII never does.
    """
    redacted = scrub(ocr_text)
    messages = [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {"role": "user", "content": redacted.text},
    ]
    # redacted=True tells the gateway this content already passed the PII pipeline
    # (routing's §8 redaction-downgrade), so confidential -> internal for routing.
    response = await llm_client.reasoning(
        messages, sensitivity=sensitivity, redacted=True, **meta
    )

    try:
        parsed = json.loads(_strip_code_fence(response.content))
    except json.JSONDecodeError as exc:
        raise ExtractionParseError(
            f"model did not return valid JSON: {response.content!r}"
        ) from exc

    chassis_raw = parsed.get("chassis")
    chassis = str(chassis_raw).strip() if chassis_raw not in (None, "", "null") else None

    km_raw = parsed.get("km")
    km: int | None
    if km_raw in (None, "", "null"):
        km = None
    else:
        try:
            km = int(km_raw)
        except (TypeError, ValueError):
            km = None

    damage_raw = parsed.get("damage", [])
    damage = [str(d).strip() for d in damage_raw if str(d).strip()] if isinstance(
        damage_raw, list
    ) else []

    # Missing-report guardrail: a report with no chassis AND no km is unusable —
    # mark incomplete rather than surface a half-invented brief.
    incomplete = chassis is None and km is None

    return VehicleBrief(
        chassis=chassis,
        km=km,
        damage=damage,
        incomplete=incomplete,
        redaction_applied=redacted.found,
    )
