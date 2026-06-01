import { Feather } from "@expo/vector-icons";
import { LinearGradient } from "expo-linear-gradient";
import { router } from "expo-router";
import React, { useState } from "react";
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
import { buildPersonalSnapshot, type PersonalInsight } from "@/lib/personalizationSnapshot";

function pctColor(value: number | null, key: string): string {
  if (value == null) return "#94a3b8";
  if (key === "problems" || key === "hidden") {
    if (value >= 70) return "#22c55e";
    if (value >= 50) return "#f59e0b";
    return "#ef4444";
  }
  if (value >= 70) return "#22c55e";
  if (value >= 50) return "#f59e0b";
  return "#ef4444";
}

export default function PersonalizationScreen() {
  const insets = useSafeAreaInsets();
  const { kundli, language } = useUser();
  const { C } = useColors();
  const [feedback, setFeedback] = useState<"yes" | "no" | null>(null);
  const snapshot = buildPersonalSnapshot(kundli, language);
  const metrics = snapshot.insights.filter(item => item.key !== "theme");

  const androidStatusBar = StatusBar.currentHeight ?? 24;
  const topPad = Platform.OS === "web" ? 67 : Platform.OS === "android" ? Math.max(insets.top, androidStatusBar) : insets.top;
  const openCategoryDetail = (category: string) => {
    router.push({ pathname: "/kundli-category-detail", params: { category } } as any);
  };

  return (
    <CosmicBg>
      <View style={[s.topBar, { paddingTop: topPad }]}>
        <Pressable onPress={() => router.back()} style={s.backBtn}>
          <Feather name="arrow-left" size={20} color={C.text} />
        </Pressable>
        <Text style={[s.headerTitle, { color: C.text }]}>Personalization</Text>
        <View style={{ width: 36 }} />
      </View>

      <ScrollView contentContainerStyle={{ paddingHorizontal: 16, paddingTop: topPad + 64, paddingBottom: insets.bottom + 96 }}>
        <LinearGradient colors={snapshot.darkGrad} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={s.heroCard}>
          <View style={s.heroHeader}>
            <Text style={s.heroKicker}>YOUR KUNDLI UNDERSTANDS YOU</Text>
            <Text style={s.themePill}>{snapshot.themeLabel}</Text>
          </View>
          <View style={s.powerBox}>
            <View>
              <Text style={s.powerLabel}>KUNDLI CATEGORY</Text>
              <View style={s.powerTypeRow}>
                <Text style={s.powerType}>{snapshot.powerType}</Text>
                <Pressable onPress={() => openCategoryDetail(snapshot.powerType)} style={s.powerTypeViewPill}>
                  <Text style={s.powerTypeViewText}>VIEW</Text>
                  <Feather name="arrow-right" size={10} color="#f9a8d4" />
                </Pressable>
              </View>
            </View>
            <View style={s.powerScoreCircle}>
              <Text style={s.powerScore}>{snapshot.powerScore == null ? "--" : `${snapshot.powerScore}%`}</Text>
            </View>
          </View>
          <Text style={s.powerLine}>{snapshot.powerLine}</Text>
          <Text style={s.innerType}>{snapshot.innerType}</Text>
          <Text style={s.heroTitle}>{snapshot.identityLine}</Text>
          <Text style={s.heroBody}>{snapshot.innerTypeSub}</Text>
          <View style={s.highlightRow}>
            <View style={s.highlightBox}>
              <Text style={s.highlightLabel}>STRONGEST TRAIT</Text>
              <Text style={s.highlightValue}>{snapshot.strongestTrait}</Text>
            </View>
            <View style={s.highlightBox}>
              <Text style={s.highlightLabel}>PRESSURE POINT</Text>
              <Text style={s.highlightValue}>{snapshot.pressurePoint}</Text>
            </View>
          </View>
        </LinearGradient>

        {!!snapshot.categoryScores.length && (
          <View style={[s.categoryCard, { backgroundColor: C.bgCard2, borderColor: C.border }]}>
            <View style={s.categoryHeader}>
              <View>
                <Text style={[s.noteTitle, { color: C.text }]}>All Kundli Categories</Text>
                <Text style={[s.noteBody, { color: C.textMuted }]}>
                  Your strongest category is highlighted.
                </Text>
              </View>
              <Feather name="layers" size={16} color={snapshot.color} />
            </View>
            <View style={s.categoryList}>
              {snapshot.categoryScores.map(cat => {
                const color = cat.selected ? snapshot.color : pctColor(cat.score, "category");
                return (
                  <Pressable
                    key={cat.type}
                    onPress={() => openCategoryDetail(cat.type)}
                    style={[
                      s.categoryRow,
                      {
                        borderColor: cat.selected ? `${snapshot.color}77` : C.border,
                        backgroundColor: cat.selected ? `${snapshot.color}18` : "transparent",
                      },
                    ]}
                  >
                    <View style={s.categoryText}>
                      <View style={s.categoryTitleRow}>
                        <Text style={[s.categoryName, { color: C.text }]}>{cat.type}</Text>
                        {cat.selected && (
                          <Text style={[s.selectedPill, { color: snapshot.color, borderColor: `${snapshot.color}66` }]}>
                            SELECTED
                          </Text>
                        )}
                      </View>
                      <Text style={[s.categoryReason, { color: C.textMuted }]} numberOfLines={1}>
                        {cat.reasons.join(" · ")}
                      </Text>
                    </View>
                    <View style={s.categoryAction}>
                      <Text style={[s.categoryScore, { color }]}>{cat.score}%</Text>
                      <View style={[s.categoryViewPill, { borderColor: `${color}66`, backgroundColor: `${color}14` }]}>
                        <Text style={[s.categoryViewText, { color }]}>VIEW</Text>
                        <Feather name="chevron-right" size={10} color={color} />
                      </View>
                    </View>
                  </Pressable>
                );
              })}
            </View>
          </View>
        )}

        <View style={s.memoryGrid}>
          <MemoryCard title="Hidden Strength" body={snapshot.hiddenStrength} icon="zap" color="#22c55e" />
          <MemoryCard title="Pressure Trigger" body={snapshot.pressureTrigger} icon="alert-triangle" color="#f59e0b" />
          <MemoryCard title="Today's Tip" body={snapshot.todayTip} icon="sun" color="#38bdf8" />
          <MemoryCard title="Best Mode" body={snapshot.bestMode} icon="target" color="#a78bfa" />
        </View>

        <View style={s.metricGrid}>
          {metrics.map(metric => (
            <MetricCard key={metric.key} metric={metric} />
          ))}
        </View>

        <View style={[s.bulletCard, { backgroundColor: C.bgCard2, borderColor: C.border }]}>
          <Text style={[s.noteTitle, { color: C.text }]}>What your chart is hinting</Text>
          {snapshot.bullets.map((bullet, idx) => (
            <View key={idx} style={s.bulletRow}>
              <View style={[s.bulletDot, { backgroundColor: snapshot.color }]} />
              <Text style={[s.bulletText, { color: C.textMuted }]}>{bullet}</Text>
            </View>
          ))}
        </View>

        <View style={[s.noteCard, { backgroundColor: C.bgCard2, borderColor: C.border }]}>
          <Text style={[s.noteTitle, { color: C.text }]}>Does this feel accurate?</Text>
          <Text style={[s.noteBody, { color: C.textMuted }]}>
            Your response helps us tune the personalization experience.
          </Text>
          <View style={s.feedbackRow}>
            <Pressable
              onPress={() => setFeedback("yes")}
              style={[s.feedbackBtn, { borderColor: feedback === "yes" ? "#22c55e" : C.border, backgroundColor: feedback === "yes" ? "rgba(34,197,94,0.16)" : "transparent" }]}
            >
              <Text style={[s.feedbackTxt, { color: feedback === "yes" ? "#22c55e" : C.text }]}>Feels accurate</Text>
            </Pressable>
            <Pressable
              onPress={() => setFeedback("no")}
              style={[s.feedbackBtn, { borderColor: feedback === "no" ? "#f59e0b" : C.border, backgroundColor: feedback === "no" ? "rgba(245,158,11,0.16)" : "transparent" }]}
            >
              <Text style={[s.feedbackTxt, { color: feedback === "no" ? "#f59e0b" : C.text }]}>Not quite</Text>
            </Pressable>
          </View>
        </View>

        <View style={[s.trustCard, { backgroundColor: C.bgCard2, borderColor: C.border }]}>
          <Feather name="shield" size={15} color={snapshot.color} />
          <Text style={[s.trustText, { color: C.textMuted }]}>{snapshot.trustLine}</Text>
        </View>
      </ScrollView>
    </CosmicBg>
  );
}

