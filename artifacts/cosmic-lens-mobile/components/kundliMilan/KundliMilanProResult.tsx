import { Feather } from "@expo/vector-icons";
import { LinearGradient } from "expo-linear-gradient";
import React from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";
import {
  bandColor,
  type MarriageBasicsPayload,
  type MarriagePartnerBasics,
} from "@/lib/milanMarriageBasics";

type Props = {
  data: MarriageBasicsPayload;
  isDark: boolean;
  pdfLoading: boolean;
  onDownloadPdf: () => void;
};

function SectionHeader({ title, isDark }: { title: string; isDark: boolean }) {
  return (
    <View style={st.sectionHead}>
      <Text style={[st.sectionTitle, { color: isDark ? "#e9d5ff" : "#5b21b6" }]}>{title}</Text>
      <View style={[st.sectionLine, { backgroundColor: isDark ? "rgba(167,139,250,0.22)" : "rgba(91,33,182,0.12)" }]} />
    </View>
  );
}

function ProPartnerCard({ person, isDark }: { person: MarriagePartnerBasics; isDark: boolean }) {
  const col = bandColor(person.readiness_band);
  const pc = person.plain_copy;
  const positives = pc?.positives?.length
    ? person.strengths?.length
      ? [...pc.positives, ...person.strengths.slice(0, 2)]
      : pc.positives
    : (person.strengths ?? []).slice(0, 3);
  const watchouts = pc?.watchouts?.length
    ? person.pressures?.length
      ? [...pc.watchouts, ...person.pressures.slice(0, 2)]
      : pc.watchouts
    : (person.pressures ?? []).slice(0, 3);

  return (
    <View
      style={[
        st.card,
        {
          backgroundColor: isDark ? "rgba(255,255,255,0.04)" : "#fff",
          borderColor: isDark ? `${col}35` : `${col}25`,
        },
      ]}
    >
      <View style={st.rowHead}>
        <Text style={[st.name, { color: isDark ? "#f3e8ff" : "#1e1b4b" }]}>{person.name}</Text>
        <View style={[st.pill, { backgroundColor: `${col}20`, borderColor: `${col}40` }]}>
          <Text style={[st.pillTxt, { color: col }]}>{pc?.band_label ?? person.readiness_band}</Text>
          <Text style={[st.pillScore, { color: isDark ? "rgba(255,255,255,0.55)" : "#64748b" }]}>
            {person.readiness_score}/100
          </Text>
        </View>
      </View>

      {pc?.headline ? (
        <Text style={[st.lead, { color: isDark ? "rgba(241,245,249,0.85)" : "#475569" }]}>{pc.headline}</Text>
      ) : null}

      {positives.slice(0, 3).map((line, i) => (
        <View key={`p-${i}`} style={st.bulletRow}>
          <Feather name="check" size={11} color={isDark ? "#86efac" : "#15803d"} />
          <Text style={[st.body, { color: isDark ? "#f8fafc" : "#334155" }]}>{line}</Text>
        </View>
      ))}

      {watchouts.slice(0, 3).map((line, i) => (
        <View key={`w-${i}`} style={st.bulletRow}>
          <Feather name="alert-circle" size={11} color={isDark ? "#fca5a5" : "#dc2626"} />
          <Text style={[st.body, { color: isDark ? "#f8fafc" : "#334155" }]}>{line}</Text>
        </View>
      ))}

      {(person.critical_alerts?.detail ?? []).length > 0 ? (
        <View style={[st.unlockBox, { backgroundColor: isDark ? "rgba(239,68,68,0.1)" : "rgba(239,68,68,0.06)" }]}>
          <Text style={[st.unlockLbl, { color: isDark ? "#fca5a5" : "#b91c1c" }]}>Hidden alerts — unlocked</Text>
          {person.critical_alerts!.detail!.map(a => (
            <Text key={a.id} style={[st.body, { color: isDark ? "#fecaca" : "#991b1b" }]}>
              • {a.label}
            </Text>
          ))}
        </View>
      ) : null}

      <View style={[st.box, { backgroundColor: isDark ? "rgba(251,191,36,0.1)" : "rgba(251,191,36,0.08)" }]}>
        <Text style={[st.boxLbl, { color: isDark ? "#fde68a" : "#b45309" }]}>Main friction</Text>
        <Text style={[st.body, { color: isDark ? "#f8fafc" : "#334155" }]}>
          {pc?.friction ?? person.friction}
        </Text>
      </View>
      <View style={[st.box, { backgroundColor: isDark ? "rgba(34,197,94,0.1)" : "rgba(34,197,94,0.08)" }]}>
        <Text style={[st.boxLbl, { color: isDark ? "#86efac" : "#15803d" }]}>Full remedy</Text>
        <Text style={[st.body, { color: isDark ? "#f8fafc" : "#334155" }]}>
          {pc?.remedy ?? person.remedy}
        </Text>
      </View>
    </View>
  );
}

