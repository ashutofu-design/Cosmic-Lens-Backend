"""
Engine 4 — Facial Width-to-Height Ratio (fWHR).  v2.

Sex-dimorphic, testosterone-exposure marker introduced by Carré &
McCormick (2008, Proc R Soc B).  v2 integrates 17 audit fixes on top
of v1's 20 baseline fixes.

v1 fixes (1-20): see git history.
v2 fixes (additional 17):
  21. 3D cheekbone z-projection (lateral cheek depth from 3D mesh)
  22. Lower-face WHR (jaw_w / stomion-to-chin)
  23. Forehead-WHR (forehead_w / forehead_h)
  24. Anatomical clarification of MP 234/454 (maxillary, not strict zygion)
  25. Smile / expression detection → warn user if non-neutral
  26. Per-trait replication strength labels (robust/moderate/weak/contested)
  27. signal_type per trait (perceived vs behavioral_proxy)
  28. Outlier flag per variant (|z| > 3 → 'unusual_measurement')
  29. Test-retest reliability note (typical re-measurement ±0.05 fWHR)
  30. Testosterone:Cortisol caveat (Carré 2014 — fWHR predicts only when
       cortisol low; we have no cortisol proxy)
  31. Pubertal-window educational note
  32. Cultural inversion flag (east_asian beauty standards prefer LOWER fWHR)
  33. Sexual dimorphism 2D vector + 4-quadrant typology
  34. Compactness index (face polygon area / bounding-box area)
  35. Eye placement contribution (eye_w / face_w; Gomez-Valdes 2013)
  36. Per-norm evidence_quality field
  37. Auto-shave SD ×1.3 for low-evidence ethnic norms
"""
from __future__ import annotations

import math
from typing import Sequence, Optional

import numpy as np

from .anthropometry import (
    LM as LMK,
    IOD_BASELINE_MM,
    R_INNER_EYE,
    L_INNER_EYE,
    FOREHEAD,
    CHIN,
    _build_face_frame,
)


LANDMARK_JITTER_PX  = 1.5
DENOM_FLOOR_PX      = 5.0
YAW_FRONTAL_OK      = 8.0
YAW_FRONTAL_REFUSE  = 15.0
TEST_RETEST_FWHR_SD = 0.05      # typical re-measurement variation


# ─────────────────────────────────────────────────────────────────────────────
# Population norms.  Sources: Carré 2008; Lefevre 2012; Hehman 2015;
# Geniuk 2017; Robertson 2017; Whitehouse 2015 (jaw_whr).
# ─────────────────────────────────────────────────────────────────────────────
NORMS_BY_GENDER = {
    "M": {
        "carre":         (1.95, 0.15),
        "lefevre":       (2.05, 0.18),
        "hehman":        (1.85, 0.16),
        "geniuk":        (0.94, 0.07),
        "jaw_whr":       (1.55, 0.15),
        "lower_face_whr":(1.50, 0.18),
        "forehead_whr":  (2.40, 0.30),
    },
    "F": {
        "carre":         (1.85, 0.15),
        "lefevre":       (1.95, 0.18),
        "hehman":        (1.78, 0.16),
        "geniuk":        (0.92, 0.07),
        "jaw_whr":       (1.45, 0.15),
        "lower_face_whr":(1.42, 0.18),
        "forehead_whr":  (2.35, 0.30),
    },
    "U": {
        "carre":         (1.90, 0.16),
        "lefevre":       (2.00, 0.18),
        "hehman":        (1.81, 0.16),
        "geniuk":        (0.93, 0.07),
        "jaw_whr":       (1.50, 0.16),
        "lower_face_whr":(1.46, 0.18),
        "forehead_whr":  (2.37, 0.30),
    },
}

ETHNIC_NORM_SHIFT = {
    "caucasian":   {"carre": 0.00, "lefevre": 0.00, "hehman": 0.00,
                    "geniuk": 0.00, "jaw_whr": 0.00,
                    "lower_face_whr": 0.00, "forehead_whr": 0.00},
    "east_asian":  {"carre": +0.08, "lefevre": +0.06, "hehman": +0.07,
                    "geniuk": +0.03, "jaw_whr": +0.05,
                    "lower_face_whr": +0.04, "forehead_whr": +0.10},
    "south_asian": {"carre": +0.02, "lefevre": +0.02, "hehman": +0.02,
                    "geniuk": +0.01, "jaw_whr": +0.02,
                    "lower_face_whr": +0.01, "forehead_whr": +0.02},
    "african":     {"carre": -0.03, "lefevre": -0.02, "hehman": -0.02,
                    "geniuk": -0.01, "jaw_whr": -0.02,
                    "lower_face_whr": -0.02, "forehead_whr": -0.03},
    "u":           {"carre": 0.00, "lefevre": 0.00, "hehman": 0.00,
                    "geniuk": 0.00, "jaw_whr": 0.00,
                    "lower_face_whr": 0.00, "forehead_whr": 0.00},
}

