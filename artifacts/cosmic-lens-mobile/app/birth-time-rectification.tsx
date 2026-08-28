import { Feather } from "@expo/vector-icons";
import * as Haptics from "expo-haptics";
import { LinearGradient } from "expo-linear-gradient";
import { router, useFocusEffect } from "expo-router";
import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  ActivityIndicator,
  Alert,
  Animated,
  Easing,
  Platform,
  Pressable,
  ScrollView,
  StatusBar,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { CosmicBg } from "@/components/CosmicBg";
import { FadeInView, staggerDelay } from "@/components/motion/FadeInView";
import { useC } from "@/context/ThemeContext";
import { useUser } from "@/context/UserContext";
import { API_BASE } from "@/lib/apiConfig";
import {
  consumeBirthTimePaidReady,
  gateBirthTimeRectificationCheckout,
  getPendingBirthTimePurchaseId,
} from "@/lib/birthTimeRectificationCheckoutFlow";
import { clearPendingBirthTimeCheckout } from "@/lib/pendingBirthTimeCheckout";
import type { BirthTimeSubmitPayload } from "@/lib/pendingBirthTimeCheckout";

type Impact = "" | "positive" | "negative" | "mixed";

type Milestone = {
  id: string;
  label: string;
  selected: boolean;
  month: string;
  year: string;
  impact: Impact;
};

const MILESTONE_DEFS: { id: string; label: string }[] = [
  { id: "first_relationship", label: "When did your first serious relationship begin?" },
  { id: "first_breakup", label: "When was your first breakup? (if any)" },
  { id: "left_home", label: "When did you first leave home for studies or work?" },
  { id: "first_job_income", label: "When did your first job / regular income begin?" },
  { id: "education_complete", label: "When did you complete your highest education?" },
  { id: "career_turning", label: "When was your biggest career turning point?" },
  { id: "emotional_turning", label: "When was your biggest emotional turning point?" },
  { id: "city_shift", label: "When did you first move to another city or country?" },
  { id: "marriage", label: "When did you get married or engaged?" },
  { id: "first_child", label: "When was your first child born? (if any)" },
  { id: "surgery", label: "When did you have a major surgery or hospitalization?" },
  { id: "accident", label: "When was your most significant accident?" },
  { id: "family_event", label: "When did a major life event happen for close family (parents/sibling)?" },
  { id: "foreign_travel", label: "When did you take your first foreign trip?" },
];

const IMPACTS: {
  id: Exclude<Impact, "">;
  label: string;
  color: string;
  bg: string;
}[] = [
  { id: "positive", label: "Positive", color: "#16a34a", bg: "#16a34a28" },
  { id: "negative", label: "Negative", color: "#dc2626", bg: "#dc262628" },
  { id: "mixed", label: "Mixed", color: "#ca8a04", bg: "#ca8a0428" },
];

const GENDER_OPTIONS = ["Male", "Female", "Other"] as const;

const MIN_MILESTONES = 5;
const MIN_15Y_CHARS = 40;

function pad2(n: number) {
  return String(n).padStart(2, "0");
}

function isValidYear(y: string): boolean {
  if (!/^\d{4}$/.test(y)) return false;
  const n = Number(y);
  const max = new Date().getFullYear() + 1;
  return n >= 1950 && n <= max;
}

function notify(title: string, message: string) {
  if (Platform.OS === "web" && typeof window !== "undefined") {
    window.alert(`${title}\n\n${message}`);
    return;
  }
  Alert.alert(title, message);
}

