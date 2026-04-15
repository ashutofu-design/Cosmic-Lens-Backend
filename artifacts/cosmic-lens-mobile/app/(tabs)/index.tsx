import { Feather } from "@expo/vector-icons";
import { LinearGradient } from "expo-linear-gradient";
import * as Haptics from "expo-haptics";
import { Redirect, router } from "expo-router";
import React, { useEffect, useRef, useState } from "react";
import {
  Animated,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  useWindowDimensions,
  View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { CosmicBg } from "@/components/CosmicBg";
import EnergyChart from "@/components/EnergyChart";
import { useUser } from "@/context/UserContext";
import { getT } from "@/lib/i18n";
import { useColors } from "@/hooks/useColors";
import { computeTodayEnergy } from "@/lib/todayEnergyCalc";
import { computeActiveDasha, type ActiveDashaResult } from "@/lib/proInsightEngine";
import type { MoonHistoryPoint } from "@/types";

// ── Font aliases ──────────────────────────────────────────────────────────────
const F = {
  regular:  "Nunito_400Regular",
  medium:   "Nunito_500Medium",
  semibold: "Nunito_600SemiBold",
  bold:     "Nunito_700Bold",
};

const N = 12;
const DEMO_PTS    = [42, 55, 38, 61, 70, 65, 48, 72, 68, 54, 60, 63];
const DEMO_LABELS = ["10PM","","","1AM","","","4AM","","","7AM","","Now"];

import { API_BASE as BASE_URL, apiFetch } from "@/lib/apiConfig";

function energyInsight(energy: number): { icon: string; text: string; color: string } {
  if (energy >= 75) return { icon: "🔥", text: "Strong positive energy today",  color: "#22c55e" };
  if (energy >= 55) return { icon: "✨", text: "Moderate energy, stay focused",  color: "#f59e0b" };
  if (energy >= 35) return { icon: "⚠️", text: "Energy unstable today",          color: "#f97316" };
  return             { icon: "🌑", text: "Low energy — rest & introspect",    color: "#ef4444" };
}

// ── Animation hooks ───────────────────────────────────────────────────────────
function usePulseScale(amplitude = 0.022, dur = 950) {
  const anim = useRef(new Animated.Value(1)).current;
  useEffect(() => {
    Animated.loop(
      Animated.sequence([
        Animated.timing(anim, { toValue: 1 + amplitude, duration: dur, useNativeDriver: true }),
        Animated.timing(anim, { toValue: 1,             duration: dur, useNativeDriver: true }),
      ])
    ).start();
  }, []);
  return anim;
}

function useOpacityPulse(min = 0.4, max = 1.0, dur = 1100) {
  const anim = useRef(new Animated.Value(min)).current;
  useEffect(() => {
    Animated.loop(
      Animated.sequence([
        Animated.timing(anim, { toValue: max, duration: dur, useNativeDriver: true }),
        Animated.timing(anim, { toValue: min, duration: dur, useNativeDriver: true }),
      ])
    ).start();
  }, []);
  return anim;
}

function useFadeSlideIn(delay = 0) {
  const opacity   = useRef(new Animated.Value(0)).current;
  const translateY = useRef(new Animated.Value(18)).current;
  useEffect(() => {
    Animated.parallel([
      Animated.timing(opacity,    { toValue: 1, duration: 500, delay, useNativeDriver: true }),
      Animated.timing(translateY, { toValue: 0, duration: 440, delay, useNativeDriver: true }),
    ]).start();
  }, []);
  return { opacity, transform: [{ translateY }] };
}

// ── Shimmer sweep — makes card feel live & active ─────────────────────────────
function useShimmer(cardWidth: number) {
  const anim = useRef(new Animated.Value(-cardWidth)).current;
  useEffect(() => {
    Animated.loop(
      Animated.sequence([
        Animated.delay(1800),
        Animated.timing(anim, { toValue: cardWidth * 2, duration: 800, useNativeDriver: true }),
        Animated.delay(300),
      ])
    ).start();
    return () => anim.stopAnimation();
  }, [cardWidth]);
  return anim;
}

// ── Blink — for live indicators ───────────────────────────────────────────────
function useBlink(onMs = 450, offMs = 450, pauseMs = 1100) {
  const anim = useRef(new Animated.Value(1)).current;
  useEffect(() => {
    Animated.loop(
      Animated.sequence([
        Animated.timing(anim, { toValue: 0.1, duration: offMs, useNativeDriver: true }),
        Animated.timing(anim, { toValue: 1,   duration: onMs,  useNativeDriver: true }),
        Animated.delay(pauseMs),
      ])
    ).start();
  }, []);
  return anim;
}

// ── Score counter animation ───────────────────────────────────────────────────
function useCountUp(target: number, delay = 200) {
  const [display, setDisplay] = useState(0);
  useEffect(() => {
    const timeout = setTimeout(() => {
      let start = 0;
      const step = Math.ceil(target / 30);
      const timer = setInterval(() => {
        start = Math.min(start + step, target);
        setDisplay(start);
        if (start >= target) clearInterval(timer);
      }, 30);
      return () => clearInterval(timer);
    }, delay);
    return () => clearTimeout(timeout);
  }, [target]);
  return display;
}

// ── Home Screen ───────────────────────────────────────────────────────────────
export default function HomeScreen() {
  const insets = useSafeAreaInsets();
  const colors = useColors();
  const { kundli, todayEnergy, setTodayEnergy, setMoonData, moonData, user, isLoading, language } = useUser();
  const t = getT(language);

  const [targetPts, setTargetPts] = useState<number[]>([]);
  const [labels,    setLabels]    = useState<string[]>([]);
  const [loading,   setLoading]   = useState(false);
  const [settled,   setSettled]   = useState(false);
  const cancelRef = useRef(false);

  useEffect(() => {
    if (!kundli) return;
    cancelRef.current = false;
    setLoading(true); setTargetPts([]); setLabels([]); setSettled(false);

    apiFetch(`${BASE_URL}/api/moon_history?count=${N}&interval=2`)
      .then(r => r.json())
      .then((data: { points: MoonHistoryPoint[] }) => {
        if (cancelRef.current) return;
        const values = data.points.map((pt, idx) => {
          if (idx === data.points.length - 1) {
            const e = computeTodayEnergy(pt.longitude, pt.rashiIndex, kundli);
            if (e !== null) { setTodayEnergy(e); setMoonData({ longitude: pt.longitude, rashiIndex: pt.rashiIndex }); }
            return e ?? 0;
          }
          return computeTodayEnergy(pt.longitude, pt.rashiIndex, kundli) ?? 0;
        });
        const lbls = data.points.map((pt, idx) =>
          idx === data.points.length - 1 ? "Now" : pt.label
        );
        setTargetPts(values); setLabels(lbls); setLoading(false);
        setTimeout(() => { if (!cancelRef.current) setSettled(true); }, 1400);
      })
      .catch(() => { if (!cancelRef.current) setLoading(false); });

    return () => { cancelRef.current = true; };
  }, [kundli]);

  // ── All hooks MUST come before any early return ───────────────────────────
  const greetAnim = useFadeSlideIn(0);
  const heroAnim  = useFadeSlideIn(120);
  const card1Anim = useFadeSlideIn(220);
  const card2Anim = useFadeSlideIn(310);
  const card3Anim = useFadeSlideIn(400);

  if (!isLoading && !user) return <Redirect href="/login" />;

  const topPad = Platform.OS === "web" ? 67 : insets.top;
  const botPad = Platform.OS === "web" ? 34 : insets.bottom;

  const showDemo    = !kundli;
  const chartPts    = showDemo ? DEMO_PTS    : targetPts;
  const chartLbls   = showDemo ? DEMO_LABELS : labels;
  const chartEnergy = showDemo ? 38          : todayEnergy;
  const insight     = energyInsight(chartEnergy);

  const activeDasha: ActiveDashaResult | null =
    kundli && moonData ? computeActiveDasha(kundli, moonData.longitude) : null;

  return (
    <CosmicBg contentStyle={{ paddingTop: topPad, paddingBottom: botPad + 60 }}>

      {/* ── Greeting ── */}
      <Animated.View style={[styles.greetRow, greetAnim, { paddingHorizontal: 16, paddingVertical: 8 }]}>
        <View>
          <Text style={[styles.greetSub, { color: colors.mutedForeground }]}>
            {kundli ? `Hello, ${kundli.name}` : "Hello"}
          </Text>
          <Text style={[styles.greetTitle, { color: colors.foreground }]}>{t.todayEnergy}</Text>
        </View>
        <Pressable
          onPress={() => { Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light); router.push("/forecast"); }}
          style={styles.forecastPill}
        >
          <Feather name="calendar" size={11} color="#f59e0b" />
          <Text style={styles.forecastPillText}>7 Days</Text>
        </Pressable>
      </Animated.View>

      {/* ── Hero Energy Card — 60% ── */}
      <Animated.View style={[heroAnim, { flex: 6, paddingHorizontal: 12, paddingBottom: 8 }]}>
        <HeroEnergyCard
          chartPts={chartPts}
          chartLbls={chartLbls}
          chartEnergy={chartEnergy}
          insight={insight}
          showDemo={showDemo}
          loading={!showDemo && loading && targetPts.length === 0}
        />
      </Animated.View>

      {/* ── 3 Feature Rows — 40% ── */}
      <View style={{ flex: 4, paddingHorizontal: 12, paddingBottom: 6, justifyContent: "space-around" }}>

        <Animated.View style={card1Anim}>
          <DoshMini onPress={() => { Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium); router.push("/dosh"); }} />
        </Animated.View>

        <Animated.View style={card2Anim}>
          <BadTimeMini onPress={() => { Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light); router.push("/forecast"); }} activeDasha={activeDasha} />
        </Animated.View>

        <Animated.View style={card3Anim}>
          <MilanMini onPress={() => { Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium); router.push("/kundli-milan"); }} />
        </Animated.View>

      </View>

    </CosmicBg>
  );
}

