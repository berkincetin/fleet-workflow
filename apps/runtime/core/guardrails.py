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
import secrets
from collections.abc import Sequence

_TAG = "untrusted_context"
# Any literal delimiter-like token in the body is neutralised before wrapping so
# untrusted content can never forge (or even resemble) the block boundary. A
# random per-call nonce on the real delimiter is the primary defence; this
# scrub is defence-in-depth and also keeps a forged bare tag from confusing a
# human reading the trace.
_TAG_TOKEN_RE = re.compile(rf"</?\s*{_TAG}\b[^>]*>?", re.IGNORECASE)

_INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions", re.IGNORECASE),
    re.compile(r"disregard\s+(all\s+|the\s+)?(previous|prior|above)", re.IGNORECASE),
    re.compile(r"önceki\s+talimatlar[ıi]\s*(n[ıi])?\s*yoksay", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+(in\s+)?(developer|admin|dan)\s+mode", re.IGNORECASE),
    re.compile(r"reveal\s+(the\s+)?system\s+prompt", re.IGNORECASE),
    re.compile(r"base64:", re.IGNORECASE),
]


def _neutralise_delimiters(text: str) -> str:
    """Defang any literal quarantine-tag token embedded in untrusted content.

    A forged `</untrusted_context>` inside a retrieved chunk must never be able
    to close the real block early (the delimiter-injection escape). We strip
    the angle brackets so the token survives as visible text but is no longer a
    delimiter — combined with the per-call nonce on the real tag, the boundary
    is unforgeable.
    """
    return _TAG_TOKEN_RE.sub(lambda m: m.group(0).replace("<", "‹").replace(">", "›"), text)


def wrap_untrusted(content: str | Sequence[str]) -> str:
    """Wrap retrieved/tool content in a nonce-delimited quarantine block.

    A single string is wrapped as-is; a sequence is numbered [chunk:N] so a
    model can cite a specific item without the block being mistaken for
    instructions.

    The delimiter carries a random per-call `nonce` that untrusted content
    cannot predict, so an embedded closing tag can never terminate the block
    prematurely (TRD §7.3 prompt-injection containment; the 9.2 injection
    corpus regression-tests this). Any literal tag token already in the body is
    additionally neutralised.
    """
    if isinstance(content, str):
        body = _neutralise_delimiters(content)
    else:
        body = "\n\n".join(
            f"[chunk:{i}] {_neutralise_delimiters(item)}"
            for i, item in enumerate(content, start=1)
        )
    nonce = secrets.token_hex(8)
    return f'<{_TAG} nonce="{nonce}">\n{body}\n</{_TAG} nonce="{nonce}">'


def strip_untrusted_blocks(text: str) -> str:
    """Remove complete nonce-matched quarantine blocks from `text`.

    The inverse of wrap_untrusted: what remains is the instruction-eligible
    region (system/user text the model may treat as commands). Matching is
    anchored on the paired nonce, so a forged inner close tag cannot make this
    strip the wrong span — the property the delimiter-injection attack targets.
    """
    pattern = re.compile(
        rf'<{_TAG} nonce="([0-9a-f]+)">.*?</{_TAG} nonce="\1">',
        re.IGNORECASE | re.DOTALL,
    )
    return pattern.sub(" ", text)


def detect_injection(text: str) -> bool:
    """Flag instruction-like patterns or encoded payloads in untrusted text."""
    return any(pattern.search(text) for pattern in _INJECTION_PATTERNS)
