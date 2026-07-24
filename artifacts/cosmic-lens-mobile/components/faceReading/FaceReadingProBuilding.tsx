import { Feather } from "@expo/vector-icons";
import { LinearGradient } from "expo-linear-gradient";
import React, { useEffect, useRef } from "react";
import { Animated, Easing, StyleSheet, Text, View } from "react-native";

import { useC } from "@/context/ThemeContext";
import { useT } from "@/hooks/useT";

const ACCENT = "#ec4899";
const GOLD = "#C2A878";

export function FaceReadingProBuilding() {
  const C = useC();
  const t = useT();
  const pulse = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    const loop = Animated.loop(
      Animated.sequence([
        Animated.timing(pulse, { toValue: 1, duration: 1600, easing: Easing.inOut(Easing.ease), useNativeDriver: true }),
        Animated.timing(pulse, { toValue: 0, duration: 1600, easing: Easing.inOut(Easing.ease), useNativeDriver: true }),
      ]),
    );
    loop.start();
    return () => loop.stop();
  }, [pulse]);

  const orbScale = pulse.interpolate({ inputRange: [0, 1], outputRange: [1, 1.06] });
  const orbOpacity = pulse.interpolate({ inputRange: [0, 1], outputRange: [0.5, 0.9] });

  return (
    <View style={bp.wrap}>
      <View style={[bp.card, { borderColor: C.border, backgroundColor: C.bgCard }]}>
        <LinearGradient
          colors={[`${ACCENT}22`, "transparent"]}
          start={{ x: 0.5, y: 0 }}
          end={{ x: 0.5, y: 1 }}
          style={StyleSheet.absoluteFill}
        />
        <Animated.View style={[bp.orbGlow, { opacity: orbOpacity, transform: [{ scale: orbScale }] }]} />
        <Text style={bp.emoji}>👁️</Text>

        <LinearGradient colors={[ACCENT, "#a21caf"]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }} style={bp.badge}>
          <Feather name="tool" size={11} color="#fff" />
          <Text style={bp.badgeTxt}>{t.fr_wipBadge}</Text>
        </LinearGradient>

        <Text style={[bp.title, { color: C.text }]}>{t.fr_wipTitle}</Text>

        <View style={[bp.hintBox, { borderColor: `${GOLD}44`, backgroundColor: `${GOLD}10` }]}>
          <Feather name="clock" size={14} color={GOLD} />
          <Text style={[bp.hint, { color: C.textMuted }]}>{t.fr_wipHint}</Text>
        </View>
      </View>
    </View>
  );
}

const bp = StyleSheet.create({
  wrap: { flex: 1, paddingHorizontal: 20, paddingTop: 24, justifyContent: "center" },
  card: {
    borderRadius: 22,
    borderWidth: 1,
    padding: 24,
    alignItems: "center",
    gap: 12,
    overflow: "hidden",
  },
  orbGlow: {
    position: "absolute",
    top: 28,
    width: 88,
    height: 88,
    borderRadius: 44,
    backgroundColor: "rgba(236,72,153,0.25)",
  },
  emoji: { fontSize: 44, marginTop: 4 },
  badge: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 20,
    marginTop: 4,
  },
  badgeTxt: {
    color: "#fff",
    fontSize: 10,
    fontFamily: "Nunito_800ExtraBold",
    letterSpacing: 1.2,
    textTransform: "uppercase",
  },
  title: {
    fontSize: 20,
    fontFamily: "Nunito_800ExtraBold",
    textAlign: "center",
    letterSpacing: -0.3,
    lineHeight: 26,
    marginTop: 4,
  },
  hintBox: {
    flexDirection: "row",
    alignItems: "flex-start",
    gap: 8,
    borderWidth: 1,
    borderRadius: 14,
    padding: 12,
    marginTop: 6,
    width: "100%",
  },
  hint: {
    flex: 1,
    fontSize: 12,
    fontFamily: "Nunito_600SemiBold",
    lineHeight: 18,
  },
});
