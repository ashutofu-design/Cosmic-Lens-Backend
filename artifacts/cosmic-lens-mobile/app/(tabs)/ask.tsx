import { Feather } from "@expo/vector-icons";
import { LinearGradient } from "expo-linear-gradient";
import * as Haptics from "expo-haptics";
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
import { useC } from "@/context/ThemeContext";
import { useUser } from "@/context/UserContext";
import { getT } from "@/lib/i18n";
import { router } from "expo-router";

const API_BASE = `https://${process.env.EXPO_PUBLIC_DOMAIN ?? ""}`;

interface Message {
  id: string;
  role: "user" | "assistant";
  text: string;
  loading?: boolean;
}

const DEMO_MESSAGES: Message[] = [
  {
    id: "d1",
    role: "assistant",
    text: "Hello! I'm your Vedic Astrology assistant. Ask me anything about your Kundli — dasha, planets, houses, or any other question.",
  },
  {
    id: "d2",
    role: "user",
    text: "How will my career be this year?",
  },
  {
    id: "d3",
    role: "assistant",
    text: "Without a Kundli I can only give general information. Create your birth chart — then I'll give you a personalized career analysis based on your active dasha!",
  },
];

const STARTERS = [
  "How will my career be this year?",
  "What is the right time for marriage?",
  "Tell me about my health",
  "When will I see financial gains?",
];

export default function AskScreen() {
  const insets = useSafeAreaInsets();
  const C = useC();
  const { kundli, birthData, language } = useUser();
  const t = getT(language);
  const topPad = Platform.OS === "web" ? 67 : insets.top;
  const botPad = Platform.OS === "web" ? 34 : insets.bottom;
  const showDemo = !kundli;

  const [messages, setMessages] = useState<Message[]>(() =>
    showDemo
      ? DEMO_MESSAGES
      : [
          {
            id: "init",
            role: "assistant",
            text: `Hello! I can read your kundli. Ask me about your planets, dasha, or any area of life.`,
          },
        ]
  );
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const listRef = useRef<FlatList>(null);

  const scrollToEnd = useCallback(() => {
    setTimeout(() => listRef.current?.scrollToEnd({ animated: true }), 100);
  }, []);

  useEffect(() => { scrollToEnd(); }, [messages]);

  const send = useCallback(
    async (text: string) => {
      if (!text.trim() || loading) return;
      if (showDemo) {
        router.push("/onboarding");
        return;
      }
      const userMsg: Message = { id: Date.now().toString(), role: "user", text: text.trim() };
      const thinkMsg: Message = { id: "thinking", role: "assistant", text: "", loading: true };
      setMessages(prev => [...prev, userMsg, thinkMsg]);
      setInput("");
      setLoading(true);
      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);

      try {
        const res = await fetch(`${API_BASE}/api/ask`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ question: text.trim(), kundli, birthData }),
        });
        const json = await res.json();
        const answer = json.answer ?? json.response ?? "Kshama karein, abhi jawab dene mein dikkat aa rahi hai.";
        setMessages(prev =>
          prev.filter(m => m.id !== "thinking").concat({ id: Date.now().toString(), role: "assistant", text: answer })
        );
      } catch {
        setMessages(prev =>
          prev.filter(m => m.id !== "thinking").concat({
            id: Date.now().toString(),
            role: "assistant",
            text: "Network error — thodi der baad try karein.",
          })
        );
      } finally {
        setLoading(false);
      }
    },
    [loading, showDemo, kundli, birthData]
  );

  const renderMsg = ({ item }: { item: Message }) => {
    const isUser = item.role === "user";
    return (
      <View style={[s.bubble, isUser ? s.bubbleUser : s.bubbleAssistant]}>
        {!isUser && (
          <View style={s.avatar}>
            <Text style={{ fontSize: 12 }}>🔭</Text>
          </View>
        )}
        <View style={[s.bubbleInner, isUser ? s.bubbleInnerUser : s.bubbleInnerAssistant]}>
          {item.loading ? (
            <ActivityIndicator size="small" color="#f59e0b" />
          ) : (
            <Text style={[s.bubbleText, isUser ? s.bubbleTextUser : s.bubbleTextAssist]}>
              {item.text}
            </Text>
          )}
        </View>
      </View>
    );
  };

  return (
    <KeyboardAvoidingView
      style={[s.root, { backgroundColor: C.bg }]}
      behavior={Platform.OS === "ios" ? "padding" : undefined}
      keyboardVerticalOffset={Platform.OS === "ios" ? 0 : 0}
    >
      {/* Header */}
      <View style={[s.header, { paddingTop: topPad + 12 }]}>
        <View style={s.headerDot} />
        <Text style={s.headerTitle}>Jyotish AI</Text>
        <Text style={s.headerSub}>Vedic Astrology Assistant</Text>
      </View>

      {/* Demo banner */}
      {showDemo && (
        <Pressable style={s.demoBanner} onPress={() => router.push("/onboarding")}>
          <Feather name="lock" size={12} color="#fbbf24" />
          <Text style={s.demoText}>
            Kundli banao — personalized answers ke liye tap karein
          </Text>
          <Feather name="chevron-right" size={12} color="#fbbf24" />
        </Pressable>
      )}

      {/* Messages */}
      <FlatList
        ref={listRef}
        data={messages}
        keyExtractor={m => m.id}
        renderItem={renderMsg}
        contentContainerStyle={[s.list, { paddingBottom: 12 }]}
        showsVerticalScrollIndicator={false}
      />

      {/* Starter chips (only if single init message) */}
      {messages.length <= 1 && !showDemo && (
        <View style={s.starters}>
          {STARTERS.map(q => (
            <Pressable key={q} style={s.starter} onPress={() => send(q)}>
              <Text style={s.starterText}>{q}</Text>
            </Pressable>
          ))}
        </View>
      )}

      {/* Input row */}
      <View style={[s.inputRow, { paddingBottom: botPad + 100 }]}>
        <TextInput
          style={s.input}
          value={input}
          onChangeText={setInput}
          placeholder={t.askPlaceholder}
          placeholderTextColor="#1e3a5f"
          multiline
          editable={!showDemo}
          onSubmitEditing={() => send(input)}
          returnKeyType="send"
        />
        <Pressable
          onPress={() => (showDemo ? router.push("/onboarding") : send(input))}
          style={({ pressed }) => [s.sendBtn, pressed && { opacity: 0.7 }]}
        >
          <LinearGradient
            colors={["#0ea5e9", "#3b82f6"]}
            style={s.sendGrad}
          >
            <Feather name={showDemo ? "lock" : "send"} size={16} color="#fff" />
          </LinearGradient>
        </Pressable>
      </View>
    </KeyboardAvoidingView>
  );
}

