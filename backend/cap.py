"""
Public alert export in CAP 1.2 (OASIS Common Alerting Protocol), the standard public warning systems ingest.
Always status "Exercise": this is a demo, never a real alert.
"""
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

import scenario as S

NS = "urn:oasis:names:tc:emergency:cap:1.2"
IST = timezone(timedelta(hours=5, minutes=30))
ET.register_namespace("", NS)


def _sub(parent, tag, text=None):
    el = ET.SubElement(parent, f"{{{NS}}}{tag}")
    if text is not None:
        el.text = str(text)
    return el


def build_cap(st, ann_id):
    """CAP 1.2 XML (bytes, UTF-8) for one announcement, or None if the id is unknown."""
    a = next((x for x in st["announcements"] if x["id"] == ann_id), None)
    if a is None:
        return None
    zid = a["zone"]
    z = st["zones"][zid]
    lat, lng = S.NODES["VENUE"]

    alert = ET.Element(f"{{{NS}}}alert")
    _sub(alert, "identifier", f"NERISAL-{a['minute']}-{zid}-{a['id']}")
    _sub(alert, "sender", "nerisal-zero.demo")
    _sub(alert, "sent", datetime.now(IST).replace(microsecond=0).isoformat())
    _sub(alert, "status", "Exercise")
    _sub(alert, "msgType", "Alert")
    _sub(alert, "scope", "Public")

    texts = {
        "ta-IN": (f"மண்டலம் {zid}: கூட்ட நெரிசல் அபாயம்",
                  f"மண்டலம் {zid}-இல் கூட்ட அடர்த்தி ஒரு சதுர மீட்டருக்கு {z['density']} பேர். இது ஒரு பயிற்சி எச்சரிக்கை.",
                  a["ta"]),
        "en-IN": (f"Crowd crush risk in {z['name']}",
                  f"Crowd density in {z['name']} is {z['density']} people per square metre. This is an exercise alert.",
                  a["en"]),
    }
    for lang, (headline, description, instruction) in texts.items():
        info = _sub(alert, "info")  # CAP element order matters
        _sub(info, "language", lang)
        _sub(info, "category", "Safety")
        _sub(info, "event", "Crowd crush risk")
        _sub(info, "urgency", "Immediate")
        _sub(info, "severity", "Severe")
        _sub(info, "certainty", "Likely")
        _sub(info, "senderName", "NERISAL ZERO (demo)")
        _sub(info, "headline", headline)
        _sub(info, "description", description)
        _sub(info, "instruction", instruction)
        area = _sub(info, "area")
        _sub(area, "areaDesc", f"{z['name']}, {st['venue']['name']}")
        _sub(area, "circle", f"{lat},{lng} 0.5")
    ET.indent(alert)  # readable in the modal
    return ET.tostring(alert, encoding="utf-8", xml_declaration=True)
