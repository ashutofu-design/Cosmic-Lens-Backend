import { Feather } from "@expo/vector-icons";
import { BlurView } from "expo-blur";
import * as Haptics from "expo-haptics";
import { LinearGradient } from "expo-linear-gradient";
import { router, useLocalSearchParams } from "expo-router";
import React, { lazy, Suspense, useEffect, useRef, useState } from "react";
import {
  ActivityIndicator,
  Animated,
  Easing,
  Platform,
  Pressable,
  StyleSheet,
  Text,
  View,
} from "react-native";
import Svg, { Circle } from "react-native-svg";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { CosmicBg } from "@/components/CosmicBg";
import { useFeatureGate } from "@/components/FeatureGate";
import { useC } from "@/context/ThemeContext";
import { useUser } from "@/context/UserContext";
import { useT } from "@/hooks/useT";
import { API_BASE, userAuthHeaders } from "@/lib/apiConfig";
import {
  coerceLoveBasicLang,
  pickLoveBasicCopy,
  type LoveBasicLang,
} from "@/lib/loveRealityBasicLang";
import {
  humanizeDisplayText,
  loyaltyCompareVerdict,
  mapLoveRealityResult,
  type LoveCompatDetail,
  type FutureOutcomeDetail,
  type LoveRealityBasicDisplay,
  type LoveRealityToolKey,
  type LoyaltyCompareData,
} from "@/lib/loveRealityToolMappers";
import type { ChartProof } from "@/lib/loveRealityChartProof";
import { LOVE_REALITY_PRO_CTA_LABEL } from "@/lib/loveRealityProCopy";
import type { BirthData } from "@/types";

const AnimatedCircle = Animated.createAnimatedComponent(Circle);

const LoveRealityToolResultPanel = lazy(() =>
  import("@/components/loveReality/LoveRealityToolResultPanel").then(m => ({
    default: m.LoveRealityToolResultPanel,
  })),
);

export type LoveRealityToolConfig = {
  toolKey: LoveRealityToolKey;
  title: string;
  apiPath: string;
  featureGate: "love_reality_full" | "future_timeline_6m";
  loadingHint: string;
  accentGradient: [string, string];
};

function packPerson(bd: BirthData) {
  return {
    name: bd.name,
    day: bd.day,
    month: bd.month,
    year: bd.year,
    hour: bd.hour,
    minute: bd.minute,
    ampm: bd.ampm,
    lat: bd.lat,
    lon: bd.lon,
    tz: bd.tz,
    place: bd.place,
  };
}

function CircularScoreMeter({
  percent,
  isDark,
  glowColor,
  compact = false,
}: {
  percent: number;
  isDark: boolean;
  glowColor: string;
  compact?: boolean;
}) {
  const R = compact ? 54 : 88;
  const size = compact ? 128 : 200;
  const cx = size / 2;
  const circ = 2 * Math.PI * R;
  const anim = useRef(new Animated.Value(0)).current;
  const [display, setDisplay] = useState(0);

  useEffect(() => {
    anim.setValue(0);
    const sub = anim.addListener(({ value }) => setDisplay(Math.round(value)));
    Animated.timing(anim, {
      toValue: percent,
      duration: 1400,
      easing: Easing.out(Easing.cubic),
      useNativeDriver: false,
    }).start();
    return () => anim.removeListener(sub);
  }, [percent, anim]);

  const offset = anim.interpolate({
    inputRange: [0, 100],
    outputRange: [circ, 0],
  });

  const scoreColor = percent >= 67 ? "#4ade80" : percent >= 45 ? "#fbbf24" : "#f87171";

  return (
    <View style={[meterStyles.wrap, compact && meterStyles.wrapCompact]}>
      <View
        style={[
          meterStyles.glow,
          compact && meterStyles.glowCompact,
          {
            shadowColor: glowColor,
            backgroundColor: isDark ? "rgba(168,85,247,0.12)" : "rgba(124,58,237,0.08)",
          },
        ]}
      />
      <Svg width={size} height={size}>
        <Circle
          cx={cx}
          cy={cx}
          r={R}
          stroke={isDark ? "rgba(255,255,255,0.06)" : "rgba(15,23,42,0.08)"}
          strokeWidth={compact ? 10 : 14}
          fill="none"
        />
        <AnimatedCircle
          cx={cx}
          cy={cx}
          r={R}
          stroke={scoreColor}
          strokeWidth={compact ? 10 : 14}
          fill="none"
          strokeLinecap="round"
          strokeDasharray={`${circ} ${circ}`}
          strokeDashoffset={offset}
          transform={`rotate(-90 ${cx} ${cx})`}
        />
      </Svg>
      <View style={meterStyles.center}>
        <Text style={[meterStyles.pct, compact && meterStyles.pctCompact, { color: scoreColor }]}>
          {display}%
        </Text>
        <Text
          style={[
            meterStyles.lbl,
            compact && meterStyles.lblCompact,
            { color: isDark ? "rgba(203,213,225,0.55)" : "#64748B" },
          ]}
        >
          Match
        </Text>
      </View>
    </View>
  );
}

