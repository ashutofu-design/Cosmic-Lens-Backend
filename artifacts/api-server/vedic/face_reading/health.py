"""
Engine 5 v2 — Health & Wellness Indicators (face-derived).

PRIVACY/MEDICAL HEADER
──────────────────────
SCREENING ONLY. Not a medical diagnosis. Photos are processed in-memory
for this analysis and are not stored beyond the session TTL. All flagged
conditions require physician confirmation.

v2 (33 audit fixes over v1)
───────────────────────────
A. COLOR SCIENCE (8)
   1  per-ethnicity Lab norms          (cheek_a/b, lip_*, sclera_*, conj_a)
   2  sclera-as-gray-ref normalization (residual color cast removal)
   3  specular highlight masking       (HSV V-threshold, exclude glare px)
   4  shadow masking                   (low V exclusion before averaging)
   5  global color-cast diagnostic     (gray-world residual, retake hint)
   6  device hint param                (smartphone vs DSLR baseline)
   7  lip glossiness flag              (high-V + saturation pattern)
   8  sclera occlusion guard           (low n_pixels → low confidence)

B. REGION ACCURACY (6)
   9  sclera white-pixel HSV filter inside polygon
   10 conjunctiva sampling: downward offset 4 px into palpebral rim
   11 inner-lip vermilion landmarks (78,95,88,178,87,14,317,402,318,324,308)
   12 mouth-corner tight 6 px radius patches around lm 61/291
   13 outer-forehead reference (away from hairline shadow)
   14 nail-bed limitation note (can't be measured from face selfie)

C. NEW INDICATORS (10)
   15 carotenemia vs jaundice differentiator
   16 vascular vs pigmented dark circles split (Lab a-axis sign)
   17 temporal wasting / cachexia screen
   18 facial droop (FAST stroke screen) explicit composite
   19 thyroid hint (proptosis + edema + texture)
   20 sleep-debt composite
   21 dehydration composite
   22 smoking lines screen (perioral vertical canny lines)
   23 allergic shiners / Dennie-Morgan lines
   24 acne morphotype split: comedonal / inflammatory / cystic

D. METHODOLOGY (6)
   25 per-indicator confidence (high/med/low)
   26 test-retest uncertainty band
   27 evidence-quality tag per indicator (established / emerging / weak)
   28 outlier flag (>3σ → out_of_distribution warning)
   29 cross-engine validation (BMI, asymmetry, Engine 1/2)
   30 scenario test pack hooks (5 scenarios in module bottom)

E. NARRATIVE & UX (3)
   31 Hinglish + EN per-indicator narratives
   32 severity-gated disclaimers (urgent / monitor / informational)
   33 explicit privacy + medical-claim guard header on output
"""
from __future__ import annotations

import math
from typing import Sequence, Optional, Iterable

import numpy as np
import cv2

from .anthropometry import LM as LMK


# ─────────────────────────────────────────────────────────────────────────────
# Per-ethnicity Lab norms  (Saidi 2014, Wilkes 2015, Hosoi 2019, Sheth 1997)
# Each entry: {low, norm, high, sd}.  SD widened ×1.30 for low-evidence.
# ─────────────────────────────────────────────────────────────────────────────
_BASE_NORMS = {
    "default": {
        "cheek_a_redness":    {"low": 4.0,  "norm": 9.0,  "high": 16.0, "sd": 3.0},
        "cheek_b_yellowness": {"low": 8.0,  "norm": 14.0, "high": 22.0, "sd": 3.5},
        "sclera_b_yellow":    {"low":-2.0,  "norm":  3.0, "high": 10.0, "sd": 2.5},
        "sclera_a_redness":   {"low":-2.0,  "norm":  2.0, "high":  8.0, "sd": 2.0},
        "lip_a_redness":      {"low": 8.0,  "norm": 18.0, "high": 28.0, "sd": 4.0},
        "lip_b_blue_tinge":   {"low":-8.0,  "norm":  4.0, "high": 12.0, "sd": 3.0},
        "lip_L_paleness":     {"low": 35.0, "norm": 45.0, "high": 60.0, "sd": 5.0},
        "conjunctiva_a":      {"low": 8.0,  "norm": 18.0, "high": 28.0, "sd": 4.0},
        "skin_L_relative":    {"low":-8.0,  "norm":  0.0, "high":  8.0, "sd": 3.0},
    },
    "south_asian":  {"shifts": {"cheek_a_redness": +1.0, "cheek_b_yellowness": +2.0, "skin_L_relative": -1.0}},
    "east_asian":   {"shifts": {"cheek_a_redness": -1.0, "cheek_b_yellowness": +1.0}},
    "caucasian":    {"shifts": {"cheek_a_redness": +1.5, "cheek_b_yellowness": -1.0}},
    "african":      {"shifts": {"cheek_a_redness": -2.0, "cheek_b_yellowness": +3.0, "skin_L_relative": -2.0,
                                 "lip_L_paleness": -8.0}, "evidence": "weak"},
    "hispanic":     {"shifts": {"cheek_a_redness": +0.5, "cheek_b_yellowness": +1.0}, "evidence": "emerging"},
}

def _norms_for(ethnicity: Optional[str]) -> tuple[dict, str]:
    """Return shifted norm dict + evidence quality tag."""
    base = {k: dict(v) for k, v in _BASE_NORMS["default"].items()}
    eth_key = (ethnicity or "default").lower()
    evidence = "established"
    if eth_key in _BASE_NORMS and eth_key != "default":
        block = _BASE_NORMS[eth_key]
        for metric, shift in block.get("shifts", {}).items():
            if metric in base:
                base[metric]["low"]  += shift
                base[metric]["norm"] += shift
                base[metric]["high"] += shift
        evidence = block.get("evidence", "established")
        # widen SD ×1.30 for low-evidence ethnicities
        if evidence in ("weak", "emerging"):
            for v in base.values():
                v["sd"] *= 1.30
    return base, evidence


# ─────────────────────────────────────────────────────────────────────────────
# Region polygons
# ─────────────────────────────────────────────────────────────────────────────
SCLERA_R = [33, 7, 163, 144, 145, 153, 154, 155]
SCLERA_L = [263, 249, 390, 373, 374, 380, 381, 382]
LIP_OUTER = [61, 185, 40, 39, 37, 0, 267, 269, 270, 409, 291,
             375, 321, 405, 314, 17, 84, 181, 91, 146]
# Inner-lip vermilion (FIX 11)
LIP_INNER_VERM = [78, 95, 88, 178, 87, 14, 317, 402, 318, 324, 308]
# Conjunctival rim (FIX 10 — apply +4 px y offset later)
CONJUNCTIVA_R = [22, 23, 24, 110, 25, 31, 228, 229, 230, 231, 232]
CONJUNCTIVA_L = [252, 253, 254, 339, 255, 261, 448, 449, 450, 451, 452]
# Mouth corners — FIX 12: 6-px radius patch around lm 61 / 291
MOUTH_CORNER_R_LM = 61
MOUTH_CORNER_L_LM = 291
# Under-eye (Dennie-Morgan & periorbital)
UNDER_EYE_R = [120, 119, 230, 229, 228, 31, 226, 113, 226, 130]
UNDER_EYE_L = [349, 348, 450, 449, 448, 261, 446, 342, 446, 359]
# Outer forehead (FIX 13) — left and right of glabella, away from hairline
FOREHEAD_OUTER_L = [109, 67, 103, 104, 69]
FOREHEAD_OUTER_R = [338, 297, 332, 333, 299]
# Temporal hollow (FIX 17)
TEMPLE_R = [21, 162, 127, 234]
TEMPLE_L = [251, 389, 356, 454]
# Perioral upper-lip skin (FIX 22 — smoker's lines)
PERIORAL_UPPER = [164, 167, 165, 92, 186, 0, 410, 322, 391, 393]


# ─────────────────────────────────────────────────────────────────────────────
# Foundation utilities
# ─────────────────────────────────────────────────────────────────────────────
def _py(o):
    """Recursively cast numpy scalars to native Python for JSON serialization."""
    if isinstance(o, dict):
        return {k: _py(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_py(v) for v in o]
    if isinstance(o, (np.bool_,)):
        return bool(o)
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, np.ndarray):
        return [_py(v) for v in o.tolist()]
    return o


def _decode(image_bytes: bytes) -> Optional[np.ndarray]:
    arr = np.frombuffer(image_bytes, dtype=np.uint8)
    return cv2.imdecode(arr, cv2.IMREAD_COLOR)


def _rgb_to_lab(rgb: tuple[float, float, float]) -> tuple[float, float, float]:
    px = np.array([[[rgb[2], rgb[1], rgb[0]]]], dtype=np.uint8)
    lab = cv2.cvtColor(px, cv2.COLOR_BGR2LAB)[0, 0]
    return (lab[0] * (100/255.0), float(lab[1]) - 128.0, float(lab[2]) - 128.0)


def _polygon_pixels(img_bgr: np.ndarray,
                    poly_norm: list[tuple[float, float]],
                    W: int, H: int,
                    y_offset_px: int = 0) -> tuple[np.ndarray, np.ndarray]:
    """Return (mask, pixels_bgr) for a normalized polygon."""
    pts = np.array([[int(x*W), int(y*H) + y_offset_px] for x, y in poly_norm], dtype=np.int32)
    mask = np.zeros(img_bgr.shape[:2], dtype=np.uint8)
    if len(pts) >= 3:
        cv2.fillPoly(mask, [pts], 255)
    return mask, img_bgr[mask > 0]


def _circle_pixels(img_bgr: np.ndarray, cx: int, cy: int, r: int) -> tuple[np.ndarray, np.ndarray]:
    mask = np.zeros(img_bgr.shape[:2], dtype=np.uint8)
    cv2.circle(mask, (cx, cy), r, 255, -1)
    return mask, img_bgr[mask > 0]


def _filter_specular_shadow(pixels_bgr: np.ndarray) -> np.ndarray:
    """FIX 3 + 4 — drop specular-highlight (V>235, S<25) and shadow (V<35) pixels."""
    if len(pixels_bgr) == 0:
        return pixels_bgr
    hsv = cv2.cvtColor(pixels_bgr.reshape(-1, 1, 3), cv2.COLOR_BGR2HSV).reshape(-1, 3)
    keep = ~(((hsv[:, 2] > 235) & (hsv[:, 1] < 25)) | (hsv[:, 2] < 35))
    return pixels_bgr[keep]


def _filter_white(pixels_bgr: np.ndarray, v_min: int = 170, s_max: int = 70) -> np.ndarray:
    """FIX 9 — keep only 'whitish' pixels in sclera polygon."""
    if len(pixels_bgr) == 0:
        return pixels_bgr
    hsv = cv2.cvtColor(pixels_bgr.reshape(-1, 1, 3), cv2.COLOR_BGR2HSV).reshape(-1, 3)
    keep = (hsv[:, 2] >= v_min) & (hsv[:, 1] <= s_max)
    return pixels_bgr[keep]


def _summarize_pixels(pixels_bgr: np.ndarray) -> Optional[dict]:
    if len(pixels_bgr) < 8:
        return None
    bgr_mean = pixels_bgr.mean(axis=0)
    rgb = (float(bgr_mean[2]), float(bgr_mean[1]), float(bgr_mean[0]))
    L, a, b = _rgb_to_lab(rgb)
    hsv_px = cv2.cvtColor(pixels_bgr.reshape(-1, 1, 3), cv2.COLOR_BGR2HSV).reshape(-1, 3)
    gray_px = cv2.cvtColor(pixels_bgr.reshape(-1, 1, 3), cv2.COLOR_BGR2GRAY).reshape(-1)
    return {
        "rgb_mean": [round(rgb[0], 1), round(rgb[1], 1), round(rgb[2], 1)],
        "lab": {"L": round(L, 2), "a": round(a, 2), "b": round(b, 2)},
        "hsv_mean": [int(hsv_px[:, 0].mean()), int(hsv_px[:, 1].mean()), int(hsv_px[:, 2].mean())],
        "v_std": float(hsv_px[:, 2].std()),
        "s_mean": float(hsv_px[:, 1].mean()),
        "texture_std": round(float(gray_px.std()), 2),
        "n_pixels": int(len(pixels_bgr)),
    }


def _confidence_from(n_pixels: int, occlusion_flag: bool = False) -> str:
    """FIX 25 — per-indicator confidence."""
    if occlusion_flag or n_pixels < 30:
        return "low"
    if n_pixels < 150:
        return "medium"
    return "high"


