import { useCallback, useEffect, useRef, useState } from "react";

import {
  asDict,
  asList,
  lineDetectionInfo,
  num,
  pointsOf,
  PRIMARY_MAJOR_LINES,
  resolveMajorLinePath,
  majorLineHasContinuousGeometry,
  majorLineShowsInSelector,
  fateLineWasEvaluated,
  ScanPhaseId,
  SCAN_PHASES,
  SECONDARY_MAJOR_LINES,
  str,
  type Dict,
  type LineDetectionInfo,
} from "./palmScanModel";

export type PhaseStatus = "pending" | "active" | "complete" | "failed";

export type LineCard = {
  lineId: string;
  label: string;
  detected: boolean;
  failed: boolean;
  continuity: string;
  confidence: string;
  visible: boolean;
};

export type LiveScanState = {
  phaseIndex: number;
  phaseStatuses: Record<ScanPhaseId, PhaseStatus>;
  lineProgress: Record<string, number>;
  lineCards: LineCard[];
  interactive: boolean;
  scanComplete: boolean;
  scanEnded: boolean;
  activeLineId: string | null;
  phaseFailures: { phaseId: ScanPhaseId; message: string }[];
  geometryReveal: number;
  boundaryReveal: number;
  landmarksReveal: number;
  markingsReveal: number;
};

const REQUIRED_MAJOR_LINES = ["life_line", "head_line", "heart_line"] as const;

function initialPhaseStatuses(): Record<ScanPhaseId, PhaseStatus> {
  return {
    hand_detection: "pending",
    palm_geometry: "pending",
    major_lines: "pending",
    secondary_lines: "pending",
    markings: "pending",
    verification: "pending",
  };
}

function lineAnimateMs(pathLen: number) {
  return Math.min(1400, Math.max(500, pathLen * 18));
}

function easeOut(t: number) {
  return 1 - (1 - t) ** 2;
}

