"""
remedies.py
───────────
Deterministic Vedic remedies engine. Replaces AI's per-answer remedy
hallucination with a single source of truth — classical mantras, gemstones,
charity items, fasting days, colours, and yantras drawn from BPHS,
Phaladeepika, and Lal Kitab consensus.

Triggering logic (priority order)
─────────────────────────────────
  1. Current Mahadasha lord — if WEAK / combust / debilitated → its remedy
     dominates (you live this planet's vibration for years).
  2. Special doshas — Sade-Sati / Dhaiya (Saturn), Mangal Dosh (Mars),
     Kal Sarpa (Rahu-Ketu) get their own dedicated remedies.
  3. Topic-specific weakness — if the question is marriage and 7L is WEAK,
     surface the 7L-planet remedy.
  4. Strongest WEAK planet across the chart (fallback).

Public API
──────────
    select_remedies(planet_verdicts, current_dasha, special_dosha_list,
                    intel, topic) -> list[dict]
    format_remedies_summary(remedies) -> str

Each remedy dict shape:
    {
      "for":       str,     # what this is fixing — e.g. "Saturn (Mahadasha lord, weak)"
      "planet":    str,     # canonical planet name
      "mantra":    {"sanskrit": "...", "transliteration": "...", "count": 108, "day": "Saturday"},
      "gemstone":  {"name": "Blue Sapphire", "weight_carats": "5-7", "metal": "Silver", "finger": "Middle"},
      "charity":   ["Black sesame seeds", "Iron items", "Mustard oil"],
      "fast_day":  "Saturday",
      "colour":    "Dark blue / black",
      "yantra":    "Shani Yantra",
    }

Notes
─────
- ⚠️ Rahu and Ketu have NO classical gemstone in the strict BPHS sense —
  Hessonite (Rahu) and Cat's Eye (Ketu) are post-classical Lal Kitab additions.
  We surface them but mark the caveat.
- We never fabricate a "lucky number" or astrological gimmick — if a remedy
  category isn't traditionally prescribed for a planet, we omit it.
"""
from __future__ import annotations
from typing import Any

