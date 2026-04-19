import { Feather } from "@expo/vector-icons";
import * as Haptics from "expo-haptics";
import { LinearGradient } from "expo-linear-gradient";
import { router, Stack } from "expo-router";
import React, { useState } from "react";
import {
  ActivityIndicator,
  Alert,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  ScrollView,
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
  lagna?: { sign: string; degree: string; nakshatra?: string; sub_lord?: string };
  verdict?: { code: string; label_hi: string; label_en: string; meaning: string };
  cusp_analysis?: CuspAnalysis[];
  timing?: string;
  narrative?: string;
  classical_refs?: string[];
};

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
  const topPad = Platform.OS === "ios" ? insets.top : 24;

  const [numberStr, setNumberStr] = useState("");
  const [question, setQuestion] = useState("");
  const [category, setCategory] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<Result | null>(null);

  const submit = async () => {
    const n = parseInt(numberStr.trim(), 10);
    if (!n || n < 1 || n > 249) {
      Alert.alert("Invalid number", "Krupya 1 se 249 ke beech sankhya likhein.");
      return;
    }
    setLoading(true);
    setResult(null);
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    try {
      const headers: Record<string, string> = { "Content-Type": "application/json" };
      if (user?.api_key) headers["X-API-Key"] = user.api_key;
      const res = await apiFetch(`${API_BASE}/api/prashna/number-ask`, {
        method: "POST",
        headers,
        body: JSON.stringify({
          number: n,
          question: question.trim(),
          category: category || undefined,
          user_id: user?.id,
        }),
      });
      const json = await res.json().catch(() => ({} as any));
      if (res.status === 402) {
        Alert.alert("Daily limit", json?.message || "Aaj ka prashna limit poora ho gaya.");
        return;
      }
      if (!res.ok) {
        Alert.alert("Error", json?.error || json?.message || "Kuch galti hui — phir try karein.");
        return;
      }
      setResult(json);
      try { Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success); } catch {}
    } catch {
      Alert.alert("Network error", "Internet check karke phir try karein.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <CosmicBg>
      <Stack.Screen options={{ headerShown: false }} />
      <KeyboardAvoidingView style={s.root} behavior={Platform.OS === "ios" ? "padding" : undefined}>
        {/* Header */}
        <View style={[s.header, { paddingTop: topPad + 8, borderBottomColor: C.border }]}>
          <Pressable onPress={() => router.back()} style={s.backBtn} hitSlop={10}>
            <Feather name="chevron-left" size={22} color={C.text} />
            <Text style={{ color: C.text, fontSize: 14, fontWeight: "600" }}>Back</Text>
          </Pressable>
          <View style={{ alignItems: "center" }}>
            <Text style={[s.title, { color: C.text }]}>Prashna Kundli</Text>
            <Text style={[s.sub,   { color: C.textMuted }]}>KP Horary 1-249</Text>
          </View>
          <View style={{ width: 60 }} />
        </View>

        <ScrollView contentContainerStyle={{ padding: 16, paddingBottom: 80 }} keyboardShouldPersistTaps="handled">
          {!result && (
            <>
              {/* Intro card */}
              <LinearGradient
                colors={["#0e7490", "#0891b2"]}
                start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }}
                style={s.intro}
              >
                <Text style={s.introEmoji}>🔢</Text>
                <Text style={s.introTitle}>Mann mein ek number sochiye</Text>
                <Text style={s.introBody}>
                  Aankhein band karke 1 se 249 ke beech jo bhi number sabse pehle aaye, woh likhiye.
                  Wahi sankhya aapki Prashna Kundli ka lagna banegi — cusp ka sub-lord aapko jawab dega.
                </Text>
                <Text style={s.introRef}>
                  Adhar: KP Reader VI (K. S. Krishnamurti) — Cuspal Interlinks Theory
                </Text>
              </LinearGradient>

              {/* Number input */}
              <Text style={[s.label, { color: C.text }]}>Aapki sankhya (1 - 249)</Text>
              <TextInput
                value={numberStr}
                onChangeText={t => setNumberStr(t.replace(/[^0-9]/g, "").slice(0, 3))}
                placeholder="e.g. 137"
                placeholderTextColor={C.textMuted}
                keyboardType="number-pad"
                maxLength={3}
                style={[s.numberInput, {
                  backgroundColor: C.bgCard,
                  borderColor: numberStr ? "#0891b2" : C.border,
                  color: C.text,
                }]}
              />

              {/* Question (optional) */}
              <Text style={[s.label, { color: C.text, marginTop: 18 }]}>
                Aapka prashna <Text style={{ color: C.textMuted, fontWeight: "400" }}>(optional)</Text>
              </Text>
              <TextInput
                value={question}
                onChangeText={setQuestion}
                placeholder="e.g. Mera promotion is saal hoga?"
                placeholderTextColor={C.textMuted}
                multiline
                style={[s.input, { backgroundColor: C.bgCard, borderColor: C.border, color: C.text }]}
              />

              {/* Category chips */}
              <Text style={[s.label, { color: C.text, marginTop: 18 }]}>
                Vargi-karan <Text style={{ color: C.textMuted, fontWeight: "400" }}>(optional)</Text>
              </Text>
              <View style={s.chipRow}>
                {QUICK_CATEGORIES.map(c => {
                  const active = category === c.key;
                  return (
                    <Pressable
                      key={c.key}
                      onPress={() => { setCategory(active ? null : c.key); Haptics.selectionAsync(); }}
                      style={[s.chip, {
                        backgroundColor: active ? "#0891b2" : C.bgCard,
                        borderColor: active ? "#14b8a6" : C.border,
                      }]}
                    >
                      <Text style={{ fontSize: 14 }}>{c.emoji}</Text>
                      <Text style={{ color: active ? "#fff" : C.textMid, fontSize: 12, fontWeight: "600" }}>
                        {c.label_hi}
                      </Text>
                    </Pressable>
                  );
                })}
              </View>

              {/* Submit */}
              <Pressable onPress={submit} disabled={loading || !numberStr} style={{ marginTop: 24 }}>
                <LinearGradient
                  colors={loading || !numberStr ? ["#475569", "#334155"] : ["#0e7490", "#0891b2", "#14b8a6"]}
                  start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }}
                  style={s.cta}
                >
                  {loading ? (
                    <ActivityIndicator color="#fff" />
                  ) : (
                    <>
                      <Feather name="zap" size={16} color="#fff" />
                      <Text style={s.ctaText}>Prashna Kundli Banao</Text>
                    </>
                  )}
                </LinearGradient>
              </Pressable>
            </>
          )}

          {result && (
            <View>
              {/* Reset */}
              <Pressable
                onPress={() => { setResult(null); setNumberStr(""); setQuestion(""); setCategory(null); }}
                style={[s.resetBtn, { borderColor: C.border, backgroundColor: C.bgCard }]}
              >
                <Feather name="refresh-cw" size={13} color={C.textMid} />
                <Text style={{ color: C.textMid, fontSize: 12, fontWeight: "600" }}>Naya prashna</Text>
              </Pressable>

              {/* Caution banner (advisory — verdict still shown below) */}
              {(result.caution || (result as any).validity) && (
                <View style={[s.invalid, { backgroundColor: C.warningBg, borderColor: C.warningBorder }]}>
                  <Feather name="alert-triangle" size={18} color={C.warningText} />
                  <Text style={[s.invalidTitle, { color: C.warningText, fontSize: 13 }]}>
                    Prashna kaal sangya — saavdhani
                  </Text>
                  <Text style={{ color: C.warningText, fontSize: 12, marginTop: 4, textAlign: "center", lineHeight: 17 }}>
                    {result.caution?.reason
                      || (result as any).validity?.reason
                      || (result as any).validity?.message
                      || "Lagna avastha sangya — uttar margdarshan-roop mein lijiye, antim nirnaay nahi."}
                  </Text>
                  {result.caution?.classical_ref && (
                    <Text style={{ color: C.warningText, fontSize: 10, marginTop: 4, opacity: 0.75, fontStyle: "italic" }}>
                      Aadhar: {result.caution.classical_ref}
                    </Text>
                  )}
                </View>
              )}

              {/* Verdict card */}
              {result.verdict && (
                <LinearGradient
                  colors={[`${verdictColor(result.verdict.code)}25`, `${verdictColor(result.verdict.code)}10`]}
                  start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }}
                  style={[s.verdict, { borderColor: `${verdictColor(result.verdict.code)}60` }]}
                >
                  <Text style={[s.verdictNum, { color: C.textMuted }]}>Sankhya: {result.number}</Text>
                  <Text style={[s.verdictLabel, { color: verdictColor(result.verdict.code) }]}>
                    {result.verdict.label_hi}
                  </Text>
                  <Text style={[s.verdictMeaning, { color: C.text }]}>{result.verdict.meaning}</Text>
                </LinearGradient>
              )}

              {/* Lagna */}
              {result.lagna && (
                <View style={[s.box, { backgroundColor: C.bgCard, borderColor: C.border }]}>
                  <Text style={[s.boxTitle, { color: C.text }]}>Forced Lagna (your number → ascendant)</Text>
                  <Text style={[s.boxLine, { color: C.textMid }]}>
                    Rashi: <Text style={{ color: C.text, fontWeight: "700" }}>{result.lagna.sign}</Text>  ·  {result.lagna.degree}
                  </Text>
                  {result.lagna.nakshatra && (
                    <Text style={[s.boxLine, { color: C.textMid }]}>
                      Nakshatra: <Text style={{ color: C.text, fontWeight: "700" }}>{result.lagna.nakshatra}</Text>
                    </Text>
                  )}
                  {result.lagna.sub_lord && (
                    <Text style={[s.boxLine, { color: C.textMid }]}>
                      Sub-Lord: <Text style={{ color: C.text, fontWeight: "700" }}>{result.lagna.sub_lord}</Text>
                    </Text>
                  )}
                </View>
              )}

              {/* Cusp analysis */}
              {result.cusp_analysis && result.cusp_analysis.length > 0 && (
                <View style={[s.box, { backgroundColor: C.bgCard, borderColor: C.border }]}>
                  <Text style={[s.boxTitle, { color: C.text }]}>Cusp Analysis (KP Sub-Lord)</Text>
                  {result.cusp_analysis.map((cv, i) => (
                    <View key={i} style={{ marginTop: i === 0 ? 4 : 10 }}>
                      <Text style={[s.boxLine, { color: C.text, fontWeight: "700" }]}>
                        {cv.house}{cv.house === 1 ? "st" : cv.house === 2 ? "nd" : cv.house === 3 ? "rd" : "th"} House  ·  {cv.sign} {cv.degree}
                      </Text>
                      <Text style={[s.boxLine, { color: C.textMid }]}>
                        Sub-Lord: <Text style={{ color: C.text, fontWeight: "600" }}>{cv.sub_lord}</Text>  →  signifies houses [{cv.signifies.join(", ")}]
                      </Text>
                      <Text style={[s.boxLine, { color: C.textMid }]}>
                        +{cv.pos_hits.length > 0 ? cv.pos_hits.join(",") : "—"}  /  -{cv.neg_hits.length > 0 ? cv.neg_hits.join(",") : "—"}  →  <Text style={{ color: verdictColor(cv.verdict), fontWeight: "700" }}>{cv.verdict}</Text>
                      </Text>
                    </View>
                  ))}
                </View>
              )}

              {/* Timing */}
              {result.timing && (
                <View style={[s.box, { backgroundColor: C.bgCard, borderColor: C.border }]}>
                  <Text style={[s.boxTitle, { color: C.text }]}>⏳ Samay (Timing)</Text>
                  <Text style={[s.boxLine, { color: C.textMid }]}>{result.timing}</Text>
                </View>
              )}

              {/* Classical refs */}
              {result.classical_refs && result.classical_refs.length > 0 && (
                <View style={[s.box, { backgroundColor: C.bgCard, borderColor: C.border }]}>
                  <Text style={[s.boxTitle, { color: C.text }]}>📜 Shastriya Adhar</Text>
                  {result.classical_refs.map((ref, i) => (
                    <Text key={i} style={[s.boxLine, { color: C.textMid, fontStyle: "italic" }]}>• {ref}</Text>
                  ))}
                </View>
              )}
            </View>
          )}
        </ScrollView>
      </KeyboardAvoidingView>
    </CosmicBg>
  );
}

