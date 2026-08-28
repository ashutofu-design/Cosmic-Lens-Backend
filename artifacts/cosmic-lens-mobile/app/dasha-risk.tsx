import { Feather } from "@expo/vector-icons";
import { router } from "expo-router";
import * as Haptics from "expo-haptics";
import React, { useEffect, useMemo, useState } from "react";
import {
  ActivityIndicator,
  I18nManager,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { CosmicBg } from "@/components/CosmicBg";
import { CosmicRadarView, Risk24h } from "@/components/CosmicRadarView";
import {
  computeRisk,
  DayForecast,
  fmtDate,
  RiskRadarCard,
} from "@/components/RiskRadarCard";
import { FadeInView, staggerDelay } from "@/components/motion/FadeInView";
import { useC } from "@/context/ThemeContext";
import { useUser } from "@/context/UserContext";
import { useT } from "@/hooks/useT";
import { API_BASE, apiFetch } from "@/lib/apiConfig";
import type { UILang } from "@/lib/i18n";
import { rashiAt } from "@/lib/i18nVedic";
import {
  buildNatalTransitPayload,
  chartSeed,
  natalLagnaSignIndex,
  natalMoonSignIndex,
  parseTransitDayList,
  scorePersonalizedDay,
  type TransitDayEntry,
} from "@/lib/chartPersonalize";
import {
  fetchRiskRadar,
  isRiskRadarOk,
  type PerDayRisk,
  type RiskRadarResponse,
} from "@/lib/riskTextAPI";

function moonSign(lon: number, lang: UILang): string {
  return rashiAt(Math.floor(lon / 30) % 12, lang);
}

function moonPhase(date: Date, lang: UILang): string {
  const ref = new Date("2000-01-06").getTime();
  const cycle = 29.53058770576;
  const diff = (date.getTime() - ref) / (1000 * 60 * 60 * 24);
  const phase = ((diff % cycle) + cycle) % cycle;
  const labels = {
    en: { amavasya: "Amavasya", shukla: "Shukla Paksha", purnima: "Purnima", krishna: "Krishna Paksha" },
    hn: { amavasya: "Amavasya", shukla: "Shukla Paksha", purnima: "Purnima", krishna: "Krishna Paksha" },
    hi: { amavasya: "अमावस्या", shukla: "शुक्ल पक्ष", purnima: "पूर्णिमा", krishna: "कृष्ण पक्ष" },
  }[lang];
  if (phase < 2)  return labels.amavasya;
  if (phase < 7)  return labels.shukla;
  if (phase < 15) return labels.shukla;
  if (phase < 17) return labels.purnima;
  if (phase < 22) return labels.krishna;
  if (phase < 29) return labels.krishna;
  return labels.amavasya;
}

function scoreToTrend(s: number): "UP" | "MIXED" | "DOWN" {
  return s >= 65 ? "UP" : s <= 40 ? "DOWN" : "MIXED";
}

/** Overlay kundli-personalised /api/risk-radar text onto local day cards. */
function mergeRadarIntoDays(
  base: DayForecast[],
  radar: RiskRadarResponse,
  scoreSummary: (trend: "UP" | "MIXED" | "DOWN") => string,
): DayForecast[] {
  const per = Array.isArray(radar.per_day) ? radar.per_day : [];
  const applyOne = (d: DayForecast, pd: PerDayRisk | undefined, i: number): DayForecast => {
    if (!pd && !(i === 0 && radar.top_risk)) return d;
    const top = radar.top_risk;
    const riskDetail = pd?.kya_risk_hai || top?.kya_risk_hai || d.riskDetail;
    const riskAvoid = pd?.kya_avoid_karna_hai || top?.kya_avoid_karna_hai || d.riskAvoid;
    const riskKarna = pd?.kya_karna_hai || top?.kya_karna_hai || d.riskKarna;
    const riskRemedy = pd?.upay || top?.upay || d.riskRemedy;
    const riskLevel = (pd?.risk_level || d.riskLevel) as DayForecast["riskLevel"];
    const riskScore = typeof pd?.risk_score === "number" ? pd.risk_score : d.riskScore;
    const riskShort =
      (pd?.summary || "").trim() ||
      riskDetail.slice(0, 96) ||
      d.riskShort;
    const bestTime = pd?.best_time?.window || (i === 0 ? radar.best_time?.window : undefined) || d.bestTime;
    const avoidTime = pd?.avoid_time?.window || (i === 0 ? radar.avoid_time?.window : undefined) || d.avoidTime;
    let luckyColor = d.luckyColor;
    if (pd?.shubh_rang_name && pd?.shubh_rang_hex) {
      luckyColor = {
        name: pd.shubh_rang_name,
        emoji: d.luckyColor.emoji,
        hex: pd.shubh_rang_hex,
      };
    }
    const luckyNumbers =
      pd?.shubh_ank != null
        ? [pd.shubh_ank, ...d.luckyNumbers.filter((n) => n !== pd.shubh_ank)].slice(0, 3)
        : d.luckyNumbers;
    const energyLike =
      riskLevel === "low" ? 72 : riskLevel === "high" ? 38 : 55;
    return {
      ...d,
      // Keep transit energy when present; still personalise risk readout from API
      summary: scoreSummary(scoreToTrend(d.score || energyLike)),
      riskLevel,
      riskScore,
      riskShort,
      riskCategory: pd?.category || top?.category || d.riskCategory,
      riskDetail,
      riskAvoid,
      riskKarna,
      riskRemedy,
      bestTime,
      avoidTime,
      luckyColor,
      luckyNumbers,
    };
  };

  if (per.length > 0) {
    return base.map((d, i) => applyOne(d, per[i], i));
  }
  if (radar.top_risk && base[0]) {
    return base.map((d, i) => applyOne(d, undefined, i));
  }
  return base;
}

export default function DashaRiskScreen() {
  const insets = useSafeAreaInsets();
  const C = useC();
  const t = useT();
  const { kundli, moonData, birthData, user } = useUser();
  const scoreSummary = (trend: "UP" | "MIXED" | "DOWN") =>
    trend === "UP" ? t.rrScoreUp : trend === "DOWN" ? t.rrScoreDown : t.rrScoreMixed;
  const topPad = Platform.OS === "web" ? 67 : insets.top;
  const botPad = Platform.OS === "web" ? 34 : insets.bottom;
  const showDemo = !kundli;

  const [days, setDays]         = useState<DayForecast[]>([]);
  const [selected, setSelected] = useState(0);   // Today by default
  const [loading, setLoading]   = useState(true);

  // Build 7 dates starting FROM TODAY (Risk Radar focuses on the next 24h
  // first, then onward — different from /forecast which skips today).
  useEffect(() => {
    const dates: string[] = [];
    const today = new Date();
    for (let i = 0; i <= 6; i++) {
      const d = new Date(today);
      d.setDate(today.getDate() + i);
      dates.push(`${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`);
    }

    if (showDemo) {
      const demoScores = [62, 58, 81, 45, 70, 65, 77];
      const demoMoons  = [120, 133, 147, 162, 177, 192, 207];
      setDays(dates.map((ds, i) => {
        const dt = new Date(ds);
        return {
          date: dt,
          score: demoScores[i],
          moonLon: demoMoons[i],
          moonSign: moonSign(demoMoons[i], t.lang),
          phase: moonPhase(dt, t.lang),
          summary: scoreSummary(scoreToTrend(demoScores[i])),
          ...computeRisk(demoScores[i], i, dt, t.lang),
        };
      }));
      return;
    }

    setLoading(true);
    const natal = buildNatalTransitPayload(kundli);
    const seed = chartSeed(kundli, birthData);
    const natalHints = {
      moonSign: natalMoonSignIndex(kundli),
      lagnaSign: natalLagnaSignIndex(kundli),
    };
    const moonLon = moonData?.longitude ?? 0;

    const buildFromList = (list: TransitDayEntry[]) =>
      list.map((item, i) => {
        const dayOffset   = i;
        const transitMoon = Number(item.positions?.Moon ?? (moonLon + dayOffset * 13.2));
        const { score } = scorePersonalizedDay(item, kundli, dayOffset);
        const dt    = new Date(item.date + "T00:00:00");
        return {
          date:     dt,
          score,
          moonLon:  transitMoon,
          moonSign: moonSign(transitMoon, t.lang),
          phase:    moonPhase(dt, t.lang),
          summary:  scoreSummary(scoreToTrend(score)),
          ...computeRisk(score, i, dt, t.lang, seed, natalHints),
        };
      });

    const buildLocal = () =>
      dates.map((ds, i) => {
        const transitMoon = moonLon + i * 13.2;
        const { score } = scorePersonalizedDay(
          { date: ds, positions: { Moon: transitMoon } },
          kundli,
          i,
        );
        const dt = new Date(ds + "T00:00:00");
        return {
          date: dt,
          score,
          moonLon: transitMoon,
          moonSign: moonSign(transitMoon, t.lang),
          phase: moonPhase(dt, t.lang),
          summary: scoreSummary(scoreToTrend(score)),
          ...computeRisk(score, i, dt, t.lang, seed, natalHints),
        };
      });

    const personalizeWithRadar = async (base: DayForecast[]) => {
      const radar = await fetchRiskRadar({
        kundli: kundli as Record<string, unknown>,
        birthData: (birthData as Record<string, unknown>) || undefined,
        userId: user?.id ?? null,
        apiKey: user?.api_key ?? null,
        lang: t.lang,
      });
      if (!isRiskRadarOk(radar) || radar.enriched === false) {
        return base;
      }
      return mergeRadarIntoDays(base, radar, scoreSummary);
    };

    apiFetch(`${API_BASE}/api/transits`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ dates, natal }),
    })
      .then(async r => {
        const data = await r.json().catch(() => null);
        const list = parseTransitDayList(data);
        if (!r.ok || list.length === 0) throw new Error("transits_empty");
        return list;
      })
      .then(async (list: TransitDayEntry[]) => {
        const base = buildFromList(list);
        setDays(await personalizeWithRadar(base));
      })
      .catch(async () => {
        const base = buildLocal();
        try {
          setDays(await personalizeWithRadar(base));
        } catch {
          setDays(base);
        }
      })
      .finally(() => setLoading(false));
  }, [kundli, moonData, birthData, user?.id, user?.api_key, showDemo, t.lang]);

  const back = () => {
    if (router.canGoBack()) router.back();
    else router.replace("/(tabs)");
  };

  const dayLabel = (d: Date, i: number) => {
    if (i === 0) return t.radarDayToday;
    if (i === 1) return t.radarDayTomorrow;
    return fmtDate(d, t.lang);
  };

  // Synthesize 1-3 risk dots for the cosmic radar from the selected day's data.
  // The radar visualization is decorative + indicative — actionable detail lives
  // in the consolidated card below.
  const radarRisks = useMemo<Risk24h[]>(() => {
    const day = days[selected];
    if (!day) return [];
    const lvl = day.riskLevel; // "low" | "med" | "high"
    if (lvl === "high") {
      return [
        { level: "high",   title: t.rrDotPrimary,   reason: day.riskShort,    advice: day.riskKarna },
        { level: "medium", title: t.rrDotSecondary, reason: day.riskCategory, advice: day.riskAvoid },
        { level: "low",    title: t.rrDotWatch,     reason: t.rrDotRoutine,   advice: day.riskRemedy },
      ];
    }
    if (lvl === "med") {
      return [
        { level: "medium", title: t.rrDotPrimary,   reason: day.riskShort,    advice: day.riskKarna },
        { level: "low",    title: t.rrDotSecondary, reason: day.riskCategory, advice: day.riskAvoid },
      ];
    }
    return [
      { level: "low", title: t.rrDotStable, reason: day.riskShort, advice: day.riskKarna },
    ];
  }, [days, selected, t]);

  return (
    <View style={[s.root, { paddingTop: topPad, backgroundColor: C.bg }]}>
      <CosmicBg />

      {/* Header */}
      <View style={[s.header, { borderBottomColor: C.border }]}>
        <Pressable onPress={back} style={s.back} hitSlop={10}>
          <Feather
            name={I18nManager.isRTL ? "arrow-right" : "arrow-left"}
            size={20}
            color={C.textMuted}
          />
        </Pressable>
        <View style={{ flex: 1 }}>
          <Text style={[s.headerTitle, { color: C.text }]}>{t.radarTitle}</Text>
          <Text style={[s.headerSub,   { color: C.textMuted }]}>
            {t.radarHeaderSub}
          </Text>
        </View>
        {showDemo && (
          <View style={[s.demoPill, { borderColor: C.border, backgroundColor: C.bgCard }]}>
            <Feather name="lock" size={9} color={C.textDim} />
            <Text style={[s.demoPillText, { color: C.textDim }]}>{t.ds_demo}</Text>
          </View>
        )}
      </View>

      <ScrollView
        contentContainerStyle={[s.content, { paddingBottom: botPad + 30 }]}
        showsVerticalScrollIndicator={false}
      >
        {loading && days.length === 0 ? (
          <View style={s.loadingBox}>
            <ActivityIndicator size="large" color="#fbbf24" />
            <Text style={[s.loadingTxt, { color: C.textMuted }]}>
              {t.radarLoadingTxt}
            </Text>
          </View>
        ) : days.length === 0 ? (
          <View style={[s.emptyCard, { backgroundColor: C.bgCard, borderColor: C.border }]}>
            <Text style={s.emptyIcon}>🪐</Text>
            <Text style={[s.emptyTitle, { color: C.text }]}>
              {t.radarEmptyTitle}
            </Text>
            <Text style={[s.emptyBody, { color: C.textMuted }]}>
              {t.radarEmptyBody}
            </Text>
          </View>
        ) : (
          <>
            {/* Day picker — horizontal scroll of 7 day chips */}
            <FadeInView delay={staggerDelay(0)}>
            <View>
              <Text style={[s.pickerLabel, { color: C.textMuted }]}>
                {t.radarPickerLabel}
              </Text>
              <ScrollView
                horizontal
                showsHorizontalScrollIndicator={false}
                contentContainerStyle={s.pickerRow}
              >
                {days.map((d, i) => {
                  const active = i === selected;
                  const tone   =
                    d.riskLevel === "low" ? "#4ade80" :
                    d.riskLevel === "med" ? "#fbbf24" : "#ef4444";
                  return (
                    <Pressable
                      key={i}
                      onPress={() => { setSelected(i); Haptics.selectionAsync(); }}
                      style={[
                        s.dayChip,
                        {
                          backgroundColor: active ? `${tone}1a` : C.bgCard,
                          borderColor:     active ? tone : C.border,
                        },
                      ]}
                    >
                      <Text style={[
                        s.dayChipLabel,
                        { color: active ? tone : C.textMuted },
                      ]}>
                        {dayLabel(d.date, i)}
                      </Text>
                      <View style={[s.dayChipDot, { backgroundColor: tone }]} />
                    </Pressable>
                  );
                })}
              </ScrollView>
            </View>
            </FadeInView>

            {/* Sci-fi cosmic radar visualization (separate section, above the card) */}
            <FadeInView delay={staggerDelay(1)}>
            <CosmicRadarView risks={radarRisks} />
            </FadeInView>

            {/* Total risks banner — clear count of active threat signals for the day */}
            <FadeInView delay={staggerDelay(2)}>
            {(() => {
              const total = radarRisks.length;
              const tone =
                total >= 3 ? "#ef4444" :
                total === 2 ? "#f59e0b" :
                "#4ade80";
              const label =
                total >= 3 ? t.radarBadgeHigh :
                total === 2 ? t.radarBadgeMed :
                t.radarBadgeLow;
              const sub =
                selected === 0
                  ? t.radarSubToday
                  : t.radarSubOther.replace("{date}", dayLabel(days[selected].date, selected));
              return (
                <View
                  style={[
                    s.totalBanner,
                    { backgroundColor: `${tone}10`, borderColor: `${tone}40` },
                  ]}
                >
                  <View style={[s.totalNumBox, { backgroundColor: `${tone}22`, borderColor: tone }]}>
                    <Text style={[s.totalNumTxt, { color: tone }]}>{total}</Text>
                  </View>
                  <View style={{ flex: 1 }}>
                    <Text style={[s.totalLabel, { color: tone }]}>
                      {t.radarTotalLabel}
                    </Text>
                    <Text style={[s.totalSub, { color: C.textMuted }]}>{sub}</Text>
                  </View>
                  <View style={[s.totalBadge, { backgroundColor: tone }]}>
                    <Text style={s.totalBadgeTxt}>{label}</Text>
                  </View>
                </View>
              );
            })()}
            </FadeInView>

            {/* The consolidated 8-section card */}
            <FadeInView delay={staggerDelay(3)}>
            <RiskRadarCard
              days={days}
              selected={selected}
              onSelect={setSelected}
              fullAccess={!showDemo}
            />
            </FadeInView>

            {/* Footer */}
            <FadeInView delay={staggerDelay(4)}>
            <Text style={[s.noteFooter, { color: C.textDim }]}>
              {t.rrLuckyPoweredBy}
            </Text>
            </FadeInView>
          </>
        )}
      </ScrollView>
    </View>
  );
}

