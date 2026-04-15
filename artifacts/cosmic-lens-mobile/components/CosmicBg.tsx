import { LinearGradient } from "expo-linear-gradient";
import React from "react";
import { Dimensions, StyleSheet, View, ViewStyle } from "react-native";

import { useC } from "@/context/ThemeContext";

const { width: W, height: H } = Dimensions.get("window");

const MOON  = W * 0.50;
const GLOW1 = MOON * 1.22;
const GLOW2 = MOON * 1.60;
const GLOW3 = MOON * 2.10;
const GLOW4 = MOON * 2.80;
const GLOW5 = MOON * 3.60;

interface Props {
  children: React.ReactNode;
  style?: ViewStyle;
  contentStyle?: ViewStyle;
}

function GlowingMoon({ isDark }: { isDark: boolean }) {
  if (!isDark) {
    return (
      <View style={s.moonWrap}>
        <View style={[s.glowRing, { width: GLOW4, height: GLOW4, borderRadius: GLOW4 / 2, backgroundColor: "rgba(180,150,255,0.04)" }]} />
        <View style={[s.glowRing, { width: GLOW3, height: GLOW3, borderRadius: GLOW3 / 2, backgroundColor: "rgba(180,150,255,0.06)" }]} />
        <View style={[s.glowRing, { width: GLOW2, height: GLOW2, borderRadius: GLOW2 / 2, backgroundColor: "rgba(180,150,255,0.09)" }]} />
        <View style={[s.glowRing, { width: GLOW1, height: GLOW1, borderRadius: GLOW1 / 2, backgroundColor: "rgba(200,170,255,0.14)" }]} />
        <LinearGradient
          colors={["rgba(245,240,220,0.70)", "rgba(210,205,185,0.55)", "rgba(180,175,165,0.40)"]}
          style={[s.moonBody, { width: MOON, height: MOON, borderRadius: MOON / 2 }]}
          start={{ x: 0.25, y: 0.10 }}
          end={{ x: 0.80, y: 0.90 }}
        />
      </View>
    );
  }

  return (
    <View style={s.moonWrap}>
      {/* Outermost atmospheric diffusion */}
      <View style={[s.glowRing, { width: GLOW5, height: GLOW5, borderRadius: GLOW5 / 2, backgroundColor: "rgba(100,120,255,0.025)" }]} />
      {/* Outer atmospheric halo */}
      <View style={[s.glowRing, { width: GLOW4, height: GLOW4, borderRadius: GLOW4 / 2, backgroundColor: "rgba(130,150,255,0.045)" }]} />
      {/* Mid blue-white halo */}
      <View style={[s.glowRing, { width: GLOW3, height: GLOW3, borderRadius: GLOW3 / 2, backgroundColor: "rgba(180,200,255,0.08)" }]} />
      {/* Inner cool-white halo */}
      <View style={[s.glowRing, { width: GLOW2, height: GLOW2, borderRadius: GLOW2 / 2, backgroundColor: "rgba(220,230,255,0.13)" }]} />
      {/* Tight warm glow */}
      <View style={[s.glowRing, { width: GLOW1, height: GLOW1, borderRadius: GLOW1 / 2, backgroundColor: "rgba(255,252,230,0.20)" }]} />
      {/* Moon surface */}
      <LinearGradient
        colors={["rgba(255,252,240,1.0)", "rgba(238,234,210,0.97)", "rgba(200,196,178,0.94)"]}
        style={[s.moonBody, { width: MOON, height: MOON, borderRadius: MOON / 2 }]}
        start={{ x: 0.20, y: 0.08 }}
        end={{ x: 0.85, y: 0.92 }}
      />
      {/* Craters */}
      <View style={[s.crater, { width: MOON * 0.10, height: MOON * 0.10, borderRadius: MOON * 0.05, top: MOON * 0.22, left: MOON * 0.20 }]} />
      <View style={[s.crater, { width: MOON * 0.07, height: MOON * 0.07, borderRadius: MOON * 0.035, top: MOON * 0.45, left: MOON * 0.55 }]} />
      <View style={[s.crater, { width: MOON * 0.05, height: MOON * 0.05, borderRadius: MOON * 0.025, top: MOON * 0.60, left: MOON * 0.25 }]} />
      <View style={[s.crater, { width: MOON * 0.12, height: MOON * 0.12, borderRadius: MOON * 0.06, top: MOON * 0.35, left: MOON * 0.38 }]} />
      <View style={[s.crater, { width: MOON * 0.06, height: MOON * 0.06, borderRadius: MOON * 0.03, top: MOON * 0.70, left: MOON * 0.45 }]} />
    </View>
  );
}

