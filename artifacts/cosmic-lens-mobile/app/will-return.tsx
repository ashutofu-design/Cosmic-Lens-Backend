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

type Chance      = "unlikely" | "possible" | "strong" | "very strong";
type ReunionType = "temporary" | "long-term" | "unstable";
type Initiator   = "person A" | "person B" | "mutual";

interface ReturnFactors {
  dasha: string; transit: string; love_houses: string;
  separation_houses: string; kp: string;
}
interface ReturnBreakdown {
  start: number; dasha: number; transit: number;
  love: number; separation: number; kp: number; synastry: number;
}
interface ReturnResult {
  return_probability: number;
  return_chance:      Chance;
  time_window:        string;
  reunion_type:       ReunionType;
  initiator:          Initiator;
  factors:            ReturnFactors;
  reasons:            string[];
  breakdown:          ReturnBreakdown;
}

function packPerson(bd: BirthData) {
  return {
    name: bd.name,
    day: bd.day, month: bd.month, year: bd.year,
    hour: bd.hour, minute: bd.minute, ampm: bd.ampm,
    lat: bd.lat, lon: bd.lon, tz: bd.tz, place: bd.place,
  };
}

export default function WillReturnScreen() {
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
  const [result, setResult] = useState<ReturnResult | null>(null);

  const accent = isDark ? "#f59e0b" : "#7C3AED";
  const textHi = isDark ? "#fff" : "#0F172A";
  const textLo = isDark ? "rgba(203,213,225,0.7)" : "#64748B";
  const bgCard = isDark ? "rgba(14,22,42,0.72)" : "rgba(255,255,255,0.95)";
  const bgCard2 = isDark ? "#1A2135" : "#EEF0F4";
  const border  = isDark ? "rgba(255,255,255,0.08)" : "rgba(15,23,42,0.08)";

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
      const resp = await fetch(`${API_BASE}/api/will-return`, {
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
      setResult(json as ReturnResult);
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
        <View style={s.hero}>
          <LinearGradient colors={["#f59e0b", "#fbbf24"]} start={{ x:0,y:0 }} end={{ x:1,y:1 }} style={s.heroIcon}>
            <Text style={{ fontSize: 28 }}>🪃</Text>
          </LinearGradient>
          <Text style={[s.heroTitle, { color: textHi, fontFamily: "Nunito_700Bold" }]}>Will They Return?</Text>
          <Text style={[s.heroSub, { color: textLo, fontFamily: "Nunito_400Regular" }]}>
            Reading your chart · Dasha · Transit · Love vs Separation · KP
          </Text>
        </View>

        {canAnalyze && (
          <View style={[s.pairCard, { backgroundColor: bgCard, borderColor: border }]}>
            <PersonChip label="You (Primary)" name={primaryProfile!.name} place={primaryProfile!.birthData?.place}
              color="#f59e0b" textHi={textHi} textLo={textLo} bgCard2={bgCard2} border={border} />
            <View style={s.pairDivider}>
              <Text style={{ fontSize: 18 }}>🪃</Text>
            </View>
            <PersonChip label="Them (Ref.)" name={partnerProfile!.name} place={partnerProfile!.birthData?.place}
              color="#fbbf24" textHi={textHi} textLo={textLo} bgCard2={bgCard2} border={border} />
          </View>
        )}

        {!canAnalyze && (
          <View style={[s.gateCard, { backgroundColor: bgCard, borderColor: border }]}>
            <View style={[s.gateIcon, { backgroundColor: "rgba(245,158,11,0.12)", borderColor: "rgba(245,158,11,0.3)" }]}>
              <Feather name="lock" size={22} color="#f59e0b" />
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

        {canAnalyze && loading && (
          <View style={[s.loadingCard, { backgroundColor: bgCard, borderColor: border }]}>
            <ActivityIndicator color="#f59e0b" size="large" />
            <Text style={[s.loadingText, { color: textHi }]}>Reading return signals…</Text>
            <Text style={[s.loadingSub, { color: textLo }]}>
              Your Dasha · Live Transits · 5/7/11 · 6/8/12 · KP
            </Text>
          </View>
        )}

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

        {canAnalyze && !loading && result && (
          <ResultView
            result={result} accent={accent} textHi={textHi} textLo={textLo}
            bgCard={bgCard} bgCard2={bgCard2} border={border} isDark={isDark}
            onReAnalyze={runAnalysis}
            A_name={primaryProfile!.name}
            B_name={partnerProfile!.name}
          />
        )}
      </ScrollView>
    </CosmicBg>
  );
}

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

function chanceColor(c: Chance) {
  if (c === "very strong") return "#22c55e";
  if (c === "strong")      return "#84cc16";
  if (c === "possible")    return "#f59e0b";
  return "#ef4444";
}
function reunionColor(r: ReunionType) {
  if (r === "long-term") return "#22c55e";
  if (r === "temporary") return "#f59e0b";
  return "#ef4444";
}
function reunionEmoji(r: ReunionType) {
  if (r === "long-term") return "💞";
  if (r === "temporary") return "⏳";
  return "🌗";
}

function ResultView({
  result, accent, textHi, textLo, bgCard, bgCard2, border, isDark, onReAnalyze, A_name, B_name,
}: {
  result: ReturnResult; accent: string; textHi: string; textLo: string;
  bgCard: string; bgCard2: string; border: string; isDark: boolean;
  onReAnalyze: () => void; A_name: string; B_name: string;
}) {
  const R = 70;
  const circ = 2 * Math.PI * R;
  const frac = Math.max(0, Math.min(1, result.return_probability / 100));
  const offset = circ * (1 - frac);
  const scoreCol = chanceColor(result.return_chance);
  const reuCol = reunionColor(result.reunion_type);

  const FACTOR_ORDER: (keyof ReturnFactors)[] =
    ["dasha", "transit", "love_houses", "separation_houses", "kp"];
  const FACTOR_LBL: Record<keyof ReturnFactors, string> = {
    dasha: "Your Dasha (±30)",
    transit: "Live Transit (±20)",
    love_houses: "Love houses 5/7/11 (+15)",
    separation_houses: "Separation houses 6/8/12 (−25)",
    kp: "KP sub-lord (±10)",
  };
  const FACTOR_EMOJI: Record<keyof ReturnFactors, string> = {
    dasha: "⏳", transit: "🌠", love_houses: "💘", separation_houses: "🚧", kp: "🔭",
  };

  const BRK: [string, number][] = [
    ["Baseline",      result.breakdown.start],
    ["Dasha",         result.breakdown.dasha],
    ["Transit",       result.breakdown.transit],
    ["Love houses",   result.breakdown.love],
    ["Separation",    result.breakdown.separation],
    ["KP",            result.breakdown.kp],
    ["Synastry (B)",  result.breakdown.synastry],
  ];

  const initiatorLabel =
    result.initiator === "person A" ? `${A_name} reaches out`
    : result.initiator === "person B" ? `${B_name} reaches out`
    : "Mutual contact";

  return (
    <View style={{ gap: 14 }}>
      <View style={[s.resCard, { backgroundColor: bgCard, borderColor: border }]}>
        <View style={s.scoreWrap}>
          <Svg width={170} height={170}>
            <Circle cx={85} cy={85} r={R} stroke={bgCard2} strokeWidth={12} fill="none" />
            <Circle cx={85} cy={85} r={R} stroke={scoreCol} strokeWidth={12} fill="none"
              strokeDasharray={`${circ} ${circ}`} strokeDashoffset={offset}
              strokeLinecap="round" transform="rotate(-90 85 85)" />
          </Svg>
          <View style={s.scoreTextWrap}>
            <Text style={[s.scoreText, { color: scoreCol, fontFamily: "Nunito_700Bold" }]}>
              {result.return_probability}
            </Text>
            <Text style={[s.scoreSub, { color: textLo }]}>return chance</Text>
          </View>
        </View>

        <View style={[s.chanceBadge, { backgroundColor: scoreCol + "22", borderColor: scoreCol + "66" }]}>
          <Feather name="target" size={13} color={scoreCol} />
          <Text style={{ color: scoreCol, fontFamily: "Nunito_700Bold", fontSize: 13, letterSpacing: 0.3, textTransform: "uppercase" }}>
            {result.return_chance}
          </Text>
        </View>

        <View style={s.metaRow}>
          <View style={[s.metaChip, { backgroundColor: reuCol + "18", borderColor: reuCol + "55" }]}>
            <Text style={{ fontSize: 13 }}>{reunionEmoji(result.reunion_type)}</Text>
            <Text style={{ color: reuCol, fontSize: 12, fontFamily: "Nunito_700Bold", textTransform: "capitalize" }}>
              {result.reunion_type}
            </Text>
          </View>
          <View style={[s.metaChip, { backgroundColor: accent + "18", borderColor: accent + "55" }]}>
            <Feather name="clock" size={12} color={accent} />
            <Text style={{ color: accent, fontSize: 12, fontFamily: "Nunito_700Bold" }}>
              {result.time_window}
            </Text>
          </View>
          <View style={[s.metaChip, { backgroundColor: "#a855f7" + "18", borderColor: "#a855f7" + "55" }]}>
            <Feather name="user" size={12} color="#a855f7" />
            <Text style={{ color: "#a855f7", fontSize: 12, fontFamily: "Nunito_700Bold" }}>
              {initiatorLabel}
            </Text>
          </View>
        </View>
      </View>

      <View style={[s.resCard, { backgroundColor: bgCard, borderColor: border }]}>
        <Text style={[s.sectionTitle, { color: textHi }]}>Factor summary</Text>
        <View style={{ gap: 10 }}>
          {FACTOR_ORDER.map((k) => (
            <View key={k} style={[s.factorRow, { backgroundColor: bgCard2, borderColor: border }]}>
              <Text style={{ fontSize: 18 }}>{FACTOR_EMOJI[k]}</Text>
              <View style={{ flex: 1, minWidth: 0 }}>
                <Text style={{ color: textHi, fontSize: 12.5, fontFamily: "Nunito_700Bold" }}>
                  {FACTOR_LBL[k]}
                </Text>
                <Text style={{ color: textLo, fontSize: 11.5, fontFamily: "Nunito_500Medium", marginTop: 2, lineHeight: 16 }}>
                  {result.factors[k]}
                </Text>
              </View>
            </View>
          ))}
        </View>
      </View>

      <View style={[s.resCard, { backgroundColor: bgCard, borderColor: border }]}>
        <Text style={[s.sectionTitle, { color: textHi }]}>Point breakdown</Text>
        {BRK.map(([lbl, val]) => {
          const isBase = lbl === "Baseline";
          const col = isBase ? "#64748B"
            : val > 0 ? "#22c55e"
            : val < 0 ? "#ef4444"
            : "#64748B";
          return (
            <View key={lbl} style={s.brkRow}>
              <Text style={[s.brkLbl, { color: textLo }]}>{lbl}</Text>
              <View style={[s.brkVal, { backgroundColor: col + "22", borderColor: col + "55" }]}>
                <Text style={{ color: col, fontSize: 12.5, fontFamily: "Nunito_700Bold" }}>
                  {isBase ? val : val > 0 ? `+${val}` : val}
                </Text>
              </View>
            </View>
          );
        })}
      </View>

      {result.reasons.length > 0 && (
        <View style={[s.resCard, { backgroundColor: bgCard, borderColor: border }]}>
          <Text style={[s.sectionTitle, { color: textHi }]}>
            Astrological reasoning ({result.reasons.length})
          </Text>
          <View style={{ gap: 8 }}>
            {result.reasons.map((r, i) => {
              const lower = r.toLowerCase();
              const positive = /revival|reconnection|reunion|supports|well-placed|confirmed|pulls partner|affection window|return confirmed|opportunity|supports reunion|sudden\/unexpected|magnetic pull|strong love/.test(lower);
              const negative = /separation|cut-off|delay|karmic test|detachment|blocks|hinder|dusthana|continues|split|rejects|impulsive friction|bleeds into/.test(lower);
              const col = positive && !negative ? "#22c55e" : negative ? "#ef4444" : accent;
              return (
                <View key={i} style={[s.reasonItem, { backgroundColor: bgCard2, borderLeftColor: col }]}>
                  <Text style={{ color: textHi, fontSize: 12.5, lineHeight: 18, fontFamily: "Nunito_500Medium" }}>{r}</Text>
                </View>
              );
            })}
          </View>
        </View>
      )}

      <Pressable onPress={onReAnalyze} style={{ marginTop: 4 }}>
        <View style={[s.cta, { backgroundColor: accent }]}>
          <Feather name="refresh-cw" size={16} color="#fff" />
          <Text style={s.ctaText}>Re-analyze</Text>
        </View>
      </Pressable>
    </View>
  );
}

const s = StyleSheet.create({
  topBar: { position: "absolute", top: 0, left: 0, right: 0, zIndex: 20, paddingHorizontal: 16, paddingBottom: 8 },
  backBtn: { alignSelf: "flex-start" },
  backCircle: { width: 40, height: 40, borderRadius: 20, alignItems: "center", justifyContent: "center", borderWidth: 1 },

  hero: { alignItems: "center", marginBottom: 18, gap: 8 },
  heroIcon: { width: 64, height: 64, borderRadius: 32, alignItems: "center", justifyContent: "center",
    borderWidth: 2, borderColor: "rgba(255,255,255,0.15)" },
  heroTitle: { fontSize: 24, letterSpacing: -0.4 },
  heroSub: { fontSize: 12.5, letterSpacing: 0.2, textAlign: "center", maxWidth: 330 },

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
  loadingSub: { fontSize: 12, fontFamily: "Nunito_500Medium", textAlign: "center" },

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

  chanceBadge: { flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 6,
    alignSelf: "center", paddingHorizontal: 14, paddingVertical: 7, borderRadius: 999, borderWidth: 1 },

  metaRow: { flexDirection: "row", justifyContent: "center", flexWrap: "wrap", gap: 8, marginTop: 12 },
  metaChip: { flexDirection: "row", alignItems: "center", gap: 6,
    paddingHorizontal: 12, paddingVertical: 7, borderRadius: 10, borderWidth: 1 },

  sectionTitle: { fontSize: 13, marginBottom: 10, fontFamily: "Nunito_700Bold", letterSpacing: 0.3, textTransform: "uppercase" },

  factorRow: { flexDirection: "row", alignItems: "flex-start", gap: 10,
    padding: 12, borderRadius: 12, borderWidth: 1 },

  brkRow: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", marginBottom: 8 },
  brkLbl: { fontSize: 12.5, fontFamily: "Nunito_600SemiBold", flex: 1 },
  brkVal: { paddingHorizontal: 10, paddingVertical: 4, borderRadius: 8, borderWidth: 1, minWidth: 54, alignItems: "center" },

  reasonItem: { paddingVertical: 9, paddingHorizontal: 12, borderRadius: 10, borderLeftWidth: 3 },
});
