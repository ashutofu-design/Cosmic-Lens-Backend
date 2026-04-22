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
import { useC } from "@/context/ThemeContext";
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

interface BasicBlock {
  score: number;
  trend: "Good" | "Average" | "Risk" | string;
  summary: string;
  hook: string;
}
interface PlanetStrength {
  name: string; sign: string; house: number;
  status: string; retrograde?: boolean;
}
interface HouseInfo { house: number; sign: string; lord: string; occupants: string; }
interface ProBlock {
  houses: { h10: HouseInfo; h6: HouseInfo; h11: HouseInfo };
  planets: PlanetStrength[];
  dasha: { mahadasha: string; antardasha: string; verdict: string; ends: string };
  transit: string[];
  growth: string[];
  struggles: string[];
  promotion: string[];
  job_change: string[];
  risks: string[];
  reasons: string[];
}
interface CareerResponse {
  level: "basic" | "pro";
  pro_locked: boolean;
  basic: BasicBlock;
  pro?: ProBlock;
}

function trendColor(trend: string): string {
  if (trend === "Good")  return "#22c55e";
  if (trend === "Risk")  return "#ef4444";
  return "#f59e0b";
}

function ScoreRing({ score, color }: { score: number; color: string }) {
  const size = 168;
  const stroke = 14;
  const r = (size - stroke) / 2;
  const circ = 2 * Math.PI * r;
  const dash = (score / 100) * circ;
  const animated = useRef(new Animated.Value(0)).current;
  useEffect(() => {
    Animated.timing(animated, {
      toValue: 1, duration: 1200, easing: Easing.out(Easing.cubic),
      useNativeDriver: false,
    }).start();
  }, [score]);
  return (
    <View style={{ width: size, height: size, alignItems: "center", justifyContent: "center" }}>
      <Svg width={size} height={size}>
        <Defs>
          <SvgGrad id="ring" x1="0" y1="0" x2="1" y2="1">
            <Stop offset="0" stopColor={color} stopOpacity={1} />
            <Stop offset="1" stopColor={color} stopOpacity={0.5} />
          </SvgGrad>
        </Defs>
        <Circle cx={size / 2} cy={size / 2} r={r}
          stroke="rgba(255,255,255,0.08)" strokeWidth={stroke} fill="none" />
        <Circle cx={size / 2} cy={size / 2} r={r}
          stroke="url(#ring)" strokeWidth={stroke} fill="none"
          strokeDasharray={`${dash}, ${circ}`} strokeLinecap="round"
          transform={`rotate(-90 ${size / 2} ${size / 2})`} />
      </Svg>
      <View style={{ position: "absolute", alignItems: "center" }}>
        <Text style={{ color: "#fff", fontSize: 44, fontFamily: F.extra, letterSpacing: -1 }}>
          {score}
        </Text>
        <Text style={{ color: "rgba(255,255,255,0.5)", fontSize: 11, fontFamily: F.semi, letterSpacing: 1 }}>
          / 100
        </Text>
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
        <Text style={[s.cardTitle, { color: "#fff" }]}>{title}</Text>
      </View>
      <View style={{ gap: 8 }}>{children}</View>
    </View>
  );
}

function Bullet({ children, color }: { children: React.ReactNode; color: string }) {
  return (
    <View style={{ flexDirection: "row", gap: 8 }}>
      <View style={[s.bullet, { backgroundColor: color }]} />
      <Text style={[s.bulletText, { color: "rgba(255,255,255,0.85)" }]}>{children}</Text>
    </View>
  );
}

