import { Feather } from "@expo/vector-icons";
import { LinearGradient } from "expo-linear-gradient";
import * as Haptics from "expo-haptics";
import React, { useCallback, useEffect, useRef, useState } from "react";
import {
  ActivityIndicator,
  FlatList,
  KeyboardAvoidingView,
  Modal,
  Platform,
  Pressable,
  StatusBar,
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
import { getT } from "@/lib/i18n";
import { router } from "expo-router";

import { API_BASE, apiFetch } from "@/lib/apiConfig";

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
    text: "Pranam beta 🙏 Mai Acharya Vidyasagar — 35 saal se kundli padh raha hu Kashi mein. Aap apni kundli, dasha, vivah, karya, swasthya — kuch bhi pooch sakte hain, mai margdarshan dunga.",
  },
  {
    id: "d2",
    role: "user",
    text: "How will my career be this year?",
  },
  {
    id: "d3",
    role: "assistant",
    text: "Beta, bina kundli dekhe mai sirf saamanya baat keh sakta hu. Aap pehle apni janm-kundli banaiye — phir mai aapke graha, dasha aur yog dekh ke ekdum personalized margdarshan dunga.",
  },
];

const STARTERS = [
  "Mera vivah kab hoga?",
  "Career mein safalta kab milegi?",
  "Mere swasthya ke baare mein bataiye",
  "Dhan-laabh kab hoga mujhe?",
];

