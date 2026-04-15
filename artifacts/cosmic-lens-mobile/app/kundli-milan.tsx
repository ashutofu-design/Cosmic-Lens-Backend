import { Feather } from "@expo/vector-icons";
import * as Haptics from "expo-haptics";
import { LinearGradient } from "expo-linear-gradient";
import { router } from "expo-router";
import React, { useState } from "react";
import {
  ActivityIndicator, KeyboardAvoidingView, Platform,
  Pressable, ScrollView, StyleSheet, Text,
  TextInput, View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useC } from "@/context/ThemeContext";
import { useUser } from "@/context/UserContext";

// ── Nakshatra / Rashi Data ────────────────────────────────────────────────────

const NAKSHATRAS = [
  "Ashwini","Bharani","Krittika","Rohini","Mrigashira","Ardra","Punarvasu","Pushya",
  "Ashlesha","Magha","Purva Phalguni","Uttara Phalguni","Hasta","Chitra","Swati",
  "Vishakha","Anuradha","Jyeshtha","Mula","Purva Ashadha","Uttara Ashadha","Shravana",
  "Dhanishtha","Shatabhisha","Purva Bhadrapada","Uttara Bhadrapada","Revati",
];

const RASHIS = [
  "Mesh","Vrishabh","Mithun","Kark","Simha","Kanya",
  "Tula","Vrishchik","Dhanu","Makar","Kumbh","Meen",
];

const ENGLISH_TO_RASHI: Record<string, string> = {
  "Aries":"Mesh","Taurus":"Vrishabh","Gemini":"Mithun","Cancer":"Kark",
  "Leo":"Simha","Virgo":"Kanya","Libra":"Tula","Scorpio":"Vrishchik",
  "Sagittarius":"Dhanu","Capricorn":"Makar","Aquarius":"Kumbh","Pisces":"Meen",
};

// Nakshatra → Nadi (0=Vata/Adi, 1=Pitta/Madhya, 2=Kapha/Antya)
const NADI = [0,1,2,2,1,0,0,1,2,2,1,0,0,1,2,2,1,0,0,1,2,2,1,0,0,1,2];
const NADI_NAMES = ["Vata (Adi)","Pitta (Madhya)","Kapha (Antya)"];

// Nakshatra → Gana (0=Dev, 1=Manushya, 2=Raksha)
const GANA = [0,1,2,1,0,1,0,0,2,2,1,1,0,2,0,2,0,2,2,1,1,0,1,2,1,1,0];
const GANA_NAMES = ["Dev","Manushya","Raksha"];

// Rashi → Varna (0=Brahmin, 1=Kshatriya, 2=Vaishya, 3=Shudra)
const VARNA = [1,2,3,0,1,2,3,0,1,2,3,0];

// Nakshatra → Yoni animal (0–14, pair must not be enemy)
const YONI = [0,1,2,3,4,5,6,7,8,9,10,2,11,12,13,14,14,13,5,12,11,10,3,7,4,9,0];
// Yoni enemy pairs (indices)
const YONI_ENEMIES: [number,number][] = [[0,1],[2,3],[4,5],[6,7],[8,9],[10,11],[12,13],[14,0]];

function isYoniEnemy(a: number, b: number) {
  return YONI_ENEMIES.some(([x,y]) => (a===x&&b===y)||(a===y&&b===x));
}

// Rashi lord (0=Sun,1=Moon,2=Mars,3=Mercury,4=Jupiter,5=Venus,6=Saturn,7=Rahu)
const RASHI_LORD = [2,5,3,1,0,3,5,2,4,6,6,4];

// Planet friendship matrix [planet][planet] = 2(friend), 1(neutral), 0(enemy)
const PLN_FRIEND: number[][] = [
  [1,2,2,1,2,0,0],
  [2,1,0,1,2,2,0],
  [2,0,1,1,2,0,2],
  [2,0,2,1,0,2,0],
  [2,1,2,1,1,0,0],
  [2,2,0,2,1,1,0],
  [0,0,2,2,2,0,1],
];

