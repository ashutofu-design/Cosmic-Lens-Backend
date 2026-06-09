import { Feather } from "@expo/vector-icons";
import { LinearGradient } from "expo-linear-gradient";
import { router, useLocalSearchParams } from "expo-router";
import React, { useCallback, useEffect, useRef, useState } from "react";
import {
  Animated,
  Easing,
  ActivityIndicator,
  Alert,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { CosmicBg } from "@/components/CosmicBg";
import { LoveRealityProReportView } from "@/components/loveReality/LoveRealityProReportView";
import { useC } from "@/context/ThemeContext";
import { useUser } from "@/context/UserContext";
import {
  buildLoveReportSections,
  fetchLoveRealityProReport,
  type LoveProReportResponse,
} from "@/lib/loveRealityProReport";
import {
  loveReportCacheKey,
  loadCachedLoveReport,
  saveCachedLoveReport,
} from "@/lib/loveRealityProReportCache";
import { connectLoveRealityPageToPdf } from "@/lib/loveRealityProPdfDownload";
import { coerceProPdfLang } from "@/lib/proPdfLang";

const LOAD_STAGES = [
  "Loading your charts…",
  "Running compatibility engines…",
  "Writing personalized insights…",
  "Almost ready…",
] as const;

function ReportLoadingView({
  pct,
  stageIdx,
  isDark,
  done,
  fromCache,
}: {
  pct: number;
  stageIdx: number;
  isDark: boolean;
  done: boolean;
  fromCache: boolean;
}) {
  const spinAnim = useRef(new Animated.Value(0)).current;
  const barAnim = useRef(new Animated.Value(0)).current;
  const pulseAnim = useRef(new Animated.Value(1)).current;

  useEffect(() => {
    Animated.timing(barAnim, {
      toValue: pct / 100,
      duration: 380,
      easing: Easing.out(Easing.cubic),
      useNativeDriver: false,
    }).start();
  }, [pct, barAnim]);

  useEffect(() => {
    if (done) return;
    spinAnim.setValue(0);
    const spin = Animated.loop(
      Animated.timing(spinAnim, {
        toValue: 1,
        duration: 1100,
        easing: Easing.linear,
        useNativeDriver: true,
      }),
    );
    spin.start();
    return () => spin.stop();
  }, [done, spinAnim]);

  useEffect(() => {
    if (done) return;
    const pulse = Animated.loop(
      Animated.sequence([
        Animated.timing(pulseAnim, {
          toValue: 1.06,
          duration: 900,
          easing: Easing.inOut(Easing.ease),
          useNativeDriver: true,
        }),
        Animated.timing(pulseAnim, {
          toValue: 1,
          duration: 900,
          easing: Easing.inOut(Easing.ease),
          useNativeDriver: true,
        }),
      ]),
    );
    pulse.start();
    return () => pulse.stop();
  }, [done, pulseAnim]);

  const text = isDark ? "#f1f5f9" : "#0F172A";
  const dim = isDark ? "rgba(226,232,240,0.72)" : "#64748B";
  const cardBg = isDark ? "#0F0A1F" : "#FFFFFF";
  const trackBg = isDark ? "rgba(255,255,255,0.08)" : "#F3F4F6";

  return (
    <View style={ld.wrap}>
      <LinearGradient
        colors={["#9333ea", "#ec4899", "#f59e0b"]}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
        style={ld.borderGrad}
      >
        <View style={[ld.card, { backgroundColor: cardBg }]}>
          <Animated.View style={{ transform: [{ scale: done ? 1 : pulseAnim }] }}>
            {done ? (
              <LinearGradient
                colors={["#10B981", "#059669"]}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 1 }}
                style={ld.iconCircle}
              >
                <Feather name="check" size={32} color="#fff" />
              </LinearGradient>
            ) : (
              <LinearGradient
                colors={["#9333ea", "#ec4899"]}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 1 }}
                style={ld.iconCircle}
              >
                <Animated.View
                  style={{
                    transform: [{
                      rotate: spinAnim.interpolate({
                        inputRange: [0, 1],
                        outputRange: ["0deg", "360deg"],
                      }),
                    }],
                  }}
                >
                  <Feather name="loader" size={28} color="#fff" />
                </Animated.View>
              </LinearGradient>
            )}
          </Animated.View>

          <Text style={[ld.title, { color: text }]}>
            {done ? "Report ready!" : "Loading…"}
          </Text>
          <Text style={[ld.stage, { color: dim }]}>
            {done
              ? "Opening your Love Reality Pro report"
              : fromCache
                ? "Loading saved report…"
                : LOAD_STAGES[stageIdx]}
          </Text>

          <View style={[ld.track, { backgroundColor: trackBg }]}>
            <Animated.View
              style={[
                ld.fillWrap,
                {
                  width: barAnim.interpolate({
                    inputRange: [0, 1],
                    outputRange: ["0%", "100%"],
                  }),
                },
              ]}
            >
              <LinearGradient
                colors={["#9333ea", "#ec4899", "#f59e0b"]}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 0 }}
                style={ld.fill}
              />
            </Animated.View>
          </View>

          <View style={ld.pctRow}>
            <Text style={[ld.pct, { color: text }]}>{pct}%</Text>
            {!done ? (
              <Text style={[ld.hint, { color: dim }]}>
                {fromCache ? "No new AI call — instant replay" : "First load may take 1–2 min — please wait"}
              </Text>
            ) : null}
          </View>
        </View>
      </LinearGradient>
    </View>
  );
}

