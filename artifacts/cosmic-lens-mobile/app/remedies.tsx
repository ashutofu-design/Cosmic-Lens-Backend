import { Feather } from "@expo/vector-icons";
import * as Haptics from "expo-haptics";
import { router } from "expo-router";
import React, { useState } from "react";
import { Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { CosmicBg } from "@/components/CosmicBg";
import { useC } from "@/context/ThemeContext";
import { useT } from "@/hooks/useT";

const F = {
  bold: "Nunito_700Bold", semibold: "Nunito_600SemiBold",
  medium: "Nunito_500Medium", regular: "Nunito_400Regular",
};

const PLANETS = [
  {
    id: "surya", name: "Surya", hi: "सूर्य", emoji: "☀️", day: "Ravivaar", color: "#f59e0b",
    gemstone: "Manikya (Ruby)", gemstoneColor: "#ef4444",
    daan: "Gehu, Gur, Tambe ka bartan, Lal kapda",
    mantra: "ॐ ह्रां ह्रीं ह्रौं सः सूर्याय नमः",
    mantraCount: "108 baar Ravivaar ke din",
    upay: [
      "Har Ravivaar suryoday ke samay Surya ko arghya den",
      "Lal rang ke kapde Ravivaar ko pahnen",
      "Gehu aur gur ka daan Brahmin ko karein",
      "Surya yantra sthaapit karein",
    ],
    weak_signs: ["Shani weak — career rukavat", "Pitta rog — aankhen, pet"],
    deity: "Surya Bhagwan", deity_emoji: "☀️",
  },
  {
    id: "chandra", name: "Chandra", hi: "चंद्र", emoji: "🌙", day: "Somvar", color: "#94a3b8",
    gemstone: "Moti (Pearl)", gemstoneColor: "#e2e8f0",
    daan: "Chawal, Dudh, Chandi ka bartan, Safed kapda",
    mantra: "ॐ श्रां श्रीं श्रौं सः चंद्रमसे नमः",
    mantraCount: "11 baar ya 108 baar Somvar ko",
    upay: [
      "Chandra darshan karein Purnima ko",
      "Somvar ko Shiva puja karein",
      "Dudh aur chawal ka daan karein",
      "Safed rang ke kapde Somvar ko pahnen",
    ],
    weak_signs: ["Man ki shanti mein kami", "Neend ki takleef", "Mata se takraav"],
    deity: "Shiv-Parvati", deity_emoji: "🔱",
  },
  {
    id: "mangal", name: "Mangal", hi: "मंगल", emoji: "♂️", day: "Mangalvar", color: "#ef4444",
    gemstone: "Moonga (Red Coral)", gemstoneColor: "#f87171",
    daan: "Masoor dal, Lal kapda, Tambe ka bartan, Kheer",
    mantra: "ॐ क्रां क्रीं क्रौं सः भौमाय नमः",
    mantraCount: "108 baar Mangalvar ke din subah",
    upay: [
      "Hanuman chalisa Mangalvar ko path karein",
      "Lal rang ke kapde Mangalvar ko pahnen",
      "Masoor dal ka daan karein",
      "Mangal yantra sthaapit karein",
    ],
    weak_signs: ["Mangal dosh — vivah mein baadha", "Rakt vikar — khoon ki problem"],
    deity: "Hanuman ji", deity_emoji: "🐒",
  },
  {
    id: "budha", name: "Budha", hi: "बुध", emoji: "☿️", day: "Budhavar", color: "#10b981",
    gemstone: "Panna (Emerald)", gemstoneColor: "#34d399",
    daan: "Moong dal, Hari sabzi, Kaansa bartan, Hari kitaaben",
    mantra: "ॐ ब्रां ब्रीं ब्रौं सः बुधाय नमः",
    mantraCount: "108 baar Budhavar ke din",
    upay: [
      "Budh yantra Budhavar ko sthapit karein",
      "Hari mung dal Budhavar ko khayein",
      "Vishnu sahastranaam path karein",
      "Budh graha shanti puja karwayen",
    ],
    weak_signs: ["Vani dosha — bolne mein diqqat", "Buddhi ka kum upyog", "Vyapar mein haani"],
    deity: "Shri Vishnu", deity_emoji: "🪷",
  },
  {
    id: "guru", name: "Guru (Jupiter)", hi: "गुरु", emoji: "🪐", day: "Guruvaar", color: "#facc15",
    gemstone: "Pukhraj (Yellow Sapphire)", gemstoneColor: "#fde047",
    daan: "Chane ki dal, Peela kapda, Sona, Haldi",
    mantra: "ॐ ग्रां ग्रीं ग्रौं सः गुरवे नमः",
    mantraCount: "19000 baar ya 108 baar Guruvaar ko",
    upay: [
      "Brahmin ko chane ki dal daan karein Guruvaar ko",
      "Peela kapda Guruvaar ko pahnen",
      "Guru Yantra sthaapit karein",
      "Vishnu puja aur Guru stotra path karein",
    ],
    weak_signs: ["Santaan sukh mein kami", "Dharm ke prati aastha ghati", "Vivah mein deri"],
    deity: "Shri Vishnu / Brihaspati", deity_emoji: "🌟",
  },
  {
    id: "shukra", name: "Shukra", hi: "शुक्र", emoji: "♀️", day: "Shukravar", color: "#f43f5e",
    gemstone: "Heera (Diamond)", gemstoneColor: "#e2e8f0",
    daan: "Safed kapda, Chini, Ghee, Safed phool",
    mantra: "ॐ द्रां द्रीं द्रौं सः शुक्राय नमः",
    mantraCount: "108 baar Shukravar ke din",
    upay: [
      "Shukravar ko Lakshmi puja karein",
      "Safed rang ke kapde pahnen",
      "Gaay ko chara dein",
      "Durgasaptashati path karein",
    ],
    weak_signs: ["Prem jeevan mein takleef", "Saundaryabodh ki kami", "Vahaan-vastu sukh mein rukawat"],
    deity: "Maa Lakshmi", deity_emoji: "🌸",
  },
  {
    id: "shani", name: "Shani", hi: "शनि", emoji: "⚖️", day: "Shanivaar", color: "#8b5cf6",
    gemstone: "Neelam (Blue Sapphire)", gemstoneColor: "#60a5fa",
    daan: "Kala til, Sarson tel, Kaala kapda, Loha",
    mantra: "ॐ प्रां प्रीं प्रौं सः शनये नमः",
    mantraCount: "108 baar Shanivaar ke din, Hanuman Chalisa bhi",
    upay: [
      "Shanivaar ko Shani dev ki puja karein",
      "Kaale til ka daan karein",
      "Pippal ke ped ko Shanivaar ko jal chadhayein",
      "Hanuman ji ki aradhana karein",
    ],
    weak_signs: ["Shani dhaiya ya saadesaati", "Karya mein rukawat", "Sehat mein giraawat"],
    deity: "Shani Dev / Hanuman", deity_emoji: "⚖️",
  },
  {
    id: "rahu", name: "Rahu", hi: "राहु", emoji: "🌑", day: "Shanivaar", color: "#6366f1",
    gemstone: "Hessonite (Gomed)", gemstoneColor: "#fbbf24",
    daan: "Nariyal, Kaala kapda, Sarson, Muli",
    mantra: "ॐ भ्रां भ्रीं भ्रौं सः राहवे नमः",
    mantraCount: "18000 baar ya 108 baar Shanivaar ko",
    upay: [
      "Rahu shanti puja karwayen",
      "Durga puja aur Saraswati ki aradhana karein",
      "Kaala kapda Shanivaar ko daan karein",
      "Bhojan Brahmin ko karwayen",
    ],
    weak_signs: ["Rog aur manorog", "Dushman badhna", "Career mein achanak giraaavat"],
    deity: "Maa Durga", deity_emoji: "🗡️",
  },
  {
    id: "ketu", name: "Ketu", hi: "केतु", emoji: "🌠", day: "Mangalvar", color: "#fb923c",
    gemstone: "Cat's Eye (Lahsuniya)", gemstoneColor: "#d9f99d",
    daan: "Chokh kapda, Bila til, Kutte ko roti, Kaala kambal",
    mantra: "ॐ स्त्रां स्त्रीं स्त्रौं सः केतवे नमः",
    mantraCount: "7000 baar ya 108 baar Mangalvar ko",
    upay: [
      "Ketu shanti puja karwayen",
      "Kutte ko roz roti dein",
      "Ganesha aradhana karein",
      "Ketu yantra sthaapit karein",
    ],
    weak_signs: ["Rahasya rog", "Spiritual pareshani", "Accident ka darr"],
    deity: "Shri Ganesh", deity_emoji: "🐘",
  },
];

export default function RemediesScreen() {
  const C = useC();
  const t = useT();
  const insets = useSafeAreaInsets();
  const [selected, setSelected] = useState<string>("surya");
  const planet = PLANETS.find(p => p.id === selected)!;

  return (
    <View style={{ flex: 1 }}>
      <CosmicBg />
      <View style={[s.topBar, { paddingTop: insets.top + 10 }]}>
        <Pressable onPress={() => router.back()} style={s.backBtn}>
          <Feather name="arrow-left" size={20} color={C.text} />
        </Pressable>
        <View>
          <Text style={[s.title, { color: C.text }]}>{t.remediesTitle}</Text>
          <Text style={[s.sub, { color: C.textMuted }]}>Mantra, Daan aur Remedies</Text>
        </View>
        <View style={{ width: 36 }} />
      </View>

      {/* Planet pills */}
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        style={{ flexGrow: 0 }}
        contentContainerStyle={{ paddingHorizontal: 16, gap: 8, paddingBottom: 14 }}
      >
        {PLANETS.map(p => (
          <Pressable
            key={p.id}
            onPress={() => { Haptics.selectionAsync(); setSelected(p.id); }}
            style={[
              s.pill,
              { backgroundColor: C.bgCard, borderColor: C.border },
              selected === p.id && { backgroundColor: `${p.color}18`, borderColor: `${p.color}60` },
            ]}
          >
            <Text style={{ fontSize: 16 }}>{p.emoji}</Text>
            <Text style={[s.pillText, { color: selected === p.id ? p.color : C.textMuted }]}>{p.hi}</Text>
          </Pressable>
        ))}
      </ScrollView>

      <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={{ paddingHorizontal: 16, paddingBottom: insets.bottom + 100, gap: 14 }}>

        {/* Hero */}
        <View style={[s.hero, { backgroundColor: `${planet.color}10`, borderColor: `${planet.color}30` }]}>
          <Text style={{ fontSize: 40 }}>{planet.emoji}</Text>
          <View>
            <Text style={[s.heroTitle, { color: planet.color }]}>{planet.name}</Text>
            <Text style={[s.heroDev, { color: C.text }]}>{planet.deity_emoji} {planet.deity}</Text>
            <Text style={[s.heroDay, { color: C.textMuted }]}>Puja ka din: {planet.day}</Text>
          </View>
        </View>

        {/* Gemstone */}
        <View style={[s.card, { backgroundColor: C.bgCard, borderColor: C.border }]}>
          <Text style={[s.cardTitle, { color: C.textMuted }]}>💎 RATAN (GEMSTONE)</Text>
          <View style={{ flexDirection: "row", alignItems: "center", gap: 12 }}>
            <View style={[s.gemCircle, { backgroundColor: `${planet.gemstoneColor}20`, borderColor: `${planet.gemstoneColor}50` }]}>
              <Text style={{ fontSize: 24 }}>💎</Text>
            </View>
            <View>
              <Text style={[s.gemName, { color: C.text }]}>{planet.gemstone}</Text>
              <Text style={[s.gemTip, { color: C.textMuted }]}>Sone ya Chandi mein, shubh muhurat mein dharan karein</Text>
            </View>
          </View>
        </View>

        {/* Mantra */}
        <View style={[s.card, { backgroundColor: C.bgCard, borderColor: C.border }]}>
          <Text style={[s.cardTitle, { color: C.textMuted }]}>🔔 GRAHA MANTRA</Text>
          <View style={[s.mantraBox, { backgroundColor: `${planet.color}08`, borderColor: `${planet.color}25` }]}>
            <Text style={[s.mantraText, { color: planet.color }]}>{planet.mantra}</Text>
          </View>
          <View style={{ flexDirection: "row", alignItems: "center", gap: 6 }}>
            <Feather name="repeat" size={12} color={C.textDim} />
            <Text style={[s.mantraCount, { color: C.textMuted }]}>{planet.mantraCount}</Text>
          </View>
        </View>

        {/* Daan */}
        <View style={[s.card, { backgroundColor: C.bgCard, borderColor: C.border }]}>
          <Text style={[s.cardTitle, { color: C.textMuted }]}>🤲 DAAN (CHARITY)</Text>
          <Text style={[s.daanText, { color: C.textMid }]}>{planet.daan}</Text>
          <View style={[s.tipBox, { backgroundColor: C.bgCard2, borderColor: C.border }]}>
            <Feather name="info" size={12} color={C.textDim} />
            <Text style={[s.tipText, { color: C.textMuted }]}>{planet.day} ko ya grahan ke samay daan karna vishesh phal deta hai</Text>
          </View>
        </View>

        {/* Upay */}
        <View style={[s.card, { backgroundColor: C.bgCard, borderColor: C.border }]}>
          <Text style={[s.cardTitle, { color: C.textMuted }]}>⚡ UPAY (REMEDIES)</Text>
          {planet.upay.map((u, i) => (
            <View key={i} style={s.upayRow}>
              <View style={[s.upayDot, { backgroundColor: planet.color }]} />
              <Text style={[s.upayText, { color: C.textMid }]}>{u}</Text>
            </View>
          ))}
        </View>

        {/* Weak sign symptoms */}
        <View style={[s.card, { backgroundColor: C.bgCard, borderColor: C.border }]}>
          <Text style={[s.cardTitle, { color: C.textMuted }]}>⚠️ WEAK {planet.name.toUpperCase()} KE LAKSHAN</Text>
          {planet.weak_signs.map((w, i) => (
            <View key={i} style={[s.signRow, { borderBottomColor: C.border3 }, i === planet.weak_signs.length - 1 && { borderBottomWidth: 0 }]}>
              <Text style={{ fontSize: 16 }}>🔴</Text>
              <Text style={[s.signText, { color: C.textMid }]}>{w}</Text>
            </View>
          ))}
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
  pill: {
    flexDirection: "row", alignItems: "center", gap: 6,
    paddingHorizontal: 12, paddingVertical: 8,
    borderRadius: 20, borderWidth: 1,
  },
  pillText: { fontSize: 12, fontFamily: F.semibold },
  hero: {
    flexDirection: "row", alignItems: "center", gap: 16,
    borderRadius: 16, borderWidth: 1, padding: 18,
  },
  heroTitle: { fontSize: 20, fontFamily: F.bold },
  heroDev: { fontSize: 13, fontFamily: F.medium, marginTop: 2 },
  heroDay: { fontSize: 11, fontFamily: F.regular, marginTop: 2 },
  card: { borderRadius: 16, borderWidth: 1, padding: 16, gap: 10 },
  cardTitle: { fontSize: 10, fontFamily: F.bold, letterSpacing: 1.5 },
  gemCircle: {
    width: 52, height: 52, borderRadius: 26,
    alignItems: "center", justifyContent: "center", borderWidth: 1.5,
  },
  gemName: { fontSize: 16, fontFamily: F.bold },
  gemTip: { fontSize: 11, fontFamily: F.regular, marginTop: 2 },
  mantraBox: {
    padding: 14, borderRadius: 12, borderWidth: 1,
  },
  mantraText: { fontSize: 15, fontFamily: F.semibold, textAlign: "center", lineHeight: 26 },
  mantraCount: { fontSize: 11, fontFamily: F.regular },
  daanText: { fontSize: 13, fontFamily: F.regular, lineHeight: 21 },
  tipBox: {
    flexDirection: "row", gap: 6, alignItems: "flex-start",
    padding: 10, borderRadius: 10, borderWidth: 1,
  },
  tipText: { flex: 1, fontSize: 11, fontFamily: F.regular, lineHeight: 17 },
  upayRow: { flexDirection: "row", alignItems: "flex-start", gap: 10 },
  upayDot: { width: 7, height: 7, borderRadius: 3.5, marginTop: 6 },
  upayText: { flex: 1, fontSize: 12, fontFamily: F.regular, lineHeight: 20 },
  signRow: {
    flexDirection: "row", alignItems: "center", gap: 10,
    paddingVertical: 9, borderBottomWidth: 1,
  },
  signText: { flex: 1, fontSize: 12, fontFamily: F.regular },
});