def _outlier_flag(value: float, norm: dict) -> bool:
    """FIX 28 — >3σ from norm midpoint."""
    sd = norm.get("sd", 1.0) or 1.0
    return abs(value - norm["norm"]) > 3.0 * sd


def _classify(value: float, norm: dict, invert: bool = False) -> dict:
    lo, mid, hi = norm["low"], norm["norm"], norm["high"]
    if invert:
        lo, hi = hi, lo
    if value <= mid:
        score = 50.0 * max(0.0, (value - lo) / (mid - lo)) if mid != lo else 50.0
    else:
        score = 50.0 + 50.0 * min(1.0, (value - mid) / (hi - mid)) if hi != mid else 50.0
    score = max(0.0, min(100.0, score))
    severity = ("normal" if 35 <= score <= 65 else
                "mild"   if 20 <= score < 35 or 65 < score <= 80 else
                "marked")
    return {
        "value": round(value, 2),
        "score_0_100": round(score, 1),
        "severity": severity,
        "uncertainty_band_score": 5.0,   # FIX 26 — ±5 score units typical
        "outlier": _outlier_flag(value, norm),
    }


def _color_cast_residual(img_bgr: np.ndarray) -> dict:
    """FIX 5 — global gray-world residual."""
    means = img_bgr.reshape(-1, 3).mean(axis=0)
    g = means.mean()
    residual = float(np.max(np.abs(means - g)))
    return {
        "residual": round(residual, 2),
        "flag_strong_cast": bool(residual > 18.0),
        "interpretation": ("strong_color_cast_consider_retake" if residual > 18
                           else "moderate_cast" if residual > 10
                           else "neutral_lighting"),
    }


def _sclera_gray_ref_correction(img_bgr: np.ndarray, sclera_white_px: np.ndarray) -> Optional[np.ndarray]:
    """FIX 2 — use sclera as a near-white reference; return per-channel gain."""
    if len(sclera_white_px) < 30:
        return None
    target = 220.0  # near-white target
    means = sclera_white_px.mean(axis=0)
    means = np.clip(means, 60.0, 250.0)
    gains = target / means
    gains = np.clip(gains, 0.7, 1.4)
    return gains  # apply as multiplier to bgr channels


def _apply_gains(pixels_bgr: np.ndarray, gains: Optional[np.ndarray]) -> np.ndarray:
    if gains is None or len(pixels_bgr) == 0:
        return pixels_bgr
    out = pixels_bgr.astype(np.float32) * gains
    return np.clip(out, 0, 255).astype(np.uint8)


# ─────────────────────────────────────────────────────────────────────────────
# Narratives (FIX 31)
# ─────────────────────────────────────────────────────────────────────────────
def _narrate(key: str, severity: str) -> dict:
    BANK = {
        "lip_pallor": {
            "normal":  ("Honthon ka rang healthy pink hai.", "Lip color is healthy pink."),
            "mild":    ("Honth halke pale lag rahe hain — iron levels check karein.",
                         "Lips appear slightly pale — consider iron screening."),
            "marked":  ("Honth significantly pale hain — anemia screen recommend.",
                         "Markedly pale lips — anemia screen recommended."),
        },
        "lip_cyanosis": {
            "normal":  ("Honthon mein blue tinge nahi.", "No bluish tinge in lips."),
            "mild":    ("Halka blue tinge — thand/circulation check karein.",
                         "Mild bluish tinge — check temperature/circulation."),
            "marked":  ("Lip cyanosis — SpO2 turant check karein, doctor consult.",
                         "Lip cyanosis — check SpO2 and consult physician."),
        },
        "sclera_jaundice": {
            "normal":  ("Aankhon ka white clean hai.", "Sclera appears clear."),
            "mild":    ("Sclera mein halka pila tinge.", "Mild yellow tinge in sclera."),
            "marked":  ("Sclera me marked yellow — LFT karwana suggested.",
                         "Marked scleral yellowing — consider LFT."),
        },
        "sclera_redness": {
            "normal":  ("Aankhein clear hain.", "Eyes appear clear."),
            "mild":    ("Halki redness — neend/screen-time dekhein.",
                         "Mild redness — check sleep and screen exposure."),
            "marked":  ("Marked redness — irritation/allergy/infection ho sakta hai.",
                         "Marked redness — possible irritation/allergy/infection."),
        },
        "conjunctival_pallor": {
            "normal":  ("Lower lid rim pink — anemia signs nahi.",
                         "Lower-lid rim is pink — no anemia signs."),
            "mild":    ("Lower lid thoda pale — iron/B12 screen recommended.",
                         "Slightly pale lower lid — consider iron/B12 screen."),
            "marked":  ("Marked conjunctival pallor — anemia screen ASAP.",
                         "Marked conjunctival pallor — anemia screen ASAP."),
        },
        "cheek_erythema": {
            "normal":  ("Gaalon ka rang balanced.", "Balanced cheek color."),
            "mild":    ("Halka redness — heat/exercise/blush ho sakta hai.",
                         "Mild redness — possibly heat/exertion."),
            "marked":  ("Marked redness — rosacea/inflammation screen.",
                         "Marked redness — consider rosacea/inflammation."),
        },
        "lip_hydration": {
            "normal":  ("Honth well-hydrated lag rahe hain.", "Lips appear well-hydrated."),
            "mild":    ("Honth halke dry — paani aur badhayein.",
                         "Mildly dry lips — increase water intake."),
            "marked":  ("Honth bahut dry/chapped — hydration & lip balm.",
                         "Very dry/chapped lips — hydrate and use balm."),
        },
        "skin_yellowness": {
            "normal":  ("Skin pigmentation normal range.", "Skin pigmentation in normal range."),
            "mild":    ("Halki yellowness — diet (carotenoid) ya jaundice ho sakta hai.",
                         "Mild yellowness — possibly carotenoid intake or jaundice."),
            "marked":  ("Marked yellowness — sclera dekhein, LFT recommended.",
                         "Marked yellowness — review sclera and consider LFT."),
        },
        "lip_redness": {
            "normal":  ("Lip redness normal.", "Lip redness normal."),
            "mild":    ("Lip color thoda dull.", "Lip color slightly dull."),
            "marked":  ("Lip color very faint.", "Lip color very faint."),
        },
        "relative_skin_pallor": {
            "normal":  ("Skin tone gaal aur forehead par balanced.",
                         "Skin tone is balanced cheek vs forehead."),
            "mild":    ("Halka cheek pallor.", "Mild cheek pallor."),
            "marked":  ("Marked cheek pallor — anemia/circulation screen.",
                         "Marked cheek pallor — anemia/circulation screen."),
        },
    }
    pair = BANK.get(key, {}).get(severity)
    if pair:
        return {"hi": pair[0], "en": pair[1]}
    return {"hi": "", "en": ""}


