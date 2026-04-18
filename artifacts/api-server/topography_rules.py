"""
Plot topography Vastu rules — slope, water flow, depressions.

Engine accepts an optional input:
  plot_topography: {
    "slope_low":   "NE" | "N" | "E" | ...,   # corner that slopes downward
    "slope_high":  "SW",                      # corner that's elevated
    "water_inlet": "N" | "NE" | "E",          # where water enters / well location
    "water_outlet":"SE" | "S" | "SW",         # drainage exit
  }

Returns finding dicts. Brihat Samhita Ch.53 + Vastu Saar Ch.4 + Mansara Ch.4.
"""
from __future__ import annotations
from typing import Any, Dict, List

# Ideal slope: NE low, SW high. Ideal water: enters N/NE, exits N/NE (never SW/S).
_IDEAL_LOW   = {"NE", "N", "E"}
_BAD_LOW     = {"SW", "S", "W"}     # SW low = "shubh nahi", drains wealth/health
_IDEAL_HIGH  = {"SW", "S", "W"}
_GOOD_INLET  = {"N", "NE", "E"}
_GOOD_OUTLET = {"N", "NE", "E"}     # water should LEAVE in NE direction too (counter-intuitive)
_BAD_OUTLET  = {"SW", "S"}          # SW outlet drains positive energy


def _norm(d: Any) -> str:
    s = str(d or "").strip().upper().replace("-", "")
    repl = {"NORTHEAST": "NE", "NORTHWEST": "NW", "SOUTHEAST": "SE", "SOUTHWEST": "SW",
            "NORTH": "N", "SOUTH": "S", "EAST": "E", "WEST": "W"}
    return repl.get(s, s)


