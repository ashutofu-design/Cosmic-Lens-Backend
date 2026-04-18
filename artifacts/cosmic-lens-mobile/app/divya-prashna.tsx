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
import { API_BASE } from "@/lib/apiConfig";

type Category = {
  key: string;
  label_hi: string;
  emoji: string;
};

const QUICK_CATEGORIES: Category[] = [
  { key: "stolen_item",      label_hi: "Sona / saaman milega?", emoji: "💰" },
  { key: "partner_feelings", label_hi: "Partner ke feelings",   emoji: "💔" },
  { key: "job",              label_hi: "Naukri lagegi?",        emoji: "💼" },
  { key: "marriage",         label_hi: "Shaadi kab?",           emoji: "💍" },
  { key: "health",           label_hi: "Bimari theek hogi?",    emoji: "🏥" },
  { key: "litigation",       label_hi: "Mukadma jeetenge?",     emoji: "⚖️" },
  { key: "travel",           label_hi: "Yatra hogi?",           emoji: "✈️" },
  { key: "general",          label_hi: "Aam sawaal",            emoji: "🔮" },
];

const CATEGORY_PROMPTS: Record<string, string> = {
  stolen_item:      "Mera sona / paisa chori ho gaya, wapas milega ya nahi?",
  partner_feelings: "Mera partner mere bare me abhi kya soch raha hai?",
  job:              "Mujhe yeh job / naya role milega ya nahi?",
  marriage:         "Meri shaadi kab tak ho jayegi?",
  health:           "Meri / mere apno ki bimari theek hogi?",
  litigation:       "Mera mukadma main jeetunga ya nahi?",
  travel:           "Meri planned yatra sampann hogi?",
  general:          "",
};

type CuspAnalysis = {
  house: number;
  sub_lord: string;
  star_lord: string;
  sign: string;
  degree: string;
  signifies: number[];
  pos_hits: number[];
  neg_hits: number[];
  verdict: string;
};

type PrashnaResult = {
  ok: boolean;
  reason?: string;
  validity?: { reason: string; classical_ref: string; retry_after_min: number };
  question?: string;
  category?: string;
  category_label?: string;
  place?: { name: string; state: string };
  timestamp?: string;
  lagna?: { sign: string; degree: string };
  verdict?: { code: string; label_hi: string; label_en: string; meaning: string };
  cusp_analysis?: CuspAnalysis[];
  timing?: string;
  narrative?: string;
  classical_refs?: string[];
};

