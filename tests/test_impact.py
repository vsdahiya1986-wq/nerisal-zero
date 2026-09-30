"""Impact score: live vs no-action twin."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
os.environ.pop("ANTHROPIC_API_KEY", None)

from fastapi.testclient import TestClient  # noqa: E402

from engine import Engine  # noqa: E402


def test_no_action_live_equals_twin():
    e = Engine()
    e.step(12)
    imp = e.impact()
    assert imp["live"] == imp["twin"]
    assert imp["live"]["crush"] and imp["live"]["people_minutes_above_5"] > 0


def test_averted_run_beats_twin():
    e = Engine()
    e.step(1)
    e.decide("open_G4", "approve")
    e.decide("stop_entry_G1", "approve")
    e.step(14)
    live, twin = e.impact()["live"], e.impact()["twin"]
    assert live["crush"] is False and twin["crush"] is True
    assert live["people_minutes_above_5"] < twin["people_minutes_above_5"]


def test_api_state_and_page_have_impact():
    import app
    c = TestClient(app.app)
    c.post("/api/reset")
    assert "impact" in c.get("/api/state").json()
    assert "impact" in c.get("/api/aar").json()
    html = c.get("/").text
    assert 'id="impact"' in html and 'id="aarimpact"' in html
