import { Feather } from "@expo/vector-icons";
import { LinearGradient } from "expo-linear-gradient";
import { router, useLocalSearchParams } from "expo-router";
import React from "react";
import {
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
import { useUser } from "@/context/UserContext";
import { useColors } from "@/hooks/useColors";
import { buildPersonalSnapshot, type KundliCategoryScore } from "@/lib/personalizationSnapshot";

function scoreColor(score: number): string {
  if (score >= 70) return "#22c55e";
  if (score >= 50) return "#f59e0b";
  return "#ef4444";
}

export default function KundliCategoryDetailScreen() {
  const insets = useSafeAreaInsets();
  const { C } = useColors();
  const { kundli, language } = useUser();
  const params = useLocalSearchParams<{ category?: string }>();
  const snapshot = buildPersonalSnapshot(kundli, language);
  const selected = snapshot.categoryScores.find(item => item.type === params.category)
    ?? snapshot.categoryScores.find(item => item.selected)
    ?? snapshot.categoryScores[0];
  const color = selected ? scoreColor(selected.score) : snapshot.color;
  const androidStatusBar = StatusBar.currentHeight ?? 24;
  const topPad = Platform.OS === "web" ? 67 : Platform.OS === "android" ? Math.max(insets.top, androidStatusBar) : insets.top;

  return (
    <CosmicBg>
      <View style={[s.topBar, { paddingTop: topPad }]}>
        <Pressable onPress={() => router.back()} style={s.backBtn}>
          <Feather name="arrow-left" size={20} color={C.text} />
        </Pressable>
        <Text style={[s.headerTitle, { color: C.text }]}>Category Structure</Text>
        <View style={{ width: 36 }} />
      </View>

      <ScrollView contentContainerStyle={{ paddingHorizontal: 16, paddingTop: topPad + 64, paddingBottom: insets.bottom + 80 }}>
        {!selected ? (
          <View style={[s.emptyCard, { backgroundColor: C.bgCard2, borderColor: C.border }]}>
            <Text style={[s.emptyTitle, { color: C.text }]}>No category found</Text>
            <Text style={[s.emptyBody, { color: C.textMuted }]}>Create your kundli to see full category scoring.</Text>
          </View>
        ) : (
          <>
            <LinearGradient colors={[`${color}33`, "rgba(15,23,42,0.92)"]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={[s.hero, { borderColor: `${color}66` }]}>
              <View style={s.heroTop}>
                <View style={[s.iconBubble, { backgroundColor: `${color}22`, borderColor: `${color}66` }]}>
                  <Feather name="layers" size={18} color={color} />
                </View>
                <View style={[s.scoreCircle, { borderColor: color, backgroundColor: `${color}18` }]}>
                  <Text style={[s.scoreText, { color }]}>{selected.score}%</Text>
                </View>
              </View>
              <Text style={s.kicker}>KUNDLI CATEGORY BREAKDOWN</Text>
              <Text style={s.title}>{selected.type}</Text>
              <Text style={s.line}>{selected.line}</Text>
              {selected.selected && (
                <Text style={[s.selectedPill, { color, borderColor: `${color}66`, backgroundColor: `${color}16` }]}>SELECTED CATEGORY</Text>
              )}
            </LinearGradient>

            <Section title="What Was Checked" icon="check-circle" color={color} C={C}>
              <View style={s.chipWrap}>
                {selected.checked.map((item, idx) => (
                  <Text key={idx} style={[s.checkChip, { color: C.text, borderColor: C.border, backgroundColor: C.bgCard2 }]}>
                    {item}
                  </Text>
                ))}
              </View>
            </Section>

            <Section title="Score Components" icon="bar-chart-2" color={color} C={C}>
              <View style={s.detailList}>
                {selected.details.map(row => (
                  <BreakdownRow key={row.key} row={row} color={scoreColor(row.score)} />
                ))}
              </View>
            </Section>

            <Section title="Rules Used" icon="shield" color={color} C={C}>
              <View style={s.ruleList}>
                {selected.rules.map((rule, idx) => (
                  <View key={idx} style={s.ruleRow}>
                    <View style={[s.ruleDot, { backgroundColor: color }]} />
                    <Text style={[s.ruleText, { color: C.textMuted }]}>{rule}</Text>
                  </View>
                ))}
              </View>
            </Section>

            <View style={[s.noteCard, { backgroundColor: C.bgCard2, borderColor: C.border }]}>
              <Feather name="info" size={15} color={color} />
              <Text style={[s.noteText, { color: C.textMuted }]}>
                This page explains the lifetime Kundli Category score. For Money Builder, the dasha row shows the current finance timing score used by LifeMap Finance.
              </Text>
            </View>
          </>
        )}
      </ScrollView>
    </CosmicBg>
  );
}

function Section({ title, icon, color, C, children }: {
  title: string;
  icon: keyof typeof Feather.glyphMap;
  color: string;
  C: ReturnType<typeof useColors>["C"];
  children: React.ReactNode;
}) {
  return (
    <View style={[s.section, { backgroundColor: C.bgCard2, borderColor: C.border }]}>
      <View style={s.sectionHeader}>
        <Feather name={icon} size={15} color={color} />
        <Text style={[s.sectionTitle, { color: C.text }]}>{title}</Text>
      </View>
      {children}
    </View>
  );
}

function BreakdownRow({ row, color }: { row: KundliCategoryScore["details"][number]; color: string }) {
  const { C } = useColors();
  const barWidth = `${Math.max(6, Math.min(100, row.score))}%` as const;
  return (
    <View style={[s.breakdownRow, { borderColor: C.border }]}>
      <View style={s.breakdownTop}>
        <View style={s.breakdownTitleWrap}>
          <Text style={[s.breakdownTitle, { color: C.text }]}>{row.label}</Text>
          <Text style={[s.breakdownDetail, { color: C.textMuted }]}>{row.detail}</Text>
        </View>
        <View style={s.breakdownScoreWrap}>
          <Text style={[s.breakdownScore, { color }]}>{row.score}%</Text>
          <Text style={[s.weightText, { color: C.textDim }]}>{row.weightPct ? `${row.weightPct}% weight` : "validator"}</Text>
        </View>
      </View>
      <View style={[s.barTrack, { backgroundColor: C.border }]}>
        <View style={[s.barFill, { backgroundColor: color, width: barWidth }]} />
      </View>
      <View style={s.factorList}>
        {row.factors.map((factor, idx) => (
          <Text key={idx} style={[s.factorText, { color: C.textMuted }]}>- {factor}</Text>
        ))}
      </View>
    </View>
  );
}

const s = StyleSheet.create({
  topBar: {
    position: "absolute", top: 0, left: 0, right: 0, zIndex: 10,
    height: 64, paddingHorizontal: 14,
    flexDirection: "row", alignItems: "center", justifyContent: "space-between",
  },
  backBtn: {
    width: 36, height: 36, borderRadius: 18,
    alignItems: "center", justifyContent: "center",
    backgroundColor: "rgba(15,23,42,0.45)",
  },
  headerTitle: { fontFamily: "Nunito_700Bold", fontSize: 17 },
  hero: {
    borderWidth: 1,
    borderRadius: 20,
    padding: 16,
    gap: 8,
  },
  heroTop: { flexDirection: "row", alignItems: "center", justifyContent: "space-between" },
  iconBubble: { width: 38, height: 38, borderRadius: 19, borderWidth: 1, alignItems: "center", justifyContent: "center" },
  scoreCircle: { width: 62, height: 62, borderRadius: 31, borderWidth: 3, alignItems: "center", justifyContent: "center" },
  scoreText: { fontFamily: "Nunito_700Bold", fontSize: 16, letterSpacing: -0.5 },
  kicker: { color: "rgba(255,255,255,0.55)", fontFamily: "Nunito_700Bold", fontSize: 9, letterSpacing: 1.4 },
  title: { color: "#fff", fontFamily: "Nunito_700Bold", fontSize: 22, lineHeight: 28, letterSpacing: -0.5 },
  line: { color: "rgba(255,255,255,0.74)", fontFamily: "Nunito_600SemiBold", fontSize: 12.5, lineHeight: 18 },
  selectedPill: {
    alignSelf: "flex-start",
    borderWidth: 1,
    borderRadius: 999,
    paddingHorizontal: 8,
    paddingVertical: 4,
    fontFamily: "Nunito_700Bold",
    fontSize: 9,
    letterSpacing: 0.7,
    overflow: "hidden",
  },
  section: { marginTop: 14, borderRadius: 18, borderWidth: 1, padding: 14, gap: 12 },
  sectionHeader: { flexDirection: "row", alignItems: "center", gap: 8 },
  sectionTitle: { fontFamily: "Nunito_700Bold", fontSize: 14 },
  chipWrap: { flexDirection: "row", flexWrap: "wrap", gap: 8 },
  checkChip: {
    borderWidth: 1,
    borderRadius: 999,
    paddingHorizontal: 9,
    paddingVertical: 5,
    fontFamily: "Nunito_600SemiBold",
    fontSize: 10.5,
    overflow: "hidden",
  },
  detailList: { gap: 10 },
  breakdownRow: { borderWidth: 1, borderRadius: 14, padding: 11, gap: 9 },
  breakdownTop: { flexDirection: "row", alignItems: "flex-start", gap: 10 },
  breakdownTitleWrap: { flex: 1, gap: 2 },
  breakdownTitle: { fontFamily: "Nunito_700Bold", fontSize: 13 },
  breakdownDetail: { fontFamily: "Nunito_500Medium", fontSize: 11, lineHeight: 15 },
  breakdownScoreWrap: { alignItems: "flex-end", minWidth: 74 },
  breakdownScore: { fontFamily: "Nunito_700Bold", fontSize: 17, letterSpacing: -0.5 },
  weightText: { fontFamily: "Nunito_700Bold", fontSize: 8.5 },
  barTrack: { height: 6, borderRadius: 999, overflow: "hidden" },
  barFill: { height: 6, borderRadius: 999 },
  factorList: { gap: 4 },
  factorText: { fontFamily: "Nunito_600SemiBold", fontSize: 10.5, lineHeight: 15 },
  ruleList: { gap: 8 },
  ruleRow: { flexDirection: "row", alignItems: "flex-start", gap: 8 },
  ruleDot: { width: 7, height: 7, borderRadius: 3.5, marginTop: 5 },
  ruleText: { flex: 1, fontFamily: "Nunito_600SemiBold", fontSize: 12, lineHeight: 17 },
  noteCard: { marginTop: 14, borderRadius: 14, borderWidth: 1, padding: 12, flexDirection: "row", gap: 8, alignItems: "flex-start" },
  noteText: { flex: 1, fontFamily: "Nunito_600SemiBold", fontSize: 11.5, lineHeight: 16 },
  emptyCard: { borderRadius: 16, borderWidth: 1, padding: 16, gap: 6 },
  emptyTitle: { fontFamily: "Nunito_700Bold", fontSize: 15 },
  emptyBody: { fontFamily: "Nunito_600SemiBold", fontSize: 12, lineHeight: 17 },
});
