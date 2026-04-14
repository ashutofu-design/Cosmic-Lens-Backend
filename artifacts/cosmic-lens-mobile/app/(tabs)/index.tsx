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
  View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import EnergyChart from "@/components/EnergyChart";
import { useUser } from "@/context/UserContext";
import { useColors } from "@/hooks/useColors";
import { computeTodayEnergy } from "@/lib/todayEnergyCalc";
import { computeActiveDasha, type ActiveDashaResult } from "@/lib/proInsightEngine";
import type { MoonHistoryPoint } from "@/types";

const N = 12;
const DEMO_PTS = [42, 55, 38, 61, 70, 65, 48, 72, 68, 54, 60, 63];
const DEMO_LABELS = ["10PM","","","1AM","","","4AM","","","7AM","","Now"];

const BASE_URL = process.env.EXPO_PUBLIC_DOMAIN
  ? `https://${process.env.EXPO_PUBLIC_DOMAIN}`
  : "";

function energyInsight(energy: number): { icon: string; text: string; color: string } {
  if (energy >= 75) return { icon: "🔥", text: "Strong positive energy today", color: "#22c55e" };
  if (energy >= 55) return { icon: "✨", text: "Moderate energy, stay focused", color: "#f59e0b" };
  if (energy >= 35) return { icon: "⚠️", text: "Energy unstable today", color: "#f97316" };
  return { icon: "🌑", text: "Low energy — rest & introspect", color: "#ef4444" };
}

// ── Pulse animation hook ──────────────────────────────────────────────────────
function usePulse() {
  const anim = useRef(new Animated.Value(1)).current;
  useEffect(() => {
    Animated.loop(
      Animated.sequence([
        Animated.timing(anim, { toValue: 1.025, duration: 900, useNativeDriver: true }),
        Animated.timing(anim, { toValue: 1,     duration: 900, useNativeDriver: true }),
      ])
    ).start();
  }, []);
  return anim;
}

// ── Glow pulse for border ─────────────────────────────────────────────────────
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
    setLoading(true);
    setTargetPts([]);
    setLabels([]);
    setSettled(false);

    fetch(`${BASE_URL}/api/moon_history?count=${N}&interval=2`)
      .then(r => r.json())
      .then((data: { points: MoonHistoryPoint[] }) => {
        if (cancelRef.current) return;
        const values: number[] = data.points.map((pt, idx) => {
          if (idx === data.points.length - 1) {
            const e = computeTodayEnergy(pt.longitude, pt.rashiIndex, kundli);
            if (e !== null) {
              setTodayEnergy(e);
              setMoonData({ longitude: pt.longitude, rashiIndex: pt.rashiIndex });
            }
            return e ?? 0;
          }
          return computeTodayEnergy(pt.longitude, pt.rashiIndex, kundli) ?? 0;
        });
        const lbls = data.points.map((pt, idx) =>
          idx === data.points.length - 1 ? "Now" : pt.label
        );
        setTargetPts(values);
        setLabels(lbls);
        setLoading(false);
        setTimeout(() => { if (!cancelRef.current) setSettled(true); }, 1400);
      })
      .catch(() => { if (!cancelRef.current) setLoading(false); });

    return () => { cancelRef.current = true; };
  }, [kundli]);

  if (!isLoading && !user) return <Redirect href="/login" />;

  const topPad = Platform.OS === "web" ? 67 : insets.top;
  const botPad = Platform.OS === "web" ? 34 : insets.bottom;

  const showDemo    = !kundli;
  const chartPts    = showDemo ? DEMO_PTS   : targetPts;
  const chartLbls   = showDemo ? DEMO_LABELS : labels;
  const chartEnergy = showDemo ? 38 : todayEnergy;
  const insight     = energyInsight(chartEnergy);

  const activeDasha: ActiveDashaResult | null =
    kundli && moonData ? computeActiveDasha(kundli, moonData.longitude) : null;

  return (
    <ScrollView
      style={[styles.root, { backgroundColor: colors.background }]}
      contentContainerStyle={[styles.content, { paddingTop: topPad + 16, paddingBottom: botPad + 100 }]}
      showsVerticalScrollIndicator={false}
    >
      {/* Greeting */}
      <View style={styles.greetRow}>
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
          <Feather name="calendar" size={12} color="#00d4ff" />
          <Text style={styles.forecastPillText}>7 Days</Text>
        </Pressable>
      </View>

      {/* ── HERO: Today Energy Card ── */}
      <HeroEnergyCard
        chartPts={chartPts}
        chartLbls={chartLbls}
        chartEnergy={chartEnergy}
        insight={insight}
        showDemo={showDemo}
        loading={!showDemo && loading && targetPts.length === 0}
      />

      {/* ── DOSH ANALYSIS (dominant) ── */}
      <DoshCard onPress={() => { Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium); router.push("/dosh"); }} kundli={kundli} />

      {/* ── UPCOMING CHALLENGES (includes hidden issues) ── */}
      <BadTimeCard onPress={() => { Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light); router.push("/forecast"); }} activeDasha={activeDasha} />

      {/* ── KUNDLI MILAN PREMIUM ── */}
      <KundliMilanCard onPress={() => { Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium); router.push("/kundli-milan"); }} />
    </ScrollView>
  );
}

