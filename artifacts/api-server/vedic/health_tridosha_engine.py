"""
health_tridosha_v1 — Vata / Pitta / Kapha from D1 + D9 + KP 6th CSL.

Weighted aggregation (display gauges):
  Final = D1 * 0.40 + D9 * 0.30 + 6th_CSL * 0.30

KP Step A — complete 6th CSL house script; dusthana 6/8/12 gating.
KP Step B — CSL planet humor override when connected to 6/8/12.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Set, Tuple

try:
    from stock_engine.kp_5th_csl import _csl_signification_chain
except ImportError:
    _csl_signification_chain = None  # type: ignore

try:
    from event_timing._shared.kp_significator_scan import _kp_sig_for_planet, _to_int_house_list
except ImportError:
    _kp_sig_for_planet = None  # type: ignore
    _to_int_house_list = None  # type: ignore

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]
_SIGN_IDX = {s: i for i, s in enumerate(SIGNS)}
SIGN_LORD = {
    "Aries": "Mars", "Taurus": "Venus", "Gemini": "Mercury", "Cancer": "Moon",
    "Leo": "Sun", "Virgo": "Mercury", "Libra": "Venus", "Scorpio": "Mars",
    "Sagittarius": "Jupiter", "Capricorn": "Saturn", "Aquarius": "Saturn", "Pisces": "Jupiter",
}
EXALT = {
    "Sun": "Aries", "Moon": "Taurus", "Mars": "Capricorn", "Mercury": "Virgo",
    "Jupiter": "Cancer", "Venus": "Pisces", "Saturn": "Libra",
}
DEBIL = {
    "Sun": "Libra", "Moon": "Scorpio", "Mars": "Cancer", "Mercury": "Pisces",
    "Jupiter": "Capricorn", "Venus": "Virgo", "Saturn": "Aries",
}
OWN = {
    "Sun": ["Leo"], "Moon": ["Cancer"], "Mars": ["Aries", "Scorpio"],
    "Mercury": ["Gemini", "Virgo"], "Jupiter": ["Sagittarius", "Pisces"],
    "Venus": ["Taurus", "Libra"], "Saturn": ["Capricorn", "Aquarius"],
}
SIGN_DOSHA = {
    "Aries": "pitta", "Taurus": "kapha", "Gemini": "vata", "Cancer": "kapha",
    "Leo": "pitta", "Virgo": "vata", "Libra": "vata", "Scorpio": "pitta",
    "Sagittarius": "pitta", "Capricorn": "vata", "Aquarius": "vata", "Pisces": "kapha",
}
PLANET_DOSHA = {
    "Sun": "pitta", "Mars": "pitta", "Saturn": "vata", "Mercury": "vata",
    "Moon": "kapha", "Venus": "kapha", "Jupiter": "kapha", "Rahu": "vata", "Ketu": "vata",
}
_WATER_SIGNS = frozenset({"Cancer", "Scorpio", "Pisces"})
_AIR_SIGNS = frozenset({"Gemini", "Libra", "Aquarius"})
_FIRE_SIGNS = frozenset({"Aries", "Leo", "Sagittarius"})
_BENEFICS = frozenset({"Jupiter", "Venus", "Mercury", "Moon"})
_MALEFICS = frozenset({"Saturn", "Mars", "Rahu", "Ketu", "Sun"})
_PLANETS_9 = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu")
_DUSTHANA = frozenset({6, 8, 12})
_HOUSE_DOSHA_BIAS = {4: "kapha", 5: "pitta"}
_W_D1, _W_D9, _W_CSL = 0.40, 0.30, 0.30

_CLINICAL_LABELS = {
    "kapha": "Kapha (Cough / Allergy)",
    "vata": "Vata (Baat / Gas / Nerve Pain)",
    "pitta": "Pitta (Acidity / Blood / Inflammation)",
}

_DIETARY_REMEDIES = {
    "kapha": [
        "Light warm meals; kam sweets, dairy, fried food",
        "Morning walk / brisk movement daily",
        "Ginger, black pepper, tulsi — congestion ko light rakho",
    ],
    "vata": [
        "Warm oily food; sesame/olive oil in diet",
        "Fixed sleep time; cold/dry food avoid",
        "Jeera-ajwain water; gentle abhyanga (oil massage)",
    ],
    "pitta": [
        "Cooling foods — coconut water, cucumber, sweet fruits",
        "Spice, anger, midday sun kam karo",
        "Amalaki, coriander, fennel — heat aur acidity balance",
    ],
}


def _find_p(planets: List[dict], name: str) -> Optional[dict]:
    return next((p for p in planets if p.get("name") == name), None)


def _dusthana_lords(asc_idx: int) -> set[str]:
    return {SIGN_LORD[SIGNS[(asc_idx + h - 1) % 12]] for h in _DUSTHANA}


def _planet_house(planets: List[dict], pname: str) -> Optional[int]:
    p = _find_p(planets, pname)
    if not p:
        return None
    h = p.get("house")
    return int(h) if isinstance(h, int) else None


def _aspects_house(aspector: str, ap_house: int, target_house: int) -> bool:
    if not (1 <= ap_house <= 12 and 1 <= target_house <= 12):
        return False
    diff = ((target_house - ap_house) % 12) + 1
    if diff == 7:
        return True
    extras = {
        "Mars": {4, 8}, "Jupiter": {5, 9}, "Saturn": {3, 10},
        "Rahu": {3, 10}, "Ketu": {3, 10},
    }
    return diff in extras.get(aspector, set())


def _is_combust(p: dict, sun: Optional[dict]) -> bool:
    if p.get("combust") or p.get("isCombust"):
        return True
    if not sun:
        return False
    pl, sl = p.get("longitude"), sun.get("longitude")
    if pl is None or sl is None:
        return False
    try:
        diff = abs(float(pl) - float(sl)) % 360.0
        return diff < 8.0 or diff > 352.0
    except (TypeError, ValueError):
        return False


def _is_retro(p: dict) -> bool:
    return bool(p.get("retrograde") or p.get("isRetrograde") or p.get("vakri"))


def _varga_chart(kundli: Optional[dict], key: str) -> Optional[dict]:
    if not kundli:
        return None
    dv = kundli.get("divisionalCharts") or {}
    ch = dv.get(key) or dv.get(key.lower())
    if isinstance(ch, dict) and ch.get("planets"):
        return ch
    return None


def _varga_asc_idx(chart: dict, fallback: int) -> int:
    asc = chart.get("ascendantSignIndex")
    if isinstance(asc, int):
        return int(asc) % 12
    asc_s = chart.get("ascendant") or ""
    if isinstance(asc_s, str) and asc_s in SIGNS:
        return SIGNS.index(asc_s)
    return fallback % 12


def _d9_dignity_tier(d9: dict, pname: str) -> str:
    p = _find_p(d9.get("planets") or [], pname)
    if not p:
        return "neutral"
    sg = str(p.get("sign") or "")
    if pname in EXALT and sg == EXALT[pname]:
        return "strong"
    if pname in OWN and sg in OWN[pname]:
        return "strong"
    if pname in DEBIL and sg == DEBIL[pname]:
        return "weak"
    return "neutral"


def _kp_cusp(kp: dict, house: int) -> Optional[dict]:
    for c in (kp or {}).get("cusps", []) or []:
        if isinstance(c, dict) and c.get("house") == house:
            return c
    return None


def _kp_flat_signified(kp: dict, planet: str) -> List[int]:
    sig = (kp or {}).get("significations") or {}
    raw = sig.get(planet) or sig.get(planet.lower()) or []
    if isinstance(raw, list):
        out: List[int] = []
        for v in raw:
            try:
                h = int(v)
                if 1 <= h <= 12:
                    out.append(h)
            except (TypeError, ValueError):
                continue
        return sorted(set(out))
    return []


def _norm_planet(p: Any) -> Optional[str]:
    if not p or not isinstance(p, str):
        return None
    return p.strip().title() or None


def _normalize_pct(raw: Dict[str, float]) -> Dict[str, int]:
    total = sum(raw.values()) or 1.0
    pct = {k: int(round(v * 100.0 / total)) for k, v in raw.items()}
    drift = 100 - sum(pct.values())
    if drift:
        dom = max(pct, key=pct.get)
        pct[dom] = max(0, pct[dom] + drift)
    return pct


def _share_scores(scores: Dict[str, float]) -> Dict[str, float]:
    total = sum(scores.values()) or 1.0
    return {k: (scores[k] / total) * 100.0 for k in scores}


def _dosha_state(pct: int) -> str:
    if pct < 36:
        return "Balanced"
    if pct < 44:
        return "Afflicted"
    return "Elevated"


def _clinical_humor(csl: str) -> Optional[str]:
    if csl in ("Venus", "Moon", "Jupiter"):
        return "kapha"
    if csl in ("Saturn", "Rahu", "Mercury"):
        return "vata"
    if csl in ("Sun", "Mars"):
        return "pitta"
    if csl == "Ketu":
        return "vata"
    return None


def _extract_6th_csl_script(kundli: Optional[dict], asc_idx: int) -> Dict[str, Any]:
    """Complete KP 6th CSL house signification chain."""
    out: Dict[str, Any] = {
        "csl_planet": None,
        "house_script": [],
        "chain": {},
        "dusthana_hits": [],
        "connects_to_dusthana": False,
        "clinical_disease_promise": False,
        "verdict": "UNKNOWN",
        "immunity_message": "",
    }
    if not kundli:
        return out

    kp = kundli.get("kp") or {}
    cusp = _kp_cusp(kp, 6)
    if not cusp:
        return out

    csl_raw = cusp.get("sb") or cusp.get("subLord") or cusp.get("sub_lord") or cusp.get("sl")
    csl = _norm_planet(csl_raw)
    out["csl_planet"] = csl
    if not csl:
        return out

    script: Set[int] = set()
    chain: Dict[str, Any] = {}

    if _kp_sig_for_planet and _to_int_house_list:
        sig = _kp_sig_for_planet(kp, csl)
        if sig:
            for key in ("pl", "sl", "sb_houses", "ss_houses"):
                script.update(_to_int_house_list(sig.get(key)))
            chain = {
                "nl_lord": sig.get("nl_lord"),
                "sb_lord": sig.get("sb_lord"),
                "ss_lord": sig.get("ss_lord"),
                "houses_pl": _to_int_house_list(sig.get("pl")),
                "houses_nl": _to_int_house_list(sig.get("sl")),
                "houses_sb": _to_int_house_list(sig.get("sb_houses")),
                "houses_ss": _to_int_house_list(sig.get("ss_houses")),
            }

    if not script and _csl_signification_chain:
        planets = kundli.get("planets") or []
        asc_si = _SIGN_IDX.get(str(kundli.get("ascendant") or ""), asc_idx)
        if planets:
            chain = _csl_signification_chain(csl, planets, asc_si)
            script.update(chain.get("signified") or [])

    if not script:
        script.update(_kp_flat_signified(kp, csl))

    house_script = sorted(script)
    out["house_script"] = house_script
    out["chain"] = chain

    dusthana_hits = sorted(h for h in house_script if h in _DUSTHANA)
    out["dusthana_hits"] = dusthana_hits
    out["connects_to_dusthana"] = bool(dusthana_hits)

    hset = set(house_script)
    out["clinical_disease_promise"] = (6 in hset and 8 in hset) or (8 in hset and 12 in hset)

    if not out["connects_to_dusthana"]:
        out["verdict"] = "HIGH_IMMUNITY"
        out["immunity_message"] = (
            "High Immunity / Sub-clinical Tendencies only."
        )
    elif out["clinical_disease_promise"]:
        out["verdict"] = "DISEASE_PROMISE_ACTIVE"
        out["immunity_message"] = ""
    else:
        out["verdict"] = "DUSTHANA_LINK_WEAK"
        out["immunity_message"] = ""

    return out


def _d1_layer(
    planets: List[dict], asc_idx: int
) -> Tuple[Dict[str, float], List[Tuple[str, str, float]]]:
    scores = {"vata": 0.0, "pitta": 0.0, "kapha": 0.0}
    ledger: List[Tuple[str, str, float]] = []
    sign_1 = SIGNS[asc_idx % 12]
    dusthana_lords = _dusthana_lords(asc_idx)
    sun = _find_p(planets, "Sun")

    def _add(dosha: str, w: float, planet: str = "") -> None:
        scores[dosha] += w
        if planet and w > 0:
            ledger.append((planet, dosha, w))

    _add(SIGN_DOSHA.get(sign_1, "vata"), 25.0)
    moon = _find_p(planets, "Moon")
    if moon and moon.get("sign"):
        _add(SIGN_DOSHA.get(str(moon.get("sign")), "vata"), 25.0, "Moon")
    if sun and sun.get("sign"):
        _add(SIGN_DOSHA.get(str(sun.get("sign")), "vata"), 15.0, "Sun")
    _add(PLANET_DOSHA.get(SIGN_LORD[sign_1], "vata"), 15.0, SIGN_LORD[sign_1])

    for p in planets or []:
        nm = str(p.get("name") or "")
        if nm not in _PLANETS_9:
            continue
        sg = str(p.get("sign") or "")
        if sg in _WATER_SIGNS:
            _add("kapha", 3.0, nm)
        elif sg in _AIR_SIGNS:
            _add("vata", 3.0, nm)
        elif sg in _FIRE_SIGNS:
            _add("pitta", 3.0, nm)
        else:
            _add(SIGN_DOSHA.get(sg, "kapha"), 2.0, nm)
        _add(PLANET_DOSHA.get(nm, "vata"), 2.0, nm)

    for h in (4, 5, 6):
        bias = _HOUSE_DOSHA_BIAS.get(h)
        for p in planets or []:
            if p.get("house") != h:
                continue
            nm = str(p.get("name") or "")
            if nm not in _PLANETS_9:
                continue
            target = bias or PLANET_DOSHA.get(nm, "vata")
            if nm in _MALEFICS:
                w = 7.0 * (2.0 if nm in dusthana_lords else 1.0)
                _add(target, w, nm)
            elif nm in _BENEFICS:
                _add(target, 3.0, nm)

        for pname in _PLANETS_9:
            ap_h = _planet_house(planets, pname)
            if not ap_h or not _aspects_house(pname, ap_h, h):
                continue
            target = bias or PLANET_DOSHA.get(pname, "vata")
            if pname in _MALEFICS:
                w = 5.0 * (2.0 if pname in dusthana_lords else 1.0)
                _add(target, w, pname)
            elif pname in _BENEFICS:
                _add(target, 2.0, pname)

    sat, rahu = _find_p(planets, "Saturn"), _find_p(planets, "Rahu")
    mars, venus = _find_p(planets, "Mars"), _find_p(planets, "Venus")
    for p in (sat, rahu):
        if p and p.get("house") in (1, 6):
            w = 10.0 * (2.0 if str(p.get("name")) in dusthana_lords else 1.0)
            _add("vata", w, str(p.get("name")))
    for p in (sun, mars):
        if p and p.get("house") in (5, 6):
            _add("pitta", 8.0, str(p.get("name") or ""))
    for p in (moon, venus):
        if not p:
            continue
        hit = _is_combust(p, sun) or _is_retro(p)
        if not hit:
            for aff in (sat, rahu):
                if aff and p.get("house") and aff.get("house"):
                    if abs(int(p.get("house") or 0) - int(aff.get("house") or 0)) <= 1:
                        hit = True
                        break
        if hit:
            _add("kapha", 8.0, str(p.get("name")))

    return scores, ledger


def _d9_layer(
    planets: List[dict],
    asc_idx: int,
    kundli: Optional[dict],
    ledger: List[Tuple[str, str, float]],
) -> Tuple[Dict[str, float], str]:
    """Independent D9 dosha scores + immunity verdict."""
    d9 = _varga_chart(kundli, "D9")
    if not d9:
        d1, _ = _d1_layer(planets, asc_idx)
        return dict(d1), "D9 unavailable — D1 prakriti used for D9 layer"

    d9_planets = d9.get("planets") or []
    d9_asc = _varga_asc_idx(d9, asc_idx)
    scores = {"vata": 0.0, "pitta": 0.0, "kapha": 0.0}

    sign_9 = SIGNS[d9_asc % 12]
    scores[SIGN_DOSHA.get(sign_9, "vata")] += 30.0
    moon9 = _find_p(d9_planets, "Moon")
    if moon9 and moon9.get("sign"):
        scores[SIGN_DOSHA.get(str(moon9.get("sign")), "vata")] += 25.0
    sun9 = _find_p(d9_planets, "Sun")
    if sun9 and sun9.get("sign"):
        scores[SIGN_DOSHA.get(str(sun9.get("sign")), "vata")] += 20.0
    lord_9 = SIGN_LORD[sign_9]
    scores[PLANET_DOSHA.get(lord_9, "vata")] += 15.0

    for p in d9_planets:
        nm = str(p.get("name") or "")
        if nm not in _PLANETS_9:
            continue
        sg = str(p.get("sign") or "")
        scores[SIGN_DOSHA.get(sg, PLANET_DOSHA.get(nm, "vata"))] += 2.0
        scores[PLANET_DOSHA.get(nm, "vata")] += 2.0

    strong_n, weak_n = 0, 0
    for planet, dosha, w in ledger:
        tier = _d9_dignity_tier(d9, planet)
        if tier == "strong":
            scores[dosha] = max(0.0, scores[dosha] - w * 0.4)
            strong_n += 1
        elif tier == "weak":
            scores[dosha] += w * 0.5
            weak_n += 1

    if weak_n > strong_n:
        verdict = "Chronic Risk — D9 debilitated graha dominate"
    elif strong_n > weak_n:
        verdict = "High Recovery Capabilities — D9 strong graha dominate"
    else:
        verdict = "Mixed D9 immunity"

    return scores, verdict


def _csl_significance_scores(csl_meta: Dict[str, Any]) -> Tuple[Dict[str, float], Optional[str]]:
    """6th CSL humor significance for 30% weight layer."""
    base = {"vata": 33.0, "pitta": 33.0, "kapha": 34.0}
    csl = csl_meta.get("csl_planet") or ""
    humor = _clinical_humor(csl) if csl else None

    if not csl_meta.get("connects_to_dusthana"):
        return base, None

    if not humor:
        return base, None

    active = {"vata": 12.0, "pitta": 12.0, "kapha": 12.0}
    boost = 64.0 if csl_meta.get("clinical_disease_promise") else 52.0
    active[humor] = boost
    return active, humor


def _structural_reason(
    csl_meta: Dict[str, Any],
    d9_verdict: str,
    clinical_trigger: Optional[str],
    dosha_balance: Dict[str, int],
) -> str:
    parts: List[str] = []
    csl = csl_meta.get("csl_planet") or "?"
    script = csl_meta.get("house_script") or []

    if csl_meta.get("verdict") == "HIGH_IMMUNITY":
        parts.append(
            f"KP 6th CSL {csl} chain {script} does not connect to houses 6/8/12 — "
            "major triggers dormant; High Immunity / Sub-clinical Tendencies only."
        )
    elif clinical_trigger:
        combo = ""
        if csl_meta.get("clinical_disease_promise"):
            combo = " (6-8 or 8-12 clinical promise)"
        parts.append(
            f"KP 6th CSL {csl} chain {script} connects to dusthana "
            f"{csl_meta.get('dusthana_hits')}{combo} — "
            f"{_CLINICAL_LABELS.get(clinical_trigger, clinical_trigger)} clinically activated."
        )
    else:
        parts.append(
            f"D1 prakriti dominant {max(dosha_balance, key=dosha_balance.get).title()} "
            f"({dosha_balance[max(dosha_balance, key=dosha_balance.get)]}%) with KP script {script}."
        )

    if d9_verdict:
        parts.append(d9_verdict)
    return " ".join(parts)


def compute_tridosha_balance(
    planets: List[dict],
    asc_idx: int,
    kundli: Optional[dict] = None,
) -> Dict[str, Any]:
    """D1 (40%) + D9 (30%) + 6th CSL (30%) → final vata/pitta/kapha %."""
    d1_raw, ledger = _d1_layer(planets, asc_idx)
    d9_raw, d9_verdict = _d9_layer(planets, asc_idx, kundli, ledger)
    csl_meta = _extract_6th_csl_script(kundli, asc_idx)
    csl_raw, clinical_trigger = _csl_significance_scores(csl_meta)

    d1_share = _share_scores(d1_raw)
    d9_share = _share_scores(d9_raw)
    csl_share = _share_scores(csl_raw)

    merged = {
        k: d1_share[k] * _W_D1 + d9_share[k] * _W_D9 + csl_share[k] * _W_CSL
        for k in ("vata", "pitta", "kapha")
    }
    dosha_balance = _normalize_pct(merged)
    dosha_states = {k: _dosha_state(dosha_balance[k]) for k in dosha_balance}

    d1_dominant = max(d1_share, key=d1_share.get)
    score_dominant = max(dosha_balance, key=dosha_balance.get)

    if csl_meta.get("connects_to_dusthana") and clinical_trigger:
        dominant_clinical = clinical_trigger
        primary_imbalance = clinical_trigger
        dominant_label = _CLINICAL_LABELS.get(clinical_trigger, clinical_trigger.title())
    else:
        dominant_clinical = score_dominant
        primary_imbalance = score_dominant
        dominant_label = score_dominant.title()

    dietary = list(_DIETARY_REMEDIES.get(dominant_clinical, []))
    structural = _structural_reason(csl_meta, d9_verdict, clinical_trigger, dosha_balance)

    kp_validation = {
        "csl_planet": csl_meta.get("csl_planet"),
        "house_script": csl_meta.get("house_script") or [],
        "signified_houses": csl_meta.get("house_script") or [],
        "dusthana_hits": csl_meta.get("dusthana_hits") or [],
        "clinical_disease_promise": bool(csl_meta.get("clinical_disease_promise")),
        "connects_to_dusthana": bool(csl_meta.get("connects_to_dusthana")),
        "verdict": (
            "DISEASE_PROMISE_ACTIVE"
            if csl_meta.get("clinical_disease_promise")
            else csl_meta.get("verdict", "UNKNOWN")
        ),
        "immunity_message": csl_meta.get("immunity_message") or "",
        "chain": csl_meta.get("chain") or {},
    }

    return {
        "engine": "health_tridosha_v1",
        "dosha_balance": dosha_balance,
        "dosha_states": dosha_states,
        "diagnostics": {
            "vata_score_state": dosha_states["vata"],
            "pitta_score_state": dosha_states["pitta"],
            "kapha_score_state": dosha_states["kapha"],
        },
        "dominant_dosha": dominant_label,
        "dominant_clinical_trigger": _CLINICAL_LABELS.get(
            dominant_clinical, dominant_clinical.title()
        ),
        "primary_imbalance": primary_imbalance,
        "d1_dominant": d1_dominant,
        "structural_reason": structural,
        "dietary_remedies": dietary,
        "tridosha_care": dietary[:2],
        "d9_immunity_verdict": d9_verdict,
        "kp_6th_csl": kp_validation,
        "kp_6th_csl_validation": kp_validation,
        "layer_breakdown": {
            "d1_pct": {k: round(d1_share[k], 1) for k in d1_share},
            "d9_pct": {k: round(d9_share[k], 1) for k in d9_share},
            "csl_pct": {k: round(csl_share[k], 1) for k in csl_share},
            "weights": {"d1": _W_D1, "d9": _W_D9, "csl": _W_CSL},
        },
        "clinical_disease_promise": bool(csl_meta.get("clinical_disease_promise")),
    }
