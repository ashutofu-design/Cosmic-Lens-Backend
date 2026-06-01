"""
floor_plan_loader.py — Cosmic Lens

Normalizes a user-uploaded floor plan into a single PNG data URL suitable for
the Cosmic Intelligence Engine (vision model input).

Accepts payloads of shape:
  {"type": "image", "data_url": "data:image/jpeg;base64,..."}
  {"type": "image", "base64": "..."}                       (assumes png/jpeg)
  {"type": "pdf",   "base64": "<raw pdf base64>"}          (renders page 1)

Returns:
  data URL string (image/png base64) ready for OpenAI vision.

Hard limits (anti-abuse / cost control):
  - Raw input        : 12 MB
  - Output long-edge : 1600 px (resized via Pillow)
  - PDF page index   : 0 only

Raises ValueError on bad input. Never raises on transient I/O.
"""

from __future__ import annotations

import base64
import io
import re

_MAX_RAW_BYTES = 12 * 1024 * 1024
_MAX_LONG_EDGE = 1600
_PREVIEW_LONG_EDGE = 1280  # preview — enough for CAD labels; full scan uses 1600px
_PDF_RENDER_SCALE = 2.0  # 144 DPI-ish for clarity

# Mapping: where the user said North is on the plan → CCW degrees to rotate so
# that North ends up at the TOP of the image (which is the convention vision
# prompts assume).
_NORTH_AT_ROTATE_CCW = {
    "top":           0,
    "top-right":     315,   # CCW so plan north (top-right) → image top
    "right":         90,
    "bottom-right":  225,
    "bottom":        180,
    "bottom-left":   135,
    "left":          270,
    "top-left":      45,
}


def _strip_data_url(s: str) -> bytes:
    s = s.strip()
    if s.startswith("data:"):
        m = re.match(r"^data:[^;]+;base64,(.+)$", s, flags=re.S)
        if not m:
            raise ValueError("invalid data URL")
        s = m.group(1)
    s = re.sub(r"\s+", "", s)
    try:
        return base64.b64decode(s, validate=False)
    except Exception as exc:
        raise ValueError(f"base64 decode failed: {exc}") from exc


def decode_upload_raw_bytes(payload: dict) -> bytes:
    """Decode floor_plan_upload to raw bytes (before resize). For cache keys."""
    if not isinstance(payload, dict):
        raise ValueError("floor_plan_upload must be an object")
    src = payload.get("data_url") or payload.get("base64") or ""
    if not src:
        raise ValueError("floor_plan_upload requires data_url or base64")
    raw = _strip_data_url(src) if isinstance(src, str) else b""
    if len(raw) > _MAX_RAW_BYTES:
        raise ValueError(
            f"floor_plan_upload too large ({len(raw)} bytes; max {_MAX_RAW_BYTES})"
        )
    return raw


def _bytes_to_png_data_url(
    raw: bytes,
    rotate_ccw_deg: int = 0,
    max_long_edge: int = _MAX_LONG_EDGE,
) -> str:
    if not raw:
        raise ValueError("empty image bytes")
    try:
        from PIL import Image
    except Exception as exc:
        raise ValueError(f"Pillow not installed: {exc}") from exc
    try:
        img = Image.open(io.BytesIO(raw))
        img.load()
    except Exception as exc:
        raise ValueError(f"image decode failed: {exc}") from exc

    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGB")

    # Rotate first (so resize cap applies post-rotation). PIL.rotate is CCW.
    rot = int(rotate_ccw_deg) % 360
    if rot in (90, 180, 270):
        img = img.rotate(rot, expand=True)

    w, h = img.size
    cap = max(512, int(max_long_edge or _MAX_LONG_EDGE))
    long_edge = max(w, h)
    if long_edge > cap:
        scale = cap / float(long_edge)
        new_size = (max(1, int(w * scale)), max(1, int(h * scale)))
        img = img.resize(new_size, Image.LANCZOS)

    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    out_b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/png;base64,{out_b64}"


def _pdf_first_page_to_png_bytes(raw: bytes) -> bytes:
    try:
        import pypdfium2 as pdfium
    except Exception as exc:
        raise ValueError(f"pypdfium2 not installed: {exc}") from exc
    try:
        pdf = pdfium.PdfDocument(raw)
        if len(pdf) == 0:
            raise ValueError("PDF has no pages")
        page = pdf[0]
        pil = page.render(scale=_PDF_RENDER_SCALE).to_pil()
        buf = io.BytesIO()
        pil.save(buf, format="PNG", optimize=True)
        return buf.getvalue()
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError(f"PDF render failed: {exc}") from exc


def to_image_data_url(
    payload: dict,
    *,
    preview: bool = False,
    align_user_north: bool | None = None,
) -> str:
    """
    Convert a floor-plan upload payload into a PNG data URL ready for vision.

    Args:
      payload: {"type": "image"|"pdf", "data_url"?: str, "base64"?: str}
      preview: True → smaller image (1024px) for cheap validation reads

    Returns:
      "data:image/png;base64,<...>"

    Raises:
      ValueError on invalid input or oversize.
    """
    if not isinstance(payload, dict):
        raise ValueError("floor_plan_upload must be an object")
    kind = (payload.get("type") or "").strip().lower()
    if kind not in ("image", "pdf"):
        raise ValueError("floor_plan_upload.type must be 'image' or 'pdf'")

    raw = decode_upload_raw_bytes(payload)
    max_edge = _PREVIEW_LONG_EDGE if preview else _MAX_LONG_EDGE

    north_at = (payload.get("north_at") or "top").strip().lower()
    if align_user_north is None:
        # Vision reads true north from the arrow on the plan (unrotated image).
        align_user_north = False
    rotate_ccw = _NORTH_AT_ROTATE_CCW.get(north_at, 0) if align_user_north else 0

    if kind == "pdf":
        png_bytes = _pdf_first_page_to_png_bytes(raw)
        return _bytes_to_png_data_url(
            png_bytes, rotate_ccw_deg=rotate_ccw, max_long_edge=max_edge,
        )

    return _bytes_to_png_data_url(
        raw, rotate_ccw_deg=rotate_ccw, max_long_edge=max_edge,
    )
