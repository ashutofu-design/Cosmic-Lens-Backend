/**
 * AstroVastuWallet — Phase-2 status + buy CTAs widget.
 *
 * Shown atop /astrovastu-basic and /astrovastu-pro. Fetches the user's
 * unlock state (room credits + lifetime property unlocks + plan) and
 * renders one of three states:
 *
 *   1) Pro plan        → green pill "Pro Plan • Unlimited"
 *   2) Has credits     → blue pill "N credits left" + buy more
 *   3) Has unlocks     → gold pill "Mumbai Flat • Unlimited" + property picker
 *   4) Nothing         → gold "Unlock AstroVastu" CTA opens BuyOptionsSheet
 *
 * Phase 3 will replace the dev-grant call with a Cashfree WebView session.
 */
import { Feather } from "@expo/vector-icons";
import * as Haptics from "expo-haptics";
import { router } from "expo-router";
import React, { useCallback, useEffect, useState } from "react";
import {
  ActivityIndicator,
  Alert,
  Modal,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";

import { useC } from "@/context/ThemeContext";
import { useUser } from "@/context/UserContext";
import { API_BASE } from "@/lib/apiConfig";

// ─────────────────────────────────────────────────────────────────────
// Types (mirror backend SKU_CATALOG + status response)
// ─────────────────────────────────────────────────────────────────────
type Sku = {
  price: number;
  label: string;
  grants: "credits" | "unlock";
  credits?: number;
};
type Catalog = Record<string, Sku>;

export type UnlockedProperty = {
  property_name: string;
  tier: string;
  unlocked_at: string | null;
};

export type WalletStatus = {
  plan: string;
  is_pro: boolean;
  room_credits: number;
  unlocked_properties: UnlockedProperty[];
  monthly_pro_used: number;
  monthly_pro_limit: number;
  catalog: Catalog;
};

// SKUs grouped for the buy sheet
const HOME_SKUS: string[] = ["1room_199", "bundle_499", "full_home_2999"];
const BIZ_SKUS:  string[] = ["shop_999", "office_1499", "factory_2999"];

// ─────────────────────────────────────────────────────────────────────
type Props = {
  /** Variant tunes copy + which SKUs are emphasised */
  variant?: "basic" | "pro";
  /** Currently active property — sent to PRO scan; required for unlock SKUs */
  propertyName?: string;
  onPropertyNameChange?: (name: string) => void;
  /** Bumps a counter to force-refresh status (e.g. after a successful scan) */
  refreshKey?: number;
  /** Called when status is loaded so parent screens can read credits/unlocks */
  onStatus?: (s: WalletStatus | null) => void;
};

export function AstroVastuWallet({
  variant = "basic",
  propertyName = "",
  onPropertyNameChange,
  refreshKey = 0,
  onStatus,
}: Props) {
  const C = useC();
  const { user } = useUser();
  const [status, setStatus]   = useState<WalletStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [buyOpen, setBuyOpen] = useState(false);

  // ── Fetch status ───────────────────────────────────────────────────
  const loadStatus = useCallback(async () => {
    if (!user?.id || !user?.api_key) {
      setLoading(false);
      return;
    }
    try {
      const res = await fetch(`${API_BASE}/api/astrovastu/status`, {
        method:  "POST",
        headers: { "Content-Type": "application/json", "X-API-Key": user.api_key },
        body:    JSON.stringify({ user_id: user.id }),
      });
      if (res.ok) {
        const body = (await res.json()) as WalletStatus;
        setStatus(body);
        onStatus?.(body);
      }
    } catch {
      /* silent — wallet is non-blocking */
    } finally {
      setLoading(false);
    }
  }, [user?.id, user?.api_key, onStatus]);

  useEffect(() => { loadStatus(); }, [loadStatus, refreshKey]);

  // ── Buy flow (Phase 3 — Cashfree one-time WebView) ─────────────────
  const handleBuy = useCallback(async (sku: string) => {
    if (!user?.id || !user?.api_key) return;
    const spec = status?.catalog?.[sku];
    if (!spec) return;

    // Unlock SKUs need a property name
    let propName = propertyName.trim();
    if (spec.grants === "unlock" && !propName) {
      Alert.alert(
        "Property name required",
        "Please name this property (e.g. 'Mumbai Flat') above before buying.",
      );
      setBuyOpen(false);
      return;
    }

    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);

    try {
      const orderRes = await fetch(`${API_BASE}/api/astrovastu/create-order`, {
        method:  "POST",
        headers: { "Content-Type": "application/json", "X-API-Key": user.api_key },
        body:    JSON.stringify({
          user_id: user.id, sku, property_name: propName,
        }),
      });
      const order = await orderRes.json();
      if (!orderRes.ok || !order?.payment_session_id) {
        Alert.alert(
          "Couldn't start payment",
          order?.detail || order?.message || order?.error || "Try again.",
        );
        return;
      }

      setBuyOpen(false);
      // Hand off to the shared payment WebView (kind=astrovastu branch).
      router.push({
        pathname: "/payment-webview",
        params: {
          plan:        "astrovastu",
          cycle:       "onetime",
          kind:        "astrovastu",
          sku,
          purchaseId:  String(order.purchase_id),
          orderId:     order.order_id,
          sessionId:   order.payment_session_id,
          paymentLink: order.payment_link || "",
          amount:      String(order.amount || spec.price),
          label:       spec.label,
          propertyName: propName,
        },
      });
    } catch (e: any) {
      Alert.alert("Network error", e?.message || "Try again.");
    }
  }, [user, status?.catalog, propertyName]);

  // ── Skeleton ───────────────────────────────────────────────────────
  if (loading) {
    return (
      <View style={[s.card, { backgroundColor: C.bgCard, borderColor: C.border }]}>
        <ActivityIndicator color={C.text} />
      </View>
    );
  }
  if (!status) return null;

  // ── Derived banner state ───────────────────────────────────────────
  const isPro     = status.is_pro;
  const credits   = status.room_credits || 0;
  const unlocks   = status.unlocked_properties || [];
  const hasUnlock = unlocks.length > 0;

  // Banner colors
  const bannerColor = isPro
    ? "#10b981"        // green = unlimited
    : hasUnlock
      ? "#f9d76b"      // gold = property unlocked
      : credits > 0
        ? "#3b82f6"    // blue = credits available
        : "#a78bfa";   // purple = nothing yet, prompt to buy

  const bannerText = isPro
    ? "Pro Plan  •  Unlimited everything"
    : hasUnlock
      ? `${unlocks[0].property_name}  •  Unlocked for life`
      : credits > 0
        ? `${credits} room credit${credits > 1 ? "s" : ""} available`
        : variant === "pro"
          ? "Unlock this home for ₹2,999 (lifetime) or upgrade to Pro"
          : "Buy a Room Check ₹199, Bundle ₹499, or Full Home ₹2,999";

  return (
    <View style={[s.card, {
      backgroundColor: C.bgCard,
      borderColor: bannerColor + "55",
      borderWidth: 1.5,
    }]}>
      {/* ── Status header row ───────────────────────────────────── */}
      <View style={s.row}>
        <View style={[s.dot, { backgroundColor: bannerColor }]} />
        <Text style={[s.statusText, { color: C.text }]} numberOfLines={2}>
          {bannerText}
        </Text>
      </View>

      {/* ── PRO variant: property name input (drives unlock matching) */}
      {variant === "pro" && !isPro && (
        <View style={{ marginTop: 10 }}>
          <Text style={[s.label, { color: C.textMuted }]}>Property name</Text>
          <TextInput
            value={propertyName}
            onChangeText={onPropertyNameChange}
            placeholder='e.g. "Mumbai Flat"'
            placeholderTextColor={C.textMuted}
            style={[s.input, {
              color: C.text,
              backgroundColor: C.isDark ? "#0b1220" : "#f3f4f6",
              borderColor: C.border,
            }]}
            maxLength={80}
          />
          {hasUnlock && unlocks.length > 0 && (
            <View style={s.unlockChips}>
              {unlocks.slice(0, 4).map((u) => (
                <Pressable
                  key={u.property_name}
                  onPress={() => onPropertyNameChange?.(u.property_name)}
                  style={[s.chip, { borderColor: "#f9d76b88" }]}>
                  <Feather name="check-circle" size={11} color="#f9d76b" />
                  <Text style={[s.chipText, { color: C.text }]} numberOfLines={1}>
                    {u.property_name}
                  </Text>
                </Pressable>
              ))}
            </View>
          )}
        </View>
      )}

      {/* ── Buy CTA (hidden when Pro plan covers everything) ────── */}
      {!isPro && (
        <Pressable onPress={() => { Haptics.selectionAsync(); setBuyOpen(true); }}
                   style={[s.cta, { backgroundColor: bannerColor }]}>
          <Feather name="shopping-bag" size={14} color="#0a0a14" />
          <Text style={s.ctaText}>
            {credits > 0 || hasUnlock ? "Buy more / Manage" : "Unlock AstroVastu"}
          </Text>
        </Pressable>
      )}

      {/* ── Buy options sheet ───────────────────────────────────── */}
      <BuyOptionsSheet
        visible={buyOpen}
        onClose={() => setBuyOpen(false)}
        catalog={status.catalog}
        homeSkus={HOME_SKUS}
        bizSkus={BIZ_SKUS}
        onBuy={handleBuy}
      />
    </View>
  );
}

