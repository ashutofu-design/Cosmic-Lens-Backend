"""Deterministic chart-fact answers — NO LLM.

Handles placement lookups: lagna, rashi, nakshatra, dasha, house occupants,
planet position, house lord, per-planet nakshatra, KP cusp sub-lord, divisional
chart (D9/D12/…) placements. Chart-fact questions must never fall through to
the LLM narrator.
"""
from __future__ import annotations

import re
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

# Intents handled deterministically (from _classify_ask_intent + local tags).
_CHART_LOOKUP_INTENTS = frozenset({
    "lagna_lookup",
    "moon_sign_lookup",
    "sun_sign_lookup",
    "nakshatra_lookup",
    "dasha_current",
    "house_lookup",
    "planet_in_house",
    "planet_position",
    "house_lord_lookup",
    "planet_nakshatra_lookup",
    "kp_cusp_lookup",
    "divisional_lookup",
    "sign_house_lookup",
})

_HOUSE_NUM_RX = re.compile(
    r"\b(\d{1,2})(?:st|nd|rd|th)?\s*(?:house|ghar|bhav[a]?|h)\b"
    r"|\b(?:lagna|first|pehla|pehle)\s*(?:house|ghar|bhav[a]?)\b",
    re.I,
)
_HOUSE_SHORT_RX = re.compile(
    r"\b(\d{1,2})(?:st|nd|rd|th)?\s+me\b.*\b(kon|kaun|kya|planet|grah)\b",
    re.I,
)
_HOUSE_LORD_RX = re.compile(
    r"\b(\d{1,2})(?:st|nd|rd|th)?\s+(?:house|ghar|bhav[a]?)\s+"
    r"(?:k[ae]\s+)?(?:lord|swami|malik|adhipati|owner)\b"
    r"|\b(\d{1,2})(?:st|nd|rd|th)?\s+(?:ka|ke)\s+(?:lord|swami|malik|adhipati)\b",
    re.I,
)
_PLANET_NAK_RX = re.compile(
    r"\b(sun|surya|moon|chandra|mars|mangal|mercury|budh|jupiter|guru|"
    r"venus|shukra|saturn|shani|sani|rahu|ketu)\b"
    r".{0,25}\b(nakshatra|nakshatr)\b"
    r"|\b(nakshatra|nakshatr)\b.{0,25}\b(sun|surya|moon|chandra|mars|mangal|"
    r"mercury|budh|jupiter|guru|venus|shukra|saturn|shani|sani|rahu|ketu)\b",
    re.I,
)
_CSL_HOUSE_RX = re.compile(r"\b(\d{1,2})(?:st|nd|rd|th)?\s+csl\b", re.I)
_KP_CUSP_RX = re.compile(
    r"\b(?:kp|sub[\s-]?lord|sublord|cusp|csl|cuspal\s*sub[\s-]?lord)\b"
    r"|\b(\d{1,2})(?:st|nd|rd|th)?\s+(?:csl|cusp|sub[\s-]?lord)\b",
    re.I,
)
_SIGN_ALIASES: dict[str, str] = {
    "mesh": "aries", "aries": "aries",
    "vrishabh": "taurus", "vrishabha": "taurus", "taurus": "taurus",
    "mithun": "gemini", "gemini": "gemini",
    "kark": "cancer", "karka": "cancer", "cancer": "cancer",
    "singh": "leo", "simha": "leo", "leo": "leo",
    "kanya": "virgo", "virgo": "virgo",
    "tula": "libra", "libra": "libra",
    "vrishchik": "scorpio", "vrishchika": "scorpio", "scorpio": "scorpio",
    "dhanu": "sagittarius", "sagittarius": "sagittarius",
    "makar": "capricorn", "capricorn": "capricorn",
    "kumbh": "aquarius", "aquarius": "aquarius",
    "meen": "pisces", "meena": "pisces", "pisces": "pisces",
}
_SIGN_IN_HOUSE_RX = re.compile(
    r"\b(kis\s+(?:ghar|house|bhav)|kahan|kahaan|kaun\s+sa\s+ghar|which\s+house|"
    r"ghar\s+me|house\s+me)\b",
    re.I,
)
_DIV_CHART_RX = re.compile(
    r"\b(d\d{1,2}|navamsa|navamsha|dwadasamsa|dasamsa|saptamsa|"
    r"horamsa|chaturthamsa|trimsamsa)\b",
    re.I,
)
_CHART_LOOKUP_RX = re.compile(
    r"\b("
    r"kahan|kahaan|kis\s+(?:house|ghar|bhav|rashi|sign|nakshatra)|"
    r"which\s+(?:house|sign|placement)|placement|placed|sthit|"
    r"house|ghar|bhav[a]?|lord|swami|malik|adhipati|"
    r"lagna|ascendant|nakshatra|dasha|"
    r"sub[\s-]?lord|sublord|cusp|csl|navamsa|navamsha|"
    r"d\d{1,2}|kon\s+he|kaun\s+he|kya\s+hai"
    r")\b",
    re.I,
)
_INTERPRET_RX = re.compile(
    r"\b(result|matlab|meaning|impact|effect|phala|fal|"
    r"kya\s+(?:hoga|hogi|hoti|hote)|kaise\s+(?:affect|prabhav)|"
    r"dikkat|problem|issue|accha|bura|lucky|unlucky|"
    r"good|bad|favourable|favorable)\b",
    re.I,
)
_DIV_CHART_MAP = {
    "d1": "D1",
    "d2": "D2",
    "d3": "D3",
    "d4": "D4",
    "d7": "D7",
    "d9": "D9",
    "d10": "D10",
    "d12": "D12",
    "d16": "D16",
    "d20": "D20",
    "d24": "D24",
    "d27": "D27",
    "d30": "D30",
    "d40": "D40",
    "d45": "D45",
    "d60": "D60",
    "navamsa": "D9",
    "navamsha": "D9",
    "dasamsa": "D10",
    "dwadasamsa": "D12",
    "saptamsa": "D7",
    "horamsa": "D2",
    "chaturthamsa": "D4",
    "trimsamsa": "D30",
}

