"""
Phase 2.5.11.23 — 7-Chapter Score Derivation
============================================
PURE DETERMINISTIC. NO LLM. Maps engine facts (Ashtakoot + D9 + 7L synastry +
KP marriage promise) onto 7 user-facing chapters, each with:
  - score_0_10            (final user-visible score)
  - drivers   : list[str] (plain-language strengths — feeds LLM prompt as context)
  - cautions  : list[str] (plain-language frictions — feeds LLM prompt)
  - key_facts : dict      (structured anchors LLM MUST cite verbatim)

Chapters (locked):
  ch1 Emotional Compatibility
  ch2 Trust & Loyalty
  ch3 Communication & Conflict
  ch4 Marriage Stability
  ch5 Physical + Emotional Chemistry
  ch6 Family + Practical Life
  ch7 Long-Term Future Direction

Branding: never name AI/LLM. Defensive — never raises on missing inputs.
"""
from __future__ import annotations
from typing import Any

CHAPTER_TITLES = {
    "ch1": "Emotional Compatibility",
    "ch2": "Trust & Loyalty",
    "ch3": "Communication & Conflict",
    "ch4": "Marriage Stability",
    "ch5": "Physical + Emotional Chemistry",
    "ch6": "Family + Practical Life",
    "ch7": "Long-Term Future Direction",
}


def _koot(milan_facts: dict, key: str) -> dict:
    """Return koot dict by key (nadi/gana/bhakut/maitri/yoni/tara/vasya/varna)."""
    if not isinstance(milan_facts, dict):
        return {}
    for k in milan_facts.get("koots") or []:
        if isinstance(k, dict) and k.get("key") == key:
            return k
    return {}


def _koot_norm(milan_facts: dict, key: str) -> float:
    """Return koot score / max as 0.0-1.0. 0.0 if missing."""
    k = _koot(milan_facts, key)
    sc = k.get("score")
    mx = k.get("max")
    if isinstance(sc, (int, float)) and isinstance(mx, (int, float)) and mx > 0:
        return max(0.0, min(1.0, sc / mx))
    return 0.0


def _clamp(x: float) -> float:
    return max(0.0, min(10.0, round(x, 1)))


def _kp_weight(verdict: str | None) -> float:
    """Map KP couple verdict to 0-1 multiplier."""
    return {"STRONG": 1.0, "PARTIAL": 0.6, "WEAK": 0.25}.get(verdict or "", 0.5)


def _ch1_emotional(milan_facts: dict, d9: dict, syn: dict) -> dict[str, Any]:
    """Moon-nakshatra harmony + Tara + Yoni + D9 Venus dignity + nakshatra resonance."""
    drivers: list[str] = []
    cautions: list[str] = []
    key_facts: dict[str, Any] = {}

    tara = _koot_norm(milan_facts, "tara")
    yoni = _koot_norm(milan_facts, "yoni")
    nadi = _koot_norm(milan_facts, "nadi")

    # D9 Venus dignity (both partners)
    p1d9 = (d9 or {}).get("p1") or {}
    p2d9 = (d9 or {}).get("p2") or {}
    v1 = p1d9.get("d9_venus_dignity", "neutral")
    v2 = p2d9.get("d9_venus_dignity", "neutral")
    venus_bonus = 0.0
    if v1 in ("exalted", "own-sign"):
        venus_bonus += 0.7
        drivers.append(f"P1 Venus is {v1} in D9 — natural emotional softness")
    elif v1 in ("debilitated", "enemy-sign"):
        venus_bonus -= 0.5
        cautions.append(f"P1 Venus is {v1} in D9 — affection needs intentional warmth")
    if v2 in ("exalted", "own-sign"):
        venus_bonus += 0.7
        drivers.append(f"P2 Venus is {v2} in D9 — natural emotional softness")
    elif v2 in ("debilitated", "enemy-sign"):
        venus_bonus -= 0.5
        cautions.append(f"P2 Venus is {v2} in D9 — affection needs intentional warmth")

    nak_match = ((syn or {}).get("nakshatra_resonance") or {}).get("count", 0)
    if nak_match >= 1:
        drivers.append(f"Nakshatra-lord resonance: {nak_match} match(es) — quiet karmic familiarity")

    # Score = weighted Tara(2.0) + Yoni(1.5) + Nadi(2.0) + Venus(1.5) + Resonance(1.0) + base 2.0
    raw = 2.0 + (tara * 2.0) + (yoni * 1.5) + (nadi * 2.0) + venus_bonus + min(1.0, nak_match * 0.5)
    if tara < 0.4:
        cautions.append("Tara koot weak — emotional rhythm differs; learn each other's mood-cycles")
    if yoni < 0.5:
        cautions.append("Yoni mismatch — instinctive needs differ; conscious empathy needed")
    if nadi == 0.0:
        cautions.append("Nadi dosha present — emotional health needs deliberate care")

    key_facts["tara_score"] = _koot(milan_facts, "tara").get("score")
    key_facts["yoni_score"] = _koot(milan_facts, "yoni").get("score")
    key_facts["nadi_score"] = _koot(milan_facts, "nadi").get("score")
    key_facts["p1_venus_d9"] = v1
    key_facts["p2_venus_d9"] = v2
    key_facts["nakshatra_matches"] = nak_match

    return {"score_0_10": _clamp(raw), "drivers": drivers, "cautions": cautions, "key_facts": key_facts}


