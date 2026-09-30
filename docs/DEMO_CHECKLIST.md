# Demo checklist — NERISAL ZERO

Print this. Tick every box the night before AND 30 minutes before the slot.

## A. Laptop setup (night before)
- [ ] Python 3.10+ installed ("Add Python to PATH" ticked). Check: `python --version`.
- [ ] First run done **with internet**: double-click `run_windows.bat` (creates `.venv`, installs packages). After this, no internet is needed to start.
- [ ] `python -m pytest -q` from the project root → all green (17 tests).
- [ ] Browser: Chrome or Edge, **zoom 100%**, window maximised. At 1366×768 use the `⇥ Panel` button or fullscreen map as needed.
- [ ] Tamil voice installed: Windows Settings → Time & language → Language & region → add **Tamil** → Speech. Test: Live tab → any announcement → 🔊 தமிழ். If no Tamil voice, the button shows a message; use 🔊 English.
- [ ] Microphone allowed for localhost (for 🎤 Speak). Test once with a Tamil sentence.
- [ ] Charger, HDMI/USB-C adapter, phone charged (marshal page).
- [ ] Backup video of the full demo recorded and on the desktop **and** a USB stick.

## B. Wi-Fi-off test (do it once)
Turn Wi-Fi off, start the server, run Demo mode.
- Works offline: simulation, all agents, Preview, twin chart, Permit test, After-action, rule-based triage, Explain (template), 🔊 voices installed in Windows.
- Needs internet: **map background tiles** (roads/zones/units still draw on a dark background), **🎤 Speak** (Chrome sends audio to Google), Claude triage/Explain (falls back to rules/template automatically).
- If venue Wi-Fi is flaky: **unset `ANTHROPIC_API_KEY`** so a typed report never waits 8 s for a timeout.

## C. Start (30 min before)
1. Double-click `run_windows.bat` → browser opens http://localhost:8000.
2. Header shows `T+0 min`. Click **⟲ Reset**.
3. Phone for marshal page: stop the server, run from `backend`: `..\.venv\Scripts\python -m uvicorn app:app --host 0.0.0.0 --port 8000`, allow the Windows Firewall prompt, open `http://<laptop IP>:8000/marshal?zone=B` on the phone (same Wi-Fi). `ipconfig` shows the IP.

## D. Run 1 — nobody acts (click path, expected screen)
| Step | Click | You should see |
|---|---|---|
| 1 | Permit test tab → *Rally, 10k declared* preset | 1×: CONDITIONS · 2× and 2.7×: NO-GO · 2.7× needs 14 ambulances (6 planned), danger at stage in 4 min |
| 2 | Live tab → ⟲ Reset → Venue | 3 incidents from Tanglish/Tamil/English reports, units on map |
| 3 | +1 min | Zone B **CRITICAL**, forecast > 5. Cards: *Stop entry at Gate 1*, *Open Gate 4* |
| 4 | 🔮 Preview on *Open Gate 4* | Table: Crowd crush **no** (approve) vs **YES** (reject). **Do not approve.** |
| 5 | ▶ Play | T+7: orange **SILENT ALARM · Zone B** banner |
| 6 | Pause at T+10 | Red **CROWD CRUSH** banner. Fragility **39**. Cards: halt event, **mutual aid** (mass-casualty), **Hold A4 in reserve**. Hospital panel: nearest-only overloads KMCH, our plan doesn't. Open incidents card: crush has the steepest line |
| 7 | Explain on a Plan Diff line | Reason appears under the line (template, or Claude + Tamil with a key) |
| 8 | Approve *mutual aid* | A7, A8 join; Fragility **39 → 16** |
| 9 | Play to T+13 | Log: **STALL DETECTED: A2**, police task created |
| 10 | Judge types a report | `someone collapsed` → "Confirm details" card (no guessing) |

**Hands-free alternative:** 🎬 Demo mode plays steps 2–9 (without approvals) automatically; Pause stops it.

## E. Run 2 — act early
| Step | Click | You should see |
|---|---|---|
| 1 | ⟲ Reset → +1 min | Same two cards |
| 2 | Approve *Stop entry* and *Open Gate 4* | Gate 4 turns green, corridor opens |
| 3 | ▶ Play to T+12 | Green **CRUSH AVERTED** banner. Chart: live line stays under 5, twin line crosses it |
| 4 | After-action tab | Live: no crush vs twin: crush at T+10; decision latency table |

## F. If something breaks
- **Clock shows "⚠ server not responding"**: the server crashed or was closed. Close the black window, double-click `run_windows.bat` again, press ⟲ Reset, jump with +1 min / Play to where you were (≈10 s).
- **Page frozen / weird state**: ⟲ Reset. Every run is deterministic, so the same clicks give the same screen.
- **Map blank**: no internet for tiles. Keep going; everything on the map still draws. Say "tiles need internet, the system doesn't".
- **Voice silent**: use the English button, or read the Tamil line aloud yourself.
- **Laptop dead**: play the backup video from USB on any machine.

## G. Say this if asked
All data is synthetic. Hospital beds, crowd numbers and the permit assumptions are adjustable planning values, not official standards.
