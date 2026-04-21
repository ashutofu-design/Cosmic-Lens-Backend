"""
PDF Visuals — generates PNG bytes for PDF embedding.
  • make_cover_photo: square crop of user's front photo, with rounded frame
  • make_face_map: annotated face with zone labels (forehead/eyes/nose/cheeks/lips/jaw)
  • make_radar_chart: 5-axis OCEAN radar
  • make_score_bars: horizontal bar chart of 5 bonus scores
"""
from __future__ import annotations
from io import BytesIO
from typing import Dict, List, Tuple, Optional
import math

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Wedge


# Brand palette (matches pdf_report.py)
C_PRIMARY = "#7B1F1F"
C_ACCENT  = "#C2A878"
C_INK     = "#2A2418"
C_MUTED   = "#7A7164"
C_BG      = "#FAF6EC"
C_TRACK   = "#EDE3CA"


# ── Mediapipe landmark indices (468-point face mesh) ──────────────────────
# Used to compute zone centers + face bbox
_LM = {
    "forehead":   10,
    "left_eye":   33,
    "right_eye":  263,
    "nose_tip":   1,
    "lips_top":   13,
    "lips_bot":   14,
    "chin":       152,
    "jaw_left":   234,
    "jaw_right":  454,
    "cheek_left": 50,
    "cheek_right":280,
    "brow_left":  70,
    "brow_right": 300,
    "ear_left":   234,    # approx
    "ear_right":  454,
}


# ── Image decoders ────────────────────────────────────────────────────────
def _decode(image_bytes: bytes) -> Optional[Image.Image]:
    try:
        im = Image.open(BytesIO(image_bytes))
        im = ImageOps.exif_transpose(im)
        return im.convert("RGB")
    except Exception:
        return None


def _safe_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold
        else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold
        else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue
    return ImageFont.load_default()


# ── 1. Cover photo (square crop, gold frame) ──────────────────────────────
def make_cover_photo(image_bytes: bytes, points_norm: Optional[List] = None,
                     out_size: int = 520) -> Optional[bytes]:
    """Square-crop around face if landmarks available, else center-crop. Add gold frame."""
    im = _decode(image_bytes)
    if im is None:
        return None
    W, H = im.size

    # Crop box around face
    if points_norm and len(points_norm) > 200:
        xs = [p[0] for p in points_norm]
        ys = [p[1] for p in points_norm]
        x_min, x_max = min(xs), max(xs)
        y_min, y_max = min(ys), max(ys)
        cx = (x_min + x_max) / 2 * W
        cy = (y_min + y_max) / 2 * H
        face_h = (y_max - y_min) * H
        side = min(W, H, face_h * 2.0)
    else:
        cx, cy = W / 2, H / 2
        side = min(W, H) * 0.95

    side = max(64, side)
    x0 = max(0, int(cx - side / 2)); y0 = max(0, int(cy - side / 2))
    x1 = min(W, int(cx + side / 2)); y1 = min(H, int(cy + side / 2))
    crop = im.crop((x0, y0, x1, y1)).resize((out_size, out_size), Image.LANCZOS)

    # Build canvas with gold double-frame on cream
    pad = 18
    canvas = Image.new("RGB", (out_size + pad * 2, out_size + pad * 2), C_BG)
    draw = ImageDraw.Draw(canvas)
    # outer thin
    draw.rectangle([2, 2, canvas.size[0] - 3, canvas.size[1] - 3], outline=C_ACCENT, width=2)
    # inner thicker
    draw.rectangle([pad - 6, pad - 6, out_size + pad + 5, out_size + pad + 5],
                   outline=C_PRIMARY, width=4)
    canvas.paste(crop, (pad, pad))

    out = BytesIO()
    canvas.save(out, "PNG", optimize=True)
    return out.getvalue()


# ── 2. Annotated face map ─────────────────────────────────────────────────
_ZONES = [
    # (label_hi, lm_index, dx, dy, side)  side: 'L'=label-left of point, 'R'=right
    ("Mastak (Forehead)",   "forehead",   -180,  -10, "L"),
    ("Bhravu (Brows)",      "brow_left",  -180,    0, "L"),
    ("Aankhein (Eyes)",     "right_eye",   140,  -10, "R"),
    ("Naak (Nose)",         "nose_tip",    150,    0, "R"),
    ("Gaal (Cheeks)",       "cheek_left", -180,    5, "L"),
    ("Hoṭh (Lips)",         "lips_top",    150,   30, "R"),
    ("Jabdaa (Jaw)",        "jaw_right",   140,   20, "R"),
    ("Thoddi (Chin)",       "chin",        140,   60, "R"),
]


