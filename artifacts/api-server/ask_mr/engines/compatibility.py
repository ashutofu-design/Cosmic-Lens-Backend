from __future__ import annotations

import re

from vedic.love_reality.scoring_core import KundliReader, risk_band_high_is_good

from ._lordship import lordship_clause
from ._person_signals import build_person_signals, pick_notes
from ..types import EngineResult

_GUN_MILAN_Q = re.compile(r"(?ix)\b(gun\s*milan|36\s*gun|match\s*making)\b")
_EMOTIONAL_COMPAT_Q = re.compile(
    r"(?ix)\b("
    r"emotionally\s*compat(?:ible)?|emotional\s*compat(?:ibility)?|dil\s*ka\s*match"
    r")\b",
)
_MENTAL_COMPAT_Q = re.compile(
    r"(?ix)\b("
    r"mentally\s*compat(?:ible)?|mental\s*match|mental\s*compat(?:ibility)?|"
    r"thinking\s*match|soch\s*match|soch\s*milt|dimag|dimaag|personalities?\s*match|"
    r"swabhav\s*match"
    r")\b",
)
_INTELLECTUAL_COMPAT_Q = re.compile(
    r"(?ix)\b("
    r"intellectually\s*compat(?:ible)?|intellectual\s*match|intellectual\s*compat(?:ibility)?|"
    r"budhi|akl|samajh\s*match"
    r")\b",
)
_VALUES_GOALS_Q = re.compile(
    r"(?ix)\b("
    r"values?\s*(same|match|milt|align)|life\s*goals?\s*match|expectations?\s*(same|ek\s*jais)|"
    r"lifestyle\s*compat|hamare\s+sapne|ambition.*match"
    r")\b",
)
_GENERAL_COMPAT_Q = re.compile(r"\b(compatible|compatibility|rishta\s*achha)\b", re.I)

_POSITIVE_NOTE_KEYS = [
    "5th lord strong",
    "Moon-Moon supportive",
    "emotional reopening",
    "Saturn as 7th lord in 7th",
]
_FRICTION_NOTE_KEYS = [
    "Saturn on 7th",
    "Mars on 7th",
    "7th lord in dusthana",
    "7th lord debilitated",
    "Moon under Saturn/Rahu",
    "nodes on 7th",
    "Venus in dusthana",
    "Venus debilitated",
    "Navamsa Venus weak",
    "Navamsa Moon debilitated",
]


def _compatibility_intent(question: str) -> str:
    q = question or ""
    try:
        from ask_intent_fidelity import infer_compatibility_angle

        angle = (infer_compatibility_angle(q) or "").strip().lower()
        if angle in ("emotional_compatibility",):
            return "emotional_compatibility"
        if angle in ("mental_compatibility", "thinking_match", "personalities_match"):
            return "mental_compatibility"
        if angle in ("intellectual_compatibility",):
            return "intellectual_compatibility"
        if angle in ("values_match", "life_goals_match", "expectations_match"):
            return "values_goals_compatibility"
        if angle == "general_compatibility":
            return "general_compatibility"
    except Exception:
        pass
    if _GUN_MILAN_Q.search(q):
        return "gun_milan"
    if _MENTAL_COMPAT_Q.search(q):
        return "mental_compatibility"
    if _INTELLECTUAL_COMPAT_Q.search(q):
        return "intellectual_compatibility"
    if _EMOTIONAL_COMPAT_Q.search(q):
        return "emotional_compatibility"
    if _GENERAL_COMPAT_Q.search(q):
        return "general_compatibility"
    if _VALUES_GOALS_Q.search(q):
        return "values_goals_compatibility"
    return "general_compatibility"


def _synthesize_emotional_compatibility(kundli: dict, sig) -> list[str]:
    k = dict(kundli or {})
    k.setdefault("name", "You")
    r = KundliReader(k)
    lines: list[str] = []

    occ7 = r.occupants(7)
    if "Moon" in occ7:
        lines.append(
            "Moon in 7th — emotional tie to partner runs deep; closeness and mood-sync matter"
            f"{lordship_clause(r, 'Moon')}."
        )
    if "Venus" in occ7:
        lines.append(
            "Venus in 7th — affection and emotional harmony in partnership house"
            f"{lordship_clause(r, 'Venus')}."
        )
    if "Jupiter" in occ7:
        lines.append(
            "Jupiter in 7th — emotional maturity and fairness support compatibility"
            f"{lordship_clause(r, 'Jupiter')}."
        )

    ven = r.planet("Venus") or {}
    if ven.get("house") in (1, 4, 7, 9, 11):
        lines.append(
            f"Venus in house {ven.get('house')} — warmth and emotional generosity help the bond"
            f"{lordship_clause(r, 'Venus')}."
        )

    moon = r.planet("Moon") or {}
    if moon.get("house") in (1, 4, 5, 7) and "Moon in 7th" not in " ".join(lines):
        lines.append(
            f"Moon in house {moon.get('house')} — feelings are central; emotional language needs space"
            f"{lordship_clause(r, 'Moon')}."
        )

    for key in ("Moon under Saturn/Rahu", "Saturn on 7th", "nodes on 7th", "Moon debilitated"):
        picked = pick_notes(sig, [key], limit=1)
        if picked:
            line = picked[0]
            if not any(line in existing for existing in lines):
                extra = ""
                for pname in ("Moon", "Saturn", "Rahu", "Ketu"):
                    if pname in line:
                        extra = lordship_clause(r, pname)
                        break
                lines.append(f"Emotional friction: {line}{extra}")
        if len(lines) >= 5:
            break

    return lines[:5]


