import { Feather } from "@expo/vector-icons";
import { router, useLocalSearchParams } from "expo-router";
import React, { useCallback, useEffect, useRef, useState } from "react";
import {
  ActivityIndicator,
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
import { coerceProPdfLang } from "@/lib/proPdfLang";

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

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [report, setReport] = useState<LoveProReportResponse | null>(null);
  const loadedRef = useRef(false);

  const load = useCallback(async () => {
    if (!user?.id || !primaryProfile?.birthData || !partnerProfile?.birthData) {
      setError("Complete both kundlis and sign in to read the report.");
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    const ctrl = new AbortController();
    const timer = setTimeout(() => ctrl.abort(), 240000);
    try {
      const data = await fetchLoveRealityProReport({
        user,
        p1: primaryProfile.birthData,
        p2: partnerProfile.birthData,
        p1Name: primaryProfile.name || "You",
        p2Name: partnerProfile.name || "Partner",
        lang,
        signal: ctrl.signal,
      });
      setReport(data);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Could not load report";
      setError(/abort/i.test(msg) ? "Report timed out — tap Retry." : msg);
    } finally {
      clearTimeout(timer);
      setLoading(false);
    }
  }, [user, primaryProfile, partnerProfile, lang]);

  useEffect(() => {
    if (loadedRef.current) return;
    loadedRef.current = true;
    load();
  }, [load]);

  const sections = report ? buildLoveReportSections(report, lang) : [];

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
          <View style={{ width: 24 }} />
        </View>

        {loading ? (
          <View style={s.center}>
            <ActivityIndicator size="large" color="#ec4899" />
            <Text style={[s.loadTxt, { color: C.textDim }]}>
              Preparing your full report…
            </Text>
            <Text style={[s.loadHint, { color: C.textDim }]}>
              This may take 1–2 minutes the first time.
            </Text>
          </View>
        ) : error ? (
          <View style={s.center}>
            <Feather name="alert-circle" size={32} color="#f472b6" />
            <Text style={[s.errTxt, { color: C.text }]}>{error}</Text>
            <Pressable onPress={() => { loadedRef.current = false; load(); }} style={s.retryBtn}>
              <Text style={s.retryTxt}>Retry</Text>
            </Pressable>
          </View>
        ) : report ? (
          <ScrollView
            contentContainerStyle={{ paddingHorizontal: 16, paddingBottom: insets.bottom + 28 }}
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
        ) : null}
      </View>
    </CosmicBg>
  );
}

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
  center: { flex: 1, alignItems: "center", justifyContent: "center", padding: 24, gap: 12 },
  loadTxt: { fontFamily: "Nunito_600SemiBold", fontSize: 15, textAlign: "center" },
  loadHint: { fontFamily: "Nunito_400Regular", fontSize: 12, textAlign: "center" },
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