// ── Hero Energy Card — vertical layout, fills 60% ────────────────────────────
function HeroEnergyCard({ chartPts, chartLbls, chartEnergy, insight, showDemo, loading }: {
  chartPts: number[]; chartLbls: string[]; chartEnergy: number;
  insight: { icon: string; text: string; color: string };
  showDemo: boolean; loading: boolean;
}) {
  const { language } = useUser();
  const tHero = getT(language);
  const { C: Ctheme } = useColors();
  const displayScore = useCountUp(chartEnergy, 350);
  const glowPulse    = useOpacityPulse(0.06, 0.22, 1800);

  return (
    <View style={[hero.card, { flex: 1, backgroundColor: Ctheme.bgCard, borderColor: Ctheme.border2, boxShadow: Ctheme.cardShadow } as any]}>
      <Animated.View style={[hero.glow, { backgroundColor: insight.color, opacity: glowPulse }]} />

      {/* ── TOP ROW: label + score + demo badge ── */}
      <View style={hero.topRow}>
        <View>
          <Text style={[hero.label, { color: Ctheme.textMuted }]}>{tHero.todayEnergy.toUpperCase()}</Text>
          <View style={{ flexDirection: "row", alignItems: "flex-end", gap: 3, marginTop: 1 }}>
            <Text style={[hero.score, { color: insight.color }]}>{displayScore}</Text>
            <Text style={[hero.scoreMax, { color: Ctheme.textDim }]}>/100</Text>
          </View>
        </View>
        <View style={{ alignItems: "flex-end", gap: 5 }}>
          {showDemo && (
            <View style={[hero.demoBadge, { backgroundColor: Ctheme.bgCard2, borderColor: Ctheme.border }]}>
              <Feather name="lock" size={9} color={Ctheme.textDim} />
              <Text style={[hero.demoBadgeText, { color: Ctheme.textDim }]}>DEMO</Text>
            </View>
          )}
          <View style={[hero.insightPill, { backgroundColor: `${insight.color}12`, borderColor: `${insight.color}28` }]}>
            <Text style={hero.insightIcon}>{insight.icon}</Text>
            <Text style={[hero.insightText, { color: insight.color }]}>{insight.text}</Text>
          </View>
        </View>
      </View>

      {/* ── CHART — fills remaining space, no transform needed ── */}
      <View style={{ flex: 1, marginTop: 8 }}>
        <EnergyChart
          targetPts={chartPts}
          labels={chartLbls}
          finalEnergy={chartEnergy}
          loading={loading}
          instant={showDemo}
        />
      </View>
    </View>
  );
}

