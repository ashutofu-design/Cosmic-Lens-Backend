import { Feather } from "@expo/vector-icons";
import * as Haptics from "expo-haptics";
import { LinearGradient } from "expo-linear-gradient";
import React, { useEffect, useRef } from "react";
import { Animated, Easing, Pressable, StyleSheet, Text, View } from "react-native";
import {
  bandColor,
  type CouplePlainCopy,
  type MarriageBasicsPayload,
  type MarriagePartnerBasics,
} from "@/lib/milanMarriageBasics";
import { buildPartnerPlainView } from "@/lib/partnerPlainCopy";

/** Legacy Pro / deep-link route — 36 Gun shape converter */
export interface MilanKootItem {
  score: number;
  max: number;
  label: string;
  detail: string;
  bad: boolean;
}

export interface MilanBasicResultData {
  nadi: MilanKootItem;
  gana: MilanKootItem;
  bhakut: MilanKootItem;
  maitri: MilanKootItem;
  yoni: MilanKootItem;
  tara: MilanKootItem;
  vasya: MilanKootItem;
  varna: MilanKootItem;
  total: number;
  manglik: boolean;
}

export function milanJsonToResult(json: { koots: { key: string }[]; total?: number; manglik_dosh?: boolean }): MilanBasicResultData {
  const bk: Record<string, MilanKootItem> = {};
  for (const k of json.koots) bk[k.key] = k as MilanKootItem;
  return {
    nadi: bk.nadi ?? { score: 0, max: 8, label: "Nadi", detail: "-", bad: true },
    gana: bk.gana ?? { score: 0, max: 6, label: "Gana", detail: "-", bad: true },
    bhakut: bk.bhakut ?? { score: 0, max: 7, label: "Bhakut", detail: "-", bad: true },
    maitri: bk.maitri ?? { score: 0, max: 5, label: "Graha Maitri", detail: "-", bad: true },
    yoni: bk.yoni ?? { score: 0, max: 4, label: "Yoni", detail: "-", bad: true },
    tara: bk.tara ?? { score: 0, max: 3, label: "Tara", detail: "-", bad: true },
    vasya: bk.vasya ?? { score: 0, max: 2, label: "Vasya", detail: "-", bad: false },
    varna: bk.varna ?? { score: 0, max: 1, label: "Varna", detail: "-", bad: true },
    total: json.total ?? 0,
    manglik: json.manglik_dosh ?? false,
  };
}

type Props = {
  data: MarriageBasicsPayload;
  isDark: boolean;
  onOpenPro: () => void;
  onRecalculate: () => void;
};

type CompactPlain = {
  bandLabel: string;
  headline: string;
  positive: string;
  watchout: string;
  proLockTeaser: string;
  remedyTeaser: string;
};

function SectionHeader({ title, isDark }: { title: string; isDark: boolean }) {
  return (
    <View style={st.sectionHead}>
      <Text style={[st.sectionTitle, { color: isDark ? "#e9d5ff" : "#5b21b6" }]}>{title}</Text>
      <View style={[st.sectionLine, { backgroundColor: isDark ? "rgba(167,139,250,0.22)" : "rgba(91,33,182,0.12)" }]} />
    </View>
  );
}

function resolveCompactPlain(person: MarriagePartnerBasics): CompactPlain {
  const pc = person.plain_copy;
  if (pc?.headline && pc.positives?.length) {
    const alertTeaser =
      person.critical_alerts?.locked && person.critical_alerts.teaser
        ? `${person.critical_alerts.teaser} — full detail in Pro.`
        : null;
    return {
      bandLabel: pc.band_label,
      headline: pc.headline,
      positive: pc.positives[0] ?? "Chart shows some supportive marriage signals.",
      watchout: pc.watchouts[0] ?? "Stay conscious before big decisions.",
      proLockTeaser: pc.pro_lock_teaser ?? alertTeaser ?? "Deeper marriage timing + hidden alerts — unlock in Pro.",
      remedyTeaser: pc.remedy_teaser ?? "Full personalized remedy chain — Pro report mein.",
    };
  }
  const fb = buildPartnerPlainView(person);
  return {
    bandLabel: fb.bandLabel,
    headline: fb.headline,
    positive: fb.positives[0] ?? "Some supportive signals present.",
    watchout: fb.watchouts[0] ?? "Some areas need care.",
    proLockTeaser: person.critical_alerts?.teaser
      ? `${person.critical_alerts.teaser} — Pro unlock.`
      : "Marriage dasha windows + hidden alerts — Pro mein.",
    remedyTeaser: "Full remedy plan locked in Pro report.",
  };
}

