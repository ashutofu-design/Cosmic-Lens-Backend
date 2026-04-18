/**
 * AstroVastu PRO — Result page
 *
 * Receives the freshly generated report from `proResultCache` and renders:
 *   • Big circular score gauge (SVG)
 *   • Top-3 priority actions card with R/A/G colour coding
 *   • Per-room horizontal scroll cards
 *   • Open PDF button (in-app browser)
 *   • Share-on-WhatsApp button
 *
 * Branding: surfaces "Cosmic Vision" / "Cosmic Intelligence" — never AI/LLM/GPT.
 */
import { Feather } from "@expo/vector-icons";
import * as Haptics from "expo-haptics";
import * as Linking from "expo-linking";
import { LinearGradient } from "expo-linear-gradient";
import { router, Stack } from "expo-router";
import * as WebBrowser from "expo-web-browser";
import React, { useMemo, useState } from "react";
import {
  Alert,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import Svg, { Circle, Defs, LinearGradient as SvgGradient, Stop } from "react-native-svg";

import { useC } from "@/context/ThemeContext";
import { API_BASE } from "@/lib/apiConfig";
import { openReportPdfWithLanguageChoice } from "@/lib/pdfLanguagePicker";
import { proResultCache } from "@/lib/proResultCache";
import { ScanBasisBadge, VisionRoomFindings } from "@/components/ScanBasisBadge";

// ─────────────────────────────────────────────────────────────────────────
const VERDICT_COLOR: Record<string, { bg: string; fg: string; border: string; rag: "R"|"A"|"G" }> = {
  Ideal:                { bg: "rgba(16,185,129,0.18)", fg: "#10B981", border: "rgba(16,185,129,0.45)", rag: "G" },
  Acceptable:           { bg: "rgba(59,130,246,0.18)", fg: "#3B82F6", border: "rgba(59,130,246,0.45)", rag: "G" },
  "Adjustment Needed":  { bg: "rgba(245,158,11,0.18)", fg: "#F59E0B", border: "rgba(245,158,11,0.45)", rag: "A" },
  Avoid:                { bg: "rgba(239,68,68,0.18)",  fg: "#EF4444", border: "rgba(239,68,68,0.45)",  rag: "R" },
};
const RAG_COLOR = { R: "#EF4444", A: "#F59E0B", G: "#10B981" } as const;
const GRADE_COLOR: Record<string, string> = {
  A: "#10B981", B: "#3B82F6", C: "#F59E0B", D: "#EF4444", E: "#EF4444",
};

type Remedy = { action?: string; english?: string; hindi?: string; priority?: number; classical_ref?: string };
type RoomReport = {
  room_type: string; direction: string; verdict: string; score: number;
  zone?: { direction?: string; planet?: string; deity?: string; element?: string };
  mahadasha_layer?: { applies?: boolean; reason_en?: string };
  remedies?: Remedy[];
  direction_basis?: string;
};
type PriorityAction = {
  room_type: string; direction: string; verdict: string;
  why: string; remedies: Remedy[];
};
type ProResponse = {
  overall: {
    score: number; grade: string;
    summary?: { en?: string; hi?: string };
    counts?: { ideal?: number; acceptable?: number; adjustment_needed?: number; avoid?: number };
  };
  rooms?: RoomReport[];
  priority_actions?: PriorityAction[];
  pdf_url?:   string;
  pdf_token?: string;
  footer?:    string;
  vision_room_findings?: VisionRoomFindings;
};

// ─────────────────────────────────────────────────────────────────────────
function ScoreGauge({ score, grade }: { score: number; grade: string }) {
  const C = useC();
  const size      = 180;
  const stroke    = 14;
  const r         = (size - stroke) / 2;
  const circ      = 2 * Math.PI * r;
  const pct       = Math.max(0, Math.min(100, score)) / 100;
  const dashOff   = circ * (1 - pct);
  const colour    = GRADE_COLOR[grade] || C.accent;

  return (
    <View style={{ alignItems: "center", justifyContent: "center" }}>
      <Svg width={size} height={size}>
        <Defs>
          <SvgGradient id="grad" x1="0" y1="0" x2="1" y2="1">
            <Stop offset="0%"  stopColor={colour} stopOpacity={1}   />
            <Stop offset="100%" stopColor={colour} stopOpacity={0.7} />
          </SvgGradient>
        </Defs>
        <Circle
          cx={size/2} cy={size/2} r={r}
          stroke={C.border} strokeWidth={stroke} fill="none"
        />
        <Circle
          cx={size/2} cy={size/2} r={r}
          stroke="url(#grad)" strokeWidth={stroke} fill="none"
          strokeLinecap="round"
          strokeDasharray={`${circ} ${circ}`}
          strokeDashoffset={dashOff}
          rotation={-90}
          origin={`${size/2}, ${size/2}`}
        />
      </Svg>
      <View style={{ position: "absolute", alignItems: "center" }}>
        <Text style={{ color: colour, fontSize: 44, fontWeight: "900", lineHeight: 50 }}>
          {Math.round(score)}
        </Text>
        <Text style={{ color: C.textMid, fontSize: 12, fontWeight: "700" }}>OUT OF 100</Text>
        <View style={{
          marginTop: 6, paddingHorizontal: 12, paddingVertical: 4, borderRadius: 10,
          backgroundColor: colour,
        }}>
          <Text style={{ color: "#fff", fontSize: 13, fontWeight: "800" }}>
            Grade {grade}
          </Text>
        </View>
      </View>
    </View>
  );
}

// ─────────────────────────────────────────────────────────────────────────
export default function AstroVastuProResultScreen() {
  const C = useC();
  const insets = useSafeAreaInsets();
  const [result] = useState<ProResponse | null>(() => proResultCache.get());

  const overall  = result?.overall  || { score: 0, grade: "C" };
  const rooms    = useMemo(() => Array.isArray(result?.rooms) ? result!.rooms! : [], [result]);
  const priors   = useMemo(() => Array.isArray(result?.priority_actions) ? result!.priority_actions!.slice(0, 3) : [], [result]);
  const summary  = overall.summary || {};
  const pdfFull  = result?.pdf_url && result?.pdf_token
    ? `${API_BASE}${result.pdf_url}?t=${encodeURIComponent(result.pdf_token)}`
    : null;

  const openPdf = () => {
    if (!pdfFull) return;
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    openReportPdfWithLanguageChoice(pdfFull);
  };

  const shareWhatsApp = async () => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    const lines = [
      `🪔 *AstroVastu PRO Report*`,
      `📊 Score: ${Math.round(overall.score)}/100  ·  Grade ${overall.grade}`,
    ];
    if (summary.en) lines.push("", summary.en);
    if (pdfFull)    lines.push("", `📄 Open report:`, pdfFull);
    lines.push("", `_Powered by Advanced Cosmic Intelligence_`);
    const msg = lines.join("\n");

    const wa = `whatsapp://send?text=${encodeURIComponent(msg)}`;
    try {
      const can = await Linking.canOpenURL(wa);
      if (can) { await Linking.openURL(wa); return; }
      await Linking.openURL(`https://wa.me/?text=${encodeURIComponent(msg)}`);
    } catch (e: any) {
      Alert.alert("Couldn't share", String(e?.message || e));
    }
  };

  // ─── Empty state when user lands here without a cached result ───────
  if (!result) {
    return (
      <View style={{ flex: 1, backgroundColor: C.bg, paddingTop: insets.top, padding: 20 }}>
        <Stack.Screen options={{ headerShown: false }} />
        <View style={[s.emptyCard, { backgroundColor: C.bgCard, borderColor: C.border }]}>
          <Feather name="alert-circle" size={28} color={C.textMid} />
          <Text style={{ color: C.text, fontSize: 16, fontWeight: "700", marginTop: 8 }}>
            No report loaded
          </Text>
          <Text style={{ color: C.textMid, fontSize: 13, marginTop: 6, textAlign: "center" }}>
            Please run a Smart Scan first to view the result here.
          </Text>
          <Pressable
            onPress={() => router.replace("/astrovastu-pro")}
            style={[s.cta, { backgroundColor: C.accent, marginTop: 18 }]}
          >
            <Text style={s.ctaText}>Open AstroVastu PRO</Text>
          </Pressable>
        </View>
      </View>
    );
  }

  return (
    <View style={{ flex: 1, backgroundColor: C.bg, paddingTop: insets.top }}>
      <Stack.Screen options={{ headerShown: false }} />
      <LinearGradient
        colors={[C.bg, C.bgCard]}
        style={s.header}
      >
        <Pressable onPress={() => router.back()} hitSlop={10} style={{ padding: 6 }}>
          <Feather name="arrow-left" size={22} color={C.text} />
        </Pressable>
        <Text style={[s.headerTitle, { color: C.text }]}>Your AstroVastu Report</Text>
        <View style={{ width: 28 }} />
      </LinearGradient>

      <ScrollView contentContainerStyle={{ padding: 16, paddingBottom: insets.bottom + 40 }}>
        {/* ── Score gauge ──────────────────────────────────────── */}
        <View style={[s.scoreCard, { backgroundColor: C.bgCard, borderColor: C.border }]}>
          <ScoreGauge score={overall.score || 0} grade={overall.grade || "C"} />
          {summary.en ? (
            <Text style={{ color: C.text, fontSize: 13, lineHeight: 19, marginTop: 12, textAlign: "center" }}>
              {summary.en}
            </Text>
          ) : null}
          {summary.hi ? (
            <Text style={{ color: C.textMid, fontSize: 12, lineHeight: 18, marginTop: 4, textAlign: "center" }}>
              {summary.hi}
            </Text>
          ) : null}
          <ScanBasisBadge
            visionRoomFindings={result.vision_room_findings}
            perRoomBasis={rooms.map((r) => ({
              room_type: r.room_type, direction_basis: r.direction_basis,
            }))}
          />
        </View>

        {/* ── Action buttons row ───────────────────────────────── */}
        <View style={s.actionsRow}>
          {pdfFull && (
            <Pressable onPress={openPdf} style={[s.actionBtn, { backgroundColor: C.accent }]}>
              <Feather name="file-text" size={16} color="#fff" />
              <Text style={s.actionText}>Open PDF</Text>
            </Pressable>
          )}
          <Pressable onPress={shareWhatsApp} style={[s.actionBtn, { backgroundColor: "#25D366" }]}>
            <Feather name="share-2" size={16} color="#fff" />
            <Text style={s.actionText}>WhatsApp</Text>
          </Pressable>
        </View>

        {/* ── Top-3 priority actions ───────────────────────────── */}
        {priors.length > 0 && (
          <View style={[s.card, { backgroundColor: C.bgCard, borderColor: C.border, marginTop: 16 }]}>
            <Text style={[s.sectionLabel, { color: C.textMid, marginBottom: 10 }]}>
              SABSE PEHLE YE 3 CHEEZEIN THEEK KARO
            </Text>
            {priors.map((p, i) => {
              const meta = VERDICT_COLOR[p.verdict] || VERDICT_COLOR.Acceptable;
              const rag  = RAG_COLOR[meta.rag];
              return (
                <View
                  key={`${p.room_type}-${p.direction}-${i}`}
                  style={[s.priRow, { borderLeftColor: rag, backgroundColor: meta.bg }]}
                >
                  <View style={[s.priBadge, { backgroundColor: rag }]}>
                    <Text style={{ color: "#fff", fontWeight: "900", fontSize: 14 }}>{i + 1}</Text>
                  </View>
                  <View style={{ flex: 1 }}>
                    <Text style={{ color: C.text, fontWeight: "800", fontSize: 14 }}>
                      {p.room_type} · {p.direction}
                    </Text>
                    <Text style={{ color: meta.fg, fontSize: 11, fontWeight: "700", marginTop: 2 }}>
                      {p.verdict.toUpperCase()}
                    </Text>
                    {p.why ? (
                      <Text style={{ color: C.textMid, fontSize: 12, marginTop: 4, lineHeight: 17 }}>
                        {p.why}
                      </Text>
                    ) : null}
                    {(p.remedies || []).slice(0, 2).map((rem, j) => (
                      <Text key={j} style={{ color: C.text, fontSize: 12, marginTop: 4 }}>
                        • {rem.english || rem.action}
                      </Text>
                    ))}
                  </View>
                </View>
              );
            })}
          </View>
        )}

        {/* ── Per-room horizontal scroll ───────────────────────── */}
        {rooms.length > 0 && (
          <View style={{ marginTop: 18 }}>
            <Text style={[s.sectionLabel, { color: C.textMid, marginBottom: 10, marginLeft: 2 }]}>
              ROOM-BY-ROOM
            </Text>
            <ScrollView
              horizontal
              showsHorizontalScrollIndicator={false}
              contentContainerStyle={{ paddingRight: 8, gap: 10 }}
            >
              {rooms.map((r, idx) => {
                const meta = VERDICT_COLOR[r.verdict] || VERDICT_COLOR.Acceptable;
                return (
                  <View
                    key={idx}
                    style={[s.roomCard, {
                      backgroundColor: C.bgCard, borderColor: meta.border,
                    }]}
                  >
                    <View style={[s.dot, { backgroundColor: meta.fg }]} />
                    <Text style={{ color: C.text, fontWeight: "800", fontSize: 14 }} numberOfLines={1}>
                      {r.room_type}
                    </Text>
                    <Text style={{ color: C.textMid, fontSize: 11, marginTop: 2 }}>
                      {r.direction}
                    </Text>
                    <Text style={{ color: meta.fg, fontSize: 22, fontWeight: "900", marginTop: 8 }}>
                      {Math.round(r.score)}
                    </Text>
                    <Text style={{ color: meta.fg, fontSize: 10, fontWeight: "800" }}>
                      {r.verdict.toUpperCase()}
                    </Text>
                    {r.zone?.planet ? (
                      <Text style={{ color: C.textMid, fontSize: 10, marginTop: 6 }} numberOfLines={2}>
                        {r.zone.planet} · {r.zone.deity || ""}
                      </Text>
                    ) : null}
                  </View>
                );
              })}
            </ScrollView>
          </View>
        )}

        {/* ── Branding footer ──────────────────────────────────── */}
        <Text style={[s.brand, { color: C.textMid }]}>
          ✨ Powered by Advanced Cosmic Intelligence
        </Text>
      </ScrollView>
    </View>
  );
}

