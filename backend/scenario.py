"""
Synthetic scenario: a political/public rally at a trade-fair ground on Avinashi Road, Coimbatore.
All numbers are synthetic and for demonstration only. Hospital capacities are NOT real data.
"""

# ---------------- Road graph (approximate coordinates, synthetic) ----------------
NODES = {
    # Venue (gates + stage centre)
    "VENUE":   (11.0353, 77.0410),
    "G1":      (11.0372, 77.0395),   # north entry gate
    "G2":      (11.0372, 77.0428),   # north-east entry gate
    "G3":      (11.0334, 77.0392),   # south exit gate
    "G4":      (11.0334, 77.0430),   # south-east emergency exit (closed at start)
    # Junctions
    "J_AIR":   (11.0392, 77.0432),   # Avinashi Rd near airport
    "J_HOPE":  (11.0290, 77.0180),   # Hope College junction
    "J_PSG":   (11.0250, 77.0040),   # Peelamedu / PSG
    "J_GANDHI": (11.0170, 76.9680),  # Gandhipuram side
    "S_EAST":  (11.0300, 77.0405),   # southern service road
    "S_MID":   (11.0150, 77.0150),
    "S_WEST":  (11.0080, 76.9800),
    # Hospitals
    "H_KMCH":  (11.0450, 77.0480),
    "H_PSG":   (11.0245, 77.0065),
    "H_CMCH":  (11.0165, 76.9705),
    "H_ROYAL": (11.0610, 77.0900),
    # 108 ambulance bases
    "B_PEEL":  (11.0270, 77.0080),
    "B_GANDHI": (11.0180, 76.9640),
    "B_NEEL":  (11.0590, 77.0850),
}

# (a, b, road_name, kind)  kind: 'road' or 'venue' (inside the crowd)
EDGES = [
    ("G1", "VENUE", "Venue lane north", "venue"),
    ("G2", "VENUE", "Venue lane north-east", "venue"),
    ("G3", "VENUE", "Venue lane south", "venue"),
    ("G4", "VENUE", "Emergency corridor (G4)", "corridor"),
    ("G1", "J_AIR", "Airport link", "road"),
    ("G2", "J_AIR", "Airport link east", "road"),
    ("J_AIR", "H_KMCH", "Avinashi Rd (east)", "road"),
    ("J_AIR", "J_HOPE", "Avinashi Rd (Airport-Hope College)", "road"),
    ("J_HOPE", "J_PSG", "Avinashi Rd (Hope-Peelamedu)", "road"),
    ("J_PSG", "H_PSG", "PSG Hospital road", "road"),
    ("J_PSG", "B_PEEL", "Peelamedu base road", "road"),
    ("J_PSG", "J_GANDHI", "Avinashi Rd (west)", "road"),
    ("J_GANDHI", "H_CMCH", "Trichy Rd link", "road"),
    ("J_GANDHI", "B_GANDHI", "Gandhipuram base road", "road"),
    ("H_KMCH", "B_NEEL", "Avinashi Rd (Neelambur)", "road"),
    ("B_NEEL", "H_ROYAL", "Neelambur link", "road"),
    ("G3", "S_EAST", "Service road south", "road"),
    ("G4", "S_EAST", "Service road south-east", "road"),
    ("G4", "J_AIR", "Airport service road (east)", "road"),
    ("S_EAST", "S_MID", "Kamarajar Rd (east)", "road"),
    ("S_MID", "S_WEST", "Kamarajar Rd (west)", "road"),
    ("S_WEST", "H_CMCH", "CMCH south link", "road"),
    ("S_MID", "H_PSG", "PSG south link", "road"),
]

# ---------------- Venue ----------------
VENUE = {
    "name": "Rally ground, Avinashi Road, Coimbatore (synthetic)",
    "planned_capacity": 10000,
    "heat_c": 36,
    "power": True,
    "vip_delay_min": 0,
    "event_halted": False,
}

# Zones: area in m2, count = people at minute 0
ZONES = {
    "A": {"name": "Zone A (north, near Gate 1)", "lat": 11.0366, "lng": 77.0398, "radius": 55, "area": 4000, "count": 8000},
    "B": {"name": "Zone B (stage front)",       "lat": 11.0354, "lng": 77.0412, "radius": 40, "area": 1800, "count": 8300},
    "C": {"name": "Zone C (east, near Gate 2/4)", "lat": 11.0352, "lng": 77.0428, "radius": 50, "area": 3000, "count": 5200},
    "D": {"name": "Zone D (south-west, near Gate 3)", "lat": 11.0340, "lng": 77.0397, "radius": 52, "area": 3200, "count": 4500},
}

