"""
Tier 7 — Wealth & Money (Life Mastery Report)
Wraps existing `vedic.financial.financial_engine.run_financial_engine` (Sprint 48)
and adds a numerology money-temperament layer + current-dasha wealth window.

Inputs : kundli dict (with `planets`, `ascendant`, `currentDasha`).
Outputs: dict with 11 wealth blocks ready for Tier 7 renderer.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

log = logging.getLogger(__name__)


# ─── Driver-number money temperament (numerology layer) ────────────────
# Each driver is ruled by a planet; that planet's *money personality* drives
# the native's instinctive money-mindset, savings vs spending tendency,
# best income channel, and lucky money days.
DRIVER_MONEY = {
    1: {  # Sun — leadership wealth
        "planet": "Sun", "mindset": "Authority-driven — earns through leadership, govt, status",
        "tendency": "Spends on prestige (status purchases, premium brands)",
        "savings_style": "Moderate — needs visible assets (gold, real-estate)",
        "income_channel": "Leadership roles, government, top-tier brand presence",
        "lucky_days": ["Sunday"], "lucky_money_numbers": [1, 4],
    },
    2: {  # Moon — emotional wealth
        "planet": "Moon", "mindset": "Emotion-driven — earns through people, hospitality, food, public-mood",
        "tendency": "Spends on family + emotional comforts (home, gifts)",
        "savings_style": "Inconsistent — high in good moods, leaks in low moods",
        "income_channel": "Public-facing service, nurturing roles, water/dairy/hospitality",
        "lucky_days": ["Monday"], "lucky_money_numbers": [2, 7],
    },
    3: {  # Jupiter — wisdom wealth
        "planet": "Jupiter", "mindset": "Knowledge-driven — earns through teaching, advising, content, expansion",
        "tendency": "Spends on learning, travel, charity, religious causes",
        "savings_style": "Strong — Jupiter naturally accumulates",
        "income_channel": "Teaching, consulting, publishing, religious/spiritual services",
        "lucky_days": ["Thursday"], "lucky_money_numbers": [3, 9],
    },
    4: {  # Rahu — unconventional wealth
        "planet": "Rahu", "mindset": "Innovation-driven — earns through tech, foreign markets, sudden breakthroughs",
        "tendency": "Big swings — sudden gains AND sudden losses",
        "savings_style": "Volatile — needs strict automation (SIP, fixed transfers)",
        "income_channel": "Tech, foreign income, crypto, viral/digital, unconventional fields",
        "lucky_days": ["Saturday", "Sunday"], "lucky_money_numbers": [4, 8],
    },
    5: {  # Mercury — intelligence wealth
        "planet": "Mercury", "mindset": "Speed-driven — earns through trading, communication, multiple streams",
        "tendency": "Diversified spending — small frequent purchases",
        "savings_style": "Excellent if disciplined — Mercury natively likes accumulation via numbers",
        "income_channel": "Trading, brokerage, communication, multi-stream entrepreneurship",
        "lucky_days": ["Wednesday"], "lucky_money_numbers": [5, 6],
    },
    6: {  # Venus — luxury wealth
        "planet": "Venus", "mindset": "Beauty-driven — earns through luxury, art, beauty, relationships",
        "tendency": "High spend on aesthetics, lifestyle, partner, comforts",
        "savings_style": "Weak by default — Venus prefers enjoyment over accumulation",
        "income_channel": "Luxury, fashion, beauty, art, entertainment, hospitality",
        "lucky_days": ["Friday"], "lucky_money_numbers": [6, 5],
    },
    7: {  # Ketu — detached wealth
        "planet": "Ketu", "mindset": "Purpose-driven — earns through research, occult, healing, niche mastery",
        "tendency": "Low material craving — money flows only when deeply engaged",
        "savings_style": "Naturally minimalist — saves by not desiring much",
        "income_channel": "Research, occult, healing, spiritual services, niche expertise",
        "lucky_days": ["Tuesday"], "lucky_money_numbers": [7, 2],
    },
    8: {  # Saturn — slow-built wealth
        "planet": "Saturn", "mindset": "Discipline-driven — earns through long-term effort, structure, real assets",
        "tendency": "Conservative — fears spending, sometimes to a fault",
        "savings_style": "Excellent — Saturn is THE wealth-builder over decades",
        "income_channel": "Long-term industries, real-estate, mining, infrastructure, govt service",
        "lucky_days": ["Saturday"], "lucky_money_numbers": [8, 1],
    },
    9: {  # Mars — energetic wealth
        "planet": "Mars", "mindset": "Action-driven — earns through courage, risk, real-estate, defence, sports",
        "tendency": "Impulsive — quick decisions, sometimes regretted",
        "savings_style": "Moderate — needs systems to override impulse",
        "income_channel": "Real-estate, defence, surgery, sports, engineering, action-business",
        "lucky_days": ["Tuesday"], "lucky_money_numbers": [9, 3],
    },
}

# Driver-conductor wealth synergy lookup (instinct vs execution alignment)
def _money_synergy(driver: int, conductor: int) -> str:
    if driver == conductor:
        return "FOCUSED — instinct and execution aligned; one clear money channel"
    # Friction (enemies) is checked FIRST so that classical hostile pairs like
    # 2↔9 (Moon↔Mars), 3↔5, 4↔5, 6↔7 etc. are not silently masked by the
    # broader "same-family" heuristic. (Earlier we had 1↔8 in BOTH sets which
    # made the FRICTION branch unreachable for that pair — fixed.)
    enemies = {(2,9),(9,2),(3,5),(5,3),(4,5),(5,4),(6,7),(7,6),(2,5),(5,2)}
    if (driver, conductor) in enemies:
        return "FRICTION — instinct pulls one way, execution another; needs explicit money-systems"
    same_family = {(1,4),(4,1),(1,8),(8,1),(2,7),(7,2),(3,9),(9,3),(5,6),(6,5)}
    if (driver, conductor) in same_family or (conductor, driver) in same_family:
        return "SYNERGY — instinct (driver) + execution (conductor) reinforce each other"
    return "NEUTRAL — flexibility across multiple money channels, but requires intentional focus"


# ─── Planet → wealth-house relationship (for current-dasha window) ─────
WEALTH_HOUSES = {2, 5, 9, 11}  # Dhana houses

PLANET_WEALTH_NATURE = {
    "Jupiter": "STRONG-WEALTH — natural Dhana karaka; expansion of resources",
    "Venus":   "STRONG-WEALTH — Lakshmi karaka; luxury, comfort, partner-money",
    "Mercury": "GOOD-WEALTH — trade, commerce, multi-stream income",
    "Moon":    "GOOD-WEALTH — public/emotional money flow; hospitality, daily-cash",
    "Sun":     "STATUS-WEALTH — leadership-pay, govt, prestige income (not always large)",
    "Mars":    "EFFORT-WEALTH — earned through risk, action, real-estate, courage",
    "Saturn":  "SLOW-WEALTH — long-term accumulation; delays followed by stability",
    "Rahu":    "VOLATILE-WEALTH — sudden gains; tech, foreign, unconventional channels",
    "Ketu":    "DETACHED-WEALTH — minimal but enough; research/occult/spiritual income",
}


def _adapt_kundli_for_finance(kundli: Dict[str, Any]) -> Dict[str, Any]:
    """`run_financial_engine` reads `kundli['vimshottari']['current']`, but
    `kundli_engine.calculate_kundli` exposes the same data under `currentDasha`
    (`{maha, antar, startDate, endDate}`). Add the shim non-destructively."""
    if kundli.get("vimshottari"):
        return kundli  # already shaped
    cd = kundli.get("currentDasha") or {}
    if not cd:
        return kundli
    shim = dict(kundli)
    shim["vimshottari"] = {"current": {
        "mahadasha_lord": cd.get("maha"),
        "antardasha_lord": cd.get("antar"),
        "md_start": cd.get("startDate"),
        "md_end":   cd.get("endDate"),
    }}
    return shim


def _current_dasha_window(kundli: Dict[str, Any]) -> Dict[str, Any]:
    """Verdict on current MD lord's relationship to wealth houses."""
    cd = kundli.get("currentDasha") or {}
    md = cd.get("maha")
    if not md:
        return {"available": False}
    planets = kundli.get("planets") or []
    md_planet = next((p for p in planets if p.get("name") == md), None)
    in_wealth_house = bool(md_planet and md_planet.get("house") in WEALTH_HOUSES)
    nature = PLANET_WEALTH_NATURE.get(md, "MIXED — depends on chart-specific placement")
    if in_wealth_house:
        verdict = "STRONG WEALTH WINDOW — current MD lord sits in a Dhana house"
    elif md in ("Jupiter", "Venus"):
        verdict = "FAVOURABLE — natural wealth karaka active; income should expand"
    elif md in ("Saturn", "Rahu"):
        verdict = "BUILDING — slow / volatile but foundation-laying years"
    elif md in ("Ketu",):
        verdict = "MINIMALIST — focus on purpose over accumulation right now"
    else:
        verdict = "MIXED — wealth proceeds at chart-baseline pace"
    return {
        "available": True,
        "md_lord": md, "antar_lord": cd.get("antar"),
        "md_house": md_planet.get("house") if md_planet else None,
        "md_in_wealth_house": in_wealth_house,
        "nature": nature, "verdict": verdict,
        "md_start": cd.get("startDate"), "md_end": cd.get("endDate"),
    }


