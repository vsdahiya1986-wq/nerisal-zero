"""CAP 1.2 public alert export."""
import os
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
os.environ.pop("ANTHROPIC_API_KEY", None)

from fastapi.testclient import TestClient  # noqa: E402

import app  # noqa: E402

NS = {"cap": "urn:oasis:names:tc:emergency:cap:1.2"}


def client_with_announcement():
    c = TestClient(app.app)
    c.post("/api/reset")
    st = c.post("/api/step", json={"n": 1}).json()
    assert st["announcements"], "demo should have an announcement by T+1"
    return c, st["announcements"][0]


def test_cap_xml_is_valid_exercise_with_tamil_and_english():
    c, ann = client_with_announcement()
    r = c.get(f"/api/cap/{ann['id']}")
    assert r.status_code == 200 and "xml" in r.headers["content-type"]
    root = ET.fromstring(r.content)
    assert root.tag == "{urn:oasis:names:tc:emergency:cap:1.2}alert"
    assert root.find("cap:status", NS).text == "Exercise"
    assert root.find("cap:sent", NS).text.endswith("+05:30")
    infos = root.findall("cap:info", NS)
    assert [i.find("cap:language", NS).text for i in infos] == ["ta-IN", "en-IN"]
    ta = infos[0].find("cap:instruction", NS).text
    assert ta and ta == ann["ta"]  # Tamil survives the round trip unmangled
    assert infos[1].find("cap:instruction", NS).text == ann["en"]
    assert infos[0].find("cap:area/cap:circle", NS).text.endswith(" 0.5")


def test_cap_unknown_id_is_404():
    c, _ = client_with_announcement()
    assert c.get("/api/cap/NOPE").status_code == 404


def test_page_has_public_alert_modal():
    html = TestClient(app.app).get("/").text
    assert 'id="capdlg"' in html and "Public alert" in html and "EXERCISE / DEMO" in html
