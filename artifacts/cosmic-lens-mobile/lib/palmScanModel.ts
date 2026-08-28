export const FATE_PIPELINE_REVISION = "image_first_fate_line_detector/v8.2";

export const MAJOR_LINES = [
  "heart_line",
  "head_line",
  "life_line",
  "fate_line",
  "sun_apollo_line",
  "mercury_line",
  "mars_support_line",
] as const;

export const PRIMARY_MAJOR_LINES = [
  "life_line",
  "head_line",
  "heart_line",
  "fate_line",
] as const;

export const SECONDARY_MAJOR_LINES = [
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
  mercury_line: "Mercury Line",
  mars_support_line: "Mars Line",
};

export const LINE_COLORS: Record<string, string> = {
  heart_line: "#ef4444",
  head_line: "#f59e0b",
  life_line: "#22c55e",
  fate_line: "#a855f7",
  sun_apollo_line: "#06b6d4",
  mercury_line: "#eab308",
  mars_support_line: "#fb7185",
};

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

export function str(value: unknown, fallback = ""): string {
  if (value == null || value === "") return fallback;
  return String(value);
}

export const MIN_MAJOR_LINE_PATH_POINTS = 4;

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

export function creaseCandidateById(scan: Dict, candidateId: string): Dict | null {
  const row = asList(asDict(scan.secondary_lines).crease_candidates)
    .map((item) => asDict(item))
    .find((item) => str(item.id, "") === candidateId);
  return row || null;
}

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

export function fateLineWasEvaluated(scan: Dict): boolean {
  const line = asDict(asDict(scan.major_lines).fate_line);
  if (str(line.detection_method)) return true;
  if (str(asDict(scan.metadata).fate_line_pipeline) === "image_first_fate_line_detector") {
    return true;
  }
  return Boolean(str(asDict(asDict(scan.secondary_lines).fate_line_detection).method));
}

/** Lines shown in the tap-to-inspect chip row (includes evaluated but non-detected Fate Line). */
export function majorLineShowsInSelector(scan: Dict, lineId: string): boolean {
  if (lineDetectionInfo(scan, lineId).detected) return true;
  if (lineId === "fate_line" && fateLineWasEvaluated(scan)) return true;
  return majorLineHasContinuousGeometry(scan, lineId);
}

export function masterOf(scan: Dict): Dict {
  return asDict(scan.master_extraction);
}

export function mapPointToDisplay(
  scan: Dict,
  point: { x: number; y: number },
  imageLayer: "original" | "processed" = "original",
): { x: number; y: number } {
  if (imageLayer !== "original") return point;
  const prep = asDict(scan.preprocessing);
  const stages = asDict(prep.stages);
  const resolution = asDict(stages.resolution_normalization);
  const perspective = asDict(stages.perspective_normalization);
  const inputSize = asList(resolution.input_size).map((item) => num(item) ?? 0);
  const outputSize = asList(resolution.output_size).map((item) => num(item) ?? 0);
  const scale = num(resolution.scale) ?? 1;
  const matrixRows = asList(perspective.homography).map((row) =>
    asList(row).map((item) => num(item) ?? 0),
  );
  if (inputSize.length !== 2 || outputSize.length !== 2 || matrixRows.length !== 3) {
    return point;
  }
  const widthOut = outputSize[0] || 1;
  const heightOut = outputSize[1] || 1;
  const widthIn = inputSize[0] || widthOut;
  const heightIn = inputSize[1] || heightOut;
  const matrix = matrixRows.map((row) => [row[0] || 0, row[1] || 0, row[2] || 0]);
  const det =
    matrix[0][0] * (matrix[1][1] * matrix[2][2] - matrix[1][2] * matrix[2][1]) -
    matrix[0][1] * (matrix[1][0] * matrix[2][2] - matrix[1][2] * matrix[2][0]) +
    matrix[0][2] * (matrix[1][0] * matrix[2][1] - matrix[1][1] * matrix[2][0]);
  if (!Number.isFinite(det) || Math.abs(det) < 1e-9) return point;
  const inv = invert3x3(matrix);
  if (!inv) return point;
  const x = point.x * widthOut;
  const y = point.y * heightOut;
  const w = inv[2][0] * x + inv[2][1] * y + inv[2][2];
  if (!Number.isFinite(w) || Math.abs(w) < 1e-9) return point;
  const nx = (inv[0][0] * x + inv[0][1] * y + inv[0][2]) / w;
  const ny = (inv[1][0] * x + inv[1][1] * y + inv[1][2]) / w;
  const ox = nx / Math.max(scale, 1e-9);
  const oy = ny / Math.max(scale, 1e-9);
  return {
    x: Math.min(1, Math.max(0, ox / widthIn)),
    y: Math.min(1, Math.max(0, oy / heightIn)),
  };
}

