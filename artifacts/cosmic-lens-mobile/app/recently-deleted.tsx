import { Feather } from "@expo/vector-icons";
import * as Haptics from "expo-haptics";
import { router, Stack } from "expo-router";
import React, { useCallback, useEffect, useState } from "react";
import {
  ActivityIndicator,
  Alert,
  Pressable,
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { useC } from "@/context/ThemeContext";
import { useUser } from "@/context/UserContext";
import { API_BASE } from "@/lib/apiConfig";

const F = {
  bold: "Inter_700Bold",
  semi: "Inter_600SemiBold",
  medium: "Inter_500Medium",
  regular: "Inter_400Regular",
};

interface DeletedProfile {
  id: string;
  name: string;
  gender?: string;
  relation?: string;
  deletedAt?: string | null;
  birthData?: { day: number; month: number; year: number; place: string } | null;
}

function timeAgo(iso?: string | null): string {
  if (!iso) return "";
  const ms = Date.now() - new Date(iso).getTime();
  if (Number.isNaN(ms)) return "";
  const mins = Math.floor(ms / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

function hoursLeft(iso?: string | null): number {
  if (!iso) return 0;
  const elapsedMs = Date.now() - new Date(iso).getTime();
  const remainingMs = 24 * 3600 * 1000 - elapsedMs;
  return Math.max(0, Math.ceil(remainingMs / 3600000));
}

export default function RecentlyDeletedScreen() {
  const C = useC();
  const insets = useSafeAreaInsets();
  const { user, refreshUser } = useUser();

  const [items, setItems] = useState<DeletedProfile[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [restoringId, setRestoringId] = useState<string | null>(null);
  const [error, setError] = useState("");

  const ac = C.isDark ? "#f59e0b" : "#7C3AED";

  const fetchDeleted = useCallback(async () => {
    if (!user?.id || !user?.api_key) {
      setLoading(false);
      return;
    }
    setError("");
    try {
      const r = await fetch(`${API_BASE}/api/user/${user.id}/profiles/deleted`, {
        headers: { "X-API-Key": user.api_key },
      });
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const data = await r.json();
      setItems(data?.profiles ?? []);
    } catch (e: any) {
      setError("Couldn't load. Pull to retry.");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [user?.id, user?.api_key]);

  useEffect(() => {
    fetchDeleted();
  }, [fetchDeleted]);

  const onRefresh = useCallback(() => {
    setRefreshing(true);
    fetchDeleted();
  }, [fetchDeleted]);

  async function handleRestore(p: DeletedProfile) {
    if (!user?.id || !user?.api_key) return;
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    setRestoringId(p.id);
    try {
      const r = await fetch(
        `${API_BASE}/api/user/${user.id}/profiles/${p.id}/restore`,
        {
          method: "POST",
          headers: { "X-API-Key": user.api_key },
        },
      );
      const data = await r.json();
      if (!r.ok || !data?.ok) {
        Alert.alert("Restore failed", data?.error ?? "Try again later.");
        setRestoringId(null);
        return;
      }
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      setItems(prev => prev.filter(x => x.id !== p.id));
      setRestoringId(null);
      // Sync UserContext so restored profile reappears in Profile Edit
      // and isn't re-soft-deleted by the next local-vs-cloud reconcile.
      try { await refreshUser(); } catch {}
    } catch {
      Alert.alert("Restore failed", "Check your internet and try again.");
      setRestoringId(null);
    }
  }

  return (
    <View style={{ flex: 1, backgroundColor: C.bg }}>
      <Stack.Screen options={{ headerShown: false }} />

      {/* Header */}
      <View
        style={{
          paddingTop: insets.top + 8,
          paddingBottom: 14,
          paddingHorizontal: 16,
          flexDirection: "row",
          alignItems: "center",
          gap: 12,
          borderBottomWidth: 1,
          borderBottomColor: C.isDark ? C.border2 : "#E5E7EB",
        }}
      >
        <Pressable
          onPress={() => router.back()}
          hitSlop={12}
          style={{
            width: 36,
            height: 36,
            borderRadius: 18,
            backgroundColor: C.isDark ? C.bgCard : "#F3F4F6",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <Feather name="arrow-left" size={18} color={C.text} />
        </Pressable>
        <View style={{ flex: 1 }}>
          <Text style={{ color: C.text, fontSize: 17, fontFamily: F.bold }}>
            Recently Deleted
          </Text>
          <Text style={{ color: C.textMuted, fontSize: 11.5, fontFamily: F.medium, marginTop: 2 }}>
            Restore within 24 hours
          </Text>
        </View>
      </View>

      {loading ? (
        <View style={{ flex: 1, alignItems: "center", justifyContent: "center" }}>
          <ActivityIndicator color={ac} />
        </View>
      ) : (
        <ScrollView
          contentContainerStyle={{ padding: 16, paddingBottom: insets.bottom + 32, gap: 10 }}
          refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={ac} />}
        >
          {error ? (
            <Text style={{ color: "#ef4444", fontSize: 13, fontFamily: F.medium, textAlign: "center", marginBottom: 8 }}>
              {error}
            </Text>
          ) : null}

          {items.length === 0 && !error ? (
            <View style={{ alignItems: "center", paddingVertical: 60, gap: 12 }}>
              <View
                style={{
                  width: 64,
                  height: 64,
                  borderRadius: 32,
                  backgroundColor: `${ac}15`,
                  alignItems: "center",
                  justifyContent: "center",
                }}
              >
                <Feather name="trash-2" size={26} color={ac} />
              </View>
              <Text style={{ color: C.text, fontSize: 16, fontFamily: F.bold }}>
                Nothing here
              </Text>
              <Text
                style={{
                  color: C.textMuted,
                  fontSize: 12.5,
                  fontFamily: F.medium,
                  textAlign: "center",
                  lineHeight: 19,
                  paddingHorizontal: 32,
                }}
              >
                Deleted profiles appear here{"\n"}for 24 hours before being permanently removed.
              </Text>
            </View>
          ) : null}

          {items.map(p => {
            const remaining = hoursLeft(p.deletedAt);
            const dob = p.birthData
              ? `${p.birthData.day}/${p.birthData.month}/${p.birthData.year}`
              : "";
            const isRestoring = restoringId === p.id;
            return (
              <View
                key={p.id}
                style={[
                  s.card,
                  {
                    backgroundColor: C.isDark ? C.bgCard : "#FFFFFF",
                    borderColor: C.isDark ? C.border2 : "#E5E7EB",
                  },
                ]}
              >
                <View style={{ flex: 1, gap: 4 }}>
                  <Text style={{ color: C.text, fontSize: 15, fontFamily: F.bold }} numberOfLines={1}>
                    {p.name || "Unnamed"}
                  </Text>
                  <Text style={{ color: C.textMuted, fontSize: 11.5, fontFamily: F.medium }} numberOfLines={1}>
                    {p.relation ? `${p.relation} · ` : ""}
                    {dob}
                    {p.birthData?.place ? ` · ${p.birthData.place}` : ""}
                  </Text>
                  <View style={{ flexDirection: "row", alignItems: "center", gap: 6, marginTop: 2 }}>
                    <Feather name="clock" size={11} color={C.textMuted} />
                    <Text style={{ color: C.textMuted, fontSize: 10.5, fontFamily: F.medium }}>
                      Deleted {timeAgo(p.deletedAt)} · {remaining}h left
                    </Text>
                  </View>
                </View>
                <Pressable
                  onPress={() => handleRestore(p)}
                  disabled={isRestoring}
                  style={({ pressed }) => [
                    {
                      paddingHorizontal: 14,
                      paddingVertical: 9,
                      borderRadius: 10,
                      backgroundColor: ac,
                      opacity: isRestoring ? 0.6 : pressed ? 0.85 : 1,
                      flexDirection: "row",
                      alignItems: "center",
                      gap: 6,
                    },
                  ]}
                >
                  {isRestoring ? (
                    <ActivityIndicator size="small" color="#fff" />
                  ) : (
                    <Feather name="rotate-ccw" size={13} color="#fff" />
                  )}
                  <Text style={{ color: "#fff", fontSize: 12.5, fontFamily: F.bold }}>
                    Restore
                  </Text>
                </Pressable>
              </View>
            );
          })}
        </ScrollView>
      )}
    </View>
  );
}

const s = StyleSheet.create({
  card: {
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
    padding: 12,
    borderRadius: 14,
    borderWidth: 1,
  },
});