export default function DivyaPrashnaScreen() {
  const c       = useC();
  const insets  = useSafeAreaInsets();
  const { user } = useUser();

  const [question, setQuestion] = useState("");
  const [category, setCategory] = useState<string | undefined>(undefined);
  const [loading,  setLoading]  = useState(false);
  const [result,   setResult]   = useState<PrashnaResult | null>(null);
  const [errMsg,   setErrMsg]   = useState<string | null>(null);

  const ask = async () => {
    const q = question.trim();
    if (!q) {
      Alert.alert("Sawaal likhein", "Kya pucchna chahte ho woh likhein.");
      return;
    }
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    setLoading(true);
    setResult(null);
    setErrMsg(null);
    try {
      const ctrl  = new AbortController();
      const timer = setTimeout(() => ctrl.abort(), 30000);
      const headers: Record<string, string> = { "Content-Type": "application/json" };
      if (user?.api_key) headers["X-API-Key"] = user.api_key;
      const body: Record<string, unknown> = { question: q, category };
      if (user?.id) body.user_id = user.id;

      const resp  = await fetch(`${API_BASE}/api/prashna/ask`, {
        method:  "POST",
        headers,
        body:    JSON.stringify(body),
        signal:  ctrl.signal,
      });
      clearTimeout(timer);
      const json = (await resp.json()) as PrashnaResult & {
        error?: string; message?: string; upgrade_required?: boolean;
      };

      // Quota / auth / server errors
      if (resp.status === 402 || json.upgrade_required) {
        setErrMsg(json.message || "Aaj ka prashna limit poora ho gaya. Pro upgrade karein.");
        Haptics.notificationAsync(Haptics.NotificationFeedbackType.Warning);
        return;
      }
      if (resp.status === 401) {
        setErrMsg("Session khatm ho gayi. Punah login karein.");
        Haptics.notificationAsync(Haptics.NotificationFeedbackType.Warning);
        return;
      }
      if (!resp.ok) {
        setErrMsg(json.message || json.error || "Jawab nahi mil saka. Punah prayaas karein.");
        Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
        return;
      }

      setResult(json);
      if (json.ok) {
        Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      } else {
        Haptics.notificationAsync(Haptics.NotificationFeedbackType.Warning);
      }
    } catch (e: any) {
      setErrMsg(e?.message || "Jawab nahi mil saka. Punah prayaas karein.");
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
    } finally {
      setLoading(false);
    }
  };

  const pickCategory = (cat: Category) => {
    Haptics.selectionAsync();
    setCategory(cat.key);
    setQuestion(CATEGORY_PROMPTS[cat.key] || "");
  };

  const verdictColor = (code?: string) => {
    if (!code) return "#a78bfa";
    if (code.startsWith("YES"))      return "#10b981";
    if (code.startsWith("NO"))       return "#ef4444";
    return "#f59e0b";
  };

  return (
    <CosmicBg>
      <Stack.Screen options={{ headerShown: false }} />
      <View style={[styles.header, { paddingTop: insets.top + 8 }]}>
        <Pressable onPress={() => router.back()} hitSlop={10} style={styles.backBtn}>
          <Feather name="chevron-left" size={28} color={c.text} />
        </Pressable>
        <View style={{ flex: 1 }}>
          <Text style={[styles.title, { color: c.text }]}>🔮 Divya Prashna</Text>
          <Text style={[styles.subtitle, { color: c.text + "99" }]}>
            Apna sawaal pucho — turant Vedic jawab
          </Text>
        </View>
      </View>

      <KeyboardAvoidingView
        style={{ flex: 1 }}
        behavior={Platform.OS === "ios" ? "padding" : undefined}
      >
        <ScrollView
          contentContainerStyle={{ padding: 16, paddingBottom: insets.bottom + 100 }}
          keyboardShouldPersistTaps="handled"
        >
          {/* Place + time strip */}
          <View style={[styles.metaStrip, { backgroundColor: c.text + "10" }]}>
            <Feather name="map-pin" size={14} color={c.text + "99"} />
            <Text style={[styles.metaText, { color: c.text + "cc" }]}>
              Bhubaneswar, Odisha · Server time
            </Text>
          </View>

          {/* Quick category chips */}
          <Text style={[styles.sectionLabel, { color: c.text }]}>Quick sawaal</Text>
          <View style={styles.chipsRow}>
            {QUICK_CATEGORIES.map((cat) => {
              const active = category === cat.key;
              return (
                <Pressable
                  key={cat.key}
                  onPress={() => pickCategory(cat)}
                  style={[
                    styles.chip,
                    {
                      backgroundColor: active ? c.text + "22" : c.text + "0a",
                      borderColor:     active ? c.text + "55" : c.text + "1a",
                    },
                  ]}
                >
                  <Text style={styles.chipEmoji}>{cat.emoji}</Text>
                  <Text style={[styles.chipText, { color: c.text }]} numberOfLines={1}>
                    {cat.label_hi}
                  </Text>
                </Pressable>
              );
            })}
          </View>

          {/* Question input */}
          <Text style={[styles.sectionLabel, { color: c.text, marginTop: 18 }]}>
            Ya apna sawaal type karo
          </Text>
          <TextInput
            value={question}
            onChangeText={setQuestion}
            placeholder="Jaise: Mera kho gaya phone milega kya?"
            placeholderTextColor={c.text + "55"}
            multiline
            style={[
              styles.input,
              {
                backgroundColor: c.text + "08",
                borderColor:     c.text + "22",
                color:           c.text,
              },
            ]}
          />

          {/* Submit */}
          <Pressable
            onPress={ask}
            disabled={loading}
            style={({ pressed }) => [
              styles.submitWrap,
              { opacity: loading ? 0.6 : pressed ? 0.85 : 1 },
            ]}
          >
            <LinearGradient
              colors={["#7c3aed", "#a855f7", "#ec4899"]}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 1 }}
              style={styles.submitBtn}
            >
              {loading ? (
                <ActivityIndicator color="#fff" />
              ) : (
                <>
                  <Feather name="send" size={18} color="#fff" />
                  <Text style={styles.submitText}>Jawab Pao</Text>
                </>
              )}
            </LinearGradient>
          </Pressable>

          {/* Error / quota message */}
          {errMsg && (
            <View style={[styles.card, { backgroundColor: "#ef444418", borderColor: "#ef444455" }]}>
              <Text style={[styles.cardTitle, { color: "#ef4444" }]}>⚠️ Suchana</Text>
              <Text style={[styles.cardBody, { color: c.text }]}>{errMsg}</Text>
              {errMsg.toLowerCase().includes("upgrade") && (
                <Pressable
                  onPress={() => { Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light); router.push("/subscription"); }}
                  style={{ marginTop: 10, alignSelf: "flex-start", paddingHorizontal: 14, paddingVertical: 8, borderRadius: 8, backgroundColor: "#ef4444" }}
                >
                  <Text style={{ color: "#fff", fontWeight: "700", fontSize: 13 }}>Upgrade dekho →</Text>
                </Pressable>
              )}
            </View>
          )}

          {/* Result */}
          {result && !result.ok && result.validity && (
            <View style={[styles.card, { backgroundColor: "#fbbf2418", borderColor: "#fbbf2455" }]}>
              <Text style={[styles.cardTitle, { color: "#f59e0b" }]}>
                ⚠️ Prashna abhi paripakv nahi
              </Text>
              <Text style={[styles.cardBody, { color: c.text }]}>
                {result.validity.reason}
              </Text>
              <Text style={[styles.refText, { color: c.text + "88" }]}>
                Ref: {result.validity.classical_ref}
              </Text>
              <Text style={[styles.refText, { color: c.text + "88", marginTop: 4 }]}>
                Punah prayaas: ~{result.validity.retry_after_min} minute baad
              </Text>
            </View>
          )}

          {result?.ok && result.verdict && (
            <>
              {/* Verdict card */}
              <View
                style={[
                  styles.card,
                  {
                    backgroundColor: verdictColor(result.verdict.code) + "1a",
                    borderColor:     verdictColor(result.verdict.code) + "66",
                  },
                ]}
              >
                <Text style={[styles.verdictLabel, { color: verdictColor(result.verdict.code) }]}>
                  {result.verdict.label_hi}
                </Text>
                <Text style={[styles.verdictMeaning, { color: c.text }]}>
                  {result.verdict.meaning}
                </Text>
                {result.timing && (
                  <View style={styles.timingRow}>
                    <Feather name="clock" size={14} color={c.text + "99"} />
                    <Text style={[styles.timingText, { color: c.text + "cc" }]}>
                      {result.timing}
                    </Text>
                  </View>
                )}
              </View>

              {/* Chart snapshot */}
              <View style={[styles.card, { backgroundColor: c.text + "08", borderColor: c.text + "1a" }]}>
                <Text style={[styles.cardTitle, { color: c.text }]}>📊 Prashna Chart</Text>
                <View style={styles.chartRow}>
                  <Text style={[styles.chartKey,   { color: c.text + "99" }]}>Lagna</Text>
                  <Text style={[styles.chartValue, { color: c.text }]}>
                    {result.lagna?.sign} · {result.lagna?.degree}
                  </Text>
                </View>
                <View style={styles.chartRow}>
                  <Text style={[styles.chartKey,   { color: c.text + "99" }]}>Sthan</Text>
                  <Text style={[styles.chartValue, { color: c.text }]}>
                    {result.place?.name}, {result.place?.state}
                  </Text>
                </View>
                <View style={styles.chartRow}>
                  <Text style={[styles.chartKey,   { color: c.text + "99" }]}>Vargi-karan</Text>
                  <Text style={[styles.chartValue, { color: c.text }]}>
                    {result.category_label}
                  </Text>
                </View>
              </View>

              {/* Cusp analysis */}
              {result.cusp_analysis && result.cusp_analysis.length > 0 && (
                <View style={[styles.card, { backgroundColor: c.text + "08", borderColor: c.text + "1a" }]}>
                  <Text style={[styles.cardTitle, { color: c.text }]}>
                    🪔 Cusp Vishleshan
                  </Text>
                  {result.cusp_analysis.map((cv, i) => (
                    <View key={i} style={styles.cuspBlock}>
                      <Text style={[styles.cuspHead, { color: c.text }]}>
                        {cv.house}th Bhava — {cv.sign} {cv.degree}
                      </Text>
                      <Text style={[styles.cuspMeta, { color: c.text + "aa" }]}>
                        Sub-Lord: {cv.sub_lord} · Star-Lord: {cv.star_lord}
                      </Text>
                      <Text style={[styles.cuspMeta, { color: c.text + "aa" }]}>
                        Signifies houses: {cv.signifies.join(", ") || "—"}
                      </Text>
                      <Text style={[styles.cuspVerdict, { color: verdictColor(cv.verdict) }]}>
                        {cv.verdict.replace("_", " ")}
                      </Text>
                    </View>
                  ))}
                </View>
              )}

              {/* Classical refs */}
              {result.classical_refs && (
                <View style={[styles.card, { backgroundColor: c.text + "06", borderColor: c.text + "12" }]}>
                  <Text style={[styles.cardTitle, { color: c.text }]}>📖 Aadhar Granth</Text>
                  {result.classical_refs.map((r, i) => (
                    <Text key={i} style={[styles.refText, { color: c.text + "99" }]}>
                      • {r}
                    </Text>
                  ))}
                </View>
              )}
            </>
          )}
        </ScrollView>
      </KeyboardAvoidingView>
    </CosmicBg>
  );
}