// ─────────────────────────────────────────────────────────────────────
// BuyOptionsSheet — modal listing all SKUs with price + label + buy btn
// ─────────────────────────────────────────────────────────────────────
function BuyOptionsSheet({
  visible, onClose, catalog, homeSkus, bizSkus, onBuy,
}: {
  visible: boolean;
  onClose: () => void;
  catalog: Catalog;
  homeSkus: string[];
  bizSkus: string[];
  onBuy: (sku: string) => void;
}) {
  const C = useC();
  const renderRow = (sku: string) => {
    const spec = catalog[sku];
    if (!spec) return null;
    const isBest = sku === "full_home_2999";
    return (
      <Pressable
        key={sku}
        onPress={() => onBuy(sku)}
        style={[s.skuRow, {
          borderColor: isBest ? "#f9d76b" : C.border,
          backgroundColor: C.isDark ? "#0b1220" : "#f7f7fb",
        }]}>
        <View style={{ flex: 1 }}>
          <Text style={[s.skuLabel, { color: C.text }]}>{spec.label}</Text>
          {spec.grants === "unlock" && (
            <Text style={[s.skuSub, { color: C.textMuted }]}>Lifetime · per property</Text>
          )}
          {spec.grants === "credits" && (
            <Text style={[s.skuSub, { color: C.textMuted }]}>
              {spec.credits} room check{(spec.credits ?? 1) > 1 ? "s" : ""}
            </Text>
          )}
        </View>
        {isBest && (
          <View style={s.bestBadge}><Text style={s.bestBadgeText}>BEST VALUE</Text></View>
        )}
        <Text style={[s.skuPrice, { color: C.text }]}>₹{spec.price}</Text>
      </Pressable>
    );
  };

  return (
    <Modal visible={visible} transparent animationType="slide" onRequestClose={onClose}>
      <Pressable style={s.modalBackdrop} onPress={onClose} />
      <View style={[s.modalSheet, { backgroundColor: C.bg }]}>
        <View style={s.modalHandle} />
        <View style={s.modalHeader}>
          <Text style={[s.modalTitle, { color: C.text }]}>AstroVastu Unlocks</Text>
          <Pressable onPress={onClose} hitSlop={10}>
            <Feather name="x" size={22} color={C.text} />
          </Pressable>
        </View>

        <ScrollView contentContainerStyle={{ padding: 16, gap: 16, paddingBottom: 32 }}>
          <View>
            <Text style={[s.section, { color: C.textMuted }]}>HOME</Text>
            <View style={{ gap: 8, marginTop: 6 }}>
              {homeSkus.map(renderRow)}
            </View>
          </View>
          <View>
            <Text style={[s.section, { color: C.textMuted }]}>BUSINESS  •  Coming soon</Text>
            <View style={{ gap: 8, marginTop: 6, opacity: 0.55 }}>
              {bizSkus.map(renderRow)}
            </View>
          </View>
          <Text style={[s.fineprint, { color: C.textMuted }]}>
            One-time payments · No auto-renewal · Lifetime unlocks tied to property name.
          </Text>
        </ScrollView>
      </View>
    </Modal>
  );
}