const meterStyles = StyleSheet.create({
  wrap: { width: 200, height: 200, alignItems: "center", justifyContent: "center" },
  wrapCompact: { width: 128, height: 128 },
  glow: {
    ...StyleSheet.absoluteFillObject,
    borderRadius: 100,
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.65,
    shadowRadius: 28,
    elevation: 12,
  },
  center: { position: "absolute", alignItems: "center" },
  pct: { fontSize: 44, fontFamily: "Nunito_800ExtraBold", letterSpacing: -1 },
  pctCompact: { fontSize: 28 },
  lbl: {
    fontSize: 11,
    fontFamily: "Nunito_600SemiBold",
    letterSpacing: 2,
    textTransform: "uppercase",
    marginTop: 2,
  },
  lblCompact: { fontSize: 9, letterSpacing: 1.2 },
  glowCompact: { borderRadius: 64, shadowRadius: 16 },
});

function RiskGaugeMeter({
  score,
  riskLevel,
  isDark,
  compact = false,
}: {
  score: number;
  riskLevel: string;
  isDark: boolean;
  compact?: boolean;
}) {
  const needle = useRef(new Animated.Value(0)).current;
  const [needlePct, setNeedlePct] = useState(33);

  useEffect(() => {
    const target = Math.max(0, Math.min(100, score)) / 100;
    needle.setValue(0);
    const id = needle.addListener(({ value }) => setNeedlePct(Math.round(value * 100)));
    Animated.timing(needle, {
      toValue: target,
      duration: 1200,
      easing: Easing.out(Easing.cubic),
      useNativeDriver: false,
    }).start();
    return () => needle.removeListener(id);
  }, [score, needle]);

  const zoneColor = riskLevel.includes("high")
    ? "#ef4444"
    : riskLevel.includes("low")
      ? "#22c55e"
      : "#fbbf24";

  return (
    <View style={[gaugeStyles.wrap, compact && gaugeStyles.wrapCompact]}>
      <Text style={[gaugeStyles.score, compact && gaugeStyles.scoreCompact, { color: zoneColor }]}>{score}</Text>
      <Text style={[gaugeStyles.riskTag, { color: zoneColor, borderColor: zoneColor + "55" }]}>
        {humanizeDisplayText(riskLevel).toUpperCase()} RISK
      </Text>
      <View style={[gaugeStyles.track, { backgroundColor: isDark ? "rgba(255,255,255,0.06)" : "rgba(0,0,0,0.06)" }]}>
        <LinearGradient
          colors={["#22c55e", "#fbbf24", "#ef4444"]}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 0 }}
          style={gaugeStyles.fill}
        />
        <View style={[gaugeStyles.needle, { left: `${needlePct}%` }]} />
      </View>
      <View style={gaugeStyles.labels}>
        {(["LOW", "MEDIUM", "HIGH"] as const).map(z => (
          <Text key={z} style={[gaugeStyles.zoneLbl, { color: isDark ? "rgba(203,213,225,0.45)" : "#94a3b8" }]}>
            {z}
          </Text>
        ))}
      </View>
    </View>
  );
}

const gaugeStyles = StyleSheet.create({
  wrap: { width: "100%", maxWidth: 300, alignItems: "center", gap: 10 },
  wrapCompact: { maxWidth: 280, gap: 6 },
  score: { fontSize: 48, fontFamily: "Nunito_800ExtraBold", letterSpacing: -2 },
  scoreCompact: { fontSize: 34 },
  riskTag: {
    fontSize: 10,
    fontFamily: "Nunito_800ExtraBold",
    letterSpacing: 1.5,
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 8,
    borderWidth: 1,
  },
  track: { width: "100%", height: 14, borderRadius: 7, overflow: "visible", marginTop: 4 },
  fill: { ...StyleSheet.absoluteFillObject, borderRadius: 7 },
  needle: {
    position: "absolute",
    top: -5,
    width: 4,
    height: 24,
    marginLeft: -2,
    borderRadius: 2,
    backgroundColor: "#fff",
    shadowColor: "#fff",
    shadowOpacity: 0.9,
    shadowRadius: 6,
    elevation: 4,
  },
  labels: { flexDirection: "row", justifyContent: "space-between", width: "100%", paddingHorizontal: 2 },
  zoneLbl: { fontSize: 9, fontFamily: "Nunito_700Bold", letterSpacing: 0.8 },
});

