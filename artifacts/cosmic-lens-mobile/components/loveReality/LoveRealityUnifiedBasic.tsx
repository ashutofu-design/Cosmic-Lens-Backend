import { Feather } from "@expo/vector-icons";
import * as Haptics from "expo-haptics";
import { LinearGradient } from "expo-linear-gradient";
import { router } from "expo-router";
import React, { useEffect, useRef, useState } from "react";
import {
  ActivityIndicator,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";

import { LoveRealityToolResultPanel } from "@/components/loveReality/LoveRealityToolResultPanel";
import { API_BASE } from "@/lib/apiConfig";
import {
  mapLoveRealityResult,
  type LoveRealityBasicDisplay,
  type LoveRealityToolKey,
} from "@/lib/loveRealityToolMappers";
import { LOVE_REALITY_TOOLS, toolDefForKey, type LoveRealityToolDef } from "@/lib/loveRealityToolsConfig";
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

export function LoveRealityUnifiedBasic({
  isDark,
  bottomPad,
  primaryProfile,
  partnerProfile,
  initialToolKey,
  onOpenPro,
}: {
  isDark: boolean;
  bottomPad: number;
  primaryProfile: { name: string; birthData: BirthData } | null;
  partnerProfile: { name: string; birthData: BirthData } | null;
  initialToolKey?: string;
  onOpenPro: () => void;
}) {
  const canAnalyze = !!primaryProfile?.birthData && !!partnerProfile?.birthData;
  const [selected, setSelected] = useState<LoveRealityToolKey>(
    (toolDefForKey(initialToolKey ?? "love-compat").key),
  );
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<ResultsMap>({});
  const [fetchErr, setFetchErr] = useState<string | null>(null);
  const didFetch = useRef(false);

  const active = toolDefForKey(selected);
  const display = results[selected];
  const textHi = isDark ? "#fff" : "#0F172A";
  const textLo = isDark ? "rgba(203,213,225,0.65)" : "#64748B";

  useEffect(() => {
    if (!canAnalyze || didFetch.current) return;
    didFetch.current = true;
    void fetchAllTools();
  }, [canAnalyze]);

  async function fetchAllTools() {
    if (!primaryProfile?.birthData || !partnerProfile?.birthData) return;
    setLoading(true);
    setFetchErr(null);
    const body = JSON.stringify({
      p1: packPerson(primaryProfile.birthData),
      p2: packPerson(partnerProfile.birthData),
    });

    try {
      const pairs = await Promise.all(
        LOVE_REALITY_TOOLS.map(async tool => {
          const ctrl = new AbortController();
          const timer = setTimeout(() => ctrl.abort(), 35000);
          try {
            const resp = await fetch(`${API_BASE}${tool.apiPath}`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body,
              signal: ctrl.signal,
            });
            clearTimeout(timer);
            const json = await resp.json();
            if (!resp.ok || json.error) throw new Error(json.error || tool.title);
            return [tool.key, mapLoveRealityResult(tool.key, json as Record<string, unknown>)] as const;
          } catch (e) {
            clearTimeout(timer);
            throw e;
          }
        }),
      );
      setResults(Object.fromEntries(pairs) as ResultsMap);
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
    } catch (e: unknown) {
      setFetchErr(e instanceof Error ? e.message : "Could not load readings");
    } finally {
      setLoading(false);
    }
  }

  function selectTool(tool: LoveRealityToolDef) {
    Haptics.selectionAsync();
    setSelected(tool.key);
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
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={u.chipRow}
        style={u.chipScroll}
      >
        {LOVE_REALITY_TOOLS.map(tool => {
          const on = tool.key === selected;
          const [c1, c2] = tool.gradient;
          return (
            <Pressable key={tool.key} onPress={() => selectTool(tool)} style={({ pressed }) => ({ opacity: pressed ? 0.85 : 1 })}>
              {on ? (
                <LinearGradient colors={[c1, c2]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }} style={u.chipOn}>
                  <Text style={u.chipEmoji}>{tool.emoji}</Text>
                  <Text style={u.chipLblOn}>{tool.shortLabel}</Text>
                </LinearGradient>
              ) : (
                <View style={[u.chipOff, { borderColor: isDark ? `${tool.iconColor}35` : `${tool.iconColor}25` }]}>
                  <Text style={u.chipEmoji}>{tool.emoji}</Text>
                  <Text style={[u.chipLblOff, { color: isDark ? "rgba(203,213,225,0.7)" : "#64748B" }]}>{tool.shortLabel}</Text>
                </View>
              )}
            </Pressable>
          );
        })}
      </ScrollView>

      <View style={u.resultZone}>
        {loading && !display && (
          <View style={u.centerState}>
            <ActivityIndicator size="large" color={active.gradient[0]} />
            <Text style={[u.stateTxt, { color: textHi }]}>Reading all 5 tools…</Text>
          </View>
        )}

        {fetchErr && !display && !loading && (
          <View style={u.centerState}>
            <Text style={[u.stateTxt, { color: textHi }]}>{fetchErr}</Text>
            <Pressable onPress={() => { didFetch.current = false; void fetchAllTools(); }}>
              <Text style={{ color: active.gradient[0], fontFamily: "Nunito_700Bold", marginTop: 8 }}>Retry</Text>
            </Pressable>
          </View>
        )}

        {display && primaryProfile && partnerProfile && (
          <LoveRealityToolResultPanel
            toolTitle={active.title}
            userName={primaryProfile.name || "You"}
            partnerName={partnerProfile.name || "Partner"}
            display={display}
            isDark={isDark}
            bottomPad={bottomPad}
            accentGradient={active.gradient}
            onOpenPro={onOpenPro}
          />
        )}
      </View>
    </View>
  );
}

const u = StyleSheet.create({
  root: { flex: 1, minHeight: 0 },
  chipScroll: { flexGrow: 0, maxHeight: 52, marginBottom: 6 },
  chipRow: { paddingHorizontal: 16, gap: 8, alignItems: "center" },
  chipOn: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    paddingHorizontal: 14,
    paddingVertical: 10,
    borderRadius: 14,
  },
  chipOff: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    paddingHorizontal: 14,
    paddingVertical: 10,
    borderRadius: 14,
    borderWidth: 1,
    backgroundColor: "rgba(14,22,42,0.45)",
  },
  chipEmoji: { fontSize: 16 },
  chipLblOn: { color: "#fff", fontSize: 12, fontFamily: "Nunito_800ExtraBold" },
  chipLblOff: { fontSize: 12, fontFamily: "Nunito_700Bold" },
  resultZone: { flex: 1, minHeight: 0 },
  centerState: { flex: 1, alignItems: "center", justifyContent: "center", gap: 10, paddingHorizontal: 16 },
  stateTxt: { fontSize: 14, fontFamily: "Nunito_600SemiBold", textAlign: "center" },
  gate: { flex: 1, alignItems: "center", justifyContent: "center", padding: 24, gap: 8 },
  gateTitle: { fontSize: 16, fontFamily: "Nunito_700Bold" },
  gateSub: { fontSize: 13, textAlign: "center", fontFamily: "Nunito_500Medium" },
  gateBtn: { paddingVertical: 14, borderRadius: 14, alignItems: "center", paddingHorizontal: 24 },
  gateBtnTxt: { color: "#fff", fontFamily: "Nunito_700Bold" },
});