function ProMiniStrip({ text, isDark, onOpenPro }: { text: string; isDark: boolean; onOpenPro: () => void }) {
  return (
    <Pressable
      onPress={onOpenPro}
      style={[
        st.proStrip,
        {
          backgroundColor: isDark ? "rgba(124,58,237,0.14)" : "rgba(124,58,237,0.06)",
          borderColor: isDark ? "rgba(167,139,250,0.3)" : "rgba(124,58,237,0.18)",
        },
      ]}
    >
      <Feather name="zap" size={14} color={isDark ? "#c4b5fd" : "#7c3aed"} />
      <Text style={[st.proStripTxt, { color: isDark ? "#e9d5ff" : "#5b21b6" }]}>{text}</Text>
      <Feather name="chevron-right" size={14} color={isDark ? "#a78bfa" : "#7c3aed"} />
    </Pressable>
  );
}

function PartnerCard({ person, isDark, onOpenPro }: { person: MarriagePartnerBasics; isDark: boolean; onOpenPro: () => void }) {
  const col = bandColor(person.readiness_band);
  const plain = resolveCompactPlain(person);
  const genderLabel = person.gender === "male" ? "Male" : person.gender === "female" ? "Female" : "Chart";

  return (
    <View
      style={[
        st.partnerCard,
        {
          backgroundColor: isDark ? "rgba(255,255,255,0.04)" : "#fff",
          borderColor: isDark ? `${col}35` : `${col}25`,
        },
      ]}
    >
      <View style={st.partnerHead}>
        <View style={{ flex: 1 }}>
          <Text style={[st.partnerName, { color: isDark ? "#f3e8ff" : "#1e1b4b" }]}>{person.name}</Text>
          <Text style={[st.partnerGender, { color: isDark ? "#c4b5fd" : "#6366f1" }]}>{genderLabel}</Text>
        </View>
        <View style={[st.bandPill, { backgroundColor: `${col}20`, borderColor: `${col}40` }]}>
          <Text style={[st.bandPillTxt, { color: col }]}>{plain.bandLabel}</Text>
          <Text style={[st.bandScore, { color: isDark ? "rgba(255,255,255,0.6)" : "#64748b" }]}>
            {person.readiness_score}/100
          </Text>
        </View>
      </View>

      <Text style={[st.headline, { color: isDark ? "rgba(241,245,249,0.82)" : "#475569" }]}>{plain.headline}</Text>

      <View style={st.bulletRow}>
        <Feather name="check" size={12} color={isDark ? "#86efac" : "#15803d"} style={st.bulletIcon} />
        <Text style={[st.bulletTxt, { color: isDark ? "rgba(241,245,249,0.88)" : "#334155" }]}>{plain.positive}</Text>
      </View>
      <View style={st.bulletRow}>
        <Feather name="alert-circle" size={12} color={isDark ? "#fca5a5" : "#dc2626"} style={st.bulletIcon} />
        <Text style={[st.bulletTxt, { color: isDark ? "rgba(241,245,249,0.88)" : "#334155" }]}>{plain.watchout}</Text>
      </View>

      <Pressable
        onPress={onOpenPro}
        style={[st.lockBox, { backgroundColor: isDark ? "rgba(239,68,68,0.12)" : "rgba(239,68,68,0.08)", borderColor: isDark ? "rgba(239,68,68,0.28)" : "rgba(239,68,68,0.2)" }]}
      >
        <Feather name="lock" size={14} color={isDark ? "#fca5a5" : "#b91c1c"} />
        <Text style={[st.lockTxt, { color: isDark ? "#fecaca" : "#991b1b" }]}>{plain.proLockTeaser}</Text>
        <Text style={[st.lockSub, { color: isDark ? "rgba(255,255,255,0.5)" : "#64748b" }]}>Unlock in Pro →</Text>
      </Pressable>

      <Pressable onPress={onOpenPro} style={[st.remedyLock, { backgroundColor: isDark ? "rgba(255,255,255,0.04)" : "rgba(0,0,0,0.03)" }]}>
        <Feather name="lock" size={11} color={isDark ? "rgba(255,255,255,0.35)" : "#94a3b8"} />
        <Text style={[st.remedyLockTxt, { color: isDark ? "rgba(255,255,255,0.45)" : "#64748b" }]} numberOfLines={2}>
          {plain.remedyTeaser}
        </Text>
      </Pressable>
    </View>
  );
}

