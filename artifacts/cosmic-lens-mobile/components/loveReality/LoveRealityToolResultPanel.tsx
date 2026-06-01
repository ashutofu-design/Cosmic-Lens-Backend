import { Feather } from "@expo/vector-icons";
import { BlurView } from "expo-blur";
import * as Haptics from "expo-haptics";
import { LinearGradient } from "expo-linear-gradient";
import React from "react";
import { Platform, Pressable, StyleSheet, Text, View } from "react-native";

import { LoveRealityResultHero } from "@/components/loveReality/LoveRealityBasicScreen";
import type { ChartProof } from "@/lib/loveRealityChartProof";
import type { LoveRealityBasicDisplay } from "@/lib/loveRealityToolMappers";
import { LOVE_REALITY_PRO_UI_PRICING } from "@/lib/loveRealityProOffer";

function ChartDataGrid({
  proof,
  isDark,
}: {
  proof: ChartProof;
  isDark: boolean;
}) {
  const colBg = isDark ? "rgba(8,12,28,0.72)" : "rgba(15,23,42,0.04)";
  const border = isDark ? "rgba(148,163,184,0.14)" : "rgba(15,23,42,0.08)";
  const hi = isDark ? "#f8fafc" : "#0F172A";
  const lo = isDark ? "rgba(148,163,184,0.75)" : "#64748B";
  const accent = isDark ? "#c4b5fd" : "#7c3aed";

  function Column({ title, rows }: { title: string; rows: { line: string }[] }) {
    return (
      <View style={[g.col, { backgroundColor: colBg, borderColor: border }]}>
        <Text style={[g.colHead, { color: accent }]} numberOfLines={1}>
          {title}
        </Text>
        {rows.map((row, i) => {
          const parts = row.line.split(" — ");
          const main = parts[0] ?? row.line;
          const tag = parts[1];
          return (
            <View key={`${title}-${i}`} style={g.row}>
              <Text style={[g.planetLine, { color: hi }]} numberOfLines={2}>
                {main}
              </Text>
              {tag ? (
                <Text style={[g.tag, { color: "#f87171" }]} numberOfLines={1}>
                  {tag}
                </Text>
              ) : null}
            </View>
          );
        })}
      </View>
    );
  }

  return (
    <View style={g.grid}>
      <View style={g.cols}>
        <Column title="Your Chart" rows={proof.p1Rows} />
        <Column title={proof.p2Name} rows={proof.p2Rows} />
      </View>
      <Text style={[g.engineNote, { color: lo }]}>Lahiri · D1 + D9 · Swiss Ephemeris</Text>
    </View>
  );
}

function AspectPills({ badges, isDark }: { badges: ChartProof["aspectBadges"]; isDark: boolean }) {
  if (!badges.length) return null;
  return (
    <View style={g.pillRow}>
      {badges.map((b, i) => (
        <View
          key={`${b.label}-${i}`}
          style={[
            g.pill,
            {
              borderColor: isDark ? "rgba(251,191,36,0.45)" : "rgba(245,158,11,0.35)",
              backgroundColor: isDark ? "rgba(251,191,36,0.08)" : "rgba(251,191,36,0.06)",
            },
          ]}
        >
          <Text style={g.pillIcon}>{b.icon}</Text>
          <Text style={[g.pillTxt, { color: isDark ? "#fde68a" : "#b45309" }]} numberOfLines={2}>
            {b.label}
          </Text>
        </View>
      ))}
    </View>
  );
}

