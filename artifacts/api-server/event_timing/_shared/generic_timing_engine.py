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
_DASHA_MD, _DASHA_AD, _DASHA_PD = 1, 5, 6
_MIN_GAP_DAYS = 45


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
    for k in ("subDashas", "antardashas", "ad", "sub_dashas", "pratyantar", "pd", "children"):
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
        d9 = compute_d9(kundli)
        d9p = (d9 or {}).get("planets") if isinstance(d9, dict) else None
        if not d9p:
            return out
        for pname in candidates:
            si = _planet_sign_idx(d9p, pname)
            if si is None:
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
        windows.append({
            "md": w["md"], "ad": w["ad"], "pd": w["pd"],
            "start": w["start"], "end": w["end"],
            "start_iso": w["start"].strftime("%Y-%m-%d"),
            "end_iso": w["end"].strftime("%Y-%m-%d"),
            "score": round(net, 2),
            "triggers": triggers,
        })
    windows.sort(key=lambda x: (-x["score"], x["start"]))
    return windows


def _pick_top(windows: List[Dict[str, Any]], n: int = 3) -> List[Dict[str, Any]]:
    chosen: List[Dict[str, Any]] = []
    for w in windows:
        if all(abs((w["start"] - c["start"]).days) >= _MIN_GAP_DAYS for c in chosen):
            chosen.append(w)
        if len(chosen) >= n:
            break
    return chosen


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
    top3 = _pick_top(windows, 3)
    factors.append(f"STEP5 windows_found={len(windows)} top3={len(top3)}")

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

    top_score = top3[0]["score"] if top3 else 5.0
    if dt_result.get("active") and top3:
        top_score *= 0.85
    verdict, band = _verdict(top_score, cfg)

    current = None
    for w in windows:
        if w["start"] <= now <= w["end"]:
            current = w
            break
    if not current and top3:
        current = top3[0]

    return {
        "verdict": verdict,
        "band": band,
        "bucket": bucket,
        "domain": cfg.domain,
        "current_window": current,
        "next_3_windows": top3,
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
