// ────────────────────────────────────────────────────────────────────────────
// AstroVastu Pro Premium — Page 2 chooser
//   • Home Vastu Advanced  → /astrovastu-pro (existing PRO multi-room screen)
//   • Business Vastu       → /business-vastu (Office / Shop / Factory) — placeholder
// ────────────────────────────────────────────────────────────────────────────
import React from "react";
import { View, Text, Pressable, ScrollView, StyleSheet, Platform, Alert } from "react-native";
import { router } from "expo-router";
import { Feather } from "@expo/vector-icons";
import { LinearGradient } from "expo-linear-gradient";
import * as Haptics from "expo-haptics";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useC } from "@/context/ThemeContext";

export default function AstroVastuProOptions() {
  const insets = useSafeAreaInsets();
  const C = useC();
  const topPad = Platform.OS === "web" ? 67 : insets.top;
  const botPad = Platform.OS === "web" ? 34 : insets.bottom;

  const goHome = () => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    router.push("/astrovastu-pro" as any);
  };

  const goBusiness = () => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    Alert.alert(
      "Coming Soon",
      "Business Vastu (Shop / Office / Factory) abhi build ho raha hai. Bahut jaldi available hoga!",
      [{ text: "OK" }]
    );
  };

  const goReports = () => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    router.push("/my-reports" as any);
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
          <View style={{ flexDirection: "row", alignItems: "center", gap: 8 }}>
            <Text style={[s.title, { color: C.text }]}>AstroVastu Pro Premium</Text>
            <View style={s.premBadge}>
              <Feather name="award" size={9} color="#3a2404" />
              <Text style={s.premBadgeText}>PREMIUM</Text>
            </View>
          </View>
          <Text style={[s.titleSub, { color: C.textMuted }]}>Home ya Business — kya scan karna hai?</Text>
        </View>
      </View>

      <ScrollView
        contentContainerStyle={[s.content, { paddingBottom: botPad + 30 }]}
        showsVerticalScrollIndicator={false}
      >
        {/* ── HOME VASTU ADVANCED ── */}
        <Pressable onPress={goHome} style={[s.card, { borderColor: "#a78bfa", backgroundColor: C.isDark ? "#0d0a1a" : C.bgCard }]}>
          <LinearGradient
            colors={["#a78bfa18", "#7c3aed10", "transparent"]}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 1 }}
            style={StyleSheet.absoluteFill}
          />
          <View style={[s.tag, { backgroundColor: "#a78bfa22", borderColor: "#a78bfa" }]}>
            <Text style={[s.tagText, { color: "#a78bfa" }]}>FOR HOME / RESIDENCE</Text>
          </View>

          <View style={s.cardHeader}>
            <Text style={s.emoji}>🏠</Text>
            <View style={{ flex: 1 }}>
              <Text style={[s.cardTitle, { color: C.text }]}>Home Vastu Advanced</Text>
              <Text style={[s.cardTagline, { color: C.textMuted }]}>
                Kundli + multi-floor + family member match
              </Text>
            </View>
          </View>

          <View style={s.bullets}>
            <Bullet color="#a78bfa" C={C} text="Single room (Quick Check) — ₹199" />
            <Bullet color="#a78bfa" C={C} text="3-room bundle (Spot Check) — ₹499" />
            <Bullet color="#a78bfa" C={C} text="Full Home Advanced — ₹2,999 lifetime per property" />
            <Bullet color="#a78bfa" C={C} text="Mahadasha + Antardasha conflict alerts" />
            <Bullet color="#a78bfa" C={C} text="Family kundlis (up to 5) cross-match" />
            <Bullet color="#a78bfa" C={C} text="PDF download + history + WhatsApp share" />
          </View>

          <View style={[s.ctaRow, { backgroundColor: "#a78bfa22" }]}>
            <Text style={[s.ctaText, { color: "#a78bfa" }]}>Open Home Vastu</Text>
            <Feather name="arrow-right" size={16} color="#a78bfa" />
          </View>
        </Pressable>

        {/* ── BUSINESS VASTU ── */}
        <Pressable onPress={goBusiness} style={[s.card, { borderColor: "#06b6d4", backgroundColor: C.isDark ? "#04141a" : C.bgCard }]}>
          <LinearGradient
            colors={["#06b6d422", "#0891b218", "transparent"]}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 1 }}
            style={StyleSheet.absoluteFill}
          />
          <View style={[s.tag, { backgroundColor: "#06b6d422", borderColor: "#06b6d4" }]}>
            <Text style={[s.tagText, { color: "#06b6d4" }]}>FOR BUSINESS / COMMERCIAL</Text>
          </View>
          <View style={[s.soonBadge, { backgroundColor: "#f59e0b" }]}>
            <Text style={s.soonBadgeText}>COMING SOON</Text>
          </View>

          <View style={s.cardHeader}>
            <Text style={s.emoji}>🏢</Text>
            <View style={{ flex: 1 }}>
              <Text style={[s.cardTitle, { color: C.text }]}>Business Vastu</Text>
              <Text style={[s.cardTagline, { color: C.textMuted }]}>
                Shop, Office, Factory — owner kundli driven
              </Text>
            </View>
          </View>

          <View style={s.bullets}>
            <Bullet color="#06b6d4" C={C} text="🏪 Shop Vastu — ₹999 (cash counter, entrance, owner seat)" />
            <Bullet color="#06b6d4" C={C} text="🏢 Office Vastu — ₹1,499 (CEO cabin, conference, locker)" />
            <Bullet color="#06b6d4" C={C} text="🏭 Factory Vastu — ₹2,999 (machinery, raw material, boiler)" />
            <Bullet color="#06b6d4" C={C} text="Owner kundli + up to 3 partners ka analysis" />
            <Bullet color="#06b6d4" C={C} text="Business start muhurat chart consideration" />
          </View>

          <View style={[s.ctaRow, { backgroundColor: "#06b6d422" }]}>
            <Text style={[s.ctaText, { color: "#06b6d4" }]}>Notify When Ready</Text>
            <Feather name="bell" size={15} color="#06b6d4" />
          </View>
        </Pressable>

        {/* My Reports — history of paid scans */}
        <Pressable
          onPress={goReports}
          style={({ pressed }) => [
            s.reportsCard,
            {
              backgroundColor: C.isDark ? "#0e1318" : C.bgCard,
              borderColor: C.border,
              opacity: pressed ? 0.85 : 1,
            },
          ]}
        >
          <View style={[s.reportsIcon, { backgroundColor: "#f6c45322", borderColor: "#f6c453" }]}>
            <Feather name="folder" size={18} color="#f6c453" />
          </View>
          <View style={{ flex: 1 }}>
            <Text style={[s.reportsTitle, { color: C.text }]}>My Reports</Text>
            <Text style={[s.reportsSub, { color: C.textMuted }]}>
              View &amp; share all your past PDF scans
            </Text>
          </View>
          <Feather name="chevron-right" size={18} color={C.textMuted} />
        </Pressable>

        {/* Pro discount note */}
        <View style={[s.noteCard, { backgroundColor: C.bgCard, borderColor: C.border }]}>
          <Feather name="zap" size={14} color="#f59e0b" />
          <Text style={[s.noteText, { color: C.textMuted }]}>
            <Text style={{ fontWeight: "800", color: "#f59e0b" }}>General Pro subscribers</Text> get{" "}
            <Text style={{ fontWeight: "800", color: C.text }}>20% off</Text> on all AstroVastu purchases above.
          </Text>
        </View>

        <Text style={[s.branding, { color: C.textDim }]}>
          Powered by Advanced Cosmic Intelligence
        </Text>
      </ScrollView>
    </View>
  );
}

