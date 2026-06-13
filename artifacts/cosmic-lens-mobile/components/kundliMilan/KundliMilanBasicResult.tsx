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

function PartnerCard({ person, isDark }: { person: MarriagePartnerBasics; isDark: boolean }) {
  const col = bandColor(person.readiness_band);
  const genderLabel =
    person.gender === "male" ? "Male chart" : person.gender === "female" ? "Female chart" : "Chart";

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
        <View>
          <Text style={[st.partnerName, { color: isDark ? "#f3e8ff" : "#1e1b4b" }]}>{person.name}</Text>
          <Text style={[st.partnerGender, { color: isDark ? "#c4b5fd" : "#6366f1" }]}>{genderLabel}</Text>
        </View>
        <View style={[st.bandPill, { backgroundColor: `${col}20`, borderColor: `${col}40` }]}>
          <Text style={[st.bandPillTxt, { color: col }]}>{person.readiness_band}</Text>
          <Text style={[st.bandScore, { color: isDark ? "rgba(255,255,255,0.6)" : "#64748b" }]}>
            {person.readiness_score}/100
          </Text>
        </View>
      </View>

      <Text style={[st.blockTitle, { color: isDark ? "#ddd6fe" : "#4338ca" }]}>D1 Marriage Axis</Text>
      <FactRow isDark={isDark} label="7th house" value={`${person.d1.seventh_house_sign}${person.d1.planets_in_seventh.length ? ` · ${person.d1.planets_in_seventh.join(", ")}` : " · empty"}`} />
      <FactRow
        isDark={isDark}
        label="Shubh / pressure"
        value={`${person.d1.benefics_in_seventh.length} benefic · ${person.d1.malefics_in_seventh.length} malefic`}
      />
      {person.d1.aspects_on_seventh.length > 0 ? (
        <FactRow isDark={isDark} label="Aspects on 7th" value={person.d1.aspects_on_seventh.join(", ")} />
      ) : null}
      <FactRow
        isDark={isDark}
        label="7th lord"
        value={`${person.d1.seventh_lord} → ${person.d1.seventh_lord_sign ?? "?"} house ${person.d1.seventh_lord_house ?? "?"} (${person.d1.seventh_lord_strength})`}
      />
      <FactRow isDark={isDark} label="Lordship" value={person.d1.lordship_note} multiline />

      <Text style={[st.blockTitle, { color: isDark ? "#ddd6fe" : "#4338ca" }]}>D9 Married Life Base</Text>
      {person.d9.available ? (
        <>
          <FactRow isDark={isDark} label="D9 7th" value={`${person.d9.seventh_house_sign} · lord ${person.d9.seventh_lord}`} />
          <FactRow
            isDark={isDark}
            label="D9 7L placement"
            value={`${person.d9.seventh_lord_sign ?? "?"} · house ${person.d9.seventh_lord_house ?? "?"} · ${person.d9.band}`}
          />
        </>
      ) : (
        <FactRow isDark={isDark} label="D9" value="Navamsa data unavailable" />
      )}

      <Text style={[st.blockTitle, { color: isDark ? "#ddd6fe" : "#4338ca" }]}>Spouse Signature</Text>
      <FactRow isDark={isDark} label="Darakaraka" value={person.darakaraka.note} multiline />
      <FactRow
        isDark={isDark}
        label={person.karaka.role}
        value={person.karaka.note}
        multiline
      />

      {person.upapada.available ? (
        <FactRow
          isDark={isDark}
          label="Upapada"
          value={`${person.upapada.ul_sign} · lord ${person.upapada.ul_lord} · ${person.upapada.stability}`}
        />
      ) : null}

      {person.kp.available ? (
        <FactRow
          isDark={isDark}
          label="KP 7th cusp"
          value={`${person.kp.verdict} · houses ${person.kp.signified_houses.join(", ") || "—"} · depth ${person.kp.commitment_depth}`}
          multiline
        />
      ) : null}

      {person.gender_flags.length > 0 ? (
        <View style={st.flagWrap}>
          {person.gender_flags.map(f => (
            <View key={f} style={[st.flagChip, { backgroundColor: isDark ? "rgba(239,68,68,0.12)" : "rgba(239,68,68,0.08)" }]}>
              <Text style={[st.flagTxt, { color: isDark ? "#fca5a5" : "#b91c1c" }]}>{f}</Text>
            </View>
          ))}
        </View>
      ) : null}

      <View style={[st.insightBox, { backgroundColor: isDark ? "rgba(251,191,36,0.1)" : "rgba(251,191,36,0.08)" }]}>
        <Text style={[st.insightLabel, { color: isDark ? "#fde68a" : "#b45309" }]}>Friction</Text>
        <Text style={[st.insightBody, { color: isDark ? "#f8fafc" : "#334155" }]}>{person.friction}</Text>
      </View>
      <View style={[st.insightBox, { backgroundColor: isDark ? "rgba(34,197,94,0.1)" : "rgba(34,197,94,0.08)" }]}>
        <Text style={[st.insightLabel, { color: isDark ? "#86efac" : "#15803d" }]}>Remedy</Text>
        <Text style={[st.insightBody, { color: isDark ? "#f8fafc" : "#334155" }]}>{person.remedy}</Text>
      </View>
    </View>
  );
}

function FactRow({
  label,
  value,
  isDark,
  multiline,
}: {
  label: string;
  value: string;
  isDark: boolean;
  multiline?: boolean;
}) {
  return (
    <View style={st.factRow}>
      <Text style={[st.factLabel, { color: isDark ? "rgba(255,255,255,0.45)" : "#64748b" }]}>{label}</Text>
      <Text
        style={[st.factValue, { color: isDark ? "rgba(241,245,249,0.9)" : "#1e293b" }]}
        numberOfLines={multiline ? undefined : 2}
      >
        {value}
      </Text>
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
      <PartnerCard person={data.p1} isDark={isDark} />

      <SectionHeader title="PARTNER B" isDark={isDark} />
      <PartnerCard person={data.p2} isDark={isDark} />

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
  blockTitle: { fontSize: 10, fontFamily: "Nunito_800ExtraBold", letterSpacing: 0.8, marginTop: 6 },
  factRow: { gap: 2 },
  factLabel: { fontSize: 9, fontFamily: "Nunito_700Bold", letterSpacing: 0.5, textTransform: "uppercase" },
  factValue: { fontSize: 11.5, fontFamily: "Nunito_500Medium", lineHeight: 17 },
  flagWrap: { flexDirection: "row", flexWrap: "wrap", gap: 6, marginTop: 4 },
  flagChip: { borderRadius: 8, paddingHorizontal: 8, paddingVertical: 4 },
  flagTxt: { fontSize: 9, fontFamily: "Nunito_700Bold" },
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