// ── Dosh Mini — full-width horizontal row ─────────────────────────────────────
function DoshMini({ onPress }: { onPress: () => void }) {
  const blinkDot = useBlink(400, 400, 1400);
  const shimmerX = useShimmer(360);
  const { C } = useColors();
  const grad = C.isDark
    ? (["#3b0a0a","#5c1111"] as const)
    : (["#fff0f0","#ffe2e6"] as const);
  const titleClr = C.isDark ? "#ffffff" : "#be123c";
  const subClr   = C.isDark ? "rgba(255,255,255,0.45)" : "rgba(190,18,60,0.6)";

  return (
    <Pressable onPress={onPress} style={({ pressed }) => [mini.row, pressed && mini.rowPressed]}>
      <LinearGradient colors={grad} start={{x:0,y:0}} end={{x:1,y:0}} style={mini.rowGrad}>
        <Animated.View style={[mini.shimmer, { transform: [{ translateX: shimmerX }] }]} />
        <View style={[mini.border, { borderColor: C.isDark ? "rgba(255,51,85,0.35)" : "rgba(255,51,85,0.20)" }]} />

        <View style={[mini.iconCircle, { backgroundColor:"rgba(255,34,68,0.18)", borderColor:"rgba(255,34,68,0.35)" }]}>
          <Text style={mini.iconEmoji}>☿</Text>
        </View>

        <View style={mini.textBlock}>
          <Text style={[mini.rowTitle, { color: titleClr }]}>Dosh Analysis</Text>
          <Text style={[mini.rowSub, { color: subClr }]}>3 doshas detected in chart</Text>
        </View>

        <View style={mini.rightBlock}>
          <View style={[mini.badge, { backgroundColor:"rgba(255,34,68,0.18)", borderColor:"rgba(255,34,68,0.4)" }]}>
            <Animated.View style={[mini.badgeDot, { backgroundColor:"#ff2244", opacity: blinkDot }]} />
            <Text style={[mini.badgeTxt, { color:"#ff6b6b" }]}>LIVE</Text>
          </View>
          <Feather name="chevron-right" size={14} color={C.isDark ? "rgba(255,107,107,0.5)" : "rgba(190,18,60,0.5)"} />
        </View>
      </LinearGradient>
    </Pressable>
  );
}

// ── Bad Time Mini — full-width horizontal row ─────────────────────────────────
function BadTimeMini({ onPress, activeDasha }: { onPress: () => void; activeDasha: ActiveDashaResult | null }) {
  const blinkDot = useBlink(350, 350, 1200);
  const shimmerX = useShimmer(360);
  const { C } = useColors();
  const grad = C.isDark
    ? (["#2d1005","#5c2208"] as const)
    : (["#fff5ec","#ffe8d0"] as const);
  const titleClr = C.isDark ? "#ffffff" : "#c2410c";
  const subClr   = C.isDark ? "rgba(255,255,255,0.45)" : "rgba(194,65,12,0.6)";

  return (
    <Pressable onPress={onPress} style={({ pressed }) => [mini.row, pressed && mini.rowPressed]}>
      <LinearGradient colors={grad} start={{x:0,y:0}} end={{x:1,y:0}} style={mini.rowGrad}>
        <Animated.View style={[mini.shimmer, { transform: [{ translateX: shimmerX }] }]} />
        <View style={[mini.border, { borderColor: C.isDark ? "rgba(249,115,22,0.35)" : "rgba(249,115,22,0.22)" }]} />

        <View style={[mini.iconCircle, { backgroundColor:"rgba(249,115,22,0.18)", borderColor:"rgba(249,115,22,0.35)" }]}>
          <Text style={mini.iconEmoji}>⚡</Text>
        </View>

        <View style={mini.textBlock}>
          <Text style={[mini.rowTitle, { color: titleClr }]}>Risk Alert</Text>
          <Text style={[mini.rowSub, { color: subClr }]}>
            {activeDasha ? `${activeDasha.mdPlanet}–${activeDasha.adPlanet} Dasha active` : "2 risk periods ahead"}
          </Text>
        </View>

        <View style={mini.rightBlock}>
          <View style={[mini.badge, { backgroundColor:"rgba(249,115,22,0.18)", borderColor:"rgba(249,115,22,0.4)" }]}>
            <Animated.View style={[mini.badgeDot, { backgroundColor:"#f97316", opacity: blinkDot }]} />
            <Text style={[mini.badgeTxt, { color:"#fb923c" }]}>ALERT</Text>
          </View>
          <Feather name="chevron-right" size={14} color={C.isDark ? "rgba(251,146,60,0.5)" : "rgba(194,65,12,0.5)"} />
        </View>
      </LinearGradient>
    </Pressable>
  );
}

