import { Feather } from "@expo/vector-icons";
import { LinearGradient } from "expo-linear-gradient";
import * as Haptics from "expo-haptics";
import { router, useFocusEffect } from "expo-router";
import React, { useCallback, useRef, useState } from "react";
import {
  ActivityIndicator,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";

import { LoveRealityToolSectionContent } from "@/components/loveReality/LoveRealityToolResultPanel";
import { useUser } from "@/context/UserContext";
import { apiFetch, apiFetchBases, userAuthHeaders } from "@/lib/apiConfig";
import { coerceLoveBasicLang, pickLoveBasicCopy } from "@/lib/loveRealityBasicLang";
import { loveRealityProScreenCopy } from "@/lib/loveRealityProCopyI18n";
import { LOVE_REALITY_PRO_CTA_LABEL } from "@/lib/loveRealityProCopy";
import {
  buildLoyaltyCompareFromJson,
  buildLoveCompatDetailFromJson,
  mapLoveRealityResult,
  resolveLoyaltyCompare,
  type LoveRealityBasicDisplay,
  type LoveRealityToolKey,
  type LoyaltyCompareData,
} from "@/lib/loveRealityToolMappers";
import { LOVE_REALITY_TOOLS, type LoveRealityToolDef } from "@/lib/loveRealityToolsConfig";
import { coerceProPdfLang } from "@/lib/proPdfLang";
import type { BirthData } from "@/types";

function packPerson(bd: BirthData) {
  return {
    name: bd.name,
    day: bd.day,
    month: bd.month,
    year: bd.year,
    hour: bd.hour,
    minute: bd.minute,
    ampm: bd.ampm,
    lat: bd.lat,
    lon: bd.lon,
    tz: bd.tz,
    place: bd.place,
  };
}

type ResultsMap = Partial<Record<LoveRealityToolKey, LoveRealityBasicDisplay>>;
type RawResultsMap = Partial<Record<LoveRealityToolKey, Record<string, unknown>>>;

function resolveLoyaltyForTool(
  toolKey: LoveRealityToolKey,
  rawResults: RawResultsMap,
  display?: LoveRealityBasicDisplay,
): LoyaltyCompareData | undefined {
  if (toolKey !== "loyalty") return undefined;
  return (
    resolveLoyaltyCompare(rawResults.loyalty, rawResults["love-compat"]) ??
    display?.loyaltyCompare ??
    (rawResults.loyalty ? buildLoyaltyCompareFromJson(rawResults.loyalty) : undefined)
  );
}

function ToolSectionHeader({ tool, isDark }: { tool: LoveRealityToolDef; isDark: boolean }) {
  const textHi = isDark ? "#fff" : "#0F172A";
  const [c1, c2] = tool.gradient;
  return (
    <View style={u.sectionHead}>
      <LinearGradient colors={[c1, c2]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }} style={u.sectionBadge}>
        <Text style={u.sectionEmoji}>{tool.emoji}</Text>
      </LinearGradient>
      <View style={{ flex: 1, gap: 2 }}>
        <Text style={[u.sectionTitle, { color: textHi }]}>{tool.title}</Text>
      </View>
    </View>
  );
}

