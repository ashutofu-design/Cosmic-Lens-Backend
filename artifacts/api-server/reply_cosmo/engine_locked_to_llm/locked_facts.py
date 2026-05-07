"""
locked_facts.py
───────────────
Assembles ALL deterministic chart facts into ONE clean structured block that
the AI is forced to MIRROR (never invent counts/names).

Pulls from:
  • chart_intelligence.analyze_chart   → lagna, dignities, house lords,
                                          yogas, mangal-dosh, sade-sati
  • dosh_engine.analyze_doshas         → 9-dosh status + counts
  • shadbala.compute_shadbala          → planet strength % (when computable)
  • planet_strength.verdict_table      → STRONG/MODERATE/WEAK band

Single entry point:
    build_locked_facts(kundli, birth=None) -> str

Returns "" if not enough data.  Never raises.
"""

from __future__ import annotations
from typing import Any, Optional


def _safe(call):
    try:
        return call()
    except Exception as exc:  # noqa: BLE001
        print(f"[locked_facts] {call.__name__ if hasattr(call,'__name__') else 'op'} failed: {exc}")
        return None


def _normalise_planets_for_dosh(kundli: dict) -> list:
    """dosh_engine expects {name, house, longitude, sign, retrograde}."""
    out = []
    for p in (kundli.get("planets") or []):
        if not isinstance(p, dict):
            continue
        out.append({
            "name":       p.get("name"),
            "house":      p.get("house"),
            "longitude":  p.get("longitude"),
            "sign":       p.get("sign"),
            "retrograde": bool(p.get("retrograde")),
        })
    return out


def _normalise_planets_for_shadbala(kundli: dict) -> list:
    """compute_shadbala expects {name, lon, house, retrograde}."""
    out = []
    for p in (kundli.get("planets") or []):
        if not isinstance(p, dict):
            continue
        out.append({
            "name":       p.get("name"),
            "lon":        p.get("longitude"),
            "house":      p.get("house"),
            "retrograde": bool(p.get("retrograde")),
        })
    return out


def _lagna_sign_idx(kundli: dict, intel: dict) -> Optional[int]:
    SIGNS = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo",
             "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"]
    name = intel.get("lagna_sign") or kundli.get("ascendant") or kundli.get("lagna")
    if isinstance(name, str):
        try:
            return SIGNS.index(name)
        except ValueError:
            pass
    ad = kundli.get("ascendantDeg") or kundli.get("ascendant_lon")
    if isinstance(ad, (int, float)):
        return int(ad % 360 / 30)
    return None


# ── Yoga polarity classifier ────────────────────────────────────────────────
# Tags each detected yoga as POSITIVE / NEGATIVE / NEUTRAL so the AI never
# mistakes a misery-yoga (e.g. Kemadruma) for a "blessing yoga". Matched by
# substring on the yoga name. Extend lists as new detectors are added.
_NEGATIVE_YOGA_KEYWORDS = (
    "Kemadruma", "Daridra", "Shakata", "Visha yoga", "Visha-yoga",
    "Punarphoo", "Kala Sarpa", "Kalasarpa", "Kaal Sarp", "Kaal-Sarp",
    "Guru-Chandala", "Guru Chandal", "Angarak", "Pisach",
)
_NEUTRAL_YOGA_KEYWORDS = (
    "Vipareeta",  # adversity-converts — context-dependent, mark neutral
)


def _yoga_polarity(name: str) -> str:
    s = (name or "")
    if any(k.lower() in s.lower() for k in _NEGATIVE_YOGA_KEYWORDS):
        return "NEGATIVE"
    if any(k.lower() in s.lower() for k in _NEUTRAL_YOGA_KEYWORDS):
        return "NEUTRAL"
    return "POSITIVE"


_POLARITY_TAG = {"POSITIVE": "[+ POSITIVE]", "NEGATIVE": "[− NEGATIVE]", "NEUTRAL": "[~ NEUTRAL]"}


def _format_yoga_block(yogas: list) -> str:
    if not yogas:
        return ("▸ YOGA COUNT: 0\n"
                "▸ POSITIVE YOGAS: 0   NEGATIVE: 0   NEUTRAL: 0\n"
                "▸ YOGA LIST: (none of the major classical yogas detected)")
    pos = neg = neu = 0
    rows = []
    for y in yogas:
        pol = _yoga_polarity(y)
        if pol == "POSITIVE":   pos += 1
        elif pol == "NEGATIVE": neg += 1
        else:                   neu += 1
        rows.append((pol, y))
    # Clean (raw) name = yoga string up to "(" or " yoga" — used for safe
    # name-listing in user-facing replies (Rule B). Polarity tags are for
    # AI internal reasoning ONLY and must never be echoed to the user.
    def _clean(y: str) -> str:
        s = y.split("(")[0].strip()
        return s if s else y
    raw_names = [_clean(y) for _, y in rows]
    lines = [
        f"▸ YOGA COUNT: {len(yogas)}",
        f"▸ POSITIVE YOGAS: {pos}   NEGATIVE: {neg}   NEUTRAL: {neu}",
        f"▸ YOGA NAMES (raw, USE THESE for any 'kaunse yog' answer — NEVER include the [+/−/~] tags below): {', '.join(raw_names)}",
        "▸ YOGA LIST (with polarity tags — POSITIVE=blessing, NEGATIVE=struggle, NEUTRAL=context-dependent. Tags are FOR YOUR REASONING ONLY, do NOT echo to user):",
    ]
    for i, (pol, y) in enumerate(rows, 1):
        lines.append(f"   {i}. {_POLARITY_TAG[pol]} {y}")
    return "\n".join(lines)


def _format_dosh_block(dosh: dict) -> str:
    if not isinstance(dosh, dict):
        return "▸ DOSHA DATA: (unavailable)"
    actives = [d for d in dosh.get("dosh_list", []) if d.get("status") == "Active"]
    milds   = [d for d in dosh.get("dosh_list", []) if d.get("status") == "Mild"]
    lines = [
        f"▸ DOSHA COUNT (Active): {len(actives)}",
        f"▸ DOSHA COUNT (Mild):   {len(milds)}",
        f"▸ DOSHA COUNT (None):   {dosh.get('none_count', 0)}",
    ]
    if actives:
        lines.append("▸ ACTIVE DOSHAS:")
        for i, d in enumerate(actives, 1):
            lines.append(f"   {i}. {d.get('name','?')} — {d.get('headline','')}")
    if milds:
        lines.append("▸ MILD DOSHAS:")
        for i, d in enumerate(milds, 1):
            lines.append(f"   {i}. {d.get('name','?')} — {d.get('headline','')}")
    if not actives and not milds:
        lines.append("▸ ACTIVE DOSHAS: (none — chart is dosha-free)")
    return "\n".join(lines)


# ─── Sprint-25 Fix-J: deterministic strength facts ─────────────────────────
# Vargottam (D1 sign == D9 sign) + STRONG / MODERATE / WEAK buckets are
# precomputed and emitted explicitly into the prompt so the narrator cannot
# fabricate ("Moon vargottam" when Moon is Mithun→Makar across D1/D9).
# Also exposed via compute_strength_facts() for the supertype validator to
# enforce "named planets MUST come from these buckets" at response time.
_SIGN_NORM_ALIASES = {
    "mesh": "aries", "vrishabh": "taurus", "vrishabha": "taurus",
    "mithun": "gemini", "mithuna": "gemini",
    "kark": "cancer", "karka": "cancer", "karkat": "cancer",
    "simh": "leo", "simha": "leo",
    "kanya": "virgo",
    "tula": "libra", "tul": "libra",
    "vrishchik": "scorpio", "vrischika": "scorpio", "vrischik": "scorpio",
    "dhanu": "sagittarius", "dhanus": "sagittarius",
    "makar": "capricorn", "makara": "capricorn",
    "kumbh": "aquarius", "kumbha": "aquarius",
    "meen": "pisces", "meena": "pisces",
}


def _norm_sign_name(s: Any) -> str:
    if not isinstance(s, str):
        return ""
    k = s.strip().lower()
    return _SIGN_NORM_ALIASES.get(k, k)


def compute_strength_facts(kundli: Any,
                           verdicts: Optional[dict] = None) -> dict:
    """Deterministic strength buckets for a chart.

    Returns:
        {
          "vargottam": [planet_name, ...],   # D1 sign == D9 sign
          "strong":    [planet_name, ...],   # verdict band STRONG
          "moderate":  [planet_name, ...],   # verdict band MODERATE
          "weak":      [planet_name, ...],   # verdict band WEAK
        }

    Cached on `kundli["_strength_facts_cache"]` so prompt builder + validator
    pay the cost only once per request.
    """
    if isinstance(kundli, dict):
        cached = kundli.get("_strength_facts_cache")
        if isinstance(cached, dict) and cached.get("_built"):
            return cached

    out: dict = {"vargottam": [], "strong": [], "moderate": [], "weak": [],
                 "_built": True}

    if not isinstance(kundli, dict):
        return out

    # ── Vargottam: D1 sign == D9 sign ────────────────────────────────────
    d1_signs: dict[str, str] = {}
    for p in (kundli.get("planets") or []):
        if not isinstance(p, dict):
            continue
        nm = p.get("name") or p.get("planet")
        sg = p.get("sign")
        if isinstance(nm, str) and isinstance(sg, str):
            d1_signs[nm] = _norm_sign_name(sg)

    d9 = ((kundli.get("divisionalCharts") or {}).get("D9") or {})
    d9_signs: dict[str, str] = {}
    d9_planets = d9.get("planets") if isinstance(d9, dict) else None
    if isinstance(d9_planets, list):
        for p in d9_planets:
            if not isinstance(p, dict):
                continue
            nm = p.get("name") or p.get("planet")
            sg = p.get("sign")
            if isinstance(nm, str) and isinstance(sg, str):
                d9_signs[nm] = _norm_sign_name(sg)

    out["vargottam"] = sorted([
        nm for nm in d1_signs
        if nm in d9_signs and d1_signs[nm] and d1_signs[nm] == d9_signs[nm]
    ])

    # ── STRONG / MODERATE / WEAK buckets (from verdict_table) ────────────
    if isinstance(verdicts, dict):
        for nm, v in verdicts.items():
            band = (v or {}).get("verdict") if isinstance(v, dict) else None
            if band == "STRONG":
                out["strong"].append(nm)
            elif band == "MODERATE":
                out["moderate"].append(nm)
            elif band == "WEAK":
                out["weak"].append(nm)
        out["strong"]   = sorted(out["strong"])
        out["moderate"] = sorted(out["moderate"])
        out["weak"]     = sorted(out["weak"])

    if isinstance(kundli, dict):
        kundli["_strength_facts_cache"] = out

    return out


def _format_strength_block(verdicts: dict,
                           dignities: list,
                           strength_facts: Optional[dict] = None) -> str:
    """Tabular planet strength block + explicit vargottam / bucket lines.

    `strength_facts` is the dict returned by `compute_strength_facts()`. When
    present, two extra lines are emitted so the LLM can ground its answer:
        ▸ VARGOTTAM (D1 sign == D9 sign): Mars, Jupiter
        ▸ STRENGTH BUCKETS — STRONG: Mars, Jupiter | MODERATE: Sun | WEAK: Saturn
    """
    if not verdicts:
        return "▸ PLANET STRENGTHS: (unavailable)"
    # Build dignity lookup for sign/house annotations
    sign_house = {row["planet"]: (row.get("sign","?"), row.get("house","?"))
                  for row in (dignities or []) if isinstance(row, dict) and row.get("planet")}
    lines = ["▸ PLANET STRENGTHS:"]
    order = ["Sun","Moon","Mars","Mercury","Jupiter","Venus","Saturn","Rahu","Ketu"]
    for p in order:
        v = verdicts.get(p)
        if not v:
            continue
        sign, house = sign_house.get(p, ("?","?"))
        lines.append(f"   {p:<8} {v['verdict']:<8} ({sign} H{house} — {v['reason']})")

    if isinstance(strength_facts, dict):
        vg = strength_facts.get("vargottam") or []
        lines.append(
            "▸ VARGOTTAM (D1 sign == D9 sign): "
            + (", ".join(vg) if vg else "(none — no planet has same sign in D1 and D9)")
        )
        s_strong = strength_facts.get("strong")   or []
        s_mod    = strength_facts.get("moderate") or []
        s_weak   = strength_facts.get("weak")     or []
        lines.append(
            "▸ STRENGTH BUCKETS — "
            f"STRONG: {', '.join(s_strong) if s_strong else '(none)'} | "
            f"MODERATE: {', '.join(s_mod) if s_mod else '(none)'} | "
            f"WEAK: {', '.join(s_weak) if s_weak else '(none)'}"
        )
        lines.append(
            "   ▸ When asked which planets are strong/weak/vargottam, answer "
            "ONLY from the lists on the two lines above. Do NOT move planets "
            "between buckets, do NOT invent vargottam."
        )
    return "\n".join(lines)


# ── Dasha helpers (Phase 2.5.11 — current + next-5-yr horizon) ──────
# Tolerantly normalize either of the two known dasha-array shapes so
# the LLM block can compute the active MD/AD/PD AND list every dasha
# transition over the next 5 years from a single normalized chain.
#   Shape A (Vimshottari export): {planet, startDate, endDate, years,
#                                  subDashas: [{planet, startDate, ...}]}
#   Shape B (engine internal):    {lord, start, end,
#                                  antardashas: [{lord, start, end,
#                                                 pratyantar: [...]}]}
def _parse_iso(v):
    """Parse 'YYYY-MM-DD' or 'YYYY-MM-DDTHH:MM:SS' → datetime, else None."""
    from datetime import datetime
    if v is None:
        return None
    if hasattr(v, "isoformat"):
        return v
    s = str(v).strip()
    if not s:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M",
                "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    # Last-resort: strip a trailing Z / fractional seconds
    try:
        return datetime.fromisoformat(s.rstrip("Z").split(".")[0])
    except Exception:
        return None


