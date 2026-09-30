# Out-of-the-box brainstorm — what makes NERISAL ZERO different

Most Domain 4 teams will build: incidents → priority queue → nearest ambulance → map. That is a dispatcher.
We built around three research findings about why crowd disasters actually happen.

## The three research findings the whole design stands on

| Finding | Evidence | What we built |
|---|---|---|
| **Warnings exist, but arrive one at a time and nobody adds them up** | Itaewon, Seoul 2022: 11 emergency calls from the alley from 6:34 pm, about 3 h 40 min before the crush; police were dispatched only 4 times (NPR). | **Silent Alarm** – 3+ independent crowding reports from one zone in 15 min become one pattern alarm, even if each call sounds minor. |
| **Detection is not the gap; response capacity is** | Maha Kumbh 2025: 2,760 AI cameras sent "timely alerts on crowd surge", but "there were not enough policemen on the ground"; when officers rushed to one spot, "another stampede was sparked on the other side" (Context/Thomson Reuters). | **Coverage gaps + Fragility Score** – the system tracks which zones are left with no free police / first aid and stress-tests every plan against the *next* shock, recommending reserves or mutual aid. |
| **The failure starts at permission, not at the stampede** | Karur 2025: ~27–30k people at a venue expected for ~10k, ~7-hour delay, heat, power cut; ambulances could not get through; after it the Madras High Court ordered Tamil Nadu to frame an SOP for rallies. Ambulance drivers cited a norm of 4–5 ambulances per 10,000 people. | **Permit Stress-Test** – police test the organiser's plan against 1×, 2×, 2.7× turnout and a long delay *before* granting permission, and get concrete conditions. |

Crowd science: G. Keith Still's work shows moving crowds reach critical density around 2–4 people/m², after which flow
collapses; standing crowds pushing forward above ~5/m² are the classic crush condition. Our thresholds (watch 4.5, danger 5)
are for a standing rally crowd and are editable.

## The eight features, ranked by judge impact

1. **Decision Preview (🔮)** – before approving, the commander sees the next 10 minutes simulated both ways
   (crush yes/no, peak density, unmet needs, patients at hospital). Human-in-the-loop that is *informed*, not a rubber stamp.
2. **No-action twin** – the same scenario runs in parallel with nobody acting. The chart shows both futures
   diverging. After-action report: "live: no crush · twin: crush at T+10".
3. **Silent Alarm** (Itaewon lesson).
4. **Stall detection** (Karur lesson) – an ambulance whose GPS stops moving for 2 minutes while responding is detected
   *without anyone reporting it*, marked unavailable, its patients re-assigned and police sent to free it.
5. **Coverage gaps + Fragility** (Kumbh lesson).
6. **Hospital Surge** – our plan vs "everyone to the nearest hospital", side by side.
7. **Permit Stress-Test** – prevention before the event.
8. **Marshal phone view** – the last mile: big Tamil instructions per zone for people on the ground, with a speak button.

Also: multilingual triage (Tamil, Tanglish, Hindi, English), duplicate merging, "no location → ask, don't guess",
Tamil/English/Hindi announcements, plan diff with reasons, after-action report with **decision latency**
(how long each alert waited for a human – accountability without blaming individuals).

## Ideas we considered and parked (say this if judges ask "what next")
- Real CCTV crowd counting (e.g. density-map CNNs) feeding the Crowd Pressure Agent.
- Anonymised mobile-network density (the approach Seoul moved towards after Itaewon).
- Voice call intake with speech-to-text in Tamil.
- Traffic-signal pre-emption for the ambulance corridor.
- Wearable/beacon counts at gates; turnstile integration with automatic stop-entry at 90% capacity.
- Learning time-criticality weights from real outcome data.

## Sources
- NPR, "Desperate calls for help came hours before the Seoul crowd surge turned deadly" (2 Nov 2022).
- Context (Thomson Reuters Foundation), "Did AI fail to prevent fatal stampede at India's Kumbh festival?"
- The Federal, "Over 120 deaths in 2025, why stampedes remain a recurring tragedy"; Karur ambulance drivers' accounts.
- Gulf News, report on the Karur rally stampede: delay, blackout, heat (facts on crowd size, delay, power cut).
- The Federal / Tribune / Deccan Herald: Madras High Court orders SOP for political rallies after Karur (Oct 2025).
- G. Keith Still, gkstill.com – moving crowd density and flow.
- Telangana AI-powered Dial 112 (Aug 2026): per-call AI; processing time 190 → 133 s.