export default function LoveRealityProReportScreen() {
  const C = useC();
  const { user, profiles, primaryProfileId } = useUser();
  const insets = useSafeAreaInsets();
  const params = useLocalSearchParams<{ partnerId?: string; lang?: string }>();
  const lang = coerceProPdfLang(params.lang);

  const primaryProfile = profiles.find(p => p.id === primaryProfileId) ?? profiles[0] ?? null;
  const partnerProfile = params.partnerId
    ? (profiles.find(p => p.id === params.partnerId) ?? null)
    : null;

  const [fetching, setFetching] = useState(true);
  const [loadPct, setLoadPct] = useState(0);
  const [stageIdx, setStageIdx] = useState(0);
  const [loadDone, setLoadDone] = useState(false);
  const [showReport, setShowReport] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [report, setReport] = useState<LoveProReportResponse | null>(null);
  const [fromCache, setFromCache] = useState(false);
  const [pdfConnecting, setPdfConnecting] = useState(false);
  const loadedRef = useRef(false);
  const fetchDoneRef = useRef(false);
  const fastCacheRef = useRef(false);

  const finishLoad = useCallback((data: LoveProReportResponse, cached: boolean) => {
    fetchDoneRef.current = true;
    fastCacheRef.current = cached;
    setFromCache(cached);
    setReport(data);
  }, []);

  const load = useCallback(async () => {
    if (!user?.id || !primaryProfile?.birthData || !partnerProfile?.birthData) {
      setError("Complete both kundlis and sign in to read the report.");
      setFetching(false);
      return;
    }
    setFetching(true);
    setLoadPct(0);
    setLoadDone(false);
    setShowReport(false);
    setStageIdx(0);
    setError(null);
    fetchDoneRef.current = false;
    fastCacheRef.current = false;
    setFromCache(false);

    const cacheKey = loveReportCacheKey({
      userId: user.id,
      p1: primaryProfile.birthData,
      p2: partnerProfile.birthData,
      p1Name: primaryProfile.name || "You",
      p2Name: partnerProfile.name || "Partner",
      lang,
    });

    try {
      const cached = await loadCachedLoveReport(cacheKey);
      if (cached) {
        finishLoad(cached, true);
        return;
      }

      const ctrl = new AbortController();
      const timer = setTimeout(() => ctrl.abort(), 240000);
      try {
        const { data, serverCacheHit } = await fetchLoveRealityProReport({
          user,
          p1: primaryProfile.birthData,
          p2: partnerProfile.birthData,
          p1Name: primaryProfile.name || "You",
          p2Name: partnerProfile.name || "Partner",
          lang,
          signal: ctrl.signal,
        });
        await saveCachedLoveReport(cacheKey, data);
        finishLoad(data, serverCacheHit);
      } finally {
        clearTimeout(timer);
      }
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Could not load report";
      setError(/abort/i.test(msg) ? "Report timed out — tap Retry." : msg);
      setFetching(false);
    }
  }, [user, primaryProfile, partnerProfile, lang, finishLoad]);

  useEffect(() => {
    if (loadedRef.current) return;
    loadedRef.current = true;
    load();
  }, [load]);

  useEffect(() => {
    if (!fetching || fetchDoneRef.current) return;
    const fast = fastCacheRef.current;
    const tickMs = fast ? 70 : 900;
    const step = fast ? 10 : 1;
    const cap = fast ? 100 : 90;
    const tick = setInterval(() => {
      setLoadPct(p => (p >= cap ? cap : Math.min(cap, p + step)));
    }, tickMs);
    return () => clearInterval(tick);
  }, [fetching]);

  useEffect(() => {
    if (!fetching || fetchDoneRef.current) return;
    const tick = setInterval(() => {
      setStageIdx(i => (i + 1) % LOAD_STAGES.length);
    }, 3200);
    return () => clearInterval(tick);
  }, [fetching]);

  useEffect(() => {
    if (!fetchDoneRef.current || !report) return;
    setFetching(false);
    setLoadDone(true);
    setLoadPct(100);
  }, [report]);

  useEffect(() => {
    if (!loadDone || loadPct < 100 || !report) return;
    const delay = fastCacheRef.current ? 300 : 650;
    const t = setTimeout(() => setShowReport(true), delay);
    return () => clearTimeout(t);
  }, [loadDone, loadPct, report]);

  const handleConnectToPdf = useCallback(async () => {
    if (
      !user?.id
      || !primaryProfile?.birthData
      || !partnerProfile?.birthData
      || !report?.pro_premium
      || !report.pdf_context
      || !report.page1
      || pdfConnecting
    ) {
      if (report && (!report.pdf_context || !report.page1)) {
        Alert.alert(
          "Report refresh needed",
          "This saved report is incomplete. Tap Retry to reload, then Connect to PDF.",
          [{ text: "OK" }],
        );
      }
      return;
    }
    setPdfConnecting(true);
    try {
      const result = await connectLoveRealityPageToPdf({
        user,
        p1: primaryProfile.birthData,
        p2: partnerProfile.birthData,
        p1Name: primaryProfile.name || "You",
        p2Name: partnerProfile.name || "Partner",
        lang,
        reportSnapshot: {
          pro_premium: report.pro_premium,
          pdf_context: report.pdf_context,
          page1: report.page1,
        },
        appSections: buildLoveReportSections(report, lang),
        scores: report.scores,
      });
      const fromCache = result.reportCacheHit ? " (server cache)" : "";
      const mirrorNote = result.pdfSource === "app_mirror_fresh"
        ? "Built from this page — 1–3 sec is normal, not old cache."
        : `Source: ${result.pdfSource || "fresh render"}${fromCache}.`;
      Alert.alert(
        "PDF connected",
        result.savedToRegistry
          ? `${mirrorNote} Saved to My Reports — open the newest entry (Connected from page).`
          : mirrorNote,
        [
          { text: "OK", style: "cancel" },
          ...(result.savedToRegistry
            ? [{
                text: "Open My Reports",
                onPress: () => router.push("/my-reports" as never),
              }]
            : []),
        ],
      );
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Could not connect page to PDF";
      Alert.alert("Connect to PDF failed", msg, [{ text: "OK" }]);
    } finally {
      setPdfConnecting(false);
    }
  }, [user, primaryProfile, partnerProfile, lang, pdfConnecting, report]);

  const sections = report ? buildLoveReportSections(report, lang) : [];
  const isLoadingUi = fetching || (loadDone && !showReport);

  return (
    <CosmicBg>
      <View style={[s.shell, { paddingTop: insets.top + 8 }]}>
        <View style={s.header}>
          <Pressable onPress={() => router.back()} hitSlop={10}>
            <Feather name="chevron-left" size={24} color={C.isDark ? "#fff" : "#0F172A"} />
          </Pressable>
          <Text style={[s.headerTitle, { color: C.isDark ? "#fff" : "#0F172A" }]} numberOfLines={1}>
            Love Reality Pro
          </Text>
          {report && showReport && !error ? (
            <Pressable
              onPress={handleConnectToPdf}
              disabled={pdfConnecting}
              style={[s.savePdfBtn, pdfConnecting && { opacity: 0.7 }]}
              hitSlop={6}
            >
              {pdfConnecting ? (
                <ActivityIndicator size="small" color="#fff" />
              ) : (
                <>
                  <Feather name="link" size={13} color="#fff" />
                  <Text style={s.savePdfTxt}>Connect PDF</Text>
                </>
              )}
            </Pressable>
          ) : (
            <View style={{ width: 88 }} />
          )}
        </View>

        {error ? (
          <View style={s.center}>
            <Feather name="alert-circle" size={32} color="#f472b6" />
            <Text style={[s.errTxt, { color: C.text }]}>{error}</Text>
            <Pressable
              onPress={() => {
                loadedRef.current = false;
                fetchDoneRef.current = false;
                load();
                loadedRef.current = true;
              }}
              style={s.retryBtn}
            >
              <Text style={s.retryTxt}>Retry</Text>
            </Pressable>
          </View>
        ) : isLoadingUi ? (
          <ReportLoadingView
            pct={loadPct}
            stageIdx={stageIdx}
            isDark={C.isDark}
            done={loadDone}
            fromCache={fromCache}
          />
        ) : report && showReport ? (
          <>
            <ScrollView
              contentContainerStyle={{ paddingHorizontal: 16, paddingBottom: insets.bottom + 120 }}
              showsVerticalScrollIndicator={false}
            >
              <LoveRealityProReportView
                isDark={C.isDark}
                p1Name={report.p1_name}
                p2Name={report.p2_name}
                scores={report.scores}
                sections={sections}
              />
            </ScrollView>
            <View
              style={[
                s.connectBar,
                {
                  paddingBottom: insets.bottom + 10,
                  backgroundColor: C.isDark ? "rgba(15,10,31,0.96)" : "rgba(255,255,255,0.96)",
                  borderTopColor: C.isDark ? "rgba(255,255,255,0.08)" : "rgba(0,0,0,0.06)",
                },
              ]}
            >
              <Text style={[s.connectHint, { color: C.isDark ? "rgba(226,232,240,0.72)" : "#64748B" }]}>
                Uses exact content from this page — fresh PDF, no old cache
              </Text>
              <Pressable
                onPress={handleConnectToPdf}
                disabled={pdfConnecting}
                style={[s.connectBtn, pdfConnecting && { opacity: 0.75 }]}
              >
                <LinearGradient
                  colors={["#9333ea", "#ec4899"]}
                  start={{ x: 0, y: 0 }}
                  end={{ x: 1, y: 0 }}
                  style={s.connectBtnGrad}
                >
                  {pdfConnecting ? (
                    <>
                      <ActivityIndicator size="small" color="#fff" />
                      <Text style={s.connectBtnTxt}>Connecting to PDF…</Text>
                    </>
                  ) : (
                    <>
                      <Feather name="link-2" size={18} color="#fff" />
                      <Text style={s.connectBtnTxt}>Connect to PDF</Text>
                    </>
                  )}
                </LinearGradient>
              </Pressable>
            </View>
          </>
        ) : null}
      </View>
    </CosmicBg>
  );
}