function getGrahaMaitri(r1: number, r2: number): number {
  const l1 = RASHI_LORD[r1] ?? 0;
  const l2 = RASHI_LORD[r2] ?? 0;
  if (l1 >= PLN_FRIEND.length || l2 >= PLN_FRIEND.length) return 3;
  const ab = PLN_FRIEND[l1]?.[l2] ?? 1;
  const ba = PLN_FRIEND[l2]?.[l1] ?? 1;
  const total = ab + ba;
  if (total >= 4) return 5;
  if (total === 3) return 4;
  if (total === 2) return 3;
  return 0;
}

// Tara: count from nak1 to nak2
function getTara(n1: number, n2: number): number {
  const fwd = ((n2 - n1 + 27) % 27) + 1;
  const rev = ((n1 - n2 + 27) % 27) + 1;
  const bad = [3,5,7];
  const fwdBad = bad.includes(fwd % 9 || 9);
  const revBad = bad.includes(rev % 9 || 9);
  if (!fwdBad && !revBad) return 3;
  if (!fwdBad || !revBad) return 1.5;
  return 0;
}

// Bhakut: based on rashi relationship
function getBhakut(r1: number, r2: number): number {
  const diff = Math.abs(r1 - r2);
  const rel  = Math.min(diff, 12 - diff);
  // 2-12, 5-9, 6-8 are bad (0 pts)
  const badPairs = [
    [1,11],[4,8],[5,7],
  ];
  const bad = badPairs.some(([a,b]) => (diff===a||diff===b));
  return bad ? 0 : 7;
}

// Vasya (simplified)
function getVasya(r1: number, r2: number): number {
  if (r1 === r2) return 2;
  const groups = [[0,3,4],[1,6,7,9],[2,8],[5,10,11]];
  const g1 = groups.findIndex(g => g.includes(r1));
  const g2 = groups.findIndex(g => g.includes(r2));
  return g1 === g2 ? 2 : 1;
}

interface AshtakootResult {
  nadi:       { score: number; max: 8;  label: string; detail: string; bad: boolean };
  gana:       { score: number; max: 6;  label: string; detail: string; bad: boolean };
  bhakut:     { score: number; max: 7;  label: string; detail: string; bad: boolean };
  maitri:     { score: number; max: 5;  label: string; detail: string; bad: boolean };
  yoni:       { score: number; max: 4;  label: string; detail: string; bad: boolean };
  tara:       { score: number; max: 3;  label: string; detail: string; bad: boolean };
  vasya:      { score: number; max: 2;  label: string; detail: string; bad: boolean };
  varna:      { score: number; max: 1;  label: string; detail: string; bad: boolean };
  total:      number;
  manglikDosha: boolean;
}

