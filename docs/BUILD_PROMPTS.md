# Claude Code prompts — copy, paste, verify

Open the project folder in Claude Code. It reads `CLAUDE.md` automatically. Use these prompts **in order**.
After each one: run `python -m pytest -q`, open the dashboard, and check the "Verify" line yourself.
If something breaks, say: *"Revert your last change, tests are failing: <paste error>."*

---

## Phase 0 — Understand (everyone, hour 0–1)
**Prompt 0.1**
> Read CLAUDE.md and every file in backend/ and frontend/. Explain to a first-year student, in 15 bullet points,
> how one re-plan works from a new field report to the dashboard. Then list the 5 functions I must understand to answer judges.

Verify: each teammate can explain one agent in 30 seconds.

---

## Phase 1 — Make the demo bullet-proof (hour 1–5)
**Prompt 1.1 (Vinith)**
> Add a "Demo mode" button in the header that runs the full scripted story automatically: reset, step to T+1,
> pause 4 s, open the preview for "Open Gate 4", then continue to T+14 at 1 step per 1.5 s. It must stop if I press Pause.
> Do not change the engine. Keep tests green.

Verify: one click plays the whole Run 1 hands-free.

**Prompt 1.2 (Mahima)**
> Improve projector legibility of frontend/index.html: minimum 12px text, zone labels on the map at least 13px with dark halo,
> add a fullscreen toggle for the map, and make the right column collapsible. No new libraries.

Verify: readable from the back of a classroom at 1366×768.

**Prompt 1.3 (Preetha)**
> Write tests for agents/resource.py: (a) an ALS need is never filled by a BLS unit, (b) a unit already on scene is never
> reassigned, (c) when 2 incidents compete for 1 ambulance, the higher-weight incident gets it. Fix bugs you find.

---

## Phase 2 — Make the AI visibly intelligent (hour 5–12)
**Prompt 2.1 (Vikram)**
> In agents/triage.py, make the Claude path production-grade: 8-second timeout, JSON schema validation with pydantic,
> retry once, then fall back to rules. Log which parser was used. Add a unit test that monkeypatches the client to raise,
> and asserts the rule parser is used.

**Prompt 2.2 (Vikram)**
> Add an optional "Explain" button on each Plan Diff item. If ANTHROPIC_API_KEY is set, send the structured plan diff and
> reasons (not raw state) to Claude and show a 2-sentence plain-English + Tamil explanation for the commander.
> Without a key, show the existing template reason. Never let the LLM change the plan.

**Prompt 2.3 (Preetha)**
> Add a small "time-criticality" sparkline next to each open incident in the right panel: expected harm vs minutes of delay,
> using weight() from agents/resource.py. Pure SVG.

---

## Phase 3 — Depth features (hour 12–18) — pick at most TWO
**Prompt 3.1 (Mahima) – Replay scrubber**
> Store a snapshot every minute in engine.st["history"] (only the fields the dashboard needs). Add a timeline scrubber under
> the map that lets me drag back to any minute and see the map and panels as they were. Live mode resumes on release.

**Prompt 3.2 (Vinith) – Second scenario**
> In scenario.py, refactor so multiple scenarios can exist (dict of name → data). Add "Temple festival" with 4 zones around a
> temple car route and a surge at a narrow street. Add a scenario dropdown in the header that resets into that scenario.
> Keep the rally scenario the default and keep tests green.

**Prompt 3.3 (Vikram) – Voice report**
> In the "New field report" card, add a 🎤 button using the Web Speech API (lang ta-IN, fallback en-IN) that fills the textarea.
> Show a clear message if the browser does not support it.

**Prompt 3.4 (Preetha) – Reserve optimiser**
> In the Fragility card, show which single idle unit, if held in reserve, lowers the Fragility Score the most (try each one
> with resource.solve and the existing shock). Offer it as the "Hold in reserve" proposal instead of the first idle unit.

---

## Phase 4 — Freeze and rehearse (hour 18–24)
**Prompt 4.1**
> Code freeze. Review the whole project for crashes: missing keys, None values, division by zero, empty lists in the
> frontend render(). Fix only crash bugs. Do not add features. Run tests.

**Prompt 4.2**
> Generate docs/DEMO_CHECKLIST.md: laptop setup (Python version, how to start, Tamil voice installed, browser zoom 100%,
> Wi-Fi off test), the exact click-path for Run 1 and Run 2 with expected screen at each step, and a fallback plan if the server crashes.

Rule: nothing new after hour 20. Rehearse three times. Record a backup video of the full demo.
