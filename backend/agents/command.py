"""
Command / Planning Agent (orchestrator)
1. Takes the optimised plan from the Resource Agent.
2. Stress-tests it against the next likely shocks -> Fragility Score (0-100).
3. Compares it with the previous plan -> Plan Diff (what changed, who is worse off, by how much).
4. Writes plain-language reasons.
5. Applies low-risk dispatches automatically, and sends risky actions (diverting a unit that is
   already responding, opening gates, halting the event, calling mutual aid) to the human gate.
"""
import copy

from .resource import weight, UNMET_MIN

CAP_LABEL = {"als": "advanced ambulance", "bls": "ambulance", "police": "police", "medic": "medic team",
             "first_aid": "first-aid", "water": "water team", "cpr": "CPR responder", "transport": "transport"}


class CommandAgent:
    name = "Command Agent"

    # ------------------------------------------------------------------
    def shock_share(self, st, route, resource, zid, removed=()):
        """Share of a hypothetical new crush's needs that would go unmet or late. Reserves ARE usable here:
        that is what a reserve is for."""
        shock = {"id": "SHOCK", "type": "crush", "title": "Hypothetical new crush", "location": zid,
                 "severity": 5, "confidence": 1.0, "casualties": {"red": 3, "yellow": 3, "green": 0},
                 "needs": {"als": 1, "bls": 1, "police": 1, "first_aid": 1}, "status": "open"}
        p1 = resource.solve(st, route, extra_incidents=[shock], removed_units=removed, use_reserve=True)
        shock_slots = [s for s in p1["slots"] if s["incident"] == "SHOCK"]
        miss = sum(1 for s in shock_slots if not s["unit"]) + 0.5 * sum(1 for s in shock_slots if s["unit"] and (s["eta"] or 0) > 12)
        return miss / max(1, len(shock_slots))

    def fragility(self, st, route, resource, plan):
        zid = st.get("riskiest_zone") or "B"
        s1 = self.shock_share(st, route, resource, zid)
        # shock 2: the busiest free ambulance fails
        amb = [u for u, i in plan["unit_to_inc"].items() if st["units"][u]["type"] in ("ALS", "BLS")
               and st["units"][u]["status"] in ("available", "en_route")]
        s2 = 0.0
        if amb:
            lost = amb[0]
            p2 = resource.solve(st, route, removed_units=[lost])
            s2 = min(1.0, max(0.0, (p2["unmet_weight"] - plan["unmet_weight"]) / max(1e-6, plan["total_weight"]) * 4))
        idle_amb = [u for u in st["units"].values() if u["type"] in ("ALS", "BLS") and u["status"] == "available"
                    and u["id"] not in plan["unit_to_inc"] and not u.get("reserve")]
        score = min(100, round(100 * (0.65 * s1 + 0.35 * s2)))
        # Reserve optimiser: for each idle ambulance, what would fragility be if it got committed elsewhere?
        # The one whose loss hurts most is the one worth holding back.
        if_lost = {u["id"]: min(100, round(100 * (0.65 * self.shock_share(st, route, resource, zid, [u["id"]]) + 0.35 * s2)))
                   for u in idle_amb}
        return {"score": score, "shock_zone": zid, "shock_unmet_share": round(s1, 2),
                "idle_ambulances": [u["id"] for u in idle_amb], "if_lost": if_lost,
                "best_reserve": max(if_lost, key=if_lost.get) if if_lost else None,
                "reserve": [u["id"] for u in st["units"].values() if u.get("reserve")]}

    # ------------------------------------------------------------------
    def coverage(self, st, route, log):
        """Kumbh 2025 lesson: AI cameras sent timely alerts, but when police rushed to one spot a second
        crush started elsewhere. Track, per zone, how fast a FREE police team and first-aider could arrive."""
        cov = {}
        for zid in st["zones"]:
            probe = {"location": zid}
            best = {"police": None, "first_aid": None}
            for u in st["units"].values():
                if u["status"] != "available" or u.get("reserve"):
                    continue
                for cap in best:
                    if cap in u["caps"]:
                        e = route.eta(st, u, probe)
                        if e is not None and (best[cap] is None or e < best[cap]):
                            best[cap] = e
            gap = [c for c, e in best.items() if e is None or e > 8]
            cov[zid] = {"police_eta": best["police"], "aid_eta": best["first_aid"], "gap": gap}
            was = st.get("coverage", {}).get(zid, {}).get("gap", [])
            if gap and not was and st["zones"][zid]["density"] >= 3.0:
                names = " and ".join("police" if g == "police" else "first aid" for g in gap)
                log(self.name, f"COVERAGE GAP: Zone {zid} has no free {names} within 8 min – every team is committed "
                               "elsewhere. A second surge here would go unanswered (the Kumbh 2025 failure mode).")
        st["coverage"] = cov
        return cov

    # ------------------------------------------------------------------
    def diff(self, st, prev, plan):
        out = []
        if prev is None:
            return out
        pu, nu = prev["unit_to_inc"], plan["unit_to_inc"]
        inc = st["incidents"]
        for u in sorted(set(pu) | set(nu)):
            a, b = pu.get(u), nu.get(u)
            if a == b:
                continue
            ta = inc[a]["title"] + f" ({a})" if a in inc else None
            tb = inc[b]["title"] + f" ({b})" if b in inc else None
            if a and b:
                out.append({"kind": "moved", "text": f"{u}: {ta} → {tb}"})
            elif b:
                out.append({"kind": "added", "text": f"{u} dispatched → {tb}"})
            else:
                out.append({"kind": "removed", "text": f"{u} released from {ta}"})
        # per-incident arrival change (best ETA)
        def best(p):
            r = {}
            for s in p["slots"]:
                if s["unit"] is not None and s["eta"] is not None:
                    r[s["incident"]] = min(r.get(s["incident"], 99), s["eta"])
            return r
        bp, bn = best(prev), best(plan)
        for iid in sorted(set(bp) | set(bn)):
            if iid not in inc or inc[iid]["status"] != "open":
                continue
            a, b = bp.get(iid), bn.get(iid)
            if a is not None and b is not None and b - a >= 1.5:
                out.append({"kind": "worse", "text": f"{inc[iid]['title']} ({iid}) first help now {b:.0f} min (was {a:.0f}) — worse by {b - a:.0f} min"})
            elif a is not None and b is not None and a - b >= 1.5:
                out.append({"kind": "better", "text": f"{inc[iid]['title']} ({iid}) first help now {b:.0f} min (was {a:.0f})"})
        pu_unmet = {(x["incident"], x["cap"]) for x in prev["unmet"]}
        for x in plan["unmet"]:
            if (x["incident"], x["cap"]) not in pu_unmet and x["incident"] in inc:
                out.append({"kind": "unmet", "text": f"NEW SHORTFALL: {inc[x['incident']]['title']} ({x['incident']}) has no {CAP_LABEL.get(x['cap'], x['cap'])}"})
        return out

    # ------------------------------------------------------------------
    def reasons(self, st, plan, prev):
        out = []
        inc = st["incidents"]
        pu = prev["unit_to_inc"] if prev else {}
        by_inc = {}
        for s in plan["slots"]:
            by_inc.setdefault(s["incident"], []).append(s)
        order = sorted(by_inc, key=lambda i: -weight(inc[i]) if i in inc else 0)
        for iid in order:
            if iid not in inc:
                continue
            i = inc[iid]
            got = [s for s in by_inc[iid] if s["unit"]]
            miss = [s for s in by_inc[iid] if not s["unit"]]
            new = [s for s in got if pu.get(s["unit"]) != iid and not s["locked"]]
            if new:
                parts = ", ".join(f"{s['unit']} ({CAP_LABEL.get(s['cap'], s['cap'])}, {s['eta']:.0f} min)" for s in new)
                out.append(f"{i['title']} ({iid}, severity {i['severity']}, priority weight {weight(i):.1f}): "
                           f"sent {parts} — the fastest units with the right capability once higher-harm incidents were covered.")
            if miss:
                caps = ", ".join(sorted({CAP_LABEL.get(s['cap'], s['cap']) for s in miss}))
                out.append(f"{i['title']} ({iid}) still short of: {caps}. Every eligible unit is committed to incidents "
                           f"with higher expected harm.")
        return out[:8]

    # ------------------------------------------------------------------
    def run(self, st, route, resource, hospital, log, propose):
        prev = st.get("plan_raw")
        plan = resource.solve(st, route)

        # Risky diversions -> human gate. Keep the unit on its current job until approved.
        for uid, iid in list(plan["unit_to_inc"].items()):
            u = st["units"][uid]
            if u["status"] == "en_route" and u.get("incident") and u["incident"] != iid and not u.get("forced"):
                old = st["incidents"][u["incident"]]
                new = st["incidents"][iid]
                gain = weight(new) * UNMET_MIN
                loss = weight(old) * 10
                # Only worth a human's attention if clearly better, and never pull help away from a crowd crush.
                sensible = gain >= 1.5 * loss and weight(new) > weight(old) and old["type"] != "crush"
                if sensible:
                        propose(f"divert_{uid}_{iid}", f"Divert {uid} from {old['title']} ({old['id']}) to {new['title']} ({new['id']})",
                            f"{uid} is already driving to {old['id']}. Moving it saves an estimated {gain:.0f} harm-points at "
                            f"{new['id']} and costs about {loss:.0f} at {old['id']} (help there arrives ~10 min later). "
                            "Pulling a responding unit is a human decision.",
                            {"kind": "divert", "unit": uid, "incident": iid}, risk="high")
                # keep current job in the applied plan
                plan["unit_to_inc"][uid] = u["incident"]
                for s in plan["slots"]:
                    if s["unit"] == uid:
                        s["unit"], s["eta"] = None, None
                        plan["unmet"].append({"incident": s["incident"], "cap": s["cap"]})
                for s in plan["slots"]:
                    if s["incident"] == old["id"] and s["unit"] is None and s["cap"] in u["caps"]:
                        s["unit"], s["eta"] = uid, u.get("eta_left")
                        plan["unmet"] = [x for x in plan["unmet"]
                                         if not (x["incident"] == old["id"] and x["cap"] == s["cap"])] + \
                            [x for x in plan["unmet"] if x["incident"] == old["id"] and x["cap"] == s["cap"]][1:]
                        break

        # Apply: dispatch newly assigned free units
        for s in plan["slots"]:
            uid = s["unit"]
            if not uid:
                continue
            u = st["units"][uid]
            if u["status"] == "available" or (u["status"] == "en_route" and u.get("forced") == s["incident"]):
                target = st["incidents"][s["incident"]]
                u.update(status="en_route", incident=target["id"], eta_left=s["eta"], eta_total=max(0.5, s["eta"] or 0.5),
                         start=(u["lat"], u["lng"]), cap_used=s["cap"])
                u.pop("forced", None)
            elif u["status"] == "en_route" and u.get("incident") == s["incident"] and s["eta"] is not None \
                    and not s.get("locked"):
                old_left = u.get("eta_left") or 0
                if abs(s["eta"] - old_left) >= 3:
                    elapsed = (u.get("eta_total") or 0) - old_left
                    u["eta_left"], u["eta_total"] = s["eta"], elapsed + s["eta"]
                    log("Corridor & Route Agent", f"{uid} re-routed: arrival now {s['eta']:.0f} min (was {old_left:.0f}).")
        # units no longer needed -> available
        for u in st["units"].values():
            if u["status"] == "en_route" and u["id"] not in plan["unit_to_inc"]:
                u.update(status="available", incident=None)

        hospital.run(st, route, log)
        self.coverage(st, route, log)
        frag = self.fragility(st, route, resource, plan)
        d = self.diff(st, prev, plan)
        changed = prev is None or prev["unit_to_inc"] != plan["unit_to_inc"] or \
            {(x['incident'], x['cap']) for x in prev["unmet"]} != {(x['incident'], x['cap']) for x in plan["unmet"]}
        if changed:
            st["plan_version"] += 1
            st["last_diff"] = {"version": st["plan_version"], "minute": st["minute"], "items": d}
            st["reasons"] = self.reasons(st, plan, prev)
            log(self.name, f"Plan v{st['plan_version']}: {len(plan['unit_to_inc'])} units assigned, "
                           f"{len(plan['unmet'])} unmet needs, fragility {frag['score']}/100.")
        st["plan_raw"] = copy.deepcopy(plan)
        st["fragility"] = frag

        # Fragility-driven proposals
        # Mutual aid: standard mass-casualty practice (a crush is open and the local fleet is almost fully
        # committed), or the plan is too fragile for the next shock.
        mci = any(i["type"] == "crush" and i["status"] == "open" for i in st["incidents"].values())
        if not st.get("mutual_aid") and (frag["score"] >= 50 or (mci and len(frag["idle_ambulances"]) <= 1)):
            why = (f"Mass-casualty incident open and only {len(frag['idle_ambulances'])} ambulance(s) idle. "
                   if mci else f"Fragility {frag['score']}/100. ")
            propose("mutual_aid", "Request 2 ambulances from neighbouring district (mutual aid)",
                    why + f"If one more crush happens in Zone {frag['shock_zone']}, "
                    f"{int(frag['shock_unmet_share'] * 100)}% of its needs could not be met in time.",
                    {"kind": "mutual_aid"}, risk="medium")
        if 35 <= frag["score"] and frag["best_reserve"] and not frag["reserve"]                 and not any(k.startswith("reserve_") for k in st["approvals"]):
            uid, lost = frag["best_reserve"], frag["if_lost"]
            tried = ", ".join(f"{u} → {v}" for u, v in sorted(lost.items(), key=lambda kv: -kv[1]))
            why = (f"{uid} is the idle ambulance the next-shock plan leans on most: if it is sent elsewhere, fragility "
                   f"rises to {lost[uid]}. (Fragility if each idle unit is lost: {tried}.)") if lost[uid] > frag["score"] else                 "No single idle ambulance changes the score; holding one back still keeps a unit free for the next shock."
            propose(f"reserve_{uid}", f"Hold {uid} in reserve at the venue",
                    f"Fragility {frag['score']}/100 now. {why}", {"kind": "reserve", "unit": uid}, risk="medium")
        return plan
