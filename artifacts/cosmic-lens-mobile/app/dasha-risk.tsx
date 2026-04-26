import { Feather } from "@expo/vector-icons";
import { LinearGradient } from "expo-linear-gradient";
import { router } from "expo-router";
import React, { useCallback, useEffect, useState } from "react";
import {
  ActivityIndicator,
  I18nManager,
  Pressable,
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { CosmicBg } from "@/components/CosmicBg";
import { useC } from "@/context/ThemeContext";
import { useUser } from "@/context/UserContext";
import { API_BASE, apiFetch } from "@/lib/apiConfig";

const F = {
  regular: "Nunito_400Regular",
  semi:    "Nunito_600SemiBold",
  bold:    "Nunito_700Bold",
  extra:   "Nunito_800ExtraBold",
} as const;

type RiskLevel = "low" | "medium" | "high";

interface Risk24h {
  level:   RiskLevel;
  title:   string;
  reason:  string;
  advice:  string;
  timing?: string;
}

interface Risk7dBlock {
  range:  string;
  level:  RiskLevel;
  label:  string;
  advice: string;
}

interface RiskRadarData {
  risk_radar_24h: Risk24h[];
  risk_radar_7d:  Risk7dBlock[];
  summary:        string;
  date?:          string;
  score?:         number;
}

// ── Level styling ─────────────────────────────────────────────────────────────
function levelColor(l: RiskLevel): string {
  if (l === "high")   return "#ef4444";
  if (l === "medium") return "#f59e0b";
  return "#22c55e";
}
function levelBg(l: RiskLevel): string {
  if (l === "high")   return "rgba(239,68,68,0.12)";
  if (l === "medium") return "rgba(245,158,11,0.12)";
  return "rgba(34,197,94,0.12)";
}
function levelLabel(l: RiskLevel): string {
  if (l === "high")   return "High";
  if (l === "medium") return "Medium";
  return "Low";
}
function levelIcon(l: RiskLevel): string {
  if (l === "high")   return "⚠️";
  if (l === "medium") return "🌗";
  return "✅";
}

export default function DashaRiskScreen() {
  const C        = useC();
  const insets   = useSafeAreaInsets();
  const { user, kundli, birthData } = useUser();

  const [data, setData]         = useState<RiskRadarData | null>(null);
  const [loading, setLoading]   = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError]       = useState<string | null>(null);

  const loadRadar = useCallback(async (silent = false) => {
    // Prefer stateless POST with primary kundli (works for non-logged-in
    // users too). Fall back to user_id+API key if local kundli not ready.
    if (!silent) setLoading(true);
    setError(null);

    const hasLocalKundli = !!(kundli && Array.isArray(kundli.planets) && kundli.planets.length > 0);

    if (!hasLocalKundli && !(user?.id && user?.api_key)) {
      setError("NO_KUNDLI");
      setLoading(false);
      return;
    }

    try {
      let r: Response;
      if (hasLocalKundli) {
        r = await apiFetch(`${API_BASE}/api/risk-radar`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            chart_data: kundli,
            birthData: birthData ?? undefined,
          }),
        });
      } else {
        r = await apiFetch(`${API_BASE}/api/risk-radar?user_id=${user!.id}`, {
          method: "GET",
          headers: { "X-API-Key": user!.api_key },
        });
      }
      const j = await r.json();
      if (!r.ok) {
        const msg = (j?.error || "").toLowerCase();
        if (msg.includes("kundli") || r.status === 404) {
          setError("NO_KUNDLI");
        } else {
          setError(j?.error || "Could not load Risk Radar");
        }
        setData(null);
      } else {
        setData(j as RiskRadarData);
      }
    } catch (e: any) {
      setError(e?.message || "Network error");
      setData(null);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [user?.id, user?.api_key, kundli, birthData]);

  useEffect(() => { loadRadar(); }, [loadRadar]);

  const onRefresh = useCallback(() => {
    setRefreshing(true);
    loadRadar(true);
  }, [loadRadar]);

  const back = () => {
    if (router.canGoBack()) router.back();
    else router.replace("/(tabs)");
  };

  const summaryColor = (() => {
    if (!data) return C.textMid;
    const high = data.risk_radar_24h.filter(r => r.level === "high").length;
    if (high >= 2) return levelColor("high");
    if (high === 1) return levelColor("medium");
    return levelColor("low");
  })();

  return (
    <View style={[s.root, { backgroundColor: C.bg }]}>
      <CosmicBg />

      {/* Header */}
      <View style={[s.header, { paddingTop: insets.top + 6 }]}>
        <Pressable
          onPress={back}
          style={[s.backBtn, { borderColor: C.border, backgroundColor: C.bgCard }]}
          hitSlop={10}
        >
          <Feather
            name={I18nManager.isRTL ? "arrow-right" : "arrow-left"}
            size={18}
            color={C.text}
          />
        </Pressable>
        <View style={{ flex: 1 }}>
          <Text style={[s.h1, { color: C.text }]}>Risk Radar</Text>
          <Text style={[s.h1Sub, { color: C.textMuted }]}>
            Aaj aur agle 7 din ke important signals
          </Text>
        </View>
      </View>

      <ScrollView
        contentContainerStyle={{ padding: 16, paddingBottom: insets.bottom + 80 }}
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={onRefresh}
            tintColor={C.text}
          />
        }
      >
        {loading ? (
          <View style={s.loadingBox}>
            <ActivityIndicator size="large" color={C.accent} />
            <Text style={[s.loadingTxt, { color: C.textMuted }]}>
              Aapka radar tayyar kar rahe hain…
            </Text>
          </View>
        ) : error === "NO_KUNDLI" ? (
          <View style={[s.card, s.emptyCard, { backgroundColor: C.bgCard, borderColor: C.border }]}>
            <Text style={s.emptyIcon}>🪐</Text>
            <Text style={[s.emptyTitle, { color: C.text }]}>
              Pehle apni kundli banayein
            </Text>
            <Text style={[s.emptyBody, { color: C.textMuted }]}>
              Risk Radar aapke janma kundli ke signals pe based hai. Kundli
              banane ke baad aapko aaj aur agle 7 din ke important signals
              dikhenge.
            </Text>
            <Pressable
              onPress={() => router.push("/(tabs)/profile")}
              style={[s.retryBtn, { backgroundColor: C.accent }]}
            >
              <Text style={s.retryTxt}>Kundli banayein</Text>
            </Pressable>
          </View>
        ) : error === "LOGIN_REQUIRED" ? (
          <View style={[s.card, s.emptyCard, { backgroundColor: C.bgCard, borderColor: C.border }]}>
            <Text style={s.emptyIcon}>🔐</Text>
            <Text style={[s.emptyTitle, { color: C.text }]}>
              Pehle login karein
            </Text>
            <Text style={[s.emptyBody, { color: C.textMuted }]}>
              Risk Radar dekhne ke liye apne account mein login karein.
            </Text>
            <Pressable
              onPress={() => router.push("/login")}
              style={[s.retryBtn, { backgroundColor: C.accent }]}
            >
              <Text style={s.retryTxt}>Login</Text>
            </Pressable>
          </View>
        ) : error ? (
          <View style={[s.card, { backgroundColor: C.bgCard, borderColor: C.border }]}>
            <Text style={[s.errTitle, { color: levelColor("high") }]}>
              Risk Radar load nahi ho saka
            </Text>
            <Text style={[s.errBody, { color: C.textMuted }]}>{error}</Text>
            <Pressable
              onPress={() => loadRadar()}
              style={[s.retryBtn, { backgroundColor: C.accent }]}
            >
              <Text style={s.retryTxt}>Phir try karein</Text>
            </Pressable>
          </View>
        ) : data ? (
          <>
            {/* Summary card */}
            <LinearGradient
              colors={[C.bgCard, C.bgCard2]}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 1 }}
              style={[s.card, s.summaryCard, { borderColor: C.border }]}
            >
              <View style={s.summaryHead}>
                <View style={[s.dot, { backgroundColor: summaryColor }]} />
                <Text style={[s.summaryLabel, { color: C.textMuted }]}>
                  Aaj ka radar
                </Text>
              </View>
              <Text style={[s.summaryTxt, { color: C.text }]}>
                {data.summary}
              </Text>
              {typeof data.score === "number" && (
                <View style={s.scoreRow}>
                  <Text style={[s.scoreLabel, { color: C.textMuted }]}>
                    Energy Score
                  </Text>
                  <Text style={[s.scoreVal, { color: C.text }]}>
                    {Math.round(data.score)}/100
                  </Text>
                </View>
              )}
            </LinearGradient>

            {/* 24h section */}
            <View style={s.sectionHead}>
              <Text style={[s.sectionTitle, { color: C.text }]}>
                Next 24 Hours
              </Text>
              <Text style={[s.sectionSub, { color: C.textMuted }]}>
                Aaj ke top {data.risk_radar_24h.length} signal
              </Text>
            </View>

            {data.risk_radar_24h.map((risk, i) => (
              <View
                key={`r24-${i}`}
                style={[
                  s.card,
                  s.riskCard,
                  {
                    backgroundColor: C.bgCard,
                    borderColor: C.border,
                    borderLeftColor: levelColor(risk.level),
                  },
                ]}
              >
                <View style={s.riskHead}>
                  <Text style={s.riskIcon}>{levelIcon(risk.level)}</Text>
                  <Text style={[s.riskTitle, { color: C.text }]}>
                    {risk.title}
                  </Text>
                  <View
                    style={[
                      s.levelPill,
                      { backgroundColor: levelBg(risk.level) },
                    ]}
                  >
                    <Text
                      style={[
                        s.levelPillTxt,
                        { color: levelColor(risk.level) },
                      ]}
                    >
                      {levelLabel(risk.level)}
                    </Text>
                  </View>
                </View>
                <Text style={[s.riskReason, { color: C.textMid }]}>
                  {risk.reason}
                </Text>
                <View
                  style={[
                    s.adviceBox,
                    { backgroundColor: C.bgCard2, borderColor: C.border3 },
                  ]}
                >
                  <Text style={[s.adviceLabel, { color: C.textMuted }]}>
                    💡 Kya karein
                  </Text>
                  <Text style={[s.adviceTxt, { color: C.text }]}>
                    {risk.advice}
                  </Text>
                </View>
                {risk.timing ? (
                  <View style={s.timingRow}>
                    <Feather name="clock" size={12} color={C.textMuted} />
                    <Text style={[s.timingTxt, { color: C.textMuted }]}>
                      {risk.timing}
                    </Text>
                  </View>
                ) : null}
              </View>
            ))}

            {/* 7d section */}
            <View style={[s.sectionHead, { marginTop: 12 }]}>
              <Text style={[s.sectionTitle, { color: C.text }]}>
                Next 7 Days
              </Text>
              <Text style={[s.sectionSub, { color: C.textMuted }]}>
                3 phases ka outlook
              </Text>
            </View>

            {data.risk_radar_7d.map((block, i) => (
              <View
                key={`r7-${i}`}
                style={[
                  s.card,
                  s.blockCard,
                  {
                    backgroundColor: C.bgCard,
                    borderColor: C.border,
                  },
                ]}
              >
                <View style={s.blockHead}>
                  <View
                    style={[
                      s.blockRangePill,
                      { backgroundColor: C.bgCard2, borderColor: C.border3 },
                    ]}
                  >
                    <Text style={[s.blockRangeTxt, { color: C.text }]}>
                      {block.range}
                    </Text>
                  </View>
                  <View
                    style={[
                      s.levelPill,
                      { backgroundColor: levelBg(block.level) },
                    ]}
                  >
                    <Text
                      style={[
                        s.levelPillTxt,
                        { color: levelColor(block.level) },
                      ]}
                    >
                      {levelLabel(block.level)}
                    </Text>
                  </View>
                </View>
                <Text style={[s.blockLabel, { color: C.text }]}>
                  {levelIcon(block.level)}  {block.label}
                </Text>
                <Text style={[s.blockAdvice, { color: C.textMid }]}>
                  {block.advice}
                </Text>
              </View>
            ))}

            {/* Honest accuracy note */}
            <View
              style={[
                s.noteCard,
                { backgroundColor: C.bgCard2, borderColor: C.border3 },
              ]}
            >
              <Text style={[s.noteTitle, { color: C.text }]}>
                Note
              </Text>
              <Text style={[s.noteBody, { color: C.textMuted }]}>
                Yeh radar aapke janma kundli + aaj ke gochar (planetary transits) ke
                signals pe based hai. Yeh probability hai, certainty nahi — aap
                apne best judgement ke saath isko use karein.
              </Text>
              <Text style={[s.noteFooter, { color: C.textDim }]}>
                Powered by Advanced Cosmic Intelligence
              </Text>
            </View>
          </>
        ) : null}
      </ScrollView>
    </View>
  );
}

