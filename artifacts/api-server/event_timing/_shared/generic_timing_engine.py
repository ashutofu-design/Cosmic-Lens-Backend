"""Configurable domain timing engine — FILTER→VERIFY→KP→DASHA→TRANSIT→WINDOW."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple

try:
    from divisional_charts import compute_d9  # type: ignore
except Exception:
    compute_d9 = None  # type: ignore

try:
    from event_timing._shared.double_transit import check_double_transit  # type: ignore
except Exception:
    check_double_transit = None  # type: ignore

_SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]
_SIGN_IDX = {s: i for i, s in enumerate(_SIGNS)}
_SIGN_LORDS: Dict[int, str] = {
    0: "Mars", 1: "Venus", 2: "Mercury", 3: "Moon", 4: "Sun",
    5: "Mercury", 6: "Venus", 7: "Mars", 8: "Jupiter",
    9: "Saturn", 10: "Saturn", 11: "Jupiter",
}
_EXALT: Dict[str, int] = {
    "Sun": 0, "Moon": 1, "Mars": 9, "Mercury": 5,
    "Jupiter": 3, "Venus": 11, "Saturn": 6,
}
_OWN_SIGNS: Dict[str, Set[int]] = {
    "Sun": {4}, "Moon": {3}, "Mars": {0, 7}, "Mercury": {2, 5},
    "Jupiter": {8, 11}, "Venus": {1, 6}, "Saturn": {9, 10},
}
_PLANETS_9 = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]
_D1_MIN = 10.0
_CONJUNCT_LORD_WEIGHT: Dict[int, float] = {5: 12.0, 7: 12.0, 11: 10.0}
_MIN_GAP_DAYS = 45
# Mandatory: no MD/AD/PD window may be cited unless activation score >= this.
MIN_AD_PD_ACTIVATION = 9.0
# Dasha-level weights for window scoring (MD background · AD trigger · PD finest).
_DASHA_MD, _DASHA_AD, _DASHA_PD = 2.0, 7.0, 9.0


@dataclass
class DomainTimingConfig:
    domain: str
    engine_version: str = "v1.0.0"
    concern_houses: List[Tuple[int, float, str]] = field(default_factory=list)
    leak_houses: List[Tuple[int, float, str]] = field(default_factory=list)
    occupant_bumps: List[Tuple[int, float, str]] = field(default_factory=list)
    aspect_target_houses: List[Tuple[int, float, str]] = field(default_factory=list)
    karakas: List[Tuple[str, float, str]] = field(default_factory=list)
    kp_cusps: List[int] = field(default_factory=list)
    promote_tags: Tuple[str, ...] = ()
    obstruct_tags: Tuple[str, ...] = ()
    double_transit_houses: List[int] = field(default_factory=list)
    verdict_promised: float = 2.5
    verdict_favourable: float = 5.0
    verdict_caution: float = 8.0
    promised_label: str = "FAVOURABLE_WINDOW"
    favourable_label: str = "MODERATE_WINDOW"
    caution_label: str = "DELAYED_WINDOW"
    defer_label: str = "LOW_PROBABILITY"
    brand_safety: List[str] = field(default_factory=list)
    llm_directives: List[str] = field(default_factory=list)
    # Current AD/PD must reach this activation score to answer with running dasha.
    min_current_activation: float = MIN_AD_PD_ACTIVATION


def _sign_idx(v: Any) -> Optional[int]:
    if isinstance(v, int):
        return v % 12
    if isinstance(v, str):
        return _SIGN_IDX.get(v.strip().capitalize()) or _SIGN_IDX.get(v)
    return None


def _lagna_si(kundli: dict) -> Optional[int]:
    asc = kundli.get("ascendant")
    si = _sign_idx(asc) if isinstance(asc, str) else None
    if si is not None:
        return si
    for k in ("lagnaSign", "ascendant_sign", "ascendantSign"):
        si = _sign_idx(kundli.get(k))
        if si is not None:
            return si
    return None


def _house_lord(lagna_si: int, house: int) -> str:
    return _SIGN_LORDS[(lagna_si + house - 1) % 12]


def _planet_house(planets: List[dict], name: str) -> Optional[int]:
    for p in planets or []:
        if isinstance(p, dict) and p.get("name") == name:
            h = p.get("house")
            if isinstance(h, int):
                return h
    return None


def _planet_sign_idx(planets: List[dict], name: str) -> Optional[int]:
    for p in planets or []:
        if isinstance(p, dict) and p.get("name") == name:
            si = p.get("sign_idx")
            if isinstance(si, int):
                return si % 12
            return _sign_idx(p.get("sign"))
    return None


def _planets_in_house(planets: List[dict], house: int) -> List[str]:
    return [
        p["name"] for p in (planets or [])
        if isinstance(p, dict) and p.get("house") == house and p.get("name") in _PLANETS_9
    ]


def _aspects_house(aspector: str, ap_house: int, target: int) -> bool:
    if not (1 <= ap_house <= 12 and 1 <= target <= 12):
        return False
    diff = ((target - ap_house) % 12) + 1
    if diff == 7:
        return True
    extras = {"Mars": {4, 8}, "Jupiter": {5, 9}, "Saturn": {3, 10}, "Rahu": {3, 10}, "Ketu": {3, 10}}
    return diff in extras.get(aspector, set())


def _kp_cusp(kp: dict, house: int) -> Optional[dict]:
    for c in (kp or {}).get("cusps", []) or []:
        if isinstance(c, dict) and c.get("house") == house:
            return c
    return None


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


def _dasha_lord(node: dict) -> Optional[str]:
    for k in ("lord", "planet", "name", "ruler"):
        v = node.get(k)
        if v:
            return str(v)
    return None


def _dasha_start_end(node: dict) -> Tuple[Optional[datetime], Optional[datetime]]:
    s = node.get("start") or node.get("startDate") or node.get("from") or node.get("start_date")
    e = node.get("end") or node.get("endDate") or node.get("to") or node.get("end_date")
    return _parse_iso(s), _parse_iso(e)


def _dasha_children(node: dict) -> List[dict]:
    for k in (
        "subDashas", "antardashas", "ad", "sub_dashas",
        "pratyantar", "pratyantar_dashas", "pratyantardashas",
        "pd", "children",
    ):
        v = node.get(k)
        if isinstance(v, list):
            return v
    return []


def _flatten_dasha_chain(kundli: dict) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    dashas = kundli.get("dashas") or []
    if not isinstance(dashas, list):
        return out
    for md in dashas:
        if not isinstance(md, dict):
            continue
        md_lord = _dasha_lord(md)
        ads = _dasha_children(md)
        if not ads:
            ms, me = _dasha_start_end(md)
            if ms and me:
                out.append({"md": md_lord, "ad": None, "pd": None, "start": ms, "end": me})
            continue
        for ad in ads:
            if not isinstance(ad, dict):
                continue
            ad_lord = _dasha_lord(ad)
            pds = _dasha_children(ad)
            if not pds:
                ads_, ade_ = _dasha_start_end(ad)
                if ads_ and ade_:
                    out.append({"md": md_lord, "ad": ad_lord, "pd": None, "start": ads_, "end": ade_})
                continue
            for pd in pds:
                if not isinstance(pd, dict):
                    continue
                pds_, pde_ = _dasha_start_end(pd)
                if pds_ and pde_:
                    out.append({
                        "md": md_lord, "ad": ad_lord, "pd": _dasha_lord(pd),
                        "start": pds_, "end": pde_,
                    })
    return out


def _step1_filter(kundli: dict, lagna_si: int, cfg: DomainTimingConfig) -> Dict[str, Dict[str, Any]]:
    planets = kundli.get("planets") or []
    out: Dict[str, Dict[str, Any]] = {
        p: {"d1": 0.0, "links": [], "in_filter": False} for p in _PLANETS_9
    }
    for h, w, label in cfg.concern_houses:
        lord = _house_lord(lagna_si, h)
        out[lord]["d1"] += w
        out[lord]["links"].append(label)
        out[lord]["links"].append(f"{h}L")
        lord_house = _planet_house(planets, lord)
        if lord_house:
            conj_w = _CONJUNCT_LORD_WEIGHT.get(h, 10.0)
            for pname in _planets_in_house(planets, lord_house):
                if pname != lord:
                    out[pname]["d1"] += conj_w
                    out[pname]["links"].append(f"conjunct {h}L({lord})")
    for h, w, label in cfg.leak_houses:
        lord = _house_lord(lagna_si, h)
        out[lord]["d1"] += w
        out[lord]["links"].append(label)
    for h, w, label in cfg.occupant_bumps:
        for pname in _planets_in_house(planets, h):
            out[pname]["d1"] += w
            out[pname]["links"].append(label)
    for h, w, label in cfg.aspect_target_houses:
        for pname in _PLANETS_9:
            ap = _planet_house(planets, pname)
            if ap and _aspects_house(pname, ap, h):
                out[pname]["d1"] += w
                out[pname]["links"].append(label)
    for name, w, label in cfg.karakas:
        if name in out:
            out[name]["d1"] += w
            out[name]["links"].append(label)
    for pname, info in out.items():
        info["in_filter"] = info["d1"] >= _D1_MIN
    return out


def _step2_d9(kundli: dict, candidates: Set[str]) -> Dict[str, float]:
    out = {p: 8.0 for p in candidates}
    if not candidates or compute_d9 is None:
        return out
    try:
        planets = kundli.get("planets") or []
        asc_lon = next(
            (
                kundli.get(key)
                for key in (
                    "ascendantDeg", "ascendantLongitude",
                    "ascendant_longitude", "lagnaLongitude",
                )
                if isinstance(kundli.get(key), (int, float))
            ),
            None,
        )
        d9 = compute_d9(planets, lagna_lon=asc_lon)
        if not isinstance(d9, dict) or not d9:
            return out
        for pname in candidates:
            info = d9.get(pname)
            si = info.get("sign_idx") if isinstance(info, dict) else None
            if not isinstance(si, int):
                continue
            if pname in _EXALT and si == _EXALT[pname]:
                out[pname] = 22.0
            elif pname in _OWN_SIGNS and si in _OWN_SIGNS[pname]:
                out[pname] = 18.0
            else:
                out[pname] = 10.0
    except Exception:
        pass
    return out


def _step3_kp(kp: dict, cfg: DomainTimingConfig) -> Dict[str, Any]:
    layer: Dict[str, Any] = {"cusps": {}, "score": 0.0}
    for h in cfg.kp_cusps:
        c = _kp_cusp(kp, h)
        if c:
            layer["cusps"][h] = c.get("subLord") or c.get("sub_lord") or "?"
            layer["score"] += 5.0
    return layer


def _step4_rank(d1: Dict[str, Dict[str, Any]], d9: Dict[str, float], kp_score: float) -> List[Dict[str, Any]]:
    ranked: List[Dict[str, Any]] = []
    candidates = [p for p, info in d1.items() if info.get("in_filter")]
    if not candidates:
        candidates = sorted(_PLANETS_9, key=lambda p: d1[p]["d1"], reverse=True)[:4]
    kp_each = kp_score / max(len(candidates), 1)
    for pname in candidates:
        score = d1[pname]["d1"] * 0.5 + d9.get(pname, 8.0) * 0.35 + kp_each * 0.15
        ranked.append({
            "name": pname,
            "score": round(score, 2),
            "links": list(d1[pname]["links"]),
        })
    ranked.sort(key=lambda r: r["score"], reverse=True)
    return ranked


def _classify_lords(ranked: List[Dict[str, Any]], cfg: DomainTimingConfig) -> Tuple[Set[str], Set[str]]:
    promote: Set[str] = set()
    obstruct: Set[str] = set()
    for r in ranked:
        links = r.get("links") or []
        pc = sum(1 for l in links if any(t in l for t in cfg.promote_tags))
        oc = sum(1 for l in links if any(t in l for t in cfg.obstruct_tags))
        if pc > oc:
            promote.add(r["name"])
        elif oc > pc:
            obstruct.add(r["name"])
    return promote, obstruct


def _duration_days(w: Dict[str, Any]) -> int:
    start, end = w.get("start"), w.get("end")
    if isinstance(start, datetime) and isinstance(end, datetime):
        return max(1, (end - start).days)
    return 999_999


def _finest_windows_containing_now(
    windows: List[Dict[str, Any]],
    now: datetime,
) -> List[Dict[str, Any]]:
    """Among dasha rows active at `now`, keep only the narrowest (PD > AD > MD)."""
    running = [w for w in windows if w.get("start") and w.get("end") and w["start"] <= now <= w["end"]]
    if not running:
        return []
    with_pd = [w for w in running if w.get("pd")]
    pool = with_pd if with_pd else running
    min_days = min(_duration_days(w) for w in pool)
    return [w for w in pool if _duration_days(w) == min_days]


def _lords_label(w: Dict[str, Any]) -> str:
    if w.get("lords"):
        return str(w["lords"])
    return "/".join(x for x in (w.get("md"), w.get("ad"), w.get("pd")) if x)


def _enrich_window_row(w: Dict[str, Any]) -> Dict[str, Any]:
    row = dict(w)
    row["lords"] = _lords_label(row)
    return row


def _step5_windows(
    chain: List[Dict[str, Any]],
    ranked: List[Dict[str, Any]],
    cfg: DomainTimingConfig,
    now: datetime,
    horizon_years: int = 8,
) -> List[Dict[str, Any]]:
    if not chain or not ranked:
        return []
    score_map = {r["name"]: r["score"] for r in ranked}
    max_s = max(score_map.values()) or 1.0
    promote, obstruct = _classify_lords(ranked, cfg)
    horizon = now + timedelta(days=365 * horizon_years)
    windows: List[Dict[str, Any]] = []
    for w in chain:
        if w["end"] < now or w["start"] > horizon:
            continue
        pos, neg = 0.0, 0.0
        triggers: List[str] = []
        for role, lord, wt in (("MD", w["md"], _DASHA_MD), ("AD", w["ad"], _DASHA_AD), ("PD", w["pd"], _DASHA_PD)):
            if not lord or lord not in score_map:
                continue
            rel = score_map[lord] / max_s
            contrib = wt * rel
            if lord in promote:
                pos += contrib
                triggers.append(f"{role}={lord}(PROMOTE,+{contrib:.1f})")
            elif lord in obstruct:
                neg += contrib
                triggers.append(f"{role}={lord}(OBSTRUCT,+{contrib:.1f})")
            else:
                pos += contrib * 0.5
                triggers.append(f"{role}={lord}(NEUTRAL,+{contrib*0.5:.1f})")
        net = max(0.1, pos - neg * 0.5)
        windows.append(_enrich_window_row({
            "md": w["md"], "ad": w["ad"], "pd": w["pd"],
            "start": w["start"], "end": w["end"],
            "start_iso": w["start"].strftime("%Y-%m-%d"),
            "end_iso": w["end"].strftime("%Y-%m-%d"),
            "score": round(net, 2),
            "triggers": triggers,
        }))
    windows.sort(key=lambda x: (x["start"], -x["score"]))
    return windows


def _pick_top(windows: List[Dict[str, Any]], n: int = 3) -> List[Dict[str, Any]]:
    chosen: List[Dict[str, Any]] = []
    for w in windows:
        if all(abs((w["start"] - c["start"]).days) >= _MIN_GAP_DAYS for c in chosen):
            chosen.append(w)
        if len(chosen) >= n:
            break
    return chosen


def _norm_lord(name: Any) -> str:
    return str(name or "").strip().title()


def _activation_score(
    w: Dict[str, Any],
    promote: Set[str],
    score_map: Dict[str, float],
) -> float:
    """AD/PD-led domain activation; MD is background only."""
    val = 0.0
    md = _norm_lord(w.get("md"))
    if md in promote:
        val += 1.0
    elif score_map.get(md, 0) >= 12:
        val += 0.5
    for _role, key, wt in (("PD", "pd", 6.0), ("AD", "ad", 5.0)):
        lord = _norm_lord(w.get(key))
        if not lord:
            continue
        if lord in promote:
            val += wt
        elif score_map.get(lord, 0) >= 10:
            val += wt * 0.55
        elif score_map.get(lord, 0) >= 6:
            val += wt * 0.25
    return val


def _score_map_from_ranked(ranked: List[Dict[str, Any]]) -> Dict[str, float]:
    return {
        str(r["name"]): float(r.get("score") or 0)
        for r in ranked
        if r.get("name")
    }


def _build_domain_significator_rank(
    lagna_si: int,
    kundli: dict,
    cfg: DomainTimingConfig,
    ranked: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """All love/domain triggers rank-wise: lords, occupants, aspectors, conjunct lords, karakas."""
    planets = kundli.get("planets") or []
    score_map = _score_map_from_ranked(ranked)
    entries: List[Dict[str, Any]] = []
    seen: Set[Tuple[str, str, int]] = set()

    def _add(planet: str, role: str, house: int, tag: str, link: str) -> None:
        if not planet:
            return
        key = (planet, role, house)
        if key in seen:
            return
        seen.add(key)
        entries.append({
            "planet": planet,
            "role": role,
            "house": house,
            "tag": tag,
            "link": link,
            "score": round(score_map.get(planet, 0.0), 2),
        })

    for h, _w, label in cfg.concern_houses:
        lord = _house_lord(lagna_si, h)
        _add(lord, f"{h}L", h, f"{h}L", f"{h}L lord — {label}")

        for pname in _planets_in_house(planets, h):
            _add(pname, "occupant", h, f"{h}H", f"occupies {h}H — {label}")

        for pname in _PLANETS_9:
            ap = _planet_house(planets, pname)
            if ap and _aspects_house(pname, ap, h):
                _add(pname, "aspector", h, f"aspect_{h}H", f"aspects {h}H — {label}")

        lord_house = _planet_house(planets, lord)
        if lord_house:
            for pname in _planets_in_house(planets, lord_house):
                if pname != lord:
                    _add(
                        pname, "conjunct_lord", h, f"conj_{h}L",
                        f"conjunct {h}L ({lord}) — {label}",
                    )

    for name, _w, label in cfg.karakas:
        _add(name, "karaka", 0, "karaka", label)

    entries.sort(key=lambda x: (-x["score"], x["house"], x["planet"]))
    return entries


def _build_domain_house_lords(
    lagna_si: int,
    cfg: DomainTimingConfig,
    ranked: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Per concern-house lord (e.g. 5L/7L/11L) with D1+divisional composite score."""
    score_map = _score_map_from_ranked(ranked)
    seen: Set[int] = set()
    out: List[Dict[str, Any]] = []
    for h, _w, label in cfg.concern_houses:
        if h in seen:
            continue
        seen.add(h)
        planet = _house_lord(lagna_si, h)
        out.append({
            "tag": f"{h}L",
            "house": h,
            "planet": planet,
            "score": round(score_map.get(planet, 0.0), 2),
            "label": label,
        })
    out.sort(key=lambda x: (-x["score"], x["house"]))
    return out


