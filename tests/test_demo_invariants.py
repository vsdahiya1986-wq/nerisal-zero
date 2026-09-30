"""
Demo invariants. If any of these fail, the live demo story is broken.
Run from the project root:  python -m pytest -q
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
os.environ.pop("ANTHROPIC_API_KEY", None)  # tests always use the offline rule parser

from engine import Engine  # noqa: E402
from agents.triage import IncidentTriageAgent  # noqa: E402


def run_no_action(minutes=15):
    e = Engine()
    e.step(minutes)
    return e


def test_no_action_run_has_crush_at_t10():
    e = run_no_action(12)
    assert e.st["crush_minute"] == 10


def test_early_actions_avert_crush():
    e = Engine()
    e.step(1)
    e.decide("open_G4", "approve")
    e.decide("stop_entry_G1", "approve")
    e.step(14)
    assert e.st["crush_minute"] is None
    assert e.st["averted"] is True
    assert e.baseline.st["crush_minute"] == 10  # the twin still had it


def test_silent_alarm_fires_before_crush():
    e = run_no_action(8)
    assert any(a["id"].startswith("silent_") for a in e.st["approvals"].values())


def test_stall_detected_without_a_report():
    e = run_no_action(15)
    assert any("STALL DETECTED" in l["msg"] for l in e.st["log"])
    assert e.st["units"]["A2"]["status"] in ("unavailable", "available")


def test_hospital_plan_avoids_overload_that_nearest_only_causes():
    e = run_no_action(10)
    hp = e.st["hospital_plan"]
    assert hp["overload_naive"] and not hp["overload_plan"]


def test_decision_preview_shows_prevention():
    e = Engine()
    e.step(1)
    p = e.preview("open_G4")
    assert p["reject"]["crush"] and not p["approve"]["crush"]


def test_multilingual_triage():
    t = IncidentTriageAgent()
    assert t.parse("குழந்தை காணவில்லை zone A")["type"] == "missing_child"
    assert t.parse("Zone D-la oru aal mayakkam")["type"] == "faint"
    assert t.parse("stampede near stage")["type"] == "crush"
    assert t.parse("someone collapsed")["location"] is None  # must not guess


def test_mutual_aid_card_at_crush_but_not_applied():
    e = run_no_action(10)
    assert e.st["approvals"]["mutual_aid"]["status"] == "pending"
    assert "A7" not in e.st["units"]
    assert "mutual_aid" not in run_no_action(9).st["approvals"]


def test_risky_actions_never_auto_apply():
    e = run_no_action(12)
    assert e.st["gates"]["G4"]["open"] is False
    assert e.st["venue"]["event_halted"] is False
