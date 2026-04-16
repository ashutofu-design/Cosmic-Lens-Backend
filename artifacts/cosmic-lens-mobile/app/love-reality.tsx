import { Feather } from "@expo/vector-icons";
import { BlurView } from "expo-blur";
import * as Haptics from "expo-haptics";
import { LinearGradient } from "expo-linear-gradient";
import { router, useLocalSearchParams } from "expo-router";
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
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { CosmicBg } from "@/components/CosmicBg";
import { useC } from "@/context/ThemeContext";
import { useT } from "@/hooks/useT";

interface Feature {
  key: string;
  title: string;
  subtitle: string;
  emoji: string;
  iconColor: string;
  gradient: [string, string];
}

const FEATURES: Feature[] = [
  {
    key: "love-compat",
    title: "Love Compatibility",
    subtitle: "How deep is your connection?",
    emoji: "💘",
    iconColor: "#f472b6",
    gradient: ["#ec4899", "#f472b6"],
  },
  {
    key: "breakup",
    title: "Breakup Chances",
    subtitle: "What threatens your bond?",
    emoji: "💔",
    iconColor: "#f87171",
    gradient: ["#ef4444", "#f87171"],
  },
  {
    key: "loyalty",
    title: "Loyalty Check",
    subtitle: "How faithful is the connection?",
    emoji: "🛡️",
    iconColor: "#fb923c",
    gradient: ["#f97316", "#fb923c"],
  },
  {
    key: "will-return",
    title: "Will X Return?",
    subtitle: "Chances of reconnection",
    emoji: "🪃",
    iconColor: "#fbbf24",
    gradient: ["#f59e0b", "#fbbf24"],
  },
  {
    key: "future-outcome",
    title: "Future Outcome",
    subtitle: "Where is this relationship headed?",
    emoji: "🔮",
    iconColor: "#c084fc",
    gradient: ["#a855f7", "#c084fc"],
  },
];

