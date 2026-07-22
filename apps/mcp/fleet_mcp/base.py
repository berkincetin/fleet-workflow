"""MCP server base: tool registry with declared risk_class, schema validation,
and bearer-token auth (task 5.1, TRD §7.1 auth, §7.3 LLM08 tool allowlists,
§9 risk_class -> autonomous vs approval).

Every Fleet MCP server (pg_ro, ocr, email, internal-mock, jira, github, slack)
is built the same way: construct an MCPServer, register() one ToolContract per
tool, then let callers reach tools only through call_tool() — which enforces
auth and validates the payload against the tool's own input_schema before the
tool function ever runs. Credentials for the underlying integration (DB
creds, SMTP, provider tokens) live inside the server process, never in the
LLM context (CLAUDE.md rule 3 / TRD §7.2).

Schema validation here is intentionally minimal (required fields, type check,
additionalProperties) — enough to catch a malformed tool call before it reaches
integration code, not a full JSON Schema implementation.
"""

from __future__ import annotations

import hmac
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

VALID_RISK_CLASSES = {"read", "write:internal", "write:external"}

ToolFn = Callable[..., Awaitable[Any]]

_TYPE_MAP: dict[str, type | tuple[type, ...]] = {
    "string": str,
    "number": (int, float),
    "integer": int,
    "boolean": bool,
    "object": dict,
    "array": list,
}


class MCPAuthError(Exception):
    """Raised when a call_tool request carries a wrong/missing API key."""


class MCPValidationError(Exception):
    """Raised when a call_tool payload fails the tool's input_schema."""


@dataclass(frozen=True)
class ToolContract:
    name: str
    risk_class: str  # read | write:internal | write:external (TRD §9)
    description: str
    input_schema: dict[str, Any]
    fn: ToolFn


def _validate_schema(payload: dict[str, Any], schema: dict[str, Any]) -> None:
    properties: dict[str, Any] = schema.get("properties", {})
    required: list[str] = schema.get("required", [])
    for field in required:
        if field not in payload:
            raise MCPValidationError(f"missing required field: {field}")
    if schema.get("additionalProperties") is False:
        extra = set(payload) - set(properties)
        if extra:
            raise MCPValidationError(f"unexpected field(s): {sorted(extra)}")
    for field, value in payload.items():
        expected = properties.get(field, {}).get("type")
        py_type = _TYPE_MAP.get(expected) if expected else None
        if py_type is not None and not isinstance(value, py_type):
            raise MCPValidationError(
                f"field {field!r} expected type {expected}, got {type(value).__name__}"
            )


class MCPServer:
    """Registry + dispatcher for one MCP server's tools."""

    def __init__(self, *, name: str, api_key: str) -> None:
        self.name = name
        self._api_key = api_key
        self._tools: dict[str, ToolContract] = {}

    def register(self, tool: ToolContract) -> None:
        if tool.risk_class not in VALID_RISK_CLASSES:
            raise ValueError(
                f"invalid risk_class {tool.risk_class!r}, "
                f"must be one of {sorted(VALID_RISK_CLASSES)}"
            )
        self._tools[tool.name] = tool

    def list_tools(self) -> list[dict[str, Any]]:
        return [
            {
                "name": t.name,
                "risk_class": t.risk_class,
                "description": t.description,
                "input_schema": t.input_schema,
            }
            for t in self._tools.values()
        ]

    def _check_auth(self, api_key: str) -> None:
        if not hmac.compare_digest(api_key, self._api_key):
            raise MCPAuthError("invalid MCP server API key")

    async def call_tool(self, name: str, payload: dict[str, Any], *, api_key: str) -> Any:
        self._check_auth(api_key)
        tool = self._tools[name]
        _validate_schema(payload, tool.input_schema)
        return await tool.fn(**payload)
