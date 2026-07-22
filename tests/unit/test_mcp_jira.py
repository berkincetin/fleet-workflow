"""fleet_mcp.servers.jira: fixture-backed Jira mock + real-config option
(task 5.3, dept scenario 03 Dev Agent).

# INTEGRATION-POINT (CLAUDE.md rule 2): real Jira Cloud auth/API isn't wired
in this environment; JiraTool is built over an injected JiraBackend Protocol
so a FixtureJiraBackend (this file) and a real REST-backed implementation
share the same tool surface without the caller needing to know which is live.
Both jira.search and jira.get_issue are `read` risk_class.
"""

from __future__ import annotations

import pytest
from fleet_mcp.servers.jira import IssueNotFoundError, JiraTool


class _FixtureBackend:
    def __init__(self, issues: dict[str, dict[str, object]]) -> None:
        self.issues = issues

    async def search(self, jql: str) -> list[dict[str, object]]:
        if "agent-ok" in jql:
            return [i for i in self.issues.values() if "agent-ok" in i.get("labels", [])]
        return list(self.issues.values())

    async def get_issue(self, key: str) -> dict[str, object]:
        if key not in self.issues:
            raise IssueNotFoundError(key)
        return self.issues[key]


def _backend() -> _FixtureBackend:
    return _FixtureBackend(
        {
            "DEV-1": {"key": "DEV-1", "summary": "Fix typo", "labels": ["agent-ok"]},
            "DEV-2": {"key": "DEV-2", "summary": "Rework auth", "labels": []},
        }
    )


async def test_search_returns_matching_issues() -> None:
    tool = JiraTool(backend=_backend())
    results = await tool.search(jql="labels = agent-ok")
    assert [r["key"] for r in results] == ["DEV-1"]


async def test_get_issue_returns_issue_by_key() -> None:
    tool = JiraTool(backend=_backend())
    issue = await tool.get_issue(key="DEV-2")
    assert issue["summary"] == "Rework auth"


async def test_get_issue_raises_on_unknown_key() -> None:
    tool = JiraTool(backend=_backend())
    with pytest.raises(IssueNotFoundError):
        await tool.get_issue(key="DEV-999")


def test_contracts_declare_read_risk_class() -> None:
    tool = JiraTool(backend=_backend())
    contracts = tool.as_contracts()
    names = {c.name: c.risk_class for c in contracts}
    assert names == {"jira.search": "read", "jira.get_issue": "read"}
