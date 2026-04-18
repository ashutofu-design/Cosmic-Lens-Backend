// ────────────────────────────────────────────────────────────────────────────
// AstroVastu — Page 1 chooser
// LEFT: AstroVastu (FREE)        → /vastu (compass + ROOMS guide)
// RIGHT: AstroVastu Pro Premium  → /astrovastu-pro-options (Page 2)
// ────────────────────────────────────────────────────────────────────────────
import React from "react";
import { View, Text, Pressable, ScrollView, StyleSheet, Platform } from "react-native";
import { router } from "expo-router";
import { Feather } from "@expo/vector-icons";
import { LinearGradient } from "expo-linear-gradient";
import * as Haptics from "expo-haptics";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useC } from "@/context/ThemeContext";

export default function AstroVastuChooser() {
  const insets = useSafeAreaInsets();
  const C = useC();
  const topPad = Platform.OS === "web" ? 67 : insets.top;
  const botPad = Platform.OS === "web" ? 34 : insets.bottom;

  const goFree = () => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    router.push("/vastu" as any);
  };

  const goPro = () => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    router.push("/astrovastu-pro-options" as any);
  };

  return (
    <View style={[s.root, { backgroundColor: C.isDark ? "#050709" : C.bg }]}>
      {C.isDark && (
        <LinearGradient
          colors={["#050709", "#0a0604", "#1a0e02"]}
          locations={[0, 0.55, 1]}
          style={StyleSheet.absoluteFill}
          pointerEvents="none"
        />
      )}

      {/* Header */}
      <View style={[s.header, { paddingTop: topPad + 8, borderBottomColor: C.border }]}>
        <Pressable onPress={() => router.back()} style={s.back}>
          <Feather name="arrow-left" size={20} color={C.textMuted} />
        </Pressable>
        <View style={{ flex: 1 }}>
          <Text style={[s.title, { color: C.text }]}>AstroVastu</Text>
          <Text style={[s.titleSub, { color: C.textMuted }]}>Choose your Vastu journey</Text>
        </View>
      </View>

      <ScrollView
        contentContainerStyle={[s.content, { paddingBottom: botPad + 30 }]}
        showsVerticalScrollIndicator={false}
      >
        {/* Intro */}
        <Text style={[s.heading, { color: C.text }]}>Aap kaunsa Vastu chahte hain?</Text>
        <Text style={[s.subHeading, { color: C.textMuted }]}>
          Free se shuruaat karein ya kundli-personalized Premium analysis lein
        </Text>

        {/* ── LEFT: AstroVastu (FREE) ── */}
        <Pressable
          onPress={goFree}
          style={[s.card, { borderColor: C.accent, backgroundColor: C.isDark ? "#0c1722" : C.bgCard }]}
        >
          <View style={[s.tag, { backgroundColor: `${C.accent}22`, borderColor: C.accent }]}>
            <Text style={[s.tagText, { color: C.accent }]}>FREE · ALWAYS</Text>
          </View>

          <View style={s.cardHeader}>
            <Text style={s.emoji}>🧭</Text>
            <View style={{ flex: 1 }}>
              <Text style={[s.cardTitle, { color: C.text }]}>AstroVastu</Text>
              <Text style={[s.cardTagline, { color: C.textMuted }]}>Compass + basic Vastu guide</Text>
            </View>
          </View>

          <View style={s.bullets}>
            <Bullet C={C} text="Real magnetometer compass — direction find karein" />
            <Bullet C={C} text="Room-wise guide: kitchen, bedroom, pooja kahan hona chahiye" />
            <Bullet C={C} text="General do's & don'ts per direction" />
            <Bullet C={C} text="8 directions ka deity, element & meaning" />
          </View>

          <View style={[s.ctaRow, { backgroundColor: `${C.accent}15` }]}>
            <Text style={[s.ctaText, { color: C.accent }]}>Open Free Vastu</Text>
            <Feather name="arrow-right" size={16} color={C.accent} />
          </View>
        </Pressable>

        {/* ── RIGHT: AstroVastu Pro Premium ── */}
        <Pressable onPress={goPro} style={[s.card, s.proCard]}>
          {/* Premium gold glow */}
          <LinearGradient
            colors={["#f9d76b22", "#f59e0b18", "#3a240400"]}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 1 }}
            style={StyleSheet.absoluteFill}
          />

          <View style={[s.tag, { backgroundColor: "#f9d76b", borderColor: "#f9d76b" }]}>
            <Feather name="award" size={9} color="#3a2404" />
            <Text style={[s.tagText, { color: "#3a2404", marginLeft: 4 }]}>PRO PREMIUM</Text>
          </View>

          <View style={s.cardHeader}>
            <Text style={s.emoji}>🌟</Text>
            <View style={{ flex: 1 }}>
              <Text style={[s.cardTitle, { color: "#fef3c7" }]}>AstroVastu Pro Premium</Text>
              <Text style={[s.cardTagline, { color: "#f9d76bcc" }]}>
                Kundli-personalized Vastu — Home & Business
              </Text>
            </View>
          </View>

          <View style={s.bullets}>
            <BulletGold text="Single room quick check — ₹199" />
            <BulletGold text="3-room bundle — ₹499" />
            <BulletGold text="Full Home Advanced (lifetime) — ₹2,999" />
            <BulletGold text="Business: Shop / Office / Factory — ₹999 onwards" />
            <BulletGold text="Mahadasha-mandatory analysis + classical refs + PDF" />
          </View>

          <View style={[s.ctaRow, { backgroundColor: "#f9d76b22" }]}>
            <Text style={[s.ctaText, { color: "#f9d76b" }]}>View Premium Options</Text>
            <Feather name="arrow-right" size={16} color="#f9d76b" />
          </View>
        </Pressable>

        {/* Branding */}
        <Text style={[s.branding, { color: C.textDim }]}>
          Powered by Advanced Cosmic Intelligence
        </Text>
      </ScrollView>
    </View>
  );
}

