"""
Hospital Surge Agent
Distributes casualties across hospitals by severity, travel time and live free beds,
so the nearest hospital is not overwhelmed while others sit idle (at Karur, one
government hospital had to call in every available doctor).
Also computes what a naive 'everyone to the nearest hospital' policy would do, so the
commander can see the difference.
"""
OVERLOAD_PEN = 40.0


class HospitalSurgeAgent:
    name = "Hospital Surge Agent"

    def run(self, st, route, log):
        hosp = st["hospitals"]
        load = {h: {"red": hosp[h]["load_red"], "yellow": hosp[h]["load_yellow"]} for h in hosp}
        naive = {h: {"red": hosp[h]["load_red"], "yellow": hosp[h]["load_yellow"]} for h in hosp}
        dist = {}
        for inc in st["incidents"].values():
            if inc["status"] != "open":
                continue
            etas = {h: route.eta_to_hospital(inc, h) for h in hosp}
            etas = {h: t for h, t in etas.items() if t is not None}
            if not etas:
                continue
            nearest = min(etas, key=etas.get)
            d = {}
            for tier in ("red", "yellow"):
                pending = inc["casualties"].get(tier, 0) - inc.get("delivered", {}).get(tier, 0)
                for _ in range(max(0, pending)):
                    naive[nearest][tier] += 1

                    def cost(h):
                        over = max(0, load[h][tier] + 1 - hosp[h][f"cap_{tier}"])
                        return etas[h] + OVERLOAD_PEN * over

                    best = min(etas, key=cost)
                    load[best][tier] += 1
                    d.setdefault(best, {"red": 0, "yellow": 0})[tier] += 1
            if d:
                dist[inc["id"]] = {"nearest": nearest, "split": d, "etas": etas}

        overload_naive = [h for h in hosp if naive[h]["red"] > hosp[h]["cap_red"] or naive[h]["yellow"] > hosp[h]["cap_yellow"]]
        overload_plan = [h for h in hosp if load[h]["red"] > hosp[h]["cap_red"] or load[h]["yellow"] > hosp[h]["cap_yellow"]]
        st["hospital_plan"] = {"distribution": dist, "projected": load, "naive": naive,
                               "overload_naive": overload_naive, "overload_plan": overload_plan}
        sig = str(sorted((k, sorted((h, tuple(v.items())) for h, v in d["split"].items())) for k, d in dist.items()))
        if sig != st.get("_hosp_sig"):
            st["_hosp_sig"] = sig
            for iid, d in dist.items():
                parts = ", ".join(f"{hosp[h]['name'].split(' (')[0]}: {v['red']} red / {v['yellow']} yellow" for h, v in d["split"].items())
                log(self.name, f"{iid} casualties -> {parts}.")
            if overload_naive and not overload_plan:
                names = ", ".join(hosp[h]["name"].split(" (")[0] for h in overload_naive)
                log(self.name, f"Sending everyone to the nearest hospital would overload {names}; "
                               "the plan spreads patients so no hospital exceeds its free beds.")
        return st["hospital_plan"]

    def pick(self, st, inc, tier="red"):
        """Hospital for the next patient of this incident (used when an ambulance leaves the scene)."""
        d = st.get("hospital_plan", {}).get("distribution", {}).get(inc["id"])
        if not d:
            return None
        for h, v in d["split"].items():
            if v.get(tier, 0) > 0 or v.get("yellow", 0) > 0:
                return h
        return next(iter(d["split"]))
