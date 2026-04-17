/**
 * useFeatureGate — drop-in premium-content lock for any screen.
 *
 * Adapts based on the user's plan vs. the feature's required tier:
 *
 *   ┌──────────────────┬────────────────────────────────────────────────┐
 *   │ User plan         │ Behavior                                       │
 *   ├──────────────────┼────────────────────────────────────────────────┤
 *   │ Pro              │ allowed=true,  no overlay (full content shown) │
 *   │ Basic + pro feat │ allowed=false, INLINE bottom banner (sticky)   │
 *   │                  │   → user already paid; sees content but        │
 *   │                  │     deep section is teased with upgrade CTA    │
 *   │ Free / Trial     │ allowed=false, FULL overlay (blur + lock card) │
 *   │                  │   → Back button is rendered INSIDE the card    │
 *   │                  │     so user is never trapped                   │
 *   └──────────────────┴────────────────────────────────────────────────┘
 *
 * Usage (unchanged):
 *   const { allowed, LockOverlay } = useFeatureGate("marriage_compat_full");
 *   …
 *   return (
 *     <CosmicBg>
 *       …existing content…
 *       {LockOverlay}
 *     </CosmicBg>
 *   );
 */

import React from "react";
import { Platform, Pressable, StyleSheet, Text, View } from "react-native";
import { Feather } from "@expo/vector-icons";
import { LinearGradient } from "expo-linear-gradient";
import { BlurView } from "expo-blur";
import { router } from "expo-router";
import * as Haptics from "expo-haptics";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useC } from "@/context/ThemeContext";
import {
  usePlan,
  FeatureKey,
  FEATURE_REQUIREMENT,
  UPGRADE_COPY,
} from "@/lib/subscription";

interface GateOptions {
  /** Override the auto-derived tier */
  tier?: "basic" | "pro";
  /** Custom title shown in the lock card */
  title?: string;
  /** Custom message shown in the lock card */
  message?: string;
}

const F = {
  regular:  "Nunito_400Regular",
  semibold: "Nunito_600SemiBold",
  bold:     "Nunito_700Bold",
} as const;

export function useFeatureGate(feature: FeatureKey, opts: GateOptions = {}) {
  const { has, plan } = usePlan();
  const C = useC();
  const insets = useSafeAreaInsets();

  const allowed       = has(feature);
  const requiredTier  = opts.tier ?? FEATURE_REQUIREMENT[feature];
  const accent        = requiredTier === "pro" ? "#f59e0b" : "#a78bfa";

  // Basic-tier user trying to access a Pro feature → soft inline banner.
  // (They already paid for Basic — don't hide the entire screen.)
  const isPaidUserOnHigherFeature =
    !allowed &&
    plan === "basic" &&
    requiredTier === "pro";

  const handleUpgrade = () => {
    try { Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium); } catch {}
    router.push("/subscription");
  };

  const handleBack = () => {
    try { Haptics.selectionAsync(); } catch {}
    if (router.canGoBack()) router.back();
    else router.replace("/");
  };

  // ── PRO user (or basic user on basic feature) → no lock ─────────────────
  if (allowed) {
    return { allowed: true, LockOverlay: null as React.ReactNode };
  }

  // ── BASIC user on PRO feature → bottom sticky banner ─────────────────────
  if (isPaidUserOnHigherFeature) {
    const message =
      opts.message ?? "Aapka Basic plan summary tak limited hai. Pro upgrade karke full deep analysis paayein.";

    return {
      allowed: false,
      LockOverlay: (
        <View pointerEvents="box-none" style={[s.bottomDock, { bottom: Math.max(insets.bottom + 6, 18) }]}>
          <Pressable
            onPress={handleUpgrade}
            style={({ pressed }) => [
              s.bottomCard,
              {
                backgroundColor: C.bgCard,
                borderColor:     `${accent}55`,
                opacity:         pressed ? 0.9 : 1,
              },
            ]}
          >
            <View style={[s.bottomIcon, { backgroundColor: `${accent}1F` }]}>
              <Feather name="lock" size={14} color={accent} />
            </View>
            <View style={{ flex: 1 }}>
              <Text style={[s.bottomTitle, { color: C.text }]} numberOfLines={1}>
                Pro feature
              </Text>
              <Text style={[s.bottomMsg, { color: C.textMuted }]} numberOfLines={2}>
                {message}
              </Text>
            </View>
            <LinearGradient
              colors={["#d97706", "#f59e0b"]}
              start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }}
              style={s.bottomCta}
            >
              <Feather name="zap" size={11} color="#fff" />
              <Text style={s.bottomCtaText}>Upgrade</Text>
            </LinearGradient>
          </Pressable>
        </View>
      ) as React.ReactNode,
    };
  }

  // ── FREE / TRIAL user → full-screen blur overlay with self-contained nav ─
  const fullMessage =
    opts.message ??
    (requiredTier === "pro" ? UPGRADE_COPY.proLocked : UPGRADE_COPY.basicLocked);
  const fullTitle =
    opts.title ?? (requiredTier === "pro" ? "Pro Feature" : "Basic Feature");

  const LockOverlay: React.ReactNode = (
    <View style={s.overlay} pointerEvents="auto">
      {Platform.OS === "ios" ? (
        <BlurView
          intensity={45}
          tint={C.isDark ? "dark" : "light"}
          style={StyleSheet.absoluteFillObject}
        />
      ) : (
        <View
          style={[
            StyleSheet.absoluteFillObject,
            { backgroundColor: C.isDark ? "rgba(8,5,20,0.85)" : "rgba(255,255,255,0.86)" },
          ]}
        />
      )}

      <View style={s.center}>
        <View
          style={[
            s.card,
            {
              backgroundColor: C.bgCard,
              borderColor:     `${accent}40`,
            },
          ]}
        >
          {/* Back button at top of card — user is never trapped */}
          <Pressable
            onPress={handleBack}
            hitSlop={10}
            style={({ pressed }) => [
              s.cardBack,
              { borderColor: C.border, opacity: pressed ? 0.6 : 1 },
            ]}
          >
            <Feather name="arrow-left" size={14} color={C.textMid} />
            <Text style={[s.cardBackText, { color: C.textMid }]}>Back</Text>
          </Pressable>

          <View
            style={[
              s.cardIcon,
              { backgroundColor: `${accent}1A`, borderColor: `${accent}40` },
            ]}
          >
            <Feather name="lock" size={26} color={accent} />
          </View>

          <Text style={[s.cardTitle, { color: C.text }]}>{fullTitle}</Text>
          <Text style={[s.cardMsg, { color: C.textMid }]}>{fullMessage}</Text>

          <Pressable
            onPress={handleUpgrade}
            style={({ pressed }) => [
              { width: "100%", marginTop: 8, opacity: pressed ? 0.9 : 1 },
            ]}
          >
            <LinearGradient
              colors={requiredTier === "pro" ? ["#d97706", "#f59e0b"] : ["#7c3aed", "#a78bfa"]}
              start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }}
              style={s.cardCta}
            >
              <Feather name={requiredTier === "pro" ? "zap" : "star"} size={15} color="#fff" />
              <Text style={s.cardCtaText}>
                {requiredTier === "pro" ? "Upgrade to Pro 🔓" : "Get Basic 🔓"}
              </Text>
            </LinearGradient>
          </Pressable>
        </View>
      </View>
    </View>
  );

  return { allowed: false, LockOverlay };
}

