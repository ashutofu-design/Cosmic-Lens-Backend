"""
Mole Detector v1 — Section 17 "Secret Markings on Face"

Detects moles/dark spots on face using OpenCV blob detection on the
RGB image, then maps each mole to a classical Samudrika Shastra zone
with its phala (life meaning) in Hinglish.

Inputs:
    rgb_image:  np.ndarray (H, W, 3) RGB uint8
    points_px:  list of (x, y) pixel landmark tuples (468 from MediaPipe FaceMesh)

Output:
    {
      "engine": "mole_detector",
      "version": 1,
      "ok": True,
      "mole_count": int,
      "moles": [
          {"zone": "...", "zone_hi": "...", "phala_hi": "...",
           "x": int, "y": int, "size_px": int, "darkness": float}
      ],
      "summary_hi": "...",
      "disclaimer": "Computer-vision based estimate. Not a medical diagnosis."
    }
"""
from __future__ import annotations
from typing import List, Tuple, Dict, Optional
import numpy as np

try:
    import cv2
except Exception:
    cv2 = None


# ── Classical Samudrika mole-zone phala (Hinglish) ──────────────────────────
ZONE_MEANINGS: Dict[str, Dict[str, str]] = {
    "forehead_center":   {"hi": "Madhya-Lalat",       "phala_hi": "Leadership aur naam-shohrat ka sanket — log naturally tumhari taraf dekhte hain."},
    "forehead_right":    {"hi": "Dakshin-Lalat",      "phala_hi": "Career me unexpected promotion aur fame ka yog."},
    "forehead_left":     {"hi": "Vaam-Lalat",         "phala_hi": "Travel aur foreign opportunities likhi hain."},
    "between_brows":     {"hi": "Bhrumadhya",         "phala_hi": "Spiritual destiny strong — intuition par bharosa karo, sahi disha milegi."},
    "nose_tip":          {"hi": "Nasagra",            "phala_hi": "Achanak dhan-laabh — sudden money flow ka sanket."},
    "nose_bridge":       {"hi": "Nasa-Madhya",        "phala_hi": "Ambition aur willpower zyada — apni baat manvane ki shakti."},
    "right_eye_area":    {"hi": "Dakshin-Netra",      "phala_hi": "Bhagya saath deta hai — lucky breaks aate hain."},
    "left_eye_area":     {"hi": "Vaam-Netra",         "phala_hi": "Emotionally sensitive — relationships me dil zyada laga lete ho."},
    "right_cheek":       {"hi": "Dakshin-Kapola",     "phala_hi": "Dhan aur sampatti ka indicator — savings naturally banti hain."},
    "left_cheek":        {"hi": "Vaam-Kapola",        "phala_hi": "Struggle phase aate hain but har baar wapas uth jate ho."},
    "upper_lip":         {"hi": "Uttara-Oshtha",      "phala_hi": "Magnetic personality — opposite gender aakarshit hota hai."},
    "lower_lip":         {"hi": "Adhara-Oshtha",      "phala_hi": "Bhog-vilas aur taste me indulgent — khane-peene ke shaukeen."},
    "chin":              {"hi": "Chibuka",            "phala_hi": "Budhape me wealth aur respect — late-life prosperity."},
    "right_jaw":         {"hi": "Dakshin-Hanu",       "phala_hi": "Sambandh strong rehte hain — loyal partner milta hai."},
    "left_jaw":          {"hi": "Vaam-Hanu",          "phala_hi": "Family me vivad ka risk — patience rakhna padega."},
}


# ── Key MediaPipe FaceMesh landmark indices (468-point model) ────────────────
# Reference: https://github.com/google/mediapipe/blob/master/mediapipe/python/solutions/face_mesh_connections.py
_FACE_OVAL_IDX = [10, 338, 297, 332, 284, 251, 389, 356, 454, 323, 361, 288,
                  397, 365, 379, 378, 400, 377, 152, 148, 176, 149, 150, 136,
                  172, 58, 132, 93, 234, 127, 162, 21, 54, 103, 67, 109]
