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
import Svg, { Circle } from "react-native-svg";
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
  route?: string;
}

const CATEGORIES: Category[] = [
  { key: "relationship", icon: "heart",       emoji: "💕", gradient: ["#ff6b9d", "#c44569"], glowColor: "#ff6b9d" },
  { key: "career",       icon: "briefcase",   emoji: "🚀", gradient: ["#f59e0b", "#d97706"], glowColor: "#f59e0b" },
  { key: "health",       icon: "activity",    emoji: "🧘", gradient: ["#10b981", "#059669"], glowColor: "#10b981" },
  { key: "finance",      icon: "dollar-sign", emoji: "💰", gradient: ["#60a5fa", "#3b82f6"], glowColor: "#60a5fa" },
];

const STAR_POSITIONS = [
  { x: 12, y: 8, size: 2, opacity: 0.5, delay: 0 },
  { x: 85, y: 15, size: 1.5, opacity: 0.4, delay: 400 },
  { x: 45, y: 5, size: 1.8, opacity: 0.35, delay: 800 },
  { x: 70, y: 22, size: 2.2, opacity: 0.45, delay: 200 },
  { x: 25, y: 20, size: 1.2, opacity: 0.3, delay: 600 },
  { x: 92, y: 6, size: 1.6, opacity: 0.38, delay: 1000 },
  { x: 55, y: 18, size: 1.4, opacity: 0.32, delay: 300 },
  { x: 8, y: 25, size: 1.8, opacity: 0.42, delay: 700 },
];

