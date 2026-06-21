"""Future spouse physical appearance — 7H + Venus + D9 (deterministic evidence)."""
from __future__ import annotations

import re

from vedic.love_reality.scoring_core import KundliReader

from ..types import EngineResult
from ._chart_axes import (
    d9_spouse_appearance_lines,
    dignity_word,
    house_sign,
    planet_line,
    sign7_appearance_baseline,
)

_APPEARANCE_RX = re.compile(
    r"(?ix)\b("
    r"height|lamba[iy]?|chota|short|tall|"
    r"complexion|rang|fair|gora|gora|sanwla|"
    r"face|chehra|face\s*shape|"
    r"eyes?|aankh|"
    r"hair|baal|"
    r"body\s*type|figure|built|"
    r"dress|dressing|style|kapde|"
    r"voice|awaaz|bolne|"
    r"aura|presence|look|"
    r"attract|beautiful|handsome|good\s*looking|"
    r"physical\s*appear|shakl|surat"
    r")\b"
)

_FOCUS_RX: list[tuple[str, re.Pattern[str]]] = [
    ("height", re.compile(r"(?ix)\b(height|lamba[iy]?|chota|short|tall|kad|lambai)\b")),
    ("complexion", re.compile(r"(?ix)\b(complexion|rang|fair|gora|sanwla|skin)\b")),
    ("face", re.compile(r"(?ix)\b(face|chehra|face\s*shape|oval|round)\b")),
    ("eyes", re.compile(r"(?ix)\b(eyes?|aankh|nazar)\b")),
    ("hair", re.compile(r"(?ix)\b(hair|baal|bal)\b")),
    ("body", re.compile(r"(?ix)\b(body\s*type|figure|built|pet|mota|patla)\b")),
    ("dressing", re.compile(r"(?ix)\b(dress|dressing|style|kapde|fashion)\b")),
    ("voice", re.compile(r"(?ix)\b(voice|awaaz|bolne|tone)\b")),
    ("aura", re.compile(r"(?ix)\b(aura|presence|vibe|energy)\b")),
    ("attractiveness", re.compile(r"(?ix)\b(attract|beautiful|handsome|good\s*looking|khoobsurat)\b")),
]


def _detect_focus(q: str) -> str:
    for name, rx in _FOCUS_RX:
        if rx.search(q or ""):
            return name
    return "general"


def _height_evidence(r: KundliReader, sign7: str | None, occ7: list[str]) -> list[str]:
    sat = r.planet("Saturn") or {}
    jup = r.planet("Jupiter") or {}
    lines: list[str] = []
    tall_signs = sign7 in ("Sagittarius", "Capricorn", "Aquarius", "Leo")
    medium_signs = sign7 in ("Aries", "Libra", "Gemini", "Cancer", "Virgo", "Scorpio", "Taurus", "Pisces")
    if tall_signs or sat.get("house") in (1, 7, 10) or jup.get("house") in (1, 7):
        lines.append(
            "Height pattern: tall-to-medium tendency — Saturn/Jupiter strength or airy/fixed 7th sign "
            "supports above-average frame."
        )
    elif medium_signs:
        lines.append(
            f"Height pattern: medium build tendency — 7th sign {sign7 or 'unknown'} sets average-to-medium frame."
        )
    if "Mars" in occ7:
        lines.append("Mars in 7th — athletic compact build; height average, posture strong.")
    return lines


def _complexion_evidence(r: KundliReader, sign7: str | None) -> list[str]:
    ven = r.planet("Venus") or {}
    sun = r.planet("Sun") or {}
    moon = r.planet("Moon") or {}
    lines: list[str] = []
    ven_dw = dignity_word(r, "Venus", ven.get("sign"))
    lines.append(
        f"Complexion axis: Venus in house {ven.get('house')} sign {ven.get('sign')} ({ven_dw}) — "
        "primary skin tone / glow marker for spouse appearance."
    )
    if sun.get("house"):
        lines.append(
            f"Sun in house {sun.get('house')} sign {sun.get('sign')} — warmth/fairness tone in complexion."
        )
    if moon.get("house"):
        lines.append(
            f"Moon in house {moon.get('house')} sign {moon.get('sign')} — softness/moisture in skin expression."
        )
    if sign7 in ("Taurus", "Libra", "Cancer", "Pisces"):
        lines.append(f"7th sign {sign7} — generally pleasing/well-toned complexion tendency.")
    return lines


