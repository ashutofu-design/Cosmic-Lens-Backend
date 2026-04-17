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
import { useT } from "@/hooks/useT";
import { API_BASE } from "@/lib/apiConfig";
import type { BirthData } from "@/types";
import { useFeatureGate } from "@/components/FeatureGate";

type LoyaltyLevel  = "high" | "moderate" | "unstable" | "risky";
type Behavior      = "loyal" | "tempted" | "emotionally unstable" | "dual-nature";
type TimeFactor    = "temporary_phase" | "long_term_pattern";

interface LoyaltyFactors {
  venus: string; moon: string; "7th_house": string;
  rahu: string;  dasha: string; kp: string;
}
interface LoyaltyBreakdown {
  venus: number; moon: number; seventh: number;
  rahu: number;  cross: number; dasha: number;
  kp: number;    start: number;
}
interface LoyaltyResult {
  loyalty_score: number;
  loyalty_level: LoyaltyLevel;
  behavior_type: Behavior;
  time_factor:   TimeFactor;
  factors:       LoyaltyFactors;
  reasons:       string[];
  breakdown:     LoyaltyBreakdown;
}

function packPerson(bd: BirthData) {
  return {
    name: bd.name,
    day: bd.day, month: bd.month, year: bd.year,
    hour: bd.hour, minute: bd.minute, ampm: bd.ampm,
    lat: bd.lat, lon: bd.lon, tz: bd.tz, place: bd.place,
  };
}