const s = StyleSheet.create({
  root: { flex: 1, backgroundColor: "#020d1a" },

  header: {
    alignItems: "center", paddingBottom: 14,
    borderBottomWidth: 1, borderBottomColor: "rgba(255,255,255,0.04)",
    gap: 2,
  },
  headerDot: {
    width: 8, height: 8, borderRadius: 4, backgroundColor: "#22c55e",
    marginBottom: 4,
  },
  headerTitle: { color: "#dde8f4", fontSize: 16, fontWeight: "700" },
  headerSub:   { color: "#3d5a7a", fontSize: 11 },

  demoBanner: {
    flexDirection: "row", alignItems: "center", gap: 7,
    backgroundColor: "rgba(251,191,36,0.06)", borderBottomWidth: 1,
    borderBottomColor: "rgba(251,191,36,0.12)", paddingHorizontal: 20, paddingVertical: 10,
    justifyContent: "center",
  },
  demoText: { color: "#fbbf24", fontSize: 12, flex: 1, textAlign: "center" },

  list: { paddingHorizontal: 16, paddingTop: 12, gap: 10 },

  bubble: { flexDirection: "row", gap: 8, marginBottom: 10 },
  bubbleUser:      { justifyContent: "flex-end" },
  bubbleAssistant: { justifyContent: "flex-start" },

  avatar: {
    width: 28, height: 28, borderRadius: 14,
    backgroundColor: "rgba(245,158,11,0.12)", borderWidth: 1, borderColor: "rgba(245,158,11,0.2)",
    alignItems: "center", justifyContent: "center",
    alignSelf: "flex-end",
  },

  bubbleInner: {
    maxWidth: "80%", borderRadius: 16, paddingHorizontal: 14, paddingVertical: 10,
  },
  bubbleInnerUser: {
    backgroundColor: "#0c3257", borderBottomRightRadius: 4,
  },
  bubbleInnerAssistant: {
    backgroundColor: "#040e1f", borderWidth: 1, borderColor: "rgba(255,255,255,0.06)",
    borderBottomLeftRadius: 4,
  },
  bubbleText:       { fontSize: 13, lineHeight: 20 },
  bubbleTextUser:   { color: "#dde8f4" },
  bubbleTextAssist: { color: "#94a3b8" },

  starters: {
    paddingHorizontal: 16, paddingBottom: 10, gap: 8,
    flexDirection: "row", flexWrap: "wrap",
  },
  starter: {
    paddingHorizontal: 12, paddingVertical: 8, borderRadius: 20,
    backgroundColor: "#040e1f", borderWidth: 1, borderColor: "rgba(245,158,11,0.15)",
  },
  starterText: { color: "#f59e0b", fontSize: 12 },

  inputRow: {
    flexDirection: "row", alignItems: "flex-end", gap: 10,
    paddingHorizontal: 16, paddingTop: 10,
    borderTopWidth: 1, borderTopColor: "rgba(255,255,255,0.04)",
    backgroundColor: "#020d1a",
  },
  input: {
    flex: 1, backgroundColor: "#040e1f", borderRadius: 22, borderWidth: 1,
    borderColor: "rgba(255,255,255,0.07)", paddingHorizontal: 16, paddingVertical: 10,
    color: "#dde8f4", fontSize: 13, maxHeight: 100,
  },
  sendBtn:  { borderRadius: 22, overflow: "hidden" },
  sendGrad: { width: 44, height: 44, borderRadius: 22, alignItems: "center", justifyContent: "center" },
});
