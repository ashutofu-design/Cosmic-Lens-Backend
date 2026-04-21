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
        "forehead_height_pct", "midface_height_pct", "lower_face_height_pct",
        "fwhr", "eye_separation_ratio", "lip_thickness_ratio",
    }

    # Anthropometry emits ratios.third_upper / third_middle / third_lower as
    # 0..1 fractions. Convert to height-pct fields used by Section 5 zones.
    ratios = r.get("ratios") or {}
    indices_raw = dict(r.get("classical_indices") or {})
    if "third_upper" in ratios and "forehead_height_pct" not in indices_raw:
        indices_raw["forehead_height_pct"] = round(float(ratios["third_upper"]) * 100, 1)
    if "third_middle" in ratios and "midface_height_pct" not in indices_raw:
        indices_raw["midface_height_pct"] = round(float(ratios["third_middle"]) * 100, 1)
    if "third_lower" in ratios and "lower_face_height_pct" not in indices_raw:
        indices_raw["lower_face_height_pct"] = round(float(ratios["third_lower"]) * 100, 1)

    # Keep micro-measurements needed by Section 6 deep feature analysis
    keep_mm = {
        "iod_inner", "outer_eye_span",
        "right_eye_width", "left_eye_width",
        "right_eye_height", "left_eye_height",
        "nose_length", "nose_width_alar",
        "upper_lip_thickness", "lower_lip_thickness", "mouth_width",
        "jaw_width", "nose_tip_to_chin", "lip_to_chin",
        "forehead_height", "forehead_width",
        "brow_distance_inner",
    }
    keep_angles = {
        "canthal_tilt", "nose_tip_projection", "lip_commissure_tilt",
        "jaw_angle_gonial", "chin_pointedness",
        "forehead_slope", "brow_arch_angle",
    }
    keep_ratios = {
        "eye_spacing_to_eye_width", "eye_aspect_ratio_avg",
        "eye_span_to_face_width",
        "nose_length_to_face", "nose_width_to_mouth_width",
        "lip_ratio_upper_to_lower", "mouth_to_face_width",
        "jaw_to_face_width", "forehead_to_face_width",
    }
    mm_full = r.get("measurements_mm") or {}
    angles_full = r.get("angles_deg") or {}

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
            k: v for k, v in indices_raw.items()
            if k in keep_indices
        },
        "measurements_mm": {k: v for k, v in mm_full.items() if k in keep_mm},
        "angles_deg":     {k: v for k, v in angles_full.items() if k in keep_angles},
        "ratios":         {k: v for k, v in ratios.items() if k in keep_ratios},
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

    # Personality engine emits OCEAN as {"O","C","E","A","N"} but section_mapper
    # reads {"openness","conscientiousness","extraversion","agreeableness","neuroticism"}.
    # Normalize both summary_scores and percentiles to long-form keys.
    _OCEAN_ALIAS = {"O": "openness", "C": "conscientiousness",
                    "E": "extraversion", "A": "agreeableness", "N": "neuroticism"}
    def _normalize_ocean(d):
        if not isinstance(d, dict):
            return d
        out = {}
        for k, v in d.items():
            long_k = _OCEAN_ALIAS.get(k, k)
            out[long_k] = v
            # also keep short-form for any code that reads it
            out[k] = v
        return out

    return {
        "engine": r.get("engine"),
        "version": r.get("version"),
        "ok": True,
        "ocean_summary_scores": _normalize_ocean(r.get("ocean_summary_scores")),
        "ocean_percentiles":    _normalize_ocean(r.get("ocean_percentiles")),
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
        # Engine emits perceived_age.apparent_age + age_diff; mapper reads .value/.lower/.upper
        "perceived_age": (lambda pa: ({
            "value": pa.get("apparent_age") if isinstance(pa, dict) else None,
            "apparent_age": pa.get("apparent_age") if isinstance(pa, dict) else None,
            "age_diff": pa.get("age_diff") if isinstance(pa, dict) else None,
            "lower": pa.get("lower") if isinstance(pa, dict) else None,
            "upper": pa.get("upper") if isinstance(pa, dict) else None,
        }) if isinstance(pa, dict) else pa)(r.get("perceived_age")),
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

    # Strip the heavy Vedic verbiage from each feature dict.
    # Real samudrika emits phala_english/phala_hinglish — alias to short forms
    # that section_mapper._read() expects (phala_hi, phala_en, english).
    def _slim_feature(f: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if not isinstance(f, dict):
            return f
        out_f = {}
        # canonical short fields used downstream
        if f.get("phala_hinglish") or f.get("phala_hi"):
            out_f["phala_hi"] = f.get("phala_hinglish") or f.get("phala_hi")
        if f.get("phala_english") or f.get("phala_en"):
            out_f["phala_en"] = f.get("phala_english") or f.get("phala_en")
        if f.get("english_name") or f.get("english"):
            out_f["english"] = f.get("english_name") or f.get("english")
        if f.get("classification"):
            out_f["classification"] = f.get("classification")
        if f.get("transliteration"):
            out_f["translit"] = f.get("transliteration")
        if f.get("is_auspicious") is not None:
            out_f["is_auspicious"] = f.get("is_auspicious")
        return out_f

    out = {
        "engine": r.get("engine"),
        "version": r.get("version"),
        "ok": True,
    }

    # Real samudrika nests all 12 regions under mukha_pradesh_analysis.
    mpa = r.get("mukha_pradesh_analysis") or {}

    # 7 core features mapped from samudrika regions to template Section 6.
    # Use real samudrika keys first, then loose fallbacks.
    features_map = {
        "eyes":     mpa.get("04_netra")   or r.get("netra")   or r.get("eyes"),
        "nose":     mpa.get("05_nasika")  or r.get("nasika")  or r.get("nose"),
        "lips":     mpa.get("06_oshtha")  or r.get("oshtha")  or r.get("lips"),
        "jaw_chin": mpa.get("10_hanu")    or mpa.get("07_chibuka") or r.get("hanu") or r.get("chibuka") or r.get("jaw"),
        "forehead": mpa.get("02_lalata")  or r.get("lalata")  or r.get("forehead"),
        "eyebrows": mpa.get("03_bhru")    or r.get("bhru")    or r.get("eyebrows"),
        "ears":     mpa.get("08_karna")   or r.get("karna")   or r.get("ears"),
    }
    out["features"] = {k: _slim_feature(v) for k, v in features_map.items() if v}

    # Face shape (mukha-akriti) — slim
    mukha = mpa.get("01_mukha_akriti") or r.get("mukha_akriti") or r.get("mukha")
    if mukha:
        out["face_shape"] = _slim_feature(mukha)

    # Complexion (mukha-varna)
    varna = mpa.get("11_mukha_varna") or r.get("mukha_varna") or r.get("varna")
    if varna:
        if isinstance(varna, dict):
            out["complexion"] = (
                varna.get("english_name") or varna.get("english")
                or varna.get("classification") or varna.get("class") or varna.get("type")
            )
        else:
            out["complexion"] = varna

    # Pancha-Mahabhuta → element profile. Real key is pancha_mahabhuta_facial_mapping
    # with prithvi_pct/jal_pct/agni_pct/vayu_pct/akash_pct + primary_mahabhuta.
    mahabhuta = (r.get("pancha_mahabhuta_facial_mapping")
                 or r.get("pancha_mahabhuta") or r.get("mahabhuta"))
    if isinstance(mahabhuta, dict):
        mb_clean = {
            "prithvi": mahabhuta.get("prithvi_pct") or mahabhuta.get("prithvi") or mahabhuta.get("earth"),
            "jal":     mahabhuta.get("jal_pct")     or mahabhuta.get("jal")     or mahabhuta.get("water"),
            "agni":    mahabhuta.get("agni_pct")    or mahabhuta.get("agni")    or mahabhuta.get("fire"),
            "vayu":    mahabhuta.get("vayu_pct")    or mahabhuta.get("vayu")    or mahabhuta.get("air"),
            "akash":   mahabhuta.get("akash_pct")   or mahabhuta.get("akash")   or mahabhuta.get("ether"),
            "dominant": mahabhuta.get("primary_mahabhuta")
                        or mahabhuta.get("dominant") or mahabhuta.get("dominant_element"),
        }
        # drop None values
        mb_clean = {k: v for k, v in mb_clean.items() if v is not None}
        if mb_clean:
            out["element_profile"] = mb_clean
            # convenience top-level (some sections read .dominant_element directly)
            if mb_clean.get("dominant"):
                out["dominant_element"] = mb_clean["dominant"]

    # Saubhagya by 3 aayu-kaal → Section 15 age-wise map.
    # Real key: saubhagya_phala_by_aayu with purva_aayu_0_25 / madhya_aayu_25_50 / uttara_aayu_50_plus
    saubhagya = (r.get("saubhagya_phala_by_aayu")
                 or r.get("saubhagya_phala") or r.get("saubhagya"))
    if isinstance(saubhagya, dict):
        purva  = saubhagya.get("purva_aayu_0_25")  or saubhagya.get("purva_aayu")  or saubhagya.get("0_25")
        madhya = saubhagya.get("madhya_aayu_25_50") or saubhagya.get("madhya_aayu") or saubhagya.get("25_50")
        uttara = saubhagya.get("uttara_aayu_50_plus") or saubhagya.get("uttara_aayu") or saubhagya.get("50_plus")
        def _score(b):
            return b.get("score") if isinstance(b, dict) else b
        out["age_wise_fortune"] = {
            "purva_aayu":  _score(purva),
            "madhya_aayu": _score(madhya),
            "uttara_aayu": _score(uttara),
            "purva_phala_hi":  (purva  or {}).get("phala_hi") if isinstance(purva, dict)  else None,
            "madhya_phala_hi": (madhya or {}).get("phala_hi") if isinstance(madhya, dict) else None,
            "uttara_phala_hi": (uttara or {}).get("phala_hi") if isinstance(uttara, dict) else None,
            "summary": saubhagya.get("summary"),
        }

    # Composite Vedic scores (Bhagya / Buddhi / Dhana / Aayu / Sambandha)
    # Samudrika emits keys as "<name>_score" (bhagya_score, buddhi_score, ...).
    # Section_mapper reads short forms (bhagya, buddhi, ...). Alias both.
    composite = r.get("composite_scores") or r.get("composites")
    if isinstance(composite, dict):
        out["composite_scores"] = {
            "bhagya":    composite.get("bhagya_score")    or composite.get("bhagya"),
            "buddhi":    composite.get("buddhi_score")    or composite.get("buddhi"),
            "dhana":     composite.get("dhana_score")     or composite.get("dhana"),
            "aayu":      composite.get("aayu_score")      or composite.get("aayu"),
            "sambandha": composite.get("sambandha_score") or composite.get("sambandha"),
            "bala":      composite.get("bala_score")      or composite.get("bala"),
        }
        # drop None entries
        out["composite_scores"] = {k: v for k, v in out["composite_scores"].items() if v is not None}

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
