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
  glowColor: string;
  badge: string;
  subtitle: string;
  primary?: boolean;
  route?: string;
}

const CATEGORIES: Category[] = [
  {
    key: "relationship",
    icon: "heart",
    emoji: "💕",
    gradient: ["#ff4d8d", "#ff1a6c"],
    glowColor: "#ff4d8d",
    badge: "❤️ LOVE",
    subtitle: "Check love & marriage future",
    primary: true,
  },
  {
    key: "career",
    icon: "briefcase",
    emoji: "🚀",
    gradient: ["#ff7b00", "#ff9500"],
    glowColor: "#ff9500",
    badge: "🚀 FAST GROWTH",
    subtitle: "Will you succeed or struggle?",
  },
  {
    key: "health",
    icon: "activity",
    emoji: "🧘",
    gradient: ["#00e676", "#10b981"],
    glowColor: "#00e676",
    badge: "⚠️ HEALTH CHECK",
    subtitle: "Is your health at risk?",
  },
  {
    key: "finance",
    icon: "dollar-sign",
    emoji: "💰",
    gradient: ["#ffc107", "#ff9800"],
    glowColor: "#ffc107",
    badge: "💰 MONEY FLOW",
    subtitle: "Will you gain or lose money?",
  },
];

const STAR_COUNT = 14;
const STARS = Array.from({ length: STAR_COUNT }, (_, i) => ({
  x: (7 + i * 31 + (i % 3) * 17) % 95,
  y: (5 + i * 19 + (i % 4) * 11) % 90,
  size: 1.2 + (i % 3) * 0.6,
  delay: i * 220,
}));

