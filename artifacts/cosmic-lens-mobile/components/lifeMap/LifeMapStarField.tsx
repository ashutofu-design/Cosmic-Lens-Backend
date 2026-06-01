import React, { useEffect, useRef } from "react";
import { Animated, Easing, StyleSheet, View } from "react-native";

import { useC } from "@/context/ThemeContext";

const STAR_COUNT = 16;
const STARS = Array.from({ length: STAR_COUNT }, (_, i) => ({
  x: (7 + i * 23 + (i % 5) * 13) % 95,
  y: (3 + i * 17 + (i % 4) * 11) % 92,
  size: 1 + (i % 4) * 0.6,
  delay: i * 200,
  bright: i % 5 === 0,
}));

export function LifeMapStarField() {
  const C = useC();
  const driftAnims = useRef(STARS.map(() => new Animated.Value(0))).current;
  const opacityAnims = useRef(STARS.map(() => new Animated.Value(0.1))).current;

  useEffect(() => {
    const drifts = driftAnims.map((anim, i) =>
      Animated.loop(
        Animated.sequence([
          Animated.timing(anim, {
            toValue: 8 + (i % 3) * 4,
            duration: 6000 + i * 400,
            delay: STARS[i].delay,
            easing: Easing.inOut(Easing.sin),
            useNativeDriver: true,
          }),
          Animated.timing(anim, {
            toValue: 0,
            duration: 6000 + i * 400,
            easing: Easing.inOut(Easing.sin),
            useNativeDriver: true,
          }),
        ]),
      ),
    );

    const twinkles = opacityAnims.map((anim, i) =>
      Animated.loop(
        Animated.sequence([
          Animated.timing(anim, {
            toValue: STARS[i].bright ? 0.8 : 0.45,
            duration: 2200 + i * 180,
            delay: STARS[i].delay + 100,
            easing: Easing.inOut(Easing.sin),
            useNativeDriver: true,
          }),
          Animated.timing(anim, {
            toValue: 0.08,
            duration: 2200 + i * 180,
            easing: Easing.inOut(Easing.sin),
            useNativeDriver: true,
          }),
        ]),
      ),
    );

    const all = [...drifts, ...twinkles];
    Animated.stagger(80, all).start();
    return () => all.forEach(a => a.stop());
  }, []);

  return (
    <View style={StyleSheet.absoluteFill} pointerEvents="none">
      {STARS.map((star, i) => (
        <Animated.View
          key={i}
          style={{
            position: "absolute",
            left: `${star.x}%`,
            top: `${star.y}%`,
            width: star.bright ? star.size * 3 : star.size * 2,
            height: star.bright ? star.size * 3 : star.size * 2,
            borderRadius: star.size * 2,
            backgroundColor: C.isDark
              ? star.bright ? "rgba(245,158,11,0.9)" : "rgba(255,255,255,0.75)"
              : star.bright ? "rgba(124,58,237,0.4)" : "rgba(124,58,237,0.2)",
            opacity: opacityAnims[i],
            transform: [{ translateY: driftAnims[i] }],
          }}
        />
      ))}
    </View>
  );
}
