import { Feather } from "@expo/vector-icons";
import { LinearGradient } from "expo-linear-gradient";
import * as Haptics from "expo-haptics";
import { Redirect, router } from "expo-router";
import React, { useEffect, useRef, useState } from "react";
import {
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
import { computeActiveDasha, pName, type ActiveDashaResult } from "@/lib/proInsightEngine";
import type { MoonHistoryPoint } from "@/types";

const N = 12;

// Demo sample energy points for no-kundli state
const DEMO_PTS = [42, 55, 38, 61, 70, 65, 48, 72, 68, 54, 60, 63];
const DEMO_LABELS = ["10PM","","","1AM","","","4AM","","","7AM","","Now"];

const BASE_URL = process.env.EXPO_PUBLIC_DOMAIN
  ? `https://${process.env.EXPO_PUBLIC_DOMAIN}`
  : "";

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

  // Auth gate — all hooks declared above this point
  if (!isLoading && !user) {
    return <Redirect href="/login" />;
  }

  const topPad = Platform.OS === "web" ? 67 : insets.top;
  const botPad = Platform.OS === "web" ? 34 : insets.bottom;

  // Active dasha (only when kundli + moon data available)
  const activeDasha: ActiveDashaResult | null =
    kundli && moonData ? computeActiveDasha(kundli, moonData.longitude) : null;

  // Decide which chart data to show
  const showDemo   = !kundli;
  const chartPts   = showDemo ? DEMO_PTS   : targetPts;
  const chartLbls  = showDemo ? DEMO_LABELS : labels;
  const chartEnergy = showDemo ? 63 : todayEnergy;

  return (
    <ScrollView
      style={[styles.root, { backgroundColor: colors.background }]}
      contentContainerStyle={[
        styles.content,
        { paddingTop: topPad + 20, paddingBottom: botPad + 100 },
      ]}
      showsVerticalScrollIndicator={false}
    >
      {/* Welcome */}
      <Text style={[styles.welcome, { color: colors.textSub }]}>
        {kundli
          ? <>Hello, <Text style={{ color: "#cbd5e1", fontWeight: "600" }}>{kundli.name}</Text></>
          : "Hello — Set Up Your Kundli"}
      </Text>

      {/* ── Energy Chart (real or demo) ── */}
      <View style={styles.chartWrap}>
        {showDemo && (
          <View style={[styles.demoOverlay, { pointerEvents: "none" }]}>
            <View style={styles.demoBadge}>
              <Feather name="lock" size={10} color="#3d5a7a" />
              <Text style={styles.demoBadgeText}>DEMO PREVIEW</Text>
            </View>
          </View>
        )}
        <EnergyChart
          targetPts={chartPts}
          labels={chartLbls}
          finalEnergy={chartEnergy}
          loading={!showDemo && loading && targetPts.length === 0}
          instant={showDemo}
        />
      </View>

      {/* Subtitle */}
      <Text style={[styles.subtitle, { color: colors.textDim }]}>
        {!showDemo && settled
          ? "Birth chart · Navatara · Ashtakavarga"
          : !showDemo && loading
          ? "Reading cosmic signals..."
          : "Birth chart · Navatara · Ashtakavarga"}
      </Text>

      {/* ── Action buttons ── */}
      <View style={styles.btnRow}>
        <ActionCard
          label="7 Days Forecast"
          icon="calendar"
          accent="#00d4ff"
          bg="#040e20"
          border="rgba(0,200,255,0.25)"
          locked={false}
          onPress={() => { Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light); router.push("/forecast"); }}
        />
        <ActionCard
          label="Planet Position"
          icon="target"
          accent="#f59e0b"
          bg="#120900"
          border="rgba(251,191,36,0.3)"
          locked={false}
          onPress={() => { Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light); router.push("/planet-position"); }}
        />
      </View>

      {/* ── Cosmic Tools ── */}
      <View style={styles.toolsWrap}>
        <Text style={styles.toolsLabel}>COSMIC TOOLS</Text>
        <ToolCard
          emoji="🔴"
          title="Dosh Analysis"
          titleHindi="ग्रह दोष विश्लेषण"
          desc="Kalsarp, Manglik, Pitra, Guru Chandal — all doshas in one place"
          accent="#ef4444"
          bg="rgba(239,68,68,0.05)"
          border="rgba(239,68,68,0.2)"
          onPress={() => { Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light); router.push("/dosh"); }}
        />
        <ToolCard
          emoji="♥"
          title="Kundli Milan"
          titleHindi="अष्टकूट गुण मिलान"
          desc="36-point compatibility check for marriage matching"
          accent="#a78bfa"
          bg="rgba(167,139,250,0.05)"
          border="rgba(167,139,250,0.22)"
          onPress={() => { Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light); router.push("/kundli-milan"); }}
        />
        <ToolCard
          emoji="🏠"
          title="Vastu Shastra"
          titleHindi="वास्तु शास्त्र"
          desc="Vastu tips and remedies for every room in your home"
          accent="#34d399"
          bg="rgba(52,211,153,0.05)"
          border="rgba(52,211,153,0.2)"
          onPress={() => { Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light); router.push("/vastu"); }}
        />
      </View>

      {/* ── Active Dasha card (real data only) ── */}
      {activeDasha && (
        <ActiveDashaCard dasha={activeDasha} onPress={() => {}} />
      )}
    </ScrollView>
  );
}

