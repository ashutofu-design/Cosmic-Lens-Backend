"""Shared request normalization for face-reading API routes."""
from __future__ import annotations

from typing import Any, Optional


def normalize_gender(raw: Optional[str]) -> str:
    """Map mobile/API gender strings to M | F | U."""
    v = (raw or "U").strip().upper()
    if v in ("M", "MALE", "MAN", "BOY"):
        return "M"
    if v in ("F", "FEMALE", "WOMAN", "GIRL", "W"):
        return "F"
    if v in ("U", "UNKNOWN", "OTHER", "NONBINARY", "NB", ""):
        return "U"
    return "U"


def best_profile_landmark_set(landmark_sets: dict[str, Any]) -> tuple[Any | None, str | None]:
    """Pick the highest-quality left/right profile for phi side-view.

    Returns (LandmarkSet | None, angle_name | None).
    """
    best = None
    best_angle: str | None = None
    best_score = 0.0
    for angle in ("left", "right"):
        ls = landmark_sets.get(angle)
        if ls is None:
            continue
        q = getattr(ls, "quality", None)
        if q is None or not getattr(q, "face_detected", False):
            continue
        score = float(getattr(q, "score", 0) or 0)
        if score > best_score:
            best_score = score
            best = ls
            best_angle = angle
    return best, best_angle


# Minimum quality scores (0–100) to accept a photo for report generation
MIN_SCORE_FRONT = 50
MIN_SCORE_PROFILE = 35
# Profile uploads: only hard-reject below this (shallow angle still allowed)
MIN_SCORE_PROFILE_HARD = 28


def _issues_list(q: Any) -> list:
    if q is None:
        return []
    issues = getattr(q, "issues", None)
    if issues is None and isinstance(q, dict):
        issues = q.get("issues")
    return list(issues or [])


def angle_rejection_from_landmark_set(ls: Any, *, angle: str) -> tuple[bool, str, str]:
    """Return (accepted, code, user_message).

    Codes: ok | no_face | not_a_face | low_quality | multiple_faces
    """
    if ls is None:
        return False, "missing", "Photo missing."

    q = getattr(ls, "quality", None)
    issues = _issues_list(q)
    issues_lc = " ".join(issues).lower()

    face_ok = bool(getattr(q, "face_detected", False)) if q is not None else False
    score = int(getattr(q, "score", 0) or 0) if q is not None else 0
    min_score = MIN_SCORE_FRONT if angle == "front" else MIN_SCORE_PROFILE

    if not face_ok or "no_face_detected" in issues_lc or "no_face_in_image" in issues_lc:
        return (
            False,
            "no_face",
            "Is photo mein chehra detect nahi hua. Sirf apna face wali clear selfie upload karo.",
        )

    if "not_a_face" in issues_lc:
        return (
            False,
            "not_a_face",
            "Yeh image face reading ke liye valid nahi lagti (object/scene/wrong photo). Face selfie use karo.",
        )

    if "multiple_faces" in issues_lc:
        return (
            False,
            "multiple_faces",
            "Ek se zyada chehre detect hue. Sirf ek person ki photo upload karo.",
        )

    if score < min_score:
        if angle in ("left", "right") and score >= MIN_SCORE_PROFILE_HARD:
            return True, "ok", ""
        return (
            False,
            "low_quality",
            f"Photo quality kam hai ({score}/100). Lighting theek karo, camera seedha face par rakho.",
        )

    return True, "ok", ""


def angle_rejection_from_result_dict(angle: str, result: dict[str, Any]) -> tuple[bool, str, str]:
    """Validate API JSON angle block from landmark_set_to_dict."""
    if result.get("error"):
        return False, "processing_failed", "Photo process nahi ho payi. Dobara try karo."

    q = result.get("quality") or {}
    issues = list(q.get("issues") or [])
    issues_lc = " ".join(str(i) for i in issues).lower()

    if not q.get("face_detected"):
        if "no_face" in issues_lc or "no_face_detected" in issues_lc:
            return (
                False,
                "no_face",
                "Is photo mein chehra detect nahi hua. Sirf apna face wali clear selfie upload karo.",
            )
        return False, "no_face", "Chehra detect nahi hua — galat ya unclear photo."

    if "not_a_face" in issues_lc:
        return (
            False,
            "not_a_face",
            "Yeh face reading ke liye valid nahi (kuch aur object/scene ho sakta hai).",
        )

    if "multiple_faces" in issues_lc:
        return False, "multiple_faces", "Multiple faces — sirf ek person."

    score = int(q.get("score") or 0)
    min_score = MIN_SCORE_FRONT if angle == "front" else MIN_SCORE_PROFILE
    if score < min_score:
        if angle in ("left", "right") and score >= MIN_SCORE_PROFILE_HARD:
            return True, "ok", ""
        return False, "low_quality", f"Quality kam ({score}/100). Retake with better light."

    return True, "ok", ""


def validate_uploaded_angles(
    results: dict[str, Any],
    angles_expected: tuple[str, ...] = ("front", "left", "right"),
) -> dict[str, Any]:
    """Build rejection map for all uploaded angles."""
    rejected: dict[str, Any] = {}
    for angle in angles_expected:
        if angle not in results:
            continue
        ok, code, msg = angle_rejection_from_result_dict(angle, results[angle])
        if not ok:
            rejected[angle] = {"code": code, "message": msg}
    return rejected


def profile_angles_summary(landmark_sets: dict[str, Any]) -> dict[str, Any]:
    """Per-angle quality snapshot for API / mobile UI."""
    out: dict[str, Any] = {}
    for angle in ("front", "left", "right"):
        ls = landmark_sets.get(angle)
        if ls is None:
            out[angle] = {"present": False}
            continue
        q = getattr(ls, "quality", None)
        out[angle] = {
            "present": True,
            "face_detected": bool(getattr(q, "face_detected", False)),
            "score": int(getattr(q, "score", 0) or 0),
            "issues": list(getattr(q, "issues", []) or [])[:6],
        }
    return out
