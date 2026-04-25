import { Feather } from "@expo/vector-icons";
import { router } from "expo-router";
import React, { useMemo } from "react";
import {
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
import { useUser } from "@/context/UserContext";
import { useT } from "@/hooks/useT";
import {
  RASHI, COLOR, METAL, ELEMENT, GEMSTONE, DAY, DEITY, DIRECTION,
  pick, type RashiKey,
} from "@/lib/i18nVedic";

const F = {
  bold: "Nunito_700Bold", semibold: "Nunito_600SemiBold",
  medium: "Nunito_500Medium", regular: "Nunito_400Regular",
};

// ── Lucky data: keys instead of hardcoded strings ─────────────────────────────
type LuckyData = {
  colors: { key: string; hex: string }[];
  numbers: number[];
  days: ("sun"|"mon"|"tue"|"wed"|"thu"|"fri"|"sat")[];
  gemstone: keyof typeof GEMSTONE;
  direction: keyof typeof DIRECTION; directionEmoji: string;
  metal: keyof typeof METAL;
  deity: keyof typeof DEITY;
  mantra: string;                    // Sanskrit — kept in Devanagari (sacred)
  element: keyof typeof ELEMENT; elementEmoji: string;
};

const LUCKY: Record<RashiKey, LuckyData> = {
  mesh:      { colors:[{key:"red",hex:"#ef4444"},{key:"orange",hex:"#fb923c"}],     numbers:[1,9], days:["tue","sun"],   gemstone:"coral",          direction:"N", directionEmoji:"⬆️",  metal:"copper", deity:"hanuman",   mantra:"ॐ क्रां क्रीं क्रौं सः भौमाय नमः",  element:"fire",  elementEmoji:"🔥" },
  vrishabh:  { colors:[{key:"white",hex:"#f8fafc"},{key:"pink",hex:"#fca5a5"}],     numbers:[2,6], days:["fri","wed"],   gemstone:"diamond",        direction:"S", directionEmoji:"⬇️",  metal:"silver", deity:"lakshmi",   mantra:"ॐ द्रां द्रीं द्रौं सः शुक्राय नमः",  element:"earth", elementEmoji:"🌍" },
  mithun:    { colors:[{key:"yellow",hex:"#facc15"},{key:"green",hex:"#84cc16"}],   numbers:[3,5], days:["wed","fri"],   gemstone:"emerald",        direction:"W", directionEmoji:"⬅️",  metal:"gold",   deity:"ganesh",    mantra:"ॐ ब्रां ब्रीं ब्रौं सः बुधाय नमः",   element:"air",   elementEmoji:"💨" },
  kark:      { colors:[{key:"white",hex:"#e2e8f0"},{key:"yellow",hex:"#fef08a"}],   numbers:[2,7], days:["mon","thu"],   gemstone:"pearl",          direction:"N", directionEmoji:"⬆️",  metal:"silver", deity:"shiva",     mantra:"ॐ श्रां श्रीं श्रौं सः चंद्रमसे नमः",  element:"water", elementEmoji:"💧" },
  simha:     { colors:[{key:"gold",hex:"#f59e0b"},{key:"orange",hex:"#fb923c"}],    numbers:[1,4], days:["sun","tue"],   gemstone:"ruby",           direction:"E", directionEmoji:"➡️",  metal:"gold",   deity:"surya",     mantra:"ॐ ह्रां ह्रीं ह्रौं सः सूर्याय नमः",  element:"fire",  elementEmoji:"🔥" },
  kanya:     { colors:[{key:"green",hex:"#22c55e"},{key:"lime",hex:"#bef264"}],     numbers:[5,6], days:["wed","fri"],   gemstone:"emerald",        direction:"W", directionEmoji:"⬅️",  metal:"silver", deity:"saraswati", mantra:"ॐ ब्रां ब्रीं ब्रौं सः बुधाय नमः",   element:"earth", elementEmoji:"🌍" },
  tula:      { colors:[{key:"blue",hex:"#60a5fa"},{key:"pink",hex:"#f9a8d4"}],      numbers:[6,8], days:["fri","wed"],   gemstone:"diamond",        direction:"E", directionEmoji:"➡️",  metal:"silver", deity:"lakshmi",   mantra:"ॐ द्रां द्रीं द्रौं सः शुक्राय नमः",  element:"air",   elementEmoji:"💨" },
  vrishchik: { colors:[{key:"red",hex:"#f43f5e"},{key:"maroon",hex:"#991b1b"}],     numbers:[1,9], days:["tue","sun"],   gemstone:"coral",          direction:"N", directionEmoji:"⬆️",  metal:"iron",   deity:"kali",      mantra:"ॐ क्रां क्रीं क्रौं सः भौमाय नमः",  element:"water", elementEmoji:"💧" },
  dhanu:     { colors:[{key:"yellow",hex:"#eab308"},{key:"orange",hex:"#fb923c"}],  numbers:[3,9], days:["thu","sun"],   gemstone:"yellowsapphire", direction:"NE",directionEmoji:"↗️", metal:"gold",   deity:"vishnu",    mantra:"ॐ ग्रां ग्रीं ग्रौं सः गुरवे नमः",  element:"fire",  elementEmoji:"🔥" },
  makar:     { colors:[{key:"black",hex:"#1e293b"},{key:"blue",hex:"#1d4ed8"}],     numbers:[8,4], days:["sat","wed"],   gemstone:"bluesapphire",   direction:"W", directionEmoji:"⬅️",  metal:"iron",   deity:"shani",     mantra:"ॐ प्रां प्रीं प्रौं सः शनये नमः",   element:"earth", elementEmoji:"🌍" },
  kumbh:     { colors:[{key:"skyblue",hex:"#7dd3fc"},{key:"violet",hex:"#a78bfa"}], numbers:[4,8], days:["sat","sun"],   gemstone:"bluesapphire",   direction:"W", directionEmoji:"⬅️",  metal:"iron",   deity:"shani",     mantra:"ॐ प्रां प्रीं प्रौं सः शनये नमः",   element:"air",   elementEmoji:"💨" },
  meen:      { colors:[{key:"yellow",hex:"#fef08a"},{key:"seagreen",hex:"#34d399"}],numbers:[3,7], days:["thu","mon"],   gemstone:"yellowsapphire", direction:"NE",directionEmoji:"↗️", metal:"gold",   deity:"vishnu",    mantra:"ॐ ग्रां ग्रीं ग्रौं सः गुरवे नमः",  element:"water", elementEmoji:"💧" },
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

// Map English/Hindi/Hinglish sign names → RashiKey
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

function dayOfYear(d: Date): number {
  const start = new Date(d.getFullYear(), 0, 0);
  return Math.floor((d.getTime() - start.getTime()) / 86400000);
}

const RASHI_INDEX: Record<RashiKey, number> = {
  mesh: 0, vrishabh: 1, mithun: 2, kark: 3, simha: 4, kanya: 5,
  tula: 6, vrishchik: 7, dhanu: 8, makar: 9, kumbh: 10, meen: 11,
};

// Daily energy hint — translated to all 3 vocab buckets
const DAILY_HINTS: Record<"en"|"hn"|"hi", string[]> = {
  en: [
    "Today's planetary alignment is steady — work with calm focus.",
    "The Moon's influence is strong — handle emotions with wisdom.",
    "Mars energy is active — a day for courage and bold action.",
    "Mercury blesses you — communication and planning will flow well.",
    "Jupiter's grace is upon you — wisdom and higher learning favored.",
    "Venus radiates warmly — a day for art, love, and beauty.",
    "Saturn's gaze is deep — stability and discipline reward patience.",
  ],
  hn: [
    "Aaj ka graha-yog steady hai — shanti ke saath kaam karein.",
    "Chandrama prabhav prabal — bhaavnaaen samajhdari se sambhalein.",
    "Mangal urja active — saahas aur action ka din.",
    "Budh ki kripa — sanchaar aur planning sukhad hogi.",
    "Guru ka ashirvaad — gyaan aur uchch shiksha ke avsar.",
    "Shukra ka prabhav — kala, prem aur soundarya ka din.",
    "Shani ka asar — sthirta aur mehnat ka din, dheeraj rakhein.",
  ],
  hi: [
    "आज का ग्रह-योग स्थिर है — शांति के साथ कार्य करें।",
    "चंद्रमा का प्रभाव प्रबल है — भावनाओं को समझदारी से संभालें।",
    "मंगल ऊर्जा सक्रिय — साहस और कर्म का दिन।",
    "बुध की कृपा — संचार और योजना सुखद होगी।",
    "गुरु का आशीर्वाद — ज्ञान और उच्च शिक्षा के अवसर।",
    "शुक्र का प्रभाव — कला, प्रेम और सौंदर्य का दिन।",
    "शनि का असर — स्थिरता और मेहनत का दिन, धैर्य रखें।",
  ],
};

export default function LuckyScreen() {
  const C = useC();
  const t = useT();
  const insets = useSafeAreaInsets();
  const { profiles, kundli } = useUser();
  const rashi = deriveRashi(kundli?.moonSign, kundli?.planets);
  const baseLucky = LUCKY[rashi] ?? LUCKY.mesh;
  const now = new Date();

  // Resolve names based on current language
  const v = t.vlang;
  const rashiDisplay = pick(v, RASHI[rashi]);
  const rashiEmoji = RASHI[rashi].emoji;

  const dailyLucky = useMemo(() => {
    const dy = dayOfYear(now);
    const seed = (RASHI_INDEX[rashi] ?? 0) * 13 + dy;
    const todaysNumber = ((seed % 9) + 1);
    const todaysHint   = DAILY_HINTS[v][now.getDay()];
    const numbers = Array.from(new Set([todaysNumber, ...baseLucky.numbers])).slice(0, 3);
    return { ...baseLucky, numbers, hint: todaysHint };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [rashi, v]);
  const lucky = dailyLucky;

  const today = useMemo(() => {
    const d = new Date();
    const locale = v === "en" ? "en-US" : v === "hi" ? "hi-IN" : "en-IN";
    return d.toLocaleDateString(locale, { weekday: "long", day: "numeric", month: "long", year: "numeric" });
  }, [v]);

  return (
    <View style={{ flex: 1 }}>
      <CosmicBg />
      <View style={[s.topBar, { paddingTop: insets.top + 10 }]}>
        <Pressable onPress={() => router.back()} style={s.backBtn}>
          <Feather name={I18nManager.isRTL ? "arrow-right" : "arrow-left"} size={20} color={C.text} />
        </Pressable>
        <View>
          <Text style={[s.title, { color: C.text }]}>{t.luckyTitle}</Text>
          <Text style={[s.sub, { color: C.textMuted }]}>{rashiEmoji} {rashiDisplay} · {today}</Text>
        </View>
        <View style={{ width: 36 }} />
      </View>

      <ScrollView
        showsVerticalScrollIndicator={false}
        contentContainerStyle={{ paddingHorizontal: 16, paddingBottom: insets.bottom + 100, gap: 14 }}
      >
        {/* Today's Cosmic Pulse */}
        <Card title={t.luckyHeaderTodaysPulse}>
          <Text style={{ color: C.text, fontSize: 13, fontFamily: F.medium, lineHeight: 19 }}>
            {lucky.hint}
          </Text>
        </Card>

        {/* Lucky Colors */}
        <Card title={t.luckyHeaderColors}>
          <View style={{ flexDirection: "row", gap: 10 }}>
            {lucky.colors.map(c => (
              <View key={c.hex} style={{ alignItems: "center", gap: 6 }}>
                <View style={[s.colorSwatch, { backgroundColor: c.hex, borderColor: `${c.hex}60` }]} />
                <Text style={[s.colorName, { color: C.text }]}>{pick(v, COLOR[c.key] ?? COLOR.gold)}</Text>
              </View>
            ))}
          </View>
        </Card>

        {/* Lucky Numbers */}
        <Card title={t.luckyHeaderNumbers}>
          <View style={{ flexDirection: "row", gap: 10 }}>
            {lucky.numbers.map(n => (
              <View key={n} style={[s.numCircle, { backgroundColor: C.isDark ? "#f59e0b22" : C.warningBg, borderColor: C.isDark ? "#f59e0b44" : C.warningBorder }]}>
                <Text style={[s.numText, { color: C.isDark ? "#f59e0b" : "#92400E" }]}>{n}</Text>
              </View>
            ))}
          </View>
        </Card>

        {/* Lucky Days */}
        <Card title={t.luckyHeaderDays}>
          <View style={{ flexDirection: "row", gap: 8, flexWrap: "wrap" }}>
            {lucky.days.map(d => (
              <View key={d} style={[s.chip, { backgroundColor: C.isDark ? "#22c55e14" : "#DCFCE7", borderColor: C.isDark ? "#22c55e40" : "#86EFAC" }]}>
                <Text style={[s.chipText, { color: "#22c55e" }]}>{pick(v, DAY[d])}</Text>
              </View>
            ))}
          </View>
        </Card>

        {/* Gemstone */}
        <Card title={t.luckyHeaderGemstone}>
          <View style={[s.gemRow, { backgroundColor: C.bgCard2, borderColor: C.border }]}>
            <Text style={{ fontSize: 32 }}>💎</Text>
            <View>
              <Text style={[s.gemName, { color: C.text }]}>{pick(v, GEMSTONE[lucky.gemstone])}</Text>
              {v !== "en" && (
                <Text style={[s.gemEn, { color: C.textMuted }]}>{GEMSTONE[lucky.gemstone].en}</Text>
              )}
              <Text style={[s.gemTip, { color: C.textDim }]}>{t.luckyGemstoneTip}</Text>
            </View>
          </View>
        </Card>

        {/* Direction + Metal + Element */}
        <View style={{ flexDirection: "row", gap: 10 }}>
          <View style={[s.smallCard, { backgroundColor: C.bgCard, borderColor: C.border, flex: 1 }]}>
            <Text style={[s.smallLabel, { color: C.textMuted }]}>{t.luckyLabelDirection}</Text>
            <Text style={{ fontSize: 22 }}>{lucky.directionEmoji}</Text>
            <Text style={[s.smallVal, { color: C.text }]}>{pick(v, DIRECTION[lucky.direction])}</Text>
          </View>
          <View style={[s.smallCard, { backgroundColor: C.bgCard, borderColor: C.border, flex: 1 }]}>
            <Text style={[s.smallLabel, { color: C.textMuted }]}>{t.luckyLabelMetal}</Text>
            <Text style={{ fontSize: 22 }}>🔩</Text>
            <Text style={[s.smallVal, { color: C.text }]}>{pick(v, METAL[lucky.metal])}</Text>
          </View>
          <View style={[s.smallCard, { backgroundColor: C.bgCard, borderColor: C.border, flex: 1 }]}>
            <Text style={[s.smallLabel, { color: C.textMuted }]}>{t.luckyLabelElement}</Text>
            <Text style={{ fontSize: 22 }}>{lucky.elementEmoji}</Text>
            <Text style={[s.smallVal, { color: C.text }]}>{pick(v, ELEMENT[lucky.element])}</Text>
          </View>
        </View>

        {/* Deity */}
        <Card title={t.luckyHeaderDeity}>
          <View style={[s.deityRow, { backgroundColor: C.bgCard2, borderColor: C.border }]}>
            <Text style={{ fontSize: 26 }}>🕉️</Text>
            <View style={{ flex: 1 }}>
              <Text style={[s.deityName, { color: C.text }]}>{pick(v, DEITY[lucky.deity])}</Text>
              <Text style={[s.deityTip, { color: C.textMuted }]}>{t.luckyDeityTip}</Text>
            </View>
          </View>
        </Card>

        {/* Mantra — kept in Sanskrit (Devanagari) always, sacred */}
        <Card title={t.luckyHeaderMantra}>
          <View style={[s.mantraBox, { backgroundColor: C.isDark ? "#f59e0b08" : C.warningBg, borderColor: C.isDark ? "#f59e0b30" : C.warningBorder }]}>
            <Text style={[s.mantraText, { color: C.isDark ? "#f59e0b" : "#92400E" }]}>{lucky.mantra}</Text>
            <Text style={[s.mantraTip, { color: C.textMuted }]}>{t.luckyMantraTip}</Text>
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
