import { Feather } from "@expo/vector-icons";
import * as Haptics from "expo-haptics";
import { LinearGradient } from "expo-linear-gradient";
import { router } from "expo-router";
import React from "react";
import {
  Alert,
  Linking,
  Platform,
  Pressable,
  ScrollView,
  StatusBar,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { CosmicBg } from "@/components/CosmicBg";
import { FadeInView, staggerDelay } from "@/components/motion/FadeInView";
import { useC } from "@/context/ThemeContext";
import { FOUNDER_PROFILE } from "@/lib/founderProfile";
import { openFounderWhatsApp } from "@/lib/founderWhatsApp";

const F = {
  medium: "Nunito_500Medium",
  semi: "Nunito_600SemiBold",
  bold: "Nunito_700Bold",
  /** App only loads Nunito up to 700 — ExtraBold is not registered. */
  extra: "Nunito_700Bold",
} as const;

async function openExternal(url: string, label: string) {
  try {
    await Linking.openURL(url);
  } catch {
    Alert.alert(
      `${label} open nahi ho paya`,
      "Internet check karke dobara try karein.",
      [{ text: "OK" }],
    );
  }
}

type ChannelRowProps = {
  emoji: string;
  title: string;
  subtitle: string;
  accent: string;
  onPress: () => void;
  primary?: boolean;
};

function ChannelRow({ emoji, title, subtitle, accent, onPress, primary }: ChannelRowProps) {
  const C = useC();
  return (
    <Pressable
      onPress={() => {
        try { Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium); } catch {}
        onPress();
      }}
      style={({ pressed }) => [
        s.row,
        {
          backgroundColor: primary ? `${accent}18` : C.bgCard,
          borderColor: primary ? `${accent}66` : C.border,
          opacity: pressed ? 0.88 : 1,
          transform: [{ scale: pressed ? 0.985 : 1 }],
        },
      ]}
    >
      <View style={[s.rowIcon, { backgroundColor: `${accent}22`, borderColor: `${accent}55` }]}>
        <Text style={{ fontSize: 22 }}>{emoji}</Text>
      </View>
      <View style={{ flex: 1 }}>
        <Text style={[s.rowTitle, { color: C.text }]}>{title}</Text>
        <Text style={[s.rowSub, { color: C.textMuted }]}>{subtitle}</Text>
      </View>
      <View style={[s.rowArrow, { backgroundColor: accent }]}>
        <Feather name="external-link" size={13} color="#fff" />
      </View>
    </Pressable>
  );
}

