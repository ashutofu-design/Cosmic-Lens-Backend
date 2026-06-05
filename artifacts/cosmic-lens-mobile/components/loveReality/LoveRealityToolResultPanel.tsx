import { Feather } from "@expo/vector-icons";
import * as Haptics from "expo-haptics";
import React from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";

import { LoveRealityResultHero } from "@/components/loveReality/LoveRealityBasicScreen";
import type { LoveRealityBasicDisplay } from "@/lib/loveRealityToolMappers";

export function LoveRealityToolResultPanel({
  toolTitle,
  display,
  isDark,
  bottomPad,
  accentGradient,
  showHeader = false,
  onBack,
}: {
  toolTitle: string;
  userName: string;
  partnerName: string;
  display: LoveRealityBasicDisplay;
  isDark: boolean;
  bottomPad: number;
  accentGradient: [string, string];
  onOpenPro?: () => void;
  showHeader?: boolean;
  onBack?: () => void;
}) {
  const textHi = isDark ? "#fff" : "#0F172A";

  return (
    <View style={p.root}>
      {showHeader && (
        <View style={p.header}>
          <Pressable
            onPress={() => {
              Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
              onBack?.();
            }}
            hitSlop={8}
          >
            <View
              style={[
                p.backCircle,
                {
                  borderColor: isDark ? "rgba(255,255,255,0.12)" : "rgba(0,0,0,0.08)",
                  backgroundColor: isDark ? "rgba(255,255,255,0.06)" : "rgba(0,0,0,0.04)",
                },
              ]}
            >
              <Feather name="chevron-left" size={22} color={textHi} />
            </View>
          </Pressable>
          <Text style={[p.headerTitle, { color: textHi }]} numberOfLines={1}>
            {toolTitle}
          </Text>
          <View style={{ width: 40 }} />
        </View>
      )}

      <View style={[p.body, { paddingBottom: bottomPad + 12 }]}>
        <LoveRealityResultHero display={display} isDark={isDark} accentGradient={accentGradient} compact />
      </View>
    </View>
  );
}

const p = StyleSheet.create({
  root: { flex: 1, minHeight: 0 },
  header: {
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: 16,
    paddingBottom: 6,
    gap: 10,
  },
  backCircle: {
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: "center",
    justifyContent: "center",
    borderWidth: 1,
  },
  headerTitle: { flex: 1, fontSize: 17, fontFamily: "Nunito_700Bold", textAlign: "center" },
  body: {
    flex: 1,
    minHeight: 0,
    paddingHorizontal: 16,
    alignItems: "center",
    justifyContent: "center",
  },
});
