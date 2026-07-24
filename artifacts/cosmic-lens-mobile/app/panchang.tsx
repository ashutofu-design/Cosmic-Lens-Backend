import { Feather } from "@expo/vector-icons";
import { router } from "expo-router";
import * as Haptics from "expo-haptics";
import React, { useEffect, useMemo, useRef, useState } from "react";
import {
  ActivityIndicator,
  I18nManager,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
  type TextStyle,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { CosmicBg } from "@/components/CosmicBg";
import { FadeInView, staggerDelay } from "@/components/motion/FadeInView";
import { NaamJaapTimer } from "@/components/NaamJaapTimer";
import { useC } from "@/context/ThemeContext";
import { useT } from "@/hooks/useT";
import { uiDateLocale } from "@/lib/i18n";
import { useUser } from "@/context/UserContext";
import {
  fetchDailyMuhurat,
  fetchEkadashiSchedule,
  fetchPanchangVivahDates,
  fetchRealPanchang,
  fetchTarabalaChandrabala,
  type DailyMuhurat,
  type EkadashiSchedule,
  type RealPanchang,
  type TarabalaStrength,
  type VivahMuhuratDay,
} from "@/lib/panchangAPI";
import { FESTIVALS_BY_YEAR, type Festival } from "@/data/festivals10y";
import { useScreenLayout, type ScreenLayout } from "@/lib/screenLayout";

const NAK_NORMALIZE: Record<string, string> = {
  "P.Phalguni": "Purva Phalguni", "U.Phalguni": "Uttara Phalguni",
  "P.Ashadha": "Purva Ashadha",  "U.Ashadha": "Uttara Ashadha",
  "P.Bhadrapada": "Purva Bhadrapada", "U.Bhadrapada": "Uttara Bhadrapada",
  "Dhanishta": "Dhanishtha",
};
function normalizeNak(n: string): string { return NAK_NORMALIZE[n] || n; }

const VAAR_MAP: Record<string, string> = {
  Monday: "Somvar", Tuesday: "Mangalvar", Wednesday: "Budhavar",
  Thursday: "Guruvaar", Friday: "Shukravar", Saturday: "Shanivaar", Sunday: "Ravivaar",
};

const F = {
  bold: "Nunito_700Bold", semibold: "Nunito_600SemiBold",
  medium: "Nunito_500Medium", regular: "Nunito_400Regular",
};

const TAB_IDS = ["Aaj", "Muhurat", "Vrat", "Vivah", "Jaap"] as const;
type TabId = (typeof TAB_IDS)[number];

type AuspiciousBandKey = "excellent" | "good" | "mixed" | "caution";

function getPanchang(date: Date) {
  const TITHIS = ["Pratipada","Dwitiya","Tritiya","Chaturthi","Panchami","Shashthi","Saptami","Ashtami","Navami","Dashami","Ekadashi","Dwadashi","Trayodashi","Chaturdashi","Purnima/Amavasya"];
  const NAKSHATRAS = ["Ashwini","Bharani","Krittika","Rohini","Mrigashira","Ardra","Punarvasu","Pushya","Ashlesha","Magha","Purva Phalguni","Uttara Phalguni","Hasta","Chitra","Swati","Vishakha","Anuradha","Jyeshtha","Mula","Purva Ashadha","Uttara Ashadha","Shravana","Dhanishtha","Shatabhisha","Purva Bhadrapada","Uttara Bhadrapada","Revati"];
  const YOGAS = ["Vishkambha","Priti","Ayushman","Saubhagya","Shobhana","Atiganda","Sukarma","Dhriti","Shula","Ganda","Vriddhi","Dhruva","Vyaghata","Harshana","Vajra","Siddhi","Vyatipata","Variyana","Parigha","Shiva","Siddha","Sadhya","Shubha","Shukla","Brahma","Indra","Vaidhriti"];
  const KARANAS = ["Bava","Balava","Kaulava","Taitila","Gara","Vanija","Vishti","Shakuni","Chatushpada","Naga","Kimstughna"];
  const PAKSHA = ["Shukla","Krishna"];
  const DAYS = ["Ravivaar","Somvar","Mangalvar","Budhavar","Guruvaar","Shukravar","Shanivaar"];
  const doy = Math.floor((date.getTime() - new Date(date.getFullYear(), 0, 0).getTime()) / 86400000);
  const lunar = Math.floor(((doy * 12.37) % 30));
  const tithi = TITHIS[lunar % 15];
  const paksha = lunar < 15 ? PAKSHA[0] : PAKSHA[1];
  return {
    tithi: `${paksha} ${tithi}`,
    nakshatra: NAKSHATRAS[doy % 27],
    yoga: YOGAS[doy % 27],
    karana: KARANAS[doy % 11],
    var: DAYS[date.getDay()],
  };
}

function festivalOn(iso: string): Festival | undefined {
  const list = FESTIVALS_BY_YEAR[parseInt(iso.slice(0, 4), 10)] || [];
  return list.find((f) => f.iso === iso);
}

function getAuspiciousScore(p: { tithi: string; nakshatra: string; yoga: string; karana: string; var: string; iso?: string }) {
  let score = 45;
  const tCore = p.tithi.split(" ").slice(-1)[0].replace("/Amavasya", "");
  if (["Panchami","Saptami","Dashami","Ekadashi","Trayodashi"].includes(tCore)) score += 10;
  else if (["Chaturthi","Navami","Chaturdashi","Amavasya"].includes(tCore)) score -= 14;
  if (["Pushya","Rohini","Hasta","Anuradha","Shravana","Revati"].includes(p.nakshatra)) score += 12;
  else if (["Bharani","Krittika","Ashlesha","Magha","Mula","Jyeshtha","Vishakha","Ardra"].includes(p.nakshatra)) score -= 14;
  const fest = p.iso ? festivalOn(p.iso) : undefined;
  if (fest?.major) score += 25;
  score = Math.max(8, Math.min(98, score));
  let bandKey: AuspiciousBandKey, color: string, emoji: string;
  if (score >= 80) { bandKey = "excellent"; color = "#22c55e"; emoji = "🌟"; }
  else if (score >= 65) { bandKey = "good"; color = "#84cc16"; emoji = "✨"; }
  else if (score >= 35) { bandKey = "mixed"; color = "#f59e0b"; emoji = "⚖️"; }
  else { bandKey = "caution"; color = "#ef4444"; emoji = "⚠️"; }
  return { score, bandKey, color, emoji, festival: fest };
}

function formatToday(iso: string, locale: string) {
  return new Date(iso + "T12:00:00").toLocaleDateString(locale, {
    weekday: "long", day: "numeric", month: "long", year: "numeric",
  });
}

function InfoRow({
  label, value, emoji, border, rowValStyle,
}: {
  label: string; value: string; emoji: string; border: string; rowValStyle?: TextStyle;
}) {
  const C = useC();
  const { rs } = useScreenLayout();
  return (
    <View style={[pr.row, { borderBottomColor: border, paddingVertical: rs(10) }]}>
      <Text style={{ fontSize: rs(18) }}>{emoji}</Text>
      <View style={{ flex: 1, minWidth: 0 }}>
        <Text style={[pr.rowLabel, { color: C.textMuted, fontSize: rs(10) }]}>{label}</Text>
        <Text style={[pr.rowVal, { color: C.text, fontSize: rs(15), flexShrink: 1 }, rowValStyle]} numberOfLines={2}>
          {value}
        </Text>
      </View>
    </View>
  );
}

function MuhuratLine({ label, period, danger }: { label: string; period: { start: string; end: string }; danger?: boolean }) {
  const C = useC();
  const { rs } = useScreenLayout();
  return (
    <View style={[pr.row, { borderBottomColor: C.border3, paddingVertical: rs(10) }]}>
      <Text style={{ fontSize: rs(16) }}>{danger ? "⛔" : "🕐"}</Text>
      <View style={{ flex: 1, minWidth: 0 }}>
        <Text style={[pr.rowLabel, { color: C.textMuted, fontSize: rs(10) }]}>{label}</Text>
        <Text
          style={[pr.rowVal, { color: danger ? "#ef4444" : C.text, fontSize: rs(14), flexShrink: 1 }]}
          numberOfLines={2}
        >
          {period.start} – {period.end}
        </Text>
      </View>
    </View>
  );
}

export default function PanchangScreen() {
  const C = useC();
  const t = useT();
  const insets = useSafeAreaInsets();
  const L = useScreenLayout();
  const sty = useMemo(() => makeStyles(L), [L.width, L.height, L.compact, L.narrow]);
  const [tab, setTab] = useState<TabId>("Aaj");
  const dateLocale = useMemo(() => uiDateLocale(t.lang), [t.lang]);
  const tabs = useMemo(
    () => [
      { id: "Aaj" as TabId, label: t.pn_tabToday },
      { id: "Muhurat" as TabId, label: t.pn_tabMuhurat },
      { id: "Vrat" as TabId, label: t.pn_tabVrat },
      { id: "Vivah" as TabId, label: t.pn_tabVivah },
      { id: "Jaap" as TabId, label: t.pn_tabJaap },
    ],
    [t],
  );
  const bandLabels = useMemo(
    () => ({
      excellent: t.pn_bandExcellent,
      good: t.pn_bandGood,
      mixed: t.pn_bandMixed,
      caution: t.pn_bandCaution,
    }),
    [t],
  );
  const { primaryProfile, profiles } = useUser() as {
    primaryProfile?: { id?: string; birthData?: { lat?: number; lon?: number; tz?: number }; kundli?: { moonSign?: string; nakshatra?: string } };
    profiles?: { id?: string; kundli?: { moonSign?: string; nakshatra?: string } }[];
  };
  const bd = primaryProfile?.birthData ?? null;
  const kundli = primaryProfile?.kundli ?? null;
  const userLat = bd?.lat ?? 28.6139;
  const userLng = bd?.lon ?? 77.2090;
  const userTz = bd?.tz ?? 5.5;
  const natalMoon = kundli?.moonSign as string | undefined;
  const natalNak = kundli?.nakshatra as string | undefined;
  const partnerProfile = useMemo(
    () => (profiles ?? []).find((p) => p.id !== primaryProfile?.id && p.kundli?.nakshatra),
    [profiles, primaryProfile?.id],
  );
  const coupleNaks = useMemo(() => {
    const brideNak = natalNak;
    const groomNak = partnerProfile?.kundli?.nakshatra as string | undefined;
    return { brideNak, groomNak, brideMoon: natalMoon, groomMoon: partnerProfile?.kundli?.moonSign as string | undefined };
  }, [natalNak, natalMoon, partnerProfile]);

  const today = useMemo(() => { const d = new Date(); d.setHours(0, 0, 0, 0); return d; }, []);
  const todayIso = useMemo(() => {
    const y = today.getFullYear();
    return `${y}-${String(today.getMonth() + 1).padStart(2, "0")}-${String(today.getDate()).padStart(2, "0")}`;
  }, [today]);

  const [real, setReal] = useState<RealPanchang | null>(null);
  const [muhurat, setMuhurat] = useState<DailyMuhurat | null>(null);
  const [strength, setStrength] = useState<TarabalaStrength | null>(null);
  const [ekadashi, setEkadashi] = useState<EkadashiSchedule | null>(null);
  const [ekadashiLoading, setEkadashiLoading] = useState(false);
  const defaultMonthKey = useMemo(
    () => `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, "0")}`,
    [today],
  );
  const [selectedMonthKey, setSelectedMonthKey] = useState(defaultMonthKey);
  const [vivah, setVivah] = useState<VivahMuhuratDay[]>([]);
  const [vivahLoading, setVivahLoading] = useState(false);
  const [vivahProgress, setVivahProgress] = useState({ y: 0, t: 5 });
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);
  const seq = useRef(0);

  useEffect(() => {
    const id = ++seq.current;
    const ctrl = new AbortController();
    setLoading(true);
    setErr(null);
    const base = { lat: userLat, lng: userLng, tz: userTz, signal: ctrl.signal };

    const tasks: Promise<void>[] = [
      fetchRealPanchang({ date: today, ...base }).then((d) => {
        if (id !== seq.current) return;
        setReal(d);
        if (d.muhurat_detail) setMuhurat(d.muhurat_detail);
      }),
      fetchDailyMuhurat({ date: today, ...base })
        .then((d) => { if (id === seq.current) setMuhurat(d); })
        .catch(() => { /* fallback: muhurat_detail from /api/panchang */ }),
      (async () => {
        setEkadashiLoading(true);
        try {
          const r = await fetchEkadashiSchedule({
            fromDate: today,
            years: 5,
            lat: userLat,
            lng: userLng,
            tz: userTz,
            signal: ctrl.signal,
          });
          if (id === seq.current) {
            setEkadashi(r);
            setSelectedMonthKey(defaultMonthKey);
            setEkadashiLoading(false);
          }
        } catch {
          if (id === seq.current) setEkadashiLoading(false);
        }
      })(),
      (async () => {
        setVivahLoading(true);
        try {
          const r = await fetchPanchangVivahDates({
            fromDate: today,
            years: 5,
            lat: userLat,
            lng: userLng,
            tz: userTz,
            brideNak: coupleNaks.brideNak,
            groomNak: coupleNaks.groomNak,
            brideMoonRashi: coupleNaks.brideMoon,
            groomMoonRashi: coupleNaks.groomMoon,
            signal: ctrl.signal,
            onProgress: (y, t) => {
              if (id === seq.current) setVivahProgress({ y, t });
            },
          });
          if (id === seq.current) {
            setVivah(r.dates);
            setVivahLoading(false);
          }
        } catch {
          if (id === seq.current) {
            setVivah([]);
            setVivahLoading(false);
          }
        }
      })(),
    ];

    if (natalMoon && natalNak) {
      tasks.push(
        fetchTarabalaChandrabala({
          natalMoonSign: natalMoon,
          natalNakshatra: natalNak,
          date: today,
          tz: userTz,
          signal: ctrl.signal,
        }).then((d) => { if (id === seq.current) setStrength(d); }),
      );
    }

    Promise.allSettled(tasks).then((results) => {
      if (id !== seq.current) return;
      const failed = results.filter((r) => r.status === "rejected");
      if (failed.length === results.length) {
        setErr(t.pn_loadFail);
      }
      setLoading(false);
    });

    return () => ctrl.abort();
  }, [today, todayIso, userLat, userLng, userTz, natalMoon, natalNak, defaultMonthKey, coupleNaks, t.pn_loadFail]);

  const localPanchang = useMemo(() => getPanchang(today), [today]);
  const panchang = useMemo(() => {
    if (!real) return localPanchang;
    return {
      tithi: real.tithi || localPanchang.tithi,
      nakshatra: normalizeNak(real.nakshatra || localPanchang.nakshatra),
      yoga: real.yoga || localPanchang.yoga,
      karana: (real.karana || localPanchang.karana).replace(" (Bhadra)", ""),
      var: (real.vaar && VAAR_MAP[real.vaar]) || localPanchang.var,
    };
  }, [real, localPanchang]);

  const auspicious = useMemo(() => getAuspiciousScore({ ...panchang, iso: todayIso }), [panchang, todayIso]);
  const todayEkadashi = useMemo(() => {
    if (!ekadashi) return [];
    for (const m of ekadashi.months) {
      const hit = m.dates.find((d) => d.date === todayIso);
      if (hit) return [hit];
    }
    return [];
  }, [ekadashi, todayIso]);

  const selectedEkadashiMonth = useMemo(
    () => ekadashi?.months.find((m) => m.month_key === selectedMonthKey) ?? null,
    [ekadashi, selectedMonthKey],
  );

  const vivahByMonth = useMemo(() => {
    const byMonth: Record<string, VivahMuhuratDay[]> = {};
    for (const item of vivah) {
      const m = new Date(item.date + "T12:00:00").toLocaleString(dateLocale, { month: "long", year: "numeric" });
      (byMonth[m] = byMonth[m] || []).push(item);
    }
    return Object.entries(byMonth);
  }, [vivah, dateLocale]);

  const dateStr = formatToday(todayIso, dateLocale);
  const auspiciousBand = bandLabels[auspicious.bandKey];
  const selectedMonthTitle = useMemo(() => {
    if (!selectedEkadashiMonth) return "";
    return new Date(selectedEkadashiMonth.year, selectedEkadashiMonth.month - 1, 1)
      .toLocaleDateString(dateLocale, { month: "long", year: "numeric" })
      .toUpperCase();
  }, [selectedEkadashiMonth, dateLocale]);

  return (
    <CosmicBg>
      <View style={[sty.topBar, { paddingTop: insets.top + L.rs(8) }]}>
        <Pressable onPress={() => router.back()} style={sty.backBtn}>
          <Feather name={I18nManager.isRTL ? "arrow-right" : "arrow-left"} size={L.rs(20)} color={C.text} />
        </Pressable>
        <View style={{ flex: 1, minWidth: 0 }}>
          <Text style={[sty.title, { color: C.text }]} numberOfLines={1}>{t.panchangTitle}</Text>
          <Text style={[sty.sub, { color: C.textMuted }]} numberOfLines={1} adjustsFontSizeToFit minimumFontScale={0.85}>
            {dateStr}
          </Text>
        </View>
        <View style={{ width: L.rs(36) }} />
      </View>

      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        style={{ flexGrow: 0, maxHeight: L.tabRowH + L.rs(8) }}
        contentContainerStyle={{ paddingHorizontal: L.ph, gap: L.rs(6), paddingBottom: L.rs(6) }}
      >
        {tabs.map((tb) => (
          <Pressable
            key={tb.id}
            onPress={() => { Haptics.selectionAsync(); setTab(tb.id); }}
            style={[sty.tab, { borderColor: C.border }, tab === tb.id && { backgroundColor: "#a78bfa", borderColor: "#a78bfa" }]}
          >
            <Text
              style={[sty.tabText, { color: tab === tb.id ? "#fff" : C.textMuted }]}
              numberOfLines={1}
              adjustsFontSizeToFit={L.compact}
              minimumFontScale={0.8}
            >
              {tb.label}
            </Text>
          </Pressable>
        ))}
      </ScrollView>

      <View style={{ flex: 1, minHeight: 0 }}>
      {loading && tab === "Aaj" ? (
        <View style={[sty.centerLoad, { flex: 1 }]}>
          <ActivityIndicator color="#a78bfa" size="large" />
          <Text style={[sty.loadingTxt, { color: C.textMuted }]}>{t.pn_loadPanchang}</Text>
        </View>
      ) : (
        <ScrollView
          style={{ flex: 1 }}
          showsVerticalScrollIndicator={false}
          keyboardShouldPersistTaps="handled"
          contentContainerStyle={{
            paddingHorizontal: L.ph,
            paddingBottom: L.padBottom,
            gap: L.gap,
            flexGrow: 1,
            ...(tab === "Jaap" ? { justifyContent: "flex-start" as const } : null),
          }}
        >
          {err && tab === "Aaj" ? (
            <Text style={[sty.hint, { color: "#f59e0b", textAlign: "center" }]}>{err}</Text>
          ) : null}

          {/* ── AAJ ── */}
          {tab === "Aaj" && (
            <>
              <FadeInView delay={staggerDelay(0)} resetKey={tab}>
              <View style={[sty.auspCard, { backgroundColor: C.bgCard, borderColor: auspicious.color + "55" }]}>
                <Text style={[sty.sectionLbl, { color: C.textMuted }]}>{t.pn_auspicious}</Text>
                <View style={sty.auspHeader}>
                  <Text style={[sty.auspBand, { color: auspicious.color, flex: 1, flexShrink: 1 }]} numberOfLines={2}>
                    {auspicious.emoji} {auspiciousBand}
                  </Text>
                  <View style={[sty.auspScoreCircle, { borderColor: auspicious.color }]}>
                    <Text style={[sty.auspScoreNum, { color: auspicious.color }]}>{auspicious.score}</Text>
                    <Text style={[sty.auspScorePct, { color: auspicious.color }]}>%</Text>
                  </View>
                </View>
                <View style={[sty.auspBarBg, { backgroundColor: C.isDark ? "#1e293b" : "#e5e7eb" }]}>
                  <View style={[sty.auspBarFg, { width: `${auspicious.score}%`, backgroundColor: auspicious.color }]} />
                </View>
              </View>
              </FadeInView>

              {strength && (
                <FadeInView delay={staggerDelay(1)} resetKey={tab}>
                <View style={[sty.card, { backgroundColor: C.bgCard, borderColor: C.border, paddingVertical: L.rs(12) }]}>
                  <Text style={[sty.sectionLbl, { color: C.textMuted, marginBottom: L.rs(8) }]}>{t.pn_tarabalaHdr}</Text>
                  <Text style={[sty.vivahDate, { color: strength.overall_ok ? "#22c55e" : "#f59e0b" }]}>
                    {strength.strength_band} · {strength.strength_score}%
                  </Text>
                  <Text style={[sty.vivahMeta, { color: C.textMuted, marginTop: 4 }]} numberOfLines={3}>
                    Tarabala: {strength.tarabala.tara_name} {strength.tarabala.ok ? "✓" : "✗"}
                    {"  ·  "}Chandra: {strength.transit_moon_sign}
                  </Text>
                </View>
                </FadeInView>
              )}
              {!natalMoon && !natalNak && (
                <FadeInView delay={staggerDelay(1)} resetKey={tab}>
                <Text style={[sty.hint, { color: C.textMuted }]}>{t.pn_tarabalaHint}</Text>
                </FadeInView>
              )}

              <FadeInView delay={staggerDelay(2)} resetKey={tab}>
              <View style={[sty.card, { backgroundColor: C.bgCard, borderColor: C.border }]}>
                <InfoRow label={t.panTithi} value={panchang.tithi} emoji="🌙" border={C.border3} />
                <InfoRow label={t.panNakshatra} value={panchang.nakshatra} emoji="⭐" border={C.border3} />
                <InfoRow label={t.panYoga} value={panchang.yoga} emoji="🔮" border={C.border3} />
                <InfoRow label={t.panKarana} value={panchang.karana} emoji="✨" border={C.border3} />
                <InfoRow label={t.panVaar} value={panchang.var} emoji="📆" border={C.border3} />
                <View style={[pr.row, { borderBottomWidth: 0 }]}>
                  <Text style={{ fontSize: 20 }}>🌅</Text>
                  <View style={{ flex: 1 }}>
                    <Text style={[pr.rowLabel, { color: C.textMuted }]}>{t.panSunrise} / {t.panSunset}</Text>
                    <Text style={[pr.rowVal, { color: C.text }]}>
                      {(muhurat || real)
                        ? `${muhurat?.sunrise || real?.sunrise} – ${muhurat?.sunset || real?.sunset}`
                        : "—"}
                    </Text>
                  </View>
                </View>
              </View>
              </FadeInView>

              {todayEkadashi.length > 0 && (
                <FadeInView delay={staggerDelay(3)} resetKey={tab}>
                <View style={[sty.card, { backgroundColor: C.bgCard, borderColor: "#a78bfa55", padding: L.rs(14) }]}>
                  <Text style={[sty.sectionLbl, { color: "#a78bfa", marginBottom: 8 }]}>{t.pn_ekadashiTodayHdr}</Text>
                  {todayEkadashi.map((f) => (
                    <Text key={f.date} style={[sty.vivahDate, { color: C.text }]}>
                      🪔 {f.festival_name} · {f.paksha} {t.pn_pakshaWord}
                    </Text>
                  ))}
                </View>
                </FadeInView>
              )}
            </>
          )}

          {/* ── MUHURAT ── */}
          {tab === "Muhurat" && (
            <FadeInView delay={staggerDelay(0)} resetKey={tab}>
            <View style={[sty.card, { backgroundColor: C.bgCard, borderColor: C.border }]}>
              {muhurat ? (
                <>
                  <MuhuratLine label={t.pn_brahmaMuhurta} period={muhurat.brahma_muhurta} />
                  <MuhuratLine label={t.rahukaal} period={muhurat.rahu_kaal} danger />
                  <MuhuratLine label={t.pn_gulika} period={muhurat.gulika_kaal} danger />
                  <MuhuratLine label={t.panYamaghanta || "Yamaganda"} period={muhurat.yamaghanta} danger />
                  <View style={[pr.row, { borderBottomWidth: 0 }]}>
                    <Text style={{ fontSize: 18 }}>✨</Text>
                    <View style={{ flex: 1 }}>
                      <Text style={[pr.rowLabel, { color: C.textMuted }]}>{t.pn_abhijit}</Text>
                      <Text style={[pr.rowVal, { color: "#22c55e" }]}>
                        {muhurat.abhijit_muhurat.start} – {muhurat.abhijit_muhurat.end}
                      </Text>
                    </View>
                  </View>
                </>
              ) : (
                <Text style={[sty.hint, { color: C.textMuted, padding: 16 }]}>{t.pn_muhuratFail}</Text>
              )}
              <Text style={[sty.hint, { color: C.textMuted, padding: 12 }]}>
                {t.pn_muhuratLoc} ({userLat.toFixed(1)}°, {userLng.toFixed(1)}°)
              </Text>
            </View>
            </FadeInView>
          )}

          {/* ── VRAT ── */}
          {tab === "Vrat" && (
            <FadeInView delay={staggerDelay(0)} resetKey={tab} style={{ gap: L.gap }}>
            <>
              <Text style={[sty.countLine, { color: C.textMuted }]}>
                {t.pn_ekadashiCount.replace("{n}", String(ekadashi?.total ?? "—"))}
              </Text>
              <Text style={[sty.hint, { color: C.textMuted, lineHeight: 14 }]}>{t.pn_ekadashiNote}</Text>

              {ekadashiLoading ? (
                <View style={sty.centerLoad}>
                  <ActivityIndicator color="#a78bfa" />
                  <Text style={[sty.loadingTxt, { color: C.textMuted }]}>{t.pn_loadEkadashi}</Text>
                </View>
              ) : (
                <>
                  <ScrollView
                    horizontal
                    showsHorizontalScrollIndicator={false}
                    style={{ flexGrow: 0 }}
                    contentContainerStyle={{ gap: 8, paddingVertical: 4 }}
                  >
                    {ekadashi?.months.map((m) => {
                      const active = m.month_key === selectedMonthKey;
                      const isCurrent = m.month_key === defaultMonthKey;
                      return (
                        <Pressable
                          key={m.month_key}
                          onPress={() => {
                            Haptics.selectionAsync();
                            setSelectedMonthKey(m.month_key);
                          }}
                          style={[
                            sty.monthChip,
                            { borderColor: C.border },
                            active && { backgroundColor: "#a78bfa", borderColor: "#a78bfa" },
                          ]}
                        >
                          <Text style={[sty.monthChipText, { color: active ? "#fff" : C.textMuted }]}>
                            {new Date(m.year, m.month - 1, 1).toLocaleString(dateLocale, { month: "short", year: "2-digit" })}
                          </Text>
                          {isCurrent && <View style={sty.monthChipDot} />}
                        </Pressable>
                      );
                    })}
                  </ScrollView>

                  <Text style={[sty.monthHdr, { color: C.isDark ? "#a78bfa" : "#7c3aed" }]}>
                    {selectedMonthTitle}
                    {selectedMonthKey === defaultMonthKey ? ` · ${t.pn_currentMonth}` : ""}
                  </Text>

                  {!selectedEkadashiMonth?.dates.length ? (
                    <View style={[sty.card, { backgroundColor: C.bgCard, borderColor: C.border }]}>
                      <Text style={[sty.emptyTitle, { color: C.text }]}>{t.pn_noEkadashiMonth}</Text>
                    </View>
                  ) : (
                    <View style={[sty.card, { backgroundColor: C.bgCard, borderColor: C.border }]}>
                      {selectedEkadashiMonth.dates.map((f, i) => {
                        const isToday = f.date === todayIso;
                        const isLast = i === selectedEkadashiMonth.dates.length - 1;
                        return (
                          <View
                            key={f.date}
                            style={[
                              sty.vivahRow,
                              { borderBottomColor: C.border3, opacity: f.date < todayIso ? 0.55 : 1 },
                              isLast && { borderBottomWidth: 0 },
                            ]}
                          >
                            <View style={{ flex: 1, minWidth: 0 }}>
                              <Text style={[sty.vivahDate, { color: C.text }]} numberOfLines={2}>
                                {f.display} · {f.weekday}
                                {isToday ? `  ·  ${t.pn_tagToday}` : ""}
                              </Text>
                              <Text style={[sty.vivahMeta, { color: C.textMuted }]} numberOfLines={2}>
                                {f.festival_name} · {f.paksha} {t.pn_pakshaWord}
                              </Text>
                            </View>
                          </View>
                        );
                      })}
                    </View>
                  )}
                </>
              )}
            </>
            </FadeInView>
          )}

          {/* ── NAAM JAAP ── */}
          {tab === "Jaap" && (
            <FadeInView delay={staggerDelay(0)} resetKey={tab}>
              <NaamJaapTimer />
            </FadeInView>
          )}

          {/* ── VIVAH ── */}
          {tab === "Vivah" && (
            <FadeInView delay={staggerDelay(0)} resetKey={tab} style={{ gap: L.gap }}>
            <>
              {vivahLoading ? (
                <View style={sty.centerLoad}>
                  <ActivityIndicator color="#a78bfa" />
                  <Text style={[sty.loadingTxt, { color: C.textMuted }]}>
                    {t.pn_vivahLoading.replace("{y}", String(vivahProgress.y)).replace("{t}", String(vivahProgress.t))}
                  </Text>
                </View>
              ) : vivah.length === 0 ? (
                <View style={[sty.card, { backgroundColor: C.bgCard, borderColor: C.border }]}>
                  <Text style={[sty.emptyTitle, { color: C.text }]}>{t.pn_vivahEmpty}</Text>
                </View>
              ) : (
                <>
                <Text style={[sty.vivahCountHdr, { color: C.textMuted }]}>
                  {t.pn_vivahCount.replace("{n}", String(vivah.length))}
                </Text>
                {vivahByMonth.map(([month, items]) => (
                  <View key={month}>
                    <Text style={[sty.monthHdr, { color: C.isDark ? "#a78bfa" : "#7c3aed" }]}>
                      {month.toUpperCase()}
                    </Text>
                    <View style={[sty.card, { backgroundColor: C.bgCard, borderColor: C.border }]}>
                      {items.map((item, i) => {
                        const win = item.best_windows?.[0];
                        const isLast = i === items.length - 1;
                        return (
                          <View
                            key={item.date}
                            style={[
                              sty.vivahRow,
                              { borderBottomColor: C.border3, opacity: item.date < todayIso ? 0.55 : 1 },
                              isLast && { borderBottomWidth: 0 },
                            ]}
                          >
                            <View style={{ flex: 1, minWidth: 0 }}>
                              <Text style={[sty.vivahDate, { color: C.text }]} numberOfLines={2}>
                                {item.display || item.date} · {item.weekday || ""}
                                {item.tier === "highly_favorable" ? "  ★" : ""}
                              </Text>
                              <Text style={[sty.vivahMeta, { color: C.textMuted }]} numberOfLines={2}>
                                {item.tithi}{item.nakshatra ? ` · ${item.nakshatra}` : ""}
                                {item.confidence != null ? ` · ${item.confidence}% ${t.pn_vivahConf}` : ""}
                              </Text>
                              {win ? (
                                <Text style={[sty.vivahMeta, { color: "#22c55e", marginTop: 2 }]} numberOfLines={3}>
                                  {t.pn_vivahWindow}: {win.start} – {win.end}
                                  {win.lagna ? ` · ${win.lagna}` : ""}
                                </Text>
                              ) : null}
                            </View>
                          </View>
                        );
                      })}
                    </View>
                  </View>
                ))}
                </>
              )}
            </>
            </FadeInView>
          )}
        </ScrollView>
      )}
      </View>
    </CosmicBg>
  );
}

