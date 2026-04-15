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

// Pre-calculated star positions [x%, y%, size, opacity]
// spread across full screen to look like a real galaxy
const STARS: [number, number, number, number][] = [
  // tiny faint stars
  [0.04, 0.06, 1, 0.25], [0.92, 0.03, 1, 0.20], [0.17, 0.10, 1, 0.30],
  [0.43, 0.07, 1, 0.22], [0.68, 0.04, 1, 0.28], [0.81, 0.09, 1, 0.18],
  [0.29, 0.14, 1, 0.25], [0.55, 0.11, 1, 0.32], [0.73, 0.15, 1, 0.20],
  [0.11, 0.19, 1, 0.27], [0.38, 0.18, 1, 0.23], [0.62, 0.21, 1, 0.30],
  [0.88, 0.16, 1, 0.22], [0.06, 0.24, 1, 0.18], [0.24, 0.27, 1, 0.28],
  [0.50, 0.25, 1, 0.20], [0.76, 0.23, 1, 0.25], [0.95, 0.28, 1, 0.17],
  [0.14, 0.32, 1, 0.22], [0.36, 0.30, 1, 0.28], [0.58, 0.34, 1, 0.18],
  [0.82, 0.31, 1, 0.24], [0.03, 0.37, 1, 0.20], [0.46, 0.38, 1, 0.26],
  [0.70, 0.36, 1, 0.19], [0.91, 0.40, 1, 0.22], [0.19, 0.42, 1, 0.28],
  [0.63, 0.43, 1, 0.20], [0.08, 0.48, 1, 0.17], [0.34, 0.46, 1, 0.25],
  [0.77, 0.50, 1, 0.22], [0.96, 0.47, 1, 0.18], [0.22, 0.53, 1, 0.26],
  [0.48, 0.52, 1, 0.20], [0.67, 0.56, 1, 0.22], [0.85, 0.54, 1, 0.17],
  [0.12, 0.59, 1, 0.25], [0.40, 0.58, 1, 0.19], [0.72, 0.61, 1, 0.23],
  [0.02, 0.64, 1, 0.18], [0.30, 0.63, 1, 0.27], [0.55, 0.67, 1, 0.20],
  [0.89, 0.65, 1, 0.22], [0.16, 0.70, 1, 0.17], [0.44, 0.72, 1, 0.25],
  [0.69, 0.69, 1, 0.19], [0.97, 0.73, 1, 0.20], [0.26, 0.76, 1, 0.24],
  [0.60, 0.75, 1, 0.17], [0.08, 0.80, 1, 0.22], [0.38, 0.81, 1, 0.19],
  [0.75, 0.79, 1, 0.25], [0.53, 0.84, 1, 0.18], [0.20, 0.87, 1, 0.22],
  [0.84, 0.85, 1, 0.17], [0.45, 0.89, 1, 0.20], [0.93, 0.88, 1, 0.15],
  // medium stars
  [0.09, 0.08, 2, 0.40], [0.31, 0.05, 2, 0.35], [0.57, 0.09, 2, 0.42],
  [0.79, 0.06, 2, 0.38], [0.21, 0.20, 2, 0.36], [0.66, 0.17, 2, 0.40],
  [0.47, 0.29, 2, 0.35], [0.84, 0.26, 2, 0.38], [0.13, 0.35, 2, 0.42],
  [0.59, 0.39, 2, 0.36], [0.87, 0.37, 2, 0.33], [0.28, 0.44, 2, 0.40],
  [0.72, 0.48, 2, 0.35], [0.05, 0.54, 2, 0.38], [0.41, 0.57, 2, 0.42],
  [0.93, 0.55, 2, 0.34], [0.18, 0.62, 2, 0.38], [0.64, 0.64, 2, 0.36],
  [0.35, 0.71, 2, 0.40], [0.80, 0.68, 2, 0.34], [0.10, 0.75, 2, 0.38],
  [0.51, 0.78, 2, 0.35], [0.77, 0.82, 2, 0.40], [0.25, 0.86, 2, 0.36],
  [0.62, 0.91, 2, 0.32], [0.90, 0.93, 2, 0.35],
  // bright stars
  [0.15, 0.12, 3, 0.60], [0.53, 0.16, 3, 0.55], [0.88, 0.20, 3, 0.58],
  [0.33, 0.36, 3, 0.62], [0.70, 0.33, 3, 0.56], [0.07, 0.46, 3, 0.60],
  [0.48, 0.50, 3, 0.54], [0.92, 0.44, 3, 0.58], [0.22, 0.66, 3, 0.62],
  [0.65, 0.70, 3, 0.55], [0.43, 0.83, 3, 0.58], [0.85, 0.78, 3, 0.52],
  // very bright (sparkle) stars
  [0.26, 0.08, 4, 0.80], [0.74, 0.13, 4, 0.75], [0.42, 0.60, 4, 0.78],
  [0.87, 0.58, 4, 0.72], [0.11, 0.88, 4, 0.76],
];

