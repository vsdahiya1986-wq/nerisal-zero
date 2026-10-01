"""
Crowd Pressure Agent
Turns zone head-counts into density (people per m2), forecasts density 10 minutes ahead
from the recent trend plus aggravating factors (heat, delay, power loss), and proposes
crowd-control actions and calm multilingual announcements.

Thresholds follow widely used crowd-safety guidance: above ~4 people/m2 a crowd starts
to lose free movement; around 5+/m2 in a pushing crowd, crush risk becomes serious.
"""

SAFE, WATCH, DANGER, CRITICAL = 3.5, 4.5, 5.0, 5.5


def risk_level(d):
    if d >= CRITICAL:
        return "critical"
    if d >= DANGER:
        return "danger"
    if d >= WATCH:
        return "watch"
    if d >= SAFE:
        return "elevated"
    return "normal"


RISK_ORDER = ["normal", "elevated", "watch", "danger", "critical"]

ANNOUNCE = {
    "ta": "அன்பார்ந்த நண்பர்களே, தயவுசெய்து அமைதியாக இருங்கள். {zone_ta} பகுதியில் உள்ளவர்கள் மெதுவாக {gate} வழியாக வெளியே செல்லவும். ஓட வேண்டாம், தள்ள வேண்டாம். குடிநீர் {gate} அருகில் கிடைக்கும்.",
    "en": "Dear friends, please stay calm. People in {zone_en} please move slowly towards {gate}. Do not run, do not push. Drinking water is available near {gate}.",
    "hi": "कृपया शांत रहें। {zone_en} के लोग धीरे-धीरे {gate} की ओर जाएँ। दौड़ें नहीं, धक्का न दें। पानी {gate} के पास उपलब्ध है।",
}


class CrowdPressureAgent:
    name = "Crowd Pressure Agent"

    def run(self, st, log, propose):
        v = st["venue"]
        aggravation = 0.0
        factors = []
        if v["heat_c"] >= 35:
            aggravation += 0.2
            factors.append(f"heat {v['heat_c']}°C")
        if not v["power"]:
            aggravation += 0.6
            factors.append("power failure")
        if v["vip_delay_min"] >= 60 and not v["event_halted"]:
            aggravation += 0.3
            factors.append(f"guest delayed {v['vip_delay_min']} min")

        worst = None
        for zid, z in st["zones"].items():
            d = z["count"] / z["area"]
            hist = z.setdefault("history", [])
            if z.get("hist_minute") != st["minute"]:
                hist.append(round(d, 3))
                z["hist_minute"] = st["minute"]
            else:
                hist[-1] = round(d, 3)
            del hist[:-15]
            past = hist[-6] if len(hist) >= 6 else hist[0]
            slope = (d - past) / max(1, min(5, len(hist) - 1))
            fc = max(0.0, d + slope * 10 + (aggravation if d > 3 else aggravation * 0.3))
            prev_level = z.get("risk", "normal")
            z.update(density=round(d, 2), forecast=round(fc, 2), trend=round(slope, 3))
            level = risk_level(max(d, fc))
            z["risk"] = level
            z["confidence"] = round(0.9 if len(hist) >= 5 else 0.6, 2)
            if worst is None or fc > st["zones"][worst]["forecast"]:
                worst = zid
            if RISK_ORDER.index(level) > RISK_ORDER.index(prev_level) and level in ("watch", "danger", "critical"):
                log(self.name, f"{z['name']}: now {d:.1f} p/m², forecast {fc:.1f} p/m² in 10 min "
                               f"({level.upper()}){'; aggravated by ' + ', '.join(factors) if factors else ''}.")
                self._announce(st, zid, log)

        st["crowd_factors"] = factors
        st["riskiest_zone"] = worst
        self._propose_actions(st, propose, log)

    # ------------------------------------------------------------------
    def _exit_gate_for(self, st, zid):
        if zid in ("B", "C") and st["gates"]["G4"]["open"]:
            return "Gate 4"
        return "Gate 3"

    MAKE_WAY = {
        "ta": "மருத்துவக் குழு வருகிறது. மேடை அருகில் உள்ளவர்கள் இடமும் வலமும் நகர்ந்து வழி விடுங்கள். ஓட வேண்டாம்.",
        "en": "Medical team coming through. People near the stage, please step left and right and make a path. Do not run.",
        "hi": "मेडिकल टीम आ रही है। कृपया बाएँ-दाएँ हटकर रास्ता दें। दौड़ें नहीं।",
    }

    def make_way(self, st, zid, gate, iid, log):
        """Casualty extraction started: ask the crowd to open a path (once per incident; caller guards)."""
        a = {"id": f"AN{len(st['announcements']) + 1}", "minute": st["minute"], "zone": zid, "gate": gate,
             "kind": "make_way", "incident": iid, **self.MAKE_WAY}
        st["announcements"].insert(0, a)
        log(self.name, f"Drafted 'Make way' announcement for Zone {zid}: medical team carrying casualties of {iid} to {gate}.")

    def _announce(self, st, zid, log):
        gate = self._exit_gate_for(st, zid)
        z_en = f"Zone {zid}"
        z_ta = f"மண்டலம் {zid}"
        a = {
            "id": f"AN{len(st['announcements']) + 1}",
            "minute": st["minute"], "zone": zid, "gate": gate,
            "ta": ANNOUNCE["ta"].format(zone_ta=z_ta, gate=gate),
            "en": ANNOUNCE["en"].format(zone_en=z_en, gate=gate),
            "hi": ANNOUNCE["hi"].format(zone_en=z_en, gate=gate),
        }
        st["announcements"].insert(0, a)
        log(self.name, f"Drafted calm announcement for Zone {zid} (Tamil / English / Hindi), directing people to {gate}.")

    def _propose_actions(self, st, propose, log):
        zones, gates, v = st["zones"], st["gates"], st["venue"]
        hot = [z for z in zones.values() if RISK_ORDER.index(z["risk"]) >= RISK_ORDER.index("watch")]
        if not hot:
            return
        if gates["G1"]["open"] and not v["event_halted"]:
            propose("stop_entry_G1", "Stop entry at Gate 1",
                    f"Zone B is forecast at {zones['B']['forecast']} p/m². Gate 1 is still admitting ~300 people/min. "
                    "Stopping entry keeps the crowd from growing while exits clear.",
                    {"kind": "gate", "gate": "G1", "open": False}, risk="medium")
        danger = [z for z in zones.values() if RISK_ORDER.index(z["risk"]) >= RISK_ORDER.index("danger")]
        if danger and not gates["G4"]["open"]:
            propose("open_G4", "Open Gate 4 and clear an ambulance corridor",
                    "Opens the emergency exit for Zones B and C (~400 people/min out) and gives ambulances a clear lane "
                    "to the stage front. Needs police at Gate 4 so the outside road is not flooded.",
                    {"kind": "open_corridor"}, risk="high")
        if danger and v["vip_delay_min"] >= 60 and not v["event_halted"]:
            propose("halt_event", "Ask organisers to halt the event and disperse in phases",
                    f"The main guest is {v['vip_delay_min']} min late and {len(danger)} zone(s) are in danger. "
                    "Waiting will only increase the crowd. Phased dispersal: Zone D via Gate 3 first, then C via Gate 4.",
                    {"kind": "halt_event"}, risk="high")
