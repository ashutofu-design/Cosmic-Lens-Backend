import { Feather } from "@expo/vector-icons";
import * as Haptics from "expo-haptics";
import { LinearGradient } from "expo-linear-gradient";
import { router } from "expo-router";
import React, { useEffect, useState } from "react";
import {
  ActivityIndicator,
  Platform,
  Pressable,
  ScrollView,
  StatusBar,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { CosmicBg } from "@/components/CosmicBg";
import Svg, { Circle, Defs, Line, LinearGradient as SvgGrad, Path, Stop, Text as SvgText } from "react-native-svg";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useC } from "@/context/ThemeContext";
import { useUser } from "@/context/UserContext";
import { getT } from "@/lib/i18n";
import {
  computeProInsight,
  generatePDForecast,
  pName,
  type MonthForecast,
  type PDForecast,
  type ProInsight,
} from "@/lib/proInsightEngine";

type Category = "career" | "relationship" | "finance" | "health";

const CATEGORY_META: { key: Category; icon: string; color: string }[] = [
  { key: "career",       icon: "💼", color: "#f59e0b" },
  { key: "relationship", icon: "💞", color: "#ec4899" },
  { key: "finance",      icon: "💰", color: "#4ade80" },
  { key: "health",       icon: "🌿", color: "#fbbf24" },
];

const PLANET_CLR: Record<string, string> = {
  Sun:"#f59e0b", Moon:"#94a3b8", Mars:"#ef4444", Mercury:"#10b981",
  Jupiter:"#facc15", Venus:"#ec4899", Saturn:"#a78bfa",
  Rahu:"#f59e0b", Ketu:"#fb923c",
};

function formatDate(d: Date | null): string {
  if (!d) return "";
  return `${d.toLocaleString("default", { month: "short" })} ${d.getDate()}, ${d.getFullYear()}`;
}

function fmtPDDate(d: Date): string {
  return `${String(d.getDate()).padStart(2,"0")}/${String(d.getMonth()+1).padStart(2,"0")}/${d.getFullYear().toString().slice(2)}`;
}

// ── 6-month line chart ─────────────────────────────────────────────────────────
function LineChart({ months, scores, color }: { months: string[]; scores: number[]; color: string }) {
  const C = useC();
  const W = 300, H = 120, PAD_L = 30, PAD_R = 12, PAD_T = 10, PAD_B = 28;
  const chartW = W - PAD_L - PAD_R;
  const chartH = H - PAD_T - PAD_B;

  const pts = scores.map((s, i) => {
    const x = PAD_L + (i / (scores.length - 1)) * chartW;
    const y = PAD_T + (1 - s / 100) * chartH;
    return { x, y, s };
  });

  let smoothPath = `M ${pts[0].x} ${pts[0].y}`;
  for (let i = 1; i < pts.length; i++) {
    const cp = { x: (pts[i-1].x + pts[i].x) / 2, y: (pts[i-1].y + pts[i].y) / 2 };
    smoothPath += ` Q ${pts[i-1].x} ${pts[i-1].y} ${cp.x} ${cp.y}`;
  }
  smoothPath += ` L ${pts[pts.length-1].x} ${pts[pts.length-1].y}`;
  const areaPath = smoothPath + ` L ${pts[pts.length-1].x} ${PAD_T+chartH} L ${pts[0].x} ${PAD_T+chartH} Z`;

  return (
    <Svg width={W} height={H}>
      <Defs>
        <SvgGrad id="area" x1="0" y1="0" x2="0" y2="1">
          <Stop offset="0" stopColor={color} stopOpacity={0.25} />
          <Stop offset="1" stopColor={color} stopOpacity={0.0} />
        </SvgGrad>
      </Defs>
      {[25, 50, 75].map(v => (
        <Line
          key={v}
          x1={PAD_L} y1={PAD_T + (1 - v/100)*chartH}
          x2={W - PAD_R} y2={PAD_T + (1 - v/100)*chartH}
          stroke={C.border3} strokeWidth={1}
        />
      ))}
      <Path d={areaPath} fill="url(#area)" />
      <Path d={smoothPath} fill="none" stroke={color} strokeWidth={2} strokeLinecap="round" />
      {pts.map((p, i) => (
        <React.Fragment key={i}>
          <Circle cx={p.x} cy={p.y} r={4} fill={color} />
          <SvgText x={p.x} y={p.y - 9} fontSize={8} fill={color} textAnchor="middle" fontWeight="bold">
            {p.s}
          </SvgText>
          <SvgText x={p.x} y={H - 6} fontSize={9} fill={C.textDim} textAnchor="middle">
            {months[i]}
          </SvgText>
        </React.Fragment>
      ))}
      {[25, 50, 75].map(v => (
        <SvgText key={v} x={PAD_L - 4} y={PAD_T + (1 - v/100)*chartH + 3.5} fontSize={7} fill={C.textDim} textAnchor="end">
          {v}
        </SvgText>
      ))}
    </Svg>
  );
}