function computeAshtakoot(
  n1: number, r1: number, mars1: boolean,
  n2: number, r2: number, mars2: boolean,
): AshtakootResult {
  const nad1 = NADI[n1] ?? 0;
  const nad2 = NADI[n2] ?? 0;
  const nadiScore = nad1 !== nad2 ? 8 : 0;
  const nadiLabel = nadiScore === 8 ? "Alag Nadi" : `Dono ${NADI_NAMES[nad1]} — Nadi Dosh`;

  const g1 = GANA[n1] ?? 0;
  const g2 = GANA[n2] ?? 0;
  let ganaScore = 6;
  if      ((g1===0&&g2===2)||(g1===2&&g2===0)) ganaScore = 1;
  else if ((g1===1&&g2===2)||(g1===2&&g2===1)) ganaScore = 0;
  const ganaLabel = ganaScore === 6 ? `${GANA_NAMES[g1]}+${GANA_NAMES[g2]} — Uttam`
    : ganaScore > 0 ? `${GANA_NAMES[g1]}+${GANA_NAMES[g2]} — Madhyam`
    : `${GANA_NAMES[g1]}+${GANA_NAMES[g2]} — Gana Dosh`;

  const bhakutScore = getBhakut(r1, r2);
  const rashiDiff   = ((r2 - r1 + 12) % 12) + 1;
  const bhakutLabel = bhakutScore === 7 ? `${rashiDiff}-${13-rashiDiff} Shubh` : `${rashiDiff}-${13-rashiDiff} Bhakut Dosh`;

  const maitriScore = getGrahaMaitri(r1, r2);
  const maitriLabel = maitriScore >= 4 ? "Graha Mitra" : maitriScore >= 3 ? "Sam" : "Graha Shatru";

  const y1 = YONI[n1] ?? 0;
  const y2 = YONI[n2] ?? 0;
  const enemy = isYoniEnemy(y1, y2);
  const yoniScore = y1 === y2 ? 4 : enemy ? 0 : 2;
  const yoniLabel = yoniScore === 4 ? "Sama Yoni" : yoniScore === 2 ? "Madhyam Yoni" : "Yoni Dosh";

  const taraScore = getTara(n1, n2);
  const taraLabel = taraScore === 3 ? "Shubh Tara" : taraScore > 0 ? "Madhyam Tara" : "Vipat Tara";

  const vasya   = getVasya(r1, r2);
  const vasLabel = vasya === 2 ? "Vasya Shubh" : "Vasya Madhyam";

  const v1 = VARNA[r1] ?? 0;
  const v2 = VARNA[r2] ?? 0;
  const varnaScore = v1 <= v2 ? 1 : 0;
  const varnaLabel = varnaScore ? "Varna Sahi" : "Varna Anmatch";

  const total = nadiScore + ganaScore + bhakutScore + maitriScore +
    yoniScore + taraScore + vasya + varnaScore;

  const manglikDosha = mars1 !== mars2;

  return {
    nadi:   { score:nadiScore,   max:8, label:"Nadi",        detail:nadiLabel,   bad:nadiScore===0 },
    gana:   { score:ganaScore,   max:6, label:"Gana",        detail:ganaLabel,   bad:ganaScore===0 },
    bhakut: { score:bhakutScore, max:7, label:"Bhakut",      detail:bhakutLabel, bad:bhakutScore===0 },
    maitri: { score:maitriScore, max:5, label:"Graha Maitri",detail:maitriLabel, bad:maitriScore<3 },
    yoni:   { score:yoniScore,   max:4, label:"Yoni",        detail:yoniLabel,   bad:yoniScore===0 },
    tara:   { score:taraScore,   max:3, label:"Tara",        detail:taraLabel,   bad:taraScore===0 },
    vasya:  { score:vasya,       max:2, label:"Vasya",       detail:vasLabel,    bad:false },
    varna:  { score:varnaScore,  max:1, label:"Varna",       detail:varnaLabel,  bad:varnaScore===0 },
    total,
    manglikDosha,
  };
}

function getMatchGrade(total: number) {
  if (total >= 32) return { label:"Excellent",    color:"#22c55e", emoji:"💚", desc:"Very auspicious. An ideal match for marriage." };
  if (total >= 27) return { label:"Very Good",    color:"#4ade80", emoji:"🌿", desc:"Great compatibility. A happy marriage is possible." };
  if (total >= 21) return { label:"Average",      color:"#fbbf24", emoji:"💛", desc:"Moderate match. Some precautions recommended." };
  if (total >= 18) return { label:"Below Average",color:"#f97316", emoji:"🟠", desc:"Average match. Consult a Jyotishi for guidance." };
  return              { label:"Not Compatible", color:"#ef4444", emoji:"❤️", desc:"Low score. Remedies and expert guidance strongly advised." };
}

// ── Form fields ───────────────────────────────────────────────────────────────
function FormRow({
  label, value, onChangeText, placeholder, keyboardType = "default",
}: {
  label: string; value: string; onChangeText: (v: string) => void;
  placeholder?: string; keyboardType?: "default" | "numeric";
}) {
  return (
    <View style={f.row}>
      <Text style={f.label}>{label}</Text>
      <TextInput
        value={value}
        onChangeText={onChangeText}
        placeholder={placeholder ?? label}
        placeholderTextColor="#1e3a5f"
        keyboardType={keyboardType}
        style={f.input}
      />
    </View>
  );
}