def _normalize_dasha_array(kundli: dict) -> list:
    """Return list of MD dicts: {lord, start, end, ads:[{lord, start, end,
    pds:[{lord, start, end}]}]}. Tolerates both export shapes."""
    raw = kundli.get("dashas") or []
    if not isinstance(raw, list):
        return []
    out = []
    for md in raw:
        if not isinstance(md, dict):
            continue
        lord = md.get("planet") or md.get("lord")
        s = _parse_iso(md.get("startDate") or md.get("start"))
        e = _parse_iso(md.get("endDate") or md.get("end"))
        ads_raw = md.get("subDashas") or md.get("antardashas") or []
        ads = []
        for ad in ads_raw:
            if not isinstance(ad, dict):
                continue
            pds_raw = (ad.get("subDashas") or ad.get("pratyantar")
                       or ad.get("pratyantardashas") or [])
            pds = []
            for pd in pds_raw:
                if not isinstance(pd, dict):
                    continue
                pds.append({
                    "lord":  pd.get("planet") or pd.get("lord"),
                    "start": _parse_iso(pd.get("startDate") or pd.get("start")),
                    "end":   _parse_iso(pd.get("endDate")   or pd.get("end")),
                })
            ads.append({
                "lord":  ad.get("planet") or ad.get("lord"),
                "start": _parse_iso(ad.get("startDate") or ad.get("start")),
                "end":   _parse_iso(ad.get("endDate")   or ad.get("end")),
                "pds":   pds,
            })
        out.append({"lord": lord, "start": s, "end": e, "ads": ads})
    return out


def _fmt_d(dt) -> str:
    if dt is None:
        return "?"
    return dt.strftime("%Y-%m-%d")


def _format_dasha_block(kundli: dict) -> str:
    """Phase 2.5.11 — emit current MD/AD/PD + every dasha transition
    in the next 5 years (MD changes + AD changes within current MD).
    Also accepts a `currentDasha` compact form as a fallback when the
    full `dashas` array is missing."""
    from datetime import datetime, timedelta

    md_chain = _normalize_dasha_array(kundli)

    # ── Fallback: compact currentDasha-only form (no horizon possible) ──
    if not md_chain:
        cd = kundli.get("currentDasha") or {}
        if not isinstance(cd, dict) or not cd:
            return "▸ CURRENT DASHA: (unavailable)"
        md  = cd.get("maha") or cd.get("mahadasha") or cd.get("md") or cd.get("planet")
        ad  = cd.get("antar") or cd.get("antardasha") or cd.get("ad")
        pd_ = cd.get("pratyantar") or cd.get("pd")
        start = cd.get("startDate") or cd.get("start")
        end   = cd.get("endDate") or cd.get("end")
        parts = []
        if md: parts.append(f"{md} Mahadasha")
        if ad: parts.append(f"→ {ad} Antardasha")
        if pd_: parts.append(f"→ {pd_} Pratyantar")
        line = " ".join(parts) if parts else "(unavailable)"
        extra = (f"\n▸ DASHA WINDOW: {start or '?'} to {end or '?'}"
                 if (start or end) else "")
        return (f"▸ CURRENT DASHA: {line}{extra}\n"
                f"▸ DASHA TIMELINE (next 5 years): "
                f"(unavailable — full dasha array missing)")

    now = datetime.utcnow()
    horizon_end = now + timedelta(days=int(5 * 365.25))

    # ── Locate current MD / AD / PD ─────────────────────────────────
    cur_md = next((m for m in md_chain
                   if m["start"] and m["end"]
                   and m["start"] <= now <= m["end"]), None)
    cur_ad = cur_pd = None
    if cur_md:
        cur_ad = next((a for a in cur_md["ads"]
                       if a["start"] and a["end"]
                       and a["start"] <= now <= a["end"]), None)
        if cur_ad:
            cur_pd = next((p for p in cur_ad["pds"]
                           if p["start"] and p["end"]
                           and p["start"] <= now <= p["end"]), None)

    head_parts = []
    if cur_md: head_parts.append(f"{cur_md['lord']} Mahadasha")
    if cur_ad: head_parts.append(f"→ {cur_ad['lord']} Antardasha")
    if cur_pd: head_parts.append(f"→ {cur_pd['lord']} Pratyantar")
    head = " ".join(head_parts) if head_parts else "(unavailable)"

    pd_window = ""
    if cur_pd and (cur_pd["start"] or cur_pd["end"]):
        pd_window = (f"\n▸ DASHA WINDOW (current PD): "
                     f"{_fmt_d(cur_pd['start'])} → {_fmt_d(cur_pd['end'])}")
    elif cur_ad and (cur_ad["start"] or cur_ad["end"]):
        pd_window = (f"\n▸ DASHA WINDOW (current AD): "
                     f"{_fmt_d(cur_ad['start'])} → {_fmt_d(cur_ad['end'])}")

    # ── Build next-5-yr timeline ────────────────────────────────────
    # Show: every MD that overlaps [now, horizon_end] with its window,
    # and within each shown MD list every AD that overlaps the horizon.
    # Cap total lines so we don't spam — prefer MD changes over AD.
    timeline_lines = []
    md_in_horizon = [m for m in md_chain
                      if m["end"] and m["start"]
                      and m["end"] >= now
                      and m["start"] <= horizon_end]
    for m in md_in_horizon:
        # Mark which segment of this MD overlaps the horizon
        seg_start = max(m["start"], now)
        seg_end   = min(m["end"],   horizon_end)
        marker = "now"  if m is cur_md else "starts"
        timeline_lines.append(
            f"   • {m['lord']} MD ({_fmt_d(m['start'])} → {_fmt_d(m['end'])}) "
            f"[{marker}]")
        # ADs inside the visible segment of this MD
        for a in m["ads"]:
            if not (a["start"] and a["end"]):
                continue
            if a["end"] < seg_start or a["start"] > seg_end:
                continue
            ad_marker = ""
            if a is cur_ad:
                ad_marker = " ← current"
            timeline_lines.append(
                f"       – {m['lord']}-{a['lord']} AD "
                f"({_fmt_d(a['start'])} → {_fmt_d(a['end'])}){ad_marker}")
        # Hard cap to keep block size bounded for the LLM
        if len(timeline_lines) >= 60:
            timeline_lines.append("   … (truncated — showing 5-yr horizon only)")
            break

    timeline_block = ""
    if timeline_lines:
        timeline_block = ("\n▸ DASHA TIMELINE (next 5 years — MD + AD changes):\n"
                          + "\n".join(timeline_lines))

    return f"▸ CURRENT DASHA: {head}{pd_window}{timeline_block}"


def _format_house_lords(intel: dict) -> str:
    hl = intel.get("house_lords") or []
    if not hl:
        return ""
    items = []
    for h in hl:
        if h.get("lord_in_house"):
            items.append(f"H{h['house']}({h['sign']})→{h['lord']} sits H{h['lord_in_house']}")
        else:
            items.append(f"H{h['house']}({h['sign']})→{h['lord']}")
    return "▸ HOUSE-LORD PLACEMENTS:\n   " + "; ".join(items)


def _format_basics(kundli: dict, intel: dict) -> str:
    parts = []
    if intel.get("lagna_sign"):
        parts.append(f"▸ LAGNA: {intel['lagna_sign']}")
    moon_sign = kundli.get("moonSign") or kundli.get("moon_sign")
    if moon_sign:
        parts.append(f"▸ MOON SIGN (Rashi): {moon_sign}")
    sun_sign = kundli.get("sunSign")
    if sun_sign:
        parts.append(f"▸ SUN SIGN: {sun_sign}")
    nak = kundli.get("nakshatra")
    if nak:
        pada = kundli.get("nakshatraPada")
        line = f"▸ NAKSHATRA: {nak}" + (f" (Pada {pada})" if pada else "")
        parts.append(line)
    if intel.get("sade_sati"):
        parts.append(f"▸ SADE-SATI: {intel['sade_sati']}")
    return "\n".join(parts)


# Sprint-26 Fix-K: engine status tracker. Populated by build_locked_facts
# every call so callers (openai_helper.py timing-validator) can reason
# about whether the engine actually produced timing data, instead of
# silently rejecting the AI's reasonable answer just because some phase
# crashed upstream.
#
# Storage is thread-local — Flask serves requests on multiple threads,
# and a plain module-global dict would let one request overwrite another's
# status between build_locked_facts() and get_last_engine_status(),
# producing wrong soften/reject decisions under concurrency.
import threading as _threading_fixk
_FIXK_TLS = _threading_fixk.local()


def _fixk_get_status() -> dict[str, Any]:
    s = getattr(_FIXK_TLS, "status", None)
    if s is None:
        s = {"ok": [], "skipped": [], "failed": [], "overall": "empty"}
        _FIXK_TLS.status = s
    return s


def get_last_engine_status() -> dict[str, Any]:
    """Return the engine status from the most recent build_locked_facts call
    on THIS thread. Thread-local — safe under Flask's threaded server."""
    return dict(_fixk_get_status())


def _record_phase(name: str, status: str, reason: str = "") -> None:
    """Record one phase's outcome. status ∈ {ok, skipped, failed}."""
    entry = {"phase": name, "reason": reason} if reason else {"phase": name}
    _fixk_get_status()[status].append(entry)


def _finalise_engine_status() -> None:
    """Compute overall verdict after all phases have reported."""
    s = _fixk_get_status()
    ok = len(s["ok"])
    failed = len(s["failed"])
    if ok == 0:
        s["overall"] = "empty"
    elif failed == 0:
        s["overall"] = "ok"
    else:
        s["overall"] = "partial"


# Phase 4.2 — primary vs optional phase classifier (Apr 28, 2026).
# PRIMARY phases (phase-A through phase-G) are core kundli facts that MUST
# succeed — birth time/date is guaranteed present per the gating constraint
# ("ask section bina kundli ke khulta hi nahi"). Failure of any primary
# phase means a real backend bug, NOT a legitimate data gap, so the timing
# validator must REFUSE instead of silently softening (Sprint-26 Fix-K
# inversion). OPTIONAL phases (phase-H onward, Sprint-33+) may legitimately
# fail/skip and only warrant a footer warning.
import re as _re_fixk_phase
_PRIMARY_PHASE_RX = _re_fixk_phase.compile(r"^phase-[A-G]\b", _re_fixk_phase.IGNORECASE)


def _is_primary_phase(name: str) -> bool:
    """True if this phase is core (failure → user-facing refusal)."""
    if not name or not isinstance(name, str):
        return False
    return bool(_PRIMARY_PHASE_RX.search(name.strip()))