_CLASSICAL_YOGA_RX = re.compile(
    r"(?ix)\b("
    r"raj\s*yog|raja\s*yog|gaj\s*kesari|gaja\s*kesari|"
    r"kal\s*sarp|kalsarp|mangal\s*dosh|manglik|"
    r"dhana\s*yog|chandra\s*mangal|budha\s*aditya|"
    r"neecha\s*bhanga|viparita|panch\s*mahapurush|"
    r"kaal\s*sarp|pitri\s*dosh|guru\s*chandal"
    r")\b",
)

_DOMAIN_OUTCOME_YOGA_RX = re.compile(
    r"(?ix)\b("
    r"true\s*love|sach+a\s*pyaar|sach+a\s*pyar|sachchi\s*mohabbat|"
    r"bachcha\s*pyaar|pyaar\s+milne|pyar\s+milne|prem\s+milne|love\s+milne|"
    r"pya+a?r\s+.*\byog|pya+a?r\s+.*\blikha|true\s*love\s+.*\byog|"
    r"prem\s+sambandh|love\s+life|milne\s+ka\s+yog|"
    r"shaadi|shadi|vivah|marriage|biwi|pati|rishta|"
    r"bachch|santaan|child|"
    r"career|naukri|job|promotion|"
    r"wealth|dhan|paisa|travel|videsh|foreign"
    r")\b",
)


def is_domain_outcome_yoga_question(question: str) -> bool:
    """Life-domain yog (love/career/marriage) — engines/LLM, not chart_fact lookup."""
    q = normalize_ask_typos((question or "").strip())
    if not q or not re.search(r"\byog", q, re.I):
        return False
    if _CLASSICAL_YOGA_RX.search(q):
        return False
    if _DOMAIN_OUTCOME_YOGA_RX.search(q):
        return True
    try:
        from ask_marriage_relationship_slice import is_marriage_relationship_static_question

        if is_marriage_relationship_static_question(q):
            return True
    except Exception:
        pass
    try:
        from ask_career.classifier import is_career_static_question

        if is_career_static_question(q):
            return True
    except Exception:
        pass
    return False


