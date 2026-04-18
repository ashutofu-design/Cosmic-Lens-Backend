/**
 * ScanBasisBadge — surfaces "what is this report based on" trust signal.
 *
 * Inputs:
 *  - vision_room_findings (from backend annotate_report_with_room_photos): tells
 *    us how many room photos were analyzed and whether magnetometer was used.
 *  - rooms (from report): may contain visual_findings + direction_basis.
 *
 * Branding: never mentions AI/LLM/GPT — uses "Cosmic Vision".
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
};

export function ScanBasisBadge({ visionRoomFindings, perRoomBasis }: Props) {
  const C = useC();

  const analyzed = visionRoomFindings?.rooms_analyzed || 0;
  const applied  = visionRoomFindings?.applied_score_delta || 0;

  // Determine basis from per-room data (priority) or from per_room.direction_basis
  const bases = new Set<string>();
  (perRoomBasis || []).forEach((r) => {
    if (r.direction_basis) bases.add(r.direction_basis);
  });
  (visionRoomFindings?.per_room || []).forEach((r) => {
    if (r.direction_basis) bases.add(r.direction_basis);
  });

  const compassConfirmed = bases.has("magnetometer");
  const visualOnly       = !compassConfirmed && (bases.has("visual_inference") || bases.has("assumed"));

  // If nothing to show (no vision, no photos), render nothing — keeps card clean.
  if (analyzed === 0 && bases.size === 0) return null;

  const tone =
    compassConfirmed ? { fg: "#10b981", bg: "#10b98115", label: "Compass-confirmed", icon: "compass" as const }
    : visualOnly     ? { fg: "#f59e0b", bg: "#f59e0b15", label: "Visual inference",   icon: "eye"     as const }
    :                  { fg: C.accent,   bg: C.accent + "15", label: "Cosmic Vision",  icon: "zap"    as const };

  return (
    <View style={[s.wrap, { borderColor: tone.fg + "55", backgroundColor: tone.bg }]}>
      <Feather name={tone.icon} size={14} color={tone.fg} />
      <View style={{ flex: 1 }}>
        <Text style={[s.title, { color: tone.fg }]}>
          Scan basis: {tone.label}
        </Text>
        <Text style={[s.body, { color: C.textMid }]}>
          {analyzed > 0
            ? `${analyzed} room photo${analyzed === 1 ? "" : "s"} analyzed by Cosmic Vision`
            : "Floor plan only — no room photos provided"}
          {applied !== 0 ? `  ·  Score adjustment: ${applied > 0 ? "+" : ""}${applied}` : ""}
        </Text>
        {visualOnly && analyzed > 0 ? (
          <Text style={[s.hint, { color: C.textMid }]}>
            Tip: Capture room photos with compass for sensor-confirmed accuracy.
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
