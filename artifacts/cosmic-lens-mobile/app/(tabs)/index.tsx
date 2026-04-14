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

function energyInsight(e: number) {
  if (e >= 75) return { icon: "🔥", text: "Strong positive energy", color: "#22c55e" };
  if (e >= 55) return { icon: "✨", text: "Moderate — stay focused", color: "#f59e0b" };
  if (e >= 35) return { icon: "⚠️", text: "Energy unstable today",  color: "#f97316" };
  return          { icon: "🌑", text: "Low energy — rest",          color: "#ef4444" };
}

function useOpacityPulse(min = 0.35, max = 1.0, dur = 1100) {
  const anim = useRef(new Animated.Value(min)).current;
  useEffect(() => {
    Animated.loop(Animated.sequence([
      Animated.timing(anim, { toValue: max, duration: dur, useNativeDriver: true }),
      Animated.timing(anim, { toValue: min, duration: dur, useNativeDriver: true }),
    ])).start();
  }, []);
  return anim;
}

// ── Mini bar chart (replaces the huge SVG chart) ──────────────────────────────
function MiniBarChart({ pts, color }: { pts: number[]; color: string }) {
  const max = Math.max(...pts, 1);
  return (
    <View style={{ flexDirection: "row", alignItems: "flex-end", gap: 3, height: 40 }}>
      {pts.map((v, i) => (
        <View
          key={i}
          style={{
            flex: 1,
            height: Math.max(4, (v / max) * 40),
            borderRadius: 3,
            backgroundColor: i === pts.length - 1 ? color : `${color}55`,
          }}
        />
      ))}
    </View>
  );
}

export default function HomeScreen() {
  const insets = useSafeAreaInsets();
  const colors = useColors();
  const { kundli, todayEnergy, setTodayEnergy, setMoonData, moonData, user, isLoading } = useUser();

  const [targetPts, setTargetPts] = useState<number[]>([]);
  const [labels,    setLabels]    = useState<string[]>([]);
  const [loading,   setLoading]   = useState(false);
  const cancelRef = useRef(false);

  useEffect(() => {
    if (!kundli) return;
    cancelRef.current = false;
    setLoading(true);
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
        setTargetPts(values);
        setLabels(data.points.map((pt, idx) => idx === data.points.length - 1 ? "Now" : pt.label));
        setLoading(false);
      })
      .catch(() => { if (!cancelRef.current) setLoading(false); });
    return () => { cancelRef.current = true; };
  }, [kundli]);

  if (!isLoading && !user) return <Redirect href="/login" />;

  const topPad = Platform.OS === "web" ? 67 : insets.top;
  const botPad = Platform.OS === "web" ? 34 : insets.bottom;

  const showDemo    = !kundli;
  const chartPts    = showDemo ? DEMO_PTS  : (targetPts.length ? targetPts : DEMO_PTS);
  const chartEnergy = showDemo ? 38 : (todayEnergy ?? 38);
  const insight     = energyInsight(chartEnergy);

  const activeDasha: ActiveDashaResult | null =
    kundli && moonData ? computeActiveDasha(kundli, moonData.longitude) : null;

  const dashaTxt = activeDasha
    ? `${activeDasha.mdPlanet}–${activeDasha.adPlanet} dasha active`
    : "Transit & dasha analysis";

  return (
    <ScrollView
      style={[S.root, { backgroundColor: colors.background }]}
      contentContainerStyle={[S.content, { paddingTop: topPad + 12, paddingBottom: botPad + 90 }]}
      showsVerticalScrollIndicator={false}
    >
      {/* ── Greeting row ── */}
      <View style={S.greetRow}>
        <View>
          <Text style={S.greetSub}>{kundli ? `Namaste, ${kundli.name}` : "Namaste"}</Text>
          <Text style={S.greetTitle}>Aaj ka Cosmic Report</Text>
        </View>
        <Pressable
          onPress={() => { Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light); router.push("/forecast"); }}
          style={S.forecastPill}
        >
          <Feather name="calendar" size={11} color="#00d4ff" />
          <Text style={S.forecastPillText}>7 Days</Text>
        </Pressable>
      </View>

      {/* ── HERO: Today Energy (compact) ── */}
      <View style={hero.card}>
        <View style={[hero.glow, { backgroundColor: `${insight.color}18` }]} />
        <View style={hero.topRow}>
          <View>
            <Text style={hero.label}>TODAY ENERGY</Text>
            <View style={{ flexDirection: "row", alignItems: "baseline", gap: 3, marginTop: 2 }}>
              <Text style={[hero.score, { color: insight.color }]}>{chartEnergy}</Text>
              <Text style={hero.scoreMax}>/100</Text>
            </View>
          </View>
          <View style={{ flex: 1, paddingLeft: 16, paddingTop: 4 }}>
            <MiniBarChart pts={chartPts} color={insight.color} />
          </View>
          {showDemo && (
            <View style={hero.demoBadge}>
              <Feather name="lock" size={8} color="#3d5a7a" />
              <Text style={hero.demoBadgeText}>DEMO</Text>
            </View>
          )}
        </View>
        <View style={[hero.insightPill, { backgroundColor: `${insight.color}12`, borderColor: `${insight.color}30` }]}>
          <Text style={{ fontSize: 12 }}>{insight.icon}</Text>
          <Text style={[hero.insightText, { color: insight.color }]}>{insight.text}</Text>
        </View>
      </View>

      {/* ── DOSH ANALYSIS (full-width, dominant) ── */}
      <DoshCard onPress={() => { Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium); router.push("/dosh"); }} kundli={kundli} />

      {/* ── 2×2 GRID ── */}
      <View style={S.grid}>
        {/* Hidden Issues */}
        <GridCard
          onPress={() => { Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light); router.push("/kundli"); }}
          color="#f59e0b"
          bg={["#1a1000","#1c1100"]}
          icon={<Feather name="alert-triangle" size={18} color="#f59e0b" />}
          title="Hidden Issues"
          subtitle="Weak planets & afflicted houses"
        />

        {/* Kundli Milan */}
        <GridCard
          onPress={() => { Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium); router.push("/kundli-milan"); }}
          color="#a78bfa"
          bg={["#130a2a","#1a0d38"]}
          icon={<Text style={{ fontSize: 18 }}>♥</Text>}
          title="Kundli Milan"
          subtitle="36-point marriage match"
          badge="PRO"
        />

        {/* Bad Time Alert */}
        <GridCard
          onPress={() => { Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light); router.push("/forecast"); }}
          color="#ef4444"
          bg={["#1f0400","#180300"]}
          icon={<Feather name="zap" size={18} color="#ef4444" />}
          title="Challenges Ahead"
          subtitle={dashaTxt}
          badge="ALERT"
          badgeColor="#ef4444"
        />

        {/* Planet Position */}
        <GridCard
          onPress={() => { Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light); router.push("/planet-position"); }}
          color="#f59e0b"
          bg={["#120900","#150b00"]}
          icon={<Feather name="target" size={18} color="#f59e0b" />}
          title="Planet Position"
          subtitle="Live graha degrees"
        />
      </View>
    </ScrollView>
  );
}

