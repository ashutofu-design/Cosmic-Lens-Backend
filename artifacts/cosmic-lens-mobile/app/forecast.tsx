import { Feather } from "@expo/vector-icons";
import { router } from "expo-router";
import * as Haptics from "expo-haptics";
import React, { useEffect, useState } from "react";
import {
  I18nManager,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";
import Svg, { Circle, Defs, G, Line, LinearGradient as SvgGrad, Path, Rect, Stop, Text as SvgText } from "react-native-svg";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useC } from "@/context/ThemeContext";
import { useUser } from "@/context/UserContext";
import { useT } from "@/hooks/useT";

import { API_BASE, apiFetch } from "@/lib/apiConfig";

const MONTHS_SHORT = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
const fmtDate = (d: Date) => `${d.getDate()} ${MONTHS_SHORT[d.getMonth()]}`;

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

// ── shapeJourney — same exact transform the home EnergyChart uses ────────────
//   Turns raw scores into an always-rising visual sweep that ENDS at the real
//   final value. Mid-points carry a small wiggle proportional to their actual
//   score so the line still has personality, but the overall arc is the same
//   "journey upward" shape the home chart shows.
function shapeJourney(rawPts: number[]): number[] {
  if (rawPts.length === 0) return [];
  const final = rawPts[rawPts.length - 1];
  const len   = rawPts.length;
  const shaped: number[] = [];
  for (let i = 0; i < len; i++) {
    const t           = len <= 1 ? 1 : i / (len - 1);
    const envelope    = Math.pow(t, 1.4);
    const rawNorm     = rawPts[i] / 100;
    const wiggle      = (rawNorm - 0.5) * 0.35;
    const base        = final * envelope;
    const startOffset = (1 - t) * 8;
    let val           = base + wiggle * final - startOffset;
    val = Math.max(2, Math.min(98, val));
    if (i === len - 1) val = final;
    shaped.push(Math.round(val));
  }
  return shaped;
}

