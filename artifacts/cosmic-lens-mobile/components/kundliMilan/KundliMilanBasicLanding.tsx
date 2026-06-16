import { Feather } from "@expo/vector-icons";
import * as Haptics from "expo-haptics";
import { LinearGradient } from "expo-linear-gradient";
import React from "react";
import {
  ActivityIndicator,
  I18nManager,
  Pressable,
  StyleSheet,
  Text,
  View,
} from "react-native";
import type { UILang } from "@/lib/i18n";
import { MILAN_KOOT_DISPLAY } from "@/lib/milanKootDisplay";
import { milanResultScreenCopy } from "@/lib/milanResultCopyI18n";

export type AstroPreview = {
  moonSign: string;
  nakshatra: string;
};

type Props = {
  isDark: boolean;
  textColor: string;
  mutedColor: string;
  youLabel: string;
  matchingWithLabel: string;
  person1Name: string;
  partnerName?: string | null;
  person1Astro?: AstroPreview | null;
  partnerAstro?: AstroPreview | null;
  hasPartner: boolean;
  canCalculate: boolean;
  calcLoading: boolean;
  lang?: UILang;
  onSelectPartner: () => void;
  onEditPartner: () => void;
  onCalculate: () => void;
  onOpenPro?: () => void;
};

function BenefitRow({ text, isDark, accent }: { text: string; isDark: boolean; accent: string }) {
  return (
    <View style={st.benefitRow}>
      <View style={[st.benefitDot, { backgroundColor: isDark ? "rgba(34,197,94,0.2)" : "rgba(22,163,74,0.12)" }]}>
        <Feather name="check" size={11} color={isDark ? "#86efac" : "#15803d"} />
      </View>
      <Text style={[st.benefitTxt, { color: isDark ? "rgba(241,245,249,0.9)" : "#334155" }]}>{text}</Text>
    </View>
  );
}

function KootChipPreview({
  emoji,
  title,
  isDark,
  accent,
}: {
  emoji: string;
  title: string;
  isDark: boolean;
  accent: string;
}) {
  return (
    <View
      style={[
        st.kootChip,
        {
          backgroundColor: isDark ? "rgba(255,255,255,0.04)" : "rgba(99,102,241,0.04)",
          borderColor: isDark ? "rgba(167,139,250,0.2)" : "rgba(99,102,241,0.14)",
        },
      ]}
    >
      <Text style={{ fontSize: 12 }}>{emoji}</Text>
      <Text style={[st.kootChipTxt, { color: isDark ? accent : "#4338ca" }]} numberOfLines={1}>
        {title}
      </Text>
      <Feather name="lock" size={9} color={isDark ? "rgba(255,255,255,0.28)" : "#94a3b8"} />
    </View>
  );
}