export function CosmicBg({ children, style, contentStyle }: Props) {
  const C = useC();

  return (
    <View style={[s.root, { backgroundColor: C.bg }, style]}>

      {/* ── Glowing Moon ── */}
      <GlowingMoon isDark={C.isDark} />

      {/* ── Bottom purple nebula wash ── */}
      <LinearGradient
        colors={C.isDark
          ? ["transparent", "rgba(80,50,160,0.08)", "rgba(60,30,120,0.14)"]
          : ["transparent", "rgba(139,92,246,0.04)", "rgba(109,40,217,0.08)"]}
        style={s.bottomWash}
        start={{ x: 0.5, y: 0 }}
        end={{ x: 0.5, y: 1 }}
      />

      {/* ── Stars (dark mode) ── */}
      {C.isDark && (
        <>
          <View style={[s.star,            { top: H * 0.28, left: W * 0.08 }]} />
          <View style={[s.star,            { top: H * 0.33, left: W * 0.75 }]} />
          <View style={[s.starBig,         { top: H * 0.38, left: W * 0.88 }]} />
          <View style={[s.star,            { top: H * 0.42, left: W * 0.18 }]} />
          <View style={[s.starBig,         { top: H * 0.50, left: W * 0.60 }]} />
          <View style={[s.star,            { top: H * 0.56, left: W * 0.32 }]} />
          <View style={[s.starBig,         { top: H * 0.62, left: W * 0.78 }]} />
          <View style={[s.star,            { top: H * 0.68, left: W * 0.45 }]} />
          <View style={[s.star,            { top: H * 0.74, left: W * 0.12 }]} />
          <View style={[s.starBig,         { top: H * 0.80, left: W * 0.55 }]} />
          <View style={[s.starFaint,       { top: H * 0.85, left: W * 0.28 }]} />
          <View style={[s.starFaint,       { top: H * 0.72, left: W * 0.92 }]} />
          <View style={[s.starFaint,       { top: H * 0.46, left: W * 0.04 }]} />
          <View style={[s.starFaint,       { top: H * 0.88, left: W * 0.68 }]} />
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

  /* ── Moon ── */
  moonWrap: {
    position: "absolute",
    alignItems: "center",
    justifyContent: "center",
    top: -MOON * 0.42,
    right: -MOON * 0.32,
  },
  glowRing: {
    position: "absolute",
  },
  moonBody: {
    position: "absolute",
  },
  crater: {
    position: "absolute",
    backgroundColor: "rgba(160,155,130,0.28)",
  },

  /* ── Bottom wash ── */
  bottomWash: {
    position: "absolute",
    width: W,
    height: H * 0.50,
    bottom: 0,
    left: 0,
  },

  /* ── Stars ── */
  star: {
    position: "absolute",
    width: 2,
    height: 2,
    borderRadius: 1,
    backgroundColor: "rgba(255,255,255,0.40)",
  },
  starBig: {
    position: "absolute",
    width: 3,
    height: 3,
    borderRadius: 1.5,
    backgroundColor: "rgba(255,255,255,0.60)",
  },
  starFaint: {
    position: "absolute",
    width: 2,
    height: 2,
    borderRadius: 1,
    backgroundColor: "rgba(255,255,255,0.20)",
  },

  content: {
    flex: 1,
  },
});
