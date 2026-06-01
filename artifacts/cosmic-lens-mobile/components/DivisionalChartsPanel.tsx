import { Feather } from "@expo/vector-icons";
import * as Haptics from "expo-haptics";
import { router } from "expo-router";
import React, { useMemo, useState } from "react";
import { Pressable, ScrollView, StyleSheet, Text, View } from "react-native";

import { PlanetPositionCard } from "@/components/PlanetPositionCard";
import { useC } from "@/context/ThemeContext";
import { useUser } from "@/context/UserContext";
import { useT } from "@/hooks/useT";
import { SIGNS } from "@/lib/planetPositionUtils";
import { getVargaPlanetCards, type VargaKey } from "@/lib/vargaCompute";

const VARGAS: { key: VargaKey; label: string; hint: string }[] = [
  { key: "D9", label: "D9 Navamsa", hint: "Marriage & dharma" },
  { key: "D10", label: "D10 Dashamsha", hint: "Career & karma" },
  { key: "D7", label: "D7 Saptamsa", hint: "Children & progeny" },
  { key: "D2", label: "D2 Hora", hint: "Wealth" },
  { key: "D3", label: "D3 Drekkana", hint: "Siblings & courage" },
  { key: "D12", label: "D12 Dwadashamsha", hint: "Parents" },
  { key: "D30", label: "D30 Trimsamsa", hint: "Misfortunes" },
];

type Props = {
  showKundliLink?: boolean;
};

export function DivisionalChartsPanel({ showKundliLink = true }: Props) {
  const C = useC();
  const t = useT();
  const { kundli } = useUser();
  const [active, setActive] = useState<VargaKey>("D9");

  const meta = VARGAS.find(v => v.key === active)!;
  const vargaData = useMemo(() => getVargaPlanetCards(kundli, active), [kundli, active]);
  const lagnaIdx = vargaData ? SIGNS.findIndex(s => s.startsWith(vargaData.lagnaShort)) : -1;
  const lagnaFull = lagnaIdx >= 0 ? SIGNS[lagnaIdx] : vargaData?.lagnaShort ?? "—";

  if (!kundli) {
    return (
      <View style={[s.empty, { backgroundColor: C.bgCard, borderColor: C.border }]}>
        <Text style={{ fontSize: 32 }}>📊</Text>
        <Text style={[s.emptyTitle, { color: C.text }]}>{t.kundliRequired}</Text>
        <Text style={[s.emptySub, { color: C.textMuted }]}>{t.kundliRequiredSub}</Text>
        <Pressable
          onPress={() => router.push("/onboarding")}
          style={[s.onboardBtn, { borderColor: C.border, backgroundColor: C.bgCard2 }]}
        >
          <Text style={{ color: C.text, fontSize: 13, fontWeight: "600" }}>{t.kundliRequired}</Text>
        </Pressable>
      </View>
    );
  }

  return (
    <View style={{ gap: 12 }}>
      <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={{ gap: 8, paddingVertical: 4 }}>
        {VARGAS.map(v => {
          const on = v.key === active;
          return (
            <Pressable
              key={v.key}
              onPress={() => { Haptics.selectionAsync(); setActive(v.key); }}
              style={[s.chip, { borderColor: C.border, backgroundColor: on ? "#7c3aed" : C.bgCard }]}
            >
              <Text style={{ color: on ? "#fff" : C.text, fontSize: 12, fontFamily: "Nunito_700Bold" }}>{v.key}</Text>
            </Pressable>
          );
        })}
      </ScrollView>

      <View style={[s.lagnaBar, { backgroundColor: C.bgCard, borderColor: C.border }]}>
        <Text style={[s.lagnaLabel, { color: C.textMuted }]}>{meta.label}</Text>
        <Text style={[s.lagnaHint, { color: "#a78bfa" }]}>{meta.hint}</Text>
        <Text style={[s.lagnaValue, { color: C.text }]}>Lagna: {lagnaFull}</Text>
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
        <Pressable
          onPress={() => router.push("/(tabs)/kundli")}
          style={[s.linkBtn, { borderColor: C.border, backgroundColor: C.bgCard }]}
        >
          <Feather name="layers" size={16} color="#f59e0b" />
          <Text style={{ color: C.text, fontFamily: "Nunito_600SemiBold", flex: 1 }}>{t.tabKundli}</Text>
          <Feather name="chevron-right" size={16} color={C.textMuted} />
        </Pressable>
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
  lagnaBar: { borderRadius: 14, borderWidth: 1, padding: 12, gap: 4 },
  lagnaLabel: { fontSize: 11, fontFamily: "Nunito_700Bold", letterSpacing: 0.8 },
  lagnaHint: { fontSize: 12, fontFamily: "Nunito_600SemiBold" },
  lagnaValue: { fontSize: 13, fontFamily: "Nunito_600SemiBold", marginTop: 2 },
  linkBtn: { flexDirection: "row", alignItems: "center", gap: 10, padding: 14, borderRadius: 14, borderWidth: 1 },
});
