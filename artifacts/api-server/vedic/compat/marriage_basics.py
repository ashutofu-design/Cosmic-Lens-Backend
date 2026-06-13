"""
Deterministic Kundli Milan Basic — marriage chart intelligence (no LLM).

Per partner: D1 7th axis, D9 7th depth, Darakaraka, Upapada, KP 7th CSL,
gender-aware karaka (Venus for male / Jupiter for female), friction + remedy.

Couple: structural marriage band = average of both partners (no overlay bonuses).
Phase A (v3): 7L synastry, full D9 couple sync, manglik cancellation, relationship_signals.
Phase B (v4): 7L combust/retro, Graha Maitri synastry, dasha timeline, critical-alert lock-box.
Phase C (v5): occupant dignity, functional benefic, maraka 2/8, empty 7th, D9 occ, PD dasha, KP couple.
Phase D (v6): degree-based aspect orbs, DK/UL depth (aspects, D9 DK), nakshatra pada+yoni, 2/8 occupants.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Literal

from karakas import compute_karakas
from vedic.compat.marriage_copy_picker import build_partner_plain_copy, partner_copy_seed
from jaimini import compute_arudha_padas, compute_upapada
from vedic.compat.d9_marriage import _per_partner as d9_per_partner, compute_d9_marriage, _friendship_word
from vedic.compat.kp_marriage_promise import compute_kp_couple_promise, compute_kp_marriage_promise
from vedic.compat.synastry_7l import NAKSHATRAS, compute_synastry_7l
from vedic.doshas.dosh_deep import _norm as dosh_norm, mangal_dosh_full
from vedic.love_reality.relationship_signals import (
    PersonSignals,
    _analyze_person,
    analyze_couple,
)
from vedic.love_reality.scoring_core import (
    BENEFIC,
    DUSTHANA,
    KundliReader,
    MALEFIC,
    SIGN_LORDS,
    SIGNS,
    angular_distance_deg,
    orb_penalty_multiplier,
    planet_longitude,
)

_NAK_SIZE = 13.0 + 20.0 / 60.0
_YONI = [
    0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 2, 11, 12, 13, 14, 14, 13, 5, 12, 11, 10, 3, 7, 4, 9, 0,
]
_YONI_ENEMY = [(0, 1), (2, 3), (4, 5), (6, 7), (8, 9), (10, 11), (12, 13), (14, 0)]

Gender = Literal["male", "female", "unknown"]
Band = Literal["Strong", "Moderate", "Strained"]
CoupleBand = Literal["Promising", "Workable", "High Effort"]
KpVerdict = Literal["STRONG", "PARTIAL", "WEAK", "UNAVAILABLE"]

_MALE = frozenset({"m", "male", "man", "boy", "ladka", "son", "husband"})
_FEMALE = frozenset({"f", "female", "woman", "girl", "ladki", "daughter", "wife"})


def normalize_gender(raw: str | None) -> Gender:
    g = str(raw or "").strip().lower()
    if not g:
        return "unknown"
    base = g.split()[0].rstrip(".")
    if base in _MALE or ("male" in base and "female" not in base):
        return "male"
    if base in _FEMALE or "female" in base or "woman" in base or "girl" in base:
        return "female"
    return "unknown"


GOOD_LORDSHIP_HOUSES = frozenset({1, 4, 5, 7, 9, 10, 11})
_MARRIAGE_BASE = 52
_MARRIAGE_READINESS_FLOOR = 20
_MARRIAGE_COUPLE_FLOOR = 22
_STRESS_DASHA_LORDS = frozenset({"Saturn", "Rahu", "Ketu", "Mars"})
_SUPPORT_DASHA_LORDS = frozenset({"Venus", "Moon", "Jupiter"})
_DASHA_HORIZON_YEARS = 3
_SENSITIVE_NOTE_WORDS = (
    "loyalty", "third-person", "third person", "secret", "parallel",
    "venus-mars", "extramarital", "ghosting", "obsession", "blur",
)
_SENSITIVE_FLAG_WORDS = ("loyalty", "third-person", "secrecy", "parallel")
_VIMS_ORDER = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]
_VIMS_YEARS = {"Ketu": 7, "Venus": 20, "Sun": 6, "Moon": 10, "Mars": 7, "Rahu": 18, "Jupiter": 16, "Saturn": 19, "Mercury": 17}
_ALERT_LABELS = {
    "loyalty_axis": "Loyalty stress — passion/impulse may override commitment",
    "secrecy_axis": "Secrecy axis — hidden ties or parallel attention risk",
    "passion_override": "Venus-Mars tight conjunction — impulse over loyalty",
    "hidden_emotion": "Moon in 8th — hidden emotional layers test trust",
    "parallel_pull": "12th lord in 5th — secret parallel attraction line",
    "karmic_obsession": "Nodes on 7th — obsessive/karmic pull on partnership",
}


def _parse_dasha_date(raw: Any) -> datetime | None:
    if not raw:
        return None
    if isinstance(raw, datetime):
        return raw
    s = str(raw).strip()[:10]
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


def _fmt_month_range(start: datetime, end: datetime) -> str:
    if start.year == end.year and start.month == end.month:
        return start.strftime("%b %Y")
    if start.year == end.year:
        return f"{start.strftime('%b')} – {end.strftime('%b %Y')}"
    return f"{start.strftime('%b %Y')} – {end.strftime('%b %Y')}"


def _flatten_pratyantar_windows(kundli: dict) -> list[dict[str, Any]]:
    """Finer PD windows (~3 year horizon) from nested dashas."""
    out: list[dict[str, Any]] = []
    today = datetime.utcnow()
    horizon = today + timedelta(days=365 * _DASHA_HORIZON_YEARS)
    for md in kundli.get("dashas") or []:
        if not isinstance(md, dict):
            continue
        md_lord = md.get("planet") or md.get("maha")
        if not md_lord:
            continue
        for ad in md.get("subDashas") or md.get("antar_dashas") or []:
            if not isinstance(ad, dict):
                continue
            ad_lord = ad.get("planet") or ad.get("antar")
            ad_start = _parse_dasha_date(ad.get("startDate") or ad.get("start"))
            ad_end = _parse_dasha_date(ad.get("endDate") or ad.get("end"))
            if not (ad_lord and ad_start and ad_end):
                continue
            pd_list = ad.get("subDashas") or ad.get("pratyantar_dashas") or []
            if pd_list:
                for pd in pd_list:
                    if not isinstance(pd, dict):
                        continue
                    pd_lord = pd.get("planet") or pd.get("pratyantar")
                    pd_start = _parse_dasha_date(pd.get("startDate") or pd.get("start"))
                    pd_end = _parse_dasha_date(pd.get("endDate") or pd.get("end"))
                    if not (pd_lord and pd_start and pd_end):
                        continue
                    if pd_end < today - timedelta(days=14) or pd_start > horizon:
                        continue
                    out.append({
                        "maha": md_lord, "antar": ad_lord, "pratyantar": pd_lord,
                        "start": pd_start, "end": pd_end,
                        "range_label": _fmt_month_range(pd_start, pd_end),
                        "granularity": "pd",
                    })
            else:
                if ad_end < today - timedelta(days=14) or ad_start > horizon:
                    continue
                ad_secs = (ad_end - ad_start).total_seconds()
                if ad_secs <= 0 or ad_lord not in _VIMS_ORDER:
                    continue
                total = sum(_VIMS_YEARS.values())
                start_idx = _VIMS_ORDER.index(ad_lord)
                cursor = ad_start
                for k in range(9):
                    pd_lord = _VIMS_ORDER[(start_idx + k) % 9]
                    frac = _VIMS_YEARS[pd_lord] / total
                    pd_end = cursor + timedelta(seconds=ad_secs * frac)
                    if pd_end >= today - timedelta(days=14) and cursor <= horizon:
                        out.append({
                            "maha": md_lord, "antar": ad_lord, "pratyantar": pd_lord,
                            "start": cursor, "end": pd_end,
                            "range_label": _fmt_month_range(cursor, pd_end),
                            "granularity": "pd_synth",
                        })
                    cursor = pd_end
    out.sort(key=lambda r: r["start"])
    return out


def _flatten_antardashas(kundli: dict) -> list[dict[str, Any]]:
    """Upcoming antardasha windows from kundli['dashas'] (next ~3 years)."""
    out: list[dict[str, Any]] = []
    today = datetime.utcnow()
    horizon = today + timedelta(days=365 * _DASHA_HORIZON_YEARS)
    for md in kundli.get("dashas") or []:
        if not isinstance(md, dict):
            continue
        md_lord = md.get("planet") or md.get("maha")
        if not md_lord:
            continue
        for ad in md.get("subDashas") or md.get("antar_dashas") or []:
            if not isinstance(ad, dict):
                continue
            ad_lord = ad.get("planet") or ad.get("antar")
            ad_start = _parse_dasha_date(ad.get("startDate") or ad.get("start"))
            ad_end = _parse_dasha_date(ad.get("endDate") or ad.get("end"))
            if not (ad_lord and ad_start and ad_end):
                continue
            if ad_end < today - timedelta(days=14) or ad_start > horizon:
                continue
            out.append({
                "maha": md_lord,
                "antar": ad_lord,
                "start": ad_start,
                "end": ad_end,
                "range_label": _fmt_month_range(ad_start, ad_end),
            })
    out.sort(key=lambda r: r["start"])
    return out


def _classify_dasha_window(maha: str, antar: str) -> str:
    if antar in _STRESS_DASHA_LORDS or maha in _STRESS_DASHA_LORDS:
        return "stress"
    if antar in _SUPPORT_DASHA_LORDS:
        return "reconnection"
    return "neutral"


def _dasha_window_note(kind: str, maha: str, antar: str, range_label: str) -> str:
    if kind == "stress":
        if antar in ("Rahu", "Ketu"):
            return (
                f"Stress window {range_label}: {maha}/{antar} AD — trust/confusion "
                "pressure may rise; avoid impulsive decisions."
            )
        if antar == "Saturn":
            return (
                f"Stress window {range_label}: {maha}/{antar} AD — distance/patience "
                "tests; bond needs structure not ultimatums."
            )
        return (
            f"Stress window {range_label}: {maha}/{antar} AD — heated friction "
            "theme; cool-down rituals help."
        )
    if kind == "reconnection":
        return (
            f"Reconnection window {range_label}: {maha}/{antar} AD — warmth/repair "
            "capacity improves if both show up."
        )
    return f"Neutral phase {range_label}: {maha}/{antar} AD — steady effort decides tone."


def _dasha_window_note_pd(kind: str, maha: str, antar: str, praty: str, range_label: str) -> str:
    base = _dasha_window_note(kind, maha, antar, range_label).replace(" AD ", f" AD / {praty} PD ")
    return base.replace("Stress window", "Stress window (PD)" if kind == "stress" else "Reconnection window (PD)" if kind == "reconnection" else "Neutral phase (PD)")


def _partner_dasha_timeline(kundli: dict, name: str) -> dict[str, Any]:
    cd = kundli.get("currentDasha") or {}
    maha = cd.get("maha")
    antar = cd.get("antar")
    praty = cd.get("pratyantar")
    start = cd.get("startDate")
    end = cd.get("endDate")
    current_note = "Dasha data unavailable."
    if maha and antar:
        end_dt = _parse_dasha_date(end)
        range_txt = _fmt_month_range(_parse_dasha_date(start) or datetime.utcnow(), end_dt) if end_dt else "ongoing"
        pr_txt = f" · PD {praty}" if praty else ""
        kind = _classify_dasha_window(str(maha), str(antar))
        current_note = (
            f"Now: {maha} MD / {antar} AD{pr_txt} ({range_txt}) — "
            f"{'pressure phase' if kind == 'stress' else 'repair-friendly' if kind == 'reconnection' else 'mixed phase'}."
        )

    stress_windows: list[dict[str, str]] = []
    reconnection_windows: list[dict[str, str]] = []
    today = datetime.utcnow()
    pd_rows = _flatten_pratyantar_windows(kundli)
    rows = pd_rows if pd_rows else [
        {**r, "pratyantar": r["antar"], "granularity": "ad"}
        for r in _flatten_antardashas(kundli)
    ]
    for row in rows:
        if row["end"] < today:
            continue
        praty = row.get("pratyantar") or row["antar"]
        kind = _classify_dasha_window(row["maha"], praty)
        is_pd = str(row.get("granularity", "")).startswith("pd")
        if is_pd:
            note = _dasha_window_note_pd(kind, row["maha"], row["antar"], praty, row["range_label"])
        else:
            note = _dasha_window_note(kind, row["maha"], row["antar"], row["range_label"])
        entry = {
            "range": row["range_label"],
            "maha": row["maha"],
            "antar": row["antar"],
            "pratyantar": praty,
            "granularity": row.get("granularity", "ad"),
            "note": note,
        }
        if kind == "stress" and len(stress_windows) < 3:
            stress_windows.append(entry)
        elif kind == "reconnection" and len(reconnection_windows) < 3:
            reconnection_windows.append(entry)

    return {
        "available": bool(maha and antar) or bool(stress_windows or reconnection_windows),
        "current": {
            "maha": maha,
            "antar": antar,
            "pratyantar": praty,
            "start_date": start,
            "end_date": end,
            "note": current_note,
        },
        "stress_windows": stress_windows,
        "reconnection_windows": reconnection_windows,
        "why_now_hint": (
            stress_windows[0]["note"]
            if stress_windows and _classify_dasha_window(str(maha or ""), str(antar or "")) == "stress"
            else current_note
        ),
    }


def _moon_graha_maitri(k1: KundliReader, k2: KundliReader) -> dict[str, Any]:
    m1, m2 = k1.planet("Moon"), k2.planet("Moon")
    if not m1 or not m2:
        return {"available": False, "relation": "neutral", "score_delta": 0, "note": "Moon data unavailable."}
    lord1 = SIGN_LORDS[k1.sidx(m1["sign"])]
    lord2 = SIGN_LORDS[k2.sidx(m2["sign"])]
    rel = _friendship_word(lord1, lord2)
    score_delta = 0
    if rel in ("same", "friendly"):
        score_delta = 3
        note = (
            f"Graha Maitri supportive — Moon lords {lord1} ↔ {lord2} ({rel}); "
            "thinking rhythm can align with effort."
        )
    elif rel == "hostile":
        score_delta = -4
        note = (
            f"Graha Maitri friction — Moon lords {lord1} ↔ {lord2} hostile; "
            "mental pace may clash even when structure is strong."
        )
    else:
        note = f"Graha Maitri neutral — Moon lords {lord1} ↔ {lord2}."
    return {
        "available": True,
        "p1_moon_sign": m1.get("sign"),
        "p2_moon_sign": m2.get("sign"),
        "p1_moon_lord": lord1,
        "p2_moon_lord": lord2,
        "relation": rel,
        "score_delta": score_delta,
        "note": note,
    }


def _is_sensitive_note(note: str) -> bool:
    low = note.lower()
    return any(w in low for w in _SENSITIVE_NOTE_WORDS)


def _critical_alerts_detail(sig: PersonSignals) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    checks = (
        ("loyalty_axis", sig.loyalty_risk_high),
        ("secrecy_axis", sig.third_person_risk),
        ("passion_override", sig.venus_mars_conjunct_tight),
        ("hidden_emotion", sig.moon_in_8th),
        ("parallel_pull", sig.twelfth_lord_in_fifth),
        ("karmic_obsession", sig.rahu_on_7th_axis),
    )
    for key, active in checks:
        if active:
            items.append({"id": key, "label": _ALERT_LABELS[key]})
    return items


def _critical_alerts_block(sig: PersonSignals) -> dict[str, Any]:
    categories: list[str] = []
    if sig.loyalty_risk_high:
        categories.append("loyalty_axis")
    if sig.third_person_risk:
        categories.append("secrecy_axis")
    if sig.venus_mars_conjunct_tight:
        categories.append("passion_override")
    if sig.moon_in_8th:
        categories.append("hidden_emotion")
    if sig.twelfth_lord_in_fifth:
        categories.append("parallel_pull")
    if sig.rahu_on_7th_axis:
        categories.append("karmic_obsession")
    count = len(categories)
    detail = _critical_alerts_detail(sig)
    return {
        "count": count,
        "locked": count > 0,
        "teaser": (
            f"⚠️ {count} Critical Hidden Karmic Alert{'s' if count != 1 else ''} detected in your chart axis."
            if count
            else "No critical hidden karmic alerts flagged."
        ),
        "unlock_in": "pro" if count else None,
        "detail": detail,
    }


def _person_signals_block_safe(sig: PersonSignals) -> dict[str, Any]:
    return {
        "affliction_weight": sig.affliction_weight,
        "reconnection_yoga": sig.reconnection_yoga,
        "separation_yoga": sig.separation_yoga,
        "safe_notes": [n for n in sig.notes if not _is_sensitive_note(n)][:4],
    }


def _sanitize_display_flags(flags: list[str]) -> list[str]:
    return [f for f in flags if not any(w in f.lower() for w in _SENSITIVE_FLAG_WORDS)]


def _sanitize_friction(friction: str, critical: dict[str, Any]) -> str:
    if critical.get("locked") and _is_sensitive_note(friction):
        return str(critical.get("teaser") or friction)
    return friction


def _yogakaraka_planet(asc_idx: int) -> str | None:
    return {
        1: "Saturn", 6: "Saturn",
        3: "Mars", 4: "Mars",
        9: "Venus", 10: "Venus",
    }.get(asc_idx)


def _functional_nature(k: KundliReader, planet: str) -> tuple[str, bool]:
    """Return (effective nature benefic/malefic/neutral, is_yogakaraka)."""
    yk = _yogakaraka_planet(k.asc_index())
    is_yk = planet == yk
    if is_yk:
        return "benefic", True
    if planet in BENEFIC:
        return "benefic", False
    if planet in MALEFIC:
        return "malefic", False
    return "neutral", False


def _occupant_condition_modifiers(k: KundliReader, planet: str) -> dict[str, Any]:
    p = k.planet(planet)
    if not p:
        return {"dignity": 0, "dignity_word": "unknown", "combust": False, "retrograde": False, "score_delta": 0, "notes": []}
    sign = p.get("sign") or "Aries"
    dig = k.dignity(planet, k.sidx(sign))
    combust = k.is_combust(planet)
    retro = k.is_retrograde(planet)
    notes: list[str] = []
    score_delta = 0
    if dig >= 2:
        score_delta += 3
        notes.append(f"{planet} exalted in 7th — strong shubh presence.")
    elif dig == 1:
        score_delta += 2
        notes.append(f"{planet} own/friendly in 7th — supportive.")
    elif dig <= -2:
        score_delta -= 5
        notes.append(f"{planet} debilitated in 7th — promise weak on surface.")
    elif dig == -1:
        score_delta -= 2
    if combust and planet not in ("Sun", "Rahu", "Ketu"):
        score_delta -= 4
        notes.append(f"{planet} combust in 7th — significator burned, effect fades.")
    if retro:
        score_delta -= 2
        notes.append(f"{planet} vakri in 7th — delayed/unpredictable expression.")
    return {
        "dignity": dig,
        "dignity_word": k.dignity_word(dig),
        "combust": combust,
        "retrograde": retro,
        "score_delta": score_delta,
        "notes": notes,
    }


def _aspecting_planets_to_sign(k: KundliReader, sign_idx: int) -> list[str]:
    """Vedic whole-sign aspects landing on `sign_idx`."""
    hits: list[str] = []
    for p in k.k.get("planets") or []:
        nm = p.get("name")
        if not nm:
            continue
        ps = k.sidx(p.get("sign"))
        d = (sign_idx - ps + 12) % 12
        ok = d == 6
        if nm == "Mars":
            ok = ok or d in (3, 7)
        if nm == "Jupiter":
            ok = ok or d in (4, 8)
        if nm == "Saturn":
            ok = ok or d in (2, 9)
        if nm in ("Rahu", "Ketu"):
            ok = ok or d in (4, 8)
        if ok:
            hits.append(str(nm))
    return hits


def _aspect_orb_multiplier(k: KundliReader, aspecting_planet: str, house: int) -> tuple[float, float | None]:
    """Degree-tight orb weight for a planet aspecting `house` (≤8° full, wider half)."""
    plon = planet_longitude(k, aspecting_planet)
    if plon is None:
        return orb_penalty_multiplier(None, sign_only=True), None

    targets: list[float] = []
    for occ in k.occupants(house):
        olon = planet_longitude(k, occ)
        if olon is not None:
            targets.append(olon)

    if not targets:
        sign_idx = (k.asc_index() + house - 1) % 12
        targets.append(sign_idx * 30.0 + 15.0)

    dist = min(angular_distance_deg(plon, t) for t in targets)
    return orb_penalty_multiplier(dist, sign_only=False), round(dist, 1)


def _moon_nak_pada(kundli: dict) -> dict[str, Any] | None:
    moon = None
    for p in kundli.get("planets") or []:
        if p.get("name") == "Moon":
            moon = p
            break
    if not moon:
        return None
    lon = moon.get("longitude")
    if not isinstance(lon, (int, float)):
        return None
    ml = float(lon) % 360.0
    nak_idx = int(ml / _NAK_SIZE) % 27
    pada = int((ml % _NAK_SIZE) / (_NAK_SIZE / 4)) + 1
    return {
        "nak_idx": nak_idx,
        "nak_name": NAKSHATRAS[nak_idx],
        "pada": pada,
        "yoni": _YONI[nak_idx],
    }


def _yoni_score(n1: int, n2: int) -> tuple[int, str]:
    y1, y2 = _YONI[n1], _YONI[n2]
    if y1 == y2:
        return 4, "Same Yoni"
    if any((y1 == a and y2 == b) or (y1 == b and y2 == a) for a, b in _YONI_ENEMY):
        return 0, "Hostile Yoni"
    return 2, "Moderate Yoni"


def _nakshatra_pada_yoni_couple(kundli_p1: dict, kundli_p2: dict) -> dict[str, Any]:
    """Full Moon nakshatra pada + yoni synastry (Ashtakoot-grade yoni, pada resonance)."""
    m1 = _moon_nak_pada(kundli_p1)
    m2 = _moon_nak_pada(kundli_p2)
    if not (m1 and m2):
        return {"available": False, "score_delta": 0, "note": "Moon nakshatra/pada unavailable."}

    yoni_sc, yoni_label = _yoni_score(m1["nak_idx"], m2["nak_idx"])
    same_nak = m1["nak_idx"] == m2["nak_idx"]
    same_pada = m1["pada"] == m2["pada"]
    if same_nak and same_pada:
        pada_match = "exact"
        pada_note = f"Same nakshatra+pada ({m1['nak_name']} pada {m1['pada']}) — deep star resonance."
        pada_delta = 3
    elif same_nak:
        pada_match = "same_nak_diff_pada"
        pada_note = (
            f"Same nakshatra {m1['nak_name']} but pada {m1['pada']} vs {m2['pada']} — "
            "star-lord match, pada tone differs."
        )
        pada_delta = 1
    else:
        pada_match = "different_nak"
        pada_note = (
            f"{m1['nak_name']} pada {m1['pada']} × {m2['nak_name']} pada {m2['pada']} — "
            "distinct nakshatra streams."
        )
        pada_delta = 0

    yoni_delta = {4: 4, 2: 1, 0: -5}.get(yoni_sc, 0)
    score_delta = pada_delta + yoni_delta

    return {
        "available": True,
        "p1_nak": m1["nak_name"],
        "p1_pada": m1["pada"],
        "p2_nak": m2["nak_name"],
        "p2_pada": m2["pada"],
        "pada_match": pada_match,
        "pada_note": pada_note,
        "yoni_score": yoni_sc,
        "yoni_max": 4,
        "yoni_label": yoni_label,
        "score_delta": score_delta,
        "note": f"{pada_note} Yoni: {yoni_label} ({yoni_sc}/4).",
    }


def _build_darakaraka_block(k: KundliReader, dk_planet: str | None) -> dict[str, Any]:
    base: dict[str, Any] = {
        "planet": dk_planet,
        "sign": None,
        "house": None,
        "dignity": None,
        "aspects": [],
        "conjunctions": [],
        "d9": None,
        "score_delta": 0,
        "note": "Darakaraka unavailable.",
    }
    if not dk_planet:
        return base
    dk_p = k.planet(dk_planet)
    if not dk_p:
        return base

    house = dk_p.get("house")
    sign = dk_p.get("sign")
    dig = k.dignity(dk_planet, k.sidx(sign or "Aries"))
    aspects = k.aspects_planet(dk_planet)
    conjunctions = [
        str(p["name"])
        for p in k.k.get("planets") or []
        if p.get("name") != dk_planet and p.get("house") == house
    ]

    score_delta = 0
    depth_notes: list[str] = []
    malefic_asp = [a for a in aspects if a in MALEFIC]
    benefic_asp = [a for a in aspects if a in BENEFIC]
    if malefic_asp:
        score_delta -= 3 * len(malefic_asp)
        depth_notes.append(f"Malefics aspect DK: {', '.join(malefic_asp)}.")
    if benefic_asp:
        score_delta += 2 * len(benefic_asp)
        depth_notes.append(f"Benefics aspect DK: {', '.join(benefic_asp)}.")
    malefic_conj = [c for c in conjunctions if c in MALEFIC]
    benefic_conj = [c for c in conjunctions if c in BENEFIC]
    if malefic_conj:
        score_delta -= 4
        depth_notes.append(f"DK conjunct {', '.join(malefic_conj)} — spouse tone coloured by that graha.")
    elif benefic_conj:
        score_delta += 3
        depth_notes.append(f"DK conjunct {', '.join(benefic_conj)} — spouse tone softened.")

    if dig >= 1:
        score_delta += 3
    elif dig <= -2:
        score_delta -= 4

    d9_block = None
    d9_dk = k.d9_planet(dk_planet)
    if d9_dk:
        d9_sign = d9_dk.get("sign")
        d9_si = k.sidx(d9_sign) if isinstance(d9_sign, str) else None
        d9_house = ((d9_si - k.d9_asc_index()) % 12) + 1 if d9_si is not None else None
        d9_dig = k.dignity(dk_planet, d9_si) if d9_si is not None else 0
        if d9_house == 7:
            score_delta += 5
            depth_notes.append("D9 DK in 7th — inner spouse promise strong.")
        elif d9_house in DUSTHANA:
            score_delta -= 5
            depth_notes.append(f"D9 DK in dusthana {d9_house} — inner marriage tone strained.")
        elif d9_dig >= 1:
            score_delta += 2
        d9_block = {
            "sign": d9_sign,
            "house": d9_house,
            "dignity": k.dignity_word(d9_dig),
        }

    note = (
        f"Darakaraka {dk_planet} in {sign} house {house} ({k.dignity_word(dig)})."
    )
    if depth_notes:
        note += " " + " ".join(depth_notes)

    base.update({
        "sign": sign,
        "house": house,
        "dignity": k.dignity_word(dig),
        "aspects": aspects,
        "conjunctions": conjunctions,
        "d9": d9_block,
        "score_delta": score_delta,
        "note": note,
    })
    return base


def _upapada_depth(k: KundliReader, ul: dict[str, Any]) -> dict[str, Any]:
    if not ul:
        return {
            "aspects_on_ul_lord": [],
            "ul_lord_conjunctions": [],
            "aspects_on_ul_sign": [],
            "score_delta": 0,
            "depth_note": "",
        }
    ul_lord = ul.get("ul_lord")
    ul_sign = ul.get("ul_sign")
    ul_idx = SIGNS.index(ul_sign) if isinstance(ul_sign, str) and ul_sign in SIGNS else None

    aspects_on_lord = k.aspects_planet(str(ul_lord)) if ul_lord else []
    lord_conjs: list[str] = []
    if ul_lord:
        lp = k.planet(str(ul_lord))
        if lp:
            lh = lp.get("house")
            lord_conjs = [
                str(p["name"])
                for p in k.k.get("planets") or []
                if p.get("name") != ul_lord and p.get("house") == lh
            ]
    aspects_on_sign = _aspecting_planets_to_sign(k, ul_idx) if ul_idx is not None else []

    score_delta = 0
    notes: list[str] = []
    mal_asp = [a for a in aspects_on_lord if a in MALEFIC]
    ben_asp = [a for a in aspects_on_lord if a in BENEFIC]
    if mal_asp:
        score_delta -= 3
        notes.append(f"Malefics aspect UL lord {ul_lord}: {', '.join(mal_asp)}.")
    if ben_asp:
        score_delta += 2
        notes.append(f"Benefics aspect UL lord {ul_lord}: {', '.join(ben_asp)}.")
    mal_ul = [a for a in aspects_on_sign if a in MALEFIC]
    if mal_ul:
        score_delta -= 2
        notes.append(f"Malefics aspect Upapada sign: {', '.join(mal_ul)}.")
    if lord_conjs:
        if any(c in MALEFIC for c in lord_conjs):
            score_delta -= 3
            notes.append(f"UL lord conjunct {', '.join(lord_conjs)}.")

    return {
        "aspects_on_ul_lord": aspects_on_lord,
        "ul_lord_conjunctions": lord_conjs,
        "aspects_on_ul_sign": aspects_on_sign,
        "score_delta": score_delta,
        "depth_note": notes[0] if notes else "",
    }


def _maraka_axis_block(k: KundliReader) -> dict[str, Any]:
    h2l, h8l = k.house_lord(2), k.house_lord(8)
    occ2 = k.occupants(2)
    occ8 = k.occupants(8)
    score_delta = 0
    notes: list[str] = []
    for label, lord in (("2nd", h2l), ("8th", h8l)):
        p = k.planet(lord)
        if not p:
            continue
        house = p.get("house")
        dig = k.dignity(lord, k.sidx(p.get("sign") or "Aries"))
        if house == 7:
            score_delta -= 7
            notes.append(f"{lord} ({label} maraka) in 7th — family/longevity load sits on marriage house.")
        elif house in DUSTHANA:
            score_delta -= 4
            notes.append(f"{label} maraka lord {lord} in dusthana {house} — in-law/family friction theme.")
        elif dig >= 1 and house in {1, 4, 5, 9, 10, 11}:
            score_delta += 2
            notes.append(f"{label} maraka lord {lord} dignified — family axis manageable.")
    for label, occ in (("2nd", occ2), ("8th", occ8)):
        if not occ:
            continue
        malefics = [p for p in occ if p in MALEFIC]
        benefics = [p for p in occ if p in BENEFIC]
        if malefics:
            score_delta -= 5 * len(malefics)
            notes.append(
                f"{label} house occupied by malefic(s) {', '.join(malefics)} — maraka pressure in family axis."
            )
        if benefics:
            score_delta += 2 * len(benefics)
            notes.append(
                f"{label} house has benefic(s) {', '.join(benefics)} — family axis cushioned."
            )
    return {
        "second_lord": h2l,
        "eighth_lord": h8l,
        "second_occupants": occ2,
        "eighth_occupants": occ8,
        "score_delta": score_delta,
        "notes": notes,
        "note": notes[0] if notes else "2nd/8th maraka lords not pressuring 7th directly.",
    }


def _empty_seventh_block(
    occupants: list[str],
    dignity: int,
    lord_house: int | None,
) -> dict[str, Any]:
    if occupants:
        return {"empty": False, "score_delta": 0, "note": None}
    if dignity >= 1 and lord_house in {1, 4, 5, 7, 9, 10, 11}:
        return {
            "empty": True,
            "score_delta": 4,
            "note": "7th empty but 7th lord strong — bond rides on lord, clean but lord-dependent.",
        }
    if dignity <= -2 or lord_house in DUSTHANA:
        return {
            "empty": True,
            "score_delta": -7,
            "note": "7th empty + weak 7th lord — marriage axis lacks visible and structural anchor.",
        }
    return {
        "empty": True,
        "score_delta": -2,
        "note": "7th empty — all partnership results flow through 7th lord only.",
    }


def _d9_seventh_occupants(kundli: dict) -> dict[str, Any]:
    d9 = ((kundli.get("divisionalCharts") or {}).get("D9")) or {}
    asc = d9.get("ascendant")
    if not isinstance(asc, str) or asc not in SIGNS:
        for p in d9.get("planets") or []:
            if isinstance(p.get("name"), str) and str(p["name"]).lower().startswith("lagna"):
                asc = p.get("sign")
                break
    if not isinstance(asc, str) or asc not in SIGNS:
        return {"available": False, "occupants": [], "note": "D9 7th occupants unavailable."}
    asc_idx = SIGNS.index(asc)
    occ: list[str] = []
    for p in d9.get("planets") or []:
        if not isinstance(p, dict):
            continue
        nm = p.get("name")
        if not nm or str(nm).lower().startswith("lagna"):
            continue
        si = p.get("signIndex")
        if si is None and isinstance(p.get("sign"), str):
            si = SIGNS.index(p["sign"]) if p["sign"] in SIGNS else None
        if si is None:
            continue
        if ((int(si) - asc_idx) % 12) + 1 == 7:
            occ.append(str(nm))
    malefics = [p for p in occ if p in MALEFIC]
    benefics = [p for p in occ if p in BENEFIC]
    note = (
        f"D9 7th has {', '.join(occ)} — inner married-life tone carries these planets."
        if occ else "D9 7th empty — inner bond tone follows D9 7th lord only."
    )
    score_delta = 3 * len(benefics) - 4 * len(malefics)
    return {
        "available": True,
        "occupants": occ,
        "benefics": benefics,
        "malefics": malefics,
        "score_delta": score_delta,
        "note": note,
    }


def _houses_ruled_by(k: KundliReader, planet: str) -> list[int]:
    asc = k.asc_index()
    out: list[int] = []
    for hi, lord in enumerate(SIGN_LORDS):
        if lord == planet:
            out.append(((hi - asc) % 12) + 1)
    return sorted(out)


def _lordship_profile(k: KundliReader, planet: str) -> dict[str, Any]:
    houses = _houses_ruled_by(k, planet)
    dusthana_rules = [h for h in houses if h in DUSTHANA]
    good_rules = [h for h in houses if h in GOOD_LORDSHIP_HOUSES]
    if dusthana_rules and not good_rules:
        tier = "dusthana_lord"
    elif dusthana_rules and good_rules:
        tier = "mixed_lord"
    elif good_rules:
        tier = "supportive_lord"
    else:
        tier = "neutral_lord"
    return {
        "rules_houses": houses,
        "dusthana_rules": dusthana_rules,
        "good_rules": good_rules,
        "tier": tier,
    }


def _evaluate_seventh_influence(
    k: KundliReader,
    planet: str,
    *,
    from_aspect: bool = False,
    orb_multiplier: float = 1.0,
    orb_degrees: float | None = None,
) -> dict[str, Any]:
    """Functional benefic/malefic + lordship + occupant dignity on 7th influence."""
    natural_raw = (
        "benefic" if planet in BENEFIC
        else "malefic" if planet in MALEFIC
        else "neutral"
    )
    natural, is_yogakaraka = _functional_nature(k, planet)
    lordship = _lordship_profile(k, planet)
    tier = lordship["tier"]
    dusthana_rules = lordship["dusthana_rules"]
    good_rules = lordship["good_rules"]
    rules_txt = ", ".join(str(h) for h in lordship["rules_houses"]) or "—"
    aspect_scale = orb_multiplier if from_aspect else 1.0

    if natural == "benefic":
        if tier == "dusthana_lord":
            effect = "weakened_benefic"
            score_delta = int(round((2 if not from_aspect else 1) * aspect_scale))
            note = (
                f"{planet} is benefic{' (yogakaraka)' if is_yogakaraka else ''} in/aspecting 7th but rules dusthana "
                f"({', '.join(str(h) for h in dusthana_rules)}) — shubh effect reduced."
            )
        elif tier == "mixed_lord":
            effect = "mixed_benefic"
            score_delta = int(round((4 if not from_aspect else 2) * aspect_scale))
            note = (
                f"{planet} benefic in/aspecting 7th with mixed lordship "
                f"(good {', '.join(str(h) for h in good_rules)} · dusthana "
                f"{', '.join(str(h) for h in dusthana_rules)}) — partial support."
            )
        else:
            effect = "strong_benefic"
            score_delta = int(round((6 if not from_aspect else 3) * aspect_scale))
            note = (
                f"{planet} benefic{' (yogakaraka)' if is_yogakaraka else ''} in/aspecting 7th "
                f"rules supportive houses ({rules_txt}) — clean partnership support."
            )
    elif natural == "malefic":
        if is_yogakaraka:
            effect = "functional_benefic"
            score_delta = int(round((5 if not from_aspect else 3) * aspect_scale))
            note = f"{planet} yogakaraka in/aspecting 7th — functional benefic despite natural malefic tag."
        elif tier == "supportive_lord":
            effect = "softened_malefic"
            score_delta = int(round((-5 if not from_aspect else -3) * aspect_scale))
            note = (
                f"{planet} malefic in/aspecting 7th but rules good houses ({rules_txt}) — "
                "pressure present but functional role softens it."
            )
        elif tier == "dusthana_lord":
            effect = "harsh_malefic"
            score_delta = int(round((-11 if not from_aspect else -6) * aspect_scale))
            note = (
                f"{planet} malefic in/aspecting 7th and dusthana lord "
                f"({', '.join(str(h) for h in dusthana_rules)}) — strong marriage pressure."
            )
        else:
            effect = "malefic"
            score_delta = int(round((-9 if not from_aspect else -5) * aspect_scale))
            note = f"{planet} malefic in/aspecting 7th — conflict/delay themes."
    else:
        effect = "neutral"
        score_delta = 0
        note = f"{planet} neutral influence on 7th."

    cond: dict[str, Any] = {}
    if not from_aspect:
        cond = _occupant_condition_modifiers(k, planet)
        score_delta += cond["score_delta"]
        if cond["notes"]:
            note = f"{note} {' '.join(cond['notes'])}"

    return {
        "planet": planet,
        "source": "aspect" if from_aspect else "occupant",
        "natural": natural_raw,
        "functional": natural,
        "is_yogakaraka": is_yogakaraka,
        "rules_houses": lordship["rules_houses"],
        "dusthana_rules": dusthana_rules,
        "good_rules": good_rules,
        "lordship_tier": tier,
        "effect": effect,
        "score_delta": score_delta,
        "orb_degrees": orb_degrees if from_aspect else None,
        "orb_weight": round(orb_multiplier, 2) if from_aspect else 1.0,
        "dignity_word": cond.get("dignity_word"),
        "combust": cond.get("combust"),
        "retrograde": cond.get("retrograde"),
        "note": note,
    }


def _build_seventh_influences(k: KundliReader) -> dict[str, Any]:
    occupants = k.occupants(7)
    aspects = k.aspects_house(7)
    occupant_details = [_evaluate_seventh_influence(k, p, from_aspect=False) for p in occupants]
    aspect_details = []
    for p in aspects:
        if p in occupants:
            continue
        mult, orb_deg = _aspect_orb_multiplier(k, p, 7)
        aspect_details.append(
            _evaluate_seventh_influence(
                k, p, from_aspect=True, orb_multiplier=mult, orb_degrees=orb_deg,
            )
        )
    all_details = occupant_details + aspect_details

    score_delta = sum(d["score_delta"] for d in all_details)
    strong_benefic = sum(1 for d in all_details if d["effect"] == "strong_benefic")
    weakened_benefic = sum(1 for d in all_details if d["effect"] in ("weakened_benefic", "mixed_benefic"))
    harsh_malefic = sum(1 for d in all_details if d["effect"] in ("harsh_malefic", "malefic"))
    softened_malefic = sum(1 for d in all_details if d["effect"] == "softened_malefic")

    benefics_raw = [p for p in occupants if _functional_nature(k, p)[0] == "benefic"]
    malefics_raw = [p for p in occupants if _functional_nature(k, p)[0] == "malefic"]

    if weakened_benefic and not strong_benefic:
        lordship_summary = (
            f"Benefic(s) in 7th ({', '.join(benefics_raw) or '—'}) lose strength — "
            "they rule dusthana/mixed houses."
        )
    elif weakened_benefic:
        lordship_summary = (
            f"Mixed 7th read: {strong_benefic} clean benefic, {weakened_benefic} weakened by lordship."
        )
    elif strong_benefic:
        lordship_summary = "7th benefics carry clean lordship — partnership support is real."
    elif harsh_malefic:
        lordship_summary = "7th malefic pressure amplified by dusthana lordship."
    else:
        lordship_summary = "7th influence is moderate after lordship weighting."

    return {
        "occupant_details": occupant_details,
        "aspect_details": aspect_details,
        "score_delta": score_delta,
        "strong_benefic_count": strong_benefic,
        "weakened_benefic_count": weakened_benefic,
        "harsh_malefic_count": harsh_malefic,
        "softened_malefic_count": softened_malefic,
        "lordship_summary": lordship_summary,
        "benefics_in_seventh_raw": benefics_raw,
        "malefics_in_seventh_raw": malefics_raw,
    }


def _planets_for_dosh(planets: list | None) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for p in planets or []:
        if not isinstance(p, dict):
            continue
        q = dict(p)
        if q.get("sign_idx") is None and q.get("signIndex") is not None:
            q["sign_idx"] = q["signIndex"]
        out.append(q)
    return out


def _manglik_profile(kundli: dict) -> dict[str, Any]:
    """BPHS mangal dosh with cancellation rules (from dosh_deep)."""
    out: dict[str, Any] = {
        "has_dosh": False,
        "effective": "none",
        "severity": "none",
        "sources": [],
        "cancellations": [],
        "note": "No Mangal dosh detected.",
    }
    if not isinstance(kundli, dict):
        return out
    asc = kundli.get("ascendant")
    if not isinstance(asc, str) or asc not in SIGNS:
        return out
    asc_idx = SIGNS.index(asc)
    pmap = dosh_norm(_planets_for_dosh(kundli.get("planets")), asc_idx)
    entries = mangal_dosh_full(pmap, asc_idx)
    if not entries:
        return out

    sources: list[str] = []
    cancellations: list[str] = []
    for e in entries:
        name = str(e.get("name") or "")
        detail = str(e.get("detail") or "")
        if "Cancellation" in name:
            cancellations.append(detail)
        else:
            sources.append(detail or name)

    has_dosh = bool(sources)
    has_cancel = bool(cancellations)
    high = any(
        str(e.get("severity") or "").upper() == "HIGH"
        for e in entries
        if "Cancellation" not in str(e.get("name") or "")
    )

    if has_dosh and has_cancel:
        effective = "reduced"
        severity = "reduced"
        note = "Mangal dosh present but cancellation/reduction rules apply."
    elif has_dosh:
        effective = "active"
        severity = "high" if high else "medium"
        note = "Mangal dosh active — heated marriage axis unless consciously managed."
    else:
        effective = "none"
        severity = "none"
        note = "No Mangal dosh detected."

    out.update({
        "has_dosh": has_dosh,
        "effective": effective,
        "severity": severity,
        "sources": sources,
        "cancellations": cancellations,
        "note": note,
    })
    return out


def _manglik_score_delta(profile: dict[str, Any]) -> int:
    eff = profile.get("effective")
    if eff == "active":
        return -8 if profile.get("severity") == "high" else -5
    if eff == "reduced":
        return -2
    return 0


def _person_signals_block(sig: PersonSignals) -> dict[str, Any]:
    return {
        "affliction_weight": sig.affliction_weight,
        "loyalty_risk_high": sig.loyalty_risk_high,
        "third_person_risk": sig.third_person_risk,
        "separation_yoga": sig.separation_yoga,
        "reconnection_yoga": sig.reconnection_yoga,
        "venus_mars_conjunct": sig.venus_mars_conjunct,
        "venus_mars_conjunct_tight": sig.venus_mars_conjunct_tight,
        "moon_in_8th": sig.moon_in_8th,
        "moon_afflicted": sig.moon_afflicted,
        "venus_debil": sig.venus_debil,
        "venus_afflicted": sig.venus_afflicted,
        "d9_seventh_lord_weak": sig.d9_seventh_lord_weak,
        "seventh_lord_dusthana": sig.seventh_lord_dusthana,
        "seventh_lord_debil": sig.seventh_lord_debil,
        "saturn_on_7th": sig.saturn_on_7th,
        "saturn_on_7th_as_lord": sig.saturn_on_7th_as_lord,
        "rahu_on_7th_axis": sig.rahu_on_7th_axis,
        "ketu_detachment": sig.ketu_detachment,
        "key_notes": sig.notes[:6],
    }


def _signal_readiness_adjustment(sig: PersonSignals) -> int:
    """Map full affliction_weight into readiness score (capped)."""
    penalty = min(28, int(round(sig.affliction_weight * 0.38)))
    bonus = 0
    if sig.reconnection_yoga:
        bonus += 3
    if sig.venus_d9_exalted:
        bonus += 2
    if sig.moon_d9_exalted:
        bonus += 2
    if sig.saturn_on_7th_as_lord:
        bonus += 2
    return bonus - penalty


def _marriage_signal_adjustment(sig: PersonSignals) -> int:
    """
    Loyalty/secrecy/emotional layers only — skip weights already priced in
    D1 7th influences, 7L dignity/house, D9 maturity, KP, manglik.
    Prevents double-negative (e.g. Saturn on 7th counted twice).
    """
    overlap = 0
    if sig.seventh_lord_dusthana:
        overlap += 12
    if sig.seventh_lord_debil:
        overlap += 10
    if sig.saturn_on_7th:
        overlap += 11
    if sig.mars_on_7th:
        overlap += 9
    if sig.rahu_on_7th_axis:
        overlap += 10
    if sig.ketu_detachment:
        overlap += 7
    if sig.d9_seventh_lord_weak:
        overlap += 10

    net_weight = max(0, sig.affliction_weight - overlap)
    penalty = min(18, int(round(net_weight * 0.35)))
    bonus = 0
    if sig.reconnection_yoga:
        bonus += 3
    if sig.venus_d9_exalted:
        bonus += 2
    if sig.moon_d9_exalted:
        bonus += 2
    if sig.saturn_on_7th_as_lord:
        bonus += 2
    return bonus - penalty


def _synastry_summary(syn: dict[str, Any]) -> str:
    if not syn.get("available"):
        return "7th-lord synastry unavailable."
    bits: list[str] = []
    p1x = syn.get("p1_7l_in_p2_chart") or {}
    p2x = syn.get("p2_7l_in_p1_chart") or {}
    if p1x.get("available") and p1x.get("house"):
        bits.append(f"P1 7L in P2 chart house {p1x['house']}")
    if p2x.get("available") and p2x.get("house"):
        bits.append(f"P2 7L in P1 chart house {p2x['house']}")
    score = syn.get("score_0_10")
    if score is not None:
        bits.append(f"synastry {score}/10")
    drivers = syn.get("drivers") or []
    if drivers:
        bits.append(drivers[0])
    return " · ".join(bits) if bits else "Synastry computed."


def _d9_sync_summary(sync: dict[str, Any], d9_1: float, d9_2: float) -> str:
    if sync.get("available"):
        notes = sync.get("notes") or []
        head = f"D9 depth A {d9_1}/10 · B {d9_2}/10 · sync {sync.get('score_0_10', 5)}/10"
        if notes:
            return f"{head} — {notes[0]}"
        return head
    return f"D9 depth A {d9_1}/10 · B {d9_2}/10"


def _couple_manglik_note(p1: dict[str, Any], p2: dict[str, Any]) -> dict[str, Any]:
    m1 = p1.get("manglik") or {}
    m2 = p2.get("manglik") or {}
    e1 = m1.get("effective", "none")
    e2 = m2.get("effective", "none")
    has1 = bool(m1.get("has_dosh"))
    has2 = bool(m2.get("has_dosh"))
    mutual = has1 and has2
    imbalance = (e1 == "active" and e2 == "none") or (e2 == "active" and e1 == "none")

    if mutual:
        note = "Both charts carry Mangal dosh — classical mutual cancellation applies."
    elif e1 == "active" or e2 == "active":
        who = p1.get("name") if e1 == "active" else p2.get("name")
        note = f"Only {who} has active Mangal dosh — imbalance; remedy advised."
    elif e1 == "reduced" or e2 == "reduced":
        note = "Mangal dosh present with reduction/cancellation on one or both charts."
    else:
        note = "No active Mangal dosh imbalance between partners."

    return {
        "p1_has_dosh": has1,
        "p2_has_dosh": has2,
        "p1_effective": e1,
        "p2_effective": e2,
        "mutual_cancellation": mutual,
        "imbalance": imbalance,
        "note": note,
    }


def _lord_strength_word(dignity: int, house: int | None) -> str:
    score = dignity
    if house in DUSTHANA:
        score -= 2
    elif house in {1, 4, 5, 7, 9, 10, 11}:
        score += 1
    if score >= 2:
        return "strong"
    if score >= 0:
        return "moderate"
    return "weak"


def _band_from_score(score: int) -> Band:
    if score >= 68:
        return "Strong"
    if score >= 48:
        return "Moderate"
    return "Strained"


def _couple_band(score: int) -> CoupleBand:
    if score >= 65:
        return "Promising"
    if score >= 48:
        return "Workable"
    return "High Effort"


def _d9_band(maturity: float) -> str:
    if maturity >= 7:
        return "Supportive"
    if maturity >= 5:
        return "Mixed"
    return "Weak"


def _kp_depth(verdict: str) -> str:
    return {
        "STRONG": "strong",
        "PARTIAL": "partial",
        "WEAK": "weak",
        "UNAVAILABLE": "unavailable",
    }.get(verdict, "unavailable")


def _lordship_note(lord: str, houses: list[int]) -> str:
    if not houses:
        return f"{lord} lordship data unavailable."
    htxt = ", ".join(str(h) for h in houses)
    marriage_h = 7 in houses
    if marriage_h and len(houses) == 1:
        return f"{lord} rules only the 7th — marriage themes dominate this planet's expression."
    if marriage_h:
        return f"{lord} rules houses {htxt} — partnership links with other life areas (not isolated)."
    return f"{lord} rules houses {htxt} — marriage flows through those house themes."


def _karaka_planet(gender: Gender) -> str:
    if gender == "female":
        return "Jupiter"
    if gender == "male":
        return "Venus"
    return "Venus"


def _friction_and_remedy(
    k: KundliReader,
    gender: Gender,
    sig: PersonSignals,
    kp: dict[str, Any],
    ul: dict[str, Any],
    manglik: dict[str, Any],
) -> tuple[str, str, list[str], list[str]]:
    pressures: list[str] = []
    strengths: list[str] = []

    h7l = k.house_lord(7)
    p7l = k.planet(h7l)
    seventh_inf = _build_seventh_influences(k)
    benefics = seventh_inf["benefics_in_seventh_raw"]
    malefics = seventh_inf["malefics_in_seventh_raw"]

    for det in seventh_inf["occupant_details"]:
        if det["effect"] == "strong_benefic":
            strengths.append(det["note"])
        elif det["effect"] in ("weakened_benefic", "mixed_benefic"):
            pressures.append(det["note"])
        elif det["effect"] in ("harsh_malefic", "malefic"):
            pressures.append(det["note"])
        elif det["effect"] == "softened_malefic":
            strengths.append(det["note"])

    for det in seventh_inf["aspect_details"]:
        if det["effect"] == "strong_benefic":
            strengths.append(f"Aspect: {det['note']}")
        elif det["effect"] in ("weakened_benefic", "mixed_benefic", "harsh_malefic", "malefic"):
            pressures.append(f"Aspect: {det['note']}")
        elif det["effect"] == "softened_malefic":
            strengths.append(f"Aspect: {det['note']}")

    if seventh_inf["weakened_benefic_count"] and not seventh_inf["strong_benefic_count"]:
        pressures.append(seventh_inf["lordship_summary"])
    elif seventh_inf["strong_benefic_count"]:
        strengths.append(seventh_inf["lordship_summary"])

    if p7l and p7l.get("house") in DUSTHANA:
        pressures.append(f"7th lord {h7l} in dusthana house {p7l.get('house')} — bond needs structural patience.")
    elif p7l and p7l.get("house") in {1, 4, 5, 7, 10, 11}:
        strengths.append(f"7th lord {h7l} in supportive house {p7l.get('house')}.")
    if k.is_combust(h7l):
        pressures.append(
            f"7th lord {h7l} combust — marriage significator weakened despite sign placement."
        )
    if k.is_retrograde(h7l):
        pressures.append(
            f"7th lord {h7l} retrograde (Vakri) — karmic delays or past-pattern replay in partnership."
        )

    if manglik.get("effective") == "active":
        pressures.append(manglik.get("note") or "Mangal dosh active on marriage axis.")
    elif manglik.get("effective") == "reduced":
        strengths.append(manglik.get("note") or "Mangal dosh reduced by cancellation rules.")

    for n in sig.notes:
        if any(w in n.lower() for w in ("weak", "debilitated", "dusthana", "distance", "fight", "confusion", "risk", "strain", "secret", "detach", "unstable", "afflict")):
            if n not in pressures:
                pressures.append(n)
        elif any(w in n.lower() for w in ("strong", "supportive", "harmony", "aligned", "loyalty", "reconnection", "committed", "stable")):
            if n not in strengths:
                strengths.append(n)

    if gender == "female":
        jup = k.planet("Jupiter")
        if jup:
            jd = k.dignity("Jupiter", k.sidx(jup["sign"]))
            if jd >= 1:
                strengths.append("Jupiter (husband karaka) well placed — pati-significator supportive.")
            elif jd <= -2:
                pressures.append("Jupiter debilitated — husband-significator needs remedy support.")
    elif gender == "male":
        ven = k.planet("Venus")
        if ven:
            vd = k.dignity("Venus", k.sidx(ven["sign"]))
            if vd >= 1:
                strengths.append("Venus (wife karaka) well placed — spouse-significator supportive.")
            elif vd <= -2:
                pressures.append("Venus debilitated — wife-significator needs conscious nurture.")

    kv = kp.get("verdict")
    if kv == "WEAK":
        pressures.append("KP 7th cusp chain weak — commitment may need time to solidify.")
    elif kv == "STRONG":
        strengths.append("KP 7th cusp supports marriage promise on structural level.")

    ul_v = str(ul.get("verdict") or "")
    if "STRAINED" in ul_v.upper():
        pressures.append("Upapada shows strain — marriage manifestation needs realistic pacing.")
    elif "STABLE" in ul_v.upper():
        strengths.append("Upapada supports stable marriage manifestation.")

    friction = pressures[0] if pressures else "No major structural friction flagged — still nurture communication daily."
    remedy = _pick_remedy(k, gender, pressures)
    return friction, remedy, strengths[:5], pressures[:6]


def _pick_remedy(k: KundliReader, gender: Gender, pressures: list[str]) -> str:
    blob = " ".join(pressures).lower()
    if "saturn" in blob or "distance" in blob or "delay" in blob:
        return "Saturday discipline: sesame-oil lamp, patience rituals, no ultimatums on Saturdays."
    if "mars" in blob or "manglik" in blob or "fight" in blob:
        return "Tuesday Hanuman Chalisa; cool-down rule before replying in anger."
    if "rahu" in blob or "ketu" in blob or "confusion" in blob:
        return "Thursday Vishnu quiet time; reduce impulsive relationship decisions."
    if "venus" in blob and gender == "male":
        return "Friday white sweets + Venus mantra; express appreciation without score-keeping."
    if "jupiter" in blob and gender == "female":
        return "Thursday yellow charity; honour wisdom and elders in partner choices."
    if "debilitated" in blob or "dusthana" in blob:
        return "Strengthen 7th lord day (planet weekday) with simple daan + consistent boundaries."
    h7l = k.house_lord(7)
    weekday = {
        "Sun": "Sunday", "Moon": "Monday", "Mars": "Tuesday", "Mercury": "Wednesday",
        "Jupiter": "Thursday", "Venus": "Friday", "Saturn": "Saturday",
    }.get(h7l, "Friday")
    return f"{weekday} light for 7th lord {h7l}; joint ritual with partner weekly."


def _analyze_partner(kundli: dict, *, name: str, gender: Gender) -> dict[str, Any]:
    k = KundliReader({**kundli, "name": name})
    manglik = _manglik_profile(kundli)
    asc = k.asc_index()
    h7_sign = SIGNS[(asc + 6) % 12]
    h7l = k.house_lord(7)
    p7l = k.planet(h7l)
    h7_occ = k.occupants(7)
    asp7 = k.aspects_house(7)
    seventh_inf = _build_seventh_influences(k)
    benefics = seventh_inf["benefics_in_seventh_raw"]
    malefics = seventh_inf["malefics_in_seventh_raw"]
    lord_houses = _houses_ruled_by(k, h7l)

    dignity = 0
    lord_sign = None
    lord_house = None
    h7l_combust = False
    h7l_retro = False
    if p7l:
        lord_sign = p7l.get("sign")
        lord_house = p7l.get("house")
        dignity = k.dignity(h7l, k.sidx(lord_sign or "Aries"))
        h7l_combust = k.is_combust(h7l)
        h7l_retro = k.is_retrograde(h7l)

    d9 = d9_per_partner(kundli)
    d9_occ7 = _d9_seventh_occupants(kundli)
    maraka = _maraka_axis_block(k)
    empty7 = _empty_seventh_block(h7_occ, dignity, lord_house)
    kp = compute_kp_marriage_promise(kundli)
    sig = _analyze_person(k)

    karakas = compute_karakas(kundli.get("planets") or [])
    dk_planet = karakas.get("DK")
    dk_block = _build_darakaraka_block(k, dk_planet)

    arudha = compute_arudha_padas(kundli.get("planets") or [], kundli.get("ascendant"))
    ul = compute_upapada(arudha, kundli.get("planets") or []) if arudha else {}
    ul_depth = _upapada_depth(k, ul)
    ul_stability = "neutral"
    if ul:
        vs = str(ul.get("verdict") or "")
        if "STABLE" in vs.upper():
            ul_stability = "stable"
        elif "STRAINED" in vs.upper():
            ul_stability = "strained"
        elif "MIXED" in vs.upper():
            ul_stability = "mixed"

    karaka_name = _karaka_planet(gender)
    karaka_p = k.planet(karaka_name)
    karaka_block: dict[str, Any] = {
        "primary": karaka_name,
        "role": "wife karaka" if gender == "male" else "husband karaka" if gender == "female" else "relationship karaka",
        "sign": None,
        "house": None,
        "dignity": "unknown",
        "strength": "unknown",
        "note": f"{karaka_name} data unavailable.",
    }
    if karaka_p:
        kd = k.dignity(karaka_name, k.sidx(karaka_p.get("sign") or "Aries"))
        karaka_block.update({
            "sign": karaka_p.get("sign"),
            "house": karaka_p.get("house"),
            "dignity": k.dignity_word(kd),
            "strength": _lord_strength_word(kd, karaka_p.get("house")),
            "note": f"{karaka_name} ({karaka_block['role']}) in {karaka_p.get('sign')} house {karaka_p.get('house')}.",
        })

    score = _MARRIAGE_BASE
    score += seventh_inf["score_delta"]
    score += empty7["score_delta"]
    score += maraka["score_delta"]
    score += dk_block.get("score_delta", 0)
    score += ul_depth.get("score_delta", 0)
    if d9_occ7.get("available"):
        score += d9_occ7.get("score_delta", 0)

    score += {2: 12, 1: 7, 0: 0, -2: -14}.get(dignity, 0)
    if h7l_combust:
        score -= 6
    if h7l_retro:
        score -= 3
    if lord_house in DUSTHANA:
        score -= 10
    elif lord_house in {1, 4, 5, 7, 9, 10, 11}:
        score += 6

    if d9.get("available"):
        score += int(round((float(d9.get("marriage_maturity_0_10") or 5) - 5) * 3))

    kv = kp.get("verdict")
    if kv == "STRONG":
        score += 10
    elif kv == "PARTIAL":
        score += 4
    elif kv == "WEAK":
        score -= 8

    if ul_stability == "stable":
        score += 6
    elif ul_stability == "strained":
        score -= 8

    if karaka_p:
        kd = k.dignity(karaka_name, k.sidx(karaka_p.get("sign") or "Aries"))
        if kd >= 1:
            score += 8
        elif kd <= -2:
            score -= 10

    score += _manglik_score_delta(manglik)
    score += _marriage_signal_adjustment(sig)
    score = max(0, min(100, score))
    if score < _MARRIAGE_READINESS_FLOOR:
        score = _MARRIAGE_READINESS_FLOOR

    friction, remedy, strengths, pressures = _friction_and_remedy(k, gender, sig, kp, ul, manglik)
    critical = _critical_alerts_block(sig)
    friction = _sanitize_friction(friction, critical)
    dasha_tl = _partner_dasha_timeline(kundli, name)

    gender_flags: list[str] = []
    if h7l_combust:
        gender_flags.append("7th lord combust — promise weakens despite sign strength")
    if h7l_retro:
        gender_flags.append("7th lord retrograde — karmic delay pattern")
    if manglik.get("effective") == "active":
        gender_flags.append("Mangal dosh active")
    elif manglik.get("effective") == "reduced":
        gender_flags.append("Mangal dosh reduced/cancelled")
    if sig.separation_yoga:
        gender_flags.append("Separation yoga pattern")
    if sig.d9_seventh_lord_weak:
        gender_flags.append("D9 7th lord weak")
    if gender == "female" and karaka_p and k.dignity("Jupiter", k.sidx(karaka_p.get("sign") or "Aries")) <= -2:
        gender_flags.append("Jupiter husband-karaka under pressure")
    if gender == "male" and karaka_p and k.dignity("Venus", k.sidx(karaka_p.get("sign") or "Aries")) <= -2:
        gender_flags.append("Venus wife-karaka under pressure")
    if sig.seventh_lord_dusthana:
        gender_flags.append("7th lord in dusthana")
    if sig.saturn_on_7th:
        gender_flags.append("Saturn on 7th axis")

    safe_flags = _sanitize_display_flags(gender_flags)
    safe_pressures = [p for p in pressures if not _is_sensitive_note(p)][:6]
    if critical.get("locked") and critical.get("teaser") not in safe_pressures:
        safe_pressures = [str(critical["teaser"]), *safe_pressures[:5]]

    payload: dict[str, Any] = {
        "name": name,
        "gender": gender,
        "readiness_score": score,
        "readiness_band": _band_from_score(score),
        "d1": {
            "seventh_house_sign": h7_sign,
            "planets_in_seventh": h7_occ,
            "benefics_in_seventh": benefics,
            "malefics_in_seventh": malefics,
            "aspects_on_seventh": asp7,
            "seventh_occupant_details": seventh_inf["occupant_details"],
            "seventh_aspect_details": seventh_inf["aspect_details"],
            "seventh_lordship_summary": seventh_inf["lordship_summary"],
            "seventh_influence_score_delta": seventh_inf["score_delta"],
            "seventh_lord": h7l,
            "seventh_lord_house": lord_house,
            "seventh_lord_sign": lord_sign,
            "seventh_lord_dignity": k.dignity_word(dignity),
            "seventh_lord_strength": _lord_strength_word(dignity, lord_house),
            "seventh_lord_combust": h7l_combust,
            "seventh_lord_retrograde": h7l_retro,
            "seventh_empty": empty7,
            "maraka_axis": maraka,
            "lordship_houses": lord_houses,
            "lordship_note": _lordship_note(h7l, lord_houses),
        },
        "d9": {
            "available": bool(d9.get("available")),
            "seventh_house_sign": d9.get("d9_7h_sign"),
            "seventh_lord": d9.get("d9_7h_lord"),
            "seventh_lord_sign": d9.get("d9_7l_sign"),
            "seventh_lord_house": d9.get("d9_7l_house"),
            "maturity_0_10": d9.get("marriage_maturity_0_10"),
            "band": _d9_band(float(d9.get("marriage_maturity_0_10") or 5)),
            "venus_dignity": d9.get("d9_venus_dignity"),
            "jupiter_dignity": d9.get("d9_jupiter_dignity"),
            "seventh_occupants": d9_occ7.get("occupants") or [],
            "seventh_occupants_note": d9_occ7.get("note"),
        },
        "darakaraka": dk_block,
        "upapada": {
            "available": bool(ul),
            "ul_sign": ul.get("ul_sign"),
            "ul_lord": ul.get("ul_lord"),
            "ul_lord_house_from_ul": ul.get("ul_lord_house"),
            "stability": ul_stability,
            "verdict": ul.get("verdict"),
            "occupants_ul": ul.get("occupants_ul") or [],
            "aspects_on_ul_lord": ul_depth.get("aspects_on_ul_lord") or [],
            "ul_lord_conjunctions": ul_depth.get("ul_lord_conjunctions") or [],
            "aspects_on_ul_sign": ul_depth.get("aspects_on_ul_sign") or [],
            "depth_note": ul_depth.get("depth_note") or "",
        },
        "kp": {
            "available": bool(kp.get("available")),
            "verdict": kp.get("verdict"),
            "commitment_depth": _kp_depth(str(kp.get("verdict") or "UNAVAILABLE")),
            "seven_csl": kp.get("seven_csl"),
            "signified_houses": kp.get("signified_houses") or [],
            "promise_hits": kp.get("promise_hits", 0),
            "negation_hits": kp.get("negation_hits", 0),
        },
        "karaka": karaka_block,
        "manglik": manglik,
        "dasha_timeline": dasha_tl,
        "critical_alerts": critical,
        "relationship_signals": _person_signals_block(sig),
        "relationship_signals_safe": _person_signals_block_safe(sig),
        "gender_flags": safe_flags,
        "friction": friction,
        "remedy": remedy,
        "strengths": strengths,
        "pressures": safe_pressures,
    }
    payload["plain_copy"] = build_partner_plain_copy(
        payload, partner_copy_seed(kundli, name)
    )
    return payload


def _couple_verdict(band: CoupleBand, p1: dict, p2: dict) -> str:
    if band == "Promising":
        return (
            "Both marriage axes show supportive structure — if these two marry, "
            "long-term direction can grow well with steady effort."
        )
    if band == "Workable":
        return (
            "Marriage is workable but not effortless — strengths exist on both sides; "
            "friction points need conscious handling after wedding."
        )
    return (
        "High effort match — marriage is possible but demands patience, remedies, "
        "and realistic expectations on both charts."
    )


def compute_marriage_basics(
    kundli_p1: dict,
    kundli_p2: dict,
    *,
    p1_name: str = "Partner A",
    p2_name: str = "Partner B",
    p1_gender: str | None = None,
    p2_gender: str | None = None,
) -> dict[str, Any]:
    """Full deterministic Basic marriage payload for a couple."""
    g1 = normalize_gender(p1_gender)
    g2 = normalize_gender(p2_gender)
    person1 = _analyze_partner(kundli_p1, name=p1_name, gender=g1)
    person2 = _analyze_partner(kundli_p2, name=p2_name, gender=g2)

    d9_full = compute_d9_marriage(kundli_p1, kundli_p2)
    d9_sync = d9_full.get("sync") or {}
    pada_yoni = _nakshatra_pada_yoni_couple(kundli_p1, kundli_p2)
    synastry = compute_synastry_7l(kundli_p1, kundli_p2)
    couple_sig = analyze_couple(
        KundliReader({**kundli_p1, "name": p1_name}),
        KundliReader({**kundli_p2, "name": p2_name}),
    )
    manglik_couple = _couple_manglik_note(person1, person2)
    graha_maitri = _moon_graha_maitri(
        KundliReader({**kundli_p1, "name": p1_name}),
        KundliReader({**kundli_p2, "name": p2_name}),
    )
    kp_couple = compute_kp_couple_promise(kundli_p1, kundli_p2)

    d9_1 = float(person1["d9"].get("maturity_0_10") or 5)
    d9_2 = float(person2["d9"].get("maturity_0_10") or 5)

    # Couple structural = average of both partners (no synastry/D9/KP overlay on score).
    structural = int(round((person1["readiness_score"] + person2["readiness_score"]) / 2))
    structural = max(0, min(100, structural))
    if structural < _MARRIAGE_COUPLE_FLOOR:
        structural = _MARRIAGE_COUPLE_FLOOR
    couple_band = _couple_band(structural)

    return {
        "engine": "marriage_basics_v6",
        "couple": {
            "structural_score": structural,
            "structural_band": couple_band,
            "future_verdict": _couple_verdict(couple_band, person1, person2),
            "d9_sync_note": _d9_sync_summary(d9_sync, d9_1, d9_2),
            "d9_sync": {
                "available": bool(d9_sync.get("available")),
                "score_0_10": d9_sync.get("score_0_10"),
                "lagna_lord_relation": d9_sync.get("lagna_lord_relation"),
                "seven_lord_relation": d9_sync.get("seven_lord_relation"),
                "notes": d9_sync.get("notes") or [],
            },
            "synastry": {
                "available": bool(synastry.get("available")),
                "score_0_10": synastry.get("score_0_10"),
                "p1_7l": synastry.get("p1_7l"),
                "p2_7l": synastry.get("p2_7l"),
                "summary": _synastry_summary(synastry),
                "drivers": synastry.get("drivers") or [],
                "cautions": synastry.get("cautions") or [],
                "p1_7l_in_p2_house": (synastry.get("p1_7l_in_p2_chart") or {}).get("house"),
                "p2_7l_in_p1_house": (synastry.get("p2_7l_in_p1_chart") or {}).get("house"),
                "pada_yoni": pada_yoni,
            },
            "manglik": manglik_couple,
            "graha_maitri": graha_maitri,
            "kp_couple": {
                "available": bool(kp_couple.get("available")),
                "couple_verdict": kp_couple.get("couple_verdict"),
                "p1_verdict": (kp_couple.get("p1") or {}).get("verdict"),
                "p2_verdict": (kp_couple.get("p2") or {}).get("verdict"),
            },
            "dasha_timeline": {
                "p1": person1.get("dasha_timeline"),
                "p2": person2.get("dasha_timeline"),
            },
            "couple_signals": {
                "moon_mismatch": couple_sig.moon_mismatch,
                "cross_rahu_venus": couple_sig.cross_rahu_venus,
                "combined_affliction": couple_sig.combined_affliction,
                "synastry_notes": [
                    n for n in couple_sig.synastry_notes if not _is_sensitive_note(n)
                ] or (
                    [graha_maitri["note"]] if graha_maitri.get("available") else []
                ),
            },
            "critical_alerts_total": (
                int((person1.get("critical_alerts") or {}).get("count") or 0)
                + int((person2.get("critical_alerts") or {}).get("count") or 0)
                + (1 if couple_sig.cross_rahu_venus else 0)
            ),
        },
        "p1": person1,
        "p2": person2,
    }
