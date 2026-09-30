# Judge Q&A — 25 hard questions, honest answers

Every answer matches what the code does today. Numbers come from running the code (Evidence Lab: `docs/evidence.json`).
If you do not know, say so — "that is on our what-next list" beats a guess.

## Does it work?

**1. Does it only work in your one scripted demo?**
No. The Evidence Lab runs 200 randomised rallies (starting crowd ±20 %, entry rates ±30 %, guest delay 60–240 min, power cut at
T+8–13 or none, heat 32–40 °C), the same seeds for every policy. Acting on NERISAL's first warnings kept Zone B out of crush
conditions in 73 % of runs vs 0 % with no action. It is a simulation of our own model, not real-world validation — we say that on the tab.

**2. Why only 73 %?**
51 of the 200 runs start *already* at crush density (Zone B above 5 p/m² at T+0), before any warning can exist. Of the other 149
runs, 98 % stayed safe with advice. We kept those runs in the headline rather than hide them.

**3. What does "late action" show?**
Approving the same actions only after crush conditions start still ends in crush conditions in 100 % of runs, but the median peak
drops from 8.45 to 5.19 p/m². Timing is the whole game: the same decisions, ten minutes earlier.

**4. How do you define a crush?**
One physical rule for every policy: Zone B at or above 5 people/m² for 2 or more consecutive minutes. In the variants, the
"stampede" report only arrives if that physical condition is met.

**5. Where does the crowd density come from in reality?**
CCTV head counts, gate counters and anonymised mobile-network density, plus Citizen Pulse taps from attendees. In the demo it is simulated.

## The AI

**6. Is this "AI" or just rules?**
Six agents with deterministic maths: a density forecast, a Hungarian-algorithm assignment that minimises expected harm, a road
graph, a hospital distribution, a fragility stress-test. Claude is used only for language: reading messy multilingual reports and
explaining a plan change in English and Tamil.

**7. Why not let the LLM decide who gets the ambulance?**
Life-critical allocation must be repeatable and auditable. The same inputs always give the same plan, with written reasons. The LLM
never changes the plan, and every LLM call has an 8-second timeout and a rule-based fallback.

**8. What if the model is wrong?**
Three guards. A human approves every risky action. Decision Preview shows both futures before the click. Low-confidence reports
(no location, or from a phone tap) raise a "Confirm details" card instead of being trusted.

**9. What if a report has no location?**
It is treated cautiously as the densest zone, marked low-confidence, and a marshal is asked to confirm. It never guesses silently.

**10. How is the Decision Preview computed?**
The engine clones the whole state and runs the next 10 minutes twice, approve and reject, with the same scripted events.

**11. What stops the plan from flip-flopping?**
A switching penalty in the optimiser. Diverting a unit already on its way needs a human, and we only raise that card when the
gain is at least 1.5× the loss — never to pull help away from a crowd crush.

## Why not just…

**12. Why not just use CCTV AI?**
Detection was not the gap at the Kumbh: 2,760 AI cameras sent alerts. The gap was response capacity — police rushing to one spot
left another uncovered. We track coverage gaps and stress-test the plan against the next shock. CCTV would be one more input to
our Crowd Pressure Agent.

**13. Why not a simple dispatcher that sends the nearest ambulance?**
"Nearest" fails in a crush. In our no-action run, ambulance A1 is parked at Gate 4, a few hundred metres from the crush, and is
still stuck behind the closed corridor at T+30. Only 1 of 5 red patients reaches hospital by then. Opening Gate 4 at T+10 gets the
first crush patient to hospital by T+20. And "everyone to the nearest hospital" overloads KMCH; our plan does not.

**14. What is new compared with existing control rooms?**
Adding up weak signals (Silent Alarm, Citizen Pulse), testing a decision before taking it (Preview), proving its value (the
no-action twin and Impact card), and noticing what nobody reports (a stalled ambulance).

## People, privacy, accountability

**15. Who is accountable?**
The human who approves. The After-action report records every alert, who approved or rejected it and how long it waited
(decision latency). That is accountability without blaming a single person — it shows where the system was slow.

**16. What does Citizen Pulse collect? Privacy?**
Only the zone, the kind of tap and a random code stored on the phone (to stop repeated taps). No name, no phone number, no GPS.
Taps are kept in memory for the event only. One tap per phone per 20 seconds.

**17. Can someone flood Citizen Pulse with fake taps?**
The per-phone rate limit slows it down. A tap only creates a report after a *pattern* (5+ "can't move" taps, or 30 %+ of taps, in
3 minutes); medical taps start at low confidence with a Confirm card; and the commander still approves any action. A production
system would add per-network limits and cross-check with cameras.

**18. What about people without smartphones?**
Marshals get a Tamil phone page, the PA gets Tamil/English/Hindi announcements with a speak button, and the public alert has a
160-character SMS version.

**19. Isn't opening gates or halting an event dangerous?**
Yes — that is why the system never does it by itself. It proposes, previews both futures, and waits for a human.

## Feasibility

**20. How would police adopt this?**
Start before the event: the Permit Stress-Test runs on the organiser's declared numbers and gives concrete conditions (an entry
cap, total exit width, ambulances with a barricaded lane, stage-front pens with relief exits, a no-show dispersal rule). After Karur, the Madras High Court ordered an SOP for rallies; this is a tool for that SOP. On the day,
it runs on one laptop with no internet except map tiles.

**21. Does it follow any standard?**
The public alert is exported as CAP 1.2 (the OASIS Common Alerting Protocol) that public warning systems ingest, in Tamil and
English, always marked "Exercise" in the demo.

**22. What does it cost?**
The software is open-source Python on one laptop; no GPU. Claude is optional (only for language). Real costs would be integration:
camera counts, gate counters, radio/GPS feeds.

**23. How does it scale to the Kumbh or a stadium?**
Only `scenario.py` changes: zones, gates, roads, hospitals, units. The agents do not change. Today one re-plan of 18 units takes well under a millisecond, and a whole Evidence Lab
(600 simulated 30-minute events) runs in about 21 seconds on a laptop. We have not yet load-tested a Kumbh-sized fleet.

**24. What are the honest limits?**
All data is synthetic. The crowd model is a zone-flow model, not physics. Thresholds and permit assumptions are editable planning
values, not official standards. The Evidence Lab tests our model against itself.

**25. Whose fault was Karur?**
"We do not assign blame. We fix the system failures every stampede inquiry points to: warnings not added up, too few responders
in the right place, ambulances that could not get through, and a permit that did not plan for the real crowd."
