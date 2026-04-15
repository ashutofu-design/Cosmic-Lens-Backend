import { Feather } from "@expo/vector-icons";
import { LinearGradient } from "expo-linear-gradient";
import * as Haptics from "expo-haptics";
import { router } from "expo-router";
import React, { useState } from "react";
import {
  Alert, Platform, Pressable, ScrollView,
  StyleSheet, Text, View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { CosmicBg } from "@/components/CosmicBg";
import { useC } from "@/context/ThemeContext";
import { useUser, type ProfileEntry } from "@/context/UserContext";

const F = {
  regular:  "Nunito_400Regular",
  medium:   "Nunito_500Medium",
  semibold: "Nunito_600SemiBold",
  bold:     "Nunito_700Bold",
};

export default function MyKundliScreen() {
  const insets = useSafeAreaInsets();
  const C = useC();
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
          <Feather name="arrow-left" size={18} color={C.text} />
        </Pressable>
        <View style={{ flex: 1 }}>
          <Text style={[s.pageTitle, { color: C.text }]}>My Kundli</Text>
          <Text style={{ color: C.textMuted, fontSize: 11, fontFamily: F.medium }}>{kundliProfiles.length} kundli saved</Text>
        </View>
      </View>

      <ScrollView
        contentContainerStyle={{ paddingHorizontal: 16, paddingBottom: botPad + 90, gap: 12 }}
        showsVerticalScrollIndicator={false}
      >
        {kundliProfiles.length === 0 && (
          <View style={[s.emptyCard, { backgroundColor: C.bgCard, borderColor: C.border }]}>
            <Text style={{ fontSize: 36 }}>📜</Text>
            <Text style={{ color: C.text, fontSize: 15, fontFamily: F.semibold, textAlign: "center" }}>No Kundli Yet</Text>
            <Text style={{ color: C.textMuted, fontSize: 12, fontFamily: F.medium, textAlign: "center", lineHeight: 18 }}>
              Add a profile with birth details to generate your first kundli
            </Text>
            <Pressable
              onPress={() => { Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light); router.push("/profile-edit"); }}
              style={({ pressed }) => [s.addBtnEmpty, { backgroundColor: C.isDark ? "rgba(245,158,11,0.12)" : "rgba(124,58,237,0.08)", borderColor: C.isDark ? "rgba(245,158,11,0.25)" : "rgba(124,58,237,0.2)", opacity: pressed ? 0.8 : 1 }]}
            >
              <Feather name="plus" size={14} color={C.isDark ? "#f59e0b" : "#7C3AED"} />
              <Text style={{ color: C.isDark ? "#f59e0b" : "#7C3AED", fontSize: 13, fontFamily: F.semibold }}>Add New Kundli</Text>
            </Pressable>
          </View>
        )}

        {kundliProfiles.map((profile) => {
          const k = profile.kundli!;
          const isPrimary = profile.id === primaryProfileId;
          return (
            <View
              key={profile.id}
              style={[s.card, { backgroundColor: C.bgCard, borderColor: isPrimary ? (C.isDark ? "rgba(245,158,11,0.25)" : "rgba(124,58,237,0.2)") : C.border }]}
            >
              <View style={s.cardHeader}>
                <LinearGradient
                  colors={C.isDark ? ["#0ea5e9","#f59e0b"] : ["#7C3AED","#6D28D9"]}
                  style={s.avatar}
                >
                  <Text style={s.avatarText}>
                    {profile.name.split(" ").map(w => w[0] ?? "").join("").slice(0, 2).toUpperCase()}
                  </Text>
                </LinearGradient>

                <View style={{ flex: 1 }}>
                  <View style={{ flexDirection: "row", alignItems: "center", gap: 6 }}>
                    <Text style={{ color: C.text, fontSize: 14.5, fontFamily: F.bold }} numberOfLines={1}>{profile.name}</Text>
                    {isPrimary && (
                      <View style={[s.primaryBadge, { backgroundColor: "#16a34a" }]}>
                        <Feather name="check-circle" size={8} color="#fff" />
                        <Text style={{ color: "#fff", fontSize: 8, fontFamily: F.bold, letterSpacing: 0.8 }}>PRIMARY</Text>
                      </View>
                    )}
                  </View>
                  {profile.relation && profile.relation !== "Self" && (
                    <Text style={{ color: C.textMuted, fontSize: 10.5, fontFamily: F.medium, marginTop: 1 }}>{profile.relation}</Text>
                  )}
                </View>
                {!isPrimary && (
                  <Pressable
                    onPress={() => { Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium); setPrimaryProfile(profile.id); }}
                    hitSlop={6}
                    style={({ pressed }) => [s.makePrimaryBtn, {
                      borderColor: C.isDark ? "rgba(255,255,255,0.12)" : "rgba(0,0,0,0.12)",
                      backgroundColor: C.isDark ? "rgba(255,255,255,0.04)" : "rgba(0,0,0,0.03)",
                      opacity: pressed ? 0.6 : 1,
                    }]}
                  >
                    <Feather name="arrow-up-circle" size={10} color={C.textMuted} />
                    <Text style={{ color: C.textMuted, fontSize: 9, fontFamily: F.semibold, letterSpacing: 0.2 }}>Set as Primary</Text>
                  </Pressable>
                )}
              </View>

              <View style={[s.infoStrip, { backgroundColor: C.isDark ? "rgba(255,255,255,0.03)" : C.bgCard2, borderColor: C.border }]}>
                {[
                  { label: "Rashi", value: k.moonSign ?? "—" },
                  { label: "Nakshatra", value: k.nakshatra ?? "—" },
                  { label: "Lagna", value: k.ascendant ?? "—" },
                ].map((item, i) => (
                  <React.Fragment key={i}>
                    {i > 0 && <View style={{ width: 1, height: 20, backgroundColor: C.border }} />}
                    <View style={{ flex: 1, alignItems: "center" }}>
                      <Text style={{ color: C.textDim, fontSize: 8.5, fontFamily: F.bold, letterSpacing: 0.8 }}>{item.label.toUpperCase()}</Text>
                      <Text style={{ color: C.text, fontSize: 11.5, fontFamily: F.semibold, marginTop: 1 }} numberOfLines={1}>{item.value}</Text>
                    </View>
                  </React.Fragment>
                ))}
              </View>

              <View style={s.actionRow}>
                <Pressable
                  onPress={() => handleView(profile.id)}
                  style={({ pressed }) => [s.actionBtn, { backgroundColor: C.isDark ? "rgba(245,158,11,0.08)" : "rgba(124,58,237,0.06)", borderColor: C.isDark ? "rgba(245,158,11,0.2)" : "rgba(124,58,237,0.15)", opacity: pressed ? 0.7 : 1 }]}
                >
                  <Feather name="eye" size={13} color={C.isDark ? "#f59e0b" : "#7C3AED"} />
                  <Text style={{ color: C.isDark ? "#f59e0b" : "#7C3AED", fontSize: 11, fontFamily: F.semibold }}>View</Text>
                </Pressable>

                <Pressable
                  onPress={() => handleEdit(profile.id)}
                  style={({ pressed }) => [s.actionBtn, { backgroundColor: C.isDark ? "rgba(255,255,255,0.03)" : C.bgCard2, borderColor: C.border, opacity: pressed ? 0.7 : 1 }]}
                >
                  <Feather name="edit-2" size={13} color={C.textMuted} />
                  <Text style={{ color: C.textMuted, fontSize: 11, fontFamily: F.semibold }}>Edit</Text>
                </Pressable>

                <Pressable
                  onPress={() => handleDelete(profile.id)}
                  style={({ pressed }) => [s.actionBtn, { backgroundColor: "rgba(239,68,68,0.06)", borderColor: "rgba(239,68,68,0.15)", opacity: pressed ? 0.7 : 1 }]}
                >
                  <Feather name="trash-2" size={13} color="#EF4444" />
                  <Text style={{ color: "#EF4444", fontSize: 11, fontFamily: F.semibold }}>Delete</Text>
                </Pressable>
              </View>
            </View>
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
            <Text style={{ color: C.isDark ? "#f59e0b" : "#7C3AED", fontSize: 13, fontFamily: F.semibold }}>Add New Kundli</Text>
          </Pressable>
        )}
      </ScrollView>

      {confirmDeleteId && deleteTarget && (
        <View style={s.overlay}>
          <View style={[s.modal, { backgroundColor: C.bgCard, borderColor: C.border }]}>
            <View style={s.modalIcon}>
              <Feather name="alert-triangle" size={22} color="#EF4444" />
            </View>
            <Text style={{ color: C.text, fontSize: 16, fontFamily: F.bold, textAlign: "center" }}>Delete Kundli?</Text>
            <Text style={{ color: C.textMuted, fontSize: 12, fontFamily: F.medium, textAlign: "center", lineHeight: 18 }}>
              {deleteTarget.name} ki kundli permanently delete ho jayegi. Yeh action undo nahi hoga.
            </Text>
            <View style={{ flexDirection: "row", gap: 12, marginTop: 6 }}>
              <Pressable
                onPress={() => setConfirmDeleteId(null)}
                style={[s.modalBtn, { backgroundColor: C.bgCard2, borderColor: C.border }]}
              >
                <Text style={{ color: C.textMuted, fontSize: 13, fontFamily: F.semibold }}>Cancel</Text>
              </Pressable>
              <Pressable
                onPress={confirmDel}
                style={[s.modalBtn, { backgroundColor: "#EF4444", borderColor: "#EF4444" }]}
              >
                <Text style={{ color: "#fff", fontSize: 13, fontFamily: F.bold }}>Delete</Text>
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
    borderRadius: 16, borderWidth: 1, overflow: "hidden",
    padding: 14, gap: 12,
  },
  cardHeader: {
    flexDirection: "row", alignItems: "center", gap: 12,
  },
  avatar: {
    width: 42, height: 42, borderRadius: 21,
    alignItems: "center", justifyContent: "center",
  },
  avatarText: {
    color: "#fff", fontSize: 15, fontFamily: F.bold,
  },
  primaryBadge: {
    flexDirection: "row", alignItems: "center", gap: 3,
    paddingVertical: 2, paddingHorizontal: 7, borderRadius: 6,
  },
  makePrimaryBtn: {
    flexDirection: "row", alignItems: "center", gap: 4,
    paddingVertical: 5, paddingHorizontal: 8,
    borderRadius: 8, borderWidth: 1,
  },
  infoStrip: {
    flexDirection: "row", alignItems: "center",
    borderRadius: 10, borderWidth: 1, paddingVertical: 8, paddingHorizontal: 4,
  },
  actionRow: {
    flexDirection: "row", gap: 8,
  },
  actionBtn: {
    flex: 1, flexDirection: "row", alignItems: "center", justifyContent: "center",
    gap: 5, paddingVertical: 9, borderRadius: 10, borderWidth: 1,
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
