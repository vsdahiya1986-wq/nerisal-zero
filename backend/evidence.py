"""
Evidence Lab: does acting on NERISAL's warnings help beyond the one scripted demo?
Runs N randomised rallies (same seeds for every policy) and compares three human policies.

    python backend/evidence.py --n 200 --out docs/evidence.json   (chart needs: pip install matplotlib)

Synthetic model-based simulation, not real-world validation.
"""
import argparse
import json
import os
import random
import statistics
import time

import scenario as S
from engine import Engine

POLICIES = {
    "no_action": "No action – nobody approves anything",
    "late": "Late action – approve crowd-control only after crush conditions start",
    "advised": "NERISAL advised – approve crowd-control 1 minute after it is raised",
}
# Crowd-control proposals a commander would approve on the system's advice. Diversions and confirmations are
# judgement calls and are never auto-approved by any policy.
CROWD_CONTROL = {"gate", "open_corridor", "halt_event", "mutual_aid", "reserve"}
CRUSH_DENSITY = 5.0


def make_variant(seed):
    rng = random.Random(seed)
    zone_mult = {z: round(rng.uniform(0.8, 1.2), 3) for z in sorted(S.ZONES)}
    entry_mult = {"G1": round(rng.uniform(0.7, 1.3), 3), "G2": round(rng.uniform(0.7, 1.3), 3)}
    delay, delay_at = rng.randint(60, 240), rng.randint(6, 12)
    power_at = None if rng.random() < 0.25 else rng.randint(8, 13)
    heat = round(rng.uniform(32, 40), 1)
    events = []
    for ev in S.EVENTS:
        ev = dict(ev)
        if ev["type"] == "report" and (ev.get("needs_crush") or Engine._is_crush_text(ev["text"])):
            continue  # in variants the crush report comes from the physics (Engine._physical_crush_report)
        if ev["type"] == "vip_delay":
            ev.update(minute=delay_at, minutes=delay, note=f"Organisers announce the main guest will be {delay} min late")
        if ev["type"] == "power":
            if power_at is None:
                continue
            ev["minute"] = power_at if not ev["on"] else power_at + 4
        events.append(ev)
    return {"seed": seed, "zone_mult": zone_mult, "entry_mult": entry_mult, "heat_c": heat, "events": events,
            "crush_on_condition": True,
            "knobs": {"guest_delay_min": delay, "delay_announced_at": delay_at, "power_fail_at": power_at, "heat_c": heat}}


def run_one(seed, policy, minutes=S.END_MINUTE):
    e = Engine(variant=make_variant(seed), twin=False)
    decisions, crush_start = 0, None
    for _ in range(minutes):
        e.step(1)
        m, ser = e.st["minute"], e.st["series"]
        if crush_start is None and len(ser) >= 2 and ser[-1]["B"] >= CRUSH_DENSITY and ser[-2]["B"] >= CRUSH_DENSITY:
            crush_start = ser[-2]["m"]
        if policy == "no_action":
            continue
        for a in list(e.st["approvals"].values()):
            if a["status"] != "pending" or a["effect"]["kind"] not in CROWD_CONTROL:
                continue
            if (policy == "advised" and m >= a["minute"] + 1) or (policy == "late" and crush_start is not None):
                e.decide(a["id"], "approve")
                decisions += 1
    ser = e.st["series"]
    return {"seed": seed, "crush": crush_start is not None, "crush_start": crush_start,
            "start_b": ser[0]["B"],  # >= 5 means crush density before any warning could exist
            "peak_b": max(r["B"] for r in ser),
            "people_minutes_above_5": sum(r["B_people"] for r in ser if r["B"] > CRUSH_DENSITY),
            "unmet_at_end": len(e.st.get("plan_raw", {}).get("unmet", [])),
            "hospitals_overloaded": len((e.st.get("hospital_plan") or {}).get("overload_plan", [])),
            "decisions": decisions}


def _pct(xs, q):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, max(0, round(q * (len(xs) - 1))))]


def summarise(runs):
    peaks = [r["peak_b"] for r in runs]
    prev = [r for r in runs if r["start_b"] < CRUSH_DENSITY]
    return {"crush_rate": round(sum(r["crush"] for r in runs) / len(runs), 3),
            "preventable_runs": len(prev),
            "crush_rate_preventable": round(sum(r["crush"] for r in prev) / len(prev), 3) if prev else None,
            "peak_b_median": round(statistics.median(peaks), 2), "peak_b_p10": _pct(peaks, 0.1), "peak_b_p90": _pct(peaks, 0.9),
            "people_minutes_above_5_median": statistics.median(r["people_minutes_above_5"] for r in runs),
            "unmet_at_end_mean": round(statistics.mean(r["unmet_at_end"] for r in runs), 2),
            "hospitals_overloaded_rate": round(sum(r["hospitals_overloaded"] > 0 for r in runs) / len(runs), 3),
            "decisions_mean": round(statistics.mean(r["decisions"] for r in runs), 2)}


