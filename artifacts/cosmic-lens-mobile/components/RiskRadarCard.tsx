import { Feather } from "@expo/vector-icons";
import AsyncStorage from "@react-native-async-storage/async-storage";
import { router } from "expo-router";
import * as Haptics from "expo-haptics";
import React, { useEffect, useState } from "react";
import { I18nManager, Pressable, StyleSheet, Text, View } from "react-native";
import { useC } from "@/context/ThemeContext";
import { useT } from "@/hooks/useT";
import type { UILang } from "@/lib/i18n";
import { getRiskBucket } from "@/lib/riskRadarContent";

const MONTHS_EN = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
const MONTHS_HI = ["जन","फ़र","मार्च","अप्रै","मई","जून","जुल","अग","सित","अक्टू","नव","दिस"];

export const fmtDate = (d: Date, lang: UILang = "en") => {
  const months = lang === "hi" ? MONTHS_HI : MONTHS_EN;
  return `${d.getDate()} ${months[d.getMonth()]}`;
};

export type RiskLevel = "low" | "med" | "high";
export interface LuckyColor { name: string; emoji: string; hex: string; }

export interface DayForecast {
  date: Date;
  score: number;
  moonLon: number;
  moonSign: string;
  phase: string;
  summary: string;
  riskLevel:    RiskLevel;
  riskScore:    number;
  riskShort:    string;
  riskCategory: string;
  riskDetail:   string;
  riskAvoid:    string;
  riskKarna:    string;
  riskRemedy:   string;
  luckyNumbers: number[];
  luckyColor:   LuckyColor;
  bestTime:     string;
  avoidTime:    string;
}

export function scoreToRiskScore(score: number): number {
  return Math.round(Math.max(0, Math.min(10, (100 - score) / 7)));
}
export function scoreToRiskLevel(rs: number): RiskLevel {
  if (rs <= 3) return "low";
  if (rs <= 6) return "med";
  return "high";
}

const BEST_TIME_SLOTS = [
  "10:30 AM — 12:45 PM", "8:00 AM — 10:15 AM", "4:30 PM — 6:30 PM",
  "11:00 AM — 1:15 PM", "9:00 AM — 11:00 AM", "5:00 PM — 7:00 PM",
  "7:30 AM — 9:45 AM",
];
const AVOID_TIME_SLOTS = [
  "3:15 PM — 5:00 PM", "1:00 PM — 2:30 PM", "7:00 PM — 8:30 PM",
  "2:30 PM — 4:00 PM", "12:30 PM — 2:00 PM", "8:00 PM — 9:30 PM",
  "1:45 PM — 3:15 PM",
];

/** Moon-sign lucky digits — same table as the Lucky screen (Mesh=1,9 …). */
const RASHI_LUCKY_NUMS: number[][] = [
  [1, 9], [2, 6], [3, 5], [2, 7], [1, 4], [5, 6],
  [6, 8], [1, 9], [3, 9], [8, 4], [4, 8], [3, 7],
];

/** Canonical Hinglish names so Forecast i18n (Suneheri → Golden) still maps. */
const RASHI_LUCKY_COLOR: LuckyColor[] = [
  { name: "Kesari",   emoji: "🟠", hex: "#ef4444" },
  { name: "Safed",    emoji: "⚪", hex: "#f8fafc" },
  { name: "Hara",     emoji: "🟢", hex: "#84cc16" },
  { name: "Safed",    emoji: "⚪", hex: "#e2e8f0" },
  { name: "Suneheri", emoji: "🟠", hex: "#f59e0b" },
  { name: "Hara",     emoji: "🟢", hex: "#22c55e" },
  { name: "Neela",    emoji: "🔵", hex: "#60a5fa" },
  { name: "Kesari",   emoji: "🟠", hex: "#f43f5e" },
  { name: "Pila",     emoji: "🟡", hex: "#eab308" },
  { name: "Neela",    emoji: "🔵", hex: "#1d4ed8" },
  { name: "Neela",    emoji: "🔵", hex: "#7dd3fc" },
  { name: "Pila",     emoji: "🟡", hex: "#fef08a" },
];

