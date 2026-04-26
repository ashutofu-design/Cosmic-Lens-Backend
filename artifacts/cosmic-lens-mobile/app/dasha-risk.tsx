import { Feather } from "@expo/vector-icons";
import { LinearGradient } from "expo-linear-gradient";
import { router } from "expo-router";
import React, { useCallback, useEffect, useMemo, useState } from "react";
import {
  ActivityIndicator,
  I18nManager,
  Pressable,
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";
import Animated, {
  Easing,
  useAnimatedProps,
  useAnimatedStyle,
  useSharedValue,
  withDelay,
  withRepeat,
  withTiming,
} from "react-native-reanimated";
import Svg, {
  Circle,
  Defs,
  Line,
  Path,
  RadialGradient,
  Stop,
  Text as SvgText,
} from "react-native-svg";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { CosmicBg } from "@/components/CosmicBg";
import { useC } from "@/context/ThemeContext";
import { useUser } from "@/context/UserContext";
import { API_BASE, apiFetch } from "@/lib/apiConfig";

const F = {
  regular: "Nunito_400Regular",
  semi:    "Nunito_600SemiBold",
  bold:    "Nunito_700Bold",
  extra:   "Nunito_800ExtraBold",
} as const;

type RiskLevel = "low" | "medium" | "high";

interface Risk24h {
  level:   RiskLevel;
  title:   string;
  reason:  string;
  advice:  string;
  timing?: string;
}

interface RiskRadarData {
  risk_radar_24h: Risk24h[];
  summary:        string;
  date?:          string;
  score?:         number;
}

// ── Level styling ─────────────────────────────────────────────────────────────
function levelColor(l: RiskLevel): string {
  if (l === "high")   return "#ef4444";
  if (l === "medium") return "#f59e0b";
  return "#22c55e";
}
function levelBg(l: RiskLevel): string {
  if (l === "high")   return "rgba(239,68,68,0.12)";
  if (l === "medium") return "rgba(245,158,11,0.12)";
  return "rgba(34,197,94,0.12)";
}
function levelLabel(l: RiskLevel): string {
  if (l === "high")   return "High";
  if (l === "medium") return "Medium";
  return "Low";
}
function levelIcon(l: RiskLevel): string {
  if (l === "high")   return "⚠️";
  if (l === "medium") return "🌗";
  return "✅";
}

// ── Radar geometry helpers ────────────────────────────────────────────────────
const RADAR_SIZE = 280;
const RADAR_R    = RADAR_SIZE / 2 - 6;
const RADAR_C    = RADAR_SIZE / 2;

function polar(angleDeg: number, radius: number) {
  const rad = (angleDeg - 90) * Math.PI / 180;
  return {
    x: RADAR_C + Math.cos(rad) * radius,
    y: RADAR_C + Math.sin(rad) * radius,
  };
}

function severityRadius(level: RiskLevel): number {
  if (level === "high")   return RADAR_R * 0.35;
  if (level === "medium") return RADAR_R * 0.62;
  return RADAR_R * 0.85;
}

function buildWedgePath(startAngle: number, endAngle: number): string {
  const start = polar(startAngle, RADAR_R);
  const end   = polar(endAngle,   RADAR_R);
  const largeArc = endAngle - startAngle > 180 ? 1 : 0;
  return `M ${RADAR_C} ${RADAR_C} L ${start.x} ${start.y} A ${RADAR_R} ${RADAR_R} 0 ${largeArc} 1 ${end.x} ${end.y} Z`;
}

const SWEEP_PATH = buildWedgePath(-70, 0); // 70° trailing wedge — wider, more dramatic

// Halo padding around the radar so the outer glow can bleed
const HALO_PAD  = 22;
const WRAP_SIZE = RADAR_SIZE + HALO_PAD * 2;

// Pre-computed background "stars" inside the radar (stable, deterministic)
const BG_STARS = Array.from({ length: 26 }, (_, i) => {
  const angle  = (i * 53.7) % 360;
  const radius = ((i * 17 + 11) % (RADAR_R - 24)) + 14;
  const p      = polar(angle, radius);
  return {
    x: p.x,
    y: p.y,
    r: 0.5 + ((i * 3) % 4) * 0.3,
    op: 0.25 + ((i * 11) % 6) / 14,
  };
});

// Tick marks around the outer ring (every 15°, longer at cardinals)
const TICKS = Array.from({ length: 24 }, (_, i) => {
  const angle      = i * 15;
  const isCardinal = i % 6 === 0;
  const innerR     = RADAR_R - (isCardinal ? 14 : 7);
  const outerR     = RADAR_R - 2;
  const p1         = polar(angle, innerR);
  const p2         = polar(angle, outerR);
  return { x1: p1.x, y1: p1.y, x2: p2.x, y2: p2.y, isCardinal };
});

const AnimatedCircle = Animated.createAnimatedComponent(Circle);

// ── Radar visualization ───────────────────────────────────────────────────────
function RadarView({ risks }: { risks: Risk24h[] }) {
  const sweep    = useSharedValue(0);
  const halo     = useSharedValue(0);
  const dotPulse = useSharedValue(0);
  const ping1    = useSharedValue(0);
  const ping2    = useSharedValue(0);

  useEffect(() => {
    sweep.value = withRepeat(
      withTiming(360, { duration: 5000, easing: Easing.linear }),
      -1,
      false,
    );
    halo.value = withRepeat(
      withTiming(1, { duration: 2800, easing: Easing.inOut(Easing.ease) }),
      -1,
      true,
    );
    dotPulse.value = withRepeat(
      withTiming(1, { duration: 1400, easing: Easing.inOut(Easing.ease) }),
      -1,
      true,
    );
    ping1.value = withRepeat(
      withTiming(1, { duration: 3500, easing: Easing.out(Easing.cubic) }),
      -1,
      false,
    );
    ping2.value = withDelay(
      1750,
      withRepeat(
        withTiming(1, { duration: 3500, easing: Easing.out(Easing.cubic) }),
        -1,
        false,
      ),
    );
  }, [sweep, halo, dotPulse, ping1, ping2]);

  const sweepStyle = useAnimatedStyle(() => ({
    transform: [{ rotate: `${sweep.value}deg` }],
  }));

  const haloStyle = useAnimatedStyle(() => ({
    opacity: 0.30 + halo.value * 0.40,
    transform: [{ scale: 0.96 + halo.value * 0.06 }],
  }));

  const haloInnerStyle = useAnimatedStyle(() => ({
    opacity: 0.5 + (1 - halo.value) * 0.4,
  }));

  const dotPulseStyle = useAnimatedStyle(() => ({
    opacity: 0.20 + dotPulse.value * 0.55,
    transform: [{ scale: 0.8 + dotPulse.value * 0.55 }],
  }));

  const statusDotStyle = useAnimatedStyle(() => ({
    opacity: 0.5 + dotPulse.value * 0.5,
  }));

  const ping1Props = useAnimatedProps(() => ({
    r: 6 + ping1.value * (RADAR_R - 8),
    opacity: 0.55 * (1 - ping1.value),
    strokeWidth: 1.5 - ping1.value * 0.8,
  }));
  const ping2Props = useAnimatedProps(() => ({
    r: 6 + ping2.value * (RADAR_R - 8),
    opacity: 0.45 * (1 - ping2.value),
    strokeWidth: 1.5 - ping2.value * 0.8,
  }));

  // Stable angles per risk: golden angle so they spread nicely
  const dots = useMemo(() => {
    return risks.map((r, i) => {
      const angle  = (i * 137.5 + 30) % 360;
      const radius = severityRadius(r.level);
      const p      = polar(angle, radius);
      return {
        ...p,
        color: levelColor(r.level),
        level: r.level,
        idx:   i + 1,
      };
    });
  }, [risks]);

  return (
    <View style={radarS.outerWrap}>
      {/* Status bar */}
      <View style={radarS.statusRow}>
        <Animated.View
          style={[radarS.statusDot, statusDotStyle, { backgroundColor: "#22d3ee" }]}
        />
        <Text style={radarS.statusTxt}>SCANNING • LIVE</Text>
        <View style={radarS.statusSpacer} />
        <Text style={radarS.statusMeta}>
          {risks.length} {risks.length === 1 ? "SIGNAL" : "SIGNALS"}
        </Text>
      </View>

      <View style={radarS.wrap}>
        {/* Outer pulsing halo */}
        <Animated.View style={[radarS.haloOuter, haloStyle]} />
        <Animated.View style={[radarS.haloInner, haloInnerStyle]} />

        {/* Static base layer */}
        <Svg
          width={RADAR_SIZE}
          height={RADAR_SIZE}
          style={{ position: "absolute", left: HALO_PAD, top: HALO_PAD }}
        >
          <Defs>
            <RadialGradient id="bg" cx="50%" cy="50%" r="50%">
              <Stop offset="0%"   stopColor="#1a2545" stopOpacity="1" />
              <Stop offset="55%"  stopColor="#0a1430" stopOpacity="1" />
              <Stop offset="100%" stopColor="#02060f" stopOpacity="1" />
            </RadialGradient>
          </Defs>

          {/* Background disc */}
          <Circle cx={RADAR_C} cy={RADAR_C} r={RADAR_R + 4} fill="url(#bg)" />

          {/* Bezel chrome (double ring) */}
          <Circle cx={RADAR_C} cy={RADAR_C} r={RADAR_R + 4}
            stroke="#22d3ee" strokeWidth={2} strokeOpacity={0.6} fill="none" />
          <Circle cx={RADAR_C} cy={RADAR_C} r={RADAR_R}
            stroke="#67e8f9" strokeWidth={1} strokeOpacity={0.3} fill="none" />

          {/* Tick marks */}
          {TICKS.map((t, i) => (
            <Line key={`tick-${i}`}
              x1={t.x1} y1={t.y1} x2={t.x2} y2={t.y2}
              stroke="#67e8f9"
              strokeWidth={t.isCardinal ? 1.8 : 1}
              strokeOpacity={t.isCardinal ? 0.75 : 0.32} />
          ))}

          {/* Cosmic background stars */}
          {BG_STARS.map((s, i) => (
            <Circle key={`star-${i}`}
              cx={s.x} cy={s.y} r={s.r}
              fill="#fff" fillOpacity={s.op} />
          ))}

          {/* Concentric rings (severity zones) */}
          {[0.85, 0.62, 0.4].map((p, i) => (
            <Circle key={`ring-${i}`}
              cx={RADAR_C} cy={RADAR_C} r={RADAR_R * p}
              stroke="rgba(34,211,238,0.22)" strokeWidth={1} fill="none"
              strokeDasharray={i === 1 ? "3 5" : undefined} />
          ))}

          {/* Spokes — 4 cardinal + 4 diagonal */}
          {[0, 45, 90, 135].map((angle, i) => {
            const p1 = polar(angle, RADAR_R - 4);
            const p2 = polar(angle + 180, RADAR_R - 4);
            const isCardinal = angle % 90 === 0;
            return (
              <Line key={`spoke-${i}`}
                x1={p1.x} y1={p1.y} x2={p2.x} y2={p2.y}
                stroke="#22d3ee"
                strokeWidth={isCardinal ? 1 : 0.6}
                strokeOpacity={isCardinal ? 0.18 : 0.10} />
            );
          })}

          {/* Compass labels */}
          <SvgText x={RADAR_C} y={20} fill="#67e8f9"
            fontSize="11" fontWeight="800" textAnchor="middle">N</SvgText>
          <SvgText x={RADAR_SIZE - 8} y={RADAR_C + 4} fill="#67e8f9"
            fontSize="11" fontWeight="800" textAnchor="end">E</SvgText>
          <SvgText x={RADAR_C} y={RADAR_SIZE - 8} fill="#67e8f9"
            fontSize="11" fontWeight="800" textAnchor="middle">S</SvgText>
          <SvgText x={8} y={RADAR_C + 4} fill="#67e8f9"
            fontSize="11" fontWeight="800" textAnchor="start">W</SvgText>

          {/* Sonar pings */}
          <AnimatedCircle cx={RADAR_C} cy={RADAR_C}
            stroke="#22d3ee" fill="none" animatedProps={ping1Props} />
          <AnimatedCircle cx={RADAR_C} cy={RADAR_C}
            stroke="#67e8f9" fill="none" animatedProps={ping2Props} />

          {/* Center hub */}
          <Circle cx={RADAR_C} cy={RADAR_C} r={6} fill="#22d3ee" fillOpacity={0.3} />
          <Circle cx={RADAR_C} cy={RADAR_C} r={3.5} fill="#22d3ee" />
          <Circle cx={RADAR_C} cy={RADAR_C} r={1.5} fill="#fff" />
        </Svg>

        {/* Animated sweep beam (rotating wedge) */}
        <Animated.View
          style={[
            {
              position: "absolute",
              left:   HALO_PAD,
              top:    HALO_PAD,
              width:  RADAR_SIZE,
              height: RADAR_SIZE,
            },
            sweepStyle,
          ]}
        >
          <Svg width={RADAR_SIZE} height={RADAR_SIZE}>
            <Defs>
              <RadialGradient id="sweep" cx="50%" cy="50%" r="50%">
                <Stop offset="0%"   stopColor="#22d3ee" stopOpacity="0.65" />
                <Stop offset="100%" stopColor="#22d3ee" stopOpacity="0" />
              </RadialGradient>
            </Defs>
            <Path d={SWEEP_PATH} fill="url(#sweep)" />
            {/* Glowing leading edge */}
            <Line
              x1={RADAR_C} y1={RADAR_C}
              x2={RADAR_C} y2={RADAR_C - RADAR_R}
              stroke="#a5f3fc" strokeWidth={2.5} strokeOpacity={0.95}
              strokeLinecap="round"
            />
            <Line
              x1={RADAR_C} y1={RADAR_C}
              x2={RADAR_C} y2={RADAR_C - RADAR_R}
              stroke="#fff" strokeWidth={1} strokeOpacity={0.7}
              strokeLinecap="round"
            />
            {/* Tip glow */}
            <Circle cx={RADAR_C} cy={RADAR_C - RADAR_R + 6} r={5}
              fill="#a5f3fc" fillOpacity={0.85} />
            <Circle cx={RADAR_C} cy={RADAR_C - RADAR_R + 6} r={2.5}
              fill="#fff" />
          </Svg>
        </Animated.View>

        {/* Risk dots (with ripple halos) */}
        {dots.map((d, i) => (
          <View
            key={`dot-${i}`}
            pointerEvents="none"
            style={{
              position: "absolute",
              left: HALO_PAD + d.x - 20,
              top:  HALO_PAD + d.y - 20,
              width: 40, height: 40,
              alignItems: "center", justifyContent: "center",
            }}
          >
            {/* Outer ripple ring */}
            <Animated.View
              style={[
                {
                  position: "absolute",
                  width: 40, height: 40, borderRadius: 20,
                  borderWidth: 1.5, borderColor: d.color,
                },
                dotPulseStyle,
              ]}
            />
            {/* Inner soft glow */}
            <View
              style={{
                position: "absolute",
                width: 28, height: 28, borderRadius: 14,
                backgroundColor: d.color, opacity: 0.30,
              }}
            />
            {/* Solid dot with number badge */}
            <View
              style={{
                width: 20, height: 20, borderRadius: 10,
                backgroundColor: d.color,
                borderWidth: 2, borderColor: "#fff",
                alignItems: "center", justifyContent: "center",
                shadowColor: d.color,
                shadowOpacity: 0.9,
                shadowRadius: 6,
                shadowOffset: { width: 0, height: 0 },
                elevation: 6,
              }}
            >
              <Text style={radarS.dotIdx}>{d.idx}</Text>
            </View>
          </View>
        ))}

        {/* All Clear overlay */}
        {risks.length === 0 && (
          <View style={radarS.emptyOverlay} pointerEvents="none">
            <Text style={radarS.emptyTxt}>ALL CLEAR</Text>
            <Text style={radarS.emptySub}>Aaj koi major signal nahi</Text>
          </View>
        )}
      </View>
    </View>
  );
}

// ── Main screen ───────────────────────────────────────────────────────────────
export default function DashaRiskScreen() {
  const C        = useC();
  const insets   = useSafeAreaInsets();
  const { user, kundli, birthData } = useUser();

  const [data, setData]             = useState<RiskRadarData | null>(null);
  const [loading, setLoading]       = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError]           = useState<string | null>(null);

  const loadRadar = useCallback(async (silent = false) => {
    if (!silent) setLoading(true);
    setError(null);

    const hasLocalKundli = !!(kundli && Array.isArray(kundli.planets) && kundli.planets.length > 0);

    if (!hasLocalKundli && !(user?.id && user?.api_key)) {
      setError("NO_KUNDLI");
      setLoading(false);
      return;
    }

    try {
      let r: Response;
      if (hasLocalKundli) {
        r = await apiFetch(`${API_BASE}/api/risk-radar`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            chart_data: kundli,
            birthData: birthData ?? undefined,
          }),
        });
      } else {
        r = await apiFetch(`${API_BASE}/api/risk-radar?user_id=${user!.id}`, {
          method: "GET",
          headers: { "X-API-Key": user!.api_key },
        });
      }
      const j = await r.json();
      if (!r.ok) {
        const msg = (j?.error || "").toLowerCase();
        if (msg.includes("kundli") || r.status === 404) {
          setError("NO_KUNDLI");
        } else {
          setError(j?.error || "Could not load Risk Radar");
        }
        setData(null);
      } else {
        setData(j as RiskRadarData);
      }
    } catch (e: any) {
      setError(e?.message || "Network error");
      setData(null);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [user?.id, user?.api_key, kundli, birthData]);

  useEffect(() => { loadRadar(); }, [loadRadar]);

  const onRefresh = useCallback(() => {
    setRefreshing(true);
    loadRadar(true);
  }, [loadRadar]);

  const back = () => {
    if (router.canGoBack()) router.back();
    else router.replace("/(tabs)");
  };

  // Filter out the "Stable Day" baseline so radar shows clean when no risks
  const realRisks = (data?.risk_radar_24h ?? []).filter(
    r => !(r.level === "low" && r.title === "Stable Day"),
  );

  const summaryColor = (() => {
    if (!data) return C.textMid;
    const high = realRisks.filter(r => r.level === "high").length;
    if (high >= 2) return levelColor("high");
    if (high === 1) return levelColor("medium");
    return levelColor("low");
  })();

  return (
    <View style={[s.root, { backgroundColor: C.bg }]}>
      <CosmicBg />

      {/* Header */}
      <View style={[s.header, { paddingTop: insets.top + 6 }]}>
        <Pressable
          onPress={back}
          style={[s.backBtn, { borderColor: C.border, backgroundColor: C.bgCard }]}
          hitSlop={10}
        >
          <Feather
            name={I18nManager.isRTL ? "arrow-right" : "arrow-left"}
            size={18}
            color={C.text}
          />
        </Pressable>
        <View style={{ flex: 1 }}>
          <Text style={[s.h1, { color: C.text }]}>Risk Radar</Text>
          <Text style={[s.h1Sub, { color: C.textMuted }]}>
            Aaj ke 24 ghante ke important signals
          </Text>
        </View>
      </View>

      <ScrollView
        contentContainerStyle={{ padding: 16, paddingBottom: insets.bottom + 80 }}
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={onRefresh}
            tintColor={C.text}
          />
        }
      >
        {loading ? (
          <View style={s.loadingBox}>
            <ActivityIndicator size="large" color={C.accent} />
            <Text style={[s.loadingTxt, { color: C.textMuted }]}>
              Aapka radar tayyar kar rahe hain…
            </Text>
          </View>
        ) : error === "NO_KUNDLI" ? (
          <View style={[s.card, s.emptyCard, { backgroundColor: C.bgCard, borderColor: C.border }]}>
            <Text style={s.emptyIcon}>🪐</Text>
            <Text style={[s.emptyTitle, { color: C.text }]}>
              Pehle apni kundli banayein
            </Text>
            <Text style={[s.emptyBody, { color: C.textMuted }]}>
              Risk Radar aapke janma kundli ke signals pe based hai. Kundli
              banane ke baad aapko aaj ke 24 ghante ke important signals
              dikhenge.
            </Text>
            <Pressable
              onPress={() => router.push("/(tabs)/profile")}
              style={[s.retryBtn, { backgroundColor: C.accent }]}
            >
              <Text style={s.retryTxt}>Kundli banayein</Text>
            </Pressable>
          </View>
        ) : error ? (
          <View style={[s.card, { backgroundColor: C.bgCard, borderColor: C.border }]}>
            <Text style={[s.errTitle, { color: levelColor("high") }]}>
              Risk Radar load nahi ho saka
            </Text>
            <Text style={[s.errBody, { color: C.textMuted }]}>{error}</Text>
            <Pressable
              onPress={() => loadRadar()}
              style={[s.retryBtn, { backgroundColor: C.accent }]}
            >
              <Text style={s.retryTxt}>Phir try karein</Text>
            </Pressable>
          </View>
        ) : data ? (
          <>
            {/* Radar visualization (hero) */}
            <RadarView risks={realRisks} />

            {/* Radar legend */}
            <View style={s.legendRow}>
              <View style={s.legendItem}>
                <View style={[s.legendDot, { backgroundColor: levelColor("high") }]} />
                <Text style={[s.legendTxt, { color: C.textMuted }]}>High</Text>
              </View>
              <View style={s.legendItem}>
                <View style={[s.legendDot, { backgroundColor: levelColor("medium") }]} />
                <Text style={[s.legendTxt, { color: C.textMuted }]}>Medium</Text>
              </View>
              <View style={s.legendItem}>
                <View style={[s.legendDot, { backgroundColor: levelColor("low") }]} />
                <Text style={[s.legendTxt, { color: C.textMuted }]}>Low</Text>
              </View>
            </View>

            {/* Summary card */}
            <LinearGradient
              colors={[C.bgCard, C.bgCard2]}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 1 }}
              style={[s.card, s.summaryCard, { borderColor: C.border }]}
            >
              <View style={s.summaryHead}>
                <View style={[s.dot, { backgroundColor: summaryColor }]} />
                <Text style={[s.summaryLabel, { color: C.textMuted }]}>
                  Aaj ka radar
                </Text>
              </View>
              <Text style={[s.summaryTxt, { color: C.text }]}>
                {data.summary}
              </Text>
              {typeof data.score === "number" && (
                <View style={s.scoreRow}>
                  <Text style={[s.scoreLabel, { color: C.textMuted }]}>
                    Energy Score
                  </Text>
                  <Text style={[s.scoreVal, { color: C.text }]}>
                    {Math.round(data.score)}/100
                  </Text>
                </View>
              )}
            </LinearGradient>

            {/* 24h section */}
            <View style={s.sectionHead}>
              <Text style={[s.sectionTitle, { color: C.text }]}>
                Active Signals
              </Text>
              <Text style={[s.sectionSub, { color: C.textMuted }]}>
                {realRisks.length > 0
                  ? `Aaj ke top ${realRisks.length} signal`
                  : "Aaj koi major signal nahi"}
              </Text>
            </View>

            {(realRisks.length > 0 ? realRisks : data.risk_radar_24h).map((risk, i) => (
              <View
                key={`r24-${i}`}
                style={[
                  s.card,
                  s.riskCard,
                  {
                    backgroundColor: C.bgCard,
                    borderColor: C.border,
                    borderLeftColor: levelColor(risk.level),
                  },
                ]}
              >
                <View style={s.riskHead}>
                  {realRisks.length > 0 ? (
                    <View
                      style={[
                        s.numBadge,
                        { backgroundColor: levelColor(risk.level) },
                      ]}
                    >
                      <Text style={s.numBadgeTxt}>{i + 1}</Text>
                    </View>
                  ) : (
                    <Text style={s.riskIcon}>{levelIcon(risk.level)}</Text>
                  )}
                  <Text style={[s.riskTitle, { color: C.text }]}>
                    {risk.title}
                  </Text>
                  <View
                    style={[
                      s.levelPill,
                      { backgroundColor: levelBg(risk.level) },
                    ]}
                  >
                    <Text
                      style={[
                        s.levelPillTxt,
                        { color: levelColor(risk.level) },
                      ]}
                    >
                      {levelLabel(risk.level)}
                    </Text>
                  </View>
                </View>
                <Text style={[s.riskReason, { color: C.textMid }]}>
                  {risk.reason}
                </Text>
                <View
                  style={[
                    s.adviceBox,
                    { backgroundColor: C.bgCard2, borderColor: C.border3 },
                  ]}
                >
                  <Text style={[s.adviceLabel, { color: C.textMuted }]}>
                    💡 Kya karein
                  </Text>
                  <Text style={[s.adviceTxt, { color: C.text }]}>
                    {risk.advice}
                  </Text>
                </View>
                {risk.timing ? (
                  <View style={s.timingRow}>
                    <Feather name="clock" size={12} color={C.textMuted} />
                    <Text style={[s.timingTxt, { color: C.textMuted }]}>
                      {risk.timing}
                    </Text>
                  </View>
                ) : null}
              </View>
            ))}

            {/* Footer */}
            <Text style={[s.noteFooter, { color: C.textDim }]}>
              Powered by Advanced Cosmic Intelligence
            </Text>
          </>
        ) : null}
      </ScrollView>
    </View>
  );
}