GATES = {
    "G1": {"name": "Gate 1 (entry)", "kind": "entry", "open": True, "zone": "A"},
    "G2": {"name": "Gate 2 (entry)", "kind": "entry", "open": True, "zone": "C"},
    "G3": {"name": "Gate 3 (exit)", "kind": "exit", "open": True, "zone": "D"},
    "G4": {"name": "Gate 4 (emergency exit)", "kind": "exit", "open": False, "zone": "C"},
}

HOSPITALS = {
    "H_KMCH":  {"name": "KMCH (Avinashi Rd)",           "cap_red": 2, "cap_yellow": 3},
    "H_PSG":   {"name": "PSG Hospitals (Peelamedu)",    "cap_red": 5, "cap_yellow": 10},
    "H_CMCH":  {"name": "Coimbatore Medical College Hospital", "cap_red": 8, "cap_yellow": 15},
    "H_ROYAL": {"name": "Royal Care (Neelambur)",       "cap_red": 3, "cap_yellow": 6},
}

# Unit types and capabilities
UNIT_TYPES = {
    "ALS": {"label": "ALS ambulance", "caps": ["als", "bls", "transport"]},
    "BLS": {"label": "BLS ambulance", "caps": ["bls", "transport"]},
    "MED": {"label": "Medic team", "caps": ["medic", "first_aid"]},
    "POL": {"label": "Police squad", "caps": ["police"]},
    "VOL": {"label": "CPR-trained volunteer", "caps": ["first_aid", "cpr"]},
    "WAT": {"label": "Water & cooling team", "caps": ["water"]},
}

UNITS = [
    ("A1", "ALS", "G4"), ("A2", "BLS", "G1"), ("A3", "ALS", "B_PEEL"),
    ("A4", "BLS", "B_GANDHI"), ("A5", "BLS", "B_NEEL"), ("A6", "ALS", "B_GANDHI"),
    ("M1", "MED", "VENUE"), ("M2", "MED", "G3"),
    ("P1", "POL", "G1"), ("P2", "POL", "VENUE"), ("P3", "POL", "J_AIR"), ("P4", "POL", "G3"), ("P5", "POL", "G2"),
    ("W1", "WAT", "G3"),
    ("V1", "VOL", "zone:A"), ("V2", "VOL", "zone:B"), ("V3", "VOL", "zone:C"), ("V4", "VOL", "zone:D"),
]

# ---------------- Timed events (the demo script) ----------------
# Each event is applied at the start of the given minute.
END_MINUTE = 30  # the scenario stops here; /api/step clamps, Play and Demo mode stop

EVENTS = [
    {"minute": 0, "type": "report", "text": "Zone A-la 2 per mayakkam pottu vizhunthutaanga, romba veyil. (2 people fainted in Zone A, too hot)"},
    {"minute": 0, "type": "report", "text": "மண்டலம் C-யில் 5 வயது குழந்தை காணவில்லை, சிவப்பு சட்டை. (child missing in Zone C)"},
    {"minute": 0, "type": "report", "text": "Road accident at Hope College junction on Avinashi Road, bike and car, 2 injured, one unconscious."},
    {"minute": 2, "type": "report", "text": "Another person fainted near Gate 1 in zone A, heat exhaustion."},
    {"minute": 4, "type": "report", "text": "Stage front zone B people pushing hard, very crowded, someone shouting"},
    {"minute": 6, "type": "report", "text": "Zone B too tight, we cannot move, kids are crying, please do something"},
    {"minute": 7, "type": "report", "text": "B பகுதியில் ரொம்ப கூட்டம், நகர முடியவில்லை, தள்ளுகிறார்கள் (Zone B very crowded, cannot move, people pushing)"},
    {"minute": 10, "type": "vip_delay", "minutes": 180, "note": "Organisers announce the main guest will be 3 hours late"},
    {"minute": 10, "type": "power", "on": False, "note": "Power failure at the venue - lights and PA system down"},
    {"minute": 10, "type": "report", "text": "STAMPEDE at stage front zone B!! people falling, 12 injured, 4 not breathing properly, blood"},
    {"minute": 11, "type": "unit_stall", "unit": "A2", "note": "(hidden truth) crowd surrounds ambulance A2 near Gate 1 - it stops moving; nobody reports it"},
    {"minute": 11, "type": "report", "text": "நெரிசல் B பகுதியில், நிறைய பேர் கீழே விழுந்துவிட்டார்கள் (crush in zone B, many people fell)"},
    {"minute": 12, "type": "road_block", "a": "J_AIR", "b": "J_HOPE", "note": "Avinashi Rd between Airport and Hope College blocked by crowd spill-over"},
    {"minute": 14, "type": "power", "on": True, "note": "Power restored"},
]
