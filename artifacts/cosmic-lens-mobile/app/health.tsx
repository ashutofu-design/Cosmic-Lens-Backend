import { Feather } from "@expo/vector-icons";
import { BlurView } from "expo-blur";
import * as Haptics from "expo-haptics";
import { LinearGradient } from "expo-linear-gradient";
import { router } from "expo-router";
import React, { useEffect, useRef, useState } from "react";
import {
  ActivityIndicator,
  Animated,
  Easing,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";
import Svg, { Circle, Defs, LinearGradient as SvgGrad, Stop } from "react-native-svg";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { CosmicBg } from "@/components/CosmicBg";
import { useUser } from "@/context/UserContext";
import { useT } from "@/hooks/useT";
import { API_BASE, apiFetch } from "@/lib/apiConfig";
import { usePlan } from "@/lib/subscription";

const F = {
  regular: "Nunito_400Regular",
  semi:    "Nunito_600SemiBold",
  bold:    "Nunito_700Bold",
  extra:   "Nunito_800ExtraBold",
} as const;

interface BasicBlock { score: number; risk: string; summary: string; hook: string; }
interface PlanetStrength { name: string; sign: string; house: number; status: string; retrograde?: boolean; }
interface HouseInfo { sign: string; lord: string; occupants: string; meaning: string; }
interface ProBlock {
  houses: { h1: HouseInfo; h6: HouseInfo; h8: HouseInfo; h12: HouseInfo };
  planets: PlanetStrength[];
  transit: string[];
  risk_periods: string[];
  nature: string[];
  recovery: string;
  prevent: string[];
  remedies: string[];
  reasons: string[];
}
interface HealthResponse {
  level: "basic" | "pro";
  pro_locked: boolean;
  basic: BasicBlock;
  pro?: ProBlock;
}

function riskColor(risk: string): string {
  if (risk === "Low")  return "#22c55e";
  if (risk === "High") return "#ef4444";
  return "#f59e0b";
}
function riskPhrase(risk: string): string {
  if (risk === "Low")  return "Healthy Phase";
  if (risk === "High") return "Care Needed";
  return "Mixed Phase";
}

function ScoreRing({ score, color }: { score: number; color: string }) {
  const size = 168, stroke = 14;
  const r = (size - stroke) / 2;
  const circ = 2 * Math.PI * r;
  const dash = (score / 100) * circ;
  const animated = useRef(new Animated.Value(0)).current;
  useEffect(() => {
    Animated.timing(animated, { toValue: 1, duration: 1100,
      easing: Easing.out(Easing.cubic), useNativeDriver: false }).start();
  }, [score]);
  return (
    <View style={{ width: size, height: size, alignItems: "center", justifyContent: "center" }}>
      <Svg width={size} height={size}>
        <Defs>
          <SvgGrad id="hring" x1="0" y1="0" x2="1" y2="1">
            <Stop offset="0" stopColor={color} stopOpacity={1} />
            <Stop offset="1" stopColor={color} stopOpacity={0.5} />
          </SvgGrad>
        </Defs>
        <Circle cx={size/2} cy={size/2} r={r}
          stroke="rgba(255,255,255,0.08)" strokeWidth={stroke} fill="none" />
        <Circle cx={size/2} cy={size/2} r={r}
          stroke="url(#hring)" strokeWidth={stroke} fill="none"
          strokeDasharray={`${dash}, ${circ}`} strokeLinecap="round"
          transform={`rotate(-90 ${size/2} ${size/2})`} />
      </Svg>
      <View style={{ position: "absolute", alignItems: "center" }}>
        <Text style={{ color: "#fff", fontSize: 44, fontFamily: F.extra, letterSpacing: -1 }}>{score}</Text>
        <Text style={{ color: "rgba(255,255,255,0.5)", fontSize: 11, fontFamily: F.semi, letterSpacing: 1 }}>/ 100</Text>
      </View>
    </View>
  );
}

function SectionCard({
  icon, title, children, accent,
}: {
  icon: React.ComponentProps<typeof Feather>["name"];
  title: string;
  children: React.ReactNode;
  accent: string;
}) {
  return (
    <View style={[s.card, { borderColor: `${accent}33` }]}>
      <LinearGradient
        colors={["rgba(255,255,255,0.04)", "rgba(255,255,255,0.01)"]}
        start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }}
        style={StyleSheet.absoluteFill}
      />
      <View style={s.cardHead}>
        <View style={[s.cardIcon, { backgroundColor: `${accent}1F`, borderColor: `${accent}55` }]}>
          <Feather name={icon} size={14} color={accent} />
        </View>
        <Text style={s.cardTitle}>{title}</Text>
      </View>
      <View style={{ gap: 8 }}>{children}</View>
    </View>
  );
}

