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
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { CosmicBg } from "@/components/CosmicBg";
import { useC } from "@/context/ThemeContext";
import { useT } from "@/hooks/useT";
import { useUser } from "@/context/UserContext";
import {
  fetchDailyMuhurat,
  fetchEkadashiSchedule,
  fetchGochar,
  fetchMarriageDates,
  fetchRealPanchang,
  fetchTarabalaChandrabala,
  type DailyMuhurat,
  type EkadashiSchedule,
  type GocharResponse,
  type MarriageDatesScan,
  type RealPanchang,
  type TarabalaStrength,
} from "@/lib/panchangAPI";
import { FESTIVALS_BY_YEAR, type Festival } from "@/data/festivals10y";

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

const TABS = ["Aaj", "Muhurat", "Gochar", "Vrat", "Vivah"] as const;
type TabId = (typeof TABS)[number];

const GOCHAR_ORDER = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu"];
const GOCHAR_HI: Record<string, string> = {
  sun: "Surya", moon: "Chandra", mars: "Mangal", mercury: "Budh",
  jupiter: "Guru", venus: "Shukra", saturn: "Shani", rahu: "Rahu", ketu: "Ketu",
};

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
  let band: string, color: string, emoji: string;
  if (score >= 80) { band = "Bahut Shubh"; color = "#22c55e"; emoji = "🌟"; }
  else if (score >= 65) { band = "Shubh"; color = "#84cc16"; emoji = "✨"; }
  else if (score >= 35) { band = "Mishrit"; color = "#f59e0b"; emoji = "⚖️"; }
  else { band = "Asubh"; color = "#ef4444"; emoji = "⚠️"; }
  return { score, band, color, emoji, festival: fest };
}

function formatToday(iso: string) {
  return new Date(iso + "T12:00:00").toLocaleDateString("hi-IN", {
    weekday: "long", day: "numeric", month: "long", year: "numeric",
  });
}

function InfoRow({ label, value, emoji, border }: { label: string; value: string; emoji: string; border: string }) {
  const C = useC();
  return (
    <View style={[pr.row, { borderBottomColor: border }]}>
      <Text style={{ fontSize: 20 }}>{emoji}</Text>
      <View style={{ flex: 1 }}>
        <Text style={[pr.rowLabel, { color: C.textMuted }]}>{label}</Text>
        <Text style={[pr.rowVal, { color: C.text }]}>{value}</Text>
      </View>
    </View>
  );
}