function MetricCard({ metric }: { metric: PersonalInsight }) {
  const { C } = useColors();
  const valueColor = pctColor(metric.value, metric.key);

  return (
    <View style={[s.metricCard, { backgroundColor: C.bgCard2, borderColor: C.border }]}>
      <View style={[s.bigCircle, { borderColor: valueColor, backgroundColor: `${valueColor}18` }]}>
        <Text style={[s.bigValue, { color: valueColor }]}>{metric.value == null ? "--" : `${metric.value}%`}</Text>
        <Text style={[s.bigLabel, { color: C.textDim }]}>{metric.label}</Text>
      </View>
      <Text style={[s.metricTitle, { color: C.text }]}>{metric.title}</Text>
      <Text style={[s.metricTag, { color: valueColor }]}>{metric.tag}</Text>
      <Text style={[s.metricSub, { color: C.textMuted }]}>{metric.sub}</Text>
      <Text style={[s.metricLine, { color: C.text }]}>{metric.line}</Text>
      {!!metric.factors?.length && (
        <View style={s.factorWrap}>
          {metric.factors.slice(0, 4).map((factor, idx) => (
            <Text key={idx} style={[s.factorChip, { color: C.textMuted, borderColor: C.border }]}>
              {factor}
            </Text>
          ))}
        </View>
      )}
    </View>
  );
}