# ─────────────────────────────────────────────────────────────────────
# Main aggregator
# ─────────────────────────────────────────────────────────────────────
def compute_wealth_bundle(kundli: Dict[str, Any], dob: str,
                          driver: int, conductor: int) -> Dict[str, Any]:
    """Compute Tier 7 wealth bundle for a single kundli."""
    if not kundli or not kundli.get("planets"):
        return {"available": False, "reason": "no kundli"}

    # ── 1. Run financial engine ───────────────────────────────────
    fin: Dict[str, Any] = {"available": False}
    try:
        from vedic.financial.financial_engine import run_financial_engine
        fin = run_financial_engine(_adapt_kundli_for_finance(kundli)) or {"available": False}
    except Exception as e:
        log.warning("run_financial_engine failed: %s", e)

    if not fin.get("available", True):  # engine sets available implicitly via shape
        # Some versions return the dict without 'available' — treat presence of f1 as ok
        fin_ok = bool(fin.get("f1_wealth_houses"))
    else:
        fin_ok = bool(fin.get("f1_wealth_houses"))
    if not fin_ok:
        return {"available": False, "reason": "financial_engine returned no data"}

    # ── 2. Numerology money-temperament layer ─────────────────────
    self_money = DRIVER_MONEY.get(driver, {})
    cond_money = DRIVER_MONEY.get(conductor, {})
    money_numerology = {
        "self_driver": driver, "self_conductor": conductor,
        "self_planet": self_money.get("planet", "—"),
        "conductor_planet": cond_money.get("planet", "—"),
        "mindset": self_money.get("mindset", ""),
        "spending_tendency": self_money.get("tendency", ""),
        "savings_style": self_money.get("savings_style", ""),
        "ideal_income_channel": self_money.get("income_channel", ""),
        "lucky_money_days": self_money.get("lucky_days", []),
        "lucky_money_numbers": self_money.get("lucky_money_numbers", []),
        "synergy_verdict": _money_synergy(driver, conductor),
        "execution_style": cond_money.get("savings_style", ""),
    }

    # ── 3. Current-dasha wealth window ────────────────────────────
    dasha_window = _current_dasha_window(kundli)

    # ── 4. Synthesis verdict (combines yoga count + scorecard avg) ─
    yoga_count = len(fin.get("f2_dhana_yogas") or [])
    daridra_active = bool((fin.get("f3_daridra") or {}).get("yogas")) and \
                     not (fin.get("f3_daridra") or {}).get("cancelled")
    scorecard = fin.get("f13_wealth_scorecard") or []
    avg_score = (sum(s.get("score", 0) for s in scorecard) / len(scorecard)) if scorecard else 0.0
    if daridra_active and yoga_count == 0:
        synthesis = "CHALLENGING — active Daridra without Dhana support; remedies + discipline essential"
    elif yoga_count >= 3 and avg_score >= 1.5:
        synthesis = "EXCEPTIONAL — multiple Dhana yogas active + strong wealth-house support"
    elif yoga_count >= 2:
        synthesis = "STRONG — clear wealth signatures; capitalise via aligned career/risk profile"
    elif avg_score >= 1.0:
        synthesis = "MODERATE — wealth houses support steady accumulation; no major windfalls"
    else:
        synthesis = "BUILD-MODE — chart asks for disciplined long-term wealth-building (Saturn approach)"

    return {
        "available": True,
        "wealth_dna": {
            "driver_money": self_money,
            "yoga_count": yoga_count,
            "daridra_cancelled": (fin.get("f3_daridra") or {}).get("cancelled"),
            "scorecard_avg": round(avg_score, 2),
            "risk_profile": fin.get("f11_risk_profile"),
        },
        "dhana_yogas":     fin.get("f2_dhana_yogas") or [],
        "wealth_houses":   fin.get("f1_wealth_houses") or [],
        "daridra_audit":   fin.get("f3_daridra") or {},
        "income_source":   fin.get("f4_income_source") or {},
        "debt_risk":       fin.get("f5_debt_risk") or {},
        "real_estate":     fin.get("f6_real_estate") or {},
        "foreign_income":  fin.get("f7_foreign_income") or {},
        "speculation":     fin.get("f8_speculation") or {},
        "career_income":   fin.get("f9_career_income") or [],
        "wealth_strategies": fin.get("f10_top_strategies") or [],
        "risk_profile":    fin.get("f11_risk_profile") or "",
        "roadmap_15yr":    fin.get("f12_roadmap_15yr") or [],
        "scorecard":       scorecard,
        "money_numerology": money_numerology,
        "current_dasha_window": dasha_window,
        "synthesis_verdict": synthesis,
    }


