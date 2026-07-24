import React from "react";
import { StyleSheet, View } from "react-native";

import { useC } from "@/context/ThemeContext";

/** Static starfield — animated loops were too heavy on Android tab switches. */
const STAR_COUNT = 12;
const STARS = Array.from({ length: STAR_COUNT }, (_, i) => ({
  x: (7 + i * 23 + (i % 5) * 13) % 95,
  y: (3 + i * 17 + (i % 4) * 11) % 92,
  size: 1 + (i % 4) * 0.6,
  bright: i % 5 === 0,
  opacity: i % 5 === 0 ? 0.55 : 0.28,
}));

export function LifeMapStarField() {
  const C = useC();

  return (
    <View style={StyleSheet.absoluteFill} pointerEvents="none">
      {STARS.map((star, i) => (
        <View
          key={i}
          style={{
            position: "absolute",
            left: `${star.x}%`,
            top: `${star.y}%`,
            width: star.bright ? star.size * 3 : star.size * 2,
            height: star.bright ? star.size * 3 : star.size * 2,
            borderRadius: star.size * 2,
            opacity: star.opacity,
            backgroundColor: C.isDark
              ? star.bright ? "rgba(245,158,11,0.9)" : "rgba(255,255,255,0.75)"
              : star.bright ? "rgba(124,58,237,0.4)" : "rgba(124,58,237,0.2)",
          }}
        />
      ))}
    </View>
  );
}