function Bullet({ children, color }: { children: React.ReactNode; color: string }) {
  return (
    <View style={{ flexDirection: "row", gap: 8 }}>
      <View style={[s.bullet, { backgroundColor: color }]} />
      <Text style={s.bulletText}>{children}</Text>
    </View>
  );
}

export default function HealthScreen() {
  const insets = useSafeAreaInsets();
  const { user, kundli } = useUser();
  const t = useT();
  const { isPro, isTrial } = usePlan();
  const isProUser = isPro || isTrial;

  const [data, setData] = useState<HealthResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);

  const fade = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    if (!user?.id || !user?.api_key) {
      setErr("Please log in to view your health analysis."); setLoading(false); return;
    }
    if (!kundli) {
      setErr(t.errKundliRequired);
      setLoading(false); return;
    }
    setLoading(true);
    apiFetch(`${API_BASE}/api/health-analysis`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-API-Key": user.api_key },
      body: JSON.stringify({ user_id: user.id, kundli }),
    })
      .then(async r => {
        const j = await r.json();
        if (!r.ok) throw new Error(j?.error || "Analysis failed");
        return j as HealthResponse;
      })
      .then(d => {
        setData(d); setErr(null);
        Animated.timing(fade, { toValue: 1, duration: 600, useNativeDriver: true }).start();
      })
      .catch(e => setErr(e?.message || "Health analysis load nahi ho saka."))
      .finally(() => setLoading(false));
  }, [user?.id, user?.api_key, kundli]);

  const accent = "#14b8a6";

  return (
    <CosmicBg>
      <LinearGradient
        colors={["rgba(0,0,0,0.45)", "transparent", "rgba(0,0,0,0.3)"]}
        locations={[0, 0.4, 1]}
        style={StyleSheet.absoluteFill}
        pointerEvents="none"
      />

      <View style={[s.topBar, { paddingTop: insets.top + 8 }]}>
        <Pressable
          onPress={() => { Haptics.selectionAsync(); router.back(); }}
          style={s.backBtn}
          hitSlop={10}
        >
          <View style={s.backCircle}>
            <Feather name="arrow-left" size={20} color="#fff" />
          </View>
        </Pressable>
        <Text style={s.topTitle}>Health Analysis</Text>
        <View style={{ width: 40 }} />
      </View>

      <ScrollView
        contentContainerStyle={{
          paddingTop: insets.top + 60,
          paddingBottom: insets.bottom + 80,
          paddingHorizontal: 18,
          gap: 16,
        }}
        showsVerticalScrollIndicator={false}
      >
        {loading && (
          <View style={{ paddingVertical: 60, alignItems: "center", gap: 12 }}>
            <ActivityIndicator size="large" color={accent} />
            <Text style={{ color: "rgba(255,255,255,0.6)", fontFamily: F.semi }}>
              Reading your chart…
            </Text>
          </View>
        )}

        {!loading && err && (
          <View style={[s.card, { borderColor: "#ef444455", padding: 22, alignItems: "center", gap: 10 }]}>
            <Feather name="alert-circle" size={28} color="#ef4444" />
            <Text style={[s.cardTitle, { textAlign: "center" }]}>{err}</Text>
            {!kundli && (
              <Pressable onPress={() => router.push("/profile-edit" as any)}
                style={({ pressed }) => ({ opacity: pressed ? 0.8 : 1, marginTop: 6 })}>
                <LinearGradient colors={["#0d9488", "#14b8a6"]}
                  start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }}
                  style={{ paddingHorizontal: 18, paddingVertical: 11, borderRadius: 12 }}>
                  <Text style={{ color: "#fff", fontFamily: F.bold, fontSize: 13 }}>
                    Add Birth Details
                  </Text>
                </LinearGradient>
              </Pressable>
            )}
          </View>
        )}

        {!loading && data && (
          <Animated.View style={{ opacity: fade, gap: 16 }}>
            {/* HERO */}
            <View style={[s.hero, { borderColor: `${accent}3A` }]}>
              <LinearGradient
                colors={["rgba(20,184,166,0.18)", "rgba(20,184,166,0.04)", "transparent"]}
                start={{ x: 0.5, y: 0 }} end={{ x: 0.5, y: 1 }}
                style={StyleSheet.absoluteFill}
              />
              <View style={{ alignItems: "center", paddingTop: 8, paddingBottom: 16 }}>
                <Text style={s.heroLabel}>HEALTH SCORE</Text>
                <View style={{ marginTop: 12 }}>
                  <ScoreRing score={data.basic.score} color={riskColor(data.basic.risk)} />
                </View>
                <View style={[s.trendPill, {
                  backgroundColor: `${riskColor(data.basic.risk)}22`,
                  borderColor: `${riskColor(data.basic.risk)}66`,
                  marginTop: 14,
                }]}>
                  <View style={[s.trendDot, { backgroundColor: riskColor(data.basic.risk) }]} />
                  <Text style={[s.trendText, { color: riskColor(data.basic.risk) }]}>
                    {riskPhrase(data.basic.risk)}  •  Risk: {data.basic.risk}
                  </Text>
                </View>
              </View>
            </View>

            {/* SUMMARY */}
            <SectionCard icon="message-circle" title="Quick Reading" accent={accent}>
              <Text style={s.summary}>{data.basic.summary}</Text>
            </SectionCard>

            {/* HOOK (non-pro) */}
            {!isProUser && (
              <View style={[s.hookCard, { borderColor: `${accent}55` }]}>
                <LinearGradient
                  colors={["rgba(20,184,166,0.18)", "rgba(20,184,166,0.05)"]}
                  start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }}
                  style={StyleSheet.absoluteFill}
                />
                <View style={s.hookRow}>
                  <View style={[s.hookIcon, { borderColor: `${accent}66` }]}>
                    <Feather name="zap" size={14} color={accent} />
                  </View>
                  <Text style={[s.hookHeading, { color: accent }]}>HIDDEN INSIGHT</Text>
                </View>

                <View style={{ position: "relative", marginTop: 8, minHeight: 56 }}>
                  <Text style={s.hookText}>{data.basic.hook}</Text>
                  {Platform.OS !== "web" ? (
                    <BlurView intensity={28} tint="dark"
                      style={[StyleSheet.absoluteFill, { borderRadius: 8 }]} />
                  ) : (
                    <View style={[StyleSheet.absoluteFill,
                      { backgroundColor: "rgba(5,20,18,0.55)", borderRadius: 8 }]} />
                  )}
                  <View style={[StyleSheet.absoluteFill, { alignItems: "center", justifyContent: "center" }]}>
                    <Feather name="lock" size={18} color={accent} />
                  </View>
                </View>

                <Text style={s.hookCta}>
                  Unlock full health analysis with exact risk periods and prevention guidance.
                </Text>

                <Pressable
                  onPress={() => {
                    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
                    router.push("/subscription");
                  }}
                  style={({ pressed }) => ({ opacity: pressed ? 0.85 : 1, marginTop: 12 })}
                >
                  <LinearGradient
                    colors={["#0d9488", "#14b8a6"]}
                    start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }}
                    style={s.upgradeBtn}
                  >
                    <Feather name="zap" size={14} color="#fff" />
                    <Text style={s.upgradeBtnText}>Upgrade to Pro</Text>
                  </LinearGradient>
                </Pressable>
              </View>
            )}

            {/* PRO sections */}
            {isProUser && data.pro && (
              <>
                {/* Houses */}
                <SectionCard icon="home" title="Health Houses" accent={accent}>
                  {([
                    { num: 1,  info: data.pro.houses.h1  },
                    { num: 6,  info: data.pro.houses.h6  },
                    { num: 8,  info: data.pro.houses.h8  },
                    { num: 12, info: data.pro.houses.h12 },
                  ]).map(h => (
                    <View key={h.num} style={s.kvRow}>
                      <View style={s.kvLeft}>
                        <Text style={s.kvHouse}>{h.num}{h.num === 1 ? "st" : h.num === 8 ? "th" : "th"}</Text>
                        <Text style={s.kvSign}>{h.info.sign}</Text>
                      </View>
                      <View style={{ flex: 1 }}>
                        <Text style={s.kvMeaning}>{h.info.meaning}</Text>
                        <Text style={s.kvLabel}>Lord: <Text style={s.kvVal}>{h.info.lord}</Text></Text>
                        <Text style={s.kvLabel}>In house: <Text style={s.kvVal}>{h.info.occupants}</Text></Text>
                      </View>
                    </View>
                  ))}
                </SectionCard>

                {/* Planets */}
                <SectionCard icon="star" title="Health Planets" accent={accent}>
                  {data.pro.planets.map(p => {
                    const sc = p.status === "exalted" ? "#22c55e"
                      : p.status === "debilitated" ? "#ef4444"
                      : p.status === "own sign" ? "#3b82f6" : "#94a3b8";
                    return (
                      <View key={p.name} style={s.planetRow}>
                        <Text style={s.planetName}>{p.name}</Text>
                        <Text style={s.planetMeta}>{p.sign} • H{p.house}</Text>
                        <View style={[s.statusPill, { borderColor: `${sc}55`, backgroundColor: `${sc}22` }]}>
                          <Text style={[s.statusText, { color: sc }]}>
                            {p.status}{p.retrograde ? " ℞" : ""}
                          </Text>
                        </View>
                      </View>
                    );
                  })}
                </SectionCard>

                <SectionCard icon="globe" title="Live Planetary Transit" accent={accent}>
                  {data.pro.transit.map((t, i) => (<Bullet key={i} color={accent}>{t}</Bullet>))}
                </SectionCard>

                <SectionCard icon="alert-triangle" title="Risk Periods" accent="#f59e0b">
                  {data.pro.risk_periods.map((t, i) => (<Bullet key={i} color="#f59e0b">{t}</Bullet>))}
                </SectionCard>

                <SectionCard icon="activity" title="Nature of Issues" accent="#a78bfa">
                  {data.pro.nature.map((t, i) => (<Bullet key={i} color="#a78bfa">{t}</Bullet>))}
                </SectionCard>

                <SectionCard icon="heart" title="Recovery Strength" accent="#22c55e">
                  <Text style={[s.summary, { color: "rgba(255,255,255,0.9)" }]}>
                    {data.pro.recovery}
                  </Text>
                </SectionCard>

                <SectionCard icon="shield" title="Preventive Guidance" accent="#22c55e">
                  {data.pro.prevent.map((t, i) => (<Bullet key={i} color="#22c55e">{t}</Bullet>))}
                </SectionCard>

                <SectionCard icon="sun" title="Remedies (Mantra & Lifestyle)" accent="#f59e0b">
                  {data.pro.remedies.map((t, i) => (<Bullet key={i} color="#f59e0b">{t}</Bullet>))}
                </SectionCard>

                {data.pro.reasons.length > 0 && (
                  <SectionCard icon="info" title="Why This Reading" accent="#94a3b8">
                    {data.pro.reasons.map((t, i) => (<Bullet key={i} color="#94a3b8">{t}</Bullet>))}
                  </SectionCard>
                )}
              </>
            )}
          </Animated.View>
        )}
      </ScrollView>
    </CosmicBg>
  );
}

