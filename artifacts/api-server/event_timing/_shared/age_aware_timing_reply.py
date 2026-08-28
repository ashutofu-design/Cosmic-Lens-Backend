"""User-facing age-first lines for timing answers.

Dasha windows can be near-term (6 months / 1 year) even for a child chart.
This module forces the reply to acknowledge current age and reframe young
users as prepare/delay — not "job/shaadi abhi 6 mahine mein".
"""
from __future__ import annotations

from typing import Any, Optional

from event_timing._shared.practical_manifestation_filter import (
    DOMAIN_MIN_ELIGIBLE_AGE,
    min_eligible_age,
    resolve_timing_age,
)

_DOMAIN_LABEL = {
    "marriage": {"hn": "shaadi", "hi": "शादी", "en": "marriage"},
    "love": {"hn": "love / partner", "hi": "प्रेम / साथी", "en": "love / partner"},
    "career": {"hn": "job / career", "hi": "नौकरी / करियर", "en": "job / career"},
    "finance": {"hn": "paisa / finance", "hi": "पैसा / वित्त", "en": "money / finance"},
    "property": {"hn": "property / ghar", "hi": "प्रॉपर्टी / घर", "en": "property / home"},
    "education": {"hn": "padhai", "hi": "पढ़ाई", "en": "studies"},
    "children": {"hn": "santaan", "hi": "संतान", "en": "children"},
    "travel": {"hn": "travel", "hi": "यात्रा", "en": "travel"},
    "vehicle": {"hn": "vehicle", "hi": "वाहन", "en": "vehicle"},
}


def _lang(code: str) -> str:
    c = (code or "hn").strip().lower()
    if c in ("hi", "hindi", "hin", "devanagari"):
        return "hi"
    if c in ("en", "english", "eng"):
        return "en"
    return "hn"


def _label(domain: str, lang: str) -> str:
    d = (domain or "universal").strip().lower()
    row = _DOMAIN_LABEL.get(d) or {
        "hn": d or "event",
        "hi": d or "घटना",
        "en": d or "event",
    }
    return row.get(lang) or row["hn"]


def resolve_user_age_for_timing(
    *,
    question: str = "",
    birth: Any = None,
    kundli: Any = None,
    user_age: Optional[int] = None,
) -> Optional[int]:
    if isinstance(user_age, int) and user_age >= 0:
        return user_age
    return resolve_timing_age(question, birth, kundli)


def age_aware_timing_opener(
    domain: str,
    *,
    user_age: Optional[int],
    window: str = "",
    lang: str = "hn",
    question: str = "",
    predicted_age: Optional[int] = None,
) -> str:
    """One mandatory opener: current age + young = prepare, not near-term action."""
    code = _lang(lang)
    ua = user_age if isinstance(user_age, int) and user_age >= 0 else None
    w = (window or "").strip()
    event = _label(domain, code)
    min_age = min_eligible_age(domain, question)
    young = bool(ua is not None and ua < min_age)
    pred = predicted_age if isinstance(predicted_age, int) and predicted_age > 0 else None

    if ua is None:
        return ""

    if code == "hi":
        if young:
            later = f" लगभग {pred} साल की उम्र" if pred else ""
            win = f" (चार्ट संकेत: {w})" if w else ""
            return (
                f"आप अभी सिर्फ {ua} साल के हैं — अभी {event} का समय नहीं है। "
                f"यह सवाल सही है, पर जवाब delay/prepare वाला है"
                f"{later}{win}।"
            )
        if pred and w:
            return (
                f"आप अभी {ua} साल के हैं। {event} लगभग {pred} साल की उम्र के आसपास "
                f"— {w} के बीच दिखता है।"
            )
        if w:
            return f"आप अभी {ua} साल के हैं। {event} का समय {w} के बीच दिखता है।"
        return f"आप अभी {ua} साल के हैं।"

    if code == "en":
        if young:
            later = f" around age {pred}" if pred else ""
            win = f" (chart signals: {w})" if w else ""
            return (
                f"You're only {ua} right now — this is not yet time for {event}. "
                f"The question is valid, but the answer is delay/prepare"
                f"{later}{win}."
            )
        if pred and w:
            return (
                f"You're about {ua} now. {event.capitalize()} looks around age {pred} "
                f"— between {w}."
            )
        if w:
            return f"You're about {ua} now. {event.capitalize()} timing looks between {w}."
        return f"You're about {ua} now."

    # Hinglish
    if young:
        later = f" lagbhag age {pred}" if pred else ""
        win = f" (chart signal: {w})" if w else ""
        return (
            f"Aap abhi sirf {ua} saal ke ho — abhi {event} ka time nahi hai. "
            f"Sawal sahi hai, lekin jawab delay/prepare wala hai"
            f"{later}{win}."
        )
    if pred and w:
        return (
            f"Aap abhi {ua} saal ke ho. {event.capitalize()} lagbhag age {pred} ke around "
            f"— {w} ke beech dikhta hai."
        )
    if w:
        return f"Aap abhi {ua} saal ke ho. {event.capitalize()} ka time {w} ke beech dikhta hai."
    return f"Aap abhi {ua} saal ke ho."


def lock_lines_for_prompt(
    domain: str,
    *,
    user_age: Optional[int],
    window: str = "",
    question: str = "",
    predicted_age: Optional[int] = None,
) -> str:
    """HARD lock for LLM narrator — must open with age; young ≠ near-term action."""
    ua = user_age
    min_age = min_eligible_age(domain, question)
    young = bool(ua is not None and ua < min_age)
    floor = DOMAIN_MIN_ELIGIBLE_AGE.get((domain or "").lower(), 16)
    lines = [
        "=== AGE LOCK (MANDATORY — first sentence of user reply) ===",
        f"user_age_now={ua if ua is not None else 'UNKNOWN'}",
        f"domain={domain} practical_min_age={min_age} (catalog_floor≈{floor})",
        f"too_young_now={young}",
    ]
    if young:
        lines.append(
            "RULE: User is a child/teen relative to this event. "
            "DO NOT say job/shaadi/event '6 mahine / 1 saal mein hoga' as if actionable now. "
            "Say: abhi age chhoti hai → delay/prepare; dasha window = future signal only."
        )
    else:
        lines.append(
            "RULE: Open with current age, then give the window. "
            "Never hide age when answering timing."
        )
    opener = age_aware_timing_opener(
        domain,
        user_age=ua,
        window=window,
        lang="hn",
        question=question,
        predicted_age=predicted_age,
    )
    if opener:
        lines.append(f"SERVE_OPENER_VERBATIM (or same meaning): {opener}")
    return "\n".join(lines)


def prepend_opener_to_answer(
    text: str,
    domain: str,
    *,
    user_age: Optional[int],
    window: str = "",
    lang: str = "hn",
    question: str = "",
    predicted_age: Optional[int] = None,
) -> str:
    """Ensure final user text starts with age-aware opener."""
    body = (text or "").strip()
    opener = age_aware_timing_opener(
        domain,
        user_age=user_age,
        window=window,
        lang=lang,
        question=question,
        predicted_age=predicted_age,
    )
    if not opener:
        return body
    # Already age-aware
    if user_age is not None and (
        f"{user_age} saal" in body.lower()
        or f"{user_age} साल" in body
        or f"about {user_age}" in body.lower()
        or f"only {user_age}" in body.lower()
        or f"सिर्फ {user_age}" in body
    ):
        return body
    if not body:
        return opener
    return f"{opener} {body}"
