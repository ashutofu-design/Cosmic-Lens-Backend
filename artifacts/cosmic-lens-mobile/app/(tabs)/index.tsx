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
  const pulse = usePulse();
  const glowOpacity = useOpacityPulse(0.3, 0.85, 1000);

  return (
    <Pressable onPress={onPress} style={({ pressed }) => [{ opacity: pressed ? 0.9 : 1 }]}>
      <Animated.View style={[dosh.card, { transform: [{ scale: pulse }] }]}>
        {/* Pulsing border glow */}
        <Animated.View style={[dosh.borderGlow, { opacity: glowOpacity }]} />

        <LinearGradient
          colors={["#1a0408", "#200610", "#180309"]}
          style={dosh.gradient}
        >
          <View style={dosh.row}>
            <View style={dosh.iconWrap}>
              <Text style={{ fontSize: 26 }}>☿</Text>
            </View>
            <View style={{ flex: 1 }}>
              <View style={dosh.titleRow}>
                <Text style={dosh.title}>⚠️ Dosh Analysis</Text>
                <View style={dosh.alertBadge}>
                  <Text style={dosh.alertBadgeText}>ALERT</Text>
                </View>
              </View>
              <Text style={dosh.subtitle}>
                {kundli ? "Graha doshas detected in your chart" : "Scan your kundli for doshas"}
              </Text>
              <Text style={dosh.cta}>Tap to view remedies →</Text>
            </View>
          </View>

          {/* Chips */}
          <View style={dosh.chipRow}>
            {["Kalsarp", "Manglik", "Pitra"].map(d => (
              <View key={d} style={dosh.chip}>
                <Text style={dosh.chipText}>{d}</Text>
              </View>
            ))}
          </View>
        </LinearGradient>
      </Animated.View>
    </Pressable>
  );
}

// ── Upcoming Challenges Card (merged with Hidden Issues) ──────────────────────
function BadTimeCard({ onPress, activeDasha }: { onPress: () => void; activeDasha: ActiveDashaResult | null }) {
  const dashaTxt = activeDasha
    ? `${activeDasha.mdPlanet}–${activeDasha.adPlanet} dasha active`
    : "Transit & dasha analysis";

  return (
    <Pressable onPress={onPress} style={({ pressed }) => [{ opacity: pressed ? 0.88 : 1 }]}>
      <LinearGradient
        colors={["#1f0400", "#1a0600", "#150300"]}
        start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }}
        style={bad.card}
      >
        {/* Top row — urgency */}
        <View style={bad.topRow}>
          <View style={bad.iconWrap}>
            <Feather name="zap" size={20} color="#ef4444" />
          </View>
          <View style={{ flex: 1 }}>
            <Text style={bad.title}>Upcoming Challenges</Text>
            <Text style={bad.subtitle}>Agle kuch din mushkil ho sakte hain</Text>
          </View>
          <View style={bad.urgencyBadge}>
            <Text style={bad.urgencyText}>URGENT</Text>
          </View>
        </View>

        <View style={bad.divider} />

        {/* Hidden issues row */}
        <View style={bad.issueRow}>
          <Feather name="alert-triangle" size={12} color="#f59e0b" />
          <Text style={bad.issueText}>Weak planets & afflicted houses detected in kundli</Text>
        </View>

        {/* Dasha row */}
        <View style={bad.bottomRow}>
          <Feather name="clock" size={11} color="#7f1d1d" />
          <Text style={bad.bottomText}>{dashaTxt} · Tap for full forecast</Text>
        </View>
      </LinearGradient>
    </Pressable>
  );
}

// ── Kundli Milan Premium Card ─────────────────────────────────────────────────
function KundliMilanCard({ onPress }: { onPress: () => void }) {
  const glowOpacity = useOpacityPulse(0.5, 1.0, 1400);
  return (
    <Pressable onPress={onPress} style={({ pressed }) => [{ opacity: pressed ? 0.88 : 1 }]}>
      <LinearGradient
        colors={["#140a2e", "#1a0d3a", "#110830"]}
        start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }}
        style={milan.card}
      >
        <Animated.View style={[milan.glowBar, { opacity: glowOpacity }]} />
        <View style={milan.row}>
          <View style={milan.iconWrap}>
            <Text style={{ fontSize: 24 }}>♥</Text>
          </View>
          <View style={{ flex: 1 }}>
            <View style={milan.titleRow}>
              <Text style={milan.title}>Kundli Milan</Text>
              <View style={milan.proBadge}>
                <Text style={milan.proBadgeText}>PRO 🔒</Text>
              </View>
            </View>
            <Text style={milan.subtitle}>36-point compatibility check for marriage</Text>
            <Text style={milan.cta}>Check compatibility →</Text>
          </View>
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

