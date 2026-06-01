import { Feather } from "@expo/vector-icons";
import * as Haptics from "expo-haptics";
import { router } from "expo-router";
import React from "react";
import { I18nManager, Platform, Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { CosmicBg } from "@/components/CosmicBg";
import { DivisionalChartsPanel } from "@/components/DivisionalChartsPanel";
import { useC } from "@/context/ThemeContext";
import { useT } from "@/hooks/useT";

/** Deep link / legacy route — same content as Planet Position → Divisional tab. */
export default function DivisionalChartsScreen() {
  const C = useC();
  const t = useT();
  const insets = useSafeAreaInsets();
  const topPad = Platform.OS === "web" ? 67 : insets.top;

  return (
    <CosmicBg>
      <View style={[s.topBar, { paddingTop: topPad + 8 }]}>
        <Pressable
          onPress={() => { Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light); router.back(); }}
          style={[s.backBtn, { backgroundColor: C.bgCard, borderColor: C.border }]}
        >
          <Feather name={I18nManager.isRTL ? "arrow-right" : "arrow-left"} size={20} color={C.text} />
        </Pressable>
        <View style={{ flex: 1 }}>
          <Text style={[s.title, { color: C.text }]}>{t.mdDivisionalTitle}</Text>
          <Text style={[s.sub, { color: C.textMuted }]}>{t.mdDivisionalSub}</Text>
        </View>
      </View>

      <ScrollView
        contentContainerStyle={{ paddingHorizontal: 16, paddingBottom: insets.bottom + 40, gap: 14 }}
        showsVerticalScrollIndicator={false}
      >
        <DivisionalChartsPanel />
      </ScrollView>
    </CosmicBg>
  );
}

const s = StyleSheet.create({
  topBar: { flexDirection: "row", alignItems: "center", gap: 12, paddingHorizontal: 16, paddingBottom: 12 },
  backBtn: { width: 40, height: 40, borderRadius: 20, borderWidth: 1, alignItems: "center", justifyContent: "center" },
  title: { fontSize: 18, fontFamily: "Nunito_700Bold" },
  sub: { fontSize: 11, fontFamily: "Nunito_500Medium", marginTop: 2 },
});