# ── Canonical per-planet remedy table ────────────────────────────────────────
_REMEDY_TABLE: dict[str, dict[str, Any]] = {
    "Sun": {
        "mantra": {
            "sanskrit": "ॐ घृणि सूर्याय नमः",
            "transliteration": "Om Ghrini Suryaya Namah",
            "count": 108, "day": "Sunday",
        },
        "gemstone": {"name": "Ruby (Manik)", "weight_carats": "3-5",
                     "metal": "Gold / Copper", "finger": "Ring"},
        "charity": ["Wheat", "Jaggery (gud)", "Copper items", "Red cloth"],
        "fast_day": "Sunday (sunrise to sunset, no salt)",
        "colour":   "Red / Saffron / Orange",
        "yantra":   "Surya Yantra",
    },
    "Moon": {
        "mantra": {
            "sanskrit": "ॐ श्रां श्रीं श्रौं सः चन्द्रमसे नमः",
            "transliteration": "Om Shraam Shreem Shraum Sah Chandramase Namah",
            "count": 108, "day": "Monday",
        },
        "gemstone": {"name": "Pearl (Moti)", "weight_carats": "5-7",
                     "metal": "Silver", "finger": "Little"},
        "charity": ["Rice", "Milk", "White cloth", "Silver items"],
        "fast_day": "Monday",
        "colour":   "White / Silver",
        "yantra":   "Chandra Yantra",
    },
    "Mars": {
        "mantra": {
            "sanskrit": "ॐ क्रां क्रीं क्रौं सः भौमाय नमः",
            "transliteration": "Om Kraam Kreem Kraum Sah Bhaumaya Namah",
            "count": 108, "day": "Tuesday",
        },
        "gemstone": {"name": "Red Coral (Moonga)", "weight_carats": "5-9",
                     "metal": "Copper / Gold", "finger": "Ring"},
        "charity": ["Red lentils (masoor dal)", "Jaggery", "Red cloth", "Copper"],
        "fast_day": "Tuesday",
        "colour":   "Red",
        "yantra":   "Mangal Yantra",
    },
    "Mercury": {
        "mantra": {
            "sanskrit": "ॐ ब्रां ब्रीं ब्रौं सः बुधाय नमः",
            "transliteration": "Om Braam Breem Braum Sah Budhaya Namah",
            "count": 108, "day": "Wednesday",
        },
        "gemstone": {"name": "Emerald (Panna)", "weight_carats": "3-5",
                     "metal": "Gold / Silver", "finger": "Little"},
        "charity": ["Green moong dal", "Green vegetables", "Green cloth", "Books / pens"],
        "fast_day": "Wednesday",
        "colour":   "Green",
        "yantra":   "Budha Yantra",
    },
    "Jupiter": {
        "mantra": {
            "sanskrit": "ॐ ग्रां ग्रीं ग्रौं सः गुरवे नमः",
            "transliteration": "Om Graam Greem Graum Sah Gurave Namah",
            "count": 108, "day": "Thursday",
        },
        "gemstone": {"name": "Yellow Sapphire (Pukhraj)", "weight_carats": "5-7",
                     "metal": "Gold", "finger": "Index"},
        "charity": ["Chana dal", "Turmeric", "Yellow cloth", "Banana", "Gold (if affordable)"],
        "fast_day": "Thursday",
        "colour":   "Yellow",
        "yantra":   "Guru Yantra",
    },
    "Venus": {
        "mantra": {
            "sanskrit": "ॐ द्रां द्रीं द्रौं सः शुक्राय नमः",
            "transliteration": "Om Draam Dreem Draum Sah Shukraya Namah",
            "count": 108, "day": "Friday",
        },
        "gemstone": {"name": "Diamond (Heera) / White Sapphire (substitute)",
                     "weight_carats": "0.5-1 (diamond) or 5-7 (white sapphire)",
                     "metal": "Silver / Platinum", "finger": "Middle"},
        "charity": ["Rice", "Sugar / mishri", "White cloth", "Curd", "Perfume"],
        "fast_day": "Friday",
        "colour":   "White / Pastels",
        "yantra":   "Shukra Yantra",
    },
    "Saturn": {
        "mantra": {
            "sanskrit": "ॐ शं शनैश्चराय नमः",
            "transliteration": "Om Sham Shanaishcharaya Namah",
            "count": 108, "day": "Saturday",
        },
        "gemstone": {"name": "Blue Sapphire (Neelam)", "weight_carats": "5-7",
                     "metal": "Silver / Panchdhatu", "finger": "Middle",
                     "caveat": "TRIAL FIRST 3 days — Blue Sapphire is the most reactive gemstone; if you feel disturbance, do NOT wear."},
        "charity": ["Black sesame (til)", "Mustard oil", "Iron items", "Black cloth", "Urad dal"],
        "fast_day": "Saturday",
        "colour":   "Dark blue / Black",
        "yantra":   "Shani Yantra",
    },
    "Rahu": {
        "mantra": {
            "sanskrit": "ॐ भ्रां भ्रीं भ्रौं सः राहवे नमः",
            "transliteration": "Om Bhraam Bhreem Bhraum Sah Rahave Namah",
            "count": 108, "day": "Saturday (or Wednesday)",
        },
        "gemstone": {"name": "Hessonite (Gomed)", "weight_carats": "5-7",
                     "metal": "Silver / Panchdhatu", "finger": "Middle",
                     "caveat": "Post-classical (Lal Kitab tradition) — not prescribed in strict BPHS."},
        "charity": ["Mustard oil", "Black urad dal", "Coconut", "Blue cloth"],
        "fast_day": "Saturday",
        "colour":   "Smoky grey / Dark blue",
        "yantra":   "Rahu Yantra",
    },
    "Ketu": {
        "mantra": {
            "sanskrit": "ॐ स्रां स्रीं स्रौं सः केतवे नमः",
            "transliteration": "Om Sraam Sreem Sraum Sah Ketave Namah",
            "count": 108, "day": "Tuesday",
        },
        "gemstone": {"name": "Cat's Eye (Lehsunia)", "weight_carats": "3-5",
                     "metal": "Silver / Panchdhatu", "finger": "Middle",
                     "caveat": "Post-classical — wear only after astrologer confirmation; Ketu is volatile."},
        "charity": ["Black-and-white blanket", "Sesame seeds", "Coconut to a temple"],
        "fast_day": "Tuesday",
        "colour":   "Multi-colour / Smoky",
        "yantra":   "Ketu Yantra",
    },
}


_MAHADASHA_AFFLICTION = {"WEAK"}    # treat WEAK MD lord as primary trigger


def _is_combust_or_debil(planet: str, intel: dict) -> bool:
    for d in (intel.get("dignities") or []):
        if d.get("planet") == planet and d.get("status") in {"DEBILITATED", "COMBUST"}:
            return True
    return False