# v2.36 — per-ethnicity evidence quality (sample size & study count).
ETHNIC_EVIDENCE = {
    "caucasian":   {"quality": "high",   "sd_mult": 1.00,
                    "note": "Large samples (Carré 2008 n=900+, Hehman 2015 n=2k+)."},
    "east_asian":  {"quality": "medium", "sd_mult": 1.15,
                    "note": "Moderate samples (Wang 2022, n≈300)."},
    "south_asian": {"quality": "low",    "sd_mult": 1.30,
                    "note": "Limited samples (Robertson 2017, n≈80)."},
    "african":     {"quality": "low",    "sd_mult": 1.30,
                    "note": "Limited large-scale data."},
    "u":           {"quality": "medium", "sd_mult": 1.00,
                    "note": "Pooled unisex norms."},
}

AGE_NORM_SHIFT = [
    ("child",       0,  18, {k: -v for k, v in {"carre": 0.10, "lefevre": 0.10, "hehman": 0.08,
                              "geniuk": 0.04, "jaw_whr": 0.10,
                              "lower_face_whr": 0.10, "forehead_whr": 0.05}.items()}),
    ("young_adult", 18, 30, {"carre": 0.0, "lefevre": 0.0, "hehman": 0.0,
                              "geniuk": 0.0, "jaw_whr": 0.0,
                              "lower_face_whr": 0.0, "forehead_whr": 0.0}),
    ("adult",       30, 50, {"carre": +0.02, "lefevre": +0.02, "hehman": +0.02,
                              "geniuk": +0.01, "jaw_whr": +0.02,
                              "lower_face_whr": +0.02, "forehead_whr": +0.02}),
    ("mature",      50, 70, {"carre": +0.04, "lefevre": +0.04, "hehman": +0.04,
                              "geniuk": +0.02, "jaw_whr": +0.04,
                              "lower_face_whr": +0.04, "forehead_whr": +0.04}),
    ("elderly",     70, 200,{"carre": +0.05, "lefevre": +0.05, "hehman": +0.05,
                              "geniuk": +0.02, "jaw_whr": +0.05,
                              "lower_face_whr": +0.05, "forehead_whr": +0.05}),
]

# v2.26 — per-trait replication strength + signal_type
TRAITS = {
    "dominance":           {"beta":  0.45, "replication": "robust",
                            "signal_type": "perceived",
                            "source": "Carré 2008; Wang 2022 r≈0.18-0.30"},
    "aggression":          {"beta":  0.40, "replication": "contested",
                            "signal_type": "behavioral_proxy",
                            "source": "Carré 2008 r≈0.40 BUT Kosinski 2017 meta r≈0.08"},
    "trustworthiness":     {"beta": -0.30, "replication": "moderate",
                            "signal_type": "perceived",
                            "source": "Stirrat & Perrett 2010; Hehman 2013 (mostly males)"},
    "achievement_drive":   {"beta":  0.25, "replication": "weak",
                            "signal_type": "behavioral_proxy",
                            "source": "Lewis 2012; failed multiple replications"},
    "risk_taking":         {"beta":  0.30, "replication": "moderate",
                            "signal_type": "behavioral_proxy",
                            "source": "Welker 2015"},
    "perceived_threat":    {"beta":  0.38, "replication": "robust",
                            "signal_type": "perceived",
                            "source": "Hehman 2015; Geniuk 2017"},
    "leadership_emergence":{"beta":  0.22, "replication": "moderate",
                            "signal_type": "perceived",
                            "source": "Wong 2011 (CEO study)"},
}

CONFIDENCE_DAMP_BY_REPLICATION = {
    "robust":    1.00,
    "moderate":  0.80,
    "weak":      0.55,
    "contested": 0.40,
}


def _age_band(age: Optional[int]) -> tuple[str, dict]:
    if age is None or age < 0:
        return ("unknown", {k: 0.0 for k in NORMS_BY_GENDER["U"]})
    for name, lo, hi, shift in AGE_NORM_SHIFT:
        if lo <= age < hi:
            return (name, shift)
    return ("adult", {k: 0.0 for k in NORMS_BY_GENDER["U"]})


def _norm(metric: str, gender: str, ethnicity: str, age_shift: dict) -> tuple[float, float, dict]:
    """Combine baseline + ethnic + age shifts; v2.37 widens SD for low-evidence."""
    base_mean, base_sd = NORMS_BY_GENDER.get(gender, NORMS_BY_GENDER["U"])[metric]
    eth_shift = ETHNIC_NORM_SHIFT.get(ethnicity, {}).get(metric, 0.0)
    age_s     = age_shift.get(metric, 0.0)
    ev = ETHNIC_EVIDENCE.get(ethnicity, ETHNIC_EVIDENCE["u"])
    return (base_mean + eth_shift + age_s, base_sd * ev["sd_mult"], ev)


