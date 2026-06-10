import { Feather } from "@expo/vector-icons";
import { LinearGradient } from "expo-linear-gradient";
import { router, useLocalSearchParams } from "expo-router";
import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
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
  buildReportSectionsFromPayload,
  fetchLoveRealityProReport,
  loveRealityReportLabels,
  type LoveProReportResponse,
} from "@/lib/loveRealityProReport";
import {
  clearLoveReportCacheAllLangs,
  purgeHiDeviceCacheIfNeeded,
  deviceCacheNeedsServerRefresh,
  markLoveReportPdfSynced,
  resolveLoveReportCache,
  saveLoveReportCache,
  touchLoveReportCacheRevision,
} from "@/lib/loveRealityProReportCache";
import type { LoveReportChangeKind } from "@/lib/loveRealityReportRevision";
import { connectLoveRealityPageToPdf } from "@/lib/loveRealityProPdfDownload";
import { coerceProPdfLang, type ProPdfLangCode } from "@/lib/proPdfLang";
import {
  reportHasDisplayableContent,
  reportHindiFullyReady,
  section8HiLoadGate,
  section8HiLoadReady,
  reportNeedsHindiRetry,
  reportSummaryMatchesLang,
} from "@/lib/loveRealityReportLang";

const LOVE_REALITY_LAST_LANG_KEY = "cosmic.loveRealityPro.lastLang";

function routeLangParam(raw: string | string[] | undefined): ProPdfLangCode {
  const one = Array.isArray(raw) ? raw[0] : raw;
  return coerceProPdfLang(one);
}

const LOAD_STAGES = [
  "Loading your charts…",
  "Running compatibility engines…",
  "Writing personalized insights…",
  "Generating Hinglish report…",
  "Almost ready…",
] as const;

