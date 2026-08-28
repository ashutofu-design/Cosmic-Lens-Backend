import { Feather } from "@expo/vector-icons";
import { router } from "expo-router";
import * as Haptics from "expo-haptics";
import React, { useEffect, useState } from "react";
import {
  Platform,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import {
  AshtakavargaTab,
  DashaTab,
  JaiminiTab,
  KPTab,
  NavataraTab,
  TransitTab,
  activeDashaIndex,
  getKundliLabels,
} from "./(tabs)/kundli";
import { DivisionalChartsPanel } from "@/components/DivisionalChartsPanel";
import { PlanetPositionCard } from "@/components/PlanetPositionCard";
import { FadeInView } from "@/components/motion/FadeInView";
import { ScalePressable } from "@/components/motion/ScalePressable";
import { D1_CHART_META } from "@/lib/divisionalVargaMeta";
import { useC } from "@/context/ThemeContext";
import { useUser } from "@/context/UserContext";
import { useT } from "@/hooks/useT";
import { SIGNS_EN, SIGNS_SHORT, signEnFromShort } from "@/lib/planetPositionUtils";

type PlanetView =
  | "positions"
  | "divisional"
  | "kundli"
  | "kp"
  | "ashtakavarga"
  | "navatara"
  | "jaimini"
  | "transit";

const F = {
  medium: "Nunito_500Medium",
  semibold: "Nunito_600SemiBold",
  bold: "Nunito_700Bold",
};

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

const TABS: { id: PlanetView; label: string; icon: keyof typeof Feather.glyphMap; accent: string }[] = [
  { id: "positions", label: "D1", icon: "target", accent: "#06b6d4" },
  { id: "divisional", label: "Divisional", icon: "grid", accent: "#7c3aed" },
  { id: "kundli", label: "Kundli", icon: "star", accent: "#f59e0b" },
  { id: "kp", label: "KP", icon: "crosshair", accent: "#0891b2" },
  { id: "ashtakavarga", label: "Ashtakavarga", icon: "grid", accent: "#22c55e" },
  { id: "navatara", label: "Navatara", icon: "compass", accent: "#a78bfa" },
  { id: "jaimini", label: "Jaimini", icon: "award", accent: "#ec4899" },
  { id: "transit", label: "Transit", icon: "navigation", accent: "#3b82f6" },
];

export default function PlanetPositionScreen() {
  const insets = useSafeAreaInsets();
  const C = useC();
  const t = useT();
  const L = getKundliLabels(t);
  const { kundli, profiles, primaryProfileId } = useUser();
  const primaryProfile = profiles.find((p) => p.id === primaryProfileId) ?? profiles[0] ?? null;
  const [view, setView] = useState<PlanetView>("positions");
  const [mahaIdx, setMahaIdx] = useState(0);
  const [antarIdx, setAntarIdx] = useState(0);
  const [pratIdx, setPratIdx] = useState(0);
  const topPad = Platform.OS === "web" ? 67 : insets.top;
  const botPad = Platform.OS === "web" ? 34 : insets.bottom;
  const showDemo = !kundli;
  const ac = C.isDark ? "#f59e0b" : "#7C3AED";

  const data = showDemo ? DEMO_KUNDLI : kundli;
  const rawPlanets = data?.planets ?? [];
  const planets = rawPlanets.map((p) => ({
    ...p,
    sign: p.sign ?? SIGNS_SHORT[Math.floor((p.longitude ?? 0) / 30) % 12],
    degrees:
      p.degrees ??
      `${Math.floor((p.longitude ?? 0) % 30)}°${Math.floor(((p.longitude ?? 0) % 1) * 60)}'`,
  }));
  const lagnaIdx = Math.floor(((data as { ascendantDeg?: number })?.ascendantDeg ?? 0) / 30) % 12;
  const lagnaSign = SIGNS_EN[lagnaIdx] ?? signEnFromShort(SIGNS_SHORT[lagnaIdx] ?? "");
  const sunLon = planets.find((p) => p.name === "Sun")?.longitude ?? 0;
  const canViewD1Chart = !showDemo && !!kundli;

  useEffect(() => {
    if (!kundli?.dashas?.length) return;
    const mi = activeDashaIndex(kundli.dashas);
    setMahaIdx(mi);
    const subs = kundli.dashas[mi]?.subDashas ?? [];
    const ai = activeDashaIndex(subs);
    setAntarIdx(ai);
  }, [kundli]);

  const snapshotRows = kundli
    ? [
        { label: L.snapAscendant, value: kundli.ascendant, icon: "sunrise" as const },
        { label: L.snapMoonSign, value: kundli.moonSign, icon: "moon" as const },
        ...(kundli.nakshatra
          ? [
              {
                label: L.snapNakshatra,
                value: `${kundli.nakshatra} (${L.padaLabel} ${kundli.nakshatraPada ?? "?"})`,
                icon: "star" as const,
              },
            ]
          : []),
        ...(kundli.nakshatraRuler
          ? [
              {
                label: L.snapNakshatraLord,
                value: kundli.nakshatraRuler,
                icon: "shield" as const,
              },
            ]
          : []),
      ]
    : [];

  const headerSub =
    view === "positions"
      ? `Lagna: ${lagnaSign}`
      : view === "divisional"
        ? t.mdDivisionalSub
        : view === "kundli"
          ? L.birthChartSnap
          : view === "kp"
            ? L.secKpPaddhati
            : view === "ashtakavarga"
              ? L.secAshtakavarga
              : view === "navatara"
                ? L.secNavatara9Tara
                : view === "jaimini"
                  ? L.secJaiminiKarakas
                  : L.secGrahaTransit;

  const needsRealKundli =
    view !== "positions" && view !== "divisional" && showDemo;

  return (
    <View style={[s.root, { paddingTop: topPad, backgroundColor: C.bg }]}>
      <View style={[s.header, { borderBottomColor: C.border }]}>
        <ScalePressable onPress={() => router.back()} style={s.back} haptic="light">
          <Feather name="arrow-left" size={20} color={C.textMid} />
        </ScalePressable>
        <View style={{ flex: 1 }}>
          <Text style={[s.headerTitle, { color: C.text }]}>{t.planetTitle}</Text>
          <Text style={[s.headerSub, { color: C.textMuted }]} numberOfLines={1}>
            {headerSub}
          </Text>
        </View>
        {showDemo && (
          <View style={s.demoPill}>
            <Text style={s.demoPillText}>Demo</Text>
          </View>
        )}
      </View>

      <FadeInView delay={40}>
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          style={{ borderBottomWidth: 1, borderBottomColor: C.border }}
          contentContainerStyle={s.tabRow}
        >
          {TABS.map((tab) => {
            const active = view === tab.id;
            const accent = tab.accent;
            return (
              <ScalePressable
                key={tab.id}
                onPress={() => {
                  setView(tab.id);
                  Haptics.selectionAsync();
                }}
                haptic="none"
                style={[
                  s.tab,
                  {
                    borderColor: active ? accent : C.border,
                    backgroundColor: active ? `${accent}1f` : C.bgCard,
                  },
                ]}
              >
                <Feather name={tab.icon} size={12} color={active ? accent : C.textMuted} />
                <Text
                  style={[s.tabLabel, { color: active ? accent : C.textMuted }]}
                  numberOfLines={1}
                >
                  {tab.label}
                </Text>
              </ScalePressable>
            );
          })}
        </ScrollView>
      </FadeInView>

      <ScrollView
        contentContainerStyle={[s.content, { paddingBottom: botPad + 30 }]}
        showsVerticalScrollIndicator={false}
      >
        <FadeInView key={view} delay={80} slide={10}>
          {needsRealKundli ? (
            <ScalePressable
              style={[s.demoBanner, { backgroundColor: C.warningBg, borderColor: C.warningBorder }]}
              onPress={() => router.push("/onboarding")}
              haptic="medium"
            >
              <Feather name="lock" size={12} color={C.warningText} />
              <Text style={[s.demoText, { color: C.warningText }]}>
                Apni kundli banao — yeh details real chart se aati hain
              </Text>
              <Feather name="chevron-right" size={12} color={C.warningText} />
            </ScalePressable>
          ) : null}

          {view === "positions" ? (
            <>
              {showDemo && (
                <ScalePressable
                  style={[s.demoBanner, { backgroundColor: C.warningBg, borderColor: C.warningBorder }]}
                  onPress={() => router.push("/onboarding")}
                  haptic="medium"
                >
                  <Feather name="lock" size={12} color={C.warningText} />
                  <Text style={[s.demoText, { color: C.warningText }]}>
                    Sample data — Apni kundli banao exact positions ke liye
                  </Text>
                  <Feather name="chevron-right" size={12} color={C.warningText} />
                </ScalePressable>
              )}

              <View style={[s.d1Bar, { backgroundColor: C.bgCard, borderColor: C.border }]}>
                <View style={{ flex: 1, gap: 4 }}>
                  <Text style={[s.d1Label, { color: C.textMuted }]}>{D1_CHART_META.label}</Text>
                  <Text style={[s.d1Hint, { color: "#06b6d4" }]}>{D1_CHART_META.hint}</Text>
                  <Text style={[s.d1Lagna, { color: C.text }]}>Lagna: {lagnaSign}</Text>
                </View>
                {canViewD1Chart && (
                  <ScalePressable
                    onPress={() => {
                      router.push({ pathname: "/varga-chart", params: { varga: "D1" } });
                    }}
                    haptic="medium"
                    style={[s.viewChartBtn, { borderColor: "#06b6d4", backgroundColor: "rgba(6,182,212,0.12)" }]}
                  >
                    <Feather name="grid" size={14} color="#06b6d4" />
                    <Text style={[s.viewChartTxt, { color: "#67e8f9" }]}>{t.viewChart}</Text>
                    <Feather name="chevron-right" size={14} color="#06b6d4" />
                  </ScalePressable>
                )}
              </View>

              {snapshotRows.length > 0 ? (
                <View
                  style={{
                    borderRadius: 18,
                    borderWidth: 1,
                    overflow: "hidden",
                    backgroundColor: C.bgCard,
                    borderColor: C.border,
                    marginTop: 4,
                    marginBottom: 8,
                  }}
                >
                  <View
                    style={{
                      backgroundColor: C.isDark ? "rgba(6,182,212,0.12)" : "rgba(6,182,212,0.1)",
                      paddingVertical: 10,
                      paddingHorizontal: 16,
                      borderBottomWidth: 1,
                      borderBottomColor: C.border,
                      flexDirection: "row",
                      alignItems: "center",
                      gap: 8,
                    }}
                  >
                    <Feather name="book-open" size={13} color="#06b6d4" />
                    <Text style={{ color: "#06b6d4", fontSize: 11, fontFamily: F.bold, letterSpacing: 1 }}>
                      {L.birthChartSnap}
                    </Text>
                  </View>
                  {snapshotRows.map(({ label, value, icon }, idx) => (
                    <View
                      key={label}
                      style={{
                        flexDirection: "row",
                        alignItems: "center",
                        paddingVertical: 10,
                        paddingHorizontal: 14,
                        gap: 10,
                        backgroundColor:
                          idx % 2 === 0
                            ? "transparent"
                            : C.isDark
                              ? "rgba(6,182,212,0.05)"
                              : "rgba(6,182,212,0.06)",
                        borderBottomWidth: idx < snapshotRows.length - 1 ? 1 : 0,
                        borderBottomColor: C.border,
                      }}
                    >
                      <Feather name={icon} size={12} color={C.textMid} />
                      <Text
                        style={{
                          color: C.textMid,
                          fontSize: 10,
                          fontFamily: F.bold,
                          letterSpacing: 0.5,
                          flex: 1,
                        }}
                      >
                        {label}
                      </Text>
                      <Text style={{ color: C.text, fontSize: 13, fontFamily: F.semibold }} numberOfLines={1}>
                        {value}
                      </Text>
                    </View>
                  ))}
                </View>
              ) : null}

              {kundli?.dashas?.length ? (
                <View style={{ gap: 10, marginTop: 4, marginBottom: 8 }}>
                  <View style={{ flexDirection: "row", alignItems: "center", gap: 8 }}>
                    <Feather name="clock" size={13} color="#06b6d4" />
                    <Text
                      style={{
                        color: "#06b6d4",
                        fontSize: 12,
                        fontFamily: F.bold,
                        letterSpacing: 2,
                        flex: 1,
                      }}
                    >
                      {L.secDashaTimeline}
                    </Text>
                  </View>
                  <DashaTab
                    kundli={kundli}
                    mahaIdx={mahaIdx}
                    setMahaIdx={setMahaIdx}
                    antarIdx={antarIdx}
                    setAntarIdx={setAntarIdx}
                    pratIdx={pratIdx}
                    setPratIdx={setPratIdx}
                  />
                </View>
              ) : null}

              {planets.map((p) => (
                <PlanetPositionCard key={p.name} planet={p} sunLon={sunLon} mode="d1" />
              ))}

              <View style={[s.legend, { backgroundColor: C.bgCard, borderColor: C.border }]}>
                {[
                  { label: "Kendra", color: "#4ade80", desc: "Houses 1,4,7,10" },
                  { label: "Trikona", color: "#f59e0b", desc: "Houses 5,9" },
                  { label: "Dusthana", color: "#ef4444", desc: "Houses 6,8,12" },
                  { label: "Madhyam", color: "#fbbf24", desc: "Others" },
                ].map((l) => (
                  <View key={l.label} style={s.legendItem}>
                    <View style={[s.legendDot, { backgroundColor: l.color }]} />
                    <Text style={[s.legendLabel, { color: C.textMuted }]}>{l.label}</Text>
                    <Text style={[s.legendDesc, { color: C.textMid }]}>{l.desc}</Text>
                  </View>
                ))}
              </View>
            </>
          ) : null}

          {view === "divisional" ? <DivisionalChartsPanel showKundliLink={false} /> : null}

          {view === "kundli" && kundli ? (
            <View style={{ gap: 16 }}>
              <View
                style={{
                  borderRadius: 18,
                  borderWidth: 1,
                  overflow: "hidden",
                  backgroundColor: C.bgCard,
                  borderColor: C.border,
                }}
              >
                <View
                  style={{
                    backgroundColor: C.isDark ? "rgba(245,158,11,0.12)" : "rgba(124,58,237,0.12)",
                    paddingVertical: 10,
                    paddingHorizontal: 16,
                    borderBottomWidth: 1,
                    borderBottomColor: C.border,
                    flexDirection: "row",
                    alignItems: "center",
                    gap: 8,
                  }}
                >
                  <Feather name="book-open" size={13} color={ac} />
                  <Text style={{ color: ac, fontSize: 11, fontFamily: F.bold, letterSpacing: 1 }}>
                    {L.birthChartSnap}
                  </Text>
                </View>
                {snapshotRows.map(({ label, value, icon }, idx) => (
                  <View
                    key={label}
                    style={{
                      flexDirection: "row",
                      alignItems: "center",
                      paddingVertical: 10,
                      paddingHorizontal: 14,
                      gap: 10,
                      backgroundColor:
                        idx % 2 === 0
                          ? "transparent"
                          : C.isDark
                            ? "rgba(245,158,11,0.05)"
                            : "rgba(124,58,237,0.05)",
                      borderBottomWidth: idx < snapshotRows.length - 1 ? 1 : 0,
                      borderBottomColor: C.border,
                    }}
                  >
                    <Feather name={icon} size={12} color={C.textMid} />
                    <Text
                      style={{
                        color: C.textMid,
                        fontSize: 10,
                        fontFamily: F.bold,
                        letterSpacing: 0.5,
                        flex: 1,
                      }}
                    >
                      {label}
                    </Text>
                    <Text style={{ color: C.text, fontSize: 13, fontFamily: F.semibold }} numberOfLines={1}>
                      {value}
                    </Text>
                  </View>
                ))}
              </View>

              <Text
                style={{
                  color: ac,
                  fontSize: 12,
                  fontFamily: F.bold,
                  letterSpacing: 2,
                }}
              >
                {L.secDashaTimeline}
              </Text>
              <DashaTab
                kundli={kundli}
                mahaIdx={mahaIdx}
                setMahaIdx={setMahaIdx}
                antarIdx={antarIdx}
                setAntarIdx={setAntarIdx}
                pratIdx={pratIdx}
                setPratIdx={setPratIdx}
              />
            </View>
          ) : null}

          {view === "kp" && kundli ? <KPTab kundli={kundli} /> : null}
          {view === "ashtakavarga" && kundli ? <AshtakavargaTab kundli={kundli} /> : null}
          {view === "navatara" && kundli ? <NavataraTab kundli={kundli} /> : null}
          {view === "jaimini" && kundli ? <JaiminiTab kundli={kundli} /> : null}
          {view === "transit" && kundli ? (
            <TransitTab
              kundli={kundli}
              lat={primaryProfile?.birthData?.lat}
              lng={primaryProfile?.birthData?.lon}
              tz={primaryProfile?.birthData?.tz}
              active={view === "transit"}
            />
          ) : null}
        </FadeInView>
      </ScrollView>
    </View>
  );
}

const s = StyleSheet.create({
  root: { flex: 1, backgroundColor: "#020d1a" },
  header: {
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: 16,
    paddingBottom: 12,
    paddingTop: 12,
    gap: 10,
    borderBottomWidth: 1,
    borderBottomColor: "rgba(255,255,255,0.04)",
  },
  back: { padding: 4 },
  headerTitle: { color: "#dde8f4", fontSize: 18, fontWeight: "700" },
  headerSub: { color: "#3d5a7a", fontSize: 11 },
  demoPill: {
    backgroundColor: "rgba(251,191,36,0.15)",
    borderRadius: 10,
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderWidth: 1,
    borderColor: "rgba(251,191,36,0.3)",
  },
  demoPillText: { color: "#fbbf24", fontSize: 10, fontWeight: "600" },
  tabRow: {
    flexDirection: "row",
    gap: 8,
    paddingHorizontal: 12,
    paddingVertical: 10,
  },
  tab: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 10,
    borderWidth: 1.5,
  },
  tabLabel: { fontSize: 12, fontFamily: "Nunito_700Bold" },
  content: { paddingHorizontal: 16, paddingTop: 14, gap: 12 },
  demoBanner: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    padding: 12,
    borderRadius: 12,
    borderWidth: 1,
    marginBottom: 4,
  },
  demoText: { flex: 1, fontSize: 12, fontFamily: "Nunito_600SemiBold" },
  d1Bar: {
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
    padding: 14,
    borderRadius: 14,
    borderWidth: 1,
  },
  d1Label: { fontSize: 11, fontFamily: "Nunito_700Bold", letterSpacing: 0.5 },
  d1Hint: { fontSize: 12, fontFamily: "Nunito_600SemiBold" },
  d1Lagna: { fontSize: 14, fontFamily: "Nunito_700Bold", marginTop: 2 },
  viewChartBtn: {
    flexDirection: "row",
    alignItems: "center",
    gap: 4,
    paddingVertical: 8,
    paddingHorizontal: 10,
    borderRadius: 10,
    borderWidth: 1,
  },
  viewChartTxt: { fontSize: 12, fontFamily: "Nunito_700Bold" },
  legend: {
    borderRadius: 14,
    borderWidth: 1,
    padding: 14,
    gap: 8,
    marginTop: 4,
  },
  legendItem: { flexDirection: "row", alignItems: "center", gap: 8 },
  legendDot: { width: 8, height: 8, borderRadius: 4 },
  legendLabel: { fontSize: 11, fontFamily: "Nunito_700Bold", width: 64 },
  legendDesc: { fontSize: 11, fontFamily: "Nunito_500Medium", flex: 1 },
});
