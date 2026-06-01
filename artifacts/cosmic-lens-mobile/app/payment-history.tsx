import { Feather } from "@expo/vector-icons";
import * as Haptics from "expo-haptics";
import { router, useFocusEffect } from "expo-router";
import React, { useCallback, useState } from "react";
import {
  ActivityIndicator,
  FlatList,
  I18nManager,
  Pressable,
  RefreshControl,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { CosmicBg } from "@/components/CosmicBg";
import { useC } from "@/context/ThemeContext";
import { useUser } from "@/context/UserContext";
import { useT } from "@/hooks/useT";
import { API_BASE } from "@/lib/apiConfig";

export type PurchaseRow = {
  id: string;
  kind: string;
  title: string;
  subtitle?: string;
  amount_inr: number;
  order_id: string;
  status: string;
  paid_at: string | null;
};

function labels(t: ReturnType<typeof useT>) {
  const hn = t.lang === "hn";
  const hi = t.lang === "hi";
  return {
    title: hi ? "भुगतान इतिहास" : hn ? "Payment History" : "Payment History",
    sub: hi
      ? "आपकी सफल खरीदारी और ऑर्डर"
      : hn
        ? "Aapki successful purchases aur orders"
        : "Your successful purchases and orders",
    empty: hi
      ? "अभी कोई खरीदारी नहीं"
      : hn
        ? "Abhi koi purchase nahi"
        : "No purchases yet",
    emptySub: hi
      ? "PDF, AstroVastu या subscription खरीदने पर यहाँ दिखेगा"
      : hn
        ? "PDF, AstroVastu ya subscription lene par yahan dikhega"
        : "Purchases appear here after you pay for reports or plans",
    order: hi ? "ऑर्डर" : hn ? "Order" : "Order",
    paid: hi ? "भुगतान" : hn ? "Paid" : "Paid",
    login: hi ? "लॉगिन ज़रूरी" : hn ? "Login zaroori" : "Please sign in",
  };
}

function formatWhen(iso: string | null) {
  if (!iso) return "—";
  try {
    const d = new Date(/[zZ]|[+-]\d{2}/.test(iso) ? iso : `${iso}Z`);
    if (Number.isNaN(d.getTime())) return iso.slice(0, 10);
    return d.toLocaleString("en-IN", {
      timeZone: "Asia/Kolkata",
      dateStyle: "medium",
      timeStyle: "short",
    });
  } catch {
    return iso.slice(0, 16);
  }
}

function kindIcon(kind: string): keyof typeof Feather.glyphMap {
  if (kind === "subscription") return "award";
  if (kind === "astrovastu" || kind === "property_unlock") return "home";
  if (kind === "career") return "briefcase";
  return "file-text";
}

export default function PaymentHistoryScreen() {
  const insets = useSafeAreaInsets();
  const C = useC();
  const t = useT();
  const L = labels(t);
  const { user } = useUser();
  const ac = C.isDark ? "#f59e0b" : "#7C3AED";

  const [items, setItems] = useState<PurchaseRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");

  const fetchPurchases = useCallback(async () => {
    if (!user?.id || !user?.api_key) {
      setItems([]);
      setLoading(false);
      setError(L.login);
      return;
    }
    setError("");
    try {
      const r = await fetch(`${API_BASE}/api/user/${user.id}/purchases`, {
        headers: { "X-API-Key": user.api_key },
      });
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const data = await r.json();
      setItems(data?.purchases ?? []);
    } catch {
      setError(t.lang === "hn" ? "Load nahi ho paya. Dubara try karein." : "Couldn't load. Pull to retry.");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [user?.id, user?.api_key, L.login, t.lang]);

  useFocusEffect(
    useCallback(() => {
      setLoading(true);
      fetchPurchases();
    }, [fetchPurchases]),
  );

  return (
    <CosmicBg>
      <View style={[s.root, { paddingTop: insets.top + 8, paddingBottom: insets.bottom + 16 }]}>
        <View style={[s.header, { borderBottomColor: C.border }]}>
          <Pressable
            onPress={() => router.back()}
            style={[s.backBtn, { backgroundColor: C.bgCard, borderColor: C.border }]}
            hitSlop={8}
          >
            <Feather name={I18nManager.isRTL ? "arrow-right" : "arrow-left"} size={20} color={C.text} />
          </Pressable>
          <View style={{ flex: 1 }}>
            <Text style={[s.headerTitle, { color: C.text }]}>{L.title}</Text>
            <Text style={[s.headerSub, { color: C.textMuted }]}>{L.sub}</Text>
          </View>
          <View style={{ width: 36 }} />
        </View>

        {loading && items.length === 0 ? (
          <View style={s.center}>
            <ActivityIndicator color={ac} />
          </View>
        ) : (
          <FlatList
            data={items}
            keyExtractor={(item) => item.id}
            contentContainerStyle={[
              s.list,
              items.length === 0 && { flexGrow: 1, justifyContent: "center" },
            ]}
            refreshControl={
              <RefreshControl
                refreshing={refreshing}
                onRefresh={() => {
                  setRefreshing(true);
                  fetchPurchases();
                }}
                tintColor={ac}
              />
            }
            ListEmptyComponent={
              <View style={s.center}>
                <Feather name="shopping-bag" size={40} color={C.textDim} />
                <Text style={[s.emptyTitle, { color: C.text }]}>{error || L.empty}</Text>
                {!error ? (
                  <Text style={[s.emptySub, { color: C.textMuted }]}>{L.emptySub}</Text>
                ) : null}
              </View>
            }
            renderItem={({ item }) => (
              <View style={[s.card, { backgroundColor: C.bgCard, borderColor: C.border }]}>
                <View style={[s.iconWrap, { backgroundColor: `${ac}18` }]}>
                  <Feather name={kindIcon(item.kind)} size={18} color={ac} />
                </View>
                <View style={{ flex: 1, gap: 4 }}>
                  <Text style={[s.cardTitle, { color: C.text }]} numberOfLines={2}>
                    {item.title}
                  </Text>
                  {item.subtitle ? (
                    <Text style={[s.cardSub, { color: C.textMuted }]} numberOfLines={1}>
                      {item.subtitle}
                    </Text>
                  ) : null}
                  <Text style={[s.meta, { color: C.textDim }]}>
                    {L.paid}: {formatWhen(item.paid_at)}
                  </Text>
                  {item.order_id ? (
                    <Text style={[s.meta, { color: C.textDim }]} numberOfLines={1}>
                      {L.order}: {item.order_id}
                    </Text>
                  ) : null}
                </View>
                <Text style={[s.amount, { color: ac }]}>
                  {item.amount_inr > 0 ? `₹${item.amount_inr.toLocaleString("en-IN")}` : "—"}
                </Text>
              </View>
            )}
          />
        )}
      </View>
    </CosmicBg>
  );
}

const s = StyleSheet.create({
  root: { flex: 1 },
  header: {
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: 16,
    paddingBottom: 12,
    borderBottomWidth: 1,
    gap: 10,
  },
  backBtn: {
    width: 36,
    height: 36,
    borderRadius: 18,
    alignItems: "center",
    justifyContent: "center",
    borderWidth: 1,
  },
  headerTitle: { fontSize: 18, fontFamily: "Nunito_700Bold" },
  headerSub: { fontSize: 11.5, fontFamily: "Nunito_500Medium", marginTop: 2 },
  center: { flex: 1, alignItems: "center", justifyContent: "center", padding: 32, gap: 10 },
  list: { padding: 16, gap: 10 },
  card: {
    flexDirection: "row",
    alignItems: "flex-start",
    gap: 12,
    padding: 14,
    borderRadius: 14,
    borderWidth: 1,
  },
  iconWrap: {
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: "center",
    justifyContent: "center",
  },
  cardTitle: { fontSize: 14, fontFamily: "Nunito_700Bold" },
  cardSub: { fontSize: 12, fontFamily: "Nunito_500Medium" },
  meta: { fontSize: 10.5, fontFamily: "Nunito_500Medium" },
  amount: { fontSize: 15, fontFamily: "Nunito_700Bold", marginTop: 2 },
  emptyTitle: { fontSize: 16, fontFamily: "Nunito_700Bold", textAlign: "center", marginTop: 8 },
  emptySub: { fontSize: 12, fontFamily: "Nunito_500Medium", textAlign: "center", lineHeight: 18 },
});
