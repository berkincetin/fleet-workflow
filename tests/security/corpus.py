"""Prompt-injection corpus loader + an injection oracle (task 9.2, TRD §13.5).

The corpus (`injection_corpus.jsonl`) holds attack payloads *as they would
appear inside a retrieved KB document* served to the Support Copilot. Each case
carries a `marker` — a string that only appears if the injected instruction was
followed — plus `detect_expected`, whether the cheap `core.guardrails`
heuristic is expected to flag it.

`InjectionOracle` is the honest part. A static canned-response FakeLLM cannot
"decide" to obey an injection, so it would make the containment test pass
trivially. Instead the oracle simulates a *compliant-but-injectable* model: it
reads the outgoing prompt, treats anything **inside** the `<untrusted_context>`
quarantine block as inert data, and obeys imperative instructions found
**outside** it. If a payload ever leaks out of quarantine into an instruction
position, the oracle follows it and emits the marker — failing the test. This
turns "0 successful instruction-follows from quarantined content" (the 9.2 AC)
into something the pipeline must actually earn structurally, not assert.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from core.guardrails import strip_untrusted_blocks

_CORPUS_PATH = Path(__file__).with_name("injection_corpus.jsonl")


@dataclass(frozen=True)
class InjectionCase:
    id: str
    category: str
    payload: str
    marker: str
    detect_expected: bool
    note: str


def load_corpus() -> list[InjectionCase]:
    cases: list[InjectionCase] = []
    for line in _CORPUS_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        raw = json.loads(line)
        cases.append(
            InjectionCase(
                id=raw["id"],
                category=raw["category"],
                payload=raw["payload"],
                marker=raw["marker"],
                detect_expected=bool(raw["detect_expected"]),
                note=raw.get("note", ""),
            )
        )
    if not cases:
        raise ValueError("injection corpus is empty")
    return cases


def strip_quarantine(prompt_text: str) -> str:
    """Return the prompt with every quarantine block removed.

    Delegates to the production `strip_untrusted_blocks`, whose nonce-anchored
    matching is exactly what defeats the delimiter-injection escape. What
    remains is the text the model is entitled to treat as instructions; a model
    that only ever obeys *this* region can never be injected by retrieved
    content — the property 9.2 asserts.
    """
    return strip_untrusted_blocks(prompt_text)


class _OracleResponse:
    def __init__(self, content: str) -> None:
        self.content = content
        self.tool_call: dict[str, Any] | None = None


class InjectionOracle:
    """A reasoning client that faithfully obeys instructions OUTSIDE quarantine.

    It never invents the attack marker on its own: the marker only appears in
    its output if the corresponding payload text was present in the
    instruction-eligible (non-quarantined) region of the prompt. So a leaked
    payload → marker in output → test failure; a contained payload → marker
    absent → pass.
    """

    def __init__(self, markers: list[str]) -> None:
        self._markers = markers
        self.calls: list[dict[str, Any]] = []
        # Raw markers the model actually emitted, across all calls. This is the
        # ground truth for "did an injection get followed" — checked directly,
        # because the RAG grounding guardrail would otherwise degrade a
        # citation-less injected answer to a fixed string and hide the marker.
        self.emitted_markers: list[str] = []

    def _flatten(self, messages: list[dict[str, Any]]) -> str:
        return "\n".join(str(m.get("content", "")) for m in messages)

    async def reasoning(self, messages: list[dict[str, Any]], **kwargs: Any) -> Any:
        self.calls.append({"messages": messages, **kwargs})
        instruction_region = strip_quarantine(self._flatten(messages))
        # Simulate instruction-following: if a marker's payload survived into
        # the instruction region, the model "obeys" and emits the marker.
        emitted = [m for m in self._markers if m.lower() in instruction_region.lower()]
        if emitted:
            self.emitted_markers.extend(emitted)
            return _OracleResponse(" ".join(emitted))
        # No injection leaked: behave like a grounded copilot, cite chunk 1.
        return _OracleResponse("Here is the grounded answer. [chunk:1]")

    async def utility(self, messages: list[dict[str, Any]], **kwargs: Any) -> Any:
        return await self.reasoning(messages, **kwargs)