// ── Score Ring ─────────────────────────────────────────────────────────────────
function ScoreRing({ score, color }: { score: number; color: string }) {
  const C = useC();
  const R = 28, STROKE = 5;
  const circ = 2 * Math.PI * R;
  const dash = (score / 100) * circ;
  return (
    <Svg width={70} height={70}>
      <Circle cx={35} cy={35} r={R} fill="none" stroke={C.border} strokeWidth={STROKE} />
      <Circle
        cx={35} cy={35} r={R} fill="none"
        stroke={color} strokeWidth={STROKE}
        strokeDasharray={`${dash} ${circ - dash}`}
        strokeLinecap="round"
        rotation={-90} origin="35,35"
      />
      <SvgText x={35} y={39} fontSize={14} fontWeight="bold" fill={color} textAnchor="middle">{score}</SvgText>
    </Svg>
  );
}

// ── Reason item ────────────────────────────────────────────────────────────────
function ReasonItem({ text, color }: { text: string; color: string }) {
  const C = useC();
  const isBad = text.toLowerCase().includes("stress") ||
                text.toLowerCase().includes("weaken") ||
                text.toLowerCase().includes("debilitat") ||
                text.toLowerCase().includes("obstacle") ||
                text.toLowerCase().includes("sade sati") ||
                text.toLowerCase().includes("dusthana") ||
                text.toLowerCase().includes("challenged") ||
                text.toLowerCase().includes("friction") ||
                text.toLowerCase().includes("pressure");
  const dotColor = isBad ? "#ef4444" : "#4ade80";
  return (
    <View style={s.reasonItem}>
      <View style={[s.reasonDot, { backgroundColor: dotColor }]} />
      <Text style={[s.reasonText, { color: C.textMuted }]}>{text}</Text>
    </View>
  );
}

