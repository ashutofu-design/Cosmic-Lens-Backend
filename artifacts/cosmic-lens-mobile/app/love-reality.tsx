import { Feather } from "@expo/vector-icons";
import { BlurView } from "expo-blur";
import * as Haptics from "expo-haptics";
import { LinearGradient } from "expo-linear-gradient";
import { router, useFocusEffect, useLocalSearchParams } from "expo-router";
import React, { useCallback, useEffect, useRef, useState } from "react";
import {
  ActivityIndicator,
  Alert,
  Animated,
  Easing,
  Modal,
  Platform,
  Pressable,
  ScrollView,
  StatusBar,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { CosmicBg } from "@/components/CosmicBg";
import { LoveRealityUnifiedBasic } from "@/components/loveReality/LoveRealityUnifiedBasic";
import { ProPdfLanguagePickerModal } from "@/components/ProPdfLanguagePickerModal";
import { useC } from "@/context/ThemeContext";
import { useUser } from "@/context/UserContext";
import { useT } from "@/hooks/useT";
import {
  consumeCouplePaidReady,
  gateCoupleReportAfterLangPick,
} from "@/lib/coupleReportCheckoutFlow";
import { getPendingCoupleCheckout } from "@/lib/pendingCoupleCheckout";
import { checkCoupleReportEntitlement } from "@/lib/coupleReportBilling";
import {
  downloadLoveRealityProPdf,
  packLovePerson,
} from "@/lib/loveRealityProPdfDownload";
import {
  LOVE_REALITY_CHECKOUT_CONFIG,
  LOVE_REALITY_PRO_UI_PRICING,
  runLoveRealityProUnlockCta,
} from "@/lib/loveRealityProOffer";
import AsyncStorage from "@react-native-async-storage/async-storage";
import { coerceProPdfLang } from "@/lib/proPdfLang";
import {
  LOVE_PRO_UNLOCK_ITEMS,
  LOVE_REALITY_PRO_BENEFIT,
  LOVE_REALITY_PRO_CTA_TITLE,
  LOVE_REALITY_PRO_FOOTNOTE,
  LOVE_REALITY_PRO_SECTION_LABEL,
  LOVE_REALITY_PRO_SUBTITLE,
} from "@/lib/loveRealityProCopy";

const PRO_CHIPS = ["6 tools · Full report", "English · Hinglish · Hindi"];

function LoveRealityProUnlockList({ isDark }: { isDark: boolean }) {
  const titleColor = isDark ? "#f5e6c8" : "#1e293b";
  const hookColor = isDark ? "rgba(226,232,240,0.65)" : "#64748B";
  const borderColor = isDark ? "rgba(255,255,255,0.08)" : "rgba(0,0,0,0.06)";

  return (
    <View style={s.unlockWrap}>
      <View style={s.unlockHead}>
        <Feather name="unlock" size={13} color={isDark ? "#f472b6" : "#db2777"} />
        <Text style={[s.unlockHeadTxt, { color: isDark ? "#f472b6" : "#db2777" }]}>
          {LOVE_REALITY_PRO_SECTION_LABEL}
        </Text>
      </View>
      <View style={{ gap: 8 }}>
        {LOVE_PRO_UNLOCK_ITEMS.map(sec => (
          <View key={sec.title} style={[s.unlockRow, { borderColor }]}>
            <Text style={s.unlockEmoji}>{sec.emoji}</Text>
            <View style={{ flex: 1, gap: 5 }}>
              <Text style={[s.unlockTitle, { color: titleColor }]}>{sec.title}</Text>
              <Text style={[s.unlockHook, { color: hookColor }]}>{sec.shortHook}</Text>
            </View>
          </View>
        ))}
      </View>
    </View>
  );
}

function LoveRealityProPanel({
  isDark,
  canPro,
  pdfLoading,
  onUnlock,
}: {
  isDark: boolean;
  canPro: boolean;
  pdfLoading: boolean;
  onUnlock: () => void;
}) {
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const slideAnim = useRef(new Animated.Value(20)).current;
  const glowAnim = useRef(new Animated.Value(0.2)).current;

  useEffect(() => {
    Animated.parallel([
      Animated.timing(fadeAnim, { toValue: 1, duration: 600, delay: 120, useNativeDriver: true }),
      Animated.spring(slideAnim, { toValue: 0, delay: 120, useNativeDriver: true, speed: 12, bounciness: 5 }),
    ]).start();
    const glow = Animated.loop(
      Animated.sequence([
        Animated.timing(glowAnim, { toValue: 0.55, duration: 2800, easing: Easing.inOut(Easing.sin), useNativeDriver: true }),
        Animated.timing(glowAnim, { toValue: 0.2, duration: 2800, easing: Easing.inOut(Easing.sin), useNativeDriver: true }),
      ]),
    );
    glow.start();
    return () => { glow.stop(); };
  }, []);

  const { originalInr, offerInr, discountLabel } = LOVE_REALITY_PRO_UI_PRICING;

  return (
    <Animated.View style={{ opacity: fadeAnim, transform: [{ translateY: slideAnim }] }}>
        <View style={[s.proCard, {
          shadowColor: "#a855f7",
          shadowOpacity: isDark ? 0.45 : 0.2,
          shadowRadius: 24,
          shadowOffset: { width: 0, height: 8 },
          elevation: 12,
        }]}>
          <LinearGradient
            colors={["#1a0a2e", "#111827", "#150a20"]}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 1 }}
            style={[StyleSheet.absoluteFill, { borderRadius: 26 }]}
          />
          <Animated.View style={[StyleSheet.absoluteFill, { borderRadius: 26, opacity: glowAnim, overflow: "hidden" }]}>
            <LinearGradient
              colors={["rgba(168,85,247,0.22)", "rgba(236,72,153,0.12)", "transparent"]}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 1 }}
              style={StyleSheet.absoluteFill}
            />
          </Animated.View>
          <View style={[StyleSheet.absoluteFill, { borderRadius: 26, borderWidth: 1, borderColor: "rgba(168,85,247,0.35)" }]} />

          <View style={s.proContent}>
            <LinearGradient colors={["#9333ea", "#ec4899"]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={s.proEmojiCircle}>
              <Text style={{ fontSize: 26 }}>💞</Text>
            </LinearGradient>

            <View style={{ flex: 1, gap: 4 }}>
              <Text style={s.proTitle}>Love Reality Pro Report</Text>
              <Text style={s.proBenefit}>{LOVE_REALITY_PRO_BENEFIT}</Text>
              <Text style={s.proSub}>{LOVE_REALITY_PRO_SUBTITLE}</Text>
            </View>
          </View>

          <View style={s.proChipsRow}>
            {PRO_CHIPS.map(chip => (
              <View key={chip} style={s.proChip}>
                <Text style={s.proChipText}>{chip}</Text>
              </View>
            ))}
          </View>

          <View style={s.proPriceRow}>
            <Text style={s.proStrike}>₹{originalInr}</Text>
            <Text style={s.proOffer}>₹{offerInr}</Text>
            <View style={s.proOffPill}>
              <Text style={s.proOffText}>{discountLabel}</Text>
            </View>
          </View>

          <Pressable
            onPress={onUnlock}
            disabled={pdfLoading || !canPro}
            style={({ pressed }) => ({
              opacity: !canPro ? 0.55 : pressed ? 0.88 : 1,
              marginTop: 4,
              borderRadius: 14,
              overflow: "hidden",
            })}
          >
            <LinearGradient
              colors={canPro ? ["#9333ea", "#ec4899", "#f59e0b"] : ["#4b5563", "#374151"]}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 0 }}
              style={s.proCtaGrad}
            >
              {pdfLoading ? (
                <ActivityIndicator color="#fff" />
              ) : (
                <View style={s.proCtaInner}>
                  <Feather name="file-text" size={16} color="#fff" />
                  <View style={{ flex: 1, alignItems: "center" }}>
                    <Text style={s.proCtaText}>
                      {canPro ? LOVE_REALITY_PRO_CTA_TITLE : "Add partner kundli to unlock"}
                    </Text>
                    {canPro ? (
                      <Text style={s.proCtaPrice}>Only ₹{offerInr} · {discountLabel}</Text>
                    ) : null}
                  </View>
                </View>
              )}
            </LinearGradient>
          </Pressable>

          <View style={s.proFoot}>
            <Feather name="zap" size={11} color="#c084fc" />
            <Text style={s.proFootText}>{LOVE_REALITY_PRO_FOOTNOTE}</Text>
          </View>
        </View>
    </Animated.View>
  );
}

