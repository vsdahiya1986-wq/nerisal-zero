"""
The only place that talks to Claude. Used for LANGUAGE only (reading reports, explaining plans),
never for allocation, routing or forecasts. Every caller must have a rule-based fallback.
"""
import os

MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-opus-5")
TIMEOUT_S = 8.0


def enabled():
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


def client():
    import anthropic  # optional dependency
    # max_retries=0: callers decide whether to retry, so a dead network costs 8 s, not 24 s.
    return anthropic.Anthropic(timeout=TIMEOUT_S, max_retries=0)