def _face_evidence(r: KundliReader, sign7: str | None, occ7: list[str]) -> list[str]:
    moon = r.planet("Moon") or {}
    lines = [sign7_appearance_baseline(sign7).replace("baseline", "face baseline")]
    if "Moon" in occ7 or moon.get("house") == 7:
        lines.append("Moon on partnership axis — roundish/soft expressive face shape.")
    if sign7 in ("Leo", "Aries"):
        lines.append(f"7th sign {sign7} — defined forehead/cheekbone structure in face shape.")
    if sign7 in ("Gemini", "Virgo"):
        lines.append(f"7th sign {sign7} — oval-angular refined face shape tendency.")
    return lines


def _eyes_evidence(r: KundliReader, occ7: list[str]) -> list[str]:
    moon = r.planet("Moon") or {}
    ven = r.planet("Venus") or {}
    lines: list[str] = []
    if "Moon" in occ7:
        lines.append("Moon in 7th — large expressive soft eyes, emotional gaze.")
    elif moon.get("house"):
        lines.append(
            f"Moon in house {moon.get('house')} sign {moon.get('sign')} — eye softness/expressiveness."
        )
    if ven.get("house"):
        lines.append(
            f"Venus in house {ven.get('house')} sign {ven.get('sign')} — attractive bright eye tone."
        )
    if "Saturn" in occ7:
        lines.append("Saturn in 7th — deep serious eyes, steady gaze.")
    if not lines:
        lines.append("Eye tone: read from Moon + Venus partnership influence — expressive balanced gaze.")
    return lines


def _hair_evidence(r: KundliReader, sign7: str | None, occ7: list[str]) -> list[str]:
    sat = r.planet("Saturn") or {}
    merc = r.planet("Mercury") or {}
    lines: list[str] = []
    if sat.get("house") in (1, 7, 10) or "Saturn" in occ7:
        lines.append("Saturn influence — thick/dark well-kept hair or mature hairline pattern.")
    if merc.get("house") in (1, 7, 5):
        lines.append(
            f"Mercury in house {merc.get('house')} — youthful hair texture, neat grooming tendency."
        )
    if sign7 == "Leo":
        lines.append("Leo 7th sign — full healthy hair / strong mane-like presence tendency.")
    if not lines:
        lines.append(f"Hair pattern: 7th sign {sign7 or 'unknown'} + Saturn/Mercury tone grooming style.")
    return lines


def _body_evidence(r: KundliReader, sign7: str | None, occ7: list[str]) -> list[str]:
    mars = r.planet("Mars") or {}
    ven = r.planet("Venus") or {}
    lines = [sign7_appearance_baseline(sign7).replace("baseline", "body baseline")]
    if "Mars" in occ7 or mars.get("house") == 7:
        lines.append("Mars on partnership axis — athletic/firm body type, active physique.")
    if ven.get("house") and dignity_word(r, "Venus", ven.get("sign")) == "strong":
        lines.append("Strong Venus — proportionate attractive body, graceful build.")
    if sign7 in ("Taurus", "Cancer", "Pisces"):
        lines.append(f"{sign7} 7th — softer/fuller body type tendency.")
    if sign7 in ("Virgo", "Gemini", "Aquarius"):
        lines.append(f"{sign7} 7th — slim/lean body type tendency.")
    return lines


def _dressing_evidence(r: KundliReader, sign7: str | None, occ7: list[str]) -> list[str]:
    ven = r.planet("Venus") or {}
    merc = r.planet("Mercury") or {}
    lines: list[str] = []
    lines.append(
        f"Dressing style: Venus house {ven.get('house')} sign {ven.get('sign')} — "
        "taste, colour sense and grooming for spouse look."
    )
    if merc.get("house"):
        lines.append(
            f"Mercury in house {merc.get('house')} — smart/modern dressing, detail in style choices."
        )
    if sign7 in ("Libra", "Leo", "Taurus"):
        lines.append(f"7th sign {sign7} — polished fashionable dressing tendency.")
    if sign7 in ("Capricorn", "Virgo"):
        lines.append(f"7th sign {sign7} — clean classic formal dressing tendency.")
    return lines


def _voice_evidence(r: KundliReader, occ7: list[str]) -> list[str]:
    merc = r.planet("Mercury") or {}
    moon = r.planet("Moon") or {}
    sign8 = house_sign(r, 8)
    lines: list[str] = []
    lines.append(
        f"Voice axis (2nd from spouse = 8th house sign {sign8 or 'unknown'}) — "
        "speech tone and sound quality of partner."
    )
    if merc.get("house") in (2, 3, 7, 8):
        lines.append(
            f"Mercury in house {merc.get('house')} sign {merc.get('sign')} — clear quick speech / expressive voice."
        )
    if "Moon" in occ7 or moon.get("house") == 7:
        lines.append("Moon on partnership axis — soft melodious emotional voice tone.")
    return lines


