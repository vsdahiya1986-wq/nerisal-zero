# NERISAL ZERO — Team WINNERS · GATEWAYS 2026 · Domain 4 (Crisis Command)

நெரிசல் = crowd crush. A multi-agent command system that **sees a crowd crush coming, lets the commander test each decision
before taking it, and re-plans the whole emergency response live** — with a human approving every risky step.

- `CLAUDE.md` – project brief for Claude Code (read automatically).
- `docs/BRAINSTORM.md` – the research behind every feature, and the "what next" list.
- `docs/BUILD_PROMPTS.md` – copy-paste Claude Code prompts for the 24 hours, per person.
- `tests/` – demo invariants. `python -m pytest -q` must stay green.

---

## 1. Run it (5 minutes)
Python 3.10+ (python.org, tick "Add Python to PATH").

- **Windows:** double-click `run_windows.bat` → opens http://localhost:8000
- **Mac/Linux:** `./run_mac_linux.sh`
- **Manual:** `pip install -r requirements.txt` → `cd backend` → `python -m uvicorn app:app --port 8000`

Pages: **http://localhost:8000** (Live · Permit test · After-action tabs) and **http://localhost:8000/marshal?zone=B** (open on a phone
on the same Wi-Fi using the laptop's IP, e.g. http://192.168.x.x:8000/marshal — start uvicorn with `--host 0.0.0.0`).

Optional Claude triage: set `ANTHROPIC_API_KEY` and `ANTHROPIC_MODEL` (a current model id from docs.claude.com). Without it, the
offline Tamil/Tanglish/Hindi/English rule parser runs. The map tiles need internet; everything else works offline.

---

## 2. What's inside — six agents + four "out of the box" layers

| Agent | Job |
|---|---|
| Crowd Pressure | density per zone, 10-min forecast (heat, delay, power loss aggravate), gate/halt proposals, Tamil/English/Hindi announcements |
| Incident Triage | multilingual reports → structured incidents, duplicate merge, **Silent Alarm** |
| Corridor & Route | road graph; crowd slows vehicles; Gate 4 corridor; blocked roads; **stall detection** |
| Resource Allocation | Hungarian-algorithm assignment minimising expected harm; switch penalty; unmet needs shown |
| Hospital Surge | spreads casualties by free beds; compares with "nearest-only" |
| Command | Fragility Score, **coverage gaps**, Plan Diff, reasons, human-approval gate |

| Layer | Research it answers |
|---|---|
| 🔮 **Decision Preview** – every approval card can simulate approve vs reject 10 min ahead | Human-in-the-loop must be informed, not a rubber stamp |
| **No-action twin** – same scenario running in parallel with nobody acting; chart + after-action report | Proves the value of each decision |
| **Silent Alarm** – 3+ crowding reports from one zone in 15 min = one pattern alarm | Itaewon 2022: 11 calls in ~4 hours before the crush, handled one by one |
| **Coverage gaps + Fragility** – which zones have no free police / first aid; stress-test vs next shock | Kumbh 2025: AI cameras alerted, but police rushing to one spot left another uncovered |
| **Stall detection** – responding ambulance stops moving for 2 min → detected with no report | Karur 2025: ambulances surrounded and immobilised |
| **Permit Stress-Test** – test the organiser's plan at 1×/2×/2.7× turnout before permission | Karur: ~3× the expected crowd, 7-hour delay |
| **After-action report** – timeline, who approved what, decision latency, printable | Accountability without blame |
| **Marshal phone view** – big Tamil instructions per zone | Alerts must reach the people on the ground |

---

## What's new tonight
- **Impact score** – card at the top of the right column (and the top of the After-action report): your decisions vs the no-action twin. Run 2 at T+12: crush no vs YES (T+10), peak Zone B 4.68 vs 6.03 p/m², red casualties 0 vs 4, people-minutes above 5 p/m² 0 vs 67,834.
- **Public alert (CAP 1.2)** – 📢 *Public alert* on any announcement opens the alert as Common Alerting Protocol XML (Tamil + English, status *Exercise*), with Copy and Download. It is the format public warning systems ingest. Always labelled EXERCISE / DEMO.
- **Living crowd view** – animated dots on the map, 1 dot ≈ 50 people, coloured by density (teal < 4, amber ≥ 4, red ≥ 5 p/m²). Watch Zone B pack toward the stage, then stream out through Gate 4 once it is approved. Toggle: *Crowd view* next to Venue / City.

---

## 3. Demo script (8 minutes) — rehearse exactly