// ── Main Screen ───────────────────────────────────────────────────────────────
export default function KundliMilanScreen() {
  const insets = useSafeAreaInsets();
  const C = useC();
  const topPad = Platform.OS === "web" ? 67 : insets.top;
  const botPad = Platform.OS === "web" ? 34 : insets.bottom;
  const { kundli: p1Kundli, profiles, primaryProfileId } = useUser();
  const apiBase = process.env.EXPO_PUBLIC_API_BASE_URL ?? "";

  const p1Profile = profiles.find(p => p.id === primaryProfileId);

  // Person 2 form
  const [p2Name,   setP2Name]   = useState("");
  const [p2DOB,    setP2DOB]    = useState("");
  const [p2Time,   setP2Time]   = useState("");
  const [p2Place,  setP2Place]  = useState("");

  const [loading,  setLoading]  = useState(false);
  const [result,   setResult]   = useState<AshtakootResult | null>(null);
  const [error,    setError]    = useState("");

  // Person 1 nakshatra / rashi from kundli
  const p1Nak   = NAKSHATRAS.indexOf(p1Kundli?.nakshatra ?? "");
  const p1RashiEn = p1Kundli?.moonSign ?? "";
  const p1RashiHi = ENGLISH_TO_RASHI[p1RashiEn] ?? "";
  const p1Rashi = RASHIS.indexOf(p1RashiHi);
  const p1Mars  = (p1Kundli?.planets.find(p => p.name === "Mars")?.house ?? 0);
  const p1Manglik = [1,4,7,8,12].includes(p1Mars);

  async function handleCalculate() {
    if (!p1Kundli) { setError("Please create your kundli from your profile first."); return; }
    if (!p2DOB || !p2Time || !p2Place) { setError("Please fill in all birth details for Person 2."); return; }

    setError(""); setLoading(true);
    try {
      const [day, month, year] = p2DOB.split("/").map(Number);
      const [hourMin, ampm]    = p2Time.trim().split(" ");
      const [h, m]             = (hourMin ?? "").split(":").map(Number);
      if (!day || !month || !year || !h || !m) throw new Error("Invalid date/time format. Use DD/MM/YYYY HH:MM AM");

      const url = `${apiBase}/api/kundli`;
      const body = {
        name: p2Name || "Person 2",
        day, month, year, hour: h, minute: m,
        ampm: ampm ?? "AM", place: p2Place,
      };
      const res  = await fetch(url, { method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify(body) });
      const json = await res.json();

      const p2Nak   = NAKSHATRAS.indexOf(json.nakshatra ?? "");
      const p2RashiHi = ENGLISH_TO_RASHI[json.moonSign ?? ""] ?? "";
      const p2Rashi = RASHIS.indexOf(p2RashiHi);
      const p2MarsH = (json.planets as any[]).find(p => p.name === "Mars")?.house ?? 0;
      const p2Manglik = [1,4,7,8,12].includes(p2MarsH);

      if (p2Nak < 0 || p2Rashi < 0) throw new Error("Could not calculate Person 2's kundli.");
      if (p1Nak < 0 || p1Rashi < 0) throw new Error("Could not find Person 1's nakshatra/rashi.");

      const res2 = computeAshtakoot(p1Nak, p1Rashi, p1Manglik, p2Nak, p2Rashi, p2Manglik);
      setResult(res2);
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
    } catch (e: any) {
      setError(e?.message ?? "An error occurred. Please try again.");
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
    } finally {
      setLoading(false);
    }
  }

  const grade = result ? getMatchGrade(result.total) : null;

  const KOOT_ORDER = ["nadi","gana","bhakut","maitri","yoni","tara","vasya","varna"] as const;

  return (
    <KeyboardAvoidingView style={{ flex:1 }} behavior={Platform.OS === "ios" ? "padding" : "height"}>
      <View style={{ flex:1, backgroundColor: C.bg }}>
        {/* Header */}
        <View style={[s.header, { paddingTop: topPad + 8 }]}>
          <Pressable onPress={() => router.back()} style={s.back}>
            <Feather name="arrow-left" size={20} color="#dde8f4" />
          </Pressable>
          <View style={{ flex:1 }}>
            <Text style={s.title}>Kundli Milan</Text>
            <Text style={s.titleHindi}>अष्टकूट गुण मिलान</Text>
          </View>
        </View>

        <ScrollView
          contentContainerStyle={[s.content, { paddingBottom: botPad + 40 }]}
          showsVerticalScrollIndicator={false}
          keyboardShouldPersistTaps="handled"
        >
          {/* ── Person 1 Card ── */}
          <View>
            <Text style={s.sectionLabel}>PERSON 1 (AAPKA)</Text>
            <View style={s.p1Card}>
              <View style={{ flexDirection:"row", alignItems:"center", gap:12 }}>
                <View style={s.p1Avatar}>
                  <Text style={{ fontSize:18 }}>♀</Text>
                </View>
                <View>
                  <Text style={s.p1Name}>{p1Profile?.name ?? "Aapki Profile"}</Text>
                  {p1Kundli ? (
                    <Text style={s.p1Detail}>
                      {p1Kundli.nakshatra} Nakshatra · {p1RashiHi || p1RashiEn} Rashi
                    </Text>
                  ) : (
                    <Pressable onPress={() => router.push("/onboarding")}>
                      <Text style={{ color:"#fbbf24", fontSize:11 }}>Kundli nahi bani — banao →</Text>
                    </Pressable>
                  )}
                </View>
              </View>
            </View>
          </View>

          {/* Connector */}
          <View style={{ alignItems:"center", marginVertical: -4, zIndex:1 }}>
            <View style={s.connector}>
              <Text style={{ fontSize:16 }}>♥</Text>
            </View>
          </View>

          {/* ── Person 2 Form ── */}
          <View>
            <Text style={s.sectionLabel}>PERSON 2 (PARTNER)</Text>
            <View style={s.formCard}>
              <FormRow label="Name" value={p2Name} onChangeText={setP2Name} placeholder="Partner's name" />
              <View style={s.divider} />
              <FormRow label="Birth Date" value={p2DOB} onChangeText={setP2DOB} placeholder="DD/MM/YYYY" keyboardType="numeric" />
              <View style={s.divider} />
              <FormRow label="Birth Time" value={p2Time} onChangeText={setP2Time} placeholder="HH:MM AM / PM" />
              <View style={s.divider} />
              <FormRow label="Birth Place" value={p2Place} onChangeText={setP2Place} placeholder="E.g. Delhi, India" />
            </View>
          </View>

          {error ? (
            <View style={s.errorRow}>
              <Feather name="alert-circle" size={13} color="#ef4444" />
              <Text style={s.errorText}>{error}</Text>
            </View>
          ) : null}

          {/* Calculate Button */}
          <Pressable
            onPress={() => { Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium); handleCalculate(); }}
            disabled={loading}
            style={({ pressed }) => [{ opacity: pressed || loading ? 0.7 : 1 }]}
          >
            <LinearGradient
              colors={["#4f46e5","#7c3aed","#a855f7"]}
              start={{ x:0, y:0 }} end={{ x:1, y:0 }}
              style={s.calcBtn}
            >
              {loading ? (
                <ActivityIndicator color="white" size="small" />
              ) : (
                <>
                  <Text style={{ fontSize:16 }}>⚡</Text>
                  <Text style={s.calcBtnText}>Calculate Compatibility</Text>
                </>
              )}
            </LinearGradient>
          </Pressable>

          {/* ── Results ── */}
          {result && grade && (
            <>
              {/* Score banner */}
              <View style={[s.scoreBanner, { borderColor:`${grade.color}40` }]}>
                <Text style={{ fontSize:36 }}>{grade.emoji}</Text>
                <View style={{ alignItems:"center", gap:4 }}>
                  <View style={{ flexDirection:"row", alignItems:"baseline", gap:4 }}>
                    <Text style={[s.scoreTotal, { color:grade.color }]}>{result.total}</Text>
                    <Text style={s.scoreMax}>/36</Text>
                  </View>
                  <Text style={[s.gradeLabel, { color:grade.color }]}>{grade.label}</Text>
                  <Text style={s.gradeDesc}>{grade.desc}</Text>
                </View>
                {result.manglikDosha && (
                  <View style={s.manglikBadge}>
                    <Text style={s.manglikText}>Manglik Dosh</Text>
                  </View>
                )}
              </View>

              {/* Score bar */}
              <View style={s.scoreBarWrap}>
                <View style={[s.scoreBarFill, {
                  width:`${Math.round((result.total/36)*100)}%` as any,
                  backgroundColor: grade.color,
                }]} />
              </View>

              {/* 8 Koots breakdown */}
              <Text style={s.sectionLabel}>ASHTAKOOT BREAKDOWN</Text>
              <View style={s.kootGrid}>
                {KOOT_ORDER.map(key => {
                  const k = result[key];
                  const pct = k.max > 0 ? k.score / k.max : 0;
                  const kColor = k.bad ? "#ef4444"
                    : pct >= 0.8 ? "#22c55e"
                    : pct >= 0.5 ? "#fbbf24" : "#f97316";
                  return (
                    <View key={key} style={[s.kootCard, k.bad && s.kootCardBad]}>
                      <View style={{ flexDirection:"row", justifyContent:"space-between", alignItems:"center" }}>
                        <Text style={s.kootName}>{k.label}</Text>
                        <View style={[s.kootScore, { backgroundColor:`${kColor}15` }]}>
                          <Text style={[s.kootScoreText, { color:kColor }]}>{k.score}/{k.max}</Text>
                        </View>
                      </View>
                      <Text style={s.kootDetail}>{k.detail}</Text>
                      {/* Mini bar */}
                      <View style={s.kootBarBg}>
                        <View style={[s.kootBarFill, { width:`${Math.round(pct*100)}%` as any, backgroundColor:kColor }]} />
                      </View>
                    </View>
                  );
                })}
              </View>

              {/* Manglik info */}
              {result.manglikDosha && (
                <View style={s.manglikCard}>
                  <Text style={{ fontSize:16 }}>🔴</Text>
                  <View style={{ flex:1 }}>
                    <Text style={{ color:"#f97316", fontWeight:"700", fontSize:13 }}>Manglik Dosh</Text>
                    <Text style={{ color:"#64748b", fontSize:11, marginTop:3, lineHeight:17 }}>
                      One person is Manglik, the other is not. Perform Kumbh Vivah or remedies before marriage. Consult a qualified Jyotishi.
                    </Text>
                  </View>
                </View>
              )}

              {/* Disclaimer */}
              <View style={s.disclaimer}>
                <Feather name="info" size={12} color="#1e3a5f" />
                <Text style={s.disclaimerText}>
                  This Ashtakoot Milan is an estimate. Always consult a qualified Jyotishi for a complete kundli analysis before marriage.
                </Text>
              </View>
            </>
          )}

          {/* How it works (before results) */}
          {!result && (
            <View style={s.howCard}>
              <Text style={s.howTitle}>What is Ashtakoot Milan?</Text>
              <Text style={s.howBody}>
                In Vedic astrology, 8 gunas (koots) give a total of 36 points:{"\n"}
                Nadi (8) · Bhakut (7) · Gana (6) · Graha Maitri (5) · Yoni (4) · Tara (3) · Vasya (2) · Varna (1){"\n\n"}
                18+ = Acceptable{"\n"}
                24+ = Good{"\n"}
                28+ = Very Good{"\n"}
                32+ = Excellent
              </Text>
            </View>
          )}
        </ScrollView>
      </View>
    </KeyboardAvoidingView>
  );
}

