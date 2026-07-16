import { Feather } from "@expo/vector-icons";
import * as Haptics from "expo-haptics";
import { LinearGradient } from "expo-linear-gradient";
import { router, Stack } from "expo-router";
import React, { useCallback, useEffect, useRef, useState } from "react";
import {
  ActivityIndicator,
  FlatList,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { CosmicBg } from "@/components/CosmicBg";
import { useC } from "@/context/ThemeContext";
import { useUser } from "@/context/UserContext";
import { useT } from "@/hooks/useT";
import { API_BASE, apiFetch } from "@/lib/apiConfig";

type Bubble =
  | { id: string; kind: "assistant-text"; text: string }
  | { id: string; kind: "user-text"; text: string }
  | { id: string; kind: "thinking" };

export default function PrashnaKundliScreen() {
  const insets = useSafeAreaInsets();
  const C = useC();
  const t = useT();
  const { user } = useUser();
  const androidSB = Platform.OS === "android" ? 24 : 0;
  const topPad = Platform.OS === "ios" ? insets.top : androidSB;
  const botPad = Platform.OS === "web" ? 24 : insets.bottom;

  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [bubbles, setBubbles] = useState<Bubble[]>([
    { id: "init", kind: "assistant-text", text: t.pk_initMsg },
  ]);
  const listRef = useRef<FlatList<Bubble>>(null);

  useEffect(() => {
    setBubbles((prev) => {
      if (prev.length === 1 && prev[0].id === "init" && prev[0].kind === "assistant-text") {
        return [{ id: "init", kind: "assistant-text", text: t.pk_initMsg }];
      }
      return prev;
    });
  }, [t.pk_initMsg]);

  useEffect(() => {
    setTimeout(() => listRef.current?.scrollToEnd({ animated: true }), 80);
  }, [bubbles]);

  const submit = useCallback(async () => {
    if (loading) return;
    const q = question.trim();
    if (!q) return;

    setBubbles((prev) => [
      ...prev,
      { id: `u-${Date.now()}`, kind: "user-text", text: q },
      { id: "thinking", kind: "thinking" },
    ]);
    setQuestion("");
    setLoading(true);
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);

    try {
      const headers: Record<string, string> = { "Content-Type": "application/json" };
      if (user?.api_key) headers["X-API-Key"] = user.api_key;
      const res = await apiFetch(`${API_BASE}/api/prashna/simple-ask`, {
        method: "POST",
        headers,
        body: JSON.stringify({
          question: q,
          user_id: user?.id,
          lang: t.vlang === "en" ? "en" : "hn",
        }),
      });
      const rawText = await res.text().catch(() => "");
      let json: any = {};
      try {
        json = rawText ? JSON.parse(rawText) : {};
      } catch {
        json = {};
      }

      if (res.status === 402) {
        setBubbles((prev) =>
          prev.filter((b) => b.id !== "thinking").concat({
            id: Date.now().toString(),
            kind: "assistant-text",
            text: `⛔ ${json?.message || json?.text || t.pk_qLimit}`,
          }),
        );
        return;
      }

      if (res.status === 404 || res.status === 405) {
        setBubbles((prev) =>
          prev.filter((b) => b.id !== "thinking").concat({
            id: Date.now().toString(),
            kind: "assistant-text",
            text:
              "⚠️ Server pe naya Prashna endpoint abhi live nahi hai. VPS pe git pull + pm2 restart cosmic-api karein, phir try karein.",
          }),
        );
        return;
      }

      const answer = String(
        json?.text || json?.message || json?.error || (rawText && !rawText.startsWith("<") ? rawText : "") || t.pk_genErr,
      ).trim();
      setBubbles((prev) =>
        prev.filter((b) => b.id !== "thinking").concat({
          id: Date.now().toString(),
          kind: "assistant-text",
          text: answer || t.pk_genErr,
        }),
      );
      if (res.ok && json?.ok !== false) {
        try {
          Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
        } catch {}
      }
    } catch {
      setBubbles((prev) =>
        prev.filter((b) => b.id !== "thinking").concat({
          id: Date.now().toString(),
          kind: "assistant-text",
          text: t.pk_netErr,
        }),
      );
    } finally {
      setLoading(false);
    }
  }, [loading, question, user?.id, user?.api_key, t.pk_qLimit, t.pk_genErr, t.pk_netErr, t.vlang]);

  const renderBubble = ({ item }: { item: Bubble }) => {
    if (item.kind === "thinking") {
      return (
        <View style={[s.bubble, s.bubbleAssistant]}>
          <View style={[s.avatar, { backgroundColor: C.accentBg, borderColor: `${C.accent}30` }]}>
            <Text style={{ fontSize: 12 }}>🔮</Text>
          </View>
          <View style={[s.bubbleInner, { backgroundColor: C.bgCard, borderColor: C.border }]}>
            <ActivityIndicator size="small" color={C.accent} />
          </View>
        </View>
      );
    }
    if (item.kind === "user-text") {
      return (
        <View style={[s.bubble, s.bubbleUser]}>
          <View
            style={[
              s.bubbleInner,
              s.bubbleInnerUser,
              {
                backgroundColor: C.isDark ? "#0e3a4d" : "#cffafe",
                borderColor: "#0891b260",
              },
            ]}
          >
            <Text style={[s.bubbleText, { color: C.text }]}>{item.text}</Text>
          </View>
        </View>
      );
    }
    return (
      <View style={[s.bubble, s.bubbleAssistant]}>
        <View style={[s.avatar, { backgroundColor: C.accentBg, borderColor: `${C.accent}30` }]}>
          <Text style={{ fontSize: 12 }}>🔮</Text>
        </View>
        <View style={[s.bubbleInner, { backgroundColor: C.bgCard, borderColor: C.border }]}>
          <Text style={[s.bubbleText, { color: C.textMid }]}>{item.text}</Text>
        </View>
      </View>
    );
  };

  return (
    <CosmicBg>
      <Stack.Screen options={{ headerShown: false }} />
      <KeyboardAvoidingView
        style={s.root}
        behavior={Platform.OS === "ios" ? "padding" : "height"}
      >
        <View style={[s.header, { paddingTop: topPad + 12, borderBottomColor: C.border }]}>
          <Pressable onPress={() => router.back()} style={s.backBtn} hitSlop={10}>
            <Feather name="chevron-left" size={20} color={C.text} />
          </Pressable>
          <View style={s.headerDot} />
          <Text style={[s.headerTitle, { color: C.text }]}>{t.pk_headerTitle}</Text>
          <Text style={[s.headerSub, { color: C.textMuted }]}>{t.pk_headerSub}</Text>
        </View>

        <View
          style={[
            s.modeSwitch,
            { backgroundColor: (C as any).bgCard2 ?? C.bgCard, borderColor: C.border },
          ]}
        >
          <Pressable
            onPress={() => {
              Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
              router.back();
            }}
            style={({ pressed }) => [s.modeSwitchSeg, pressed && { opacity: 0.7 }]}
          >
            <Feather name="message-circle" size={13} color={C.textMuted} />
            <Text style={[s.modeSwitchText, { color: C.textMuted }]}>{t.pk_modeAsk}</Text>
          </Pressable>
          <View style={[s.modeSwitchSeg, { backgroundColor: C.accentBg, borderColor: `${C.accent}80` }]}>
            <Feather name="book-open" size={13} color={C.accent} />
            <Text style={[s.modeSwitchText, { color: C.accent }]}>{t.pk_modeNumber}</Text>
          </View>
        </View>

        <FlatList
          ref={listRef}
          data={bubbles}
          keyExtractor={(b) => b.id}
          renderItem={renderBubble}
          contentContainerStyle={[s.list, { paddingBottom: 12 }]}
          showsVerticalScrollIndicator={false}
        />

        <View
          style={[
            s.inputRow,
            { paddingBottom: botPad + 12, backgroundColor: C.bg, borderTopColor: C.border },
          ]}
        >
          <TextInput
            style={[s.input, { backgroundColor: C.bgCard, borderColor: C.border, color: C.text }]}
            value={question}
            onChangeText={setQuestion}
            placeholder={t.pk_qInputPh}
            placeholderTextColor={C.textMuted}
            multiline
            editable={!loading}
            onSubmitEditing={submit}
            returnKeyType="send"
          />
          <Pressable
            onPress={submit}
            disabled={loading || !question.trim()}
            style={({ pressed }) => [s.sendBtn, pressed && { opacity: 0.7 }]}
          >
            <LinearGradient
              colors={
                loading || !question.trim()
                  ? ["#475569", "#334155"]
                  : ["#0e7490", "#0891b2", "#14b8a6"]
              }
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 1 }}
              style={s.sendGrad}
            >
              {loading ? (
                <ActivityIndicator color="#fff" size="small" />
              ) : (
                <Feather name="send" size={16} color="#fff" />
              )}
            </LinearGradient>
          </Pressable>
        </View>
      </KeyboardAvoidingView>
    </CosmicBg>
  );
}

