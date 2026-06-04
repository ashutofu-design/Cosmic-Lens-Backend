import { Feather } from "@expo/vector-icons";
import * as Haptics from "expo-haptics";
import { router } from "expo-router";
import React, { useMemo, useState } from "react";
import { ScrollView, StyleSheet, Text, View } from "react-native";

import { PlanetPositionCard } from "@/components/PlanetPositionCard";
import { ScalePressable } from "@/components/motion/ScalePressable";
import { useC } from "@/context/ThemeContext";
import { useUser } from "@/context/UserContext";
import { useT } from "@/hooks/useT";
import { DIVISIONAL_VARGAS } from "@/lib/divisionalVargaMeta";
import { SIGNS_EN, SIGNS_SHORT, signEnFromShort } from "@/lib/planetPositionUtils";
import { getVargaPlanetCards, type VargaKey } from "@/lib/vargaCompute";

type Props = {
  showKundliLink?: boolean;
};

export function DivisionalChartsPanel({ showKundliLink = true }: Props) {
  const C = useC();
  const t = useT();
  const { kundli } = useUser();
  const [active, setActive] = useState<VargaKey>("D9");

  const meta = DIVISIONAL_VARGAS.find(v => v.key === active)!;
  const vargaData = useMemo(() => getVargaPlanetCards(kundli, active), [kundli, active]);
  const lagnaIdx = vargaData ? SIGNS_SHORT.indexOf(vargaData.lagnaShort) : -1;
  const lagnaFull = lagnaIdx >= 0 ? SIGNS_EN[lagnaIdx] : signEnFromShort(vargaData?.lagnaShort ?? "—");

  if (!kundli) {
    return (
      <View style={[s.empty, { backgroundColor: C.bgCard, borderColor: C.border }]}>
        <Text style={{ fontSize: 32 }}>📊</Text>
        <Text style={[s.emptyTitle, { color: C.text }]}>{t.kundliRequired}</Text>
        <Text style={[s.emptySub, { color: C.textMuted }]}>{t.kundliRequiredSub}</Text>
        <ScalePressable
          onPress={() => router.push("/onboarding")}
          haptic="medium"
          style={[s.onboardBtn, { borderColor: C.border, backgroundColor: C.bgCard2 }]}
        >
          <Text style={{ color: C.text, fontSize: 13, fontWeight: "600" }}>{t.kundliRequired}</Text>
        </ScalePressable>
      </View>
    );
  }

  return (
    <View style={{ gap: 12 }}>
      <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={{ gap: 8, paddingVertical: 4 }}>
        {DIVISIONAL_VARGAS.map(v => {
          const on = v.key === active;
          return (
            <ScalePressable
              key={v.key}
              onPress={() => { Haptics.selectionAsync(); setActive(v.key); }}
              haptic="none"
              style={[s.chip, { borderColor: C.border, backgroundColor: on ? "#7c3aed" : C.bgCard }]}
            >
              <Text style={{ color: on ? "#fff" : C.text, fontSize: 12, fontFamily: "Nunito_700Bold" }}>{v.key}</Text>
            </ScalePressable>
          );
        })}
      </ScrollView>

      <View style={[s.lagnaBar, { backgroundColor: C.bgCard, borderColor: C.border }]}>
        <View style={s.lagnaHeaderRow}>
          <View style={{ flex: 1, gap: 4 }}>
            <Text style={[s.lagnaLabel, { color: C.textMuted }]}>{meta.label}</Text>
            <Text style={[s.lagnaHint, { color: "#a78bfa" }]}>{meta.hint}</Text>
            <Text style={[s.lagnaValue, { color: C.text }]}>Lagna: {lagnaFull}</Text>
          </View>
          {vargaData && (
            <ScalePressable
              onPress={() => router.push({ pathname: "/varga-chart", params: { varga: active } })}
              haptic="medium"
              style={[s.viewChartBtn, { borderColor: "#7c3aed", backgroundColor: "rgba(124,58,237,0.12)" }]}
            >
              <Feather name="grid" size={14} color="#a78bfa" />
              <Text style={[s.viewChartTxt, { color: "#c4b5fd" }]}>{t.viewChart}</Text>
              <Feather name="chevron-right" size={14} color="#a78bfa" />
            </ScalePressable>
          )}
        </View>
      </View>

      {vargaData ? (
        vargaData.planets.map(p => (
          <PlanetPositionCard
            key={`${active}-${p.name}`}
            planet={p}
            mode="varga"
            vargaLabel={meta.label}
          />
        ))
      ) : (
        <View style={[s.empty, { backgroundColor: C.bgCard, borderColor: C.border }]}>
          <Text style={{ color: C.textMuted, fontSize: 13, fontFamily: "Nunito_500Medium", textAlign: "center" }}>
            Chart data unavailable — refresh kundli from profile.
          </Text>
        </View>
      )}

      {showKundliLink && (
        <ScalePressable
          onPress={() => router.push("/(tabs)/kundli")}
          haptic="light"
          style={[s.linkBtn, { borderColor: C.border, backgroundColor: C.bgCard }]}
        >
          <Feather name="layers" size={16} color="#f59e0b" />
          <Text style={{ color: C.text, fontFamily: "Nunito_600SemiBold", flex: 1 }}>{t.tabKundli}</Text>
          <Feather name="chevron-right" size={16} color={C.textMuted} />
        </ScalePressable>
      )}
    </View>
  );
}

const s = StyleSheet.create({
  empty: { padding: 28, borderRadius: 18, borderWidth: 1, alignItems: "center", gap: 8 },
  emptyTitle: { fontSize: 16, fontFamily: "Nunito_700Bold", textAlign: "center" },
  emptySub: { fontSize: 12, fontFamily: "Nunito_500Medium", textAlign: "center", lineHeight: 18 },
  onboardBtn: { marginTop: 8, paddingHorizontal: 16, paddingVertical: 10, borderRadius: 12, borderWidth: 1 },
  chip: { paddingHorizontal: 14, paddingVertical: 10, borderRadius: 12, borderWidth: 1 },
  lagnaBar: { borderRadius: 14, borderWidth: 1, padding: 12 },
  lagnaHeaderRow: { flexDirection: "row", alignItems: "flex-start", gap: 10 },
  lagnaLabel: { fontSize: 11, fontFamily: "Nunito_700Bold", letterSpacing: 0.8 },
  lagnaHint: { fontSize: 12, fontFamily: "Nunito_600SemiBold" },
  lagnaValue: { fontSize: 13, fontFamily: "Nunito_600SemiBold", marginTop: 2 },
  viewChartBtn: {
    flexDirection: "row",
    alignItems: "center",
    gap: 5,
    paddingVertical: 8,
    paddingHorizontal: 10,
    borderRadius: 10,
    borderWidth: 1,
    marginTop: 2,
  },
  viewChartTxt: { fontSize: 11, fontFamily: "Nunito_700Bold" },
  linkBtn: { flexDirection: "row", alignItems: "center", gap: 10, padding: 14, borderRadius: 14, borderWidth: 1 },
});
