import React, { useEffect, useRef } from "react";
import { Animated, Easing, StyleSheet, Text, View, type ViewStyle } from "react-native";
import { planetEmoji } from "@/lib/futureTimelineCopy";
import type { Trend } from "@/lib/proInsightEngine";

/** Static hourglass — perpetual spin was stacking on Future tab. */
export function LiveHourglass({ size = 16 }: { size?: number }) {
  return <Text style={{ fontSize: size }}>⏳</Text>;
}

/** Static planet emoji — row-level loops were too many on a full timeline. */
export function LivePlanetEmoji({ planet, size = 22 }: { planet: string; size?: number }) {
  const emoji = planetEmoji(planet);
  return <Text style={{ fontSize: size }}>{emoji}</Text>;
}

/** Pulsing green dot + label — cosmic clock is running */
export function LiveNowBadge({ label, color = "#4ade80" }: { label: string; color?: string }) {
  const pulse = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    const anim = Animated.loop(
      Animated.sequence([
        Animated.timing(pulse, { toValue: 1, duration: 900, easing: Easing.inOut(Easing.ease), useNativeDriver: true }),
        Animated.timing(pulse, { toValue: 0, duration: 900, easing: Easing.inOut(Easing.ease), useNativeDriver: true }),
      ]),
    );
    anim.start();
    return () => anim.stop();
  }, [pulse]);

  const dotScale = pulse.interpolate({ inputRange: [0, 1], outputRange: [1, 1.45] });
  const dotOpacity = pulse.interpolate({ inputRange: [0, 1], outputRange: [0.55, 1] });
  const glowOpacity = pulse.interpolate({ inputRange: [0, 1], outputRange: [0.15, 0.45] });

  return (
    <View style={lb.row}>
      <View style={lb.dotWrap}>
        <Animated.View style={[lb.glow, { backgroundColor: color, opacity: glowOpacity }]} />
        <Animated.View style={[lb.dot, { backgroundColor: color, opacity: dotOpacity, transform: [{ scale: dotScale }] }]} />
      </View>
      <Text style={[lb.label, { color }]}>{label}</Text>
    </View>
  );
}

/** Static trend arrow — bounce loops multiplied across Future rows. */
export function LiveTrendArrow({ trend, color, size = 16 }: { trend: Trend; color: string; size?: number }) {
  const arrow = trend === "UP" ? "↑" : trend === "DOWN" ? "↓" : "→";
  return (
    <Text style={{ fontSize: size, fontFamily: "Nunito_800ExtraBold", color }}>
      {arrow}
    </Text>
  );
}

/** PD period progress — fills as time passes */
export function LiveDashaProgress({
  pct,
  color,
  trackColor,
  style,
}: {
  pct: number;
  color: string;
  trackColor: string;
  style?: ViewStyle;
}) {
  const shimmer = useRef(new Animated.Value(0)).current;
  const widthAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.timing(widthAnim, {
      toValue: Math.min(100, Math.max(0, pct)),
      duration: 800,
      easing: Easing.out(Easing.cubic),
      useNativeDriver: false,
    }).start();
  }, [pct, widthAnim]);

  useEffect(() => {
    const anim = Animated.loop(
      Animated.sequence([
        Animated.timing(shimmer, { toValue: 1, duration: 1200, easing: Easing.inOut(Easing.ease), useNativeDriver: true }),
        Animated.timing(shimmer, { toValue: 0, duration: 1200, easing: Easing.inOut(Easing.ease), useNativeDriver: true }),
      ]),
    );
    anim.start();
    return () => anim.stop();
  }, [shimmer]);

  const barWidth = widthAnim.interpolate({ inputRange: [0, 100], outputRange: ["0%", "100%"] });
  const fillOpacity = shimmer.interpolate({ inputRange: [0, 1], outputRange: [0.85, 1] });

  // width (JS-driven) and opacity (native-driven) must live on separate
  // Animated nodes — mixing them in one style crashes Android with
  // "Attempting to run JS driven animation on animated node ... 'native'".
  return (
    <View style={[pb.track, { backgroundColor: trackColor }, style]}>
      <Animated.View style={[pb.fill, { width: barWidth }]}>
        <Animated.View
          style={[StyleSheet.absoluteFillObject, { backgroundColor: color, opacity: fillOpacity }]}
        />
      </Animated.View>
    </View>
  );
}

/** Soft breathing glow behind hero card */
export function LiveHeroGlow({ color }: { color: string }) {
  const glow = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    const anim = Animated.loop(
      Animated.sequence([
        Animated.timing(glow, { toValue: 1, duration: 2800, easing: Easing.inOut(Easing.ease), useNativeDriver: true }),
        Animated.timing(glow, { toValue: 0, duration: 2800, easing: Easing.inOut(Easing.ease), useNativeDriver: true }),
      ]),
    );
    anim.start();
    return () => anim.stop();
  }, [glow]);

  const opacity = glow.interpolate({ inputRange: [0, 1], outputRange: [0.25, 0.55] });
  const scale = glow.interpolate({ inputRange: [0, 1], outputRange: [1, 1.06] });

  return (
    <Animated.View
      pointerEvents="none"
      style={[hg.glow, { backgroundColor: color, opacity, transform: [{ scale }] }]}
    />
  );
}

export function pdElapsedPct(start: Date | null, end: Date | null): number {
  if (!start || !end) return 0;
  const total = end.getTime() - start.getTime();
  if (total <= 0) return 0;
  return Math.min(100, Math.max(0, ((Date.now() - start.getTime()) / total) * 100));
}

const lb = StyleSheet.create({
  row: { flexDirection: "row", alignItems: "center", gap: 7 },
  dotWrap: { width: 14, height: 14, alignItems: "center", justifyContent: "center" },
  glow: { position: "absolute", width: 14, height: 14, borderRadius: 7 },
  dot: { width: 7, height: 7, borderRadius: 4 },
  label: { fontSize: 11, fontFamily: "Nunito_700Bold", letterSpacing: 0.6 },
});

const pb = StyleSheet.create({
  track: { height: 5, borderRadius: 3, overflow: "hidden" },
  fill: { height: "100%", borderRadius: 3 },
});

const hg = StyleSheet.create({
  glow: {
    position: "absolute",
    top: -20,
    right: -20,
    width: 100,
    height: 100,
    borderRadius: 50,
  },
});