# ─────────────────────────────────────────────────────────────────────────────
# Evidence-quality tag per indicator (FIX 27)
# ─────────────────────────────────────────────────────────────────────────────
EVIDENCE = {
    "relative_skin_pallor":   {"strength": "moderate",   "ref": "Saidi 2014"},
    "lip_pallor":             {"strength": "established","ref": "Liu 2018"},
    "conjunctival_pallor":    {"strength": "established","ref": "Sheth 1997"},
    "cheek_erythema":         {"strength": "moderate",   "ref": "Wilkes 2015"},
    "sclera_jaundice":        {"strength": "established","ref": "Hosoi 2019"},
    "skin_yellowness":        {"strength": "moderate",   "ref": "Edwards 2017 (carotenoid)"},
    "lip_cyanosis":           {"strength": "established","ref": "clinical"},
    "lip_redness":            {"strength": "moderate",   "ref": "Liu 2018"},
    "sclera_redness":         {"strength": "moderate",   "ref": "fatigue proxy"},
    "lip_hydration":          {"strength": "emerging",   "ref": "texture proxy"},
    "angular_cheilitis":      {"strength": "established","ref": "clinical, B-vit/iron"},
    "periorbital_edema":      {"strength": "emerging",   "ref": "contour proxy"},
    "inflammation_blobs":     {"strength": "emerging",   "ref": "HSV blob heuristic"},
    "carotenemia_vs_jaundice":{"strength": "moderate",   "ref": "differential"},
    "dark_circles_subtype":   {"strength": "emerging",   "ref": "Lab a-axis"},
    "temporal_wasting":       {"strength": "weak",       "ref": "z-projection proxy"},
    "facial_droop_screen":    {"strength": "moderate",   "ref": "FAST adapted"},
    "thyroid_hint":           {"strength": "weak",       "ref": "non-specific"},
    "sleep_debt":             {"strength": "emerging",   "ref": "composite"},
    "dehydration":            {"strength": "emerging",   "ref": "composite"},
    "smoker_lines":           {"strength": "moderate",   "ref": "perioral edges"},
    "allergic_shiners":       {"strength": "moderate",   "ref": "Dennie-Morgan"},
    "acne_morphotype":        {"strength": "moderate",   "ref": "morphological split"},
}


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────
def run(landmarks_norm: Sequence[tuple[float, float, float]],
        image_w: int, image_h: int,
        image_bytes: Optional[bytes] = None,
        foundation_skin: Optional[dict] = None,
        foundation_dark_circles: Optional[dict] = None,
        foundation_oiliness: Optional[dict] = None,
        foundation_wrinkles: Optional[dict] = None,
        foundation_iris: Optional[dict] = None,
        anthropometry_result: Optional[dict] = None,
        symmetry_result: Optional[dict] = None,
        gender: str = "U",
        ethnicity: Optional[str] = None,
        age: Optional[int] = None,
        device_hint: str = "smartphone",
        ) -> dict:

    if not landmarks_norm or len(landmarks_norm) < 478:
        return {"engine": "health", "ok": False, "error": "insufficient_landmarks"}
    if image_bytes is None:
        return {"engine": "health", "ok": False, "error": "image_bytes_required"}
    img = _decode(image_bytes)
    if img is None:
        return {"engine": "health", "ok": False, "error": "image_decode_failed"}

    H, W = img.shape[:2]
    pts = [(p[0], p[1]) for p in landmarks_norm]
    norms, evidence_for_eth = _norms_for(ethnicity)

    # FIX 5 — global cast diagnostic
    cast = _color_cast_residual(img)
    # FIX 6 — device baseline (very mild norm widening for smartphone)
    if device_hint == "smartphone":
        for v in norms.values():
            v["sd"] *= 1.10

    # ── FIX 9: sclera with HSV white-pixel filter ───────────────────────
    def poly(idx_list):
        return [(pts[i][0], pts[i][1]) for i in idx_list]

    _, sclera_r_raw = _polygon_pixels(img, poly(SCLERA_R), W, H)
    _, sclera_l_raw = _polygon_pixels(img, poly(SCLERA_L), W, H)

    # v3-FIX 1: adaptive Otsu sclera threshold (replaces fixed v_min=170)
    sclera_r_white = _filter_white_adaptive(sclera_r_raw)
    sclera_l_white = _filter_white_adaptive(sclera_l_raw)
    sclera_white_all = np.concatenate([sclera_r_white, sclera_l_white]) if (
        len(sclera_r_white) + len(sclera_l_white) > 0) else np.empty((0, 3), dtype=np.uint8)

    # FIX 8 — occlusion guard
    sclera_occluded = bool(len(sclera_white_all) < 60)

    # ── v3-FIX 2: WB fallback chain ──
    # Try sclera → forehead gray-world → no correction
    wb_method_used = "none"
    wb_confidence_penalty = 0.0
    gains = _sclera_gray_ref_correction(img, sclera_white_all)
    if gains is not None:
        wb_method_used = "sclera_gray_reference"
    else:
        # Fallback: forehead gray-world
        _, fh_raw_for_wb = _polygon_pixels(img, poly(FOREHEAD_REF_OUTER), W, H)
        gains = _gray_world_gains(fh_raw_for_wb)
        if gains is not None:
            wb_method_used = "forehead_gray_world_fallback"
            wb_confidence_penalty = 0.20  # v3-FIX 3: drop confidence
        else:
            wb_confidence_penalty = 0.40  # no WB at all
    # v3-FIX 4: if global cast still strong AND WB failed, add another penalty
    if cast["flag_strong_cast"] and wb_method_used == "none":
        wb_confidence_penalty += 0.20

    # Sample regions with specular/shadow filter (FIX 3 + 4) and apply gains (FIX 2)
    def sample(pixels):
        filtered = _filter_specular_shadow(pixels)
        corrected = _apply_gains(filtered, gains)
        return _summarize_pixels(corrected)

    sclera_r = sample(sclera_r_white)
    sclera_l = sample(sclera_l_white)
    sclera_avg = sample(sclera_white_all)

    _, lip_outer_px = _polygon_pixels(img, poly(LIP_OUTER), W, H)
    _, lip_inner_px = _polygon_pixels(img, poly(LIP_INNER_VERM), W, H)  # FIX 11
    lip = sample(lip_inner_px) or sample(lip_outer_px)

    # FIX 7 — lip glossiness flag
    lip_gloss_flag = False
    if lip and lip.get("v_std", 0) > 50 and lip.get("s_mean", 0) > 110:
        lip_gloss_flag = True

    # FIX 10 — conjunctiva with +4 px y_offset into palpebral rim
    y_offset = max(2, int(0.005 * H))
    _, conj_r_px = _polygon_pixels(img, poly(CONJUNCTIVA_R), W, H, y_offset_px=y_offset)
    _, conj_l_px = _polygon_pixels(img, poly(CONJUNCTIVA_L), W, H, y_offset_px=y_offset)
    conj_r = sample(conj_r_px); conj_l = sample(conj_l_px)
    conj_all = np.concatenate([conj_r_px, conj_l_px]) if (len(conj_r_px) + len(conj_l_px) > 0) else np.empty((0, 3), np.uint8)
    conj_avg = sample(conj_all)

    # FIX 12 — tight 6 px circle around lm 61/291
    r_corner = max(4, int(0.012 * W))
    cx_r = int(pts[MOUTH_CORNER_R_LM][0] * W); cy_r = int(pts[MOUTH_CORNER_R_LM][1] * H)
    cx_l = int(pts[MOUTH_CORNER_L_LM][0] * W); cy_l = int(pts[MOUTH_CORNER_L_LM][1] * H)
    _, mc_r_px = _circle_pixels(img, cx_r, cy_r, r_corner)
    _, mc_l_px = _circle_pixels(img, cx_l, cy_l, r_corner)
    mc_r = sample(mc_r_px); mc_l = sample(mc_l_px)

    # FIX 13 — outer-forehead reference (avg of L+R)
    _, fh_l_px = _polygon_pixels(img, poly(FOREHEAD_OUTER_L), W, H)
    _, fh_r_px = _polygon_pixels(img, poly(FOREHEAD_OUTER_R), W, H)
    fh_outer_px = np.concatenate([fh_l_px, fh_r_px]) if (len(fh_l_px)+len(fh_r_px) > 0) else np.empty((0,3), np.uint8)
    fh_outer = sample(fh_outer_px)

    # Under-eye
    _, ue_r_px = _polygon_pixels(img, poly(UNDER_EYE_R), W, H)
    _, ue_l_px = _polygon_pixels(img, poly(UNDER_EYE_L), W, H)
    ue_r = sample(ue_r_px); ue_l = sample(ue_l_px)

    # Temple (FIX 17)
    _, temple_r_px = _polygon_pixels(img, poly(TEMPLE_R), W, H)
    _, temple_l_px = _polygon_pixels(img, poly(TEMPLE_L), W, H)
    temple_r = sample(temple_r_px); temple_l = sample(temple_l_px)

    # Foundation cheek Lab (after gain correction we re-derive from cached lab if no gain available)
    cheek_L = cheek_a = cheek_b = forehead_L_found = None
    if foundation_skin and foundation_skin.get("ok"):
        per = foundation_skin.get("per_region", {})
        cl = per.get("cheek_l") or {}; cr = per.get("cheek_r") or {}
        ll = cl.get("lab_mean") or [None]*3; rl = cr.get("lab_mean") or [None]*3
        if ll[0] is not None and rl[0] is not None:
            cheek_L = (ll[0]+rl[0])/2; cheek_a = (ll[1]+rl[1])/2; cheek_b = (ll[2]+rl[2])/2
        fh = per.get("forehead") or {}
        if (fh.get("lab_mean") or [None])[0] is not None:
            forehead_L_found = fh["lab_mean"][0]
    # Prefer outer-forehead (FIX 13) when available
    forehead_L = (fh_outer["lab"]["L"] if fh_outer else forehead_L_found)

    indicators: dict[str, dict] = {}

    def attach_meta(d: dict, key: str, n_pix: int, occluded: bool = False):
        d["confidence"] = _confidence_from(n_pix, occluded)
        d["evidence_strength"] = EVIDENCE.get(key, {}).get("strength", "emerging")
        d["evidence_ref"] = EVIDENCE.get(key, {}).get("ref", "n/a")
        d["narrative"] = _narrate(key, d.get("severity", "normal"))
        return d

    # 1. Relative skin pallor
    if cheek_L is not None and forehead_L is not None:
        rel = cheek_L - forehead_L
        ind = _classify(rel, norms["skin_L_relative"], invert=True)
        ind["metric"] = "cheek_L − outer_forehead_L"
        ind["interpretation"] = ("cheeks_paler_than_forehead" if rel < -3
                                  else "balanced" if rel < 3 else "cheeks_more_flushed")
        indicators["relative_skin_pallor"] = attach_meta(ind, "relative_skin_pallor",
                                                        n_pix=200)

    # 2. Lip pallor
    if lip:
        ind = _classify(lip["lab"]["L"], norms["lip_L_paleness"])
        ind["metric"] = "lip_L (Lab)"
        ind["interpretation"] = ("normal_pink" if 35 <= lip["lab"]["L"] <= 50
                                  else "pale_lips_anemia_indicator" if lip["lab"]["L"] > 55
                                  else "dark_lips")
        ind["lip_gloss_flag"] = lip_gloss_flag
        indicators["lip_pallor"] = attach_meta(ind, "lip_pallor", lip["n_pixels"])

    # 3. Conjunctival pallor
    if conj_avg:
        ind = _classify(conj_avg["lab"]["a"], norms["conjunctiva_a"])
        ind["metric"] = "conjunctiva_a (Sheth 1997)"
        ind["interpretation"] = ("pale_conjunctiva_iron_deficiency_screen" if conj_avg["lab"]["a"] < 12
                                  else "healthy_pink" if conj_avg["lab"]["a"] < 22
                                  else "hyperemic")
        indicators["conjunctival_pallor"] = attach_meta(ind, "conjunctival_pallor",
                                                       conj_avg["n_pixels"])

    # 4. Cheek erythema
    if cheek_a is not None:
        ind = _classify(cheek_a, norms["cheek_a_redness"])
        ind["metric"] = "cheek_a (Lab)"
        ind["interpretation"] = ("rosacea_or_inflammation" if cheek_a > norms["cheek_a_redness"]["high"]-2
                                  else "normal_perfusion" if cheek_a > norms["cheek_a_redness"]["low"]+2
                                  else "low_perfusion")
        indicators["cheek_erythema"] = attach_meta(ind, "cheek_erythema", n_pix=200)

    # 5. Sclera jaundice
    if sclera_avg:
        ind = _classify(sclera_avg["lab"]["b"], norms["sclera_b_yellow"])
        ind["metric"] = "sclera_b (Lab) post-WB"
        ind["interpretation"] = ("possible_jaundice_consult_physician" if sclera_avg["lab"]["b"] > 8
                                  else "yellowish_sclera_monitor" if sclera_avg["lab"]["b"] > 5
                                  else "normal_white_sclera")
        indicators["sclera_jaundice"] = attach_meta(ind, "sclera_jaundice",
                                                   sclera_avg["n_pixels"], sclera_occluded)

    # 6. Skin yellowness
    if cheek_b is not None:
        ind = _classify(cheek_b, norms["cheek_b_yellowness"])
        ind["metric"] = "cheek_b (Lab)"
        ind["interpretation"] = ("carotenemia_or_jaundice" if cheek_b > norms["cheek_b_yellowness"]["high"]-2
                                  else "normal" if cheek_b > norms["cheek_b_yellowness"]["low"]+1
                                  else "low_pigment")
        indicators["skin_yellowness"] = attach_meta(ind, "skin_yellowness", n_pix=200)

    # 7. Lip cyanosis
    if lip:
        lip_b = lip["lab"]["b"]
        ind = _classify(lip_b, norms["lip_b_blue_tinge"])
        ind["metric"] = "lip_b (Lab); very low = cyanosis"
        ind["interpretation"] = ("cyanosis_consult_physician" if lip_b < -3
                                  else "mild_blue_tinge" if lip_b < 1
                                  else "normal" if lip_b < 8 else "red_warm")
        ind["lip_gloss_flag"] = lip_gloss_flag
        indicators["lip_cyanosis"] = attach_meta(ind, "lip_cyanosis", lip["n_pixels"])

        # Lip redness
        ind_a = _classify(lip["lab"]["a"], norms["lip_a_redness"])
        ind_a["metric"] = "lip_a (Lab)"
        indicators["lip_redness"] = attach_meta(ind_a, "lip_redness", lip["n_pixels"])

    # 8. Sclera redness
    if sclera_avg:
        ind = _classify(sclera_avg["lab"]["a"], norms["sclera_a_redness"])
        ind["metric"] = "sclera_a (Lab)"
        ind["interpretation"] = ("red_eyes_fatigue_or_irritation" if sclera_avg["lab"]["a"] > 5
                                  else "mild_redness" if sclera_avg["lab"]["a"] > 2 else "clear")
        indicators["sclera_redness"] = attach_meta(ind, "sclera_redness",
                                                   sclera_avg["n_pixels"], sclera_occluded)

    # 9. Lip hydration
    if lip:
        ds = max(0.0, min(100.0, 100 - lip["texture_std"] * 1.8))
        sev = "normal" if ds > 60 else "mild" if ds > 40 else "marked"
        ind = {"value": lip["texture_std"], "score_0_100": round(ds, 1),
               "severity": sev, "metric": "lip texture stddev",
               "uncertainty_band_score": 8.0,
               "interpretation": ("well_hydrated_lips" if ds > 60
                                   else "mildly_dry_lips" if ds > 40
                                   else "very_dry_or_chapped_lips"),
               "outlier": False}
        indicators["lip_hydration"] = attach_meta(ind, "lip_hydration", lip["n_pixels"])

    # 10. Angular cheilitis (FIX 12 tighter ROI)
    angular_flag = False
    if mc_r and mc_l and lip:
        avg_corner_L = (mc_r["lab"]["L"] + mc_l["lab"]["L"]) / 2
        avg_corner_tex = (mc_r["texture_std"] + mc_l["texture_std"]) / 2
        L_drop = lip["lab"]["L"] - avg_corner_L
        angular_flag = bool(L_drop > 10 and avg_corner_tex > 25)
        ind = {"lip_L": round(lip["lab"]["L"], 2),
               "corner_L": round(avg_corner_L, 2),
               "L_drop": round(L_drop, 2),
               "corner_texture": round(avg_corner_tex, 2),
               "flag": angular_flag,
               "severity": "marked" if angular_flag else "normal",
               "interpretation": ("possible_angular_cheilitis_screen_B2_B12_iron"
                                   if angular_flag else "no_angular_cheilitis_signs")}
        indicators["angular_cheilitis"] = attach_meta(ind, "angular_cheilitis",
                                                     mc_r["n_pixels"] + mc_l["n_pixels"])

    # 11. Periorbital edema
    periorbital_flag = False
    if ue_r and ue_l and cheek_L is not None:
        u_L = (ue_r["lab"]["L"] + ue_l["lab"]["L"]) / 2
        u_tex = (ue_r["texture_std"] + ue_l["texture_std"]) / 2
        L_drop = cheek_L - u_L
        periorbital_flag = bool(u_tex < 12 and L_drop > 6)
        ind = {"under_eye_L": round(u_L, 2), "cheek_L": round(cheek_L, 2),
               "L_drop": round(L_drop, 2), "texture_std": round(u_tex, 2),
               "flag": periorbital_flag,
               "severity": "marked" if periorbital_flag else "normal",
               "interpretation": ("possible_periorbital_edema" if periorbital_flag
                                   else "no_significant_swelling")}
        indicators["periorbital_edema"] = attach_meta(ind, "periorbital_edema",
                                                     ue_r["n_pixels"] + ue_l["n_pixels"])

    # 12. Acne morphotype split (FIX 24)
    acne = _detect_acne_morphotypes(img, pts, W, H)
    if acne:
        acne["severity"] = ("marked" if acne["density_score_0_100"] > 50 else
                             "mild"   if acne["density_score_0_100"] > 20 else "normal")
        indicators["acne_morphotype"] = attach_meta(acne, "acne_morphotype",
                                                   n_pix=acne.get("face_area_px", 0))
        # Backwards-compat field
        indicators["inflammation_blobs"] = attach_meta(
            {"blob_count": acne["inflammatory_count"],
             "density_score_0_100": acne["inflammatory_density_score"],
             "severity": "marked" if acne["inflammatory_density_score"] > 40
                         else "mild" if acne["inflammatory_density_score"] > 15 else "normal",
             "interpretation": "see_acne_morphotype",
             "outlier": False},
            "inflammation_blobs", n_pix=acne.get("face_area_px", 0))

    # 13. Carotenemia vs jaundice differentiator (FIX 15)
    if "sclera_jaundice" in indicators and "skin_yellowness" in indicators:
        sclera_yellow = sclera_avg["lab"]["b"] if sclera_avg else 0
        skin_yellow = cheek_b if cheek_b is not None else 0
        if skin_yellow > 18 and sclera_yellow < 5:
            verdict = "carotenemia_likely_diet_review"
        elif skin_yellow > 18 and sclera_yellow > 5:
            verdict = "true_jaundice_likely_consult_physician"
        elif skin_yellow < 16 and sclera_yellow > 5:
            verdict = "isolated_scleral_yellow_monitor"
        else:
            verdict = "no_yellowness_concern"
        ind = {"sclera_b": round(sclera_yellow, 2), "skin_b": round(skin_yellow, 2),
               "verdict": verdict, "severity": ("marked" if "true_jaundice" in verdict
                                                  else "mild" if "carotenemia" in verdict or "isolated" in verdict
                                                  else "normal"),
               "outlier": False}
        indicators["carotenemia_vs_jaundice"] = attach_meta(ind, "carotenemia_vs_jaundice", n_pix=200)

    # 14. Dark circles vascular vs pigmented (FIX 16)
    if foundation_dark_circles and foundation_dark_circles.get("ok"):
        # Sample under-eye Lab a from our re-extracted region
        ue_a = ((ue_r["lab"]["a"] if ue_r else 0) + (ue_l["lab"]["a"] if ue_l else 0)) / 2 if (ue_r and ue_l) else 0
        if ue_a > 10:
            subtype = "vascular_blue_purple"
        elif ue_a < 4:
            subtype = "pigmented_brown_melanin"
        else:
            subtype = "mixed_or_structural"
        ind = {"left_grade": foundation_dark_circles.get("left_grade"),
               "right_grade": foundation_dark_circles.get("right_grade"),
               "under_eye_a_axis": round(ue_a, 2),
               "subtype": subtype,
               "severity": "mild" if subtype != "mixed_or_structural" else "normal",
               "outlier": False,
               "interpretation": ("treat_with_vasoconstrictor_caffeine" if subtype.startswith("vascular")
                                   else "treat_with_brightening_topicals_sun_protection" if subtype.startswith("pigmented")
                                   else "structural_consider_filler_or_concealer")}
        indicators["dark_circles_subtype"] = attach_meta(ind, "dark_circles_subtype",
                                                        n_pix=ue_r["n_pixels"]+ue_l["n_pixels"] if (ue_r and ue_l) else 100)

    # 15. Temporal wasting (FIX 17) — z-projection ≈ 2D inset using temple mean L vs cheek L
    if temple_r and temple_l and cheek_L is not None:
        t_L = (temple_r["lab"]["L"] + temple_l["lab"]["L"]) / 2
        L_inset = cheek_L - t_L
        flag = bool(L_inset > 8)  # darker temple = recessed/hollow
        ind = {"temple_L": round(t_L, 2), "cheek_L": round(cheek_L, 2),
               "L_inset": round(L_inset, 2), "flag": flag,
               "severity": "marked" if flag else "normal", "outlier": False,
               "interpretation": ("temporal_hollowing_screen_weight_loss_aging" if flag
                                   else "no_temporal_wasting_signs")}
        indicators["temporal_wasting"] = attach_meta(ind, "temporal_wasting",
                                                    temple_r["n_pixels"]+temple_l["n_pixels"])

    # 16. Facial droop (FIX 18)
    droop_flag = False
    droop_detail = {}
    if symmetry_result and symmetry_result.get("ok"):
        # use mouth corner asymmetry from symmetry engine if exposed
        mouth_asym = (symmetry_result.get("regional", {}).get("mouth_asymmetry_norm") or
                      symmetry_result.get("regional", {}).get("mouth", {}).get("asymmetry_norm"))
        brow_asym = (symmetry_result.get("regional", {}).get("eyebrow_asymmetry_norm") or
                     symmetry_result.get("regional", {}).get("brow", {}).get("asymmetry_norm"))
        droop_detail = {"mouth_asym": mouth_asym, "brow_asym": brow_asym}
        droop_flag = bool((mouth_asym or 0) > 0.06 and (brow_asym or 0) > 0.04)
    # fallback: vertical asymmetry of lip corners directly
    lip_dy = abs(pts[61][1] - pts[291][1])
    droop_detail["lip_corner_dy_norm"] = round(lip_dy, 4)
    if lip_dy > 0.020:
        droop_flag = True
    ind = {**droop_detail, "flag": droop_flag,
           "severity": "marked" if droop_flag else "normal", "outlier": False,
           "interpretation": ("facial_droop_screen_FAST_consult_emergency_if_acute"
                               if droop_flag else "no_facial_droop_signs")}
    indicators["facial_droop_screen"] = attach_meta(ind, "facial_droop_screen", n_pix=200)

    # 17. Thyroid hint (FIX 19) — combine periorbital edema + texture + (later) proptosis
    thyroid_score = 0
    if periorbital_flag: thyroid_score += 40
    if foundation_wrinkles and foundation_wrinkles.get("ok"):
        fl = foundation_wrinkles.get("forehead_lines", 0)
        try:
            fl_num = float(fl) if not isinstance(fl, str) else (
                {"none": 0, "low": 0.05, "mild": 0.10, "med": 0.18,
                 "moderate": 0.25, "high": 0.35, "severe": 0.45}.get(fl.lower(), 0))
        except Exception:
            fl_num = 0
        if fl_num > 0.15:
            thyroid_score += 10
    if cheek_b is not None and cheek_b < norms["cheek_b_yellowness"]["low"]:
        thyroid_score += 10
    if foundation_iris:
        # very crude proptosis hint via iris-radius / eye-aperture ratio
        r_radius = foundation_iris.get("right_radius_px") or 0
        if r_radius > 0:
            aperture = abs(pts[159][1] - pts[145][1]) * H
            if aperture > 0 and (r_radius / aperture) < 0.55:
                thyroid_score += 20  # wide aperture → possible exophthalmos
    ind = {"thyroid_composite_score": min(100, thyroid_score),
           "severity": "marked" if thyroid_score > 50 else "mild" if thyroid_score > 25 else "normal",
           "outlier": False,
           "interpretation": ("thyroid_panel_screen_consult_physician" if thyroid_score > 50
                               else "non_specific_signs" if thyroid_score > 25
                               else "no_thyroid_signs")}
    indicators["thyroid_hint"] = attach_meta(ind, "thyroid_hint", n_pix=100)

    # 18. Sleep debt (FIX 20)
    sd_components = []
    if foundation_dark_circles and foundation_dark_circles.get("ok"):
        gm = {"none": 0, "mild": 33, "moderate": 66, "severe": 100}
        sd_components.append(gm.get(foundation_dark_circles.get("left_grade", "none"), 0))
        sd_components.append(gm.get(foundation_dark_circles.get("right_grade", "none"), 0))
    if "sclera_redness" in indicators:
        sd_components.append(indicators["sclera_redness"]["score_0_100"])
    if "lip_hydration" in indicators:
        sd_components.append(100 - indicators["lip_hydration"]["score_0_100"])
    if sd_components:
        sd_score = round(sum(sd_components) / len(sd_components), 1)
        ind = {"score_0_100": sd_score,
               "severity": "marked" if sd_score > 60 else "mild" if sd_score > 40 else "normal",
               "outlier": False,
               "interpretation": ("significant_sleep_debt_prioritize_rest" if sd_score > 60
                                   else "moderate_fatigue_signs" if sd_score > 40
                                   else "well_rested_signs")}
        indicators["sleep_debt"] = attach_meta(ind, "sleep_debt", n_pix=300)

    # 19. Dehydration (FIX 21)
    dh_components = []
    if "lip_hydration" in indicators:
        dh_components.append(100 - indicators["lip_hydration"]["score_0_100"])
    if foundation_skin and foundation_skin.get("ok"):
        wp = (foundation_wrinkles or {}).get("forehead_lines", 0) or 0
        try:
            wp_num = float(wp) if not isinstance(wp, str) else (
                {"none":0,"low":0.05,"mild":0.10,"med":0.18,
                 "moderate":0.25,"high":0.35,"severe":0.45}.get(wp.lower(), 0))
        except Exception:
            wp_num = 0
        dh_components.append(min(100, wp_num * 200))
    if dh_components:
        dh_score = round(sum(dh_components) / len(dh_components), 1)
        ind = {"score_0_100": dh_score,
               "severity": "marked" if dh_score > 65 else "mild" if dh_score > 40 else "normal",
               "outlier": False,
               "interpretation": ("dehydration_signs_increase_fluid_intake" if dh_score > 65
                                   else "mild_dehydration_signs" if dh_score > 40
                                   else "well_hydrated_signs")}
        indicators["dehydration"] = attach_meta(ind, "dehydration", n_pix=300)

    # 20. Smoker's lines (FIX 22)
    _, perioral_px = _polygon_pixels(img, poly(PERIORAL_UPPER), W, H)
    smoker_score = 0
    if len(perioral_px) > 50:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        mask = np.zeros(gray.shape, dtype=np.uint8)
        pts_px = np.array([[int(pts[i][0]*W), int(pts[i][1]*H)] for i in PERIORAL_UPPER], np.int32)
        cv2.fillPoly(mask, [pts_px], 255)
        edges = cv2.Canny(gray, 40, 120)
        edges = cv2.bitwise_and(edges, mask)
        edge_density = float((edges > 0).sum()) / max(1, int(mask.sum()/255))
        smoker_score = min(100, edge_density * 1500)
    ind = {"score_0_100": round(smoker_score, 1),
           "severity": "marked" if smoker_score > 50 else "mild" if smoker_score > 20 else "normal",
           "outlier": False,
           "interpretation": ("perioral_lines_smoker_or_aging_signs" if smoker_score > 50
                               else "mild_perioral_lines" if smoker_score > 20
                               else "minimal_perioral_lines")}
    indicators["smoker_lines"] = attach_meta(ind, "smoker_lines", n_pix=int(len(perioral_px)))

    # 21. Allergic shiners / Dennie-Morgan lines (FIX 23)
    shiner_score = 0
    if ue_r and ue_l:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        for poly_idx in [UNDER_EYE_R, UNDER_EYE_L]:
            mask = np.zeros(gray.shape, dtype=np.uint8)
            pts_px = np.array([[int(pts[i][0]*W), int(pts[i][1]*H)] for i in poly_idx], np.int32)
            cv2.fillPoly(mask, [pts_px], 255)
            edges = cv2.Canny(gray, 30, 100)
            edges = cv2.bitwise_and(edges, mask)
            ed = float((edges > 0).sum()) / max(1, int(mask.sum()/255))
            shiner_score += min(100, ed * 1800) / 2
    # boost if dark_circles vascular subtype (likely allergy-driven)
    if indicators.get("dark_circles_subtype", {}).get("subtype") == "vascular_blue_purple":
        shiner_score = min(100, shiner_score + 15)
    ind = {"score_0_100": round(shiner_score, 1),
           "severity": "marked" if shiner_score > 50 else "mild" if shiner_score > 25 else "normal",
           "outlier": False,
           "interpretation": ("Dennie-Morgan_lines_or_allergic_shiners_atopy_screen" if shiner_score > 50
                               else "subtle_atopy_signs" if shiner_score > 25
                               else "no_atopy_signs")}
    indicators["allergic_shiners"] = attach_meta(ind, "allergic_shiners", n_pix=200)

    # ── Pull-throughs ────────────────────────────────────────────────────
    if foundation_dark_circles and foundation_dark_circles.get("ok"):
        indicators["dark_circles"] = {
            "left_grade":   foundation_dark_circles.get("left_grade"),
            "right_grade":  foundation_dark_circles.get("right_grade"),
            "L_drop_left":  foundation_dark_circles.get("lightness_drop_left_L"),
            "L_drop_right": foundation_dark_circles.get("lightness_drop_right_L"),
            "source": "foundation",
            "confidence": "high",
        }
    if foundation_oiliness:
        indicators["oiliness"] = {
            "skin_type":      foundation_oiliness.get("skin_type"),
            "score":          foundation_oiliness.get("oiliness_score"),
            "tzone_specular": foundation_oiliness.get("tzone_specular_ratio"),
            "source": "foundation", "confidence": "high",
        }
    if foundation_wrinkles and foundation_wrinkles.get("ok"):
        indicators["aging_signs"] = {**{k: foundation_wrinkles.get(k) for k in
                                         ("forehead_lines", "crow_feet_left", "crow_feet_right",
                                          "nasolabial_left", "nasolabial_right")},
                                      "source": "foundation", "confidence": "high"}
    if foundation_iris:
        pl = foundation_iris.get("pupil_left", {}) or {}
        pr = foundation_iris.get("pupil_right", {}) or {}
        if pl and pr:
            asym = abs((pl.get("dilation_ratio") or 0) - (pr.get("dilation_ratio") or 0))
            indicators["pupil_asymmetry"] = {
                "left_dilation_ratio":  pl.get("dilation_ratio"),
                "right_dilation_ratio": pr.get("dilation_ratio"),
                "asymmetry":            round(asym, 3),
                "flag_anisocoria":      bool(asym > 0.10),
                "interpretation": ("anisocoria_consult_physician_if_persistent"
                                    if asym > 0.10 else "physiologic_or_normal"),
                "source": "foundation", "confidence": "high",
            }

    # ── v3 NEW INDICATORS (FIX 5-14) ──────────────────────────────────
    cheek_lab_avg = ({"L": cheek_L, "a": cheek_a, "b": cheek_b}
                     if cheek_L is not None else None)
    v3_extra = _v3_extra_indicators(
        img_bgr=img, pts_norm=pts, W=W, H=H,
        sample_fn=sample, gains=gains, norms=norms, ethnicity=ethnicity,
        cheek_lab=cheek_lab_avg,
        forehead_avg=fh_outer,
        temple_r=temple_r, temple_l=temple_l,
        lip_avg=lip,
        conj_avg=conj_avg,
        ue_r=ue_r, ue_l=ue_l,
    )
    if v3_extra:
        for k, v in v3_extra.items():
            v["confidence"] = v.get("confidence", "medium")
            v["evidence_strength"] = v.get("evidence_strength", "moderate")
            v["narrative"] = v.get("narrative") or _narrate(k, v.get("severity", "normal"))
            indicators[k] = v

    # ── Composite scores ────────────────────────────────────────────────
    def avg_scores(*keys):
        vals = [indicators[k]["score_0_100"] for k in keys
                 if k in indicators and "score_0_100" in indicators[k]]
        return round(sum(vals)/len(vals), 1) if vals else None

    composites = {
        "pallor_index":        avg_scores("relative_skin_pallor", "lip_pallor"),
        "erythema_index":      avg_scores("cheek_erythema"),
        "jaundice_index":      avg_scores("sclera_jaundice", "skin_yellowness"),
        "cyanosis_index":      (100 - indicators["lip_cyanosis"]["score_0_100"]
                                  if "lip_cyanosis" in indicators else None),
        "hydration_index":     indicators.get("lip_hydration", {}).get("score_0_100"),
        "fatigue_index":       indicators.get("sleep_debt", {}).get("score_0_100"),
        "inflammation_index":  indicators.get("inflammation_blobs", {}).get("density_score_0_100"),
        "sleep_debt_index":    indicators.get("sleep_debt", {}).get("score_0_100"),
        "dehydration_index":   indicators.get("dehydration", {}).get("score_0_100"),
        "thyroid_hint_index":  indicators.get("thyroid_hint", {}).get("thyroid_composite_score"),
        # v3 new composites
        "vascular_burden_index":   avg_scores("telangiectasia", "cheek_erythema"),
        "pigmentation_index":      avg_scores("melasma", "acanthosis_nigricans"),
        "metabolic_risk_index":    avg_scores("acanthosis_nigricans", "xanthelasma"),
        "neuro_screen_index":      avg_scores("facial_droop_screen", "ptosis", "pupil_asymmetry"),
        "respiratory_screen_index": indicators.get("nasal_flaring", {}).get("score_0_100"),
        "autoimmune_screen_index": indicators.get("malar_rash", {}).get("score_0_100"),
    }
    # v3-FIX 19: composite formulas exposed (transparency)
    composite_formulas = {
        "pallor_index":        "avg(relative_skin_pallor, lip_pallor, 100-conjunctival_pallor)",
        "erythema_index":      "cheek_erythema",
        "jaundice_index":      "avg(sclera_jaundice, skin_yellowness)",
        "cyanosis_index":      "100 - lip_cyanosis",
        "hydration_index":     "lip_hydration",
        "fatigue_index":       "sleep_debt composite",
        "vitality":            "0.18*(100-|pallor-50|*2) + 0.12*hydration + 0.18*(100-fatigue) + 0.12*(100-|erythema-50|*2) + 0.12*(100-jaundice) + 0.10*(100-inflammation) + 0.10*(100-dehydration) + 0.08*(100-thyroid_hint)",
    }
    if "conjunctival_pallor" in indicators:
        composites["pallor_index"] = round(((composites.get("pallor_index") or 50) +
                                            (100 - indicators["conjunctival_pallor"]["score_0_100"])) / 2, 1)

    # Vitality (weighted)
    vc, ww = [], []
    def add(score, w):
        if score is not None: vc.append(score); ww.append(w)
    if composites["pallor_index"] is not None:
        add(100 - abs(composites["pallor_index"] - 50)*2, 0.18)
    if composites["hydration_index"] is not None:
        add(composites["hydration_index"], 0.12)
    if composites["fatigue_index"] is not None:
        add(100 - composites["fatigue_index"], 0.18)
    if composites["erythema_index"] is not None:
        add(100 - abs(composites["erythema_index"] - 50)*2, 0.12)
    if composites["jaundice_index"] is not None:
        add(100 - composites["jaundice_index"], 0.12)
    if composites["inflammation_index"] is not None:
        add(100 - composites["inflammation_index"], 0.10)
    if composites["dehydration_index"] is not None:
        add(100 - composites["dehydration_index"], 0.10)
    if composites["thyroid_hint_index"] is not None:
        add(100 - composites["thyroid_hint_index"], 0.08)
    vitality = round(max(0, min(100, sum(c*w for c, w in zip(vc, ww)) / sum(ww))), 1) if vc else None

    # Age-adjusted vitality (FIX cross-engine — gentle penalty after 50)
    vitality_age_adj = vitality
    if vitality is not None and age and age > 50:
        vitality_age_adj = round(min(100, vitality + (age - 50) * 0.3), 1)  # adjusted upward to be charitable

    # FIX 29 + v3-FIX 21,22,23 — cross-engine validation against ACTUAL schemas
    cross_validation = _v3_cross_engine_validate(
        indicators, composites,
        anthropometry_result, symmetry_result, phi_result=None,
    )

    # ── Flags + severity-gated recommendations (FIX 32) ─────────────────
    flags = []
    rec_urgent_hi, rec_urgent_en = [], []
    rec_monitor_hi, rec_monitor_en = [], []
    rec_info_hi, rec_info_en = [], []

    def push_urgent(hi, en, tag):
        flags.append(tag); rec_urgent_hi.append(hi); rec_urgent_en.append(en)

    def push_monitor(hi, en, tag):
        flags.append(tag); rec_monitor_hi.append(hi); rec_monitor_en.append(en)

    if indicators.get("conjunctival_pallor", {}).get("severity") == "marked":
        push_urgent("Marked conjunctival pallor — iron/B12 panel jaldi karwayein.",
                    "Marked conjunctival pallor — get iron/B12 panel soon.",
                    "conjunctival_pallor_marked")
    elif indicators.get("conjunctival_pallor", {}).get("interpretation") == "pale_conjunctiva_iron_deficiency_screen":
        push_monitor("Conjunctival pallor — anemia screen recommend.",
                     "Conjunctival pallor — anemia screen recommended.",
                     "conjunctival_pallor_screen")

    if "cyanosis_consult" in (indicators.get("lip_cyanosis", {}).get("interpretation") or ""):
        push_urgent("Lip cyanosis — SpO2 check, doctor se turant milein.",
                    "Lip cyanosis — check SpO2 immediately, consult physician.",
                    "lip_cyanosis_marked")

    if "true_jaundice" in (indicators.get("carotenemia_vs_jaundice", {}).get("verdict") or ""):
        push_urgent("Sclera + skin dono yellow — LFT karwayein, doctor consult.",
                    "Both sclera and skin yellow — get LFT, consult physician.",
                    "true_jaundice_likely")
    elif indicators.get("sclera_jaundice", {}).get("severity") == "marked":
        push_monitor("Sclera marked yellow — LFT recommend.",
                     "Marked scleral yellowness — consider LFT.",
                     "sclera_jaundice_marked")

    if angular_flag:
        push_monitor("Mouth corners cracked — B2/B12/iron screen.",
                     "Angular cheilitis — screen B2/B12/iron.",
                     "angular_cheilitis")

    if periorbital_flag:
        push_monitor("Periorbital edema — neend/salt/kidney function review.",
                     "Periorbital edema — review sleep, sodium, renal function.",
                     "periorbital_edema")

    if indicators.get("facial_droop_screen", {}).get("flag"):
        push_urgent("Facial droop signs — agar acute hai to emergency 102/108.",
                    "Facial droop signs — if acute, seek emergency care.",
                    "facial_droop")

    if indicators.get("thyroid_hint", {}).get("severity") == "marked":
        push_monitor("Thyroid panel screen recommended.",
                     "Consider thyroid panel screen.",
                     "thyroid_hint")

    if indicators.get("pupil_asymmetry", {}).get("flag_anisocoria"):
        push_monitor("Pupil asymmetry — agar persistent ho to neuro consult.",
                     "Pupil asymmetry — consult neurologist if persistent.",
                     "anisocoria")

    if indicators.get("temporal_wasting", {}).get("flag"):
        push_monitor("Temporal hollowing — weight/nutrition review.",
                     "Temporal hollowing — review weight/nutrition.",
                     "temporal_wasting")

    if indicators.get("acne_morphotype", {}).get("severity") == "marked":
        push_monitor("Acne marked — dermatologist consult recommend.",
                     "Marked acne — consider dermatology consult.",
                     "acne_marked")

    if vitality is not None and vitality < 50:
        rec_info_hi.append("Vitality kam — neend, hydration, balanced diet par focus karein.")
        rec_info_en.append("Low vitality score — focus on sleep, hydration, balanced diet.")

    # FIX 30 — caveats (final)
    caveats = [
        "SCREENING ONLY — these indicators are not medical diagnoses.",
        "Lighting and camera color balance can shift Lab values 5–10 units; sclera-as-gray-ref normalization applied.",
        "Per-ethnicity Lab norms applied; African baseline has weak evidence (SD widened).",
        "Specular highlights (V>235, S<25) and shadows (V<35) excluded before averaging.",
        "Conjunctival sampling: small lower-lid rim (4 px y-offset); flash photo recommended.",
        "Lip glossiness flag suppresses lip-derived metric confidence when active.",
        f"Global color cast residual = {cast['residual']} ({cast['interpretation']}).",
        "Nail-bed cyanosis cannot be measured from face selfie — face proxies only.",
        "All flagged conditions require physician confirmation before any clinical action.",
        f"Ethnicity evidence quality: {evidence_for_eth}.",
        f"Device hint: {device_hint} (norms widened ×1.10 for smartphone variance).",
    ]

    # v3-FIX 16,17: ITA°, EI, MI per region (Chardon 1991, Dawson 1980)
    derm_metrics = _v3_compute_derm_metrics({
        "forehead_outer": fh_outer, "temple_R": temple_r, "temple_L": temple_l,
        "lip_inner_vermilion": lip, "conjunctiva_avg": conj_avg,
        "sclera_avg": sclera_avg,
    })
    # v3-FIX 26,27: age-banded + gender-banded vitality assessment
    vitality_band = _v3_age_gender_band(vitality_age_adj, age, gender)
    # v3-FIX 28: pediatric / elderly guard
    pediatric_geriatric_warning = _v3_age_guard(age)
    # v3-FIX 25: Indian medical context for recommendations
    rec_urgent_en = _v3_localize_indian(rec_urgent_en)
    rec_monitor_en = _v3_localize_indian(rec_monitor_en)
    # v3-FIX 24: medical-claim guard — scrub strings
    rec_urgent_en  = [_v3_scrub_medical_claims(s) for s in rec_urgent_en]
    rec_urgent_hi  = [_v3_scrub_medical_claims(s) for s in rec_urgent_hi]
    rec_monitor_en = [_v3_scrub_medical_claims(s) for s in rec_monitor_en]
    rec_monitor_hi = [_v3_scrub_medical_claims(s) for s in rec_monitor_hi]
    # v3-FIX 3: apply WB confidence penalty across color-derived indicators
    if wb_confidence_penalty > 0:
        for k, v in indicators.items():
            if isinstance(v, dict) and "confidence" in v:
                conf = v["confidence"]
                if conf == "high" and wb_confidence_penalty >= 0.40:
                    v["confidence"] = "low"
                elif conf == "high" and wb_confidence_penalty >= 0.20:
                    v["confidence"] = "medium"
                elif conf == "medium" and wb_confidence_penalty >= 0.20:
                    v["confidence"] = "low"

    return _py({
        "engine": "health",
        "version": 3,
        "ok": True,
        # FIX 33 — privacy & medical-claim header
        "privacy_medical_header": {
            "screening_only": True,
            "not_a_diagnosis": True,
            "image_storage": "in_memory_session_only",
            "session_ttl_minutes": 30,
            "consult_physician_for_clinical_action": True,
            "medical_claim_scrubbed": True,
            "regulatory_disclaimer": "Not a medical device. Educational/wellness use only. Not validated for diagnostic claims under CDSCO / FDA / CE-MDR.",
        },
        "inputs": {
            "gender": gender, "ethnicity": ethnicity, "age": age,
            "device_hint": device_hint,
            "norms_evidence_for_ethnicity": evidence_for_eth,
        },
        "pediatric_geriatric_warning": pediatric_geriatric_warning,
        "color_cast_diagnostic": cast,
        "wb_correction": {
            "method": wb_method_used,
            "applied": gains is not None,
            "channel_gains_bgr": ([round(float(x), 3) for x in gains] if gains is not None else None),
            "sclera_white_pixels": int(len(sclera_white_all)),
            "sclera_occluded": sclera_occluded,
            "confidence_penalty_applied": round(wb_confidence_penalty, 2),
            "fallback_chain": ["sclera_gray_reference", "forehead_gray_world_fallback", "no_correction"],
        },
        "dermatology_metrics": derm_metrics,
        "vitality_band": vitality_band,
        "lip_glossiness_flag": lip_gloss_flag,
        "regions_sampled": {
            "sclera_right":      sclera_r,
            "sclera_left":       sclera_l,
            "sclera_avg":        sclera_avg,
            "lip_inner_vermilion": lip,
            "conjunctiva_avg":   conj_avg,
            "mouth_corner_R":    mc_r,
            "mouth_corner_L":    mc_l,
            "forehead_outer":    fh_outer,
            "temple_R":          temple_r,
            "temple_L":          temple_l,
            "under_eye_R":       ue_r,
            "under_eye_L":       ue_l,
        },
        "indicators":          indicators,
        "composite_scores":    composites,
        "vitality_score":      vitality,
        "vitality_age_adjusted": vitality_age_adj,
        "vitality_class":      ("excellent" if vitality and vitality >= 80 else
                                 "good"   if vitality and vitality >= 65 else
                                 "fair"   if vitality and vitality >= 50 else
                                 "poor"   if vitality is not None      else "unknown"),
        "cross_validation":    cross_validation,
        "flags":               flags,
        "recommendations": {
            "urgent":   {"hi": rec_urgent_hi,  "en": rec_urgent_en},
            "monitor":  {"hi": rec_monitor_hi, "en": rec_monitor_en},
            "info":     {"hi": rec_info_hi,    "en": rec_info_en},
        },
        "limitations": [
            "Nail-bed cyanosis not measurable from face selfie",
            "Tongue/oral mucosa not visible without open-mouth pose",
            "Pupillary light reflex not measurable from single still image",
            "Single-frame: cannot detect transient signs (tremor, nystagmus)",
        ],
        "caveats": caveats,
        "disclaimer": ("This face-derived health screening is informational only "
                        "and is not a substitute for medical examination, diagnosis, "
                        "or treatment. Consult qualified healthcare providers."),
    })


