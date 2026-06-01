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

import hashlib
import os
import re
import threading
import time
from collections import OrderedDict
from typing import Any, Optional, Tuple

# Vision layout cache keyed by upload fingerprint + mode (preview|full).
_VISION_LAYOUT_CACHE: OrderedDict[str, Tuple[float, dict]] = OrderedDict()
_VISION_CACHE_LOCK = threading.Lock()
_VISION_CACHE_MAX = int(os.environ.get("ASTROVASTU_VISION_CACHE_MAX", "200"))
_VISION_CACHE_TTL = int(os.environ.get("ASTROVASTU_VISION_CACHE_TTL_SEC", "1800"))

# Rejected uploads — same file retry = no second Vision bill (30 min).
_NEGATIVE_CACHE: OrderedDict[str, Tuple[float, str, str]] = OrderedDict()
_NEGATIVE_CACHE_MAX = 400

# Per-user preview attempts (stops 8–9 random files burning tokens).
_PREVIEW_RATE: dict[str, list[float]] = {}
_PREVIEW_RATE_LOCK = threading.Lock()


def _vision_cache_enabled() -> bool:
    return os.environ.get("ASTROVASTU_VISION_CACHE_DISABLE", "").strip().lower() not in (
        "1", "true", "yes",
    )


def _upload_fingerprint(upload_payload: dict, business_type: str | None) -> str:
    from floor_plan_loader import decode_upload_raw_bytes
    raw = decode_upload_raw_bytes(upload_payload)
    north = ((upload_payload.get("north_at") if isinstance(upload_payload, dict) else None) or "top")
    north = str(north).strip().lower()
    biz = (business_type or "residential").strip().lower()
    return hashlib.sha256(raw + b"|" + north.encode() + b"|" + biz.encode()).hexdigest()


def _vision_cache_key(fingerprint: str, mode: str) -> str:
    return f"{fingerprint}:{mode}"


def _reuse_preview_on_scan_enabled() -> bool:
    return os.environ.get("ASTROVASTU_REUSE_PREVIEW_VISION", "1").strip().lower() not in (
        "0", "false", "no",
    )


def _preview_vision_detail() -> str:
    return os.environ.get("OPENAI_VISION_PREVIEW_DETAIL", "auto").strip().lower() or "auto"


def _preview_retry_high_enabled() -> bool:
    return os.environ.get("ASTROVASTU_PREVIEW_RETRY_HIGH", "1").strip().lower() not in (
        "0", "false", "no",
    )


def _full_vision_detail() -> str:
    return os.environ.get("OPENAI_VISION_DETAIL", "high").strip().lower() or "high"


def _preview_reuse_min_confidence() -> int:
    try:
        return max(0, min(100, int(os.environ.get("ASTROVASTU_PREVIEW_REUSE_MIN_CONF", "50"))))
    except ValueError:
        return 50


def _negative_cache_get(fingerprint: str) -> Optional[Tuple[str, str]]:
    now = time.time()
    with _VISION_CACHE_LOCK:
        entry = _NEGATIVE_CACHE.get(fingerprint)
        if not entry:
            return None
        expires, msg, code = entry
        if expires < now:
            _NEGATIVE_CACHE.pop(fingerprint, None)
            return None
        _NEGATIVE_CACHE.move_to_end(fingerprint)
        return msg, code


def _negative_cache_put(fingerprint: str, message: str, code: str) -> None:
    with _VISION_CACHE_LOCK:
        _NEGATIVE_CACHE[fingerprint] = (
            time.time() + _VISION_CACHE_TTL,
            message,
            code or "invalid_floor_plan",
        )
        _NEGATIVE_CACHE.move_to_end(fingerprint)
        while len(_NEGATIVE_CACHE) > _NEGATIVE_CACHE_MAX:
            _NEGATIVE_CACHE.popitem(last=False)


def _negative_cache_clear(fingerprint: str) -> None:
    with _VISION_CACHE_LOCK:
        _NEGATIVE_CACHE.pop(fingerprint, None)


def check_floor_plan_preview_rate(user_id: int, lang: str = "en") -> Tuple[bool, str]:
    """Return (allowed, user_message). Caps cheap preview Vision calls per hour."""
    try:
        max_n = max(3, int(os.environ.get("ASTROVASTU_PREVIEW_RATE_PER_HOUR", "12")))
    except ValueError:
        max_n = 12
    window = 3600.0
    key = str(user_id)
    now = time.time()
    with _PREVIEW_RATE_LOCK:
        hits = [t for t in _PREVIEW_RATE.get(key, []) if now - t < window]
        if len(hits) >= max_n:
            if (lang or "en").strip().lower() in ("hi", "hn"):
                return False, (
                    "Bahut baar preview try ho chuka hai. 1 ghante baad dubara koshish karein, "
                    "ya ek hi sahi top-down floor plan upload karein."
                )
            return False, (
                "Too many floor-plan preview attempts. Please wait an hour, "
                "or upload one clear top-down plan instead of many random files."
            )
        hits.append(now)
        _PREVIEW_RATE[key] = hits[-max_n:]
    return True, ""