def _annotate_significator_on_window(
    row: Dict[str, Any],
    significator: Optional[str],
) -> Dict[str, Any]:
    """Mark whether love trigger is via AD or PD for the top significator planet."""
    out = dict(row)
    sig = _norm_lord(significator)
    if not sig:
        return out
    ad, pd = _norm_lord(out.get("ad")), _norm_lord(out.get("pd"))
    out["love_planet"] = significator
    if pd == sig:
        out["love_via"] = "PD"
    elif ad == sig:
        out["love_via"] = "AD"
    else:
        out["love_via"] = None
    return out


def _pick_primary_significator(
    significator_rank: List[Dict[str, Any]],
    ranked: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Highest-score linkage (lord / occupant / aspect / conjunct / karaka) — timing via AD/PD."""
    by_planet: Dict[str, Dict[str, Any]] = {}
    for entry in significator_rank:
        planet = str(entry.get("planet") or "").strip()
        if not planet:
            continue
        sc = float(entry.get("score") or 0)
        if planet not in by_planet or sc > float(by_planet[planet].get("score") or 0):
            by_planet[planet] = dict(entry)
    if not by_planet:
        for r in ranked[:6]:
            name = str(r.get("name") or "").strip()
            if name:
                by_planet[name] = {"planet": name, "score": float(r.get("score") or 0), "tag": "ranked"}
    if not by_planet:
        return {}
    best_name, best_entry = max(
        by_planet.items(),
        key=lambda x: float(x[1].get("score") or 0),
    )
    roles = sorted({
        str(e.get("tag") or e.get("role") or "")
        for e in significator_rank
        if str(e.get("planet") or "").strip() == best_name and (e.get("tag") or e.get("role"))
    })
    links = [
        str(e.get("link") or "")
        for e in significator_rank
        if str(e.get("planet") or "").strip() == best_name and e.get("link")
    ]
    return {
        "name": best_name,
        "score": round(float(best_entry.get("score") or 0), 2),
        "house_tag": best_entry.get("tag") or (roles[0] if roles else None),
        "roles": roles,
        "link": links[0] if links else best_entry.get("link"),
        "expected_via": "AD/PD",
    }


def _build_three_timing_periods(
    windows: List[Dict[str, Any]],
    ranked: List[Dict[str, Any]],
    promote: Set[str],
    now: datetime,
    min_activation: float,
    primary: Optional[Dict[str, Any]],
    significator: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Up to 3 qualified windows (activation >= min), chronological, min gap apart."""
    score_map = _score_map_from_ranked(ranked)
    qualified: List[Dict[str, Any]] = []
    for w in sorted(windows, key=lambda x: x.get("start") or now):
        if not w.get("end") or w["end"] <= now:
            continue
        act = _activation_score(w, promote, score_map)
        if act < min_activation:
            continue
        row = _enrich_window_row(w)
        row["activation_score"] = round(act, 2)
        row["is_active_now"] = bool(w.get("start") and w["start"] <= now <= w["end"])
        qualified.append(_annotate_significator_on_window(row, significator))

    if primary and primary.get("start"):
        ps = primary["start"]
        qualified.sort(key=lambda x: (0 if x.get("start") == ps else 1, x.get("start") or now))

    chosen: List[Dict[str, Any]] = []
    for w in qualified:
        if all(abs((w["start"] - c["start"]).days) >= _MIN_GAP_DAYS for c in chosen):
            row = dict(w)
            row["rank"] = len(chosen) + 1
            chosen.append(row)
        if len(chosen) >= 3:
            break
    return chosen


def pick_primary_timing_window(
    windows: List[Dict[str, Any]],
    ranked: List[Dict[str, Any]],
    promote: Set[str],
    now: datetime,
    *,
    min_ad_pd: float = MIN_AD_PD_ACTIVATION,
) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]], str, bool]:
    """Dasha-first: current AD/PD active → else strongest suitable AD/PD window.

    Mandatory: periods with activation < min_ad_pd are never cited. Selection
    priority is AD+PD > AD > PD; MD remains background context.
    """
    if not windows:
        return None, None, "none", False

    score_map = {
        str(r["name"]): float(r.get("score") or 0)
        for r in ranked
        if r.get("name")
    }

    def _qualified(w: Dict[str, Any]) -> bool:
        return _activation_score(w, promote, score_map) >= min_ad_pd

    def _ad_pd_rank(w: Dict[str, Any]) -> int:
        ad = _norm_lord(w.get("ad"))
        pd = _norm_lord(w.get("pd"))
        ad_hit = ad in promote
        pd_hit = pd in promote
        if ad_hit and pd_hit:
            return 0
        if ad_hit:
            return 1
        if pd_hit:
            return 2
        return 3

    def _suitable_key(w: Dict[str, Any]) -> tuple:
        return (
            _ad_pd_rank(w),
            -_activation_score(w, promote, score_map),
            w.get("start") or datetime.max,
        )

    running = _finest_windows_containing_now(windows, now)
    if running:
        best_run = min(running, key=_suitable_key)
        act = _activation_score(best_run, promote, score_map)
        if act >= min_ad_pd:
            future = sorted(
                [w for w in windows if w.get("start") and w["start"] > now],
                key=_suitable_key,
            )
            nxt = next((w for w in future if _qualified(w)), None)
            row = _enrich_window_row(best_run)
            row["is_active_now"] = True
            row["activation_score"] = round(act, 2)
            return row, (_enrich_window_row(nxt) if nxt else None), "current_dasha_active", True

    future = sorted(
        [w for w in windows if w.get("end") and w["end"] > now],
        key=_suitable_key,
    )
    for w in future:
        if not _qualified(w):
            continue
        act = _activation_score(w, promote, score_map)
        row = _enrich_window_row(w)
        row["is_active_now"] = w["start"] <= now <= w["end"]
        row["activation_score"] = round(act, 2)
        nxt = next(
            (x for x in future if x is not w and _qualified(x)),
            None,
        )
        return row, (_enrich_window_row(nxt) if nxt else None), "next_dasha_scan", False

    return None, None, "no_qualified_window", False


