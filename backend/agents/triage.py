"""
Incident Triage Agent (Incident Assessment)
Turns messy reports (Tamil, English, Hindi, Tanglish) into structured incidents with
type, location, casualties, severity, confidence and resource needs, and merges
duplicate reports of the same event.

If ANTHROPIC_API_KEY is set, a Claude model does the extraction (forced JSON).
Otherwise (or on any error) a rule-based multilingual parser is used, so the demo
never depends on the network.
"""
import re
from typing import Literal, Optional

from pydantic import BaseModel

from . import llm

TYPES = {
    "crush": {"title": "Crowd crush", "rate": 5.0, "sev": 5,
              "kw": ["stampede", "crush", "trampl", "people falling", "fell", "நெரிசல்", "கீழே விழு", "மிதி", "bhagdad", "भगदड़", "nerisal"]},
    "accident": {"title": "Road accident", "rate": 3.0, "sev": 4,
                 "kw": ["accident", "collision", "crash", "hit by", "விபத்து", "vibathu", "durghatna", "दुर्घटना"]},
    "cardiac": {"title": "Cardiac / not breathing", "rate": 5.0, "sev": 5,
                "kw": ["not breathing", "no pulse", "cardiac", "heart attack", "மூச்சு இல்லை", "மாரடைப்பு", "saans nahi"]},
    "faint": {"title": "Fainting / heat exhaustion", "rate": 1.2, "sev": 2,
              "kw": ["faint", "collapsed", "unconscious", "heat", "dizzy", "மயக்க", "mayakkam", "mayakam", "behosh", "बेहोश", "veyil", "வெயில்"]},
    "missing_child": {"title": "Missing child", "rate": 1.5, "sev": 3,
                      "kw": ["missing", "lost child", "child lost", "காணவில்லை", "kaanom", "kanavillai", "bachcha kho", "गुम"]},
    "pressure": {"title": "Dangerous crowd pressure", "rate": 2.5, "sev": 3,
                 "kw": ["pushing", "crowded", "squeez", "too many people", "தள்ளு", "கூட்டம்", "dhakka", "धक्का"]},
    "fire": {"title": "Fire", "rate": 4.0, "sev": 5, "kw": ["fire", "smoke", "தீ", "aag", "आग"]},
    "unit_blocked": {"title": "Responder blocked by crowd", "rate": 2.2, "sev": 3, "kw": []},
}
PRIORITY = ["crush", "cardiac", "fire", "accident", "missing_child", "faint", "pressure"]

NEEDS = {
    "crush": {"als": 2, "bls": 2, "police": 2, "medic": 1, "first_aid": 2},
    "cardiac": {"als": 1, "cpr": 1},
    "fire": {"police": 1, "bls": 1},
    "accident": {"als": 1, "police": 1},
    "faint": {"first_aid": 1, "water": 1},
    "missing_child": {"police": 1},
    "pressure": {"police": 1},
    "unit_blocked": {"police": 1},
}

LOCATIONS = [
    (r"\bzone\s*-?\s*a\b|மண்டலம்\s*a\b|a\s*பகுதி|zone a-la|gate\s*1\b", "A"),
    (r"\bzone\s*-?\s*b\b|மண்டலம்\s*b\b|b\s*பகுதி|stage", "B"),
    (r"\bzone\s*-?\s*c\b|மண்டலம்\s*c\b|c\s*பகுதி|gate\s*2\b|gate\s*4\b", "C"),
    (r"\bzone\s*-?\s*d\b|மண்டலம்\s*d\b|d\s*பகுதி|gate\s*3\b", "D"),
    (r"hope college|avinashi", "J_HOPE"),
]


class Casualties(BaseModel):
    red: int
    yellow: int
    green: int


class TriageOut(BaseModel):
    """Schema Claude must fill. 'unit_blocked' is sensor-only, so it is not offered."""
    type: Literal["crush", "accident", "cardiac", "faint", "missing_child", "pressure", "fire"]
    location: Optional[Literal["A", "B", "C", "D", "J_HOPE"]]
    severity: int
    confidence: float
    casualties: Casualties
    summary: str