export function KundliMilanProResult({ data, isDark, pdfLoading, onDownloadPdf }: Props) {
  const coupleCol = bandColor(data.couple.structural_band);
  const couple = data.couple;

  return (
    <View style={st.wrap}>
      <LinearGradient
        colors={isDark ? ["#1a0533", "#0f172a"] : ["#f5f3ff", "#ede9fe"]}
        style={[st.hero, { borderColor: isDark ? `${coupleCol}50` : `${coupleCol}35` }]}
      >
        <Text style={[st.eyebrow, { color: isDark ? "#c4b5fd" : "#6366f1" }]}>PRO · MARRIAGE ENGINE READ</Text>
        <Text style={[st.score, { color: coupleCol }]}>{couple.structural_score}</Text>
        <Text style={[st.denom, { color: isDark ? "rgba(255,255,255,0.5)" : "#64748b" }]}>/ 100 · {couple.structural_band}</Text>
        <Text style={[st.verdict, { color: isDark ? "rgba(241,245,249,0.9)" : "#334155" }]}>{couple.future_verdict}</Text>
      </LinearGradient>

      <SectionHeader title="PARTNER A" isDark={isDark} />
      <ProPartnerCard person={data.p1} isDark={isDark} />

      <SectionHeader title="PARTNER B" isDark={isDark} />
      <ProPartnerCard person={data.p2} isDark={isDark} />

      <SectionHeader title="TOGETHER — FULL READ" isDark={isDark} />
      <View style={[st.card, { backgroundColor: isDark ? "rgba(255,255,255,0.04)" : "#fff", borderColor: isDark ? "rgba(167,139,250,0.25)" : "rgba(124,58,237,0.15)" }]}>
        {couple.plain_copy?.gap_teaser ? (
          <Text style={[st.lead, { color: isDark ? "#f8fafc" : "#334155" }]}>{couple.plain_copy.gap_teaser}</Text>
        ) : null}
        {couple.synastry?.summary ? (
          <Text style={[st.body, { color: isDark ? "rgba(255,255,255,0.75)" : "#475569" }]}>
            Synastry: {couple.synastry.summary}
          </Text>
        ) : null}
        {couple.d9_sync_note ? (
          <Text style={[st.body, { color: isDark ? "rgba(255,255,255,0.75)" : "#475569" }]}>{couple.d9_sync_note}</Text>
        ) : null}
        {couple.manglik?.note ? (
          <Text style={[st.body, { color: isDark ? "rgba(255,255,255,0.75)" : "#475569" }]}>Manglik: {couple.manglik.note}</Text>
        ) : null}
        {couple.graha_maitri?.note ? (
          <Text style={[st.body, { color: isDark ? "rgba(255,255,255,0.75)" : "#475569" }]}>{couple.graha_maitri.note}</Text>
        ) : null}
        {couple.kp_couple?.couple_verdict ? (
          <Text style={[st.body, { color: isDark ? "rgba(255,255,255,0.75)" : "#475569" }]}>
            KP couple: {couple.kp_couple.couple_verdict}
          </Text>
        ) : null}
      </View>

      <Pressable onPress={onDownloadPdf} disabled={pdfLoading} style={({ pressed }) => ({ opacity: pressed || pdfLoading ? 0.88 : 1 })}>
        <LinearGradient colors={["#6366F1", "#8B5CF6", "#db2777"]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }} style={st.pdfBtn}>
          <Feather name="download" size={16} color="#fff" />
          <Text style={st.pdfBtnTxt}>{pdfLoading ? "PDF generate ho raha hai…" : "Download Full Pro PDF"}</Text>
        </LinearGradient>
      </Pressable>
    </View>
  );
}

const st = StyleSheet.create({
  wrap: { gap: 12, marginTop: 4, marginBottom: 12 },
  hero: { borderRadius: 22, borderWidth: 1.5, padding: 20, alignItems: "center", gap: 6 },
  eyebrow: { fontSize: 9, fontFamily: "Nunito_800ExtraBold", letterSpacing: 1.4 },
  score: { fontSize: 44, fontFamily: "Nunito_800ExtraBold", lineHeight: 48 },
  denom: { fontSize: 12, fontFamily: "Nunito_600SemiBold", marginTop: -6 },
  verdict: { fontSize: 13, fontFamily: "Nunito_500Medium", textAlign: "center", lineHeight: 20, marginTop: 8 },
  sectionHead: { flexDirection: "row", alignItems: "center", gap: 10, marginTop: 6 },
  sectionTitle: { fontSize: 10, fontFamily: "Nunito_800ExtraBold", letterSpacing: 1.4 },
  sectionLine: { flex: 1, height: 1 },
  card: { borderRadius: 18, borderWidth: 1, padding: 14, gap: 8 },
  rowHead: { flexDirection: "row", justifyContent: "space-between", alignItems: "flex-start", gap: 10 },
  name: { fontSize: 16, fontFamily: "Nunito_800ExtraBold", flex: 1 },
  pill: { borderWidth: 1, borderRadius: 12, paddingHorizontal: 10, paddingVertical: 6, alignItems: "center" },
  pillTxt: { fontSize: 11, fontFamily: "Nunito_800ExtraBold" },
  pillScore: { fontSize: 9, fontFamily: "Nunito_600SemiBold", marginTop: 2 },
  lead: { fontSize: 12, fontFamily: "Nunito_500Medium", lineHeight: 18 },
  bulletRow: { flexDirection: "row", alignItems: "flex-start", gap: 8 },
  body: { flex: 1, fontSize: 11.5, fontFamily: "Nunito_500Medium", lineHeight: 17 },
  unlockBox: { borderRadius: 12, padding: 10, gap: 4 },
  unlockLbl: { fontSize: 9, fontFamily: "Nunito_800ExtraBold", letterSpacing: 0.6 },
  box: { borderRadius: 12, padding: 10, gap: 4 },
  boxLbl: { fontSize: 9, fontFamily: "Nunito_800ExtraBold", letterSpacing: 0.6 },
  pdfBtn: { flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 8, borderRadius: 14, paddingVertical: 15, marginTop: 4 },
  pdfBtnTxt: { color: "#fff", fontSize: 14, fontFamily: "Nunito_800ExtraBold" },
});