function StarField() {
  const driftAnims = useRef(STARS.map(() => new Animated.Value(0))).current;
  const opacityAnims = useRef(STARS.map(() => new Animated.Value(0.2))).current;

  useEffect(() => {
    const drifts = driftAnims.map((anim, i) =>
      Animated.loop(
        Animated.sequence([
          Animated.timing(anim, {
            toValue: 8 + (i % 3) * 4,
            duration: 4000 + i * 400,
            delay: STARS[i].delay,
            easing: Easing.inOut(Easing.sin),
            useNativeDriver: true,
          }),
          Animated.timing(anim, {
            toValue: 0,
            duration: 4000 + i * 400,
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
            toValue: 0.8 + (i % 3) * 0.15,
            duration: 1600 + i * 180,
            delay: STARS[i].delay + 100,
            easing: Easing.inOut(Easing.sin),
            useNativeDriver: true,
          }),
          Animated.timing(anim, {
            toValue: 0.15,
            duration: 1600 + i * 180,
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
            width: star.size * 2,
            height: star.size * 2,
            borderRadius: star.size,
            backgroundColor: "#fff",
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

  useEffect(() => {
    const pulse = Animated.loop(
      Animated.sequence([
        Animated.timing(pulseAnim, {
          toValue: 1.18,
          duration: 1800,
          delay: index * 250,
          easing: Easing.inOut(Easing.sin),
          useNativeDriver: true,
        }),
        Animated.timing(pulseAnim, {
          toValue: 1,
          duration: 1800,
          easing: Easing.inOut(Easing.sin),
          useNativeDriver: true,
        }),
      ])
    );
    const glow = Animated.loop(
      Animated.sequence([
        Animated.timing(glowAnim, {
          toValue: cat.primary ? 0.55 : 0.35,
          duration: 2200,
          delay: index * 200,
          easing: Easing.inOut(Easing.sin),
          useNativeDriver: true,
        }),
        Animated.timing(glowAnim, {
          toValue: cat.primary ? 0.3 : 0.15,
          duration: 2200,
          easing: Easing.inOut(Easing.sin),
          useNativeDriver: true,
        }),
      ])
    );
    const fade = Animated.timing(fadeAnim, {
      toValue: 1,
      duration: 500,
      delay: 150 + index * 120,
      useNativeDriver: true,
    });
    pulse.start();
    glow.start();
    fade.start();
    return () => { pulse.stop(); glow.stop(); };
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
    ? isPrimary ? "rgba(50,10,30,0.7)" : "rgba(15,23,42,0.65)"
    : isPrimary ? "rgba(255,230,240,0.85)" : "rgba(255,255,255,0.78)";
  const borderCol = isDark
    ? `${cat.glowColor}${isPrimary ? "55" : "35"}`
    : `${cat.glowColor}${isPrimary ? "40" : "25"}`;

  function handlePressIn() {
    Animated.parallel([
      Animated.spring(scaleAnim, { toValue: 0.955, useNativeDriver: true, speed: 50, bounciness: 4 }),
      Animated.timing(glowAnim, { toValue: 0.7, duration: 150, useNativeDriver: true }),
    ]).start();
  }
  function handlePressOut() {
    Animated.parallel([
      Animated.spring(scaleAnim, { toValue: 1, useNativeDriver: true, speed: 22, bounciness: 6 }),
      Animated.timing(glowAnim, { toValue: isPrimary ? 0.35 : 0.2, duration: 400, useNativeDriver: true }),
    ]).start();
  }

  return (
    <Animated.View style={{ transform: [{ scale: scaleAnim }], opacity: fadeAnim }}>
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
            borderColor: borderCol,
            shadowColor: cat.glowColor,
            shadowOpacity: isDark ? (isPrimary ? 0.45 : 0.25) : (isPrimary ? 0.2 : 0.1),
          },
        ]}>
          {Platform.OS !== "web" ? (
            <BlurView
              intensity={isDark ? 35 : 45}
              tint={isDark ? "dark" : "light"}
              style={StyleSheet.absoluteFill}
            />
          ) : null}
          <View style={[StyleSheet.absoluteFill, { backgroundColor: cardBg, borderRadius: isPrimary ? 22 : 18 }]} />

          <Animated.View style={[
            StyleSheet.absoluteFill,
            { overflow: "hidden", borderRadius: isPrimary ? 22 : 18, opacity: glowAnim },
          ]}>
            <LinearGradient
              colors={isDark
                ? [`${cat.glowColor}20`, `${cat.glowColor}08`, "transparent"]
                : [`${cat.glowColor}15`, `${cat.glowColor}05`, "transparent"]}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 1 }}
              style={StyleSheet.absoluteFill}
            />
          </Animated.View>

          {isPrimary && (
            <View style={s.mostUsedWrap}>
              <LinearGradient
                colors={isDark ? ["#ff4d8d", "#ff1a6c"] : ["#e91e63", "#c2185b"]}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 0 }}
                style={s.mostUsedBadge}
              >
                <Text style={s.mostUsedText}>🔥 MOST USED</Text>
              </LinearGradient>
            </View>
          )}

          <View style={[s.cardRow, isPrimary && s.cardRowPrimary]}>
            <View style={[s.iconOuter, isPrimary && s.iconOuterPrimary]}>
              <Animated.View style={[
                s.iconGlow,
                isPrimary && s.iconGlowPrimary,
                {
                  backgroundColor: `${cat.glowColor}${isPrimary ? "30" : "18"}`,
                  transform: [{ scale: pulseAnim }],
                },
              ]} />
              <LinearGradient
                colors={[c1, c2]}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 1 }}
                style={[s.iconWrap, isPrimary && s.iconWrapPrimary]}
              >
                <Text style={[s.emoji, isPrimary && { fontSize: 26 }]}>{cat.emoji}</Text>
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
                <View style={[
                  s.badge,
                  { backgroundColor: isDark ? `${cat.glowColor}18` : `${cat.glowColor}12`, borderColor: `${cat.glowColor}30` },
                ]}>
                  <Text style={[s.badgeLabel, { color: cat.glowColor }]}>{cat.badge}</Text>
                </View>
              </View>
              <Text
                style={[s.cardSub, { color: isDark ? "rgba(203,213,225,0.75)" : "#64748B", fontFamily: "Nunito_500Medium" }]}
                numberOfLines={1}
              >
                {sub}
              </Text>
            </View>

            <View style={[s.arrowBtn, { shadowColor: cat.glowColor }]}>
              <LinearGradient
                colors={isDark ? [c1, c2] : [`${c1}50`, `${c2}35`]}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 1 }}
                style={[s.arrowGrad, isPrimary && s.arrowGradPrimary]}
              >
                <Feather name="chevron-right" size={isPrimary ? 18 : 15} color={isDark ? "#fff" : c2} />
              </LinearGradient>
            </View>
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
  const headerSlide = useRef(new Animated.Value(-12)).current;
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
        contentContainerStyle={[s.content, { paddingTop: topPad + 16, paddingBottom: botPad + 110 }]}
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
          <Text style={[s.subtitle, { color: isDark ? "rgba(203,213,225,0.6)" : "#64748B", fontFamily: "Nunito_400Regular" }]}>
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
            borderColor: isDark ? `${ac}20` : `${ac}15`,
            shadowColor: ac,
          },
        ]}>
          {Platform.OS !== "web" ? (
            <BlurView
              intensity={isDark ? 25 : 35}
              tint={isDark ? "dark" : "light"}
              style={StyleSheet.absoluteFill}
            />
          ) : null}
          <View style={[StyleSheet.absoluteFill, {
            backgroundColor: isDark ? "rgba(15,23,42,0.5)" : "rgba(255,255,255,0.6)",
            borderRadius: 16,
          }]} />

          <View style={s.footerRow}>
            <View style={[s.footerIcon, { backgroundColor: isDark ? `${ac}15` : `${ac}10` }]}>
              <Feather name="compass" size={18} color={ac} />
            </View>
            <View style={{ flex: 1 }}>
              <Text style={[s.footerTitle, { color: isDark ? "rgba(255,255,255,0.7)" : "#475569", fontFamily: "Nunito_600SemiBold" }]}>
                {t.lifeMapComing ?? "More dimensions coming"}
              </Text>
              <Text style={[s.footerSub, { color: isDark ? "rgba(255,255,255,0.4)" : "#94A3B8", fontFamily: "Nunito_400Regular" }]}>
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
  content: { paddingHorizontal: 18, gap: 14 },

  headerWrap: { gap: 4, marginBottom: 6 },
  headerBadge: { alignSelf: "flex-start", marginBottom: 8 },
  headerBadgeGrad: {
    flexDirection: "row",
    alignItems: "center",
    gap: 5,
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 20,
  },
  headerBadgeText: {
    color: "#fff",
    fontSize: 9,
    fontFamily: "Nunito_700Bold",
    letterSpacing: 1.5,
  },

  heading: { fontSize: 28, letterSpacing: -0.5 },
  subtitle: { fontSize: 13.5, letterSpacing: 0.1 },

  grid: { gap: 12 },

  card: {
    borderRadius: 18,
    borderWidth: 1,
    overflow: "hidden",
    shadowOffset: { width: 0, height: 4 },
    shadowRadius: 14,
    elevation: 5,
  },
  cardPrimary: {
    borderRadius: 22,
    borderWidth: 1.5,
    shadowOffset: { width: 0, height: 6 },
    shadowRadius: 22,
    elevation: 8,
  },

  mostUsedWrap: {
    position: "absolute",
    top: 0,
    right: 0,
    zIndex: 10,
  },
  mostUsedBadge: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderBottomLeftRadius: 12,
    borderTopRightRadius: 20,
  },
  mostUsedText: {
    color: "#fff",
    fontSize: 8.5,
    fontFamily: "Nunito_800ExtraBold",
    letterSpacing: 1,
  },

  cardRow: {
    flexDirection: "row",
    alignItems: "center",
    padding: 16,
    paddingVertical: 18,
    gap: 14,
  },
  cardRowPrimary: {
    paddingVertical: 22,
    padding: 18,
  },

  iconOuter: {
    width: 52,
    height: 52,
    alignItems: "center",
    justifyContent: "center",
  },
  iconOuterPrimary: {
    width: 60,
    height: 60,
  },
  iconGlow: {
    ...StyleSheet.absoluteFillObject,
    borderRadius: 26,
  },
  iconGlowPrimary: {
    borderRadius: 30,
  },
  iconWrap: {
    width: 48,
    height: 48,
    borderRadius: 15,
    alignItems: "center",
    justifyContent: "center",
  },
  iconWrapPrimary: {
    width: 54,
    height: 54,
    borderRadius: 17,
  },
  emoji: { fontSize: 22 },
  cardText: { flex: 1, gap: 4 },
  cardTitle: { fontSize: 16.5, letterSpacing: -0.2 },
  cardTitlePrimary: { fontSize: 18.5 },
  cardSub: { fontSize: 12.5, letterSpacing: 0.1 },

  badge: {
    paddingHorizontal: 7,
    paddingVertical: 2,
    borderRadius: 8,
    borderWidth: 1,
  },
  badgeLabel: {
    fontSize: 7.5,
    fontFamily: "Nunito_700Bold",
    letterSpacing: 0.8,
  },

  arrowBtn: {
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.5,
    shadowRadius: 10,
    elevation: 5,
  },
  arrowGrad: {
    width: 34,
    height: 34,
    borderRadius: 17,
    alignItems: "center",
    justifyContent: "center",
    borderWidth: 1,
    borderColor: "rgba(255,255,255,0.12)",
  },
  arrowGradPrimary: {
    width: 40,
    height: 40,
    borderRadius: 20,
  },
  bottomBar: {
    height: 2.5,
    marginHorizontal: 18,
    marginBottom: 3,
    borderRadius: 2,
    opacity: 0.6,
  },
  bottomBarPrimary: {
    height: 3,
    opacity: 0.8,
  },

  footerCard: {
    borderRadius: 16,
    borderWidth: 1,
    overflow: "hidden",
    padding: 14,
    marginTop: 4,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 8,
    elevation: 2,
  },
  footerRow: { flexDirection: "row", alignItems: "center", gap: 12 },
  footerIcon: {
    width: 40,
    height: 40,
    borderRadius: 12,
    alignItems: "center",
    justifyContent: "center",
  },
  footerTitle: { fontSize: 13, letterSpacing: 0.1 },
  footerSub: { fontSize: 11, marginTop: 2 },
});