class IncidentTriageAgent:
    name = "Incident Triage Agent"

    def __init__(self):
        self.use_llm = llm.enabled()

    # ------------------------------------------------------------------
    def parse(self, text):
        err = None
        if self.use_llm:
            for attempt in range(2):  # retry once, but not after a timeout (the network is down; go to rules)
                try:
                    out = self._parse_llm(text)
                    out["parser"] = "llm"
                    return out
                except Exception as e:  # never let the model break the control room
                    err = f"{type(e).__name__}: {e}"[:160]
                    print(f"LLM parse attempt {attempt + 1} failed: {err}")
                    if "Timeout" in type(e).__name__:
                        break
        out = self._parse_rules(text)
        out["parser"] = "rules"
        if err:
            out["llm_error"] = err
        return out

    def _parse_rules(self, text):
        t = text.lower()
        found = [k for k in PRIORITY if any(w in t for w in TYPES[k]["kw"])]
        itype = found[0] if found else "pressure"
        conf = 0.75 if found else 0.35
        loc = None
        for pat, z in LOCATIONS:
            if re.search(pat, t):
                loc = z
                break
        if loc is None:
            conf -= 0.25
        nums = [int(n) for n in re.findall(r"\b(\d{1,3})\b", t)]
        injured = max([n for n in nums if n < 200], default=0)
        if itype == "missing_child":
            injured = 0
        sev = TYPES[itype]["sev"]
        if any(w in t for w in ["not breathing", "unconscious", "blood", "ரத்தம்", "மூச்சு"]):
            sev = min(5, sev + 1)
        red = yellow = green = 0
        if itype == "crush":
            injured = injured or 8
            red = max(1, round(injured * 0.33))
            yellow = max(0, round(injured * 0.5))
            green = max(0, injured - red - yellow)
        elif itype == "accident":
            injured = injured or 1
            red = 1 if sev >= 4 else 0
            yellow = max(0, injured - red)
        elif itype == "faint":
            injured = injured or 1
            green = injured
        return {"type": itype, "location": loc, "severity": sev, "confidence": round(max(0.2, conf), 2),
                "casualties": {"red": red, "yellow": yellow, "green": green}, "summary": text[:140]}

    def _parse_llm(self, text):
        prompt = (
            "You are the triage agent in an emergency control room for a crowded rally in Coimbatore. "
            "Reports may be in Tamil, English, Hindi or mixed (Tanglish). Extract ONE incident. "
            "Zones: A north near Gate 1, B stage front, C east near Gates 2/4, D south-west near Gate 3; "
            "J_HOPE is the Hope College junction on Avinashi Road. Use location null if the report does not say "
            "where - never guess. severity 1-5; confidence 0-1, lower when location or facts are unclear; "
            "casualties is a START triage estimate (red/yellow/green counts); summary is short English.\n\nReport: " + text
        )
        msg = llm.client().messages.parse(model=llm.MODEL, max_tokens=2000, output_config={"effort": "low"},
                                          messages=[{"role": "user", "content": prompt}], output_format=TriageOut)
        if msg.stop_reason != "end_turn" or msg.parsed_output is None:
            raise ValueError(f"no usable output (stop_reason={msg.stop_reason})")
        d = msg.parsed_output.model_dump()
        # The schema fixes the shape; these keep the numbers sane.
        d["severity"] = min(5, max(1, d["severity"]))
        d["confidence"] = round(min(1.0, max(0.0, d["confidence"])), 2)
        d["casualties"] = {k: max(0, min(500, v)) for k, v in d["casualties"].items()}
        return d

    # ------------------------------------------------------------------
    def ingest(self, st, text, log, propose):
        p = self.parse(text)
        itype, loc = p["type"], p["location"]
        # Duplicate merge: same type + same location, open, within 10 minutes
        for inc in st["incidents"].values():
            same_type = inc["type"] == itype or (inc["type"] == "pressure" and itype == "crush")
            if inc["status"] == "open" and same_type and inc["location"] == loc and st["minute"] - inc["created"] <= 10:
                if itype == "crush" and inc["type"] == "pressure":
                    self._upgrade(inc, p)
                    inc["crush_at"] = st["minute"]
                    log(self.name, f"Report upgrades {inc['id']} from crowd pressure to CROWD CRUSH (severity 5). "
                                   f"Casualties est. red {inc['casualties']['red']}, yellow {inc['casualties']['yellow']}.")
                    return inc
                inc["reports"] += 1
                inc["confidence"] = round(min(0.97, inc["confidence"] + 0.12), 2)
                inc["severity"] = max(inc["severity"], p["severity"])
                for k in ("red", "yellow", "green"):
                    inc["casualties"][k] = max(inc["casualties"][k], p["casualties"].get(k, 0))
                inc["texts"].append(text)
                inc.setdefault("report_minutes", [inc["created"]]).append(st["minute"])
                log(self.name, f"Merged duplicate report into {inc['id']} ({inc['title']}), now {inc['reports']} reports, "
                               f"confidence {inc['confidence']}.")
                self._silent_alarm(st, inc, log, propose)
                return inc

        iid = f"I{len(st['incidents']) + 1}"
        needs = dict(NEEDS[itype])
        if itype == "faint" and p["severity"] >= 3:
            needs["bls"] = 1
        inc = {
            "id": iid, "type": itype, "title": TYPES[itype]["title"], "location": loc,
            "severity": p["severity"], "confidence": p["confidence"], "casualties": p["casualties"],
            "needs": needs, "reports": 1, "texts": [text], "created": st["minute"], "status": "open",
            "parser": p["parser"], "summary": p.get("summary", text[:140]), "served_since": None,
        }
        st["incidents"][iid] = inc
        where = loc or "UNKNOWN location"
        log(self.name, f"New incident {iid}: {inc['title']} at {where}, severity {inc['severity']}/5, "
                       f"confidence {inc['confidence']} (parser: {p['parser']}"
                       + (f", Claude failed: {p['llm_error']}" if p.get("llm_error") else "") + ").")
        if loc is None or inc["confidence"] < 0.5:
            inc["location"] = loc or "B"  # cautious default: the densest zone
            propose(f"confirm_{iid}", f"Confirm details of {iid} ({inc['title']})",
                    f"The report is unclear ('{text[:80]}'). Treated cautiously as Zone {inc['location']} for now. "
                    "Ask the nearest marshal to confirm location and casualties.",
                    {"kind": "confirm", "incident": iid}, risk="info")
        return inc

    def _silent_alarm(self, st, inc, log, propose):
        """Itaewon lesson: 11 calls warned of crushing ~4 hours before; each was handled alone.
        Several independent reports of crowding from one zone in a short window = pattern alarm."""
        if inc["type"] != "pressure" or inc.get("silent_alarm"):
            return
        recent = [m for m in inc.get("report_minutes", []) if st["minute"] - m <= 15]
        if len(recent) >= 3:
            inc["silent_alarm"] = True
            inc["severity"] = max(inc["severity"], 4)
            inc["needs"]["police"] = max(inc["needs"].get("police", 1), 2)
            inc["needs"]["medic"] = 1
            span = st["minute"] - min(recent)
            log(self.name, f"SILENT ALARM: {len(recent)} separate reports of dangerous crowding in Zone {inc['location']} "
                           f"within {span} min. Individually minor, together a crush precursor. Escalated to severity 4.")
            propose(f"silent_{inc['id']}", f"SILENT ALARM – Zone {inc['location']}: {len(recent)} crowding reports in {span} min",
                    "Pattern, not a single call: several people independently say they cannot move. At Itaewon (Seoul, 2022) "
                    "11 such calls came in the ~4 hours before the crush and were handled one by one. Recommend: stop entry, "
                    "open relief exits, move police to the zone edge to meter flow.",
                    {"kind": "gate", "gate": "G1", "open": False}, risk="high")

    def _upgrade(self, inc, p):
        inc.update(type="crush", title=TYPES["crush"]["title"], severity=5, needs=dict(NEEDS["crush"]))
        inc["casualties"] = p["casualties"]
        inc["confidence"] = max(inc["confidence"], p["confidence"])
        inc["reports"] += 1
        inc["texts"].append(p["summary"])
