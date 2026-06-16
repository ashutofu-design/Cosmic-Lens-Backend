import { Feather } from "@expo/vector-icons";
import * as Haptics from "expo-haptics";
import { router, useLocalSearchParams } from "expo-router";
import React from "react";
import { Platform, Pressable, ScrollView, StatusBar, StyleSheet, Text, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { KundliMilanBasicResult } from "@/components/kundliMilan/KundliMilanBasicResult";
import { kootsToGunScores } from "@/components/kundliMilan/MilanGunBreakdown";
import { useC } from "@/context/ThemeContext";
import { useT } from "@/hooks/useT";
import type { MarriageBasicsPayload } from "@/lib/milanMarriageBasics";
import { MilanResultStore } from "@/lib/milanResultStore";
import { useFeatureGate } from "@/components/FeatureGate";

/** Standalone route — main Basic flow is inline on /kundli-milan */
export default function KundliMilanResultScreen() {
  const C = useC();
  const { LockOverlay } = useFeatureGate("kundli_milan");
  const t = useT();
  const insets = useSafeAreaInsets();
  const androidSB = StatusBar.currentHeight ?? 24;
  const topPad = Platform.OS === "android" ? Math.max(insets.top, androidSB) : insets.top;
  const botPad = insets.bottom;
  const isDark = C.isDark;

  const params = useLocalSearchParams<{ p1Name?: string; p2Name?: string }>();
  const backendData = MilanResultStore.get();
  const marriageBasics = backendData?.marriage_basics as MarriageBasicsPayload | undefined;
  const gunScores = kootsToGunScores(backendData?.koots);
  const gunTotal = typeof backendData?.total === "number" ? backendData.total : null;

  if (!marriageBasics?.couple) {
    return (
      <View style={{ flex: 1, backgroundColor: C.bg, justifyContent: "center", alignItems: "center", padding: 32 }}>
        <Text style={{ fontSize: 40, marginBottom: 16 }}>⚠️</Text>
        <Text style={{ color: C.text, fontSize: 18, fontFamily: "Nunito_700Bold", textAlign: "center", marginBottom: 8 }}>
          Result Not Found
        </Text>
        <Text style={{ color: C.textMuted, fontSize: 14, fontFamily: "Nunito_400Regular", textAlign: "center", marginBottom: 32 }}>
          {t.noResultFound}
        </Text>
        <Pressable
          onPress={() => router.replace("/kundli-milan" as never)}
          style={{ backgroundColor: C.isDark ? "#f59e0b" : "#7C3AED", paddingHorizontal: 32, paddingVertical: 14, borderRadius: 14 }}
        >
          <Text style={{ color: "#fff", fontFamily: "Nunito_700Bold", fontSize: 16 }}>{t.goBack}</Text>
        </Pressable>
      </View>
    );
  }

  return (
    <View style={[st.root, { backgroundColor: C.bg }]}>
      <View style={[st.topBar, { paddingTop: topPad + 8 }]}>
        <Pressable
          onPress={() => {
            Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
            router.back();
          }}
        >
          <View
            style={[
              st.backCircle,
              {
                backgroundColor: isDark ? "rgba(255,255,255,0.08)" : "rgba(0,0,0,0.05)",
                borderColor: isDark ? "rgba(255,255,255,0.14)" : "rgba(0,0,0,0.08)",
              },
            ]}
          >
            <Feather name="arrow-left" size={20} color={isDark ? "#fff" : "#0F172A"} />
          </View>
        </Pressable>
        <Text style={[st.headerTitle, { color: isDark ? "#f3e8ff" : "#0F172A" }]}>{t.milanResult}</Text>
        <View style={{ width: 42 }} />
      </View>

      <ScrollView
        contentContainerStyle={[st.scroll, { paddingTop: topPad + 64, paddingBottom: botPad + 32 }]}
        showsVerticalScrollIndicator={false}
      >
        <KundliMilanBasicResult
          data={marriageBasics}
          isDark={isDark}
          gunScores={gunScores}
          gunTotal={gunTotal}
          lang={t.lang}
          onOpenPro={() => {
            MilanResultStore.requestProOnReturn();
            router.replace("/kundli-milan?openPro=1" as never);
          }}
        />
      </ScrollView>
      {LockOverlay}
    </View>
  );
}

const st = StyleSheet.create({
  root: { flex: 1 },
  topBar: {
    position: "absolute",
    top: 0,
    left: 0,
    right: 0,
    zIndex: 20,
    paddingHorizontal: 16,
    paddingBottom: 10,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
  },
  backCircle: {
    width: 42,
    height: 42,
    borderRadius: 21,
    alignItems: "center",
    justifyContent: "center",
    borderWidth: 1,
  },
  headerTitle: { fontSize: 18, fontFamily: "Nunito_700Bold" },
  scroll: { paddingHorizontal: 18 },
});
