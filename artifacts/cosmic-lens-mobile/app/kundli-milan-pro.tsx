import { Feather } from "@expo/vector-icons";
import * as Haptics from "expo-haptics";
import { router, useFocusEffect, useLocalSearchParams } from "expo-router";
import React, { useCallback, useState } from "react";
import {
  Alert,
  Platform,
  Pressable,
  ScrollView,
  StatusBar,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import AsyncStorage from "@react-native-async-storage/async-storage";

import { CosmicBg } from "@/components/CosmicBg";
import { MarriageCompatProPurchase } from "@/components/kundliMilan/MarriageCompatProPurchase";
import { MarriageCompatProStickyCta } from "@/components/kundliMilan/MarriageCompatProStickyCta";
import { FadeInView, staggerDelay } from "@/components/motion/FadeInView";
import { ProPdfLanguagePickerModal } from "@/components/ProPdfLanguagePickerModal";
import { OrderSuccessModal } from "@/components/OrderSuccessModal";
import { useC } from "@/context/ThemeContext";
import { useUser } from "@/context/UserContext";
import { useT } from "@/hooks/useT";
import {
  consumeCouplePaidReady,
  gateCoupleReportAfterLangPick,
} from "@/lib/coupleReportCheckoutFlow";
import {
  getPendingCoupleCheckout,
} from "@/lib/pendingCoupleCheckout";
import { submitMilanHumanOrder } from "@/lib/milanHumanOrder";
import { milanProScreenCopy } from "@/lib/milanProCopyI18n";
import {
  MILAN_PRO_CHECKOUT_CONFIG,
  MILAN_PRO_UI_PRICING,
  milanOrderTotalInr,
  runMilanProUnlockCta,
} from "@/lib/milanProOffer";
import { packLovePerson } from "@/lib/loveRealityPack";
import { coerceProPdfLang } from "@/lib/proPdfLang";

export default function KundliMilanProScreen() {
  const C = useC();
  const t = useT();
  const { user, profiles, primaryProfileId, language } = useUser();
  const params = useLocalSearchParams<{ partnerId?: string }>();
  const partnerId = typeof params.partnerId === "string" ? params.partnerId : null;
  const insets = useSafeAreaInsets();
  const androidSB = StatusBar.currentHeight ?? 24;
  const topPad = Platform.OS === "android" ? Math.max(insets.top, androidSB) : insets.top;
  const botPad = insets.bottom;
  const isDark = C.isDark;

  const primaryProfile = profiles.find(p => p.id === primaryProfileId) ?? profiles[0] ?? null;
  const partnerProfile = partnerId
    ? (profiles.find(p => p.id === partnerId) ?? null)
    : (profiles.find(p => p.id !== primaryProfileId && p.kundli && p.birthData) ?? null);

  const pendingMilan = getPendingCoupleCheckout()?.product === "milan_pro"
    ? getPendingCoupleCheckout()
    : null;

  const hasSelfKundli = !!primaryProfile?.kundli && !!primaryProfile?.birthData;
  const hasPartnerKundli = !!partnerProfile?.kundli && !!partnerProfile?.birthData;
  const hasPendingCouple = !!(pendingMilan?.p1 && pendingMilan?.p2);
  const canPro = (hasSelfKundli && hasPartnerKundli) || hasPendingCouple;

  const [priorityDelivery, setPriorityDelivery] = useState(false);
  const [langPickerVisible, setLangPickerVisible] = useState(false);
  const [selectedPdfLang, setSelectedPdfLang] = useState(coerceProPdfLang(language || t.lang));
  const displayLang = coerceProPdfLang(selectedPdfLang);
  const proCopy = milanProScreenCopy(displayLang);
  const [checkoutLoading, setCheckoutLoading] = useState(false);
  const [submittingOrder, setSubmittingOrder] = useState(false);
  const [preparingBanner, setPreparingBanner] = useState<{
    priority: boolean;
    etaHours: number;
  } | null>(null);

  useFocusEffect(
    useCallback(() => {
      if (consumeCouplePaidReady()) {
        const pending = getPendingCoupleCheckout();
        if (pending?.lang) setSelectedPdfLang(coerceProPdfLang(pending.lang));
        if (pending?.urgent != null) setPriorityDelivery(pending.urgent);
        void placeVerifiedPdfOrder({
          langOverride: pending?.lang,
          urgentOverride: pending?.urgent,
        });
      }
    }, []),
  );

  function goBack() {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    router.replace({
      pathname: "/kundli-milan",
      params: { partnerId: partnerId ?? "" },
    } as never);
  }

  function showKundliRequired() {
    if (!hasSelfKundli) {
      router.push("/profile-edit" as any);
      return;
    }
    if (!partnerProfile) {
      router.push("/relationship" as any);
      return;
    }
    if (!hasPartnerKundli) {
      router.push("/profile-edit?relation=partner" as any);
    }
  }

  async function placeVerifiedPdfOrder(opts?: {
    langOverride?: string;
    urgentOverride?: boolean;
  }) {
    if (!user?.id) {
      Alert.alert("Login required", proCopy.loginRequired, [{ text: "OK" }]);
      return;
    }

    const lang = coerceProPdfLang(opts?.langOverride ?? selectedPdfLang);
    const urgent = opts?.urgentOverride ?? priorityDelivery;

    let p1: Record<string, unknown> | null = null;
    let p2: Record<string, unknown> | null = null;

    if (primaryProfile?.birthData && partnerProfile?.birthData) {
      p1 = packLovePerson(primaryProfile.birthData, primaryProfile.name);
      p2 = packLovePerson(partnerProfile.birthData, partnerProfile.name);
    } else if (pendingMilan?.p1 && pendingMilan?.p2) {
      p1 = pendingMilan.p1;
      p2 = pendingMilan.p2;
    }

    if (!p1 || !p2) {
      Alert.alert("Kundli missing", proCopy.kundliMissing, [{ text: "OK" }]);
      return;
    }

    setSubmittingOrder(true);
    try {
      const result = await submitMilanHumanOrder({
        p1,
        p2,
        lang,
        urgent,
        userId: user.id,
        cosmoUserId: user.cosmo_user_id,
        apiKey: user.api_key,
      });
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      setPreparingBanner({
        priority: urgent,
        etaHours: Number(result.eta_hours) || (urgent ? 12 : 24),
      });
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Order failed";
      Alert.alert("Could not place order", msg);
    } finally {
      setSubmittingOrder(false);
    }
  }

  function startProUnlock() {
    if (!canPro) {
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Warning);
      showKundliRequired();
      return;
    }
    runMilanProUnlockCta({
      continueProExperience: () => {
        void (async () => {
          try {
            const stored = await AsyncStorage.getItem("cosmic.milanPro.lastLang");
            setSelectedPdfLang(coerceProPdfLang(stored || t.lang));
          } catch {
            setSelectedPdfLang(coerceProPdfLang(t.lang));
          }
          setLangPickerVisible(true);
        })();
      },
    });
  }

  async function onLangPickerContinue() {
    if (!user?.id) {
      Alert.alert("Login required", proCopy.loginRequired, [{ text: "OK" }]);
      return;
    }

    const hasBirthPair =
      (primaryProfile?.birthData && partnerProfile?.birthData) ||
      (pendingMilan?.p1 && pendingMilan?.p2);
    if (!hasBirthPair) {
      Alert.alert("Kundli missing", proCopy.kundliMissing, [{ text: "OK" }]);
      return;
    }

    const lang = coerceProPdfLang(selectedPdfLang);
    void AsyncStorage.setItem("cosmic.milanPro.lastLang", lang);
    setLangPickerVisible(false);

    if (MILAN_PRO_CHECKOUT_CONFIG.bypassCheckoutForTesting) {
      await placeVerifiedPdfOrder();
      return;
    }

    setCheckoutLoading(true);
    try {
      const p1 = primaryProfile?.birthData && partnerProfile?.birthData
        ? { ...primaryProfile.birthData, name: primaryProfile.name }
        : (pendingMilan?.p1 ?? null);
      const p2 = primaryProfile?.birthData && partnerProfile?.birthData
        ? { ...partnerProfile.birthData, name: partnerProfile.name }
        : (pendingMilan?.p2 ?? null);
      if (!p1 || !p2) return;

      await gateCoupleReportAfterLangPick({
        user,
        product: "milan_pro",
        p1,
        p2,
        lang,
        label: "Marriage Compatibility Pro",
        amountInr: milanOrderTotalInr(priorityDelivery),
        bypassCheckout: false,
        urgent: priorityDelivery,
        onEntitled: () => {
          void placeVerifiedPdfOrder();
        },
      });
    } finally {
      setCheckoutLoading(false);
    }
  }

  const titleColor = isDark ? "#fff" : "#0F172A";
  const subColor = isDark ? "rgba(203,213,225,0.55)" : "#64748B";
  const ctaLoading = checkoutLoading || submittingOrder;

  return (
    <CosmicBg>
      <View style={[s.shell, { paddingTop: topPad + 6 }]}>
        <View style={s.headerRow}>
          <Pressable onPress={goBack} hitSlop={8}>
            <View style={[s.backCircle, {
              backgroundColor: isDark ? "rgba(255,255,255,0.08)" : "rgba(0,0,0,0.05)",
              borderColor: isDark ? "rgba(255,255,255,0.12)" : "rgba(0,0,0,0.08)",
            }]}>
              <Feather name="chevron-left" size={22} color={titleColor} />
            </View>
          </Pressable>
          <View style={{ flex: 1, alignItems: "center", paddingHorizontal: 4 }}>
            <Text style={[s.headerTitle, { color: titleColor }]} numberOfLines={1}>
              {proCopy.title}
            </Text>
            <Text style={[s.headerSub, { color: subColor }]} numberOfLines={1}>
              {proCopy.subtitle}
            </Text>
          </View>
          <View style={{ width: 40 }} />
        </View>

        <View style={{ flex: 1 }}>
          <ScrollView
            style={s.scroll}
            contentContainerStyle={{ paddingHorizontal: 16, paddingBottom: botPad + 88, gap: 12 }}
            showsVerticalScrollIndicator={false}
          >
            {!canPro && (
              <FadeInView delay={staggerDelay(0)}>
                <Pressable
                  onPress={showKundliRequired}
                  style={[s.partnerHint, { borderColor: isDark ? "rgba(167,139,250,0.35)" : "rgba(124,58,237,0.25)" }]}
                >
                  <Feather name="users" size={14} color="#a78bfa" />
                  <Text style={[s.partnerHintText, { color: isDark ? "#e9d5ff" : "#5b21b6" }]}>
                    {!partnerProfile ? proCopy.partnerMissing : proCopy.kundliMissing}
                  </Text>
                  <Feather name="chevron-right" size={14} color="#a78bfa" />
                </Pressable>
              </FadeInView>
            )}
            <FadeInView delay={staggerDelay(canPro ? 0 : 1)}>
              <MarriageCompatProPurchase
                isDark={isDark}
                primaryName={primaryProfile?.name}
                partnerName={partnerProfile?.name}
                priorityDelivery={priorityDelivery}
                onPriorityDeliveryChange={setPriorityDelivery}
                lang={displayLang}
              />
            </FadeInView>
          </ScrollView>

          <MarriageCompatProStickyCta
            isDark={isDark}
            canPro={canPro}
            loading={ctaLoading}
            regularInr={MILAN_PRO_UI_PRICING.regularInr}
            totalInr={milanOrderTotalInr(priorityDelivery)}
            onUnlock={startProUnlock}
            lang={displayLang}
          />
        </View>
      </View>

      <ProPdfLanguagePickerModal
        visible={langPickerVisible}
        selectedLang={selectedPdfLang}
        onSelectLang={setSelectedPdfLang}
        onClose={() => setLangPickerVisible(false)}
        onContinue={onLangPickerContinue}
        delivery={{
          priorityDelivery,
          onPriorityDeliveryChange: setPriorityDelivery,
        }}
      />
      <OrderSuccessModal
        visible={!!preparingBanner}
        onClose={() => setPreparingBanner(null)}
        onViewReports={() => {
          setPreparingBanner(null);
          router.push("/my-reports" as any);
        }}
        title="Order Confirmed!"
        message="Your order has been received. Our expert is personally preparing your Marriage Compatibility Pro report — it's on its way."
        etaLabel={
          preparingBanner?.priority
            ? "Report in My Reports within 12 hrs"
            : "Report in My Reports within 24 hrs"
        }
      />
    </CosmicBg>
  );
}

const s = StyleSheet.create({
  shell: { flex: 1 },
  scroll: { flex: 1 },
  headerRow: { flexDirection: "row", alignItems: "center", paddingHorizontal: 16, paddingBottom: 10, gap: 8 },
  headerTitle: { fontSize: 17, fontFamily: "Nunito_800ExtraBold", letterSpacing: -0.3 },
  headerSub: { fontSize: 11, fontFamily: "Nunito_500Medium", marginTop: 2 },
  backCircle: { width: 40, height: 40, borderRadius: 20, alignItems: "center", justifyContent: "center", borderWidth: 1 },
  partnerHint: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    padding: 12,
    borderRadius: 14,
    borderWidth: 1,
    backgroundColor: "rgba(124,58,237,0.08)",
  },
  partnerHintText: { flex: 1, fontSize: 12, fontFamily: "Nunito_600SemiBold" },
});