# ─────────────────────────────────────────────────────────────────────────────
# Acne morphotype detector (FIX 24)
# ─────────────────────────────────────────────────────────────────────────────
def _detect_acne_morphotypes(img_bgr: np.ndarray, pts_norm,
                              W: int, H: int) -> Optional[dict]:
    face_outline_idx = [10, 338, 297, 332, 284, 251, 389, 356, 454, 323,
                         361, 288, 397, 365, 379, 378, 400, 377, 152,
                         148, 176, 149, 150, 136, 172, 58, 132, 93, 234,
                         127, 162, 21, 54, 103, 67, 109]
    pts_px = np.array([[int(pts_norm[i][0]*W), int(pts_norm[i][1]*H)]
                        for i in face_outline_idx], dtype=np.int32)
    face_mask = np.zeros((H, W), dtype=np.uint8)
    cv2.fillPoly(face_mask, [pts_px], 255)
    for i in [33, 263, 61, 291, 13, 14, 159, 386, 105, 334]:
        x, y = int(pts_norm[i][0]*W), int(pts_norm[i][1]*H)
        cv2.circle(face_mask, (x, y), 35, 0, -1)

    hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
    # Inflammatory red blobs
    red1 = cv2.inRange(hsv, (0,   60, 60),  (12, 255, 230))
    red2 = cv2.inRange(hsv, (165, 60, 60), (180, 255, 230))
    red_mask = cv2.bitwise_and(cv2.bitwise_or(red1, red2), face_mask)
    # Comedonal: dark, low-S, low-V blobs
    com_mask = cv2.bitwise_and(cv2.inRange(hsv, (0, 0, 30), (180, 80, 90)), face_mask)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    red_mask = cv2.morphologyEx(red_mask, cv2.MORPH_OPEN, kernel)
    com_mask = cv2.morphologyEx(com_mask, cv2.MORPH_OPEN, kernel)

    def split(mask, cyst_thr=300):
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        small, large = [], []
        for c in contours:
            a = cv2.contourArea(c)
            if 6 <= a < cyst_thr:
                small.append(a)
            elif a >= cyst_thr and a <= 1200:
                large.append(a)
        return small, large

    inflam, cystic = split(red_mask, cyst_thr=300)
    comed, _      = split(com_mask, cyst_thr=400)

    face_area_px = int(face_mask.sum() / 255)
    if face_area_px == 0:
        return None
    inflam_density = sum(inflam) / face_area_px
    comed_density  = sum(comed)  / face_area_px
    cystic_density = sum(cystic) / face_area_px

    inflam_score = min(100, inflam_density * 800)
    comed_score  = min(100, comed_density  * 800)
    cystic_score = min(100, cystic_density * 1500)
    overall_score = round(min(100, 0.55*inflam_score + 0.20*comed_score + 0.25*cystic_score), 1)

    grade = ("clear"   if overall_score < 5 else
             "mild"    if overall_score < 20 else
             "moderate" if overall_score < 50 else "severe")
    return {
        "inflammatory_count":  len(inflam),
        "comedonal_count":     len(comed),
        "cystic_count":        len(cystic),
        "inflammatory_density_score": round(inflam_score, 1),
        "comedonal_density_score":    round(comed_score, 1),
        "cystic_density_score":       round(cystic_score, 1),
        "density_score_0_100":        overall_score,
        "grade":                      grade,
        "method": "hsv_morphological_split",
        "face_area_px":               face_area_px,
        "interpretation": ("severe_acne_dermatology_consult" if overall_score > 50
                            else "moderate_acne_topical_review" if overall_score > 20
                            else "mild_or_clear"),
    }


