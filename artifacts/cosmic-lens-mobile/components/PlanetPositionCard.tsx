import { Feather } from "@expo/vector-icons";
import * as Haptics from "expo-haptics";
import React, { useEffect, useState } from "react";
import { LayoutAnimation, Platform, StyleSheet, Text, UIManager, View } from "react-native";
import Animated, {
  interpolate,
  useAnimatedStyle,
  useSharedValue,
  withSpring,
} from "react-native-reanimated";

import { ScalePressable } from "@/components/motion/ScalePressable";
import { useC } from "@/context/ThemeContext";
import {
  angDist,
  degreeInSign,
  houseCategory,
  KARAKA,
  nakshatra,
  PLANET_CLR,
  PLANET_GLYPH,
  signEnFromShort,
  signStatusEn,
  signStatusFromSignEn,
  SIGNS_SHORT,
  type PlanetCardData,
} from "@/lib/planetPositionUtils";

if (Platform.OS === "android" && UIManager.setLayoutAnimationEnabledExperimental) {
  UIManager.setLayoutAnimationEnabledExperimental(true);
}

type Props = {
  planet: PlanetCardData;
  sunLon?: number;
  mode?: "d1" | "varga";
  vargaLabel?: string;
};

function DetailRow({ label, value, clrValue }: { label: string; value: string; clrValue?: string }) {
  const C = useC();
  return (
    <View style={[s.row, { borderBottomColor: C.border }]}>
      <Text style={[s.rowLabel, { color: C.textMuted }]}>{label}</Text>
      <Text style={[s.rowValue, { color: C.textMid }, clrValue ? { color: clrValue } : {}]}>{value}</Text>
    </View>
  );
}

export function PlanetPositionCard({ planet, sunLon = 0, mode = "d1", vargaLabel }: Props) {
  const C = useC();
  const [open, setOpen] = useState(false);
  const expand = useSharedValue(0);
  const clr = PLANET_CLR[planet.name] ?? "#f59e0b";
  const signShort = planet.sign || SIGNS_SHORT[Math.floor(planet.longitude / 30) % 12];
  const signEn = signEnFromShort(signShort);
  const status = mode === "varga"
    ? signStatusFromSignEn(planet.name, signShort)
    : signStatusEn(planet.name, planet.longitude);
  const houseCat = houseCategory(planet.house);
  const karaka = KARAKA[planet.name] ?? [];
  const nak = mode === "d1" ? nakshatra(planet.longitude) : null;

  let combustLabel = "";
  if (mode === "d1" && planet.name !== "Sun" && planet.name !== "Rahu" && planet.name !== "Ketu") {
    const dist = angDist(sunLon, planet.longitude);
    const thresholds: Record<string, number> = {
      Moon: 12, Mars: 17, Mercury: 14, Jupiter: 11, Venus: 10, Saturn: 15,
    };
    const thr = thresholds[planet.name] ?? 12;
    if (dist <= thr) combustLabel = `Combust (${dist.toFixed(1)}° from Sun)`;
  }

  const degFmt = degreeInSign(planet.longitude);

  useEffect(() => {
    expand.value = withSpring(open ? 1 : 0, { damping: 16, stiffness: 240 });
  }, [open, expand]);

  const chevronStyle = useAnimatedStyle(() => ({
    transform: [{ rotate: `${interpolate(expand.value, [0, 1], [0, 180])}deg` }],
  }));

  function toggleOpen() {
    LayoutAnimation.configureNext(LayoutAnimation.create(280, "easeInEaseOut", "opacity"));
    Haptics.selectionAsync();
    setOpen((v) => !v);
  }

  return (
    <ScalePressable
      onPress={toggleOpen}
      haptic="none"
      style={[s.card, { backgroundColor: C.bgCard, borderColor: open ? `${clr}55` : C.border }]}
    >
      <View style={s.cardHeader}>
        <View style={[s.glyph, { backgroundColor: `${clr}15`, borderColor: `${clr}30` }]}>
          <Text style={[s.glyphText, { color: clr }]}>{PLANET_GLYPH[planet.name] ?? "★"}</Text>
        </View>
        <View style={s.cardInfo}>
          <View style={s.nameRow}>
            <Text style={[s.planetName, { color: clr }]}>{planet.name}</Text>
            {planet.retrograde && <Text style={s.retroBadge}>℞</Text>}
            {combustLabel !== "" && <Text style={s.combustBadge}>Combust</Text>}
          </View>
          <Text style={[s.cardSub, { color: C.textMuted }]}>
            {signEn} · {degFmt} · H{planet.house}
          </Text>
        </View>
        <View style={s.cardRight}>
          <View style={[s.statusBadge, { borderColor: `${status.color}44` }]}>
            <Text style={[s.statusText, { color: status.color }]}>{status.label}</Text>
          </View>
          <Animated.View style={chevronStyle}>
            <Feather name="chevron-down" size={14} color={C.textMuted} />
          </Animated.View>
        </View>
      </View>

      {open && (
        <View style={s.details}>
          <View style={[s.divider, { backgroundColor: C.border }]} />

          <DetailRow label="Sign" value={signEn} />
          {mode === "varga" && vargaLabel ? (
            <DetailRow label="Varga" value={vargaLabel} clrValue="#a78bfa" />
          ) : null}
          {nak ? (
            <>
              <DetailRow label="Nakshatra" value={`${nak.name} Pada ${nak.pada}`} />
              <DetailRow label="Nakshatra Lord" value={nak.lord} />
            </>
          ) : null}
          <DetailRow label="Longitude" value={`${planet.longitude.toFixed(2)}°`} />
          {mode === "d1" ? (
            <DetailRow
              label="Speed"
              value={planet.speed != null ? `${planet.speed.toFixed(2)}°/day` : "—"}
            />
          ) : null}
          <DetailRow
            label="Motion"
            value={planet.retrograde ? "Retrograde" : "Direct"}
            clrValue={planet.retrograde ? "#fbbf24" : "#4ade80"}
          />
          <DetailRow label="House Type" value={houseCat.label} clrValue={houseCat.color} />
          <DetailRow label="Dignity" value={status.label} clrValue={status.color} />
          {combustLabel !== "" && <DetailRow label="Combust" value={combustLabel} clrValue="#ef4444" />}

          {karaka.length > 0 && (
            <View style={s.karakaRow}>
              <Text style={[s.karakaLabel, { color: C.textMuted }]}>Significations:</Text>
              <Text style={[s.karakaValue, { color: C.textMid }]}>{karaka.join(", ")}</Text>
            </View>
          )}
        </View>
      )}
    </ScalePressable>
  );
}