// ── Tool Card ─────────────────────────────────────────────────────────────────
function ToolCard({
  emoji, title, titleHindi, desc, accent, bg, border, onPress,
}: {
  emoji: string; title: string; titleHindi: string; desc: string;
  accent: string; bg: string; border: string; onPress: () => void;
}) {
  return (
    <Pressable
      onPress={onPress}
      style={({ pressed }) => [
        styles.toolCard,
        { backgroundColor: bg, borderColor: border },
        pressed && { opacity: 0.75, transform: [{ scale: 0.98 }] },
      ]}
    >
      <View style={[styles.toolEmoji, { backgroundColor: `${accent}12` }]}>
        <Text style={{ fontSize: 20 }}>{emoji}</Text>
      </View>
      <View style={{ flex: 1 }}>
        <Text style={[styles.toolTitle, { color: accent }]}>{title}</Text>
        <Text style={styles.toolHindi}>{titleHindi}</Text>
        <Text style={styles.toolDesc} numberOfLines={2}>{desc}</Text>
      </View>
      <View style={[styles.toolArrow, { backgroundColor: `${accent}15`, borderColor: `${accent}25` }]}>
        <Feather name="chevron-right" size={14} color={accent} />
      </View>
    </Pressable>
  );
}

// ── Action Card ──────────────────────────────────────────────────────────────
function ActionCard({
  label, icon, accent, bg, border, locked, onPress,
}: {
  label: string; icon: string; accent: string;
  bg: string; border: string; locked?: boolean; onPress: () => void;
}) {
  return (
    <Pressable
      onPress={onPress}
      style={({ pressed }) => [
        styles.actionCard,
        { backgroundColor: bg, borderColor: border, opacity: locked ? 0.45 : 1 },
        pressed && !locked && { opacity: 0.75, transform: [{ scale: 0.97 }] },
      ]}
    >
      <Feather name={icon as any} size={18} color={accent} />
      <Text style={[styles.actionLabel, { color: accent }]}>
        {label.toUpperCase()}
      </Text>
      {locked && (
        <Feather name="lock" size={10} color={accent} style={{ opacity: 0.6 }} />
      )}
    </Pressable>
  );
}

// ── Active Dasha Card ────────────────────────────────────────────────────────
function ActiveDashaCard({ dasha, onPress }: { dasha: ActiveDashaResult; onPress: () => void }) {
  const trend  = dasha.careerTrend;
  const tColor = trend === "UP" ? "#22c55e" : trend === "DOWN" ? "#ef4444" : "#f59e0b";
  const tIcon  = trend === "UP" ? "↑" : trend === "DOWN" ? "↓" : "~";
  const tLabel = trend === "UP" ? "Growth" : trend === "DOWN" ? "Decline" : "Mixed";

  return (
    <Pressable
      onPress={onPress}
      style={({ pressed }) => [styles.dashaCard, pressed && { opacity: 0.85 }]}
    >
      <View style={styles.dashaTop}>
        <View style={{ flex: 1 }}>
          <Text style={styles.dashaTitle}>ACTIVE DASHA</Text>
          <View style={styles.dashaPlanets}>
            {[
              { lbl: "MD", planet: dasha.mdPlanet, color: "#4b6a86" },
              { lbl: "AD", planet: dasha.adPlanet, color: "#7c6ed4" },
              { lbl: "PD", planet: dasha.pdPlanet, color: "#00d4ff" },
            ].map(({ lbl, planet, color }, i) => (
              <React.Fragment key={lbl}>
                <View style={styles.dashaPlItem}>
                  <Text style={styles.dashaPlLabel}>{lbl}</Text>
                  <Text style={[
                    styles.dashaPlName, { color },
                    lbl === "PD" && {
                      textShadowColor: `${color}66`,
                      textShadowOffset: { width: 0, height: 0 },
                      textShadowRadius: 8,
                    },
                  ]}>
                    {pName(planet)}
                  </Text>
                </View>
                {i < 2 && <Text style={styles.dashaSep}>→</Text>}
              </React.Fragment>
            ))}
          </View>
        </View>
        <View style={styles.trendWrap}>
          <View style={[styles.trendCircle, {
            backgroundColor: `${tColor}14`,
            borderColor: `${tColor}44`,
            shadowColor: tColor,
          }]}>
            <Text style={[styles.trendIcon, { color: tColor }]}>{tIcon}</Text>
          </View>
          <Text style={[styles.trendLabel, { color: `${tColor}aa` }]}>{tLabel}</Text>
        </View>
      </View>
      <View style={styles.dashaFooter}>
        <Text style={styles.dashaFooterText}>Full Insights</Text>
        <Text style={styles.dashaFooterArrow}>→</Text>
      </View>
    </Pressable>
  );
}