function ImpactChip({
  label,
  color,
  bg,
  active,
  onPress,
}: {
  label: string;
  color: string;
  bg: string;
  active: boolean;
  onPress: () => void;
}) {
  const scale = useRef(new Animated.Value(1)).current;

  useEffect(() => {
    if (!active) return;
    scale.setValue(0.88);
    Animated.spring(scale, {
      toValue: 1,
      friction: 4,
      tension: 160,
      useNativeDriver: true,
    }).start();
  }, [active, scale]);

  return (
    <Pressable
      onPress={() => {
        try {
          Haptics.selectionAsync();
        } catch {}
        onPress();
      }}
    >
      <Animated.View
        style={[
          s.impactChip,
          {
            transform: [{ scale }],
            backgroundColor: active ? bg : "transparent",
            borderColor: active ? color : "#ffffff22",
          },
        ]}
      >
        <Text
          style={{
            color: active ? color : "#9ca3af",
            fontSize: 12,
            fontWeight: "800",
          }}
        >
          {label}
        </Text>
      </Animated.View>
    </Pressable>
  );
}

function MilestoneCard({
  m,
  C,
  onToggle,
  onPatch,
}: {
  m: Milestone;
  C: ReturnType<typeof useC>;
  onToggle: () => void;
  onPatch: (patch: Partial<Milestone>) => void;
}) {
  const fade = useRef(new Animated.Value(m.selected ? 1 : 0)).current;

  useEffect(() => {
    Animated.timing(fade, {
      toValue: m.selected ? 1 : 0,
      duration: 220,
      easing: Easing.out(Easing.cubic),
      useNativeDriver: true,
    }).start();
  }, [m.selected, fade]);

  const yearOk = !m.year || isValidYear(m.year);

  return (
    <View
      style={[
        s.mileCard,
        {
          backgroundColor: m.selected ? `${C.accent}14` : C.bgCard,
          borderColor: m.selected ? C.accent : C.border,
        },
      ]}
    >
      <Pressable onPress={onToggle} style={s.mileHead}>
        <Feather
          name={m.selected ? "check-square" : "square"}
          size={18}
          color={m.selected ? C.accent : C.textMuted}
        />
        <Text style={[s.mileLabel, { color: C.text }]}>{m.label}</Text>
      </Pressable>
      {m.selected ? (
        <Animated.View style={{ opacity: fade }}>
          <View style={s.mileBody}>
            <View style={s.myRow}>
              <View style={s.myField}>
                <Text style={[s.miniLabel, { color: C.textMuted }]}>Month *</Text>
                <TextInput
                  value={m.month}
                  onChangeText={(t) => onPatch({ month: t })}
                  placeholder="e.g. Mar"
                  placeholderTextColor={C.textMuted}
                  autoCapitalize="words"
                  style={[
                    s.input,
                    { color: C.text, backgroundColor: C.bgCard2, borderColor: C.border },
                  ]}
                />
              </View>
              <View style={s.myField}>
                <Text style={[s.miniLabel, { color: C.textMuted }]}>Year *</Text>
                <TextInput
                  value={m.year}
                  onChangeText={(t) => {
                    const digits = t.replace(/[^\d]/g, "").slice(0, 4);
                    onPatch({ year: digits });
                  }}
                  placeholder="e.g. 2019"
                  placeholderTextColor={C.textMuted}
                  keyboardType="numeric"
                  maxLength={4}
                  style={[
                    s.input,
                    {
                      color: C.text,
                      backgroundColor: C.bgCard2,
                      borderColor: yearOk ? C.border : "#dc2626",
                    },
                  ]}
                />
                {!yearOk ? (
                  <Text style={s.yearErr}>Enter a 4-digit year (e.g. 2019)</Text>
                ) : null}
              </View>
            </View>
            <Text style={[s.miniLabel, { color: C.textMuted }]}>Impact *</Text>
            <View style={s.impactRow}>
              {IMPACTS.map((imp) => (
                <ImpactChip
                  key={imp.id}
                  label={imp.label}
                  color={imp.color}
                  bg={imp.bg}
                  active={m.impact === imp.id}
                  onPress={() => onPatch({ impact: imp.id })}
                />
              ))}
            </View>
          </View>
        </Animated.View>
      ) : null}
    </View>
  );
}