// ── Kundli Milan Mini — full-width horizontal row ─────────────────────────────
function MilanMini({ onPress }: { onPress: () => void }) {
  const shimmerX = useShimmer(360);
  const { C } = useColors();
  const grad = C.isDark
    ? (["#1e0a3d","#3b1570"] as const)
    : (["#f5f0ff","#ede0fe"] as const);
  const titleClr = C.isDark ? "#ffffff" : "#6d28d9";
  const subClr   = C.isDark ? "rgba(255,255,255,0.45)" : "rgba(109,40,217,0.6)";

  return (
    <Pressable onPress={onPress} style={({ pressed }) => [mini.row, pressed && mini.rowPressed]}>
      <LinearGradient colors={grad} start={{x:0,y:0}} end={{x:1,y:0}} style={mini.rowGrad}>
        <Animated.View style={[mini.shimmer, { transform: [{ translateX: shimmerX }] }]} />
        <View style={[mini.border, { borderColor: C.isDark ? "rgba(168,85,247,0.35)" : "rgba(168,85,247,0.22)" }]} />

        <View style={[mini.iconCircle, { backgroundColor:"rgba(168,85,247,0.18)", borderColor:"rgba(168,85,247,0.35)" }]}>
          <Text style={mini.iconEmoji}>♥</Text>
        </View>

        <View style={mini.textBlock}>
          <Text style={[mini.rowTitle, { color: titleClr }]}>Kundli Milan</Text>
          <Text style={[mini.rowSub, { color: subClr }]}>36 guna match · Vivah compatibility</Text>
        </View>

        <View style={mini.rightBlock}>
          <View style={[mini.badge, { backgroundColor:"rgba(168,85,247,0.18)", borderColor:"rgba(168,85,247,0.4)" }]}>
            <Feather name="lock" size={8} color="#c084fc" />
            <Text style={[mini.badgeTxt, { color:"#c084fc" }]}>PRO</Text>
          </View>
          <Feather name="chevron-right" size={14} color={C.isDark ? "rgba(192,132,252,0.5)" : "rgba(109,40,217,0.5)"} />
        </View>
      </LinearGradient>
    </Pressable>
  );
}

// ── Dosh Analysis Card — LIVE, URGENT, PREMIUM ───────────────────────────────
function DoshCard({ onPress, kundli }: { onPress: () => void; kundli: any }) {
  const { width: screenW }  = useWindowDimensions();
  const cardW               = screenW - 28; // scroll padding
  const glowOpacity         = useOpacityPulse(0.5, 1.0, 750);
  const outerGlow           = useOpacityPulse(0.3, 0.9, 1100);
  const shimmerX            = useShimmer(cardW);
  const blinkDot            = useBlink(400, 400, 1200);
  const ctaPulse            = usePulseScale(0.03, 800);
  const warningPulse        = useOpacityPulse(0.6, 1.0, 600);

  const DOSHAS = ["Kalsarp", "Manglik", "Pitra"];

  return (
    <Pressable
      onPress={onPress}
      style={({ pressed }) => [{
        transform: [{ scale: pressed ? 0.970 : 1 }],
        opacity: pressed ? 0.88 : 1,
      }]}
    >
      {/* Outer shadow glow — pulsing red aura */}
      <Animated.View style={[dosh.outerGlow, { opacity: outerGlow }]} />

      <LinearGradient
        colors={["#6b0f0f", "#991b1b", "#7f1d1d"]}
        start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }}
        style={dosh.card}
      >
        {/* Shimmer sweep */}
        <Animated.View style={[dosh.shimmer, { transform: [{ translateX: shimmerX }] }]} />

        {/* Animated border */}
        <Animated.View style={[dosh.borderGlow, { opacity: glowOpacity }]} />

        {/* Decorative astro symbol */}
        <Text style={dosh.bigSymbol}>☿</Text>

        {/* ── TOP ROW: Live badge + count + arrow ── */}
        <View style={dosh.topRow}>
          <View style={dosh.liveRow}>
            {/* Blinking red dot */}
            <Animated.View style={[dosh.liveDot, { opacity: blinkDot }]} />
            <Text style={dosh.liveTxt}>LIVE ANALYSIS</Text>
          </View>
          <Animated.View style={[dosh.arrowCircle, { transform: [{ scale: ctaPulse }] }]}>
            <Feather name="chevron-right" size={16} color="#ff6b6b" />
          </Animated.View>
        </View>

        {/* ── TITLE ── */}
        <Text style={dosh.title}>Dosh Analysis</Text>

        {/* ── THREAT METER ── */}
        <View style={dosh.meterRow}>
          <Text style={dosh.meterLabel}>Threat Level</Text>
          <View style={dosh.meterTrack}>
            <Animated.View style={[dosh.meterFill, { opacity: warningPulse }]} />
          </View>
          <Text style={dosh.meterValue}>HIGH</Text>
        </View>

        {/* ── DOSH CHIPS ── */}
        <View style={dosh.chipRow}>
          {DOSHAS.map((d, i) => (
            <View key={d} style={[dosh.chip, i === 0 && dosh.chipDanger]}>
              <View style={[dosh.chipDot, { backgroundColor: i === 0 ? "#ff3355" : "rgba(255,255,255,0.5)" }]} />
              <Text style={[dosh.chipText, i === 0 && { color: "#ff6b6b" }]}>{d}</Text>
            </View>
          ))}
        </View>

        {/* ── CTA FOOTER ── */}
        <View style={dosh.ctaBar}>
          <Text style={dosh.ctaTxt}>⚠ 3 issues detected in your chart</Text>
          <View style={dosh.ctaBtn}>
            <Text style={dosh.ctaBtnTxt}>Tap to Reveal</Text>
            <Feather name="arrow-right" size={11} color="#ff6b6b" />
          </View>
        </View>
      </LinearGradient>
    </Pressable>
  );
}

