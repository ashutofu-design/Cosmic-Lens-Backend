import { Feather } from "@expo/vector-icons";
import React, { useMemo, useState } from "react";
import {
  Image,
  Pressable,
  StyleSheet,
  Text,
  View,
} from "react-native";
import Svg, { Circle, Path, Polygon } from "react-native-svg";

import {
  asDict,
  asList,
  displayPoints,
  FATE_PIPELINE_REVISION,
  lineDetectionInfo,
  LINE_COLORS,
  LINE_LABELS,
  majorLineHasContinuousGeometry,
  mapPointToDisplay,
  num,
  partialPath,
  pathToSvgD,
  pointsOf,
  PRIMARY_MAJOR_LINES,
  resolveMajorLinePath,
  SCAN_PHASES,
  SECONDARY_MAJOR_LINES,
  str,
  type Dict,
  type LayerPreset,
} from "@/lib/palmScanModel";
import {
  collectDetectedLines,
  useLivePalmScanSequence,
  validationLabel,
} from "@/lib/palmLiveScanSequence";

const ACCENT = "#14b8a6";

type Props = {
  imageUri: string;
  scan: Dict;
  handLabel: string;
  theme: {
    text: string;
    textMuted: string;
    bgCard: string;
    bgCard2: string;
    border: string;
  };
  onRetake?: () => void;
  onContinue?: () => void;
  /** Internal CV / validation controls — hidden from end users by default. */
  showDebugUI?: boolean;
};

const LAYER_PRESETS: { id: LayerPreset; label: string }[] = [
  { id: "original", label: "Original" },
  { id: "lines", label: "Lines" },
  { id: "landmarks", label: "Landmarks" },
  { id: "markings", label: "Markings" },
  { id: "all", label: "All" },
];

function phaseIcon(status: string) {
  if (status === "complete") return "✓";
  if (status === "active") return "●";
  if (status === "failed") return "✕";
  return "○";
}

function creasePathById(scan: Dict, creaseKey: string): { x: number; y: number }[] {
  const id = creaseKey.replace(/^crease:/, "");
  const row = asList(asDict(scan.secondary_lines).crease_candidates)
    .map((item) => asDict(item))
    .find((item) => str(item.id) === id);
  return row ? pointsOf(row.path) : [];
}

