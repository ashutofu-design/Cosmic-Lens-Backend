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

type Props = {
  isDark: boolean;
  textColor: string;
  mutedColor: string;
  youLabel: string;
  matchingWithLabel: string;
  person1Name: string;
  partnerName?: string | null;
  hasPartner: boolean;
  canCalculate: boolean;
  calcLoading: boolean;
  onSelectPartner: () => void;
  onEditPartner: () => void;
  onCalculate: () => void;
};

export function KundliMilanBasicLanding({
  isDark,
  textColor,
  mutedColor,
  youLabel,
  matchingWithLabel,
  person1Name,
  partnerName,
  hasPartner,
  canCalculate,
  calcLoading,
  onSelectPartner,
  onEditPartner,
  onCalculate,
}: Props) {
  const accent = isDark ? "#a78bfa" : "#6366f1";
  const cardBg = isDark ? "rgba(255,255,255,0.04)" : "#ffffff";
  const cardBorder = isDark ? "rgba(167,139,250,0.18)" : "rgba(99,102,241,0.12)";

  return (
    <View style={st.wrap}>
      <View style={[st.hero, { backgroundColor: cardBg, borderColor: cardBorder }]}>
        <LinearGradient
          colors={isDark ? ["rgba(99,102,241,0.14)", "transparent"] : ["rgba(99,102,241,0.08)", "transparent"]}
          style={[StyleSheet.absoluteFill, { borderRadius: 20 }]}
        />
        <Text style={[st.heroTitle, { color: textColor }]}>Compatibility Check</Text>
        <Text style={[st.heroSub, { color: mutedColor }]}>
          36 Gun Ashtakoot — Soul Sync, Emotional Bond, Intimacy Match & 5 more dimensions
        </Text>
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
          <Text style={[st.modePillTxt, { color: accent }]}>YOU ARE IN BASIC MODE</Text>
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
              <Text style={[st.partnerReady, { color: accent }]}>Charts ready · tap Check Compatibility</Text>
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
              <Text style={[st.selectTitle, { color: textColor }]}>Select Partner for Milan</Text>
              <Text style={[st.selectSub, { color: mutedColor }]}>
                Both moon signs & nakshatras needed for Gun Milan scores
              </Text>
            </View>
            <Feather name={I18nManager.isRTL ? "arrow-left" : "arrow-right"} size={18} color={accent} />
          </View>
        </Pressable>
      )}

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
              <Text style={st.ctaTxt}>{canCalculate ? "Check Compatibility" : "Check Compatibility"}</Text>
            </>
          )}
        </LinearGradient>
      </Pressable>
      <Text style={[st.ctaHint, { color: mutedColor }]}>
        {!hasPartner
          ? `Select ${youLabel} & partner first`
          : "Tap Check Compatibility for full 36 Gun breakdown"}
      </Text>
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
  ctaBtn: { flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 10, paddingVertical: 17, borderRadius: 16, shadowColor: "#6366f1", shadowOpacity: 0.35, shadowRadius: 14, shadowOffset: { width: 0, height: 6 }, elevation: 6 },
  ctaTxt: { color: "#fff", fontSize: 17, fontFamily: "Nunito_800ExtraBold", letterSpacing: 0.3 },
  ctaHint: { fontSize: 11, fontFamily: "Nunito_500Medium", textAlign: "center", marginTop: 8 },
});