function CoupleGapCard({ copy, isDark, onOpenPro }: { copy: CouplePlainCopy; isDark: boolean; onOpenPro: () => void }) {
  return (
    <View
      style={[
        st.gapCard,
        {
          backgroundColor: isDark ? "rgba(251,191,36,0.08)" : "rgba(251,191,36,0.06)",
          borderColor: isDark ? "rgba(251,191,36,0.25)" : "rgba(245,158,11,0.2)",
        },
      ]}
    >
      <Text style={[st.gapEyebrow, { color: isDark ? "#fde68a" : "#b45309" }]}>TOGETHER — WHAT BASIC HIDES</Text>
      <Text style={[st.gapBody, { color: isDark ? "rgba(241,245,249,0.9)" : "#334155" }]}>{copy.gap_teaser}</Text>
      {(copy.locked_highlights ?? []).map(item => (
        <View key={item} style={st.gapRow}>
          <Feather name="lock" size={10} color={isDark ? "#fcd34d" : "#d97706"} />
          <Text style={[st.gapItem, { color: isDark ? "rgba(255,255,255,0.55)" : "#64748b" }]}>{item}</Text>
        </View>
      ))}
      <Pressable onPress={onOpenPro} style={({ pressed }) => ({ opacity: pressed ? 0.88 : 1 })}>
        <LinearGradient colors={["#6366F1", "#8B5CF6", "#db2777"]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }} style={st.gapBtn}>
          <Text style={st.gapBtnTxt}>{copy.pro_cta_line}</Text>
          <Feather name="arrow-right" size={14} color="#fff" />
        </LinearGradient>
      </Pressable>
    </View>
  );
}

function defaultCoupleGap(data: MarriageBasicsPayload): CouplePlainCopy {
  return {
    gap_teaser: `Together ${data.couple.structural_score}/100 — full cross-chart read sirf Pro mein.`,
    pro_cta_line: "Get Full Pro Report — PDF + timing + 36 Gun",
    locked_highlights: [
      "36 Gun full score breakdown",
      "Cross-chart synastry depth",
      "Marriage dasha windows (both partners)",
      "Full remedy chain + downloadable PDF",
    ],
  };
}