function MuhuratLine({ label, period, danger }: { label: string; period: { start: string; end: string }; danger?: boolean }) {
  const C = useC();
  return (
    <View style={[pr.row, { borderBottomColor: C.border3 }]}>
      <Text style={{ fontSize: 18 }}>{danger ? "⛔" : "🕐"}</Text>
      <View style={{ flex: 1 }}>
        <Text style={[pr.rowLabel, { color: C.textMuted }]}>{label}</Text>
        <Text style={[pr.rowVal, { color: danger ? "#ef4444" : C.text }]}>
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
  const [tab, setTab] = useState<TabId>("Aaj");

  const { primaryProfile } = useUser() as any;
  const bd = primaryProfile?.birthData ?? null;
  const kundli = primaryProfile?.kundli ?? null;
  const userLat = bd?.lat ?? 28.6139;
  const userLng = bd?.lon ?? 77.2090;
  const userTz = bd?.tz ?? 5.5;
  const natalMoon = kundli?.moonSign as string | undefined;
  const natalNak = kundli?.nakshatra as string | undefined;

  const today = useMemo(() => { const d = new Date(); d.setHours(0, 0, 0, 0); return d; }, []);
  const todayIso = useMemo(() => {
    const y = today.getFullYear();
    return `${y}-${String(today.getMonth() + 1).padStart(2, "0")}-${String(today.getDate()).padStart(2, "0")}`;
  }, [today]);

  const [real, setReal] = useState<RealPanchang | null>(null);
  const [muhurat, setMuhurat] = useState<DailyMuhurat | null>(null);
  const [strength, setStrength] = useState<TarabalaStrength | null>(null);
  const [gochar, setGochar] = useState<GocharResponse | null>(null);
  const [gocharErr, setGocharErr] = useState<string | null>(null);
  const [ekadashi, setEkadashi] = useState<EkadashiSchedule | null>(null);
  const [ekadashiLoading, setEkadashiLoading] = useState(false);
  const defaultMonthKey = useMemo(
    () => `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, "0")}`,
    [today],
  );
  const [selectedMonthKey, setSelectedMonthKey] = useState(defaultMonthKey);
  const [vivah, setVivah] = useState<MarriageDatesScan["dates"]>([]);
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
        if (d.gochar) { setGochar(d.gochar); setGocharErr(null); }
      }),
      fetchDailyMuhurat({ date: today, ...base })
        .then((d) => { if (id === seq.current) setMuhurat(d); })
        .catch(() => { /* fallback: muhurat_detail from /api/panchang */ }),
      fetchGochar(base)
        .then((d) => { if (id === seq.current) { setGochar(d); setGocharErr(null); } })
        .catch((e) => {
          if (id !== seq.current) return;
          const msg = String((e as Error)?.message || e);
          setGocharErr(msg.includes("404") ? "deploy" : msg);
        }),
      (async () => {
        setEkadashiLoading(true);
        try {
          const r = await fetchEkadashiSchedule({
            fromDate: today, years: 5, tz: userTz, signal: ctrl.signal,
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
      fetchMarriageDates({ fromDate: today, years: 5, tz: userTz, signal: ctrl.signal })
        .then((r) => { if (id === seq.current) setVivah(r.dates || []); }),
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
        setErr("Panchang load nahi hua — server check karein");
      }
      setLoading(false);
    });

    return () => ctrl.abort();
  }, [today, todayIso, userLat, userLng, userTz, natalMoon, natalNak, defaultMonthKey]);

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
    const byMonth: Record<string, MarriageDatesScan["dates"]> = {};
    for (const item of vivah) {
      const m = new Date(item.date + "T12:00:00").toLocaleString("hi-IN", { month: "long", year: "numeric" });
      (byMonth[m] = byMonth[m] || []).push(item);
    }
    return Object.entries(byMonth);
  }, [vivah]);

  const dateStr = formatToday(todayIso);

  return (
    <View style={{ flex: 1 }}>
      <CosmicBg />
      <View style={[s.topBar, { paddingTop: insets.top + 10 }]}>
        <Pressable onPress={() => router.back()} style={s.backBtn}>
          <Feather name={I18nManager.isRTL ? "arrow-right" : "arrow-left"} size={20} color={C.text} />
        </Pressable>
        <View style={{ flex: 1 }}>
          <Text style={[s.title, { color: C.text }]}>{t.panchangTitle}</Text>
          <Text style={[s.sub, { color: C.textMuted }]} numberOfLines={1}>{dateStr}</Text>
        </View>
        <View style={{ width: 36 }} />
      </View>

      <ScrollView horizontal showsHorizontalScrollIndicator={false}
        style={{ flexGrow: 0, maxHeight: 44 }}
        contentContainerStyle={{ paddingHorizontal: 16, gap: 8, paddingBottom: 10 }}>
        {TABS.map((tb) => (
          <Pressable
            key={tb}
            onPress={() => { Haptics.selectionAsync(); setTab(tb); }}
            style={[s.tab, { borderColor: C.border }, tab === tb && { backgroundColor: "#a78bfa", borderColor: "#a78bfa" }]}
          >
            <Text style={[s.tabText, { color: tab === tb ? "#fff" : C.textMuted }]}>{tb}</Text>
          </Pressable>
        ))}
      </ScrollView>

      {loading && tab === "Aaj" ? (
        <View style={s.centerLoad}>
          <ActivityIndicator color="#a78bfa" size="large" />
          <Text style={[s.loadingTxt, { color: C.textMuted }]}>Panchang load ho raha hai…</Text>
        </View>
      ) : (
        <ScrollView
          showsVerticalScrollIndicator={false}
          contentContainerStyle={{ paddingHorizontal: 16, paddingBottom: insets.bottom + 100, gap: 14 }}
        >
          {err && tab === "Aaj" ? (
            <Text style={[s.hint, { color: "#f59e0b", textAlign: "center" }]}>{err}</Text>
          ) : null}

          {/* ── AAJ ── */}
          {tab === "Aaj" && (
            <>
              <View style={[s.auspCard, { backgroundColor: C.bgCard, borderColor: auspicious.color + "55" }]}>
                <Text style={[s.sectionLbl, { color: C.textMuted }]}>AAJ KI SHUBHATA</Text>
                <View style={s.auspHeader}>
                  <Text style={[s.auspBand, { color: auspicious.color }]}>
                    {auspicious.emoji} {auspicious.band}
                  </Text>
                  <View style={[s.auspScoreCircle, { borderColor: auspicious.color }]}>
                    <Text style={[s.auspScoreNum, { color: auspicious.color }]}>{auspicious.score}</Text>
                    <Text style={[s.auspScorePct, { color: auspicious.color }]}>%</Text>
                  </View>
                </View>
                <View style={[s.auspBarBg, { backgroundColor: C.isDark ? "#1e293b" : "#e5e7eb" }]}>
                  <View style={[s.auspBarFg, { width: `${auspicious.score}%`, backgroundColor: auspicious.color }]} />
                </View>
              </View>

              {strength && (
                <View style={[s.card, { backgroundColor: C.bgCard, borderColor: C.border, paddingVertical: 12 }]}>
                  <Text style={[s.sectionLbl, { color: C.textMuted, marginBottom: 8 }]}>AAPKI TARABALA / CHANDRABALA</Text>
                  <Text style={[s.vivahDate, { color: strength.overall_ok ? "#22c55e" : "#f59e0b" }]}>
                    {strength.strength_band} · {strength.strength_score}%
                  </Text>
                  <Text style={[s.vivahMeta, { color: C.textMuted, marginTop: 4 }]}>
                    Tarabala: {strength.tarabala.tara_name} {strength.tarabala.ok ? "✓" : "✗"}
                    {"  ·  "}Chandra: {strength.transit_moon_sign}
                  </Text>
                </View>
              )}
              {!natalMoon && !natalNak && (
                <Text style={[s.hint, { color: C.textMuted }]}>
                  Tarabala ke liye profile mein kundli complete karein.
                </Text>
              )}

              <View style={[s.card, { backgroundColor: C.bgCard, borderColor: C.border }]}>
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

              {todayEkadashi.length > 0 && (
                <View style={[s.card, { backgroundColor: C.bgCard, borderColor: "#a78bfa55", padding: 14 }]}>
                  <Text style={[s.sectionLbl, { color: "#a78bfa", marginBottom: 8 }]}>AAJ EKADASHI VRAT</Text>
                  {todayEkadashi.map((f) => (
                    <Text key={f.date} style={[s.vivahDate, { color: C.text }]}>
                      🪔 {f.festival_name} · {f.paksha} paksha
                    </Text>
                  ))}
                </View>
              )}
            </>
          )}

          {/* ── MUHURAT ── */}
          {tab === "Muhurat" && (
            <View style={[s.card, { backgroundColor: C.bgCard, borderColor: C.border }]}>
              {muhurat ? (
                <>
                  <MuhuratLine label="Brahma Muhurta" period={muhurat.brahma_muhurta} />
                  <MuhuratLine label={t.rahukaal} period={muhurat.rahu_kaal} danger />
                  <MuhuratLine label="Gulika Kaal" period={muhurat.gulika_kaal} danger />
                  <MuhuratLine label={t.panYamaghanta || "Yamaganda"} period={muhurat.yamaghanta} danger />
                  <View style={[pr.row, { borderBottomWidth: 0 }]}>
                    <Text style={{ fontSize: 18 }}>✨</Text>
                    <View style={{ flex: 1 }}>
                      <Text style={[pr.rowLabel, { color: C.textMuted }]}>Abhijit Muhurat</Text>
                      <Text style={[pr.rowVal, { color: "#22c55e" }]}>
                        {muhurat.abhijit_muhurat.start} – {muhurat.abhijit_muhurat.end}
                      </Text>
                    </View>
                  </View>
                </>
              ) : (
                <Text style={[s.hint, { color: C.textMuted, padding: 16 }]}>
                  Muhurat load nahi hua — location set karein.
                </Text>
              )}
              <Text style={[s.hint, { color: C.textMuted, padding: 12 }]}>
                Sunrise/sunset se 8 hisse — aapke {userLat.toFixed(1)}°, {userLng.toFixed(1)}° par
              </Text>
            </View>
          )}

          {/* ── GOCHAR ── */}
          {tab === "Gochar" && (
            <View style={[s.card, { backgroundColor: C.bgCard, borderColor: C.border }]}>
              {gochar ? (
                GOCHAR_ORDER.map((key, i) => {
                  const p = gochar.planets[key];
                  if (!p) return null;
                  const isLast = i === GOCHAR_ORDER.length - 1;
                  return (
                    <View
                      key={key}
                      style={[s.vivahRow, { borderBottomColor: C.border3 }, isLast && { borderBottomWidth: 0 }]}
                    >
                      <Text style={{ fontSize: 18, width: 28 }}>☉</Text>
                      <View style={{ flex: 1 }}>
                        <Text style={[s.vivahDate, { color: C.text }]}>{GOCHAR_HI[key] || key}</Text>
                        <Text style={[s.vivahMeta, { color: C.textMuted }]}>
                          {p.rashi} · {p.degree.toFixed(2)}°
                          {p.is_retrograde ? " · Vakri" : ""}
                        </Text>
                      </View>
                      {p.status ? (
                        <Text style={[s.planetOk, { color: p.status === "Uday" ? "#22c55e" : "#ef4444" }]}>
                          {p.status}
                        </Text>
                      ) : null}
                    </View>
                  );
                })
              ) : (
                <View style={{ padding: 16, gap: 8 }}>
                  <Text style={[s.emptyTitle, { color: C.text }]}>Gochar load nahi hua</Text>
                  <Text style={[s.hint, { color: C.textMuted, lineHeight: 16 }]}>
                    {gocharErr === "deploy"
                      ? "Aapka server (VPS) purana hai — naya backend deploy karein. Tab /api/panchang/gochar chalega."
                      : "API se connect nahi ho paya. Metro restart karke dubara try karein."}
                  </Text>
                  {real && !gochar ? (
                    <Text style={[s.hint, { color: "#f59e0b" }]}>
                      Purana /api/panchang chal raha hai; gochar usme bundled nahi hai abhi.
                    </Text>
                  ) : null}
                </View>
              )}
            </View>
          )}

          {/* ── VRAT ── */}
          {tab === "Vrat" && (
            <>
              <Text style={[s.countLine, { color: C.textMuted }]}>
                Ekadashi vrat · aaj se agle 5 saal · kul {ekadashi?.total ?? "—"} din
              </Text>

              {ekadashiLoading ? (
                <View style={s.centerLoad}>
                  <ActivityIndicator color="#a78bfa" />
                  <Text style={[s.loadingTxt, { color: C.textMuted }]}>Ekadashi gin raha hai…</Text>
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
                            s.monthChip,
                            { borderColor: C.border },
                            active && { backgroundColor: "#a78bfa", borderColor: "#a78bfa" },
                          ]}
                        >
                          <Text style={[s.monthChipText, { color: active ? "#fff" : C.textMuted }]}>
                            {new Date(m.year, m.month - 1, 1).toLocaleString("hi-IN", { month: "short", year: "2-digit" })}
                          </Text>
                          {isCurrent && <View style={s.monthChipDot} />}
                        </Pressable>
                      );
                    })}
                  </ScrollView>

                  <Text style={[s.monthHdr, { color: C.isDark ? "#a78bfa" : "#7c3aed" }]}>
                    {(selectedEkadashiMonth?.label || "").toUpperCase()}
                    {selectedMonthKey === defaultMonthKey ? " · ABHI KA MAHINA" : ""}
                  </Text>

                  {!selectedEkadashiMonth?.dates.length ? (
                    <View style={[s.card, { backgroundColor: C.bgCard, borderColor: C.border }]}>
                      <Text style={[s.emptyTitle, { color: C.text }]}>Is mahine koi Ekadashi nahi</Text>
                    </View>
                  ) : (
                    <View style={[s.card, { backgroundColor: C.bgCard, borderColor: C.border }]}>
                      {selectedEkadashiMonth.dates.map((f, i) => {
                        const isToday = f.date === todayIso;
                        const isLast = i === selectedEkadashiMonth.dates.length - 1;
                        return (
                          <View
                            key={f.date}
                            style={[
                              s.vivahRow,
                              { borderBottomColor: C.border3, opacity: f.date < todayIso ? 0.55 : 1 },
                              isLast && { borderBottomWidth: 0 },
                            ]}
                          >
                            <View style={{ flex: 1 }}>
                              <Text style={[s.vivahDate, { color: C.text }]}>
                                {f.display} · {f.weekday}
                                {isToday ? "  ·  Aaj" : ""}
                              </Text>
                              <Text style={[s.vivahMeta, { color: C.textMuted }]}>
                                {f.festival_name} · {f.paksha} paksha
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
          )}

          {/* ── VIVAH ── */}
          {tab === "Vivah" && (
            <>
              <Text style={[s.countLine, { color: C.textMuted }]}>
                {vivah.length} shubh vivah din · agle 5 saal
              </Text>
              {vivah.length === 0 ? (
                <View style={[s.card, { backgroundColor: C.bgCard, borderColor: C.border }]}>
                  <Text style={[s.emptyTitle, { color: C.text }]}>Abhi vivah dates load nahi hui</Text>
                </View>
              ) : (
                vivahByMonth.slice(0, 6).map(([month, items]) => (
                  <View key={month}>
                    <Text style={[s.monthHdr, { color: C.isDark ? "#a78bfa" : "#7c3aed" }]}>{month.toUpperCase()}</Text>
                    <View style={[s.card, { backgroundColor: C.bgCard, borderColor: C.border }]}>
                      {items.slice(0, 8).map((item, i) => (
                        <View
                          key={item.date}
                          style={[s.vivahRow, { borderBottomColor: C.border3 }, i === Math.min(items.length, 8) - 1 && { borderBottomWidth: 0 }]}
                        >
                          <View style={{ flex: 1 }}>
                            <Text style={[s.vivahDate, { color: C.text }]}>
                              {item.display || item.date} · {item.weekday || ""}
                            </Text>
                            <Text style={[s.vivahMeta, { color: C.textMuted }]}>
                              {item.tithi}{item.nakshatra ? ` · ${item.nakshatra}` : ""}
                            </Text>
                          </View>
                        </View>
                      ))}
                    </View>
                  </View>
                ))
              )}
            </>
          )}
        </ScrollView>
      )}
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
    paddingHorizontal: 20, paddingBottom: 10, gap: 8,
  },
  backBtn: { width: 36, height: 36, alignItems: "center", justifyContent: "center" },
  title: { fontSize: 20, fontFamily: F.bold },
  sub: { fontSize: 11, fontFamily: F.regular, marginTop: 2 },
  tab: { paddingHorizontal: 14, paddingVertical: 7, borderRadius: 20, borderWidth: 1 },
  tabText: { fontSize: 12, fontFamily: F.semibold },
  sectionLbl: { fontSize: 10, fontFamily: F.bold, letterSpacing: 1.5 },
  auspCard: { borderRadius: 16, borderWidth: 1.5, padding: 16, gap: 10 },
  auspHeader: { flexDirection: "row", alignItems: "center", justifyContent: "space-between" },
  auspBand: { fontSize: 22, fontFamily: F.bold },
  auspScoreCircle: {
    width: 64, height: 64, borderRadius: 32, borderWidth: 3,
    alignItems: "center", justifyContent: "center", flexDirection: "row",
  },
  auspScoreNum: { fontSize: 22, fontFamily: F.bold },
  auspScorePct: { fontSize: 11, fontFamily: F.bold, marginTop: 4 },
  auspBarBg: { height: 8, borderRadius: 4, overflow: "hidden" },
  auspBarFg: { height: "100%", borderRadius: 4 },
  card: { borderRadius: 16, borderWidth: 1, overflow: "hidden" },
  hint: { fontSize: 10, fontFamily: F.semibold },
  countLine: { fontSize: 11, fontFamily: F.medium },
  monthHdr: { fontSize: 11, fontFamily: F.bold, letterSpacing: 1.5, paddingVertical: 6 },
  vivahRow: { flexDirection: "row", alignItems: "center", gap: 10, paddingVertical: 12, paddingHorizontal: 14, borderBottomWidth: 1 },
  vivahDate: { fontSize: 14, fontFamily: F.bold },
  vivahMeta: { fontSize: 11, fontFamily: F.regular, marginTop: 2 },
  planetOk: { fontSize: 10, fontFamily: F.bold },
  emptyTitle: { fontSize: 14, fontFamily: F.semibold, padding: 14 },
  centerLoad: { alignItems: "center", justifyContent: "center", gap: 12, paddingVertical: 28 },
  loadingTxt: { fontSize: 13, fontFamily: F.medium },
  monthChip: {
    paddingHorizontal: 12, paddingVertical: 8, borderRadius: 16, borderWidth: 1,
    flexDirection: "row", alignItems: "center", gap: 6,
  },
  monthChipText: { fontSize: 12, fontFamily: F.semibold },
  monthChipDot: { width: 5, height: 5, borderRadius: 3, backgroundColor: "#22c55e" },
});
