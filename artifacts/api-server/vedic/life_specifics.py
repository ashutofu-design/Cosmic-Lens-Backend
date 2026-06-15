"""
Life Specifics — deep, structured kundli analysis for Career / Health / Finance
screens.

Each helper takes the same inputs (planets list + ascendant index + dasha info)
and returns structured arrays the UI can render directly:

  • compute_health_specifics() → issues[], dosha_balance, vulnerable_organs[]
  • compute_career_specifics() → tenth_lord, atmakaraka, suitable_fields[],
                                 business_vs_job, peak_growth_period
  • compute_finance_specifics() → wealth_tier, dhana_yogas[],
  • compute_career_specifics() → suitable_fields[] (classical 10H / 10L rules),
                                  peak_growth_period

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

_DUSTHANA_HOUSES = frozenset({6, 8, 12})


def compute_tridosha_balance(
    planets: List[dict],
    asc_idx: int,
    kundli: Optional[dict] = None,
) -> Dict[str, Any]:
    from vedic.health_tridosha_engine import compute_tridosha_balance as _compute

    return _compute(planets, asc_idx, kundli)

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

_MALEFICS = frozenset({"Saturn", "Mars", "Rahu", "Ketu"})

# 6th lord placed in house → rog / health theme (plain language)
_LORD_6_IN_HOUSE: Dict[int, str] = {
    1: "6th lord in 1st house — illness can affect overall constitution",
    2: "6th lord in 2nd house — throat, diet and digestion need steady care",
    3: "6th lord in 3rd house — stress, nerves and shoulders may carry strain",
    4: "6th lord in 4th house — chest, stomach or emotional comfort may feel taxed",
    5: "6th lord in 5th house — digestion, children or creative stress can drain energy",
    6: "6th lord in 6th house — disease house doubled; recurring complaints possible",
    7: "6th lord in 7th house — partner or public life may reflect health friction",
    8: "6th lord in 8th house — chronic, slow recovery or hidden complaints possible",
    9: "6th lord in 9th house — long travel or faith fatigue can lower immunity",
    10: "6th lord in 10th house — work load and career pressure may affect health",
    11: "6th lord in 11th house — social strain or irregular routine may wear immunity",
    12: "6th lord in 12th house — hidden weakness, sleep loss or hospital/rest themes",
}

_LORD_8_IN_HOUSE: Dict[int, str] = {
    8: "8th lord in 8th house — chronic or deep health cycles need patience",
    6: "8th lord in 6th house — illness and longevity houses linked — guard recovery",
    12: "8th lord in 12th house — hidden fatigue, isolation or hospital themes",
    1: "8th lord in 1st house — vitality can feel sensitive in hard seasons",
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

# Dhana yoga — approved list only (see dhan_yoga_engine_v1)
def _has_dhana_yoga_for_chart(planets: List[dict], asc_idx: int) -> List[Dict[str, str]]:
    from vedic.dhan_yoga_engine_v1 import scan_dhan_yogas
    return [
        {"name": y["name"], "detail": y["detail"]}
        for y in scan_dhan_yogas(planets, asc_idx)
    ]


def _serialize_yoga_metrics_api(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [
        {
            "name": str(y.get("name") or ""),
            "detail": str(y.get("detail") or ""),
            "link": str(y.get("link") or ""),
            "houses": list(y.get("houses") or []),
            "planets": list(y.get("planets") or []),
        }
        for y in (items or [])
    ]


def _serialize_dhan_yogas_api(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return _serialize_yoga_metrics_api(items)


def _patch_wealth_finance_yoga_details(
    wealth_finance: Dict[str, Any],
    planets: List[dict],
    asc_idx: int,
) -> Dict[str, Any]:
    """Always attach full dhan_yogas[] and raj_yogas[] for Finance tap-detail UI."""
    from vedic.dhan_yoga_engine_v1 import scan_dhan_yogas
    from vedic.raj_yoga_engine_v1 import scan_raj_yogas
    wf = dict(wealth_finance or {})
    ym = dict(wf.get("yog_metrics") or {})
    dhan = scan_dhan_yogas(planets, asc_idx)
    raj = scan_raj_yogas(planets, asc_idx)
    ym["dhan_yogas"] = _serialize_yoga_metrics_api(dhan)
    ym["dhan_count"] = len(ym["dhan_yogas"])
    ym["dhan_yoga_names"] = [x["name"] for x in ym["dhan_yogas"] if x.get("name")]
    ym["raj_yogas"] = _serialize_yoga_metrics_api(raj)
    ym["raj_count"] = len(ym["raj_yogas"])
    ym["raj_yoga_names"] = [x["name"] for x in ym["raj_yogas"] if x.get("name")]
    wf["yog_metrics"] = ym
    return wf


def _patch_wealth_finance_dhan_details(
    wealth_finance: Dict[str, Any],
    planets: List[dict],
    asc_idx: int,
) -> Dict[str, Any]:
    return _patch_wealth_finance_yoga_details(wealth_finance, planets, asc_idx)


# ── HEALTH chart helpers ───────────────────────────────────────────────────
def _sign_idx(sign: str) -> int:
    try:
        return SIGNS.index(sign)
    except ValueError:
        return 0


def _aspectors_on_house(planets: List[dict], asc_idx: int, house: int) -> List[str]:
    """Planets whose sign aspects the target house (Mars/Jup/Sat/Rahu/Ketu drishti)."""
    tgt = (asc_idx + house - 1) % 12
    hits: List[str] = []
    for p in planets or []:
        nm = p.get("name")
        if not nm:
            continue
        ps = _sign_idx(str(p.get("sign") or ""))
        d = (tgt - ps + 12) % 12
        ok = d == 6
        if nm == "Mars":
            ok = ok or d in (3, 7)
        elif nm == "Jupiter":
            ok = ok or d in (4, 8)
        elif nm == "Saturn":
            ok = ok or d in (2, 9)
        elif nm in ("Rahu", "Ketu"):
            ok = ok or d in (4, 8)
        if ok and nm not in hits:
            hits.append(str(nm))
    return hits


# Short UI lines — chart logic stays internal; no house/planet names in output.
_PLANET_WELLNESS_SHORT: Dict[str, str] = {
    "Sun": "Heart, BP, eyes",
    "Moon": "Mind, sleep, hormones",
    "Mars": "Inflammation, acidity, injuries",
    "Mercury": "Nerves, skin, light digestion",
    "Jupiter": "Liver, blood sugar, weight",
    "Venus": "Kidney, hormones, urinary",
    "Saturn": "Joints, bones, chronic pain",
    "Rahu": "Sudden issues, allergies, phobia",
    "Ketu": "Hidden, unexplained, throat-area",
}

_LORD_6_PLAIN: Dict[int, str] = {
    1: "Illness can weaken whole-body strength",
    2: "Throat, diet and digestion",
    3: "Stress, nerves and shoulders",
    4: "Chest, stomach or inner peace",
    5: "Digestion and inner tension",
    6: "Recurring complaints",
    7: "Health tied to relationships or balance",
    8: "Slow or chronic recovery",
    9: "Immunity down after travel or strain",
    10: "Work pressure on health",
    11: "Irregular routine wears immunity",
    12: "Sleep loss or hidden fatigue",
}

_LORD_8_PLAIN: Dict[int, str] = {
    1: "Vitality sensitive in hard phases",
    6: "Illness and recovery need extra care",
    8: "Deep or chronic health cycles",
    12: "Hidden fatigue or rest needed",
}


def _wellness_zone_from_sign(sign: str) -> str:
    raw = SIGN_ORGAN.get(sign, "")
    parts = [p.strip() for p in raw.split(",") if p.strip()]
    if not parts:
        return ""
    return " & ".join(parts[:2])


def _wellness_issue_from_planet(planet: str) -> str:
    return _PLANET_WELLNESS_SHORT.get(
        planet,
        (PLANET_DISEASE_TENDENCY.get(planet, ("Sensitivity", ""))[0].split(",")[0] or "Sensitivity").strip(),
    )


def _build_wellness_sensitivities_from_chart(
    planets: List[dict], asc_idx: int
) -> List[str]:
    """Plain health sensitivities from 1st / 6th / 8th — no house or aspect wording."""
    out: List[str] = []
    seen: set = set()

    def push(line: str) -> None:
        key = line.lower().strip()
        if not key or key in seen or len(out) >= 6:
            return
        seen.add(key)
        out.append(line.strip())

    def find_p(name: str):
        return next((p for p in planets if p.get("name") == name), None)

    sign_6 = SIGNS[(asc_idx + 5) % 12]
    sign_8 = SIGNS[(asc_idx + 7) % 12]
    sign_1 = SIGNS[asc_idx % 12]
    lord_6 = SIGN_LORD[sign_6]
    lord_8 = SIGN_LORD[sign_8]
    lord_1 = SIGN_LORD[sign_1]

    occ_6 = [p for p in planets if int(p.get("house") or 0) == 6]
    zone_6 = _wellness_zone_from_sign(sign_6)
    if zone_6 and (occ_6 or _aspectors_on_house(planets, asc_idx, 6)):
        push(zone_6)

    for p in occ_6:
        push(_wellness_issue_from_planet(str(p.get("name") or "")))

    l6 = find_p(lord_6)
    if l6:
        h6 = int(l6.get("house") or 0)
        if h6 in _LORD_6_PLAIN:
            push(_LORD_6_PLAIN[h6])
        elif h6:
            push(_wellness_zone_from_sign(SIGNS[(asc_idx + h6 - 1) % 12]))
        if l6.get("sign") == DEBIL.get(lord_6):
            push("Low immunity, slow recovery")

    for nm in _aspectors_on_house(planets, asc_idx, 6):
        if nm not in {str(p.get("name")) for p in occ_6}:
            push(_wellness_issue_from_planet(nm))

    occ_8 = [p for p in planets if int(p.get("house") or 0) == 8]
    zone_8 = _wellness_zone_from_sign(sign_8)
    if occ_8 and zone_8:
        push(zone_8)
    for p in occ_8:
        push(_wellness_issue_from_planet(str(p.get("name") or "")))

    l8 = find_p(lord_8)
    if l8:
        h8 = int(l8.get("house") or 0)
        if h8 in _LORD_8_PLAIN:
            push(_LORD_8_PLAIN[h8])

    for nm in _aspectors_on_house(planets, asc_idx, 8):
        if nm not in {str(p.get("name")) for p in occ_8}:
            push(_wellness_issue_from_planet(nm))

    for p in planets:
        if int(p.get("house") or 0) == 1 and p.get("name") in _MALEFICS:
            push(_wellness_issue_from_planet(str(p.get("name") or "")))

    l1 = find_p(lord_1)
    if l1 and l1.get("sign") == DEBIL.get(lord_1):
        push("Core vitality needs steady routine")
    elif l1 and int(l1.get("house") or 0) in (6, 8, 12):
        push("Constitution linked to illness or chronic strain")

    return out[:6]


# ── HEALTH ────────────────────────────────────────────────────────────────
def compute_health_specifics(planets: List[dict], asc_idx: int,
                             current_dasha: Optional[dict] = None,
                             kundli: Optional[dict] = None,
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

        # ── Tridosha balance (Vata / Pitta / Kapha %) ─────────────────────
        tri = compute_tridosha_balance(planets, asc_idx, kundli)
        dosha_balance = tri["dosha_balance"]
        dosha_states = tri["dosha_states"]
        dominant = tri["dominant_dosha"]

        from vedic.health_organ_matrix_v1 import compute_organ_vulnerability_matrix
        organ_vulnerability_matrix = compute_organ_vulnerability_matrix(
            planets, asc_idx, issues, dosha_balance, kundli,
        )

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
            "dosha_states":       dosha_states,
            "dominant_dosha":     dominant,
            "primary_imbalance":  tri.get("primary_imbalance"),
            "tridosha_care":      tri.get("tridosha_care") or [],
            "tridosha_engine":    tri.get("engine"),
            "d9_immunity_verdict": tri.get("d9_immunity_verdict") or "",
            "kp_6th_csl":         tri.get("kp_6th_csl") or {},
            "kp_6th_csl_validation": tri.get("kp_6th_csl_validation") or tri.get("kp_6th_csl") or {},
            "dominant_clinical_trigger": tri.get("dominant_clinical_trigger") or "",
            "structural_reason":  tri.get("structural_reason") or "",
            "dietary_remedies":   tri.get("dietary_remedies") or [],
            "clinical_disease_promise": bool(tri.get("clinical_disease_promise")),
            "diagnostics":        tri.get("diagnostics") or {},
            "vulnerable_organs":  vuln_set[:10],
            "organ_vulnerability_matrix": organ_vulnerability_matrix,
            "wellness_tendencies": _build_wellness_sensitivities_from_chart(
                planets, asc_idx
            ),
        }
    except Exception as exc:
        return {"issues": [], "issues_total": 0, "error": str(exc)}


_PLANETS = (
    "sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu",
)


def _has_astro_jargon(text: str) -> bool:
    low = (text or "").lower()
    if any(s.lower() in low for s in SIGNS):
        return True
    if "house" in low or "lagna" in low or "dasha" in low or "transit" in low:
        return True
    if "karaka" in low or "debilitat" in low:
        return True
    for n in ("1st", "2nd", "3rd", "4th", "5th", "6th", "7th", "8th", "9th", "10th", "11th", "12th"):
        if n in low:
            return True
    return False


def _is_raw_watch_label(text: str) -> bool:
    """True if label should not be shown as-is on the wellness UI."""
    low = (text or "").lower().strip()
    if not low or _has_astro_jargon(text):
        return True
    if "karaka" in low or "debilitat" in low or " weak" in low:
        return True
    if any(p in low for p in _PLANETS):
        return True
    if "constitution" in low and ";" in low:
        return True
    return False


def _short_wellness_label(issue: Dict[str, Any]) -> str:
    """Plain body-area label — no sign/house jargon for UI."""
    blob = " ".join(
        [
            str(issue.get("area") or ""),
            str(issue.get("organs") or ""),
            str(issue.get("reason") or ""),
        ]
    ).lower()
    if any(k in blob for k in ("throat", "neck", "vocal")):
        return "throat & neck"
    if any(k in blob for k in ("digest", "intestin", "stomach", "abdomen", "gut")):
        return "digestion"
    if any(k in blob for k in ("sleep", "rest", "12th", "insomnia", "dream")):
        return "sleep"
    if any(k in blob for k in ("joint", "bone", "knee", "back", "stiff", "saturn")):
        return "joints"
    if any(k in blob for k in ("stress", "mind", "mood", "mental", "anxiety", "8th", "chronic")):
        return "stress & recovery"
    if any(k in blob for k in ("heart", "chest", "bp", "circulat")):
        return "vitality"
    if any(k in blob for k in ("nerve", "skin", "mercury")):
        return "nervous system"
    if any(k in blob for k in ("liver", "weight", "sugar", "jupiter")):
        return "metabolism"
    if any(k in blob for k in ("immune", "energy", "sun")):
        return "vitality"
    if "karaka" in blob or "debilitat" in blob:
        if "sun" in blob:
            return "vitality"
        if "moon" in blob:
            return "mind & sleep"
        if "mars" in blob:
            return "cooling & calm"
        if "mercury" in blob:
            return "nervous system"
        if "jupiter" in blob:
            return "metabolism"
        return "general wellness"
    if any(k in blob for k in ("inflam", "acidity", "blood pressure", "mars")):
        return "cooling & calm"
    if any(k in blob for k in ("allergy", "rahu", "sudden")):
        return "sensitivity"
    if any(k in blob for k in ("detox", "ketu", "parasit")):
        return "rest & reset"
    if "hidden" in blob or "12th" in blob:
        return "sleep"
    if "1st" in blob or "lagna" in blob:
        return "constitution"
    return "general wellness"


# One calm tip per watch label — never paste raw planet remedies on the card.
_LABEL_TIPS: Dict[str, str] = {
    "digestion": "Light, regular meals",
    "sleep": "Protect sleep — calmer evenings",
    "mind & sleep": "Protect sleep — calmer evenings",
    "joints": "Warmth for joints and comfort",
    "vitality": "Morning light and steady hydration",
    "cooling & calm": "Favor cooling, light meals",
    "stress & recovery": "Quiet time and gentle pace",
    "nervous system": "Calm routine and light meals",
    "metabolism": "Balanced meals — ease heavy sweets",
    "immunity": "Rest, hydration, steady routine",
    "sensitivity": "Clean space and gentle pace",
    "rest & reset": "Quiet time and early sleep",
    "constitution": "Steady meals and regular sleep",
    "throat & neck": "Warm sips and easy-to-digest food",
    "general wellness": "Keep your daily rhythm steady",
}


def _tip_for_watch_label(label: str) -> str:
    return _LABEL_TIPS.get((label or "").lower().strip(), "")


_CALM_TIP_BY_KEYWORD = (
    ("overheat", "Stay cool — ease heat and spice"),
    ("warm constitution", "Stay cool — ease heat and spice"),
    ("cooling food", "Favor cooling, light meals"),
    ("anger", "Stay calm — ease spice and heat"),
    ("detox", "Gentle cleansing habits"),
    ("meditation", "Quiet time each day"),
    ("grounding", "Grounding routine and tidy space"),
    ("hydration", "Steady hydration through the day"),
    ("emotional stability", "Steady hydration and calm routine"),
    ("warmth", "Warmth for joints and comfort"),
    ("light meal", "Light, regular meals"),
    ("calm routine", "Light, regular meals"),
    ("sleep", "Protect sleep — calmer evenings"),
    ("sugar", "Watch sweets and heavy foods"),
    ("hygiene", "Balanced routine and hygiene"),
    ("patience", "Warmth for joints — go slow"),
    ("sweetness", "Balanced meals — not too sweet"),
)


def _short_wellness_tip(remedy: str) -> str:
    """One calm line — no mantra / planet-template jargon."""
    tip = (remedy or "").strip()
    if not tip:
        return ""
    low_full = tip.lower()
    if tip.lower().startswith("needs "):
        tip = tip[6:].strip()
    for cut in ("—", "–", ";", "108", "mantra", "Om ", "Chalisa"):
        if cut in tip:
            tip = tip.split(cut)[0].strip()
    if "+" in tip:
        tip = tip.split("+")[0].strip()
    low = tip.lower()
    for key, calm in _CALM_TIP_BY_KEYWORD:
        if key in low or key in low_full:
            return calm
    if _has_astro_jargon(tip) or _has_astro_jargon(low_full):
        return ""
    if any(w in low for w in ("karaka", "debilitat", "constitution", "disease", "hospital")):
        return ""
    if low.startswith("needs ") or low.startswith("warm ") or low.startswith("watch "):
        return ""
    if len(tip) > 48:
        return ""
    return ""


_CALM_DAILY_DEFAULTS = [
    "Hydrate properly through the day",
    "Reduce late nights — protect sleep",
    "Cooling, light meals when possible",
    "Maintain gentle daily movement",
]


def _plain_organ_label(fragment: str) -> str:
    """Short wellness-friendly organ/zone label."""
    low = (fragment or "").lower().strip()
    if not low or _has_astro_jargon(fragment):
        return ""
    if "heart" in low or "bp" in low or "immunity" in low:
        return "Heart & vitality"
    if "mind" in low or "mood" in low or "sleep" in low:
        return "Mind & sleep"
    if "throat" in low or "neck" in low or "vocal" in low:
        return "Throat & neck"
    if "joint" in low or "bone" in low or "knee" in low:
        return "Joints & bones"
    if "stomach" in low or "digest" in low or "intestin" in low:
        return "Digestion"
    if "liver" in low or "sugar" in low or "weight" in low:
        return "Metabolism"
    if "skin" in low or "nerve" in low:
        return "Skin & nerves"
    if "reproductive" in low or "kidney" in low or "urinary" in low:
        return "Kidney & hydration"
    if "eye" in low:
        return "Eyes"
    if "blood" in low or "inflam" in low:
        return "Circulation"
    if len(fragment) > 36:
        return fragment[:33].rsplit(" ", 1)[0]
    return fragment.strip().title() if fragment.islower() else fragment.strip()


_RISK_RANK = {"High": 3, "Medium": 2, "Low": 1}


def _build_risky_organs(
    issues: Optional[List[Dict[str, Any]]],
    raw_organs: Optional[List[str]] = None,
) -> List[str]:
    """Up to 4 body zones — High-risk chart hits first, plain language."""
    out: List[str] = []
    seen: set = set()

    ranked = sorted(
        issues or [],
        key=lambda it: -_RISK_RANK.get(str(it.get("risk") or "Low"), 0),
    )
    for it in ranked:
        blob = str(it.get("organs") or "")
        for part in blob.replace(";", ",").split(","):
            label = _plain_organ_label(part.strip())
            if not label:
                continue
            key = label.lower()
            if key in seen:
                continue
            seen.add(key)
            out.append(label)
            if len(out) >= 4:
                return out

    for item in raw_organs or []:
        if not item:
            continue
        for part in str(item).replace(";", ",").split(","):
            label = _plain_organ_label(part.strip())
            if not label:
                continue
            key = label.lower()
            if key in seen:
                continue
            seen.add(key)
            out.append(label)
            if len(out) >= 4:
                return out
    return out


def _sanitize_sensitive_areas(
    raw: Optional[List[str]],
    issues: Optional[List[Dict[str, Any]]] = None,
) -> List[str]:
    """Up to 4 plain body zones — no sign/house or disease jargon."""
    out: List[str] = []
    seen: set = set()
    sources = list(raw or [])
    if not sources and issues:
        for it in issues:
            sources.append(str(it.get("organs") or ""))

    for item in sources:
        if not item:
            continue
        for part in item.replace(";", ",").split(","):
            label = _plain_organ_label(part.strip())
            if not label:
                continue
            key = label.lower()
            if key in seen:
                continue
            seen.add(key)
            out.append(label)
            if len(out) >= 4:
                return out
    return out


def _sanitize_daily_line(line: str) -> str:
    tip = _short_wellness_tip(line) or (line or "").strip()
    if not tip or _has_astro_jargon(tip):
        return ""
    if len(tip) > 56:
        tip = tip[:53].rsplit(" ", 1)[0]
    low = tip.lower()
    if any(w in low for w in ("mantra", "108", "doctor", "diagnos", "disease", "disorder")):
        return ""
    return tip


def _pick_health_focus_key(
    dominant_dosha: str,
    risk: str,
    issues: List[Dict[str, Any]],
    transit_notes: Optional[List[str]] = None,
) -> str:
    labels = [_short_wellness_label(it) for it in issues[:5]]
    notes = " ".join(transit_notes or []).lower()
    dom = (dominant_dosha or "").lower()

    if "sleep" in labels or "sleep" in notes:
        return "sleep"
    if dom == "pitta" or "inflamm" in notes or "mars" in notes:
        return "cooling"
    if dom == "vata" or "joint" in labels:
        return "grounding"
    if "stress" in labels or "mental" in " ".join(labels):
        return "mental_reset"
    if risk == "Low":
        return "steady"
    if "digest" in labels:
        return "hydration"
    return "movement"


def _issue_tendency_blob(it: Dict[str, Any]) -> str:
    """Merge organs, reason, area and planet karaka text for one issue."""
    area_low = str(it.get("area") or "").lower()
    parts = [
        str(it.get("organs") or ""),
        str(it.get("reason") or ""),
        area_low,
    ]
    for pname, (disease, _) in PLANET_DISEASE_TENDENCY.items():
        if pname.lower() in area_low or pname.lower() in str(it.get("reason") or "").lower():
            parts.append(disease)
    return " ".join(parts).lower()


def _phrases_for_blob(blob: str) -> List[str]:
    """Specific multi-area lines — not one-word labels like 'allergy sensitivity'."""
    b = blob.lower()
    found: List[str] = []

    def add(p: str) -> None:
        if p.lower() not in {x.lower() for x in found}:
            found.append(p)

    if "allergy" in b or "phobia" in b:
        zones: List[str] = []
        if "skin" in b:
            zones.append("skin")
        if any(k in b for k in ("digest", "stomach", "intestin", "abdomen", "gut")):
            zones.append("digestion")
        if "respir" in b or "lung" in b or "throat" in b or "neck" in b:
            zones.append("breathing")
        if "nerve" in b:
            zones.append("nerves")
        if zones:
            add(f"Allergies — {', '.join(zones)} may react more easily")
        else:
            add("Allergies — skin, food, air or digestion may react more easily")

    if "sudden" in b or "unexplained" in b:
        add("Sudden flare-ups — track food, sleep and environment")

    if "skin" in b and not any("allerg" in x.lower() for x in found):
        add("Skin sensitivity — mild products and hydration")

    if "nerve" in b and not any("nerve" in x.lower() for x in found):
        add("Nervous system — calm routine and light meals")

    if any(k in b for k in ("diabetes", "blood-sugar", "sugar")) and "jupiter" in b:
        add("Blood sugar — watch sweets and meal timing")
    elif any(k in b for k in ("diabetes", "blood-sugar")):
        add("Blood sugar sensitivity")

    if "bp" in b or ("heart" in b and "pressure" in b):
        add("Heart & blood pressure awareness")

    elif "heart" in b:
        add("Heart & circulation — avoid overheating")

    if any(k in b for k in ("inflamm", "acidity", "mars")):
        add("Inflammation — cooling foods and calm pace")

    if any(k in b for k in ("joint", "bone", "knee", "saturn")):
        add("Joints & bones — warmth and gentle movement")

    if "chronic" in b:
        add("Slow recovery — extra rest and patience")

    if any(k in b for k in ("sleep", "insomnia", "fatigue", "12th")):
        add("Sleep & mental rest — protect evening wind-down")

    if any(k in b for k in ("digest", "stomach", "intestin", "abdomen")) and not any(
        "digest" in x.lower() for x in found
    ):
        add("Digestion — lighter, regular meals")

    if any(k in b for k in ("liver", "weight")):
        add("Liver & metabolism — ease heavy or oily food")

    if any(k in b for k in ("kidney", "urinary", "reproductive")):
        add("Kidney & hydration — steady water intake")

    if any(k in b for k in ("parasit", "ketu", "detox")):
        add("Immunity & cleansing — rest and simple food")

    if any(k in b for k in ("hormone", "fluid", "mood", "mind", "mental", "moon")):
        if not any("sleep" in x.lower() or "mind" in x.lower() for x in found):
            add("Mind, mood & hormones — stability and hydration")

    if any(k in b for k in ("eye", "vision")):
        add("Eyes & vision — screen breaks and morning light")

    if "accident" in b or ("blood" in b and "mars" in b):
        add("Minor injuries — warm up before activity")

    if "immunity" in b and not any("immun" in x.lower() for x in found):
        add("Immunity support — sleep and whole foods")

    return found


def _extract_wellness_tendencies(
    issues: List[Dict[str, Any]],
    nature: Optional[List[str]] = None,
) -> List[str]:
    """Chart-based wellness sensitivities — specific body systems, not vague one-liners."""
    out: List[str] = []
    seen: set = set()

    def push(phrase: str) -> None:
        key = phrase.lower()
        if key in seen:
            return
        seen.add(key)
        out.append(phrase)

    for it in issues:
        blob = _issue_tendency_blob(it)
        for phrase in _phrases_for_blob(blob):
            push(phrase)
            if len(out) >= 6:
                return out[:6]

    if nature:
        nat_blob = " ".join(nature).lower()
        for phrase in _phrases_for_blob(nat_blob):
            push(phrase)
            if len(out) >= 6:
                break

    if not out and issues:
        combined = " ".join(_issue_tendency_blob(it) for it in issues)
        for phrase in _phrases_for_blob(combined):
            push(phrase)
            if len(out) >= 6:
                break

    return out[:6]


def _pick_phase_key(risk: str, recovery: str) -> str:
    rec = (recovery or "").lower()
    if risk == "Low":
        return "steady"
    if risk == "High" or "slow" in rec:
        return "recovery"
    return "moderate"


def build_health_basic_insights(
    score: int,
    risk: str,
    summary: str,
    deep: Dict[str, Any],
    *,
    nature: Optional[List[str]] = None,
    prevent: Optional[List[str]] = None,
    recovery: str = "",
    risk_periods: Optional[List[str]] = None,
    current_dasha: Optional[dict] = None,
) -> Dict[str, Any]:
    """Calm wellness dashboard — minimal fields, no anxiety triggers."""
    issues = deep.get("issues") or []
    dominant = str(deep.get("dominant_dosha") or "")

    watch_areas: List[Dict[str, str]] = []
    seen: set = set()
    for it in issues:
        label = _short_wellness_label(it)
        if label in seen:
            continue
        seen.add(label)
        tip = _tip_for_watch_label(label)
        entry: Dict[str, str] = {"label": label}
        if tip:
            entry["tip"] = tip
        watch_areas.append(entry)
        if len(watch_areas) >= 3:
            break

    if not watch_areas and (nature or []):
        for line in (nature or [])[:3]:
            lbl = "wellness"
            low = line.lower()
            if "sleep" in low or "stress" in low:
                lbl = "sleep" if "sleep" in low else "stress & calm"
            elif "joint" in low:
                lbl = "joints"
            elif "digest" in low or "meal" in low:
                lbl = "digestion"
            elif "inflam" in low:
                lbl = "cooling foods"
            tip = _tip_for_watch_label(lbl)
            row: Dict[str, str] = {"label": lbl}
            if tip:
                row["tip"] = tip
            watch_areas.append(row)
            if len(watch_areas) >= 3:
                break

    daily: List[str] = []
    for p in (prevent or []):
        short = _sanitize_daily_line(str(p))
        if short and short not in daily:
            daily.append(short)
        if len(daily) >= 4:
            break
    for fallback in _CALM_DAILY_DEFAULTS:
        if len(daily) >= 4:
            break
        if fallback not in daily:
            daily.append(fallback)
    daily = daily[:4]

    focus_key = _pick_health_focus_key(dominant, risk, issues)
    phase_key = _pick_phase_key(risk, recovery)
    sensitive_areas = _sanitize_sensitive_areas(
        deep.get("vulnerable_organs"),
        issues,
    )
    risky_organs = _build_risky_organs(issues, deep.get("vulnerable_organs"))
    if not risky_organs:
        risky_organs = list(sensitive_areas)
    wellness_tendencies = list(deep.get("wellness_tendencies") or [])
    if not wellness_tendencies:
        wellness_tendencies = _extract_wellness_tendencies(issues, nature)

    return {
        "score": score,
        "risk": risk,
        "summary": summary,
        "phase_key": phase_key,
        "health_focus_key": focus_key,
        "watch_areas": watch_areas,
        "sensitive_areas": sensitive_areas,
        "risky_organs": risky_organs,
        "organ_vulnerability_matrix": deep.get("organ_vulnerability_matrix") or [],
        "wellness_tendencies": wellness_tendencies,
        "dosha_balance": deep.get("dosha_balance") or {},
        "dosha_states": deep.get("dosha_states") or {},
        "dominant_dosha": dominant,
        "primary_imbalance": deep.get("primary_imbalance") or "",
        "tridosha_care": deep.get("tridosha_care") or [],
        "tridosha_engine": deep.get("tridosha_engine") or "",
        "d9_immunity_verdict": deep.get("d9_immunity_verdict") or "",
        "kp_6th_csl": deep.get("kp_6th_csl") or {},
        "kp_6th_csl_validation": deep.get("kp_6th_csl_validation") or deep.get("kp_6th_csl") or {},
        "dominant_clinical_trigger": deep.get("dominant_clinical_trigger") or "",
        "structural_reason": deep.get("structural_reason") or "",
        "dietary_remedies": deep.get("dietary_remedies") or [],
        "clinical_disease_promise": bool(deep.get("clinical_disease_promise")),
        "daily_care": daily,
    }


# ── CAREER ────────────────────────────────────────────────────────────────
def _compute_job_business_path(
    planets: List[dict],
    asc_idx: int,
    lord_10: str,
    kundli: Optional[dict] = None,
) -> Dict[str, Any]:
    """Multi-layer career inclination (D1 + D10, explainable). job_pct + business_pct = 100."""
    from vedic.career_inclination_engine import compute_career_inclination

    result = compute_career_inclination(planets, asc_idx, kundli)
    return {
        "job_pct": result["job_pct"],
        "business_pct": result["business_pct"],
        "dominant": result.get("dominant", "balanced"),
        "path_verdict": result.get("path_verdict", ""),
        "confidence": result.get("confidence"),
        "confidence_score": result.get("confidence_score"),
        "career_mode": result.get("career_mode"),
        "secondary_path": result.get("secondary_path"),
        "reasoning_summary": result.get("reasoning_summary", []),
        "psychology": result.get("psychology", {}),
        "d1_d10_alignment": result.get("d1_d10_alignment"),
        "job_subtypes": result.get("job_subtypes", []),
        "business_subtypes": result.get("business_subtypes", []),
        "inclination": result,
    }


def compute_career_specifics(planets: List[dict], asc_idx: int,
                             current_dasha: Optional[dict] = None,
                             kundli: Optional[dict] = None,
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

        occupants = [p["name"] for p in planets if p.get("house") == 10]

        from vedic.classical_career_fields import compute_classical_top_careers

        classical = compute_classical_top_careers(
            planets, asc_idx, kundli, top_n=5,
        )
        suitable_fields = classical.get("suitable_fields") or []
        classical_summary = classical.get("classical_summary") or ""

        path = _compute_job_business_path(planets, asc_idx, lord_10, kundli)
        job_pct = path["job_pct"]
        business_pct = path["business_pct"]
        biz_verdict = path["path_verdict"]
        inclination = path.get("inclination") or {}

        # Top careers = classical fields only (not 127 micro-niche catalog)
        income_paths = [
            {
                "label": str(f.get("field") or "").strip(),
                "strength": int(f.get("score") or 50),
            }
            for f in suitable_fields[:4]
            if str(f.get("field") or "").strip()
        ]
        income_sources: List[Dict[str, Any]] = []

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
            "amatyakaraka":       (
                {"planet": classical.get("amatyakaraka")}
                if classical.get("amatyakaraka") else None
            ),
            "suitable_fields":    suitable_fields,
            "classical_summary":  classical_summary,
            "business_vs_job":    biz_verdict,
            "job_pct":            job_pct,
            "business_pct":       business_pct,
            "path_verdict":       path["path_verdict"],
            "path_dominant":      path["dominant"],
            "career_inclination": inclination,
            "peak_growth_period": peak_period,
            "income_paths":       income_paths,
            "income_sources":     income_sources,
        }
    except Exception as exc:
        return {"error": str(exc)}


def _compute_chart_income_paths(
    planets: List[dict],
    asc_idx: int,
    kundli: Optional[dict],
    job_pct: int,
    business_pct: int,
) -> List[Dict[str, Any]]:
    """Score 127 micro-niches from chart; align with job vs business verdict."""
    from vedic.finance_income_niches import score_income_niches_from_chart

    sign_2 = SIGNS[(asc_idx + 1) % 12]
    sign_11 = SIGNS[(asc_idx + 10) % 12]
    sources = score_income_niches_from_chart(
        planets,
        asc_idx,
        lord_2=SIGN_LORD[sign_2],
        lord_11=SIGN_LORD[sign_11],
        exalt=EXALT,
        debil=DEBIL,
        own=OWN,
    )
    return _align_income_sources_with_career(
        sources,
        max(0, min(100, int(job_pct))),
        max(0, min(100, int(business_pct))),
    )


def _compact_career_field(raw: str) -> str:
    """Short user-facing label — labels are already compact from classical_career_fields."""
    s = (raw or "").strip()
    if not s:
        return s
    # Legacy long keys still map for old cached payloads
    legacy = {
        "IT / Software / Coding": "Tech / AI",
        "Business / Trading / Stocks": "Business / Trading",
        "Writing / Journalism / Editing": "Media / Communication",
        "Religious / Spiritual leadership": "Spiritual / Religious",
        "Software / Cyber / AI": "Tech / AI",
    }
    return legacy.get(s, s)


_PLANET_STRENGTHS = {
    "Sun": "leadership",
    "Moon": "emotional intelligence",
    "Mars": "drive & execution",
    "Mercury": "communication & analysis",
    "Jupiter": "wisdom & strategy",
    "Venus": "creativity & people skills",
    "Saturn": "discipline & endurance",
    "Rahu": "innovation & bold moves",
    "Ketu": "research mindset",
}

_PHASE_COPY = {
    "Excellent": "Strong growth phase — visibility and advancement are favored.",
    "Very Good": "Positive momentum — steady wins with focused effort.",
    "Good (slow but solid)": "Slow but stable growth phase. Skill-building is favored currently.",
    "Mixed (works in spurts)": "Mixed phase — bursts of progress; consistency matters.",
    "Average": "Consolidation phase — refine skills before the next push.",
    "Volatile (sudden moves)": "Unpredictable phase — avoid impulsive career jumps.",
    "Pause / introspection phase": "Reflection phase — depth over speed wins now.",
    "Neutral": "Balanced phase — plan carefully, avoid rushed switches.",
}


def build_career_basic_insights(
    score: int,
    trend: str,
    deep: Dict[str, Any],
    current_dasha: Optional[dict] = None,
    score_meta: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Structured Basic-tier payload — plain language, no heavy jargon."""
    cd = current_dasha or {}
    peak = deep.get("peak_growth_period") or {}
    fields = deep.get("suitable_fields") or []
    planet_power = deep.get("planet_power") or {}

    score_meta = score_meta or {}
    score_label = str(score_meta.get("score_label") or "")
    if not score_label:
        if score >= 70:
            score_label = "Strong Growth Potential"
        elif score >= 50:
            score_label = "Steady Progress Phase"
        else:
            score_label = "Build Skills First"
    score_context = str(
        score_meta.get("score_context")
        or "Based on your birth chart + current dasha & transits (updates over time)",
    )

    suitable = deep.get("suitable_fields") or []
    classical_summary = str(deep.get("classical_summary") or "").strip()

    top_matches: List[Dict[str, Any]] = []
    if suitable:
        top_matches = [
            {
                "label": _compact_career_field(str(f.get("field") or "")),
                "score": max(10, min(98, int(f.get("score") or 50))),
                "driver": str(f.get("driver") or "").strip(),
            }
            for f in suitable[:4]
            if f.get("field")
        ]
        # Field list is shown in top_matches / income_paths — no duplicate verdict line.
        verdict = ""
    else:
        top_matches = [
            {"label": _compact_career_field(f.get("field", "")), "score": f.get("score", 0)}
            for f in fields[:3]
            if f.get("field")
        ]
        if not top_matches:
            top_matches = [
                {"label": "General professional growth", "score": 70},
                {"label": "Skill-based roles", "score": 60},
                {"label": "People-facing work", "score": 55},
            ]
        themes = []
        for m in top_matches:
            t = m["label"].lower()
            if "tech" in t or "software" in t:
                themes.append("analytical")
            elif "business" in t or "trade" in t or "finance" in t:
                themes.append("business-oriented")
            elif "media" in t or "communication" in t or "marketing" in t:
                themes.append("communication")
            elif "law" in t or "education" in t:
                themes.append("advisory")
            elif "creative" in t:
                themes.append("creative")
            else:
                themes.append(m["label"].split("/")[0].strip().lower())
        themes = list(dict.fromkeys(themes))[:3]
        if len(themes) >= 2:
            verdict = (
                f"You are naturally suited for {', '.join(themes[:-1])} "
                f"and {themes[-1]} careers."
            )
        elif themes:
            verdict = f"You are naturally suited for {themes[0]} and growth-oriented careers."
        else:
            verdict = "Your chart favors versatile professional growth with the right timing."

    incl = deep.get("career_inclination") or {}
    job_pct = int(incl.get("job_pct") or deep.get("job_pct", 50))
    business_pct = 100 - job_pct
    path_verdict = str(
        incl.get("path_verdict")
        or deep.get("path_verdict")
        or deep.get("business_vs_job")
        or "Your chart shows a viable mix of job and business paths."
    )
    confidence = str(incl.get("confidence") or "Medium")
    career_mode = str(incl.get("career_mode") or "Hybrid Career")
    reasoning_summary = incl.get("reasoning_summary") or []

    income_paths = [
        {"label": m["label"], "strength": m["score"]}
        for m in top_matches[:4]
    ]

    rating = peak.get("rating", "Neutral")
    current_phase = _PHASE_COPY.get(rating, _PHASE_COPY["Neutral"])

    planet_power: Dict[str, int] = dict(deep.get("planet_power") or {})
    if not planet_power:
        tenth = deep.get("tenth_lord") or {}
        lord = tenth.get("planet")
        if lord:
            planet_power[lord] = int(tenth.get("strength_pct") or 50)
        occ_str = str((deep.get("tenth_house") or {}).get("occupants") or "")
        if occ_str and occ_str.lower() not in ("khaali", "empty", "—"):
            for nm in occ_str.split(","):
                nm = nm.strip()
                if nm:
                    planet_power[nm] = planet_power.get(nm, 0) + 22
        if deep.get("atmakaraka"):
            akp = deep["atmakaraka"].get("planet")
            if akp:
                planet_power[akp] = planet_power.get(akp, 0) + 18

    ranked_planets = sorted(planet_power.items(), key=lambda x: -x[1])
    strengths = []
    for pl, _ in ranked_planets:
        kw = _PLANET_STRENGTHS.get(pl)
        if kw and kw not in strengths:
            strengths.append(kw)
        if len(strengths) >= 2:
            break
    if not strengths:
        strengths = ["discipline", "communication"][:2]

    if trend == "Risk":
        main_risk = "Rushing major moves may backfire — deepen skills before switching."
    elif trend == "Average":
        main_risk = "Overthinking may delay execution — pick one direction and commit."
    else:
        main_risk = "Spreading focus too thin during growth windows can slow results."

    ends = str(peak.get("ends") or cd.get("endDate") or "")
    year_hint = ""
    for token in ends.replace(",", " ").split():
        if len(token) == 4 and token.isdigit() and token.startswith("20"):
            year_hint = token
            break
    if year_hint:
        timing_insight = f"Major growth window strengthens after mid-{year_hint}."
    elif peak.get("next_lord"):
        timing_insight = (
            f"Next uplift phase opens under {peak.get('next_lord')} mahadasha — plan ahead."
        )
    else:
        timing_insight = "Next 12–18 months favor consolidation before a stronger push."

    return {
        "score": score,
        "trend": trend,
        "score_label": score_label,
        "score_context": score_context,
        "verdict": verdict,
        "top_matches": top_matches,
        "income_paths": income_paths,
        "job_pct": job_pct,
        "business_pct": business_pct,
        "path_verdict": path_verdict,
        "confidence": confidence,
        "career_mode": career_mode,
        "reasoning_summary": reasoning_summary[:5],
        "dominant_path": incl.get("dominant") or deep.get("path_dominant"),
        "secondary_path": incl.get("secondary_path"),
        "commercial_score": incl.get("commercial_score"),
        "execution_score": incl.get("execution_score"),
        "freelance_score": incl.get("freelance_score"),
        "current_phase": current_phase,
        "strengths": strengths[:2],
        "main_risk": main_risk,
        "timing_insight": timing_insight,
    }


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

