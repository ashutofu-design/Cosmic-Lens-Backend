import { Feather } from "@expo/vector-icons";
import { BlurView } from "expo-blur";
import * as Haptics from "expo-haptics";
import { LinearGradient } from "expo-linear-gradient";
import { router } from "expo-router";
import React, { useEffect, useMemo, useRef } from "react";
import {
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
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { CosmicBg } from "@/components/CosmicBg";
import { FadeInView, staggerDelay } from "@/components/motion/FadeInView";
import { useUser } from "@/context/UserContext";
import { useT } from "@/hooks/useT";
import {
  GEMSTONE_CATALOG,
  pickLocalized,
  recommendedGemstoneKey,
  type GemstoneCatalogEntry,
} from "@/lib/gemstoneCatalog";
import {
  formatInr,
  GEMSTONE_PRODUCT_LINES,
  lowestSelfPriceForProduct,
} from "@/lib/gemstonePricing";
import { gemstoneWhatsAppMessage } from "@/lib/gemstoneProductContent";
import { openFounderWhatsApp } from "@/lib/founderWhatsApp";
import { DAY, GEMSTONE, PLANET, pick } from "@/lib/i18nVedic";

const F = {
  regular: "Nunito_400Regular",
  semi: "Nunito_600SemiBold",
  bold: "Nunito_700Bold",
  extra: "Nunito_800ExtraBold",
} as const;

const GEM_ACCENT = "#c084fc";
const ACCENT = "#fbbf24";

function PremiumOrb({ color }: { color: string }) {
  const pulse = useRef(new Animated.Value(0)).current;
  useEffect(() => {
    const loop = Animated.loop(
      Animated.sequence([
        Animated.timing(pulse, { toValue: 1, duration: 2400, easing: Easing.inOut(Easing.ease), useNativeDriver: true }),
        Animated.timing(pulse, { toValue: 0, duration: 2400, easing: Easing.inOut(Easing.ease), useNativeDriver: true }),
      ]),
    );
    loop.start();
    return () => loop.stop();
  }, [pulse]);
  const scale = pulse.interpolate({ inputRange: [0, 1], outputRange: [1, 1.14] });
  const opacity = pulse.interpolate({ inputRange: [0, 1], outputRange: [0.2, 0.48] });
  return (
    <Animated.View
      pointerEvents="none"
      style={[ui.orb, { backgroundColor: color, transform: [{ scale }], opacity }]}
    />
  );
}

function GemOrb({ entry }: { entry: GemstoneCatalogEntry }) {
  const shimmer = useRef(new Animated.Value(0)).current;
  useEffect(() => {
    const loop = Animated.loop(
      Animated.sequence([
        Animated.timing(shimmer, { toValue: 1, duration: 2200, easing: Easing.inOut(Easing.ease), useNativeDriver: true }),
        Animated.timing(shimmer, { toValue: 0, duration: 2200, easing: Easing.inOut(Easing.ease), useNativeDriver: true }),
      ]),
    );
    loop.start();
    return () => loop.stop();
  }, [shimmer]);
  const glow = shimmer.interpolate({ inputRange: [0, 1], outputRange: [0.35, 0.85] });
  return (
    <View style={s.gemOrbWrap}>
      <Animated.View style={[s.gemOrbGlow, { backgroundColor: entry.accent, opacity: glow }]} />
      <LinearGradient
        colors={entry.gradient}
        start={{ x: 0.2, y: 0 }}
        end={{ x: 0.9, y: 1 }}
        style={s.gemOrb}
      >
        <Text style={s.gemOrbEmoji}>💎</Text>
      </LinearGradient>
    </View>
  );
}

function GemCard({
  entry,
  vlang,
  highlight,
  delay,
}: {
  entry: GemstoneCatalogEntry;
  vlang: "en" | "hn" | "hi";
  highlight?: boolean;
  delay: number;
}) {
  const gemName = pick(vlang, GEMSTONE[entry.gemstoneKey]);
  const planetName = pick(vlang, PLANET[entry.planetKey]);
  const dayName = pick(vlang, DAY[entry.day]);

  return (
    <FadeInView delay={delay}>
      <View style={[s.card, { borderColor: `${entry.accent}${highlight ? "88" : "44"}` }]}>
        <LinearGradient
          colors={[`${entry.accent}18`, "rgba(255,255,255,0.03)", "transparent"]}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 1 }}
          style={StyleSheet.absoluteFill}
          pointerEvents="none"
        />
        {highlight ? (
          <View style={[s.recommendedRibbon, { backgroundColor: `${entry.accent}22`, borderColor: `${entry.accent}55` }]}>
            <Feather name="star" size={10} color={entry.accent} />
            <Text style={[s.recommendedRibbonText, { color: entry.accent }]}>For You</Text>
          </View>
        ) : null}
        <View style={s.cardRow}>
          <GemOrb entry={entry} />
          <View style={{ flex: 1, gap: 4 }}>
            <Text style={s.gemTitle}>{gemName}</Text>
            {vlang !== "en" ? (
              <Text style={s.gemSubEn}>{GEMSTONE[entry.gemstoneKey].en}</Text>
            ) : null}
            <View style={s.planetRow}>
              <Text style={s.planetEmoji}>{entry.planetEmoji}</Text>
              <Text style={[s.planetText, { color: entry.accent }]}>{planetName}</Text>
              <Text style={s.dayDot}>·</Text>
              <Text style={s.dayText}>{dayName}</Text>
            </View>
          </View>
        </View>
        <Text style={s.benefitText}>{pickLocalized(vlang, entry.benefit)}</Text>
        <View style={s.metaRow}>
          <MetaChip icon="hand" label={pickLocalized(vlang, entry.finger)} accent={entry.accent} />
          <MetaChip icon="hexagon" label={pickLocalized(vlang, entry.metal)} accent={entry.accent} />
          <MetaChip icon="maximize-2" label={entry.weight} accent={entry.accent} />
        </View>
      </View>
    </FadeInView>
  );
}