// Dosh card
const dosh = StyleSheet.create({
  card: {
    borderRadius: 20, overflow: "hidden",
    shadowColor: "#ef4444", shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.35, shadowRadius: 18, elevation: 8,
  },
  borderGlow: {
    position: "absolute", inset: 0, borderRadius: 20,
    borderWidth: 1.5, borderColor: "#ef4444", zIndex: 1,
  },
  gradient: { borderRadius: 20, padding: 11, gap: 8 },
  row: { flexDirection: "row", alignItems: "flex-start", gap: 10 },
  iconWrap: {
    width: 44, height: 44, borderRadius: 12,
    backgroundColor: "rgba(239,68,68,0.12)", borderWidth: 1,
    borderColor: "rgba(239,68,68,0.3)", alignItems: "center", justifyContent: "center", flexShrink: 0,
  },
  titleRow: { flexDirection: "row", alignItems: "center", gap: 8, marginBottom: 4 },
  title:    { color: "#fca5a5", fontSize: 16, fontWeight: "800" },
  alertBadge: { backgroundColor: "#7f1d1d", borderRadius: 6, paddingHorizontal: 7, paddingVertical: 2 },
  alertBadgeText: { color: "#fca5a5", fontSize: 8, fontWeight: "800", letterSpacing: 1 },
  subtitle: { color: "#7f1d1d", fontSize: 12, lineHeight: 17, marginBottom: 5 },
  cta:      { color: "#ef4444", fontSize: 12, fontWeight: "700" },
  chipRow:  { flexDirection: "row", flexWrap: "wrap", gap: 6 },
  chip: {
    backgroundColor: "rgba(239,68,68,0.1)", borderWidth: 1,
    borderColor: "rgba(239,68,68,0.25)", borderRadius: 20,
    paddingVertical: 4, paddingHorizontal: 10,
  },
  chipText: { color: "#f87171", fontSize: 10, fontWeight: "600" },
});

// Bad time card (merged with hidden issues)
const bad = StyleSheet.create({
  card: {
    borderRadius: 18, padding: 10, borderWidth: 1,
    borderColor: "rgba(239,68,68,0.2)",
    shadowColor: "#dc2626", shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.22, shadowRadius: 16, elevation: 6,
  },
  topRow:    { flexDirection: "row", alignItems: "center", gap: 12 },
  iconWrap: {
    width: 44, height: 44, borderRadius: 12,
    backgroundColor: "rgba(239,68,68,0.12)", borderWidth: 1,
    borderColor: "rgba(239,68,68,0.25)", alignItems: "center", justifyContent: "center", flexShrink: 0,
  },
  title:    { color: "#fca5a5", fontSize: 14, fontWeight: "800", marginBottom: 3 },
  subtitle: { color: "#7f1d1d", fontSize: 11 },
  urgencyBadge: {
    backgroundColor: "rgba(239,68,68,0.15)", borderWidth: 1,
    borderColor: "rgba(239,68,68,0.35)", borderRadius: 8,
    paddingVertical: 4, paddingHorizontal: 8,
  },
  urgencyText: { color: "#ef4444", fontSize: 8, fontWeight: "900", letterSpacing: 1.5 },
  divider:   { height: 1, backgroundColor: "rgba(239,68,68,0.08)", marginVertical: 6 },
  issueRow:  { flexDirection: "row", alignItems: "center", gap: 6, marginBottom: 4 },
  issueText: { color: "#92400e", fontSize: 10, flex: 1 },
  bottomRow: { flexDirection: "row", alignItems: "center", gap: 6 },
  bottomText: { color: "#7f1d1d", fontSize: 10, flex: 1 },
});

// Kundli milan card
const milan = StyleSheet.create({
  card: {
    borderRadius: 20, padding: 11, borderWidth: 1,
    borderColor: "rgba(167,139,250,0.3)", overflow: "hidden",
    shadowColor: "#a78bfa", shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.25, shadowRadius: 18, elevation: 7,
  },
  glowBar: {
    position: "absolute", top: 0, left: 0, right: 0, height: 2,
    backgroundColor: "#a78bfa", borderRadius: 2,
  },
  row:      { flexDirection: "row", alignItems: "flex-start", gap: 10, marginBottom: 0 },
  iconWrap: {
    width: 44, height: 44, borderRadius: 12,
    backgroundColor: "rgba(167,139,250,0.12)", borderWidth: 1,
    borderColor: "rgba(167,139,250,0.3)", alignItems: "center", justifyContent: "center", flexShrink: 0,
  },
  titleRow: { flexDirection: "row", alignItems: "center", gap: 8, marginBottom: 4 },
  title:    { color: "#c4b5fd", fontSize: 16, fontWeight: "800" },
  proBadge: {
    backgroundColor: "rgba(167,139,250,0.2)", borderWidth: 1,
    borderColor: "rgba(167,139,250,0.4)", borderRadius: 8,
    paddingVertical: 3, paddingHorizontal: 8,
  },
  proBadgeText: { color: "#a78bfa", fontSize: 9, fontWeight: "800" },
  subtitle: { color: "#4c1d95", fontSize: 11, lineHeight: 16, marginBottom: 5 },
  cta:      { color: "#a78bfa", fontSize: 12, fontWeight: "700" },
  starsRow: { flexDirection: "row", flexWrap: "wrap", gap: 5 },
  starChip: {
    backgroundColor: "rgba(167,139,250,0.07)", borderWidth: 1,
    borderColor: "rgba(167,139,250,0.18)", borderRadius: 20,
    paddingVertical: 3, paddingHorizontal: 8,
  },
  starText: { color: "#6d28d9", fontSize: 9, fontWeight: "600" },
});