def make_face_map(image_bytes: bytes, points_norm: List,
                  max_height: int = 720) -> Optional[bytes]:
    """Photo with zone-label callouts. Returns PNG bytes."""
    im = _decode(image_bytes)
    if im is None or not points_norm or len(points_norm) < 200:
        return None
    W, H = im.size

    # Crop face region with extra room for labels (1.6x face height each way)
    xs = [p[0] for p in points_norm]; ys = [p[1] for p in points_norm]
    x_min, x_max = min(xs)*W, max(xs)*W
    y_min, y_max = min(ys)*H, max(ys)*H
    face_w, face_h = x_max - x_min, y_max - y_min
    pad_x = face_w * 1.0
    pad_y = face_h * 0.4
    cx0 = max(0, int(x_min - pad_x))
    cy0 = max(0, int(y_min - pad_y))
    cx1 = min(W, int(x_max + pad_x))
    cy1 = min(H, int(y_max + pad_y))
    crop = im.crop((cx0, cy0, cx1, cy1))
    cw, ch = crop.size

    # Resize to target height
    scale = max_height / ch
    new_w = int(cw * scale); new_h = max_height
    crop = crop.resize((new_w, new_h), Image.LANCZOS)

    # Recompute landmark pixel positions in new image space
    def lm_xy(idx: int) -> Tuple[int, int]:
        nx, ny = points_norm[idx][0], points_norm[idx][1]
        px = (nx * W - cx0) * scale
        py = (ny * H - cy0) * scale
        return int(px), int(py)

    # Soften the face image so labels pop
    base = Image.new("RGB", crop.size, C_BG)
    base.paste(crop, (0, 0))
    draw = ImageDraw.Draw(base, "RGBA")

    font_lab = _safe_font(15, bold=True)
    font_dot = _safe_font(11, bold=True)

    for (label, key, dx, dy, side) in _ZONES:
        idx = _LM.get(key)
        if idx is None or idx >= len(points_norm):
            continue
        px, py = lm_xy(idx)
        # Marker dot (gold ring + maroon center)
        draw.ellipse([px-7, py-7, px+7, py+7], outline=C_ACCENT, width=2,
                     fill=(123, 31, 31, 230))
        # Label box position
        lx = px + dx; ly = py + dy
        # measure text
        tb = draw.textbbox((0, 0), label, font=font_lab)
        tw, th = tb[2]-tb[0], tb[3]-tb[1]
        pad = 6
        bx0 = lx - pad; by0 = ly - pad
        bx1 = lx + tw + pad; by1 = ly + th + pad
        # Clamp inside canvas
        if bx0 < 4: 
            shift = 4 - bx0; bx0 += shift; bx1 += shift; lx += shift
        if bx1 > new_w - 4:
            shift = bx1 - (new_w - 4); bx0 -= shift; bx1 -= shift; lx -= shift
        if by0 < 4:
            shift = 4 - by0; by0 += shift; by1 += shift; ly += shift
        if by1 > new_h - 4:
            shift = by1 - (new_h - 4); by0 -= shift; by1 -= shift; ly -= shift
        # Connector line from dot to label box edge
        anchor_x = bx0 if side == "R" else bx1
        anchor_y = (by0 + by1) // 2
        draw.line([(px, py), (anchor_x, anchor_y)], fill=C_PRIMARY, width=2)
        # Label background (cream w/ gold border)
        draw.rectangle([bx0, by0, bx1, by1], fill=(255, 244, 220, 240),
                       outline=C_ACCENT, width=2)
        draw.text((lx, ly), label, fill=C_INK, font=font_lab)

    out = BytesIO()
    base.save(out, "PNG", optimize=True)
    return out.getvalue()