// ── Hero Energy Card ──────────────────────────────────────────────────────────
function HeroEnergyCard({ chartPts, chartLbls, chartEnergy, insight, showDemo, loading }: {
  chartPts: number[]; chartLbls: string[]; chartEnergy: number;
  insight: { icon: string; text: string; color: string };
  showDemo: boolean; loading: boolean;
}) {
  return (
    <View style={hero.card}>
      {/* Ambient glow */}
      <View style={[hero.glow, { backgroundColor: `${insight.color}18` }]} />

      <View style={hero.header}>
        <View>
          <Text style={hero.label}>TODAY ENERGY</Text>
          <Text style={[hero.score, { color: insight.color }]}>{chartEnergy}<Text style={hero.scoreMax}>/100</Text></Text>
        </View>
        {showDemo && (
          <View style={hero.demoBadge}>
            <Feather name="lock" size={9} color="#3d5a7a" />
            <Text style={hero.demoBadgeText}>DEMO</Text>
          </View>
        )}
      </View>

      {/* Scale chart down so cards below are visible without scrolling */}
      <View style={{ height: 196, overflow: "hidden" }}>
        <View style={{ transform: [{ scale: 0.68 }], marginTop: -48, marginLeft: -16, marginRight: -16 }}>
          <EnergyChart
            targetPts={chartPts}
            labels={chartLbls}
            finalEnergy={chartEnergy}
            loading={loading}
            instant={showDemo}
          />
        </View>
      </View>

      {/* Insight pill */}
      <View style={[hero.insightPill, { backgroundColor: `${insight.color}15`, borderColor: `${insight.color}35` }]}>
        <Text style={hero.insightIcon}>{insight.icon}</Text>
        <Text style={[hero.insightText, { color: insight.color }]}>{insight.text}</Text>
      </View>
    </View>
  );
}

// ── Dosh Analysis Card ────────────────────────────────────────────────────────
function DoshCard({ onPress, kundli }: { onPress: () => void; kundli: any }) {
  const glowOpacity = useOpacityPulse(0.5, 1.0, 900);

  return (
    <Pressable onPress={onPress} style={({ pressed }) => [{ transform: [{ scale: pressed ? 0.975 : 1 }], opacity: pressed ? 0.93 : 1 }]}>
      <LinearGradient
        colors={["#7f1d1d", "#991b1b", "#6b1212"]}
        start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }}
        style={dosh.card}
      >
        {/* Animated border glow */}
        <Animated.View style={[dosh.borderGlow, { opacity: glowOpacity }]} />

        {/* Big decorative symbol */}
        <Text style={dosh.bigSymbol}>☿</Text>

        <View style={dosh.topRow}>
          <View style={dosh.alertBadge}>
            <Text style={dosh.alertBadgeText}>⚠ DOSH ALERT</Text>
          </View>
          <View style={dosh.arrowCircle}>
            <Feather name="arrow-right" size={14} color="#ff6b6b" />
          </View>
        </View>

        <Text style={dosh.title}>Dosh Analysis</Text>
        <Text style={dosh.subtitle}>
          {kundli ? "Active doshas found — see your remedies" : "Kalsarp · Manglik · Pitra · Guru Chandal"}
        </Text>

        <View style={dosh.chipRow}>
          {["Kalsarp", "Manglik", "Pitra"].map(d => (
            <View key={d} style={dosh.chip}>
              <Text style={dosh.chipText}>{d}</Text>
            </View>
          ))}
        </View>
      </LinearGradient>
    </Pressable>
  );
}

