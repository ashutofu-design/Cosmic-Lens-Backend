from __future__ import annotations

from vedic.love_reality.scoring_core import KundliReader, SIGNS

from ._person_signals import build_person_signals, pick_notes
from ..types import EngineResult


def run_second_marriage(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    k = dict(kundli or {})
    k.setdefault("name", "You")
    r = KundliReader(k)
    sig = build_person_signals(k)

    asc_i = r.asc_index()
    sign7 = SIGNS[(asc_i + 6) % 12] if isinstance(asc_i, int) else ""
    dual_7th = sign7 in ("Gemini", "Virgo", "Sagittarius", "Pisces")

    drivers = 0
    if dual_7th:
        drivers += 1
    if sig.separation_yoga:
        drivers += 1
    if sig.seventh_lord_dusthana or sig.seventh_lord_debil:
        drivers += 1
    if sig.rahu_on_7th_axis or sig.mars_on_7th:
        drivers += 1

    if drivers >= 3:
        level = "visible — second union theme can repeat after lessons"
    elif drivers >= 2:
        level = "mixed — one strong bond possible, but chart shows repeat-lesson pattern"
    else:
        level = "moderate — primary focus stays on one committed path"

    verdict = f"Second marriage / repeat union pattern: {level}"

    evidence: list[str] = []
    if dual_7th:
        evidence.append(f"7th house sign {sign7} is dual — chart can show more than one serious bond arc.")
    evidence.extend(
        pick_notes(
            sig,
            [
                "Saturn on 7th",
                "Mars on 7th",
                "nodes on 7th",
                "7th lord in dusthana",
                "7th lord debilitated",
                "separation",
            ],
            limit=5,
        )
    )
    if not evidence:
        evidence = ["No strong repeat-marriage driver; one stable union path looks normal."]

    return EngineResult(
        archetype="second_marriage",
        verdict=verdict,
        confidence="medium",
        word_budget=85 if wants_explain else 60,
        answer_plan="2–3 sentences: repeat-union pattern → 1–2 reasons → mature choice line (no doom).",
        summary=[
            "Answer second marriage / remarriage pattern directly — confident voice.",
            "NO shayad/ho sakta hai/lagta hai. Avoid fatalism; focus on maturity and clarity.",
        ],
        evidence=evidence[:6],
        ignore=["timing dates/windows", "exact year of second marriage"],
        checks={
            "slice_type": "mr_engine_v1",
            "archetype": "second_marriage",
            "dual_7th_sign": dual_7th,
            "driver_count": drivers,
        },
    )
