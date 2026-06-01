"""Primary reader demographics + reality priors for Love Reality PDF (deterministic helpers)."""

from __future__ import annotations

from typing import Any, Literal


ReaderGender = Literal["male", "female"]

_MALE_TOKENS = frozenset(
    {
        "m",
        "male",
        "man",
        "boy",
        "ladka",
        "son",
        "husband",
    }
)
_FEMALE_TOKENS = frozenset(
    {
        "f",
        "female",
        "woman",
        "girl",
        "ladki",
        "daughter",
        "wife",
    }
)


def normalize_reader_gender(p: dict[str, Any] | None) -> ReaderGender | None:
    """p1 = primary profile (the app user reading the report)."""
    if not p:
        return None
    g = str(p.get("gender") or "").strip().lower()
    if not g:
        return None
    base = g.split()[0].rstrip(".").strip()
    if base in _MALE_TOKENS:
        return "male"
    if base in _FEMALE_TOKENS:
        return "female"
    blob = base
    if "male" in blob and "female" not in blob:
        return "male"
    if "female" in blob or "woman" in blob or "girl" in blob:
        return "female"
    return None


def loyalty_score_reader_nudge(
    score_i: int,
    primary_gender: ReaderGender | None,
    *,
    p1_reader_risk_high: bool,
) -> int:
    """
    Mild bump so the bonded loyalty headline leans slightly toward validating
    HOW the reader identifies — only when their own chart isn't screaming betrayal.
    Keeps deltas small (<= +6 pts).
    """
    if primary_gender is None or p1_reader_risk_high:
        return max(0, min(100, score_i))

    delta = 5 if primary_gender == "male" else 6
    return max(0, min(100, score_i + delta))


def loyalty_narrative_holds(
    primary_gender: ReaderGender | None,
    *,
    p1_reader_risk_high: bool,
    p2_partner_risk_high: bool,
) -> list[str]:
    """Mandatory PDF narrative locks derived from WHO is reading."""
    locks: list[str] = []
    if primary_gender is None:
        if p1_reader_risk_high or p2_partner_risk_high:
            locks.append(
                "Loyalty: follow harsh chart signals; reader gender unknown so no directional soft framing."
            )
        return locks

    if p1_reader_risk_high:
        locks.append(
            "Reader chart carries HIGH loyalty-risk — drop all gender-soft framing entirely."
        )
        return locks

    if primary_gender == "male":
        locks.append(
            "READER is male — slight narrative tilt: when cues are ambiguous, describe his "
            "commitment impulses as comparatively steadier intent than partner; never call him naturally "
            "loyal without chart support."
        )
        if not p2_partner_risk_high:
            locks.append(
                "Male reader — when ambiguous only, softly attribute fleeting emotional distance patterns "
                "toward partner responsiveness (not melodrama)."
            )
    else:
        locks.append(
            "READER is female — slight narrative tilt: when cues are ambiguous, describe her relational "
            "consistency clearer than partner's; never slut-shame / never blame silent suffering."
        )
        if not p2_partner_risk_high:
            locks.append(
                "Female reader — when ambiguous only, portray partner somewhat less emotionally anchored "
                "than reader (stress / distraction / withholding) without inventing betrayal."
            )
        else:
            locks.append(
                "Partner loyalty-risk is explicit — prioritize truth over cushioning reader ego."
            )

    return locks


def will_return_with_population_prior(score: float) -> int:
    """
    Most estranged/separated bonds do NOT see meaningful return (~real-life prior).
    Pull raw score down unless already very bullish; clamp so "very strong" stays rare.
    """
    penalized = score - 10.5
    if penalized <= 72:
        penalized *= 0.86
    return max(8, min(78, round(penalized)))