export default function TalkToFounderScreen() {
  const insets = useSafeAreaInsets();
  const C = useC();
  const androidSB = StatusBar.currentHeight ?? 24;
  const topPad = Platform.OS === "web" ? 67 : Platform.OS === "android" ? Math.max(insets.top, androidSB) : insets.top;

  return (
    <CosmicBg>
      <View style={[s.topBar, { paddingTop: topPad + 8 }]}>
        <Pressable
          onPress={() => router.back()}
          style={[s.backBtn, { backgroundColor: C.bgCard, borderColor: C.border }]}
          hitSlop={10}
        >
          <Feather name="arrow-left" size={18} color={C.text} />
        </Pressable>
        <View style={{ flex: 1 }}>
          <Text style={[s.headerTitle, { color: C.text }]}>Talk to Founder</Text>
          <Text style={[s.headerSub, { color: C.textMuted }]}>Follow karo ya personally baat karo</Text>
        </View>
        <View style={{ width: 36 }} />
      </View>

      <ScrollView
        contentContainerStyle={{
          paddingHorizontal: 16,
          paddingTop: 8,
          paddingBottom: insets.bottom + 40,
          gap: 14,
        }}
        showsVerticalScrollIndicator={false}
      >
        <FadeInView delay={staggerDelay(0)}>
          <View style={[s.hero, { borderColor: C.border, backgroundColor: C.bgCard, overflow: "hidden" }]}>
            <LinearGradient
              colors={["rgba(124,58,237,0.22)", "rgba(37,211,102,0.08)"]}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 1 }}
              style={StyleSheet.absoluteFill}
            />
            <LinearGradient colors={["#6366f1", "#7c3aed"]} style={s.avatar}>
              <Text style={s.avatarTxt}>{FOUNDER_PROFILE.initials}</Text>
            </LinearGradient>
            <Text style={[s.heroName, { color: C.text }]}>{FOUNDER_PROFILE.displayName}</Text>
            <Text style={[s.heroRole, { color: C.textMuted }]}>{FOUNDER_PROFILE.roleLine}</Text>
          </View>
        </FadeInView>

        <FadeInView delay={staggerDelay(1)}>
          <Text style={[s.sectionLbl, { color: C.textMuted }]}>Follow & watch</Text>
          <View style={{ gap: 10 }}>
            <ChannelRow
              emoji="📸"
              title="Instagram"
              subtitle={FOUNDER_PROFILE.instagramHandle}
              accent="#E1306C"
              onPress={() => openExternal(FOUNDER_PROFILE.instagramUrl, "Instagram")}
            />
            <ChannelRow
              emoji="▶️"
              title="YouTube"
              subtitle={FOUNDER_PROFILE.youtubeHandle}
              accent="#FF0000"
              onPress={() => openExternal(FOUNDER_PROFILE.youtubeUrl, "YouTube")}
            />
          </View>
        </FadeInView>

        <FadeInView delay={staggerDelay(2)}>
          <View style={s.dividerRow}>
            <View style={[s.divLine, { backgroundColor: C.border }]} />
            <Text style={[s.divTxt, { color: C.textDim }]}>Direct chat</Text>
            <View style={[s.divLine, { backgroundColor: C.border }]} />
          </View>
          <ChannelRow
            emoji="💬"
            title="WhatsApp"
            subtitle="Discuss your kundli or questions personally"
            accent="#25D366"
            primary
            onPress={() => { void openFounderWhatsApp(); }}
          />
        </FadeInView>

        <FadeInView delay={staggerDelay(3)}>
          <Text style={[s.footerNote, { color: C.textDim }]}>
            Instagram / YouTube pe updates dekho. Personal sawaal ke liye WhatsApp best hai.
          </Text>
        </FadeInView>
      </ScrollView>
    </CosmicBg>
  );
}

const s = StyleSheet.create({
  topBar: {
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
    paddingHorizontal: 16,
    paddingBottom: 12,
  },
  backBtn: {
    width: 36,
    height: 36,
    borderRadius: 11,
    borderWidth: 1,
    alignItems: "center",
    justifyContent: "center",
  },
  headerTitle: { fontSize: 17, fontFamily: F.extra, letterSpacing: -0.2 },
  headerSub: { fontSize: 11, fontFamily: F.medium, marginTop: 1 },

  hero: {
    borderRadius: 20,
    borderWidth: 1,
    paddingVertical: 22,
    paddingHorizontal: 18,
    alignItems: "center",
    gap: 8,
  },
  avatar: {
    width: 64,
    height: 64,
    borderRadius: 22,
    alignItems: "center",
    justifyContent: "center",
    marginBottom: 4,
  },
  avatarTxt: { color: "#fff", fontSize: 22, fontFamily: F.extra },
  heroName: { fontSize: 18, fontFamily: F.extra },
  heroRole: { fontSize: 12, fontFamily: F.medium, textAlign: "center", lineHeight: 17 },

  sectionLbl: {
    fontSize: 10,
    fontFamily: F.extra,
    letterSpacing: 1.1,
    textTransform: "uppercase",
    marginBottom: 8,
    marginLeft: 2,
  },

  row: {
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
    padding: 14,
    borderRadius: 16,
    borderWidth: 1.5,
  },
  rowIcon: {
    width: 48,
    height: 48,
    borderRadius: 14,
    borderWidth: 1,
    alignItems: "center",
    justifyContent: "center",
  },
  rowTitle: { fontSize: 15, fontFamily: F.bold },
  rowSub: { fontSize: 12, fontFamily: F.medium, marginTop: 2 },
  rowArrow: {
    width: 32,
    height: 32,
    borderRadius: 16,
    alignItems: "center",
    justifyContent: "center",
  },

  dividerRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    marginBottom: 10,
    marginTop: 2,
  },
  divLine: { flex: 1, height: 1 },
  divTxt: { fontSize: 11, fontFamily: F.semi, letterSpacing: 0.3 },

  footerNote: {
    fontSize: 11,
    fontFamily: F.medium,
    textAlign: "center",
    lineHeight: 16,
    paddingHorizontal: 12,
    marginTop: 4,
  },
});
