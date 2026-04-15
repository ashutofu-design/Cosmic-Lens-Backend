import { LinearGradient } from "expo-linear-gradient";
import React from "react";
import { Dimensions, StyleSheet, View, ViewStyle } from "react-native";

import { useC } from "@/context/ThemeContext";

const { width: W, height: H } = Dimensions.get("window");

interface Props {
  children: React.ReactNode;
  style?: ViewStyle;
  contentStyle?: ViewStyle;
}

export function CosmicBg({ children, style, contentStyle }: Props) {
  const C = useC();

  const orb1 = C.isDark
    ? (["rgba(120,80,255,0.28)", "rgba(90,50,200,0.10)", "transparent"] as const)
    : (["rgba(139,92,246,0.14)", "rgba(109,40,217,0.06)", "transparent"] as const);

  const orb2 = C.isDark
    ? (["rgba(80,100,255,0.22)", "rgba(60,80,200,0.08)", "transparent"] as const)
    : (["rgba(99,102,241,0.10)", "rgba(79,70,229,0.04)", "transparent"] as const);

  const orb3 = C.isDark
    ? (["rgba(245,158,11,0.10)", "rgba(245,158,11,0.03)", "transparent"] as const)
    : (["rgba(245,158,11,0.07)", "rgba(245,158,11,0.02)", "transparent"] as const);

  const orb4 = C.isDark
    ? (["rgba(236,72,153,0.12)", "rgba(236,72,153,0.03)", "transparent"] as const)
    : (["rgba(236,72,153,0.07)", "transparent", "transparent"] as const);

  return (
    <View style={[s.root, { backgroundColor: C.bg }, style]}>
      {/* Orb 1 — top-left violet nebula */}
      <LinearGradient
        colors={orb1}
        style={[s.orb, s.orbTL]}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
      />
      {/* Orb 2 — bottom-right indigo */}
      <LinearGradient
        colors={orb2}
        style={[s.orb, s.orbBR]}
        start={{ x: 1, y: 1 }}
        end={{ x: 0, y: 0 }}
      />
      {/* Orb 3 — mid amber accent */}
      <LinearGradient
        colors={orb3}
        style={[s.orb, s.orbMid]}
        start={{ x: 0.5, y: 0 }}
        end={{ x: 0.5, y: 1 }}
      />
      {/* Orb 4 — top-right pink */}
      <LinearGradient
        colors={orb4}
        style={[s.orb, s.orbTR]}
        start={{ x: 1, y: 0 }}
        end={{ x: 0, y: 1 }}
      />
      {/* Subtle star dots (dark mode only) */}
      {C.isDark && (
        <>
          <View style={[s.star, { top: H * 0.12, left: W * 0.18 }]} />
          <View style={[s.star, { top: H * 0.22, left: W * 0.72 }]} />
          <View style={[s.star, s.starBig, { top: H * 0.08, left: W * 0.55 }]} />
          <View style={[s.star, { top: H * 0.35, left: W * 0.10 }]} />
          <View style={[s.star, s.starBig, { top: H * 0.45, left: W * 0.88 }]} />
          <View style={[s.star, { top: H * 0.62, left: W * 0.25 }]} />
          <View style={[s.star, s.starBig, { top: H * 0.70, left: W * 0.65 }]} />
          <View style={[s.star, { top: H * 0.80, left: W * 0.42 }]} />
          <View style={[s.star, { top: H * 0.88, left: W * 0.80 }]} />
          <View style={[s.star, s.starBig, { top: H * 0.15, left: W * 0.38 }]} />
        </>
      )}
      <View style={[s.content, contentStyle]}>{children}</View>
    </View>
  );
}

const s = StyleSheet.create({
  root: {
    flex: 1,
    overflow: "hidden",
  },
  orb: {
    position: "absolute",
    borderRadius: 9999,
  },
  orbTL: {
    width: W * 1.1,
    height: W * 1.1,
    top: -W * 0.35,
    left: -W * 0.30,
  },
  orbBR: {
    width: W * 1.2,
    height: W * 1.2,
    bottom: -W * 0.35,
    right: -W * 0.30,
  },
  orbMid: {
    width: W * 0.75,
    height: W * 0.75,
    top: H * 0.30,
    left: W * 0.12,
  },
  orbTR: {
    width: W * 0.65,
    height: W * 0.65,
    top: -W * 0.15,
    right: -W * 0.10,
  },
  star: {
    position: "absolute",
    width: 2,
    height: 2,
    borderRadius: 1,
    backgroundColor: "rgba(255,255,255,0.35)",
  },
  starBig: {
    width: 3,
    height: 3,
    borderRadius: 1.5,
    backgroundColor: "rgba(255,255,255,0.55)",
  },
  content: {
    flex: 1,
  },
});
