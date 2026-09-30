"""
Resource Allocation Agent
Assigns units to incident needs by solving an assignment problem that minimises
expected harm = (time-criticality of the incident) x (arrival time), plus a penalty for
leaving a need unmet. This is deterministic optimisation, not an LLM guess, so every
decision is repeatable and auditable.

- Units already on scene / transporting / unavailable are locked.
- A unit already driving to one incident gets a switching penalty, so the plan does not
  flip-flop; if the optimiser still wants to divert it, the Command Agent asks a human.
"""
import numpy as np
from scipy.optimize import linear_sum_assignment

from .triage import TYPES

UNMET_MIN = 45.0      # an unmet need is treated like a 45-minute delay
SWITCH_PEN = 12.0     # minutes-equivalent penalty for diverting an en-route unit
ALS_ON_BLS_PEN = 2.0  # keep advanced ambulances for the worst cases
BIG = 1e9


def weight(inc):
    rate = TYPES[inc["type"]]["rate"]
    cas = inc["casualties"]
    size = 1 + 0.25 * cas.get("red", 0) + 0.08 * cas.get("yellow", 0)
    return rate * (inc["severity"] / 3.0) * (0.6 + 0.4 * inc["confidence"]) * size


class ResourceAgent:
    name = "Resource Allocation Agent"

    def solve(self, st, route, extra_incidents=(), removed_units=(), respect_locks=True, use_reserve=False):
        incidents = [i for i in st["incidents"].values() if i["status"] == "open"] + list(extra_incidents)
        units = {u["id"]: u for u in st["units"].values() if u["id"] not in removed_units}

        # 1. slots
        slots = []
        for inc in incidents:
            for cap, n in inc["needs"].items():
                for k in range(n):
                    slots.append({"inc": inc, "cap": cap})

        # 2. pre-fill with locked units (on scene at that incident) and forced diversions
        fixed = {}
        free_units = []
        for u in units.values():
            if u["status"] == "unavailable" or (u.get("reserve") and not use_reserve):
                continue
            locked = u["status"] in ("on_scene", "transporting") or (u["status"] == "en_route" and u.get("no_divert"))
            if respect_locks and locked and u.get("incident"):
                fixed[u["id"]] = u["incident"]
            elif u.get("forced"):
                fixed[u["id"]] = u["forced"]
            else:
                free_units.append(u)

        open_slots = []
        used_fixed = set()
        for s in slots:
            match = None
            for uid, iid in fixed.items():
                if uid in used_fixed or iid != s["inc"]["id"]:
                    continue
                if s["cap"] in units[uid]["caps"]:
                    match = uid
                    break
            if match:
                used_fixed.add(match)
                s["unit"] = match
                s["eta"] = 0.0 if units[match]["status"] in ("on_scene", "transporting") else units[match].get("eta_left", 0)
                s["locked"] = True
            else:
                open_slots.append(s)
        # transporting ambulances are not free even if their slot was not matched
        free_units = [u for u in free_units if u["status"] not in ("transporting",)]

        # 3. cost matrix
        n, m = len(open_slots), len(free_units)
        assign = {}
        if n:
            C = np.full((n, m + n), BIG)
            eta_cache = {}
            for i, s in enumerate(open_slots):
                w = weight(s["inc"])
                for j, u in enumerate(free_units):
                    if s["cap"] not in u["caps"]:
                        continue
                    key = (u["id"], s["inc"]["id"])
                    if key not in eta_cache:
                        e = route.eta(st, u, s["inc"])
                        if e is not None and u["status"] == "en_route":
                            elapsed = (u.get("eta_total") or 0) - (u.get("eta_left") or 0)
                            e = round(max(0.5, e - elapsed), 1)
                        eta_cache[key] = e
                    eta = eta_cache[key]
                    if eta is None:
                        continue
                    c = w * eta
                    if s["cap"] == "bls" and "als" in u["caps"]:
                        c += w * ALS_ON_BLS_PEN
                    if u["status"] == "en_route" and u.get("incident") and u["incident"] != s["inc"]["id"]:
                        c += w * SWITCH_PEN
                    C[i, j] = c
                C[i, m + i] = w * UNMET_MIN
            rows, cols = linear_sum_assignment(C)
            for i, j in zip(rows, cols):
                s = open_slots[i]
                if j < m and C[i, j] < BIG:
                    u = free_units[j]
                    s["unit"] = u["id"]
                    s["eta"] = eta_cache[(u["id"], s["inc"]["id"])]
                    assign[u["id"]] = s
        # 4. summarise
        plan = {"slots": [], "unmet": [], "unit_to_inc": {}, "harm": 0.0, "unmet_weight": 0.0, "total_weight": 0.0}
        for s in slots:
            w = weight(s["inc"])
            plan["total_weight"] += w
            row = {"incident": s["inc"]["id"], "cap": s["cap"], "unit": s.get("unit"), "eta": s.get("eta"),
                   "locked": s.get("locked", False)}
            plan["slots"].append(row)
            if s.get("unit"):
                plan["unit_to_inc"][s["unit"]] = s["inc"]["id"]
                plan["harm"] += w * (s.get("eta") or 0)
            else:
                plan["unmet"].append({"incident": s["inc"]["id"], "cap": s["cap"]})
                plan["unmet_weight"] += w
                plan["harm"] += w * UNMET_MIN
        return plan
