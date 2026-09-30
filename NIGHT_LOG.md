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
