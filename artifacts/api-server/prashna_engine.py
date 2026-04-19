"""
Divya Prashna — Vedic Horary engine.

Classical "Time Prashna" (Prashna Marga + Krishneeyam) using the existing
KP cuspal sub-lord chart. The user only types a question; the chart is cast
for the *current server time* at *Bhubaneswar, Odisha* (the astrologer's
seat). The relevant cusp's sub-lord and its significators are evaluated
against the question category's positive / negative house set to produce
a deterministic Yes / No / Conditional verdict with timing.

Sources cited inline:
- Prashna Marga, Ch. 5 (cuspal lord rulership)
- Shatpanchashika of Prithuyashas (yogas in horary)
- KP Reader VI by K. S. Krishnamurti (sub-lord theory)
- Krishneeyam (validity rules)
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from zoneinfo import ZoneInfo

from kp_engine import (
    calculate_kp,
    VIMSHOTTARI_SEQ, VIMSHOTTARI_YRS, NAKSHA_EXTENT,
    NAKSHATRAS, SIGNS, get_kp_lords, get_kp_house, get_owned_houses,
    format_deg_sign, ALL_PLANETS,
)


# ── Astrologer's seat (locked) ──────────────────────────────────────────────
# Bhubaneswar, Odisha — Lingaraj kshetra, classical jyotish bhoomi.
ASTROLOGER_SEAT = {
    "name": "Bhubaneswar",
    "state": "Odisha",
    "lat": 20.2961,
    "lon": 85.8245,
    "tz_name": "Asia/Kolkata",
    "tz_offset": 5.5,
}


# ── Question category → primary cusps + positive / negative house sets ──────
# Standard KP horary house groups (KP Reader VI).
CATEGORIES: Dict[str, Dict[str, Any]] = {
    "stolen_item": {
        "label_en": "Stolen / lost item recovery",
        "label_hi": "Chori / kho gaya saaman wapas milega?",
        "primary_cusps":  [2, 11],
        "positive": {2, 11},
        "negative": {6, 8, 12},
        "positive_meaning": "saaman wapas milega",
        "negative_meaning": "saaman wapas nahi milega",
    },
    "partner_feelings": {
        "label_en": "Partner's current feelings",
        "label_hi": "Partner ke abhi ke feelings",
        "primary_cusps":  [7, 5, 11],
        "positive": {2, 5, 7, 11},
        "negative": {1, 6, 10, 12},
        "positive_meaning": "partner pyar / lagaav mehsoos kar raha hai",
        "negative_meaning": "rishta thanda ya doori ki taraf",
    },
    "job": {
        "label_en": "Will I get the job / new role?",
        "label_hi": "Naukri lagegi ya nahi?",
        "primary_cusps":  [6, 10, 11],
        "positive": {2, 6, 10, 11},
        "negative": {5, 8, 9, 12},
        "positive_meaning": "naukri / role milega",
        "negative_meaning": "abhi nahi milega, prayatna jaari rakhein",
    },
    "marriage": {
        "label_en": "When will marriage happen?",
        "label_hi": "Shaadi kab hogi?",
        "primary_cusps":  [2, 7, 11],
        "positive": {2, 7, 11},
        "negative": {1, 6, 10},
        "positive_meaning": "shaadi yog ban raha hai",
        "negative_meaning": "vilamb (delay) ya rukavat hai",
    },
    "health": {
        "label_en": "Will the illness be cured?",
        "label_hi": "Bimari theek hogi?",
        "primary_cusps":  [1, 5, 11],
        "positive": {1, 5, 11},
        "negative": {6, 8, 12},
        "positive_meaning": "swasthya labh hoga",
        "negative_meaning": "rog dheere theek hoga, dhairya rakhein",
    },
    "litigation": {
        "label_en": "Will I win the case?",
        "label_hi": "Mukadma jeetenge?",
        "primary_cusps":  [6, 11],
        "positive": {6, 10, 11},
        "negative": {5, 7, 8, 12},
        "positive_meaning": "vijay hogi",
        "negative_meaning": "samjhauta ya pratikool faisla",
    },
    "travel": {
        "label_en": "Will the journey happen?",
        "label_hi": "Yatra hogi ya nahi?",
        "primary_cusps":  [3, 9, 12],
        "positive": {3, 9, 12},
        "negative": {1, 4, 8},
        "positive_meaning": "yatra sampann hogi",
        "negative_meaning": "yatra rukegi ya tal jayegi",
    },
    "general": {
        "label_en": "General yes / no question",
        "label_hi": "Saamanya prashna",
        "primary_cusps":  [11],
        "positive": {11},
        "negative": {12},
        "positive_meaning": "icchha purna hogi",
        "negative_meaning": "icchha abhi purna nahi hogi",
    },
}


# ── Keyword-based category inference (Hindi + English + Hinglish) ───────────
_KEYWORDS: List[Tuple[str, List[str]]] = [
    ("stolen_item",     ["chori", "chura", "stolen", "lost", "kho", "missing",
                          "wapas", "milega", "sona", "paisa gaya", "money lost"]),
    ("partner_feelings",["partner", "boyfriend", "girlfriend", "bf", "gf", "pyar",
                          "love", "feelings", "soch", "yaad", "miss", "rishta",
                          "ladka", "ladki"]),
    ("marriage",        ["shaadi", "marriage", "vivah", "wedding", "rishta pakka",
                          "engagement", "biya"]),
    ("job",             ["job", "naukri", "interview", "promotion", "kaam",
                          "career", "office", "hire", "salary"]),
    ("health",          ["bimari", "illness", "rog", "health", "swasthya",
                          "operation", "surgery", "dard", "pain", "doctor"]),
    ("litigation",      ["mukadma", "case", "court", "kacheri", "lawsuit",
                          "police", "fir", "vivad", "dispute"]),
    ("travel",          ["yatra", "travel", "journey", "trip", "videsh",
                          "abroad", "visa", "flight"]),
]


def infer_category(question: str) -> str:
    q = (question or "").lower()
    for cat, words in _KEYWORDS:
        for w in words:
            if w in q:
                return cat
    return "general"


# ── Validity check (Krishneeyam) ────────────────────────────────────────────
def _validity_check(cusps: List[Dict[str, Any]],
                    planets: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Return {valid:bool, reason:str|None, retry_after_min:int|None}."""
    lagna = cusps[0]
    lagna_lon = lagna["longitude"]
    deg_in_sign = lagna_lon % 30.0

    # Rule 1: lagna in first or last 3° of a sign — "infant" / "old" prashna
    if deg_in_sign < 3.0:
        return {
            "valid": False,
            "reason": ("Lagna sign ke prarambh mein hai (bal-avastha). "
                       "Prashna abhi paripakv nahi. Kuch der baad punah pucchein."),
            "classical_ref": "Krishneeyam Ch. 2",
            "retry_after_min": int((3.0 - deg_in_sign) * 4) + 5,
        }
    if deg_in_sign > 27.0:
        return {
            "valid": False,
            "reason": ("Lagna sign ke ant mein hai (vriddha-avastha). "
                       "Prashna ab nishphal sa hai. Lagna badalne ke baad pucchein."),
            "classical_ref": "Krishneeyam Ch. 2",
            "retry_after_min": int((30.0 - deg_in_sign) * 4) + 5,
        }

    # Rule 2: Rahu / Ketu in lagna → bhrami (deluded) prashna
    for p in planets:
        if p["name"] in ("Rahu", "Ketu") and p["house"] == 1:
            return {
                "valid": False,
                "reason": ("Lagna mein chhaaya graha (Rahu / Ketu) baitha hai — "
                           "prashna mein bhram ya gupt mansha hai. Mann shant kar "
                           "ke punah pucchein."),
                "classical_ref": "Prashna Marga Ch. 4",
                "retry_after_min": 30,
            }

    return {"valid": True, "reason": None, "retry_after_min": None}


