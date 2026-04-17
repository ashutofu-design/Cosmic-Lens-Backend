import { Feather } from "@expo/vector-icons";
import { router } from "expo-router";
import React, { useMemo } from "react";
import { ScrollView, StyleSheet, Text, View, Pressable } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import CosmicBg from "@/components/CosmicBg";
import { useC } from "@/context/ThemeContext";
import { useUser } from "@/context/UserContext";
import { useT } from "@/hooks/useT";

const F = {
  bold: "Nunito_700Bold", semibold: "Nunito_600SemiBold",
  medium: "Nunito_500Medium", regular: "Nunito_400Regular",
};

type RashiKey = "mesh"|"vrishabh"|"mithun"|"kark"|"simha"|"kanya"|"tula"|"vrishchik"|"dhanu"|"makar"|"kumbh"|"meen";

const LUCKY: Record<RashiKey, {
  colors: {name:string;hex:string}[];
  numbers: number[];
  days: string[];
  gemstone: string; gemstoneHi: string;
  direction: string; directionEmoji: string;
  metal: string;
  deity: string;
  mantra: string;
  element: string; elementEmoji: string;
}> = {
  mesh:      { colors:[{name:"Laal",hex:"#ef4444"},{name:"Narangi",hex:"#fb923c"}], numbers:[1,9], days:["Mangalvar","Ravivaar"], gemstone:"Coral",     gemstoneHi:"Moonga",   direction:"Uttar",   directionEmoji:"⬆️", metal:"Tamba",  deity:"Hanuman",    mantra:"ॐ क्रां क्रीं क्रौं सः भौमाय नमः", element:"Agni", elementEmoji:"🔥" },
  vrishabh:  { colors:[{name:"Safed",hex:"#f8fafc"},{name:"Gulabi",hex:"#fca5a5"}], numbers:[2,6], days:["Shukravar","Budhavar"], gemstone:"Diamond",   gemstoneHi:"Heera",    direction:"Dakshin", directionEmoji:"⬇️", metal:"Chandi",  deity:"Lakshmi",   mantra:"ॐ द्रां द्रीं द्रौं सः शुक्राय नमः", element:"Prithvi", elementEmoji:"🌍" },
  mithun:    { colors:[{name:"Peela",hex:"#facc15"},{name:"Hari",hex:"#84cc16"}],   numbers:[3,5], days:["Budhavar","Shukravar"], gemstone:"Emerald",   gemstoneHi:"Panna",    direction:"Paschim", directionEmoji:"⬅️", metal:"Sona",    deity:"Ganesh",    mantra:"ॐ ब्रां ब्रीं ब्रौं सः बुधाय नमः", element:"Vayu", elementEmoji:"💨" },
  kark:      { colors:[{name:"Safed",hex:"#e2e8f0"},{name:"Peela",hex:"#fef08a"}],  numbers:[2,7], days:["Somvar","Guruvaar"],   gemstone:"Pearl",     gemstoneHi:"Moti",     direction:"Uttar",   directionEmoji:"⬆️", metal:"Chandi",  deity:"Shiva",     mantra:"ॐ श्रां श्रीं श्रौं सः चंद्रमसे नमः", element:"Jal", elementEmoji:"💧" },
  simha:     { colors:[{name:"Sona",hex:"#f59e0b"},{name:"Narangi",hex:"#fb923c"}], numbers:[1,4], days:["Ravivaar","Mangalvar"], gemstone:"Ruby",      gemstoneHi:"Manikya",  direction:"Purva",   directionEmoji:"➡️", metal:"Sona",    deity:"Surya",     mantra:"ॐ ह्रां ह्रीं ह्रौं सः सूर्याय नमः", element:"Agni", elementEmoji:"🔥" },
  kanya:     { colors:[{name:"Hari",hex:"#22c55e"},{name:"Neebu",hex:"#bef264"}],   numbers:[5,6], days:["Budhavar","Shukravar"], gemstone:"Emerald",   gemstoneHi:"Panna",    direction:"Paschim", directionEmoji:"⬅️", metal:"Chandi",  deity:"Saraswati", mantra:"ॐ ब्रां ब्रीं ब्रौं सः बुधाय नमः", element:"Prithvi", elementEmoji:"🌍" },
  tula:      { colors:[{name:"Neela",hex:"#60a5fa"},{name:"Gulabi",hex:"#f9a8d4"}], numbers:[6,8], days:["Shukravar","Budhavar"], gemstone:"Diamond",   gemstoneHi:"Heera",    direction:"Purva",   directionEmoji:"➡️", metal:"Chandi",  deity:"Lakshmi",   mantra:"ॐ द्रां द्रीं द्रौं सः शुक्राय नमः", element:"Vayu", elementEmoji:"💨" },
  vrishchik: { colors:[{name:"Laal",hex:"#f43f5e"},{name:"Maroon",hex:"#991b1b"}],  numbers:[1,9], days:["Mangalvar","Ravivaar"], gemstone:"Coral",     gemstoneHi:"Moonga",   direction:"Uttar",   directionEmoji:"⬆️", metal:"Loha",    deity:"Kali",      mantra:"ॐ क्रां क्रीं क्रौं सः भौमाय नमः", element:"Jal", elementEmoji:"💧" },
  dhanu:     { colors:[{name:"Peela",hex:"#eab308"},{name:"Narangi",hex:"#fb923c"}], numbers:[3,9], days:["Guruvaar","Ravivaar"],  gemstone:"Yellow Sapphire", gemstoneHi:"Pukhraj", direction:"Uttar-Purva", directionEmoji:"↗️", metal:"Sona",    deity:"Vishnu",    mantra:"ॐ ग्रां ग्रीं ग्रौं सः गुरवे नमः", element:"Agni", elementEmoji:"🔥" },
  makar:     { colors:[{name:"Kaala",hex:"#1e293b"},{name:"Neela",hex:"#1d4ed8"}],  numbers:[8,4], days:["Shanivaar","Budhavar"], gemstone:"Blue Sapphire", gemstoneHi:"Neelam", direction:"Paschim", directionEmoji:"⬅️", metal:"Loha",    deity:"Shani",     mantra:"ॐ प्रां प्रीं प्रौं सः शनये नमः", element:"Prithvi", elementEmoji:"🌍" },
  kumbh:     { colors:[{name:"Neela",hex:"#7dd3fc"},{name:"Violet",hex:"#a78bfa"}], numbers:[4,8], days:["Shanivaar","Ravivaar"], gemstone:"Blue Sapphire", gemstoneHi:"Neelam", direction:"Paschim", directionEmoji:"⬅️", metal:"Loha",    deity:"Shani",     mantra:"ॐ प्रां प्रीं प्रौं सः शनये नमः", element:"Vayu", elementEmoji:"💨" },
  meen:      { colors:[{name:"Peela",hex:"#fef08a"},{name:"Sea Green",hex:"#34d399"}], numbers:[3,7], days:["Guruvaar","Somvar"],  gemstone:"Yellow Sapphire", gemstoneHi:"Pukhraj", direction:"Uttar-Purva", directionEmoji:"↗️", metal:"Sona",    deity:"Vishnu",    mantra:"ॐ ग्रां ग्रीं ग्रौं सः गुरवे नमः", element:"Jal", elementEmoji:"💧" },
};

