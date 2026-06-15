"""
wealth_finance_v1 — Life Map Finance diagnostic pipeline.

D1 yog blueprint → D9 verify → D2 hora style → KP 2/11 tier lock
→ dasha yoga activation → 12CSL leakage + transit liquidity hints.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Set, Tuple

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]
SIGN_LORD = {
    "Aries": "Mars", "Taurus": "Venus", "Gemini": "Mercury", "Cancer": "Moon",
    "Leo": "Sun", "Virgo": "Mercury", "Libra": "Venus", "Scorpio": "Mars",
    "Sagittarius": "Jupiter", "Capricorn": "Saturn", "Aquarius": "Saturn", "Pisces": "Jupiter",
}
EXALT = {
    "Sun": "Aries", "Moon": "Taurus", "Mars": "Capricorn", "Mercury": "Virgo",
    "Jupiter": "Cancer", "Venus": "Pisces", "Saturn": "Libra",
}
OWN = {
    "Sun": ["Leo"], "Moon": ["Cancer"], "Mars": ["Aries", "Scorpio"],
    "Mercury": ["Gemini", "Virgo"], "Jupiter": ["Sagittarius", "Pisces"],
    "Venus": ["Taurus", "Libra"], "Saturn": ["Capricorn", "Aquarius"],
}
_KENDRA = frozenset({1, 4, 7, 10})
_TRIKONA = frozenset({1, 5, 9})
_BENEFICS = frozenset({"Jupiter", "Venus", "Mercury", "Moon"})
_GAIN_KP = frozenset({2, 6, 11})
_JOB_KP = frozenset({6, 7, 10})

_2L_CHANNELS: Dict[int, str] = {
    1: "self-driven wealth and personal brand",
    2: "family savings and self-made accumulation",
    3: "communication, media and skill-based income",
    4: "property, comfort assets and home-based work",
    5: "creativity, speculation and advisory roles",
    6: "service, salary and competitive earnings",
    7: "business partnerships and client-facing roles",
    8: "inheritance, sudden shifts and other people's capital",
    9: "fortune, consultation and foreign or digital scaling",
    10: "corporate career, rank and administrative authority",
    11: "network gains, elder support and multiple streams",
    12: "foreign, digital or behind-the-scenes income",
}

_CSL10_CHANNELS: Dict[str, str] = {
    "Venus": "luxury, fashion, arts and entertainment",
    "Mars": "tech, engineering, real estate and enterprise",
    "Mercury": "trading, finance, coding and communication",
    "Jupiter": "education, law, coaching and advisory",
    "Sun": "government, leadership and authority roles",
    "Saturn": "long-build industry, manufacturing and discipline",
    "Moon": "public-facing care, hospitality and fluid income",
    "Rahu": "foreign, digital and unconventional scaling",
    "Ketu": "research, niche expertise and spiritual commerce",
}


def _find_p(planets: List[dict], name: str) -> Optional[dict]:
    return next((p for p in planets if p.get("name") == name), None)


def _house_lord(asc_idx: int, house: int) -> str:
    return SIGN_LORD[SIGNS[(asc_idx + house - 1) % 12]]


def _planet_house(planets: List[dict], name: str) -> Optional[int]:
    p = _find_p(planets, name)
    if not p:
        return None
    h = p.get("house")
    return int(h) if isinstance(h, int) else None


def _scan_raj_yogas(planets: List[dict], asc_idx: int) -> List[Dict[str, Any]]:
    from vedic.raj_yoga_engine_v1 import scan_raj_yogas
    return scan_raj_yogas(planets, asc_idx)[:12]


def _serialize_yogas_api(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [
        {
            "name": str(y.get("name") or ""),
            "detail": str(y.get("detail") or ""),
            "link": str(y.get("link") or ""),
            "houses": list(y.get("houses") or []),
            "planets": list(y.get("planets") or []),
        }
        for y in (items or [])
    ]


def _scan_dhan_yogas(
    planets: List[dict],
    asc_idx: int,
    existing: Optional[List[Dict[str, str]]] = None,
) -> List[Dict[str, Any]]:
    from vedic.dhan_yoga_engine_v1 import scan_dhan_yogas
    return scan_dhan_yogas(planets, asc_idx)[:8]


def _yoga_activation_pct(
    yogas: List[Dict[str, Any]],
    current_dasha: Optional[dict],
) -> Tuple[int, List[str]]:
    if not yogas:
        return 0, []
    cd = current_dasha or {}
    md = str(cd.get("maha") or "")
    ad = str(cd.get("antar") or "")
    pd = str(cd.get("pratyantar") or cd.get("pratyantarDasha") or "")
    weights = [(md, 0.30), (ad, 0.50), (pd, 0.20)]
    active: List[str] = []
    active_score = 0.0
    for y in yogas:
        parts = set(str(x) for x in (y.get("planets") or []))
        hit = 0.0
        for planet, w in weights:
            if planet and planet in parts:
                hit += w
        if hit >= 0.25:
            active.append(str(y.get("name") or ""))
            active_score += min(1.0, hit)
    pct = int(round(min(100.0, (active_score / max(1, len(yogas))) * 100)))
    return pct, [a for a in active if a]


def _varga_chart(kundli: Optional[dict], key: str) -> Optional[dict]:
    if not kundli:
        return None
    dv = kundli.get("divisionalCharts") or {}
    ch = dv.get(key) or dv.get(key.lower())
    if isinstance(ch, dict) and ch.get("planets"):
        return ch
    return None


def _d2_chandra_pct(kundli: Optional[dict], asc_idx: int) -> Tuple[int, str]:
    d2 = _varga_chart(kundli, "D2")
    if not d2:
        return 50, "mixed"
    planets = d2.get("planets") or []

    def hora(name: str) -> str:
        p = _find_p(planets, name)
        if not p:
            return "other"
        sg = str(p.get("sign") or "")
        si = SIGNS.index(sg) if sg in SIGNS else -1
        if si == 3:
            return "moon"
        if si == 4:
            return "sun"
        if si < 0:
            return "other"
        return "moon" if si % 2 == 1 else "sun"

    moon_n = sum(1 for p in planets if hora(str(p.get("name") or "")) == "moon")
    sun_n = sum(1 for p in planets if hora(str(p.get("name") or "")) == "sun")
    total = max(1, moon_n + sun_n)
    pct = int(round(100 * moon_n / total))
    if pct >= 58:
        tag = "chandra_dominant"
    elif pct <= 42:
        tag = "surya_dominant"
    else:
        tag = "mixed"
    return pct, tag


def _chart_plane_verdicts(
    planets: List[dict],
    asc_idx: int,
    kundli: Optional[dict],
) -> Dict[str, Any]:
    jup = _find_p(planets, "Jupiter")
    ven = _find_p(planets, "Venus")
    d1_ok = bool(
        jup and int(jup.get("house") or 0) in (2, 5, 9, 11)
        or ven and int(ven.get("house") or 0) in (2, 11)
        or _planet_house(planets, _house_lord(asc_idx, 2)) in (2, 11, 5, 9)
    )
    d9 = _varga_chart(kundli, "D9")
    d9_ok = False
    if d9:
        d9p = d9.get("planets") or []
        j9 = _find_p(d9p, "Jupiter")
        l11 = _house_lord(asc_idx, 11)
        p11 = _find_p(d9p, l11)
        d9_ok = bool(
            j9 and str(j9.get("sign") or "") in OWN.get("Jupiter", []) + [EXALT["Jupiter"]]
            or p11 and int(p11.get("house") or 0) in (2, 11, 9)
        )
    chandra_pct, d2_tag = _d2_chandra_pct(kundli, asc_idx)
    return {
        "d1_verdict": "strong" if d1_ok else "moderate",
        "d9_verdict": "stable" if d9_ok else "building",
        "d2_tag": d2_tag,
        "d2_chandra_pct": chandra_pct,
    }


_TIER_RANK = {
    "middle_class": 0,
    "rich": 1,
    "ultra_rich": 2,
    "millionaire": 3,
}


def wealth_tier_from_score(score: int) -> str:
    """Score → tier. Yog count does not affect this — only Money Builder score."""
    c = int(score)
    if c >= 85:
        return "millionaire"
    if c >= 72:
        return "ultra_rich"
    if c >= 60:
        return "rich"
    return "middle_class"


def _kp_tier_downgrade(
    kp: Optional[Dict[str, Any]],
    score_tier: str,
) -> str:
    """KP may lower wealth tier (leakage / job-only); never upgrade above score band."""
    if not kp:
        return score_tier
    h2, h11 = kp.get("h2") or {}, kp.get("h11") or {}
    g2 = set(h2.get("gain_hits") or [])
    g11 = set(h11.get("gain_hits") or [])
    combined = g2 | g11
    loss = bool(h2.get("loss_hits") or h11.get("loss_hits"))

    if loss and not (g11 & _GAIN_KP):
        return "middle_class"

    job_only = combined and combined <= _JOB_KP and not (combined & {2, 11})
    if job_only:
        return "middle_class"

    if loss:
        return "middle_class"

    if h2.get("verdict") == "RED" or h11.get("verdict") == "RED":
        if score_tier in ("ultra_rich", "millionaire"):
            return "rich"
        if score_tier == "rich":
            return "middle_class"

    return score_tier


def _kp_tier_lock(
    kp: Optional[Dict[str, Any]],
    d2_chandra_pct: int,
    fallback: str,
    wealth_score: int = 50,
) -> str:
    """Legacy name — score drives tier; KP can only downgrade."""
    _ = (d2_chandra_pct, fallback)
    score_tier = wealth_tier_from_score(wealth_score)
    return _kp_tier_downgrade(kp, score_tier)


def _wealth_source(
    planets: List[dict],
    asc_idx: int,
    kundli: Optional[dict],
) -> Dict[str, str]:
    lord_2 = _house_lord(asc_idx, 2)
    h2l = _planet_house(planets, lord_2) or 0
    channel_a = _2L_CHANNELS.get(h2l, "mixed income channels")

    channel_b = "diverse professional paths"
    try:
        from finance_static.kp_finance_csl import evaluate_kp_cusp_by_house
        h10 = evaluate_kp_cusp_by_house(kundli or {}, 10, "10th")
        if h10:
            csl = str(h10.get("csl_planet") or "")
            channel_b = _CSL10_CHANNELS.get(csl, channel_b)
    except Exception:
        pass

    label = f"{channel_b.title()} via {channel_a}"
    return {
        "channel": channel_b,
        "path": channel_a,
        "label": label,
    }


_LEAKAGE_ORDER = (
    "expense_drain_active",
    "property_legal_loss_risk",
    "speculation_trading_fraud_risk",
)
_DUSTHANA = frozenset({6, 8, 12})
_12H_DRAIN_PLANETS = frozenset({"Saturn", "Rahu", "Ketu", "Mars"})


def _d1_leakage_flags(planets: List[dict], asc_idx: int) -> Set[str]:
    """Classical D1 wealth leak signals (works without KP cusps)."""
    flags: Set[str] = set()
    for house in (2, 11):
        lord = _house_lord(asc_idx, house)
        lord_h = _planet_house(planets, lord)
        if lord_h in _DUSTHANA:
            flags.add("expense_drain_active")
    if _planet_house(planets, "Ketu") == 2:
        flags.add("expense_drain_active")
    if _planet_house(planets, "Rahu") == 8:
        flags.add("property_legal_loss_risk")
    for name in _12H_DRAIN_PLANETS:
        if _planet_house(planets, name) == 12:
            flags.add("expense_drain_active")
            break
    return flags


def _kp_leakage_flags(
    h2: Optional[Dict[str, Any]],
    h11: Optional[Dict[str, Any]],
    h12: Optional[Dict[str, Any]],
) -> Set[str]:
    """KP 2nd / 11th / 12th CSL leak signals — deduped per contamination bucket."""
    flags: Set[str] = set()

    for block in (h2, h11):
        if not block:
            continue
        if block.get("loss_hits") or block.get("verdict") == "RED":
            flags.add("expense_drain_active")

    if not h12:
        return flags

    csl = str(h12.get("csl_planet") or "")
    sig = set((h12.get("chain") or {}).get("signified") or [])
    loss = set(h12.get("loss_hits") or [])
    red = h12.get("verdict") == "RED"
    kp_vyaya = red or bool(loss)

    if kp_vyaya:
        flags.add("expense_drain_active")

    if csl in ("Saturn", "Mars"):
        flags.add("property_legal_loss_risk")

    if csl == "Rahu" and (sig & {5, 8}):
        flags.add("speculation_trading_fraud_risk")

    # One 8/12 contamination on 12th CSL → expense only (not property from same signal).
    if kp_vyaya and csl not in ("Saturn", "Mars"):
        flags.discard("property_legal_loss_risk")

    return flags


def _leakage_alerts(
    planets: List[dict],
    asc_idx: int,
    h2: Optional[Dict[str, Any]] = None,
    h11: Optional[Dict[str, Any]] = None,
    h12: Optional[Dict[str, Any]] = None,
) -> List[str]:
    """D1 + KP hybrid leakage flags in stable display order."""
    combined = _d1_leakage_flags(planets, asc_idx) | _kp_leakage_flags(h2, h11, h12)
    return [key for key in _LEAKAGE_ORDER if key in combined]


def _liquidity_index(
    planets: List[dict],
    asc_idx: int,
    transit_notes: Optional[List[str]] = None,
) -> str:
    notes = " ".join(transit_notes or []).lower()
    if any(k in notes for k in ("jupiter currently", "wealth-building", "opportunity phase")):
        return "high"
    if any(k in notes for k in ("saturn in", "discipline on expenses", "restricted")):
        return "restricted"
    moon = _find_p(planets, "Moon")
    if moon:
        mh = int(moon.get("house") or 0)
        if mh in (2, 5, 9, 11):
            return "high"
    return "restricted" if "expense" in notes else "moderate"


_TIER_LABELS = {
    "middle_class": "Stable",
    "rich": "Rich",
    "ultra_rich": "Ultra Rich",
    "millionaire": "Millionaire Potential",
}


def compute_wealth_finance_diagnostic(
    planets: List[dict],
    asc_idx: int,
    current_dasha: Optional[dict] = None,
    kundli: Optional[dict] = None,
    *,
    dhana_yogas: Optional[List[Dict[str, str]]] = None,
    wealth_karma_score: int = 50,
    fallback_category: str = "middle_class",
    transit_notes: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Full finance diagnostic payload for Life Map Finance screen."""
    dhan = _scan_dhan_yogas(planets, asc_idx, dhana_yogas)
    raj = _scan_raj_yogas(planets, asc_idx)
    all_yogas = dhan + raj
    activation_pct, active_yogas = _yoga_activation_pct(all_yogas, current_dasha)
    matrix = _chart_plane_verdicts(planets, asc_idx, kundli)
    chandra_pct = int(matrix["d2_chandra_pct"])

    kp: Optional[Dict[str, Any]] = None
    h12: Optional[Dict[str, Any]] = None
    try:
        from finance_static.kp_finance_csl import compute_kp_finance_csl, evaluate_kp_cusp_by_house
        kp = compute_kp_finance_csl(kundli or {})
        h12 = evaluate_kp_cusp_by_house(kundli or {}, 12, "12th")
    except Exception:
        pass

    # Wealth tier = Money Builder score only (KP shown in kp_layer, does not change tier).
    tier = wealth_tier_from_score(int(wealth_karma_score))

    source = _wealth_source(planets, asc_idx, kundli)
    h2_block = (kp or {}).get("h2") if kp else None
    h11_block = (kp or {}).get("h11") if kp else None
    leakage = _leakage_alerts(planets, asc_idx, h2_block, h11_block, h12)
    liquidity = _liquidity_index(planets, asc_idx, transit_notes)

    return {
        "engine": "wealth_finance_v1",
        "disclaimer": "Chart-based wellness guidance only — not investment or tax advice.",
        "yog_metrics": {
            "dhan_count": len(dhan),
            "raj_count": len(raj),
            "total_count": len(all_yogas),
            "activation_pct": activation_pct,
            "active_yogas": active_yogas[:4],
            "dhan_yoga_names": [str(y.get("name") or "") for y in dhan],
            "dhan_yogas": _serialize_yogas_api(dhan),
            "raj_yoga_names": [str(y.get("name") or "") for y in raj],
            "raj_yogas": _serialize_yogas_api(raj),
        },
        "chart_matrix": matrix,
        "wealth_tier": tier,
        "wealth_tier_label": _TIER_LABELS.get(tier, tier.replace("_", " ").title()),
        "wealth_source": source,
        "kp_layer": {
            "h2_verdict": (kp or {}).get("h2", {}).get("verdict"),
            "h11_verdict": (kp or {}).get("h11", {}).get("verdict"),
            "h12_verdict": (h12 or {}).get("verdict"),
        },
        "leakage_alerts": leakage,
        "current_liquidity_index": liquidity,
    }