export type NatalLuckyHints = {
  moonSign: number;
  lagnaSign: number;
};

function dayHash(dateMs: number): number { return Math.floor(dateMs / 86400000); }

/** Mix calendar-day with chart seed (NOT dateMs+seed — seed is << 1 day in ms). */
function chartDayMix(dateMs: number, chartSeed: number, salt = 0): number {
  return Math.abs(dayHash(dateMs) * 10007 + Math.abs(chartSeed) * 7919 + salt * 104729);
}

function getLuckyNumbers(dateMs: number, chartSeed: number, natal?: NatalLuckyHints): number[] {
  const moon = ((natal?.moonSign ?? (Math.abs(chartSeed) % 12)) + 12) % 12;
  const lagna = ((natal?.lagnaSign ?? 0) + 12) % 12;
  const pair = RASHI_LUCKY_NUMS[moon];
  const mix = chartDayMix(dateMs, chartSeed, lagna + 1);
  const primary = pair[mix % pair.length];
  const secondary = pair[(mix + 1) % pair.length];
  const tertiary = 1 + ((mix + moon + lagna) % 9);
  const nums = [primary, secondary, tertiary].filter((n, i, a) => a.indexOf(n) === i);
  while (nums.length < 3) nums.push(1 + ((mix + nums.length * 11) % 9));
  return nums.slice(0, 3);
}

function getLuckyColor(dateMs: number, chartSeed: number, natal?: NatalLuckyHints): LuckyColor {
  const moon = ((natal?.moonSign ?? (Math.abs(chartSeed) % 12)) + 12) % 12;
  const lagna = ((natal?.lagnaSign ?? 0) + 12) % 12;
  const mix = chartDayMix(dateMs, chartSeed, 3);
  const sign = mix % 2 === 0 ? moon : lagna;
  return RASHI_LUCKY_COLOR[sign % 12];
}

function getBestTime(dateMs: number, chartSeed: number, natal?: NatalLuckyHints): string {
  const moon = natal?.moonSign ?? 0;
  const lagna = natal?.lagnaSign ?? 0;
  const idx = chartDayMix(dateMs, chartSeed, moon * 3 + lagna * 5 + 1) % BEST_TIME_SLOTS.length;
  return BEST_TIME_SLOTS[idx];
}

function getAvoidTime(dateMs: number, chartSeed: number, natal?: NatalLuckyHints): string {
  const moon = natal?.moonSign ?? 0;
  const lagna = natal?.lagnaSign ?? 0;
  const bestIdx = chartDayMix(dateMs, chartSeed, moon * 3 + lagna * 5 + 1) % AVOID_TIME_SLOTS.length;
  let idx = chartDayMix(dateMs, chartSeed, moon * 3 + lagna * 5 + 2) % AVOID_TIME_SLOTS.length;
  if (idx === bestIdx) idx = (idx + 3) % AVOID_TIME_SLOTS.length;
  return AVOID_TIME_SLOTS[idx];
}

export function computeRisk(
  score: number,
  _dayIdx: number,
  date: Date,
  lang: UILang = "en",
  chartSeed = 0,
  natal?: NatalLuckyHints,
) {
  const riskScore = scoreToRiskScore(score);
  const level     = scoreToRiskLevel(riskScore);
  const bucket    = getRiskBucket(lang, level);
  const dateMs    = date.getTime();
  const dh        = chartDayMix(dateMs, chartSeed);
  const shortLine = bucket.shorts[dh % bucket.shorts.length];
  const det       = bucket.details[dh % bucket.details.length];
  return {
    riskLevel: level,
    riskScore,
    riskShort:    shortLine,
    riskCategory: det.cat,
    riskDetail:   det.detail,
    riskAvoid:    det.avoid,
    riskKarna:    det.karna,
    riskRemedy:   det.remedy,
    luckyNumbers: getLuckyNumbers(dateMs, chartSeed, natal),
    luckyColor:   getLuckyColor(dateMs, chartSeed, natal),
    bestTime:     getBestTime(dateMs, chartSeed, natal),
    avoidTime:    getAvoidTime(dateMs, chartSeed, natal),
  };
}

