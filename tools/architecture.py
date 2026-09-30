"""Draw docs/architecture.png:  python tools/architecture.py"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch  # noqa: E402

OUT = os.path.join(os.path.dirname(__file__), "..", "docs", "architecture.png")
fig, ax = plt.subplots(figsize=(13, 7.2), dpi=120)
ax.set_xlim(0, 13)
ax.set_ylim(0, 7.2)
ax.axis("off")


def box(x, y, w, h, text, fc, ec="#1f2937", size=10, bold=False):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.04,rounding_size=0.12", fc=fc, ec=ec, lw=1.4))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=size, fontweight="bold" if bold else "normal", wrap=True)
    return (x, y, w, h)


def arrow(a, b, color="#374151", style="-|>", ls="-"):
    ax.add_patch(FancyArrowPatch(a, b, arrowstyle=style, mutation_scale=14, color=color, lw=1.4, linestyle=ls))


# inputs
ax.text(1.2, 6.85, "INPUTS", ha="center", fontsize=10, color="#6b7280", fontweight="bold")
box(0.1, 5.6, 2.2, 1.0, "Field reports\nTamil · Tanglish\nHindi · English", "#e0f2fe")
box(0.1, 4.3, 2.2, 1.0, "Citizen Pulse\nattendees' phones", "#ffedd5")
box(0.1, 3.0, 2.2, 1.0, "Crowd counts · unit GPS\n(simulated sensors)", "#e0f2fe")
box(0.1, 1.7, 2.2, 1.0, "Organiser's plan\n→ Permit Stress-Test", "#f3f4f6")

# shared state
state = box(4.1, 2.9, 3.0, 1.5, "Shared situation state\n(zones, incidents, units,\nhospitals, gates, log)", "#fef9c3", size=11, bold=True)
for y in (6.1, 4.8, 3.5):
    arrow((2.35, y), (4.05, 3.65))

# agents ring
agents = [("Crowd Pressure\nforecast 10 min", 3.1, 5.6), ("Incident Triage\nSilent Alarm", 5.0, 5.6),
          ("Corridor & Route\nstall detection", 6.9, 5.6), ("Resource Allocation\nHungarian, min harm", 3.1, 0.9),
          ("Hospital Surge\nspread by free beds", 5.0, 0.9), ("Command\nFragility · Plan Diff", 6.9, 0.9)]
for text, x, y in agents:
    box(x, y, 1.8, 0.95, text, "#ede9fe", size=9)
    top = y > 3
    arrow((x + 0.9, y if top else y + 0.95), (5.6, 4.45 if top else 2.85), color="#7c3aed", style="<|-|>")
ax.text(5.6, 6.85, "SIX AGENTS (deterministic maths; Claude only reads/explains language)", ha="center", fontsize=10,
        color="#6b7280", fontweight="bold")

# human gate + simulation
gate = box(8.9, 3.0, 2.0, 1.3, "HUMAN GATE\nCommander approves /\nrejects every risky step", "#fee2e2", ec="#b91c1c", size=10, bold=True)
arrow((7.15, 3.65), (8.85, 3.65), color="#b91c1c")
box(8.9, 5.0, 2.0, 1.1, "Decision Preview\napprove vs reject,\n10 min ahead", "#dcfce7", size=9)
box(8.9, 1.2, 2.0, 1.1, "No-action twin\nsame world, nobody acts\n→ Impact score", "#dcfce7", size=9)
arrow((9.9, 4.95), (9.9, 4.35), color="#15803d")
arrow((9.9, 2.35), (9.9, 2.95), color="#15803d")

# outputs
ax.text(12.0, 6.85, "OUTPUTS", ha="center", fontsize=10, color="#6b7280", fontweight="bold")
for i, t in enumerate(["Commander dashboard\nmap · living crowd", "Marshal phone page\n(Tamil)", "Public alert\nCAP 1.2 + SMS",
                       "After-action report\ngolden hour · latency", "Evidence Lab\n200 simulated rallies"]):
    y = 5.7 - i * 1.2
    box(11.2, y, 1.7, 0.95, t, "#f3f4f6", size=8.5)
    arrow((10.95, 3.65), (11.15, y + 0.47), color="#6b7280")

ax.text(6.5, 0.15, "NERISAL ZERO – all data synthetic; every risky action waits for a human.", ha="center", fontsize=9, color="#6b7280")
fig.tight_layout()
fig.savefig(OUT)
print("wrote", os.path.abspath(OUT))
