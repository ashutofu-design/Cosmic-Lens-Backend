/**
 * Home / Shop / Office / Factory — choose before floor plan upload (with per-type price).
 */
import { Feather } from "@expo/vector-icons";
import * as Haptics from "expo-haptics";
import React, { useMemo } from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";

import type { PlanKind, PlanKindLabels } from "@/lib/planKind";
import { useC } from "@/context/ThemeContext";
import { priceForPlanKind } from "@/lib/astrovastuFloorPlanPricing";

const OPTS: { key: PlanKind; icon: keyof typeof Feather.glyphMap }[] = [
  { key: "home", icon: "home" },
  { key: "shop", icon: "shopping-bag" },
  { key: "office", icon: "briefcase" },
  { key: "factory", icon: "tool" },
];

type Props = {
  value: PlanKind | null;
  onChange: (k: PlanKind) => void;
  labels: PlanKindLabels;
  disabled?: boolean;
  detected?: PlanKind | "unclear" | null;
  catalog?: Record<string, { price?: number; label?: string }> | null;
  floorScanWallet?: Record<string, number> | null;
};

export function FloorPlanKindPicker({
  value,
  onChange,
  labels,
  disabled,
  detected,
  catalog,
  floorScanWallet,
}: Props) {
  const C = useC();

  const prices = useMemo(() => {
    const out: Record<PlanKind, number> = {
      home: priceForPlanKind("home", catalog).price,
      shop: priceForPlanKind("shop", catalog).price,
      office: priceForPlanKind("office", catalog).price,
      factory: priceForPlanKind("factory", catalog).price,
    };
    return out;
  }, [catalog]);

  return (
    <View style={[s.wrap, { backgroundColor: C.bgCard, borderColor: C.border }]}>
      <Text style={[s.title, { color: C.text }]}>{labels.title}</Text>
      <Text style={[s.hint, { color: C.textMid }]}>{labels.hint}</Text>
      <View style={s.row}>
        {OPTS.map(({ key, icon }) => {
          const sel = value === key;
          const wrong = detected && detected !== "unclear" && key !== detected;
          const label =
            key === "home"
              ? labels.home
              : key === "shop"
                ? labels.shop
                : key === "office"
                  ? labels.office
                  : labels.factory;
          const paidLeft = floorScanWallet?.[key] ?? 0;
          return (
            <Pressable
              key={key}
              disabled={disabled}
              onPress={() => {
                Haptics.selectionAsync();
                onChange(key);
              }}
              style={({ pressed }) => [
                s.btn,
                {
                  borderColor: sel ? C.accent : wrong ? "#EF444488" : C.border,
                  backgroundColor: sel ? C.accent + "18" : "transparent",
                  opacity: disabled ? 0.5 : pressed ? 0.85 : 1,
                },
              ]}
            >
              <Feather
                name={icon}
                size={18}
                color={sel ? C.accent : wrong ? "#EF4444" : C.textMid}
              />
              <Text
                style={{
                  color: sel ? C.accent : wrong ? "#EF4444" : C.text,
                  fontWeight: "700",
                  fontSize: 12,
                  marginTop: 6,
                  textAlign: "center",
                }}
                numberOfLines={2}
              >
                {label}
              </Text>
              <Text
                style={{
                  color: sel ? C.accent : C.textMid,
                  fontWeight: "900",
                  fontSize: 15,
                  marginTop: 4,
                }}
              >
                ₹{prices[key]}
              </Text>
              {paidLeft > 0 ? (
                <Text style={[s.paidBadge, { color: "#10B981" }]}>
                  {paidLeft} paid
                </Text>
              ) : (
                <Text style={[s.perScan, { color: C.textMuted }]}>per scan</Text>
              )}
            </Pressable>
          );
        })}
      </View>
    </View>
  );
}

const s = StyleSheet.create({
  wrap: {
    borderRadius: 12,
    borderWidth: 1,
    padding: 14,
    marginBottom: 12,
  },
  title: { fontSize: 14, fontWeight: "800", marginBottom: 4 },
  hint: { fontSize: 12, lineHeight: 17, marginBottom: 12 },
  row: { flexDirection: "row", flexWrap: "wrap", gap: 10 },
  btn: {
    width: "47%",
    paddingVertical: 12,
    paddingHorizontal: 8,
    borderRadius: 10,
    borderWidth: 1.5,
    alignItems: "center",
  },
  perScan: { fontSize: 9, fontWeight: "600", marginTop: 2 },
  paidBadge: { fontSize: 9, fontWeight: "800", marginTop: 2 },
});
