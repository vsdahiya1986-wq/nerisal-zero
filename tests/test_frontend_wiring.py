"""The dashboard HTML contains the controls the demo relies on."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from fastapi.testclient import TestClient  # noqa: E402

import app  # noqa: E402


def test_living_crowd_canvas_and_toggle_present():
    html = TestClient(app.app).get("/").text
    assert 'id="crowdcanvas"' in html and 'id="crowdbtn"' in html and "Crowd view: ON" in html
    # existing demo controls still there
    for s in ("Demo mode", "Preview", 'id="chart"', "Fullscreen", "Speak", 'id="impact"'):
        assert s in html
