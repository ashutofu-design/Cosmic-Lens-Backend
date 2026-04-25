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
import { useT } from "@/hooks/useT";
import { API_BASE, apiFetch } from "@/lib/apiConfig";

const F = {
  regular:  "Nunito_400Regular",
  semibold: "Nunito_600SemiBold",
  bold:     "Nunito_700Bold",
} as const;

export default function DeleteAccountScreen() {
  const C = useC();
  const t = useT();
  const { user, logout } = useUser();

  const [confirmText, setConfirmText] = useState("");
  const [loading, setLoading] = useState(false);

  const canDelete = confirmText.trim().toUpperCase() === "DELETE" && !loading;

  async function handleDelete() {
    if (!user?.id || !user?.api_key) {
      Alert.alert(t.da_alertNotSignedIn, t.da_alertLoginFirst);
      return;
    }
    Alert.alert(
      t.da_alertConfirmTtl,
      t.da_alertConfirmMsg,
      [
        { text: t.da_alertCancel, style: "cancel" },
        {
          text: t.da_alertYesDelete,
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
              logout();
              Alert.alert(
                t.da_alertDeletedTtl,
                t.da_alertDeletedMsg,
                [{ text: t.da_alertOk, onPress: () => router.replace("/login") }]
              );
            } catch (e: any) {
              Alert.alert(t.da_alertFailedTtl, e?.message || t.da_alertFailedMsg);
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
      title={t.da_title}
      subtitle={t.da_subtitle}
    >
      <Callout tone="danger">
        <Strong>{t.da_calloutDanger}</Strong>
      </Callout>

      <Section title={t.da_secWhatHappens}>
        <Bullet>{t.da_wb1}</Bullet>
        <Bullet>{t.da_wb2}</Bullet>
        <Bullet>{t.da_wb3}</Bullet>
        <Bullet>{t.da_wb4}</Bullet>
        <Bullet>{t.da_wb5}</Bullet>
      </Section>

      <Section title={t.da_secBefore}>
        <P>{t.da_pBefore}</P>
        <Bullet>{t.da_bb1}</Bullet>
        <Bullet>{t.da_bb2}</Bullet>
        <Bullet>{t.da_bb3}</Bullet>
        <Bullet>{t.da_bb4}</Bullet>
      </Section>

      <Section title={t.da_secConfirm}>
        <P>{t.da_pConfirm}</P>

        <View style={[da.inputWrap, { backgroundColor: C.bgCard, borderColor: C.border }]}>
          <Feather name="trash-2" size={15} color="#ef4444" />
          <TextInput
            value={confirmText}
            onChangeText={setConfirmText}
            placeholder={t.da_inputPh}
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
              {loading ? t.da_btnDeleting : t.da_btnDelete}
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
          <Text style={[da.cancelText, { color: C.textMid }]}>{t.da_btnCancelBack}</Text>
        </Pressable>
      </Section>

      <Section title={t.da_secNeedHelp}>
        <P>{t.da_pNeedHelp}</P>
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