export default function BirthTimeRectificationScreen() {
  const insets = useSafeAreaInsets();
  const C = useC();
  const { user, birthData } = useUser();
  const androidSB = StatusBar.currentHeight ?? 24;
  const topPad =
    Platform.OS === "web"
      ? 67
      : Platform.OS === "android"
        ? Math.max(insets.top, androidSB)
        : insets.top;

  const prefill = useMemo(() => {
    const bd = birthData;
    if (!bd) {
      return { name: "", dob: "", tob: "", place: "", gender: "" };
    }
    return {
      name: bd.name || "",
      dob: `${pad2(bd.day)}/${pad2(bd.month)}/${bd.year}`,
      tob: `${pad2(bd.hour)}:${pad2(bd.minute)} ${bd.ampm || ""}`.trim(),
      place: bd.place || "",
      gender: "",
    };
  }, [birthData]);

  const [fullName, setFullName] = useState(prefill.name);
  const [gender, setGender] = useState(prefill.gender);
  const [dob, setDob] = useState(prefill.dob);
  const [approxTob, setApproxTob] = useState(prefill.tob);
  const [birthPlace, setBirthPlace] = useState(prefill.place);
  const [milestones, setMilestones] = useState<Milestone[]>(() =>
    MILESTONE_DEFS.map((d) => ({
      id: d.id,
      label: d.label,
      selected: false,
      month: "",
      year: "",
      impact: "" as Impact,
    })),
  );
  const [last15y, setLast15y] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const toggleMilestone = (id: string) => {
    try {
      Haptics.selectionAsync();
    } catch {}
    setMilestones((prev) =>
      prev.map((m) => (m.id === id ? { ...m, selected: !m.selected } : m)),
    );
  };

  const patchMilestone = (id: string, patch: Partial<Milestone>) => {
    setMilestones((prev) =>
      prev.map((m) => (m.id === id ? { ...m, ...patch } : m)),
    );
  };

  const fail = (title: string, message: string) => {
    setFormError(message);
    notify(title, message);
  };

  const buildValidatedPayload = (): BirthTimeSubmitPayload | null => {
    setFormError(null);
    if (!user?.id || !user?.api_key) {
      fail("Login required", "Please log in before submitting this form.");
      return null;
    }
    if (!fullName.trim()) {
      fail("Required", "Full name is required.");
      return null;
    }
    if (!gender.trim()) {
      fail("Required", "Please select Gender (Male / Female / Other).");
      return null;
    }
    if (!dob.trim()) {
      fail("Required", "Date of birth is required.");
      return null;
    }
    if (!approxTob.trim()) {
      fail("Required", "Approximate birth time is required.");
      return null;
    }
    if (!birthPlace.trim()) {
      fail("Required", "Birth place is required.");
      return null;
    }

    const selected = milestones.filter((m) => m.selected);
    if (selected.length < MIN_MILESTONES) {
      fail(
        "More events needed",
        `Selected ${selected.length}/${MIN_MILESTONES}. Select and complete at least ${MIN_MILESTONES} life milestones.`,
      );
      return null;
    }

    const incomplete = selected.find(
      (m) => !m.month.trim() || !isValidYear(m.year.trim()) || !m.impact,
    );
    if (incomplete) {
      const why = !incomplete.month.trim()
        ? "Month"
        : !isValidYear(incomplete.year.trim())
          ? "Year (4 digits, e.g. 2019)"
          : "Impact";
      fail(
        "Incomplete milestone",
        `"${incomplete.label}" needs ${why}.`,
      );
      return null;
    }

    if (last15y.trim().length < MIN_15Y_CHARS) {
      fail(
        "Required",
        "Please fill the last 15 years box with your top 5 events (Event · Month/Year · Impact).",
      );
      return null;
    }

    return {
      full_name: fullName.trim(),
      gender: gender.trim(),
      dob: dob.trim(),
      approx_tob: approxTob.trim(),
      birth_place: birthPlace.trim(),
      milestone_events: selected.map((m) => ({
        id: m.id,
        label: m.label,
        month: m.month.trim(),
        year: m.year.trim(),
        month_year: `${m.month.trim()} ${m.year.trim()}`,
        impact: m.impact,
      })),
      last_15y_events_text: last15y.trim(),
    };
  };

  const postSubmit = async (
    payload: BirthTimeSubmitPayload,
    purchaseId?: number,
  ) => {
    if (!user?.id || !user?.api_key) {
      fail("Login required", "Please log in before submitting this form.");
      return;
    }
    setSubmitting(true);
    try {
      const res = await fetch(`${API_BASE}/api/birth-time-rectification/submit`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-API-Key": user.api_key,
          "X-User-Id": String(user.id),
        },
        body: JSON.stringify({
          user_id: user.id,
          purchase_id: purchaseId,
          ...payload,
        }),
      });
      const json = await res.json().catch(() => ({} as any));
      if (!res.ok) {
        if (res.status === 405) {
          throw new Error(
            "API server needs update (birth-time submit route missing). Deploy api-server + pm2 restart cosmic-api.",
          );
        }
        if (res.status === 402) {
          throw new Error(json?.message || "Payment required before submit.");
        }
        throw new Error(json?.message || json?.error || `Submit failed (${res.status})`);
      }
      clearPendingBirthTimeCheckout();
      try {
        Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      } catch {}
      setFormError(null);
      const okMsg =
        json?.message ||
        "Request received. Our astrologer will review your events and contact you soon.";
      if (Platform.OS === "web") {
        notify("Request sent", okMsg);
        router.back();
      } else {
        Alert.alert("Request sent", okMsg, [
          { text: "OK", onPress: () => router.back() },
        ]);
      }
    } catch (e: any) {
      fail("Submit failed", String(e?.message || e));
    } finally {
      setSubmitting(false);
    }
  };

  const submit = async () => {
    const payload = buildValidatedPayload();
    if (!payload) return;

    let handedOffToSubmit = false;
    setSubmitting(true);
    try {
      await gateBirthTimeRectificationCheckout({
        user,
        payload,
        onEntitled: (purchaseId) => {
          handedOffToSubmit = true;
          void postSubmit(payload, purchaseId ?? getPendingBirthTimePurchaseId());
        },
      });
    } finally {
      if (!handedOffToSubmit) setSubmitting(false);
    }
  };

  useFocusEffect(
    useCallback(() => {
      const paidPayload = consumeBirthTimePaidReady();
      if (!paidPayload) return;
      const pid = getPendingBirthTimePurchaseId();
      void postSubmit(paidPayload, pid);
      // eslint-disable-next-line react-hooks/exhaustive-deps -- resume once after Razorpay
    }, [user?.id, user?.api_key]),
  );

  const field = (
    label: string,
    value: string,
    onChange: (t: string) => void,
    opts?: { placeholder?: string; multiline?: boolean; minHeight?: number },
  ) => (
    <View style={s.field}>
      <Text style={[s.label, { color: C.textMuted }]}>{label}</Text>
      <TextInput
        value={value}
        onChangeText={onChange}
        placeholder={opts?.placeholder}
        placeholderTextColor={C.textMuted}
        multiline={opts?.multiline}
        textAlignVertical={opts?.multiline ? "top" : "center"}
        style={[
          s.input,
          {
            color: C.text,
            backgroundColor: C.bgCard2,
            borderColor: C.border,
            minHeight: opts?.minHeight,
          },
        ]}
      />
    </View>
  );

  return (
    <CosmicBg>
      <View style={[s.topBar, { paddingTop: topPad + 8 }]}>
        <Pressable
          onPress={() => router.back()}
          style={[s.backBtn, { backgroundColor: C.bgCard, borderColor: C.border }]}
          hitSlop={10}
        >
          <Feather name="arrow-left" size={18} color={C.text} />
        </Pressable>
        <Text style={[s.topTitle, { color: C.text }]} numberOfLines={1}>
          Birth Time Rectification
        </Text>
        <View style={{ width: 38 }} />
      </View>

      <ScrollView
        contentContainerStyle={[s.scroll, { paddingBottom: insets.bottom + 28 }]}
        keyboardShouldPersistTaps="handled"
        showsVerticalScrollIndicator={false}
      >
        <FadeInView delay={0}>
          <Text style={[s.hero, { color: C.text }]}>
            Precision Birth Time Rectification
          </Text>
          <Text style={[s.sub, { color: C.textMid }]}>
            All fields are mandatory. Select at least {MIN_MILESTONES} milestones and fill
            Month, Year, and Impact inside each card. Also complete the last 15 years box.
          </Text>
        </FadeInView>

        <FadeInView delay={staggerDelay(1, 50, 40)}>
          <Text style={[s.section, { color: C.accent }]}>1 · Identity</Text>
          {field("Full name *", fullName, setFullName, { placeholder: "Your full name" })}
          <View style={s.field}>
            <Text style={[s.label, { color: C.textMuted }]}>Gender *</Text>
            <View style={s.genderRow}>
              {GENDER_OPTIONS.map((g) => {
                const on = gender === g;
                return (
                  <Pressable
                    key={g}
                    onPress={() => {
                      try {
                        Haptics.selectionAsync();
                      } catch {}
                      setGender(g);
                    }}
                    style={[
                      s.genderChip,
                      {
                        backgroundColor: on ? `${C.accent}22` : C.bgCard2,
                        borderColor: on ? C.accent : C.border,
                      },
                    ]}
                  >
                    <Text
                      style={{
                        color: on ? C.accent : C.textMuted,
                        fontSize: 13,
                        fontWeight: "800",
                      }}
                    >
                      {g}
                    </Text>
                  </Pressable>
                );
              })}
            </View>
          </View>
          {field("Date of birth *", dob, setDob, { placeholder: "DD/MM/YYYY" })}
          {field("Approximate birth time *", approxTob, setApproxTob, {
            placeholder: "e.g. 10:30 AM",
          })}
          {field("Birth place *", birthPlace, setBirthPlace, {
            placeholder: "City, State, Country",
          })}
        </FadeInView>

        <FadeInView delay={staggerDelay(2, 50, 60)}>
          <Text style={[s.section, { color: C.accent }]}>
            2 · Life milestones (select + Month / Year + Impact)
          </Text>
          <Text style={[s.hint, { color: C.textMuted }]}>
            Tap a milestone, then fill Month, Year, and Impact inside the same card.
            Positive = green · Negative = red · Mixed = yellow.
          </Text>
        </FadeInView>

        {milestones.map((m, i) => (
          <FadeInView key={m.id} delay={staggerDelay(3 + (i % 6), 35, 70)}>
            <MilestoneCard
              m={m}
              C={C}
              onToggle={() => toggleMilestone(m.id)}
              onPatch={(patch) => patchMilestone(m.id, patch)}
            />
          </FadeInView>
        ))}

        <FadeInView delay={staggerDelay(4, 50, 90)}>
          <Text style={[s.section, { color: C.accent }]}>
            3 · Last 15 years — top 5 events *
          </Text>
          <Text style={[s.hint, { color: C.textMuted }]}>
            One line per event: Event · Month/Year · Impact (Positive / Negative / Mixed)
          </Text>
          <TextInput
            value={last15y}
            onChangeText={setLast15y}
            placeholder={
              "Example:\n" +
              "1) First job — Jun 2018 — Positive\n" +
              "2) Moved to Pune — Jan 2020 — Mixed\n" +
              "3) Marriage — Nov 2022 — Positive\n" +
              "4) …\n" +
              "5) …"
            }
            placeholderTextColor={C.textMuted}
            multiline
            textAlignVertical="top"
            style={[
              s.bigBox,
              {
                color: C.text,
                backgroundColor: C.bgCard,
                borderColor: C.accent,
              },
            ]}
          />
        </FadeInView>

        <FadeInView delay={staggerDelay(5, 50, 110)}>
          {formError ? (
            <View style={s.errorBox}>
              <Feather name="alert-circle" size={16} color="#fecaca" />
              <Text style={s.errorText}>{formError}</Text>
            </View>
          ) : null}

          <View
            style={[
              s.buyCard,
              {
                backgroundColor: C.bgCard,
                borderColor: C.accent,
              },
            ]}
          >
            <View style={s.buyTop}>
              <View style={[s.offerPill, { backgroundColor: `${C.accent}22`, borderColor: C.accent }]}>
                <Text style={[s.offerPillText, { color: C.accent }]}>LIMITED OFFER</Text>
              </View>
              <Text style={s.saveText}>Save ₹2,000</Text>
            </View>

            <View style={s.buyPriceRow}>
              <View>
                <Text style={[s.wasLabel, { color: C.textMuted }]}>Was</Text>
                <Text style={[s.priceStrikeBig, { color: C.textMuted }]}>₹2,999</Text>
              </View>
              <View style={s.buyPriceNow}>
                <Text style={[s.nowLabel, { color: C.accent }]}>Today</Text>
                <Text style={[s.priceNowBig, { color: C.text }]}>₹999</Text>
              </View>
            </View>

            <Pressable
              onPress={() => {
                try {
                  Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
                } catch {}
                submit();
              }}
              disabled={submitting}
              style={({ pressed }) => [
                { opacity: pressed || submitting ? 0.88 : 1, marginTop: 14 },
              ]}
            >
              <LinearGradient
                colors={["#7c3aed", "#db2777"]}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 0 }}
                style={s.buyCta}
              >
                {submitting ? (
                  <ActivityIndicator color="#fff" />
                ) : (
                  <>
                    <Text style={s.buyCtaText}>Get Precision Birth Time</Text>
                    <Text style={s.buyCtaSub}>Pay ₹999 · Unlock now</Text>
                  </>
                )}
              </LinearGradient>
            </Pressable>

            <Text style={[s.buyFoot, { color: C.textMuted }]}>
              One-time payment · Reviewed by our astrologer
            </Text>
          </View>
        </FadeInView>
      </ScrollView>
    </CosmicBg>
  );
}

