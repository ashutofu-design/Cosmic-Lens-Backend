import { Feather } from "@expo/vector-icons";
import { BlurView } from "expo-blur";
import * as Haptics from "expo-haptics";
import { LinearGradient } from "expo-linear-gradient";
import { router, useLocalSearchParams } from "expo-router";
import React, { useEffect, useRef, useState } from "react";
import {
  ActivityIndicator,
  Animated,
  Easing,
  Platform,
  Pressable,
  StyleSheet,
  Text,
  View,
} from "react-native";
import Svg, { Circle } from "react-native-svg";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { CosmicBg } from "@/components/CosmicBg";
import { LoveRealityToolResultPanel } from "@/components/loveReality/LoveRealityToolResultPanel";
import { useFeatureGate } from "@/components/FeatureGate";
import { useC } from "@/context/ThemeContext";
import { useUser } from "@/context/UserContext";
import { useT } from "@/hooks/useT";
import { API_BASE } from "@/lib/apiConfig";
import {
  mapLoveRealityResult,
  type LoveRealityBasicDisplay,
  type LoveRealityToolKey,
} from "@/lib/loveRealityToolMappers";
import { LOVE_REALITY_PRO_UI_PRICING } from "@/lib/loveRealityProOffer";
import type { BirthData } from "@/types";

const AnimatedCircle = Animated.createAnimatedComponent(Circle);

export type LoveRealityToolConfig = {
  toolKey: LoveRealityToolKey;
  title: string;
  apiPath: string;
  featureGate: "love_reality_full" | "future_timeline_6m";
  loadingHint: string;
  accentGradient: [string, string];
};

function packPerson(bd: BirthData) {
  return {
    name: bd.name,
    day: bd.day,
    month: bd.month,
    year: bd.year,
    hour: bd.hour,
    minute: bd.minute,
    ampm: bd.ampm,
    lat: bd.lat,
    lon: bd.lon,
    tz: bd.tz,
    place: bd.place,
  };
}

function CircularScoreMeter({
  percent,
  isDark,
  glowColor,
  compact = false,
}: {
  percent: number;
  isDark: boolean;
  glowColor: string;
  compact?: boolean;
}) {
  const R = compact ? 54 : 88;
  const size = compact ? 128 : 200;
  const cx = size / 2;
  const circ = 2 * Math.PI * R;
  const anim = useRef(new Animated.Value(0)).current;
  const [display, setDisplay] = useState(0);

  useEffect(() => {
    anim.setValue(0);
    const sub = anim.addListener(({ value }) => setDisplay(Math.round(value)));
    Animated.timing(anim, {
      toValue: percent,
      duration: 1400,
      easing: Easing.out(Easing.cubic),
      useNativeDriver: false,
    }).start();
    return () => anim.removeListener(sub);
  }, [percent, anim]);

  const offset = anim.interpolate({
    inputRange: [0, 100],
    outputRange: [circ, 0],
  });

  const scoreColor = percent >= 67 ? "#4ade80" : percent >= 45 ? "#fbbf24" : "#f87171";

  return (
    <View style={[meterStyles.wrap, compact && meterStyles.wrapCompact]}>
      <View
        style={[
          meterStyles.glow,
          compact && meterStyles.glowCompact,
          {
            shadowColor: glowColor,
            backgroundColor: isDark ? "rgba(168,85,247,0.12)" : "rgba(124,58,237,0.08)",
          },
        ]}
      />
      <Svg width={size} height={size}>
        <Circle
          cx={cx}
          cy={cx}
          r={R}
          stroke={isDark ? "rgba(255,255,255,0.06)" : "rgba(15,23,42,0.08)"}
          strokeWidth={compact ? 10 : 14}
          fill="none"
        />
        <AnimatedCircle
          cx={cx}
          cy={cx}
          r={R}
          stroke={scoreColor}
          strokeWidth={compact ? 10 : 14}
          fill="none"
          strokeLinecap="round"
          strokeDasharray={`${circ} ${circ}`}
          strokeDashoffset={offset}
          transform={`rotate(-90 ${cx} ${cx})`}
        />
      </Svg>
      <View style={meterStyles.center}>
        <Text style={[meterStyles.pct, compact && meterStyles.pctCompact, { color: scoreColor }]}>
          {display}%
        </Text>
        <Text
          style={[
            meterStyles.lbl,
            compact && meterStyles.lblCompact,
            { color: isDark ? "rgba(203,213,225,0.55)" : "#64748B" },
          ]}
        >
          Match
        </Text>
      </View>
    </View>
  );
}