_LEFT_EYE_IDX  = [33, 133, 159, 145]   # outer, inner, top, bottom
_RIGHT_EYE_IDX = [362, 263, 386, 374]
_NOSE_TIP_IDX  = 4
_NOSE_BRIDGE_IDX = 6  # between brows-ish
_FOREHEAD_TOP_IDX = 10
_BROW_LEFT_INNER = 55
_BROW_RIGHT_INNER = 285
_LIP_UPPER_IDX = 13
_LIP_LOWER_IDX = 14
_CHIN_IDX = 152
_LEFT_CHEEK_IDX = 234
_RIGHT_CHEEK_IDX = 454


def _safe_pt(points_px: List[Tuple[int, int]], idx: int) -> Optional[Tuple[int, int]]:
    if 0 <= idx < len(points_px):
        return points_px[idx]
    return None


def _classify_zone(x: int, y: int, ref: Dict[str, Tuple[int, int]]) -> str:
    """Assign a mole at (x,y) to nearest classical zone by anchor distances + heuristics."""
    if not ref:
        return "unknown"

    # Quick zone tests by Y bands first
    forehead_y = ref.get("forehead_top", (0, 0))[1]
    brow_y     = ((ref.get("brow_left", (0, 0))[1] + ref.get("brow_right", (0, 0))[1]) // 2) or forehead_y + 50
    nose_y     = ref.get("nose_tip", (0, 0))[1]
    lip_y      = ref.get("lip_upper", (0, 0))[1]
    chin_y     = ref.get("chin", (0, 0))[1]
    cheek_l_x  = ref.get("left_cheek", (0, 0))[0]
    cheek_r_x  = ref.get("right_cheek", (0, 0))[0]
    face_cx    = (cheek_l_x + cheek_r_x) // 2 if cheek_l_x and cheek_r_x else x

    # ── Forehead band (above eyebrows) ─────────────────────────────────────
    if y < brow_y - 5:
        if abs(x - face_cx) < 25:
            return "forehead_center"
        return "forehead_right" if x > face_cx else "forehead_left"

    # ── Between brows (Bhrumadhya) ─────────────────────────────────────────
    if brow_y - 5 <= y <= brow_y + 15 and abs(x - face_cx) < 20:
        return "between_brows"

    # ── Eye area band ──────────────────────────────────────────────────────
    if brow_y < y < nose_y - 15:
        return "right_eye_area" if x > face_cx else "left_eye_area"

    # ── Nose band ──────────────────────────────────────────────────────────
    if abs(x - face_cx) < 25 and nose_y - 25 <= y <= nose_y + 8:
        return "nose_tip" if y >= nose_y - 8 else "nose_bridge"

    # ── Cheek band (outside nose, above lips) ──────────────────────────────
    if nose_y - 20 < y < lip_y - 5 and abs(x - face_cx) >= 25:
        return "right_cheek" if x > face_cx else "left_cheek"

    # ── Lip band ───────────────────────────────────────────────────────────
    if lip_y - 5 <= y <= lip_y + 20:
        return "upper_lip"
    if lip_y + 10 < y < chin_y - 30:
        return "lower_lip"

    # ── Chin / jaw band ────────────────────────────────────────────────────
    if y >= chin_y - 30:
        if abs(x - face_cx) < 30:
            return "chin"
        return "right_jaw" if x > face_cx else "left_jaw"

    # Fallback by halves
    return "right_cheek" if x > face_cx else "left_cheek"


def _build_anchor_ref(points_px: List[Tuple[int, int]]) -> Dict[str, Tuple[int, int]]:
    return {
        "forehead_top": _safe_pt(points_px, _FOREHEAD_TOP_IDX) or (0, 0),
        "brow_left":    _safe_pt(points_px, _BROW_LEFT_INNER) or (0, 0),
        "brow_right":   _safe_pt(points_px, _BROW_RIGHT_INNER) or (0, 0),
        "nose_tip":     _safe_pt(points_px, _NOSE_TIP_IDX) or (0, 0),
        "nose_bridge":  _safe_pt(points_px, _NOSE_BRIDGE_IDX) or (0, 0),
        "lip_upper":    _safe_pt(points_px, _LIP_UPPER_IDX) or (0, 0),
        "lip_lower":    _safe_pt(points_px, _LIP_LOWER_IDX) or (0, 0),
        "chin":         _safe_pt(points_px, _CHIN_IDX) or (0, 0),
        "left_cheek":   _safe_pt(points_px, _LEFT_CHEEK_IDX) or (0, 0),
        "right_cheek":  _safe_pt(points_px, _RIGHT_CHEEK_IDX) or (0, 0),
    }


def _build_face_mask(rgb: np.ndarray, points_px: List[Tuple[int, int]]) -> np.ndarray:
    """Polygon mask of the face region using FACE_OVAL landmarks."""
    h, w = rgb.shape[:2]
    mask = np.zeros((h, w), dtype=np.uint8)
    pts = []
    for idx in _FACE_OVAL_IDX:
        p = _safe_pt(points_px, idx)
        if p:
            pts.append(p)
    if len(pts) >= 3:
        cv2.fillPoly(mask, [np.array(pts, dtype=np.int32)], 255)
    return mask


def _exclude_eyes_lips(mask: np.ndarray, points_px: List[Tuple[int, int]]) -> np.ndarray:
    """Carve out eye and inner-lip regions to reduce false positives."""
    out = mask.copy()
    for indices in (_LEFT_EYE_IDX, _RIGHT_EYE_IDX):
        pts = [p for p in (_safe_pt(points_px, i) for i in indices) if p]
        if len(pts) >= 3:
            xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
            cx, cy = (min(xs)+max(xs))//2, (min(ys)+max(ys))//2
            rx, ry = max(8, (max(xs)-min(xs))//2 + 6), max(6, (max(ys)-min(ys))//2 + 6)
            cv2.ellipse(out, (cx, cy), (rx, ry), 0, 0, 360, 0, -1)
    # Lips area
    lip_u = _safe_pt(points_px, _LIP_UPPER_IDX)
    lip_l = _safe_pt(points_px, _LIP_LOWER_IDX)
    if lip_u and lip_l:
        cx, cy = (lip_u[0]+lip_l[0])//2, (lip_u[1]+lip_l[1])//2
        cv2.ellipse(out, (cx, cy), (35, 18), 0, 0, 360, 0, -1)
    # Nostrils area (around nose tip, slightly below)
    nt = _safe_pt(points_px, _NOSE_TIP_IDX)
    if nt:
        cv2.ellipse(out, (nt[0], nt[1] + 4), (20, 10), 0, 0, 360, 0, -1)
    return out


def detect_moles(rgb_image: Optional[np.ndarray],
                 points_px: List[Tuple[int, int]],
                 max_moles: int = 8) -> Dict:
    """Main entrypoint."""
    if cv2 is None:
        return {"engine": "mole_detector", "version": 1, "ok": False,
                "error": "opencv_unavailable", "mole_count": 0, "moles": []}

    if rgb_image is None or not isinstance(rgb_image, np.ndarray):
        return {"engine": "mole_detector", "version": 1, "ok": False,
                "error": "no_image", "mole_count": 0, "moles": []}

    if not points_px or len(points_px) < 200:
        return {"engine": "mole_detector", "version": 1, "ok": False,
                "error": "insufficient_landmarks", "mole_count": 0, "moles": []}

    h, w = rgb_image.shape[:2]

    # 1. Face polygon mask + exclude eyes/lips/nostrils
    face_mask = _build_face_mask(rgb_image, points_px)
    skin_mask = _exclude_eyes_lips(face_mask, points_px)

    # 2. Convert to LAB; use L-channel (luminance) for darkness detection
    lab = cv2.cvtColor(rgb_image, cv2.COLOR_RGB2LAB)
    L = lab[:, :, 0].astype(np.float32)

    # 3. Compute local skin mean (large blur) and find points significantly darker
    blurred = cv2.GaussianBlur(L, (51, 51), 0)
    diff = blurred - L                                # positive where darker than local mean
    diff[skin_mask == 0] = 0

    # 4. Threshold + morphology
    _, mole_bin = cv2.threshold(diff, 18.0, 255, cv2.THRESH_BINARY)
    mole_bin = mole_bin.astype(np.uint8)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    mole_bin = cv2.morphologyEx(mole_bin, cv2.MORPH_OPEN,  kernel, iterations=1)
    mole_bin = cv2.morphologyEx(mole_bin, cv2.MORPH_CLOSE, kernel, iterations=1)

    # 5. Connected components → candidate blobs
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(mole_bin, connectivity=8)

    # 6. Filter by size + collect candidates
    iod = max(40, abs(_safe_pt(points_px, _LEFT_EYE_IDX[0])[0] - _safe_pt(points_px, _RIGHT_EYE_IDX[1])[0]) if _safe_pt(points_px, _LEFT_EYE_IDX[0]) and _safe_pt(points_px, _RIGHT_EYE_IDX[1]) else 60)
    min_area = max(4, int((iod / 60.0) ** 2 * 4))     # scale with face size
    max_area = max(60, int((iod / 60.0) ** 2 * 200))  # exclude shadows / large patches

    ref = _build_anchor_ref(points_px)
    candidates = []
    for i in range(1, num_labels):
        area = int(stats[i, cv2.CC_STAT_AREA])
        if area < min_area or area > max_area:
            continue
        cx, cy = int(centroids[i][0]), int(centroids[i][1])
        # Mean darkness over the blob (higher = darker than skin)
        blob_mask = (labels == i)
        darkness = float(np.mean(diff[blob_mask]))
        candidates.append((darkness, area, cx, cy))

    # 7. Sort by darkness × size, keep top N
    candidates.sort(key=lambda t: (t[0] * (t[1] ** 0.5)), reverse=True)
    top = candidates[:max_moles]

    moles_out = []
    seen_zones = set()
    for darkness, area, cx, cy in top:
        zone = _classify_zone(cx, cy, ref)
        if zone in seen_zones:
            continue  # one mole per zone is enough for the report
        seen_zones.add(zone)
        meaning = ZONE_MEANINGS.get(zone, {"hi": zone, "phala_hi": "Special marking — vishesh sanket."})
        moles_out.append({
            "zone": zone,
            "zone_hi": meaning["hi"],
            "phala_hi": meaning["phala_hi"],
            "x": cx, "y": cy,
            "size_px": int(area),
            "darkness": round(darkness, 2),
        })

    if not moles_out:
        summary_hi = "Tumhare chehre par koi prominent mole detect nahi hua — clean canvas hai. Iska matlab destiny tumhari apni khud ki banayi hui hogi."
    else:
        zones_hi = ", ".join(m["zone_hi"] for m in moles_out[:3])
        summary_hi = f"{len(moles_out)} prominent mole detect hue ({zones_hi})."

    return {
        "engine": "mole_detector",
        "version": 1,
        "ok": True,
        "mole_count": len(moles_out),
        "moles": moles_out,
        "summary_hi": summary_hi,
        "disclaimer": "Computer-vision based estimate; lighting aur image quality se accuracy vary kar sakti hai. Medical diagnosis nahi hai.",
    }


def section_17_secret_markings(detector_output: Dict) -> Dict:
    """Wrap mole_detector output into Section 17 of the 21-section report."""
    if not detector_output or not detector_output.get("ok"):
        return {
            "moles_found": 0,
            "moles": [],
            "summary_hi": "Mole detection skip ho gaya — clean canvas maan ke chalo.",
        }
    return {
        "moles_found": detector_output.get("mole_count", 0),
        "moles": [
            {
                "position_hi": m["zone_hi"],
                "position_en": m["zone"].replace("_", " ").title(),
                "meaning_hi": m["phala_hi"],
            }
            for m in detector_output.get("moles", [])
        ],
        "summary_hi": detector_output.get("summary_hi", ""),
    }
