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
import { useC } from "@/context/ThemeContext";
import { useUser } from "@/context/UserContext";
import { API_BASE, apiFetch } from "@/lib/apiConfig";

const SIGNS = [
  "Mesh","Vrishabh","Mithun","Kark","Simha","Kanya",
  "Tula","Vrishchik","Dhanu","Makar","Kumbh","Meen",
];
function moonSign(lon: number): string { return SIGNS[Math.floor(lon / 30) % 12]; }
function moonPhase(date: Date): string {
  const ref = new Date("2000-01-06").getTime();
  const cycle = 29.53058770576;
  const diff = (date.getTime() - ref) / (1000 * 60 * 60 * 24);
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
function scoreToTrend(s: number): "UP" | "MIXED" | "DOWN" {
  return s >= 65 ? "UP" : s <= 40 ? "DOWN" : "MIXED";
}

export default function DashaRiskScreen() {
  const insets = useSafeAreaInsets();
  const C = useC();
  const { kundli, moonData } = useUser();
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
          moonSign: moonSign(demoMoons[i]),
          phase: moonPhase(dt),
          summary: SCORE_SUMMARIES[scoreToTrend(demoScores[i])],
          ...computeRisk(demoScores[i], i, dt),
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
      .then((data: { date: string; positions: Record<string, number> }[]) => {
        const moonLon = moonData?.longitude ?? 0;
        const baseScore = 60;
        const built = data.map((item, i) => {
          const dayOffset   = i;
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
            ...computeRisk(score, i, dt),
          };
        });
        setDays(built);
      })
      .catch(() => setDays([]))
      .finally(() => setLoading(false));
  }, [kundli, moonData, showDemo]);

  const back = () => {
    if (router.canGoBack()) router.back();
    else router.replace("/(tabs)");
  };

  const dayLabel = (d: Date, i: number) => {
    if (i === 0) return "Aaj";
    if (i === 1) return "Kal";
    return fmtDate(d);
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
        { level: "high",   title: "Primary",   reason: day.riskShort,    advice: day.riskKarna },
        { level: "medium", title: "Secondary", reason: day.riskCategory, advice: day.riskDhyan },
        { level: "low",    title: "Watch",     reason: "Routine check",  advice: day.riskRemedy },
      ];
    }
    if (lvl === "med") {
      return [
        { level: "medium", title: "Primary",   reason: day.riskShort,    advice: day.riskKarna },
        { level: "low",    title: "Secondary", reason: day.riskCategory, advice: day.riskDhyan },
      ];
    }
    return [
      { level: "low", title: "Stable", reason: day.riskShort, advice: day.riskKarna },
    ];
  }, [days, selected]);

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
          <Text style={[s.headerTitle, { color: C.text }]}>Risk Radar</Text>
          <Text style={[s.headerSub,   { color: C.textMuted }]}>
            Aane wale 7 dino ka cosmic radar
          </Text>
        </View>
        {showDemo && (
          <View style={[s.demoPill, { borderColor: C.border, backgroundColor: C.bgCard }]}>
            <Feather name="lock" size={9} color={C.textDim} />
            <Text style={[s.demoPillText, { color: C.textDim }]}>DEMO</Text>
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
              Aapka radar tayyar kar rahe hain…
            </Text>
          </View>
        ) : days.length === 0 ? (
          <View style={[s.emptyCard, { backgroundColor: C.bgCard, borderColor: C.border }]}>
            <Text style={s.emptyIcon}>🪐</Text>
            <Text style={[s.emptyTitle, { color: C.text }]}>
              Radar load nahi ho saka
            </Text>
            <Text style={[s.emptyBody, { color: C.textMuted }]}>
              Internet check karein ya thodi der baad phir try karein.
            </Text>
          </View>
        ) : (
          <>
            {/* Day picker — horizontal scroll of 7 day chips */}
            <View>
              <Text style={[s.pickerLabel, { color: C.textMuted }]}>
                APNA DIN CHUNEIN
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

            {/* Sci-fi cosmic radar visualization (separate section, above the card) */}
            <CosmicRadarView risks={radarRisks} />

            {/* Total risks banner — clear count of active threat signals for the day */}
            {(() => {
              const total = radarRisks.length;
              const tone =
                total >= 3 ? "#ef4444" :
                total === 2 ? "#f59e0b" :
                "#4ade80";
              const label =
                total >= 3 ? "HIGH ALERT" :
                total === 2 ? "ELEVATED"   :
                "STABLE";
              const sub =
                selected === 0
                  ? "Aaj 24 ghante mein active threat signals"
                  : `${dayLabel(days[selected].date, selected)} ke 24 ghante mein active signals`;
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
                      TOTAL RISK SIGNALS
                    </Text>
                    <Text style={[s.totalSub, { color: C.textMuted }]}>{sub}</Text>
                  </View>
                  <View style={[s.totalBadge, { backgroundColor: tone }]}>
                    <Text style={s.totalBadgeTxt}>{label}</Text>
                  </View>
                </View>
              );
            })()}

            {/* The consolidated 8-section card */}
            <RiskRadarCard
              days={days}
              selected={selected}
              onSelect={setSelected}
              fullAccess={!showDemo}
            />

            {/* Footer */}
            <Text style={[s.noteFooter, { color: C.textDim }]}>
              Powered by Advanced Cosmic Intelligence
            </Text>
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