const s = StyleSheet.create({
  root: { flex: 1 },
  header: {
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    gap: 12,
  },
  back: { padding: 4 },
  headerTitle: { fontSize: 18, fontWeight: "800", letterSpacing: 0.3 },
  headerSub:   { fontSize: 11, fontWeight: "500", marginTop: 1 },
  demoPill: {
    flexDirection: "row", alignItems: "center", gap: 4,
    paddingHorizontal: 7, paddingVertical: 3,
    borderRadius: 8, borderWidth: 1,
  },
  demoPillText: { fontSize: 9, fontWeight: "800", letterSpacing: 1 },

  content: { padding: 16, gap: 14 },

  loadingBox: { alignItems: "center", paddingVertical: 60, gap: 12 },
  loadingTxt: { fontSize: 13, fontWeight: "500" },

  emptyCard: {
    borderRadius: 14, borderWidth: 1, padding: 24,
    alignItems: "center", gap: 10,
  },
  emptyIcon:  { fontSize: 36 },
  emptyTitle: { fontSize: 15, fontWeight: "800", textAlign: "center" },
  emptyBody:  { fontSize: 12, fontWeight: "500", textAlign: "center", lineHeight: 17 },

  pickerLabel: {
    fontSize: 10, fontWeight: "800", letterSpacing: 1.4,
    marginBottom: 8, marginLeft: 2,
  },
  pickerRow: { flexDirection: "row", gap: 8, paddingRight: 4 },
  dayChip: {
    paddingHorizontal: 12, paddingVertical: 8,
    borderRadius: 10, borderWidth: 1,
    flexDirection: "row", alignItems: "center", gap: 6,
    minWidth: 64, justifyContent: "center",
  },
  dayChipLabel: { fontSize: 12, fontWeight: "700" },
  dayChipDot:   { width: 6, height: 6, borderRadius: 3 },

  noteFooter: {
    fontSize: 10, fontWeight: "600",
    textAlign: "center", letterSpacing: 0.6,
    marginTop: 6,
  },

  totalBanner: {
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
    padding: 12,
    borderRadius: 14,
    borderWidth: 1,
  },
  totalNumBox: {
    width: 48, height: 48, borderRadius: 24,
    borderWidth: 2,
    alignItems: "center", justifyContent: "center",
  },
  totalNumTxt: {
    fontSize: 22, fontWeight: "900",
  },
  totalLabel: {
    fontSize: 11, fontWeight: "800", letterSpacing: 1.4,
  },
  totalSub: {
    fontSize: 11, fontWeight: "500", marginTop: 2,
  },
  totalBadge: {
    paddingHorizontal: 9, paddingVertical: 5,
    borderRadius: 8,
  },
  totalBadgeTxt: {
    fontSize: 9, fontWeight: "900",
    letterSpacing: 1.2,
    color: "#0b0f1a",
  },
});