const meterStyles = StyleSheet.create({
  wrap: { width: 200, height: 200, alignItems: "center", justifyContent: "center" },
  wrapCompact: { width: 128, height: 128 },
  glow: {
    ...StyleSheet.absoluteFillObject,
    borderRadius: 100,
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.65,
    shadowRadius: 28,
    elevation: 12,
  },
  center: { position: "absolute", alignItems: "center" },
  pct: { fontSize: 44, fontFamily: "Nunito_800ExtraBold", letterSpacing: -1 },
  pctCompact: { fontSize: 28 },
  lbl: {
    fontSize: 11,
    fontFamily: "Nunito_600SemiBold",
    letterSpacing: 2,
    textTransform: "uppercase",
    marginTop: 2,
  },
  lblCompact: { fontSize: 9, letterSpacing: 1.2 },
  glowCompact: { borderRadius: 64, shadowRadius: 16 },
});

function RiskGaugeMeter({
  score,
  riskLevel,
  isDark,
  compact = false,
}: {
  score: number;
  riskLevel: string;
  isDark: boolean;
  compact?: boolean;
}) {
  const needle = useRef(new Animated.Value(0)).current;
  const [needlePct, setNeedlePct] = useState(33);

  useEffect(() => {
    const target = Math.max(0, Math.min(100, score)) / 100;
    needle.setValue(0);
    const id = needle.addListener(({ value }) => setNeedlePct(Math.round(value * 100)));
    Animated.timing(needle, {
      toValue: target,
      duration: 1200,
      easing: Easing.out(Easing.cubic),
      useNativeDriver: false,
    }).start();
    return () => needle.removeListener(id);
  }, [score, needle]);

  const zoneColor = riskLevel.includes("high")
    ? "#ef4444"
    : riskLevel.includes("low")
      ? "#22c55e"
      : "#fbbf24";

  return (
    <View style={[gaugeStyles.wrap, compact && gaugeStyles.wrapCompact]}>
      <Text style={[gaugeStyles.score, compact && gaugeStyles.scoreCompact, { color: zoneColor }]}>{score}</Text>
      <Text style={[gaugeStyles.riskTag, { color: zoneColor, borderColor: zoneColor + "55" }]}>
        {riskLevel.replace(/\s+/g, " ").toUpperCase()} RISK
      </Text>
      <View style={[gaugeStyles.track, { backgroundColor: isDark ? "rgba(255,255,255,0.06)" : "rgba(0,0,0,0.06)" }]}>
        <LinearGradient
          colors={["#22c55e", "#fbbf24", "#ef4444"]}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 0 }}
          style={gaugeStyles.fill}
        />
        <View style={[gaugeStyles.needle, { left: `${needlePct}%` }]} />
      </View>
      <View style={gaugeStyles.labels}>
        {(["LOW", "MEDIUM", "HIGH"] as const).map(z => (
          <Text key={z} style={[gaugeStyles.zoneLbl, { color: isDark ? "rgba(203,213,225,0.45)" : "#94a3b8" }]}>
            {z}
          </Text>
        ))}
      </View>
    </View>
  );
}

const gaugeStyles = StyleSheet.create({
  wrap: { width: "100%", maxWidth: 300, alignItems: "center", gap: 10 },
  wrapCompact: { maxWidth: 280, gap: 6 },
  score: { fontSize: 48, fontFamily: "Nunito_800ExtraBold", letterSpacing: -2 },
  scoreCompact: { fontSize: 34 },
  riskTag: {
    fontSize: 10,
    fontFamily: "Nunito_800ExtraBold",
    letterSpacing: 1.5,
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 8,
    borderWidth: 1,
  },
  track: { width: "100%", height: 14, borderRadius: 7, overflow: "visible", marginTop: 4 },
  fill: { ...StyleSheet.absoluteFillObject, borderRadius: 7 },
  needle: {
    position: "absolute",
    top: -5,
    width: 4,
    height: 24,
    marginLeft: -2,
    borderRadius: 2,
    backgroundColor: "#fff",
    shadowColor: "#fff",
    shadowOpacity: 0.9,
    shadowRadius: 6,
    elevation: 4,
  },
  labels: { flexDirection: "row", justifyContent: "space-between", width: "100%", paddingHorizontal: 2 },
  zoneLbl: { fontSize: 9, fontFamily: "Nunito_700Bold", letterSpacing: 0.8 },
});