def _z_to_pct(z: float) -> float:
    return round(0.5 * (1.0 + math.erf(z / math.sqrt(2.0))) * 100.0, 1)


def _ratio_uncertainty(num_px: float, den_px: float, ratio: float) -> float:
    if num_px <= 0 or den_px <= 0:
        return 0.0
    rel_var = ((LANDMARK_JITTER_PX * math.sqrt(2)) / num_px) ** 2 + \
              ((LANDMARK_JITTER_PX * math.sqrt(2)) / den_px) ** 2
    return ratio * math.sqrt(rel_var)


def _classify_fwhr(z: float, gender: str) -> str:
    bias = 0.25 if gender == "F" else 0.0
    if z >= 2.0 - bias:  return "very_high"
    if z >= 1.0 - bias:  return "high"
    if z >  -1.0 + bias: return "average"
    if z > -2.0 + bias:  return "low"
    return "very_low"


def _confidence_label(abs_z: float, gender: str, replication: str = "moderate") -> str:
    """v2.26 — replication strength now damps confidence."""
    rep_mult = CONFIDENCE_DAMP_BY_REPLICATION.get(replication, 0.8)
    base = abs_z * (0.7 if gender == "F" else 1.0) * rep_mult
    if base >= 1.5: return "strong"
    if base >= 1.0: return "moderate"
    if base >= 0.5: return "weak"
    return "inconclusive"


def _polygon_area(points: list[tuple[float, float]]) -> float:
    """Shoelace formula."""
    n = len(points)
    if n < 3: return 0.0
    s = 0.0
    for i in range(n):
        x1, y1 = points[i]
        x2, y2 = points[(i + 1) % n]
        s += x1 * y2 - x2 * y1
    return abs(s) * 0.5


# ─────────────────────────────────────────────────────────────────────────────
# Narratives (Hinglish + English)
# ─────────────────────────────────────────────────────────────────────────────
NARRATIVES = {
    "carre": {
        "hi": "Carré-McCormick fWHR (bizygomatic ÷ brow-to-upper-lip) = {value}. Norm {norm_mean} ± {norm_sd}. Z = {z}, percentile = {pct}.",
        "en": "Carré-McCormick fWHR = {value}. Norm {norm_mean} ± {norm_sd}. Z = {z}, percentile = {pct}.",
    },
    "lefevre": {
        "hi": "Lefevre variant (bizygomatic ÷ brow-to-stomion) = {value}. Z = {z}, pct = {pct}.",
        "en": "Lefevre variant = {value}. Z = {z}, pct = {pct}.",
    },
    "hehman": {
        "hi": "Hehman variant (bizygomatic ÷ nasion-to-upper-lip) = {value}. Z = {z}, pct = {pct}.",
        "en": "Hehman variant = {value}. Z = {z}, pct = {pct}.",
    },
    "geniuk": {
        "hi": "Geniuk full-face WHR (bizygomatic ÷ trichion-to-chin) = {value}. Z = {z}, pct = {pct}.",
        "en": "Geniuk full-face WHR = {value}. Z = {z}, pct = {pct}.",
    },
    "jaw_whr": {
        "hi": "Jaw-WHR (jaw width ÷ brow-to-upper-lip; Whitehouse 2015) = {value}. Z = {z}, pct = {pct}.",
        "en": "Jaw-WHR (Whitehouse 2015) = {value}. Z = {z}, pct = {pct}.",
    },
    "lower_face_whr": {
        "hi": "Lower-face WHR (jaw_w ÷ stomion-to-chin) = {value}. Lower-jaw dominance signal. Z = {z}, pct = {pct}.",
        "en": "Lower-face WHR = {value}. Lower-jaw dominance signal. Z = {z}, pct = {pct}.",
    },
    "forehead_whr": {
        "hi": "Forehead-WHR (forehead_w ÷ forehead_h) = {value}. Z = {z}, pct = {pct}.",
        "en": "Forehead-WHR = {value}. Z = {z}, pct = {pct}.",
    },
}

TRAIT_LABELS = {
    "dominance":            {"hi": "Dominance",            "en": "Perceived dominance"},
    "aggression":           {"hi": "Aggression",           "en": "Reactive aggression"},
    "trustworthiness":      {"hi": "Trustworthiness",      "en": "Perceived trustworthiness"},
    "achievement_drive":    {"hi": "Achievement drive",    "en": "Achievement striving"},
    "risk_taking":          {"hi": "Risk-taking",          "en": "Risk-taking propensity"},
    "perceived_threat":     {"hi": "Threat perception",    "en": "Threat perception by others"},
    "leadership_emergence": {"hi": "Leadership emergence", "en": "Leadership emergence"},
}


