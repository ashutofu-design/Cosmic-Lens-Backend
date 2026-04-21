import { Feather } from "@expo/vector-icons";
import { router } from "expo-router";
import React from "react";
import { Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { useC } from "@/context/ThemeContext";

export default function FaceReadingScreen() {
  const C = useC();
  const insets = useSafeAreaInsets();

  return (
    <View style={[styles.root, { backgroundColor: C.bg, paddingTop: insets.top }]}>
      {/* Header */}
      <View style={styles.header}>
        <Pressable onPress={() => router.back()} style={styles.backBtn} hitSlop={12}>
          <Feather name="chevron-left" size={26} color={C.text} />
        </Pressable>
        <Text style={[styles.headerTitle, { color: C.text }]}>Face Reading Pro</Text>
        <View style={{ width: 26 }} />
      </View>

      <ScrollView contentContainerStyle={styles.scroll} showsVerticalScrollIndicator={false}>
        {/* Hero */}
        <View style={[styles.hero, { backgroundColor: C.card, borderColor: C.border }]}>
          <Text style={styles.eyeEmoji}>👁️</Text>
          <Text style={[styles.heroTitle, { color: C.text }]}>
            World's First{"\n"}Vedic + Science Fusion
          </Text>
          <Text style={[styles.heroSub, { color: C.muted }]}>
            80+ page personalized report combining 16 ancient & modern frameworks
          </Text>
          <View style={styles.badge}>
            <Text style={styles.badgeText}>Coming Soon</Text>
          </View>
        </View>

        {/* What's Inside */}
        <Text style={[styles.section, { color: C.text }]}>What's Inside</Text>

        <Card C={C} icon="🕉️" title="8 Vedic Engines" body="Samudrika Shastra, Mukha Lakshana, Lalat Rekha, Netra Vigyan, Ayurvedic Prakriti, Mian Xiang Palaces, 100-Year Age Map, Wu Xing 5 Elements" />
        <Card C={C} icon="🧬" title="8 Scientific Engines" body="Anthropometry (32 points), Symmetry, Golden Ratio, fWHR, Health Indicators, Big Five (OCEAN), First Impression, Phenotype Profile" />
        <Card C={C} icon="🔗" title="3 Fusion Engines" body="Vedic-Science Cross-Validation, Numerology Combo, Predictive Synthesis (career, marriage, wealth, health)" />
        <Card C={C} icon="✍️" title="AI Storytelling" body="Each insight narrated in Ashutosh Bharadwaj voice with classical authority + modern clarity" />

        {/* How It Works */}
        <Text style={[styles.section, { color: C.text }]}>How It Works</Text>
        <Step C={C} n="1" title="Upload 3 selfies" body="Front + left + right profile (guided capture)" />
        <Step C={C} n="2" title="AI verifies quality" body="Lighting, angle, focus check" />
        <Step C={C} n="3" title="468 face landmarks extracted" body="Google Mediapipe (free, on-device accurate)" />
        <Step C={C} n="4" title="19 engines analyze in parallel" body="Pure mathematical + classical rules" />
        <Step C={C} n="5" title="80-page PDF report generated" body="Delivered in ~45 seconds" />

        {/* Notify */}
        <View style={[styles.notifyCard, { backgroundColor: C.card, borderColor: C.border }]}>
          <Feather name="bell" size={20} color="#ec4899" />
          <Text style={[styles.notifyText, { color: C.text }]}>
            Engine under construction. We'll notify you the day it launches.
          </Text>
        </View>

        <View style={{ height: 40 }} />
      </ScrollView>
    </View>
  );
}

function Card({ C, icon, title, body }: { C: any; icon: string; title: string; body: string }) {
  return (
    <View style={[styles.card, { backgroundColor: C.card, borderColor: C.border }]}>
      <Text style={styles.cardIcon}>{icon}</Text>
      <View style={{ flex: 1 }}>
        <Text style={[styles.cardTitle, { color: C.text }]}>{title}</Text>
        <Text style={[styles.cardBody, { color: C.muted }]}>{body}</Text>
      </View>
    </View>
  );
}

function Step({ C, n, title, body }: { C: any; n: string; title: string; body: string }) {
  return (
    <View style={[styles.step, { backgroundColor: C.card, borderColor: C.border }]}>
      <View style={styles.stepNum}>
        <Text style={styles.stepNumText}>{n}</Text>
      </View>
      <View style={{ flex: 1 }}>
        <Text style={[styles.stepTitle, { color: C.text }]}>{title}</Text>
        <Text style={[styles.stepBody, { color: C.muted }]}>{body}</Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1 },
  header: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: 16,
    paddingBottom: 12,
  },
  backBtn: { padding: 4 },
  headerTitle: { fontSize: 17, fontWeight: "700" },
  scroll: { paddingHorizontal: 16, paddingBottom: 24 },
  hero: {
    borderRadius: 20,
    borderWidth: 1,
    padding: 24,
    alignItems: "center",
    marginBottom: 24,
  },
  eyeEmoji: { fontSize: 56, marginBottom: 12 },
  heroTitle: { fontSize: 22, fontWeight: "800", textAlign: "center", lineHeight: 30 },
  heroSub: { fontSize: 14, textAlign: "center", marginTop: 10, lineHeight: 20 },
  badge: {
    marginTop: 16,
    backgroundColor: "#ec4899",
    paddingHorizontal: 14,
    paddingVertical: 6,
    borderRadius: 999,
  },
  badgeText: { color: "#fff", fontWeight: "700", fontSize: 12, letterSpacing: 0.5 },
  section: { fontSize: 16, fontWeight: "700", marginTop: 8, marginBottom: 12 },
  card: {
    flexDirection: "row",
    gap: 12,
    padding: 14,
    borderRadius: 14,
    borderWidth: 1,
    marginBottom: 10,
  },
  cardIcon: { fontSize: 26 },
  cardTitle: { fontSize: 15, fontWeight: "700", marginBottom: 4 },
  cardBody: { fontSize: 13, lineHeight: 18 },
  step: {
    flexDirection: "row",
    gap: 12,
    padding: 12,
    borderRadius: 12,
    borderWidth: 1,
    marginBottom: 8,
    alignItems: "center",
  },
  stepNum: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: "#ec4899",
    alignItems: "center",
    justifyContent: "center",
  },
  stepNumText: { color: "#fff", fontWeight: "800", fontSize: 14 },
  stepTitle: { fontSize: 14, fontWeight: "700", marginBottom: 2 },
  stepBody: { fontSize: 12, lineHeight: 16 },
  notifyCard: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    padding: 14,
    borderRadius: 12,
    borderWidth: 1,
    marginTop: 16,
  },
  notifyText: { flex: 1, fontSize: 13, lineHeight: 18 },
});