# ── Verdict calculation ─────────────────────────────────────────────────────
def _significator_houses(planet_name: str,
                         significations: Dict[str, Any]) -> List[int]:
    """Combined houses a planet signifies (PL ∪ NL houses ∪ SB houses)."""
    sig = significations.get(planet_name, {})
    houses: set = set()
    for key in ("pl", "sl", "sb_houses"):
        for h in sig.get(key, []) or []:
            houses.add(int(h))
    return sorted(houses)


def _evaluate_cusp(cusp: Dict[str, Any],
                   significations: Dict[str, Any],
                   positive: set,
                   negative: set) -> Dict[str, Any]:
    """For a single cusp, judge YES / NO / MIXED based on its sub-lord."""
    sub_lord = cusp["sb"]
    sig_houses = set(_significator_houses(sub_lord, significations))
    pos_hits = sig_houses & positive
    neg_hits = sig_houses & negative

    if pos_hits and not neg_hits:
        verdict = "YES"
    elif neg_hits and not pos_hits:
        verdict = "NO"
    elif pos_hits and neg_hits:
        # Mixed — favour positive only if positive hits outnumber negatives
        verdict = "YES_CONDITIONAL" if len(pos_hits) > len(neg_hits) else "NO_CONDITIONAL"
    else:
        verdict = "NEUTRAL"

    return {
        "house":      cusp["house"],
        "sub_lord":   sub_lord,
        "star_lord":  cusp["nl"],
        "sign":       cusp["sign"],
        "degree":     cusp["degree"],
        "signifies":  sorted(sig_houses),
        "pos_hits":   sorted(pos_hits),
        "neg_hits":   sorted(neg_hits),
        "verdict":    verdict,
    }


