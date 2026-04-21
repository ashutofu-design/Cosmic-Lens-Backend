"""
Image input pipeline (validate → decode → EXIF → downscale → WB).

Hardening goals:
  • File-size cap (MAX_BYTES)
  • Magic-byte / MIME validation (reject non-image binaries)
  • HEIC/HEIF + animated GIF/WebP first-frame fallback
  • EXIF auto-rotation (iPhone sideways selfies)
  • Auto-downscale to MAX_LONG_EDGE (memory-safe; 12 MP iPhone selfies = 36 MB raw)
  • Optional un-mirror (front-camera selfies are usually horizontally flipped)
"""
from __future__ import annotations

import io
from dataclasses import dataclass

import numpy as np
from PIL import Image, ImageOps, ImageSequence

try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
    _HEIF_OK = True
except Exception:
    _HEIF_OK = False


MAX_BYTES = 12 * 1024 * 1024     # 12 MB hard cap
MAX_LONG_EDGE = 2048             # downscale anything bigger
MIN_LONG_EDGE = 256              # below this, useless

# Magic bytes for accepted image formats
_MAGIC = (
    (b"\xff\xd8\xff",          "jpeg"),
    (b"\x89PNG\r\n\x1a\n",     "png"),
    (b"GIF87a",                "gif"),
    (b"GIF89a",                "gif"),
    (b"RIFF",                  "webp_or_avi"),  # need extra check
    (b"BM",                    "bmp"),
    (b"II*\x00",               "tiff"),
    (b"MM\x00*",               "tiff"),
)


def _detect_format(buf: bytes) -> str | None:
    if len(buf) < 12:
        return None
    for magic, name in _MAGIC:
        if buf.startswith(magic):
            if name == "webp_or_avi":
                if buf[8:12] == b"WEBP":
                    return "webp"
                return None
            return name
    # HEIC: ftyp box at offset 4, brand 'heic' or 'heif' or 'mif1'
    if buf[4:8] == b"ftyp":
        brand = buf[8:12].lower()
        if brand in (b"heic", b"heix", b"hevc", b"heim", b"heis", b"hevm",
                     b"hevs", b"heif", b"mif1", b"msf1"):
            return "heic"
    return None


@dataclass
class DecodedImage:
    rgb: np.ndarray              # HxWx3 uint8 RGB
    width: int
    height: int
    original_width: int
    original_height: int
    format: str
    downscaled: bool
    mirror_applied: bool
    bytes_in: int
    notes: list


def decode_image(image_bytes: bytes,
                 mirror: bool = False,
                 max_long_edge: int = MAX_LONG_EDGE) -> tuple[DecodedImage | None, str | None]:
    """Validate → decode → orient → downscale.

    Returns (decoded, error_str). On success error_str is None.
    """
    notes: list[str] = []
    if not image_bytes:
        return None, "empty_payload"
    if len(image_bytes) > MAX_BYTES:
        return None, f"file_too_large ({len(image_bytes)} > {MAX_BYTES} bytes)"

    fmt = _detect_format(image_bytes)
    if fmt is None:
        return None, "unsupported_or_corrupt_image"
    if fmt == "heic" and not _HEIF_OK:
        return None, "heic_support_unavailable"

    try:
        pil = Image.open(io.BytesIO(image_bytes))
        # Animated GIF / multi-frame WebP → first frame only
        if getattr(pil, "is_animated", False):
            notes.append(f"animated_{fmt}_first_frame_used")
            pil.seek(0)
            pil = next(ImageSequence.Iterator(pil)).copy()
        # EXIF auto-rotation (iPhone "sideways" portrait fix)
        pil = ImageOps.exif_transpose(pil)
        if pil.mode != "RGB":
            pil = pil.convert("RGB")
    except Exception as e:
        return None, f"image_decode_failed: {e}"

    orig_w, orig_h = pil.width, pil.height
    if max(orig_w, orig_h) < MIN_LONG_EDGE:
        return None, f"image_too_small ({orig_w}x{orig_h})"

    # Downscale if needed
    downscaled = False
    if max(orig_w, orig_h) > max_long_edge:
        ratio = max_long_edge / float(max(orig_w, orig_h))
        new_w = int(round(orig_w * ratio))
        new_h = int(round(orig_h * ratio))
        pil = pil.resize((new_w, new_h), Image.LANCZOS)
        downscaled = True
        notes.append(f"downscaled_{orig_w}x{orig_h}_to_{new_w}x{new_h}")

    rgb = np.asarray(pil, dtype=np.uint8)

    # Optional un-mirror (front camera selfies are usually flipped horizontally)
    mirror_applied = False
    if mirror:
        rgb = np.ascontiguousarray(rgb[:, ::-1, :])
        mirror_applied = True
        notes.append("mirror_unflip_applied")

    return DecodedImage(
        rgb=rgb,
        width=rgb.shape[1],
        height=rgb.shape[0],
        original_width=orig_w,
        original_height=orig_h,
        format=fmt,
        downscaled=downscaled,
        mirror_applied=mirror_applied,
        bytes_in=len(image_bytes),
        notes=notes,
    ), None
