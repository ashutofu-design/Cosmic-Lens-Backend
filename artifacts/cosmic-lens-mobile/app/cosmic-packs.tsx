/**
 * Cosmic Packs — conversion-focused V3 flagship + V1 packs.
 * Payment / booking starts here (Ask tab only redirects here for packs).
 */
import { Feather } from "@expo/vector-icons";
import AsyncStorage from "@react-native-async-storage/async-storage";
import * as Haptics from "expo-haptics";
import { LinearGradient } from "expo-linear-gradient";
import { router, Stack, useLocalSearchParams } from "expo-router";
import React, { useEffect, useRef, useState } from "react";
import {
  ActivityIndicator,
  Alert,
  I18nManager,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";
import Animated, {
  Easing,
  interpolate,
  useAnimatedStyle,
  useSharedValue,
  withDelay,
  withRepeat,
  withSequence,
  withTiming,
} from "react-native-reanimated";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { CosmicBg } from "@/components/CosmicBg";
import { FadeInView, staggerDelay } from "@/components/motion/FadeInView";
import { ScalePressable } from "@/components/motion/ScalePressable";
import { useC } from "@/context/ThemeContext";
import { useUser } from "@/context/UserContext";
import { ASK_V1_PACKS, type AskV1PackId } from "@/lib/askV1PackBilling";
import { startAskV1PackPayment } from "@/lib/askV1PackCheckoutFlow";
import { startAskV3PackPayment } from "@/lib/askV3CheckoutFlow";
import {
  ASK_REPLY_LANG_STORAGE_KEY,
  loadAskReplyLang,
} from "@/lib/askReplyLang";

const F = {
  medium: "Nunito_500Medium",
  semibold: "Nunito_600SemiBold",
  bold: "Nunito_700Bold",
} as const;

const V3_PACKS = [
  {
    id: "15",
    label: "15 min",
    price: 399,
    feel: "First live try — one clear answer",
    badge: null as null | string,
  },
  {
    id: "30",
    label: "30 min",
    price: 699,
    feel: "Full consultation — what most people book",
    badge: "MOST POPULAR",
    highlight: true,
  },
  {
    id: "45",
    label: "45 min",
    price: 999,
    feel: "Career · love · timing — deep dive",
    badge: null as null | string,
  },
  {
    id: "60",
    label: "60 min",
    price: 1299,
    feel: "Full hour with your chart · best value",
    badge: "BEST VALUE",
  },
];

function LivePulseDot() {
  const pulse = useSharedValue(0);
  useEffect(() => {
    pulse.value = withRepeat(
      withTiming(1, { duration: 1100, easing: Easing.inOut(Easing.ease) }),
      -1,
      true,
    );
  }, [pulse]);
  const glow = useAnimatedStyle(() => ({
    opacity: interpolate(pulse.value, [0, 1], [0.35, 1]),
    transform: [{ scale: interpolate(pulse.value, [0, 1], [0.85, 1.25]) }],
  }));
  return (
    <View style={{ width: 10, height: 10, alignItems: "center", justifyContent: "center" }}>
      <Animated.View
        style={[
          {
            position: "absolute",
            width: 10,
            height: 10,
            borderRadius: 5,
            backgroundColor: "#4ade80",
          },
          glow,
        ]}
      />
      <View
        style={{
          width: 7,
          height: 7,
          borderRadius: 4,
          backgroundColor: "#22c55e",
        }}
      />
    </View>
  );
}

function HeroShimmer() {
  const x = useSharedValue(-1);
  useEffect(() => {
    x.value = withRepeat(
      withTiming(1, { duration: 2400, easing: Easing.inOut(Easing.ease) }),
      -1,
      false,
    );
  }, [x]);
  const style = useAnimatedStyle(() => ({
    transform: [{ translateX: interpolate(x.value, [-1, 1], [-120, 280]) }],
    opacity: 0.18,
  }));
  return (
    <Animated.View
      pointerEvents="none"
      style={[
        {
          position: "absolute",
          top: 0,
          bottom: 0,
          width: 80,
          backgroundColor: "#fff",
        },
        style,
      ]}
    />
  );
}

function CtaPulse({ children }: { children: React.ReactNode }) {
  const s = useSharedValue(1);
  useEffect(() => {
    s.value = withRepeat(
      withSequence(
        withTiming(1.02, { duration: 900 }),
        withTiming(1, { duration: 900 }),
      ),
      -1,
      false,
    );
  }, [s]);
  const style = useAnimatedStyle(() => ({ transform: [{ scale: s.value }] }));
  return <Animated.View style={style}>{children}</Animated.View>;
}

function StaggerIn({
  index,
  children,
}: {
  index: number;
  children: React.ReactNode;
}) {
  const y = useSharedValue(16);
  const o = useSharedValue(0);
  useEffect(() => {
    y.value = withDelay(
      80 + index * 70,
      withTiming(0, { duration: 420, easing: Easing.out(Easing.cubic) }),
    );
    o.value = withDelay(80 + index * 70, withTiming(1, { duration: 420 }));
  }, [index, o, y]);
  const style = useAnimatedStyle(() => ({
    opacity: o.value,
    transform: [{ translateY: y.value }],
  }));
  return <Animated.View style={style}>{children}</Animated.View>;
}

export default function CosmicPacksScreen() {
  const C = useC();
  const insets = useSafeAreaInsets();
  const { user } = useUser();
  const params = useLocalSearchParams<{ focus?: string | string[]; pack?: string | string[] }>();
  const focusRaw = Array.isArray(params.focus) ? params.focus[0] : params.focus;
  const focus = focusRaw === "v1" ? "v1" : focusRaw === "v3" ? "v3" : null;
  const packRaw = Array.isArray(params.pack) ? params.pack[0] : params.pack;

  const [v3Pick, setV3Pick] = useState("30");
  const [v1Pick, setV1Pick] = useState<AskV1PackId>("popular");
  const [v3Busy, setV3Busy] = useState(false);
  const [v1Busy, setV1Busy] = useState(false);
  const scrollRef = useRef<ScrollView>(null);
  const v1Y = useRef(0);

  useEffect(() => {
    const id = String(packRaw || "").trim();
    if (id && V3_PACKS.some((p) => p.id === id)) {
      setV3Pick(id);
    }
  }, [packRaw]);

  useEffect(() => {
    if (focus !== "v1") return;
    const t = setTimeout(() => {
      scrollRef.current?.scrollTo({ y: Math.max(0, v1Y.current - 12), animated: true });
    }, 350);
    return () => clearTimeout(t);
  }, [focus]);

  const buyV1 = async () => {
    if (v1Busy) return;
    setV1Busy(true);
    try {
      const result = await startAskV1PackPayment(user, v1Pick);
      if (result === "paid_bypass") {
        router.replace("/(tabs)/ask" as any);
      }
      // checkout → payment-webview handles returnTo=ask
    } finally {
      setV1Busy(false);
    }
  };

  const bookV3 = async (packIdOverride?: string) => {
    if (v3Busy) return;
    if (!user?.id || !user?.api_key) {
      Alert.alert("Login required", "Please sign in to book a V3 live session.");
      return;
    }
    const pick = packIdOverride || v3Pick;
    const pack = V3_PACKS.find((p) => p.id === pick) ?? V3_PACKS[1];
    setV3Busy(true);
    try {
      let preferred = "hn";
      try {
        const raw = await AsyncStorage.getItem(ASK_REPLY_LANG_STORAGE_KEY);
        preferred = loadAskReplyLang(raw);
      } catch { /* default hn */ }

      // Pay first — session is created only after payment succeeds.
      await startAskV3PackPayment(user, pack.id, preferred);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Could not start payment";
      Alert.alert("V3 payment", msg);
    } finally {
      setV3Busy(false);
    }
  };

  return (
    <CosmicBg>
      <Stack.Screen options={{ headerShown: false }} />
      <View style={[s.header, { paddingTop: insets.top + 6, borderBottomColor: C.border }]}>
        <Pressable onPress={() => router.back()} hitSlop={10} style={s.back}>
          <Feather
            name={I18nManager.isRTL ? "arrow-right" : "arrow-left"}
            size={20}
            color={C.textMuted}
          />
        </Pressable>
        <View style={{ flex: 1 }}>
          <Text style={[s.title, { color: C.text }]}>Cosmic Packs</Text>
          <Text style={[s.sub, { color: C.textMuted }]}>
            {focus === "v1"
              ? "Buy V1 questions · pay here"
              : focus === "v3"
                ? "Book V3 live · pay / request here"
                : "V3 live · V1 Q&A packs"}
          </Text>
        </View>
      </View>

      <ScrollView
        ref={scrollRef}
        contentContainerStyle={{ padding: 10, paddingBottom: insets.bottom + 20, gap: 8 }}
        showsVerticalScrollIndicator={false}
      >
        {/* ── V3 FLAGSHIP HERO (compact) ── */}
        <FadeInView delay={staggerDelay(0)}>
          <View style={s.heroWrap}>
            <LinearGradient
              colors={
                C.isDark
                  ? ["#92400e", "#78350f", "#1c1917"]
                  : ["#b45309", "#d97706", "#f59e0b"]
              }
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 1 }}
              style={s.hero}
            >
              <HeroShimmer />
              <View style={s.heroTopRow}>
                <View style={s.heroRibbon}>
                  <Text style={s.heroRibbonTxt}>MOST POWERFUL</Text>
                </View>
                <View style={s.liveChip}>
                  <LivePulseDot />
                  <Text style={s.liveChipTxt}>LIVE</Text>
                </View>
              </View>

              <Text style={s.heroTitle}>Cosmic Intelligence V3</Text>
              <Text style={s.heroHook}>Deep Astrology session</Text>
            </LinearGradient>
          </View>
        </FadeInView>

        {/* V3 packs — compact 2-col grid */}
        <FadeInView delay={staggerDelay(1)}>
          <View style={s.sectionHead}>
            <Feather name="zap" size={15} color="#f59e0b" />
            <Text style={[s.sectionTitle, { color: C.text }]}>Book V3 live</Text>
            <View style={[s.powerPill, { borderColor: "#f59e0b", backgroundColor: "#f59e0b18" }]}>
              <Text style={[s.powerPillTxt, { color: "#f59e0b" }]}>FLAGSHIP</Text>
            </View>
          </View>

          <View style={s.packGrid}>
            {V3_PACKS.map((p, i) => {
              const active = v3Pick === p.id;
              const accent = "#f59e0b";
              return (
                <View key={p.id} style={s.gridCell}>
                  <StaggerIn index={i}>
                    <ScalePressable
                      haptic="light"
                      onPress={() => {
                        setV3Pick(p.id);
                        Haptics.selectionAsync().catch(() => {});
                      }}
                    >
                      <View
                        style={[
                          s.gridCard,
                          {
                            backgroundColor: active
                              ? C.isDark
                                ? "rgba(245,158,11,0.16)"
                                : "rgba(245,158,11,0.1)"
                              : C.bgCard,
                            borderColor: active || p.highlight ? accent : C.border,
                            borderWidth: active || p.highlight ? 1.5 : 1,
                          },
                        ]}
                      >
                        {p.badge ? (
                          <Text style={[s.gridBadge, { color: accent }]} numberOfLines={1}>
                            {p.badge}
                          </Text>
                        ) : (
                          <View style={{ height: 12 }} />
                        )}
                        <Text style={[s.gridLabel, { color: C.text }]}>{p.label}</Text>
                        <Text style={[s.gridPrice, { color: accent }]}>
                          ₹{p.price.toLocaleString("en-IN")}
                        </Text>
                        {active ? (
                          <View style={[s.gridCheck, { backgroundColor: accent }]}>
                            <Feather name="check" size={10} color="#fff" />
                          </View>
                        ) : null}
                      </View>
                    </ScalePressable>
                  </StaggerIn>
                </View>
              );
            })}
          </View>

          <CtaPulse>
            <ScalePressable
              haptic="medium"
              onPress={() => {
                if (v3Busy) return;
                Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium).catch(() => {});
                void bookV3();
              }}
              style={{ marginTop: 8 }}
            >
              <LinearGradient
                colors={["#b45309", "#f59e0b"]}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 0 }}
                style={s.ctaGrad}
              >
                {v3Busy ? (
                  <ActivityIndicator color="#fff" />
                ) : (
                  <>
                    <Feather name="zap" size={15} color="#fff" />
                    <Text style={s.ctaTxt} numberOfLines={1} adjustsFontSizeToFit>
                      Pay & Reserve V3 ·{" "}
                      {V3_PACKS.find((p) => p.id === v3Pick)?.label ?? "30 min"} · ₹
                      {(
                        V3_PACKS.find((p) => p.id === v3Pick)?.price ?? 699
                      ).toLocaleString("en-IN")}
                    </Text>
                  </>
                )}
              </LinearGradient>
            </ScalePressable>
          </CtaPulse>
        </FadeInView>

        {/* V1 — compact */}
        <FadeInView delay={staggerDelay(2)}>
          <View
            style={s.v1Wrap}
            onLayout={(e) => {
              v1Y.current = e.nativeEvent.layout.y;
            }}
          >
            <LinearGradient
              colors={
                C.isDark
                  ? ["#1e3a8a", "#172554", "#0b1120"]
                  : ["#2563eb", "#3b82f6", "#06b6d4"]
              }
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 1 }}
              style={s.v1Hero}
            >
              <HeroShimmer />
              <View style={s.heroTopRow}>
                <View style={s.v1Ribbon}>
                  <Feather name="message-circle" size={11} color="#1e3a8a" />
                  <Text style={s.v1RibbonTxt}>SMART Q&A</Text>
                </View>
                <View style={s.v1FromChip}>
                  <Text style={s.v1FromTxt}>From ₹49</Text>
                </View>
              </View>
              <Text style={s.heroTitle}>Cosmic Intelligence V1</Text>
              <Text style={s.v1Hook} numberOfLines={1}>
                Instant answers from your kundli · anytime
              </Text>
            </LinearGradient>

            <View
              style={[
                s.v1Body,
                { backgroundColor: C.bgCard, borderColor: C.border },
              ]}
            >
              <View style={{ gap: 5 }}>
                {ASK_V1_PACKS.map((p, i) => {
                  const active = v1Pick === p.id;
                  const isPop = p.badge === "popular";
                  const isBest = p.badge === "best";
                  const accent = "#3b82f6";
                  return (
                    <StaggerIn key={p.id} index={i}>
                      <ScalePressable
                        haptic="light"
                        onPress={() => {
                          setV1Pick(p.id);
                          Haptics.selectionAsync().catch(() => {});
                        }}
                      >
                        <View
                          style={[
                            s.row,
                            {
                              backgroundColor: active
                                ? C.isDark
                                  ? "rgba(59,130,246,0.16)"
                                  : "rgba(59,130,246,0.08)"
                                : C.isDark
                                  ? "#0f1118"
                                  : "#f8fafc",
                              borderColor: active || isPop ? accent : C.border,
                              borderWidth: active || isPop ? 1.5 : 1,
                            },
                          ]}
                        >
                          <View
                            style={[
                              s.radio,
                              {
                                borderColor: active ? accent : C.border,
                                backgroundColor: active ? accent : "transparent",
                              },
                            ]}
                          >
                            {active ? <Feather name="check" size={10} color="#fff" /> : null}
                          </View>
                          <View
                            style={[
                              s.v1QBox,
                              {
                                backgroundColor: C.isDark
                                  ? "rgba(59,130,246,0.18)"
                                  : "rgba(59,130,246,0.1)",
                              },
                            ]}
                          >
                            <Text style={[s.v1QNum, { color: "#60a5fa" }]}>{p.questions}</Text>
                            <Text style={[s.v1QLbl, { color: C.textMuted }]}>Q</Text>
                          </View>
                          <View style={{ flex: 1, gap: 1 }}>
                            <View style={{ flexDirection: "row", alignItems: "center", gap: 6, flexWrap: "wrap" }}>
                              <Text style={[s.rowTitle, { color: C.text }]}>{p.label}</Text>
                              {isPop ? (
                                <View style={[s.badge, { borderColor: accent, backgroundColor: `${accent}22` }]}>
                                  <Text style={[s.badgeTxt, { color: "#60a5fa" }]}>POPULAR</Text>
                                </View>
                              ) : null}
                              {isBest ? (
                                <View style={[s.badge, { borderColor: "#22c55e", backgroundColor: "#22c55e22" }]}>
                                  <Text style={[s.badgeTxt, { color: "#4ade80" }]}>BEST</Text>
                                </View>
                              ) : null}
                            </View>
                            <Text style={[s.rowSub, { color: C.textMuted }]} numberOfLines={1}>
                              {p.days} days · {p.feel}
                            </Text>
                          </View>
                          <Text style={[s.price, { color: "#60a5fa" }]}>
                            ₹{p.price_inr.toLocaleString("en-IN")}
                          </Text>
                        </View>
                      </ScalePressable>
                    </StaggerIn>
                  );
                })}
              </View>

              <ScalePressable
                haptic="light"
                onPress={() => {
                  if (v1Busy) return;
                  Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light).catch(() => {});
                  void buyV1();
                }}
                style={{ marginTop: 8 }}
              >
                <LinearGradient
                  colors={["#2563eb", "#06b6d4"]}
                  start={{ x: 0, y: 0 }}
                  end={{ x: 1, y: 0 }}
                  style={s.ctaGrad}
                >
                  {v1Busy ? (
                    <ActivityIndicator color="#fff" />
                  ) : (
                    <>
                      <Feather name="credit-card" size={15} color="#fff" />
                      <Text style={s.ctaTxt}>
                        Buy V1 · {ASK_V1_PACKS.find((p) => p.id === v1Pick)?.label ?? "Popular"} · ₹
                        {(
                          ASK_V1_PACKS.find((p) => p.id === v1Pick)?.price_inr ?? 99
                        ).toLocaleString("en-IN")}
                      </Text>
                    </>
                  )}
                </LinearGradient>
              </ScalePressable>
            </View>
          </View>
        </FadeInView>

        <Text style={[s.footnote, { color: C.textMuted }]}>
          3 free V1 questions on signup · V3 = live personal time
        </Text>
      </ScrollView>
    </CosmicBg>
  );
}

