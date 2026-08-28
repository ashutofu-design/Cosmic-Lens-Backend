"""Landmark-normalized fate line ridge tracing (affine + proportional corridor + graph path)."""
from __future__ import annotations

import heapq
import math
from typing import Any

import cv2
import numpy as np


FATE_WARP_SIZE = 512


def landmarks_by_id(landmarks: list[dict]) -> dict[int, dict]:
    return {
        int(p["id"]): p
        for p in landmarks
        if isinstance(p, dict) and "id" in p
    }


def proportional_fate_corridor(landmarks: list[dict]) -> dict[str, float]:
    """Search zone in normalized 0..1 coords — scales with palm geometry."""
    by_id = landmarks_by_id(landmarks)
    wrist = by_id.get(0, {"x": 0.5, "y": 0.88})
    middle = by_id.get(9, {"x": 0.5, "y": 0.48})
    index = by_id.get(5, middle)
    pinky = by_id.get(17, middle)
    palm_width = max(abs(float(index["x"]) - float(pinky["x"])), 0.12)
    span = max(abs(float(wrist["y"]) - float(middle["y"])), 0.12)
    y_top = float(middle["y"]) - 0.15 * span
    y_bottom = float(wrist["y"]) + 0.10 * span
    x_center = (float(index["x"]) + float(pinky["x"])) / 2.0
    x_half = 0.15 * palm_width
    return {
        "y_top": y_top,
        "y_bottom": y_bottom,
        "x_center": x_center,
        "x_half": x_half,
        "palm_width": palm_width,
        "span_y": span,
        "fate_axis_x": float(middle["x"]),
        "wrist_y": float(wrist["y"]),
        "middle_mcp_y": float(middle["y"]),
    }


def wrist_middle_rotation_degrees(landmarks: list[dict]) -> float:
    by_id = landmarks_by_id(landmarks)
    wrist = by_id.get(0, {"x": 0.5, "y": 0.88})
    middle = by_id.get(9, {"x": 0.5, "y": 0.48})
    dy = float(middle["y"]) - float(wrist["y"])
    dx = float(middle["x"]) - float(wrist["x"])
    return math.degrees(math.atan2(dy, dx)) - 90.0


def build_affine_warp(
    landmarks: list[dict],
    width: int,
    height: int,
    *,
    output_size: int = FATE_WARP_SIZE,
) -> dict[str, Any] | None:
    if len(landmarks) < 21:
        return None
    by_id = landmarks_by_id(landmarks)
    wrist = by_id.get(0)
    middle = by_id.get(9)
    index = by_id.get(5)
    pinky = by_id.get(17)
    if not all([wrist, middle, index, pinky]):
        return None

    def px(p: dict) -> np.ndarray:
        return np.array([float(p["x"]) * width, float(p["y"]) * height], dtype=np.float32)

    p0, p9, p5, p17 = px(wrist), px(middle), px(index), px(pinky)
    palm_width_px = max(float(np.linalg.norm(p5 - p17)), 8.0)
    angle = wrist_middle_rotation_degrees(landmarks)
    center = (p0 + p9) / 2.0
    rotate = cv2.getRotationMatrix2D(tuple(center), angle, 1.0)

    rotated_pts = cv2.transform(
        np.array([p0, p9, p5, p17], dtype=np.float32)[None, :, :],
        rotate,
    )[0]
    r0, r9, r5, r17 = rotated_pts
    palm_h = max(float(np.linalg.norm(r9 - r0)), palm_width_px * 0.8)
    dst_w = output_size
    dst_h = output_size
    margin = 0.08
    src_pts = np.float32([r0, r9, r17])
    dst_pts = np.float32([
        [dst_w * 0.5, dst_h * (1.0 - margin)],
        [dst_w * 0.5, dst_h * margin],
        [dst_w * (0.5 + margin), dst_h * (margin + 0.12)],
    ])
    affine = cv2.getAffineTransform(src_pts, dst_pts)
    combined = affine @ np.vstack([rotate, [0.0, 0.0, 1.0]])
    combined = combined[:2, :]
    inv = cv2.invertAffineTransform(combined)
    return {
        "affine": combined,
        "inverse_affine": inv,
        "rotation_deg": angle,
        "output_size": (dst_w, dst_h),
        "palm_width_px": palm_width_px,
    }