def evaluate_topography(topo: Dict[str, Any]) -> List[Dict[str, Any]]:
    if not isinstance(topo, dict) or not topo:
        return []

    out: List[Dict[str, Any]] = []
    low      = _norm(topo.get("slope_low"))
    high     = _norm(topo.get("slope_high"))
    inlet    = _norm(topo.get("water_inlet"))
    outlet   = _norm(topo.get("water_outlet"))

    # ── Slope check ────────────────────────────────────────────────
    if low and high:
        if low in _IDEAL_LOW and high in _IDEAL_HIGH:
            out.append({
                "category":   "slope",
                "verdict":    "Ideal",
                "severity":   "minor",
                "title":      f"Plot slope ({low} low, {high} high) is ideal",
                "reason_en":  f"Brihat Samhita 53.86–88 prescribes the plot slope toward NE/N/E and elevation toward SW/S/W. Your plot's {low}-low / {high}-high gradient matches this exactly — water and prana flow naturally in the auspicious direction.",
                "reason_hi":  f"Brihat Samhita 53.86–88 ke anusaar plot ka dhalaan NE/N/E ki taraf hona chahiye. Aapka plot ({low} neecha, {high} ooncha) shubh hai — paani aur prana sahi disha me beh rahe hain.",
                "classical_ref": {"type": "vastu", "source": "Brihat Samhita 53.86"},
                "remedy_en":  "Maintain this slope; do not regrade. Keep the NE corner clear of heavy structures.",
                "remedy_hi":  "Yeh dhalaan banaye rakhein. NE kone me bhaari nirman na karein.",
            })
        elif low in _BAD_LOW:
            out.append({
                "category":   "slope",
                "verdict":    "Avoid",
                "severity":   "major",
                "title":      f"Plot slope reversed — {low} corner is low",
                "reason_en":  f"Vastu Saar Ch.4 warns that an SW/S/W low corner (yours: {low}) drains stability and accumulated wealth toward the dead-energy side. Brihat Samhita classifies this as 'Vipreet Vastu'.",
                "reason_hi":  f"Vastu Saar Ch.4 ke anusaar SW/S/W kone ka neecha hona ('{low}' aapke yahan) sthirta aur sanchit dhan ko nikaal deta hai — Vipreet Vastu.",
                "classical_ref": {"type": "vastu", "source": "Vastu Saar Ch.4"},
                "remedy_en":  "Raise the SW/S/W corner with paving, soil fill, or a heavy planter. If structural change isn't possible, plant a tall Ashok / coconut tree at the low corner to anchor energy.",
                "remedy_hi":  f"{low} kone ko ooncha karein (mitti / paver). Possible nahi to wahan lamba Ashok / nariyal ka ped lagayein.",
            })
        else:
            out.append({
                "category":   "slope",
                "verdict":    "Adjustment Needed",
                "severity":   "moderate",
                "title":      f"Plot slope ({low} low) is acceptable but not ideal",
                "reason_en":  f"Your slope toward {low} is neutral — neither classically ideal nor a defect. Brihat Samhita 53.86 prefers NE-low for maximum prana flow.",
                "reason_hi":  f"{low} ki taraf dhalaan tatastha hai — shubh nahi par dosh bhi nahi. NE-low sabse uttam.",
                "classical_ref": {"type": "vastu", "source": "Brihat Samhita 53.86"},
                "remedy_en":  "Add a small water feature (fountain / bird-bath) in the NE to compensate.",
                "remedy_hi":  "NE me chhota fountain / pakshi-jal-paatra rakhein.",
            })

    # ── Water inlet ────────────────────────────────────────────────
    if inlet:
        if inlet in _GOOD_INLET:
            out.append({
                "category":   "water_inlet",
                "verdict":    "Ideal",
                "severity":   "minor",
                "title":      f"Water inlet from {inlet} is auspicious",
                "reason_en":  f"Vastu Saar Ch.4 and Mansara Ch.4 require water (well, borewell, municipal connection) to enter from N/NE/E. Yours enters from {inlet} — auspicious.",
                "reason_hi":  f"Vastu Saar / Mansara ke anusaar paani N/NE/E se aana chahiye. Aapka {inlet} se aa raha hai — shubh.",
                "classical_ref": {"type": "vastu", "source": "Vastu Saar Ch.4"},
                "remedy_en":  "Keep the inlet area clean and unblocked. A small Tulsi plant near the inlet enhances energy.",
                "remedy_hi":  "Inlet ke paas safai rakhein, Tulsi ka paudha lagayein.",
            })
        else:
            out.append({
                "category":   "water_inlet",
                "verdict":    "Avoid",
                "severity":   "major",
                "title":      f"Water inlet from {inlet} is inauspicious",
                "reason_en":  f"Water entering from {inlet} (S / SW / W) is classified as Jal-dosh in Vastu Saar Ch.4 — it brings stagnation and disease into the home.",
                "reason_hi":  f"{inlet} se paani aana Jal-dosh hai (Vastu Saar Ch.4) — sthirta ki jagah rog laata hai.",
                "classical_ref": {"type": "vastu", "source": "Vastu Saar Ch.4"},
                "remedy_en":  "Reroute the inlet pipe to enter from N or NE if possible. Otherwise install a copper kalash with Ganga-jal at the actual entry point.",
                "remedy_hi":  "Inlet pipe N/NE se laayein. Nahi ho sake to entry par tambe ka kalash + Ganga-jal rakhein.",
            })

    # ── Water outlet ───────────────────────────────────────────────
    if outlet:
        if outlet in _BAD_OUTLET:
            out.append({
                "category":   "water_outlet",
                "verdict":    "Adjustment Needed",
                "severity":   "moderate",
                "title":      f"Drainage exit from {outlet}",
                "reason_en":  f"Mansara Ch.4 cautions against waste-water exit through SW or S — these directions hold accumulated wealth and stability. Yours exits {outlet}.",
                "reason_hi":  f"Mansara Ch.4: SW/S se waste-water nikalna theek nahi (yahan: {outlet}).",
                "classical_ref": {"type": "vastu", "source": "Mansara Ch.4"},
                "remedy_en":  "If possible reroute the drain to exit NE or N. Otherwise place a Vastu pyramid at the outlet point.",
                "remedy_hi":  "Drain ko NE/N se nikalwayein. Nahi to outlet par Vastu pyramid rakhein.",
            })
        elif outlet in _GOOD_OUTLET:
            out.append({
                "category":   "water_outlet",
                "verdict":    "Ideal",
                "severity":   "minor",
                "title":      f"Drainage exit from {outlet} is auspicious",
                "reason_en":  f"Drainage flowing out via {outlet} keeps the SW/S corners 'heavy' as required by Brihat Samhita 53.88.",
                "reason_hi":  f"{outlet} se nikasi shubh — Brihat Samhita 53.88.",
                "classical_ref": {"type": "vastu", "source": "Brihat Samhita 53.88"},
                "remedy_en":  "Keep the outlet clear and odour-free.",
                "remedy_hi":  "Outlet saaf rakhein.",
            })
    return out