export default function AskScreen() {
  const insets = useSafeAreaInsets();
  const C = useC();
  const { kundli, birthData, language, user } = useUser();
  const t = useT();
  const androidSB = StatusBar.currentHeight ?? 24;
  const topPad = Platform.OS === "web" ? 67 : Platform.OS === "android" ? Math.max(insets.top, androidSB) : insets.top;
  const botPad = Platform.OS === "web" ? 34 : insets.bottom;
  const showDemo = !kundli;

  const [messages, setMessages] = useState<Message[]>(() =>
    showDemo
      ? DEMO_MESSAGES
      : [
          {
            id: "init",
            role: "assistant",
            text: `Pranam beta 🙏 Mai Acharya Vidyasagar — Kashi se. Aapki kundli mere saamne hai. Vivah, karya, swasthya, dhan — jo bhi prashna ho, nishankoch poochiye.`,
          },
        ]
  );
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [quotaModal, setQuotaModal] = useState<null | {
    used: number;
    limit: number;
    plan: string;
    message: string;
  }>(null);
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
        const headers: Record<string, string> = { "Content-Type": "application/json" };
        if (user?.api_key) headers["X-API-Key"] = user.api_key;

        const res = await apiFetch(`${API_BASE}/api/ask`, {
          method: "POST",
          headers,
          body: JSON.stringify({
            question: text.trim(),
            kundli,
            birthData,
            lang: language,
            user_id: user?.id,
          }),
        });
        const json = await res.json().catch(() => ({} as any));

        // ── Quota exhausted (HTTP 402) ─────────────────────────────────────
        if (res.status === 402) {
          // Remove the thinking bubble and the user's just-sent message
          // (they didn't actually consume an answer).
          setMessages(prev => prev.filter(m => m.id !== "thinking" && m.id !== userMsg.id));
          setInput(text); // restore input so they can retry after upgrade
          setQuotaModal({
            used:    json?.quota?.used  ?? 0,
            limit:   json?.quota?.limit ?? 0,
            plan:    json?.plan         ?? "free",
            message: json?.message      ?? t.askDailyLimitOver,
          });
          try { Haptics.notificationAsync(Haptics.NotificationFeedbackType.Warning); } catch {}
          return;
        }

        // ── Auth error (401) ──────────────────────────────────────────────
        if (res.status === 401) {
          setMessages(prev =>
            prev.filter(m => m.id !== "thinking").concat({
              id: Date.now().toString(),
              role: "assistant",
              text: "Session expired — kripya logout karke phir login karein.",
            })
          );
          return;
        }

        const answer =
          json.text ?? json.answer ?? json.response ??
          "Kshama karein, abhi jawab dene mein dikkat aa rahi hai.";
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
    [loading, showDemo, kundli, birthData, user?.id, user?.api_key, language]
  );

  const renderMsg = ({ item }: { item: Message }) => {
    const isUser = item.role === "user";
    return (
      <View style={[s.bubble, isUser ? s.bubbleUser : s.bubbleAssistant]}>
        {!isUser && (
          <View style={[s.avatar, { backgroundColor: C.accentBg, borderColor: `${C.accent}30` }]}>
            <Text style={{ fontSize: 12 }}>🔭</Text>
          </View>
        )}
        <View style={[s.bubbleInner, isUser
          ? [s.bubbleInnerUser, { backgroundColor: C.isDark ? "#1E1B4B" : "#EDE9FE", borderColor: `${C.accent}30` }]
          : [s.bubbleInnerAssistant, { backgroundColor: C.bgCard, borderColor: C.border }]]}>
          {item.loading ? (
            <ActivityIndicator size="small" color={C.accent} />
          ) : (
            <Text style={[s.bubbleText, isUser
              ? [s.bubbleTextUser, { color: C.text }]
              : [s.bubbleTextAssist, { color: C.textMid }]]}>
              {item.text}
            </Text>
          )}
        </View>
      </View>
    );
  };

  return (
    <CosmicBg>
    <KeyboardAvoidingView
      style={s.root}
      behavior={Platform.OS === "ios" ? "padding" : "height"}
      keyboardVerticalOffset={Platform.OS === "ios" ? 0 : 0}
    >
      {/* Header */}
      <View style={[s.header, { paddingTop: topPad + 12, borderBottomColor: C.border }]}>
        <View style={s.headerDot} />
        <Text style={[s.headerTitle, { color: C.text }]}>Acharya Vidyasagar</Text>
        <Text style={[s.headerSub, { color: C.textMuted }]}>Powered by Advanced Cosmic Intelligence</Text>
      </View>

      {/* Demo banner */}
      {showDemo && (
        <Pressable style={[s.demoBanner, { backgroundColor: C.warningBg, borderColor: C.warningBorder }]} onPress={() => router.push("/onboarding")}>
          <Feather name="lock" size={12} color={C.warningText} />
          <Text style={[s.demoText, { color: C.warningText }]}>
            Kundli banao — personalized answers ke liye tap karein
          </Text>
          <Feather name="chevron-right" size={12} color={C.warningText} />
        </Pressable>
      )}

      {/* Divya Prashna entry */}
      <Pressable
        onPress={() => { Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium); router.push("/divya-prashna"); }}
        style={{ marginHorizontal: 12, marginBottom: 8, borderRadius: 14, overflow: "hidden" }}
      >
        <LinearGradient
          colors={["#7c3aed", "#a855f7", "#ec4899"]}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 1 }}
          style={{ paddingHorizontal: 14, paddingVertical: 12, flexDirection: "row", alignItems: "center", gap: 12 }}
        >
          <Text style={{ fontSize: 22 }}>🔮</Text>
          <View style={{ flex: 1 }}>
            <Text style={{ color: "#fff", fontSize: 14, fontWeight: "800" }}>Divya Prashna</Text>
            <Text style={{ color: "#ffffffcc", fontSize: 11, marginTop: 2 }}>
              Apna sawaal pucho — turant Vedic horary jawab
            </Text>
          </View>
          <Feather name="chevron-right" size={18} color="#fff" />
        </LinearGradient>
      </Pressable>

      {/* Prashna Kundli (KP 1-249) entry */}
      <Pressable
        onPress={() => { Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium); router.push("/prashna-kundli"); }}
        style={{ marginHorizontal: 12, marginBottom: 10, borderRadius: 14, overflow: "hidden" }}
      >
        <LinearGradient
          colors={["#0e7490", "#0891b2", "#14b8a6"]}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 1 }}
          style={{ paddingHorizontal: 14, paddingVertical: 12, flexDirection: "row", alignItems: "center", gap: 12 }}
        >
          <Text style={{ fontSize: 22 }}>🔢</Text>
          <View style={{ flex: 1 }}>
            <Text style={{ color: "#fff", fontSize: 14, fontWeight: "800" }}>Prashna Kundli (KP 1-249)</Text>
            <Text style={{ color: "#ffffffcc", fontSize: 11, marginTop: 2 }}>
              Ek number socho 1-249 — cusp sub-lord ka sahi jawab
            </Text>
          </View>
          <Feather name="chevron-right" size={18} color="#fff" />
        </LinearGradient>
      </Pressable>

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
            <Pressable key={q} style={[s.starter, { backgroundColor: C.bgCard, borderColor: `${C.accent}30` }]} onPress={() => send(q)}>
              <Text style={[s.starterText, { color: C.accent }]}>{q}</Text>
            </Pressable>
          ))}
        </View>
      )}

      {/* Input row */}
      <View style={[s.inputRow, { paddingBottom: botPad + 90, backgroundColor: C.bg, borderTopColor: C.border }]}>
        <TextInput
          style={[s.input, { backgroundColor: C.bgCard, borderColor: C.border, color: C.text }]}
          value={input}
          onChangeText={setInput}
          placeholder={t.askPlaceholder}
          placeholderTextColor={C.textMuted}
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
            colors={[C.btnGradStart, C.btnGradEnd]}
            start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }}
            style={s.sendGrad}
          >
            <Feather name={showDemo ? "lock" : "send"} size={16} color="#fff" />
          </LinearGradient>
        </Pressable>
      </View>

      {/* ── Daily quota exhausted modal ──────────────────────────────────── */}
      <Modal
        visible={!!quotaModal}
        transparent
        animationType="fade"
        onRequestClose={() => setQuotaModal(null)}
      >
        <Pressable style={qm.backdrop} onPress={() => setQuotaModal(null)}>
          <Pressable style={[qm.card, { backgroundColor: C.bgCard, borderColor: `${C.accent}40` }]} onPress={(e) => e.stopPropagation?.()}>
            <View style={[qm.iconWrap, { backgroundColor: C.accentBg, borderColor: `${C.accent}40` }]}>
              <Feather name="zap" size={28} color={C.accent} />
            </View>

            <Text style={[qm.title, { color: C.text }]}>Daily limit poora</Text>

            <Text style={[qm.usage, { color: C.textMid }]}>
              <Text style={{ fontWeight: "700", color: C.text }}>{quotaModal?.used ?? 0}</Text>
              <Text> / </Text>
              <Text style={{ fontWeight: "700", color: C.text }}>{quotaModal?.limit ?? 0}</Text>
              <Text> questions used today</Text>
            </Text>

            <Text style={[qm.msg, { color: C.textMuted }]}>
              {quotaModal?.plan === "pro"
                ? quotaModal?.message
                : quotaModal?.plan === "basic"
                  ? "Basic plan mein 10 questions/day milte hain. Pro upgrade karke unlimited paayein."
                  : quotaModal?.plan === "trial"
                    ? "Trial mein 3 questions/day milte hain. Pro lekar unlimited karein."
                    : "Free mein 1 question/day. Trial start karein ya Basic/Pro lein."}
            </Text>

            {quotaModal?.plan !== "pro" && (
              <Pressable
                onPress={() => {
                  setQuotaModal(null);
                  router.push("/subscription");
                }}
                style={({ pressed }) => [{ width: "100%", marginTop: 4, opacity: pressed ? 0.9 : 1 }]}
              >
                <LinearGradient
                  colors={["#d97706", "#f59e0b"]}
                  start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }}
                  style={qm.cta}
                >
                  <Feather name="zap" size={15} color="#fff" />
                  <Text style={qm.ctaText}>Upgrade Now</Text>
                </LinearGradient>
              </Pressable>
            )}

            <Pressable onPress={() => setQuotaModal(null)} style={qm.dismiss}>
              <Text style={[qm.dismissText, { color: C.textMuted }]}>
                {quotaModal?.plan === "pro" ? "Theek hai" : "Baad mein"}
              </Text>
            </Pressable>
          </Pressable>
        </Pressable>
      </Modal>
    </KeyboardAvoidingView>
    </CosmicBg>
  );
}