def _usable_preview_for_full_scan(raw: dict) -> bool:
    if not isinstance(raw, dict) or raw.get("scan_inconclusive"):
        return False
    rooms = raw.get("rooms") or []
    n = 0
    for r in rooms:
        if isinstance(r, dict) and (r.get("room_type") or "").strip() and (r.get("direction") or "").strip():
            n += 1
    return n >= 1 and int(raw.get("confidence") or 0) >= _preview_reuse_min_confidence()


def _vision_cache_get(key: str) -> Optional[dict]:
    now = time.time()
    with _VISION_CACHE_LOCK:
        entry = _VISION_LAYOUT_CACHE.get(key)
        if not entry:
            return None
        expires, raw = entry
        if expires < now:
            _VISION_LAYOUT_CACHE.pop(key, None)
            return None
        _VISION_LAYOUT_CACHE.move_to_end(key)
        return dict(raw)


def _vision_cache_put(key: str, raw: dict) -> None:
    with _VISION_CACHE_LOCK:
        _VISION_LAYOUT_CACHE[key] = (time.time() + _VISION_CACHE_TTL, dict(raw))
        _VISION_LAYOUT_CACHE.move_to_end(key)
        while len(_VISION_LAYOUT_CACHE) > _VISION_CACHE_MAX:
            _VISION_LAYOUT_CACHE.popitem(last=False)

# Canonical direction tokens accepted by the deterministic engines
_VALID_DIRS = {"N", "NE", "E", "SE", "S", "SW", "W", "NW", "center"}

_DIR_ALIASES = {
    "n": "N", "north": "N",
    "ne": "NE", "north-east": "NE", "northeast": "NE", "north east": "NE",
    "e": "E", "east": "E",
    "se": "SE", "south-east": "SE", "southeast": "SE", "south east": "SE",
    "s": "S", "south": "S",
    "sw": "SW", "south-west": "SW", "southwest": "SW", "south west": "SW",
    "w": "W", "west": "W",
    "nw": "NW", "north-west": "NW", "northwest": "NW", "north west": "NW",
    "center": "center", "centre": "center", "middle": "center", "brahmasthan": "center",
}

# Labels on architect / 3D renders → engine room keys
_FLOOR_PLAN_ROOM_ALIASES: dict[str, str] = {
    "bedroom-1": "bedroom", "bedroom_1": "bedroom", "bedroom-2": "bedroom",
    "bedroom1": "bedroom", "bedroom2": "bedroom",
    "master_bedroom": "bedroom", "master bedroom": "bedroom", "mbr": "bedroom",
    "guest_room": "bedroom", "guest room": "bedroom", "guest": "bedroom",
    "kids_room": "bedroom", "children_room": "bedroom",
    "living_room": "living", "living room": "living", "lounge": "living",
    "dining_area": "dining", "dining room": "dining", "dining_room": "dining",
    "kitchen": "kitchen",
    "puja_room": "pooja", "puja room": "pooja", "puja": "pooja", "pooja_room": "pooja",
    "pooja room": "pooja", "prayer": "pooja", "mandir": "pooja",
    "toilet": "bathroom", "wc": "bathroom", "washroom": "bathroom", "bath": "bathroom",
    "bathroom": "bathroom",
    "study_room": "study", "study room": "study", "office_room": "study",
    "foyer": "main_door", "verandah": "main_door", "veranda": "main_door",
    "entrance": "main_door", "main_entrance": "main_door", "main door": "main_door",
    "main_door": "main_door",
    "stair": "staircase", "stairs": "staircase", "staircase": "staircase",
    "store_room": "store", "store": "store", "storage": "store",
    "balcony": "balcony",
    "patio": "living", "courtyard": "living", "deck": "living",
    "drawing_room": "living", "drawing": "living", "family_room": "living",
    "sitting_room": "living", "sitting": "living", "hall": "living",
    "great_room": "living", "family": "living",
    "porch": "main_door", "front_porch": "main_door", "portico": "main_door",
    "lobby": "main_door", "entry_hall": "main_door",
    "ensuite": "bathroom", "en_suite": "bathroom", "attached_bath": "bathroom",
    "powder_room": "bathroom", "half_bath": "bathroom",
    "living_dining": "living", "living/dining": "living", "open_plan": "living",
    "bedroom_1": "bedroom", "bedroom_2": "bedroom", "bedroom-3": "bedroom",
    "toilet_1": "bathroom", "toilet_2": "bathroom", "bath_room": "bathroom",
    "rear_terrace": "balcony", "front_porch": "main_door",
}

# Devanagari labels on Indian architect sheets → engine keys
_HINDI_ROOM_MAP: dict[str, str] = {
    "बैठक": "living", "हॉल": "living", "लिविंग": "living",
    "शयनकक्ष": "bedroom", "शयन": "bedroom", "बेडरूम": "bedroom",
    "रसोई": "kitchen", "किचन": "kitchen",
    "स्नानघर": "bathroom", "बाथरूम": "bathroom", "शौचालय": "bathroom",
    "पूजा": "pooja", "पूजाघर": "pooja", "मंदिर": "pooja",
    "भोजन": "dining", "डाइनिंग": "dining",
    "सीढ़ी": "staircase", "सीढी": "staircase",
}

