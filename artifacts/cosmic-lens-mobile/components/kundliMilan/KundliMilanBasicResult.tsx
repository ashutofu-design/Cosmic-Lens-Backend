import { Feather } from "@expo/vector-icons";
import * as Haptics from "expo-haptics";
import { LinearGradient } from "expo-linear-gradient";
import React, { useEffect, useRef } from "react";
import { Animated, Easing, Pressable, StyleSheet, Text, View } from "react-native";
import {
  bandColor,
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

function SectionHeader({ title, isDark }: { title: string; isDark: boolean }) {
  return (
    <View style={st.sectionHead}>
      <Text style={[st.sectionTitle, { color: isDark ? "#e9d5ff" : "#5b21b6" }]}>{title}</Text>
      <View style={[st.sectionLine, { backgroundColor: isDark ? "rgba(167,139,250,0.22)" : "rgba(91,33,182,0.12)" }]} />
    </View>
  );
}

function BulletList({
  items,
  icon,
  iconColor,
  isDark,
}: {
  items: string[];
  icon: "check" | "alert-circle";
  iconColor: string;
  isDark: boolean;
}) {
  return (
    <View style={st.bulletList}>
      {items.map((item, i) => (
        <View key={`${icon}-${i}`} style={st.bulletRow}>
          <Feather name={icon} size={12} color={iconColor} style={st.bulletIcon} />
          <Text style={[st.bulletTxt, { color: isDark ? "rgba(241,245,249,0.88)" : "#334155" }]}>{item}</Text>
        </View>
      ))}
    </View>
  );
}

function resolvePlainView(person: MarriagePartnerBasics) {
  const pc = person.plain_copy;
  if (pc?.headline && pc.positives?.length) {
    return {
      bandLabel: pc.band_label,
      headline: pc.headline,
      positives: pc.positives,
      watchouts: pc.watchouts ?? [],
      spouseLine: pc.spouse_line ?? null,
      longTermLine: pc.long_term_line ?? null,
      manglikLine: pc.manglik_line ?? null,
      timingLine: pc.timing_line ?? null,
      friction: pc.friction,
      remedy: pc.remedy,
    };
  }
  const fallback = buildPartnerPlainView(person);
  return {
    ...fallback,
    friction: person.friction,
    remedy: person.remedy,
  };
}

function PartnerCard({ person, isDark, onOpenPro }: { person: MarriagePartnerBasics; isDark: boolean; onOpenPro?: () => void }) {
  const col = bandColor(person.readiness_band);
  const plain = resolvePlainView(person);
  const genderLabel =
    person.gender === "male" ? "Male" : person.gender === "female" ? "Female" : "Chart";

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

      <Text style={[st.blockTitle, { color: isDark ? "#86efac" : "#15803d" }]}>What helps marriage</Text>
      <BulletList items={plain.positives} icon="check" iconColor={isDark ? "#86efac" : "#15803d"} isDark={isDark} />

      <Text style={[st.blockTitle, { color: isDark ? "#fca5a5" : "#b91c1c" }]}>What needs care</Text>
      <BulletList items={plain.watchouts} icon="alert-circle" iconColor={isDark ? "#fca5a5" : "#dc2626"} isDark={isDark} />

      {(plain.spouseLine || plain.longTermLine) ? (
        <>
          <Text style={[st.blockTitle, { color: isDark ? "#ddd6fe" : "#4338ca" }]}>Partner & long-term tone</Text>
          {plain.spouseLine ? (
            <Text style={[st.plainLine, { color: isDark ? "rgba(241,245,249,0.88)" : "#334155" }]}>{plain.spouseLine}</Text>
          ) : null}
          {plain.longTermLine ? (
            <Text style={[st.plainLine, { color: isDark ? "rgba(241,245,249,0.88)" : "#334155" }]}>{plain.longTermLine}</Text>
          ) : null}
        </>
      ) : null}

      {plain.manglikLine ? (
        <>
          <Text style={[st.blockTitle, { color: isDark ? "#fde68a" : "#b45309" }]}>Mangal dosh</Text>
          <Text style={[st.plainLine, { color: isDark ? "rgba(241,245,249,0.88)" : "#334155" }]}>{plain.manglikLine}</Text>
        </>
      ) : null}

      {plain.timingLine ? (
        <>
          <Text style={[st.blockTitle, { color: isDark ? "#ddd6fe" : "#4338ca" }]}>Current life phase</Text>
          <Text style={[st.plainLine, { color: isDark ? "rgba(241,245,249,0.88)" : "#334155" }]}>{plain.timingLine}</Text>
        </>
      ) : null}

      {person.critical_alerts?.locked ? (
        <Pressable onPress={onOpenPro} style={[st.lockBox, { backgroundColor: isDark ? "rgba(239,68,68,0.12)" : "rgba(239,68,68,0.08)", borderColor: isDark ? "rgba(239,68,68,0.28)" : "rgba(239,68,68,0.2)" }]}>
          <Feather name="lock" size={14} color={isDark ? "#fca5a5" : "#b91c1c"} />
          <Text style={[st.lockTxt, { color: isDark ? "#fecaca" : "#991b1b" }]}>{person.critical_alerts.teaser}</Text>
          <Text style={[st.lockSub, { color: isDark ? "rgba(255,255,255,0.5)" : "#64748b" }]}>Unlock in Pro →</Text>
        </Pressable>
      ) : null}

      <View style={[st.insightBox, { backgroundColor: isDark ? "rgba(251,191,36,0.1)" : "rgba(251,191,36,0.08)" }]}>
        <Text style={[st.insightLabel, { color: isDark ? "#fde68a" : "#b45309" }]}>Main friction</Text>
        <Text style={[st.insightBody, { color: isDark ? "#f8fafc" : "#334155" }]}>{plain.friction}</Text>
      </View>
      <View style={[st.insightBox, { backgroundColor: isDark ? "rgba(34,197,94,0.1)" : "rgba(34,197,94,0.08)" }]}>
        <Text style={[st.insightLabel, { color: isDark ? "#86efac" : "#15803d" }]}>Simple remedy</Text>
        <Text style={[st.insightBody, { color: isDark ? "#f8fafc" : "#334155" }]}>{plain.remedy}</Text>
      </View>
    </View>
  );
}

