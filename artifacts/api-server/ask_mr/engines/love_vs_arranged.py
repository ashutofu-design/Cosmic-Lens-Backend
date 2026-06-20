from __future__ import annotations

from vedic.love_reality.scoring_core import KundliReader

from ..types import EngineResult


def _tilt(reader: KundliReader) -> tuple[str, list[str]]:
    """Return (tilt, evidence_lines)."""
    e: list[str] = []

    rahu_h = (reader.planet("Rahu") or {}).get("house")
    jup_h = (reader.planet("Jupiter") or {}).get("house")
    sat_h = (reader.planet("Saturn") or {}).get("house")

    love = 0
    arranged = 0

    if rahu_h in (5, 7, 11):
        love += 2
        e.append("Rahu on love/partnership axis → unconventional pull / self-choice tendency.")

    if jup_h in (2, 7, 9) or sat_h in (2, 7, 9):
        arranged += 2
        e.append("Jupiter/Saturn tied to family/dharma axis → tradition/structure favors arranged path.")

    # 5L ↔ 7L bridge (simple): if 5L aspects 7L or vice-versa by drishti to the planet.
    lord5 = reader.house_lord(5)
    lord7 = reader.house_lord(7)
    asp_7l = set(reader.aspects_planet(lord7))
    asp_5l = set(reader.aspects_planet(lord5))
    if lord5 in asp_7l or lord7 in asp_5l:
        love += 1
        e.append("5th lord–7th lord linkage → love-to-marriage conversion support.")

    # Venus-Mars share house → strong attraction (can trigger love tilt)
    if reader.share_house("Venus", "Mars"):
        love += 1
        e.append("Venus–Mars linkage → strong attraction/passion, self-driven bonding.")

    if love > arranged:
        return "love_marriage_tilt", e
    if arranged > love:
        return "arranged_marriage_tilt", e
    return "mixed_neutral", e


def run_love_vs_arranged(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    k = dict(kundli or {})
    k.setdefault("name", "You")
    r = KundliReader(k)

    tilt, ev = _tilt(r)
    verdict = {
        "love_marriage_tilt": "Tilt: love-marriage side stronger",
        "arranged_marriage_tilt": "Tilt: arranged-marriage side stronger",
        "mixed_neutral": "Tilt: mixed / neutral (both possible)",
    }.get(tilt, f"Tilt: {tilt}")

    # Keep evidence compact and deterministic.
    evidence = ev[:6] if ev else ["No strong tilt driver triggered; outcome depends on choices + family context."]

    return EngineResult(
        archetype="love_vs_arranged",
        verdict=verdict,
        confidence="medium" if tilt == "mixed_neutral" else "high",
        word_budget=85 if wants_explain else 55,
        answer_plan="One clear tilt → 1–2 reasons → soft practical note (communication/family).",
        summary=[
            "Do not guarantee outcome; present as tendency.",
        ],
        evidence=evidence,
        ignore=[
            "timing dates/windows",
            "spouse profession",
            "manglik (unless asked)",
            "breakup risk (unless asked)",
        ],
        checks={
            "slice_type": "mr_engine_v1",
            "archetype": "love_vs_arranged",
            "tilt": tilt,
        },
    )