const ld = StyleSheet.create({
  wrap: { flex: 1, alignItems: "center", justifyContent: "center", padding: 24 },
  borderGrad: { borderRadius: 22, padding: 1.5, width: "100%", maxWidth: 380 },
  card: {
    borderRadius: 20,
    paddingVertical: 28,
    paddingHorizontal: 22,
    alignItems: "center",
    gap: 10,
  },
  iconCircle: {
    width: 68,
    height: 68,
    borderRadius: 34,
    alignItems: "center",
    justifyContent: "center",
    marginBottom: 6,
  },
  title: { fontFamily: "Nunito_800ExtraBold", fontSize: 20, letterSpacing: -0.3 },
  stage: {
    fontFamily: "Nunito_500Medium",
    fontSize: 13,
    textAlign: "center",
    lineHeight: 18,
    minHeight: 36,
    paddingHorizontal: 8,
  },
  track: { height: 10, borderRadius: 5, overflow: "hidden", width: "100%", marginTop: 8 },
  fillWrap: { height: 10, borderRadius: 5, overflow: "hidden", minWidth: 0 },
  fill: { width: "100%", height: 10, borderRadius: 5 },
  pctRow: {
    width: "100%",
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    marginTop: 6,
  },
  pct: { fontFamily: "Nunito_700Bold", fontSize: 24, letterSpacing: -0.5 },
  hint: { flex: 1, textAlign: "right", fontFamily: "Nunito_500Medium", fontSize: 10.5, marginLeft: 8 },
});