function StatusDestinyCard({
  label,
  accent,
  isDark,
  compact = false,
}: {
  label: string;
  accent: string;
  isDark: boolean;
  compact?: boolean;
}) {
  const pulse = useRef(new Animated.Value(0.35)).current;
  useEffect(() => {
    const loop = Animated.loop(
      Animated.sequence([
        Animated.timing(pulse, { toValue: 0.7, duration: 2200, easing: Easing.inOut(Easing.sin), useNativeDriver: true }),
        Animated.timing(pulse, { toValue: 0.35, duration: 2200, easing: Easing.inOut(Easing.sin), useNativeDriver: true }),
      ]),
    );
    loop.start();
    return () => loop.stop();
  }, [pulse]);

  return (
    <View style={[statusStyles.wrap, compact && statusStyles.wrapCompact]}>
      <Animated.View
        style={[statusStyles.outerGlow, { opacity: pulse, shadowColor: accent, backgroundColor: accent + "18" }]}
      />
      <LinearGradient
        colors={isDark ? ["rgba(15,10,30,0.95)", "rgba(20,15,40,0.9)"] : ["#faf5ff", "#fff"]}
        style={[statusStyles.card, compact && statusStyles.cardCompact, { borderColor: accent + "45" }]}
      >
        <Text style={[statusStyles.eyebrow, { color: accent }]}>COSMIC SIGNAL</Text>
        <Text
          style={[statusStyles.label, compact && statusStyles.labelCompact, { color: isDark ? "#fff" : "#0F172A" }]}
          numberOfLines={2}
        >
          {label}
        </Text>
      </LinearGradient>
    </View>
  );
}

const statusStyles = StyleSheet.create({
  wrap: { width: "100%", maxWidth: 320, alignItems: "center" },
  wrapCompact: { maxWidth: 280 },
  cardCompact: { paddingVertical: 16, paddingHorizontal: 16 },
  labelCompact: { fontSize: 20, lineHeight: 26 },
  outerGlow: {
    ...StyleSheet.absoluteFillObject,
    borderRadius: 24,
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.8,
    shadowRadius: 24,
  },
  card: {
    width: "100%",
    borderRadius: 22,
    borderWidth: 1.5,
    paddingVertical: 28,
    paddingHorizontal: 22,
    alignItems: "center",
    gap: 8,
  },
  eyebrow: { fontSize: 10, fontFamily: "Nunito_800ExtraBold", letterSpacing: 2.2 },
  label: { fontSize: 26, fontFamily: "Nunito_800ExtraBold", textAlign: "center", lineHeight: 34, letterSpacing: -0.5 },
});

function loyaltyBarColor(score: number): string {
  if (score >= 72) return "#22c55e";
  if (score >= 52) return "#fbbf24";
  if (score >= 35) return "#fb923c";
  return "#ef4444";
}

function loyaltyLevelShort(level: string): string {
  switch (level) {
    case "high":
      return "Strong";
    case "moderate":
      return "Moderate";
    case "unstable":
      return "Weak";
    case "risky":
      return "Risky";
    default:
      return humanizeDisplayText(level) || "—";
  }
}