// ── Risk Alert Card — LIVE, URGENT, PREMIUM ───────────────────────────────────
function BadTimeCard({ onPress, activeDasha }: { onPress: () => void; activeDasha: ActiveDashaResult | null }) {
  const { width: screenW } = useWindowDimensions();
  const cardW              = screenW - 28;
  const dashaTxt           = activeDasha
    ? `${activeDasha.mdPlanet}–${activeDasha.adPlanet} Dasha`
    : "Saturn Transit";
  const glowOpacity        = useOpacityPulse(0.4, 1.0, 700);
  const outerGlow          = useOpacityPulse(0.25, 0.85, 950);
  const shimmerX           = useShimmer(cardW);
  const blinkDot           = useBlink(350, 350, 1400);
  const ctaPulse           = usePulseScale(0.03, 900);
  const warningPulse       = useOpacityPulse(0.5, 1.0, 550);

  return (
    <Pressable
      onPress={onPress}
      style={({ pressed }) => [{
        transform: [{ scale: pressed ? 0.970 : 1 }],
        opacity: pressed ? 0.88 : 1,
      }]}
    >
      {/* Outer glow — pulsing orange aura */}
      <Animated.View style={[bad.outerGlow, { opacity: outerGlow }]} />

      <LinearGradient
        colors={["#5c1f08", "#c2410c", "#7c2d12"]}
        start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }}
        style={bad.card}
      >
        {/* Shimmer sweep */}
        <Animated.View style={[bad.shimmer, { transform: [{ translateX: shimmerX }] }]} />

        <Animated.View style={[bad.borderGlow, { opacity: glowOpacity }]} />
        <Text style={bad.bigSymbol}>⚡</Text>

        {/* ── TOP ROW ── */}
        <View style={bad.topRow}>
          <View style={bad.liveRow}>
            <Animated.View style={[bad.liveDot, { opacity: blinkDot }]} />
            <Text style={bad.liveTxt}>ALERT NOW</Text>
          </View>
          <Animated.View style={[bad.arrowCircle, { transform: [{ scale: ctaPulse }] }]}>
            <Feather name="chevron-right" size={16} color="#ff8c42" />
          </Animated.View>
        </View>

        {/* ── TITLE ── */}
        <Text style={bad.title}>Risk Alert</Text>

        {/* ── ACTIVE DASHA + RISK BARS ── */}
        <View style={bad.dashaRow}>
          <Feather name="zap" size={11} color="#ff8c42" />
          <Text style={bad.dashaTxt}>
            Active: <Text style={{ color: "#ffb347", fontFamily: F.bold }}>{dashaTxt}</Text>
          </Text>
        </View>

        {/* Risk indicators */}
        <View style={bad.riskRow}>
          {[
            { label: "Sade Sati",   pct: 75, hot: true  },
            { label: "Weak Houses", pct: 55, hot: false },
          ].map(r => (
            <View key={r.label} style={bad.riskItem}>
              <View style={bad.riskHeader}>
                <Text style={bad.riskLabel}>{r.label}</Text>
                <Animated.View style={{ opacity: r.hot ? warningPulse : 1 }}>
                  <Text style={[bad.riskPct, r.hot && { color: "#ff4444" }]}>{r.pct}%</Text>
                </Animated.View>
              </View>
              <View style={bad.riskTrack}>
                <Animated.View style={[
                  bad.riskFill,
                  { width: `${r.pct}%`, backgroundColor: r.hot ? "#ff4444" : "#f97316" },
                  r.hot && { opacity: warningPulse },
                ]} />
              </View>
            </View>
          ))}
        </View>

        {/* ── CTA FOOTER ── */}
        <View style={bad.ctaBar}>
          <Text style={bad.ctaTxt}>⚡ 2 active planetary risks</Text>
          <View style={bad.ctaBtn}>
            <Text style={bad.ctaBtnTxt}>Check Now</Text>
            <Feather name="arrow-right" size={11} color="#ff8c42" />
          </View>
        </View>
      </LinearGradient>
    </Pressable>
  );
}