const RASHIS_META: Record<RashiKey, {name:string;emoji:string}> = {
  mesh:{name:"मेष",emoji:"♈"}, vrishabh:{name:"वृषभ",emoji:"♉"}, mithun:{name:"मिथुन",emoji:"♊"},
  kark:{name:"कर्क",emoji:"♋"}, simha:{name:"सिंह",emoji:"♌"}, kanya:{name:"कन्या",emoji:"♍"},
  tula:{name:"तुला",emoji:"♎"}, vrishchik:{name:"वृश्चिक",emoji:"♏"}, dhanu:{name:"धनु",emoji:"♐"},
  makar:{name:"मकर",emoji:"♑"}, kumbh:{name:"कुम्भ",emoji:"♒"}, meen:{name:"मीन",emoji:"♓"},
};

function Card({ title, children }: { title: string; children: React.ReactNode }) {
  const C = useC();
  return (
    <View style={[card.wrap, { backgroundColor: C.bgCard, borderColor: C.border }]}>
      <Text style={[card.title, { color: C.textMuted }]}>{title}</Text>
      {children}
    </View>
  );
}
const card = StyleSheet.create({
  wrap: { borderRadius: 16, borderWidth: 1, padding: 16, gap: 12 },
  title: { fontSize: 10, fontFamily: "Nunito_700Bold", letterSpacing: 1.5 },
});

