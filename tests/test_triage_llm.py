"""The Claude path of the Triage Agent: must fall back to rules on any failure. No network is used."""
import os
import sys
from types import SimpleNamespace

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from agents import llm  # noqa: E402
from agents.triage import IncidentTriageAgent, TriageOut  # noqa: E402


class FakeClient:
    def __init__(self, result):
        self.calls = 0
        self.messages = self
        self.result = result

    def parse(self, **kw):
        self.calls += 1
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


def agent_with(monkeypatch, result):
    fake = FakeClient(result)
    monkeypatch.setattr(llm, "client", lambda: fake)
    a = IncidentTriageAgent()
    a.use_llm = True
    return a, fake


def test_llm_failure_falls_back_to_rules_after_one_retry(monkeypatch):
    a, fake = agent_with(monkeypatch, RuntimeError("boom"))
    out = a.parse("stampede near stage")
    assert out["parser"] == "rules" and out["type"] == "crush"
    assert "boom" in out["llm_error"]
    assert fake.calls == 2


def test_llm_timeout_is_not_retried(monkeypatch):
    class APITimeoutError(Exception):
        pass
    a, fake = agent_with(monkeypatch, APITimeoutError("slow"))
    assert a.parse("fire near gate 3")["parser"] == "rules"
    assert fake.calls == 1


def test_llm_success_is_used_and_clamped(monkeypatch):
    parsed = TriageOut(type="faint", location="D", severity=9, confidence=1.4,
                       casualties={"red": 0, "yellow": 0, "green": -2}, summary="one person fainted")
    a, _ = agent_with(monkeypatch, SimpleNamespace(stop_reason="end_turn", parsed_output=parsed))
    out = a.parse("Zone D-la oru aal mayakkam")
    assert out["parser"] == "llm" and out["location"] == "D"
    assert out["severity"] == 5 and out["confidence"] == 1.0 and out["casualties"]["green"] == 0


def test_refusal_falls_back(monkeypatch):
    a, _ = agent_with(monkeypatch, SimpleNamespace(stop_reason="refusal", parsed_output=None))
    assert a.parse("someone collapsed")["parser"] == "rules"
