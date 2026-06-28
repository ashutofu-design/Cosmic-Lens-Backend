"""Dual-track timing — STEP0 promise, then Vedic dasha vs KP significator (NOT mixed).

Marriage domain excluded at router level.

KP note: periods follow Vimshottari (same calendar as Vedic MD/AD/PD) but
fructification is scored via KP NL→SB→SS house significations — separate
score track, winner = higher score; CONVERGED when both pick same period.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from event_timing._shared.dasha_kp_sync import attach_dasha_kp_sync
from event_timing._shared.generic_timing_engine import (
    _flatten_dasha_chain,
    _house_lord,
    _lagna_si,
    _planet_house,
)

_PLANETS_9 = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]
_VEDIC_ROLE_W = {"MD": 1.0, "AD": 5.0, "PD": 6.0}
_KP_ROLE_W = {"MD": 1.0, "AD": 5.0, "PD": 6.0}


def _norm(name: Any) -> str:
    return str(name or "").strip().title()


def _kp_signifies_houses(kp: dict, planet: str, target_houses: list[int]) -> dict[str, Any]:
    """KP significator chain hits for target houses (travel-engine pattern, generic)."""
    out: dict[str, Any] = {"hits": [], "score": 0, "layers": []}
    if not isinstance(kp, dict) or not target_houses:
        return out
    sig_all = kp.get("significations") or kp.get("significators") or {}
    if not isinstance(sig_all, dict):
        return out
    sig = sig_all.get(planet) or sig_all.get(planet.lower())
    if sig is None:
        return out
    target_set = set(int(h) for h in target_houses)
    hits: set[int] = set()
    if isinstance(sig, dict):
        for layer_key in ("pl", "sl", "sb_houses", "ss_houses"):
            layer_houses = sig.get(layer_key) or []
            if not isinstance(layer_houses, list):
                continue
            layer_hits = [int(h) for h in layer_houses if int(h) in target_set]
            if layer_hits:
                hits.update(layer_hits)
                out["layers"].append(f"{layer_key}={sorted(set(layer_hits))}")
    elif isinstance(sig, list):
        for v in sig:
            try:
                h = int(v)
            except (TypeError, ValueError):
                continue
            if h in target_set:
                hits.add(h)
        if hits:
            out["layers"].append(f"flat={sorted(hits)}")
    out["hits"] = sorted(hits)
    out["score"] = len(out["hits"])
    return out


def _kp_dasha_map(kp: dict, target_houses: list[int]) -> dict[str, dict[str, Any]]:
    return {p: _kp_signifies_houses(kp, p, target_houses) for p in _PLANETS_9}


def _concern_lords(lagna_si: int, concern_houses: list[int]) -> set[str]:
    return {_house_lord(lagna_si, h) for h in concern_houses if 1 <= h <= 12}


def _planet_fits_concern_vedic(
    pname: str,
    lagna_si: int,
    planets: list[dict],
    concern_houses: list[int],
    concern_lords: set[str],
    karakas: list[str],
) -> list[str]:
    reasons: list[str] = []
    if pname in concern_lords:
        reasons.append(f"{pname}=concern-house-lord")
    ph = _planet_house(planets, pname)
    if ph in concern_houses:
        reasons.append(f"{pname} in {ph}H")
    if pname in {_norm(k) for k in karakas}:
        reasons.append(f"{pname}=topic-karaka")
    return reasons


def _step0_promise_check(
    kundli: dict,
    kp: dict | None,
    concern_houses: list[int],
    karakas: list[str],
    ranked_top: list[str] | None = None,
) -> dict[str, Any]:
    lagna_si = _lagna_si(kundli)
    factors: list[str] = []
    if lagna_si is None or not concern_houses:
        return {"promised": False, "level": "UNKNOWN", "factors": ["STEP0 missing lagna/houses"]}

    planets = kundli.get("planets") or []
    lords = _concern_lords(lagna_si, concern_houses)
    vedic_hits = 0
    for lord in lords:
        ph = _planet_house(planets, lord)
        if ph in concern_houses or ph in (1, 4, 5, 7, 9, 10, 11):
            vedic_hits += 1
            factors.append(f"STEP0 VEDIC {lord} supportive placement {ph}H")
    for k in karakas[:4]:
        kn = _norm(k)
        if _planet_fits_concern_vedic(kn, lagna_si, planets, concern_houses, lords, karakas):
            vedic_hits += 1

    kp_hits = 0
    if isinstance(kp, dict):
        cusps_raw = kp.get("cusps") or []
        cusp_map: dict[int, str] = {}
        if isinstance(cusps_raw, list):
            for c in cusps_raw:
                if isinstance(c, dict) and c.get("house"):
                    cusp_map[int(c["house"])] = _norm(c.get("subLord") or c.get("sub_lord") or c.get("sb"))
        for h in concern_houses:
            csl = cusp_map.get(h)
            if not csl:
                continue
            sig = _kp_signifies_houses(kp, csl, concern_houses)
            if sig["score"] > 0:
                kp_hits += 1
                factors.append(f"STEP0 KP {h}H CSL {csl} signifies {sig['hits']}")

    promised = vedic_hits >= 1 or kp_hits >= 1
    if vedic_hits >= 2 and kp_hits >= 1:
        level = "STRONG"
    elif promised:
        level = "MODERATE"
    else:
        level = "WEAK"
        factors.append("STEP0 promise WEAK — event houses not strongly linked in D1/KP")

    return {"promised": promised, "level": level, "factors": factors, "vedic_hits": vedic_hits, "kp_hits": kp_hits}


def _score_kp_windows(
    chain: list[dict],
    kp_map: dict[str, dict[str, Any]],
    now: datetime,
    horizon_years: int = 8,
) -> list[dict]:
    from datetime import timedelta

    horizon = now + timedelta(days=365 * horizon_years)
    out: list[dict] = []
    for w in chain:
        if w["end"] < now or w["start"] > horizon:
            continue
        score = 0.0
        triggers: list[str] = []
        hits: set[int] = set()
        for role, lord, wt in (
            ("MD", w.get("md"), _KP_ROLE_W["MD"]),
            ("AD", w.get("ad"), _KP_ROLE_W["AD"]),
            ("PD", w.get("pd"), _KP_ROLE_W["PD"]),
        ):
            lord_n = _norm(lord)
            if not lord_n:
                continue
            info = kp_map.get(lord_n) or {}
            hlist = info.get("hits") or []
            if hlist:
                contrib = len(hlist) * wt
                score += contrib
                hits.update(int(x) for x in hlist)
                triggers.append(f"{role}={lord_n} KP-hits={hlist} +{contrib:.1f}")
        if score <= 0:
            continue
        out.append({
            "md": w.get("md"), "ad": w.get("ad"), "pd": w.get("pd"),
            "start": w["start"], "end": w["end"],
            "start_iso": w["start"].strftime("%Y-%m-%d"),
            "end_iso": w["end"].strftime("%Y-%m-%d"),
            "score": round(score, 2),
            "track": "KP",
            "kp_hits": sorted(hits),
            "triggers": triggers,
        })
    out.sort(key=lambda x: (-x["score"], x["start"]))
    return out


def _running_lord_fit(
    running: dict | None,
    kundli: dict,
    concern_houses: list[int],
    karakas: list[str],
    kp: dict | None,
    kp_map: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """AD/PD running now — Vedic house-lord fit vs KP significator fit (separate)."""
    if not running:
        return {"vedic": {}, "kp": {}}
    lagna_si = _lagna_si(kundli)
    if lagna_si is None:
        return {"vedic": {}, "kp": {}}
    planets = kundli.get("planets") or []
    lords = _concern_lords(lagna_si, concern_houses)
    vedic: dict[str, Any] = {}
    kp_side: dict[str, Any] = {}
    for role in ("AD", "PD"):
        lord = _norm(running.get(role.lower()) or running.get(role))
        if not lord:
            continue
        vedic[role] = {
            "lord": lord,
            "fits": _planet_fits_concern_vedic(lord, lagna_si, planets, concern_houses, lords, karakas),
            "active_now": bool(_planet_fits_concern_vedic(lord, lagna_si, planets, concern_houses, lords, karakas)),
        }
        kp_info = kp_map.get(lord) or {}
        kp_side[role] = {
            "lord": lord,
            "hits": kp_info.get("hits") or [],
            "active_now": bool(kp_info.get("score", 0) > 0),
        }
    return {"vedic": vedic, "kp": kp_side}


def _periods_overlap(a: dict, b: dict, min_days: int = 14) -> bool:
    try:
        a_s = a.get("start") or datetime.fromisoformat(str(a.get("start_iso", ""))[:10])
        a_e = a.get("end") or datetime.fromisoformat(str(a.get("end_iso", ""))[:10])
        b_s = b.get("start") or datetime.fromisoformat(str(b.get("start_iso", ""))[:10])
        b_e = b.get("end") or datetime.fromisoformat(str(b.get("end_iso", ""))[:10])
    except (ValueError, TypeError):
        return False
    overlap_start = max(a_s, b_s)
    overlap_end = min(a_e, b_e)
    return (overlap_end - overlap_start).days >= min_days


def _pick_winner(vedic_best: dict | None, kp_best: dict | None) -> dict[str, Any]:
    v_score = float((vedic_best or {}).get("score") or 0)
    k_score = float((kp_best or {}).get("score") or 0)
    converged = bool(vedic_best and kp_best and _periods_overlap(vedic_best, kp_best))
    if converged:
        winner = "CONVERGED"
        final = dict(vedic_best or kp_best)
        final["track"] = "CONVERGED"
        final["vedic_score"] = v_score
        final["kp_score"] = k_score
        final["score"] = round(max(v_score, k_score) * 1.05, 2)
    elif v_score >= k_score and vedic_best:
        winner = "VEDIC"
        final = dict(vedic_best)
        final["track"] = "VEDIC"
        final["vedic_score"] = v_score
        final["kp_score"] = k_score
    elif kp_best:
        winner = "KP"
        final = dict(kp_best)
        final["track"] = "KP"
        final["vedic_score"] = v_score
        final["kp_score"] = k_score
    else:
        winner = "NONE"
        final = {}
    return {"winner": winner, "converged": converged, "final_window": final}


def enrich_dual_track_timing(
    raw: dict,
    kundli: dict,
    kp: Optional[dict],
    *,
    concern_houses: list[int],
    karakas: Optional[list[str]] = None,
    domain: str = "",
) -> dict:
    """Attach promise + separate Vedic/KP dasha tracks; set final window from winner."""
    if not isinstance(raw, dict):
        return raw
    houses = [int(h) for h in concern_houses if isinstance(h, (int, float)) or str(h).isdigit()]
    if not houses:
        houses = list(raw.get("dynamic_houses") or [])
    k_karakas = [_norm(k) for k in (karakas or raw.get("dynamic_karakas") or []) if k]

    raw = attach_dasha_kp_sync(raw, kundli, kp or {}) if "kp_dasha_sync" not in raw else raw
    factors = list(raw.get("factors") or [])

    promise = _step0_promise_check(kundli, kp, houses, k_karakas)
    raw["promise_check"] = promise
    factors.extend(promise.get("factors") or [])

    kp_map = _kp_dasha_map(kp or {}, houses)
    chain = _flatten_dasha_chain(kundli if isinstance(kundli, dict) else {})
    now = datetime.utcnow()

    vedic_windows = []
    for w in raw.get("next_3_windows") or []:
        if isinstance(w, dict):
            row = dict(w)
            row["track"] = "VEDIC"
            vedic_windows.append(row)
    if not vedic_windows:
        cw = raw.get("current_window")
        if isinstance(cw, dict):
            vedic_windows = [dict(cw, track="VEDIC")]

    kp_windows = _score_kp_windows(chain, kp_map, now)
    kp_top3 = kp_windows[:3]

    vedic_best = vedic_windows[0] if vedic_windows else None
    kp_best = kp_windows[0] if kp_windows else None
    pick = _pick_winner(vedic_best, kp_best)

    running = raw.get("dasha_running_now")
    running_fit = _running_lord_fit(running, kundli, houses, k_karakas, kp, kp_map)

    dual = {
        "vedic": {
            "top_windows": vedic_windows[:3],
            "best_score": float((vedic_best or {}).get("score") or 0),
            "running_ad_pd": running_fit.get("vedic") or {},
        },
        "kp": {
            "top_windows": kp_top3,
            "best_score": float((kp_best or {}).get("score") or 0),
            "running_ad_pd": running_fit.get("kp") or {},
            "significator_map": {
                p: kp_map[p]["hits"] for p in _PLANETS_9 if kp_map[p]["score"] > 0
            },
        },
        "winner": pick["winner"],
        "converged": pick["converged"],
        "final_window": pick["final_window"],
    }
    raw["dual_track"] = dual

    if pick["final_window"]:
        ts = str(raw.get("timing_source") or "")
        cw = raw.get("current_window") if isinstance(raw.get("current_window"), dict) else {}
        if ts in ("current_dasha_active", "next_dasha_scan") and cw:
            raw["dual_track_window"] = pick["final_window"]
            if pick["converged"]:
                raw["vedic_kp_converged"] = True
        else:
            raw["current_window"] = pick["final_window"]
    if not raw.get("promise_check", {}).get("promised"):
        raw["verdict"] = raw.get("verdict") or "LOW_PROMISE"
        if raw.get("band") == "STRONG":
            raw["band"] = "MEDIUM"

    for role, side in (running_fit.get("vedic") or {}).items():
        fits = side.get("fits") or []
        if fits:
            factors.append(f"STEP5b VEDIC {role}={side.get('lord')} {';'.join(fits)}")
        else:
            factors.append(f"STEP5b VEDIC {role}={side.get('lord')} NOT linked to topic houses")
    for role, side in (running_fit.get("kp") or {}).items():
        hits = side.get("hits") or []
        if hits:
            factors.append(f"STEP5c KP {role}={side.get('lord')} signifies {hits}")
        else:
            factors.append(f"STEP5c KP {role}={side.get('lord')} NOT signifying topic houses")

    factors.append(
        f"STEP7 DUAL-TRACK winner={pick['winner']} "
        f"vedic={dual['vedic']['best_score']} kp={dual['kp']['best_score']} "
        f"converged={pick['converged']}"
    )
    raw["factors"] = factors
    raw["domain"] = raw.get("domain") or domain
    return raw


def format_dual_track_block(raw: dict) -> str:
    """LOCKED addendum for narrator — Vedic vs KP separate, winner explicit."""
    dt = raw.get("dual_track") if isinstance(raw, dict) else None
    if not isinstance(dt, dict):
        return ""
    prom = raw.get("promise_check") or {}
    lines = [
        "──────── DUAL-TRACK TIMING (VEDIC ≠ KP — NOT MIXED) ────────",
        f"Promise check: {prom.get('level', '?')} (promised={prom.get('promised')})",
    ]
    run = raw.get("dasha_running_now") or {}
    if run:
        lines.append(f"Running dasha: {run.get('lords')} ({run.get('start_iso')}→{run.get('end_iso')})")
    v_run = (dt.get("vedic") or {}).get("running_ad_pd") or {}
    k_run = (dt.get("kp") or {}).get("running_ad_pd") or {}
    for role in ("AD", "PD"):
        vs = v_run.get(role) or {}
        ks = k_run.get(role) or {}
        if vs:
            lines.append(
                f"  Vedic {role} {vs.get('lord')}: "
                f"{'TOPIC-LINKED' if vs.get('active_now') else 'NOT linked'} "
                f"{vs.get('fits') or []}"
            )
        if ks:
            lines.append(
                f"  KP {role} {ks.get('lord')}: "
                f"{'SIGNIFIES' if ks.get('active_now') else 'NOT signifying'} "
                f"houses {ks.get('hits') or []}"
            )
    lines.append(f"Winner track: {dt.get('winner')} (converged={dt.get('converged')})")
    fw = dt.get("final_window") or {}
    if fw:
        lines.append(
            f"Final window ({fw.get('track')}): {fw.get('start_iso')}→{fw.get('end_iso')} "
            f"{fw.get('md')}/{fw.get('ad')} score={fw.get('score')}"
        )
    vb = (dt.get("vedic") or {}).get("top_windows") or []
    kb = (dt.get("kp") or {}).get("top_windows") or []
    if vb:
        w = vb[0]
        lines.append(f"  Vedic best: {w.get('start_iso')}→{w.get('end_iso')} score={w.get('score')}")
    if kb:
        w = kb[0]
        lines.append(f"  KP best: {w.get('start_iso')}→{w.get('end_iso')} score={w.get('score')}")
    lines.append("⛔ Do NOT merge Vedic+KP scores — cite winner track; CONVERGED = both agree")
    lines.append("────────────────────────────────────────────────────────────")
    return "\n".join(lines)


def concern_houses_from_spec(spec: dict, raw: dict | None = None) -> list[int]:
    raw = raw or {}
    dyn = raw.get("dynamic_houses")
    if isinstance(dyn, list) and dyn:
        return [int(h) for h in dyn if str(h).isdigit()]
    houses = spec.get("houses") or []
    out: list[int] = []
    for h in houses:
        if isinstance(h, int):
            out.append(h)
        elif str(h).isdigit():
            out.append(int(h))
    return out


def karakas_from_spec(spec: dict, raw: dict | None = None) -> list[str]:
    raw = raw or {}
    dyn = raw.get("dynamic_karakas")
    if isinstance(dyn, list) and dyn:
        return [str(k) for k in dyn]
    return [str(k) for k in (spec.get("karakas") or []) if k]