export function LoveRealityToolResultPanel({
  toolTitle,
  userName,
  partnerName,
  display,
  isDark,
  bottomPad,
  accentGradient,
  onOpenPro,
  showHeader = false,
  onBack,
}: {
  toolTitle: string;
  userName: string;
  partnerName: string;
  display: LoveRealityBasicDisplay;
  isDark: boolean;
  bottomPad: number;
  accentGradient: [string, string];
  onOpenPro: () => void;
  showHeader?: boolean;
  onBack?: () => void;
}) {
  const textHi = isDark ? "#fff" : "#0F172A";
  const textLo = isDark ? "rgba(203,213,225,0.65)" : "#64748B";
  const { offerInr } = LOVE_REALITY_PRO_UI_PRICING;
  const proof = display.chartProof;
  const neonBorder = isDark ? "rgba(168,85,247,0.55)" : "rgba(124,58,237,0.35)";

  return (
    <View style={p.root}>
      {showHeader && (
        <View style={p.header}>
          <Pressable
            onPress={() => {
              Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
              onBack?.();
            }}
            hitSlop={8}
          >
            <View
              style={[
                p.backCircle,
                {
                  borderColor: isDark ? "rgba(255,255,255,0.12)" : "rgba(0,0,0,0.08)",
                  backgroundColor: isDark ? "rgba(255,255,255,0.06)" : "rgba(0,0,0,0.04)",
                },
              ]}
            >
              <Feather name="chevron-left" size={22} color={textHi} />
            </View>
          </Pressable>
          <Text style={[p.headerTitle, { color: textHi }]} numberOfLines={1}>
            {toolTitle}
          </Text>
          <View style={{ width: 40 }} />
        </View>
      )}

      <View style={[p.badge, { borderColor: neonBorder, shadowColor: accentGradient[0] }]}>
        <LinearGradient
          colors={isDark ? ["rgba(124,58,237,0.12)", "rgba(236,72,153,0.06)"] : ["rgba(124,58,237,0.06)", "rgba(236,72,153,0.04)"]}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 0 }}
          style={StyleSheet.absoluteFill}
        />
        <Text style={[p.badgeTxt, { color: isDark ? "#e9d5ff" : "#6d28d9" }]} numberOfLines={1}>
          Deep Chart Analysis: {userName} ✦ {partnerName}
        </Text>
      </View>

      <View style={p.body}>
        <View style={p.heroZone}>
          <LoveRealityResultHero display={display} isDark={isDark} accentGradient={accentGradient} compact />
        </View>

        {proof ? (
          <View style={p.proofZone}>
            <ChartDataGrid proof={proof} isDark={isDark} />
            <AspectPills badges={proof.aspectBadges} isDark={isDark} />
          </View>
        ) : null}

        <Text style={[p.hook, { color: textHi }]} numberOfLines={3}>
          {display.hookLine}
        </Text>
      </View>

      <View style={[p.upsellWrap, { paddingBottom: bottomPad + 6 }]}>
        <Pressable
          onPress={() => {
            Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
            onOpenPro();
          }}
          style={({ pressed }) => ({ opacity: pressed ? 0.9 : 1 })}
        >
          <View style={[p.upsellCard, { borderColor: isDark ? "rgba(251,146,60,0.4)" : "rgba(234,88,12,0.28)" }]}>
            {Platform.OS !== "web" ? (
              <BlurView intensity={isDark ? 38 : 52} tint={isDark ? "dark" : "light"} style={StyleSheet.absoluteFill} />
            ) : null}
            <View
              style={[
                StyleSheet.absoluteFill,
                { backgroundColor: isDark ? "rgba(10,6,22,0.82)" : "rgba(255,255,255,0.88)" },
              ]}
            />
            <View style={p.upsellInner}>
              <Text style={[p.upsellHead, { color: textHi }]}>Want the complete 14-page truth?</Text>
              <Text style={[p.upsellSub, { color: textLo }]}>
                Get the combined Pro PDF with exact planetary remedies, detailed aspect breakdowns, and timelines.
              </Text>
              <LinearGradient
                colors={["#f97316", "#ec4899", "#9333ea"]}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 0 }}
                style={p.upsellBtn}
              >
                <Feather name="file-text" size={15} color="#fff" />
                <Text style={p.upsellBtnTxt}>Unlock Full Pro PDF — ₹{offerInr}</Text>
              </LinearGradient>
            </View>
          </View>
        </Pressable>
      </View>
    </View>
  );
}

const g = StyleSheet.create({
  grid: { gap: 6 },
  cols: { flexDirection: "row", gap: 8 },
  col: {
    flex: 1,
    borderRadius: 10,
    borderWidth: 1,
    paddingHorizontal: 8,
    paddingVertical: 7,
    gap: 4,
    minWidth: 0,
  },
  colHead: { fontSize: 9, fontFamily: "Nunito_800ExtraBold", letterSpacing: 0.8, marginBottom: 2 },
  row: { gap: 1 },
  planetLine: { fontSize: 9.5, fontFamily: "Nunito_700Bold", lineHeight: 13 },
  tag: { fontSize: 8.5, fontFamily: "Nunito_600SemiBold" },
  engineNote: { fontSize: 8, fontFamily: "Nunito_500Medium", textAlign: "center", marginTop: 2 },
  pillRow: { flexDirection: "row", flexWrap: "wrap", gap: 6, justifyContent: "center" },
  pill: {
    flexDirection: "row",
    alignItems: "center",
    gap: 5,
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 20,
    borderWidth: 1,
    maxWidth: "48%",
    flexGrow: 1,
    minWidth: "46%",
  },
  pillIcon: { fontSize: 11 },
  pillTxt: { flex: 1, fontSize: 9, fontFamily: "Nunito_700Bold", lineHeight: 12 },
});

const p = StyleSheet.create({
  root: { flex: 1, minHeight: 0 },
  header: {
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: 16,
    paddingBottom: 6,
    gap: 10,
  },
  backCircle: {
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: "center",
    justifyContent: "center",
    borderWidth: 1,
  },
  headerTitle: { flex: 1, fontSize: 17, fontFamily: "Nunito_700Bold", textAlign: "center" },
  badge: {
    marginHorizontal: 16,
    marginBottom: 6,
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 12,
    borderWidth: 1,
    overflow: "hidden",
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.35,
    shadowRadius: 8,
    elevation: 4,
  },
  badgeTxt: { fontSize: 11, fontFamily: "Nunito_700Bold", textAlign: "center" },
  body: { flex: 1, minHeight: 0, paddingHorizontal: 16, justifyContent: "space-between" },
  heroZone: { alignItems: "center", paddingTop: 2 },
  proofZone: { gap: 6, flexShrink: 1 },
  hook: {
    fontSize: 12,
    fontFamily: "Nunito_700Bold",
    fontStyle: "italic",
    textAlign: "center",
    lineHeight: 17,
    paddingVertical: 4,
  },
  upsellWrap: { paddingHorizontal: 16, paddingTop: 2 },
  upsellCard: { borderRadius: 16, borderWidth: 1, overflow: "hidden" },
  upsellInner: { padding: 12, gap: 4 },
  upsellHead: { fontSize: 13, fontFamily: "Nunito_800ExtraBold" },
  upsellSub: { fontSize: 10, fontFamily: "Nunito_500Medium", lineHeight: 14 },
  upsellBtn: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
    paddingVertical: 11,
    borderRadius: 11,
    marginTop: 4,
  },
  upsellBtnTxt: { color: "#fff", fontSize: 12, fontFamily: "Nunito_800ExtraBold" },
});