const s = StyleSheet.create({
  header: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    paddingHorizontal: 10,
    paddingBottom: 8,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  back: { padding: 4 },
  title: { fontSize: 17, fontFamily: F.bold },
  sub: { fontSize: 11, fontFamily: F.medium, marginTop: 1 },
  heroWrap: { borderRadius: 14, overflow: "hidden" },
  hero: { paddingHorizontal: 12, paddingVertical: 10, gap: 4, overflow: "hidden" },
  heroTopRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    gap: 6,
    flexWrap: "wrap",
  },
  heroRibbon: {
    flexDirection: "row",
    alignItems: "center",
    gap: 4,
    backgroundColor: "#fde68a",
    borderRadius: 999,
    paddingHorizontal: 8,
    paddingVertical: 3,
  },
  heroRibbonTxt: {
    color: "#78350f",
    fontSize: 9,
    fontFamily: F.bold,
    letterSpacing: 0.7,
  },
  liveChip: {
    flexDirection: "row",
    alignItems: "center",
    gap: 5,
    backgroundColor: "rgba(0,0,0,0.28)",
    borderRadius: 999,
    paddingHorizontal: 8,
    paddingVertical: 3,
  },
  liveChipTxt: {
    color: "#bbf7d0",
    fontSize: 9,
    fontFamily: F.bold,
    letterSpacing: 0.5,
  },
  heroTitle: { color: "#fff", fontSize: 17, fontFamily: F.bold, marginTop: 1 },
  heroHook: {
    color: "#fef3c7",
    fontSize: 12,
    lineHeight: 16,
    fontFamily: F.semibold,
  },
  heroBody: {
    color: "rgba(255,255,255,0.9)",
    fontSize: 12,
    lineHeight: 16,
    fontFamily: F.medium,
  },
  trustRow: { flexDirection: "row", flexWrap: "wrap", gap: 5, marginTop: 2 },
  trustPill: {
    flexDirection: "row",
    alignItems: "center",
    gap: 3,
    backgroundColor: "rgba(0,0,0,0.22)",
    borderRadius: 999,
    paddingHorizontal: 7,
    paddingVertical: 3,
  },
  trustPillTxt: { color: "#fff", fontSize: 10, fontFamily: F.semibold },
  proofStrip: {
    flexDirection: "row",
    alignItems: "flex-start",
    gap: 8,
    borderWidth: 1,
    borderRadius: 12,
    paddingHorizontal: 10,
    paddingVertical: 7,
  },
  proofTxt: { flex: 1, fontSize: 12, lineHeight: 16, fontFamily: F.medium },
  sectionHead: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    flexWrap: "wrap",
    marginBottom: 6,
  },
  sectionTitle: { fontSize: 14, fontFamily: F.bold },
  sectionHint: { fontSize: 11, fontFamily: F.medium, marginTop: 2, lineHeight: 15 },
  powerPill: {
    borderWidth: 1,
    borderRadius: 999,
    paddingHorizontal: 7,
    paddingVertical: 1,
  },
  powerPillTxt: { fontSize: 9, fontFamily: F.bold, letterSpacing: 0.5 },
  packGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    justifyContent: "space-between",
    rowGap: 6,
  },
  gridCell: {
    width: "48.5%",
  },
  gridCard: {
    borderRadius: 12,
    paddingHorizontal: 10,
    paddingVertical: 10,
    alignItems: "flex-start",
    gap: 2,
    position: "relative",
    minHeight: 72,
  },
  gridBadge: { fontSize: 8, fontFamily: F.bold, letterSpacing: 0.3 },
  gridLabel: { fontSize: 14, fontFamily: F.bold },
  gridPrice: { fontSize: 15, fontFamily: F.bold, marginTop: 2 },
  gridCheck: {
    position: "absolute",
    top: 8,
    right: 8,
    width: 16,
    height: 16,
    borderRadius: 8,
    alignItems: "center",
    justifyContent: "center",
  },
  row: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    borderRadius: 12,
    paddingHorizontal: 10,
    paddingVertical: 7,
  },
  radio: {
    width: 18,
    height: 18,
    borderRadius: 9,
    borderWidth: 1.5,
    alignItems: "center",
    justifyContent: "center",
  },
  rowTitle: { fontSize: 13, fontFamily: F.bold },
  rowSub: { fontSize: 11, fontFamily: F.medium, lineHeight: 14 },
  price: { fontSize: 14, fontFamily: F.bold },
  badge: {
    borderWidth: 1,
    borderRadius: 999,
    paddingHorizontal: 6,
    paddingVertical: 1,
  },
  badgeTxt: { fontSize: 8, fontFamily: F.bold, letterSpacing: 0.3 },
  ctaGrad: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 6,
    borderRadius: 12,
    paddingVertical: 10,
    paddingHorizontal: 10,
  },
  ctaTxt: { color: "#fff", fontSize: 13.5, fontFamily: F.bold, flexShrink: 1, textAlign: "center" },
  urgency: {
    textAlign: "center",
    fontSize: 11,
    fontFamily: F.medium,
    marginTop: 5,
    lineHeight: 14,
  },
  v1Wrap: { borderRadius: 14, overflow: "hidden" },
  v1Hero: { paddingHorizontal: 12, paddingVertical: 10, gap: 3, overflow: "hidden" },
  v1Ribbon: {
    flexDirection: "row",
    alignItems: "center",
    gap: 4,
    backgroundColor: "#bfdbfe",
    borderRadius: 999,
    paddingHorizontal: 8,
    paddingVertical: 3,
  },
  v1RibbonTxt: {
    color: "#1e3a8a",
    fontSize: 9,
    fontFamily: F.bold,
    letterSpacing: 0.7,
  },
  v1FromChip: {
    backgroundColor: "rgba(0,0,0,0.25)",
    borderRadius: 999,
    paddingHorizontal: 8,
    paddingVertical: 3,
  },
  v1FromTxt: { color: "#dbeafe", fontSize: 10, fontFamily: F.bold, letterSpacing: 0.3 },
  v1Hook: {
    color: "#dbeafe",
    fontSize: 12,
    lineHeight: 16,
    fontFamily: F.semibold,
  },
  v1Body: {
    borderWidth: 1,
    borderTopWidth: 0,
    borderBottomLeftRadius: 14,
    borderBottomRightRadius: 14,
    padding: 8,
  },
  v1QBox: {
    width: 34,
    height: 34,
    borderRadius: 9,
    alignItems: "center",
    justifyContent: "center",
  },
  v1QNum: { fontSize: 14, fontFamily: F.bold, lineHeight: 16 },
  v1QLbl: { fontSize: 8, fontFamily: F.bold, letterSpacing: 0.4 },
  v1Card: {
    borderWidth: 1,
    borderRadius: 14,
    padding: 12,
  },
  rowSoft: {
    flexDirection: "row",
    alignItems: "center",
    borderWidth: StyleSheet.hairlineWidth,
    borderRadius: 10,
    paddingHorizontal: 10,
    paddingVertical: 8,
  },
  ctaSoft: {
    marginTop: 8,
    alignItems: "center",
    borderWidth: 1,
    borderRadius: 10,
    paddingVertical: 9,
  },
  footnote: {
    fontSize: 11,
    lineHeight: 15,
    fontFamily: F.medium,
    textAlign: "center",
  },
});