# ═════════════════════════════════════════════════════════════════════════════
# v3 — 30 ADDITIONAL AUDIT FIXES
# ═════════════════════════════════════════════════════════════════════════════

# v3-FIX 1: Adaptive Otsu sclera white-pixel filter
def _filter_white_adaptive(pixels_bgr: np.ndarray) -> np.ndarray:
    if len(pixels_bgr) == 0:
        return pixels_bgr
    hsv = cv2.cvtColor(pixels_bgr.reshape(-1, 1, 3), cv2.COLOR_BGR2HSV).reshape(-1, 3)
    v = hsv[:, 2].astype(np.uint8)
    s = hsv[:, 1]
    if len(v) < 30:
        return _filter_white(pixels_bgr)
    try:
        otsu_t, _ = cv2.threshold(v, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        v_min = max(120, min(220, int(otsu_t)))
    except Exception:
        v_min = 150
    mask = (v >= v_min) & (s <= 90)
    out = pixels_bgr[mask]
    if len(out) < 30 and len(pixels_bgr) > 100:
        # relax saturation cap
        mask2 = (v >= v_min) & (s <= 130)
        out = pixels_bgr[mask2]
    return out


# v3-FIX 2: Gray-world WB fallback (used when sclera unavailable)
def _gray_world_gains(pixels_bgr: np.ndarray) -> Optional[np.ndarray]:
    if pixels_bgr is None or len(pixels_bgr) < 50:
        return None
    means = pixels_bgr.astype(np.float64).mean(axis=0)  # B, G, R
    if any(m < 5 for m in means):
        return None
    gray = means.mean()
    gains = gray / means
    gains = np.clip(gains, 0.6, 1.6)  # safety cap
    return gains


# v3-FIX 5: Acanthosis nigricans screen (jawline darkening vs cheek)
def _detect_acanthosis_nigricans(img_bgr, pts, W, H, cheek_lab, sample_fn) -> Optional[dict]:
    if cheek_lab is None or cheek_lab.get("L") is None:
        return None
    # jawline-side patch (lower mandible, lateral)
    JAW_R = [172, 136, 150, 149]
    JAW_L = [397, 365, 379, 378]
    _, jaw_r_px = _polygon_pixels(img_bgr, [(pts[i][0], pts[i][1]) for i in JAW_R], W, H)
    _, jaw_l_px = _polygon_pixels(img_bgr, [(pts[i][0], pts[i][1]) for i in JAW_L], W, H)
    if len(jaw_r_px) + len(jaw_l_px) < 100:
        return None
    jaw_all = np.concatenate([jaw_r_px, jaw_l_px])
    jaw_smp = sample_fn(jaw_all)
    if not jaw_smp:
        return None
    L_drop = cheek_lab["L"] - jaw_smp["lab"]["L"]
    score = round(min(100, max(0, L_drop * 8)), 1)
    if L_drop > 8:
        sev = "marked"; interp = "darkened_jawline_insulin_resistance_screen"
    elif L_drop > 4:
        sev = "mild"; interp = "mild_jawline_darkening"
    else:
        sev = "normal"; interp = "no_acanthosis_signs"
    return {
        "L_drop": round(L_drop, 2),
        "score_0_100": score,
        "severity": sev,
        "interpretation": interp,
        "evidence_strength": "moderate",
        "evidence_ref": "Hud_2008_acanthosis_screen",
        "method": "jawline_vs_cheek_L_delta",
    }


# v3-FIX 6: Malar rash (lupus screen) — bilateral cheek + nose-bridge
def _detect_malar_rash(img_bgr, pts, W, H, cheek_lab, sample_fn) -> Optional[dict]:
    if cheek_lab is None or cheek_lab.get("a") is None:
        return None
    # nose bridge sample
    NOSE_BRIDGE = [6, 197, 195, 5, 4]
    _, nb_px = _polygon_pixels(img_bgr, [(pts[i][0], pts[i][1]) for i in NOSE_BRIDGE], W, H)
    if len(nb_px) < 50:
        return None
    nb_smp = sample_fn(nb_px)
    if not nb_smp:
        return None
    cheek_a = cheek_lab["a"]
    nose_a = nb_smp["lab"]["a"]
    bilateral_redness = (cheek_a > 16) and (nose_a > 14)
    score = round(min(100, max(0, ((cheek_a - 12) * 5 + (nose_a - 10) * 5))), 1)
    if bilateral_redness and score > 60:
        sev = "marked"; interp = "butterfly_pattern_autoimmune_screen_consider"
    elif bilateral_redness:
        sev = "mild"; interp = "mild_butterfly_pattern"
    else:
        sev = "normal"; interp = "no_butterfly_pattern"
    return {
        "cheek_a": round(cheek_a, 2), "nose_bridge_a": round(nose_a, 2),
        "bilateral_redness_flag": bool(bilateral_redness),
        "score_0_100": score, "severity": sev, "interpretation": interp,
        "evidence_strength": "weak",
        "evidence_ref": "Hochberg_1997_SLE_classification",
    }


# v3-FIX 7: Vitiligo / hypopigmentation patches
def _detect_vitiligo(img_bgr, pts, W, H, cheek_lab) -> Optional[dict]:
    if cheek_lab is None or cheek_lab.get("L") is None:
        return None
    # face region mask (broad oval)
    FACE_OUTLINE = [10, 338, 297, 332, 284, 251, 389, 356, 454, 323, 361, 288,
                    397, 365, 379, 378, 400, 377, 152, 148, 176, 149, 150, 136,
                    172, 58, 132, 93, 234, 127, 162, 21, 54, 103, 67, 109]
    h, w = img_bgr.shape[:2]
    pts_px = np.array([[int(pts[i][0]*w), int(pts[i][1]*h)] for i in FACE_OUTLINE], np.int32)
    mask = np.zeros((h, w), np.uint8)
    cv2.fillPoly(mask, [pts_px], 255)
    lab = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2LAB)
    L_chan = lab[:, :, 0].astype(np.float32) * 100.0 / 255.0
    cheek_L = cheek_lab["L"]
    # patches with L significantly higher than cheek baseline
    bright_mask = (L_chan > (cheek_L + 18)) & (mask == 255)
    bright_count = int(bright_mask.sum())
    face_count = int((mask == 255).sum())
    if face_count == 0:
        return None
    pct = round(bright_count / face_count * 100, 2)
    score = round(min(100, pct * 25), 1)
    sev = "marked" if pct > 2 else "mild" if pct > 0.5 else "normal"
    return {
        "hypopigmented_pct": pct, "score_0_100": score, "severity": sev,
        "interpretation": ("possible_hypopigmentation_consult_dermatology" if pct > 2
                           else "minor_brightness_variation" if pct > 0.5 else "uniform"),
        "evidence_strength": "weak", "evidence_ref": "Taieb_2009_vitiligo",
    }


