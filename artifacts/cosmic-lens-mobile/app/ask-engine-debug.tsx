import { Feather } from "@expo/vector-icons";
import * as Clipboard from "expo-clipboard";
import { Stack, router, useLocalSearchParams } from "expo-router";
import React, { useCallback, useEffect, useMemo, useState } from "react";
import {
  ActivityIndicator,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { useTheme } from "@/context/ThemeContext";
import { useUser } from "@/context/UserContext";
import { API_BASE, apiFetch } from "@/lib/apiConfig";

type PipelineStep = { label?: string; value?: string };

type Observability = {
  routing_warning?: string | null;
  question_dna_pipeline?: PipelineStep[];
  engine_health?: Record<string, unknown>;
  engine_execution?: {
    engine_name?: string;
    final_score?: unknown;
    verdict?: string;
    verdict_level?: string;
    modules?: { module?: string; loaded?: boolean }[];
    fired?: { rule_id?: string; note?: string; polarity?: string }[];
    ignored?: { rule_id?: string; reason?: string }[];
  };
  rule_decisions?: { rule_id?: string; status?: string; weight?: number; reason?: string }[];
  planet_evidence?: {
    positive?: { label?: string }[];
    negative?: { label?: string }[];
  };
  conflict_resolution?: { conflict?: string; reason?: string; final_result?: string };
  scorecard?: Record<string, number>;
  narrator_input?: unknown;
  narrator_output?: string | null;
  hallucination_summary?: Record<string, { ok?: boolean; detail?: string; items?: string[] }>;
  final_trace?: { label?: string; value?: string }[];
};

type DebugRow = {
  id?: string;
  question_text?: string;
  answer_text?: string;
  topic?: string;
  answer_source?: string;
  engine_tag?: string;
  verdict_summary?: string;
  created_at?: string;
  debug_export_text?: string;
  observability?: Observability;
  llm_context?: { observability?: Observability };
};

function DebugSection({
  title,
  children,
  defaultOpen = true,
}: {
  title: string;
  children: React.ReactNode;
  defaultOpen?: boolean;
}) {
  const { colors: C } = useTheme();
  const [open, setOpen] = useState(defaultOpen);
  return (
    <View style={[styles.section, { borderColor: C.border, backgroundColor: C.bgCard }]}>
      <Pressable onPress={() => setOpen((v) => !v)} style={styles.sectionHead}>
        <Text style={[styles.sectionTitle, { color: C.text }]}>{title}</Text>
        <Feather name={open ? "chevron-up" : "chevron-down"} size={16} color={C.textMuted} />
      </Pressable>
      {open ? <View style={styles.sectionBody}>{children}</View> : null}
    </View>
  );
}

function PipelineBlock({ steps }: { steps?: PipelineStep[] }) {
  const { colors: C } = useTheme();
  if (!steps?.length) {
    return <Text style={[styles.muted, { color: C.textMuted }]}>—</Text>;
  }
  return (
    <View style={styles.gap8}>
      {steps.map((step, i) => (
        <View key={`${step.label}-${i}`}>
          <Text style={[styles.pipeLabel, { color: C.accent }]}>{step.label}</Text>
          <Text style={[styles.mono, { color: C.text }]}>{step.value || "—"}</Text>
        </View>
      ))}
    </View>
  );
}

export default function AskEngineDebugScreen() {
  const { colors: C } = useTheme();
  const { user } = useUser();
  const insets = useSafeAreaInsets();
  const params = useLocalSearchParams<{ questionId?: string }>();
  const questionId = String(params.questionId || "").trim();

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [row, setRow] = useState<DebugRow | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      if (!questionId || !user?.id || !user?.api_key) {
        setError("Debug data unavailable — login and ask again.");
        setLoading(false);
        return;
      }
      setLoading(true);
      setError(null);
      try {
        const res = await apiFetch(`${API_BASE}/api/history/${encodeURIComponent(questionId)}/debug`, {
          headers: {
            "X-User-Id": String(user.id),
            "X-API-Key": user.api_key,
          },
        });
        if (!res.ok) {
          throw new Error(res.status === 404 ? "Debug not found yet — try again in a moment." : `HTTP ${res.status}`);
        }
        const json = (await res.json()) as DebugRow;
        if (!cancelled) setRow(json);
      } catch (e: any) {
        if (!cancelled) setError(String(e?.message || "Failed to load debugger"));
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, [questionId, user?.api_key, user?.id]);

  const obs = useMemo(
    () => row?.observability || row?.llm_context?.observability || null,
    [row],
  );

  const copyAll = useCallback(async () => {
    const text = row?.debug_export_text || "";
    if (!text.trim()) return;
    await Clipboard.setStringAsync(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  }, [row?.debug_export_text]);

  return (
    <View style={[styles.root, { backgroundColor: C.bg, paddingTop: insets.top }]}>
      <Stack.Screen options={{ title: "Developer debugger", headerShown: false }} />

      <View style={[styles.topBar, { borderBottomColor: C.border }]}>
        <Pressable onPress={() => router.back()} style={styles.backBtn} hitSlop={8}>
          <Feather name="arrow-left" size={18} color={C.text} />
        </Pressable>
        <Text style={[styles.topTitle, { color: C.text, flex: 1 }]}>Developer debugger</Text>
        <Pressable onPress={copyAll} style={[styles.copyBtn, { borderColor: `${C.accent}55` }]}>
          <Feather name="copy" size={14} color={C.accent} />
          <Text style={{ color: C.accent, fontSize: 12, fontWeight: "700" }}>
            {copied ? "Copied!" : "Copy All"}
          </Text>
        </Pressable>
      </View>

      {loading ? (
        <View style={styles.center}>
          <ActivityIndicator color={C.accent} />
          <Text style={[styles.muted, { color: C.textMuted, marginTop: 10 }]}>Loading engine trace…</Text>
        </View>
      ) : error ? (
        <View style={styles.center}>
          <Text style={[styles.error, { color: "#f87171" }]}>{error}</Text>
        </View>
      ) : (
        <ScrollView contentContainerStyle={[styles.scroll, { paddingBottom: insets.bottom + 24 }]}>
          <Text style={[styles.question, { color: C.text }]}>{row?.question_text || "—"}</Text>
          <Text style={[styles.meta, { color: C.textMuted }]}>
            {row?.topic || "—"} · {row?.answer_source || "—"} · {row?.engine_tag || "—"}
          </Text>

          <DebugSection title="Final answer (user saw)">
            <Text style={[styles.body, { color: C.text }]}>{row?.answer_text || "—"}</Text>
          </DebugSection>

          {obs?.routing_warning ? (
            <View style={[styles.warnBox, { borderColor: "#f59e0b55", backgroundColor: "#f59e0b18" }]}>
              <Text style={[styles.warnText, { color: "#fbbf24" }]}>{obs.routing_warning}</Text>
            </View>
          ) : null}

          <DebugSection title="1. Question DNA">
            <PipelineBlock steps={obs?.question_dna_pipeline} />
          </DebugSection>

          <DebugSection title="2. Engine Health">
            <Text style={[styles.mono, { color: C.text }]}>
              Modules: {String(obs?.engine_health?.modules_loaded ?? "—")}{"\n"}
              Rules fired: {String(obs?.engine_health?.rules_fired ?? "—")}{"\n"}
              Confidence: {String(obs?.engine_health?.confidence_pct ?? "—")}%
            </Text>
          </DebugSection>

          <DebugSection title="3. Engine Execution">
            <Text style={[styles.mono, { color: C.text }]}>
              Engine: {obs?.engine_execution?.engine_name || "—"}{"\n"}
              Score: {String(obs?.engine_execution?.final_score ?? "—")}{"\n"}
              Verdict: {obs?.engine_execution?.verdict || obs?.engine_execution?.verdict_level || "—"}
            </Text>
            <Text style={[styles.pipeLabel, { color: C.accent, marginTop: 10 }]}>Modules</Text>
            {(obs?.engine_execution?.modules || []).map((m, i) => (
              <Text key={`mod-${i}`} style={[styles.mono, { color: C.text }]}>
                {(m.loaded ? "✅" : "❌")} {m.module}
              </Text>
            ))}
            <Text style={[styles.pipeLabel, { color: C.accent, marginTop: 10 }]}>Rules fired</Text>
            {(obs?.engine_execution?.fired || []).length === 0 ? (
              <Text style={[styles.muted, { color: C.textMuted }]}>—</Text>
            ) : (
              (obs?.engine_execution?.fired || []).map((r, i) => (
                <Text key={`rule-${i}`} style={[styles.mono, { color: C.text }]}>
                  {r.rule_id} {r.polarity === "negative" ? "❌" : "✅"} {r.note || ""}
                </Text>
              ))
            )}
          </DebugSection>

          <DebugSection title="4. Rule Decision Table" defaultOpen={false}>
            {(obs?.rule_decisions || []).length === 0 ? (
              <Text style={[styles.muted, { color: C.textMuted }]}>—</Text>
            ) : (
              (obs?.rule_decisions || []).map((d, i) => (
                <Text key={`dec-${i}`} style={[styles.mono, { color: C.text }]}>
                  {d.rule_id} | {d.status} | {d.weight ?? 0} | {d.reason || "—"}
                </Text>
              ))
            )}
          </DebugSection>

          <DebugSection title="5. Planet Evidence" defaultOpen={false}>
            <Text style={[styles.pipeLabel, { color: C.accent }]}>Positive</Text>
            {(obs?.planet_evidence?.positive || []).map((e, i) => (
              <Text key={`pos-${i}`} style={[styles.mono, { color: C.text }]}>• {e.label}</Text>
            ))}
            <Text style={[styles.pipeLabel, { color: C.accent, marginTop: 8 }]}>Negative</Text>
            {(obs?.planet_evidence?.negative || []).map((e, i) => (
              <Text key={`neg-${i}`} style={[styles.mono, { color: C.text }]}>• {e.label}</Text>
            ))}
          </DebugSection>

          <DebugSection title="6–11. Full export" defaultOpen={false}>
            <Text style={[styles.mono, { color: C.text }]} selectable>
              {row?.debug_export_text || "—"}
            </Text>
          </DebugSection>
        </ScrollView>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1 },
  topBar: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: StyleSheet.hairlineWidth,
    gap: 10,
  },
  backBtn: { padding: 4 },
  topTitle: { fontSize: 18, fontWeight: "800" },
  copyBtn: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    borderWidth: 1,
    borderRadius: 999,
    paddingHorizontal: 12,
    paddingVertical: 6,
  },
  center: { flex: 1, alignItems: "center", justifyContent: "center", padding: 24 },
  scroll: { padding: 16, gap: 12 },
  question: { fontSize: 16, fontWeight: "700", lineHeight: 22 },
  meta: { fontSize: 12, marginBottom: 4 },
  body: { fontSize: 14, lineHeight: 21 },
  muted: { fontSize: 13 },
  mono: { fontSize: 12, lineHeight: 18, fontFamily: "monospace" },
  pipeLabel: { fontSize: 12, fontWeight: "700", marginBottom: 4 },
  gap8: { gap: 8 },
  section: { borderWidth: 1, borderRadius: 12, overflow: "hidden" },
  sectionHead: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: 14,
    paddingVertical: 12,
  },
  sectionTitle: { fontSize: 14, fontWeight: "800" },
  sectionBody: { paddingHorizontal: 14, paddingBottom: 14 },
  warnBox: { borderWidth: 1, borderRadius: 10, padding: 12 },
  warnText: { fontSize: 12, lineHeight: 18 },
  error: { fontSize: 14, textAlign: "center" },
});
