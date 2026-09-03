"""apps/web/messages: TR/EN parity and no missing keys (task 13.2 AC).

next-intl fails at render time on a missing key, and a screen nobody opened in
the other locale is exactly where that hides. Two checks:

1. **Parity** — `tr.json` and `en.json` carry the same key set, so translating a
   new string is not something a reviewer has to notice.
2. **Resolvability** — every literal `t("…")` in the web app resolves against
   the namespace its component declared. Dynamic keys (template literals) are
   skipped: they are guarded in code with `t.has(...)`, which this cannot see.

Pure file inspection — no Node, no browser.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

WEB = Path(__file__).resolve().parents[2] / "apps" / "web"
MESSAGES = WEB / "messages"

_NAMESPACE_RE = re.compile(
    r"""(?:const|let|var)\s+(?P<var>t[A-Za-z0-9_]*)\s*=\s*"""
    r"""(?:await\s+)?(?:useTranslations|getTranslations)\(\s*["'](?P<ns>[^"']+)["']\s*\)"""
)


def _flatten(node: object, prefix: str = "") -> set[str]:
    keys: set[str] = set()
    if isinstance(node, dict):
        for key, value in node.items():
            keys |= _flatten(value, f"{prefix}{key}.")
    else:
        keys.add(prefix.rstrip("."))
    return keys


def _load(locale: str) -> dict:
    return json.loads((MESSAGES / f"{locale}.json").read_text(encoding="utf-8"))


def test_tr_and_en_have_the_same_keys() -> None:
    tr, en = _flatten(_load("tr")), _flatten(_load("en"))
    assert sorted(tr - en) == [], "keys present in TR but missing from EN"
    assert sorted(en - tr) == [], "keys present in EN but missing from TR"


def _tsx_files() -> list[Path]:
    return [
        path
        for pattern in ("app/**/*.tsx", "components/**/*.tsx")
        for path in WEB.glob(pattern)
        if "node_modules" not in path.parts
    ]


def _referenced_keys() -> dict[Path, set[str]]:
    """Literal `t("key")` calls, resolved to full dotted paths per file."""
    found: dict[Path, set[str]] = {}
    for path in _tsx_files():
        source = path.read_text(encoding="utf-8")
        namespaces = {m.group("var"): m.group("ns") for m in _NAMESPACE_RE.finditer(source)}
        if not namespaces:
            continue
        keys: set[str] = set()
        for var, namespace in namespaces.items():
            for match in re.finditer(rf"\b{re.escape(var)}\(\s*[\"']([^\"']+)[\"']", source):
                keys.add(f"{namespace}.{match.group(1)}")
            # `t.raw("howTo")` resolves like a plain lookup.
            for match in re.finditer(rf"\b{re.escape(var)}\.raw\(\s*[\"']([^\"']+)[\"']", source):
                keys.add(f"{namespace}.{match.group(1)}")
        if keys:
            found[path] = keys
    return found


ACTION_NAMES_RE = re.compile(
    r"export const ACTION_NAMES = \[(?P<body>.*?)\] as const;", re.S
)


def _action_names() -> list[str]:
    source = (WEB / "lib" / "recipe-actions.ts").read_text(encoding="utf-8")
    match = ACTION_NAMES_RE.search(source)
    assert match, "ACTION_NAMES not found in lib/recipe-actions.ts"
    return re.findall(r'"([^"]+)"', match.group("body"))


@pytest.mark.parametrize("locale", ["tr", "en"])
def test_every_recipe_action_has_a_label_and_help(locale: str) -> None:
    """Guards the class of bug the literal scan cannot see.

    The builder looks these up dynamically (`t(`actions.${action}.label`)`), and
    next-intl resolves a key by splitting on ".", so an action id that contains
    a dot — every one of them does — must be *nested* in the messages file
    (`actions.pg.query.label`), not stored under a literal "pg.query" key. When
    it was flat, next-intl silently rendered the raw key path in the UI.
    """
    actions = _load(locale)["builder"]["actions"]
    missing: list[str] = []
    for action in _action_names():
        # Walk the nesting the way next-intl does — a literal "pg.query" key
        # would satisfy a flattened-path check while still failing at runtime.
        node: object = actions
        for segment in action.split("."):
            node = node.get(segment) if isinstance(node, dict) else None
        for field in ("label", "help"):
            if not isinstance(node, dict) or not isinstance(node.get(field), str):
                missing.append(f"builder.actions.{action}.{field}")
    assert missing == [], f"missing {locale} keys: {missing}"


@pytest.mark.parametrize("locale", ["tr", "en"])
def test_every_literal_translation_key_exists(locale: str) -> None:
    available = _flatten(_load(locale))
    # `t.raw("howTo")` points at an array, which flattens to `ns.howTo.0`, so a
    # key is present if it is a leaf *or* the prefix of one.
    prefixes = {key.rsplit(".", 1)[0] for key in available}

    missing: list[str] = []
    for path, keys in _referenced_keys().items():
        for key in sorted(keys):
            if key not in available and key not in prefixes:
                missing.append(f"{path.relative_to(WEB)}: {key}")
    assert missing == [], f"missing {locale} keys:\n" + "\n".join(missing)
