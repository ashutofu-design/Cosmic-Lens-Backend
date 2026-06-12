import { Feather } from "@expo/vector-icons";
import * as Haptics from "expo-haptics";
import { LinearGradient } from "expo-linear-gradient";
import { router, useLocalSearchParams } from "expo-router";
import React, { useEffect, useMemo, useState } from "react";
import {
  ActivityIndicator,
  Alert,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { CosmicBg } from "@/components/CosmicBg";
import { useC } from "@/context/ThemeContext";
import { useUser } from "@/context/UserContext";
import {
  fetchLoveRealityEngineSnapshot,
  submitLoveRealityHumanOrder,
  type EngineSnapshot,
} from "@/lib/loveRealityHumanOrder";
import { packLovePerson } from "@/lib/loveRealityProPdfDownload";
import {
  LOVE_REALITY_URGENT_SURCHARGE_INR,
  LOVE_REALITY_PRO_UI_PRICING,
  loveRealityOrderTotalInr,
} from "@/lib/loveRealityProOffer";
import { mapLoveRealityResult, type LoveRealityToolKey } from "@/lib/loveRealityToolMappers";
import { coerceProPdfLang, proPdfLangDisplayName } from "@/lib/proPdfLang";

const PREVIEW_TOOLS: { key: LoveRealityToolKey; emoji: string; label: string }[] = [
  { key: "love-compat", emoji: "💘", label: "Love" },
  { key: "breakup", emoji: "💔", label: "Breakup Risk" },
  { key: "loyalty", emoji: "🛡️", label: "Loyalty" },
  { key: "will-return", emoji: "🔄", label: "Return" },
  { key: "future-outcome", emoji: "🔮", label: "Future" },
];

const STEPS = [
  { emoji: "📊", title: "Free engine snapshot", body: "Your charts are calculated instantly — no AI." },
  { emoji: "🔍", title: "Founder review", body: "Our astrologer reads both kundlis in depth." },
  { emoji: "📄", title: "Verified PDF", body: "14-page personalized report with remedies." },
  { emoji: "📲", title: "Delivered to you", body: "Sent on WhatsApp or email — language you picked." },
];

function scoreLine(key: LoveRealityToolKey, json: Record<string, unknown>): string {
  const mapped = mapLoveRealityResult(key, json);
  if (mapped.percent != null) return `${mapped.percent}%`;
  if (mapped.riskScore != null) return `${mapped.riskScore}% risk`;
  if (mapped.statusLabel) return mapped.statusLabel;
  if (mapped.loyaltyCompare) {
    return `You ${mapped.loyaltyCompare.youScore}% · Partner ${mapped.loyaltyCompare.partnerScore}%`;
  }
  return "Ready";
}

export default function LoveRealityHumanOrderScreen() {
  const C = useC();
  const insets = useSafeAreaInsets();
  const { user, profiles, primaryProfileId } = useUser();
  const params = useLocalSearchParams<{ partnerId?: string; lang?: string }>();
  const partnerId = typeof params.partnerId === "string" ? params.partnerId : null;
  const lang = coerceProPdfLang(typeof params.lang === "string" ? params.lang : "en");

  const primaryProfile = profiles.find(p => p.id === primaryProfileId) ?? profiles[0] ?? null;
  const partnerProfile = partnerId ? (profiles.find(p => p.id === partnerId) ?? null) : null;

  const [snapshot, setSnapshot] = useState<EngineSnapshot | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [done, setDone] = useState<{ orderId: string; etaHours: number } | null>(null);
  const [contactMethod, setContactMethod] = useState<"whatsapp" | "email">("whatsapp");
  const [contactValue, setContactValue] = useState("");
  const [urgent, setUrgent] = useState(false);

  const totalInr = loveRealityOrderTotalInr(urgent);
  const langLabel = proPdfLangDisplayName(lang);

  const p1 = useMemo(() => {
    if (!primaryProfile?.birthData) return null;
    return packLovePerson(primaryProfile.birthData, primaryProfile.name);
  }, [primaryProfile]);

  const p2 = useMemo(() => {
    if (!partnerProfile?.birthData) return null;
    return packLovePerson(partnerProfile.birthData, partnerProfile.name);
  }, [partnerProfile]);

  useEffect(() => {
    if (!p1 || !p2) {
      setLoading(false);
      return;
    }
    let cancelled = false;
    void (async () => {
      setLoading(true);
      try {
        const snap = await fetchLoveRealityEngineSnapshot({
          p1,
          p2,
          userId: user?.id,
          apiKey: user?.api_key,
        });
        if (!cancelled) setSnapshot(snap);
      } catch (e: unknown) {
        if (!cancelled) {
          const msg = e instanceof Error ? e.message : "Could not load scores";
          Alert.alert("Engine error", msg, [{ text: "OK", onPress: () => router.back() }]);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [p1, p2, user?.id, user?.api_key]);

  async function onSubmit() {
    if (!p1 || !p2 || !user?.id) return;
    const trimmed = contactValue.trim();
    if (!trimmed) {
      Alert.alert("Contact required", "Add WhatsApp number or email for PDF delivery.");
      return;
    }
    setSubmitting(true);
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    try {
      const result = await submitLoveRealityHumanOrder({
        p1,
        p2,
        lang,
        contactMethod,
        contactValue: trimmed,
        urgent,
        userId: user.id,
        apiKey: user.api_key,
      });
      setDone({ orderId: result.order_id, etaHours: result.eta_hours });
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Order failed";
      Alert.alert("Could not place order", msg);
    } finally {
      setSubmitting(false);
    }
  }

  if (!primaryProfile?.birthData || !partnerProfile?.birthData) {
    return (
      <CosmicBg>
        <View style={[s.center, { paddingTop: insets.top + 40 }]}>
          <Text style={{ color: C.text, fontFamily: "Nunito_600SemiBold" }}>Partner kundli required</Text>
          <Pressable onPress={() => router.back()} style={s.backBtn}>
            <Text style={s.backBtnTxt}>Go back</Text>
          </Pressable>
        </View>
      </CosmicBg>
    );
  }

  if (done) {
    return (
      <CosmicBg>
        <View style={[s.center, { paddingTop: insets.top + 48, paddingHorizontal: 28 }]}>
          <Text style={{ fontSize: 48 }}>✅</Text>
          <Text style={[s.successTitle, { color: C.text }]}>Order placed!</Text>
          <Text style={[s.successSub, { color: C.textDim }]}>
            Your verified Love Reality PDF ({langLabel}) will be prepared by our astrologer and sent on{" "}
            {contactMethod === "whatsapp" ? "WhatsApp" : "email"} within{" "}
            {done.etaHours <= 24 ? "12 hours" : "24–48 hours"}.
          </Text>
          <Text style={[s.orderId, { color: C.textMuted }]}>Order #{done.orderId.slice(0, 8)}</Text>
          <Pressable
            onPress={() => router.replace({ pathname: "/love-reality", params: { partnerId: partnerId ?? "", openPro: "1" } } as never)}
            style={s.primaryBtn}
          >
            <LinearGradient colors={["#9333ea", "#ec4899"]} style={s.primaryGrad}>
              <Text style={s.primaryTxt}>Done</Text>
            </LinearGradient>
          </Pressable>
        </View>
      </CosmicBg>
    );
  }

  return (
    <CosmicBg>
      <KeyboardAvoidingView
        style={{ flex: 1 }}
        behavior={Platform.OS === "ios" ? "padding" : undefined}
      >
        <ScrollView
          contentContainerStyle={{
            paddingTop: insets.top + 8,
            paddingBottom: insets.bottom + 28,
            paddingHorizontal: 16,
            gap: 16,
          }}
          keyboardShouldPersistTaps="handled"
        >
          <View style={s.topRow}>
            <Pressable onPress={() => router.back()} hitSlop={10}>
              <Feather name="chevron-left" size={24} color={C.text} />
            </Pressable>
            <View style={{ flex: 1, alignItems: "center" }}>
              <Text style={[s.title, { color: C.text }]}>Verified PDF Order</Text>
              <Text style={[s.sub, { color: C.textDim }]}>
                {primaryProfile.name} & {partnerProfile.name} · {langLabel}
              </Text>
            </View>
            <View style={{ width: 24 }} />
          </View>

          <LinearGradient colors={["#1a0a2e", "#150a20"]} style={s.heroCard}>
            <Text style={s.heroEmoji}>🪐</Text>
            <Text style={s.heroTitle}>Your free cosmic snapshot</Text>
            <Text style={s.heroSub}>
              Engine-calculated scores — instant & accurate. Full explanation comes in your founder-verified PDF.
            </Text>
          </LinearGradient>

          {loading ? (
            <View style={s.loadingBox}>
              <ActivityIndicator color="#ec4899" />
              <Text style={{ color: C.textDim, fontFamily: "Nunito_500Medium" }}>Calculating charts…</Text>
            </View>
          ) : snapshot ? (
            <View style={s.scoreGrid}>
              {PREVIEW_TOOLS.map(tool => {
                const json = snapshot.tools[tool.key] ?? {};
                return (
                  <View key={tool.key} style={[s.scoreCard, { borderColor: C.border }]}>
                    <Text style={s.scoreEmoji}>{tool.emoji}</Text>
                    <Text style={[s.scoreLabel, { color: C.textDim }]}>{tool.label}</Text>
                    <Text style={[s.scoreVal, { color: C.text }]}>{scoreLine(tool.key, json)}</Text>
                  </View>
                );
              })}
            </View>
          ) : null}

          <View style={[s.stepsCard, { backgroundColor: C.bgCard, borderColor: C.border }]}>
            <Text style={[s.stepsHead, { color: C.text }]}>What happens next</Text>
            {STEPS.map(step => (
              <View key={step.title} style={s.stepRow}>
                <Text style={s.stepEmoji}>{step.emoji}</Text>
                <View style={{ flex: 1 }}>
                  <Text style={[s.stepTitle, { color: C.text }]}>{step.title}</Text>
                  <Text style={[s.stepBody, { color: C.textDim }]}>{step.body}</Text>
                </View>
              </View>
            ))}
          </View>

          <View style={[s.formCard, { backgroundColor: C.bgCard, borderColor: C.border }]}>
            <Text style={[s.formHead, { color: C.text }]}>Delivery details</Text>
            <View style={s.methodRow}>
              {(["whatsapp", "email"] as const).map(m => (
                <Pressable
                  key={m}
                  onPress={() => {
                    setContactMethod(m);
                    Haptics.selectionAsync();
                  }}
                  style={[
                    s.methodBtn,
                    {
                      borderColor: contactMethod === m ? "#ec4899" : C.border,
                      backgroundColor: contactMethod === m ? "rgba(236,72,153,0.12)" : "transparent",
                    },
                  ]}
                >
                  <Feather name={m === "whatsapp" ? "message-circle" : "mail"} size={14} color="#ec4899" />
                  <Text style={[s.methodTxt, { color: C.text }]}>
                    {m === "whatsapp" ? "WhatsApp" : "Email"}
                  </Text>
                </Pressable>
              ))}
            </View>
            <TextInput
              value={contactValue}
              onChangeText={setContactValue}
              placeholder={contactMethod === "whatsapp" ? "10-digit mobile number" : "your@email.com"}
              placeholderTextColor={C.textMuted}
              keyboardType={contactMethod === "whatsapp" ? "phone-pad" : "email-address"}
              autoCapitalize="none"
              style={[s.input, { color: C.text, borderColor: C.border, backgroundColor: C.bg }]}
            />

            <Pressable
              onPress={() => {
                setUrgent(v => !v);
                Haptics.selectionAsync();
              }}
              style={[s.urgentRow, { borderColor: urgent ? "#f59e0b" : C.border }]}
            >
              <View style={{ flex: 1 }}>
                <Text style={[s.urgentTitle, { color: C.text }]}>⚡ Urgent delivery (12 hours)</Text>
                <Text style={[s.urgentSub, { color: C.textDim }]}>
                  +₹{LOVE_REALITY_URGENT_SURCHARGE_INR} · priority founder review
                </Text>
              </View>
              <View style={[s.check, { borderColor: urgent ? "#f59e0b" : C.border, backgroundColor: urgent ? "#f59e0b" : "transparent" }]}>
                {urgent ? <Feather name="check" size={14} color="#fff" /> : null}
              </View>
            </Pressable>
          </View>

          <Pressable onPress={onSubmit} disabled={submitting || loading} style={{ opacity: submitting ? 0.7 : 1 }}>
            <LinearGradient colors={["#9333ea", "#ec4899", "#f59e0b"]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }} style={s.primaryGrad}>
              {submitting ? (
                <ActivityIndicator color="#fff" />
              ) : (
                <Text style={s.primaryTxt}>
                  Place order · ₹{totalInr}
                  {urgent ? "" : ` (was ₹${LOVE_REALITY_PRO_UI_PRICING.originalInr})`}
                </Text>
              )}
            </LinearGradient>
          </Pressable>

          <Text style={[s.footnote, { color: C.textMuted }]}>
            No AI report on screen — your PDF is hand-prepared by our astrologer for accuracy.
          </Text>
        </ScrollView>
      </KeyboardAvoidingView>
    </CosmicBg>
  );
}

const s = StyleSheet.create({
  center: { flex: 1, alignItems: "center", gap: 12 },
  topRow: { flexDirection: "row", alignItems: "center", marginBottom: 4 },
  title: { fontSize: 18, fontFamily: "Nunito_700Bold" },
  sub: { fontSize: 12, fontFamily: "Nunito_500Medium", marginTop: 2 },
  heroCard: { borderRadius: 20, padding: 18, gap: 6 },
  heroEmoji: { fontSize: 28 },
  heroTitle: { color: "#f5e6c8", fontSize: 17, fontFamily: "Nunito_700Bold" },
  heroSub: { color: "rgba(226,232,240,0.75)", fontSize: 13, lineHeight: 19, fontFamily: "Nunito_400Regular" },
  loadingBox: { alignItems: "center", gap: 10, paddingVertical: 24 },
  scoreGrid: { flexDirection: "row", flexWrap: "wrap", gap: 10 },
  scoreCard: {
    width: "31%",
    flexGrow: 1,
    minWidth: 96,
    borderRadius: 14,
    borderWidth: 1,
    padding: 12,
    gap: 4,
    alignItems: "center",
  },
  scoreEmoji: { fontSize: 22 },
  scoreLabel: { fontSize: 10, fontFamily: "Nunito_600SemiBold", textAlign: "center" },
  scoreVal: { fontSize: 13, fontFamily: "Nunito_700Bold", textAlign: "center" },
  stepsCard: { borderRadius: 18, borderWidth: 1, padding: 16, gap: 12 },
  stepsHead: { fontSize: 15, fontFamily: "Nunito_700Bold" },
  stepRow: { flexDirection: "row", gap: 10, alignItems: "flex-start" },
  stepEmoji: { fontSize: 18, marginTop: 1 },
  stepTitle: { fontSize: 13, fontFamily: "Nunito_700Bold" },
  stepBody: { fontSize: 12, lineHeight: 17, fontFamily: "Nunito_400Regular", marginTop: 2 },
  formCard: { borderRadius: 18, borderWidth: 1, padding: 16, gap: 12 },
  formHead: { fontSize: 15, fontFamily: "Nunito_700Bold" },
  methodRow: { flexDirection: "row", gap: 10 },
  methodBtn: {
    flex: 1,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 6,
    paddingVertical: 10,
    borderRadius: 12,
    borderWidth: 1,
  },
  methodTxt: { fontSize: 13, fontFamily: "Nunito_600SemiBold" },
  input: {
    borderWidth: 1,
    borderRadius: 12,
    paddingHorizontal: 14,
    paddingVertical: Platform.OS === "ios" ? 12 : 10,
    fontFamily: "Nunito_500Medium",
    fontSize: 15,
  },
  urgentRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    borderWidth: 1,
    borderRadius: 12,
    padding: 12,
  },
  urgentTitle: { fontSize: 13, fontFamily: "Nunito_700Bold" },
  urgentSub: { fontSize: 11, fontFamily: "Nunito_400Regular", marginTop: 2 },
  check: {
    width: 22,
    height: 22,
    borderRadius: 6,
    borderWidth: 1.5,
    alignItems: "center",
    justifyContent: "center",
  },
  primaryBtn: { marginTop: 8, width: "100%" },
  primaryGrad: { borderRadius: 14, paddingVertical: 15, alignItems: "center" },
  primaryTxt: { color: "#fff", fontSize: 15, fontFamily: "Nunito_700Bold" },
  footnote: { fontSize: 11, textAlign: "center", lineHeight: 16, fontFamily: "Nunito_400Regular" },
  successTitle: { fontSize: 22, fontFamily: "Nunito_700Bold", marginTop: 8 },
  successSub: { fontSize: 14, lineHeight: 21, textAlign: "center", fontFamily: "Nunito_400Regular" },
  orderId: { fontSize: 12, fontFamily: "Nunito_500Medium", marginTop: 4 },
  backBtn: { marginTop: 16, padding: 12 },
  backBtnTxt: { color: "#ec4899", fontFamily: "Nunito_600SemiBold" },
});