def _sign_label(sign: str | None, lang: str) -> str:
    if not sign:
        return ""
    s = str(sign).strip()
    if not s:
        return ""
    key = s[:1].upper() + s[1:].lower() if s else s
    for en in _SIGNS_EN:
        if en.lower() == s.lower():
            key = en
            break
    if lang in ("hi", "hn"):
        return _SIGN_EN_TO_HI.get(key, s)
    return key


def _parse_named_sign(q: str) -> str | None:
    ql = (q or "").lower()
    for alias, canon in _SIGN_ALIASES.items():
        if re.search(r"\b" + re.escape(alias) + r"\b", ql):
            return canon
    return None


def _detect_sign_house_lookup(q: str) -> bool:
    return bool(_parse_named_sign(q) and _SIGN_IN_HOUSE_RX.search(q or ""))


def _parse_house_num(q: str) -> int | None:
    m_csl = _CSL_HOUSE_RX.search(q or "")
    if m_csl and m_csl.group(1):
        try:
            h = int(m_csl.group(1))
            return h if 1 <= h <= 12 else None
        except (TypeError, ValueError):
            pass
    m = _HOUSE_NUM_RX.search(q or "")
    if m and m.group(1):
        try:
            h = int(m.group(1))
            return h if 1 <= h <= 12 else None
        except (TypeError, ValueError):
            pass
    m2 = _HOUSE_SHORT_RX.search(q or "")
    if m2 and m2.group(1):
        try:
            h = int(m2.group(1))
            return h if 1 <= h <= 12 else None
        except (TypeError, ValueError):
            pass
    m3 = _KP_CUSP_RX.search(q or "")
    if m3 and m3.group(1):
        try:
            h = int(m3.group(1))
            return h if 1 <= h <= 12 else None
        except (TypeError, ValueError):
            pass
    if re.search(r"\blagna\b|\bfirst\s*house\b|\bpehla\b", q or "", re.I):
        return 1
    return None


def _detect_divisional(q: str) -> str | None:
    m = _DIV_CHART_RX.search(q or "")
    if not m:
        return None
    tok = (m.group(1) or "").strip().lower()
    return _DIV_CHART_MAP.get(tok)


def _detect_local_lookup_tag(q: str) -> str | None:
    if _KP_CUSP_RX.search(q):
        return "kp_cusp_lookup"
    if _detect_sign_house_lookup(q):
        return "sign_house_lookup"
    if _HOUSE_LORD_RX.search(q):
        return "house_lord_lookup"
    if _PLANET_NAK_RX.search(q):
        return "planet_nakshatra_lookup"
    if _detect_divisional(q):
        return "divisional_lookup"
    return None


def is_chart_lookup_question(question: str) -> bool:
    """True when the question is a chart placement/fact lookup (engine-only)."""
    q = normalize_ask_typos((question or "").strip())
    if not q or len(q.split()) > 18:
        return False
    if is_domain_outcome_yoga_question(q):
        return False
    # Love / vehicle / career timing must not be mis-routed as chart yoga lookup.
    for _mod, _fn in (
        ("ask_love.timing_registry", "is_love_timing_question"),
        ("ask_vehicle.timing_registry", "is_vehicle_timing_question"),
        ("ask_career.timing_registry", "is_career_timing_question"),
    ):
        try:
            import importlib

            if getattr(importlib.import_module(_mod), _fn)(q):
                return False
        except Exception:
            pass
    local = _detect_local_lookup_tag(q)
    if local:
        return True
    try:
        from openai_helper import _classify_ask_intent, _is_chart_fact_question

        if _is_chart_fact_question(q):
            return True
        intent = _classify_ask_intent(q, "hn")
        it = intent.get("intent") or ""
        if it in _CHART_LOOKUP_INTENTS:
            return True
        if it in ("planet_strength", "yoga_check", "comparison", "planet_combo"):
            if it == "yoga_check" and is_domain_outcome_yoga_question(q):
                return False
            return True
    except Exception:
        pass
    if _CHART_LOOKUP_RX.search(q) and _parse_house_num(q) is not None:
        return True
    if _CHART_LOOKUP_RX.search(q):
        try:
            from openai_helper import _detect_planets

            if _detect_planets(q):
                return True
        except Exception:
            pass
    return False