function FeatureCard({
  feature,
  index,
  isDark,
  partnerId,
}: {
  feature: Feature;
  index: number;
  isDark: boolean;
  partnerId?: string | null;
}) {
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const slideAnim = useRef(new Animated.Value(24)).current;
  const scaleAnim = useRef(new Animated.Value(1)).current;
  const glowAnim = useRef(new Animated.Value(0.12)).current;
  const arrowPulse = useRef(new Animated.Value(1)).current;

  useEffect(() => {
    const entrance = Animated.parallel([
      Animated.timing(fadeAnim, { toValue: 1, duration: 500, delay: 250 + index * 90, useNativeDriver: true }),
      Animated.spring(slideAnim, { toValue: 0, delay: 250 + index * 90, useNativeDriver: true, speed: 14, bounciness: 4 }),
    ]);
    const glow = Animated.loop(
      Animated.sequence([
        Animated.timing(glowAnim, { toValue: 0.35, duration: 2500, delay: index * 200, easing: Easing.inOut(Easing.sin), useNativeDriver: true }),
        Animated.timing(glowAnim, { toValue: 0.08, duration: 2500, easing: Easing.inOut(Easing.sin), useNativeDriver: true }),
      ])
    );
    const arrow = Animated.loop(
      Animated.sequence([
        Animated.timing(arrowPulse, { toValue: 1.12, duration: 1300, delay: index * 100, easing: Easing.inOut(Easing.sin), useNativeDriver: true }),
        Animated.timing(arrowPulse, { toValue: 1, duration: 1300, easing: Easing.inOut(Easing.sin), useNativeDriver: true }),
      ])
    );
    entrance.start();
    glow.start();
    arrow.start();
    return () => { glow.stop(); arrow.stop(); };
  }, []);

  const [c1, c2] = feature.gradient;

  function handlePressIn() {
    Animated.parallel([
      Animated.spring(scaleAnim, { toValue: 0.96, useNativeDriver: true, speed: 50, bounciness: 4 }),
      Animated.timing(glowAnim, { toValue: 0.7, duration: 100, useNativeDriver: true }),
    ]).start();
  }
  function handlePressOut() {
    Animated.parallel([
      Animated.spring(scaleAnim, { toValue: 1, useNativeDriver: true, speed: 18, bounciness: 10 }),
      Animated.timing(glowAnim, { toValue: 0.12, duration: 400, useNativeDriver: true }),
    ]).start();
  }

  return (
    <Animated.View style={{ transform: [{ scale: scaleAnim }, { translateY: slideAnim }], opacity: fadeAnim }}>
      <Pressable onPressIn={handlePressIn} onPressOut={handlePressOut} onPress={() => {
        Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
        if (feature.key === "love-compat") {
          const url = partnerId ? `/love-compatibility?partnerId=${partnerId}` : "/love-compatibility";
          router.push(url as any);
        } else if (feature.key === "breakup") {
          const url = partnerId ? `/breakup-chances?partnerId=${partnerId}` : "/breakup-chances";
          router.push(url as any);
        }
      }}>
        <View style={[s.card, {
          shadowColor: feature.iconColor,
          shadowOpacity: isDark ? 0.3 : 0.12,
          shadowRadius: 18,
          shadowOffset: { width: 0, height: 5 },
          elevation: 7,
        }]}>
          {Platform.OS !== "web" ? (
            <BlurView intensity={isDark ? 40 : 55} tint={isDark ? "dark" : "light"} style={StyleSheet.absoluteFill} />
          ) : null}
          <View style={[StyleSheet.absoluteFill, {
            backgroundColor: isDark ? "rgba(14,22,42,0.72)" : "rgba(255,255,255,0.94)",
            borderRadius: 20,
          }]} />

          <Animated.View style={[StyleSheet.absoluteFill, { overflow: "hidden", borderRadius: 20, opacity: glowAnim }]}>
            <LinearGradient
              colors={isDark
                ? [`${feature.iconColor}20`, `${feature.iconColor}08`, "transparent"]
                : [`${feature.iconColor}10`, `${feature.iconColor}04`, "transparent"]}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 1 }}
              style={StyleSheet.absoluteFill}
            />
          </Animated.View>

          <View style={[StyleSheet.absoluteFill, {
            borderRadius: 20,
            borderWidth: isDark ? 1 : 0.5,
            borderColor: isDark ? `${feature.iconColor}28` : `${feature.iconColor}0C`,
          }]} />

          {isDark && (
            <LinearGradient
              colors={["rgba(255,255,255,0.04)", "transparent"]}
              start={{ x: 0, y: 0 }}
              end={{ x: 0, y: 1 }}
              style={[StyleSheet.absoluteFill, { borderRadius: 20, height: "50%" }]}
            />
          )}

          <View style={s.cardRow}>
            <LinearGradient colors={[c1, c2]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={s.iconWrap}>
              <Text style={s.iconEmoji}>{feature.emoji}</Text>
            </LinearGradient>

            <View style={s.textArea}>
              <Text style={[s.cardTitle, { color: isDark ? "#fff" : "#0F172A", fontFamily: "Nunito_700Bold" }]}>
                {feature.title}
              </Text>
              <Text style={[s.cardSub, { color: isDark ? "rgba(203,213,225,0.7)" : "#64748B", fontFamily: "Nunito_500Medium" }]} numberOfLines={1}>
                {feature.subtitle}
              </Text>
            </View>

            <Animated.View style={{
              transform: [{ scale: arrowPulse }],
              shadowColor: feature.iconColor,
              shadowOpacity: isDark ? 0.5 : 0.2,
              shadowRadius: 12,
              shadowOffset: { width: 0, height: 3 },
              elevation: 6,
            }}>
              <LinearGradient colors={[c1, c2]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={s.arrowCircle}>
                <Feather name="chevron-right" size={16} color="#fff" />
              </LinearGradient>
            </Animated.View>
          </View>
        </View>
      </Pressable>
    </Animated.View>
  );
}

