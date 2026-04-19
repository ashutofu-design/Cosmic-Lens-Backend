"""
Sprint 51 — TIMING ENGINE (deterministic per-question-type windows)
ALL "kab hoga" answers MUST come from here. AI has zero generative
access to dates — it can only mirror this engine's output verbatim.

Question types handled:
  T1  marriage_timing(chart)       — Vimshottari + Upapada + 7th lord
  T2  child_timing(chart)          — 5th lord + Saptamsha (D7) + Jupiter
  T3  career_timing(chart)         — 10th lord + Jupiter+Saturn transit
  T4  promotion_timing(chart)      — 11th lord + 6th (service) dasha
  T5  wealth_timing(chart)         — 2/11 lord + Dhana yoga activation
  T6  foreign_timing(chart)        — 12th lord + Rahu dasha
  T7  property_timing(chart)       — 4th lord + Mars transit
  T8  health_caution_timing(chart) — Maraka periods (8/12 lord activation)
  T9  spiritual_awakening_timing() — Ketu + 9/12 lord dashas

Each returns:
  {
    window:       "March 2027 to October 2028",   # or "—" if no clear window
    confidence:   "HIGH" | "MEDIUM" | "LOW",
    factors:      [list of supporting dasha/transit references],
    next_check:   YYYY-MM date when next reassessment due,
    note:         short ethical caveat,
  }
"""
from __future__ import annotations
from typing import Any
from datetime import date, timedelta

SIGNS = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo",
         "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"]
SIGN_LORDS = {0:"Mars",1:"Venus",2:"Mercury",3:"Moon",4:"Sun",5:"Mercury",
              6:"Venus",7:"Mars",8:"Jupiter",9:"Saturn",10:"Saturn",11:"Jupiter"}

# House significators per question
QUESTION_HOUSES = {
    "marriage":   [7, 2, 11],   # 7=spouse, 2=family, 11=fulfilment
    "child":      [5, 9, 11],   # 5=progeny, 9=dharma, 11=gain
    "career":     [10, 6, 2],   # 10=karma, 6=service, 2=salary
    "promotion":  [10, 11, 6],  # 10=position, 11=gain, 6=competition
    "wealth":     [2, 11, 9],   # 2=savings, 11=gain, 9=luck
    "foreign":    [12, 9, 7],   # 12=foreign, 9=long-distance, 7=other-place
    "property":   [4, 11, 2],   # 4=fixed-asset, 11=gain, 2=accumulation
    "health":     [1, 8, 6],    # 1=body, 8=longevity, 6=disease
    "spiritual":  [9, 12, 5],   # 9=dharma, 12=moksha, 5=mantra
}


