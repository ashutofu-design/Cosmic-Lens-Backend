import * as Haptics from "expo-haptics";
import { LinearGradient } from "expo-linear-gradient";
import React from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";

import { useC } from "@/context/ThemeContext";

export type LifeMapMode = "lifemap" | "explore";

export function LifeMapModeTabs({
  active,
  lifeMapLabel,
  exploreLabel,
  onSelect,
}: {
  active: LifeMapMode;
  lifeMapLabel: string;
  exploreLabel: string;
  onSelect: (mode: LifeMapMode) => void;
}) {
  const C = useC();
  const isDark = C.isDark;

  function TabBtn({
    mode,
    label,
    icon,
  }: {
    mode: LifeMapMode;
    label: string;
    icon: string;
  }) {
    const selected = active === mode;
    return (
      <Pressable
        onPress={() => {
          Haptics.selectionAsync();
          onSelect(mode);
        }}
        style={[
          s.tab,
          {
            backgroundColor: selected
              ? (isDark ? "rgba(124,58,237,0.35)" : "rgba(124,58,237,0.12)")
              : (isDark ? "rgba(255,255,255,0.04)" : "rgba(0,0,0,0.03)"),
            borderColor: selected
              ? (isDark ? "rgba(124,58,237,0.55)" : "rgba(124,58,237,0.35)")
              : (isDark ? "rgba(255,255,255,0.08)" : "rgba(0,0,0,0.06)"),
          },
        ]}
      >
        {selected && (
          <LinearGradient
            colors={isDark ? ["rgba(124,58,237,0.25)", "transparent"] : ["rgba(124,58,237,0.08)", "transparent"]}
            style={StyleSheet.absoluteFill}
          />
        )}
        <Text style={s.tabIcon}>{icon}</Text>
        <Text
          style={[
            s.tabLabel,
            {
              color: selected
                ? (isDark ? "#fff" : "#7C3AED")
                : (isDark ? "rgba(203,213,225,0.65)" : "#64748B"),
              fontFamily: selected ? "Nunito_700Bold" : "Nunito_600SemiBold",
            },
          ]}
          numberOfLines={1}
        >
          {label}
        </Text>
      </Pressable>
    );
  }

  return (
    <View style={[s.row, { backgroundColor: isDark ? "rgba(14,22,42,0.6)" : "rgba(248,250,252,0.9)", borderColor: isDark ? "rgba(255,255,255,0.08)" : "rgba(0,0,0,0.06)" }]}>
      <TabBtn mode="lifemap" label={lifeMapLabel} icon="🗺️" />
      <TabBtn mode="explore" label={exploreLabel} icon="✨" />
    </View>
  );
}

const s = StyleSheet.create({
  row: {
    flexDirection: "row",
    gap: 10,
    padding: 6,
    borderRadius: 16,
    borderWidth: 1,
  },
  tab: {
    flex: 1,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
    paddingVertical: 12,
    paddingHorizontal: 10,
    borderRadius: 12,
    borderWidth: 1,
    overflow: "hidden",
  },
  tabIcon: { fontSize: 16 },
  tabLabel: { fontSize: 13, letterSpacing: 0.2 },
});