def _aggregate_verdict(cusp_verdicts: List[Dict[str, Any]]) -> str:
    """Combine multiple cusp verdicts into a single answer."""
    score = 0
    for cv in cusp_verdicts:
        v = cv["verdict"]
        if   v == "YES":             score += 2
        elif v == "YES_CONDITIONAL": score += 1
        elif v == "NO_CONDITIONAL":  score -= 1
        elif v == "NO":              score -= 2

    if score >= 3:   return "YES"
    if score >= 1:   return "YES_LIKELY"
    if score == 0:   return "UNCERTAIN"
    if score >= -2:  return "NO_LIKELY"
    return "NO"


VERDICT_LABELS = {
    "YES":        ("Haan ✅",          "Yes — clear positive"),
    "YES_LIKELY": ("Sambhavna prabal", "Likely yes"),
    "UNCERTAIN":  ("Anishchit",        "Uncertain — chart mixed"),
    "NO_LIKELY":  ("Sambhavna kam",    "Unlikely"),
    "NO":         ("Nahi ❌",          "No — clear negative"),
}


def _timing_hint(cusp_verdicts: List[Dict[str, Any]],
                 planets: List[Dict[str, Any]]) -> str:
    """Rough timing window from sub-lord nakshatra dasha (KP convention)."""
    if not cusp_verdicts:
        return "Samay anuman nahi nikla."

    primary = cusp_verdicts[0]
    sub_lord = primary["sub_lord"]

    # Vimshottari dasha years
    dasha_years = {
        "Sun": 6, "Moon": 10, "Mars": 7, "Rahu": 18, "Jupiter": 16,
        "Saturn": 19, "Mercury": 17, "Ketu": 7, "Venus": 20,
    }
    yrs = dasha_years.get(sub_lord, 7)

    # Heuristic: faster planets → days/weeks; slower → months
    if sub_lord in ("Moon", "Mercury"):
        return f"Samay: agle 7-21 din ke andar sanket milne ki sambhavna ({sub_lord} sub-lord)."
    if sub_lord in ("Sun", "Venus", "Mars"):
        return f"Samay: 1-2 mahine ke andar parinaam ({sub_lord} sub-lord)."
    if sub_lord in ("Jupiter", "Saturn"):
        return f"Samay: 3-6 mahine ya {sub_lord} ke transit par ({yrs} yr maha-dasha karak)."
    return f"Samay: {sub_lord} ke gochar par dhyaan dein."