export function KundliMilanBasicResult({ data, isDark, onOpenPro, onRecalculate }: Props) {
  const fade = useRef(new Animated.Value(0)).current;
  const coupleCol = bandColor(data.couple.structural_band);
  const coupleCopy = data.couple.plain_copy ?? defaultCoupleGap(data);
  const p1Strip = data.p1.plain_copy?.pro_strip ?? `Pro for ${data.p1.name}: full marriage consultation + PDF`;

  useEffect(() => {
    Animated.timing(fade, { toValue: 1, duration: 450, easing: Easing.out(Easing.cubic), useNativeDriver: true }).start();
    Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
  }, [fade]);

  return (
    <Animated.View style={[st.wrap, { opacity: fade }]}>
      <LinearGradient
        colors={isDark ? ["#1a0533", "#0f172a"] : ["#f5f3ff", "#ede9fe"]}
        style={[st.heroCard, { borderColor: isDark ? `${coupleCol}50` : `${coupleCol}35` }]}
      >
        <Text style={[st.heroEyebrow, { color: isDark ? "#c4b5fd" : "#6366f1" }]}>COUPLE MARRIAGE STRUCTURE</Text>
        <Text style={[st.heroScore, { color: coupleCol }]}>{data.couple.structural_score}</Text>
        <Text style={[st.heroDenom, { color: isDark ? "rgba(255,255,255,0.5)" : "#64748b" }]}>/ 100</Text>
        <View style={[st.heroBand, { backgroundColor: `${coupleCol}22`, borderColor: `${coupleCol}44` }]}>
          <Text style={[st.heroBandTxt, { color: coupleCol }]}>{data.couple.structural_band}</Text>
        </View>
        <Text style={[st.heroVerdict, { color: isDark ? "rgba(241,245,249,0.9)" : "#334155" }]}>
          {data.couple.future_verdict}
        </Text>
      </LinearGradient>

      <SectionHeader title="PARTNER A" isDark={isDark} />
      <PartnerCard person={data.p1} isDark={isDark} onOpenPro={onOpenPro} />
      <ProMiniStrip text={p1Strip} isDark={isDark} onOpenPro={onOpenPro} />

      <SectionHeader title="PARTNER B" isDark={isDark} />
      <PartnerCard person={data.p2} isDark={isDark} onOpenPro={onOpenPro} />

      <CoupleGapCard copy={coupleCopy} isDark={isDark} onOpenPro={onOpenPro} />

      <View
        style={[
          st.proCard,
          {
            backgroundColor: isDark ? "rgba(124,58,237,0.12)" : "rgba(124,58,237,0.05)",
            borderColor: isDark ? "rgba(167,139,250,0.28)" : "rgba(124,58,237,0.15)",
          },
        ]}
      >
        <Text style={[st.proEyebrow, { color: isDark ? "#c4b5fd" : "#6d28d9" }]}>Basic = summary only</Text>
        <Text style={[st.proLead, { color: isDark ? "rgba(241,245,249,0.88)" : "#1e293b" }]}>
          Pro gives the full marriage consultation — 36 Gun, synastry, dasha timing, remedies & PDF. Engine-only, no fluff.
        </Text>
        <Pressable onPress={onOpenPro} style={({ pressed }) => ({ opacity: pressed ? 0.9 : 1 })}>
          <LinearGradient colors={["#6366F1", "#8B5CF6", "#db2777"]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }} style={st.proBtn}>
            <Text style={st.proBtnTxt}>Get Full Pro Report</Text>
            <Feather name="arrow-right" size={16} color="#fff" />
          </LinearGradient>
        </Pressable>
      </View>

      <Pressable onPress={onRecalculate} style={[st.recalcBtn, { borderColor: isDark ? "rgba(255,255,255,0.1)" : "rgba(0,0,0,0.08)" }]}>
        <Feather name="refresh-cw" size={14} color={isDark ? "rgba(255,255,255,0.5)" : "#64748B"} />
        <Text style={{ color: isDark ? "rgba(255,255,255,0.5)" : "#64748B", fontSize: 13, fontFamily: "Nunito_500Medium" }}>
          Recalculate / Change Details
        </Text>
      </Pressable>
    </Animated.View>
  );
}

