import { Feather } from "@expo/vector-icons";
import React from "react";
import { StyleSheet, Text, View } from "react-native";

import { useC } from "@/context/ThemeContext";
import { useT } from "@/hooks/useT";

const ACCENT = "#ec4899";

export function FaceReadingProBuilding() {
  const C = useC();
  const t = useT();

  return (
    <View style={bp.wrap}>
      <View style={[bp.card, { borderColor: C.border, backgroundColor: C.bgCard }]}>
        <Text style={bp.emoji}>👁️</Text>
        <View style={[bp.pill, { backgroundColor: `${ACCENT}22`, borderColor: `${ACCENT}55` }]}>
          <Feather name="clock" size={14} color={ACCENT} />
          <Text style={[bp.pillText, { color: ACCENT }]}>{t.fr_wipTitle}</Text>
        </View>
        <Text style={[bp.sub, { color: C.textMuted }]}>{t.fr_wipHint}</Text>
      </View>
    </View>
  );
}

const bp = StyleSheet.create({
  wrap: {
    flex: 1,
    paddingHorizontal: 24,
    justifyContent: "center",
    alignItems: "center",
  },
  card: {
    width: "100%",
    maxWidth: 340,
    borderRadius: 20,
    borderWidth: 1,
    paddingVertical: 36,
    paddingHorizontal: 24,
    alignItems: "center",
    gap: 16,
  },
  emoji: { fontSize: 48 },
  pill: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 999,
    borderWidth: 1,
  },
  pillText: {
    fontSize: 18,
    fontWeight: "800",
    letterSpacing: 0.3,
  },
  sub: {
    fontSize: 13,
    fontWeight: "600",
    textAlign: "center",
    lineHeight: 20,
  },
});
