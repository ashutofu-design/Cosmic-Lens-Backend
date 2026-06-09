import { Feather } from "@expo/vector-icons";
import { LinearGradient } from "expo-linear-gradient";
import React from "react";
import { StyleSheet, Text, View } from "react-native";

import type { LoveReportSection } from "@/lib/loveRealityProReport";

type Props = {
  isDark: boolean;
  p1Name: string;
  p2Name: string;
  scores: { love: number; breakup: number; loyalty: number; return: number; future: number };
  sections: LoveReportSection[];
};

function ScorePill({ label, value, isDark }: { label: string; value: number; isDark: boolean }) {
  return (
    <View style={[s.scorePill, { borderColor: isDark ? "rgba(244,114,182,0.35)" : "rgba(236,72,153,0.25)" }]}>
      <Text style={[s.scoreLbl, { color: isDark ? "#fbcfe8" : "#9d174d" }]}>{label}</Text>
      <Text style={[s.scoreVal, { color: isDark ? "#fff" : "#0F172A" }]}>{value}</Text>
    </View>
  );
}

export function LoveRealityProReportView({ isDark, p1Name, p2Name, scores, sections }: Props) {
  const text = isDark ? "#f1f5f9" : "#0F172A";
  const dim = isDark ? "rgba(226,232,240,0.7)" : "#64748B";
  const cardBg = isDark ? "rgba(255,255,255,0.06)" : "rgba(255,255,255,0.92)";
  const border = isDark ? "rgba(255,255,255,0.1)" : "rgba(0,0,0,0.06)";

  return (
    <View style={{ gap: 14 }}>
      <LinearGradient
        colors={isDark ? ["rgba(147,51,234,0.35)", "rgba(236,72,153,0.2)"] : ["rgba(147,51,234,0.12)", "rgba(236,72,153,0.08)"]}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
        style={[s.hero, { borderColor: border }]}
      >
        <Text style={[s.heroTitle, { color: text }]}>Love Reality Pro</Text>
        <Text style={[s.heroNames, { color: dim }]}>
          {p1Name} & {p2Name}
        </Text>
        <View style={s.scoreRow}>
          <ScorePill label="Love" value={scores.love} isDark={isDark} />
          <ScorePill label="Breakup" value={scores.breakup} isDark={isDark} />
          <ScorePill label="Loyalty" value={scores.loyalty} isDark={isDark} />
          <ScorePill label="Return" value={scores.return} isDark={isDark} />
          <ScorePill label="Future" value={scores.future} isDark={isDark} />
        </View>
      </LinearGradient>

      {sections.map((sec, idx) => (
        <View key={sec.id} style={[s.card, { backgroundColor: cardBg, borderColor: border }]}>
          <Text style={[s.secNum, { color: isDark ? "#f472b6" : "#db2777" }]}>
            {String(idx + 1).padStart(2, "0")}
          </Text>
          <Text style={[s.secTitle, { color: text }]}>{sec.title}</Text>
          {sec.subtitle ? (
            <Text style={[s.secSub, { color: dim }]}>{sec.subtitle}</Text>
          ) : null}
          {sec.body ? (
            <Text style={[s.body, { color: text }]}>{sec.body}</Text>
          ) : null}
          {(sec.tableRows || []).map((row, ri) => (
            <View key={`${sec.id}-t-${ri}`} style={[s.tableRow, { borderColor: border }]}>
              {row.map((cell, ci) => (
                <Text
                  key={`${sec.id}-t-${ri}-${ci}`}
                  style={[
                    s.tableCell,
                    { color: text, flex: ci === row.length - 1 ? 1.4 : 1 },
                  ]}
                >
                  {cell}
                </Text>
              ))}
            </View>
          ))}
          {(sec.bullets || []).map((b, i) => (
            <View key={`${sec.id}-b-${i}`} style={s.bulletRow}>
              <Text style={[s.bulletDot, { color: isDark ? "#f472b6" : "#db2777" }]}>•</Text>
              <Text style={[s.bulletTxt, { color: text }]}>{b}</Text>
            </View>
          ))}
        </View>
      ))}
    </View>
  );
}

const s = StyleSheet.create({
  hero: { borderRadius: 16, borderWidth: 1, padding: 16, gap: 8 },
  heroTitle: { fontFamily: "Nunito_700Bold", fontSize: 20 },
  heroNames: { fontFamily: "Nunito_500Medium", fontSize: 13 },
  scoreRow: { flexDirection: "row", flexWrap: "wrap", gap: 8, marginTop: 6 },
  scorePill: {
    borderWidth: 1,
    borderRadius: 10,
    paddingHorizontal: 10,
    paddingVertical: 6,
    minWidth: 72,
  },
  scoreLbl: { fontFamily: "Nunito_500Medium", fontSize: 10 },
  scoreVal: { fontFamily: "Nunito_700Bold", fontSize: 16, marginTop: 2 },
  card: { borderRadius: 14, borderWidth: 1, padding: 14, gap: 8 },
  secNum: { fontFamily: "Nunito_700Bold", fontSize: 11, letterSpacing: 1 },
  secTitle: { fontFamily: "Nunito_700Bold", fontSize: 16, lineHeight: 22 },
  secSub: { fontFamily: "Nunito_500Medium", fontSize: 12, lineHeight: 17 },
  body: { fontFamily: "Nunito_400Regular", fontSize: 14, lineHeight: 22 },
  bulletRow: { flexDirection: "row", gap: 8, alignItems: "flex-start" },
  bulletDot: { fontFamily: "Nunito_700Bold", fontSize: 14, lineHeight: 22 },
  bulletTxt: { flex: 1, fontFamily: "Nunito_400Regular", fontSize: 14, lineHeight: 22 },
  tableRow: {
    flexDirection: "row",
    gap: 6,
    borderTopWidth: StyleSheet.hairlineWidth,
    paddingTop: 6,
    marginTop: 4,
  },
  tableCell: { fontFamily: "Nunito_500Medium", fontSize: 12, lineHeight: 17 },
});
