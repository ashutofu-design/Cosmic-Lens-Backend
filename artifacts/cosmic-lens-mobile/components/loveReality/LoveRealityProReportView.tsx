import { Feather } from "@expo/vector-icons";
import { LinearGradient } from "expo-linear-gradient";
import React from "react";
import { StyleSheet, Text, View } from "react-native";

import type { LoveReportSection } from "@/lib/loveRealityProReport";
import { loveRealityReportLabels, loveReportPdfSectionNo } from "@/lib/loveRealityProReport";
import type { ProPdfLangCode } from "@/lib/proPdfLang";

type Props = {
  isDark: boolean;
  lang?: ProPdfLangCode;
  p1Name: string;
  p2Name: string;
  scores: { love: number; breakup: number; loyalty: number; return: number; future: number };
  sections: LoveReportSection[];
};

type SectionTheme = {
  accent: string;
  soft: string;
  icon: keyof typeof Feather.glyphMap;
  chip: string;
};

function scoreTone(value: number, invert = false): string {
  const v = invert ? 100 - value : value;
  if (v >= 70) return "#10B981";
  if (v >= 45) return "#F59E0B";
  return "#EF4444";
}

function sectionTheme(sec: LoveReportSection, lang: ProPdfLangCode): SectionTheme {
  const labels = loveRealityReportLabels(lang);
  const id = sec.id.toLowerCase();
  if (id.includes("exec") || id.includes("summary")) {
    return { accent: "#A855F7", soft: "rgba(168,85,247,0.14)", icon: "sun", chip: labels.chipOverview };
  }
  if (id.includes("scorecard") || id.includes("metric") || id.includes("core")) {
    return { accent: "#EC4899", soft: "rgba(236,72,153,0.14)", icon: "bar-chart-2", chip: labels.chipScores };
  }
  if (id.includes("deep_connection")) {
    return { accent: "#6366F1", soft: "rgba(99,102,241,0.14)", icon: "heart", chip: labels.chipDeepDive };
  }
  if (id.includes("strength")) {
    return { accent: "#10B981", soft: "rgba(16,185,129,0.14)", icon: "trending-up", chip: labels.chipStrengths };
  }
  if (id.includes("challenge")) {
    return { accent: "#F97316", soft: "rgba(249,115,22,0.14)", icon: "alert-triangle", chip: labels.chipChallenges };
  }
  if (id.includes("verdict")) {
    return { accent: "#FBBF24", soft: "rgba(251,191,36,0.16)", icon: "star", chip: labels.chipVerdict };
  }
  if (id.includes("recommend")) {
    return { accent: "#14B8A6", soft: "rgba(20,184,166,0.14)", icon: "check-circle", chip: labels.chipActionPlan };
  }
  if (id.startsWith("deep_") || id.includes("analysis")) {
    return { accent: "#6366F1", soft: "rgba(99,102,241,0.14)", icon: "heart", chip: labels.chipDeepDive };
  }
  if (id.includes("blueprint")) {
    return { accent: "#8B5CF6", soft: "rgba(139,92,246,0.14)", icon: "compass", chip: labels.chipBlueprint };
  }
  if (id.includes("dimension")) {
    return { accent: "#D946EF", soft: "rgba(217,70,239,0.14)", icon: "grid", chip: labels.chipFiveDimensions };
  }
  if (id.includes("moon")) {
    return { accent: "#38BDF8", soft: "rgba(56,189,248,0.14)", icon: "moon", chip: labels.chipMoonSync };
  }
  if (id.includes("root")) {
    return { accent: "#EF4444", soft: "rgba(239,68,68,0.12)", icon: "zap", chip: labels.chipRootCause };
  }
  return { accent: "#EC4899", soft: "rgba(236,72,153,0.12)", icon: "bookmark", chip: labels.chipInsight };
}

function parseMetricBullet(text: string): { label: string; score: number; band?: string } | null {
  const m = text.match(/^(.+?):\s*(\d+)\s*\/\s*100(?:\s*[—–-]\s*(.+))?$/i);
  if (!m) return null;
  return { label: m[1].trim(), score: Number(m[2]), band: m[3]?.trim() };
}

