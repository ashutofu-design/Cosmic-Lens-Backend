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

import EnergyChart from "@/components/EnergyChart";
import { useUser } from "@/context/UserContext";
import { useColors } from "@/hooks/useColors";
import { computeTodayEnergy } from "@/lib/todayEnergyCalc";
import { computeActiveDasha, type ActiveDashaResult } from "@/lib/proInsightEngine";
import type { MoonHistoryPoint } from "@/types";

// ── Font aliases ──────────────────────────────────────────────────────────────
const F = {
  regular:  "Inter_400Regular",
  medium:   "Inter_500Medium",
  semibold: "Inter_600SemiBold",
  bold:     "Inter_700Bold",
};

const N = 12;
const DEMO_PTS    = [42, 55, 38, 61, 70, 65, 48, 72, 68, 54, 60, 63];
const DEMO_LABELS = ["10PM","","","1AM","","","4AM","","","7AM","","Now"];

const BASE_URL = process.env.EXPO_PUBLIC_DOMAIN
  ? `https://${process.env.EXPO_PUBLIC_DOMAIN}`
  : "";

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
  const { kundli, todayEnergy, setTodayEnergy, setMoonData, moonData, user, isLoading } = useUser();

  const [targetPts, setTargetPts] = useState<number[]>([]);
  const [labels,    setLabels]    = useState<string[]>([]);
  const [loading,   setLoading]   = useState(false);
  const [settled,   setSettled]   = useState(false);
  const cancelRef = useRef(false);

  useEffect(() => {
    if (!kundli) return;
    cancelRef.current = false;
    setLoading(true); setTargetPts([]); setLabels([]); setSettled(false);

    fetch(`${BASE_URL}/api/moon_history?count=${N}&interval=2`)
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
    <ScrollView
      style={[styles.root, { backgroundColor: colors.background }]}
      contentContainerStyle={[styles.content, { paddingTop: topPad + 12, paddingBottom: botPad + 100 }]}
      showsVerticalScrollIndicator={false}
      scrollEnabled={true}
    >
      {/* ── Greeting ── */}
      <Animated.View style={[styles.greetRow, greetAnim]}>
        <View>
          <Text style={styles.greetSub}>
            {kundli ? `Namaste, ${kundli.name}` : "Namaste"}
          </Text>
          <Text style={styles.greetTitle}>Aaj ka Cosmic Report</Text>
        </View>
        <Pressable
          onPress={() => { Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light); router.push("/forecast"); }}
          style={styles.forecastPill}
        >
          <Feather name="calendar" size={11} color="#00d4ff" />
          <Text style={styles.forecastPillText}>7 Days</Text>
        </Pressable>
      </Animated.View>

      {/* ── Hero Energy Card ── */}
      <Animated.View style={heroAnim}>
        <HeroEnergyCard
          chartPts={chartPts}
          chartLbls={chartLbls}
          chartEnergy={chartEnergy}
          insight={insight}
          showDemo={showDemo}
          loading={!showDemo && loading && targetPts.length === 0}
        />
      </Animated.View>

      {/* ── 3 Feature Cards ── */}
      <Animated.View style={card1Anim}>
        <DoshCard onPress={() => { Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium); router.push("/dosh"); }} kundli={kundli} />
      </Animated.View>

      <Animated.View style={card2Anim}>
        <BadTimeCard onPress={() => { Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light); router.push("/forecast"); }} activeDasha={activeDasha} />
      </Animated.View>

      <Animated.View style={card3Anim}>
        <KundliMilanCard onPress={() => { Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium); router.push("/kundli-milan"); }} />
      </Animated.View>
    </ScrollView>
  );
}

// ── Hero Energy Card ──────────────────────────────────────────────────────────
// EnergyChart SVG is 300×300 (VW=300, VH=300)
const CHART_SVG = 300;

