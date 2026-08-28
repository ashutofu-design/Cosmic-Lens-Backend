import { Feather } from "@expo/vector-icons";
import * as Haptics from "expo-haptics";
import { router, useFocusEffect, useLocalSearchParams } from "expo-router";
import React, { useCallback, useEffect, useState } from "react";
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
import { registerPendingMyReport } from "@/lib/registerPendingMyReport";
import { STANDARD_DELIVERY_ETA } from "@/lib/deliverySla";
import { milanProPurchaseCopy, milanProScreenCopy } from "@/lib/milanProCopyI18n";
import {
  MILAN_PRO_CHECKOUT_CONFIG,
  MILAN_PRO_UI_PRICING,
  milanOrderTotalInr,
  runMilanProUnlockCta,
  type MilanProDeliverable,
} from "@/lib/milanProOffer";
import { normalizeWhatsappDigits } from "@/lib/loveRealityProOffer";
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
  const [deliverable, setDeliverable] = useState<MilanProDeliverable>("report");
  const [whatsapp, setWhatsapp] = useState("");
  const [langPickerVisible, setLangPickerVisible] = useState(false);
  const [selectedPdfLang, setSelectedPdfLang] = useState(coerceProPdfLang(language || t.lang));
  const displayLang = coerceProPdfLang(selectedPdfLang);
  const proCopy = milanProScreenCopy(displayLang);
  const purchaseCopy = milanProPurchaseCopy(displayLang);
  const waDigits = normalizeWhatsappDigits(whatsapp || user?.phone || "");
  const whatsappLocked = !!(user?.personal_phone_locked || normalizeWhatsappDigits(user?.phone || "").length === 10);
  const [checkoutLoading, setCheckoutLoading] = useState(false);
  const [submittingOrder, setSubmittingOrder] = useState(false);
  const [preparingBanner, setPreparingBanner] = useState<{
    priority: boolean;
    etaHours: number;
  } | null>(null);

  useEffect(() => {
    const fromProfile = normalizeWhatsappDigits(user?.phone || "");
    if (fromProfile.length === 10) setWhatsapp(fromProfile);
  }, [user?.phone]);

  useFocusEffect(
    useCallback(() => {
      if (consumeCouplePaidReady()) {
        const pending = getPendingCoupleCheckout();
        if (pending?.lang) setSelectedPdfLang(coerceProPdfLang(pending.lang));
        if (pending?.urgent != null) setPriorityDelivery(pending.urgent);
        if (pending?.contactMethod === "whatsapp") {
          setDeliverable("video");
          if (pending.contactValue) setWhatsapp(normalizeWhatsappDigits(pending.contactValue));
        }
        void placeVerifiedPdfOrder({
          langOverride: pending?.lang,
          urgentOverride: pending?.urgent,
          deliverableOverride: pending?.contactMethod === "whatsapp" ? "video" : "report",
          whatsappOverride: pending?.contactValue,
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
    deliverableOverride?: MilanProDeliverable;
    whatsappOverride?: string;
  }) {
    if (!user?.id) {
      Alert.alert("Login required", proCopy.loginRequired, [{ text: "OK" }]);
      return;
    }

    const lang = coerceProPdfLang(opts?.langOverride ?? selectedPdfLang);
    const urgent = opts?.urgentOverride ?? priorityDelivery;
    const kind = opts?.deliverableOverride ?? deliverable;
    const wa = normalizeWhatsappDigits(opts?.whatsappOverride ?? waDigits);

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
        deliverable: kind,
        whatsapp: wa,
        amountInr: milanOrderTotalInr(urgent, kind),
        priorityFeeInr: urgent ? 299 : 0,
      });
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      const displayOid = String(result.order_id || "").slice(0, 8).toUpperCase();
      const n1 = (primaryProfile?.name || p1?.name || "You").toString().trim() || "You";
      const n2 = (partnerProfile?.name || p2?.name || "Partner").toString().trim() || "Partner";
      const couple = `${n1} & ${n2}`;
      try {
        await registerPendingMyReport(user.id, {
          kind: "milan",
          title: kind === "video"
            ? `${couple} — Video (WhatsApp)`
            : `${couple} — Kundli Milan Report`,
          subtitle: displayOid ? `Order ${displayOid}` : "Preparing…",
          orderId: result.order_id || undefined,
          publicOrderId: displayOid || undefined,
          etaLabel: urgent
            ? "⚡ Priority — within 12 hours"
            : `📦 Standard — ${STANDARD_DELIVERY_ETA}`,
          deliverable: kind,
        });
      } catch {
        /* ignore */
      }
      setPreparingBanner({
        priority: urgent,
        etaHours: Number(result.eta_hours) || (urgent ? 12 : 144),
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
    if (deliverable === "video" && waDigits.length !== 10) {
      Alert.alert("WhatsApp number", purchaseCopy.whatsappRequired, [{ text: "OK" }]);
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
        label: deliverable === "video" ? "Personalized Video Explanation" : "Kundli Milan Pro Report",
        amountInr: milanOrderTotalInr(priorityDelivery, deliverable),
        bypassCheckout: false,
        urgent: priorityDelivery,
        contactMethod: deliverable === "video" ? "whatsapp" : undefined,
        contactValue: deliverable === "video" ? waDigits : undefined,
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

        <View style={{ flex: 1, minHeight: 0 }}>
          <ScrollView
            style={s.scroll}
            contentContainerStyle={{ paddingHorizontal: 16, paddingBottom: botPad + 88, gap: 12, flexGrow: 1 }}
            showsVerticalScrollIndicator={false}
            nestedScrollEnabled
            keyboardShouldPersistTaps="handled"
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
                deliverable={deliverable}
                onDeliverableChange={setDeliverable}
                whatsapp={whatsapp}
                onWhatsappChange={setWhatsapp}
                whatsappLocked={whatsappLocked}
                lang={displayLang}
              />
            </FadeInView>
          </ScrollView>

          <MarriageCompatProStickyCta
            isDark={isDark}
            canPro={canPro}
            loading={ctaLoading}
            regularInr={MILAN_PRO_UI_PRICING.regularInr}
            totalInr={milanOrderTotalInr(priorityDelivery, deliverable)}
            onUnlock={startProUnlock}
            lang={displayLang}
            isVideo={deliverable === "video"}
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
        message={
          deliverable === "video"
            ? "Your Personalized Video Explanation is being prepared. It will be sent to your WhatsApp. No PDF/report is included."
            : "Your order has been received. Our expert is personally preparing your Marriage Compatibility Pro report — it's on its way."
        }
        etaLabel={
          deliverable === "video"
            ? preparingBanner?.priority
              ? "Video on WhatsApp within 12 hrs"
              : "Video on WhatsApp within 24 hrs"
            : preparingBanner?.priority
              ? "Report in My Reports within 12 hrs"
              : "Report in My Reports within 24 hrs"
        }
      />
    </CosmicBg>
  );
}

const s = StyleSheet.create({
  shell: { flex: 1, minHeight: 0 },
  scroll: { flex: 1, minHeight: 0 },
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
