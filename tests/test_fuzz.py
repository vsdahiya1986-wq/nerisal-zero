"""Crash sweep: random actions against every endpoint must never produce a server error (5xx)."""
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
os.environ.pop("ANTHROPIC_API_KEY", None)

from fastapi.testclient import TestClient  # noqa: E402

import app  # noqa: E402

JUNK = ["", "stampede near stage", "someone collapsed", "குழந்தை காணவில்லை zone A", "🔥 fire gate 3 😱", "x" * 5000,
        "zone Z 999999 injured", "<img src=x onerror=alert(1)>", "null\x00byte"]


def test_random_actions_never_500():
    rng = random.Random(7)
    c = TestClient(app.app)
    c.post("/api/reset")
    for _ in range(400):
        s = c.get("/api/state").json()
        pend = [a["id"] for a in s["approvals"] if a["status"] == "pending"] or ["NOPE"]
        anns = [a["id"] for a in s["announcements"]] + ["NOPE"]
        op = rng.randrange(12)
        if op < 3:
            r = c.post("/api/step", json={"n": rng.choice([1, 1, 3, -2, 99])})
        elif op == 3:
            r = c.post("/api/report", json={"text": rng.choice(JUNK)})
        elif op == 4:
            r = c.post("/api/decide", json={"id": rng.choice(pend + ["NOPE", ""]), "decision": rng.choice(["approve", "reject", "x"])})
        elif op == 5:
            r = c.get("/api/preview/" + rng.choice(pend))
        elif op == 6:
            r = c.get(rng.choice(["/api/cap/", "/api/sms/"]) + rng.choice(anns))
        elif op == 7:
            r = c.get(f"/api/explain?v={rng.randint(-1, 30)}&i={rng.randint(-1, 9)}")
        elif op == 8:
            r = c.post("/api/pulse", json={"zone": rng.choice("ABCDZ"), "kind": rng.choice(["ok", "cant_move", "medical", "bad"]),
                                           "device": f"f{rng.randint(0, 999)}"})
        elif op == 9:
            r = c.post("/api/pulse/simulate", json={"n": rng.choice([1, 60, -1])})
        elif op == 10:
            r = c.post("/api/permit", json={"declared": rng.choice([0, -1, 10000]), "area_m2": rng.choice([0, 12000]),
                                            "exit_width_m": rng.choice([0, 20]), "multipliers": rng.choice([[], [1.0, 2.7]])})
        else:
            r = c.post("/api/reset") if rng.random() < 0.3 else c.get("/api/aar")
        assert r.status_code < 500, (op, r.status_code, r.text[:200])