def _verdict(score: float, cfg: DomainTimingConfig) -> Tuple[str, str]:
    if score >= cfg.verdict_caution:
        return cfg.defer_label, "WEAK"
    if score >= cfg.verdict_favourable:
        return cfg.caution_label, "MEDIUM"
    if score >= cfg.verdict_promised:
        return cfg.favourable_label, "MEDIUM"
    return cfg.promised_label, "STRONG"


def compute_generic_timing_window(
    kundli: dict,
    cfg: DomainTimingConfig,
    intel: Optional[dict] = None,
    kp: Optional[dict] = None,
    birth: Any = None,
    question: str = "",
    bucket: str = "general",
) -> dict:
    """Run configurable timing pipeline for a domain."""
    intel = intel or {}
    kp = kp or {}
    factors: List[str] = [f"DOMAIN={cfg.domain} BUCKET={bucket}"]
    if not isinstance(kundli, dict) or not kundli.get("planets"):
        return {
            "verdict": "UNKNOWN", "band": "WEAK", "bucket": bucket,
            "factors": ["GATE missing planets"], "engine_version": cfg.engine_version,
            "engine_arch": "FILTER→VERIFY→KP→DASHA→TRANSIT→WINDOW",
        }
    lagna_si = _lagna_si(kundli)
    if lagna_si is None:
        return {
            "verdict": "UNKNOWN", "band": "WEAK", "bucket": bucket,
            "factors": ["GATE missing lagna"], "engine_version": cfg.engine_version,
            "engine_arch": "FILTER→VERIFY→KP→DASHA→TRANSIT→WINDOW",
        }

    now = datetime.utcnow()
    d1 = _step1_filter(kundli, lagna_si, cfg)
    candidates = {p for p, info in d1.items() if info.get("in_filter")}
    d9 = _step2_d9(kundli, candidates)
    kp_layer = _step3_kp(kp, cfg)
    ranked = _step4_rank(d1, d9, kp_layer.get("score", 0.0))
    factors.append(f"STEP1 top={[r['name'] for r in ranked[:3]]}")

    chain = _flatten_dasha_chain(kundli)
    windows = _step5_windows(chain, ranked, cfg, now)
    promote, _obstruct = _classify_lords(ranked, cfg)
    score_map = {
        str(r["name"]): float(r.get("score") or 0)
        for r in ranked
        if r.get("name")
    }
    running_now = [w for w in windows if w["start"] <= now <= w["end"]]
    running_activation = None
    if running_now:
        best_run = max(
            running_now,
            key=lambda w: (_activation_score(w, promote, score_map), w.get("score", 0)),
        )
        running_activation = round(_activation_score(best_run, promote, score_map), 2)

    primary, next_win, timing_source, current_supports = pick_primary_timing_window(
        windows, ranked, promote, now,
        min_ad_pd=cfg.min_current_activation,
    )

    domain_house_lords = _build_domain_house_lords(lagna_si, cfg, ranked)
    significator_rank = _build_domain_significator_rank(lagna_si, kundli, cfg, ranked)
    primary_significator = _pick_primary_significator(significator_rank, ranked)
    sig_name = primary_significator.get("name") if primary_significator else None

    timing_periods = _build_three_timing_periods(
        windows, ranked, promote, now, cfg.min_current_activation,
        primary, sig_name,
    )
    if timing_periods:
        primary = timing_periods[0]
        next_win = timing_periods[1] if len(timing_periods) > 1 else next_win

    top3: List[Dict[str, Any]] = list(timing_periods)
    if not top3:
        if primary:
            top3.append(primary)
        if next_win:
            top3.append(next_win)
        future_only = sorted(
            [w for w in windows if w.get("start") and w["start"] > now],
            key=lambda x: x["start"],
        )
        for w in future_only:
            if len(top3) >= 3:
                break
            act = _activation_score(w, promote, score_map)
            if act < cfg.min_current_activation:
                continue
            if all(w.get("start") != x.get("start") for x in top3):
                row = _enrich_window_row(w)
                row["activation_score"] = round(act, 2)
                top3.append(_annotate_significator_on_window(row, sig_name))

    if significator_rank:
        sig_bits = [
            f"{e['planet']}({e['score']})={e.get('tag') or e.get('role')}"
            for e in significator_rank[:8]
        ]
        factors.append(f"STEP2 significators={' · '.join(sig_bits)}")
    elif domain_house_lords:
        lord_bits = [
            f"{hl['tag']}={hl['planet']}({hl['score']})"
            for hl in domain_house_lords[:5]
        ]
        factors.append(f"STEP2 domain_lords={' · '.join(lord_bits)}")
    if primary_significator:
        factors.append(
            f"STEP3 TOP_SIGNIFICATOR={primary_significator.get('name')} "
            f"score={primary_significator.get('score')} "
            f"roles={','.join(primary_significator.get('roles') or []) or primary_significator.get('house_tag') or 'karaka'} "
            f"link={primary_significator.get('link') or '—'} "
            "→ love via this planet AD/PD"
        )
    if timing_periods:
        period_bits = [
            f"#{p.get('rank')} {p.get('start_iso')}→{p.get('end_iso')} "
            f"{p.get('lords') or ''} act={p.get('activation_score')}"
            + (f" love_via={p.get('love_via')}" if p.get("love_via") else "")
            for p in timing_periods
        ]
        factors.append(f"STEP3 PERIODS={' | '.join(period_bits)}")

    factors.append(f"STEP5 windows_found={len(windows)} source={timing_source}")
    if timing_source == "current_dasha_active" and primary:
        factors.append(
            f"STEP5 PRIMARY=CURRENT AD/PD active score={primary.get('activation_score')} "
            f"{primary.get('ad')}/{primary.get('pd')} — cite abhi running period"
        )
    elif timing_source == "next_dasha_scan" and primary:
        factors.append(
            f"STEP5 PRIMARY=NEXT current AD/PD below min {cfg.min_current_activation} "
            f"(running={running_activation}) for {cfg.domain} — "
            f"first active {primary.get('start_iso')}→{primary.get('end_iso')} "
            f"AD/PD={primary.get('ad')}/{primary.get('pd')} score={primary.get('activation_score')}"
        )
    elif timing_source == "no_qualified_window":
        factors.append(
            f"STEP5 PRIMARY=NONE — no AD/PD/PD window scored >= {cfg.min_current_activation}; "
            "do not cite sub-threshold dasha periods"
        )
    elif primary:
        factors.append("STEP5 PRIMARY=qualified window")

    dt_result: Dict[str, Any] = {}
    if check_double_transit and cfg.double_transit_houses:
        try:
            dt_result = check_double_transit(
                kundli,
                now,
                lagna_si,
                kundli.get("planets") or [],
                cfg.double_transit_houses,
            ) or {}
            if dt_result.get("active"):
                factors.append(f"STEP6 double_transit=STRONG {dt_result.get('verdict')}")
            else:
                factors.append(f"STEP6 double_transit={dt_result.get('verdict', 'N/A')}")
        except Exception as exc:
            factors.append(f"STEP6 double_transit skipped: {exc}")

    top_score = primary.get("score", 0) if primary else 5.0
    if dt_result.get("active") and primary:
        top_score *= 0.85
    if not primary:
        verdict, band = cfg.defer_label, "WEAK"
    else:
        verdict, band = _verdict(top_score, cfg)

    payload = {
        "verdict": verdict,
        "band": band,
        "bucket": bucket,
        "domain": cfg.domain,
        "current_window": primary,
        "next_3_windows": top3,
        "timing_periods": timing_periods,
        "domain_house_lords": domain_house_lords,
        "significator_rank": significator_rank,
        "primary_significator": primary_significator,
        "next_child_window": next_win,
        "timing_source": timing_source,
        "current_supports": current_supports,
        "current_running_activation_score": running_activation,
        "min_current_activation": cfg.min_current_activation,
        "top_planets": ranked[:5],
        "kp_layer": kp_layer,
        "double_transit": dt_result,
        "factors": factors,
        "brand_safety_warnings": list(cfg.brand_safety),
        "llm_directives": list(cfg.llm_directives),
        "engine_version": cfg.engine_version,
        "engine_arch": "FILTER→VERIFY→KP→DASHA→TRANSIT→WINDOW",
        "question": question,
    }
    try:
        from event_timing._shared.dasha_kp_sync import attach_dasha_kp_sync

        payload = attach_dasha_kp_sync(payload, kundli, kp)
    except Exception:
        pass
    try:
        from event_timing._shared.step_audit import attach_timing_pipeline_audit

        return attach_timing_pipeline_audit(payload, cfg.domain)
    except Exception:
        return payload
