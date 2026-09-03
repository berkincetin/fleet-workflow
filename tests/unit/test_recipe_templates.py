"""The in-app examples: ready-made recipes, chat starters, guide walkthroughs (13.7).

These three lists are the first thing a new user touches, so the failure mode
that matters is an example that *looks* official and does not work — a template
whose SQL the server refuses, a Slack channel outside the allowlist, a starter
question for an agent nobody seeded, or a walkthrough step whose i18n key was
never written.

`test_i18n_messages.py` cannot catch the copy half of that: every key here is
built dynamically (`t(\\`templates.${tpl.id}.title\\`)`), and that test skips
template literals by design. So this module resolves them explicitly.

Pure file inspection, like its neighbour — the TS is parsed with regexes rather
than executed, which is enough because these files are literal data tables.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
WEB = ROOT / "apps" / "web"
MESSAGES = WEB / "messages"
TEMPLATES_TS = WEB / "lib" / "recipe-templates.ts"
STARTERS_TS = WEB / "lib" / "chat-starters.ts"
GUIDE_TS = WEB / "lib" / "guide.ts"
SERVICE_PY = ROOT / "apps" / "api" / "fleet_api" / "routers" / "service.py"
SEED_PY = ROOT / "apps" / "api" / "fleet_api" / "seed.py"


def _messages(locale: str) -> dict:
    return json.loads((MESSAGES / f"{locale}.json").read_text(encoding="utf-8"))


def _resolve(messages: dict, dotted: str) -> object | None:
    node: object = messages
    for part in dotted.split("."):
        if not isinstance(node, dict) or part not in node:
            return None
        node = node[part]
    return node


def _py_set(name: str) -> set[str]:
    """A `_NAME = {"a", "b"}` literal out of service.py."""
    source = SERVICE_PY.read_text(encoding="utf-8")
    match = re.search(rf"^{name}\s*=\s*\{{(?P<body>[^}}]*)\}}", source, re.MULTILINE)
    assert match, f"{name} not found in {SERVICE_PY.name} — was it renamed?"
    return set(re.findall(r'"([^"]+)"', match.group("body")))


# --- the template list itself -------------------------------------------

def _templates() -> list[dict]:
    """Each template as {id, name, actions, params, channels, emails, sql}."""
    source = TEMPLATES_TS.read_text(encoding="utf-8")
    # Split on the `id:` of each entry; every template declares one.
    chunks = re.split(r"\n    id: \"", source)[1:]
    out = []
    for chunk in chunks:
        tid = chunk[: chunk.index('"')]
        out.append(
            {
                "id": tid,
                "name": re.search(r'name: "([^"]+)"', chunk).group(1),
                "actions": re.findall(r'action: "([^"]+)"', chunk),
                "channels": re.findall(r'channel: "([^"]+)"', chunk),
                "emails": re.findall(r'to: "([^"]+)"', chunk),
                "agents": re.findall(r'agent: "([^"]+)"', chunk),
                "sql": " ".join(re.findall(r'sql:\s*\n?\s*"(.*?)",\n', chunk, re.S)),
                "raw": chunk,
            }
        )
    return out


def test_templates_are_discoverable() -> None:
    """A parse that silently found nothing would make every check below vacuous."""
    templates = _templates()
    assert len(templates) >= 4
    assert {t["id"] for t in templates} >= {
        "weeklySalesDigest",
        "refundWatch",
        "agentBriefing",
        "monthlyReport",
    }


def test_template_names_match_the_api_slug_rule() -> None:
    """Mirrors `_RECIPE_NAME_RE` — a template that cannot be saved is worthless."""
    pattern = re.compile(r"^[a-z0-9][a-z0-9-]{1,62}[a-z0-9]$")
    for tpl in _templates():
        assert pattern.match(tpl["name"]), f"{tpl['id']}: bad slug {tpl['name']!r}"


def test_template_actions_are_in_the_allowlist() -> None:
    allowed = {"pg.query", "agent.run", "slack.post", "email.send", "http.notify"}
    for tpl in _templates():
        assert tpl["actions"], f"{tpl['id']} has no steps"
        unknown = set(tpl["actions"]) - allowed
        assert not unknown, f"{tpl['id']} uses unlisted action(s): {unknown}"


def test_template_sql_only_reads_allowlisted_tables() -> None:
    """`_ALLOWLISTED_TABLES` in service.py is the real gate; a template that
    queries anything else compiles fine and then 422s at run time."""
    allowed = _py_set("_ALLOWLISTED_TABLES")
    for tpl in _templates():
        for table in re.findall(r"FROM\s+([a-z_][a-z0-9_]*)", tpl["sql"], re.I):
            assert table in allowed, f"{tpl['id']} reads {table}, not in {allowed}"


def test_template_sql_is_read_only() -> None:
    forbidden = ("INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE", "GRANT")
    for tpl in _templates():
        upper = tpl["sql"].upper()
        for word in forbidden:
            assert word not in upper, f"{tpl['id']} SQL contains {word}"


def test_template_slack_channels_are_allowlisted() -> None:
    allowed = _py_set("_ALLOWLISTED_CHANNELS")
    for tpl in _templates():
        for channel in tpl["channels"]:
            assert channel in allowed, f"{tpl['id']} posts to {channel}, not in {allowed}"


def test_template_email_domains_are_allowlisted() -> None:
    allowed = _py_set("_ALLOWED_EMAIL_DOMAINS")
    for tpl in _templates():
        for address in tpl["emails"]:
            domain = address.split("@")[-1]
            assert domain in allowed, f"{tpl['id']} mails {domain}, not in {allowed}"


def test_template_agents_are_seeded() -> None:
    """`agent.run` naming an agent `make seed` never creates would fail live."""
    seeded = set(re.findall(r'"([a-z_]+)"', SEED_PY.read_text(encoding="utf-8").split("]")[0]))
    for tpl in _templates():
        for agent in tpl["agents"]:
            assert agent in seeded, f"{tpl['id']} runs unseeded agent {agent!r}"


def test_only_email_templates_are_flagged_as_needing_approval() -> None:
    """`needsApproval` drives a badge the reader trusts, so it must track the
    actual `write:external` action rather than being maintained by hand."""
    for tpl in _templates():
        flagged = "needsApproval: true" in tpl["raw"]
        writes = "email.send" in tpl["actions"]
        assert flagged == writes, f"{tpl['id']}: needsApproval={flagged} but writes={writes}"


@pytest.mark.parametrize("locale", ["tr", "en"])
def test_every_template_has_copy_in_both_locales(locale: str) -> None:
    messages = _messages(locale)
    for tpl in _templates():
        for field in ("title", "description", "when"):
            key = f"builder.templates.{tpl['id']}.{field}"
            value = _resolve(messages, key)
            assert isinstance(value, str) and value.strip(), f"{locale}: missing {key}"


# --- chat starters -------------------------------------------------------

def _starters() -> list[tuple[str, int]]:
    source = STARTERS_TS.read_text(encoding="utf-8")
    return [
        (agent, int(count))
        for agent, count in re.findall(r'agent: "([^"]+)", count: (\d+)', source)
    ]


@pytest.mark.parametrize("locale", ["tr", "en"])
def test_every_starter_question_exists_in_both_locales(locale: str) -> None:
    """`count` is what the component loops to; a mismatch renders a raw key."""
    messages = _messages(locale)
    starters = _starters()
    assert starters, "no starters parsed"
    for agent, count in starters:
        for index in range(1, count + 1):
            key = f"chat.starters.{agent}.q{index}"
            value = _resolve(messages, key)
            assert isinstance(value, str) and value.strip(), f"{locale}: missing {key}"
        extra = f"chat.starters.{agent}.q{count + 1}"
        assert _resolve(messages, extra) is None, (
            f"{locale}: {extra} exists but count={count}, so it is never rendered"
        )


def test_starter_agents_are_seeded() -> None:
    seeded = set(re.findall(r'"([a-z_]+)"', SEED_PY.read_text(encoding="utf-8").split("]")[0]))
    for agent, _ in _starters():
        assert agent in seeded, f"starters defined for unseeded agent {agent!r}"


# --- guide walkthroughs --------------------------------------------------

def _walkthroughs() -> list[tuple[str, int]]:
    source = GUIDE_TS.read_text(encoding="utf-8")
    chunks = re.split(r'\n    id: "', source)[1:]
    return [
        (chunk[: chunk.index('"')], int(re.search(r"steps: (\d+)", chunk).group(1)))
        for chunk in chunks
    ]


@pytest.mark.parametrize("locale", ["tr", "en"])
def test_every_walkthrough_step_exists_in_both_locales(locale: str) -> None:
    messages = _messages(locale)
    walkthroughs = _walkthroughs()
    assert len(walkthroughs) >= 4
    for wid, steps in walkthroughs:
        for field in ("title", "intro", "cta"):
            key = f"guide.walkthroughs.{wid}.{field}"
            assert isinstance(_resolve(messages, key), str), f"{locale}: missing {key}"
        for index in range(1, steps + 1):
            key = f"guide.walkthroughs.{wid}.s{index}"
            value = _resolve(messages, key)
            assert isinstance(value, str) and value.strip(), f"{locale}: missing {key}"
        extra = f"guide.walkthroughs.{wid}.s{steps + 1}"
        assert _resolve(messages, extra) is None, (
            f"{locale}: {extra} exists but steps={steps}, so it is never rendered"
        )


def test_walkthrough_links_point_at_real_templates() -> None:
    """A walkthrough deep-linking `?template=` at an id that no longer exists
    would drop the reader into a blank form mid-instruction."""
    ids = {t["id"] for t in _templates()}
    source = GUIDE_TS.read_text(encoding="utf-8")
    for referenced in re.findall(r"\?template=([A-Za-z0-9]+)", source):
        assert referenced in ids, f"guide links to unknown template {referenced!r}"
