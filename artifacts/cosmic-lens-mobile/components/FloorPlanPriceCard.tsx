import React from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";

import type { WalletStatus } from "@/components/AstroVastuWallet";
import { useC } from "@/context/ThemeContext";
import { useT } from "@/hooks/useT";
import { priceForPlanKind } from "@/lib/astrovastuFloorPlanPricing";
import type { PlanKind } from "@/lib/planKind";
import { canRunWholePlanProScan, floorScanCreditsFor } from "@/lib/astrovastuWalletGate";

type Props = {
  planKind: PlanKind;
  walletStatus: WalletStatus | null;
  loading?: boolean;
  onPay: () => void;
};

export function FloorPlanPriceCard({ planKind, walletStatus, loading, onPay }: Props) {
  const C = useC();
  const t = useT() as Record<string, string>;
  const spec = priceForPlanKind(planKind, walletStatus?.catalog);
  const paid = floorScanCreditsFor(walletStatus, planKind);
  const canScan = canRunWholePlanProScan(walletStatus, planKind);

  if (walletStatus?.is_pro) return null;

  return (
    <View
      style={[s.wrap, { backgroundColor: C.accentBg, borderColor: C.accent + "55" }]}
    >
      <Text style={[s.title, { color: C.text }]}>{spec.label}</Text>
      <Text style={[s.body, { color: C.textMid }]}>
        {canScan && paid > 0
          ? (t.avp_floorScanReady ||
              "You have 1 paid scan for this plan type. Upload your PDF/image, then run the scan.")
          : (t.avp_floorPlanPriceNote ||
              "₹{price} one-time · personalized Vastu report + downloadable PDF").replace(
              "{price}",
              String(spec.price),
            )}
      </Text>
      {!canScan || paid < 1 ? (
        <Pressable
          onPress={onPay}
          disabled={loading}
          style={({ pressed }) => [
            s.btn,
            { backgroundColor: C.accent, opacity: loading || pressed ? 0.85 : 1 },
          ]}
        >
          <Text style={s.btnTxt}>
            {(t.avp_btnPayFloorScan || "Pay ₹{price}").replace("{price}", String(spec.price))}
          </Text>
        </Pressable>
      ) : null}
    </View>
  );
}

const s = StyleSheet.create({
  wrap: { borderRadius: 12, borderWidth: 1, padding: 14, marginBottom: 12 },
  title: { fontWeight: "800", fontSize: 14 },
  body: { fontSize: 12, marginTop: 4, lineHeight: 17 },
  btn: { marginTop: 12, paddingVertical: 13, borderRadius: 12, alignItems: "center" },
  btnTxt: { color: "#fff", fontWeight: "800", fontSize: 14 },
});
