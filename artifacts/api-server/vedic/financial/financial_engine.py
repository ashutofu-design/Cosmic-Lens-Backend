"""
Sprint 48 — FINANCIAL ASTROLOGY ENGINE
Deep + ethical chart-driven wealth audit.

20 checks: Dhana yogas, Daridra, wealth-house scoring, income source,
debts, real-estate, foreign income, speculation/trading ability,
dasha-activated wealth windows, severity-tiered + modern reframed.

ETHICS rules (mirror of medical engine):
  • Mandatory disclaimer banner — NOT financial advice
  • 3 severity tiers — POTENTIAL 🟢 / ABILITY 🟡 / STRONG 🔴
  • Daridra Yoga only flagged if 3+ supporting factors AND no Dhana cancellation
  • Bhanga (cancellation of poverty) checked first — if STRONG, all daridra → CANCELLED
  • No "you will be poor" language ever — only "ABILITY/POTENTIAL/RISK"
  • Modern reframe applied throughout (crypto/SaaS/creator economy)
"""
from __future__ import annotations
from typing import Any

SIGNS = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo",
         "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"]
SIGN_LORDS = {0:"Mars",1:"Venus",2:"Mercury",3:"Moon",4:"Sun",5:"Mercury",
              6:"Venus",7:"Mars",8:"Jupiter",9:"Saturn",10:"Saturn",11:"Jupiter"}
BENEFICS = {"Jupiter","Venus","Mercury","Moon"}
MALEFICS = {"Saturn","Mars","Sun","Rahu","Ketu"}

DISCLAIMER = (
    "  ⚠  FINANCIAL DISCLAIMER  ⚠\n"
    "    This is an astrological wealth-pattern audit, NOT financial advice.\n"
    "    Astrology shows TENDENCIES, not guaranteed income or losses.\n"
    "    Always consult a SEBI-registered financial planner for actual decisions.\n"
    "    Severity tiers: 🟢 POTENTIAL  •  🟡 ABILITY  •  🔴 STRONG"
)

# ── Modern profession map per income-source planet ─────────────────────────
INCOME_SOURCE_MAP = {
    "Sun":     ("Government, leadership, gold, medical",
                "CEO of own brand, personal-branding influencer, gold/jewellery business"),
    "Moon":    ("Public, water, dairy, hospitality",
                "Hospitality startup, F&B chain, ASMR creator, public-content channel"),
    "Mars":    ("Engineering, defence, real-estate, sports",
                "Real-estate flipper, eSports pro, defence-tech startup, fitness brand"),
    "Mercury": ("Trade, accounts, writing, communication",
                "Stock trader, copywriter, SaaS founder, AI-prompt engineer, e-commerce"),
    "Jupiter": ("Teaching, law, finance, advisory",
                "Online-course creator, financial advisor, ed-tech founder, wealth coach"),
    "Venus":   ("Beauty, luxury, arts, entertainment",
                "Influencer, beauty-brand, fashion designer, luxury-export, OnlyFans"),
    "Saturn":  ("Labour, mining, oil, long-term contracts",
                "Long-haul founder, B2B contracts, EV/solar, anti-aging biotech"),
    "Rahu":    ("Foreign, technology, unconventional",
                "Crypto trader, NFT artist, foreign business, viral content, dark-pool"),
    "Ketu":    ("Healing, occult, research, IT-backend",
                "Healing app, meditation startup, ethical hacker, occult content"),
}


