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
import { LoveRealityProPurchase } from "@/components/loveReality/LoveRealityProPurchase";
import { LoveRealityProStickyCta } from "@/components/loveReality/LoveRealityProStickyCta";
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
import { getPendingCoupleCheckout } from "@/lib/pendingCoupleCheckout";
import { submitLoveRealityHumanOrder } from "@/lib/loveRealityHumanOrder";
import { registerPendingMyReport } from "@/lib/registerPendingMyReport";
import { STANDARD_DELIVERY_ETA } from "@/lib/deliverySla";
import {
  LOVE_REALITY_CHECKOUT_CONFIG,
  LOVE_REALITY_PRO_UI_PRICING,
  loveRealityOrderTotalInr,
  normalizeWhatsappDigits,
  runLoveRealityProUnlockCta,
  type CoupleProDeliverable,
} from "@/lib/loveRealityProOffer";
import { packLovePerson } from "@/lib/loveRealityProPdfDownload";
import { coerceProPdfLang } from "@/lib/proPdfLang";
import { loveRealityProPurchaseCopy, loveRealityProScreenCopy } from "@/lib/loveRealityProCopyI18n";

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
  const [deliverable, setDeliverable] = useState<CoupleProDeliverable>("report");
  const [whatsapp, setWhatsapp] = useState("");
  const [whatsappError, setWhatsappError] = useState<string | null>(null);
  const [langPickerVisible, setLangPickerVisible] = useState(false);
  const [selectedPdfLang, setSelectedPdfLang] = useState(coerceProPdfLang(language || t.lang));
  const displayLang = coerceProPdfLang(selectedPdfLang);
  const proCopy = loveRealityProScreenCopy(displayLang);
  const purchaseCopy = loveRealityProPurchaseCopy(displayLang);
  /** Prefer typed WhatsApp; fall back to profile only when field is empty. */
  const waDigits = normalizeWhatsappDigits(whatsapp || user?.phone || "");
  const whatsappLocked = !!(user?.personal_phone_locked || normalizeWhatsappDigits(user?.phone || "").length === 10);

  function notify(title: string, message: string) {
    if (Platform.OS === "web" && typeof window !== "undefined") {
      window.alert(`${title}\n\n${message}`);
      return;
    }
    Alert.alert(title, message, [{ text: "OK" }]);
  }

  /** Video CTA: require a real 10-digit mobile. Returns digits or null. */
  function requireVideoMobile(): string | null {
    const typed = normalizeWhatsappDigits(whatsapp);
    const fromProfile = normalizeWhatsappDigits(user?.phone || "");
    const wa = typed.length === 10 ? typed : fromProfile.length === 10 ? fromProfile : typed || fromProfile;
    if (wa.length === 10) {
      setWhatsappError(null);
      if (typed.length !== 10 && fromProfile.length === 10) setWhatsapp(fromProfile);
      return wa;
    }
    const msg = purchaseCopy.whatsappRequired;
    setWhatsappError(msg);
    Haptics.notificationAsync(Haptics.NotificationFeedbackType.Warning);
    notify("Mobile number required", msg);
    return null;
  }
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
    deliverableOverride?: CoupleProDeliverable;
    whatsappOverride?: string;
  }) {
    if (!primaryProfile?.birthData || !partnerProfile?.birthData || !user?.id) return;

    const lang = coerceProPdfLang(opts?.langOverride ?? selectedPdfLang);
    const urgent = opts?.urgentOverride ?? priorityDelivery;
    const kind = opts?.deliverableOverride ?? deliverable;
    const wa = normalizeWhatsappDigits(opts?.whatsappOverride ?? waDigits);

    if (kind === "video" && wa.length !== 10) {
      const msg = purchaseCopy.whatsappRequired;
      setWhatsappError(msg);
      notify("Mobile number required", msg);
      return;
    }

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
        deliverable: kind,
        whatsapp: wa,
        amountInr: loveRealityOrderTotalInr(urgent, kind),
        priorityFeeInr: urgent ? 299 : 0,
      });
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      const displayOid = String(result.order_id || "").slice(0, 8).toUpperCase();
      const couple = `${(primaryProfile.name || "You").trim()} & ${(partnerProfile.name || "Partner").trim()}`;
      try {
        await registerPendingMyReport(user.id, {
          kind: "love_reality",
          title: kind === "video"
            ? `${couple} — Video (WhatsApp)`
            : `${couple} — Love Reality Report`,
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
    if (deliverable === "video" && !requireVideoMobile()) {
      return;
    }
    setWhatsappError(null);
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
      notify("Login required", proCopy.loginRequired);
      return;
    }

    let videoWa: string | undefined;
    if (deliverable === "video") {
      const wa = requireVideoMobile();
      if (!wa) {
        setLangPickerVisible(false);
        return;
      }
      videoWa = wa;
    }

    const lang = coerceProPdfLang(selectedPdfLang);
    void AsyncStorage.setItem("cosmic.loveRealityPro.lastLang", lang);
    setLangPickerVisible(false);

    if (LOVE_REALITY_CHECKOUT_CONFIG.bypassCheckoutForTesting) {
      await placeVerifiedPdfOrder({
        whatsappOverride: videoWa,
        deliverableOverride: deliverable,
      });
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
        label: deliverable === "video" ? "Personalized Video Explanation" : "Love Reality Pro Report",
        amountInr: loveRealityOrderTotalInr(priorityDelivery, deliverable),
        bypassCheckout: false,
        urgent: priorityDelivery,
        contactMethod: deliverable === "video" ? "whatsapp" : undefined,
        contactValue: deliverable === "video" ? videoWa : undefined,
        onEntitled: () => {
          void placeVerifiedPdfOrder({
            whatsappOverride: videoWa,
            deliverableOverride: deliverable,
          });
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
              </FadeInView>
            )}
            <FadeInView delay={staggerDelay(canPro ? 0 : 1)}>
              <LoveRealityProPurchase
                isDark={isDark}
                primaryName={primaryProfile?.name}
                partnerName={partnerProfile?.name}
                priorityDelivery={priorityDelivery}
                onPriorityDeliveryChange={setPriorityDelivery}
                deliverable={deliverable}
                onDeliverableChange={(id) => {
                  setDeliverable(id);
                  setWhatsappError(null);
                }}
                whatsapp={whatsapp}
                onWhatsappChange={(t) => {
                  setWhatsapp(t);
                  if (whatsappError) setWhatsappError(null);
                }}
                whatsappLocked={whatsappLocked}
                whatsappError={whatsappError}
                lang={displayLang}
              />
            </FadeInView>
          </ScrollView>

          <LoveRealityProStickyCta
            isDark={isDark}
            canPro={canPro}
            loading={ctaLoading}
            regularInr={LOVE_REALITY_PRO_UI_PRICING.regularInr}
            totalInr={loveRealityOrderTotalInr(priorityDelivery, deliverable)}
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
            : "Your order has been received. Our expert is personally preparing your Love Reality Pro report — it's on its way."
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