function ScoreBar({
  value,
  accent,
  invert,
  isDark,
}: {
  value: number;
  accent: string;
  invert?: boolean;
  isDark: boolean;
}) {
  const pct = Math.max(0, Math.min(100, value));
  const fill = scoreTone(value, invert);
  return (
    <View style={[s.barTrack, { backgroundColor: isDark ? "rgba(255,255,255,0.08)" : "rgba(0,0,0,0.06)" }]}>
      <View style={[s.barFill, { width: `${pct}%`, backgroundColor: fill || accent }]} />
    </View>
  );
}

function ScorePill({
  label,
  value,
  isDark,
  invert,
}: {
  label: string;
  value: number;
  isDark: boolean;
  invert?: boolean;
}) {
  const tone = scoreTone(value, invert);
  return (
    <View style={[s.scorePill, { borderColor: `${tone}55`, backgroundColor: isDark ? `${tone}18` : `${tone}12` }]}>
      <Text style={[s.scoreLbl, { color: isDark ? "rgba(255,255,255,0.72)" : "#64748B" }]}>{label}</Text>
      <Text style={[s.scoreVal, { color: tone }]}>{value}</Text>
      <ScoreBar value={value} accent={tone} invert={invert} isDark={isDark} />
    </View>
  );
}

function MetricRow({
  line,
  theme,
  isDark,
  text,
  dim,
}: {
  line: string;
  theme: SectionTheme;
  isDark: boolean;
  text: string;
  dim: string;
}) {
  const parsed = parseMetricBullet(line);
  if (!parsed) {
    return (
      <View style={s.bulletRow}>
        <View style={[s.bulletIcon, { backgroundColor: theme.soft }]}>
          <Feather name="chevron-right" size={12} color={theme.accent} />
        </View>
        <Text style={[s.bulletTxt, { color: text }]}>{line}</Text>
      </View>
    );
  }
  const invert = /breakup|risk|challenge|gap|conflict|escalation/i.test(parsed.label);
  const tone = scoreTone(parsed.score, invert);
  return (
    <View style={[s.metricRow, { backgroundColor: isDark ? "rgba(255,255,255,0.04)" : "rgba(255,255,255,0.85)", borderColor: `${tone}33` }]}>
      <View style={s.metricTop}>
        <Text style={[s.metricLabel, { color: text }]}>{parsed.label}</Text>
        <Text style={[s.metricScore, { color: tone }]}>{parsed.score}/100</Text>
      </View>
      <ScoreBar value={parsed.score} accent={theme.accent} invert={invert} isDark={isDark} />
      {parsed.band ? (
        <Text style={[s.metricBand, { color: dim }]}>{parsed.band}</Text>
      ) : null}
    </View>
  );
}

