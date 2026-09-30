"""Citizen Pulse: attendees' phones as sensors."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
os.environ.pop("ANTHROPIC_API_KEY", None)

from fastapi.testclient import TestClient  # noqa: E402

import app  # noqa: E402
import pulse  # noqa: E402
from engine import Engine  # noqa: E402


def fresh_client():
    app.last_tap.clear()
    c = TestClient(app.app)
    c.post("/api/reset")
    return c


def test_rate_limit_per_device():
    c = fresh_client()
    assert c.post("/api/pulse", json={"zone": "B", "kind": "ok", "device": "phone1"}).status_code == 200
    r = c.post("/api/pulse", json={"zone": "B", "kind": "ok", "device": "phone1"})
    assert r.status_code == 429 and r.json()["retry_after_s"] > 0
    assert c.post("/api/pulse", json={"zone": "B", "kind": "ok", "device": "phone2"}).status_code == 200


def test_bad_zone_or_kind_rejected():
    c = fresh_client()
    assert c.post("/api/pulse", json={"zone": "Z", "kind": "ok", "device": "x1"}).status_code == 400
    assert c.post("/api/pulse", json={"zone": "B", "kind": "party", "device": "x2"}).status_code == 400


def test_six_cant_move_taps_create_one_crowding_report():
    e = Engine()
    e.step(1)
    for i in range(6):
        pulse.tap(e, "B", "cant_move", f"d{i}")
    inc = [i for i in e.st["incidents"].values() if i["type"] == "pressure" and i["location"] == "B"]
    assert len(inc) == 1 and inc[0]["texts"][0].startswith("Citizen Pulse")
    assert sum("Citizen Pulse" in l["agent"] for l in e.st["log"]) == 1  # 6th tap does not spam a 2nd report
    assert e.baseline.st["incidents"]  # the twin sees the same world


def test_pulse_reports_merge_and_can_trigger_silent_alarm():
    e = Engine()
    e.step(4)  # scripted crowding report in B exists
    for i in range(5):
        pulse.tap(e, "B", "cant_move", f"d{i}")
    e.step(2)  # T+6 scripted report arrives
    assert any(a["id"].startswith("silent_") for a in e.st["approvals"].values())


def test_medical_tap_creates_confirm_card():
    e = Engine()
    e.step(1)
    g = pulse.tap(e, "C", "medical", "m1")
    iid = g["fed_incident"]
    assert iid and e.st["approvals"][f"confirm_{iid}"]["status"] == "pending"
    assert e.st["incidents"][iid]["confidence"] <= 0.4


def test_lost_child_tap_creates_missing_child():
    e = Engine()
    g = pulse.tap(e, "A", "lost_child", "k1")
    assert e.st["incidents"][g["fed_incident"]]["type"] == "missing_child"


def test_guidance_changes_when_zone_b_is_critical():
    e = Engine()
    e.st["zones"]["B"]["risk"] = "normal"
    calm = pulse.guidance(e, "A")
    e.st["zones"]["B"]["risk"] = "critical"
    warn = pulse.guidance(e, "A")
    assert calm["en"] != warn["en"] and "Zone B" in warn["en"] and "மண்டலம் B" in warn["ta"]


def test_pulse_page_has_four_buttons_and_dashboard_card():
    c = fresh_client()
    html = c.get("/pulse").text
    for kind in pulse.KINDS:
        assert f'data-kind="{kind}"' in html
    for ta, en in pulse.KINDS.values():
        assert ta in html and en in html
    dash = c.get("/").text
    assert 'id="pulse"' in dash and "Simulate 60 attendees" in dash and "Copy SMS" in dash


def test_simulate_qr_and_sms():
    c = fresh_client()
    st = c.post("/api/pulse/simulate", json={"n": 60}).json()
    assert sum(z["total"] for z in st["pulse"].values()) == 60
    q = c.get("/api/pulse/qr").json()
    assert q["url"].endswith("/pulse") and q["svg"].startswith("<svg")
    ann = c.post("/api/step", json={"n": 1}).json()["announcements"][0]["id"]
    s = c.get(f"/api/sms/{ann}").json()
    assert 0 < s["chars"] <= 160 and "EXERCISE" in s["text"] and "மண்டலம்" in s["text"]
    assert c.get("/api/sms/NOPE").status_code == 404
