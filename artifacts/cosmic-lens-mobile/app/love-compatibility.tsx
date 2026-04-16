import { Feather } from "@expo/vector-icons";
import * as Haptics from "expo-haptics";
import { LinearGradient } from "expo-linear-gradient";
import { router } from "expo-router";
import React, { useRef, useState } from "react";
import {
  ActivityIndicator, Animated, KeyboardAvoidingView, Platform, Pressable,
  ScrollView, StyleSheet, Text, TextInput, View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import Svg, { Circle } from "react-native-svg";
import { CosmicBg } from "@/components/CosmicBg";
import { useC } from "@/context/ThemeContext";
import { API_BASE } from "@/lib/apiConfig";

// ── 15 common Indian cities with lat/lon (tz always 5.5) ─────────────────────
const CITIES: { name: string; lat: number; lon: number; tz: number }[] = [
  { name: "Delhi",      lat: 28.6139, lon: 77.2090, tz: 5.5 },
  { name: "Mumbai",     lat: 19.0760, lon: 72.8777, tz: 5.5 },
  { name: "Bangalore",  lat: 12.9716, lon: 77.5946, tz: 5.5 },
  { name: "Kolkata",    lat: 22.5726, lon: 88.3639, tz: 5.5 },
  { name: "Chennai",    lat: 13.0827, lon: 80.2707, tz: 5.5 },
  { name: "Hyderabad",  lat: 17.3850, lon: 78.4867, tz: 5.5 },
  { name: "Pune",       lat: 18.5204, lon: 73.8567, tz: 5.5 },
  { name: "Ahmedabad",  lat: 23.0225, lon: 72.5714, tz: 5.5 },
  { name: "Jaipur",     lat: 26.9124, lon: 75.7873, tz: 5.5 },
  { name: "Lucknow",    lat: 26.8467, lon: 80.9462, tz: 5.5 },
  { name: "Patna",      lat: 25.5941, lon: 85.1376, tz: 5.5 },
  { name: "Chandigarh", lat: 30.7333, lon: 76.7794, tz: 5.5 },
  { name: "Varanasi",   lat: 25.3176, lon: 82.9739, tz: 5.5 },
  { name: "Bhopal",     lat: 23.2599, lon: 77.4126, tz: 5.5 },
  { name: "Nagpur",     lat: 21.1458, lon: 79.0882, tz: 5.5 },
];

interface PersonForm {
  name: string;
  day: string; month: string; year: string;
  hour: string; minute: string; ampm: "AM" | "PM";
  cityIdx: number;
}

interface Breakdown {
  emotional: number; attraction: number; communication: number;
  karmic: number; stability: number; dasha_transit: number; dosha_severity: number;
}
interface Factors {
  emotional: string; attraction: string; communication: string;
  karmic: string; stability: string;
}
interface Result {
  score: number;
  factors: Factors;
  reasons: string[];
  breakdown: Breakdown;
}

const emptyPerson = (): PersonForm => ({
  name: "", day: "", month: "", year: "",
  hour: "", minute: "", ampm: "AM", cityIdx: 0,
});

export default function LoveCompatibilityScreen() {
  const C = useC();
  const insets = useSafeAreaInsets();
  const topPad = Platform.OS === "android" ? Math.max(insets.top, 24) : insets.top;
  const isDark = C.isDark;

  const [p1, setP1] = useState<PersonForm>(emptyPerson());
  const [p2, setP2] = useState<PersonForm>(emptyPerson());
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [result, setResult] = useState<Result | null>(null);

  const accent = isDark ? "#f59e0b" : "#7C3AED";
  const textHi = isDark ? "#fff" : "#0F172A";
  const textLo = isDark ? "rgba(203,213,225,0.7)" : "#64748B";
  const bgCard = isDark ? "rgba(14,22,42,0.72)" : "rgba(255,255,255,0.95)";
  const bgCard2 = isDark ? "#1A2135" : "#EEF0F4";
  const border  = isDark ? "rgba(255,255,255,0.08)" : "rgba(15,23,42,0.08)";

  function valid(p: PersonForm): boolean {
    const d = +p.day, mo = +p.month, y = +p.year, h = +p.hour, mi = +p.minute;
    return !!p.name.trim() && d>=1&&d<=31 && mo>=1&&mo<=12 && y>=1900&&y<=2100
        && h>=1&&h<=12 && mi>=0&&mi<=59;
  }

  async function analyze() {
    if (!valid(p1) || !valid(p2)) {
      setErr("Please fill both partners' details correctly.");
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
      return;
    }
    setErr(null); setResult(null); setLoading(true);
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);

    const pack = (p: PersonForm) => {
      const c = CITIES[p.cityIdx];
      return {
        name: p.name.trim(),
        day: +p.day, month: +p.month, year: +p.year,
        hour: +p.hour, minute: +p.minute, ampm: p.ampm,
        lat: c.lat, lon: c.lon, tz: c.tz, place: c.name,
      };
    };

    try {
      const ctrl = new AbortController();
      const timer = setTimeout(() => ctrl.abort(), 30000);
      const resp = await fetch(`${API_BASE}/api/love-compatibility`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ p1: pack(p1), p2: pack(p2) }),
        signal: ctrl.signal,
      });
      clearTimeout(timer);
      const json = await resp.json();
      if (!resp.ok || json.error) throw new Error(json.error || "Analysis failed");
      setResult(json as Result);
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
    } catch (e: any) {
      setErr(e?.message || "Could not analyze. Please try again.");
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
    } finally {
      setLoading(false);
    }
  }

  function reset() {
    setResult(null); setErr(null);
  }

  return (
    <CosmicBg>
      <View style={[s.topBar, { paddingTop: topPad + 8 }]}>
        <Pressable
          onPress={() => { Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light); router.back(); }}
          style={s.backBtn}
        >
          <View style={[s.backCircle, {
            backgroundColor: isDark ? "rgba(255,255,255,0.08)" : "rgba(0,0,0,0.05)",
            borderColor: border,
          }]}>
            <Feather name="arrow-left" size={20} color={textHi} />
          </View>
        </Pressable>
      </View>

      <KeyboardAvoidingView
        behavior={Platform.OS === "ios" ? "padding" : undefined}
        style={{ flex: 1 }}
      >
        <ScrollView
          contentContainerStyle={{ paddingTop: topPad + 60, paddingBottom: insets.bottom + 40, paddingHorizontal: 18 }}
          showsVerticalScrollIndicator={false}
          keyboardShouldPersistTaps="handled"
        >
          {/* Hero */}
          <View style={s.hero}>
            <LinearGradient colors={["#ec4899", "#f472b6"]} start={{ x:0,y:0 }} end={{ x:1,y:1 }} style={s.heroIcon}>
              <Text style={{ fontSize: 28 }}>💘</Text>
            </LinearGradient>
            <Text style={[s.heroTitle, { color: textHi, fontFamily: "Nunito_700Bold" }]}>Love Compatibility</Text>
            <Text style={[s.heroSub, { color: textLo, fontFamily: "Nunito_400Regular" }]}>
              Vedic D1 + D9 analysis with real transits
            </Text>
          </View>

          {/* Result view */}
          {result ? (
            <ResultView result={result} accent={accent} textHi={textHi} textLo={textLo}
              bgCard={bgCard} bgCard2={bgCard2} border={border} isDark={isDark} onAgain={reset} />
          ) : (
            <>
              {/* Person 1 */}
              <PersonForm label="Partner 1" emoji="👤" color="#ec4899" person={p1} setPerson={setP1}
                textHi={textHi} textLo={textLo} bgCard={bgCard} bgCard2={bgCard2} border={border} />
              {/* Person 2 */}
              <PersonForm label="Partner 2" emoji="👤" color="#a855f7" person={p2} setPerson={setP2}
                textHi={textHi} textLo={textLo} bgCard={bgCard} bgCard2={bgCard2} border={border} />

              {err && (
                <View style={[s.errBox, { borderColor: "#ef4444" }]}>
                  <Feather name="alert-circle" size={16} color="#ef4444" />
                  <Text style={{ color: "#ef4444", fontSize: 13, flex: 1, fontFamily: "Nunito_500Medium" }}>{err}</Text>
                </View>
              )}

              <Pressable onPress={analyze} disabled={loading} style={{ marginTop: 8 }}>
                <LinearGradient colors={["#ec4899", "#a855f7"]} start={{ x:0,y:0 }} end={{ x:1,y:1 }}
                  style={[s.cta, { opacity: loading ? 0.7 : 1 }]}>
                  {loading ? (
                    <ActivityIndicator color="#fff" />
                  ) : (
                    <>
                      <Feather name="heart" size={18} color="#fff" />
                      <Text style={s.ctaText}>Analyze Compatibility</Text>
                    </>
                  )}
                </LinearGradient>
              </Pressable>
            </>
          )}
        </ScrollView>
      </KeyboardAvoidingView>
    </CosmicBg>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