def _ch2_trust(milan_facts: dict, d9: dict, kp: dict) -> dict[str, Any]:
    """Trust = Maitri + KP promise + D9 7L house stability."""
    drivers: list[str] = []
    cautions: list[str] = []
    key_facts: dict[str, Any] = {}

    maitri = _koot_norm(milan_facts, "maitri")
    kp_v = (kp or {}).get("couple_verdict", "UNAVAILABLE")
    kp_w = _kp_weight(kp_v)

    p1d9 = (d9 or {}).get("p1") or {}
    p2d9 = (d9 or {}).get("p2") or {}
    h1 = p1d9.get("d9_7l_house")
    h2 = p2d9.get("d9_7l_house")
    stable_houses = {1, 4, 5, 7, 9, 10, 11}
    risky_houses = {6, 8, 12}
    stability_bonus = 0.0
    for label, h in (("P1", h1), ("P2", h2)):
        if h in stable_houses:
            stability_bonus += 0.6
            drivers.append(f"{label}'s D9 7L sits in {h}H — committed-bond house")
        elif h in risky_houses:
            stability_bonus -= 0.6
            cautions.append(f"{label}'s D9 7L sits in {h}H — patience layer needed")

    raw = 2.0 + (maitri * 2.5) + (kp_w * 3.0) + stability_bonus + 1.0
    if maitri < 0.5:
        cautions.append("Graha Maitri weak — friendship layer needs continuous deposits")
    if kp_v == "WEAK":
        cautions.append("Underlying commitment-promise layer is soft — needs intentional anchoring")
    elif kp_v == "STRONG":
        drivers.append("Underlying commitment-promise layer is strong — natural loyalty grain")

    key_facts["maitri_score"] = _koot(milan_facts, "maitri").get("score")
    key_facts["kp_couple_verdict"] = kp_v
    key_facts["p1_d9_7l_house"] = h1
    key_facts["p2_d9_7l_house"] = h2

    return {"score_0_10": _clamp(raw), "drivers": drivers, "cautions": cautions, "key_facts": key_facts}


def _ch3_conflict(milan_facts: dict, manglik_dosh: bool) -> dict[str, Any]:
    """Communication & Conflict = Bhakut + Gana + Manglik."""
    drivers: list[str] = []
    cautions: list[str] = []
    key_facts: dict[str, Any] = {}

    bhakut = _koot_norm(milan_facts, "bhakut")
    gana = _koot_norm(milan_facts, "gana")

    raw = 3.0 + (bhakut * 3.5) + (gana * 2.5)
    if manglik_dosh:
        raw -= 1.5
        cautions.append("Manglik mismatch — fiery moments possible; conscious cool-down ritual helps")
    else:
        drivers.append("No Manglik mismatch — temper-energy is balanced")

    if bhakut == 0.0:
        cautions.append("Bhakut dosha — daily-life friction zones; map them early")
    elif bhakut >= 0.9:
        drivers.append("Bhakut clean — daily compatibility flows naturally")
    if gana < 0.4:
        cautions.append("Gana mismatch — temperament rhythm differs; respect different paces")

    key_facts["bhakut_score"] = _koot(milan_facts, "bhakut").get("score")
    key_facts["gana_score"] = _koot(milan_facts, "gana").get("score")
    key_facts["manglik_mismatch"] = bool(manglik_dosh)

    return {"score_0_10": _clamp(raw), "drivers": drivers, "cautions": cautions, "key_facts": key_facts}


