"""Pure numerology analysis for mobile, vehicle, house, name identifiers."""
from __future__ import annotations

from collections import Counter
from typing import Any, Dict, List, Tuple

from numerology.core.compatibility import rel_code
from numerology.core.digits import DIGIT_TRAITS, archetype_for, digit_trait, reduce_number

# Adjacent-digit friction (behavioral, not planetary)
_CONFLICT_PAIRS: Dict[Tuple[int, int], str] = {
    (4, 8): "Structure vs power — pace mismatch, delays under pressure",
    (8, 4): "Power vs structure — control struggles, rigid bottlenecks",
    (5, 8): "Change vs control — communication breaks when stressed",
    (8, 5): "Control vs change — micromanagement clashes",
    (6, 8): "Harmony vs authority — relationship/money tension",
    (8, 6): "Authority vs harmony — duty overload",
    (1, 8): "Leadership vs authority — ego vs hierarchy friction",
    (8, 1): "Authority vs leadership — competing agendas",
}

_HARMONY_PAIRS: Dict[Tuple[int, int], str] = {
    (1, 3): "Leadership + expression — visibility and messaging align",
    (3, 1): "Expression + leadership — pitch and presence combine",
    (2, 7): "Cooperation + analysis — listening + depth",
    (7, 2): "Analysis + cooperation — research + empathy",
    (3, 6): "Expression + harmony — creative client delight",
    (6, 3): "Harmony + expression — service with story",
    (5, 6): "Adaptability + harmony — sales and relationships",
    (6, 5): "Harmony + adaptability — network + care",
    (1, 5): "Leadership + movement — entrepreneurship energy",
    (5, 1): "Movement + leadership — agile initiative",
}


def _digits(value: str) -> List[int]:
    return [int(c) for c in value if c.isdigit()]


def repeating_digit_report(digits: List[int]) -> List[str]:
    if not digits:
        return []
    counts = Counter(digits)
    out = []
    for d, n in sorted(counts.items(), key=lambda x: -x[1]):
        if n >= 2:
            theme, _ = digit_trait(d)
            out.append(f"Digit {d} repeats {n}× — amplifies {theme}")
    return out


def missing_numbers_profile(digits: List[int]) -> List[int]:
    present = {d for d in digits if d != 0}
    return [n for n in range(1, 10) if n not in present]


def dominance_score(digits: List[int]) -> Tuple[int, float]:
    if not digits:
        return 0, 0.0
    counts = Counter(digits)
    dom_digit, dom_count = counts.most_common(1)[0]
    return dom_digit, round(dom_count / len(digits), 2)


def rhythm_pattern(digits: List[int]) -> str:
    if len(digits) < 3:
        return "Short sequence — limited rhythm data"
    jumps = [abs(digits[i] - digits[i + 1]) for i in range(len(digits) - 1)]
    avg = sum(jumps) / len(jumps)
    if avg <= 2:
        return "Smooth rhythm — gradual digit transitions"
    if avg >= 5:
        return "Volatile rhythm — sharp digit swings"
    return "Mixed rhythm — alternating calm and spike digits"


def stability_score(digits: List[int], driver: int) -> int:
    """0–100: higher = more aligned with driver number psychology."""
    if not digits:
        return 50
    reduced = [reduce_number(d) for d in digits]
    friend_hits = sum(1 for d in reduced if rel_code(driver, d) in ("T", "F"))
    base = int(40 + (friend_hits / len(reduced)) * 50)
    conflicts = sum(
        1 for i in range(len(digits) - 1)
        if (digits[i], digits[i + 1]) in _CONFLICT_PAIRS
    )
    return max(10, min(100, base - conflicts * 8))


def detect_digit_pairs(value: str) -> Tuple[List[Tuple[str, str]], List[Tuple[str, str]]]:
    digits = _digits(value)
    bad, good = [], []
    for i in range(len(digits) - 1):
        pair = (digits[i], digits[i + 1])
        key = f"{pair[0]}{pair[1]}"
        if pair in _CONFLICT_PAIRS:
            bad.append((key, _CONFLICT_PAIRS[pair]))
        if pair in _HARMONY_PAIRS:
            good.append((key, _HARMONY_PAIRS[pair]))
    return bad, good


def digit_position_rows(value: str, lang: str = "hinglish") -> List[Tuple[str, str]]:
    digits = _digits(value)
    if len(digits) < 4:
        return []
    first, middle, last = digits[0], digits[len(digits) // 2], digits[-1]
    last4 = "".join(str(d) for d in digits[-4:])
    t1, b1 = digit_trait(first)
    t2, b2 = digit_trait(middle)
    t3, b3 = digit_trait(last)
    return [
        ("First digit (opening tone)", f"{first} — {t1}: {b1}"),
        ("Middle digit (daily friction)", f"{middle} — {t2}: {b2}"),
        ("Last digit (closing impression)", f"{last} — {t3}: {b3}"),
        ("Last 4 digits (memory block)", f"{last4} — pattern people recall in OTP/SMS previews"),
    ]


def digit_chain_label(value: str) -> str:
    digits = _digits(value)[-6:]
    parts = []
    for d in digits:
        theme, _ = digit_trait(d)
        parts.append(f"{d}({theme.split('/')[0].strip()})")
    return " → ".join(parts)


def analyze_identifier(
    value: str,
    kind: str,
    driver: int,
    conductor: int,
) -> Dict[str, Any]:
    digits = _digits(value)
    total = sum(digits) if digits else 0
    reduced = reduce_number(total) if digits else 0
    dom_d, dom_pct = dominance_score(digits)
    return {
        "kind": kind,
        "raw": value,
        "digits": digits,
        "sum": total,
        "reduced": reduced,
        "archetype": archetype_for(reduced),
        "driver": driver,
        "conductor": conductor,
        "repeating": repeating_digit_report(digits),
        "missing": missing_numbers_profile(digits),
        "dominant_digit": dom_d,
        "dominance_pct": dom_pct,
        "rhythm": rhythm_pattern(digits),
        "stability_score": stability_score(digits, driver),
        "chain": digit_chain_label(value),
        "pairs_bad": detect_digit_pairs(value)[0],
        "pairs_good": detect_digit_pairs(value)[1],
    }


def why_impact_action_for_number(reduced: int, kind: str, lang: str = "hinglish") -> Dict[str, str]:
    arch = archetype_for(reduced)
    theme, behavior = digit_trait(reduced)
    templates = {
        "mobile": (
            f"Total reduces to {reduced} ({arch}) — {theme}.",
            f"Call/message habits reflect {behavior}.",
            "Schedule important conversations on dates that reduce to numbers in high sync with your Driver.",
        ),
        "vehicle": (
            f"Registration reduces to {reduced} ({arch}) — {theme}.",
            f"Travel pace and maintenance style follow {behavior}.",
            "Service and major trips on numerology-friendly dates for your Driver.",
        ),
        "house": (
            f"Unit number reduces to {reduced} ({arch}) — {theme}.",
            f"Home environment trends toward {behavior}.",
            "Keep entrance organised; reduce clutter on high-friction number dates.",
        ),
        "name": (
            f"Name vibration {reduced} ({arch}) — {theme}.",
            f"Public perception leans {behavior}.",
            "Align signature and display name with your corrected total when possible.",
        ),
    }
    why, impact, action = templates.get(kind, templates["mobile"])
    return {"why": why, "impact": impact, "action": action, "archetype": arch}
