import { Feather } from "@expo/vector-icons";
import { router, useLocalSearchParams } from "expo-router";
import * as Haptics from "expo-haptics";
import React, { useMemo, useState } from "react";
import { ScrollView, StyleSheet, Text, View, Pressable } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import CosmicBg from "@/components/CosmicBg";
import { useC } from "@/context/ThemeContext";

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

const FESTIVALS_2026 = [
  { date: "Jan 14", name: "Makar Sankranti", emoji: "🪁", type: "tyohar" },
  { date: "Jan 23", name: "Basant Panchami", emoji: "🌼", type: "tyohar" },
  { date: "Feb 26", name: "Mahashivratri", emoji: "🔱", type: "tyohar" },
  { date: "Mar 3",  name: "Holi", emoji: "🎨", type: "tyohar" },
  { date: "Mar 2",  name: "Holika Dahan", emoji: "🔥", type: "tyohar" },
  { date: "Mar 30", name: "Ram Navami", emoji: "🏹", type: "tyohar" },
  { date: "Apr 2",  name: "Hanuman Jayanti", emoji: "🙏", type: "tyohar" },
  { date: "Apr 14", name: "Dr. Ambedkar Jayanti", emoji: "📚", type: "rashtriya" },
  { date: "Apr 15", name: "Baisakhi", emoji: "🌾", type: "tyohar" },
  { date: "May 12", name: "Buddha Purnima", emoji: "☸️", type: "tyohar" },
  { date: "Jun 11", name: "Eid ul-Adha", emoji: "🌙", type: "tyohar" },
  { date: "Jul 9",  name: "Rath Yatra", emoji: "🛕", type: "tyohar" },
  { date: "Aug 3",  name: "Guru Purnima", emoji: "🌕", type: "tyohar" },
  { date: "Aug 9",  name: "Nag Panchami", emoji: "🐍", type: "tyohar" },
  { date: "Aug 19", name: "Raksha Bandhan", emoji: "🪢", type: "tyohar" },
  { date: "Aug 26", name: "Janmashtami", emoji: "🦚", type: "tyohar" },
  { date: "Sep 1",  name: "Ganesh Chaturthi", emoji: "🐘", type: "tyohar" },
  { date: "Oct 2",  name: "Gandhi Jayanti", emoji: "🕊️", type: "rashtriya" },
  { date: "Oct 2",  name: "Navratri Shuru", emoji: "🪷", type: "tyohar" },
  { date: "Oct 9",  name: "Dussehra", emoji: "🏹", type: "tyohar" },
  { date: "Oct 20", name: "Diwali", emoji: "🪔", type: "tyohar" },
  { date: "Oct 22", name: "Govardhan Puja", emoji: "🐄", type: "tyohar" },
  { date: "Oct 23", name: "Bhai Dooj", emoji: "👫", type: "tyohar" },
  { date: "Nov 5",  name: "Chhath Puja", emoji: "☀️", type: "tyohar" },
  { date: "Nov 27", name: "Guru Nanak Jayanti", emoji: "✨", type: "tyohar" },
  { date: "Dec 25", name: "Christmas", emoji: "🎄", type: "tyohar" },
];

const TABS = ["Panchang", "Rahu Kaal", "Tyohar & Vrat"];

