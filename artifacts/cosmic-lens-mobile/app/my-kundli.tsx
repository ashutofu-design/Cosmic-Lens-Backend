import { Feather } from "@expo/vector-icons";
import { LinearGradient } from "expo-linear-gradient";
import * as Haptics from "expo-haptics";
import { router } from "expo-router";
import React, { useState } from "react";
import {
  Alert,
  I18nManager,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { CosmicBg } from "@/components/CosmicBg";
import { useC } from "@/context/ThemeContext";
import { useT } from "@/hooks/useT";
import { useUser, type ProfileEntry } from "@/context/UserContext";
import { relationLabel } from "./profile-edit";

const F = {
  regular:  "Nunito_400Regular",
  medium:   "Nunito_500Medium",
  semibold: "Nunito_600SemiBold",
  bold:     "Nunito_700Bold",
};

export default function MyKundliScreen() {
  const insets = useSafeAreaInsets();
  const C = useC();
  const t = useT();
  const { profiles, primaryProfileId, deleteProfile, setPrimaryProfile } = useUser();
  const topPad = Platform.OS === "web" ? 67 : insets.top;
  const botPad = Platform.OS === "web" ? 34 : insets.bottom;

  const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null);
  const deleteTarget = confirmDeleteId ? profiles.find(p => p.id === confirmDeleteId) : null;

  const kundliProfiles = profiles.filter(p => p.kundli);

  function handleDelete(id: string) {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    setConfirmDeleteId(id);
  }

  function confirmDel() {
    if (!confirmDeleteId) return;
    deleteProfile(confirmDeleteId);
    setConfirmDeleteId(null);
    Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
  }

  function handleView(profileId: string) {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    if (profileId !== primaryProfileId) {
      setPrimaryProfile(profileId);
    }
    router.push("/(tabs)/kundli");
  }

  function handleEdit(profileId: string) {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    router.push("/profile-edit");
  }

  return (
    <CosmicBg>
      <View style={{ paddingTop: topPad + 8, paddingHorizontal: 16, paddingBottom: 12, flexDirection: "row", alignItems: "center", gap: 12 }}>
        <Pressable
          onPress={() => { Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light); router.back(); }}
          style={[s.backBtn, { backgroundColor: C.bgCard, borderColor: C.border }]}
        >
          <Feather name={I18nManager.isRTL ? "arrow-right" : "arrow-left"} size={18} color={C.text} />
        </Pressable>
        <View style={{ flex: 1 }}>
          <Text style={[s.pageTitle, { color: C.text }]}>{t.myKundliTitle}</Text>
          <Text style={{ color: C.textMuted, fontSize: 11, fontFamily: F.medium }}>{kundliProfiles.length} {t.mk_savedCount}</Text>
        </View>
      </View>

      <ScrollView
        contentContainerStyle={{ paddingHorizontal: 16, paddingBottom: botPad + 90, gap: 12 }}
        showsVerticalScrollIndicator={false}
      >
        {kundliProfiles.length === 0 && (
          <View style={[s.emptyCard, { backgroundColor: C.bgCard, borderColor: C.border }]}>
            <Text style={{ fontSize: 36 }}>📜</Text>
            <Text style={{ color: C.text, fontSize: 15, fontFamily: F.semibold, textAlign: "center" }}>{t.mk_emptyTitle}</Text>
            <Text style={{ color: C.textMuted, fontSize: 12, fontFamily: F.medium, textAlign: "center", lineHeight: 18 }}>
              {t.mk_emptyDesc}
            </Text>
            <Pressable
              onPress={() => { Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light); router.push("/profile-edit"); }}
              style={({ pressed }) => [s.addBtnEmpty, { backgroundColor: C.isDark ? "rgba(245,158,11,0.12)" : "rgba(124,58,237,0.08)", borderColor: C.isDark ? "rgba(245,158,11,0.25)" : "rgba(124,58,237,0.2)", opacity: pressed ? 0.8 : 1 }]}
            >
              <Feather name="plus" size={14} color={C.isDark ? "#f59e0b" : "#7C3AED"} />
              <Text style={{ color: C.isDark ? "#f59e0b" : "#7C3AED", fontSize: 13, fontFamily: F.semibold }}>{t.mk_addNew}</Text>
            </Pressable>
          </View>
        )}

        {kundliProfiles.map((profile) => {
          const k = profile.kundli!;
          const isPrimary = profile.id === primaryProfileId;
          const ac = C.isDark ? "#f59e0b" : "#7C3AED";
          const astroLine = [k.moonSign, k.nakshatra, k.ascendant].filter(Boolean).join(" \u2022 ") || "—";
          return (
            <Pressable
              key={profile.id}
              onPress={() => handleView(profile.id)}
              style={({ pressed }) => [s.card, {
                backgroundColor: C.bgCard,
                borderColor: isPrimary ? (C.isDark ? "rgba(245,158,11,0.25)" : "rgba(124,58,237,0.2)") : C.border,
                opacity: pressed ? 0.85 : 1,
              }]}
            >
              <View style={s.cardHeader}>
                <LinearGradient
                  colors={isPrimary ? (C.isDark ? ["#f59e0b","#ef4444"] : ["#7C3AED","#6D28D9"]) : (C.isDark ? ["#0ea5e9","#f59e0b"] : ["#7C3AED","#a78bfa"])}
                  style={s.avatar}
                >
                  <Text style={s.avatarText}>
                    {profile.name.split(" ").map(w => w[0] ?? "").join("").slice(0, 2).toUpperCase()}
                  </Text>
                </LinearGradient>

                <View style={{ flex: 1 }}>
                  <View style={{ flexDirection: "row", alignItems: "center", gap: 6 }}>
                    <Text style={{ color: C.text, fontSize: 13.5, fontFamily: F.bold, flexShrink: 1 }} numberOfLines={1}>{profile.name}</Text>
                    {isPrimary && (
                      <View style={[s.primaryBadge, { backgroundColor: `${ac}15` }]}>
                        <Feather name="star" size={7} color={ac} />
                        <Text style={{ color: ac, fontSize: 7.5, fontFamily: F.bold, letterSpacing: 0.6 }}>{t.mk_primary}</Text>
                      </View>
                    )}
                    {!isPrimary && profile.relation && profile.relation !== "Self" && (
                      <Text style={{ color: C.textDim, fontSize: 9, fontFamily: F.bold, letterSpacing: 0.5, borderWidth: 0.75, borderColor: C.isDark ? "rgba(255,255,255,0.08)" : "rgba(0,0,0,0.08)", borderRadius: 5, paddingHorizontal: 5, paddingVertical: 1 }}>{relationLabel(profile.relation, t)}</Text>
                    )}
                  </View>
                  <Text style={{ color: isPrimary ? (C.isDark ? "rgba(250,204,21,0.8)" : "#7C3AED") : C.textMuted, fontSize: 11.5, fontFamily: F.medium, marginTop: 2 }} numberOfLines={1}>{astroLine}</Text>
                </View>

                <View style={{ flexDirection: "row", alignItems: "center", gap: 4 }}>
                  <Pressable
                    onPress={() => handleEdit(profile.id)}
                    hitSlop={6}
                    style={({ pressed }) => [s.iconBtn, { backgroundColor: C.isDark ? "rgba(255,255,255,0.04)" : "rgba(0,0,0,0.03)", opacity: pressed ? 0.6 : 1 }]}
                  >
                    <Feather name="edit-2" size={12} color={C.textMuted} />
                  </Pressable>
                  <Pressable
                    onPress={() => handleDelete(profile.id)}
                    hitSlop={6}
                    style={({ pressed }) => [s.iconBtn, { backgroundColor: "rgba(239,68,68,0.06)", opacity: pressed ? 0.6 : 1 }]}
                  >
                    <Feather name="trash-2" size={12} color="#EF4444" />
                  </Pressable>
                </View>
              </View>
            </Pressable>
          );
        })}

        {kundliProfiles.length > 0 && (
          <Pressable
            onPress={() => { Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light); router.push("/profile-edit"); }}
            style={({ pressed }) => [s.addBtn, { borderColor: C.isDark ? "rgba(245,158,11,0.2)" : "rgba(124,58,237,0.15)", opacity: pressed ? 0.8 : 1 }]}
          >
            <View style={[s.addCircle, { backgroundColor: C.isDark ? "rgba(245,158,11,0.08)" : "rgba(124,58,237,0.06)", borderColor: C.isDark ? "rgba(245,158,11,0.2)" : "rgba(124,58,237,0.15)" }]}>
              <Feather name="plus" size={16} color={C.isDark ? "#f59e0b" : "#7C3AED"} />
            </View>
            <Text style={{ color: C.isDark ? "#f59e0b" : "#7C3AED", fontSize: 13, fontFamily: F.semibold }}>{t.mk_addNew}</Text>
          </Pressable>
        )}
      </ScrollView>

      {confirmDeleteId && deleteTarget && (
        <View style={s.overlay}>
          <View style={[s.modal, { backgroundColor: C.bgCard, borderColor: C.border }]}>
            <View style={s.modalIcon}>
              <Feather name="alert-triangle" size={22} color="#EF4444" />
            </View>
            <Text style={{ color: C.text, fontSize: 16, fontFamily: F.bold, textAlign: "center" }}>{t.mk_deleteTitle}</Text>
            <Text style={{ color: C.textMuted, fontSize: 12, fontFamily: F.medium, textAlign: "center", lineHeight: 18 }}>
              {deleteTarget.name} — {t.mk_deleteDesc}
            </Text>
            <View style={{ flexDirection: "row", gap: 12, marginTop: 6 }}>
              <Pressable
                onPress={() => setConfirmDeleteId(null)}
                style={[s.modalBtn, { backgroundColor: C.bgCard2, borderColor: C.border }]}
              >
                <Text style={{ color: C.textMuted, fontSize: 13, fontFamily: F.semibold }}>{t.mk_cancel}</Text>
              </Pressable>
              <Pressable
                onPress={confirmDel}
                style={[s.modalBtn, { backgroundColor: "#EF4444", borderColor: "#EF4444" }]}
              >
                <Text style={{ color: "#fff", fontSize: 13, fontFamily: F.bold }}>{t.mk_delete}</Text>
              </Pressable>
            </View>
          </View>
        </View>
      )}
    </CosmicBg>
  );
}