export function LoveRealityUnifiedBasic({
  isDark,
  bottomPad,
  primaryProfile,
  partnerProfile,
  onOpenPro,
}: {
  isDark: boolean;
  bottomPad: number;
  primaryProfile: { name: string; birthData: BirthData } | null;
  partnerProfile: { name: string; birthData: BirthData } | null;
  initialToolKey?: string;
  onOpenPro: () => void;
}) {
  const { language, user } = useUser();
  const contentLang = coerceLoveBasicLang(language);
  const proUiLang = coerceProPdfLang(language);
  const proScreenCopy = loveRealityProScreenCopy(proUiLang);
  const canAnalyze = !!primaryProfile?.birthData && !!partnerProfile?.birthData;
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<ResultsMap>({});
  const [rawResults, setRawResults] = useState<RawResultsMap>({});
  const [fetchErr, setFetchErr] = useState<string | null>(null);
  const fetchGen = useRef(0);

  const textHi = isDark ? "#fff" : "#0F172A";
  const textLo = isDark ? "rgba(203,213,225,0.65)" : "#64748B";
  const hasResults = LOVE_REALITY_TOOLS.some(tool => results[tool.key]);

  useFocusEffect(
    useCallback(() => {
      if (!canAnalyze) return;
      void fetchAllTools();
    }, [canAnalyze, primaryProfile?.birthData, partnerProfile?.birthData, contentLang]),
  );

  async function fetchAllTools() {
    if (!primaryProfile?.birthData || !partnerProfile?.birthData) return;
    const gen = ++fetchGen.current;
    setLoading(true);
    setFetchErr(null);
    const body = JSON.stringify({
      p1: packPerson(primaryProfile.birthData),
      p2: packPerson(partnerProfile.birthData),
      lang: contentLang,
    });

    const isRetryable = (msg: string) =>
      /Network request failed|Failed to fetch|Load failed|fetch|abort/i.test(msg);

    let lastErr = "Could not load readings";
    for (const base of apiFetchBases()) {
      try {
        const pairs = await Promise.all(
          LOVE_REALITY_TOOLS.map(async tool => {
            const ctrl = new AbortController();
            const timer = setTimeout(() => ctrl.abort(), 35000);
            try {
              const resp = await apiFetch(`${base}${tool.apiPath}`, {
                method: "POST",
                headers: { ...userAuthHeaders(user), "Content-Type": "application/json" },
                body,
                signal: ctrl.signal,
              });
              clearTimeout(timer);
              const json = await resp.json();
              if (!resp.ok || json.error) {
                if (resp.status >= 502 && resp.status <= 504) {
                  throw new Error(`Server busy (${resp.status})`);
                }
                throw new Error(json.error || tool.title);
              }
              return [tool.key, mapLoveRealityResult(tool.key, json as Record<string, unknown>, contentLang), json] as const;
            } catch (e) {
              clearTimeout(timer);
              throw e;
            }
          }),
        );
        if (gen !== fetchGen.current) return;
        const mapped = Object.fromEntries(pairs.map(([k, v]) => [k, v])) as ResultsMap;
        const raw = Object.fromEntries(pairs.map(([k, , r]) => [k, r as Record<string, unknown>])) as RawResultsMap;
        const loyaltyCmp = resolveLoyaltyCompare(raw.loyalty, raw["love-compat"]);
        if (loyaltyCmp && mapped.loyalty) {
          mapped.loyalty = { ...mapped.loyalty, loyaltyCompare: loyaltyCmp };
        }
        const loveDetail = buildLoveCompatDetailFromJson(raw["love-compat"] ?? {});
        if (loveDetail && mapped["love-compat"]) {
          mapped["love-compat"] = { ...mapped["love-compat"], loveDetail };
        }
        setResults(mapped);
        setRawResults(raw);
        Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
        setLoading(false);
        return;
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : String(e);
        lastErr = msg;
        if (isRetryable(msg)) continue;
        break;
      }
    }
    setFetchErr(lastErr);
    setLoading(false);
  }

  if (!canAnalyze) {
    return (
      <View style={u.gate}>
        <Feather name="lock" size={26} color="#f472b6" />
        <Text style={[u.gateTitle, { color: textHi }]}>Partner kundli required</Text>
        <Text style={[u.gateSub, { color: textLo }]}>Select partner on Relationship screen first.</Text>
        <Pressable onPress={() => router.replace("/relationship" as never)} style={{ width: "100%", marginTop: 12 }}>
          <LinearGradient colors={["#ec4899", "#a855f7"]} style={u.gateBtn}>
            <Text style={u.gateBtnTxt}>Go to Relationship</Text>
          </LinearGradient>
        </Pressable>
      </View>
    );
  }

  return (
    <View style={u.root}>
      <ScrollView
        style={u.scroll}
        contentContainerStyle={[u.scrollContent, { paddingBottom: bottomPad + 24 }]}
        showsVerticalScrollIndicator={false}
      >
        <View style={u.topBar}>
          <Text style={[u.modeLabel, { color: textLo }]}>You are in basic mode</Text>
        </View>

        {loading && !hasResults ? (
          <View style={u.centerState}>
            <ActivityIndicator size="large" color="#f472b6" />
            <Text style={[u.stateTxt, { color: textHi }]}>Reading all checks…</Text>
          </View>
        ) : null}

        {fetchErr && !hasResults && !loading ? (
          <View style={u.centerState}>
            <Text style={[u.stateTxt, { color: textHi }]}>{fetchErr}</Text>
            <Pressable onPress={() => { void fetchAllTools(); }}>
              <Text style={{ color: "#f472b6", fontFamily: "Nunito_700Bold", marginTop: 8 }}>Retry</Text>
            </Pressable>
          </View>
        ) : null}

        {primaryProfile && partnerProfile
          ? LOVE_REALITY_TOOLS.map((tool, index) => {
              const display = results[tool.key];
              if (!display) return null;
              const loyaltyCompare = resolveLoyaltyForTool(tool.key, rawResults, display);
              const border = isDark ? "rgba(255,255,255,0.08)" : "rgba(15,23,42,0.08)";
              return (
                <View key={tool.key} style={u.section}>
                  <ToolSectionHeader tool={tool} isDark={isDark} />
                  <LoveRealityToolSectionContent
                    toolKey={tool.key}
                    userName={primaryProfile.name || pickLoveBasicCopy(contentLang, "You", "Aap", "आप")}
                    partnerName={partnerProfile.name || pickLoveBasicCopy(contentLang, "Partner", "Partner", "साथी")}
                    display={display}
                    loyaltyCompare={loyaltyCompare}
                    isDark={isDark}
                    accentGradient={tool.gradient}
                    lang={contentLang}
                  />
                  {index < LOVE_REALITY_TOOLS.length - 1 ? (
                    <View style={[u.sectionDivider, { backgroundColor: border }]} />
                  ) : null}
                </View>
              );
            })
          : null}

        {hasResults ? (
          <Text style={[u.lockedHint, { color: isDark ? "rgba(203,213,225,0.42)" : "rgba(100,116,139,0.55)" }]}>
            {proScreenCopy.basicLockedHint}
          </Text>
        ) : null}

        {hasResults ? (
          <Pressable
            onPress={() => {
              Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
              onOpenPro();
            }}
            style={({ pressed }) => ({ opacity: pressed ? 0.9 : 1, marginTop: 4 })}
          >
            <LinearGradient colors={["#ec4899", "#a855f7"]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }} style={u.proTease}>
              <Feather name="file-text" size={16} color="#fff" />
              <Text style={u.proTeaseTxt}>{LOVE_REALITY_PRO_CTA_LABEL}</Text>
              <Feather name="chevron-right" size={16} color="#fff" />
            </LinearGradient>
          </Pressable>
        ) : null}
      </ScrollView>
    </View>
  );
}

