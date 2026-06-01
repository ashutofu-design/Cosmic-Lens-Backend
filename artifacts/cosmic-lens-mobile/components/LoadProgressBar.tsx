import { LinearGradient } from "expo-linear-gradient";
import React from "react";
import { StyleSheet, Text, View } from "react-native";
import { useC } from "@/context/ThemeContext";

const F = {
  semibold: "Nunito_600SemiBold",
  bold: "Nunito_700Bold",
};

export function LoadProgressBar({
  progress,
  label,
  compact,
}: {
  progress: number;
  label: string;
  compact?: boolean;
}) {
  const C = useC();
  const pct = Math.min(100, Math.max(0, Math.round(progress)));

  return (
    <View style={[s.wrap, compact && s.wrapCompact]}>
      {!compact ? (
        <Text style={[s.label, { color: C.text }]}>{label}</Text>
      ) : null}
      <View style={s.row}>
        <View style={[s.track, { backgroundColor: C.isDark ? "rgba(255,255,255,0.12)" : "rgba(15,23,42,0.1)" }]}>
          <LinearGradient
            colors={["#a78bfa", "#ec4899", "#fbbf24"]}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 0 }}
            style={[s.fill, { width: `${pct}%` }]}
          />
        </View>
        <Text style={[s.pct, { color: C.isDark ? "#c4b5fd" : "#7c3aed" }]}>{pct}%</Text>
      </View>
    </View>
  );
}

const s = StyleSheet.create({
  wrap: { gap: 12, paddingVertical: 8 },
  wrapCompact: { paddingVertical: 0, gap: 6 },
  label: { fontSize: 14, fontFamily: F.semibold, textAlign: "center" },
  row: { flexDirection: "row", alignItems: "center", gap: 12 },
  track: { flex: 1, height: 10, borderRadius: 8, overflow: "hidden" },
  fill: { height: "100%", borderRadius: 8 },
  pct: { fontSize: 16, fontFamily: F.bold, minWidth: 44, textAlign: "right" },
});