// ── Kundli Milan Card ─────────────────────────────────────────────────────────
function KundliMilanCard({ onPress }: { onPress: () => void }) {
  const glowOpacity = useOpacityPulse(0.5, 1.0, 1300);
  const pulse       = usePulseScale(0.012, 1350);

  return (
    <Pressable onPress={onPress} style={({ pressed }) => [{ transform: [{ scale: pressed ? 0.974 : 1 }], opacity: pressed ? 0.92 : 1 }]}>
      <LinearGradient
        colors={["#4c1d95", "#7c3aed", "#3b1570"]}
        start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }}
        style={milan.card}
      >
        <Animated.View style={[milan.borderGlow, { opacity: glowOpacity }]} />
        <Text style={milan.bigSymbol}>♥</Text>

        <View style={milan.row}>
          <View style={milan.left}>
            <View style={milan.badge}>
              <Text style={milan.badgeText}>PRO 🔒</Text>
            </View>
            <Text style={milan.title}>Kundli Milan</Text>
            <Text style={milan.subtitle}>36-point compatibility check</Text>
            <View style={milan.scoreRow}>
              {[72, 84, 66, 91].map((v, i) => (
                <View key={i} style={milan.barTrack}>
                  <View style={[milan.barFill, { width: `${v}%`, backgroundColor: i % 2 === 0 ? "#a855f7" : "#ec4899" }]} />
                </View>
              ))}
            </View>
          </View>
          <Animated.View style={[milan.arrowCircle, { transform: [{ scale: pulse }] }]}>
            <Feather name="arrow-right" size={15} color="#c084fc" />
          </Animated.View>
        </View>
      </LinearGradient>
    </Pressable>
  );
}

// ── Styles ────────────────────────────────────────────────────────────────────
const styles = StyleSheet.create({
  root:    { flex: 1 },
  content: { paddingHorizontal: 14, gap: 9 },

  greetRow: {
    flexDirection: "row", alignItems: "center",
    justifyContent: "space-between", marginBottom: 2,
  },
  greetSub: {
    color: "#3d5a7a", fontSize: 11,
    fontFamily: F.semibold, letterSpacing: 0.2,
  },
  greetTitle: {
    color: "#dde8f4", fontSize: 17,
    fontFamily: F.bold, marginTop: 1, letterSpacing: -0.3,
  },
  forecastPill: {
    flexDirection: "row", alignItems: "center", gap: 5,
    backgroundColor: "rgba(245,158,11,0.07)", borderWidth: 1,
    borderColor: "rgba(245,158,11,0.22)", borderRadius: 20,
    paddingVertical: 7, paddingHorizontal: 11,
  },
  forecastPillText: {
    color: "#f59e0b", fontSize: 11, fontFamily: F.bold,
  },
});

// ── Hero card ─────────────────────────────────────────────────────────────────
const hero = StyleSheet.create({
  card: {
    backgroundColor: "#040e1e", borderRadius: 18, borderWidth: 1,
    borderColor: "rgba(255,255,255,0.06)", padding: 14, overflow: "hidden",
    shadowColor: "#f59e0b", shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.1, shadowRadius: 18, elevation: 5,
  },
  glow: {
    position: "absolute", top: -50, right: -50,
    width: 200, height: 200, borderRadius: 100,
  },
  topRow: {
    flexDirection: "row", alignItems: "flex-start",
    justifyContent: "space-between", gap: 8,
  },
  label:    { color: "#3d5a7a", fontSize: 9, fontFamily: F.bold, letterSpacing: 2.2 },
  score:    { fontSize: 38, fontFamily: F.bold, letterSpacing: -1.5, lineHeight: 42 },
  scoreMax: { fontSize: 15, color: "#1e3a5f", fontFamily: F.semibold, paddingBottom: 6 },
  demoBadge: {
    flexDirection: "row", alignItems: "center", gap: 4,
    backgroundColor: "rgba(2,13,26,0.85)", borderWidth: 1,
    borderColor: "rgba(0,200,255,0.15)", paddingVertical: 4,
    paddingHorizontal: 8, borderRadius: 6,
  },
  demoBadgeText: { color: "#3d5a7a", fontSize: 8, fontFamily: F.bold, letterSpacing: 1.5 },
  insightPill: {
    flexDirection: "row", alignItems: "center", gap: 6,
    borderWidth: 1, borderRadius: 8, paddingVertical: 5, paddingHorizontal: 10,
  },
  insightIcon: { fontSize: 12 },
  insightText: { fontSize: 10, fontFamily: F.semibold, maxWidth: 140 },
});