export function useLivePalmScanSequence(scan: Dict | null): LiveScanState {
  const [phaseIndex, setPhaseIndex] = useState(0);
  const [phaseStatuses, setPhaseStatuses] = useState(initialPhaseStatuses);
  const [lineProgress, setLineProgress] = useState<Record<string, number>>({});
  const [lineCards, setLineCards] = useState<LineCard[]>([]);
  const [interactive, setInteractive] = useState(false);
  const [scanComplete, setScanComplete] = useState(false);
  const [scanEnded, setScanEnded] = useState(false);
  const [activeLineId, setActiveLineId] = useState<string | null>(null);
  const [phaseFailures, setPhaseFailures] = useState<{ phaseId: ScanPhaseId; message: string }[]>([]);
  const [geometryReveal, setGeometryReveal] = useState(0);
  const [boundaryReveal, setBoundaryReveal] = useState(0);
  const [landmarksReveal, setLandmarksReveal] = useState(0);
  const [markingsReveal, setMarkingsReveal] = useState(0);

  const rafRef = useRef<number | null>(null);
  const timersRef = useRef<ReturnType<typeof setTimeout>[]>([]);

  const clearTimers = useCallback(() => {
    timersRef.current.forEach(clearTimeout);
    timersRef.current = [];
    if (rafRef.current != null) {
      cancelAnimationFrame(rafRef.current);
      rafRef.current = null;
    }
  }, []);

  const markPhase = useCallback((id: ScanPhaseId, status: PhaseStatus) => {
    setPhaseStatuses((current) => ({ ...current, [id]: status }));
  }, []);

  const failPhase = useCallback((id: ScanPhaseId, message: string) => {
    markPhase(id, "failed");
    setPhaseFailures((current) => [...current.filter((f) => f.phaseId !== id), { phaseId: id, message }]);
    markPhase("verification", "complete");
    setScanEnded(true);
    setInteractive(true);
  }, [markPhase]);

  const animateScalar = useCallback(
    (setter: (value: number) => void, durationMs: number, onDone?: () => void) => {
      const start = performance.now();
      const tick = (now: number) => {
        const t = Math.min(1, (now - start) / durationMs);
        setter(easeOut(t));
        if (t < 1) {
          rafRef.current = requestAnimationFrame(tick);
        } else {
          rafRef.current = null;
          onDone?.();
        }
      };
      rafRef.current = requestAnimationFrame(tick);
    },
    [],
  );

  const animateLine = useCallback(
    (lineId: string, durationMs: number, onDone?: () => void) => {
      const start = performance.now();
      const tick = (now: number) => {
        const t = Math.min(1, (now - start) / durationMs);
        setLineProgress((current) => ({ ...current, [lineId]: easeOut(t) }));
        if (t < 1) {
          rafRef.current = requestAnimationFrame(tick);
        } else {
          rafRef.current = null;
          onDone?.();
        }
      };
      rafRef.current = requestAnimationFrame(tick);
    },
    [],
  );

  useEffect(() => {
    if (!scan) return undefined;
    clearTimers();
    setPhaseIndex(0);
    setPhaseStatuses(initialPhaseStatuses());
    setLineProgress({});
    setLineCards([]);
    setInteractive(false);
    setScanComplete(false);
    setScanEnded(false);
    setActiveLineId(null);
    setPhaseFailures([]);
    setGeometryReveal(0);
    setBoundaryReveal(0);
    setLandmarksReveal(0);
    setMarkingsReveal(0);

    const hand = asDict(scan.hand);
    const segs = asDict(scan.segmentation);
    const palmBoundary = asDict(segs.palm_region);
    const handDetected = hand.status === "detected";
    const boundaryOk =
      palmBoundary.status === "detected" && pointsOf(palmBoundary.polygon).length >= 3;

    let cancelled = false;
    const wait = (ms: number) =>
      new Promise<void>((resolve) => {
        const id = setTimeout(resolve, ms);
        timersRef.current.push(id);
      });

    const run = async () => {
      // Phase 01 — Hand Detection
      setPhaseIndex(0);
      markPhase("hand_detection", "active");
      if (!handDetected) {
        failPhase(
          "hand_detection",
          str(hand.reason, "Unable to detect an open palm in this image."),
        );
        return;
      }
      animateScalar(setBoundaryReveal, 700);
      await wait(750);
      if (cancelled) return;
      if (!boundaryOk) {
        failPhase(
          "hand_detection",
          str(palmBoundary.reason, "Palm boundary could not be established."),
        );
        return;
      }
      markPhase("hand_detection", "complete");

      // Phase 02 — Palm Geometry
      setPhaseIndex(1);
      markPhase("palm_geometry", "active");
      animateScalar(setGeometryReveal, 500);
      animateScalar(setLandmarksReveal, 900);
      await wait(950);
      if (cancelled) return;
      const landmarkCount = asList(scan.landmarks).length;
      if (landmarkCount < 21) {
        failPhase(
          "palm_geometry",
          `Only ${landmarkCount}/21 landmarks mapped. Retake with full palm visible.`,
        );
        return;
      }
      markPhase("palm_geometry", "complete");

      // Phase 03 — Major Lines
      setPhaseIndex(2);
      markPhase("major_lines", "active");
      const majorCards: LineCard[] = [];
      for (const lineId of PRIMARY_MAJOR_LINES) {
        const info = lineDetectionInfo(scan, lineId);
        const path = resolveMajorLinePath(scan, lineId);
        const required = (REQUIRED_MAJOR_LINES as readonly string[]).includes(lineId);
        const fateEvaluated = lineId === "fate_line" && fateLineWasEvaluated(scan);
        if (!majorLineHasContinuousGeometry(scan, lineId) && !required && !fateEvaluated) {
          continue;
        }
        majorCards.push({
          lineId: info.id,
          label: info.label,
          detected: info.detected,
          failed: info.failed,
          continuity: info.continuity,
          confidence: info.confidence,
          visible: false,
        });
        setLineCards([...majorCards]);
        if (info.failed && required) {
          majorCards[majorCards.length - 1].visible = path.length >= 2;
          setLineCards([...majorCards]);
          setActiveLineId(lineId);
          setPhaseFailures((current) => [
            ...current.filter((item) => item.phaseId !== "major_lines"),
            {
              phaseId: "major_lines",
              message: `${info.label}: weak detection — ${info.status}. Retake with clearer lighting if needed.`,
            },
          ]);
          if (path.length >= 2) {
            await new Promise<void>((resolve) => {
              animateLine(lineId, lineAnimateMs(path.length), resolve);
            });
            if (cancelled) return;
            await wait(120);
          }
          continue;
        }
        if (info.failed && lineId === "fate_line" && path.length >= 2) {
          majorCards[majorCards.length - 1].visible = true;
          setLineCards([...majorCards]);
          continue;
        }
        if (!info.detected) {
          if (fateEvaluated && path.length >= 2) {
            majorCards[majorCards.length - 1].visible = true;
            setLineCards([...majorCards]);
          }
          continue;
        }
        if (path.length >= 2) {
          majorCards[majorCards.length - 1].visible = true;
          setLineCards([...majorCards]);
          setActiveLineId(lineId);
          await new Promise<void>((resolve) => {
            animateLine(lineId, lineAnimateMs(path.length), resolve);
          });
          if (cancelled) return;
          await wait(120);
        }
      }
      markPhase("major_lines", "complete");
      setActiveLineId(null);

      // Phase 04 — Secondary Lines
      setPhaseIndex(3);
      markPhase("secondary_lines", "active");
      const secondaryIds = [
        ...SECONDARY_MAJOR_LINES,
        ...asList(asDict(scan.secondary_lines).crease_candidates)
          .map((item) => asDict(item))
          .filter((row) => str(row.audit_status) === "accepted")
          .map((row) => str(row.id))
          .filter(Boolean),
      ];
      for (const lineId of SECONDARY_MAJOR_LINES) {
        if (!majorLineHasContinuousGeometry(scan, lineId)) continue;
        const info = lineDetectionInfo(scan, lineId);
        const path = resolveMajorLinePath(scan, lineId);
        if (!info.detected || path.length < 2) continue;
        majorCards.push({
          lineId: info.id,
          label: info.label,
          detected: true,
          failed: false,
          continuity: info.continuity,
          confidence: info.confidence,
          visible: true,
        });
        setLineCards([...majorCards]);
        setActiveLineId(lineId);
        await new Promise<void>((resolve) => {
          animateLine(lineId, lineAnimateMs(path.length), resolve);
        });
        if (cancelled) return;
      }
      // Accepted crease candidates not already shown as major lines
      const majorCandidateIds = new Set(
        PRIMARY_MAJOR_LINES.concat(SECONDARY_MAJOR_LINES)
          .map((name) => str(asDict(asDict(scan.major_lines)[name]).source_candidate_id))
          .filter(Boolean),
      );
      const creaseCandidates = asList(asDict(scan.secondary_lines).crease_candidates).map((item) =>
        asDict(item),
      );
      let creaseIndex = 0;
      for (const row of creaseCandidates) {
        const id = str(row.id, `crease_${creaseIndex}`);
        if (str(row.audit_status) !== "accepted") continue;
        if (majorCandidateIds.has(id)) continue;
        const path = pointsOf(row.path);
        if (path.length < 2) continue;
        const creaseId = `crease:${id}`;
        majorCards.push({
          lineId: creaseId,
          label: str(row.label, `Crease ${creaseIndex + 1}`),
          detected: true,
          failed: false,
          continuity: formatMetric(row.continuity ?? asDict(row.measurements).continuity),
          confidence: formatMetric(row.confidence),
          visible: true,
        });
        setLineCards([...majorCards]);
        setActiveLineId(creaseId);
        await new Promise<void>((resolve) => {
          animateLine(creaseId, lineAnimateMs(path.length), resolve);
        });
        if (cancelled) return;
        creaseIndex += 1;
      }
      void secondaryIds;
      markPhase("secondary_lines", "complete");
      setActiveLineId(null);

      // Phase 05 — Markings
      setPhaseIndex(4);
      markPhase("markings", "active");
      animateScalar(setMarkingsReveal, 800);
      await wait(850);
      if (cancelled) return;
      markPhase("markings", "complete");

      // Phase 06 — Verification
      setPhaseIndex(5);
      markPhase("verification", "active");
      await wait(400);
      if (cancelled) return;
      markPhase("verification", "complete");
      setScanComplete(true);
      setScanEnded(true);
      setInteractive(true);
    };

    void run();
    return () => {
      cancelled = true;
      clearTimers();
    };
  }, [scan, animateLine, animateScalar, clearTimers, failPhase, markPhase]);

  return {
    phaseIndex,
    phaseStatuses,
    lineProgress,
    lineCards,
    interactive,
    scanComplete,
    scanEnded,
    activeLineId,
    phaseFailures,
    geometryReveal,
    boundaryReveal,
    landmarksReveal,
    markingsReveal,
  };
}

