import { Feather } from "@expo/vector-icons";
import { LinearGradient } from "expo-linear-gradient";
import { router } from "expo-router";
import React, { useEffect, useRef } from "react";
import {
  Animated,
  Easing,
  Platform,
  Pressable,
  ScrollView,
  StatusBar,
  StyleSheet,
  Text,
  View,
} from "react-native";
import Svg, { Circle, Defs, LinearGradient as SvgGrad, Stop } from "react-native-svg";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { CosmicBg } from "@/components/CosmicBg";
import { useC } from "@/context/ThemeContext";

const ACCENT = "#ec4899";
const ACCENT_2 = "#7B1F1F";
const GOLD = "#C2A878";

// ─── Animated glowing eye orb ─────────────────────────────────────────────────
function GlowOrb() {
  const pulse = useRef(new Animated.Value(0)).current;
  useEffect(() => {
    Animated.loop(
      Animated.sequence([
        Animated.timing(pulse, { toValue: 1, duration: 1800, easing: Easing.inOut(Easing.ease), useNativeDriver: true }),
        Animated.timing(pulse, { toValue: 0, duration: 1800, easing: Easing.inOut(Easing.ease), useNativeDriver: true }),
      ])
    ).start();
  }, []);
  const scale = pulse.interpolate({ inputRange: [0, 1], outputRange: [1, 1.08] });
  const opacity = pulse.interpolate({ inputRange: [0, 1], outputRange: [0.45, 0.85] });
  return (
    <View style={s.orbWrap}>
      <Animated.View style={[s.orbGlow, { transform: [{ scale }], opacity }]} />
      <Svg width={108} height={108} viewBox="0 0 108 108">
        <Defs>
          <SvgGrad id="orb" x1="0" y1="0" x2="1" y2="1">
            <Stop offset="0" stopColor={ACCENT} stopOpacity={0.95} />
            <Stop offset="1" stopColor={GOLD} stopOpacity={0.85} />
          </SvgGrad>
        </Defs>
        <Circle cx={54} cy={54} r={50} fill="url(#orb)" />
        <Circle cx={54} cy={54} r={50} fill="none" stroke="#fff" strokeOpacity={0.25} strokeWidth={1.5} />
      </Svg>
      <Text style={s.orbEmoji}>👁️</Text>
    </View>
  );
}

// ─── Reusable cards ───────────────────────────────────────────────────────────
function StatPill({ value, label, C }: { value: string; label: string; C: any }) {
  return (
    <View style={[s.statPill, { backgroundColor: C.bgCard, borderColor: C.border }]}>
      <Text style={[s.statValue, { color: C.text }]}>{value}</Text>
      <Text style={[s.statLabel, { color: C.textMuted }]}>{label}</Text>
    </View>
  );
}

function PreviewCard({ icon, title, sub, color, C }: { icon: string; title: string; sub: string; color: string; C: any }) {
  return (
    <View style={[s.previewCard, { borderColor: C.border, backgroundColor: C.bgCard }]}>
      <LinearGradient
        colors={[`${color}22`, `${color}05`]}
        start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }}
        style={s.previewGrad}
      />
      <Text style={s.previewIcon}>{icon}</Text>
      <Text style={[s.previewTitle, { color: C.text }]} numberOfLines={1}>{title}</Text>
      <Text style={[s.previewSub, { color: C.textMuted }]} numberOfLines={2}>{sub}</Text>
    </View>
  );
}

function EngineCard({ icon, count, group, body, color, C }: { icon: string; count: string; group: string; body: string; color: string; C: any }) {
  return (
    <View style={[s.engineCard, { borderColor: C.border, backgroundColor: C.bgCard }]}>
      <View style={[s.engineIconBox, { backgroundColor: `${color}18`, borderColor: `${color}55` }]}>
        <Text style={s.engineIcon}>{icon}</Text>
      </View>
      <View style={{ flex: 1, gap: 3 }}>
        <View style={s.engineHeadRow}>
          <Text style={[s.engineCount, { color }]}>{count}</Text>
          <Text style={[s.engineGroup, { color: C.text }]}>{group}</Text>
        </View>
        <Text style={[s.engineBody, { color: C.textMuted }]}>{body}</Text>
      </View>
    </View>
  );
}

function StepRow({ n, title, body, color, last, C }: { n: string; title: string; body: string; color: string; last?: boolean; C: any }) {
  return (
    <View style={s.stepRow}>
      <View style={s.stepLeft}>
        <LinearGradient
          colors={[color, `${color}aa`]}
          start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }}
          style={s.stepNum}
        >
          <Text style={s.stepNumText}>{n}</Text>
        </LinearGradient>
        {!last && <View style={[s.stepLine, { backgroundColor: C.border }]} />}
      </View>
      <View style={{ flex: 1, paddingTop: 2, paddingBottom: 14 }}>
        <Text style={[s.stepTitle, { color: C.text }]}>{title}</Text>
        <Text style={[s.stepBody, { color: C.textMuted }]}>{body}</Text>
      </View>
    </View>
  );
}