# ── Main entry point ────────────────────────────────────────────────────────
def ask_prashna(question: str,
                category: Optional[str] = None,
                now: Optional[datetime] = None) -> Dict[str, Any]:
    """
    Answer a horary question.

    Args:
      question: user's free-text question (any language)
      category: one of CATEGORIES keys, or None to infer from text
      now: optional override (for testing). Default = current Bhubaneswar local time.

    Returns:
      A dict with chart snapshot + verdict + timing + classical refs.
    """
    if not question or not question.strip():
        return {"error": "question_required",
                "message": "Apna sawaal type karein."}

    cat_key = category if (category in CATEGORIES) else infer_category(question)
    cat = CATEGORIES[cat_key]

    # ── Cast chart for *now* at Bhubaneswar ────────────────────────────────
    if now is None:
        now = datetime.now(ZoneInfo(ASTROLOGER_SEAT["tz_name"]))

    is_pm = now.hour >= 12
    hr12  = now.hour % 12 or 12

    chart = calculate_kp({
        "day":    now.day,
        "month":  now.month,
        "year":   now.year,
        "hour":   hr12,
        "minute": now.minute,
        "ampm":   "PM" if is_pm else "AM",
        "lat":    ASTROLOGER_SEAT["lat"],
        "lon":    ASTROLOGER_SEAT["lon"],
        "tz":     ASTROLOGER_SEAT["tz_offset"],
    })

    cusps          = chart["cusps"]
    planets        = chart["planets"]
    significations = chart["significations"]

    # ── Validity (Krishneeyam) ─────────────────────────────────────────────
    validity = _validity_check(cusps, planets)
    if not validity["valid"]:
        return {
            "ok":        False,
            "reason":    "invalid_prashna_time",
            "validity":  validity,
            "category":  cat_key,
            "timestamp": now.isoformat(),
            "place":     ASTROLOGER_SEAT,
        }

    # ── Evaluate primary cusps ─────────────────────────────────────────────
    cusp_verdicts = []
    for h in cat["primary_cusps"]:
        cusp = next((c for c in cusps if c["house"] == h), None)
        if cusp:
            cusp_verdicts.append(
                _evaluate_cusp(cusp, significations, cat["positive"], cat["negative"])
            )

    final = _aggregate_verdict(cusp_verdicts)
    label_hi, label_en = VERDICT_LABELS[final]

    # ── Build narrative (Hinglish) ─────────────────────────────────────────
    cusp_lines = []
    for cv in cusp_verdicts:
        cusp_lines.append(
            f"{cv['house']}th cusp ({cv['sign']} {cv['degree']}) — Sub-Lord "
            f"{cv['sub_lord']} → houses {cv['signifies']}; "
            f"positive hits {cv['pos_hits']}, negative hits {cv['neg_hits']} "
            f"=> {cv['verdict']}"
        )

    if final in ("YES", "YES_LIKELY"):
        meaning = cat["positive_meaning"]
    elif final in ("NO", "NO_LIKELY"):
        meaning = cat["negative_meaning"]
    else:
        meaning = "Sthithi mishrit hai — kuch graha haan keh rahe hain, kuch nahi."

    narrative = (
        f"Aap ka prashna: \"{question.strip()}\"\n\n"
        f"Vargi-karan: {cat['label_hi']}\n"
        f"Lagna: {cusps[0]['sign']} {cusps[0]['degree']}\n\n"
        f"Cusp vishleshan:\n  • " + "\n  • ".join(cusp_lines) + "\n\n"
        f"Nirnaay: {label_hi} — {meaning}.\n"
        f"{_timing_hint(cusp_verdicts, planets)}"
    )

    return {
        "ok":         True,
        "question":   question.strip(),
        "category":   cat_key,
        "category_label": cat["label_hi"],
        "place":      ASTROLOGER_SEAT,
        "timestamp":  now.isoformat(),
        "lagna":      {
            "sign":   cusps[0]["sign"],
            "degree": cusps[0]["degree"],
        },
        "verdict": {
            "code":         final,
            "label_hi":     label_hi,
            "label_en":     label_en,
            "meaning":      meaning,
        },
        "cusp_analysis":  cusp_verdicts,
        "timing":         _timing_hint(cusp_verdicts, planets),
        "narrative":      narrative,
        "classical_refs": [
            "Prashna Marga, Adhyaya 5 — cuspal lord rulership",
            "Krishneeyam — prashna validity rules",
            "KP Reader VI (K. S. Krishnamurti) — sub-lord significator theory",
        ],
        "chart": {
            "cusps":   cusps,
            "planets": planets,
        },
    }


