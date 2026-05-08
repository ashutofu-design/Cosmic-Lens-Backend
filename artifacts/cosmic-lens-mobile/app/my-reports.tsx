/**
 * Phase 5 — My Reports
 *
 * Combined history of paid AstroVastu PRO + Business Vastu deep-scans.
 * Each card lets the user reopen the PDF or share it on WhatsApp.
 *
 * Branding: "Powered by Advanced Cosmic Intelligence" — never reveal AI/LLM.
 */
import { Feather } from "@expo/vector-icons";
import * as Haptics from "expo-haptics";
import * as Linking from "expo-linking";
import * as WebBrowser from "expo-web-browser";
import { LinearGradient } from "expo-linear-gradient";
import { router, Stack, useFocusEffect } from "expo-router";
import React, { useCallback, useState } from "react";
import { useT } from "@/hooks/useT";
import {
  ActivityIndicator,
  Alert,
  FlatList,
  I18nManager,
  Pressable,
  RefreshControl,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { useC } from "@/context/ThemeContext";
import { useUser } from "@/context/UserContext";
import { API_BASE } from "@/lib/apiConfig";
import {
  openReportPdfWithLanguageChoice,
  pickReportPdfLanguage,
} from "@/lib/pdfLanguagePicker";
import {
  deleteLocalReport,
  listLocalReports,
  openLocalReport,
  shareLocalReport,
  type LocalReport,
} from "@/lib/localReports";

type HistoryItem = {
  kind: "business" | "pro";
  id: number;
  property_name: string;
  business_type: string | null;
  rooms_count: number;
  score: number;
  grade: string;
  created_at: string | null;
  pdf_url: string;
  pdf_token: string;
};

type HistoryResponse = { count: number; items: HistoryItem[] };

const GRADE_COLOR: Record<string, string> = {
  A: "#10b981", B: "#22c55e", C: "#eab308", D: "#f97316", E: "#ef4444",
};

function fmtDate(iso: string | null): string {
  if (!iso) return "";
  try {
    const d = new Date(iso);
    return d.toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" });
  } catch { return ""; }
}

function kindLabel(it: HistoryItem, t: ReturnType<typeof useT>): string {
  if (it.kind === "pro") return t.mr_kindHomePro;
  const bt = (it.business_type || "").toLowerCase();
  if (bt === "shop")    return t.mr_kindShop;
  if (bt === "office")  return t.mr_kindOffice;
  if (bt === "factory") return t.mr_kindFactory;
  return t.mr_kindBusiness;
}

export default function MyReportsScreen() {
  const insets = useSafeAreaInsets();
  const C = useC();
  const t = useT();
  const { user } = useUser();

  const [items, setItems]       = useState<HistoryItem[]>([]);
  const [localItems, setLocal]  = useState<LocalReport[]>([]);
  const [loading, setLoading]   = useState(false);
  const [refreshing, setRefresh]= useState(false);
  const [error, setError]       = useState<string | null>(null);

  const loadLocal = useCallback(async () => {
    try { setLocal(await listLocalReports()); } catch { setLocal([]); }
  }, []);

  const load = useCallback(async (silent = false) => {
    if (!user?.id || !user?.api_key) {
      setError(t.mr_loginRequired);
      return;
    }
    if (!silent) setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/api/user/${user.id}/reports/history?limit=100`, {
        headers: { "X-API-Key": user.api_key },
      });
      if (!res.ok) {
        setError(t.mr_loadError);
        setItems([]);
        return;
      }
      const data: HistoryResponse = await res.json();
      setItems(Array.isArray(data.items) ? data.items : []);
    } catch {
      setError(t.mr_networkError);
    } finally {
      setLoading(false);
      setRefresh(false);
    }
  }, [user?.id, user?.api_key]);

  useFocusEffect(useCallback(() => { load(); loadLocal(); }, [load, loadLocal]));

  const onOpenLocal = async (r: LocalReport) => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    await openLocalReport(r);
  };
  const onShareLocal = async (r: LocalReport) => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    await shareLocalReport(r);
  };
  const onDeleteLocal = (r: LocalReport) => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    Alert.alert(
      "Delete report?",
      `${r.title}\n\nYeh PDF aapke device se hata di jayegi.`,
      [
        { text: "Cancel", style: "cancel" },
        {
          text: "Delete", style: "destructive",
          onPress: async () => {
            await deleteLocalReport(r.id);
            await loadLocal();
          },
        },
      ],
    );
  };

  const KIND_LABEL: Record<LocalReport["kind"], string> = {
    milan:           "Kundli Milan",
    numerology:      "Numerology",
    astrovastu_pro:  "AstroVastu Pro",
    business_vastu:  "Business Vastu",
    face_reading:    "Face Reading",
    other:           "Report",
  };
  const KIND_ICON: Record<LocalReport["kind"], React.ComponentProps<typeof Feather>["name"]> = {
    milan:           "heart",
    numerology:      "hash",
    astrovastu_pro:  "home",
    business_vastu:  "briefcase",
    face_reading:    "user",
    other:           "file-text",
  };

  const renderLocalCard = (r: LocalReport) => {
    const created = new Date(r.createdAt);
    const date = created.toLocaleDateString("en-IN", {
      day: "numeric", month: "short", year: "numeric",
    });
    const time = created.toLocaleTimeString("en-IN", {
      hour: "numeric", minute: "2-digit", hour12: true,
    });
    return (
      <View
        key={r.id}
        style={[s.card, { backgroundColor: C.isDark ? "#0e1318" : "#ffffff", borderColor: C.border, marginBottom: 12 }]}
      >
        <View style={s.cardTop}>
          <View style={[s.scoreBadge, { backgroundColor: (C.accent || "#f6c453") + "22", borderColor: C.accent || "#f6c453" }]}>
            <Feather name={KIND_ICON[r.kind]} size={26} color={C.accent || "#f6c453"} />
          </View>
          <View style={s.cardMeta}>
            <Text style={[s.kindLabel, { color: C.textMuted }]} numberOfLines={1}>
              {KIND_LABEL[r.kind]}
            </Text>
            <Text style={[s.propName, { color: C.text }]} numberOfLines={2}>
              {r.title}
            </Text>
            <Text style={[s.subMeta, { color: C.textMuted }]} numberOfLines={1}>
              {date} · {time}
            </Text>
          </View>
        </View>
        <View style={s.btnRow}>
          <Pressable
            onPress={() => onOpenLocal(r)}
            style={({ pressed }) => [
              s.actionBtn,
              { backgroundColor: C.isDark ? "#1a2330" : "#eef3fb", opacity: pressed ? 0.85 : 1, borderColor: C.border },
            ]}
          >
            <Feather name="file-text" size={16} color={C.text} />
            <Text style={[s.actionText, { color: C.text }]}>Open</Text>
          </Pressable>
          <Pressable
            onPress={() => onShareLocal(r)}
            style={({ pressed }) => [
              s.actionBtn,
              { backgroundColor: "#25D366", opacity: pressed ? 0.85 : 1, borderColor: "#1ebe5b" },
            ]}
          >
            <Feather name="share-2" size={16} color="#ffffff" />
            <Text style={[s.actionText, { color: "#ffffff" }]}>Share</Text>
          </Pressable>
          <Pressable
            onPress={() => onDeleteLocal(r)}
            style={({ pressed }) => [
              s.actionBtn,
              { backgroundColor: "rgba(239,68,68,0.10)", opacity: pressed ? 0.85 : 1, borderColor: "rgba(239,68,68,0.4)", flex: 0, paddingHorizontal: 14 },
            ]}
          >
            <Feather name="trash-2" size={16} color="#ef4444" />
          </Pressable>
        </View>
      </View>
    );
  };

  const LocalHeader = () => {
    if (localItems.length === 0 && !error) return null;
    return (
      <View style={{ marginBottom: 18 }}>
        {error ? (
          <View
            style={{
              borderRadius: 10, borderWidth: 1, borderColor: "rgba(239,68,68,0.4)",
              backgroundColor: "rgba(239,68,68,0.08)", paddingVertical: 10, paddingHorizontal: 12,
              flexDirection: "row", alignItems: "center", gap: 10, marginBottom: 14,
            }}
          >
            <Feather name="alert-circle" size={16} color="#ef4444" />
            <Text style={{ color: C.text, fontSize: 12, flex: 1 }} numberOfLines={2}>
              Server reports load nahi hue · {error}
            </Text>
            <Pressable onPress={() => load()} hitSlop={8}>
              <Text style={{ color: "#ef4444", fontWeight: "700", fontSize: 12 }}>Retry</Text>
            </Pressable>
          </View>
        ) : null}
        {localItems.length > 0 ? (
          <>
            <Text style={[s.kindLabel, { color: C.textMuted, marginBottom: 10, letterSpacing: 1 }]}>
              SAVED ON THIS DEVICE · {localItems.length}
            </Text>
            {localItems.map(renderLocalCard)}
          </>
        ) : null}
      </View>
    );
  };

  const onOpenPdf = (it: HistoryItem) => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    const url = `${API_BASE}${it.pdf_url}?t=${encodeURIComponent(it.pdf_token)}`;
    openReportPdfWithLanguageChoice(url);
  };

  const onShareWhatsApp = (it: HistoryItem) => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    const baseUrl = `${API_BASE}${it.pdf_url}?t=${encodeURIComponent(it.pdf_token)}`;
    pickReportPdfLanguage(baseUrl, async (url) => {
    const msg =
      `🪔 *${kindLabel(it, t)}*\n` +
      `🏠 ${it.property_name}\n` +
      `📊 Score: ${it.score}/100 (Grade ${it.grade})\n\n` +
      `📄 Open report:\n${url}\n\n` +
      `_Powered by Advanced Cosmic Intelligence_`;
    const wa = `whatsapp://send?text=${encodeURIComponent(msg)}`;
    try {
      const can = await Linking.canOpenURL(wa);
      if (can) {
        await Linking.openURL(wa);
        return;
      }
      // Fallback to wa.me universal link (works on web & if WhatsApp not installed)
      const fallback = `https://wa.me/?text=${encodeURIComponent(msg)}`;
      await Linking.openURL(fallback);
    } catch {
      Alert.alert(
        t.mr_waErrorTitle,
        "Please install WhatsApp to share, or copy the report link manually."
      );
    }
    });
  };

  const renderItem = ({ item: it }: { item: HistoryItem }) => {
    const grade = GRADE_COLOR[it.grade] || C.textMuted;
    return (
      <View
        style={[
          s.card,
          { backgroundColor: C.isDark ? "#0e1318" : "#ffffff", borderColor: C.border },
        ]}
      >
        <View style={s.cardTop}>
          <View style={[s.scoreBadge, { backgroundColor: grade + "22", borderColor: grade }]}>
            <Text style={[s.scoreText, { color: grade }]}>{it.score}</Text>
            <Text style={[s.gradeText, { color: grade }]}>{it.grade}</Text>
          </View>
          <View style={s.cardMeta}>
            <Text style={[s.kindLabel, { color: C.textMuted }]} numberOfLines={1}>
              {kindLabel(it, t)}
            </Text>
            <Text style={[s.propName, { color: C.text }]} numberOfLines={1}>
              {it.property_name}
            </Text>
            <Text style={[s.subMeta, { color: C.textMuted }]}>
              {it.rooms_count} rooms · {fmtDate(it.created_at)}
            </Text>
          </View>
        </View>

        <View style={s.btnRow}>
          <Pressable
            onPress={() => onOpenPdf(it)}
            style={({ pressed }) => [
              s.actionBtn,
              {
                backgroundColor: C.isDark ? "#1a2330" : "#eef3fb",
                opacity: pressed ? 0.85 : 1,
                borderColor: C.border,
              },
            ]}
          >
            <Feather name="file-text" size={16} color={C.text} />
            <Text style={[s.actionText, { color: C.text }]}>{t.mr_openPdf}</Text>
          </Pressable>

          <Pressable
            onPress={() => onShareWhatsApp(it)}
            style={({ pressed }) => [
              s.actionBtn,
              {
                backgroundColor: "#25D366",
                opacity: pressed ? 0.85 : 1,
                borderColor: "#1ebe5b",
              },
            ]}
          >
            <Feather name="share-2" size={16} color="#ffffff" />
            <Text style={[s.actionText, { color: "#ffffff" }]}>{t.mr_whatsapp}</Text>
          </Pressable>
        </View>
      </View>
    );
  };

  return (
    <View style={[s.root, { backgroundColor: C.isDark ? "#050709" : C.bg }]}>
      <Stack.Screen options={{ headerShown: false }} />
      {C.isDark && (
        <LinearGradient
          colors={["#050709", "#0a0e14", "#0e1722"]}
          locations={[0, 0.55, 1]}
          style={StyleSheet.absoluteFill}
          pointerEvents="none"
        />
      )}

      {/* Header */}
      <View
        style={[
          s.header,
          { paddingTop: insets.top + 8, borderBottomColor: C.border },
        ]}
      >
        <Pressable onPress={() => router.back()} style={s.back} hitSlop={10}>
          <Feather name={I18nManager.isRTL ? "arrow-right" : "arrow-left"} size={20} color={C.textMuted} />
        </Pressable>
        <Text style={[s.title, { color: C.text }]}>{t.mr_pageTitle}</Text>
        <View style={{ width: 28 }} />
      </View>

      {loading && items.length === 0 ? (
        <View style={s.center}>
          <ActivityIndicator size="large" color={C.accent || "#f6c453"} />
          <Text style={[s.muted, { color: C.textMuted, marginTop: 12 }]}>
            {t.mr_loading}
          </Text>
        </View>
      ) : error && localItems.length === 0 ? (
        <View style={s.center}>
          <Feather name="alert-circle" size={36} color={C.textMuted} />
          <Text style={[s.muted, { color: C.textMuted, marginTop: 12, textAlign: "center" }]}>
            {error}
          </Text>
          <Pressable
            onPress={() => load()}
            style={[s.retryBtn, { borderColor: C.border }]}
          >
            <Text style={{ color: C.text, fontWeight: "600" }}>Retry</Text>
          </Pressable>
        </View>
      ) : items.length === 0 && localItems.length === 0 ? (
        <View style={s.center}>
          <Feather name="inbox" size={48} color={C.textMuted} />
          <Text style={[s.empty, { color: C.text }]}>{t.mr_emptyTitle}</Text>
          <Text style={[s.muted, { color: C.textMuted, textAlign: "center", marginTop: 6 }]}>
            Aapke saare generated PDF reports — Kundli Milan, Numerology, AstroVastu Pro, Business Vastu — yahan automatically save honge.
          </Text>
        </View>
      ) : (
        <FlatList
          data={items}
          keyExtractor={(it) => `${it.kind}-${it.id}`}
          renderItem={renderItem}
          contentContainerStyle={{ padding: 16, paddingBottom: insets.bottom + 32 }}
          ItemSeparatorComponent={() => <View style={{ height: 12 }} />}
          ListHeaderComponent={<LocalHeader />}
          refreshControl={
            <RefreshControl
              refreshing={refreshing}
              onRefresh={() => { setRefresh(true); load(true); loadLocal(); }}
              tintColor={C.textMuted}
            />
          }
          ListFooterComponent={
            <Text style={[s.footer, { color: C.textMuted }]}>
              {t.mr_footer}
            </Text>
          }
        />
      )}
    </View>
  );
}