const s = StyleSheet.create({
  backBtn: {
    width: 38, height: 38, borderRadius: 12,
    alignItems: "center", justifyContent: "center",
    borderWidth: 1,
  },
  pageTitle: {
    fontSize: 20, fontFamily: F.bold, letterSpacing: -0.4,
  },
  emptyCard: {
    borderRadius: 16, borderWidth: 1, padding: 32,
    alignItems: "center", gap: 10,
  },
  addBtnEmpty: {
    flexDirection: "row", alignItems: "center", gap: 6,
    paddingVertical: 10, paddingHorizontal: 18,
    borderRadius: 12, borderWidth: 1, marginTop: 6,
  },
  card: {
    borderRadius: 14, borderWidth: 1, overflow: "hidden",
    paddingVertical: 10, paddingHorizontal: 12,
  },
  cardHeader: {
    flexDirection: "row", alignItems: "center", gap: 10,
  },
  avatar: {
    width: 36, height: 36, borderRadius: 18,
    alignItems: "center", justifyContent: "center",
  },
  avatarText: {
    color: "#fff", fontSize: 13, fontFamily: F.bold,
  },
  primaryBadge: {
    flexDirection: "row", alignItems: "center", gap: 3,
    paddingVertical: 2, paddingHorizontal: 6, borderRadius: 6,
  },
  iconBtn: {
    width: 28, height: 28, borderRadius: 8,
    alignItems: "center", justifyContent: "center",
  },
  addBtn: {
    flexDirection: "row", alignItems: "center", gap: 12,
    padding: 14, borderRadius: 14,
    borderWidth: 1, borderStyle: "dashed" as any,
  },
  addCircle: {
    width: 34, height: 34, borderRadius: 17,
    borderWidth: 1, alignItems: "center", justifyContent: "center",
  },
  overlay: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: "rgba(0,0,0,0.7)",
    alignItems: "center", justifyContent: "center",
    zIndex: 999,
  },
  modal: {
    width: "85%" as any, borderRadius: 20, borderWidth: 1,
    padding: 24, alignItems: "center", gap: 10,
  },
  modalIcon: {
    width: 48, height: 48, borderRadius: 24,
    backgroundColor: "rgba(239,68,68,0.1)",
    alignItems: "center", justifyContent: "center",
  },
  modalBtn: {
    flex: 1, alignItems: "center", paddingVertical: 11,
    borderRadius: 12, borderWidth: 1,
  },
});
