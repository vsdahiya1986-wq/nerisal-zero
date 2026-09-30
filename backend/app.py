"""
NERISAL ZERO - API server.
Run:  python -m uvicorn app:app --port 8000   (from the backend folder)
Then open http://localhost:8000          (commander dashboard)
          http://localhost:8000/marshal  (phone view for ground marshals)
"""
import os
import threading
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from agents.explain import explain
from cap import build_cap
from engine import Engine
from permit import assess

app = FastAPI(title="NERISAL ZERO")
engine = Engine()
lock = threading.Lock()
FRONT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))
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


@app.get("/api/health")
def health():
    return {"ok": True, "llm": bool(os.environ.get("ANTHROPIC_API_KEY"))}
