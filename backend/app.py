"""
NERISAL ZERO - API server.
Run:  python -m uvicorn app:app --port 8000   (from the backend folder)
Then open http://localhost:8000          (commander dashboard)
          http://localhost:8000/marshal  (phone view for ground marshals)
"""
import io
import json
import os
import socket
import threading
import time
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from agents.explain import explain
import evidence
import pulse
from cap import build_cap, build_sms
from engine import Engine
from permit import assess

app = FastAPI(title="NERISAL ZERO")
engine = Engine()
lock = threading.Lock()
FRONT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))
DOCS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "docs"))
EVIDENCE_JSON = os.path.join(DOCS_DIR, "evidence.json")
lab = {"running": False, "progress": 0.0, "error": None}  # background Evidence Lab job
app.mount("/vendor", StaticFiles(directory=os.path.join(FRONT_DIR, "vendor")), name="vendor")


class Step(BaseModel):
    n: int = 1


class Report(BaseModel):
    text: str


class Decision(BaseModel):
    id: str
    decision: str  # "approve" | "reject"


class Permit(BaseModel):
    declared: int = 10000
    area_m2: float = 12000
    exit_width_m: float = 20
    ambulances: int = 6
    delay_min: int = 0
    heat_c: float = 32
    multipliers: List[float] = [1.0, 2.0, 2.7]
    assumptions: Optional[dict] = None


def snap():
    return JSONResponse(engine.snapshot())


@app.get("/")
def index():
    return FileResponse(os.path.join(FRONT_DIR, "index.html"))


@app.get("/pulse")
def pulse_page():
    return FileResponse(os.path.join(FRONT_DIR, "pulse.html"))


@app.get("/marshal")
def marshal():
    return FileResponse(os.path.join(FRONT_DIR, "marshal.html"))


@app.get("/api/state")
def state():
    with lock:
        return snap()


@app.post("/api/step")
def step(body: Step):
    with lock:
        engine.step(body.n)
        return snap()


@app.post("/api/reset")
def reset():
    with lock:
        engine.reset()
        return snap()


@app.post("/api/report")
def report(body: Report):
    with lock:
        if body.text.strip():
            engine.report(body.text.strip())
        return snap()


@app.post("/api/decide")
def decide(body: Decision):
    with lock:
        engine.decide(body.id, body.decision)
        return snap()


@app.get("/api/preview/{pid}")
def preview(pid: str):
    with lock:
        return JSONResponse(engine.preview(pid) or {})


@app.get("/api/explain")
def explain_diff(v: int, i: int):
    with lock:  # copy under the lock, call Claude outside it so a slow network never freezes the sim
        d = engine.st["last_diff"]
        if not d or d["version"] != v or not 0 <= i < len(d["items"]):
            return JSONResponse({"en": "The plan has changed since - press Explain on the new line.", "ta": None,
                                 "source": "stale"})
        item, reasons = dict(d["items"][i]), list(engine.st["reasons"])
    return JSONResponse(explain(item, reasons))


@app.get("/api/cap/{ann_id}")
def cap(ann_id: str):
    with lock:
        xml = build_cap(engine.st, ann_id)
    if xml is None:
        raise HTTPException(404, "Unknown announcement")
    return Response(xml, media_type="application/xml")


@app.get("/api/aar")
def aar():
    with lock:
        return JSONResponse(engine.after_action())


@app.post("/api/permit")
def permit(body: Permit):
    return JSONResponse(assess(body.declared, body.area_m2, body.exit_width_m, body.ambulances,
                               body.delay_min, body.heat_c, tuple(body.multipliers), body.assumptions))


class PulseTap(BaseModel):
    zone: str
    kind: str
    device: str = ""


class PulseSim(BaseModel):
    n: int = 60


PULSE_GAP_S = 20
last_tap = {}  # device id -> monotonic time of its last accepted tap


def _zone(z):
    z = (z or "").strip().upper()
    if z not in engine.st["zones"]:
        raise HTTPException(400, "Unknown zone")
    return z


