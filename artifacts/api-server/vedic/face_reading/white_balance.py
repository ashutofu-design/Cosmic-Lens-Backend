"""
Simple gray-world white balance.

Rationale: phone auto-WB causes the same person's skin metrics to shift
±5–10 in Lab space across photos. Without normalization, the skin-pixel
sampling output is not reproducible.

Method: compute per-channel mean over a face-mask sub-region; rescale so
all three channels share the same mean (gray-world assumption applied to
the skin region rather than the whole image, which is more accurate for
portraits).
"""
from __future__ import annotations

import numpy as np


def gray_world_balance(rgb: np.ndarray,
                       face_bbox: dict | None = None) -> tuple[np.ndarray, dict]:
    """Apply gray-world WB based on the face region (falls back to full image).

    Returns (balanced_rgb, info_dict).
    """
    if rgb is None or rgb.ndim != 3:
        return rgb, {"applied": False, "reason": "invalid_input"}

    h, w = rgb.shape[:2]
    if face_bbox and all(k in face_bbox for k in ("x", "y", "w", "h")):
        x, y, bw, bh = face_bbox["x"], face_bbox["y"], face_bbox["w"], face_bbox["h"]
        # Inset 15% to avoid hair/background bias
        x0 = max(0, x + int(bw * 0.15))
        y0 = max(0, y + int(bh * 0.15))
        x1 = min(w, x + int(bw * 0.85))
        y1 = min(h, y + int(bh * 0.85))
        roi = rgb[y0:y1, x0:x1]
    else:
        roi = rgb

    if roi.size == 0:
        return rgb, {"applied": False, "reason": "empty_roi"}

    mean_per_ch = roi.reshape(-1, 3).mean(axis=0).astype(np.float32)
    if (mean_per_ch < 1.0).any():
        return rgb, {"applied": False, "reason": "near_black_channel"}

    target = float(mean_per_ch.mean())
    gain = target / mean_per_ch
    # Clip extreme gains (avoid amplifying noise in low-light shots)
    gain = np.clip(gain, 0.7, 1.4)

    balanced = np.clip(rgb.astype(np.float32) * gain, 0, 255).astype(np.uint8)
    return balanced, {
        "applied": True,
        "method": "gray_world_face_roi",
        "channel_means_pre":  [round(float(v), 2) for v in mean_per_ch],
        "gain_rgb":           [round(float(v), 3) for v in gain],
        "target_mean":        round(target, 2),
    }