function StatusDestinyCard({
  label,
  accent,
  isDark,
  compact = false,
}: {
  label: string;
  accent: string;
  isDark: boolean;
  compact?: boolean;
}) {
  const pulse = useRef(new Animated.Value(0.35)).current;
  useEffect(() => {
    const loop = Animated.loop(
      Animated.sequence([
        Animated.timing(pulse, { toValue: 0.7, duration: 2200, easing: Easing.inOut(Easing.sin), useNativeDriver: true }),
        Animated.timing(pulse, { toValue: 0.35, duration: 2200, easing: Easing.inOut(Easing.sin), useNativeDriver: true }),
      ]),
    );
    loop.start();
    return () => loop.stop();
  }, [pulse]);

  return (
    <View style={[statusStyles.wrap, compact && statusStyles.wrapCompact]}>
      <Animated.View
        style={[statusStyles.outerGlow, { opacity: pulse, shadowColor: accent, backgroundColor: accent + "18" }]}
      />
      <LinearGradient
        colors={isDark ? ["rgba(15,10,30,0.95)", "rgba(20,15,40,0.9)"] : ["#faf5ff", "#fff"]}
        style={[statusStyles.card, compact && statusStyles.cardCompact, { borderColor: accent + "45" }]}
      >
        <Text style={[statusStyles.eyebrow, { color: accent }]}>COSMIC SIGNAL</Text>
        <Text
          style={[statusStyles.label, compact && statusStyles.labelCompact, { color: isDark ? "#fff" : "#0F172A" }]}
          numberOfLines={2}
        >
          {label}
        </Text>
      </LinearGradient>
    </View>
  );
}

const statusStyles = StyleSheet.create({
  wrap: { width: "100%", maxWidth: 320, alignItems: "center" },
  wrapCompact: { maxWidth: 280 },
  cardCompact: { paddingVertical: 16, paddingHorizontal: 16 },
  labelCompact: { fontSize: 20, lineHeight: 26 },
  outerGlow: {
    ...StyleSheet.absoluteFillObject,
    borderRadius: 24,
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.8,
    shadowRadius: 24,
  },
  card: {
    width: "100%",
    borderRadius: 22,
    borderWidth: 1.5,
    paddingVertical: 28,
    paddingHorizontal: 22,
    alignItems: "center",
    gap: 8,
  },
  eyebrow: { fontSize: 10, fontFamily: "Nunito_800ExtraBold", letterSpacing: 2.2 },
  label: { fontSize: 26, fontFamily: "Nunito_800ExtraBold", textAlign: "center", lineHeight: 34, letterSpacing: -0.5 },
});

export function LoveRealityResultHero({
  display,
  isDark,
  accentGradient,
  compact = false,
}: {
  display: LoveRealityBasicDisplay;
  isDark: boolean;
  accentGradient: [string, string];
  compact?: boolean;
}) {
  if (display.visual === "circular" && display.percent != null) {
    return (
      <CircularScoreMeter
        percent={display.percent}
        isDark={isDark}
        glowColor={accentGradient[0]}
        compact={compact}
      />
    );
  }
  if (display.visual === "risk-gauge") {
    return (
      <RiskGaugeMeter
        score={display.riskScore ?? 50}
        riskLevel={display.riskLevel ?? "medium"}
        isDark={isDark}
        compact={compact}
      />
    );
  }
  return (
    <StatusDestinyCard
      label={display.statusLabel ?? "Cosmic Reading"}
      accent={display.statusAccent ?? accentGradient[0]}
      isDark={isDark}
      compact={compact}
    />
  );
}

