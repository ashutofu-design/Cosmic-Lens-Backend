import { Feather } from "@expo/vector-icons";
import { BlurView } from "expo-blur";
import * as Haptics from "expo-haptics";
import { LinearGradient } from "expo-linear-gradient";
import { router } from "expo-router";
import React, { useEffect, useRef } from "react";
import {
  Animated,
  Easing,
  Platform,
  Pressable,
  StyleSheet,
  Text,
  View,
} from "react-native";

import { useC } from "@/context/ThemeContext";
import { useUser } from "@/context/UserContext";
import { useT } from "@/hooks/useT";
import { gateCareerLifeMapAccess } from "@/lib/careerCheckoutFlow";
import type { LifeMapCategory } from "@/lib/lifeMapData";

export function LifeMapCategoryCard({
  cat,
  index,
}: {
  cat: LifeMapCategory;
  index: number;
}) {
  const C = useC();
  const t = useT();
  const { user } = useUser();
  const scaleAnim = useRef(new Animated.Value(1)).current;
  const pulseAnim = useRef(new Animated.Value(1)).current;
  const glowAnim = useRef(new Animated.Value(0.25)).current;
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const slideAnim = useRef(new Animated.Value(30)).current;
  const arrowPulse = useRef(new Animated.Value(1)).current;
  const arrowGlow = useRef(new Animated.Value(0.5)).current;

  useEffect(() => {
    const pulse = Animated.loop(
      Animated.sequence([
        Animated.timing(pulseAnim, {
          toValue: 1.25,
          duration: 2200,
          delay: index * 300,
          easing: Easing.inOut(Easing.sin),
          useNativeDriver: true,
        }),
        Animated.timing(pulseAnim, {
          toValue: 1,
          duration: 2200,
          easing: Easing.inOut(Easing.sin),
          useNativeDriver: true,
        }),
      ]),
    );
    const glow = Animated.loop(
      Animated.sequence([
        Animated.timing(glowAnim, {
          toValue: cat.primary ? 0.65 : 0.45,
          duration: 2800,
          delay: index * 200,
          easing: Easing.inOut(Easing.sin),
          useNativeDriver: true,
        }),
        Animated.timing(glowAnim, {
          toValue: cat.primary ? 0.3 : 0.15,
          duration: 2800,
          easing: Easing.inOut(Easing.sin),
          useNativeDriver: true,
        }),
      ]),
    );
    const arrow = Animated.loop(
      Animated.sequence([
        Animated.timing(arrowPulse, {
          toValue: 1.15,
          duration: 1200,
          delay: index * 100,
          easing: Easing.inOut(Easing.sin),
          useNativeDriver: true,
        }),
        Animated.timing(arrowPulse, {
          toValue: 1,
          duration: 1200,
          easing: Easing.inOut(Easing.sin),
          useNativeDriver: true,
        }),
      ]),
    );
    const aGlow = Animated.loop(
      Animated.sequence([
        Animated.timing(arrowGlow, {
          toValue: 1,
          duration: 1500,
          delay: index * 120,
          easing: Easing.inOut(Easing.sin),
          useNativeDriver: true,
        }),
        Animated.timing(arrowGlow, {
          toValue: 0.4,
          duration: 1500,
          easing: Easing.inOut(Easing.sin),
          useNativeDriver: true,
        }),
      ]),
    );
    const entrance = Animated.parallel([
      Animated.timing(fadeAnim, { toValue: 1, duration: 600, delay: 120 + index * 120, useNativeDriver: true }),
      Animated.spring(slideAnim, { toValue: 0, delay: 120 + index * 120, useNativeDriver: true, speed: 14, bounciness: 4 }),
    ]);
    pulse.start();
    glow.start();
    arrow.start();
    aGlow.start();
    entrance.start();
    return () => { pulse.stop(); glow.stop(); arrow.stop(); aGlow.stop(); };
  }, []);

  const titles: Record<string, string> = {
    relationship: t.relationship,
    career: t.career,
    health: t.health,
    finance: t.finance,
    "divya-prashna": "Divya Prashna",
  };

  const title = cat.title ?? titles[cat.key] ?? cat.key;
  const sub = cat.subtitle;
  const [c1, c2] = cat.gradient;
  const isDark = C.isDark;
  const isPrimary = !!cat.primary;

  const cardBg = isDark
    ? isPrimary ? "rgba(50,10,35,0.78)" : "rgba(14,22,42,0.72)"
    : isPrimary ? "rgba(255,228,240,0.96)" : "rgba(255,255,255,0.94)";

  function handlePressIn() {
    Animated.parallel([
      Animated.spring(scaleAnim, { toValue: 0.955, useNativeDriver: true, speed: 50, bounciness: 4 }),
      Animated.timing(glowAnim, { toValue: 0.9, duration: 100, useNativeDriver: true }),
    ]).start();
  }
  function handlePressOut() {
    Animated.parallel([
      Animated.spring(scaleAnim, { toValue: 1, useNativeDriver: true, speed: 18, bounciness: 10 }),
      Animated.timing(glowAnim, { toValue: isPrimary ? 0.35 : 0.2, duration: 500, useNativeDriver: true }),
    ]).start();
  }

  return (
    <Animated.View style={{ transform: [{ scale: scaleAnim }, { translateY: slideAnim }], opacity: fadeAnim }}>
      <Pressable
        onPressIn={handlePressIn}
        onPressOut={handlePressOut}
        onPress={() => {
          Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
          if (!cat.route) return;
          if (cat.paywall && cat.key === "career") {
            void gateCareerLifeMapAccess({ user });
            return;
          }
          if (cat.navTab) {
            router.push({ pathname: cat.route, params: { tab: cat.navTab } } as any);
          } else if (cat.route) {
            router.push(cat.route as any);
          }
        }}
      >
        <View style={[
          s.card,
          isPrimary && s.cardPrimary,
          {
            shadowColor: cat.glowColor,
            shadowOpacity: isDark ? (isPrimary ? 0.6 : 0.35) : (isPrimary ? 0.25 : 0.12),
            shadowRadius: isPrimary ? 32 : 22,
            shadowOffset: { width: 0, height: isPrimary ? 10 : 6 },
            elevation: isPrimary ? 14 : 8,
          },
        ]}>
          {Platform.OS !== "web" ? (
            <BlurView
              intensity={isDark ? 45 : 55}
              tint={isDark ? "dark" : "light"}
              style={StyleSheet.absoluteFill}
            />
          ) : null}
          <View style={[StyleSheet.absoluteFill, {
            backgroundColor: cardBg,
            borderRadius: isPrimary ? 26 : 22,
          }]} />

          <Animated.View style={[
            StyleSheet.absoluteFill,
            { overflow: "hidden", borderRadius: isPrimary ? 26 : 22, opacity: glowAnim },
          ]}>
            <LinearGradient
              colors={isDark
                ? [cat.glowOuter[0], cat.glowOuter[1], "transparent"]
                : [`${cat.glowColor}15`, `${cat.glowColor}08`, "transparent"]}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 1 }}
              style={StyleSheet.absoluteFill}
            />
          </Animated.View>

          {isDark && (
            <LinearGradient
              colors={[`${cat.glowColor}08`, "transparent"]}
              start={{ x: 0.5, y: 1 }}
              end={{ x: 0.5, y: 0.3 }}
              style={[StyleSheet.absoluteFill, { borderRadius: isPrimary ? 26 : 22 }]}
            />
          )}

          <View style={[StyleSheet.absoluteFill, {
            borderRadius: isPrimary ? 26 : 22,
            borderWidth: isDark ? 1.2 : 0.6,
            borderColor: isDark
              ? `${cat.glowColor}${isPrimary ? "50" : "28"}`
              : `${cat.glowColor}${isPrimary ? "22" : "0C"}`,
          }]} />

          <LinearGradient
            colors={isDark
              ? ["rgba(255,255,255,0.06)", "rgba(255,255,255,0.01)", "transparent"]
              : ["rgba(255,255,255,0.5)", "rgba(255,255,255,0.1)", "transparent"]}
            start={{ x: 0, y: 0 }}
            end={{ x: 0, y: 1 }}
            style={[StyleSheet.absoluteFill, { borderRadius: isPrimary ? 26 : 22, height: "45%" }]}
          />

          {isPrimary && (
            <View style={s.mostUsedWrap}>
              <LinearGradient
                colors={isDark ? ["#ff4d8d", "#c026d3"] : ["#e91e63", "#9c27b0"]}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 0 }}
                style={s.mostUsedBadge}
              >
                <View style={s.mostUsedDot} />
                <Text style={s.mostUsedText}>{cat.badgeIcon} {cat.badge.toUpperCase()}</Text>
              </LinearGradient>
            </View>
          )}

          <View style={[s.cardRow, isPrimary && s.cardRowPrimary]}>
            <View style={[s.iconOuter, isPrimary && s.iconOuterPrimary]}>
              <Animated.View style={[
                s.iconGlow,
                isPrimary && s.iconGlowPrimary,
                {
                  backgroundColor: `${cat.glowColor}${isPrimary ? "30" : "1A"}`,
                  transform: [{ scale: pulseAnim }],
                },
              ]} />
              <LinearGradient
                colors={[c1, c2]}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 1 }}
                style={[s.iconWrap, isPrimary && s.iconWrapPrimary]}
              >
                <Text style={[s.emoji, isPrimary && { fontSize: 30 }]}>{cat.emoji}</Text>
              </LinearGradient>
            </View>

            <View style={s.cardText}>
              <View style={{ flexDirection: "row", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
                <Text style={[
                  s.cardTitle,
                  isPrimary && s.cardTitlePrimary,
                  { color: isDark ? "#fff" : "#0F172A", fontFamily: "Nunito_700Bold" },
                ]}>
                  {title}
                </Text>
                {!isPrimary && (
                  <View style={[
                    s.badge,
                    {
                      backgroundColor: isDark ? `${cat.glowColor}18` : `${cat.glowColor}14`,
                      borderColor: isDark ? `${cat.glowColor}35` : `${cat.glowColor}28`,
                    },
                  ]}>
                    <Text style={[s.badgeLabel, { color: cat.glowColor }]}>
                      {cat.badgeIcon} {cat.badge}
                    </Text>
                  </View>
                )}
              </View>
              <Text
                style={[s.cardSub, {
                  color: isDark ? "rgba(203,213,225,0.75)" : "#64748B",
                  fontFamily: "Nunito_500Medium",
                }]}
                numberOfLines={1}
              >
                {sub}
              </Text>
              {!!cat.priceInr && cat.paywall && (
                <View style={[s.pricePill, {
                  backgroundColor: isDark ? `${cat.glowColor}22` : `${cat.glowColor}14`,
                  borderColor: isDark ? `${cat.glowColor}44` : `${cat.glowColor}30`,
                }]}>
                  <Text style={[s.pricePillText, { color: cat.glowColor }]}>
                    Unlock · ₹{cat.priceInr}
                  </Text>
                </View>
              )}
            </View>

            <Animated.View style={[s.arrowBtn, {
              shadowColor: cat.glowColor,
              shadowOpacity: isDark ? 0.7 : 0.35,
              shadowRadius: 18,
              shadowOffset: { width: 0, height: 4 },
              transform: [{ scale: arrowPulse }],
              opacity: arrowGlow,
            }]}>
              <LinearGradient
                colors={[c1, c2]}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 1 }}
                style={[s.arrowGrad, isPrimary && s.arrowGradPrimary]}
              >
                <Feather name="chevron-right" size={isPrimary ? 22 : 18} color="#fff" />
              </LinearGradient>
            </Animated.View>
          </View>

          <View style={{ paddingHorizontal: isPrimary ? 22 : 18, paddingBottom: isPrimary ? 8 : 6 }}>
            <LinearGradient
              colors={[c1, c2]}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 0 }}
              style={[s.bottomBar, isPrimary && s.bottomBarPrimary]}
            />
          </View>
        </View>
      </Pressable>
    </Animated.View>
  );
}

