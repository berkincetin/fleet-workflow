"""Untrusted-content quarantine + prompt-injection heuristics (CLAUDE.md rule 4, TRD §7.3/§9).

Retrieved/tool content is untrusted data and is never concatenated raw into a
system prompt — it is always wrapped via wrap_untrusted first, with an explicit
instruction that the block is data, not commands. detect_injection is a cheap
pattern check (instruction-like phrases, encoded payloads) used to flag
suspicious content for `guardrail_blocks_total` + reviewer note; it does not
block on its own — high-risk agents re-check flagged content with a
utility-model classifier (§7.3), which is a separate, heavier call-site.
"""

from __future__ import annotations

import re
from collections.abc import Sequence

_INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions", re.IGNORECASE),
    re.compile(r"disregard\s+(all\s+)?(previous|prior|above)", re.IGNORECASE),
    re.compile(r"önceki\s+talimatlar[ıi]\s*(n[ıi])?\s*yoksay", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+(in\s+)?(developer|admin|dan)\s+mode", re.IGNORECASE),
    re.compile(r"reveal\s+(the\s+)?system\s+prompt", re.IGNORECASE),
    re.compile(r"base64:", re.IGNORECASE),
]


def wrap_untrusted(content: str | Sequence[str]) -> str:
    """Wrap retrieved/tool content in a quarantine block.

    A single string is wrapped as-is; a sequence is numbered [chunk:N] so a
    model can cite a specific item without the block being mistaken for
    instructions.
    """
    if isinstance(content, str):
        body = content
    else:
        body = "\n\n".join(f"[chunk:{i}] {item}" for i, item in enumerate(content, start=1))
    return f"<untrusted_context>\n{body}\n</untrusted_context>"


def detect_injection(text: str) -> bool:
    """Flag instruction-like patterns or encoded payloads in untrusted text."""
    return any(pattern.search(text) for pattern in _INJECTION_PATTERNS)
