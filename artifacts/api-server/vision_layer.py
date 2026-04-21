"""
vision_layer.py — Phase 6 glue between Photo Reading Engine and Flask routes.

Two responsibilities:
  1) extract_floor_plan_from_upload(payload, business_type, lang)
       Convert an image/PDF upload into a floor_plan list of {room_type,direction}
       suitable for the deterministic Vastu engine. Returns ({"rooms":[...],
       "structural_notes":[...], "confidence":N, "plot_shape":..., "main_entrance":...},
       error_or_None).

  2) annotate_report_with_room_photos(report, room_photos, lang)
       For each room photo provided, call analyze_room_visuals and merge
       findings into the matching room of the report. Applies a NET score_delta
       (capped to [-15, +10]) to report["overall"]["score"] (clamped 30..100).
       Returns vision_summary dict.

Design:
- Pure functions, no Flask imports.
- Never raise — return ({}, "error string") on failure so route can decide.
- Branding: never expose AI/OpenAI to user (already enforced in openai_helper).
"""
from __future__ import annotations

from typing import Any

# Canonical direction tokens accepted by the deterministic engines
_VALID_DIRS = {"N", "NE", "E", "SE", "S", "SW", "W", "NW", "center"}

# Server-side guards
_MAX_PHOTO_BYTES        = 8 * 1024 * 1024   # 8 MB raw decoded image per photo
_MAX_ROOM_PHOTOS        = 6
_ALLOWED_IMAGE_PREFIXES = ("data:image/jpeg", "data:image/jpg",
                           "data:image/png",  "data:image/webp")

# Brand-safe error message returned to users (never expose AI / OpenAI)
_BRAND_ERR_DEFAULT = "Photo Engine could not read this upload. Please try a clearer image or PDF."

def _brand_safe_error(_internal_reason: str) -> str:
    """Map any internal vision error to a single brand-safe user message."""
    # Internal reason intentionally ignored in user output; logged by caller.
    return _BRAND_ERR_DEFAULT


# Per-room retake guidance — what features the user should make sure to capture.
_ROOM_FEATURE_HINTS = {
    "kitchen":    "stove, sink, and counter",
    "bathroom":   "WC/commode, tap, and wall tiles",
    "pooja":      "mandir/idols and the altar area",
    "bedroom":    "bed and the wall behind it",
    "hall":       "sofa/seating area and the main wall",
    "livingroom": "sofa/seating area and the main wall",
    "office":     "desk and chair area",
    "cabin":      "desk and chair area",
    "factory":    "main machinery and floor area",
    "shop":       "counter and display shelves",
    "entrance":   "main door and threshold",
}

def _room_feature_hint(rt: str) -> str:
    return _ROOM_FEATURE_HINTS.get((rt or "").lower(), "key room features")

def _retake_guidance(rt: str, reason: str) -> str:
    """Craft a short retake tip combining what's wrong + what to capture."""
    feat = _room_feature_hint(rt)
    r = (reason or "").lower()
    if "paas" in r or "close" in r or "zoom" in r:
        return f"Step back 2-3 feet so {feat} all fit in one frame."
    if "door" in r or "far" in r or "duur" in r or "context" in r:
        return f"Move closer so the {feat} are clearly visible."
    if "dark" in r or "roshni" in r or "light" in r or "dim" in r:
        return f"Turn on the room lights and take the photo facing the {feat}."
    if "blur" in r or "shake" in r:
        return "Hold the phone steady and tap to focus before clicking."
    # Default — generic guidance
    return f"Stand at one corner and capture the {feat} in one clear frame with good lighting."


def _photo_size_bytes(data_url: str) -> int:
    """Approximate decoded byte size of a base64 data URL."""
    if "," in data_url:
        b64 = data_url.split(",", 1)[1]
    else:
        b64 = data_url
    # base64 expands by ~4/3
    return (len(b64) * 3) // 4


def _is_allowed_image_data_url(s: str) -> bool:
    if not isinstance(s, str):
        return False
    s_low = s.strip().lower()
    return any(s_low.startswith(p) for p in _ALLOWED_IMAGE_PREFIXES)


