from __future__ import annotations

from ask_gaps_shared import clamp_score, gap_result, house_axis, planet_line, reader
from .spiritual_registry import detect_spiritual_archetype


def _score(kundli: dict, archetype: str) -> int:
    r = reader(kundli)
    score = 50
    jup = r.planet("Jupiter") or {}
    ketu = r.planet("Ketu") or {}
    moon = r.planet("Moon") or {}
    if archetype in ("guru_yog", "deity_faith", "karma_past_life", "spiritual_path", "general_spiritual"):
        if jup.get("house") and int(jup["house"]) in (1, 4, 5, 9, 10, 12):
            score += 10
    if archetype in ("intuition_occult", "karma_past_life", "moksha_liberation", "spiritual_path", "general_spiritual"):
        if ketu.get("house") and int(ketu["house"]) in (8, 9, 12):
            score += 8
    if archetype in ("meditation_peace", "moksha_liberation", "spiritual_path", "general_spiritual"):
        if moon.get("house") and int(moon["house"]) in (4, 8, 9, 12):
            score += 6
    focus_houses = {
        "intuition_occult": (8,),
        "guru_yog": (9,),
        "deity_faith": (9, 5),
        "meditation_peace": (12,),
        "karma_past_life": (8, 9),
        "moksha_liberation": (12, 8),
        "spiritual_path": (8, 9, 12),
        "general_spiritual": (8, 9, 12),
    }.get(archetype, (8, 9, 12))
    for h in focus_houses:
        for occ in r.occupants(h) or []:
            if occ in {"Jupiter", "Ketu", "Moon"}:
                score += 5
    return clamp_score(score)


def _evidence(kundli: dict, archetype: str) -> list[str]:
    r = reader(kundli)
    lines: list[str] = []
    if archetype == "intuition_occult":
        lines.extend([
            house_axis(r, 8, "Occult/intuition axis (8th house)"),
            planet_line(r, "Ketu", "moksha/occult karaka"),
            planet_line(r, "Rahu", "hidden-knowledge amplifier"),
        ])
    elif archetype == "guru_yog":
        lines.extend([
            house_axis(r, 9, "Guru/dharma/blessings axis (9th house)"),
            planet_line(r, "Jupiter", "guru/dharma karaka"),
        ])
    elif archetype == "deity_faith":
        lines.extend([
            house_axis(r, 9, "Bhakti/dharma axis (9th house)"),
            house_axis(r, 5, "Devotion/mantra axis (5th house)"),
            planet_line(r, "Jupiter", "faith/blessings karaka"),
        ])
    elif archetype == "meditation_peace":
        lines.extend([
            house_axis(r, 12, "Moksha/meditation axis (12th house)"),
            planet_line(r, "Moon", "mind/peace karaka"),
        ])
    elif archetype == "karma_past_life":
        lines.extend([
            house_axis(r, 8, "Karma/transformation axis (8th house)"),
            house_axis(r, 9, "Purva-punya/dharma axis (9th house)"),
            planet_line(r, "Ketu", "past-life/moksha karaka"),
        ])
    elif archetype == "moksha_liberation":
        lines.extend([
            house_axis(r, 12, "Moksha/letting-go axis (12th house)"),
            house_axis(r, 8, "Transformation axis (8th house)"),
            planet_line(r, "Ketu", "detachment karaka"),
        ])
    elif archetype == "spiritual_path":
        lines.extend([
            house_axis(r, 9, "Dharma/guru axis (9th house)"),
            house_axis(r, 12, "Moksha axis (12th house)"),
            house_axis(r, 8, "Inner-change axis (8th house)"),
        ])
    else:
        lines.extend([
            house_axis(r, 9, "Dharma/guru/blessings axis (9th house)"),
            house_axis(r, 12, "Moksha/letting-go axis (12th house)"),
            house_axis(r, 8, "Occult/transformation axis (8th house)"),
            planet_line(r, "Ketu", "moksha/detachment karaka"),
            planet_line(r, "Jupiter", "guru/dharma karaka"),
        ])
    lines.append(f"Spiritual-inclination index ({archetype}): {_score(kundli, archetype)}/100.")
    return lines[:8]


def run_spiritual_static_engine(
    kundli: dict,
    question: str,
    *,
    wants_explain: bool = False,
    archetype: str | None = None,
) -> "EngineResult":
    arch = (archetype or detect_spiritual_archetype(question)).strip().lower()
    sc = _score(kundli, arch)
    verdicts = {
        "intuition_occult": (
            "Intuition/occult axis strong — 8H + Ketu favour hidden knowledge & purnanumaan",
            "Intuition mixed — practice + ethics ke saath gradual sharpen hogi",
            "Occult/intuition abhi dheere — pehle basics, phir deep study",
        ),
        "karma_past_life": (
            "Karmic/purva-punya axis active — 8H/9H past patterns resolve hone ka yog",
            "Karma themes mixed — patience + dharma se balance aayega",
            "Karmic load heavy abhi — steady sadhana + seva se relief",
        ),
        "guru_yog": (
            "Guru-yog strong — 9H + Jupiter favour sahi margdarshan",
            "Guru connection mixed — readiness badhne par sahi guide dikhega",
            "Guru-yog abhi kamzor — pehle nishtha + self-study",
        ),
        "meditation_peace": (
            "Meditation/peace axis favourable — 12H + Moon inner shanti dete hain",
            "Mental peace mixed — routine dhyan se dheere sudhar",
            "Shanti abhi challenge — grounding + steady practice zaroori",
        ),
        "deity_faith": (
            "Bhakti/deity axis strong — 9H/5H faith & blessings favour karte hain",
            "Bhakti mixed — nishtha badhne par connection gehra hoga",
            "Bhakti abhi kamzor — simple mantra/seva se start karo",
        ),
        "moksha_liberation": (
            "Moksha/vairagya themes strong — 12H + Ketu detachment support",
            "Moksha interest mixed — worldly duty + inner sadhana dono chahiye",
            "Moksha abhi door — patience; forced sanyas mat socho",
        ),
        "spiritual_path": (
            "Spiritual path strong — awakening/transformation ke yog active",
            "Spiritual path mixed — phases of seeking + grounding dono",
            "Spiritual path abhi early — steady sadhana, jaldi mat jao",
        ),
    }
    v_high, v_mid, v_low = verdicts.get(
        arch,
        (
            "Spiritual path strong — 9H/12H + Jupiter/Ketu favour dharma & inner growth",
            "Spiritual interest mixed — chart phases of seeking + worldly duty both",
            "Spiritual path needs patience — pehle grounding, phir steady sadhana",
        ),
    )
    return gap_result(
        archetype=arch,
        slice_type="spiritual_engine_v1",
        kundli=kundli,
        score=sc,
        evidence=_evidence(kundli, arch),
        verdict_high=v_high,
        verdict_mid=v_mid,
        verdict_low=v_low,
        summary=[f"QUESTION FOCUS: {arch.replace('_', ' ')} — NOT exact deeksha/date guarantee."],
        answer_plan="Archetype-wise 8H/9H/12H + Jupiter/Ketu/Moon only.",
        wants_explain=wants_explain,
        score_key="spiritual_score",
    )
