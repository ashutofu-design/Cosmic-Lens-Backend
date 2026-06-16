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
import React, { useCallback, useEffect, useState } from "react";
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
import {
  formatLocalReportSize,
  listLocalReports,
  openLocalReport,
  shareLocalReport,
  type LocalReport,
} from "@/lib/localReports";
import { clearServerSyncCache, syncServerReportsForUser } from "@/lib/serverMyReports";
import { subscribeNewReports } from "@/lib/reportAutoSync";

export default function MyReportsScreen() {
  const insets = useSafeAreaInsets();
  const C = useC();
  const t = useT();
  const { user } = useUser();

  const [localItems, setLocal]  = useState<LocalReport[]>([]);
  const [loading, setLoading]   = useState(false);
  const [refreshing, setRefresh]= useState(false);
  const [fetching, setFetching] = useState(false);
  const [fetchHint, setFetchHint] = useState<string | null>(null);

  const loadLocal = useCallback(async (silent = false) => {
    if (!silent) setLoading(true);
    try {
      if (user?.id && user.api_key) {
        await syncServerReportsForUser({ userId: user.id, apiKey: user.api_key });
      }
      setLocal(await listLocalReports());
    } catch { setLocal([]); }
    finally { setLoading(false); setRefresh(false); }
  }, [user?.id, user?.api_key]);

  const fetchFromServer = useCallback(async () => {
    if (!user?.id || !user.api_key) {
      Alert.alert("Login required", "Server se report lene ke liye login karein.");
      return;
    }
    setFetching(true);
    setFetchHint(null);
    try {
      await clearServerSyncCache();
      const result = await syncServerReportsForUser({
        userId: user.id,
        apiKey: user.api_key,
        force: true,
      });
      setLocal(await listLocalReports());
      if (result.added > 0) {
        setFetchHint(`${result.added} report server se fetch ho gayi.`);
        Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      } else if (result.error === "auth") {
        Alert.alert(
          "Fetch nahi hua",
          "Account server se match nahi ho raha. Logout karke dubara login karein, phir Fetch try karein.",
        );
      } else if (result.error === "network" || result.error === "server") {
        Alert.alert(
          "Fetch nahi hua",
          "Server se connect nahi hua. Thodi der baad dubara try karein.",
        );
      } else if (result.error === "already_local" && result.serverCount > 0) {
        setFetchHint(`${result.serverCount} report server pe hain — device pe pehle se saved honi chahiye.`);
      } else {
        setFetchHint("Server pe abhi koi pending report nahi mili.");
      }
    } catch {
      Alert.alert("Fetch nahi hua", "Network error — dubara try karein.");
    } finally {
      setFetching(false);
    }
  }, [user?.id, user?.api_key]);

  useFocusEffect(useCallback(() => { loadLocal(); }, [loadLocal]));

  useEffect(() => {
    return subscribeNewReports((added) => {
      if (added <= 0) return;
      void listLocalReports().then(setLocal);
    });
  }, []);

  const onOpenLocal = async (r: LocalReport) => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    await openLocalReport(r);
  };
  const onShareLocal = async (r: LocalReport) => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    await shareLocalReport(r);
  };
  const KIND_LABEL: Record<LocalReport["kind"], string> = {
    milan:           "Kundli Milan",
    numerology:      "Numerology",
    astrovastu_pro:  "AstroVastu Pro",
    business_vastu:  "Business Vastu",
    face_reading:    "Face Reading",
    love_reality:    "Love Reality Pro",
    other:           "Report",
  };
  const KIND_ICON: Record<LocalReport["kind"], React.ComponentProps<typeof Feather>["name"]> = {
    milan:           "heart",
    numerology:      "hash",
    astrovastu_pro:  "home",
    business_vastu:  "briefcase",
    face_reading:    "user",
    love_reality:    "heart",
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
    const sizeLabel = formatLocalReportSize(r.bytes);
    const metaLine = [date, time, sizeLabel].filter(Boolean).join(" · ");
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
            <View style={s.cardMetaTop}>
              <Text style={[s.kindLabel, { color: C.textMuted, flex: 1 }]} numberOfLines={1}>
                {KIND_LABEL[r.kind]}
              </Text>
              {r.restored ? (
                <View style={[s.restoredBadge, {
                  backgroundColor: C.isDark ? "rgba(16,185,129,0.14)" : "rgba(16,185,129,0.10)",
                  borderColor: C.isDark ? "rgba(16,185,129,0.35)" : "rgba(16,185,129,0.30)",
                }]}>
                  <Feather name="download-cloud" size={10} color="#10b981" />
                  <Text style={s.restoredBadgeTxt}>Restored Report</Text>
                </View>
              ) : null}
            </View>
            <Text style={[s.propName, { color: C.text }]} numberOfLines={2}>
              {r.title}
            </Text>
            <Text style={[s.subMeta, { color: C.textMuted }]} numberOfLines={1}>
              {metaLine}
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
        <Pressable
          onPress={fetchFromServer}
          disabled={fetching}
          style={({ pressed }) => [
            s.fetchHeaderBtn,
            {
              borderColor: C.border,
              backgroundColor: C.isDark ? "#141c28" : "#eef3fb",
              opacity: pressed || fetching ? 0.7 : 1,
            },
          ]}
          hitSlop={8}
        >
          {fetching ? (
            <ActivityIndicator size="small" color={C.accent || "#f6c453"} />
          ) : (
            <Feather name="download-cloud" size={18} color={C.accent || "#f6c453"} />
          )}
        </Pressable>
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
            Report deliver hote hi notification aayegi aur yahan auto-save hogi.
          </Text>
          <Pressable
            onPress={fetchFromServer}
            disabled={fetching}
            style={({ pressed }) => [
              s.fetchMainBtn,
              {
                backgroundColor: C.accent || "#f6c453",
                opacity: pressed || fetching ? 0.85 : 1,
              },
            ]}
          >
            {fetching ? (
              <ActivityIndicator size="small" color="#1a1200" />
            ) : (
              <Feather name="download-cloud" size={18} color="#1a1200" />
            )}
            <Text style={s.fetchMainBtnTxt}>
              {fetching ? "Refreshing…" : "Refresh"}
            </Text>
          </Pressable>
          {fetchHint ? (
            <Text style={[s.fetchHint, { color: C.textMuted }]}>{fetchHint}</Text>
          ) : null}
        </View>
      ) : (
        <FlatList
          data={localItems}
          keyExtractor={(r) => r.id}
          renderItem={({ item }) => renderLocalCard(item)}
          contentContainerStyle={{ padding: 16, paddingBottom: insets.bottom + 32 }}
          ItemSeparatorComponent={() => <View style={{ height: 0 }} />}
          ListHeaderComponent={
            <View style={{ marginBottom: 10 }}>
              <View style={s.listHeaderRow}>
                <Text style={[s.kindLabel, { color: C.textMuted, letterSpacing: 1, flex: 1 }]}>
                  SAVED ON THIS DEVICE · {localItems.length}
                </Text>
                <Pressable
                  onPress={fetchFromServer}
                  disabled={fetching}
                  style={({ pressed }) => [
                    s.fetchInlineBtn,
                    { borderColor: C.border, opacity: pressed || fetching ? 0.75 : 1 },
                  ]}
                >
                  {fetching ? (
                    <ActivityIndicator size="small" color={C.accent || "#f6c453"} />
                  ) : (
                    <Feather name="download-cloud" size={14} color={C.accent || "#f6c453"} />
                  )}
                  <Text style={[s.fetchInlineTxt, { color: C.accent || "#f6c453" }]}>
                    Refresh
                  </Text>
                </Pressable>
              </View>
              {fetchHint ? (
                <Text style={[s.fetchHint, { color: C.textMuted, marginTop: 6 }]}>{fetchHint}</Text>
              ) : null}
            </View>
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
  fetchHeaderBtn: {
    width: 36, height: 36, borderRadius: 10, borderWidth: 1,
    alignItems: "center", justifyContent: "center",
  },
  fetchMainBtn: {
    flexDirection: "row", alignItems: "center", gap: 8,
    marginTop: 20, paddingHorizontal: 20, paddingVertical: 12, borderRadius: 12,
  },
  fetchMainBtnTxt: { fontSize: 15, fontWeight: "700", color: "#1a1200" },
  fetchHint: { fontSize: 13, textAlign: "center", marginTop: 12, lineHeight: 18 },
  listHeaderRow: { flexDirection: "row", alignItems: "center", gap: 10 },
  fetchInlineBtn: {
    flexDirection: "row", alignItems: "center", gap: 5,
    paddingHorizontal: 10, paddingVertical: 6, borderRadius: 999, borderWidth: 1,
  },
  fetchInlineTxt: { fontSize: 12, fontWeight: "700" },
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
  cardMetaTop: { flexDirection: "row", alignItems: "center", gap: 8, marginBottom: 0 },
  restoredBadge: {
    flexDirection: "row", alignItems: "center", gap: 4,
    paddingHorizontal: 8, paddingVertical: 3, borderRadius: 999, borderWidth: 1,
  },
  restoredBadgeTxt: { fontSize: 10, fontWeight: "700", color: "#10b981", letterSpacing: 0.2 },
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