function invert3x3(m: number[][]) {
  const det =
    m[0][0] * (m[1][1] * m[2][2] - m[1][2] * m[2][1]) -
    m[0][1] * (m[1][0] * m[2][2] - m[1][2] * m[2][0]) +
    m[0][2] * (m[1][0] * m[2][1] - m[1][1] * m[2][0]);
  if (!Number.isFinite(det) || Math.abs(det) < 1e-9) return null;
  const invDet = 1 / det;
  return [
    [
      (m[1][1] * m[2][2] - m[1][2] * m[2][1]) * invDet,
      (m[0][2] * m[2][1] - m[0][1] * m[2][2]) * invDet,
      (m[0][1] * m[1][2] - m[0][2] * m[1][1]) * invDet,
    ],
    [
      (m[1][2] * m[2][0] - m[1][0] * m[2][2]) * invDet,
      (m[0][0] * m[2][2] - m[0][2] * m[2][0]) * invDet,
      (m[0][2] * m[1][0] - m[0][0] * m[1][2]) * invDet,
    ],
    [
      (m[1][0] * m[2][1] - m[1][1] * m[2][0]) * invDet,
      (m[0][1] * m[2][0] - m[0][0] * m[2][1]) * invDet,
      (m[0][0] * m[1][1] - m[0][1] * m[1][0]) * invDet,
    ],
  ];
}

export function displayPoints(
  scan: Dict,
  points: { x: number; y: number }[],
  imageLayer: "original" | "processed" = "original",
) {
  return points.map((point) => mapPointToDisplay(scan, point, imageLayer));
}

export function partialPath(points: { x: number; y: number }[], progress: number) {
  if (progress >= 1 || points.length < 2) return points;
  if (progress <= 0) return [points[0]];
  const totalSegments = points.length - 1;
  const exact = progress * totalSegments;
  const fullSegments = Math.floor(exact);
  const frac = exact - fullSegments;
  const result = points.slice(0, fullSegments + 1);
  if (frac > 0 && fullSegments < totalSegments) {
    const a = points[fullSegments];
    const b = points[fullSegments + 1];
    result.push({
      x: a.x + (b.x - a.x) * frac,
      y: a.y + (b.y - a.y) * frac,
    });
  }
  return result;
}

export function pathToSvgD(points: { x: number; y: number }[]) {
  if (points.length < 2) return "";
  return points
    .map((p, i) => `${i ? "L" : "M"} ${p.x * 1000} ${p.y * 1000}`)
    .join(" ");
}

export function formatMetric(value: unknown, asPercent = true): string {
  const n = num(value);
  if (n == null) return "Not available";
  const pct = asPercent ? (n <= 1 ? n * 100 : n) : n;
  return `${Math.round(pct)}%`;
}

export type LineDetectionInfo = {
  id: string;
  label: string;
  status: string;
  detected: boolean;
  failed: boolean;
  path: { x: number; y: number }[];
  continuity: string;
  confidence: string;
  detectionMethod: string;
  imageSupport: string;
  coverageSpan: string;
  backendStale: boolean;
  backendNeedsRestart: boolean;
  fatePipelineRevision?: string;
  startPoint: { x: number; y: number } | null;
  endPoint: { x: number; y: number } | null;
  branches: { x: number; y: number }[];
  forks: { x: number; y: number }[];
  islands: { x: number; y: number }[];
  breaks: { x: number; y: number }[];
  intersections: { x: number; y: number }[];
};