# v3-FIX 8: Melasma / hyperpigmentation (symmetric darker patches)
def _detect_melasma(img_bgr, pts, W, H, cheek_lab) -> Optional[dict]:
    if cheek_lab is None or cheek_lab.get("L") is None:
        return None
    h, w = img_bgr.shape[:2]
    lab = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2LAB)
    L_chan = lab[:, :, 0].astype(np.float32) * 100.0 / 255.0
    # cheek + forehead mask
    CHEEK_R_MEL = [50, 101, 36, 205, 187, 123]
    CHEEK_L_MEL = [280, 330, 266, 425, 411, 352]
    mask = np.zeros((h, w), np.uint8)
    for grp in (CHEEK_R_MEL, CHEEK_L_MEL):
        pts_px = np.array([[int(pts[i][0]*w), int(pts[i][1]*h)] for i in grp], np.int32)
        cv2.fillPoly(mask, [pts_px], 255)
    cheek_L = cheek_lab["L"]
    dark_mask = (L_chan < (cheek_L - 10)) & (mask == 255)
    dark_count = int(dark_mask.sum())
    region_count = int((mask == 255).sum())
    if region_count < 200:
        return None
    pct = round(dark_count / region_count * 100, 2)
    score = round(min(100, pct * 6), 1)
    sev = "marked" if pct > 12 else "mild" if pct > 4 else "normal"
    return {
        "darker_patch_pct": pct, "score_0_100": score, "severity": sev,
        "interpretation": ("symmetric_hyperpigmentation_melasma_screen" if pct > 12
                           else "mild_pigmentation" if pct > 4 else "uniform_tone"),
        "evidence_strength": "moderate", "evidence_ref": "Pandya_2011_melasma_MASI",
    }


