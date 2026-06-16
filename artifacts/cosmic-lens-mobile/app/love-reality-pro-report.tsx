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
  loveReportLlmCostInr,
  type LoveProReportResponse,
} from "@/lib/loveRealityProReport";
import {
  clearLoveReportCacheAllLangs,
  purgeEnDeviceCacheIfNeeded,
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
  enHnReportCacheReady,
  englishLlmNarrativeReady,
  reportContentMatchesLang,
  reportHasDisplayableContent,
  hindiReportPageLoadReady,
  reportNeedsHindiRetry,
  reportSummaryMatchesLang,
} from "@/lib/loveRealityReportLang";

const LOVE_REALITY_LAST_LANG_KEY = "cosmic.loveRealityPro.lastLang";

function routeLangParam(raw: string | string[] | undefined): ProPdfLangCode {
  const one = Array.isArray(raw) ? raw[0] : raw;
  return coerceProPdfLang(one);
}

/** Fixed steps — % only advances when that stage completes (LLM step creeps slowly, max 82). */
const LOAD_STEPS = [
  { n: 1, pct: 10, label: "Preparing your report…" },
  { n: 2, pct: 20, label: "Checking saved report…" },
  { n: 3, pct: 30, label: "Loading birth charts…" },
  { n: 4, pct: 40, label: "Connecting to server…" },
  { n: 5, pct: 50, label: "Writing personalized insights…", llm: true, creepCap: 82 },
  { n: 6, pct: 88, label: "Building report sections…" },
  { n: 7, pct: 94, label: "Almost ready…" },
] as const;

const OPEN_AT_PCT = 100;
const READY_PCT = 99;
const LLM_CREEP_MS = 5_000;

function reportFetchTimeoutMs(lang: ProPdfLangCode): number {
  if (lang === "hi") return 600_000;
  if (lang === "hn") return 480_000;
  return 300_000;
}

function loadStageLabel(lang: ProPdfLangCode, stepN: number): string {
  const step = LOAD_STEPS.find(s => s.n === stepN);
  const base = step?.label || "Loading…";
  if (stepN === 5) {
    if (lang === "hi") return "Hindi report likh rahe hain — 2–5 min…";
    if (lang === "hn") return "Hinglish report likh rahe hain — 2–5 min…";
    return "Writing your report — 2–4 min…";
  }
  if (lang === "hi" && stepN === 3) return "Charts load ho rahe hain…";
  if (lang === "hn" && stepN === 3) return "Charts load ho rahe hain…";
  return base;
}

