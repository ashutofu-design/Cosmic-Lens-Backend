"""
Six-Month Deep Future Engine
─────────────────────────────
For each of the next 6 months, projects:

  • Active Mahadasha (MD), Antardasha (AD), Pratyantardasha (PD)
  • Each lord's natal house ownership + natal placement
  • Live Saturn / Jupiter / Rahu transit on critical houses for that month
  • Composite score (0-100) for the month
  • Life-area outlook: career, finance, health, relationship, spirituality
  • Key events likely / opportunities / cautions
  • One personalised remedy of the month

Pure deterministic Vedic logic. Reuses pratyantar.py constants.
Fails-soft: returns partial data on error, never raises.
"""
from __future__ import annotations
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

# Vimshottari constants (mirror pratyantar.py to avoid circular import)
_VIMS_ORDER = ["Ketu", "Venus", "Sun", "Moon", "Mars",
               "Rahu", "Jupiter", "Saturn", "Mercury"]
_VIMS_YEARS = {"Ketu": 7, "Venus": 20, "Sun": 6, "Moon": 10, "Mars": 7,
               "Rahu": 18, "Jupiter": 16, "Saturn": 19, "Mercury": 17}
_TOTAL = 120

SIGNS = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo",
         "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"]
SIGN_LORD = {
    "Aries":"Mars","Taurus":"Venus","Gemini":"Mercury","Cancer":"Moon",
    "Leo":"Sun","Virgo":"Mercury","Libra":"Venus","Scorpio":"Mars",
    "Sagittarius":"Jupiter","Capricorn":"Saturn","Aquarius":"Saturn","Pisces":"Jupiter",
}
EXALT = {"Sun":"Aries","Moon":"Taurus","Mars":"Capricorn","Mercury":"Virgo",
         "Jupiter":"Cancer","Venus":"Pisces","Saturn":"Libra"}
DEBIL = {"Sun":"Libra","Moon":"Scorpio","Mars":"Cancer","Mercury":"Pisces",
         "Jupiter":"Capricorn","Venus":"Virgo","Saturn":"Aries"}
OWN   = {"Sun":["Leo"],"Moon":["Cancer"],"Mars":["Aries","Scorpio"],
         "Mercury":["Gemini","Virgo"],"Jupiter":["Sagittarius","Pisces"],
         "Venus":["Taurus","Libra"],"Saturn":["Capricorn","Aquarius"]}

BENEFIC = {"Jupiter", "Venus", "Mercury", "Moon"}
MALEFIC = {"Saturn", "Mars", "Rahu", "Ketu"}

# House ownership: planet → list of (sign positions where planet rules)
def _planet_owns_houses(planet: str, asc_idx: int) -> List[int]:
    """Return houses that this planet rules from given ascendant."""
    if planet in ("Rahu", "Ketu"):
        return []  # nodes don't rule houses
    houses: List[int] = []
    for i in range(12):
        sign = SIGNS[(asc_idx + i) % 12]
        if SIGN_LORD.get(sign) == planet:
            houses.append(i + 1)
    return houses


# House meanings (used in life-area mapping)
HOUSE_DOMAIN = {
    1:  {"label": "Self / Body / Vitality",          "areas": ["health"]},
    2:  {"label": "Wealth / Family / Speech",        "areas": ["finance"]},
    3:  {"label": "Courage / Siblings / Skills",     "areas": ["career"]},
    4:  {"label": "Home / Mother / Comforts",        "areas": ["health", "relationship"]},
    5:  {"label": "Children / Creativity / Love",    "areas": ["relationship", "career"]},
    6:  {"label": "Enemies / Disease / Service",     "areas": ["health", "career"]},
    7:  {"label": "Marriage / Partners / Public",    "areas": ["relationship", "career"]},
    8:  {"label": "Transformation / Hidden",         "areas": ["spirituality", "health"]},
    9:  {"label": "Luck / Dharma / Father",          "areas": ["career", "spirituality"]},
    10: {"label": "Career / Status / Authority",     "areas": ["career"]},
    11: {"label": "Gains / Income / Network",        "areas": ["finance", "career"]},
    12: {"label": "Loss / Foreign / Spirituality",   "areas": ["spirituality", "finance"]},
}


