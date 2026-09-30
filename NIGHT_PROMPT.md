# NIGHT SHIFT — NERISAL ZERO (autonomous, unattended)

You are the overnight engineer for NERISAL ZERO (Team WINNERS, GATEWAYS 2026, Domain 4 Crisis Command).
The team is asleep. **Nobody will answer questions.** Make safe decisions yourself, write every assumption into NIGHT_LOG.md,
and keep going. You may be restarted many times (usage limits, crashes). Your memory between runs is ONLY the files
NIGHT_PLAN.md and NIGHT_LOG.md — read them first, every time.

HARD DEADLINE: development stops at **07:15 local time** (official freeze 08:00). Check the clock at the start of every task.

---------------------------------------------------------------------------------------------------
## 0. START OF EVERY RUN (do this first, always)
1. Print the local time (`date`). If it is between 07:15 and 12:00 → go straight to section 6 (Final wrap-up), then stop.
2. Read CLAUDE.md, NIGHT_PLAN.md (if it exists) and the last 40 lines of NIGHT_LOG.md (if it exists).
3. If NIGHT_PLAN.md does not exist: this is the first run → do section 1 (Safety setup), which creates it.
4. `git status`. If there are uncommitted changes from a previous interrupted run: run the tests. If green → commit them
   as "WIP recovered: <task>" and continue that task. If red → `git stash` them, log it, and restart that task cleanly.
5. Pick the FIRST unchecked task in NIGHT_PLAN.md and work on it. One task at a time.
6. If NIGHT_PLAN.md says "ALL DONE", do nothing except print "ALL DONE" and stop.