// ── Radar styles ──────────────────────────────────────────────────────────────
const radarS = StyleSheet.create({
  outerWrap: {
    alignSelf: "center",
    alignItems: "center",
    marginTop: 4,
    marginBottom: 12,
  },

  statusRow: {
    flexDirection: "row",
    alignItems: "center",
    width: WRAP_SIZE - 16,
    paddingHorizontal: 4,
    marginBottom: 6,
    gap: 8,
  },
  statusDot: {
    width: 8, height: 8, borderRadius: 4,
    shadowColor: "#22d3ee",
    shadowOpacity: 1,
    shadowRadius: 6,
    shadowOffset: { width: 0, height: 0 },
    elevation: 4,
  },
  statusTxt: {
    color: "#67e8f9",
    fontSize: 10,
    fontFamily: F.extra,
    letterSpacing: 2,
  },
  statusSpacer: { flex: 1 },
  statusMeta: {
    color: "rgba(167, 243, 252, 0.7)",
    fontSize: 10,
    fontFamily: F.bold,
    letterSpacing: 1.5,
  },

  wrap: {
    width:  WRAP_SIZE,
    height: WRAP_SIZE,
    alignItems: "center",
    justifyContent: "center",
  },

  // Outer pulsing halo (soft ring outside the bezel)
  haloOuter: {
    position: "absolute",
    width: WRAP_SIZE - 4,
    height: WRAP_SIZE - 4,
    borderRadius: (WRAP_SIZE - 4) / 2,
    borderWidth: 16,
    borderColor: "rgba(34, 211, 238, 0.18)",
  },
  // Inner sharper halo glow against the bezel
  haloInner: {
    position: "absolute",
    width: RADAR_SIZE + 14,
    height: RADAR_SIZE + 14,
    borderRadius: (RADAR_SIZE + 14) / 2,
    borderWidth: 2,
    borderColor: "rgba(103, 232, 249, 0.45)",
  },

  dotIdx: {
    color: "#fff",
    fontSize: 10,
    fontFamily: F.extra,
    lineHeight: 12,
  },

  emptyOverlay: {
    ...StyleSheet.absoluteFillObject,
    alignItems: "center",
    justifyContent: "center",
  },
  emptyTxt: {
    color: "#22c55e",
    fontFamily: F.extra,
    fontSize: 22,
    letterSpacing: 3,
    textShadowColor: "rgba(34, 197, 94, 0.55)",
    textShadowOffset: { width: 0, height: 0 },
    textShadowRadius: 12,
  },
  emptySub: {
    color: "rgba(255,255,255,0.65)",
    fontFamily: F.semi,
    fontSize: 11,
    marginTop: 4,
    letterSpacing: 0.5,
  },
});