_SKIP_ROOM_TYPES = frozenset({
    "parking", "garage", "car_park", "driveway", "garden", "lawn",
    "landscape", "landscaping", "open_area", "terrace", "sitout",
    "hallway", "passage", "corridor", "circulation",
    "utility", "utility_room", "laundry", "mechanical", "closet",
    "walk_in_closet", "wic", "pantry", "store", "store_room", "storage",
    "servant", "maid", "maids", "boiler", "plant_room",
})

_COMPASS_ORDER = ("N", "NE", "E", "SE", "S", "SW", "W", "NW")

_PLAN_NORTH_VALID = frozenset({
    "top", "top-right", "right", "bottom-right",
    "bottom", "bottom-left", "left", "top-left", "none",
})


def _suggest_user_north_at(plan_north: str | None) -> str | None:
    """Map vision-detected north arrow edge → UI north_at picker value."""
    p = (plan_north or "").strip().lower()
    if p in _PLAN_NORTH_VALID and p != "none":
        return p
    return None


def _inject_main_door_room(
    engine_rooms: list[dict],
    full_rooms: list[dict],
    main_ent: str,
) -> tuple[list[dict], list[dict]]:
    """Ensure main entrance from plan arrow appears in room list."""
    d = _norm_direction_short(main_ent)
    if not d or d not in _VALID_DIRS:
        return engine_rooms, full_rooms
    if any(r.get("room_type") == "main_door" for r in engine_rooms):
        return engine_rooms, full_rooms
    engine_rooms = list(engine_rooms) + [{"room_type": "main_door", "direction": d}]
    full_rooms = list(full_rooms) + [{
        "room_type": "main_door",
        "direction": d,
        "position_grid": "",
        "notes": "Main entrance (from plan)",
    }]
    return engine_rooms, full_rooms


def _finalize_engine_rooms(
    engine_rooms: list[dict],
    full_rooms: list[dict],
    raw: dict,
) -> tuple[list[dict], list[dict]]:
    """
    Dedupe, cap count, drop duplicate mis-read stores, prefer core Vastu rooms.
    """
    main_ent = (raw.get("main_entrance_direction") or "").strip()
    engine_rooms, full_rooms = _inject_main_door_room(engine_rooms, full_rooms, main_ent)

    core_priority = {
        "main_door": 0, "kitchen": 1, "pooja": 2, "bedroom": 3, "bathroom": 4,
        "living": 5, "dining": 6, "study": 7, "staircase": 8, "balcony": 9, "store": 10,
    }

    seen: set[tuple[str, str]] = set()
    paired: list[tuple[dict, dict, int]] = []
    for er, fr in zip(engine_rooms, full_rooms):
        key = (er.get("room_type"), er.get("direction"))
        if key in seen:
            continue
        seen.add(key)
        pri = core_priority.get(er.get("room_type") or "", 50)
        paired.append((er, fr, pri))

    store_n = sum(1 for er, _, _ in paired if er.get("room_type") == "store")
    if store_n > 1:
        paired = [(er, fr, p) for er, fr, p in paired if er.get("room_type") != "store"]

    paired.sort(key=lambda x: (x[2], x[0].get("room_type", "")))
    paired = paired[:12]
    return (
        [p[0] for p in paired],
        [p[1] for p in paired],
    )


def _norm_direction_short(d: str) -> str:
    """Map any direction string to N/NE/... or ''."""
    t = (d or "").strip()
    if not t:
        return ""
    if t in _VALID_DIRS:
        return t
    low = t.lower().replace("_", " ")
    for long, short in [
        ("north-east", "NE"), ("north east", "NE"),
        ("south-east", "SE"), ("south east", "SE"),
        ("south-west", "SW"), ("south west", "SW"),
        ("north-west", "NW"), ("north west", "NW"),
        ("north", "N"), ("east", "E"), ("south", "S"), ("west", "W"),
        ("center", "center"), ("centre", "center"),
    ]:
        if low == long or low == long.replace(" ", "-"):
            return short
    return _DIR_ALIASES.get(low.replace(" ", "-"), _DIR_ALIASES.get(low, ""))


def _normalize_floor_plan_room_type(room_type: str) -> str:
    raw = (room_type or "").strip()
    if raw in _HINDI_ROOM_MAP:
        return _HINDI_ROOM_MAP[raw]
    rt = raw.lower().replace(" ", "_")
    while "__" in rt:
        rt = rt.replace("__", "_")
    rt = rt.strip("_")
    if not rt or rt in _SKIP_ROOM_TYPES:
        return ""
    if rt in _FLOOR_PLAN_ROOM_ALIASES:
        return _FLOOR_PLAN_ROOM_ALIASES[rt]
    rt_sp = rt.replace("_", " ")
    if rt_sp in _FLOOR_PLAN_ROOM_ALIASES:
        return _FLOOR_PLAN_ROOM_ALIASES[rt_sp]
    m = re.match(r"^(bedroom|kitchen|bathroom|toilet|pooja|puja)(?:[-_]?)(\d+)$", rt)
    if m:
        return _FLOOR_PLAN_ROOM_ALIASES.get(m.group(1), m.group(1))
    return rt