const s = StyleSheet.create({
  card: { borderRadius: 22, overflow: "hidden" },
  cardPrimary: { borderRadius: 26 },
  mostUsedWrap: { position: "absolute", top: 0, right: 0, zIndex: 10 },
  mostUsedBadge: {
    flexDirection: "row",
    alignItems: "center",
    gap: 5,
    paddingHorizontal: 13,
    paddingVertical: 6,
    borderBottomLeftRadius: 16,
    borderTopRightRadius: 24,
  },
  mostUsedDot: { width: 5, height: 5, borderRadius: 3, backgroundColor: "#fff", opacity: 0.9 },
  mostUsedText: { color: "#fff", fontSize: 8.5, fontFamily: "Nunito_800ExtraBold", letterSpacing: 1.2 },
  cardRow: { flexDirection: "row", alignItems: "center", padding: 20, paddingVertical: 22, gap: 16 },
  cardRowPrimary: { paddingVertical: 28, padding: 22 },
  iconOuter: { width: 58, height: 58, alignItems: "center", justifyContent: "center" },
  iconOuterPrimary: { width: 68, height: 68 },
  iconGlow: { ...StyleSheet.absoluteFillObject, borderRadius: 29 },
  iconGlowPrimary: { borderRadius: 34 },
  iconWrap: {
    width: 52, height: 52, borderRadius: 17,
    alignItems: "center", justifyContent: "center",
    borderWidth: 1, borderColor: "rgba(255,255,255,0.12)",
  },
  iconWrapPrimary: { width: 62, height: 62, borderRadius: 21 },
  emoji: { fontSize: 24 },
  cardText: { flex: 1, gap: 6 },
  cardTitle: { fontSize: 18, letterSpacing: -0.2 },
  cardTitlePrimary: { fontSize: 21 },
  cardSub: { fontSize: 12.5, letterSpacing: 0.15 },
  pricePill: {
    alignSelf: "flex-start",
    marginTop: 6,
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 999,
    borderWidth: 1,
  },
  pricePillText: { fontSize: 11, fontFamily: "Nunito_700Bold", letterSpacing: 0.2 },
  badge: { paddingHorizontal: 9, paddingVertical: 3, borderRadius: 12, borderWidth: 1 },
  badgeLabel: { fontSize: 8, fontFamily: "Nunito_700Bold", letterSpacing: 0.5 },
  arrowBtn: { elevation: 8 },
  arrowGrad: {
    width: 42, height: 42, borderRadius: 21,
    alignItems: "center", justifyContent: "center",
    borderWidth: 1.5, borderColor: "rgba(255,255,255,0.2)",
  },
  arrowGradPrimary: { width: 50, height: 50, borderRadius: 25 },
  bottomBar: { height: 3, borderRadius: 2, opacity: 0.6 },
  bottomBarPrimary: { height: 3.5, opacity: 0.8 },
});