// Map English/Hindi sign names → RashiKey
const SIGN_TO_RASHI: Record<string, RashiKey> = {
  aries: "mesh", mesh: "mesh", "मेष": "mesh",
  taurus: "vrishabh", vrishabh: "vrishabh", "वृषभ": "vrishabh",
  gemini: "mithun", mithun: "mithun", "मिथुन": "mithun",
  cancer: "kark", kark: "kark", "कर्क": "kark",
  leo: "simha", simha: "simha", "सिंह": "simha",
  virgo: "kanya", kanya: "kanya", "कन्या": "kanya",
  libra: "tula", tula: "tula", "तुला": "tula",
  scorpio: "vrishchik", vrishchik: "vrishchik", "वृश्चिक": "vrishchik",
  sagittarius: "dhanu", dhanu: "dhanu", "धनु": "dhanu",
  capricorn: "makar", makar: "makar", "मकर": "makar",
  aquarius: "kumbh", kumbh: "kumbh", "कुम्भ": "kumbh", "कुंभ": "kumbh",
  pisces: "meen", meen: "meen", "मीन": "meen",
};

function deriveRashi(moonSign?: string | null, planets?: Array<{ name: string; rashi?: string }>): RashiKey {
  if (moonSign) {
    const k = SIGN_TO_RASHI[moonSign.trim().toLowerCase()];
    if (k) return k;
  }
  const moon = planets?.find(p => p?.name === "Moon");
  if (moon?.rashi) {
    const k = SIGN_TO_RASHI[moon.rashi.trim().toLowerCase()];
    if (k) return k;
  }
  return "mesh";
}

// Day-of-year (0..365) — used as deterministic seed for daily rotation
function dayOfYear(d: Date): number {
  const start = new Date(d.getFullYear(), 0, 0);
  return Math.floor((d.getTime() - start.getTime()) / 86400000);
}

const RASHI_INDEX: Record<RashiKey, number> = {
  mesh: 0, vrishabh: 1, mithun: 2, kark: 3, simha: 4, kanya: 5,
  tula: 6, vrishchik: 7, dhanu: 8, makar: 9, kumbh: 10, meen: 11,
};

// Daily energy hint — rotates by weekday (deterministic, no API needed)
const DAILY_HINTS = [
  "Aaj ka graha-yog steady hai — shanti ke saath kaam karein.",     // Sun
  "Chandrama prabhav prabal — bhaavnaaen samajhdari se sambhalein.", // Mon
  "Mangal urja active — saahas aur action ka din.",                  // Tue
  "Budh ki kripa — sanchaar aur planning sukhad hogi.",              // Wed
  "Guru ka ashirvaad — gyaan aur uchch shiksha ke avsar.",           // Thu
  "Shukra ka prabhav — kala, prem aur soundarya ka din.",            // Fri
  "Shani ka asar — sthirta aur mehnat ka din, dheeraj rakhein.",     // Sat
];