const s = StyleSheet.create({
  root: { flex: 1 },
  header: {
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: 14,
    paddingBottom: 12,
    gap: 8,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  backBtn: { width: 32, height: 32, alignItems: "center", justifyContent: "center" },
  headerDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: "#14b8a6",
  },
  headerTitle: { fontSize: 16, fontWeight: "700", flexShrink: 1 },
  headerSub: { fontSize: 11, marginLeft: "auto", maxWidth: 120 },
  modeSwitch: {
    flexDirection: "row",
    marginHorizontal: 14,
    marginTop: 10,
    marginBottom: 4,
    borderRadius: 12,
    borderWidth: 1,
    padding: 3,
    gap: 4,
  },
  modeSwitchSeg: {
    flex: 1,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 6,
    paddingVertical: 8,
    borderRadius: 9,
    borderWidth: 1,
    borderColor: "transparent",
  },
  modeSwitchText: { fontSize: 12, fontWeight: "600" },
  list: { paddingHorizontal: 14, paddingTop: 12, gap: 10 },
  bubble: { flexDirection: "row", gap: 8, maxWidth: "92%" },
  bubbleAssistant: { alignSelf: "flex-start" },
  bubbleUser: { alignSelf: "flex-end" },
  avatar: {
    width: 28,
    height: 28,
    borderRadius: 14,
    borderWidth: 1,
    alignItems: "center",
    justifyContent: "center",
    marginTop: 2,
  },
  bubbleInner: {
    borderWidth: 1,
    borderRadius: 14,
    paddingHorizontal: 12,
    paddingVertical: 10,
    maxWidth: "100%",
  },
  bubbleInnerUser: { borderTopRightRadius: 4 },
  bubbleText: { fontSize: 13.5, lineHeight: 20 },
  inputRow: {
    flexDirection: "row",
    alignItems: "flex-end",
    gap: 8,
    paddingHorizontal: 12,
    paddingTop: 10,
    borderTopWidth: StyleSheet.hairlineWidth,
  },
  input: {
    flex: 1,
    minHeight: 42,
    maxHeight: 110,
    borderWidth: 1,
    borderRadius: 14,
    paddingHorizontal: 12,
    paddingVertical: 10,
    fontSize: 14,
  },
  sendBtn: { borderRadius: 14, overflow: "hidden" },
  sendGrad: {
    width: 44,
    height: 42,
    alignItems: "center",
    justifyContent: "center",
  },
});