def _topic_planet(topic: str | None, intel: dict) -> tuple[int, str | None]:
    """Return (house, lord_planet) most relevant to the topic."""
    house_lords = intel.get("house_lords") or []

    def _lord(h: int) -> str | None:
        return next((x.get("lord") for x in house_lords if x.get("house") == h), None)

    t = (topic or "").lower()
    if "marriage" in t or "relationship" in t: return 7, _lord(7)
    if "career"   in t or "job"          in t: return 10, _lord(10)
    if "money"    in t or "wealth"       in t: return 2,  _lord(2)
    if "child"    in t or "education"    in t: return 5,  _lord(5)
    if "health"   in t:                        return 6,  _lord(6)
    if "home"     in t or "family"       in t: return 4,  _lord(4)
    return 0, None


def _build_entry(reason: str, planet: str) -> dict[str, Any]:
    base = _REMEDY_TABLE.get(planet)
    if not base:
        return {}
    return {
        "for":      reason,
        "planet":   planet,
        "mantra":   base["mantra"],
        "gemstone": base["gemstone"],
        "charity":  base["charity"],
        "fast_day": base["fast_day"],
        "colour":   base["colour"],
        "yantra":   base["yantra"],
    }


def _special_dosha_remedy(dosha_name: str) -> dict[str, Any] | None:
    """Special dedicated remedies for top-3 doshas."""
    n = (dosha_name or "").lower().replace("-", " ").replace("_", " ")
    if "sade" in n:
        return {
            "for":      "Sade-Sati (Saturn 12/1/2 from natal Moon)",
            "planet":   "Saturn",
            "mantra":   {"sanskrit": "ॐ नीलाञ्जन समाभासं रविपुत्रं यमाग्रजम् | छायामार्ताण्डसम्भूतं तं नमामि शनैश्चरम् ||",
                         "transliteration": "Om Neelanjana Samabhasam Raviputram Yamagrajam | Chhaya Martanda Sambhutam Tam Namami Shanaishcharam",
                         "count": 11, "day": "Saturday"},
            "gemstone": _REMEDY_TABLE["Saturn"]["gemstone"],
            "charity":  ["Mustard oil to a poor person on Saturday",
                         "Black sesame in flowing water",
                         "Feed black dogs / crows / labourers"],
            "fast_day": "Saturday",
            "colour":   "Dark blue / Black",
            "yantra":   "Shani Yantra (under pillow during Sade-Sati)",
            "extra":    "Recite Hanuman Chalisa daily — Hanuman protects from Saturn affliction.",
        }
    if "mangal" in n or "manglik" in n:
        return {
            "for":      "Mangal Dosh (Mars in 1/4/7/8/12)",
            "planet":   "Mars",
            "mantra":   {"sanskrit": "ॐ अंगारकाय नमः",
                         "transliteration": "Om Angarakaya Namah",
                         "count": 108, "day": "Tuesday"},
            "gemstone": _REMEDY_TABLE["Mars"]["gemstone"],
            "charity":  ["Red lentils (masoor) on Tuesday",
                         "Red cloth to a temple",
                         "Sweets to the poor"],
            "fast_day": "Tuesday",
            "colour":   "Red",
            "yantra":   "Mangal Yantra",
            "extra":    "Hanuman Chalisa daily; visit Hanuman temple on Tuesdays.",
        }
    # Match "kal sarp", "kaal sarp", "kal sarpa", "kalasarpa" etc.
    if "kal" in n and "sarp" in n:
        return {
            "for":      "Kal Sarpa Dosh (all 7 planets between Rahu & Ketu)",
            "planet":   "Rahu",
            "mantra":   {"sanskrit": "ॐ नागदेवाय नमः",
                         "transliteration": "Om Nag-Devaya Namah",
                         "count": 108, "day": "Saturday or Naga-panchami"},
            "gemstone": _REMEDY_TABLE["Rahu"]["gemstone"],
            "charity":  ["Donate silver naga (snake) at Shiva temple",
                         "Offer milk to Shiva-linga on Mondays",
                         "Sponsor Naga-Pratishtha puja at Trimbakeshwar / Kalahasti"],
            "fast_day": "Naga-panchami / Saturday",
            "colour":   "Silver / White",
            "yantra":   "Kal-Sarpa Yantra",
            "extra":    "Mahamrityunjaya jaap (108 daily) + visit Trimbakeshwar/Kalahasti for one-time Kal-Sarpa shanti.",
        }
    return None