def _varga_asc_idx(chart: Dict[str, Any], fallback: int) -> int:
    asc = chart.get("ascendantSignIndex")
    if isinstance(asc, int):
        return int(asc) % 12
    asc_s = chart.get("ascendant") or ""
    if isinstance(asc_s, str) and asc_s in SIGNS:
        return SIGNS.index(asc_s)
    return fallback % 12


def _wealth_lord_of_house(asc_idx: int, house_num: int) -> str:
    return SIGN_LORD[SIGNS[(asc_idx + house_num - 1) % 12]]


def _wealth_planet_house(planets: List[dict], name: str) -> int:
    p = next((x for x in (planets or []) if x.get("name") == name), None)
    return int(p.get("house") or 0) if p else 0


def _has_lord_exchange(planets: List[dict], asc_idx: int, house_a: int, house_b: int) -> bool:
    """True when lords of house_a and house_b sit in each other's houses (parivartana)."""
    lord_a = _wealth_lord_of_house(asc_idx, house_a)
    lord_b = _wealth_lord_of_house(asc_idx, house_b)
    if lord_a == lord_b:
        return False
    return (
        _wealth_planet_house(planets, lord_a) == house_b
        and _wealth_planet_house(planets, lord_b) == house_a
    )


def _wealth_exchange_bonus(planets: List[dict], asc_idx: int) -> int:
    """Major dhana amplifiers — 9↔11 fortune–gains loop, 2↔11 accumulation–gains."""
    bonus = 0
    if _has_lord_exchange(planets, asc_idx, 9, 11):
        bonus += 10
    if _has_lord_exchange(planets, asc_idx, 2, 11):
        bonus += 7
    return min(15, bonus)