function MemoryCard({ title, body, icon, color }: { title: string; body: string; icon: keyof typeof Feather.glyphMap; color: string }) {
  const { C } = useColors();
  return (
    <View style={[s.memoryCard, { backgroundColor: C.bgCard2, borderColor: C.border }]}>
      <View style={[s.memoryIcon, { backgroundColor: `${color}18`, borderColor: `${color}55` }]}>
        <Feather name={icon} size={14} color={color} />
      </View>
      <Text style={[s.memoryTitle, { color: C.text }]}>{title}</Text>
      <Text style={[s.memoryBody, { color: C.textMuted }]}>{body}</Text>
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
  heroCard: {
    borderRadius: 20, padding: 18, borderWidth: 1,
    borderColor: "rgba(236,72,153,0.35)", gap: 9,
  },
  heroHeader: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", gap: 8 },
  heroKicker: { color: "rgba(255,255,255,0.55)", fontFamily: "Nunito_700Bold", fontSize: 9, letterSpacing: 1.5 },
  themePill: {
    color: "#f9a8d4", fontFamily: "Nunito_700Bold", fontSize: 9,
    borderWidth: 1, borderColor: "rgba(249,168,212,0.35)",
    borderRadius: 20, paddingVertical: 4, paddingHorizontal: 8,
    backgroundColor: "rgba(236,72,153,0.14)", overflow: "hidden",
  },
  powerBox: {
    marginTop: 2, borderWidth: 1, borderColor: "rgba(255,255,255,0.16)",
    borderRadius: 16, padding: 12, backgroundColor: "rgba(255,255,255,0.08)",
    flexDirection: "row", alignItems: "center", justifyContent: "space-between", gap: 10,
  },
  powerLabel: { color: "rgba(255,255,255,0.5)", fontFamily: "Nunito_700Bold", fontSize: 8.5, letterSpacing: 1.4 },
  powerTypeRow: { flexDirection: "row", alignItems: "center", gap: 8, marginTop: 2, flexWrap: "wrap" },
  powerType: { color: "#fff", fontFamily: "Nunito_700Bold", fontSize: 18, letterSpacing: -0.3, flexShrink: 1 },
  powerTypeViewPill: {
    flexDirection: "row",
    alignItems: "center",
    gap: 3,
    borderWidth: 1,
    borderColor: "rgba(249,168,212,0.6)",
    backgroundColor: "rgba(249,168,212,0.16)",
    borderRadius: 999,
    paddingHorizontal: 8,
    paddingVertical: 3,
  },
  powerTypeViewText: { color: "#f9a8d4", fontFamily: "Nunito_700Bold", fontSize: 8, letterSpacing: 0.7 },
  powerScoreCircle: {
    width: 54, height: 54, borderRadius: 27,
    borderWidth: 3, borderColor: "rgba(249,168,212,0.8)",
    alignItems: "center", justifyContent: "center",
    backgroundColor: "rgba(236,72,153,0.16)",
  },
  powerScore: { color: "#f9a8d4", fontFamily: "Nunito_700Bold", fontSize: 13, letterSpacing: -0.5 },
  powerLine: { color: "rgba(255,255,255,0.72)", fontFamily: "Nunito_600SemiBold", fontSize: 12.5, lineHeight: 18 },
  innerType: { color: "#f9a8d4", fontFamily: "Nunito_700Bold", fontSize: 13, letterSpacing: 1.4, textTransform: "uppercase" },
  heroTitle: { color: "#fff", fontFamily: "Nunito_700Bold", fontSize: 22, letterSpacing: -0.5, lineHeight: 28 },
  heroBody: { color: "rgba(255,255,255,0.72)", fontFamily: "Nunito_500Medium", fontSize: 13, lineHeight: 19 },
  highlightRow: { flexDirection: "row", gap: 10, marginTop: 5 },
  highlightBox: {
    flex: 1, borderWidth: 1, borderColor: "rgba(255,255,255,0.14)",
    backgroundColor: "rgba(255,255,255,0.08)", borderRadius: 14,
    paddingVertical: 10, paddingHorizontal: 10,
  },
  highlightLabel: { color: "rgba(255,255,255,0.48)", fontFamily: "Nunito_700Bold", fontSize: 8.5, letterSpacing: 1 },
  highlightValue: { color: "#fff", fontFamily: "Nunito_700Bold", fontSize: 12.5, marginTop: 3 },
  memoryGrid: { flexDirection: "row", flexWrap: "wrap", gap: 12, marginTop: 14 },
  memoryCard: { width: "48%", borderRadius: 16, borderWidth: 1, padding: 13, gap: 7 },
  memoryIcon: { width: 30, height: 30, borderRadius: 15, borderWidth: 1, alignItems: "center", justifyContent: "center" },
  memoryTitle: { fontFamily: "Nunito_700Bold", fontSize: 12.5 },
  memoryBody: { fontFamily: "Nunito_600SemiBold", fontSize: 11.2, lineHeight: 16 },
  categoryCard: { marginTop: 14, borderRadius: 18, borderWidth: 1, padding: 14, gap: 12 },
  categoryHeader: { flexDirection: "row", alignItems: "flex-start", justifyContent: "space-between", gap: 10 },
  categoryList: { gap: 8 },
  categoryRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    borderWidth: 1,
    borderRadius: 14,
    paddingVertical: 10,
    paddingHorizontal: 11,
  },
  categoryText: { flex: 1, gap: 3 },
  categoryTitleRow: { flexDirection: "row", alignItems: "center", gap: 6, flexWrap: "wrap" },
  categoryName: { fontFamily: "Nunito_700Bold", fontSize: 12.5 },
  selectedPill: {
    borderWidth: 1,
    borderRadius: 999,
    paddingHorizontal: 6,
    paddingVertical: 2,
    fontFamily: "Nunito_700Bold",
    fontSize: 8,
    letterSpacing: 0.6,
  },
  categoryReason: { fontFamily: "Nunito_500Medium", fontSize: 10.5 },
  categoryAction: { alignItems: "flex-end", gap: 4 },
  categoryScore: { fontFamily: "Nunito_700Bold", fontSize: 16, letterSpacing: -0.4 },
  categoryViewPill: {
    flexDirection: "row",
    alignItems: "center",
    gap: 2,
    borderWidth: 1,
    borderRadius: 999,
    paddingHorizontal: 6,
    paddingVertical: 2,
  },
  categoryViewText: { fontFamily: "Nunito_700Bold", fontSize: 7.5, letterSpacing: 0.6 },
  metricGrid: { flexDirection: "row", flexWrap: "wrap", gap: 12, marginTop: 14 },
  metricCard: {
    width: "48%", borderRadius: 18, borderWidth: 1,
    padding: 14, alignItems: "center", gap: 8,
  },
  bigCircle: {
    width: 86, height: 86, borderRadius: 43, borderWidth: 4,
    alignItems: "center", justifyContent: "center",
  },
  bigValue: { fontFamily: "Nunito_700Bold", fontSize: 22, letterSpacing: -1 },
  bigLabel: { fontFamily: "Nunito_700Bold", fontSize: 9, letterSpacing: 1.2 },
  metricTitle: { fontFamily: "Nunito_700Bold", fontSize: 14, textAlign: "center" },
  metricTag: { fontFamily: "Nunito_700Bold", fontSize: 10.5, textAlign: "center", textTransform: "uppercase", letterSpacing: 0.5 },
  metricSub: { fontFamily: "Nunito_500Medium", fontSize: 10.5, textAlign: "center" },
  metricLine: { fontFamily: "Nunito_600SemiBold", fontSize: 11.5, textAlign: "center", lineHeight: 16 },
  factorWrap: { width: "100%", gap: 5, marginTop: 2 },
  factorChip: {
    borderWidth: 1, borderRadius: 9, paddingVertical: 4, paddingHorizontal: 7,
    fontFamily: "Nunito_600SemiBold", fontSize: 9.5, lineHeight: 13,
  },
  bulletCard: { marginTop: 14, borderRadius: 16, borderWidth: 1, padding: 14, gap: 10 },
  bulletRow: { flexDirection: "row", alignItems: "flex-start", gap: 9 },
  bulletDot: { width: 7, height: 7, borderRadius: 3.5, marginTop: 5 },
  bulletText: { flex: 1, fontFamily: "Nunito_600SemiBold", fontSize: 12.5, lineHeight: 18 },
  noteCard: { marginTop: 14, borderRadius: 16, borderWidth: 1, padding: 14, gap: 5 },
  noteTitle: { fontFamily: "Nunito_700Bold", fontSize: 13 },
  noteBody: { fontFamily: "Nunito_500Medium", fontSize: 12, lineHeight: 17 },
  feedbackRow: { flexDirection: "row", gap: 10, marginTop: 8 },
  feedbackBtn: { flex: 1, borderWidth: 1, borderRadius: 12, paddingVertical: 10, alignItems: "center" },
  feedbackTxt: { fontFamily: "Nunito_700Bold", fontSize: 12 },
  trustCard: {
    marginTop: 12, borderRadius: 14, borderWidth: 1, padding: 12,
    flexDirection: "row", alignItems: "center", gap: 8,
  },
  trustText: { flex: 1, fontFamily: "Nunito_600SemiBold", fontSize: 11.5, lineHeight: 16 },
});