def _md_lord(current_dasha: dict | None) -> str | None:
    """Robust extraction — accept multiple key conventions."""
    if not isinstance(current_dasha, dict):
        return None
    for k in ("maha", "mahadasha", "md", "planet", "lord"):
        v = current_dasha.get(k)
        if isinstance(v, str) and v in _REMEDY_TABLE:
            return v
    return None


def select_remedies(planet_verdicts: dict | None,
                    current_dasha:   dict | None,
                    doshas_present:  list[str] | None,
                    intel:           dict,
                    topic:           str | None,
                    planet_scores:   dict | None = None) -> list[dict[str, Any]]:
    """
    Returns up to 3 remedies, in priority order. `planet_scores` is the optional
    full {planet: {verdict, reason, score}} payload — used to pick the TRULY
    weakest planet for the fallback (lowest score wins).
    """
    out: list[dict[str, Any]] = []
    seen_planets: set[str] = set()

    # 1. Special dosha remedies
    for d in (doshas_present or []):
        rem = _special_dosha_remedy(d)
        if rem and rem["planet"] not in seen_planets:
            out.append(rem)
            seen_planets.add(rem["planet"])
            if len(out) >= 3:
                return out

    # 2. Mahadasha lord if weak / debilitated / combust
    md_lord = _md_lord(current_dasha)
    if md_lord and md_lord not in seen_planets:
        verdict = (planet_verdicts or {}).get(md_lord, "")
        afflicted = verdict in _MAHADASHA_AFFLICTION or _is_combust_or_debil(md_lord, intel)
        if afflicted:
            entry = _build_entry(
                f"{md_lord} (running Mahadasha lord, {verdict.lower() or 'afflicted'})", md_lord)
            if entry:
                out.append(entry); seen_planets.add(md_lord)
                if len(out) >= 3: return out

    # 3. Topic-specific lord if weak
    _, topic_lord = _topic_planet(topic, intel)
    if topic_lord and topic_lord in _REMEDY_TABLE and topic_lord not in seen_planets:
        v = (planet_verdicts or {}).get(topic_lord, "")
        if v == "WEAK" or _is_combust_or_debil(topic_lord, intel):
            entry = _build_entry(
                f"{topic_lord} (lord of the house most relevant to your question, weak)",
                topic_lord)
            if entry:
                out.append(entry); seen_planets.add(topic_lord)
                if len(out) >= 3: return out

    # 4. Fallback: TRULY weakest remaining planet (lowest score, not dict order)
    if planet_verdicts:
        weak_candidates = []
        for p, v in planet_verdicts.items():
            if v != "WEAK" or p not in _REMEDY_TABLE or p in seen_planets:
                continue
            sc = None
            if isinstance(planet_scores, dict):
                row = planet_scores.get(p)
                if isinstance(row, dict):
                    sc = row.get("score")
            weak_candidates.append((sc if isinstance(sc, (int, float)) else 0, p))
        if weak_candidates:
            weak_candidates.sort(key=lambda t: t[0])  # lowest score first
            p = weak_candidates[0][1]
            entry = _build_entry(f"{p} (weakest planet in chart)", p)
            if entry:
                out.append(entry); seen_planets.add(p)

    return out


def format_remedies_summary(remedies: list[dict]) -> str:
    if not remedies:
        return ""    # no obvious affliction → don't surface generic remedy
    lines = ["▸ REMEDIES (classical — cite EXACTLY, do NOT invent mantras/gemstones):"]
    for i, r in enumerate(remedies, 1):
        lines.append(f"   ── REMEDY {i}: for: {r['for']} ──")
        m = r["mantra"]
        lines.append(f"      ▸ MANTRA: {m['transliteration']}  ({m['sanskrit']})")
        lines.append(f"        → {m['count']} times, on {m['day']}")
        g = r["gemstone"]
        gem_line = f"      ▸ GEMSTONE: {g['name']}, {g['weight_carats']} ct, {g['metal']}, {g['finger']} finger"
        if g.get("caveat"):
            gem_line += f"\n        ⚠️ {g['caveat']}"
        lines.append(gem_line)
        lines.append(f"      ▸ CHARITY (Daan): {', '.join(r['charity'])}")
        lines.append(f"      ▸ FAST DAY: {r['fast_day']}    COLOUR: {r['colour']}    YANTRA: {r['yantra']}")
        if r.get("extra"):
            lines.append(f"      ▸ EXTRA: {r['extra']}")
    return "\n".join(lines)