export function LoyaltyCompareCard({
  compare,
  youName,
  partnerName,
  isDark,
  compact = false,
  lang = "en",
}: {
  compare: LoyaltyCompareData;
  youName: string;
  partnerName: string;
  isDark: boolean;
  compact?: boolean;
  lang?: LoveBasicLang;
}) {
  const lane = coerceLoveBasicLang(lang);
  const you = youName.trim() || pickLoveBasicCopy(lane, "You", "Aap", "आप");
  const partner = partnerName.trim() || pickLoveBasicCopy(lane, "Partner", "Partner", "साथी");
  const verdict = loyaltyCompareVerdict(compare, you, partner, lane);
  const textHi = isDark ? "#fff" : "#0F172A";
  const textLo = isDark ? "rgba(203,213,225,0.65)" : "#64748B";
  const cardBg = isDark ? "rgba(255,255,255,0.04)" : "rgba(15,23,42,0.03)";
  const border = isDark ? "rgba(255,255,255,0.1)" : "rgba(15,23,42,0.08)";

  const rows = [
    {
      key: "you" as const,
      label: you,
      sub: pickLoveBasicCopy(lane, "You", "Aap", "आप"),
      score: compare.youScore,
      level: compare.youLevel,
      isHigher: compare.higherSide === "you",
    },
    {
      key: "partner" as const,
      label: partner,
      sub: pickLoveBasicCopy(lane, "Partner", "Partner", "साथी"),
      score: compare.partnerScore,
      level: compare.partnerLevel,
      isHigher: compare.higherSide === "partner",
    },
  ];

  return (
    <View style={[loyaltyCmpStyles.wrap, compact && loyaltyCmpStyles.wrapCompact]}>
      <Text style={[loyaltyCmpStyles.verdict, { color: textHi }]}>{verdict}</Text>
      <View style={[loyaltyCmpStyles.card, { backgroundColor: cardBg, borderColor: border }]}>
        {rows.map(row => {
          const color = loyaltyBarColor(row.score);
          return (
            <View key={row.key} style={loyaltyCmpStyles.row}>
              <View style={loyaltyCmpStyles.rowHead}>
                <View style={{ flex: 1 }}>
                  <Text style={[loyaltyCmpStyles.name, { color: textHi }]} numberOfLines={1}>
                    {row.label}
                  </Text>
                  <Text style={[loyaltyCmpStyles.sub, { color: textLo }]}>{row.sub}</Text>
                </View>
                <View style={loyaltyCmpStyles.scoreCol}>
                  <Text style={[loyaltyCmpStyles.score, { color }]}>{row.score}</Text>
                  <Text style={[loyaltyCmpStyles.level, { color: textLo }]}>
                    {loyaltyLevelShort(row.level)}
                  </Text>
                </View>
                {row.isHigher && compare.higherSide !== "tie" ? (
                  <View style={[loyaltyCmpStyles.badge, { backgroundColor: color + "22", borderColor: color + "55" }]}>
                    <Text style={[loyaltyCmpStyles.badgeTxt, { color }]}>
                      {pickLoveBasicCopy(lane, "Higher", "Zyada", "ज़्यादा")}
                    </Text>
                  </View>
                ) : compare.higherSide === "tie" ? (
                  <View style={[loyaltyCmpStyles.badge, { backgroundColor: border, borderColor: border }]}>
                    <Text style={[loyaltyCmpStyles.badgeTxt, { color: textLo }]}>
                      {pickLoveBasicCopy(lane, "Equal", "Barabar", "बराबर")}
                    </Text>
                  </View>
                ) : (
                  <View style={{ width: 52 }} />
                )}
              </View>
              <View style={[loyaltyCmpStyles.track, { backgroundColor: isDark ? "rgba(255,255,255,0.06)" : "rgba(0,0,0,0.06)" }]}>
                <View style={[loyaltyCmpStyles.fill, { width: `${row.score}%`, backgroundColor: color }]} />
              </View>
            </View>
          );
        })}
      </View>
    </View>
  );
}

const loyaltyCmpStyles = StyleSheet.create({
  wrap: { width: "100%", maxWidth: 320, gap: 10, marginTop: 14 },
  wrapCompact: { maxWidth: 280, marginTop: 10 },
  title: { fontSize: 14, fontFamily: "Nunito_800ExtraBold", letterSpacing: 0.2, textAlign: "center" },
  estBadge: {
    fontSize: 10,
    fontFamily: "Nunito_600SemiBold",
    textAlign: "center",
    lineHeight: 14,
    paddingHorizontal: 8,
  },
  card: { borderRadius: 16, borderWidth: 1, padding: 12, gap: 14 },
  row: { gap: 6 },
  rowHead: { flexDirection: "row", alignItems: "center", gap: 8 },
  name: { fontSize: 14, fontFamily: "Nunito_700Bold" },
  sub: { fontSize: 10, fontFamily: "Nunito_600SemiBold", marginTop: 1 },
  scoreCol: { alignItems: "flex-end", minWidth: 44 },
  score: { fontSize: 18, fontFamily: "Nunito_800ExtraBold", letterSpacing: -0.5 },
  level: { fontSize: 9, fontFamily: "Nunito_700Bold", letterSpacing: 0.5, textTransform: "uppercase" },
  badge: {
    borderWidth: 1,
    borderRadius: 8,
    paddingHorizontal: 8,
    paddingVertical: 3,
    minWidth: 52,
    alignItems: "center",
  },
  badgeTxt: { fontSize: 10, fontFamily: "Nunito_800ExtraBold", letterSpacing: 0.3 },
  track: { height: 8, borderRadius: 4, overflow: "hidden" },
  fill: { height: "100%", borderRadius: 4 },
  verdict: {
    fontSize: 13,
    fontFamily: "Nunito_600SemiBold",
    lineHeight: 19,
    textAlign: "center",
    paddingHorizontal: 4,
  },
});

function barColor(score: number): string {
  if (score >= 67) return "#22c55e";
  if (score >= 45) return "#fbbf24";
  return "#f87171";
}