// ── Mini cards — full-width horizontal rows ────────────────────────────────────
const mini = StyleSheet.create({
  row: {
    borderRadius: 14, overflow: "hidden",
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.4, shadowRadius: 10, elevation: 6,
  },
  rowPressed: { opacity: 0.82 },
  rowGrad: {
    flexDirection: "row", alignItems: "center", gap: 12,
    paddingVertical: 13, paddingHorizontal: 14, overflow: "hidden",
  },
  shimmer: {
    position: "absolute", top: 0, bottom: 0, width: 60, zIndex: 2,
    backgroundColor: "rgba(255,255,255,0.06)",
    transform: [{ skewX: "-18deg" }],
  },
  border: {
    position: "absolute", inset: 0, borderRadius: 14,
    borderWidth: 1, zIndex: 1,
  },
  iconCircle: {
    width: 40, height: 40, borderRadius: 12,
    borderWidth: 1, alignItems: "center", justifyContent: "center",
  },
  iconEmoji: { fontSize: 18 },
  textBlock: { flex: 1, gap: 2 },
  rowTitle: { color: "#ffffff", fontSize: 13.5, fontFamily: F.bold, letterSpacing: -0.2 },
  rowSub:   { color: "rgba(255,255,255,0.45)", fontSize: 10.5, fontFamily: F.medium },
  rightBlock: { flexDirection: "row", alignItems: "center", gap: 8 },
  badge: {
    flexDirection: "row", alignItems: "center", gap: 4,
    borderWidth: 1, borderRadius: 20,
    paddingVertical: 3, paddingHorizontal: 8,
  },
  badgeDot: { width: 5, height: 5, borderRadius: 2.5 },
  badgeTxt: { fontSize: 8.5, fontFamily: F.bold, letterSpacing: 1 },
});

// ── Shared card layout ────────────────────────────────────────────────────────
const CARD_RADIUS   = 18;
const CARD_PADDING  = 14;

// ── Dosh card — premium live ───────────────────────────────────────────────────
const dosh = StyleSheet.create({
  outerGlow: {
    position: "absolute", inset: -3, borderRadius: CARD_RADIUS + 3,
    backgroundColor: "#ff1133",
    shadowColor: "#ff1133", shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 1, shadowRadius: 18, elevation: 0,
  },
  card: {
    borderRadius: CARD_RADIUS, padding: CARD_PADDING, overflow: "hidden",
    shadowColor: "#ff2244", shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.7, shadowRadius: 24, elevation: 18,
  },
  shimmer: {
    position: "absolute", top: 0, bottom: 0, width: 60, zIndex: 2,
    backgroundColor: "rgba(255,255,255,0.07)",
    transform: [{ skewX: "-20deg" }],
  },
  borderGlow: {
    position: "absolute", inset: 0, borderRadius: CARD_RADIUS,
    borderWidth: 1.5, borderColor: "#ff3355", zIndex: 1,
  },
  bigSymbol: {
    position: "absolute", right: 4, top: -8,
    fontSize: 88, opacity: 0.11, color: "#ffffff",
  },
  topRow:   { flexDirection: "row", alignItems: "center", justifyContent: "space-between", marginBottom: 6 },
  liveRow:  { flexDirection: "row", alignItems: "center", gap: 6 },
  liveDot:  { width: 7, height: 7, borderRadius: 3.5, backgroundColor: "#ff2244" },
  liveTxt:  { color: "#ff6b6b", fontSize: 9, fontFamily: F.bold, letterSpacing: 1.8 },
  arrowCircle: {
    width: 30, height: 30, borderRadius: 15, borderWidth: 1.5,
    borderColor: "rgba(255,100,100,0.5)", backgroundColor: "rgba(255,50,50,0.2)",
    alignItems: "center", justifyContent: "center",
  },
  title:    { color: "#ffffff", fontSize: 21, fontFamily: F.bold, letterSpacing: -0.6, marginBottom: 8 },
  meterRow: { flexDirection: "row", alignItems: "center", gap: 8, marginBottom: 10 },
  meterLabel: { color: "rgba(255,255,255,0.55)", fontSize: 9.5, fontFamily: F.medium, width: 72 },
  meterTrack: { flex: 1, height: 5, backgroundColor: "rgba(255,255,255,0.1)", borderRadius: 3, overflow: "hidden" },
  meterFill:  { width: "78%", height: "100%", backgroundColor: "#ff2244", borderRadius: 3 },
  meterValue: { color: "#ff4466", fontSize: 9.5, fontFamily: F.bold, letterSpacing: 0.8, width: 32 },
  chipRow:  { flexDirection: "row", gap: 6, marginBottom: 10 },
  chip: {
    flexDirection: "row", alignItems: "center", gap: 5,
    backgroundColor: "rgba(255,255,255,0.11)", borderWidth: 1,
    borderColor: "rgba(255,255,255,0.25)", borderRadius: 20,
    paddingVertical: 4, paddingHorizontal: 10,
  },
  chipDanger: {
    backgroundColor: "rgba(255,34,68,0.22)", borderColor: "rgba(255,50,80,0.5)",
  },
  chipDot:  { width: 5, height: 5, borderRadius: 2.5 },
  chipText: { color: "#ffffff", fontSize: 9.5, fontFamily: F.semibold },
  ctaBar: {
    flexDirection: "row", alignItems: "center", justifyContent: "space-between",
    backgroundColor: "rgba(0,0,0,0.25)", borderRadius: 10,
    paddingVertical: 8, paddingHorizontal: 12,
    borderWidth: 1, borderColor: "rgba(255,50,70,0.3)",
  },
  ctaTxt:    { color: "rgba(255,255,255,0.6)", fontSize: 10, fontFamily: F.medium },
  ctaBtn:    { flexDirection: "row", alignItems: "center", gap: 4 },
  ctaBtnTxt: { color: "#ff6b6b", fontSize: 10, fontFamily: F.bold, letterSpacing: 0.3 },
});

