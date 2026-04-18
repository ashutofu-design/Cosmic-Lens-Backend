/**
 * AstroVastu PRO — Multi-room Deep Scan
 *
 * User builds a floor plan (up to 12 rooms × direction), backend runs a
 * deterministic kundli-aware deep scan with the **mahadasha-mandatory layer**
 * and returns:
 *   - overall house score 0-100 + grade A-D
 *   - active-mahadasha-wide alert (which rooms conflict / which are favoured)
 *   - per-room verdict + remedies + classical refs
 *   - priority action plan (top 5 most urgent fixes)
 *
 * No AI/LLM — pure rules + classical Vastu × Jyotish synthesis.
 * Quota: 1 scan / month for Basic, unlimited for Pro.
 */
import { Feather } from "@expo/vector-icons";
import * as Haptics from "expo-haptics";
import * as Linking from "expo-linking";
import { LinearGradient } from "expo-linear-gradient";
import { router, Stack } from "expo-router";
import React, { useCallback, useState } from "react";
import {
  ActivityIndicator,
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
import { AstroVastuWallet } from "@/components/AstroVastuWallet";
import { RoomPhoto, RoomPhotoCapture } from "@/components/RoomPhotoCapture";
import { ScanBasisBadge, VisionRoomFindings } from "@/components/ScanBasisBadge";
import { SmartScanUpload, SmartScanUploadValue } from "@/components/SmartScanUpload";

// ─────────────────────────────────────────────────────────────────────────
// Static option lists (ready for 24-language i18n migration)
// ─────────────────────────────────────────────────────────────────────────
const ROOM_OPTIONS: { key: string; en: string; hi: string; icon: keyof typeof Feather.glyphMap }[] = [
  { key: "bedroom",  en: "Bedroom",       hi: "Shayan",        icon: "moon"      },
  { key: "kitchen",  en: "Kitchen",       hi: "Rasoi",         icon: "coffee"    },
  { key: "pooja",    en: "Pooja Room",    hi: "Pooja sthal",   icon: "sun"       },
  { key: "study",    en: "Study",         hi: "Adhyayan",      icon: "book-open" },
  { key: "bathroom", en: "Bathroom",      hi: "Snan-grih",     icon: "droplet"   },
  { key: "toilet",   en: "Toilet",        hi: "Shauchalaya",   icon: "alert-circle" },
  { key: "living",   en: "Living Room",   hi: "Baithak",       icon: "home"      },
  { key: "entrance", en: "Entrance",      hi: "Pravesh dwaar", icon: "log-in"    },
  { key: "store",    en: "Store",         hi: "Bhandaar",      icon: "package"   },
];

const DIRECTION_OPTIONS: { key: string; short: string; en: string; hi: string }[] = [
  { key: "N",  short: "N",  en: "North",      hi: "Uttar"    },
  { key: "NE", short: "NE", en: "North-East", hi: "Ishan"    },
  { key: "E",  short: "E",  en: "East",       hi: "Poorv"    },
  { key: "SE", short: "SE", en: "South-East", hi: "Agneya"   },
  { key: "S",  short: "S",  en: "South",      hi: "Dakshin"  },
  { key: "SW", short: "SW", en: "South-West", hi: "Nairutya" },
  { key: "W",  short: "W",  en: "West",       hi: "Paschim"  },
  { key: "NW", short: "NW", en: "North-West", hi: "Vayavya"  },
];

const VERDICT_COLOR: Record<string, { bg: string; fg: string; border: string }> = {
  Ideal:                { bg: "rgba(16,185,129,0.18)", fg: "#10B981", border: "rgba(16,185,129,0.45)" },
  Acceptable:           { bg: "rgba(59,130,246,0.18)", fg: "#3B82F6", border: "rgba(59,130,246,0.45)" },
  "Adjustment Needed":  { bg: "rgba(245,158,11,0.18)", fg: "#F59E0B", border: "rgba(245,158,11,0.45)" },
  Avoid:                { bg: "rgba(239,68,68,0.18)",  fg: "#EF4444", border: "rgba(239,68,68,0.45)"  },
};

const GRADE_COLOR: Record<string, string> = {
  A: "#10B981", B: "#3B82F6", C: "#F59E0B", D: "#EF4444",
};

// ─────────────────────────────────────────────────────────────────────────
// Response types (mirror backend astrovastu_pro_response.py)
// ─────────────────────────────────────────────────────────────────────────
type Remedy = { action: string; english: string; hindi: string; priority: number; classical_ref: string };
type ClassicalRef = { type: string; source: string };
type RoomReport = {
  room_type: string; direction: string; verdict: string;
  verdict_label: { en: string; hi: string };
  severity: string; severity_label: string; score: number;
  zone: { direction: string; planet?: string; deity?: string; element?: string };
  mahadasha_layer: { applies: boolean; kind?: string; reason_en?: string; reason_hi?: string };
  remedies: Remedy[]; classical_refs: ClassicalRef[];
  reasons?: { en?: string; hi?: string };
};
type PriorityAction = {
  room_type: string; direction: string; verdict: string; severity: string;
  why: string; remedies: Remedy[];
};
type ProResponse = {
  meta:   { powered_by: string; generated_at: string; tier: string; rooms_count: number };
  overall: {
    score: number; grade: string;
    summary: { en: string; hi: string };
    counts: { ideal: number; acceptable: number; adjustment_needed: number; avoid: number };
  };
  kundli_summary: { lagna?: string; moon_sign?: string; mahadasha?: string; sade_sati: boolean; atmakaraka?: string; ishta_devata?: string };
  mahadasha_alert?: {
    active_lord: string; lord_direction: string;
    conflict_rooms: string[]; favourable_rooms: string[];
    summary_en: string; summary_hi: string;
  } | null;
  rooms: RoomReport[];
  priority_actions: PriorityAction[];
  classical_summary: ClassicalRef[];
  footer: string;
  quota: { used: number; limit: number; plan: string };
  pdf_url?: string;
  pdf_token?: string;
  report_id?: number;
  vision_room_findings?: VisionRoomFindings;
};

type ErrorPayload = {
  error: string; message?: string; missing_fields?: string[];
  upgrade_required?: boolean; quota?: { used: number; limit: number };
  plan?: string;
};

// ─────────────────────────────────────────────────────────────────────────
type FloorRoom = { room_type: string; direction: string };

const DEFAULT_ROOMS: FloorRoom[] = [
  { room_type: "bedroom", direction: "" },
  { room_type: "kitchen", direction: "" },
  { room_type: "pooja",   direction: "" },
];

// ─────────────────────────────────────────────────────────────────────────
export default function AstroVastuProScreen() {
  const C = useC();
  const insets = useSafeAreaInsets();
  const { user } = useUser();

  const [rooms,   setRooms]   = useState<FloorRoom[]>(DEFAULT_ROOMS);
  const [editIdx, setEditIdx] = useState<number | null>(null);   // which row is choosing direction
  const [loading, setLoading] = useState(false);
  const [result,  setResult]  = useState<ProResponse | null>(null);
  const [error,   setError]   = useState<ErrorPayload | null>(null);
  const [propertyName, setPropertyName] = useState<string>("");  // Phase 2: per-property unlock match
  const [walletKey,    setWalletKey]    = useState(0);
  const [scanUpload,   setScanUpload]   = useState<SmartScanUploadValue | null>(null);
  const [roomPhotos,   setRoomPhotos]   = useState<RoomPhoto[]>([]);

  // ── Floor-plan editor handlers ────────────────────────────────────────
  const addRoom = useCallback(() => {
    if (rooms.length >= 12) return;
    Haptics.selectionAsync();
    setRooms((rs) => [...rs, { room_type: "bedroom", direction: "" }]);
  }, [rooms.length]);

  const removeRoom = useCallback((idx: number) => {
    Haptics.selectionAsync();
    setRooms((rs) => rs.filter((_, i) => i !== idx));
  }, []);

  const updateRoom = useCallback((idx: number, patch: Partial<FloorRoom>) => {
    setRooms((rs) => rs.map((r, i) => (i === idx ? { ...r, ...patch } : r)));
  }, []);

  // ── Submit handler ────────────────────────────────────────────────────
  const onSubmit = useCallback(async () => {
    if (loading) return;
    if (!user?.id || !user?.api_key) {
      setError({ error: "auth_required", message: "Please log in to run a deep scan." });
      return;
    }
    const valid = rooms.filter((r) => r.room_type && r.direction);
    if (valid.length === 0 && !scanUpload) {
      setError({ error: "validation", message: "Add at least one room with a direction, or upload a floor plan." });
      return;
    }

    setError(null); setResult(null); setLoading(true);
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);

    try {
      const resp = await fetch(`${API_BASE}/api/astrovastu-pro`, {
        method:  "POST",
        headers: { "Content-Type": "application/json", "X-API-Key": user.api_key },
        body:    JSON.stringify({
          user_id: user.id,
          floor_plan: valid,
          property_name: propertyName.trim(),
          ...(scanUpload ? { floor_plan_upload: {
              type:     scanUpload.type,
              ...(scanUpload.data_url ? { data_url: scanUpload.data_url } : {}),
              ...(scanUpload.base64   ? { base64:   scanUpload.base64   } : {}),
              ...(scanUpload.north_at ? { north_at: scanUpload.north_at } : {}),
            } } : {}),
          ...(roomPhotos.length > 0 ? { room_photos: roomPhotos } : {}),
        }),
      });
      const body = await resp.json();
      if (!resp.ok) {
        setError({ ...(body as ErrorPayload), error: body.error || `HTTP ${resp.status}` });
        Haptics.notificationAsync(Haptics.NotificationFeedbackType.Warning);
      } else {
        setResult(body as ProResponse);
        setWalletKey((k) => k + 1);
        Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      }
    } catch (e: any) {
      setError({ error: "network", message: String(e?.message || e) });
    } finally {
      setLoading(false);
    }
  }, [loading, rooms, user, propertyName, scanUpload, roomPhotos]);

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
        {/* ── Intro card ──────────────────────────────────────────────── */}
        <View style={[styles.card, { backgroundColor: C.bgCard, borderColor: C.border }]}>
          <View style={{ flexDirection: "row", alignItems: "center", gap: 8, marginBottom: 6 }}>
            <Feather name="layers" size={18} color={C.accent} />
            <Text style={[styles.cardTitle, { color: C.text }]}>Full-house Deep Scan</Text>
          </View>
          <Text style={[styles.bodyText, { color: C.textMid }]}>
            Add each room of your home with its direction. We synthesize Vastu Shastra +
            your Kundli + the active Mahadasha to generate a personalised priority plan.
          </Text>
          <Text style={[styles.bodyTextSmall, { color: C.textMid, marginTop: 6 }]}>
            Aapke ghar ke har kamre ki disha daalein. Hum Vastu Shastra + aapki Kundli +
            chal rahi Mahadasha ka deep analysis karenge.
          </Text>
        </View>

        {/* ── AstroVastu Wallet (Phase 2: unlocks + buy CTAs) ─────── */}
        <AstroVastuWallet
          variant="pro"
          propertyName={propertyName}
          onPropertyNameChange={setPropertyName}
          refreshKey={walletKey}
        />

        {/* ── Smart Scan upload (Phase 6) ────────────────────────────── */}
        <View style={{ marginTop: 14 }}>
          <SmartScanUpload value={scanUpload} onChange={setScanUpload} disabled={loading} />
        </View>

        {/* ── Room photo capture with live compass (Phase 7) ──────────── */}
        <RoomPhotoCapture
          rooms={rooms
            .filter((r) => r.room_type && r.direction)
            .map((r, i) => {
              const ro = ROOM_OPTIONS.find((x) => x.key === r.room_type);
              const di = DIRECTION_OPTIONS.find((x) => x.key === r.direction);
              return {
                key:   `${r.room_type}-${i}`,
                label: `${ro?.en || r.room_type} (${di?.short || r.direction})`,
              };
            })
            .filter((c, i, arr) => arr.findIndex((x) => x.key === c.key) === i)
            .map((c) => ({ key: c.key.split("-")[0], label: c.label }))}
          photos={roomPhotos}
          onChange={setRoomPhotos}
          disabled={loading}
        />

        {/* ── Floor-plan editor ───────────────────────────────────────── */}
        <Text style={[styles.sectionTitle, { color: C.text, marginTop: 4 }]}>
          {scanUpload ? "Optional: Refine Rooms" : `Your Floor Plan (${rooms.length}/12)`}
        </Text>
        {scanUpload ? (
          <Text style={{ color: C.textMid, fontSize: 11, marginBottom: 6 }}>
            Cosmic Vision will detect rooms from your upload. You can also list rooms here to override.
          </Text>
        ) : null}

        {rooms.map((r, idx) => {
          const ro = ROOM_OPTIONS.find((x) => x.key === r.room_type) ?? ROOM_OPTIONS[0];
          const di = DIRECTION_OPTIONS.find((x) => x.key === r.direction);
          const isEditing = editIdx === idx;
          return (
            <View key={idx} style={[styles.roomRow, { backgroundColor: C.bgCard, borderColor: C.border }]}>
              <View style={{ flex: 1 }}>
                {/* Room type chips */}
                <ScrollView horizontal showsHorizontalScrollIndicator={false}
                            contentContainerStyle={{ gap: 6, paddingVertical: 2 }}>
                  {ROOM_OPTIONS.map((opt) => {
                    const sel = opt.key === r.room_type;
                    return (
                      <Pressable key={opt.key}
                                 onPress={() => { Haptics.selectionAsync(); updateRoom(idx, { room_type: opt.key }); }}
                                 style={[styles.roomChip,
                                         { borderColor: sel ? C.accent : C.border,
                                           backgroundColor: sel ? C.accentBg : "transparent" }]}>
                        <Feather name={opt.icon} size={12} color={sel ? C.accent : C.textMid} />
                        <Text style={{ color: sel ? C.accent : C.textMid, fontSize: 11, fontWeight: "600" }}>
                          {opt.en}
                        </Text>
                      </Pressable>
                    );
                  })}
                </ScrollView>

                {/* Direction picker (collapsed → expanded) */}
                <Pressable
                  onPress={() => { Haptics.selectionAsync(); setEditIdx(isEditing ? null : idx); }}
                  style={[styles.dirSummary, { borderColor: C.border }]}
                >
                  <Text style={{ color: C.textMid, fontSize: 12 }}>Direction:</Text>
                  <Text style={{ color: di ? C.text : C.textMid, fontSize: 13, fontWeight: "700" }}>
                    {di ? `${di.short} · ${di.hi}` : "Select direction"}
                  </Text>
                  <Feather name={isEditing ? "chevron-up" : "chevron-down"} size={14} color={C.textMid} />
                </Pressable>

                {isEditing && (
                  <View style={styles.dirGrid}>
                    {DIRECTION_OPTIONS.map((d) => {
                      const sel = d.key === r.direction;
                      return (
                        <Pressable key={d.key}
                                   onPress={() => { Haptics.selectionAsync(); updateRoom(idx, { direction: d.key }); setEditIdx(null); }}
                                   style={[styles.dirChip, {
                                     borderColor: sel ? C.accent : C.border,
                                     backgroundColor: sel ? C.accentBg : "transparent",
                                   }]}>
                          <Text style={{ color: sel ? C.accent : C.text, fontWeight: "800" }}>{d.short}</Text>
                          <Text style={{ color: sel ? C.accent : C.textMid, fontSize: 10 }}>{d.hi}</Text>
                        </Pressable>
                      );
                    })}
                  </View>
                )}
              </View>

              <Pressable onPress={() => removeRoom(idx)} hitSlop={8} style={{ paddingHorizontal: 6 }}>
                <Feather name="x-circle" size={20} color={C.textMid} />
              </Pressable>
            </View>
          );
        })}

        <Pressable onPress={addRoom} disabled={rooms.length >= 12}
                   style={[styles.addBtn, { borderColor: C.border, opacity: rooms.length >= 12 ? 0.5 : 1 }]}>
          <Feather name="plus" size={16} color={C.accent} />
          <Text style={{ color: C.accent, fontWeight: "700" }}>Add Room</Text>
        </Pressable>

        {/* ── Submit ─────────────────────────────────────────────────── */}
        <Pressable onPress={onSubmit} disabled={loading}
                   style={[styles.submitBtn, { backgroundColor: C.accent, opacity: loading ? 0.7 : 1 }]}>
          {loading ? <ActivityIndicator color="#fff" />
                   : <Text style={styles.submitText}>Run Deep Scan</Text>}
        </Pressable>

        {/* ── Error / 402 paywall card ───────────────────────────────── */}
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
                 "Deep scan failed"}
              </Text>
              <Text style={[styles.errBody, { color: C.textMid, marginTop: 4 }]}>
                {error.message || "Please try again."}
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

        {/* ── PDF-only result for paid PRO scans ─────────────────────── */}
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
              const ok = await Linking.canOpenURL(pdfFullUrl);
              if (!ok) throw new Error("Cannot open URL");
              await Linking.openURL(pdfFullUrl);
            } catch (e: any) {
              Alert.alert(
                "Open PDF",
                "Could not open the PDF viewer.\n\n" + String(e?.message || e),
              );
            }
          };
          return (
            <View style={{ marginTop: 18 }}>
              <View style={[styles.scoreCard, { backgroundColor: C.bgCard, borderColor: C.border }]}>
                <View style={{ flex: 1 }}>
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
              </View>

              <View style={[styles.card, {
                backgroundColor: C.bgCard, borderColor: C.border, marginTop: 12,
              }]}>
                <View style={{ flexDirection: "row", alignItems: "center", gap: 8, marginBottom: 8 }}>
                  <Feather name="file-text" size={18} color={C.accent} />
                  <Text style={[styles.cardTitle, { color: C.text }]}>Detailed PDF Report Ready</Text>
                </View>
                <Text style={{ color: C.text, fontSize: 13, marginBottom: 4 }}>
                  Aapka full AstroVastu PRO report PDF me ready hai — har room ka deep verdict,
                  Mahadasha layer, priority actions aur classical references.
                </Text>
                <Text style={{ color: C.textMid, fontSize: 12, marginBottom: 12 }}>
                  Your full AstroVastu PRO report is available as a PDF — open, save, or share it.
                </Text>
                <Pressable
                  onPress={openPdf}
                  style={[styles.submitBtn, { backgroundColor: C.accent }]}
                >
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

        {/* ── Legacy on-screen result (only when no pdf_url) ──────────── */}
        {result && !result.pdf_url && (() => {
          const overall  = result.overall  || ({} as ProResponse["overall"]);
          const counts   = overall.counts  || { ideal: 0, acceptable: 0, adjustment_needed: 0, avoid: 0 };
          const summary  = overall.summary || { en: "", hi: "" };
          const grade    = overall.grade   || "C";
          const score    = typeof overall.score === "number" ? overall.score : 0;
          const rooms_   = Array.isArray(result.rooms) ? result.rooms : [];
          const priorities = Array.isArray(result.priority_actions) ? result.priority_actions : [];
          const classicals = Array.isArray(result.classical_summary) ? result.classical_summary : [];
          const mdAlert  = result.mahadasha_alert || null;
          const quota    = result.quota || { used: 0, limit: 0, plan: "" };
          return (
          <View style={{ marginTop: 18 }}>
            {/* Overall score */}
            <View style={[styles.scoreCard, { backgroundColor: C.bgCard, borderColor: C.border }]}>
              <View style={{ flex: 1 }}>
                <Text style={[styles.sectionLabel, { color: C.textMid }]}>OVERALL HOUSE SCORE</Text>
                <View style={{ flexDirection: "row", alignItems: "baseline", gap: 6, marginTop: 4 }}>
                  <Text style={[styles.scoreNum, { color: GRADE_COLOR[grade] || C.text }]}>
                    {score}
                  </Text>
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
                <Text style={{ color: C.text, fontSize: 13, marginTop: 6 }}>
                  {summary.en}
                </Text>
                <Text style={{ color: C.textMid, fontSize: 12, marginTop: 2 }}>
                  {summary.hi}
                </Text>
              </View>
            </View>

            {/* Counts */}
            <View style={[styles.countsRow]}>
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

            {/* Mahadasha alert */}
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

            {/* Priority actions */}
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

            {/* Per-room breakdown */}
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
                  {r.remedies.length > 0 && r.remedies.slice(0, 2).map((rem, j) => (
                    <Text key={j} style={{ color: C.text, fontSize: 12, marginTop: 4 }}>• {rem.english}</Text>
                  ))}
                </View>
              );
            })}

            {/* Classical refs */}
            {classicals.length > 0 && (
              <View style={[styles.card, { backgroundColor: C.bgCard, borderColor: C.border, marginTop: 14 }]}>
                <Text style={[styles.sectionLabel, { color: C.textMid, marginBottom: 8 }]}>
                  CLASSICAL SOURCES
                </Text>
                {classicals.map((ref, i) => (
                  <Text key={i} style={{ color: C.textMid, fontSize: 11, marginBottom: 2 }}>
                    • {ref.type} — {ref.source}
                  </Text>
                ))}
              </View>
            )}

            {/* Quota footer */}
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

  card:        { borderRadius: 14, borderWidth: 1, padding: 14, marginBottom: 14 },
  cardTitle:   { fontSize: 15, fontWeight: "700" },
  bodyText:    { fontSize: 13, lineHeight: 19 },
  bodyTextSmall:{ fontSize: 12, lineHeight: 17 },

  sectionTitle:{ fontSize: 13, fontWeight: "700", marginBottom: 8, opacity: 0.85 },
  sectionLabel:{ fontSize: 11, fontWeight: "800", textTransform: "uppercase", letterSpacing: 0.5 },

  roomRow:     {
    flexDirection: "row", alignItems: "flex-start", gap: 6,
    borderWidth: 1, borderRadius: 12, padding: 8, marginBottom: 8,
  },
  roomChip:    {
    flexDirection: "row", alignItems: "center", gap: 4,
    paddingHorizontal: 8, paddingVertical: 4,
    borderWidth: 1, borderRadius: 14,
  },
  dirSummary:  {
    flexDirection: "row", alignItems: "center", gap: 8,
    borderWidth: 1, borderRadius: 10, paddingHorizontal: 10, paddingVertical: 8, marginTop: 8,
  },
  dirGrid:     { flexDirection: "row", flexWrap: "wrap", gap: 6, marginTop: 8 },
  dirChip:     {
    width: "23%", aspectRatio: 1, borderRadius: 10, borderWidth: 1,
    alignItems: "center", justifyContent: "center", gap: 2,
  },

  addBtn:      {
    flexDirection: "row", alignItems: "center", justifyContent: "center",
    gap: 6, borderRadius: 12, borderWidth: 1, borderStyle: "dashed",
    paddingVertical: 12, marginBottom: 6,
  },

  submitBtn:   {
    height: 50, borderRadius: 14, alignItems: "center", justifyContent: "center",
    marginTop: 14, shadowOpacity: 0.2, shadowRadius: 8, elevation: 3,
  },
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
  priBadge:    {
    width: 26, height: 26, borderRadius: 13,
    alignItems: "center", justifyContent: "center", marginTop: 1,
  },

  roomReport:  { borderRadius: 12, borderWidth: 1, padding: 12, marginBottom: 8 },
  miniPill:    {
    paddingHorizontal: 8, paddingVertical: 3,
    borderRadius: 8, borderWidth: 1,
  },

  brandingFooter:      { fontSize: 12, textAlign: "center", marginTop: 28, fontWeight: "600" },
  brandingFooterSmall: { fontSize: 10, textAlign: "center", marginTop: 4, opacity: 0.7 },
});
