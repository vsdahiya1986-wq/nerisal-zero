"""Offline guarantees: only map tiles come from the internet; no-network paths degrade gracefully."""
import os
import re
import socket
import sys
from types import SimpleNamespace

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
os.environ.pop("ANTHROPIC_API_KEY", None)

from fastapi.testclient import TestClient  # noqa: E402

import app  # noqa: E402

FRONT = os.path.join(os.path.dirname(__file__), "..", "frontend")


def test_pages_load_nothing_from_the_internet_except_map_tiles():
    for name in os.listdir(FRONT):
        if not name.endswith(".html"):
            continue
        html = open(os.path.join(FRONT, name), encoding="utf-8").read()
        urls = set(re.findall(r"https?://[^\"'`\s)]+", html)) - {"http://www.w3.org/2000/svg"}
        assert urls <= {"https://tile.openstreetmap.org/{z}/{x}/{y}.png"}, (name, urls)
        for ref in re.findall(r'(?:src|href)="(/[^"$]+)"', html):  # local assets exist
            assert TestClient(app.app).get(ref.split("?")[0]).status_code == 200, ref


def test_qr_works_without_any_network(monkeypatch):
    class NoNet:
        def __init__(self, *a, **k):
            pass

        def connect(self, *a):
            raise OSError("network unreachable")

        def close(self):
            pass
    # only the app's socket module: the test client itself still needs real sockets
    monkeypatch.setattr(app, "socket", SimpleNamespace(socket=NoNet, AF_INET=socket.AF_INET, SOCK_DGRAM=socket.SOCK_DGRAM))
    q = TestClient(app.app).get("/api/pulse/qr").json()
    assert q["url"].startswith("http://127.0.0.1:") and q["svg"]


def test_no_api_key_means_rules_and_template():
    c = TestClient(app.app)
    assert c.get("/api/health").json()["llm"] is False
    c.post("/api/reset")
    st = c.post("/api/report", json={"text": "fire near gate 3"}).json()
    assert any("parser: rules" in l["msg"] for l in st["log"])


def test_qr_uses_public_url_when_hosted(monkeypatch):
    monkeypatch.setenv("RENDER_EXTERNAL_URL", "https://nerisal-zero.onrender.com/")
    assert TestClient(app.app).get("/api/pulse/qr").json()["url"] == "https://nerisal-zero.onrender.com/pulse"
