import { Feather } from "@expo/vector-icons";
import * as Haptics from "expo-haptics";
import { router } from "expo-router";
import React, { useState } from "react";
import { Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import CosmicBg from "@/components/CosmicBg";
import { useC } from "@/context/ThemeContext";

const F = {
  bold: "Nunito_700Bold", semibold: "Nunito_600SemiBold",
  medium: "Nunito_500Medium", regular: "Nunito_400Regular",
};

const CATEGORIES = [
  { id: "shadi",     emoji: "💒", title: "Vivah Muhurat",       subtitle: "Shadi ke shubh din", color: "#f43f5e" },
  { id: "griha",     emoji: "🏠", title: "Griha Pravesh",        subtitle: "Naye ghar mein pravesh", color: "#f59e0b" },
  { id: "business",  emoji: "💼", title: "Vyapar Aarambh",       subtitle: "Business shuru karne ka din", color: "#22c55e" },
  { id: "vehicle",   emoji: "🚗", title: "Vahan Kharidi",        subtitle: "Naya vahan kharidna", color: "#60a5fa" },
  { id: "namkaran",  emoji: "👶", title: "Namkaran Muhurat",     subtitle: "Bacche ka naam rakhna", color: "#a78bfa" },
  { id: "mundane",   emoji: "✂️", title: "Mundan Muhurat",       subtitle: "Bacche ka pehla mudan", color: "#fb923c" },
  { id: "thread",    emoji: "🧵", title: "Yagyopavit Muhurat",   subtitle: "Janeu / Upanayana", color: "#10b981" },
  { id: "travel",    emoji: "✈️", title: "Yatra Muhurat",        subtitle: "Safar ke liye shubh samay", color: "#06b6d4" },
];

type MuhuratData = {
  month: string; dates: { date: string; day: string; time: string; nakshatra: string; good: boolean }[];
}[];

const MUHURAT_DATA: Record<string, MuhuratData> = {
  shadi: [
    { month: "April 2026", dates: [
      { date: "Apr 18", day: "Shanivaar", time: "7:12 AM – 1:45 PM", nakshatra: "Rohini", good: true },
      { date: "Apr 21", day: "Mangalvar", time: "6:58 AM – 11:30 AM", nakshatra: "Mrigashira", good: true },
      { date: "Apr 27", day: "Somvar",    time: "8:00 AM – 12:15 PM", nakshatra: "Punarvasu", good: false },
    ]},
    { month: "May 2026", dates: [
      { date: "May 5",  day: "Mangalvar", time: "7:00 AM – 10:45 AM", nakshatra: "Magha",    good: false },
      { date: "May 10", day: "Ravivaar",  time: "6:50 AM – 1:00 PM",  nakshatra: "Hasta",    good: true },
      { date: "May 17", day: "Ravivaar",  time: "7:10 AM – 2:30 PM",  nakshatra: "Anuradha", good: true },
      { date: "May 24", day: "Ravivaar",  time: "6:55 AM – 11:00 AM", nakshatra: "Shravana", good: true },
    ]},
    { month: "November 2026", dates: [
      { date: "Nov 15", day: "Ravivaar",  time: "7:30 AM – 2:00 PM", nakshatra: "Mrigashira", good: true },
      { date: "Nov 22", day: "Ravivaar",  time: "7:45 AM – 1:30 PM", nakshatra: "Pushya",    good: true },
      { date: "Nov 29", day: "Ravivaar",  time: "8:00 AM – 12:00 PM", nakshatra: "Uttara Phalguni", good: true },
    ]},
  ],
  griha: [
    { month: "April 2026", dates: [
      { date: "Apr 9",  day: "Guruvaar",  time: "8:15 AM – 12:30 PM", nakshatra: "Rohini",   good: true },
      { date: "Apr 16", day: "Guruvaar",  time: "7:50 AM – 1:15 PM",  nakshatra: "Hasta",    good: true },
    ]},
    { month: "May 2026", dates: [
      { date: "May 7",  day: "Guruvaar",  time: "7:30 AM – 11:45 AM", nakshatra: "Pushya",   good: true },
      { date: "May 14", day: "Guruvaar",  time: "7:15 AM – 12:00 PM", nakshatra: "Rohini",   good: true },
    ]},
  ],
  business: [
    { month: "April 2026", dates: [
      { date: "Apr 8",  day: "Budhavar",  time: "9:00 AM – 12:00 PM", nakshatra: "Ashwini",  good: true },
      { date: "Apr 15", day: "Budhavar",  time: "8:30 AM – 1:00 PM",  nakshatra: "Rohini",   good: true },
      { date: "Apr 22", day: "Budhavar",  time: "9:15 AM – 11:30 AM", nakshatra: "Mrigashira", good: false },
    ]},
    { month: "May 2026", dates: [
      { date: "May 6",  day: "Budhavar",  time: "8:45 AM – 12:30 PM", nakshatra: "Hasta",    good: true },
      { date: "May 13", day: "Budhavar",  time: "9:00 AM – 1:15 PM",  nakshatra: "Chitra",   good: true },
    ]},
  ],
  vehicle: [
    { month: "April 2026", dates: [
      { date: "Apr 3",  day: "Shukravar", time: "10:00 AM – 1:30 PM", nakshatra: "Rohini",    good: true },
      { date: "Apr 10", day: "Shukravar", time: "9:30 AM – 12:00 PM", nakshatra: "Hasta",     good: true },
    ]},
  ],
  namkaran: [
    { month: "April 2026", dates: [
      { date: "Apr 12", day: "Ravivaar",  time: "8:00 AM – 10:30 AM", nakshatra: "Pushya",   good: true },
      { date: "Apr 26", day: "Ravivaar",  time: "7:45 AM – 11:00 AM", nakshatra: "Rohini",   good: true },
    ]},
  ],
  mundane: [
    { month: "April 2026", dates: [
      { date: "Apr 5",  day: "Ravivaar",  time: "7:30 AM – 10:00 AM", nakshatra: "Ashwini",  good: true },
      { date: "Apr 19", day: "Ravivaar",  time: "7:00 AM – 9:30 AM",  nakshatra: "Hasta",    good: true },
    ]},
  ],
  thread: [
    { month: "May 2026", dates: [
      { date: "May 3",  day: "Ravivaar",  time: "7:15 AM – 9:45 AM",  nakshatra: "Pushya",   good: true },
      { date: "May 17", day: "Ravivaar",  time: "6:58 AM – 10:00 AM", nakshatra: "Rohini",   good: true },
    ]},
  ],
  travel: [
    { month: "April 2026", dates: [
      { date: "Apr 7",  day: "Mangalvar", time: "6:00 AM – 8:00 AM",  nakshatra: "Ashwini",  good: true },
      { date: "Apr 14", day: "Mangalvar", time: "7:00 AM – 9:00 AM",  nakshatra: "Mrigashira", good: true },
      { date: "Apr 9",  day: "Guruvaar",  time: "8:00 AM – 10:00 AM", nakshatra: "Rohini",   good: false },
    ]},
  ],
};

export default function MuhuratScreen() {
  const C = useC();
  const insets = useSafeAreaInsets();
  const [selected, setSelected] = useState<string>("shadi");

  const data = MUHURAT_DATA[selected] ?? [];
  const cat = CATEGORIES.find(c => c.id === selected)!;

  return (
    <View style={{ flex: 1 }}>
      <CosmicBg />
      <View style={[s.topBar, { paddingTop: insets.top + 10 }]}>
        <Pressable onPress={() => router.back()} style={s.backBtn}>
          <Feather name="arrow-left" size={20} color={C.text} />
        </Pressable>
        <View>
          <Text style={[s.title, { color: C.text }]}>Shubh Muhurat</Text>
          <Text style={[s.sub, { color: C.textMuted }]}>Har kaarya ke liye shubh samay</Text>
        </View>
        <View style={{ width: 36 }} />
      </View>

      {/* Category pills */}
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        style={{ flexGrow: 0 }}
        contentContainerStyle={{ paddingHorizontal: 16, gap: 8, paddingBottom: 14 }}
      >
        {CATEGORIES.map(c => (
          <Pressable
            key={c.id}
            onPress={() => { Haptics.selectionAsync(); setSelected(c.id); }}
            style={[
              s.catPill,
              { backgroundColor: C.bgCard, borderColor: C.border },
              selected === c.id && { backgroundColor: `${c.color}18`, borderColor: `${c.color}60` },
            ]}
          >
            <Text style={{ fontSize: 16 }}>{c.emoji}</Text>
            <Text style={[s.catText, { color: selected === c.id ? c.color : C.textMuted }]}>{c.title}</Text>
          </Pressable>
        ))}
      </ScrollView>

      <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={{ paddingHorizontal: 16, paddingBottom: insets.bottom + 100, gap: 16 }}>
        {/* Header */}
        <View style={[s.heroCard, { backgroundColor: `${cat.color}12`, borderColor: `${cat.color}30` }]}>
          <Text style={{ fontSize: 36 }}>{cat.emoji}</Text>
          <View>
            <Text style={[s.heroTitle, { color: cat.color }]}>{cat.title}</Text>
            <Text style={[s.heroSub, { color: C.textMuted }]}>{cat.subtitle}</Text>
          </View>
        </View>

        {/* Muhurat list */}
        {data.length === 0 ? (
          <View style={[s.emptyBox, { backgroundColor: C.bgCard, borderColor: C.border }]}>
            <Text style={{ fontSize: 32 }}>🔭</Text>
            <Text style={[s.emptyText, { color: C.textMuted }]}>Is category ke liye abhi muhurat nahi hai. Jald aayenge.</Text>
          </View>
        ) : (
          data.map(monthData => (
            <View key={monthData.month}>
              <Text style={[s.monthLabel, { color: C.textMuted }]}>{monthData.month.toUpperCase()}</Text>
              <View style={[s.monthCard, { backgroundColor: C.bgCard, borderColor: C.border }]}>
                {monthData.dates.map((d, i) => (
                  <View
                    key={`${d.date}-${d.time}`}
                    style={[
                      s.dateRow,
                      { borderBottomColor: C.border3 },
                      i === monthData.dates.length - 1 && { borderBottomWidth: 0 },
                    ]}
                  >
                    <View style={[s.dateBox, { backgroundColor: d.good ? (C.isDark ? `${cat.color}18` : `${cat.color}22`) : (C.isDark ? "rgba(239,68,68,0.08)" : "#FEE2E2"), borderColor: d.good ? `${cat.color}40` : "rgba(239,68,68,0.2)" }]}>
                      <Text style={[s.dateNum, { color: d.good ? cat.color : "#ef4444" }]}>{d.date.split(" ")[1]}</Text>
                      <Text style={[s.dateMon, { color: d.good ? cat.color : "#ef4444" }]}>{d.date.split(" ")[0]}</Text>
                    </View>
                    <View style={{ flex: 1 }}>
                      <View style={{ flexDirection: "row", alignItems: "center", gap: 6 }}>
                        <Text style={[s.dayName, { color: C.text }]}>{d.day}</Text>
                        {!d.good && (
                          <View style={s.avoidBadge}>
                            <Text style={s.avoidText}>Avoid</Text>
                          </View>
                        )}
                      </View>
                      <Text style={[s.timeText, { color: d.good ? cat.color : C.textDim }]}>⏰ {d.time}</Text>
                      <Text style={[s.nakshatraText, { color: C.textMuted }]}>⭐ {d.nakshatra} Nakshatra</Text>
                    </View>
                    {d.good && <Feather name="check-circle" size={18} color={cat.color} />}
                  </View>
                ))}
              </View>
            </View>
          ))
        )}

        {/* Note */}
        <View style={[s.noteBox, { backgroundColor: C.bgCard2, borderColor: C.border }]}>
          <Feather name="info" size={14} color={C.textDim} />
          <Text style={[s.noteText, { color: C.textMuted }]}>
            Muhurat dates approximate hain. Pandit ji se exact time aur local timing confirm zaroor karein.
          </Text>
        </View>
      </ScrollView>
    </View>
  );
}

const s = StyleSheet.create({
  topBar: {
    flexDirection: "row", alignItems: "center", justifyContent: "space-between",
    paddingHorizontal: 20, paddingBottom: 14,
  },
  backBtn: { width: 36, height: 36, alignItems: "center", justifyContent: "center" },
  title: { fontSize: 20, fontFamily: F.bold, letterSpacing: -0.3 },
  sub: { fontSize: 11, fontFamily: F.regular, marginTop: 1 },
  catPill: {
    flexDirection: "row", alignItems: "center", gap: 7,
    paddingHorizontal: 12, paddingVertical: 8,
    borderRadius: 20, borderWidth: 1,
  },
  catText: { fontSize: 12, fontFamily: F.semibold },
  heroCard: {
    flexDirection: "row", alignItems: "center", gap: 16,
    borderRadius: 16, borderWidth: 1, padding: 18,
  },
  heroTitle: { fontSize: 18, fontFamily: F.bold },
  heroSub: { fontSize: 12, fontFamily: F.regular, marginTop: 2 },
  monthLabel: { fontSize: 10, fontFamily: F.bold, letterSpacing: 1.5, marginBottom: 8 },
  monthCard: { borderRadius: 16, borderWidth: 1, overflow: "hidden" },
  dateRow: {
    flexDirection: "row", alignItems: "center", gap: 12,
    padding: 14, borderBottomWidth: 1,
  },
  dateBox: {
    width: 50, height: 56, borderRadius: 12, borderWidth: 1,
    alignItems: "center", justifyContent: "center",
  },
  dateNum: { fontSize: 18, fontFamily: F.bold, lineHeight: 22 },
  dateMon: { fontSize: 10, fontFamily: F.medium },
  dayName: { fontSize: 14, fontFamily: F.semibold },
  avoidBadge: {
    paddingHorizontal: 6, paddingVertical: 2,
    borderRadius: 6, backgroundColor: "rgba(239,68,68,0.12)",
  },
  avoidText: { fontSize: 9, fontFamily: F.bold, color: "#ef4444" },
  timeText: { fontSize: 12, fontFamily: F.medium, marginTop: 2 },
  nakshatraText: { fontSize: 11, fontFamily: F.regular, marginTop: 2 },
  emptyBox: {
    alignItems: "center", gap: 12, padding: 32,
    borderRadius: 16, borderWidth: 1,
  },
  emptyText: { fontSize: 13, fontFamily: F.regular, textAlign: "center", lineHeight: 20 },
  noteBox: {
    flexDirection: "row", gap: 8, alignItems: "flex-start",
    padding: 12, borderRadius: 12, borderWidth: 1,
  },
  noteText: { flex: 1, fontSize: 11, fontFamily: F.regular, lineHeight: 17 },
});
