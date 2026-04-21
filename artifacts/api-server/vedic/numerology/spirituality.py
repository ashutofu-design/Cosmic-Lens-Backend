"""Tier 11 — Spirituality, Moksha & Dharma-Path engine.

Hard data gate (asc + 9 grahas required); refuses on missing data.
Computes Moksha Trikona (4-8-12) audit, Atmakaraka + Karakamsa (Jaimini),
classical Ishta Devata (lord of 12th-from-Karakamsa in D9), Kuldevta (9th
house), Mantra Sadhana (numerology + planet beej), Saturn-Ketu Vairagya
score, and a synthesis verdict.
"""
from __future__ import annotations

from typing import Any, Dict, List, Tuple

SIGNS = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
         "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
SIGN_LORD = {
    "Aries": "Mars", "Taurus": "Venus", "Gemini": "Mercury", "Cancer": "Moon",
    "Leo": "Sun", "Virgo": "Mercury", "Libra": "Venus", "Scorpio": "Mars",
    "Sagittarius": "Jupiter", "Capricorn": "Saturn", "Aquarius": "Saturn",
    "Pisces": "Jupiter",
}
WATER = {"Cancer", "Scorpio", "Pisces"}
FIRE = {"Aries", "Leo", "Sagittarius"}
EARTH = {"Taurus", "Virgo", "Capricorn"}
AIR = {"Gemini", "Libra", "Aquarius"}
DUSTHANA = {6, 8, 12}
KENDRA = {1, 4, 7, 10}
TRIKONA = {1, 5, 9}

# Driver-number → ruling planet & beej mantra (numerology frame)
DRIVER_BEEJ: Dict[int, Dict[str, str]] = {
    1: {"planet": "Sun", "beej": "Om Hraam Hreem Hraum Sah Suryaaya Namah",
        "japa": "7,000 in 40 days", "best_time": "sunrise (Sunday)",
        "deity": "Surya / Lord Vishnu"},
    2: {"planet": "Moon", "beej": "Om Shraam Shreem Shraum Sah Chandraaya Namah",
        "japa": "11,000 in 40 days", "best_time": "Monday evening",
        "deity": "Goddess Parvati / Lord Krishna"},
    3: {"planet": "Jupiter", "beej": "Om Graam Greem Graum Sah Gurave Namah",
        "japa": "19,000 in 40 days", "best_time": "Thursday morning",
        "deity": "Lord Vishnu / Brihaspati / Sri Rama"},
    4: {"planet": "Rahu", "beej": "Om Bhraam Bhreem Bhraum Sah Rahave Namah",
        "japa": "18,000 in 40 days", "best_time": "Saturday dusk",
        "deity": "Goddess Durga"},
    5: {"planet": "Mercury", "beej": "Om Braam Breem Braum Sah Budhaaya Namah",
        "japa": "9,000 in 40 days", "best_time": "Wednesday morning",
        "deity": "Lord Vishnu / Krishna"},
    6: {"planet": "Venus", "beej": "Om Draam Dreem Draum Sah Shukraaya Namah",
        "japa": "16,000 in 40 days", "best_time": "Friday morning",
        "deity": "Goddess Lakshmi / Devi"},
    7: {"planet": "Ketu", "beej": "Om Sraam Sreem Sraum Sah Ketave Namah",
        "japa": "7,000 in 40 days", "best_time": "Tuesday or Sunday dusk",
        "deity": "Lord Ganesha / Matsya Avatar"},
    8: {"planet": "Saturn", "beej": "Om Praam Preem Praum Sah Shanaye Namah",
        "japa": "23,000 in 40 days", "best_time": "Saturday dusk",
        "deity": "Lord Hanuman / Shani / Bhairava"},
    9: {"planet": "Mars", "beej": "Om Kraam Kreem Kraum Sah Bhaumaaya Namah",
        "japa": "10,000 in 40 days", "best_time": "Tuesday morning",
        "deity": "Lord Hanuman / Skanda / Narasimha"},
}