# ── 3. Radar chart (OCEAN big-5) ──────────────────────────────────────────
def make_radar_chart(traits_score_0_100: Dict[str, float]) -> bytes:
    """5-axis radar of OCEAN traits. Input keys: O,C,E,A,N or full names."""
    label_map = {
        "O": "Openness\n(Naya soch)",
        "C": "Conscientiousness\n(Anushasan)",
        "E": "Extraversion\n(Bahirmukh)",
        "A": "Agreeableness\n(Madhurta)",
        "N": "Neuroticism\n(Bhavuk-tha)",
    }
    keys = ["O", "C", "E", "A", "N"]
    vals = []
    for k in keys:
        v = traits_score_0_100.get(k)
        if v is None:
            v = traits_score_0_100.get({"O":"openness","C":"conscientiousness","E":"extraversion","A":"agreeableness","N":"neuroticism"}[k])
        try:
            vals.append(float(v))
        except Exception:
            vals.append(50.0)

    angles = [n / 5 * 2 * math.pi for n in range(5)]
    angles += angles[:1]
    vals_closed = vals + vals[:1]

    fig, ax = plt.subplots(figsize=(5.2, 5.2), subplot_kw=dict(polar=True))
    fig.patch.set_facecolor(C_BG)
    ax.set_facecolor(C_BG)

    ax.plot(angles, vals_closed, color=C_PRIMARY, linewidth=2.2)
    ax.fill(angles, vals_closed, color=C_PRIMARY, alpha=0.28)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels([label_map[k] for k in keys], fontsize=9, color=C_INK)
    ax.set_yticks([20, 40, 60, 80])
    ax.set_yticklabels(["20", "40", "60", "80"], fontsize=7, color=C_MUTED)
    ax.set_ylim(0, 100)
    ax.spines["polar"].set_color(C_ACCENT)
    ax.grid(color=C_TRACK, linewidth=0.8)

    # Value annotations
    for ang, val, k in zip(angles[:-1], vals, keys):
        r = min(95, val + 7)
        ax.text(ang, r, f"{val:.0f}", color=C_PRIMARY,
                fontsize=10, fontweight="bold",
                ha="center", va="center")

    ax.set_title("Big-5 Vyaktitva Fingerprint", color=C_PRIMARY,
                 fontsize=13, fontweight="bold", pad=18)

    out = BytesIO()
    plt.savefig(out, format="png", dpi=170, bbox_inches="tight",
                facecolor=C_BG)
    plt.close(fig)
    return out.getvalue()


# ── 4. Score bars (5 bonus scores out of 10) ──────────────────────────────
def make_score_bars(scores_10: Dict[str, float]) -> bytes:
    """Horizontal bar chart of 5 bonus scores."""
    pretty = [
        ("leadership_10",   "Leadership"),
        ("intelligence_10", "Intelligence"),
        ("money_10",        "Money / Wealth"),
        ("love_10",         "Love / Relationship"),
        ("health_10",       "Health / Vitality"),
    ]
    labels = [p[1] for p in pretty]
    vals   = [float(scores_10.get(p[0]) or 0.0) for p in pretty]

    fig, ax = plt.subplots(figsize=(5.6, 3.8))
    fig.patch.set_facecolor(C_BG)
    ax.set_facecolor(C_BG)

    y = np.arange(len(labels))
    ax.barh(y, [10] * len(labels), color=C_TRACK, height=0.55)
    bars = ax.barh(y, vals, color=C_PRIMARY, height=0.55)

    for i, (v, bar) in enumerate(zip(vals, bars)):
        ax.text(v + 0.18, i, f"{v:.1f}/10", va="center",
                fontsize=10, color=C_PRIMARY, fontweight="bold")

    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=10, color=C_INK)
    ax.set_xlim(0, 11)
    ax.set_xticks([0, 2, 4, 6, 8, 10])
    ax.tick_params(axis="x", colors=C_MUTED, labelsize=8)
    ax.invert_yaxis()
    for sp in ("top", "right", "left"):
        ax.spines[sp].set_visible(False)
    ax.spines["bottom"].set_color(C_ACCENT)
    ax.set_title("Tumhare 5 Premium Scores", color=C_PRIMARY,
                 fontsize=13, fontweight="bold", pad=12, loc="left")

    out = BytesIO()
    plt.savefig(out, format="png", dpi=170, bbox_inches="tight",
                facecolor=C_BG)
    plt.close(fig)
    return out.getvalue()
