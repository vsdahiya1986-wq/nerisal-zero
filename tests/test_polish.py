"""T1 polish: scenario end at T+30, sensible diversion cards."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
os.environ.pop("ANTHROPIC_API_KEY", None)

from fastapi.testclient import TestClient  # noqa: E402

import app  # noqa: E402
from engine import Engine  # noqa: E402


def test_scenario_stops_at_t30():
    e = Engine()
    e.step(30)
    e.step(20)
    assert e.st["minute"] == 30 and e.baseline.st["minute"] == 30


def test_api_step_clamps_without_error():
    c = TestClient(app.app)
    c.post("/api/reset")
    for _ in range(3):
        r = c.post("/api/step", json={"n": 20})
        assert r.status_code == 200
    assert r.json()["minute"] == 30 and r.json()["end_minute"] == 30


def test_no_card_pulls_help_away_from_a_crush():
    e = Engine()
    e.step(15)
    pending = [a["title"] for a in e.st["approvals"].values() if a["status"] == "pending"]
    assert not any("from Crowd crush" in t for t in pending)
