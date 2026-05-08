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
import {
  deleteLocalReport,
  listLocalReports,
  openLocalReport,
  shareLocalReport,
  type LocalReport,
} from "@/lib/localReports";

export default function MyReportsScreen() {
  const insets = useSafeAreaInsets();
  const C = useC();
  const t = useT();

  const [localItems, setLocal]  = useState<LocalReport[]>([]);
  const [loading, setLoading]   = useState(false);
  const [refreshing, setRefresh]= useState(false);

  const loadLocal = useCallback(async (silent = false) => {
    if (!silent) setLoading(true);
    try { setLocal(await listLocalReports()); } catch { setLocal([]); }
    finally { setLoading(false); setRefresh(false); }
  }, []);

  useFocusEffect(useCallback(() => { loadLocal(); }, [loadLocal]));

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

      {loading && localItems.length === 0 ? (
        <View style={s.center}>
          <ActivityIndicator size="large" color={C.accent || "#f6c453"} />
          <Text style={[s.muted, { color: C.textMuted, marginTop: 12 }]}>
            {t.mr_loading}
          </Text>
        </View>
      ) : localItems.length === 0 ? (
        <View style={s.center}>
          <Feather name="inbox" size={48} color={C.textMuted} />
          <Text style={[s.empty, { color: C.text }]}>{t.mr_emptyTitle}</Text>
          <Text style={[s.muted, { color: C.textMuted, textAlign: "center", marginTop: 6 }]}>
            Aapke saare generated PDF reports — Kundli Milan, Numerology, AstroVastu Pro, Business Vastu — yahan automatically save honge.
          </Text>
        </View>
      ) : (
        <FlatList
          data={localItems}
          keyExtractor={(r) => r.id}
          renderItem={({ item }) => renderLocalCard(item)}
          contentContainerStyle={{ padding: 16, paddingBottom: insets.bottom + 32 }}
          ItemSeparatorComponent={() => <View style={{ height: 0 }} />}
          ListHeaderComponent={
            <Text style={[s.kindLabel, { color: C.textMuted, marginBottom: 10, letterSpacing: 1 }]}>
              SAVED ON THIS DEVICE · {localItems.length}
            </Text>
          }
          refreshControl={
            <RefreshControl
              refreshing={refreshing}
              onRefresh={() => { setRefresh(true); loadLocal(true); }}
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