# Karakamsa D9 sign → soul-dharma theme (Jaimini classical)
KARAKAMSA_DHARMA: Dict[str, str] = {
    "Aries":       "Kshatriya-path: leadership, courage, defending dharma; soul learns through pioneering action.",
    "Taurus":      "Arts/food/wealth-dharma: beauty, sustenance, sensual offerings; soul matures through stewardship of resources.",
    "Gemini":      "Teaching, writing, communication; soul's mission = transmit knowledge & translate ideas across worlds.",
    "Cancer":      "Devotional bhakti, mother-care, nurturing; soul-path through emotional surrender & service to family/community.",
    "Leo":         "Kingship, government, devotion to Surya/Vishnu; soul learns dharma through visible authority & generosity.",
    "Virgo":       "Service, healing, analysis, ayurveda; soul refines via humble work, purification & detail.",
    "Libra":       "Harmony, judgment, partnership-dharma; soul learns equilibrium between worldly law & cosmic balance.",
    "Scorpio":     "Occult, transformation, tantra, kundalini; soul matures through crisis, depth-psychology & shadow-work.",
    "Sagittarius": "Guru-path, philosophy, teaching dharma; soul born to be a teacher / philosopher / spiritual guide.",
    "Capricorn":   "Discipline, austerity (tapas), karma-yoga; soul matures through structured renunciation & long sadhana.",
    "Aquarius":    "Mystical / esoteric / humanitarian work; soul-path = serve collective consciousness, break old molds.",
    "Pisces":      "Moksha, sannyasa, ultimate liberation; soul oriented toward dissolution & union with the Divine.",
}

# Lord of 12th-from-Karakamsa-in-D9 → Ishta Devata (classical Jaimini)
PLANET_ISHTA: Dict[str, str] = {
    "Sun":     "Lord Shiva / Surya / Lord Rama (kshatriya solar deity)",
    "Moon":    "Lord Krishna / Goddess Parvati / Gauri (lunar/devi)",
    "Mars":    "Lord Hanuman / Skanda (Kartikeya) / Narasimha",
    "Mercury": "Lord Vishnu (especially Mridu / Krishna form)",
    "Jupiter": "Lord Vishnu / Vamana avatar / Sri Rama / Dakshinamurti",
    "Venus":   "Goddess Lakshmi / Devi / Mahalakshmi",
    "Saturn":  "Lord Hanuman / Shani / Bhairava / Kurma avatar",
    "Rahu":    "Goddess Durga / Goddess Kali (tamasic shakti form)",
    "Ketu":    "Lord Ganesha / Matsya avatar (jnana-karaka)",
}


# ── helpers ────────────────────────────────────────────────────────
def _planet_lon(planets: List[Dict], name: str) -> float | None:
    for p in planets or []:
        if isinstance(p, dict) and p.get("name") == name:
            try:
                return float(p.get("longitude"))
            except Exception:
                return None
    return None


def _planet_sign(planets: List[Dict], name: str) -> str:
    for p in planets or []:
        if isinstance(p, dict) and p.get("name") == name:
            return p.get("sign", "—")
    return "—"


def _planet_house(planets: List[Dict], asc_sign: str) -> Dict[str, int]:
    if asc_sign not in SIGNS:
        return {}
    asc_idx = SIGNS.index(asc_sign)
    out: Dict[str, int] = {}
    for p in planets or []:
        if not isinstance(p, dict):
            continue
        sgn, nm = p.get("sign"), p.get("name")
        if sgn in SIGNS and nm:
            out[nm] = ((SIGNS.index(sgn) - asc_idx + 12) % 12) + 1
    return out


def _occupants(planets: List[Dict], asc_sign: str, house_num: int) -> List[str]:
    h = _planet_house(planets, asc_sign)
    return sorted([nm for nm, hn in h.items() if hn == house_num])


def _compute_atmakaraka(planets: List[Dict]) -> str | None:
    """AK = highest degrees-in-sign among 7 chara karakas (Sun..Saturn).
    Rahu reversed (30 - deg). Excludes Ketu in standard 7-karaka scheme."""
    candidates: List[Tuple[str, float]] = []
    for nm in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"):
        lon = _planet_lon(planets, nm)
        if lon is None:
            return None
        candidates.append((nm, lon % 30.0))
    if not candidates:
        return None
    candidates.sort(key=lambda x: x[1], reverse=True)
    return candidates[0][0]


