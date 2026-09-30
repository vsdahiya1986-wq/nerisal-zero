"""Resource Allocation Agent rules. Uses a stub router so ETAs are fixed and the tests only check the optimiser."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from agents.resource import ResourceAgent  # noqa: E402


class StubRoute:
    def __init__(self, etas):
        self.etas = etas  # {(unit_id, incident_id): minutes}

    def eta(self, st, unit, inc):
        return self.etas.get((unit["id"], inc["id"]), 5.0)


def unit(uid, caps, status="available", incident=None):
    return {"id": uid, "caps": caps, "status": status, "incident": incident}


def incident(iid, itype, needs, severity=5):
    return {"id": iid, "type": itype, "needs": needs, "severity": severity, "confidence": 0.9,
            "casualties": {"red": 1, "yellow": 0, "green": 0}, "status": "open"}


def solve(incidents, units, etas=None):
    st = {"incidents": {i["id"]: i for i in incidents}, "units": {u["id"]: u for u in units}}
    return ResourceAgent().solve(st, StubRoute(etas or {}))


def test_als_need_never_filled_by_bls():
    plan = solve([incident("I1", "cardiac", {"als": 1})],
                 [unit("B1", ["bls", "transport"]), unit("B2", ["bls", "transport"])])
    assert plan["unit_to_inc"] == {}
    assert plan["unmet"] == [{"incident": "I1", "cap": "als"}]


def test_unit_on_scene_is_never_reassigned():
    # A1 is on scene at a minor accident; a cardiac arrest appears right next to it.
    plan = solve([incident("I1", "accident", {"als": 1}, severity=3), incident("I2", "cardiac", {"als": 1})],
                 [unit("A1", ["als", "bls", "transport"], status="on_scene", incident="I1")],
                 etas={("A1", "I2"): 0.5})
    assert plan["unit_to_inc"] == {"A1": "I1"}


def test_higher_weight_incident_wins_single_ambulance():
    # The accident is closer, but the cardiac arrest is more time-critical.
    plan = solve([incident("I1", "accident", {"als": 1}, severity=4), incident("I2", "cardiac", {"als": 1})],
                 [unit("A1", ["als", "bls", "transport"])],
                 etas={("A1", "I1"): 2.0, ("A1", "I2"): 3.0})
    assert plan["unit_to_inc"] == {"A1": "I2"}


def test_reserve_optimiser_picks_most_valuable_unit_and_reserve_never_hurts():
    from engine import Engine
    e = Engine()
    e.step(10)
    f = e.st["fragility"]
    assert f["best_reserve"] == max(f["if_lost"], key=f["if_lost"].get)
    pid = f"reserve_{f['best_reserve']}"
    assert pid in e.st["approvals"]
    before = f["score"]
    e.decide(pid, "approve")
    assert e.st["fragility"]["score"] <= before  # a reserve is usable by the next shock
