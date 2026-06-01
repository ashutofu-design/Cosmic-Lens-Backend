/**
 * Room scan pricing — always visible ₹99 / ₹249 / ₹399 cards.
 */
import * as Haptics from "expo-haptics";
import React, { useMemo } from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";

import { useC } from "@/context/ThemeContext";
import {
  mergeRoomScanCatalog,
  ROOM_SCAN_SKUS,
  type RoomScanSku,
  type RoomScanSkuSpec,
} from "@/lib/astrovastuRoomPricing";

type Props = {
  onSelectSku: (sku: RoomScanSku) => void;
  catalog?: Record<string, Partial<RoomScanSkuSpec>> | null;
  /** Pro subscription — show note; cards still tappable to buy extra credits */
  isPro?: boolean;
  credits?: number;
  compact?: boolean;
};

export function RoomScanPricingBar({
  onSelectSku,
  catalog,
  isPro = false,
  credits = 0,
  compact = false,
}: Props) {
  const C = useC();
  const merged = useMemo(() => mergeRoomScanCatalog(catalog), [catalog]);

  return (
    <View style={[s.wrap, compact ? { marginBottom: 12 } : { marginTop: 4, marginBottom: 14 }]}>
      <Text style={[s.title, { color: C.textMuted }]}>ROOM SCAN PRICING</Text>
      {isPro ? (
        <Text style={[s.proNote, { color: C.accent }]}>
          {credits > 0
            ? `${credits} prepaid scan${credits > 1 ? "s" : ""} left · or buy more below`
            : "Pay per room · buy a pack below to upload a photo"}
        </Text>
      ) : credits > 0 ? (
        <Text style={[s.proNote, { color: "#3b82f6" }]}>
          {credits} scan{credits > 1 ? "s" : ""} left in your wallet
        </Text>
      ) : null}
      <View style={s.grid}>
        {ROOM_SCAN_SKUS.map((sku) => {
          const spec = merged[sku];
          const popular = sku === "bundle_249";
          const best = sku === "bundle_399";
          return (
            <Pressable
              key={sku}
              onPress={() => {
                Haptics.selectionAsync();
                onSelectSku(sku);
              }}
              style={({ pressed }) => [
                s.card,
                {
                  borderColor: best ? "#f9d76b" : popular ? C.accent : C.border,
                  backgroundColor: C.isDark ? "#0b1220" : "#f7f7fb",
                  opacity: pressed ? 0.85 : 1,
                },
              ]}
            >
              {popular ? (
                <Text style={[s.badge, { backgroundColor: C.accent, color: "#fff" }]}>POPULAR</Text>
              ) : null}
              {best ? (
                <Text style={[s.badge, { backgroundColor: "#f9d76b", color: "#3a2404" }]}>BEST</Text>
              ) : null}
              <Text style={[s.rooms, { color: C.textMuted }]}>
                {spec.credits} room{spec.credits > 1 ? "s" : ""}
              </Text>
              <Text style={[s.price, { color: C.text }]}>₹{spec.price}</Text>
              <Text style={[s.per, { color: C.textMuted }]}>
                ₹{Math.round(spec.price / spec.credits)}/scan
              </Text>
            </Pressable>
          );
        })}
      </View>
      <Text style={[s.hint, { color: C.textMuted }]}>
        Tap to pay · 1 credit = 1 Upload Photo room scan
      </Text>
    </View>
  );
}

const s = StyleSheet.create({
  wrap: { gap: 8 },
  title: { fontSize: 10, fontWeight: "800", letterSpacing: 1.2 },
  proNote: { fontSize: 11, fontWeight: "700", lineHeight: 16 },
  grid: { flexDirection: "row", gap: 8 },
  card: {
    flex: 1,
    borderRadius: 12,
    borderWidth: 1.5,
    paddingVertical: 12,
    paddingHorizontal: 6,
    alignItems: "center",
    gap: 2,
    minHeight: 86,
  },
  badge: {
    fontSize: 7,
    fontWeight: "900",
    letterSpacing: 0.5,
    paddingHorizontal: 5,
    paddingVertical: 2,
    borderRadius: 4,
    marginBottom: 2,
  },
  rooms: { fontSize: 10, fontWeight: "700" },
  price: { fontSize: 18, fontWeight: "900" },
  per: { fontSize: 9, fontWeight: "600" },
  hint: { fontSize: 10, lineHeight: 14 },
});
