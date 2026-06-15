import { Feather } from "@expo/vector-icons";
import { BlurView } from "expo-blur";
import * as Haptics from "expo-haptics";
import { LinearGradient } from "expo-linear-gradient";
import { router } from "expo-router";
import React, { useEffect, useMemo, useRef, useState } from "react";
import {
  ActivityIndicator,
  Animated,
  Easing,
  I18nManager,
  Platform,
  Pressable,
  Modal,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from "react-native";
import Svg, { Circle, Defs, LinearGradient as SvgGrad, Stop } from "react-native-svg";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { CosmicBg } from "@/components/CosmicBg";
import { useUser } from "@/context/UserContext";
import { useT } from "@/hooks/useT";
import { API_BASE, apiFetch } from "@/lib/apiConfig";
import { usePlan } from "@/lib/subscription";
import {
  financeWealthCopy,
  WEALTH_TIER_ORDER,
  wealthTierFromScore,
  type LeakageKey,
  type LiquidityKey,
  type WealthTierKey,
} from "@/lib/financeWealthCopy";
import { buildPersonalSnapshot } from "@/lib/personalizationSnapshot";
import {
  buildWealthDashaTimeline,
  currentOperationalWealthScore,
  formatDashaRange,
  type WealthDashaTimeline,
} from "@/lib/wealthDashaTiming";
import { coerceUILang } from "@/lib/i18n";

const F = {
  regular: "Nunito_400Regular",
  semi:    "Nunito_600SemiBold",
  bold:    "Nunito_700Bold",
  extra:   "Nunito_800ExtraBold",
} as const;

type YogaItem = {
  name: string;
  detail: string;
  link?: string;
  houses?: number[];
  planets?: string[];
};

type LeakChannelAlert = {
  channel: string;
  fact: string;
  severity?: number;
  message_en: string;
  message_hn?: string;
  message_hi?: string;
};

function leakChannelMessage(alert: LeakChannelAlert, lang: string): string {
  const L = coerceUILang(lang);
  if (L === "hi" && alert.message_hi) return alert.message_hi;
  if (L === "hn" && alert.message_hn) return alert.message_hn;
  return alert.message_en;
}

function resolveYogas(
  yog: BasicBlock["wealth_finance"] extends { yog_metrics?: infer Y } ? Y : undefined,
  key: "dhan" | "raj",
  basicFallback?: Array<{ name: string; detail?: string }>,
): YogaItem[] {
  const listKey = key === "dhan" ? "dhan_yogas" : "raj_yogas";
  const namesKey = key === "dhan" ? "dhan_yoga_names" : "raj_yoga_names";
  const countKey = key === "dhan" ? "dhan_count" : "raj_count";
  const label = key === "dhan" ? "Dhan Yog" : "Raj Yog";

  const fromMetrics = (yog?.[listKey] as YogaItem[] | undefined)?.filter((x) => x?.name) ?? [];
  if (fromMetrics.length > 0) return fromMetrics;

  const fromBasic = (basicFallback ?? []).filter((x) => x?.name).map((x) => ({
    name: x.name,
    detail: x.detail ?? "",
    link: x.link ?? "",
    houses: x.houses ?? [],
    planets: x.planets ?? [],
  }));
  if (fromBasic.length > 0) return fromBasic;

  const names = yog?.[namesKey]?.filter(Boolean) ?? [];
  if (names.length > 0) {
    return names.map((name) => ({
      name,
      detail: "",
      link: "",
      houses: [] as number[],
      planets: [] as string[],
    }));
  }

  const count = yog?.[countKey] ?? 0;
  if (count > 0) {
    return Array.from({ length: count }, (_, i) => ({
      name: `${label} ${i + 1}`,
      detail: "",
      link: "",
      houses: [] as number[],
      planets: [] as string[],
    }));
  }

  return [];
}

type WealthCopy = ReturnType<typeof financeWealthCopy>;

function yogaHouseHint(houses: number[] | undefined, wealthCopy: WealthCopy): string | null {
  if (!houses?.length) return null;
  if (houses.length === 2) return wealthCopy.housePair(houses[0], houses[1]);
  if (typeof wealthCopy.housesLine === "function") {
    return wealthCopy.housesLine(houses);
  }
  return `Houses ${houses.join(", ")}`;
}

function YogaDetailModal({
  visible,
  onClose,
  title,
  subtitle,
  items,
  emptyText,
  closeLabel,
  wealthCopy,
  accent,
}: {
  visible: boolean;
  onClose: () => void;
  title: string;
  subtitle: string;
  items: YogaItem[];
  emptyText: string;
  closeLabel: string;
  wealthCopy: WealthCopy;
  accent: { name: string; pillBorder: string; pillBg: string; pillText: string };
}) {
  return (
    <Modal visible={visible} animationType="slide" transparent onRequestClose={onClose}>
      <Pressable style={s.modalBackdrop} onPress={onClose}>
        <Pressable style={s.modalSheet} onPress={(e) => e.stopPropagation()}>
          <View style={s.modalHandle} />
          <Text style={s.modalTitle}>{title}</Text>
          <Text style={s.modalSub}>{subtitle}</Text>
          <ScrollView style={{ maxHeight: 420 }} showsVerticalScrollIndicator={false}>
            {items.length > 0 ? (
              items.map((item, i) => {
                const linkKey = item.link ?? "";
                const linkLabel = wealthCopy.linkType[linkKey] ?? linkKey;
                const houseHint = yogaHouseHint(item.houses, wealthCopy);
                return (
                  <View key={`${item.name}-${i}`} style={s.dhanDetailRow}>
                    <Text style={[s.dhanDetailName, accent.name ? { color: accent.name } : null]}>
                      {item.name}
                    </Text>
                    {linkLabel ? (
                      <View style={[s.dhanLinkPill, {
                        borderColor: accent.pillBorder,
                        backgroundColor: accent.pillBg,
                      }]}>
                        <Text style={[s.dhanLinkPillText, { color: accent.pillText }]}>
                          {linkLabel}
                        </Text>
                      </View>
                    ) : null}
                    {houseHint ? (
                      <Text style={s.dhanDetailMeta}>{houseHint}</Text>
                    ) : null}
                    {item.planets && item.planets.length > 0 ? (
                      <Text style={s.dhanDetailMeta}>{item.planets.join(" • ")}</Text>
                    ) : null}
                    <Text style={s.dhanDetailBody}>{item.detail || "—"}</Text>
                  </View>
                );
              })
            ) : (
              <Text style={s.dhanDetailBody}>{emptyText}</Text>
            )}
          </ScrollView>
          <Pressable
            onPress={onClose}
            style={({ pressed }) => [s.modalCloseBtn, { opacity: pressed ? 0.85 : 1 }]}
          >
            <Text style={s.modalCloseText}>{closeLabel}</Text>
          </Pressable>
        </Pressable>
      </Pressable>
    </Modal>
  );
}

interface BasicBlock {
  score: number;
  trend: string;
  summary: string;
  wealth_karma_score?: number;
  wealth_score?: number;
  hook: string;
  money_habits?: string[];
  dhana_yogas?: YogaItem[];
  raj_yogas?: YogaItem[];
  wealth_finance?: {
    engine?: string;
    disclaimer?: string;
    yog_metrics?: {
      dhan_count?: number;
      raj_count?: number;
      total_count?: number;
      activation_pct?: number;
      active_yogas?: string[];
      dhan_yoga_names?: string[];
      dhan_yogas?: YogaItem[];
      raj_yoga_names?: string[];
      raj_yogas?: YogaItem[];
    };
    chart_matrix?: {
      d1_verdict?: string;
      d9_verdict?: string;
      d2_tag?: string;
      d2_chandra_pct?: number;
    };
    wealth_tier?: WealthTierKey;
    wealth_tier_label?: string;
    wealth_source?: { channel?: string; path?: string; label?: string };
    leakage_alerts?: string[];
    leakage_channels?: LeakChannelAlert[];
    current_liquidity_index?: LiquidityKey;
  };
}
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
  icon, title, children, accent, compact, headerRight,
}: {
  icon: React.ComponentProps<typeof Feather>["name"];
  title: string;
  children: React.ReactNode;
  accent: string;
  compact?: boolean;
  headerRight?: React.ReactNode;
}) {
  return (
    <View style={[s.card, compact && s.cardCompact, { borderColor: `${accent}33` }]}>
      <LinearGradient
        colors={["rgba(255,255,255,0.04)", "rgba(255,255,255,0.01)"]}
        start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }}
        style={StyleSheet.absoluteFill}
        pointerEvents="none"
      />
      <View style={[s.cardHead, compact && s.cardHeadCompact]}>
        <View style={s.cardHeadLeft}>
          <View style={[
            s.cardIcon,
            compact && s.cardIconCompact,
            { backgroundColor: `${accent}1F`, borderColor: `${accent}55` },
          ]}>
            <Feather name={icon} size={compact ? 12 : 14} color={accent} />
          </View>
          <Text style={[s.cardTitle, compact && s.cardTitleCompact]}>{title}</Text>
        </View>
        {headerRight}
      </View>
      <View style={{ gap: compact ? 6 : 8 }}>{children}</View>
    </View>
  );
}