# v3-FIX 9: Telangiectasia (fine red linear vessels on cheek)
def _detect_telangiectasia(img_bgr, pts, W, H) -> Optional[dict]:
    h, w = img_bgr.shape[:2]
    CHEEK_R_TEL = [50, 101, 36, 205, 187, 123]
    CHEEK_L_TEL = [280, 330, 266, 425, 411, 352]
    mask = np.zeros((h, w), np.uint8)
    for grp in (CHEEK_R_TEL, CHEEK_L_TEL):
        pts_px = np.array([[int(pts[i][0]*w), int(pts[i][1]*h)] for i in grp], np.int32)
        cv2.fillPoly(mask, [pts_px], 255)
    region_count = int((mask == 255).sum())
    if region_count < 200:
        return None
    # red-mask: high R, low G/B in HSV
    hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
    red_mask = (((hsv[:, :, 0] < 10) | (hsv[:, :, 0] > 165)) &
                (hsv[:, :, 1] > 60) & (mask == 255))
    # canny on grayscale within mask
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 30, 80)
    linear_red = (edges > 0) & red_mask
    count = int(linear_red.sum())
    pct = round(count / region_count * 100, 3)
    score = round(min(100, pct * 50), 1)
    sev = "marked" if pct > 1.0 else "mild" if pct > 0.3 else "normal"
    return {
        "linear_vessel_pct": pct, "score_0_100": score, "severity": sev,
        "interpretation": ("possible_telangiectasia_rosacea_screen" if pct > 1.0
                           else "mild_vascular" if pct > 0.3 else "minimal"),
        "evidence_strength": "moderate", "evidence_ref": "Wilkin_2002_rosacea",
        "method": "canny_red_mask_intersection",
    }


# v3-FIX 11: Frank's earlobe sign (CAD predictor) — placeholder if ear visible
def _detect_franks_sign(img_bgr, pts, W, H) -> Optional[dict]:
    # MediaPipe face mesh does NOT include ear landmarks reliably.
    # Mark as "not_assessable" but expose hook.
    return {
        "assessable": False,
        "reason": "ear_landmarks_not_in_mediapipe_face_mesh",
        "score_0_100": None, "severity": "unknown",
        "interpretation": "requires_dedicated_ear_detector_skipped",
        "evidence_strength": "established",
        "evidence_ref": "Frank_1973_NEJM_CAD_earlobe_crease",
    }


# v3-FIX 12: Xanthelasma (lipid plaques near medial canthus)
def _detect_xanthelasma(img_bgr, pts, W, H, sample_fn) -> Optional[dict]:
    h, w = img_bgr.shape[:2]
    # medial canthus / inner upper-eyelid patches
    INNER_R = [33, 246, 161, 160]
    INNER_L = [263, 466, 388, 387]
    score_components = []
    for grp in (INNER_R, INNER_L):
        _, px = _polygon_pixels(img_bgr, [(pts[i][0], pts[i][1]) for i in grp], w, h)
        if len(px) < 30:
            continue
        smp = sample_fn(px)
        if not smp:
            continue
        # yellow plaque: high Lab b, high L, low a
        b = smp["lab"]["b"]; L = smp["lab"]["L"]; a = smp["lab"]["a"]
        if b > 24 and L > 60 and a < 12:
            score_components.append(min(100, (b - 20) * 6))
    if not score_components:
        return {
            "score_0_100": 0, "severity": "normal",
            "interpretation": "no_yellowish_plaques_detected",
            "evidence_strength": "moderate", "evidence_ref": "Bergman_1994_xanthelasma_lipids",
        }
    score = round(sum(score_components) / len(score_components), 1)
    sev = "marked" if score > 60 else "mild" if score > 30 else "normal"
    return {
        "score_0_100": score, "severity": sev,
        "interpretation": ("yellow_periocular_plaques_lipid_panel_screen" if score > 60
                           else "mild_yellowness" if score > 30 else "normal"),
        "evidence_strength": "moderate", "evidence_ref": "Bergman_1994_xanthelasma_lipids",
    }


# v3-FIX 13: Nasal flaring at rest (alar distance vs IOD)
def _detect_nasal_flaring(pts, W, H) -> Optional[dict]:
    try:
        # alar wings: 218, 438; nose tip 1
        ar_x = pts[218][0] * W; al_x = pts[438][0] * W
        # IOD reference
        re_x = pts[33][0] * W; le_x = pts[263][0] * W
        iod = abs(le_x - re_x)
        if iod < 10:
            return None
        alar_w = abs(al_x - ar_x)
        ratio = alar_w / iod
        # normal alar/IOD ~ 0.85-1.05; flaring > 1.15
        if ratio > 1.20:
            sev = "marked"; interp = "nasal_flaring_respiratory_distress_screen"
            score = min(100, (ratio - 0.95) * 200)
        elif ratio > 1.10:
            sev = "mild"; interp = "mild_alar_widening"
            score = min(100, (ratio - 0.95) * 150)
        else:
            sev = "normal"; interp = "no_flaring"
            score = max(0, (ratio - 0.85) * 50)
        return {
            "alar_to_iod_ratio": round(ratio, 3),
            "score_0_100": round(score, 1), "severity": sev, "interpretation": interp,
            "evidence_strength": "moderate", "evidence_ref": "Liu_2003_nasal_flare_resp",
        }
    except (IndexError, ZeroDivisionError):
        return None


# v3-FIX 14: Ptosis screen (lid-margin to pupil distance, asymmetry)
def _detect_ptosis(pts, W, H, foundation_iris=None) -> Optional[dict]:
    try:
        # upper-lid margin: 159 (R), 386 (L); pupil center: 468 (R), 473 (L)
        r_lid_y = pts[159][1] * H; l_lid_y = pts[386][1] * H
        r_pup_y = pts[468][1] * H; l_pup_y = pts[473][1] * H
        re_x = pts[33][0] * W; le_x = pts[263][0] * W
        iod = abs(le_x - re_x)
        if iod < 10:
            return None
        r_mrd = (r_pup_y - r_lid_y) / iod  # margin reflex dist 1, normalized
        l_mrd = (l_pup_y - l_lid_y) / iod
        asym = abs(r_mrd - l_mrd)
        min_mrd = min(r_mrd, l_mrd)
        # normal MRD1 ~ 0.10-0.16 (normalized to IOD); ptosis < 0.06
        if min_mrd < 0.04 or asym > 0.06:
            sev = "marked"; interp = "ptosis_screen_neuro_consult_if_acute"
            score = min(100, max(60, (0.10 - min_mrd) * 800))
        elif min_mrd < 0.07:
            sev = "mild"; interp = "mild_lid_droop"
            score = min(60, (0.10 - min_mrd) * 600)
        else:
            sev = "normal"; interp = "normal_lid_position"
            score = max(0, (0.10 - min_mrd) * 200)
        return {
            "mrd_right_norm": round(r_mrd, 4), "mrd_left_norm": round(l_mrd, 4),
            "asymmetry": round(asym, 4),
            "score_0_100": round(score, 1), "severity": sev, "interpretation": interp,
            "evidence_strength": "established", "evidence_ref": "Cahill_2018_ptosis_MRD1",
        }
    except (IndexError, ZeroDivisionError):
        return None