const qm = StyleSheet.create({
  backdrop: {
    flex: 1,
    backgroundColor: "rgba(0,0,0,0.6)",
    alignItems: "center",
    justifyContent: "center",
    paddingHorizontal: 24,
  },
  card: {
    width: "100%",
    maxWidth: 360,
    borderRadius: 20,
    borderWidth: 1.5,
    padding: 24,
    alignItems: "center",
    gap: 10,
  },
  iconWrap: {
    width: 60, height: 60, borderRadius: 16, borderWidth: 1.5,
    alignItems: "center", justifyContent: "center",
    marginBottom: 4,
  },
  title: {
    fontSize: 19, fontWeight: "700", letterSpacing: -0.3, textAlign: "center",
  },
  usage: { fontSize: 13, textAlign: "center" },
  msg: {
    fontSize: 12.5, textAlign: "center", lineHeight: 18, marginBottom: 6,
  },
  cta: {
    flexDirection: "row", alignItems: "center", justifyContent: "center",
    gap: 8, paddingVertical: 13, borderRadius: 13,
  },
  ctaText: { color: "#fff", fontSize: 14.5, fontWeight: "700" },
  dismiss: { paddingVertical: 8, paddingHorizontal: 16, marginTop: 4 },
  dismissText: { fontSize: 12.5, fontWeight: "600" },
});

const s = StyleSheet.create({
  root: { flex: 1 },

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