// ── Risk Alert card — premium live ────────────────────────────────────────────
const bad = StyleSheet.create({
  outerGlow: {
    position: "absolute", inset: -3, borderRadius: CARD_RADIUS + 3,
    backgroundColor: "#ff6600",
    shadowColor: "#ff6600", shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 1, shadowRadius: 16, elevation: 0,
  },
  card: {
    borderRadius: CARD_RADIUS, padding: CARD_PADDING, overflow: "hidden",
    shadowColor: "#ff6600", shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.65, shadowRadius: 22, elevation: 16,
  },
  shimmer: {
    position: "absolute", top: 0, bottom: 0, width: 60, zIndex: 2,
    backgroundColor: "rgba(255,255,255,0.07)",
    transform: [{ skewX: "-20deg" }],
  },
  borderGlow: {
    position: "absolute", inset: 0, borderRadius: CARD_RADIUS,
    borderWidth: 1.5, borderColor: "#f97316", zIndex: 1,
  },
  bigSymbol: {
    position: "absolute", right: 6, top: -6,
    fontSize: 84, opacity: 0.11, color: "#ffffff",
  },
  topRow:   { flexDirection: "row", alignItems: "center", justifyContent: "space-between", marginBottom: 6 },
  liveRow:  { flexDirection: "row", alignItems: "center", gap: 6 },
  liveDot:  { width: 7, height: 7, borderRadius: 3.5, backgroundColor: "#ff6600" },
  liveTxt:  { color: "#ffb347", fontSize: 9, fontFamily: F.bold, letterSpacing: 1.8 },
  arrowCircle: {
    width: 30, height: 30, borderRadius: 15, borderWidth: 1.5,
    borderColor: "rgba(255,140,66,0.5)", backgroundColor: "rgba(255,100,30,0.2)",
    alignItems: "center", justifyContent: "center",
  },
  title:    { color: "#ffffff", fontSize: 21, fontFamily: F.bold, letterSpacing: -0.6, marginBottom: 6 },
  dashaRow: { flexDirection: "row", alignItems: "center", gap: 6, marginBottom: 10 },
  dashaTxt: { color: "rgba(255,255,255,0.65)", fontSize: 10.5, fontFamily: F.medium },
  riskRow:  { gap: 7, marginBottom: 10 },
  riskItem: { gap: 4 },
  riskHeader: { flexDirection: "row", alignItems: "center", justifyContent: "space-between" },
  riskLabel:  { color: "rgba(255,255,255,0.65)", fontSize: 9.5, fontFamily: F.medium },
  riskPct:    { color: "#ff8c42", fontSize: 9.5, fontFamily: F.bold },
  riskTrack:  { height: 4, backgroundColor: "rgba(255,255,255,0.1)", borderRadius: 3, overflow: "hidden" },
  riskFill:   { height: "100%", borderRadius: 3 },
  ctaBar: {
    flexDirection: "row", alignItems: "center", justifyContent: "space-between",
    backgroundColor: "rgba(0,0,0,0.25)", borderRadius: 10,
    paddingVertical: 8, paddingHorizontal: 12,
    borderWidth: 1, borderColor: "rgba(255,120,30,0.3)",
  },
  ctaTxt:    { color: "rgba(255,255,255,0.6)", fontSize: 10, fontFamily: F.medium },
  ctaBtn:    { flexDirection: "row", alignItems: "center", gap: 4 },
  ctaBtnTxt: { color: "#ff8c42", fontSize: 10, fontFamily: F.bold, letterSpacing: 0.3 },
});

// ── Kundli Milan card ─────────────────────────────────────────────────────────
const milan = StyleSheet.create({
  card: {
    borderRadius: CARD_RADIUS, padding: CARD_PADDING, overflow: "hidden",
    shadowColor: "#9933ff", shadowOffset: { width: 0, height: 5 },
    shadowOpacity: 0.5, shadowRadius: 22, elevation: 12,
  },
  borderGlow: {
    position: "absolute", inset: 0, borderRadius: CARD_RADIUS,
    borderWidth: 1.5, borderColor: "#a855f7",
  },
  bigSymbol: {
    position: "absolute", right: 8, top: -4,
    fontSize: 80, opacity: 0.14, color: "#ffffff",
  },
  row:  { flexDirection: "row", alignItems: "center", justifyContent: "space-between" },
  left: { flex: 1, gap: 5 },
  badge: {
    alignSelf: "flex-start",
    backgroundColor: "rgba(255,255,255,0.16)", borderWidth: 1,
    borderColor: "rgba(255,255,255,0.4)", borderRadius: 20,
    paddingVertical: 4, paddingHorizontal: 11,
  },
  badgeText:  { color: "#ffffff", fontSize: 9.5, fontFamily: F.bold, letterSpacing: 0.5 },
  title:      { color: "#ffffff", fontSize: 20, fontFamily: F.bold, letterSpacing: -0.5 },
  subtitle:   { color: "rgba(255,255,255,0.72)", fontSize: 11.5, fontFamily: F.medium },
  scoreRow:   { flexDirection: "row", gap: 5 },
  barTrack:   { flex: 1, height: 4, backgroundColor: "rgba(255,255,255,0.12)", borderRadius: 3, overflow: "hidden" },
  barFill:    { height: "100%", borderRadius: 3 },
  arrowCircle: {
    width: 34, height: 34, borderRadius: 17, borderWidth: 1.5,
    borderColor: "rgba(255,255,255,0.38)", backgroundColor: "rgba(255,255,255,0.13)",
    alignItems: "center", justifyContent: "center", marginLeft: 10,
  },
});