function ReportLoadingView({
  pct,
  loadStep,
  isDark,
  fromCache,
  cacheChange,
  llmRefresh,
  forceUpdate,
  updateHint,
  lang,
}: {
  pct: number;
  loadStep: number;
  isDark: boolean;
  fromCache: boolean;
  cacheChange: LoveReportChangeKind;
  llmRefresh: boolean;
  forceUpdate: boolean;
  updateHint: string;
  lang: ProPdfLangCode;
}) {
  const opening = pct >= READY_PCT;
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
    if (opening) return;
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
  }, [opening, spinAnim]);

  useEffect(() => {
    if (opening) return;
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
  }, [opening, pulseAnim]);

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
          <Animated.View style={{ transform: [{ scale: opening ? 1 : pulseAnim }] }}>
            <LinearGradient
              colors={opening ? ["#10B981", "#059669"] : ["#9333ea", "#ec4899"]}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 1 }}
              style={ld.iconCircle}
            >
              {opening ? (
                <Feather name="check" size={32} color="#fff" />
              ) : (
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
              )}
            </LinearGradient>
          </Animated.View>

          <Text style={[ld.title, { color: text }]}>
            {pct >= READY_PCT
              ? "Opening report…"
              : forceUpdate
                ? "Updating report…"
                : "Loading…"}
          </Text>
          <Text style={[ld.stage, { color: dim }]}>
            {pct >= READY_PCT
              ? "Love Reality Pro report"
              : forceUpdate
                ? updateHint
                : cacheChange === "app_layout"
                ? "Updating report…"
                : llmRefresh
                  ? (lang === "hi"
                    ? "Hindi report likh rahe hain — 2–5 min"
                    : lang === "hn"
                      ? "Hinglish report likh rahe hain — 2–5 min"
                      : "Writing your report — 2–4 min")
                  : cacheChange === "pdf_layout"
                  ? "Preparing report…"
                  : fromCache
                    ? "Loading saved report…"
                    : loadStageLabel(lang, loadStep)}
          </Text>

          {loadStep > 0 && pct < READY_PCT ? (
            <Text style={[ld.stepTag, { color: dim }]}>
              Step {loadStep} / {LOAD_STEPS.length}
            </Text>
          ) : null}

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
  const [loadStep, setLoadStepState] = useState(0);
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
  const awaitingLlmRef = useRef(false);
  const showReportTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const setLoadStep = useCallback((stepNum: number) => {
    const step = LOAD_STEPS.find(s => s.n === stepNum);
    if (!step) return;
    awaitingLlmRef.current = Boolean("llm" in step && step.llm);
    setLoadStepState(stepNum);
    setLoadPct(prev => (step.pct > prev ? step.pct : prev));
  }, []);

  const finishLoad = useCallback((data: LoveProReportResponse, cached: boolean) => {
    fetchDoneRef.current = true;
    awaitingLlmRef.current = false;
    fastCacheRef.current = cached;
    setFromCache(cached);
    setReport(data);
    setLoadStepState(LOAD_STEPS.length);
    setLoadPct(READY_PCT);
    if (showReportTimerRef.current) clearTimeout(showReportTimerRef.current);
    showReportTimerRef.current = setTimeout(() => {
      setLoadPct(OPEN_AT_PCT);
      showReportTimerRef.current = setTimeout(() => {
        setShowReport(true);
        setFetching(false);
        showReportTimerRef.current = null;
      }, cached ? 200 : 350);
    }, cached ? 320 : 520);
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
    setLoadStepState(0);
    setShowReport(false);
    setError(null);
    fetchDoneRef.current = false;
    fastCacheRef.current = false;
    awaitingLlmRef.current = false;
    setFromCache(false);
    setLoadStep(1);
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
      } else if (lang === "en") {
        await purgeEnDeviceCacheIfNeeded({
          userId: cacheOpts.userId,
          p1: cacheOpts.p1,
          p2: cacheOpts.p2,
          p1Name: cacheOpts.p1Name,
          p2Name: cacheOpts.p2Name,
        });
      }
      setLoadStep(2);
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
      let deviceCacheEmpty = true;
      if (!forceUpdate) {
        const resolved = await resolveLoveReportCache(cacheOpts);
        deviceCacheEmpty = !resolved.payload;
        setLoadStep(3);
        setCacheChange(resolved.changeKind);
        mustLlm = deviceCacheNeedsServerRefresh(resolved.payload, resolved.meta, lang);
        setLlmRefresh(mustLlm);

        if (
          resolved.payload
          && !mustLlm
          && resolved.changeKind === "app_layout"
          && (lang === "en" || lang === "hn")
        ) {
          await touchLoveReportCacheRevision({
            ...cacheOpts,
            polishSource: resolved.payload.polish_source,
          });
          setLoadStep(7);
          finishLoad(resolved.payload, true);
          return;
        }

        if (resolved.payload && !mustLlm && resolved.changeKind === "none") {
          const hiStale = lang === "hi" && !hindiReportPageLoadReady(resolved.payload, lang).ok;
          const enHnReady = (lang === "en" || lang === "hn")
            && enHnReportCacheReady(resolved.payload, lang);
          if (hiStale) {
            // Stale Hindi device cache — refetch from server.
          } else if (lang === "hi" || enHnReady) {
            setLoadStep(7);
            finishLoad(resolved.payload, true);
            return;
          }
        }

        // Reinstall / clear data — restore from server account cache (same login + couple).
        if (!resolved.payload && (lang === "en" || lang === "hn")) {
          fastCacheRef.current = true;
          setFromCache(true);
          setLoadStep(4);
          try {
            const restored = await fetchLoveRealityProReport({
              user,
              p1: primaryProfile.birthData,
              p2: partnerProfile.birthData,
              p1Name: primaryProfile.name || "You",
              p2Name: partnerProfile.name || "Partner",
              lang,
              preferServerCache: true,
            });
            if (
              restored.serverCacheHit
              && reportHasDisplayableContent(restored.data)
            ) {
              await saveLoveReportCache(cacheOpts, restored.data);
              setLoadStep(7);
              finishLoad(restored.data, true);
              return;
            }
          } catch {
            /* fall through — first-time generate */
          }
        }
      }

      setLoadStep(4);
      const fetchReport = async (mode: "full" | "relocalize" | "cache") => {
        const ctrl = new AbortController();
        const timer = setTimeout(() => ctrl.abort(), reportFetchTimeoutMs(lang));
        try {
          return await fetchLoveRealityProReport({
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
        } finally {
          clearTimeout(timer);
        }
      };

      const useFullFetch = forceUpdate || mustLlm || deviceCacheEmpty;
      fastCacheRef.current = !useFullFetch && !mustLlm;
      setLoadStep(5);
      let { data, serverCacheHit } = await fetchReport(
        useFullFetch ? "full" : "cache",
      );

      const snapshotNeedsRegen =
        data.polish_source === "polish_snapshot"
        && (
          lang === "hi"
            ? !hindiReportPageLoadReady(data, lang).ok
            : !reportContentMatchesLang(data, lang)
            || (lang === "en" && !englishLlmNarrativeReady(data))
        );
      if (snapshotNeedsRegen) {
        setLoadStep(5);
        const fresh = await fetchReport("full");
        data = fresh.data;
        serverCacheHit = fresh.serverCacheHit;
      }

      if (
        !forceUpdate
        && lang === "en"
        && (!reportContentMatchesLang(data, lang) || !englishLlmNarrativeReady(data))
      ) {
        setLoadStep(5);
        const fresh = await fetchReport("full");
        data = fresh.data;
        serverCacheHit = fresh.serverCacheHit;
      } else if (!forceUpdate && lang === "hn" && reportNeedsHindiRetry(data, lang)) {
        setLoadStep(5);
        const retry = await fetchReport("relocalize");
        data = retry.data;
        serverCacheHit = retry.serverCacheHit;
      } else if (
        !forceUpdate
        && lang === "hi"
        && !hindiReportPageLoadReady(data, lang).ok
      ) {
        setLoadStep(5);
        const retry = await fetchReport("full");
        data = retry.data;
        serverCacheHit = retry.serverCacheHit;
      }

        setLoadStep(6);

        if (!reportHasDisplayableContent(data)) {
          setError("Report empty — dubara Update dabayein.");
          setFetching(false);
          setLoadPct(0);
          setUpdatingReport(false);
          setForceUpdateRun(false);
          return;
        }
        if (lang === "hi") {
          let hiReady = hindiReportPageLoadReady(data, lang);
          if (!hiReady.ok && !forceUpdate) {
            setLoadStep(5);
            const retry = await fetchReport("full");
            data = retry.data;
            serverCacheHit = retry.serverCacheHit;
            hiReady = hindiReportPageLoadReady(data, lang);
          }
          if (!hiReady.ok) {
            const dbg4 = (data as { section4_debug?: { llm_source?: string; words?: number; deva?: number } }).section4_debug;
            const dbg8 = (data as { section8_debug?: { gate_ver?: string; breakup_deva?: number } }).section8_debug;
            const script = (data.content_script || "").trim();
            let extra = "";
            if (dbg4?.llm_source) {
              extra += ` [s4 llm=${dbg4.llm_source}, words=${dbg4.words ?? "?"}, deva=${dbg4.deva ?? "?"}]`;
            }
            if (dbg8?.gate_ver) {
              extra += ` [s8 ${dbg8.gate_ver}, deva=${dbg8.breakup_deva ?? "?"}]`;
            }
            if (script) extra += ` [script=${script}]`;
            setError(hiReady.reason + extra);
            setFetching(false);
            setLoadPct(0);
            setUpdatingReport(false);
            setForceUpdateRun(false);
            return;
          }
        }
        setLoadStep(7);
        try {
          await saveLoveReportCache(cacheOpts, data);
        } catch {
          /* open report even if device save fails */
        }
        finishLoad(data, serverCacheHit || enHnReportCacheReady(data, lang));
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Could not load report";
      const timedOut = /abort/i.test(msg);
      setError(
        timedOut
          ? (lang === "hi"
            ? "Hindi report timeout — server 5–10 min leta hai. «पुनः» dabayein."
            : lang === "hn"
              ? "Hinglish report timeout — 5–8 min wait karo, phir Retry dabao."
              : "Report timed out — tap Retry.")
          : msg,
      );
      setFetching(false);
      setLoadPct(0);
    } finally {
      setUpdatingReport(false);
      setForceUpdateRun(false);
    }
  }, [user, primaryProfile, partnerProfile, lang, finishLoad, labels, setLoadStep]);

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
    if (!fetching || fetchDoneRef.current || !awaitingLlmRef.current) return;
    const llmStep = LOAD_STEPS.find(s => "llm" in s && s.llm);
    const cap = llmStep?.creepCap ?? 82;
    const tick = setInterval(() => {
      if (fetchDoneRef.current || !awaitingLlmRef.current) return;
      setLoadPct(prev => (prev >= cap ? prev : prev + 1));
    }, LLM_CREEP_MS);
    return () => clearInterval(tick);
  }, [fetching, loadStep]);

  const sections = useMemo(
    () => (report ? buildReportSectionsFromPayload(report, lang) : []),
    [report, lang, reportEpoch],
  );

  const llmCostInr = useMemo(
    () => (report ? loveReportLlmCostInr(report) : null),
    [report, reportEpoch],
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
      Alert.alert(
        labels.alertPdfSaved,
        result.savedToRegistry ? labels.alertPdfSavedBody : labels.alertPdfSaveFailed,
        [
          { text: labels.ok, style: "cancel" },
          ...(result.savedToRegistry
            ? [{
                text: labels.openMyReports,
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

  const isLoadingUi = !error && !showReport;

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
            <View style={s.headerRight}>
              {llmCostInr != null ? (
                <Text style={[s.llmCostTxt, { color: C.isDark ? "#A5B4FC" : "#6366F1" }]}>
                  {llmCostInr}
                </Text>
              ) : null}
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
            </View>
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
                load();
                loadedRef.current = true;
              }}
              style={s.retryBtn}
            >
              <Text style={s.retryTxt}>{labels.retry}</Text>
            </Pressable>
          </View>
        ) : isLoadingUi ? (
          <ReportLoadingView
            pct={loadPct}
            loadStep={loadStep}
            isDark={C.isDark}
            fromCache={fromCache}
            cacheChange={cacheChange}
            llmRefresh={llmRefresh}
            forceUpdate={forceUpdateRun}
            updateHint={labels.updateHint}
            lang={lang}
          />
        ) : report && showReport ? (
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
  stepTag: {
    fontFamily: "Nunito_600SemiBold",
    fontSize: 12,
    letterSpacing: 0.4,
    marginTop: -4,
    marginBottom: 2,
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
  headerRight: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    minWidth: 96,
    justifyContent: "flex-end",
  },
  llmCostTxt: {
    fontFamily: "Nunito_800ExtraBold",
    fontSize: 13,
    letterSpacing: 0.2,
  },
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