def is_chart_interpretation_question(question: str) -> bool:
    """Placement + result/meaning — LLM must NOT interpret; engine gives facts only."""
    q = normalize_ask_typos((question or "").strip())
    if not q:
        return False
    if not _INTERPRET_RX.search(q):
        return False
    return bool(_CHART_LOOKUP_RX.search(q) or _parse_house_num(q))


def chart_lookup_refusal_payload(question: str, lang: str = "hn") -> dict:
    """When chart lookup detected but data/engine cannot answer — NO LLM."""
    lang_use = lang if lang in ("hi", "hn", "en") else "hn"
    if lang_use == "en":
        text = (
            "I can only answer chart placements from your saved birth chart data. "
            "This lookup could not be resolved from the chart — please rephrase "
            "(e.g. '5th house me kaun hai', 'Mars kis house me hai', '7th cusp sub-lord')."
        )
    else:
        text = (
            "Main sirf aapki kundli ke chart-fact seedha bata sakta hoon — "
            "yeh lookup chart data se resolve nahi hua. Sawaal thoda clear likhiye "
            "(jaise '5th house me kaun hai', 'Mars kis house me hai', '7th cusp sub-lord')."
        )
    return {
        "text": text,
        "topic": "chart_fact",
        "question_type": "STATIC",
        "confidence": 1.0,
        "source": "chart_fact_deterministic:unresolved",
        "engine_tag": "ans-cosmo",
        "follow_ups": [],
    }


def _payload(text: str, intent: str, topic: str = "chart_fact") -> dict:
    return {
        "text": text,
        "topic": topic,
        "question_type": "STATIC",
        "confidence": 1.0,
        "source": f"chart_fact_deterministic:{intent}",
        "engine_tag": "ans-cosmo",
        "follow_ups": [],
    }


def _truth(kundli: dict) -> dict:
    from openai_helper import _build_truth_facts

    return _build_truth_facts(kundli)


def _planet_display(name: str) -> str:
    return (name or "").strip().title() or name


def _answer_house_lookup(kundli: dict, house: int, lang: str) -> str | None:
    from vedic.love_reality.scoring_core import KundliReader

    r = KundliReader(kundli)
    occ = r.occupants(house)
    sign = (_truth(kundli).get("house_sign") or {}).get(house)
    sign_l = _sign_label(sign.title() if sign else None, lang) if sign else ""

    if lang == "en":
        if occ:
            pl = ", ".join(_planet_display(p) for p in occ)
            base = f"In your {house}{_ordinal(house)} house: {pl}."
        else:
            base = f"Your {house}{_ordinal(house)} house has no planets."
        if sign_l:
            base += f" House sign: {sign_l}."
        return base

    if occ:
        pl = ", ".join(_planet_display(p) for p in occ)
        base = f"Aapke {house}th house mein {pl} hain."
    else:
        base = f"Aapke {house}th house mein koi graha nahi hai."
    if sign_l:
        base += f" Is ghar ki rashi {sign_l} hai."
    return base