function ProUpsellBanner({
  isDark,
  bottomPad,
  onPress,
}: {
  isDark: boolean;
  bottomPad: number;
  onPress: () => void;
}) {
  const { offerInr } = LOVE_REALITY_PRO_UI_PRICING;
  const glassBg = isDark ? "rgba(12,8,28,0.72)" : "rgba(255,255,255,0.82)";
  const borderC = isDark ? "rgba(168,85,247,0.35)" : "rgba(124,58,237,0.22)";

  return (
    <View style={[upsellStyles.wrap, { paddingBottom: bottomPad + 12 }]}>
      <Pressable onPress={onPress} style={({ pressed }) => ({ opacity: pressed ? 0.92 : 1 })}>
        <View style={[upsellStyles.card, { borderColor: borderC }]}>
          {Platform.OS !== "web" ? (
            <BlurView intensity={isDark ? 40 : 60} tint={isDark ? "dark" : "light"} style={StyleSheet.absoluteFill} />
          ) : null}
          <View style={[StyleSheet.absoluteFill, { backgroundColor: glassBg }]} />
          <View style={upsellStyles.inner}>
            <Text style={[upsellStyles.headline, { color: isDark ? "#fff" : "#0F172A" }]}>
              Want the complete 14-page truth?
            </Text>
            <Text style={[upsellStyles.sub, { color: isDark ? "rgba(203,213,225,0.65)" : "#64748B" }]}>
              Reveal hidden red flags, exact monthly timelines, and Vedic remedies.
            </Text>
            <LinearGradient
              colors={["#f59e0b", "#ec4899", "#9333ea"]}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 0 }}
              style={upsellStyles.btn}
            >
              <Feather name="file-text" size={16} color="#fff" />
              <Text style={upsellStyles.btnTxt}>Unlock Full Pro PDF — ₹{offerInr}</Text>
            </LinearGradient>
          </View>
        </View>
      </Pressable>
    </View>
  );
}

const upsellStyles = StyleSheet.create({
  wrap: { paddingHorizontal: 16, paddingTop: 8 },
  card: { borderRadius: 20, borderWidth: 1, overflow: "hidden" },
  inner: { padding: 16, gap: 8 },
  headline: { fontSize: 15, fontFamily: "Nunito_800ExtraBold", letterSpacing: -0.2 },
  sub: { fontSize: 12, fontFamily: "Nunito_500Medium", lineHeight: 18 },
  btn: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
    paddingVertical: 14,
    borderRadius: 14,
    marginTop: 6,
  },
  btnTxt: { color: "#fff", fontSize: 14, fontFamily: "Nunito_800ExtraBold", letterSpacing: 0.2 },
});