// ─────────────────────────────────────────────────────────────────────
const s = StyleSheet.create({
  card:        { borderRadius: 14, padding: 14, marginBottom: 14, gap: 4 },
  row:         { flexDirection: "row", alignItems: "center", gap: 10 },
  dot:         { width: 10, height: 10, borderRadius: 5 },
  statusText:  { fontSize: 13, fontWeight: "700", flex: 1, lineHeight: 18 },
  label:       { fontSize: 10, fontWeight: "800", letterSpacing: 1, marginBottom: 4 },
  input:       { borderRadius: 10, borderWidth: 1, paddingHorizontal: 12, paddingVertical: 9, fontSize: 14 },
  unlockChips: { flexDirection: "row", flexWrap: "wrap", gap: 6, marginTop: 8 },
  chip:        { flexDirection: "row", alignItems: "center", gap: 4, paddingHorizontal: 8, paddingVertical: 4, borderRadius: 12, borderWidth: 1 },
  chipText:    { fontSize: 11, fontWeight: "700", maxWidth: 110 },
  cta:         { marginTop: 12, flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 8, paddingVertical: 11, borderRadius: 11 },
  ctaText:     { color: "#0a0a14", fontSize: 13, fontWeight: "900", letterSpacing: 0.4 },

  // Modal
  modalBackdrop: { ...StyleSheet.absoluteFillObject, backgroundColor: "rgba(0,0,0,0.55)" },
  modalSheet:    { position: "absolute", left: 0, right: 0, bottom: 0, borderTopLeftRadius: 20, borderTopRightRadius: 20, maxHeight: "85%" },
  modalHandle:   { alignSelf: "center", width: 36, height: 4, borderRadius: 2, backgroundColor: "#888", marginTop: 8, opacity: 0.5 },
  modalHeader:   { flexDirection: "row", justifyContent: "space-between", alignItems: "center", paddingHorizontal: 16, paddingTop: 10, paddingBottom: 4 },
  modalTitle:    { fontSize: 17, fontWeight: "900" },
  section:       { fontSize: 11, fontWeight: "900", letterSpacing: 1.2 },

  // SKU row
  skuRow:        { flexDirection: "row", alignItems: "center", gap: 10, padding: 14, borderRadius: 12, borderWidth: 1.5 },
  skuLabel:      { fontSize: 14, fontWeight: "800" },
  skuSub:        { fontSize: 11, marginTop: 2 },
  skuPrice:      { fontSize: 16, fontWeight: "900" },
  bestBadge:     { backgroundColor: "#f9d76b", paddingHorizontal: 7, paddingVertical: 3, borderRadius: 5 },
  bestBadgeText: { fontSize: 8, fontWeight: "900", color: "#3a2404", letterSpacing: 0.6 },
  fineprint:     { fontSize: 10.5, lineHeight: 15, textAlign: "center", marginTop: 4 },
});
