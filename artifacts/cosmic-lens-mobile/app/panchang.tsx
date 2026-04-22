import { Feather } from "@expo/vector-icons";
import { LinearGradient } from "expo-linear-gradient";
import { router, useLocalSearchParams } from "expo-router";
import * as Haptics from "expo-haptics";
import React, { useMemo, useState } from "react";
import { ScrollView, StyleSheet, Text, View, Pressable } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { CosmicBg } from "@/components/CosmicBg";
import { useC } from "@/context/ThemeContext";
import { useT } from "@/hooks/useT";
import {
  FESTIVALS_BY_YEAR, FESTIVAL_YEARS, daysUntil, type Festival,
} from "@/data/festivals10y";

const F = {
  bold: "Nunito_700Bold", semibold: "Nunito_600SemiBold",
  medium: "Nunito_500Medium", regular: "Nunito_400Regular",
};

// ── Approximate Panchang calculation ─────────────────────────────────────────
function getPanchang(date: Date) {
  const TITHIS = ["Pratipada","Dwitiya","Tritiya","Chaturthi","Panchami","Shashthi","Saptami","Ashtami","Navami","Dashami","Ekadashi","Dwadashi","Trayodashi","Chaturdashi","Purnima/Amavasya"];
  const NAKSHATRAS = ["Ashwini","Bharani","Krittika","Rohini","Mrigashira","Ardra","Punarvasu","Pushya","Ashlesha","Magha","Purva Phalguni","Uttara Phalguni","Hasta","Chitra","Swati","Vishakha","Anuradha","Jyeshtha","Mula","Purva Ashadha","Uttara Ashadha","Shravana","Dhanishtha","Shatabhisha","Purva Bhadrapada","Uttara Bhadrapada","Revati"];
  const YOGAS = ["Vishkambha","Priti","Ayushman","Saubhagya","Shobhana","Atiganda","Sukarma","Dhriti","Shula","Ganda","Vriddhi","Dhruva","Vyaghata","Harshana","Vajra","Siddhi","Vyatipata","Variyana","Parigha","Shiva","Siddha","Sadhya","Shubha","Shukla","Brahma","Indra","Vaidhriti"];
  const KARANAS = ["Bava","Balava","Kaulava","Taitila","Gara","Vanija","Vishti","Shakuni","Chatushpada","Naga","Kimstughna"];
  const PAKSHA = ["Shukla","Krishna"];
  const DAYS = ["Ravivaar","Somvar","Mangalvar","Budhavar","Guruvaar","Shukravar","Shanivaar"];

  // Simple approximation using day-of-year
  const doy = Math.floor((date.getTime() - new Date(date.getFullYear(), 0, 0).getTime()) / 86400000);
  const lunar = Math.floor(((doy * 12.37) % 30));
  const tithi = TITHIS[lunar % 15];
  const paksha = lunar < 15 ? PAKSHA[0] : PAKSHA[1];
  const nakshatra = NAKSHATRAS[doy % 27];
  const yoga = YOGAS[doy % 27];
  const karana = KARANAS[doy % 11];
  const var_ = DAYS[date.getDay()];

  return { tithi: `${paksha} ${tithi}`, nakshatra, yoga, karana, var: var_ };
}

// ── Auspicious Score (Shubh Prataishaat) ─────────────────────────────────────
// Composite 0-100 score based on classical Vedic shubh-ashubh mapping of
// tithi / nakshatra / yoga / karana / vaar.
const SHUBH_TITHIS  = ["Dwitiya","Tritiya","Panchami","Saptami","Dashami","Ekadashi","Trayodashi","Purnima/Amavasya"];
const ASHUBH_TITHIS = ["Chaturthi","Navami","Chaturdashi"];
const SHUBH_NAKS    = ["Rohini","Mrigashira","Pushya","Hasta","Anuradha","Shravana","Revati","Uttara Phalguni","Uttara Ashadha","Uttara Bhadrapada","Swati"];
const ASHUBH_NAKS   = ["Bharani","Krittika","Ashlesha","Magha","Mula","Jyeshtha","Vishakha"];
const SHUBH_YOGAS   = ["Priti","Ayushman","Saubhagya","Shobhana","Sukarma","Dhriti","Vriddhi","Dhruva","Harshana","Siddhi","Variyana","Shiva","Siddha","Sadhya","Shubha","Brahma","Indra"];
const ASHUBH_YOGAS  = ["Vishkambha","Atiganda","Shula","Ganda","Vyaghata","Vajra","Vyatipata","Parigha","Vaidhriti"];
const VISHTI_KARANA = "Vishti";   // Bhadra — strictly avoid
const SHUBH_VARS    = ["Somvar","Budhavar","Guruvaar","Shukravar"];
const ASHUBH_VARS   = ["Shanivaar"];

