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
import { LoveRealityProPurchase } from "@/components/loveReality/LoveRealityProPurchase";
import { LoveRealityProStickyCta } from "@/components/loveReality/LoveRealityProStickyCta";
import { ProPdfLanguagePickerModal } from "@/components/ProPdfLanguagePickerModal";
import { useC } from "@/context/ThemeContext";
import { useUser } from "@/context/UserContext";
import { useT } from "@/hooks/useT";
import {
  consumeCouplePaidReady,
  gateCoupleReportAfterLangPick,
} from "@/lib/coupleReportCheckoutFlow";
import { getPendingCoupleCheckout } from "@/lib/pendingCoupleCheckout";
import { submitLoveRealityHumanOrder } from "@/lib/loveRealityHumanOrder";
import {
  LOVE_REALITY_CHECKOUT_CONFIG,
  LOVE_REALITY_PRO_UI_PRICING,
  loveRealityOrderTotalInr,
  runLoveRealityProUnlockCta,
} from "@/lib/loveRealityProOffer";
import { packLovePerson } from "@/lib/loveRealityProPdfDownload";
import { coerceProPdfLang, proPdfLangDisplayName } from "@/lib/proPdfLang";
import { loveRealityProScreenCopy } from "@/lib/loveRealityProCopyI18n";

export default function LoveRealityProScreen() {
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
  const partnerProfile = partnerId ? (profiles.find(p => p.id === partnerId) ?? null) : null;

  const hasSelfKundli = !!primaryProfile?.kundli && !!primaryProfile?.birthData;
  const hasPartnerKundli = !!partnerProfile?.kundli && !!partnerProfile?.birthData;
  const canPro = hasSelfKundli && hasPartnerKundli;

  const [priorityDelivery, setPriorityDelivery] = useState(false);
  const [langPickerVisible, setLangPickerVisible] = useState(false);
  const [selectedPdfLang, setSelectedPdfLang] = useState(coerceProPdfLang(language || t.lang));
  const displayLang = coerceProPdfLang(selectedPdfLang);
  const proCopy = loveRealityProScreenCopy(displayLang);
  const [checkoutLoading, setCheckoutLoading] = useState(false);
  const [submittingOrder, setSubmittingOrder] = useState(false);

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
      pathname: "/love-reality",
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
    if (!primaryProfile?.birthData || !partnerProfile?.birthData || !user?.id) return;

    const lang = coerceProPdfLang(opts?.langOverride ?? selectedPdfLang);
    const urgent = opts?.urgentOverride ?? priorityDelivery;

    setSubmittingOrder(true);
    try {
      const p1 = packLovePerson(primaryProfile.birthData, primaryProfile.name);
      const p2 = packLovePerson(partnerProfile.birthData, partnerProfile.name);
      const result = await submitLoveRealityHumanOrder({
        p1,
        p2,
        lang,
        urgent,
        userId: user.id,
        cosmoUserId: user.cosmo_user_id,
        apiKey: user.api_key,
      });
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      const langLabel = proPdfLangDisplayName(lang);
      const etaLabel = result.eta_hours <= 24 ? "12 hours" : "24–48 hours";
      Alert.alert(
        proCopy.orderPlacedTitle,
        proCopy.orderPlacedBody(langLabel, etaLabel),
        [{ text: "OK" }],
      );
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
    runLoveRealityProUnlockCta({
      continueProExperience: () => {
        void (async () => {
          try {
            const stored = await AsyncStorage.getItem("cosmic.loveRealityPro.lastLang");
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
    if (!primaryProfile?.birthData || !partnerProfile?.birthData) return;

    if (!user?.id) {
      Alert.alert(
        "Login required",
        proCopy.loginRequired,
        [{ text: "OK" }],
      );
      return;
    }

    const lang = coerceProPdfLang(selectedPdfLang);
    void AsyncStorage.setItem("cosmic.loveRealityPro.lastLang", lang);
    setLangPickerVisible(false);

    if (LOVE_REALITY_CHECKOUT_CONFIG.bypassCheckoutForTesting) {
      await placeVerifiedPdfOrder();
      return;
    }

    setCheckoutLoading(true);
    try {
      const p1 = { ...primaryProfile.birthData, name: primaryProfile.name };
      const p2 = { ...partnerProfile.birthData, name: partnerProfile.name };

      await gateCoupleReportAfterLangPick({
        user,
        product: "love_reality_pro",
        p1,
        p2,
        lang,
        label: "Love Reality Pro",
        amountInr: loveRealityOrderTotalInr(priorityDelivery),
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
              <Pressable
                onPress={showKundliRequired}
                style={[s.partnerHint, { borderColor: isDark ? "rgba(244,114,182,0.35)" : "rgba(236,72,153,0.25)" }]}
              >
                <Feather name="users" size={14} color="#f472b6" />
                <Text style={[s.partnerHintText, { color: isDark ? "#fbcfe8" : "#9d174d" }]}>
                  {!partnerProfile
                    ? proCopy.partnerMissing
                    : proCopy.kundliMissing}
                </Text>
                <Feather name="chevron-right" size={14} color="#f472b6" />
              </Pressable>
            )}
            <LoveRealityProPurchase
              isDark={isDark}
              primaryName={primaryProfile?.name}
              partnerName={partnerProfile?.name}
              priorityDelivery={priorityDelivery}
              onPriorityDeliveryChange={setPriorityDelivery}
              lang={displayLang}
            />
          </ScrollView>

          <LoveRealityProStickyCta
            isDark={isDark}
            canPro={canPro}
            loading={ctaLoading}
            regularInr={LOVE_REALITY_PRO_UI_PRICING.regularInr}
            totalInr={loveRealityOrderTotalInr(priorityDelivery)}
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
    </CosmicBg>
  );
}

const s = StyleSheet.create({
  shell: { flex: 1 },
  scroll: { flex: 1 },
  headerRow: {
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: 16,
    paddingBottom: 10,
    gap: 8,
  },
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
    backgroundColor: "rgba(236,72,153,0.08)",
  },
  partnerHintText: { flex: 1, fontSize: 12, fontFamily: "Nunito_600SemiBold" },
});
