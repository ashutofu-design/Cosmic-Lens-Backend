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
import { MilanGunBreakdown, type MilanGunKootScores } from "@/components/kundliMilan/MilanGunBreakdown";
import type { UILang } from "@/lib/i18n";
import { milanResultScreenCopy, type CoupleBandKey, type MilanResultScreenCopy } from "@/lib/milanResultCopyI18n";

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
  gunScores?: MilanGunKootScores | null;
  gunTotal?: number | null;
  lang?: UILang;
};

type CompactPlain = {
  bandLabel: string;
  headline: string;
  positive: string;
  watchout: string;
  proLockTeaser: string;
  remedyTeaser: string;
};

function TwoLensExplainer({ isDark, text }: { isDark: boolean; text: string }) {
  return (
    <View
      style={[
        st.lensCard,
        {
          backgroundColor: isDark ? "rgba(124,58,237,0.1)" : "rgba(124,58,237,0.05)",
          borderColor: isDark ? "rgba(167,139,250,0.28)" : "rgba(124,58,237,0.14)",
        },
      ]}
    >
      <Feather name="info" size={14} color={isDark ? "#c4b5fd" : "#7c3aed"} />
      <Text style={[st.lensTxt, { color: isDark ? "rgba(241,245,249,0.88)" : "#475569", flex: 1 }]}>
        {text}
      </Text>
    </View>
  );
}

function SectionHeader({ title, isDark }: { title: string; isDark: boolean }) {
  return (
    <View style={st.sectionHead}>
      <Text style={[st.sectionTitle, { color: isDark ? "#e9d5ff" : "#5b21b6" }]}>{title}</Text>
      <View style={[st.sectionLine, { backgroundColor: isDark ? "rgba(167,139,250,0.22)" : "rgba(91,33,182,0.12)" }]} />
    </View>
  );
}

