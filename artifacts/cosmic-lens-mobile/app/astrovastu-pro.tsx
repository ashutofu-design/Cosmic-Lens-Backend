/**
 * AstroVastu PRO — Single-tap Smart Scan
 *
 * Minimal flow:
 *   1. User taps "Smart Scan — Open Camera".
 *   2. Live camera with compass overlay opens.
 *   3. Shutter captures a photo + magnetometer heading.
 *   4. We POST the photo as floor_plan_upload; Cosmic Vision detects rooms
 *      and runs the kundli-aware deep scan.
 *   5. Result + PDF link rendered on the same screen.
 *
 * No AI/LLM branding — surfaces "Cosmic Vision" only.
 */
import { Feather } from "@expo/vector-icons";
import * as Haptics from "expo-haptics";
import * as Linking from "expo-linking";
import * as WebBrowser from "expo-web-browser";
import { LinearGradient } from "expo-linear-gradient";
import { router, Stack } from "expo-router";
import React, { useCallback, useState } from "react";
import {
  Alert,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { useC } from "@/context/ThemeContext";
import { useUser } from "@/context/UserContext";
import { API_BASE } from "@/lib/apiConfig";
import { GalleryScanResult, GalleryScanUpload } from "@/components/GalleryScanUpload";
import { RoomPhoto, RoomPhotoCapture, RoomChoice } from "@/components/RoomPhotoCapture";
import { ScanBasisBadge, VisionRoomFindings } from "@/components/ScanBasisBadge";
import { SmartScanCamera, SmartScanResult } from "@/components/SmartScanCamera";
import type { NorthAt } from "@/components/SmartScanUpload";

// Default room list for PRO (full-house residential) — used by RoomPhotoCapture
// since the PRO flow doesn't ask the user to list rooms upfront (vision detects).
const PRO_DEFAULT_ROOMS: RoomChoice[] = [
  { key: "bedroom",   label: "Bedroom"      },
  { key: "kitchen",   label: "Kitchen"      },
  { key: "pooja",     label: "Pooja Room"   },
  { key: "living",    label: "Living Room"  },
  { key: "bathroom",  label: "Bathroom"     },
  { key: "entrance",  label: "Entrance"     },
];

// ─────────────────────────────────────────────────────────────────────────
const VERDICT_COLOR: Record<string, { bg: string; fg: string; border: string }> = {
  Ideal:                { bg: "rgba(16,185,129,0.18)", fg: "#10B981", border: "rgba(16,185,129,0.45)" },
  Acceptable:           { bg: "rgba(59,130,246,0.18)", fg: "#3B82F6", border: "rgba(59,130,246,0.45)" },
  "Adjustment Needed":  { bg: "rgba(245,158,11,0.18)", fg: "#F59E0B", border: "rgba(245,158,11,0.45)" },
  Avoid:                { bg: "rgba(239,68,68,0.18)",  fg: "#EF4444", border: "rgba(239,68,68,0.45)"  },
};
const GRADE_COLOR: Record<string, string> = {
  A: "#10B981", B: "#3B82F6", C: "#F59E0B", D: "#EF4444",
};

type Remedy = { action: string; english: string; hindi: string; priority: number; classical_ref: string };
type RoomReport = {
  room_type: string; direction: string; verdict: string; score: number;
  zone: { direction: string; planet?: string; deity?: string; element?: string };
  mahadasha_layer: { applies: boolean; reason_en?: string };
  remedies: Remedy[];
  direction_basis?: string;
};
type PriorityAction = {
  room_type: string; direction: string; verdict: string;
  why: string; remedies: Remedy[];
};
type ProResponse = {
  overall: {
    score: number; grade: string;
    summary: { en: string; hi: string };
    counts: { ideal: number; acceptable: number; adjustment_needed: number; avoid: number };
  };
  mahadasha_alert?: {
    active_lord: string; lord_direction: string;
    summary_en: string; summary_hi: string;
  } | null;
  rooms: RoomReport[];
  priority_actions: PriorityAction[];
  footer: string;
  quota: { used: number; limit: number; plan: string };
  pdf_url?: string;
  pdf_token?: string;
  vision_room_findings?: VisionRoomFindings;
};
type ErrorPayload = {
  error: string; message?: string; missing_fields?: string[];
  upgrade_required?: boolean;
};

// ─────────────────────────────────────────────────────────────────────────
export default function AstroVastuProScreen() {
  const C = useC();
  const insets = useSafeAreaInsets();
  const { user } = useUser();

  const [loading,    setLoading]    = useState(false);
  const [result,     setResult]     = useState<ProResponse | null>(null);
  const [error,      setError]      = useState<ErrorPayload | null>(null);
  const [northAt,    setNorthAt]    = useState<NorthAt>("top");
  const [roomPhotos, setRoomPhotos] = useState<RoomPhoto[]>([]);

  // ── Shared submit helper ──────────────────────────────────────────────
  const runScan = useCallback(async (payload: Record<string, unknown>) => {
    if (loading) return;
    if (!user?.id || !user?.api_key) {
      setError({ error: "auth_required", message: "Please log in to run a Smart Scan." });
      return;
    }
    setError(null); setResult(null); setLoading(true);
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    try {
      const resp = await fetch(`${API_BASE}/api/astrovastu-pro`, {
        method:  "POST",
        headers: { "Content-Type": "application/json", "X-API-Key": user.api_key },
        body:    JSON.stringify({ user_id: user.id, ...payload }),
      });
      const body = await resp.json();
      if (!resp.ok) {
        setError({ ...(body as ErrorPayload), error: body.error || `HTTP ${resp.status}` });
        Haptics.notificationAsync(Haptics.NotificationFeedbackType.Warning);
      } else {
        setResult(body as ProResponse);
        Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      }
    } catch (e: any) {
      setError({ error: "network", message: String(e?.message || e) });
    } finally {
      setLoading(false);
    }
  }, [loading, user]);

  // ── Camera capture: send only the image (vision will detect rooms) ──
  const onCapture = useCallback((capture: SmartScanResult) => {
    runScan({
      floor_plan_upload: {
        type:     "image",
        data_url: capture.data_url,
        north_at: northAt,
        ...(typeof capture.heading_deg === "number"
          ? { heading_deg: capture.heading_deg }
          : {}),
      },
      ...(roomPhotos.length > 0 ? { room_photos: roomPhotos } : {}),
    });
  }, [runScan, northAt, roomPhotos]);

  // ── Gallery / PDF upload: file + user-tagged room/direction (ground truth) ─
  const onGallerySubmit = useCallback((g: GalleryScanResult) => {
    runScan({
      floor_plan: [{ room_type: g.room_type, direction: g.direction }],
      floor_plan_upload: {
        type:     g.kind,
        data_url: g.data_url,
        north_at: northAt,
      },
      ...(roomPhotos.length > 0 ? { room_photos: roomPhotos } : {}),
    });
  }, [runScan, northAt, roomPhotos]);

  // ─────────────────────────────────────────────────────────────────────
  return (
    <View style={{ flex: 1, backgroundColor: C.bg, paddingTop: insets.top }}>
      <Stack.Screen options={{ headerShown: false }} />
      <LinearGradient
        colors={[C.bg, C.bgCard]}
        style={[styles.header, { paddingTop: 4 }]}
      >
        <Pressable onPress={() => router.back()} hitSlop={10} style={{ padding: 6 }}>
          <Feather name="arrow-left" size={22} color={C.text} />
        </Pressable>
        <Text style={[styles.headerTitle, { color: C.text }]}>AstroVastu PRO</Text>
        <View style={{ width: 28 }} />
      </LinearGradient>

      <ScrollView
        contentContainerStyle={{ padding: 16, paddingBottom: insets.bottom + 40 }}
        keyboardShouldPersistTaps="handled"
      >
        {/* ── Hero + Smart Scan button ─────────────────────────────── */}
        <View style={[styles.hero, { backgroundColor: C.bgCard, borderColor: C.border }]}>
          <View style={[styles.heroIcon, { backgroundColor: C.accentBg }]}>
            <Feather name="zap" size={26} color={C.accent} />
          </View>
          <Text style={[styles.heroTitle, { color: C.text }]}>Smart Scan</Text>
          <Text style={[styles.heroBody, { color: C.textMid }]}>
            Tap the button below to open the live camera with a built-in compass.
            Aim at your floor plan or any room — we'll detect the layout and run
            a personalised Vastu × Kundli analysis.
          </Text>
        </View>

        <SmartScanCamera
          onCapture={onCapture}
          loading={loading}
          hint="Camera + compass · One tap to scan"
        />

        {/* OR divider */}
        <View style={styles.orRow}>
          <View style={[styles.orLine, { backgroundColor: C.border }]} />
          <Text style={[styles.orText, { color: C.textMid }]}>OR</Text>
          <View style={[styles.orLine, { backgroundColor: C.border }]} />
        </View>

        {/* Gallery upload — for users not at home */}
        <GalleryScanUpload
          onSubmit={onGallerySubmit}
          loading={loading}
        />

        {/* ── North-at calibration (applies to camera + gallery upload) ── */}
        <View style={[styles.northCard, { backgroundColor: C.bgCard, borderColor: C.border }]}>
          <View style={{ flexDirection: "row", alignItems: "center", gap: 6, marginBottom: 4 }}>
            <Feather name="compass" size={14} color={C.accent} />
            <Text style={[styles.northTitle, { color: C.text }]}>
              Where is North on your floor plan?
            </Text>
          </View>
          <Text style={[styles.northSub, { color: C.textMid }]}>
            Look for a North arrow (N↑) on your plan. If unsure, leave it on Top.
          </Text>
          <View style={styles.northRow}>
            {(["top","right","bottom","left"] as const).map((opt) => {
              const sel = northAt === opt;
              return (
                <Pressable
                  key={opt}
                  onPress={() => setNorthAt(opt)}
                  disabled={loading}
                  style={({ pressed }) => [
                    styles.northBtn,
                    {
                      borderColor: sel ? C.accent : C.border,
                      backgroundColor: sel ? C.accentBg : "transparent",
                      opacity: loading ? 0.5 : pressed ? 0.7 : 1,
                    },
                  ]}
                >
                  <Text style={{ color: sel ? C.accent : C.text, fontWeight: "700", fontSize: 12 }}>
                    {opt[0].toUpperCase() + opt.slice(1)}
                  </Text>
                </Pressable>
              );
            })}
          </View>
        </View>

        {/* ── Optional: per-room photos with live magnetometer compass ── */}
        <RoomPhotoCapture
          rooms={PRO_DEFAULT_ROOMS}
          photos={roomPhotos}
          onChange={setRoomPhotos}
          disabled={loading}
        />

        {/* ── Error / paywall card ─────────────────────────────────── */}
        {error && (
          <View style={[styles.errCard, {
            backgroundColor: C.bgCard, borderColor: VERDICT_COLOR.Avoid.border,
          }]}>
            <Feather name="alert-triangle" size={18} color={VERDICT_COLOR.Avoid.fg} style={{ marginTop: 2 }} />
            <View style={{ flex: 1 }}>
              <Text style={[styles.errTitle, { color: C.text }]}>
                {error.error === "monthly_limit_reached" ? "Monthly limit reached" :
                 error.error === "upgrade_required"      ? "Upgrade required"      :
                 error.error === "profile_incomplete"    ? "Complete your profile" :
                 error.error === "vision_no_rooms"       ? "Couldn't read this photo" :
                 "Smart Scan failed"}
              </Text>
              <Text style={[styles.errBody, { color: C.textMid, marginTop: 4 }]}>
                {error.message || "Please try a clearer photo of your floor plan or the full room."}
              </Text>
              {error.error === "profile_incomplete" && (
                <Pressable onPress={() => router.push("/profile-edit")}
                           style={[styles.upgradeBtn, { backgroundColor: C.accent, marginTop: 10 }]}>
                  <Text style={styles.upgradeText}>Complete Profile</Text>
                </Pressable>
              )}
              {(error.upgrade_required || error.error === "upgrade_required" ||
                error.error === "monthly_limit_reached") && (
                <Pressable onPress={() => router.push("/subscription")}
                           style={[styles.upgradeBtn, { backgroundColor: C.accent, marginTop: 10 }]}>
                  <Text style={styles.upgradeText}>Upgrade to Pro — Unlimited</Text>
                </Pressable>
              )}
            </View>
          </View>
        )}

        {/* ── Result: PDF version ────────────────────────────────────── */}
        {result && result.pdf_url && result.pdf_token && (() => {
          const overall = result.overall || ({} as ProResponse["overall"]);
          const grade   = overall.grade || "C";
          const score   = typeof overall.score === "number" ? overall.score : 0;
          const summary = overall.summary || { en: "", hi: "" };
          const pdfFullUrl =
            `${API_BASE}${result.pdf_url}?t=${encodeURIComponent(result.pdf_token)}`;
          const openPdf = async () => {
            try {
              Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
              await WebBrowser.openBrowserAsync(pdfFullUrl, {
                presentationStyle: WebBrowser.WebBrowserPresentationStyle.FULL_SCREEN,
                showTitle: true,
                enableBarCollapsing: true,
              });
            } catch (e: any) {
              try { await Linking.openURL(pdfFullUrl); }
              catch { Alert.alert("Open PDF", "Could not open the PDF.\n\n" + String(e?.message || e)); }
            }
          };
          return (
            <View style={{ marginTop: 18 }}>
              <View style={[styles.scoreCard, { backgroundColor: C.bgCard, borderColor: C.border }]}>
                <Text style={[styles.sectionLabel, { color: C.textMid }]}>OVERALL HOUSE SCORE</Text>
                <View style={{ flexDirection: "row", alignItems: "baseline", gap: 6, marginTop: 4 }}>
                  <Text style={[styles.scoreNum, { color: GRADE_COLOR[grade] || C.text }]}>{score}</Text>
                  <Text style={{ color: C.textMid, fontWeight: "600" }}>/100</Text>
                  <View style={{
                    marginLeft: 8, paddingHorizontal: 10, paddingVertical: 3, borderRadius: 8,
                    backgroundColor: GRADE_COLOR[grade] || C.accent,
                  }}>
                    <Text style={{ color: "#fff", fontWeight: "800" }}>Grade {grade}</Text>
                  </View>
                </View>
                {summary.en ? (
                  <Text style={{ color: C.text, fontSize: 13, marginTop: 6 }}>{summary.en}</Text>
                ) : null}
                <ScanBasisBadge
                  visionRoomFindings={result.vision_room_findings}
                  perRoomBasis={(result.rooms || []).map((rr: any) => ({
                    room_type: rr.room_type, direction_basis: rr.direction_basis,
                  }))}
                />
              </View>

              <View style={[styles.card, { backgroundColor: C.bgCard, borderColor: C.border, marginTop: 12 }]}>
                <View style={{ flexDirection: "row", alignItems: "center", gap: 8, marginBottom: 8 }}>
                  <Feather name="file-text" size={18} color={C.accent} />
                  <Text style={[styles.cardTitle, { color: C.text }]}>Detailed PDF Report Ready</Text>
                </View>
                <Text style={{ color: C.text, fontSize: 13, marginBottom: 12 }}>
                  Aapka full AstroVastu PRO report PDF me ready hai — har room ka deep verdict,
                  Mahadasha layer, priority actions aur classical references.
                </Text>
                <Pressable onPress={openPdf} style={[styles.submitBtn, { backgroundColor: C.accent }]}>
                  <View style={{ flexDirection: "row", alignItems: "center", gap: 8 }}>
                    <Feather name="download" size={16} color="#fff" />
                    <Text style={styles.submitText}>Open PDF Report</Text>
                  </View>
                </Pressable>
              </View>

              <Text style={{ color: C.textMid, fontSize: 11, marginTop: 14, textAlign: "center" }}>
                {result.footer || "Powered by Advanced Cosmic Intelligence"}
              </Text>
            </View>
          );
        })()}

        {/* ── Result: in-app version (no PDF) ──────────────────────── */}
        {result && !result.pdf_url && (() => {
          const overall  = result.overall  || ({} as ProResponse["overall"]);
          const counts   = overall.counts  || { ideal: 0, acceptable: 0, adjustment_needed: 0, avoid: 0 };
          const summary  = overall.summary || { en: "", hi: "" };
          const grade    = overall.grade   || "C";
          const score    = typeof overall.score === "number" ? overall.score : 0;
          const rooms_   = Array.isArray(result.rooms) ? result.rooms : [];
          const priorities = Array.isArray(result.priority_actions) ? result.priority_actions : [];
          const mdAlert  = result.mahadasha_alert || null;
          const quota    = result.quota || { used: 0, limit: 0, plan: "" };
          return (
          <View style={{ marginTop: 18 }}>
            <View style={[styles.scoreCard, { backgroundColor: C.bgCard, borderColor: C.border }]}>
              <Text style={[styles.sectionLabel, { color: C.textMid }]}>OVERALL HOUSE SCORE</Text>
              <View style={{ flexDirection: "row", alignItems: "baseline", gap: 6, marginTop: 4 }}>
                <Text style={[styles.scoreNum, { color: GRADE_COLOR[grade] || C.text }]}>{score}</Text>
                <Text style={{ color: C.textMid, fontWeight: "600" }}>/100</Text>
                <View style={{
                  marginLeft: 8, paddingHorizontal: 10, paddingVertical: 3, borderRadius: 8,
                  backgroundColor: GRADE_COLOR[grade] || C.accent,
                }}>
                  <Text style={{ color: "#fff", fontWeight: "800" }}>Grade {grade}</Text>
                </View>
              </View>
              <ScanBasisBadge
                visionRoomFindings={result.vision_room_findings}
                perRoomBasis={(result.rooms || []).map((rr: any) => ({
                  room_type: rr.room_type, direction_basis: rr.direction_basis,
                }))}
              />
              <Text style={{ color: C.text, fontSize: 13, marginTop: 6 }}>{summary.en}</Text>
              <Text style={{ color: C.textMid, fontSize: 12, marginTop: 2 }}>{summary.hi}</Text>
            </View>

            <View style={styles.countsRow}>
              {([
                ["Ideal",      counts.ideal,             VERDICT_COLOR.Ideal],
                ["Acceptable", counts.acceptable,        VERDICT_COLOR.Acceptable],
                ["Adjust",     counts.adjustment_needed, VERDICT_COLOR["Adjustment Needed"]],
                ["Avoid",      counts.avoid,             VERDICT_COLOR.Avoid],
              ] as const).map(([label, count, col]) => (
                <View key={label} style={[styles.countPill, { backgroundColor: col.bg, borderColor: col.border }]}>
                  <Text style={{ color: col.fg, fontWeight: "800", fontSize: 16 }}>{count}</Text>
                  <Text style={{ color: col.fg, fontSize: 10, fontWeight: "600" }}>{label}</Text>
                </View>
              ))}
            </View>

            {mdAlert && (
              <View style={[styles.mdAlert, {
                backgroundColor: C.bgCard, borderColor: VERDICT_COLOR["Adjustment Needed"].border,
              }]}>
                <View style={{ flexDirection: "row", alignItems: "center", gap: 6, marginBottom: 6 }}>
                  <Feather name="zap" size={16} color={VERDICT_COLOR["Adjustment Needed"].fg} />
                  <Text style={[styles.cardTitle, { color: C.text }]}>
                    Mahadasha Alert · {mdAlert.active_lord} ({mdAlert.lord_direction})
                  </Text>
                </View>
                <Text style={{ color: C.text, fontSize: 13 }}>{mdAlert.summary_en}</Text>
                <Text style={{ color: C.textMid, fontSize: 12, marginTop: 4 }}>{mdAlert.summary_hi}</Text>
              </View>
            )}

            {priorities.length > 0 && (
              <View style={[styles.card, { backgroundColor: C.bgCard, borderColor: C.border, marginTop: 14 }]}>
                <Text style={[styles.sectionLabel, { color: C.textMid, marginBottom: 8 }]}>
                  PRIORITY ACTIONS
                </Text>
                {priorities.map((p, i) => {
                  const col = VERDICT_COLOR[p.verdict] || VERDICT_COLOR.Acceptable;
                  return (
                    <View key={`${p.room_type}-${p.direction}-${i}`} style={styles.priRow}>
                      <View style={[styles.priBadge, { backgroundColor: col.fg }]}>
                        <Text style={{ color: "#fff", fontWeight: "800" }}>{i + 1}</Text>
                      </View>
                      <View style={{ flex: 1 }}>
                        <Text style={{ color: C.text, fontWeight: "700", fontSize: 14 }}>
                          {p.room_type} · {p.direction}  ·  {p.verdict}
                        </Text>
                        <Text style={{ color: C.textMid, fontSize: 12, marginTop: 2 }}>{p.why}</Text>
                        {p.remedies.slice(0, 2).map((rem, j) => (
                          <Text key={j} style={{ color: C.text, fontSize: 12, marginTop: 4 }}>
                            • {rem.english}
                          </Text>
                        ))}
                      </View>
                    </View>
                  );
                })}
              </View>
            )}

            <Text style={[styles.sectionLabel, { color: C.textMid, marginTop: 16, marginBottom: 6 }]}>
              ROOM-BY-ROOM BREAKDOWN
            </Text>
            {rooms_.map((r, idx) => {
              const col = VERDICT_COLOR[r.verdict] || VERDICT_COLOR.Acceptable;
              return (
                <View key={idx} style={[styles.roomReport, { backgroundColor: C.bgCard, borderColor: C.border }]}>
                  <View style={{ flexDirection: "row", alignItems: "center", justifyContent: "space-between" }}>
                    <Text style={{ color: C.text, fontSize: 14, fontWeight: "700" }}>
                      {r.room_type} · {r.direction}
                    </Text>
                    <View style={[styles.miniPill, { backgroundColor: col.bg, borderColor: col.border }]}>
                      <Text style={{ color: col.fg, fontWeight: "800", fontSize: 11 }}>{r.verdict}</Text>
                    </View>
                  </View>
                  {r.zone?.planet && (
                    <Text style={{ color: C.textMid, fontSize: 11, marginTop: 4 }}>
                      Zone: {r.zone.planet} · {r.zone.deity}  ·  Score {r.score}/100
                    </Text>
                  )}
                  {r.mahadasha_layer?.applies && r.mahadasha_layer?.reason_en && (
                    <Text style={{ color: VERDICT_COLOR["Adjustment Needed"].fg, fontSize: 11, marginTop: 4 }}>
                      ⚡ {r.mahadasha_layer.reason_en}
                    </Text>
                  )}
                  {r.remedies.slice(0, 2).map((rem, j) => (
                    <Text key={j} style={{ color: C.text, fontSize: 12, marginTop: 4 }}>• {rem.english}</Text>
                  ))}
                </View>
              );
            })}

            <Text style={{ color: C.textMid, fontSize: 11, textAlign: "center", marginTop: 14 }}>
              {quota.limit === -1
                ? `Unlimited PRO scans (Pro plan)`
                : `Scan ${quota.used}/${quota.limit} this month`}
            </Text>
          </View>
          );
        })()}

        {/* ── Branding footer (NEVER reveal AI/LLM) ──────────────────── */}
        <Text style={[styles.brandingFooter, { color: C.textMid }]}>
          ✨ Powered by Advanced Cosmic Intelligence
        </Text>
        <Text style={[styles.brandingFooterSmall, { color: C.textMid }]}>
          Cosmic AstroVastu Drishti — PRO Engine v1.0
        </Text>
      </ScrollView>
    </View>
  );
}

// ─────────────────────────────────────────────────────────────────────────
const styles = StyleSheet.create({
  header: {
    flexDirection: "row", alignItems: "center", justifyContent: "space-between",
    paddingHorizontal: 16, paddingBottom: 10,
  },
  headerTitle: { fontSize: 17, fontWeight: "700" },

  hero:        { borderRadius: 16, borderWidth: 1, padding: 20,
                 marginBottom: 16, alignItems: "center" },
  heroIcon:    { width: 56, height: 56, borderRadius: 28,
                 alignItems: "center", justifyContent: "center", marginBottom: 10 },
  heroTitle:   { fontSize: 22, fontWeight: "800", marginBottom: 6 },
  heroBody:    { fontSize: 13, lineHeight: 19, textAlign: "center" },

  card:        { borderRadius: 14, borderWidth: 1, padding: 14, marginBottom: 14 },
  cardTitle:   { fontSize: 15, fontWeight: "700" },
  sectionLabel:{ fontSize: 11, fontWeight: "800", textTransform: "uppercase", letterSpacing: 0.5 },

  submitBtn:   { height: 50, borderRadius: 14, alignItems: "center", justifyContent: "center",
                 shadowOpacity: 0.2, shadowRadius: 8, elevation: 3 },
  submitText:  { color: "#fff", fontSize: 16, fontWeight: "700" },

  errCard:     { flexDirection: "row", alignItems: "flex-start", gap: 10,
                 borderRadius: 12, borderWidth: 1, padding: 12, marginTop: 16 },
  errTitle:    { fontSize: 14, fontWeight: "700" },
  errBody:     { fontSize: 13, lineHeight: 18 },
  upgradeBtn:  { paddingVertical: 10, paddingHorizontal: 14, borderRadius: 10, alignItems: "center" },
  upgradeText: { color: "#fff", fontWeight: "700", fontSize: 13 },

  scoreCard:   { borderRadius: 16, borderWidth: 1, padding: 14 },
  scoreNum:    { fontSize: 44, fontWeight: "800" },

  countsRow:   { flexDirection: "row", gap: 8, marginTop: 10 },
  countPill:   { flex: 1, alignItems: "center", paddingVertical: 8, borderRadius: 10, borderWidth: 1 },

  mdAlert:     { borderRadius: 12, borderWidth: 1, padding: 12, marginTop: 14 },

  priRow:      { flexDirection: "row", gap: 10, paddingVertical: 8, alignItems: "flex-start" },
  priBadge:    { width: 26, height: 26, borderRadius: 13,
                 alignItems: "center", justifyContent: "center", marginTop: 1 },

  roomReport:  { borderRadius: 12, borderWidth: 1, padding: 12, marginBottom: 8 },
  miniPill:    { paddingHorizontal: 8, paddingVertical: 3, borderRadius: 8, borderWidth: 1 },

  brandingFooter:      { fontSize: 12, textAlign: "center", marginTop: 28, fontWeight: "600" },
  brandingFooterSmall: { fontSize: 10, textAlign: "center", marginTop: 4, opacity: 0.7 },

  orRow:    { flexDirection: "row", alignItems: "center", gap: 12, marginVertical: 16 },
  orLine:   { flex: 1, height: 1 },
  orText:   { fontSize: 11, fontWeight: "700", letterSpacing: 1 },

  northCard:  { borderRadius: 12, borderWidth: 1, padding: 12, marginTop: 14, marginBottom: 14 },
  northTitle: { fontSize: 13, fontWeight: "700" },
  northSub:   { fontSize: 11, lineHeight: 15, marginTop: 2, marginBottom: 8 },
  northRow:   { flexDirection: "row", gap: 6 },
  northBtn:   { flex: 1, paddingVertical: 9, borderRadius: 8, borderWidth: 1, alignItems: "center" },
});
