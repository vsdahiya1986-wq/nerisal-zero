"""Evidence Lab: deterministic, advice helps, default demo untouched."""
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
os.environ.pop("ANTHROPIC_API_KEY", None)

from fastapi.testclient import TestClient  # noqa: E402

import app  # noqa: E402
import evidence  # noqa: E402
from engine import Engine  # noqa: E402


def test_same_seed_same_result():
    assert evidence.run_lab(10, seed0=7) | {"seconds": 0} == evidence.run_lab(10, seed0=7) | {"seconds": 0}


def test_advice_never_worse_than_no_action():
    d = evidence.run_lab(10)
    s = {p: d["policies"][p]["summary"] for p in evidence.POLICIES}
    assert s["advised"]["crush_rate"] <= s["no_action"]["crush_rate"]
    assert s["advised"]["peak_b_median"] <= s["no_action"]["peak_b_median"]


def test_default_engine_still_crushes_at_t10():
    e = Engine()
    e.step(12)
    assert e.st["crush_minute"] == 10


def test_variant_crush_report_only_when_physics_says_so():
    # advised policy on a seed that starts below crush density: no crush incident is ever created
    d = evidence.run_one(3, "advised")
    v = evidence.make_variant(3)
    assert not any(ev["type"] == "report" and "STAMPEDE" in ev["text"] for ev in v["events"])
    if not d["crush"]:
        e = Engine(variant=v, twin=False)
        e.step(30)  # no action: physics decides
        assert any(i["type"] == "crush" for i in e.st["incidents"].values()) == (max(r["B"] for r in e.st["series"]) >= 5.0)


def test_api_evidence_missing_then_background_run(tmp_path, monkeypatch):
    monkeypatch.setattr(app, "EVIDENCE_JSON", str(tmp_path / "evidence.json"))
    monkeypatch.setattr(app, "DOCS_DIR", str(tmp_path))
    c = TestClient(app.app)
    assert c.get("/api/evidence").json()["missing"] is True
    assert c.post("/api/evidence/run", json={"n": 10}).status_code == 200
    for _ in range(200):
        if not app.lab["running"]:
            break
        time.sleep(0.1)
    d = c.get("/api/evidence").json()
    assert d["n"] == 10 and "headline" in d and "runs" not in d["policies"]["advised"]
    assert c.post("/api/evidence/run", json={"n": 10}).status_code == 409  # never overwrite existing evidence


def test_committed_evidence_is_served_and_tab_present():
    c = TestClient(app.app)
    d = c.get("/api/evidence").json()
    assert d.get("n") == 200 and set(d["policies"]) == set(evidence.POLICIES)
    assert c.get("/evidence.png").status_code == 200
    html = c.get("/").text
    assert 'data-v="evidence"' in html and 'id="evbody"' in html