export default function PanchangScreen() {
  const C = useC();
  const insets = useSafeAreaInsets();
  const params = useLocalSearchParams<{ tab?: string }>();
  const initTab = params.tab === "rahu" ? 1 : params.tab === "festivals" ? 2 : 0;
  const [tabIdx, setTabIdx] = useState(initTab);

  const today = new Date();
  const panchang = useMemo(() => getPanchang(today), []);
  const kaal = useMemo(() => getRahuKaal(today.getDay()), []);

  const dateStr = today.toLocaleDateString("hi-IN", { weekday: "long", day: "numeric", month: "long", year: "numeric" });

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
          <Text style={[s.title, { color: C.text }]}>Panchang</Text>
          <Text style={[s.sub, { color: C.textMuted }]}>{dateStr}</Text>
        </View>
        <View style={{ width: 36 }} />
      </View>

      {/* Tabs */}
      <ScrollView horizontal showsHorizontalScrollIndicator={false} style={{ flexGrow: 0 }} contentContainerStyle={{ paddingHorizontal: 16, gap: 8, paddingBottom: 12 }}>
        {TABS.map((t, i) => (
          <Pressable
            key={t}
            onPress={() => { Haptics.selectionAsync(); setTabIdx(i); }}
            style={[s.tab, { borderColor: C.border }, tabIdx === i && { backgroundColor: "#a78bfa", borderColor: "#a78bfa" }]}
          >
            <Text style={[s.tabText, { color: tabIdx === i ? "#fff" : C.textMuted }]}>{t}</Text>
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
                  <Text style={[s.sunLabel, { color: C.textMuted }]}>Sunrise</Text>
                  <Text style={[s.sunVal, { color: "#f59e0b" }]}>{SUNRISE}</Text>
                </View>
              </View>
              <View style={[s.sunDivider, { backgroundColor: C.border }]} />
              <View style={s.sunItem}>
                <Text style={{ fontSize: 24 }}>🌇</Text>
                <View>
                  <Text style={[s.sunLabel, { color: C.textMuted }]}>Sunset</Text>
                  <Text style={[s.sunVal, { color: "#fb923c" }]}>{SUNSET}</Text>
                </View>
              </View>
            </View>

            {/* Panchang details */}
            <View style={[s.card, { backgroundColor: C.bgCard, borderColor: C.border }]}>
              <InfoRow label="Vaar (Weekday)" value={panchang.var}      emoji="📆" />
              <InfoRow label="Tithi"          value={panchang.tithi}    emoji="🌙" />
              <InfoRow label="Nakshatra"      value={panchang.nakshatra}emoji="⭐" />
              <InfoRow label="Yoga"           value={panchang.yoga}     emoji="🔮" />
              <InfoRow label="Karana"         value={panchang.karana}   emoji="✨" />
            </View>

            {/* Subah muhurt note */}
            <View style={[s.card, { backgroundColor: C.bgCard, borderColor: C.border }]}>
              <Text style={[s.cardTitle, { color: C.textMuted }]}>🌟 BRAHMA MUHURTA</Text>
              <Text style={[s.cardVal, { color: "#f59e0b" }]}>04:38 AM – 05:26 AM</Text>
              <Text style={[s.cardTip, { color: C.textMuted }]}>Puja, dhyan aur naye kaaryon ke liye param shubh samay</Text>
            </View>
          </>
        )}

        {/* ── RAHU KAAL TAB ── */}
        {tabIdx === 1 && (
          <>
            <View style={[s.rahuHero, { backgroundColor: C.isDark ? "rgba(239,68,68,0.07)" : "#FEE2E2", borderColor: "rgba(239,68,68,0.2)" }]}>
              <Text style={{ fontSize: 36 }}>⛔</Text>
              <View>
                <Text style={[s.rahuTitle, { color: "#ef4444" }]}>Rahu Kaal</Text>
                <Text style={[s.rahuTime, { color: C.text }]}>{kaal.rahu}</Text>
                <Text style={[s.rahuTip, { color: C.textMuted }]}>Is samay mein koi shubh kaarya na karein</Text>
              </View>
            </View>

            <View style={[s.card, { backgroundColor: C.bgCard, borderColor: C.border }]}>
              <View style={pr.row}>
                <Text style={{ fontSize: 20 }}>⚡</Text>
                <View style={{ flex: 1 }}>
                  <Text style={[pr.rowLabel, { color: C.textMuted }]}>Yamaghanta</Text>
                  <Text style={[pr.rowVal, { color: C.text }]}>{kaal.yama}</Text>
                  <Text style={[s.rahuTip, { color: C.textDim }]}>Shubh kaarya avoid karein</Text>
                </View>
              </View>
              <View style={[pr.row, { borderBottomWidth: 0 }]}>
                <Text style={{ fontSize: 20 }}>🌑</Text>
                <View style={{ flex: 1 }}>
                  <Text style={[pr.rowLabel, { color: C.textMuted }]}>Gulika Kaal</Text>
                  <Text style={[pr.rowVal, { color: C.text }]}>{kaal.gulika}</Text>
                  <Text style={[s.rahuTip, { color: C.textDim }]}>Maanglik kaarya na karein</Text>
                </View>
              </View>
            </View>

            <View style={[s.card, { backgroundColor: C.bgCard, borderColor: C.border, gap: 8 }]}>
              <Text style={[s.cardTitle, { color: C.textMuted }]}>ℹ️ ABHIJIT MUHURTA (SHUBH)</Text>
              <Text style={[s.cardVal, { color: "#22c55e" }]}>11:54 AM – 12:46 PM</Text>
              <Text style={[s.cardTip, { color: C.textMuted }]}>Har shubh kaarya ke liye uchit samay. Din ka sabse shubh muhurta.</Text>
            </View>
          </>
        )}

        {/* ── FESTIVALS TAB ── */}
        {tabIdx === 2 && (
          <>
            <Text style={[s.yearLabel, { color: C.textMuted }]}>📅 2026 KE PRAMUKH TYOHAR & RASHTRIYA PARV</Text>
            <View style={[s.card, { backgroundColor: C.bgCard, borderColor: C.border }]}>
              {FESTIVALS_2026.map((f, i) => (
                <View
                  key={`${f.date}-${f.name}`}
                  style={[
                    s.festRow,
                    { borderBottomColor: C.border3 },
                    i === FESTIVALS_2026.length - 1 && { borderBottomWidth: 0 },
                  ]}
                >
                  <Text style={{ fontSize: 22, width: 32 }}>{f.emoji}</Text>
                  <View style={{ flex: 1 }}>
                    <Text style={[s.festName, { color: C.text }]}>{f.name}</Text>
                    <Text style={[s.festDate, { color: C.textMuted }]}>{f.date}, 2026</Text>
                  </View>
                  {f.type === "rashtriya" && (
                    <View style={[s.badge, { backgroundColor: C.isDark ? "#3b82f620" : "#DBEAFE", borderColor: C.isDark ? "#3b82f640" : "#93C5FD" }]}>
                      <Text style={[s.badgeText, { color: "#60a5fa" }]}>Rashtriya</Text>
                    </View>
                  )}
                </View>
              ))}
            </View>
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
  festRow: {
    flexDirection: "row", alignItems: "center", gap: 10,
    paddingVertical: 12, borderBottomWidth: 1,
  },
  festName: { fontSize: 14, fontFamily: F.semibold },
  festDate: { fontSize: 11, fontFamily: F.regular, marginTop: 1 },
  badge: { paddingHorizontal: 7, paddingVertical: 3, borderRadius: 8, borderWidth: 1 },
  badgeText: { fontSize: 9, fontFamily: F.bold },
});
