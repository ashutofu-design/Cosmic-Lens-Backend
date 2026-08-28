export const MAJOR_LINES = [
  "heart_line",
  "head_line",
  "life_line",
  "fate_line",
  "sun_apollo_line",
  "mercury_line",
  "mars_support_line",
] as const;

export const LINE_LABELS: Record<string, string> = {
  heart_line: "Heart Line",
  head_line: "Head Line",
  life_line: "Life Line",
  fate_line: "Fate Line",
  sun_apollo_line: "Sun / Apollo Line",
  mercury_line: "Mercury / Health Line",
  mars_support_line: "Mars / Inner Mars Line",
};

export const MOUNTS = [
  "Jupiter",
  "Saturn",
  "Sun/Apollo",
  "Mercury",
  "Venus",
  "Moon/Luna",
  "Upper Mars",
  "Lower Mars",
  "Plain of Mars",
] as const;

export const FINGERS = ["index", "middle", "ring", "little"] as const;

export const LAYERS = [
  { id: "original_image", label: "Original image" },
  { id: "raw_crease_evidence", label: "Raw crease evidence" },
  { id: "hand_boundary", label: "Hand boundary" },
  { id: "palm_boundary", label: "Palm boundary" },
  { id: "wrist", label: "Wrist" },
  { id: "palm_center", label: "Palm center" },
  { id: "grid", label: "Coordinate grid" },
  { id: "landmarks", label: "Landmarks" },
  { id: "hand_geometry", label: "Hand geometry" },
  { id: "major_lines", label: "Major lines" },
  { id: "crease_candidates", label: "Raw crease candidates" },
  { id: "accepted_crease_paths", label: "Accepted crease paths" },
  { id: "rejected_candidates", label: "Rejected / ambiguous candidates" },
  { id: "minor_lines", label: "Minor lines" },
  { id: "segments", label: "Line segments" },
  { id: "micro", label: "Branches / forks / islands" },
  { id: "markings", label: "Special markings" },
  { id: "intersections", label: "Intersections" },
  { id: "mounts", label: "Mount boundaries" },
  { id: "fingers", label: "Finger landmarks" },
  { id: "thumb", label: "Thumb landmarks" },
  { id: "rascette", label: "Wrist / Rascette" },
] as const;

export type LayerId = (typeof LAYERS)[number]["id"];

export type Dict = Record<string, unknown>;

export function asDict(value: unknown): Dict {
  return value && typeof value === "object" && !Array.isArray(value) ? (value as Dict) : {};
}

export function asList(value: unknown): unknown[] {
  return Array.isArray(value) ? value : [];
}

