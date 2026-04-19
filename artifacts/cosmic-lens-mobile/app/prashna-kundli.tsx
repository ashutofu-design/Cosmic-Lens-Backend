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
import { API_BASE, apiFetch } from "@/lib/apiConfig";

type Category = { key: string; label_hi: string; emoji: string };

const QUICK_CATEGORIES: Category[] = [
  { key: "stolen_item",      label_hi: "Saaman milega?", emoji: "💰" },
  { key: "partner_feelings", label_hi: "Partner feelings", emoji: "💔" },
  { key: "job",              label_hi: "Naukri lagegi?",  emoji: "💼" },
  { key: "marriage",         label_hi: "Shaadi kab?",     emoji: "💍" },
  { key: "health",           label_hi: "Bimari theek?",   emoji: "🏥" },
  { key: "litigation",       label_hi: "Mukadma jeet?",   emoji: "⚖️" },
  { key: "travel",           label_hi: "Yatra hogi?",     emoji: "✈️" },
  { key: "general",          label_hi: "Aam sawaal",      emoji: "🔮" },
];

type CuspAnalysis = {
  house: number;
  sub_lord: string;
  sign: string;
  degree: string;
  signifies: number[];
  pos_hits: number[];
  neg_hits: number[];
  verdict: string;
};

type Result = {
  ok: boolean;
  number?: number;
  question?: string;
  category_label?: string;
  reason?: string;
  message?: string;
  validity?: { valid: boolean; reason?: string; message?: string };
  caution?: { reason?: string; classical_ref?: string };
  lagna?: { sign: string; degree: string; nakshatra?: string; sub_lord?: string };
  verdict?: { code: string; label_hi: string; label_en: string; meaning: string };
  cusp_analysis?: CuspAnalysis[];
  timing?: string;
  narrative?: string;
  classical_refs?: string[];
};

type Bubble =
  | { id: string; kind: "assistant-text"; text: string }
  | { id: string; kind: "user-query"; number: number; question?: string; category?: string }
  | { id: string; kind: "result"; data: Result }
  | { id: string; kind: "thinking" };

const verdictColor = (code?: string) => {
  if (!code) return "#94a3b8";
  if (code.startsWith("YES")) return "#22c55e";
  if (code.startsWith("NO"))  return "#ef4444";
  return "#f59e0b";
};