const s = StyleSheet.create({
  // ── Full overlay (free/trial users) ──────────────────────────────────────
  overlay: {
    ...StyleSheet.absoluteFillObject,
    zIndex:    999,
    elevation: 999,
  },
  center: {
    flex: 1,
    alignItems:     "center",
    justifyContent: "center",
    paddingHorizontal: 24,
  },
  card: {
    width: "100%",
    maxWidth: 360,
    borderRadius: 20,
    borderWidth: 1.5,
    padding: 24,
    paddingTop: 20,
    alignItems: "center",
    gap: 8,
  },
  cardBack: {
    alignSelf: "flex-start",
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    paddingVertical: 6,
    paddingHorizontal: 10,
    borderRadius: 10,
    borderWidth: 1,
    marginBottom: 6,
  },
  cardBackText: { fontSize: 11.5, fontFamily: F.semibold },
  cardIcon: {
    width: 60, height: 60,
    borderRadius: 16,
    borderWidth: 1.5,
    alignItems: "center", justifyContent: "center",
    marginTop: 4, marginBottom: 4,
  },
  cardTitle: {
    fontSize: 18, fontFamily: F.bold,
    letterSpacing: -0.3,
    textAlign: "center",
  },
  cardMsg: {
    fontSize: 13, fontFamily: F.regular,
    textAlign: "center",
    lineHeight: 19,
    marginBottom: 4,
  },
  cardCta: {
    flexDirection: "row", alignItems: "center", justifyContent: "center",
    gap: 8, paddingVertical: 13, borderRadius: 13,
  },
  cardCtaText: {
    color: "#fff",
    fontSize: 14.5, fontFamily: F.bold,
  },

  // ── Bottom sticky banner (basic users on pro features) ───────────────────
  bottomDock: {
    position: "absolute",
    left: 12, right: 12,
    zIndex:    998,
    elevation: 998,
  },
  bottomCard: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    paddingVertical: 10,
    paddingLeft: 12,
    paddingRight: 8,
    borderRadius: 14,
    borderWidth: 1,
    shadowColor: "#000",
    shadowOpacity: 0.18,
    shadowRadius: 12,
    shadowOffset: { width: 0, height: 4 },
  },
  bottomIcon: {
    width: 32, height: 32, borderRadius: 9,
    alignItems: "center", justifyContent: "center",
  },
  bottomTitle: { fontSize: 12.5, fontFamily: F.bold },
  bottomMsg:   { fontSize: 11, fontFamily: F.regular, lineHeight: 14, marginTop: 1 },
  bottomCta: {
    flexDirection: "row",
    alignItems: "center",
    gap: 5,
    paddingVertical: 8, paddingHorizontal: 12,
    borderRadius: 10,
  },
  bottomCtaText: {
    color: "#fff",
    fontSize: 11.5, fontFamily: F.bold,
  },
});