function PersonForm({
  label, emoji, color, person, setPerson,
  textHi, textLo, bgCard, bgCard2, border,
}: {
  label: string; emoji: string; color: string;
  person: PersonForm; setPerson: (p: PersonForm) => void;
  textHi: string; textLo: string; bgCard: string; bgCard2: string; border: string;
}) {
  const update = (patch: Partial<PersonForm>) => setPerson({ ...person, ...patch });

  return (
    <View style={[s.personCard, { backgroundColor: bgCard, borderColor: border }]}>
      <View style={s.personHead}>
        <LinearGradient colors={[color, color + "aa"]} start={{ x:0,y:0 }} end={{ x:1,y:1 }} style={s.personBadge}>
          <Text style={{ fontSize: 18 }}>{emoji}</Text>
        </LinearGradient>
        <Text style={[s.personLabel, { color: textHi, fontFamily: "Nunito_700Bold" }]}>{label}</Text>
      </View>

      <TextInput
        placeholder="Name"
        placeholderTextColor={textLo}
        value={person.name}
        onChangeText={(v) => update({ name: v })}
        style={[s.input, { color: textHi, backgroundColor: bgCard2, borderColor: border }]}
      />

      <Text style={[s.lbl, { color: textLo }]}>Date of Birth</Text>
      <View style={s.row3}>
        <TextInput placeholder="DD" placeholderTextColor={textLo} value={person.day}
          onChangeText={(v) => update({ day: v.replace(/[^\d]/g, "").slice(0,2) })}
          keyboardType="number-pad"
          style={[s.input, s.inputSm, { color: textHi, backgroundColor: bgCard2, borderColor: border }]} />
        <TextInput placeholder="MM" placeholderTextColor={textLo} value={person.month}
          onChangeText={(v) => update({ month: v.replace(/[^\d]/g, "").slice(0,2) })}
          keyboardType="number-pad"
          style={[s.input, s.inputSm, { color: textHi, backgroundColor: bgCard2, borderColor: border }]} />
        <TextInput placeholder="YYYY" placeholderTextColor={textLo} value={person.year}
          onChangeText={(v) => update({ year: v.replace(/[^\d]/g, "").slice(0,4) })}
          keyboardType="number-pad"
          style={[s.input, s.inputSm, { color: textHi, backgroundColor: bgCard2, borderColor: border }]} />
      </View>

      <Text style={[s.lbl, { color: textLo }]}>Time of Birth</Text>
      <View style={s.row3}>
        <TextInput placeholder="HH" placeholderTextColor={textLo} value={person.hour}
          onChangeText={(v) => update({ hour: v.replace(/[^\d]/g, "").slice(0,2) })}
          keyboardType="number-pad"
          style={[s.input, s.inputSm, { color: textHi, backgroundColor: bgCard2, borderColor: border }]} />
        <TextInput placeholder="MM" placeholderTextColor={textLo} value={person.minute}
          onChangeText={(v) => update({ minute: v.replace(/[^\d]/g, "").slice(0,2) })}
          keyboardType="number-pad"
          style={[s.input, s.inputSm, { color: textHi, backgroundColor: bgCard2, borderColor: border }]} />
        <View style={[s.ampmWrap, { backgroundColor: bgCard2, borderColor: border }]}>
          {(["AM","PM"] as const).map((ap) => (
            <Pressable key={ap} onPress={() => update({ ampm: ap })}
              style={[s.ampmBtn, person.ampm === ap && { backgroundColor: color }]}>
              <Text style={{ color: person.ampm === ap ? "#fff" : textLo, fontSize: 13, fontFamily: "Nunito_600SemiBold" }}>{ap}</Text>
            </Pressable>
          ))}
        </View>
      </View>

      <Text style={[s.lbl, { color: textLo }]}>Place of Birth</Text>
      <ScrollView horizontal showsHorizontalScrollIndicator={false}
        contentContainerStyle={{ gap: 8, paddingVertical: 2 }}>
        {CITIES.map((c, i) => (
          <Pressable key={c.name} onPress={() => update({ cityIdx: i })}
            style={[s.cityChip, {
              backgroundColor: person.cityIdx === i ? color : bgCard2,
              borderColor: person.cityIdx === i ? color : border,
            }]}>
            <Text style={{ color: person.cityIdx === i ? "#fff" : textHi, fontSize: 12.5, fontFamily: "Nunito_600SemiBold" }}>
              {c.name}
            </Text>
          </Pressable>
        ))}
      </ScrollView>
    </View>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
function ResultView({
  result, accent, textHi, textLo, bgCard, bgCard2, border, isDark, onAgain,
}: {
  result: Result; accent: string; textHi: string; textLo: string;
  bgCard: string; bgCard2: string; border: string; isDark: boolean; onAgain: () => void;
}) {
  const R = 70;
  const circ = 2 * Math.PI * R;
  const frac = Math.max(0, Math.min(1, result.score / 100));
  const offset = circ * (1 - frac);
  const scoreColor = result.score >= 67 ? "#22c55e" : result.score >= 45 ? "#f59e0b" : "#ef4444";
  const verdict =
    result.score >= 75 ? "Excellent match" :
    result.score >= 60 ? "Strong compatibility" :
    result.score >= 45 ? "Moderate — workable" :
    result.score >= 30 ? "Challenging — needs effort" :
                          "Low compatibility";

  const FACTOR_ORDER: (keyof Factors)[] = ["emotional", "attraction", "communication", "karmic", "stability"];
  const FACTOR_EMOJI: Record<string,string> = {
    emotional: "💗", attraction: "🔥", communication: "💬", karmic: "🌀", stability: "🏛️",
  };

  return (
    <View style={{ gap: 14 }}>
      {/* Score circle */}
      <View style={[s.resCard, { backgroundColor: bgCard, borderColor: border }]}>
        <View style={s.scoreWrap}>
          <Svg width={170} height={170}>
            <Circle cx={85} cy={85} r={R} stroke={bgCard2} strokeWidth={12} fill="none" />
            <Circle cx={85} cy={85} r={R} stroke={scoreColor} strokeWidth={12} fill="none"
              strokeDasharray={`${circ} ${circ}`} strokeDashoffset={offset}
              strokeLinecap="round" transform="rotate(-90 85 85)" />
          </Svg>
          <View style={s.scoreTextWrap}>
            <Text style={[s.scoreText, { color: scoreColor, fontFamily: "Nunito_700Bold" }]}>{result.score}</Text>
            <Text style={[s.scoreSub, { color: textLo }]}>out of 100</Text>
          </View>
        </View>
        <Text style={[s.verdict, { color: textHi, fontFamily: "Nunito_700Bold" }]}>{verdict}</Text>
      </View>

      {/* Factor pills */}
      <View style={[s.resCard, { backgroundColor: bgCard, borderColor: border }]}>
        <Text style={[s.sectionTitle, { color: textHi }]}>Core factors</Text>
        <View style={s.factorGrid}>
          {FACTOR_ORDER.map((k) => {
            const v = result.factors[k];
            const col = v === "strong" ? "#22c55e" : v === "medium" ? "#f59e0b" : "#ef4444";
            return (
              <View key={k} style={[s.factorPill, { backgroundColor: bgCard2, borderColor: col + "55" }]}>
                <Text style={{ fontSize: 16 }}>{FACTOR_EMOJI[k]}</Text>
                <View style={{ flex: 1 }}>
                  <Text style={{ color: textHi, fontSize: 12.5, fontFamily: "Nunito_700Bold", textTransform: "capitalize" }}>{k}</Text>
                  <Text style={{ color: col, fontSize: 11, fontFamily: "Nunito_600SemiBold", textTransform: "capitalize" }}>{v}</Text>
                </View>
              </View>
            );
          })}
        </View>
      </View>

      {/* Breakdown bars */}
      <View style={[s.resCard, { backgroundColor: bgCard, borderColor: border }]}>
        <Text style={[s.sectionTitle, { color: textHi }]}>Section scores</Text>
        {([
          ["Emotional",     result.breakdown.emotional],
          ["Attraction",    result.breakdown.attraction],
          ["Communication", result.breakdown.communication],
          ["Karmic",        result.breakdown.karmic],
          ["Stability",     result.breakdown.stability],
          ["Dasha + Transit", result.breakdown.dasha_transit],
        ] as const).map(([lbl, val]) => {
          const col = val >= 67 ? "#22c55e" : val >= 45 ? "#f59e0b" : "#ef4444";
          return (
            <View key={lbl} style={s.barRow}>
              <Text style={[s.barLbl, { color: textLo }]}>{lbl}</Text>
              <View style={[s.barTrack, { backgroundColor: bgCard2 }]}>
                <View style={[s.barFill, { width: `${val}%`, backgroundColor: col }]} />
              </View>
              <Text style={[s.barVal, { color: textHi }]}>{val}</Text>
            </View>
          );
        })}
        {result.breakdown.dosha_severity > 0 && (
          <View style={[s.doshaRow, { borderColor: "#ef4444" + "44" }]}>
            <Feather name="alert-triangle" size={14} color="#ef4444" />
            <Text style={{ color: "#ef4444", fontSize: 12.5, fontFamily: "Nunito_600SemiBold" }}>
              Dosha penalty: −{result.breakdown.dosha_severity} pts
            </Text>
          </View>
        )}
      </View>

      {/* Reasons list */}
      <View style={[s.resCard, { backgroundColor: bgCard, borderColor: border }]}>
        <Text style={[s.sectionTitle, { color: textHi }]}>
          Astrological reasoning ({result.reasons.length})
        </Text>
        <View style={{ gap: 8 }}>
          {result.reasons.map((r, i) => {
            const lower = r.toLowerCase();
            const positive = /supporting|friendly|strong|well-placed|exalted|own-sign|blessings|graceful|magnetic|active now|harmony|warmth|durable|secured|fulfil|passion|romantic window|grounded|nurturing|clear articulate|self-cancels/.test(lower);
            const negative = /afflict|debilit|stress|dosha|weak|delay|friction|mismatch|hostile|conflict|challenging|struggl|instability|dusthana|obsess|confus|detach|manglik placement|misunderstand|disappoint|strain|test \/ delay|blunt|harsh|temper/.test(lower);
            const col = positive && !negative ? "#22c55e" : negative ? "#ef4444" : accent;
            return (
              <View key={i} style={[s.reasonItem, { backgroundColor: bgCard2, borderLeftColor: col }]}>
                <Text style={{ color: textHi, fontSize: 12.5, lineHeight: 18, fontFamily: "Nunito_500Medium" }}>{r}</Text>
              </View>
            );
          })}
        </View>
      </View>

      <Pressable onPress={onAgain} style={{ marginTop: 4 }}>
        <View style={[s.cta, { backgroundColor: accent }]}>
          <Feather name="refresh-cw" size={16} color="#fff" />
          <Text style={s.ctaText}>Analyze another pair</Text>
        </View>
      </Pressable>
    </View>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
const s = StyleSheet.create({
  topBar: { position: "absolute", top: 0, left: 0, right: 0, zIndex: 20, paddingHorizontal: 16, paddingBottom: 8 },
  backBtn: { alignSelf: "flex-start" },
  backCircle: { width: 40, height: 40, borderRadius: 20, alignItems: "center", justifyContent: "center", borderWidth: 1 },

  hero: { alignItems: "center", marginBottom: 22, gap: 8 },
  heroIcon: { width: 64, height: 64, borderRadius: 32, alignItems: "center", justifyContent: "center",
    borderWidth: 2, borderColor: "rgba(255,255,255,0.15)" },
  heroTitle: { fontSize: 24, letterSpacing: -0.4 },
  heroSub: { fontSize: 12.5, letterSpacing: 0.2 },

  personCard: { borderRadius: 18, borderWidth: 1, padding: 16, gap: 10, marginBottom: 14 },
  personHead: { flexDirection: "row", alignItems: "center", gap: 10, marginBottom: 4 },
  personBadge: { width: 36, height: 36, borderRadius: 18, alignItems: "center", justifyContent: "center" },
  personLabel: { fontSize: 16, letterSpacing: -0.2 },

  input: { borderRadius: 12, borderWidth: 1, paddingHorizontal: 14, paddingVertical: 11, fontSize: 14, fontFamily: "Nunito_500Medium" },
  inputSm: { flex: 1, textAlign: "center" },
  lbl: { fontSize: 11.5, marginTop: 4, marginBottom: -2, fontFamily: "Nunito_600SemiBold", letterSpacing: 0.3, textTransform: "uppercase" },
  row3: { flexDirection: "row", gap: 8 },

  ampmWrap: { flex: 1, flexDirection: "row", borderRadius: 12, borderWidth: 1, padding: 3 },
  ampmBtn: { flex: 1, alignItems: "center", justifyContent: "center", borderRadius: 9, paddingVertical: 7 },

  cityChip: { paddingHorizontal: 12, paddingVertical: 8, borderRadius: 10, borderWidth: 1 },

  errBox: { flexDirection: "row", alignItems: "center", gap: 8, padding: 12, borderRadius: 12,
    borderWidth: 1, backgroundColor: "rgba(239,68,68,0.08)", marginTop: 4, marginBottom: 4 },

  cta: { flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 8,
    paddingVertical: 16, borderRadius: 14 },
  ctaText: { color: "#fff", fontSize: 15, fontFamily: "Nunito_700Bold", letterSpacing: 0.3 },

  resCard: { borderRadius: 18, borderWidth: 1, padding: 16 },
  scoreWrap: { alignItems: "center", justifyContent: "center", marginBottom: 10 },
  scoreTextWrap: { position: "absolute", alignItems: "center" },
  scoreText: { fontSize: 42, letterSpacing: -1 },
  scoreSub: { fontSize: 11, fontFamily: "Nunito_500Medium", letterSpacing: 0.3 },
  verdict: { fontSize: 16, textAlign: "center", letterSpacing: -0.2 },

  sectionTitle: { fontSize: 13, marginBottom: 10, fontFamily: "Nunito_700Bold", letterSpacing: 0.3, textTransform: "uppercase" },

  factorGrid: { flexDirection: "row", flexWrap: "wrap", gap: 8 },
  factorPill: { flexDirection: "row", alignItems: "center", gap: 8, padding: 10, borderRadius: 12,
    borderWidth: 1, minWidth: "47%", flexGrow: 1 },

  barRow: { flexDirection: "row", alignItems: "center", gap: 10, marginBottom: 9 },
  barLbl: { width: 110, fontSize: 12, fontFamily: "Nunito_600SemiBold" },
  barTrack: { flex: 1, height: 8, borderRadius: 4, overflow: "hidden" },
  barFill: { height: "100%", borderRadius: 4 },
  barVal: { width: 28, textAlign: "right", fontSize: 12.5, fontFamily: "Nunito_700Bold" },

  doshaRow: { flexDirection: "row", alignItems: "center", gap: 6, marginTop: 4, paddingTop: 10, borderTopWidth: 1 },

  reasonItem: { paddingVertical: 9, paddingHorizontal: 12, borderRadius: 10, borderLeftWidth: 3 },
});
