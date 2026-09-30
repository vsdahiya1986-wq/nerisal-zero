"""
Permit Stress-Test (before the event).
Police / district administration enter what the organiser declared; the tool stress-tests the plan
against the crowd that may actually turn up (turnout multiplier) and a long delay of the main guest.

This is a deliberately simple, transparent planning model. Every assumption is visible and editable,
and none of it replaces official guidance (NDMA crowd-management guide, state SOPs for rallies).
"""
import math

ASSUMPTIONS = {
    "planning_density": 2.0,      # people per m2 used for planning a standing crowd (conservative)
    "danger_density": 5.0,        # people per m2 where crush risk becomes serious in a pushing crowd
    "exit_flow": 82,              # people per metre of exit width per minute (editable assumption)
    "target_egress_min": 8,       # minutes to empty the venue
    "ambulances_per_10k": 5,      # "4-5 ambulances per 10,000" cited by ambulance drivers after Karur
    "stage_area_share": 0.15,     # share of the ground in front of the stage
    "stage_crowd_share": 0.30,    # share of the crowd that packs the stage front at the start
    "drift_per_min": 0.007,       # share of the rest that pushes forward each minute of waiting
}


def assess(declared, area_m2, exit_width_m, ambulances, delay_min=0, heat_c=30, multipliers=(1.0, 2.0, 2.7), a=None):
    a = dict(ASSUMPTIONS, **(a or {}))
    # Form fields can be blank (0) or negative: clamp instead of crashing mid-pitch.
    declared, area_m2, ambulances, delay_min = max(0, declared), max(1.0, area_m2), max(0, ambulances), max(0, delay_min)
    multipliers = tuple(m for m in multipliers if m > 0) or (1.0, 2.0, 2.7)
    rows = []
    for m in multipliers:
        crowd = int(declared * m)
        avg = crowd / area_m2
        stage_area = max(1.0, area_m2 * a["stage_area_share"])
        stage = crowd * a["stage_crowd_share"]
        rest = crowd - stage
        drift = a["drift_per_min"] + (0.004 if delay_min >= 60 else 0) + (0.002 if heat_c >= 35 else 0)
        wait = min(delay_min, 90)
        for _ in range(int(wait)):
            mv = rest * drift
            rest -= mv
            stage += mv
        peak = stage / stage_area
        minutes_to_danger = None
        s2, r2 = crowd * a["stage_crowd_share"], crowd * (1 - a["stage_crowd_share"])
        for t in range(0, 181):
            if s2 / stage_area >= a["danger_density"]:
                minutes_to_danger = t
                break
            mv = r2 * drift
            r2 -= mv
            s2 += mv
        egress = crowd / max(0.1, exit_width_m * a["exit_flow"])
        amb_needed = math.ceil(crowd / 10000 * a["ambulances_per_10k"])
        issues = []
        if avg > a["planning_density"]:
            issues.append(f"Average {avg:.1f} p/m² is above the planning density of {a['planning_density']} p/m².")
        if peak >= a["danger_density"]:
            issues.append(f"Stage front reaches {peak:.1f} p/m² after a {wait}-min wait – crush risk.")
        elif peak >= 4:
            issues.append(f"Stage front reaches {peak:.1f} p/m² – very tight, movement lost.")
        if egress > a["target_egress_min"]:
            issues.append(f"Emptying the ground takes {egress:.0f} min (target {a['target_egress_min']}).")
        if ambulances < amb_needed:
            issues.append(f"{ambulances} ambulances on site; {amb_needed} recommended for this crowd.")
        if peak >= a["danger_density"] or avg > 4:
            verdict = "NO-GO"
        elif issues:
            verdict = "CONDITIONS"
        else:
            verdict = "GO"
        rows.append({"multiplier": m, "crowd": crowd, "avg_density": round(avg, 2), "stage_peak": round(peak, 2),
                     "minutes_to_danger": minutes_to_danger, "egress_min": round(egress, 1),
                     "ambulances_needed": amb_needed, "verdict": verdict, "issues": issues})
    cap_safe = int(area_m2 * a["planning_density"])
    exits_needed = round(declared * max(multipliers) / (a["exit_flow"] * a["target_egress_min"]), 1)
    conditions = [
        f"Cap entry at {cap_safe:,} people (gate counters; stop entry automatically at 90%).",
        f"Provide at least {exits_needed} m of total exit width for the worst-case turnout.",
        f"Keep {math.ceil(declared * max(multipliers) / 10000 * a['ambulances_per_10k'])} ambulances with a dedicated, barricaded ambulance lane.",
        "Barricaded pens at the stage front with a clear relief exit behind each pen.",
        "No-show rule: if the main guest is more than 60 minutes late, start phased dispersal.",
        "Backup power for lights and PA; pre-recorded Tamil / English dispersal announcements.",
    ]
    if heat_c >= 35:
        conditions.append("Heat above 35°C: shaded water points in every zone and roaming cooling teams.")
    return {"rows": rows, "safe_capacity": cap_safe, "exit_width_needed_m": exits_needed,
            "conditions": conditions, "assumptions": a}