const s = StyleSheet.create({
  root: { flex: 1 },
  header: {
    flexDirection: "row", alignItems: "center", justifyContent: "space-between",
    paddingHorizontal: 12, paddingBottom: 12,
    borderBottomWidth: 1,
  },
  backBtn: { flexDirection: "row", alignItems: "center", gap: 2, width: 60 },
  title: { fontSize: 16, fontWeight: "700" },
  sub:   { fontSize: 11, marginTop: 1 },

  intro: {
    borderRadius: 16, padding: 18, marginBottom: 22, alignItems: "center",
  },
  introEmoji: { fontSize: 32, marginBottom: 6 },
  introTitle: { color: "#fff", fontSize: 16, fontWeight: "800", textAlign: "center" },
  introBody:  { color: "#ffffffd0", fontSize: 12.5, lineHeight: 18, marginTop: 8, textAlign: "center" },
  introRef:   { color: "#ffffff90", fontSize: 10.5, marginTop: 10, fontStyle: "italic", textAlign: "center" },

  label: { fontSize: 13, fontWeight: "700", marginBottom: 8 },

  numberInput: {
    borderWidth: 1.5, borderRadius: 14, paddingHorizontal: 18, paddingVertical: 16,
    fontSize: 22, fontWeight: "700", textAlign: "center", letterSpacing: 4,
  },
  input: {
    borderWidth: 1, borderRadius: 12, paddingHorizontal: 14, paddingVertical: 12,
    fontSize: 13, minHeight: 60, textAlignVertical: "top",
  },

  chipRow: { flexDirection: "row", flexWrap: "wrap", gap: 8 },
  chip: {
    flexDirection: "row", alignItems: "center", gap: 6,
    paddingHorizontal: 12, paddingVertical: 8, borderRadius: 20, borderWidth: 1,
  },

  cta: {
    flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 8,
    paddingVertical: 15, borderRadius: 14,
  },
  ctaText: { color: "#fff", fontSize: 15, fontWeight: "800" },

  resetBtn: {
    flexDirection: "row", alignItems: "center", gap: 6,
    paddingHorizontal: 12, paddingVertical: 8, borderRadius: 20, borderWidth: 1,
    alignSelf: "flex-start", marginBottom: 14,
  },

  verdict: {
    borderWidth: 1.5, borderRadius: 16, padding: 20, marginBottom: 14, alignItems: "center",
  },
  verdictNum:     { fontSize: 11, fontWeight: "700", letterSpacing: 1, marginBottom: 6 },
  verdictLabel:   { fontSize: 26, fontWeight: "800", letterSpacing: -0.5, textAlign: "center" },
  verdictMeaning: { fontSize: 13, marginTop: 8, textAlign: "center", lineHeight: 19 },

  invalid: {
    borderWidth: 1, borderRadius: 14, padding: 16, marginBottom: 14, alignItems: "center",
  },
  invalidTitle: { fontSize: 13, fontWeight: "700", marginTop: 6, textAlign: "center" },

  box: {
    borderWidth: 1, borderRadius: 14, padding: 14, marginBottom: 12,
  },
  boxTitle: { fontSize: 13, fontWeight: "700", marginBottom: 8 },
  boxLine:  { fontSize: 12.5, lineHeight: 18, marginTop: 2 },
});
