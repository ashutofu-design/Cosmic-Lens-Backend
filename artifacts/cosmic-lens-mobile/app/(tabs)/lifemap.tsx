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
  ScrollView,
  StatusBar,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { CosmicBg } from "@/components/CosmicBg";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useC } from "@/context/ThemeContext";
import { useUser } from "@/context/UserContext";
import { getT } from "@/lib/i18n";

interface Category {
  key: string;
  icon: React.ComponentProps<typeof Feather>["name"];
  emoji: string;
  gradient: [string, string];
  glowOuter: [string, string];
  glowColor: string;
  badge: string;
  badgeIcon: string;
  subtitle: string;
  primary?: boolean;
  route?: string;
}

const CATEGORIES: Category[] = [
  {
    key: "relationship",
    icon: "heart",
    emoji: "💕",
    gradient: ["#ff4d8d", "#c026d3"],
    glowOuter: ["rgba(255,77,141,0.25)", "rgba(192,38,211,0.12)"],
    glowColor: "#ff4d8d",
    badge: "Most Used",
    badgeIcon: "🔥",
    subtitle: "Love & marriage future insights",
    primary: true,
    route: "/relationship",
  },
  {
    key: "career",
    icon: "briefcase",
    emoji: "🚀",
    gradient: ["#ff7b00", "#fbbf24"],
    glowOuter: ["rgba(255,123,0,0.2)", "rgba(251,191,36,0.08)"],
    glowColor: "#ff9500",
    badge: "Trending",
    badgeIcon: "🚀",
    subtitle: "Career growth & breakthrough insights",
    route: "/career",
  },
  {
    key: "health",
    icon: "activity",
    emoji: "🧘",
    gradient: ["#00e676", "#14b8a6"],
    glowOuter: ["rgba(0,230,118,0.18)", "rgba(20,184,166,0.08)"],
    glowColor: "#00e676",
    badge: "Check Now",
    badgeIcon: "⚠️",
    subtitle: "Energy, health & risk prediction",
    route: "/health",
  },
  {
    key: "finance",
    icon: "dollar-sign",
    emoji: "💰",
    gradient: ["#448aff", "#fbbf24"],
    glowOuter: ["rgba(68,138,255,0.2)", "rgba(251,191,36,0.08)"],
    glowColor: "#448aff",
    badge: "Important",
    badgeIcon: "💰",
    subtitle: "Money flow & financial future",
    route: "/finance",
  },
  {
    key: "divya-prashna",
    icon: "help-circle",
    emoji: "🔮",
    gradient: ["#8b5cf6", "#f59e0b"],
    glowOuter: ["rgba(139,92,246,0.22)", "rgba(245,158,11,0.10)"],
    glowColor: "#8b5cf6",
    badge: "KP Horary",
    badgeIcon: "✨",
    subtitle: "Ek hi sawaal — instant verdict (KP 1-249 sub-lord)",
    route: "/divya-prashna",
  },
  {
    key: "six-month-future",
    icon: "calendar",
    emoji: "🗓️",
    gradient: ["#a78bfa", "#6366f1"],
    glowOuter: ["rgba(167,139,250,0.22)", "rgba(99,102,241,0.10)"],
    glowColor: "#a78bfa",
    badge: "New",
    badgeIcon: "⚡",
    subtitle: "Agle 6 mahine — MD/AD/PD ke saath month-by-month outlook",
    route: "/six-month-future",
  },
];

const STAR_COUNT = 16;
const STARS = Array.from({ length: STAR_COUNT }, (_, i) => ({
  x: (7 + i * 23 + (i % 5) * 13) % 95,
  y: (3 + i * 17 + (i % 4) * 11) % 92,
  size: 1 + (i % 4) * 0.6,
  delay: i * 200,
  bright: i % 5 === 0,
}));

function StarField() {
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
        ])
      )
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
        ])
      )
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

function CategoryCard({
  cat, index, C, t,
}: {
  cat: Category;
  index: number;
  C: ReturnType<typeof useC>;
  t: ReturnType<typeof getT>;
}) {
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
      ])
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
      ])
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
      ])
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
      ])
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

  const title = titles[cat.key] || cat.key;
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
          if (cat.route) router.push(cat.route as any);
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