function MetaChip({ icon, label, accent }: { icon: React.ComponentProps<typeof Feather>["name"]; label: string; accent: string }) {
  return (
    <View style={[s.metaChip, { borderColor: `${accent}33`, backgroundColor: `${accent}10` }]}>
      <Feather name={icon} size={10} color={accent} />
      <Text style={s.metaChipText} numberOfLines={1}>{label}</Text>
    </View>
  );
}

export default function GemstonesScreen() {
  const insets = useSafeAreaInsets();
  const t = useT();
  const { kundli } = useUser();
  const vlang = t.vlang;

  const recommendedKey = useMemo(
    () => recommendedGemstoneKey(kundli?.rashi, kundli?.planets),
    [kundli],
  );
  const recommended = recommendedKey
    ? GEMSTONE_CATALOG.find(g => g.id === recommendedKey)
    : null;
  const others = GEMSTONE_CATALOG.filter(g => g.id !== recommendedKey);
  const headerTopPad = insets.top + 8;

  return (
    <CosmicBg>
      <LinearGradient
        colors={["rgba(0,0,0,0.45)", "transparent", "rgba(0,0,0,0.3)"]}
        locations={[0, 0.4, 1]}
        style={StyleSheet.absoluteFill}
        pointerEvents="none"
      />
      <PremiumOrb color={GEM_ACCENT} />

      <View style={[s.topBar, { paddingTop: headerTopPad, borderBottomColor: `${GEM_ACCENT}22` }]}>
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
          <View style={{ flex: 1, alignItems: "center" }}>
            <Text style={ui.headerBadge}>{t.ku_gemstonesBadge}</Text>
            <Text style={s.topTitle}>{t.ku_gemstones}</Text>
          </View>
          <View style={{ width: 40 }} />
        </View>
      </View>

      <ScrollView
        contentContainerStyle={{
          paddingTop: headerTopPad + 58,
          paddingBottom: insets.bottom + 80,
          paddingHorizontal: 18,
          gap: 14,
        }}
        showsVerticalScrollIndicator={false}
      >
        <FadeInView delay={staggerDelay(0)}>
          <View style={[s.introCard, { borderColor: `${GEM_ACCENT}44` }]}>
            <LinearGradient
              colors={[`${GEM_ACCENT}20`, "rgba(255,255,255,0.02)", "transparent"]}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 1 }}
              style={StyleSheet.absoluteFill}
              pointerEvents="none"
            />
            <Text style={s.introEmoji}>💎</Text>
            <Text style={s.introTitle}>{t.ku_gemstonesHero}</Text>
            <Text style={s.introSub}>{t.ku_gemstonesSub}</Text>
          </View>
        </FadeInView>

        <FadeInView delay={staggerDelay(1)}>
          <Text style={s.sectionLabel}>{t.gs_shopTitle}</Text>
          {GEMSTONE_PRODUCT_LINES.map((line, idx) => (
            <Pressable
              key={line.id}
              onPress={() => {
                Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
                void openFounderWhatsApp(gemstoneWhatsAppMessage(line.label));
              }}
              style={({ pressed }) => ({ opacity: pressed ? 0.9 : 1, marginBottom: idx < GEMSTONE_PRODUCT_LINES.length - 1 ? 10 : 0 })}
            >
              <View style={[s.shopCard, { borderColor: `${line.accent}55` }]}>
                <LinearGradient
                  colors={[`${line.accent}28`, "transparent"]}
                  style={StyleSheet.absoluteFill}
                  pointerEvents="none"
                />
                <View style={s.shopRow}>
                  <View style={{ flex: 1, gap: 4 }}>
                    <Text style={s.shopTitle}>{line.label}</Text>
                    <Text style={s.shopSub}>
                      {line.id === "emerald" ? "5 Ratti · Certified Zambia" : t.gs_shopSizes}
                    </Text>
                    <View style={s.shopPriceRow}>
                      <Text style={s.shopMrp}>{t.gs_shopFrom}</Text>
                      <Text style={[s.shopPrice, { color: line.accent }]}>
                        {formatInr(lowestSelfPriceForProduct(line.id))}
                      </Text>
                    </View>
                    <Text style={s.shopOffer}>
                      {line.id === "emerald"
                        ? `5 ${t.gs_ratti} · ${t.gs_selfBuy} & ${t.gs_referralBuy}`
                        : `5–10 ${t.gs_ratti} · ${t.gs_selfBuy} & ${t.gs_referralBuy}`}
                    </Text>
                  </View>
                  <View style={[s.shopCta, { borderColor: `${line.accent}66`, backgroundColor: `${line.accent}2e` }]}>
                    <Text style={s.shopCtaText}>{t.gs_whatsappCta}</Text>
                    <Feather name="message-circle" size={14} color="#fff" />
                  </View>
                </View>
              </View>
            </Pressable>
          ))}
        </FadeInView>

        {recommended ? (
          <GemCard
            entry={recommended}
            vlang={vlang}
            highlight
            delay={staggerDelay(2)}
          />
        ) : null}

        <FadeInView delay={staggerDelay(recommended ? 3 : 2)}>
          <Text style={s.sectionLabel}>{t.ku_gemstonesAll}</Text>
        </FadeInView>

        {others.map((entry, i) => (
          <GemCard
            key={entry.id}
            entry={entry}
            vlang={vlang}
            delay={staggerDelay((recommended ? 4 : 3) + i)}
          />
        ))}

        <FadeInView delay={staggerDelay(12)}>
          <Text style={s.disclaimer}>{t.remGemstoneTip}</Text>
        </FadeInView>
      </ScrollView>
    </CosmicBg>
  );
}

