import React, { useEffect, useState } from "react";
import {
  I18nManager,
  Linking,
  Pressable,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { Feather } from "@expo/vector-icons";
import Constants from "expo-constants";
import * as Updates from "expo-updates";
import { router } from "expo-router";
import LegalScreen, { Section, P } from "@/components/LegalScreen";
import { FadeInView, staggerDelay } from "@/components/motion/FadeInView";
import { useC } from "@/context/ThemeContext";
import { useT } from "@/hooks/useT";
import { LEGAL_META } from "@/lib/legalPolicies";

const F = {
  regular:  "Nunito_400Regular",
  semibold: "Nunito_600SemiBold",
  bold:     "Nunito_700Bold",
} as const;

const APP_VERSION = Constants.expoConfig?.version ?? "1.0.0";
const SUPPORT_EMAIL = LEGAL_META.supportEmail;
const WEB_URL = LEGAL_META.website;

function LinkRow({
  icon, label, value, onPress,
}: { icon: any; label: string; value: string; onPress: () => void }) {
  const C = useC();
  return (
    <Pressable
      onPress={onPress}
      style={({ pressed }) => [
        ar.row,
        { backgroundColor: C.bgCard, borderColor: C.border, opacity: pressed ? 0.85 : 1 },
      ]}
    >
      <View style={[ar.iconWrap, { backgroundColor: C.isDark ? "rgba(245,158,11,0.12)" : "rgba(124,58,237,0.10)" }]}>
        <Feather name={icon} size={15} color={C.isDark ? "#f59e0b" : "#7c3aed"} />
      </View>
      <View style={{ flex: 1 }}>
        <Text style={[ar.label, { color: C.textMuted }]}>{label}</Text>
        <Text style={[ar.value, { color: C.text }]} numberOfLines={1}>{value}</Text>
      </View>
      <Feather name="external-link" size={14} color={C.textMuted} />
    </Pressable>
  );
}

type OtaInfo = {
  updateId: string;
  channel: string;
  runtime: string;
  createdAt: string;
  isEmbedded: boolean;
};

export default function AboutScreen() {
  const C = useC();
  const t = useT();
  const [ota, setOta] = useState<OtaInfo | null>(null);

  useEffect(() => {
    try {
      const created = Updates.createdAt;
      setOta({
        updateId: Updates.updateId ?? "(embedded / no OTA)",
        channel: Updates.channel ?? "(none)",
        runtime: Updates.runtimeVersion ?? "—",
        createdAt: created ? created.toISOString() : "—",
        isEmbedded: !!Updates.isEmbeddedLaunch,
      });
    } catch {
      setOta({
        updateId: "(updates unavailable)",
        channel: "(none)",
        runtime: "—",
        createdAt: "—",
        isEmbedded: true,
      });
    }
  }, []);

  const legalLinks: { label: string; path: string; icon: string }[] = [
    { label: t.ab_linkPrivacy,    path: "/privacy",        icon: "shield" },
    { label: t.ab_linkTerms,      path: "/terms",          icon: "file-text" },
    { label: t.ab_linkRefund,     path: "/refund",         icon: "rotate-ccw" },
    { label: t.ab_linkDisclaimer, path: "/disclaimer",     icon: "alert-triangle" },
    { label: t.ab_linkDelete,     path: "/delete-account", icon: "trash-2" },
  ];

  return (
    <LegalScreen title={t.ab_title} subtitle={t.ab_subtitle}>
      <FadeInView delay={staggerDelay(0)}>
      <Section title={t.ab_secMission}>
        <P>{t.ab_pMission1}</P>
        <P>{t.ab_pMission2}</P>
      </Section>
      </FadeInView>

      <FadeInView delay={staggerDelay(1)}>
      <Section title={t.ab_secInside}>
        <P>{t.ab_pInside}</P>
      </Section>
      </FadeInView>

      <FadeInView delay={staggerDelay(2)}>
      <Section title={t.ab_secDifferent}>
        <P>{t.ab_pDifferent}</P>
      </Section>
      </FadeInView>

      <FadeInView delay={staggerDelay(3)}>
      <Section title={t.ab_secConnect}>
        <View style={{ gap: 10, marginTop: 4 }}>
          <LinkRow
            icon="mail"
            label={t.ab_lblSupportEmail}
            value={SUPPORT_EMAIL}
            onPress={() => Linking.openURL(`mailto:${SUPPORT_EMAIL}`)}
          />
          <LinkRow
            icon="globe"
            label={t.ab_lblWebsite}
            value={WEB_URL.replace("https://", "")}
            onPress={() => Linking.openURL(WEB_URL)}
          />
        </View>
      </Section>
      </FadeInView>

      <FadeInView delay={staggerDelay(4)}>
      <Section title={t.ab_secLegal}>
        <View style={{ gap: 10, marginTop: 4 }}>
          {legalLinks.map(item => (
            <Pressable
              key={item.path}
              onPress={() => router.push(item.path as any)}
              style={({ pressed }) => [
                ar.row,
                { backgroundColor: C.bgCard, borderColor: C.border, opacity: pressed ? 0.85 : 1 },
              ]}
            >
              <View style={[ar.iconWrap, { backgroundColor: C.isDark ? "rgba(245,158,11,0.12)" : "rgba(124,58,237,0.10)" }]}>
                <Feather name={item.icon as any} size={15} color={C.isDark ? "#f59e0b" : "#7c3aed"} />
              </View>
              <Text style={[ar.linkLabel, { color: C.text }]}>{item.label}</Text>
              <Feather name={I18nManager.isRTL ? "chevron-left" : "chevron-right"} size={16} color={C.textMuted} />
            </Pressable>
          ))}
        </View>
      </Section>
      </FadeInView>

      <FadeInView delay={staggerDelay(5)}>
      <View style={[ar.versionCard, { backgroundColor: C.bgCard, borderColor: C.border }]}>
        <Text style={[ar.versionLabel, { color: C.textMuted }]}>{t.ab_lblAppVersion}</Text>
        <Text style={[ar.versionValue, { color: C.text }]}>v{APP_VERSION}</Text>
        {ota ? (
          <View style={{ marginTop: 10, gap: 4, alignSelf: "stretch" }}>
            <Text style={[ar.metaLine, { color: C.textMuted }]}>
              Channel: {ota.channel}
            </Text>
            <Text style={[ar.metaLine, { color: C.textMuted }]}>
              Runtime: {ota.runtime}
            </Text>
            <Text style={[ar.metaLine, { color: C.textMuted }]} selectable>
              Update ID: {ota.updateId}
            </Text>
            <Text style={[ar.metaLine, { color: C.textMuted }]}>
              OTA time: {ota.createdAt}
            </Text>
            <Text style={[ar.metaLine, { color: ota.isEmbedded ? "#f59e0b" : "#22c55e" }]}>
              {ota.isEmbedded
                ? "Status: Embedded build (OTA not applied yet)"
                : "Status: Running EAS Update (OTA OK)"}
            </Text>
          </View>
        ) : null}
        <Text style={[ar.versionFoot, { color: C.textMuted }]}>
          {t.ab_versionFoot}
        </Text>
      </View>
      </FadeInView>
    </LegalScreen>
  );
}

const ar = StyleSheet.create({
  row: {
    flexDirection: "row", alignItems: "center", gap: 12,
    paddingVertical: 12, paddingHorizontal: 14,
    borderRadius: 12, borderWidth: 1,
  },
  iconWrap: {
    width: 32, height: 32, borderRadius: 9,
    alignItems: "center", justifyContent: "center",
  },
  label:     { fontSize: 10.5, fontFamily: F.semibold, letterSpacing: 0.4, textTransform: "uppercase" },
  value:     { fontSize: 13, fontFamily: F.semibold, marginTop: 2 },
  linkLabel: { flex: 1, fontSize: 13.5, fontFamily: F.semibold },

  versionCard: {
    marginTop: 24, padding: 16, borderRadius: 14,
    borderWidth: 1, alignItems: "center", gap: 4,
  },
  versionLabel: { fontSize: 10.5, fontFamily: F.semibold, letterSpacing: 0.4, textTransform: "uppercase" },
  versionValue: { fontSize: 18, fontFamily: F.bold, letterSpacing: -0.3 },
  versionFoot:  { fontSize: 11, fontFamily: F.regular, marginTop: 8 },
  metaLine:     { fontSize: 10.5, fontFamily: F.medium, textAlign: "left" },
});
