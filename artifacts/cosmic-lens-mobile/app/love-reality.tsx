import { Feather } from "@expo/vector-icons";
import * as Haptics from "expo-haptics";
import { LinearGradient } from "expo-linear-gradient";
import { router, useLocalSearchParams } from "expo-router";
import React, { useEffect } from "react";
import {
  Platform,
  Pressable,
  StatusBar,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { CosmicBg } from "@/components/CosmicBg";
import { LoveRealityUnifiedBasic } from "@/components/loveReality/LoveRealityUnifiedBasic";
import { FadeInView, staggerDelay } from "@/components/motion/FadeInView";
import { useC } from "@/context/ThemeContext";
import { useUser } from "@/context/UserContext";
import { useT } from "@/hooks/useT";
import { loveRealityProRouteParams } from "@/lib/loveRealityProOffer";

export default function LoveRealityScreen() {
  const C = useC();
  const t = useT();
  const { profiles, primaryProfileId } = useUser();
  const params = useLocalSearchParams<{ partnerId?: string; openPro?: string; tool?: string }>();
  const partnerId = typeof params.partnerId === "string" ? params.partnerId : null;
  const initialToolKey = typeof params.tool === "string" ? params.tool : undefined;
  const insets = useSafeAreaInsets();
  const androidSB = StatusBar.currentHeight ?? 24;
  const topPad = Platform.OS === "android" ? Math.max(insets.top, androidSB) : insets.top;
  const botPad = insets.bottom;
  const isDark = C.isDark;

  const primaryProfile = profiles.find(p => p.id === primaryProfileId) ?? profiles[0] ?? null;
  const partnerProfile = partnerId ? (profiles.find(p => p.id === partnerId) ?? null) : null;

  useEffect(() => {
    if (params.openPro === "1") {
      router.replace(loveRealityProRouteParams(partnerId) as never);
    }
  }, [params.openPro, partnerId]);

  function openProScreen() {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    router.push(loveRealityProRouteParams(partnerId) as never);
  }

  return (
    <CosmicBg>
      <View style={[s.shell, { paddingTop: topPad + 6 }]}>
        <FadeInView delay={staggerDelay(0)}>
          <View style={s.headerRow}>
            <Pressable
              onPress={() => { Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light); router.back(); }}
              hitSlop={8}
            >
              <View style={[s.backCircle, {
                backgroundColor: isDark ? "rgba(255,255,255,0.08)" : "rgba(0,0,0,0.05)",
                borderColor: isDark ? "rgba(255,255,255,0.12)" : "rgba(0,0,0,0.08)",
              }]}>
                <Feather name="chevron-left" size={22} color={isDark ? "#fff" : "#0F172A"} />
              </View>
            </Pressable>
            <View style={{ flex: 1, alignItems: "center", paddingHorizontal: 4 }}>
              <Text style={[s.headerTitle, { color: isDark ? "#fff" : "#0F172A" }]} numberOfLines={1}>
                {t.rl_loveTitle}
              </Text>
              <Text style={[s.headerSub, { color: isDark ? "rgba(203,213,225,0.5)" : "#64748B" }]} numberOfLines={2}>
                {t.rl_loveSub}
              </Text>
            </View>
            <View style={{ width: 40 }} />
          </View>
        </FadeInView>

        <FadeInView delay={staggerDelay(1)}>
          <View style={s.segRow}>
            <View style={[s.segWrap, { backgroundColor: isDark ? "rgba(255,255,255,0.07)" : "rgba(0,0,0,0.05)" }]}>
              <Pressable
                style={[s.segBtn, { backgroundColor: isDark ? "#1e2744" : "#ec4899" }]}
              >
                <Text style={[s.segTxt, { color: "#fff" }]}>{t.km_basic}</Text>
              </Pressable>
              <Pressable onPress={openProScreen} style={[s.segBtn, { overflow: "hidden" }]}>
                <LinearGradient
                  colors={["#5b21b6", "#9d174d"]}
                  start={{ x: 0, y: 0 }}
                  end={{ x: 1, y: 0 }}
                  style={[StyleSheet.absoluteFillObject, { borderRadius: 14 }]}
                />
                <Text style={[s.segTxt, { color: "#fff" }]}>✨ Pro</Text>
              </Pressable>
            </View>
          </View>
        </FadeInView>

        {partnerProfile && (
          <FadeInView delay={staggerDelay(2)}>
            <View style={[s.partnerPill, {
              borderColor: isDark ? "rgba(236,72,153,0.35)" : "rgba(236,72,153,0.25)",
            }]}>
              <LinearGradient
                colors={isDark ? ["rgba(236,72,153,0.14)", "rgba(168,85,247,0.08)"] : ["rgba(236,72,153,0.08)", "rgba(168,85,247,0.05)"]}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 0 }}
                style={StyleSheet.absoluteFill}
              />
              <Feather name="heart" size={12} color="#f472b6" />
              <Text style={[s.partnerPillTxt, { color: isDark ? "#fbcfe8" : "#9d174d" }]} numberOfLines={1}>
                Checking with {partnerProfile.name}
              </Text>
              <Pressable onPress={() => router.push("/relationship" as never)} hitSlop={8}>
                <Feather name="edit-2" size={12} color={isDark ? "#f472b6" : "#db2777"} />
              </Pressable>
            </View>
          </FadeInView>
        )}

        <FadeInView delay={staggerDelay(partnerProfile ? 3 : 2)} style={{ flex: 1 }}>
          <LoveRealityUnifiedBasic
            isDark={isDark}
            bottomPad={botPad}
            primaryProfile={primaryProfile?.birthData ? { name: primaryProfile.name, birthData: primaryProfile.birthData } : null}
            partnerProfile={partnerProfile?.birthData ? { name: partnerProfile.name, birthData: partnerProfile.birthData } : null}
            initialToolKey={initialToolKey}
            onOpenPro={openProScreen}
          />
        </FadeInView>
      </View>
    </CosmicBg>
  );
}

const s = StyleSheet.create({
  shell: { flex: 1 },
  headerRow: {
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: 16,
    paddingBottom: 6,
    gap: 8,
  },
  headerTitle: { fontSize: 17, fontFamily: "Nunito_700Bold", letterSpacing: -0.3, textAlign: "center" },
  headerSub: { fontSize: 11, fontFamily: "Nunito_400Regular", textAlign: "center", marginTop: 2, lineHeight: 15 },
  backCircle: { width: 40, height: 40, borderRadius: 20, alignItems: "center", justifyContent: "center", borderWidth: 1 },
  segRow: { alignItems: "center", marginBottom: 10, paddingHorizontal: 16 },
  segWrap: { flexDirection: "row", borderRadius: 18, padding: 3, gap: 3, width: 220 },
  segBtn: { flex: 1, height: 36, borderRadius: 14, alignItems: "center", justifyContent: "center" },
  segTxt: { fontSize: 12, fontFamily: "Nunito_800ExtraBold" },
  partnerPill: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    borderWidth: 1,
    borderRadius: 12,
    paddingHorizontal: 12,
    paddingVertical: 8,
    marginHorizontal: 16,
    marginBottom: 8,
    overflow: "hidden",
  },
  partnerPillTxt: { flex: 1, fontSize: 12, fontFamily: "Nunito_600SemiBold" },
});