function AuthorityChip({ label, C }: { label: string; C: any }) {
  return (
    <View style={[s.authChip, { borderColor: C.border, backgroundColor: C.bgCard2 }]}>
      <Text style={[s.authChipText, { color: C.textMuted }]}>{label}</Text>
    </View>
  );
}

// ─── Screen ───────────────────────────────────────────────────────────────────
export default function FaceReadingScreen() {
  const C = useC();
  const insets = useSafeAreaInsets();
  const androidSB = StatusBar.currentHeight ?? 24;
  const topPad = Platform.OS === "android" ? Math.max(insets.top, androidSB) : insets.top;

  return (
    <CosmicBg>
      {/* Header */}
      <View style={[s.header, { paddingTop: topPad + 4 }]}>
        <Pressable onPress={() => router.back()} style={s.backBtn} hitSlop={12}>
          <Feather name="chevron-left" size={26} color={C.text} />
        </Pressable>
        <Text style={[s.headerTitle, { color: C.text }]}>Face Reading Pro</Text>
        <View style={{ width: 26 }} />
      </View>

      <ScrollView
        contentContainerStyle={[s.scroll, { paddingBottom: insets.bottom + 32 }]}
        showsVerticalScrollIndicator={false}
      >
        {/* ───── HERO ───── */}
        <View style={[s.heroWrap, { borderColor: C.border }]}>
          <LinearGradient
            colors={[`${ACCENT_2}55`, `${ACCENT}22`, "transparent"]}
            start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }}
            style={StyleSheet.absoluteFill as any}
          />
          <GlowOrb />
          <Text style={[s.heroEyebrow, { color: GOLD }]}>WORLD'S FIRST</Text>
          <Text style={[s.heroTitle, { color: C.text }]}>
            Vedic + Science{"\n"}Face Reading Fusion
          </Text>
          <Text style={[s.heroSub, { color: C.textMuted }]}>
            40-page premium PDF report combining 19 ancient & modern frameworks — narrated in Hinglish storytelling.
          </Text>
          <View style={s.heroBadgeRow}>
            <LinearGradient
              colors={[ACCENT, "#a21caf"]}
              start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }}
              style={s.priceBadge}
            >
              <Text style={s.priceBadgeText}>₹1499</Text>
              <Text style={s.priceBadgeSub}> · Coming Soon</Text>
            </LinearGradient>
          </View>
        </View>

        {/* ───── STAT STRIP ───── */}
        <View style={s.statsRow}>
          <StatPill value="40" label="pages" C={C} />
          <StatPill value="22" label="sections" C={C} />
          <StatPill value="19" label="engines" C={C} />
          <StatPill value="468" label="landmarks" C={C} />
        </View>

        {/* ───── INSIDE YOUR REPORT ───── */}
        <Text style={[s.sectionCap, { color: C.textDim }]}>INSIDE YOUR REPORT</Text>
        <View style={s.previewGrid}>
          <PreviewCard icon="📔" title="Branded Cover"  sub="Aapki photo · personalized seal"  color={ACCENT_2} C={C} />
          <PreviewCard icon="🗺️" title="7-Zone Face Map" sub="Annotated landmarks + callouts"   color="#7c6ed4" C={C} />
          <PreviewCard icon="📊" title="Visual Snapshot" sub="OCEAN radar + 5-score chart"      color="#10b981" C={C} />
          <PreviewCard icon="⭐" title="Celeb Match"    sub="Archetype × element library"      color={GOLD}   C={C} />
        </View>

        {/* ───── 19 ENGINES ───── */}
        <Text style={[s.sectionCap, { color: C.textDim }]}>19 ANALYSIS ENGINES</Text>
        <EngineCard
          icon="🕉️" count="8" group="Vedic Engines"
          body="Samudrika Shastra · Mukha Lakshana · Lalat Rekha · Netra Vigyan · Ayurvedic Prakriti · Mian Xiang · 100-Year Age Map · Wu Xing 5 Elements"
          color={ACCENT_2} C={C}
        />
        <EngineCard
          icon="🧬" count="8" group="Scientific Engines"
          body="Anthropometry (32 pts) · Symmetry · Golden Ratio (φ) · fWHR · Health Indicators · Big Five OCEAN · First Impression · Phenotype Profile"
          color="#7c6ed4" C={C}
        />
        <EngineCard
          icon="🔗" count="3" group="Fusion Engines"
          body="Vedic-Science Cross-Validation · Numerology Combo · Predictive Synthesis (career, marriage, wealth, health)"
          color="#10b981" C={C}
        />

        {/* ───── HOW IT WORKS ───── */}
        <Text style={[s.sectionCap, { color: C.textDim }]}>HOW IT WORKS</Text>
        <View style={[s.stepsCard, { borderColor: C.border, backgroundColor: C.bgCard }]}>
          <StepRow n="1" title="Upload 3 selfies"           body="Front + left + right profile (guided capture, lighting & angle check)" color={ACCENT}    C={C} />
          <StepRow n="2" title="468 landmarks extracted"    body="Google Mediapipe — runs on-device for privacy"                          color="#7c6ed4"  C={C} />
          <StepRow n="3" title="19 engines analyze parallel" body="~75% real CV measurements · 0% fake or hardcoded data"                  color="#10b981"  C={C} />
          <StepRow n="4" title="40-page PDF generated"      body="Visual charts, face map, Hinglish narrative · ready in ~45 seconds"     color={GOLD}     last C={C} />
        </View>

        {/* ───── AUTHORITY STRIP ───── */}
        <Text style={[s.sectionCap, { color: C.textDim }]}>BUILT ON</Text>
        <View style={s.authRow}>
          <AuthorityChip label="MediaPipe" C={C} />
          <AuthorityChip label="Samudrika Shastra" C={C} />
          <AuthorityChip label="Big Five OCEAN" C={C} />
          <AuthorityChip label="Wu Xing 五行" C={C} />
          <AuthorityChip label="Golden Ratio φ" C={C} />
          <AuthorityChip label="Mian Xiang 面相" C={C} />
        </View>

        {/* ───── DATA HONESTY ───── */}
        <View style={[s.honestCard, { borderColor: C.border, backgroundColor: C.bgCard }]}>
          <View style={s.honestHead}>
            <Feather name="shield" size={14} color="#10b981" />
            <Text style={[s.honestTitle, { color: "#10b981" }]}>100% Honest Data</Text>
          </View>
          <View style={s.honestRow}>
            <View style={[s.honestBar, { backgroundColor: C.bgCard2 }]}>
              <View style={[s.honestFill, { width: "75%", backgroundColor: "#10b981" }]} />
            </View>
            <Text style={[s.honestLabel, { color: C.textMuted }]}>75% real CV measurements</Text>
          </View>
          <View style={s.honestRow}>
            <View style={[s.honestBar, { backgroundColor: C.bgCard2 }]}>
              <View style={[s.honestFill, { width: "20%", backgroundColor: GOLD }]} />
            </View>
            <Text style={[s.honestLabel, { color: C.textMuted }]}>20% derived (real numbers + Hinglish prose)</Text>
          </View>
          <View style={s.honestRow}>
            <View style={[s.honestBar, { backgroundColor: C.bgCard2 }]}>
              <View style={[s.honestFill, { width: "5%", backgroundColor: "#7c6ed4" }]} />
            </View>
            <Text style={[s.honestLabel, { color: C.textMuted }]}>5% curated (celeb library, combo titles)</Text>
          </View>
          <Text style={[s.honestFootnote, { color: C.textDim }]}>
            Zero fake or hardcoded readings — sab kuch aapki actual photo se nikalta hai.
          </Text>
        </View>

        {/* ───── CTA ───── */}
        <Pressable style={s.ctaWrap} onPress={() => { /* TODO: notify-me API */ }}>
          <LinearGradient
            colors={[ACCENT, "#a21caf"]}
            start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }}
            style={s.ctaBtn}
          >
            <Feather name="bell" size={16} color="#fff" />
            <Text style={s.ctaText}>Notify Me on Launch</Text>
          </LinearGradient>
        </Pressable>
        <Text style={[s.ctaSub, { color: C.textDim }]}>
          Engine under final QA. Aapko launch ke din pehle slot milega.
        </Text>
      </ScrollView>
    </CosmicBg>
  );
}