// ── Screen styles ─────────────────────────────────────────────────────────────
const s = StyleSheet.create({
  root: { flex: 1 },

  header: {
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: 16,
    paddingBottom: 8,
    gap: 12,
  },
  backBtn: {
    width: 36, height: 36, borderRadius: 12,
    borderWidth: 1, alignItems: "center", justifyContent: "center",
  },
  h1:    { fontSize: 22, fontFamily: F.extra },
  h1Sub: { fontSize: 12, fontFamily: F.regular, marginTop: 2 },

  loadingBox: {
    paddingVertical: 60, alignItems: "center", gap: 12,
  },
  loadingTxt: { fontSize: 13, fontFamily: F.regular },

  card: {
    borderRadius: 16, borderWidth: 1, padding: 16, marginBottom: 12,
  },

  legendRow: {
    flexDirection: "row",
    justifyContent: "center",
    gap: 16,
    marginTop: 4,
    marginBottom: 14,
  },
  legendItem: {
    flexDirection: "row", alignItems: "center", gap: 6,
  },
  legendDot: { width: 10, height: 10, borderRadius: 5 },
  legendTxt: { fontSize: 11, fontFamily: F.semi },

  summaryCard: { paddingVertical: 18 },
  summaryHead: {
    flexDirection: "row", alignItems: "center", gap: 8, marginBottom: 8,
  },
  dot: { width: 8, height: 8, borderRadius: 4 },
  summaryLabel: {
    fontSize: 11, fontFamily: F.semi,
    textTransform: "uppercase", letterSpacing: 0.5,
  },
  summaryTxt: {
    fontSize: 15, fontFamily: F.semi, lineHeight: 22,
  },
  scoreRow: {
    flexDirection: "row", alignItems: "center", justifyContent: "space-between",
    marginTop: 12, paddingTop: 12, borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: "rgba(127,127,127,0.2)",
  },
  scoreLabel: { fontSize: 12, fontFamily: F.semi },
  scoreVal:   { fontSize: 16, fontFamily: F.extra },

  sectionHead: {
    marginTop: 6, marginBottom: 8, paddingHorizontal: 4,
  },
  sectionTitle: { fontSize: 16, fontFamily: F.bold },
  sectionSub:   { fontSize: 11, fontFamily: F.regular, marginTop: 2 },

  riskCard: { borderLeftWidth: 4 },
  riskHead: {
    flexDirection: "row", alignItems: "center", gap: 8, marginBottom: 8,
  },
  riskIcon:  { fontSize: 18 },
  numBadge: {
    width: 22, height: 22, borderRadius: 11,
    alignItems: "center", justifyContent: "center",
  },
  numBadgeTxt: {
    color: "#fff", fontSize: 12, fontFamily: F.extra,
  },
  riskTitle: { fontSize: 15, fontFamily: F.bold, flex: 1 },
  riskReason:{ fontSize: 13, fontFamily: F.regular, lineHeight: 19, marginBottom: 10 },

  levelPill: {
    paddingHorizontal: 8, paddingVertical: 3, borderRadius: 999,
  },
  levelPillTxt: {
    fontSize: 10, fontFamily: F.bold,
    textTransform: "uppercase", letterSpacing: 0.4,
  },

  adviceBox: {
    borderRadius: 10, padding: 10, borderWidth: 1, gap: 4,
  },
  adviceLabel: {
    fontSize: 11, fontFamily: F.semi,
    textTransform: "uppercase", letterSpacing: 0.4,
  },
  adviceTxt: { fontSize: 13, fontFamily: F.semi, lineHeight: 19 },

  timingRow: {
    flexDirection: "row", alignItems: "center", gap: 6, marginTop: 8,
  },
  timingTxt: { fontSize: 11, fontFamily: F.semi },

  noteCard: {
    borderRadius: 14, borderWidth: 1, padding: 14, marginTop: 8,
  },
  noteTitle:  { fontSize: 13, fontFamily: F.bold, marginBottom: 6 },
  noteBody:   { fontSize: 12, fontFamily: F.regular, lineHeight: 18 },
  noteFooter: {
    fontSize: 10, fontFamily: F.semi, marginTop: 10, textAlign: "center",
    letterSpacing: 0.3,
  },

  emptyCard: {
    alignItems: "center", paddingVertical: 28, gap: 8,
  },
  emptyIcon:  { fontSize: 44, marginBottom: 6 },
  emptyTitle: {
    fontSize: 17, fontFamily: F.bold, textAlign: "center",
  },
  emptyBody: {
    fontSize: 13, fontFamily: F.regular, lineHeight: 19,
    textAlign: "center", marginBottom: 12,
  },

  errTitle: { fontSize: 15, fontFamily: F.bold, marginBottom: 6 },
  errBody:  { fontSize: 13, fontFamily: F.regular, marginBottom: 12 },
  retryBtn: {
    paddingVertical: 10, paddingHorizontal: 16,
    borderRadius: 10, alignSelf: "flex-start",
  },
  retryTxt: { color: "#fff", fontFamily: F.bold, fontSize: 13 },
});
