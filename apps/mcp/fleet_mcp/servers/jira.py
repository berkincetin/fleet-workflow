"""jira MCP tool: search/get_issue (task 5.3, dept scenario 03 Dev Agent).

# INTEGRATION-POINT (CLAUDE.md rule 2): no real Jira Cloud credentials are
configured in this environment, so the default backend is fixture-backed
(FixtureJiraBackend). A real-config option (RestJiraBackend) is provided for
when Jira credentials become available — both implement the same JiraBackend
Protocol, so JiraTool and its MCP contracts don't change either way. Both
tools are `read` risk_class (TRD §9) — Dev Agent only ever reads tickets,
never writes back to Jira.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Protocol

import httpx
from fleet_mcp.base import ToolContract

SEARCH_SCHEMA = {
    "type": "object",
    "properties": {"jql": {"type": "string"}},
    "required": ["jql"],
    "additionalProperties": False,
}
GET_ISSUE_SCHEMA = {
    "type": "object",
    "properties": {"key": {"type": "string"}},
    "required": ["key"],
    "additionalProperties": False,
}


class IssueNotFoundError(Exception):
    """No issue exists for the given key."""


class JiraBackend(Protocol):
    async def search(self, jql: str) -> list[dict[str, Any]]: ...
    async def get_issue(self, key: str) -> dict[str, Any]: ...


@dataclass
class FixtureJiraBackend:
    """# INTEGRATION-POINT: in-memory fixture tickets, keyed by issue key."""

    issues: dict[str, dict[str, Any]] = field(default_factory=dict)

    async def search(self, jql: str) -> list[dict[str, Any]]:
        if "agent-ok" in jql:
            return [i for i in self.issues.values() if "agent-ok" in i.get("labels", [])]
        return list(self.issues.values())

    async def get_issue(self, key: str) -> dict[str, Any]:
        if key not in self.issues:
            raise IssueNotFoundError(key)
        return self.issues[key]


@dataclass
class RestJiraBackend:
    """Real Jira Cloud REST backend — used once FLEET_JIRA_* env is configured."""

    base_url: str
    email: str
    api_token: str

    async def search(self, jql: str) -> list[dict[str, Any]]:
        async with httpx.AsyncClient(auth=(self.email, self.api_token)) as client:
            resp = await client.get(f"{self.base_url}/rest/api/3/search", params={"jql": jql})
            resp.raise_for_status()
            return list(resp.json().get("issues", []))

    async def get_issue(self, key: str) -> dict[str, Any]:
        async with httpx.AsyncClient(auth=(self.email, self.api_token)) as client:
            resp = await client.get(f"{self.base_url}/rest/api/3/issue/{key}")
            if resp.status_code == 404:
                raise IssueNotFoundError(key)
            resp.raise_for_status()
            return dict(resp.json())


@dataclass
class JiraTool:
    backend: JiraBackend

    async def search(self, jql: str) -> list[dict[str, Any]]:
        return await self.backend.search(jql)

    async def get_issue(self, key: str) -> dict[str, Any]:
        return await self.backend.get_issue(key)

    def as_contracts(self) -> list[ToolContract]:
        return [
            ToolContract(
                name="jira.search",
                risk_class="read",
                description="Search Jira issues by JQL.",
                input_schema=SEARCH_SCHEMA,
                fn=self.search,
            ),
            ToolContract(
                name="jira.get_issue",
                risk_class="read",
                description="Fetch one Jira issue by key.",
                input_schema=GET_ISSUE_SCHEMA,
                fn=self.get_issue,
            ),
        ]


def build_default_backend() -> JiraBackend:
    """FLEET_JIRA_BASE_URL/EMAIL/API_TOKEN present -> real backend; else fixtures."""
    base_url = os.environ.get("FLEET_JIRA_BASE_URL")
    email = os.environ.get("FLEET_JIRA_EMAIL")
    api_token = os.environ.get("FLEET_JIRA_API_TOKEN")
    if base_url and email and api_token:
        return RestJiraBackend(base_url=base_url, email=email, api_token=api_token)
    return FixtureJiraBackend()