function Bullet({ C, text, color }: { C: any; text: string; color: string }) {
  return (
    <View style={s.bulletRow}>
      <Feather name="check" size={13} color={color} />
      <Text style={[s.bulletText, { color: C.textMid || C.text }]}>{text}</Text>
    </View>
  );
}

const s = StyleSheet.create({
  root:           { flex: 1 },
  header:         { flexDirection: "row", alignItems: "center", gap: 12, paddingHorizontal: 16, paddingBottom: 14, borderBottomWidth: 1 },
  back:           { width: 36, height: 36, alignItems: "center", justifyContent: "center" },
  title:          { fontSize: 16, fontWeight: "800" },
  titleSub:       { fontSize: 11, marginTop: 2 },
  premBadge:      { flexDirection: "row", alignItems: "center", gap: 3, backgroundColor: "#f9d76b", paddingHorizontal: 6, paddingVertical: 2, borderRadius: 5 },
  premBadgeText:  { fontSize: 8, fontWeight: "900", color: "#3a2404", letterSpacing: 0.6 },
  content:        { paddingHorizontal: 16, paddingTop: 18, gap: 14 },
  card:           { borderRadius: 18, borderWidth: 2, padding: 16, gap: 12, position: "relative", overflow: "hidden" },
  tag:            { flexDirection: "row", alignItems: "center", alignSelf: "flex-start", paddingHorizontal: 9, paddingVertical: 4, borderRadius: 7, borderWidth: 1 },
  tagText:        { fontSize: 9, fontWeight: "900", letterSpacing: 1.2 },
  soonBadge:      { position: "absolute", top: 14, right: 14, paddingHorizontal: 8, paddingVertical: 3, borderRadius: 6 },
  soonBadgeText:  { fontSize: 8, fontWeight: "900", color: "#3a2404", letterSpacing: 1 },
  cardHeader:     { flexDirection: "row", alignItems: "center", gap: 12 },
  emoji:          { fontSize: 36 },
  cardTitle:      { fontSize: 17, fontWeight: "800", marginBottom: 3 },
  cardTagline:    { fontSize: 12, lineHeight: 16 },
  bullets:        { gap: 7, marginTop: 4 },
  bulletRow:      { flexDirection: "row", alignItems: "flex-start", gap: 8 },
  bulletText:     { fontSize: 12, lineHeight: 17, flex: 1 },
  ctaRow:         { flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 8, paddingVertical: 11, borderRadius: 10, marginTop: 6 },
  ctaText:        { fontSize: 13, fontWeight: "800", letterSpacing: 0.3 },
  reportsCard:    { flexDirection: "row", alignItems: "center", gap: 12, padding: 14, borderRadius: 12, borderWidth: 1, marginTop: 4 },
  reportsIcon:    { width: 38, height: 38, borderRadius: 10, borderWidth: 1, alignItems: "center", justifyContent: "center" },
  reportsTitle:   { fontSize: 14, fontWeight: "800" },
  reportsSub:     { fontSize: 11, marginTop: 2 },
  noteCard:       { flexDirection: "row", alignItems: "center", gap: 10, padding: 12, borderRadius: 12, borderWidth: 1, marginTop: 4 },
  noteText:       { fontSize: 11, lineHeight: 16, flex: 1 },
  branding:       { fontSize: 10, textAlign: "center", marginTop: 8, letterSpacing: 1.2, fontWeight: "600" },
});