const styles = StyleSheet.create({
  header: {
    flexDirection: "row",
    alignItems:    "center",
    paddingHorizontal: 16,
    paddingBottom:     8,
  },
  backBtn: { padding: 4, marginRight: 8 },
  title:    { fontSize: 22, fontWeight: "800" },
  subtitle: { fontSize: 12, marginTop: 2 },

  metaStrip: {
    flexDirection: "row",
    alignItems:    "center",
    gap: 6,
    paddingHorizontal: 12,
    paddingVertical:   8,
    borderRadius:      8,
    marginBottom:      18,
  },
  metaText: { fontSize: 12, fontWeight: "500" },

  sectionLabel: { fontSize: 13, fontWeight: "700", marginBottom: 10, opacity: 0.85 },

  chipsRow: { flexDirection: "row", flexWrap: "wrap", gap: 8 },
  chip: {
    flexDirection: "row",
    alignItems:    "center",
    gap: 6,
    paddingHorizontal: 12,
    paddingVertical:   8,
    borderRadius:      18,
    borderWidth:       1,
    maxWidth:          "100%",
  },
  chipEmoji: { fontSize: 14 },
  chipText:  { fontSize: 13, fontWeight: "600" },

  input: {
    minHeight:       96,
    borderRadius:    12,
    borderWidth:     1,
    padding:         14,
    fontSize:        15,
    textAlignVertical: "top",
  },

  submitWrap:  { marginTop: 16, borderRadius: 14, overflow: "hidden" },
  submitBtn: {
    flexDirection: "row",
    alignItems:    "center",
    justifyContent:"center",
    gap: 8,
    paddingVertical: 14,
  },
  submitText: { color: "#fff", fontWeight: "800", fontSize: 16 },

  card: {
    marginTop:    16,
    padding:      16,
    borderRadius: 14,
    borderWidth:  1,
  },
  cardTitle: { fontSize: 14, fontWeight: "700", marginBottom: 10 },
  cardBody:  { fontSize: 14, lineHeight: 21 },

  verdictLabel:   { fontSize: 26, fontWeight: "900" },
  verdictMeaning: { fontSize: 15, marginTop: 6, lineHeight: 22 },
  timingRow: {
    flexDirection: "row",
    alignItems:    "center",
    gap: 6,
    marginTop: 10,
  },
  timingText: { fontSize: 13, flex: 1 },

  chartRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    paddingVertical: 4,
  },
  chartKey:   { fontSize: 13 },
  chartValue: { fontSize: 13, fontWeight: "600" },

  cuspBlock: {
    paddingVertical: 8,
    borderTopWidth:  StyleSheet.hairlineWidth,
    borderTopColor:  "#ffffff15",
  },
  cuspHead:    { fontSize: 13, fontWeight: "700" },
  cuspMeta:    { fontSize: 12, marginTop: 2 },
  cuspVerdict: { fontSize: 12, fontWeight: "800", marginTop: 4 },

  refText: { fontSize: 11, lineHeight: 16 },
});