def _aura_evidence(r: KundliReader, sign7: str | None, occ7: list[str]) -> list[str]:
    sun = r.planet("Sun") or {}
    ven = r.planet("Venus") or {}
    rahu = r.planet("Rahu") or {}
    lines: list[str] = []
    if sun.get("house") in (1, 7, 5, 9):
        lines.append(
            f"Sun in house {sun.get('house')} sign {sun.get('sign')} — confident radiant aura / strong presence."
        )
    if ven.get("house") in (1, 7, 9):
        lines.append(
            f"Venus in house {ven.get('house')} — warm charming aura, people feel drawn."
        )
    if rahu.get("house") in (1, 7, 5):
        lines.append(
            f"Rahu in house {rahu.get('house')} — magnetic unusual aura, stands out in crowd."
        )
    lines.append(sign7_appearance_baseline(sign7).replace("baseline", "overall presence baseline"))
    return lines


def _attractiveness_evidence(r: KundliReader, sign7: str | None, occ7: list[str]) -> list[str]:
    ven = r.planet("Venus") or {}
    dw = dignity_word(r, "Venus", ven.get("sign"))
    lines = [
        f"Attractiveness karaka: Venus in house {ven.get('house')} sign {ven.get('sign')} ({dw}) — "
        "primary beauty/charm score for spouse.",
        sign7_appearance_baseline(sign7),
    ]
    if "Venus" in occ7:
        lines.append("Venus in 7th house — naturally attractive partner, strong physical appeal.")
    if "Jupiter" in occ7:
        lines.append("Jupiter in 7th — dignified attractive presence, graceful appeal.")
    return lines


_FOCUS_BUILDERS = {
    "height": lambda r, s7, o7, _k: _height_evidence(r, s7, o7),
    "complexion": lambda r, s7, o7, _k: _complexion_evidence(r, s7),
    "face": lambda r, s7, o7, _k: _face_evidence(r, s7, o7),
    "eyes": lambda r, s7, o7, _k: _eyes_evidence(r, o7),
    "hair": lambda r, s7, o7, _k: _hair_evidence(r, s7, o7),
    "body": lambda r, s7, o7, k: _body_evidence(r, s7, o7),
    "dressing": lambda r, s7, o7, _k: _dressing_evidence(r, s7, o7),
    "voice": lambda r, s7, o7, _k: _voice_evidence(r, o7),
    "aura": lambda r, s7, o7, _k: _aura_evidence(r, s7, o7),
    "attractiveness": lambda r, s7, o7, k: _attractiveness_evidence(r, s7, o7),
}


def run_spouse_appearance(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    k = dict(kundli or {})
    k.setdefault("name", "You")
    r = KundliReader(k)
    q = (question or "").lower()
    focus = _detect_focus(q)

    sign7 = house_sign(r, 7)
    occ7 = r.occupants(7)
    lord7 = r.house_lord(7)
    p7l = r.planet(lord7) if lord7 else None

    evidence: list[str] = [
        sign7_appearance_baseline(sign7),
        f"Planets in 7th house (direct spouse look modifier): {', '.join(occ7) if occ7 else 'none'}.",
    ]
    if lord7 and p7l:
        evidence.append(
            f"7th lord {lord7} in house {p7l.get('house')} sign {p7l.get('sign')} — "
            "refines partner's physical expression."
        )
    ven_line = planet_line(r, "Venus", role="beauty/appearance karak")
    if ven_line:
        evidence.append(ven_line)

    builder = _FOCUS_BUILDERS.get(focus)
    if builder:
        for line in builder(r, sign7, occ7, k):
            if line not in evidence:
                evidence.append(line)
    else:
        evidence.extend(_attractiveness_evidence(r, sign7, occ7)[:2])

    for line in d9_spouse_appearance_lines(k)[:3]:
        if line not in evidence:
            evidence.append(line)

    verdict = f"Spouse physical appearance ({focus}): pattern from 7th house + Venus + Navamsa D9"

    return EngineResult(
        archetype="spouse_appearance",
        verdict=verdict,
        confidence="medium",
        word_budget=110 if wants_explain else 90,
        answer_plan=(
            "Para1: direct answer to the physical trait asked → "
            "Para2: 7H/Venus/D9 evidence → Para3: one soft caveat (not exact cm/shade guarantee)."
        ),
        summary=[
            f"QUESTION FOCUS: spouse appearance — {focus}.",
            "Use ONLY appearance evidence lines — not personality or profession axes.",
            "Give descriptive pattern (medium-tall, fair-wheatish, expressive eyes) — no exact measurements.",
        ],
        evidence=evidence[:10],
        ignore=["personality traits", "profession", "timing dates/windows", "exact height in cm"],
        checks={
            "slice_type": "mr_engine_v1",
            "archetype": "spouse_appearance",
            "question_focus": focus,
            "sign7": sign7,
        },
    )
