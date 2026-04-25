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
  I18nManager,
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

interface BasicBlock { score: number; trend: string; summary: string; hook: string; }
interface PlanetStrength { name: string; sign: string; house: number; status: string; retrograde?: boolean; }
interface HouseInfo { sign: string; lord: string; occupants: string; meaning: string; }
interface ProBlock {
  houses: { h2: HouseInfo; h11: HouseInfo; h5: HouseInfo; h9: HouseInfo };
  planets: PlanetStrength[];
  transit: string[];
  inflow: string[];
  expenses: string[];
  invest: string[];
  sudden: string[];
  stability: string;
  remedies: string[];
  reasons: string[];
}
interface FinanceResponse {
  level: "basic" | "pro";
  pro_locked: boolean;
  basic: BasicBlock;
  pro?: ProBlock;
}

function trendColor(t: string): string {
  if (t === "Gain")   return "#22c55e";
  if (t === "Loss")   return "#ef4444";
  return "#3b82f6";
}
function trendPhrase(trend: string, t: any): string {
  if (trend === "Gain")   return t.fn_growthPhase;
  if (trend === "Loss")   return t.fn_cautionPhase;
  return t.fn_stablePhase;
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
          <SvgGrad id="fring" x1="0" y1="0" x2="1" y2="1">
            <Stop offset="0" stopColor={color} stopOpacity={1} />
            <Stop offset="1" stopColor={color} stopOpacity={0.5} />
          </SvgGrad>
        </Defs>
        <Circle cx={size/2} cy={size/2} r={r}
          stroke="rgba(255,255,255,0.08)" strokeWidth={stroke} fill="none" />
        <Circle cx={size/2} cy={size/2} r={r}
          stroke="url(#fring)" strokeWidth={stroke} fill="none"
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

export default function FinanceScreen() {
  const insets = useSafeAreaInsets();
  const { user, kundli } = useUser();
  const t = useT();
  const { isPro, isTrial } = usePlan();
  const isProUser = isPro || isTrial;

  const [data, setData] = useState<FinanceResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);

  const fade = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    if (!user?.id || !user?.api_key) {
      setErr(t.fn_pageTitle + " — login required"); setLoading(false); return;
    }
    if (!kundli) {
      setErr(t.errKundliRequired);
      setLoading(false); return;
    }
    setLoading(true);
    apiFetch(`${API_BASE}/api/finance-analysis`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-API-Key": user.api_key },
      body: JSON.stringify({ user_id: user.id, kundli }),
    })
      .then(async r => {
        const j = await r.json();
        if (!r.ok) throw new Error(j?.error || "Analysis failed");
        return j as FinanceResponse;
      })
      .then(d => {
        setData(d); setErr(null);
        Animated.timing(fade, { toValue: 1, duration: 600, useNativeDriver: true }).start();
      })
      .catch(e => setErr(e?.message || "Finance analysis load nahi ho saka."))
      .finally(() => setLoading(false));
  }, [user?.id, user?.api_key, kundli]);

  const accent = "#3b82f6";

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
            <Feather name={I18nManager.isRTL ? "arrow-right" : "arrow-left"} size={20} color="#fff" />
          </View>
        </Pressable>
        <Text style={s.topTitle}>{t.fn_pageTitle}</Text>
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
                <LinearGradient colors={["#1d4ed8", "#3b82f6"]}
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
                colors={["rgba(59,130,246,0.18)", "rgba(59,130,246,0.04)", "transparent"]}
                start={{ x: 0.5, y: 0 }} end={{ x: 0.5, y: 1 }}
                style={StyleSheet.absoluteFill}
              />
              <View style={{ alignItems: "center", paddingTop: 8, paddingBottom: 16 }}>
                <Text style={s.heroLabel}>{t.fn_scoreLabel}</Text>
                <View style={{ marginTop: 12 }}>
                  <ScoreRing score={data.basic.score} color={trendColor(data.basic.trend)} />
                </View>
                <View style={[s.trendPill, {
                  backgroundColor: `${trendColor(data.basic.trend)}22`,
                  borderColor: `${trendColor(data.basic.trend)}66`,
                  marginTop: 14,
                }]}>
                  <View style={[s.trendDot, { backgroundColor: trendColor(data.basic.trend) }]} />
                  <Text style={[s.trendText, { color: trendColor(data.basic.trend) }]}>
                    {trendPhrase(data.basic.trend, t)}  •  {data.basic.trend}
                  </Text>
                </View>
              </View>
            </View>

            {/* SUMMARY */}
            <SectionCard icon="message-circle" title={t.cr_quickReading} accent={accent}>
              <Text style={s.summary}>{data.basic.summary}</Text>
            </SectionCard>

            {/* HOOK */}
            {!isProUser && (
              <View style={[s.hookCard, { borderColor: `${accent}55` }]}>
                <LinearGradient
                  colors={["rgba(59,130,246,0.18)", "rgba(59,130,246,0.05)"]}
                  start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }}
                  style={StyleSheet.absoluteFill}
                />
                <View style={s.hookRow}>
                  <View style={[s.hookIcon, { borderColor: `${accent}66` }]}>
                    <Feather name="zap" size={14} color={accent} />
                  </View>
                  <Text style={[s.hookHeading, { color: accent }]}>{t.fn_hidden}</Text>
                </View>

                <View style={{ position: "relative", marginTop: 8, minHeight: 56 }}>
                  <Text style={s.hookText}>{data.basic.hook}</Text>
                  {Platform.OS !== "web" ? (
                    <BlurView intensity={28} tint="dark"
                      style={[StyleSheet.absoluteFill, { borderRadius: 8 }]} />
                  ) : (
                    <View style={[StyleSheet.absoluteFill,
                      { backgroundColor: "rgba(8,16,30,0.55)", borderRadius: 8 }]} />
                  )}
                  <View style={[StyleSheet.absoluteFill, { alignItems: "center", justifyContent: "center" }]}>
                    <Feather name="lock" size={18} color={accent} />
                  </View>
                </View>

                <Text style={s.hookCta}>
                  Unlock full financial analysis with exact gain periods and money insights.
                </Text>

                <Pressable
                  onPress={() => {
                    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
                    router.push("/subscription");
                  }}
                  style={({ pressed }) => ({ opacity: pressed ? 0.85 : 1, marginTop: 12 })}
                >
                  <LinearGradient
                    colors={["#1d4ed8", "#3b82f6"]}
                    start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }}
                    style={s.upgradeBtn}
                  >
                    <Feather name="zap" size={14} color="#fff" />
                    <Text style={s.upgradeBtnText}>{t.cr_upgradeBtn}</Text>
                  </LinearGradient>
                </Pressable>
              </View>
            )}

            {/* PRO sections */}
            {isProUser && data.pro && (
              <>
                <SectionCard icon="home" title={t.fn_houses} accent={accent}>
                  {([
                    { num: 2,  info: data.pro.houses.h2  },
                    { num: 11, info: data.pro.houses.h11 },
                    { num: 5,  info: data.pro.houses.h5  },
                    { num: 9,  info: data.pro.houses.h9  },
                  ]).map(h => (
                    <View key={h.num} style={s.kvRow}>
                      <View style={s.kvLeft}>
                        <Text style={s.kvHouse}>{h.num}{h.num === 2 ? "nd" : h.num === 5 ? "th" : "th"}</Text>
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

                <SectionCard icon="star" title={t.fn_planets} accent={accent}>
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

                <SectionCard icon="globe" title={t.cr_transit} accent={accent}>
                  {data.pro.transit.map((t, i) => (<Bullet key={i} color={accent}>{t}</Bullet>))}
                </SectionCard>

                <SectionCard icon="trending-up" title={t.fn_inflow} accent="#22c55e">
                  {data.pro.inflow.map((t, i) => (<Bullet key={i} color="#22c55e">{t}</Bullet>))}
                </SectionCard>

                <SectionCard icon="trending-down" title={t.fn_expense} accent="#f59e0b">
                  {data.pro.expenses.map((t, i) => (<Bullet key={i} color="#f59e0b">{t}</Bullet>))}
                </SectionCard>

                <SectionCard icon="bar-chart-2" title={t.fn_invest} accent="#a78bfa">
                  {data.pro.invest.map((t, i) => (<Bullet key={i} color="#a78bfa">{t}</Bullet>))}
                </SectionCard>

                <SectionCard icon="zap" title={t.fn_sudden} accent="#fbbf24">
                  {data.pro.sudden.map((t, i) => (<Bullet key={i} color="#fbbf24">{t}</Bullet>))}
                </SectionCard>

                <SectionCard icon="shield" title={t.fn_stability} accent="#22c55e">
                  <Text style={[s.summary, { color: "rgba(255,255,255,0.9)" }]}>
                    {data.pro.stability}
                  </Text>
                </SectionCard>

                {/* DEEP — Wealth tier */}
                {!!(data.pro as any).wealth_tier && (
                  <SectionCard icon="award" title={`Wealth Tier — ${(data.pro as any).wealth_tier}`} accent="#fbbf24">
                    {typeof (data.pro as any).wealth_score === "number" && (
                      <View style={{ marginBottom: 10 }}>
                        <View style={{ flexDirection: "row", justifyContent: "space-between", marginBottom: 4 }}>
                          <Text style={{ color: "#94a3b8", fontSize: 12 }}>{t.fn_wealthKarma}</Text>
                          <Text style={{ color: "#fbbf24", fontSize: 13, fontWeight: "700" }}>{(data.pro as any).wealth_score}/95</Text>
                        </View>
                        <View style={{ height: 8, backgroundColor: "#1e293b", borderRadius: 4, overflow: "hidden" }}>
                          <View style={{ width: `${(data.pro as any).wealth_score}%`, height: "100%", backgroundColor: "#fbbf24" }} />
                        </View>
                      </View>
                    )}
                    <Text style={{ color: "#cbd5e1", fontSize: 13, lineHeight: 19 }}>
                      {(data.pro as any).wealth_tier_msg}
                    </Text>
                  </SectionCard>
                )}

                {/* Income sources */}
                {Array.isArray((data.pro as any).income_sources) && (data.pro as any).income_sources.length > 0 && (
                  <SectionCard icon="dollar-sign" title={t.fn_income} accent="#22c55e">
                    {(data.pro as any).income_sources.map((s: any, i: number) => (
                      <View key={i} style={{ marginBottom: 12 }}>
                        <View style={{ flexDirection: "row", justifyContent: "space-between", marginBottom: 4 }}>
                          <Text style={{ color: "#e2e8f0", fontSize: 13, fontWeight: "600", flex: 1 }}>{s.source}</Text>
                          <Text style={{ color: "#22c55e", fontSize: 12, fontWeight: "700" }}>{s.strength}%</Text>
                        </View>
                        <View style={{ height: 6, backgroundColor: "#1e293b", borderRadius: 3, overflow: "hidden", marginBottom: 3 }}>
                          <View style={{ width: `${s.strength}%`, height: "100%", backgroundColor: "#22c55e" }} />
                        </View>
                        <Text style={{ color: "#94a3b8", fontSize: 11 }}>{s.why}</Text>
                      </View>
                    ))}
                  </SectionCard>
                )}

                {/* Dhana yogas */}
                {Array.isArray((data.pro as any).dhana_yogas) && (data.pro as any).dhana_yogas.length > 0 && (
                  <SectionCard icon="star" title={`Dhana Yogas Detected (${(data.pro as any).yogas_count})`} accent="#a78bfa">
                    {(data.pro as any).dhana_yogas.map((y: any, i: number) => (
                      <View key={i} style={{ backgroundColor: "#1e1b4b", padding: 10, borderRadius: 8, marginBottom: 8, borderLeftWidth: 3, borderLeftColor: "#a78bfa" }}>
                        <Text style={{ color: "#c4b5fd", fontSize: 13, fontWeight: "700", marginBottom: 4 }}>{y.name}</Text>
                        <Text style={{ color: "#cbd5e1", fontSize: 12, lineHeight: 17 }}>{y.detail}</Text>
                      </View>
                    ))}
                  </SectionCard>
                )}

                <SectionCard icon="sun" title="Remedies (Practical & Astrological)" accent="#f59e0b">
                  {data.pro.remedies.map((t, i) => (<Bullet key={i} color="#f59e0b">{t}</Bullet>))}
                </SectionCard>

                {data.pro.reasons.length > 0 && (
                  <SectionCard icon="info" title={t.cr_reasoning} accent="#94a3b8">
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
    backgroundColor: "rgba(10,18,30,0.85)",
    borderWidth: 1.2,
    overflow: "hidden",
  },
  heroLabel: {
    color: "rgba(59,130,246,0.95)",
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
    backgroundColor: "rgba(10,15,25,0.78)",
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
    backgroundColor: "rgba(8,18,32,0.85)",
    overflow: "hidden",
  },
  hookRow: { flexDirection: "row", alignItems: "center", gap: 8 },
  hookIcon: {
    width: 26, height: 26, borderRadius: 8, borderWidth: 1,
    alignItems: "center", justifyContent: "center",
    backgroundColor: "rgba(59,130,246,0.15)",
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
  kvHouse: { color: "#3b82f6", fontSize: 16, fontFamily: F.extra },
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