// ── Week chart — pixel-aligned with home EnergyChart ────────────────────────
//   Identical viewBox, padding, gradient defs, grid lines, area fill,
//   stroke widths, dot halos, callout box and footer text. Only differences
//   from the home chart: 7 points (vs 12), date x-axis labels (vs day names),
//   and the "selected" dot replaces home's "final/Now" dot for callouts.
function WeekChart({
  days, scores, selected, onSelect,
}: {
  days: DayForecast[]; scores: number[]; selected: number;
  onSelect: (i: number) => void;
}) {
  const C = useC();
  // Match home EnergyChart exactly.
  const VW  = 340;
  const VH  = 260;
  const PL  = 30;
  const PR  = 14;
  const PT  = 16;
  const GW  = VW - PL - PR;
  const GH  = 190;
  const BOT = PT + GH;

  const N    = scores.length;
  const px   = (i: number) => PL + (N <= 1 ? GW / 2 : (i / (N - 1)) * GW);
  const py   = (v: number) => PT + (1 - v / 100) * GH;

  // VISUAL y-positions = always-rising journey (matches home).
  // Real scores still drive the callout text + the per-day cards below.
  const journeyPts = shapeJourney(scores);

  const buildLinePath = () => {
    if (journeyPts.length < 2) return "";
    let d = `M ${px(0).toFixed(1)},${py(journeyPts[0]).toFixed(1)}`;
    for (let i = 1; i < N; i++) {
      const x0 = px(i - 1), y0 = py(journeyPts[i - 1]);
      const x1 = px(i),     y1 = py(journeyPts[i]);
      const cpx = (x0 + x1) / 2;
      d += ` C ${cpx.toFixed(1)},${y0.toFixed(1)} ${cpx.toFixed(1)},${y1.toFixed(1)} ${x1.toFixed(1)},${y1.toFixed(1)}`;
    }
    return d;
  };

  const linePath = buildLinePath();
  const areaPath = `${linePath} L ${px(N-1).toFixed(1)},${BOT} L ${px(0).toFixed(1)},${BOT} Z`;

  const YGRID = [
    { v: 100, y: PT },
    { v:  75, y: PT + GH * 0.25 },
    { v:  50, y: PT + GH * 0.50 },
    { v:  25, y: PT + GH * 0.75 },
    { v:   0, y: BOT },
  ];

  const gridLine   = C.isDark ? "rgba(255,255,255,0.05)" : "rgba(140,100,200,0.08)";
  const gridStrong = C.isDark ? "rgba(255,255,255,0.07)" : "rgba(140,100,200,0.12)";
  const axisLabel  = C.isDark ? "rgba(255,255,255,0.18)" : "rgba(140,100,200,0.4)";
  const footerText = C.isDark ? "rgba(255,255,255,0.10)" : "rgba(140,100,200,0.35)";
  const calloutBg  = C.isDark ? "rgba(0,20,10,0.85)" : "rgba(255,255,255,0.92)";

  // Color of the selected dot (and its callout border) on the gradient.
  const tSel = N <= 1 ? 1 : selected / (N - 1);
  const selClr = tSel < 0.2 ? "#ff3b3b"
    : tSel < 0.4 ? "#ff8c00"
    : tSel < 0.6 ? "#ffd700"
    : tSel < 0.8 ? "#f59e0b"
    : "#00ff99";

  const sx = px(selected);
  const sy = py(journeyPts[selected] ?? 0);   // visual position rides the journey curve
  const realScore = scores[selected] ?? 0;     // actual score shown inside the callout

  return (
    <Svg viewBox={`0 0 ${VW} ${VH}`} width="100%" height="100%" style={{ display: "flex" }}>
      <Defs>
        {/* Identical gradient ids/stops to home EnergyChart. */}
        <SvgGrad id="wg-line" x1={PL} y1="0" x2={PL + GW} y2="0" gradientUnits="userSpaceOnUse">
          <Stop offset="0%"   stopColor="#ff3b3b" />
          <Stop offset="20%"  stopColor="#ff8c00" />
          <Stop offset="40%"  stopColor="#ffd700" />
          <Stop offset="60%"  stopColor="#f59e0b" />
          <Stop offset="100%" stopColor="#00ff99" />
        </SvgGrad>
        <SvgGrad id="wg-area" x1="0" y1={PT} x2="0" y2={BOT} gradientUnits="userSpaceOnUse">
          <Stop offset="0%"   stopColor={C.isDark ? "#00ffcc" : "#9f7aea"} stopOpacity={0.18} />
          <Stop offset="50%"  stopColor={C.isDark ? "#00ffcc" : "#9f7aea"} stopOpacity={0.06} />
          <Stop offset="100%" stopColor={C.isDark ? "#00ffcc" : "#9f7aea"} stopOpacity={0} />
        </SvgGrad>
      </Defs>

      {/* y-axis grid (same dash + opacity as home) */}
      {YGRID.map(({ v, y: gy }) => (
        <G key={v}>
          <Line
            x1={PL} y1={gy} x2={PL + GW} y2={gy}
            stroke={v === 0 || v === 100 ? gridStrong : gridLine}
            strokeWidth={v === 0 || v === 100 ? 0.8 : 0.5}
            strokeDasharray={v === 0 || v === 100 ? undefined : "3,8"}
          />
          <SvgText x={PL - 6} y={gy + 3} textAnchor="end" fill={axisLabel} fontSize={7}>
            {v}
          </SvgText>
        </G>
      ))}

      {scores.length > 1 && <Path d={areaPath} fill="url(#wg-area)" />}

      {scores.length > 1 && (
        <Path d={linePath} fill="none" stroke="url(#wg-line)" strokeWidth={14} opacity={0.06} strokeLinecap="round" strokeLinejoin="round" />
      )}

      {scores.length > 1 && (
        <Path d={linePath} fill="none" stroke="url(#wg-line)" strokeWidth={2.8} strokeLinecap="round" strokeLinejoin="round" />
      )}

      {/* Non-selected dot markers — same r=4 halo + r=2 dot as home.
          y is shaped (journeyPts[i]) so all dots ride the rising sweep. */}
      {scores.map((_, i) => {
        if (i === selected) return null;
        const t = N <= 1 ? 0 : i / (N - 1);
        const color = t < 0.2 ? "#ff3b3b"
          : t < 0.4 ? "#ff8c00"
          : t < 0.6 ? "#ffd700"
          : t < 0.8 ? "#f59e0b"
          : "#00ff99";
        const x = px(i), y = py(journeyPts[i]);
        return (
          <G key={i}>
            <Circle cx={x} cy={y} r={4} fill={color} opacity={0.10} />
            <Circle cx={x} cy={y} r={2} fill={color} />
          </G>
        );
      })}

      {/* Selected dot — pulse-style halo nest matching home's "final dot" */}
      {scores.length > 0 && (
        <G>
          <Circle cx={sx} cy={sy} r={12}  fill={selClr} opacity={0.07} />
          <Circle cx={sx} cy={sy} r={7}   fill={selClr} opacity={0.14} />
          <Circle cx={sx} cy={sy} r={4.5} fill={selClr} opacity={0.9} />
          <Circle cx={sx} cy={sy} r={1.8} fill="white"  opacity={0.95} />
        </G>
      )}

      {/* Selected score callout — same rect/stroke/font as home's final callout.
          Edge-aware placement (left of dot by default; flips right if clipped). */}
      {scores.length > 0 && (() => {
        const W = 38, H = 21, GAP = 14;
        const minX = PL - 4;
        const maxX = PL + GW + 4 - W;
        let cx = sx - W - GAP;
        if (cx < minX) cx = sx + GAP;
        cx = Math.max(minX, Math.min(maxX, cx));
        const tx = cx + W / 2;
        return (
          <G>
            <Rect x={cx} y={sy - 14} width={W} height={H} rx={7}
              fill={calloutBg} stroke={selClr} strokeOpacity={0.5} strokeWidth={0.8} />
            <SvgText x={tx} y={sy + 2.5} textAnchor="middle" fill={selClr} fontSize={11} fontWeight="800">
              {realScore}
            </SvgText>
          </G>
        );
      })()}

      {/* Invisible tap targets — placed AFTER markers so they catch presses.
          Use journey y-positions so taps line up with the visible dots. */}
      {scores.map((_, i) => {
        const x = px(i), y = py(journeyPts[i]);
        return (
          <Circle
            key={`tap-${i}`}
            cx={x} cy={y} r={16} fill="transparent"
            onPress={() => { onSelect(i); Haptics.selectionAsync(); }}
          />
        );
      })}

      {/* Date labels on x-axis (replaces home's "Now" + sparse weekday labels) */}
      {days.map((d, i) => {
        const isSel = i === selected;
        return (
          <SvgText key={i}
            x={px(i)} y={BOT + 16}
            textAnchor="middle"
            fill={isSel ? selClr : axisLabel}
            fontSize={isSel ? 8 : 7}
            fontWeight={isSel ? "700" : "400"}>
            {fmtDate(d.date)}
          </SvgText>
        );
      })}

      {/* Footer signature — same exact line as home */}
      <SvgText x={VW / 2} y={VH - 4} textAnchor="middle" fill={footerText} fontSize={5.5} letterSpacing={2.5}>
        NAVATARA  ·  MOON TRANSIT  ·  ASHTAKAVARGA
      </SvgText>
    </Svg>
  );
}

