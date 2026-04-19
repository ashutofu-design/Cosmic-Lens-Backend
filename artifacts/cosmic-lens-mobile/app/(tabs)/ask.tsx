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

  // Mode picker: null = show 2-option landing, "chat" = open Acharya chat
  const [mode, setMode] = useState<"chat" | null>(null);

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
  const [prashnaNumber, setPrashnaNumber] = useState("");
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

  const sendPrashna = useCallback(
    async (numStr: string, qText: string) => {
      if (loading) return;
      const n = parseInt(numStr, 10);
      if (!Number.isFinite(n) || n < 1 || n > 249) {
        setMessages(prev => [...prev, {
          id: Date.now().toString(),
          role: "assistant",
          text: "⚠️ Number 1 se 249 ke beech hona chahiye. Mann shant karke ek sankhya sochiye.",
        }]);
        return;
      }
      if (showDemo) { router.push("/onboarding"); return; }

      const userMsg: Message = {
        id: Date.now().toString(),
        role: "user",
        text: `🔢 Sankhya: ${n}${qText.trim() ? ` — ${qText.trim()}` : ""}`,
      };
      const thinkMsg: Message = { id: "thinking", role: "assistant", text: "", loading: true };
      setMessages(prev => [...prev, userMsg, thinkMsg]);
      setPrashnaNumber("");
      setInput("");
      setLoading(true);
      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);

      try {
        const headers: Record<string, string> = { "Content-Type": "application/json" };
        if (user?.api_key) headers["X-API-Key"] = user.api_key;

        const res = await apiFetch(`${API_BASE}/api/prashna/number-ask`, {
          method: "POST",
          headers,
          body: JSON.stringify({
            number: n,
            question: qText.trim(),
            user_id: user?.id,
          }),
        });
        const json = await res.json().catch(() => ({} as any));

        if (res.status === 402) {
          setMessages(prev => prev.filter(m => m.id !== "thinking" && m.id !== userMsg.id));
          setPrashnaNumber(numStr);
          setInput(qText);
          setQuotaModal({
            used:    json?.quota?.used  ?? 0,
            limit:   json?.quota?.limit ?? 0,
            plan:    json?.plan         ?? "free",
            message: json?.message      ?? t.askDailyLimitOver,
          });
          try { Haptics.notificationAsync(Haptics.NotificationFeedbackType.Warning); } catch {}
          return;
        }

        const v = json?.verdict;
        const c = json?.caution;
        let answer = "";
        if (v) {
          answer += `${v.label_hi || v.label || ""}\n${v.meaning || ""}\n`;
        }
        if (json?.timing) answer += `\n⏰ ${json.timing}`;
        if (Array.isArray(json?.cusp_analysis) && json.cusp_analysis.length) {
          const cuspLines = json.cusp_analysis.slice(0, 3).map((cu: any) =>
            `• Bhav ${cu.house}: ${cu.sub_lord || ""}${cu.verdict_note ? ` — ${cu.verdict_note}` : ""}`
          ).join("\n");
          if (cuspLines) answer += `\n\n📊 Cusp Analysis:\n${cuspLines}`;
        }
        if (c?.reason) answer += `\n\n⚠️ Saavdhani: ${c.reason}`;
        if (!answer.trim()) answer = json?.error || "Kshama karein, abhi prashna ka jawab nahi mil paaya.";

        setMessages(prev =>
          prev.filter(m => m.id !== "thinking").concat({
            id: Date.now().toString(),
            role: "assistant",
            text: answer.trim(),
          })
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
    [loading, showDemo, user?.id, user?.api_key, t.askDailyLimitOver]
  );

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
        {mode === "chat" && (
          <Pressable
            onPress={() => { Haptics.selectionAsync(); setMode(null); }}
            hitSlop={12}
            style={s.backBtn}
          >
            <Feather name="chevron-left" size={20} color={C.text} />
          </Pressable>
        )}
        <View style={s.headerDot} />
        <Text style={[s.headerTitle, { color: C.text }]}>Acharya Vidyasagar</Text>
        <Text style={[s.headerSub, { color: C.textMuted }]}>Powered by Advanced Cosmic Intelligence</Text>
      </View>

      {/* ── Mode switcher pill (chat ⇄ prashna) ───────────────────────────── */}
      {(mode === "chat" || mode === "prashna") && (
        <View style={[s.modeSwitch, { backgroundColor: (C as any).bgCard2 ?? C.bgCard, borderColor: C.border }]}>
          <Pressable
            onPress={() => {
              if (mode === "chat") return;
              Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
              setMode("chat");
            }}
            style={({ pressed }) => [
              s.modeSwitchSeg,
              mode === "chat" && { backgroundColor: C.accentBg, borderColor: `${C.accent}80` },
              pressed && mode !== "chat" && { opacity: 0.7 },
            ]}
          >
            <Feather name="message-circle" size={13} color={mode === "chat" ? C.accent : C.textMuted} />
            <Text style={[s.modeSwitchText, { color: mode === "chat" ? C.accent : C.textMuted }]}>
              Advance Ask Engine
            </Text>
          </Pressable>
          <Pressable
            onPress={() => {
              if (mode === "prashna") return;
              Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
              if (showDemo) { router.push("/onboarding"); return; }
              setMode("prashna");
              setMessages(prev => {
                if (prev.some(m => m.id === "prashna-init")) return prev;
                return [...prev, {
                  id: "prashna-init",
                  role: "assistant",
                  text: "🔢 Prashna Kundli (KP 1-249) — mann ko shant karke ek number 1 se 249 ke beech sochiye, neeche likhiye. Aap apna prashna bhi saath mein likh sakte hain. Wahi sankhya aapki prashna-kundli ka lagna banegi.",
                }];
              });
            }}
            style={({ pressed }) => [
              s.modeSwitchSeg,
              mode === "prashna" && { backgroundColor: C.accentBg, borderColor: `${C.accent}80` },
              pressed && mode !== "prashna" && { opacity: 0.7 },
            ]}
          >
            <Feather name="hash" size={13} color={mode === "prashna" ? C.accent : C.textMuted} />
            <Text style={[s.modeSwitchText, { color: mode === "prashna" ? C.accent : C.textMuted }]}>
              Prashna Kundli
            </Text>
          </Pressable>
        </View>
      )}

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

      {/* ───── Mode Picker (default landing) ────────────────────────────── */}
      {mode === null && (
        <View style={s.pickerWrap}>
          <Text style={[s.pickerHi, { color: C.text }]}>Pranam beta 🙏</Text>
          <Text style={[s.pickerSub, { color: C.textMid }]}>
            Aaj kis vidhi se margdarshan chahte hain?
          </Text>

          {/* Card 1: Ask Anything (Chat) */}
          <Pressable
            onPress={() => {
              Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
              if (showDemo) { router.push("/onboarding"); return; }
              setMode("chat");
            }}
            style={({ pressed }) => [s.modeCard, pressed && { opacity: 0.85 }]}
          >
            <LinearGradient
              colors={["#1e40af", "#3b82f6", "#06b6d4"]}
              start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }}
              style={s.modeGrad}
            >
              <Text style={s.modeEmoji}>💬</Text>
              <View style={{ flex: 1 }}>
                <Text style={s.modeTitle}>Ask Anything</Text>
                <Text style={s.modeBody}>
                  Acharya se seedhi baat — kundli, dasha, vivah, karya, swasthya — koi bhi prashna poochho.
                </Text>
                <View style={s.modeMeta}>
                  <Feather name="message-circle" size={11} color="#ffffffcc" />
                  <Text style={s.modeMetaText}>Personalized chat · BPHS aadhar</Text>
                </View>
              </View>
              <Feather name="chevron-right" size={20} color="#fff" />
            </LinearGradient>
          </Pressable>

          {/* Card 2: Prashna Kundli (KP 1-249) */}
          <Pressable
            onPress={() => {
              Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
              if (showDemo) { router.push("/onboarding"); return; }
              setMode("prashna");
              setMessages(prev => prev.some(m => m.id === "prashna-init") ? prev : [...prev, {
                id: "prashna-init",
                role: "assistant",
                text: "🔢 Prashna Kundli (KP 1-249) — mann ko shant karke ek number 1 se 249 ke beech sochiye, neeche likhiye. Aap apna prashna bhi saath mein likh sakte hain. Wahi sankhya aapki prashna-kundli ka lagna banegi.",
              }]);
            }}
            style={({ pressed }) => [s.modeCard, pressed && { opacity: 0.85 }]}
          >
            <LinearGradient
              colors={["#0e7490", "#0891b2", "#14b8a6"]}
              start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }}
              style={s.modeGrad}
            >
              <Text style={s.modeEmoji}>🔢</Text>
              <View style={{ flex: 1 }}>
                <View style={{ flexDirection: "row", alignItems: "center", gap: 6 }}>
                  <Text style={s.modeTitle}>Prashna Kundli</Text>
                  <View style={s.modeBadge}>
                    <Text style={s.modeBadgeText}>KP 1-249</Text>
                  </View>
                </View>
                <Text style={s.modeBody}>
                  Mann mein ek number 1-249 socho — wahi sankhya aapki kundli ka lagna banegi, cusp sub-lord se sahi jawab.
                </Text>
                <View style={s.modeMeta}>
                  <Feather name="hash" size={11} color="#ffffffcc" />
                  <Text style={s.modeMetaText}>K. S. Krishnamurti · Cuspal Interlinks</Text>
                </View>
              </View>
              <Feather name="chevron-right" size={20} color="#fff" />
            </LinearGradient>
          </Pressable>

          {/* Optional: small Divya Prashna link (legacy, less prominent) */}
          <Pressable
            onPress={() => {
              Haptics.selectionAsync();
              if (showDemo) { router.push("/onboarding"); return; }
              router.push("/divya-prashna");
            }}
            style={s.legacyLink}
          >
            <Feather name="clock" size={12} color={C.textMuted} />
            <Text style={[s.legacyLinkText, { color: C.textMuted }]}>
              Time-based Divya Prashna (current moment)
            </Text>
          </Pressable>
        </View>
      )}

      {/* ───── Chat / Prashna Mode ──────────────────────────────────────── */}
      {(mode === "chat" || mode === "prashna") && (<>
      {/* Messages */}
      <FlatList
        ref={listRef}
        data={messages}
        keyExtractor={m => m.id}
        renderItem={renderMsg}
        contentContainerStyle={[s.list, { paddingBottom: 12 }]}
        showsVerticalScrollIndicator={false}
      />

      {/* Starter chips (only chat mode, single init) */}
      {mode === "chat" && messages.length <= 1 && !showDemo && (
        <View style={s.starters}>
          {STARTERS.map(q => (
            <Pressable key={q} style={[s.starter, { backgroundColor: C.bgCard, borderColor: `${C.accent}30` }]} onPress={() => send(q)}>
              <Text style={[s.starterText, { color: C.accent }]}>{q}</Text>
            </Pressable>
          ))}
        </View>
      )}

      {/* ── Prashna number-entry row (above question) ─────────────────── */}
      {mode === "prashna" && (
        <View style={[s.prashnaNumRow, { backgroundColor: C.bg, borderTopColor: C.border }]}>
          <View style={[s.prashnaNumWrap, { backgroundColor: C.bgCard, borderColor: `${C.accent}50` }]}>
            <Feather name="hash" size={14} color={C.accent} />
            <TextInput
              style={[s.prashnaNumInput, { color: C.text }]}
              value={prashnaNumber}
              onChangeText={(v) => setPrashnaNumber(v.replace(/[^0-9]/g, "").slice(0, 3))}
              placeholder="1 — 249"
              placeholderTextColor={C.textMuted}
              keyboardType="number-pad"
              maxLength={3}
              editable={!showDemo && !loading}
            />
          </View>
          <Text style={[s.prashnaNumHint, { color: C.textMuted }]}>
            Sankhya sochiye (lagna nirdharit)
          </Text>
        </View>
      )}

      {/* Input row */}
      <View style={[s.inputRow, { paddingBottom: botPad + 90, backgroundColor: C.bg, borderTopColor: C.border }]}>
        <TextInput
          style={[s.input, { backgroundColor: C.bgCard, borderColor: C.border, color: C.text }]}
          value={input}
          onChangeText={setInput}
          placeholder={mode === "prashna" ? "Apna prashna likhiye (vaikalpik)…" : t.askPlaceholder}
          placeholderTextColor={C.textMuted}
          multiline
          editable={!showDemo}
          onSubmitEditing={() => mode === "prashna" ? sendPrashna(prashnaNumber, input) : send(input)}
          returnKeyType="send"
        />
        <Pressable
          onPress={() => {
            if (showDemo) { router.push("/onboarding"); return; }
            if (mode === "prashna") sendPrashna(prashnaNumber, input);
            else send(input);
          }}
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
      </>)}

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

  modeSwitch: {
    flexDirection: "row",
    marginHorizontal: 16,
    marginTop: 10,
    padding: 4,
    borderRadius: 12,
    borderWidth: 1,
    gap: 4,
  },
  modeSwitchSeg: {
    flex: 1,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 6,
    paddingVertical: 8,
    paddingHorizontal: 8,
    borderRadius: 9,
    borderWidth: 1,
    borderColor: "transparent",
  },
  modeSwitchActive: {},
  modeSwitchText: {
    fontSize: 12,
    fontWeight: "700",
    letterSpacing: 0.2,
  },

  prashnaNumRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderTopWidth: StyleSheet.hairlineWidth,
  },
  prashnaNumWrap: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 10,
    borderWidth: 1.5,
    minWidth: 110,
  },
  prashnaNumInput: {
    fontSize: 16,
    fontWeight: "700",
    letterSpacing: 1,
    minWidth: 60,
    paddingVertical: 0,
  },
  prashnaNumHint: {
    flex: 1,
    fontSize: 11,
    fontStyle: "italic",
  },
  backBtn: {
    position: "absolute", left: 12, top: 0, bottom: 0,
    justifyContent: "center", paddingHorizontal: 4,
  },

  // ── Mode picker ─────────────────────────────────────────────────────────
  pickerWrap: { paddingHorizontal: 16, paddingTop: 28, gap: 14 },
  pickerHi:   { fontSize: 22, fontWeight: "800", letterSpacing: -0.4 },
  pickerSub:  { fontSize: 13, marginBottom: 14 },
  modeCard:   { borderRadius: 18, overflow: "hidden" },
  modeGrad: {
    paddingHorizontal: 18, paddingVertical: 18,
    flexDirection: "row", alignItems: "center", gap: 14,
  },
  modeEmoji: { fontSize: 36 },
  modeTitle: { color: "#fff", fontSize: 18, fontWeight: "800", letterSpacing: -0.3 },
  modeBody:  { color: "#ffffffd0", fontSize: 12.5, lineHeight: 17, marginTop: 4 },
  modeMeta:  { flexDirection: "row", alignItems: "center", gap: 5, marginTop: 8 },
  modeMetaText: { color: "#ffffffcc", fontSize: 10.5, fontWeight: "600" },
  modeBadge: {
    backgroundColor: "rgba(255,255,255,0.22)",
    paddingHorizontal: 7, paddingVertical: 2, borderRadius: 8,
  },
  modeBadgeText: { color: "#fff", fontSize: 9.5, fontWeight: "800", letterSpacing: 0.3 },
  legacyLink: {
    flexDirection: "row", alignItems: "center", justifyContent: "center",
    gap: 6, paddingVertical: 14, marginTop: 4,
  },
  legacyLinkText: { fontSize: 12, fontWeight: "600" },

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