def _saturn_exalt_in_wealth_house(planets: List[dict], asc_idx: int) -> bool:
    from vedic.career_inclination_engine import ensure_planet_houses

    normed = ensure_planet_houses(list(planets or []), asc_idx)
    sat = next((p for p in normed if p.get("name") == "Saturn"), None)
    if not sat or (sat.get("sign") or "") != EXALT["Saturn"]:
        return False
    return int(sat.get("house") or 0) in (2, 11)


def _saturn_exalt_in_house(planets: List[dict], asc_idx: int, house_num: int) -> bool:
    from vedic.career_inclination_engine import ensure_planet_houses

    normed = ensure_planet_houses(list(planets or []), asc_idx)
    sat = next((p for p in normed if p.get("name") == "Saturn"), None)
    if not sat or (sat.get("sign") or "") != EXALT["Saturn"]:
        return False
    return int(sat.get("house") or 0) == house_num


def _wealth_saturn_compounding_bonus(kundli: Optional[dict], d1_asc_idx: int) -> int:
    """D9 exalted Saturn in 11th + D10 exalted Saturn in 2nd = long-term compounding empire pattern."""
    if not kundli or not isinstance(kundli, dict):
        return 0
    dv = kundli.get("divisionalCharts") or {}
    d9 = dv.get("D9") or {}
    d10 = dv.get("D10") or {}
    if not (isinstance(d9, dict) and d9.get("planets") and isinstance(d10, dict) and d10.get("planets")):
        return 0
    d9_asc = _varga_asc_idx(d9, d1_asc_idx)
    d10_asc = _varga_asc_idx(d10, d1_asc_idx)
    if (
        _saturn_exalt_in_house(d9.get("planets"), d9_asc, 11)
        and _saturn_exalt_in_house(d10.get("planets"), d10_asc, 2)
    ):
        return 8
    if (
        _saturn_exalt_in_wealth_house(d9.get("planets"), d9_asc)
        and _saturn_exalt_in_wealth_house(d10.get("planets"), d10_asc)
    ):
        return 4
    return 0


