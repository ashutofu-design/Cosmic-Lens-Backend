import { Feather } from "@expo/vector-icons";
import { router } from "expo-router";
import * as Haptics from "expo-haptics";
import React, { useEffect, useState } from "react";
import {
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
import { computeActiveDasha, pName } from "@/lib/proInsightEngine";

import { API_BASE } from "@/lib/apiConfig";

const DAY_NAMES = ["Aaditya (Sun)", "Soma (Mon)", "Mangal (Tue)", "Budh (Wed)", "Guru (Thu)", "Shukra (Fri)", "Shani (Sat)"];
const SHORT_DAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

interface DayForecast {
  date: Date;
  score: number;
  moonLon: number;
  moonSign: string;
  phase: string;
  summary: string;
}

const SIGNS = [
  "Mesh","Vrishabh","Mithun","Kark","Simha","Kanya",
  "Tula","Vrishchik","Dhanu","Makar","Kumbh","Meen",
];

function moonSign(lon: number): string { return SIGNS[Math.floor(lon / 30) % 12]; }

function moonPhase(date: Date): string {
  const ref = new Date("2000-01-06").getTime();
  const cycle = 29.53058770576;
  const diff = (date.getTime() - ref) / (1000*60*60*24);
  const phase = ((diff % cycle) + cycle) % cycle;
  if (phase < 2)  return "Amavasya";
  if (phase < 7)  return "Shukla Paksha";
  if (phase < 15) return "Shukla Paksha";
  if (phase < 17) return "Purnima";
  if (phase < 22) return "Krishna Paksha";
  if (phase < 29) return "Krishna Paksha";
  return "Amavasya";
}

const SCORE_SUMMARIES: Record<string, string> = {
  UP: "Today is filled with positive energy. A great day to start new ventures.",
  MIXED: "A mixed day — some opportunities, some things to watch out for.",
  DOWN: "Slightly challenging energy today. Stay patient, avoid being reactive.",
};

function scoreToTrend(s: number): "UP"|"MIXED"|"DOWN" {
  return s >= 65 ? "UP" : s <= 40 ? "DOWN" : "MIXED";
}

// ── Small chart ───────────────────────────────────────────────────────────────
function WeekChart({
  days, scores, selected, onSelect, color,
}: {
  days: DayForecast[]; scores: number[]; selected: number;
  onSelect: (i: number) => void; color: string;
}) {
  const C = useC();
  const W = 320, H = 90, PAD = 16;
  const chartW = W - PAD * 2;
  const pts = scores.map((s, i) => ({
    x: PAD + (i / (scores.length - 1)) * chartW,
    y: 12 + (1 - s / 100) * (H - 30),
    s,
  }));
  let path = `M ${pts[0].x} ${pts[0].y}`;
  for (let i = 1; i < pts.length; i++) {
    const cpx = (pts[i-1].x + pts[i].x) / 2;
    path += ` C ${cpx} ${pts[i-1].y} ${cpx} ${pts[i].y} ${pts[i].x} ${pts[i].y}`;
  }
  const area = path + ` L ${pts[pts.length-1].x} ${H-18} L ${pts[0].x} ${H-18} Z`;

  return (
    <Pressable onPress={() => {}}>
      <Svg width={W} height={H}>
        <Defs>
          <SvgGrad id="wg" x1="0" y1="0" x2="0" y2="1">
            <Stop offset="0" stopColor={color} stopOpacity={0.3} />
            <Stop offset="1" stopColor={color} stopOpacity={0.0} />
          </SvgGrad>
        </Defs>
        <Path d={area} fill="url(#wg)" />
        <Path d={path} fill="none" stroke={color} strokeWidth={2} strokeLinecap="round" />
        {pts.map((p, i) => (
          <React.Fragment key={i}>
            <Circle
              cx={p.x} cy={p.y} r={i === selected ? 7 : 4}
              fill={i === selected ? color : C.bgCard}
              stroke={color} strokeWidth={i === selected ? 2 : 1.5}
              onPress={() => { onSelect(i); Haptics.selectionAsync(); }}
            />
            <SvgText
              x={p.x} y={H - 4} fontSize={9}
              fill={i === selected ? color : C.textMuted}
              textAnchor="middle" fontWeight={i === selected ? "bold" : "normal"}
            >
              {SHORT_DAYS[days[i].date.getDay()]}
            </SvgText>
          </React.Fragment>
        ))}
      </Svg>
    </Pressable>
  );
}

export default function ForecastScreen() {
  const insets   = useSafeAreaInsets();
  const C = useC();
  const { kundli, moonData } = useUser();
  const topPad   = Platform.OS === "web" ? 67 : insets.top;
  const botPad   = Platform.OS === "web" ? 34 : insets.bottom;
  const showDemo = !kundli;

  const [days, setDays]       = useState<DayForecast[]>([]);
  const [selected, setSelected] = useState(0);
  const [loading, setLoading]   = useState(false);

  // Build 7 dates starting today
  useEffect(() => {
    const dates: string[] = [];
    const today = new Date();
    for (let i = 0; i < 7; i++) {
      const d = new Date(today);
      d.setDate(today.getDate() + i);
      dates.push(`${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,"0")}-${String(d.getDate()).padStart(2,"0")}`);
    }

    if (showDemo) {
      const demoScores = [72, 58, 81, 45, 70, 65, 77];
      const demoMoons  = [120, 133, 147, 162, 177, 192, 207];
      setDays(dates.map((ds, i) => {
        const dt = new Date(ds);
        return {
          date: dt,
          score: demoScores[i],
          moonLon: demoMoons[i],
          moonSign: moonSign(demoMoons[i]),
          phase: moonPhase(dt),
          summary: SCORE_SUMMARIES[scoreToTrend(demoScores[i])],
        };
      }));
      return;
    }

    setLoading(true);
    fetch(`${API_BASE}/api/transits`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ dates }),
    })
      .then(r => r.json())
      .then((data: { date: string; positions: Record<string,number> }[]) => {
        const moonLon = moonData?.longitude ?? 0;
        const dasha   = kundli ? computeActiveDasha(kundli, moonLon) : null;
        const baseScore = dasha?.careerScore ?? 60;

        const built = data.map((item, i) => {
          const transitMoon = item.positions?.Moon ?? (moonLon + i * 13.2);
          const variation   = Math.sin(i * 1.3) * 12 + (item.positions?.Jupiter ? 5 : 0)
            - (item.positions?.Saturn ? 6 : 0);
          const score = Math.max(10, Math.min(90, Math.round(baseScore + variation)));
          const dt    = new Date(item.date + "T00:00:00");
          return {
            date:     dt,
            score,
            moonLon:  transitMoon,
            moonSign: moonSign(transitMoon),
            phase:    moonPhase(dt),
            summary:  SCORE_SUMMARIES[scoreToTrend(score)],
          };
        });
        setDays(built);
      })
      .catch(() => {
        // fallback
        const fallback = [72, 58, 81, 45, 70, 65, 77];
        setDays(dates.map((ds, i) => {
          const dt = new Date(ds + "T00:00:00");
          return {
            date: dt, score: fallback[i],
            moonLon: 120 + i * 13,
            moonSign: moonSign(120 + i * 13),
            phase: moonPhase(dt),
            summary: SCORE_SUMMARIES[scoreToTrend(fallback[i])],
          };
        }));
      })
      .finally(() => setLoading(false));
  }, [kundli, moonData, showDemo]);

  const sel = days[selected];
  const scoreColor = sel
    ? (sel.score >= 65 ? "#4ade80" : sel.score <= 40 ? "#ef4444" : "#fbbf24")
    : "#f59e0b";

  const dasha = kundli ? computeActiveDasha(kundli, moonData?.longitude ?? 0) : null;

  return (
    <View style={[s.root, { paddingTop: topPad, backgroundColor: C.bg }]}>
      {/* Header */}
      <View style={[s.header, { borderBottomColor: C.border }]}>
        <Pressable onPress={() => router.back()} style={s.back}>
          <Feather name="arrow-left" size={20} color={C.textMuted} />
        </Pressable>
        <Text style={[s.headerTitle, { color: C.text }]}>7 Days Forecast</Text>
        {showDemo && (
          <View style={s.demoPill}>
            <Text style={s.demoPillText}>Demo</Text>
          </View>
        )}
      </View>

      <ScrollView contentContainerStyle={[s.content, { paddingBottom: botPad + 30 }]} showsVerticalScrollIndicator={false}>
        {/* Week chart */}
        <View style={[s.chartCard, { backgroundColor: C.bgCard, borderColor: C.border }]}>
          <Text style={[s.chartLabel, { color: C.textMuted }]}>Daily Energy Score</Text>
          {days.length > 0 ? (
            <WeekChart
              days={days}
              scores={days.map(d => d.score)}
              selected={selected}
              onSelect={setSelected}
              color="#f59e0b"
            />
          ) : (
            <View style={s.chartPlaceholder}>
              <Text style={[s.placeholderText, { color: C.textMuted }]}>Loading...</Text>
            </View>
          )}
        </View>

        {/* Selected day detail */}
        {sel && (
          <>
            {/* Day header */}
            <View style={s.dayHeader}>
              <View>
                <Text style={[s.dayName, { color: C.text }]}>
                  {sel.date.toLocaleDateString("en-IN", { weekday: "long" })}
                </Text>
                <Text style={[s.dayDate, { color: C.textMuted }]}>
                  {sel.date.toLocaleDateString("en-IN", { day: "numeric", month: "long", year: "numeric" })}
                </Text>
              </View>
              <View style={[s.scoreCircle, { borderColor: scoreColor }]}>
                <Text style={[s.scoreNum, { color: scoreColor }]}>{sel.score}</Text>
                <Text style={[s.scoreLabel, { color: C.textMuted }]}>score</Text>
              </View>
            </View>

            {/* Summary */}
            <View style={[s.summaryCard, { backgroundColor: C.bgCard, borderColor: C.border }]}>
              <Feather name="sun" size={14} color={scoreColor} />
              <Text style={[s.summaryText, { color: C.textMuted }]}>{sel.summary}</Text>
            </View>

            {/* Moon info */}
            <View style={s.infoGrid}>
              <View style={[s.infoItem, { backgroundColor: C.bgCard, borderColor: C.border }]}>
                <Text style={s.infoIcon}>🌙</Text>
                <Text style={[s.infoLabel, { color: C.textMuted }]}>Moon Rashi</Text>
                <Text style={[s.infoValue, { color: C.text }]}>{sel.moonSign}</Text>
              </View>
              <View style={[s.infoItem, { backgroundColor: C.bgCard, borderColor: C.border }]}>
                <Text style={s.infoIcon}>🔮</Text>
                <Text style={[s.infoLabel, { color: C.textMuted }]}>Paksha</Text>
                <Text style={[s.infoValue, { color: C.text }]}>{sel.phase}</Text>
              </View>
              <View style={[s.infoItem, { backgroundColor: C.bgCard, borderColor: C.border }]}>
                <Text style={s.infoIcon}>⚡</Text>
                <Text style={[s.infoLabel, { color: C.textMuted }]}>Energy</Text>
                <Text style={[s.infoValue, { color: scoreColor }]}>
                  {sel.score >= 65 ? "Uchch" : sel.score <= 40 ? "Neech" : "Madhyam"}
                </Text>
              </View>
            </View>

            {/* Active dasha */}
            {dasha && (
              <View style={[s.dashaCard, { backgroundColor: C.bgCard, borderColor: C.border }]}>
                <Text style={[s.dashaLabel, { color: C.textMuted }]}>Active Dasha</Text>
                <View style={s.dashaRow}>
                  <Text style={[s.dashaItem, { color: C.textMuted }]}>{pName(dasha.mdPlanet)} MD</Text>
                  <Feather name="chevron-right" size={10} color={C.textDim} />
                  <Text style={[s.dashaItem, { color: C.textMuted }]}>{pName(dasha.adPlanet)} AD</Text>
                  <Feather name="chevron-right" size={10} color={C.textDim} />
                  <Text style={[s.dashaItem, { color: "#f59e0b" }]}>{pName(dasha.pdPlanet)} PD</Text>
                </View>
              </View>
            )}

            {/* Day navigation row */}
            <View style={s.navRow}>
              <Pressable
                style={[s.navBtn, selected === 0 && s.navBtnDisabled]}
                onPress={() => { if (selected > 0) { setSelected(selected - 1); Haptics.selectionAsync(); } }}
              >
                <Feather name="chevron-left" size={16} color={selected === 0 ? C.textDim : C.text} />
                <Text style={[s.navLabel, { color: C.text }, selected === 0 && { color: C.textDim }]}>Pehle Din</Text>
              </Pressable>
              <View style={s.navDots}>
                {days.map((_, i) => (
                  <Pressable key={i} onPress={() => setSelected(i)}>
                    <View style={[s.navDot, { backgroundColor: C.border }, i === selected && s.navDotActive]} />
                  </Pressable>
                ))}
              </View>
              <Pressable
                style={[s.navBtn, selected === 6 && s.navBtnDisabled]}
                onPress={() => { if (selected < days.length-1) { setSelected(selected + 1); Haptics.selectionAsync(); } }}
              >
                <Text style={[s.navLabel, { color: C.text }, selected === 6 && { color: C.textDim }]}>Agle Din</Text>
                <Feather name="chevron-right" size={16} color={selected === 6 ? C.textDim : C.text} />
              </Pressable>
            </View>
          </>
        )}

        {/* Demo unlock prompt */}
        {showDemo && (
          <Pressable style={s.unlockBanner} onPress={() => router.push("/onboarding")}>
            <Feather name="lock" size={14} color="#fbbf24" />
            <View style={{ flex: 1 }}>
              <Text style={s.unlockTitle}>Personalized Forecast Unlock Karein</Text>
              <Text style={s.unlockSub}>Apni Kundli ke hisaab se daily energy score milega</Text>
            </View>
            <Feather name="chevron-right" size={14} color="#fbbf24" />
          </Pressable>
        )}
      </ScrollView>
    </View>
  );
}

