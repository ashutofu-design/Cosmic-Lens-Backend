from __future__ import annotations

from ..types import EngineResult

_VERDICT_LABELS = {
    "clear_love": "Clear love-marriage yog (classical rules)",
    "leaning_love": "Love-marriage side stronger (leaning)",
    "clear_arrange": "Clear arrange-marriage yog (classical rules)",
    "leaning_arrange": "Arranged-marriage side stronger (leaning)",
    "inconclusive": "Mixed / neutral (both possible)",
}


def _confidence_label(verdict_public: str, numeric: float) -> str:
    if verdict_public in ("clear_love", "clear_arrange"):
        return "high"
    if verdict_public in ("leaning_love", "leaning_arrange"):
        return "medium"
    if numeric >= 0.75:
        return "medium"
    return "low"


def run_love_vs_arranged(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    """Classical love-vs-arrange tilt via Phase 5.5 rules (D1 + D9)."""
    # Lazy import — reuses production-tested rules; avoids circular import at load time.
    from openai_helper import _phase55_compute_love_vs_arrange

    computed = _phase55_compute_love_vs_arrange(kundli)
    if not computed:
        return EngineResult(
            archetype="love_vs_arranged",
            verdict="Tilt: inconclusive (chart data incomplete)",
            confidence="low",
            word_budget=55,
            answer_plan="Say chart data is insufficient; do not invent placements.",
            summary=["Do not guess love vs arrange without D1 planets."],
            evidence=["Required D1 planet data missing for classical love/arrange rules."],
            ignore=[
                "timing dates/windows",
                "spouse profession",
                "manglik detail (unless asked)",
            ],
            checks={"slice_type": "mr_engine_v1", "archetype": "love_vs_arranged", "error": "no_data"},
        )

    verdict_public = str(computed.get("verdict_public") or "inconclusive")
    headline = (
        computed.get("verdict_text_public")
        or computed.get("verdict_text_hi")
        or _VERDICT_LABELS.get(verdict_public, verdict_public)
    )

    evidence: list[str] = []
    for reason in computed.get("reasons_love") or []:
        evidence.append(f"Love indicator: {reason}")
    for reason in computed.get("reasons_arrange") or []:
        evidence.append(f"Arrange indicator: {reason}")

    if not evidence:
        evidence.append(
            "No strong classical driver triggered; outcome depends on choices + family context."
        )

    love_score = int(computed.get("love_score") or 0)
    arrange_score = int(computed.get("arrange_score") or 0)
    numeric_conf = float(computed.get("confidence") or 0.55)

    summary = [
        f"Classical scores — love: {love_score}, arrange: {arrange_score}.",
        "Present as tendency, not guarantee.",
    ]
    if wants_explain:
        summary.append("User wants explanation — cite 3–5 evidence lines in plain Hinglish.")

    return EngineResult(
        archetype="love_vs_arranged",
        verdict=headline,
        confidence=_confidence_label(verdict_public, numeric_conf),
        word_budget=120 if wants_explain else 55,
        answer_plan=(
            "State headline tilt → 2–4 classical reasons → soft practical note."
            if wants_explain
            else "One clear tilt line → 1–2 reasons → soft practical note."
        ),
        summary=summary,
        evidence=evidence[:10],
        ignore=[
            "timing dates/windows",
            "spouse profession",
            "manglik detail (unless asked)",
            "breakup risk (unless asked)",
        ],
        checks={
            "slice_type": "mr_engine_v1",
            "archetype": "love_vs_arranged",
            "verdict_public": verdict_public,
            "verdict_internal": computed.get("verdict"),
            "love_score": love_score,
            "arrange_score": arrange_score,
            "confidence_ratio": computed.get("confidence_ratio"),
            "confidence_numeric": numeric_conf,
        },
    )
