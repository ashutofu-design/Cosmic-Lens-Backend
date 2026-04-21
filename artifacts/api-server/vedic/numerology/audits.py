"""
Tier 4 — Personal Audits / Doshas (Life Mastery Report)
Wraps existing dosh_engine + dosh_deep into a 9-card audit bundle.

Inputs: full kundli dict (with `planets`, `ascendant`, `nakshatra`).
Outputs: dict with 9 audit cards + summary score.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

log = logging.getLogger(__name__)

SIGNS = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
         "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]


def _sign_idx(name: str) -> Optional[int]:
    if not name:
        return None
    for i, s in enumerate(SIGNS):
        if s.lower() == name.lower():
            return i
    return None


def _current_saturn_sign() -> Optional[int]:
    """Get current Saturn sign index (0-11) for Sade Sati / Ashtama checks."""
    try:
        import swisseph as swe
        from datetime import datetime, timezone
        now = datetime.now(tz=timezone.utc)
        jd = swe.julday(now.year, now.month, now.day,
                        now.hour + now.minute / 60.0)
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL
        res, _ = swe.calc_ut(jd, swe.SATURN, flags)
        return int((res[0] % 360) // 30)
    except Exception as e:
        log.warning("current_saturn_sign failed: %s", e)
        return None


# ─────────────────────────────────────────────────────────────────────
# Static remedy fallbacks for the 9 dosha cards (already shipped via
# dosh_engine remedies, but we add prose intros for storytelling cards)
# ─────────────────────────────────────────────────────────────────────
DOSH_INTRO = {
    "manglik": (
        "Mangal Dosh is when Mars sits in the 1st, 4th, 7th, 8th or 12th house from "
        "Lagna, Moon, or Venus — its fiery energy can stress marriage and partnership. "
        "Several cancellations exist (Mars in own/exalted sign, with Jupiter/Moon, etc.)."
    ),
    "kaal_sarp": (
        "Kaal Sarp Dosh forms when ALL 7 planets sit between Rahu and Ketu — a "
        "karmic hourglass that delays results in early life but compounds them later. "
        "12 named variants (Anant, Kulik, Vasuki, etc.) refine the impact area."
    ),
    "pitru": (
        "Pitru Dosh marks unresolved ancestor karma — usually shown by Sun/Rahu in 9th, "
        "Moon afflicted, or Saturn near luminaries. Manifests as repeated obstacles in "
        "areas where the bloodline carries debt (children, dharma, public work)."
    ),
    "guru_chandal": (
        "Guru Chandal forms when Jupiter conjuncts Rahu/Ketu — wisdom mixed with "
        "shadow. Excellent for non-linear creativity, dangerous for orthodox guidance."
    ),
    "grahan": (
        "Grahan Dosh = Sun or Moon conjunct Rahu/Ketu — your luminaries are 'eclipsed'. "
        "Affects identity (Sun) or emotional clarity (Moon) until consciously cleansed."
    ),
    "daridra": (
        "Daridra Dosh = wealth-house lords debilitated/combust — chronic resource leakage "
        "that feels like 'always running but never accumulating'."
    ),
    "angarak": (
        "Angarak Dosh = Mars-Rahu conjunction — explosive temper, accident-proneness, "
        "high-courage / high-impulse combination."
    ),
    "shrapit": (
        "Shrapit Dosh = Saturn-Rahu conjunction — slow, heavy karma marked by long delays "
        "and sudden upheavals. The classical 'curse-yoga' that demands sustained tapasya."
    ),
    "kemadruma": (
        "Kemadruma forms when Moon has no planetary support in adjacent houses — "
        "psychological isolation, mood-vulnerability, self-doubt despite outer success. "
        "Cancellations: Moon in own sign, exalted, or with strong aspects."
    ),
}


# ─────────────────────────────────────────────────────────────────────
# Main aggregator
# ─────────────────────────────────────────────────────────────────────
def compute_audits_bundle(kundli: Dict[str, Any], dob: str,
                           tob: Optional[str], driver: int) -> Dict[str, Any]:
    """Compute all Tier 4 audit data for a single kundli."""
    if not kundli or not kundli.get("planets"):
        return {"available": False, "reason": "no kundli"}

    planets = kundli.get("planets") or []
    nakshatra = kundli.get("nakshatra") or ""
    ascendant = kundli.get("ascendant") or ""
    lagna_idx = _sign_idx(ascendant)

    # ── 1. Run analyze_doshas (9 standard doshas) ─────────────────
    primary: Dict[str, Any] = {}
    try:
        from dosh_engine import analyze_doshas
        primary = analyze_doshas(planets, nakshatra)
    except Exception as e:
        log.warning("analyze_doshas failed: %s", e)
        primary = {"dosh_list": [], "active_count": 0, "mild_count": 0, "none_count": 9}

    by_key = {d["key"]: d for d in primary.get("dosh_list", [])}

    # ── 2. Run detect_deep_doshas (BPHS-precise rules) ────────────
    deep: List[Dict[str, Any]] = []
    if lagna_idx is not None:
        try:
            from vedic.doshas.dosh_deep import detect_deep_doshas
            sat_sign = _current_saturn_sign()
            deep = detect_deep_doshas(planets, lagna_idx, sat_sign, nakshatra) or []
        except Exception as e:
            log.warning("detect_deep_doshas failed: %s", e)

    # Group deep doshas by family (mangal, sade-sati, kantaka, vish, karaka, grahan, shrapit, pitra, nadi)
    deep_by_family: Dict[str, List[Dict[str, Any]]] = {}
    for d in deep:
        nm = (d.get("name") or "").lower()
        fam = "other"
        if "mangal" in nm:
            fam = "mangal"
        elif "sade" in nm or "sadesati" in nm or "sade sati" in nm:
            fam = "sadesati"
        elif "kantaka" in nm or "ashtama" in nm:
            fam = "shani_extra"
        elif "vish" in nm:
            fam = "vish"
        elif "karaka" in nm or "putra" in nm or "matri" in nm or "bhratri" in nm or "pitri" in nm:
            fam = "karaka"
        elif "grahan" in nm:
            fam = "grahan"
        elif "shrapit" in nm:
            fam = "shrapit"
        elif "pitra" in nm or "pitru" in nm:
            fam = "pitra"
        elif "nadi" in nm:
            fam = "nadi"
        deep_by_family.setdefault(fam, []).append(d)

    # ── 3. Severity tally ─────────────────────────────────────────
    high_cnt = sum(1 for d in deep if d.get("severity") == "HIGH")
    med_cnt = sum(1 for d in deep if d.get("severity") == "MEDIUM")
    info_cnt = sum(1 for d in deep if d.get("severity") == "INFO")

    # ── 4. Build 9 audit cards ────────────────────────────────────
    # NOTE: `primary_key` indexes the `analyze_doshas` output (e.g. "manglik"),
    # while `family_key` indexes the deep-dosha classification (e.g. "mangal").
    # The two taxonomies differ slightly — keep them mapped explicitly here.
    def _card(card_key: str, primary_key: str, family_key: str,
              headline_default: str) -> Dict[str, Any]:
        prim = by_key.get(primary_key, {})
        deep_match = deep_by_family.get(family_key, [])
        status = prim.get("status", "None")
        # Promote status if deep audit found HIGH severity
        if any(d.get("severity") == "HIGH" for d in deep_match):
            status = "Active"
        elif status == "None" and any(d.get("severity") == "MEDIUM" for d in deep_match):
            status = "Mild"
        return {
            "key": card_key,
            "name": prim.get("name", headline_default),
            "icon": prim.get("icon", "•"),
            "status": status,
            "headline": prim.get("headline", ""),
            "description": prim.get("description", ""),
            "remedies": prim.get("remedies", []),
            "intro": DOSH_INTRO.get(card_key, ""),
            "deep_findings": [
                {"name": d.get("name"), "sev": d.get("severity"), "detail": d.get("detail")}
                for d in deep_match
            ],
        }

    cards = {
        "mangal":       _card("mangal",       "manglik",      "mangal",       "Mangal Dosh"),
        "kaal_sarp":    _card("kaal_sarp",    "kaal_sarp",    "kaal_sarp",    "Kaal Sarp Dosh"),
        "pitru":        _card("pitru",        "pitru",        "pitra",        "Pitru Dosh"),
        "guru_chandal": _card("guru_chandal", "guru_chandal", "guru_chandal", "Guru Chandal Dosh"),
        "grahan":       _card("grahan",       "grahan",       "grahan",       "Grahan Dosh"),
        "daridra":      _card("daridra",      "daridra",      "daridra",      "Daridra Dosh"),
        "angarak":      _card("angarak",      "angarak",      "angarak",      "Angarak Dosh"),
        "shrapit":      _card("shrapit",      "shrapit",      "shrapit",      "Shrapit Dosh"),
        "kemadruma":    _card("kemadruma",    "kemadruma",    "kemadruma",    "Kemadruma Dosh"),
    }

    # ── 5. Shani-extra block (Ashtama / Kantaka — separate from Sade Sati) ──
    shani_findings = deep_by_family.get("shani_extra", []) + deep_by_family.get("sadesati", [])
    shani_block = {
        "available": bool(shani_findings),
        "items": [
            {"name": d.get("name"), "sev": d.get("severity"), "detail": d.get("detail")}
            for d in shani_findings
        ],
    }

    # ── 6. Karaka afflictions (Putra/Matri/Bhratri/Pitri) ─────────
    karaka_findings = deep_by_family.get("karaka", [])
    karaka_block = {
        "available": bool(karaka_findings),
        "items": [
            {"name": d.get("name"), "sev": d.get("severity"), "detail": d.get("detail")}
            for d in karaka_findings
        ],
    }

    # ── 7. Vish Yog (Moon-Saturn) standalone audit ────────────────
    vish_findings = deep_by_family.get("vish", [])
    vish_block = {
        "available": bool(vish_findings),
        "items": [
            {"name": d.get("name"), "sev": d.get("severity"), "detail": d.get("detail")}
            for d in vish_findings
        ],
    }

    # ── 8. Audit summary score ────────────────────────────────────
    # Recount from FINAL card statuses so primary + deep promotion are
    # collapsed into a single coherent 9-card tally (totals always == 9).
    active_total = sum(1 for c in cards.values() if c["status"] == "Active")
    mild_total   = sum(1 for c in cards.values() if c["status"] == "Mild")
    clear_total  = sum(1 for c in cards.values() if c["status"] == "None")

    # Health score 0-100 (higher = cleaner chart)
    score = max(0, 100 - (active_total * 12) - (mild_total * 5))
    if score >= 80:
        verdict = "EXCELLENT — light karmic load"
    elif score >= 60:
        verdict = "GOOD — manageable, normal life-friction"
    elif score >= 40:
        verdict = "MIXED — multiple active areas, focused remedies needed"
    else:
        verdict = "INTENSIVE — strong tapasya recommended"

    return {
        "available": True,
        "summary": {
            "active_count": active_total,
            "mild_count": mild_total,
            "clear_count": clear_total,
            "deep_high": high_cnt,
            "deep_medium": med_cnt,
            "deep_info": info_cnt,
            "score": score,
            "verdict": verdict,
        },
        "cards": cards,
        "shani_extra": shani_block,
        "karaka_afflictions": karaka_block,
        "vish_yog": vish_block,
    }


if __name__ == "__main__":  # pragma: no cover — smoke test
    from kundli_engine import calculate_kundli
    k = calculate_kundli({
        "name": "Rahul Sharma", "day": 15, "month": 5, "year": 1990,
        "hour": 10, "minute": 30, "ampm": "AM",
        "lat": 28.6139, "lon": 77.2090, "tz": 5.5, "place": "New Delhi",
    })
    b = compute_audits_bundle(k, "1990-05-15", "10:30", driver=6)
    print("AVAILABLE:", b.get("available"))
    print("SUMMARY:", b.get("summary"))
    print("CARDS keys:", list(b.get("cards", {}).keys()))
    for k, v in b.get("cards", {}).items():
        print(f"  {k}: status={v['status']} deep_findings={len(v['deep_findings'])}")
    print("SHANI EXTRA:", b.get("shani_extra"))
    print("KARAKA:", b.get("karaka_afflictions"))
    print("VISH:", b.get("vish_yog"))
