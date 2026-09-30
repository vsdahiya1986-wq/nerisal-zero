"""Replay scrubber: one frozen dashboard frame per minute."""
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
os.environ.pop("ANTHROPIC_API_KEY", None)

from fastapi.testclient import TestClient  # noqa: E402

import app  # noqa: E402
from engine import Engine  # noqa: E402


def test_frames_are_frozen_copies():
    e = Engine()
    e.step(1)
    b1 = e.history[1]["zones"]["B"]["density"]
    assert e.history[1]["zones"]["B"]["risk"] == "critical"
    e.step(9)
    assert e.history[1]["zones"]["B"]["density"] == b1  # later minutes never change an old frame
    assert sorted(e.history) == list(range(11))
    assert e.history[10]["crush_minute"] == 10 and e.history[10]["baseline"]["crush_minute"] == 10  # twin in step


def test_decision_updates_the_frame_of_that_minute():
    e = Engine()
    e.step(1)
    e.decide("open_G4", "approve")
    assert e.history[1]["gates"]["G4"]["open"] is True


def test_previews_and_evidence_runs_keep_no_history():
    e = Engine()
    e.step(3)
    assert e.clone().history == {}
    assert Engine(twin=False).history == {}
    t = time.perf_counter()
    e.preview(next(a["id"] for a in e.st["approvals"].values() if a["status"] == "pending"))
    assert time.perf_counter() - t < 2.0


def test_history_endpoint_and_scrubber_present():
    c = TestClient(app.app)
    c.post("/api/reset")
    c.post("/api/step", json={"n": 5})
    assert c.get("/api/history/3").json()["minute"] == 3
    assert c.get("/api/history/99").status_code == 404
    html = c.get("/").text
    assert 'id="scrub"' in html and "endReplay" in html