export default function LuckyScreen() {
  const C = useC();
  const t = useT();
  const insets = useSafeAreaInsets();
  const { profiles, kundli } = useUser();
  const rashi = deriveRashi(kundli?.moonSign, kundli?.planets);
  const rashiMeta = RASHIS_META[rashi] ?? RASHIS_META.mesh;
  const baseLucky = LUCKY[rashi] ?? LUCKY.mesh;
  const now = new Date();

  // Daily-varying lucky number derived from rashi seed + day-of-year
  const dailyLucky = useMemo(() => {
    const dy = dayOfYear(now);
    const seed = (RASHI_INDEX[rashi] ?? 0) * 13 + dy;
    const todaysNumber = ((seed % 9) + 1);   // 1..9
    const todaysHint   = DAILY_HINTS[now.getDay()];
    // Merge daily number with the rashi's base 2 numbers (deduped)
    const numbers = Array.from(new Set([todaysNumber, ...baseLucky.numbers])).slice(0, 3);
    return { ...baseLucky, numbers, hint: todaysHint };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [rashi]);
  const lucky = dailyLucky;

  const today = useMemo(() => {
    const d = new Date();
    return d.toLocaleDateString("hi-IN", { weekday: "long", day: "numeric", month: "long", year: "numeric" });
  }, []);

  return (
    <View style={{ flex: 1 }}>
      <CosmicBg />
      <View style={[s.topBar, { paddingTop: insets.top + 10 }]}>
        <Pressable onPress={() => router.back()} style={s.backBtn}>
          <Feather name="arrow-left" size={20} color={C.text} />
        </Pressable>
        <View>
          <Text style={[s.title, { color: C.text }]}>{t.luckyTitle}</Text>
          <Text style={[s.sub, { color: C.textMuted }]}>{rashiMeta.emoji} {rashiMeta.name} · {today}</Text>
        </View>
        <View style={{ width: 36 }} />
      </View>

      <ScrollView
        showsVerticalScrollIndicator={false}
        contentContainerStyle={{ paddingHorizontal: 16, paddingBottom: insets.bottom + 100, gap: 14 }}
      >
        {/* Today's Cosmic Pulse — daily-rotating hint */}
        <Card title="✨ AAJ KA YOG (TODAY'S PULSE)">
          <Text style={{ color: C.text, fontSize: 13, fontFamily: F.medium, lineHeight: 19 }}>
            {lucky.hint}
          </Text>
        </Card>

        {/* Lucky Colors */}
        <Card title="🎨 LUCKY RANG (COLORS)">
          <View style={{ flexDirection: "row", gap: 10 }}>
            {lucky.colors.map(c => (
              <View key={c.hex} style={{ alignItems: "center", gap: 6 }}>
                <View style={[s.colorSwatch, { backgroundColor: c.hex, borderColor: `${c.hex}60` }]} />
                <Text style={[s.colorName, { color: C.text }]}>{c.name}</Text>
              </View>
            ))}
          </View>
        </Card>

        {/* Lucky Numbers */}
        <Card title="🔢 LUCKY ANKA (NUMBERS)">
          <View style={{ flexDirection: "row", gap: 10 }}>
            {lucky.numbers.map(n => (
              <View key={n} style={[s.numCircle, { backgroundColor: C.isDark ? "#f59e0b22" : C.warningBg, borderColor: C.isDark ? "#f59e0b44" : C.warningBorder }]}>
                <Text style={[s.numText, { color: C.isDark ? "#f59e0b" : "#92400E" }]}>{n}</Text>
              </View>
            ))}
          </View>
        </Card>

        {/* Lucky Days */}
        <Card title="📅 LUCKY DIN (DAYS)">
          <View style={{ flexDirection: "row", gap: 8, flexWrap: "wrap" }}>
            {lucky.days.map(d => (
              <View key={d} style={[s.chip, { backgroundColor: C.isDark ? "#22c55e14" : "#DCFCE7", borderColor: C.isDark ? "#22c55e40" : "#86EFAC" }]}>
                <Text style={[s.chipText, { color: "#22c55e" }]}>{d}</Text>
              </View>
            ))}
          </View>
        </Card>

        {/* Gemstone */}
        <Card title="💎 LUCKY RATAN (GEMSTONE)">
          <View style={[s.gemRow, { backgroundColor: C.bgCard2, borderColor: C.border }]}>
            <Text style={{ fontSize: 32 }}>💎</Text>
            <View>
              <Text style={[s.gemName, { color: C.text }]}>{lucky.gemstoneHi}</Text>
              <Text style={[s.gemEn, { color: C.textMuted }]}>{lucky.gemstone}</Text>
              <Text style={[s.gemTip, { color: C.textDim }]}>Sone ya Chandi mein dharan karein</Text>
            </View>
          </View>
        </Card>

        {/* Direction + Metal + Element */}
        <View style={{ flexDirection: "row", gap: 10 }}>
          <View style={[s.smallCard, { backgroundColor: C.bgCard, borderColor: C.border, flex: 1 }]}>
            <Text style={[s.smallLabel, { color: C.textMuted }]}>⬆️ DISHA</Text>
            <Text style={{ fontSize: 22 }}>{lucky.directionEmoji}</Text>
            <Text style={[s.smallVal, { color: C.text }]}>{lucky.direction}</Text>
          </View>
          <View style={[s.smallCard, { backgroundColor: C.bgCard, borderColor: C.border, flex: 1 }]}>
            <Text style={[s.smallLabel, { color: C.textMuted }]}>⚗️ DHATU</Text>
            <Text style={{ fontSize: 22 }}>🔩</Text>
            <Text style={[s.smallVal, { color: C.text }]}>{lucky.metal}</Text>
          </View>
          <View style={[s.smallCard, { backgroundColor: C.bgCard, borderColor: C.border, flex: 1 }]}>
            <Text style={[s.smallLabel, { color: C.textMuted }]}>TATVA</Text>
            <Text style={{ fontSize: 22 }}>{lucky.elementEmoji}</Text>
            <Text style={[s.smallVal, { color: C.text }]}>{lucky.element}</Text>
          </View>
        </View>

        {/* Deity */}
        <Card title="🛕 ARADHYA DEVTA">
          <View style={[s.deityRow, { backgroundColor: C.bgCard2, borderColor: C.border }]}>
            <Text style={{ fontSize: 26 }}>🕉️</Text>
            <View style={{ flex: 1 }}>
              <Text style={[s.deityName, { color: C.text }]}>{lucky.deity}</Text>
              <Text style={[s.deityTip, { color: C.textMuted }]}>Puja aur dhyan se vishesh laabh milega</Text>
            </View>
          </View>
        </Card>

        {/* Mantra */}
        <Card title="🔔 GRAHA MANTRA">
          <View style={[s.mantraBox, { backgroundColor: C.isDark ? "#f59e0b08" : C.warningBg, borderColor: C.isDark ? "#f59e0b30" : C.warningBorder }]}>
            <Text style={[s.mantraText, { color: C.isDark ? "#f59e0b" : "#92400E" }]}>{lucky.mantra}</Text>
            <Text style={[s.mantraTip, { color: C.textMuted }]}>Roshandar ya Shubh muhurat mein 108 baar jaap karein</Text>
          </View>
        </Card>
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
  colorSwatch: {
    width: 56, height: 56, borderRadius: 16, borderWidth: 2,
  },
  colorName: { fontSize: 11, fontFamily: F.semibold },
  numCircle: {
    width: 50, height: 50, borderRadius: 25,
    alignItems: "center", justifyContent: "center", borderWidth: 1.5,
  },
  numText: { fontSize: 22, fontFamily: F.bold },
  chip: {
    paddingHorizontal: 14, paddingVertical: 7,
    borderRadius: 20, borderWidth: 1,
  },
  chipText: { fontSize: 13, fontFamily: F.semibold },
  gemRow: {
    flexDirection: "row", alignItems: "center", gap: 14,
    padding: 14, borderRadius: 12, borderWidth: 1,
  },
  gemName: { fontSize: 18, fontFamily: F.bold },
  gemEn: { fontSize: 12, fontFamily: F.medium },
  gemTip: { fontSize: 10, fontFamily: F.regular, marginTop: 3 },
  smallCard: {
    borderRadius: 14, borderWidth: 1, padding: 12,
    alignItems: "center", gap: 4,
  },
  smallLabel: { fontSize: 8, fontFamily: F.bold, letterSpacing: 1.2 },
  smallVal: { fontSize: 12, fontFamily: F.bold, textAlign: "center" },
  deityRow: {
    flexDirection: "row", alignItems: "center", gap: 12,
    padding: 14, borderRadius: 12, borderWidth: 1,
  },
  deityName: { fontSize: 17, fontFamily: F.bold },
  deityTip: { fontSize: 11, fontFamily: F.regular, marginTop: 2 },
  mantraBox: {
    padding: 14, borderRadius: 12, borderWidth: 1, gap: 8,
  },
  mantraText: { fontSize: 15, fontFamily: F.semibold, textAlign: "center", lineHeight: 24 },
  mantraTip: { fontSize: 11, fontFamily: F.regular, textAlign: "center" },
});