def extract_floor_plan_from_upload(
    upload_payload: dict,
    business_type: str | None = None,
    lang: str = "en",
) -> tuple[dict, str | None]:
    """
    upload_payload: {"type":"image"|"pdf","data_url"?|"base64"?:str}
    Returns (vision_dict, error_or_None) where vision_dict shape:
      {
        "rooms":            [ {room_type, direction}, ... ],   # ready for engine
        "rooms_full":       [ {room_type, direction, position_grid, notes}, ... ],
        "structural_notes": [...],
        "plot_shape":       str,
        "main_entrance":    str,
        "confidence":       int 0-100,
        "scan_inconclusive":bool,
        "inconclusive_reason": str,
      }
    """
    try:
        from floor_plan_loader import to_image_data_url
        from openai_helper import extract_floor_plan_layout
    except Exception as exc:
        print(f"[vision_layer] vision_unavailable: {exc}")
        return {}, _brand_safe_error(f"vision_unavailable: {exc}")

    try:
        png_data_url = to_image_data_url(upload_payload)
    except Exception as exc:
        print(f"[vision_layer] floor_plan_decode_failed: {exc}")
        return {}, _brand_safe_error(f"floor_plan_decode_failed: {exc}")

    try:
        raw = extract_floor_plan_layout(png_data_url, business_type=business_type, lang=lang)
    except Exception as exc:
        print(f"[vision_layer] vision_extract_failed: {exc}")
        return {}, _brand_safe_error(f"vision_extract_failed: {exc}")

    rooms_full = raw.get("rooms") or []
    engine_rooms: list[dict] = []
    full_rooms:   list[dict] = []
    for r in rooms_full:
        if not isinstance(r, dict):
            continue
        rt = (r.get("room_type") or "").strip().lower()
        d  = (r.get("direction") or "").strip()
        if not rt or d not in _VALID_DIRS:
            continue
        engine_rooms.append({"room_type": rt, "direction": d})
        full_rooms.append({
            "room_type": rt,
            "direction": d,
            "position_grid": (r.get("position_grid") or "").strip(),
            "notes":         (r.get("notes") or "").strip(),
        })

    return ({
        "rooms":              engine_rooms,
        "rooms_full":         full_rooms,
        "structural_notes":   list(raw.get("structural_notes") or [])[:10],
        "plot_shape":         (raw.get("plot_shape") or "").strip(),
        "main_entrance":      (raw.get("main_entrance_direction") or "").strip(),
        "confidence":         int(raw.get("confidence") or 0),
        "scan_inconclusive":  bool(raw.get("scan_inconclusive")),
        "inconclusive_reason":(raw.get("inconclusive_reason") or "").strip(),
    }, None)