export function KundliMilanBasicLanding({
  isDark,
  textColor,
  mutedColor,
  youLabel,
  matchingWithLabel,
  person1Name,
  partnerName,
  person1Astro,
  partnerAstro,
  hasPartner,
  canCalculate,
  calcLoading,
  lang = "en",
  onSelectPartner,
  onEditPartner,
  onCalculate,
  onOpenPro,
}: Props) {
  const copy = milanResultScreenCopy(lang);
  const landing = copy.landing;
  const accent = isDark ? "#a78bfa" : "#6366f1";
  const cardBg = isDark ? "rgba(255,255,255,0.04)" : "#ffffff";
  const cardBorder = isDark ? "rgba(167,139,250,0.18)" : "rgba(99,102,241,0.12)";
  const showAstro = hasPartner && person1Astro?.moonSign && partnerAstro?.moonSign;

  const fmtAstro = (a: AstroPreview) => landing.rashiNakshatra(a.moonSign, a.nakshatra);

  return (
    <View style={st.wrap}>
      <View style={[st.hero, { backgroundColor: cardBg, borderColor: cardBorder }]}>
        <LinearGradient
          colors={isDark ? ["rgba(99,102,241,0.14)", "transparent"] : ["rgba(99,102,241,0.08)", "transparent"]}
          style={[StyleSheet.absoluteFill, { borderRadius: 20 }]}
        />
        <Text style={[st.heroTitle, { color: textColor }]}>{landing.title}</Text>
        <Text style={[st.heroSub, { color: mutedColor }]}>{landing.subtitle}</Text>
        <View
          style={[
            st.modePill,
            {
              backgroundColor: isDark ? "rgba(99,102,241,0.14)" : "rgba(99,102,241,0.08)",
              borderColor: isDark ? "rgba(167,139,250,0.35)" : "rgba(99,102,241,0.22)",
              marginTop: 4,
            },
          ]}
        >
          <Text style={[st.modePillTxt, { color: accent }]}>{copy.basicMode}</Text>
        </View>
      </View>

      {hasPartner ? (
        <View
          style={[
            st.partnerRow,
            {
              backgroundColor: isDark ? "rgba(99,102,241,0.1)" : "rgba(99,102,241,0.06)",
              borderColor: isDark ? "rgba(167,139,250,0.28)" : "rgba(99,102,241,0.2)",
            },
          ]}
        >
          <View style={[st.partnerIcon, { backgroundColor: isDark ? "rgba(99,102,241,0.18)" : "rgba(99,102,241,0.12)" }]}>
            <Text style={{ fontSize: 16 }}>💑</Text>
          </View>
          <View style={{ flex: 1 }}>
            <Text style={[st.partnerEyebrow, { color: mutedColor }]}>{matchingWithLabel}</Text>
            <Text style={[st.partnerNames, { color: textColor }]} numberOfLines={1}>
              {person1Name}  ✦  {partnerName}
            </Text>
            {canCalculate ? (
              <Text style={[st.partnerReady, { color: accent }]}>{landing.chartsReady}</Text>
            ) : null}
          </View>
          <Pressable onPress={onEditPartner} hitSlop={8} style={({ pressed }) => ({ opacity: pressed ? 0.6 : 1, padding: 6 })}>
            <Feather name="edit-2" size={14} color={accent} />
          </Pressable>
        </View>
      ) : (
        <Pressable
          onPress={() => {
            Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
            onSelectPartner();
          }}
          style={({ pressed }) => ({
            opacity: pressed ? 0.88 : 1,
            backgroundColor: isDark ? "rgba(99,102,241,0.08)" : "rgba(99,102,241,0.04)",
            borderWidth: 1,
            borderStyle: "dashed",
            borderColor: isDark ? "rgba(167,139,250,0.35)" : "rgba(99,102,241,0.28)",
            borderRadius: 16,
            padding: 16,
          })}
        >
          <View style={{ flexDirection: "row", alignItems: "center", gap: 12 }}>
            <View style={[st.partnerIcon, { backgroundColor: isDark ? "rgba(99,102,241,0.18)" : "rgba(99,102,241,0.1)" }]}>
              <Text style={{ fontSize: 18 }}>💑</Text>
            </View>
            <View style={{ flex: 1 }}>
              <Text style={[st.selectTitle, { color: textColor }]}>{landing.selectPartner}</Text>
              <Text style={[st.selectSub, { color: mutedColor }]}>{landing.selectPartnerSub}</Text>
            </View>
            <Feather name={I18nManager.isRTL ? "arrow-left" : "arrow-right"} size={18} color={accent} />
          </View>
        </Pressable>
      )}

      {showAstro ? (
        <View style={st.astroRow}>
          <View
            style={[
              st.astroCard,
              {
                backgroundColor: isDark ? "rgba(99,102,241,0.08)" : "rgba(99,102,241,0.04)",
                borderColor: isDark ? "rgba(167,139,250,0.22)" : "rgba(99,102,241,0.14)",
              },
            ]}
          >
            <Text style={[st.astroEyebrow, { color: mutedColor }]}>{landing.youAstroLabel}</Text>
            <Text style={[st.astroVal, { color: textColor }]} numberOfLines={2}>
              {fmtAstro(person1Astro!)}
            </Text>
          </View>
          <View
            style={[
              st.astroCard,
              {
                backgroundColor: isDark ? "rgba(219,39,119,0.08)" : "rgba(219,39,119,0.04)",
                borderColor: isDark ? "rgba(244,114,182,0.22)" : "rgba(219,39,119,0.14)",
              },
            ]}
          >
            <Text style={[st.astroEyebrow, { color: mutedColor }]}>{landing.partnerAstroLabel}</Text>
            <Text style={[st.astroVal, { color: textColor }]} numberOfLines={2}>
              {fmtAstro(partnerAstro!)}
            </Text>
          </View>
        </View>
      ) : null}

      <View
        style={[
          st.kootPreviewCard,
          {
            backgroundColor: isDark ? "rgba(14,116,144,0.06)" : "rgba(240,249,255,0.7)",
            borderColor: isDark ? "rgba(56,189,248,0.18)" : "rgba(14,165,233,0.14)",
          },
        ]}
      >
        <Text style={[st.kootPreviewHdr, { color: isDark ? "#7dd3fc" : "#0369a1" }]}>{landing.kootPreviewLabel}</Text>
        <View style={st.kootGrid}>
          {MILAN_KOOT_DISPLAY.map(def => (
            <KootChipPreview
              key={def.key}
              emoji={def.emoji}
              title={copy.kootTitles[def.key]}
              isDark={isDark}
              accent={accent}
            />
          ))}
        </View>
      </View>

      <View
        style={[
          st.benefitCard,
          {
            backgroundColor: isDark ? "rgba(124,58,237,0.08)" : "rgba(124,58,237,0.04)",
            borderColor: isDark ? "rgba(167,139,250,0.22)" : "rgba(124,58,237,0.12)",
          },
        ]}
      >
        <Text style={[st.benefitHdr, { color: isDark ? "#c4b5fd" : "#5b21b6" }]}>{landing.whatYouGetTitle}</Text>
        <BenefitRow text={landing.benefitStructure} isDark={isDark} accent={accent} />
        <BenefitRow text={landing.benefitGun} isDark={isDark} accent={accent} />
        <BenefitRow text={landing.benefitPartners} isDark={isDark} accent={accent} />
      </View>

      <View
        style={[
          st.lensNote,
          {
            backgroundColor: isDark ? "rgba(124,58,237,0.06)" : "rgba(124,58,237,0.03)",
            borderColor: isDark ? "rgba(167,139,250,0.15)" : "rgba(124,58,237,0.1)",
          },
        ]}
      >
        <Feather name="info" size={12} color={isDark ? "#c4b5fd" : "#7c3aed"} />
        <Text style={[st.lensNoteTxt, { color: mutedColor }]}>{landing.lensNoteShort}</Text>
      </View>

      <Pressable
        onPress={onCalculate}
        disabled={!canCalculate || calcLoading}
        style={({ pressed }) => ({ opacity: !canCalculate ? 0.5 : pressed ? 0.92 : 1 })}
      >
        <LinearGradient
          colors={canCalculate ? ["#6366f1", "#7c3aed", "#8b5cf6"] : ["#64748b", "#475569"]}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 0 }}
          style={st.ctaBtn}
        >
          {calcLoading ? (
            <ActivityIndicator color="#fff" />
          ) : (
            <>
              <Feather name="heart" size={18} color="#fff" />
              <Text style={st.ctaTxt}>{landing.checkBtn}</Text>
            </>
          )}
        </LinearGradient>
      </Pressable>
      <Text style={[st.ctaHint, { color: mutedColor }]}>
        {!hasPartner ? landing.hintNoPartner(youLabel) : landing.hintReady}
      </Text>

      {onOpenPro ? (
        <Pressable onPress={onOpenPro} style={({ pressed }) => ({ opacity: pressed ? 0.75 : 1 })}>
          <Text style={[st.proTeaser, { color: mutedColor }]}>{landing.proTeaser}</Text>
        </Pressable>
      ) : null}
    </View>
  );
}