const s = StyleSheet.create({
  root: { flex: 1 },

  header: {
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: 16,
    paddingBottom: 8,
    gap: 12,
  },
  backBtn: {
    width: 36, height: 36, borderRadius: 12,
    borderWidth: 1, alignItems: "center", justifyContent: "center",
  },
  h1:    { fontSize: 22, fontFamily: F.extra },
  h1Sub: { fontSize: 12, fontFamily: F.regular, marginTop: 2 },

  loadingBox: {
    paddingVertical: 60, alignItems: "center", gap: 12,
  },
  loadingTxt: { fontSize: 13, fontFamily: F.regular },

  card: {
    borderRadius: 16, borderWidth: 1, padding: 16, marginBottom: 12,
  },

  summaryCard: { paddingVertical: 18 },
  summaryHead: {
    flexDirection: "row", alignItems: "center", gap: 8, marginBottom: 8,
  },
  dot: { width: 8, height: 8, borderRadius: 4 },
  summaryLabel: {
    fontSize: 11, fontFamily: F.semi,
    textTransform: "uppercase", letterSpacing: 0.5,
  },
  summaryTxt: {
    fontSize: 15, fontFamily: F.semi, lineHeight: 22,
  },
  scoreRow: {
    flexDirection: "row", alignItems: "center", justifyContent: "space-between",
    marginTop: 12, paddingTop: 12, borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: "rgba(127,127,127,0.2)",
  },
  scoreLabel: { fontSize: 12, fontFamily: F.semi },
  scoreVal:   { fontSize: 16, fontFamily: F.extra },

  sectionHead: {
    marginTop: 6, marginBottom: 8, paddingHorizontal: 4,
  },
  sectionTitle: { fontSize: 16, fontFamily: F.bold },
  sectionSub:   { fontSize: 11, fontFamily: F.regular, marginTop: 2 },

  riskCard: { borderLeftWidth: 4 },
  riskHead: {
    flexDirection: "row", alignItems: "center", gap: 8, marginBottom: 8,
  },
  riskIcon:  { fontSize: 18 },
  riskTitle: { fontSize: 15, fontFamily: F.bold, flex: 1 },
  riskReason:{ fontSize: 13, fontFamily: F.regular, lineHeight: 19, marginBottom: 10 },

  levelPill: {
    paddingHorizontal: 8, paddingVertical: 3, borderRadius: 999,
  },
  levelPillTxt: {
    fontSize: 10, fontFamily: F.bold,
    textTransform: "uppercase", letterSpacing: 0.4,
  },

  adviceBox: {
    borderRadius: 10, padding: 10, borderWidth: 1, gap: 4,
  },
  adviceLabel: {
    fontSize: 11, fontFamily: F.semi,
    textTransform: "uppercase", letterSpacing: 0.4,
  },
  adviceTxt: { fontSize: 13, fontFamily: F.semi, lineHeight: 19 },

  timingRow: {
    flexDirection: "row", alignItems: "center", gap: 6, marginTop: 8,
  },
  timingTxt: { fontSize: 11, fontFamily: F.semi },

  blockCard: { gap: 8 },
  blockHead: {
    flexDirection: "row", alignItems: "center", justifyContent: "space-between",
  },
  blockRangePill: {
    paddingHorizontal: 10, paddingVertical: 4,
    borderRadius: 999, borderWidth: 1,
  },
  blockRangeTxt: { fontSize: 11, fontFamily: F.bold },
  blockLabel:    { fontSize: 14, fontFamily: F.bold, marginTop: 4 },
  blockAdvice:   { fontSize: 13, fontFamily: F.regular, lineHeight: 19 },

  noteCard: {
    borderRadius: 14, borderWidth: 1, padding: 14, marginTop: 8,
  },
  noteTitle:  { fontSize: 13, fontFamily: F.bold, marginBottom: 6 },
  noteBody:   { fontSize: 12, fontFamily: F.regular, lineHeight: 18 },
  noteFooter: {
    fontSize: 10, fontFamily: F.semi, marginTop: 10, textAlign: "center",
    letterSpacing: 0.3,
  },

  emptyCard: {
    alignItems: "center", paddingVertical: 28, gap: 8,
  },
  emptyIcon:  { fontSize: 44, marginBottom: 6 },
  emptyTitle: {
    fontSize: 17, fontFamily: F.bold, textAlign: "center",
  },
  emptyBody: {
    fontSize: 13, fontFamily: F.regular, lineHeight: 19,
    textAlign: "center", marginBottom: 12,
  },

  errTitle: { fontSize: 15, fontFamily: F.bold, marginBottom: 6 },
  errBody:  { fontSize: 13, fontFamily: F.regular, marginBottom: 12 },
  retryBtn: {
    paddingVertical: 10, paddingHorizontal: 16,
    borderRadius: 10, alignSelf: "flex-start",
  },
  retryTxt: { color: "#fff", fontFamily: F.bold, fontSize: 13 },
});
