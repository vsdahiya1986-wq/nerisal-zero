# CLAUDE.md — NERISAL ZERO (Team WINNERS, GATEWAYS 2026)

You are helping a 4-person student team build and demo **NERISAL ZERO** in a 24-hour hackathon.
Read this file fully before changing anything. The demo story is more important than any new feature.

## What this is
Domain 4 "Crisis Command – Multi-Agent Emergency Response & Resource Coordination".
Our angle: mass-gathering emergencies (crowd crush / stampede). India lost 120+ people to stampedes in 2025
(Karur, Tamil Nadu: 41 dead). The system predicts a crush before it happens, coordinates ambulances, police,
volunteers, hospitals and announcements, re-plans live when anything changes, and keeps a human in charge of
every risky decision.

## Run
```
pip install -r requirements.txt
cd backend && python -m uvicorn app:app --reload --port 8000
# http://localhost:8000   commander dashboard (tabs: Live / Permit test / After-action)
# http://localhost:8000/marshal?zone=B   phone view for ground marshals
python -m pytest -q        # from project root - MUST stay green
```

## Architecture (backend/)
- `engine.py` – shared situation state, scenario clock, crowd + unit simulation, agent orchestration,
  **no-action twin** (`self.baseline`, same events, no approvals), **Decision Preview** (`preview(pid)` clones the
  engine and runs approve vs reject 10 minutes ahead), after-action report.
- `scenario.py` – ALL demo data: road graph, zones, gates, hospitals, units, timed events. Edit data here, not in agents.
- `agents/crowd.py` – Crowd Pressure Agent: density, 10-min forecast, risk level, gate/halt proposals, Tamil/English/Hindi announcements.
- `agents/triage.py` – Incident Triage Agent: multilingual parsing (Claude if `ANTHROPIC_API_KEY`, else rules), duplicate merge, **Silent Alarm** (3+ crowding reports in 15 min).
- `agents/route.py` – Corridor & Route Agent: networkx road graph, crowd slows vehicles, Gate 4 corridor, blocked roads.
- `agents/resource.py` – Resource Allocation Agent: Hungarian assignment (scipy), cost = time-criticality × ETA, unmet penalty, switch penalty.
- `agents/hospital.py` – Hospital Surge Agent: distribute casualties by free beds vs nearest-only baseline.
- `agents/command.py` – Command Agent: Fragility Score, coverage gaps, Plan Diff, reasons, human-approval gate.
- `agents/llm.py` – the ONLY Claude client (model via `ANTHROPIC_MODEL`, default `claude-opus-5`; 8 s timeout, no SDK retries).
- `agents/explain.py` – "Explain" on Plan Diff lines: Claude rewords diff + reasons into English + Tamil; template fallback.
- `cap.py` – CAP 1.2 public-alert XML for an announcement (ElementTree, status always "Exercise").
- `permit.py` – pre-event Permit Stress-Test (transparent planning model, editable assumptions).
- `app.py` – FastAPI routes: /api/state, /step, /reset, /report, /decide, /preview/{id}, /explain?v=&i=, /cap/{announcement_id}, /aar, /permit. `/api/state` includes `impact` (live vs twin).
- Frontend: `frontend/index.html` (vanilla JS + Leaflet, no build step), `frontend/marshal.html`.

## Non-negotiable rules
1. **Tests stay green.** `tests/test_demo_invariants.py` encodes the demo story (crush at T+10 with no action;
   averted if Gate 4 + stop-entry approved at T+1; silent alarm by T+7; stall detected; hospital plan avoids overload;
   risky actions never auto-apply). Run pytest after every change.
2. **Risky actions never auto-apply.** Opening gates, halting the event, diverting an en-route unit, mutual aid and
   reserves always go through `propose(...)` → human Approve/Reject.
3. **LLM only for language.** Allocation, routing, hospital distribution and forecasts are deterministic code.
   Any LLM call must have a timeout and a rule-based fallback. The demo must work with no internet.
4. **No new heavy dependencies** (no React build, no databases, no Docker required). Vanilla JS + FastAPI.
5. **Data is synthetic.** Never present hospital capacities or crowd numbers as real. Never name political parties
   or people in the UI, scenario or pitch.
6. **Keep the UI legible on a projector**: min 12px text, high contrast, no information only in colour.
7. Small, reviewable changes. Explain what you changed and how to see it in the demo.

## Demo-critical flows (do not break)
- Reset → +1 min → Zone B CRITICAL, cards "Stop entry at Gate 1" and "Open Gate 4".
- 🔮 Preview on "Open Gate 4" at T+1 → Approve: no crush; Reject: crush.
- Play to T+10 without approving → CROWD CRUSH banner, plan diff, fragility ~39 (47 by T+12), mutual-aid card (mass-casualty trigger), "Hold A4 in reserve" card, hospital panel shows nearest-only overload.
- T+13 → "STALL DETECTED: A2" in the log, police task created.
- After-action tab → live vs twin outcome, decision latency table.
- Judge types any report (Tamil/Tanglish/English) → incident appears; no location → "Confirm details" card.
