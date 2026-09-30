"""
Explain one Plan Diff line for the commander, in English + Tamil.
Claude only rewords the structured diff and the Command Agent's reasons; it never sees raw state and
cannot change the plan. Without a key (or on any failure) the matching template reason is shown.
"""
import re

from pydantic import BaseModel

from . import llm


class Explanation(BaseModel):
    english: str
    tamil: str


def template(item, reasons):
    ids = set(re.findall(r"\b[A-Z]\d+\b", item["text"]))
    hits = [r for r in reasons if ids & set(re.findall(r"\b[A-Z]\d+\b", r))]
    return " ".join(hits[:2]) or "No specific reason was recorded for this change."


def explain(item, reasons):
    fallback = template(item, reasons)
    if not llm.enabled():
        return {"en": fallback, "ta": None, "source": "template"}
    prompt = (
        "You explain an emergency dispatch plan change to the incident commander at a crowded rally. "
        "Use ONLY the facts below. Do not suggest a different plan. Write exactly 2 short sentences in plain English, "
        "and the same 2 sentences in simple Tamil.\n\n"
        f"Plan change ({item['kind']}): {item['text']}\n"
        "Planner's reasons:\n" + "\n".join(f"- {r}" for r in reasons)
    )
    try:
        msg = llm.client().messages.parse(model=llm.MODEL, max_tokens=2000, output_config={"effort": "low"},
                                          messages=[{"role": "user", "content": prompt}], output_format=Explanation)
        if msg.stop_reason != "end_turn" or msg.parsed_output is None:
            raise ValueError(f"stop_reason={msg.stop_reason}")
        return {"en": msg.parsed_output.english, "ta": msg.parsed_output.tamil, "source": "claude"}
    except Exception as e:
        print("Explain failed, using template:", e)
        return {"en": fallback, "ta": None, "source": "template"}