def _ch4_stability(d9: dict, kp: dict, milan_facts: dict) -> dict[str, Any]:
    """Marriage Stability = KP promise (heavy) + D9 7L + Bhakut."""
    drivers: list[str] = []
    cautions: list[str] = []
    key_facts: dict[str, Any] = {}

    kp_v = (kp or {}).get("couple_verdict", "UNAVAILABLE")
    kp_w = _kp_weight(kp_v)
    bhakut = _koot_norm(milan_facts, "bhakut")

    p1d9 = (d9 or {}).get("p1") or {}
    p2d9 = (d9 or {}).get("p2") or {}
    s1 = p1d9.get("marriage_maturity_0_10", 5)
    s2 = p2d9.get("marriage_maturity_0_10", 5)
    avg_d9 = (s1 + s2) / 2.0  # already 0-10

    raw = (kp_w * 4.0) + (avg_d9 * 0.4) + (bhakut * 1.5) + 0.5
    if kp_v == "STRONG":
        drivers.append("Deeper karmic commitment-layer is strong on both sides")
    elif kp_v == "WEAK":
        cautions.append("Deeper karmic commitment-layer is soft — anchor through rituals + clear boundaries")
    if avg_d9 >= 7.5:
        drivers.append(f"Both D9 marriage-maturity scores high (avg {avg_d9:.1f}/10)")
    elif avg_d9 <= 4.5:
        cautions.append(f"D9 marriage-maturity average is modest ({avg_d9:.1f}/10) — growth required")

    key_facts["kp_couple_verdict"] = kp_v
    key_facts["p1_d9_maturity"] = s1
    key_facts["p2_d9_maturity"] = s2
    key_facts["bhakut_score"] = _koot(milan_facts, "bhakut").get("score")

    return {"score_0_10": _clamp(raw), "drivers": drivers, "cautions": cautions, "key_facts": key_facts}


def _ch5_chemistry(milan_facts: dict, syn: dict) -> dict[str, Any]:
    """Chemistry = Venus overlay + Yoni + Mars synastry hints."""
    drivers: list[str] = []
    cautions: list[str] = []
    key_facts: dict[str, Any] = {}

    yoni = _koot_norm(milan_facts, "yoni")
    venus_a = ((syn or {}).get("venus_overlay_p2_to_p1") or {}).get("touches") or []
    venus_b = ((syn or {}).get("venus_overlay_p1_to_p2") or {}).get("touches") or []
    venus_touch_count = len(venus_a) + len(venus_b)

    raw = 3.0 + (yoni * 3.0) + min(3.0, venus_touch_count * 0.8) + 1.0
    if venus_touch_count >= 2:
        drivers.append(f"Venus overlay touches {venus_touch_count} key points — strong physical-emotional pull")
    elif venus_touch_count == 0:
        cautions.append("No direct Venus overlay — chemistry needs conscious cultivation")
    if yoni == 0.0:
        cautions.append("Yoni hostile — instinct-level mismatch; talk openly about needs")
    elif yoni == 1.0:
        drivers.append("Yoni perfectly matched — instinctive comfort")

    key_facts["yoni_score"] = _koot(milan_facts, "yoni").get("score")
    key_facts["venus_overlay_touches"] = venus_a + venus_b

    return {"score_0_10": _clamp(raw), "drivers": drivers, "cautions": cautions, "key_facts": key_facts}


def _ch6_family(milan_facts: dict) -> dict[str, Any]:
    """Family + Practical = Bhakut + Vasya + Varna."""
    drivers: list[str] = []
    cautions: list[str] = []
    key_facts: dict[str, Any] = {}

    bhakut = _koot_norm(milan_facts, "bhakut")
    vasya = _koot_norm(milan_facts, "vasya")
    varna = _koot_norm(milan_facts, "varna")

    raw = 3.0 + (bhakut * 3.0) + (vasya * 2.0) + (varna * 1.5) + 0.5
    if bhakut < 0.5:
        cautions.append("Bhakut soft — extended-family dynamics may need extra communication")
    if vasya < 0.5:
        cautions.append("Vasya weak — power-balance needs conscious symmetry")
    elif vasya == 1.0:
        drivers.append("Vasya strong — natural mutual influence balance")
    if varna == 0.0:
        cautions.append("Varna mismatch — work-style and ego-needs differ; respect each other's lane")

    key_facts["bhakut_score"] = _koot(milan_facts, "bhakut").get("score")
    key_facts["vasya_score"] = _koot(milan_facts, "vasya").get("score")
    key_facts["varna_score"] = _koot(milan_facts, "varna").get("score")

    return {"score_0_10": _clamp(raw), "drivers": drivers, "cautions": cautions, "key_facts": key_facts}


