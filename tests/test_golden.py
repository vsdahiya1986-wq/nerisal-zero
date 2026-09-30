"""Golden-hour patient tracker."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
os.environ.pop("ANTHROPIC_API_KEY", None)

from fastapi.testclient import TestClient  # noqa: E402

import app  # noqa: E402
from engine import Engine  # noqa: E402


def test_averted_run_has_no_crush_patients():
    e = Engine()
    e.step(1)
    e.decide("open_G4", "approve")
    e.decide("stop_entry_G1", "approve")
    e.step(29)
    crush_ids = {i["id"] for i in e.st["incidents"].values() if i["type"] == "crush"}
    assert not crush_ids
    assert not [p for p in e.st.get("patients", []) if p["incident"] in crush_ids]


def test_no_action_red_patients_reach_hospital_with_positive_times():
    e = Engine()
    e.step(30)
    g = e.golden(e.st)
    assert g["red"]["total"] > 0 and g["red"]["in_hospital"] >= 1
    done = [p for p in e.st["patients"] if p["at_hospital"] is not None]
    assert done and all(p["at_hospital"] > p["injured"] and p["reached"] >= p["injured"] for p in done)


def test_opening_gate4_at_t10_gets_crush_patients_to_hospital_sooner():
    slow, fast = Engine(), Engine()
    slow.step(30)
    fast.step(10)
    fast.decide("open_G4", "approve")
    fast.step(20)
    assert fast.golden(fast.st)["red"]["in_hospital"] > slow.golden(slow.st)["red"]["in_hospital"]


def test_golden_in_state_impact_and_aar():
    c = TestClient(app.app)
    c.post("/api/reset")
    st = c.post("/api/step", json={"n": 20}).json()
    assert "golden" in st and "red_not_in_hospital" in st["impact"]["live"]
    aar = c.get("/api/aar").json()
    assert "golden" in aar and all("hospital_name" in p for p in aar["patients"])
    html = c.get("/").text
    assert 'id="golden"' in html and 'id="aargold"' in html
