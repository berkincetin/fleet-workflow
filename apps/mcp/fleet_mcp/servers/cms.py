"""cms + social MCP tools: publish (write:external) — task 11.3, dept scenario
08 (Insights Publisher).

# INTEGRATION-POINT (CLAUDE.md rule 2): no real CMS or social platform is wired
in this environment (dept scenario 08 names this — "mock CMS/social"). `publish`
records the published payload in-memory and returns synthetic ids, the same
fixture-backed pattern as erp.py / listings.py.

Both cms.publish and social.post are write:external: publishing public marketing
content is exactly the external side effect that must never execute without a
human approval (TRD §9), and dept scenario 08's rollout is "approval-gated
(public content)" — so this is reached only after the HITL interrupt approves.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

from fleet_mcp.base import ToolContract

PUBLISH_SCHEMA = {
    "type": "object",
    "properties": {"report": {"type": "string"}, "social": {"type": "string"}},
    "required": ["report", "social"],
    "additionalProperties": False,
}


@dataclass
class CmsTool:
    published: list[dict[str, Any]] = field(default_factory=list)

    async def publish(self, *, report: str, social: str) -> dict[str, Any]:
        record = {
            "cms_id": f"POST-{uuid.uuid4().hex[:10]}",
            "social_id": f"SOC-{uuid.uuid4().hex[:10]}",
            "status": "published",
        }
        self.published.append({**record, "report": report, "social": social})
        return record


def build_cms_server(*, api_key: str) -> Any:
    from fleet_mcp.base import MCPServer

    tool = CmsTool()
    server = MCPServer(name="cms", api_key=api_key)
    server.register(
        ToolContract(
            name="cms.publish",
            risk_class="write:external",
            description="Publish a report + social variant to the CMS/social channels (mock).",
            input_schema=PUBLISH_SCHEMA,
            fn=tool.publish,
        )
    )
    return server, tool