function StarField() {
  const anims = useRef(STAR_POSITIONS.map(() => new Animated.Value(0.3))).current;

  useEffect(() => {
    const animations = anims.map((anim, i) =>
      Animated.loop(
        Animated.sequence([
          Animated.timing(anim, {
            toValue: 1,
            duration: 1800 + i * 200,
            delay: STAR_POSITIONS[i].delay,
            easing: Easing.inOut(Easing.sin),
            useNativeDriver: true,
          }),
          Animated.timing(anim, {
            toValue: 0.2,
            duration: 1800 + i * 200,
            easing: Easing.inOut(Easing.sin),
            useNativeDriver: true,
          }),
        ])
      )
    );
    Animated.stagger(150, animations).start();
    return () => animations.forEach(a => a.stop());
  }, []);

  return (
    <View style={StyleSheet.absoluteFill} pointerEvents="none">
      {STAR_POSITIONS.map((star, i) => (
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
            opacity: anims[i],
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

  useEffect(() => {
    const loop = Animated.loop(
      Animated.sequence([
        Animated.timing(pulseAnim, {
          toValue: 1.15,
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
    loop.start();
    return () => loop.stop();
  }, []);

  const titles: Record<string, string> = {
    relationship: t.relationship,
    career: t.career,
    health: t.health,
    finance: t.finance,
  };
  const subtitles: Record<string, string> = {
    relationship: t.lifeMapRelSub ?? "Love, compatibility & bonds",
    career: t.lifeMapCarSub ?? "Growth, success & purpose",
    health: t.lifeMapHealthSub ?? "Body, mind & vitality",
    finance: t.lifeMapFinSub ?? "Wealth, stability & flow",
  };

  const title = titles[cat.key] || cat.key;
  const sub = subtitles[cat.key];
  const [c1, c2] = cat.gradient;
  const isDark = C.isDark;

  const cardBg = isDark ? "rgba(15,23,42,0.65)" : "rgba(255,255,255,0.75)";
  const borderCol = isDark ? `${cat.glowColor}35` : `${cat.glowColor}25`;

  function handlePressIn() {
    Animated.spring(scaleAnim, { toValue: 0.97, useNativeDriver: true, speed: 40, bounciness: 4 }).start();
  }
  function handlePressOut() {
    Animated.spring(scaleAnim, { toValue: 1, useNativeDriver: true, speed: 20, bounciness: 6 }).start();
  }

  return (
    <Animated.View style={{ transform: [{ scale: scaleAnim }] }}>
      <Pressable
        onPressIn={handlePressIn}
        onPressOut={handlePressOut}
        onPress={() => {
          Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
          if (cat.route) router.push(cat.route as any);
        }}
      >
        <View style={[
          s.card,
          {
            borderColor: borderCol,
            shadowColor: cat.glowColor,
            shadowOpacity: isDark ? 0.25 : 0.12,
          },
        ]}>
          {Platform.OS !== "web" ? (
            <BlurView
              intensity={isDark ? 30 : 40}
              tint={isDark ? "dark" : "light"}
              style={StyleSheet.absoluteFill}
            />
          ) : null}
          <View style={[StyleSheet.absoluteFill, { backgroundColor: cardBg, borderRadius: 18 }]} />

          <View style={[StyleSheet.absoluteFill, { overflow: "hidden", borderRadius: 18 }]}>
            <LinearGradient
              colors={isDark
                ? [`${cat.glowColor}08`, `${cat.glowColor}03`, "transparent"]
                : [`${cat.glowColor}06`, "transparent"]}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 1 }}
              style={StyleSheet.absoluteFill}
            />
          </View>

          <View style={s.cardRow}>
            <View style={s.iconOuter}>
              <Animated.View style={[
                s.iconGlow,
                {
                  backgroundColor: `${cat.glowColor}15`,
                  transform: [{ scale: pulseAnim }],
                },
              ]} />
              <LinearGradient
                colors={[c1, c2]}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 1 }}
                style={s.iconWrap}
              >
                <Text style={s.emoji}>{cat.emoji}</Text>
              </LinearGradient>
            </View>

            <View style={s.cardText}>
              <Text style={[s.cardTitle, { color: isDark ? "#fff" : "#0F172A", fontFamily: "Nunito_700Bold" }]}>
                {title}
              </Text>
              <Text
                style={[s.cardSub, { color: isDark ? "rgba(203,213,225,0.7)" : "#64748B", fontFamily: "Nunito_400Regular" }]}
                numberOfLines={1}
              >
                {sub}
              </Text>
            </View>

            <View style={[s.arrowBtn, { shadowColor: cat.glowColor }]}>
              <LinearGradient
                colors={isDark ? [`${c1}40`, `${c2}25`] : [`${c1}20`, `${c2}12`]}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 1 }}
                style={s.arrowGrad}
              >
                <Feather name="arrow-right" size={14} color={isDark ? cat.glowColor : c2} />
              </LinearGradient>
            </View>
          </View>

          <LinearGradient
            colors={[c1, c2]}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 0 }}
            style={s.bottomBar}
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
  useEffect(() => {
    Animated.timing(headerFade, {
      toValue: 1,
      duration: 600,
      useNativeDriver: true,
    }).start();
  }, []);

  return (
    <CosmicBg>
      <StarField />

      <ScrollView
        style={s.root}
        contentContainerStyle={[s.content, { paddingTop: topPad + 16, paddingBottom: botPad + 110 }]}
        showsVerticalScrollIndicator={false}
      >
        <Animated.View style={[s.headerWrap, { opacity: headerFade }]}>
          <View style={s.headerBadge}>
            <LinearGradient
              colors={isDark ? ["#f59e0b", "#d97706"] : ["#7C3AED", "#6D5DF6"]}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 0 }}
              style={s.badgeGrad}
            >
              <Feather name="map" size={10} color="#fff" />
              <Text style={s.badgeText}>LIFE MAP</Text>
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

  headerWrap: { gap: 4, marginBottom: 4 },
  headerBadge: { alignSelf: "flex-start", marginBottom: 8 },
  badgeGrad: {
    flexDirection: "row",
    alignItems: "center",
    gap: 5,
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 20,
  },
  badgeText: {
    color: "#fff",
    fontSize: 9,
    fontFamily: "Nunito_700Bold",
    letterSpacing: 1.5,
  },

  heading: { fontSize: 26, letterSpacing: -0.5 },
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
  cardRow: {
    flexDirection: "row",
    alignItems: "center",
    padding: 16,
    paddingVertical: 18,
    gap: 14,
  },
  iconOuter: {
    width: 52,
    height: 52,
    alignItems: "center",
    justifyContent: "center",
  },
  iconGlow: {
    ...StyleSheet.absoluteFillObject,
    borderRadius: 26,
  },
  iconWrap: {
    width: 48,
    height: 48,
    borderRadius: 15,
    alignItems: "center",
    justifyContent: "center",
  },
  emoji: { fontSize: 22 },
  cardText: { flex: 1, gap: 3 },
  cardTitle: { fontSize: 16.5, letterSpacing: -0.2 },
  cardSub: { fontSize: 12.5 },

  arrowBtn: {
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.4,
    shadowRadius: 8,
    elevation: 4,
  },
  arrowGrad: {
    width: 34,
    height: 34,
    borderRadius: 17,
    alignItems: "center",
    justifyContent: "center",
    borderWidth: 1,
    borderColor: "rgba(255,255,255,0.08)",
  },
  bottomBar: {
    height: 2.5,
    marginHorizontal: 18,
    marginBottom: 3,
    borderRadius: 2,
    opacity: 0.5,
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