export function num(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

export function str(value: unknown, fallback = "—"): string {
  if (value == null || value === "") return fallback;
  return String(value);
}

export function confBand(value: unknown): string {
  const n = num(value);
  if (n == null) return "unknown";
  if (n >= 0.9) return "Very High";
  if (n >= 0.75) return "High";
  if (n >= 0.55) return "Moderate";
  if (n >= 0.35) return "Ambiguous";
  return "Unreliable";
}

export function scanOf(order: Dict, hand: "left" | "right"): Dict {
  return asDict(order[`${hand}_palm_scan_result`]);
}

export function masterOf(scan: Dict): Dict {
  return asDict(scan.master_extraction);
}

export function pointsOf(value: unknown): { x: number; y: number }[] {
  return asList(value)
    .map((item) => {
      const row = asDict(item);
      const x = num(row.x ?? row.normalized_x);
      const y = num(row.y ?? row.normalized_y);
      return x == null || y == null ? null : { x, y };
    })
    .filter((item): item is { x: number; y: number } => item != null);
}

export const MIN_MAJOR_LINE_PATH_POINTS = 4;

export function creaseCandidateById(scan: Dict, candidateId: string): Dict | null {
  const row = asList(asDict(scan.secondary_lines).crease_candidates)
    .map((item) => asDict(item))
    .find((item) => str(item.id, "") === candidateId);
  return row || null;
}

/** Canonical major-line geometry — never substitute endpoints/landmarks for the crease path. */
export function resolveMajorLinePath(scan: Dict, lineName: string): { x: number; y: number }[] {
  const line = asDict(asDict(scan.major_lines)[lineName]);
  let path = pointsOf(line.path);
  if (path.length >= MIN_MAJOR_LINE_PATH_POINTS) return path;

  const candidateId = str(line.source_candidate_id);
  if (candidateId) {
    const candidate = creaseCandidateById(scan, candidateId);
    if (candidate) {
      path = pointsOf(candidate.path);
      if (path.length >= MIN_MAJOR_LINE_PATH_POINTS) return path;
    }
    for (const group of asList(asDict(scan.line_stitching).groups).map((item) => asDict(item))) {
      const ids = asList(group.source_candidate_ids).map((item) => str(item));
      if (!ids.includes(candidateId)) continue;
      path = pointsOf(group.path);
      if (path.length >= 2) return path;
    }
  }
  return path;
}

export function majorLineHasContinuousGeometry(scan: Dict, lineName: string): boolean {
  return resolveMajorLinePath(scan, lineName).length >= MIN_MAJOR_LINE_PATH_POINTS;
}

export function completeness(scan: Dict): { items: { id: string; ok: boolean }[]; pct: number } {
  const quality = asDict(scan.quality);
  const segs = asDict(scan.segmentation);
  const geom = asDict(scan.palm_geometry);
  const lines = asDict(scan.major_lines);
  const mounts = asDict(scan.mounts);
  const fingers = asDict(scan.fingers);
  const items = [
    { id: "image quality", ok: quality.usable === true },
    { id: "segmentation", ok: asDict(segs.palm_region).status === "detected" },
    { id: "landmarks", ok: asList(scan.landmarks).length >= 21 },
    { id: "palm geometry", ok: asDict(geom.width).status === "detected" },
    {
      id: "major lines",
      ok: Object.values(lines).some((line) => asDict(line).status === "detected"),
    },
    { id: "minor lines", ok: asDict(scan.union_lines).status !== "unknown" },
    {
      id: "mounts",
      ok: Object.values(mounts).some((mount) => asDict(mount).status === "detected"),
    },
    {
      id: "fingers",
      ok: FINGERS.every((name) => asDict(fingers[name]).status === "detected"),
    },
    { id: "thumb", ok: asDict(scan.thumb).status === "detected" },
    { id: "wrist", ok: asDict(segs.wrist).status === "detected" },
    { id: "markings", ok: asList(asDict(scan.special_markings).candidates).length >= 0 },
    { id: "intersections", ok: asList(masterOf(scan).line_relationships).length > 0 },
    { id: "relationships", ok: asList(masterOf(scan).line_relationships).some((row) => asDict(row).status === "detected") },
  ];
  const ok = items.filter((item) => item.ok).length;
  return { items, pct: Math.round((ok / items.length) * 100) };
}

export function caseStatus(order: Dict, left: Dict, right: Dict): string {
  const human = str(order.status, "");
  if (human === "human_verified") return "HUMAN VERIFIED";
  if (asDict(left.quality).usable === false || asDict(right.quality).usable === false) {
    return "RETAKE REQUIRED";
  }
  if (!Object.keys(left).length || !Object.keys(right).length) return "PARTIAL";
  if (asDict(left.hand).status !== "detected" || asDict(right.hand).status !== "detected") {
    return "FAILED";
  }
  const leftC = completeness(left).pct;
  const rightC = completeness(right).pct;
  if (leftC >= 70 && rightC >= 70) return "COMPLETE";
  return "PARTIAL";
}

export function qualityGate(scan: Dict): { label: "PASS" | "WARNING" | "FAIL"; reasons: string[] } {
  const quality = asDict(scan.quality);
  const issues = asList(quality.issues).map((item) => asDict(item));
  const errors = issues.filter((item) => item.severity === "error");
  const warnings = issues.filter((item) => item.severity === "warning");
  if (quality.usable === false || errors.length) {
    return {
      label: "FAIL",
      reasons: errors.map((item) => str(item.message || item.code)),
    };
  }
  if (warnings.length) {
    return {
      label: "WARNING",
      reasons: warnings.map((item) => str(item.message || item.code)),
    };
  }
  return { label: "PASS", reasons: ["Quality gate passed"] };
}

export function metricRows(scan: Dict): { key: string; value: string }[] {
  const quality = asDict(scan.quality);
  const metrics = asDict(quality.metrics);
  const dims = asDict(metrics.dimensions);
  const resolution = asDict(metrics.resolution);
  const blur = asDict(metrics.blur);
  const brightness = asDict(metrics.brightness);
  const contrast = asDict(metrics.contrast);
  const glare = asDict(metrics.glare);
  const shadows = asDict(metrics.shadows);
  const compression = asDict(metrics.compression);
  const palm = asDict(metrics.palm_visibility);
  const finger = asDict(metrics.finger_visibility);
  const thumb = asDict(metrics.thumb_visibility);
  const wrist = asDict(metrics.wrist_visibility);
  const crop = asDict(metrics.cropping);
  const rotation = asDict(metrics.rotation || metrics.orientation);
  return [
    ["resolution", str(resolution.megapixels) + " MP"],
    ["width", str(dims.width_px) + " px"],
    ["height", str(dims.height_px) + " px"],
    ["blur score", str(blur.laplacian_variance)],
    ["sharpness", str(quality.blur_score)],
    ["brightness", str(brightness.mean_luma)],
    ["contrast", str(contrast.luma_stddev)],
    ["exposure", str(quality.lighting_score)],
    ["glare", str(glare.highlight_fraction)],
    ["shadow level", str(shadows.dark_fraction)],
    ["compression quality", str(compression.laplacian_variance)],
    ["hand visibility", str(asDict(scan.hand).status)],
    ["palm visibility", str(palm.visible ?? palm.status)],
    ["finger visibility", str(finger.all_tips_visible ?? finger.status)],
    ["thumb visibility", str(thumb.visible ?? thumb.status)],
    ["wrist visibility", str(wrist.visible ?? wrist.status)],
    ["cropping", str(crop.palm_inside_frame ?? crop.status)],
    ["rotation", str(rotation.angle_from_vertical_deg) + "°"],
    ["perspective distortion", str(asDict(metrics.perspective).reason || asDict(metrics.perspective).status)],
    ["occlusion", str(asDict(metrics.occlusion).reason || asDict(metrics.occlusion).status)],
    ["background interference", str(asDict(metrics.background_interference).reason || asDict(metrics.background_interference).status)],
    ["overall image quality score", str(quality.score ?? quality.overall_score)],
  ].map(([key, value]) => ({ key, value }));
}