// ── Cosmic Risk Radar Card ──────────────────────────────────────────────────
//   The single consolidated 8-section card that bundles every "next-24-hours"
//   signal: gauge, week chips, 24-hour breakdown (4 quadrants), upay, lucky
//   numbers, lucky color, best-time, avoid-time. Streak counter at top-right
//   increments once per UTC day via AsyncStorage and only renders when ≥ 2.
//
//   Premium gating: when `fullAccess=false`, only Day 1 (selected=0) is
//   unlocked; Days 2-7 show the upgrade card with a "Day 1 free hai" inner
//   tap fallback that bounces the user back to the unlocked day.
const FREE_DAYS = 1;

export function RiskRadarCard({
  days, selected, onSelect, fullAccess,
}: {
  days: DayForecast[]; selected: number; onSelect: (i: number) => void; fullAccess: boolean;
}) {
  const C = useC();
  const t = useT();
  // Risk fields come from parent (dasha-risk merges /api/risk-radar per kundli).

  const [streak, setStreak] = useState(0);
  useEffect(() => {
    (async () => {
      try {
        const today  = new Date().toISOString().slice(0, 10);
        const last   = await AsyncStorage.getItem("@cl_radar_last_open");
        const cntStr = await AsyncStorage.getItem("@cl_radar_streak");
        const cnt    = parseInt(cntStr || "0", 10) || 0;
        if (last === today) { setStreak(cnt); return; }
        const yest = new Date(); yest.setUTCDate(yest.getUTCDate() - 1);
        const yestStr = yest.toISOString().slice(0, 10);
        const newCnt  = (last === yestStr) ? (cnt + 1) : 1;
        await AsyncStorage.setItem("@cl_radar_last_open", today);
        await AsyncStorage.setItem("@cl_radar_streak",    String(newCnt));
        setStreak(newCnt);
      } catch { /* AsyncStorage unavailable — streak stays 0, badge hides */ }
    })();
  }, []);

  if (days.length === 0) return null;
  const sel = days[selected];
  if (!sel) return null;

  // Risk fields on `sel` come from parent — preferably /api/risk-radar
  // (kundli + DOB personalised). Local computeRisk() is fallback only.
  const selData: DayForecast = sel;

  // (The "Aaj Ka Shubh Ank + Rang" resolver that used to live here moved
  // to the Forecast screen along with the lucky panel. This card now
  // renders only the per-day risk readout.)

  let safestIdx = 0, riskiestIdx = 0;
  days.forEach((d, i) => {
    if (d.riskScore < days[safestIdx].riskScore)   safestIdx   = i;
    if (d.riskScore > days[riskiestIdx].riskScore) riskiestIdx = i;
  });

  const isLocked   = !fullAccess && selected >= FREE_DAYS;
  // Gauge reflects the SELECTED day's real risk (per_day score when API is
  // live — otherwise local template). Color + label + marker all derive
  // from selData so Days 2-7 also show the engine-driven score, not the
  // stale local one.
  const levelColor =
    selData.riskLevel === "low" ? "#4ade80" :
    selData.riskLevel === "med" ? "#fbbf24" : "#ef4444";
  // Localized level badge label. Indic scripts have no case so .toUpperCase()
  // is a safe no-op for them; for Latin scripts (EN/HN) it yields LOW/MED/HIGH
  // matching the original visual treatment.
  const levelLabel = (
    selData.riskLevel === "low"  ? t.rrLevelLow  :
    selData.riskLevel === "med"  ? t.rrLevelMed  : t.rrLevelHigh
  ).toUpperCase();
  const markerPct  = `${(selData.riskScore / 10) * 100}%` as `${number}%`;

  return (
    <View style={[s.card, { backgroundColor: C.bgCard, borderColor: C.border }]}>
      {/* Header */}
      <View style={s.head}>
        <View style={s.titleRow}>
          <Feather name="alert-triangle" size={13} color="#fbbf24" />
          <Text style={[s.title, { color: C.text }]}>{t.rrCardTitle}</Text>
        </View>
        <View style={s.headRight}>
          {streak >= 2 && (
            <View style={s.streakPill}>
              <Text style={s.streakPillText}>🔥 {streak}</Text>
            </View>
          )}
          <Text style={[s.headHint, { color: C.textDim }]}>
            {t.rrDayOf7.replace("{n}", String(selected + 1))}
          </Text>
        </View>
      </View>

      {/* Week highlights */}
      <View style={s.chipsRow}>
        <Pressable
          onPress={() => { onSelect(safestIdx); Haptics.selectionAsync(); }}
          style={[s.chip, { backgroundColor: "rgba(74,222,128,0.10)", borderColor: "rgba(74,222,128,0.30)" }]}
        >
          <Text style={[s.chipLabel, { color: "#4ade80" }]}>{t.rrSafestChip}</Text>
          <Text style={[s.chipDay,   { color: C.text }]}>{fmtDate(days[safestIdx].date, t.lang)}</Text>
        </Pressable>
        <Pressable
          onPress={() => { onSelect(riskiestIdx); Haptics.selectionAsync(); }}
          style={[s.chip, { backgroundColor: "rgba(239,68,68,0.10)", borderColor: "rgba(239,68,68,0.30)" }]}
        >
          <Text style={[s.chipLabel, { color: "#ef4444" }]}>{t.rrChallengingChip}</Text>
          <Text style={[s.chipDay,   { color: C.text }]}>{fmtDate(days[riskiestIdx].date, t.lang)}</Text>
        </Pressable>
      </View>

      {isLocked ? (
        <Pressable
          style={[s.lockedCard, { backgroundColor: "rgba(251,191,36,0.06)", borderColor: "rgba(251,191,36,0.30)" }]}
          onPress={() => router.push("/onboarding")}
        >
          <View style={s.lockedTop}>
            <Feather name="lock" size={14} color="#fbbf24" />
            <Text style={s.lockedTitle}>
              {t.rrLockedTitle.replace("{date}", fmtDate(sel.date, t.lang))}
            </Text>
          </View>
          <Text style={s.lockedSub}>{t.rrLockedSub}</Text>
          <Pressable
            onPress={(e) => { e.stopPropagation?.(); onSelect(0); Haptics.selectionAsync(); }}
            style={[s.lockedHint, { borderColor: C.border }]}
          >
            <Text style={[s.lockedHintText, { color: C.textMuted }]}>
              {t.rrLockedHint}
            </Text>
          </Pressable>
          <View style={s.lockedCta}>
            <Text style={s.lockedCtaText}>{t.rrLockedCta}</Text>
            <Feather name={I18nManager.isRTL ? "arrow-left" : "arrow-right"} size={11} color="#fbbf24" />
          </View>
        </Pressable>
      ) : (
        <>
          {/* Gauge */}
          <View style={s.gaugeHead}>
            <Text style={[s.gaugeMicro, { color: C.textMuted }]}>{t.rrLabelRiskLevel.toUpperCase()}</Text>
            <View style={{ flexDirection: "row", alignItems: "center", gap: 6 }}>
              <Text style={[s.gaugeLevel, { color: levelColor   }]}>{levelLabel}</Text>
              <Text style={[s.gaugeValue, { color: C.textMuted  }]}>{selData.riskScore}/10</Text>
            </View>
          </View>
          <View style={s.gaugeTrack}>
            <View style={[s.gaugeSeg, { backgroundColor: "rgba(74,222,128,0.22)",  borderTopLeftRadius: 4, borderBottomLeftRadius: 4 }]} />
            <View style={[s.gaugeSeg, { backgroundColor: "rgba(251,191,36,0.22)" }]} />
            <View style={[s.gaugeSeg, { backgroundColor: "rgba(239,68,68,0.22)",   borderTopRightRadius: 4, borderBottomRightRadius: 4 }]} />
            <View style={[s.gaugeMarker, { left: markerPct, backgroundColor: levelColor, shadowColor: levelColor }]} />
          </View>
          <View style={s.gaugeScale}>
            <Text style={[s.gaugeScaleText, { color: C.textDim }]}>{t.rrLevelLow}</Text>
            <Text style={[s.gaugeScaleText, { color: C.textDim }]}>{t.rrLevelMed}</Text>
            <Text style={[s.gaugeScaleText, { color: C.textDim }]}>{t.rrLevelHigh}</Text>
          </View>

          {/* Generic warning line — risk content (short, detail, avoid, karna,
              upay) is fully derived from the per-day Energy Score by the local
              deterministic computeRisk(), so it's immediately ready and never
              needs a spinner. */}
          <View style={[s.shortRow, { borderColor: C.border }]}>
            <Text style={s.shortIcon}>💬</Text>
            <Text style={[s.shortText, { color: C.text }]}>{selData.riskShort}</Text>
          </View>

          {/* 24-hour breakdown */}
          <View style={s.bdHead}>
            <Feather name="clock" size={11} color={C.textMuted} />
            <Text style={[s.bdHeadText, { color: C.textMuted }]}>
              {selected === 0
                ? t.rrSection24hToday
                : t.rrSection24hWithDate.replace(
                    "{date}",
                    fmtDate(sel.date, t.lang).toUpperCase(),
                  )}
            </Text>
          </View>

          <View style={[s.bdRow, { backgroundColor: `${levelColor}10`, borderColor: `${levelColor}30` }]}>
            <View style={[s.bdIconBox, { backgroundColor: `${levelColor}22` }]}>
              <Feather name="alert-triangle" size={14} color={levelColor} />
            </View>
            <View style={s.bdText}>
              <Text style={[s.bdLabel, { color: levelColor }]}>{t.rrLabelKyaRisk.toUpperCase()}</Text>
              <Text style={[s.bdBody,  { color: C.text     }]}>{selData.riskDetail}</Text>
            </View>
          </View>

          <View style={[s.bdRow, { backgroundColor: "rgba(239,68,68,0.08)", borderColor: "rgba(239,68,68,0.25)" }]}>
            <View style={[s.bdIconBox, { backgroundColor: "rgba(239,68,68,0.22)" }]}>
              <Feather name="x-circle" size={14} color="#ef4444" />
            </View>
            <View style={s.bdText}>
              <Text style={[s.bdLabel, { color: "#ef4444" }]}>{t.rrLabelKyaAvoid.toUpperCase()}</Text>
              <Text style={[s.bdBody,  { color: C.text    }]}>{selData.riskAvoid}</Text>
            </View>
          </View>

          <View style={[s.bdRow, { backgroundColor: "rgba(74,222,128,0.08)", borderColor: "rgba(74,222,128,0.25)" }]}>
            <View style={[s.bdIconBox, { backgroundColor: "rgba(74,222,128,0.22)" }]}>
              <Feather name="check-circle" size={14} color="#4ade80" />
            </View>
            <View style={s.bdText}>
              <Text style={[s.bdLabel, { color: "#4ade80" }]}>{t.rrLabelKyaKarna.toUpperCase()}</Text>
              <Text style={[s.bdBody,  { color: C.text    }]}>{selData.riskKarna}</Text>
            </View>
          </View>

          {/* Mini upay */}
          <View style={[s.remedyRow, { backgroundColor: C.bgCard, borderColor: C.border }]}>
            <Text style={s.remedyIcon}>🪔</Text>
            <View style={{ flex: 1 }}>
              <Text style={[s.remedyLabel, { color: C.textMuted }]}>{t.rrLabelUpay.toUpperCase()}</Text>
              <Text style={[s.remedyText,  { color: C.text      }]}>{selData.riskRemedy}</Text>
            </View>
          </View>

          {/* The Shubh Ank/Rang + Best Time/Avoid Time + brand footer panel
              that used to live here has been moved to the Forecast screen
              (app/forecast.tsx) so this card stays focused on the day's
              risk readout (kya risk hai / kya avoid karna / kya karna /
              upay) — and the Lucky panel has a single canonical home. */}
        </>
      )}
    </View>
  );
}