// ── Risk Alert Card ───────────────────────────────────────────────────────────
function BadTimeCard({ onPress, activeDasha }: { onPress: () => void; activeDasha: ActiveDashaResult | null }) {
  const dashaTxt = activeDasha
    ? `${activeDasha.mdPlanet}–${activeDasha.adPlanet} dasha active`
    : "Transit & dasha analysis";
  const glowOpacity = useOpacityPulse(0.4, 0.95, 1000);

  return (
    <Pressable onPress={onPress} style={({ pressed }) => [{ transform: [{ scale: pressed ? 0.975 : 1 }], opacity: pressed ? 0.93 : 1 }]}>
      <LinearGradient
        colors={["#7c2d12", "#c2410c", "#6b2200"]}
        start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }}
        style={bad.card}
      >
        <Animated.View style={[bad.borderGlow, { opacity: glowOpacity }]} />

        {/* Decorative icon */}
        <Text style={bad.bigSymbol}>⚡</Text>

        <View style={bad.topRow}>
          <View style={bad.urgencyBadge}>
            <Text style={bad.urgencyText}>🔴 URGENT</Text>
          </View>
          <View style={bad.arrowCircle}>
            <Feather name="arrow-right" size={14} color="#ff8c42" />
          </View>
        </View>

        <Text style={bad.title}>Risk Alert</Text>
        <Text style={bad.subtitle}>Planetary risks & weak houses in your kundli</Text>

        <View style={bad.divider} />
        <View style={bad.bottomRow}>
          <Feather name="clock" size={11} color="#c2410c" />
          <Text style={bad.bottomText}>{dashaTxt} · Tap for full forecast</Text>
        </View>
      </LinearGradient>
    </Pressable>
  );
}

// ── Kundli Milan Premium Card ─────────────────────────────────────────────────
function KundliMilanCard({ onPress }: { onPress: () => void }) {
  const glowOpacity = useOpacityPulse(0.5, 1.0, 1300);
  return (
    <Pressable onPress={onPress} style={({ pressed }) => [{ transform: [{ scale: pressed ? 0.975 : 1 }], opacity: pressed ? 0.93 : 1 }]}>
      <LinearGradient
        colors={["#4c1d95", "#6d28d9", "#3b1570"]}
        start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }}
        style={milan.card}
      >
        <Animated.View style={[milan.borderGlow, { opacity: glowOpacity }]} />

        {/* Decorative symbol */}
        <Text style={milan.bigSymbol}>♥</Text>

        <View style={milan.topRow}>
          <View style={milan.proBadge}>
            <Text style={milan.proBadgeText}>PRO 🔒</Text>
          </View>
          <View style={milan.arrowCircle}>
            <Feather name="arrow-right" size={14} color="#c084fc" />
          </View>
        </View>

        <Text style={milan.title}>Kundli Milan</Text>
        <Text style={milan.subtitle}>36-point compatibility check for marriage</Text>

        <View style={milan.scoreRow}>
          {[72, 80, 65, 90].map((v, i) => (
            <View key={i} style={milan.scoreBar}>
              <View style={[milan.scoreFill, { width: `${v}%`, backgroundColor: i % 2 === 0 ? "#a855f7" : "#ec4899" }]} />
            </View>
          ))}
        </View>
      </LinearGradient>
    </Pressable>
  );
}