def _d1_rahu_eighth_bonus(planets: List[dict], asc_idx: int) -> int:
    """Rahu in 8th — hidden / unconventional / transformative wealth potential (modern charts)."""
    from vedic.career_inclination_engine import ensure_planet_houses

    normed = ensure_planet_houses(list(planets or []), asc_idx)
    rahu = next((p for p in normed if p.get("name") == "Rahu"), None)
    if rahu and int(rahu.get("house") or 0) == 8:
        return 5
    return 0


def _derive_wealth_styles(
    planets: List[dict],
    asc_idx: int,
    kundli: Optional[dict],
    pattern_signals: Dict[str, bool],
    lord_2: str,
    lord_5: str,
    lord_9: str,
    lord_11: str,
) -> List[str]:
    """Internal wealth-style tags (does not change category score)."""
    weights: Dict[str, int] = {}

    def bump(key: str, n: int = 1) -> None:
        weights[key] = weights.get(key, 0) + n

    def find_p(name: str) -> Optional[dict]:
        return next((p for p in planets if p.get("name") == name), None)

    rahu_h = _wealth_planet_house(planets, "Rahu")
    if rahu_h == 8:
        bump("speculative", 4)
        bump("assets", 2)
    elif rahu_h in (5, 11):
        bump("speculative", 2)

    if pattern_signals.get("exchange_911"):
        bump("assets", 2)
    if pattern_signals.get("exchange_211"):
        bump("business", 2)
        bump("compounding", 1)

    if pattern_signals.get("saturn_exalt_wealth"):
        bump("compounding", 4)
    sat = find_p("Saturn")
    if sat and int(sat.get("house") or 0) in (2, 11):
        bump("compounding", 2)

    merc = find_p("Mercury")
    if merc and int(merc.get("house") or 0) in (1, 2, 7, 10, 11):
        bump("business", 3)
    if merc and int(merc.get("house") or 0) in (3, 6, 10, 11):
        bump("internet", 2)

    if pattern_signals.get("rahu_11"):
        bump("internet", 4)
        bump("speculative", 1)

    jup = find_p("Jupiter")
    if jup and int(jup.get("house") or 0) in (8, 9):
        bump("inheritance", 3)
    if jup and int(jup.get("house") or 0) in (2, 5, 11):
        bump("inheritance", 1)

    ven = find_p("Venus")
    if ven and int(ven.get("house") or 0) in (2, 4, 11):
        bump("assets", 3)

    mars = find_p("Mars")
    if mars and int(mars.get("house") or 0) in (4, 10, 11):
        bump("assets", 2)
        bump("business", 1)

    if rahu_h in (9, 12):
        bump("foreign", 3)
    if kundli and isinstance(kundli, dict):
        for key in ("D9", "D10"):
            ch = (kundli.get("divisionalCharts") or {}).get(key) or {}
            if isinstance(ch, dict) and ch.get("planets"):
                aidx = _varga_asc_idx(ch, asc_idx)
                if _wealth_planet_house(ch.get("planets"), "Rahu") in (11, 12):
                    bump("foreign", 2)
                if _wealth_planet_house(ch.get("planets"), "Mercury") in (3, 6, 10, 11):
                    bump("internet", 2)

    if kundli and _wealth_saturn_compounding_bonus(kundli, asc_idx) >= 8:
        bump("compounding", 5)

    ranked = sorted(weights.items(), key=lambda x: -x[1])
    return [k for k, v in ranked if v >= 2][:4]


def _wealth_debil_softened(
    d1_planets: List[dict],
    asc_idx: int,
    kundli: Optional[dict],
) -> bool:
    """Reduce debility penalty when exchange or divisional wealth themes compensate."""
    if _wealth_exchange_bonus(d1_planets, asc_idx) >= 10:
        return True
    if not kundli or not isinstance(kundli, dict):
        return False
    dv = kundli.get("divisionalCharts") or {}
    sat_hits = 0
    for key in ("D9", "D10"):
        ch = dv.get(key) or {}
        if isinstance(ch, dict) and ch.get("planets"):
            aidx = _varga_asc_idx(ch, asc_idx)
            if _saturn_exalt_in_wealth_house(ch.get("planets"), aidx):
                sat_hits += 1
    return sat_hits >= 2


def _wealth_debil_penalty(lord: str, sign: str, softened: bool) -> int:
    if lord not in DEBIL or sign != DEBIL[lord]:
        return 0
    return -3 if softened else -5