@app.post("/api/pulse")
def pulse_tap(body: PulseTap):
    if body.kind not in pulse.KINDS:
        raise HTTPException(400, "Unknown kind")
    device = (body.device or "").strip()[:64] or "anonymous"
    now = time.monotonic()
    with lock:
        zid = _zone(body.zone)
        if now - last_tap.get(device, -1e9) < PULSE_GAP_S:
            wait = int(PULSE_GAP_S - (now - last_tap[device])) + 1
            return JSONResponse({"error": "rate_limited", "retry_after_s": wait,
                                 "ta": f"{wait} விநாடிகள் கழித்து மீண்டும் முயற்சிக்கவும்.",
                                 "en": f"Please wait {wait} seconds before tapping again."}, status_code=429)
        last_tap[device] = now
        if len(last_tap) > 20000:  # bounded memory
            last_tap.clear()
        return JSONResponse(pulse.tap(engine, zid, body.kind, device))


@app.get("/api/pulse/guidance")
def pulse_guidance(zone: str = "B"):
    with lock:
        return JSONResponse(pulse.guidance(engine, _zone(zone)))


@app.post("/api/pulse/simulate")
def pulse_simulate(body: PulseSim):
    with lock:
        pulse.simulate(engine, max(1, min(200, body.n)))
        return snap()


def lan_ip():
    """This laptop's address on the local network (no packets are sent)."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))
        return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        s.close()


@app.get("/api/pulse/qr")
def pulse_qr(request: Request):
    url = f"http://{lan_ip()}:{request.url.port or 8000}/pulse"
    try:
        import qrcode
        import qrcode.image.svg
        buf = io.BytesIO()
        qrcode.make(url, image_factory=qrcode.image.svg.SvgPathImage, border=2).save(buf)
        svg = buf.getvalue().decode("utf-8")
        svg = svg[svg.index("<svg"):]  # drop the XML declaration so it can be inlined
    except ImportError:
        svg = None  # the URL text still works
    return JSONResponse({"url": url, "svg": svg})


@app.get("/api/sms/{ann_id}")
def sms(ann_id: str):
    with lock:
        text = build_sms(engine.st, ann_id)
    if text is None:
        raise HTTPException(404, "Unknown announcement")
    return JSONResponse({"text": text, "chars": len(text)})


class LabRun(BaseModel):
    n: int = 50


@app.get("/api/evidence")
def get_evidence():
    """Summaries only (the per-run rows stay in docs/evidence.json)."""
    if not os.path.exists(EVIDENCE_JSON):
        return JSONResponse({"missing": True, "job": lab})
    with open(EVIDENCE_JSON, encoding="utf-8") as f:
        d = json.load(f)
    for p in d["policies"].values():
        p.pop("runs", None)
    d["job"] = lab
    return JSONResponse(d)


@app.post("/api/evidence/run")
def run_evidence(body: LabRun):
    # Only when no results exist: never overwrite the committed 200-run evidence from a button.
    if os.path.exists(EVIDENCE_JSON):
        raise HTTPException(409, "Evidence already exists")
    if lab["running"]:
        return JSONResponse({"job": lab})
    n = max(10, min(200, body.n))

    def work():
        try:
            data = evidence.run_lab(n, progress=lambda f: lab.update(progress=round(f, 3)))
            os.makedirs(DOCS_DIR, exist_ok=True)
            with open(EVIDENCE_JSON, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=1)
            try:
                evidence.write_png(data, os.path.join(DOCS_DIR, "evidence.png"))
            except ImportError:
                pass  # matplotlib is optional at run time; the tab still shows the numbers
        except Exception as e:  # report, never crash the server
            lab["error"] = f"{type(e).__name__}: {e}"
        finally:
            lab["running"] = False

    lab.update(running=True, progress=0.0, error=None)
    threading.Thread(target=work, daemon=True).start()
    return JSONResponse({"job": lab})


@app.get("/evidence.png")
def evidence_png():
    p = os.path.join(DOCS_DIR, "evidence.png")
    if not os.path.exists(p):
        raise HTTPException(404, "No chart yet")
    return FileResponse(p, media_type="image/png")


@app.get("/api/health")
def health():
    return {"ok": True, "llm": bool(os.environ.get("ANTHROPIC_API_KEY"))}
