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
  I18nManager,
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
import {
  downloadLoveRealityProPdf,
  shareLoveRealityPdf,
} from "@/lib/loveRealityProPdfDownload";
import {
  LOVE_REALITY_CHECKOUT_CONFIG,
  LOVE_REALITY_PRO_UI_PRICING,
  runLoveRealityProUnlockCta,
} from "@/lib/loveRealityProOffer";
import { coerceProPdfLang } from "@/lib/proPdfLang";

const PRO_CHIPS = [
  "All 5 love tools in one PDF",
  "Breakup · Loyalty · Return · Future",
  "Red flags & remedies chapter",
  "Saved in My Reports",
];

const LOVE_PRO_UNLOCK = [
  { emoji: "💘", title: "Love Compatibility", tease: "How deep your bond really runs — and what silently blocks full connection —" },
  { emoji: "💔", title: "Breakup Chances", tease: "The real risk window isn’t random — one planetary phase can flip everything —" },
  { emoji: "🛡️", title: "Loyalty Check", tease: "Trust looks fine on the surface, but charts reveal where doubt actually starts —" },
  { emoji: "🪃", title: "Will X Return?", tease: "Return isn’t just hope — timing and karma both point to one answer —" },
  { emoji: "🔮", title: "Future Outcome", tease: "Where this relationship is headed in 1–3 years — the full arc is in the PDF —" },
  { emoji: "🚩", title: "Red Flags & Remedies", tease: "Hidden warning signs plus practical upay — only in the Pro report —" },
];

