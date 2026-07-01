from __future__ import annotations

from ..types import EngineResult
from ._luck_base import fortune_snapshot, luck_score, lucky_trait_hints, reader


def _luck_result(
    *,
    archetype: str,
    kundli: dict,
    wants_explain: bool,
    focus: str,
    verdict_high: str,
    verdict_mid: str,
    verdict_low: str,
    summary: list[str],
    ignore: list[str] | None = None,
) -> EngineResult:
    score, label = luck_score(kundli)
    evidence = fortune_snapshot(kundli, focus=focus)
    if score >= 72:
        verdict, confidence = verdict_high, "high"
    elif score >= 55:
        verdict, confidence = verdict_mid, "medium"
    else:
        verdict, confidence = verdict_low, "medium"
    return EngineResult(
        archetype=archetype,
        verdict=verdict,
        confidence=confidence,
        word_budget=95 if wants_explain else 80,
        answer_plan=f"Answer {archetype.replace('_', ' ')} from 9H/5H/11H + Jupiter evidence.",
        summary=summary,
        evidence=evidence,
        ignore=ignore or ["exact dates", "guaranteed lottery win", "fatalism"],
        checks={
            "slice_type": "luck_engine_v1",
            "archetype": archetype,
            "luck_score": score,
            "luck_label": label,
            "open_chart_qa": True,
        },
    )


def run_overall_luck(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    return _luck_result(
        archetype="overall_luck",
        kundli=kundli,
        wants_explain=wants_explain,
        focus="overall",
        verdict_high="Overall bhagya supportive — grace + gains axis strong, effort ke saath results milte hain",
        verdict_mid="Overall luck mixed — kabhi strong support, kabhi delay; discipline + right timing matter",
        verdict_low="Overall luck me effort zyada chahiye — chart patience + remedies suggest karta hai",
        summary=[
            "QUESTION FOCUS: general luck/bhagya/kismat quality — NOT kab/when.",
            "Use 9H + Jupiter + 5H/11H only.",
        ],
    )


def run_luck_strength(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    return _luck_result(
        archetype="luck_strength",
        kundli=kundli,
        wants_explain=wants_explain,
        focus="overall",
        verdict_high="Luck/bhagya chart me strong side pe hai — favourable houses + Guru support",
        verdict_mid="Luck strength medium — chart mixed; right dasha + effort se improve hota hai",
        verdict_low="Luck strength weak tone — chart discipline/remedies + patience suggest karta hai",
        summary=["QUESTION FOCUS: luck strong/weak — qualitative only."],
    )


def run_career_luck(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    return _luck_result(
        archetype="career_luck",
        kundli=kundli,
        wants_explain=wants_explain,
        focus="career",
        verdict_high="Career me luck supportive — karma axis + bhagya dono help karte hain",
        verdict_mid="Career luck mixed — mehnat ke baad hi breakthrough; chart delay bhi dikhata hai",
        verdict_low="Career luck me extra effort — chart patience + skill building pe focus",
        summary=["QUESTION FOCUS: career/job luck — NOT promotion timing."],
        ignore=["exact promotion date", "guaranteed job"],
    )


def run_love_luck(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    return _luck_result(
        archetype="love_luck",
        kundli=kundli,
        wants_explain=wants_explain,
        focus="love",
        verdict_high="Love/marriage luck supportive — 7H + Venus + bhagya axis favour",
        verdict_mid="Love luck mixed — rishta possible hai par timing/effort dono matter",
        verdict_low="Love luck me patience — chart delay tone; right dasha + clarity zaroori",
        summary=["QUESTION FOCUS: love/shaadi luck — NOT marriage date."],
        ignore=["exact marriage date", "partner name"],
    )


def run_money_luck(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    return _luck_result(
        archetype="money_luck",
        kundli=kundli,
        wants_explain=wants_explain,
        focus="money",
        verdict_high="Paisa/dhan luck supportive — 2H/11H + bhagya gains axis active",
        verdict_mid="Money luck mixed — income ho sakti hai par leak/delay bhi chart me",
        verdict_low="Money luck me discipline — chart saving/control pe zor deta hai",
        summary=["QUESTION FOCUS: wealth/lottery/money luck tone — NOT exact amount."],
        ignore=["lottery number", "exact amount", "stock tips"],
    )


def run_lucky_traits(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    score, label = luck_score(kundli)
    evidence = fortune_snapshot(kundli, focus="overall")
    evidence.extend(lucky_trait_hints(kundli))
    r = reader(kundli)
    lord9 = r.house_lord(9)
    return EngineResult(
        archetype="lucky_traits",
        verdict=f"Chart-based lucky hints — 9L {lord9 or 'Guru'} + Jupiter axis se day/colour/stone direction",
        confidence="medium",
        word_budget=85 if wants_explain else 70,
        answer_plan="Give practical lucky day/colour from 9L + Jupiter — no fabricated lottery numbers.",
        summary=["QUESTION FOCUS: lucky number/colour/day from chart — keep modest."],
        evidence=evidence[:8],
        ignore=["guaranteed lottery", "exact lucky number claims"],
        checks={"slice_type": "luck_engine_v1", "archetype": "lucky_traits", "luck_score": score},
    )


def run_general_luck(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    return run_overall_luck(kundli, question, wants_explain=wants_explain)
