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
import { FadeInView, staggerDelay } from "@/components/motion/FadeInView";
import { useUser } from "@/context/UserContext";
import { useColors } from "@/hooks/useColors";
import { buildPersonalSnapshot, formatCategoryScore } from "@/lib/personalizationSnapshot";

function scoreColor(score: number): string {
  if (score >= 70) return "#22c55e";
  if (score >= 50) return "#f59e0b";
  return "#ef4444";
}

export default function KundliCategoryDetailScreen() {
  const insets = useSafeAreaInsets();
  const { C } = useColors();
  const { kundli } = useUser();
  const params = useLocalSearchParams<{ category?: string }>();
  const snapshot = buildPersonalSnapshot(kundli);
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
        <Text style={[s.headerTitle, { color: C.text }]}>Category Meaning</Text>
        <View style={{ width: 36 }} />
      </View>

      <ScrollView contentContainerStyle={{ paddingHorizontal: 16, paddingTop: topPad + 64, paddingBottom: insets.bottom + 80 }}>
        {!selected ? (
          <FadeInView delay={staggerDelay(0)}>
          <View style={[s.emptyCard, { backgroundColor: C.bgCard2, borderColor: C.border }]}>
            <Text style={[s.emptyTitle, { color: C.text }]}>No category found</Text>
            <Text style={[s.emptyBody, { color: C.textMuted }]}>Create your kundli to see your Kundli category meaning.</Text>
          </View>
          </FadeInView>
        ) : (
          <>
            <FadeInView delay={staggerDelay(0)}>
            <LinearGradient colors={[`${color}33`, "rgba(15,23,42,0.92)"]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={[s.hero, { borderColor: `${color}66` }]}>
              <View style={s.heroTop}>
                <View style={[s.iconBubble, { backgroundColor: `${color}22`, borderColor: `${color}66` }]}>
                  <Feather name="layers" size={18} color={color} />
                </View>
                <View style={[s.scoreCircle, { borderColor: color, backgroundColor: `${color}18` }]}>
                  <Text style={[s.scoreText, { color }]}>{formatCategoryScore(selected.score)}%</Text>
                </View>
              </View>
              <Text style={s.kicker}>WHAT THIS MEANS</Text>
              <Text style={s.title}>{selected.type}</Text>
              <Text style={s.line}>{selected.meaning}</Text>
              {selected.selected && (
                <Text style={[s.selectedPill, { color, borderColor: `${color}66`, backgroundColor: `${color}16` }]}>SELECTED CATEGORY</Text>
              )}
            </LinearGradient>
            </FadeInView>

            <FadeInView delay={staggerDelay(1)}>
            <View style={[s.section, { backgroundColor: C.bgCard2, borderColor: C.border }]}>
              <View style={s.sectionHeader}>
                <Feather name="heart" size={15} color={color} />
                <Text style={[s.sectionTitle, { color: C.text }]}>In Your Life</Text>
              </View>
              <View style={s.pointList}>
                {selected.meaningPoints.map((point, idx) => (
                  <View key={idx} style={s.pointRow}>
                    <View style={[s.pointDot, { backgroundColor: color }]} />
                    <Text style={[s.pointText, { color: C.textMuted }]}>{point}</Text>
                  </View>
                ))}
              </View>
            </View>
            </FadeInView>

            <FadeInView delay={staggerDelay(2)}>
            <View style={[s.noteCard, { backgroundColor: C.bgCard2, borderColor: C.border }]}>
              <Feather name="info" size={15} color={color} />
              <Text style={[s.noteText, { color: C.textMuted }]}>
                This meaning comes from your saved kundli. It stays the same unless your birth chart details change.
              </Text>
            </View>
            </FadeInView>
          </>
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
  pointList: { gap: 10 },
  pointRow: { flexDirection: "row", alignItems: "flex-start", gap: 8 },
  pointDot: { width: 7, height: 7, borderRadius: 3.5, marginTop: 5 },
  pointText: { flex: 1, fontFamily: "Nunito_600SemiBold", fontSize: 12.5, lineHeight: 18 },
  noteCard: { marginTop: 14, borderRadius: 14, borderWidth: 1, padding: 12, flexDirection: "row", gap: 8, alignItems: "flex-start" },
  noteText: { flex: 1, fontFamily: "Nunito_600SemiBold", fontSize: 11.5, lineHeight: 16 },
  emptyCard: { borderRadius: 16, borderWidth: 1, padding: 16, gap: 6 },
  emptyTitle: { fontFamily: "Nunito_700Bold", fontSize: 15 },
  emptyBody: { fontFamily: "Nunito_600SemiBold", fontSize: 12, lineHeight: 17 },
});
