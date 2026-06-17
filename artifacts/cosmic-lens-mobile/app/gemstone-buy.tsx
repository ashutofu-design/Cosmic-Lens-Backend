import { Feather } from "@expo/vector-icons";
import { BlurView } from "expo-blur";
import * as Clipboard from "expo-clipboard";
import * as Haptics from "expo-haptics";
import { LinearGradient } from "expo-linear-gradient";
import { router, useLocalSearchParams } from "expo-router";
import React, { useCallback, useEffect, useMemo, useState } from "react";
import {
  ActivityIndicator,
  Alert,
  I18nManager,
  Platform,
  Pressable,
  ScrollView,
  Share,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { CosmicBg } from "@/components/CosmicBg";
import { GemstoneProductGallery } from "@/components/gemstone/GemstoneProductGallery";
import { FadeInView, staggerDelay } from "@/components/motion/FadeInView";
import { useUser } from "@/context/UserContext";
import { useT } from "@/hooks/useT";
import {
  fetchGemstoneQuote,
  fetchMyReferralCode,
  type GemstoneQuote,
  type MyReferralInfo,
} from "@/lib/gemstoneBilling";
import { startGemstoneCheckout } from "@/lib/gemstoneCheckoutFlow";
import { GEMSTONE_CATALOG } from "@/lib/gemstoneCatalog";
import {
  EMERALD_BENEFITS,
  EMERALD_CARE_TIPS,
  EMERALD_SPECS,
  EMERALD_TRUST_BADGES,
  EMERALD_WEAR_STEPS,
  PUKHRAJ_BENEFITS,
  PUKHRAJ_CARE_TIPS,
  PUKHRAJ_SPECS,
  PUKHRAJ_TRUST_BADGES,
  PUKHRAJ_WEAR_STEPS,
} from "@/lib/gemstoneProductContent";
import {
  formatInr,
  getDefaultSkuForProduct,
  getGemstoneSkuPricing,
  getProductLineById,
  getProductLineForSku,
  isSelfReferral,
  normalizeReferralCode,
  referralCodeForUserId,
  referralPriceFor,
  selfPriceFor,
  type GemstoneProductId,
} from "@/lib/gemstonePricing";
import { GEMSTONE, pick } from "@/lib/i18nVedic";

const F = {
  regular: "Nunito_400Regular",
  semi: "Nunito_600SemiBold",
  bold: "Nunito_700Bold",
  extra: "Nunito_800ExtraBold",
} as const;

function Collapsible({
  title,
  icon,
  open,
  onToggle,
  children,
  accentColor = "#fbbf24",
}: {
  title: string;
  icon: keyof typeof Feather.glyphMap;
  open: boolean;
  onToggle: () => void;
  children: React.ReactNode;
  accentColor?: string;
}) {
  return (
    <View style={s.card}>
      <Pressable onPress={onToggle} style={s.collapseHead}>
        <View style={s.collapseTitleRow}>
          <Feather name={icon} size={15} color={accentColor} />
          <Text style={s.collapseTitle}>{title}</Text>
        </View>
        <Feather name={open ? "chevron-up" : "chevron-down"} size={18} color="rgba(255,255,255,0.45)" />
      </Pressable>
      {open ? <View style={s.collapseBody}>{children}</View> : null}
    </View>
  );
}

export default function GemstoneBuyScreen() {
  const insets = useSafeAreaInsets();
  const t = useT();
  const { user } = useUser();
  const vlang = t.vlang;
  const params = useLocalSearchParams<{ sku?: string; ref?: string; ratti?: string; product?: string }>();
  const productId: GemstoneProductId = params.product === "emerald" ? "emerald" : "pukhraj";
  const productLine = getProductLineById(productId)!;
  const accent = productLine.accent;
  const rattiRows = productLine.rattiRows;
  const trustBadges = productId === "emerald" ? EMERALD_TRUST_BADGES : PUKHRAJ_TRUST_BADGES;
  const specs = productId === "emerald" ? EMERALD_SPECS : PUKHRAJ_SPECS;
  const benefits = productId === "emerald" ? EMERALD_BENEFITS : PUKHRAJ_BENEFITS;
  const wearSteps = productId === "emerald" ? EMERALD_WEAR_STEPS : PUKHRAJ_WEAR_STEPS;
  const careTips = productId === "emerald" ? EMERALD_CARE_TIPS : PUKHRAJ_CARE_TIPS;
  const benefitTag = productId === "emerald" ? "Speech, Business & Budh Blessings" : t.gs_benefitTag;

  const initialSku = (params.sku as string)
    || (params.ratti
      ? rattiRows.find(r => String(r.ratti) === String(params.ratti))?.sku
      : undefined)
    || getDefaultSkuForProduct(productId);
  const [selectedSku, setSelectedSku] = useState(initialSku);
  const pricing = getGemstoneSkuPricing(selectedSku) ?? rattiRows[0];
  const activeLine = getProductLineForSku(selectedSku) ?? productLine;
  const catalog = GEMSTONE_CATALOG.find(g => g.id === activeLine.catalogId);

  const [referralInput, setReferralInput] = useState((params.ref as string) || "");
  const [useReferral, setUseReferral] = useState(!!params.ref);
  const [quote, setQuote] = useState<GemstoneQuote | null>(null);
  const [referralInfo, setReferralInfo] = useState<MyReferralInfo | null>(null);
  const [loadingQuote, setLoadingQuote] = useState(false);
  const [paying, setPaying] = useState(false);
  const [quoteErr, setQuoteErr] = useState<string | null>(null);
  const [openSpecs, setOpenSpecs] = useState(true);
  const [openWhy, setOpenWhy] = useState(false);
  const [openWear, setOpenWear] = useState(false);
  const [openCare, setOpenCare] = useState(false);

  const headerTopPad = insets.top + 8;
  const gemName = catalog ? pick(vlang, GEMSTONE[catalog.gemstoneKey]) : activeLine.label;

  const loadQuote = useCallback(async () => {
    if (!user?.id || !user.api_key) {
      setQuote(null);
      return;
    }
    setLoadingQuote(true);
    setQuoteErr(null);
    try {
      const code = useReferral ? normalizeReferralCode(referralInput) : undefined;
      if (useReferral && code && isSelfReferral(user.id, code)) {
        setQuoteErr("self_referral_not_allowed");
        setQuote(null);
        return;
      }
      const q = await fetchGemstoneQuote(user, selectedSku, useReferral ? code : undefined);
      setQuote(q);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "quote_failed";
      setQuoteErr(msg);
      setQuote(null);
    } finally {
      setLoadingQuote(false);
    }
  }, [user, selectedSku, useReferral, referralInput]);

  useEffect(() => {
    void loadQuote();
  }, [loadQuote]);

  useEffect(() => {
    if (!user?.id || !user.api_key) return;
    fetchMyReferralCode(user)
      .then(setReferralInfo)
      .catch(() => undefined);
  }, [user?.id, user?.api_key]);

  const displayQuote = useMemo(() => {
    const disc = useReferral ? pricing.referralBuyerDiscountInr : pricing.selfDiscountInr;
    if (quote) return quote;
    return {
      sku: selectedSku,
      mrp_inr: pricing.mrpInr,
      discount_inr: disc,
      discount_type: (useReferral ? "referral" : "self") as "self" | "referral",
      amount_inr: pricing.mrpInr - disc,
      referrer_reward_inr: useReferral ? pricing.referrerRewardInr : 0,
    };
  }, [quote, pricing, selectedSku, useReferral]);

  const referrerReward = quote?.referrer_reward_inr ?? pricing.referrerRewardInr;
  const savePct = Math.max(1, Math.round((displayQuote.discount_inr / displayQuote.mrp_inr) * 100));

  async function handleBuy() {
    if (!user?.id) {
      Alert.alert("Login required", "Please sign in to continue.", [{ text: "OK" }]);
      return;
    }
    setPaying(true);
    try {
      await startGemstoneCheckout({
        user,
        sku: selectedSku,
        referralCode: useReferral ? normalizeReferralCode(referralInput) : undefined,
        label: `${activeLine.label} — ${pricing.ratti} ${t.gs_ratti}`,
      });
    } finally {
      setPaying(false);
    }
  }

  async function shareReferral() {
    const code = referralInfo?.referral_code || (user?.id ? referralCodeForUserId(user.id) : "");
    const msg = referralInfo?.share_message
      || `Use code ${code} on Cosmic Lens gemstones — referral discount for you, reward for me after delivery.`;
    try {
      await Share.share({ message: msg });
    } catch {
      await Clipboard.setStringAsync(msg);
      Alert.alert("Copied", "Referral message copied.");
    }
  }

  return (
    <CosmicBg>
      <View style={[s.topBar, { paddingTop: headerTopPad, borderBottomColor: `${accent}22` }]}>
        {Platform.OS === "ios" ? (
          <BlurView intensity={48} tint="dark" style={StyleSheet.absoluteFill} />
        ) : (
          <View style={[StyleSheet.absoluteFill, s.topBarBg]} />
        )}
        <View style={s.topBarRow}>
          <Pressable onPress={() => { Haptics.selectionAsync(); router.back(); }} style={s.backBtn} hitSlop={10}>
            <View style={s.backCircle}>
              <Feather name={I18nManager.isRTL ? "arrow-right" : "arrow-left"} size={20} color="#fff" />
            </View>
          </Pressable>
          <Text style={s.topTitle}>{t.gs_buyTitle}</Text>
          <View style={{ width: 40 }} />
        </View>
      </View>

      <ScrollView
        contentContainerStyle={{ paddingTop: headerTopPad + 52, paddingBottom: insets.bottom + 110 }}
        showsVerticalScrollIndicator={false}
        keyboardShouldPersistTaps="handled"
      >
        <FadeInView delay={staggerDelay(0)}>
          <GemstoneProductGallery
            product={productId}
            accent={accent}
            trustLabel={t.gs_certified}
            reviewHint={productId === "pukhraj" ? "Verified buyers" : undefined}
          />
        </FadeInView>

        <View style={s.content}>
          <FadeInView delay={staggerDelay(1)}>
            <View style={s.titleBlock}>
              <Text style={s.productTitle}>{gemName}</Text>
              <Text style={s.productSub}>{activeLine.label}</Text>
              <View style={[s.benefitPill, { backgroundColor: `${accent}1f`, borderColor: `${accent}59` }]}>
                <Text style={[s.benefitPillText, { color: accent }]}>{benefitTag}</Text>
              </View>
            </View>
          </FadeInView>

          <FadeInView delay={staggerDelay(2)}>
            <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={s.trustRow}>
              {trustBadges.map(b => (
                <View key={b.label} style={s.trustChip}>
                  <Feather name={b.icon} size={12} color={accent} />
                  <Text style={s.trustChipText}>{b.label}</Text>
                </View>
              ))}
            </ScrollView>
            <Text style={s.promiseText}>{t.gs_authenticPromise}</Text>
          </FadeInView>

          <FadeInView delay={staggerDelay(3)}>
            <View style={[s.priceCard, { borderColor: `${accent}44` }]}>
              <LinearGradient colors={[`${accent}18`, "transparent"]} style={StyleSheet.absoluteFill} pointerEvents="none" />
              <View style={s.priceTop}>
                <View>
                  <Text style={s.mrpStrike}>{formatInr(displayQuote.mrp_inr)}</Text>
                  <Text style={[s.payPrice, { color: accent }]}>{formatInr(displayQuote.amount_inr)}</Text>
                </View>
                <View style={s.offBadge}>
                  <Text style={s.offBadgeText}>{savePct}% OFF</Text>
                </View>
              </View>
              <Text style={s.saveLine}>
                {t.gs_youSave} {formatInr(displayQuote.discount_inr)} · {pricing.ratti} {t.gs_ratti}
              </Text>
            </View>
          </FadeInView>

          <FadeInView delay={staggerDelay(4)}>
            <View style={[s.card, s.rattiCard]}>
              <Text style={s.rattiLabel}>{t.gs_selectRatti}</Text>
              <View style={s.rattiRow}>
                {rattiRows.map(row => {
                  const on = row.sku === selectedSku;
                  return (
                    <Pressable
                      key={row.sku}
                      disabled={!row.inStock}
                      onPress={() => {
                        if (!row.inStock) return;
                        Haptics.selectionAsync();
                        setSelectedSku(row.sku);
                        setQuote(null);
                      }}
                      style={({ pressed }) => [
                        s.rattiChip, on && [s.rattiChipOn, { borderColor: `${accent}88`, backgroundColor: `${accent}24` }], !row.inStock && s.rattiChipOff,
                        pressed && { opacity: 0.85 },
                      ]}
                    >
                      <Text style={[s.rattiChipText, on && { color: accent }]}>
                        {row.ratti}
                        <Text style={[s.rattiChipSuffix, on && { color: `${accent}b3` }]}>R</Text>
                      </Text>
                    </Pressable>
                  );
                })}
              </View>
            </View>
          </FadeInView>

          <FadeInView delay={staggerDelay(6)}>
            <View style={s.card}>
              <Text style={s.cardLabel}>{t.gs_offerSelf}</Text>
              <Pressable
                onPress={() => { setUseReferral(false); Haptics.selectionAsync(); }}
                style={[s.optionRow, !useReferral && [s.optionRowOn, { borderColor: `${accent}55`, backgroundColor: `${accent}0f` }]]}
              >
                <Feather name={!useReferral ? "check-circle" : "circle"} size={18} color={!useReferral ? accent : "#64748b"} />
                <View style={{ flex: 1 }}>
                  <Text style={s.optionTitle}>{t.gs_selfBuy}</Text>
                  <Text style={s.optionSub}>{formatInr(pricing.selfDiscountInr)} {t.gs_flatOff}</Text>
                </View>
                <Text style={s.optionAmt}>{formatInr(selfPriceFor(pricing))}</Text>
              </Pressable>
            </View>
          </FadeInView>

          <FadeInView delay={staggerDelay(7)}>
            <View style={[s.card, { borderColor: "#a78bfa44" }]}>
              <Text style={s.cardLabel}>{t.gs_offerReferral}</Text>
              <Pressable
                onPress={() => { setUseReferral(true); Haptics.selectionAsync(); }}
                style={[s.optionRow, useReferral && s.optionRowOnPurple]}
              >
                <Feather name={useReferral ? "check-circle" : "circle"} size={18} color={useReferral ? "#a78bfa" : "#64748b"} />
                <View style={{ flex: 1 }}>
                  <Text style={s.optionTitle}>{t.gs_referralBuy}</Text>
                  <Text style={s.optionSub}>
                    {formatInr(pricing.referralBuyerDiscountInr)} {t.gs_flatOff} · {t.gs_referrerGets}{" "}
                    {formatInr(referrerReward)}
                  </Text>
                </View>
                <Text style={s.optionAmt}>{formatInr(referralPriceFor(pricing))}</Text>
              </Pressable>
              {useReferral ? (
                <View style={{ gap: 8, marginTop: 4 }}>
                  <TextInput
                    value={referralInput}
                    onChangeText={setReferralInput}
                    placeholder={t.gs_referralPlaceholder}
                    placeholderTextColor="rgba(255,255,255,0.35)"
                    autoCapitalize="characters"
                    style={s.input}
                  />
                  {quoteErr === "self_referral_not_allowed" ? (
                    <Text style={s.errText}>{t.gs_selfReferralErr}</Text>
                  ) : null}
                  <Text style={s.hintText}>{t.gs_referralHint}</Text>
                </View>
              ) : null}
            </View>
          </FadeInView>

          {user?.id ? (
            <FadeInView delay={staggerDelay(8)}>
              <View style={[s.card, { borderColor: "rgba(34,197,94,0.35)" }]}>
                <Text style={s.cardLabel}>{t.gs_yourReferral}</Text>
                <View style={s.refRow}>
                  <Text style={s.refCode}>{referralInfo?.referral_code || referralCodeForUserId(user.id)}</Text>
                  <Pressable
                    onPress={async () => {
                      const c = referralInfo?.referral_code || referralCodeForUserId(user.id);
                      await Clipboard.setStringAsync(c);
                      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
                      Alert.alert("Copied", c);
                    }}
                    style={s.iconBtn}
                  >
                    <Feather name="copy" size={16} color="#22c55e" />
                  </Pressable>
                  <Pressable onPress={() => void shareReferral()} style={s.iconBtn}>
                    <Feather name="share-2" size={16} color="#22c55e" />
                  </Pressable>
                </View>
                <Text style={s.hintText}>
                  {t.gs_referralEarn} up to {formatInr(Math.max(...rattiRows.map(r => r.referrerRewardInr)))}{" "}
                  {t.gs_afterDelivery}
                </Text>
              </View>
            </FadeInView>
          ) : null}

          <FadeInView delay={staggerDelay(9)}>
            <Collapsible
              title={t.gs_productSpecs}
              icon="settings"
              open={openSpecs}
              onToggle={() => setOpenSpecs(v => !v)}
              accentColor={accent}
            >
              {specs.map(row => (
                <View key={row.label} style={s.specRow}>
                  <Text style={s.specLabel}>{row.label}</Text>
                  <Text style={s.specVal}>{row.value}</Text>
                </View>
              ))}
            </Collapsible>
          </FadeInView>

          <FadeInView delay={staggerDelay(10)}>
            <Collapsible
              title={t.gs_whyWear}
              icon="star"
              open={openWhy}
              onToggle={() => setOpenWhy(v => !v)}
              accentColor={accent}
            >
              {benefits.map(b => (
                <View key={b} style={s.bulletRow}>
                  <Feather name="check" size={13} color={accent} />
                  <Text style={s.bulletText}>{b}</Text>
                </View>
              ))}
            </Collapsible>
          </FadeInView>

          <FadeInView delay={staggerDelay(11)}>
            <Collapsible
              title={t.gs_howToWear}
              icon="help-circle"
              open={openWear}
              onToggle={() => setOpenWear(v => !v)}
              accentColor={accent}
            >
              <View style={s.grid2}>
                {wearSteps.map(step => (
                  <View key={step.title} style={s.gridCard}>
                    <View style={[s.gridIcon, { backgroundColor: `${accent}1a` }]}>
                      <Feather name={step.icon} size={16} color={accent} />
                    </View>
                    <Text style={s.gridText}>{step.title}</Text>
                  </View>
                ))}
              </View>
            </Collapsible>
          </FadeInView>

          <FadeInView delay={staggerDelay(12)}>
            <Collapsible
              title={t.gs_careTitle}
              icon="heart"
              open={openCare}
              onToggle={() => setOpenCare(v => !v)}
              accentColor={accent}
            >
              <View style={s.grid2}>
                {careTips.map(tip => (
                  <View key={tip.text} style={s.gridCard}>
                    <View style={[s.gridIcon, { backgroundColor: `${accent}1a` }]}>
                      <Feather name={tip.icon} size={16} color={accent} />
                    </View>
                    <Text style={s.gridText}>{tip.text}</Text>
                  </View>
                ))}
              </View>
            </Collapsible>
          </FadeInView>

          <FadeInView delay={staggerDelay(13)}>
            <View style={[s.deliveryCard, { backgroundColor: `${accent}0f`, borderColor: `${accent}33` }]}>
              <Feather name="package" size={16} color={accent} />
              <Text style={s.deliveryText}>{t.gs_deliveryNote}</Text>
            </View>
            <Text style={s.disclaimer}>{t.gs_disclaimer}</Text>
          </FadeInView>
        </View>
      </ScrollView>

      <View style={[s.footer, { paddingBottom: insets.bottom + 10 }]}>
        <View style={s.footerPrice}>
          <Text style={s.footerPay}>{formatInr(displayQuote.amount_inr)}</Text>
          <Text style={s.footerMrp}>{formatInr(displayQuote.mrp_inr)}</Text>
        </View>
        <Pressable
          disabled={paying || loadingQuote || quoteErr === "self_referral_not_allowed" || (useReferral && !referralInput.trim())}
          onPress={() => void handleBuy()}
          style={({ pressed }) => [s.footerBtnWrap, { opacity: pressed ? 0.88 : 1, flex: 1 }]}
        >
          <LinearGradient colors={[productId === "emerald" ? "#059669" : "#d97706", accent]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }} style={s.buyBtn}>
            {paying || loadingQuote ? (
              <ActivityIndicator color="#fff" />
            ) : (
              <>
                <Feather name="shopping-bag" size={16} color="#fff" />
                <Text style={s.buyBtnText}>{t.gs_payNow}</Text>
              </>
            )}
          </LinearGradient>
        </Pressable>
      </View>
    </CosmicBg>
  );
}