const s = StyleSheet.create({
  shell: { flex: 1 },
  header: {
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: 16,
    paddingBottom: 10,
    gap: 8,
  },
  headerTitle: { flex: 1, textAlign: "center", fontFamily: "Nunito_700Bold", fontSize: 17 },
  savePdfBtn: {
    flexDirection: "row",
    alignItems: "center",
    gap: 4,
    backgroundColor: "#ec4899",
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 999,
    minWidth: 88,
    justifyContent: "center",
  },
  savePdfTxt: { color: "#fff", fontFamily: "Nunito_700Bold", fontSize: 10.5 },
  connectBar: {
    position: "absolute",
    left: 0,
    right: 0,
    bottom: 0,
    paddingHorizontal: 16,
    paddingTop: 10,
    borderTopWidth: StyleSheet.hairlineWidth,
    gap: 8,
  },
  connectHint: {
    fontFamily: "Nunito_500Medium",
    fontSize: 11.5,
    textAlign: "center",
    lineHeight: 16,
  },
  connectBtn: { borderRadius: 14, overflow: "hidden" },
  connectBtnGrad: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
    paddingVertical: 14,
    paddingHorizontal: 18,
  },
  connectBtnTxt: { color: "#fff", fontFamily: "Nunito_800ExtraBold", fontSize: 16 },
  center: { flex: 1, alignItems: "center", justifyContent: "center", padding: 24, gap: 12 },
  errTxt: { fontFamily: "Nunito_500Medium", fontSize: 14, textAlign: "center" },
  retryBtn: {
    marginTop: 8,
    backgroundColor: "#ec4899",
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 10,
  },
  retryTxt: { color: "#fff", fontFamily: "Nunito_700Bold", fontSize: 14 },
});