def _wealth_modern_scaling_bonus(
    d1_planets: List[dict],
    d1_asc_idx: int,
    kundli: Optional[dict],
) -> int:
    """Rahu/Mercury upachaya scaling — digital, network, unconventional growth."""
    from vedic.career_inclination_engine import ensure_planet_houses

    bonus = 0
    d1n = ensure_planet_houses(list(d1_planets or []), d1_asc_idx)
    rahu = next((p for p in d1n if p.get("name") == "Rahu"), None)
    if rahu and int(rahu.get("house") or 0) == 11:
        bonus += 4
    merc = next((p for p in d1n if p.get("name") == "Mercury"), None)
    if merc and int(merc.get("house") or 0) in (3, 6, 10, 11):
        bonus += 3

    if kundli and isinstance(kundli, dict):
        d10 = (kundli.get("divisionalCharts") or {}).get("D10") or {}
        if isinstance(d10, dict) and d10.get("planets"):
            d10_asc = _varga_asc_idx(d10, d1_asc_idx)
            d10n = ensure_planet_houses(list(d10.get("planets")), d10_asc)
            r10 = next((p for p in d10n if p.get("name") == "Rahu"), None)
            if r10 and int(r10.get("house") or 0) == 11:
                bonus += 7
            m10 = next((p for p in d10n if p.get("name") == "Mercury"), None)
            if m10 and int(m10.get("house") or 0) in (3, 6, 10, 11):
                bonus += 3
    return min(8, bonus)


def _collect_wealth_pattern_signals(
    d1_planets: List[dict],
    d1_asc_idx: int,
    kundli: Optional[dict],
) -> Dict[str, bool]:
    """Repeating wealth themes across D1 / D9 / D10 for pattern amplifier."""
    sig: Dict[str, bool] = {
        "exchange_911": _has_lord_exchange(d1_planets, d1_asc_idx, 9, 11),
        "exchange_211": _has_lord_exchange(d1_planets, d1_asc_idx, 2, 11),
        "saturn_exalt_wealth": _saturn_exalt_in_wealth_house(d1_planets, d1_asc_idx),
        "rahu_11": _wealth_planet_house(d1_planets, "Rahu") == 11,
        "rahu_8": _wealth_planet_house(d1_planets, "Rahu") == 8,
    }
    if not kundli or not isinstance(kundli, dict):
        return sig
    dv = kundli.get("divisionalCharts") or {}
    for key in ("D9", "D10"):
        ch = dv.get(key) or {}
        if not isinstance(ch, dict) or not ch.get("planets"):
            continue
        aidx = _varga_asc_idx(ch, d1_asc_idx)
        pl = ch.get("planets")
        if _has_lord_exchange(pl, aidx, 9, 11):
            sig["exchange_911"] = True
        if _has_lord_exchange(pl, aidx, 2, 11):
            sig["exchange_211"] = True
        if _saturn_exalt_in_wealth_house(pl, aidx):
            sig["saturn_exalt_wealth"] = True
        if _wealth_planet_house(pl, "Rahu") == 11:
            sig["rahu_11"] = True
        if _wealth_planet_house(pl, "Rahu") == 8:
            sig["rahu_8"] = True
    return sig


def _wealth_pattern_amplifier(signals: Dict[str, bool]) -> int:
    """Bonus when the same wealth theme repeats across charts (synthesis layer)."""
    themes = sum(1 for v in signals.values() if v)
    if themes >= 4:
        return 7
    if themes >= 3:
        return 5
    if themes >= 2:
        return 2
    return 0


def _score_wealth_varga(
    varga_planets: List[dict],
    asc_idx: int,
    *,
    is_d10: bool = False,
) -> int:
    """D9/D10: 2nd & 11th lords + wealth houses — confirms D1 dhana potential."""
    from vedic.career_inclination_engine import ensure_planet_houses

    planets = ensure_planet_houses(list(varga_planets or []), asc_idx)
    if not planets:
        return 0

    delta = 0
    sign_2 = SIGNS[(asc_idx + 1) % 12]
    sign_11 = SIGNS[(asc_idx + 10) % 12]
    for ld in (SIGN_LORD[sign_2], SIGN_LORD[sign_11]):
        p = next((x for x in planets if x.get("name") == ld), None)
        if not p:
            continue
        h = int(p.get("house") or 0)
        if h in (1, 2, 4, 5, 9, 10, 11):
            delta += 5
        elif h in (6, 8, 12):
            delta -= 5
        sg = p.get("sign") or ""
        if ld in EXALT and sg == EXALT[ld]:
            delta += 4
        elif ld in DEBIL and sg == DEBIL[ld]:
            delta -= 4
        elif sg in OWN.get(ld, []):
            delta += 2

    benefics = {"Jupiter", "Venus", "Mercury", "Moon"}
    for p in planets:
        h = int(p.get("house") or 0)
        nm = p.get("name") or ""
        if h in (2, 11):
            if nm in benefics:
                delta += 4
            elif nm in ("Saturn", "Rahu", "Ketu"):
                delta -= 3
            elif nm == "Sun":
                delta += 2
            if is_d10 and h == 11 and nm == "Rahu":
                delta += 4
        if is_d10 and h == 10 and nm in ("Jupiter", "Venus", "Mercury", "Sun"):
            delta += 3
        if not is_d10 and h == 9 and nm in ("Jupiter", "Venus"):
            delta += 2

    return max(-8, min(18, delta))


def _vargottama_wealth_bonus(d1_planets: List[dict], varga_planets: List[dict]) -> int:
    """Same sign in D1 + D9 for wealth karakas = stronger dhana confirmation."""
    d1_by = {p["name"]: p for p in (d1_planets or []) if p.get("name")}
    bonus = 0
    for key in ("Jupiter", "Venus", "Moon", "Mercury"):
        d9p = d1_by.get(key)
        v9p = next((x for x in varga_planets if x.get("name") == key), None)
        if d9p and v9p and (d9p.get("sign") or "") == (v9p.get("sign") or ""):
            bonus += 3
    return min(9, bonus)


def _wealth_d9_d10_adjustment(
    d1_planets: List[dict],
    d1_asc_idx: int,
    kundli: Optional[dict],
) -> int:
    """Layer D9 (navamsa) + D10 (dashamsa) on top of D1 wealth karma — static birth only."""
    if not kundli or not isinstance(kundli, dict):
        return 0
    dv = kundli.get("divisionalCharts") or {}
    total = 0

    d9 = dv.get("D9") or {}
    d9_has = False
    if isinstance(d9, dict) and d9.get("planets"):
        d9_asc = _varga_asc_idx(d9, d1_asc_idx)
        total += _score_wealth_varga(d9.get("planets"), d9_asc, is_d10=False)
        total += _vargottama_wealth_bonus(d1_planets, d9.get("planets"))
        d9_has = True

    d10 = dv.get("D10") or {}
    d10_has = False
    if isinstance(d10, dict) and d10.get("planets"):
        d10_asc = _varga_asc_idx(d10, d1_asc_idx)
        total += _score_wealth_varga(d10.get("planets"), d10_asc, is_d10=True)
        d10_has = True

    total += _wealth_saturn_compounding_bonus(kundli, d1_asc_idx)

    return max(-10, min(24, total))


def _income_path_bucket(label: str, bucket: Optional[str] = None) -> str:
    """Group finance income labels for career-path alignment."""
    b = (bucket or "").strip().lower()
    if b in ("digital", "gig", "business"):
        return "business"
    if b == "employment":
        return "employment"
    if b == "enterprise":
        return "enterprise"
    if b in ("professional", "creative"):
        return b
    low = (label or "").lower()
    if any(k in low for k in (
        "business", "trading", " it ", "speculation", "crypto", "foreign",
        "e-commerce", "dropship", "youtuber", "vlogger", "influencer", "tiktok",
        "podcast", "blogger", "affiliate", "streamer", "esports", "saas", "developer",
        "designer", "digital", "online", "edtech", "marketplace",
    )):
        return "business"
    if any(k in low for k in (
        "government", "authority", "salary", "civil", "pension", "job", "officer",
        "engineer", "teacher", "professor", "doctor", "nurse", "banking", "defense",
        "police", "pilot", "lawyer", "accountant", "corporate", "software",
    )):
        return "employment"
    if any(k in low for k in (
        "real estate", "property", "construction", "contractor", "rental", "airbnb",
        "farming", "agriculture", "dairy", "land / plot",
    )):
        return "enterprise"
    if any(k in low for k in ("teaching", "advisory", "banking", "inheritance")):
        return "professional"
    if any(k in low for k in (
        "arts", "luxury", "beauty", "hospitality", "actor", "model", "singer", "dj",
        "dancer", "makeup", "fashion", "photographer", "comedian", "author", "voice",
    )):
        return "creative"
    if any(k in low for k in ("cab", "delivery", "freelance", "electrician", "plumber", "gig")):
        return "gig"
    return "neutral"