const s = StyleSheet.create({
  card: { borderRadius: 14, borderWidth: 1, padding: 14, gap: 12 },
  poweredBy: { fontSize: 10, fontWeight: "600", letterSpacing: 0.6,
                textAlign: "center", marginTop: 2, opacity: 0.8 },
  head: { flexDirection: "row", alignItems: "center", justifyContent: "space-between" },
  titleRow: { flexDirection: "row", alignItems: "center", gap: 8 },
  title:    { fontSize: 14, fontWeight: "800", letterSpacing: 0.3 },
  headRight: { flexDirection: "row", alignItems: "center", gap: 8 },
  headHint:  { fontSize: 10, fontWeight: "600", letterSpacing: 1 },

  streakPill: {
    backgroundColor: "rgba(251,146,60,0.14)",
    borderWidth: 1, borderColor: "rgba(251,146,60,0.40)",
    paddingHorizontal: 7, paddingVertical: 2, borderRadius: 10,
  },
  streakPillText: { color: "#fb923c", fontSize: 10, fontWeight: "800", letterSpacing: 0.4 },

  chipsRow: { flexDirection: "row", gap: 8 },
  chip:     { flex: 1, borderRadius: 10, borderWidth: 1, paddingVertical: 8, paddingHorizontal: 10, gap: 2 },
  chipLabel:{ fontSize: 9, fontWeight: "800", letterSpacing: 1.2 },
  chipDay:  { fontSize: 12, fontWeight: "700" },

  gaugeHead: { flexDirection: "row", alignItems: "center", justifyContent: "space-between" },
  gaugeMicro:{ fontSize: 10, fontWeight: "800", letterSpacing: 1.4 },
  gaugeLevel:{ fontSize: 12, fontWeight: "800", letterSpacing: 1 },
  gaugeValue:{ fontSize: 11, fontWeight: "700" },
  gaugeTrack:{ flexDirection: "row", height: 8, borderRadius: 4, overflow: "visible", position: "relative" },
  gaugeSeg:  { flex: 1, height: 8 },
  gaugeMarker: {
    position: "absolute", top: -3, width: 14, height: 14, borderRadius: 7,
    marginLeft: -7, shadowOpacity: 0.8, shadowRadius: 6, shadowOffset: { width: 0, height: 0 }, elevation: 4,
  },
  gaugeScale: { flexDirection: "row", justifyContent: "space-between", marginTop: 2 },
  gaugeScaleText: { fontSize: 9, fontWeight: "600", letterSpacing: 1 },

  shortRow: {
    flexDirection: "row", alignItems: "center", gap: 8,
    paddingVertical: 8, paddingHorizontal: 10, borderRadius: 8, borderWidth: 1,
  },
  shortIcon: { fontSize: 13 },
  shortText: { flex: 1, fontSize: 12, fontWeight: "600", lineHeight: 16 },

  bdHead:     { flexDirection: "row", alignItems: "center", gap: 6, marginTop: 4 },
  bdHeadText: { fontSize: 10, fontWeight: "800", letterSpacing: 1.4 },
  bdRow: {
    flexDirection: "row", alignItems: "flex-start", gap: 10,
    padding: 10, borderRadius: 10, borderWidth: 1,
  },
  bdIconBox: {
    width: 28, height: 28, borderRadius: 8,
    alignItems: "center", justifyContent: "center", flexShrink: 0,
  },
  bdText:  { flex: 1, gap: 3 },
  bdLabel: { fontSize: 9,  fontWeight: "800", letterSpacing: 1.2 },
  bdBody:  { fontSize: 12, fontWeight: "500", lineHeight: 17 },

  remedyRow: {
    flexDirection: "row", alignItems: "center", gap: 10,
    padding: 10, borderRadius: 10, borderWidth: 1,
  },
  remedyIcon:  { fontSize: 18 },
  remedyLabel: { fontSize: 9,  fontWeight: "800", letterSpacing: 1.4, marginBottom: 2 },
  remedyText:  { fontSize: 12, fontWeight: "600", lineHeight: 16 },

  luckyGrid: { flexDirection: "row", gap: 8 },
  luckyTile: {
    flex: 1, borderRadius: 10, borderWidth: 1,
    paddingVertical: 10, paddingHorizontal: 10, gap: 8,
    minHeight: 64, justifyContent: "space-between",
  },
  luckyTileLabel: { fontSize: 9, fontWeight: "800", letterSpacing: 1.2 },
  luckyNumRow:    { flexDirection: "row", gap: 6, flexWrap: "wrap" },
  luckyNumPill: {
    minWidth: 28, paddingHorizontal: 6, paddingVertical: 3,
    borderRadius: 6, borderWidth: 1, alignItems: "center",
    backgroundColor: "rgba(251,191,36,0.10)",
  },
  luckyNumText: { fontSize: 12, fontWeight: "800", letterSpacing: 0.5 },
  luckyColorRow:    { flexDirection: "row", alignItems: "center", gap: 8 },
  luckyColorSwatch: { width: 20, height: 20, borderRadius: 10, borderWidth: 1 },
  luckyColorName:   { fontSize: 13, fontWeight: "700" },
  luckyTimeText:    { fontSize: 12, fontWeight: "700", letterSpacing: 0.3 },

  // ── Personalised "Aaj Ka Shubh Ank" + "Aaj Ka Shubh Rang" hero card ──
  shubhCard: {
    borderRadius: 12, borderWidth: 1, padding: 12, gap: 10,
  },
  shubhRow: {
    flexDirection: "row", alignItems: "stretch",
  },
  shubhAnkBox:  { flex: 1, alignItems: "flex-start", gap: 6 },
  shubhRangBox: { flex: 1, alignItems: "flex-start", gap: 6, paddingLeft: 12 },
  shubhDivider: { width: 1, backgroundColor: "rgba(255,255,255,0.10)" },
  shubhMicro:   { fontSize: 9, fontWeight: "800", letterSpacing: 1.2 },
  shubhAnkBadge: {
    width: 56, height: 56, borderRadius: 28, borderWidth: 2,
    alignItems: "center", justifyContent: "center",
  },
  shubhAnkText: { fontSize: 26, fontWeight: "900", letterSpacing: 0.5 },
  shubhRangRow: { flexDirection: "row", alignItems: "center", gap: 10, paddingTop: 6 },
  shubhSwatch:  { width: 36, height: 36, borderRadius: 18, borderWidth: 1 },
  shubhRangName:{ fontSize: 16, fontWeight: "800" },
  shubhReason:  { fontSize: 12, fontWeight: "500", lineHeight: 17 },
  shubhFooter:  { fontSize: 9, fontWeight: "700", letterSpacing: 1.2, textAlign: "right" },

  lockedCard:     { borderRadius: 10, borderWidth: 1, padding: 12, gap: 8 },
  lockedTop:      { flexDirection: "row", alignItems: "center", gap: 8 },
  lockedTitle:    { color: "#fbbf24", fontSize: 12, fontWeight: "700", flex: 1 },
  lockedSub:      { color: "#92704e", fontSize: 11, lineHeight: 15 },
  lockedHint: {
    flexDirection: "row", alignItems: "center",
    paddingVertical: 7, paddingHorizontal: 10,
    borderRadius: 8, borderWidth: 1,
  },
  lockedHintText: { fontSize: 11, fontWeight: "600" },
  lockedCta:      { flexDirection: "row", alignItems: "center", gap: 4, marginTop: 2, alignSelf: "flex-start" },
  lockedCtaText:  { color: "#fbbf24", fontSize: 10, fontWeight: "800", letterSpacing: 1.5 },
});
