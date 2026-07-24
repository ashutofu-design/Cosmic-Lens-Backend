import { Feather } from "@expo/vector-icons";
import * as Haptics from "expo-haptics";
import { router, useLocalSearchParams } from "expo-router";
import React, { useMemo } from "react";
import {
  I18nManager,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { NorthIndianChart } from "@/components/NorthIndianChart";
import { FadeInView, staggerDelay } from "@/components/motion/FadeInView";
import { useC } from "@/context/ThemeContext";
import { useUser } from "@/context/UserContext";
import { useT } from "@/hooks/useT";
import { chartVargaMeta, parseChartVargaParam } from "@/lib/divisionalVargaMeta";
import { getD1ChartData } from "@/lib/d1Chart";
import { SIGNS, SIGNS_SHORT } from "@/lib/planetPositionUtils";
import { getVargaPlanetCards } from "@/lib/vargaCompute";

export default function VargaChartScreen() {
  const C = useC();
  const t = useT();
  const insets = useSafeAreaInsets();
  const { kundli } = useUser();
  const params = useLocalSearchParams<{ varga?: string }>();
  const chartKey = parseChartVargaParam(params.varga);
  const meta = chartVargaMeta(chartKey);
  const isD1 = chartKey === "D1";

  const topPad = Platform.OS === "web" ? 67 : insets.top;
  const botPad = Platform.OS === "web" ? 34 : insets.bottom;

  const d1Data = useMemo(() => (isD1 ? getD1ChartData(kundli) : null), [kundli, isD1]);
  const vargaData = useMemo(
    () => (!isD1 ? getVargaPlanetCards(kundli, chartKey) : null),
    [kundli, chartKey, isD1],
  );
  const lagnaFull = useMemo(() => {
    if (isD1) return d1Data?.lagnaFull ?? "—";
    if (!vargaData) return "—";
    const lagnaIdx = SIGNS.findIndex(s => s.startsWith(vargaData.lagnaShort));
    return lagnaIdx >= 0 ? SIGNS[lagnaIdx] : vargaData.lagnaShort;
  }, [isD1, d1Data, vargaData]);

  const lagnaSignIdx = useMemo(() => {
    if (isD1 && d1Data) return d1Data.lagnaSignIdx;
    if (!vargaData) return 0;
    const i = SIGNS_SHORT.findIndex(
      s => vargaData.lagnaShort === s || vargaData.lagnaShort.startsWith(s),
    );
    return i >= 0 ? i : 0;
  }, [isD1, d1Data, vargaData]);

  const chartSubtitle = isD1
    ? d1Data?.lagnaShort ?? ""
    : (vargaData?.lagnaShort ?? "");

  return (
    <View style={[s.root, { backgroundColor: C.bg }]}>
      <View style={[s.header, { paddingTop: topPad + 12, borderBottomColor: C.border }]}>
        <Pressable
          onPress={() => {
            Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
            router.back();
          }}
          style={s.back}
        >
          <Feather
            name={I18nManager.isRTL ? "arrow-right" : "arrow-left"}
            size={20}
            color={C.textMid}
          />
        </Pressable>
        <View style={{ flex: 1 }}>
          <Text style={[s.headerTitle, { color: C.text }]}>{meta.label}</Text>
          <Text style={[s.headerSub, { color: C.textMuted }]}>
            {meta.hint} · Lagna: {lagnaFull}
          </Text>
        </View>
      </View>

      <ScrollView
        contentContainerStyle={[s.content, { paddingBottom: botPad + 32 }]}
        showsVerticalScrollIndicator={false}
      >
        <FadeInView delay={staggerDelay(0)}>
          {!kundli ? (
            <View style={[s.empty, { backgroundColor: C.bgCard, borderColor: C.border }]}>
              <Text style={[s.emptyTitle, { color: C.text }]}>{t.kundliRequired}</Text>
              <Pressable
                onPress={() => router.push("/onboarding")}
                style={[s.emptyBtn, { borderColor: C.border }]}
              >
                <Text style={{ color: C.text, fontFamily: "Nunito_600SemiBold" }}>{t.kundliRequired}</Text>
              </Pressable>
            </View>
          ) : (isD1 ? !d1Data : !vargaData) ? (
            <View style={[s.empty, { backgroundColor: C.bgCard, borderColor: C.border }]}>
              <Text style={{ color: C.textMuted, textAlign: "center", fontFamily: "Nunito_500Medium" }}>
                Chart data unavailable — refresh kundli from profile.
              </Text>
            </View>
          ) : (
            <NorthIndianChart
              variant="full"
              showHeader
              title={meta.label}
              subtitle={`${chartSubtitle} · ${meta.hint}`}
              lagnaSignIndex={lagnaSignIdx}
              ascendantDeg={isD1 ? d1Data?.ascendantDeg : undefined}
              planets={
                isD1
                  ? (d1Data?.planets ?? [])
                  : vargaData!.planets.map(p => ({
                      name: p.name,
                      house: p.house,
                      retrograde: p.retrograde,
                      longitude: p.longitude,
                    }))
              }
            />
          )}
        </FadeInView>
      </ScrollView>
    </View>
  );
}

const s = StyleSheet.create({
  root: { flex: 1 },
  header: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    paddingHorizontal: 16,
    paddingBottom: 12,
    borderBottomWidth: 1,
  },
  back: { padding: 4 },
  headerTitle: { fontSize: 18, fontFamily: "Nunito_700Bold" },
  headerSub: { fontSize: 11, fontFamily: "Nunito_500Medium", marginTop: 2 },
  content: {
    padding: 16,
    paddingBottom: 32,
    width: "100%",
    alignItems: "center",
    alignSelf: "center",
    maxWidth: 520,
  },
  empty: {
    width: "100%",
    padding: 28,
    borderRadius: 16,
    borderWidth: 1,
    alignItems: "center",
    gap: 12,
  },
  emptyTitle: { fontSize: 16, fontFamily: "Nunito_700Bold", textAlign: "center" },
  emptyBtn: { paddingHorizontal: 16, paddingVertical: 10, borderRadius: 12, borderWidth: 1 },
});