if __name__ == "__main__":  # pragma: no cover — smoke test
    from kundli_engine import calculate_kundli
    k = calculate_kundli({
        "name": "Rahul Sharma", "day": 15, "month": 5, "year": 1990,
        "hour": 10, "minute": 30, "ampm": "AM",
        "lat": 28.6139, "lon": 77.2090, "tz": 5.5, "place": "New Delhi",
    })
    b = compute_wealth_bundle(k, "1990-05-15", driver=6, conductor=3)
    print("AVAILABLE:", b.get("available"))
    if b.get("available"):
        print("WEALTH_DNA:", b["wealth_dna"])
        print("DHANA_YOGAS count:", len(b["dhana_yogas"]))
        for y in b["dhana_yogas"][:5]:
            print("  •", y.get("tier"), y.get("name"))
        print("DARIDRA cancelled:", b["daridra_audit"].get("cancelled"),
              "yogas=", len(b["daridra_audit"].get("yogas") or []))
        print("INCOME_SOURCE:", b["income_source"])
        print("DEBT_RISK:", b["debt_risk"].get("risk_tier"))
        print("STRATEGIES:", b["wealth_strategies"])
        print("RISK_PROFILE:", b["risk_profile"])
        print("MONEY_NUMEROLOGY mindset:", b["money_numerology"]["mindset"])
        print("MONEY_NUMEROLOGY synergy:", b["money_numerology"]["synergy_verdict"])
        print("DASHA_WINDOW:", b["current_dasha_window"])
        print("SCORECARD:")
        for s in b["scorecard"]:
            print(f"  H{s['house']}: score={s['score']} verdict={s['verdict']}")
        print("SYNTHESIS:", b["synthesis_verdict"])