function riskLevelLabel(risk?: string): string | null {
  if (!risk) return null;
  const r = risk.toLowerCase();
  if (r.includes("very high")) return "High friction";
  if (r.includes("high")) return "Some friction";
  if (r.includes("medium")) return "Mixed bond";
  if (r.includes("low")) return "Strong bond";
  return risk;
}

export function LoveCompatibilityDetailCard({
  detail,
  isDark,
  compact = false,
}: {
  detail: LoveCompatDetail;
  isDark: boolean;
  compact?: boolean;
}) {
  const textHi = isDark ? "#fff" : "#0F172A";
  const cardBg = isDark ? "rgba(255,255,255,0.04)" : "rgba(15,23,42,0.03)";
  const border = isDark ? "rgba(255,255,255,0.1)" : "rgba(15,23,42,0.08)";

  return (
    <View style={[loveDetStyles.wrap, compact && loveDetStyles.wrapCompact]}>
      <Text style={[loveDetStyles.sectionTitle, { color: textHi }]}>Love dimensions</Text>
      <View style={[loveDetStyles.card, { backgroundColor: cardBg, borderColor: border }]}>
        {detail.dimensions.map(dim => {
          const color = barColor(dim.score);
          return (
            <View key={dim.key} style={loveDetStyles.dimRow}>
              <View style={loveDetStyles.dimHead}>
                <Text style={[loveDetStyles.dimLbl, { color: textHi }]}>{dim.label}</Text>
                <Text style={[loveDetStyles.dimScore, { color }]}>{dim.score}</Text>
              </View>
              <View style={[loveDetStyles.track, { backgroundColor: isDark ? "rgba(255,255,255,0.06)" : "rgba(0,0,0,0.06)" }]}>
                <View style={[loveDetStyles.fill, { width: `${dim.score}%`, backgroundColor: color }]} />
              </View>
            </View>
          );
        })}
      </View>
    </View>
  );
}

export function FutureOutcomeDetailCard({
  detail,
  isDark,
  compact = false,
}: {
  detail: FutureOutcomeDetail;
  isDark: boolean;
  compact?: boolean;
}) {
  const textHi = isDark ? "#fff" : "#0F172A";
  const textLo = isDark ? "rgba(203,213,225,0.65)" : "#64748B";

  return (
    <View style={[loveDetStyles.wrap, compact && loveDetStyles.wrapCompact]}>
      <Text style={[loveDetStyles.summary, { color: textHi }]}>{detail.verdictLine}</Text>
      {detail.reasonLine ? (
        <Text style={[loveDetStyles.reason, { color: textLo, textAlign: "center", paddingHorizontal: 8 }]}>
          {detail.reasonLine}
        </Text>
      ) : null}
    </View>
  );
}

const loveDetStyles = StyleSheet.create({
  wrap: { width: "100%", maxWidth: 320, gap: 10, marginTop: 12 },
  wrapCompact: { maxWidth: 280, marginTop: 8 },
  summary: {
    fontSize: 13,
    fontFamily: "Nunito_600SemiBold",
    lineHeight: 19,
    textAlign: "center",
    paddingHorizontal: 6,
  },
  bondBadge: {
    alignSelf: "center",
    borderWidth: 1,
    borderRadius: 999,
    paddingHorizontal: 12,
    paddingVertical: 4,
  },
  bondTxt: { fontSize: 10, fontFamily: "Nunito_800ExtraBold", letterSpacing: 0.8, textTransform: "uppercase" },
  sectionTitle: {
    fontSize: 12,
    fontFamily: "Nunito_800ExtraBold",
    letterSpacing: 0.3,
    textAlign: "center",
  },
  card: { borderRadius: 16, borderWidth: 1, padding: 12, gap: 10 },
  dimRow: { gap: 5 },
  dimHead: { flexDirection: "row", justifyContent: "space-between", alignItems: "center" },
  dimLbl: { fontSize: 12, fontFamily: "Nunito_700Bold" },
  dimScore: { fontSize: 13, fontFamily: "Nunito_800ExtraBold" },
  track: { height: 7, borderRadius: 4, overflow: "hidden" },
  fill: { height: "100%", borderRadius: 4 },
  reason: { fontSize: 11, fontFamily: "Nunito_600SemiBold", lineHeight: 16 },
});

