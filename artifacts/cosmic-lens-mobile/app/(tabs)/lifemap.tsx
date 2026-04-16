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
  useWindowDimensions,
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
    glowOuter: ["rgba(255,77,141,0.18)", "rgba(192,38,211,0.08)"],
    glowColor: "#ff4d8d",
    badge: "Most Used",
    badgeIcon: "🔥",
    subtitle: "Love & marriage future insights",
    primary: true,
  },
  {
    key: "career",
    icon: "briefcase",
    emoji: "🚀",
    gradient: ["#ff7b00", "#fbbf24"],
    glowOuter: ["rgba(255,123,0,0.15)", "rgba(251,191,36,0.06)"],
    glowColor: "#ff9500",
    badge: "Trending",
    badgeIcon: "🚀",
    subtitle: "Career growth & breakthrough insights",
  },
  {
    key: "health",
    icon: "activity",
    emoji: "🧘",
    gradient: ["#00e676", "#14b8a6"],
    glowOuter: ["rgba(0,230,118,0.14)", "rgba(20,184,166,0.06)"],
    glowColor: "#00e676",
    badge: "Check Now",
    badgeIcon: "⚠️",
    subtitle: "Energy, health & risk prediction",
  },
  {
    key: "finance",
    icon: "dollar-sign",
    emoji: "💰",
    gradient: ["#448aff", "#fbbf24"],
    glowOuter: ["rgba(68,138,255,0.15)", "rgba(251,191,36,0.06)"],
    glowColor: "#448aff",
    badge: "Important",
    badgeIcon: "💰",
    subtitle: "Money flow & financial future",
  },
];

const STAR_COUNT = 12;
const STARS = Array.from({ length: STAR_COUNT }, (_, i) => ({
  x: (7 + i * 31 + (i % 3) * 17) % 95,
  y: (5 + i * 19 + (i % 4) * 11) % 88,
  size: 1 + (i % 3) * 0.5,
  delay: i * 250,
}));