// ─────────────────────────────────────────────────────────────────────────
const s = StyleSheet.create({
  header: {
    flexDirection: "row", alignItems: "center", justifyContent: "space-between",
    paddingHorizontal: 16, paddingTop: 4, paddingBottom: 10,
  },
  headerTitle: { fontSize: 17, fontWeight: "700" },

  scoreCard: {
    borderRadius: 18, borderWidth: 1, padding: 18, alignItems: "center",
  },
  sectionLabel: {
    fontSize: 11, fontWeight: "800", textTransform: "uppercase", letterSpacing: 0.6,
  },

  actionsRow: { flexDirection: "row", gap: 10, marginTop: 14 },
  actionBtn:  {
    flex: 1, height: 46, borderRadius: 12,
    flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 8,
    shadowOpacity: 0.18, shadowRadius: 6, elevation: 2,
  },
  actionText: { color: "#fff", fontSize: 14, fontWeight: "800" },

  card: { borderRadius: 14, borderWidth: 1, padding: 14 },

  priRow: {
    flexDirection: "row", gap: 12,
    borderLeftWidth: 4, borderRadius: 10,
    padding: 12, marginBottom: 10,
  },
  priBadge: {
    width: 30, height: 30, borderRadius: 15,
    alignItems: "center", justifyContent: "center",
  },

  roomCard: {
    width: 130, padding: 12, borderRadius: 14, borderWidth: 1,
  },
  dot: { width: 8, height: 8, borderRadius: 4, marginBottom: 8 },

  emptyCard: {
    borderRadius: 16, borderWidth: 1, padding: 22, alignItems: "center", marginTop: 80,
  },
  cta:     { paddingHorizontal: 18, paddingVertical: 12, borderRadius: 12 },
  ctaText: { color: "#fff", fontWeight: "800" },

  brand: { fontSize: 12, fontWeight: "600", textAlign: "center", marginTop: 28 },
});