// ─── Styles ───────────────────────────────────────────────────────────────────
const s = StyleSheet.create({
  header: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: 16,
    paddingBottom: 10,
  },
  backBtn: { padding: 4 },
  headerTitle: { fontSize: 17, fontWeight: "700" },
  scroll: { paddingHorizontal: 16, gap: 14 },

  // Hero
  heroWrap: {
    borderRadius: 24,
    borderWidth: 1,
    paddingTop: 26,
    paddingBottom: 24,
    paddingHorizontal: 22,
    alignItems: "center",
    overflow: "hidden",
    marginBottom: 4,
  },
  orbWrap: {
    width: 108, height: 108,
    alignItems: "center", justifyContent: "center",
    marginBottom: 14,
  },
  orbGlow: {
    position: "absolute",
    width: 130, height: 130,
    borderRadius: 65,
    backgroundColor: ACCENT,
  },
  orbEmoji: { position: "absolute", fontSize: 46 },
  heroEyebrow: { fontSize: 11, fontWeight: "800", letterSpacing: 2.5, marginBottom: 6 },
  heroTitle: { fontSize: 24, fontWeight: "800", textAlign: "center", lineHeight: 32 },
  heroSub: { fontSize: 13.5, textAlign: "center", marginTop: 12, lineHeight: 20, paddingHorizontal: 4 },
  heroBadgeRow: { marginTop: 18 },
  priceBadge: {
    flexDirection: "row", alignItems: "center",
    paddingHorizontal: 18, paddingVertical: 9, borderRadius: 999,
  },
  priceBadgeText: { color: "#fff", fontWeight: "800", fontSize: 16, letterSpacing: 0.3 },
  priceBadgeSub:  { color: "#fff", fontWeight: "600", fontSize: 12, opacity: 0.92 },

  // Stats
  statsRow: { flexDirection: "row", gap: 8, marginTop: 4 },
  statPill: {
    flex: 1, borderWidth: 1, borderRadius: 14,
    paddingVertical: 12, alignItems: "center", gap: 2,
  },
  statValue: { fontSize: 18, fontWeight: "800" },
  statLabel: { fontSize: 10, fontWeight: "600", letterSpacing: 0.6, textTransform: "uppercase" },

  // Section caps
  sectionCap: {
    fontSize: 10, fontWeight: "700", letterSpacing: 2,
    marginTop: 14, marginBottom: 4, paddingLeft: 2,
  },

  // Preview grid
  previewGrid: { flexDirection: "row", flexWrap: "wrap", gap: 10 },
  previewCard: {
    width: "48.5%",
    borderRadius: 16, borderWidth: 1,
    paddingHorizontal: 14, paddingVertical: 14,
    overflow: "hidden",
    minHeight: 110,
  },
  previewGrad: { borderRadius: 16 },
  previewIcon: { fontSize: 24, marginBottom: 6 },
  previewTitle: { fontSize: 13.5, fontWeight: "700", marginBottom: 3 },
  previewSub: { fontSize: 11, lineHeight: 15 },

  // Engine card
  engineCard: {
    flexDirection: "row", gap: 12, alignItems: "center",
    borderRadius: 16, borderWidth: 1, padding: 14,
  },
  engineIconBox: {
    width: 46, height: 46, borderRadius: 12, borderWidth: 1,
    alignItems: "center", justifyContent: "center",
  },
  engineIcon: { fontSize: 22 },
  engineHeadRow: { flexDirection: "row", alignItems: "baseline", gap: 8 },
  engineCount: { fontSize: 18, fontWeight: "800" },
  engineGroup: { fontSize: 14, fontWeight: "700" },
  engineBody:  { fontSize: 11.5, lineHeight: 17 },

  // Steps
  stepsCard: { borderWidth: 1, borderRadius: 18, padding: 16, paddingBottom: 4 },
  stepRow: { flexDirection: "row", gap: 12 },
  stepLeft: { width: 32, alignItems: "center" },
  stepNum: {
    width: 30, height: 30, borderRadius: 15,
    alignItems: "center", justifyContent: "center",
  },
  stepNumText: { color: "#fff", fontWeight: "800", fontSize: 13 },
  stepLine: { width: 2, flex: 1, marginTop: 2, opacity: 0.6 },
  stepTitle: { fontSize: 14, fontWeight: "700", marginBottom: 2 },
  stepBody:  { fontSize: 12, lineHeight: 17 },

  // Authority chips
  authRow: { flexDirection: "row", flexWrap: "wrap", gap: 7 },
  authChip: {
    paddingHorizontal: 11, paddingVertical: 6,
    borderRadius: 999, borderWidth: 1,
  },
  authChipText: { fontSize: 11, fontWeight: "600" },

  // Honesty card
  honestCard: { borderWidth: 1, borderRadius: 16, padding: 14, gap: 10, marginTop: 4 },
  honestHead: { flexDirection: "row", alignItems: "center", gap: 6 },
  honestTitle: { fontSize: 13, fontWeight: "700" },
  honestRow: { gap: 4 },
  honestBar: { height: 7, borderRadius: 4, overflow: "hidden" },
  honestFill: { height: "100%", borderRadius: 4 },
  honestLabel: { fontSize: 11.5 },
  honestFootnote: { fontSize: 11, fontStyle: "italic", marginTop: 2 },

  // CTA
  ctaWrap: { marginTop: 18, borderRadius: 16, overflow: "hidden" },
  ctaBtn: {
    flexDirection: "row", gap: 8, alignItems: "center", justifyContent: "center",
    paddingVertical: 15, borderRadius: 16,
  },
  ctaText: { color: "#fff", fontWeight: "800", fontSize: 15, letterSpacing: 0.3 },
  ctaSub:  { fontSize: 11, textAlign: "center", marginTop: 8 },
});