def _parse_dt(s: Any) -> Optional[datetime]:
    if not s:
        return None
    if isinstance(s, datetime):
        return s
    s = str(s).strip()
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(s[:len(fmt) if "T" not in fmt else 19], fmt)
        except Exception:
            continue
    return None


# ── PD chain projection ──────────────────────────────────────────────────
def _project_pd_chain(md_lord: str, ad_lord: str,
                      ad_start: datetime, ad_end: datetime,
                      from_dt: datetime, months_needed: int = 6
                      ) -> List[Dict[str, Any]]:
    """
    Build PD chain inside the current AD. If `months_needed` extends past
    `ad_end`, also walk forward into the next AD(s) under the same MD.
    Returns sequence of {md, ad, pd, start, end} dicts.
    """
    out: List[Dict[str, Any]] = []
    horizon = from_dt + timedelta(days=months_needed * 31)

    cur_md, cur_ad = md_lord, ad_lord
    cur_ad_start, cur_ad_end = ad_start, ad_end

    safety = 0
    while cur_ad_start < horizon and safety < 30:
        safety += 1
        if cur_ad not in _VIMS_YEARS:
            break

        ad_seconds = (cur_ad_end - cur_ad_start).total_seconds()
        if ad_seconds <= 0:
            break

        start_idx = _VIMS_ORDER.index(cur_ad)
        cursor = cur_ad_start
        for k in range(9):
            pd_lord = _VIMS_ORDER[(start_idx + k) % 9]
            frac = _VIMS_YEARS[pd_lord] / _TOTAL
            pd_end = cursor + timedelta(seconds=ad_seconds * frac)
            if pd_end > from_dt:  # only keep PDs that overlap our window
                out.append({
                    "md":    cur_md,
                    "ad":    cur_ad,
                    "pd":    pd_lord,
                    "start": cursor,
                    "end":   pd_end,
                })
            cursor = pd_end
            if cursor >= horizon:
                break

        # Advance to next AD under same MD
        next_ad_idx = (_VIMS_ORDER.index(cur_ad) + 1) % 9
        next_ad = _VIMS_ORDER[next_ad_idx]
        # Each AD length under MD = (MD_years * AD_planet_years) / 120 → in years
        # We don't know MD start/end exactly here, so estimate AD length
        # using the SAME MD lord's total years × the new AD's share.
        md_total_years = _VIMS_YEARS.get(cur_md, 16)
        next_ad_years  = (md_total_years * _VIMS_YEARS.get(next_ad, 7)) / _TOTAL
        next_ad_days   = next_ad_years * 365.25
        cur_ad         = next_ad
        cur_ad_start   = cur_ad_end
        cur_ad_end     = cur_ad_end + timedelta(days=next_ad_days)

    return out


# ── Score one month based on MD/AD/PD planet quality ────────────────────
def _planet_quality_score(planet: str, planets_natal: List[dict]) -> int:
    """Quality of a planet from natal chart: -25..+25"""
    p = next((x for x in planets_natal if x.get("name") == planet), None)
    if not p:
        # Rahu/Ketu may be present; fall through neutral
        return 0
    sg = p.get("sign", "")
    h  = p.get("house", 0)
    score = 0
    if planet in EXALT and sg == EXALT[planet]:        score += 15
    elif planet in DEBIL and sg == DEBIL[planet]:      score -= 15
    elif sg in OWN.get(planet, []):                    score += 8
    if h in (1, 4, 5, 7, 9, 10, 11):                   score += 8
    elif h in (6, 8, 12):                              score -= 8
    if planet in BENEFIC:                              score += 4
    elif planet in MALEFIC:                            score -= 2
    if p.get("retrograde"):                            score -= 3
    return max(-25, min(25, score))