def _synthesize_mental_compatibility(kundli: dict, sig) -> list[str]:
    from .general_mr import _synthesize_communication

    lines = _synthesize_communication(kundli, sig)[:4]
    if not lines:
        lines.append(
            "Mental rapport builds through clear talk and shared routines — patience bridges thinking gaps."
        )
    for key in ("Saturn on 7th", "Moon under Saturn/Rahu", "Mars on 7th"):
        picked = pick_notes(sig, [key], limit=1)
        if picked and len(lines) < 5:
            lines.append(f"Mental friction: {picked[0]} — different processing pace needs patience.")
    return lines[:5]


def _synthesize_intellectual_compatibility(kundli: dict, sig) -> list[str]:
    k = dict(kundli or {})
    k.setdefault("name", "You")
    r = KundliReader(k)
    lines: list[str] = []

    merc = r.planet("Mercury") or {}
    if merc.get("house") in (1, 3, 5, 7, 9, 11):
        lines.append(
            f"Mercury in house {merc.get('house')} — ideas, debate and learning pace shape intellectual match"
            f"{lordship_clause(r, 'Mercury')}."
        )
    jup = r.planet("Jupiter") or {}
    if jup.get("house") in (1, 5, 7, 9, 11):
        lines.append(
            f"Jupiter in house {jup.get('house')} — wisdom and shared learning support intellectual sync"
            f"{lordship_clause(r, 'Jupiter')}."
        )
    occ7 = r.occupants(7)
    if "Mercury" in occ7:
        lines.append(
            "Mercury in 7th — partner thinks aloud; intellectual sync needs open dialogue."
        )
    for key in ("Saturn on 7th", "Moon under Saturn/Rahu"):
        picked = pick_notes(sig, [key], limit=1)
        if picked and len(lines) < 5:
            lines.append(f"Intellectual friction: {picked[0]} — explain ideas plainly when pace differs.")
    if not lines:
        lines.append(
            "Intellectual match is mixed — shared interests and respectful debate matter most."
        )
    return lines[:5]


def _synthesize_values_goals_compatibility(kundli: dict, sig) -> list[str]:
    k = dict(kundli or {})
    k.setdefault("name", "You")
    r = KundliReader(k)
    lines: list[str] = []

    jup = r.planet("Jupiter") or {}
    if jup.get("house") in (1, 4, 7, 9, 11):
        lines.append(
            f"Jupiter in house {jup.get('house')} — shared values and long-term direction align more easily"
            f"{lordship_clause(r, 'Jupiter')}."
        )
    lord7 = r.house_lord(7)
    p7l = r.planet(lord7) if lord7 else None
    if lord7 == "Saturn" or (p7l and p7l.get("house") in (10, 11)):
        lines.append(
            "Partnership axis leans practical — life goals need explicit planning and patience."
        )
    for key in ("Saturn on 7th", "7th lord in dusthana", "nodes on 7th"):
        picked = pick_notes(sig, [key], limit=1)
        if picked and len(lines) < 5:
            lines.append(f"Values/goals friction: {picked[0]} — align expectations through honest talk.")
    if not lines:
        lines.append(
            "Values and life-goal fit looks mixed — shared priorities and compromise habits matter most."
        )
    return lines[:5]


def _synthesize_gun_milan(kundli: dict, sig) -> list[str]:
    k = dict(kundli or {})
    k.setdefault("name", "You")
    r = KundliReader(k)
    lines: list[str] = []

    occ7 = r.occupants(7)
    if "Venus" in occ7 or "Jupiter" in occ7:
        lines.append("7th house grace markers — traditional match factors lean supportive.")
    elif "Saturn" in occ7 or "Mars" in occ7:
        lines.append("7th house heat/delay markers — gun milan needs temperament and duty balance.")

    ven = r.planet("Venus") or {}
    if ven.get("house") in (1, 4, 7, 9, 11):
        lines.append(
            f"Venus strength in house {ven.get('house')} — affection and harmony support match score"
            f"{lordship_clause(r, 'Venus')}."
        )
    for key in ("Navamsa Venus weak", "Navamsa Moon debilitated", "7th lord debilitated"):
        picked = pick_notes(sig, [key], limit=1)
        if picked:
            lines.append(f"Match caution: {picked[0]} — D9/D1 care needed in traditional scoring.")
    if not lines:
        lines.append("Gun milan pattern: moderate — temperament and Moon/Venus tone decide daily fit.")
    return lines[:5]


