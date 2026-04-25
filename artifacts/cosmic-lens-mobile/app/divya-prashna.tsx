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
import { useT, type T } from "@/hooks/useT";
import { API_BASE } from "@/lib/apiConfig";

type CategoryKey =
  | "stolen_item" | "partner_feelings" | "job" | "marriage"
  | "health" | "litigation" | "travel" | "general";

const QUICK_CATEGORIES: { key: CategoryKey; emoji: string }[] = [
  { key: "stolen_item",      emoji: "💰" },
  { key: "partner_feelings", emoji: "💔" },
  { key: "job",              emoji: "💼" },
  { key: "marriage",         emoji: "💍" },
  { key: "health",           emoji: "🏥" },
  { key: "litigation",       emoji: "⚖️" },
  { key: "travel",           emoji: "✈️" },
  { key: "general",          emoji: "🔮" },
];

function categoryLabel(k: CategoryKey, t: T): string {
  switch (k) {
    case "stolen_item":      return t.dp_cat_stolen;
    case "partner_feelings": return t.dp_cat_partner;
    case "job":              return t.dp_cat_job;
    case "marriage":         return t.dp_cat_marriage;
    case "health":           return t.dp_cat_health;
    case "litigation":       return t.dp_cat_litigation;
    case "travel":           return t.dp_cat_travel;
    case "general":          return t.dp_cat_general;
  }
}
function categoryPrompt(k: CategoryKey, t: T): string {
  switch (k) {
    case "stolen_item":      return t.dp_pr_stolen;
    case "partner_feelings": return t.dp_pr_partner;
    case "job":              return t.dp_pr_job;
    case "marriage":         return t.dp_pr_marriage;
    case "health":           return t.dp_pr_health;
    case "litigation":       return t.dp_pr_litigation;
    case "travel":           return t.dp_pr_travel;
    case "general":          return "";
  }
}

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
  const t       = useT();

  const [question, setQuestion] = useState("");
  const [category, setCategory] = useState<CategoryKey | undefined>(undefined);
  const [loading,  setLoading]  = useState(false);
  const [result,   setResult]   = useState<PrashnaResult | null>(null);
  const [errMsg,   setErrMsg]   = useState<string | null>(null);

  const ask = async () => {
    const q = question.trim();
    if (!q) {
      Alert.alert(t.dp_alertEmptyTtl, t.dp_alertEmptyMsg);
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
        setErrMsg(json.message || t.dp_errQuotaPro);
        Haptics.notificationAsync(Haptics.NotificationFeedbackType.Warning);
        return;
      }
      if (resp.status === 401) {
        setErrMsg(t.dp_errSession);
        Haptics.notificationAsync(Haptics.NotificationFeedbackType.Warning);
        return;
      }
      if (!resp.ok) {
        setErrMsg(json.message || json.error || t.dp_errFetch);
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
      setErrMsg(e?.message || t.dp_errFetch);
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
    } finally {
      setLoading(false);
    }
  };

  const pickCategory = (catKey: CategoryKey) => {
    Haptics.selectionAsync();
    setCategory(catKey);
    setQuestion(categoryPrompt(catKey, t));
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
          <Text style={[styles.title, { color: c.text }]}>{t.dp_title}</Text>
          <Text style={[styles.subtitle, { color: c.text + "99" }]}>
            {t.dp_subtitle}
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
              {t.dp_metaCity}
            </Text>
          </View>

          {/* Quick category chips */}
          <Text style={[styles.sectionLabel, { color: c.text }]}>{t.dp_quickQuestion}</Text>
          <View style={styles.chipsRow}>
            {QUICK_CATEGORIES.map((cat) => {
              const active = category === cat.key;
              return (
                <Pressable
                  key={cat.key}
                  onPress={() => pickCategory(cat.key)}
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
                    {categoryLabel(cat.key, t)}
                  </Text>
                </Pressable>
              );
            })}
          </View>

          {/* Question input */}
          <Text style={[styles.sectionLabel, { color: c.text, marginTop: 18 }]}>
            {t.dp_orType}
          </Text>
          <TextInput
            value={question}
            onChangeText={setQuestion}
            placeholder={t.dp_inputPh}
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
                  <Text style={styles.submitText}>{t.dp_btnGetAnswer}</Text>
                </>
              )}
            </LinearGradient>
          </Pressable>

          {/* Error / quota message */}
          {errMsg && (
            <View style={[styles.card, { backgroundColor: "#ef444418", borderColor: "#ef444455" }]}>
              <Text style={[styles.cardTitle, { color: "#ef4444" }]}>{t.dp_errNoticeTtl}</Text>
              <Text style={[styles.cardBody, { color: c.text }]}>{errMsg}</Text>
              {errMsg.toLowerCase().includes("upgrade") && (
                <Pressable
                  onPress={() => { Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light); router.push("/subscription"); }}
                  style={{ marginTop: 10, alignSelf: "flex-start", paddingHorizontal: 14, paddingVertical: 8, borderRadius: 8, backgroundColor: "#ef4444" }}
                >
                  <Text style={{ color: "#fff", fontWeight: "700", fontSize: 13 }}>{t.dp_btnSeeUpgrade}</Text>
                </Pressable>
              )}
            </View>
          )}

          {/* Result */}
          {result && !result.ok && result.validity && (
            <View style={[styles.card, { backgroundColor: "#fbbf2418", borderColor: "#fbbf2455" }]}>
              <Text style={[styles.cardTitle, { color: "#f59e0b" }]}>
                {t.dp_immatureTitle}
              </Text>
              <Text style={[styles.cardBody, { color: c.text }]}>
                {result.validity.reason}
              </Text>
              <Text style={[styles.refText, { color: c.text + "88" }]}>
                {t.dp_refPrefix}: {result.validity.classical_ref}
              </Text>
              <Text style={[styles.refText, { color: c.text + "88", marginTop: 4 }]}>
                {t.dp_retryAfter}: ~{result.validity.retry_after_min} {t.dp_minutesLater}
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
                  {t.vlang === "en" ? result.verdict.label_en : result.verdict.label_hi}
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
                <Text style={[styles.cardTitle, { color: c.text }]}>{t.dp_chartTitle}</Text>
                <View style={styles.chartRow}>
                  <Text style={[styles.chartKey,   { color: c.text + "99" }]}>{t.dp_chartLagna}</Text>
                  <Text style={[styles.chartValue, { color: c.text }]}>
                    {result.lagna?.sign} · {result.lagna?.degree}
                  </Text>
                </View>
                <View style={styles.chartRow}>
                  <Text style={[styles.chartKey,   { color: c.text + "99" }]}>{t.dp_chartPlace}</Text>
                  <Text style={[styles.chartValue, { color: c.text }]}>
                    {result.place?.name}, {result.place?.state}
                  </Text>
                </View>
                <View style={styles.chartRow}>
                  <Text style={[styles.chartKey,   { color: c.text + "99" }]}>{t.dp_chartCategory}</Text>
                  <Text style={[styles.chartValue, { color: c.text }]}>
                    {result.category_label}
                  </Text>
                </View>
              </View>

              {/* Cusp analysis */}
              {result.cusp_analysis && result.cusp_analysis.length > 0 && (
                <View style={[styles.card, { backgroundColor: c.text + "08", borderColor: c.text + "1a" }]}>
                  <Text style={[styles.cardTitle, { color: c.text }]}>
                    {t.dp_cuspTitle}
                  </Text>
                  {result.cusp_analysis.map((cv, i) => (
                    <View key={i} style={styles.cuspBlock}>
                      <Text style={[styles.cuspHead, { color: c.text }]}>
                        {cv.house}{ordinalSuffix(cv.house, t)} {t.dp_houseSuffix} — {cv.sign} {cv.degree}
                      </Text>
                      <Text style={[styles.cuspMeta, { color: c.text + "aa" }]}>
                        {t.dp_subLord}: {cv.sub_lord} · {t.dp_starLord}: {cv.star_lord}
                      </Text>
                      <Text style={[styles.cuspMeta, { color: c.text + "aa" }]}>
                        {t.dp_signifies}: {cv.signifies.join(", ") || "—"}
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
                  <Text style={[styles.cardTitle, { color: c.text }]}>{t.dp_classicalTitle}</Text>
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

function ordinalSuffix(n: number, t: T): string {
  const r10 = n % 10, r100 = n % 100;
  if (r100 >= 11 && r100 <= 13) return t.pk_houseTh;
  if (r10 === 1) return t.pk_houseSt;
  if (r10 === 2) return t.pk_houseNd;
  if (r10 === 3) return t.pk_houseRd;
  return t.pk_houseTh;
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