def _life_area_impact(planet: str, planets_natal: List[dict],
                      asc_idx: int) -> Dict[str, str]:
    """For a given dasha lord, summarise what life areas it lights up."""
    if not planet:
        return {}
    p = next((x for x in planets_natal if x.get("name") == planet), None)
    owned_houses = _planet_owns_houses(planet, asc_idx)
    sitting_house = p.get("house") if p else None

    # Combine owned + sitting houses → impacted areas
    impacted_houses = list(set(owned_houses + ([sitting_house] if sitting_house else [])))
    area_set: Dict[str, List[str]] = {
        "career": [], "finance": [], "health": [],
        "relationship": [], "spirituality": []
    }
    for h in impacted_houses:
        meta = HOUSE_DOMAIN.get(h)
        if not meta:
            continue
        for area in meta.get("areas", []):
            area_set.setdefault(area, []).append(f"{h}H ({meta['label']})")

    # Strength tag
    quality = _planet_quality_score(planet, planets_natal)
    if quality >= 12:    tag = "STRONG"
    elif quality >= 4:   tag = "FAVORABLE"
    elif quality >= -4:  tag = "MIXED"
    elif quality >= -12: tag = "TENSE"
    else:                tag = "DIFFICULT"

    return {
        "planet":         planet,
        "quality_tag":    tag,
        "quality_score":  quality,
        "owns_houses":    owned_houses,
        "sits_in_house":  sitting_house,
        "impact_by_area": area_set,
    }


def _month_text(md: str, ad: str, pd: str, score: int,
                md_info: dict, ad_info: dict, pd_info: dict,
                month_label: str) -> Dict[str, Any]:
    """Generate human-readable predictions per life area."""
    if score >= 75:    overall = "Highly Favorable"
    elif score >= 60:  overall = "Favorable"
    elif score >= 45:  overall = "Mixed"
    elif score >= 30:  overall = "Challenging"
    else:              overall = "Tough — extra care zone"

    # Per-life-area sentences
    AREA_TXT = {
        "career":       "career & work",
        "finance":      "money & wealth",
        "health":       "health & vitality",
        "relationship": "love & relationships",
        "spirituality": "spiritual / inner growth",
    }

    # Combine impact_by_area across MD/AD/PD
    combined: Dict[str, List[str]] = {k: [] for k in AREA_TXT}
    for src, info in (("MD", md_info), ("AD", ad_info), ("PD", pd_info)):
        for area, hits in (info.get("impact_by_area") or {}).items():
            for h in hits:
                combined[area].append(f"{src} {info.get('planet')} → {h}")

    # Build life-area outlook
    outlook: List[Dict[str, Any]] = []
    for area, label in AREA_TXT.items():
        hits = combined.get(area, [])
        if not hits:
            continue
        # Determine area trend by averaging quality of contributing lords
        contributors_q = []
        for src, info in (("MD", md_info), ("AD", ad_info), ("PD", pd_info)):
            if any(src in h for h in hits):
                contributors_q.append(info.get("quality_score", 0))
        avg_q = sum(contributors_q) / max(len(contributors_q), 1)
        if avg_q >= 8:    trend = "up"
        elif avg_q >= -4: trend = "neutral"
        else:             trend = "down"

        outlook.append({
            "area":    area,
            "label":   label,
            "trend":   trend,
            "hits":    hits[:3],
            "summary": _area_summary(area, trend, md, ad, pd),
        })

    # Opportunities / cautions
    opportunities = []
    cautions = []
    for src, info in (("MD", md_info), ("AD", ad_info), ("PD", pd_info)):
        plnt = info.get("planet")
        q    = info.get("quality_score", 0)
        if q >= 8:
            opportunities.append(
                f"{src} {plnt} strong — "
                f"{('career growth, recognition, deals close fast' if plnt in ('Sun','Jupiter','Mercury') else 'creative & people-energy peaks' if plnt == 'Venus' else 'action, courage, breakthroughs' if plnt == 'Mars' else 'emotional support, family time, networking' if plnt == 'Moon' else 'long-term wins, structures get built' if plnt == 'Saturn' else 'sudden gains / unconventional luck' if plnt == 'Rahu' else 'inner clarity, research wins' if plnt == 'Ketu' else 'overall positive flow')}"
            )
        elif q <= -8:
            cautions.append(
                f"{src} {plnt} weak — "
                f"{('joints / bones / delays, slow paperwork' if plnt == 'Saturn' else 'conflict, accidents, anger, BP — speak softly' if plnt == 'Mars' else 'sudden drama, foreign tangles, scams' if plnt == 'Rahu' else 'detachment phase, unexplained losses, isolation' if plnt == 'Ketu' else 'emotional dips, sleep issues, water-related caution' if plnt == 'Moon' else 'general dasha caution — pace yourself')}"
            )

    if not opportunities:
        opportunities.append("Subtle opportunities — keep showing up, big breaks may not be visible yet.")
    if not cautions:
        cautions.append("No major red flags this month — just maintain routine.")

    # Remedy of month — based on weakest dasha lord
    weakest = min((md_info, ad_info, pd_info),
                  key=lambda x: x.get("quality_score", 0))
    remedy = _remedy_for_planet(weakest.get("planet", ""))

    return {
        "overall":        overall,
        "outlook":        outlook,
        "opportunities":  opportunities[:4],
        "cautions":       cautions[:4],
        "remedy_focus":   {"planet": weakest.get("planet"), "action": remedy},
    }


