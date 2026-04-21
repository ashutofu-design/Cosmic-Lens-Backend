"""
Tier 5 — Relationships & Compatibility (Life Mastery Report — single-side)
Combines:
  • Vedic Ashtakoot single-side profile (compute_phase_p)
  • Numerology partner-fit (NUMBER_FRIENDS / NUMBER_ENEMIES)
  • Ideal-partner Nakshatra suggestions (Yoni harmony, Gana compatibility)
  • Mangal need flag (do you need a Mangal-partner to balance Mars?)
  • Marriage stability (Upapada Lagna proxy)

Inputs: kundli dict, dob (str), driver (int), conductor (int)
Output: dict ready for Tier 5 renderer.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

log = logging.getLogger(__name__)

# ─── Taxonomy aliases — phase_p uses abbreviations, our 27-name table uses full forms ───
# Map FROM phase_p's short form TO our canonical full-form (NAKSHATRA_PROFILE keys).
NAKSHATRA_ALIAS = {
    "P.Phalguni": "Purva Phalguni", "U.Phalguni": "Uttara Phalguni",
    "P.Ashadha": "Purva Ashadha",   "U.Ashadha":  "Uttara Ashadha",
    "P.Bhadrapada": "Purva Bhadrapada", "U.Bhadrapada": "Uttara Bhadrapada",
    "Mrigashira": "Mrigashirsha",
}
# Map FROM phase_p yoni form TO our local yoni table key.
YONI_ALIAS = {"Serpent": "Snake"}


def _canon_nak(n: str) -> str:
    return NAKSHATRA_ALIAS.get(n, n) if n else n


def _canon_yoni(y: str) -> str:
    return YONI_ALIAS.get(y, y) if y else y


# ─── Yoni friendship table (14 animals; from compat/phase_p) ───────────
YONI_FRIENDS = {
    "Horse": ["Horse", "Buffalo"], "Elephant": ["Elephant", "Sheep"],
    "Sheep": ["Elephant", "Sheep"], "Snake": ["Snake", "Mongoose"],
    "Dog": ["Dog", "Deer"], "Cat": ["Cat"], "Rat": ["Rat", "Cow"],
    "Cow": ["Cow", "Tiger"], "Buffalo": ["Buffalo", "Horse"],
    "Tiger": ["Tiger", "Cow"], "Deer": ["Deer", "Dog"],
    "Monkey": ["Monkey", "Sheep"], "Mongoose": ["Snake", "Mongoose"],
    "Lion": ["Lion"],
}
YONI_ENEMIES = {
    "Horse": ["Buffalo"], "Elephant": ["Lion"], "Sheep": ["Monkey", "Tiger"],
    "Snake": ["Mongoose"], "Dog": ["Deer"], "Cat": ["Rat"],
    "Rat": ["Cat"], "Cow": ["Tiger"], "Buffalo": ["Horse"],
    "Tiger": ["Cow", "Sheep"], "Deer": ["Dog"], "Monkey": ["Sheep"],
    "Mongoose": ["Snake"], "Lion": ["Elephant"],
}

# ─── 27 Nakshatras with their Yoni + Gana attributes (for partner suggestions) ───
NAKSHATRA_PROFILE = {
    "Ashwini": {"yoni": "Horse", "gana": "Deva"},
    "Bharani": {"yoni": "Elephant", "gana": "Manushya"},
    "Krittika": {"yoni": "Sheep", "gana": "Rakshasa"},
    "Rohini": {"yoni": "Snake", "gana": "Manushya"},
    "Mrigashirsha": {"yoni": "Snake", "gana": "Deva"},
    "Ardra": {"yoni": "Dog", "gana": "Manushya"},
    "Punarvasu": {"yoni": "Cat", "gana": "Deva"},
    "Pushya": {"yoni": "Sheep", "gana": "Deva"},
    "Ashlesha": {"yoni": "Cat", "gana": "Rakshasa"},
    "Magha": {"yoni": "Rat", "gana": "Rakshasa"},
    "Purva Phalguni": {"yoni": "Rat", "gana": "Manushya"},
    "Uttara Phalguni": {"yoni": "Cow", "gana": "Manushya"},
    "Hasta": {"yoni": "Buffalo", "gana": "Deva"},
    "Chitra": {"yoni": "Tiger", "gana": "Rakshasa"},
    "Swati": {"yoni": "Buffalo", "gana": "Deva"},
    "Vishakha": {"yoni": "Tiger", "gana": "Rakshasa"},
    "Anuradha": {"yoni": "Deer", "gana": "Deva"},
    "Jyeshtha": {"yoni": "Deer", "gana": "Rakshasa"},
    "Mula": {"yoni": "Dog", "gana": "Rakshasa"},
    "Purva Ashadha": {"yoni": "Monkey", "gana": "Manushya"},
    "Uttara Ashadha": {"yoni": "Mongoose", "gana": "Manushya"},
    "Shravana": {"yoni": "Monkey", "gana": "Deva"},
    "Dhanishta": {"yoni": "Lion", "gana": "Rakshasa"},
    "Shatabhisha": {"yoni": "Horse", "gana": "Rakshasa"},
    "Purva Bhadrapada": {"yoni": "Lion", "gana": "Manushya"},
    "Uttara Bhadrapada": {"yoni": "Cow", "gana": "Manushya"},
    "Revati": {"yoni": "Elephant", "gana": "Deva"},
}

# Driver-number deity / planet (used for explanatory prose)
DRIVER_PLANET = {
    1: "Sun", 2: "Moon", 3: "Jupiter", 4: "Rahu", 5: "Mercury",
    6: "Venus", 7: "Ketu", 8: "Saturn", 9: "Mars",
}


def _is_mangal_dosh(planets: List[Dict[str, Any]], lagna_idx: Optional[int]) -> bool:
    """Quick Mangal-dosh check — Mars in 1/4/7/8/12 from Lagna or Moon."""
    if not planets:
        return False
    mars = next((p for p in planets if p.get("name") == "Mars"), None)
    if not mars:
        return False
    bad_houses = {1, 4, 7, 8, 12}
    if mars.get("house") in bad_houses:
        return True
    # Also check from Moon
    moon = next((p for p in planets if p.get("name") == "Moon"), None)
    if moon and isinstance(moon.get("longitude"), (int, float)) \
            and isinstance(mars.get("longitude"), (int, float)):
        moon_sign = int((moon["longitude"] % 360) // 30)
        mars_sign = int((mars["longitude"] % 360) // 30)
        rel = ((mars_sign - moon_sign) % 12) + 1
        if rel in bad_houses:
            return True
    return False


def compute_relationships_bundle(kundli: Dict[str, Any], dob: str,
                                  driver: int, conductor: int,
                                  name: str) -> Dict[str, Any]:
    """Compute single-side relationship/compatibility bundle for Tier 5."""
    if not kundli or not kundli.get("planets"):
        return {"available": False, "reason": "no kundli"}

    planets = kundli.get("planets") or []
    lagna_idx = None
    SIGNS = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
             "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
    asc = kundli.get("ascendant") or ""
    for i, s in enumerate(SIGNS):
        if s.lower() == asc.lower():
            lagna_idx = i
            break

    # ── 1. Phase P single-side compatibility profile ──────────────
    phase_p: Dict[str, Any] = {}
    try:
        from vedic.compat.phase_p import compute_phase_p
        phase_p = compute_phase_p(kundli)
    except Exception as e:
        log.warning("compute_phase_p failed: %s", e)
        phase_p = {"available": False}

    if not phase_p.get("available"):
        return {"available": False, "reason": phase_p.get("reason", "phase_p missing")}

    # Canonicalise to the full-form names used in our local taxonomy tables.
    moon_nak = _canon_nak(phase_p.get("moon_nakshatra") or "")
    a8 = phase_p.get("p1_ashtakoot_attrs", {})
    yoni_detail = phase_p.get("p5_yoni_detail", {})
    rajju = phase_p.get("p7_rajju_type", {})
    self_yoni = _canon_yoni(yoni_detail.get("yoni_animal", "?"))
    self_gana = a8.get("Gana", "?")
    self_nadi = a8.get("Nadi", "?")
    self_varna = a8.get("Varna", "?")
    self_vashya = a8.get("Vashya", "?")
    self_bhakoot = a8.get("Bhakoot_sign", "?")
    self_tara_idx = a8.get("Tara_index", None)

    compat_dna = {
        "moon_nakshatra": moon_nak,
        "moon_pada": phase_p.get("moon_pada"),
        "moon_sign": phase_p.get("moon_sign"),
        "varna": self_varna,
        "vashya": self_vashya,
        "tara_index": self_tara_idx,
        "yoni": self_yoni,
        "graha_maitri_lord": a8.get("Graha_Maitri_lord"),
        "gana": self_gana,
        "bhakoot_sign": self_bhakoot,
        "nadi": self_nadi,
        "rajju": rajju.get("Rajju"),
        "rajju_dosha_if_same": rajju.get("dosha_if_same_with_partner"),
        "linga": phase_p.get("p6_linga_gana", {}).get("Linga"),
    }

    # ── 2. Yoni temperament ───────────────────────────────────────
    yoni_block = {
        "self_yoni": self_yoni,
        "gender": yoni_detail.get("yoni_gender"),
        "compatible": yoni_detail.get("compatible_yonis", []),
        "incompatible": yoni_detail.get("incompatible_yonis", []),
    }

    # ── 3. Numerology partner-fit ─────────────────────────────────
    try:
        from .phase_s import NUMBER_FRIENDS, NUMBER_ENEMIES
        friend_drivers = NUMBER_FRIENDS.get(driver, []) or []
        enemy_drivers = NUMBER_ENEMIES.get(driver, []) or []
        all_nums = set(range(1, 10))
        neutral_drivers = sorted(all_nums - set(friend_drivers) - set(enemy_drivers) - {driver})
        friend_conductors = NUMBER_FRIENDS.get(conductor, []) or []
        enemy_conductors = NUMBER_ENEMIES.get(conductor, []) or []
    except Exception as e:
        log.warning("phase_s numerology lookup failed: %s", e)
        friend_drivers = enemy_drivers = neutral_drivers = []
        friend_conductors = enemy_conductors = []

    partner_numerology = {
        "self_driver": driver,
        "self_conductor": conductor,
        "self_planet": DRIVER_PLANET.get(driver, "—"),
        "best_partner_drivers": friend_drivers,
        "challenging_partner_drivers": enemy_drivers,
        "neutral_partner_drivers": neutral_drivers,
        "best_partner_conductors": friend_conductors,
        "challenging_partner_conductors": enemy_conductors,
    }

    # ── 4. Ideal partner Nakshatras (Yoni-friend AND non-Rakshasa-Deva clash) ─
    ideal_nakshatras: List[Dict[str, str]] = []
    for nak, info in NAKSHATRA_PROFILE.items():
        if nak == moon_nak:
            continue
        n_yoni = info["yoni"]
        n_gana = info["gana"]
        # Yoni must be in friends (or same)
        yoni_ok = n_yoni == self_yoni or n_yoni in YONI_FRIENDS.get(self_yoni, [])
        if not yoni_ok:
            continue
        # Gana clash: Deva-Rakshasa is bad
        gana_clash = (
            (self_gana == "Deva" and n_gana == "Rakshasa")
            or (self_gana == "Rakshasa" and n_gana == "Deva")
        )
        if gana_clash:
            continue
        ideal_nakshatras.append({
            "nakshatra": nak, "yoni": n_yoni, "gana": n_gana,
            "match_quality": "EXCELLENT" if n_yoni == self_yoni else "GOOD",
        })
    # Cap to top 8 for the report
    ideal_nakshatras.sort(key=lambda x: 0 if x["match_quality"] == "EXCELLENT" else 1)
    ideal_nakshatras = ideal_nakshatras[:8]

    # ── 5. Mangal need (do YOU have Mangal-dosh? if yes you need Mangal-partner) ─
    self_has_mangal = _is_mangal_dosh(planets, lagna_idx)
    mangal_block = {
        "self_has_mangal_dosh": self_has_mangal,
        "guidance": (
            "You carry Mangal Dosh — partner ideally should also have Mangal Dosh "
            "(or its proper cancellation), so that Mars-energy mirrors and neutralises. "
            "A non-Mangal partner can experience friction in early marriage years."
            if self_has_mangal else
            "You do NOT carry Mangal Dosh — choose a partner without active Mangal Dosh "
            "for smoothest fit. If they DO have it, ensure the cancellation rules apply."
        ),
    }

    # ── 6. Nadi status ────────────────────────────────────────────
    # phase_p emits Nadi as Vata / Pitta / Kapha (Ayurveda taxonomy used by
    # Ashtakoot in modern engines). Same Nadi between partners = Nadi Dosh.
    nadi_block = {
        "self_nadi": self_nadi,
        "rule": "Same Nadi between partners = Nadi Dosh (classical). Different Nadi = clear.",
        "ideal_partner_nadi": [n for n in ("Vata", "Pitta", "Kapha") if n != self_nadi],
    }

    # ── 7. Marriage stability via Upapada (best-effort) ───────────
    marriage_stability: Dict[str, Any] = {"available": False}
    try:
        from jaimini import compute_arudha_padas, compute_upapada
        ar = compute_arudha_padas(planets, lagna_idx) if lagna_idx is not None else None
        if ar:
            ul = compute_upapada(ar, planets) or {}
            marriage_stability = {
                "available": True,
                "ul_sign": ul.get("ul_sign"),
                "verdict": ul.get("verdict") or "MIXED",
                "occupants_2nd": ul.get("occupants_2nd", []),
            }
    except Exception as e:
        log.warning("upapada calc failed: %s", e)

    # ── 8. Synthesis: ideal partner profile ───────────────────────
    ideal_profile_lines: List[str] = []
    if friend_drivers:
        ideal_profile_lines.append(
            f"Driver number {friend_drivers[0]} (planet: {DRIVER_PLANET.get(friend_drivers[0], '—')})"
        )
    if ideal_nakshatras:
        ideal_profile_lines.append(
            f"Moon-Nakshatra: any of {', '.join(n['nakshatra'] for n in ideal_nakshatras[:3])}"
        )
    ideal_profile_lines.append(
        f"Yoni: {', '.join(YONI_FRIENDS.get(self_yoni, [self_yoni]))}"
    )
    ideal_profile_lines.append(
        f"Avoid: drivers {enemy_drivers if enemy_drivers else '—'}, "
        f"yoni {YONI_ENEMIES.get(self_yoni, [])}"
    )

    ideal_profile = {
        "lines": ideal_profile_lines,
        "self_summary": (
            f"You are a Driver {driver} ({DRIVER_PLANET.get(driver, '—')}) / "
            f"Conductor {conductor} ({DRIVER_PLANET.get(conductor, '—')}) "
            f"with Moon in {moon_nak} (Yoni: {self_yoni}, Gana: {self_gana}, Nadi: {self_nadi})."
        ),
    }

    return {
        "available": True,
        "compat_dna": compat_dna,
        "yoni_temperament": yoni_block,
        "partner_numerology": partner_numerology,
        "ideal_nakshatras": ideal_nakshatras,
        "mangal": mangal_block,
        "nadi": nadi_block,
        "marriage_stability": marriage_stability,
        "ideal_partner_profile": ideal_profile,
    }


if __name__ == "__main__":  # pragma: no cover — smoke test
    from kundli_engine import calculate_kundli
    k = calculate_kundli({
        "name": "Rahul Sharma", "day": 15, "month": 5, "year": 1990,
        "hour": 10, "minute": 30, "ampm": "AM",
        "lat": 28.6139, "lon": 77.2090, "tz": 5.5, "place": "New Delhi",
    })
    b = compute_relationships_bundle(k, "1990-05-15", driver=6, conductor=3,
                                      name="Rahul Sharma")
    print("AVAILABLE:", b.get("available"))
    if b.get("available"):
        print("COMPAT_DNA:", b["compat_dna"])
        print("YONI:", b["yoni_temperament"])
        print("PARTNER_NUMEROLOGY:", b["partner_numerology"])
        print("IDEAL_NAKSHATRAS:", b["ideal_nakshatras"])
        print("MANGAL:", b["mangal"])
        print("NADI:", b["nadi"])
        print("MARRIAGE_STABILITY:", b["marriage_stability"])
        print("IDEAL_PROFILE:", b["ideal_partner_profile"])
