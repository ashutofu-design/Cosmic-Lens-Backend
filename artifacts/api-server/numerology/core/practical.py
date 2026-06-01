"""
Sprint 53-N2 — Numerology Practical (psychology-only).

Pinnacles & challenges, mobile/vehicle/house checker, couple compatibility,
career recommendations — no gems, mantras, directions, or ritual catalog.
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Any

MASTER = {11, 22, 33}


def _digits(s: str) -> list[int]:
    return [int(c) for c in str(s) if c.isdigit()]


def _reduce(n: int, keep_master: bool = False) -> int:
    while n > 9:
        if keep_master and n in MASTER:
            return n
        n = sum(_digits(str(n)))
    return n


def _parse_dob(s: str) -> date | None:
    if not s:
        return None
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(s, fmt).date()
        except Exception:
            continue
    return None


PINNACLE_THEME = {
    1: "Independence, leadership, self-reliance",
    2: "Cooperation, partnerships, sensitivity",
    3: "Creative expression, social communication",
    4: "Hard work, foundation, building systems",
    5: "Freedom, change, versatility",
    6: "Family, responsibility, service",
    7: "Study, introspection, analysis",
    8: "Material success, power, recognition",
    9: "Humanitarianism, completion, wisdom",
    11: "Intuitive leadership (master pinnacle)",
    22: "Master building on grand scale",
    33: "Master teaching and healing impact",
}

CHALLENGE_THEME = {
    0: "No specific challenge — use full power of life-path",
    1: "Avoid dependence; learn to stand alone and decide independently",
    2: "Hyper-sensitivity; learn detachment, don't take things personally",
    3: "Self-doubt about creativity; express yourself without fear",
    4: "Rigidity / overwork; learn flexibility and rest",
    5: "Restlessness / addictions; learn discipline and commitment",
    6: "Over-responsibility; let others carry their own load",
    7: "Isolation / cynicism; trust life and people",
    8: "Money obsession or fear of power; balance material and personal values",
}


def compute_pinnacles_challenges(dob: date) -> dict[str, Any]:
    m = _reduce(dob.month)
    d = _reduce(dob.day)
    y = _reduce(dob.year)
    lp = _reduce(m + d + y)
    p1_end = 36 - lp
    pin = [
        ("1st Pinnacle", f"birth – age {p1_end}", _reduce(m + d, keep_master=True)),
        ("2nd Pinnacle", f"age {p1_end + 1} – {p1_end + 9}", _reduce(d + y, keep_master=True)),
        (
            "3rd Pinnacle",
            f"age {p1_end + 10} – {p1_end + 18}",
            _reduce(_reduce(m + d) + _reduce(d + y), keep_master=True),
        ),
        ("4th Pinnacle", f"age {p1_end + 19} – end", _reduce(m + y, keep_master=True)),
    ]
    chl = [
        ("1st Challenge", f"birth – age {p1_end}", abs(_reduce(m) - _reduce(d))),
        ("2nd Challenge", f"age {p1_end + 1} – {p1_end + 9}", abs(_reduce(d) - _reduce(y))),
        (
            "3rd Challenge",
            f"age {p1_end + 10} – {p1_end + 18}",
            abs(abs(_reduce(m) - _reduce(d)) - abs(_reduce(d) - _reduce(y))),
        ),
        ("4th Challenge", f"age {p1_end + 19} – end", abs(_reduce(m) - _reduce(y))),
    ]
    return {
        "life_path": lp,
        "pinnacles": [
            {"name": n, "period": p, "number": num, "theme": PINNACLE_THEME.get(num, "")}
            for n, p, num in pin
        ],
        "challenges": [
            {"name": n, "period": p, "number": num, "theme": CHALLENGE_THEME.get(num, "")}
            for n, p, num in chl
        ],
    }


NUMBER_DAILY_USE = {
    1: "Strong for leadership roles and visible accountability. Weak if you avoid ownership.",
    2: "Strong for partnerships, support roles, and client care. Weak for solo high-pressure sales.",
    3: "Strong for teaching, advisory, content, and communication income.",
    4: "Mixed — sudden shifts; good for tech, systems, and innovation. Weak if you need rigid stability.",
    5: "Versatile — sales, media, travel, brokerage. Suits most profiles when variety is wanted.",
    6: "Strong for hospitality, beauty, design, and relationship-led business.",
    7: "Mixed — research, writing, solo work. Weak for high-noise retail or constant social selling.",
    8: "Heavy — suits long-horizon builders and ops leaders. Can feel slow for impatient profiles.",
    9: "Strong for high-energy, mission-driven, physical or emergency roles.",
}


def check_number(
    any_number: str | int,
    driver: int | None = None,
    conductor: int | None = None,
) -> dict[str, Any]:
    s = str(any_number)
    digits = _digits(s)
    if not digits:
        return {"available": False, "reason": "no digits in input"}
    full_sum = sum(digits)
    last4_sum = sum(digits[-4:]) if len(digits) >= 4 else full_sum
    final = _reduce(full_sum)
    last4_final = _reduce(last4_sum)

    verdict = "NEUTRAL"
    reason = []
    if driver:
        from numerology.core.phase_s import NUMBER_ENEMIES, NUMBER_FRIENDS

        if final in NUMBER_FRIENDS.get(driver, []):
            verdict = "GOOD"
            reason.append(f"Final {final} is friend of your Driver {driver}")
        elif final in NUMBER_ENEMIES.get(driver, []):
            verdict = "AVOID"
            reason.append(f"Final {final} is enemy of your Driver {driver}")
    if conductor and conductor != driver:
        from numerology.core.phase_s import NUMBER_ENEMIES, NUMBER_FRIENDS

        if final in NUMBER_ENEMIES.get(conductor, []):
            if verdict == "GOOD":
                verdict = "MIXED"
            elif verdict == "NEUTRAL":
                verdict = "CAUTION"
            reason.append(f"Final {final} is enemy of Conductor {conductor}")

    return {
        "available": True,
        "input": s,
        "digit_sum": full_sum,
        "last4_sum": last4_sum,
        "final_number": final,
        "last4_final": last4_final,
        "vibration": NUMBER_DAILY_USE.get(final, ""),
        "verdict": verdict,
        "reason": reason or ["No driver/conductor reference — generic vibration only"],
    }


def compute_couple_compat(p1_birth: dict, p2_birth: dict) -> dict[str, Any]:
    d1 = _parse_dob((p1_birth or {}).get("dob", ""))
    d2 = _parse_dob((p2_birth or {}).get("dob", ""))
    if not d1 or not d2:
        return {"available": False, "reason": "Both DOBs required"}
    from numerology.core.phase_s import ARCHETYPE_BY_NUMBER, NUMBER_ENEMIES, NUMBER_FRIENDS

    drv1, drv2 = _reduce(d1.day), _reduce(d2.day)
    cond1 = _reduce(sum(_digits(d1.strftime("%d%m%Y"))))
    cond2 = _reduce(sum(_digits(d2.strftime("%d%m%Y"))))
    lp1 = _reduce(_reduce(d1.month) + _reduce(d1.day) + _reduce(d1.year))
    lp2 = _reduce(_reduce(d2.month) + _reduce(d2.day) + _reduce(d2.year))

    def rate(a, b):
        if a in NUMBER_FRIENDS.get(b, []) or b in NUMBER_FRIENDS.get(a, []):
            return "HARMONIOUS"
        if a in NUMBER_ENEMIES.get(b, []) or b in NUMBER_ENEMIES.get(a, []):
            return "CONFLICT"
        return "NEUTRAL"

    matches = {
        "driver_match": {"p1": drv1, "p2": drv2, "verdict": rate(drv1, drv2)},
        "conductor_match": {"p1": cond1, "p2": cond2, "verdict": rate(cond1, cond2)},
        "life_path_match": {"p1": lp1, "p2": lp2, "verdict": rate(lp1, lp2)},
    }
    score = sum(
        2 if m["verdict"] == "HARMONIOUS" else (-1 if m["verdict"] == "CONFLICT" else 0)
        for m in matches.values()
    )
    overall = (
        "EXCELLENT" if score >= 4 else
        "GOOD" if score >= 2 else
        "AVERAGE" if score >= 0 else "CHALLENGING"
    )
    a1 = ARCHETYPE_BY_NUMBER.get(drv1, "")
    a2 = ARCHETYPE_BY_NUMBER.get(drv2, "")
    return {
        "available": True,
        "p1_archetype": a1,
        "p2_archetype": a2,
        "p1_planet": a1,  # legacy key
        "p2_planet": a2,  # legacy key
        "matches": matches,
        "raw_score": score,
        "overall": overall,
    }


CAREER_BY_NUMBER = {
    1: [
        "Founder / CEO", "Project lead", "Sales leadership", "Public policy / civil services",
        "Executive coaching", "Operations commander",
    ],
    2: [
        "HR / people operations", "Counselling", "Nursing", "Hospitality",
        "Client success", "Diplomacy / partnerships",
    ],
    3: [
        "Teaching / professor", "Law / advocacy", "Banking / finance advisory",
        "Publishing / writing", "Content strategy", "Corporate training",
    ],
    4: [
        "IT / software", "Aviation", "Foreign trade", "Product research",
        "Film / photography", "Fintech / startup ops",
    ],
    5: [
        "Sales / marketing", "Media / journalism", "Brokerage", "Content creator",
        "Consulting", "Travel / events",
    ],
    6: [
        "Fashion / beauty", "Hotels / restaurants", "Interior design",
        "Healthcare client experience", "Music / arts", "Wedding / events",
    ],
    7: [
        "Research / analytics", "Writing / philosophy", "Psychology",
        "Data science", "Solo consulting", "Technical writing",
    ],
    8: [
        "Real estate", "Infrastructure / logistics", "Banking / insurance",
        "Manufacturing ops", "Judiciary-adjacent roles", "Asset management",
    ],
    9: [
        "Defence / security", "Sports / fitness", "Surgery / emergency medicine",
        "Engineering", "Manufacturing", "Motivational training",
    ],
}


PRODUCTIVITY_HABITS = {
    1: {
        "focus_block": "Morning 90-min deep work before meetings",
        "communication": "Direct updates — no passive-aggressive hints",
        "stress_reset": "Walk after conflict before replying",
        "lucky_dates": [1, 10, 19, 28],
    },
    2: {
        "focus_block": "Batch emotional 1:1s; protect quiet lunch",
        "communication": "Name feelings early — small issues out loud",
        "stress_reset": "Journal 5 min before bed",
        "lucky_dates": [2, 11, 20, 29],
    },
    3: {
        "focus_block": "Teach/create AM; admin PM",
        "communication": "Verify advice before sending",
        "stress_reset": "One screen-free creative hour weekly",
        "lucky_dates": [3, 12, 21, 30],
    },
    4: {
        "focus_block": "Deep work sprints; novelty via projects not jobs",
        "communication": "Document decisions — reduce ambiguity",
        "stress_reset": "Phone off 1 hr before sleep",
        "lucky_dates": [4, 13, 22, 31],
    },
    5: {
        "focus_block": "Time-box multitasking; one priority per block",
        "communication": "Phone-free hour with partner daily",
        "stress_reset": "10-min breathwork midday",
        "lucky_dates": [5, 14, 23],
    },
    6: {
        "focus_block": "Beauty/client AM; family admin PM",
        "communication": "Ask for reciprocity explicitly",
        "stress_reset": "Weekly personal hobby slot",
        "lucky_dates": [6, 15, 24],
    },
    7: {
        "focus_block": "Research blocks + 1 hr practical admin",
        "communication": "Share inner world in writing first",
        "stress_reset": "Solo walk without podcasts",
        "lucky_dates": [7, 16, 25],
    },
    8: {
        "focus_block": "Financial review weekly; long tasks Saturday",
        "communication": "Say appreciation out loud",
        "stress_reset": "Strength + mobility 3× week",
        "lucky_dates": [8, 17, 26],
    },
    9: {
        "focus_block": "Hard tasks early; movement before email",
        "communication": "24-hour rule on angry messages",
        "stress_reset": "Sport or gym daily non-negotiable",
        "lucky_dates": [9, 18, 27],
    },
}


def compute_practical(birth: dict) -> dict[str, Any]:
    dob = _parse_dob((birth or {}).get("dob", ""))
    if not dob:
        return {"available": False, "reason": "DOB missing"}
    drv = _reduce(dob.day)
    cond = _reduce(sum(_digits(dob.strftime("%d%m%Y"))))
    return {
        "available": True,
        "driver": drv,
        "conductor": cond,
        "pinnacles_challenges": compute_pinnacles_challenges(dob),
        "career_recommendations_driver": CAREER_BY_NUMBER.get(drv, []),
        "career_recommendations_conductor": CAREER_BY_NUMBER.get(cond, []),
        "productivity_habits_driver": PRODUCTIVITY_HABITS.get(drv, {}),
        "productivity_habits_conductor": PRODUCTIVITY_HABITS.get(cond, {}),
    }


def format_practical(r: dict) -> str:
    if not r or not r.get("available"):
        return "▸ NUMEROLOGY PRACTICAL (Sprint 53-N2): ❌ unavailable"
    lines = ["▸ NUMEROLOGY PRACTICAL (Sprint 53-N2)"]

    pc = r["pinnacles_challenges"]
    lines.append(f"  • Life-Path: {pc['life_path']}")
    lines.append("  • PINNACLES (4 life cycles):")
    for p in pc["pinnacles"]:
        lines.append(f"      ▪ {p['name']:<13} ({p['period']:<22}) → {p['number']}: {p['theme']}")
    lines.append("  • CHALLENGES (4 life cycles):")
    for c in pc["challenges"]:
        lines.append(f"      ▪ {c['name']:<13} ({c['period']:<22}) → {c['number']}: {c['theme']}")

    lines.append(f"  • CAREER FIT (Driver {r['driver']}):")
    for c in r["career_recommendations_driver"]:
        lines.append(f"      ▪ {c}")
    if r["conductor"] != r["driver"]:
        lines.append(f"  • CAREER FIT (Conductor {r['conductor']}):")
        for c in r["career_recommendations_conductor"]:
            lines.append(f"      ▪ {c}")

    habits = r.get("productivity_habits_driver") or {}
    if habits:
        lines.append(f"  • PRODUCTIVITY HABITS (Driver {r['driver']}):")
        lines.append(f"      Focus: {habits.get('focus_block', '—')}")
        lines.append(f"      Communication: {habits.get('communication', '—')}")
        lines.append(f"      Stress reset: {habits.get('stress_reset', '—')}")

    return "\n".join(lines)