function SectionCard({
  sec,
  idx,
  isDark,
  text,
  dim,
  lang,
}: {
  sec: LoveReportSection;
  idx: number;
  isDark: boolean;
  text: string;
  dim: string;
  lang: ProPdfLangCode;
}) {
  const labels = loveRealityReportLabels(lang);
  const theme = sectionTheme(sec, lang);
  const isVerdict = sec.id.includes("verdict");
  const isMetrics = sec.id.includes("metric") || sec.id.includes("core");
  const cosmicScoreMatch = sec.subtitle?.match(/(\d+)\s*\/\s*100/);
  const badgeNo = sec.pdfSectionNo ?? loveReportPdfSectionNo(sec.id) ?? idx + 1;
  const inner = (
    <View style={[s.cardInner, { backgroundColor: isDark ? "rgba(15,10,31,0.72)" : "rgba(255,255,255,0.96)" }]}>
      <View style={s.cardHead}>
        <View style={[s.numBadge, { backgroundColor: theme.soft, borderColor: `${theme.accent}44` }]}>
          <Text style={[s.secNum, { color: theme.accent }]}>{String(badgeNo).padStart(2, "0")}</Text>
        </View>
        <View style={{ flex: 1, gap: 4 }}>
          <View style={s.titleRow}>
            <View style={[s.chip, { backgroundColor: theme.soft }]}>
              <Feather name={theme.icon} size={11} color={theme.accent} />
              <Text style={[s.chipTxt, { color: theme.accent }]}>{theme.chip}</Text>
            </View>
          </View>
          <Text style={[s.secTitle, { color: text }]}>{sec.title}</Text>
          {sec.subtitle ? (
            <Text style={[s.secSub, { color: dim }]}>{sec.subtitle}</Text>
          ) : null}
        </View>
      </View>

      {isMetrics && cosmicScoreMatch ? (
        <View style={[s.heroScoreBox, { backgroundColor: theme.soft, borderColor: `${theme.accent}44` }]}>
          <Text style={[s.heroScoreLbl, { color: dim }]}>{labels.cosmicAlignment}</Text>
          <Text style={[s.heroScoreVal, { color: theme.accent }]}>
            {cosmicScoreMatch[1]}/100
          </Text>
        </View>
      ) : null}

      {sec.body ? (
        <View style={[s.bodyBox, isVerdict && { backgroundColor: theme.soft, borderColor: `${theme.accent}33` }]}>
          <Text style={[s.body, { color: text }]}>{sec.body}</Text>
        </View>
      ) : null}

      {(sec.bullets || []).map((b, i) => (
        <MetricRow key={`${sec.id}-b-${i}`} line={b} theme={theme} isDark={isDark} text={text} dim={dim} />
      ))}

      {(sec.tableRows || []).map((row, ri) => (
        <View key={`${sec.id}-t-${ri}`} style={[s.tableCard, { borderColor: `${theme.accent}33` }]}>
          <Text style={[s.tableMain, { color: text }]}>{row[0]}</Text>
          <View style={s.tableMeta}>
            <Text style={[s.tableScore, { color: theme.accent }]}>{row[1]}</Text>
            {row[2] ? <Text style={[s.tableNote, { color: dim }]}>{row[2]}</Text> : null}
          </View>
        </View>
      ))}
    </View>
  );

  return (
    <LinearGradient
      colors={[`${theme.accent}55`, isDark ? "rgba(147,51,234,0.25)" : "rgba(236,72,153,0.2)"]}
      start={{ x: 0, y: 0 }}
      end={{ x: 1, y: 1 }}
      style={s.cardBorder}
    >
      {inner}
    </LinearGradient>
  );
}

export function LoveRealityProReportView({ isDark, lang = "en", p1Name, p2Name, scores, sections }: Props) {
  const labels = loveRealityReportLabels(lang);
  const text = isDark ? "#f1f5f9" : "#0F172A";
  const dim = isDark ? "rgba(226,232,240,0.72)" : "#64748B";

  return (
    <View style={{ gap: 16 }}>
      <LinearGradient
        colors={isDark ? ["#4C1D95", "#831843", "#1e1033"] : ["#F5F3FF", "#FDF2F8", "#FFFFFF"]}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
        style={s.heroBorder}
      >
        <View style={[s.hero, { backgroundColor: isDark ? "rgba(15,10,31,0.55)" : "rgba(255,255,255,0.88)" }]}>
          <View style={s.heroTop}>
            <View style={[s.proBadge, { backgroundColor: isDark ? "rgba(251,191,36,0.15)" : "rgba(251,191,36,0.2)" }]}>
              <Feather name="star" size={11} color="#FBBF24" />
              <Text style={s.proBadgeTxt}>{labels.proBadge}</Text>
            </View>
            <Text style={[s.heroTitle, { color: text }]}>{labels.heroTitle}</Text>
            <Text style={[s.heroNames, { color: dim }]}>
              {p1Name}  ·  {p2Name}
            </Text>
          </View>
          <View style={s.scoreRow}>
            <ScorePill label={labels.scoreLove} value={scores.love} isDark={isDark} />
            <ScorePill label={labels.scoreBreakup} value={scores.breakup} isDark={isDark} invert />
            <ScorePill label={labels.scoreLoyalty} value={scores.loyalty} isDark={isDark} />
            <ScorePill label={labels.scoreReturn} value={scores.return} isDark={isDark} />
            <ScorePill label={labels.scoreFuture} value={scores.future} isDark={isDark} />
          </View>
        </View>
      </LinearGradient>

      {sections.map((sec, idx) => (
        <SectionCard key={sec.id} sec={sec} idx={idx} isDark={isDark} text={text} dim={dim} lang={lang} />
      ))}
    </View>
  );
}