function HeroEnergyCard({ chartPts, chartLbls, chartEnergy, insight, showDemo, loading }: {
  chartPts: number[]; chartLbls: string[]; chartEnergy: number;
  insight: { icon: string; text: string; color: string };
  showDemo: boolean; loading: boolean;
}) {
  const { width: screenW } = useWindowDimensions();
  const displayScore = useCountUp(chartEnergy, 350);
  const glowPulse    = useOpacityPulse(0.05, 0.2, 1800);

  // Square chart — side-by-side with score for compact hero card
  // Chart occupies ~45% of card width as a clean square
  const cardInnerW = screenW - 28; // scroll padding 14+14
  const chartSide  = Math.floor(cardInnerW * 0.46);
  const scale      = chartSide / CHART_SVG;
  const offset     = -(CHART_SVG * (1 - scale)) / 2;

  return (
    <View style={hero.card}>
      {/* Ambient glow blob */}
      <Animated.View style={[hero.glow, { backgroundColor: insight.color, opacity: glowPulse }]} />

      {/* Horizontal layout: left = score info, right = square chart */}
      <View style={hero.body}>

        {/* Left: score + label + insight */}
        <View style={hero.left}>
          <Text style={hero.label}>TODAY ENERGY</Text>
          <View style={{ flexDirection: "row", alignItems: "flex-end", gap: 2, marginTop: 2 }}>
            <Text style={[hero.score, { color: insight.color }]}>{displayScore}</Text>
            <Text style={hero.scoreMax}>/100</Text>
          </View>

          {showDemo && (
            <View style={[hero.demoBadge, { marginTop: 8 }]}>
              <Feather name="lock" size={9} color="#3d5a7a" />
              <Text style={hero.demoBadgeText}>DEMO</Text>
            </View>
          )}

          {/* Insight pill below score */}
          <View style={[hero.insightPill, { backgroundColor: `${insight.color}12`, borderColor: `${insight.color}30`, marginTop: "auto" }]}>
            <Text style={hero.insightIcon}>{insight.icon}</Text>
            <Text style={[hero.insightText, { color: insight.color }]}>{insight.text}</Text>
          </View>
        </View>

        {/* Right: perfect square chart — no clipping, no overflow */}
        <View style={{
          width: chartSide,
          height: chartSide,
          overflow: "hidden",
          borderRadius: 10,
          backgroundColor: "rgba(0,0,0,0.15)",
        }}>
          <View style={{
            width: CHART_SVG,
            height: CHART_SVG,
            transform: [{ scale }],
            marginTop: offset,
            marginLeft: offset,
          }}>
            <EnergyChart
              targetPts={chartPts}
              labels={chartLbls}
              finalEnergy={chartEnergy}
              loading={loading}
              instant={showDemo}
            />
          </View>
        </View>

      </View>
    </View>
  );
}

// ── Dosh Analysis Card ────────────────────────────────────────────────────────
function DoshCard({ onPress, kundli }: { onPress: () => void; kundli: any }) {
  const glowOpacity = useOpacityPulse(0.45, 1.0, 850);
  const pulse       = usePulseScale(0.012, 1100);

  return (
    <Pressable onPress={onPress} style={({ pressed }) => [{ transform: [{ scale: pressed ? 0.974 : 1 }], opacity: pressed ? 0.92 : 1 }]}>
      <LinearGradient
        colors={["#7f1d1d", "#b91c1c", "#6b1212"]}
        start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }}
        style={dosh.card}
      >
        <Animated.View style={[dosh.borderGlow, { opacity: glowOpacity }]} />

        <Text style={dosh.bigSymbol}>☿</Text>

        <View style={dosh.row}>
          <View style={dosh.left}>
            <View style={dosh.badge}>
              <Text style={dosh.badgeText}>⚠ DOSH ALERT</Text>
            </View>
            <Text style={dosh.title}>Dosh Analysis</Text>
            <Text style={dosh.subtitle}>
              {kundli ? "Active doshas — see remedies" : "Kalsarp · Manglik · Pitra"}
            </Text>
            <View style={dosh.chipRow}>
              {["Kalsarp", "Manglik", "Pitra"].map(d => (
                <View key={d} style={dosh.chip}>
                  <Text style={dosh.chipText}>{d}</Text>
                </View>
              ))}
            </View>
          </View>
          <Animated.View style={[dosh.arrowCircle, { transform: [{ scale: pulse }] }]}>
            <Feather name="arrow-right" size={15} color="#ff6b6b" />
          </Animated.View>
        </View>
      </LinearGradient>
    </Pressable>
  );
}