// ── Dosh Card (full-width, pulsing) ───────────────────────────────────────────
function DoshCard({ onPress, kundli }: { onPress: () => void; kundli: any }) {
  const glowOp = useOpacityPulse(0.3, 0.9, 950);
  return (
    <Pressable onPress={onPress} style={({ pressed }) => [{ opacity: pressed ? 0.9 : 1 }]}>
      <View style={dosh.outer}>
        <Animated.View style={[dosh.borderGlow, { opacity: glowOp }]} />
        <LinearGradient colors={["#1a0408","#200610","#180309"]} style={dosh.inner}>
          <View style={dosh.row}>
            <View style={dosh.iconWrap}>
              <Text style={{ fontSize: 22 }}>☿</Text>
            </View>
            <View style={{ flex: 1 }}>
              <View style={{ flexDirection: "row", alignItems: "center", gap: 7, marginBottom: 2 }}>
                <Text style={dosh.title}>⚠️ Dosh Analysis</Text>
                <View style={dosh.alertBadge}><Text style={dosh.alertText}>ALERT</Text></View>
              </View>
              <Text style={dosh.sub}>
                {kundli ? "Doshas detected — view remedies" : "Scan your kundli for doshas"}
              </Text>
            </View>
            <Feather name="chevron-right" size={16} color="#ef4444" style={{ opacity: 0.7 }} />
          </View>
          <View style={dosh.chips}>
            {["Kalsarp","Manglik","Pitra","Guru Chandal"].map(d => (
              <View key={d} style={dosh.chip}><Text style={dosh.chipText}>{d}</Text></View>
            ))}
          </View>
        </LinearGradient>
      </View>
    </Pressable>
  );
}

// ── Grid Card (compact 2-column) ──────────────────────────────────────────────
function GridCard({ onPress, color, bg, icon, title, subtitle, badge, badgeColor }: {
  onPress: () => void; color: string; bg: [string, string];
  icon: React.ReactNode; title: string; subtitle: string;
  badge?: string; badgeColor?: string;
}) {
  return (
    <Pressable onPress={onPress} style={({ pressed }) => [grid.card, pressed && { opacity: 0.82, transform: [{ scale: 0.97 }] }]}>
      <LinearGradient colors={bg} style={[grid.inner, { borderColor: `${color}28` }]}>
        <View style={[grid.iconWrap, { backgroundColor: `${color}12`, borderColor: `${color}25` }]}>
          {icon}
        </View>
        {badge && (
          <View style={[grid.badge, { backgroundColor: `${badgeColor ?? color}18`, borderColor: `${badgeColor ?? color}35` }]}>
            <Text style={[grid.badgeText, { color: badgeColor ?? color }]}>{badge}</Text>
          </View>
        )}
        <Text style={[grid.title, { color }]} numberOfLines={1}>{title}</Text>
        <Text style={grid.sub} numberOfLines={2}>{subtitle}</Text>
      </LinearGradient>
    </Pressable>
  );
}