def normalize_floor_plan_entries(rooms: list) -> list[dict]:
    """Normalize client or vision room list → [{room_type, direction}, ...]."""
    out: list[dict] = []
    seen: set[tuple[str, str]] = set()
    for r in rooms or []:
        if not isinstance(r, dict):
            continue
        rt = _normalize_floor_plan_room_type(r.get("room_type") or "")
        d = _norm_direction_short(r.get("direction") or "")
        if not rt or not d or d not in _VALID_DIRS:
            continue
        key = (rt, d)
        if key in seen:
            continue
        seen.add(key)
        out.append({"room_type": rt, "direction": d})
        if len(out) >= 12:
            break
    return out

# Server-side guards
_MAX_PHOTO_BYTES        = 8 * 1024 * 1024   # 8 MB raw decoded image per photo
_MAX_ROOM_PHOTOS        = 6
_ALLOWED_IMAGE_PREFIXES = ("data:image/jpeg", "data:image/jpg",
                           "data:image/png",  "data:image/webp")

# Brand-safe error message returned to users (never expose AI / OpenAI)
_BRAND_ERR_DEFAULT = "Photo Engine could not read this upload. Please try a clearer image or PDF."


# Room tokens Photo Engine uses — used to guess home vs commercial layout.
_RESIDENTIAL_ROOM_HINTS = (
    "bedroom", "master_bedroom", "kitchen", "pooja", "living", "dining",
    "bathroom", "toilet", "balcony", "guest", "wardrobe", "study",
    "store_room", "entrance", "hall", "drawing",
)
_SHOP_ROOM_HINTS = (
    "shop", "showroom", "billing", "cash_counter", "counter", "display",
    "retail", "showroom", "cash", "billing_counter",
)
_OFFICE_ROOM_HINTS = (
    "reception", "cabin", "conference", "workstation", "office", "meeting",
    "boardroom", "staff", "pantry", "server_room",
)
_FACTORY_ROOM_HINTS = (
    "factory", "warehouse", "godown", "machine", "raw_material",
    "finished_goods", "production", "loading", "plant", "assembly",
)


def _infer_plan_kind_detailed(room_types: list[str]) -> str:
    """Return home | shop | office | factory | unclear from detected rooms."""
    home = shop = office = factory = 0
    for rt in room_types:
        rt = (rt or "").strip().lower().replace(" ", "_")
        if not rt:
            continue
        if any(h in rt for h in _RESIDENTIAL_ROOM_HINTS):
            home += 1
        if any(h in rt for h in _SHOP_ROOM_HINTS):
            shop += 1
        if any(h in rt for h in _OFFICE_ROOM_HINTS):
            office += 1
        if any(h in rt for h in _FACTORY_ROOM_HINTS):
            factory += 1

    commercial = {"shop": shop, "office": office, "factory": factory}
    best_com = max(commercial, key=commercial.get)

    if home >= 2 and shop + office + factory == 0:
        return "home"
    if commercial[best_com] >= 2 and home == 0:
        return best_com
    if home >= max(commercial.values()) + 2:
        return "home"
    if max(commercial.values()) >= home + 2 and commercial[best_com] >= 2:
        return best_com
    return "unclear"


def _normalize_user_plan_kind(kind: str | None) -> str | None:
    k = (kind or "").strip().lower()
    if k in ("home", "residential", "house"):
        return "home"
    if k in ("shop", "office", "factory"):
        return k
    return None


def _plan_kind_label(kind: str, lang: str) -> str:
    k = (kind or "").strip().lower()
    labels_en = {
        "home": "Home", "shop": "Shop", "office": "Office", "factory": "Factory",
        "unclear": "Unknown",
    }
    labels_hi = {
        "home": "Ghar", "shop": "Dukaan", "office": "Office", "factory": "Factory",
        "unclear": "Unclear",
    }
    if lang in ("hi", "hn"):
        return labels_hi.get(k, k)
    return labels_en.get(k, k.title())


def _plan_kind_mismatch_message(
    lang: str, selected: str, detected: str,
) -> str:
    sel = _plan_kind_label(selected, lang)
    det = _plan_kind_label(detected, lang)
    if lang in ("hi", "hn"):
        return (
            f"Aapne «{sel}» chuna hai, lekin floor plan «{det}» jaisa lagta hai. "
            f"Neeche sahi type chunein aur dubara «Run Whole-Floor Vastu Scan» dabayein."
        )
    return (
        f"You selected «{sel}», but this floor plan looks like a «{det}» layout. "
        f"Please pick the matching type below and run the scan again."
    )


def _check_plan_kind_mismatch(
    user_plan_kind: str | None,
    detected: str,
    lang: str = "en",
) -> tuple[str | None, str | None]:
    """Return (message, error_code) when user's choice conflicts with detected layout."""
    expected = _normalize_user_plan_kind(user_plan_kind)
    if not expected or not detected or detected == "unclear":
        return None, None
    if expected == detected:
        return None, None
    return _plan_kind_mismatch_message(lang, expected, detected), "plan_kind_mismatch"


def _vision_business_type(plan_kind: str | None) -> str | None:
    k = (plan_kind or "").strip().lower()
    if k in ("shop", "office", "factory"):
        return k
    return None