def _compat_level(sig, friction: list[str]) -> str:
    w = int(sig.affliction_weight or 0)
    n = len(friction)
    score = max(0, min(100, 100 - int(round(w * 1.2))))
    band = risk_band_high_is_good(score)

    if band == "low" and n <= 1:
        return "strong" if getattr(sig, "reconnection_yoga", False) else "supportive"
    if band == "low":
        return "supportive"
    if n >= 3 or w >= 34 or band == "very high":
        return "strained"
    if n >= 2 or w >= 22 or band == "high":
        return "mixed"
    if n >= 1 or w >= 14 or getattr(sig, "saturn_on_7th", False) or band == "medium":
        return "moderate"
    return "supportive"


def _compat_verdict(intent: str, level: str) -> str:
    labels = {
        "emotional_compatibility": "Emotional compatibility",
        "mental_compatibility": "Mental compatibility",
        "intellectual_compatibility": "Intellectual compatibility",
        "values_goals_compatibility": "Values and life-goals fit",
        "gun_milan": "Gun milan / traditional match",
        "general_compatibility": "Overall compatibility",
    }
    topic = labels.get(intent, "Compatibility")
    tone = {
        "strong": f"{topic}: strong supportive bond — caring depth and sync are present",
        "supportive": f"{topic}: supportive — bond can grow with steady care and respect",
        "moderate": f"{topic}: moderate — mel hai par patience aur clear talk chahiye",
        "mixed": f"{topic}: mixed — alignment hai lekin friction points ko address karna padega",
        "strained": f"{topic}: strained patterns — effort, boundaries aur honest dialogue zaroori",
    }
    return tone.get(level, f"{topic}: mixed — communication and respect matter")


def run_compatibility(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    try:
        from ask_mr.v2 import v2_enabled_for
        from ask_mr.v2.adapter import v2_to_engine_result
        from ask_mr.v2.engines.compatibility import run_compatibility_v2

        if v2_enabled_for("compatibility"):
            out = run_compatibility_v2(kundli, question, wants_explain=wants_explain)
            return v2_to_engine_result(out)
    except Exception:
        pass

    sig = build_person_signals(kundli)
    intent = _compatibility_intent(question)
    friction = pick_notes(sig, _FRICTION_NOTE_KEYS, limit=4)
    level = _compat_level(sig, friction)
    verdict = _compat_verdict(intent, level)

    if intent == "emotional_compatibility":
        evidence = _synthesize_emotional_compatibility(kundli, sig)
    elif intent == "mental_compatibility":
        evidence = _synthesize_mental_compatibility(kundli, sig)
    elif intent == "intellectual_compatibility":
        evidence = _synthesize_intellectual_compatibility(kundli, sig)
    elif intent == "values_goals_compatibility":
        evidence = _synthesize_values_goals_compatibility(kundli, sig)
    elif intent == "gun_milan":
        evidence = _synthesize_gun_milan(kundli, sig)
    else:
        evidence = _synthesize_emotional_compatibility(kundli, sig)
        for line in _synthesize_mental_compatibility(kundli, sig)[:2]:
            if line not in evidence and len(evidence) < 5:
                evidence.append(line)

    support = pick_notes(sig, _POSITIVE_NOTE_KEYS, limit=2)
    if support and getattr(sig, "reconnection_yoga", False):
        evidence.insert(0, support[0])
    elif support and intent == "emotional_compatibility" and not any("5th lord" in e for e in evidence):
        evidence.insert(0, support[0])

    if friction and len(evidence) < 6:
        for line in friction[:2]:
            tag = f"Friction: {line}"
            if tag not in evidence:
                evidence.append(tag)

    if not evidence:
        evidence = ["Compatibility pattern looks balanced — daily respect and talk build the match."]

    summary = [
        "Answer compatibility with confident pattern voice — state what the chart shows for THIS angle.",
        "NO shayad/ho sakta hai — give a clear stance on match quality.",
        "If mixed: name one friction point + one repair habit (talk, patience, shared routine).",
    ]
    if intent == "gun_milan":
        summary[0] = "Answer gun milan / match quality — temperament + Moon/Venus tone; no fake point score."

    return EngineResult(
        archetype="compatibility",
        verdict=verdict,
        confidence="medium",
        word_budget=90 if wants_explain else 60,
        answer_plan="2–3 short sentences: compatibility level → 1–2 chart reasons → one practical habit.",
        summary=summary,
        evidence=evidence,
        ignore=[
            "timing dates/windows",
            "spouse profession",
            "breakup/divorce unless asked",
            "manglik detail unless asked",
        ],
        checks={
            "slice_type": "mr_engine_v1",
            "archetype": "compatibility",
            "question_intent": intent,
            "compat_level": level,
            "affliction_weight": int(sig.affliction_weight or 0),
        },
    )