function resolveCompactPlain(person: MarriagePartnerBasics, copy: MilanResultScreenCopy): CompactPlain {
  const pc = person.plain_copy;
  if (pc?.headline && pc.positives?.length) {
    const alertTeaser =
      person.critical_alerts?.locked && person.critical_alerts.teaser
        ? `${person.critical_alerts.teaser} — ${copy.proDetailSuffix}`
        : null;
    return {
      bandLabel: pc.band_label,
      headline: pc.headline,
      positive: pc.positives[0] ?? copy.fallbackPositive,
      watchout: pc.watchouts[0] ?? copy.fallbackWatchout,
      proLockTeaser: pc.pro_lock_teaser ?? alertTeaser ?? copy.fallbackProLock,
      remedyTeaser: pc.remedy_teaser ?? copy.fallbackRemedy,
    };
  }
  const fb = buildPartnerPlainView(person);
  return {
    bandLabel: fb.bandLabel,
    headline: fb.headline,
    positive: fb.positives[0] ?? copy.fallbackPositive,
    watchout: fb.watchouts[0] ?? copy.fallbackWatchout,
    proLockTeaser: person.critical_alerts?.teaser
      ? `${person.critical_alerts.teaser} — ${copy.proDetailSuffix}`
      : copy.fallbackProLock,
    remedyTeaser: copy.fallbackRemedy,
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

function PartnerCard({
  person,
  isDark,
  onOpenPro,
  copy,
}: {
  person: MarriagePartnerBasics;
  isDark: boolean;
  onOpenPro: () => void;
  copy: MilanResultScreenCopy;
}) {
  const col = bandColor(person.readiness_band);
  const plain = resolveCompactPlain(person, copy);
  const genderLabel =
    person.gender === "male" ? copy.genderMale : person.gender === "female" ? copy.genderFemale : copy.genderChart;

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
        <Text style={[st.lockSub, { color: isDark ? "rgba(255,255,255,0.5)" : "#64748b" }]}>{copy.unlockInPro}</Text>
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

function CoupleGapCard({
  copy,
  coupleCopy,
  isDark,
  onOpenPro,
}: {
  copy: MilanResultScreenCopy;
  coupleCopy: CouplePlainCopy;
  isDark: boolean;
  onOpenPro: () => void;
}) {
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
      <Text style={[st.gapEyebrow, { color: isDark ? "#fde68a" : "#b45309" }]}>{copy.coupleGapEyebrow}</Text>
      <Text style={[st.gapBody, { color: isDark ? "rgba(241,245,249,0.9)" : "#334155" }]}>{coupleCopy.gap_teaser}</Text>
      {(coupleCopy.locked_highlights ?? []).map(item => (
        <View key={item} style={st.gapRow}>
          <Feather name="lock" size={10} color={isDark ? "#fcd34d" : "#d97706"} />
          <Text style={[st.gapItem, { color: isDark ? "rgba(255,255,255,0.55)" : "#64748b" }]}>{item}</Text>
        </View>
      ))}
      <Pressable onPress={onOpenPro} style={({ pressed }) => ({ opacity: pressed ? 0.88 : 1 })}>
        <LinearGradient colors={["#6366F1", "#8B5CF6", "#db2777"]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }} style={st.gapBtn}>
          <Text style={st.gapBtnTxt}>{coupleCopy.pro_cta_line}</Text>
          <Feather name="arrow-right" size={14} color="#fff" />
        </LinearGradient>
      </Pressable>
    </View>
  );
}

function defaultCoupleGap(data: MarriageBasicsPayload, copy: MilanResultScreenCopy): CouplePlainCopy {
  const alerts = data.couple.critical_alerts_total ?? 0;
  const highlights: string[] = [];
  if (alerts > 0) highlights.push(copy.lockedHighlights.alerts(alerts));
  if (data.couple.synastry?.available) highlights.push(copy.lockedHighlights.synastry);
  if (data.couple.manglik?.p1_has_dosh || data.couple.manglik?.p2_has_dosh) {
    highlights.push(copy.lockedHighlights.manglik);
  }
  highlights.push(copy.lockedHighlights.dasha);
  highlights.push(copy.lockedHighlights.pdf);

  return {
    gap_teaser: copy.defaultGapTeaser(data.couple.structural_score),
    pro_cta_line: copy.defaultGapCta,
    locked_highlights: highlights.slice(0, 4),
  };
}

const GUN_COPY_RE = /36\s*gun|ashtakoot|guna\s*milan|full\s*score\s*breakdown/i;

/** Strip legacy Gun Milan lines from API copy (old server builds). */
function resolveCoupleCopy(data: MarriageBasicsPayload, copy: MilanResultScreenCopy): CouplePlainCopy {
  const fallback = defaultCoupleGap(data, copy);
  const api = data.couple.plain_copy;
  if (!api) return fallback;

  const rawHighlights = api.locked_highlights ?? [];
  const cleaned = rawHighlights.filter(line => !GUN_COPY_RE.test(line));
  const highlights =
    cleaned.length > 0
      ? cleaned.slice(0, 4)
      : (fallback.locked_highlights ?? []).slice(0, 4);

  if (cleaned.length < 4 && cleaned.length < rawHighlights.length) {
    for (const line of fallback.locked_highlights ?? []) {
      if (highlights.length >= 4) break;
      if (!highlights.includes(line)) highlights.push(line);
    }
  }

  return {
    gap_teaser: GUN_COPY_RE.test(api.gap_teaser ?? "") ? fallback.gap_teaser : (api.gap_teaser || fallback.gap_teaser),
    pro_cta_line: GUN_COPY_RE.test(api.pro_cta_line ?? "") ? fallback.pro_cta_line : (api.pro_cta_line || fallback.pro_cta_line),
    alert_count: api.alert_count,
    locked_highlights: highlights.slice(0, 4),
  };
}

function localizeCoupleBand(band: string, copy: MilanResultScreenCopy): string {
  return copy.coupleBands[band as CoupleBandKey] ?? band;
}

function localizeFutureVerdict(band: string, apiVerdict: string, copy: MilanResultScreenCopy): string {
  const localized = copy.coupleVerdict[band as CoupleBandKey];
  if (!localized) return apiVerdict;
  // Prefer API text when server already localized (Devanagari for hi).
  if (/[\u0900-\u097F]/.test(apiVerdict)) return apiVerdict;
  return localized;
}

export function KundliMilanBasicResult({ data, isDark, onOpenPro, gunScores, gunTotal, lang = "en" }: Props) {
  const copy = milanResultScreenCopy(lang);
  const fade = useRef(new Animated.Value(0)).current;
  const coupleCol = bandColor(data.couple.structural_band);
  const coupleCopy = resolveCoupleCopy(data, copy);
  const coupleBandLabel =
    (data.couple as { structural_band_label?: string }).structural_band_label ??
    localizeCoupleBand(data.couple.structural_band, copy);
  const futureVerdict = localizeFutureVerdict(data.couple.structural_band, data.couple.future_verdict, copy);
  const p1Strip = data.p1.plain_copy?.pro_strip ?? copy.fallbackProStrip(data.p1.name);

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
        <Text style={[st.heroEyebrow, { color: isDark ? "#c4b5fd" : "#6366f1" }]}>{copy.basicMode}</Text>
        <Text style={[st.heroEyebrow, { color: isDark ? "#a78bfa" : "#6366f1", marginTop: 4 }]}>
          {copy.primaryBadge} · {copy.structureTitle.toUpperCase()}
        </Text>
        <Text style={[st.heroSub, { color: isDark ? "rgba(255,255,255,0.55)" : "#64748b" }]}>
          {copy.structureSubtitle}
        </Text>
        <Text style={[st.heroScore, { color: coupleCol }]}>{data.couple.structural_score}</Text>
        <Text style={[st.heroDenom, { color: isDark ? "rgba(255,255,255,0.5)" : "#64748b" }]}>/ 100</Text>
        <View style={[st.heroBand, { backgroundColor: `${coupleCol}22`, borderColor: `${coupleCol}44` }]}>
          <Text style={[st.heroBandTxt, { color: coupleCol }]}>{coupleBandLabel}</Text>
        </View>
        <Text style={[st.heroVerdict, { color: isDark ? "rgba(241,245,249,0.9)" : "#334155" }]}>
          {futureVerdict}
        </Text>
      </LinearGradient>

      {gunScores ? (
        <TwoLensExplainer isDark={isDark} text={copy.twoLensExplainer} />
      ) : null}

      {gunScores ? (
        <MilanGunBreakdown
          scores={gunScores}
          total={gunTotal ?? null}
          isDark={isDark}
          textColor={isDark ? "#f8fafc" : "#0f172a"}
          mutedColor={isDark ? "rgba(255,255,255,0.55)" : "#64748b"}
          copy={copy}
        />
      ) : null}

      <SectionHeader title={copy.partnerA} isDark={isDark} />
      <PartnerCard person={data.p1} isDark={isDark} onOpenPro={onOpenPro} copy={copy} />
      <ProMiniStrip text={p1Strip} isDark={isDark} onOpenPro={onOpenPro} />

      <SectionHeader title={copy.partnerB} isDark={isDark} />
      <PartnerCard person={data.p2} isDark={isDark} onOpenPro={onOpenPro} copy={copy} />

      <CoupleGapCard copy={copy} coupleCopy={coupleCopy} isDark={isDark} onOpenPro={onOpenPro} />
    </Animated.View>
  );
}

const st = StyleSheet.create({
  wrap: { gap: 12, marginTop: 4 },
  heroCard: { borderRadius: 22, borderWidth: 1.5, padding: 20, alignItems: "center", gap: 6 },
  heroEyebrow: { fontSize: 9, fontFamily: "Nunito_800ExtraBold", letterSpacing: 1.4 },
  heroSub: { fontSize: 11, fontFamily: "Nunito_500Medium", textAlign: "center", lineHeight: 16, marginTop: 2, paddingHorizontal: 8 },
  heroScore: { fontSize: 44, fontFamily: "Nunito_800ExtraBold", lineHeight: 48 },
  lensCard: { flexDirection: "row", alignItems: "flex-start", gap: 10, borderWidth: 1, borderRadius: 14, padding: 12 },
  lensTxt: { fontSize: 11, fontFamily: "Nunito_500Medium", lineHeight: 17 },
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
});
