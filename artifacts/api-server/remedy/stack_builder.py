"""21/40-day Remedy Stack Builder.

Assembles a SINGLE daily routine (morning + day + evening) out of the
3 selected planet-remedies, instead of giving the user 12 disconnected
items they'll forget by day 3.

Per user-mandated design: connected daily routine has ~5x better
follow-through than disconnected lists.
"""
from __future__ import annotations

from typing import Any, Dict, List


def build_stack(planet_remedies: List[Dict[str, Any]],
                  system_practices: List[Dict[str, str]],
                  duration_days: int = 21,
                  topic: str = "health") -> Dict[str, Any]:
    """Build a single daily routine.

    Returns:
        {
          "duration_days": 21 | 40,
          "morning":   [str],
          "day":       [str],
          "evening":   [str],
          "weekly":    [str],   # day-specific items (Tue Hanuman etc)
          "track":     [str],   # KPI items to log
        }
    """
    morning: List[str] = []
    day:     List[str] = []
    evening: List[str] = []
    weekly:  List[str] = []
    track:   List[str] = []

    for r in (planet_remedies or [])[:3]:
        planet = r.get("planet", "?")
        prac = r.get("practical") or {}
        ayur = r.get("ayurvedic") or {}
        vedic = r.get("vedic") or {}

        # Practical → morning if "morning"/"AM" mentioned, else day
        action = prac.get("action") or ""
        if action:
            slot = morning if any(k in action.lower() for k in
                                    ("morning", "sunrise", "before 9", "am ")) \
                            else day
            slot.append(f"[{planet} • PRACTICAL] {action}")

        # KPI → track
        kpi = prac.get("kpi")
        if kpi:
            track.append(f"{planet}: {kpi}")

        # Ayurvedic → evening (most pranayama/herbs are evening-friendly)
        ayur_practice = ayur.get("practice")
        if ayur_practice:
            evening.append(f"[{planet} • AYURVEDIC] {ayur_practice}")
        ayur_herb = ayur.get("herb")
        if ayur_herb:
            note = f"[{planet} • HERB] {ayur_herb}"
            cav = ayur.get("vaidya_caveat")
            if cav and cav != "—":
                note += f" — ⚠ {cav}"
            evening.append(note)

        # Vedic → weekly (day-specific)
        v_day = vedic.get("day")
        v_mantra = vedic.get("mantra")
        v_count = vedic.get("count")
        v_free = vedic.get("free_alt")
        if v_day and v_mantra:
            weekly.append(
                f"[{planet} • VEDIC] {v_day}: \"{v_mantra}\" × {v_count}"
                + (f"  |  free alt: {v_free}" if v_free else "")
            )

    # System practices → daily (small, frequent)
    for sp in (system_practices or [])[:3]:
        day.append(f"[SYSTEM • {sp.get('system','?')}] {sp.get('practice','')}")

    return {
        "duration_days": duration_days,
        "morning":       morning,
        "day":           day,
        "evening":       evening,
        "weekly":        weekly,
        "track":         track,
    }