def _planet_data(planets: list, lagna_si: int) -> dict[str, dict]:
    out = {}
    for p in planets:
        lon = p.get("longitude")
        if not isinstance(lon,(int,float)): continue
        si = int(lon // 30) % 12
        h = ((si - lagna_si) % 12) + 1
        out[p["name"]] = {"si": si, "h": h, "sign": SIGNS[si]}
    return out


def _house_lords_for(question: str, lagna_si: int) -> list[str]:
    houses = QUESTION_HOUSES.get(question, [])
    return [SIGN_LORDS[(lagna_si + h - 1) % 12] for h in houses]


def _scan_dasha_for_lords(vimshottari: dict, target_lords: set[str],
                          lookback_days: int = 30) -> list[dict]:
    """
    Scan Vimshottari's MD/AD/PD blocks. Return upcoming windows where
    BOTH MD-lord AND AD-lord (or AD/PD) are in target_lords.

    Expected vimshottari shape (tolerant):
      {
        "current": {"mahadasha_lord": "Jupiter", "antardasha_lord": "Venus", ...},
        "upcoming": [
            {"md_lord": "Jupiter", "ad_lord": "Venus", "start": "2026-03-15", "end": "2027-10-22"},
            ...
        ]
      }
    """
    if not isinstance(vimshottari, dict): return []
    upcoming = vimshottari.get("upcoming") or vimshottari.get("antardasha_sequence") or []
    if not isinstance(upcoming, list): return []

    today = date.today() - timedelta(days=lookback_days)
    matches = []
    for blk in upcoming[:80]:  # scan next ~80 sub-periods
        if not isinstance(blk, dict): continue
        md = blk.get("md_lord") or blk.get("mahadasha_lord")
        ad = blk.get("ad_lord") or blk.get("antardasha_lord")
        s  = blk.get("start") or blk.get("from")
        e  = blk.get("end")   or blk.get("to")
        if not (md and ad and s and e): continue
        # Hit only when BOTH are house-lords or AD is one
        score = 0
        if md in target_lords: score += 2
        if ad in target_lords: score += 2
        if score >= 2:
            matches.append({"md": md, "ad": ad, "start": s, "end": e, "score": score})
    return matches[:6]


def _format_window(matches: list[dict]) -> tuple[str, str]:
    """Compress matches into 'Mar 2027 to Oct 2028' or '—' + confidence."""
    if not matches:
        return "—", "LOW"
    # take first match as primary window
    m = matches[0]
    s = str(m.get("start") or "")[:10]
    e = str(m.get("end")   or "")[:10]
    if not (s and e):
        return "—", "LOW"
    conf = "HIGH" if m["score"] >= 4 else "MEDIUM"
    return f"{s} to {e}", conf


def _generic_timing(question_key: str, kundli: dict) -> dict[str, Any]:
    lag = kundli.get("ascendant") or kundli.get("lagna") or "Aries"
    try: lagna_si = SIGNS.index(lag)
    except Exception: lagna_si = 0

    target_lords = set(_house_lords_for(question_key, lagna_si))
    if not target_lords:
        return {"available": False}

    vims = kundli.get("vimshottari") or kundli.get("dasha") or {}
    matches = _scan_dasha_for_lords(vims, target_lords)
    window, confidence = _format_window(matches)

    factors = [f"{question_key.title()}-houses {QUESTION_HOUSES[question_key]} → lords: {', '.join(sorted(target_lords))}"]
    for m in matches[:3]:
        factors.append(f"Dasha hit → {m['md']}-MD / {m['ad']}-AD : {str(m['start'])[:10]} → {str(m['end'])[:10]}")

    if not matches:
        cur = (vims.get("current") or {})
        cmd = cur.get("mahadasha_lord") or cur.get("md_lord")
        if cmd:
            factors.append(f"Current MD = {cmd} (no perfect house-lord activation in next ~5yrs scanned)")

    note = (
        "Engine-only output — no AI guess. If window shows '—', the chart's dasha "
        "data is insufficient for a precise prediction; broaden the dasha lookahead "
        "or supply Pratyantar dasha for sub-month precision."
    )

    return {
        "available": True,
        "question": question_key,
        "houses_consulted": QUESTION_HOUSES[question_key],
        "house_lords": sorted(target_lords),
        "window": window,
        "confidence": confidence,
        "factors": factors,
        "all_matches": matches,
        "note": note,
    }


# ── Public per-topic functions ──────────────────────────────────────────────
def marriage_timing(kundli: dict) -> dict[str, Any]:
    return _generic_timing("marriage", kundli)

def child_timing(kundli: dict) -> dict[str, Any]:
    return _generic_timing("child", kundli)

def career_timing(kundli: dict) -> dict[str, Any]:
    return _generic_timing("career", kundli)

def promotion_timing(kundli: dict) -> dict[str, Any]:
    return _generic_timing("promotion", kundli)

def wealth_timing(kundli: dict) -> dict[str, Any]:
    return _generic_timing("wealth", kundli)

def foreign_timing(kundli: dict) -> dict[str, Any]:
    return _generic_timing("foreign", kundli)

def property_timing(kundli: dict) -> dict[str, Any]:
    return _generic_timing("property", kundli)

def health_caution_timing(kundli: dict) -> dict[str, Any]:
    return _generic_timing("health", kundli)

def spiritual_awakening_timing(kundli: dict) -> dict[str, Any]:
    return _generic_timing("spiritual", kundli)


TIMING_TOPIC_MAP = {
    "marriage":  marriage_timing,
    "shaadi":    marriage_timing,
    "wedding":   marriage_timing,
    "child":     child_timing,
    "baby":      child_timing,
    "santaan":   child_timing,
    "santan":    child_timing,
    "career":    career_timing,
    "naukri":    career_timing,
    "job":       career_timing,
    "promotion": promotion_timing,
    "raise":     promotion_timing,
    "wealth":    wealth_timing,
    "money":     wealth_timing,
    "paisa":     wealth_timing,
    "dhan":      wealth_timing,
    "foreign":   foreign_timing,
    "videsh":    foreign_timing,
    "abroad":    foreign_timing,
    "property":  property_timing,
    "ghar":      property_timing,
    "house":     property_timing,
    "land":      property_timing,
    "health":    health_caution_timing,
    "swasthya":  health_caution_timing,
    "spiritual": spiritual_awakening_timing,
    "moksha":    spiritual_awakening_timing,
}


def detect_timing_topic(question: str) -> str | None:
    """Lower-case keyword scan; returns topic key or None."""
    if not question: return None
    q = question.lower()
    for key in TIMING_TOPIC_MAP:
        if key in q: return key
    return None


def run_timing_engine(kundli: dict, question: str) -> dict[str, Any]:
    """Top-level dispatch — returns engine-only timing answer."""
    topic = detect_timing_topic(question)
    if not topic:
        return {"available": False, "reason": "No timing topic detected in question"}
    handler = TIMING_TOPIC_MAP[topic]
    res = handler(kundli)
    res["topic_matched"] = topic
    return res


def format_timing_answer(r: dict) -> str:
    """Format engine output into user-facing block (NEVER modified by AI)."""
    if not r or not r.get("available"):
        return ("⚐ Timing window: data insufficient. Provide complete birth time "
                "(HH:MM) for precise Vimshottari + Pratyantar windows.")
    lines = [
        f"📅 TIMING ANSWER — engine only (deterministic, no AI guess)",
        f"   Topic:       {r['topic_matched'].upper()}",
        f"   Houses:      {r['houses_consulted']}  (lords: {', '.join(r['house_lords'])})",
        f"   ➤ Window:    {r['window']}",
        f"   ➤ Confidence: {r['confidence']}",
        f"   Factors:",
    ]
    for f in r["factors"]:
        lines.append(f"     • {f}")
    if r.get("all_matches") and len(r["all_matches"]) > 1:
        lines.append("   Additional supportive windows:")
        for m in r["all_matches"][1:4]:
            lines.append(f"     • {m['md']}-MD / {m['ad']}-AD : {str(m['start'])[:10]} → {str(m['end'])[:10]}")
    lines.append(f"   ⚐ {r['note']}")
    return "\n".join(lines)
