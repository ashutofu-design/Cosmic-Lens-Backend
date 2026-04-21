/**
 * ScanBasisBadge — surfaces "what is this report based on" trust signal.
 *
 * Inputs:
 *  - vision_room_findings (from backend annotate_report_with_room_photos): tells
 *    us how many room photos were analyzed and whether magnetometer was used.
 *  - rooms (from report): may contain visual_findings + direction_basis.
 *
 * Branding: never mentions AI/LLM/GPT — uses "Photo Engine".
 */
import { Feather } from "@expo/vector-icons";
import React from "react";
import { StyleSheet, Text, View } from "react-native";

import { useC } from "@/context/ThemeContext";

export type VisionPerRoom = {
  room_type:        string;
  findings_count:   number;
  score_delta:      number;
  confidence:       number;
  scan_inconclusive: boolean;
  matched_in_report: boolean;
  direction_basis?: string;   // "magnetometer" | "visual_inference" | "assumed"
};

export type VisionRoomFindings = {
  rooms_analyzed:     number;
  applied_score_delta?: number;
  per_room?:          VisionPerRoom[];
};

type Props = {
  visionRoomFindings?: VisionRoomFindings | null;
  perRoomBasis?: Array<{ room_type: string; direction_basis?: string }>;
  /**
   * report.vision_used (top-level flag from backend). When true and no
   * per-room basis says "magnetometer", the badge surfaces "Visual
   * inference" — the floor-plan was read by Photo Engine even if no
   * room photos were submitted.
   */
  visionUsed?: boolean;
  /** report.vision_findings_count (top-level flag from backend). */
  visionFindingsCount?: number;
};

export function ScanBasisBadge({
  visionRoomFindings,
  perRoomBasis,
  visionUsed,
  visionFindingsCount,
}: Props) {
  const C = useC();

  const analyzed = visionRoomFindings?.rooms_analyzed || 0;
  const applied  = visionRoomFindings?.applied_score_delta || 0;
  const findingsCount = typeof visionFindingsCount === "number"
    ? visionFindingsCount
    : (visionRoomFindings?.per_room || [])
        .reduce((sum, r) => sum + (r.findings_count || 0), 0);

  // Determine basis from per-room data (priority) or from per_room.direction_basis
  const bases = new Set<string>();
  (perRoomBasis || []).forEach((r) => {
    if (r.direction_basis) bases.add(r.direction_basis);
  });
  (visionRoomFindings?.per_room || []).forEach((r) => {
    if (r.direction_basis) bases.add(r.direction_basis);
  });

  const compassConfirmed = bases.has("magnetometer");
  const anyVisionRan     = !!visionUsed || analyzed > 0
                            || bases.has("visual_inference");

  // Per spec: badge ALWAYS reflects actual data — three distinct labels.
  const tone = compassConfirmed
    ? { fg: "#10b981", bg: "#10b98115", label: "Compass-confirmed", icon: "compass" as const }
    : anyVisionRan
    ? { fg: "#f59e0b", bg: "#f59e0b15", label: "Visual inference",  icon: "eye"     as const }
    : { fg: C.textMid, bg: C.textMid + "15", label: "Assumed layout", icon: "help-circle" as const };

  // Footer line — always shows what backend reported.
  const meta: string[] = [];
  if (analyzed > 0) {
    meta.push(`${analyzed} room photo${analyzed === 1 ? "" : "s"} analyzed`);
  } else if (visionUsed) {
    meta.push("Floor plan read by Photo Engine");
  } else {
    meta.push("Default Vastu layout assumed");
  }
  if (findingsCount > 0) meta.push(`${findingsCount} finding${findingsCount === 1 ? "" : "s"}`);
  if (applied !== 0)     meta.push(`Score Δ ${applied > 0 ? "+" : ""}${applied}`);

  return (
    <View style={[s.wrap, { borderColor: tone.fg + "55", backgroundColor: tone.bg }]}>
      <Feather name={tone.icon} size={14} color={tone.fg} />
      <View style={{ flex: 1 }}>
        <Text style={[s.title, { color: tone.fg }]}>
          Scan basis: {tone.label}
        </Text>
        <Text style={[s.body, { color: C.textMid }]}>
          {meta.join("  ·  ")}
        </Text>
        {tone.label === "Visual inference" ? (
          <Text style={[s.hint, { color: C.textMid }]}>
            Tip: Capture room photos with compass for sensor-confirmed accuracy.
          </Text>
        ) : tone.label === "Assumed layout" ? (
          <Text style={[s.hint, { color: C.textMid }]}>
            Tip: Upload a floor plan or room photos for a more accurate read.
          </Text>
        ) : null}
      </View>
    </View>
  );
}

const s = StyleSheet.create({
  wrap:  { flexDirection: "row", alignItems: "flex-start", gap: 9,
           padding: 10, borderRadius: 10, borderWidth: 1, marginTop: 10 },
  title: { fontSize: 12, fontWeight: "800", marginBottom: 2 },
  body:  { fontSize: 11, lineHeight: 15 },
  hint:  { fontSize: 10, fontStyle: "italic", marginTop: 4 },
});