def _area_summary(area: str, trend: str, md: str, ad: str, pd: str) -> str:
    arrow = "↑" if trend == "up" else "↓" if trend == "down" else "→"
    base = {
        "career": {
            "up":      "Promotion / recognition / new project clearance ke chances strong.",
            "neutral": "Steady work, kuch politics ho sakti hai — patience zaroori.",
            "down":    "Authority figures se thandi rakhein, jaldbaazi se nuksaan possible.",
        },
        "finance": {
            "up":      "Income flow active, naye sources khulne ke chances. Invest soch-samajh ke.",
            "neutral": "Routine income, big jumps abhi nahi. Savings discipline important.",
            "down":    "Outflow zyada ho sakta hai. Loan/large purchase tale.",
        },
        "health": {
            "up":      "Energy strong, recovery fast. Naye fitness routine start kar sakte ho.",
            "neutral": "Maintenance phase. Sleep + diet pe dhyan.",
            "down":    "Joints, BP, ya digestion check karein. Stress management zaroori.",
        },
        "relationship": {
            "up":      "Bonds deepen ho sakte hain. Naye connections, family harmony.",
            "neutral": "Routine equation. Listen more, react less.",
            "down":    "Misunderstandings ka chance. Soft tone, no big arguments.",
        },
        "spirituality": {
            "up":      "Meditation / sadhana mein gehraai milegi. Guru-darshan auspicious.",
            "neutral": "Pravachan/ paath se shanti milegi. Routine puja sufficient.",
            "down":    "Mind chanchal — daily 10 min silence + mantra zaroori.",
        },
    }.get(area, {}).get(trend, "Mixed energy — observe before acting.")
    return f"{arrow} {base}"


def _remedy_for_planet(planet: str) -> str:
    return {
        "Sun":     "Subah Surya ko jal arpan + 'Om Suryaya Namah' 11 baar.",
        "Moon":    "Somvaar shaam white sweet + Shiv-jal abhishek.",
        "Mars":    "Mangalvaar Hanuman Chalisa + red chana donate.",
        "Mercury": "Budhvaar green moong gareeb ko + 'Om Bum Budhaya Namah' 21 baar.",
        "Jupiter": "Guruvaar peela vastra / haldi + Vishnu Sahasranama path.",
        "Venus":   "Shukravaar white flowers Lakshmi ko + sweets gau-mata ko.",
        "Saturn":  "Shanivaar til-tel ka deepak Peepal ke neeche + black urad daan.",
        "Rahu":    "Shanivaar Durga path + sky-blue cloth daan + roz coconut water.",
        "Ketu":    "Mangalvaar Ganpati Atharvashirsha + multi-color blanket donate.",
    }.get(planet, "Daily 'Om Namo Bhagavate Vasudevaya' 21 baar — sarva-graha shanti.")


