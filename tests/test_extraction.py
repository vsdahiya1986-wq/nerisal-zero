"""Casualty Extraction Path: what if the injured person is in the middle of the crowd?"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
os.environ.pop("ANTHROPIC_API_KEY", None)

from fastapi.testclient import TestClient  # noqa: E402

import app  # noqa: E402
from engine import Engine  # noqa: E402


def test_no_action_t11_has_crush_extraction_in_zone_b():
    e = Engine()
    e.step(11)
    x = [x for x in e.extractions() if x["title"] == "Crowd crush"]
    assert len(x) == 1 and x[0]["zone"] == "B"
    assert x[0]["responder"] and x[0]["gate_id"] in ("G3", "G4") and x[0]["total_min"] > 0
    assert x[0]["carry_min"] > 0 and len(x[0]["steps"]) == 4


def test_make_way_announcement_exactly_once():
    e = Engine()
    e.step(15)
    mw = [a for a in e.st["announcements"] if a.get("kind") == "make_way"]
    assert len(mw) == 1 and mw[0]["zone"] == "B"
    assert mw[0]["ta"].startswith("மருத்துவக் குழு வருகிறது") and mw[0]["en"].startswith("Medical team coming through")
    assert mw[0]["hi"].startswith("मेडिकल टीम")


def test_averted_run_has_no_crush_extraction():
    e = Engine()
    e.step(1)
    e.decide("open_G4", "approve")
    e.decide("stop_entry_G1", "approve")
    e.step(14)
    assert not [x for x in e.extractions() if x["title"] == "Crowd crush"]


def test_gate4_shortens_the_carry():
    closed, opened = Engine(), Engine()
    closed.step(11)
    opened.step(10)
    opened.decide("open_G4", "approve")
    opened.step(1)
    c, o = closed.extractions()[0], opened.extractions()[0]
    assert o["gate_id"] == "G4" and o["carry_min"] < c["carry_min"]


def test_state_and_pages_show_extraction():
    c = TestClient(app.app)
    c.post("/api/reset")
    assert c.get("/api/state").json()["extractions"] == []
    assert c.post("/api/step", json={"n": 11}).json()["extractions"]
    assert 'id="extract"' in c.get("/").text and "human chain" in c.get("/marshal").text.lower()