const u = StyleSheet.create({
  root: { flex: 1, minHeight: 0 },
  scroll: { flex: 1 },
  scrollContent: { paddingHorizontal: 16, paddingTop: 4, gap: 4 },
  topBar: { marginBottom: 8, alignItems: "center" },
  modeLabel: {
    fontSize: 12,
    fontFamily: "Nunito_700Bold",
    letterSpacing: 0.6,
    textTransform: "uppercase",
    textAlign: "center",
  },
  centerState: { alignItems: "center", justifyContent: "center", gap: 10, paddingVertical: 48, paddingHorizontal: 16 },
  stateTxt: { fontSize: 14, fontFamily: "Nunito_600SemiBold", textAlign: "center" },
  section: { gap: 8, paddingVertical: 8 },
  sectionHead: { flexDirection: "row", alignItems: "center", gap: 10, paddingHorizontal: 4 },
  sectionBadge: {
    width: 36,
    height: 36,
    borderRadius: 12,
    alignItems: "center",
    justifyContent: "center",
  },
  sectionEmoji: { fontSize: 18 },
  sectionTitle: { fontSize: 16, fontFamily: "Nunito_800ExtraBold" },
  sectionDivider: { height: 1, marginTop: 12, marginHorizontal: 8 },
  lockedHint: {
    fontSize: 11.5,
    fontFamily: "Nunito_500Medium",
    lineHeight: 17,
    textAlign: "center",
    marginTop: 12,
    paddingHorizontal: 12,
  },
  proTease: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
    paddingVertical: 14,
    paddingHorizontal: 14,
    borderRadius: 14,
  },
  proTeaseTxt: {
    flex: 1,
    flexShrink: 1,
    color: "#fff",
    fontSize: 12.5,
    fontFamily: "Nunito_700Bold",
    textAlign: "center",
    lineHeight: 17,
  },
  gate: { flex: 1, alignItems: "center", justifyContent: "center", padding: 24, gap: 8 },
  gateTitle: { fontSize: 16, fontFamily: "Nunito_700Bold" },
  gateSub: { fontSize: 13, textAlign: "center", fontFamily: "Nunito_500Medium" },
  gateBtn: { paddingVertical: 14, borderRadius: 14, alignItems: "center", paddingHorizontal: 24 },
  gateBtnTxt: { color: "#fff", fontFamily: "Nunito_700Bold" },
});