def warp_rgb_mask(
    rgb: np.ndarray,
    palm_mask: np.ndarray,
    affine: np.ndarray,
    output_size: tuple[int, int],
) -> tuple[np.ndarray, np.ndarray]:
    dsize = (int(output_size[0]), int(output_size[1]))
    warped_rgb = cv2.warpAffine(
        rgb, affine, dsize, flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT_101,
    )
    warped_mask = cv2.warpAffine(
        palm_mask, affine, dsize, flags=cv2.INTER_NEAREST, borderMode=cv2.BORDER_CONSTANT,
    )
    return warped_rgb, warped_mask


def lab_clahe_lightness(rgb: np.ndarray) -> np.ndarray:
    lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB)
    l_channel, a_channel, b_channel = cv2.split(lab)
    bg = cv2.GaussianBlur(l_channel, (0, 0), 31)
    illum = cv2.addWeighted(l_channel, 1.0, bg, -1.0, 128)
    enhanced_l = cv2.createCLAHE(2.0, (8, 8)).apply(illum)
    merged = cv2.merge((enhanced_l, a_channel, b_channel))
    return cv2.cvtColor(merged, cv2.COLOR_LAB2RGB)


def hessian_ridge_response(gray: np.ndarray, sigmas: tuple[float, ...] = (1.0, 2.0, 3.5)) -> np.ndarray:
    """Frangi-like ridge emphasis without skimage — multiscale Hessian."""
    gray_f = gray.astype(np.float32) / 255.0
    response = np.zeros_like(gray_f)
    for sigma in sigmas:
        k = max(3, int(sigma * 6) | 1)
        blurred = cv2.GaussianBlur(gray_f, (k, k), sigma)
        dxx = cv2.Sobel(blurred, cv2.CV_32F, 2, 0, ksize=3)
        dyy = cv2.Sobel(blurred, cv2.CV_32F, 0, 2, ksize=3)
        dxy = cv2.Sobel(blurred, cv2.CV_32F, 1, 1, ksize=3)
        trace = dxx + dyy
        det = dxx * dyy - dxy * dxy
        temp = np.sqrt(np.maximum(trace * trace / 4.0 - det, 0.0))
        l1 = trace / 2.0 + temp
        l2 = trace / 2.0 - temp
        # Dark crease ridges: smaller eigenvalue magnitude along crease direction
        rb = np.abs(l2) - 0.5 * np.abs(l1)
        rb = np.clip(rb, 0.0, None)
        response = np.maximum(response, rb)
    if response.max() > 1e-6:
        response = response / float(response.max())
    return response.astype(np.float32)


def _try_frangi(gray: np.ndarray) -> np.ndarray | None:
    try:
        from skimage.filters import frangi  # type: ignore

        normalized = gray.astype(np.float64) / 255.0
        ridges = frangi(normalized, sigmas=range(1, 4), black_ridges=True)
        if ridges.max() > 1e-6:
            ridges = ridges / float(ridges.max())
        return ridges.astype(np.float32)
    except Exception:
        return None


def ridge_response_map(rgb: np.ndarray) -> np.ndarray:
    lab_rgb = lab_clahe_lightness(rgb)
    gray = cv2.cvtColor(lab_rgb, cv2.COLOR_RGB2GRAY)
    frangi = _try_frangi(gray)
    if frangi is not None:
        return frangi
    return hessian_ridge_response(gray)


def corridor_mask_from_corridor(
    shape: tuple[int, int],
    corridor: dict[str, float],
) -> np.ndarray:
    height, width = shape
    mask = np.zeros((height, width), np.uint8)
    y0 = int(np.clip(corridor["y_top"] * height, 0, height - 1))
    y1 = int(np.clip(corridor["y_bottom"] * height, 0, height - 1))
    x0 = int(np.clip((corridor["x_center"] - corridor["x_half"]) * width, 0, width - 1))
    x1 = int(np.clip((corridor["x_center"] + corridor["x_half"]) * width, 0, width - 1))
    if y1 > y0 and x1 > x0:
        mask[y0:y1 + 1, x0:x1 + 1] = 255
    return mask