function getAuspiciousScore(p: { tithi: string; nakshatra: string;
                                  yoga: string; karana: string; var: string }) {
  const reasons: { good: string[]; bad: string[] } = { good: [], bad: [] };
  let score = 50;

  // Tithi
  const tCore = p.tithi.split(" ").slice(-1)[0];
  if (SHUBH_TITHIS.includes(tCore)) { score += 12; reasons.good.push(`Tithi ${tCore} shubh hai`); }
  else if (ASHUBH_TITHIS.includes(tCore)) { score -= 12; reasons.bad.push(`Tithi ${tCore} kamzor hai`); }
  if (p.tithi.includes("Krishna") && tCore === "Chaturdashi") {
    score -= 5; reasons.bad.push("Krishna Chaturdashi — naye karya talein");
  }

  // Nakshatra
  if (SHUBH_NAKS.includes(p.nakshatra))  { score += 14; reasons.good.push(`${p.nakshatra} nakshatra anukool`); }
  else if (ASHUBH_NAKS.includes(p.nakshatra)) { score -= 14; reasons.bad.push(`${p.nakshatra} nakshatra ki saavdhani`); }

  // Yoga
  if (SHUBH_YOGAS.includes(p.yoga))  { score += 10; reasons.good.push(`${p.yoga} yoga shubh`); }
  else if (ASHUBH_YOGAS.includes(p.yoga)) { score -= 10; reasons.bad.push(`${p.yoga} yoga me dhyan rakhein`); }

  // Karana
  if (p.karana === VISHTI_KARANA) {
    score -= 15; reasons.bad.push("Vishti (Bhadra) karana — koi shubh karya na karein");
  } else {
    score += 4; reasons.good.push(`${p.karana} karana neutral-positive`);
  }

  // Vaar (day)
  if (SHUBH_VARS.includes(p.var))  { score += 6; reasons.good.push(`${p.var} shubh vaar`); }
  else if (ASHUBH_VARS.includes(p.var)) { score -= 4; reasons.bad.push(`${p.var} pe Shani prabhav — slow & steady`); }

  score = Math.max(5, Math.min(98, score));

  let band: "Bahut Shubh" | "Shubh" | "Mishrit" | "Saavdhani";
  let color: string;
  let emoji: string;
  if (score >= 78)      { band = "Bahut Shubh"; color = "#22c55e"; emoji = "🌟"; }
  else if (score >= 60) { band = "Shubh";       color = "#84cc16"; emoji = "✨"; }
  else if (score >= 40) { band = "Mishrit";     color = "#f59e0b"; emoji = "⚖️"; }
  else                  { band = "Saavdhani";   color = "#ef4444"; emoji = "⚠️"; }

  return { score, band, color, emoji,
           good: reasons.good.slice(0, 4),
           bad:  reasons.bad.slice(0, 3) };
}