export default function LoveRealityScreen() {
  const C = useC();
  const t = useT();
  const params = useLocalSearchParams<{ partnerId?: string }>();
  const partnerId = typeof params.partnerId === "string" ? params.partnerId : null;
  const insets = useSafeAreaInsets();
  const androidSB = StatusBar.currentHeight ?? 24;
  const topPad = Platform.OS === "android" ? Math.max(insets.top, androidSB) : insets.top;
  const botPad = insets.bottom;
  const isDark = C.isDark;

  const headerFade = useRef(new Animated.Value(0)).current;
  const headerSlide = useRef(new Animated.Value(-20)).current;

  useEffect(() => {
    Animated.parallel([
      Animated.timing(headerFade, { toValue: 1, duration: 700, useNativeDriver: true }),
      Animated.spring(headerSlide, { toValue: 0, useNativeDriver: true, speed: 12, bounciness: 5 }),
    ]).start();
  }, []);

  return (
    <CosmicBg>
      <LinearGradient
        colors={isDark
          ? ["rgba(0,0,0,0.35)", "transparent", "rgba(0,0,0,0.2)"]
          : ["rgba(255,255,255,0.15)", "transparent", "rgba(255,255,255,0.08)"]}
        locations={[0, 0.4, 1]}
        style={StyleSheet.absoluteFill}
        pointerEvents="none"
      />

      <View style={[s.topBar, { paddingTop: topPad + 8 }]}>
        <Pressable
          onPress={() => { Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light); router.back(); }}
          style={s.backBtn}
        >
          <View style={[s.backCircle, {
            backgroundColor: isDark ? "rgba(255,255,255,0.08)" : "rgba(0,0,0,0.05)",
            borderColor: isDark ? "rgba(255,255,255,0.12)" : "rgba(0,0,0,0.08)",
          }]}>
            <Feather name="arrow-left" size={20} color={isDark ? "#fff" : "#0F172A"} />
          </View>
        </Pressable>
      </View>

      <ScrollView
        style={s.root}
        contentContainerStyle={[s.content, { paddingTop: topPad + 60, paddingBottom: botPad + 40 }]}
        showsVerticalScrollIndicator={false}
      >
        <Animated.View style={[s.heroWrap, { opacity: headerFade, transform: [{ translateY: headerSlide }] }]}>
          <View style={s.heroEmojiWrap}>
            <LinearGradient colors={["#ef4444", "#f97316"]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={s.heroEmojiCircle}>
              <Text style={s.heroEmoji}>🔥</Text>
            </LinearGradient>
            <View style={[s.heroEmojiGlow, { backgroundColor: "rgba(239,68,68,0.12)" }]} />
          </View>
          <Text style={[s.heroTitle, { color: isDark ? "#fff" : "#0F172A", fontFamily: "Nunito_700Bold" }]}>
            {t.loveTitle}
          </Text>
          <Text style={[s.heroSub, { color: isDark ? "rgba(203,213,225,0.5)" : "#64748B", fontFamily: "Nunito_400Regular" }]}>
            Know the truth about your relationship
          </Text>
        </Animated.View>

        <View style={s.list}>
          {FEATURES.map((f, i) => (
            <FeatureCard key={f.key} feature={f} index={i} isDark={isDark} partnerId={partnerId} />
          ))}
        </View>
      </ScrollView>
    </CosmicBg>
  );
}

const s = StyleSheet.create({
  root: { flex: 1 },
  content: { paddingHorizontal: 18 },

  topBar: { position: "absolute", top: 0, left: 0, right: 0, zIndex: 20, paddingHorizontal: 16, paddingBottom: 8 },
  backBtn: { alignSelf: "flex-start" },
  backCircle: { width: 40, height: 40, borderRadius: 20, alignItems: "center", justifyContent: "center", borderWidth: 1 },

  heroWrap: { alignItems: "center", marginBottom: 26, gap: 8 },
  heroEmojiWrap: { alignItems: "center", justifyContent: "center", marginBottom: 8 },
  heroEmojiCircle: {
    width: 72, height: 72, borderRadius: 36,
    alignItems: "center", justifyContent: "center",
    borderWidth: 2, borderColor: "rgba(255,255,255,0.15)",
  },
  heroEmoji: { fontSize: 34 },
  heroEmojiGlow: {
    position: "absolute", width: 92, height: 92, borderRadius: 46, zIndex: -1,
  },
  heroTitle: { fontSize: 26, letterSpacing: -0.5, textAlign: "center" },
  heroSub: { fontSize: 13, textAlign: "center", letterSpacing: 0.2, maxWidth: 260 },

  list: { gap: 14 },

  card: { borderRadius: 20, overflow: "hidden" },
  cardRow: { flexDirection: "row", alignItems: "center", padding: 18, paddingVertical: 20, gap: 14 },

  iconWrap: {
    width: 50, height: 50, borderRadius: 16,
    alignItems: "center", justifyContent: "center",
    borderWidth: 1, borderColor: "rgba(255,255,255,0.12)",
  },
  iconEmoji: { fontSize: 22 },

  textArea: { flex: 1, gap: 4 },
  cardTitle: { fontSize: 16, letterSpacing: -0.2 },
  cardSub: { fontSize: 11.5, letterSpacing: 0.1 },

  arrowCircle: {
    width: 38, height: 38, borderRadius: 19,
    alignItems: "center", justifyContent: "center",
    borderWidth: 1.5, borderColor: "rgba(255,255,255,0.18)",
  },
});