// ── Styles ────────────────────────────────────────────────────────────────────
const S = StyleSheet.create({
  root:    { flex: 1 },
  content: { paddingHorizontal: 13, gap: 10 },

  greetRow: { flexDirection: "row", alignItems: "center", justifyContent: "space-between" },
  greetSub:   { color: "#3d5a7a", fontSize: 10, fontWeight: "600" },
  greetTitle: { color: "#dde8f4", fontSize: 16, fontWeight: "800", marginTop: 1 },

  forecastPill: {
    flexDirection: "row", alignItems: "center", gap: 5,
    backgroundColor: "rgba(0,212,255,0.07)", borderWidth: 1,
    borderColor: "rgba(0,212,255,0.22)", borderRadius: 20,
    paddingVertical: 6, paddingHorizontal: 10,
  },
  forecastPillText: { color: "#00d4ff", fontSize: 10, fontWeight: "700" },

  grid: { flexDirection: "row", flexWrap: "wrap", gap: 10 },
});

const hero = StyleSheet.create({
  card: {
    backgroundColor: "#040e1e", borderRadius: 16, borderWidth: 1,
    borderColor: "rgba(255,255,255,0.07)", padding: 12, overflow: "hidden",
    shadowColor: "#00d4ff", shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.08, shadowRadius: 16, elevation: 3,
  },
  glow: { position: "absolute", top: -30, right: -30, width: 120, height: 120, borderRadius: 60 },
  topRow: { flexDirection: "row", alignItems: "flex-end", marginBottom: 10 },
  label:    { color: "#3d5a7a", fontSize: 8, fontWeight: "800", letterSpacing: 1.8 },
  score:    { fontSize: 28, fontWeight: "900" },
  scoreMax: { color: "#1e3a5f", fontSize: 12, fontWeight: "600" },
  demoBadge: {
    flexDirection: "row", alignItems: "center", gap: 3,
    backgroundColor: "rgba(2,13,26,0.85)", borderWidth: 1,
    borderColor: "rgba(0,200,255,0.12)", paddingVertical: 3,
    paddingHorizontal: 6, borderRadius: 5, marginLeft: 8,
  },
  demoBadgeText: { color: "#3d5a7a", fontSize: 7, fontWeight: "800", letterSpacing: 1.2 },
  insightPill: {
    flexDirection: "row", alignItems: "center", gap: 6,
    borderWidth: 1, borderRadius: 8, paddingVertical: 6, paddingHorizontal: 10,
  },
  insightText: { fontSize: 11, fontWeight: "700" },
});

const dosh = StyleSheet.create({
  outer: {
    borderRadius: 16, overflow: "hidden",
    shadowColor: "#ef4444", shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.3, shadowRadius: 14, elevation: 7,
  },
  borderGlow: {
    position: "absolute", inset: 0, borderRadius: 16,
    borderWidth: 1.5, borderColor: "#ef4444", zIndex: 1,
  },
  inner:  { borderRadius: 16, padding: 12, gap: 8 },
  row:    { flexDirection: "row", alignItems: "center", gap: 10 },
  iconWrap: {
    width: 44, height: 44, borderRadius: 12,
    backgroundColor: "rgba(239,68,68,0.12)", borderWidth: 1,
    borderColor: "rgba(239,68,68,0.28)", alignItems: "center", justifyContent: "center", flexShrink: 0,
  },
  title:    { color: "#fca5a5", fontSize: 14, fontWeight: "800" },
  alertBadge: { backgroundColor: "#7f1d1d", borderRadius: 5, paddingHorizontal: 6, paddingVertical: 1 },
  alertText:  { color: "#fca5a5", fontSize: 7, fontWeight: "800", letterSpacing: 1 },
  sub:   { color: "#7f1d1d", fontSize: 11 },
  chips: { flexDirection: "row", gap: 5 },
  chip:  { backgroundColor: "rgba(239,68,68,0.09)", borderWidth: 1, borderColor: "rgba(239,68,68,0.22)", borderRadius: 20, paddingVertical: 3, paddingHorizontal: 9 },
  chipText: { color: "#f87171", fontSize: 9, fontWeight: "600" },
});

const grid = StyleSheet.create({
  card:  { width: "47.5%", borderRadius: 14, overflow: "hidden" },
  inner: {
    borderRadius: 14, padding: 11, gap: 5,
    borderWidth: 1, minHeight: 120,
  },
  iconWrap: {
    width: 36, height: 36, borderRadius: 10, borderWidth: 1,
    alignItems: "center", justifyContent: "center", marginBottom: 2,
  },
  badge: {
    position: "absolute", top: 8, right: 8,
    borderWidth: 1, borderRadius: 5, paddingHorizontal: 5, paddingVertical: 1,
  },
  badgeText: { fontSize: 7, fontWeight: "900", letterSpacing: 0.8 },
  title: { fontSize: 12, fontWeight: "800" },
  sub:   { color: "#475569", fontSize: 10, lineHeight: 14 },
});
