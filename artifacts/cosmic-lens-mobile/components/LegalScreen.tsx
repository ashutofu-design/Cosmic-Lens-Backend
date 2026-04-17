/**
 * LegalScreen — shared layout for legal/policy pages
 * Provides consistent header, scrollable body, and helper components for
 * Section / Paragraph / BulletList rendering.
 *
 * Used by: privacy, terms, refund, disclaimer, delete-account, about screens.
 */

import { Feather } from "@expo/vector-icons";
import { router } from "expo-router";
import React from "react";
import {
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useC } from "@/context/ThemeContext";

const F = {
  regular:  "Nunito_400Regular",
  medium:   "Nunito_500Medium",
  semibold: "Nunito_600SemiBold",
  bold:     "Nunito_700Bold",
} as const;

interface Props {
  title:        string;
  subtitle?:    string;
  lastUpdated?: string;
  children:     React.ReactNode;
}

export default function LegalScreen({ title, subtitle, lastUpdated, children }: Props) {
  const insets = useSafeAreaInsets();
  const C      = useC();
  const topPad = Platform.OS === "web" ? 67 : insets.top;
  const botPad = Platform.OS === "web" ? 34 : insets.bottom;

  return (
    <View style={[s.root, { backgroundColor: C.bg }]}>
      <View style={[s.header, { paddingTop: topPad + 6, borderBottomColor: C.border }]}>
        <Pressable onPress={() => router.back()} style={s.backBtn} hitSlop={8}>
          <Feather name="arrow-left" size={20} color={C.text} />
        </Pressable>
        <View style={{ flex: 1 }}>
          <Text style={[s.title, { color: C.text }]} numberOfLines={1}>{title}</Text>
          {subtitle && (
            <Text style={[s.subtitle, { color: C.textMuted }]} numberOfLines={1}>{subtitle}</Text>
          )}
        </View>
      </View>

      <ScrollView
        contentContainerStyle={[s.scroll, { paddingBottom: botPad + 32 }]}
        showsVerticalScrollIndicator={false}
      >
        {lastUpdated && (
          <View style={[s.updatedPill, { backgroundColor: C.bgCard, borderColor: C.border }]}>
            <Feather name="calendar" size={11} color={C.textMuted} />
            <Text style={[s.updatedText, { color: C.textMuted }]}>
              Last updated: {lastUpdated}
            </Text>
          </View>
        )}
        {children}
      </ScrollView>
    </View>
  );
}

// ── Helper components ────────────────────────────────────────────────────────

export function Section({ title, children }: { title: string; children: React.ReactNode }) {
  const C = useC();
  return (
    <View style={s.section}>
      <Text style={[s.sectionTitle, { color: C.text }]}>{title}</Text>
      <View style={{ gap: 10 }}>{children}</View>
    </View>
  );
}

export function P({ children }: { children: React.ReactNode }) {
  const C = useC();
  return <Text style={[s.paragraph, { color: C.textMid }]}>{children}</Text>;
}

export function Bullet({ children }: { children: React.ReactNode }) {
  const C = useC();
  return (
    <View style={s.bulletRow}>
      <View style={[s.bulletDot, { backgroundColor: C.textMuted }]} />
      <Text style={[s.bulletText, { color: C.textMid }]}>{children}</Text>
    </View>
  );
}

export function Strong({ children }: { children: React.ReactNode }) {
  const C = useC();
  return <Text style={{ color: C.text, fontFamily: F.bold }}>{children}</Text>;
}

export function Callout({
  children, tone = "info",
}: { children: React.ReactNode; tone?: "info" | "warn" | "danger" }) {
  const C = useC();
  const palette = {
    info:   { bg: C.isDark ? "#1e3a8a30" : "#dbeafe", border: "#3b82f640", icon: "#3b82f6" },
    warn:   { bg: C.isDark ? "#7c2d1230" : "#fef3c7", border: "#f59e0b40", icon: "#f59e0b" },
    danger: { bg: C.isDark ? "#7f1d1d30" : "#fee2e2", border: "#ef444440", icon: "#ef4444" },
  }[tone];
  const iconName = tone === "danger" ? "alert-octagon" : tone === "warn" ? "alert-triangle" : "info";

  return (
    <View style={[s.callout, { backgroundColor: palette.bg, borderColor: palette.border }]}>
      <Feather name={iconName as any} size={14} color={palette.icon} style={{ marginTop: 2 }} />
      <Text style={[s.calloutText, { color: C.text }]}>{children}</Text>
    </View>
  );
}

const s = StyleSheet.create({
  root: { flex: 1 },
  header: {
    flexDirection: "row", alignItems: "center", gap: 12,
    paddingHorizontal: 16, paddingBottom: 12,
    borderBottomWidth: 1,
  },
  backBtn: {
    width: 36, height: 36, borderRadius: 10,
    backgroundColor: "rgba(255,255,255,0.06)",
    alignItems: "center", justifyContent: "center",
  },
  title:    { fontSize: 18, fontFamily: F.bold, letterSpacing: -0.3 },
  subtitle: { fontSize: 11, fontFamily: F.regular, marginTop: 2 },
  scroll:   { paddingHorizontal: 18, paddingTop: 14, gap: 8 },

  updatedPill: {
    flexDirection: "row", alignItems: "center", gap: 6,
    alignSelf: "flex-start",
    paddingVertical: 6, paddingHorizontal: 10,
    borderRadius: 8, borderWidth: 1, marginBottom: 10,
  },
  updatedText: { fontSize: 11, fontFamily: F.medium },

  section: { marginTop: 18, gap: 10 },
  sectionTitle: {
    fontSize: 15, fontFamily: F.bold, letterSpacing: -0.2,
    marginBottom: 2,
  },
  paragraph: {
    fontSize: 13, fontFamily: F.regular,
    lineHeight: 21,
  },

  bulletRow: { flexDirection: "row", gap: 10, paddingLeft: 4 },
  bulletDot: {
    width: 5, height: 5, borderRadius: 2.5,
    marginTop: 8,
  },
  bulletText: {
    flex: 1, fontSize: 13, fontFamily: F.regular,
    lineHeight: 21,
  },

  callout: {
    flexDirection: "row", gap: 9,
    padding: 12, borderRadius: 10,
    borderWidth: 1, marginTop: 4,
  },
  calloutText: {
    flex: 1, fontSize: 12.5, fontFamily: F.medium,
    lineHeight: 19,
  },
});
