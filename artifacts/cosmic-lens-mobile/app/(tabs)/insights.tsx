import { Feather } from "@expo/vector-icons";
import * as Haptics from "expo-haptics";
import { router } from "expo-router";
import React, { useEffect, useState } from "react";
import {
  ActivityIndicator,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";
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

// ── 6-month line chart ────────────────────────────────────────────────────────
function LineChart({ months, scores, color }: { months: string[]; scores: number[]; color: string }) {
  const W = 300, H = 120, PAD_L = 30, PAD_R = 12, PAD_T = 10, PAD_B = 28;
  const chartW = W - PAD_L - PAD_R;
  const chartH = H - PAD_T - PAD_B;

  const pts = scores.map((s, i) => {
    const x = PAD_L + (i / (scores.length - 1)) * chartW;
    const y = PAD_T + (1 - s / 100) * chartH;
    return { x, y, s };
  });
  const polyline = pts.map(p => `${p.x},${p.y}`).join(" ");

  // Smooth path (using quadratic curves)
  let smoothPath = `M ${pts[0].x} ${pts[0].y}`;
  for (let i = 1; i < pts.length; i++) {
    const cp = { x: (pts[i-1].x + pts[i].x) / 2, y: (pts[i-1].y + pts[i].y) / 2 };
    smoothPath += ` Q ${pts[i-1].x} ${pts[i-1].y} ${cp.x} ${cp.y}`;
  }
  smoothPath += ` L ${pts[pts.length-1].x} ${pts[pts.length-1].y}`;

  // Fill area
  const areaPath = smoothPath + ` L ${pts[pts.length-1].x} ${PAD_T+chartH} L ${pts[0].x} ${PAD_T+chartH} Z`;

  return (
    <Svg width={W} height={H}>
      <Defs>
        <SvgGrad id="area" x1="0" y1="0" x2="0" y2="1">
          <Stop offset="0" stopColor={color} stopOpacity={0.25} />
          <Stop offset="1" stopColor={color} stopOpacity={0.0} />
        </SvgGrad>
      </Defs>
      {/* Y-axis grid lines */}
      {[25, 50, 75].map(v => (
        <Line
          key={v}
          x1={PAD_L} y1={PAD_T + (1 - v/100)*chartH}
          x2={W - PAD_R} y2={PAD_T + (1 - v/100)*chartH}
          stroke="rgba(255,255,255,0.05)" strokeWidth={1}
        />
      ))}
      {/* Area fill */}
      <Path d={areaPath} fill="url(#area)" />
      {/* Line */}
      <Path d={smoothPath} fill="none" stroke={color} strokeWidth={2} strokeLinecap="round" />
      {/* Points + scores */}
      {pts.map((p, i) => (
        <React.Fragment key={i}>
          <Circle cx={p.x} cy={p.y} r={4} fill={color} />
          <SvgText
            x={p.x} y={p.y - 9}
            fontSize={8} fill={color}
            textAnchor="middle" fontWeight="bold"
          >
            {p.s}
          </SvgText>
          <SvgText
            x={p.x} y={H - 6}
            fontSize={9} fill="#3d5a7a"
            textAnchor="middle"
          >
            {months[i]}
          </SvgText>
        </React.Fragment>
      ))}
      {/* Y labels */}
      {[25, 50, 75].map(v => (
        <SvgText
          key={v}
          x={PAD_L - 4} y={PAD_T + (1 - v/100)*chartH + 3.5}
          fontSize={7} fill="#1e3a5f" textAnchor="end"
        >
          {v}
        </SvgText>
      ))}
    </Svg>
  );
}

// ── Score Ring ────────────────────────────────────────────────────────────────
function ScoreRing({ score, color }: { score: number; color: string }) {
  const R = 28, STROKE = 5;
  const circ = 2 * Math.PI * R;
  const dash = (score / 100) * circ;
  return (
    <Svg width={70} height={70}>
      <Circle cx={35} cy={35} r={R} fill="none" stroke="#071525" strokeWidth={STROKE} />
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

export default function InsightsScreen() {
  const insets     = useSafeAreaInsets();
  const C = useC();
  const { kundli, moonData, language } = useUser();
  const t = getT(language);
  const CATEGORIES = CATEGORY_META.map(c => ({
    ...c,
    label: t[c.key as "career" | "finance" | "relationship" | "health"],
  }));
  const topPad     = Platform.OS === "web" ? 67 : insets.top;
  const botPad     = Platform.OS === "web" ? 34 : insets.bottom;
  const showDemo   = !kundli;

  const [cat, setCat]               = useState<Category>("career");
  const [insight, setInsight]       = useState<ProInsight | null>(null);
  const [forecast, setForecast]     = useState<MonthForecast | null>(null);
  const [forecastLoading, setForecastLoading] = useState(false);

  // Compute ProInsight from kundli
  useEffect(() => {
    if (!kundli) return;
    const moonLon = moonData?.longitude ?? 0;
    const result = computeProInsight(kundli, moonLon);
    setInsight(result);
  }, [kundli, moonData]);

  // Load forecast when category or insight changes
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

  // Demo mock data
  const DEMO_INSIGHT: ProInsight = {
    mdPlanet: "Saturn", adPlanet: "Mercury", pdPlanet: "Jupiter",
    pdStart: new Date(2025, 9, 1), pdEnd: new Date(2026, 2, 15),
    career:       { score: 72, trend: "UP",    activePlanet: "Jupiter",  text: "Career mein achi progress expected hai." },
    relationship: { score: 55, trend: "MIXED", activePlanet: "Jupiter",  text: "Rishton mein stability-instability ka mix." },
    finance:      { score: 63, trend: "MIXED", activePlanet: "Jupiter",  text: "Dhan labh ke avsar hain, sawdhani bhi." },
    health:       { score: 80, trend: "UP",    activePlanet: "Jupiter",  text: "Swasthya accha rahega, energy high hai." },
    upcomingPDs:  [
      { planet: "Jupiter", start: new Date(2025,9,1), end: new Date(2026,2,15) },
      { planet: "Saturn",  start: new Date(2026,2,15), end: new Date(2026,8,1) },
      { planet: "Mercury", start: new Date(2026,8,1), end: new Date(2026,11,20) },
    ],
  };
  const DEMO_FORECAST: MonthForecast = {
    months: ["Oct","Nov","Dec","Jan","Feb","Mar"],
    scores: [68, 72, 75, 65, 80, 78],
    trend: "UP", avgScore: 73,
    howItWillGo: "Career mein achi progress expected hai.",
    caution: "Overconfidence se bachein.",
    remedy: "Roj subah Surya namaskar karein.",
  };

  const displayInsight  = showDemo ? DEMO_INSIGHT  : insight;
  const displayForecast = showDemo ? DEMO_FORECAST : forecast;
  const displayCat      = displayInsight ? displayInsight[cat] : null;

  const trendColor = displayInsight?.[cat]?.trend === "UP" ? "#4ade80"
                   : displayInsight?.[cat]?.trend === "DOWN" ? "#ef4444"
                   : "#fbbf24";
  const trendIcon  = displayInsight?.[cat]?.trend === "UP" ? "trending-up"
                   : displayInsight?.[cat]?.trend === "DOWN" ? "trending-down"
                   : "minus";

  return (
    <ScrollView
      style={[s.root, { backgroundColor: C.bg }]}
      contentContainerStyle={[s.content, { paddingTop: topPad + 16, paddingBottom: botPad + 110 }]}
      showsVerticalScrollIndicator={false}
    >
      {/* Header */}
      <Text style={[s.heading, { color: C.text }]}>{t.insightsTitle}</Text>

      {/* Demo lock banner */}
      {showDemo && (
        <Pressable style={s.demoBanner} onPress={() => router.push("/onboarding")}>
          <Feather name="lock" size={12} color="#fbbf24" />
          <Text style={s.demoText}>Sample data — Apni kundli banao personalized insights ke liye</Text>
          <Feather name="chevron-right" size={12} color="#fbbf24" />
        </Pressable>
      )}

      {/* Dasha Phase card */}
      {displayInsight && (
        <View style={[s.dashaCard, { backgroundColor: C.bgCard, borderColor: C.border }]}>
          <Text style={[s.dashaLabel, { color: C.textMuted }]}>Active Dasha Phase</Text>
          <View style={s.dashaRow}>
            {[
              { lbl: "MD", planet: displayInsight.mdPlanet, clr: "#4b6a86" },
              { lbl: "AD", planet: displayInsight.adPlanet, clr: "#7c6ed4" },
              { lbl: "PD", planet: displayInsight.pdPlanet, clr: "#f59e0b" },
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
          {displayInsight.pdStart && displayInsight.pdEnd && (
            <Text style={[s.dashaDate,{ color: C.textMuted }]}>
              PD: {formatDate(displayInsight.pdStart)} — {formatDate(displayInsight.pdEnd)}
            </Text>
          )}
        </View>
      )}

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
      {displayInsight && displayCat && (
        <View style={[s.scoreCard, { backgroundColor: C.bgCard, borderColor: C.border }]}>
          <ScoreRing score={displayCat.score} color={catColor} />
          <View style={s.scoreRight}>
            <View style={s.trendRow}>
              <Feather name={trendIcon} size={14} color={trendColor} />
              <Text style={[s.trendText, { color: trendColor }]}>
                {displayCat.trend === "UP" ? "Accha" : displayCat.trend === "DOWN" ? "Chunautiyan" : "Average"} phase
              </Text>
            </View>
            <Text style={[s.activePlanetText, { color: C.textMuted }]}>
              Active: <Text style={{ color: PLANET_CLR[displayCat.activePlanet] ?? catColor }}>
                {pName(displayCat.activePlanet)}
              </Text>
            </Text>
            <Text style={[s.catText, { color: C.textMuted }]}>{displayCat.text}</Text>
          </View>
        </View>
      )}

      {/* 6-month forecast graph */}
      <View style={[s.graphCard, { backgroundColor: C.bgCard, borderColor: C.border }]}>
        <View style={s.graphHeader}>
          <Text style={[s.graphTitle, { color: C.textMuted }]}>6-Month Trend</Text>
          {(forecastLoading && !showDemo) && <ActivityIndicator size="small" color={catColor} />}
        </View>
        {displayForecast ? (
          <ScrollView horizontal showsHorizontalScrollIndicator={false}>
            <LineChart months={displayForecast.months} scores={displayForecast.scores} color={catColor} />
          </ScrollView>
        ) : (
          <View style={s.graphPlaceholder}>
            <ActivityIndicator color={catColor} />
          </View>
        )}
      </View>

      {/* Upcoming PD chips */}
      {displayInsight && displayInsight.upcomingPDs.length > 0 && (
        <View style={s.pdSection}>
          <Text style={[s.sectionTitle,{ color: C.textMuted }]}>Upcoming Pratyantardasha</Text>
          <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={s.pdRow}>
            {displayInsight.upcomingPDs.map((pd, i) => {
              const clr = PLANET_CLR[pd.planet] ?? "#f59e0b";
              const isActive = i === 0;
              return (
                <View key={i} style={[s.pdChip, { borderColor: `${clr}44`, backgroundColor: `${clr}10` }, isActive && { borderColor: clr }]}>
                  {isActive && <View style={[s.pdActiveDot, { backgroundColor: clr }]} />}
                  <Text style={[s.pdPlanet, { color: clr }]}>{pName(pd.planet)}</Text>
                  <Text style={[s.pdDates,{ color: C.textMuted }]}>{fmtPDDate(pd.start)}</Text>
                  <Text style={[s.pdDatesTo,{ color: C.textDim }]}>–</Text>
                  <Text style={[s.pdDates,{ color: C.textMuted }]}>{fmtPDDate(pd.end)}</Text>
                </View>
              );
            })}
          </ScrollView>
        </View>
      )}

      {/* Text insight cards */}
      {displayForecast && (
        <View style={s.textCards}>
          <View style={[s.textCard, { backgroundColor: C.bgCard, borderColor: C.border }]}>
            <View style={s.textCardHeader}>
              <Feather name="compass" size={13} color={catColor} />
              <Text style={[s.textCardTitle, { color: catColor }]}>Kaisa rahega?</Text>
            </View>
            <Text style={[s.textCardBody, { color: C.textMuted }]}>{displayForecast.howItWillGo}</Text>
          </View>
          <View style={[s.textCard, { backgroundColor: C.bgCard, borderColor: C.border }]}>
            <View style={s.textCardHeader}>
              <Feather name="alert-triangle" size={13} color="#fbbf24" />
              <Text style={[s.textCardTitle, { color: "#fbbf24" }]}>Sawdhani</Text>
            </View>
            <Text style={[s.textCardBody, { color: C.textMuted }]}>{displayForecast.caution}</Text>
          </View>
          <View style={[s.textCard, { backgroundColor: C.bgCard, borderColor: C.border }]}>
            <View style={s.textCardHeader}>
              <Feather name="sun" size={13} color="#4ade80" />
              <Text style={[s.textCardTitle, { color: "#4ade80" }]}>Upay</Text>
            </View>
            <Text style={[s.textCardBody, { color: C.textMuted }]}>{displayForecast.remedy}</Text>
          </View>
        </View>
      )}

      {/* Avg score badge */}
      {displayForecast && (
        <View style={[s.avgBadge, { borderColor: `${catColor}40`, backgroundColor: `${catColor}08` }]}>
          <Text style={[s.avgScore, { color: catColor }]}>{displayForecast.avgScore}</Text>
          <Text style={[s.avgLabel,{ color: C.textMuted }]}>6-month average score</Text>
        </View>
      )}
    </ScrollView>
  );
}

const s = StyleSheet.create({
  root:    { flex: 1, backgroundColor: "#020d1a" },
  content: { paddingHorizontal: 16, gap: 14 },
  heading: { color: "#dde8f4", fontSize: 22, fontWeight: "700" },

  demoBanner: {
    flexDirection: "row", alignItems: "center", gap: 8,
    backgroundColor: "rgba(251,191,36,0.07)", borderRadius: 12,
    borderWidth: 1, borderColor: "rgba(251,191,36,0.2)",
    paddingHorizontal: 14, paddingVertical: 10,
  },
  demoText: { color: "#fbbf24", fontSize: 11, flex: 1 },

  dashaCard: {
    backgroundColor: "#040e1f", borderRadius: 18,
    borderWidth: 1, borderColor: "rgba(255,255,255,0.05)",
    padding: 16, gap: 10,
  },
  dashaLabel: { color: "#1e3a5f", fontSize: 10, fontWeight: "600", letterSpacing: 1.2, textTransform: "uppercase" },
  dashaRow:   { flexDirection: "row", alignItems: "center", gap: 8 },
  dashaItem:  { alignItems: "center", gap: 4, flex: 1 },
  dashaPlanetLbl: { fontSize: 10, fontWeight: "700", letterSpacing: 1 },
  dashaPlanetDot: {
    paddingHorizontal: 10, paddingVertical: 5,
    borderRadius: 12, borderWidth: 1,
  },
  dashaPlanetName: { fontSize: 13, fontWeight: "600" },
  dashaDate: { color: "#3d5a7a", fontSize: 11, textAlign: "center" },

  tabsScroll: { flexGrow: 0 },
  tabs:       { gap: 8, paddingRight: 4 },
  tab: {
    flexDirection: "row", alignItems: "center", gap: 6,
    paddingHorizontal: 14, paddingVertical: 9, borderRadius: 20,
    backgroundColor: "#040e1f", borderWidth: 1, borderColor: "rgba(255,255,255,0.07)",
  },
  tabIcon:  { fontSize: 14 },
  tabLabel: { color: "#3d5a7a", fontSize: 13, fontWeight: "600" },

  scoreCard: {
    backgroundColor: "#040e1f", borderRadius: 18,
    borderWidth: 1, borderColor: "rgba(255,255,255,0.05)",
    padding: 16, flexDirection: "row", gap: 16, alignItems: "center",
  },
  scoreRight: { flex: 1, gap: 5 },
  trendRow:   { flexDirection: "row", alignItems: "center", gap: 6 },
  trendText:  { fontSize: 13, fontWeight: "700" },
  activePlanetText: { color: "#3d5a7a", fontSize: 11 },
  catText:    { color: "#475569", fontSize: 12, lineHeight: 18 },

  graphCard: {
    backgroundColor: "#040e1f", borderRadius: 18,
    borderWidth: 1, borderColor: "rgba(255,255,255,0.05)",
    padding: 16, gap: 12,
  },
  graphHeader: { flexDirection: "row", alignItems: "center", justifyContent: "space-between" },
  graphTitle:  { color: "#3d5a7a", fontSize: 11, fontWeight: "600", letterSpacing: 0.8, textTransform: "uppercase" },
  graphPlaceholder: { height: 100, alignItems: "center", justifyContent: "center" },

  pdSection: { gap: 10 },
  sectionTitle: { color: "#3d5a7a", fontSize: 11, fontWeight: "600", letterSpacing: 0.8, textTransform: "uppercase" },
  pdRow: { gap: 8, paddingRight: 4 },
  pdChip: {
    borderRadius: 12, borderWidth: 1.5, paddingHorizontal: 12, paddingVertical: 10,
    gap: 2, alignItems: "center", minWidth: 80,
  },
  pdActiveDot: { width: 6, height: 6, borderRadius: 3, marginBottom: 2 },
  pdPlanet: { fontSize: 12, fontWeight: "700" },
  pdDatesTo: { color: "#1e3a5f", fontSize: 10 },
  pdDates: { color: "#3d5a7a", fontSize: 10 },

  textCards: { gap: 10 },
  textCard: {
    backgroundColor: "#040e1f", borderRadius: 16,
    borderWidth: 1, borderColor: "rgba(255,255,255,0.04)",
    padding: 14, gap: 8,
  },
  textCardHeader: { flexDirection: "row", alignItems: "center", gap: 7 },
  textCardTitle:  { fontSize: 12, fontWeight: "700" },
  textCardBody:   { color: "#475569", fontSize: 13, lineHeight: 20 },

  avgBadge: {
    borderRadius: 14, borderWidth: 1,
    paddingVertical: 14, alignItems: "center", gap: 2,
  },
  avgScore: { fontSize: 28, fontWeight: "800" },
  avgLabel: { color: "#3d5a7a", fontSize: 11 },
});
