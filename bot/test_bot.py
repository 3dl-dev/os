"""Tests for the Atom Teams Bot — card builders and command parsing."""

import json
import sys
import os
import types

# Add bot directory to path
sys.path.insert(0, os.path.dirname(__file__))

# Mock botbuilder modules so we can test without the SDK installed
for mod_name in [
    "botbuilder", "botbuilder.core", "botbuilder.core.teams",
    "botbuilder.schema", "botframework", "botframework.teams",
    "aiohttp",
]:
    if mod_name not in sys.modules:
        m = types.ModuleType(mod_name)
        # Add stub classes that bot.py imports
        if mod_name == "botbuilder.core":
            m.TurnContext = type("TurnContext", (), {})
            m.CardFactory = type("CardFactory", (), {"adaptive_card": staticmethod(lambda x: x)})
            m.BotFrameworkAdapter = type("BotFrameworkAdapter", (), {})
            m.BotFrameworkAdapterSettings = type("BotFrameworkAdapterSettings", (), {})
            m.InvokeResponse = type("InvokeResponse", (), {"__init__": lambda self, **kw: None})
        if mod_name == "botbuilder.core.teams":
            m.TeamsActivityHandler = type("TeamsActivityHandler", (), {})
        if mod_name == "botbuilder.schema":
            m.Activity = type("Activity", (), {})
            m.ActivityTypes = type("ActivityTypes", (), {"message": "message"})
        sys.modules[mod_name] = m

import cards
from bot import _extract_bead_id, _strip_mention, _extract_project, AtomBot


# ---- Unit tests for helpers ----

def test_extract_bead_id():
    assert _extract_bead_id("show os-mjb") == "os-mjb"
    assert _extract_bead_id("show me 3dl-k3e please") == "3dl-k3e"
    assert _extract_bead_id("galtrader-d0a is blocked") == "galtrader-d0a"
    assert _extract_bead_id("no bead here") is None
    assert _extract_bead_id("") is None


def test_strip_mention():
    assert _strip_mention("<at>Atom</at> help") == "help"
    assert _strip_mention("<at>3DL OS Bot</at> show os-mjb") == "show os-mjb"
    assert _strip_mention("plain text") == "plain text"
    assert _strip_mention("") == ""


def test_extract_project():
    assert _extract_project("list 3dl") == "3dl"
    assert _extract_project("show me galtrader beads") == "galtrader"
    assert _extract_project("what's the os status?") == "os"
    assert _extract_project("hello") is None


def test_project_from_bead_id():
    assert AtomBot._project_from_bead_id("os-mjb") == "os"
    assert AtomBot._project_from_bead_id("3dl-k3e") == "3dl"
    assert AtomBot._project_from_bead_id("galtrader-d0a") == "galtrader"
    assert AtomBot._project_from_bead_id("vms-123") == "vms"
    assert AtomBot._project_from_bead_id("unknown-xyz") is None


# ---- Unit tests for card builders ----

def test_bead_card():
    bead = {
        "id": "os-mjb",
        "title": "Teams bot MVP",
        "status": "in_progress",
        "priority": 1,
        "assignee": "baron",
        "type": "task",
        "description": "Build the Teams bot.",
    }
    card = cards.bead_card(bead)
    assert card["type"] == "AdaptiveCard"
    assert card["version"] == "1.4"
    # Should have actions for open bead
    assert len(card["actions"]) == 2
    assert card["actions"][0]["data"]["action"] == "claim"


def test_bead_card_closed():
    bead = {
        "id": "os-o01",
        "title": "API layer",
        "status": "closed",
        "priority": 0,
        "assignee": "baron",
        "type": "task",
    }
    card = cards.bead_card(bead)
    # Closed beads should have no claim/close actions
    assert len(card["actions"]) == 0


def test_bead_list_card():
    beads = [
        {"id": "os-mjb", "title": "Teams bot", "status": "open", "priority": 1},
        {"id": "os-9fj", "title": "GitHub Actions", "status": "open", "priority": 1},
    ]
    card = cards.bead_list_card(beads, title="Test List")
    assert card["body"][0]["text"] == "Test List"
    # Header + 2 bead rows
    assert len(card["body"]) == 3


def test_bead_list_card_empty():
    card = cards.bead_list_card([], title="Empty")
    assert any("No beads found" in str(item) for item in card["body"])


def test_ready_card():
    card = cards.ready_card([{"id": "x-1", "title": "Test", "status": "open", "priority": 0}])
    assert card["body"][0]["text"] == "Ready Work"


def test_help_card():
    card = cards.help_card()
    assert card["type"] == "AdaptiveCard"
    assert any("ready" in str(item).lower() for item in card["body"])


def test_close_prompt_card():
    card = cards.close_prompt_card("os-mjb")
    assert card["body"][0]["text"] == "Close os-mjb"
    # Should have input field
    assert card["body"][1]["type"] == "Input.Text"
    assert card["actions"][0]["data"]["action"] == "close"


def test_error_card():
    card = cards.error_card("Something broke")
    body_text = " ".join(str(item) for item in card["body"])
    assert "Something broke" in body_text


def test_projects_card():
    projects = [
        {"name": "os", "prefix": "os", "has_beads": True},
        {"name": "3dl", "prefix": "3dl", "has_beads": True},
    ]
    card = cards.projects_card(projects)
    assert card["body"][0]["text"] == "Registered Projects"


def test_confirmation_card():
    card = cards.confirmation_card("Done!")
    body_text = " ".join(str(item) for item in card["body"])
    assert "Done!" in body_text


def test_text_card():
    card = cards.text_card("Hello", title="Greeting")
    assert card["body"][0]["text"] == "Greeting"
    assert card["body"][1]["text"] == "Hello"


def test_bead_list_truncation():
    """List card should cap at 15 beads."""
    beads = [{"id": f"x-{i}", "title": f"Bead {i}", "status": "open", "priority": 2} for i in range(25)]
    card = cards.bead_list_card(beads)
    # Header + 15 beads + "...and N more" text
    assert len(card["body"]) == 17


def test_all_cards_valid_json():
    """All card builders should return JSON-serializable dicts."""
    test_cards = [
        cards.help_card(),
        cards.error_card("test"),
        cards.text_card("hello"),
        cards.confirmation_card("ok"),
        cards.close_prompt_card("x-1"),
        cards.bead_card({"id": "x-1", "title": "t", "status": "open", "priority": 1}),
        cards.bead_list_card([]),
        cards.ready_card([]),
        cards.projects_card([]),
    ]
    for c in test_cards:
        serialized = json.dumps(c)
        assert isinstance(serialized, str)
        parsed = json.loads(serialized)
        assert parsed["type"] == "AdaptiveCard"


# ---- Run ----

if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = 0
    failed = 0
    for t in tests:
        try:
            t()
            passed += 1
            print(f"  PASS  {t.__name__}")
        except Exception as e:
            failed += 1
            print(f"  FAIL  {t.__name__}: {e}")
    print(f"\n{passed} passed, {failed} failed")
    sys.exit(1 if failed else 0)
