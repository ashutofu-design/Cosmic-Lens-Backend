import { Feather } from "@expo/vector-icons";
import React from "react";
import { Platform, ScrollView, StyleSheet, Text, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useUser } from "@/context/UserContext";

interface Notice {
  dot: string;
  icon: keyof typeof Feather.glyphMap;
  title: string;
  desc: string;
  time: string;
}

const DEMO_NOTICES: Notice[] = [
  {
    dot: "#ef4444",
    icon: "alert-triangle",
    title: "Phase change aane wali hai",
    desc: "Aapka Shani-Rahu phase 3 din mein khatam ho raha hai. Ek noticeable energy shift aayega — taiyaar rahein.",
    time: "2h pehle",
  },
  {
    dot: "#fbbf24",
    icon: "calendar",
    title: "Kal ka din strong hai",
    desc: "Sun-Jupiter alignment career moves ke liye favorable hai. Zaroori meetings schedule karein.",
    time: "5h pehle",
  },
  {
    dot: "#ef4444",
    icon: "moon",
    title: "Emotional dip likely",
    desc: "Moon 8th house mein transit kar raha hai. Aaj bade relationship conversations se bachein.",
    time: "8h pehle",
  },
  {
    dot: "#4ade80",
    icon: "zap",
    title: "Weekly insight ready hai",
    desc: "Aapka personalized weekly breakdown Insights tab mein available hai.",
    time: "1 din pehle",
  },
  {
    dot: "#fbbf24",
    icon: "trending-up",
    title: "Finance window khul rahi hai",
    desc: "Venus agle hafte aapke 2nd house mein enter karega. Investments ke liye acha period.",
    time: "2 din pehle",
  },
  {
    dot: "#a78bfa",
    icon: "star",
    title: "Jupiter transit update",
    desc: "Guru graha aapke 9th house se 10th house mein jaayega — career mein nayi uchaaiyaan sambhav.",
    time: "3 din pehle",
  },
];

function buildNoticesFromKundli(): Notice[] {
  return DEMO_NOTICES;
}

export default function NoticeScreen() {
  const insets  = useSafeAreaInsets();
  const { kundli } = useUser();
  const topPad  = Platform.OS === "web" ? 67 : insets.top;
  const botPad  = Platform.OS === "web" ? 34 : insets.bottom;
  const notices = DEMO_NOTICES;
  const unread  = notices.filter((_, i) => i < 2).length;

  return (
    <ScrollView
      style={s.root}
      contentContainerStyle={[s.content, { paddingTop: topPad + 16, paddingBottom: botPad + 110 }]}
      showsVerticalScrollIndicator={false}
    >
      {/* Header */}
      <View style={s.headerRow}>
        <Text style={s.heading}>Notices</Text>
        {unread > 0 && (
          <View style={s.badge}>
            <Text style={s.badgeText}>{unread} new</Text>
          </View>
        )}
      </View>

      {/* List */}
      <View style={s.card}>
        {notices.map((n, i) => (
          <View key={i} style={[s.row, i < notices.length - 1 && s.rowBorder]}>
            <View style={[s.dotWrap, { backgroundColor: `${n.dot}15` }]}>
              <Feather name={n.icon} size={14} color={n.dot} />
            </View>
            <View style={s.body}>
              <View style={s.titleRow}>
                <Text style={s.title}>{n.title}</Text>
                {i < unread && <View style={s.newDot} />}
              </View>
              <Text style={s.desc}>{n.desc}</Text>
              <Text style={s.time}>{n.time}</Text>
            </View>
          </View>
        ))}
      </View>

      {/* Footer */}
      <View style={s.footer}>
        <Feather name="bell-off" size={12} color="#1e3a5f" />
        <Text style={s.footerText}>
          {kundli
            ? "Aur notifications kundli update hone par aayenge"
            : "Kundli banao — personalized alerts milenge"}
        </Text>
      </View>
    </ScrollView>
  );
}

const s = StyleSheet.create({
  root:       { flex: 1, backgroundColor: "#020d1a" },
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