export function ChartProofPanel({
  proof,
  isDark,
  compact = false,
}: {
  proof: ChartProof;
  isDark: boolean;
  compact?: boolean;
}) {
  const textHi = isDark ? "#fff" : "#0F172A";
  const textLo = isDark ? "rgba(203,213,225,0.65)" : "#64748B";
  const border = isDark ? "rgba(255,255,255,0.1)" : "rgba(15,23,42,0.08)";
  const cardBg = isDark ? "rgba(255,255,255,0.04)" : "rgba(15,23,42,0.03)";

  return (
    <View style={[proofStyles.wrap, compact && proofStyles.wrapCompact]}>
      <Text style={[proofStyles.title, { color: textHi }]}>Chart proof (D1 + D9)</Text>
      {proof.aspectBadges.length > 0 ? (
        <View style={proofStyles.badgeRow}>
          {proof.aspectBadges.map((b, i) => (
            <View key={i} style={[proofStyles.badge, { borderColor: border, backgroundColor: cardBg }]}>
              <Text style={[proofStyles.badgeTxt, { color: textLo }]}>
                {b.icon} {b.label}
              </Text>
            </View>
          ))}
        </View>
      ) : null}
      <View style={[proofStyles.card, { borderColor: border, backgroundColor: cardBg }]}>
        <Text style={[proofStyles.person, { color: "#f472b6" }]}>{proof.p1Name}</Text>
        {proof.p1Rows.map((r, i) => (
          <Text key={`p1-${i}`} style={[proofStyles.line, { color: textLo }]}>
            {r.line}
            {r.tag ? ` · ${r.tag}` : ""}
          </Text>
        ))}
        <View style={[proofStyles.divider, { backgroundColor: border }]} />
        <Text style={[proofStyles.person, { color: "#c084fc" }]}>{proof.p2Name}</Text>
        {proof.p2Rows.map((r, i) => (
          <Text key={`p2-${i}`} style={[proofStyles.line, { color: textLo }]}>
            {r.line}
            {r.tag ? ` · ${r.tag}` : ""}
          </Text>
        ))}
      </View>
    </View>
  );
}

const proofStyles = StyleSheet.create({
  wrap: { width: "100%", maxWidth: 320, gap: 8, marginTop: 10 },
  wrapCompact: { maxWidth: 280 },
  title: { fontSize: 12, fontFamily: "Nunito_800ExtraBold", textAlign: "center", letterSpacing: 0.3 },
  badgeRow: { gap: 6 },
  badge: { borderWidth: 1, borderRadius: 10, paddingHorizontal: 10, paddingVertical: 6 },
  badgeTxt: { fontSize: 10, fontFamily: "Nunito_600SemiBold", lineHeight: 14 },
  card: { borderWidth: 1, borderRadius: 14, padding: 12, gap: 4 },
  person: { fontSize: 11, fontFamily: "Nunito_800ExtraBold", marginBottom: 2 },
  line: { fontSize: 10, fontFamily: "Nunito_600SemiBold", lineHeight: 14 },
  divider: { height: 1, marginVertical: 6 },
});

export function LoveRealityResultHero({
  display,
  isDark,
  accentGradient,
  compact = false,
  youName,
  partnerName,
  hideLoyaltyCompare = false,
  lang = "en",
}: {
  display: LoveRealityBasicDisplay;
  isDark: boolean;
  accentGradient: [string, string];
  compact?: boolean;
  youName?: string;
  partnerName?: string;
  hideLoyaltyCompare?: boolean;
  lang?: LoveBasicLang;
}) {
  const lane = coerceLoveBasicLang(lang);
  if (display.visual === "circular" && display.percent != null) {
    return (
      <View style={{ width: "100%", alignItems: "center" }}>
        <CircularScoreMeter
          percent={display.percent}
          isDark={isDark}
          glowColor={accentGradient[0]}
          compact={compact}
        />
      </View>
    );
  }
  if (display.visual === "risk-gauge") {
    return (
      <RiskGaugeMeter
        score={display.riskScore ?? 50}
        riskLevel={display.riskLevel ?? "medium"}
        isDark={isDark}
        compact={compact}
      />
    );
  }
  return (
    <View style={{ width: "100%", alignItems: "center" }}>
      <StatusDestinyCard
        label={display.statusLabel ?? "Cosmic Reading"}
        accent={display.statusAccent ?? accentGradient[0]}
        isDark={isDark}
        compact={compact}
      />
      {display.loyaltyCompare && !hideLoyaltyCompare ? (
        <LoyaltyCompareCard
          compare={display.loyaltyCompare}
          youName={youName ?? pickLoveBasicCopy(lane, "You", "Aap", "आप")}
          partnerName={partnerName ?? pickLoveBasicCopy(lane, "Partner", "Partner", "साथी")}
          isDark={isDark}
          compact={compact}
          lang={lane}
        />
      ) : null}
    </View>
  );
}

