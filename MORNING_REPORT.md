# Morning report — night shift, 1 Oct 2026

All 10 required tasks are done, the optional video was skipped (low memory), and one allowed extra (Replay) was added.
**55 tests pass (baseline 24).** Everything is committed and pushed to GitHub.

How the night ran: `night_runner.ps1` could not be started from the Claude session (Claude Code's safety check blocks launching
Claude with all permissions skipped). The same `NIGHT_PROMPT.md` tasks were done directly in the open session, 00:07–00:45,
one commit per task, tests green before every commit. Full detail: `NIGHT_LOG.md`.

## What was added (and how to see it)
| # | Feature | How to see it |
|---|---|---|
| T1 | Scenario ends at T+30; readable chart labels; no silly "divert from Crowd crush" cards | Play to the end: header "Scenario end (T+30) — press Reset" |
| T2 | **Evidence Lab**: 200 randomised rallies × 3 human policies | **Evidence** tab (or key E) |
| T3 | **Citizen Pulse**: attendees' phones as sensors, QR code, personal advice, SMS fallback | Left column card → **👥 Simulate 60 attendees**; phone page `/pulse`; Public alert window → Copy SMS |
| T4 | **Golden hour**: every red/yellow patient from injury to hospital | Hospital card line; After-action tab (bottom table); Impact card rows |
| T5 | **Presenter mode** (A+ or F) and **keyboard shortcuts** (press ?) | Header buttons A+ and ? |
| T6 | README rebuilt: pitch, why it matters, proof, charts, architecture diagram | `README.md`, `docs/evidence.png`, `docs/architecture.png` |
| T7 | 25 hard judge questions with honest answers; 2-min and 60-s pitch | `docs/JUDGE_QA.md`, `docs/PITCH.md` |
| T8 | Crash sweep: 3,200 random actions on every endpoint, 0 server errors | `tests/test_fuzz.py` keeps it that way |
| T9 | Performance: `/api/state` 38 KB, 5 ms at T+30 (limits 300 KB / 150 ms) | No change needed |
| T10 | Offline: only map tiles need internet (enforced by a test) | `docs/DEMO_CHECKLIST.md` section B |
| Extra | **Replay scrubber**: drag back to any minute, release for live | Amber slider under the map |

Also fixed tonight: the header overflowed at 1920 px (and would at 1366 px) — measured in Chrome and fixed; now it fits both, in
normal and presenter mode, with no text under 12 px.

## Skipped
- **T11 backup video**: only 0.5 GB of 7.7 GB RAM was free; running a recording browser risked crashing things. Record by hand.

## Evidence Lab headline (synthetic simulation, not real-world validation)
- NERISAL advised: **73 %** of 200 runs stayed out of crush conditions, vs **0 %** with no action and **0 %** with late action.
- 51 runs start already at crush density (nothing can prevent those). Of the other 149: **98 %** stayed safe with advice.
- Median peak Zone B density: 8.45 p/m² (no action) → 5.19 (late) → 4.79 (advised).

## Worth saying in the demo (all from running the code)
- No action: by T+30 only 1 of 5 red patients is in hospital; ambulance A1, parked at Gate 4, is still stuck behind the closed
  corridor. Approving Gate 4 at T+10 gets the first crush patient to hospital by T+20.
- Run 2 Impact card: crush no vs YES, peak 4.68 vs 6.03 p/m², red casualties 0 vs 4.

## Check by eye before the demo
1. **Projector**: living crowd dots, Impact card, presenter mode (A+). Everything was measured to fit 1366 and 1920 px wide.
2. **QR on a real phone**: start the server with `--host 0.0.0.0`, same Wi-Fi (or the laptop's hotspot), scan the Citizen Pulse QR, tap.
3. **Tamil voice + microphone** on the demo laptop.
4. **On a different laptop that already has a `.venv`**: run `.venv\Scripts\pip install -r requirements.txt` once (new: `matplotlib`,
   `qrcode`). Without `qrcode` the card shows the URL as text instead of a QR; nothing breaks.
5. Still open from before: test Claude with a real `ANTHROPIC_API_KEY` once, and ask the organisers whether starter code is allowed.

## Rollback
- Before tonight: `git checkout demo-safe-v2`
- Tonight's final state: `git checkout night-final` (back to latest: `git checkout main`)

## Your 5 remaining human steps
1. Record the backup demo video (and check it plays).
2. Make the repo public at 07:45: `gh repo edit vsdahiya1986-wq/nerisal-zero --visibility public --accept-visibility-change-consequences`
3. Test on the demo laptop (`run_windows.bat`, then Demo mode).
4. Rehearse once with `docs/DEMO_CHECKLIST.md` and `docs/PITCH.md`.
5. Submit.