def annotate_report_with_room_photos(
    report: dict,
    room_photos: list[dict],
    lang: str = "en",
) -> dict:
    """
    room_photos: list of {room_type, image_data_url|data_url|image, heading_deg?}
                 (max 6)
    Modifies `report` in-place:
      - For each photo, attach `visual_findings` to the matching room (by
        room_type, first match) under key 'visual_findings'.
      - Append a top-level 'vision_room_findings' summary list (room_type,
        n_findings, score_delta).
      - Adjust report['overall']['score'] by NET sum of score_deltas, capped
        to [-15, +10] in TOTAL across all photos. Final score clamped 30..100.

    Returns vision_summary dict:
      { "rooms_analyzed": N, "total_score_delta": int,
        "errors": [...], "scan_inconclusive_count": int }
    """
    summary: dict = {
        "rooms_analyzed":          0,
        "total_score_delta":       0,
        "errors":                  [],
        "scan_inconclusive_count": 0,
        "per_room":                [],
    }
    if not isinstance(room_photos, list) or not room_photos:
        return summary

    try:
        from openai_helper import analyze_room_visuals
    except Exception as exc:
        print(f"[vision_layer] room-photo vision_unavailable: {exc}")
        summary["errors"].append(_brand_safe_error(f"vision_unavailable: {exc}"))
        return summary

    rooms_in_report = report.get("rooms") or []
    if not isinstance(rooms_in_report, list):
        rooms_in_report = []

    net_delta = 0
    capped_total = 15  # absolute cap on |sum| of vision deltas applied to overall
    used_room_indices: set[int] = set()

    for i, p in enumerate(room_photos[:_MAX_ROOM_PHOTOS]):
        if not isinstance(p, dict):
            summary["errors"].append(f"Photo #{i+1}: invalid format.")
            continue
        rt  = (p.get("room_type") or "").strip().lower()
        img = (p.get("image_data_url") or p.get("data_url") or p.get("image") or "").strip()
        if not rt or not img:
            summary["errors"].append(f"Photo #{i+1}: room and image required.")
            continue
        if not _is_allowed_image_data_url(img):
            summary["errors"].append(f"Photo #{i+1}: unsupported image format. Use JPEG, PNG or WebP.")
            continue
        if _photo_size_bytes(img) > _MAX_PHOTO_BYTES:
            summary["errors"].append(f"Photo #{i+1}: image too large (max 8 MB).")
            continue
        h = p.get("heading_deg")
        try:
            h = float(h) if h is not None else None
        except Exception:
            h = None

        try:
            vf = analyze_room_visuals(img, rt, heading_deg=h, lang=lang)
        except Exception as exc:
            print(f"[vision_layer] photo[{i}]/{rt} failed: {exc}")
            summary["errors"].append(f"Photo #{i+1}: Photo Engine could not analyze this image.")
            continue

        if vf.get("scan_inconclusive"):
            summary["scan_inconclusive_count"] += 1

        # ── Room identity verification gate ──────────────────────────────
        identity_match    = vf.get("room_identity_match")
        detected_rt       = (vf.get("detected_room_type") or "").strip().lower()
        features_seen     = vf.get("identity_features_seen") or []
        inconclusive_why  = (vf.get("inconclusive_reason") or "").strip()
        # If model didn't include the new field (defensive), default True so
        # we don't break existing scans — but if explicitly False, reject.
        if identity_match is False:
            # Pretty room label used in the user-facing reject message.
            room_label = rt.replace("_", " ")
            # 1) Mismatch: detected a different specific room
            if detected_rt and detected_rt not in ("unclear", "", rt):
                detected_label = detected_rt.replace("_", " ")
                err_msg = (
                    f"This is not the exact {room_label} photo — looks like a "
                    f"{detected_label}. Please retake the photo from inside your "
                    f"{room_label} so the {_room_feature_hint(rt)} are clearly visible."
                )
            # 2) Too close / too far / dark / blurry — model gave a reason
            elif inconclusive_why:
                # Use model's specific reason + add retake guidance
                guidance = _retake_guidance(rt, inconclusive_why)
                err_msg = (
                    f"This is not the exact {room_label} photo. {inconclusive_why} "
                    f"Tip: {guidance}"
                )
            # 3) Generic unclear
            else:
                err_msg = (
                    f"This is not the exact {room_label} photo. "
                    f"Tip: {_retake_guidance(rt, '')}"
                )
            summary["errors"].append(err_msg)
            summary["per_room"].append({
                "room_type":          rt,
                "rejected":           True,
                "rejection_reason":   "room_identity_mismatch",
                "detected_room_type": detected_rt or "unclear",
                "features_seen":      list(features_seen)[:6],
                "findings_count":     0,
                "score_delta":        0,
                "matched_in_report":  False,
            })
            continue  # do NOT merge findings, do NOT apply score_delta

        findings = vf.get("visual_findings") or []
        delta    = int(vf.get("score_delta") or 0)

        # Match into the engine's room report by room_type (first un-used)
        matched_idx = -1
        for idx, rr in enumerate(rooms_in_report):
            if idx in used_room_indices:
                continue
            if (rr.get("room_type") or "").strip().lower() == rt:
                matched_idx = idx
                used_room_indices.add(idx)
                break
        # direction_basis is the trust signal we expose to UI:
        # "magnetometer" | "visual_inference" | "assumed"
        # If client sent heading_deg, force magnetometer regardless of model output.
        if h is not None:
            direction_basis = "magnetometer"
        else:
            direction_basis = (vf.get("direction_basis") or "").strip().lower() or "visual_inference"

        if matched_idx >= 0:
            existing = rooms_in_report[matched_idx].get("visual_findings") or []
            rooms_in_report[matched_idx]["visual_findings"] = existing + findings
            rooms_in_report[matched_idx]["visual_score_delta"] = delta
            rooms_in_report[matched_idx]["direction_basis"]    = direction_basis
        # If no room match, findings still surface in summary

        summary["rooms_analyzed"] += 1
        summary["per_room"].append({
            "room_type":          rt,
            "findings_count":     len(findings),
            "score_delta":        delta,
            "confidence":         int(vf.get("confidence") or 0),
            "scan_inconclusive":  bool(vf.get("scan_inconclusive")),
            "matched_in_report":  matched_idx >= 0,
            "direction_basis":    direction_basis,
        })
        net_delta += delta

    # Cap the applied delta
    applied = max(-capped_total, min(capped_total, net_delta))
    summary["total_score_delta"]  = net_delta
    summary["applied_score_delta"] = applied

    if applied != 0:
        try:
            overall = report.setdefault("overall", {})
            score = int(overall.get("score") or 0)
            new_score = max(30, min(100, score + applied))
            overall["score_before_vision"] = score
            overall["score"] = new_score
            overall["vision_adjusted"] = True
        except Exception as exc:
            summary["errors"].append(f"score_apply_failed: {exc}")

    report["vision_room_findings"] = summary
    return summary
