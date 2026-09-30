"""
NERISAL ZERO simulation engine.
Holds the shared situation state, runs the scenario clock, simulates the crowd and unit
movement, and orchestrates the agents on every event (every event triggers a re-plan).
"""
import copy

import scenario as S
from agents.command import CommandAgent
from agents.crowd import CrowdPressureAgent
from agents.geo import lerp
from agents.hospital import HospitalSurgeAgent
from agents.resource import ResourceAgent, weight
from agents.route import RouteAgent
from agents.triage import IncidentTriageAgent

FOOT = {"MED", "VOL", "WAT"}


class Engine:
    def __init__(self, shadow=False):
        self.shadow = shadow
        self.baseline = None
        self.crowd = CrowdPressureAgent()
        self.triage = IncidentTriageAgent()
        self.route = RouteAgent(S.NODES, S.EDGES)
        self.resource = ResourceAgent()
        self.hospital = HospitalSurgeAgent()
        self.command = CommandAgent()
        self.reset()

    # ------------------------------------------------------------------ setup
    def reset(self):
        st = {
            "minute": 0, "venue": copy.deepcopy(S.VENUE), "zones": copy.deepcopy(S.ZONES),
            "gates": copy.deepcopy(S.GATES), "incidents": {}, "units": {}, "hospitals": {},
            "blocked": set(), "approvals": {}, "announcements": [], "log": [], "events_seen": [],
            "plan_version": 0, "last_diff": None, "reasons": [], "fragility": {}, "mutual_aid": False,
            "averted": False, "series": [], "crush_minute": None,
        }
        for zid, z in st["zones"].items():
            z["density"] = round(z["count"] / z["area"], 2)
            z["forecast"] = z["density"]
            z["risk"] = "normal"
        for hid, h in S.HOSPITALS.items():
            lat, lng = S.NODES[hid]
            st["hospitals"][hid] = dict(h, id=hid, lat=lat, lng=lng, load_red=0, load_yellow=0)
        for uid, t, base in S.UNITS:
            self._add_unit(st, uid, t, base)
        self.st = st
        self._apply_events(0)
        self._think()
        self._record()
        if not self.shadow:
            # "No-action" twin: same crowd, same events, nobody approves anything.
            self.baseline = Engine(shadow=True)
        self._preview_cache = {}
        return st

    def _add_unit(self, st, uid, t, base):
        if base.startswith("zone:"):
            z = st["zones"][base[5:]]
            lat, lng, node = z["lat"], z["lng"], base
        else:
            lat, lng = S.NODES[base]
            node = base
        st["units"][uid] = {
            "id": uid, "type": t, "label": S.UNIT_TYPES[t]["label"], "caps": S.UNIT_TYPES[t]["caps"],
            "mode": "foot" if (t in FOOT or (t == "POL" and (base in ("G1", "G2", "G3", "G4", "VENUE")))) else "vehicle", "node": node, "lat": lat, "lng": lng,
            "status": "available", "incident": None,
        }

    # ------------------------------------------------------------------ helpers
    def log(self, agent, msg):
        self.st["log"].insert(0, {"minute": self.st["minute"], "agent": agent, "msg": msg})
        del self.st["log"][250:]

    def propose(self, pid, title, detail, effect, risk="medium"):
        if pid in self.st["approvals"]:
            return
        self.st["approvals"][pid] = {"id": pid, "title": title, "detail": detail, "effect": effect,
                                     "risk": risk, "status": "pending", "minute": self.st["minute"]}
        self.log("Command Agent", f"NEEDS HUMAN: {title}")

    def _think(self):
        """One full agent cycle: crowd -> route -> resource -> hospital -> command."""
        st = self.st
        self.crowd.run(st, self.log, self.propose)
        self.route.run(st, self.log)
        self.command.run(st, self.route, self.resource, self.hospital, self.log, self.propose)

    # ------------------------------------------------------------------ events
    def _apply_events(self, minute):
        st = self.st
        for i, ev in enumerate(S.EVENTS):
            if ev["minute"] != minute or i in st["events_seen"]:
                continue
            st["events_seen"].append(i)
            t = ev["type"]
            if t == "report":
                if ev.get("needs_crush") or self._is_crush_text(ev["text"]):
                    if st["zones"]["B"]["count"] / st["zones"]["B"]["area"] < 5.0:
                        if not st["averted"]:
                            st["averted"] = True
                            self.log("Crowd Pressure Agent",
                                     f"CRUSH AVERTED: after the shock, Zone B is at "
                                     f"{st['zones']['B']['count'] / st['zones']['B']['area']:.1f} p/m² (below 5.0). "
                                     "Early actions prevented the stampede that happens in the no-action run.")
                        continue
                self.log("Field report", ev["text"])
                self.triage.ingest(st, ev["text"], self.log, self.propose)
            elif t == "vip_delay":
                st["venue"]["vip_delay_min"] = ev["minutes"]
                self.log("Field report", ev["note"])
            elif t == "power":
                st["venue"]["power"] = ev["on"]
                self.log("Field report", ev["note"])
            elif t == "unit_stall":
                st["units"][ev["unit"]]["stalled"] = True
            elif t == "unit_down":
                u = st["units"][ev["unit"]]
                u.update(status="unavailable", incident=None)
                self.log("Field report", ev["note"])
            elif t == "road_block":
                st["blocked"].add(frozenset((ev["a"], ev["b"])))
                self.log("Field report", ev["note"])
                self.log("Corridor & Route Agent", "Road graph updated; all travel times recomputed and units re-routed.")

    @staticmethod
    def _is_crush_text(text):
        t = text.lower()
        return any(k in t for k in ["stampede", "நெரிசல்"])

    # ------------------------------------------------------------------ crowd dynamics
    def _crowd_step(self):
        st = self.st
        z, g, v = st["zones"], st["gates"], st["venue"]
        halted = v["event_halted"]
        if not halted:
            if g["G1"]["open"]:
                z["A"]["count"] += 300
            if g["G2"]["open"]:
                z["C"]["count"] += 180
        drift = 0.007
        if v["vip_delay_min"] >= 60 and not halted:
            drift += 0.004
        if not v["power"]:
            drift += 0.02
        if halted:
            drift = 0.0
        for zid in ("A", "C", "D"):
            mv = int(z[zid]["count"] * drift)
            z[zid]["count"] -= mv
            z["B"]["count"] += mv
        out3 = 150 if not halted else 350
        mv = min(z["D"]["count"], out3)
        z["D"]["count"] -= mv
        if halted:  # people move from B towards exits
            mv = int(z["B"]["count"] * 0.04)
            z["B"]["count"] -= mv
            z["D"]["count"] += mv // 2
            z["C"]["count"] += mv - mv // 2
            mv = min(z["A"]["count"], 200)
            z["A"]["count"] -= mv
        if g["G4"]["open"]:
            mv = min(z["B"]["count"], 260)
            z["B"]["count"] -= mv
            mv = min(z["C"]["count"], 200)
            z["C"]["count"] -= mv
        for zz in z.values():
            zz["count"] = max(0, zz["count"])

    # ------------------------------------------------------------------ unit movement
    def _target_coords(self, inc):
        if inc["location"] in self.st["zones"]:
            zz = self.st["zones"][inc["location"]]
            return (zz["lat"], zz["lng"]), "VENUE"
        return S.NODES[inc["location"]], inc["location"]

    def _move_units(self):
        st = self.st
        for u in st["units"].values():
            if u["status"] == "en_route":
                inc = st["incidents"].get(u["incident"])
                if not inc or inc["status"] != "open":
                    u.update(status="available", incident=None)
                    continue
                if u.get("stalled"):
                    # The vehicle is physically stuck. Nobody reports it; the system must notice.
                    u["no_progress"] = u.get("no_progress", 0) + 1
                    if u["no_progress"] >= 2:
                        self._stall_detected(u)
                    continue
                u["eta_left"] = round(max(0.0, (u.get("eta_left") or 0) - 1), 1)
                tgt, node = self._target_coords(inc)
                frac = 1 - u["eta_left"] / max(0.5, u.get("eta_total") or 1)
                u["lat"], u["lng"] = lerp(u.get("start", tgt), tgt, frac)
                if u["eta_left"] <= 0:
                    u.update(status="on_scene", arrived=st["minute"], lat=tgt[0], lng=tgt[1])
                    if u["mode"] == "vehicle":
                        u["node"] = node
                    self.log("Resource Allocation Agent", f"{u['id']} arrived at {inc['title']} ({inc['id']}).")
            elif u["status"] == "on_scene" and "transport" in u["caps"]:
                inc = st["incidents"].get(u["incident"])
                if not inc:
                    continue
                if st["minute"] - u.get("arrived", st["minute"]) >= 2:
                    delivered = inc.setdefault("delivered", {"red": 0, "yellow": 0})
                    moving = inc.setdefault("in_transit", {"red": 0, "yellow": 0})
                    left_red = inc["casualties"]["red"] - delivered["red"] - moving["red"]
                    left_yel = inc["casualties"]["yellow"] - delivered["yellow"] - moving["yellow"]
                    if left_red > 0:
                        load = {"red": 1, "yellow": 0}
                    elif left_yel > 0:
                        load = {"red": 0, "yellow": min(2, left_yel)}
                    else:
                        continue
                    hid = self.hospital.pick(st, inc) or "H_CMCH"
                    eta = self.route.eta_to_hospital(inc, hid) or 15
                    for k in load:
                        moving[k] += load[k]
                    u.update(status="transporting", hospital=hid, carry=load, eta_left=eta, eta_total=eta,
                             start=(u["lat"], u["lng"]))
                    self.log("Hospital Surge Agent", f"{u['id']} leaving {inc['id']} with "
                                                     f"{load['red']} red / {load['yellow']} yellow -> "
                                                     f"{st['hospitals'][hid]['name']} (ETA {eta:.0f} min).")
            elif u["status"] == "transporting":
                u["eta_left"] = round(max(0.0, u["eta_left"] - 1), 1)
                h = st["hospitals"][u["hospital"]]
                frac = 1 - u["eta_left"] / max(0.5, u["eta_total"])
                u["lat"], u["lng"] = lerp(u["start"], (h["lat"], h["lng"]), frac)
                if u["eta_left"] <= 0:
                    inc = st["incidents"].get(u["incident"])
                    h["load_red"] += u["carry"]["red"]
                    h["load_yellow"] += u["carry"]["yellow"]
                    if inc:
                        for k in ("red", "yellow"):
                            inc["in_transit"][k] -= u["carry"][k]
                            inc["delivered"][k] += u["carry"][k]
                    u.update(status="available", incident=None, node=u["hospital"], lat=h["lat"], lng=h["lng"],
                             carry=None)
                    self.log("Hospital Surge Agent", f"{u['id']} handed over patients at {h['name']}; available again.")

    def _stall_detected(self, u):
        st = self.st
        old = u.get("incident")
        u.update(status="unavailable", incident=None)
        # nearest zone to the stuck vehicle becomes the location of a new police task
        zid = min(st["zones"], key=lambda z: (st["zones"][z]["lat"] - u["lat"]) ** 2 + (st["zones"][z]["lng"] - u["lng"]) ** 2)
        self.log("Corridor & Route Agent",
                 f"STALL DETECTED: {u['id']} has not moved for 2 min while responding to {old}. Nobody reported it. "
                 f"Marked unavailable, its patients re-assigned, police requested to secure it (Karur: ambulances were surrounded).")
        iid = f"I{len(st['incidents']) + 1}"
        st["incidents"][iid] = {
            "id": iid, "type": "unit_blocked", "title": f"Ambulance {u['id']} blocked by crowd", "location": zid,
            "severity": 3, "confidence": 0.9, "casualties": {"red": 0, "yellow": 0, "green": 0},
            "needs": {"police": 1}, "reports": 1, "texts": ["auto-detected: no GPS progress"], "created": st["minute"],
            "status": "open", "parser": "sensor", "summary": f"{u['id']} GPS frozen for 2 min", "served_since": None,
            "unit_blocked": u["id"],
        }

    def _resolve_incidents(self):
        st = self.st
        for inc in st["incidents"].values():
            if inc["status"] != "open":
                continue
            here = [u for u in st["units"].values() if u.get("incident") == inc["id"] and u["status"] == "on_scene"]
            if here and inc.get("served_since") is None:
                inc["served_since"] = st["minute"]
            done = False
            if inc["type"] == "faint" and inc["served_since"] is not None and st["minute"] - inc["served_since"] >= 4:
                done, note = True, "patients cooled, rehydrated and recovering"
            elif inc["type"] == "missing_child" and inc["served_since"] is not None and st["minute"] - inc["served_since"] >= 5:
                done, note = True, "child found and reunited with parents"
            elif inc["type"] == "unit_blocked" and inc["served_since"] is not None and st["minute"] - inc["served_since"] >= 3:
                done, note = True, f"police cleared a path; {inc['unit_blocked']} moving again"
                bu = st["units"].get(inc["unit_blocked"])
                if bu:
                    bu.update(status="available", stalled=False, no_progress=0)
            elif inc["type"] == "pressure" and inc["location"] in st["zones"] and st["zones"][inc["location"]]["density"] < 4.0:
                done, note = True, "crowd density back below 4 p/m²"
            elif inc["type"] in ("crush", "accident", "cardiac", "fire"):
                dl = inc.get("delivered", {"red": 0, "yellow": 0})
                if dl["red"] >= inc["casualties"]["red"] and dl["yellow"] >= inc["casualties"]["yellow"] and \
                        (inc["casualties"]["red"] + inc["casualties"]["yellow"]) > 0:
                    done, note = True, "all red and yellow patients delivered to hospital"
            if done:
                inc["status"] = "resolved"
                inc["resolved_at"] = st["minute"]
                for u in st["units"].values():
                    if u.get("incident") == inc["id"] and u["status"] in ("on_scene", "en_route"):
                        u.update(status="available", incident=None)
                self.log("Command Agent", f"{inc['id']} {inc['title']} resolved: {note}.")

    # ------------------------------------------------------------------ public API
    def step(self, n=1):
        for _ in range(max(1, min(30, n))):
            self.st["minute"] += 1
            m = self.st["minute"]
            self._crowd_step()
            self._move_units()
            self._resolve_incidents()
            self._apply_events(m)
            self._think()
            self._record()
        if self.baseline:
            self.baseline.step(n)
        self._preview_cache = {}
        return self.st

    def report(self, text):
        self.log("Field report", text)
        self.triage.ingest(self.st, text, self.log, self.propose)
        self._think()
        if self.baseline:
            self.baseline.report(text)
        self._preview_cache = {}
        return self.st

    def decide(self, pid, decision):
        st = self.st
        a = st["approvals"].get(pid)
        if not a or a["status"] != "pending":
            return st
        a["status"] = "approved" if decision == "approve" else "rejected"
        a["decided_at"] = st["minute"]
        e = a["effect"]
        self.log("Commander (human)", f"{a['status'].upper()}: {a['title']}")
        if a["status"] == "approved":
            k = e["kind"]
            if k == "gate":
                st["gates"][e["gate"]]["open"] = e["open"]
            elif k == "open_corridor":
                st["gates"]["G4"]["open"] = True
                self.log("Corridor & Route Agent", "Gate 4 open: ambulance corridor to the stage front is clear.")
            elif k == "halt_event":
                st["venue"]["event_halted"] = True
                self.log("Crowd Pressure Agent", "Event halted: entries closed, phased dispersal started.")
            elif k == "mutual_aid":
                st["mutual_aid"] = True
                self._add_unit(st, "A7", "BLS", "B_NEEL")
                self._add_unit(st, "A8", "ALS", "B_NEEL")
                self.log("Resource Allocation Agent", "Mutual aid: A7 (BLS) and A8 (ALS) joined from the neighbouring district.")
            elif k == "reserve":
                st["units"][e["unit"]]["reserve"] = True
            elif k == "divert":
                st["units"][e["unit"]]["forced"] = e["incident"]
            elif k == "confirm":
                inc = st["incidents"].get(e["incident"])
                if inc:
                    inc["confidence"] = 0.9
        else:
            if e["kind"] == "divert":
                st["units"][e["unit"]]["no_divert"] = True
            if e["kind"] == "confirm" and e["incident"] in st["incidents"]:
                st["incidents"][e["incident"]]["status"] = "dismissed"
        self._think()
        self._preview_cache = {}
        return st

    # ------------------------------------------------------------------ twin futures
    def _record(self):
        st = self.st
        crush = [i for i in st["incidents"].values() if i["type"] == "crush"]
        if crush and st["crush_minute"] is None:
            st["crush_minute"] = min(i.get("crush_at", i["created"]) for i in crush)
        row = {"m": st["minute"], "B": st["zones"]["B"]["density"], "B_people": st["zones"]["B"]["count"],
               "max": max(z["density"] for z in st["zones"].values()),
               "unmet": len(st.get("plan_raw", {}).get("unmet", [])),
               "frag": st.get("fragility", {}).get("score", 0),
               "people": sum(z["count"] for z in st["zones"].values())}
        st["series"] = [r for r in st["series"] if r["m"] != row["m"]] + [row]

    @staticmethod
    def _impact_of(st):
        crush = [i for i in st["incidents"].values() if i["type"] == "crush"]
        return {"crush": st["crush_minute"] is not None, "crush_minute": st["crush_minute"],
                "peak_zone_b_density": max(r["B"] for r in st["series"]),
                "estimated_red_casualties": sum(i["casualties"]["red"] for i in crush),
                "people_minutes_above_5": sum(r.get("B_people", 0) for r in st["series"] if r["B"] > 5.0),
                "hospitals_overloaded": len((st.get("hospital_plan") or {}).get("overload_plan", [])),
                "unmet_needs_now": len(st.get("plan_raw", {}).get("unmet", []))}

    def impact(self):
        """Live vs no-action twin, in numbers."""
        return {"live": self._impact_of(self.st),
                "twin": self._impact_of(self.baseline.st) if self.baseline else None}

    def clone(self):
        b, self.baseline = self.baseline, None
        c = copy.deepcopy(self)
        self.baseline = b
        c.shadow = True
        return c

    def outcome(self, horizon):
        st = self.st
        crush = st["crush_minute"] is not None
        red = sum(i["casualties"]["red"] for i in st["incidents"].values() if i["type"] == "crush")
        delivered = sum(h["load_red"] + h["load_yellow"] for h in st["hospitals"].values())
        return {"peak_B": round(max(r["B"] for r in st["series"][-horizon - 1:]), 2), "crush": crush,
                "critical_red": red, "unmet": len(st.get("plan_raw", {}).get("unmet", [])),
                "fragility": st.get("fragility", {}).get("score", 0), "delivered": delivered,
                "people": sum(z["count"] for z in st["zones"].values())}

    def preview(self, pid, horizon=10):
        """Decision Preview: run the next `horizon` minutes twice - approve vs reject - before the human clicks."""
        key = (pid, self.st["minute"])
        if key in self._preview_cache:
            return self._preview_cache[key]
        a = self.st["approvals"].get(pid)
        if not a or a["status"] != "pending":
            return None
        out = {}
        for choice in ("approve", "reject"):
            c = self.clone()
            c.decide(pid, choice)
            c.step(horizon)
            out[choice] = c.outcome(horizon)
        y, n = out["approve"], out["reject"]
        verdict = []
        if n["crush"] and not y["crush"]:
            verdict.append("Approving PREVENTS the crush in this simulation.")
        if y["peak_B"] < n["peak_B"] - 0.2:
            verdict.append(f"Peak density in Zone B {y['peak_B']} vs {n['peak_B']} p/m².")
        if y["unmet"] < n["unmet"]:
            verdict.append(f"{n['unmet'] - y['unmet']} fewer unmet needs.")
        if y["fragility"] < n["fragility"] - 5:
            verdict.append(f"Fragility {y['fragility']} vs {n['fragility']}.")
        if y["delivered"] > n["delivered"]:
            verdict.append(f"{y['delivered']} patients reach hospital vs {n['delivered']}.")
        if y["crush"] and n["crush"]:
            verdict.append("On its own this does NOT prevent the crush in the next 10 min - combine it with other actions.")
        if not verdict:
            verdict.append("Little measurable difference in the next 10 minutes - judgement call.")
        res = {"id": pid, "horizon": horizon, "approve": y, "reject": n, "verdict": verdict}
        self._preview_cache[key] = res
        return res

    # ------------------------------------------------------------------ after-action report
    def after_action(self):
        st = self.st
        decisions = []
        for a in st["approvals"].values():
            decisions.append({"title": a["title"], "raised": a["minute"], "status": a["status"],
                              "decided": a.get("decided_at"),
                              "latency": (a["decided_at"] - a["minute"]) if a.get("decided_at") is not None else None})
        decisions.sort(key=lambda d: d["raised"])
        key_agents = ("Field report", "Commander (human)", "Command Agent", "Crowd Pressure Agent", "Corridor & Route Agent", "Incident Triage Agent")
        timeline = [l for l in reversed(st["log"]) if l["agent"] in key_agents and
                    any(k in l["msg"] for k in ("NEEDS HUMAN", "APPROVED", "REJECTED", "SILENT ALARM", "STALL", "COVERAGE GAP",
                                                "CRUSH", "resolved", "New incident", "CRITICAL", "DANGER", "Plan v"))
                    or l["agent"] == "Field report"]
        base = self.baseline.st if self.baseline else None
        return {
            "minute": st["minute"], "decisions": decisions, "timeline": timeline[-60:], "impact": self.impact(),
            "incidents": [{k: i[k] for k in ("id", "title", "location", "severity", "status", "created", "casualties")}
                          for i in st["incidents"].values()],
            "hospitals": [{k: h[k] for k in ("name", "load_red", "load_yellow", "cap_red", "cap_yellow")} for h in st["hospitals"].values()],
            "live": {"crush_minute": st["crush_minute"], "peak_B": max(r["B"] for r in st["series"]), "series": st["series"]},
            "baseline": {"crush_minute": base["crush_minute"], "peak_B": max(r["B"] for r in base["series"]),
                         "series": base["series"]} if base else None,
        }

    # ------------------------------------------------------------------ serialisation
    def snapshot(self):
        st = self.st
        roads = []
        for a, b, name, kind in S.EDGES:
            roads.append({"a": S.NODES[a], "b": S.NODES[b], "name": name, "kind": kind,
                          "blocked": frozenset((a, b)) in st["blocked"],
                          "corridor_closed": kind == "corridor" and not st["gates"]["G4"]["open"]})
        gates = {gid: dict(g, lat=S.NODES[gid][0], lng=S.NODES[gid][1]) for gid, g in st["gates"].items()}
        units = []
        for u in st["units"].values():
            units.append({k: u.get(k) for k in ("id", "type", "label", "status", "incident", "lat", "lng",
                                                 "eta_left", "hospital", "reserve", "mode", "no_progress")})
        plan = st.get("plan_raw", {})
        return {
            "minute": st["minute"], "venue": st["venue"], "zones": st["zones"], "gates": gates,
            "incidents": [dict(i, weight=round(weight(i), 2)) for i in st["incidents"].values()], "units": units, "hospitals": list(st["hospitals"].values()),
            "hospital_plan": st.get("hospital_plan"), "roads": roads,
            "approvals": sorted(st["approvals"].values(), key=lambda a: (a["status"] != "pending", -a["minute"])),
            "announcements": st["announcements"][:6], "log": st["log"][:80], "plan_version": st["plan_version"],
            "last_diff": st["last_diff"], "reasons": st["reasons"], "fragility": st["fragility"],
            "slots": plan.get("slots", []), "unmet": plan.get("unmet", []), "route_info": st.get("route_info"),
            "crowd_factors": st.get("crowd_factors", []), "averted": st["averted"],
            "coverage": st.get("coverage", {}), "series": st["series"], "crush_minute": st["crush_minute"],
            "baseline": ({"series": self.baseline.st["series"], "crush_minute": self.baseline.st["crush_minute"],
                          "averted": self.baseline.st["averted"]} if self.baseline else None),
            "total_people": sum(z["count"] for z in st["zones"].values()), "impact": self.impact(),
            "next_events": [e for i, e in enumerate(S.EVENTS) if i not in st["events_seen"]][:4],
        }
