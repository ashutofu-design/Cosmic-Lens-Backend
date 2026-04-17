import React from "react";
import { Linking, Pressable, StyleSheet, Text, View } from "react-native";
import { Feather } from "@expo/vector-icons";
import { router } from "expo-router";
import LegalScreen, { Section, P, Strong } from "@/components/LegalScreen";
import { useC } from "@/context/ThemeContext";

const F = {
  regular:  "Nunito_400Regular",
  semibold: "Nunito_600SemiBold",
  bold:     "Nunito_700Bold",
} as const;

const APP_VERSION = "1.0.0";
const SUPPORT_EMAIL = "support@cosmiclens.app";
const WEB_URL = "https://cosmiclens.app";

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

export default function AboutScreen() {
  const C = useC();
  return (
    <LegalScreen title="About Cosmic Lens" subtitle="Vedic astrology, modernised">
      <Section title="Our Mission">
        <P>
          Cosmic Lens brings the timeless wisdom of <Strong>Vedic Jyotish</Strong>
          to your pocket. We combine classical Parashari principles with modern
          ephemeris computations and AI-assisted interpretation to give you
          accurate, accessible, and personal astrological guidance — in your
          language.
        </P>
        <P>
          Whether you’re curious about your kundli, planning a marriage,
          exploring career options, or simply seeking daily insight, our
          mission is to help you navigate life with clarity and intention.
        </P>
      </Section>

      <Section title="What Makes Us Different">
        <P>
          • Calculations use the traditional <Strong>Lahiri ayanamsa</Strong> with
          high-precision Swiss Ephemeris data.{"\n"}
          • Available in <Strong>24 languages</Strong> including 13 Indian
          regional languages and Hinglish.{"\n"}
          • Honest, transparent pricing — <Strong>no in-app currency</Strong>,
          no surprise charges.{"\n"}
          • Privacy-first — we never sell your kundli or chat data.{"\n"}
          • 7-day free trial so you can experience before paying.
        </P>
      </Section>

      <Section title="Connect With Us">
        <View style={{ gap: 10, marginTop: 4 }}>
          <LinkRow
            icon="mail"
            label="Support Email"
            value={SUPPORT_EMAIL}
            onPress={() => Linking.openURL(`mailto:${SUPPORT_EMAIL}`)}
          />
          <LinkRow
            icon="globe"
            label="Website"
            value={WEB_URL.replace("https://", "")}
            onPress={() => Linking.openURL(WEB_URL)}
          />
        </View>
      </Section>

      <Section title="Legal & Policies">
        <View style={{ gap: 10, marginTop: 4 }}>
          {[
            { label: "Privacy Policy",          path: "/privacy",        icon: "shield" },
            { label: "Terms of Service",        path: "/terms",          icon: "file-text" },
            { label: "Refund & Cancellation",   path: "/refund",         icon: "rotate-ccw" },
            { label: "Astrology Disclaimer",    path: "/disclaimer",     icon: "alert-triangle" },
            { label: "Delete My Account",       path: "/delete-account", icon: "trash-2" },
          ].map(item => (
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
              <Feather name="chevron-right" size={16} color={C.textMuted} />
            </Pressable>
          ))}
        </View>
      </Section>

      <View style={[ar.versionCard, { backgroundColor: C.bgCard, borderColor: C.border }]}>
        <Text style={[ar.versionLabel, { color: C.textMuted }]}>App Version</Text>
        <Text style={[ar.versionValue, { color: C.text }]}>v{APP_VERSION}</Text>
        <Text style={[ar.versionFoot, { color: C.textMuted }]}>
          Made with ♥ in India · © 2026 Cosmic Lens
        </Text>
      </View>
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
});