# ── Catalog helper for mobile UI ────────────────────────────────────────────
def list_categories() -> List[Dict[str, str]]:
    return [
        {"key": k, "label_hi": v["label_hi"], "label_en": v["label_en"]}
        for k, v in CATEGORIES.items()
    ]


# ════════════════════════════════════════════════════════════════════════════
#  KP-249 Number System (K. S. Krishnamurti — Cuspal Interlinks Theory)
# ════════════════════════════════════════════════════════════════════════════
#  The querent picks a number 1-249. Each number maps to a fixed sub-division
#  of the 360° zodiac. That sub's mid-longitude becomes the FORCED LAGNA of
#  the horary chart cast at the current moment at the astrologer's seat.
#
#  Total = 27 nakshatras × 9 sub-lords = 243 raw subs. Subs that straddle a
#  sign boundary are split into TWO entries (one per sign), giving 249.
#
#  Source: KP Reader VI, Chapter 9 — "Horary by Number".
# ════════════════════════════════════════════════════════════════════════════

def _build_kp_249_table() -> List[Dict[str, Any]]:
    table: List[Dict[str, Any]] = []
    for nidx in range(27):
        n_lord = VIMSHOTTARI_SEQ[nidx % 9]            # Ashwini=Ketu, Bharani=Venus, ...
        start_idx = VIMSHOTTARI_SEQ.index(n_lord)
        cursor = nidx * NAKSHA_EXTENT
        for k in range(9):
            sub = VIMSHOTTARI_SEQ[(start_idx + k) % 9]
            sub_extent = NAKSHA_EXTENT * VIMSHOTTARI_YRS[sub] / 120.0
            sub_start, sub_end = cursor, cursor + sub_extent
            cursor = sub_end

            sign_a = int(sub_start / 30.0 + 1e-9) % 12
            sign_b = int((sub_end - 1e-9) / 30.0) % 12
            if sign_a == sign_b:
                table.append({"start": sub_start, "end": sub_end,
                              "sign_idx": sign_a, "naksh_idx": nidx, "sub_lord": sub})
            else:
                boundary = (sign_a + 1) * 30.0
                table.append({"start": sub_start, "end": boundary,
                              "sign_idx": sign_a, "naksh_idx": nidx, "sub_lord": sub})
                table.append({"start": boundary, "end": sub_end,
                              "sign_idx": sign_b, "naksh_idx": nidx, "sub_lord": sub})
    for i, row in enumerate(table):
        row["num"] = i + 1
    return table


KP_249_TABLE = _build_kp_249_table()
KP_249_COUNT = len(KP_249_TABLE)   # = 249


