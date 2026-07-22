"""github MCP tool: read_repo/create_branch/open_pr (task 5.3, dept scenario
03 Dev Agent).

Guardrails enforced in GitHubTool, ahead of any backend call:
- create_branch and commit_file both require the `agent/*` name pattern
  (dept scenario 03's explicit guardrail — the Dev Agent may only ever
  create/write on branches under this prefix, never touch an existing branch).
- open_pr is always `write:external` (TRD §9 — PR creation is the department
  scenario's canonical "always approval queue, no exception" example); this
  tool never decides autonomy, it only executes once HITL has approved/resumed.

commit_file exists because a PR against a branch with zero commits ahead of
its base is rejected by GitHub (422 "no commits between ... and ...") — the
Dev Agent's own task wording ("implementation draft") already implies a real
change lands on the branch before PR, this just makes that a real API call
instead of an assumption. It writes one file via the Contents API (base64,
matches GitHub's REST contract) — a minimal real diff, not a full patch
apply engine.

RestGitHubBackend talks to the real GitHub REST API directly via httpx (no
PyGithub dependency, matching the plain-httpx pattern already used for
jira.RestJiraBackend and email/slack's transports) — used against the
sandbox repo (FLEET_GITHUB_SANDBOX_REPO/TOKEN) for 5.3's live smoke test and
5.5's Dev Agent.
"""

from __future__ import annotations

import base64
import os
import re
from dataclasses import dataclass
from typing import Any, Protocol

import httpx
from fleet_mcp.base import ToolContract

READ_REPO_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {},
    "additionalProperties": False,
}
CREATE_BRANCH_SCHEMA = {
    "type": "object",
    "properties": {"branch_name": {"type": "string"}, "from_ref": {"type": "string"}},
    "required": ["branch_name", "from_ref"],
    "additionalProperties": False,
}
COMMIT_FILE_SCHEMA = {
    "type": "object",
    "properties": {
        "branch_name": {"type": "string"},
        "path": {"type": "string"},
        "content": {"type": "string"},
        "message": {"type": "string"},
    },
    "required": ["branch_name", "path", "content", "message"],
    "additionalProperties": False,
}
OPEN_PR_SCHEMA = {
    "type": "object",
    "properties": {
        "branch_name": {"type": "string"},
        "title": {"type": "string"},
        "body": {"type": "string"},
    },
    "required": ["branch_name", "title", "body"],
    "additionalProperties": False,
}

_AGENT_BRANCH_RE = re.compile(r"^agent/.+")


class BranchNamePatternError(Exception):
    """create_branch was asked to create a name outside the `agent/*` pattern."""


class GitHubBackend(Protocol):
    async def read_repo(self) -> dict[str, Any]: ...
    async def create_branch(self, branch_name: str, from_ref: str) -> dict[str, Any]: ...
    async def commit_file(
        self, *, branch_name: str, path: str, content: str, message: str
    ) -> dict[str, Any]: ...
    async def open_pr(self, *, branch_name: str, title: str, body: str) -> dict[str, Any]: ...


@dataclass
class RestGitHubBackend:
    repo: str  # "owner/name"
    token: str

    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            base_url="https://api.github.com",
            headers={
                "Authorization": f"Bearer {self.token}",
                "Accept": "application/vnd.github+json",
            },
        )

    async def read_repo(self) -> dict[str, Any]:
        async with self._client() as client:
            resp = await client.get(f"/repos/{self.repo}")
            resp.raise_for_status()
            return dict(resp.json())

    async def create_branch(self, branch_name: str, from_ref: str) -> dict[str, Any]:
        async with self._client() as client:
            ref_resp = await client.get(f"/repos/{self.repo}/git/ref/heads/{from_ref}")
            ref_resp.raise_for_status()
            base_sha = ref_resp.json()["object"]["sha"]

            resp = await client.post(
                f"/repos/{self.repo}/git/refs",
                json={"ref": f"refs/heads/{branch_name}", "sha": base_sha},
            )
            resp.raise_for_status()
            return dict(resp.json())

    async def commit_file(
        self, *, branch_name: str, path: str, content: str, message: str
    ) -> dict[str, Any]:
        async with self._client() as client:
            encoded = base64.b64encode(content.encode("utf-8")).decode("ascii")
            # Contents API upserts: if the file already exists on this branch
            # (re-run of the same ticket), GitHub requires the current sha.
            existing = await client.get(
                f"/repos/{self.repo}/contents/{path}", params={"ref": branch_name}
            )
            body: dict[str, Any] = {"message": message, "content": encoded, "branch": branch_name}
            if existing.status_code == 200:
                body["sha"] = existing.json()["sha"]

            resp = await client.put(f"/repos/{self.repo}/contents/{path}", json=body)
            resp.raise_for_status()
            return dict(resp.json())

    async def open_pr(self, *, branch_name: str, title: str, body: str) -> dict[str, Any]:
        async with self._client() as client:
            repo_resp = await client.get(f"/repos/{self.repo}")
            repo_resp.raise_for_status()
            base_branch = repo_resp.json()["default_branch"]

            resp = await client.post(
                f"/repos/{self.repo}/pulls",
                json={"title": title, "body": body, "head": branch_name, "base": base_branch},
            )
            resp.raise_for_status()
            return dict(resp.json())


@dataclass
class GitHubTool:
    backend: GitHubBackend

    async def read_repo(self) -> dict[str, Any]:
        return await self.backend.read_repo()

    async def create_branch(self, branch_name: str, from_ref: str) -> dict[str, Any]:
        if not _AGENT_BRANCH_RE.match(branch_name):
            raise BranchNamePatternError(
                f"branch name {branch_name!r} does not match required pattern 'agent/*'"
            )
        return await self.backend.create_branch(branch_name, from_ref)

    async def commit_file(
        self, branch_name: str, path: str, content: str, message: str
    ) -> dict[str, Any]:
        if not _AGENT_BRANCH_RE.match(branch_name):
            raise BranchNamePatternError(
                f"branch name {branch_name!r} does not match required pattern 'agent/*'"
            )
        return await self.backend.commit_file(
            branch_name=branch_name, path=path, content=content, message=message
        )

    async def open_pr(self, branch_name: str, title: str, body: str) -> dict[str, Any]:
        return await self.backend.open_pr(branch_name=branch_name, title=title, body=body)

    def as_contracts(self) -> list[ToolContract]:
        return [
            ToolContract(
                name="github.read_repo",
                risk_class="read",
                description="Read repository metadata.",
                input_schema=READ_REPO_SCHEMA,
                fn=self.read_repo,
            ),
            ToolContract(
                name="github.create_branch",
                risk_class="write:internal",
                description="Create a branch under the agent/* naming pattern.",
                input_schema=CREATE_BRANCH_SCHEMA,
                fn=self.create_branch,
            ),
            ToolContract(
                name="github.commit_file",
                risk_class="write:internal",
                description="Commit one file to a branch under the agent/* naming pattern.",
                input_schema=COMMIT_FILE_SCHEMA,
                fn=self.commit_file,
            ),
            ToolContract(
                name="github.open_pr",
                risk_class="write:external",
                description="Open a pull request (always approval-gated).",
                input_schema=OPEN_PR_SCHEMA,
                fn=self.open_pr,
            ),
        ]


def build_default_backend() -> GitHubBackend:
    repo = os.environ.get("FLEET_GITHUB_SANDBOX_REPO", "")
    token = os.environ.get("FLEET_GITHUB_SANDBOX_TOKEN", "")
    return RestGitHubBackend(repo=repo, token=token)