def _build_engine_rooms_from_raw(raw: dict) -> tuple[list[dict], list[dict], int]:
    """Parse vision JSON → engine rooms, full rooms, raw room count before filtering."""
    rooms_full = raw.get("rooms") or []
    engine_rooms: list[dict] = []
    full_rooms: list[dict] = []
    raw_n = 0
    for r in rooms_full:
        if not isinstance(r, dict):
            continue
        raw_n += 1
        rt = _normalize_floor_plan_room_type(r.get("room_type") or "")
        d = _norm_direction_short(r.get("direction") or "")
        if not rt or not d or d not in _VALID_DIRS:
            continue
        engine_rooms.append({"room_type": rt, "direction": d})
        full_rooms.append({
            "room_type": rt,
            "direction": d,
            "position_grid": (r.get("position_grid") or "").strip(),
            "notes": (r.get("notes") or "").strip(),
        })
    return engine_rooms, full_rooms, raw_n


def _should_preview_retry_high(raw: dict, engine_count: int, detail: str) -> bool:
    if not _preview_retry_high_enabled():
        return False
    if detail == "high":
        return False
    if raw.get("scan_inconclusive"):
        return True
    if engine_count < 2:
        return True
    if int(raw.get("confidence") or 0) < 45:
        return True
    return False


def _invalid_floor_plan_message(lang: str) -> str:
    """User-facing message when upload is not a house/building floor plan."""
    l = (lang or "en").strip().lower()
    if l in ("hi", "hn"):
        return (
            "Yeh photo sahi ghar ka floor plan nahi lag rahi. "
            "Kripaya sirf apne ghar ka top-down floor plan upload karein "
            "(architect ka naksha, PDF ya clear layout image) — selfie, room photo "
            "ya koi aur photo nahi."
        )
    if l == "en":
        return (
            "This photo is not a valid house floor plan. "
            "Please upload only your home's top-down floor plan "
            "(architect drawing, PDF, or a clear layout image) — not selfies, "
            "room photos, or other pictures."
        )
    return (
        "This photo is not a valid house floor plan. "
        "Please upload only your home's top-down floor plan "
        "(architect drawing, PDF, or a clear layout image)."
    )


def _floor_plan_read_failed_message(lang: str, *, had_raw_rooms: bool) -> str:
    """Plan looks like a layout but rooms/directions could not be mapped."""
    l = (lang or "en").strip().lower()
    if had_raw_rooms:
        if l in ("hi", "hn"):
            return (
                "Floor plan dikhai de raha hai, lekin kamre/disha sahi map nahi ho paye. "
                "North direction sahi chunein aur dubara Run Scan karein — "
                "architect CAD / bilingual naksha supported hai."
            )
        return (
            "We can see a floor plan but could not map rooms to directions. "
            "Confirm North direction and run the scan again — architect CAD and "
            "bilingual plans are supported."
        )
    return _invalid_floor_plan_message(lang)


def _vision_user_error(internal_reason: str, lang: str = "en") -> Tuple[str, str]:
    """
    Map internal vision failures → (user_message, error_code).
    Connection / missing API key → vision_unavailable (not user's floor plan).
    """
    low = (internal_reason or "").lower()
    l = (lang or "en").strip().lower()
    hi = l in ("hi", "hn")

    if (
        "connection error" in low
        or "connecttimeout" in low
        or "connection refused" in low
        or "name or service not known" in low
        or "failed to establish" in low
        or "timed out" in low
        or "timeout" in low
    ):
        if hi:
            return (
                "Photo Engine ab server se connect nahi ho pa raha. "
                "Internet check karein. Local test par artifacts/api-server/.env mein "
                "OPENAI_API_KEY set karein, phir server restart karein.",
                "vision_unavailable",
            )
        return (
            "Photo Engine cannot reach the analysis service (connection error). "
            "Check your internet. For local dev, set OPENAI_API_KEY in "
            "artifacts/api-server/.env and restart the server.",
            "vision_unavailable",
        )

    if (
        "not configured" in low
        or "missing" in low and "openai" in low
        or "api_key" in low
        or "vision_unavailable" in low
    ):
        if hi:
            return (
                "Photo Engine configure nahi hai. Server par OPENAI_API_KEY set karein "
                "(ya cloud vision integration), phir dubara try karein.",
                "vision_unavailable",
            )
        return (
            "Photo Engine is not configured. Set OPENAI_API_KEY on the server "
            "(or cloud vision integration), then try again.",
            "vision_unavailable",
        )

    if "floor_plan_decode_failed" in low:
        if hi:
            return (
                "Floor plan file read nahi ho payi. Chhota/clear PNG ya PDF dubara upload karein.",
                "invalid_floor_plan",
            )
        return (
            "Could not read the floor plan file. Try a smaller or clearer PNG/PDF.",
            "invalid_floor_plan",
        )

    return (
        _invalid_floor_plan_message(lang)
        if "invalid" in low or "inconclusive" in low
        else _BRAND_ERR_DEFAULT,
        "invalid_floor_plan",
    )