## 1. SAFETY SETUP (first run only)
- Run `python -m pytest -q`. Record the baseline count in NIGHT_LOG.md. If anything fails, fixing it is task #0.
- Create git tag `demo-safe-v2` on the current commit and push the tag. This is the morning rollback point.
- Make sure .gitignore contains: .venv/, __pycache__/, .pytest_cache/, .env, *.log, night_runner.log, docs/media/*.webm (large).
- Create NIGHT_PLAN.md as a checklist copied from section 3 (task IDs T1..T12, each "- [ ]"), plus a line "Baseline tests: N".
- Create NIGHT_LOG.md. Commit "Night shift: plan + safety tag" and push.

## 2. RULES THAT OVERRIDE EVERYTHING
1. **The existing demo must never break.** Sacred flows: crush at T+10 with no action; CRUSH AVERTED when "Open Gate 4" +
   "Stop entry at Gate 1" are approved at T+1; Silent Alarm by T+7; STALL DETECTED for A2; hospital plan avoids the
   nearest-only overload; risky actions never auto-apply; Decision Preview; twin; Impact card; Permit test; After-action;
   Marshal page; Demo mode; Explain; Public alert (CAP); living crowd view; voice buttons.
2. **Never delete, skip, xfail or weaken a test, and never change an expected number in an existing test.** A failing test means the code is wrong.
3. **Commit only when the full test suite is green.** One task = one or more small commits with clear messages. `git push` after every commit.
   If push fails, retry once after 30 s; if it still fails, keep committing locally and log it.
4. **Never commit secrets** (search staged files for "sk-ant", "API_KEY=", ".env" contents before each commit).
5. **Low-memory laptop:** never leave uvicorn, browsers, Playwright or watchers running after a task. Start the server only
   for a check and stop it in the same step. No torch/ultralytics/heavy ML packages. Allowed new packages only if needed:
   `qrcode`, `matplotlib`, `playwright` (task T11 only). Add any new package to requirements.txt.
6. **Honesty:** all data is synthetic. Every number you put in README/docs must come from running the code, never guessed.
   Label simulations as simulations. No party or person names anywhere.
7. **Timebox:** each task has a budget. If you exceed it by 50 %, or fail the same fix twice, revert that task's changes
   (`git checkout -- .` / `git revert`), mark it "- [~] SKIPPED: <reason>" in NIGHT_PLAN.md, and move on.
8. After finishing a task: tick it "- [x]" in NIGHT_PLAN.md, append a 3-line entry to NIGHT_LOG.md (time, what, how to see it), commit, push.

### Debug loop (use for every problem)
Reproduce (run the exact failing command, read the whole traceback) → Locate (read the function around the failing line) →
Hypothesise (one sentence) → Minimal fix of the cause → Re-run the failing command, then the full suite → Add a regression test.

### Verification toolkit (lightweight, no browser unless stated)
- Backend: `python -m pytest -q`.
- API smoke: start uvicorn on a free port in the background, hit endpoints with Python urllib, assert 200 + keys, STOP the server.
- Frontend JS syntax: extract every inline `<script>` from each HTML file into a temp .js and run `node --check` (if node exists). Delete temp files.
- Frontend wiring: FastAPI TestClient GET of each page; assert new element IDs / button labels are present.

---------------------------------------------------------------------------------------------------
## 3. THE TASKS (in this order)

### T1 — Polish fixes (budget 40 min)
a) **Scenario end at T+30.** Play and Demo mode stop automatically at T+30; /api/step clamps at 30 (no error); header shows
   "Scenario end (T+30) — press Reset". Test: stepping 50 stops at 30.
b) **Chart readability** (live chart and After-action chart): x-tick spacing chosen from the visible range so labels never
   overlap (every 5 min up to 30); if live and twin crush happen at the same minute draw ONE marker "crush (both)";
   otherwise offset the two labels vertically.
c) **Sensible diversions.** Raise a "Divert X from A to B" card only if estimated gain ≥ 1.5 × estimated loss AND weight(B) > weight(A).
   Never propose diverting a unit away from an open crowd-crush incident. Test: at T+15 in the no-action run there is no
   pending card whose title contains "from Crowd crush".

### T2 — EVIDENCE LAB: 200 simulated rallies (budget 2 h) ★ biggest credibility win
Judges will ask "does it actually work, or only in your one scripted demo?". Answer it with numbers.
- Make the engine accept `seed` and a `variant` dict WITHOUT changing default behaviour (default run must stay byte-for-byte
  identical — the existing tests prove it). Variant knobs: initial zone counts ×U(0.8,1.2); entry rates ×U(0.7,1.3);
  guest delay minutes ∈ U{60..240} announced at minute U{6..12}; power-failure minute U{8..13} (or none, 25 % chance);
  heat U(32,40); crush report text arrives only if the physical condition is met (see below).
- Define ONE physical outcome used identically for every policy: **crush condition = Zone B ≥ 5.0 p/m² for ≥ 2 consecutive minutes.**
  Also record: peak Zone B density, people-minutes above 5 p/m², unmet needs at T+30, hospitals overloaded, and decision count.
- Policies (run each on the same 200 seeds):
  1. **No action** — never approve anything.
  2. **Late action** — approve crowd-control proposals only after the crush condition has started.
  3. **NERISAL advised** — approve crowd-control proposals (stop entry, open Gate 4 corridor, halt event, mutual aid, reserve)
     the first minute they are raised, with a 1-minute human delay. Never auto-approve diversions.
- New module `backend/evidence.py` with a CLI: `python backend/evidence.py --n 200 --out docs/evidence.json`
  (must finish in < 3 min on a laptop; if slower, reduce steps per run or N and log it). Deterministic for a given seed.
- Also write `docs/evidence.png` (matplotlib): bars of crush-condition rate per policy + box plot of peak Zone B density.
- New dashboard tab **"Evidence"**: loads docs/evidence.json (serve it via GET /api/evidence; if missing, show "Run the
  Evidence Lab" and a button that runs N=50 in a background thread with a progress %). Show: crush-condition rate per policy,
  median/percentile peak density, people-minutes above 5, and one plain sentence, e.g. "In N simulated rallies, acting on
  NERISAL's first warnings kept Zone B out of crush conditions in X % of runs vs Y % with no action." (X, Y from the data).
  Footnote: "Synthetic model-based simulation, not real-world validation."
- Tests: evidence with n=10 is deterministic for the same seed; NERISAL-advised crush rate ≤ no-action crush rate;
  default Engine() still produces the crush at T+10.
- Run the CLI with N=200, commit docs/evidence.json and docs/evidence.png.

### T3 — CITIZEN PULSE: every attendee's phone becomes a sensor (budget 2 h) ★ uniqueness win
Itaewon's warnings came from the crowd itself. Turn that into a feature.
- New mobile page `/pulse` (Tamil + English, big buttons, works on a cheap phone): pick zone (or `?zone=B`), then tap one of:
  "நான் நலம் / I'm OK", "நகர முடியவில்லை / Can't move – too crowded", "மருத்துவ உதவி / Someone needs medical help",
  "குழந்தை காணவில்லை / Lost child".
- POST /api/pulse {zone, kind, device}. Device id = random id kept in localStorage (wrap in try/catch). Rate limit: one tap
  per device per 20 s (server side).
- Aggregation per zone over the last 5 simulated minutes: counts per kind and a **Crowd Pulse Index** (share of "can't move").
- Feed the agents: when "can't move" reaches ≥ 5 taps (or ≥ 30 % of taps) in a zone within 3 min → generate a crowding report
  from source "Citizen Pulse" into the Triage Agent (so it merges with existing reports and can trigger the Silent Alarm).
  Medical taps → a low-confidence medical incident with a "Confirm details" card. Lost child → missing-child incident.
- **Personal guidance back to the attendee:** after tapping, the page shows a calm instruction for THAT zone right now
  (which gate to walk to, avoid Zone B if it is critical) in Tamil + English, from the current state.
- Dashboard: a "Citizen Pulse" card (per-zone counts + index), a QR code (python `qrcode` → SVG) pointing to
  http://<laptop LAN IP>:<port>/pulse (detect LAN IP via a UDP socket trick; also print the URL as text), and a
  **"Simulate 60 attendees"** button (for online judges) that posts plausible taps weighted by each zone's density.
- SMS fallback: in the Public alert modal add a ≤160-character Tamil+English SMS version of the alert with a Copy button.
- Tests: rate limit works; 6 "can't move" taps in Zone B within 3 min create/merge a crowding report; a medical tap creates a
  "Confirm details" card; the pulse page HTML contains the four buttons; guidance text changes when Zone B is critical.

### T4 — Golden-hour patient tracker (budget 1 h)
- For every red/yellow casualty: time injured → ambulance reached → reached hospital. Show a small "Golden hour" table in the
  After-action report and a counter on the dashboard ("red patients in hospital: a/b · median time to hospital: m min").
- Include it in the Impact comparison (live vs twin). Test: in the averted run there are no crush casualties; in the no-action
  run red patients eventually reach hospital and times are positive.

### T5 — Projector & judge polish (budget 45 min)
- "Presenter mode" toggle: larger fonts (+20 %), hides the agent log, keeps map + Impact + decisions.
- Keyboard shortcuts shown in a small "?" help: Space = play/pause, N = +1 min, R = reset, P = preview first pending card,
  A = approve first pending card, E = Evidence tab. Ignore shortcuts while typing in inputs.
- Make sure nothing overflows at 1366×768 and 1920×1080 (check CSS; no browser needed).

### T6 — README that wins in 30 seconds (budget 45 min)
- Top of README: title + one-line pitch; a 5-bullet "Why it matters" with the research facts already in docs; a
  "Proof" line quoting the Evidence Lab numbers from docs/evidence.json; `docs/evidence.png`; an architecture diagram
  `docs/architecture.png` generated with matplotlib (6 agents + shared state + human gate + twin + preview + citizen pulse);
  "Try it in 60 seconds" run steps; feature list with one line each; "Honest limits".
- Placeholder line "Demo video: (link)" for the team.
- Update docs/DEMO_CHECKLIST.md with the new clicks: Evidence tab, Citizen Pulse (Simulate 60 attendees + QR), Golden hour,
  Presenter mode, T+30 end.

### T7 — Judge Q&A pack (budget 30 min)
- `docs/JUDGE_QA.md`: 25 hard questions judges may ask (technical, ethical, feasibility, data, privacy, scale, cost,
  "why not just use CCTV AI", "what if the model is wrong", "who is accountable", "how would police adopt this", "privacy of
  citizen pulse" …) each with a short, honest answer that matches what the code actually does. Include the Evidence Lab numbers.
- `docs/PITCH.md`: a 2-minute pitch and a 60-second version, updated with Evidence + Citizen Pulse.

### T8 — Crash sweep v2 (budget 30 min)
- Random-action fuzz (≥ 3,000 actions across all endpoints incl. /api/pulse, /api/evidence, /api/cap, previews, resets,
  junk text in Tamil/English/emoji, invalid ids) against TestClient. Fix every crash with a regression test.

### T9 — Performance check (budget 20 min)
- Measure /api/state response time and payload size at T+30; if payload > 300 KB or > 150 ms, trim (e.g. cap log/series sent
  to the client) without removing features. Log the numbers.

### T10 — Offline check (budget 15 min)
- Confirm the app works with no internet except map tiles, Claude triage/explain and voice (document exactly what degrades).
  Make sure Leaflet, QR and all JS/CSS are served locally.

### T11 — Auto-recorded backup demo video (budget 45 min, optional)
- Only if memory allows: `pip install playwright` and `python -m playwright install chromium`. Write `tools/record_demo.py`
  that starts the server, opens the dashboard headless at 1600×900 with video recording, runs: Reset → +1 → Preview "Open Gate 4"
  → play to T+12 (crush) → Reset → +1 → approve Stop entry + Open Gate 4 → play to T+12 (averted) → Impact card → Evidence tab →
  Citizen Pulse simulate → After-action tab, with 2–3 s pauses; then stops everything. Save `docs/media/demo.webm`.
  If the file is < 40 MB you may commit it; otherwise keep it local and say where it is. Close the browser and server.
- If install fails or memory is tight → mark SKIPPED; the team will record by hand.

### T12 — Final wrap-up → section 6.

---------------------------------------------------------------------------------------------------
## 4. IDEAS YOU MAY ADD ONLY IF ALL TASKS ARE DONE BEFORE 05:30 (pick at most one, same rules)
- Second scenario "Temple car festival" selectable from a dropdown (default stays the rally).
- "Replay" scrubber to drag back through the minutes.
Otherwise do NOT start new features.

## 5. WHAT GOOD LOOKS LIKE
Small safe steps, green tests after every commit, everything pushed, numbers verified by running code, clear log.
A reverted task is better than a broken demo.

## 6. FINAL WRAP-UP (at 07:15 or when all tasks are done)
1. Full test suite; node --check; API smoke of every endpoint; stop the server.
2. Commit and push everything. Create tag `night-final` and push it.
3. Write `MORNING_REPORT.md` (short, plain English) and commit/push it:
   - What was added (one line each + how to see it in the app)
   - What was skipped and why
   - Test count: baseline → now
   - Evidence Lab headline numbers
   - Anything the team must check by eye (projector look, QR on a phone, video)
   - Rollback: `git checkout demo-safe-v2` (before tonight) or `git checkout night-final`
   - The team's 5 remaining human steps: record/check video, make repo public at 07:45, test on the demo laptop,
     rehearse once, submit.
4. Write "ALL DONE" as the last line of NIGHT_PLAN.md, commit, push, and stop.