def _ch7_future(d9: dict, syn: dict, milan_facts: dict) -> dict[str, Any]:
    """Long-term future = D9 lagna-sync + Jupiter overlay + total %."""
    drivers: list[str] = []
    cautions: list[str] = []
    key_facts: dict[str, Any] = {}

    sync = (d9 or {}).get("sync") or {}
    sync_score = sync.get("score_0_10", 5)
    jup_a = ((syn or {}).get("jupiter_overlay_p2_to_p1") or {}).get("touches") or []
    jup_b = ((syn or {}).get("jupiter_overlay_p1_to_p2") or {}).get("touches") or []
    jup_touch = len(jup_a) + len(jup_b)
    raw_total = milan_facts.get("total", 0) if isinstance(milan_facts, dict) else 0
    try:
        total = float(raw_total) if raw_total not in (None, "") else 0.0
    except (TypeError, ValueError):
        total = 0.0
    # Clamp to 0..36 so malformed payloads can't push pct >100%.
    total = max(0.0, min(36.0, total))
    pct = total / 36.0

    raw = (sync_score * 0.4) + min(2.5, jup_touch * 0.8) + (pct * 4.0) + 1.5
    if sync_score >= 7.5:
        drivers.append(f"D9 lagna-lord sync is strong ({sync_score}/10) — life-direction alignment")
    elif sync_score <= 4.0:
        cautions.append(f"D9 lagna-lord sync is modest ({sync_score}/10) — life-vision drift possible")
    if jup_touch >= 2:
        drivers.append(f"Jupiter overlay blesses {jup_touch} key points — wisdom + growth together")
    if pct >= 0.7:
        drivers.append(f"Overall match {round(pct*100)}% — long-term direction has tailwind")

    key_facts["d9_sync_score"] = sync_score
    key_facts["jupiter_overlay_touches"] = jup_a + jup_b
    key_facts["total_pct"] = round(pct * 100, 1)

    return {"score_0_10": _clamp(raw), "drivers": drivers, "cautions": cautions, "key_facts": key_facts}


def compute_chapter_scores(
    milan_facts: dict,
    d9_marriage: dict,
    synastry: dict,
    kp_promise: dict,
) -> dict[str, Any]:
    """Master derivation. Returns dict keyed ch1..ch7 + overall_avg.

    `milan_facts` shape (from /api/kundli-milan):
       { koots: [{key, score, max, ...}], total, manglik_dosh, ... }

    `d9_marriage`  : output of d9_marriage.compute_d9_marriage
    `synastry`     : output of synastry_7l.compute_synastry_7l
    `kp_promise`   : output of kp_marriage_promise.compute_kp_couple_promise
    """
    if not isinstance(milan_facts, dict):
        milan_facts = {}
    manglik_dosh = bool(milan_facts.get("manglik_dosh"))

    chapters = {
        "ch1": {"title": CHAPTER_TITLES["ch1"], **_ch1_emotional(milan_facts, d9_marriage, synastry)},
        "ch2": {"title": CHAPTER_TITLES["ch2"], **_ch2_trust(milan_facts, d9_marriage, kp_promise)},
        "ch3": {"title": CHAPTER_TITLES["ch3"], **_ch3_conflict(milan_facts, manglik_dosh)},
        "ch4": {"title": CHAPTER_TITLES["ch4"], **_ch4_stability(d9_marriage, kp_promise, milan_facts)},
        "ch5": {"title": CHAPTER_TITLES["ch5"], **_ch5_chemistry(milan_facts, synastry)},
        "ch6": {"title": CHAPTER_TITLES["ch6"], **_ch6_family(milan_facts)},
        "ch7": {"title": CHAPTER_TITLES["ch7"], **_ch7_future(d9_marriage, synastry, milan_facts)},
    }
    avg = round(sum(c["score_0_10"] for c in chapters.values()) / 7.0, 1)
    return {
        "chapters": chapters,
        "overall_avg_0_10": avg,
        "ordered_keys": ["ch1", "ch2", "ch3", "ch4", "ch5", "ch6", "ch7"],
    }
