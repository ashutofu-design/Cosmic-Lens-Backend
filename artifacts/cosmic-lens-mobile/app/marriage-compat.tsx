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
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { CosmicBg } from "@/components/CosmicBg";
import { useC } from "@/context/ThemeContext";
import { useT } from "@/hooks/useT";
import { useFeatureGate } from "@/components/FeatureGate";

function KundliMilanCard({ isDark }: { isDark: boolean }) {
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const slideAnim = useRef(new Animated.Value(24)).current;
  const scaleAnim = useRef(new Animated.Value(1)).current;
  const glowAnim = useRef(new Animated.Value(0.12)).current;
  const arrowPulse = useRef(new Animated.Value(1)).current;

  useEffect(() => {
    Animated.parallel([
      Animated.timing(fadeAnim, { toValue: 1, duration: 500, delay: 300, useNativeDriver: true }),
      Animated.spring(slideAnim, { toValue: 0, delay: 300, useNativeDriver: true, speed: 14, bounciness: 4 }),
    ]).start();
    const glow = Animated.loop(
      Animated.sequence([
        Animated.timing(glowAnim, { toValue: 0.3, duration: 2500, easing: Easing.inOut(Easing.sin), useNativeDriver: true }),
        Animated.timing(glowAnim, { toValue: 0.08, duration: 2500, easing: Easing.inOut(Easing.sin), useNativeDriver: true }),
      ])
    );
    const arrow = Animated.loop(
      Animated.sequence([
        Animated.timing(arrowPulse, { toValue: 1.12, duration: 1300, easing: Easing.inOut(Easing.sin), useNativeDriver: true }),
        Animated.timing(arrowPulse, { toValue: 1, duration: 1300, easing: Easing.inOut(Easing.sin), useNativeDriver: true }),
      ])
    );
    glow.start();
    arrow.start();
    return () => { glow.stop(); arrow.stop(); };
  }, []);

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
      <Pressable
        onPressIn={handlePressIn}
        onPressOut={handlePressOut}
        onPress={() => {
          Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
          router.push("/kundli-milan" as any);
        }}
      >
        <View style={[s.card, {
          shadowColor: "#6366f1",
          shadowOpacity: isDark ? 0.3 : 0.12,
          shadowRadius: 20,
          shadowOffset: { width: 0, height: 6 },
          elevation: 8,
        }]}>
          {Platform.OS !== "web" ? (
            <BlurView intensity={isDark ? 40 : 55} tint={isDark ? "dark" : "light"} style={StyleSheet.absoluteFill} />
          ) : null}
          <View style={[StyleSheet.absoluteFill, {
            backgroundColor: isDark ? "rgba(14,22,42,0.72)" : "rgba(255,255,255,0.94)",
            borderRadius: 22,
          }]} />

          <Animated.View style={[StyleSheet.absoluteFill, { overflow: "hidden", borderRadius: 22, opacity: glowAnim }]}>
            <LinearGradient
              colors={isDark ? ["rgba(99,102,241,0.18)", "rgba(129,140,248,0.06)", "transparent"] : ["rgba(99,102,241,0.08)", "transparent"]}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 1 }}
              style={StyleSheet.absoluteFill}
            />
          </Animated.View>

          <View style={[StyleSheet.absoluteFill, {
            borderRadius: 22,
            borderWidth: isDark ? 1 : 0.5,
            borderColor: isDark ? "rgba(99,102,241,0.25)" : "rgba(99,102,241,0.0C)",
          }]} />

          {isDark && (
            <LinearGradient
              colors={["rgba(255,255,255,0.04)", "transparent"]}
              start={{ x: 0, y: 0 }}
              end={{ x: 0, y: 1 }}
              style={[StyleSheet.absoluteFill, { borderRadius: 22, height: "50%" }]}
            />
          )}

          <View style={s.cardInner}>
            <LinearGradient
              colors={["#6366f1", "#818cf8"]}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 1 }}
              style={s.iconWrap}
            >
              <Text style={s.iconEmoji}>🔗</Text>
            </LinearGradient>

            <View style={s.textArea}>
              <View style={s.titleRow}>
                <Text style={[s.cardTitle, { color: isDark ? "#fff" : "#0F172A", fontFamily: "Nunito_700Bold" }]}>
                  Kundli Milan
                </Text>
                <LinearGradient colors={["#f59e0b", "#d97706"]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }} style={s.proBadge}>
                  <Text style={s.proText}>PRO</Text>
                </LinearGradient>
              </View>
              <Text style={[s.cardSub, { color: isDark ? "rgba(203,213,225,0.7)" : "#64748B", fontFamily: "Nunito_500Medium" }]} numberOfLines={1}>
                36 Gunas · Ashtakoot match analysis
              </Text>
            </View>

            <Animated.View style={{
              transform: [{ scale: arrowPulse }],
              shadowColor: "#6366f1",
              shadowOpacity: isDark ? 0.5 : 0.2,
              shadowRadius: 12,
              shadowOffset: { width: 0, height: 3 },
              elevation: 6,
            }}>
              <LinearGradient colors={["#6366f1", "#818cf8"]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={s.arrowCircle}>
                <Feather name="chevron-right" size={16} color="#fff" />
              </LinearGradient>
            </Animated.View>
          </View>
        </View>
      </Pressable>
    </Animated.View>
  );
}