def _ordinal(n: int) -> str:
    if 10 <= n % 100 <= 20:
        return "th"
    return {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")


def _answer_house_lord(kundli: dict, house: int, lang: str) -> str | None:
    facts = _truth(kundli)
    lord = (facts.get("house_lord") or {}).get(house)
    if not lord:
        return None
    lord_title = _planet_display(lord)
    h = (facts.get("planet_house") or {}).get(lord.lower())
    sign = (facts.get("planet_sign") or {}).get(lord.lower())
    sign_l = _sign_label(sign.title() if sign else None, lang) if sign else ""

    if lang == "en":
        text = f"{house}{_ordinal(house)} house lord is {lord_title}."
        if isinstance(h, int):
            text += f" {lord_title} is in house {h}"
            if sign_l:
                text += f" ({sign_l})"
            text += "."
        return text

    text = f"{house}th house ka lord {lord_title} hai."
    if isinstance(h, int):
        text += f" {lord_title} {h}th house mein hai"
        if sign_l:
            text += f" ({sign_l} rashi)"
        text += "."
    return text


def _answer_planet_position(kundli: dict, planet: str, lang: str) -> str | None:
    facts = _truth(kundli)
    pn = planet.lower()
    h = (facts.get("planet_house") or {}).get(pn)
    sign = (facts.get("planet_sign") or {}).get(pn)
    if h is None and not sign:
        return None
    pl = _planet_display(planet)
    sign_l = _sign_label(sign.title() if sign else None, lang) if sign else ""
    retro = pn in (facts.get("retrograde") or set())

    if lang == "en":
        parts = [f"{pl}"]
        if isinstance(h, int):
            parts.append(f"is in house {h}")
        if sign_l:
            parts.append(f"sign {sign_l}")
        if retro:
            parts.append("(retrograde)")
        return " ".join(parts) + "."

    text = f"{pl}"
    if isinstance(h, int) and sign_l:
        text += f" {h}th house mein hai, rashi {sign_l}."
    elif isinstance(h, int):
        text += f" {h}th house mein hai."
    elif sign_l:
        text += f" ki rashi {sign_l} hai."
    if retro:
        text += " (vakri)"
    return text


def _answer_planet_nakshatra(kundli: dict, planet: str, lang: str) -> str | None:
    facts = _truth(kundli)
    pn = planet.lower()
    nak = (facts.get("nakshatra") or {}).get(pn)
    pada = (facts.get("nakshatra_pada") or {}).get(pn)
    if not nak and pn == "moon":
        nak = _nakshatra(kundli)
    if not nak:
        return None
    pl = _planet_display(planet)
    if lang == "en":
        text = f"{pl}'s nakshatra is {nak.title()}."
        if pada:
            text += f" Pada {pada}."
        return text
    text = f"{pl} ka nakshatra {nak.title()} hai."
    if pada:
        text += f" Pada {pada}."
    return text


def _answer_sign_in_house(kundli: dict, sign_canon: str, lang: str) -> str | None:
    facts = _truth(kundli)
    house_sign = facts.get("house_sign") or {}
    matches = [h for h, s in house_sign.items() if str(s).lower() == sign_canon.lower()]
    if not matches:
        return None
    h = int(matches[0])
    sign_disp = _sign_label(sign_canon.title(), lang)
    if lang == "en":
        return f"{sign_disp} sign is in your {h}{_ordinal(h)} house."
    return f"{sign_disp} rashi aapke {h}th house mein hai."


def _ensure_kp_on_kundli(kundli: dict) -> dict | None:
    """Return kp dict from kundli, computing lazily from birth fields if missing."""
    kp = kundli.get("kp") if isinstance(kundli, dict) else None
    if isinstance(kp, dict) and isinstance(kp.get("cusps"), list):
        return kp
    birth_keys = ("day", "month", "year", "hour", "minute", "ampm", "lat", "lon", "tz")
    if not all(kundli.get(k) is not None for k in birth_keys):
        return None
    try:
        from kp_engine import calculate_kp

        kp = calculate_kp({k: kundli.get(k) for k in birth_keys})
        if isinstance(kp, dict):
            kundli["kp"] = kp
            return kp
    except Exception:
        return None
    return None


def _answer_kp_cusp(kundli: dict, house: int, lang: str, *, use_csl: bool = False) -> str | None:
    _ensure_kp_on_kundli(kundli)
    kp = kundli.get("kp") if isinstance(kundli, dict) else None
    if not isinstance(kp, dict):
        return None
    cusps = kp.get("cusps")
    if not isinstance(cusps, list):
        return None
    cusp = next((c for c in cusps if isinstance(c, dict) and c.get("house") == house), None)
    if not cusp:
        return None
    sb = cusp.get("sb") or cusp.get("subLord") or cusp.get("sub_lord")
    sign = cusp.get("sign")
    if not sb:
        return None
    sb_disp = _planet_display(str(sb))
    sign_l = _sign_label(str(sign), lang) if sign else ""
    label = "CSL (cusp sub-lord)" if use_csl else "cusp sub-lord"

    if lang == "en":
        text = f"{house}{_ordinal(house)} {label} is {sb_disp}."
        if sign_l:
            text += f" Cusp sign: {sign_l}."
        return text

    label_hn = "CSL (cusp sub-lord)" if use_csl else "cusp ka sub-lord"
    text = f"{house}th cusp ka {label_hn} {sb_disp} hai."
    if sign_l:
        text += f" Cusp ki rashi {sign_l} hai."
    return text


def _answer_divisional(
    kundli: dict,
    varga: str,
    *,
    planet: str | None,
    house: int | None,
    lang: str,
) -> str | None:
    div = (kundli.get("divisionalCharts") or {}).get(varga)
    if not isinstance(div, dict):
        return None
    planets = div.get("planets") or []

    if planet:
        pl = next(
            (p for p in planets if isinstance(p, dict) and (p.get("name") or "").lower() == planet.lower()),
            None,
        )
        if not pl:
            return None
        sign = pl.get("sign")
        sign_l = _sign_label(str(sign), lang) if sign else ""
        h = pl.get("house")
        pl_disp = _planet_display(planet)
        tag = varga
        if lang == "en":
            text = f"In {tag}, {pl_disp}"
            if sign_l:
                text += f" is in {sign_l}"
            if isinstance(h, int):
                text += f" (house {h})"
            return text + "."

        text = f"{tag} mein {pl_disp}"
        if sign_l:
            text += f" {sign_l} rashi mein hai"
        if isinstance(h, int):
            text += f" ({h}th house)"
        return text + "."

    if house is not None:
        occ = [p.get("name") for p in planets if isinstance(p, dict) and p.get("house") == house]
        occ = [o for o in occ if o]
        if lang == "en":
            if occ:
                return f"In {varga} {house}{_ordinal(house)} house: {', '.join(_planet_display(o) for o in occ)}."
            return f"In {varga}, {house}{_ordinal(house)} house has no planets."

        if occ:
            pl = ", ".join(_planet_display(o) for o in occ)
            return f"{varga} ke {house}th house mein {pl} hain."
        return f"{varga} ke {house}th house mein koi graha nahi hai."

    return None


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
    birth: Any = None,
) -> dict | None:
    """Return a full ask-response dict for chart lookups, or None if not a lookup."""
    if not isinstance(kundli, dict) or not kundli.get("planets"):
        return None

    # Merge birth fields for lazy KP compute when client sends birthData separately.
    if isinstance(birth, dict):
        for k in ("day", "month", "year", "hour", "minute", "ampm", "lat", "lon", "tz"):
            if kundli.get(k) is None and birth.get(k) is not None:
                kundli[k] = birth.get(k)

    q = normalize_ask_typos(question or "")
    lang_use = lang if lang in ("hi", "hn", "en") else "hn"

    local_tag = _detect_local_lookup_tag(q)
    it = local_tag or ""
    planets: list[str] = []

    if not is_chart_lookup_question(q):
        return None

    try:
        from openai_helper import _classify_ask_intent, _detect_planets

        if not it:
            it = (_classify_ask_intent(q, lang_use).get("intent") or "")
        planets = _detect_planets(q)
    except Exception:
        if not it:
            it = "house_lookup"

    house = _parse_house_num(q)
    varga = _detect_divisional(q)
    wants_interpret = is_chart_interpretation_question(q)
    use_csl = bool(re.search(r"\bcsl\b", q, re.I))

    # ── Handlers (priority order) ─────────────────────────────────────────
    # Sign-in-house BEFORE moon_sign ("Mesh rashi kis ghar me" ≠ janma rashi).
    if _detect_sign_house_lookup(q):
        sign = _parse_named_sign(q)
        if sign:
            text = _answer_sign_in_house(kundli, sign, lang_use)
            if text:
                return _payload(text, "sign_house_lookup")

    # KP CSL / cusp sub-lord — engine only, no LLM interpretation.
    if it == "kp_cusp_lookup" or _KP_CUSP_RX.search(q):
        h = house or 1
        text = _answer_kp_cusp(kundli, h, lang_use, use_csl=use_csl)
        if text:
            return _payload(text, "kp_cusp_lookup")

    if it == "lagna_lookup":
        sign = _sign_label(_lagna_sign(kundli), lang_use)
        if sign:
            text = f"Your ascendant (Lagna) is {sign}." if lang_use == "en" else f"Aapka lagna {sign} hai."
            return _payload(text, it)

    if it == "moon_sign_lookup" and not _detect_sign_house_lookup(q):
        sign = _sign_label(_moon_sign(kundli), lang_use)
        if sign:
            text = (
                f"Your Moon sign (janma rashi) is {sign}."
                if lang_use == "en"
                else f"Aapki janma rashi {sign} hai."
            )
            return _payload(text, it)

    if it == "sun_sign_lookup":
        sign = _sign_label(_sun_sign(kundli), lang_use)
        if sign:
            text = f"Your Sun sign is {sign}." if lang_use == "en" else f"Aapki Surya rashi {sign} hai."
            return _payload(text, it)

    if it == "nakshatra_lookup":
        nak = _nakshatra(kundli)
        if nak:
            text = f"Your birth nakshatra is {nak}." if lang_use == "en" else f"Aapka janma nakshatra {nak} hai."
            return _payload(text, it)

    if it == "dasha_current":
        dasha = _current_dasha(kundli)
        if dasha:
            text = f"Your current dasha is {dasha}." if lang_use == "en" else f"Abhi aapki {dasha} chal rahi hai."
            return _payload(text, it)

    if it in ("house_lord_lookup",) and house:
        text = _answer_house_lord(kundli, house, lang_use)
        if text:
            if wants_interpret:
                text += (
                    " Result/impact ke liye specific life-area question puchiye — "
                    "main sirf chart placement batata hoon."
                    if lang_use != "en"
                    else " For result/impact, ask a specific life-area question — "
                    "I only state chart placements."
                )
            return _payload(text, it)

    if it in ("planet_nakshatra_lookup",) and planets:
        text = _answer_planet_nakshatra(kundli, planets[0], lang_use)
        if text:
            return _payload(text, it)

    if it in ("divisional_lookup",) and varga:
        text = _answer_divisional(
            kundli,
            varga,
            planet=planets[0] if planets else None,
            house=house,
            lang=lang_use,
        )
        if text:
            if wants_interpret:
                text += (
                    " Result/impact ke liye alag specific sawaal puchiye."
                    if lang_use != "en"
                    else " Ask a separate specific question for result/impact."
                )
            return _payload(text, it)

    if it in ("house_lookup",) and house:
        text = _answer_house_lookup(kundli, house, lang_use)
        if text:
            if wants_interpret:
                text += (
                    " Result/impact ke liye specific topic puchiye — "
                    "main sirf placement batata hoon."
                    if lang_use != "en"
                    else " For result/impact ask a specific topic — placement only."
                )
            return _payload(text, it)

    if it in ("planet_in_house", "planet_position") and planets:
        text = _answer_planet_position(kundli, planets[0], lang_use)
        if text:
            if wants_interpret:
                text += (
                    " Result/impact ke liye specific sawaal puchiye."
                    if lang_use != "en"
                    else " Ask separately for result/impact."
                )
            return _payload(text, it)

    # Fallback: house number in question → occupants
    if house and re.search(r"\b(kon|kaun|kya|who|what|which)\b", q, re.I):
        text = _answer_house_lookup(kundli, house, lang_use)
        if text:
            return _payload(text, "house_lookup")

    return None