function formatMetric(value: unknown): string {
  const n = num(value);
  if (n == null) return "Not available";
  const pct = n <= 1 ? n * 100 : n;
  return `${Math.round(pct)}%`;
}

export function collectDetectedLines(scan: Dict): LineDetectionInfo[] {
  const items: LineDetectionInfo[] = [];
  for (const lineId of [...PRIMARY_MAJOR_LINES, ...SECONDARY_MAJOR_LINES]) {
    if (!majorLineShowsInSelector(scan, lineId)) continue;
    items.push(lineDetectionInfo(scan, lineId));
  }
  return items;
}

export function validationLabel(scan: Dict): {
  label: string;
  tone: "verified" | "pending" | "rejected";
  message: string;
} {
  const gate = asDict(scan.production_validation);
  const status = str(gate.status, "pending");
  if (status === "verified") {
    return {
      label: "Scan Verified",
      tone: "verified",
      message: str(gate.user_message, "Production validation passed."),
    };
  }
  if (status === "rejected") {
    const errors = asList(gate.validation_errors).map((item) => str(item)).filter(Boolean);
    return {
      label: "Scan Rejected",
      tone: "rejected",
      message:
        str(gate.user_message) ||
        errors.join("; ") ||
        "Scan did not pass production validation.",
    };
  }
  return {
    label: "Validation In Progress",
    tone: "pending",
    message: str(gate.user_message, "Awaiting production validation."),
  };
}