const s = StyleSheet.create({
  topBar: {
    position: "absolute", top: 0, left: 0, right: 0, zIndex: 20,
    paddingHorizontal: 14, paddingBottom: 12, borderBottomWidth: 1, overflow: "hidden",
  },
  topBarBg: { backgroundColor: "rgba(14,10,28,0.94)" },
  topBarRow: { flexDirection: "row", alignItems: "center", justifyContent: "space-between" },
  backBtn: { padding: 4 },
  backCircle: {
    width: 40, height: 40, borderRadius: 20,
    backgroundColor: "rgba(255,255,255,0.08)", borderWidth: 1, borderColor: "rgba(255,255,255,0.14)",
    alignItems: "center", justifyContent: "center",
  },
  topTitle: { color: "#fff", fontSize: 16, fontFamily: F.bold },
  content: { paddingHorizontal: 18, gap: 12, paddingTop: 12 },
  titleBlock: { gap: 6 },
  productTitle: { color: "#fff", fontSize: 22, fontFamily: F.extra, letterSpacing: -0.3 },
  productSub: { color: "rgba(255,255,255,0.55)", fontSize: 13, fontFamily: F.semi },
  benefitPill: {
    alignSelf: "flex-start", marginTop: 4, paddingHorizontal: 10, paddingVertical: 5, borderRadius: 999,
    backgroundColor: "rgba(251,191,36,0.12)", borderWidth: 1, borderColor: "rgba(251,191,36,0.35)",
  },
  benefitPillText: { fontSize: 10.5, fontFamily: F.bold },
  trustRow: { gap: 8, paddingVertical: 4 },
  trustChip: {
    flexDirection: "row", alignItems: "center", gap: 5, paddingHorizontal: 10, paddingVertical: 7,
    borderRadius: 999, backgroundColor: "rgba(255,255,255,0.04)", borderWidth: 1, borderColor: "rgba(251,191,36,0.2)",
  },
  trustChipText: { color: "rgba(255,255,255,0.75)", fontSize: 10, fontFamily: F.semi },
  promiseText: { color: "rgba(255,255,255,0.45)", fontSize: 10.5, lineHeight: 15, fontFamily: F.regular, marginTop: 4 },
  priceCard: {
    borderRadius: 16, borderWidth: 1, backgroundColor: "rgba(12,10,24,0.85)",
    padding: 14, overflow: "hidden", gap: 6,
  },
  priceTop: { flexDirection: "row", alignItems: "flex-end", justifyContent: "space-between" },
  mrpStrike: {
    color: "rgba(255,255,255,0.4)", fontSize: 13, fontFamily: F.semi, textDecorationLine: "line-through",
  },
  payPrice: { fontSize: 30, fontFamily: F.extra, letterSpacing: -0.5 },
  offBadge: {
    paddingHorizontal: 8, paddingVertical: 4, borderRadius: 6,
    backgroundColor: "rgba(34,197,94,0.15)", borderWidth: 1, borderColor: "rgba(34,197,94,0.35)",
  },
  offBadgeText: { color: "#4ade80", fontSize: 10, fontFamily: F.bold },
  saveLine: { color: "rgba(255,255,255,0.55)", fontSize: 11, fontFamily: F.semi },
  rattiCard: { paddingVertical: 10, paddingHorizontal: 12, gap: 8 },
  rattiLabel: {
    color: "rgba(255,255,255,0.45)", fontSize: 9, fontFamily: F.extra,
    letterSpacing: 1.4, textTransform: "uppercase",
  },
  rattiRow: { flexDirection: "row", gap: 5 },
  rattiChip: {
    flex: 1, paddingVertical: 7, borderRadius: 9,
    borderWidth: 1, borderColor: "rgba(255,255,255,0.1)", alignItems: "center",
    backgroundColor: "rgba(255,255,255,0.03)",
  },
  rattiChipOn: { borderColor: "rgba(251,191,36,0.53)", backgroundColor: "rgba(251,191,36,0.14)" },
  rattiChipOff: { opacity: 0.35 },
  rattiChipText: { color: "rgba(255,255,255,0.65)", fontSize: 13, fontFamily: F.bold },
  rattiChipTextOn: { color: "#fbbf24" },
  rattiChipSuffix: { fontSize: 9, fontFamily: F.semi, color: "rgba(255,255,255,0.35)" },
  rattiChipSuffixOn: { color: "rgba(251,191,36,0.7)" },
  card: {
    borderRadius: 16, borderWidth: 1, borderColor: "rgba(251,191,36,0.15)",
    backgroundColor: "rgba(10,12,22,0.78)", padding: 14, gap: 10,
  },
  cardLabel: {
    color: "rgba(255,255,255,0.45)", fontSize: 10, fontFamily: F.extra,
    letterSpacing: 1.8, textTransform: "uppercase",
  },
  optionRow: {
    flexDirection: "row", alignItems: "center", gap: 10,
    padding: 12, borderRadius: 12, borderWidth: 1, borderColor: "rgba(255,255,255,0.06)",
  },
  optionRowOn: { borderColor: "rgba(251,191,36,0.33)", backgroundColor: "rgba(251,191,36,0.06)" },
  optionRowOnPurple: { borderColor: "#a78bfa55", backgroundColor: "rgba(167,139,250,0.06)" },
  optionTitle: { color: "#fff", fontSize: 13, fontFamily: F.bold },
  optionSub: { color: "rgba(255,255,255,0.55)", fontSize: 11, fontFamily: F.semi, marginTop: 2 },
  optionAmt: { color: "#fff", fontSize: 14, fontFamily: F.extra },
  input: {
    borderWidth: 1, borderColor: "rgba(167,139,250,0.35)", borderRadius: 12,
    paddingHorizontal: 14, paddingVertical: 11, color: "#fff", fontFamily: F.semi, fontSize: 14,
    backgroundColor: "rgba(0,0,0,0.25)",
  },
  errText: { color: "#f87171", fontSize: 11, fontFamily: F.semi },
  hintText: { color: "rgba(255,255,255,0.45)", fontSize: 10.5, lineHeight: 15, fontFamily: F.regular },
  refRow: { flexDirection: "row", alignItems: "center", gap: 8 },
  refCode: { flex: 1, color: "#22c55e", fontSize: 20, fontFamily: F.extra, letterSpacing: 1 },
  iconBtn: {
    width: 36, height: 36, borderRadius: 10, alignItems: "center", justifyContent: "center",
    backgroundColor: "rgba(34,197,94,0.1)", borderWidth: 1, borderColor: "rgba(34,197,94,0.25)",
  },
  collapseHead: { flexDirection: "row", alignItems: "center", justifyContent: "space-between" },
  collapseTitleRow: { flexDirection: "row", alignItems: "center", gap: 8 },
  collapseTitle: { color: "#fff", fontSize: 13, fontFamily: F.bold },
  collapseBody: { gap: 8, marginTop: 4, paddingTop: 8, borderTopWidth: 1, borderTopColor: "rgba(255,255,255,0.06)" },
  specRow: { flexDirection: "row", justifyContent: "space-between", gap: 12, paddingVertical: 4 },
  specLabel: { color: "rgba(255,255,255,0.45)", fontSize: 11, fontFamily: F.semi, flex: 1 },
  specVal: { color: "#fff", fontSize: 11, fontFamily: F.bold, flex: 1.2, textAlign: "right" },
  bulletRow: { flexDirection: "row", alignItems: "flex-start", gap: 8 },
  bulletText: { flex: 1, color: "rgba(255,255,255,0.72)", fontSize: 11.5, lineHeight: 17, fontFamily: F.regular },
  grid2: { flexDirection: "row", flexWrap: "wrap", gap: 8 },
  gridCard: {
    width: "48%", flexGrow: 1, minWidth: "46%",
    padding: 10, borderRadius: 12, gap: 8,
    backgroundColor: "rgba(255,255,255,0.03)", borderWidth: 1, borderColor: "rgba(255,255,255,0.06)",
  },
  gridIcon: {
    width: 32, height: 32, borderRadius: 10, alignItems: "center", justifyContent: "center",
    backgroundColor: "rgba(251,191,36,0.1)",
  },
  gridText: { color: "rgba(255,255,255,0.7)", fontSize: 10.5, lineHeight: 15, fontFamily: F.regular },
  deliveryCard: {
    flexDirection: "row", alignItems: "flex-start", gap: 10, padding: 12, borderRadius: 12,
    backgroundColor: "rgba(251,191,36,0.06)", borderWidth: 1, borderColor: "rgba(251,191,36,0.2)",
  },
  deliveryText: { flex: 1, color: "rgba(255,255,255,0.65)", fontSize: 11, lineHeight: 16, fontFamily: F.semi },
  disclaimer: {
    color: "rgba(255,255,255,0.38)", fontSize: 10, lineHeight: 15, fontFamily: F.regular,
    textAlign: "center", marginTop: 10,
  },
  footer: {
    position: "absolute", left: 0, right: 0, bottom: 0,
    flexDirection: "row", alignItems: "center", gap: 12,
    paddingHorizontal: 16, paddingTop: 10,
    borderTopWidth: 1, borderTopColor: "rgba(255,255,255,0.08)",
    backgroundColor: "rgba(8,10,18,0.94)",
  },
  footerPrice: { minWidth: 88 },
  footerPay: { color: "#fff", fontSize: 18, fontFamily: F.extra },
  footerMrp: {
    color: "rgba(255,255,255,0.4)", fontSize: 11, fontFamily: F.semi, textDecorationLine: "line-through",
  },
  footerBtnWrap: { maxWidth: "100%" },
  buyBtn: {
    flexDirection: "row", alignItems: "center", justifyContent: "center",
    gap: 8, paddingVertical: 14, borderRadius: 14,
  },
  buyBtnText: { color: "#fff", fontSize: 15, fontFamily: F.bold },
});