export default function PrashnaKundliScreen() {
  const insets = useSafeAreaInsets();
  const C = useC();
  const { user } = useUser();
  const androidSB = Platform.OS === "android" ? 24 : 0;
  const topPad = Platform.OS === "ios" ? insets.top : androidSB;
  const botPad = Platform.OS === "web" ? 24 : insets.bottom;

  const [numberStr, setNumberStr] = useState("");
  const [question, setQuestion]   = useState("");
  const [category, setCategory]   = useState<string | null>(null);
  const [loading, setLoading]     = useState(false);
  const [bubbles, setBubbles]     = useState<Bubble[]>([
    {
      id: "init",
      kind: "assistant-text",
      text:
        "🔢 Pranam! Mann ko shant karke 1 se 249 ke beech jo number sabse pehle aaye, woh neeche likhiye. Apna prashna bhi sath mein likh sakte hain (vaikalpik). Wahi sankhya aapki Prashna Kundli ka lagna banegi.",
    },
  ]);
  const listRef = useRef<FlatList<Bubble>>(null);

  useEffect(() => {
    setTimeout(() => listRef.current?.scrollToEnd({ animated: true }), 80);
  }, [bubbles]);

  const submit = useCallback(async () => {
    if (loading) return;
    const n = parseInt(numberStr.trim(), 10);
    if (!Number.isFinite(n) || n < 1 || n > 249) {
      setBubbles(prev => [...prev, {
        id: Date.now().toString(),
        kind: "assistant-text",
        text: "⚠️ Number 1 se 249 ke beech hona chahiye. Ek baar aur sochiye.",
      }]);
      return;
    }

    const q = question.trim();
    const cat = category;

    setBubbles(prev => [
      ...prev,
      { id: `u-${Date.now()}`, kind: "user-query", number: n, question: q, category: cat || undefined },
      { id: "thinking", kind: "thinking" },
    ]);
    setNumberStr("");
    setQuestion("");
    setCategory(null);
    setLoading(true);
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);

    try {
      const headers: Record<string, string> = { "Content-Type": "application/json" };
      if (user?.api_key) headers["X-API-Key"] = user.api_key;
      const res = await apiFetch(`${API_BASE}/api/prashna/number-ask`, {
        method: "POST",
        headers,
        body: JSON.stringify({
          number: n,
          question: q,
          category: cat || undefined,
          user_id: user?.id,
        }),
      });
      const json = await res.json().catch(() => ({} as any));

      if (res.status === 402) {
        setBubbles(prev => prev.filter(b => b.id !== "thinking").concat({
          id: Date.now().toString(),
          kind: "assistant-text",
          text: `⛔ ${json?.message || "Aaj ka prashna limit poora ho gaya. Subscription upgrade karein."}`,
        }));
        return;
      }
      if (!res.ok) {
        setBubbles(prev => prev.filter(b => b.id !== "thinking").concat({
          id: Date.now().toString(),
          kind: "assistant-text",
          text: `⚠️ ${json?.error || json?.message || "Kuch galti hui — phir try karein."}`,
        }));
        return;
      }

      setBubbles(prev => prev.filter(b => b.id !== "thinking").concat({
        id: Date.now().toString(),
        kind: "result",
        data: json,
      }));
      try { Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success); } catch {}
    } catch {
      setBubbles(prev => prev.filter(b => b.id !== "thinking").concat({
        id: Date.now().toString(),
        kind: "assistant-text",
        text: "📡 Network error — internet check karke phir try karein.",
      }));
    } finally {
      setLoading(false);
    }
  }, [loading, numberStr, question, category, user?.id, user?.api_key]);

  const renderBubble = ({ item }: { item: Bubble }) => {
    if (item.kind === "thinking") {
      return (
        <View style={[s.bubble, s.bubbleAssistant]}>
          <View style={[s.avatar, { backgroundColor: C.accentBg, borderColor: `${C.accent}30` }]}>
            <Text style={{ fontSize: 12 }}>🔢</Text>
          </View>
          <View style={[s.bubbleInner, { backgroundColor: C.bgCard, borderColor: C.border }]}>
            <ActivityIndicator size="small" color={C.accent} />
          </View>
        </View>
      );
    }
    if (item.kind === "assistant-text") {
      return (
        <View style={[s.bubble, s.bubbleAssistant]}>
          <View style={[s.avatar, { backgroundColor: C.accentBg, borderColor: `${C.accent}30` }]}>
            <Text style={{ fontSize: 12 }}>🔢</Text>
          </View>
          <View style={[s.bubbleInner, { backgroundColor: C.bgCard, borderColor: C.border }]}>
            <Text style={[s.bubbleText, { color: C.textMid }]}>{item.text}</Text>
          </View>
        </View>
      );
    }
    if (item.kind === "user-query") {
      const catLabel = item.category ? QUICK_CATEGORIES.find(c => c.key === item.category)?.label_hi : null;
      return (
        <View style={[s.bubble, s.bubbleUser]}>
          <View style={[s.bubbleInner, s.bubbleInnerUser, { backgroundColor: C.isDark ? "#0e3a4d" : "#cffafe", borderColor: "#0891b260" }]}>
            <Text style={[s.bubbleText, { color: C.text, fontWeight: "700" }]}>🔢 Sankhya: {item.number}</Text>
            {!!item.question && <Text style={[s.bubbleText, { color: C.textMid, marginTop: 4 }]}>{item.question}</Text>}
            {!!catLabel && <Text style={[s.bubbleText, { color: C.textMuted, marginTop: 4, fontSize: 11 }]}>📌 {catLabel}</Text>}
          </View>
        </View>
      );
    }
    // result bubble
    const r = item.data;
    return (
      <View style={[s.bubble, s.bubbleAssistant]}>
        <View style={[s.avatar, { backgroundColor: C.accentBg, borderColor: `${C.accent}30` }]}>
          <Text style={{ fontSize: 12 }}>🔢</Text>
        </View>
        <View style={s.resultStack}>
          {(r.caution || (r as any).validity) && (
            <View style={[s.invalid, { backgroundColor: C.warningBg, borderColor: C.warningBorder }]}>
              <Feather name="alert-triangle" size={16} color={C.warningText} />
              <Text style={[s.invalidTitle, { color: C.warningText }]}>Prashna kaal — saavdhani</Text>
              <Text style={{ color: C.warningText, fontSize: 11.5, marginTop: 4, textAlign: "center", lineHeight: 16 }}>
                {r.caution?.reason || (r as any).validity?.reason || (r as any).validity?.message || "Margdarshan-roop mein lijiye, antim nirnaay nahi."}
              </Text>
              {r.caution?.classical_ref && (
                <Text style={{ color: C.warningText, fontSize: 10, marginTop: 4, opacity: 0.7, fontStyle: "italic" }}>
                  Aadhar: {r.caution.classical_ref}
                </Text>
              )}
            </View>
          )}

          {r.verdict && (
            <LinearGradient
              colors={[`${verdictColor(r.verdict.code)}25`, `${verdictColor(r.verdict.code)}10`]}
              start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }}
              style={[s.verdict, { borderColor: `${verdictColor(r.verdict.code)}60` }]}
            >
              <Text style={[s.verdictNum, { color: C.textMuted }]}>Sankhya: {r.number}</Text>
              <Text style={[s.verdictLabel, { color: verdictColor(r.verdict.code) }]}>{r.verdict.label_hi}</Text>
              <Text style={[s.verdictMeaning, { color: C.text }]}>{r.verdict.meaning}</Text>
            </LinearGradient>
          )}

          {r.lagna && (
            <View style={[s.box, { backgroundColor: C.bgCard, borderColor: C.border }]}>
              <Text style={[s.boxTitle, { color: C.text }]}>Forced Lagna</Text>
              <Text style={[s.boxLine, { color: C.textMid }]}>
                Rashi: <Text style={{ color: C.text, fontWeight: "700" }}>{r.lagna.sign}</Text> · {r.lagna.degree}
              </Text>
              {!!r.lagna.nakshatra && (
                <Text style={[s.boxLine, { color: C.textMid }]}>
                  Nakshatra: <Text style={{ color: C.text, fontWeight: "700" }}>{r.lagna.nakshatra}</Text>
                </Text>
              )}
              {!!r.lagna.sub_lord && (
                <Text style={[s.boxLine, { color: C.textMid }]}>
                  Sub-Lord: <Text style={{ color: C.text, fontWeight: "700" }}>{r.lagna.sub_lord}</Text>
                </Text>
              )}
            </View>
          )}

          {r.cusp_analysis && r.cusp_analysis.length > 0 && (
            <View style={[s.box, { backgroundColor: C.bgCard, borderColor: C.border }]}>
              <Text style={[s.boxTitle, { color: C.text }]}>Cusp Analysis (KP Sub-Lord)</Text>
              {r.cusp_analysis.map((cv, i) => (
                <View key={i} style={{ marginTop: i === 0 ? 4 : 10 }}>
                  <Text style={[s.boxLine, { color: C.text, fontWeight: "700" }]}>
                    {cv.house}{cv.house === 1 ? "st" : cv.house === 2 ? "nd" : cv.house === 3 ? "rd" : "th"} House · {cv.sign} {cv.degree}
                  </Text>
                  <Text style={[s.boxLine, { color: C.textMid }]}>
                    Sub-Lord: <Text style={{ color: C.text, fontWeight: "600" }}>{cv.sub_lord}</Text> → [{cv.signifies.join(", ")}]
                  </Text>
                  <Text style={[s.boxLine, { color: C.textMid }]}>
                    +{cv.pos_hits.length ? cv.pos_hits.join(",") : "—"} / -{cv.neg_hits.length ? cv.neg_hits.join(",") : "—"} → <Text style={{ color: verdictColor(cv.verdict), fontWeight: "700" }}>{cv.verdict}</Text>
                  </Text>
                </View>
              ))}
            </View>
          )}

          {!!r.timing && (
            <View style={[s.box, { backgroundColor: C.bgCard, borderColor: C.border }]}>
              <Text style={[s.boxTitle, { color: C.text }]}>⏳ Samay (Timing)</Text>
              <Text style={[s.boxLine, { color: C.textMid }]}>{r.timing}</Text>
            </View>
          )}

          {r.classical_refs && r.classical_refs.length > 0 && (
            <View style={[s.box, { backgroundColor: C.bgCard, borderColor: C.border }]}>
              <Text style={[s.boxTitle, { color: C.text }]}>📜 Shastriya Adhar</Text>
              {r.classical_refs.map((ref, i) => (
                <Text key={i} style={[s.boxLine, { color: C.textMid, fontStyle: "italic" }]}>• {ref}</Text>
              ))}
            </View>
          )}
        </View>
      </View>
    );
  };

  const hasOnlyInit = bubbles.length === 1 && bubbles[0].kind === "assistant-text";

  return (
    <CosmicBg>
      <Stack.Screen options={{ headerShown: false }} />
      <KeyboardAvoidingView
        style={s.root}
        behavior={Platform.OS === "ios" ? "padding" : "height"}
      >
        {/* Header */}
        <View style={[s.header, { paddingTop: topPad + 12, borderBottomColor: C.border }]}>
          <Pressable onPress={() => router.back()} style={s.backBtn} hitSlop={10}>
            <Feather name="chevron-left" size={20} color={C.text} />
          </Pressable>
          <View style={s.headerDot} />
          <Text style={[s.headerTitle, { color: C.text }]}>Prashna Kundli</Text>
          <Text style={[s.headerSub, { color: C.textMuted }]}>KP Horary 1-249 · Cuspal Interlinks</Text>
        </View>

        {/* Mode switcher pill */}
        <View style={[s.modeSwitch, { backgroundColor: (C as any).bgCard2 ?? C.bgCard, borderColor: C.border }]}>
          <Pressable
            onPress={() => { Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light); router.back(); }}
            style={({ pressed }) => [s.modeSwitchSeg, pressed && { opacity: 0.7 }]}
          >
            <Feather name="message-circle" size={13} color={C.textMuted} />
            <Text style={[s.modeSwitchText, { color: C.textMuted }]}>Ask Anything</Text>
          </Pressable>
          <View style={[s.modeSwitchSeg, { backgroundColor: C.accentBg, borderColor: `${C.accent}80` }]}>
            <Feather name="hash" size={13} color={C.accent} />
            <Text style={[s.modeSwitchText, { color: C.accent }]}>Prashna Kundli</Text>
          </View>
        </View>

        {/* Messages */}
        <FlatList
          ref={listRef}
          data={bubbles}
          keyExtractor={b => b.id}
          renderItem={renderBubble}
          contentContainerStyle={[s.list, { paddingBottom: 12 }]}
          showsVerticalScrollIndicator={false}
        />

        {/* Category starter chips (only when fresh) */}
        {hasOnlyInit && (
          <View style={s.starters}>
            {QUICK_CATEGORIES.map(c => (
              <Pressable
                key={c.key}
                onPress={() => {
                  setCategory(category === c.key ? null : c.key);
                  Haptics.selectionAsync();
                }}
                style={[s.chip, {
                  backgroundColor: category === c.key ? "#0891b2" : C.bgCard,
                  borderColor: category === c.key ? "#14b8a6" : `${C.accent}30`,
                }]}
              >
                <Text style={{ fontSize: 12 }}>{c.emoji}</Text>
                <Text style={{ color: category === c.key ? "#fff" : C.accent, fontSize: 11.5, fontWeight: "600" }}>
                  {c.label_hi}
                </Text>
              </Pressable>
            ))}
          </View>
        )}

        {/* Number entry row (just above question input) */}
        <View style={[s.numRow, { backgroundColor: C.bg, borderTopColor: C.border }]}>
          <View style={[s.numWrap, { backgroundColor: C.bgCard, borderColor: numberStr ? "#0891b2" : `${C.accent}50` }]}>
            <Feather name="hash" size={14} color={C.accent} />
            <TextInput
              style={[s.numInput, { color: C.text }]}
              value={numberStr}
              onChangeText={(v) => setNumberStr(v.replace(/[^0-9]/g, "").slice(0, 3))}
              placeholder="1 — 249"
              placeholderTextColor={C.textMuted}
              keyboardType="number-pad"
              maxLength={3}
              editable={!loading}
            />
          </View>
          <Text style={[s.numHint, { color: C.textMuted }]}>
            Sankhya sochiye{category ? ` · ${QUICK_CATEGORIES.find(c => c.key === category)?.label_hi}` : ""}
          </Text>
          {category && (
            <Pressable onPress={() => { setCategory(null); Haptics.selectionAsync(); }} hitSlop={8}>
              <Feather name="x-circle" size={14} color={C.textMuted} />
            </Pressable>
          )}
        </View>

        {/* Question + Send */}
        <View style={[s.inputRow, { paddingBottom: botPad + 12, backgroundColor: C.bg, borderTopColor: C.border }]}>
          <TextInput
            style={[s.input, { backgroundColor: C.bgCard, borderColor: C.border, color: C.text }]}
            value={question}
            onChangeText={setQuestion}
            placeholder="Apna prashna likhiye (vaikalpik)…"
            placeholderTextColor={C.textMuted}
            multiline
            editable={!loading}
            onSubmitEditing={submit}
            returnKeyType="send"
          />
          <Pressable onPress={submit} disabled={loading || !numberStr} style={({ pressed }) => [s.sendBtn, pressed && { opacity: 0.7 }]}>
            <LinearGradient
              colors={loading || !numberStr ? ["#475569", "#334155"] : ["#0e7490", "#0891b2", "#14b8a6"]}
              start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }}
              style={s.sendGrad}
            >
              {loading
                ? <ActivityIndicator color="#fff" size="small" />
                : <Feather name="send" size={16} color="#fff" />}
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
    alignItems: "center",
    paddingHorizontal: 12, paddingBottom: 10,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  backBtn: {
    position: "absolute", left: 12, top: 0, bottom: 0,
    justifyContent: "center", paddingHorizontal: 4,
  },
  headerDot: {
    width: 8, height: 8, borderRadius: 4, backgroundColor: "#22c55e", marginBottom: 4,
  },
  headerTitle: { fontSize: 16, fontWeight: "700" },
  headerSub:   { fontSize: 11, marginTop: 1 },

  modeSwitch: {
    flexDirection: "row",
    marginHorizontal: 16, marginTop: 10,
    padding: 4, borderRadius: 12, borderWidth: 1, gap: 4,
  },
  modeSwitchSeg: {
    flex: 1, flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 6,
    paddingVertical: 8, paddingHorizontal: 8,
    borderRadius: 9, borderWidth: 1, borderColor: "transparent",
  },
  modeSwitchText: { fontSize: 12, fontWeight: "700", letterSpacing: 0.2 },

  list: { paddingHorizontal: 12, paddingTop: 10, gap: 8 },

  bubble: { flexDirection: "row", alignItems: "flex-end", marginBottom: 8, gap: 6 },
  bubbleAssistant: { justifyContent: "flex-start" },
  bubbleUser: { justifyContent: "flex-end" },
  avatar: {
    width: 28, height: 28, borderRadius: 14,
    alignItems: "center", justifyContent: "center", borderWidth: 1,
  },
  bubbleInner: {
    maxWidth: "78%", paddingHorizontal: 12, paddingVertical: 10,
    borderRadius: 14, borderWidth: 1,
  },
  bubbleInnerUser: { borderTopRightRadius: 4 },
  bubbleText: { fontSize: 13, lineHeight: 18 },

  resultStack: { flex: 1, gap: 10 },

  starters: {
    flexDirection: "row", flexWrap: "wrap", gap: 6,
    paddingHorizontal: 12, paddingTop: 4, paddingBottom: 6,
  },
  chip: {
    flexDirection: "row", alignItems: "center", gap: 5,
    paddingHorizontal: 10, paddingVertical: 6, borderRadius: 16, borderWidth: 1,
  },

  numRow: {
    flexDirection: "row", alignItems: "center", gap: 10,
    paddingHorizontal: 16, paddingVertical: 8,
    borderTopWidth: StyleSheet.hairlineWidth,
  },
  numWrap: {
    flexDirection: "row", alignItems: "center", gap: 6,
    paddingHorizontal: 12, paddingVertical: 8,
    borderRadius: 10, borderWidth: 1.5, minWidth: 110,
  },
  numInput: {
    fontSize: 16, fontWeight: "700", letterSpacing: 1, minWidth: 60, paddingVertical: 0,
  },
  numHint: { flex: 1, fontSize: 11, fontStyle: "italic" },

  inputRow: {
    flexDirection: "row", alignItems: "flex-end", gap: 8,
    paddingHorizontal: 12, paddingTop: 8,
    borderTopWidth: StyleSheet.hairlineWidth,
  },
  input: {
    flex: 1, borderWidth: 1, borderRadius: 18,
    paddingHorizontal: 14, paddingVertical: 10,
    fontSize: 13.5, maxHeight: 100, minHeight: 40,
  },
  sendBtn: { borderRadius: 20, overflow: "hidden" },
  sendGrad: {
    width: 40, height: 40, borderRadius: 20,
    alignItems: "center", justifyContent: "center",
  },

  verdict: {
    borderWidth: 1.5, borderRadius: 16, padding: 18, alignItems: "center",
  },
  verdictNum:     { fontSize: 11, fontWeight: "700", letterSpacing: 1, marginBottom: 6 },
  verdictLabel:   { fontSize: 24, fontWeight: "800", letterSpacing: -0.5, textAlign: "center" },
  verdictMeaning: { fontSize: 13, marginTop: 6, textAlign: "center", lineHeight: 18 },

  invalid: {
    borderWidth: 1, borderRadius: 12, padding: 12, alignItems: "center",
  },
  invalidTitle: { fontSize: 12.5, fontWeight: "700", marginTop: 4 },

  box: { borderWidth: 1, borderRadius: 12, padding: 12 },
  boxTitle: { fontSize: 12.5, fontWeight: "700", marginBottom: 6 },
  boxLine:  { fontSize: 12, lineHeight: 17, marginTop: 2 },
});