export default function LoveRealityScreen() {
  const C = useC();
  const t = useT();
  const { user, profiles, primaryProfileId } = useUser();
  const params = useLocalSearchParams<{ partnerId?: string; openPro?: string; tool?: string }>();
  const partnerId = typeof params.partnerId === "string" ? params.partnerId : null;
  const initialToolKey = typeof params.tool === "string" ? params.tool : undefined;
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

  const [plan, setPlan] = useState<"basic" | "pro">(
    params.openPro === "1" ? "pro" : "basic",
  );
  const isPro = plan === "pro";

  useEffect(() => {
    if (params.openPro === "1") setPlan("pro");
  }, [params.openPro]);

  const [langPickerVisible, setLangPickerVisible] = useState(false);
  const [confirmVisible, setConfirmVisible] = useState(false);
  const [pdfLoading, setPdfLoading] = useState(false);
  const [progressVisible, setProgressVisible] = useState(false);
  const [selectedPdfLang, setSelectedPdfLang] = useState(coerceProPdfLang(t.lang));
  const [pdfPct, setPdfPct] = useState(0);
  const pdfSuccessRef = useRef(false);
  const pdfFastProgressRef = useRef(false);
  const spinAnim = useRef(new Animated.Value(0)).current;
  const barAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.timing(barAnim, {
      toValue: pdfPct / 100,
      duration: 350,
      easing: Easing.out(Easing.cubic),
      useNativeDriver: false,
    }).start();
  }, [pdfPct, barAnim]);

  useEffect(() => {
    if (!pdfLoading) return;
    spinAnim.setValue(0);
    const spin = Animated.loop(
      Animated.timing(spinAnim, {
        toValue: 1,
        duration: 1200,
        easing: Easing.linear,
        useNativeDriver: true,
      }),
    );
    spin.start();
    return () => spin.stop();
  }, [pdfLoading, spinAnim]);

  useEffect(() => {
    if (!pdfLoading) return;
    setProgressVisible(true);
    setPdfPct(0);
    barAnim.setValue(0);
    const fast = pdfFastProgressRef.current;
    const tickMs = fast ? 100 : 700;
    const step = fast ? 6 : 1;
    const id = setInterval(() => {
      setPdfPct((p) => (p >= 90 ? 90 : Math.min(90, p + step)));
    }, tickMs);
    return () => clearInterval(id);
  }, [pdfLoading]);

  useEffect(() => {
    if (pdfLoading || !progressVisible || !pdfSuccessRef.current) return;
    setPdfPct(100);
  }, [pdfLoading, progressVisible]);

  useEffect(() => {
    if (!progressVisible || pdfLoading || pdfPct < 100) return;
    const timer = setTimeout(() => {
      setProgressVisible(false);
      setPdfPct(0);
      barAnim.setValue(0);
      pdfSuccessRef.current = false;
      router.push("/my-reports" as never);
    }, 700);
    return () => clearTimeout(timer);
  }, [progressVisible, pdfLoading, pdfPct]);

  useFocusEffect(
    useCallback(() => {
      if (consumeCouplePaidReady()) {
        const pending = getPendingCoupleCheckout();
        if (pending?.lang) setSelectedPdfLang(coerceProPdfLang(pending.lang));
        openProReport(pending?.lang);
      }
    }, []),
  );

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

  function openProReport(langOverride?: string) {
    const lang = coerceProPdfLang(langOverride ?? selectedPdfLang);
    void AsyncStorage.setItem("cosmic.loveRealityPro.lastLang", lang);
    router.push({
      pathname: "/love-reality-pro-report",
      params: {
        partnerId: partnerId ?? "",
        lang,
      },
    } as never);
  }

  function startProUnlock() {
    if (!canPro) {
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Warning);
      showKundliRequired();
      return;
    }
    runLoveRealityProUnlockCta({
      continueProExperience: () => {
        setSelectedPdfLang(coerceProPdfLang(t.lang));
        setLangPickerVisible(true);
      },
    });
  }

  async function onLangPickerContinue() {
    setLangPickerVisible(false);
    if (!primaryProfile?.birthData || !partnerProfile?.birthData) return;

    if (!user?.id) {
      Alert.alert(
        "Login required",
        "Please sign in to read your Love Reality Pro report.",
        [{ text: "OK" }],
      );
      return;
    }

    if (LOVE_REALITY_CHECKOUT_CONFIG.bypassCheckoutForTesting) {
      openProReport();
      return;
    }

    const p1 = { ...primaryProfile.birthData, name: primaryProfile.name };
    const p2 = { ...partnerProfile.birthData, name: partnerProfile.name };
    const lang = coerceProPdfLang(selectedPdfLang);

    await gateCoupleReportAfterLangPick({
      user,
      product: "love_reality_pro",
      p1,
      p2,
      lang,
      label: "Love Reality Pro",
      amountInr: LOVE_REALITY_PRO_UI_PRICING.offerInr,
      bypassCheckout: false,
      onEntitled: () => openProReport(),
    });
  }

  async function handleDownloadProPdf() {
    if (!primaryProfile?.birthData || !partnerProfile?.birthData || !user?.id) return;
    setConfirmVisible(false);

    const lang = coerceProPdfLang(selectedPdfLang);
    let serverHasSavedCopy = false;
    if (user.api_key) {
      try {
        const check = await checkCoupleReportEntitlement(
          user,
          "love_reality_pro",
          packLovePerson(primaryProfile.birthData, primaryProfile.name),
          packLovePerson(partnerProfile.birthData, partnerProfile.name),
          lang,
        );
        serverHasSavedCopy = check.cache_hit;
      } catch {
        /* proceed — download will miss cache if unavailable */
      }
    }

    pdfFastProgressRef.current = serverHasSavedCopy || false;
    pdfSuccessRef.current = false;
    setPdfPct(0);
    barAnim.setValue(0);
    setProgressVisible(true);
    setPdfLoading(true);
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);

    try {
      const result = await downloadLoveRealityProPdf({
        user,
        p1: primaryProfile.birthData,
        p2: partnerProfile.birthData,
        p1Name: primaryProfile.name || "You",
        p2Name: partnerProfile.name || "Partner",
        lang: selectedPdfLang,
      });
      if (result.reportCacheHit) {
        pdfFastProgressRef.current = true;
      }
      pdfSuccessRef.current = true;
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
    } catch (e: unknown) {
      pdfSuccessRef.current = false;
      const msg = e instanceof Error ? e.message : "PDF download failed";
      setProgressVisible(false);
      setPdfPct(0);
      barAnim.setValue(0);
      Alert.alert("PDF Error", msg, [{ text: "OK" }]);
    } finally {
      setPdfLoading(false);
    }
  }

  const headerBlock = (
    <>
      <View style={s.headerRow}>
        <Pressable
          onPress={() => { Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light); router.back(); }}
          hitSlop={8}
        >
          <View style={[s.backCircle, {
            backgroundColor: isDark ? "rgba(255,255,255,0.08)" : "rgba(0,0,0,0.05)",
            borderColor: isDark ? "rgba(255,255,255,0.12)" : "rgba(0,0,0,0.08)",
          }]}>
            <Feather name="chevron-left" size={22} color={isDark ? "#fff" : "#0F172A"} />
          </View>
        </Pressable>
        <View style={{ flex: 1, alignItems: "center", paddingHorizontal: 4 }}>
          <Text style={[s.headerTitle, { color: isDark ? "#fff" : "#0F172A" }]} numberOfLines={1}>
            {t.rl_loveTitle}
          </Text>
          <Text style={[s.headerSub, { color: isDark ? "rgba(203,213,225,0.5)" : "#64748B" }]} numberOfLines={2}>
            {t.rl_loveSub}
          </Text>
        </View>
        <View style={{ width: 40 }} />
      </View>

      <View style={s.segRow}>
        <View style={[s.segWrap, { backgroundColor: isDark ? "rgba(255,255,255,0.07)" : "rgba(0,0,0,0.05)" }]}>
          <Pressable
            onPress={() => { setPlan("basic"); Haptics.selectionAsync(); }}
            style={[s.segBtn, plan === "basic" && { backgroundColor: isDark ? "#1e2744" : "#ec4899" }]}
          >
            <Text style={[s.segTxt, { color: plan === "basic" ? "#fff" : isDark ? "rgba(255,255,255,0.4)" : "rgba(0,0,0,0.4)" }]}>
              {t.km_basic}
            </Text>
          </Pressable>
          <Pressable
            onPress={() => { setPlan("pro"); Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium); }}
            style={[s.segBtn, { overflow: "hidden" }]}
          >
            <LinearGradient
              colors={plan === "pro" ? ["#9333ea", "#ec4899"] : ["#5b21b6", "#9d174d"]}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 0 }}
              style={[StyleSheet.absoluteFillObject, { borderRadius: 14 }]}
            />
            <Text style={[s.segTxt, { color: "#fff" }]}>✨ Pro</Text>
          </Pressable>
        </View>
      </View>

      {partnerProfile && (
        <View style={[s.partnerPill, {
          borderColor: isDark ? "rgba(236,72,153,0.35)" : "rgba(236,72,153,0.25)",
        }]}>
          <LinearGradient
            colors={isDark ? ["rgba(236,72,153,0.14)", "rgba(168,85,247,0.08)"] : ["rgba(236,72,153,0.08)", "rgba(168,85,247,0.05)"]}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 0 }}
            style={StyleSheet.absoluteFill}
          />
          <Feather name="heart" size={12} color="#f472b6" />
          <Text style={[s.partnerPillTxt, { color: isDark ? "#fbcfe8" : "#9d174d" }]} numberOfLines={1}>
            Checking with {partnerProfile.name}
          </Text>
          <Pressable onPress={() => router.push("/relationship" as never)} hitSlop={8}>
            <Feather name="edit-2" size={12} color={isDark ? "#f472b6" : "#db2777"} />
          </Pressable>
        </View>
      )}
    </>
  );

  return (
    <CosmicBg>
      <View style={[s.shell, { paddingTop: topPad + 6 }]}>
        {headerBlock}

        {!isPro ? (
          <LoveRealityUnifiedBasic
            isDark={isDark}
            bottomPad={botPad}
            primaryProfile={primaryProfile?.birthData ? { name: primaryProfile.name, birthData: primaryProfile.birthData } : null}
            partnerProfile={partnerProfile?.birthData ? { name: partnerProfile.name, birthData: partnerProfile.birthData } : null}
            initialToolKey={initialToolKey}
            onOpenPro={() => { setPlan("pro"); Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium); }}
          />
        ) : (
          <ScrollView
            style={s.root}
            contentContainerStyle={{ paddingHorizontal: 16, paddingBottom: botPad + 24, gap: 16 }}
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
                    ? "Select partner on Relationship screen for Pro PDF"
                    : "Complete both kundlis to unlock Pro PDF"}
                </Text>
                <Feather name="chevron-right" size={14} color="#f472b6" />
              </Pressable>
            )}
            <LoveRealityProPanel
              isDark={isDark}
              canPro={canPro}
              pdfLoading={pdfLoading}
              onUnlock={startProUnlock}
            />
            <LoveRealityProUnlockList isDark={isDark} />
          </ScrollView>
        )}
      </View>

      <ProPdfLanguagePickerModal
        visible={langPickerVisible}
        selectedLang={selectedPdfLang}
        onSelectLang={setSelectedPdfLang}
        onClose={() => setLangPickerVisible(false)}
        onContinue={onLangPickerContinue}
        title="Report Language"
        subtitle="Full Love Reality Pro report — English, Hinglish, or Hindi."
      />

      <Modal visible={confirmVisible} transparent animationType="fade" onRequestClose={() => setConfirmVisible(false)}>
        <Pressable style={cd.backdrop} onPress={() => setConfirmVisible(false)}>
          {Platform.OS !== "web" ? (
            <BlurView intensity={Platform.OS === "ios" ? 30 : 80} tint="dark" style={StyleSheet.absoluteFillObject} />
          ) : (
            <View style={[StyleSheet.absoluteFillObject, { backgroundColor: "rgba(0,0,0,0.6)" }]} />
          )}
          <Pressable style={cd.cardWrap} onPress={e => e.stopPropagation?.()}>
            <LinearGradient colors={["#8B5CF6", "#EC4899", "#F59E0B"]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={cd.borderGradient}>
              <View style={[cd.card, { backgroundColor: isDark ? "#0F0A1F" : "#FFFFFF" }]}>
                <Text style={[cd.title, { color: C.text }]}>Confirm Details</Text>
                <Text style={[cd.sub, { color: C.textDim }]}>
                  Verify both partners before generating Love Reality Pro PDF
                </Text>
                <View style={{ gap: 10, marginVertical: 14 }}>
                  <Text style={{ color: C.text, fontFamily: "Nunito_700Bold" }}>
                    👤 {primaryProfile?.name || "You"}
                  </Text>
                  <Text style={{ color: C.textDim, fontSize: 12 }}>
                    💑 {partnerProfile?.name || "Partner"}
                  </Text>
                  <Text style={{ color: "#a855f7", fontFamily: "Nunito_800ExtraBold", fontSize: 15 }}>
                    ₹{LOVE_REALITY_PRO_UI_PRICING.offerInr} · {LOVE_REALITY_PRO_UI_PRICING.discountLabel}
                  </Text>
                </View>
                <View style={cd.actions}>
                  <Pressable onPress={() => setConfirmVisible(false)} style={[cd.changeBtn, { borderColor: C.border }]}>
                    <Text style={{ color: C.text, fontFamily: "Nunito_700Bold" }}>Change</Text>
                  </Pressable>
                  <Pressable onPress={handleDownloadProPdf} style={cd.continueBtn}>
                    <LinearGradient colors={["#9333ea", "#ec4899"]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }} style={cd.continueGrad}>
                      <Text style={cd.continueTxt}>Generate PDF</Text>
                    </LinearGradient>
                  </Pressable>
                </View>
              </View>
            </LinearGradient>
          </Pressable>
        </Pressable>
      </Modal>

      <Modal visible={progressVisible} transparent animationType="fade" onRequestClose={() => {}}>
        <View style={cd.backdrop}>
          {Platform.OS !== "web" ? (
            <BlurView intensity={Platform.OS === "ios" ? 35 : 90} tint="dark" style={StyleSheet.absoluteFillObject} />
          ) : (
            <View style={[StyleSheet.absoluteFillObject, { backgroundColor: "rgba(0,0,0,0.75)" }]} />
          )}
          <View style={cd.cardWrap}>
            <LinearGradient colors={["#9333ea", "#ec4899", "#f59e0b"]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={cd.borderGradient}>
              <View style={[cd.card, { backgroundColor: isDark ? "#0F0A1F" : "#FFFFFF" }]}>
                <View style={cd.progHeader}>
                  {!pdfLoading ? (
                    <LinearGradient colors={["#10B981", "#059669"]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={cd.progIconCircle}>
                      <Feather name="check" size={32} color="#fff" />
                    </LinearGradient>
                  ) : (
                    <LinearGradient colors={["#9333ea", "#ec4899"]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={cd.progIconCircle}>
                      <Animated.View
                        style={{
                          transform: [{
                            rotate: spinAnim.interpolate({
                              inputRange: [0, 1],
                              outputRange: ["0deg", "360deg"],
                            }),
                          }],
                        }}
                      >
                        <Feather name="loader" size={28} color="#fff" />
                      </Animated.View>
                    </LinearGradient>
                  )}
                  <Text style={[cd.progTitle, { color: C.text }]}>
                    {pdfLoading ? "Your report is processing" : "Opening My Reports…"}
                  </Text>
                </View>

                <View style={[cd.progTrack, { backgroundColor: isDark ? "rgba(255,255,255,0.06)" : "#F3F4F6" }]}>
                  <Animated.View
                    style={[
                      cd.progFillWrap,
                      {
                        width: barAnim.interpolate({
                          inputRange: [0, 1],
                          outputRange: ["0%", "100%"],
                        }),
                      },
                    ]}
                  >
                    <LinearGradient
                      colors={["#9333ea", "#ec4899", "#f59e0b"]}
                      start={{ x: 0, y: 0 }}
                      end={{ x: 1, y: 0 }}
                      style={cd.progFill}
                    />
                  </Animated.View>
                </View>

                <View style={cd.progBottom}>
                  <Text style={[cd.progPct, { color: C.text }]}>{pdfPct}%</Text>
                </View>
              </View>
            </LinearGradient>
          </View>
        </View>
      </Modal>
    </CosmicBg>
  );
}

const cd = StyleSheet.create({
  backdrop: { flex: 1, alignItems: "center", justifyContent: "center", padding: 20 },
  cardWrap: { width: "100%", maxWidth: 400 },
  borderGradient: { borderRadius: 22, padding: 1.5 },
  card: { borderRadius: 20, padding: 20 },
  title: { fontSize: 18, fontFamily: "Nunito_700Bold", textAlign: "center" },
  sub: { fontSize: 12, fontFamily: "Nunito_400Regular", textAlign: "center", marginTop: 6 },
  actions: { flexDirection: "row", gap: 10 },
  changeBtn: {
    flex: 1,
    height: 46,
    borderRadius: 12,
    borderWidth: 1,
    alignItems: "center",
    justifyContent: "center",
  },
  continueBtn: { flex: 1.4, height: 46, borderRadius: 12, overflow: "hidden" },
  continueGrad: { flex: 1, alignItems: "center", justifyContent: "center", paddingVertical: 12 },
  continueTxt: { color: "#fff", fontFamily: "Nunito_700Bold", fontSize: 14 },
  progHeader: { alignItems: "center", marginBottom: 22 },
  progIconCircle: { width: 64, height: 64, borderRadius: 32, alignItems: "center", justifyContent: "center", marginBottom: 14 },
  progTitle: { fontSize: 19, fontFamily: "Nunito_700Bold", letterSpacing: -0.3, marginBottom: 6 },
  progSub: { fontSize: 13, fontFamily: "Nunito_500Medium", textAlign: "center", lineHeight: 18, paddingHorizontal: 4, minHeight: 36 },
  progTrack: { height: 10, borderRadius: 5, overflow: "hidden", width: "100%", marginTop: 4 },
  progFillWrap: { height: 10, borderRadius: 5, overflow: "hidden", minWidth: 0 },
  progFill: { width: "100%", height: 10, borderRadius: 5 },
  progBottom: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", marginTop: 10, marginBottom: 18 },
  progPct: { fontSize: 22, fontFamily: "Nunito_700Bold", letterSpacing: -0.5 },
  progTip: { flexDirection: "row", alignItems: "center", gap: 5, flex: 1, justifyContent: "flex-end" },
  progTipTxt: { fontSize: 10.5, fontFamily: "Nunito_500Medium" },
  stageList: { gap: 10, paddingTop: 14, borderTopWidth: 1 },
  stageRow: { flexDirection: "row", alignItems: "center", gap: 10 },
  stageDot: { width: 22, height: 22, borderRadius: 11, alignItems: "center", justifyContent: "center" },
  stageTxt: { fontSize: 13, fontFamily: "Nunito_500Medium", flex: 1 },
});

const s = StyleSheet.create({
  root: { flex: 1 },
  shell: { flex: 1 },
  basicFrame: { flex: 1, minHeight: 0 },
  headerRow: {
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: 16,
    paddingBottom: 6,
    gap: 8,
  },
  headerTitle: { fontSize: 17, fontFamily: "Nunito_700Bold", letterSpacing: -0.3, textAlign: "center" },
  headerSub: { fontSize: 11, fontFamily: "Nunito_400Regular", textAlign: "center", marginTop: 2, lineHeight: 15 },
  backCircle: { width: 40, height: 40, borderRadius: 20, alignItems: "center", justifyContent: "center", borderWidth: 1 },
  partnerPillTxt: { flex: 1, fontSize: 12, fontFamily: "Nunito_600SemiBold" },

  segRow: { alignItems: "center", marginBottom: 10, paddingHorizontal: 16 },
  segWrap: { flexDirection: "row", borderRadius: 18, padding: 3, gap: 3, width: 220 },
  segBtn: { flex: 1, height: 36, borderRadius: 14, alignItems: "center", justifyContent: "center" },
  segTxt: { fontSize: 12, fontFamily: "Nunito_800ExtraBold" },

  partnerPill: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    borderWidth: 1,
    borderRadius: 12,
    paddingHorizontal: 12,
    paddingVertical: 8,
    marginHorizontal: 16,
    marginBottom: 8,
    overflow: "hidden",
  },

  partnerHint: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    padding: 12,
    borderRadius: 14,
    borderWidth: 1,
    marginBottom: 14,
    backgroundColor: "rgba(236,72,153,0.08)",
  },
  partnerHintText: { flex: 1, fontSize: 12, fontFamily: "Nunito_600SemiBold" },

  proCard: { borderRadius: 22, overflow: "hidden", marginBottom: 4, paddingBottom: 12 },
  proContent: { flexDirection: "row", alignItems: "center", gap: 12, padding: 14, paddingTop: 14, paddingRight: 14 },
  proEmojiCircle: { width: 50, height: 50, borderRadius: 16, alignItems: "center", justifyContent: "center" },
  proTitle: { color: "#fff", fontSize: 17, fontFamily: "Nunito_800ExtraBold" },
  proBenefit: { color: "#f9a8d4", fontSize: 12, fontFamily: "Nunito_700Bold", lineHeight: 16 },
  proSub: { color: "#D1D5DB", fontSize: 11.5, fontFamily: "Nunito_500Medium", lineHeight: 16 },
  proChipsRow: { flexDirection: "row", flexWrap: "wrap", gap: 6, paddingHorizontal: 14, marginBottom: 8 },
  proChip: {
    paddingHorizontal: 9,
    paddingVertical: 5,
    borderRadius: 10,
    backgroundColor: "rgba(255,255,255,0.08)",
    borderWidth: 1,
    borderColor: "rgba(255,255,255,0.12)",
  },
  proChipText: { color: "#F3F4F6", fontSize: 10, fontFamily: "Nunito_700Bold" },
  proPriceRow: { flexDirection: "row", alignItems: "center", gap: 8, paddingHorizontal: 14, marginBottom: 6 },
  proStrike: { color: "rgba(255,255,255,0.4)", fontSize: 14, textDecorationLine: "line-through", fontFamily: "Nunito_600SemiBold" },
  proOffer: { color: "#fff", fontSize: 22, fontFamily: "Nunito_800ExtraBold" },
  proOffPill: { paddingHorizontal: 8, paddingVertical: 3, borderRadius: 8, backgroundColor: "rgba(34,197,94,0.25)" },
  proOffText: { color: "#86efac", fontSize: 10, fontFamily: "Nunito_800ExtraBold" },
  proCtaGrad: {
    paddingVertical: 13,
    marginHorizontal: 14,
  },
  proCtaInner: { flexDirection: "row", alignItems: "center", gap: 10, paddingHorizontal: 4 },
  proCtaText: { color: "#fff", fontSize: 13.5, fontFamily: "Nunito_800ExtraBold", textAlign: "center" },
  proCtaPrice: { color: "rgba(255,255,255,0.85)", fontSize: 11, fontFamily: "Nunito_600SemiBold", marginTop: 2, textAlign: "center" },
  proFoot: { flexDirection: "row", alignItems: "center", gap: 5, paddingHorizontal: 14, marginTop: 8 },
  proFootText: { color: "#D1D5DB", fontSize: 10.5, fontFamily: "Nunito_600SemiBold", flex: 1, lineHeight: 15 },

  unlockWrap: {
    backgroundColor: "rgba(255,255,255,0.02)",
    borderRadius: 14,
    padding: 12,
    marginTop: 4,
  },
  unlockHead: { flexDirection: "row", alignItems: "center", gap: 6, marginBottom: 10 },
  unlockHeadTxt: { fontSize: 11, fontFamily: "Nunito_800ExtraBold", letterSpacing: 0.8 },
  unlockRow: {
    flexDirection: "row",
    alignItems: "flex-start",
    gap: 10,
    paddingVertical: 10,
    paddingHorizontal: 10,
    borderRadius: 10,
    borderWidth: 1,
    backgroundColor: "rgba(255,255,255,0.03)",
  },
  unlockEmoji: { fontSize: 16, marginTop: 2 },
  unlockTitle: { fontSize: 12.5, fontFamily: "Nunito_800ExtraBold", lineHeight: 18 },
  unlockHook: { fontSize: 11, fontFamily: "Nunito_500Medium", lineHeight: 17, marginTop: 1 },

  sectionHead: { marginBottom: 12, gap: 4 },
  sectionTitle: { fontSize: 11, fontFamily: "Nunito_800ExtraBold", letterSpacing: 2 },
  sectionSub: { fontSize: 12, fontFamily: "Nunito_400Regular" },

  list: { gap: 14 },

  card: { borderRadius: 20, overflow: "hidden" },
  cardRow: { flexDirection: "row", alignItems: "center", padding: 18, paddingVertical: 20, gap: 14 },
  iconWrap: {
    width: 50, height: 50, borderRadius: 16,
    alignItems: "center", justifyContent: "center",
    borderWidth: 1, borderColor: "rgba(255,255,255,0.12)",
  },
  iconEmoji: { fontSize: 22 },
  textArea: { flex: 1, gap: 4 },
  cardTitle: { fontSize: 16, letterSpacing: -0.2 },
  cardSub: { fontSize: 11.5, letterSpacing: 0.1 },
  arrowCircle: {
    width: 38, height: 38, borderRadius: 19,
    alignItems: "center", justifyContent: "center",
    borderWidth: 1.5, borderColor: "rgba(255,255,255,0.18)",
  },
});