const s = StyleSheet.create({
  root:    { flex: 1 },
  header:  {
    flexDirection: "row", alignItems: "center", justifyContent: "space-between",
    paddingHorizontal: 16, paddingBottom: 12, borderBottomWidth: StyleSheet.hairlineWidth,
  },
  back:    { padding: 4 },
  title:   { fontSize: 17, fontWeight: "700", letterSpacing: 0.2 },
  center:  { flex: 1, alignItems: "center", justifyContent: "center", padding: 32 },
  muted:   { fontSize: 14 },
  empty:   { fontSize: 18, fontWeight: "700", marginTop: 14 },
  retryBtn:{ marginTop: 18, paddingHorizontal: 22, paddingVertical: 10, borderRadius: 10, borderWidth: 1 },

  card:    {
    borderRadius: 14, borderWidth: 1, padding: 14,
  },
  cardTop: { flexDirection: "row", alignItems: "center", gap: 14 },
  scoreBadge: {
    width: 64, height: 64, borderRadius: 14, borderWidth: 1.5,
    alignItems: "center", justifyContent: "center",
  },
  scoreText: { fontSize: 22, fontWeight: "800", lineHeight: 24 },
  gradeText: { fontSize: 11, fontWeight: "700", letterSpacing: 1, marginTop: 2 },

  cardMeta:  { flex: 1, minWidth: 0 },
  kindLabel: { fontSize: 11, fontWeight: "600", letterSpacing: 0.4, textTransform: "uppercase" },
  propName:  { fontSize: 16, fontWeight: "700", marginTop: 2 },
  subMeta:   { fontSize: 12, marginTop: 4 },

  btnRow:    { flexDirection: "row", gap: 10, marginTop: 14 },
  actionBtn: {
    flex: 1, flexDirection: "row", alignItems: "center", justifyContent: "center",
    gap: 8, paddingVertical: 11, borderRadius: 10, borderWidth: 1,
  },
  actionText:{ fontSize: 14, fontWeight: "700" },

  footer:  { textAlign: "center", fontSize: 11, marginTop: 24, letterSpacing: 0.4 },
});
