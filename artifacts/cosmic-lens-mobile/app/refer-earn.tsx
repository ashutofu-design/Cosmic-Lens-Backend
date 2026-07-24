import { Feather } from "@expo/vector-icons";
import * as Clipboard from "expo-clipboard";
import * as Haptics from "expo-haptics";
import { LinearGradient } from "expo-linear-gradient";
import { router } from "expo-router";
import React, { useEffect, useState } from "react";
import {
  ActivityIndicator,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { CosmicBg } from "@/components/CosmicBg";
import { FadeInView } from "@/components/motion/FadeInView";
import { useC } from "@/context/ThemeContext";
import { useUser } from "@/context/UserContext";
import {
  fetchPackReferralMine,
  type PackReferralMine,
} from "@/lib/packReferral";

const F = {
  medium: "Nunito_500Medium",
  semibold: "Nunito_600SemiBold",
  bold: "Nunito_700Bold",
};

export default function ReferEarnScreen() {
  const insets = useSafeAreaInsets();
  const C = useC();
  const { user } = useUser();
  const [info, setInfo] = useState<PackReferralMine | null>(null);
  const [loading, setLoading] = useState(true);
  const [copied, setCopied] = useState(false);
  const topPad = Platform.OS === "web" ? 67 : insets.top;
  const botPad = Platform.OS === "web" ? 34 : insets.bottom;
  const accent = C.isDark ? "#f472b6" : "#db2777";

  const displayCode =
    info?.referral_code || (user?.id != null ? `CL${user.id}` : "");

  const steps = [
    "Share your referral code with a friend",
    "They enter it once during signup (name & birth details)",
    "When they buy any V1 or V3 pack, you get 3 free Ask questions",
  ];

  useEffect(() => {
    if (!user?.id) {
      setLoading(false);
      return;
    }
    let cancelled = false;
    fetchPackReferralMine(user)
      .then((d) => {
        if (!cancelled) setInfo(d);
      })
      .catch(() => {
        if (!cancelled) setInfo(null);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [user?.id, user?.api_key]);

  async function copyCode() {
    if (!displayCode) return;
    try {
      await Clipboard.setStringAsync(displayCode);
      setCopied(true);
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success).catch(() => {});
      setTimeout(() => setCopied(false), 1600);
    } catch {
      /* ignore */
    }
  }

  return (
    <CosmicBg>
      <View
        style={{
          paddingTop: topPad + 8,
          paddingHorizontal: 16,
          paddingBottom: 12,
          flexDirection: "row",
          alignItems: "center",
          gap: 12,
        }}
      >
        <Pressable
          onPress={() => {
            Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
            router.back();
          }}
          style={[s.back, { backgroundColor: C.bgCard, borderColor: C.border }]}
        >
          <Feather name="arrow-left" size={18} color={C.text} />
        </Pressable>
        <View style={{ flex: 1 }}>
          <Text style={[s.title, { color: C.text }]}>Refer and Earn</Text>
          <Text style={{ color: C.textMuted, fontSize: 11, fontFamily: F.medium }}>
            Share · friend buys a pack · you get 3 free questions
          </Text>
        </View>
      </View>

      <ScrollView
        contentContainerStyle={{
          paddingHorizontal: 16,
          paddingBottom: botPad + 40,
          gap: 14,
        }}
        showsVerticalScrollIndicator={false}
      >
        <FadeInView delay={40}>
          <LinearGradient
            colors={C.isDark ? ["#4c0519", "#831843", "#9d174d"] : ["#fdf2f8", "#fce7f3", "#fbcfe8"]}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 1 }}
            style={[
              s.hero,
              {
                borderColor: C.isDark ? "rgba(244,114,182,0.35)" : "rgba(219,39,119,0.25)",
              },
            ]}
          >
            <View
              style={[
                s.heroIcon,
                {
                  backgroundColor: C.isDark ? "rgba(255,255,255,0.12)" : "rgba(219,39,119,0.12)",
                },
              ]}
            >
              <Feather name="gift" size={28} color={accent} />
            </View>
            <Text style={[s.heroTitle, { color: C.isDark ? "#fff" : "#831843" }]}>
              Refer & get 3 free questions
            </Text>
            <Text style={[s.heroSub, { color: C.isDark ? "rgba(255,255,255,0.82)" : "#9d174d" }]}>
              When your friend signs up with your code and later buys any V1 or V3 pack, you get 3
              free Ask questions. That's it.
            </Text>
          </LinearGradient>
        </FadeInView>

        <FadeInView delay={80}>
          <View style={[s.card, { backgroundColor: C.bgCard, borderColor: C.border }]}>
            <Text style={[s.cardLabel, { color: C.textMuted }]}>Your code</Text>
            {loading ? (
              <ActivityIndicator color={accent} style={{ marginVertical: 20 }} />
            ) : !user ? (
              <Text style={{ color: C.textMuted, fontFamily: F.medium, fontSize: 13, marginTop: 8 }}>
                Please sign in to view your referral code.
              </Text>
            ) : displayCode ? (
              <>
                <View style={[s.codeBox, { backgroundColor: C.bgCard2, borderColor: C.border }]}>
                  <Text style={[s.codeText, { color: C.text }]} selectable>
                    {displayCode}
                  </Text>
                  <Pressable
                    onPress={() => void copyCode()}
                    style={[s.copyBtn, { backgroundColor: `${accent}22`, borderColor: `${accent}55` }]}
                  >
                    <Feather name={copied ? "check" : "copy"} size={14} color={accent} />
                    <Text style={{ color: accent, fontSize: 12, fontFamily: F.bold }}>
                      {copied ? "Copied" : "Copy"}
                    </Text>
                  </Pressable>
                </View>
                <Text style={{ color: C.textMid, fontSize: 12, fontFamily: F.medium, marginTop: 10 }}>
                  Earned: {info?.questions_earned ?? 0} Q · Friends: {info?.friends_converted ?? 0}
                  {(info?.bonus_questions_left ?? 0) > 0
                    ? ` · Bonus left: ${info?.bonus_questions_left}`
                    : ""}
                </Text>
              </>
            ) : (
              <Text style={{ color: C.textMuted, fontFamily: F.medium, fontSize: 13, marginTop: 8 }}>
                Could not load your code. Please try again later.
              </Text>
            )}
          </View>
        </FadeInView>

        <FadeInView delay={120}>
          <View style={[s.card, { backgroundColor: C.bgCard, borderColor: C.border, gap: 10 }]}>
            <Text style={[s.cardLabel, { color: C.textMuted }]}>How it works</Text>
            {steps.map((line, i) => (
              <View key={line} style={{ flexDirection: "row", gap: 10, alignItems: "flex-start" }}>
                <View
                  style={{
                    width: 22,
                    height: 22,
                    borderRadius: 8,
                    backgroundColor: `${accent}18`,
                    alignItems: "center",
                    justifyContent: "center",
                  }}
                >
                  <Text style={{ color: accent, fontSize: 11, fontFamily: F.bold }}>{i + 1}</Text>
                </View>
                <Text
                  style={{
                    flex: 1,
                    color: C.text,
                    fontSize: 13,
                    fontFamily: F.medium,
                    lineHeight: 18,
                  }}
                >
                  {line}
                </Text>
              </View>
            ))}
          </View>
        </FadeInView>

        <FadeInView delay={160}>
          <Pressable
            onPress={() => router.push("/cosmic-packs" as any)}
            style={[s.linkRow, { borderColor: C.border, backgroundColor: C.bgCard }]}
          >
            <Feather name="package" size={16} color="#fbbf24" />
            <Text style={{ flex: 1, color: C.text, fontFamily: F.semibold, fontSize: 13 }}>
              Open Cosmic Packs
            </Text>
            <Feather name="chevron-right" size={16} color={C.textDim} />
          </Pressable>
        </FadeInView>
      </ScrollView>
    </CosmicBg>
  );
}

const s = StyleSheet.create({
  back: {
    width: 36,
    height: 36,
    borderRadius: 11,
    borderWidth: 1,
    alignItems: "center",
    justifyContent: "center",
  },
  title: { fontSize: 18, fontFamily: F.bold },
  hero: {
    borderRadius: 18,
    borderWidth: 1,
    padding: 20,
    alignItems: "center",
    gap: 8,
  },
  heroIcon: {
    width: 56,
    height: 56,
    borderRadius: 16,
    alignItems: "center",
    justifyContent: "center",
    marginBottom: 4,
  },
  heroTitle: { fontSize: 18, fontFamily: F.bold, textAlign: "center" },
  heroSub: { fontSize: 13, fontFamily: F.medium, textAlign: "center", lineHeight: 19 },
  card: {
    borderRadius: 16,
    borderWidth: 1,
    padding: 16,
  },
  cardLabel: {
    fontSize: 10,
    fontFamily: F.bold,
    letterSpacing: 1.2,
    textTransform: "uppercase",
  },
  codeBox: {
    marginTop: 12,
    borderRadius: 12,
    borderWidth: 1,
    paddingHorizontal: 14,
    paddingVertical: 12,
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
  },
  codeText: { flex: 1, fontSize: 18, fontFamily: F.bold, letterSpacing: 1 },
  copyBtn: {
    flexDirection: "row",
    alignItems: "center",
    gap: 5,
    paddingHorizontal: 10,
    paddingVertical: 7,
    borderRadius: 9,
    borderWidth: 1,
  },
  linkRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    borderRadius: 14,
    borderWidth: 1,
    padding: 14,
  },
});