export default function LifeMapScreen() {
  const C = useC();
  const { language } = useUser();
  const t = getT(language);
  const insets = useSafeAreaInsets();
  const androidSB = StatusBar.currentHeight ?? 24;
  const topPad = Platform.OS === "android" ? Math.max(insets.top, androidSB) : insets.top;
  const botPad = insets.bottom;
  const isDark = C.isDark;
  const ac = isDark ? "#f59e0b" : "#7C3AED";

  const headerFade = useRef(new Animated.Value(0)).current;
  const headerSlide = useRef(new Animated.Value(-20)).current;
  useEffect(() => {
    Animated.parallel([
      Animated.timing(headerFade, { toValue: 1, duration: 800, useNativeDriver: true }),
      Animated.spring(headerSlide, { toValue: 0, useNativeDriver: true, speed: 12, bounciness: 5 }),
    ]).start();
  }, []);

  return (
    <CosmicBg>
      <LinearGradient
        colors={isDark
          ? ["rgba(0,0,0,0.3)", "transparent", "rgba(0,0,0,0.15)"]
          : ["rgba(255,255,255,0.1)", "transparent", "rgba(255,255,255,0.05)"]}
        locations={[0, 0.4, 1]}
        style={StyleSheet.absoluteFill}
        pointerEvents="none"
      />
      <StarField />

      <ScrollView
        style={s.root}
        contentContainerStyle={[s.content, { paddingTop: topPad + 20, paddingBottom: botPad + 130 }]}
        showsVerticalScrollIndicator={false}
      >
        <Animated.View style={[s.headerWrap, { opacity: headerFade, transform: [{ translateY: headerSlide }] }]}>
          <View style={s.headerBadge}>
            <LinearGradient
              colors={isDark ? ["#f59e0b", "#d97706"] : ["#7C3AED", "#6D5DF6"]}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 0 }}
              style={s.headerBadgeGrad}
            >
              <Feather name="map" size={10} color="#fff" />
              <Text style={s.headerBadgeText}>LIFE MAP</Text>
            </LinearGradient>
          </View>

          <View style={s.headingRow}>
            <Text style={[s.heading, { color: isDark ? "#fff" : "#0F172A", fontFamily: "Nunito_700Bold" }]}>
              Life{" "}
            </Text>
            <Text style={[s.heading, { color: ac, fontFamily: "Nunito_700Bold" }]}>
              Map
            </Text>
            <Text style={[s.headingEmoji]}>  ✨</Text>
          </View>
          <Text style={[s.subtitle, {
            color: isDark ? "rgba(203,213,225,0.5)" : "#64748B",
            fontFamily: "Nunito_400Regular",
          }]}>
            Your destiny, mapped by the stars
          </Text>
        </Animated.View>

        <View style={s.grid}>
          {CATEGORIES.map((cat, i) => (
            <CategoryCard key={cat.key} cat={cat} index={i} C={C} t={t} />
          ))}
        </View>

        <View style={[
          s.footerCard,
          {
            borderColor: isDark ? `${ac}20` : `${ac}0C`,
            borderWidth: isDark ? 1 : 0,
            shadowColor: isDark ? ac : "rgba(80,60,120,0.15)",
            shadowOpacity: isDark ? 0.08 : 0.2,
            shadowRadius: isDark ? 10 : 18,
            shadowOffset: { width: 0, height: isDark ? 3 : 6 },
            elevation: isDark ? 3 : 7,
          },
        ]}>
          {Platform.OS !== "web" ? (
            <BlurView
              intensity={isDark ? 35 : 50}
              tint={isDark ? "dark" : "light"}
              style={StyleSheet.absoluteFill}
            />
          ) : null}
          <View style={[StyleSheet.absoluteFill, {
            backgroundColor: isDark ? "rgba(14,22,42,0.55)" : "rgba(255,255,255,0.9)",
            borderRadius: 22,
          }]} />

          <View style={s.footerRow}>
            <View style={[s.footerIcon, { backgroundColor: isDark ? `${ac}14` : `${ac}0C` }]}>
              <Feather name="compass" size={18} color={ac} />
            </View>
            <View style={{ flex: 1 }}>
              <Text style={[s.footerTitle, { color: isDark ? "rgba(255,255,255,0.6)" : "#475569", fontFamily: "Nunito_600SemiBold" }]}>
                {t.lifeMapComing ?? "More dimensions coming"}
              </Text>
              <Text style={[s.footerSub, { color: isDark ? "rgba(255,255,255,0.3)" : "#94A3B8", fontFamily: "Nunito_400Regular" }]}>
                {t.lifeMapComingSub ?? "Education, Travel, Spirituality & more"}
              </Text>
            </View>
          </View>
        </View>
      </ScrollView>
    </CosmicBg>
  );
}

