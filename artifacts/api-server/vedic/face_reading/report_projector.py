"""
Report Projector — filters engine outputs for the 21-section Face Intelligence Report.

Each engine internally calculates ~100 fields; this module exposes ONLY the subset
needed for the user-facing report (Hinglish, conversational, ₹1499 deliverable).

Internal/academic/debug fields are stripped. Engines themselves are unchanged —
this is a pure projection layer applied at the JSON-response boundary.

Usage:
    from vedic.face_reading.report_projector import project_engines_for_report
    cleaned = project_engines_for_report({"anthropometry": eng1_result, ...})
"""

from typing import Any, Dict, Iterable, Optional


def _pick(d: Optional[Dict[str, Any]], keys: Iterable[str]) -> Dict[str, Any]:
    if not isinstance(d, dict):
        return {}
    return {k: d[k] for k in keys if k in d}


def _pick_subdict(d: Optional[Dict[str, Any]], parent: str, keys: Iterable[str]) -> Dict[str, Any]:
    if not isinstance(d, dict):
        return {}
    sub = d.get(parent)
    if not isinstance(sub, dict):
        return {}
    return {k: sub[k] for k in keys if k in sub}


# --------------------------------------------------------------------------------------
# Per-engine projectors (whitelist approach)
# --------------------------------------------------------------------------------------


def project_anthropometry(r: Dict[str, Any]) -> Dict[str, Any]:
    """Engine 1: Keep face shape + key classifications + a small summary."""
    if not isinstance(r, dict) or not r.get("ok"):
        return r or {}

    keep_classifications = {
        "face_shape", "face_shape_label", "face_proportion",
        "jaw_type", "forehead_type", "nose_type", "lip_type",
        "eye_shape", "brow_type", "chin_type",
    }
    keep_indices = {
        "facial_index", "nasal_index", "mouth_face_width_index",
    }

    return {
        "engine": r.get("engine"),
        "version": r.get("version"),
        "ok": True,
        "face_shape_7": r.get("face_shape_7"),
        "classifications": {
            k: v for k, v in (r.get("classifications") or {}).items()
            if k in keep_classifications
        },
        "classical_indices": {
            k: v for k, v in (r.get("classical_indices") or {}).items()
            if k in keep_indices
        },
        "summary": r.get("summary"),
    }


def project_symmetry(r: Dict[str, Any]) -> Dict[str, Any]:
    """Engine 2: Keep overall score + dominant side + mask-vs-real one-liner."""
    if not isinstance(r, dict) or not r.get("ok"):
        return r or {}

    vedic = r.get("vedic_interpretation") or {}
    return {
        "engine": r.get("engine"),
        "version": r.get("version"),
        "ok": True,
        "overall_score": r.get("overall_score"),
        "tier": r.get("tier"),
        "dominant_side": r.get("dominant_side"),
        "most_symmetric_feature": r.get("most_symmetric_feature"),
        "least_symmetric_feature": r.get("least_symmetric_feature"),
        "mask_vs_real": (
            vedic.get("private_vs_public")
            or vedic.get("interpretation")
            or vedic.get("summary")
        ),
        "summary": r.get("summary"),
    }


def project_phi(r: Dict[str, Any]) -> Dict[str, Any]:
    """Engine 3: Keep overall phi + classification + interpretation only."""
    if not isinstance(r, dict) or not r.get("ok"):
        return r or {}

    interp = r.get("interpretation") or {}
    return {
        "engine": r.get("engine"),
        "version": r.get("version"),
        "ok": True,
        "overall_phi_score": r.get("overall_phi_score"),
        "classification": r.get("classification"),
        "interpretation": {
            k: v for k, v in interp.items()
            if k in {"summary", "verdict", "user_text"}
        },
    }


def project_fwhr(r: Dict[str, Any]) -> Dict[str, Any]:
    """Engine 4: Keep primary fWHR + dominance traits + interpretation."""
    if not isinstance(r, dict) or not r.get("ok"):
        return r or {}

    primary = r.get("primary") or {}
    interp = r.get("interpretation") or {}
    composite = r.get("composite_scores") or {}
    sex_dim = r.get("sex_dimorphism_vector") or {}

    return {
        "engine": r.get("engine"),
        "version": r.get("version"),
        "ok": True,
        "fwhr_value": primary.get("value") or primary.get("fwhr"),
        "fwhr_class": primary.get("class") or primary.get("classification"),
        "trait_predictions": r.get("trait_predictions"),
        "dominance_score": composite.get("dominance") or composite.get("dominance_score"),
        "masculinity_femininity": sex_dim.get("score") or sex_dim.get("class"),
        "interpretation": {
            k: v for k, v in interp.items()
            if k in {"summary", "verdict", "user_text"}
        },
    }