const s = StyleSheet.create({
  card: {
    borderRadius: 18,
    borderWidth: 1.5,
    padding: 14,
  },
  cardHeader: { flexDirection: "row", alignItems: "center", gap: 12 },
  glyph: {
    width: 40, height: 40, borderRadius: 20,
    borderWidth: 1, alignItems: "center", justifyContent: "center",
  },
  glyphText: { fontSize: 18 },
  cardInfo: { flex: 1 },
  nameRow: { flexDirection: "row", alignItems: "center", gap: 6 },
  planetName: { fontSize: 15, fontWeight: "700" },
  retroBadge: { color: "#fbbf24", fontSize: 12, fontWeight: "700" },
  combustBadge: { fontSize: 10 },
  cardSub: { fontSize: 11, marginTop: 2 },
  cardRight: { alignItems: "flex-end", gap: 6 },
  statusBadge: {
    borderWidth: 1, borderRadius: 8, paddingHorizontal: 7, paddingVertical: 2,
  },
  statusText: { fontSize: 10, fontWeight: "600" },
  details: { gap: 0 },
  divider: { height: 1, marginVertical: 10 },
  row: {
    flexDirection: "row", justifyContent: "space-between", alignItems: "flex-start",
    paddingVertical: 5, borderBottomWidth: 1,
  },
  rowLabel: { fontSize: 11, flex: 1 },
  rowValue: { fontSize: 11, textAlign: "right", fontWeight: "500", flex: 1 },
  karakaRow: { flexDirection: "row", gap: 8, paddingVertical: 8, flexWrap: "wrap" },
  karakaLabel: { fontSize: 11 },
  karakaValue: { fontSize: 11, flex: 1 },
});
