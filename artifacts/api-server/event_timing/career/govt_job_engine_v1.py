"""Government job promise + timing engine v1 — Sun-Saturn core axis.

Life promise (natal) runs first; dasha timing only when promise is not low.
Integrates with career_timing bucket `govt_job` via assess_govt_job().
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Optional

_SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]
_SIGN_LORDS = [
    "Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury",
    "Venus", "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter",
]
_STRONG_DIGNITY = frozenset({"exalted", "own-sign", "moolatrikona", "own sign", "moola-trikona"})
_KENDRA_TRIKONA = frozenset({1, 4, 5, 7, 9, 10})
_GOVT_DASHA_TARGETS = ("Sun", "Saturn", "Mercury", "Mars", "Jupiter")


def _norm(name: str) -> str:
    return (name or "").strip().capitalize()


def _planet_house(planets: list, planet_name: str) -> Optional[int]:
    for p in planets or []:
        if isinstance(p, dict) and p.get("name") == planet_name:
            h = p.get("house")
            if isinstance(h, int):
                return h
    return None


def _planet_sign(planets: list, planet_name: str) -> Optional[str]:
    for p in planets or []:
        if isinstance(p, dict) and p.get("name") == planet_name:
            s = p.get("sign")
            if isinstance(s, str) and s.strip():
                return s.strip().capitalize()
    return None


def _house_lord(intel: dict, house_num: int) -> Optional[str]:
    for h in intel.get("house_lords") or []:
        if isinstance(h, dict) and h.get("house") == house_num:
            return _norm(str(h.get("lord") or ""))
    return None


def _planet_dignity(intel: dict, planet_name: str) -> Optional[str]:
    for d in intel.get("dignities") or []:
        if isinstance(d, dict) and d.get("planet") == planet_name:
            return str(d.get("status") or d.get("dignity") or "").strip().lower()
    return None


def _is_strong_dignity(dignity: Optional[str]) -> bool:
    return bool(dignity and dignity.lower().replace("_", "-") in _STRONG_DIGNITY)


def _sign_lord(sign_name: Optional[str]) -> Optional[str]:
    if not sign_name:
        return None
    s = sign_name.strip().capitalize()
    if s not in _SIGNS:
        return None
    return _SIGN_LORDS[_SIGNS.index(s)]


def _divisional_planets(kundli: dict, chart: str) -> list:
    div = kundli.get("divisionalCharts") or {}
    block = div.get(chart) or {}
    return block.get("planets") or []


def _aspect_houses(planet: str, planet_house: int) -> set[int]:
    if not isinstance(planet_house, int) or not 1 <= planet_house <= 12:
        return set()
    out = {((planet_house - 1 + 6) % 12) + 1}
    if planet == "Mars":
        out.update({((planet_house - 1 + 3) % 12) + 1, ((planet_house - 1 + 7) % 12) + 1})
    elif planet == "Jupiter":
        out.update({((planet_house - 1 + 4) % 12) + 1, ((planet_house - 1 + 8) % 12) + 1})
    elif planet in ("Saturn", "Rahu", "Ketu"):
        out.update({((planet_house - 1 + 2) % 12) + 1, ((planet_house - 1 + 9) % 12) + 1})
    return out


def _sun_saturn_link(planets: list, chart_label: str, *, bonus: int = 0) -> tuple[int, list[str], list[str]]:
    """Conjunction, mutual 7th aspect, or parivartana between Sun and Saturn."""
    score = 0
    why: list[str] = []
    flags: list[str] = []
    sun_h = _planet_house(planets, "Sun")
    sat_h = _planet_house(planets, "Saturn")
    if not sun_h or not sat_h:
        return 0, why, flags

    if sun_h == sat_h:
        pts = 25 + bonus
        score += pts
        flags.append(f"sun_saturn_conjunct_{chart_label}")
        why.append(
            f"Sun-Saturn conjunct in h{sun_h} ({chart_label}) — "
            f"authority + service yoga (+{pts})"
        )
    elif abs(sun_h - sat_h) == 6:
        pts = 20 + bonus
        score += pts
        flags.append(f"sun_saturn_7th_{chart_label}")
        why.append(
            f"Sun-Saturn mutual 7th aspect ({chart_label}) — govt-power axis (+{pts})"
        )

    sun_sign = _planet_sign(planets, "Sun")
    sat_sign = _planet_sign(planets, "Saturn")
    if sun_sign and sat_sign and _sign_lord(sun_sign) == "Saturn" and _sign_lord(sat_sign) == "Sun":
        pts = 25 + bonus
        score += pts
        flags.append(f"sun_saturn_parivartana_{chart_label}")
        why.append(
            f"Sun-Saturn parivartana ({chart_label}) — classic sarkari yoga (+{pts})"
        )

    return score, why, flags


def _saturn_from_sun_trine(planets: list, chart_label: str, *, bonus: int = 0) -> tuple[int, list[str], list[str]]:
    sun_h = _planet_house(planets, "Sun")
    sat_h = _planet_house(planets, "Saturn")
    if not sun_h or not sat_h:
        return 0, [], []
    from_sun = ((sat_h - sun_h + 12) % 12) + 1
    if from_sun in (5, 9):
        pts = 15 + bonus
        msg = f"Saturn in {from_sun}th from Sun ({chart_label}) — kona govt support (+{pts})"
    elif from_sun == 2:
        pts = 10 + bonus
        msg = f"Saturn in 2nd from Sun ({chart_label}) — artha-axis govt support (+{pts})"
    else:
        return 0, [], []
    return pts, [msg], [f"saturn_trine_sun_{chart_label}"]


def _dasha_lords(kundli: dict) -> tuple[str, str, str]:
    cd = kundli.get("currentDasha") or {}
    md = str(
        cd.get("mahadasha") or cd.get("maha") or cd.get("MD") or cd.get("md_lord") or ""
    ).strip()
    ad = str(
        cd.get("antardasha") or cd.get("antar") or cd.get("AD") or cd.get("ad_lord") or ""
    ).strip()
    pd = str(
        cd.get("pratyantardasha") or cd.get("pratyantar") or cd.get("PD") or cd.get("pd_lord") or ""
    ).strip()
    return md, ad, pd


def _parse_iso(s: Any) -> Optional[datetime]:
    if not s:
        return None
    if isinstance(s, datetime):
        return s
    if isinstance(s, str):
        for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d", "%Y-%m-%dT%H:%M:%S.%f"):
            try:
                return datetime.strptime(s.split("+")[0].split("Z")[0], fmt)
            except (ValueError, TypeError):
                continue
    return None


def _scan_govt_dasha_windows(kundli: dict, lord_targets: set[str]) -> list[dict]:
    """Find upcoming AD rows where govt significators activate."""
    today = datetime.utcnow()
    horizon = today + timedelta(days=365 * 7)
    windows: list[dict] = []
    for top in kundli.get("dashas") or []:
        if not isinstance(top, dict):
            continue
        md = str(top.get("planet") or top.get("lord") or top.get("mahadasha") or "").strip()
        for ad_row in top.get("subDashas") or top.get("antardashas") or []:
            if not isinstance(ad_row, dict):
                continue
            ad = str(ad_row.get("planet") or ad_row.get("lord") or ad_row.get("antardasha") or "").strip()
            if ad not in lord_targets and md not in lord_targets:
                continue
            start = _parse_iso(ad_row.get("startDate") or ad_row.get("start"))
            end = _parse_iso(ad_row.get("endDate") or ad_row.get("end"))
            if not start or not end or end < today:
                continue
            if start > horizon:
                continue
            windows.append({
                "md": md,
                "ad": ad,
                "start": start.strftime("%Y-%m"),
                "end": end.strftime("%Y-%m"),
                "lords": "/".join(x for x in (md, ad) if x),
            })
    windows.sort(key=lambda w: w.get("start") or "")
    return windows[:3]


def assess_govt_job_promise(
    kundli: dict,
    intel: dict,
    *,
    karakas_d: Optional[dict] = None,
    kp_assist: Optional[dict] = None,
) -> dict:
    """Natal govt-job life promise — Sun-Saturn axis + D1/D9/D10."""
    planets = kundli.get("planets") or []
    d9 = _divisional_planets(kundli, "D9")
    d10 = _divisional_planets(kundli, "D10")

    score = 0
    why: list[str] = []
    flags: list[str] = []
    sun_sat_links: list[str] = []

    tenth_lord = _house_lord(intel, 10)
    sixth_lord = _house_lord(intel, 6)
    ninth_lord = _house_lord(intel, 9)

    # ── D1 Sun-Saturn core ───────────────────────────────────────────────
    pts, msgs, f = _sun_saturn_link(planets, "D1")
    score += pts
    why.extend(msgs)
    flags.extend(f)
    sun_sat_links.extend(f)

    pts, msgs, f = _saturn_from_sun_trine(planets, "D1")
    score += pts
    why.extend(msgs)
    flags.extend(f)

    # ── D9 confirm (+bonus) ────────────────────────────────────────────
    pts, msgs, f = _sun_saturn_link(d9, "D9", bonus=5)
    score += pts
    why.extend(msgs)
    flags.extend(f)

    sun_d9 = _planet_dignity(intel, "Sun")
    sat_d9 = _planet_dignity(intel, "Saturn")
    if _is_strong_dignity(sun_d9) and _is_strong_dignity(sat_d9):
        score += 30
        flags.append("d9_sun_saturn_both_strong")
        why.append("D9: Sun & Saturn both structurally strong — long-term govt stability (+30)")

    # ── D10 service trigger (+bonus) ───────────────────────────────────
    pts, msgs, f = _sun_saturn_link(d10, "D10", bonus=5)
    score += pts
    why.extend(msgs)
    flags.extend(f)

    pts, msgs, f = _saturn_from_sun_trine(d10, "D10", bonus=5)
    score += pts
    why.extend(msgs)
    flags.extend(f)

    sat_d10_h = _planet_house(d10, "Saturn")
    if sat_d10_h == 6:
        sat_d10_dgn = None
        for d in intel.get("dignities") or []:
            if isinstance(d, dict) and d.get("planet") == "Saturn":
                sat_d10_dgn = d.get("status")
                break
        pts = 20 if _is_strong_dignity(sat_d10_dgn) else 12
        score += pts
        flags.append("saturn_d10_6h")
        why.append(f"D10: Saturn in 6H — competition-beating service yoga (+{pts})")

    sun_d10_h = _planet_house(d10, "Sun")
    sat_d10_h2 = _planet_house(d10, "Saturn")
    if sun_d10_h == 10 or sat_d10_h2 == 10:
        score += 15
        flags.append("sun_or_saturn_d10_10h")
        why.append("D10: Sun/Saturn on 10H axis — career-status in dashamsha (+15)")

    # ── D1 10H / karaka strength ───────────────────────────────────────
    sun_h = _planet_house(planets, "Sun")
    sat_h = _planet_house(planets, "Saturn")
    sun_dgn = _planet_dignity(intel, "Sun")
    sat_dgn = _planet_dignity(intel, "Saturn")

    if sun_h == 10 and _is_strong_dignity(sun_dgn):
        score += 25
        flags.append("sun_strong_10h")
        why.append(f"D1: Sun strong in 10H ({sun_dgn}) — direct govt authority (+25)")
    if sat_h == 10 and _is_strong_dignity(sat_dgn):
        score += 25
        flags.append("saturn_strong_10h")
        why.append(f"D1: Saturn strong in 10H ({sat_dgn}) — service bureaucracy (+25)")

    if tenth_lord == "Sun":
        score += 15
        flags.append("10l_sun")
        why.append("D1: 10L = Sun — career lord is govt karaka (+15)")
    if tenth_lord == "Saturn":
        score += 12
        flags.append("10l_saturn")
        why.append("D1: 10L = Saturn — career via service/karma (+12)")

    if sun_h in _KENDRA_TRIKONA and _is_strong_dignity(sun_dgn):
        score += 10
        flags.append("sun_strong_kendra")
        why.append(f"D1: Sun {sun_dgn} in kendra/trikona h{sun_h} (+10)")

    if sat_h in _KENDRA_TRIKONA and _is_strong_dignity(sat_dgn):
        score += 8
        flags.append("saturn_strong_kendra")
        why.append(f"Sasha-yoga tone: Saturn {sat_dgn} in kendra h{sat_h} (+8)")

    # ── 6-10 service exchange ──────────────────────────────────────────
    sixth_h = _planet_house(planets, sixth_lord) if sixth_lord else None
    tenth_h = _planet_house(planets, tenth_lord) if tenth_lord else None
    if sixth_lord and sixth_h == 10:
        score += 15
        flags.append("6l_in_10h")
        why.append(f"D1: 6L {sixth_lord} in 10H — naukri/service yoga (+15)")
    if tenth_lord and tenth_h == 6:
        score += 15
        flags.append("10l_in_6h")
        why.append(f"D1: 10L {tenth_lord} in 6H — career through service (+15)")

    # ── 9H bhagya for competitive exam ─────────────────────────────────
    ninth_h = _planet_house(planets, ninth_lord) if ninth_lord else None
    if ninth_lord and _is_strong_dignity(_planet_dignity(intel, ninth_lord)):
        score += 10
        flags.append("9l_strong")
        why.append(f"D1: 9L {ninth_lord} strong — exam luck/bhagya axis (+10)")
    if ninth_lord and ninth_h in {1, 5, 9, 10}:
        score += 6
        flags.append("9l_kendra_trikona")
        why.append(f"D1: 9L {ninth_lord} in favourable house h{ninth_h} (+6)")

    # ── Mars defense / police signature ────────────────────────────────
    mars_h = _planet_house(planets, "Mars")
    if mars_h and sun_h and (mars_h == sun_h or abs(mars_h - sun_h) == 6):
        score += 10
        flags.append("sun_mars_defense")
        why.append("Sun-Mars link — defense/police/administration force potential (+10)")

    # ── Jupiter exam grace ─────────────────────────────────────────────
    jup_h = _planet_house(planets, "Jupiter")
    if jup_h in {9, 10, 1} or (sun_h and jup_h and 9 in _aspect_houses("Jupiter", jup_h)):
        score += 8
        flags.append("jupiter_grace")
        why.append("Jupiter supports 9/10 axis — exam clearance grace (+8)")

    # ── Jaimini karakas ────────────────────────────────────────────────
    amk = (karakas_d or {}).get("AmK")
    if amk == "Sun":
        score += 12
        flags.append("amk_sun")
        why.append("Amatyakaraka = Sun — soul-career aligned to authority (+12)")
    elif amk == "Saturn":
        score += 10
        flags.append("amk_saturn")
        why.append("Amatyakaraka = Saturn — soul-career aligned to service (+10)")

    # ── KP assist (optional, from career bucket) ───────────────────────
    if isinstance(kp_assist, dict) and kp_assist.get("score"):
        kp_sc = int(kp_assist.get("score") or 0)
        if kp_sc > 0:
            score += min(kp_sc, 12)
            why.extend((kp_assist.get("why") or [])[:2])
            flags.append("kp_confirms")

    promise_score = min(100, score)
    if promise_score >= 55:
        level = "high"
    elif promise_score >= 30:
        level = "moderate"
    else:
        level = "low"

    legacy_score = min(45, promise_score // 2)

    return {
        "fired": True,
        "engine": "govt_job_engine_v1",
        "score": legacy_score,
        "promise_score": promise_score,
        "govt_promise_level": level,
        "why": why,
        "flags": flags,
        "sun_saturn_links": sun_sat_links,
        "tenth_lord": tenth_lord,
        "sixth_lord": sixth_lord,
        "ninth_lord": ninth_lord,
        "defense_signature": "sun_mars_defense" in flags,
        "kp_summary": (kp_assist or {}).get("summary") if isinstance(kp_assist, dict) else None,
    }


def assess_govt_job_timing(
    kundli: dict,
    intel: dict,
    promise: dict,
) -> dict:
    """Dasha windows for govt job — only meaningful if promise not low."""
    level = str(promise.get("govt_promise_level") or "low")
    if level == "low":
        return {
            "status": "deferred_low_promise",
            "message": "Natal govt promise weak — pehle skill/build phase, timing secondary.",
            "windows": [],
        }

    targets: set[str] = set(_GOVT_DASHA_TARGETS)
    for lord in (
        promise.get("tenth_lord"),
        promise.get("sixth_lord"),
        promise.get("ninth_lord"),
    ):
        if lord:
            targets.add(str(lord))

    md, ad, pd = _dasha_lords(kundli)
    current = "/".join(x for x in (md, ad, pd) if x)
    active_now = any(x in targets for x in (md, ad, pd))

    windows = _scan_govt_dasha_windows(kundli, targets)
    if active_now and not windows:
        windows.insert(0, {
            "md": md,
            "ad": ad,
            "pd": pd,
            "start": "current",
            "end": "current",
            "lords": current,
            "note": "Govt significators active in current dasha",
        })

    return {
        "status": "ready",
        "current_lords": current,
        "active_now": active_now,
        "windows": windows,
        "dasha_targets": sorted(targets),
    }


def assess_govt_job(
    kundli: dict,
    intel: dict,
    *,
    karakas_d: Optional[dict] = None,
    kp: Optional[dict] = None,
    kp_assist_fn: Any = None,
) -> dict:
    """Full govt job engine: life promise → timing."""
    kp_assist = None
    if callable(kp_assist_fn) and kp:
        try:
            kp_assist = kp_assist_fn(kp)
        except Exception:
            kp_assist = None

    promise = assess_govt_job_promise(
        kundli, intel, karakas_d=karakas_d, kp_assist=kp_assist,
    )
    timing = assess_govt_job_timing(kundli, intel, promise)
    return {
        "promise": promise,
        "timing": timing,
        "govt_promise_level": promise.get("govt_promise_level"),
        "promise_score": promise.get("promise_score"),
        "verdict_label": _promise_verdict_label(promise, timing),
        "strategy": _promise_strategy(promise, timing),
    }


def _promise_verdict_label(promise: dict, timing: dict) -> str:
    level = promise.get("govt_promise_level")
    if level == "high" and timing.get("active_now"):
        return "GOVT_PROMISE_STRONG_NOW"
    if level == "high":
        return "GOVT_PROMISE_STRONG"
    if level == "moderate":
        return "GOVT_PROMISE_MODERATE"
    return "GOVT_PROMISE_WEAK"


def _promise_strategy(promise: dict, timing: dict) -> str:
    level = promise.get("govt_promise_level")
    if level == "low":
        return (
            "Chart mein Sun-Saturn govt-service signature abhi kamzor dikhta hai — "
            "sarkari line possible hai lekin long preparation + backup career rakhein."
        )
    if level == "moderate":
        base = (
            "Govt job ka moderate promise hai — consistent syllabus + multiple attempts "
            "realistic approach hai; selection guaranteed nahi."
        )
    else:
        base = (
            "Sun-Saturn axis strong hai — sarkari/service line chart ke saath align hai; "
            "phir bhi exam effort bina shortcut ke zaroori hai."
        )
    wins = timing.get("windows") or []
    if wins and wins[0].get("lords"):
        w = wins[0]
        base += f" Timing focus: {w.get('lords')} period ({w.get('start')}–{w.get('end')})."
    return base


def format_govt_job_block_for_prompt(result: dict, question: str = "") -> str:
    """LOCKED narrator block for govt job answers."""
    if not isinstance(result, dict):
        return ""
    promise = result.get("promise") if isinstance(result.get("promise"), dict) else result
    timing = result.get("timing") if isinstance(result.get("timing"), dict) else {}
    lines = [
        "=== GOVT JOB ENGINE v1 (LOCKED) ===",
        f"Promise level: {promise.get('govt_promise_level')} ({promise.get('promise_score')}/100)",
        f"Verdict: {result.get('verdict_label') or _promise_verdict_label(promise, timing)}",
    ]
    for w in (promise.get("why") or [])[:8]:
        lines.append(f"  • {w}")
    if timing.get("current_lords"):
        lines.append(f"Current dasha: {timing.get('current_lords')}")
    for win in (timing.get("windows") or [])[:2]:
        lines.append(
            f"Window: {win.get('lords')} {win.get('start')}→{win.get('end')}"
        )
    lines.append(f"Strategy: {result.get('strategy') or _promise_strategy(promise, timing)}")
    lines.append("GUARD: Govt selection NEVER guaranteed — hard work mandatory.")
    return "\n".join(lines)