def _warp_point_to_normalized(x: float, y: float, inv_affine: np.ndarray, width: int, height: int) -> dict:
    pt = inv_affine @ np.array([x, y, 1.0], dtype=np.float32)
    return {
        "x": round(float(np.clip(pt[0] / width, 0.0, 1.0)), 6),
        "y": round(float(np.clip(pt[1] / height, 0.0, 1.0)), 6),
    }


def _warp_normalized_to_pixel(x: float, y: float, affine: np.ndarray, width: int, height: int) -> tuple[float, float]:
    pt = affine @ np.array([x * width, y * height, 1.0], dtype=np.float32)
    return float(pt[0]), float(pt[1])


def verify_inverse_remap(
    path_warped: list[tuple[int, int]],
    inverse_affine: np.ndarray,
    forward_affine: np.ndarray,
    width: int,
    height: int,
    warped_w: int,
    warped_h: int,
) -> dict[str, float | str]:
    if not path_warped:
        return {
            "inverse_remap_max_error_px": 0.0,
            "inverse_remap_mean_error_px": 0.0,
            "coordinate_frame": "original_image_normalized",
        }
    errors: list[float] = []
    for wx, wy in path_warped[:: max(1, len(path_warped) // 8)]:
        norm = _warp_point_to_normalized(float(wx), float(wy), inverse_affine, width, height)
        back_x, back_y = _warp_normalized_to_pixel(
            norm["x"], norm["y"], forward_affine, width, height,
        )
        errors.append(math.hypot(back_x - wx, back_y - wy))
    return {
        "inverse_remap_max_error_px": round(max(errors), 4),
        "inverse_remap_mean_error_px": round(float(np.mean(errors)), 4),
        "coordinate_frame": "original_image_normalized",
    }


def _snap_to_allowed(
    allowed: np.ndarray,
    x: int,
    y: int,
    *,
    max_radius: int = 22,
) -> tuple[int, int]:
    height, width = allowed.shape
    if 0 <= x < width and 0 <= y < height and allowed[y, x]:
        return x, y
    for radius in range(1, max_radius + 1):
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                px, py = x + dx, y + dy
                if 0 <= px < width and 0 <= py < height and allowed[py, px]:
                    return px, py
    return x, y


def _zone_y_bounds(corridor: dict[str, float], height: int, *, zone: str) -> tuple[int, int]:
    span_px = int(max(corridor["span_y"] * height, height * 0.08))
    y_top = int(np.clip(corridor["y_top"] * height, 0, height - 1))
    y_bottom = int(np.clip(corridor["y_bottom"] * height, 0, height - 1))
    if zone == "top":
        y1 = min(height - 1, y_top + max(8, int(span_px * 0.18)))
        return y_top, y1
    y0 = max(0, y_bottom - max(8, int(span_px * 0.22)))
    return y0, y_bottom


def _collect_dynamic_nodes(
    ridge: np.ndarray,
    allowed: np.ndarray,
    corridor: dict[str, float],
    height: int,
    width: int,
    *,
    zone: str,
    limit: int = 12,
    percentile: float = 0.62,
) -> list[tuple[int, int]]:
    y0, y1 = _zone_y_bounds(corridor, height, zone=zone)
    if y1 <= y0:
        return []
    x_center = int(round(corridor["x_center"] * width))
    x_half = int(round(corridor["x_half"] * width))
    x0 = max(0, x_center - x_half)
    x1 = min(width, x_center + x_half)
    candidates: list[tuple[float, int, int]] = []
    for y in range(y0, y1 + 1):
        for x in range(x0, x1):
            if not allowed[y, x]:
                continue
            val = float(ridge[y, x])
            if val <= 0:
                continue
            center_w = 1.0 - min(abs(x - x_center) / max(x_half, 1), 1.0)
            candidates.append((val * (0.55 + 0.45 * center_w), x, y))
    if not candidates:
        return []
    threshold = float(np.percentile([c[0] for c in candidates], percentile * 100))
    filtered = [(x, y) for score, x, y in candidates if score >= threshold]
    if not filtered:
        filtered = [(x, y) for _, x, y in sorted(candidates, reverse=True)[:limit]]
    scored = sorted(
        ((float(ridge[y, x]), x, y) for x, y in filtered),
        reverse=True,
    )
    nodes: list[tuple[int, int]] = []
    seen: set[tuple[int, int]] = set()
    for _, x, y in scored:
        if (x, y) in seen:
            continue
        seen.add((x, y))
        nodes.append((x, y))
        if len(nodes) >= limit:
            break
    return nodes


def _path_vertical_span_ratio(
    path: list[tuple[int, int]],
    height: int,
    corridor_span_y: float,
) -> float:
    if len(path) < 2:
        return 0.0
    ys = [y / height for _, y in path]
    return float((max(ys) - min(ys)) / max(corridor_span_y, 1e-4))


def _mean_ridge_along_path(path: list[tuple[int, int]], ridge: np.ndarray) -> float:
    if not path:
        return 0.0
    values = [float(ridge[y, x]) for x, y in path if ridge[y, x] > 0]
    return float(np.mean(values)) if values else 0.0


def _reconstruct_dijkstra_path(
    prev: dict[int, int | None],
    goal: int,
    width: int,
) -> list[tuple[int, int]]:
    path: list[tuple[int, int]] = []
    node: int | None = goal
    while node is not None:
        py, px = divmod(node, width)
        path.append((px, py))
        node = prev.get(node)
    path.reverse()
    return path


def _unique_nodes(nodes: list[tuple[int, int]], limit: int = 16) -> list[tuple[int, int]]:
    seen: set[tuple[int, int]] = set()
    out: list[tuple[int, int]] = []
    for node in nodes:
        if node in seen:
            continue
        seen.add(node)
        out.append(node)
        if len(out) >= limit:
            break
    return out


def extend_ridge_path_toward(
    pixel_path: list[tuple[int, int]],
    ridge: np.ndarray,
    allowed: np.ndarray,
    target_xy: tuple[int, int],
    *,
    max_steps: int = 140,
) -> list[tuple[int, int]]:
    """Extend path end along ridge density toward a dynamic anatomical target."""
    if not pixel_path:
        return pixel_path
    path = list(pixel_path)
    tx, ty = target_xy
    x, y = path[-1]
    height, width = ridge.shape
    for _ in range(max_steps):
        if math.hypot(x - tx, y - ty) <= 4:
            if allowed[ty, tx]:
                path.append((tx, ty))
            break
        best: tuple[int, int] | None = None
        best_val = -1.0
        for dy in range(-1, 3):
            for dx in range(-1, 2):
                nx, ny = x + dx, y + dy
                if not (0 <= nx < width and 0 <= ny < height):
                    continue
                if not allowed[ny, nx]:
                    continue
                toward = 1.0 / (1.0 + math.hypot(nx - tx, ny - ty))
                val = float(ridge[ny, nx]) * (0.42 + 0.58 * toward)
                if val > best_val:
                    best_val = val
                    best = (nx, ny)
        if best is None or best_val < 0.035 or best == (x, y):
            break
        path.append(best)
        x, y = best
    return path


def extend_ridge_path_both_ends(
    pixel_path: list[tuple[int, int]],
    ridge: np.ndarray,
    allowed: np.ndarray,
    start_xy: tuple[int, int],
    end_xy: tuple[int, int],
) -> list[tuple[int, int]]:
    if not pixel_path:
        return pixel_path
    forward = extend_ridge_path_toward(pixel_path, ridge, allowed, end_xy)
    backward = extend_ridge_path_toward(list(reversed(forward)), ridge, allowed, start_xy)
    return list(reversed(backward))


def dijkstra_multi_source_multi_sink(
    ridge: np.ndarray,
    allowed: np.ndarray,
    sources: list[tuple[int, int]],
    sinks: list[tuple[int, int]],
    *,
    corridor_span_y: float,
    min_span_ratio: float = 0.20,
) -> list[tuple[int, int]]:
    if not sources or not sinks:
        return []
    height, width = ridge.shape
    cost_map = np.clip(1.0 - ridge, 0.02, 1.0)
    cost_map[~allowed] = 1e6

    best_path: list[tuple[int, int]] = []
    best_score = -1e18
    sink_set = set(sinks)
    neighbors = (
        (-1, 0), (1, 0), (0, -1), (0, 1),
        (-1, -1), (-1, 1), (1, -1), (1, 1),
    )

    for sx, sy in sources:
        start = sy * width + sx
        if cost_map[sy, sx] >= 1e5:
            continue
        dist: dict[int, float] = {start: 0.0}
        prev: dict[int, int | None] = {start: None}
        heap: list[tuple[float, int]] = [(0.0, start)]
        while heap:
            curr_cost, node = heapq.heappop(heap)
            if curr_cost > dist.get(node, 1e9):
                continue
            py, px = divmod(node, width)
            if (px, py) in sink_set:
                path = _reconstruct_dijkstra_path(prev, node, width)
                span = _path_vertical_span_ratio(path, height, corridor_span_y)
                if span >= min_span_ratio:
                    mean_ridge = _mean_ridge_along_path(path, ridge)
                    norm_cost = curr_cost / max(height * width, 1)
                    score = span * 0.52 + mean_ridge * 0.38 - norm_cost * 0.10
                    if score > best_score:
                        best_score = score
                        best_path = path
            for dy, dx in neighbors:
                ny, nx = py + dy, px + dx
                if not (0 <= nx < width and 0 <= ny < height):
                    continue
                if not allowed[ny, nx]:
                    continue
                nnode = ny * width + nx
                step = cost_map[ny, nx] * (1.414 if dx and dy else 1.0)
                nd = curr_cost + step
                if nd < dist.get(nnode, 1e9):
                    dist[nnode] = nd
                    prev[nnode] = node
                    heapq.heappush(heap, (nd, nnode))
    return best_path


def trace_vertical_ridge_column(
    ridge: np.ndarray,
    allowed: np.ndarray,
    corridor: dict[str, float],
    warped_h: int,
    warped_w: int,
    *,
    y_start: float,
    y_end: float,
) -> list[tuple[int, int]]:
    """Full-span column sweep — guarantees MCP→wrist vertical coverage."""
    x_center = int(round(corridor["x_center"] * warped_w))
    x_half = max(int(round(corridor["x_half"] * warped_w)), 4)
    y0 = int(np.clip(min(y_start, y_end) * warped_h, 0, warped_h - 1))
    y1 = int(np.clip(max(y_start, y_end) * warped_h, 0, warped_h - 1))
    if y1 - y0 < 8:
        return []
    step = max(1, (y1 - y0) // 56)
    path: list[tuple[int, int]] = []
    for y in range(y0, y1 + 1, step):
        best_x = x_center
        best_val = -1.0
        for x in range(max(0, x_center - x_half), min(warped_w, x_center + x_half + 1)):
            if not allowed[y, x]:
                continue
            center_w = 1.0 - min(abs(x - x_center) / max(x_half, 1), 1.0)
            val = float(ridge[y, x]) * (0.40 + 0.60 * center_w)
            if val > best_val:
                best_val = val
                best_x = x
        if best_val >= 0.015:
            path.append((best_x, y))
    if y1 not in [p[1] for p in path]:
        path.append((path[-1][0] if path else x_center, y1))
    return path


def _pick_best_pixel_path(
    paths: list[list[tuple[int, int]]],
    ridge: np.ndarray,
    height: int,
    corridor_span_y: float,
) -> list[tuple[int, int]]:
    ranked: list[tuple[float, list[tuple[int, int]]]] = []
    for path in paths:
        if len(path) < 4:
            continue
        span = _path_vertical_span_ratio(path, height, corridor_span_y)
        mean_ridge = _mean_ridge_along_path(path, ridge)
        score = span * 0.62 + mean_ridge * 0.38
        ranked.append((score, path))
    if not ranked:
        return []
    ranked.sort(key=lambda item: item[0], reverse=True)
    return ranked[0][1]


def _ensure_path_endpoints(
    path: list[tuple[int, int]],
    start_xy: tuple[int, int],
    end_xy: tuple[int, int],
    allowed: np.ndarray,
) -> list[tuple[int, int]]:
    if not path:
        return path
    out = list(path)
    sx, sy = start_xy
    ex, ey = end_xy
    if allowed[sy, sx] and math.hypot(out[0][0] - sx, out[0][1] - sy) > 6:
        out.insert(0, (sx, sy))
    if allowed[ey, ex] and math.hypot(out[-1][0] - ex, out[-1][1] - ey) > 6:
        out.append((ex, ey))
    return out


def dijkstra_ridge_path(
    ridge: np.ndarray,
    palm_mask: np.ndarray,
    corridor_mask: np.ndarray,
    start_xy: tuple[int, int],
    goal_xy: tuple[int, int],
) -> list[tuple[int, int]]:
    height, width = ridge.shape
    allowed = (palm_mask > 0) & (corridor_mask > 0)
    sx, sy = _snap_to_allowed(allowed, start_xy[0], start_xy[1])
    gx, gy = _snap_to_allowed(allowed, goal_xy[0], goal_xy[1])
    if not allowed[sy, sx] or not allowed[gy, gx]:
        return []

    cost_map = 1.0 - ridge
    cost_map = np.clip(cost_map, 0.02, 1.0)
    cost_map[~allowed] = 1e6

    start = sy * width + sx
    goal = gy * width + gx
    dist = {start: 0.0}
    prev: dict[int, int | None] = {start: None}
    heap: list[tuple[float, int]] = [(0.0, start)]

    neighbors = (
        (-1, 0), (1, 0), (0, -1), (0, 1),
        (-1, -1), (-1, 1), (1, -1), (1, 1),
    )

    while heap:
        curr_cost, node = heapq.heappop(heap)
        if node == goal:
            break
        if curr_cost > dist.get(node, 1e9):
            continue
        ny, nx = divmod(node, width)
        for dy, dx in neighbors:
            py, px = ny + dy, nx + dx
            if not (0 <= px < width and 0 <= py < height):
                continue
            if not allowed[py, px]:
                continue
            nnode = py * width + px
            step = cost_map[py, px] * (1.414 if dx and dy else 1.0)
            nd = curr_cost + step
            if nd < dist.get(nnode, 1e9):
                dist[nnode] = nd
                prev[nnode] = node
                heapq.heappush(heap, (nd, nnode))

    if goal not in prev:
        return []

    path: list[tuple[int, int]] = []
    node: int | None = goal
    while node is not None:
        py, px = divmod(node, width)
        path.append((px, py))
        node = prev.get(node)
    path.reverse()
    return path


def trace_fate_line_normalized(
    rgb: np.ndarray,
    palm_mask: np.ndarray,
    landmarks: list[dict],
) -> dict[str, Any] | None:
    height, width = rgb.shape[:2]
    if len(landmarks) < 21:
        return None
    warp = build_affine_warp(landmarks, width, height)
    if warp is None:
        return None

    warped_rgb, warped_mask = warp_rgb_mask(
        rgb, palm_mask, warp["affine"], warp["output_size"],
    )
    warped_h, warped_w = warped_rgb.shape[:2]
    lab_rgb = lab_clahe_lightness(warped_rgb)
    gray = cv2.cvtColor(lab_rgb, cv2.COLOR_RGB2GRAY)
    frangi_map = _try_frangi(gray)
    if frangi_map is not None:
        ridge = frangi_map
        ridge_method = "frangi"
    else:
        ridge = hessian_ridge_response(gray)
        ridge_method = "hessian_multiscale"

    by_id = landmarks_by_id(landmarks)
    warped_landmarks = []
    for lm in landmarks:
        if not isinstance(lm, dict):
            continue
        px = np.array([
            float(lm["x"]) * width,
            float(lm["y"]) * height,
            1.0,
        ], dtype=np.float32)
        wpt = warp["affine"] @ px
        warped_landmarks.append({
            **lm,
            "x": float(np.clip(wpt[0] / warped_w, 0.0, 1.0)),
            "y": float(np.clip(wpt[1] / warped_h, 0.0, 1.0)),
        })

    corridor = proportional_fate_corridor(warped_landmarks)
    corridor_mask = corridor_mask_from_corridor((warped_h, warped_w), corridor)
    corridor_mask = cv2.bitwise_and(corridor_mask, warped_mask)

    middle = landmarks_by_id(warped_landmarks).get(9, {"x": 0.5, "y": 0.15})
    wrist = landmarks_by_id(warped_landmarks).get(0, {"x": 0.5, "y": 0.85})
    allowed = (warped_mask > 0) & (corridor_mask > 0)
    middle_px = (
        int(np.clip(middle["x"] * warped_w, 0, warped_w - 1)),
        int(np.clip(middle["y"] * warped_h, 0, warped_h - 1)),
    )
    wrist_px = (
        int(np.clip(wrist["x"] * warped_w, 0, warped_w - 1)),
        int(np.clip(wrist["y"] * warped_h, 0, warped_h - 1)),
    )
    middle_px = _snap_to_allowed(allowed, middle_px[0], middle_px[1])
    wrist_px = _snap_to_allowed(allowed, wrist_px[0], wrist_px[1])

    sources = _collect_dynamic_nodes(
        ridge, allowed, corridor, warped_h, warped_w, zone="top", limit=10, percentile=0.58,
    )
    sinks = _collect_dynamic_nodes(
        ridge, allowed, corridor, warped_h, warped_w, zone="bottom", limit=10, percentile=0.52,
    )
    sources = _unique_nodes(sources + [middle_px])
    sinks = _unique_nodes(sinks + [wrist_px])

    span_y = float(corridor["span_y"])
    min_span_ratio = 0.20
    y_start = float(corridor.get("middle_mcp_y") or middle["y"])
    y_end = float(corridor.get("wrist_y") or wrist["y"])

    dynamic_path = dijkstra_multi_source_multi_sink(
        ridge,
        allowed,
        sources,
        sinks,
        corridor_span_y=span_y,
        min_span_ratio=min_span_ratio,
    )
    rigid_path = dijkstra_ridge_path(
        ridge, warped_mask, corridor_mask, middle_px, wrist_px,
    )
    column_path = trace_vertical_ridge_column(
        ridge, allowed, corridor, warped_h, warped_w, y_start=y_start, y_end=y_end,
    )

    path_candidates: list[list[tuple[int, int]]] = []
    for candidate_path in (dynamic_path, rigid_path, column_path):
        if len(candidate_path) < 4:
            continue
        extended = extend_ridge_path_both_ends(
            candidate_path, ridge, allowed, middle_px, wrist_px,
        )
        extended = _ensure_path_endpoints(extended, middle_px, wrist_px, allowed)
        path_candidates.append(extended)

    pixel_path = _pick_best_pixel_path(path_candidates, ridge, warped_h, span_y)
    if len(pixel_path) < 4:
        return None

    step = max(1, len(pixel_path) // 32)
    sampled = pixel_path[::step]
    if pixel_path[-1] not in sampled:
        sampled.append(pixel_path[-1])

    norm_path = [
        _warp_point_to_normalized(float(x), float(y), warp["inverse_affine"], width, height)
        for x, y in sampled
    ]

    ys = [p["y"] for p in norm_path]
    xs = [p["x"] for p in norm_path]
    span = max(corridor["span_y"], 1e-4)
    norm_len = (max(ys) - min(ys)) if ys else 0.0
    axis_x = corridor["fate_axis_x"]
    offset = abs(sum(xs) / max(len(xs), 1) - axis_x)

    remap_check = verify_inverse_remap(
        pixel_path,
        warp["inverse_affine"],
        warp["affine"],
        width,
        height,
        warped_w,
        warped_h,
    )

    return {
        "path": norm_path,
        "normalized_length": round(norm_len, 6),
        "ridge_method": ridge_method,
        "normalization": {
            "affine_warp": True,
            "rotation_deg": round(float(warp["rotation_deg"]), 4),
            "warp_size": list(warp["output_size"]),
            "corridor": corridor,
            "dynamic_graph_endpoints": True,
            "source_nodes": len(sources),
            "sink_nodes": len(sinks),
            "path_span_ratio": round(
                _path_vertical_span_ratio(pixel_path, warped_h, span_y), 4,
            ),
            **remap_check,
        },
        "graph_trace": True,
        "fate_axis_offset": round(offset, 4),
        "coverage_span": round(float(np.clip(norm_len / span, 0.0, 1.2)), 4),
    }
