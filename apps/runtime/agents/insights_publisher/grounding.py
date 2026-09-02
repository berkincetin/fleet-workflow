"""Numbers-match grounding guardrail (task 11.3, dept scenario 08).

Every numeric claim in a generated marketing draft must correspond to a value
in the query results the draft was built from — a public report that invents a
statistic is the exact failure this scenario guards against. This is a
deterministic post-generation check (no LLM): extract the numbers from the
draft, and require each to match (within a small tolerance) some value in the
attached data. Any unmatched number fails grounding, and the draft never
reaches the approval item.

Percentages and thousands separators are normalised before comparison so
"12,5%" / "12.5" / "1.250.000" match their raw data values. Small ordinals and
years that also appear verbatim in the data are fine; a number that appears
nowhere in the data is the failure.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

# Matches numbers like 1.250.000  12,5  %12,5  1250000  2026
_NUMBER_RE = re.compile(r"%?\s?\d[\d.,]*")


def _normalise(token: str) -> float | None:
    """Turn a display number token into a float, handling TR/EN separators.

    TR uses '.' for thousands and ',' for decimals; EN the reverse. We treat a
    comma as the decimal separator when it is followed by 1-2 trailing digits,
    otherwise strip both as grouping separators."""
    t = token.replace("%", "").replace(" ", "").strip()
    if not t:
        return None
    # Decimal comma (e.g. 12,5) -> 12.5 ; strip '.' thousands first.
    if re.search(r",\d{1,2}$", t):
        t = t.replace(".", "").replace(",", ".")
    else:
        t = t.replace(",", "").replace(".", "")
    try:
        return float(t)
    except ValueError:
        return None


def extract_numbers(text: str) -> list[float]:
    out: list[float] = []
    for m in _NUMBER_RE.findall(text):
        val = _normalise(m)
        if val is not None:
            out.append(val)
    return out


def _data_values(rows: list[dict[str, Any]]) -> set[float]:
    values: set[float] = set()
    for row in rows:
        for v in row.values():
            if isinstance(v, bool):
                continue
            if isinstance(v, (int, float)):
                values.add(float(v))
            elif isinstance(v, str):
                # A number the draft legitimately cites may be embedded in a
                # label cell (e.g. the year in "sedan-2018"), so pull EVERY
                # number out of the string, not just parse the whole cell.
                for tok in _NUMBER_RE.findall(v):
                    n = _normalise(tok)
                    if n is not None:
                        values.add(n)
    return values


@dataclass(frozen=True)
class GroundingResult:
    grounded: bool
    unmatched: list[float] = field(default_factory=list)


def check_numbers_grounded(
    *, draft_text: str, data_rows: list[dict[str, Any]], tolerance: float = 0.01
) -> GroundingResult:
    """Return grounded=True iff every number in the draft matches a data value.

    Matching is within `tolerance` (relative) to absorb rounding in prose (e.g.
    "about 12.5%" vs 12.503). A draft with no numbers is trivially grounded."""
    data = _data_values(data_rows)
    unmatched: list[float] = []
    for num in extract_numbers(draft_text):
        if not any(
            abs(num - d) <= max(tolerance, abs(d) * tolerance) for d in data
        ):
            unmatched.append(num)
    return GroundingResult(grounded=not unmatched, unmatched=unmatched)