const s = StyleSheet.create({
  header:     { flexDirection:"row", alignItems:"center", gap:12, paddingHorizontal:16, paddingBottom:14, borderBottomWidth:1, borderBottomColor:"rgba(255,255,255,0.05)" },
  back:       { width:36, height:36, alignItems:"center", justifyContent:"center" },
  title:      { color:"#dde8f4", fontSize:17, fontWeight:"800" },
  titleHindi: { color:"#3d5a7a", fontSize:11 },
  content:    { paddingHorizontal:16, gap:14, paddingTop:16 },
  sectionLabel: { fontSize:10, fontWeight:"800", letterSpacing:2.5, color:"#334155", marginBottom:8 },
  divider:    { height:1, backgroundColor:"#0a1828", marginHorizontal:12 },

  p1Card: {
    backgroundColor:"#040e20", borderRadius:14,
    borderWidth:1, borderColor:"rgba(245,158,11,0.2)", padding:14,
  },
  p1Avatar: {
    width:44, height:44, borderRadius:22,
    backgroundColor:"rgba(245,158,11,0.08)",
    borderWidth:1, borderColor:"rgba(245,158,11,0.2)",
    alignItems:"center", justifyContent:"center",
  },
  p1Name:   { color:"#dde8f4", fontSize:14, fontWeight:"600" },
  p1Detail: { color:"#475569", fontSize:11, marginTop:3 },

  connector: {
    width:40, height:40, borderRadius:20,
    backgroundColor:"rgba(248,113,113,0.12)",
    borderWidth:1, borderColor:"rgba(248,113,113,0.25)",
    alignItems:"center", justifyContent:"center", zIndex:1,
  },

  formCard: {
    backgroundColor:"#040e1f", borderRadius:14,
    borderWidth:1, borderColor:"rgba(255,255,255,0.07)",
  },

  errorRow: { flexDirection:"row", alignItems:"center", gap:6 },
  errorText: { color:"#ef4444", fontSize:12, flex:1 },

  calcBtn: {
    flexDirection:"row", alignItems:"center", justifyContent:"center", gap:10,
    borderRadius:14, paddingVertical:15,
  },
  calcBtnText: { color:"white", fontWeight:"800", fontSize:15 },

  scoreBanner: {
    backgroundColor:"#040e20", borderRadius:18,
    borderWidth:1, padding:20,
    alignItems:"center", gap:12,
  },
  scoreTotal:  { fontSize:44, fontWeight:"900", lineHeight:50 },
  scoreMax:    { fontSize:18, color:"#334155", lineHeight:50 },
  gradeLabel:  { fontSize:18, fontWeight:"800" },
  gradeDesc:   { color:"#64748b", fontSize:12, textAlign:"center", maxWidth:240 },
  manglikBadge:{ backgroundColor:"rgba(249,115,22,0.12)", borderRadius:8, paddingHorizontal:10, paddingVertical:4, borderWidth:1, borderColor:"rgba(249,115,22,0.3)" },
  manglikText: { color:"#f97316", fontSize:10, fontWeight:"700" },

  scoreBarWrap: { height:6, backgroundColor:"#0f1e2e", borderRadius:3, overflow:"hidden" },
  scoreBarFill: { height:6, borderRadius:3 },

  kootGrid: { gap:10 },
  kootCard: {
    backgroundColor:"#040e20", borderRadius:12,
    borderWidth:1, borderColor:"rgba(255,255,255,0.06)",
    padding:12, gap:6,
  },
  kootCardBad: { borderColor:"rgba(239,68,68,0.2)", backgroundColor:"rgba(239,68,68,0.03)" },
  kootName:   { color:"#dde8f4", fontSize:12, fontWeight:"700" },
  kootScore:  { borderRadius:8, paddingHorizontal:8, paddingVertical:2 },
  kootScoreText: { fontSize:12, fontWeight:"700" },
  kootDetail: { color:"#475569", fontSize:11 },
  kootBarBg:  { height:3, backgroundColor:"#0f1e2e", borderRadius:2, overflow:"hidden" },
  kootBarFill:{ height:3, borderRadius:2 },

  manglikCard: {
    flexDirection:"row", alignItems:"flex-start", gap:10,
    backgroundColor:"rgba(249,115,22,0.06)", borderRadius:12,
    borderWidth:1, borderColor:"rgba(249,115,22,0.2)", padding:14,
  },
  disclaimer: {
    flexDirection:"row", alignItems:"flex-start", gap:8,
    backgroundColor:"rgba(255,255,255,0.02)", borderRadius:10,
    padding:12, borderWidth:1, borderColor:"rgba(255,255,255,0.04)",
  },
  disclaimerText: { color:"#1e3a5f", fontSize:11, lineHeight:17, flex:1 },

  howCard: {
    backgroundColor:"rgba(99,102,241,0.05)", borderRadius:14,
    borderWidth:1, borderColor:"rgba(99,102,241,0.15)", padding:16,
  },
  howTitle: { color:"#a78bfa", fontSize:13, fontWeight:"700", marginBottom:8 },
  howBody:  { color:"#475569", fontSize:12, lineHeight:20 },
});

const f = StyleSheet.create({
  row:   { flexDirection:"row", alignItems:"center", paddingHorizontal:14, paddingVertical:12, gap:10 },
  label: { color:"#4b6a86", fontSize:12, fontWeight:"600", width:100, flexShrink:0 },
  input: {
    flex:1, color:"#dde8f4", fontSize:13,
    paddingVertical:4,
    borderBottomWidth:1, borderBottomColor:"rgba(255,255,255,0.04)",
  },
});