// Milky Way: faint diagonal streak of star clusters
const MILKY: [number, number, number][] = [
  [0.20, 0.15, 0.08], [0.28, 0.22, 0.10], [0.35, 0.29, 0.09],
  [0.42, 0.36, 0.11], [0.50, 0.44, 0.10], [0.57, 0.51, 0.09],
  [0.64, 0.58, 0.08], [0.71, 0.65, 0.07], [0.78, 0.72, 0.08],
];

export function CosmicBg({ children, style, contentStyle }: Props) {
  const C = useC();

  return (
    <View style={[s.root, { backgroundColor: C.bg }, style]}>

      {/* ── Milky Way diagonal band (dark mode) ── */}
      {C.isDark && MILKY.map(([x, y, o], i) => (
        <View
          key={`mw${i}`}
          style={{
            position: "absolute",
            width: W * 0.28,
            height: W * 0.28,
            borderRadius: W * 0.14,
            backgroundColor: `rgba(180,190,255,${o})`,
            left: W * x - W * 0.14,
            top: H * y - W * 0.14,
            opacity: 0.5,
          }}
        />
      ))}

      {/* ── Galaxy nebula color washes ── */}
      {C.isDark ? (
        <>
          {/* Deep purple wash — top */}
          <LinearGradient
            colors={["rgba(60,20,120,0.30)", "rgba(40,10,90,0.15)", "transparent"]}
            style={[s.wash, { top: 0, height: H * 0.45 }]}
            start={{ x: 0.5, y: 0 }} end={{ x: 0.5, y: 1 }}
          />
          {/* Blue-indigo wash — bottom */}
          <LinearGradient
            colors={["transparent", "rgba(20,10,80,0.20)", "rgba(30,5,70,0.30)"]}
            style={[s.wash, { bottom: 0, height: H * 0.40 }]}
            start={{ x: 0.5, y: 0 }} end={{ x: 0.5, y: 1 }}
          />
          {/* Warm amber core glow — center-right */}
          <View style={{
            position: "absolute",
            width: W * 0.70,
            height: W * 0.70,
            borderRadius: W * 0.35,
            backgroundColor: "rgba(180,80,20,0.06)",
            top: H * 0.20,
            right: -W * 0.20,
          }} />
        </>
      ) : (
        <LinearGradient
          colors={["rgba(139,92,246,0.06)", "rgba(109,40,217,0.03)", "transparent"]}
          style={[s.wash, { top: 0, height: H * 0.40 }]}
          start={{ x: 0.5, y: 0 }} end={{ x: 0.5, y: 1 }}
        />
      )}

      {/* ── Stars ── */}
      {STARS.map(([x, y, size, opacity], i) => (
        <View
          key={`st${i}`}
          style={{
            position: "absolute",
            width: size,
            height: size,
            borderRadius: size / 2,
            backgroundColor: i % 7 === 0
              ? `rgba(180,200,255,${C.isDark ? opacity : opacity * 0.5})`   // blue-tint
              : i % 11 === 0
              ? `rgba(255,240,180,${C.isDark ? opacity : opacity * 0.4})`   // warm-tint
              : `rgba(255,255,255,${C.isDark ? opacity : opacity * 0.4})`,  // white
            left: W * x,
            top: H * y,
          }}
        />
      ))}

      {/* ── Sparkle cross on very bright stars ── */}
      {C.isDark && (
        <>
          {[[0.26, 0.08], [0.74, 0.13], [0.42, 0.60], [0.87, 0.58], [0.11, 0.88]].map(([x, y], i) => (
            <React.Fragment key={`sp${i}`}>
              <View style={{ position:"absolute", width:9, height:1, backgroundColor:"rgba(255,255,255,0.35)", left:W*x-4, top:H*y }} />
              <View style={{ position:"absolute", width:1, height:9, backgroundColor:"rgba(255,255,255,0.35)", left:W*x, top:H*y-4 }} />
            </React.Fragment>
          ))}
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
  wash: {
    position: "absolute",
    left: 0,
    width: W,
  },
  content: {
    flex: 1,
  },
});