export function LivePalmScanView({
  imageUri,
  scan,
  handLabel,
  theme,
  onRetake,
  onContinue,
  showDebugUI = false,
}: Props) {
  const live = useLivePalmScanSequence(scan);
  const [layerPreset, setLayerPreset] = useState<LayerPreset>(showDebugUI ? "all" : "lines");
  const [selectedLineId, setSelectedLineId] = useState<string | null>(null);

  const validation = useMemo(() => validationLabel(scan), [scan]);
  const detectedLines = useMemo(() => collectDetectedLines(scan), [scan]);
  const selectedInfo = selectedLineId
    ? detectedLines.find((row) => row.id === selectedLineId) ||
      (selectedLineId.startsWith("crease:")
        ? null
        : lineDetectionInfo(scan, selectedLineId))
    : null;

  const showBoundary =
    live.phaseStatuses.hand_detection !== "pending" &&
    (layerPreset === "landmarks" || layerPreset === "all" || !live.interactive);
  const showLandmarks =
    live.phaseStatuses.palm_geometry !== "pending" &&
    (layerPreset === "landmarks" || layerPreset === "all" || !live.interactive);
  const showLines =
    live.phaseStatuses.major_lines !== "pending" &&
    (layerPreset === "lines" || layerPreset === "all" || !live.interactive || !showDebugUI);
  const showMarkings =
    live.phaseStatuses.markings !== "pending" &&
    (layerPreset === "markings" || layerPreset === "all" || !live.interactive);

  const segs = asDict(scan.segmentation);
  const landmarks = asList(scan.landmarks).map((item) => asDict(item));
  const mounts = asDict(scan.mounts);
  const master = asDict(scan.master_extraction);
  const micro = asList(master.line_micro_features).map((item) => asDict(item));
  const relationships = asList(master.line_relationships).map((item) => asDict(item));
  const markings = asList(asDict(scan.special_markings).candidates).map((item) => asDict(item));
  const geom = asDict(scan.palm_geometry);
  const center = asList(asDict(geom.center).normalized).map((item) => num(item) ?? 0);

  function linePath(lineId: string) {
    if (lineId.startsWith("crease:")) return creasePathById(scan, lineId);
    return resolveMajorLinePath(scan, lineId);
  }

  function renderPolyline(
    rawPoints: { x: number; y: number }[],
    key: string,
    color: string,
    progress = 1,
    strokeWidth = 4,
    highlight = false,
  ) {
    const mapped = displayPoints(scan, rawPoints);
    const shown = progress < 1 ? partialPath(mapped, progress) : mapped;
    const d = pathToSvgD(shown);
    if (!d) return null;
    return (
      <Path
        key={key}
        d={d}
        fill="none"
        stroke={color}
        strokeWidth={highlight ? strokeWidth + 3 : strokeWidth}
        strokeLinecap="round"
        strokeLinejoin="round"
        opacity={live.interactive && !highlight && selectedLineId ? 0.35 : 1}
      />
    );
  }

  function renderPoint(
    point: { x: number; y: number },
    key: string,
    color: string,
    radius = 5,
  ) {
    const mapped = mapPointToDisplay(scan, point);
    return (
      <Circle
        key={key}
        cx={mapped.x * 1000}
        cy={mapped.y * 1000}
        r={radius}
        fill={color}
      />
    );
  }

  const majorLineIds = [...PRIMARY_MAJOR_LINES, ...SECONDARY_MAJOR_LINES];
  const hand = asDict(scan.hand);
  const qualityScore = num(asDict(scan.quality).score) ?? num(asDict(scan.quality).overall_score);
  const scanConf = num(asDict(scan.scan_confidence).overall);

  return (
    <View style={[styles.root, { backgroundColor: theme.bgCard, borderColor: theme.border }]}>
      <View style={styles.scanHeader}>
        <Text style={[styles.scanTitle, { color: theme.text }]}>
          {showDebugUI ? "LIVE PALM SCAN" : "Palm Scan"}
        </Text>
        <Text style={[styles.scanSub, { color: theme.textMuted }]}>
          {showDebugUI ? `Analysing your palm structure · ${handLabel}` : handLabel}
        </Text>
      </View>

      {showDebugUI ? (
        <View style={[styles.handMeta, { backgroundColor: theme.bgCard2 }]}>
          <Text style={[styles.handMetaText, { color: theme.textMuted }]}>
            Hand: {str(hand.side, "Not available")} · Detector confidence:{" "}
            {num(hand.confidence) != null
              ? `${Math.round((num(hand.confidence) as number) * 100)}%`
              : "Not available"}
          </Text>
          <Text style={[styles.handMetaText, { color: theme.textMuted }]}>
            Orientation: {str(hand.orientation ?? hand.palm_orientation, "Not available")}
          </Text>
        </View>
      ) : null}

      <View style={styles.viewport}>
        <Image source={{ uri: imageUri }} style={styles.baseImage} resizeMode="contain" />
        <Svg
          style={StyleSheet.absoluteFill}
          viewBox="0 0 1000 1000"
          preserveAspectRatio="xMidYMid meet"
        >
          {showBoundary
            ? renderPolyline(
                pointsOf(asDict(segs.hand_boundary).polygon),
                "hand-boundary",
                "#94a3b8",
                live.boundaryReveal,
                3,
              )
            : null}
          {showBoundary
            ? renderPolyline(
                pointsOf(asDict(segs.palm_region).polygon),
                "palm-boundary",
                "#e2e8f0",
                live.boundaryReveal,
                3,
              )
            : null}
          {showBoundary
            ? renderPolyline(
                pointsOf(asDict(segs.wrist).polygon),
                "wrist",
                "#67e8f9",
                live.boundaryReveal,
                2,
              )
            : null}

          {showLandmarks && center.length === 2
            ? (() => {
                const point = mapPointToDisplay(scan, { x: center[0], y: center[1] });
                return (
                  <Circle
                    cx={point.x * 1000}
                    cy={point.y * 1000}
                    r={8 * live.geometryReveal}
                    fill="#f8fafc"
                  />
                );
              })()
            : null}

          {showLandmarks
            ? landmarks.map((lm) => {
                const raw = mapPointToDisplay(scan, {
                  x: num(lm.x) || 0,
                  y: num(lm.y) || 0,
                });
                return (
                  <Circle
                    key={String(lm.id)}
                    cx={raw.x * 1000}
                    cy={raw.y * 1000}
                    r={5 * live.landmarksReveal}
                    fill="#4ade80"
                  />
                );
              })
            : null}

          {showLines
            ? majorLineIds.map((lineId) => {
                const path = linePath(lineId);
                if (path.length < 2) return null;
                const progress = live.lineProgress[lineId] ?? (live.interactive ? 1 : 0);
                const cardVisible =
                  live.lineCards.some((c) => c.lineId === lineId && c.visible) || live.interactive;
                if (!cardVisible && progress <= 0) return null;
                const highlight = selectedLineId === lineId || live.activeLineId === lineId;
                return renderPolyline(
                  path,
                  lineId,
                  LINE_COLORS[lineId] || "#fff",
                  progress,
                  4,
                  highlight,
                );
              })
            : null}

          {showLines
            ? live.lineCards
                .filter((c) => c.lineId.startsWith("crease:"))
                .map((card) => {
                  const path = linePath(card.lineId);
                  if (path.length < 2) return null;
                  const progress = live.lineProgress[card.lineId] ?? (live.interactive ? 1 : 0);
                  if (!card.visible && progress <= 0) return null;
                  const highlight =
                    selectedLineId === card.lineId || live.activeLineId === card.lineId;
                  return renderPolyline(
                    path,
                    card.lineId,
                    "#22c55e",
                    progress,
                    3,
                    highlight,
                  );
                })
            : null}

          {showMarkings
            ? detectedLines.flatMap((line) => {
                const progress = live.lineProgress[line.id] ?? 1;
                if (progress < 1 && !live.interactive) return [];
                const items = [
                  ...line.branches.map((p, i) =>
                    renderPoint(p, `${line.id}-branch-${i}`, "#fbbf24", 4 * live.markingsReveal),
                  ),
                  ...line.forks.map((p, i) =>
                    renderPoint(p, `${line.id}-fork-${i}`, "#fb923c", 4 * live.markingsReveal),
                  ),
                  ...line.islands.map((p, i) =>
                    renderPoint(p, `${line.id}-island-${i}`, "#a78bfa", 4 * live.markingsReveal),
                  ),
                  ...line.breaks.map((p, i) =>
                    renderPoint(p, `${line.id}-break-${i}`, "#f87171", 4 * live.markingsReveal),
                  ),
                  ...line.intersections.map((p, i) =>
                    renderPoint(p, `${line.id}-ix-${i}`, "#22d3ee", 5 * live.markingsReveal),
                  ),
                ];
                return items;
              })
            : null}

          {showMarkings
            ? micro.map((item, i) => {
                const c = asDict(item.coordinates);
                const raw = mapPointToDisplay(scan, { x: num(c.x) || 0, y: num(c.y) || 0 });
                return (
                  <Circle
                    key={`micro-${i}`}
                    cx={raw.x * 1000}
                    cy={raw.y * 1000}
                    r={5 * live.markingsReveal}
                    fill="#fbbf24"
                  />
                );
              })
            : null}

          {showMarkings
            ? relationships.map((item, i) => {
                const coords = asDict(item.coordinates);
                if (num(coords.x) == null || num(coords.y) == null) return null;
                const mapped = mapPointToDisplay(scan, {
                  x: num(coords.x) || 0,
                  y: num(coords.y) || 0,
                });
                return (
                  <Circle
                    key={`rel-${i}`}
                    cx={mapped.x * 1000}
                    cy={mapped.y * 1000}
                    r={6 * live.markingsReveal}
                    fill="#22d3ee"
                  />
                );
              })
            : null}

          {showMarkings
            ? markings.map((item, i) => {
                const coords = asList(item.coordinates);
                const point = asDict(coords[0] || item.location || item);
                const mapped = mapPointToDisplay(scan, {
                  x: num(point.x) || 0,
                  y: num(point.y) || 0,
                });
                const x = mapped.x * 1000;
                const y = mapped.y * 1000;
                const s = live.markingsReveal;
                return (
                  <Polygon
                    key={`mk-${i}`}
                    points={`${x},${y - 8 * s} ${x + 8 * s},${y + 6 * s} ${x - 8 * s},${y + 6 * s}`}
                    fill="#fb7185"
                  />
                );
              })
            : null}

          {showMarkings && layerPreset === "all"
            ? Object.entries(mounts).flatMap(([name, value]) => {
                const poly = pointsOf(asDict(value).region_polygon);
                if (poly.length < 2) return [];
                return [
                  renderPolyline(poly, `mount-${name}`, "#c084fc", live.markingsReveal, 2),
                ];
              })
            : null}

          {selectedInfo && selectedInfo.path.length >= 2
            ? renderPolyline(
                selectedInfo.path,
                "selected-line-highlight",
                LINE_COLORS[selectedInfo.id] || ACCENT,
                1,
                6,
                true,
              )
            : null}
          {selectedInfo?.startPoint && selectedInfo.path.length >= 2
            ? renderPoint(selectedInfo.startPoint, "sel-start", "#34d399", 6)
            : null}
          {selectedInfo?.endPoint && selectedInfo.path.length >= 2
            ? renderPoint(selectedInfo.endPoint, "sel-end", "#f87171", 6)
            : null}
        </Svg>
      </View>

      {showDebugUI ? (
        <View style={[styles.phasePanel, { backgroundColor: theme.bgCard2 }]}>
          {SCAN_PHASES.map((phase) => {
            const status = live.phaseStatuses[phase.id];
            const active = status === "active";
            return (
              <View key={phase.id} style={styles.phaseRow}>
                <Text
                  style={[
                    styles.phaseIcon,
                    {
                      color:
                        status === "complete"
                          ? "#34d399"
                          : status === "failed"
                            ? "#f87171"
                            : active
                              ? ACCENT
                              : theme.textMuted,
                    },
                    active ? styles.phaseIconPulse : null,
                  ]}
                >
                  {phaseIcon(status)}
                </Text>
                <Text
                  style={[
                    styles.phaseLabel,
                    {
                      color: active ? theme.text : theme.textMuted,
                      fontFamily: active ? "Nunito_700Bold" : "Nunito_400Regular",
                    },
                  ]}
                >
                  {phase.label}
                </Text>
              </View>
            );
          })}
        </View>
      ) : live.scanEnded && !live.scanComplete ? (
        <View style={[styles.failBox, { backgroundColor: theme.bgCard2 }]}>
          <Feather name="info" size={16} color="#fbbf24" />
          <Text style={[styles.failText, { color: theme.textMuted }]}>
            Photo quality low — try again with clearer lighting and full palm visible.
          </Text>
        </View>
      ) : null}

      {showDebugUI
        ? live.phaseFailures.map((failure) => (
            <View key={failure.phaseId} style={styles.failBox}>
              <Feather name="x-circle" size={16} color="#f87171" />
              <Text style={styles.failText}>{failure.message}</Text>
            </View>
          ))
        : null}

      {showDebugUI && live.interactive ? (
        <>
          <View style={styles.layerRow}>
            {LAYER_PRESETS.map((preset) => (
              <Pressable
                key={preset.id}
                onPress={() => setLayerPreset(preset.id)}
                style={[
                  styles.layerChip,
                  {
                    borderColor: layerPreset === preset.id ? ACCENT : theme.border,
                    backgroundColor:
                      layerPreset === preset.id ? `${ACCENT}22` : theme.bgCard2,
                  },
                ]}
              >
                <Text
                  style={{
                    color: layerPreset === preset.id ? ACCENT : theme.textMuted,
                    fontSize: 11,
                    fontFamily: "Nunito_600SemiBold",
                  }}
                >
                  {preset.label}
                </Text>
              </Pressable>
            ))}
          </View>

          <View style={styles.lineTapRow}>
            {detectedLines.map((line) => (
              <Pressable
                key={line.id}
                onPress={() =>
                  setSelectedLineId((current) => (current === line.id ? null : line.id))
                }
                style={[
                  styles.lineTapChip,
                  {
                    borderColor:
                      selectedLineId === line.id
                        ? LINE_COLORS[line.id] || ACCENT
                        : theme.border,
                    backgroundColor: theme.bgCard2,
                  },
                ]}
              >
                <Text style={{ color: theme.text, fontSize: 11, fontFamily: "Nunito_600SemiBold" }}>
                  {LINE_LABELS[line.id] || line.id}
                </Text>
              </Pressable>
            ))}
          </View>

          {selectedInfo ? (
            <View style={[styles.detailBox, { backgroundColor: theme.bgCard2 }]}>
              <Text style={[styles.detailTitle, { color: theme.text }]}>
                {selectedInfo.label}
              </Text>
              <Text style={[styles.detailLine, { color: theme.textMuted }]}>
                Status: {selectedInfo.status}
                {selectedInfo.failed ? " (weak / not confirmed)" : ""}
              </Text>
              <Text style={[styles.detailLine, { color: theme.textMuted }]}>
                Confidence: {selectedInfo.confidence}
              </Text>
              {selectedInfo.id === "fate_line" ? (
                <>
                  {selectedInfo.backendNeedsRestart ? (
                    <Text style={[styles.detailLine, { color: "#f87171" }]}>
                      Backend missing pipeline revision — upload engine.py +
                      fate_line_detector.py (v5) and run: pm2 restart cosmic-api
                    </Text>
                  ) : null}
                  {selectedInfo.backendStale ? (
                    <Text style={[styles.detailLine, { color: "#f87171" }]}>
                      Backend outdated ({selectedInfo.fatePipelineRevision}) — need{" "}
                      {FATE_PIPELINE_REVISION}. Upload from laptop then restart API.
                    </Text>
                  ) : null}
                  <Text style={[styles.detailLine, { color: theme.textMuted }]}>
                    Method: {selectedInfo.detectionMethod}
                  </Text>
                  {selectedInfo.fatePipelineRevision ? (
                    <Text style={[styles.detailLine, { color: theme.textMuted }]}>
                      Pipeline: {selectedInfo.fatePipelineRevision}
                    </Text>
                  ) : null}
                  <Text style={[styles.detailLine, { color: theme.textMuted }]}>
                    Image support: {selectedInfo.imageSupport}
                  </Text>
                  <Text style={[styles.detailLine, { color: theme.textMuted }]}>
                    Coverage: {selectedInfo.coverageSpan}
                  </Text>
                  <Text style={[styles.detailLine, { color: theme.textMuted }]}>
                    Branches: Not validated
                  </Text>
                  <Text style={[styles.detailLine, { color: theme.textMuted }]}>
                    Forks: Not validated
                  </Text>
                </>
              ) : (
                <>
                  <Text style={[styles.detailLine, { color: theme.textMuted }]}>
                    Continuity: {selectedInfo.continuity}
                  </Text>
                  <Text style={[styles.detailLine, { color: theme.textMuted }]}>
                    Branches: {selectedInfo.branches.length || "Not available"}
                  </Text>
                  <Text style={[styles.detailLine, { color: theme.textMuted }]}>
                    Forks: {selectedInfo.forks.length || "Not available"}
                  </Text>
                </>
              )}
              <Text style={[styles.detailLine, { color: theme.textMuted }]}>
                Breaks: {selectedInfo.breaks.length || "Not available"}
              </Text>
            </View>
          ) : null}
        </>
      ) : null}

      {showDebugUI ? (
        <View style={[styles.validationBox, { backgroundColor: theme.bgCard2 }]}>
          <Text style={[styles.validationTitle, { color: theme.text }]}>
            Production Validation
          </Text>
          <Text
            style={[
              styles.validationStatus,
              {
                color:
                  validation.tone === "verified"
                    ? "#34d399"
                    : validation.tone === "rejected"
                      ? "#f87171"
                      : theme.textMuted,
              },
            ]}
          >
            {validation.tone === "verified" ? "✓" : validation.tone === "rejected" ? "✕" : "⏳"}{" "}
            {validation.label}
          </Text>
          <Text style={[styles.validationMsg, { color: theme.textMuted }]}>
            {validation.message}
          </Text>
          <View style={styles.metricRow}>
            <Text style={[styles.metricChip, { color: theme.textMuted }]}>
              Hand: {str(hand.side, "Not available")}
            </Text>
            <Text style={[styles.metricChip, { color: theme.textMuted }]}>
              Landmarks: {landmarks.length}/21
            </Text>
            <Text style={[styles.metricChip, { color: theme.textMuted }]}>
              Quality: {qualityScore != null ? `${Math.round(qualityScore * 100)}%` : "Not available"}
            </Text>
            <Text style={[styles.metricChip, { color: theme.textMuted }]}>
              Confidence: {scanConf != null ? `${Math.round(scanConf * 100)}%` : "Not available"}
            </Text>
          </View>
        </View>
      ) : null}

      {live.scanEnded ? (
        <View style={styles.completeBlock}>
          {live.scanComplete ? (
            <Text style={[styles.completeTitle, { color: "#34d399" }]}>
              {showDebugUI ? "PALM SCAN COMPLETE ✓" : "Palm scan complete ✓"}
            </Text>
          ) : null}
          {onRetake ? (
            <Pressable onPress={onRetake} style={[styles.actionBtn, styles.secondaryBtn]}>
              <Feather name="upload" size={16} color={theme.text} />
              <Text style={[styles.actionBtnText, { color: theme.text }]}>
                {showDebugUI ? "Upload Another Image" : "Retake photo"}
              </Text>
            </Pressable>
          ) : null}
          {onContinue &&
          live.scanComplete &&
          (showDebugUI ? validation.tone === "verified" : true) ? (
            <Pressable onPress={onContinue} style={[styles.actionBtn, styles.primaryBtn]}>
              <Feather name="arrow-right" size={16} color="#fff" />
              <Text style={[styles.actionBtnText, { color: "#fff" }]}>
                Continue to Palm Reading
              </Text>
            </Pressable>
          ) : null}
        </View>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  root: {
    borderWidth: 1,
    borderRadius: 18,
    padding: 14,
    gap: 12,
  },
  scanHeader: { gap: 4 },
  scanTitle: {
    fontSize: 13,
    letterSpacing: 1.2,
    fontFamily: "Nunito_700Bold",
  },
  scanSub: { fontSize: 12, fontFamily: "Nunito_400Regular" },
  handMeta: { borderRadius: 10, padding: 8, gap: 2 },
  handMetaText: { fontSize: 11, fontFamily: "Nunito_400Regular" },
  viewport: {
    width: "100%",
    aspectRatio: 1,
    borderRadius: 14,
    overflow: "hidden",
    backgroundColor: "#0f172a",
  },
  baseImage: {
    ...StyleSheet.absoluteFillObject,
    width: "100%",
    height: "100%",
  },
  phasePanel: {
    borderRadius: 12,
    padding: 10,
    gap: 6,
  },
  phaseRow: { flexDirection: "row", alignItems: "center", gap: 10 },
  phaseIcon: { width: 18, fontSize: 13, fontFamily: "Nunito_700Bold" },
  phaseIconPulse: { opacity: 0.85 },
  phaseLabel: { fontSize: 12 },
  cardsWrap: { gap: 8 },
  lineCard: {
    borderWidth: 1,
    borderRadius: 10,
    padding: 10,
    gap: 2,
  },
  lineCardTitle: { fontSize: 11, letterSpacing: 0.8, fontFamily: "Nunito_700Bold" },
  lineCardMeta: { fontSize: 12, fontFamily: "Nunito_600SemiBold" },
  lineCardDetail: { fontSize: 11, fontFamily: "Nunito_400Regular" },
  failBox: {
    flexDirection: "row",
    alignItems: "flex-start",
    gap: 8,
    padding: 10,
    borderRadius: 10,
    backgroundColor: "rgba(239,68,68,0.12)",
  },
  failText: { flex: 1, color: "#fca5a5", fontSize: 12, fontFamily: "Nunito_400Regular" },
  layerRow: { flexDirection: "row", flexWrap: "wrap", gap: 6 },
  layerChip: {
    borderWidth: 1,
    borderRadius: 999,
    paddingHorizontal: 10,
    paddingVertical: 6,
  },
  lineTapRow: { flexDirection: "row", flexWrap: "wrap", gap: 6 },
  lineTapChip: {
    borderWidth: 1,
    borderRadius: 8,
    paddingHorizontal: 8,
    paddingVertical: 6,
  },
  detailBox: { borderRadius: 10, padding: 10, gap: 4 },
  detailTitle: { fontSize: 13, fontFamily: "Nunito_700Bold" },
  detailLine: { fontSize: 11, fontFamily: "Nunito_400Regular" },
  validationBox: { borderRadius: 12, padding: 10, gap: 4 },
  validationTitle: { fontSize: 12, fontFamily: "Nunito_700Bold" },
  validationStatus: { fontSize: 13, fontFamily: "Nunito_600SemiBold" },
  validationMsg: { fontSize: 11, fontFamily: "Nunito_400Regular" },
  metricRow: { flexDirection: "row", flexWrap: "wrap", gap: 8, marginTop: 4 },
  metricChip: { fontSize: 10, fontFamily: "Nunito_400Regular" },
  completeBlock: { gap: 8 },
  completeTitle: {
    fontSize: 12,
    letterSpacing: 0.6,
    fontFamily: "Nunito_700Bold",
    textAlign: "center",
  },
  actionBtn: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
    borderRadius: 12,
    paddingVertical: 12,
  },
  primaryBtn: { backgroundColor: ACCENT },
  secondaryBtn: { backgroundColor: "rgba(148,163,184,0.15)" },
  actionBtnText: { fontSize: 13, fontFamily: "Nunito_600SemiBold" },
});
