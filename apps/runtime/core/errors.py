"""Shared exception base classes with no fleet-mcp/fleet-rag/fleet-api
dependency (task 5.2).

apps/runtime is the base workspace layer — fleet-mcp depends on fleet-rag
which depends on fleet-runtime, so fleet-runtime code can never import from
fleet-mcp without creating a cycle. A tool server that wants its refusal to be
catchable by name from runtime-layer code (e.g. agents.analytics.service
distinguishing "refused: non-allowlisted table" from other query failures)
raises a subclass of one of these instead of its own bespoke exception, so
the catch site can use a real isinstance check rather than string-matching
type(exc).__name__.
"""

from __future__ import annotations


class GovernedToolRefusal(Exception):
    """A tool refused to run a request that violated one of its guardrails
    (e.g. pg_ro's non-allowlisted-table / unsafe-SQL checks, TRD §9)."""