export function lineDetectionInfo(scan: Dict, lineId: string): LineDetectionInfo {
  const line = asDict(asDict(scan.major_lines)[lineId]);
  const path = resolveMajorLinePath(scan, lineId);
  const status = str(line.status, "unknown");
  const hasContinuousGeometry = path.length >= MIN_MAJOR_LINE_PATH_POINTS;
  const detected =
    hasContinuousGeometry &&
    (status === "detected" ||
      status === "ambiguous" ||
      (lineId === "life_line" && status === "insufficient_evidence" && path.length >= MIN_MAJOR_LINE_PATH_POINTS));
  const failed =
    status === "insufficient_geometry" ||
    (status === "insufficient_evidence" && lineId !== "life_line") ||
    status === "not_detected" ||
    (lineId === "life_line"
      ? status === "unknown" && path.length < MIN_MAJOR_LINE_PATH_POINTS
      : !detected && path.length < MIN_MAJOR_LINE_PATH_POINTS);
  const continuityRaw =
    num(line.continuity) ?? num(asDict(line.measurements).continuity);
  const confidenceRaw = num(line.confidence);
  const startRaw = asDict(line.start_point);
  const endRaw = asDict(line.end_point);
  const endpoints = asList(line.endpoints).map((item) => asDict(item));
  const startPoint =
    pointsOf([startRaw])[0] ||
    (endpoints.length ? pointsOf([endpoints[0]])[0] : path[0] || null);
  const endPoint =
    pointsOf([endRaw])[0] ||
    (endpoints.length > 1 ? pointsOf([endpoints[endpoints.length - 1]])[0] : path[path.length - 1] || null);

  const markPoints = (key: string) =>
    asList(line[key])
      .flatMap((item) => pointsOf([asDict(item).coordinates ?? item]));

  const detectionMethod =
    str(line.detection_method) ||
    str(asDict(asDict(scan.secondary_lines).fate_line_detection).method);
  const fateDebug = asDict(asDict(scan.secondary_lines).fate_line_detection);
  const imageSupportRaw =
    num(line.image_support) ??
    num(asDict(line.measurements).image_support) ??
    num(fateDebug.image_support);
  const coverageSpanRaw =
    num(line.coverage_span) ??
    num(asDict(line.measurements).coverage_span) ??
    num(fateDebug.coverage_span);
  const usesImageFirstFate =
    lineId === "fate_line" && detectionMethod === "image_first_fate_line_detector";
  const fatePipelineRevision =
    str(line.pipeline_revision) ||
    str(fateDebug.pipeline_revision) ||
    str(asDict(scan.metadata).fate_line_pipeline_revision);
  const backendNeedsRestart =
    lineId === "fate_line" &&
    detectionMethod === "image_first_fate_line_detector" &&
    !fatePipelineRevision;
  const backendStale =
    lineId === "fate_line" &&
    detectionMethod === "image_first_fate_line_detector" &&
    Boolean(fatePipelineRevision) &&
    fatePipelineRevision !== FATE_PIPELINE_REVISION;

  return {
    id: lineId,
    label: LINE_LABELS[lineId] || lineId,
    status,
    detected,
    failed,
    path,
    continuity: formatMetric(continuityRaw),
    confidence: formatMetric(confidenceRaw),
    detectionMethod: detectionMethod || "Not available",
    imageSupport: formatMetric(imageSupportRaw),
    coverageSpan: formatMetric(coverageSpanRaw),
    backendStale,
    backendNeedsRestart,
    fatePipelineRevision: fatePipelineRevision || undefined,
    startPoint: startPoint || null,
    endPoint: endPoint || null,
    branches: usesImageFirstFate ? [] : markPoints("branches"),
    forks: usesImageFirstFate ? [] : markPoints("forks"),
    islands: markPoints("islands"),
    breaks: markPoints("breaks"),
    intersections: markPoints("crosses_intersections"),
  };
}

export type LayerPreset = "original" | "lines" | "landmarks" | "markings" | "all";

export const SCAN_PHASES = [
  { id: "hand_detection", label: "Hand Detection" },
  { id: "palm_geometry", label: "Palm Geometry" },
  { id: "major_lines", label: "Major Lines" },
  { id: "secondary_lines", label: "Secondary Lines" },
  { id: "markings", label: "Markings" },
  { id: "verification", label: "Verification" },
] as const;

export type ScanPhaseId = (typeof SCAN_PHASES)[number]["id"];
