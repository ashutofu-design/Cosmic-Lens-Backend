import { Feather } from "@expo/vector-icons";
import { LinearGradient } from "expo-linear-gradient";
import { useLocalSearchParams } from "expo-router";
import React, { useEffect, useMemo, useRef, useState } from "react";
import {
  Animated,
  Platform,
  ScrollView,
  StatusBar,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { CosmicBg } from "@/components/CosmicBg";
import { FadeInView } from "@/components/motion/FadeInView";
import { LifeMapCategoryCard } from "@/components/lifeMap/LifeMapCategoryCard";
import { LifeMapModeTabs, type LifeMapMode } from "@/components/lifeMap/LifeMapModeTabs";
import { LifeMapStarField } from "@/components/lifeMap/LifeMapStarField";
import { useC } from "@/context/ThemeContext";
import { useT } from "@/hooks/useT";
import { buildExploreCategories, LIFE_MAP_CATEGORIES } from "@/lib/lifeMapData";

export default function LifeMapScreen() {
  const C = useC();
  const t = useT();
  const params = useLocalSearchParams<{ mode?: string }>();
  const insets = useSafeAreaInsets();
  const androidSB = StatusBar.currentHeight ?? 24;
  const topPad = Platform.OS === "android" ? Math.max(insets.top, androidSB) : insets.top;
  const botPad = insets.bottom;
  const isDark = C.isDark;
  const ac = isDark ? "#f59e0b" : "#7C3AED";

  const [mode, setMode] = useState<LifeMapMode>(
    params.mode === "explore" ? "explore" : "lifemap",
  );

  useEffect(() => {
    if (params.mode === "explore") setMode("explore");
    else if (params.mode === "lifemap") setMode("lifemap");
  }, [params.mode]);

  const exploreCategories = useMemo(() => buildExploreCategories(t), [t]);
  const categories = mode === "lifemap" ? LIFE_MAP_CATEGORIES : exploreCategories;

  const headerFade = useRef(new Animated.Value(0)).current;
  const headerSlide = useRef(new Animated.Value(-20)).current;
  useEffect(() => {
    Animated.parallel([
      Animated.timing(headerFade, { toValue: 1, duration: 800, useNativeDriver: true }),
      Animated.spring(headerSlide, { toValue: 0, useNativeDriver: true, speed: 12, bounciness: 5 }),
    ]).start();
  }, []);

  const isExplore = mode === "explore";

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
      <LifeMapStarField />

      <ScrollView
        style={s.root}
        contentContainerStyle={[s.content, { paddingTop: topPad + 20, paddingBottom: botPad + 130 }]}
        showsVerticalScrollIndicator={false}
      >
        <Animated.View style={[s.headerWrap, { opacity: headerFade, transform: [{ translateY: headerSlide }] }]}>
          <View style={s.headerBadge}>
            <LinearGradient
              colors={isExplore
                ? (isDark ? ["#7c3aed", "#6d28d9"] : ["#7C3AED", "#6D5DF6"])
                : (isDark ? ["#f59e0b", "#d97706"] : ["#7C3AED", "#6D5DF6"])}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 0 }}
              style={s.headerBadgeGrad}
            >
              <Feather name={isExplore ? "compass" : "map"} size={10} color="#fff" />
              <Text style={s.headerBadgeText}>{isExplore ? "EXPLORE" : "LIFE MAP"}</Text>
            </LinearGradient>
          </View>

          <View style={s.headingRow}>
            <Text style={[s.heading, { color: isDark ? "#fff" : "#0F172A", fontFamily: "Nunito_700Bold" }]}>
              {isExplore ? t.moreExplore : t.lifeMapTitle}
            </Text>
            <Text style={s.headingEmoji}>  ✨</Text>
          </View>
          <Text style={[s.subtitle, {
            color: isDark ? "rgba(203,213,225,0.5)" : "#64748B",
            fontFamily: "Nunito_400Regular",
          }]}>
            {isExplore ? t.moreSubtitle : t.lifeMapSubtitle}
          </Text>
        </Animated.View>

        <FadeInView delay={80}>
          <LifeMapModeTabs
            active={mode}
            lifeMapLabel={t.lifeMapTitle}
            exploreLabel={t.moreExplore}
            onSelect={setMode}
          />
        </FadeInView>

        <FadeInView key={mode} delay={120} resetKey={mode}>
        <View style={s.grid}>
          {categories.map((cat, i) => (
            <LifeMapCategoryCard key={`${mode}-${cat.key}`} cat={cat} index={i} />
          ))}
        </View>
        </FadeInView>

        {!isExplore && (
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
        )}
      </ScrollView>
    </CosmicBg>
  );
}

const s = StyleSheet.create({
  root: { flex: 1 },
  content: { paddingHorizontal: 20, gap: 20 },
  headerWrap: { gap: 6, marginBottom: 4 },
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
  headingRow: { flexDirection: "row", alignItems: "baseline", flexWrap: "wrap" },
  heading: { fontSize: 32, letterSpacing: -0.5 },
  headingEmoji: { fontSize: 22 },
  subtitle: { fontSize: 13.5, letterSpacing: 0.2, marginTop: 2 },
  grid: { gap: 20 },
  footerCard: {
    borderRadius: 22,
    overflow: "hidden",
    padding: 18,
  },
  footerRow: { flexDirection: "row", alignItems: "center", gap: 14 },
  footerIcon: {
    width: 44,
    height: 44,
    borderRadius: 14,
    alignItems: "center",
    justifyContent: "center",
  },
  footerTitle: { fontSize: 14 },
  footerSub: { fontSize: 12, marginTop: 3 },
});
