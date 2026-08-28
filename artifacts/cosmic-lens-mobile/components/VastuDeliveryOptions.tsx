import { Feather } from "@expo/vector-icons";
import * as Haptics from "expo-haptics";
import React from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";

import {
  PRIORITY_GUARANTEE,
  REPORT_PRIORITY_FEE_INR,
  STANDARD_DELIVERY_ETA,
} from "@/lib/deliverySla";

export function VastuDeliveryOptions({
  isDark,
  priority,
  onPriorityChange,
}: {
  isDark: boolean;
  priority: boolean;
  onPriorityChange: (value: boolean) => void;
}) {
  const border = isDark ? "rgba(255,255,255,0.1)" : "rgba(0,0,0,0.08)";
  const titleColor = isDark ? "#f8fafc" : "#0f172a";
  const bodyColor = isDark ? "rgba(226,232,240,0.72)" : "#64748b";
  const cardBg = isDark ? "rgba(255,255,255,0.04)" : "rgba(255,255,255,0.92)";

  return (
    <View style={[s.card, { backgroundColor: cardBg, borderColor: border }]}>
      <Text style={[s.title, { color: titleColor }]}>Standard Delivery</Text>
      <Text style={[s.standard, { color: bodyColor }]}>
        📁 Report in My Reports · {STANDARD_DELIVERY_ETA}
      </Text>
      <Pressable
        onPress={() => {
          onPriorityChange(!priority);
          Haptics.selectionAsync();
        }}
        style={[
          s.priorityRow,
          {
            borderColor: priority ? (isDark ? "#f59e0b" : "#d97706") : border,
            backgroundColor: priority
              ? isDark
                ? "rgba(245,158,11,0.08)"
                : "rgba(245,158,11,0.06)"
              : "transparent",
          },
        ]}
      >
        <View
          style={[
            s.check,
            {
              borderColor: priority ? "#f59e0b" : border,
              backgroundColor: priority ? "#f59e0b" : "transparent",
            },
          ]}
        >
          {priority ? <Feather name="check" size={10} color="#fff" /> : null}
        </View>
        <Text style={[s.priorityTxt, { color: titleColor }]} numberOfLines={1}>
          ⚡ Priority +₹{REPORT_PRIORITY_FEE_INR} · within 12 hours
        </Text>
      </Pressable>
      <Text style={[s.guarantee, { color: bodyColor }]}>{PRIORITY_GUARANTEE}</Text>
    </View>
  );
}

const s = StyleSheet.create({
  card: { borderRadius: 14, borderWidth: 1, padding: 14, marginBottom: 12 },
  title: { fontSize: 14, fontFamily: "Nunito_800ExtraBold" },
  standard: { fontSize: 12, fontFamily: "Nunito_500Medium", marginTop: 6 },
  priorityRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    marginTop: 8,
    paddingVertical: 8,
    paddingHorizontal: 10,
    borderRadius: 10,
    borderWidth: 1,
  },
  check: {
    width: 16,
    height: 16,
    borderRadius: 4,
    borderWidth: 1.5,
    alignItems: "center",
    justifyContent: "center",
  },
  priorityTxt: { flex: 1, fontSize: 12, fontFamily: "Nunito_700Bold" },
  guarantee: { fontSize: 11, fontFamily: "Nunito_500Medium", marginTop: 8, lineHeight: 15 },
});
