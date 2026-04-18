"""
Room dimension Vastu rules — Mansara ratio + simplified Mayamatam aaya.

Per-room optional inputs in floor_plan items:
  {"room_type": "bedroom", "direction": "NE", "length_ft": 12, "width_ft": 10}

Returns a finding dict per room (only when dims provided).

References:
  - Mansara Shilpa Shastra Ch. 5–7  (auspicious length:width ratios)
  - Mayamatam Ch. 19                (ayadi shadvarga — area-based fortune key)
  - Vastu Saar Ch. 8                (minimum dimensions per room type)
"""
from __future__ import annotations
from typing import Any, Dict, Optional


# Mansara: ratio brackets
def _ratio_finding(length: float, width: float) -> Dict[str, Any]:
    if length <= 0 or width <= 0:
        return {}
    long_side, short_side = (length, width) if length >= width else (width, length)
    ratio = round(long_side / short_side, 2)

    if 1.0 <= ratio <= 1.5:
        verdict, severity = "Ideal", "minor"
        en = (f"Length:width = {ratio}:1 falls in Mansara Ch.5's auspicious bracket "
              f"(1.0–1.5). Room geometry supports balanced energy flow.")
        hi = (f"Length:width = {ratio}:1 — Mansara Ch.5 ke shubh range (1.0–1.5) me hai. "
              f"Kamre ki rachna santulit hai.")
        rem_en = "Maintain current proportions; place a square rug to reinforce the geometry."
        rem_hi = "Yahi anupaat rakhein; chaukor chatai bichhayein."
    elif 1.5 < ratio <= 2.0:
        verdict, severity = "Acceptable", "moderate"
        en = (f"Length:width = {ratio}:1 is acceptable but Mansara Ch.5 prefers ≤1.5. "
              f"The elongated shape mildly constricts prana circulation along the long axis.")
        hi = (f"Anupaat {ratio}:1 — chalega par Mansara Ch.5 ≤1.5 chahta hai. "
              f"Lambai ke saath prana pravah halki rok hoti hai.")
        rem_en = ("Subdivide the long axis with a tall plant or open shelf around the midpoint "
                  "to break the elongation.")
        rem_hi = "Lambai ke madhya me lamba paudha / open shelf rakhein."
    else:
        verdict, severity = "Avoid", "major"
        en = (f"Length:width = {ratio}:1 exceeds Mansara Ch.5's outer limit (2.0). "
              f"Highly elongated rooms create 'sukshma vedh' — energy stagnates at the far end.")
        hi = (f"Anupaat {ratio}:1 — Mansara Ch.5 ki seema (2.0) paar. "
              f"Atyant lamba kamra sukshma-vedh utpann karta hai, urja door wale chhor par ruk jaati hai.")
        rem_en = ("Partition the room with an arch or cabinet at the 1.4:1 mark, "
                  "or use 2 separate functional zones (sleeping + reading).")
        rem_hi = "1.4:1 ke nishaan par arch/cabinet se vibhaajan karein, ya 2 zone banayein."

    return {
        "category":   "dimension_ratio",
        "ratio":      ratio,
        "verdict":    verdict,
        "severity":   severity,
        "reason_en":  en,
        "reason_hi":  hi,
        "classical_ref": {"type": "vastu", "source": "Mansara Ch.5"},
        "remedy_en":  rem_en,
        "remedy_hi":  rem_hi,
    }


# Simplified Mayamatam aaya = (area * 8 / 12) % 12 → must NOT be 0 for residential
def _aaya_finding(length: float, width: float) -> Dict[str, Any]:
    if length <= 0 or width <= 0:
        return {}
    area = length * width
    aaya = int(round(area * 8 / 12)) % 12
    # Inauspicious aaya values (simplified — full table has 8/12 categories;
    # residential prefers 1, 3, 5, 8). 0/2/6/10 are flagged.
    bad = {0, 2, 6, 10}
    if aaya in bad:
        return {
            "category":   "dimension_aaya",
            "aaya":       aaya,
            "verdict":    "Adjustment Needed",
            "severity":   "moderate",
            "reason_en":  (f"Mayamatam Ch.19 'aaya' computed for {length}×{width} ft is {aaya} — "
                           "this index is flagged as inauspicious for residential use."),
            "reason_hi":  (f"Mayamatam Ch.19 ke aaya formula se aapka kamra ka index {aaya} aata hai — "
                           "rihaayash ke liye ashubh."),
            "classical_ref": {"type": "vastu", "source": "Mayamatam Ch.19"},
            "remedy_en":  ("Adjust internal usable area by ~6 inches on either dimension "
                           "(via a built-in cabinet, floor riser, or partition) to land on a "
                           "shubh aaya — most commonly target 1, 3, 5, or 8."),
            "remedy_hi":  ("Andar ke usable area ko 6\" badal dein (cabinet / partition se) "
                           "taaki aaya 1, 3, 5 ya 8 aaye."),
        }
    return {
        "category":   "dimension_aaya",
        "aaya":       aaya,
        "verdict":    "Ideal",
        "severity":   "minor",
        "reason_en":  f"Mayamatam aaya = {aaya} — auspicious for residential use.",
        "reason_hi":  f"Mayamatam aaya = {aaya} — rihaayash ke liye shubh.",
        "classical_ref": {"type": "vastu", "source": "Mayamatam Ch.19"},
        "remedy_en":  "No change needed.",
        "remedy_hi":  "Koi badlaav nahi chahiye.",
    }


def evaluate_room_dimensions(room: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Return combined dimension findings for a single room, or None if no dims."""
    try:
        length = float(room.get("length_ft") or 0)
        width  = float(room.get("width_ft")  or 0)
    except (TypeError, ValueError):
        return None
    if length <= 0 or width <= 0:
        return None

    return {
        "room_type": room.get("room_type"),
        "direction": room.get("direction"),
        "length_ft": length,
        "width_ft":  width,
        "ratio":     _ratio_finding(length, width),
        "aaya":      _aaya_finding(length, width),
    }
