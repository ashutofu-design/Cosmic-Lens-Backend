import { Feather } from "@expo/vector-icons";
import * as Haptics from "expo-haptics";
import { LinearGradient } from "expo-linear-gradient";
import { router, useLocalSearchParams } from "expo-router";
import React, { useEffect, useRef, useState } from "react";
import {
  ActivityIndicator, Platform, Pressable, ScrollView, StyleSheet, Text, View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import Svg, { Circle } from "react-native-svg";
import { CosmicBg } from "@/components/CosmicBg";
import { useC } from "@/context/ThemeContext";
import { useUser } from "@/context/UserContext";
import { API_BASE } from "@/lib/apiConfig";
import type { BirthData } from "@/types";

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

function packPerson(bd: BirthData) {
  return {
    name: bd.name,
    day: bd.day, month: bd.month, year: bd.year,
    hour: bd.hour, minute: bd.minute, ampm: bd.ampm,
    lat: bd.lat, lon: bd.lon, tz: bd.tz, place: bd.place,
  };
}

export default function LoveCompatibilityScreen() {
  const C = useC();
  const insets = useSafeAreaInsets();
  const topPad = Platform.OS === "android" ? Math.max(insets.top, 24) : insets.top;
  const isDark = C.isDark;

  const { profiles, primaryProfileId } = useUser();
  const params = useLocalSearchParams<{ partnerId?: string }>();
  const partnerId = typeof params.partnerId === "string" ? params.partnerId : null;

  const primaryProfile = profiles.find(p => p.id === primaryProfileId) ?? profiles[0] ?? null;
  const partnerProfile = partnerId ? (profiles.find(p => p.id === partnerId) ?? null) : null;

  const hasSelfKundli    = !!primaryProfile?.kundli && !!primaryProfile?.birthData;
  const hasPartnerKundli = !!partnerProfile?.kundli && !!partnerProfile?.birthData;
  const canAnalyze = hasSelfKundli && hasPartnerKundli;

  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [result, setResult] = useState<Result | null>(null);

  const accent = isDark ? "#f59e0b" : "#7C3AED";
  const textHi = isDark ? "#fff" : "#0F172A";
  const textLo = isDark ? "rgba(203,213,225,0.7)" : "#64748B";
  const bgCard = isDark ? "rgba(14,22,42,0.72)" : "rgba(255,255,255,0.95)";
  const bgCard2 = isDark ? "#1A2135" : "#EEF0F4";
  const border  = isDark ? "rgba(255,255,255,0.08)" : "rgba(15,23,42,0.08)";

  // Auto-analyze on mount when both kundlis are ready
  const didRun = useRef(false);
  useEffect(() => {
    if (didRun.current) return;
    if (!canAnalyze) return;
    didRun.current = true;
    runAnalysis();
  }, [canAnalyze]);

  async function runAnalysis() {
    if (!primaryProfile?.birthData || !partnerProfile?.birthData) return;
    setErr(null); setResult(null); setLoading(true);
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    try {
      const ctrl = new AbortController();
      const timer = setTimeout(() => ctrl.abort(), 30000);
      const resp = await fetch(`${API_BASE}/api/love-compatibility`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          p1: packPerson(primaryProfile.birthData),
          p2: packPerson(partnerProfile.birthData),
        }),
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

      <ScrollView
        contentContainerStyle={{
          paddingTop: topPad + 60,
          paddingBottom: insets.bottom + 40,
          paddingHorizontal: 18,
        }}
        showsVerticalScrollIndicator={false}
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

        {/* Pair summary card (always visible when both kundlis present) */}
        {canAnalyze && (
          <View style={[s.pairCard, { backgroundColor: bgCard, borderColor: border }]}>
            <PersonChip label="You" name={primaryProfile!.name} place={primaryProfile!.birthData?.place}
              color="#ec4899" textHi={textHi} textLo={textLo} bgCard2={bgCard2} border={border} />
            <View style={s.pairDivider}>
              <Text style={{ fontSize: 18 }}>💞</Text>
            </View>
            <PersonChip label="Partner" name={partnerProfile!.name} place={partnerProfile!.birthData?.place}
              color="#a855f7" textHi={textHi} textLo={textLo} bgCard2={bgCard2} border={border} />
          </View>
        )}

        {/* Gate (fallback) — should rarely be seen since Relationship blocks */}
        {!canAnalyze && (
          <View style={[s.gateCard, { backgroundColor: bgCard, borderColor: border }]}>
            <View style={[s.gateIcon, { backgroundColor: "rgba(239,68,68,0.12)", borderColor: "rgba(239,68,68,0.3)" }]}>
              <Feather name="lock" size={22} color="#ef4444" />
            </View>
            <Text style={[s.gateTitle, { color: textHi }]}>Kundli required</Text>
            <Text style={[s.gateMsg, { color: textLo }]}>
              {!hasSelfKundli && !hasPartnerKundli
                ? "Both your and your partner's kundli must be saved first."
                : !hasSelfKundli
                  ? "Your kundli is not ready yet."
                  : !partnerId
                    ? "Please select a partner from the Relationship screen."
                    : `Partner's kundli is not ready yet.`}
            </Text>
            <Pressable onPress={() => router.replace("/relationship" as any)} style={{ marginTop: 14, width: "100%" }}>
              <View style={[s.cta, { backgroundColor: accent }]}>
                <Feather name="heart" size={16} color="#fff" />
                <Text style={s.ctaText}>Go to Relationship</Text>
              </View>
            </Pressable>
          </View>
        )}

        {/* Loading */}
        {canAnalyze && loading && (
          <View style={[s.loadingCard, { backgroundColor: bgCard, borderColor: border }]}>
            <ActivityIndicator color={accent} size="large" />
            <Text style={[s.loadingText, { color: textHi }]}>Reading both kundlis…</Text>
            <Text style={[s.loadingSub, { color: textLo }]}>
              D1 + D9 + Dashas + Live Transits
            </Text>
          </View>
        )}

        {/* Error */}
        {canAnalyze && !loading && err && (
          <View style={[s.errCard, { backgroundColor: bgCard, borderColor: "#ef4444" }]}>
            <Feather name="alert-circle" size={22} color="#ef4444" />
            <Text style={[s.errText, { color: textHi }]}>{err}</Text>
            <Pressable onPress={runAnalysis} style={{ width: "100%" }}>
              <View style={[s.cta, { backgroundColor: accent }]}>
                <Feather name="refresh-cw" size={16} color="#fff" />
                <Text style={s.ctaText}>Retry</Text>
              </View>
            </Pressable>
          </View>
        )}

        {/* Result */}
        {canAnalyze && !loading && result && (
          <ResultView
            result={result} accent={accent} textHi={textHi} textLo={textLo}
            bgCard={bgCard} bgCard2={bgCard2} border={border} isDark={isDark}
            onReAnalyze={runAnalysis}
          />
        )}
      </ScrollView>
    </CosmicBg>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
function PersonChip({
  label, name, place, color, textHi, textLo, bgCard2, border,
}: {
  label: string; name: string; place?: string; color: string;
  textHi: string; textLo: string; bgCard2: string; border: string;
}) {
  return (
    <View style={[s.personChip, { backgroundColor: bgCard2, borderColor: border }]}>
      <LinearGradient colors={[color, color + "aa"]} start={{ x:0,y:0 }} end={{ x:1,y:1 }}
        style={s.personChipBadge}>
        <Text style={{ fontSize: 14 }}>👤</Text>
      </LinearGradient>
      <View style={{ flex: 1, minWidth: 0 }}>
        <Text style={[s.personChipLbl, { color: textLo }]}>{label}</Text>
        <Text style={[s.personChipName, { color: textHi }]} numberOfLines={1}>{name}</Text>
        {place ? (
          <Text style={[s.personChipPlace, { color: textLo }]} numberOfLines={1}>
            <Feather name="map-pin" size={9} color={textLo} /> {place}
          </Text>
        ) : null}
      </View>
    </View>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
function ResultView({
  result, accent, textHi, textLo, bgCard, bgCard2, border, isDark, onReAnalyze,
}: {
  result: Result; accent: string; textHi: string; textLo: string;
  bgCard: string; bgCard2: string; border: string; isDark: boolean;
  onReAnalyze: () => void;
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

      <Pressable onPress={onReAnalyze} style={{ marginTop: 4 }}>
        <View style={[s.cta, { backgroundColor: accent }]}>
          <Feather name="refresh-cw" size={16} color="#fff" />
          <Text style={s.ctaText}>Re-analyze</Text>
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

  hero: { alignItems: "center", marginBottom: 18, gap: 8 },
  heroIcon: { width: 64, height: 64, borderRadius: 32, alignItems: "center", justifyContent: "center",
    borderWidth: 2, borderColor: "rgba(255,255,255,0.15)" },
  heroTitle: { fontSize: 24, letterSpacing: -0.4 },
  heroSub: { fontSize: 12.5, letterSpacing: 0.2 },

  pairCard: { flexDirection: "row", alignItems: "stretch", gap: 8,
    borderRadius: 18, borderWidth: 1, padding: 10, marginBottom: 14 },
  pairDivider: { width: 30, alignItems: "center", justifyContent: "center" },
  personChip: { flex: 1, flexDirection: "row", alignItems: "center", gap: 10,
    padding: 10, borderRadius: 12, borderWidth: 1, minWidth: 0 },
  personChipBadge: { width: 32, height: 32, borderRadius: 16, alignItems: "center", justifyContent: "center" },
  personChipLbl: { fontSize: 10, fontFamily: "Nunito_600SemiBold", letterSpacing: 0.4, textTransform: "uppercase" },
  personChipName: { fontSize: 13.5, fontFamily: "Nunito_700Bold", marginTop: 1 },
  personChipPlace: { fontSize: 10.5, fontFamily: "Nunito_500Medium", marginTop: 1 },

  gateCard: { alignItems: "center", padding: 22, borderRadius: 18, borderWidth: 1, gap: 8 },
  gateIcon: { width: 56, height: 56, borderRadius: 28, alignItems: "center", justifyContent: "center",
    borderWidth: 1, marginBottom: 6 },
  gateTitle: { fontSize: 17, fontFamily: "Nunito_700Bold" },
  gateMsg: { fontSize: 13, textAlign: "center", lineHeight: 19, fontFamily: "Nunito_500Medium" },

  loadingCard: { alignItems: "center", padding: 30, borderRadius: 18, borderWidth: 1, gap: 12 },
  loadingText: { fontSize: 15, fontFamily: "Nunito_700Bold", marginTop: 4 },
  loadingSub: { fontSize: 12, fontFamily: "Nunito_500Medium" },

  errCard: { alignItems: "center", padding: 20, borderRadius: 18, borderWidth: 1, gap: 10 },
  errText: { fontSize: 13, textAlign: "center", fontFamily: "Nunito_500Medium" },

  cta: { flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 8,
    paddingVertical: 14, borderRadius: 12 },
  ctaText: { color: "#fff", fontSize: 14.5, fontFamily: "Nunito_700Bold", letterSpacing: 0.3 },

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
