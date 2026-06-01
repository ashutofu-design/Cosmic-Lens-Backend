import { Feather } from "@expo/vector-icons";
import { router } from "expo-router";
import * as Haptics from "expo-haptics";
import React, { useState } from "react";
import {
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { FadeInView } from "@/components/motion/FadeInView";
import { DivisionalChartsPanel } from "@/components/DivisionalChartsPanel";
import { PlanetPositionCard } from "@/components/PlanetPositionCard";
import { useC } from "@/context/ThemeContext";
import { useUser } from "@/context/UserContext";
import { useT } from "@/hooks/useT";
import { SIGNS, SIGNS_SHORT } from "@/lib/planetPositionUtils";

type PlanetView = "positions" | "divisional";

const DEMO_KUNDLI = {
  planets: [
    { name: "Sun", sign: "Tula", degrees: "12°34'", house: 1, longitude: 192.57, retrograde: false, speed: 1.01 },
    { name: "Moon", sign: "Makar", degrees: "5°18'", house: 4, longitude: 275.3, retrograde: false, speed: 13.2 },
    { name: "Mars", sign: "Simha", degrees: "20°10'", house: 11, longitude: 140.17, retrograde: false, speed: 0.52 },
    { name: "Mercury", sign: "Tula", degrees: "3°45'", house: 1, longitude: 183.75, retrograde: true, speed: -0.3 },
    { name: "Jupiter", sign: "Meen", degrees: "15°22'", house: 6, longitude: 345.37, retrograde: false, speed: 0.07 },
    { name: "Venus", sign: "Kanya", degrees: "8°50'", house: 12, longitude: 158.83, retrograde: false, speed: 1.22 },
    { name: "Saturn", sign: "Kumbh", degrees: "2°30'", house: 5, longitude: 302.5, retrograde: true, speed: -0.06 },
    { name: "Rahu", sign: "Vrishabh", degrees: "18°0'", house: 8, longitude: 48.0, retrograde: true, speed: -0.05 },
    { name: "Ketu", sign: "Vrishchik", degrees: "18°0'", house: 2, longitude: 228.0, retrograde: true, speed: -0.05 },
  ],
  ascendantDeg: 192.0,
  rashi: "Tula",
};

export default function PlanetPositionScreen() {
  const insets = useSafeAreaInsets();
  const C = useC();
  const t = useT();
  const { kundli } = useUser();
  const [view, setView] = useState<PlanetView>("positions");
  const topPad = Platform.OS === "web" ? 67 : insets.top;
  const botPad = Platform.OS === "web" ? 34 : insets.bottom;
  const showDemo = !kundli;

  const data = showDemo ? DEMO_KUNDLI : kundli;
  const rawPlanets = data?.planets ?? [];
  const planets = rawPlanets.map(p => ({
    ...p,
    sign: p.sign ?? SIGNS_SHORT[Math.floor((p.longitude ?? 0) / 30) % 12],
    degrees: p.degrees ?? `${Math.floor((p.longitude ?? 0) % 30)}°${Math.floor(((p.longitude ?? 0) % 1) * 60)}'`,
  }));
  const lagnaIdx = Math.floor(((data as { ascendantDeg?: number })?.ascendantDeg ?? 0) / 30) % 12;
  const lagnaSign = SIGNS[lagnaIdx];
  const sunLon = planets.find(p => p.name === "Sun")?.longitude ?? 0;

  return (
    <View style={[s.root, { paddingTop: topPad, backgroundColor: C.bg }]}>
      <View style={[s.header, { borderBottomColor: C.border }]}>
        <Pressable onPress={() => router.back()} style={s.back}>
          <Feather name="arrow-left" size={20} color={C.textMid} />
        </Pressable>
        <View style={{ flex: 1 }}>
          <Text style={[s.headerTitle, { color: C.text }]}>{t.planetTitle}</Text>
          <Text style={[s.headerSub, { color: C.textMuted }]}>
            {view === "positions" ? `Lagna: ${lagnaSign}` : t.mdDivisionalSub}
          </Text>
        </View>
        {showDemo && (
          <View style={s.demoPill}>
            <Text style={s.demoPillText}>Demo</Text>
          </View>
        )}
      </View>

      <FadeInView delay={40}>
      <View style={[s.tabRow, { borderBottomColor: C.border }]}>
        {([
          { id: "positions" as const, label: t.ku_planetPosition, icon: "target" as const },
          { id: "divisional" as const, label: t.mdDivisionalTitle, icon: "grid" as const },
        ]).map(tab => {
          const active = view === tab.id;
          return (
            <Pressable
              key={tab.id}
              onPress={() => { setView(tab.id); Haptics.selectionAsync(); }}
              style={[
                s.tab,
                { borderColor: active ? "#06b6d4" : C.border, backgroundColor: active ? "rgba(6,182,212,0.12)" : C.bgCard },
              ]}
            >
              <Feather name={tab.icon} size={12} color={active ? "#06b6d4" : C.textMuted} />
              <Text style={[s.tabLabel, { color: active ? "#06b6d4" : C.textMuted }]}>{tab.label}</Text>
            </Pressable>
          );
        })}
      </View>
      </FadeInView>

      <ScrollView contentContainerStyle={[s.content, { paddingBottom: botPad + 30 }]} showsVerticalScrollIndicator={false}>
        <FadeInView key={view} delay={80} slide={10}>
        {view === "positions" ? (
          <>
            {showDemo && (
              <Pressable style={[s.demoBanner, { backgroundColor: C.warningBg, borderColor: C.warningBorder }]} onPress={() => router.push("/onboarding")}>
                <Feather name="lock" size={12} color={C.warningText} />
                <Text style={[s.demoText, { color: C.warningText }]}>Sample data — Apni kundli banao exact positions ke liye</Text>
                <Feather name="chevron-right" size={12} color={C.warningText} />
              </Pressable>
            )}

            {planets.map(p => (
              <PlanetPositionCard key={p.name} planet={p} sunLon={sunLon} mode="d1" />
            ))}

            <View style={[s.legend, { backgroundColor: C.bgCard, borderColor: C.border }]}>
              {[
                { label: "Kendra", color: "#4ade80", desc: "Houses 1,4,7,10" },
                { label: "Trikona", color: "#f59e0b", desc: "Houses 5,9" },
                { label: "Dusthana", color: "#ef4444", desc: "Houses 6,8,12" },
                { label: "Madhyam", color: "#fbbf24", desc: "Others" },
              ].map(l => (
                <View key={l.label} style={s.legendItem}>
                  <View style={[s.legendDot, { backgroundColor: l.color }]} />
                  <Text style={[s.legendLabel, { color: C.textMuted }]}>{l.label}</Text>
                  <Text style={[s.legendDesc, { color: C.textMid }]}>{l.desc}</Text>
                </View>
              ))}
            </View>
          </>
        ) : (
          <DivisionalChartsPanel showKundliLink={false} />
        )}
        </FadeInView>
      </ScrollView>
    </View>
  );
}

const s = StyleSheet.create({
  root: { flex: 1, backgroundColor: "#020d1a" },
  header: {
    flexDirection: "row", alignItems: "center",
    paddingHorizontal: 16, paddingBottom: 12, paddingTop: 12, gap: 10,
    borderBottomWidth: 1, borderBottomColor: "rgba(255,255,255,0.04)",
  },
  back: { padding: 4 },
  headerTitle: { color: "#dde8f4", fontSize: 18, fontWeight: "700" },
  headerSub: { color: "#3d5a7a", fontSize: 11 },
  demoPill: {
    backgroundColor: "rgba(251,191,36,0.15)", borderRadius: 10,
    paddingHorizontal: 8, paddingVertical: 2, borderWidth: 1, borderColor: "rgba(251,191,36,0.3)",
  },
  demoPillText: { color: "#fbbf24", fontSize: 10, fontWeight: "600" },
  tabRow: {
    flexDirection: "row", gap: 8, paddingHorizontal: 16, paddingBottom: 12,
  },
  tab: {
    flex: 1, flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 6,
    paddingVertical: 10, borderRadius: 12, borderWidth: 1,
  },
  tabLabel: { fontSize: 11, fontWeight: "700" },
  content: { padding: 16, gap: 12 },
  demoBanner: {
    flexDirection: "row", alignItems: "center", gap: 8,
    backgroundColor: "rgba(251,191,36,0.07)", borderRadius: 12,
    borderWidth: 1, borderColor: "rgba(251,191,36,0.2)",
    paddingHorizontal: 14, paddingVertical: 10,
  },
  demoText: { color: "#fbbf24", fontSize: 11, flex: 1 },
  legend: {
    backgroundColor: "#040e1f", borderRadius: 14,
    borderWidth: 1, borderColor: "rgba(255,255,255,0.04)",
    padding: 14, gap: 8,
  },
  legendItem: { flexDirection: "row", alignItems: "center", gap: 8 },
  legendDot: { width: 8, height: 8, borderRadius: 4 },
  legendLabel: { color: "#94a3b8", fontSize: 12, width: 70, fontWeight: "600" },
  legendDesc: { color: "#3d5a7a", fontSize: 11 },
});