function getRahuKaal(dayIdx: number) {
  const RK = [
    "4:30 PM – 6:00 PM", "7:30 AM – 9:00 AM", "3:00 PM – 4:30 PM",
    "12:00 PM – 1:30 PM", "1:30 PM – 3:00 PM", "10:30 AM – 12:00 PM", "9:00 AM – 10:30 AM"
  ];
  const YAMA = [
    "12:00 PM – 1:30 PM", "10:30 AM – 12:00 PM", "9:00 AM – 10:30 AM",
    "7:30 AM – 9:00 AM", "3:00 PM – 4:30 PM", "1:30 PM – 3:00 PM", "4:30 PM – 6:00 PM"
  ];
  const GULIKA = [
    "3:00 PM – 4:30 PM", "1:30 PM – 3:00 PM", "12:00 PM – 1:30 PM",
    "10:30 AM – 12:00 PM", "9:00 AM – 10:30 AM", "7:30 AM – 9:00 AM", "6:00 AM – 7:30 AM"
  ];
  return { rahu: RK[dayIdx], yama: YAMA[dayIdx], gulika: GULIKA[dayIdx] };
}

export default function PanchangScreen() {
  const C = useC();
  const t = useT();
  const insets = useSafeAreaInsets();
  const params = useLocalSearchParams<{ tab?: string }>();
  const initTab = params.tab === "rahu" ? 1 : params.tab === "festivals" ? 2 : 0;
  const [tabIdx, setTabIdx] = useState(initTab);
  const TABS = [t.panchangTitle, t.rahukaal, t.festivals];

  const today = useMemo(() => { const d = new Date(); d.setHours(0,0,0,0); return d; }, []);
  const [selectedDate, setSelectedDate] = useState<Date>(today);
  const panchang = useMemo(() => getPanchang(selectedDate), [selectedDate]);
  const kaal = useMemo(() => getRahuKaal(selectedDate.getDay()), [selectedDate]);
  const auspicious = useMemo(() => getAuspiciousScore(panchang), [panchang]);
  const [festYear, setFestYear] = useState<number>(today.getFullYear() < 2026 ? 2026 : today.getFullYear());

  const dateStr = selectedDate.toLocaleDateString("hi-IN", { weekday: "long", day: "numeric", month: "long", year: "numeric" });
  const isToday = selectedDate.getTime() === today.getTime();
  const dayDiff = Math.round((selectedDate.getTime() - today.getTime()) / 86400000);
  const relLabel = dayDiff === 0 ? "Aaj"
                  : dayDiff === 1 ? "Kal"
                  : dayDiff === -1 ? "Kal (beeta)"
                  : dayDiff === 2 ? "Parso"
                  : dayDiff === -2 ? "Parso (beeta)"
                  : dayDiff > 0 ? `${dayDiff} din baad`
                  : `${Math.abs(dayDiff)} din pehle`;
  function shiftDate(days: number) {
    Haptics.selectionAsync();
    const d = new Date(selectedDate);
    d.setDate(d.getDate() + days);
    d.setHours(0,0,0,0);
    setSelectedDate(d);
  }

  const SUNRISE = "06:14 AM";
  const SUNSET  = "06:47 PM";

  function InfoRow({ label, value, emoji }: { label: string; value: string; emoji: string }) {
    return (
      <View style={[pr.row, { borderBottomColor: C.border3 }]}>
        <Text style={{ fontSize: 20 }}>{emoji}</Text>
        <View style={{ flex: 1 }}>
          <Text style={[pr.rowLabel, { color: C.textMuted }]}>{label}</Text>
          <Text style={[pr.rowVal, { color: C.text }]}>{value}</Text>
        </View>
      </View>
    );
  }

  return (
    <View style={{ flex: 1 }}>
      <CosmicBg />
      <View style={[s.topBar, { paddingTop: insets.top + 10 }]}>
        <Pressable onPress={() => router.back()} style={s.backBtn}>
          <Feather name="arrow-left" size={20} color={C.text} />
        </Pressable>
        <View>
          <Text style={[s.title, { color: C.text }]}>{t.panchangTitle}</Text>
          <Text style={[s.sub, { color: C.textMuted }]}>{dateStr}</Text>
        </View>
        <View style={{ width: 36 }} />
      </View>

      {/* Date navigator — kal/aaj/parso */}
      <View style={[s.dateNav, { backgroundColor: C.bgCard, borderColor: C.border }]}>
        <Pressable onPress={() => shiftDate(-1)} style={s.dateNavBtn} hitSlop={8}>
          <Feather name="chevron-left" size={20} color={C.text} />
        </Pressable>
        <View style={{ flex: 1, alignItems: "center" }}>
          <Text style={[s.dateNavRel, { color: isToday ? "#a78bfa" : C.textMuted }]}>{relLabel}</Text>
          <Text style={[s.dateNavDate, { color: C.text }]} numberOfLines={1}>
            {selectedDate.toLocaleDateString("en-GB", { weekday: "short", day: "numeric", month: "short", year: "numeric" })}
          </Text>
        </View>
        <Pressable onPress={() => shiftDate(1)} style={s.dateNavBtn} hitSlop={8}>
          <Feather name="chevron-right" size={20} color={C.text} />
        </Pressable>
        {!isToday && (
          <Pressable
            onPress={() => { Haptics.selectionAsync(); setSelectedDate(today); }}
            style={[s.todayPill, { backgroundColor: "#a78bfa" }]}
          >
            <Text style={s.todayPillText}>Aaj</Text>
          </Pressable>
        )}
      </View>

      {/* Tabs */}
      <ScrollView horizontal showsHorizontalScrollIndicator={false} style={{ flexGrow: 0 }} contentContainerStyle={{ paddingHorizontal: 16, gap: 8, paddingBottom: 12 }}>
        {TABS.map((tab, i) => (
          <Pressable
            key={tab}
            onPress={() => { Haptics.selectionAsync(); setTabIdx(i); }}
            style={[s.tab, { borderColor: C.border }, tabIdx === i && { backgroundColor: "#a78bfa", borderColor: "#a78bfa" }]}
          >
            <Text style={[s.tabText, { color: tabIdx === i ? "#fff" : C.textMuted }]}>{tab}</Text>
          </Pressable>
        ))}
      </ScrollView>

      <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={{ paddingHorizontal: 16, paddingBottom: insets.bottom + 100, gap: 14 }}>

        {/* ── PANCHANG TAB ── */}
        {tabIdx === 0 && (
          <>
            {/* Sunrise/Sunset */}
            <View style={[s.sunRow, { backgroundColor: C.bgCard, borderColor: C.border }]}>
              <View style={s.sunItem}>
                <Text style={{ fontSize: 24 }}>🌅</Text>
                <View>
                  <Text style={[s.sunLabel, { color: C.textMuted }]}>{t.panSunrise}</Text>
                  <Text style={[s.sunVal, { color: C.isDark ? "#f59e0b" : "#92400E" }]}>{SUNRISE}</Text>
                </View>
              </View>
              <View style={[s.sunDivider, { backgroundColor: C.border }]} />
              <View style={s.sunItem}>
                <Text style={{ fontSize: 24 }}>🌇</Text>
                <View>
                  <Text style={[s.sunLabel, { color: C.textMuted }]}>{t.panSunset}</Text>
                  <Text style={[s.sunVal, { color: "#fb923c" }]}>{SUNSET}</Text>
                </View>
              </View>
            </View>

            {/* ── 1) AAJ KI DATE — full date hero ───────────────────────── */}
            <LinearGradient
              colors={C.isDark ? ["#1e1b4b", "#0f172a"] : ["#ede9fe", "#ddd6fe"]}
              start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }}
              style={[s.dateHero, { borderColor: C.border }]}
            >
              <Text style={[s.dateHeroDay, { color: C.isDark ? "#a78bfa" : "#7c3aed" }]}>
                {today.toLocaleDateString("en-US", { weekday: "long" }).toUpperCase()}
              </Text>
              <Text style={[s.dateHeroNum, { color: C.text }]}>
                {today.getDate()}
              </Text>
              <Text style={[s.dateHeroMonth, { color: C.text }]}>
                {today.toLocaleDateString("en-US", { month: "long" })} {today.getFullYear()}
              </Text>
              <Text style={[s.dateHeroHindi, { color: C.textMuted }]}>
                {dateStr}
              </Text>
            </LinearGradient>

            {/* ── 2) AUSPICIOUS PERCENTAGE — score card ─────────────────── */}
            <View style={[s.auspCard, { backgroundColor: C.bgCard, borderColor: auspicious.color + "55" }]}>
              <View style={s.auspHeader}>
                <View style={{ flex: 1 }}>
                  <Text style={[s.auspLabel, { color: C.textMuted }]}>
                    AAJ KI SHUBHATA
                  </Text>
                  <Text style={[s.auspBand, { color: auspicious.color }]}>
                    {auspicious.emoji} {auspicious.band}
                  </Text>
                </View>
                <View style={[s.auspScoreCircle, { borderColor: auspicious.color }]}>
                  <Text style={[s.auspScoreNum, { color: auspicious.color }]}>
                    {auspicious.score}
                  </Text>
                  <Text style={[s.auspScorePct, { color: auspicious.color }]}>%</Text>
                </View>
              </View>

              {/* Progress bar */}
              <View style={[s.auspBarBg, { backgroundColor: C.isDark ? "#1e293b" : "#e5e7eb" }]}>
                <View style={[s.auspBarFg, { width: `${auspicious.score}%`, backgroundColor: auspicious.color }]} />
              </View>

              {/* Reasons */}
              {auspicious.good.length > 0 && (
                <View style={{ marginTop: 12 }}>
                  {auspicious.good.map((r, i) => (
                    <Text key={`g-${i}`} style={[s.auspReason, { color: C.text }]}>
                      <Text style={{ color: "#22c55e" }}>✓ </Text>{r}
                    </Text>
                  ))}
                </View>
              )}
              {auspicious.bad.length > 0 && (
                <View style={{ marginTop: 6 }}>
                  {auspicious.bad.map((r, i) => (
                    <Text key={`b-${i}`} style={[s.auspReason, { color: C.text }]}>
                      <Text style={{ color: "#ef4444" }}>⚠ </Text>{r}
                    </Text>
                  ))}
                </View>
              )}
            </View>

            {/* Panchang details */}
            <View style={[s.card, { backgroundColor: C.bgCard, borderColor: C.border }]}>
              <InfoRow label={t.panVaar}      value={panchang.var}      emoji="📆" />
              <InfoRow label={t.panTithi}     value={panchang.tithi}    emoji="🌙" />
              <InfoRow label={t.panNakshatra} value={panchang.nakshatra}emoji="⭐" />
              <InfoRow label={t.panYoga}      value={panchang.yoga}     emoji="🔮" />
              <InfoRow label={t.panKarana}    value={panchang.karana}   emoji="✨" />
            </View>

            {/* Subah muhurt note */}
            <View style={[s.card, { backgroundColor: C.bgCard, borderColor: C.border }]}>
              <Text style={[s.cardTitle, { color: C.textMuted }]}>{t.panBrahmaMuhurta}</Text>
              <Text style={[s.cardVal, { color: C.isDark ? "#f59e0b" : "#92400E" }]}>04:38 AM – 05:26 AM</Text>
              <Text style={[s.cardTip, { color: C.textMuted }]}>{t.panBrahmaTip}</Text>
            </View>
          </>
        )}

        {/* ── RAHU KAAL TAB ── */}
        {tabIdx === 1 && (
          <>
            <View style={[s.rahuHero, { backgroundColor: C.isDark ? "rgba(239,68,68,0.07)" : "#FEE2E2", borderColor: "rgba(239,68,68,0.2)" }]}>
              <Text style={{ fontSize: 36 }}>⛔</Text>
              <View>
                <Text style={[s.rahuTitle, { color: "#ef4444" }]}>{t.panRahuKaalLbl}</Text>
                <Text style={[s.rahuTime, { color: C.text }]}>{kaal.rahu}</Text>
                <Text style={[s.rahuTip, { color: C.textMuted }]}>{t.panRahuTip}</Text>
              </View>
            </View>

            <View style={[s.card, { backgroundColor: C.bgCard, borderColor: C.border }]}>
              <View style={pr.row}>
                <Text style={{ fontSize: 20 }}>⚡</Text>
                <View style={{ flex: 1 }}>
                  <Text style={[pr.rowLabel, { color: C.textMuted }]}>{t.panYamaghanta}</Text>
                  <Text style={[pr.rowVal, { color: C.text }]}>{kaal.yama}</Text>
                  <Text style={[s.rahuTip, { color: C.textDim }]}>{t.panYamaTip}</Text>
                </View>
              </View>
              <View style={[pr.row, { borderBottomWidth: 0 }]}>
                <Text style={{ fontSize: 20 }}>🌑</Text>
                <View style={{ flex: 1 }}>
                  <Text style={[pr.rowLabel, { color: C.textMuted }]}>{t.panGulika}</Text>
                  <Text style={[pr.rowVal, { color: C.text }]}>{kaal.gulika}</Text>
                  <Text style={[s.rahuTip, { color: C.textDim }]}>{t.panGulikaTip}</Text>
                </View>
              </View>
            </View>

            <View style={[s.card, { backgroundColor: C.bgCard, borderColor: C.border, gap: 8 }]}>
              <Text style={[s.cardTitle, { color: C.textMuted }]}>{t.panAbhijitLbl}</Text>
              <Text style={[s.cardVal, { color: "#22c55e" }]}>11:54 AM – 12:46 PM</Text>
              <Text style={[s.cardTip, { color: C.textMuted }]}>{t.panAbhijitTip}</Text>
            </View>
          </>
        )}

        {/* ── FESTIVALS TAB — 10 SAAL KA CALENDAR ─────────────────────── */}
        {tabIdx === 2 && (
          <>
            {/* Year selector — 2026 → 2035 */}
            <ScrollView horizontal showsHorizontalScrollIndicator={false}
                        style={{ flexGrow: 0 }}
                        contentContainerStyle={{ gap: 8, paddingVertical: 4 }}>
              {FESTIVAL_YEARS.map(y => {
                const active = y === festYear;
                return (
                  <Pressable
                    key={y}
                    onPress={() => { Haptics.selectionAsync(); setFestYear(y); }}
                    style={[
                      s.yearChip,
                      { borderColor: C.border },
                      active && { backgroundColor: "#a78bfa", borderColor: "#a78bfa" },
                    ]}
                  >
                    <Text style={[s.yearChipText,
                                  { color: active ? "#fff" : C.textMuted }]}>
                      {y}
                    </Text>
                    {y === today.getFullYear() && (
                      <View style={s.yearChipDot} />
                    )}
                  </Pressable>
                );
              })}
            </ScrollView>

            <Text style={[s.yearLabel, { color: C.textMuted, marginTop: 4 }]}>
              {(FESTIVALS_BY_YEAR[festYear] || []).length} festivals · {festYear}
            </Text>

            {/* Group festivals by month for current year */}
            {(() => {
              const list = FESTIVALS_BY_YEAR[festYear] || [];
              const sorted = [...list].sort((a, b) => a.iso.localeCompare(b.iso));
              const byMonth: Record<string, Festival[]> = {};
              sorted.forEach(f => {
                const m = new Date(f.iso + "T00:00:00")
                  .toLocaleString("en-US", { month: "long" });
                (byMonth[m] = byMonth[m] || []).push(f);
              });
              return Object.entries(byMonth).map(([month, items]) => (
                <View key={month} style={{ marginTop: 6 }}>
                  <Text style={[s.monthHdr, { color: C.isDark ? "#a78bfa" : "#7c3aed" }]}>
                    {month.toUpperCase()}
                  </Text>
                  <View style={[s.card, { backgroundColor: C.bgCard, borderColor: C.border }]}>
                    {items.map((f, i) => {
                      const dleft = daysUntil(f.iso);
                      const isPast = dleft < 0;
                      const isSoon = dleft >= 0 && dleft <= 7;
                      return (
                        <View
                          key={`${f.iso}-${f.name}`}
                          style={[
                            s.festRow,
                            { borderBottomColor: C.border3, opacity: isPast ? 0.5 : 1 },
                            i === items.length - 1 && { borderBottomWidth: 0 },
                          ]}
                        >
                          <Text style={{ fontSize: 22, width: 32 }}>{f.emoji}</Text>
                          <View style={{ flex: 1 }}>
                            <Text style={[s.festName, { color: C.text }]}>
                              {f.name}{f.major && <Text style={{ color: "#fbbf24" }}> ★</Text>}
                            </Text>
                            <Text style={[s.festDate, { color: C.textMuted }]}>
                              {f.date}, {festYear}
                              {isSoon && (
                                <Text style={{ color: "#22c55e", fontFamily: F.bold }}>
                                  {"  · "}{dleft === 0 ? "Aaj!" : `${dleft} din baaki`}
                                </Text>
                              )}
                            </Text>
                          </View>
                          {f.type === "rashtriya" && (
                            <View style={[s.badge, { backgroundColor: C.isDark ? "#3b82f620" : "#DBEAFE", borderColor: C.isDark ? "#3b82f640" : "#93C5FD" }]}>
                              <Text style={[s.badgeText, { color: "#60a5fa" }]}>National</Text>
                            </View>
                          )}
                          {f.type === "vrat" && (
                            <View style={[s.badge, { backgroundColor: C.isDark ? "#a855f720" : "#F3E8FF", borderColor: C.isDark ? "#a855f740" : "#D8B4FE" }]}>
                              <Text style={[s.badgeText, { color: "#a855f7" }]}>Vrat</Text>
                            </View>
                          )}
                          {f.type === "muhurat" && (
                            <View style={[s.badge, { backgroundColor: C.isDark ? "#f59e0b20" : "#FEF3C7", borderColor: C.isDark ? "#f59e0b40" : "#FCD34D" }]}>
                              <Text style={[s.badgeText, { color: "#f59e0b" }]}>Muhurat</Text>
                            </View>
                          )}
                        </View>
                      );
                    })}
                  </View>
                </View>
              ));
            })()}

            <Text style={{ color: C.textMuted, fontSize: 10, textAlign: "center",
                           marginTop: 12, fontFamily: F.regular, lineHeight: 15 }}>
              Dates panchang almanac ke aadhar par hain. Ritual muhurat ke liye
              current-year panchang verify karein.
            </Text>
          </>
        )}
      </ScrollView>
    </View>
  );
}