const s = StyleSheet.create({
  topBar: {
    position: "absolute",
    top: 0,
    left: 0,
    right: 0,
    zIndex: 20,
    paddingHorizontal: 14,
    paddingBottom: 12,
    borderBottomWidth: 1,
    overflow: "hidden",
  },
  topBarBg: { backgroundColor: "rgba(14,10,28,0.94)" },
  topBarRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
  },
  backBtn: { padding: 4 },
  backCircle: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: "rgba(255,255,255,0.08)",
    borderWidth: 1,
    borderColor: "rgba(255,255,255,0.14)",
    alignItems: "center",
    justifyContent: "center",
  },
  topTitle: { color: "#fff", fontSize: 16, fontFamily: F.bold },

  introCard: {
    borderRadius: 20,
    borderWidth: 1,
    backgroundColor: "rgba(12,10,24,0.82)",
    padding: 18,
    alignItems: "center",
    gap: 8,
    overflow: "hidden",
  },
  introEmoji: { fontSize: 32 },
  introTitle: {
    color: "#fff",
    fontSize: 15,
    fontFamily: F.bold,
    textAlign: "center",
  },
  introSub: {
    color: "rgba(255,255,255,0.62)",
    fontSize: 12,
    fontFamily: F.semi,
    textAlign: "center",
    lineHeight: 18,
  },

  sectionLabel: {
    color: "rgba(255,255,255,0.45)",
    fontSize: 10,
    fontFamily: F.extra,
    letterSpacing: 2,
    textTransform: "uppercase",
    marginTop: 4,
    marginBottom: 2,
  },

  shopCard: {
    borderRadius: 18,
    borderWidth: 1,
    backgroundColor: "rgba(12,10,20,0.82)",
    padding: 16,
    overflow: "hidden",
    marginBottom: 4,
  },
  shopRow: { flexDirection: "row", alignItems: "center", gap: 12 },
  shopTitle: { color: "#fff", fontSize: 15, fontFamily: F.bold },
  shopSub: { color: "rgba(255,255,255,0.55)", fontSize: 11, fontFamily: F.semi },
  shopPriceRow: { flexDirection: "row", alignItems: "baseline", gap: 8, marginTop: 6 },
  shopMrp: {
    color: "rgba(255,255,255,0.4)", fontSize: 12, fontFamily: F.semi, textDecorationLine: "line-through",
  },
  shopPrice: { color: ACCENT, fontSize: 18, fontFamily: F.extra },
  shopOffer: { color: "rgba(255,255,255,0.5)", fontSize: 10, fontFamily: F.semi, marginTop: 4 },
  shopCta: {
    flexDirection: "row", alignItems: "center", gap: 4,
    backgroundColor: "rgba(251,191,36,0.18)", borderWidth: 1, borderColor: "rgba(251,191,36,0.4)",
    paddingHorizontal: 12, paddingVertical: 10, borderRadius: 12,
  },
  shopCtaText: { color: "#fff", fontSize: 12, fontFamily: F.bold },

  card: {
    borderRadius: 18,
    borderWidth: 1,
    backgroundColor: "rgba(10,12,22,0.78)",
    padding: 16,
    gap: 12,
    overflow: "hidden",
  },
  recommendedRibbon: {
    alignSelf: "flex-start",
    flexDirection: "row",
    alignItems: "center",
    gap: 5,
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 999,
    borderWidth: 1,
  },
  recommendedRibbonText: {
    fontSize: 9,
    fontFamily: F.extra,
    letterSpacing: 1.2,
    textTransform: "uppercase",
  },
  cardRow: { flexDirection: "row", alignItems: "center", gap: 14 },
  gemOrbWrap: { width: 58, height: 58, alignItems: "center", justifyContent: "center" },
  gemOrbGlow: {
    position: "absolute",
    width: 58,
    height: 58,
    borderRadius: 29,
  },
  gemOrb: {
    width: 52,
    height: 52,
    borderRadius: 26,
    alignItems: "center",
    justifyContent: "center",
    borderWidth: 1,
    borderColor: "rgba(255,255,255,0.25)",
  },
  gemOrbEmoji: { fontSize: 22 },
  gemTitle: { color: "#fff", fontSize: 16, fontFamily: F.extra },
  gemSubEn: { color: "rgba(255,255,255,0.45)", fontSize: 11, fontFamily: F.semi },
  planetRow: { flexDirection: "row", alignItems: "center", gap: 5, marginTop: 2 },
  planetEmoji: { fontSize: 12 },
  planetText: { fontSize: 12, fontFamily: F.bold },
  dayDot: { color: "rgba(255,255,255,0.35)", fontSize: 12 },
  dayText: { color: "rgba(255,255,255,0.55)", fontSize: 11, fontFamily: F.semi },
  benefitText: {
    color: "rgba(255,255,255,0.82)",
    fontSize: 12.5,
    fontFamily: F.semi,
    lineHeight: 19,
  },
  metaRow: { flexDirection: "row", flexWrap: "wrap", gap: 8 },
  metaChip: {
    flexDirection: "row",
    alignItems: "center",
    gap: 5,
    paddingHorizontal: 9,
    paddingVertical: 5,
    borderRadius: 999,
    borderWidth: 1,
    maxWidth: "100%",
  },
  metaChipText: {
    color: "rgba(255,255,255,0.75)",
    fontSize: 10,
    fontFamily: F.semi,
    flexShrink: 1,
  },

  disclaimer: {
    color: "rgba(255,255,255,0.4)",
    fontSize: 10,
    lineHeight: 15,
    fontFamily: F.regular,
    textAlign: "center",
    marginTop: 8,
  },
});

const ui = StyleSheet.create({
  orb: {
    position: "absolute",
    top: -50,
    right: -30,
    width: 200,
    height: 200,
    borderRadius: 100,
  },
  headerBadge: {
    fontSize: 10,
    fontFamily: F.extra,
    letterSpacing: 2.2,
    color: GEM_ACCENT,
    textTransform: "uppercase",
    marginBottom: 2,
  },
});
