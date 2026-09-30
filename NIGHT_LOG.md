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