function StarField() {
  const C = useC();
  const driftAnims = useRef(STARS.map(() => new Animated.Value(0))).current;
  const opacityAnims = useRef(STARS.map(() => new Animated.Value(0.15))).current;

  useEffect(() => {
    const drifts = driftAnims.map((anim, i) =>
      Animated.loop(
        Animated.sequence([
          Animated.timing(anim, {
            toValue: 6 + (i % 3) * 3,
            duration: 5000 + i * 500,
            delay: STARS[i].delay,
            easing: Easing.inOut(Easing.sin),
            useNativeDriver: true,
          }),
          Animated.timing(anim, {
            toValue: 0,
            duration: 5000 + i * 500,
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
            toValue: 0.5 + (i % 3) * 0.1,
            duration: 2000 + i * 200,
            delay: STARS[i].delay + 100,
            easing: Easing.inOut(Easing.sin),
            useNativeDriver: true,
          }),
          Animated.timing(anim, {
            toValue: 0.1,
            duration: 2000 + i * 200,
            easing: Easing.inOut(Easing.sin),
            useNativeDriver: true,
          }),
        ])
      )
    );

    const all = [...drifts, ...twinkles];
    Animated.stagger(100, all).start();
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
            width: star.size * 2,
            height: star.size * 2,
            borderRadius: star.size,
            backgroundColor: C.isDark ? "rgba(255,255,255,0.8)" : "rgba(124,58,237,0.25)",
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
  const glowAnim = useRef(new Animated.Value(0.2)).current;
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const slideAnim = useRef(new Animated.Value(20)).current;
  const arrowPulse = useRef(new Animated.Value(1)).current;

  useEffect(() => {
    const pulse = Animated.loop(
      Animated.sequence([
        Animated.timing(pulseAnim, {
          toValue: 1.2,
          duration: 2000,
          delay: index * 300,
          easing: Easing.inOut(Easing.sin),
          useNativeDriver: true,
        }),
        Animated.timing(pulseAnim, {
          toValue: 1,
          duration: 2000,
          easing: Easing.inOut(Easing.sin),
          useNativeDriver: true,
        }),
      ])
    );
    const glow = Animated.loop(
      Animated.sequence([
        Animated.timing(glowAnim, {
          toValue: cat.primary ? 0.5 : 0.35,
          duration: 2400,
          delay: index * 200,
          easing: Easing.inOut(Easing.sin),
          useNativeDriver: true,
        }),
        Animated.timing(glowAnim, {
          toValue: cat.primary ? 0.25 : 0.12,
          duration: 2400,
          easing: Easing.inOut(Easing.sin),
          useNativeDriver: true,
        }),
      ])
    );
    const arrow = Animated.loop(
      Animated.sequence([
        Animated.timing(arrowPulse, {
          toValue: 1.12,
          duration: 1400,
          delay: index * 150,
          easing: Easing.inOut(Easing.sin),
          useNativeDriver: true,
        }),
        Animated.timing(arrowPulse, {
          toValue: 1,
          duration: 1400,
          easing: Easing.inOut(Easing.sin),
          useNativeDriver: true,
        }),
      ])
    );
    const entrance = Animated.parallel([
      Animated.timing(fadeAnim, { toValue: 1, duration: 550, delay: 100 + index * 100, useNativeDriver: true }),
      Animated.timing(slideAnim, { toValue: 0, duration: 550, delay: 100 + index * 100, easing: Easing.out(Easing.cubic), useNativeDriver: true }),
    ]);
    pulse.start();
    glow.start();
    arrow.start();
    entrance.start();
    return () => { pulse.stop(); glow.stop(); arrow.stop(); };
  }, []);

  const titles: Record<string, string> = {
    relationship: t.relationship,
    career: t.career,
    health: t.health,
    finance: t.finance,
  };

  const title = titles[cat.key] || cat.key;
  const sub = cat.subtitle;
  const [c1, c2] = cat.gradient;
  const isDark = C.isDark;
  const isPrimary = !!cat.primary;

  const cardBg = isDark
    ? isPrimary ? "rgba(45,8,28,0.75)" : "rgba(12,20,38,0.7)"
    : isPrimary ? "rgba(255,230,242,0.95)" : "rgba(255,255,255,0.92)";

  function handlePressIn() {
    Animated.parallel([
      Animated.spring(scaleAnim, { toValue: 0.96, useNativeDriver: true, speed: 50, bounciness: 4 }),
      Animated.timing(glowAnim, { toValue: 0.8, duration: 120, useNativeDriver: true }),
    ]).start();
  }
  function handlePressOut() {
    Animated.parallel([
      Animated.spring(scaleAnim, { toValue: 1, useNativeDriver: true, speed: 20, bounciness: 8 }),
      Animated.timing(glowAnim, { toValue: isPrimary ? 0.3 : 0.15, duration: 500, useNativeDriver: true }),
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
            shadowOpacity: isDark ? (isPrimary ? 0.5 : 0.3) : (isPrimary ? 0.3 : 0.15),
            shadowRadius: isPrimary ? 28 : 18,
            shadowOffset: { width: 0, height: isPrimary ? 8 : 5 },
            elevation: isPrimary ? 12 : 7,
          },
        ]}>
          {Platform.OS !== "web" ? (
            <BlurView
              intensity={isDark ? 40 : 50}
              tint={isDark ? "dark" : "light"}
              style={StyleSheet.absoluteFill}
            />
          ) : null}
          <View style={[StyleSheet.absoluteFill, {
            backgroundColor: cardBg,
            borderRadius: isPrimary ? 24 : 20,
          }]} />

          <Animated.View style={[
            StyleSheet.absoluteFill,
            { overflow: "hidden", borderRadius: isPrimary ? 24 : 20, opacity: glowAnim },
          ]}>
            <LinearGradient
              colors={isDark
                ? [cat.glowOuter[0], cat.glowOuter[1], "transparent"]
                : [`${cat.glowColor}12`, `${cat.glowColor}06`, "transparent"]}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 1 }}
              style={StyleSheet.absoluteFill}
            />
          </Animated.View>

          <View style={[StyleSheet.absoluteFill, {
            borderRadius: isPrimary ? 24 : 20,
            borderWidth: isDark ? 1 : 0.5,
            borderColor: isDark
              ? `${cat.glowColor}${isPrimary ? "40" : "22"}`
              : `${cat.glowColor}${isPrimary ? "20" : "0A"}`,
          }]} />

          {isDark && (
            <LinearGradient
              colors={["rgba(255,255,255,0.04)", "transparent"]}
              start={{ x: 0, y: 0 }}
              end={{ x: 0, y: 1 }}
              style={[StyleSheet.absoluteFill, { borderRadius: isPrimary ? 24 : 20, height: "50%" }]}
            />
          )}

          {isPrimary && (
            <View style={s.mostUsedWrap}>
              <LinearGradient
                colors={isDark ? ["#ff4d8d", "#c026d3"] : ["#e91e63", "#9c27b0"]}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 0 }}
                style={s.mostUsedBadge}
              >
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
                  backgroundColor: `${cat.glowColor}${isPrimary ? "25" : "15"}`,
                  transform: [{ scale: pulseAnim }],
                },
              ]} />
              <LinearGradient
                colors={[c1, c2]}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 1 }}
                style={[s.iconWrap, isPrimary && s.iconWrapPrimary]}
              >
                <Text style={[s.emoji, isPrimary && { fontSize: 28 }]}>{cat.emoji}</Text>
              </LinearGradient>
            </View>

            <View style={s.cardText}>
              <View style={{ flexDirection: "row", alignItems: "center", gap: 8 }}>
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
                      backgroundColor: isDark ? `${cat.glowColor}15` : `${cat.glowColor}12`,
                      borderColor: isDark ? `${cat.glowColor}30` : `${cat.glowColor}25`,
                    },
                  ]}>
                    <Text style={[s.badgeLabel, { color: isDark ? cat.glowColor : cat.glowColor }]}>
                      {cat.badgeIcon} {cat.badge}
                    </Text>
                  </View>
                )}
              </View>
              <Text
                style={[s.cardSub, {
                  color: isDark ? "rgba(203,213,225,0.8)" : "#64748B",
                  fontFamily: "Nunito_500Medium",
                }]}
                numberOfLines={1}
              >
                {sub}
              </Text>
            </View>

            <Animated.View style={[s.arrowBtn, {
              shadowColor: cat.glowColor,
              shadowOpacity: isDark ? 0.6 : 0.3,
              shadowRadius: 14,
              transform: [{ scale: arrowPulse }],
            }]}>
              <LinearGradient
                colors={[c1, c2]}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 1 }}
                style={[s.arrowGrad, isPrimary && s.arrowGradPrimary]}
              >
                <Feather name="chevron-right" size={isPrimary ? 20 : 16} color="#fff" />
              </LinearGradient>
            </Animated.View>
          </View>

          <LinearGradient
            colors={[c1, c2]}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 0 }}
            style={[s.bottomBar, isPrimary && s.bottomBarPrimary]}
          />
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
  const headerSlide = useRef(new Animated.Value(-16)).current;
  useEffect(() => {
    Animated.parallel([
      Animated.timing(headerFade, { toValue: 1, duration: 700, useNativeDriver: true }),
      Animated.timing(headerSlide, { toValue: 0, duration: 700, easing: Easing.out(Easing.cubic), useNativeDriver: true }),
    ]).start();
  }, []);

  return (
    <CosmicBg>
      <StarField />

      <ScrollView
        style={s.root}
        contentContainerStyle={[s.content, { paddingTop: topPad + 18, paddingBottom: botPad + 120 }]}
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

          <Text style={[s.heading, { color: isDark ? "#fff" : "#0F172A", fontFamily: "Nunito_700Bold" }]}>
            {t.lifeMapTitle ?? "Life Map"}
          </Text>
          <Text style={[s.subtitle, {
            color: isDark ? "rgba(203,213,225,0.55)" : "#64748B",
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
            borderColor: isDark ? `${ac}18` : `${ac}0A`,
            borderWidth: isDark ? 1 : 0,
            shadowColor: isDark ? ac : "rgba(80,60,120,0.15)",
            shadowOpacity: isDark ? 0.06 : 0.18,
            shadowRadius: isDark ? 8 : 16,
            shadowOffset: { width: 0, height: isDark ? 2 : 5 },
            elevation: isDark ? 2 : 6,
          },
        ]}>
          {Platform.OS !== "web" ? (
            <BlurView
              intensity={isDark ? 30 : 45}
              tint={isDark ? "dark" : "light"}
              style={StyleSheet.absoluteFill}
            />
          ) : null}
          <View style={[StyleSheet.absoluteFill, {
            backgroundColor: isDark ? "rgba(12,20,38,0.55)" : "rgba(255,255,255,0.88)",
            borderRadius: 20,
          }]} />

          <View style={s.footerRow}>
            <View style={[s.footerIcon, { backgroundColor: isDark ? `${ac}12` : `${ac}0A` }]}>
              <Feather name="compass" size={18} color={ac} />
            </View>
            <View style={{ flex: 1 }}>
              <Text style={[s.footerTitle, { color: isDark ? "rgba(255,255,255,0.65)" : "#475569", fontFamily: "Nunito_600SemiBold" }]}>
                {t.lifeMapComing ?? "More dimensions coming"}
              </Text>
              <Text style={[s.footerSub, { color: isDark ? "rgba(255,255,255,0.35)" : "#94A3B8", fontFamily: "Nunito_400Regular" }]}>
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
  content: { paddingHorizontal: 20, gap: 16 },

  headerWrap: { gap: 5, marginBottom: 8 },
  headerBadge: { alignSelf: "flex-start", marginBottom: 10 },
  headerBadgeGrad: {
    flexDirection: "row",
    alignItems: "center",
    gap: 5,
    paddingHorizontal: 12,
    paddingVertical: 5,
    borderRadius: 20,
  },
  headerBadgeText: {
    color: "#fff",
    fontSize: 9,
    fontFamily: "Nunito_800ExtraBold",
    letterSpacing: 1.8,
  },

  heading: { fontSize: 30, letterSpacing: -0.5 },
  subtitle: { fontSize: 13.5, letterSpacing: 0.2 },

  grid: { gap: 16 },

  card: {
    borderRadius: 20,
    overflow: "hidden",
  },
  cardPrimary: {
    borderRadius: 24,
  },

  mostUsedWrap: {
    position: "absolute",
    top: 0,
    right: 0,
    zIndex: 10,
  },
  mostUsedBadge: {
    paddingHorizontal: 11,
    paddingVertical: 5,
    borderBottomLeftRadius: 14,
    borderTopRightRadius: 22,
  },
  mostUsedText: {
    color: "#fff",
    fontSize: 8,
    fontFamily: "Nunito_800ExtraBold",
    letterSpacing: 1.2,
  },

  cardRow: {
    flexDirection: "row",
    alignItems: "center",
    padding: 18,
    paddingVertical: 20,
    gap: 16,
  },
  cardRowPrimary: {
    paddingVertical: 24,
    padding: 20,
  },

  iconOuter: {
    width: 54,
    height: 54,
    alignItems: "center",
    justifyContent: "center",
  },
  iconOuterPrimary: {
    width: 64,
    height: 64,
  },
  iconGlow: {
    ...StyleSheet.absoluteFillObject,
    borderRadius: 27,
  },
  iconGlowPrimary: {
    borderRadius: 32,
  },
  iconWrap: {
    width: 50,
    height: 50,
    borderRadius: 16,
    alignItems: "center",
    justifyContent: "center",
  },
  iconWrapPrimary: {
    width: 58,
    height: 58,
    borderRadius: 19,
  },
  emoji: { fontSize: 23 },
  cardText: { flex: 1, gap: 5 },
  cardTitle: { fontSize: 17, letterSpacing: -0.2 },
  cardTitlePrimary: { fontSize: 19.5 },
  cardSub: { fontSize: 12.5, letterSpacing: 0.15 },

  badge: {
    paddingHorizontal: 8,
    paddingVertical: 2.5,
    borderRadius: 10,
    borderWidth: 1,
  },
  badgeLabel: {
    fontSize: 7.5,
    fontFamily: "Nunito_700Bold",
    letterSpacing: 0.5,
  },

  arrowBtn: {
    shadowOffset: { width: 0, height: 2 },
    elevation: 6,
  },
  arrowGrad: {
    width: 38,
    height: 38,
    borderRadius: 19,
    alignItems: "center",
    justifyContent: "center",
    borderWidth: 1,
    borderColor: "rgba(255,255,255,0.15)",
  },
  arrowGradPrimary: {
    width: 44,
    height: 44,
    borderRadius: 22,
  },
  bottomBar: {
    height: 2.5,
    marginHorizontal: 20,
    marginBottom: 4,
    borderRadius: 2,
    opacity: 0.55,
  },
  bottomBarPrimary: {
    height: 3,
    opacity: 0.75,
  },

  footerCard: {
    borderRadius: 20,
    overflow: "hidden",
    padding: 16,
    marginTop: 4,
  },
  footerRow: { flexDirection: "row", alignItems: "center", gap: 14 },
  footerIcon: {
    width: 42,
    height: 42,
    borderRadius: 14,
    alignItems: "center",
    justifyContent: "center",
  },
  footerTitle: { fontSize: 13, letterSpacing: 0.1 },
  footerSub: { fontSize: 11, marginTop: 2.5 },
});