# ─────────────────────────────────────────────────────────────────────────────
# Main engine
# ─────────────────────────────────────────────────────────────────────────────
def run(landmarks_norm: Sequence[tuple[float, float, float]],
        image_w: int, image_h: int,
        hairline_mm_above_mesh_top: Optional[float] = None,
        gender: str = "U",
        ethnicity: Optional[str] = None,
        age: Optional[int] = None,
        anthropometry_result: Optional[dict] = None,
        yaw_deg: float = 0.0,
        ) -> dict:
    if not landmarks_norm or len(landmarks_norm) < 478:
        return {"engine": "fwhr", "ok": False, "error": "insufficient_landmarks"}

    yaw_abs = abs(float(yaw_deg or 0.0))
    if yaw_abs > YAW_FRONTAL_REFUSE:
        return {"engine": "fwhr", "version": 2, "ok": False,
                "error": "non_frontal_view",
                "yaw_deg": round(yaw_deg, 2),
                "max_allowed_yaw_deg": YAW_FRONTAL_REFUSE,
                "hint": "fWHR foreshortens with head turn — re-shoot at yaw ≤ 8°."}
    frontal_confidence = "high" if yaw_abs <= YAW_FRONTAL_OK else "low"

    pts = np.array([(x * image_w, y * image_h, z * image_w) for x, y, z in landmarks_norm],
                   dtype=np.float64)

    def get3d(idx_or_name):
        idx = LMK[idx_or_name] if isinstance(idx_or_name, str) else idx_or_name
        return pts[idx]

    origin, R = _build_face_frame(get3d)

    def fp(idx_or_name) -> np.ndarray:
        idx = LMK[idx_or_name] if isinstance(idx_or_name, str) else idx_or_name
        return R @ (pts[idx] - origin)

    iod_px = abs(fp(L_INNER_EYE)[0] - fp(R_INNER_EYE)[0])
    if iod_px <= 0:
        return {"engine": "fwhr", "version": 2, "ok": False, "error": "invalid_iod"}
    px_per_mm = iod_px / IOD_BASELINE_MM

    # Bizygomatic — primary + alt cross-check
    bizyg_primary_px   = abs(fp(454)[0] - fp(234)[0])
    bizyg_alt_px       = abs(fp(345)[0] - fp(116)[0])
    bizyg_px           = max(bizyg_primary_px, bizyg_alt_px)
    bizyg_landmark_used = "234/454" if bizyg_primary_px >= bizyg_alt_px else "116/345"
    bizyg_disagreement = abs(bizyg_primary_px - bizyg_alt_px) / max(bizyg_primary_px, bizyg_alt_px) * 100

    # v2.21 — 3D cheekbone z-projection (lateral cheek depth)
    cheek_z_R = fp(234)[2]
    cheek_z_L = fp(454)[2]
    nose_z    = fp("nose_tip")[2]
    # Mediapipe z is unitless ~image-width-normalized; raw mm conversion is
    # not anatomically calibrated. Treat as ORDINAL signal only and clamp.
    raw_diff_mm = float((nose_z - (cheek_z_R + cheek_z_L) / 2.0) / px_per_mm)
    cheek_projection_mm = round(max(-60.0, min(60.0, raw_diff_mm)), 1)
    # Map raw delta → bounded ordinal z (typical face delta ~10-30 in our units)
    cheek_projection_z = round(max(-3.0, min(3.0, raw_diff_mm / 20.0)), 3)

    # Jaw width (gonion-gonion approximation)
    jaw_width_px = abs(fp(397)[0] - fp(172)[0])

    # Vertical anchors
    mesh_top_y       = fp(FOREHEAD)[1]
    if hairline_mm_above_mesh_top and hairline_mm_above_mesh_top > 0:
        offset_mm = min(float(hairline_mm_above_mesh_top), 60.0)
        trichion_y = mesh_top_y + offset_mm * px_per_mm
    else:
        trichion_y = mesh_top_y

    brow_y       = (fp(107)[1] + fp(336)[1]) / 2.0
    nasion_y     = fp("nose_root")[1]
    upper_lip_y  = fp(0)[1]
    stomion_y    = fp(13)[1]
    chin_y       = fp(CHIN)[1]
    lower_lip_y  = fp(17)[1]

    # Heights
    h_carre   = abs(brow_y    - upper_lip_y)
    h_lefevre = abs(brow_y    - stomion_y)
    h_hehman  = abs(nasion_y  - upper_lip_y)
    h_geniuk  = abs(trichion_y - chin_y)
    h_lower   = abs(stomion_y - chin_y)             # v2.22
    h_fore    = abs(trichion_y - brow_y)            # v2.23

    # Forehead width — use outer temple landmarks (21/251), not inner
    # frontalis bulges (109/338) which underestimate by ~3×.
    forehead_w_px = abs(fp(251)[0] - fp(21)[0])

    # v2.25 — Smile / expression detection
    # If mouth corners (61/291) are notably above stomion (13), it's a smile.
    mouth_corner_y_avg = (fp(61)[1] + fp(291)[1]) / 2.0
    smile_lift_mm = float(round((mouth_corner_y_avg - stomion_y) / px_per_mm, 2))
    is_smiling = bool(smile_lift_mm > 5.0)        # >5mm above stomion = clear smile
    mouth_open_mm = float(round(abs(fp(13)[1] - fp(14)[1]) / px_per_mm, 2))

    # Norm resolution
    g_norm   = (gender or "U").upper()
    if g_norm not in ("M", "F", "U"): g_norm = "U"
    eth_norm = (ethnicity or "U").lower()
    if eth_norm not in ETHNIC_EVIDENCE: eth_norm = "u"
    age_band, age_shift = _age_band(age)

    def metric(name: str, num_px: float, den_px: float) -> dict:
        if den_px < DENOM_FLOOR_PX or num_px <= 0:
            return {"name": name, "ok": False, "error": "denominator_too_small"}
        value = num_px / den_px
        n_mean, n_sd, ev = _norm(name, g_norm, eth_norm, age_shift)
        z = (value - n_mean) / n_sd if n_sd > 0 else 0.0
        sigma = _ratio_uncertainty(num_px, den_px, value)
        z_lo = (value - sigma - n_mean) / n_sd if n_sd > 0 else 0.0
        z_hi = (value + sigma - n_mean) / n_sd if n_sd > 0 else 0.0
        cls  = _classify_fwhr(z, g_norm)
        nar  = NARRATIVES.get(name, {})
        out = {
            "name":            name,
            "ok":              True,
            "value":           round(value, 4),
            "value_ci_low":    round(value - sigma, 4),
            "value_ci_high":   round(value + sigma, 4),
            "ratio_sigma":     round(sigma, 4),
            "norm_mean":       round(n_mean, 3),
            "norm_sd":         round(n_sd, 3),
            "norm_evidence_quality": ev["quality"],            # v2.36
            "norm_evidence_note":    ev["note"],               # v2.36
            "z":               round(z, 3),
            "z_ci_low":        round(min(z_lo, z_hi), 3),
            "z_ci_high":       round(max(z_lo, z_hi), 3),
            "percentile":      _z_to_pct(z),
            "classification":  cls,
            "numerator_mm":    round(num_px / px_per_mm, 1),
            "denominator_mm":  round(den_px / px_per_mm, 1),
            "test_retest_band": [round(value - TEST_RETEST_FWHR_SD, 3),    # v2.29
                                 round(value + TEST_RETEST_FWHR_SD, 3)],
            "narrative": {
                "hi": nar.get("hi", "").format(value=f"{value:.3f}", z=f"{z:+.2f}",
                                               pct=f"{_z_to_pct(z):.1f}",
                                               norm_mean=f"{n_mean:.2f}",
                                               norm_sd=f"{n_sd:.2f}"),
                "en": nar.get("en", "").format(value=f"{value:.3f}", z=f"{z:+.2f}",
                                               pct=f"{_z_to_pct(z):.1f}",
                                               norm_mean=f"{n_mean:.2f}",
                                               norm_sd=f"{n_sd:.2f}"),
            },
        }
        # v2.28 — outlier flag
        if abs(z) > 3.0:
            out["outlier_flag"] = True
            out["outlier_note"] = ("Value > 3σ from norm — possible measurement artifact, "
                                   "anatomical specificity, or non-neutral expression.")
        return out

    variants = {
        "carre":          metric("carre",          bizyg_px,      h_carre),
        "lefevre":        metric("lefevre",        bizyg_px,      h_lefevre),
        "hehman":         metric("hehman",         bizyg_px,      h_hehman),
        "geniuk":         metric("geniuk",         bizyg_px,      h_geniuk),
        "jaw_whr":        metric("jaw_whr",        jaw_width_px,  h_carre),
        "lower_face_whr": metric("lower_face_whr", jaw_width_px,  h_lower),     # v2.22
        "forehead_whr":   metric("forehead_whr",   forehead_w_px, h_fore),      # v2.23
    }

    primary = variants["carre"]

    # ── Trait predictions (v2.26 + v2.27) ─────────────────────────────────
    trait_predictions: dict = {}
    if primary.get("ok"):
        z = primary["z"]
        gender_mult = 0.7 if g_norm == "F" else 1.0
        for trait, meta in TRAITS.items():
            effect_z = z * meta["beta"] * gender_mult
            trait_predictions[trait] = {
                "label":              TRAIT_LABELS[trait]["en"],
                "label_hi":           TRAIT_LABELS[trait]["hi"],
                "predicted_z":        round(effect_z, 3),
                "percentile":         _z_to_pct(effect_z),
                "direction":          ("above_average" if effect_z > 0.25 else
                                        "below_average" if effect_z < -0.25 else "average"),
                "confidence":         _confidence_label(abs(effect_z), g_norm,
                                                         meta["replication"]),
                "replication_strength": meta["replication"],     # v2.26
                "signal_type":        meta["signal_type"],       # v2.27
                "source":             meta["source"],
            }

    # ── Bilateral half-fWHR ───────────────────────────────────────────────
    midline_x = (fp(R_INNER_EYE)[0] + fp(L_INNER_EYE)[0]) / 2.0
    half_r_w  = abs(midline_x - fp(234)[0])
    half_l_w  = abs(fp(454)[0] - midline_x)
    bilateral = {}
    if h_carre >= DENOM_FLOOR_PX:
        bilateral = {
            "right_half_fwhr": round((2.0 * half_r_w) / h_carre, 4),
            "left_half_fwhr":  round((2.0 * half_l_w) / h_carre, 4),
        }
        bilateral["asymmetry_pct"] = round(
            abs(bilateral["right_half_fwhr"] - bilateral["left_half_fwhr"]) /
            max(bilateral["right_half_fwhr"], bilateral["left_half_fwhr"]) * 100, 2)
        bilateral["dominant_side"] = ("right" if half_r_w > half_l_w else "left")

    # ── BMI / face-fullness confound ──────────────────────────────────────
    bmi_flag = {"flag": False, "cheek_to_jaw_ratio": None}
    if jaw_width_px >= DENOM_FLOOR_PX:
        c2j = bizyg_px / jaw_width_px
        bmi_flag["cheek_to_jaw_ratio"] = round(c2j, 3)
        if c2j > 1.50:
            bmi_flag["flag"] = True
            bmi_flag["note"] = ("Cheekbone-to-jaw ratio elevated; fWHR may be "
                                "inflated by face fullness (BMI confound).")

    # ── Engine-1 cross-validation ────────────────────────────────────────
    eng1_xv = None
    if anthropometry_result and isinstance(anthropometry_result, dict):
        fs7 = anthropometry_result.get("face_shape_7") or {}
        face_shape = fs7.get("shape")
        cls = anthropometry_result.get("classifications") or {}
        eng1_xv = {
            "face_shape":   face_shape,
            "length_class": cls.get("face_shape_length_class"),
            "jaw_class":    cls.get("face_shape_jaw_class"),
        }
        if primary.get("ok"):
            expected_high = face_shape in ("round", "square")
            expected_low  = face_shape in ("oblong", "rectangle")
            if expected_high and primary["z"] < -0.5:
                eng1_xv["consistency_flag"] = "face_shape_suggests_higher_fwhr_than_measured"
            elif expected_low and primary["z"] > 0.5:
                eng1_xv["consistency_flag"] = "face_shape_suggests_lower_fwhr_than_measured"
            else:
                eng1_xv["consistency_flag"] = "consistent"

    # ── v2.34 — Compactness index (jaw polygon area / bbox area) ─────────
    jaw_outline_idx = [10, 338, 297, 332, 284, 251, 389, 356, 454, 323,
                        361, 288, 397, 365, 379, 378, 400, 377, 152,
                        148, 176, 149, 150, 136, 172, 58, 132, 93, 234,
                        127, 162, 21, 54, 103, 67, 109]
    jaw_pts2d = [(fp(i)[0], fp(i)[1]) for i in jaw_outline_idx]
    poly_area = _polygon_area(jaw_pts2d)
    xs = [p[0] for p in jaw_pts2d]; ys = [p[1] for p in jaw_pts2d]
    bbox_area = (max(xs) - min(xs)) * (max(ys) - min(ys))
    compactness = round(poly_area / bbox_area, 4) if bbox_area > 0 else 0.0
    # 0.78 = oval norm; >0.85 = round/full; <0.72 = oblong/narrow
    compactness_class = ("round_full" if compactness > 0.85 else
                          "oval_balanced" if compactness > 0.72 else
                          "narrow_elongated")

    # ── v2.35 — Eye placement contribution (eye_w / face_w) ──────────────
    eye_w_total = (abs(fp(133)[0] - fp(33)[0]) + abs(fp(263)[0] - fp(362)[0])) / 2.0
    face_w_px = bizyg_px
    eye_to_face_w = round(eye_w_total / face_w_px, 4) if face_w_px > 0 else None
    eye_placement = {
        "eye_width_to_face_width": eye_to_face_w,
        "norm":                    0.215,           # Gomez-Valdes 2013
        "deviation_pct": round((eye_to_face_w - 0.215) / 0.215 * 100, 2)
                         if eye_to_face_w else None,
        "note": ("Eye placement modulates fWHR perception — narrower eyes "
                 "relative to face amplify dominance signal."),
    }

    # ── v2.21 cheek z-projection block ───────────────────────────────────
    cheek_3d = {
        "lateral_cheek_z_projection_mm": cheek_projection_mm,
        "z_score":                       cheek_projection_z,
        "interpretation": ("forward_projecting_cheekbones" if cheek_projection_z > 0.5 else
                           "average_projection" if cheek_projection_z > -0.5 else
                           "flatter_midface"),
        "note": ("3D depth proxy — Mediapipe z-coords are relative, not metric. "
                 "Use as ordinal signal, not absolute mm."),
    }

    # ── v2.25 expression block ───────────────────────────────────────────
    expression = {
        "smile_lift_mm":    smile_lift_mm,
        "mouth_open_mm":    mouth_open_mm,
        "is_smiling":       is_smiling,
        "is_mouth_open":    mouth_open_mm > 4.0,
        "expression_neutral": (not is_smiling and mouth_open_mm < 4.0),
    }
    if not expression["expression_neutral"]:
        expression["warning"] = ("Non-neutral expression detected — fWHR can be "
                                  "inflated 3-7%. Re-shoot with neutral face for "
                                  "best accuracy.")

    # ── v2.33 — Sexual dimorphism 2D vector + 4-quadrant typology ────────
    sex_vector = None
    if primary.get("ok") and variants["jaw_whr"].get("ok"):
        fz = primary["z"]
        jz = variants["jaw_whr"]["z"]
        if   fz >  0.3 and jz >  0.3: quadrant = "high_cheek_high_jaw_classic_masculine"
        elif fz >  0.3 and jz <= 0.3: quadrant = "high_cheek_low_jaw_maxillary_dominant"
        elif fz <= 0.3 and jz >  0.3: quadrant = "low_cheek_high_jaw_mandibular_dominant"
        else:                          quadrant = "low_cheek_low_jaw_neotenous_feminine"
        sex_vector = {
            "fwhr_z":   fz,
            "jaw_z":    jz,
            "quadrant": quadrant,
            "magnitude": round(math.sqrt(fz**2 + jz**2), 3),
            "angle_deg": round(math.degrees(math.atan2(jz, fz)), 1),
        }

    # ── Composite scores ──────────────────────────────────────────────────
    composite: dict = {}
    if primary.get("ok") and variants["jaw_whr"].get("ok"):
        eye_y = (fp(159)[1] + fp(386)[1]) / 2.0
        brow_prominence_px = abs(brow_y - eye_y)
        brow_z = (brow_prominence_px / px_per_mm - 12.0) / 3.5
        dom_z = (primary["z"] * 0.5 +
                 variants["jaw_whr"]["z"] * 0.3 +
                 brow_z * 0.2)
        composite["dominance_signal"] = {
            "z":          round(dom_z, 3),
            "percentile": _z_to_pct(dom_z),
            "components": {
                "fwhr_z":              primary["z"],
                "jaw_whr_z":           variants["jaw_whr"]["z"],
                "brow_prominence_z":   round(brow_z, 3),
                "brow_prominence_mm":  round(brow_prominence_px / px_per_mm, 1),
            },
        }
        masc_z = dom_z
        composite["masculinity_signal"] = {
            "z":          round(masc_z, 3),
            "percentile": _z_to_pct(masc_z),
            "interpretation": (
                "highly_masculinized" if masc_z >= 1.0 else
                "above_average_masculinity" if masc_z >= 0.3 else
                "androgynous" if masc_z > -0.3 else
                "below_average_masculinity" if masc_z > -1.0 else
                "highly_feminized"
            ),
            "note": "Composite of fWHR + jaw width + brow prominence.",
        }

    # ── v2.32 — Cultural inversion flag ──────────────────────────────────
    cultural_context = None
    if eth_norm in ("east_asian", "south_asian") and primary.get("ok") and primary["z"] < -0.3:
        cultural_context = {
            "flag": "low_fwhr_culturally_preferred",
            "note": ("In East/South Asian beauty standards, lower fWHR (oval, "
                     "softer midface) is often considered more attractive. "
                     "Low dominance score should NOT be read as a deficit."),
        }

    # ── Caveats / limitations ────────────────────────────────────────────
    caveats = [
        "fWHR predicts perceived traits, not behavior with certainty.",
        "Female effect sizes are ~30% weaker (Kosinski 2017 meta-analysis).",
        "Population-level statistics — individual variation is wide.",
        "BMI / face-fullness can inflate fWHR independent of testosterone.",
        "Multiple operationalizations exist; we report all seven.",
        # v2.30
        ("Carré 2014: fWHR predicts dominance reliably ONLY when cortisol is low. "
         "We have no cortisol proxy — predictions assume average cortisol."),
        # v2.29
        ("Test-retest reliability: same face, slightly different lighting/pose "
         "→ ±0.05 fWHR variation expected. Treat values within this band as equivalent."),
        # v2.31
        ("fWHR is largely set during puberty (~age 14-18) by testosterone exposure; "
         "adult lifestyle changes barely move it."),
    ]
    if frontal_confidence == "low":
        caveats.insert(0, "Pose was non-strictly frontal (yaw > 8°); foreshortening "
                          "may have shrunk bizygomatic width.")
    if bmi_flag["flag"]:
        caveats.insert(0, bmi_flag.get("note", ""))
    if expression.get("warning"):
        caveats.insert(0, expression["warning"])
    if cultural_context:
        caveats.insert(0, cultural_context["note"])

    return {
        "engine":             "fwhr",
        "version":            2,
        "ok":                 True,
        "frame":              "canonical_3d_pose_corrected",
        "iod_baseline_mm":    IOD_BASELINE_MM,
        "px_per_mm":          round(px_per_mm, 3),
        "yaw_deg":            round(yaw_deg, 2),
        "frontal_view_confidence": frontal_confidence,
        "inputs": {
            "gender":   g_norm,
            "ethnicity": eth_norm,
            "age":      age,
            "age_band": age_band,
            "ethnic_evidence_quality": ETHNIC_EVIDENCE.get(eth_norm, {}).get("quality"),
        },
        # v2.24 — anatomical clarification
        "anatomical_notes": {
            "bizygomatic_landmarks": ("Mediapipe 234/454 are MAXILLARY landmarks "
                                      "(upper-cheek surface), not the bony zygion. "
                                      "Approximation acceptable for fWHR research; "
                                      "true bony zygion would require lateral X-ray."),
            "jaw_width_landmarks":   "Mediapipe 172/397 ≈ gonial angle on skin surface.",
            "reference_frame":       "Pose-corrected canonical 3D frame (shared with Engines 1-3).",
        },
        "bizygomatic": {
            "primary_px":         round(bizyg_primary_px, 2),
            "alt_px":             round(bizyg_alt_px, 2),
            "used_px":            round(bizyg_px, 2),
            "used_landmarks":     bizyg_landmark_used,
            "disagreement_pct":   round(bizyg_disagreement, 2),
            "primary_mm":         round(bizyg_primary_px / px_per_mm, 1),
            "jaw_width_mm":       round(jaw_width_px / px_per_mm, 1),
            "forehead_width_mm":  round(forehead_w_px / px_per_mm, 1),
        },
        "cheekbone_3d":      cheek_3d,            # v2.21
        "expression":        expression,          # v2.25
        "variants":          variants,
        "primary_variant":   "carre",
        "primary":           {
            "value":          primary.get("value"),
            "z":              primary.get("z"),
            "percentile":     primary.get("percentile"),
            "classification": primary.get("classification"),
        } if primary.get("ok") else None,
        "trait_predictions": trait_predictions,
        "bilateral":         bilateral,
        "bmi_confound":      bmi_flag,
        "compactness":       {                                            # v2.34
            "value": compactness,
            "class": compactness_class,
            "norm":  0.78,
        },
        "eye_placement":     eye_placement,       # v2.35
        "sex_dimorphism_vector": sex_vector,      # v2.33
        "engine1_cross_validation": eng1_xv,
        "composite_scores":  composite,
        "cultural_context":  cultural_context,    # v2.32
        "caveats":           caveats,
        "interpretation":    _summary(primary, trait_predictions, composite,
                                      g_norm, eth_norm, age_band, frontal_confidence,
                                      sex_vector, expression),
    }