// ── Styles ────────────────────────────────────────────────────────────────────
const styles = StyleSheet.create({
  root:    { flex: 1 },
  content: { paddingHorizontal: 14, gap: 8 },

  greetRow: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", marginBottom: 4 },
  greetSub:   { color: "#3d5a7a", fontSize: 11, fontWeight: "600" },
  greetTitle: { color: "#dde8f4", fontSize: 18, fontWeight: "800", marginTop: 2 },

  forecastPill: {
    flexDirection: "row", alignItems: "center", gap: 5,
    backgroundColor: "rgba(0,212,255,0.08)", borderWidth: 1,
    borderColor: "rgba(0,212,255,0.25)", borderRadius: 20,
    paddingVertical: 7, paddingHorizontal: 12,
  },
  forecastPillText: { color: "#00d4ff", fontSize: 11, fontWeight: "700" },
});

// Hero card
const hero = StyleSheet.create({
  card: {
    backgroundColor: "#040e1e", borderRadius: 20, borderWidth: 1,
    borderColor: "rgba(255,255,255,0.07)", padding: 14, overflow: "hidden",
    shadowColor: "#00d4ff", shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.08, shadowRadius: 20, elevation: 4,
  },
  glow: { position: "absolute", top: -40, right: -40, width: 160, height: 160, borderRadius: 80 },
  header: { flexDirection: "row", alignItems: "flex-start", justifyContent: "space-between", marginBottom: 8 },
  label:    { color: "#3d5a7a", fontSize: 9, fontWeight: "800", letterSpacing: 2 },
  score:    { fontSize: 32, fontWeight: "900", marginTop: 2 },
  scoreMax: { fontSize: 14, color: "#1e3a5f", fontWeight: "600" },
  demoBadge: {
    flexDirection: "row", alignItems: "center", gap: 4,
    backgroundColor: "rgba(2,13,26,0.85)", borderWidth: 1,
    borderColor: "rgba(0,200,255,0.15)", paddingVertical: 4,
    paddingHorizontal: 8, borderRadius: 6,
  },
  demoBadgeText: { color: "#3d5a7a", fontSize: 8, fontWeight: "800", letterSpacing: 1.5 },
  insightPill: {
    flexDirection: "row", alignItems: "center", gap: 7, marginTop: 4,
    borderWidth: 1, borderRadius: 10, paddingVertical: 6, paddingHorizontal: 12,
  },
  insightIcon: { fontSize: 14 },
  insightText: { fontSize: 12, fontWeight: "700" },
});

// ── Dosh card styles ──────────────────────────────────────────────────────────
const dosh = StyleSheet.create({
  card: {
    borderRadius: 20, padding: 16, overflow: "hidden",
    shadowColor: "#ff2244", shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.6, shadowRadius: 24, elevation: 14,
  },
  borderGlow: {
    position: "absolute", inset: 0, borderRadius: 20,
    borderWidth: 2, borderColor: "#ff3355", zIndex: 1,
  },
  bigSymbol: {
    position: "absolute", right: 10, top: 0,
    fontSize: 90, opacity: 0.18, color: "#ffffff",
  },
  topRow:       { flexDirection: "row", alignItems: "center", justifyContent: "space-between", marginBottom: 14 },
  alertBadge:   { backgroundColor: "rgba(255,255,255,0.18)", borderWidth: 1, borderColor: "rgba(255,255,255,0.45)", borderRadius: 20, paddingVertical: 5, paddingHorizontal: 12 },
  alertBadgeText:{ color: "#ffffff", fontSize: 10, fontWeight: "900", letterSpacing: 1 },
  arrowCircle:  { width: 32, height: 32, borderRadius: 16, borderWidth: 1.5, borderColor: "rgba(255,255,255,0.4)", backgroundColor: "rgba(255,255,255,0.15)", alignItems: "center", justifyContent: "center" },
  title:        { color: "#ffffff", fontSize: 22, fontWeight: "900", marginBottom: 5, letterSpacing: -0.3 },
  subtitle:     { color: "rgba(255,255,255,0.75)", fontSize: 12, lineHeight: 17, marginBottom: 14 },
  chipRow:      { flexDirection: "row", gap: 7 },
  chip:         { backgroundColor: "rgba(255,255,255,0.15)", borderWidth: 1, borderColor: "rgba(255,255,255,0.35)", borderRadius: 20, paddingVertical: 5, paddingHorizontal: 13 },
  chipText:     { color: "#ffffff", fontSize: 10, fontWeight: "700" },
});