export function LoveRealityBasicScreen({ config }: { config: LoveRealityToolConfig }) {
  const C = useC();
  const t = useT();
  const isDark = C.isDark;
  const insets = useSafeAreaInsets();
  const topPad = Platform.OS === "android" ? Math.max(insets.top, 24) : insets.top;
  const { LockOverlay } = useFeatureGate(config.featureGate);

  const { profiles, primaryProfileId } = useUser();
  const params = useLocalSearchParams<{ partnerId?: string }>();
  const partnerId = typeof params.partnerId === "string" ? params.partnerId : null;

  const primaryProfile = profiles.find(p => p.id === primaryProfileId) ?? profiles[0] ?? null;
  const partnerProfile = partnerId ? (profiles.find(p => p.id === partnerId) ?? null) : null;

  const hasSelfKundli = !!primaryProfile?.kundli && !!primaryProfile?.birthData;
  const hasPartnerKundli = !!partnerProfile?.kundli && !!partnerProfile?.birthData;
  const canAnalyze = hasSelfKundli && hasPartnerKundli;

  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [display, setDisplay] = useState<LoveRealityBasicDisplay | null>(null);

  const textHi = isDark ? "#fff" : "#0F172A";
  const textLo = isDark ? "rgba(203,213,225,0.65)" : "#64748B";
  const border = isDark ? "rgba(255,255,255,0.1)" : "rgba(15,23,42,0.08)";

  const didRun = useRef(false);
  useEffect(() => {
    if (didRun.current || !canAnalyze) return;
    didRun.current = true;
    runAnalysis();
  }, [canAnalyze]);

  async function runAnalysis() {
    if (!primaryProfile?.birthData || !partnerProfile?.birthData) return;
    setErr(null);
    setDisplay(null);
    setLoading(true);
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    try {
      const ctrl = new AbortController();
      const timer = setTimeout(() => ctrl.abort(), 30000);
      const resp = await fetch(`${API_BASE}${config.apiPath}`, {
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
      setDisplay(mapLoveRealityResult(config.toolKey, json as Record<string, unknown>));
      // chart_proof attached by backend engines
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
    } catch (e: unknown) {
      setErr(e instanceof Error ? e.message : "Could not analyze. Please try again.");
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
    } finally {
      setLoading(false);
    }
  }

  function openProPdf() {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    router.push({
      pathname: "/love-reality",
      params: { partnerId: partnerId ?? "", openPro: "1" },
    } as never);
  }

  const showResult = canAnalyze && !loading && !err && display;

  return (
    <CosmicBg>
      <View style={[styles.root, { paddingTop: topPad }]}>
        <View style={styles.center}>
          {!canAnalyze && (
            <View style={styles.stateBlock}>
              <Feather name="lock" size={28} color="#f472b6" />
              <Text style={[styles.stateTitle, { color: textHi }]}>{t.needKundli}</Text>
              <Text style={[styles.stateSub, { color: textLo }]}>
                {!hasSelfKundli ? t.needKundliSub : t.needPartnerKundli}
              </Text>
              <Pressable onPress={() => router.replace("/relationship" as never)} style={{ marginTop: 12, width: "100%" }}>
                <LinearGradient colors={config.accentGradient} style={styles.retryBtn}>
                  <Text style={styles.retryTxt}>Go to Relationship</Text>
                </LinearGradient>
              </Pressable>
            </View>
          )}

          {canAnalyze && loading && (
            <View style={styles.stateBlock}>
              <ActivityIndicator size="large" color={config.accentGradient[0]} />
              <Text style={[styles.stateTitle, { color: textHi }]}>Reading both kundlis…</Text>
              <Text style={[styles.stateSub, { color: textLo }]}>{config.loadingHint}</Text>
            </View>
          )}

          {canAnalyze && !loading && err && (
            <View style={styles.stateBlock}>
              <Feather name="alert-circle" size={26} color="#ef4444" />
              <Text style={[styles.stateSub, { color: textHi, textAlign: "center" }]}>{err}</Text>
              <Pressable onPress={runAnalysis} style={{ marginTop: 12, width: "100%" }}>
                <LinearGradient colors={config.accentGradient} style={styles.retryBtn}>
                  <Text style={styles.retryTxt}>Retry</Text>
                </LinearGradient>
              </Pressable>
            </View>
          )}

          {showResult && display && primaryProfile && partnerProfile && (
            <LoveRealityToolResultPanel
              toolTitle={config.title}
              userName={primaryProfile.name || "You"}
              partnerName={partnerProfile.name || "Partner"}
              display={display}
              isDark={isDark}
              bottomPad={insets.bottom}
              accentGradient={config.accentGradient}
              onOpenPro={openProPdf}
              showHeader
              onBack={() => router.back()}
            />
          )}
        </View>
      </View>
      {LockOverlay}
    </CosmicBg>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1 },
  header: {
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: 16,
    paddingBottom: 10,
    gap: 10,
  },
  backCircle: {
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: "center",
    justifyContent: "center",
    borderWidth: 1,
  },
  title: { flex: 1, fontSize: 18, fontFamily: "Nunito_700Bold", letterSpacing: -0.3, textAlign: "center" },
  partnerBadge: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    marginHorizontal: 16,
    marginBottom: 8,
    paddingVertical: 10,
    paddingHorizontal: 14,
    borderRadius: 14,
    borderWidth: 1,
    overflow: "hidden",
  },
  partnerTxt: { flex: 1, fontSize: 12, fontFamily: "Nunito_600SemiBold" },
  center: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    paddingHorizontal: 20,
    gap: 16,
    minHeight: 0,
  },
  hook: {
    fontSize: 14,
    fontFamily: "Nunito_600SemiBold",
    fontStyle: "italic",
    textAlign: "center",
    lineHeight: 21,
    maxWidth: 340,
    paddingHorizontal: 4,
  },
  stateBlock: { alignItems: "center", gap: 10, width: "100%", maxWidth: 320 },
  stateTitle: { fontSize: 16, fontFamily: "Nunito_700Bold" },
  stateSub: { fontSize: 13, fontFamily: "Nunito_500Medium", textAlign: "center", lineHeight: 19 },
  retryBtn: { paddingVertical: 14, borderRadius: 14, alignItems: "center" },
  retryTxt: { color: "#fff", fontSize: 14, fontFamily: "Nunito_700Bold" },
});
