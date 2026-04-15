import { Feather } from "@expo/vector-icons";
import * as Haptics from "expo-haptics";
import { router, useLocalSearchParams } from "expo-router";
import React, { useState } from "react";
import {
  Pressable, ScrollView, StyleSheet, Text, View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import CosmicBg from "@/components/CosmicBg";
import { useC } from "@/context/ThemeContext";
import { useUser } from "@/context/UserContext";

const F = {
  bold: "Nunito_700Bold",
  semibold: "Nunito_600SemiBold",
  medium: "Nunito_500Medium",
  regular: "Nunito_400Regular",
};

const RASHIS = [
  { id: "mesh",       name: "मेष",       en: "Aries",       emoji: "♈", lord: "मंगल", color: "#ef4444", dates: "Mar 21–Apr 19" },
  { id: "vrishabh",   name: "वृषभ",      en: "Taurus",      emoji: "♉", lord: "शुक्र", color: "#10b981", dates: "Apr 20–May 20" },
  { id: "mithun",     name: "मिथुन",     en: "Gemini",      emoji: "♊", lord: "बुध",   color: "#facc15", dates: "May 21–Jun 20" },
  { id: "kark",       name: "कर्क",      en: "Cancer",      emoji: "♋", lord: "चंद्र", color: "#94a3b8", dates: "Jun 21–Jul 22" },
  { id: "simha",      name: "सिंह",      en: "Leo",         emoji: "♌", lord: "सूर्य", color: "#f59e0b", dates: "Jul 23–Aug 22" },
  { id: "kanya",      name: "कन्या",     en: "Virgo",       emoji: "♍", lord: "बुध",   color: "#22c55e", dates: "Aug 23–Sep 22" },
  { id: "tula",       name: "तुला",      en: "Libra",       emoji: "♎", lord: "शुक्र", color: "#60a5fa", dates: "Sep 23–Oct 22" },
  { id: "vrishchik",  name: "वृश्चिक",  en: "Scorpio",     emoji: "♏", lord: "मंगल", color: "#f43f5e", dates: "Oct 23–Nov 21" },
  { id: "dhanu",      name: "धनु",       en: "Sagittarius", emoji: "♐", lord: "गुरु",  color: "#fb923c", dates: "Nov 22–Dec 21" },
  { id: "makar",      name: "मकर",       en: "Capricorn",   emoji: "♑", lord: "शनि",   color: "#8b5cf6", dates: "Dec 22–Jan 19" },
  { id: "kumbh",      name: "कुम्भ",     en: "Aquarius",    emoji: "♒", lord: "शनि",   color: "#06b6d4", dates: "Jan 20–Feb 18" },
  { id: "meen",       name: "मीन",       en: "Pisces",      emoji: "♓", lord: "गुरु",  color: "#a78bfa", dates: "Feb 19–Mar 20" },
];

const PHAL: Record<string, { aaj: string; hafta: string; lucky: string; savdhan: string }> = {
  mesh:      { aaj: "Aaj ka din aapke liye shandar rahega. Vyavsay mein nayi safaltaen milne ki sambhavana hai. Parivar ke saath samay bitaayen. Shaam ko koi khushkhabri mil sakti hai.", hafta: "Is hafte aapki mehnat rang laegi. Karyakshetra mein tarakki ke yog hain. Premi-premika ke beech suhana samay rahega. Swasthya dhyan rakhein.", lucky: "Lal rang, Mangalvar, Ank 9", savdhan: "Gusse par niyantran rakhein." },
  vrishabh:  { aaj: "Aarthik sthiti majboot hogi. Kisi purane dost se mulaqat ho sakti hai. Grihasth jeevan mein sukh ka vaas rahega. Nayi yojana banana auspicious hai.", hafta: "Dhan laabh ke achhe yog hain. Parivar mein koi mangal karya hone ki sambhavana. Swasthya uttar mein rahega. Sher ke saath baat sambhal kar karein.", lucky: "Safed rang, Shukravar, Ank 6", savdhan: "Kharche par nazar rakhein." },
  mithun:    { aaj: "Buddhi aur vivek se kaam lein. Kisi naye prastaav ko sochsamajh kar sweekar karein. Mitron ka saath milega. Sair-sapate ka yog banta hai.", hafta: "Videsh yatra ya door ka safar ho sakta hai. Naye log milenge jo upyogi sabit honge. Maan-samman mein vriddhi hogi. Sanchar ke kshetra mein avsar.", lucky: "Peela rang, Budhavar, Ank 5", savdhan: "Zyada bolne se bachein." },
  kark:      { aaj: "Bhaavnaatmak din hai aaj. Ghar-parivar ke mamle sulajhenge. Mata ki sehat ka dhyan rakhein. Kisi pooje ya dharmik kaarya mein bhaagidaari hogi.", hafta: "Ghar mein sukh-shanti ka vaas hoga. Vyavsay mein sthirta rahegi. Santan ki khushkhabri mil sakti hai. Aarthik sthiti sudhregr", lucky: "Safed/Peela rang, Somvar, Ank 2", savdhan: "Maan ke vahem se door rahein." },
  simha:     { aaj: "Aaj aap kendra mein rahenge. Netatv ke kaarya mein safalta milegi. Logo ka dhyan aap par rahega. Samman aur pratishtha mein vriddhi hogi.", hafta: "Rajkiya kaaryon mein safalta milegi. Prem prasang mein nayi udaan aayegi. Vyavsay mein bade faisle le sakte hain. Swasthya achha rahega.", lucky: "Sona/Narangi rang, Ravivaar, Ank 1", savdhan: "Ahankar se bachein." },
  kanya:     { aaj: "Hisaab-kitaab ke mamle theek honge. Lekhak ya shikshak hain toh acha din hai. Choti-choti baaton par dhyan dena avashyak hai. Kaam mein perfection aayegi.", hafta: "Vyavsay mein methodical kaam aage badhega. Sehat ke prati satark rahein. Naye sambandh bante hain. Kisi document ya kaagaz ka kaam poora hoga.", lucky: "Hari rang, Budhavar, Ank 5", savdhan: "Zyada criticism se bachein." },
  tula:      { aaj: "Rishton mein meethas aayegi. Kisi bade faisle lene ka achi din hai. Kala aur sundar cheezen aapko akarshit karengi. Koi meetha tohfa milne ki sambhavana.", hafta: "Partnership mein fayda hoga. Prem jeevan mein romance ka vaas. Legal mamle sulajhenge. Sampatti ke mamle mein koi achhi khabar.", lucky: "Neela rang, Shukravar, Ank 6", savdhan: "Nirnay lene mein der na karein." },
  vrishchik: { aaj: "Guptata aur research ka cha din. Kisi gehri baat ki parat kholne ka samay. Transformation ke yog hain. Apni shakti ko pehchanen.", hafta: "Virasat ya joint money mein laabh ho sakta hai. Shodh ya anveshan mein safalta. Prem prasang mein gaharai aayegi. Health checkup faydemand.", lucky: "Lal/Maroon rang, Mangalvar, Ank 9", savdhan: "Shak aur ईर्ष्या से bachein." },
  dhanu:     { aaj: "Uttejana se bhara din hai. Dharmik yatra ya mandir darshan ka yog. Uchch shiksha mein safalta milegi. Door ke log yaad aayenge ya milenge.", hafta: "Videsh sambandhi kaar karya poore honge. Guru ki kripa bani rahegi. Vyavsay mein nayi dishaayen khulengi. Sampatti laabh ke yog.", lucky: "Peela rang, Guruvaar, Ank 3", savdhan: "Zyada optimistic na rahen bina sochhe." },
  makar:     { aaj: "Karya aur anushasan ka din. Mehnat se mili safalta aaj phal degi. Uchchadhikari aapka kaam recognize karenge. Zimmedaari nibhaane ka samay.", hafta: "Karya sthaan par unnati ke yog. Samajik pratishtha badhegi. Pita ya bujurgon ka ashirvaad milega. Aarthik niyojan safal hoga.", lucky: "Neela/Kaala rang, Shanivaar, Ank 8", savdhan: "Zyada kaam se sehat na bigadein." },
  kumbh:     { aaj: "Naye vichar aur innovation ka din. Dosto ka saath milega. Samaj seva mein man lagega. Kisi apratyashit laabh ka yog.", hafta: "Technical aur scientific kaam aage badhega. Naye mitron se naye avsar. Puratan sambandh toot sakte ya bane bhi rahe. Swatantra nirnay lene ka samay.", lucky: "Aasmani neela rang, Shanivaar, Ank 4", savdhan: "Abruptness se bachein." },
  meen:      { aaj: "Bhakti aur spirituality ka din. Sapne sach ho sakte hain. Kala aur sangeet mein man lagega. Kisi roohaani anubhav ka yog.", hafta: "Aatmik unnati hogi. Dharmarth kaaryon mein bhaagidaari. Kalpana ko haaqikat mein badlne ka waqt. Swasthya ka dhyan rakhein.", lucky: "Peela/Sea Green rang, Guruvaar, Ank 3", savdhan: "Dhokhebaaz logon se sachait rahein." },
};

const TABS = ["Aaj", "Is Hafta", "Is Mahine"];

export default function RashifalScreen() {
  const C = useC();
  const insets = useSafeAreaInsets();
  const params = useLocalSearchParams<{ tab?: string }>();
  const [tabIdx, setTabIdx] = useState(params.tab === "weekly" ? 1 : 0);
  const [expanded, setExpanded] = useState<string | null>(null);
  const { profiles } = useUser();
  const userRashi = profiles[0]?.rashi ?? null;

  return (
    <View style={{ flex: 1 }}>
      <CosmicBg />
      <View style={[s.topBar, { paddingTop: insets.top + 10 }]}>
        <Pressable onPress={() => router.back()} style={s.backBtn}>
          <Feather name="arrow-left" size={20} color={C.text} />
        </Pressable>
        <View>
          <Text style={[s.title, { color: C.text }]}>Rashifal</Text>
          <Text style={[s.subtitle, { color: C.textMuted }]}>Aapka rashifal aaj</Text>
        </View>
        <View style={{ width: 36 }} />
      </View>

      {/* Tab pills */}
      <View style={s.tabRow}>
        {TABS.map((tab, i) => (
          <Pressable
            key={tab}
            onPress={() => { Haptics.selectionAsync(); setTabIdx(i); }}
            style={[
              s.tabPill,
              { borderColor: C.border },
              tabIdx === i && { backgroundColor: "#f59e0b", borderColor: "#f59e0b" },
            ]}
          >
            <Text style={[s.tabText, { color: tabIdx === i ? "#fff" : C.textMuted }]}>{tab}</Text>
          </Pressable>
        ))}
      </View>

      <ScrollView
        showsVerticalScrollIndicator={false}
        contentContainerStyle={{ paddingHorizontal: 16, paddingBottom: insets.bottom + 100, gap: 12 }}
      >
        {RASHIS.map(rashi => {
          const phal = PHAL[rashi.id];
          const isMe = userRashi === rashi.id;
          const isOpen = expanded === rashi.id;
          const text = tabIdx === 0 ? phal.aaj : phal.hafta;

          return (
            <Pressable
              key={rashi.id}
              onPress={() => {
                Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
                setExpanded(isOpen ? null : rashi.id);
              }}
              style={[
                s.rashiCard,
                {
                  backgroundColor: C.bgCard,
                  borderColor: isMe ? `${rashi.color}60` : C.border,
                  borderWidth: isMe ? 1.5 : 1,
                },
              ]}
            >
              <View style={s.rashiRow}>
                <View style={[s.rashiEmoji, { backgroundColor: `${rashi.color}18` }]}>
                  <Text style={{ fontSize: 22 }}>{rashi.emoji}</Text>
                </View>
                <View style={{ flex: 1 }}>
                  <View style={{ flexDirection: "row", alignItems: "center", gap: 6 }}>
                    <Text style={[s.rashiName, { color: C.text }]}>{rashi.name}</Text>
                    <Text style={[s.rashiEn, { color: C.textDim }]}>{rashi.en}</Text>
                    {isMe && (
                      <View style={[s.meBadge, { backgroundColor: `${rashi.color}20`, borderColor: `${rashi.color}40` }]}>
                        <Text style={[s.meBadgeText, { color: rashi.color }]}>Aapki Rashi</Text>
                      </View>
                    )}
                  </View>
                  <Text style={[s.rashiLord, { color: C.textMuted }]}>Swami: {rashi.lord} · {rashi.dates}</Text>
                </View>
                <Feather name={isOpen ? "chevron-up" : "chevron-down"} size={16} color={C.textDim} />
              </View>

              {isOpen && (
                <View style={{ marginTop: 12, gap: 10 }}>
                  <View style={[s.divider, { backgroundColor: C.border3 }]} />
                  <Text style={[s.phalText, { color: C.textMid }]}>{text}</Text>
                  <View style={s.luckRow}>
                    <View style={[s.luckChip, { backgroundColor: C.bgCard2, borderColor: C.border }]}>
                      <Text style={{ fontSize: 12 }}>🍀</Text>
                      <Text style={[s.luckText, { color: C.textMuted }]}>{phal.lucky}</Text>
                    </View>
                  </View>
                  <View style={[s.savdhanBox, { backgroundColor: "rgba(239,68,68,0.06)", borderColor: "rgba(239,68,68,0.2)" }]}>
                    <Feather name="alert-triangle" size={12} color="#ef4444" />
                    <Text style={[s.savdhanText, { color: "#ef4444" }]}>Savdhan: {phal.savdhan}</Text>
                  </View>
                </View>
              )}
            </Pressable>
          );
        })}
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
  subtitle: { fontSize: 12, fontFamily: F.regular, marginTop: 1 },
  tabRow: {
    flexDirection: "row", gap: 8, paddingHorizontal: 16, marginBottom: 14,
  },
  tabPill: {
    paddingHorizontal: 16, paddingVertical: 7, borderRadius: 20,
    borderWidth: 1,
  },
  tabText: { fontSize: 12, fontFamily: F.semibold },
  rashiCard: {
    borderRadius: 14, borderWidth: 1, padding: 14,
  },
  rashiRow: { flexDirection: "row", alignItems: "center", gap: 12 },
  rashiEmoji: {
    width: 46, height: 46, borderRadius: 14,
    alignItems: "center", justifyContent: "center",
  },
  rashiName: { fontSize: 15, fontFamily: F.bold },
  rashiEn: { fontSize: 12, fontFamily: F.medium },
  rashiLord: { fontSize: 11, fontFamily: F.regular, marginTop: 2 },
  meBadge: {
    paddingHorizontal: 6, paddingVertical: 2,
    borderRadius: 8, borderWidth: 1,
  },
  meBadgeText: { fontSize: 9, fontFamily: F.bold },
  divider: { height: 1 },
  phalText: { fontSize: 13.5, fontFamily: F.regular, lineHeight: 21 },
  luckRow: { flexDirection: "row" },
  luckChip: {
    flexDirection: "row", alignItems: "center", gap: 6,
    paddingHorizontal: 10, paddingVertical: 6,
    borderRadius: 10, borderWidth: 1,
  },
  luckText: { fontSize: 11, fontFamily: F.medium },
  savdhanBox: {
    flexDirection: "row", alignItems: "center", gap: 6,
    paddingHorizontal: 10, paddingVertical: 7,
    borderRadius: 10, borderWidth: 1,
  },
  savdhanText: { fontSize: 11, fontFamily: F.medium, flex: 1 },
});