function ReportLoadingView({
  pct,
  stageIdx,
  isDark,
  done,
  fromCache,
  cacheChange,
  llmRefresh,
  forceUpdate,
  updateHint,
  lang,
}: {
  pct: number;
  stageIdx: number;
  isDark: boolean;
  done: boolean;
  fromCache: boolean;
  cacheChange: LoveReportChangeKind;
  llmRefresh: boolean;
  forceUpdate: boolean;
  updateHint: string;
  lang: ProPdfLangCode;
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
            {done ? "Report ready!" : forceUpdate ? "Updating report…" : "Loading…"}
          </Text>
          <Text style={[ld.stage, { color: dim }]}>
            {done
              ? "Opening your Love Reality Pro report"
              : forceUpdate
                ? updateHint
                : cacheChange === "app_layout"
                ? "Updating report…"
                : llmRefresh
                  ? (lang === "hi"
                    ? "Hindi report likh rahe hain — 1–2 min"
                    : lang === "hn"
                      ? "Hinglish report likh rahe hain — 1–2 min"
                      : "Writing your report — 1–2 min")
                  : cacheChange === "pdf_layout"
                  ? "Preparing report…"
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
  const params = useLocalSearchParams<{ partnerId?: string; lang?: string | string[] }>();
  const [lang, setLang] = useState<ProPdfLangCode>(() => routeLangParam(params.lang));
  const labels = loveRealityReportLabels(lang);

  useEffect(() => {
    const fromRoute = routeLangParam(params.lang);
    if (params.lang) {
      setLang(fromRoute);
      return;
    }
    void (async () => {
      try {
        const AsyncStorage = (await import("@react-native-async-storage/async-storage")).default;
        const stored = await AsyncStorage.getItem(LOVE_REALITY_LAST_LANG_KEY);
        if (stored) setLang(coerceProPdfLang(stored));
      } catch {
        /* ignore */
      }
    })();
  }, [params.lang]);

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
  const [cacheChange, setCacheChange] = useState<LoveReportChangeKind>("missing");
  const [llmRefresh, setLlmRefresh] = useState(false);
  const [pdfConnecting, setPdfConnecting] = useState(false);
  const [updatingReport, setUpdatingReport] = useState(false);
  const [forceUpdateRun, setForceUpdateRun] = useState(false);
  const [reportEpoch, setReportEpoch] = useState(0);
  const loadedRef = useRef(false);
  const fetchDoneRef = useRef(false);
  const fastCacheRef = useRef(false);
  const showReportTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const finishLoad = useCallback((data: LoveProReportResponse, cached: boolean) => {
    fetchDoneRef.current = true;
    fastCacheRef.current = cached;
    setFromCache(cached);
    setReport(data);
    setFetching(false);
    setLoadDone(true);
    setLoadPct(100);
    if (showReportTimerRef.current) clearTimeout(showReportTimerRef.current);
    showReportTimerRef.current = setTimeout(() => {
      setShowReport(true);
      showReportTimerRef.current = null;
    }, cached ? 300 : 650);
  }, []);

  const load = useCallback(async (opts?: { forceUpdate?: boolean }) => {
    if (!user?.id || !primaryProfile?.birthData || !partnerProfile?.birthData) {
      setError("Complete both kundlis and sign in to read the report.");
      setFetching(false);
      setUpdatingReport(false);
      return;
    }
    const forceUpdate = Boolean(opts?.forceUpdate);
    if (showReportTimerRef.current) {
      clearTimeout(showReportTimerRef.current);
      showReportTimerRef.current = null;
    }
    if (forceUpdate) {
      setReportEpoch(n => n + 1);
    } else {
      setReport(null);
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
    setCacheChange("missing");
    setLlmRefresh(forceUpdate);
    setForceUpdateRun(forceUpdate);
    if (forceUpdate) setUpdatingReport(true);

    const cacheOpts = {
      userId: user.id,
      p1: primaryProfile.birthData,
      p2: partnerProfile.birthData,
      p1Name: primaryProfile.name || "You",
      p2Name: partnerProfile.name || "Partner",
      lang,
    };

    try {
      if (lang === "hi") {
        await purgeHiDeviceCacheIfNeeded({
          userId: cacheOpts.userId,
          p1: cacheOpts.p1,
          p2: cacheOpts.p2,
          p1Name: cacheOpts.p1Name,
          p2Name: cacheOpts.p2Name,
        });
      }
      if (forceUpdate) {
        await clearLoveReportCacheAllLangs({
          userId: cacheOpts.userId,
          p1: cacheOpts.p1,
          p2: cacheOpts.p2,
          p1Name: cacheOpts.p1Name,
          p2Name: cacheOpts.p2Name,
        });
      }

      let mustLlm = forceUpdate;
      if (!forceUpdate) {
        const resolved = await resolveLoveReportCache(cacheOpts);
        setCacheChange(resolved.changeKind);
        mustLlm = deviceCacheNeedsServerRefresh(resolved.payload, resolved.meta, lang);
        setLlmRefresh(mustLlm);

        if (
          resolved.payload
          && !mustLlm
          && resolved.changeKind === "app_layout"
          && lang === "en"
        ) {
          await touchLoveReportCacheRevision({
            ...cacheOpts,
            polishSource: resolved.payload.polish_source,
          });
          finishLoad(resolved.payload, true);
          return;
        }

        if (resolved.payload && !mustLlm && resolved.changeKind === "none") {
          if (lang === "hi" && !section8HiLoadReady(resolved.payload, lang)) {
            // Stale device cache — server cache/rebuild, not silent full LLM update.
          } else {
            finishLoad(resolved.payload, true);
            return;
          }
        }
      }

      const ctrl = new AbortController();
      const timer = setTimeout(() => ctrl.abort(), 360000);
      try {
        const fetchReport = (mode: "full" | "relocalize" | "cache") => fetchLoveRealityProReport({
          user,
          p1: primaryProfile.birthData,
          p2: partnerProfile.birthData,
          p1Name: primaryProfile.name || "You",
          p2Name: partnerProfile.name || "Partner",
          lang,
          signal: ctrl.signal,
          fullUpdate: mode === "full",
          forceLlm: mode === "full",
          relocalizeOnly: mode === "relocalize",
          cacheBust: mode === "full" ? Date.now() : 0,
          layoutRefresh: false,
        });

        let { data, serverCacheHit } = await fetchReport(forceUpdate || mustLlm ? "full" : "cache");

        if (lang !== "en" && data.polish_source === "polish_snapshot") {
          const fresh = await fetchReport("full");
          data = fresh.data;
          serverCacheHit = fresh.serverCacheHit;
        }

        for (let attempt = 0; attempt < 2 && lang !== "en"; attempt += 1) {
          if (!reportNeedsHindiRetry(data, lang)) break;
          const retry = await fetchReport("relocalize");
          data = retry.data;
          serverCacheHit = retry.serverCacheHit;
        }

        if (!reportHasDisplayableContent(data)) {
          setError("Report empty — dubara Update dabayein.");
          setFetching(false);
          setUpdatingReport(false);
          setForceUpdateRun(false);
          return;
        }
        if (lang === "hi") {
          const s8 = section8HiLoadGate(data);
          if (!s8.ok) {
            setError(s8.reason);
            setFetching(false);
            setUpdatingReport(false);
            setForceUpdateRun(false);
            return;
          }
        }
        const hindiOk = reportHindiFullyReady(data, lang);
        await saveLoveReportCache(cacheOpts, data);
        finishLoad(data, false);
        if (forceUpdate) {
          const script = (data.content_script || "").trim();
          const hint = hindiOk
            ? labels.updateHint
            : script === "hi_partial"
              ? "Report update hua — kuch lines abhi English hain. 30 sec baad dubara Update dabayein."
              : "Report update hua. Agar English dikhe to dubara Update dabayein.";
          Alert.alert(labels.updateDone, hint, [{ text: labels.ok }]);
        }
      } finally {
        clearTimeout(timer);
      }
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Could not load report";
      setError(/abort/i.test(msg) ? "Report timed out — tap Retry." : msg);
      setFetching(false);
    } finally {
      setUpdatingReport(false);
      setForceUpdateRun(false);
    }
  }, [user, primaryProfile, partnerProfile, lang, finishLoad, labels]);

  useEffect(() => () => {
    if (showReportTimerRef.current) clearTimeout(showReportTimerRef.current);
  }, []);

  useEffect(() => {
    loadedRef.current = false;
    fetchDoneRef.current = false;
  }, [lang, params.partnerId]);

  useEffect(() => {
    if (loadedRef.current) return;
    loadedRef.current = true;
    load();
  }, [load, lang, params.partnerId]);

  useEffect(() => {
    if (!fetching || fetchDoneRef.current) return;
    const fast = fastCacheRef.current || (cacheChange === "app_layout" && !forceUpdateRun);
    const tickMs = fast ? 70 : 900;
    const step = fast ? 10 : 1;
    const cap = fast ? 100 : 90;
    const tick = setInterval(() => {
      setLoadPct(p => (p >= cap ? cap : Math.min(cap, p + step)));
    }, tickMs);
    return () => clearInterval(tick);
  }, [fetching, cacheChange, forceUpdateRun]);

  useEffect(() => {
    if (!fetching || fetchDoneRef.current) return;
    const tick = setInterval(() => {
      setStageIdx(i => (i + 1) % LOAD_STAGES.length);
    }, 3200);
    return () => clearInterval(tick);
  }, [fetching]);

  const handleUpdateReport = useCallback(() => {
    if (updatingReport) return;
    void load({ forceUpdate: true });
  }, [updatingReport, load]);

  const sections = useMemo(
    () => (report ? buildReportSectionsFromPayload(report, lang) : []),
    [report, lang, reportEpoch],
  );

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
          labels.alertRefreshTitle,
          labels.alertRefreshBody,
          [{ text: labels.ok }],
        );
      }
      return;
    }
    setPdfConnecting(true);
    try {
      if (!sections.length) {
        Alert.alert(
          labels.alertRefreshTitle,
          labels.alertRefreshBody,
          [{ text: labels.ok }],
        );
        return;
      }
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
        appSections: sections,
        scores: report.scores,
      });
      const fromCache = result.reportCacheHit ? " (server cache)" : "";
      const mirrorNote = result.pdfSource === "app_mirror_fresh"
        ? "Built from this page — 1–3 sec is normal, not old cache."
        : `Source: ${result.pdfSource || "fresh render"}${fromCache}.`;
      Alert.alert(
        labels.alertPdfSaved,
        result.savedToRegistry
          ? `${mirrorNote} Saved to My Reports — open the newest entry (Downloaded from page).`
          : mirrorNote,
        [
          { text: labels.ok, style: "cancel" },
          ...(result.savedToRegistry
            ? [{
                text: "Open My Reports",
                onPress: () => router.push("/my-reports" as never),
              }]
            : []),
        ],
      );
      if (user?.id && primaryProfile?.birthData && partnerProfile?.birthData) {
        await markLoveReportPdfSynced({
          userId: user.id,
          p1: primaryProfile.birthData,
          p2: partnerProfile.birthData,
          p1Name: primaryProfile.name || "You",
          p2Name: partnerProfile.name || "Partner",
          lang,
        });
      }
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Could not download PDF";
      Alert.alert(labels.alertPdfFailed, msg, [{ text: labels.ok }]);
    } finally {
      setPdfConnecting(false);
    }
  }, [user, primaryProfile, partnerProfile, lang, pdfConnecting, report, labels, sections]);

  const isLoadingUi = fetching && !report;

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
                  <Feather name="download" size={13} color="#fff" />
                  <Text style={s.savePdfTxt}>{labels.downloadPdf}</Text>
                </>
              )}
            </Pressable>
          ) : (
            <View style={{ width: 96 }} />
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
                const section8Blocked = /Section 8|section8_not_ready/i.test(error);
                load({ forceUpdate: section8Blocked });
                loadedRef.current = true;
              }}
              style={s.retryBtn}
            >
              <Text style={s.retryTxt}>
                {/Section 8|section8_not_ready/i.test(error) ? labels.updateReport : labels.retry}
              </Text>
            </Pressable>
          </View>
        ) : isLoadingUi ? (
          <ReportLoadingView
            pct={loadPct}
            stageIdx={stageIdx}
            isDark={C.isDark}
            done={loadDone}
            fromCache={fromCache}
            cacheChange={cacheChange}
            llmRefresh={llmRefresh}
            forceUpdate={forceUpdateRun}
            updateHint={labels.updateHint}
            lang={lang}
          />
        ) : report && showReport ? (
          <>
            <Pressable
              onPress={handleUpdateReport}
              disabled={updatingReport}
              style={[
                s.updateBar,
                {
                  backgroundColor: C.isDark ? "rgba(139,92,246,0.18)" : "rgba(139,92,246,0.1)",
                  borderColor: C.isDark ? "rgba(167,139,250,0.45)" : "rgba(139,92,246,0.35)",
                  opacity: updatingReport ? 0.65 : 1,
                },
              ]}
            >
              {updatingReport ? (
                <ActivityIndicator size="small" color="#8B5CF6" />
              ) : (
                <Feather name="refresh-cw" size={16} color="#8B5CF6" />
              )}
              <View style={{ flex: 1 }}>
                <Text style={[s.updateBarTitle, { color: C.isDark ? "#E9D5FF" : "#5B21B6" }]}>
                  {updatingReport ? labels.updatingReport : labels.updateReport}
                </Text>
                <Text style={[s.updateBarSub, { color: C.isDark ? "rgba(226,232,240,0.72)" : "#64748B" }]}>
                  {labels.updateHint}
                </Text>
              </View>
              <Feather name="chevron-right" size={18} color="#8B5CF6" />
            </Pressable>
            <ScrollView
              contentContainerStyle={{ paddingHorizontal: 16, paddingBottom: insets.bottom + 24 }}
              showsVerticalScrollIndicator={false}
            >
              <LoveRealityProReportView
                key={`lr-report-${reportEpoch}`}
                isDark={C.isDark}
                lang={lang}
                p1Name={report.p1_name}
                p2Name={report.p2_name}
                scores={report.scores}
                sections={sections}
              />
            </ScrollView>
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
    alignItems: "center",
    marginTop: 6,
  },
  pct: { fontFamily: "Nunito_700Bold", fontSize: 24, letterSpacing: -0.5 },
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
  updateBar: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    marginHorizontal: 16,
    marginBottom: 10,
    paddingHorizontal: 14,
    paddingVertical: 12,
    borderRadius: 14,
    borderWidth: 1,
  },
  updateBarTitle: { fontFamily: "Nunito_700Bold", fontSize: 14 },
  updateBarSub: { fontFamily: "Nunito_500Medium", fontSize: 11, marginTop: 2, lineHeight: 15 },
  savePdfBtn: {
    flexDirection: "row",
    alignItems: "center",
    gap: 4,
    backgroundColor: "#ec4899",
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 999,
    minWidth: 96,
    justifyContent: "center",
  },
  savePdfTxt: { color: "#fff", fontFamily: "Nunito_700Bold", fontSize: 10 },
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
