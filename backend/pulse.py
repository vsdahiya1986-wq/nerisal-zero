"""
Citizen Pulse: every attendee's phone becomes a sensor.
Itaewon (2022): the warnings came from the crowd itself, and each call was handled alone. Here each tap is
aggregated per zone, and a pattern of "can't move" taps becomes one crowding report for the Triage Agent
(where it merges with other reports and can trigger the Silent Alarm).
"""
import random

KINDS = {
    "ok": ("நான் நலம்", "I'm OK"),
    "cant_move": ("நகர முடியவில்லை", "Can't move – too crowded"),
    "medical": ("மருத்துவ உதவி", "Someone needs medical help"),
    "lost_child": ("குழந்தை காணவில்லை", "Lost child"),
}
WINDOW_MIN = 5      # dashboard summary window (simulated minutes)
TRIGGER_MIN = 3     # "can't move" pattern window
TRIGGER_TAPS = 5    # ... either 5+ taps
TRIGGER_SHARE = 0.3  # ... or 30 %+ of taps (with at least 3 taps)
MAX_TAPS = 5000


def _taps(st):
    return st.setdefault("pulse_taps", [])


def summary(st):
    m = st["minute"]
    out = {}
    for zid in st["zones"]:
        c = {k: 0 for k in KINDS}
        for t in _taps(st):
            if t["zone"] == zid and m - t["minute"] < WINDOW_MIN:
                c[t["kind"]] += 1
        total = sum(c.values())
        out[zid] = dict(c, total=total, index=round(c["cant_move"] / total, 2) if total else 0.0)
    return out


def guidance(engine, zid):
    """Calm instruction for one zone, right now, from the current state (Tamil + English)."""
    st = engine.st
    z, b = st["zones"][zid], st["zones"]["B"]
    gate = engine.crowd._exit_gate_for(st, zid)
    gate_ta = gate.replace("Gate", "வாயில்")
    if z["risk"] in ("danger", "critical"):
        en = f"Zone {zid} is very crowded. Walk slowly towards {gate}. Do not run or push; help children and elderly people."
        ta = (f"மண்டலம் {zid} மிகவும் நெரிசலாக உள்ளது. மெதுவாக {gate_ta} நோக்கி நடக்கவும். ஓட வேண்டாம், தள்ள வேண்டாம்; "
              "குழந்தைகளுக்கும் முதியவர்களுக்கும் உதவுங்கள்.")
    elif z["risk"] == "watch":
        en = f"It is getting crowded here. Stay where you are, keep some space around you, and be ready to move to {gate} if asked."
        ta = (f"இங்கு கூட்டம் அதிகரிக்கிறது. இருக்கும் இடத்திலேயே இருங்கள், சுற்றி இடம் விடுங்கள். "
              f"அறிவிப்பு வந்தால் {gate_ta} நோக்கி செல்லத் தயாராக இருங்கள்.")
    else:
        en = "Your area is calm. Stay aware and follow the instructions of safety staff."
        ta = "உங்கள் பகுதி அமைதியாக உள்ளது. கவனமாக இருங்கள், பாதுகாப்பு பணியாளர்களின் அறிவுறுத்தல்களைப் பின்பற்றுங்கள்."
    if zid != "B" and b["risk"] in ("danger", "critical"):
        en += " Do not go towards the stage (Zone B) – it is dangerously crowded."
        ta += " மேடை முன் பகுதிக்கு (மண்டலம் B) செல்ல வேண்டாம் – அங்கு ஆபத்தான நெரிசல் உள்ளது."
    return {"zone": zid, "risk": z["risk"], "gate": gate, "ta": ta, "en": en, "minute": st["minute"]}


ACK = {
    "ok": ("நன்றி. பாதுகாப்பாக இருங்கள்.", "Thank you. Stay safe."),
    "cant_move": ("தெரிவிக்கப்பட்டது. அமைதியாக இருங்கள்.", "Reported. Stay calm."),
    "medical": ("உதவி கோரப்பட்டுள்ளது. பாதுகாப்பாக இருந்தால் அந்த நபருடன் இருங்கள்; அருகிலுள்ள பணியாளரிடம் கை அசைத்து தெரிவியுங்கள்.",
                "Help has been requested. Stay with the person if it is safe; wave to the nearest staff member."),
    "lost_child": ("தெரிவிக்கப்பட்டது. இருக்கும் இடத்திலேயே இருங்கள்; அருகிலுள்ள பணியாளர் அல்லது காவல் உதவி மையத்திற்கு செல்லுங்கள்.",
                   "Reported. Stay where you are, or go to the nearest staff member or police help desk."),
}


def tap(engine, zid, kind, device):
    """Record one tap and feed the agents. Caller validates zid/kind and rate-limits the device."""
    st = engine.st
    taps = _taps(st)
    taps.append({"zone": zid, "kind": kind, "minute": st["minute"], "device": device[:64]})
    del taps[:-MAX_TAPS]
    fed = None
    if kind == "cant_move":
        m = st["minute"]
        recent = [t for t in taps if t["zone"] == zid and m - t["minute"] < TRIGGER_MIN]
        cant = sum(t["kind"] == "cant_move" for t in recent)
        last = st.setdefault("pulse_reported", {}).get(zid)
        if (cant >= TRIGGER_TAPS or (len(recent) >= 3 and cant / len(recent) >= TRIGGER_SHARE)) and \
                (last is None or m - last >= TRIGGER_MIN):
            st["pulse_reported"][zid] = m
            fed = engine.citizen_report(f"Citizen Pulse: {cant} attendees in Zone {zid} report they cannot move, too crowded")
    elif kind == "medical":
        fed = engine.citizen_report(f"Citizen Pulse: an attendee reports someone collapsed and needs medical help in Zone {zid}",
                                    confirm=True)
    elif kind == "lost_child":
        fed = engine.citizen_report(f"Citizen Pulse: an attendee reports a lost child in Zone {zid}")
    g = guidance(engine, zid)
    g["ack_ta"], g["ack_en"] = ACK[kind]
    g["fed_incident"] = fed["id"] if fed else None
    return g


def simulate(engine, n=60):
    """Plausible taps from n attendees (for online judges), weighted by each zone's crowd and density."""
    st = engine.st
    rng = random.Random(st["minute"] * 7919 + len(_taps(st)))
    zones = list(st["zones"])
    weights = [st["zones"][z]["count"] for z in zones]
    base = len(_taps(st))
    for k in range(n):
        zid = rng.choices(zones, weights)[0]
        d = st["zones"][zid]["density"]
        p_cant = min(0.85, max(0.05, (d - 3.0) / 3.0))
        r = rng.random()
        kind = "cant_move" if r < p_cant else "medical" if r < p_cant + 0.04 else "lost_child" if r < p_cant + 0.05 else "ok"
        tap(engine, zid, kind, f"sim-{base + k}")
    return summary(st)
