# Night log

00:07 — Setup. Baseline 24 tests passing. Tag demo-safe-v2 = state before the night shift.
Note: night_runner.ps1 could not be launched from the Claude session (blocked by the auto-mode safety classifier:
it spawns Claude with all permissions skipped). The same tasks are being done directly in the open Claude session instead.

00:25 — T1 done. Scenario ends at T+30 (engine clamps, Play stops, header "Scenario end (T+30) — press Reset").
Chart ticks adapt to width; same-minute crushes draw one "crush (both)" marker. Divert cards only when gain ≥ 1.5× loss,
the new incident weighs more, and never away from a crowd crush (the T+15 "Divert A6 from Crowd crush" card is gone). 27 tests.

01:05 — T2 done. Evidence Lab: 200 randomised rallies × 3 policies, same seeds (python backend/evidence.py --n 200, 21 s).
NERISAL advised: 73 % of all runs stay out of crush conditions vs 0 % no action and 0 % late action (late still cuts median peak 8.45 → 5.19).
51/200 runs START at crush density (Zone B ×1.085+ of 4.61 p/m²) — no warning can prevent those; of the other 149, 98 % stay safe with advice.
Assumption: kept the spec's ×0.8–1.2 range and reported that subset separately instead of shrinking the range. See: Evidence tab.
Default demo proven byte-identical over 30 min after the engine change. 33 tests.

01:50 — T3 done. Citizen Pulse: /pulse phone page (4 big Tamil+English buttons, zone picker, personal advice from live state),
POST /api/pulse (20 s per-device rate limit), 5+ "can't move" taps (or 30 %+ of ≥3) in 3 min → one Triage report (merges, can fire
Silent Alarm), medical → low-confidence incident + Confirm card, lost child → missing-child incident. Dashboard card with index,
QR (LAN IP), "Simulate 60 attendees". SMS fallback (136/160 chars) in the Public alert modal. 42 tests.
Assumption: the twin also receives citizen reports (same world; only the commander's approvals differ).

02:15 — T4 done. Golden hour: every transported red/yellow patient recorded (injured → ambulance reached → at hospital).
Dashboard: line in the Hospital card; After-action: per-patient table; Impact rows "Red patients not yet in hospital" and
"Median min injury → hospital". Finding (from the engine, not tuned): no action → by T+30 only 1 of 5 red patients is in
hospital (the T+0 road accident); A1, parked at Gate 4, is still stuck en route to the crush. Approving Gate 4 at T+10 → first
crush patient in hospital at T+20. Default run byte-identical (tracking only). 46 tests.

02:45 — T5 done. Presenter mode (A+ button or F): cards/chart 20 % bigger, agent log hidden, remembered per browser.
Shortcuts (? shows them): Space play/pause, N +1, R reset, P preview first pending, A approve first pending, E Evidence, L Live, F presenter.
Measured in Chrome (iframes, no window resize): header had overflowed at 1920 px (+140 px) and would at 1366; fixed (hide subtitle ≤2100,
KPIs/City/speed ≤1400 — same facts shown elsewhere) → last button at 1356/1366 and 1906/1920, no card overflow, no text < 12 px, both modes.
Shortcuts verified live (R, N, A approves Open Gate 4, typing ignored, help, E/L). 47 tests.

03:10 — T6 done. README top rewritten: pitch, 5 "why it matters" facts (from docs/BRAINSTORM.md), Proof line from docs/evidence.json,
evidence.png, new docs/architecture.png (tools/architecture.py), Try it in 60 s, one-line features, honest limits, "Demo video: (link)".
DEMO_CHECKLIST: Evidence tab, Simulate 60 attendees + QR, Golden hour line, presenter tips, T+30 end — each claim re-checked by running the engine.
Removed a politician's name from a source title in BRAINSTORM.md (night rule 6).

03:30 — T7 done. docs/JUDGE_QA.md (25 questions: works?, AI, why-not, privacy/accountability, feasibility) and docs/PITCH.md
(2-min + 60-s). Every number re-checked against code: removed two claims I could not verify (a "hundreds of units in ms" speed
claim and "holding areas" in permit conditions) and replaced them with measured / actual wording.

03:45 — T8 done. Crash sweep v2: 3,200 random actions over every endpoint (step/report/decide/preview/reset/state/aar/permit/cap/sms/
explain/pulse/pulse-simulate/guidance/qr/evidence/evidence-run/png/pages) with Tamil/English/emoji/huge/null-byte/HTML junk and invalid
ids → 0 server errors. Added tests/test_fuzz.py (400 actions, fixed seed) so it stays that way. 48 tests.

04:05 — T9 done (no change needed). At T+30 after 60 pulse taps: /api/state 38 KB, median 5 ms (limits 300 KB / 150 ms); /api/aar 16 KB 5 ms;
Preview 26–65 ms first call, ~8 ms cached; Evidence 13 ms; Simulate 60 attendees 16 ms; one step round-trip 20 ms (TestClient, this laptop).
04:10 — T10 done. Only external resource: OSM map tiles. Leaflet, QR (server-side SVG), chart, all JS/CSS local. Degrades offline:
map tiles, 🎤 Speak (Chrome → Google), Claude triage/Explain (→ rules/template), online-only Chrome voices. New tests/test_offline.py
enforces "no external URL except tiles", local assets exist, QR works with no network (127.0.0.1), no key → rules. Checklist B updated
(hotspot tip for phones). 51 tests.

04:15 — T11 SKIPPED (by the plan's own rule): 0.5 GB RAM free of 7.7 GB; installing + running Playwright Chromium with video
could get processes killed. The team records the backup video by hand (DEMO_CHECKLIST section A).

04:40 — Extra (section 4): Replay scrubber. Amber slider under the map; drag to any minute → map + all panels as they were
(frozen deep copies, one per minute, live engine only; previews/twin/Evidence runs keep none). Release or leave the slider → live.
Twin now steps minute-by-minute inside step() so each frame shows both worlds at the same minute — default run byte-identical.
Cost: 6.5 ms/step, ~1 MB per 30-min run. Verified in Chrome: T+1 no banner, T+7 Silent Alarm, T+10 crush; polling ignored during
replay; any action returns to live. 55 tests.