def _brand_safe_error(internal_reason: str, lang: str = "en") -> str:
    """Legacy wrapper — message only."""
    return _vision_user_error(internal_reason, lang)[0]


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
    user_plan_kind: str | None = None,
    preview_mode: bool = False,
) -> tuple[dict, str | None, str | None]:
    """
    upload_payload: {"type":"image"|"pdf","data_url"?|"base64"?:str}
    preview_mode: True → 1024px + low Vision detail (cheap reject path).

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
        msg, code = _vision_user_error(f"vision_unavailable: {exc}", lang)
        return {}, msg, code

    fingerprint = _upload_fingerprint(upload_payload, business_type)
    if isinstance(upload_payload, dict) and upload_payload.get("force_refresh"):
        _negative_cache_clear(fingerprint)
    neg = _negative_cache_get(fingerprint)
    if neg:
        print(f"[vision_layer] negative cache HIT fp={fingerprint[:12]}…")
        return {}, neg[0], neg[1]

    mode = "preview" if preview_mode else "full"
    cache_key = _vision_cache_key(fingerprint, mode)
    raw: dict | None = None
    if _vision_cache_enabled():
        raw = _vision_cache_get(cache_key)

    if raw is None and not preview_mode and _reuse_preview_on_scan_enabled():
        prev_key = _vision_cache_key(fingerprint, "preview")
        prev = _vision_cache_get(prev_key) if _vision_cache_enabled() else None
        if prev and _usable_preview_for_full_scan(prev):
            raw = prev
            print(f"[vision_layer] reuse preview vision for scan fp={fingerprint[:12]}…")

    if raw is None:
        try:
            png_data_url = to_image_data_url(upload_payload, preview=preview_mode)
        except Exception as exc:
            print(f"[vision_layer] floor_plan_decode_failed: {exc}")
            return {}, _brand_safe_error(f"floor_plan_decode_failed: {exc}"), "invalid_floor_plan"

        detail = _preview_vision_detail() if preview_mode else _full_vision_detail()
        try:
            raw = extract_floor_plan_layout(
                png_data_url,
                business_type=business_type,
                lang=lang,
                north_at=(upload_payload.get("north_at") if isinstance(upload_payload, dict) else None),
                vision_detail=detail,
            )
        except Exception as exc:
            print(f"[vision_layer] vision_extract_failed: {exc}")
            return {}, _brand_safe_error(f"vision_extract_failed: {exc}"), "invalid_floor_plan"

        engine_rooms, _, raw_n = _build_engine_rooms_from_raw(raw)
        if preview_mode and _should_preview_retry_high(raw, len(engine_rooms), detail):
            print(
                f"[vision_layer] preview retry high detail "
                f"(rooms={len(engine_rooms)} raw={raw_n} conf={int(raw.get('confidence') or 0)})"
            )
            try:
                png_hi = to_image_data_url(upload_payload, preview=False)
                raw_hi = extract_floor_plan_layout(
                    png_hi,
                    business_type=business_type,
                    lang=lang,
                    north_at=(
                        upload_payload.get("north_at")
                        if isinstance(upload_payload, dict) else None
                    ),
                    vision_detail="high",
                )
                er_hi, _, raw_n_hi = _build_engine_rooms_from_raw(raw_hi)
                use_hi = (
                    len(er_hi) > len(engine_rooms)
                    or (
                        not raw_hi.get("scan_inconclusive")
                        and raw.get("scan_inconclusive")
                    )
                    or int(raw_hi.get("confidence") or 0) > int(raw.get("confidence") or 0) + 10
                )
                if use_hi:
                    raw = raw_hi
                    detail = "high(retry)"
                    print(
                        f"[vision_layer] preview retry OK rooms={len(er_hi)} "
                        f"conf={int(raw.get('confidence') or 0)}"
                    )
            except Exception as exc:
                print(f"[vision_layer] preview retry failed: {exc}")

        if _vision_cache_enabled() and isinstance(raw, dict):
            _vision_cache_put(cache_key, raw)
            print(f"[vision_layer] vision cache STORE {mode} key={cache_key[:20]}… detail={detail}")
    else:
        print(f"[vision_layer] vision cache HIT {mode} key={cache_key[:20]}…")

    engine_rooms, full_rooms, raw_n = _build_engine_rooms_from_raw(raw)

    if raw.get("scan_inconclusive"):
        reason = (raw.get("inconclusive_reason") or "").strip()
        msg = reason if reason else _invalid_floor_plan_message(lang)
        print(f"[vision_layer] floor_plan rejected (inconclusive): {reason[:120]}")
        _negative_cache_put(fingerprint, msg, "invalid_floor_plan")
        return {}, msg, "invalid_floor_plan"

    if not engine_rooms:
        print(
            "[vision_layer] floor_plan rejected: no rooms detected "
            f"(confidence={int(raw.get('confidence') or 0)} raw_rooms={raw_n})"
        )
        msg = _floor_plan_read_failed_message(lang, had_raw_rooms=raw_n > 0)
        _negative_cache_put(fingerprint, msg, "invalid_floor_plan")
        return {}, msg, "invalid_floor_plan"

    engine_rooms, full_rooms = _finalize_engine_rooms(engine_rooms, full_rooms, raw)
    plan_north = (raw.get("plan_north_points_to") or "none").strip().lower()
    suggested_north = _suggest_user_north_at(plan_north)

    _negative_cache_clear(fingerprint)

    detected = _infer_plan_kind_detailed([r["room_type"] for r in engine_rooms])
    mismatch_msg, mismatch_code = _check_plan_kind_mismatch(
        user_plan_kind or upload_payload.get("plan_kind"),
        detected,
        lang,
    )
    if mismatch_msg:
        print(
            f"[vision_layer] plan_kind mismatch: user={user_plan_kind} "
            f"detected={detected} rooms={[r['room_type'] for r in engine_rooms[:8]]}"
        )
        _negative_cache_put(fingerprint, mismatch_msg, mismatch_code or "plan_kind_mismatch")
        return {}, mismatch_msg, mismatch_code

    return ({
        "rooms":              engine_rooms,
        "rooms_full":         full_rooms,
        "structural_notes":   list(raw.get("structural_notes") or [])[:10],
        "plot_shape":         (raw.get("plot_shape") or "").strip(),
        "main_entrance":      (raw.get("main_entrance_direction") or "").strip(),
        "plan_north_points_to": plan_north,
        "suggested_north_at": suggested_north,
        "upload_filename":    (
            (upload_payload.get("filename") if isinstance(upload_payload, dict) else None)
            or ""
        ).strip(),
        "confidence":         int(raw.get("confidence") or 0),
        "scan_inconclusive":  bool(raw.get("scan_inconclusive")),
        "inconclusive_reason":(raw.get("inconclusive_reason") or "").strip(),
        "detected_plan_kind": detected if detected != "unclear" else None,
    }, None, None)


_DETECTED_ROOM_TO_ENGINE: dict[str, str] = {
    "kitchen": "kitchen",
    "bedroom": "bedroom",
    "master_bedroom": "bedroom",
    "bathroom": "bathroom",
    "toilet": "bathroom",
    "washroom": "bathroom",
    "pooja": "pooja",
    "pooja_room": "pooja",
    "living": "living",
    "livingroom": "living",
    "living_room": "living",
    "hall": "living",
    "study": "study",
    "office": "study",
    "cabin": "study",
    "entrance": "entrance",
    "main_door": "entrance",
    "foyer": "entrance",
    "store": "store",
    "storeroom": "store",
    "shop": "store",
    "office": "study",
    "cabin": "study",
    "conference": "study",
    "reception": "entrance",
}

_NON_ROOM_DETECTED = frozenset({
    "floor_plan", "floorplan", "blueprint", "site_plan", "architectural_plan",
    "layout", "diagram", "map", "document", "screenshot", "selfie", "person",
    "food", "outdoor", "garden", "terrace", "street", "vehicle", "unclear",
    "unknown", "other", "factory", "warehouse",
})


def _not_a_room_photo_message(lang: str, kind: str = "generic") -> str:
    l = (lang or "en").strip().lower()
    if kind == "floor_plan":
        if l in ("hi", "hn"):
            return (
                "Yeh floor plan / naksha lag rahi hai. Upload Photo sirf ek kamre ki "
                "andar ki photo ke liye hai (bedroom, bathroom, kitchen, office cabin). "
                "Poora plan ke liye «Full Plan» use karein."
            )
        return (
            "This looks like a floor plan, not a single room. Upload Photo is only "
            "for interior room pictures (bedroom, bathroom, kitchen, office cabin). "
            "Use «Full Plan» for architect PDFs."
        )
    if kind == "outdoor":
        if l in ("hi", "hn"):
            return (
                "Yeh kamre ki andar ki photo nahi lag rahi. Sirf bedroom, bathroom, "
                "kitchen, office jaise ek room ki clear photo upload karein."
            )
        return (
            "This does not look like an indoor room photo. Upload a clear picture "
            "of one room only (bedroom, bathroom, kitchen, office, etc.)."
        )
    if l in ("hi", "hn"):
        return (
            "Sirf ek room ki andar ki photo chahiye (jaise bathroom, bedroom, kitchen, "
            "office). Floor plan, selfie ya bahar ki photo nahi."
        )
    return (
        "Please upload one interior room photo only (e.g. bathroom, bedroom, "
        "kitchen, office). Not floor plans, selfies, or outdoor shots."
    )


def _reject_non_room_photo(
    detected_raw: str,
    *,
    inconclusive: bool,
    suggested: str | None,
    inconclusive_reason: str,
    lang: str,
) -> tuple[bool, str, str]:
    """Return (reject, error_code, user_message)."""
    d = (detected_raw or "").strip().lower().replace(" ", "_")
    if d in _NON_ROOM_DETECTED:
        kind = "floor_plan" if "plan" in d or d in ("blueprint", "layout", "diagram", "map") else "outdoor"
        if d in ("floor_plan", "floorplan", "blueprint", "site_plan", "architectural_plan", "layout", "diagram", "map"):
            kind = "floor_plan"
        return True, "not_a_room_photo", _not_a_room_photo_message(lang, kind)
    if any(tok in d for tok in ("floor_plan", "floorplan", "blueprint", "naksha", "site_plan")):
        return True, "not_a_room_photo", _not_a_room_photo_message(lang, "floor_plan")
    if "floor" in d and "plan" in d:
        return True, "not_a_room_photo", _not_a_room_photo_message(lang, "floor_plan")
    if inconclusive and not suggested:
        msg = (inconclusive_reason or "").strip() or _not_a_room_photo_message(lang, "generic")
        return True, "not_a_room_photo", msg
    if not suggested and d and d not in _DETECTED_ROOM_TO_ENGINE.values():
        return True, "not_a_room_photo", _not_a_room_photo_message(lang, "generic")
    return False, "", ""


def _upload_to_image_data_url(upload_payload: dict) -> str:
    img = (
        (upload_payload.get("data_url") or upload_payload.get("image_data_url") or "")
        .strip()
    )
    if img:
        return img
    raw = (upload_payload.get("base64") or "").strip()
    if not raw:
        return ""
    if raw.lower().startswith("data:"):
        return raw
    return f"data:image/jpeg;base64,{raw}"


def _map_detected_room_type(detected: str) -> str | None:
    key = (detected or "").strip().lower().replace(" ", "_")
    if not key or key in ("unclear", "outdoor", "unknown", "other"):
        return None
    return _DETECTED_ROOM_TO_ENGINE.get(key) or (
        key if key in _DETECTED_ROOM_TO_ENGINE.values() else None
    )


def classify_room_photo_upload(upload_payload: dict, lang: str = "en") -> dict:
    """
    Photo Engine: classify a single room photo (kitchen/bedroom/…).
    Never raises — returns {ok, suggested_room_type?, confidence?, …}.
    """
    img = _upload_to_image_data_url(upload_payload or {})
    if not img or not _is_allowed_image_data_url(img):
        msg = _brand_safe_error("invalid room photo")
        return {"ok": False, "error": "invalid_image", "message": msg}

    try:
        from openai_helper import analyze_room_visuals
    except Exception as exc:
        msg, code = _vision_user_error(f"vision_unavailable: {exc}", lang)
        return {"ok": False, "error": code or "vision_unavailable", "message": msg}

    try:
        vf = analyze_room_visuals(img, "living", lang=lang)
    except Exception as exc:
        msg, code = _vision_user_error(str(exc), lang)
        return {"ok": False, "error": code or "classify_failed", "message": msg}

    detected_raw = (vf.get("detected_room_type") or "").strip().lower()
    suggested = _map_detected_room_type(detected_raw)
    conf = int(vf.get("confidence") or 0)
    inconclusive = bool(vf.get("scan_inconclusive"))
    inconclusive_reason = (vf.get("inconclusive_reason") or "").strip()
    features = vf.get("identity_features_seen") or []
    if not isinstance(features, list):
        features = []

    reject, rej_code, rej_msg = _reject_non_room_photo(
        detected_raw,
        inconclusive=inconclusive,
        suggested=suggested,
        inconclusive_reason=inconclusive_reason,
        lang=lang,
    )
    if not reject and not suggested:
        try:
            vd, verr, _ = extract_floor_plan_from_upload(
                {"type": "image", "data_url": img},
                lang=lang,
                preview_mode=True,
            )
            if not verr and len(vd.get("rooms") or []) >= 2:
                reject = True
                rej_code = "not_a_room_photo"
                rej_msg = _not_a_room_photo_message(lang, "floor_plan")
        except Exception:
            pass

    if reject:
        return {
            "ok": False,
            "error": rej_code,
            "message": rej_msg,
            "detected_room_type": detected_raw or None,
            "valid_room_photo": False,
        }

    hint = inconclusive_reason
    if not hint and suggested and not inconclusive:
        if lang in ("hi", "hn"):
            hint = (
                f"Photo Engine ne is photo ko {suggested.replace('_', ' ')} jaisa pehchana — "
                "neeche room aur disha confirm karein."
            )
        else:
            hint = (
                f"Photo Engine suggests this looks like a {suggested.replace('_', ' ')} — "
                "confirm room and direction below."
            )

    return {
        "ok": True,
        "valid_room_photo": True,
        "suggested_room_type": suggested,
        "detected_room_type": detected_raw or None,
        "confidence": conf,
        "scan_inconclusive": inconclusive,
        "features_seen": [str(x) for x in features[:6]],
        "hint": hint or None,
    }


def preview_floor_plan_from_upload(
    upload_payload: dict,
    lang: str = "en",
    user_plan_kind: str | None = None,
) -> dict:
    """
    Lightweight read after client upload (no Vastu engine / quota).
    Returns {ok, rooms_count, detected_plan_kind, confidence, room_types,
    plan_kind_mismatch?, mismatch_message?, error?, message?}.
    """
    vd, verr, verr_code = extract_floor_plan_from_upload(
        upload_payload,
        business_type=_vision_business_type(user_plan_kind),
        lang=lang,
        user_plan_kind=user_plan_kind,
        preview_mode=True,
    )
    if verr:
        return {
            "ok": False,
            "error": verr_code or "invalid_floor_plan",
            "message": verr,
        }
    detected = vd.get("detected_plan_kind") or "unclear"
    mismatch_msg, _ = _check_plan_kind_mismatch(user_plan_kind, detected, lang)
    rooms_out = vd.get("rooms") or []
    return {
        "ok": True,
        "rooms_count": len(rooms_out),
        "rooms": rooms_out,
        "detected_plan_kind": detected,
        "confidence": int(vd.get("confidence") or 0),
        "room_types": [r.get("room_type") for r in rooms_out[:12]],
        "plan_kind_mismatch": bool(mismatch_msg),
        "mismatch_message": mismatch_msg,
        "suggested_north_at": vd.get("suggested_north_at"),
        "plan_north_points_to": vd.get("plan_north_points_to"),
        "main_entrance": vd.get("main_entrance"),
        "structural_notes": (vd.get("structural_notes") or [])[:3],
    }


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
