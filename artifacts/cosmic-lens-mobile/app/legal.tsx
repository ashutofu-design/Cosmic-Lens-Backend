import { Feather } from "@expo/vector-icons";
import React from "react";
import { StyleSheet, Text, View } from "react-native";
import LegalScreen, { Section, P, Bullet, Callout } from "@/components/LegalScreen";
import { useC } from "@/context/ThemeContext";
import { useT } from "@/hooks/useT";

const F = {
  regular:  "Nunito_400Regular",
  medium:   "Nunito_500Medium",
  semibold: "Nunito_600SemiBold",
  bold:     "Nunito_700Bold",
} as const;

function DocHeading({ icon, title }: { icon: keyof typeof Feather.glyphMap; title: string }) {
  const C = useC();
  const accent = C.isDark ? "#f59e0b" : "#7C3AED";
  return (
    <View style={d.wrap}>
      <View style={[d.line, { backgroundColor: C.border }]} />
      <View style={[d.pill, { backgroundColor: C.bgCard, borderColor: accent + "55" }]}>
        <Feather name={icon} size={14} color={accent} />
        <Text style={[d.title, { color: C.text }]}>{title}</Text>
      </View>
      <View style={[d.line, { backgroundColor: C.border }]} />
    </View>
  );
}

export default function LegalAndPoliciesScreen() {
  const t = useT();
  return (
    <LegalScreen
      title={t.lg_title}
      subtitle={t.lg_subtitle}
      lastUpdated={t.lg_lastUpdated}
    >
      {/* ═══════════════════════ PRIVACY POLICY ═══════════════════════ */}
      <DocHeading icon="shield" title={t.lg_h_privacy} />

      <P>{t.lg_p_privacyIntro}</P>

      <Callout tone="info">{t.lg_callout_privacy}</Callout>

      <Section title={t.lg_s1_title}>
        <P>{t.lg_s1_a}</P>
        <P>{t.lg_s1_b}</P>
        <P>{t.lg_s1_c}</P>
        <P>{t.lg_s1_d}</P>
        <P>{t.lg_s1_e}</P>
      </Section>

      <Section title={t.lg_s2_title}>
        <Bullet>{t.lg_s2_b1}</Bullet>
        <Bullet>{t.lg_s2_b2}</Bullet>
        <Bullet>{t.lg_s2_b3}</Bullet>
        <Bullet>{t.lg_s2_b4}</Bullet>
        <Bullet>{t.lg_s2_b5}</Bullet>
        <Bullet>{t.lg_s2_b6}</Bullet>
        <Bullet>{t.lg_s2_b7}</Bullet>
        <Bullet>{t.lg_s2_b8}</Bullet>
      </Section>

      <Section title={t.lg_s3_title}>
        <P>{t.lg_s3_intro}</P>
        <Bullet>{t.lg_s3_b1}</Bullet>
        <Bullet>{t.lg_s3_b2}</Bullet>
        <Bullet>{t.lg_s3_b3}</Bullet>
        <Bullet>{t.lg_s3_b4}</Bullet>
        <P>{t.lg_s3_outro}</P>
      </Section>

      <Section title={t.lg_s4_title}>
        <P>{t.lg_s4_p}</P>
      </Section>

      <Section title={t.lg_s5_title}>
        <Bullet>{t.lg_s5_b1}</Bullet>
        <Bullet>{t.lg_s5_b2}</Bullet>
        <Bullet>{t.lg_s5_b3}</Bullet>
        <Bullet>{t.lg_s5_b4}</Bullet>
        <Bullet>{t.lg_s5_b5}</Bullet>
      </Section>

      <Section title={t.lg_s6_title}>
        <P>{t.lg_s6_intro}</P>
        <Bullet>{t.lg_s6_b1}</Bullet>
        <Bullet>{t.lg_s6_b2}</Bullet>
        <Bullet>{t.lg_s6_b3}</Bullet>
        <Bullet>{t.lg_s6_b4}</Bullet>
        <Bullet>{t.lg_s6_b5}</Bullet>
        <P>{t.lg_s6_outro}</P>
      </Section>

      <Section title={t.lg_s7_title}>
        <P>{t.lg_s7_p}</P>
      </Section>

      <Section title={t.lg_s8_title}>
        <P>{t.lg_s8_p}</P>
      </Section>

      <Section title={t.lg_s9_title}>
        <P>{t.lg_s9_p}</P>
      </Section>

      <Section title={t.lg_s10_title}>
        <P>{t.lg_s10_p}</P>
      </Section>

      <Section title={t.lg_s11_title}>
        <P>{t.lg_s11_intro}</P>
        <Bullet>{t.lg_s11_b1}</Bullet>
        <Bullet>{t.lg_s11_b2}</Bullet>
      </Section>

      {/* ═══════════════════════ TERMS OF SERVICE ═══════════════════════ */}
      <DocHeading icon="file-text" title={t.lg_h_terms} />

      <P>{t.lg_p_termsIntro}</P>

      <Section title={t.lg_t1_title}>
        <Bullet>{t.lg_t1_b1}</Bullet>
        <Bullet>{t.lg_t1_b2}</Bullet>
        <Bullet>{t.lg_t1_b3}</Bullet>
      </Section>

      <Section title={t.lg_t2_title}>
        <Bullet>{t.lg_t2_b1}</Bullet>
        <Bullet>{t.lg_t2_b2}</Bullet>
        <Bullet>{t.lg_t2_b3}</Bullet>
        <Bullet>{t.lg_t2_b4}</Bullet>
      </Section>

      <Section title={t.lg_t3_title}>
        <P>{t.lg_t3_p}</P>
      </Section>

      <Section title={t.lg_t4_title}>
        <P>{t.lg_t4_intro}</P>
        <Bullet>{t.lg_t4_b1}</Bullet>
        <Bullet>{t.lg_t4_b2}</Bullet>
        <Bullet>{t.lg_t4_b3}</Bullet>
        <Bullet>{t.lg_t4_b4}</Bullet>
        <P>{t.lg_t4_outro}</P>
      </Section>

      <Section title={t.lg_t5_title}>
        <P>{t.lg_t5_p}</P>
      </Section>

      <Section title={t.lg_t6_title}>
        <P>{t.lg_t6_p}</P>
      </Section>

      <Section title={t.lg_t7_title}>
        <Bullet>{t.lg_t7_b1}</Bullet>
        <Bullet>{t.lg_t7_b2}</Bullet>
        <Bullet>{t.lg_t7_b3}</Bullet>
        <Bullet>{t.lg_t7_b4}</Bullet>
        <Bullet>{t.lg_t7_b5}</Bullet>
        <Bullet>{t.lg_t7_b6}</Bullet>
      </Section>

      <Section title={t.lg_t8_title}>
        <P>{t.lg_t8_p}</P>
      </Section>

      <Section title={t.lg_t9_title}>
        <P>{t.lg_t9_p}</P>
      </Section>

      <Section title={t.lg_t10_title}>
        <Callout tone="warn">{t.lg_t10_callout}</Callout>
      </Section>

      <Section title={t.lg_t11_title}>
        <P>{t.lg_t11_p}</P>
      </Section>

      <Section title={t.lg_t12_title}>
        <P>{t.lg_t12_p}</P>
      </Section>

      <Section title={t.lg_t13_title}>
        <P>{t.lg_t13_p}</P>
      </Section>

      <Section title={t.lg_t14_title}>
        <P>{t.lg_t14_p}</P>
      </Section>

      <Section title={t.lg_t15_title}>
        <P>{t.lg_t15_p}</P>
      </Section>

      <Section title={t.lg_t16_title}>
        <P>{t.lg_t16_p}</P>
      </Section>

      {/* ═══════════════════════ REFUND & CANCELLATION ═══════════════════════ */}
      <DocHeading icon="rotate-ccw" title={t.lg_h_refund} />

      <P>{t.lg_p_refundIntro}</P>

      <Callout tone="info">{t.lg_callout_refund}</Callout>

      <Section title={t.lg_r1_title}>
        <P>{t.lg_r1_intro}</P>
        <Bullet>{t.lg_r1_b1}</Bullet>
        <Bullet>{t.lg_r1_b2}</Bullet>
        <P>{t.lg_r1_outro}</P>
      </Section>

      <Section title={t.lg_r2_title}>
        <P>{t.lg_r2_intro}</P>
        <Bullet>{t.lg_r2_b1}</Bullet>
        <Bullet>{t.lg_r2_b2}</Bullet>
        <Bullet>{t.lg_r2_b3}</Bullet>
        <Bullet>{t.lg_r2_b4}</Bullet>
      </Section>

      <Section title={t.lg_r3_title}>
        <Bullet>{t.lg_r3_b1}</Bullet>
        <Bullet>{t.lg_r3_b2}</Bullet>
        <Bullet>{t.lg_r3_b3}</Bullet>
        <Bullet>{t.lg_r3_b4}</Bullet>
        <Bullet>{t.lg_r3_b5}</Bullet>
        <Bullet>{t.lg_r3_b6}</Bullet>
      </Section>

      <Section title={t.lg_r4_title}>
        <P>{t.lg_r4_intro}</P>
        <Bullet>{t.lg_r4_b1}</Bullet>
        <Bullet>{t.lg_r4_b2}</Bullet>
        <Bullet>{t.lg_r4_b3}</Bullet>
        <P>{t.lg_r4_outro}</P>
      </Section>

      <Section title={t.lg_r5_title}>
        <P>{t.lg_r5_p}</P>
      </Section>

      <Section title={t.lg_r6_title}>
        <P>{t.lg_r6_p}</P>
      </Section>

      <Section title={t.lg_r7_title}>
        <P>{t.lg_r7_p}</P>
      </Section>

      <Section title={t.lg_r8_title}>
        <Bullet>{t.lg_r8_b1}</Bullet>
        <Bullet>{t.lg_r8_b2}</Bullet>
        <Bullet>{t.lg_r8_b3}</Bullet>
      </Section>

      {/* ═══════════════════════ ASTROLOGY DISCLAIMER ═══════════════════════ */}
      <DocHeading icon="alert-triangle" title={t.lg_h_disclaimer} />

      <Callout tone="warn">{t.lg_callout_disc}</Callout>

      <Section title={t.lg_d1_title}>
        <P>{t.lg_d1_p}</P>
      </Section>

      <Section title={t.lg_d2_title}>
        <P>{t.lg_d2_p}</P>
      </Section>

      <Section title={t.lg_d3_title}>
        <P>{t.lg_d3_intro}</P>
        <Bullet>{t.lg_d3_b1}</Bullet>
        <Bullet>{t.lg_d3_b2}</Bullet>
        <Bullet>{t.lg_d3_b3}</Bullet>
        <Bullet>{t.lg_d3_b4}</Bullet>
        <Bullet>{t.lg_d3_b5}</Bullet>
      </Section>

      <Section title={t.lg_d4_title}>
        <P>{t.lg_d4_p}</P>
      </Section>

      <Section title={t.lg_d5_title}>
        <P>{t.lg_d5_p}</P>
      </Section>

      <Section title={t.lg_d6_title}>
        <P>{t.lg_d6_p}</P>
      </Section>

      <Section title={t.lg_d7_title}>
        <P>{t.lg_d7_p}</P>
      </Section>

      <Section title={t.lg_d8_title}>
        <Callout tone="danger">{t.lg_d8_callout}</Callout>
      </Section>

      <Section title={t.lg_d9_title}>
        <P>{t.lg_d9_p}</P>
      </Section>
    </LegalScreen>
  );
}

const d = StyleSheet.create({
  wrap: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    marginTop: 32,
    marginBottom: 4,
  },
  line: {
    flex: 1,
    height: 1,
  },
  pill: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    paddingVertical: 8,
    paddingHorizontal: 14,
    borderRadius: 999,
    borderWidth: 1,
  },
  title: {
    fontSize: 14,
    fontFamily: F.bold,
    letterSpacing: 0.2,
  },
});