def run_lab(n=200, seed0=1, progress=None):
    t0 = time.time()
    out = {"n": n, "seed0": seed0, "minutes": S.END_MINUTE, "crush_condition": f"Zone B >= {CRUSH_DENSITY} p/m² for >= 2 consecutive minutes",
           "note": "Synthetic model-based simulation, not real-world validation.", "policies": {}}
    total, done = n * len(POLICIES), 0
    for p, label in POLICIES.items():
        runs = []
        for seed in range(seed0, seed0 + n):
            runs.append(run_one(seed, p))
            done += 1
            if progress:
                progress(done / total)
        out["policies"][p] = {"label": label, "summary": summarise(runs), "runs": runs}
    a, z = out["policies"]["advised"]["summary"], out["policies"]["no_action"]["summary"]
    out["headline"] = (f"In {n} simulated rallies, acting on NERISAL's first warnings kept Zone B out of crush conditions in "
                       f"{round(100 * (1 - a['crush_rate']))} % of runs vs {round(100 * (1 - z['crush_rate']))} % with no action.")
    k = n - a["preventable_runs"]
    if k and a["crush_rate_preventable"] is not None:
        out["headline_preventable"] = (
            f"{k} runs were already at crush density when monitoring began (no warning can prevent those). In the other "
            f"{a['preventable_runs']}: {round(100 * (1 - a['crush_rate_preventable']))} % stayed safe with NERISAL advice vs "
            f"{round(100 * (1 - z['crush_rate_preventable']))} % with no action.")
    out["seconds"] = round(time.time() - t0, 1)
    return out


def write_png(data, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    names = list(data["policies"])
    labels = ["No action", "Late action", "NERISAL advised"][:len(names)]
    colors = ["#ef4444", "#f59e0b", "#14b8a6"][:len(names)]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10, 4), dpi=120)
    xs = range(len(names))
    rates = [100 * data["policies"][p]["summary"]["crush_rate"] for p in names]
    prev = [100 * (data["policies"][p]["summary"]["crush_rate_preventable"] or 0) for p in names]
    npv = data["policies"][names[0]]["summary"]["preventable_runs"]
    for off, vals, alpha, lab in ((-0.2, rates, 1.0, f"all {data['n']} runs"),
                                  (0.2, prev, 0.45, f"{npv} runs not already critical at T+0")):
        bars = a1.bar([x + off for x in xs], vals, width=0.4, color=colors, alpha=alpha, label=lab, edgecolor="#333")
        for b, r in zip(bars, vals):
            a1.text(b.get_x() + b.get_width() / 2, r + 1.5, f"{r:.0f}%", ha="center", fontsize=9, fontweight="bold")
    a1.set_xticks(list(xs), labels)
    a1.set_ylim(0, 135)
    a1.legend(fontsize=8, loc="upper center", ncol=2, frameon=False)
    a1.set_ylabel("Runs reaching crush conditions (%)")
    a1.set_title("Crush conditions (Zone B ≥ 5 p/m² for 2+ min)")
    a2.boxplot([[r["peak_b"] for r in data["policies"][p]["runs"]] for p in names], tick_labels=labels)
    a2.axhline(CRUSH_DENSITY, color="#ef4444", ls="--", lw=1)
    a2.text(0.55, CRUSH_DENSITY + 0.08, "crush danger 5 p/m²", color="#ef4444", fontsize=9)
    a2.set_ylabel("Peak Zone B density (p/m²)")
    a2.set_title("Peak density per run")
    fig.suptitle(f"Evidence Lab – {data['n']} simulated rallies, same seeds for every policy (synthetic simulation)", fontsize=11)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--n", type=int, default=200)
    ap.add_argument("--seed0", type=int, default=1)
    ap.add_argument("--out", default=os.path.join(os.path.dirname(__file__), "..", "docs", "evidence.json"))
    ap.add_argument("--png", default=None, help="default: next to --out as evidence.png")
    args = ap.parse_args()
    shown = set()

    def show(f):
        if int(f * 10) not in shown:
            shown.add(int(f * 10))
            print(f"{10 * int(f * 10)}% ", end="", flush=True)
    data = run_lab(args.n, args.seed0, progress=show)
    print()
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    png = args.png or os.path.join(os.path.dirname(args.out), "evidence.png")
    write_png(data, png)
    print(data["headline"])
    print(data.get("headline_preventable", ""))
    for p, d in data["policies"].items():
        print(f"{p:10s} {d['summary']}")
    print(f"{data['seconds']} s -> {args.out}, {png}")