const s = StyleSheet.create({
  topBar: {
    position: "absolute", top: 0, left: 0, right: 0,
    flexDirection: "row", alignItems: "center", justifyContent: "space-between",
    paddingHorizontal: 14, zIndex: 10, height: 60,
  },
  backBtn: { padding: 4 },
  backCircle: {
    width: 40, height: 40, borderRadius: 20,
    backgroundColor: "rgba(255,255,255,0.08)",
    borderWidth: 1, borderColor: "rgba(255,255,255,0.14)",
    alignItems: "center", justifyContent: "center",
  },
  topTitle: { color: "#fff", fontSize: 16, fontFamily: F.bold },

  hero: {
    borderRadius: 22,
    backgroundColor: "rgba(10,22,22,0.85)",
    borderWidth: 1.2,
    overflow: "hidden",
  },
  heroLabel: {
    color: "rgba(20,184,166,0.95)",
    fontSize: 10, letterSpacing: 2.4,
    fontFamily: F.extra, marginTop: 10,
  },
  trendPill: {
    flexDirection: "row", alignItems: "center", gap: 8,
    paddingHorizontal: 14, paddingVertical: 7,
    borderRadius: 20, borderWidth: 1,
  },
  trendDot: { width: 6, height: 6, borderRadius: 3 },
  trendText: { fontSize: 12, fontFamily: F.bold, letterSpacing: 0.3 },

  card: {
    borderRadius: 18, borderWidth: 1,
    backgroundColor: "rgba(10,18,22,0.78)",
    padding: 16, gap: 12, overflow: "hidden",
  },
  cardHead: { flexDirection: "row", alignItems: "center", gap: 9 },
  cardIcon: {
    width: 28, height: 28, borderRadius: 9, borderWidth: 1,
    alignItems: "center", justifyContent: "center",
  },
  cardTitle: { fontSize: 13, fontFamily: F.bold, letterSpacing: 0.2, color: "#fff" },

  summary: {
    fontSize: 13.5, fontFamily: F.semi,
    lineHeight: 21, letterSpacing: 0.1,
    color: "rgba(255,255,255,0.92)",
  },

  bullet: { width: 5, height: 5, borderRadius: 3, marginTop: 7 },
  bulletText: {
    flex: 1, color: "rgba(255,255,255,0.85)",
    fontSize: 12.5, fontFamily: F.regular, lineHeight: 19,
  },

  hookCard: {
    borderRadius: 18, borderWidth: 1.4,
    padding: 16,
    backgroundColor: "rgba(8,28,28,0.85)",
    overflow: "hidden",
  },
  hookRow: { flexDirection: "row", alignItems: "center", gap: 8 },
  hookIcon: {
    width: 26, height: 26, borderRadius: 8, borderWidth: 1,
    alignItems: "center", justifyContent: "center",
    backgroundColor: "rgba(20,184,166,0.15)",
  },
  hookHeading: { fontSize: 10, fontFamily: F.extra, letterSpacing: 2 },
  hookText: { fontSize: 13, fontFamily: F.semi, lineHeight: 20, color: "rgba(255,255,255,0.85)" },
  hookCta: { fontSize: 12.5, fontFamily: F.bold, marginTop: 12, lineHeight: 18, color: "#fff" },
  upgradeBtn: {
    flexDirection: "row", alignItems: "center", justifyContent: "center",
    gap: 7, paddingVertical: 12, borderRadius: 12,
  },
  upgradeBtnText: { color: "#fff", fontSize: 13.5, fontFamily: F.bold },

  kvRow: {
    flexDirection: "row", alignItems: "flex-start", gap: 12,
    paddingVertical: 6,
  },
  kvLeft: { width: 64 },
  kvHouse: { color: "#14b8a6", fontSize: 16, fontFamily: F.extra },
  kvSign: { color: "rgba(255,255,255,0.7)", fontSize: 11, fontFamily: F.semi },
  kvMeaning: {
    color: "#fff", fontSize: 12, fontFamily: F.bold,
    marginBottom: 3, letterSpacing: 0.2,
  },
  kvLabel: {
    color: "rgba(255,255,255,0.55)", fontSize: 11.5, fontFamily: F.semi, lineHeight: 18,
  },
  kvVal: { color: "#fff", fontFamily: F.bold },

  planetRow: {
    flexDirection: "row", alignItems: "center", gap: 8,
    paddingVertical: 4,
  },
  planetName: { width: 64, color: "#fff", fontSize: 13, fontFamily: F.bold },
  planetMeta: { flex: 1, color: "rgba(255,255,255,0.65)", fontSize: 11.5, fontFamily: F.semi },
  statusPill: {
    paddingHorizontal: 9, paddingVertical: 3,
    borderRadius: 10, borderWidth: 1,
  },
  statusText: { fontSize: 10, fontFamily: F.bold, letterSpacing: 0.3 },
});