export default function InsightsScreen() {
  const insets    = useSafeAreaInsets();
  const C         = useC();
  const { kundli, moonData, language } = useUser();
  const t         = getT(language);
  const CATEGORIES = CATEGORY_META.map(c => ({
    ...c,
    label: t[c.key as "career" | "finance" | "relationship" | "health"],
  }));
  const androidSB = StatusBar.currentHeight ?? 24;
  const topPad    = Platform.OS === "web" ? 67 : Platform.OS === "android" ? Math.max(insets.top, androidSB) : insets.top;
  const botPad    = Platform.OS === "web" ? 34 : insets.bottom;
  const showDemo  = !kundli;

  const [cat, setCat]                           = useState<Category>("career");
  const [insight, setInsight]                   = useState<ProInsight | null>(null);
  const [forecast, setForecast]                 = useState<MonthForecast | null>(null);
  const [forecastLoading, setForecastLoading]   = useState(false);

  useEffect(() => {
    if (!kundli) return;
    const moonLon = moonData?.longitude ?? 0;
    const result = computeProInsight(kundli, moonLon);
    setInsight(result);
  }, [kundli, moonData]);

  useEffect(() => {
    if (!insight || !kundli) return;
    const { pdPlanet, adPlanet, mdPlanet, pdStart } = insight;
    const start = pdStart ?? new Date();
    setForecastLoading(true);
    setForecast(null);
    generatePDForecast(pdPlanet, adPlanet, mdPlanet, start, kundli, cat)
      .then(f => { setForecast(f); })
      .catch(() => {})
      .finally(() => setForecastLoading(false));
  }, [cat, insight, kundli]);

  const catInfo  = CATEGORIES.find(c => c.key === cat)!;
  const catColor = catInfo.color;
  const catData  = insight ? insight[cat] : null;

  const trendColor = catData?.trend === "UP"   ? "#4ade80"
                   : catData?.trend === "DOWN"  ? "#ef4444"
                   : "#fbbf24";
  const trendIcon  = catData?.trend === "UP"   ? "trending-up"
                   : catData?.trend === "DOWN"  ? "trending-down"
                   : "minus";

  return (
    <CosmicBg>
    <ScrollView
      style={s.root}
      contentContainerStyle={[s.content, { paddingTop: topPad + 16, paddingBottom: botPad + 110 }]}
      showsVerticalScrollIndicator={false}
    >
      {/* Header */}
      <Text style={[s.heading, { color: C.text }]}>{t.futureTitle}</Text>
      <Text style={[s.subtitle, { color: C.textDim }]}>{t.futureSubtitle}</Text>

      {/* Demo lock banner */}
      {showDemo && (
        <Pressable
          style={[s.demoBanner, { backgroundColor: C.warningBg, borderColor: C.warningBorder }]}
          onPress={() => router.push("/onboarding")}
        >
          <Feather name="lock" size={12} color={C.warningText} />
          <Text style={[s.demoText, { color: C.warningText }]}>
            {t.futureDemoBanner}
          </Text>
          <Feather name="chevron-right" size={12} color={C.warningText} />
        </Pressable>
      )}

      {/* Demo empty state */}
      {showDemo && (
        <View style={[s.emptyState, { borderColor: C.border, backgroundColor: C.bgCard }]}>
          <Text style={s.emptyEmoji}>🪐</Text>
          <Text style={[s.emptyTitle, { color: C.text }]}>{t.kundliRequired}</Text>
          <Text style={[s.emptyBody, { color: C.textDim }]}>
            {t.kundliRequiredSub}
          </Text>
          <Pressable
            style={[s.emptyBtn, { backgroundColor: C.accent }]}
            onPress={() => router.push("/onboarding")}
          >
            <Text style={s.emptyBtnText}>{t.createKundli}</Text>
          </Pressable>
        </View>
      )}

      {/* ── Real data section ── */}
      {!showDemo && (
        <>
          {/* Dasha Phase card */}
          {insight && (
            <View style={[s.dashaCard, { backgroundColor: C.bgCard, borderColor: C.border }]}>
              <Text style={[s.dashaLabel, { color: C.textMuted }]}>{t.activeDashaPhase}</Text>
              <View style={s.dashaRow}>
                {[
                  { lbl: "MD", planet: insight.mdPlanet, clr: "#4b6a86" },
                  { lbl: "AD", planet: insight.adPlanet, clr: "#7c6ed4" },
                  { lbl: "PD", planet: insight.pdPlanet, clr: "#f59e0b" },
                ].map((d, i) => (
                  <React.Fragment key={d.lbl}>
                    <View style={s.dashaItem}>
                      <Text style={[s.dashaPlanetLbl, { color: d.clr }]}>{d.lbl}</Text>
                      <View style={[s.dashaPlanetDot, { backgroundColor: `${d.clr}25`, borderColor: `${d.clr}55` }]}>
                        <Text style={[s.dashaPlanetName, { color: d.clr }]}>{pName(d.planet)}</Text>
                      </View>
                    </View>
                    {i < 2 && <Feather name="chevron-right" size={14} color={C.textDim} style={{ marginTop: 14 }} />}
                  </React.Fragment>
                ))}
              </View>
              {insight.pdStart && insight.pdEnd && (
                <Text style={[s.dashaDate, { color: C.textMuted }]}>
                  PD: {formatDate(insight.pdStart)} — {formatDate(insight.pdEnd)}
                </Text>
              )}
            </View>
          )}

          {/* 6-Month Future card — month-by-month MD/AD/PD outlook */}
          <Pressable
            onPress={() => { Haptics.selectionAsync(); router.push("/six-month-future"); }}
            style={({ pressed }) => [
              s.sixMoCard,
              { backgroundColor: C.bgCard, borderColor: C.border, opacity: pressed ? 0.85 : 1 },
            ]}
          >
            <LinearGradient
              colors={["rgba(167,139,250,0.22)", "rgba(99,102,241,0.06)"]}
              start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }}
              style={StyleSheet.absoluteFill}
            />
            <View style={s.sixMoIconWrap}>
              <Text style={s.sixMoEmoji}>🗓️</Text>
            </View>
            <View style={{ flex: 1 }}>
              <View style={s.sixMoTitleRow}>
                <Text style={[s.sixMoTitle, { color: C.text }]}>6-Month Future</Text>
                <View style={s.sixMoBadge}>
                  <Text style={s.sixMoBadgeText}>New</Text>
                </View>
              </View>
              <Text style={[s.sixMoSub, { color: C.textDim }]} numberOfLines={2}>
                Agle 6 mahine — MD/AD/PD ke saath month-by-month outlook
              </Text>
            </View>
            <Feather name="chevron-right" size={18} color={C.textDim} />
          </Pressable>

          {/* Category tabs */}
          <ScrollView horizontal showsHorizontalScrollIndicator={false} style={s.tabsScroll} contentContainerStyle={s.tabs}>
            {CATEGORIES.map(c => {
              const active = c.key === cat;
              return (
                <Pressable
                  key={c.key}
                  style={[s.tab, { backgroundColor: C.bgCard, borderColor: C.border }, active && { borderColor: c.color, backgroundColor: `${c.color}12` }]}
                  onPress={() => { setCat(c.key); Haptics.selectionAsync(); }}
                >
                  <Text style={s.tabIcon}>{c.icon}</Text>
                  <Text style={[s.tabLabel, { color: C.textMuted }, active && { color: c.color }]}>{c.label}</Text>
                </Pressable>
              );
            })}
          </ScrollView>

          {/* Score + trend row */}
          {insight && catData && (
            <View style={[s.scoreCard, { backgroundColor: C.bgCard, borderColor: C.border, boxShadow: C.cardShadow } as any]}>
              <ScoreRing score={catData.score} color={catColor} />
              <View style={s.scoreRight}>
                <View style={s.trendRow}>
                  <Feather name={trendIcon} size={14} color={trendColor} />
                  <Text style={[s.trendText, { color: trendColor }]}>
                    {catData.trend === "UP" ? t.phaseGood : catData.trend === "DOWN" ? t.phaseChallenging : t.phaseAverage} {t.phaseSuffix}
                  </Text>
                </View>
                <Text style={[s.activePlanetText, { color: C.textMuted }]}>
                  {t.activeLabel}: <Text style={{ color: PLANET_CLR[catData.activePlanet] ?? catColor }}>
                    {pName(catData.activePlanet)}
                  </Text>
                </Text>
              </View>
            </View>
          )}

          {/* Sade Sati alert */}
          {forecast?.sadeSati && (
            <View style={[s.sadeSatiAlert, { backgroundColor: "rgba(239,68,68,0.08)", borderColor: "rgba(239,68,68,0.3)" }]}>
              <Feather name="alert-octagon" size={14} color="#ef4444" />
              <Text style={[s.sadeSatiText, { color: "#ef4444" }]}>
                {t.sadeSatiAlert}
              </Text>
            </View>
          )}

          {/* Transit error banner */}
          {forecast?.transitError && (
            <View style={[s.errorBanner, { backgroundColor: C.bgCard, borderColor: C.border }]}>
              <Feather name="wifi-off" size={13} color={C.textDim} />
              <Text style={[s.errorText, { color: C.textDim }]}>
                {t.transitUnavailBanner}
              </Text>
            </View>
          )}

          {/* 6-month forecast graph */}
          <View style={[s.graphCard, { backgroundColor: C.bgCard, borderColor: C.border, boxShadow: C.cardShadow } as any]}>
            <View style={s.graphHeader}>
              <Text style={[s.graphTitle, { color: C.textMuted }]}>{t.sixMonthTrend}</Text>
              {forecastLoading && <ActivityIndicator size="small" color={catColor} />}
            </View>
            {forecast && !forecast.transitError ? (
              <ScrollView horizontal showsHorizontalScrollIndicator={false}>
                <LineChart months={forecast.months} scores={forecast.scores} color={catColor} />
              </ScrollView>
            ) : forecast?.transitError ? (
              <View style={s.graphPlaceholder}>
                <Feather name="bar-chart-2" size={24} color={C.border} />
                <Text style={[s.unavailText, { color: C.textDim }]}>{t.transitUnavailShort}</Text>
              </View>
            ) : (
              <View style={s.graphPlaceholder}>
                <ActivityIndicator color={catColor} />
              </View>
            )}
          </View>

          {/* Upcoming PD chips */}
          {insight && insight.upcomingPDs.length > 0 && (
            <View style={s.pdSection}>
              <Text style={[s.sectionTitle, { color: C.textMuted }]}>{t.upcomingPD}</Text>
              <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={s.pdRow}>
                {insight.upcomingPDs.map((pd, i) => {
                  const clr = PLANET_CLR[pd.planet] ?? "#f59e0b";
                  const isActive = i === 0;
                  return (
                    <View key={i} style={[s.pdChip, { borderColor: `${clr}44`, backgroundColor: `${clr}10` }, isActive && { borderColor: clr }]}>
                      {isActive && <View style={[s.pdActiveDot, { backgroundColor: clr }]} />}
                      <Text style={[s.pdPlanet, { color: clr }]}>{pName(pd.planet)}</Text>
                      <Text style={[s.pdDates, { color: C.textMuted }]}>{fmtPDDate(pd.start)}</Text>
                      <Text style={[s.pdDatesTo, { color: C.textDim }]}>–</Text>
                      <Text style={[s.pdDates, { color: C.textMuted }]}>{fmtPDDate(pd.end)}</Text>
                    </View>
                  );
                })}
              </ScrollView>
            </View>
          )}

          {/* Reasons section */}
          {forecast && forecast.reasons.length > 0 && (
            <View style={[s.reasonsCard, { backgroundColor: C.bgCard, borderColor: C.border }]}>
              <View style={s.reasonsHeader}>
                <Feather name="zap" size={13} color={catColor} />
                <Text style={[s.reasonsTitle, { color: catColor }]}>{t.whyThisScore}</Text>
              </View>
              {forecast.reasons.map((r, i) => (
                <ReasonItem key={i} text={r} color={catColor} />
              ))}
            </View>
          )}

          {/* Avg score badge */}
          {forecast && (
            <View style={[s.avgBadge, { borderColor: `${catColor}40`, backgroundColor: `${catColor}08` }]}>
              <Text style={[s.avgScore, { color: catColor }]}>{forecast.avgScore}</Text>
              <Text style={[s.avgLabel, { color: C.textMuted }]}>{t.sixMonthAvg}</Text>
              {forecast.transitError && (
                <Text style={[s.avgSub, { color: C.textDim }]}>{t.basedOnNatal}</Text>
              )}
            </View>
          )}
        </>
      )}
    </ScrollView>
    </CosmicBg>
  );
}