const pr = StyleSheet.create({
  row: { flexDirection: "row", alignItems: "center", gap: 12, paddingVertical: 12, borderBottomWidth: 1 },
  rowLabel: { fontSize: 10, fontFamily: "Nunito_600SemiBold", letterSpacing: 0.8 },
  rowVal: { fontSize: 15, fontFamily: "Nunito_700Bold", marginTop: 2 },
});

const s = StyleSheet.create({
  topBar: {
    flexDirection: "row", alignItems: "center", justifyContent: "space-between",
    paddingHorizontal: 20, paddingBottom: 14,
  },
  backBtn: { width: 36, height: 36, alignItems: "center", justifyContent: "center" },
  title: { fontSize: 20, fontFamily: F.bold, letterSpacing: -0.3 },
  sub: { fontSize: 11, fontFamily: F.regular, marginTop: 1 },
  tab: { paddingHorizontal: 16, paddingVertical: 7, borderRadius: 20, borderWidth: 1 },
  tabText: { fontSize: 12, fontFamily: F.semibold },

  dateNav: {
    flexDirection: "row", alignItems: "center", gap: 6,
    marginHorizontal: 16, marginBottom: 12,
    borderRadius: 14, borderWidth: 1, paddingHorizontal: 8, paddingVertical: 8,
  },
  dateNavBtn: { width: 36, height: 36, alignItems: "center", justifyContent: "center", borderRadius: 18 },
  dateNavRel: { fontSize: 10, fontFamily: F.bold, letterSpacing: 1.2, textTransform: "uppercase" },
  dateNavDate: { fontSize: 14, fontFamily: F.bold, marginTop: 1 },
  todayPill: { paddingHorizontal: 12, paddingVertical: 6, borderRadius: 14, marginLeft: 4 },
  todayPillText: { color: "#fff", fontSize: 11, fontFamily: F.bold, letterSpacing: 0.5 },
  sunRow: {
    flexDirection: "row", alignItems: "center",
    borderRadius: 16, borderWidth: 1, padding: 16,
  },
  sunItem: { flex: 1, flexDirection: "row", alignItems: "center", gap: 10 },
  sunDivider: { width: 1, height: 36, marginHorizontal: 8 },
  sunLabel: { fontSize: 10, fontFamily: F.medium },
  sunVal: { fontSize: 16, fontFamily: F.bold, marginTop: 1 },
  card: { borderRadius: 16, borderWidth: 1, paddingHorizontal: 16, paddingVertical: 8 },
  cardTitle: { fontSize: 10, fontFamily: F.bold, letterSpacing: 1.5, marginBottom: 4 },
  cardVal: { fontSize: 17, fontFamily: F.bold },
  cardTip: { fontSize: 11, fontFamily: F.regular, marginTop: 4 },
  rahuHero: {
    flexDirection: "row", alignItems: "center", gap: 16,
    borderRadius: 16, borderWidth: 1, padding: 18,
  },
  rahuTitle: { fontSize: 13, fontFamily: F.bold, letterSpacing: 0.5 },
  rahuTime: { fontSize: 22, fontFamily: F.bold, marginTop: 2 },
  rahuTip: { fontSize: 11, fontFamily: F.regular, marginTop: 3 },
  yearLabel: { fontSize: 10, fontFamily: F.bold, letterSpacing: 1.5 },

  // Date hero (Today section top)
  dateHero: {
    borderRadius: 18, borderWidth: 1, padding: 22, alignItems: "center",
  },
  dateHeroDay:   { fontSize: 11, fontFamily: F.bold, letterSpacing: 2.5 },
  dateHeroNum:   { fontSize: 56, fontFamily: F.bold, lineHeight: 62, marginTop: 4 },
  dateHeroMonth: { fontSize: 16, fontFamily: F.semibold, marginTop: 2 },
  dateHeroHindi: { fontSize: 11, fontFamily: F.regular, marginTop: 8 },

  // Auspicious score card
  auspCard: {
    borderRadius: 16, borderWidth: 1.5, padding: 16,
  },
  auspHeader: { flexDirection: "row", alignItems: "center", marginBottom: 12 },
  auspLabel:  { fontSize: 10, fontFamily: F.bold, letterSpacing: 1.5 },
  auspBand:   { fontSize: 18, fontFamily: F.bold, marginTop: 4 },
  auspScoreCircle: {
    width: 64, height: 64, borderRadius: 32, borderWidth: 3,
    alignItems: "center", justifyContent: "center", flexDirection: "row",
  },
  auspScoreNum: { fontSize: 22, fontFamily: F.bold, lineHeight: 24 },
  auspScorePct: { fontSize: 11, fontFamily: F.bold, marginLeft: 1, marginTop: 4 },
  auspBarBg: { height: 8, borderRadius: 4, overflow: "hidden" },
  auspBarFg: { height: "100%", borderRadius: 4 },
  auspReason: { fontSize: 12.5, fontFamily: F.regular, lineHeight: 19, marginTop: 2 },

  // Year selector chips
  yearChip: {
    paddingHorizontal: 14, paddingVertical: 7, borderRadius: 18, borderWidth: 1,
    flexDirection: "row", alignItems: "center", gap: 6,
  },
  yearChipText: { fontSize: 13, fontFamily: F.semibold },
  yearChipDot:  { width: 5, height: 5, borderRadius: 3, backgroundColor: "#22c55e" },
  monthHdr: {
    fontSize: 11, fontFamily: F.bold, letterSpacing: 2,
    paddingHorizontal: 4, paddingVertical: 8,
  },

  festRow: {
    flexDirection: "row", alignItems: "center", gap: 10,
    paddingVertical: 12, borderBottomWidth: 1,
  },
  festName: { fontSize: 14, fontFamily: F.semibold },
  festDate: { fontSize: 11, fontFamily: F.regular, marginTop: 1 },
  badge: { paddingHorizontal: 7, paddingVertical: 3, borderRadius: 8, borderWidth: 1 },
  badgeText: { fontSize: 9, fontFamily: F.bold },
});