// ── Risk Alert Card ───────────────────────────────────────────────────────────
function BadTimeCard({ onPress, activeDasha }: { onPress: () => void; activeDasha: ActiveDashaResult | null }) {
  const dashaTxt    = activeDasha ? `${activeDasha.mdPlanet}–${activeDasha.adPlanet} dasha active` : "Transit & dasha analysis";
  const glowOpacity = useOpacityPulse(0.35, 0.9, 1000);
  const pulse       = usePulseScale(0.012, 1200);

  return (
    <Pressable onPress={onPress} style={({ pressed }) => [{ transform: [{ scale: pressed ? 0.974 : 1 }], opacity: pressed ? 0.92 : 1 }]}>
      <LinearGradient
        colors={["#7c2d12", "#c2410c", "#5c1f08"]}
        start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }}
        style={bad.card}
      >
        <Animated.View style={[bad.borderGlow, { opacity: glowOpacity }]} />
        <Text style={bad.bigSymbol}>⚡</Text>

        <View style={bad.row}>
          <View style={bad.left}>
            <View style={bad.badge}>
              <Text style={bad.badgeText}>🔴 URGENT</Text>
            </View>
            <Text style={bad.title}>Risk Alert</Text>
            <Text style={bad.subtitle}>Planetary risks & weak houses</Text>
            <View style={bad.bottomRow}>
              <Feather name="clock" size={10} color="rgba(255,255,255,0.5)" />
              <Text style={bad.bottomText}>{dashaTxt}</Text>
            </View>
          </View>
          <Animated.View style={[bad.arrowCircle, { transform: [{ scale: pulse }] }]}>
            <Feather name="arrow-right" size={15} color="#ff8c42" />
          </Animated.View>
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
    backgroundColor: "rgba(0,212,255,0.07)", borderWidth: 1,
    borderColor: "rgba(0,212,255,0.22)", borderRadius: 20,
    paddingVertical: 7, paddingHorizontal: 11,
  },
  forecastPillText: {
    color: "#00d4ff", fontSize: 11, fontFamily: F.bold,
  },
});