# ── MAIN — six month engine ──────────────────────────────────────────────
def compute_six_month_future(kundli: Dict[str, Any]) -> Dict[str, Any]:
    """
    Returns: {
      "available": bool,
      "generated_at": iso,
      "current_dasha": {md, ad, pd, ad_start, ad_end},
      "months": [
        {month_label, start, end, md, ad, pd,
         md_info, ad_info, pd_info,
         month_score, ...month_text() output
        }, ... × 6
      ]
    }
    """
    try:
        planets = kundli.get("planets") or []
        asc_sign = kundli.get("ascendant") or "Aries"
        try:
            asc_idx = SIGNS.index(asc_sign)
        except ValueError:
            asc_idx = 0

        cd = kundli.get("currentDasha") or {}
        md_lord = cd.get("maha") or cd.get("mahadasha") or ""
        ad_lord = cd.get("antar") or cd.get("antardasha") or ""
        ad_start = _parse_dt(cd.get("startDate") or cd.get("start"))
        ad_end   = _parse_dt(cd.get("endDate")   or cd.get("end"))

        if not (planets and md_lord and ad_lord):
            return {"available": False, "reason": "Kundli ya currentDasha incomplete."}

        # If AD start/end not provided, assume current month is in middle
        # of a 1-year AD (rough fallback so engine still runs).
        now = datetime.utcnow()
        if not ad_start or not ad_end:
            ad_start = now - timedelta(days=180)
            ad_end   = now + timedelta(days=180)

        # Build PD chain for next 6 months
        chain = _project_pd_chain(md_lord, ad_lord, ad_start, ad_end,
                                  from_dt=now, months_needed=6)

        # Slice into 6 monthly buckets — for each month-anchor (today + n*30d),
        # pick the PD active at that moment. Some months may share the same PD.
        months: List[Dict[str, Any]] = []
        seen: set[str] = set()
        for n in range(6):
            anchor = now + timedelta(days=n * 30)
            month_start = anchor.replace(day=1)
            # Last day of month
            if anchor.month == 12:
                month_end = anchor.replace(year=anchor.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                month_end = anchor.replace(month=anchor.month + 1, day=1) - timedelta(days=1)

            # Find PD active at mid-month
            mid = anchor
            active = next((c for c in chain if c["start"] <= mid < c["end"]), None)
            if not active:
                # Fallback to last PD in chain
                active = chain[-1] if chain else {"md": md_lord, "ad": ad_lord, "pd": ad_lord,
                                                  "start": month_start, "end": month_end}

            md_info = _life_area_impact(active["md"], planets, asc_idx)
            ad_info = _life_area_impact(active["ad"], planets, asc_idx)
            pd_info = _life_area_impact(active["pd"], planets, asc_idx)

            # Composite month score: weighted (PD strongest current driver)
            base = 50
            base += md_info.get("quality_score", 0) * 0.3
            base += ad_info.get("quality_score", 0) * 0.4
            base += pd_info.get("quality_score", 0) * 0.6
            month_score = max(15, min(95, round(base)))

            month_label = anchor.strftime("%b %Y")
            text = _month_text(active["md"], active["ad"], active["pd"],
                               month_score, md_info, ad_info, pd_info,
                               month_label)

            uniq_key = f"{active['md']}-{active['ad']}-{active['pd']}"
            months.append({
                "month_label":  month_label,
                "start":        month_start.strftime("%Y-%m-%d"),
                "end":          month_end.strftime("%Y-%m-%d"),
                "md":           active["md"],
                "ad":           active["ad"],
                "pd":           active["pd"],
                "pd_start":     active["start"].strftime("%Y-%m-%d") if hasattr(active["start"], "strftime") else str(active["start"])[:10],
                "pd_end":       active["end"].strftime("%Y-%m-%d") if hasattr(active["end"], "strftime") else str(active["end"])[:10],
                "is_pd_change": uniq_key not in seen,
                "month_score":  month_score,
                "md_info":      md_info,
                "ad_info":      ad_info,
                "pd_info":      pd_info,
                **text,
            })
            seen.add(uniq_key)

        return {
            "available":     True,
            "generated_at":  now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "current_dasha": {
                "md":       md_lord,
                "ad":       ad_lord,
                "pd":       cd.get("pratyantar") or "",
                "ad_start": ad_start.strftime("%Y-%m-%d"),
                "ad_end":   ad_end.strftime("%Y-%m-%d"),
            },
            "months":        months,
        }
    except Exception as exc:
        return {"available": False, "error": str(exc)}
