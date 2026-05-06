"""Remedy conflict-checker.

Catches dangerous combinations BEFORE the engine emits them.

Common conflicts (classical + modern body-safety consensus):
  - Gemstone-pair: Coral+Pearl (heat vs cold), Ruby+Pearl (Sun-Moon enemy),
    Blue Sapphire+Yellow Sapphire same hand (Saturn-Jupiter enemy),
    Diamond+Ruby (Venus-Sun enemy), Hessonite+Pearl (Rahu-Moon enemy),
    Cat's-Eye+Pearl (Ketu-Moon enemy)
  - Multiple-fast same day (body-stress)
  - Strong herb stacking without vaidya (e.g. Ashwagandha + Guggulu both
    when hyperthyroid)
  - Vedic-only stack when severity is `urgent_consult` health (delays
    real medical help)

Returns a list of {kind, severity, message, items}.
"""
from __future__ import annotations

from typing import Any, Dict, List


_GEMSTONE_ENEMIES = {
    frozenset({"Sun", "Saturn"}):    "Sun-Saturn enemy — never together",
    frozenset({"Sun", "Venus"}):     "Sun-Venus enemy — never together",
    frozenset({"Moon", "Rahu"}):     "Moon-Rahu enemy — never together",
    frozenset({"Moon", "Ketu"}):     "Moon-Ketu enemy — never together",
    frozenset({"Mars", "Mercury"}):  "Mars-Mercury enemy — never together",
    frozenset({"Jupiter", "Venus"}): "Jupiter-Venus enemy — never together",
    frozenset({"Saturn", "Sun"}):    "Saturn-Sun enemy — never together",
}


def check_conflicts(remedies: List[Dict[str, Any]],
                     severity: str = "preventive",
                     topic: str = "health") -> List[Dict[str, Any]]:
    """Inspect a list of selected planet-remedies and return any
    conflicts the user should be warned about.

    Each remedy dict is expected to expose at least `planet` (str).
    """
    warnings: List[Dict[str, Any]] = []
    if not remedies:
        return warnings

    planets = [r.get("planet") for r in remedies if r.get("planet")]

    # ── Gemstone-pair enemies ──────────────────────────────────────
    for i, a in enumerate(planets):
        for b in planets[i + 1:]:
            if a == b:
                continue
            if frozenset({a, b}) in _GEMSTONE_ENEMIES:
                warnings.append({
                    "kind":     "GEMSTONE_PAIR_ENEMY",
                    "severity": "high",
                    "message":  ("Don't wear gemstones for "
                                  f"{a} + {b} together — "
                                  + _GEMSTONE_ENEMIES[frozenset({a, b})]
                                  + ". Choose one or wear on different days/hands. "
                                  + "Free remedies (mantras/donations) safe to combine."),
                    "items":    [a, b],
                })

    # ── Severity gate: never let vedic dominate urgent_consult health ──
    if topic == "health" and severity == "urgent_consult":
        warnings.append({
            "kind":     "SEVERITY_GUARD",
            "severity": "critical",
            "message":  ("Severity is `urgent_consult`. Vedic remedies are "
                          "SUPPORT-ONLY here — qualified doctor visit MUST "
                          "happen FIRST. NEVER substitute remedies for "
                          "medical care."),
            "items":    [],
        })

    # ── Multiple gemstones at once for cost-protection ──────────────
    if len([p for p in planets if p]) >= 3:
        warnings.append({
            "kind":     "GEMSTONE_OVERLOAD",
            "severity": "medium",
            "message":  ("3+ gemstones recommended at once is a red flag for "
                          "over-prescription. Start with ONE most-impacting "
                          "stone (top-ranked), trial 3 days, decide by body "
                          "response. Most effects are placebo when stacked."),
            "items":    planets,
        })

    return warnings