// ── Styles ───────────────────────────────────────────────────────────────────
const styles = StyleSheet.create({
  root:    { flex: 1 },
  content: { paddingHorizontal: 16, alignItems: "center" },

  welcome: { fontSize: 12, marginBottom: 10, alignSelf: "flex-start" },

  chartWrap: { width: "100%", maxWidth: 380, marginBottom: 10, position: "relative" },

  demoOverlay: {
    position: "absolute", top: 10, right: 12, zIndex: 10,
  },
  demoBadge: {
    flexDirection: "row", alignItems: "center", gap: 4,
    backgroundColor: "rgba(2,13,26,0.85)",
    borderWidth: 1, borderColor: "rgba(0,200,255,0.15)",
    paddingVertical: 4, paddingHorizontal: 8, borderRadius: 6,
  },
  demoBadgeText: { color: "#3d5a7a", fontSize: 7, fontWeight: "800", letterSpacing: 1.5 },

  subtitle: {
    fontSize: 9, letterSpacing: 1.6, textTransform: "uppercase",
    marginBottom: 16, lineHeight: 16, textAlign: "center",
  },

  btnRow: { width: "100%", maxWidth: 380, flexDirection: "row", gap: 10, marginBottom: 14 },

  // ── Cosmic Tools ─────────────────────────────────────────────────────────
  toolsWrap:  { width: "100%", maxWidth: 380, gap: 10, marginBottom: 16 },
  toolsLabel: { fontSize: 9, fontWeight: "800", letterSpacing: 2.5, color: "#334155", marginBottom: 2 },
  toolCard: {
    flexDirection: "row", alignItems: "center", gap: 12,
    borderRadius: 14, borderWidth: 1, padding: 12,
  },
  toolEmoji: { width: 44, height: 44, borderRadius: 12, alignItems: "center", justifyContent: "center", flexShrink: 0 },
  toolTitle: { fontSize: 13, fontWeight: "700" },
  toolHindi: { color: "#1e3a5f", fontSize: 9, marginTop: 1, marginBottom: 3 },
  toolDesc:  { color: "#334155", fontSize: 11, lineHeight: 16 },
  toolArrow: { width: 30, height: 30, borderRadius: 15, borderWidth: 1, alignItems: "center", justifyContent: "center", flexShrink: 0 },
  actionCard: {
    flex: 1, paddingVertical: 14, paddingHorizontal: 8,
    borderRadius: 14, borderWidth: 1,
    alignItems: "center", justifyContent: "center", gap: 6,
  },
  actionLabel: { fontSize: 10, fontWeight: "700", letterSpacing: 1, textAlign: "center" },

  // ── Active Dasha ──────────────────────────────────────────────────────────
  dashaCard: {
    width: "100%", maxWidth: 380,
    backgroundColor: "#040d1e",
    borderRadius: 16, borderWidth: 1, borderColor: "rgba(0,212,255,0.15)",
    padding: 14, marginBottom: 16,
    shadowColor: "#006ec8", shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.12, shadowRadius: 20, elevation: 4,
  },
  dashaTop:     { flexDirection: "row", alignItems: "flex-start", marginBottom: 10 },
  dashaTitle:   { color: "#3d5a7a", fontSize: 8, fontWeight: "800", letterSpacing: 2, textTransform: "uppercase", marginBottom: 8 },
  dashaPlanets: { flexDirection: "row", alignItems: "center", gap: 8 },
  dashaPlItem:  { alignItems: "center" },
  dashaPlLabel: { color: "#1e3a5f", fontSize: 7, fontWeight: "700", letterSpacing: 0.8, marginBottom: 2 },
  dashaPlName:  { fontSize: 13, fontWeight: "700" },
  dashaSep:     { color: "#1e3a5f", fontSize: 10, marginBottom: 2 },
  trendWrap:    { alignItems: "center", gap: 3 },
  trendCircle:  {
    width: 40, height: 40, borderRadius: 20, borderWidth: 2,
    alignItems: "center", justifyContent: "center",
    shadowOffset: { width: 0, height: 0 }, shadowOpacity: 0.22, shadowRadius: 10, elevation: 3,
  },
  trendIcon:   { fontSize: 18, fontWeight: "900" },
  trendLabel:  { fontSize: 8, fontWeight: "700" },
  dashaFooter: { flexDirection: "row", justifyContent: "flex-end", alignItems: "center", gap: 4 },
  dashaFooterText:  { color: "rgba(0,212,255,0.27)", fontSize: 9, letterSpacing: 0.5 },
  dashaFooterArrow: { color: "rgba(0,212,255,0.27)", fontSize: 11 },

});