def _karakamsa_d9_sign(kundli: Dict, ak_name: str) -> str | None:
    d9 = (kundli.get("divisionalCharts") or {}).get("D9") \
        or (kundli.get("divisionalCharts") or {}).get("d9")
    if not isinstance(d9, dict):
        return None
    for plist_key in ("planets", "Planets"):
        plist = d9.get(plist_key)
        if isinstance(plist, list):
            for pp in plist:
                if isinstance(pp, dict) and pp.get("name") == ak_name:
                    s = pp.get("sign")
                    if s in SIGNS:
                        return s
    return None


# ── main ──────────────────────────────────────────────────────────
def compute_spirituality_bundle(kundli: Dict[str, Any], dob: str,
                                 driver: int, conductor: int) -> Dict[str, Any]:
    """T11 Spirituality bundle. Hard data gate; never fabricates."""
    out: Dict[str, Any] = {"available": False}
    if not isinstance(kundli, dict):
        out["reason"] = "no kundli"
        return out
    asc = kundli.get("ascendant")
    planets = kundli.get("planets", []) or []
    if not asc or asc not in SIGNS:
        out["reason"] = f"ascendant missing or unknown ({asc!r})"
        return out
    if not isinstance(planets, list) or len(planets) < 9:
        out["reason"] = f"planets list incomplete (n={len(planets) if isinstance(planets, list) else 0})"
        return out
    required = {"Sun", "Moon", "Jupiter", "Mars", "Venus", "Mercury", "Saturn", "Rahu", "Ketu"}
    pn = {p.get("name") for p in planets if isinstance(p, dict)}
    missing = required - pn
    if missing:
        out["reason"] = f"missing required grahas: {sorted(missing)}"
        return out

    asc_idx = SIGNS.index(asc)
    p_house = _planet_house(planets, asc)

    def _hb(num: int) -> Dict[str, Any]:
        sign = SIGNS[(asc_idx + num - 1) % 12]
        lord = SIGN_LORD.get(sign, "—")
        occ = _occupants(planets, asc, num)
        return {
            "house": num, "sign": sign, "lord": lord,
            "lord_house": p_house.get(lord, 0),
            "lord_sign": _planet_sign(planets, lord),
            "occupants": occ, "occupants_count": len(occ),
        }

    fourth = _hb(4)
    eighth = _hb(8)
    ninth = _hb(9)
    twelfth = _hb(12)

    # ── 1. Moksha Trikona (4-8-12) audit ─────────────────────────
    # Score: each of 4/8/12 contributes 0-33 points.
    #   - lord placed in own/exalted house (not in 6/8/12 dusthana for 4) → +20
    #   - benefic occupant (Jup/Ven/Mer-unaffl) → +13
    moksha_score = 0
    moksha_notes: List[str] = []
    benefics = {"Jupiter", "Venus", "Mercury"}
    moksha_karakas = {"Saturn", "Ketu", "Jupiter"}

    for blk, weight in ((fourth, 33), (eighth, 33), (twelfth, 34)):
        sub = 0
        # Lord well-placed?
        if blk["lord_house"] in (KENDRA | TRIKONA):
            sub += int(weight * 0.6)
            moksha_notes.append(
                f"H{blk['house']} lord ({blk['lord']}) in H{blk['lord_house']} — strong"
            )
        elif blk["lord_house"] in DUSTHANA and blk["house"] != blk["lord_house"]:
            moksha_notes.append(
                f"H{blk['house']} lord ({blk['lord']}) in dusthana H{blk['lord_house']} — weak"
            )
        else:
            sub += int(weight * 0.25)
        # Moksha-karaka occupant?
        mk_occ = [o for o in blk["occupants"] if o in moksha_karakas]
        ben_occ = [o for o in blk["occupants"] if o in benefics]
        if mk_occ:
            sub += int(weight * 0.3)
            moksha_notes.append(
                f"H{blk['house']} occupied by moksha-karaka {', '.join(mk_occ)} — spiritual lift"
            )
        if ben_occ and not mk_occ:
            sub += int(weight * 0.15)
        moksha_score += min(sub, weight)

    moksha_score = min(moksha_score, 100)
    if moksha_score >= 70:
        moksha_verdict = "STRONG — natural pull toward moksha / sadhana / dharma-marga"
    elif moksha_score >= 40:
        moksha_verdict = "MODERATE — spiritual awakening builds with conscious sadhana"
    else:
        moksha_verdict = "BUILDING — moksha-pursuit requires structured discipline & guru guidance"

    moksha_block = {
        "fourth": fourth, "eighth": eighth, "twelfth": twelfth,
        "score": moksha_score, "verdict": moksha_verdict,
        "notes": moksha_notes[:6],
    }

    # ── 2. Atmakaraka + Karakamsa ────────────────────────────────
    ak_name = _compute_atmakaraka(planets)
    if not ak_name:
        out["reason"] = "atmakaraka calc failed (longitude missing)"
        return out
    karakamsa_sign = _karakamsa_d9_sign(kundli, ak_name)
    karakamsa_lord = SIGN_LORD.get(karakamsa_sign or "", "—")
    dharma_theme = KARAKAMSA_DHARMA.get(karakamsa_sign or "",
                                         "Soul-dharma theme requires D9 navamsha for Karakamsa.")

    karakamsa_block = {
        "atmakaraka": ak_name,
        "atmakaraka_house": p_house.get(ak_name, 0),
        "atmakaraka_sign": _planet_sign(planets, ak_name),
        "karakamsa_sign": karakamsa_sign or "—",
        "karakamsa_lord": karakamsa_lord,
        "dharma_theme": dharma_theme,
    }

    # ── 3. Ishta Devata (classical: lord of 12th from Karakamsa in D9) ──
    if karakamsa_sign:
        ks_idx = SIGNS.index(karakamsa_sign)
        twelfth_from_ks = SIGNS[(ks_idx + 11) % 12]
        ishta_lord = SIGN_LORD.get(twelfth_from_ks, "—")
    else:
        twelfth_from_ks = "—"
        ishta_lord = "—"
    ishta_deity = PLANET_ISHTA.get(ishta_lord,
                                    "Ishta Devata requires D9 chart for classical Karakamsa method.")

    ishta_block = {
        "method": "Lord of 12th-from-Karakamsa in D9 (classical Jaimini)",
        "twelfth_from_karakamsa": twelfth_from_ks,
        "ishta_lord": ishta_lord,
        "deity": ishta_deity,
        "fallback_driver_deity": DRIVER_BEEJ.get(driver, {}).get("deity", "—"),
    }

    # ── 4. Kuldevta (9th house — lineage deity) ──────────────────
    kuldevta_lord = ninth["lord"]
    kuldevta_deity = PLANET_ISHTA.get(kuldevta_lord, "—")
    kul_block = {
        **ninth,
        "kuldevta_via": "9th house lord (lineage deity)",
        "kuldevta_lord": kuldevta_lord,
        "deity": kuldevta_deity,
        "guidance": ("Worship of lineage deity activates 9th house — father's blessings, "
                      "guru-grace, dharmic luck. Visit kul-mandir at least 1× per year."),
    }

    # ── 5. Mantra Sadhana (numerology + planet beej) ─────────────
    db = DRIVER_BEEJ.get(driver, {})
    mantra_block = {
        "driver_planet": db.get("planet", "—"),
        "beej_mantra": db.get("beej", "—"),
        "japa_target": db.get("japa", "—"),
        "best_time": db.get("best_time", "—"),
        "primary_deity": db.get("deity", "—"),
        "synergy_note": (
            f"Combine driver-{driver} planet sadhana with Karakamsa-{karakamsa_sign or 'soul'} "
            f"theme: morning beej × {db.get('japa', 'daily japa')}, evening contemplation on "
            f"dharma_theme. Within 40 days expect inner shift; within 90 days outer events align."
        ),
    }

    # ── 6. Saturn-Ketu Vairagya (detachment) score ──────────────
    sat_h = p_house.get("Saturn", 0)
    ket_h = p_house.get("Ketu", 0)
    twelfth_occ_count = twelfth["occupants_count"]
    vairagya = 0
    vai_notes: List[str] = []
    # Saturn in 4/8/12 → strong vairagya signature
    if sat_h in DUSTHANA:
        vairagya += 30
        vai_notes.append(f"Saturn in H{sat_h} — natural detachment, austerity-prone")
    elif sat_h in (1, 9, 10):
        vairagya += 20
        vai_notes.append(f"Saturn in H{sat_h} — disciplined, dharmic structure")
    # Ketu in 1/4/8/9/12 → moksha karaka active
    if ket_h in (1, 4, 8, 9, 12):
        vairagya += 30
        vai_notes.append(f"Ketu in H{ket_h} — moksha-karaka activated, past-life sadhana")
    # 12th house populated → withdrawal, ashram, charity
    if twelfth_occ_count >= 1:
        vairagya += 20
        vai_notes.append(f"H12 occupied by {', '.join(twelfth['occupants'])} — withdrawal, ashram")
    # Jupiter in trine → guru-grace
    jup_h = p_house.get("Jupiter", 0)
    if jup_h in TRIKONA:
        vairagya += 20
        vai_notes.append(f"Jupiter in trine H{jup_h} — guru's grace flows naturally")
    vairagya = min(vairagya, 100)
    if vairagya >= 65:
        vai_verdict = "HIGH VAIRAGYA — soul ready for serious sadhana / sannyasa-leaning"
    elif vairagya >= 35:
        vai_verdict = "MODERATE VAIRAGYA — practical-spiritual balance, householder-yogi path"
    else:
        vai_verdict = "BUILDING VAIRAGYA — worldly themes dominant; sadhana grows slowly"
    vairagya_block = {
        "saturn_house": sat_h, "ketu_house": ket_h,
        "twelfth_occupants": twelfth["occupants"],
        "jupiter_house": jup_h,
        "score": vairagya, "verdict": vai_verdict,
        "notes": vai_notes,
    }

    # ── 7. Synthesis ─────────────────────────────────────────────
    synth_lines = [
        f"Atmakaraka {ak_name} (H{p_house.get(ak_name, 0)}, {_planet_sign(planets, ak_name)}) → "
        f"Karakamsa {karakamsa_sign or '—'} ({karakamsa_lord}) — {dharma_theme.split(';')[0]}.",
        f"Ishta Devata: {ishta_deity} (via {ishta_lord} = lord of {twelfth_from_ks}, 12th-from-Karakamsa).",
        f"Kuldevta: {kuldevta_deity} (via 9th-lord {kuldevta_lord}).",
        f"Moksha Trikona score: {moksha_score}/100 — {moksha_verdict.split('—')[0].strip()}.",
        f"Vairagya score: {vairagya}/100 — {vai_verdict.split('—')[0].strip()}.",
    ]
    synthesis_block = {
        "summary_lines": synth_lines,
        "starter_90day": [
            f"Days 1-21: Establish daily {db.get('beej', 'beej mantra')} japa "
            f"({db.get('japa', '40-day target')}) at {db.get('best_time', 'sunrise')}.",
            f"Days 22-45: Add weekly worship of Ishta Devata ({ishta_deity.split('/')[0].strip()}) "
            f"on {db.get('best_time', 'designated weekday')}.",
            f"Days 46-70: Visit kul-mandir of Kuldevta ({kuldevta_deity.split('/')[0].strip()}); "
            f"begin contemplation on Karakamsa-{karakamsa_sign or 'dharma'} theme.",
            f"Days 71-90: Long-form sadhana — silent retreat 3-7 days, charity in 12th-house "
            f"theme (food/anonymous-donation/foreign-spiritual-cause).",
        ],
        "verdict_token": ("STRONG-MOKSHA-PATH" if moksha_score >= 70 else
                           "BALANCED-DHARMA-PATH" if moksha_score >= 40 else
                           "BUILDING-DHARMA-PATH"),
    }

    out.update({
        "available": True,
        "moksha_trikona": moksha_block,
        "karakamsa": karakamsa_block,
        "ishta_devata": ishta_block,
        "kuldevta": kul_block,
        "mantra_sadhana": mantra_block,
        "vairagya": vairagya_block,
        "synthesis": synthesis_block,
    })
    return out