def _align_income_sources_with_career(
    sources: List[Dict[str, Any]],
    job_pct: int,
    business_pct: int,
) -> List[Dict[str, Any]]:
    """Reorder income paths so Finance matches Career job vs business verdict."""
    if not sources:
        return sources
    job_pct = max(0, min(100, int(job_pct)))
    business_pct = max(0, min(100, int(business_pct)))
    if abs(job_pct - business_pct) < 12:
        return sorted(sources, key=lambda x: -int(x.get("strength") or 0))[:6]

    aligned: List[Dict[str, Any]] = []
    for src in sources:
        label = str(src.get("source") or "")
        strength = int(src.get("strength") or 50)
        bucket = _income_path_bucket(label, str(src.get("bucket") or ""))

        if business_pct >= 55:
            if bucket in ("business", "digital", "gig"):
                strength += 8 + max(0, (business_pct - 50) // 4)
            elif bucket == "enterprise":
                strength += 5 + max(0, (business_pct - 50) // 6)
            elif bucket == "employment":
                strength -= 12 + max(0, (business_pct - 50) // 5)
            elif bucket == "professional" and business_pct >= 62:
                strength -= 5
        elif job_pct >= 55:
            if bucket == "employment":
                strength += 8 + max(0, (job_pct - 50) // 4)
            elif bucket == "professional":
                strength += 4 + max(0, (job_pct - 50) // 8)
            elif bucket == "business":
                strength -= 12 + max(0, (job_pct - 50) // 5)
            elif bucket == "enterprise" and job_pct >= 65:
                strength -= 6

        aligned.append({
            **src,
            "strength": max(12, min(95, strength)),
        })

    def _sort_key(item: Dict[str, Any]) -> tuple:
        strength = int(item.get("strength") or 0)
        bucket = _income_path_bucket(
            str(item.get("source") or ""),
            str(item.get("bucket") or ""),
        )
        bias = 0
        if business_pct > job_pct and bucket in ("business", "digital", "gig"):
            bias = 1
        elif job_pct > business_pct and bucket == "employment":
            bias = 1
        return (-strength, -bias)

    aligned.sort(key=_sort_key)
    return aligned[:6]


def _mb_weighted(items: List[tuple]) -> int:
    total = sum(float(w) for _, w in items) or 1.0
    return int(round(sum(float(v) * float(w) for v, w in items) / total))


def _mb_clamp(n: float, lo: int = 8, hi: int = 96) -> int:
    return max(lo, min(hi, int(round(n))))


def _mb_planet(planets: List[dict], name: str) -> Optional[dict]:
    return next((p for p in (planets or []) if p.get("name") == name), None)


def _mb_house_lord(asc_idx: int, house: int) -> str:
    return SIGN_LORD[SIGNS[(asc_idx + house - 1) % 12]]


def _mb_sign_idx(p: Optional[dict]) -> Optional[int]:
    if not p:
        return None
    sign = p.get("sign")
    if isinstance(sign, str) and sign in SIGNS:
        return SIGNS.index(sign)
    lon = p.get("longitude")
    if isinstance(lon, (int, float)):
        return int(float(lon) // 30) % 12
    sidx = p.get("signIndex")
    if isinstance(sidx, int):
        return sidx % 12
    return None


def _mb_dignity(planet: str, p: Optional[dict]) -> str:
    sign = p.get("sign") if p else ""
    if planet in EXALT and sign == EXALT[planet]:
        return "exalted"
    if planet in DEBIL and sign == DEBIL[planet]:
        return "debilitated"
    if sign in OWN.get(planet, []):
        return "own sign"
    if isinstance(sign, str) and sign in SIGN_LORD:
        sign_lord = SIGN_LORD[sign]
        friends = {
            "Sun": {"Moon", "Mars", "Jupiter"},
            "Moon": {"Sun", "Mercury"},
            "Mars": {"Sun", "Moon", "Jupiter"},
            "Mercury": {"Sun", "Venus"},
            "Jupiter": {"Sun", "Moon", "Mars"},
            "Venus": {"Mercury", "Saturn"},
            "Saturn": {"Mercury", "Venus"},
        }
        enemies = {
            "Sun": {"Saturn", "Venus"},
            "Moon": set(),
            "Mars": {"Mercury"},
            "Mercury": {"Moon"},
            "Jupiter": {"Mercury", "Venus"},
            "Venus": {"Sun", "Moon"},
            "Saturn": {"Sun", "Moon", "Mars"},
        }
        if sign_lord in friends.get(planet, set()):
            return "friendly sign"
        if sign_lord in enemies.get(planet, set()):
            return "enemy sign"
    return "neutral sign"


def _mb_norm_planet_score(planets: List[dict], asc_idx: int, planet: str) -> int:
    p = _mb_planet(planets, planet)
    if not p:
        return 50
    dig = _mb_dignity(planet, p)
    score = 0
    if dig == "exalted":
        score += 18
    elif dig == "own sign":
        score += 15
    elif dig == "friendly sign":
        score += 8
    elif dig == "enemy sign":
        score -= 8
    elif dig == "debilitated":
        score -= 18
    h = int(p.get("house") or 0)
    lorded = [house for house in range(1, 13) if _mb_house_lord(asc_idx, house) == planet]
    if any(hh in (1, 5, 9) for hh in lorded):
        score += 8
    if any(hh in (1, 4, 7, 10) for hh in lorded):
        score += 4
    if any(hh in (2, 11) for hh in lorded):
        score += 3
    if any(hh in (6, 8, 12) for hh in lorded):
        score -= 7
    if h in (1, 4, 7, 10):
        score += 10
    if h in (5, 9):
        score += 8
    if h in (6, 8, 12):
        score -= 8
    return _mb_clamp(50 + max(-35, min(35, score)) * 1.15)


def _mb_has_aspect(from_p: Optional[dict], target_sign_idx: Optional[int]) -> bool:
    if from_p is None or target_sign_idx is None:
        return False
    ps = _mb_sign_idx(from_p)
    if ps is None:
        return False
    d = (target_sign_idx - ps + 12) % 12
    nm = from_p.get("name")
    return (
        d == 6
        or (nm == "Mars" and d in (3, 7))
        or (nm == "Jupiter" and d in (4, 8))
        or (nm in ("Rahu", "Ketu") and d in (4, 8))
        or (nm == "Saturn" and d in (2, 9))
    )


def _mb_get_varga(kundli: Optional[dict], key: str) -> Optional[dict]:
    if not kundli or not isinstance(kundli, dict):
        return None
    dv = kundli.get("divisionalCharts") or {}
    chart = dv.get(key) or dv.get(key.lower())
    if isinstance(chart, dict) and chart.get("planets"):
        return chart
    return None


def _mb_varga_asc(chart: Optional[dict], fallback: int) -> int:
    return _varga_asc_idx(chart or {}, fallback)


def _mb_sarva_bindu(kundli: Optional[dict], asc_idx: int, house: int) -> Optional[float]:
    if not kundli or not isinstance(kundli, dict):
        return None
    av = kundli.get("ashtakavarga") or {}
    target = (asc_idx + house - 1) % 12
    for key in ("SAV", "sav", "Sarva", "sarva", "Sarvashtakavarga", "sarvashtakavarga", "total"):
        arr = av.get(key)
        if isinstance(arr, list) and len(arr) >= 12:
            try:
                return float(arr[target])
            except Exception:
                return None
    arrays = [arr for arr in av.values() if isinstance(arr, list) and len(arr) >= 12]
    if arrays:
        return sum(float(arr[target] or 0) for arr in arrays)
    return None


def _mb_dhan_yoga_bonus(yoga: dict) -> int:
    link = str(yoga.get("link") or "")
    houses = tuple(sorted(int(h) for h in (yoga.get("houses") or []) if isinstance(h, int)))
    if link == "parivartana":
        return 12 if houses in ((2, 11), (9, 11)) else 10
    if link == "conjunction":
        return 10 if houses == (2, 11) else 8
    if link == "mutual_aspect":
        return 6
    if link == "karaka":
        return 6
    return 5


def _mb_raj_yoga_bonus(yoga: dict) -> int:
    link = str(yoga.get("link") or "")
    name = str(yoga.get("name") or "")
    houses = {int(h) for h in (yoga.get("houses") or []) if isinstance(h, int)}
    dharma_karma = 9 in houses and 10 in houses
    if link == "parivartana":
        return 10 if dharma_karma else 8
    if link == "conjunction":
        return 8 if dharma_karma else 6
    if link == "mutual_aspect":
        return 6 if dharma_karma else 5
    if name == "Yogakaraka Yoga":
        return 8
    if name == "Gaja Kesari Yoga":
        return 5
    if name == "Trikona Lord in 10th":
        return 5
    if name == "Kendra Lord in Trikona":
        return 4
    if name == "Vipreet Raj Yoga":
        return 6
    return 5


def _mb_d1_wealth_yoga_score(planets: List[dict], asc_idx: int) -> int:
    from vedic.dhan_yoga_engine_v1 import scan_dhan_yogas
    from vedic.raj_yoga_engine_v1 import scan_raj_yogas

    raw = 50.0
    linked: set = set()

    for y in scan_dhan_yogas(planets, asc_idx):
        houses = tuple(sorted(int(h) for h in (y.get("houses") or []) if isinstance(h, int)))
        if len(houses) == 2:
            key = f"dhan-{houses[0]}-{houses[1]}"
            if key in linked:
                continue
            linked.add(key)
        raw += _mb_dhan_yoga_bonus(y)

    for y in scan_raj_yogas(planets, asc_idx):
        houses = tuple(sorted(int(h) for h in (y.get("houses") or []) if isinstance(h, int)))
        if len(houses) == 2:
            key = f"raj-{houses[0]}-{houses[1]}"
            if key in linked:
                continue
            linked.add(key)
        raw += _mb_raj_yoga_bonus(y)

    lord_2 = _mb_house_lord(asc_idx, 2)
    lord_11 = _mb_house_lord(asc_idx, 11)
    p2, p11 = _mb_planet(planets, lord_2), _mb_planet(planets, lord_11)
    p2s, p11s = _mb_sign_idx(p2), _mb_sign_idx(p11)

    for house in (5, 9):
        lord = _mb_house_lord(asc_idx, house)
        p = _mb_planet(planets, lord)
        if not p:
            continue
        ph = int(p.get("house") or 0)
        if ph in (2, 11):
            raw += 7
        pair2 = tuple(sorted((2, house)))
        pair11 = tuple(sorted((house, 11)))
        if _mb_has_aspect(p, p2s) and f"dhan-{pair2[0]}-{pair2[1]}" not in linked:
            raw += 3
        if _mb_has_aspect(p, p11s) and f"dhan-{pair11[0]}-{pair11[1]}" not in linked:
            raw += 3

    if "dhan-2-11" not in linked:
        if _mb_has_aspect(p2, p11s):
            raw += 4
        if _mb_has_aspect(p11, p2s):
            raw += 4

    return _mb_clamp(int(round(raw)))


def _mb_d1_wealth_score(planets: List[dict], asc_idx: int) -> int:
    lords = [_mb_house_lord(asc_idx, h) for h in (2, 11, 10, 9)]
    core = []
    for house, lord in zip((2, 11, 10, 9), lords):
        p = _mb_planet(planets, lord)
        score = _mb_norm_planet_score(planets, asc_idx, lord)
        if p and int(p.get("house") or 0) in (6, 8, 12):
            score -= 12 if house in (2, 11) else 7
        core.append(_mb_clamp(score))
    core_score = _mb_weighted([(core[0], .30), (core[1], .30), (core[2], .25), (core[3], .15)])

    yoga_score = _mb_d1_wealth_yoga_score(planets, asc_idx)

    benefics = {"Jupiter", "Venus", "Mercury", "Moon"}
    malefics = {"Saturn", "Mars", "Rahu", "Ketu", "Sun"}
    occupant = 50
    for p in planets or []:
        h, nm = int(p.get("house") or 0), str(p.get("name") or "")
        if h == 2:
            if nm in benefics:
                occupant += 7
            if nm in malefics:
                occupant -= 4 if nm == "Sun" else 8
        elif h in (10, 11):
            if nm in malefics:
                occupant += 7
            if nm in benefics:
                occupant += 4
        elif h == 9:
            if nm in benefics:
                occupant += 5
            if nm in malefics:
                occupant -= 2
    occupant_score = _mb_clamp(occupant)

    aspect = 50
    for house in (2, 9, 10, 11):
        target = (asc_idx + house - 1) % 12
        house_lord = _mb_house_lord(asc_idx, house)
        for p in planets or []:
            nm = str(p.get("name") or "")
            if _mb_has_aspect(p, target):
                if nm in benefics:
                    aspect += 5
                elif nm in malefics:
                    aspect -= 1 if house_lord in {"Venus", "Saturn"} and nm in ("Venus", "Saturn") else 4
        lord_p = _mb_planet(planets, house_lord)
        lord_sign = _mb_sign_idx(lord_p)
        for p in planets or []:
            nm = str(p.get("name") or "")
            if nm == house_lord:
                continue
            if _mb_has_aspect(p, lord_sign):
                aspect += 4 if nm in benefics else -4 if nm in malefics else 0
    aspect_score = _mb_clamp(aspect)

    karaka_score = _mb_weighted([
        (_mb_norm_planet_score(planets, asc_idx, "Jupiter"), .55),
        (_mb_norm_planet_score(planets, asc_idx, "Venus"), .45),
    ])
    filter_score = 50
    for house, lord in zip((2, 11, 10, 9), lords):
        p = _mb_planet(planets, lord)
        if p and int(p.get("house") or 0) in (6, 8, 12) and house in (2, 11):
            filter_score -= 10
        if p and lord in DEBIL and p.get("sign") == DEBIL[lord]:
            filter_score -= 8
    filter_score = _mb_clamp(filter_score)

    return _mb_weighted([
        (core_score, .35), (yoga_score, .20), (occupant_score, .15),
        (aspect_score, .12), (karaka_score, .10), (filter_score, .08),
    ])


def _mb_d2_score(planets: List[dict], asc_idx: int, kundli: Optional[dict], wealth_base: int) -> int:
    d2 = _mb_get_varga(kundli, "D2")
    if not d2:
        return _mb_weighted([
            (wealth_base, .45),
            (_mb_norm_planet_score(planets, asc_idx, "Jupiter"), .30),
            (_mb_norm_planet_score(planets, asc_idx, "Venus"), .25),
        ])
    d2_planets = d2.get("planets") or []
    d2_asc = _mb_varga_asc(d2, asc_idx)
    def hora(name: str) -> str:
        p = _mb_planet(d2_planets, name)
        s = _mb_sign_idx(p)
        return "moon" if s == 3 else "sun" if s == 4 else "other"
    moon = sum(1 for p in d2_planets if hora(str(p.get("name"))) == "moon")
    sun = sum(1 for p in d2_planets if hora(str(p.get("name"))) == "sun")
    keys = [_mb_house_lord(asc_idx, 1), _mb_house_lord(asc_idx, 2), _mb_house_lord(asc_idx, 11), "Jupiter"]
    key_moon = sum(1 for k in keys if hora(k) == "moon")
    key_sun = sum(1 for k in keys if hora(k) == "sun")
    dominance = _mb_clamp(48 + (moon - sun) * 2.5 + key_moon * 7 - key_sun * 2)
    lagna = 62 if d2_asc == 3 else 56 if d2_asc == 4 else 50
    for p in d2_planets:
        if int(p.get("house") or 0) == 1:
            nm = p.get("name")
            lagna += 7 if nm in {"Jupiter", "Venus", "Mercury", "Moon"} else 4 if nm in {"Sun", "Mars", "Rahu"} and d2_asc == 4 else -3 if nm in {"Saturn", "Ketu"} else 1
    vault = 50
    for p in d2_planets:
        if int(p.get("house") or 0) == 2:
            nm = p.get("name")
            vault += 10 if nm in {"Jupiter", "Venus", "Mercury"} else -10 if nm in {"Rahu", "Ketu", "Mars"} else -3 if nm == "Saturn" else 4 if nm == "Moon" else 1 if nm == "Sun" else 0
    karaka = _mb_weighted([(82 if hora("Jupiter") == "moon" else 58 if hora("Jupiter") == "sun" else 50, .55),
                           (78 if hora("Venus") == "moon" else 60 if hora("Venus") == "sun" else 50, .45)])
    lord2, lord11 = _mb_house_lord(asc_idx, 2), _mb_house_lord(asc_idx, 11)
    p2, p11 = _mb_planet(d2_planets, lord2), _mb_planet(d2_planets, lord11)
    cross = 50
    if p2 and int(p2.get("house") or 0) == 2:
        cross += 8
    if p11 and int(p11.get("house") or 0) == 2:
        cross += 14
    if hora(lord2) == "moon":
        cross += 5
    if hora(lord11) == "moon":
        cross += 5
    if p2 and int(p2.get("house") or 0) in (6, 8, 12):
        cross -= 6
    if p11 and int(p11.get("house") or 0) in (6, 8, 12):
        cross -= 6
    return _mb_weighted([(_mb_clamp(dominance), .30), (_mb_clamp(lagna), .18), (_mb_clamp(vault), .22), (karaka, .16), (_mb_clamp(cross), .14)])


def _mb_d10_placement_points(house: int) -> int:
    if house in (1, 2, 4, 5, 9, 10, 11):
        return 3
    if house in (6, 8, 12):
        return -2
    return 0


def _mb_d10_pair_bonus(link: str) -> int:
    if link == "parivartana":
        return 6
    if link == "conjunction":
        return 5
    return 4


def _mb_d10_score(planets: List[dict], asc_idx: int, kundli: Optional[dict], fallback: int) -> int:
    d10 = _mb_get_varga(kundli, "D10")
    if not d10:
        return _mb_clamp(fallback)
    from vedic.career_inclination_engine import ensure_planet_houses

    d10_asc = _mb_varga_asc(d10, asc_idx)
    d10_pl = ensure_planet_houses(list(d10.get("planets") or []), d10_asc)
    d1_pl = ensure_planet_houses(list(planets or []), asc_idx)
    lord10, lord11 = _mb_house_lord(d10_asc, 10), _mb_house_lord(d10_asc, 11)
    p10, p11 = _mb_planet(d10_pl, lord10), _mb_planet(d10_pl, lord11)

    def dig_pts(lord: str, p: Optional[dict]) -> int:
        d = _mb_dignity(lord, p)
        return 5 if d in ("exalted", "own sign") else 3 if d == "friendly sign" else -2 if d == "enemy sign" else -3 if d == "debilitated" else 0

    points = dig_pts(lord10, p10) + dig_pts(lord11, p11)
    points += _mb_d10_placement_points(int(p10.get("house") or 0) if p10 else 0)
    points += _mb_d10_placement_points(int(p11.get("house") or 0) if p11 else 0)

    link910 = _mb_wealth_lord_pair_link(d10_pl, d10_asc, 9, 10)
    if link910:
        points += _mb_d10_pair_bonus(link910)
        if _mb_wealth_lord_pair_link(d1_pl, asc_idx, 9, 10):
            points += 3

    link1011 = _mb_wealth_lord_pair_link(d10_pl, d10_asc, 10, 11)
    if link1011:
        points += _mb_d10_pair_bonus(link1011)
        if _mb_wealth_lord_pair_link(d1_pl, asc_idx, 10, 11):
            points += 3
    else:
        p10s, p11s = _mb_sign_idx(p10), _mb_sign_idx(p11)
        if p10 and p11 and (_mb_has_aspect(p10, p11s) or _mb_has_aspect(p11, p10s)):
            points += 3

    if p11 and int(p11.get("house") or 0) == 2:
        points += 4

    companion = 0
    for lord, p in ((lord10, p10), (lord11, p11)):
        if not p:
            continue
        for c in d10_pl:
            if c.get("name") != lord and c.get("house") == p.get("house"):
                if _mb_dignity(str(c.get("name")), c) in ("exalted", "own sign"):
                    companion += 3
    points += min(6, companion)

    upachaya = 0
    for p in d10_pl:
        if int(p.get("house") or 0) in (10, 11) and p.get("name") in {"Jupiter", "Venus"}:
            upachaya += 1
    points += min(8, upachaya)

    bridge = 0
    for h in (2, 9, 10, 11):
        lord = _mb_house_lord(asc_idx, h)
        p = _mb_planet(d10_pl, lord)
        bridge += _mb_d10_placement_points(int(p.get("house") or 0) if p else 0)
    points += bridge
    return _mb_clamp(50 + points * 1.5)


def _mb_mutual_aspect(planets: List[dict], lord_a: str, lord_b: str) -> bool:
    pa, pb = _mb_planet(planets, lord_a), _mb_planet(planets, lord_b)
    sa, sb = _mb_sign_idx(pa), _mb_sign_idx(pb)
    if not pa or not pb or sa is None or sb is None:
        return False
    return _mb_has_aspect(pa, sb) and _mb_has_aspect(pb, sa)


def _mb_wealth_lord_pair_link(
    chart_planets: List[dict],
    d1_asc_idx: int,
    house_a: int,
    house_b: int,
) -> Optional[str]:
    lord_a = _mb_house_lord(d1_asc_idx, house_a)
    lord_b = _mb_house_lord(d1_asc_idx, house_b)
    if lord_a == lord_b:
        return None
    pa, pb = _mb_planet(chart_planets, lord_a), _mb_planet(chart_planets, lord_b)
    ha = int(pa.get("house") or 0) if pa else 0
    hb = int(pb.get("house") or 0) if pb else 0
    if ha == house_b and hb == house_a:
        return "parivartana"
    if ha and ha == hb:
        return "conjunction"
    if _mb_mutual_aspect(chart_planets, lord_a, lord_b):
        return "mutual_aspect"
    return None


def _mb_d9_wealth_pair_bonus(house_a: int, house_b: int, link: str) -> float:
    key = tuple(sorted((house_a, house_b)))
    if link == "parivartana":
        return 4.0 if key in ((2, 11), (9, 11)) else 3.0
    if link == "conjunction":
        return 3.5 if key == (2, 11) else 2.5
    return 2.0


def _mb_d9_modifier(planets: List[dict], asc_idx: int, kundli: Optional[dict]) -> float:
    d9 = _mb_get_varga(kundli, "D9")
    if not d9:
        return 0.0
    from vedic.career_inclination_engine import ensure_planet_houses

    d9_asc = _mb_varga_asc(d9, asc_idx)
    d9_pl = ensure_planet_houses(list(d9.get("planets") or []), d9_asc)
    d1_pl = ensure_planet_houses(list(planets or []), asc_idx)
    mod = 0.0
    wealth_houses = (2, 5, 9, 11)
    wealth_pairs = ((2, 5), (2, 9), (2, 11), (5, 9), (5, 11), (9, 11))

    for h in wealth_houses:
        lord = _mb_house_lord(asc_idx, h)
        p = _mb_planet(d9_pl, lord)
        d = _mb_dignity(lord, p)
        if d == "exalted":
            mod += 2.0
        elif d == "own sign":
            mod += 1.5
        elif d == "debilitated":
            mod -= 2.0
        ph = int(p.get("house") or 0) if p else 0
        if ph in (2, 5, 9, 11):
            mod += 2.0
        elif ph in (1, 4, 7, 10):
            mod += 1.0
        elif ph in (6, 8, 12):
            mod -= 2.0

    linked: set = set()
    for ha, hb in wealth_pairs:
        link = _mb_wealth_lord_pair_link(d9_pl, asc_idx, ha, hb)
        if not link:
            continue
        key = tuple(sorted((ha, hb)))
        if key in linked:
            continue
        linked.add(key)
        mod += _mb_d9_wealth_pair_bonus(ha, hb, link)
        if _mb_wealth_lord_pair_link(d1_pl, asc_idx, ha, hb):
            mod += 3.0

    vargottama = 0.0
    for name in ("Jupiter", "Venus", "Moon", "Mercury"):
        p1, p9 = _mb_planet(d1_pl, name), _mb_planet(d9_pl, name)
        if p1 and p9 and (p1.get("sign") or "") == (p9.get("sign") or ""):
            vargottama += 1.5
    mod += min(4.5, vargottama)

    return max(-8.0, min(12.0, round(mod, 1)))


def _mb_ashtak_modifier(kundli: Optional[dict], asc_idx: int) -> int:
    total = 0
    for h in (2, 11):
        b = _mb_sarva_bindu(kundli, asc_idx, h)
        if b is None:
            continue
        total += 3 if b > 32 else -3 if b < 24 else 0
    return max(-3, min(3, total))


def _mb_wealth_builder_residual_leakage(planets: List[dict]) -> int:
    """Ketu 2H / Rahu 8H only — matches Personalization Wealth Builder leakage."""
    penalty = 0
    if any(p.get("name") == "Ketu" and int(p.get("house") or 0) == 2 for p in planets or []):
        penalty -= 1
    if any(p.get("name") == "Rahu" and int(p.get("house") or 0) == 8 for p in planets or []):
        penalty -= 1
    return penalty


def _mb_global_leakage(planets: List[dict], asc_idx: int) -> int:
    penalty = 0
    for h in (2, 11):
        lord = _mb_house_lord(asc_idx, h)
        p = _mb_planet(planets, lord)
        if p and int(p.get("house") or 0) in (6, 8, 12):
            lorded = [hh for hh in range(1, 13) if _mb_house_lord(asc_idx, hh) == lord]
            if not any(hh in (6, 8, 12) for hh in lorded):
                penalty -= 5
        # Backend finance data usually lacks exact combustion degrees; skip exact -3 unless longitudes exist.
        sun = _mb_planet(planets, "Sun")
        if p and sun and lord != "Sun" and isinstance(p.get("longitude"), (int, float)) and isinstance(sun.get("longitude"), (int, float)):
            diff = min(abs(float(p["longitude"]) - float(sun["longitude"])), 360 - abs(float(p["longitude"]) - float(sun["longitude"])))
            if diff < 8:
                penalty -= 3
    if any(p.get("name") == "Ketu" and int(p.get("house") or 0) == 2 for p in planets or []):
        penalty -= 1
    if any(p.get("name") == "Rahu" and int(p.get("house") or 0) == 8 for p in planets or []):
        penalty -= 1
    return penalty


def _mb_modern_modifier(planets: List[dict], asc_idx: int, kundli: Optional[dict]) -> float:
    mod = 0.0
    rahu = _mb_planet(planets, "Rahu")
    merc = _mb_planet(planets, "Mercury")
    sat = _mb_planet(planets, "Saturn")
    if rahu and int(rahu.get("house") or 0) in (3, 6, 10, 11):
        mod += 2
    elif rahu and int(rahu.get("house") or 0) == 8:
        mod += 1
    if merc and int(merc.get("house") or 0) in (3, 6, 10, 11, 12):
        mod += 1.5 if int(merc.get("house") or 0) == 12 else 2
    if sat and int(sat.get("house") or 0) in (3, 6, 10, 11):
        mod += 1.5
    elif _mb_dignity("Saturn", sat) == "debilitated":
        mod += 1
    d10 = _mb_get_varga(kundli, "D10")
    if d10:
        pl = d10.get("planets") or []
        r10 = _mb_planet(pl, "Rahu")
        s10 = _mb_planet(pl, "Saturn")
        m10 = _mb_planet(pl, "Mercury")
        if r10 and int(r10.get("house") or 0) in (10, 11):
            mod += 2
        if (r10 and int(r10.get("house") or 0) == 11) or (s10 and int(s10.get("house") or 0) == 11):
            mod += 2
        if m10 and int(m10.get("house") or 0) in (3, 6, 10, 11, 12):
            mod += 1
    return max(0.0, min(8.0, mod))


def _mb_trajectory_modifier(d1: int, d2: int, d10: int, modern: float) -> float:
    early_friction = max(0.0, 60.0 - float(d1)) * 0.12
    future_scaling = max(0.0, float(d2) - 60.0) * 0.10 + max(0.0, float(d10) - 60.0) * 0.12 + float(modern) * 0.45
    return max(-4.0, min(6.0, future_scaling - early_friction))


def _mb_dasha_planet_multiplier(planets: List[dict], asc_idx: int, kundli: Optional[dict], planet: str) -> float:
    if not planet:
        return 1.0
    p = _mb_planet(planets, planet)
    mult = 1.0
    if p and int(p.get("house") or 0) in (3, 6, 10, 11):
        mult += 0.15
    d1_dig = _mb_dignity(planet, p)
    d9_strong = False
    d9 = _mb_get_varga(kundli, "D9")
    if d9:
        d9p = _mb_planet(d9.get("planets") or [], planet)
        d9_dig = _mb_dignity(planet, d9p)
        d9_strong = d9_dig in ("exalted", "own sign")
    if d1_dig in ("exalted", "own sign") or d9_strong:
        mult += 0.10
    d10 = _mb_get_varga(kundli, "D10")
    if d10:
        d10p = _mb_planet(d10.get("planets") or [], planet)
        if d10p and int(d10p.get("house") or 0) in (2, 10, 11):
            mult += 0.10
    d2 = _mb_get_varga(kundli, "D2")
    if d2:
        d2p = _mb_planet(d2.get("planets") or [], planet)
        s = _mb_sign_idx(d2p)
        wealth_lords = {_mb_house_lord(asc_idx, 2), _mb_house_lord(asc_idx, 9), _mb_house_lord(asc_idx, 11)}
        if s == 3 and planet in wealth_lords:
            mult += 0.05
    has_support = d9_strong or _mb_modern_modifier(planets, asc_idx, kundli) >= 3
    if p and int(p.get("house") or 0) in (8, 12) and not has_support:
        mult -= 0.15
    if d1_dig == "debilitated":
        # Backend mirror lacks full neecha-bhanga evaluator here, so only apply a mild penalty.
        mult -= 0.10
    return max(0.80, min(1.25, mult))


def _mb_operational_score(base_score: int, planets: List[dict], asc_idx: int, kundli: Optional[dict], current_dasha: Optional[dict]) -> int:
    cd = current_dasha or {}
    md = str(cd.get("maha") or "")
    ad = str(cd.get("antar") or "")
    md_mult = _mb_dasha_planet_multiplier(planets, asc_idx, kundli, md)
    ad_mult = _mb_dasha_planet_multiplier(planets, asc_idx, kundli, ad)
    multiplier = max(0.80, min(1.25, md_mult * 0.60 + ad_mult * 0.40))
    return max(8, min(96, int(round(base_score * multiplier))))


def _money_builder_wealth_score(planets: List[dict], asc_idx: int, kundli: Optional[dict], fallback_career_score: int = 50) -> int:
    """Same architecture as Personalization Wealth Builder Kundli (50/25/25 + D9/SAV/leakage)."""
    d1 = _mb_d1_wealth_score(planets, asc_idx)
    wealth_base = _mb_clamp(d1)
    d2 = _mb_d2_score(planets, asc_idx, kundli, wealth_base)
    d10 = _mb_d10_score(planets, asc_idx, kundli, fallback_career_score)
    score = d1 * 0.50 + d2 * 0.25 + d10 * 0.25
    score += _mb_d9_modifier(planets, asc_idx, kundli)
    score += float(_mb_ashtak_modifier(kundli, asc_idx))
    score += float(_mb_wealth_builder_residual_leakage(planets))
    score = max(8.0, min(96.0, round(score * 4) / 4))
    return int(round(score))


def compute_finance_specifics(
    planets: List[dict],
    asc_idx: int,
    current_dasha: Optional[dict] = None,
    kundli: Optional[dict] = None,
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

        pattern_signals = _collect_wealth_pattern_signals(planets, asc_idx, kundli)

        # ── Wealth category now uses the same Money Builder architecture as Kundli Category:
        # D1 blueprint + D2 vault + D10 income engine + wealth planets + dhan yoga,
        # then D9/SAV validators and final leakage deductions.
        wealth_karma_score = _money_builder_wealth_score(
            planets,
            asc_idx,
            kundli,
            fallback_career_score=50,
        )
        operational_score = _mb_operational_score(
            wealth_karma_score,
            planets,
            asc_idx,
            kundli,
            current_dasha,
        )

        # ── Dhana yogas are still returned for display/styles, but no longer add
        # extra points here because Money Builder already includes a 5% yoga layer.
        yogas = _has_dhana_yoga_for_chart(planets, asc_idx)
        yogas_count = len(yogas)
        wealth_category = _classify_wealth_category(wealth_karma_score)
        wealth_styles = _derive_wealth_styles(
            planets, asc_idx, kundli, pattern_signals,
            lord_2, lord_5, lord_9, lord_11,
        )
        money_habits = _derive_static_money_habits(
            planets, asc_idx, wealth_category, pattern_signals,
        )

        # ── Peak wealth period
        cd = current_dasha or {}
        md = cd.get("maha", "")
        DASHA_WEALTH = {"Jupiter":"Excellent","Venus":"Excellent","Mercury":"Very Good",
                        "Sun":"Good","Moon":"Average","Saturn":"Slow but Solid",
                        "Mars":"Volatile","Rahu":"Sudden gains/losses","Ketu":"Spiritual phase"}
        peak = {"current_md": md, "rating": DASHA_WEALTH.get(md, "Neutral"),
                "ends": cd.get("endDate", "")}

        from vedic.wealth_finance_v1 import compute_wealth_finance_diagnostic
        wealth_finance = compute_wealth_finance_diagnostic(
            planets,
            asc_idx,
            current_dasha,
            kundli,
            dhana_yogas=yogas,
            wealth_karma_score=wealth_karma_score,
            fallback_category=wealth_category,
        )
        wealth_finance = _patch_wealth_finance_dhan_details(wealth_finance, planets, asc_idx)

        ym = (wealth_finance.get("yog_metrics") or {})
        raj_yogas = list(ym.get("raj_yogas") or [])
        if not raj_yogas:
            from vedic.raj_yoga_engine_v1 import scan_raj_yogas
            raj_yogas = _serialize_yoga_metrics_api(scan_raj_yogas(planets, asc_idx))

        return {
            "wealth_karma_score": wealth_karma_score,
            "wealth_score":       wealth_karma_score,
            "wealth_operational_score": operational_score,
            "wealth_category":    wealth_category,
            "wealth_styles":      wealth_styles,
            "uses_d9_d10":        bool(
                (kundli or {}).get("divisionalCharts", {}).get("D9", {}).get("planets")
                or (kundli or {}).get("divisionalCharts", {}).get("D10", {}).get("planets")
            ),
            "dhana_yogas":        yogas,
            "raj_yogas":          raj_yogas,
            "yogas_count":        yogas_count,
            "money_habits":       money_habits,
            "peak_wealth_period": peak,
            "wealth_finance":     wealth_finance,
        }
    except Exception as exc:
        return {"error": str(exc)}


_CALM_FINANCE_HABITS = [
    "Track monthly expenses — know where money goes",
    "Save at least 10% before spending on wants",
    "Avoid rushed big purchases this month",
    "Review subscriptions and small leaks",
]


def _classify_wealth_category(composite: int) -> str:
    """middle_class → rich → ultra_rich → millionaire (birth chart score only)."""
    from vedic.wealth_finance_v1 import wealth_tier_from_score
    return wealth_tier_from_score(composite)


def _pick_finance_focus_key(
    trend: str,
    deep: Dict[str, Any],
    transit_notes: Optional[List[str]] = None,
) -> str:
    category = str(deep.get("wealth_category") or deep.get("wealth_tier") or "")
    notes = " ".join(transit_notes or []).lower()
    if trend == "Loss" or category == "Struggle":
        return "caution"
    if "expense" in notes or "discipline on expenses" in notes:
        return "savings"
    if trend == "Gain":
        styles = [str(s).lower() for s in (deep.get("wealth_styles") or [])]
        if "speculative" in styles:
            return "invest"
        return "growth"
    if trend == "Stable":
        return "steady"
    return "steady"


def _derive_static_money_habits(
    planets: List[dict],
    asc_idx: int,
    wealth_category: str,
    pattern_signals: Dict[str, bool],
) -> List[str]:
    """Fixed money habits from birth-chart weaknesses only — no dasha, no transit, no trend."""
    out: List[str] = []
    sign_2 = SIGNS[(asc_idx + 1) % 12]
    sign_11 = SIGNS[(asc_idx + 10) % 12]
    lord_2 = SIGN_LORD[sign_2]
    lord_11 = SIGN_LORD[sign_11]

    def find_p(name: str) -> Optional[dict]:
        return next((p for p in planets if p.get("name") == name), None)

    l2 = find_p(lord_2)
    if l2:
        h2 = int(l2.get("house") or 0)
        sg2 = str(l2.get("sign") or "")
        if h2 in (6, 8, 12):
            out.append(
                "Savings can leak — 2nd lord in a drain house; track expenses and plug small outflows"
            )
        if lord_2 in DEBIL and sg2 == DEBIL[lord_2]:
            out.append(
                "Wealth needs patience — avoid get-rich-quick moves; steady income beats shortcuts"
            )

    l11 = find_p(lord_11)
    if l11:
        h11 = int(l11.get("house") or 0)
        sg11 = str(l11.get("sign") or "")
        if h11 in (6, 8, 12):
            out.append(
                "Gains may face blocks — don’t depend on one income stream; build a backup plan"
            )
        if lord_11 in DEBIL and sg11 == DEBIL[lord_11]:
            out.append(
                "Income rhythm can fluctuate — automate savings on good months"
            )

    for p in planets:
        h = int(p.get("house") or 0)
        nm = p.get("name") or ""
        if h == 2 and nm == "Ketu":
            out.append("Money can slip away quietly — review bank statements weekly for 30 days")
        elif h == 2 and nm == "Saturn":
            out.append("Wealth builds slowly — use fixed monthly SIP; avoid comparing with others")
        elif h == 2 and nm in ("Rahu", "Mars"):
            out.append("Impulsive spending risk — wait 48 hours before any large purchase")
        elif h == 12 and nm in ("Saturn", "Rahu", "Ketu"):
            out.append("Hidden expenses may hurt — cut unused subscriptions and idle memberships")
        elif h == 8 and nm in ("Mars", "Rahu", "Saturn", "Ketu"):
            out.append(
                "Sudden money swings possible — keep 6 months expenses in a separate emergency fund"
            )
        elif h == 6 and nm in ("Saturn", "Rahu", "Mars"):
            out.append("Work stress can trigger spending — set a simple monthly fun-money cap")

    rahu = find_p("Rahu")
    if rahu and int(rahu.get("house") or 0) in (5, 8):
        out.append(
            "Speculation tempts this chart — cap risky bets; never invest money you cannot afford to lose"
        )

    if pattern_signals.get("rahu_8") or pattern_signals.get("rahu_11"):
        if not any("Speculation" in x for x in out):
            out.append(
                "Unconventional income needs discipline — save part of every windfall immediately"
            )

    if wealth_category == "middle_class":
        out.append("Lifestyle creep is the main trap — raise savings % before upgrading spends")

    seen: set = set()
    unique: List[str] = []
    for line in out:
        if line not in seen:
            seen.add(line)
            unique.append(line)
        if len(unique) >= 4:
            break

    if len(unique) < 2:
        unique.extend([
            "Track monthly expenses — know where money goes",
            "Save at least 10% before spending on wants",
        ])
    return unique[:4]


def _soften_finance_transit(line: str) -> str:
    t = str(line).strip()
    if not t:
        return ""
    low = t.lower()
    if "no major" in low and ("transit" in low or "currently" in low):
        return "A calm money window — steady habits are enough."
    if "opportunity" in low or "wealth-building" in low:
        return "Good window to grow income — act on well-researched plans."
    if "expense" in low or "outflow" in low or "discipline on expenses" in low:
        return "Watch spending — track monthly outflows for a few weeks."
    if "sudden income" in low or "unconventional gain" in low:
        return "Unexpected income is possible — stay grounded and save part of it."
    if "comfort spending" in low or "luxury" in low:
        return "Comfort spending may rise — set a simple monthly cap."
    if _has_astro_jargon(t):
        return "Money energy is mixed — go steady and avoid rushed decisions."
    for planet in (
        "Saturn", "Mars", "Rahu", "Ketu", "Jupiter", "Mercury", "Venus", "Sun", "Moon",
    ):
        t = t.replace(planet, "Planetary")
    t = t.replace("transiting", "in focus").replace("—", "–")
    return t[:72] if len(t) > 72 else t


def build_finance_basic_insights(
    score: int,
    trend: str,
    summary: str,
    deep: Dict[str, Any],
    *,
    transit_notes: Optional[List[str]] = None,
    current_dasha: Optional[dict] = None,
) -> Dict[str, Any]:
    """Calm finance dashboard — minimal fields, no Pro upsell or raw chart jargon."""
    trend_n = (trend or "Stable").strip()
    if trend_n == "Gain":
        phase_key = "growth"
    elif trend_n == "Loss":
        phase_key = "caution"
    else:
        phase_key = "steady"

    # Wealth category: birth chart only (lords, houses, yogas) — no dasha, no transit.
    karma = int(deep.get("wealth_karma_score") or deep.get("wealth_score") or 50)
    wealth_category = str(deep.get("wealth_category") or _classify_wealth_category(karma))
    composite = karma
    operational = int(deep.get("wealth_operational_score") or score or karma)

    finance_focus_key = _pick_finance_focus_key(trend_n, deep, transit_notes)
    money_habits = list(deep.get("money_habits") or [])

    transits: List[str] = []
    for n in (transit_notes or []):
        soft = _soften_finance_transit(str(n))
        if soft and soft not in transits:
            transits.append(soft)
        if len(transits) >= 2:
            break

    wealth_finance = dict(deep.get("wealth_finance") or {})
    if wealth_finance and transit_notes:
        try:
            from vedic.wealth_finance_v1 import _liquidity_index
            wealth_finance["current_liquidity_index"] = _liquidity_index(
                [], 0, transit_notes=transit_notes,
            )
        except Exception:
            pass

    dhana_yogas = list(deep.get("dhana_yogas") or [])
    raj_yogas = list(deep.get("raj_yogas") or [])
    ym = dict(wealth_finance.get("yog_metrics") or {})
    if ym.get("dhan_yogas"):
        dhana_yogas = list(ym["dhan_yogas"])
    elif dhana_yogas:
        ym["dhan_yogas"] = _serialize_yoga_metrics_api(dhana_yogas)
    if ym.get("raj_yogas"):
        raj_yogas = list(ym["raj_yogas"])
    elif raj_yogas:
        ym["raj_yogas"] = _serialize_yoga_metrics_api(raj_yogas)
    if ym.get("dhan_yogas"):
        ym["dhan_count"] = len(ym["dhan_yogas"])
        ym["dhan_yoga_names"] = [str(x.get("name") or "") for x in ym["dhan_yogas"]]
    if ym.get("raj_yogas"):
        ym["raj_count"] = len(ym["raj_yogas"])
        ym["raj_yoga_names"] = [str(x.get("name") or "") for x in ym["raj_yogas"]]
    if ym:
        wealth_finance["yog_metrics"] = ym

    return {
        "score": max(0, min(100, operational)),
        "trend": trend_n,
        "summary": summary,
        "hook": (
            "Full gain windows, house-level wealth map, and remedy blueprint "
            "unlock with Pro."
        ),
        "phase_key": phase_key,
        "finance_focus_key": finance_focus_key,
        "wealth_category": wealth_category,
        "wealth_composite_score": composite,
        "wealth_karma_score": karma,
        "wealth_styles": list(deep.get("wealth_styles") or []),
        "money_habits": money_habits,
        "transit_lines": transits,
        "wealth_finance": wealth_finance,
        "dhana_yogas": dhana_yogas,
        "raj_yogas": raj_yogas,
    }