def number_to_lagna(n: int) -> Dict[str, Any]:
    """Map a KP horary number to the forced ascendant (midpoint of its sub)."""
    if n < 1 or n > KP_249_COUNT:
        raise ValueError(f"Number must be 1..{KP_249_COUNT}")
    row = KP_249_TABLE[n - 1]
    mid = (row["start"] + row["end"]) / 2.0
    return {
        "number":    n,
        "longitude": mid,
        "sign":      SIGNS[row["sign_idx"]],
        "nakshatra": NAKSHATRAS[row["naksh_idx"]],
        "sub_lord":  row["sub_lord"],
        "degree":    format_deg_sign(mid),
    }


def _cast_number_chart(forced_lagna_lon: float, now: datetime) -> Dict[str, Any]:
    """
    Cast a horary chart with the lagna FORCED to a specific longitude (from
    the querent's KP number), planet positions taken from the current moment
    at Bhubaneswar. Cusps are derived equal-house from the forced lagna —
    the standard simplification for KP horary number prashna.
    """
    is_pm = now.hour >= 12
    hr12  = now.hour % 12 or 12

    base = calculate_kp({
        "day": now.day, "month": now.month, "year": now.year,
        "hour": hr12,   "minute": now.minute,
        "ampm": "PM" if is_pm else "AM",
        "lat":  ASTROLOGER_SEAT["lat"],
        "lon":  ASTROLOGER_SEAT["lon"],
        "tz":   ASTROLOGER_SEAT["tz_offset"],
    })

    # Equal-house cusps from forced lagna
    new_cusps = [(forced_lagna_lon + 30.0 * h) % 360 for h in range(12)]
    cusps_out = []
    for h, clon in enumerate(new_cusps):
        sl, nl, sb, ss = get_kp_lords(clon)
        naksha_idx = int(clon / NAKSHA_EXTENT) % 27
        cusps_out.append({
            "house":     h + 1,
            "longitude": round(clon, 4),
            "degree":    format_deg_sign(clon),
            "sign":      SIGNS[int(clon / 30) % 12],
            "sl": sl, "nl": nl, "sb": sb, "ss": ss,
            "nakshatra": NAKSHATRAS[naksha_idx],
        })

    # Recompute planet→house using new cusps
    planet_lons = {p["name"]: p["longitude"] for p in base["planets"]}
    new_house_map = {p: get_kp_house(planet_lons[p], new_cusps) for p in ALL_PLANETS}
    planets_out = []
    for p in base["planets"]:
        p2 = dict(p)
        p2["house"] = new_house_map[p["name"]]
        planets_out.append(p2)

    # Recompute significations under new cusps
    def houses_for_lord(lord: str) -> List[int]:
        h_occ = [new_house_map[lord]] if lord in new_house_map else []
        h_own = get_owned_houses(lord, new_cusps)
        return sorted(set(h_occ + h_own))

    sig_out = {}
    for p in planets_out:
        pname = p["name"]
        owned = get_owned_houses(pname, new_cusps)
        sig_out[pname] = {
            "nl_lord":   p["nl"],
            "sb_lord":   p["sb"],
            "ss_lord":   p["ss"],
            "pl":        sorted(set([p["house"]] + owned)),
            "sl":        houses_for_lord(p["nl"]),
            "sb_houses": houses_for_lord(p["sb"]),
            "ss_houses": houses_for_lord(p["ss"]),
        }

    return {
        "cusps":          cusps_out,
        "planets":        planets_out,
        "significations": sig_out,
        "ayanamsa":       base["ayanamsa"],
    }