function Bullet({ C, text }: { C: any; text: string }) {
  return (
    <View style={s.bulletRow}>
      <Feather name="check" size={13} color={C.accent} />
      <Text style={[s.bulletText, { color: C.textMid || C.text }]}>{text}</Text>
    </View>
  );
}
function BulletGold({ text }: { text: string }) {
  return (
    <View style={s.bulletRow}>
      <Feather name="check" size={13} color="#f9d76b" />
      <Text style={[s.bulletText, { color: "#fde68a" }]}>{text}</Text>
    </View>
  );
}

const s = StyleSheet.create({
  root:        { flex: 1 },
  header:      { flexDirection: "row", alignItems: "center", gap: 12, paddingHorizontal: 16, paddingBottom: 14, borderBottomWidth: 1 },
  back:        { width: 36, height: 36, alignItems: "center", justifyContent: "center" },
  title:       { fontSize: 17, fontWeight: "800" },
  titleSub:    { fontSize: 11, marginTop: 2 },
  content:     { paddingHorizontal: 16, paddingTop: 18, gap: 14 },
  heading:     { fontSize: 18, fontWeight: "800", marginBottom: 4 },
  subHeading:  { fontSize: 12, lineHeight: 18, marginBottom: 8 },
  card:        { borderRadius: 18, borderWidth: 2, padding: 16, gap: 12, position: "relative", overflow: "hidden" },
  proCard:     { borderColor: "#f9d76b", backgroundColor: "#0a0604" },
  tag:         { flexDirection: "row", alignItems: "center", alignSelf: "flex-start", paddingHorizontal: 9, paddingVertical: 4, borderRadius: 7, borderWidth: 1 },
  tagText:     { fontSize: 9, fontWeight: "900", letterSpacing: 1.4 },
  cardHeader:  { flexDirection: "row", alignItems: "center", gap: 12 },
  emoji:       { fontSize: 36 },
  cardTitle:   { fontSize: 17, fontWeight: "800", marginBottom: 3 },
  cardTagline: { fontSize: 12, lineHeight: 16 },
  bullets:     { gap: 7, marginTop: 4 },
  bulletRow:   { flexDirection: "row", alignItems: "flex-start", gap: 8 },
  bulletText:  { fontSize: 12, lineHeight: 17, flex: 1 },
  ctaRow:      { flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 8, paddingVertical: 11, borderRadius: 10, marginTop: 6 },
  ctaText:     { fontSize: 13, fontWeight: "800", letterSpacing: 0.3 },
  branding:    { fontSize: 10, textAlign: "center", marginTop: 8, letterSpacing: 1.2, fontWeight: "600" },
});
