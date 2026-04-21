"""
Engine 5 — Health & Wellness Indicators (face-derived).

Pixel-level color analysis on:
  • cheeks / forehead / nose / chin   (Lab + HSV)
  • sclera (whites of eyes)            → jaundice / fatigue redness
  • conjunctival rim (lower lid)       → anemia (pallor)
  • lip vermilion                      → cyanosis / anemia / dehydration
  • mouth-corner crack region          → angular cheilitis (B-vit deficiency)
  • under-eye region                   → periorbital edema / dark circles

Composite scores:
  • pallor_index           (anemia proxy)
  • erythema_index         (rosacea / inflammation / heat)
  • jaundice_index         (sclera + skin yellow)
  • cyanosis_index         (lip blue)
  • hydration_index        (lip dryness + skin texture)
  • fatigue_index          (dark circles + sclera redness + droop)
  • inflammation_index     (acne / red blob density)
  • vitality_score         (overall composite, 0-100)

DISCLAIMER: This engine produces SCREENING INDICATORS, not medical
diagnoses.  All flagged conditions require physician confirmation.

Built with foundation v3 cache (skin sampling, dark_circles, oiliness,
wrinkles, iris/pupil) — re-uses precomputed metrics, adds new pixel
extractions for sclera / conjunctiva / lips that foundation does not
cover.
"""
from __future__ import annotations

import math
from typing import Sequence, Optional

import numpy as np
import cv2

from .anthropometry import (
    LM as LMK,
    IOD_BASELINE_MM,
    R_INNER_EYE,
    L_INNER_EYE,
)