const s = StyleSheet.create({
  root:    { flex: 1, backgroundColor: "#020d1a" },
  header: {
    flexDirection: "row", alignItems: "center",
    paddingHorizontal: 16, paddingBottom: 12, paddingTop: 12, gap: 10,
    borderBottomWidth: 1, borderBottomColor: "rgba(255,255,255,0.04)",
  },
  back:        { padding: 4 },
  headerTitle: { color: "#dde8f4", fontSize: 18, fontWeight: "700", flex: 1 },
  demoPill: {
    backgroundColor: "rgba(251,191,36,0.15)", borderRadius: 10,
    paddingHorizontal: 8, paddingVertical: 2, borderWidth: 1, borderColor: "rgba(251,191,36,0.3)",
  },
  demoPillText: { color: "#fbbf24", fontSize: 10, fontWeight: "600" },

  content: { padding: 16, gap: 14 },

  chartCard: {
    backgroundColor: "#040e1f", borderRadius: 18,
    borderWidth: 1, borderColor: "rgba(255,255,255,0.05)",
    padding: 16, gap: 12,
  },
  chartLabel: { color: "#3d5a7a", fontSize: 11, fontWeight: "600", letterSpacing: 0.8, textTransform: "uppercase" },
  chartPlaceholder: { height: 90, alignItems: "center", justifyContent: "center" },
  placeholderText: { color: "#1e3a5f" },

  dayHeader: {
    flexDirection: "row", justifyContent: "space-between", alignItems: "center",
  },
  dayName:  { color: "#dde8f4", fontSize: 18, fontWeight: "700" },
  dayDate:  { color: "#3d5a7a", fontSize: 12 },
  scoreCircle: {
    width: 60, height: 60, borderRadius: 30,
    borderWidth: 2, alignItems: "center", justifyContent: "center", gap: 1,
  },
  scoreNum:   { fontSize: 20, fontWeight: "800" },
  scoreLabel: { color: "#3d5a7a", fontSize: 9 },

  summaryCard: {
    backgroundColor: "#040e1f", borderRadius: 16,
    borderWidth: 1, borderColor: "rgba(255,255,255,0.05)",
    padding: 14, flexDirection: "row", gap: 10, alignItems: "flex-start",
  },
  summaryText: { color: "#94a3b8", fontSize: 13, lineHeight: 20, flex: 1 },

  infoGrid: { flexDirection: "row", gap: 10 },
  infoItem: {
    flex: 1, backgroundColor: "#040e1f", borderRadius: 14,
    borderWidth: 1, borderColor: "rgba(255,255,255,0.05)",
    padding: 12, alignItems: "center", gap: 4,
  },
  infoIcon:  { fontSize: 18 },
  infoLabel: { color: "#3d5a7a", fontSize: 10, textAlign: "center" },
  infoValue: { color: "#dde8f4", fontSize: 13, fontWeight: "600", textAlign: "center" },

  dashaCard: {
    backgroundColor: "#040e1f", borderRadius: 14,
    borderWidth: 1, borderColor: "rgba(255,255,255,0.04)",
    padding: 12, gap: 6,
  },
  dashaLabel: { color: "#1e3a5f", fontSize: 10, fontWeight: "600", letterSpacing: 1, textTransform: "uppercase" },
  dashaRow:   { flexDirection: "row", alignItems: "center", gap: 6 },
  dashaItem:  { color: "#3d5a7a", fontSize: 12, fontWeight: "600" },

  navRow:    { flexDirection: "row", alignItems: "center", justifyContent: "space-between" },
  navBtn:    { flexDirection: "row", alignItems: "center", gap: 4, padding: 8 },
  navBtnDisabled: { opacity: 0.3 },
  navLabel:  { color: "#dde8f4", fontSize: 12 },
  navDots:   { flexDirection: "row", gap: 6 },
  navDot:    { width: 6, height: 6, borderRadius: 3, backgroundColor: "#1e3a5f" },
  navDotActive: { backgroundColor: "#f59e0b", width: 16 },

  unlockBanner: {
    backgroundColor: "rgba(251,191,36,0.06)", borderRadius: 16,
    borderWidth: 1, borderColor: "rgba(251,191,36,0.2)",
    padding: 16, flexDirection: "row", gap: 12, alignItems: "center",
  },
  unlockTitle: { color: "#fbbf24", fontSize: 13, fontWeight: "600" },
  unlockSub:   { color: "#92704e", fontSize: 11 },
});