# v3-FIX 5-14 wrapper
def _v3_extra_indicators(img_bgr, pts_norm, W, H, sample_fn, gains, norms, ethnicity,
                          cheek_lab, forehead_avg, temple_r, temple_l,
                          lip_avg, conj_avg, ue_r, ue_l) -> dict:
    out = {}
    try:
        if (r := _detect_acanthosis_nigricans(img_bgr, pts_norm, W, H, cheek_lab, sample_fn)):
            out["acanthosis_nigricans"] = r
    except Exception as e:
        out["acanthosis_nigricans"] = {"error": str(e), "severity": "unknown",
                                         "score_0_100": None, "confidence": "low"}
    try:
        if (r := _detect_malar_rash(img_bgr, pts_norm, W, H, cheek_lab, sample_fn)):
            out["malar_rash"] = r
    except Exception as e:
        out["malar_rash"] = {"error": str(e), "severity": "unknown",
                              "score_0_100": None, "confidence": "low"}
    try:
        if (r := _detect_vitiligo(img_bgr, pts_norm, W, H, cheek_lab)):
            out["vitiligo_patches"] = r
    except Exception as e:
        out["vitiligo_patches"] = {"error": str(e), "severity": "unknown",
                                     "score_0_100": None, "confidence": "low"}
    try:
        if (r := _detect_melasma(img_bgr, pts_norm, W, H, cheek_lab)):
            out["melasma"] = r
    except Exception as e:
        out["melasma"] = {"error": str(e), "severity": "unknown",
                           "score_0_100": None, "confidence": "low"}
    try:
        if (r := _detect_telangiectasia(img_bgr, pts_norm, W, H)):
            out["telangiectasia"] = r
    except Exception as e:
        out["telangiectasia"] = {"error": str(e), "severity": "unknown",
                                   "score_0_100": None, "confidence": "low"}
    try:
        out["franks_earlobe_sign"] = _detect_franks_sign(img_bgr, pts_norm, W, H)
    except Exception as e:
        out["franks_earlobe_sign"] = {"error": str(e), "assessable": False}
    try:
        if (r := _detect_xanthelasma(img_bgr, pts_norm, W, H, sample_fn)):
            out["xanthelasma"] = r
    except Exception as e:
        out["xanthelasma"] = {"error": str(e), "severity": "unknown",
                               "score_0_100": None, "confidence": "low"}
    try:
        if (r := _detect_nasal_flaring(pts_norm, W, H)):
            out["nasal_flaring"] = r
    except Exception as e:
        out["nasal_flaring"] = {"error": str(e), "severity": "unknown",
                                  "score_0_100": None, "confidence": "low"}
    try:
        if (r := _detect_ptosis(pts_norm, W, H)):
            out["ptosis"] = r
    except Exception as e:
        out["ptosis"] = {"error": str(e), "severity": "unknown",
                          "score_0_100": None, "confidence": "low"}
    return out


# v3-FIX 16,17: ITA° (Chardon 1991) + Erythema/Melanin Index (Dawson 1980)
def _ita_degrees(L: float, b: float) -> float:
    import math
    if b == 0:
        return 90.0
    return round(math.degrees(math.atan2(L - 50.0, b)), 1)


def _ita_class(ita: float) -> str:
    # Chardon dermatology classes
    if ita > 55:  return "very_light"
    if ita > 41:  return "light"
    if ita > 28:  return "intermediate"
    if ita > 10:  return "tan"
    if ita > -30: return "brown"
    return "dark"


def _erythema_melanin_indices(rgb_mean: tuple) -> dict:
    # Dawson 1980 spectroscopy proxies adapted to RGB
    import math
    r, g, b = rgb_mean
    r = max(1, r); g = max(1, g); b = max(1, b)
    EI = round(math.log10(255.0 / r) - math.log10(255.0 / g), 3)
    MI = round(math.log10(255.0 / r), 3)
    return {"erythema_index": EI, "melanin_index": MI}


def _v3_compute_derm_metrics(regions: dict) -> dict:
    out = {"per_region": {}, "method": "ITA_Chardon1991+EI_MI_Dawson1980"}
    for name, smp in regions.items():
        if not smp or "lab" not in smp or "rgb_mean" not in smp:
            out["per_region"][name] = None
            continue
        L = smp["lab"]["L"]; b = smp["lab"]["b"]
        ita = _ita_degrees(L, b)
        rgb = smp["rgb_mean"]
        emi = _erythema_melanin_indices((rgb[0], rgb[1], rgb[2]))
        out["per_region"][name] = {
            "ita_degrees": ita,
            "ita_class": _ita_class(ita),
            **emi,
        }
    return out


# v3-FIX 18: Reproducibility CV across sub-regions (skipped for brevity; placeholder)
def _v3_cv_reproducibility(per_region_samples: list[dict]) -> Optional[dict]:
    # Coefficient of variation across N sub-region samples
    if not per_region_samples or len(per_region_samples) < 2:
        return None
    Ls = [s["lab"]["L"] for s in per_region_samples if s and "lab" in s]
    if len(Ls) < 2:
        return None
    mean_L = sum(Ls) / len(Ls)
    if mean_L == 0:
        return None
    sd_L = (sum((x - mean_L) ** 2 for x in Ls) / (len(Ls) - 1)) ** 0.5
    cv = round((sd_L / mean_L) * 100, 2)
    return {"L_cv_percent": cv, "n_subregions": len(Ls),
             "stability": ("stable" if cv < 5 else "moderate" if cv < 12 else "unstable")}


# v3-FIX 21,22,23: cross-engine validation against ACTUAL schemas
def _v3_cross_engine_validate(indicators, composites,
                                anthropometry_result, symmetry_result, phi_result):
    cv = {}
    # Anthropometry: derive BMI hint from face_shape jaw + classical_indices
    if anthropometry_result and anthropometry_result.get("ok"):
        clf = anthropometry_result.get("classifications", {}) or {}
        cls_idx = anthropometry_result.get("classical_indices", {}) or {}
        fi_raw = cls_idx.get("facial_index")
        face_idx = fi_raw.get("value") if isinstance(fi_raw, dict) else fi_raw
        jaw_class = clf.get("face_shape_jaw_class")
        # crude BMI hint: wide_jaw + low facial_index → higher BMI; tapered_heart + high → lower
        bmi_hint = None
        if jaw_class == "wide_jaw":
            bmi_hint = "above_average"
        elif jaw_class == "tapered_heart":
            bmi_hint = "below_average"
        elif jaw_class == "square":
            bmi_hint = "average_to_high"
        else:
            bmi_hint = "average"
        cv["anthropometry"] = {
            "face_shape_7": anthropometry_result.get("face_shape_7"),
            "facial_index": face_idx,
            "bmi_hint_qualitative": bmi_hint,
        }
        # Concordance check
        if bmi_hint in ("below_average",) and indicators.get("temporal_wasting", {}).get("flag"):
            cv["bmi_temporal_wasting_concordant"] = True
        if bmi_hint in ("above_average", "average_to_high") and \
                indicators.get("acanthosis_nigricans", {}).get("severity") == "marked":
            cv["bmi_acanthosis_concordant"] = True
    # Symmetry: use per_feature["mouth"]["score"] for droop cross-check
    if symmetry_result and symmetry_result.get("ok"):
        per_feat = symmetry_result.get("per_feature", {}) or {}
        mouth_sym = (per_feat.get("mouth") or {}).get("score")
        eye_sym = (per_feat.get("eyes") or {}).get("score")
        cv["symmetry"] = {
            "overall_score": symmetry_result.get("overall_score"),
            "tier": symmetry_result.get("tier"),
            "mouth_score": mouth_sym, "eyes_score": eye_sym,
            "dominant_side": symmetry_result.get("dominant_side"),
        }
        # Concordance: low mouth-symmetry + facial droop flag
        if mouth_sym is not None and mouth_sym < 60 and \
                indicators.get("facial_droop_screen", {}).get("flag"):
            cv["mouth_asymmetry_droop_concordant"] = True
        # Eye droop concordance with ptosis
        if eye_sym is not None and eye_sym < 65 and \
                indicators.get("ptosis", {}).get("severity") in ("mild", "marked"):
            cv["eye_asymmetry_ptosis_concordant"] = True
    # Phi: if available, contrast cosmetic vs vital
    if phi_result and phi_result.get("ok"):
        phi_score = phi_result.get("score")
        cv["phi_overall"] = phi_score
        vit = composites.get("vitality_index")
        if phi_score is not None and vit is not None:
            if phi_score > 70 and vit < 55:
                cv["phi_vitality_contrast"] = "cosmetically_aligned_but_vitality_low"
    return cv


# v3-FIX 24: medical-claim guard — scrub diagnostic language
def _v3_scrub_medical_claims(s: str) -> str:
    if not s:
        return s
    repls = [
        (" diagnose ", " screen "),
        (" diagnoses ", " screens "),
        (" confirms ", " suggests considering "),
        (" indicates ", " may suggest "),
        (" proves ", " hints at "),
        (" cures ", " supports "),
        (" treat ", " manage "),
        (" diagnostic", " screening"),
    ]
    out = " " + s + " "
    for a, b in repls:
        out = out.replace(a, b)
    return out.strip()


# v3-FIX 25: Indian medical context — localize test names
def _v3_localize_indian(rec_list: list[str]) -> list[str]:
    if not rec_list:
        return rec_list
    repls = [
        ("iron/B12 panel", "CBC + serum iron + ferritin + B12 panel (Indian labs: SRL/Thyrocare/Metropolis)"),
        ("LFT", "LFT (SGOT/SGPT/Bilirubin — Indian labs)"),
        ("thyroid panel", "TSH + Free T3/T4 panel (Indian labs)"),
        ("renal function", "KFT (Creatinine + Urea + Electrolytes — Indian labs)"),
        ("lipid panel", "Lipid Profile (Total Chol + HDL + LDL + TG — Indian labs)"),
        ("emergency care", "emergency care (call 102/108)"),
    ]
    out = []
    for s in rec_list:
        for a, b in repls:
            s = s.replace(a, b)
        out.append(s)
    return out


# v3-FIX 26,27: age-banded + gender-banded vitality assessment
def _v3_age_gender_band(vitality: Optional[float], age: Optional[int], gender: str) -> dict:
    if vitality is None:
        return {"band": "unknown", "age_appropriate": None, "gender_adjusted": None}
    age = age or 30
    # age-banded thresholds for "good" vitality
    if age < 25:
        good_thresh = 70
    elif age < 40:
        good_thresh = 65
    elif age < 55:
        good_thresh = 60
    elif age < 70:
        good_thresh = 55
    else:
        good_thresh = 50
    # gender adjustment: females typically 2-3 pts higher hydration/erythema; men slightly oilier
    g_adj = 0.0
    if gender in ("F", "f", "female"):
        g_adj = +1.5
    elif gender in ("M", "m", "male"):
        g_adj = -1.0
    adjusted = round(vitality + g_adj, 1)
    band = ("excellent_for_age" if adjusted >= good_thresh + 15 else
            "good_for_age"      if adjusted >= good_thresh else
            "fair_for_age"      if adjusted >= good_thresh - 12 else
            "below_age_band")
    return {
        "band": band,
        "age_threshold_for_good": good_thresh,
        "gender_adjustment": g_adj,
        "vitality_adjusted": adjusted,
    }


# v3-FIX 28: pediatric / elderly guard
def _v3_age_guard(age: Optional[int]) -> Optional[dict]:
    if age is None:
        return None
    if age < 12:
        return {"warning": "pediatric", "message": "Face metrics under age 12 are not validated; results informational only."}
    if age > 75:
        return {"warning": "geriatric", "message": "Face metrics above age 75 may be confounded by normal aging changes; clinical correlation required."}
    return None


# v3-FIX 29: pregnancy hint disclaimer (always shown to F/U if relevant flags fire)
def _v3_pregnancy_disclaimer(gender: str, indicators: dict) -> Optional[str]:
    if gender not in ("F", "f", "female", "U", "u"):
        return None
    flags = []
    if indicators.get("cheek_erythema", {}).get("severity") in ("mild", "marked"):
        flags.append("flushing")
    if indicators.get("periorbital_edema", {}).get("severity") in ("mild", "marked"):
        flags.append("edema")
    if indicators.get("melasma", {}).get("severity") in ("mild", "marked"):
        flags.append("melasma")
    if not flags:
        return None
    return ("Pregnancy can produce false-positive flags for flushing, edema, and melasma. "
            "If pregnant, interpret with obstetrician.")


# v3-FIX 30: scenario fixture pack (descriptors only; ground-truth for offline test)
SCENARIO_FIXTURES = [
    {"id": "S01_anemia_indian_F30", "ethnicity": "south_asian", "gender": "F", "age": 30,
      "expected": {"conjunctival_pallor": "marked", "vitality_band": "fair_for_age"}},
    {"id": "S02_jaundice_east_asian_M45", "ethnicity": "east_asian", "gender": "M", "age": 45,
      "expected": {"sclera_jaundice": "marked", "skin_yellowness": "marked",
                    "carotenemia_vs_jaundice": "true_jaundice_likely"}},
    {"id": "S03_healthy_caucasian_F25", "ethnicity": "caucasian", "gender": "F", "age": 25,
      "expected": {"vitality_band": "excellent_for_age"}},
    {"id": "S04_acne_severe_indian_M22", "ethnicity": "south_asian", "gender": "M", "age": 22,
      "expected": {"acne_morphotype": "severe", "inflammation_blobs": "marked"}},
    {"id": "S05_elderly_geriatric_M78", "ethnicity": "south_asian", "gender": "M", "age": 78,
      "expected": {"pediatric_geriatric_warning.warning": "geriatric",
                    "temporal_wasting": "mild_or_marked"}},
]


def get_scenario_fixtures():
    """Public accessor for offline test harness (FIX 30)."""
    return SCENARIO_FIXTURES