const s = StyleSheet.create({
  root: { flex: 1 },
  content: { paddingHorizontal: 20, gap: 20 },

  headerWrap: { gap: 6, marginBottom: 10 },
  headerBadge: { alignSelf: "flex-start", marginBottom: 12 },
  headerBadgeGrad: {
    flexDirection: "row",
    alignItems: "center",
    gap: 5,
    paddingHorizontal: 13,
    paddingVertical: 6,
    borderRadius: 20,
  },
  headerBadgeText: {
    color: "#fff",
    fontSize: 9,
    fontFamily: "Nunito_800ExtraBold",
    letterSpacing: 1.8,
  },

  headingRow: { flexDirection: "row", alignItems: "baseline" },
  heading: { fontSize: 32, letterSpacing: -0.5 },
  headingEmoji: { fontSize: 22 },
  subtitle: { fontSize: 13.5, letterSpacing: 0.2, marginTop: 2 },

  grid: { gap: 20 },

  card: {
    borderRadius: 22,
    overflow: "hidden",
  },
  cardPrimary: {
    borderRadius: 26,
  },

  mostUsedWrap: {
    position: "absolute",
    top: 0,
    right: 0,
    zIndex: 10,
  },
  mostUsedBadge: {
    flexDirection: "row",
    alignItems: "center",
    gap: 5,
    paddingHorizontal: 13,
    paddingVertical: 6,
    borderBottomLeftRadius: 16,
    borderTopRightRadius: 24,
  },
  mostUsedDot: {
    width: 5,
    height: 5,
    borderRadius: 3,
    backgroundColor: "#fff",
    opacity: 0.9,
  },
  mostUsedText: {
    color: "#fff",
    fontSize: 8.5,
    fontFamily: "Nunito_800ExtraBold",
    letterSpacing: 1.2,
  },

  cardRow: {
    flexDirection: "row",
    alignItems: "center",
    padding: 20,
    paddingVertical: 22,
    gap: 16,
  },
  cardRowPrimary: {
    paddingVertical: 28,
    padding: 22,
  },

  iconOuter: {
    width: 58,
    height: 58,
    alignItems: "center",
    justifyContent: "center",
  },
  iconOuterPrimary: {
    width: 68,
    height: 68,
  },
  iconGlow: {
    ...StyleSheet.absoluteFillObject,
    borderRadius: 29,
  },
  iconGlowPrimary: {
    borderRadius: 34,
  },
  iconWrap: {
    width: 52,
    height: 52,
    borderRadius: 17,
    alignItems: "center",
    justifyContent: "center",
    borderWidth: 1,
    borderColor: "rgba(255,255,255,0.12)",
  },
  iconWrapPrimary: {
    width: 62,
    height: 62,
    borderRadius: 21,
  },
  emoji: { fontSize: 24 },
  cardText: { flex: 1, gap: 6 },
  cardTitle: { fontSize: 18, letterSpacing: -0.2 },
  cardTitlePrimary: { fontSize: 21 },
  cardSub: { fontSize: 12.5, letterSpacing: 0.15 },

  badge: {
    paddingHorizontal: 9,
    paddingVertical: 3,
    borderRadius: 12,
    borderWidth: 1,
  },
  badgeLabel: {
    fontSize: 8,
    fontFamily: "Nunito_700Bold",
    letterSpacing: 0.5,
  },

  arrowBtn: {
    elevation: 8,
  },
  arrowGrad: {
    width: 42,
    height: 42,
    borderRadius: 21,
    alignItems: "center",
    justifyContent: "center",
    borderWidth: 1.5,
    borderColor: "rgba(255,255,255,0.2)",
  },
  arrowGradPrimary: {
    width: 50,
    height: 50,
    borderRadius: 25,
  },
  bottomBar: {
    height: 3,
    borderRadius: 2,
    opacity: 0.6,
  },
  bottomBarPrimary: {
    height: 3.5,
    opacity: 0.8,
  },

  footerCard: {
    borderRadius: 22,
    overflow: "hidden",
    padding: 18,
    marginTop: 4,
  },
  footerRow: { flexDirection: "row", alignItems: "center", gap: 14 },
  footerIcon: {
    width: 44,
    height: 44,
    borderRadius: 15,
    alignItems: "center",
    justifyContent: "center",
  },
  footerTitle: { fontSize: 13.5, letterSpacing: 0.1 },
  footerSub: { fontSize: 11.5, marginTop: 3 },
});
