"""Deterministic 1-line answers for simple chart lookups (lagna, rashi, nakshatra, dasha)."""
from __future__ import annotations

from typing import Any

from ask_question_normalize import normalize_ask_typos

_SIGN_EN_TO_HI: dict[str, str] = {
    "Aries": "Mesh",
    "Taurus": "Vrishabh",
    "Gemini": "Mithun",
    "Cancer": "Kark",
    "Leo": "Singh",
    "Virgo": "Kanya",
    "Libra": "Tula",
    "Scorpio": "Vrishchik",
    "Sagittarius": "Dhanu",
    "Capricorn": "Makar",
    "Aquarius": "Kumbh",
    "Pisces": "Meen",
}

_SIGNS_EN = list(_SIGN_EN_TO_HI.keys())


def _sign_label(sign: str | None, lang: str) -> str:
    if not sign:
        return ""
    s = str(sign).strip()
    if not s:
        return ""
    # Title-case canonical English key
    key = s[:1].upper() + s[1:].lower() if s else s
    for en in _SIGNS_EN:
        if en.lower() == s.lower():
            key = en
            break
    if lang in ("hi", "hn"):
        return _SIGN_EN_TO_HI.get(key, s)
    return key


def _lagna_sign(kundli: dict) -> str | None:
    asc = kundli.get("ascendant") or kundli.get("lagna")
    if isinstance(asc, dict):
        return asc.get("sign") or asc.get("name")
    if isinstance(asc, str) and asc.strip():
        return asc.strip()
    deg = kundli.get("ascendantDeg")
    if isinstance(deg, (int, float)):
        return _SIGNS_EN[int(deg / 30) % 12]
    return None


def _moon_sign(kundli: dict) -> str | None:
    m = kundli.get("moonSign") or kundli.get("moon_sign")
    return str(m).strip() if m else None


def _sun_sign(kundli: dict) -> str | None:
    s = kundli.get("sunSign") or kundli.get("sun_sign")
    return str(s).strip() if s else None


def _nakshatra(kundli: dict) -> str | None:
    n = kundli.get("nakshatra")
    return str(n).strip() if n else None


def _current_dasha(kundli: dict) -> str | None:
    cd = kundli.get("currentDasha")
    if not isinstance(cd, dict):
        return None
    maha = cd.get("maha")
    antar = cd.get("antar")
    if maha and antar:
        return f"{maha} Mahadasha / {antar} Antardasha"
    if maha:
        return f"{maha} Mahadasha"
    return None


def try_deterministic_chart_fact(
    question: str,
    kundli: Any,
    lang: str = "hn",
) -> dict | None:
    """
    Return a full ask-response dict for simple lookups, or None to use LLM.
    """
    if not isinstance(kundli, dict) or not kundli.get("planets"):
        return None

    q = normalize_ask_typos(question)
    try:
        from openai_helper import _classify_ask_intent, _is_chart_fact_question

        if not _is_chart_fact_question(q):
            return None
        intent = _classify_ask_intent(q, lang)
    except Exception:
        return None

    it = intent.get("intent") or ""
    lang_use = lang if lang in ("hi", "hn", "en") else "hn"

    def _payload(text: str, topic: str = "general") -> dict:
        return {
            "text": text,
            "topic": topic,
            "question_type": "STATIC",
            "confidence": 1.0,
            "source": f"chart_fact_deterministic:{it}",
            "engine_tag": "ans-cosmo",
            "follow_ups": [],
        }

    if it == "lagna_lookup":
        sign = _sign_label(_lagna_sign(kundli), lang_use)
        if not sign:
            return None
        if lang_use == "en":
            text = f"Your ascendant (Lagna) is {sign}."
        else:
            text = f"Aapka lagna {sign} hai."
        return _payload(text)

    if it == "moon_sign_lookup":
        sign = _sign_label(_moon_sign(kundli), lang_use)
        if not sign:
            return None
        if lang_use == "en":
            text = f"Your Moon sign (janma rashi) is {sign}."
        else:
            text = f"Aapki janma rashi {sign} hai."
        return _payload(text)

    if it == "sun_sign_lookup":
        sign = _sign_label(_sun_sign(kundli), lang_use)
        if not sign:
            return None
        if lang_use == "en":
            text = f"Your Sun sign is {sign}."
        else:
            text = f"Aapki Surya rashi {sign} hai."
        return _payload(text)

    if it == "nakshatra_lookup":
        nak = _nakshatra(kundli)
        if not nak:
            return None
        if lang_use == "en":
            text = f"Your birth nakshatra is {nak}."
        else:
            text = f"Aapka janma nakshatra {nak} hai."
        return _payload(text)

    if it == "dasha_current":
        dasha = _current_dasha(kundli)
        if not dasha:
            return None
        if lang_use == "en":
            text = f"Your current dasha is {dasha}."
        else:
            text = f"Abhi aapki {dasha} chal rahi hai."
        return _payload(text)

    return None
