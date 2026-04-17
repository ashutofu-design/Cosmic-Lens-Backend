import { Feather } from "@expo/vector-icons";
import * as Haptics from "expo-haptics";
import { LinearGradient } from "expo-linear-gradient";
import { router } from "expo-router";
import React, { useState } from "react";
import {
  ActivityIndicator,
  Alert,
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";
import LegalScreen, { Section, P, Bullet, Strong, Callout } from "@/components/LegalScreen";
import { useC } from "@/context/ThemeContext";
import { useUser } from "@/context/UserContext";
import { API_BASE, apiFetch } from "@/lib/apiConfig";

const F = {
  regular:  "Nunito_400Regular",
  semibold: "Nunito_600SemiBold",
  bold:     "Nunito_700Bold",
} as const;

export default function DeleteAccountScreen() {
  const C = useC();
  const { user, logout } = useUser();

  const [confirmText, setConfirmText] = useState("");
  const [loading, setLoading] = useState(false);

  const canDelete = confirmText.trim().toUpperCase() === "DELETE" && !loading;

  async function handleDelete() {
    if (!user?.id || !user?.api_key) {
      Alert.alert("Not signed in", "Please log in first.");
      return;
    }
    Alert.alert(
      "Delete account permanently?",
      "This action cannot be undone. All your kundlis, profiles, chat history and personal data will be erased within 30 days.",
      [
        { text: "Cancel", style: "cancel" },
        {
          text: "Yes, delete forever",
          style: "destructive",
          onPress: async () => {
            try { Haptics.notificationAsync(Haptics.NotificationFeedbackType.Warning); } catch {}
            setLoading(true);
            try {
              const r = await apiFetch(`${API_BASE}/api/user/${user.id}/delete`, {
                method: "POST",
                headers: { "X-API-Key": user.api_key },
                body: JSON.stringify({ confirm: "DELETE" }),
              });
              const data = await r.json().catch(() => ({}));
              if (!r.ok || !data.ok) {
                throw new Error(data?.error || `Server returned ${r.status}`);
              }
              // Wipe ALL local AsyncStorage (profiles, kundli, language, etc.)
              // — not just the user record — so nothing can be re-uploaded
              // by cloud sync if the device is later signed into another
              // account.
              logout();
              Alert.alert(
                "Account Deleted",
                "Your account has been permanently deleted. Thank you for using Cosmic Lens.",
                [{ text: "OK", onPress: () => router.replace("/login") }]
              );
            } catch (e: any) {
              Alert.alert("Deletion failed", e?.message || "Please try again or contact support.");
            } finally {
              setLoading(false);
            }
          },
        },
      ]
    );
  }

  return (
    <LegalScreen
      title="Delete Account"
      subtitle="Permanent and irreversible"
    >
      <Callout tone="danger">
        <Strong>This action is permanent.</Strong> Once deleted, your data
        cannot be recovered.
      </Callout>

      <Section title="What happens when you delete">
        <Bullet>Your account login (email / mobile / Google) is removed immediately.</Bullet>
        <Bullet>All saved kundlis, profiles, and chat history are erased within 30 days.</Bullet>
        <Bullet>Active subscriptions are cancelled — no further charges.</Bullet>
        <Bullet>Tax invoices for past payments may be retained for 7 years per Indian law (GST records).</Bullet>
        <Bullet>You will need to create a new account if you wish to use Cosmic Lens again.</Bullet>
      </Section>

      <Section title="Before you delete">
        <P>
          Consider these alternatives — they may solve your concern without
          losing your data:
        </P>
        <Bullet><Strong>Cancel subscription only</Strong> — Profile → Subscription → Cancel. Your account stays free.</Bullet>
        <Bullet><Strong>Disable notifications</Strong> — Profile → Notifications → Off.</Bullet>
        <Bullet><Strong>Need a refund?</Strong> See our Refund Policy first — we may help.</Bullet>
        <Bullet><Strong>Privacy concern?</Strong> Email <Strong>support@cosmiclens.app</Strong>.</Bullet>
      </Section>

      <Section title="Confirm deletion">
        <P>
          To proceed, type <Strong>DELETE</Strong> in the box below and tap the
          delete button.
        </P>

        <View style={[da.inputWrap, { backgroundColor: C.bgCard, borderColor: C.border }]}>
          <Feather name="trash-2" size={15} color="#ef4444" />
          <TextInput
            value={confirmText}
            onChangeText={setConfirmText}
            placeholder="Type DELETE to confirm"
            placeholderTextColor={C.textMuted}
            autoCapitalize="characters"
            autoCorrect={false}
            style={[da.input, { color: C.text }]}
            editable={!loading}
          />
        </View>

        <Pressable
          onPress={handleDelete}
          disabled={!canDelete}
          style={({ pressed }) => [{ opacity: !canDelete || pressed ? 0.55 : 1, marginTop: 4 }]}
        >
          <LinearGradient
            colors={canDelete ? ["#dc2626", "#ef4444"] : ["#525252", "#737373"]}
            start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }}
            style={da.deleteBtn}
          >
            {loading
              ? <ActivityIndicator size="small" color="#fff" />
              : <Feather name="trash-2" size={15} color="#fff" />}
            <Text style={da.deleteBtnText}>
              {loading ? "Deleting…" : "Delete My Account Permanently"}
            </Text>
          </LinearGradient>
        </Pressable>

        <Pressable
          onPress={() => router.back()}
          style={({ pressed }) => [
            da.cancelBtn,
            { borderColor: C.border, opacity: pressed ? 0.85 : 1 },
          ]}
        >
          <Text style={[da.cancelText, { color: C.textMid }]}>Cancel and go back</Text>
        </Pressable>
      </Section>

      <Section title="Need help instead?">
        <P>
          If you have any concern, we&apos;d love to hear from you before you
          go. Reach us at <Strong>support@cosmiclens.app</Strong> — most issues
          are resolved within 24 hours.
        </P>
      </Section>
    </LegalScreen>
  );
}

const da = StyleSheet.create({
  inputWrap: {
    flexDirection: "row", alignItems: "center", gap: 10,
    paddingVertical: 12, paddingHorizontal: 14,
    borderRadius: 12, borderWidth: 1.5,
  },
  input: {
    flex: 1, fontSize: 14, fontFamily: F.semibold,
    letterSpacing: 1.5,
  },
  deleteBtn: {
    flexDirection: "row", alignItems: "center", justifyContent: "center",
    gap: 8, paddingVertical: 14, borderRadius: 12,
  },
  deleteBtnText: {
    color: "#fff", fontSize: 14, fontFamily: F.bold,
  },
  cancelBtn: {
    paddingVertical: 12, borderRadius: 12,
    borderWidth: 1, alignItems: "center", marginTop: 8,
  },
  cancelText: { fontSize: 13, fontFamily: F.semibold },
});