function ProUpsellBanner({
  isDark,
  bottomPad,
  onPress,
}: {
  isDark: boolean;
  bottomPad: number;
  onPress: () => void;
}) {
  const glassBg = isDark ? "rgba(12,8,28,0.72)" : "rgba(255,255,255,0.82)";
  const borderC = isDark ? "rgba(168,85,247,0.35)" : "rgba(124,58,237,0.22)";

  return (
    <View style={[upsellStyles.wrap, { paddingBottom: bottomPad + 12 }]}>
      <Pressable onPress={onPress} style={({ pressed }) => ({ opacity: pressed ? 0.92 : 1 })}>
        <View style={[upsellStyles.card, { borderColor: borderC }]}>
          {Platform.OS !== "web" ? (
            <BlurView intensity={isDark ? 40 : 60} tint={isDark ? "dark" : "light"} style={StyleSheet.absoluteFill} />
          ) : null}
          <View style={[StyleSheet.absoluteFill, { backgroundColor: glassBg }]} />
          <View style={upsellStyles.inner}>
            <Text style={[upsellStyles.headline, { color: isDark ? "#fff" : "#0F172A" }]}>
              Want the complete 14-page truth?
            </Text>
            <Text style={[upsellStyles.sub, { color: isDark ? "rgba(203,213,225,0.65)" : "#64748B" }]}>
              Reveal hidden red flags, exact monthly timelines, and Vedic remedies.
            </Text>
            <LinearGradient
              colors={["#f59e0b", "#ec4899", "#9333ea"]}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 0 }}
              style={upsellStyles.btn}
            >
              <Feather name="file-text" size={16} color="#fff" />
              <Text style={upsellStyles.btnTxt}>{LOVE_REALITY_PRO_CTA_LABEL}</Text>
            </LinearGradient>
          </View>
        </View>
      </Pressable>
    </View>
  );
}

const upsellStyles = StyleSheet.create({
  wrap: { paddingHorizontal: 16, paddingTop: 8 },
  card: { borderRadius: 20, borderWidth: 1, overflow: "hidden" },
  inner: { padding: 16, gap: 8 },
  headline: { fontSize: 15, fontFamily: "Nunito_800ExtraBold", letterSpacing: -0.2 },
  sub: { fontSize: 12, fontFamily: "Nunito_500Medium", lineHeight: 18 },
  btn: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
    paddingVertical: 14,
    borderRadius: 14,
    marginTop: 6,
  },
  btnTxt: { color: "#fff", fontSize: 12, fontFamily: "Nunito_800ExtraBold", letterSpacing: 0.2, textAlign: "center", flexShrink: 1 },
});