// ── Risk Alert card styles ────────────────────────────────────────────────────
const bad = StyleSheet.create({
  card: {
    borderRadius: 20, padding: 16, overflow: "hidden",
    shadowColor: "#ff6600", shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.5, shadowRadius: 22, elevation: 12,
  },
  borderGlow:   { position: "absolute", inset: 0, borderRadius: 20, borderWidth: 2, borderColor: "#f97316", zIndex: 1 },
  bigSymbol:    { position: "absolute", right: 8, top: 0, fontSize: 85, opacity: 0.18, color: "#ffffff" },
  topRow:       { flexDirection: "row", alignItems: "center", justifyContent: "space-between", marginBottom: 10 },
  urgencyBadge: { backgroundColor: "rgba(255,255,255,0.18)", borderWidth: 1, borderColor: "rgba(255,255,255,0.45)", borderRadius: 20, paddingVertical: 5, paddingHorizontal: 12 },
  urgencyText:  { color: "#ffffff", fontSize: 10, fontWeight: "900", letterSpacing: 0.8 },
  arrowCircle:  { width: 32, height: 32, borderRadius: 16, borderWidth: 1.5, borderColor: "rgba(255,255,255,0.4)", backgroundColor: "rgba(255,255,255,0.15)", alignItems: "center", justifyContent: "center" },
  title:        { color: "#ffffff", fontSize: 22, fontWeight: "900", marginBottom: 5, letterSpacing: -0.3 },
  subtitle:     { color: "rgba(255,255,255,0.75)", fontSize: 12, lineHeight: 17, marginBottom: 12 },
  divider:      { height: 1, backgroundColor: "rgba(255,255,255,0.15)", marginBottom: 10 },
  bottomRow:    { flexDirection: "row", alignItems: "center", gap: 6 },
  bottomText:   { color: "rgba(255,255,255,0.5)", fontSize: 10, flex: 1 },
});

// ── Kundli Milan card styles ──────────────────────────────────────────────────
const milan = StyleSheet.create({
  card: {
    borderRadius: 20, padding: 16, overflow: "hidden",
    shadowColor: "#9933ff", shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.55, shadowRadius: 24, elevation: 14,
  },
  borderGlow:   { position: "absolute", inset: 0, borderRadius: 20, borderWidth: 2, borderColor: "#a855f7", zIndex: 1 },
  bigSymbol:    { position: "absolute", right: 10, top: 0, fontSize: 90, opacity: 0.18, color: "#ffffff" },
  topRow:       { flexDirection: "row", alignItems: "center", justifyContent: "space-between", marginBottom: 14 },
  proBadge:     { backgroundColor: "rgba(255,255,255,0.18)", borderWidth: 1, borderColor: "rgba(255,255,255,0.45)", borderRadius: 20, paddingVertical: 5, paddingHorizontal: 12 },
  proBadgeText: { color: "#ffffff", fontSize: 10, fontWeight: "900" },
  arrowCircle:  { width: 32, height: 32, borderRadius: 16, borderWidth: 1.5, borderColor: "rgba(255,255,255,0.4)", backgroundColor: "rgba(255,255,255,0.15)", alignItems: "center", justifyContent: "center" },
  title:        { color: "#ffffff", fontSize: 22, fontWeight: "900", marginBottom: 5, letterSpacing: -0.3 },
  subtitle:     { color: "rgba(255,255,255,0.75)", fontSize: 12, lineHeight: 17, marginBottom: 14 },
  scoreRow:     { flexDirection: "row", gap: 5 },
  scoreBar:     { flex: 1, height: 5, backgroundColor: "#ffffff11", borderRadius: 3, overflow: "hidden" },
  scoreFill:    { height: "100%", borderRadius: 3 },
});
