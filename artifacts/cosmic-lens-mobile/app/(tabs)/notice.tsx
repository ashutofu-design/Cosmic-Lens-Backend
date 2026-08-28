import { Feather } from "@expo/vector-icons";
import React, { useMemo } from "react";
import { Platform, ScrollView, StatusBar, StyleSheet, Text, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { CosmicBg } from "@/components/CosmicBg";
import { FadeInView, staggerDelay } from "@/components/motion/FadeInView";
import { useC } from "@/context/ThemeContext";
import { useUser } from "@/context/UserContext";
import { getT } from "@/lib/i18n";
import { buildNoticesFromKundli } from "@/lib/chartPersonalize";

export default function NoticeScreen() {
  const insets  = useSafeAreaInsets();
  const C = useC();
  const { kundli, language } = useUser();
  const t = getT(language);
  const androidSB = StatusBar.currentHeight ?? 24;
  const topPad  = Platform.OS === "web" ? 67 : Platform.OS === "android" ? Math.max(insets.top, androidSB) : insets.top;
  const botPad  = Platform.OS === "web" ? 34 : insets.bottom;

  const noticeLang = language === "hi" ? "hi" : language === "en" ? "en" : "hn";
  const notices = useMemo(
    () => buildNoticesFromKundli(kundli, noticeLang),
    [kundli, noticeLang],
  );
  const unread  = Math.min(2, notices.length);

  return (
    <CosmicBg>
    <ScrollView
      style={s.root}
      contentContainerStyle={[s.content, { paddingTop: topPad + 16, paddingBottom: botPad + 110 }]}
      showsVerticalScrollIndicator={false}
    >
      <FadeInView delay={staggerDelay(0)}>
        <View style={s.headerRow}>
          <Text style={[s.heading,{ color: C.text }]}>{t.noticeTitle}</Text>
          {unread > 0 && kundli && (
            <View style={s.badge}>
              <Text style={s.badgeText}>{unread} new</Text>
            </View>
          )}
        </View>
      </FadeInView>

      <View style={[s.card, { backgroundColor: C.bgCard, borderColor: C.border, boxShadow: C.cardShadow } as any]}>
        {notices.map((n, i) => (
          <FadeInView key={`${n.title}-${i}`} delay={staggerDelay(i + 1)}>
            <View style={[s.row, i < notices.length - 1 && [s.rowBorder, { borderBottomColor: C.border }]]}>
              <View style={[s.dotWrap, { backgroundColor: `${n.dot}15` }]}>
                <Feather name={n.icon} size={14} color={n.dot} />
              </View>
              <View style={s.body}>
                <View style={s.titleRow}>
                  <Text style={[s.title, { color: C.text }]}>{n.title}</Text>
                  {i < unread && kundli ? <View style={s.newDot} /> : null}
                </View>
                <Text style={[s.desc, { color: C.textMuted }]}>{n.desc}</Text>
                <Text style={[s.time, { color: C.textMuted }]}>{n.time}</Text>
              </View>
            </View>
          </FadeInView>
        ))}
      </View>

      <FadeInView delay={staggerDelay(notices.length + 1)}>
        <View style={s.footer}>
          <Feather name="bell-off" size={12} color={C.textDim} />
          <Text style={[s.footerText,{ color: C.textDim }]}>
            {kundli
              ? "Yeh alerts aapki kundli se bane hain — har profile alag dikhega"
              : "Kundli banao — personalized alerts milenge"}
          </Text>
        </View>
      </FadeInView>
    </ScrollView>
    </CosmicBg>
  );
}

const s = StyleSheet.create({
  root:       { flex: 1 },
  content:    { paddingHorizontal: 16, gap: 14 },

  headerRow:  { flexDirection: "row", alignItems: "center", gap: 10 },
  heading:    { color: "#dde8f4", fontSize: 22, fontWeight: "700" },
  badge: {
    backgroundColor: "rgba(239,68,68,0.15)", borderRadius: 12, borderWidth: 1,
    borderColor: "rgba(239,68,68,0.3)", paddingHorizontal: 8, paddingVertical: 2,
  },
  badgeText:  { color: "#f87171", fontSize: 11, fontWeight: "600" },

  card: {
    backgroundColor: "#040e1f", borderRadius: 18,
    borderWidth: 1, borderColor: "rgba(255,255,255,0.05)", overflow: "hidden",
  },
  row: {
    flexDirection: "row", alignItems: "flex-start",
    paddingHorizontal: 16, paddingVertical: 16, gap: 12,
  },
  rowBorder: { borderBottomWidth: 1, borderBottomColor: "#071525" },

  dotWrap: {
    width: 32, height: 32, borderRadius: 16,
    alignItems: "center", justifyContent: "center", marginTop: 1,
  },
  body:     { flex: 1, gap: 4 },
  titleRow: { flexDirection: "row", alignItems: "center", gap: 6 },
  title:    { color: "#dde8f4", fontSize: 13, fontWeight: "600", flex: 1 },
  newDot:   { width: 7, height: 7, borderRadius: 3.5, backgroundColor: "#ef4444" },
  desc:     { color: "#475569", fontSize: 12, lineHeight: 18 },
  time:     { color: "#1e3a5f", fontSize: 11 },

  footer: {
    flexDirection: "row", alignItems: "center", gap: 7,
    justifyContent: "center", paddingVertical: 4,
  },
  footerText: { color: "#1e3a5f", fontSize: 11, textAlign: "center" },
});