export function LoveRealityBasicScreen({ config }: { config: LoveRealityToolConfig }) {
  const C = useC();
  const t = useT();
  const isDark = C.isDark;
  const insets = useSafeAreaInsets();
  const topPad = Platform.OS === "android" ? Math.max(insets.top, 24) : insets.top;
  const { LockOverlay } = useFeatureGate(config.featureGate);

  const { profiles, primaryProfileId, language, user } = useUser();
  const params = useLocalSearchParams<{ partnerId?: string }>();
  const partnerId = typeof params.partnerId === "string" ? params.partnerId : null;

  const primaryProfile = profiles.find(p => p.id === primaryProfileId) ?? profiles[0] ?? null;
  const partnerProfile = partnerId ? (profiles.find(p => p.id === partnerId) ?? null) : null;

  const hasSelfKundli = !!primaryProfile?.kundli && !!primaryProfile?.birthData;
  const hasPartnerKundli = !!partnerProfile?.kundli && !!partnerProfile?.birthData;
  const canAnalyze = hasSelfKundli && hasPartnerKundli;

  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [display, setDisplay] = useState<LoveRealityBasicDisplay | null>(null);

  const textHi = isDark ? "#fff" : "#0F172A";
  const textLo = isDark ? "rgba(203,213,225,0.65)" : "#64748B";
  const border = isDark ? "rgba(255,255,255,0.1)" : "rgba(15,23,42,0.08)";

  const didRun = useRef(false);
  useEffect(() => {
    if (didRun.current || !canAnalyze) return;
    didRun.current = true;
    runAnalysis();
  }, [canAnalyze]);

  async function runAnalysis() {
    if (!primaryProfile?.birthData || !partnerProfile?.birthData) return;
    setErr(null);
    setDisplay(null);
    setLoading(true);
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    try {
      const ctrl = new AbortController();
      const timer = setTimeout(() => ctrl.abort(), 30000);
      const resp = await fetch(`${API_BASE}${config.apiPath}`, {
        method: "POST",
        headers: { ...userAuthHeaders(user), "Content-Type": "application/json" },
        body: JSON.stringify({
          p1: packPerson(primaryProfile.birthData),
          p2: packPerson(partnerProfile.birthData),
        }),
        signal: ctrl.signal,
      });
      clearTimeout(timer);
      const json = await resp.json();
      if (!resp.ok || json.error) throw new Error(json.error || "Analysis failed");
      setDisplay(mapLoveRealityResult(config.toolKey, json as Record<string, unknown>, language));
      // chart_proof attached by backend engines
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
    } catch (e: unknown) {
      setErr(e instanceof Error ? e.message : "Could not analyze. Please try again.");
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
    } finally {
      setLoading(false);
    }
  }

  function openProPdf() {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    router.push({
      pathname: "/love-reality-pro",
      params: { partnerId: partnerId ?? "" },
    } as never);
  }

  const showResult = canAnalyze && !loading && !err && display;

  return (
    <CosmicBg>
      <View style={[styles.root, { paddingTop: topPad }]}>
        <View style={styles.center}>
          {!canAnalyze && (
            <View style={styles.stateBlock}>
              <Feather name="lock" size={28} color="#f472b6" />
              <Text style={[styles.stateTitle, { color: textHi }]}>{t.needKundli}</Text>
              <Text style={[styles.stateSub, { color: textLo }]}>
                {!hasSelfKundli ? t.needKundliSub : t.needPartnerKundli}
              </Text>
              <Pressable onPress={() => router.replace("/relationship" as never)} style={{ marginTop: 12, width: "100%" }}>
                <LinearGradient colors={config.accentGradient} style={styles.retryBtn}>
                  <Text style={styles.retryTxt}>Go to Relationship</Text>
                </LinearGradient>
              </Pressable>
            </View>
          )}

          {canAnalyze && loading && (
            <View style={styles.stateBlock}>
              <ActivityIndicator size="large" color={config.accentGradient[0]} />
              <Text style={[styles.stateTitle, { color: textHi }]}>Reading both kundlis…</Text>
              <Text style={[styles.stateSub, { color: textLo }]}>{config.loadingHint}</Text>
            </View>
          )}

          {canAnalyze && !loading && err && (
            <View style={styles.stateBlock}>
              <Feather name="alert-circle" size={26} color="#ef4444" />
              <Text style={[styles.stateSub, { color: textHi, textAlign: "center" }]}>{err}</Text>
              <Pressable onPress={runAnalysis} style={{ marginTop: 12, width: "100%" }}>
                <LinearGradient colors={config.accentGradient} style={styles.retryBtn}>
                  <Text style={styles.retryTxt}>Retry</Text>
                </LinearGradient>
              </Pressable>
            </View>
          )}

          {showResult && display && primaryProfile && partnerProfile && (
            <Suspense
              fallback={
                <View style={styles.stateBlock}>
                  <ActivityIndicator size="large" color={config.accentGradient[0]} />
                </View>
              }
            >
              <LoveRealityToolResultPanel
                toolKey={config.toolKey}
                toolTitle={config.title}
                userName={primaryProfile.name || "You"}
                partnerName={partnerProfile.name || "Partner"}
                display={display}
              loyaltyCompare={display.loyaltyCompare}
              isDark={isDark}
              bottomPad={insets.bottom}
              accentGradient={config.accentGradient}
              onOpenPro={openProPdf}
              showHeader
              onBack={() => router.back()}
              onRefresh={runAnalysis}
              refreshing={loading}
            />
            </Suspense>
          )}
        </View>
      </View>
      {LockOverlay}
    </CosmicBg>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1 },
  header: {
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: 16,
    paddingBottom: 10,
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
  title: { flex: 1, fontSize: 18, fontFamily: "Nunito_700Bold", letterSpacing: -0.3, textAlign: "center" },
  partnerBadge: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    marginHorizontal: 16,
    marginBottom: 8,
    paddingVertical: 10,
    paddingHorizontal: 14,
    borderRadius: 14,
    borderWidth: 1,
    overflow: "hidden",
  },
  partnerTxt: { flex: 1, fontSize: 12, fontFamily: "Nunito_600SemiBold" },
  center: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    paddingHorizontal: 20,
    gap: 16,
    minHeight: 0,
  },
  hook: {
    fontSize: 14,
    fontFamily: "Nunito_600SemiBold",
    fontStyle: "italic",
    textAlign: "center",
    lineHeight: 21,
    maxWidth: 340,
    paddingHorizontal: 4,
  },
  stateBlock: { alignItems: "center", gap: 10, width: "100%", maxWidth: 320 },
  stateTitle: { fontSize: 16, fontFamily: "Nunito_700Bold" },
  stateSub: { fontSize: 13, fontFamily: "Nunito_500Medium", textAlign: "center", lineHeight: 19 },
  retryBtn: { paddingVertical: 14, borderRadius: 14, alignItems: "center" },
  retryTxt: { color: "#fff", fontSize: 14, fontFamily: "Nunito_700Bold" },
});