const s = StyleSheet.create({
  topBar: {
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: 14,
    paddingBottom: 10,
    gap: 10,
  },
  backBtn: {
    width: 38,
    height: 38,
    borderRadius: 12,
    borderWidth: 1,
    alignItems: "center",
    justifyContent: "center",
  },
  topTitle: {
    flex: 1,
    fontSize: 16,
    fontFamily: "Nunito_700Bold",
    textAlign: "center",
  },
  scroll: { paddingHorizontal: 16, paddingTop: 8 },
  hero: {
    fontSize: 22,
    fontFamily: "Nunito_700Bold",
    letterSpacing: -0.4,
  },
  sub: {
    fontSize: 13,
    lineHeight: 19,
    marginTop: 6,
    marginBottom: 14,
    fontFamily: "Nunito_500Medium",
  },
  section: {
    fontSize: 13,
    fontFamily: "Nunito_700Bold",
    marginTop: 16,
    marginBottom: 10,
    letterSpacing: 0.2,
  },
  field: { marginBottom: 10 },
  label: { fontSize: 11, fontFamily: "Nunito_700Bold", marginBottom: 5 },
  genderRow: { flexDirection: "row", flexWrap: "wrap", gap: 8 },
  genderChip: {
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 12,
    borderWidth: 1.5,
    minWidth: 88,
    alignItems: "center",
  },
  miniLabel: { fontSize: 10, fontWeight: "700", marginBottom: 4 },
  input: {
    borderWidth: 1,
    borderRadius: 12,
    paddingHorizontal: 12,
    paddingVertical: 11,
    fontSize: 14,
  },
  mileCard: {
    borderWidth: 1,
    borderRadius: 14,
    padding: 12,
    marginBottom: 8,
  },
  mileHead: { flexDirection: "row", alignItems: "flex-start", gap: 10 },
  mileLabel: { flex: 1, fontSize: 13, fontWeight: "600", lineHeight: 18 },
  mileBody: { marginTop: 10, gap: 8, paddingBottom: 2 },
  myRow: { flexDirection: "row", gap: 10 },
  myField: { flex: 1 },
  impactRow: { flexDirection: "row", flexWrap: "wrap", gap: 8 },
  impactChip: {
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 999,
    borderWidth: 1.5,
  },
  hint: { fontSize: 12, lineHeight: 16, marginBottom: 8 },
  yearErr: { color: "#f87171", fontSize: 10, fontWeight: "600", marginTop: 4 },
  bigBox: {
    minHeight: 180,
    borderWidth: 1.5,
    borderRadius: 16,
    paddingHorizontal: 14,
    paddingVertical: 12,
    fontSize: 14,
    lineHeight: 20,
    fontFamily: "Nunito_500Medium",
  },
  errorBox: {
    flexDirection: "row",
    alignItems: "flex-start",
    gap: 8,
    marginTop: 14,
    padding: 12,
    borderRadius: 12,
    backgroundColor: "#7f1d1dcc",
    borderWidth: 1,
    borderColor: "#ef4444",
  },
  errorText: {
    flex: 1,
    color: "#fecaca",
    fontSize: 13,
    lineHeight: 18,
    fontFamily: "Nunito_600SemiBold",
  },
  buyCard: {
    marginTop: 18,
    borderWidth: 1.5,
    borderRadius: 18,
    padding: 16,
  },
  buyTop: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    marginBottom: 14,
  },
  offerPill: {
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 999,
    borderWidth: 1,
  },
  offerPillText: {
    fontSize: 11,
    letterSpacing: 0.6,
    fontFamily: "Nunito_700Bold",
  },
  saveText: {
    color: "#22c55e",
    fontSize: 13,
    fontFamily: "Nunito_700Bold",
  },
  buyPriceRow: {
    flexDirection: "row",
    alignItems: "flex-end",
    justifyContent: "space-between",
    gap: 12,
  },
  wasLabel: {
    fontSize: 11,
    fontFamily: "Nunito_600SemiBold",
    marginBottom: 2,
  },
  priceStrikeBig: {
    fontSize: 18,
    fontFamily: "Nunito_600SemiBold",
    textDecorationLine: "line-through",
  },
  buyPriceNow: { alignItems: "flex-end" },
  nowLabel: {
    fontSize: 11,
    fontFamily: "Nunito_700Bold",
    marginBottom: 2,
  },
  priceNowBig: {
    fontSize: 36,
    lineHeight: 40,
    fontFamily: "Nunito_700Bold",
    letterSpacing: -1,
  },
  buyCta: {
    borderRadius: 14,
    paddingVertical: 14,
    paddingHorizontal: 16,
    alignItems: "center",
    justifyContent: "center",
    minHeight: 56,
  },
  buyCtaText: {
    color: "#fff",
    fontSize: 16,
    fontFamily: "Nunito_700Bold",
    textAlign: "center",
  },
  buyCtaSub: {
    color: "rgba(255,255,255,0.85)",
    fontSize: 12,
    fontFamily: "Nunito_600SemiBold",
    marginTop: 2,
  },
  buyFoot: {
    marginTop: 10,
    textAlign: "center",
    fontSize: 11,
    fontFamily: "Nunito_500Medium",
  },
});
