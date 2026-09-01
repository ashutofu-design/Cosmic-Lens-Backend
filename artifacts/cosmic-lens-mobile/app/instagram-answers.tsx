import { Feather, MaterialCommunityIcons } from "@expo/vector-icons";
import * as Haptics from "expo-haptics";
import { LinearGradient } from "expo-linear-gradient";
import { router, Stack } from "expo-router";
import React, { useCallback, useEffect, useRef, useState } from "react";
import {
  ActivityIndicator,
  Alert,
  FlatList,
  Keyboard,
  Linking,
  Platform,
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { AppKeyboardAvoidingView as KeyboardAvoidingView } from "@/components/AppKeyboardAvoidingView";
import { CosmicBg } from "@/components/CosmicBg";
import { useC } from "@/context/ThemeContext";
import { useUser } from "@/context/UserContext";
import { API_BASE } from "@/lib/apiConfig";
import { FOUNDER_PROFILE } from "@/lib/founderProfile";
import { INSTAGRAM_ANSWERS_ENABLED } from "@/lib/instagramAnswersFeature";

type ChatRole = "bot" | "user" | "system";

type ChatMsg = {
  id: string;
  role: ChatRole;
  text: string;
};

type MatchResult = {
  matched: boolean;
  message?: string;
  answer?: string;
  question?: string;
  videoNumber?: number;
};

const WELCOME: ChatMsg = {
  id: "welcome",
  role: "bot",
  text:
    "Namaste 🙏 Reel number set karo (upar), phir jo exact words Instagram par DM / comment mein likhte ho — wahi yahan type karo. Match par saved auto-reply dikhega.",
};

let msgSeq = 0;
function nextId() {
  msgSeq += 1;
  return `m-${Date.now()}-${msgSeq}`;
}

export default function InstagramAnswersScreen() {
  const enabled = INSTAGRAM_ANSWERS_ENABLED;

  useEffect(() => {
    if (!enabled) router.replace("/(tabs)/ask");
  }, [enabled]);

  const c = useC();
  const insets = useSafeAreaInsets();
  const { user } = useUser();
  const listRef = useRef<FlatList<ChatMsg>>(null);

  const [videoNumber, setVideoNumber] = useState("");
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<ChatMsg[]>([WELCOME]);
  const [loading, setLoading] = useState(false);

  const scrollToEnd = useCallback(() => {
    setTimeout(() => listRef.current?.scrollToEnd({ animated: true }), 80);
  }, []);

  if (!enabled) return null;

  const pushBot = (text: string) => {
    setMessages((prev) => [...prev, { id: nextId(), role: "bot", text }]);
    scrollToEnd();
  };

  const sendTrigger = async () => {
    const q = input.trim();
    const vn = Number(videoNumber.trim());
    if (!Number.isFinite(vn) || vn <= 0) {
      Alert.alert("Reel number", "Pehle video / reel number daalein (e.g. 100).");
      return;
    }
    if (!q) return;

    if (!user?.id || !user?.api_key) {
      Alert.alert("Login required", "Pehle login karein — phir free auto-replies unlock honge.");
      router.push("/login");
      return;
    }

    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    Keyboard.dismiss();
    setInput("");
    setMessages((prev) => [...prev, { id: nextId(), role: "user", text: q }]);
    scrollToEnd();
    setLoading(true);

    try {
      const resp = await fetch(`${API_BASE}/api/instagram-answers/match`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-API-Key": user.api_key,
        },
        body: JSON.stringify({
          user_id: user.id,
          video_number: vn,
          question: q,
        }),
      });
      const json = (await resp.json()) as MatchResult & { error?: string; message?: string };

      if (resp.status === 401) {
        pushBot("Session expired — dubara login karein.");
        Haptics.notificationAsync(Haptics.NotificationFeedbackType.Warning);
        return;
      }
      if (!resp.ok) {
        pushBot(json.message || json.error || "Answer fetch nahi ho paya. Dubara try karein.");
        Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
        return;
      }

      if (json.matched && json.answer) {
        pushBot(json.answer);
        Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      } else {
        pushBot(
          json.message ||
            "Is reel number aur exact words ke liye abhi koi saved auto-reply nahi hai. Spelling check karein — extra words ya typo par match nahi hota.",
        );
        Haptics.notificationAsync(Haptics.NotificationFeedbackType.Warning);
      }
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Network error";
      pushBot(msg);
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
    } finally {
      setLoading(false);
    }
  };

  const renderBubble = ({ item }: { item: ChatMsg }) => {
    if (item.role === "system") {
      return (
        <View style={s.systemWrap}>
          <Text style={[s.systemText, { color: c.textMuted }]}>{item.text}</Text>
        </View>
      );
    }
    const isUser = item.role === "user";
    return (
      <View style={[s.row, isUser ? s.rowUser : s.rowBot]}>
        {!isUser ? (
          <LinearGradient
            colors={["#833ab4", "#fd1d1d"]}
            style={s.avatar}
          >
            <MaterialCommunityIcons name="instagram" size={14} color="#fff" />
          </LinearGradient>
        ) : null}
        <View
          style={[
            s.bubble,
            isUser ? s.bubbleUser : s.bubbleBot,
            isUser
              ? { backgroundColor: "#3797f0" }
              : { backgroundColor: c.bgCard2, borderColor: c.border },
          ]}
        >
          {!isUser ? <Text style={s.bubbleLabel}>AUTO-REPLY</Text> : null}
          <Text style={[s.bubbleText, { color: isUser ? "#fff" : c.text }]}>{item.text}</Text>
        </View>
      </View>
    );
  };

  return (
    <CosmicBg>
      <Stack.Screen options={{ headerShown: false }} />
      <View style={[s.header, { paddingTop: insets.top + 6 }]}>
        <Pressable onPress={() => router.back()} hitSlop={10} style={s.backBtn}>
          <Feather name="chevron-left" size={28} color={c.text} />
        </Pressable>
        <View style={{ flex: 1 }}>
          <Text style={[s.title, { color: c.text }]}>Free Instagram Answers</Text>
          <Pressable
            onPress={() => Linking.openURL(FOUNDER_PROFILE.instagramUrl).catch(() => {})}
            style={s.handleRow}
          >
            <MaterialCommunityIcons name="instagram" size={12} color={c.accent} />
            <Text style={[s.handle, { color: c.accent }]}>{FOUNDER_PROFILE.instagramHandle}</Text>
          </Pressable>
        </View>
      </View>

      <View style={[s.videoBar, { backgroundColor: c.bgCard, borderColor: c.border }]}>
        <Text style={[s.videoLabel, { color: c.textMuted }]}>Reel #</Text>
        <TextInput
          value={videoNumber}
          onChangeText={setVideoNumber}
          placeholder="100"
          placeholderTextColor={c.textMuted}
          keyboardType="number-pad"
          style={[s.videoInput, { color: c.text, borderColor: c.border }]}
        />
        <Text style={[s.videoHint, { color: c.textMuted }]}>Trigger + video = exact match</Text>
      </View>

      <KeyboardAvoidingView style={{ flex: 1 }} keyboardVerticalOffset={Platform.OS === "ios" ? 8 : 0}>
        <FlatList
          ref={listRef}
          data={messages}
          keyExtractor={(m) => m.id}
          renderItem={renderBubble}
          contentContainerStyle={[s.list, { paddingBottom: 12 }]}
          onContentSizeChange={scrollToEnd}
          keyboardShouldPersistTaps="handled"
        />

        {loading ? (
          <View style={s.typingRow}>
            <ActivityIndicator size="small" color={c.accent} />
            <Text style={[s.typingText, { color: c.textMuted }]}>Matching trigger…</Text>
          </View>
        ) : null}

        <View
          style={[
            s.inputBar,
            {
              paddingBottom: insets.bottom + 8,
              backgroundColor: c.bgCard,
              borderTopColor: c.border,
            },
          ]}
        >
          <TextInput
            value={input}
            onChangeText={setInput}
            placeholder="Exact words — jaise Instagram DM mein likhte ho"
            placeholderTextColor={c.textMuted}
            multiline
            maxLength={500}
            style={[
              s.dmInput,
              { color: c.text, backgroundColor: c.inputBg, borderColor: c.inputBorder },
            ]}
            onSubmitEditing={() => sendTrigger()}
          />
          <Pressable
            onPress={() => sendTrigger()}
            disabled={loading || !input.trim()}
            style={[s.sendBtn, (loading || !input.trim()) && { opacity: 0.45 }]}
          >
            <LinearGradient colors={["#833ab4", "#fd1d1d"]} style={s.sendGrad}>
              <Feather name="send" size={18} color="#fff" />
            </LinearGradient>
          </Pressable>
        </View>
      </KeyboardAvoidingView>
    </CosmicBg>
  );
}

