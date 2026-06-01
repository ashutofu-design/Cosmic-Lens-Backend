"""
Phase S — core numerology (Driver, Conductor, Name number).
No Vastu, Kua, compass directions, or chart-derived home zones.
"""
from __future__ import annotations
from datetime import datetime
from typing import Any

ARCHETYPE_BY_NUMBER = {
    1: "Leadership / initiation",
    2: "Cooperation / sensitivity",
    3: "Creativity / expression",
    4: "Discipline / structure",
    5: "Adaptability / movement",
    6: "Responsibility / harmony",
    7: "Analysis / introspection",
    8: "Power / material mastery",
    9: "Completion / humanitarian drive",
}
PLANET_BY_NUMBER = ARCHETYPE_BY_NUMBER

NUMBER_NATURE = {
    1: "Leadership, originality, decisive initiative",
    2: "Sensitivity, intuition, partnership",
    3: "Learning, communication, creative expansion",
    4: "Structure, systems, steady building",
    5: "Adaptability, commerce, quick thinking",
    6: "Harmony, care, aesthetic responsibility",
    7: "Analysis, research, private depth",
    8: "Accountability, scale, long-term results",
    9: "Completion, intensity, collective impact",
}
NUMBER_FRIENDS = {
    1: [1, 3, 5, 9], 2: [2, 4, 7, 9], 3: [1, 3, 5, 6, 9], 4: [2, 4, 6, 8],
    5: [1, 3, 5, 6, 9], 6: [3, 4, 6, 8, 9], 7: [2, 5, 7, 9], 8: [4, 6, 8],
    9: [1, 2, 3, 5, 6, 9],
}
NUMBER_ENEMIES = {
    1: [8], 2: [1, 8], 3: [7, 8], 4: [5, 9], 5: [2, 8], 6: [7],
    7: [1, 3, 4, 6], 8: [1, 2, 5], 9: [8],
}


def _root(n: int) -> int:
    while n > 9:
        n = sum(int(d) for d in str(n))
    return n


def _name_number(name: str) -> int | None:
    if not name:
        return None
    m = {"a": 1, "b": 2, "c": 3, "d": 4, "e": 5, "f": 8, "g": 3, "h": 5, "i": 1, "j": 1,
         "k": 2, "l": 3, "m": 4, "n": 5, "o": 7, "p": 8, "q": 1, "r": 2, "s": 3, "t": 4,
         "u": 6, "v": 6, "w": 6, "x": 5, "y": 1, "z": 7}
    s = sum(m.get(c.lower(), 0) for c in name if c.isalpha())
    return _root(s) if s else None


def compute_phase_s(kundli: dict, birth: dict) -> dict[str, Any]:
    """Driver / Conductor / Name — kundli argument kept for API compatibility."""
    _ = kundli
    dob = birth.get("dob") or birth.get("date") or ""
    name = birth.get("name") or ""
    driver = conductor = name_num = None
    if isinstance(dob, str):
        try:
            d = datetime.strptime(dob, "%Y-%m-%d")
        except Exception:
            try:
                d = datetime.strptime(dob, "%d-%m-%Y")
            except Exception:
                d = None
        if d:
            driver = _root(d.day)
            full = sum(int(c) for c in dob if c.isdigit())
            conductor = _root(full)
    if name:
        name_num = _name_number(name)

    driver_arch = ARCHETYPE_BY_NUMBER.get(driver) if driver else None
    conductor_arch = ARCHETYPE_BY_NUMBER.get(conductor) if conductor else None
    name_arch = ARCHETYPE_BY_NUMBER.get(name_num) if name_num else None
    s1 = {
        "driver_mulank": driver,
        "conductor_bhagyank": conductor,
        "name_number": name_num,
        "driver_archetype": driver_arch,
        "conductor_archetype": conductor_arch,
        "name_archetype": name_arch,
        # legacy aliases (kept for backward compat; same psychology label, no planet)
        "driver_planet": driver_arch,
        "conductor_planet": conductor_arch,
        "name_planet": name_arch,
        "driver_nature": NUMBER_NATURE.get(driver) if driver else None,
        "conductor_nature": NUMBER_NATURE.get(conductor) if conductor else None,
        "driver_friend_numbers": NUMBER_FRIENDS.get(driver, []) if driver else [],
        "driver_enemy_numbers": NUMBER_ENEMIES.get(driver, []) if driver else [],
        "compatibility_driver_conductor": (
            "HARMONIOUS"
            if (driver and conductor and conductor in NUMBER_FRIENDS.get(driver, []))
            else (
                "CONFLICT"
                if (driver and conductor and conductor in NUMBER_ENEMIES.get(driver, []))
                else "NEUTRAL"
            )
        ),
    }
    return {"available": True, "s1_numbers": s1}


def format_phase_s(r: dict) -> str:
    if not r or not r.get("available"):
        return "▸ PHASE S NUMEROLOGY: ❌ unavailable"
    s = r["s1_numbers"]
    lines = ["▸ PHASE S CORE NUMEROLOGY (Driver / Conductor / Name):"]
    if s.get("driver_mulank"):
        lines.append(
            f"      ▪ Driver (Mulank): {s['driver_mulank']} → {s['driver_archetype']} — {s['driver_nature']}"
        )
    if s.get("conductor_bhagyank"):
        lines.append(
            f"      ▪ Conductor (Bhagyank): {s['conductor_bhagyank']} → "
            f"{s['conductor_archetype']} — {s['conductor_nature']}"
        )
    if s.get("name_number"):
        lines.append(f"      ▪ Name number: {s['name_number']} → {s['name_archetype']}")
    if s.get("driver_mulank"):
        lines.append(
            f"      ▪ Driver friends: {s['driver_friend_numbers']}; "
            f"enemies: {s['driver_enemy_numbers']}"
        )
        lines.append(f"      ▪ Driver↔Conductor: {s['compatibility_driver_conductor']}")
    return "\n".join(lines)