const pr = StyleSheet.create({
  row: { flexDirection: "row", alignItems: "center", gap: 12, borderBottomWidth: 1 },
  rowLabel: { fontFamily: "Nunito_600SemiBold", letterSpacing: 0.8 },
  rowVal: { fontFamily: "Nunito_700Bold", marginTop: 2 },
});

function makeStyles(L: ScreenLayout) {
  const { rs, ph, compact } = L;
  return StyleSheet.create({
    topBar: {
      flexDirection: "row", alignItems: "center", justifyContent: "space-between",
      paddingHorizontal: ph, paddingBottom: rs(8), gap: rs(8),
    },
    backBtn: { width: rs(36), height: rs(36), alignItems: "center", justifyContent: "center" },
    title: { fontSize: rs(compact ? 18 : 20), fontFamily: F.bold },
    sub: { fontSize: rs(compact ? 10 : 11), fontFamily: F.regular, marginTop: 2 },
    tab: { paddingHorizontal: rs(compact ? 10 : 14), paddingVertical: rs(6), borderRadius: rs(18), borderWidth: 1 },
    tabText: { fontSize: rs(compact ? 11 : 12), fontFamily: F.semibold },
    sectionLbl: { fontSize: rs(10), fontFamily: F.bold, letterSpacing: 1.2 },
    auspCard: { borderRadius: rs(14), borderWidth: 1.5, padding: rs(14), gap: rs(8) },
    auspHeader: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", gap: rs(8) },
    auspBand: { fontSize: rs(compact ? 18 : 22), fontFamily: F.bold },
    auspScoreCircle: {
      width: rs(compact ? 54 : 64), height: rs(compact ? 54 : 64), borderRadius: rs(compact ? 27 : 32),
      borderWidth: 3, alignItems: "center", justifyContent: "center", flexDirection: "row", flexShrink: 0,
    },
    auspScoreNum: { fontSize: rs(compact ? 18 : 22), fontFamily: F.bold },
    auspScorePct: { fontSize: rs(10), fontFamily: F.bold, marginTop: 4 },
    auspBarBg: { height: rs(8), borderRadius: rs(4), overflow: "hidden" },
    auspBarFg: { height: "100%", borderRadius: rs(4) },
    card: { borderRadius: rs(14), borderWidth: 1, overflow: "hidden" },
    hint: { fontSize: rs(10), fontFamily: F.semibold },
    countLine: { fontSize: rs(11), fontFamily: F.medium },
    monthHdr: { fontSize: rs(11), fontFamily: F.bold, letterSpacing: 1.2, paddingVertical: rs(6) },
    vivahCountHdr: { fontSize: rs(11), fontFamily: F.medium, paddingBottom: rs(4), paddingHorizontal: rs(2) },
    vivahRow: {
      flexDirection: "row", alignItems: "flex-start", gap: rs(8),
      paddingVertical: rs(10), paddingHorizontal: rs(12), borderBottomWidth: 1,
    },
    vivahDate: { fontSize: rs(compact ? 13 : 14), fontFamily: F.bold, flexShrink: 1 },
    vivahMeta: { fontSize: rs(compact ? 10 : 11), fontFamily: F.regular, marginTop: 2, flexShrink: 1 },
    emptyTitle: { fontSize: rs(14), fontFamily: F.semibold, padding: rs(14) },
    centerLoad: { alignItems: "center", justifyContent: "center", gap: rs(10), paddingVertical: rs(24) },
    loadingTxt: { fontSize: rs(13), fontFamily: F.medium, textAlign: "center", paddingHorizontal: ph },
    monthChip: {
      paddingHorizontal: rs(compact ? 10 : 12), paddingVertical: rs(7), borderRadius: rs(14), borderWidth: 1,
      flexDirection: "row", alignItems: "center", gap: rs(5),
    },
    monthChipText: { fontSize: rs(compact ? 11 : 12), fontFamily: F.semibold },
    monthChipDot: { width: rs(5), height: rs(5), borderRadius: rs(3), backgroundColor: "#22c55e" },
  });
}