// ── Hero card ─────────────────────────────────────────────────────────────────
const hero = StyleSheet.create({
  card: {
    backgroundColor: "#040e1e", borderRadius: 18, borderWidth: 1,
    borderColor: "rgba(255,255,255,0.06)", padding: 14, overflow: "hidden",
    shadowColor: "#00d4ff", shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.1, shadowRadius: 18, elevation: 5,
  },
  glow: {
    position: "absolute", top: -50, right: -50,
    width: 200, height: 200, borderRadius: 100,
  },
  // Horizontal layout: score on left, chart square on right
  body: {
    flexDirection: "row", alignItems: "stretch", gap: 12,
  },
  left: {
    flex: 1, gap: 6,
  },
  label:    { color: "#3d5a7a", fontSize: 9, fontFamily: F.bold, letterSpacing: 2.2 },
  score:    { fontSize: 36, fontFamily: F.bold, letterSpacing: -1.5, lineHeight: 40 },
  scoreMax: { fontSize: 14, color: "#1e3a5f", fontFamily: F.semibold, paddingBottom: 5 },
  demoBadge: {
    alignSelf: "flex-start",
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
  insightText: { fontSize: 10.5, fontFamily: F.semibold, flex: 1, flexWrap: "wrap" },
});

// ── Shared card layout ────────────────────────────────────────────────────────
const CARD_RADIUS   = 18;
const CARD_PADDING  = 14;

// ── Dosh card ─────────────────────────────────────────────────────────────────
const dosh = StyleSheet.create({
  card: {
    borderRadius: CARD_RADIUS, padding: CARD_PADDING, overflow: "hidden",
    shadowColor: "#ff2244", shadowOffset: { width: 0, height: 5 },
    shadowOpacity: 0.55, shadowRadius: 20, elevation: 12,
  },
  borderGlow: {
    position: "absolute", inset: 0, borderRadius: CARD_RADIUS,
    borderWidth: 1.5, borderColor: "#ff3355",
  },
  bigSymbol: {
    position: "absolute", right: 6, top: -6,
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
  badgeText:  { color: "#ffffff", fontSize: 9.5, fontFamily: F.bold, letterSpacing: 0.9 },
  title:      { color: "#ffffff", fontSize: 20, fontFamily: F.bold, letterSpacing: -0.5 },
  subtitle:   { color: "rgba(255,255,255,0.72)", fontSize: 11.5, fontFamily: F.medium, lineHeight: 16 },
  chipRow:    { flexDirection: "row", gap: 6 },
  chip: {
    backgroundColor: "rgba(255,255,255,0.13)", borderWidth: 1,
    borderColor: "rgba(255,255,255,0.3)", borderRadius: 20,
    paddingVertical: 3, paddingHorizontal: 10,
  },
  chipText:   { color: "#ffffff", fontSize: 9.5, fontFamily: F.semibold },
  arrowCircle: {
    width: 34, height: 34, borderRadius: 17, borderWidth: 1.5,
    borderColor: "rgba(255,255,255,0.38)", backgroundColor: "rgba(255,255,255,0.13)",
    alignItems: "center", justifyContent: "center", marginLeft: 10,
  },
});

// ── Risk Alert card ───────────────────────────────────────────────────────────
const bad = StyleSheet.create({
  card: {
    borderRadius: CARD_RADIUS, padding: CARD_PADDING, overflow: "hidden",
    shadowColor: "#ff6600", shadowOffset: { width: 0, height: 5 },
    shadowOpacity: 0.5, shadowRadius: 20, elevation: 11,
  },
  borderGlow: {
    position: "absolute", inset: 0, borderRadius: CARD_RADIUS,
    borderWidth: 1.5, borderColor: "#f97316",
  },
  bigSymbol: {
    position: "absolute", right: 8, top: -4,
    fontSize: 78, opacity: 0.14, color: "#ffffff",
  },
  row:  { flexDirection: "row", alignItems: "center", justifyContent: "space-between" },
  left: { flex: 1, gap: 5 },
  badge: {
    alignSelf: "flex-start",
    backgroundColor: "rgba(255,255,255,0.16)", borderWidth: 1,
    borderColor: "rgba(255,255,255,0.4)", borderRadius: 20,
    paddingVertical: 4, paddingHorizontal: 11,
  },
  badgeText:  { color: "#ffffff", fontSize: 9.5, fontFamily: F.bold, letterSpacing: 0.8 },
  title:      { color: "#ffffff", fontSize: 20, fontFamily: F.bold, letterSpacing: -0.5 },
  subtitle:   { color: "rgba(255,255,255,0.72)", fontSize: 11.5, fontFamily: F.medium },
  bottomRow:  { flexDirection: "row", alignItems: "center", gap: 5 },
  bottomText: { color: "rgba(255,255,255,0.48)", fontSize: 10, fontFamily: F.medium, flex: 1 },
  arrowCircle: {
    width: 34, height: 34, borderRadius: 17, borderWidth: 1.5,
    borderColor: "rgba(255,255,255,0.38)", backgroundColor: "rgba(255,255,255,0.13)",
    alignItems: "center", justifyContent: "center", marginLeft: 10,
  },
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