def project_health(r: Dict[str, Any]) -> Dict[str, Any]:
    """Engine 5: Keep vitality score + 3 macro indicators (stress/energy/burnout) + recs."""
    if not isinstance(r, dict) or not r.get("ok"):
        return r or {}

    indicators = r.get("indicators") or {}
    composites = r.get("composite_scores") or {}

    keep_indicator_names = {
        "stress", "stress_level", "stress_signal",
        "energy", "energy_level", "vitality_indicator",
        "burnout", "burnout_signal", "fatigue",
        "hydration", "skin_radiance", "puffiness",
        "sleep_deficit", "eye_clarity",
    }

    macro_indicators = {
        k: (v if not isinstance(v, dict) else v.get("score") or v.get("value") or v.get("class"))
        for k, v in indicators.items() if k in keep_indicator_names
    }

    return {
        "engine": r.get("engine"),
        "version": r.get("version"),
        "ok": True,
        "vitality_score": r.get("vitality_score"),
        "vitality_class": r.get("vitality_class"),
        "vitality_age_adjusted": r.get("vitality_age_adjusted"),
        "vitality_band": r.get("vitality_band"),
        "macro_indicators": macro_indicators,
        "stress_composite": composites.get("stress") or composites.get("stress_composite"),
        "energy_composite": composites.get("energy") or composites.get("vitality"),
        "recommendations": r.get("recommendations"),
        "disclaimer": r.get("disclaimer"),
    }


def project_personality(r: Dict[str, Any]) -> Dict[str, Any]:
    """Engine 6: Keep OCEAN top-5 + archetype + dominant traits + strengths/growth."""
    if not isinstance(r, dict) or not r.get("ok"):
        return r or {}

    composites = r.get("composites") or {}
    return {
        "engine": r.get("engine"),
        "version": r.get("version"),
        "ok": True,
        "ocean_summary_scores": r.get("ocean_summary_scores"),
        "ocean_percentiles": r.get("ocean_percentiles"),
        "traits": r.get("traits"),
        "dominant_trait": r.get("dominant_trait"),
        "secondary_trait": r.get("secondary_trait"),
        "archetype": r.get("archetype"),
        "strengths_and_growth": r.get("strengths_and_growth"),
        "composites": {
            k: v for k, v in composites.items()
            if k in {"leadership", "creativity", "warmth", "discipline"}
        },
        "do_not_use_for_hiring": r.get("do_not_use_for_hiring"),
        "disclaimer": r.get("disclaimer"),
    }


def project_first_impression(r: Dict[str, Any]) -> Dict[str, Any]:
    """Engine 7: Keep ONLY 4 dims (Confidence/Trust/Attraction/Authority) + valence + age."""
    if not isinstance(r, dict) or not r.get("ok"):
        return r or {}

    snap = r.get("snap_judgment_scores") or {}
    keep_dims = {
        "confidence", "trustworthiness", "trust", "attractiveness",
        "attraction", "authority", "dominance",
    }

    # Normalize to the 4 template fields
    def _g(*names):
        for n in names:
            if n in snap:
                v = snap[n]
                return v if not isinstance(v, dict) else v.get("score") or v.get("value")
        return None

    four_scores = {
        "confidence": _g("confidence"),
        "trust": _g("trustworthiness", "trust"),
        "attraction": _g("attractiveness", "attraction"),
        "authority": _g("authority", "dominance"),
    }

    return {
        "engine": r.get("engine"),
        "version": r.get("version"),
        "ok": True,
        "first_impression_4": four_scores,
        "first_glance_valence": r.get("first_glance_valence"),
        "perceived_age": r.get("perceived_age"),
        "snap_narrative": r.get("snap_narrative"),
        "do_not_use_for_hiring": r.get("do_not_use_for_hiring"),
        "disclaimer": r.get("disclaimer"),
    }