export default function LoyaltyCheckScreen() {
  const C = useC();
  const { LockOverlay } = useFeatureGate("love_reality_full");
  const insets = useSafeAreaInsets();
  const topPad = Platform.OS === "android" ? Math.max(insets.top, 24) : insets.top;
  const isDark = C.isDark;

  const { profiles, primaryProfileId } = useUser();
  const t = useT();
  const params = useLocalSearchParams<{ partnerId?: string }>();
  const partnerId = typeof params.partnerId === "string" ? params.partnerId : null;

  const primaryProfile = profiles.find(p => p.id === primaryProfileId) ?? profiles[0] ?? null;
  const partnerProfile = partnerId ? (profiles.find(p => p.id === partnerId) ?? null) : null;

  const hasSelfKundli    = !!primaryProfile?.kundli && !!primaryProfile?.birthData;
  const hasPartnerKundli = !!partnerProfile?.kundli && !!partnerProfile?.birthData;
  const canAnalyze = hasSelfKundli && hasPartnerKundli;

  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [result, setResult] = useState<LoyaltyResult | null>(null);

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
      const resp = await fetch(`${API_BASE}/api/loyalty-check`, {
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
      setResult(json as LoyaltyResult);
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
          <LinearGradient colors={["#f97316", "#fb923c"]} start={{ x:0,y:0 }} end={{ x:1,y:1 }} style={s.heroIcon}>
            <Text style={{ fontSize: 28 }}>🛡️</Text>
          </LinearGradient>
          <Text style={[s.heroTitle, { color: textHi, fontFamily: "Nunito_700Bold" }]}>Loyalty Check</Text>
          <Text style={[s.heroSub, { color: textLo, fontFamily: "Nunito_400Regular" }]}>
            Venus · Moon · 7th House · Rahu · Dasha · KP sub-lord
          </Text>
        </View>

        {canAnalyze && (
          <View style={[s.pairCard, { backgroundColor: bgCard, borderColor: border }]}>
            <PersonChip label="You" name={primaryProfile!.name} place={primaryProfile!.birthData?.place}
              color="#f97316" textHi={textHi} textLo={textLo} bgCard2={bgCard2} border={border} />
            <View style={s.pairDivider}>
              <Text style={{ fontSize: 18 }}>🛡️</Text>
            </View>
            <PersonChip label="Partner" name={partnerProfile!.name} place={partnerProfile!.birthData?.place}
              color="#fb923c" textHi={textHi} textLo={textLo} bgCard2={bgCard2} border={border} />
          </View>
        )}

        {!canAnalyze && (
          <View style={[s.gateCard, { backgroundColor: bgCard, borderColor: border }]}>
            <View style={[s.gateIcon, { backgroundColor: "rgba(249,115,22,0.12)", borderColor: "rgba(249,115,22,0.3)" }]}>
              <Feather name="lock" size={22} color="#f97316" />
            </View>
            <Text style={[s.gateTitle, { color: textHi }]}>{t.needKundli}</Text>
            <Text style={[s.gateMsg, { color: textLo }]}>
              {!hasSelfKundli && !hasPartnerKundli
                ? t.needBothKundli
                : !hasSelfKundli
                  ? t.needKundliSub
                  : t.needPartnerKundli}
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
            <ActivityIndicator color="#f97316" size="large" />
            <Text style={[s.loadingText, { color: textHi }]}>Reading love signatures…</Text>
            <Text style={[s.loadingSub, { color: textLo }]}>
              Cross-sync · D1 · D9 · Dasha · Transits · KP
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
          />
        )}
      </ScrollView>
      {LockOverlay}
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

function levelColor(lvl: LoyaltyLevel): string {
  if (lvl === "high")     return "#22c55e";
  if (lvl === "moderate") return "#f59e0b";
  if (lvl === "unstable") return "#f97316";
  return "#ef4444";
}
function behaviorColor(b: Behavior): string {
  if (b === "loyal") return "#22c55e";
  if (b === "tempted") return "#f59e0b";
  if (b === "emotionally unstable") return "#f97316";
  return "#ef4444";
}
function behaviorEmoji(b: Behavior): string {
  if (b === "loyal") return "🛡️";
  if (b === "tempted") return "🎭";
  if (b === "emotionally unstable") return "🌊";
  return "🎲";
}

function ResultView({
  result, accent, textHi, textLo, bgCard, bgCard2, border, isDark, onReAnalyze,
}: {
  result: LoyaltyResult; accent: string; textHi: string; textLo: string;
  bgCard: string; bgCard2: string; border: string; isDark: boolean;
  onReAnalyze: () => void;
}) {
  const R = 70;
  const circ = 2 * Math.PI * R;
  const frac = Math.max(0, Math.min(1, result.loyalty_score / 100));
  const offset = circ * (1 - frac);
  const scoreCol = levelColor(result.loyalty_level);
  const behCol = behaviorColor(result.behavior_type);

  const FACTOR_ORDER: (keyof LoyaltyFactors)[] =
    ["venus", "moon", "7th_house", "rahu", "dasha", "kp"];
  const FACTOR_LBL: Record<keyof LoyaltyFactors, string> = {
    venus: "Venus · Love nature (±20)",
    moon:  "Moon · Emotional loyalty (±15)",
    "7th_house": "7th House · Commitment (±15)",
    rahu:  "Rahu · Cheating driver (−20)",
    dasha: "Dasha · Current phase (±10)",
    kp:    "KP · Sub-lord confirmation (−10)",
  };
  const FACTOR_EMOJI: Record<keyof LoyaltyFactors, string> = {
    venus:"💘", moon:"🌙", "7th_house":"🏛️", rahu:"🐉", dasha:"⏳", kp:"🔭",
  };

  const BRK: [string, number][] = [
    ["Baseline",     result.breakdown.start],
    ["Venus",        result.breakdown.venus],
    ["Moon",         result.breakdown.moon],
    ["7th House",    result.breakdown.seventh],
    ["Rahu",         result.breakdown.rahu],
    ["Cross-sync",   result.breakdown.cross],
    ["Dasha",        result.breakdown.dasha],
    ["KP sub-lord",  result.breakdown.kp],
  ];

  const timeLabel = result.time_factor === "long_term_pattern"
    ? "Long-term natal pattern"
    : "Temporary phase";
  const timeCol = result.time_factor === "long_term_pattern" ? "#ef4444" : "#f59e0b";

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
              {result.loyalty_score}
            </Text>
            <Text style={[s.scoreSub, { color: textLo }]}>loyalty</Text>
          </View>
        </View>

        <View style={[s.lvlBadge, { backgroundColor: scoreCol + "22", borderColor: scoreCol + "66" }]}>
          <Feather name="shield" size={13} color={scoreCol} />
          <Text style={{ color: scoreCol, fontFamily: "Nunito_700Bold", fontSize: 13, letterSpacing: 0.3, textTransform: "uppercase" }}>
            {result.loyalty_level}
          </Text>
        </View>

        <View style={s.metaRow}>
          <View style={[s.metaChip, { backgroundColor: behCol + "18", borderColor: behCol + "55" }]}>
            <Text style={{ fontSize: 14 }}>{behaviorEmoji(result.behavior_type)}</Text>
            <Text style={{ color: behCol, fontSize: 12, fontFamily: "Nunito_700Bold", textTransform: "capitalize" }}>
              {result.behavior_type}
            </Text>
          </View>
          <View style={[s.metaChip, { backgroundColor: timeCol + "18", borderColor: timeCol + "55" }]}>
            <Feather name="clock" size={12} color={timeCol} />
            <Text style={{ color: timeCol, fontSize: 12, fontFamily: "Nunito_700Bold" }}>
              {timeLabel}
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
              const positive = /strong|loyal|supportive|exalted|own-sign|sincere|devoted|supportive loyal|blessing|sync|anchored|no cheating|complementary|not tied/.test(lower);
              const negative = /afflict|debilit|illusion|attraction outside|cheat|unstable|drift|obsess|restless|cold|burdensome|weakened|dusthana|novelty|hidden|secret|mismatch|temptation|detachment|coldness|depress/.test(lower);
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
  heroSub: { fontSize: 12.5, letterSpacing: 0.2, textAlign: "center", maxWidth: 320 },

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

  lvlBadge: { flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 6,
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