function LoveRealityProUnlockList({ isDark }: { isDark: boolean }) {
  return (
    <View style={{ gap: 14 }}>
      <View style={{
        backgroundColor: isDark ? "rgba(124,58,237,0.10)" : "rgba(124,58,237,0.05)",
        borderWidth: 1,
        borderColor: isDark ? "rgba(167,139,250,0.28)" : "rgba(124,58,237,0.20)",
        borderRadius: 16,
        padding: 14,
        gap: 8,
      }}>
        <View style={{ flexDirection: "row", alignItems: "center", gap: 8 }}>
          <Text style={{ fontSize: 16 }}>💞</Text>
          <Text style={{ color: isDark ? "#e9d5ff" : "#5b21b6", fontSize: 13, fontFamily: "Nunito_800ExtraBold" }}>
            Love Reality Pro PDF
          </Text>
        </View>
        <Text style={{ color: isDark ? "rgba(226,232,240,0.85)" : "#334155", fontSize: 12.5, fontFamily: "Nunito_400Regular", lineHeight: 19 }}>
          One combined 14–16 page report — all instant checks plus red flags, remedies, and personalised truth for both partners.
        </Text>
      </View>

      <View style={{
        backgroundColor: isDark ? "rgba(255,255,255,0.03)" : "rgba(0,0,0,0.02)",
        borderWidth: 1,
        borderColor: isDark ? "rgba(255,255,255,0.08)" : "rgba(0,0,0,0.06)",
        borderRadius: 16,
        padding: 14,
        gap: 10,
      }}>
        <View style={{ flexDirection: "row", alignItems: "center", gap: 8 }}>
          <Feather name="unlock" size={14} color={isDark ? "#f472b6" : "#db2777"} />
          <Text style={{ color: isDark ? "#f472b6" : "#db2777", fontSize: 12, fontFamily: "Nunito_800ExtraBold", letterSpacing: 1.2 }}>
            WHAT YOU UNLOCK
          </Text>
        </View>
        <View style={{ gap: 11 }}>
          {LOVE_PRO_UNLOCK.map((sec, i) => (
            <View key={i} style={{ gap: 3 }}>
              <View style={{ flexDirection: "row", alignItems: "center", gap: 7 }}>
                <Text style={{ fontSize: 13 }}>{sec.emoji}</Text>
                <Text style={{ color: isDark ? "#f5e6c8" : "#1e293b", fontSize: 12.5, fontFamily: "Nunito_800ExtraBold", flex: 1 }}>
                  {sec.title}
                </Text>
              </View>
              <View style={{ flexDirection: "row", alignItems: "flex-start", gap: 7, paddingLeft: 22 }}>
                <Text style={{ color: isDark ? "rgba(244,114,182,0.7)" : "rgba(219,39,119,0.65)", fontSize: 11, fontFamily: "Nunito_700Bold", marginTop: 1 }}>→</Text>
                <Text style={{ color: isDark ? "rgba(226,232,240,0.72)" : "#475569", fontSize: 11.5, fontFamily: "Nunito_400Regular", flex: 1, lineHeight: 17, fontStyle: "italic" }}>
                  {sec.tease}
                </Text>
              </View>
            </View>
          ))}
        </View>
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
  const arrowPulse = useRef(new Animated.Value(1)).current;

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
    const arrow = Animated.loop(
      Animated.sequence([
        Animated.timing(arrowPulse, { toValue: 1.1, duration: 1400, easing: Easing.inOut(Easing.sin), useNativeDriver: true }),
        Animated.timing(arrowPulse, { toValue: 1, duration: 1400, easing: Easing.inOut(Easing.sin), useNativeDriver: true }),
      ]),
    );
    glow.start();
    arrow.start();
    return () => { glow.stop(); arrow.stop(); };
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

          <View style={s.proBadgeWrap}>
            <LinearGradient colors={["#a855f7", "#ec4899"]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }} style={s.proBadge}>
              <Text style={s.proBadgeText}>✨ PRO · LOVE REALITY PDF</Text>
            </LinearGradient>
          </View>

          <View style={s.proContent}>
            <LinearGradient colors={["#9333ea", "#ec4899"]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={s.proEmojiCircle}>
              <Text style={{ fontSize: 28 }}>💞</Text>
            </LinearGradient>

            <View style={{ flex: 1, gap: 4 }}>
              <Text style={s.proTitle}>Love Reality Pro PDF</Text>
              <Text style={s.proSub}>Complete relationship truth in one report</Text>
              <View style={s.proDescTag}>
                <Text style={s.proDescText}>14–16 pages · all 5 tools + red flags</Text>
              </View>
            </View>

            <Animated.View style={{ transform: [{ scale: arrowPulse }] }}>
              <LinearGradient colors={["#9333ea", "#ec4899"]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={s.proArrow}>
                {pdfLoading ? (
                  <ActivityIndicator size="small" color="#fff" />
                ) : (
                  <Feather name={I18nManager.isRTL ? "chevron-left" : "chevron-right"} size={20} color="#fff" />
                )}
              </LinearGradient>
            </Animated.View>
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
                <>
                  <Feather name="file-text" size={16} color="#fff" />
                  <Text style={s.proCtaText}>
                    {canPro ? `Unlock Full PDF · ₹${offerInr}` : "Add partner kundli to unlock"}
                  </Text>
                </>
              )}
            </LinearGradient>
          </Pressable>

          <View style={s.proFoot}>
            <Feather name="zap" size={10} color="#c084fc" />
            <Text style={s.proFootText}>BPHS + Phaladeepika + KP · saved in My Reports</Text>
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
  const [selectedPdfLang, setSelectedPdfLang] = useState(coerceProPdfLang(t.lang));
  const [pdfDoneVisible, setPdfDoneVisible] = useState(false);
  const pdfShareRef = useRef({ uri: "", name: "" });

  useFocusEffect(
    useCallback(() => {
      if (consumeCouplePaidReady()) {
        setConfirmVisible(true);
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
    if (!primaryProfile?.birthData || !partnerProfile?.birthData || !user?.id) return;

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
      bypassCheckout: LOVE_REALITY_CHECKOUT_CONFIG.bypassCheckoutForTesting,
      onEntitled: () => setConfirmVisible(true),
    });
  }

  async function handleDownloadProPdf() {
    if (!primaryProfile?.birthData || !partnerProfile?.birthData || !user?.id) return;
    setConfirmVisible(false);
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
      pdfShareRef.current = { uri: result.shareUri, name: result.fileName };
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      setPdfDoneVisible(true);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "PDF download failed";
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
            <LoveRealityProUnlockList isDark={isDark} />
            <LoveRealityProPanel
              isDark={isDark}
              canPro={canPro}
              pdfLoading={pdfLoading}
              onUnlock={startProUnlock}
            />
          </ScrollView>
        )}
      </View>

      <ProPdfLanguagePickerModal
        visible={langPickerVisible}
        selectedLang={selectedPdfLang}
        onSelectLang={setSelectedPdfLang}
        onClose={() => setLangPickerVisible(false)}
        onContinue={onLangPickerContinue}
        title="PDF Language"
        subtitle="Love Reality Pro report — English, Hinglish, or Hindi."
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

      <Modal visible={pdfLoading} transparent animationType="fade">
        <View style={cd.loadingBackdrop}>
          <View style={[cd.loadingCard, { backgroundColor: isDark ? "#1A2135" : "#fff" }]}>
            <ActivityIndicator size="large" color="#a855f7" />
            <Text style={[cd.loadingTitle, { color: C.text }]}>Love Reality Pro PDF</Text>
            <Text style={{ color: C.textMuted, fontSize: 12, textAlign: "center", marginTop: 6 }}>
              Reading both kundlis · writing your full report…
            </Text>
          </View>
        </View>
      </Modal>

      <Modal visible={pdfDoneVisible} transparent animationType="fade" onRequestClose={() => setPdfDoneVisible(false)}>
        <Pressable style={cd.backdrop} onPress={() => setPdfDoneVisible(false)}>
          <Pressable style={cd.cardWrap} onPress={e => e.stopPropagation?.()}>
            <View style={[cd.card, { backgroundColor: isDark ? "#0F0A1F" : "#FFFFFF", padding: 24 }]}>
              <Text style={{ fontSize: 40, textAlign: "center" }}>✅</Text>
              <Text style={[cd.title, { color: C.text, marginTop: 8 }]}>PDF Ready</Text>
              <Text style={[cd.sub, { color: C.textDim }]}>
                Saved in My Reports. You can open or share anytime.
              </Text>
              <View style={{ gap: 10, marginTop: 16 }}>
                <Pressable
                  onPress={() => {
                    setPdfDoneVisible(false);
                    router.push("/my-reports" as any);
                  }}
                  style={({ pressed }) => ({ opacity: pressed ? 0.85 : 1, borderRadius: 12, overflow: "hidden" })}
                >
                  <LinearGradient colors={["#9333ea", "#ec4899"]} style={cd.continueGrad}>
                    <Text style={cd.continueTxt}>View in My Reports</Text>
                  </LinearGradient>
                </Pressable>
                <Pressable
                  onPress={async () => {
                    const { uri, name } = pdfShareRef.current;
                    if (uri) await shareLoveRealityPdf(uri, name);
                  }}
                  style={[cd.changeBtn, { borderColor: C.border, marginTop: 0 }]}
                >
                  <Text style={{ color: C.text, fontFamily: "Nunito_700Bold" }}>Share PDF</Text>
                </Pressable>
              </View>
            </View>
          </Pressable>
        </Pressable>
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
  loadingBackdrop: { flex: 1, backgroundColor: "rgba(0,0,0,0.7)", alignItems: "center", justifyContent: "center" },
  loadingCard: { padding: 28, borderRadius: 20, alignItems: "center", width: "80%", maxWidth: 320 },
  loadingTitle: { marginTop: 14, fontSize: 16, fontFamily: "Nunito_700Bold" },
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

  proCard: { borderRadius: 26, overflow: "hidden", marginBottom: 22, paddingBottom: 16 },
  proBadgeWrap: { position: "absolute", top: 0, right: 0, zIndex: 2 },
  proBadge: { paddingHorizontal: 12, paddingVertical: 6, borderBottomLeftRadius: 16, borderTopRightRadius: 24 },
  proBadgeText: { color: "#fff", fontSize: 8, fontFamily: "Nunito_800ExtraBold", letterSpacing: 1 },
  proContent: { flexDirection: "row", alignItems: "center", gap: 12, padding: 18, paddingTop: 22, paddingRight: 14 },
  proEmojiCircle: { width: 56, height: 56, borderRadius: 18, alignItems: "center", justifyContent: "center" },
  proTitle: { color: "#fff", fontSize: 17, fontFamily: "Nunito_800ExtraBold" },
  proSub: { color: "#D1D5DB", fontSize: 12, fontFamily: "Nunito_500Medium" },
  proDescTag: {
    alignSelf: "flex-start",
    marginTop: 4,
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 8,
    backgroundColor: "rgba(168,85,247,0.2)",
  },
  proDescText: { color: "#e9d5ff", fontSize: 10, fontFamily: "Nunito_700Bold" },
  proArrow: { width: 44, height: 44, borderRadius: 22, alignItems: "center", justifyContent: "center" },
  proChipsRow: { flexDirection: "row", flexWrap: "wrap", gap: 6, paddingHorizontal: 16, marginBottom: 10 },
  proChip: {
    paddingHorizontal: 9,
    paddingVertical: 5,
    borderRadius: 10,
    backgroundColor: "rgba(255,255,255,0.08)",
    borderWidth: 1,
    borderColor: "rgba(255,255,255,0.12)",
  },
  proChipText: { color: "#F3F4F6", fontSize: 9, fontFamily: "Nunito_700Bold" },
  proPriceRow: { flexDirection: "row", alignItems: "center", gap: 8, paddingHorizontal: 16, marginBottom: 8 },
  proStrike: { color: "rgba(255,255,255,0.4)", fontSize: 14, textDecorationLine: "line-through", fontFamily: "Nunito_600SemiBold" },
  proOffer: { color: "#fff", fontSize: 22, fontFamily: "Nunito_800ExtraBold" },
  proOffPill: { paddingHorizontal: 8, paddingVertical: 3, borderRadius: 8, backgroundColor: "rgba(34,197,94,0.25)" },
  proOffText: { color: "#86efac", fontSize: 10, fontFamily: "Nunito_800ExtraBold" },
  proCtaGrad: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
    paddingVertical: 14,
    marginHorizontal: 16,
  },
  proCtaText: { color: "#fff", fontSize: 14, fontFamily: "Nunito_800ExtraBold" },
  proFoot: { flexDirection: "row", alignItems: "center", gap: 5, paddingHorizontal: 16, marginTop: 10 },
  proFootText: { color: "#D1D5DB", fontSize: 10, fontFamily: "Nunito_600SemiBold" },

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