# ─────────────────────────────────────────────────────────────────────────────
# Reference norms (Lab / HSV)
# Sources: Saidi 2014 (Lab skin), Sheth 1997 (conjunctival pallor),
# Liu 2018 (lip color spectroscopy), Hosoi 2019 (sclera ITA).
# ─────────────────────────────────────────────────────────────────────────────
NORMS = {
    "cheek_a_redness":      {"low": 4.0,  "norm": 9.0,  "high": 16.0},  # Lab a
    "cheek_b_yellowness":   {"low": 8.0,  "norm": 14.0, "high": 22.0},  # Lab b
    "sclera_b_yellow":      {"low": -2.0, "norm":  3.0, "high": 10.0},  # Lab b in sclera
    "sclera_redness_a":     {"low": -2.0, "norm":  2.0, "high":  8.0},  # Lab a in sclera
    "lip_a_redness":        {"low": 8.0,  "norm": 18.0, "high": 28.0},  # Lab a in lip
    "lip_b_blue_tinge":     {"low": -8.0, "norm":  4.0, "high": 12.0},  # Lab b lip; very low = cyanosis
    "lip_L_paleness":       {"low": 35.0, "norm": 45.0, "high": 60.0},  # Lab L lip; very high = pallor
    "conjunctiva_a":        {"low": 8.0,  "norm": 18.0, "high": 28.0},  # Lab a inner lower lid
    "skin_L_relative":      {"low": -8.0, "norm":  0.0, "high":  8.0},  # cheek_L - forehead_L (negative=pale cheek)
}


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────
def _decode_image(image_bytes: bytes) -> Optional[np.ndarray]:
    """Decode bytes → BGR uint8 numpy."""
    arr = np.frombuffer(image_bytes, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    return img


def _rgb_to_lab(rgb_mean: tuple[float, float, float]) -> tuple[float, float, float]:
    """Convert a single RGB triplet → Lab."""
    px = np.array([[[rgb_mean[2], rgb_mean[1], rgb_mean[0]]]], dtype=np.uint8)  # BGR
    lab = cv2.cvtColor(px, cv2.COLOR_BGR2LAB)[0, 0]
    L = lab[0] * (100.0 / 255.0)
    a = lab[1] - 128.0
    b = lab[2] - 128.0
    return (float(L), float(a), float(b))


def _sample_polygon(img_bgr: np.ndarray,
                    polygon_norm: list[tuple[float, float]],
                    image_w: int, image_h: int) -> Optional[dict]:
    """Mean BGR + Lab + HSV inside a polygon defined in normalized coords."""
    pts_px = np.array([[int(x * image_w), int(y * image_h)] for x, y in polygon_norm],
                      dtype=np.int32)
    if len(pts_px) < 3:
        return None
    mask = np.zeros(img_bgr.shape[:2], dtype=np.uint8)
    cv2.fillPoly(mask, [pts_px], 255)
    if int(mask.sum() / 255) < 8:
        return None
    masked = cv2.bitwise_and(img_bgr, img_bgr, mask=mask)
    indices = np.where(mask > 0)
    bgr_pixels = img_bgr[indices]
    if len(bgr_pixels) == 0:
        return None
    bgr_mean = bgr_pixels.mean(axis=0)
    rgb_mean = (float(bgr_mean[2]), float(bgr_mean[1]), float(bgr_mean[0]))
    L, a, b = _rgb_to_lab(rgb_mean)
    # HSV
    hsv = cv2.cvtColor(np.array([[bgr_mean]], dtype=np.uint8), cv2.COLOR_BGR2HSV)[0, 0]
    # Texture: std on grayscale
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    tex_std = float(gray[indices].std()) if len(gray[indices]) > 0 else 0.0
    return {
        "rgb_mean":  [round(rgb_mean[0], 1), round(rgb_mean[1], 1), round(rgb_mean[2], 1)],
        "lab":       {"L": round(L, 2), "a": round(a, 2), "b": round(b, 2)},
        "hsv":       [int(hsv[0]), int(hsv[1]), int(hsv[2])],
        "texture_std": round(tex_std, 2),
        "n_pixels":  int(len(bgr_pixels)),
    }


def _classify_index(value: float, norm: dict, invert: bool = False) -> dict:
    """Map a measured value to (severity, score 0-100)."""
    lo, mid, hi = norm["low"], norm["norm"], norm["high"]
    if invert:
        lo, hi = hi, lo
    # Map: hi → 100, mid → 50, lo → 0 (linear in two segments)
    if value <= mid:
        score = 50.0 * max(0.0, (value - lo) / (mid - lo)) if mid != lo else 50.0
    else:
        score = 50.0 + 50.0 * min(1.0, (value - mid) / (hi - mid)) if hi != mid else 50.0
    severity = ("normal" if 35 <= score <= 65 else
                "mild" if 20 <= score < 35 or 65 < score <= 80 else
                "marked")
    return {"value": round(value, 2), "score_0_100": round(score, 1), "severity": severity}


def _z_to_pct(z: float) -> float:
    return round(0.5 * (1.0 + math.erf(z / math.sqrt(2.0))) * 100.0, 1)


# ─────────────────────────────────────────────────────────────────────────────
# Region polygons (Mediapipe landmark indices)
# ─────────────────────────────────────────────────────────────────────────────
SCLERA_R = [33, 7, 163, 144, 145, 153, 154, 155]      # right outer eye boundary
SCLERA_L = [263, 249, 390, 373, 374, 380, 381, 382]   # left outer eye boundary
LIP_OUTER  = [61, 185, 40, 39, 37, 0, 267, 269, 270, 409, 291,
              375, 321, 405, 314, 17, 84, 181, 91, 146]
LIP_VERMILION_UPPER = [0, 267, 269, 270, 409, 291, 61, 185, 40, 39, 37]
# Conjunctival rim — sample just below lower eyelid (inside eye socket)
CONJUNCTIVA_R = [22, 23, 24, 110, 25, 31, 228, 229, 230, 231, 232]
CONJUNCTIVA_L = [252, 253, 254, 339, 255, 261, 448, 449, 450, 451, 452]
# Mouth-corner crack regions (angular cheilitis): tiny patch around lm 61, 291
MOUTH_CORNER_R = [61, 76, 62, 78, 95]
MOUTH_CORNER_L = [291, 306, 292, 308, 324]
# Under-eye for periorbital
UNDER_EYE_R = [120, 119, 230, 229, 228, 31, 226, 113, 226, 130]
UNDER_EYE_L = [349, 348, 450, 449, 448, 261, 446, 342, 446, 359]


# ─────────────────────────────────────────────────────────────────────────────
# Main engine
# ─────────────────────────────────────────────────────────────────────────────
def run(landmarks_norm: Sequence[tuple[float, float, float]],
        image_w: int, image_h: int,
        image_bytes: Optional[bytes] = None,
        foundation_skin: Optional[dict] = None,
        foundation_dark_circles: Optional[dict] = None,
        foundation_oiliness: Optional[dict] = None,
        foundation_wrinkles: Optional[dict] = None,
        foundation_iris: Optional[dict] = None,
        gender: str = "U",
        ethnicity: Optional[str] = None,
        age: Optional[int] = None,
        ) -> dict:
    if not landmarks_norm or len(landmarks_norm) < 478:
        return {"engine": "health", "ok": False, "error": "insufficient_landmarks"}
    if image_bytes is None:
        return {"engine": "health", "ok": False,
                "error": "image_bytes_required",
                "hint": "Engine 5 needs raw image pixels for color analysis."}

    img = _decode_image(image_bytes)
    if img is None:
        return {"engine": "health", "ok": False, "error": "image_decode_failed"}

    H, W = img.shape[:2]
    # If cached image was downscaled by foundation, our landmarks are normalized
    # so they map to whatever current size we re-decoded — use img H/W.

    pts_norm = [(p[0], p[1]) for p in landmarks_norm]

    def poly(idx_list):
        return [(pts_norm[i][0], pts_norm[i][1]) for i in idx_list]

    # ── Sample regions ────────────────────────────────────────────────────
    sclera_r = _sample_polygon(img, poly(SCLERA_R), W, H)
    sclera_l = _sample_polygon(img, poly(SCLERA_L), W, H)
    lip      = _sample_polygon(img, poly(LIP_OUTER), W, H)
    conj_r   = _sample_polygon(img, poly(CONJUNCTIVA_R), W, H)
    conj_l   = _sample_polygon(img, poly(CONJUNCTIVA_L), W, H)
    mc_r     = _sample_polygon(img, poly(MOUTH_CORNER_R), W, H)
    mc_l     = _sample_polygon(img, poly(MOUTH_CORNER_L), W, H)
    under_r  = _sample_polygon(img, poly(UNDER_EYE_R), W, H)
    under_l  = _sample_polygon(img, poly(UNDER_EYE_L), W, H)

    def avg_lab(*samples):
        vals = [s for s in samples if s]
        if not vals:
            return None
        L = sum(s["lab"]["L"] for s in vals) / len(vals)
        a = sum(s["lab"]["a"] for s in vals) / len(vals)
        b = sum(s["lab"]["b"] for s in vals) / len(vals)
        tx = sum(s["texture_std"] for s in vals) / len(vals)
        return {"L": round(L, 2), "a": round(a, 2), "b": round(b, 2),
                "texture_std": round(tx, 2)}

    sclera_avg = avg_lab(sclera_r, sclera_l)
    conj_avg   = avg_lab(conj_r, conj_l)

    # Pull foundation skin (cheek + forehead) for relative pallor calc
    cheek_L = cheek_a = cheek_b = forehead_L = None
    if foundation_skin and foundation_skin.get("ok"):
        per = foundation_skin.get("per_region", {})
        cl = per.get("cheek_l") or {}; cr = per.get("cheek_r") or {}
        ch_lab_l = cl.get("lab_mean") or [None, None, None]
        ch_lab_r = cr.get("lab_mean") or [None, None, None]
        if all(x is not None for x in ch_lab_l) and all(x is not None for x in ch_lab_r):
            cheek_L = (ch_lab_l[0] + ch_lab_r[0]) / 2.0
            cheek_a = (ch_lab_l[1] + ch_lab_r[1]) / 2.0
            cheek_b = (ch_lab_l[2] + ch_lab_r[2]) / 2.0
        fh = per.get("forehead") or {}
        fh_lab = fh.get("lab_mean") or [None, None, None]
        if fh_lab[0] is not None:
            forehead_L = fh_lab[0]

    # ── Build indicator scores ────────────────────────────────────────────
    indicators = {}

    # 1. Pallor (relative + lip)
    pallor_components = []
    if cheek_L is not None and forehead_L is not None:
        rel_L = cheek_L - forehead_L
        indicators["relative_skin_pallor"] = {
            **_classify_index(rel_L, NORMS["skin_L_relative"], invert=True),
            "metric": "cheek_L − forehead_L",
            "interpretation": ("cheeks_paler_than_forehead" if rel_L < -3
                                else "balanced" if rel_L < 3
                                else "cheeks_more_flushed"),
        }
        pallor_components.append(indicators["relative_skin_pallor"]["score_0_100"])
    if lip:
        lip_L = lip["lab"]["L"]
        ind = _classify_index(lip_L, NORMS["lip_L_paleness"])
        ind["metric"] = "lip_L (Lab)"
        ind["interpretation"] = ("normal_pink" if 35 <= lip_L <= 50
                                  else "pale_lips_anemia_indicator" if lip_L > 55
                                  else "dark_lips")
        indicators["lip_pallor"] = ind
        pallor_components.append(ind["score_0_100"])
    if conj_avg:
        ind = _classify_index(conj_avg["a"], NORMS["conjunctiva_a"])
        ind["metric"] = "conjunctiva_a (Sheth 1997)"
        ind["interpretation"] = ("pale_conjunctiva_iron_deficiency_screen" if conj_avg["a"] < 12
                                  else "healthy_pink" if conj_avg["a"] < 22
                                  else "hyperemic")
        indicators["conjunctival_pallor"] = ind
        pallor_components.append(100 - ind["score_0_100"])  # invert: low=pale

    pallor_index = round(sum(pallor_components) / len(pallor_components), 1) if pallor_components else None

    # 2. Erythema (cheek redness)
    if cheek_a is not None:
        ind = _classify_index(cheek_a, NORMS["cheek_a_redness"])
        ind["metric"] = "cheek_a (Lab)"
        ind["interpretation"] = ("rosacea_or_inflammation" if cheek_a > 14
                                  else "normal_perfusion" if cheek_a > 6
                                  else "low_perfusion")
        indicators["cheek_erythema"] = ind

    # 3. Jaundice (sclera + skin yellow)
    if sclera_avg:
        ind = _classify_index(sclera_avg["b"], NORMS["sclera_b_yellow"])
        ind["metric"] = "sclera_b (Lab)"
        ind["interpretation"] = ("possible_jaundice_consult_physician" if sclera_avg["b"] > 8
                                  else "yellowish_sclera_monitor" if sclera_avg["b"] > 5
                                  else "normal_white_sclera")
        indicators["sclera_jaundice"] = ind
    if cheek_b is not None:
        ind = _classify_index(cheek_b, NORMS["cheek_b_yellowness"])
        ind["metric"] = "cheek_b (Lab)"
        ind["interpretation"] = ("carotenemia_or_jaundice" if cheek_b > 20
                                  else "normal" if cheek_b > 10
                                  else "low_pigment")
        indicators["skin_yellowness"] = ind

    # 4. Cyanosis (lip blue tinge)
    if lip:
        lip_b = lip["lab"]["b"]
        ind = _classify_index(lip_b, NORMS["lip_b_blue_tinge"])
        ind["metric"] = "lip_b (Lab); very low = blue"
        ind["interpretation"] = ("cyanosis_consult_physician" if lip_b < -3
                                  else "mild_blue_tinge" if lip_b < 1
                                  else "normal" if lip_b < 8
                                  else "red_warm")
        indicators["lip_cyanosis"] = ind
        # Lip redness as separate
        ind_a = _classify_index(lip["lab"]["a"], NORMS["lip_a_redness"])
        ind_a["metric"] = "lip_a (Lab)"
        indicators["lip_redness"] = ind_a

    # 5. Sclera redness (fatigue)
    if sclera_avg:
        ind = _classify_index(sclera_avg["a"], NORMS["sclera_redness_a"])
        ind["metric"] = "sclera_a (Lab)"
        ind["interpretation"] = ("red_eyes_fatigue_or_irritation" if sclera_avg["a"] > 5
                                  else "mild_redness" if sclera_avg["a"] > 2
                                  else "clear")
        indicators["sclera_redness"] = ind

    # 6. Hydration (lip dryness via texture + skin texture)
    hydration_components = []
    if lip:
        # Higher texture_std = drier/cracked lips
        lip_dry_score = max(0, min(100, 100 - lip["texture_std"] * 1.8))
        hyd_lip = {
            "value": lip["texture_std"],
            "score_0_100": round(lip_dry_score, 1),
            "severity": ("normal" if lip_dry_score > 60 else
                         "mild" if lip_dry_score > 40 else "marked"),
            "metric": "lip texture stddev",
            "interpretation": ("well_hydrated_lips" if lip_dry_score > 60
                                else "mildly_dry_lips" if lip_dry_score > 40
                                else "very_dry_or_chapped_lips"),
        }
        indicators["lip_hydration"] = hyd_lip
        hydration_components.append(lip_dry_score)
    hydration_index = round(sum(hydration_components) / len(hydration_components), 1) if hydration_components else None

    # 7. Angular cheilitis (mouth corner cracks — B2/B12/iron deficiency)
    angular_flag = False
    angular_details = {}
    if mc_r and mc_l:
        # If mouth corner is much darker AND has high texture_std vs lip mean,
        # it's a crack/inflammation candidate.
        avg_corner_L = (mc_r["lab"]["L"] + mc_l["lab"]["L"]) / 2.0
        avg_corner_tex = (mc_r["texture_std"] + mc_l["texture_std"]) / 2.0
        lip_L = lip["lab"]["L"] if lip else 50.0
        L_drop = lip_L - avg_corner_L
        angular_flag = bool(L_drop > 10 and avg_corner_tex > 25)
        angular_details = {
            "lip_L":          round(lip_L, 2),
            "corner_L":       round(avg_corner_L, 2),
            "L_drop":         round(L_drop, 2),
            "corner_texture": round(avg_corner_tex, 2),
            "flag":           angular_flag,
            "interpretation": ("possible_angular_cheilitis_screen_B2_B12_iron"
                               if angular_flag else "no_angular_cheilitis_signs"),
        }
        indicators["angular_cheilitis"] = angular_details

    # 8. Periorbital edema (under-eye puffiness via texture + L drop)
    periorbital = {}
    if under_r and under_l and cheek_L is not None:
        u_L = (under_r["lab"]["L"] + under_l["lab"]["L"]) / 2.0
        u_tex = (under_r["texture_std"] + under_l["texture_std"]) / 2.0
        L_drop = cheek_L - u_L
        periorbital = {
            "under_eye_L":    round(u_L, 2),
            "cheek_L":        round(cheek_L, 2),
            "L_drop":         round(L_drop, 2),
            "texture_std":    round(u_tex, 2),
            "puffiness_flag": bool(u_tex < 12 and L_drop > 6),  # smooth + darker = swollen
            "interpretation": ("possible_periorbital_edema" if (u_tex < 12 and L_drop > 6)
                                else "no_significant_swelling"),
        }
        indicators["periorbital_edema"] = periorbital

    # 9. Inflammation (acne/red blob count on cheeks/forehead via opencv)
    inflam = _detect_inflammatory_blobs(img, pts_norm, W, H)
    if inflam:
        indicators["inflammation_blobs"] = inflam

    # 10. Pull-throughs from foundation (no extra compute)
    if foundation_dark_circles and foundation_dark_circles.get("ok"):
        indicators["dark_circles"] = {
            "left_grade":    foundation_dark_circles.get("left_grade"),
            "right_grade":   foundation_dark_circles.get("right_grade"),
            "L_drop_left":   foundation_dark_circles.get("lightness_drop_left_L"),
            "L_drop_right":  foundation_dark_circles.get("lightness_drop_right_L"),
            "source": "foundation",
        }
    if foundation_oiliness:
        indicators["oiliness"] = {
            "skin_type":     foundation_oiliness.get("skin_type"),
            "score":         foundation_oiliness.get("oiliness_score"),
            "tzone_specular":foundation_oiliness.get("tzone_specular_ratio"),
            "source": "foundation",
        }
    if foundation_wrinkles and foundation_wrinkles.get("ok"):
        indicators["aging_signs"] = {
            "forehead_lines":  foundation_wrinkles.get("forehead_lines"),
            "crow_feet_left":  foundation_wrinkles.get("crow_feet_left"),
            "crow_feet_right": foundation_wrinkles.get("crow_feet_right"),
            "nasolabial_left": foundation_wrinkles.get("nasolabial_left"),
            "nasolabial_right":foundation_wrinkles.get("nasolabial_right"),
            "source": "foundation",
        }
    if foundation_iris:
        pl = foundation_iris.get("pupil_left", {})
        pr = foundation_iris.get("pupil_right", {})
        if pl and pr:
            asym = abs(pl.get("dilation_ratio", 0) - pr.get("dilation_ratio", 0))
            indicators["pupil_asymmetry"] = {
                "left_dilation_ratio":  pl.get("dilation_ratio"),
                "right_dilation_ratio": pr.get("dilation_ratio"),
                "asymmetry":            round(asym, 3),
                "flag_anisocoria":      bool(asym > 0.10),
                "interpretation": ("anisocoria_consult_physician_if_persistent"
                                   if asym > 0.10 else "physiologic_or_normal"),
                "source": "foundation",
            }

    # ── Composite scores ──────────────────────────────────────────────────
    composites = {}
    composites["pallor_index"] = pallor_index
    composites["hydration_index"] = hydration_index

    # Erythema composite
    eryth_vals = []
    if "cheek_erythema" in indicators:
        eryth_vals.append(indicators["cheek_erythema"]["score_0_100"])
    composites["erythema_index"] = round(sum(eryth_vals) / len(eryth_vals), 1) if eryth_vals else None

    # Jaundice composite
    j_vals = []
    if "sclera_jaundice" in indicators:
        j_vals.append(indicators["sclera_jaundice"]["score_0_100"])
    if "skin_yellowness" in indicators:
        j_vals.append(indicators["skin_yellowness"]["score_0_100"])
    composites["jaundice_index"] = round(sum(j_vals) / len(j_vals), 1) if j_vals else None

    # Cyanosis from lip
    composites["cyanosis_index"] = (100 - indicators["lip_cyanosis"]["score_0_100"]
                                     if "lip_cyanosis" in indicators else None)

    # Fatigue composite (dark circles + sclera redness)
    fat_vals = []
    if "dark_circles" in indicators:
        grade_map = {"none": 0, "mild": 33, "moderate": 66, "severe": 100}
        fat_vals.append(grade_map.get(indicators["dark_circles"]["left_grade"], 0))
        fat_vals.append(grade_map.get(indicators["dark_circles"]["right_grade"], 0))
    if "sclera_redness" in indicators:
        fat_vals.append(indicators["sclera_redness"]["score_0_100"])
    composites["fatigue_index"] = round(sum(fat_vals) / len(fat_vals), 1) if fat_vals else None

    # Inflammation composite
    if inflam:
        composites["inflammation_index"] = inflam["density_score_0_100"]

    # ── Vitality score (overall 0-100, higher = better) ──────────────────
    vitality_components = []
    weights = []
    if composites.get("pallor_index") is not None:
        # invert: 50 = ideal, deviations punish
        vitality_components.append(100 - abs(composites["pallor_index"] - 50) * 2)
        weights.append(0.20)
    if composites.get("hydration_index") is not None:
        vitality_components.append(composites["hydration_index"])
        weights.append(0.15)
    if composites.get("fatigue_index") is not None:
        vitality_components.append(100 - composites["fatigue_index"])
        weights.append(0.20)
    if composites.get("erythema_index") is not None:
        vitality_components.append(100 - abs(composites["erythema_index"] - 50) * 2)
        weights.append(0.15)
    if composites.get("jaundice_index") is not None:
        vitality_components.append(100 - composites["jaundice_index"])
        weights.append(0.15)
    if composites.get("inflammation_index") is not None:
        vitality_components.append(100 - composites["inflammation_index"])
        weights.append(0.15)

    if vitality_components and weights:
        wsum = sum(weights)
        vitality = sum(c * w for c, w in zip(vitality_components, weights)) / wsum
        vitality = round(max(0, min(100, vitality)), 1)
    else:
        vitality = None

    # ── Flags & recommendations ──────────────────────────────────────────
    flags = []
    recommendations_hi = []
    recommendations_en = []
    if indicators.get("conjunctival_pallor", {}).get("interpretation") == "pale_conjunctiva_iron_deficiency_screen":
        flags.append("conjunctival_pallor_anemia_screen")
        recommendations_hi.append("Conjunctival pallor dikh raha hai — iron/B12 levels check karwana acha hoga.")
        recommendations_en.append("Conjunctival pallor noted — consider iron/B12 panel.")
    if indicators.get("sclera_jaundice", {}).get("interpretation", "").startswith("possible_jaundice"):
        flags.append("sclera_jaundice_screen")
        recommendations_hi.append("Aankhon ke white mein halka pila tinge hai — liver function test karwana suggest hai.")
        recommendations_en.append("Yellow tinge in sclera — consider liver function test.")
    if indicators.get("lip_cyanosis", {}).get("interpretation", "").startswith("cyanosis"):
        flags.append("lip_cyanosis_screen")
        recommendations_hi.append("Honthon mein neela tinge — oxygen saturation check karein, doctor se milein.")
        recommendations_en.append("Bluish lip tinge — check SpO2 and consult physician.")
    if angular_flag:
        flags.append("angular_cheilitis_screen")
        recommendations_hi.append("Honthon ke kone fate hue lag rahe hain — B2/B12/iron deficiency screen recommend.")
        recommendations_en.append("Mouth-corner cracks — screen for B2/B12/iron deficiency.")
    if periorbital.get("puffiness_flag"):
        flags.append("periorbital_edema")
        recommendations_hi.append("Aankhon ke neeche sujan hai — neend/salt intake/kidney function dekhein.")
        recommendations_en.append("Under-eye puffiness — review sleep, sodium intake, kidney function.")
    if indicators.get("pupil_asymmetry", {}).get("flag_anisocoria"):
        flags.append("anisocoria")
        recommendations_hi.append("Aankhon ki pupils me size farak — agar persistent hai to neurologist se milein.")
        recommendations_en.append("Pupil size asymmetry — consult neurologist if persistent.")
    if vitality is not None and vitality < 50:
        recommendations_hi.append("Vitality score kam hai — neend, hydration, balanced diet par focus karein.")
        recommendations_en.append("Low vitality score — focus on sleep, hydration, balanced diet.")

    # ── Caveats ──────────────────────────────────────────────────────────
    caveats = [
        "SCREENING ONLY — these indicators are not medical diagnoses.",
        "Lighting and camera color balance can shift Lab values 5-10 units.",
        "Foundation white-balance applied but residual color cast possible.",
        "Conjunctival pallor sampling: small region near lower lid; flash photo recommended.",
        "Skin tone variation across ethnicities affects absolute Lab values; relative metrics are more robust.",
        "All flagged conditions require physician confirmation before any clinical action.",
    ]

    return {
        "engine":  "health",
        "version": 1,
        "ok":      True,
        "inputs": {
            "gender":    gender,
            "ethnicity": ethnicity,
            "age":       age,
        },
        "regions_sampled": {
            "sclera_right":    sclera_r,
            "sclera_left":     sclera_l,
            "sclera_avg":      sclera_avg,
            "lip_outer":       lip,
            "conjunctiva_avg": conj_avg,
            "mouth_corner_R":  mc_r,
            "mouth_corner_L":  mc_l,
            "under_eye_avg_L": (under_r["lab"]["L"] + under_l["lab"]["L"])/2 if (under_r and under_l) else None,
        },
        "indicators":         indicators,
        "composite_scores":   composites,
        "vitality_score":     vitality,
        "vitality_class":     ("excellent" if vitality and vitality >= 80 else
                                 "good"   if vitality and vitality >= 65 else
                                 "fair"   if vitality and vitality >= 50 else
                                 "poor"   if vitality is not None      else "unknown"),
        "flags":              flags,
        "recommendations": {
            "hi": recommendations_hi,
            "en": recommendations_en,
        },
        "caveats":            caveats,
        "disclaimer":         ("This face-derived health screening is informational only "
                                "and is not a substitute for medical examination, diagnosis, "
                                "or treatment. Consult qualified healthcare providers."),
    }


def _detect_inflammatory_blobs(img_bgr: np.ndarray, pts_norm,
                                W: int, H: int) -> Optional[dict]:
    """Detect inflammatory red blobs (acne candidates) inside cheek+forehead region."""
    # Build a face mask using outer face contour
    face_outline_idx = [10, 338, 297, 332, 284, 251, 389, 356, 454, 323,
                         361, 288, 397, 365, 379, 378, 400, 377, 152,
                         148, 176, 149, 150, 136, 172, 58, 132, 93, 234,
                         127, 162, 21, 54, 103, 67, 109]
    pts_px = np.array([[int(pts_norm[i][0] * W), int(pts_norm[i][1] * H)]
                        for i in face_outline_idx], dtype=np.int32)
    face_mask = np.zeros((H, W), dtype=np.uint8)
    cv2.fillPoly(face_mask, [pts_px], 255)
    # Erode to exclude lips/eyes/eyebrows
    eyes_mouth_idx = [33, 263, 61, 291, 13, 14, 159, 386, 105, 334]
    for i in eyes_mouth_idx:
        x, y = int(pts_norm[i][0] * W), int(pts_norm[i][1] * H)
        cv2.circle(face_mask, (x, y), 35, 0, -1)

    hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
    # Red blob heuristic: HSV with H near 0 or 180, S high, V moderate
    red1 = cv2.inRange(hsv, (0,   60, 60),  (12, 255, 230))
    red2 = cv2.inRange(hsv, (165, 60, 60), (180, 255, 230))
    red_mask = cv2.bitwise_or(red1, red2)
    red_mask = cv2.bitwise_and(red_mask, face_mask)
    # Morphological cleanup
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    red_mask = cv2.morphologyEx(red_mask, cv2.MORPH_OPEN, kernel)

    contours, _ = cv2.findContours(red_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    blobs = []
    for c in contours:
        area = cv2.contourArea(c)
        if 8 <= area <= 600:
            x, y, w, h = cv2.boundingRect(c)
            cx, cy = x + w//2, y + h//2
            blobs.append({"area_px": int(area),
                          "x_px": cx, "y_px": cy,
                          "norm_x": round(cx / W, 3),
                          "norm_y": round(cy / H, 3)})

    face_area_px = int(face_mask.sum() / 255)
    density = (sum(b["area_px"] for b in blobs) / face_area_px) if face_area_px > 0 else 0
    density_score = min(100, density * 800)
    grade = ("clear"   if density_score < 5 else
             "mild"    if density_score < 20 else
             "moderate" if density_score < 50 else "severe")
    return {
        "blob_count":           len(blobs),
        "density":              round(density, 5),
        "density_score_0_100":  round(density_score, 1),
        "grade":                grade,
        "method":               "hsv_red_blob_in_face_mask",
        "interpretation":       ("active_inflammation_or_acne" if density_score > 20
                                  else "low_visible_inflammation"),
        "top_blobs":            blobs[:8],
    }