const s = StyleSheet.create({
  heroBorder: { borderRadius: 18, padding: 1.5 },
  hero: { borderRadius: 16, padding: 16, gap: 12 },
  heroTop: { gap: 6 },
  proBadge: {
    alignSelf: "flex-start",
    flexDirection: "row",
    alignItems: "center",
    gap: 5,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 999,
  },
  proBadgeTxt: { fontFamily: "Nunito_800ExtraBold", fontSize: 9, color: "#FBBF24", letterSpacing: 0.8 },
  heroTitle: { fontFamily: "Nunito_800ExtraBold", fontSize: 22, letterSpacing: -0.3 },
  heroNames: { fontFamily: "Nunito_600SemiBold", fontSize: 14 },
  scoreRow: { flexDirection: "row", flexWrap: "wrap", gap: 8 },
  scorePill: {
    borderWidth: 1,
    borderRadius: 12,
    paddingHorizontal: 10,
    paddingVertical: 8,
    minWidth: 88,
    gap: 4,
  },
  scoreLbl: { fontFamily: "Nunito_600SemiBold", fontSize: 10, textTransform: "uppercase", letterSpacing: 0.4 },
  scoreVal: { fontFamily: "Nunito_800ExtraBold", fontSize: 18 },
  barTrack: { height: 5, borderRadius: 999, overflow: "hidden", marginTop: 2 },
  barFill: { height: 5, borderRadius: 999 },
  cardBorder: { borderRadius: 16, padding: 1.2 },
  cardInner: { borderRadius: 14.5, padding: 14, gap: 10 },
  cardHead: { flexDirection: "row", gap: 10, alignItems: "flex-start" },
  numBadge: {
    width: 36,
    height: 36,
    borderRadius: 10,
    borderWidth: 1,
    alignItems: "center",
    justifyContent: "center",
  },
  secNum: { fontFamily: "Nunito_800ExtraBold", fontSize: 12 },
  titleRow: { flexDirection: "row", flexWrap: "wrap", gap: 6 },
  chip: {
    flexDirection: "row",
    alignItems: "center",
    gap: 4,
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 999,
  },
  chipTxt: { fontFamily: "Nunito_700Bold", fontSize: 9.5, letterSpacing: 0.3, textTransform: "uppercase" },
  secTitle: { fontFamily: "Nunito_800ExtraBold", fontSize: 16.5, lineHeight: 22 },
  secSub: { fontFamily: "Nunito_500Medium", fontSize: 12.5, lineHeight: 18 },
  bodyBox: {
    borderRadius: 12,
    padding: 12,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: "transparent",
  },
  body: { fontFamily: "Nunito_400Regular", fontSize: 14.5, lineHeight: 23 },
  bulletRow: { flexDirection: "row", gap: 8, alignItems: "flex-start" },
  bulletIcon: {
    width: 22,
    height: 22,
    borderRadius: 11,
    alignItems: "center",
    justifyContent: "center",
    marginTop: 1,
  },
  bulletTxt: { flex: 1, fontFamily: "Nunito_400Regular", fontSize: 14, lineHeight: 22 },
  metricRow: {
    borderRadius: 12,
    borderWidth: 1,
    padding: 10,
    gap: 6,
  },
  metricTop: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", gap: 8 },
  metricLabel: { flex: 1, fontFamily: "Nunito_600SemiBold", fontSize: 13 },
  metricScore: { fontFamily: "Nunito_800ExtraBold", fontSize: 14 },
  metricBand: { fontFamily: "Nunito_500Medium", fontSize: 11.5 },
  heroScoreBox: {
    borderRadius: 12,
    borderWidth: 1,
    padding: 12,
    alignItems: "center",
    gap: 2,
  },
  heroScoreLbl: { fontFamily: "Nunito_600SemiBold", fontSize: 11, textTransform: "uppercase", letterSpacing: 0.5 },
  heroScoreVal: { fontFamily: "Nunito_800ExtraBold", fontSize: 28 },
  tableCard: {
    borderRadius: 12,
    borderWidth: 1,
    padding: 10,
    gap: 4,
  },
  tableMain: { fontFamily: "Nunito_700Bold", fontSize: 13.5 },
  tableMeta: { flexDirection: "row", alignItems: "center", gap: 8, flexWrap: "wrap" },
  tableScore: { fontFamily: "Nunito_800ExtraBold", fontSize: 13 },
  tableNote: { fontFamily: "Nunito_500Medium", fontSize: 11.5, flex: 1 },
});