const st = StyleSheet.create({
  wrap: { gap: 12, marginTop: 4 },
  heroCard: { borderRadius: 22, borderWidth: 1.5, padding: 20, alignItems: "center", gap: 6 },
  heroEyebrow: { fontSize: 9, fontFamily: "Nunito_800ExtraBold", letterSpacing: 1.4 },
  heroScore: { fontSize: 44, fontFamily: "Nunito_800ExtraBold", lineHeight: 48 },
  heroDenom: { fontSize: 12, fontFamily: "Nunito_600SemiBold", marginTop: -8 },
  heroBand: { borderWidth: 1, borderRadius: 20, paddingHorizontal: 14, paddingVertical: 5, marginTop: 4 },
  heroBandTxt: { fontSize: 14, fontFamily: "Nunito_800ExtraBold" },
  heroVerdict: { fontSize: 13, fontFamily: "Nunito_500Medium", textAlign: "center", lineHeight: 20, marginTop: 8 },
  sectionHead: { flexDirection: "row", alignItems: "center", gap: 10, marginTop: 6 },
  sectionTitle: { fontSize: 10, fontFamily: "Nunito_800ExtraBold", letterSpacing: 1.4 },
  sectionLine: { flex: 1, height: 1 },
  partnerCard: { borderRadius: 18, borderWidth: 1, padding: 14, gap: 8 },
  partnerHead: { flexDirection: "row", justifyContent: "space-between", alignItems: "flex-start", gap: 10 },
  partnerName: { fontSize: 16, fontFamily: "Nunito_800ExtraBold" },
  partnerGender: { fontSize: 10, fontFamily: "Nunito_700Bold", marginTop: 2 },
  bandPill: { borderWidth: 1, borderRadius: 12, paddingHorizontal: 10, paddingVertical: 6, alignItems: "center" },
  bandPillTxt: { fontSize: 11, fontFamily: "Nunito_800ExtraBold" },
  bandScore: { fontSize: 9, fontFamily: "Nunito_600SemiBold", marginTop: 2 },
  headline: { fontSize: 12, fontFamily: "Nunito_500Medium", lineHeight: 18, marginTop: 2, marginBottom: 2 },
  bulletRow: { flexDirection: "row", alignItems: "flex-start", gap: 8 },
  bulletIcon: { marginTop: 3 },
  bulletTxt: { flex: 1, fontSize: 11.5, fontFamily: "Nunito_500Medium", lineHeight: 17 },
  lockBox: { borderRadius: 12, borderWidth: 1, padding: 10, gap: 4, marginTop: 4 },
  lockTxt: { fontSize: 11, fontFamily: "Nunito_700Bold", lineHeight: 16 },
  lockSub: { fontSize: 9, fontFamily: "Nunito_600SemiBold" },
  remedyLock: { flexDirection: "row", alignItems: "center", gap: 8, borderRadius: 10, padding: 10, marginTop: 2 },
  remedyLockTxt: { flex: 1, fontSize: 10.5, fontFamily: "Nunito_500Medium", lineHeight: 15 },
  proStrip: { flexDirection: "row", alignItems: "center", gap: 8, borderWidth: 1, borderRadius: 12, padding: 12, marginTop: -4 },
  proStripTxt: { flex: 1, fontSize: 11, fontFamily: "Nunito_700Bold", lineHeight: 16 },
  gapCard: { borderRadius: 18, borderWidth: 1, padding: 16, gap: 8, marginTop: 4 },
  gapEyebrow: { fontSize: 9, fontFamily: "Nunito_800ExtraBold", letterSpacing: 1.2 },
  gapBody: { fontSize: 12.5, fontFamily: "Nunito_600SemiBold", lineHeight: 19 },
  gapRow: { flexDirection: "row", alignItems: "center", gap: 8, paddingLeft: 2 },
  gapItem: { fontSize: 10.5, fontFamily: "Nunito_500Medium", flex: 1 },
  gapBtn: { flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 8, borderRadius: 12, paddingVertical: 12, marginTop: 6 },
  gapBtnTxt: { color: "#fff", fontSize: 12, fontFamily: "Nunito_800ExtraBold", textAlign: "center", flex: 1 },
  proCard: { borderRadius: 20, borderWidth: 1, padding: 18, gap: 10, marginTop: 4 },
  proEyebrow: { fontSize: 11, fontFamily: "Nunito_800ExtraBold", letterSpacing: 0.8 },
  proLead: { fontSize: 12.5, fontFamily: "Nunito_500Medium", lineHeight: 19 },
  proBtn: { flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 8, borderRadius: 14, paddingVertical: 14, marginTop: 4 },
  proBtnTxt: { color: "#fff", fontSize: 14, fontFamily: "Nunito_800ExtraBold" },
  recalcBtn: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
    borderRadius: 14,
    borderWidth: 1,
    paddingVertical: 14,
    marginBottom: 8,
    marginTop: 4,
  },
});
