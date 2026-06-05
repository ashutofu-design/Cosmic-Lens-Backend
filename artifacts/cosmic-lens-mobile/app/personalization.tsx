import { Feather } from "@expo/vector-icons";
import { LinearGradient } from "expo-linear-gradient";
import { router } from "expo-router";
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
import { buildPersonalSnapshot, formatCategoryScore } from "@/lib/personalizationSnapshot";

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
  const { kundli } = useUser();
  const { C } = useColors();
  const snapshot = buildPersonalSnapshot(kundli);

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
          </View>
          <View style={s.powerBox}>
            <Text style={s.powerLabel}>KUNDLI CATEGORY</Text>
            <View style={s.powerTypeRow}>
              <Text style={s.powerType}>{snapshot.powerType}</Text>
              <Pressable onPress={() => openCategoryDetail(snapshot.powerType)} style={s.powerTypeViewPill}>
                <Text style={s.powerTypeViewText}>VIEW</Text>
                <Feather name="arrow-right" size={10} color="#f9a8d4" />
              </Pressable>
            </View>
          </View>
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
                    </View>
                    <View style={s.categoryAction}>
                      <Text style={[s.categoryScore, { color }]}>{formatCategoryScore(cat.score)}%</Text>
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
      </ScrollView>
    </CosmicBg>
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
    gap: 2,
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
  noteTitle: { fontFamily: "Nunito_700Bold", fontSize: 13 },
  noteBody: { fontFamily: "Nunito_500Medium", fontSize: 12, lineHeight: 17 },
});
