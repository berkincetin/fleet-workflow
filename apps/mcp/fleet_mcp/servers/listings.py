"""listings MCP tools: get_new (read) + flag (write:internal) — task 11.1,
dept scenario 06 (Listing Quality).

# INTEGRATION-POINT (CLAUDE.md rule 2): no real listing platform is wired in
this environment (dept scenario 06 names this — "mock listing API + synthetic
listing generator in demo"). `get_new` returns synthetic listings from an
in-memory generator; `flag` records the flag in-memory and returns a synthetic
ack, the same fixture-backed-standing-in-for-a-real-system pattern as erp.py /
internal_mock.py.

`flag` is write:internal (supervised), NOT write:external — flagging a listing
into the internal review queue is an internal side effect, not a public/external
one. There is deliberately **no unpublish/reject tool** here: the agent is
flag-only (dept scenario 06 guardrail), so the guardrail is enforced by the tool
surface simply not existing, not by a runtime check that could be bypassed.
"""

from __future__ import annotations

import base64
import hashlib
import uuid
from dataclasses import dataclass, field
from typing import Any

from fleet_mcp.base import ToolContract

GET_NEW_SCHEMA = {
    "type": "object",
    "properties": {"limit": {"type": "integer"}},
    "required": [],
    "additionalProperties": False,
}

FLAG_SCHEMA = {
    "type": "object",
    "properties": {
        "listing_id": {"type": "string"},
        "codes": {"type": "array"},
        "reasons": {"type": "array"},
    },
    "required": ["listing_id", "codes"],
    "additionalProperties": False,
}


# A tiny valid PNG (1x1) as a deterministic stand-in image. The demo's real
# vision fixtures come from evals/synthetic listings; get_new only needs to
# return a well-formed data payload for the mock API.
_STUB_PNG_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+M8AAAMBAQDJ/pLvAAAAAElFTkSuQmCC"
)


def _synthetic_listings(n: int) -> list[dict[str, Any]]:
    """Deterministic synthetic listings for the mock get_new API."""
    segments = ["sedan-2018", "suv-2020", "hatchback-2019"]
    out: list[dict[str, Any]] = []
    for i in range(n):
        seg = segments[i % len(segments)]
        out.append(
            {
                "listing_id": f"L-{i:04d}",
                "segment": seg,
                "description": f"{seg.replace('-', ' ')}, clean, well maintained.",
                "price": 400000 + (i * 25000),
                "currency": "TRY",
                "image_base64": _STUB_PNG_B64,
            }
        )
    return out


@dataclass
class ListingsTool:
    """In-memory mock of the listing platform (get_new + flag)."""

    flagged: list[dict[str, Any]] = field(default_factory=list)

    async def get_new(self, *, limit: int = 10) -> dict[str, Any]:
        return {"listings": _synthetic_listings(limit)}

    async def flag(
        self, *, listing_id: str, codes: list[str], reasons: list[str] | None = None
    ) -> dict[str, Any]:
        record = {
            "flag_id": f"FLAG-{uuid.uuid4().hex[:10]}",
            "listing_id": listing_id,
            "codes": list(codes),
            "reasons": list(reasons or []),
            "status": "queued_for_review",
        }
        self.flagged.append(record)
        return record


def build_listings_server(*, api_key: str) -> Any:
    from fleet_mcp.base import MCPServer

    tool = ListingsTool()
    server = MCPServer(name="listings", api_key=api_key)
    server.register(
        ToolContract(
            name="listings.get_new",
            risk_class="read",
            description="Fetch new listings pending a quality check (synthetic in demo).",
            input_schema=GET_NEW_SCHEMA,
            fn=tool.get_new,
        )
    )
    server.register(
        ToolContract(
            name="listings.flag",
            risk_class="write:internal",
            description="Flag a listing into the human review queue with reason codes.",
            input_schema=FLAG_SCHEMA,
            fn=tool.flag,
        )
    )
    return server, tool


def stub_image_bytes() -> bytes:
    """The stub PNG as raw bytes (for tests / fixtures)."""
    return base64.b64decode(_STUB_PNG_B64)


def image_digest(image_base64: str) -> str:
    return hashlib.sha256(image_base64.encode()).hexdigest()[:12]
