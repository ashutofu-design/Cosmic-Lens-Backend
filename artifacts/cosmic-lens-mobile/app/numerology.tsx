import { Feather } from "@expo/vector-icons";
import * as Haptics from "expo-haptics";
import { router } from "expo-router";
import React, { useState, useMemo } from "react";
import {
  Pressable, ScrollView, StyleSheet, Text,
  TextInput, View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import CosmicBg from "@/components/CosmicBg";
import { useC } from "@/context/ThemeContext";

const F = {
  bold: "Nunito_700Bold", semibold: "Nunito_600SemiBold",
  medium: "Nunito_500Medium", regular: "Nunito_400Regular",
};

function reduceToSingle(n: number): number {
  while (n > 9 && n !== 11 && n !== 22 && n !== 33) {
    n = String(n).split("").reduce((a, b) => a + parseInt(b), 0);
  }
  return n;
}

function calcLifePath(dob: string): number | null {
  const parts = dob.split("/");
  if (parts.length !== 3) return null;
  const [d, m, y] = parts.map(Number);
  if (!d || !m || !y || y < 1900) return null;
  const sum = String(d).split("").reduce((a,b)=>a+parseInt(b),0)
            + String(m).split("").reduce((a,b)=>a+parseInt(b),0)
            + String(y).split("").reduce((a,b)=>a+parseInt(b),0);
  return reduceToSingle(sum);
}

// Name number (Chaldean system)
const CHALDEAN: Record<string, number> = {
  a:1,b:2,c:3,d:4,e:5,f:8,g:3,h:5,i:1,j:1,k:2,l:3,m:4,
  n:5,o:7,p:8,q:1,r:2,s:3,t:4,u:6,v:6,w:6,x:5,y:1,z:7,
};

function calcNameNumber(name: string): number | null {
  const cleaned = name.toLowerCase().replace(/[^a-z]/g, "");
  if (!cleaned) return null;
  const sum = cleaned.split("").reduce((a, c) => a + (CHALDEAN[c] ?? 0), 0);
  return reduceToSingle(sum);
}

const NUMBER_INFO: Record<number, {
  title: string; planet: string; planetEmoji: string;
  traits: string[]; career: string; love: string; color: string; lucky: string;
}> = {
  1: { title: "Netritva", planet: "Surya", planetEmoji: "☀️", color: "#f59e0b", lucky: "1, 10, 19, 28",
       traits: ["Aatmvishwaas","Netritva","Swatantrata","Mahattvakaanksha"],
       career: "Rajneeti, Prabandhan, Udyamita, Netatva ke kaarya",
       love: "Aap dominanat partner hain. Khud ko vyakt karne wale partner se premi hain." },
  2: { title: "Sahyog", planet: "Chandra", planetEmoji: "🌙", color: "#94a3b8", lucky: "2, 11, 20, 29",
       traits: ["Sahvedna","Sahyog","Santulana","Kalpana"],
       career: "Kala, Sangeet, Counseling, Karyalaya kaarya",
       love: "Aap bahut romantic aur caring partner hain. Rishton mein harmoni chahte hain." },
  3: { title: "Srijanatmakta", planet: "Guru", planetEmoji: "🪐", color: "#facc15", lucky: "3, 12, 21, 30",
       traits: ["Srijanatmakta","Utsaah","Samajikta","Optimism"],
       career: "Lekhan, Kala, Entertainment, Shiksha",
       love: "Aap joyful aur fun-loving partner hain. Humor aapki pehchaan hai." },
  4: { title: "Sthirta", planet: "Rahu", planetEmoji: "🌑", color: "#8b5cf6", lucky: "4, 13, 22, 31",
       traits: ["Anushasan","Manat","Vyavastha","Vishwasneeyata"],
       career: "Engineering, Architecture, Sena, Wित्त",
       love: "Aap loyal aur reliable partner hain. Stability aapko chahiye." },
  5: { title: "Swatantrata", planet: "Budha", planetEmoji: "☿️", color: "#10b981", lucky: "5, 14, 23",
       traits: ["Swatantrata","Sahastra","Uchhalana","Buddhimatta"],
       career: "Patrakarita, Yatra, Sales, Technology",
       love: "Aap adventurous partner hain. Boredom se darte hain." },
  6: { title: "Prem", planet: "Shukra", planetEmoji: "♀️", color: "#f43f5e", lucky: "6, 15, 24",
       traits: ["Prem","Uttardayitv","Parivar prem","Saundaryapriyata"],
       career: "Chikitsa, Shiksha, Kala, Grihasth kaarya",
       love: "Aap deeply loving aur devoted partner hain. Parivar sabse pehle." },
  7: { title: "Gyaan", planet: "Ketu", planetEmoji: "🌠", color: "#06b6d4", lucky: "7, 16, 25",
       traits: ["Gyaan","Dhyaan","Rahasya","Aatmaavlochana"],
       career: "Anveshan, Philosophy, Science, Adhyatma",
       love: "Aap intellectual partner hain. Deep conversations chahte hain." },
  8: { title: "Samriddhi", planet: "Shani", planetEmoji: "🪐", color: "#6366f1", lucky: "8, 17, 26",
       traits: ["Samriddhi","Bal","Manat","Vyavasayika saflata"],
       career: "Vyavsay, Banking, Rajneeti, Prashasan",
       love: "Aap intense aur protective partner hain. Power dynamics matter karte hain." },
  9: { title: "Manavta", planet: "Mangal", planetEmoji: "♂️", color: "#ef4444", lucky: "9, 18, 27",
       traits: ["Karuna","Daan","Shaurya","Nishkaam seva"],
       career: "Doctor, Lawyer, Sena, Seva kaarya",
       love: "Aap passionate aur idealistic partner hain. Sach ke liye lade hain." },
  11: { title: "Prakaash", planet: "Chandra+Surya", planetEmoji: "✨", color: "#fbbf24", lucky: "11, 29",
        traits: ["Intuition","Ilham","Aatmik shakti","Prerna"],
        career: "Spiritual guidance, Kala, Healing, Netritva",
        love: "Aap deeply intuitive partner hain. Soulmate dhundhte hain." },
  22: { title: "Vishwa Nirman", planet: "Shani+Surya", planetEmoji: "🌍", color: "#a78bfa", lucky: "22",
        traits: ["Visionary","Sangathan","Badi soch","Nirmana"],
        career: "Architecture, Politics, Global business",
        love: "Aap dedicated aur visionary partner hain. Long-term goals matter karte hain." },
  33: { title: "Vishwa Prem", planet: "Guru+Shukra", planetEmoji: "💫", color: "#34d399", lucky: "33",
        traits: ["Nirswaarth prem","Shiksha","Seva","Upchar"],
        career: "Healing arts, Teaching, Spiritual leadership",
        love: "Aap unconditionally loving partner hain." },
};

export default function NumerologyScreen() {
  const C = useC();
  const insets = useSafeAreaInsets();
  const [dob, setDob] = useState("");
  const [name, setName] = useState("");
  const [calculated, setCalculated] = useState(false);

  const lifePath = useMemo(() => calcLifePath(dob), [dob]);
  const nameNum  = useMemo(() => calcNameNumber(name), [name]);

  function onCalculate() {
    if (!lifePath && !nameNum) return;
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    setCalculated(true);
  }

  const lpInfo  = lifePath ? NUMBER_INFO[lifePath] : null;
  const nnInfo  = nameNum  ? NUMBER_INFO[nameNum]  : null;

  return (
    <View style={{ flex: 1 }}>
      <CosmicBg />
      <View style={[s.topBar, { paddingTop: insets.top + 10 }]}>
        <Pressable onPress={() => router.back()} style={s.backBtn}>
          <Feather name="arrow-left" size={20} color={C.text} />
        </Pressable>
        <View>
          <Text style={[s.title, { color: C.text }]}>Numerology</Text>
          <Text style={[s.sub, { color: C.textMuted }]}>Ankon ka rahasya</Text>
        </View>
        <View style={{ width: 36 }} />
      </View>

      <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={{ paddingHorizontal: 16, paddingBottom: insets.bottom + 100, gap: 14 }}>

        {/* Input form */}
        <View style={[s.card, { backgroundColor: C.bgCard, borderColor: C.border }]}>
          <Text style={[s.cardTitle, { color: C.textMuted }]}>🔢 APNA VIVARAN DARJ KAREIN</Text>

          <View style={{ gap: 4 }}>
            <Text style={[s.label, { color: C.textMuted }]}>Janm Tithi (DD/MM/YYYY)</Text>
            <TextInput
              style={[s.input, { color: C.text, backgroundColor: C.inputBg, borderColor: C.border }]}
              placeholder="15/04/1990"
              placeholderTextColor={C.textDim}
              value={dob}
              onChangeText={setDob}
              keyboardType="numeric"
            />
          </View>

          <View style={{ gap: 4 }}>
            <Text style={[s.label, { color: C.textMuted }]}>Pura Naam (English mein)</Text>
            <TextInput
              style={[s.input, { color: C.text, backgroundColor: C.inputBg, borderColor: C.border }]}
              placeholder="RAHUL SHARMA"
              placeholderTextColor={C.textDim}
              value={name}
              onChangeText={setName}
              autoCapitalize="characters"
            />
          </View>

          <Pressable
            onPress={onCalculate}
            style={({ pressed }) => [s.calcBtn, { opacity: pressed ? 0.8 : 1 }]}
          >
            <Text style={{ fontSize: 20 }}>🔢</Text>
            <Text style={s.calcBtnText}>Calculate Karein</Text>
          </Pressable>
        </View>

        {/* Results */}
        {calculated && (
          <>
            {/* Life Path */}
            {lpInfo && lifePath && (
              <View style={[s.resultCard, { backgroundColor: C.bgCard, borderColor: `${lpInfo.color}40` }]}>
                <View style={{ flexDirection: "row", alignItems: "center", gap: 14, marginBottom: 12 }}>
                  <View style={[s.numBubble, { backgroundColor: `${lpInfo.color}18`, borderColor: `${lpInfo.color}40` }]}>
                    <Text style={[s.numBig, { color: lpInfo.color }]}>{lifePath}</Text>
                  </View>
                  <View>
                    <Text style={[s.resultLabel, { color: C.textDim }]}>LIFE PATH NUMBER</Text>
                    <Text style={[s.resultTitle, { color: C.text }]}>{lpInfo.title}</Text>
                    <Text style={[s.resultPlanet, { color: lpInfo.color }]}>{lpInfo.planetEmoji} {lpInfo.planet}</Text>
                  </View>
                </View>

                <View style={{ flexDirection: "row", flexWrap: "wrap", gap: 6, marginBottom: 12 }}>
                  {lpInfo.traits.map(t => (
                    <View key={t} style={[s.traitChip, { backgroundColor: `${lpInfo.color}14`, borderColor: `${lpInfo.color}30` }]}>
                      <Text style={[s.traitText, { color: lpInfo.color }]}>{t}</Text>
                    </View>
                  ))}
                </View>

                <View style={[s.infoRow, { borderTopColor: C.border3 }]}>
                  <Text style={[s.infoLabel, { color: C.textMuted }]}>💼 Career</Text>
                  <Text style={[s.infoVal, { color: C.textMid }]}>{lpInfo.career}</Text>
                </View>
                <View style={[s.infoRow, { borderTopColor: C.border3 }]}>
                  <Text style={[s.infoLabel, { color: C.textMuted }]}>❤️ Prem Jeevan</Text>
                  <Text style={[s.infoVal, { color: C.textMid }]}>{lpInfo.love}</Text>
                </View>
                <View style={[s.infoRow, { borderTopColor: C.border3 }]}>
                  <Text style={[s.infoLabel, { color: C.textMuted }]}>🍀 Lucky Ankh</Text>
                  <Text style={[s.infoVal, { color: lpInfo.color }]}>{lpInfo.lucky}</Text>
                </View>
              </View>
            )}

            {/* Name Number */}
            {nnInfo && nameNum && (
              <View style={[s.resultCard, { backgroundColor: C.bgCard, borderColor: `${nnInfo.color}40` }]}>
                <View style={{ flexDirection: "row", alignItems: "center", gap: 14, marginBottom: 12 }}>
                  <View style={[s.numBubble, { backgroundColor: `${nnInfo.color}18`, borderColor: `${nnInfo.color}40` }]}>
                    <Text style={[s.numBig, { color: nnInfo.color }]}>{nameNum}</Text>
                  </View>
                  <View>
                    <Text style={[s.resultLabel, { color: C.textDim }]}>NAAM ANKA (NAME NUMBER)</Text>
                    <Text style={[s.resultTitle, { color: C.text }]}>{nnInfo.title}</Text>
                    <Text style={[s.resultPlanet, { color: nnInfo.color }]}>{nnInfo.planetEmoji} {nnInfo.planet}</Text>
                  </View>
                </View>
                <View style={{ flexDirection: "row", flexWrap: "wrap", gap: 6 }}>
                  {nnInfo.traits.map(t => (
                    <View key={t} style={[s.traitChip, { backgroundColor: `${nnInfo.color}14`, borderColor: `${nnInfo.color}30` }]}>
                      <Text style={[s.traitText, { color: nnInfo.color }]}>{t}</Text>
                    </View>
                  ))}
                </View>
              </View>
            )}

            {/* All numbers guide */}
            <Text style={[s.guideLabel, { color: C.textMuted }]}>📚 SABHI ANKHA KA ARTH</Text>
            <View style={[s.card, { backgroundColor: C.bgCard, borderColor: C.border }]}>
              {[1,2,3,4,5,6,7,8,9].map((n, i) => {
                const info = NUMBER_INFO[n];
                return (
                  <View key={n} style={[s.guideRow, { borderBottomColor: C.border3 }, i === 8 && { borderBottomWidth: 0 }]}>
                    <View style={[s.guideNum, { backgroundColor: `${info.color}18`, borderColor: `${info.color}30` }]}>
                      <Text style={[s.guideNumText, { color: info.color }]}>{n}</Text>
                    </View>
                    <View style={{ flex: 1 }}>
                      <Text style={[s.guideName, { color: C.text }]}>{info.title}</Text>
                      <Text style={[s.guidePlanet, { color: C.textMuted }]}>{info.planetEmoji} {info.planet}</Text>
                    </View>
                  </View>
                );
              })}
            </View>
          </>
        )}

        {/* How it works */}
        {!calculated && (
          <View style={[s.card, { backgroundColor: C.bgCard, borderColor: C.border, gap: 10 }]}>
            <Text style={[s.cardTitle, { color: C.textMuted }]}>💡 NUMEROLOGY KYA HAI?</Text>
            <Text style={[s.howText, { color: C.textMid }]}>
              Numerology ankon ke madhyam se vyakti ki shaktiyon, kamzoriyon, aur bhavishy ka adhyayan karta hai.
              Vedic Numerology ke anusaar, har ank ek grah se juda hai jo aapke jeevan ko prabhavit karta hai.
            </Text>
            <View style={s.tipRow}>
              <Text style={{ fontSize: 18 }}>🔢</Text>
              <Text style={[s.tipText, { color: C.textMuted }]}><Text style={{ fontFamily: F.bold }}>Life Path</Text>: Janm tithi ke sabhi ankon ka yog → personality aur jeevan path</Text>
            </View>
            <View style={s.tipRow}>
              <Text style={{ fontSize: 18 }}>🅰️</Text>
              <Text style={[s.tipText, { color: C.textMuted }]}><Text style={{ fontFamily: F.bold }}>Naam Anka</Text>: Naam ke akshar ke ank → vyaktitv aur bhagya</Text>
            </View>
          </View>
        )}
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
  card: { borderRadius: 16, borderWidth: 1, padding: 16, gap: 10 },
  cardTitle: { fontSize: 10, fontFamily: F.bold, letterSpacing: 1.5 },
  label: { fontSize: 11, fontFamily: F.semibold },
  input: {
    borderRadius: 10, borderWidth: 1, paddingHorizontal: 12,
    paddingVertical: 11, fontSize: 14, fontFamily: F.medium,
  },
  calcBtn: {
    flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 8,
    backgroundColor: "#8b5cf6", borderRadius: 14, paddingVertical: 14,
  },
  calcBtnText: { color: "#fff", fontSize: 15, fontFamily: F.bold },
  resultCard: { borderRadius: 16, borderWidth: 1.5, padding: 16 },
  numBubble: {
    width: 72, height: 72, borderRadius: 36,
    alignItems: "center", justifyContent: "center", borderWidth: 2,
  },
  numBig: { fontSize: 30, fontFamily: F.bold },
  resultLabel: { fontSize: 9, fontFamily: F.bold, letterSpacing: 1.5 },
  resultTitle: { fontSize: 16, fontFamily: F.bold, marginTop: 2 },
  resultPlanet: { fontSize: 12, fontFamily: F.medium, marginTop: 1 },
  traitChip: {
    paddingHorizontal: 10, paddingVertical: 5,
    borderRadius: 10, borderWidth: 1,
  },
  traitText: { fontSize: 11, fontFamily: F.semibold },
  infoRow: { paddingTop: 10, borderTopWidth: 1, gap: 3 },
  infoLabel: { fontSize: 10, fontFamily: F.bold, letterSpacing: 0.8 },
  infoVal: { fontSize: 12, fontFamily: F.regular, lineHeight: 18 },
  guideLabel: { fontSize: 10, fontFamily: F.bold, letterSpacing: 1.5 },
  guideRow: {
    flexDirection: "row", alignItems: "center", gap: 12,
    paddingVertical: 10, borderBottomWidth: 1,
  },
  guideNum: {
    width: 36, height: 36, borderRadius: 12,
    alignItems: "center", justifyContent: "center", borderWidth: 1,
  },
  guideNumText: { fontSize: 16, fontFamily: F.bold },
  guideName: { fontSize: 13, fontFamily: F.semibold },
  guidePlanet: { fontSize: 10, fontFamily: F.regular, marginTop: 1 },
  howText: { fontSize: 13, fontFamily: F.regular, lineHeight: 21 },
  tipRow: { flexDirection: "row", alignItems: "flex-start", gap: 8 },
  tipText: { flex: 1, fontSize: 12, fontFamily: F.regular, lineHeight: 19 },
});