def build_locked_facts(kundli: Any, birth: Any = None) -> str:
    """Assemble the LOCKED FACTS block. Returns "" if kundli is empty."""
    # Reset status tracker for this call (thread-local).
    s = _fixk_get_status()
    s["ok"] = []
    s["skipped"] = []
    s["failed"] = []
    s["overall"] = "empty"

    # Phase 4.2 — primary phase tracking (Apr 28, 2026).
    # The /api/ask endpoint is gated on a complete kundli (birth time + date
    # + place required to even open the ask section), so any missing core
    # fact here is a real backend bug — NOT a legitimate data gap. Record
    # primary phases so the downstream timing-validator can REFUSE honestly
    # instead of silently softening (Sprint-26 Fix-K inversion).
    if not isinstance(kundli, dict):
        try:
            _record_phase("phase-A chart-intel (core)", "failed",
                          f"kundli not a dict (type={type(kundli).__name__})")
        except Exception:
            pass
        return ""
    if not kundli.get("planets"):
        try:
            _record_phase("phase-A chart-intel (core)", "failed",
                          "kundli has no planets array")
        except Exception:
            pass
        return ""

    # Lazy imports to avoid circular dependencies and keep test paths light
    try:
        from chart_intelligence import analyze_chart  # type: ignore
    except Exception as exc:  # noqa: BLE001
        print(f"[locked_facts] import chart_intelligence failed: {exc}")
        try:
            _record_phase("phase-A chart-intel (core)", "failed",
                          f"import failed: {exc}")
        except Exception:
            pass
        return ""

    # Phase 4.2 — phase-A core chart intelligence (must succeed)
    try:
        intel = analyze_chart(kundli, birth) or {}
        if not intel:
            try:
                _record_phase("phase-A chart-intel (core)", "failed",
                              "analyze_chart returned empty")
            except Exception:
                pass
            return ""
        try:
            _record_phase("phase-A chart-intel (core)", "ok")
        except Exception:
            pass
    except Exception as exc:  # noqa: BLE001
        print(f"[locked_facts] analyze_chart failed: {exc}")
        try:
            _record_phase("phase-A chart-intel (core)", "failed", str(exc))
        except Exception:
            pass
        return ""

    # Phase 4.2 — phase-B dasha presence (kundli must carry dasha info
    # for any timing/event question to be answerable honestly).
    # Accept multiple schema variants:
    #   - currentDasha.{maha|md|mahadasha|MD}   (compact form)
    #   - dashas: [...]                         (array form, vimshottari)
    #   - currentPhase.name                     (computed display form)
    try:
        _cd = kundli.get("currentDasha") or kundli.get("dasha") or {}
        _cph = kundli.get("currentPhase") or {}
        _dashas = kundli.get("dashas") or []
        _has_compact = isinstance(_cd, dict) and any(
            _cd.get(k) for k in ("maha", "md", "mahadasha", "MD",
                                  "lord", "planet")
        )
        _has_array = isinstance(_dashas, list) and len(_dashas) > 0
        _has_phase = isinstance(_cph, dict) and bool(_cph.get("name"))
        if _has_compact or _has_array or _has_phase:
            _record_phase("phase-B dasha-presence (core)", "ok")
        else:
            _record_phase("phase-B dasha-presence (core)", "failed",
                          "kundli missing all dasha forms "
                          "(currentDasha/dashas/currentPhase)")
    except Exception as exc:  # noqa: BLE001
        try:
            _record_phase("phase-B dasha-presence (core)", "failed", str(exc))
        except Exception:
            pass

    # Phase 4.2 — phase-C lagna presence (house facts depend on this)
    try:
        _lg = kundli.get("ascendant") or kundli.get("lagna")
        _lg_sign = _lg.get("sign") if isinstance(_lg, dict) else _lg
        if isinstance(_lg_sign, str) and _lg_sign.strip():
            _record_phase("phase-C lagna-presence (core)", "ok")
        else:
            _record_phase("phase-C lagna-presence (core)", "failed",
                          "kundli missing ascendant/lagna sign")
    except Exception as exc:  # noqa: BLE001
        try:
            _record_phase("phase-C lagna-presence (core)", "failed", str(exc))
        except Exception:
            pass

    # Doshas (9-dosh engine) — phase-D (core: powers manglik/dosh truth)
    dosh = None
    try:
        from dosh_engine import analyze_doshas  # type: ignore
        dosh = analyze_doshas(_normalise_planets_for_dosh(kundli),
                              kundli.get("nakshatra") or "")
        try:
            _record_phase("phase-D dosh-engine (core)", "ok")
        except Exception:
            pass
    except Exception as exc:  # noqa: BLE001
        print(f"[locked_facts] dosh_engine failed: {exc}")
        try:
            _record_phase("phase-D dosh-engine (core)", "failed", str(exc))
        except Exception:
            pass

    # Shadbala (best-effort — needs lagna + lon)
    shadbala = None
    try:
        from shadbala import compute_shadbala  # type: ignore
        lagna_idx = _lagna_sign_idx(kundli, intel)
        if lagna_idx is not None:
            shadbala = compute_shadbala(_normalise_planets_for_shadbala(kundli),
                                        lagna_sign=lagna_idx)
    except Exception as exc:  # noqa: BLE001
        print(f"[locked_facts] shadbala failed: {exc}")

    # Planet strength verdicts (uses shadbala if present, else fallback)
    # phase-E (core: powers planet_strength truth class in Phase 4.1)
    verdicts = {}
    try:
        from planet_strength import verdict_table  # type: ignore
        verdicts = verdict_table(intel.get("dignities") or [], shadbala)
        try:
            _record_phase("phase-E planet-verdicts (core)", "ok")
        except Exception:
            pass
    except Exception as exc:  # noqa: BLE001
        print(f"[locked_facts] planet_strength failed: {exc}")
        try:
            _record_phase("phase-E planet-verdicts (core)", "failed", str(exc))
        except Exception:
            pass

    # Sprint-25 Fix-J: deterministic vargottam + strength buckets
    strength_facts = {}
    try:
        strength_facts = compute_strength_facts(kundli, verdicts)
    except Exception as exc:  # noqa: BLE001
        print(f"[locked_facts] compute_strength_facts failed: {exc}")

    # Sprint-2 — Ashtakavarga (Sarvashtakavarga per house)
    av_str = ""
    try:
        from ashtakavarga import compute_ashtakavarga, format_sav_summary  # type: ignore
        lagna_idx = _lagna_sign_idx(kundli, intel)
        # Need sign_idx per planet — use dignity rows
        SIGN_NAMES = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo",
                      "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"]
        av_planets = []
        for p in (kundli.get("planets") or []):
            if not isinstance(p, dict):
                continue
            sn = p.get("sign")
            si = p.get("sign_idx")
            if si is None and isinstance(sn, str) and sn in SIGN_NAMES:
                si = SIGN_NAMES.index(sn)
            av_planets.append({"name": p.get("name"), "sign_idx": si})
        if lagna_idx is not None:
            av = compute_ashtakavarga(av_planets, lagna_idx)
            av_str = format_sav_summary(av) if av else ""
    except Exception as exc:  # noqa: BLE001
        print(f"[locked_facts] ashtakavarga failed: {exc}")

    # Sprint-2 — Aspects (Graha Drishti)
    asp_str = ""
    asp_obj = None
    try:
        from aspects import compute_aspects, format_aspect_summary  # type: ignore
        asp_obj = compute_aspects(kundli.get("planets") or [], _lagna_sign_idx(kundli, intel))
        asp_str = format_aspect_summary(asp_obj) if asp_obj else ""
    except Exception as exc:  # noqa: BLE001
        print(f"[locked_facts] aspects failed: {exc}")

    # Sprint-3 — Bhava Bala (house strength composite)
    bb_str = ""
    try:
        from bhava_bala import compute_bhava_bala, format_bhava_bala_summary  # type: ignore
        bb = compute_bhava_bala(intel, verdicts, asp_obj)
        bb_str = format_bhava_bala_summary(bb) if bb else ""
    except Exception as exc:  # noqa: BLE001
        print(f"[locked_facts] bhava_bala failed: {exc}")

    # Sprint-18.5 — Bhava Bala Deep (BPHS 4-fold per house: Adhipati + Digbala
    # + Drishti + Naisargika = 12 × 4 = 48 calculations)
    bbd_str = ""
    try:
        from vedic.strength.bhava_bala_deep import (compute_bhava_bala_deep,  # type: ignore
                                                    format_bhava_bala_deep_summary)
        _sign_to_idx_bb = {"Aries":0,"Taurus":1,"Gemini":2,"Cancer":3,"Leo":4,"Virgo":5,
                           "Libra":6,"Scorpio":7,"Sagittarius":8,"Capricorn":9,
                           "Aquarius":10,"Pisces":11}
        _lg_bb = kundli.get("ascendant") or kundli.get("lagna")
        _lg_sign_bb = _lg_bb.get("sign") if isinstance(_lg_bb, dict) else _lg_bb
        _lg_idx_bb = _sign_to_idx_bb.get(_lg_sign_bb) if isinstance(_lg_sign_bb, str) else None
        bbd = compute_bhava_bala_deep(intel, shadbala, asp_obj, _lg_idx_bb)
        bbd_str = format_bhava_bala_deep_summary(bbd) if bbd else ""
    except Exception as exc:  # noqa: BLE001
        print(f"[locked_facts] bhava_bala_deep (Sprint-18.5) failed: {exc}")

    # Sprint-18 placeholder — actual compute moved AFTER all divisional charts
    # so it can read real per-varga sign_idx (architect fix).
    bd_str = ""

    # Sprint-3 — Jaimini Karakas
    kk_str = ""
    try:
        from karakas import compute_karakas, format_karakas_summary  # type: ignore
        kk = compute_karakas(kundli.get("planets") or [])
        kk_str = format_karakas_summary(kk) if kk else ""
    except Exception as exc:  # noqa: BLE001
        print(f"[locked_facts] karakas failed: {exc}")

    # Sprint-4 — D9 / D10 divisional charts
    div_str = ""
    try:
        from divisional_charts import compute_d9, compute_d10, format_divisional_summary  # type: ignore
        # Lagna longitude — best effort: try kundli.lagna.longitude or intel
        lagna_lon = None
        lg = kundli.get("lagna") or kundli.get("ascendant")
        if isinstance(lg, dict):
            lagna_lon = lg.get("longitude") or lg.get("lon")
        d9  = compute_d9(kundli.get("planets") or [], lagna_lon)
        d10 = compute_d10(kundli.get("planets") or [], lagna_lon)
        div_str = format_divisional_summary(d9, d10, intel)
    except Exception as exc:  # noqa: BLE001
        print(f"[locked_facts] divisional_charts failed: {exc}")

    # Sprint-9 — D2 Hora + D3 Drekkana + D7 Saptamsa + D12 Dwadasamsa
    extra_div_str = ""
    try:
        from divisional_charts import (compute_d2, compute_d3, compute_d7,  # type: ignore
                                       compute_d12, format_extra_vargas_summary)
        _planets = kundli.get("planets") or []
        d2  = compute_d2(_planets,  lagna_lon)
        d3  = compute_d3(_planets,  lagna_lon)
        d7  = compute_d7(_planets,  lagna_lon)
        d12 = compute_d12(_planets, lagna_lon)
        extra_div_str = format_extra_vargas_summary(d2, d3, d7, d12, intel)
    except Exception as exc:  # noqa: BLE001
        print(f"[locked_facts] extra vargas (D2/D3/D7/D12) failed: {exc}")

    # Sprint-10 — D16 Shodasamsa + D20 Vimsamsa + D24 Chaturvimsamsa + D27 Bhamsa
    adv_div_str = ""
    try:
        from divisional_charts import (compute_d16, compute_d20, compute_d24,  # type: ignore
                                       compute_d27, format_advanced_vargas_summary)
        _planets2 = kundli.get("planets") or []
        d16 = compute_d16(_planets2, lagna_lon)
        d20 = compute_d20(_planets2, lagna_lon)
        d24 = compute_d24(_planets2, lagna_lon)
        d27 = compute_d27(_planets2, lagna_lon)
        adv_div_str = format_advanced_vargas_summary(d16, d20, d24, d27, intel)
    except Exception as exc:  # noqa: BLE001
        print(f"[locked_facts] advanced vargas (D16/D20/D24/D27) failed: {exc}")

    # Sprint-11 — D30 Trimsamsa + D40 Khavedamsa + D45 Akshavedamsa + D60 Shashtyamsa
    subtle_div_str = ""
    try:
        from divisional_charts import (compute_d30, compute_d40, compute_d45,  # type: ignore
                                       compute_d60, format_subtle_vargas_summary)
        _planets3 = kundli.get("planets") or []
        d30 = compute_d30(_planets3, lagna_lon)
        d40 = compute_d40(_planets3, lagna_lon)
        d45 = compute_d45(_planets3, lagna_lon)
        d60 = compute_d60(_planets3, lagna_lon)
        subtle_div_str = format_subtle_vargas_summary(d30, d40, d45, d60, intel, _planets3)
    except Exception as exc:  # noqa: BLE001
        print(f"[locked_facts] subtle vargas (D30/D40/D45/D60) failed: {exc}")

    # Sprint-12 — Per-varga deep: Vargottama matrix + Shadvarga Bala + Varga-lagna-lord
    deep_div_str = ""
    try:
        from divisional_charts import format_varga_deep_summary  # type: ignore
        deep_div_str = format_varga_deep_summary(
            kundli.get("planets") or [], lagna_lon, intel
        )
    except Exception as exc:  # noqa: BLE001
        print(f"[locked_facts] varga deep (Sprint-12) failed: {exc}")

    # Sprint-18 — Extended Bala (BPHS sub-calculations: Saptavargaja, full Kala Bala,
    # Ishta/Kashta Phala, Vimshopaka Bala, Yuddha Bala). Computed AFTER all
    # divisional charts so Saptavargaja/Vimshopaka use REAL per-varga sign_idx.
    try:
        from datetime import datetime as _dtBD
        from vedic.strength.bala_deep import (compute_bala_deep,  # type: ignore
                                              format_bala_deep_summary)
        from divisional_charts import (compute_d2 as _d2f, compute_d3 as _d3f,  # type: ignore
                                       compute_d7 as _d7f, compute_d9 as _d9f,
                                       compute_d10 as _d10f, compute_d12 as _d12f,
                                       compute_d16 as _d16f, compute_d20 as _d20f,
                                       compute_d24 as _d24f, compute_d27 as _d27f,
                                       compute_d30 as _d30f, compute_d40 as _d40f,
                                       compute_d45 as _d45f, compute_d60 as _d60f)

        _planets_bd = kundli.get("planets") or []
        _sign_to_idx = {"Aries":0,"Taurus":1,"Gemini":2,"Cancer":3,"Leo":4,"Virgo":5,
                        "Libra":6,"Scorpio":7,"Sagittarius":8,"Capricorn":9,"Aquarius":10,"Pisces":11}

        # Compute all 15 vargas (D1 from natal sign + 14 divisionals)
        _all_vargas = {
            "D2":  _d2f(_planets_bd,  lagna_lon),
            "D3":  _d3f(_planets_bd,  lagna_lon),
            "D7":  _d7f(_planets_bd,  lagna_lon),
            "D9":  _d9f(_planets_bd,  lagna_lon),
            "D10": _d10f(_planets_bd, lagna_lon),
            "D12": _d12f(_planets_bd, lagna_lon),
            "D16": _d16f(_planets_bd, lagna_lon),
            "D20": _d20f(_planets_bd, lagna_lon),
            "D24": _d24f(_planets_bd, lagna_lon),
            "D27": _d27f(_planets_bd, lagna_lon),
            "D30": _d30f(_planets_bd, lagna_lon),
            "D40": _d40f(_planets_bd, lagna_lon),
            "D45": _d45f(_planets_bd, lagna_lon),
            "D60": _d60f(_planets_bd, lagna_lon),
        }

        _varga_charts = {}
        for _p in _planets_bd:
            _name = _p.get("name")
            if not _name:
                continue
            _d1_si = _sign_to_idx.get(_p.get("sign"))
            entry = {}
            if _d1_si is not None:
                entry["D1"] = _d1_si
            for _vname, _vdict in _all_vargas.items():
                _info = (_vdict or {}).get(_name) if isinstance(_vdict, dict) else None
                if isinstance(_info, dict):
                    _si = _info.get("sign_idx")
                    if _si is None and _info.get("sign"):
                        _si = _sign_to_idx.get(_info["sign"])
                    if _si is not None:
                        entry[_vname] = _si
            if entry:
                _varga_charts[_name] = entry

        # Birth datetime
        _bdt = None
        try:
            _bsrc = birth or {}
            _dob = _bsrc.get("dob") or _bsrc.get("dateOfBirth") or kundli.get("dob")
            _tob = _bsrc.get("tob") or _bsrc.get("timeOfBirth") or kundli.get("time") or "12:00"
            if _dob:
                # Try multiple formats
                for _fmt in ("%Y-%m-%d %H:%M", "%d %b %Y %I:%M %p",
                             "%d %B %Y %I:%M %p", "%Y-%m-%d %I:%M %p"):
                    try:
                        _bdt = _dtBD.strptime(f"{_dob} {_tob}", _fmt)
                        break
                    except ValueError:
                        continue
        except Exception:
            _bdt = None

        _sun_lon = next((p.get("longitude", 0.0) for p in _planets_bd
                         if p.get("name") == "Sun"), 0.0)

        # Pull shadbala totals + per-planet uchhabala/chesta
        _sb_totals, _ub_map, _cb_map = {}, {}, {}
        if shadbala and isinstance(shadbala, dict):
            for _pn, _data in shadbala.items():
                if isinstance(_data, dict):
                    _sb_totals[_pn] = _data.get("total", 0.0)
                    _sthana = _data.get("sthana") or {}
                    if isinstance(_sthana, dict):
                        _ub_map[_pn] = _sthana.get("uchhabala", 30.0)
                    _cb_map[_pn] = _data.get("chesta", 30.0)

        bd = compute_bala_deep(
            planets=_planets_bd,
            varga_charts=_varga_charts,
            birth_dt=_bdt,
            sun_longitude=_sun_lon,
            shadbala_totals=_sb_totals,
            uchhabala_by_planet=_ub_map,
            chesta_by_planet=_cb_map,
        )
        bd_str = format_bala_deep_summary(bd) if bd else ""
    except Exception as exc:  # noqa: BLE001
        print(f"[locked_facts] bala_deep (Sprint-18) failed: {exc}")

    # Sprint-19 — Classical yogas mega-detector (Vipreet/Dhana/Negative/KaalSarp/Nabhasa/Pravrajya)
    classical_yogas_str = ""
    try:
        from vedic.yogas.classical_yogas import (detect_classical_yogas,  # type: ignore
                                                 format_classical_yogas_summary)
        _lg_cy = kundli.get("ascendant") or kundli.get("lagna")
        _lg_sign_cy = (_lg_cy.get("sign") if isinstance(_lg_cy, dict) else _lg_cy)
        _sti_cy = {n: i for i, n in enumerate([
            "Aries","Taurus","Gemini","Cancer","Leo","Virgo",
            "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"])}
        _lg_idx_cy = (_sti_cy.get(_lg_sign_cy) if isinstance(_lg_sign_cy, str)
                      else _lg_sign_cy if isinstance(_lg_sign_cy, int) else None)
        _cy = detect_classical_yogas(kundli.get("planets") or [], _lg_idx_cy)
        classical_yogas_str = format_classical_yogas_summary(_cy) if _cy else ""
    except Exception as exc:  # noqa: BLE001
        print(f"[locked_facts] classical yogas (Sprint-19) failed: {exc}")

    # Sprint-19.5 — Extra classical yogas (Saraswati, Brahma/Vishnu/Shiva,
    # Lunar peripheral, Karak-Bhuvan, Aakriti remaining 12, Royal yogas,
    # Amsavatara, Neech-Bhanga 4-rule, BPHS Lord-in-house 60+)
    extra_yogas_str = ""
    try:
        from vedic.yogas.extra_yogas import (detect_extra_yogas,  # type: ignore
                                             format_extra_yogas_summary)
        _ey = detect_extra_yogas(kundli.get("planets") or [], _lg_idx_cy)
        extra_yogas_str = format_extra_yogas_summary(_ey) if _ey else ""
    except Exception as exc:  # noqa: BLE001
        print(f"[locked_facts] extra yogas (Sprint-19.5) failed: {exc}")

    # Sprint-20 — Tier-4 Doshas Deep (Mangal full BPHS, Pitra 3-reasons,
    # Sade-Sati phase, Kantaka Shani, Vish Yog, Karaka Doshas, Grahan, Shrapit)
    deep_doshas_str = ""
    try:
        from vedic.doshas.dosh_deep import (detect_deep_doshas,  # type: ignore
                                            format_deep_doshas_summary)
        # Try to get current Saturn sign for transit-based doshas
        _cur_sat = None
        try:
            from chart_intelligence import _current_saturn_sign  # type: ignore
            _cur_sat = _current_saturn_sign()
        except Exception:
            pass
        _nak = (kundli.get("nakshatra") or
                (kundli.get("moon") or {}).get("nakshatra") or "")
        if isinstance(_nak, dict):
            _nak = _nak.get("name", "")
        _dd = detect_deep_doshas(kundli.get("planets") or [], _lg_idx_cy,
                                 current_saturn_sign=_cur_sat,
                                 nakshatra_name=_nak)
        deep_doshas_str = format_deep_doshas_summary(_dd) if _dd else ""
    except Exception as exc:  # noqa: BLE001
        print(f"[locked_facts] deep doshas (Sprint-20) failed: {exc}")

    # Sprint-21 — Tier-5 Extra Dashas (Yogini, Ashtottari, Narayana, Karaka,
    # Naisargika, Tara, Brahma, Yogardha + Pinda/Amshayur longevity)
    extra_dashas_str = ""
    try:
        from vedic.dashas.dasha_extras import (compute_all_extra_dashas,  # type: ignore
                                               format_extra_dashas_summary)
        _ed = compute_all_extra_dashas(kundli)
        extra_dashas_str = format_extra_dashas_summary(_ed) if _ed else ""
    except Exception as exc:  # noqa: BLE001
        print(f"[locked_facts] extra dashas (Sprint-21) failed: {exc}")

    # Sprint-22 — Per-Varga Deep (aspects + ashtakavarga + lagna-lord matrix)
    varga_deep_str = ""
    try:
        from vedic.varga.varga_deep import (compute_varga_deep_all,  # type: ignore
                                            format_varga_deep_summary)
        _vd = compute_varga_deep_all(kundli.get("planets") or [], lagna_lon)
        varga_deep_str = format_varga_deep_summary(_vd) if _vd else ""
    except Exception as exc:  # noqa: BLE001
        print(f"[locked_facts] varga deep (Sprint-22) failed: {exc}")

    # Sprint-23 — Tier-7 Ashtakavarga Deep (Trikona/Ekadhipatya Shodhana,
    # Sodhya Pinda, Transit overlay)
    ashtaka_deep_str = ""
    try:
        from vedic.varga.ashtaka_deep import (compute_ashtaka_deep,  # type: ignore
                                              format_ashtaka_deep_summary,
                                              SIGN_NAMES as _SN)
        _lg_ad = kundli.get("ascendant")
        _lg_si = _SN.index(_lg_ad) if isinstance(_lg_ad, str) and _lg_ad in _SN else None
        # Use natal positions as transit-baseline (real transit can be wired later)
        _transits = {p["name"]: _SN.index(p["sign"])
                     for p in (kundli.get("planets") or [])
                     if isinstance(p, dict) and p.get("name") in
                     ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")
                     and p.get("sign") in _SN}
        _ad = compute_ashtaka_deep(kundli.get("planets") or [], _lg_si,
                                   transit_signs=_transits)
        ashtaka_deep_str = format_ashtaka_deep_summary(_ad) if _ad else ""
    except Exception as exc:  # noqa: BLE001
        print(f"[locked_facts] ashtaka deep (Sprint-23) failed: {exc}")

    # Sprint-24 — Tier-8 Transit Deep (Saturn 12-house detail, Eclipse axis,
    # Fixed Stars overlap)
    transit_deep_str = ""
    try:
        from vedic.transits.transit_deep import (compute_transit_deep,  # type: ignore
                                                 format_transit_deep_summary)
        _td = compute_transit_deep(kundli)
        transit_deep_str = format_transit_deep_summary(_td) if _td else ""
    except Exception as exc:  # noqa: BLE001
        print(f"[locked_facts] transit deep (Sprint-24) failed: {exc}")

    # Sprint-25 — Tier-9 KP Deep (SSS lords, 4-level significators, RP,
    # 249 horary lookup engine, eclipse pin-point)
    kp_deep_str = ""
    try:
        from vedic.kp.kp_deep import (compute_kp_deep,  # type: ignore
                                       format_kp_deep_summary)
        _kpd = compute_kp_deep(kundli)
        kp_deep_str = format_kp_deep_summary(_kpd) if _kpd else ""
    except Exception as exc:  # noqa: BLE001
        print(f"[locked_facts] kp deep (Sprint-25) failed: {exc}")

    # Sprint-26 — Jaimini Rashi Drishti (sign aspects, BPHS Ch.7)
    rashi_drishti_str = ""
    try:
        from vedic.jaimini.rashi_drishti import (compute_rashi_drishti,  # type: ignore
                                                 format_rashi_drishti_summary,
                                                 SIGN_NAMES as _SN_RD)
        _lg_rd = kundli.get("ascendant")
        _lg_si_rd = _SN_RD.index(_lg_rd) if isinstance(_lg_rd, str) and _lg_rd in _SN_RD else None
        _rd = compute_rashi_drishti(kundli.get("planets") or [], _lg_si_rd)
        rashi_drishti_str = format_rashi_drishti_summary(_rd) if _rd else ""
    except Exception as exc:  # noqa: BLE001
        print(f"[locked_facts] rashi drishti (Sprint-26) failed: {exc}")

    # Sprint-27 — Special Lagnas (Sree, Indu, Bhrigu Bindu, Karakamsa)
    special_lagnas_str = ""
    try:
        from vedic.jaimini.special_lagnas import (compute_special_lagnas,  # type: ignore
                                                   format_special_lagnas_summary)
        _sl = compute_special_lagnas(kundli)
        special_lagnas_str = format_special_lagnas_summary(_sl) if _sl else ""
    except Exception as exc:  # noqa: BLE001
        print(f"[locked_facts] special lagnas (Sprint-27) failed: {exc}")

    # Sprint-28 / Phase A2 — Age context (current_age + life-stage + dasha-age window)
    age_context_str = ""
    try:
        from vedic.context.age_context import (compute_age_context,  # type: ignore
                                                format_age_context_summary)
        _ac = compute_age_context(birth or {}, kundli, kundli.get("currentDasha"))
        age_context_str = format_age_context_summary(_ac) if _ac else ""
    except Exception as exc:  # noqa: BLE001
        print(f"[locked_facts] age context (Sprint-28) failed: {exc}")

    # Sprint-29 / Phase B — Full Shadbala sub-bala formatter
    shadbala_full_str = ""
    try:
        from vedic.strength.shadbala_full_format import format_shadbala_full  # type: ignore
        _bd_for_fmt = locals().get("bd") or None
        shadbala_full_str = format_shadbala_full(shadbala, _bd_for_fmt)
    except Exception as exc:  # noqa: BLE001
        print(f"[locked_facts] shadbala full format (Sprint-29) failed: {exc}")

    # Sprint-50 — ASTROCARTOGRAPHY ENGINE (Tier-1 mundane + Tier-2 lines)
    astrocarto_str = ""
    try:
        from vedic.astrocarto.astrocartography_engine import run_astrocartography, format_astrocartography  # type: ignore
        astrocarto_str = format_astrocartography(run_astrocartography(kundli, birth))
    except Exception as exc:  # noqa: BLE001
        print(f"[locked_facts] astrocartography (Sprint-50) failed: {exc}")

    # Sprint-49 / Phase-V — REMEDIES DEEP ENGINE
    remedies_deep_str = ""
    try:
        from vedic.remedies.remedies_deep_engine import run_remedies_engine, format_remedies_engine  # type: ignore
        remedies_deep_str = format_remedies_engine(run_remedies_engine(kundli))
    except Exception as exc:  # noqa: BLE001
        print(f"[locked_facts] remedies deep engine (Sprint-49) failed: {exc}")

    # Sprint-48 — FINANCIAL ASTROLOGY ENGINE (deep + ethical wealth audit)
    financial_str = ""
    try:
        from vedic.financial.financial_engine import run_financial_engine, format_financial_engine  # type: ignore
        financial_str = format_financial_engine(run_financial_engine(kundli))
    except Exception as exc:  # noqa: BLE001
        print(f"[locked_facts] financial engine (Sprint-48) failed: {exc}")

    # Sprint-47 — MODERN CONTEXT REFRAME ENGINE (old astrology in TODAY's world)
    modern_reframe_str = ""
    try:
        from vedic.reframe.modern_context_engine import run_modern_reframe, format_modern_reframe  # type: ignore
        modern_reframe_str = format_modern_reframe(run_modern_reframe(kundli))
    except Exception as exc:  # noqa: BLE001
        print(f"[locked_facts] modern reframe (Sprint-47) failed: {exc}")

    # Sprint-46 — MEDICAL ASTROLOGY ENGINE (full 20-check deep chart-driven medical audit)
    medical_str = ""
    try:
        from vedic.medical.medical_engine import run_medical_engine, format_medical_engine  # type: ignore
        _med_sb = locals().get("shadbala") if "shadbala" in locals() else None
        _med_dasha = (kundli.get("current_dasha")
                      or kundli.get("vimshottari_current")
                      or {})
        medical_str = format_medical_engine(
            run_medical_engine(kundli, birth or {}, _med_sb, _med_dasha))
    except Exception as exc:  # noqa: BLE001
        print(f"[locked_facts] medical engine (Sprint-46) failed: {exc}")

    # Sprint-45 — ASTRO-VASTU ENGINE (full 13-check chart-driven Vastu audit)
    astro_vastu_str = ""
    try:
        from vedic.vastu.astro_vastu_engine import run_astro_vastu_engine, format_astro_vastu  # type: ignore
        _av_sb = locals().get("shadbala") if "shadbala" in locals() else None
        astro_vastu_str = format_astro_vastu(run_astro_vastu_engine(kundli, birth or {}, _av_sb))
    except Exception as exc:  # noqa: BLE001
        print(f"[locked_facts] astro-vastu engine (Sprint-45) failed: {exc}")

    # Sprint-44 / Phase S — Numerology + Vastu Integration (Driver/Conductor/Kua + 8 directions + chart-derived defects)
    phase_s_str = ""
    try:
        from vedic.numerology.phase_s import compute_phase_s, format_phase_s  # type: ignore
        phase_s_str = format_phase_s(compute_phase_s(kundli, birth or {}))
    except Exception as exc:  # noqa: BLE001
        print(f"[locked_facts] phase-S numerology+vastu (Sprint-44) failed: {exc}")

    # Sprint 53-N1 — Numerology DEEP (Lo Shu Grid, Personal Year/Month/Day, Life-Path, Soul-Urge/Personality/Expression, Master numbers, Karmic Debt, Cheiro Compound)
    numerology_deep_str = ""
    try:
        from vedic.numerology.extended import (  # type: ignore
            compute_extended_numerology, format_extended_numerology,
        )
        numerology_deep_str = format_extended_numerology(
            compute_extended_numerology(birth or {})
        )
    except Exception as exc:  # noqa: BLE001
        print(f"[locked_facts] numerology DEEP (Sprint 53-N1) failed: {exc}")

    # Sprint 53-N2 — Numerology PRACTICAL (Pinnacles+Challenges, Career fit, Lucky catalog: color/gem/metal/day/direction/mantra/ishta/fast/dates)
    numerology_practical_str = ""
    try:
        from vedic.numerology.practical import (  # type: ignore
            compute_practical, format_practical,
        )
        numerology_practical_str = format_practical(compute_practical(birth or {}))
    except Exception as exc:  # noqa: BLE001
        print(f"[locked_facts] numerology PRACTICAL (Sprint 53-N2) failed: {exc}")

    # Sprint-43 / Phase R — Panchang Full (Tithi + Nakshatra + Yoga + Karana + Vaar + Ritu/Ayana/Maasa + Samvatsara + Eras)
    phase_r_str = ""
    try:
        from vedic.panchang.phase_r import compute_phase_r, format_phase_r  # type: ignore
        phase_r_str = format_phase_r(compute_phase_r())
    except Exception as exc:  # noqa: BLE001
        print(f"[locked_facts] phase-R panchang (Sprint-43) failed: {exc}")

    # Sprint-42 / Phase Q — Muhurta Full (Choghadiya + Hora + Kaal + Abhijit/Brahma + 35 events)
    phase_q_str = ""
    try:
        from vedic.muhurta.phase_q import compute_phase_q, format_phase_q  # type: ignore
        phase_q_str = format_phase_q(compute_phase_q())
    except Exception as exc:  # noqa: BLE001
        print(f"[locked_facts] phase-Q muhurta (Sprint-42) failed: {exc}")

    # Sprint-41 / Phase P — Compatibility Profile (8 Ashtakoot + Dashakoot + Rajju + Vedha)
    phase_p_str = ""
    try:
        from vedic.compat.phase_p import compute_phase_p, format_phase_p  # type: ignore
        phase_p_str = format_phase_p(compute_phase_p(kundli))
    except Exception as exc:  # noqa: BLE001
        print(f"[locked_facts] phase-P compat (Sprint-41) failed: {exc}")

    # Sprint-40 / Phase O — Lal Kitab Full (Teva + Pakka Ghar + Karak + Rin + Age-dasha)
    lal_kitab_str = ""
    try:
        from vedic.lalkitab.lal_kitab_full import compute_lal_kitab, format_lal_kitab  # type: ignore
        lal_kitab_str = format_lal_kitab(compute_lal_kitab(kundli, birth))
    except Exception as exc:  # noqa: BLE001
        print(f"[locked_facts] phase-O lal-kitab (Sprint-40) failed: {exc}")

    # Sprint-39 / Phase N — Nadi Astrology (1800 amshas + Bhrigu Saral + Gana per planet)
    phase_n_str = ""
    try:
        from vedic.nadi.phase_n import compute_phase_n, format_phase_n  # type: ignore
        phase_n_str = format_phase_n(compute_phase_n(kundli))
    except Exception as exc:  # noqa: BLE001
        print(f"[locked_facts] phase-N nadi (Sprint-39) failed: {exc}")

    # Sprint-38 / Phase M — Sahams Extended (+25 → 55 total)
    sahams_m_str = ""
    try:
        from vedic.tajik.sahams_extended import (compute_phase_m_extra,  # type: ignore
                                                   format_phase_m_summary)
        _sm = compute_phase_m_extra(kundli, birth)
        sahams_m_str = format_phase_m_summary(_sm)
        if _sm and _sm.get("available", True):
            _record_phase("phase-M sahams (Sprint-38)", "ok")
        else:
            _record_phase("phase-M sahams (Sprint-38)", "skipped",
                          (_sm or {}).get("reason", "no output"))
    except Exception as exc:  # noqa: BLE001
        print(f"[locked_facts] phase-M sahams (Sprint-38) failed: {exc}")
        _record_phase("phase-M sahams (Sprint-38)", "failed", str(exc))

    # Sprint-37 / Phase L — Special Lagnas (Bhava/Hora/Ghati/Vighati/Pranapada/Varnada)
    lagnas_l_str = ""
    try:
        from vedic.jaimini.lagnas_phase_l import (compute_lagnas_phase_l,  # type: ignore
                                                    format_lagnas_phase_l_summary)
        _lp = compute_lagnas_phase_l(kundli, birth)
        lagnas_l_str = format_lagnas_phase_l_summary(_lp)
        if _lp and _lp.get("available", True):
            _record_phase("phase-L special lagnas (Sprint-37)", "ok")
        else:
            _record_phase("phase-L special lagnas (Sprint-37)", "skipped",
                          (_lp or {}).get("reason", "no output"))
    except Exception as exc:  # noqa: BLE001
        print(f"[locked_facts] phase-L special lagnas (Sprint-37) failed: {exc}")
        _record_phase("phase-L special lagnas (Sprint-37)", "failed", str(exc))

    # Sprint-36 / Phase K — Avashtas (planetary states)
    avashtas_str = ""
    try:
        from vedic.avashtas.avashtas import (compute_avashtas,  # type: ignore
                                              format_avashtas_summary)
        _av = compute_avashtas(kundli)
        avashtas_str = format_avashtas_summary(_av)
    except Exception as exc:  # noqa: BLE001
        print(f"[locked_facts] avashtas (Sprint-36) failed: {exc}")

    # Sprint-35 / Phase J — Tajik / Varshaphala (Annual)
    phase_j_str = ""
    try:
        from vedic.tajik.varshaphala import (compute_phase_j_tajik,  # type: ignore
                                              format_phase_j_summary)
        _pj = compute_phase_j_tajik(kundli, birth)
        phase_j_str = format_phase_j_summary(_pj)
        if _pj and _pj.get("available", True):
            _record_phase("phase-J tajik (Sprint-35)", "ok")
        else:
            _record_phase("phase-J tajik (Sprint-35)", "skipped",
                          (_pj or {}).get("reason", "no output"))
    except Exception as exc:  # noqa: BLE001
        print(f"[locked_facts] phase-J tajik (Sprint-35) failed: {exc}")
        _record_phase("phase-J tajik (Sprint-35)", "failed", str(exc))

    # Sprint-34 / Phase I — KP Advanced (I2 CIL + I5 Marriage)
    kp_phase_i_str = ""
    try:
        from vedic.kp.kp_phase_i import (compute_kp_phase_i,  # type: ignore
                                           format_kp_phase_i_summary)
        _kpi = compute_kp_phase_i(kundli)
        kp_phase_i_str = format_kp_phase_i_summary(_kpi)
    except Exception as exc:  # noqa: BLE001
        print(f"[locked_facts] kp phase-I (Sprint-34) failed: {exc}")

    # Sprint-33 / Phase H — Transits & Eclipses (H2/H3/H6/H7/H8 expansion)
    phase_h_str = ""
    try:
        from vedic.transits.phase_h import (compute_phase_h_transits,  # type: ignore
                                              format_phase_h_summary)
        _ph = compute_phase_h_transits(kundli, birth)
        phase_h_str = format_phase_h_summary(_ph)
        if _ph and _ph.get("available", True):
            _record_phase("phase-H transits (Sprint-33)", "ok")
        else:
            _record_phase("phase-H transits (Sprint-33)", "skipped",
                          (_ph or {}).get("reason", "no output"))
    except Exception as exc:  # noqa: BLE001
        print(f"[locked_facts] phase-H transits (Sprint-33) failed: {exc}")
        _record_phase("phase-H transits (Sprint-33)", "failed", str(exc))

    # Sprint-32 / Phase F — Per-Varga Full Depth (F3 + F4-expand + F5)
    varga_phase_f_str = ""
    try:
        from vedic.varga.varga_phase_f import (compute_varga_phase_f,  # type: ignore
                                                format_varga_phase_f_summary)
        _cd = (kundli.get("currentDasha") or kundli.get("current_dasha") or {})
        _md = _cd.get("maha") or _cd.get("md") or ""
        _ad = _cd.get("antar") or _cd.get("ad") or ""
        _ll_f = lagna_lon
        if not isinstance(_ll_f, (int, float)):
            _ll_f = (kundli.get("ascendantDeg")
                     or kundli.get("ascendant_deg")
                     or kundli.get("ascendantLongitude"))
        _vf = compute_varga_phase_f(kundli.get("planets") or [],
                                    _ll_f, _md, _ad)
        varga_phase_f_str = format_varga_phase_f_summary(_vf)
    except Exception as exc:  # noqa: BLE001
        print(f"[locked_facts] phase-F varga depth (Sprint-32) failed: {exc}")

    # Sprint-31 / Phase E — Tier-5 Dasha gap-fill (7 systems)
    phase_e_dashas_str = ""
    try:
        from vedic.dashas.dasha_phase_e import (compute_all_phase_e_dashas,  # type: ignore
                                                  format_phase_e_summary)
        # Sprint-26 Fix-K: defensive guard — birth may be None when the
        # caller passed kundli without a paired birth dict.
        _be = birth or {}
        _ke = dict(kundli)
        _ke["dob"] = _ke.get("dob") or _be.get("dob") or _be.get("date")
        _pe = compute_all_phase_e_dashas(_ke)
        phase_e_dashas_str = format_phase_e_summary(_pe)
    except Exception as exc:  # noqa: BLE001
        print(f"[locked_facts] phase-E dashas (Sprint-31) failed: {exc}")

    # Sprint-30 / Phase C — Missing yogas (Indra + Shoola Nabhasa)
    missing_yogas_str = ""
    try:
        from vedic.yogas.missing_yogas import (detect_missing_yogas,  # type: ignore
                                                format_missing_yogas_summary)
        _my = detect_missing_yogas(kundli.get("planets") or [], _lg_idx_cy)
        missing_yogas_str = format_missing_yogas_summary(_my)
    except Exception as exc:  # noqa: BLE001
        print(f"[locked_facts] missing yogas (Sprint-30) failed: {exc}")

    # Sprint-15 — Per-varga yoga / dosha detection
    varga_yogas_str = ""
    try:
        from varga_yogas import (detect_all_varga_yogas,  # type: ignore
                                 format_varga_yogas_summary)
        _lg_vy = kundli.get("ascendant") or kundli.get("lagna")
        _lg_sign_vy = (_lg_vy.get("sign") if isinstance(_lg_vy, dict) else _lg_vy)
        _vy = detect_all_varga_yogas(
            kundli.get("planets") or [], lagna_lon, _lg_sign_vy
        )
        varga_yogas_str = format_varga_yogas_summary(_vy) if _vy else ""
    except Exception as exc:  # noqa: BLE001
        print(f"[locked_facts] varga yogas (Sprint-15) failed: {exc}")

    # Sprint-14 — Sthira Dasha + Niryana Shoola Dasha (extra Jaimini sign-dashas)
    sthira_str = ""
    niryana_str = ""
    try:
        from extra_jaimini_dashas import (compute_sthira_dasha,  # type: ignore
                                          compute_niryana_shoola,
                                          format_sthira_summary,
                                          format_niryana_summary)
        _lg_xj = kundli.get("ascendant") or kundli.get("lagna")
        _lg_sign_xj = (_lg_xj.get("sign") if isinstance(_lg_xj, dict) else _lg_xj)
        _dob_xj = birth if birth else None
        _sth = compute_sthira_dasha(_lg_sign_xj, _dob_xj)
        _nir = compute_niryana_shoola(_lg_sign_xj, _dob_xj)
        sthira_str  = format_sthira_summary(_sth)  if _sth else ""
        niryana_str = format_niryana_summary(_nir) if _nir else ""
    except Exception as exc:  # noqa: BLE001
        print(f"[locked_facts] extra Jaimini dashas (Sprint-14) failed: {exc}")

    # Sprint-13 — Argala / Virodhargala (Jaimini intervention)
    argala_str = ""
    try:
        from argala import compute_argala, format_argala_summary  # type: ignore
        _lg_arg = kundli.get("ascendant") or kundli.get("lagna")
        _lg_sign_arg = (_lg_arg.get("sign") if isinstance(_lg_arg, dict) else _lg_arg)
        _arg = compute_argala(kundli.get("planets") or [], _lg_sign_arg)
        _argala_topic = (kundli.get("_topic") or "general").lower()
        argala_str = format_argala_summary(_arg, topic=_argala_topic) if _arg else ""
    except Exception as exc:  # noqa: BLE001
        print(f"[locked_facts] argala (Sprint-13) failed: {exc}")

    # Sprint-7 — Jaimini Arudha Padas (A1-A12) + Upapada Lagna (UL)
    jm_str = ""
    try:
        from jaimini import (compute_arudha_padas, compute_upapada,  # type: ignore
                             format_jaimini_summary)
        lagna_sign = kundli.get("ascendant")
        if isinstance(lagna_sign, dict):
            lagna_sign = lagna_sign.get("sign") or lagna_sign.get("name")
        ar = compute_arudha_padas(kundli.get("planets") or [], lagna_sign)
        ul = compute_upapada(ar, kundli.get("planets") or []) if ar else {}
        jm_str = format_jaimini_summary(ar, ul) if ar else ""
    except Exception as exc:  # noqa: BLE001
        print(f"[locked_facts] jaimini failed: {exc}")

    # Sprint-4 — Pratyantar dasha (sub-period under current AD)
    pd_str = ""
    try:
        from pratyantar import compute_pratyantar, format_pratyantar_summary  # type: ignore
        pd = compute_pratyantar(kundli.get("currentDasha") or {})
        pd_str = format_pratyantar_summary(pd) if pd else ""
    except Exception as exc:  # noqa: BLE001
        print(f"[locked_facts] pratyantar failed: {exc}")

    # Sprint-6 — KP Cuspal Sub-Lord cross-check (best-effort — needs lat/lon/tz)
    kp_str = ""
    try:
        from reply_cosmo.engine_locked_to_llm.kp_locked_facts import compute_kp_summary, format_kp_summary  # type: ignore
        kp_sum = compute_kp_summary(birth, kundli)
        kp_str = format_kp_summary(kp_sum) if kp_sum else ""
    except Exception as exc:  # noqa: BLE001
        print(f"[locked_facts] kp cross-check failed: {exc}")

    # Sprint-5 — Remedies (deterministic, classical) — built BEFORE transits
    # so it can use verdicts/dosh/topic that are already available.
    rem_str = ""
    try:
        from remedies import select_remedies, format_remedies_summary  # type: ignore
        active_doshas = []
        if isinstance(dosh, dict):
            for d in dosh.get("dosh_list", []):
                if d.get("status") in ("Active", "Mild"):
                    active_doshas.append(d.get("name") or "")
        # sade-sati flag from intel if engines added it
        if intel.get("sade_sati_active"):
            active_doshas.append("Sade-Sati")
        topic = (kundli.get("_topic") or "").lower()  # may be set by caller
        # verdicts is {planet: {verdict, reason, score}} — unwrap to {planet: "WEAK"|...}
        verdict_strs = {p: (v.get("verdict") if isinstance(v, dict) else v)
                        for p, v in (verdicts or {}).items()}
        rem = select_remedies(verdict_strs, kundli.get("currentDasha") or {},
                              active_doshas, intel, topic,
                              planet_scores=verdicts)
        rem_str = format_remedies_summary(rem)
    except Exception as exc:  # noqa: BLE001
        print(f"[locked_facts] remedies failed: {exc}")

    # Sprint-3 — Transits (Saturn / Jupiter / Rahu vs natal)
    tr_str = ""
    try:
        from transits import compute_transits, format_transit_summary  # type: ignore
        from datetime import datetime
        SIGN_NAMES_TR = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo",
                         "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"]
        moon_sign_str = kundli.get("moonSign") or kundli.get("moon_sign")
        moon_sign_idx = SIGN_NAMES_TR.index(moon_sign_str) if moon_sign_str in SIGN_NAMES_TR else None
        lagna_for_tr = _lagna_sign_idx(kundli, intel)
        # DOB extraction (best-effort) — supports multiple shapes
        dob_dt = None
        if isinstance(birth, dict):
            dob_str = birth.get("date") or birth.get("dob") or birth.get("birthDate")
            if isinstance(dob_str, str) and len(dob_str) >= 10:
                try:
                    dob_dt = datetime.strptime(dob_str[:10], "%Y-%m-%d")
                except Exception:
                    dob_dt = None
            # Sprint-8: also accept {day, month, year, hour, minute} shape
            if dob_dt is None and all(k in birth for k in ("day", "month", "year")):
                try:
                    dob_dt = datetime(
                        int(birth["year"]), int(birth["month"]), int(birth["day"]),
                        int(birth.get("hour") or 0), int(birth.get("minute") or 0)
                    )
                except Exception:
                    dob_dt = None
        if lagna_for_tr is not None:
            tr = compute_transits(lagna_for_tr, moon_sign_idx, dob=dob_dt)
            tr_str = format_transit_summary(tr) if tr else ""
    except Exception as exc:  # noqa: BLE001
        print(f"[locked_facts] transits failed: {exc}")

    # Sprint-51 — Pre-computed timing windows (engine-only, no AI guess)
    # These are the AUTHORITATIVE timing answers for any "kab hoga" question.
    # AI is NEVER allowed to invent dates — it must mirror these verbatim.
    #
    # Phase 2.8.53 (May 2 2026) — VIVAH-7 wiring:
    # Marriage row now sourced from event_timing.marriage.assess_marriage()
    # which runs the KP-first 7-step pipeline (compute_timing_window) and
    # returns rich verdict/band/primary_window/backup_window/confluence_strength
    # /key_trigger/risk_flag/top_3_windows/step0_tendency. The other 6 topics
    # still use the legacy single-line timing_engine (unchanged contract).
    # Falls back to legacy marriage_timing on any error so the block never
    # collapses.
    timing_str = ""
    try:
        from vedic.timing.timing_engine import (  # type: ignore
            child_timing, career_timing, promotion_timing,
            wealth_timing, foreign_timing, property_timing,
        )

        # ── Marriage: VIVAH-7 path ─────────────────────────────────────
        marriage_line = None
        try:
            from event_timing.marriage import assess_marriage  # type: ignore
            kp_dict: dict = {}
            try:
                from openai_helper import _adapt_birth_for_kp  # lazy
                from kp_engine import get_or_compute_kp  # type: ignore (Phase 2.8.58)
                kp_birth = _adapt_birth_for_kp(birth) if isinstance(birth, dict) else None
                # Phase 2.8.58: prefer cached kundli["kp"] over fresh Swiss Ephemeris
                # recompute (Phase 2.8.57 bakes it at kundli compute time and the
                # /api/kundli cache-hit path lazy-repairs older rows).
                kp_dict = get_or_compute_kp(kundli, kp_birth) or {}
            except Exception as _kpexc:  # noqa: BLE001
                print(f"[locked_facts] vivah7 kp calc failed (non-fatal): {_kpexc}")
            v = assess_marriage(kundli, intel, kp_dict, birth) or {}
            verdict = v.get("verdict") or "—"
            band = v.get("band") or "—"
            primary = v.get("primary_window") or "—"
            backup = v.get("backup_window")
            key_trigger = v.get("key_trigger")
            confluence = v.get("confluence_strength")
            risk = v.get("risk_flag")
            tendency = (v.get("step0_tendency") or {}).get("verdict")
            top3 = v.get("top_3_windows") or []
            extras = []
            if confluence:
                extras.append(f"confluence: {confluence}")
            if key_trigger:
                extras.append(f"trigger: {key_trigger}")
            if tendency:
                extras.append(f"tendency: {tendency}")
            if risk:
                extras.append(f"risk: {risk}")
            extras_str = f" [{', '.join(extras)}]" if extras else ""
            backup_str = (
                f" | backup: {backup}"
                if backup and backup != primary else ""
            )
            marriage_line = (
                f"   • Marriage   window: {primary}{backup_str}  "
                f"verdict: {verdict}/{band}{extras_str}"
            )
            # Append top_3_windows trace (compact, max 3)
            # Phase 2.8.53 — "trace:" prefix per architect note: explicitly
            # tags these as VIVAH-7 internal scoring trace so the LLM does
            # not confuse them with parallel timing rows for other topics.
            if isinstance(top3, list) and top3:
                _trace_lines = []
                for i, w in enumerate(top3[:3], 1):
                    if not isinstance(w, dict):
                        continue
                    ws = w.get("window") or "—"
                    sc = w.get("score")
                    sc_str = f" (score: {sc:.1f})" if isinstance(sc, (int, float)) else ""
                    _trace_lines.append(f"     trace {i}: {ws}{sc_str}")
                if _trace_lines:
                    marriage_line += "\n" + "\n".join(_trace_lines)
        except Exception as _exc:  # noqa: BLE001
            print(f"[locked_facts] vivah7 marriage failed, fallback to legacy: {_exc}")
            try:
                from vedic.timing.timing_engine import marriage_timing  # type: ignore
                r = marriage_timing(kundli)
                if r and r.get("available"):
                    marriage_line = (
                        f"   • Marriage   window: {r['window']}  "
                        f"[confidence: {r['confidence']}, lords: {','.join(r['house_lords'])}]"
                    )
                else:
                    marriage_line = "   • Marriage   window: — (insufficient dasha lookahead)"
            except Exception as _exc2:  # noqa: BLE001
                print(f"[locked_facts] legacy marriage fallback also failed: {_exc2}")
                marriage_line = "   • Marriage   window: — (engine unavailable)"

        # ── Other 6 topics: legacy timing_engine (unchanged) ──────────
        _ks = {
            "Child":     child_timing(kundli),
            "Career":    career_timing(kundli),
            "Promotion": promotion_timing(kundli),
            "Wealth":    wealth_timing(kundli),
            "Foreign":   foreign_timing(kundli),
            "Property":  property_timing(kundli),
        }

        # ── Health: HEALTH-TIMING-V1 path (mirror of VIVAH-7) ─────────
        # Computes the 9-step health-risk timing engine and emits a
        # verdict + current-window + top-3 risk-window line. Stashes
        # full result on a thread-local so the deterministic
        # `inject_health_engine_verdict()` post-injector can enforce
        # verbatim citation downstream. Falls back silently if the
        # engine raises so the timing block never collapses.
        health_line = None
        try:
            from event_timing.health.health_engine_v1 import (  # type: ignore
                compute_health_window,
            )
            kp_for_health: dict = {}
            try:
                kp_for_health = (kundli.get("kp")
                                  if isinstance(kundli, dict) else {}) or {}
            except Exception:
                kp_for_health = {}
            h = compute_health_window(kundli, intel, kp_for_health, birth) or {}
            verdict = h.get("verdict") or "—"
            band = h.get("band") or "—"
            tier = h.get("recommendation_tier") or "—"
            cw = h.get("current_window") or {}
            cw_str = ""
            if isinstance(cw, dict) and cw.get("md"):
                cw_str = (f" | now: {cw.get('md')}-{cw.get('ad')}-"
                           f"{cw.get('pd')}/{cw.get('severity','?')}")
            risk_str = ""
            if h.get("risk_flags"):
                risk_str = f" | risk: {','.join(h['risk_flags'][:3])}"
            health_line = (
                f"   • Health     verdict: {verdict}/{band}  "
                f"tier: {tier}{cw_str}{risk_str}"
            )
            top3_h = h.get("next_3_windows") or []
            if isinstance(top3_h, list) and top3_h:
                _trace_h = []
                for i, w in enumerate(top3_h[:3], 1):
                    if not isinstance(w, dict):
                        continue
                    ws = w.get("window") or "—"
                    sc = w.get("score")
                    sev = w.get("severity") or "—"
                    sc_str = (f" (score: {sc:.1f}, sev: {sev})"
                              if isinstance(sc, (int, float))
                              else f" ({sev})")
                    _trace_h.append(f"     trace {i}: {ws}{sc_str}")
                if _trace_h:
                    health_line += "\n" + "\n".join(_trace_h)
            try:
                _record_phase("phase-D health-timing-v1", "ok")
            except Exception:
                pass
        except Exception as _h_exc:  # noqa: BLE001
            print(f"[locked_facts] health-timing-v1 failed: {_h_exc}")
            health_line = (
                "   • Health     verdict: — (engine unavailable)"
            )
            try:
                _record_phase("phase-D health-timing-v1", "failed",
                                str(_h_exc))
            except Exception:
                pass

        # ── Finance: FINANCE-TIMING-V1 path (mirror of health v1) ────
        # Computes the 9-step finance/wealth timing engine and emits
        # a verdict + current-window + top-3 stress-window line.
        # Stashes full result on a thread-local so the finance remedy
        # block (money topic) and any future post-injector can read it.
        # Falls back silently if the engine raises.
        finance_line = None
        try:
            from event_timing.finance.finance_engine_v1 import (  # type: ignore
                compute_finance_window,
            )
            kp_for_finance: dict = {}
            try:
                kp_for_finance = (kundli.get("kp")
                                   if isinstance(kundli, dict) else {}) or {}
            except Exception:
                kp_for_finance = {}
            f = compute_finance_window(kundli, intel, kp_for_finance, birth) or {}
            f_verdict = f.get("verdict") or "—"
            f_band = f.get("band") or "—"
            f_tier = f.get("recommendation_tier") or "—"
            f_cw = f.get("current_window") or {}
            f_cw_str = ""
            if isinstance(f_cw, dict) and f_cw.get("md"):
                f_cw_str = (f" | now: {f_cw.get('md')}-{f_cw.get('ad')}-"
                             f"{f_cw.get('pd')}/{f_cw.get('severity','?')}")
            f_risk_str = ""
            if f.get("risk_flags"):
                f_risk_str = f" | risk: {','.join(f['risk_flags'][:3])}"
            finance_line = (
                f"   • Finance    verdict: {f_verdict}/{f_band}  "
                f"tier: {f_tier}{f_cw_str}{f_risk_str}"
            )
            top3_f = f.get("next_3_windows") or []
            if isinstance(top3_f, list) and top3_f:
                _trace_f = []
                for i, w in enumerate(top3_f[:3], 1):
                    if not isinstance(w, dict):
                        continue
                    ws = w.get("window") or "—"
                    sc = w.get("score")
                    sev = w.get("severity") or "—"
                    sc_str = (f" (score: {sc:.1f}, sev: {sev})"
                              if isinstance(sc, (int, float))
                              else f" ({sev})")
                    _trace_f.append(f"     trace {i}: {ws}{sc_str}")
                if _trace_f:
                    finance_line += "\n" + "\n".join(_trace_f)
            try:
                _record_phase("phase-D finance-timing-v1", "ok")
            except Exception:
                pass
        except Exception as _f_exc:  # noqa: BLE001
            print(f"[locked_facts] finance-timing-v1 failed: {_f_exc}")
            finance_line = (
                "   • Finance    verdict: — (engine unavailable)"
            )
            try:
                _record_phase("phase-D finance-timing-v1", "failed",
                                str(_f_exc))
            except Exception:
                pass

        # ── Travel: TRAVEL-TIMING-V1 path (mirror of finance v1) ─────
        # Computes the 9-step travel/foreign-travel timing engine and
        # emits a verdict + current-window + top-3 travel-window line.
        # Stashes full result on a thread-local for the travel remedy
        # block (travel topic, falls back to career). Falls back
        # silently if the engine raises.
        travel_line = None
        try:
            from event_timing.travel.travel_engine_v1 import (  # type: ignore
                compute_travel_window,
            )
            kp_for_travel: dict = {}
            try:
                kp_for_travel = (kundli.get("kp")
                                  if isinstance(kundli, dict) else {}) or {}
            except Exception:
                kp_for_travel = {}
            t = compute_travel_window(kundli, intel, kp_for_travel, birth) or {}
            t_verdict = t.get("verdict") or "—"
            t_band = t.get("band") or "—"
            t_tier = t.get("recommendation_tier") or "—"
            t_foreign = "✓" if t.get("foreign_promised") else "✗"
            t_cw = t.get("current_window") or {}
            t_cw_str = ""
            if isinstance(t_cw, dict) and t_cw.get("md"):
                t_cw_str = (f" | now: {t_cw.get('md')}-{t_cw.get('ad')}-"
                             f"{t_cw.get('pd')}/{t_cw.get('severity','?')}"
                             f"/{t_cw.get('kind','?')}")
            t_risk_str = ""
            if t.get("risk_flags"):
                t_risk_str = f" | risk: {','.join(t['risk_flags'][:3])}"
            travel_line = (
                f"   • Travel     verdict: {t_verdict}/{t_band}  "
                f"foreign: {t_foreign}  tier: {t_tier}{t_cw_str}{t_risk_str}"
            )
            top3_t = t.get("next_3_windows") or []
            if isinstance(top3_t, list) and top3_t:
                _trace_t = []
                for i, w in enumerate(top3_t[:3], 1):
                    if not isinstance(w, dict):
                        continue
                    ws = w.get("window") or "—"
                    sc = w.get("score")
                    sev = w.get("severity") or "—"
                    knd = w.get("kind") or "—"
                    sc_str = (f" (score: {sc:.1f}, sev: {sev}, kind: {knd})"
                              if isinstance(sc, (int, float))
                              else f" ({sev}, {knd})")
                    # Phase 2.5.11.15 — double-transit annotation per
                    # K.N.Rao classical rule (compulsory for ALL timing
                    # narration). Verdict tells LLM whether sky actually
                    # supports the dasha-favorable window or not.
                    dt = w.get("double_transit") or {}
                    dt_str = ""
                    if dt.get("verdict"):
                        anc = dt.get("anchors") or []
                        anc_short = "; ".join(anc[:2]) if anc else "—"
                        dt_str = (f" | DOUBLE-TRANSIT: {dt['verdict']} "
                                   f"(score {dt.get('score', 0)}; {anc_short})")
                    _trace_t.append(f"     trace {i}: {ws}{sc_str}{dt_str}")
                if _trace_t:
                    travel_line += "\n" + "\n".join(_trace_t)
            # Past windows (Phase 2.5.11.14) — historical favorable
            # foreign/travel windows. MUST be framed as "opportunity
            # existed" NEVER "user actually traveled" (UCML confirms
            # real events). Engine attaches PAST_WINDOW_IS_OPPORTUNITY_
            # NOT_EVENT directive whenever past_windows non-empty.
            past_t = t.get("past_windows") or []
            if isinstance(past_t, list) and past_t:
                _past_t = ["     past_windows (FAVORABLE OPPORTUNITY ONLY — NOT confirmed travel; UCML must verify):"]
                for i, w in enumerate(past_t[:3], 1):
                    if not isinstance(w, dict):
                        continue
                    ws = w.get("window") or "—"
                    sc = w.get("score")
                    knd = w.get("kind") or "—"
                    md_ad_pd = (f"{w.get('md','?')}-{w.get('ad','?')}-"
                                 f"{w.get('pd','?')}")
                    sc_str = (f" (score: {sc:.1f}, kind: {knd}, dasha: {md_ad_pd})"
                              if isinstance(sc, (int, float))
                              else f" (kind: {knd}, dasha: {md_ad_pd})")
                    # Phase 2.5.11.15 — past-window double-transit @ midpoint
                    # date (NOT today). STRONG = sky actually supported the
                    # window historically; PARTIAL/ABSENT = dasha-only
                    # candidate (likely no real event).
                    dt = w.get("double_transit") or {}
                    dt_str = ""
                    if dt.get("verdict"):
                        anc = dt.get("anchors") or []
                        anc_short = "; ".join(anc[:2]) if anc else "—"
                        dt_str = (f" | DOUBLE-TRANSIT: {dt['verdict']} "
                                   f"(score {dt.get('score', 0)}; {anc_short})")
                    _past_t.append(f"       past {i}: {ws}{sc_str}{dt_str}")
                travel_line += "\n" + "\n".join(_past_t)
                # Phase 2.5.11.15 — universal hard reminder for LLM:
                # K.N.Rao Double Transit is the compulsory fructification
                # filter for ANY timing claim (past/present/future).
                travel_line += ("\n     RULE: Double-Transit STRONG = "
                                 "sky-confirmed fructification window. "
                                 "PARTIAL = opportunity-only. ABSENT = "
                                 "dasha-favorable but unlikely to fructify.")
            try:
                _record_phase("phase-D travel-timing-v1", "ok")
            except Exception:
                pass
        except Exception as _t_exc:  # noqa: BLE001
            print(f"[locked_facts] travel-timing-v1 failed: {_t_exc}")
            travel_line = (
                "   • Travel     verdict: — (engine unavailable)"
            )
            try:
                _record_phase("phase-D travel-timing-v1", "failed",
                                str(_t_exc))
            except Exception:
                pass

        # ── Baby (Childbirth): BABY-TIMING-V1 path (mirror of travel v1) ─
        # Computes the 9-step baby/conception/progeny timing engine and
        # emits a verdict + current-window + top-3 baby-window line.
        # Stashes full result on a thread-local for the baby remedy
        # block (baby topic, falls back to health). Falls back silently
        # if the engine raises.
        baby_line = None
        try:
            from event_timing.baby.baby_engine_v1 import (  # type: ignore
                compute_baby_window,
            )
            kp_for_baby: dict = {}
            try:
                kp_for_baby = (kundli.get("kp")
                                if isinstance(kundli, dict) else {}) or {}
            except Exception:
                kp_for_baby = {}
            b = compute_baby_window(kundli, intel, kp_for_baby, birth) or {}
            b_verdict = b.get("verdict") or "—"
            b_band = b.get("band") or "—"
            b_tier = b.get("recommendation_tier") or "—"
            b_promised = "✓" if b.get("child_promised") else "✗"
            b_cw = b.get("current_window") or {}
            b_cw_str = ""
            if isinstance(b_cw, dict) and b_cw.get("md"):
                b_cw_str = (f" | now: {b_cw.get('md')}-{b_cw.get('ad')}-"
                             f"{b_cw.get('pd')}/{b_cw.get('severity','?')}"
                             f"/{b_cw.get('kind','?')}")
            b_risk_str = ""
            if b.get("risk_flags"):
                b_risk_str = f" | risk: {','.join(b['risk_flags'][:3])}"
            baby_line = (
                f"   • Baby       verdict: {b_verdict}/{b_band}  "
                f"child_promised: {b_promised}  tier: {b_tier}{b_cw_str}{b_risk_str}"
            )
            # D7 picture trace — surfaces 1L / 5L / 5H occupants so the
            # AI can mirror the engine's progeny-chart reading verbatim.
            b_d7 = b.get("d7_picture") or {}
            if isinstance(b_d7, dict) and b_d7.get("available"):
                _fl  = b_d7.get("first_lord") or {}
                _fih = b_d7.get("fifth_lord") or {}
                _occ5 = b_d7.get("fifth_house_occupants") or []
                _asp5 = b_d7.get("aspects_to_fifth_house") or []
                baby_line += (
                    f"\n     D7 lagna: {b_d7.get('d7_lagna')}"
                    f" | 1L: {_fl.get('planet')}@H{_fl.get('house_in_d7')}"
                    f"/{_fl.get('dignity')}/{_fl.get('sign')}"
                    f" | 5L: {_fih.get('planet')}@H{_fih.get('house_in_d7')}"
                    f"/{_fih.get('dignity')}/{_fih.get('sign')}"
                    f" | 5H_occ: {_occ5 or '—'}"
                    f" | 5H_asp: {_asp5 or '—'}"
                )
            elif isinstance(b_d7, dict):
                baby_line += "\n     D7 picture: unavailable (D1-dignity proxy)"
            top3_b = b.get("next_3_windows") or []
            if isinstance(top3_b, list) and top3_b:
                _trace_b = []
                for i, w in enumerate(top3_b[:3], 1):
                    if not isinstance(w, dict):
                        continue
                    ws = w.get("window") or "—"
                    sc = w.get("score")
                    sev = w.get("severity") or "—"
                    knd = w.get("kind") or "—"
                    sc_str = (f" (score: {sc:.1f}, sev: {sev}, kind: {knd})"
                              if isinstance(sc, (int, float))
                              else f" ({sev}, {knd})")
                    _trace_b.append(f"     trace {i}: {ws}{sc_str}")
                if _trace_b:
                    baby_line += "\n" + "\n".join(_trace_b)
            # ── Phase 2.5.8 — SAV bindus + Jupiter PUTRA-karaka BAV ──
            # Surfaces both aggregate SAV (santan band — overall
            # support from all 7 grahas) and Jupiter's own BAV on
            # 5H+11H (specific PUTRA-KARAKA strength).
            b_av = b.get("ashtakavarga") or {}
            if isinstance(b_av, dict) and (b_av.get("sav_5") is not None
                                              or b_av.get("jup_bav_5")
                                                 is not None):
                _line = (
                    f"     SAV: 5H={b_av.get('sav_5','—')}"
                    f" / 11H={b_av.get('sav_11','—')}"
                    f" → santan_band: {b_av.get('santan_band','—')}"
                )
                if b_av.get("jup_bav_5") is not None:
                    _line += (
                        f" | Jupiter BAV: 5H={b_av.get('jup_bav_5')}"
                        f"/7, 11H={b_av.get('jup_bav_11')}/7"
                        f" → PUTRA-KARAKA: "
                        f"{b_av.get('jupiter_putra_strength','—')}"
                    )
                baby_line += "\n" + _line
            # ── Phase 2.5.4 — KP 2-5-11 significator filter ──────────
            # Surfaces which planets PROMISE child via KP NL∧SBL rule
            # vs which are blocked or pure-negation. Lets the AI mirror
            # the engine's classical KP verdict verbatim.
            b_kp = b.get("kp_significator_filter") or {}
            if isinstance(b_kp, dict) and b_kp.get("available"):
                _passed  = b_kp.get("passed")  or []
                _blocked = b_kp.get("blocked") or []
                _unknown = b_kp.get("unknown") or []
                _line = (f"     KP 2-5-11: passed={_passed or '—'}"
                          f" | blocked={_blocked or '—'}")
                if _unknown:
                    _line += f" | unknown={_unknown}"
                baby_line += "\n" + _line
            # ── Phase 2.5.5 — active-window marking ──────────────────
            # The simple classical "kab promoter dasha aa rahi hai"
            # surfaced cleanly: next AD/PD ruled by FINAL-GATE-PASSED
            # promoter planets, with priority PEAK > STRONG > TRIGGER.
            b_next = b.get("next_child_window")
            if isinstance(b_next, dict) and b_next.get("window"):
                _lords = b_next.get("active_lords_in_window") or []
                _lords_str = (",".join(_lords) if _lords else "—")
                baby_line += (
                    f"\n     next promoter window: "
                    f"{b_next.get('window')} "
                    f"[{b_next.get('active_priority','?')}] "
                    f"lords={_lords_str}"
                )
            elif b.get("child_active_windows") == []:
                baby_line += ("\n     next promoter window: "
                                "none in horizon")
            # ── Phase 2.5.7 — Jupiter+Saturn Double Transit ──────────
            # Classical K.N. Rao Double Transit Theory verdict +
            # exact transit positions (sign, deg, nakshatra, house).
            b_tr = b.get("transits") or {}
            if isinstance(b_tr, dict) and not b_tr.get("note"):
                _pos = b_tr.get("positions") or {}
                _jp = _pos.get("Jupiter") or {}
                _sp = _pos.get("Saturn")  or {}
                if _jp and _sp:
                    baby_line += (
                        f"\n     Transit (Jup+Sat only): "
                        f"Jupiter {_jp.get('sign_name')} "
                        f"{_jp.get('deg_str')} "
                        f"{_jp.get('nak_name')} pada{_jp.get('pada')}"
                        f" → H{_jp.get('house_from_lagna')}"
                        f"{' (R)' if _jp.get('retrograde') else ''}"
                        f" | Saturn {_sp.get('sign_name')} "
                        f"{_sp.get('deg_str')} "
                        f"{_sp.get('nak_name')} pada{_sp.get('pada')}"
                        f" → H{_sp.get('house_from_lagna')}"
                        f"{' (R)' if _sp.get('retrograde') else ''}"
                    )
                _dt = b_tr.get("double_transit") or {}
                if isinstance(_dt, dict):
                    if _dt.get("active"):
                        baby_line += (
                            f"\n     ★ DOUBLE TRANSIT ACTIVE: "
                            f"Jupiter→{_dt.get('jupiter_anchor')}; "
                            f"Saturn→{_dt.get('saturn_anchor')} "
                            f"(5H={_dt.get('h5_sign')}, "
                            f"5L={_dt.get('h5_lord')}"
                            f"@{_dt.get('h5_lord_sign')}) "
                            f"— classical conception window"
                        )
                    elif _dt.get("partial"):
                        baby_line += (
                            f"\n     Double Transit: partial "
                            f"({_dt.get('partial')}) — not yet"
                        )
                    else:
                        baby_line += (
                            "\n     Double Transit: not active "
                            "(neither Jup nor Sat on 5H/5L)"
                        )
            try:
                _record_phase("phase-D baby-timing-v1", "ok")
            except Exception:
                pass
        except Exception as _b_exc:  # noqa: BLE001
            print(f"[locked_facts] baby-timing-v1 failed: {_b_exc}")
            baby_line = (
                "   • Baby       verdict: — (engine unavailable)"
            )
            try:
                _record_phase("phase-D baby-timing-v1", "failed",
                                str(_b_exc))
            except Exception:
                pass

        # ── REMEDIES sub-blocks (Phase 2.2, May 6 2026) ─────────────
        # Standalone hybrid Remedy Engine v1.0 (3-tier: practical →
        # ayurvedic → vedic). Emits parallel "▸ <TOPIC> REMEDIES"
        # sections for HEALTH, MARRIAGE, CAREER. Each is rendered by
        # `remedy.render_for_locked_facts(...)` which guarantees:
        #   - PRACTICAL row first, VEDIC row last (anti-superstition)
        #   - KPI + cost-ballpark + caveats on every paid item
        #   - Conflict warnings (gemstone enemy pairs, overload)
        #   - Universal disclaimer + tier-note ALWAYS injected
        #   - Doctor referral hint (health only) when severity ≥ consult
        # Rule M (anti-hallucination remedy quoting) auto-picks these up
        # so LLM cites mantras/donations/gems verbatim.
        # Falls back silently per topic — a single failure doesn't
        # collapse the timing block or the other topics' remedies.
        health_remedies_block   = ""
        marriage_remedies_block = ""
        career_remedies_block   = ""
        finance_remedies_block  = ""
        travel_remedies_block   = ""
        baby_remedies_block     = ""
        try:
            from remedy import (  # type: ignore
                get_remedies as _get_remedies,
                render_for_locked_facts as _render_remedies,
            )

            # ── HEALTH ─────────────────────────────────────────────
            try:
                from event_timing.health.health_engine_v1 import (  # type: ignore
                    get_last_health_result,
                )
                _hres = get_last_health_result() or {}
                _hrem = _hres.get("remedies") or {}
                if _hrem:
                    health_remedies_block = _render_remedies(_hrem) or ""
            except Exception as _h_rem_exc:  # noqa: BLE001
                print(f"[locked_facts] health remedies block failed: {_h_rem_exc}")

            # ── MARRIAGE ───────────────────────────────────────────
            # Sourced from `assess_marriage().top_marriage_planets`
            # which is shaped [{name, score, ...}, ...].
            try:
                _m_planets = []
                if 'v' in locals() and isinstance(v, dict):
                    _m_planets = v.get("top_marriage_planets") or []
                # Severity heuristic from VIVAH-7 band (None → safe default).
                # Architect-fix May 6 2026: VIVAH-7 emits STRONG|MEDIUM|WEAK
                # — old 'FAVOUR' branch was dead code. Now MEDIUM correctly
                # maps to supportive (not collapsing to watchful).
                _m_band = (v.get("band") if 'v' in locals() and isinstance(v, dict)
                             else None) or ""
                _m_band_u = str(_m_band).upper()
                _m_sev = ("celebratory" if "STRONG" in _m_band_u
                          else "supportive" if ("MEDIUM" in _m_band_u
                                                or "FAVOUR" in _m_band_u)
                          else "watchful")
                if _m_planets:
                    _mres = _get_remedies(
                        topic    = "marriage",
                        planets  = _m_planets,
                        areas    = ["communication", "harmony", "trust"],
                        severity = _m_sev,
                    )
                    marriage_remedies_block = _render_remedies(_mres) or ""
            except Exception as _m_rem_exc:  # noqa: BLE001
                print(f"[locked_facts] marriage remedies block failed: {_m_rem_exc}")

            # ── CAREER ─────────────────────────────────────────────
            # Sourced from legacy `career_timing(kundli).house_lords`
            # which is shaped [str, ...]; promoted to {name, score=None}.
            try:
                _c_res = (_ks.get("Career") if isinstance(_ks, dict) else {}) or {}
                _c_lords = _c_res.get("house_lords") or []
                _c_planets = [{"name": x} for x in _c_lords if isinstance(x, str)]
                if _c_planets:
                    _cres = _get_remedies(
                        topic    = "career",
                        planets  = _c_planets,
                        areas    = ["skill_depth", "networking", "stability"],
                        severity = "watchful",
                    )
                    career_remedies_block = _render_remedies(_cres) or ""
            except Exception as _c_rem_exc:  # noqa: BLE001
                print(f"[locked_facts] career remedies block failed: {_c_rem_exc}")

            # ── FINANCE / MONEY (Phase 2.3, May 7 2026) ────────────
            # Sourced from finance engine's thread-local result.
            # Engine internally delegates to remedy.get_remedies(
            # topic="money") with severity already mapped to
            # watchful/supportive/celebratory/consult, so we just
            # render the pre-built remedies dict.
            try:
                from event_timing.finance.finance_engine_v1 import (  # type: ignore
                    get_last_finance_result,
                )
                _fres = get_last_finance_result() or {}
                _frem = _fres.get("remedies") or {}
                if _frem:
                    finance_remedies_block = _render_remedies(_frem) or ""
            except Exception as _f_rem_exc:  # noqa: BLE001
                print(f"[locked_facts] finance remedies block failed: {_f_rem_exc}")

            # ── TRAVEL (Phase 2.4, May 7 2026) ─────────────────────
            # Sourced from travel engine's thread-local result.
            # Engine internally delegates to remedy.get_remedies(
            # topic="travel") with graceful fallback to career.
            try:
                from event_timing.travel.travel_engine_v1 import (  # type: ignore
                    get_last_travel_result,
                )
                _tres = get_last_travel_result() or {}
                _trem = _tres.get("remedies") or {}
                if _trem:
                    travel_remedies_block = _render_remedies(_trem) or ""
            except Exception as _t_rem_exc:  # noqa: BLE001
                print(f"[locked_facts] travel remedies block failed: {_t_rem_exc}")

            # ── BABY (Phase 2.5, May 7 2026) ───────────────────────
            # Sourced from baby engine's thread-local result.
            # Engine internally delegates to remedy.get_remedies(
            # topic="baby") with graceful fallback to health.
            try:
                from event_timing.baby.baby_engine_v1 import (  # type: ignore
                    get_last_baby_result,
                )
                _bres = get_last_baby_result() or {}
                _brem = _bres.get("remedies") or {}
                if _brem:
                    baby_remedies_block = _render_remedies(_brem) or ""
            except Exception as _b_rem_exc:  # noqa: BLE001
                print(f"[locked_facts] baby remedies block failed: {_b_rem_exc}")

        except Exception as _rem_exc:  # noqa: BLE001
            print(f"[locked_facts] remedy engine import failed: {_rem_exc}")

        _t_lines = ["▸ TIMING ENGINE (Sprint-51 — engine-only, AI MUST mirror verbatim, NEVER invent dates):"]
        if marriage_line:
            _t_lines.append(marriage_line)
        if health_line:
            _t_lines.append(health_line)
        if finance_line:
            _t_lines.append(finance_line)
        if travel_line:
            _t_lines.append(travel_line)
        if baby_line:
            _t_lines.append(baby_line)
        for topic, r in _ks.items():
            if r and r.get("available"):
                _t_lines.append(
                    f"   • {topic:10s} window: {r['window']}  "
                    f"[confidence: {r['confidence']}, lords: {','.join(r['house_lords'])}]"
                )
            else:
                _t_lines.append(f"   • {topic:10s} window: — (insufficient dasha lookahead)")
        _t_lines.append(
            "   ⚐ HARD RULE: For ANY 'kab/when' question on these topics, "
            "use ONLY the window above. NO date may appear in the answer "
            "that is not in this block."
        )
        if health_remedies_block:
            _t_lines.append(health_remedies_block)
        if marriage_remedies_block:
            _t_lines.append(marriage_remedies_block)
        if career_remedies_block:
            _t_lines.append(career_remedies_block)
        if finance_remedies_block:
            _t_lines.append(finance_remedies_block)
        if travel_remedies_block:
            _t_lines.append(travel_remedies_block)
        if baby_remedies_block:
            _t_lines.append(baby_remedies_block)
        timing_str = "\n".join(_t_lines)
    except Exception as exc:  # noqa: BLE001
        print(f"[locked_facts] timing_engine failed: {exc}")

    # Sprint-8 — Jaimini Chara Dasha (sign-based mahadasha)
    cd_str = ""
    try:
        from chara_dasha import (compute_chara_dasha,  # type: ignore
                                 format_chara_dasha_summary)
        _lg_name = None
        if intel.get("ascendant"):
            _lg_name = intel["ascendant"]
        elif kundli.get("ascendant"):
            asc = kundli["ascendant"]
            _lg_name = asc.get("sign") if isinstance(asc, dict) else asc
        cd = compute_chara_dasha(
            kundli.get("planets") or [], _lg_name, dob_dt
        )
        cd_str = format_chara_dasha_summary(cd) if cd else ""
    except Exception as exc:  # noqa: BLE001
        print(f"[locked_facts] chara_dasha failed: {exc}")

    # Assemble
    sections = [
        "═════════ LOCKED FACTS — MIRROR EXACTLY, NEVER INVENT ═════════",
        _format_basics(kundli, intel),
        _format_yoga_block(intel.get("yogas") or []),
        _format_dosh_block(dosh) if dosh else f"▸ MANGAL-DOSH: {intel.get('mangal_dosh','(unavailable)')}",
        _format_strength_block(verdicts, intel.get("dignities") or [], strength_facts),
        av_str,
        bb_str,
        bbd_str,
        bd_str,
        asp_str,
        kk_str,
        div_str,
        extra_div_str,
        adv_div_str,
        subtle_div_str,
        deep_div_str,
        classical_yogas_str,
        extra_yogas_str,
        deep_doshas_str,
        extra_dashas_str,
        varga_deep_str,
        ashtaka_deep_str,
        transit_deep_str,
        kp_deep_str,
        rashi_drishti_str,
        special_lagnas_str,
        age_context_str,
        shadbala_full_str,
        missing_yogas_str,
        phase_e_dashas_str,
        varga_phase_f_str,
        phase_h_str,
        kp_phase_i_str,
        phase_j_str,
        avashtas_str,
        lagnas_l_str,
        sahams_m_str,
        phase_n_str,
        lal_kitab_str,
        phase_p_str,
        phase_q_str,
        phase_r_str,
        phase_s_str,
        numerology_deep_str,
        numerology_practical_str,
        astro_vastu_str,
        medical_str,
        financial_str,
        remedies_deep_str,
        astrocarto_str,
        modern_reframe_str,
        varga_yogas_str,
        argala_str,
        sthira_str,
        niryana_str,
        tr_str,
        timing_str,
        _format_dasha_block(kundli),
        pd_str,
        jm_str,
        cd_str,
        _format_house_lords(intel),
        kp_str,
        rem_str,
        "════════════════════════════════════════════════════════════════",
    ]
    # Drop empty sections (e.g. no house lords)
    return "\n\n".join(s for s in sections if s and s.strip())