def project_samudrika(r: Dict[str, Any]) -> Dict[str, Any]:
    """
    Engine 8: Keep core mukha-pradesh (7 features for template Section 6) + Mahabhuta
    (mapped to Chinese 5-element later) + Saubhagya (for age-wise map). Hide Sanskrit
    shlokas, Yogas, Marma, sources, Sapta-Lakshana, citations.
    """
    if not isinstance(r, dict) or not r.get("ok"):
        return r or {}

    # Strip the heavy Vedic verbiage from each feature dict
    def _slim_feature(f: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if not isinstance(f, dict):
            return f
        return {
            k: v for k, v in f.items()
            if k in {
                "type", "subtype", "english", "phala_en", "phala_hi",
                "score", "class", "classification",
                "trait", "trait_en", "trait_hi",
            }
        }

    out = {
        "engine": r.get("engine"),
        "version": r.get("version"),
        "ok": True,
    }

    # 7 core features mapped from samudrika regions to template Section 6
    features_map = {
        "eyes": r.get("netra") or r.get("eyes"),
        "nose": r.get("nasika") or r.get("nose"),
        "lips": r.get("oshtha") or r.get("lips"),
        "jaw_chin": r.get("hanu") or r.get("chibuka") or r.get("jaw"),
        "forehead": r.get("lalata") or r.get("forehead"),
        "eyebrows": r.get("bhru") or r.get("eyebrows"),
        "ears": r.get("karna") or r.get("ears"),
    }
    out["features"] = {k: _slim_feature(v) for k, v in features_map.items() if v}

    # Face shape (mukha-akriti) — slim
    mukha = r.get("mukha_akriti") or r.get("mukha")
    if mukha:
        out["face_shape"] = _slim_feature(mukha)

    # Complexion (mukha-varna) — slim (no Sanskrit emphasis)
    varna = r.get("mukha_varna") or r.get("varna")
    if varna:
        out["complexion"] = (
            varna.get("english") or varna.get("class") or varna.get("type")
            if isinstance(varna, dict) else varna
        )

    # Pancha-Mahabhuta → kept as element percentages (mapped to Wu Xing later)
    mahabhuta = r.get("pancha_mahabhuta") or r.get("mahabhuta")
    if isinstance(mahabhuta, dict):
        # Strip Sanskrit-only fields, keep only numeric mapping
        mb_clean = {
            k: v for k, v in mahabhuta.items()
            if k in {"prithvi", "jal", "agni", "vayu", "akash",
                     "earth", "water", "fire", "air", "ether",
                     "dominant", "dominant_element", "percentages", "scores"}
        }
        if mb_clean:
            out["element_profile"] = mb_clean

    # Saubhagya by 3 aayu-kaal → maps to template Section 15 (age-wise map)
    saubhagya = r.get("saubhagya_phala") or r.get("saubhagya")
    if isinstance(saubhagya, dict):
        out["age_wise_fortune"] = {
            k: v for k, v in saubhagya.items()
            if k in {"purva_aayu", "madhya_aayu", "uttara_aayu",
                     "0_25", "25_50", "50_plus", "summary"}
        }

    # Composite Vedic scores (Bhagya / Buddhi / Dhana / Aayu / Sambandha)
    composite = r.get("composite_scores") or r.get("composites")
    if isinstance(composite, dict):
        out["composite_scores"] = {
            k: v for k, v in composite.items()
            if k in {"bhagya", "buddhi", "dhana", "aayu", "sambandha"}
        }

    # Tilaka framework (placeholder for Section 17 mole detection — to be built)
    tilaka = r.get("tilaka_phala") or r.get("til_phala")
    if isinstance(tilaka, dict):
        out["mole_framework"] = {
            "status": tilaka.get("status", "framework_only"),
            "note": tilaka.get("note"),
        }

    return out


# --------------------------------------------------------------------------------------
# Main entry-point
# --------------------------------------------------------------------------------------


_PROJECTORS = {
    "anthropometry": project_anthropometry,
    "symmetry": project_symmetry,
    "phi": project_phi,
    "fwhr": project_fwhr,
    "health": project_health,
    "personality": project_personality,
    "first_impression": project_first_impression,
    "samudrika": project_samudrika,
}


def project_engines_for_report(
    engines: Dict[str, Any],
    *,
    full: bool = False,
) -> Dict[str, Any]:
    """
    Filter engine outputs for the user-facing 21-section report.

    Args:
        engines: dict of engine_name -> raw engine output
        full: if True, returns engines unchanged (for debugging / internal use)

    Returns:
        dict of engine_name -> projected (cleaned) output
    """
    if full:
        return engines

    out: Dict[str, Any] = {}
    for name, raw in (engines or {}).items():
        proj = _PROJECTORS.get(name)
        out[name] = proj(raw) if proj else raw
    return out