export default function ForecastScreen() {
  const insets   = useSafeAreaInsets();
  const C = useC();
  const t = useT();
  const { kundli, moonData } = useUser();
  const topPad   = Platform.OS === "web" ? 67 : insets.top;
  const botPad   = Platform.OS === "web" ? 34 : insets.bottom;
  const showDemo = !kundli;

  const [days, setDays]       = useState<DayForecast[]>([]);
  // Default to the LAST day so the score callout sits on the rightmost (green
  // gradient end) — exactly like home's "Now" dot. User can tap any other day
  // to move the highlight; the curve always rises toward whichever day is selected.
  const [selected, setSelected] = useState(6);
  const [loading, setLoading]   = useState(false);

  // Build 7 dates starting from TOMORROW (today is shown on the home screen,
  // so the forecast page exclusively shows the next 7 days for planning).
  useEffect(() => {
    const dates: string[] = [];
    const today = new Date();
    for (let i = 1; i <= 7; i++) {
      const d = new Date(today);
      d.setDate(today.getDate() + i);
      dates.push(`${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,"0")}-${String(d.getDate()).padStart(2,"0")}`);
    }

    if (showDemo) {
      const demoScores = [58, 81, 45, 70, 65, 77, 62];
      const demoMoons  = [133, 147, 162, 177, 192, 207, 222];
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
    apiFetch(`${API_BASE}/api/transits`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ dates }),
    })
      .then(r => r.json())
      .then((data: { date: string; positions: Record<string,number> }[]) => {
        const moonLon = moonData?.longitude ?? 0;
        // Use a stable mid-range baseline so projected scores aren't pinned to today's
        // specific value (this page is forward-looking trends, not today's reading).
        const baseScore = 60;

        const built = data.map((item, i) => {
          // Forecast index: i=0 → tomorrow, i=6 → today + 7. Offset by +1 day for moon estimate.
          const dayOffset   = i + 1;
          const transitMoon = item.positions?.Moon ?? (moonLon + dayOffset * 13.2);
          const variation   = Math.sin(dayOffset * 1.3) * 12 + (item.positions?.Jupiter ? 5 : 0)
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
        // API failed — clear days so UI shows the empty/error state
        // (avoid fake scores that would mislead user into thinking it's real data)
        setDays([]);
      })
      .finally(() => setLoading(false));
  }, [kundli, moonData, showDemo]);

  const sel = days[selected];
  const scoreColor = sel
    ? (sel.score >= 65 ? "#4ade80" : sel.score <= 40 ? "#ef4444" : "#fbbf24")
    : "#f59e0b";

  return (
    <View style={[s.root, { paddingTop: topPad, backgroundColor: C.bg }]}>
      {/* Header */}
      <View style={[s.header, { borderBottomColor: C.border }]}>
        <Pressable onPress={() => router.back()} style={s.back}>
          <Feather name={I18nManager.isRTL ? "arrow-right" : "arrow-left"} size={20} color={C.textMuted} />
        </Pressable>
        <Text style={[s.headerTitle, { color: C.text }]}>{t.forecastTitle}</Text>
        {showDemo && (
          <View style={s.demoPill}>
            <Text style={s.demoPillText}>{t.fc_demo}</Text>
          </View>
        )}
      </View>

      <ScrollView contentContainerStyle={[s.content, { paddingBottom: botPad + 30 }]} showsVerticalScrollIndicator={false}>
        {/* Hero forecast card — mirrors the home HeroEnergyCard exactly:
            same #0f0a24 background, score-tinted border + outer glow, top row
            with label + selected score, chart filling the body, insight pill
            at the bottom. Sized with a fixed minHeight so it has the same big
            immersive presence the home card gets from `flex: 1` on home. */}
        <View style={[
          s.heroCard,
          {
            backgroundColor: "#0f0a24",
            borderColor: `${scoreColor}40`,
            shadowColor: scoreColor,
          },
        ]}>
          {/* Top row — "ENERGY FORECAST" label + DEMO badge + selected score */}
          <View style={s.heroTopRow}>
            <View style={{ flexDirection: "row", alignItems: "center", gap: 6 }}>
              <Text style={[s.heroLabel, { color: "rgba(255,255,255,0.45)" }]}>
                {t.forecastTitle?.toUpperCase?.() ?? "ENERGY FORECAST"}
              </Text>
              {showDemo && (
                <View style={[s.heroDemoBadge, { backgroundColor: C.bgCard2 ?? C.bgCard, borderColor: C.border }]}>
                  <Feather name="lock" size={8} color={C.textDim} />
                  <Text style={[s.heroDemoBadgeText, { color: C.textDim }]}>{t.fc_demo ?? "DEMO"}</Text>
                </View>
              )}
            </View>
            {sel && (
              <View style={{ flexDirection: "row", alignItems: "flex-end", gap: 2 }}>
                <Text style={[s.heroScore, { color: scoreColor }]}>{sel.score}</Text>
                <Text style={[s.heroScoreMax, { color: C.textDim }]}>/100</Text>
              </View>
            )}
          </View>

          {/* Chart — flex:1 so it fills the remaining card height, exactly like home */}
          <View style={{ flex: 1, minHeight: 240 }}>
            {days.length > 0 ? (
              <WeekChart
                days={days}
                scores={days.map(d => d.score)}
                selected={selected}
                onSelect={setSelected}
              />
            ) : (
              <View style={s.chartPlaceholder}>
                <Text style={[s.placeholderText, { color: C.textMuted }]}>
                  {loading ? t.loading : t.forecastError}
                </Text>
              </View>
            )}
          </View>

          {/* Insight pill — selected day's summary, styled like home's insightPill */}
          {sel && (
            <View style={{ flexDirection: "row", alignItems: "center" }}>
              <View style={[s.heroInsightPill, { backgroundColor: `${scoreColor}10`, borderColor: `${scoreColor}30` }]}>
                <Feather name="sun" size={11} color={scoreColor} />
                <Text style={[s.heroInsightText, { color: scoreColor }]} numberOfLines={1}>
                  {sel.date.toLocaleDateString("en-IN", { weekday: "short", day: "numeric", month: "short" })} · {sel.summary}
                </Text>
              </View>
            </View>
          )}
        </View>

        {/* Selected day detail */}
        {sel && (
          <>
            {/* Moon info */}
            <View style={s.infoGrid}>
              <View style={[s.infoItem, { backgroundColor: C.bgCard, borderColor: C.border }]}>
                <Text style={s.infoIcon}>🌙</Text>
                <Text style={[s.infoLabel, { color: C.textMuted }]}>{t.fc_moonRashi}</Text>
                <Text style={[s.infoValue, { color: C.text }]}>{sel.moonSign}</Text>
              </View>
              <View style={[s.infoItem, { backgroundColor: C.bgCard, borderColor: C.border }]}>
                <Text style={s.infoIcon}>🔮</Text>
                <Text style={[s.infoLabel, { color: C.textMuted }]}>{t.fc_paksha}</Text>
                <Text style={[s.infoValue, { color: C.text }]}>{sel.phase}</Text>
              </View>
              <View style={[s.infoItem, { backgroundColor: C.bgCard, borderColor: C.border }]}>
                <Text style={s.infoIcon}>⚡</Text>
                <Text style={[s.infoLabel, { color: C.textMuted }]}>{t.fc_energy}</Text>
                <Text style={[s.infoValue, { color: scoreColor }]}>
                  {sel.score >= 65 ? "Uchch" : sel.score <= 40 ? "Neech" : "Madhyam"}
                </Text>
              </View>
            </View>

            {/* Lock hint — every day on this page is a future day, full personal
                reading + remedies unlock on the home screen on that day itself.
                This is the daily-return hook the product depends on. */}
            <View style={[s.lockHint, { backgroundColor: C.bgCard, borderColor: C.border }]}>
              <Feather name="lock" size={12} color="#fbbf24" />
              <Text style={[s.lockHintText, { color: C.textMuted }]}>
                Us din ki full reading + remedies us din ke arrival pe home screen pe khulengi
              </Text>
            </View>

            {/* Day navigation row */}
            <View style={s.navRow}>
              <Pressable
                style={[s.navBtn, selected === 0 && s.navBtnDisabled]}
                onPress={() => { if (selected > 0) { setSelected(selected - 1); Haptics.selectionAsync(); } }}
              >
                <Feather name={I18nManager.isRTL ? "chevron-right" : "chevron-left"} size={16} color={selected === 0 ? C.textDim : C.text} />
                <Text style={[s.navLabel, { color: C.text }, selected === 0 && { color: C.textDim }]}>{t.prevDay}</Text>
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
                <Text style={[s.navLabel, { color: C.text }, selected === 6 && { color: C.textDim }]}>{t.nextDay}</Text>
                <Feather name={I18nManager.isRTL ? "chevron-left" : "chevron-right"} size={16} color={selected === 6 ? C.textDim : C.text} />
              </Pressable>
            </View>
          </>
        )}

        {/* Demo unlock prompt */}
        {showDemo && (
          <Pressable style={s.unlockBanner} onPress={() => router.push("/onboarding")}>
            <Feather name="lock" size={14} color="#fbbf24" />
            <View style={{ flex: 1 }}>
              <Text style={s.unlockTitle}>{t.unlockForecastTitle}</Text>
              <Text style={s.unlockSub}>{t.unlockForecastSub}</Text>
            </View>
            <Feather name={I18nManager.isRTL ? "chevron-left" : "chevron-right"} size={14} color="#fbbf24" />
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

  // ── Hero forecast card — dimensionally + visually identical to home HeroEnergyCard ──
  heroCard: {
    borderRadius: 16, borderWidth: 1,
    paddingHorizontal: 10, paddingTop: 10, paddingBottom: 8,
    overflow: "hidden", gap: 4,
    minHeight: 380,                           // big immersive presence (home gets this from flex:1)
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.28, shadowRadius: 24, elevation: 5,
  },
  heroTopRow: {
    flexDirection: "row", alignItems: "center",
    justifyContent: "space-between",
  },
  heroLabel:    { fontSize: 8.5, fontWeight: "700", letterSpacing: 2 },
  heroScore:    { fontSize: 28, fontWeight: "800", letterSpacing: -1, lineHeight: 32 },
  heroScoreMax: { fontSize: 12, fontWeight: "600", paddingBottom: 3 },
  heroDemoBadge: {
    flexDirection: "row", alignItems: "center", gap: 3,
    borderWidth: 1, paddingVertical: 2,
    paddingHorizontal: 6, borderRadius: 5,
  },
  heroDemoBadgeText: { fontSize: 7, fontWeight: "700", letterSpacing: 1.2 },
  heroInsightPill: {
    flexDirection: "row", alignItems: "center", gap: 5,
    borderWidth: 1, borderRadius: 7, paddingVertical: 4, paddingHorizontal: 8,
    flexShrink: 1, maxWidth: "100%",
  },
  heroInsightText: { fontSize: 10, fontWeight: "600", flexShrink: 1 },

  chartPlaceholder: { flex: 1, alignItems: "center", justifyContent: "center" },
  placeholderText: { color: "#1e3a5f" },

  infoGrid: { flexDirection: "row", gap: 10 },
  infoItem: {
    flex: 1, backgroundColor: "#040e1f", borderRadius: 14,
    borderWidth: 1, borderColor: "rgba(255,255,255,0.05)",
    padding: 12, alignItems: "center", gap: 4,
  },
  infoIcon:  { fontSize: 18 },
  infoLabel: { color: "#3d5a7a", fontSize: 10, textAlign: "center" },
  infoValue: { color: "#dde8f4", fontSize: 13, fontWeight: "600", textAlign: "center" },

  lockHint:   { flexDirection: "row", alignItems: "center", gap: 8, padding: 12, borderRadius: 10, borderWidth: 1 },
  lockHintText: { fontSize: 12, flex: 1, fontWeight: "500" },

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