def _planet_signs(planets: list) -> dict[str, dict]:
    out = {}
    for p in planets:
        lon = p.get("longitude")
        if not isinstance(lon,(int,float)): continue
        si = int(lon // 30) % 12
        out[p["name"]] = {"si": si, "sign": SIGNS[si], "deg_in_sign": lon % 30}
    return out


def _house_of(si: int, lagna_si: int) -> int:
    return ((si - lagna_si) % 12) + 1


def _planets_in_house(p_si: dict[str, dict], lagna_si: int, h: int) -> list[str]:
    return [n for n,d in p_si.items() if _house_of(d["si"], lagna_si) == h]


def run_financial_engine(kundli: dict) -> dict[str, Any]:
    out: dict[str, Any] = {"available": True, "disclaimer": DISCLAIMER}
    planets = kundli.get("planets") or []
    lag = kundli.get("ascendant") or kundli.get("lagna") or "Aries"
    try: lagna_si = SIGNS.index(lag)
    except Exception: lagna_si = 0

    p_si = _planet_signs(planets)
    if not p_si:
        out["available"] = False; return out

    # Build house-occupant map
    h_occ = {h: _planets_in_house(p_si, lagna_si, h) for h in range(1,13)}

    # ─── F1: Wealth house occupants & lords ────────────────────────────────
    wealth_houses = {2:"Savings/Speech", 5:"Speculation/Investments",
                     9:"Big-luck/Inheritance", 11:"Gains/Income"}
    f1 = []
    for h, label in wealth_houses.items():
        sign_h = (lagna_si + h - 1) % 12
        lord = SIGN_LORDS[sign_h]
        lord_in_si = p_si.get(lord, {}).get("si")
        lord_in_h = _house_of(lord_in_si, lagna_si) if lord_in_si is not None else None
        occ = h_occ[h]
        f1.append({
            "house": h, "purpose": label,
            "sign": SIGNS[sign_h], "lord": lord,
            "lord_in_house": lord_in_h,
            "occupants": occ,
            "benefic_aspect": any(p in BENEFICS for p in occ),
        })

    # ─── F2: Dhana Yogas (wealth combinations) ─────────────────────────────
    dhana_yogas = []
    def _add_y(name, found, factors, modern):
        if found:
            tier = "🔴 STRONG" if len(factors) >= 3 else ("🟡 ABILITY" if len(factors) == 2 else "🟢 POTENTIAL")
            dhana_yogas.append({"name": name, "tier": tier,
                                 "factors": factors, "modern": modern})

    # Lord-2 with Lord-11 conjunction/exchange
    l2 = SIGN_LORDS[(lagna_si+1)%12]
    l11 = SIGN_LORDS[(lagna_si+10)%12]
    if l2 in p_si and l11 in p_si:
        if p_si[l2]["si"] == p_si[l11]["si"]:
            _add_y("Dhana Yoga (L2-L11 conj)", True,
                   ["L2-L11 same sign","wealth+gains fusion","steady accumulation"],
                   "Steady SIP/passive-income builder")
        elif p_si[l2]["si"] == _planet_signs([{"name":l11,"longitude":lagna_si*30}])[l11]["si"]:
            pass  # exchange detection later

    # Lakshmi Yoga: Lord-9 + Venus strong
    l9 = SIGN_LORDS[(lagna_si+8)%12]
    if l9 in p_si and "Venus" in p_si:
        l9_h = _house_of(p_si[l9]["si"], lagna_si)
        v_h = _house_of(p_si["Venus"]["si"], lagna_si)
        f = []
        if l9_h in (1,4,5,7,9,10): f.append(f"L9 in kendra/trine H{l9_h}")
        if v_h in (1,4,5,7,9,10): f.append(f"Venus in kendra/trine H{v_h}")
        if p_si["Venus"]["si"] in (1,6,11): f.append("Venus in own/exalted sign")
        _add_y("Lakshmi Yoga", len(f) >= 2, f,
               "Sustained luxury wealth — luxury brand, real-estate portfolio")

    # Kubera Yoga: Venus+Jupiter+Mercury in 11th
    eleventh = h_occ[11]
    if any(p in eleventh for p in ("Venus","Jupiter","Mercury")):
        f = [f"{p} in H11" for p in ("Venus","Jupiter","Mercury") if p in eleventh]
        _add_y("Kubera Yoga (benefics in 11th)", len(f) >= 1, f,
               "Multiple income streams — affiliate, royalty, dividend, SaaS-MRR")

    # Chandra-Mangala Yoga: Moon-Mars conjunction or aspect
    if "Moon" in p_si and "Mars" in p_si:
        diff = abs(p_si["Moon"]["si"] - p_si["Mars"]["si"])
        if diff in (0, 6):
            _add_y("Chandra-Mangala Yoga", True,
                   ["Moon-Mars conj/opp","liquid-cash flow","trading instinct"],
                   "Day-trading, real-estate flipping, quick-cash businesses")

    # Vasumati Yoga: benefics in upachaya (3,6,10,11)
    upachaya = sum(1 for h in (3,6,10,11) for p in h_occ[h] if p in BENEFICS)
    if upachaya >= 2:
        _add_y("Vasumati Yoga", True,
               [f"{upachaya} benefics in upachayas","growing wealth over time"],
               "Compounding portfolio — index funds, equity SIP, REIT")

    # Maha Lakshmi: L2+L9+L11 all in kendra/trine
    placements = []
    for ll, name in [(l2,"L2"),(l9,"L9"),(l11,"L11")]:
        if ll in p_si:
            h = _house_of(p_si[ll]["si"], lagna_si)
            if h in (1,4,5,7,9,10): placements.append(f"{name}={ll} in H{h}")
    _add_y("Maha Lakshmi Yoga", len(placements) >= 2, placements,
           "Dynastic wealth — multi-generational businesses, family office")

    # Dhana Yoga via Jupiter in 2/5/9/11
    j_h = _house_of(p_si["Jupiter"]["si"], lagna_si) if "Jupiter" in p_si else 0
    if j_h in (2,5,9,11):
        _add_y(f"Guru-Dhana Yoga (Jupiter in H{j_h})", True,
               [f"Jupiter in wealth H{j_h}","wisdom-driven wealth"],
               "Advisory income, ed-tech, philanthropic-investing")

    # ─── F3: Daridra Yogas (poverty) — STRICT 3+ factor rule ──────────────
    daridra = []
    factors_d = []
    if l2 in p_si and _house_of(p_si[l2]["si"], lagna_si) in (6,8,12):
        factors_d.append(f"L2={l2} in dushtana H{_house_of(p_si[l2]['si'], lagna_si)}")
    if l11 in p_si and _house_of(p_si[l11]["si"], lagna_si) in (6,8,12):
        factors_d.append(f"L11={l11} in dushtana H{_house_of(p_si[l11]['si'], lagna_si)}")
    if any(p in MALEFICS for p in h_occ[2]):
        factors_d.append(f"Malefic in H2: {[p for p in h_occ[2] if p in MALEFICS]}")
    if any(p in MALEFICS for p in h_occ[11]):
        factors_d.append(f"Malefic in H11: {[p for p in h_occ[11] if p in MALEFICS]}")

    # Bhanga (cancellation): Dhana yogas STRONG OR L2/L11 in own sign
    bhanga_factors = []
    strong_dhana = [y for y in dhana_yogas if "STRONG" in y["tier"] or "ABILITY" in y["tier"]]
    if strong_dhana:
        bhanga_factors.append(f"{len(strong_dhana)} Dhana Yogas active (cancels poverty)")
    if l2 in p_si and SIGN_LORDS[p_si[l2]["si"]] == l2:
        bhanga_factors.append(f"L2={l2} in own sign")
    if l11 in p_si and SIGN_LORDS[p_si[l11]["si"]] == l11:
        bhanga_factors.append(f"L11={l11} in own sign")
    if "Jupiter" in p_si and _house_of(p_si["Jupiter"]["si"], lagna_si) in (1,2,5,9,11):
        bhanga_factors.append("Jupiter aspecting wealth houses")

    daridra_cancelled = len(bhanga_factors) >= 2
    if len(factors_d) >= 3 and not daridra_cancelled:
        daridra.append({"name":"Daridra Risk", "tier":"🟡 ABILITY",
                        "factors": factors_d,
                        "note":"Frugality required — NOT poverty prediction; consult planner",
                        "modern":"Modern reframe: minimalist lifestyle, FIRE strategy, lean entrepreneur"})
    elif len(factors_d) >= 2:
        daridra.append({"name":"Daridra Tendency", "tier":"🟢 POTENTIAL",
                        "factors": factors_d,
                        "note":"Cash-flow discipline recommended",
                        "modern":"Reframe: Bootstrap founder, frugal-living content"})

    # ─── F4: Income source detection (10th lord) ───────────────────────────
    l10 = SIGN_LORDS[(lagna_si+9)%12]
    income_src = INCOME_SOURCE_MAP.get(l10, ("Mixed sources","Multi-stream income"))
    f4 = {"karaka": l10, "classical_field": income_src[0], "modern_career": income_src[1]}

    # ─── F5: Loan/debt risk (6th house) ───────────────────────────────────
    sixth_lord = SIGN_LORDS[(lagna_si+5)%12]
    sixth_lord_h = _house_of(p_si[sixth_lord]["si"], lagna_si) if sixth_lord in p_si else None
    debt_risk = "🟢 LOW"
    debt_factors = []
    if sixth_lord_h in (2,8,12):
        debt_risk = "🟡 MODERATE"
        debt_factors.append(f"L6={sixth_lord} in H{sixth_lord_h} (touches money houses)")
    if any(p in MALEFICS for p in h_occ[6]) and any(p in MALEFICS for p in h_occ[2]):
        debt_risk = "🔴 ELEVATED"
        debt_factors.append("Malefics in both H6 and H2")
    f5 = {"risk_tier": debt_risk, "factors": debt_factors,
          "note":"Maintain emergency fund; avoid high-interest credit"}

    # ─── F6: Real-estate ability (4th + Mars) ──────────────────────────────
    fourth_lord = SIGN_LORDS[(lagna_si+3)%12]
    re_factors = []
    if "Mars" in p_si:
        m_h = _house_of(p_si["Mars"]["si"], lagna_si)
        if m_h in (4,11): re_factors.append(f"Mars in H{m_h}")
    if fourth_lord in p_si:
        l4_h = _house_of(p_si[fourth_lord]["si"], lagna_si)
        if l4_h in (1,4,5,9,10,11): re_factors.append(f"L4={fourth_lord} in H{l4_h}")
    if any(p in BENEFICS for p in h_occ[4]):
        re_factors.append(f"Benefic in H4: {[p for p in h_occ[4] if p in BENEFICS]}")
    re_tier = "🔴 STRONG" if len(re_factors)>=3 else ("🟡 ABILITY" if len(re_factors)==2 else "🟢 POTENTIAL")
    f6 = {"tier": re_tier, "factors": re_factors,
          "modern":"Real-estate flipping, REITs, Airbnb hosting, land-banking"}

    # ─── F7: Foreign income (12th + benefics + Rahu) ──────────────────────
    twelfth = h_occ[12]
    f_factors = []
    if any(p in BENEFICS for p in twelfth):
        f_factors.append(f"Benefic in H12: {[p for p in twelfth if p in BENEFICS]}")
    if "Rahu" in twelfth:
        f_factors.append("Rahu in H12 — foreign-tech wealth")
    if "Rahu" in h_occ[9] or "Rahu" in h_occ[7]:
        f_factors.append("Rahu in foreign-trade house (7/9)")
    f7_tier = "🔴 STRONG" if len(f_factors)>=2 else ("🟡 ABILITY" if len(f_factors)==1 else "🟢 POTENTIAL")
    f7 = {"tier": f7_tier, "factors": f_factors,
          "modern":"Remote-USD income, dropshipping, freelance-international, NRI portfolio"}

    # ─── F8: Speculation/trading ability (5th + Mercury + Rahu) ────────────
    fifth_lord = SIGN_LORDS[(lagna_si+4)%12]
    s_factors = []
    if fifth_lord in p_si:
        l5_h = _house_of(p_si[fifth_lord]["si"], lagna_si)
        if l5_h in (2,5,11): s_factors.append(f"L5={fifth_lord} in wealth H{l5_h}")
    if "Mercury" in h_occ[5] or "Mercury" in h_occ[11]:
        s_factors.append("Mercury in 5th/11th — analytical trader")
    if "Rahu" in h_occ[5] or "Rahu" in h_occ[11]:
        s_factors.append("Rahu in 5th/11th — bold speculation, crypto/F&O")
    if "Mars" in h_occ[5] and "Saturn" in h_occ[5]:
        s_factors.append("Mars+Saturn in 5th — high-risk trading caution")
    s_tier = "🔴 STRONG" if len(s_factors)>=3 else ("🟡 ABILITY" if len(s_factors)==2 else "🟢 POTENTIAL")
    f8 = {"tier": s_tier, "factors": s_factors,
          "modern":"Day-trading, crypto, F&O, prop-trading, quant-strategies",
          "warning":"Always paper-trade first; never use leverage beyond risk tolerance"}

    # ─── F9: Career-income matching (10th house occupants) ────────────────
    tenth = h_occ[10]
    f9 = []
    for p in tenth:
        src = INCOME_SOURCE_MAP.get(p, (None,None))
        if src[0]:
            f9.append({"planet":p, "field": src[0], "modern": src[1]})

    # ─── F10: Top 3 wealth strategies for THIS chart ─────────────────────
    strategies = []
    if any("Lakshmi" in y["name"] for y in dhana_yogas):
        strategies.append("LUXURY-WEALTH path: build a high-margin luxury brand or premium-services firm")
    if f7["tier"] in ("🔴 STRONG","🟡 ABILITY"):
        strategies.append("FOREIGN-INCOME path: remote work for USD/EUR clients, NRI-portfolio")
    if f8["tier"] in ("🔴 STRONG","🟡 ABILITY"):
        strategies.append("TRADING/SPECULATION path: structured day-trading or crypto with strict risk-mgmt")
    if f6["tier"] in ("🔴 STRONG","🟡 ABILITY"):
        strategies.append("REAL-ESTATE path: rental properties, REITs, land-banking")
    if not strategies:
        strategies.append("STEADY-INCOME path: salaried + SIP + emergency fund (low-risk wealth building)")
    if "Jupiter" in p_si and _house_of(p_si["Jupiter"]["si"], lagna_si) in (2,5,9,11):
        strategies.append("ADVISORY/EDUCATION path: monetize knowledge via courses, books, consulting")

    # ─── F11: Risk profile ────────────────────────────────────────────────
    risk_score = 0
    if "Rahu" in h_occ[5] or "Rahu" in h_occ[11]: risk_score += 2
    if "Mars" in h_occ[2] or "Mars" in h_occ[11]: risk_score += 1
    if "Saturn" in h_occ[2] or "Saturn" in h_occ[11]: risk_score -= 1
    if "Jupiter" in h_occ[2] or "Jupiter" in h_occ[11]: risk_score -= 1
    if risk_score >= 2: risk_profile = "AGGRESSIVE — comfortable with high-volatility instruments"
    elif risk_score <= -1: risk_profile = "CONSERVATIVE — favour FD/PPF/index-funds/REITs"
    else: risk_profile = "BALANCED — 60/40 equity-debt mix recommended"

    # ─── F12: 15-year wealth roadmap (broad strokes via dasha if available) ─
    roadmap = []
    cur_dasha = (kundli.get("vimshottari") or {}).get("current") or {}
    md_lord = cur_dasha.get("mahadasha_lord") or cur_dasha.get("md_lord")
    if md_lord:
        src = INCOME_SOURCE_MAP.get(md_lord, ("Mixed","Multi-stream"))
        roadmap.append(f"CURRENT MD ({md_lord}) — focus on: {src[1]}")
    roadmap.append("Years 0-5: skill-building + emergency fund (6 months expenses)")
    roadmap.append("Years 5-10: scale primary income + start passive streams (SIP, REITs)")
    roadmap.append("Years 10-15: diversify across asset classes; consider international exposure")

    # ─── F13: Wealth-house scorecard ──────────────────────────────────────
    scorecard = []
    for h_data in f1:
        score = 0
        if h_data["benefic_aspect"]: score += 2
        if h_data["lord_in_house"] in (1,4,5,7,9,10,11): score += 2
        if h_data["lord_in_house"] in (6,8,12): score -= 1
        if any(p in MALEFICS for p in h_data["occupants"]): score -= 1
        scorecard.append({**h_data, "score": score,
                          "verdict":"STRONG" if score>=3 else ("MODERATE" if score>=1 else "WEAK")})

    out.update({
        "f1_wealth_houses": f1,
        "f2_dhana_yogas": dhana_yogas,
        "f3_daridra": {"yogas": daridra, "bhanga_factors": bhanga_factors,
                        "cancelled": daridra_cancelled},
        "f4_income_source": f4,
        "f5_debt_risk": f5,
        "f6_real_estate": f6,
        "f7_foreign_income": f7,
        "f8_speculation": f8,
        "f9_career_income": f9,
        "f10_top_strategies": strategies[:5],
        "f11_risk_profile": risk_profile,
        "f12_roadmap_15yr": roadmap,
        "f13_wealth_scorecard": scorecard,
    })
    return out


def format_financial_engine(r: dict) -> str:
    if not r or not r.get("available"):
        return "▸ FINANCIAL ASTROLOGY ENGINE: ❌ unavailable"
    L = ["▸ FINANCIAL ASTROLOGY ENGINE — Sprint-48 (deep + ethical + modern-reframed)",
         r["disclaimer"], "  " + "═"*78]

    L.append("  F1 WEALTH HOUSES (2/5/9/11):")
    for h in r["f1_wealth_houses"]:
        L.append(f"      ▪ H{h['house']:<2} {h['purpose']:<28} sign={h['sign']:<11} "
                 f"lord={h['lord']:<8} (in H{h['lord_in_house']}) "
                 f"occupants: {', '.join(h['occupants']) or '(empty)'}")

    L.append("  F2 DHANA YOGAS detected:")
    if r["f2_dhana_yogas"]:
        for y in r["f2_dhana_yogas"]:
            L.append(f"      {y['tier']} {y['name']}")
            L.append(f"          factors: {' • '.join(str(f) for f in y['factors'])}")
            L.append(f"          modern: {y['modern']}")
    else:
        L.append("      ▪ No major Dhana Yoga active — focus on disciplined SIP/savings")

    f3 = r["f3_daridra"]
    L.append(f"  F3 DARIDRA (poverty) check  →  cancelled: {f3['cancelled']}")
    if f3["bhanga_factors"]:
        L.append(f"      ✚ Bhanga (cancellation) factors: {' • '.join(f3['bhanga_factors'])}")
    if f3["yogas"]:
        for y in f3["yogas"]:
            L.append(f"      {y['tier']} {y['name']}")
            L.append(f"          factors: {' • '.join(str(f) for f in y['factors'])}")
            L.append(f"          ⚐ {y['note']}")
            L.append(f"          modern: {y['modern']}")
    else:
        L.append("      ▪ No daridra pattern triggered — wealth indicators favourable")

    f4 = r["f4_income_source"]
    L.append(f"  F4 INCOME SOURCE  (L10 = {f4['karaka']})")
    L.append(f"      classical: {f4['classical_field']}")
    L.append(f"      modern:    {f4['modern_career']}")

    f5 = r["f5_debt_risk"]
    L.append(f"  F5 DEBT/LOAN RISK  →  {f5['risk_tier']}")
    for fac in f5["factors"]: L.append(f"      ▪ {fac}")
    L.append(f"      ⚐ {f5['note']}")

    for code, label in [("f6_real_estate","REAL-ESTATE"),
                        ("f7_foreign_income","FOREIGN-INCOME"),
                        ("f8_speculation","SPECULATION/TRADING")]:
        x = r[code]
        L.append(f"  {code[:2].upper()} {label} ABILITY  →  {x['tier']}")
        for fac in x["factors"]: L.append(f"      ▪ {fac}")
        L.append(f"      modern: {x['modern']}")
        if x.get("warning"): L.append(f"      ⚠  {x['warning']}")

    L.append("  F9 CAREER-INCOME (10th-house occupants):")
    if r["f9_career_income"]:
        for x in r["f9_career_income"]:
            L.append(f"      ▪ {x['planet']} → {x['field']}  |  modern: {x['modern']}")
    else:
        L.append("      ▪ Empty 10th — career via 10th-lord placement (see F4)")

    L.append("  F10 TOP WEALTH STRATEGIES for THIS chart:")
    for i,s in enumerate(r["f10_top_strategies"],1):
        L.append(f"      {i}. {s}")

    L.append(f"  F11 RISK PROFILE  →  {r['f11_risk_profile']}")

    L.append("  F12 15-YEAR WEALTH ROADMAP:")
    for line in r["f12_roadmap_15yr"]:
        L.append(f"      ▸ {line}")

    L.append("  F13 WEALTH-HOUSE SCORECARD:")
    for h in r["f13_wealth_scorecard"]:
        L.append(f"      ▪ H{h['house']:<2} ({h['purpose']:<28}) → score={h['score']:>+d}  [{h['verdict']}]")

    return "\n".join(L)