const st = StyleSheet.create({
  wrap: { gap: 14 },
  hero: { borderRadius: 20, borderWidth: 1, padding: 18, alignItems: "center", gap: 8, overflow: "hidden" },
  heroTitle: { fontSize: 20, fontFamily: "Nunito_800ExtraBold", letterSpacing: -0.3 },
  heroSub: { fontSize: 12, fontFamily: "Nunito_500Medium", textAlign: "center", lineHeight: 18, maxWidth: 320 },
  modePill: { borderWidth: 1, borderRadius: 20, paddingHorizontal: 12, paddingVertical: 5 },
  modePillTxt: { fontSize: 11, fontFamily: "Nunito_800ExtraBold", letterSpacing: 0.6 },
  partnerRow: { flexDirection: "row", alignItems: "center", gap: 10, borderWidth: 1, borderRadius: 14, paddingHorizontal: 12, paddingVertical: 11 },
  partnerIcon: { width: 36, height: 36, borderRadius: 12, alignItems: "center", justifyContent: "center" },
  partnerEyebrow: { fontSize: 9, fontFamily: "Nunito_700Bold", letterSpacing: 0.8, textTransform: "uppercase" },
  partnerNames: { fontSize: 13, fontFamily: "Nunito_800ExtraBold", marginTop: 2 },
  partnerReady: { fontSize: 10, fontFamily: "Nunito_700Bold", marginTop: 4 },
  selectTitle: { fontSize: 14, fontFamily: "Nunito_800ExtraBold" },
  selectSub: { fontSize: 11, fontFamily: "Nunito_500Medium", marginTop: 3, lineHeight: 15 },
  astroRow: { flexDirection: "row", gap: 10 },
  astroCard: { flex: 1, borderWidth: 1, borderRadius: 14, padding: 12, gap: 4 },
  astroEyebrow: { fontSize: 9, fontFamily: "Nunito_700Bold", letterSpacing: 0.6, textTransform: "uppercase" },
  astroVal: { fontSize: 12, fontFamily: "Nunito_700Bold", lineHeight: 17 },
  kootPreviewCard: { borderRadius: 16, borderWidth: 1, padding: 12, gap: 10 },
  kootPreviewHdr: { fontSize: 9, fontFamily: "Nunito_800ExtraBold", letterSpacing: 1.1 },
  kootGrid: { flexDirection: "row", flexWrap: "wrap", gap: 6 },
  kootChip: {
    flexDirection: "row",
    alignItems: "center",
    gap: 5,
    borderWidth: 1,
    borderRadius: 999,
    paddingHorizontal: 9,
    paddingVertical: 5,
    maxWidth: "48%",
    flexGrow: 1,
    flexBasis: "46%",
  },
  kootChipTxt: { flex: 1, fontSize: 9.5, fontFamily: "Nunito_700Bold" },
  benefitCard: { borderRadius: 16, borderWidth: 1, padding: 14, gap: 10 },
  benefitHdr: { fontSize: 9, fontFamily: "Nunito_800ExtraBold", letterSpacing: 1.1, marginBottom: 2 },
  benefitRow: { flexDirection: "row", alignItems: "flex-start", gap: 10 },
  benefitDot: { width: 20, height: 20, borderRadius: 10, alignItems: "center", justifyContent: "center", marginTop: 1 },
  benefitTxt: { flex: 1, fontSize: 12, fontFamily: "Nunito_600SemiBold", lineHeight: 18 },
  lensNote: { flexDirection: "row", alignItems: "flex-start", gap: 8, borderWidth: 1, borderRadius: 12, padding: 10 },
  lensNoteTxt: { flex: 1, fontSize: 10.5, fontFamily: "Nunito_500Medium", lineHeight: 16 },
  ctaBtn: { flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 10, paddingVertical: 17, borderRadius: 16, shadowColor: "#6366f1", shadowOpacity: 0.35, shadowRadius: 14, shadowOffset: { width: 0, height: 6 }, elevation: 6 },
  ctaTxt: { color: "#fff", fontSize: 17, fontFamily: "Nunito_800ExtraBold", letterSpacing: 0.3 },
  ctaHint: { fontSize: 11, fontFamily: "Nunito_500Medium", textAlign: "center", marginTop: 8 },
  proTeaser: { fontSize: 11, fontFamily: "Nunito_600SemiBold", textAlign: "center", marginTop: 4 },
});