export default function MarriageCompatScreen() {
  const C = useC();
  const { LockOverlay } = useFeatureGate("marriage_compat_full");
  const t = useT();
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
            <LinearGradient colors={["#6366f1", "#818cf8"]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={s.heroEmojiCircle}>
              <Text style={s.heroEmoji}>💍</Text>
            </LinearGradient>
            <View style={[s.heroEmojiGlow, { backgroundColor: "rgba(99,102,241,0.12)" }]} />
          </View>
          <Text style={[s.heroTitle, { color: isDark ? "#fff" : "#0F172A", fontFamily: "Nunito_700Bold" }]}>
            {t.marriageCompatTitle}
          </Text>
          <Text style={[s.heroSub, { color: isDark ? "rgba(203,213,225,0.5)" : "#64748B", fontFamily: "Nunito_400Regular" }]}>
            Check long-term marriage potential
          </Text>
        </Animated.View>

        <KundliMilanCard isDark={isDark} />

        <View style={[s.footer, {
          borderColor: isDark ? "rgba(255,255,255,0.06)" : "rgba(0,0,0,0.04)",
          borderWidth: isDark ? 1 : 0,
        }]}>
          {Platform.OS !== "web" ? (
            <BlurView intensity={isDark ? 30 : 45} tint={isDark ? "dark" : "light"} style={StyleSheet.absoluteFill} />
          ) : null}
          <View style={[StyleSheet.absoluteFill, {
            backgroundColor: isDark ? "rgba(14,22,42,0.5)" : "rgba(255,255,255,0.88)",
            borderRadius: 20,
          }]} />
          <View style={s.footerRow}>
            <View style={[s.footerIcon, { backgroundColor: isDark ? `${ac}12` : `${ac}0A` }]}>
              <Feather name="lock" size={16} color={ac} />
            </View>
            <View style={{ flex: 1 }}>
              <Text style={[s.footerTitle, { color: isDark ? "rgba(255,255,255,0.55)" : "#475569", fontFamily: "Nunito_600SemiBold" }]}>
                More tools coming soon
              </Text>
              <Text style={[s.footerSub, { color: isDark ? "rgba(255,255,255,0.3)" : "#94A3B8", fontFamily: "Nunito_400Regular" }]}>
                Nakshatra Match, Manglik Check & more
              </Text>
            </View>
          </View>
        </View>
      </ScrollView>
      {LockOverlay}
    </CosmicBg>
  );
}

const s = StyleSheet.create({
  root: { flex: 1 },
  content: { paddingHorizontal: 18 },

  topBar: { position: "absolute", top: 0, left: 0, right: 0, zIndex: 20, paddingHorizontal: 16, paddingBottom: 8 },
  backBtn: { alignSelf: "flex-start" },
  backCircle: { width: 40, height: 40, borderRadius: 20, alignItems: "center", justifyContent: "center", borderWidth: 1 },

  heroWrap: { alignItems: "center", marginBottom: 28, gap: 8 },
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

  card: { borderRadius: 22, overflow: "hidden" },
  cardInner: { flexDirection: "row", alignItems: "center", padding: 20, paddingVertical: 22, gap: 14 },

  iconWrap: {
    width: 54, height: 54, borderRadius: 18,
    alignItems: "center", justifyContent: "center",
    borderWidth: 1, borderColor: "rgba(255,255,255,0.12)",
  },
  iconEmoji: { fontSize: 24 },

  textArea: { flex: 1, gap: 4 },
  titleRow: { flexDirection: "row", alignItems: "center", gap: 8 },
  cardTitle: { fontSize: 17, letterSpacing: -0.2 },
  cardSub: { fontSize: 12, letterSpacing: 0.1 },

  proBadge: { paddingHorizontal: 8, paddingVertical: 2.5, borderRadius: 8 },
  proText: { color: "#fff", fontSize: 8, fontFamily: "Nunito_800ExtraBold", letterSpacing: 1.2 },

  arrowCircle: {
    width: 40, height: 40, borderRadius: 20,
    alignItems: "center", justifyContent: "center",
    borderWidth: 1.5, borderColor: "rgba(255,255,255,0.18)",
  },

  footer: {
    borderRadius: 20, overflow: "hidden", padding: 16, marginTop: 24,
  },
  footerRow: { flexDirection: "row", alignItems: "center", gap: 14 },
  footerIcon: { width: 40, height: 40, borderRadius: 13, alignItems: "center", justifyContent: "center" },
  footerTitle: { fontSize: 13, letterSpacing: 0.1 },
  footerSub: { fontSize: 11, marginTop: 2 },
});