export default function CareerScreen() {
  const C = useC();
  const insets = useSafeAreaInsets();
  const { user, kundli } = useUser();
  const t = useT();
  const { isPro, isTrial } = usePlan();
  const isProUser = isPro || isTrial;

  const [data, setData] = useState<CareerResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);

  const fade = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    if (!user?.id || !user?.api_key) {
      setErr("Please log in to view your career analysis.");
      setLoading(false);
      return;
    }
    if (!kundli) {
      setErr(t.errKundliRequired);
      setLoading(false);
      return;
    }
    setLoading(true);
    apiFetch(`${API_BASE}/api/career-analysis`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-API-Key": user.api_key },
      body: JSON.stringify({ user_id: user.id, kundli }),
    })
      .then(async r => {
        const j = await r.json();
        if (!r.ok) throw new Error(j?.error || "Analysis failed");
        return j as CareerResponse;
      })
      .then(d => {
        setData(d);
        setErr(null);
        Animated.timing(fade, { toValue: 1, duration: 600, useNativeDriver: true }).start();
      })
      .catch(e => setErr(e?.message || "Career analysis load nahi ho saka."))
      .finally(() => setLoading(false));
  }, [user?.id, user?.api_key, kundli]);

  const accent = "#f59e0b";

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
        <Text style={s.topTitle}>Career Analysis</Text>
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
            <Text style={[s.cardTitle, { color: "#fff", textAlign: "center" }]}>
              {err}
            </Text>
            {!kundli && (
              <Pressable onPress={() => router.push("/profile-edit" as any)}
                style={({ pressed }) => ({ opacity: pressed ? 0.8 : 1, marginTop: 6 })}>
                <LinearGradient colors={["#d97706", "#f59e0b"]}
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
            {/* ─── HERO: Score + Trend ─── */}
            <View style={[s.hero, { borderColor: `${accent}3A` }]}>
              <LinearGradient
                colors={["rgba(245,158,11,0.18)", "rgba(245,158,11,0.04)", "transparent"]}
                start={{ x: 0.5, y: 0 }} end={{ x: 0.5, y: 1 }}
                style={StyleSheet.absoluteFill}
              />
              <View style={{ alignItems: "center", paddingTop: 8, paddingBottom: 16 }}>
                <Text style={s.heroLabel}>CAREER SCORE</Text>
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
                    {data.basic.trend === "Good" ? "Strong Phase" :
                     data.basic.trend === "Risk" ? "Caution Phase" : "Mixed Phase"}
                  </Text>
                </View>
              </View>
            </View>

            {/* ─── SUMMARY ─── */}
            <SectionCard icon="message-circle" title="Quick Reading" accent={accent}>
              <Text style={[s.summary, { color: "rgba(255,255,255,0.92)" }]}>
                {data.basic.summary}
              </Text>
            </SectionCard>

            {/* ─── PRO HOOK (visible to non-Pro users) ─── */}
            {!isProUser && (
              <View style={[s.hookCard, { borderColor: `${accent}55` }]}>
                <LinearGradient
                  colors={["rgba(245,158,11,0.18)", "rgba(245,158,11,0.05)"]}
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
                  <Text style={[s.hookText, { color: "rgba(255,255,255,0.85)" }]}>
                    {data.basic.hook}
                  </Text>
                  {Platform.OS !== "web" ? (
                    <BlurView
                      intensity={28}
                      tint="dark"
                      style={[StyleSheet.absoluteFill, { borderRadius: 8 }]}
                    />
                  ) : (
                    <View
                      style={[
                        StyleSheet.absoluteFill,
                        { backgroundColor: "rgba(20,12,5,0.55)", borderRadius: 8 },
                      ]}
                    />
                  )}
                  <View style={[StyleSheet.absoluteFill, { alignItems: "center", justifyContent: "center" }]}>
                    <Feather name="lock" size={18} color={accent} />
                  </View>
                </View>

                <Text style={[s.hookCta, { color: "#fff" }]}>
                  Unlock full career analysis with exact timing, reasons, and future opportunities.
                </Text>

                <Pressable
                  onPress={() => {
                    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
                    router.push("/subscription");
                  }}
                  style={({ pressed }) => ({ opacity: pressed ? 0.85 : 1, marginTop: 12 })}
                >
                  <LinearGradient
                    colors={["#d97706", "#f59e0b"]}
                    start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }}
                    style={s.upgradeBtn}
                  >
                    <Feather name="zap" size={14} color="#fff" />
                    <Text style={s.upgradeBtnText}>Upgrade to Pro</Text>
                  </LinearGradient>
                </Pressable>
              </View>
            )}

            {/* ─── PRO SECTIONS ─── */}
            {isProUser && data.pro && (
              <>
                {/* Houses */}
                <SectionCard icon="home" title="Career Houses" accent={accent}>
                  {[data.pro.houses.h10, data.pro.houses.h6, data.pro.houses.h11].map(h => (
                    <View key={h.house} style={s.kvRow}>
                      <View style={s.kvLeft}>
                        <Text style={s.kvHouse}>{h.house}th</Text>
                        <Text style={s.kvSign}>{h.sign}</Text>
                      </View>
                      <View style={{ flex: 1 }}>
                        <Text style={s.kvLabel}>Lord: <Text style={s.kvVal}>{h.lord}</Text></Text>
                        <Text style={s.kvLabel}>In house: <Text style={s.kvVal}>{h.occupants}</Text></Text>
                      </View>
                    </View>
                  ))}
                </SectionCard>

                {/* Planet strengths */}
                <SectionCard icon="star" title="Career Planets" accent={accent}>
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

                {/* Dasha */}
                <SectionCard icon="clock" title="Current Dasha Impact" accent={accent}>
                  <View style={s.dashaRow}>
                    <View style={s.dashaCol}>
                      <Text style={s.dashaLabel}>Mahadasha</Text>
                      <Text style={s.dashaVal}>{data.pro.dasha.mahadasha || "—"}</Text>
                    </View>
                    <View style={s.dashaCol}>
                      <Text style={s.dashaLabel}>Antardasha</Text>
                      <Text style={s.dashaVal}>{data.pro.dasha.antardasha || "—"}</Text>
                    </View>
                    <View style={s.dashaCol}>
                      <Text style={s.dashaLabel}>Ends</Text>
                      <Text style={s.dashaVal}>{data.pro.dasha.ends || "—"}</Text>
                    </View>
                  </View>
                  <Text style={[s.summary, { color: "rgba(255,255,255,0.85)", marginTop: 4 }]}>
                    {data.pro.dasha.verdict}
                  </Text>
                </SectionCard>

                {/* Transit */}
                <SectionCard icon="globe" title="Live Planetary Transit" accent={accent}>
                  {data.pro.transit.map((t, i) => (
                    <Bullet key={i} color={accent}>{t}</Bullet>
                  ))}
                </SectionCard>

                {/* Growth & Promotion */}
                <SectionCard icon="trending-up" title="Career Growth Periods" accent="#22c55e">
                  {data.pro.growth.map((t, i) => (<Bullet key={i} color="#22c55e">{t}</Bullet>))}
                  {data.pro.promotion.map((t, i) => (<Bullet key={`p${i}`} color="#22c55e">{t}</Bullet>))}
                </SectionCard>

                {/* Job change */}
                <SectionCard icon="shuffle" title="Job Change Timing" accent="#3b82f6">
                  {data.pro.job_change.map((t, i) => (<Bullet key={i} color="#3b82f6">{t}</Bullet>))}
                </SectionCard>

                {/* Struggles & Risks */}
                <SectionCard icon="alert-triangle" title="Struggle Phases & Hidden Risks" accent="#ef4444">
                  {data.pro.struggles.map((t, i) => (<Bullet key={i} color="#ef4444">{t}</Bullet>))}
                  {data.pro.risks.map((t, i) => (<Bullet key={`r${i}`} color="#ef4444">{t}</Bullet>))}
                </SectionCard>

                {/* DEEP — 10th lord analysis */}
                {(data.pro as any).tenth_lord?.planet && (
                  <SectionCard icon="award" title="10th Lord Deep Analysis (Karya Bhava)" accent="#22d3ee">
                    <View style={{ backgroundColor: "#0b1220", padding: 12, borderRadius: 10 }}>
                      <Text style={{ color: "#e2e8f0", fontSize: 14, marginBottom: 6 }}>
                        10th sign: <Text style={{ color: "#22d3ee", fontWeight: "700" }}>{(data.pro as any).tenth_lord.sign_10}</Text>{" "}
                        · Lord: <Text style={{ color: "#22d3ee", fontWeight: "700" }}>{(data.pro as any).tenth_lord.planet}</Text>
                      </Text>
                      {(data.pro as any).tenth_lord.current_house && (
                        <Text style={{ color: "#cbd5e1", fontSize: 13, marginBottom: 4 }}>
                          Currently in: {(data.pro as any).tenth_lord.current_sign} ({(data.pro as any).tenth_lord.current_house}H) · {(data.pro as any).tenth_lord.status}
                          {(data.pro as any).tenth_lord.retrograde ? " · retro" : ""}
                        </Text>
                      )}
                      {typeof (data.pro as any).tenth_lord.strength_pct === "number" && (
                        <View style={{ marginTop: 8, marginBottom: 8 }}>
                          <View style={{ flexDirection: "row", justifyContent: "space-between", marginBottom: 4 }}>
                            <Text style={{ color: "#94a3b8", fontSize: 12 }}>Career karma strength</Text>
                            <Text style={{ color: "#22d3ee", fontSize: 12, fontWeight: "700" }}>{(data.pro as any).tenth_lord.strength_pct}%</Text>
                          </View>
                          <View style={{ height: 8, backgroundColor: "#1e293b", borderRadius: 4, overflow: "hidden" }}>
                            <View style={{ width: `${(data.pro as any).tenth_lord.strength_pct}%`, height: "100%", backgroundColor: "#22d3ee" }} />
                          </View>
                        </View>
                      )}
                      <Text style={{ color: "#a78bfa", fontSize: 13, marginTop: 6 }}>{(data.pro as any).tenth_lord.verdict}</Text>
                    </View>
                  </SectionCard>
                )}

                {/* Atmakaraka */}
                {(data.pro as any).atmakaraka?.planet && (
                  <SectionCard icon="star" title={`Atmakaraka — ${(data.pro as any).atmakaraka.planet} (Soul Planet)`} accent="#fbbf24">
                    <Text style={{ color: "#cbd5e1", fontSize: 13, lineHeight: 19 }}>
                      {(data.pro as any).atmakaraka.meaning}
                    </Text>
                  </SectionCard>
                )}

                {/* Suitable career fields */}
                {Array.isArray((data.pro as any).suitable_fields) && (data.pro as any).suitable_fields.length > 0 && (
                  <SectionCard icon="briefcase" title="Suitable Career Fields (chart-driven)" accent="#22c55e">
                    {(data.pro as any).suitable_fields.map((f: any, i: number) => (
                      <View key={i} style={{ marginBottom: 12 }}>
                        <View style={{ flexDirection: "row", justifyContent: "space-between", marginBottom: 4 }}>
                          <Text style={{ color: "#e2e8f0", fontSize: 13, fontWeight: "600", flex: 1 }}>{i + 1}. {f.field}</Text>
                          <Text style={{ color: "#22c55e", fontSize: 12, fontWeight: "700" }}>{f.score}%</Text>
                        </View>
                        <View style={{ height: 6, backgroundColor: "#1e293b", borderRadius: 3, overflow: "hidden", marginBottom: 3 }}>
                          <View style={{ width: `${f.score}%`, height: "100%", backgroundColor: "#22c55e" }} />
                        </View>
                        <Text style={{ color: "#94a3b8", fontSize: 11 }}>{f.driver}</Text>
                      </View>
                    ))}
                  </SectionCard>
                )}

                {/* Business vs Job */}
                {!!(data.pro as any).business_vs_job && (
                  <SectionCard icon="trending-up" title="Business vs Job — Chart Verdict" accent="#a78bfa">
                    <Text style={{ color: "#e2e8f0", fontSize: 14, lineHeight: 20 }}>
                      {(data.pro as any).business_vs_job}
                    </Text>
                  </SectionCard>
                )}

                {/* Reasoning */}
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
    backgroundColor: "rgba(20,14,30,0.85)",
    borderWidth: 1.2,
    overflow: "hidden",
  },
  heroLabel: {
    color: "rgba(245,158,11,0.9)",
    fontSize: 10, letterSpacing: 2.4,
    fontFamily: F.extra, marginTop: 10,
  },
  trendPill: {
    flexDirection: "row", alignItems: "center", gap: 6,
    paddingHorizontal: 14, paddingVertical: 7,
    borderRadius: 20, borderWidth: 1,
  },
  trendDot: { width: 6, height: 6, borderRadius: 3 },
  trendText: { fontSize: 12, fontFamily: F.bold, letterSpacing: 0.3 },

  card: {
    borderRadius: 18, borderWidth: 1,
    backgroundColor: "rgba(15,10,25,0.78)",
    padding: 16, gap: 12,
    overflow: "hidden",
  },
  cardHead: { flexDirection: "row", alignItems: "center", gap: 9 },
  cardIcon: {
    width: 28, height: 28, borderRadius: 9, borderWidth: 1,
    alignItems: "center", justifyContent: "center",
  },
  cardTitle: { fontSize: 13, fontFamily: F.bold, letterSpacing: 0.2 },

  summary: {
    fontSize: 13.5, fontFamily: F.semi,
    lineHeight: 21, letterSpacing: 0.1,
  },

  bullet: {
    width: 5, height: 5, borderRadius: 3, marginTop: 7,
  },
  bulletText: {
    flex: 1,
    fontSize: 12.5, fontFamily: F.regular,
    lineHeight: 19,
  },

  hookCard: {
    borderRadius: 18, borderWidth: 1.4,
    padding: 16,
    backgroundColor: "rgba(35,22,8,0.85)",
    overflow: "hidden",
  },
  hookRow: { flexDirection: "row", alignItems: "center", gap: 8 },
  hookIcon: {
    width: 26, height: 26, borderRadius: 8, borderWidth: 1,
    alignItems: "center", justifyContent: "center",
    backgroundColor: "rgba(245,158,11,0.15)",
  },
  hookHeading: {
    fontSize: 10, fontFamily: F.extra, letterSpacing: 2,
  },
  hookText: {
    fontSize: 13, fontFamily: F.semi,
    lineHeight: 20,
  },
  hookCta: {
    fontSize: 12.5, fontFamily: F.bold,
    marginTop: 12, lineHeight: 18,
  },
  upgradeBtn: {
    flexDirection: "row", alignItems: "center", justifyContent: "center",
    gap: 7, paddingVertical: 12, borderRadius: 12,
  },
  upgradeBtnText: {
    color: "#fff", fontSize: 13.5, fontFamily: F.bold,
  },

  kvRow: {
    flexDirection: "row", alignItems: "center", gap: 12,
    paddingVertical: 6,
  },
  kvLeft: {
    width: 64, alignItems: "flex-start",
  },
  kvHouse: {
    color: "#f59e0b", fontSize: 16, fontFamily: F.extra,
  },
  kvSign: {
    color: "rgba(255,255,255,0.7)", fontSize: 11, fontFamily: F.semi,
  },
  kvLabel: {
    color: "rgba(255,255,255,0.55)", fontSize: 11.5, fontFamily: F.semi,
    lineHeight: 18,
  },
  kvVal: {
    color: "#fff", fontFamily: F.bold,
  },

  planetRow: {
    flexDirection: "row", alignItems: "center", gap: 8,
    paddingVertical: 4,
  },
  planetName: {
    width: 64, color: "#fff", fontSize: 13, fontFamily: F.bold,
  },
  planetMeta: {
    flex: 1, color: "rgba(255,255,255,0.65)", fontSize: 11.5, fontFamily: F.semi,
  },
  statusPill: {
    paddingHorizontal: 9, paddingVertical: 3,
    borderRadius: 10, borderWidth: 1,
  },
  statusText: { fontSize: 10, fontFamily: F.bold, letterSpacing: 0.3 },

  dashaRow: {
    flexDirection: "row", gap: 10,
    paddingVertical: 4,
  },
  dashaCol: { flex: 1, alignItems: "center", gap: 3 },
  dashaLabel: {
    color: "rgba(255,255,255,0.5)", fontSize: 9.5,
    fontFamily: F.bold, letterSpacing: 1.2,
  },
  dashaVal: {
    color: "#fff", fontSize: 13, fontFamily: F.extra,
  },
});