export function KundliMilanBasicResult({ data, isDark, onOpenPro, onRecalculate }: Props) {
  const fade = useRef(new Animated.Value(0)).current;
  const coupleCol = bandColor(data.couple.structural_band);

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
        <Text style={[st.heroSub, { color: isDark ? "rgba(255,255,255,0.45)" : "#64748b" }]}>
          {data.couple.d9_sync_note}
        </Text>
      </LinearGradient>

      <SectionHeader title="PARTNER A" isDark={isDark} />
      <PartnerCard person={data.p1} isDark={isDark} onOpenPro={onOpenPro} />

      <SectionHeader title="PARTNER B" isDark={isDark} />
      <PartnerCard person={data.p2} isDark={isDark} onOpenPro={onOpenPro} />

      <View
        style={[
          st.proCard,
          {
            backgroundColor: isDark ? "rgba(124,58,237,0.12)" : "rgba(124,58,237,0.05)",
            borderColor: isDark ? "rgba(167,139,250,0.28)" : "rgba(124,58,237,0.15)",
          },
        ]}
      >
        <Text style={[st.proEyebrow, { color: isDark ? "#c4b5fd" : "#6d28d9" }]}>Want full consultation?</Text>
        <Text style={[st.proLead, { color: isDark ? "rgba(241,245,249,0.88)" : "#1e293b" }]}>
          Pro adds 36 Gun detail, dasha timing, synastry depth, remedies & full PDF — engine-only, no fluff.
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
  heroSub: { fontSize: 10, fontFamily: "Nunito_500Medium", textAlign: "center", marginTop: 4 },
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
  headline: { fontSize: 12, fontFamily: "Nunito_500Medium", lineHeight: 18, marginTop: 2 },
  blockTitle: { fontSize: 10, fontFamily: "Nunito_800ExtraBold", letterSpacing: 0.8, marginTop: 8 },
  bulletList: { gap: 6, marginTop: 2 },
  bulletRow: { flexDirection: "row", alignItems: "flex-start", gap: 8 },
  bulletIcon: { marginTop: 3 },
  bulletTxt: { flex: 1, fontSize: 11.5, fontFamily: "Nunito_500Medium", lineHeight: 17 },
  plainLine: { fontSize: 11.5, fontFamily: "Nunito_500Medium", lineHeight: 17, marginTop: 2 },
  lockBox: { borderRadius: 12, borderWidth: 1, padding: 10, gap: 4, marginTop: 4 },
  lockTxt: { fontSize: 11, fontFamily: "Nunito_700Bold", lineHeight: 16 },
  lockSub: { fontSize: 9, fontFamily: "Nunito_600SemiBold" },
  insightBox: { borderRadius: 12, padding: 10, gap: 4, marginTop: 4 },
  insightLabel: { fontSize: 9, fontFamily: "Nunito_800ExtraBold", letterSpacing: 0.6 },
  insightBody: { fontSize: 11, fontFamily: "Nunito_500Medium", lineHeight: 16 },
  proCard: { borderRadius: 20, borderWidth: 1, padding: 18, gap: 10, marginTop: 8 },
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