const s = StyleSheet.create({
  header: {
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: 12,
    paddingBottom: 8,
    gap: 4,
  },
  backBtn: { padding: 4 },
  title: { fontSize: 18, fontWeight: "800", letterSpacing: -0.3 },
  handleRow: { flexDirection: "row", alignItems: "center", gap: 5, marginTop: 2 },
  handle: { fontSize: 12, fontWeight: "700" },
  videoBar: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    marginHorizontal: 12,
    marginBottom: 8,
    paddingHorizontal: 12,
    paddingVertical: 10,
    borderRadius: 14,
    borderWidth: 1,
  },
  videoLabel: { fontSize: 12, fontWeight: "700" },
  videoInput: {
    minWidth: 56,
    borderWidth: 1,
    borderRadius: 8,
    paddingHorizontal: 10,
    paddingVertical: 6,
    fontSize: 15,
    fontWeight: "700",
  },
  videoHint: { flex: 1, fontSize: 10, lineHeight: 14 },
  list: { paddingHorizontal: 12, paddingTop: 8 },
  row: { flexDirection: "row", marginBottom: 10, alignItems: "flex-end", gap: 8 },
  rowUser: { justifyContent: "flex-end" },
  rowBot: { justifyContent: "flex-start" },
  avatar: {
    width: 28,
    height: 28,
    borderRadius: 14,
    alignItems: "center",
    justifyContent: "center",
  },
  bubble: {
    maxWidth: "82%",
    borderRadius: 18,
    paddingHorizontal: 12,
    paddingVertical: 10,
  },
  bubbleUser: { borderBottomRightRadius: 5 },
  bubbleBot: { borderWidth: 1, borderBottomLeftRadius: 5 },
  bubbleLabel: {
    color: "#ffffff99",
    fontSize: 9,
    fontWeight: "800",
    letterSpacing: 0.6,
    marginBottom: 4,
  },
  bubbleText: { fontSize: 14, lineHeight: 20 },
  systemWrap: { alignItems: "center", marginVertical: 8 },
  systemText: { fontSize: 11, textAlign: "center", lineHeight: 16 },
  typingRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    paddingHorizontal: 16,
    paddingBottom: 4,
  },
  typingText: { fontSize: 12 },
  inputBar: {
    flexDirection: "row",
    alignItems: "flex-end",
    gap: 8,
    paddingHorizontal: 12,
    paddingTop: 10,
    borderTopWidth: 1,
  },
  dmInput: {
    flex: 1,
    borderWidth: 1,
    borderRadius: 20,
    paddingHorizontal: 14,
    paddingVertical: 10,
    fontSize: 15,
    maxHeight: 100,
    minHeight: 42,
  },
  sendBtn: { marginBottom: 2 },
  sendGrad: {
    width: 42,
    height: 42,
    borderRadius: 21,
    alignItems: "center",
    justifyContent: "center",
  },
});