def _summary(primary, traits, composite, gender, ethnicity, age_band,
             frontal, sex_vec, expression) -> dict:
    out = []
    if primary and primary.get("ok"):
        out.append(f"fWHR (Carré) = {primary['value']:.3f}, Z = {primary['z']:+.2f} "
                   f"(percentile {primary['percentile']:.1f}, classification "
                   f"{primary['classification']}).")
    out.append(f"Inputs: gender={gender}, ethnicity={ethnicity}, age_band={age_band}.")
    if frontal == "low":
        out.append("⚠ Non-frontal pose; bizygomatic foreshortening may have biased the value.")
    if not expression.get("expression_neutral"):
        out.append("⚠ Non-neutral expression — re-shoot recommended.")
    if traits:
        # Only report traits with at least 'weak' confidence and replication ≥ moderate
        strong_traits = [(k, v) for k, v in traits.items()
                         if v["confidence"] != "inconclusive"
                         and v["replication_strength"] in ("robust", "moderate")]
        ranked = sorted(strong_traits, key=lambda kv: abs(kv[1]["predicted_z"]),
                         reverse=True)[:2]
        for name, p in ranked:
            out.append(f"{p['label']}: {p['direction']} (z={p['predicted_z']:+.2f}, "
                       f"conf={p['confidence']}, repl={p['replication_strength']}).")
    if sex_vec:
        out.append(f"Sex-dimorphism quadrant: {sex_vec['quadrant']} "
                   f"(magnitude {sex_vec['magnitude']}).")
    if composite.get("masculinity_signal"):
        m = composite["masculinity_signal"]
        out.append(f"Masculinity composite: {m['interpretation']} (z={m['z']:+.2f}).")
    return {"summary": " ".join(out), "highlights": out}