**0. Open (30 s).** "41 people died at Karur, 120+ in Indian stampedes in 2025. Every warning was visible. Nobody added them up."

**1. Before the event (1 min) — Permit test tab.** Click the *Rally, 10k declared* preset. "At the declared 10,000: conditions.
At 2.7× — what actually happened at Karur — NO-GO: stage front past crush density within minutes of waiting, 14 ambulances needed, not 6."

**2. Live, T+0 (1 min).** Live tab → Reset → **Venue**. Three reports in Tanglish, Tamil and English understood. Hospitals, units on the map.

**3. T+1 — the warning (1.5 min).** +1 min. Zone B CRITICAL, forecast > 5. Cards: Stop entry, Open Gate 4.
Click **🔮 Preview** on *Open Gate 4*: "Approve → no crush. Reject → crush." **Do not approve.** "Let's see what happens when nobody acts."

**4. T+7 — Silent Alarm (30 s).** Play. Orange banner: 3 independent reports in 3 minutes. "Itaewon had 11 calls. Each was handled alone."

**5. T+10 — the shock (2 min).** Guest 3 hours late, power cut, stampede. Pause. Walk through: Plan Diff, Why, Fragility, hospital
panel (nearest-only overloads KMCH, our plan doesn't), coverage gaps. Approve **Open Gate 4** → log shows re-routes, ETAs drop.

**6. T+13 — stall (30 s).** "Nobody reported it. The system noticed ambulance A2 stopped moving, re-assigned its patients and sent police."

**7. Run 2 (1 min).** Reset → +1 → approve Stop entry + Open Gate 4 → Play to T+12. Green **CRUSH AVERTED**. Chart: live line stays
below 5, twin line crosses it. "Same crowd, same heat, same power cut. One decision, ten minutes earlier."

**8. After-action + marshal (30 s).** After-action tab: live vs twin, decision latency. Show the marshal page on a phone.

**Judge's turn:** "Type any emergency, any language." Try `Zone D-la oru aal mayakkam`, `குழந்தை காணவில்லை zone A`, `fire near gate 3`,
`someone collapsed` (no location → it asks instead of guessing).

---

## 4. Pitch (2 minutes)
> In 2025, more than 120 people died in stampedes in India. At Karur, here in Tamil Nadu, 41 died — nine of them children.
> It was not a surprise. Three times the planned crowd, seven hours of waiting in the heat, a power cut. At Itaewon in Seoul,
> eleven people called for help hours before the crush. At the Kumbh, AI cameras sent alerts — but police rushing to one spot
> left another uncovered. The signals were there. What was missing was a system that adds them up, decides, and acts in time.
>
> NERISAL ZERO is that system. Six agents run the control room: they forecast crowd pressure ten minutes ahead, turn scattered
> calls into one alarm, keep an ambulance corridor open, notice a stuck ambulance nobody reported, and spread patients so no
> hospital drowns. Every risky decision waits for a human — and before they click, they can see both futures.
>
> The allocation is mathematics, not an AI guess, so every decision is repeatable and explained. And it starts before the event:
> police can stress-test a permit against the crowd that will really come.
>
> Same crowd, same heat, same power cut. The only difference is a decision made ten minutes earlier.

---

## 5. Judge Q&A
- **Where does density come from in reality?** CCTV head-counts, gate counters, anonymised mobile-network density. Simulated in the demo, as the problem statement allows.
- **Why not let the LLM decide?** Life-critical allocation must be repeatable and auditable → optimisation. The LLM only reads language, with a rule fallback.
- **How is the preview computed?** The engine clones the full state and runs the next 10 minutes twice, approve and reject, with the same scripted events.
- **What if a call has no location?** It is assumed in the most dangerous zone, marked low-confidence, and a human is asked to confirm.
- **What stops the plan from flip-flopping?** A switching penalty; diverting a unit already responding needs human approval.
- **What is Fragility?** We simulate the next likely shock (another crush in the riskiest zone; the busiest ambulance failing) and measure how much need would go unmet.
- **Scale?** Only `scenario.py` changes. The same code serves temples, stadiums, stations, the Kumbh.
- **Whose fault was Karur?** "We don't assign blame. We fix the system failures every stampede inquiry points to."

## 6. Honest limits
All data is synthetic; hospital capacities are not real. The crowd model is a zone-flow model, not physics. Density thresholds
and the permit model's assumptions are editable planning values, not official standards.

## 7. Rules check
The hackathon says work must be created during the hackathon window. Ask the organisers whether starter code is allowed.
If not, use this as a reference and rebuild with `docs/BUILD_PROMPTS.md` during the 24 hours.
