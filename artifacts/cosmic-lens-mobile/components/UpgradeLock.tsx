/**
 * UpgradeLock — Reusable lock overlay for premium features.
 *
 * Two modes:
 *   1. Inline banner (compact: true) — small upgrade prompt below content
 *   2. Full overlay (compact: false) — covers the entire feature area
 *
 * Uses theme accent automatically (gold in dark, purple in light).
 */

import React from "react";
import {
  Pressable,
  StyleSheet,
  Text,
  View,
  ViewStyle,
} from "react-native";
import { Feather } from "@expo/vector-icons";
import { LinearGradient } from "expo-linear-gradient";
import { router } from "expo-router";
import * as Haptics from "expo-haptics";
import { useC } from "@/context/ThemeContext";
import { UPGRADE_COPY } from "@/lib/subscription";

type Tier = "basic" | "pro";

interface Props {
  /** Required tier ("basic" or "pro") — controls badge label */
  tier?: Tier;
  /** Headline message shown in the lock */
  title?: string;
  /** Sub-message — defaults to standard upgrade copy */
  message?: string;
  /** Compact inline banner instead of full overlay */
  compact?: boolean;
  /** Custom CTA label (default "Upgrade to Pro 🔓") */
  cta?: string;
  /** Override navigation target */
  onPress?: () => void;
  /** Wrap style */
  style?: ViewStyle;
}

const F = {
  regular:  "Nunito_400Regular",
  medium:   "Nunito_500Medium",
  semibold: "Nunito_600SemiBold",
  bold:     "Nunito_700Bold",
} as const;

export default function UpgradeLock({
  tier    = "pro",
  title,
  message = UPGRADE_COPY.feature,
  compact = false,
  cta,
  onPress,
  style,
}: Props) {
  const C = useC();
  const accent = tier === "pro" ? "#f59e0b" : "#a78bfa";
  const ctaLabel = cta ?? (tier === "pro" ? "Upgrade to Pro 🔓" : "Get Basic 🔓");
  const titleText = title ?? (tier === "pro" ? "Pro Feature" : "Basic Feature");

  const handlePress = () => {
    if (onPress) return onPress();
    try { Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium); } catch {}
    router.push("/subscription");
  };

  // ── Compact inline banner ──────────────────────────────────────────────────
  if (compact) {
    return (
      <Pressable
        onPress={handlePress}
        style={({ pressed }) => [
          s.compact,
          {
            backgroundColor: C.isDark ? `${accent}10` : `${accent}10`,
            borderColor:     `${accent}40`,
            opacity:         pressed ? 0.85 : 1,
          },
          style,
        ]}
      >
        <View style={[s.compactIcon, { backgroundColor: `${accent}20` }]}>
          <Feather name="lock" size={12} color={accent} />
        </View>
        <View style={{ flex: 1 }}>
          <Text style={[s.compactTitle, { color: C.text }]} numberOfLines={1}>
            {titleText}
          </Text>
          <Text style={[s.compactMsg, { color: C.textMuted }]} numberOfLines={2}>
            {message}
          </Text>
        </View>
        <Feather name="chevron-right" size={16} color={accent} />
      </Pressable>
    );
  }

  // ── Full overlay card ──────────────────────────────────────────────────────
  return (
    <View style={[s.card, { backgroundColor: C.bgCard, borderColor: `${accent}35` }, style]}>
      <View style={[s.iconWrap, { backgroundColor: `${accent}1A`, borderColor: `${accent}40` }]}>
        <Feather name="lock" size={22} color={accent} />
      </View>

      <Text style={[s.title, { color: C.text }]}>{titleText}</Text>
      <Text style={[s.msg, { color: C.textMid }]}>{message}</Text>

      <Pressable
        onPress={handlePress}
        style={({ pressed }) => [{ opacity: pressed ? 0.85 : 1, width: "100%" }]}
      >
        <LinearGradient
          colors={tier === "pro" ? ["#d97706", "#f59e0b"] : ["#7c3aed", "#a78bfa"]}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 0 }}
          style={s.cta}
        >
          <Feather name={tier === "pro" ? "zap" : "star"} size={14} color="#fff" />
          <Text style={s.ctaText}>{ctaLabel}</Text>
        </LinearGradient>
      </Pressable>
    </View>
  );
}

const s = StyleSheet.create({
  // Full overlay
  card: {
    borderRadius: 16,
    borderWidth: 1.5,
    padding: 20,
    alignItems: "center",
    gap: 10,
  },
  iconWrap: {
    width: 52, height: 52, borderRadius: 14,
    borderWidth: 1,
    alignItems: "center", justifyContent: "center",
    marginBottom: 4,
  },
  title: {
    fontSize: 16, fontFamily: F.bold,
    letterSpacing: -0.2,
    textAlign: "center",
  },
  msg: {
    fontSize: 12.5, fontFamily: F.regular,
    textAlign: "center", lineHeight: 18,
    marginBottom: 6,
  },
  cta: {
    flexDirection: "row", alignItems: "center", justifyContent: "center",
    gap: 7, paddingVertical: 12, borderRadius: 12,
  },
  ctaText: {
    color: "#fff",
    fontSize: 14, fontFamily: F.bold,
  },

  // Compact inline
  compact: {
    flexDirection: "row", alignItems: "center", gap: 10,
    borderRadius: 12, borderWidth: 1,
    paddingVertical: 10, paddingHorizontal: 12,
  },
  compactIcon: {
    width: 26, height: 26, borderRadius: 7,
    alignItems: "center", justifyContent: "center",
  },
  compactTitle: { fontSize: 12.5, fontFamily: F.bold },
  compactMsg:   { fontSize: 11, fontFamily: F.regular, lineHeight: 14, marginTop: 2 },
});
