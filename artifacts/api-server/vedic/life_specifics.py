"""
Life Specifics — deep, structured kundli analysis for Career / Health / Finance
screens.

Each helper takes the same inputs (planets list + ascendant index + dasha info)
and returns structured arrays the UI can render directly:

  • compute_health_specifics() → issues[], dosha_balance, vulnerable_organs[]
  • compute_career_specifics() → tenth_lord, atmakaraka, suitable_fields[],
                                 business_vs_job, peak_growth_period
  • compute_finance_specifics() → wealth_tier, income_sources[], dhana_yogas[],
                                  peak_wealth_period

Pure deterministic Vedic logic (BPHS-based). No AI, no DB, no I/O.
Safe to call repeatedly, never raises (returns empty/default on bad input).
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional

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

# Dosha (Ayurveda) mapping — each rashi has a dominant constitution
SIGN_DOSHA = {
    "Aries":"pitta","Taurus":"kapha","Gemini":"vata","Cancer":"kapha",
    "Leo":"pitta","Virgo":"vata","Libra":"vata","Scorpio":"pitta",
    "Sagittarius":"pitta","Capricorn":"vata","Aquarius":"vata","Pisces":"kapha",
}
PLANET_DOSHA = {
    "Sun":"pitta","Mars":"pitta","Saturn":"vata","Mercury":"vata",
    "Moon":"kapha","Venus":"kapha","Jupiter":"kapha","Rahu":"vata","Ketu":"vata",
}

# Body areas governed by each rashi (head→feet, classical)
SIGN_ORGAN = {
    "Aries":"Sir, brain, eyes",
    "Taurus":"Throat, neck, vocal cord",
    "Gemini":"Lungs, shoulders, arms, nervous system",
    "Cancer":"Chest, heart-area, stomach, breasts",
    "Leo":"Heart, upper back, spine",
    "Virgo":"Intestines, digestion, abdomen",
    "Libra":"Lower back, kidneys, urinary",
    "Scorpio":"Reproductive organs, pelvis, colon",
    "Sagittarius":"Hips, thighs, liver",
    "Capricorn":"Knees, joints, bones, skin",
    "Aquarius":"Calves, ankles, blood circulation",
    "Pisces":"Feet, lymphatic system, immunity",
}

PLANET_DISEASE_TENDENCY = {
    "Sun":     ("Heart, eyes, BP, low immunity",          "warm constitution; avoid overheating"),
    "Moon":    ("Mind, mood, sleep, hormones, fluids",    "needs emotional stability + hydration"),
    "Mars":    ("Inflammation, blood, accidents, acidity","needs anger control + cooling foods"),
    "Mercury": ("Nervous system, skin, speech, digestion","needs calm routine + light meals"),
    "Jupiter": ("Liver, weight, diabetes, blood-sugar",   "watch sugar + sweets intake"),
    "Venus":   ("Reproductive, kidney, urinary, hormones","needs hygiene + balanced sweetness"),
    "Saturn":  ("Joints, bones, knees, chronic ailments", "needs warmth + slow patience"),
    "Rahu":    ("Sudden / unexplained / allergy / phobia","needs grounding + clean environment"),
    "Ketu":    ("Hidden / parasitic / spiritual sensitivity","needs detox + meditation"),
}

# Career profession mapping per planet (classical Jyotish + modern reframe)
PLANET_PROFESSIONS = {
    "Sun":     ["Government / Civil services", "Politics / Administration",
                "Medical / Surgery", "Leadership roles / CEO",
                "Pharma", "Cardiology", "Gold / Bullion trading"],
    "Moon":    ["Hospitality / Hotel", "Public relations / Communication",
                "Mother-and-child healthcare", "Dairy / Liquids / Beverages",
                "Travel / Tourism", "Mental health / Counseling",
                "Fashion / Beauty", "Real estate"],
    "Mars":    ["Defense / Army / Police", "Engineering (mechanical / civil)",
                "Surgery / Dental", "Sports / Athletics", "Real estate",
                "Construction / Builder", "Fire safety", "Metals / Steel"],
    "Mercury": ["IT / Software / Coding", "Business / Trading / Stocks",
                "Writing / Journalism / Editing", "Accounts / CA / Audit",
                "Teaching / Tutoring", "Marketing / Sales",
                "Astrology / Mathematics", "Telecom"],
    "Jupiter": ["Teaching / Professor", "Law / Judiciary", "Banking / Finance / Treasury",
                "Religious / Spiritual leadership", "Counseling / Coaching",
                "Publishing / Education sector", "Wealth advisory",
                "Pediatrics / Liver-specialist medicine"],
    "Venus":   ["Arts / Music / Films / Acting", "Fashion / Cosmetics / Beauty",
                "Hospitality / Luxury / Hotels", "Diplomacy",
                "Interior design / Architecture", "Jewelry / Diamonds",
                "Modelling / Photography", "Wedding / Event planning"],
    "Saturn":  ["Mining / Oil / Coal / Iron / Heavy industry",
                "Labour / Manufacturing", "Civil engineering / Real estate (long-term)",
                "Judiciary / Law", "Research / Science (long timelines)",
                "Servant of public — social service", "Agriculture",
                "Insurance / Pension"],
    "Rahu":    ["Foreign-related / Import-export", "Aviation / Airlines",
                "Photography / Cinema / Media", "Software / Cyber / AI",
                "Stock speculation / Crypto", "Politics / Power",
                "Research in unusual fields", "Pharma / Chemicals"],
    "Ketu":    ["Spirituality / Astrology / Tantra", "Research / R&D",
                "Medicine / Healing arts", "Philosophy",
                "Computer engineering", "Veterinary",
                "Detective / Investigation"],
}

# Dhana yoga rules (simplified — most common combos)
def _has_dhana_yoga(planets: List[dict], lord_2: str, lord_5: str,
                    lord_9: str, lord_11: str) -> List[Dict[str, str]]:
    """Detect classical wealth yogas (Lakshmi, Dhana, Kubera-like)."""
    yogas: List[Dict[str, str]] = []

    def _planet_in_house(name: str) -> Optional[int]:
        for p in planets:
            if p.get("name") == name:
                return p.get("house")
        return None

    h2  = _planet_in_house(lord_2)
    h5  = _planet_in_house(lord_5)
    h9  = _planet_in_house(lord_9)
    h11 = _planet_in_house(lord_11)

    # Dhana Yoga — 2nd lord and 11th lord conjunct or in trine
    if h2 and h11 and (h2 == h11 or abs(h2 - h11) in (4, 8)):
        yogas.append({
            "name": "Dhana Yoga",
            "detail": f"2nd & 11th lords ({lord_2} + {lord_11}) connected — strong wealth-flow combination."
        })

    # Lakshmi Yoga — 9th lord strong + Venus strong
    ven = next((p for p in planets if p.get("name") == "Venus"), None)
    if ven and h9 in (1, 4, 5, 7, 9, 10, 11):
        if (ven.get("sign") in OWN.get("Venus", []) or
                ven.get("sign") == EXALT["Venus"]):
            yogas.append({
                "name": "Lakshmi Yoga",
                "detail": f"9th lord {lord_9} well-placed + Venus dignified — luxury and wealth blessings."
            })

    # Kubera-like — Jupiter + 2nd lord in own/exalted in kendra/trikona
    jup = next((p for p in planets if p.get("name") == "Jupiter"), None)
    if jup and jup.get("house") in (1, 4, 5, 7, 9, 10):
        if jup.get("sign") in OWN.get("Jupiter", []) or jup.get("sign") == EXALT["Jupiter"]:
            yogas.append({
                "name": "Kubera Yoga (Jupiter wealth blessing)",
                "detail": "Jupiter dignified in kendra/trikona — divine wealth protection and growth."
            })

    # Chandra-Mangal Yoga — Moon and Mars in conjunction
    moon = next((p for p in planets if p.get("name") == "Moon"), None)
    mars = next((p for p in planets if p.get("name") == "Mars"), None)
    if moon and mars and moon.get("house") == mars.get("house"):
        yogas.append({
            "name": "Chandra-Mangal Yoga",
            "detail": "Moon-Mars conjunction — natural ability to convert ideas into money; entrepreneurial."
        })

    return yogas


# ── HEALTH ────────────────────────────────────────────────────────────────
def compute_health_specifics(planets: List[dict], asc_idx: int,
                             current_dasha: Optional[dict] = None
                             ) -> Dict[str, Any]:
    """Return structured health issues, dosha balance, vulnerable organs."""
    try:
        sign_1  = SIGNS[asc_idx % 12]
        sign_6  = SIGNS[(asc_idx + 5) % 12]
        sign_8  = SIGNS[(asc_idx + 7) % 12]
        sign_12 = SIGNS[(asc_idx + 11) % 12]

        def find_p(n):
            return next((p for p in planets if p.get("name") == n), None)

        # ── Issues list (each issue = body area + risk + reason) ──────────
        issues: List[Dict[str, Any]] = []

        # Lagna (1H) gives constitution; afflictions here = baseline weakness
        for p in planets:
            if p.get("house") == 1 and p.get("name") in ("Saturn", "Mars", "Rahu", "Ketu"):
                organ = SIGN_ORGAN.get(sign_1, "")
                disease, _ = PLANET_DISEASE_TENDENCY.get(p["name"], ("", ""))
                issues.append({
                    "area":       sign_1 + " (Lagna)",
                    "organs":     organ,
                    "risk":       "High" if p["name"] == "Saturn" else "Medium",
                    "reason":     f"{p['name']} in 1st house — {disease}",
                    "remedy":     PLANET_DISEASE_TENDENCY[p["name"]][1],
                })

        # 6H = disease house — every malefic here is a real issue
        for p in planets:
            if p.get("house") == 6:
                organ = SIGN_ORGAN.get(sign_6, "")
                disease, advice = PLANET_DISEASE_TENDENCY.get(p["name"], ("", ""))
                if not disease:
                    continue
                risk = "High" if p["name"] in ("Saturn", "Mars", "Rahu") else "Medium"
                issues.append({
                    "area":       f"{sign_6} (6th house — disease)",
                    "organs":     organ,
                    "risk":       risk,
                    "reason":     f"{p['name']} in 6th — {disease}",
                    "remedy":     advice,
                })

        # 8H = chronic / longevity — Saturn, Rahu, Ketu critical
        for p in planets:
            if p.get("house") == 8 and p.get("name") in ("Saturn", "Rahu", "Ketu", "Mars"):
                organ = SIGN_ORGAN.get(sign_8, "")
                disease, advice = PLANET_DISEASE_TENDENCY.get(p["name"], ("", ""))
                issues.append({
                    "area":       f"{sign_8} (8th — chronic)",
                    "organs":     organ,
                    "risk":       "High",
                    "reason":     f"{p['name']} in 8th — chronic tendency in {disease.split(',')[0]}",
                    "remedy":     advice,
                })

        # 12H = sleep / hospital / hidden
        for p in planets:
            if p.get("house") == 12 and p.get("name") in ("Saturn", "Rahu", "Ketu", "Moon"):
                organ = SIGN_ORGAN.get(sign_12, "")
                disease, advice = PLANET_DISEASE_TENDENCY.get(p["name"], ("", ""))
                if p["name"] == "Moon":
                    issues.append({
                        "area":   "Sleep / mental rest",
                        "organs": "Mind, sleep cycle, hidden anxiety",
                        "risk":   "Medium",
                        "reason": "Moon in 12th — disturbed sleep, vivid dreams, mental fatigue",
                        "remedy": "10:30 PM se pehle sleep, white food, somvar pe Shiv mantra",
                    })
                else:
                    issues.append({
                        "area":   f"{sign_12} (12th — hidden)",
                        "organs": organ,
                        "risk":   "Medium",
                        "reason": f"{p['name']} in 12th — hidden issue or hospitalization risk",
                        "remedy": advice,
                    })

        # Debilitated key planets always add an issue
        for nm in ("Sun", "Moon", "Mars", "Mercury", "Jupiter"):
            p = find_p(nm)
            if p and p.get("sign") == DEBIL.get(nm):
                disease, advice = PLANET_DISEASE_TENDENCY.get(nm, ("", ""))
                issues.append({
                    "area":   f"{nm} karaka weak",
                    "organs": disease.split(",")[0] if disease else "",
                    "risk":   "Medium",
                    "reason": f"{nm} debilitated in {p.get('sign')} — natural karaka weakness",
                    "remedy": advice,
                })

        # ── Dosha balance (Vata/Pitta/Kapha %) ────────────────────────────
        dosha_score = {"vata": 0, "pitta": 0, "kapha": 0}
        # Ascendant contributes 30%
        d_asc = SIGN_DOSHA.get(sign_1)
        if d_asc:
            dosha_score[d_asc] += 30
        # Moon sign 30%
        moon = find_p("Moon")
        if moon:
            d_moon = SIGN_DOSHA.get(moon.get("sign", ""))
            if d_moon:
                dosha_score[d_moon] += 30
        # Sun sign 20%
        sun = find_p("Sun")
        if sun:
            d_sun = SIGN_DOSHA.get(sun.get("sign", ""))
            if d_sun:
                dosha_score[d_sun] += 20
        # Lagna lord planet dosha 20%
        lord_1 = SIGN_LORD.get(sign_1)
        l1p = find_p(lord_1)
        if l1p:
            d_l1 = PLANET_DOSHA.get(lord_1)
            if d_l1:
                dosha_score[d_l1] += 20
        total = sum(dosha_score.values()) or 1
        dosha_balance = {k: round(v * 100 / total) for k, v in dosha_score.items()}
        dominant = max(dosha_balance, key=dosha_balance.get)

        # ── Vulnerable organs list (deduped) ──────────────────────────────
        vuln_set: List[str] = []
        for issue in issues:
            for organ in (issue.get("organs") or "").split(","):
                o = organ.strip()
                if o and o not in vuln_set:
                    vuln_set.append(o)

        # ── Risk distribution
        risk_counts = {"High": 0, "Medium": 0, "Low": 0}
        for it in issues:
            risk_counts[it.get("risk", "Low")] = risk_counts.get(it.get("risk", "Low"), 0) + 1

        return {
            "issues":             issues[:12],   # cap at 12
            "issues_total":       len(issues),
            "issues_by_severity": risk_counts,
            "dosha_balance":      dosha_balance,
            "dominant_dosha":     dominant.title(),
            "vulnerable_organs":  vuln_set[:10],
        }
    except Exception as exc:
        return {"issues": [], "issues_total": 0, "error": str(exc)}


# ── CAREER ────────────────────────────────────────────────────────────────
def compute_career_specifics(planets: List[dict], asc_idx: int,
                             current_dasha: Optional[dict] = None
                             ) -> Dict[str, Any]:
    """Return 10th-lord deep analysis, atmakaraka, suitable fields."""
    try:
        sign_10 = SIGNS[(asc_idx + 9) % 12]
        lord_10 = SIGN_LORD[sign_10]

        def find_p(n):
            return next((p for p in planets if p.get("name") == n), None)

        # ── 10th lord deep breakdown ──────────────────────────────────────
        l10 = find_p(lord_10)
        tenth_lord: Dict[str, Any] = {
            "planet":  lord_10,
            "sign_10": sign_10,
        }
        if l10:
            sg = l10.get("sign", "")
            h  = l10.get("house", 0)
            status = "neutral"
            strength = 50
            if sg == EXALT.get(lord_10):
                status = "exalted"; strength += 30
            elif sg == DEBIL.get(lord_10):
                status = "debilitated"; strength -= 25
            elif sg in OWN.get(lord_10, []):
                status = "own sign"; strength += 20
            if h in (1, 4, 5, 7, 9, 10, 11):
                strength += 15
            elif h in (6, 8, 12):
                strength -= 20
            if l10.get("retrograde"):
                strength -= 5
            strength = max(10, min(95, strength))

            verdict = (
                "Career karma very strong — natural authority, recognition aata hai."
                if strength >= 75 else
                "Career karma supportive — sustained effort se good growth."
                if strength >= 55 else
                "Career karma needs effort — patience + skill-building zaroori."
                if strength >= 35 else
                "Career karma challenging — wrong direction se bachein, mentorship le."
            )
            tenth_lord.update({
                "current_sign":   sg,
                "current_house":  h,
                "status":         status,
                "strength_pct":   strength,
                "retrograde":     bool(l10.get("retrograde")),
                "verdict":        verdict,
            })

        # ── Atmakaraka (Jaimini) — planet with highest degrees ────────────
        atmak: Optional[Dict[str, str]] = None
        ranked = sorted(
            [p for p in planets if p.get("name") in
             ("Sun","Moon","Mars","Mercury","Jupiter","Venus","Saturn","Rahu")],
            key=lambda p: float(p.get("degree", p.get("longitude", 0)) or 0) % 30,
            reverse=True,
        )
        if ranked:
            ak = ranked[0]
            atmak = {
                "planet":  ak.get("name"),
                "meaning": _atmakaraka_meaning(ak.get("name", "")),
            }

        # ── 10th house occupants influence too
        occupants = [p["name"] for p in planets if p.get("house") == 10]

        # ── Suitable fields (top 5 by combined planet-power) ──────────────
        # Score each planet's contribution
        planet_power = {}
        # 10th lord = top contributor
        planet_power[lord_10] = 30
        # Each occupant of 10H adds 20
        for nm in occupants:
            planet_power[nm] = planet_power.get(nm, 0) + 20
        # Atmakaraka adds 15
        if atmak:
            planet_power[atmak["planet"]] = planet_power.get(atmak["planet"], 0) + 15
        # Strong planets (exalted/own) add 10
        for p in planets:
            nm = p.get("name")
            if nm in EXALT and p.get("sign") == EXALT[nm]:
                planet_power[nm] = planet_power.get(nm, 0) + 10
            elif nm in OWN and p.get("sign") in OWN[nm]:
                planet_power[nm] = planet_power.get(nm, 0) + 6

        # Build field scores
        field_scores: Dict[str, int] = {}
        field_source: Dict[str, str] = {}
        for plnt, power in planet_power.items():
            for field in PLANET_PROFESSIONS.get(plnt, []):
                add = power
                field_scores[field] = field_scores.get(field, 0) + add
                if field not in field_source:
                    field_source[field] = plnt

        suitable = sorted(field_scores.items(), key=lambda x: -x[1])[:6]
        max_s = max((s for _, s in suitable), default=1)
        suitable_fields = [
            {"field": f, "score": round(s * 100 / max_s),
             "driver": f"Driven by {field_source[f]}"}
            for f, s in suitable
        ]

        # ── Business vs Job ──────────────────────────────────────────────
        # Strong Mercury / Mars / Rahu in 7H or 10H, or Sun weak → Business
        # Strong Sun / Saturn / Jupiter → Job / Service
        biz_score = 0
        job_score = 0
        sun = find_p("Sun"); sat = find_p("Saturn")
        merc = find_p("Mercury"); mars = find_p("Mars")
        if sun and sun.get("house") in (1, 10):
            job_score += 20
        if sun and sun.get("sign") == DEBIL["Sun"]:
            biz_score += 10; job_score -= 5
        if sat and sat.get("house") in (1, 10, 11):
            job_score += 15
        if merc and merc.get("house") in (3, 7, 10, 11):
            biz_score += 15
        if mars and mars.get("house") in (3, 7, 10):
            biz_score += 10
        rahu = find_p("Rahu")
        if rahu and rahu.get("house") in (7, 10, 11):
            biz_score += 15
        # 10H occupants
        for p in planets:
            if p.get("house") == 10 and p.get("name") in ("Mercury","Mars","Rahu","Venus"):
                biz_score += 10
            if p.get("house") == 10 and p.get("name") in ("Sun","Saturn","Jupiter"):
                job_score += 10

        if biz_score > job_score + 10:
            biz_verdict = "Business / Self-employment favored"
        elif job_score > biz_score + 10:
            biz_verdict = "Service / Job favored"
        else:
            biz_verdict = "Hybrid — Job + side-business / freelance combination ideal"

        # ── Peak growth period (current dasha lens) ───────────────────────
        cd = current_dasha or {}
        md = cd.get("maha", "")
        DASHA_GROWTH = {"Jupiter":"Excellent","Sun":"Excellent","Mercury":"Very Good",
                        "Saturn":"Good (slow but solid)","Mars":"Mixed (works in spurts)",
                        "Venus":"Average","Moon":"Average","Rahu":"Volatile (sudden moves)",
                        "Ketu":"Pause / introspection phase"}
        peak_period = {
            "current_md":  md,
            "rating":      DASHA_GROWTH.get(md, "Neutral"),
            "ends":        cd.get("endDate", ""),
            "next_lord":   cd.get("nextMaha", ""),
        }

        return {
            "tenth_house":        {"sign": sign_10, "lord": lord_10,
                                   "occupants": ", ".join(occupants) or "Khaali"},
            "tenth_lord":         tenth_lord,
            "atmakaraka":         atmak,
            "suitable_fields":    suitable_fields,
            "business_vs_job":    biz_verdict,
            "peak_growth_period": peak_period,
        }
    except Exception as exc:
        return {"error": str(exc)}


def _atmakaraka_meaning(planet: str) -> str:
    return {
        "Sun":     "Soul wants leadership, authority, recognition. Govt / leadership roles fulfill you.",
        "Moon":    "Soul wants nurturing, public connection, emotional work. People-facing careers shine.",
        "Mars":    "Soul wants action, courage, defending. Engineering / defense / surgery / sports satisfy.",
        "Mercury": "Soul wants intellect, analysis, communication. IT / business / writing / accounts work best.",
        "Jupiter": "Soul wants wisdom-sharing, teaching, guidance. Teaching / law / advisory roles bring purpose.",
        "Venus":   "Soul wants beauty, harmony, relationships. Arts / luxury / design / hospitality fulfill.",
        "Saturn":  "Soul wants discipline, hard work, service. Long-haul careers, social-service, infra work.",
        "Rahu":    "Soul wants the unconventional. Foreign / tech / fame / new fields ka pull rahega.",
    }.get(planet, "Career karma indicates a unique path — listen to inner pull.")


# ── FINANCE ───────────────────────────────────────────────────────────────
def compute_finance_specifics(planets: List[dict], asc_idx: int,
                              current_dasha: Optional[dict] = None
                              ) -> Dict[str, Any]:
    """Return wealth tier, income sources, dhana yogas."""
    try:
        sign_2  = SIGNS[(asc_idx + 1)  % 12]
        sign_5  = SIGNS[(asc_idx + 4)  % 12]
        sign_9  = SIGNS[(asc_idx + 8)  % 12]
        sign_11 = SIGNS[(asc_idx + 10) % 12]
        lord_2  = SIGN_LORD[sign_2]
        lord_5  = SIGN_LORD[sign_5]
        lord_9  = SIGN_LORD[sign_9]
        lord_11 = SIGN_LORD[sign_11]

        def find_p(n):
            return next((p for p in planets if p.get("name") == n), None)

        # ── Wealth tier (composite score) ─────────────────────────────────
        wealth_score = 50
        for ld in (lord_2, lord_11, lord_9):
            p = find_p(ld)
            if p:
                if p.get("house") in (1, 2, 5, 9, 10, 11): wealth_score += 8
                elif p.get("house") in (6, 8, 12): wealth_score -= 8
                if ld in EXALT and p.get("sign") == EXALT[ld]: wealth_score += 6
                elif ld in DEBIL and p.get("sign") == DEBIL[ld]: wealth_score -= 6

        # Jupiter / Venus karaka power
        jup = find_p("Jupiter")
        ven = find_p("Venus")
        if jup and jup.get("sign") == EXALT["Jupiter"]: wealth_score += 8
        if jup and jup.get("house") in (2, 5, 9, 11): wealth_score += 4
        if ven and ven.get("sign") == EXALT["Venus"]: wealth_score += 5
        wealth_score = max(20, min(95, wealth_score))

        if wealth_score >= 75:
            tier = "Wealthy"; tier_msg = "Strong wealth karma — luxury and abundance natural rahegi."
        elif wealth_score >= 60:
            tier = "Comfortable"; tier_msg = "Comfortable life ka clear support hai — savings & growth dono possible."
        elif wealth_score >= 45:
            tier = "Building"; tier_msg = "Wealth build hoga effort se — middle-class se upper-middle ki direction."
        else:
            tier = "Struggle"; tier_msg = "Wealth karma challenging — discipline + remedies + skill upgrade zaroori."

        # ── Income sources (top 5 by planet placement) ───────────────────
        sources: List[Dict[str, Any]] = []

        def _add(label: str, strength: int, why: str):
            sources.append({"source": label, "strength": max(10, min(95, strength)), "why": why})

        # Sun strong → Govt / authority income
        sun = find_p("Sun")
        if sun:
            s = 50
            if sun.get("house") in (1, 10, 11): s += 25
            if sun.get("sign") == EXALT["Sun"]: s += 15
            _add("Government / Authority / Salary", s,
                 f"Sun in {sun.get('sign')} ({sun.get('house')}H)")

        # Mercury strong → Business / Trading
        merc = find_p("Mercury")
        if merc:
            s = 45
            if merc.get("house") in (1, 2, 7, 10, 11): s += 25
            if merc.get("sign") == EXALT["Mercury"]: s += 15
            _add("Business / Trading / IT income", s,
                 f"Mercury in {merc.get('sign')} ({merc.get('house')}H)")

        # Venus strong → Luxury / Arts / Comfort income
        if ven:
            s = 45
            if ven.get("house") in (1, 2, 4, 7, 10, 11): s += 25
            if ven.get("sign") == EXALT["Venus"]: s += 15
            _add("Arts / Luxury / Beauty / Hospitality", s,
                 f"Venus in {ven.get('sign')} ({ven.get('house')}H)")

        # Jupiter strong → Teaching / Advisory / Inheritance
        if jup:
            s = 50
            if jup.get("house") in (2, 5, 9, 11): s += 25
            if jup.get("sign") == EXALT["Jupiter"]: s += 15
            _add("Teaching / Advisory / Inheritance / Banking", s,
                 f"Jupiter in {jup.get('sign')} ({jup.get('house')}H)")

        # Mars strong → Real estate / Engineering / Property income
        mars = find_p("Mars")
        if mars:
            s = 40
            if mars.get("house") in (1, 4, 10, 11): s += 25
            if mars.get("sign") == EXALT["Mars"]: s += 15
            _add("Real estate / Engineering / Property", s,
                 f"Mars in {mars.get('sign')} ({mars.get('house')}H)")

        # Saturn → Long-term / Service / Heavy industry
        sat = find_p("Saturn")
        if sat:
            s = 40
            if sat.get("house") in (10, 11): s += 25
            if sat.get("sign") == EXALT["Saturn"]: s += 15
            elif sat.get("sign") in OWN["Saturn"]: s += 10
            _add("Long-term service / Heavy industry / Pension", s,
                 f"Saturn in {sat.get('sign')} ({sat.get('house')}H)")

        # Rahu → Foreign / Speculation
        rahu = find_p("Rahu")
        if rahu and rahu.get("house") in (2, 5, 7, 10, 11):
            _add("Foreign income / Speculation / Crypto",
                 60, f"Rahu in {rahu.get('house')}H — sudden / unconventional gains possible")

        # Sort + cap at 6
        sources = sorted(sources, key=lambda x: -x["strength"])[:6]

        # ── Dhana yogas ─────────────────────────────────────────────────
        yogas = _has_dhana_yoga(planets, lord_2, lord_5, lord_9, lord_11)

        # ── Peak wealth period
        cd = current_dasha or {}
        md = cd.get("maha", "")
        DASHA_WEALTH = {"Jupiter":"Excellent","Venus":"Excellent","Mercury":"Very Good",
                        "Sun":"Good","Moon":"Average","Saturn":"Slow but Solid",
                        "Mars":"Volatile","Rahu":"Sudden gains/losses","Ketu":"Spiritual phase"}
        peak = {"current_md": md, "rating": DASHA_WEALTH.get(md, "Neutral"),
                "ends": cd.get("endDate", "")}

        return {
            "wealth_tier":        tier,
            "wealth_tier_msg":    tier_msg,
            "wealth_score":       wealth_score,
            "income_sources":     sources,
            "dhana_yogas":        yogas,
            "yogas_count":        len(yogas),
            "peak_wealth_period": peak,
        }
    except Exception as exc:
        return {"error": str(exc)}