function wealthScoreColor(score: number): string {
  if (score >= 72) return "#22c55e";
  if (score >= 60) return "#fbbf24";
  return "rgba(255,255,255,0.55)";
}

function DashaScoreBadge({
  score,
  wealthCopy,
}: {
  score: number;
  wealthCopy: ReturnType<typeof financeWealthCopy>;
}) {
  const tierKey = wealthTierFromScore(score);
  return (
    <View style={s.dashaScoreCol}>
      <Text style={[s.dashaScoreText, { color: wealthScoreColor(score) }]}>{score}</Text>
      <Text style={s.dashaTierText} numberOfLines={1}>
        {wealthCopy.tierLabels[tierKey]}
      </Text>
    </View>
  );
}

function WealthDashaTimingModal({
  visible,
  onClose,
  timeline,
  wealthCopy,
}: {
  visible: boolean;
  onClose: () => void;
  timeline: WealthDashaTimeline | null;
  wealthCopy: ReturnType<typeof financeWealthCopy>;
}) {
  return (
    <Modal visible={visible} animationType="slide" transparent onRequestClose={onClose}>
      <View style={s.modalBackdrop}>
        <Pressable style={s.modalBackdropDismiss} onPress={onClose} accessibilityRole="button" />
        <View style={[s.modalSheet, s.dashaTimingSheet]}>
          <View style={s.modalHandle} />
          <Text style={s.modalTitle}>{wealthCopy.dashaTimingTitle}</Text>
          <Text style={s.modalSub}>{wealthCopy.dashaTimingSub}</Text>
          <ScrollView
            style={s.dashaTimingScroll}
            contentContainerStyle={s.dashaTimingScrollContent}
            showsVerticalScrollIndicator
            nestedScrollEnabled
            keyboardShouldPersistTaps="handled"
          >
            {!timeline ? (
              <Text style={s.dhanDetailBody}>{wealthCopy.dashaNoData}</Text>
            ) : (
              <>
                <Text style={s.dashaMetaLine}>
                  {wealthCopy.dashaBaseLabel}: {Math.round(timeline.baseScore * 4) / 4}
                </Text>
                {timeline.bestMd ? (
                  <Text style={s.dashaMetaLine}>
                    {wealthCopy.dashaBestMd}: {timeline.bestMd.planet} ({timeline.bestMd.score} · {wealthCopy.tierLabels[wealthTierFromScore(timeline.bestMd.score)]})
                  </Text>
                ) : null}
                {timeline.bestAd ? (
                  <Text style={[s.dashaMetaLine, { marginBottom: 12 }]}>
                    {wealthCopy.dashaBestAd}: {timeline.bestAd.mdPlanet}/{timeline.bestAd.planet} ({timeline.bestAd.score} · {wealthCopy.tierLabels[wealthTierFromScore(timeline.bestAd.score)]})
                  </Text>
                ) : null}
                {timeline.mahadashas.map(md => (
                  <View key={`${md.planet}-${md.startDate}`} style={s.dashaMdBlock}>
                    <View style={[s.dashaRow, md.isCurrent && s.dashaRowCurrent]}>
                      <View style={{ flex: 1, gap: 2 }}>
                        <View style={{ flexDirection: "row", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
                          <Text style={s.dashaMdText}>
                            {wealthCopy.dashaMdLabel} {md.planet}
                          </Text>
                          {md.isWealthLinked ? (
                            <Text style={s.dashaWealthChip}>{wealthCopy.dashaWealthTag}</Text>
                          ) : null}
                        </View>
                        <Text style={s.dashaDateText}>{formatDashaRange(md.startDate, md.endDate)}</Text>
                      </View>
                      <DashaScoreBadge score={md.score} wealthCopy={wealthCopy} />
                    </View>
                    {md.antardashas.map(ad => (
                      <View
                        key={`${md.planet}-${ad.planet}-${ad.startDate}`}
                        style={[s.dashaRow, s.dashaAdRow, ad.isCurrent && s.dashaRowCurrent]}
                      >
                        <View style={{ flex: 1, gap: 2 }}>
                          <View style={{ flexDirection: "row", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
                            <Text style={s.dashaAdText}>
                              {wealthCopy.dashaAdLabel} {ad.planet}
                            </Text>
                            {ad.isWealthLinked ? (
                              <Text style={s.dashaWealthChip}>{wealthCopy.dashaWealthTag}</Text>
                            ) : null}
                          </View>
                          <Text style={s.dashaDateText}>{formatDashaRange(ad.startDate, ad.endDate)}</Text>
                        </View>
                        <DashaScoreBadge score={ad.score} wealthCopy={wealthCopy} />
                      </View>
                    ))}
                  </View>
                ))}
              </>
            )}
          </ScrollView>
        </View>
      </View>
    </Modal>
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
  const wealthCopy = financeWealthCopy(coerceUILang(t.lang));
  const { isPro, isTrial } = usePlan();
  const isProUser = isPro || isTrial;

  const [data, setData] = useState<FinanceResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);
  const [yogaDetailOpen, setYogaDetailOpen] = useState<"dhan" | "raj" | null>(null);
  const [dashaTimingOpen, setDashaTimingOpen] = useState(false);

  const openYogaDetail = (kind: "dhan" | "raj") => {
    setYogaDetailOpen(kind);
    void Haptics.selectionAsync().catch(() => undefined);
  };

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
  const wf = data?.basic?.wealth_finance;
  const yog = wf?.yog_metrics;
  const wealthBuilderScore = useMemo(() => {
    const snap = buildPersonalSnapshot(kundli);
    const wb = snap.categoryScores.find(item => item.type === "Wealth Builder Kundli");
    return wb?.score ?? null;
  }, [kundli]);
  const wealthBaseScore = wealthBuilderScore ?? data?.basic?.wealth_karma_score ?? data?.basic?.wealth_score ?? 50;
  const birthTierKey = useMemo((): WealthTierKey => {
    return wealthTierFromScore(wealthBaseScore);
  }, [wealthBaseScore]);
  const wealthDashaTimeline = useMemo(
    () => buildWealthDashaTimeline(kundli, wealthBaseScore),
    [kundli, wealthBaseScore],
  );
  const currentDashaWealth = useMemo(() => {
    const direct = currentOperationalWealthScore(kundli, wealthBaseScore);
    if (direct) return direct;
    if (!wealthDashaTimeline) return null;
    for (const md of wealthDashaTimeline.mahadashas) {
      const ad = md.antardashas.find(row => row.isCurrent);
      if (ad) {
        return { mdPlanet: md.planet, adPlanet: ad.planet, score: ad.score };
      }
      if (md.isCurrent) {
        return { mdPlanet: md.planet, adPlanet: "", score: md.score };
      }
    }
    return null;
  }, [kundli, wealthBaseScore, wealthDashaTimeline]);
  const tierKey = useMemo((): WealthTierKey => {
    if (currentDashaWealth) return wealthTierFromScore(currentDashaWealth.score);
    return birthTierKey;
  }, [currentDashaWealth, birthTierKey]);
  const dhanYogas = resolveYogas(yog, "dhan", data?.basic?.dhana_yogas);
  const rajYogas = resolveYogas(yog, "raj", data?.basic?.raj_yogas);
  const headerTopPad = insets.top + 8;
  const scrollTopPad = headerTopPad + 52;

  return (
    <CosmicBg>
      <LinearGradient
        colors={["rgba(0,0,0,0.45)", "transparent", "rgba(0,0,0,0.3)"]}
        locations={[0, 0.4, 1]}
        style={StyleSheet.absoluteFill}
        pointerEvents="none"
      />

      <View style={[s.topBar, { paddingTop: headerTopPad }]}>
        {Platform.OS === "ios" ? (
          <BlurView intensity={48} tint="dark" style={StyleSheet.absoluteFill} />
        ) : (
          <View style={[StyleSheet.absoluteFill, s.topBarBg]} />
        )}
        <View style={s.topBarRow}>
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
      </View>

      <ScrollView
        contentContainerStyle={{
          paddingTop: scrollTopPad,
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

            {/* WEALTH YOGAS */}
            {wf && yog && (
              <SectionCard icon="star" title={wealthCopy.yogTitle} accent="#fbbf24" compact>
                <View style={s.yogRow}>
                  <TouchableOpacity
                    activeOpacity={0.85}
                    onPress={() => openYogaDetail("dhan")}
                    style={s.yogPress}
                    accessibilityRole="button"
                    accessibilityLabel={wealthCopy.dhanYogCard}
                  >
                    <View style={s.yogCompact}>
                      <Text style={s.yogCompactLabel}>{wealthCopy.dhanYogCard}</Text>
                      <View style={s.yogCompactRight}>
                        <Text style={s.yogCompactNum}>{yog.dhan_count ?? 0}</Text>
                        <Feather name="chevron-right" size={12} color="#fbbf24" />
                      </View>
                    </View>
                  </TouchableOpacity>
                  <TouchableOpacity
                    activeOpacity={0.85}
                    onPress={() => openYogaDetail("raj")}
                    style={s.yogPress}
                    accessibilityRole="button"
                    accessibilityLabel={wealthCopy.rajYogCard}
                  >
                    <View style={[s.yogCompact, s.yogCompactRaj]}>
                      <Text style={[s.yogCompactLabel, s.yogCompactLabelRaj]}>{wealthCopy.rajYogCard}</Text>
                      <View style={s.yogCompactRight}>
                        <Text style={[s.yogCompactNum, s.yogCompactNumRaj]}>{yog.raj_count ?? 0}</Text>
                        <Feather name="chevron-right" size={12} color="#c4b5fd" />
                      </View>
                    </View>
                  </TouchableOpacity>
                </View>
              </SectionCard>
            )}

            {/* WEALTH TIER + SOURCE */}
            {wf && (
              <SectionCard icon="award" title={wealthCopy.tierTitle} accent="#fbbf24">
                <View style={s.tierRow}>
                  {WEALTH_TIER_ORDER.map(key => {
                    const selected = key === tierKey;
                    return (
                      <View
                        key={key}
                        style={[
                          s.tierTag,
                          selected ? s.tierTagSelected : s.tierTagFaded,
                        ]}
                      >
                        <Text
                          style={[
                            s.tierTagText,
                            selected ? s.tierTagTextSelected : s.tierTagTextFaded,
                          ]}
                          numberOfLines={1}
                        >
                          {wealthCopy.tierLabels[key]}
                        </Text>
                      </View>
                    );
                  })}
                </View>
                <Text style={s.tierSubtitle}>{wealthCopy.tierSubtitle}</Text>
                {currentDashaWealth ? (
                  <Text style={[s.miniLine, { marginTop: 10 }]}>
                    {wealthCopy.tierCurrentDashaLine(
                      currentDashaWealth.mdPlanet,
                      currentDashaWealth.adPlanet,
                      currentDashaWealth.score,
                      wealthCopy.tierLabels[tierKey],
                    )}
                  </Text>
                ) : null}
                {wealthBuilderScore != null ? (
                  <Text style={[s.miniLine, { marginTop: currentDashaWealth ? 6 : 10 }]}>
                    {wealthCopy.tierBirthLine(
                      Math.round(wealthBuilderScore * 4) / 4,
                      wealthCopy.tierLabels[birthTierKey],
                    )}
                  </Text>
                ) : null}
                <Pressable
                  onPress={() => {
                    setDashaTimingOpen(true);
                    void Haptics.selectionAsync().catch(() => undefined);
                  }}
                  style={({ pressed }) => [s.dashaTimingLinkRow, { opacity: pressed ? 0.85 : 1 }]}
                >
                  <Feather name="clock" size={14} color="#fbbf24" />
                  <Text style={s.dashaTimingLinkText}>{wealthCopy.dashaTimingTitle}</Text>
                  <Text style={s.tierViewBtnText}>{wealthCopy.dashaTimingView}</Text>
                  <Feather name="chevron-right" size={16} color="#fbbf24" />
                </Pressable>
              </SectionCard>
            )}

            {/* LEAKAGE */}
            {wf && (
              <SectionCard icon="alert-triangle" title={wealthCopy.leakageTitle} accent="#f59e0b">
                {(wf.leakage_channels?.length ?? 0) > 0 ? (
                  wf.leakage_channels!.map((alert, i) => (
                    <Text key={`${alert.channel}-${i}`} style={s.miniLine}>
                      • {leakChannelMessage(alert, t.lang)}
                    </Text>
                  ))
                ) : (wf.leakage_alerts?.length ?? 0) > 0 ? (
                  wf.leakage_alerts!.map((flag, i) => (
                    <Text key={`${flag}-${i}`} style={s.miniLine}>
                      • {wealthCopy.leakage[flag as LeakageKey] ?? flag}
                    </Text>
                  ))
                ) : (
                  <Text style={s.miniLine}>{wealthCopy.leakageEmpty}</Text>
                )}
                <Text style={[s.disclaimer, { marginTop: 8 }]}>{wf.disclaimer ?? wealthCopy.disclaimer}</Text>
              </SectionCard>
            )}

            {/* MONEY HABITS */}
            {(data.basic.money_habits?.length ?? 0) > 0 && (
              <SectionCard icon="check-circle" title={wealthCopy.habitsTitle} accent="#22c55e">
                {data.basic.money_habits!.slice(0, 4).map((line, i) => (
                  <Bullet key={i} color="#22c55e">{line}</Bullet>
                ))}
              </SectionCard>
            )}

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

      <YogaDetailModal
        visible={yogaDetailOpen !== null}
        onClose={() => setYogaDetailOpen(null)}
        title={yogaDetailOpen === "raj" ? wealthCopy.rajDetailTitle : wealthCopy.dhanDetailTitle}
        subtitle={yogaDetailOpen === "raj" ? wealthCopy.rajDetailSub : wealthCopy.dhanDetailSub}
        items={yogaDetailOpen === "raj" ? rajYogas : dhanYogas}
        emptyText={yogaDetailOpen === "raj" ? wealthCopy.rajEmpty : wealthCopy.dhanEmpty}
        closeLabel={wealthCopy.close}
        wealthCopy={wealthCopy}
        accent={
          yogaDetailOpen === "raj"
            ? {
                name: "#e9d5ff",
                pillBorder: "rgba(167,139,250,0.5)",
                pillBg: "rgba(167,139,250,0.15)",
                pillText: "#c4b5fd",
              }
            : {
                name: "",
                pillBorder: "rgba(251,191,36,0.45)",
                pillBg: "rgba(251,191,36,0.12)",
                pillText: "#fbbf24",
              }
        }
      />
      <WealthDashaTimingModal
        visible={dashaTimingOpen}
        onClose={() => setDashaTimingOpen(false)}
        timeline={wealthDashaTimeline}
        wealthCopy={wealthCopy}
      />
    </CosmicBg>
  );
}

const s = StyleSheet.create({
  topBar: {
    position: "absolute", top: 0, left: 0, right: 0,
    zIndex: 20,
    paddingHorizontal: 14,
    paddingBottom: 12,
    borderBottomWidth: 1,
    borderBottomColor: "rgba(255,255,255,0.08)",
    overflow: "hidden",
  },
  topBarBg: {
    backgroundColor: "rgba(10,18,30,0.94)",
  },
  topBarRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
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
  cardCompact: {
    padding: 11,
    gap: 8,
    borderRadius: 14,
  },
  cardHead: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    gap: 10,
  },
  cardHeadLeft: {
    flexDirection: "row",
    alignItems: "center",
    gap: 9,
    flexShrink: 1,
    flex: 1,
  },
  cardHeadCompact: { gap: 7 },
  cardIcon: {
    width: 28, height: 28, borderRadius: 9, borderWidth: 1,
    alignItems: "center", justifyContent: "center",
  },
  cardIconCompact: {
    width: 22, height: 22, borderRadius: 7,
  },
  cardTitle: { fontSize: 13, fontFamily: F.bold, letterSpacing: 0.2, color: "#fff" },
  cardTitleCompact: { fontSize: 12 },

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

  chipGold: {
    borderRadius: 999,
    borderWidth: 1,
    borderColor: "rgba(251,191,36,0.4)",
    backgroundColor: "rgba(251,191,36,0.1)",
    paddingHorizontal: 12,
    paddingVertical: 6,
  },
  chipGoldText: { color: "#fbbf24", fontSize: 11, fontFamily: F.semi },
  yogRow: {
    flexDirection: "row",
    gap: 8,
    zIndex: 2,
  },
  yogPress: {
    flex: 1,
    minWidth: 0,
  },
  yogCompact: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    borderRadius: 10,
    borderWidth: 1,
    borderColor: "rgba(251,191,36,0.35)",
    backgroundColor: "rgba(251,191,36,0.08)",
    paddingHorizontal: 10,
    paddingVertical: 9,
    width: "100%",
  },
  yogCompactRaj: {
    borderColor: "rgba(167,139,250,0.35)",
    backgroundColor: "rgba(167,139,250,0.08)",
  },
  yogCompactLabel: {
    color: "#fbbf24",
    fontSize: 11,
    fontFamily: F.semi,
    letterSpacing: 0.3,
    flexShrink: 1,
  },
  yogCompactLabelRaj: {
    color: "#c4b5fd",
  },
  yogCompactRight: {
    flexDirection: "row",
    alignItems: "center",
    gap: 4,
    marginLeft: 6,
  },
  yogCompactNum: {
    color: "#fbbf24",
    fontSize: 20,
    fontFamily: F.extra,
    lineHeight: 22,
  },
  yogCompactNumRaj: {
    color: "#c4b5fd",
  },
  modalBackdrop: {
    flex: 1,
    backgroundColor: "rgba(0,0,0,0.65)",
    justifyContent: "flex-end",
  },
  modalBackdropDismiss: {
    ...StyleSheet.absoluteFillObject,
  },
  modalSheet: {
    backgroundColor: "#0f172a",
    borderTopLeftRadius: 22,
    borderTopRightRadius: 22,
    borderWidth: 1,
    borderColor: "rgba(251,191,36,0.25)",
    padding: 20,
    paddingBottom: 28,
  },
  dashaTimingSheet: {
    maxHeight: "85%",
  },
  dashaTimingScroll: {
    flexGrow: 0,
    flexShrink: 1,
  },
  dashaTimingScrollContent: {
    paddingBottom: 8,
  },
  modalHandle: {
    width: 40,
    height: 4,
    borderRadius: 2,
    backgroundColor: "rgba(255,255,255,0.2)",
    alignSelf: "center",
    marginBottom: 14,
  },
  modalTitle: {
    color: "#fbbf24",
    fontSize: 17,
    fontFamily: F.bold,
    marginBottom: 6,
  },
  modalSub: {
    color: "rgba(255,255,255,0.55)",
    fontSize: 12,
    lineHeight: 18,
    fontFamily: F.regular,
    marginBottom: 14,
  },
  dhanDetailRow: {
    borderLeftWidth: 3,
    borderLeftColor: "#fbbf24",
    backgroundColor: "rgba(251,191,36,0.08)",
    borderRadius: 10,
    padding: 12,
    marginBottom: 10,
  },
  dhanDetailName: {
    color: "#fff",
    fontSize: 14,
    fontFamily: F.bold,
    marginBottom: 6,
  },
  dhanLinkPill: {
    alignSelf: "flex-start",
    backgroundColor: "rgba(251,191,36,0.15)",
    borderRadius: 999,
    paddingHorizontal: 10,
    paddingVertical: 4,
    marginBottom: 6,
  },
  dhanLinkPillText: {
    color: "#fbbf24",
    fontSize: 10,
    fontFamily: F.semi,
    textTransform: "uppercase",
  },
  dhanDetailMeta: {
    color: "rgba(255,255,255,0.5)",
    fontSize: 11,
    fontFamily: F.semi,
    marginBottom: 4,
  },
  dhanDetailBody: {
    color: "rgba(255,255,255,0.82)",
    fontSize: 12,
    lineHeight: 18,
    fontFamily: F.regular,
  },
  modalCloseBtn: {
    marginTop: 14,
    backgroundColor: "rgba(251,191,36,0.15)",
    borderRadius: 12,
    paddingVertical: 12,
    alignItems: "center",
    borderWidth: 1,
    borderColor: "rgba(251,191,36,0.35)",
  },
  modalCloseText: {
    color: "#fbbf24",
    fontSize: 14,
    fontFamily: F.bold,
  },
  miniLine: {
    color: "rgba(255,255,255,0.78)",
    fontSize: 12,
    lineHeight: 18,
    fontFamily: F.regular,
  },
  tierRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8,
  },
  tierSubtitle: {
    color: "rgba(255,255,255,0.52)",
    fontSize: 11,
    lineHeight: 16,
    fontFamily: F.regular,
    marginTop: 10,
  },
  tierTag: {
    borderRadius: 999,
    borderWidth: 1,
    paddingHorizontal: 12,
    paddingVertical: 7,
  },
  tierTagSelected: {
    borderColor: "rgba(251,191,36,0.85)",
    backgroundColor: "rgba(251,191,36,0.22)",
  },
  tierTagFaded: {
    borderColor: "rgba(255,255,255,0.12)",
    backgroundColor: "rgba(255,255,255,0.04)",
    opacity: 0.45,
  },
  tierTagText: {
    fontSize: 11,
    fontFamily: F.bold,
  },
  tierTagTextSelected: {
    color: "#fbbf24",
  },
  tierTagTextFaded: {
    color: "rgba(255,255,255,0.55)",
  },
  tierViewBtn: {
    flexDirection: "row",
    alignItems: "center",
    gap: 2,
    borderRadius: 999,
    borderWidth: 1,
    borderColor: "rgba(251,191,36,0.45)",
    backgroundColor: "rgba(251,191,36,0.1)",
    paddingHorizontal: 10,
    paddingVertical: 5,
  },
  tierViewBtnText: {
    color: "#fbbf24",
    fontSize: 11,
    fontFamily: F.bold,
  },
  dashaTimingLinkRow: {
    marginTop: 12,
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: "rgba(251,191,36,0.4)",
    backgroundColor: "rgba(251,191,36,0.1)",
    paddingHorizontal: 12,
    paddingVertical: 10,
  },
  dashaTimingLinkText: {
    color: "#fff",
    fontSize: 12,
    fontFamily: F.semi,
    flex: 1,
  },
  dashaMetaLine: {
    color: "rgba(255,255,255,0.65)",
    fontSize: 12,
    fontFamily: F.semi,
    marginBottom: 4,
  },
  dashaMdBlock: {
    marginBottom: 12,
    gap: 4,
  },
  dashaRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    paddingVertical: 8,
    paddingHorizontal: 10,
    borderRadius: 10,
    backgroundColor: "rgba(255,255,255,0.03)",
  },
  dashaRowCurrent: {
    borderWidth: 1,
    borderColor: "rgba(251,191,36,0.45)",
    backgroundColor: "rgba(251,191,36,0.08)",
  },
  dashaAdRow: {
    marginLeft: 14,
    paddingVertical: 6,
  },
  dashaMdText: {
    color: "#fff",
    fontSize: 13,
    fontFamily: F.bold,
  },
  dashaAdText: {
    color: "rgba(255,255,255,0.85)",
    fontSize: 12,
    fontFamily: F.semi,
  },
  dashaDateText: {
    color: "rgba(255,255,255,0.45)",
    fontSize: 10,
    fontFamily: F.regular,
  },
  dashaScoreCol: {
    alignItems: "flex-end",
    minWidth: 72,
    gap: 2,
  },
  dashaScoreText: {
    fontSize: 15,
    fontFamily: F.bold,
    textAlign: "right",
  },
  dashaTierText: {
    fontSize: 9,
    fontFamily: F.bold,
    color: "rgba(251,191,36,0.9)",
    textAlign: "right",
    textTransform: "uppercase",
    letterSpacing: 0.4,
  },
  dashaWealthChip: {
    color: "#fbbf24",
    fontSize: 9,
    fontFamily: F.bold,
    textTransform: "uppercase",
    letterSpacing: 0.6,
  },
  tierPill: {
    alignSelf: "flex-start",
    borderRadius: 999,
    borderWidth: 1,
    paddingHorizontal: 14,
    paddingVertical: 8,
  },
  tierPillText: { color: "#fbbf24", fontSize: 13, fontFamily: F.bold },
  cardSubTitle: {
    color: "rgba(255,255,255,0.55)",
    fontSize: 10,
    fontFamily: F.extra,
    letterSpacing: 1.5,
    textTransform: "uppercase",
  },
  disclaimer: {
    color: "rgba(255,255,255,0.45)",
    fontSize: 10,
    lineHeight: 15,
    fontFamily: F.regular,
  },
});