def ask_number_prashna(number: int,
                       question: str = "",
                       category: Optional[str] = None,
                       now: Optional[datetime] = None) -> Dict[str, Any]:
    """
    KP horary by number (1-249). The querent's number forces the lagna; the
    cuspal sub-lord at the relevant house then yields the verdict.
    """
    if not isinstance(number, int) or number < 1 or number > KP_249_COUNT:
        return {"ok": False, "error": "invalid_number",
                "message": f"Krupya 1 se {KP_249_COUNT} ke beech sankhya chunein."}

    if category in CATEGORIES:
        cat_key = category
    elif question.strip():
        cat_key = infer_category(question)
    else:
        cat_key = "general"
    cat = CATEGORIES[cat_key]

    if now is None:
        now = datetime.now(ZoneInfo(ASTROLOGER_SEAT["tz_name"]))

    lagna_info = number_to_lagna(number)
    chart = _cast_number_chart(lagna_info["longitude"], now)
    cusps, planets, sig = chart["cusps"], chart["planets"], chart["significations"]

    validity = _validity_check(cusps, planets)
    # Validity is now ADVISORY only — always compute the verdict so the
    # querent never sees an empty answer. If validity fails we attach a
    # `caution` flag the UI can surface as a banner above the verdict.
    caution = None
    if not validity["valid"]:
        caution = {
            "level":           "warning",
            "reason":          validity.get("reason"),
            "classical_ref":   validity.get("classical_ref"),
            "retry_after_min": validity.get("retry_after_min"),
        }

    cusp_verdicts = []
    for h in cat["primary_cusps"]:
        cusp = next((c for c in cusps if c["house"] == h), None)
        if cusp:
            cusp_verdicts.append(
                _evaluate_cusp(cusp, sig, cat["positive"], cat["negative"])
            )

    final = _aggregate_verdict(cusp_verdicts)
    label_hi, label_en = VERDICT_LABELS[final]

    cusp_lines = [
        f"{cv['house']}th cusp ({cv['sign']} {cv['degree']}) — Sub-Lord "
        f"{cv['sub_lord']} → houses {cv['signifies']}; "
        f"+{cv['pos_hits']} / -{cv['neg_hits']} => {cv['verdict']}"
        for cv in cusp_verdicts
    ]

    if final in ("YES", "YES_LIKELY"):
        meaning = cat["positive_meaning"]
    elif final in ("NO", "NO_LIKELY"):
        meaning = cat["negative_meaning"]
    else:
        meaning = "Sthithi mishrit hai — kuch graha haan keh rahe hain, kuch nahi."

    q_line = f"Aap ka prashna: \"{question.strip()}\"\n\n" if question.strip() else ""
    narrative = (
        q_line +
        f"Sankhya: {number}\n"
        f"Vargi-karan: {cat['label_hi']}\n"
        f"Forced Lagna: {lagna_info['sign']} {lagna_info['degree']} "
        f"(Nakshatra: {lagna_info['nakshatra']}, Sub-Lord: {lagna_info['sub_lord']})\n\n"
        f"Cusp vishleshan:\n  • " + "\n  • ".join(cusp_lines) + "\n\n"
        f"Nirnaay: {label_hi} — {meaning}.\n"
        f"{_timing_hint(cusp_verdicts, planets)}"
    )

    return {
        "ok":             True,
        "number":         number,
        "question":       question.strip(),
        "category":       cat_key,
        "category_label": cat["label_hi"],
        "place":          ASTROLOGER_SEAT,
        "timestamp":      now.isoformat(),
        "lagna": {
            "sign":      lagna_info["sign"],
            "degree":    lagna_info["degree"],
            "nakshatra": lagna_info["nakshatra"],
            "sub_lord":  lagna_info["sub_lord"],
        },
        "verdict": {
            "code":     final,
            "label_hi": label_hi,
            "label_en": label_en,
            "meaning":  meaning,
        },
        "caution":        caution,
        "cusp_analysis":  cusp_verdicts,
        "timing":         _timing_hint(cusp_verdicts, planets),
        "narrative":      narrative,
        "classical_refs": [
            "KP Reader VI (K. S. Krishnamurti) — Horary by number (1-249)",
            "Cuspal Interlinks Theory — sub-lord forced ascendant",
            "Prashna Marga, Adhyaya 5 — cuspal lord rulership",
            "Krishneeyam — prashna validity rules",
        ],
        "chart": {
            "cusps":   cusps,
            "planets": planets,
        },
    }