const s = StyleSheet.create({
  root:    { flex: 1 },
  content: { paddingHorizontal: 16, gap: 14 },
  heading: { color: "#dde8f4", fontSize: 22, fontWeight: "700" },
  subtitle: { fontSize: 13, fontWeight: "400", marginTop: 4, marginBottom: 4, opacity: 0.7 },

  demoBanner: {
    flexDirection: "row", alignItems: "center", gap: 8,
    borderRadius: 12, borderWidth: 1,
    paddingHorizontal: 14, paddingVertical: 10,
  },
  demoText: { fontSize: 11, flex: 1 },

  emptyState: {
    borderRadius: 20, borderWidth: 1, padding: 28,
    alignItems: "center", gap: 10,
  },
  emptyEmoji: { fontSize: 42, lineHeight: 52 },
  emptyTitle: { fontSize: 17, fontWeight: "700" },
  emptyBody:  { fontSize: 13, lineHeight: 20, textAlign: "center", opacity: 0.75 },
  emptyBtn:   { marginTop: 6, paddingHorizontal: 24, paddingVertical: 11, borderRadius: 14 },
  emptyBtnText: { color: "#fff", fontSize: 14, fontWeight: "700" },

  dashaCard: {
    borderRadius: 18, borderWidth: 1, padding: 16, gap: 10,
  },
  dashaLabel: { fontSize: 10, fontWeight: "600", letterSpacing: 1.2, textTransform: "uppercase" },
  dashaRow:   { flexDirection: "row", alignItems: "center", gap: 8 },
  dashaItem:  { alignItems: "center", gap: 4, flex: 1 },
  dashaPlanetLbl: { fontSize: 10, fontWeight: "700", letterSpacing: 1 },
  dashaPlanetDot: { paddingHorizontal: 10, paddingVertical: 5, borderRadius: 12, borderWidth: 1 },
  dashaPlanetName: { fontSize: 13, fontWeight: "600" },
  dashaDate: { fontSize: 11, textAlign: "center" },

  sixMoCard: {
    flexDirection: "row", alignItems: "center", gap: 12,
    borderRadius: 16, borderWidth: 1, padding: 14,
    overflow: "hidden",
  },
  sixMoIconWrap: {
    width: 44, height: 44, borderRadius: 22,
    backgroundColor: "rgba(167,139,250,0.18)",
    alignItems: "center", justifyContent: "center",
  },
  sixMoEmoji: { fontSize: 22 },
  sixMoTitleRow: { flexDirection: "row", alignItems: "center", gap: 8 },
  sixMoTitle: { fontSize: 15, fontWeight: "700" },
  sixMoBadge: {
    backgroundColor: "#a78bfa", borderRadius: 10,
    paddingHorizontal: 8, paddingVertical: 2,
  },
  sixMoBadgeText: { color: "#fff", fontSize: 10, fontWeight: "700" },
  sixMoSub: { fontSize: 12, marginTop: 3, lineHeight: 16 },

  tabsScroll: { flexGrow: 0 },
  tabs:       { gap: 8, paddingRight: 4 },
  tab: {
    flexDirection: "row", alignItems: "center", gap: 6,
    paddingHorizontal: 14, paddingVertical: 9, borderRadius: 20, borderWidth: 1,
  },
  tabIcon:  { fontSize: 14 },
  tabLabel: { fontSize: 13, fontWeight: "600" },

  scoreCard: {
    borderRadius: 18, borderWidth: 1, padding: 16,
    flexDirection: "row", gap: 16, alignItems: "center",
  },
  scoreRight:       { flex: 1, gap: 5 },
  trendRow:         { flexDirection: "row", alignItems: "center", gap: 6 },
  trendText:        { fontSize: 13, fontWeight: "700" },
  activePlanetText: { fontSize: 11 },

  sadeSatiAlert: {
    flexDirection: "row", alignItems: "flex-start", gap: 8,
    borderRadius: 14, borderWidth: 1, paddingHorizontal: 14, paddingVertical: 10,
  },
  sadeSatiText: { fontSize: 12, lineHeight: 18, flex: 1 },

  errorBanner: {
    flexDirection: "row", alignItems: "flex-start", gap: 8,
    borderRadius: 12, borderWidth: 1, paddingHorizontal: 12, paddingVertical: 8,
  },
  errorText: { fontSize: 11, lineHeight: 16, flex: 1 },

  graphCard: {
    borderRadius: 18, borderWidth: 1, padding: 16, gap: 12,
  },
  graphHeader:     { flexDirection: "row", alignItems: "center", justifyContent: "space-between" },
  graphTitle:      { fontSize: 11, fontWeight: "600", letterSpacing: 0.8, textTransform: "uppercase" },
  graphPlaceholder:{ height: 100, alignItems: "center", justifyContent: "center", gap: 8 },
  unavailText:     { fontSize: 12 },

  pdSection: { gap: 10 },
  sectionTitle: { fontSize: 11, fontWeight: "600", letterSpacing: 0.8, textTransform: "uppercase" },
  pdRow: { gap: 8, paddingRight: 4 },
  pdChip: {
    borderRadius: 12, borderWidth: 1.5, paddingHorizontal: 12, paddingVertical: 10,
    gap: 2, alignItems: "center", minWidth: 80,
  },
  pdActiveDot: { width: 6, height: 6, borderRadius: 3, marginBottom: 2 },
  pdPlanet:    { fontSize: 12, fontWeight: "700" },
  pdDatesTo:   { fontSize: 10 },
  pdDates:     { fontSize: 10 },

  reasonsCard: {
    borderRadius: 18, borderWidth: 1, padding: 16, gap: 10,
  },
  reasonsHeader: { flexDirection: "row", alignItems: "center", gap: 7, marginBottom: 2 },
  reasonsTitle:  { fontSize: 13, fontWeight: "700" },
  reasonItem:    { flexDirection: "row", alignItems: "flex-start", gap: 8 },
  reasonDot:     { width: 6, height: 6, borderRadius: 3, marginTop: 7, flexShrink: 0 },
  reasonText:    { fontSize: 12, lineHeight: 19, flex: 1 },

  avgBadge: {
    borderRadius: 14, borderWidth: 1, paddingVertical: 14, alignItems: "center", gap: 2,
  },
  avgScore: { fontSize: 28, fontWeight: "800" },
  avgLabel: { fontSize: 11 },
  avgSub:   { fontSize: 10, marginTop: 2 },

  sectionCap: {
    fontSize: 10, fontWeight: "700", letterSpacing: 2,
    textTransform: "uppercase", paddingLeft: 2,
  },
});
