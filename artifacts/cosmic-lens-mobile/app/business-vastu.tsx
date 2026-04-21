/**
 * Business Vastu — Phase 4
 *
 * Premium Vastu deep-scan for commercial premises (Shop / Office / Factory).
 * Combines Vastu Shastra + Owner Kundli + active Mahadasha + business-type
 * critical-room rules to deliver a personalised priority plan.
 *
 * Differentiators vs residential AstroVastu:
 *   - Business type selector drives critical-room rules
 *   - Optional partner kundlis (up to 3) for stakeholder synergy
 *   - Optional muhurat (business start) chart for cycle-alignment note
 *   - Lifetime per-property unlock (no monthly quota)
 *
 * Branding: "Powered by Vedic Engine" — never reveal AI/LLM.
 */
import { Feather } from "@expo/vector-icons";
import * as Haptics from "expo-haptics";
import * as Linking from "expo-linking";
import * as WebBrowser from "expo-web-browser";
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
  TextInput,
  View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { useC } from "@/context/ThemeContext";
import { useUser } from "@/context/UserContext";
import { API_BASE } from "@/lib/apiConfig";
import { openReportPdfWithLanguageChoice } from "@/lib/pdfLanguagePicker";
import { AstroVastuWallet } from "@/components/AstroVastuWallet";
import { RoomPhoto, RoomPhotoCapture } from "@/components/RoomPhotoCapture";
import { ScanBasisBadge, VisionRoomFindings } from "@/components/ScanBasisBadge";
import { SmartScanUpload, SmartScanUploadValue } from "@/components/SmartScanUpload";

// ─────────────────────────────────────────────────────────────────────────
// Static option lists per business type (mirrors backend BUSINESS_CRITICAL)
// ─────────────────────────────────────────────────────────────────────────
type BizType = "shop" | "office" | "factory";

const BIZ_OPTIONS: { key: BizType; en: string; hi: string; icon: keyof typeof Feather.glyphMap; price: number; sku: string }[] = [
  { key: "shop",    en: "Shop",    hi: "Dukaan",   icon: "shopping-bag", price: 999,  sku: "shop_999"    },
  { key: "office",  en: "Office",  hi: "Office",   icon: "briefcase",    price: 1499, sku: "office_1499" },
  { key: "factory", en: "Factory", hi: "Karkhana", icon: "tool",         price: 2999, sku: "factory_2999"},
];

const ROOM_BY_BIZ: Record<BizType, { key: string; en: string; hi: string; icon: keyof typeof Feather.glyphMap; critical?: boolean }[]> = {
  shop: [
    { key: "entrance",       en: "Entrance",       hi: "Pravesh",       icon: "log-in",       critical: true },
    { key: "owner_seat",     en: "Owner Seat",     hi: "Swami Sthaan",  icon: "user",         critical: true },
    { key: "cash_counter",   en: "Cash Counter",   hi: "Golak",         icon: "dollar-sign",  critical: true },
    { key: "vault",          en: "Vault",          hi: "Tijori",        icon: "lock",         critical: true },
    { key: "stock_storage",  en: "Stock Storage",  hi: "Bhandaar",      icon: "package" },
    { key: "display",        en: "Display Area",   hi: "Pradarshan",    icon: "grid" },
    { key: "toilet",         en: "Toilet",         hi: "Shauchalaya",   icon: "alert-circle" },
  ],
  office: [
    { key: "entrance",     en: "Entrance",     hi: "Pravesh",      icon: "log-in",      critical: true },
    { key: "owner_cabin",  en: "Owner Cabin",  hi: "Swami Cabin",  icon: "user",        critical: true },
    { key: "owner_seat",   en: "Owner Seat",   hi: "Swami Aasan",  icon: "user-check",  critical: true },
    { key: "reception",    en: "Reception",    hi: "Swagat",       icon: "smile",       critical: true },
    { key: "conference",   en: "Conference",   hi: "Sammelan",     icon: "users" },
    { key: "accounts",     en: "Accounts",     hi: "Lekha",        icon: "book",        critical: true },
    { key: "vault",        en: "Vault",        hi: "Tijori",       icon: "lock",        critical: true },
    { key: "server_room",  en: "Server Room",  hi: "Server",       icon: "server" },
    { key: "pantry",       en: "Pantry",       hi: "Pantry",       icon: "coffee" },
    { key: "toilet",       en: "Toilet",       hi: "Shauchalaya",  icon: "alert-circle" },
  ],
  factory: [
    { key: "entrance",        en: "Entrance",        hi: "Pravesh",      icon: "log-in",      critical: true },
    { key: "owner_cabin",     en: "Owner Cabin",     hi: "Swami Cabin",  icon: "user",        critical: true },
    { key: "owner_seat",      en: "Owner Seat",      hi: "Swami Aasan",  icon: "user-check",  critical: true },
    { key: "machinery",       en: "Machinery",       hi: "Yantra",       icon: "settings",    critical: true },
    { key: "heavy_machine",   en: "Heavy Machine",   hi: "Bhari Yantra", icon: "cpu",         critical: true },
    { key: "raw_storage",     en: "Raw Storage",     hi: "Kachcha Maal", icon: "box" },
    { key: "finished_goods",  en: "Finished Goods",  hi: "Tayar Maal",   icon: "package" },
    { key: "boiler",          en: "Boiler",          hi: "Boiler",       icon: "thermometer", critical: true },
    { key: "labour_quarter",  en: "Labour Quarter",  hi: "Shramik",      icon: "users" },
    { key: "toilet",          en: "Toilet",          hi: "Shauchalaya",  icon: "alert-circle" },
  ],
};

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
type FloorRoom = { room_type: string; direction: string };

type RoomReport = {
  room_type: string; direction: string; verdict: string; severity: string;
  severity_label?: string; score: number; is_critical: boolean;
  zone?: { planet?: string; deity?: string; element?: string };
  mahadasha?: { applies: boolean; kind?: string; reason_en?: string; reason_hi?: string };
  business_rule?: { applies: boolean; kind?: string; reason_en?: string; reason_hi?: string };
};
type PriorityAction = {
  room_type: string; direction: string; verdict: string;
  severity_label: string; is_critical: boolean;
  why_en: string; why_hi: string;
};
type BizResponse = {
  meta:    { powered_by: string; tier: string; rooms_count: number };
  overall: {
    score: number; grade: string;
    summary: { en: string; hi: string };
    counts:  { ideal: number; acceptable: number; adjustment_needed: number; avoid: number };
  };
  business_summary: { type: BizType; intro: { en: string; hi: string } };
  mahadasha_alert?: {
    active_lord: string; lord_direction: string;
    conflict_rooms: string[]; favourable_rooms: string[];
    summary_en: string; summary_hi: string;
  } | null;
  stakeholder?: { partner_count: number; common_favour: string[]; common_conflict: string[]; summary_en: string; summary_hi: string };
  muhurat?:     { applies: boolean; alignment?: string; summary_en?: string; summary_hi?: string } | null;
  rooms: RoomReport[];
  priority_actions: PriorityAction[];
  classical_summary: string[];
  footer: { en: string; hi: string };
  unlock?: { via: string; property_name?: string | null };
  pdf_url?: string;
  pdf_token?: string;
  report_id?: number;
  vision_room_findings?: VisionRoomFindings;
};

type ErrorPayload = {
  error: string; message?: string;
  required_sku?: string; upgrade_required?: boolean; missing_fields?: string[];
};

// ─────────────────────────────────────────────────────────────────────────
export default function BusinessVastuScreen() {
  const C = useC();
  const insets = useSafeAreaInsets();
  const { user } = useUser();

  const [bizType,   setBizType]   = useState<BizType>("shop");
  const [rooms,     setRooms]     = useState<FloorRoom[]>([
    { room_type: "entrance", direction: "" },
    { room_type: "owner_seat", direction: "" },
  ]);
  const [editIdx,   setEditIdx]   = useState<number | null>(null);
  const [propertyName, setPropertyName] = useState("");
  const [loading,   setLoading]   = useState(false);
  const [result,    setResult]    = useState<BizResponse | null>(null);
  const [error,     setError]     = useState<ErrorPayload | null>(null);
  const [walletKey, setWalletKey] = useState(0);
  const [scanUpload, setScanUpload] = useState<SmartScanUploadValue | null>(null);
  const [roomPhotos, setRoomPhotos] = useState<RoomPhoto[]>([]);

  const roomOpts = ROOM_BY_BIZ[bizType];

  const onChangeBizType = useCallback((b: BizType) => {
    Haptics.selectionAsync();
    setBizType(b);
    // Reset rooms with the first two critical rooms of the new business type
    const crits = ROOM_BY_BIZ[b].filter(r => r.critical).slice(0, 2);
    setRooms(crits.map(r => ({ room_type: r.key, direction: "" })));
    // Clear any room photos — they were tied to the previous business type's room set
    setRoomPhotos([]);
    setResult(null); setError(null);
  }, []);

  const addRoom = useCallback(() => {
    if (rooms.length >= 15) return;
    Haptics.selectionAsync();
    setRooms((rs) => [...rs, { room_type: roomOpts[0].key, direction: "" }]);
  }, [rooms.length, roomOpts]);

  const removeRoom = useCallback((idx: number) => {
    Haptics.selectionAsync();
    setRooms((rs) => rs.filter((_, i) => i !== idx));
  }, []);

  const updateRoom = useCallback((idx: number, patch: Partial<FloorRoom>) => {
    setRooms((rs) => rs.map((r, i) => (i === idx ? { ...r, ...patch } : r)));
  }, []);

  const onSubmit = useCallback(async () => {
    if (loading) return;
    if (!user?.id || !user?.api_key) {
      setError({ error: "auth_required", message: "Please log in to run a Business Vastu scan." });
      return;
    }
    const valid = rooms.filter(r => r.room_type && r.direction);
    if (valid.length === 0 && !scanUpload) {
      setError({ error: "validation", message: "Add at least one room with a direction, or upload a floor plan." });
      return;
    }
    if (!propertyName.trim()) {
      setError({ error: "validation",
                 message: "Naam your premise (e.g. 'Andheri Shop') — needed to match your unlock." });
      return;
    }

    setError(null); setResult(null); setLoading(true);
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);

    try {
      const resp = await fetch(`${API_BASE}/api/business-vastu`, {
        method:  "POST",
        headers: { "Content-Type": "application/json", "X-API-Key": user.api_key },
        body:    JSON.stringify({
          user_id:       user.id,
          business_type: bizType,
          floor_plan:    valid,
          property_name: propertyName.trim(),
          ...(scanUpload ? { floor_plan_upload: {
              type:     scanUpload.type,
              ...(scanUpload.data_url ? { data_url: scanUpload.data_url } : {}),
              ...(scanUpload.base64   ? { base64:   scanUpload.base64   } : {}),
              ...(scanUpload.north_at ? { north_at: scanUpload.north_at } : {}),
            } } : {}),
          ...(roomPhotos.length > 0
            ? { room_photos: roomPhotos.map(p => ({
                  room_type:      p.room_type,
                  image_data_url: p.image_data_url,
                  ...(typeof p.heading_deg === "number" ? { heading_deg: p.heading_deg } : {}),
                })) }
            : {}),
        }),
      });
      const body = await resp.json();
      if (!resp.ok) {
        setError({ ...(body as ErrorPayload), error: body.error || `HTTP ${resp.status}` });
        Haptics.notificationAsync(Haptics.NotificationFeedbackType.Warning);
      } else {
        setResult(body as BizResponse);
        setWalletKey(k => k + 1);
        Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      }
    } catch (e: any) {
      setError({ error: "network", message: String(e?.message || e) });
    } finally {
      setLoading(false);
    }
  }, [loading, rooms, user, bizType, propertyName, scanUpload, roomPhotos]);

  const bizMeta = BIZ_OPTIONS.find(b => b.key === bizType)!;

  // ─────────────────────────────────────────────────────────────────────
  return (
    <View style={{ flex: 1, backgroundColor: C.bg, paddingTop: insets.top }}>
      <Stack.Screen options={{ headerShown: false }} />
      <LinearGradient colors={[C.bg, C.bgCard]} style={[styles.header, { paddingTop: 4 }]}>
        <Pressable onPress={() => router.back()} hitSlop={10} style={{ padding: 6 }}>
          <Feather name="arrow-left" size={22} color={C.text} />
        </Pressable>
        <Text style={[styles.headerTitle, { color: C.text }]}>Business Vastu</Text>
        <View style={{ width: 28 }} />
      </LinearGradient>

      <ScrollView
        contentContainerStyle={{ padding: 16, paddingBottom: insets.bottom + 40 }}
        keyboardShouldPersistTaps="handled"
      >
        {/* ── Intro card ──────────────────────────────────────────────── */}
        <View style={[styles.card, { backgroundColor: C.bgCard, borderColor: C.border }]}>
          <View style={{ flexDirection: "row", alignItems: "center", gap: 8, marginBottom: 6 }}>
            <Feather name="briefcase" size={18} color={C.accent} />
            <Text style={[styles.cardTitle, { color: C.text }]}>Premium Business Vastu</Text>
          </View>
          <Text style={[styles.bodyText, { color: C.textMid }]}>
            Combine your premise layout with the owner Kundli + active Mahadasha to
            get a personalised, lifetime priority plan.
          </Text>
          <Text style={[styles.bodyTextSmall, { color: C.textMid, marginTop: 6 }]}>
            Aapke vyapar sthal ko swami ki Kundli aur chal rahi Mahadasha ke saath
            milakar ek vyaktigat sudhar yojana banayi jaati hai.
          </Text>
        </View>

        {/* ── Business type selector ─────────────────────────────────── */}
        <Text style={[styles.sectionTitle, { color: C.text, marginTop: 4 }]}>
          Business Type
        </Text>
        <View style={styles.bizRow}>
          {BIZ_OPTIONS.map((b) => {
            const sel = b.key === bizType;
            return (
              <Pressable
                key={b.key}
                onPress={() => onChangeBizType(b.key)}
                style={[styles.bizCard, {
                  borderColor: sel ? C.accent : C.border,
                  backgroundColor: sel ? C.accentBg : C.bgCard,
                }]}
              >
                <Feather name={b.icon} size={22} color={sel ? C.accent : C.textMid} />
                <Text style={{ color: sel ? C.accent : C.text, fontWeight: "800", marginTop: 4 }}>
                  {b.en}
                </Text>
                <Text style={{ color: sel ? C.accent : C.textMid, fontSize: 11 }}>
                  {b.hi}
                </Text>
                <Text style={{ color: sel ? C.accent : C.textMid, fontSize: 11, marginTop: 2, fontWeight: "700" }}>
                  ₹{b.price}
                </Text>
              </Pressable>
            );
          })}
        </View>

        {/* ── Premise name ───────────────────────────────────────────── */}
        <Text style={[styles.sectionTitle, { color: C.text, marginTop: 14 }]}>
          Premise Name
        </Text>
        <TextInput
          value={propertyName}
          onChangeText={setPropertyName}
          placeholder="e.g. Andheri Shop, Powai HQ"
          placeholderTextColor={C.textMid}
          style={[styles.input, { color: C.text, borderColor: C.border, backgroundColor: C.bgCard }]}
        />
        <Text style={{ color: C.textMid, fontSize: 11, marginTop: 4 }}>
          Required — your one-time unlock is matched to this premise name.
        </Text>

        {/* ── Wallet (Phase 2 unlocks) ───────────────────────────────── */}
        <AstroVastuWallet
          variant="pro"
          propertyName={propertyName}
          onPropertyNameChange={setPropertyName}
          refreshKey={walletKey}
        />

        {/* ── Smart Scan upload — full premise PDF/image (vision auto-detects) ── */}
        <View style={{ marginTop: 14 }}>
          <SmartScanUpload value={scanUpload} onChange={setScanUpload} disabled={loading} />
        </View>

        {/* ── Optional: room photos with magnetometer (sensor-confirmed accuracy) ── */}
        <RoomPhotoCapture
          rooms={
            // Use the user's listed rooms (whichever have a room_type filled in) —
            // de-duped so each room appears once with its business-type label.
            Array.from(
              new Map(
                rooms
                  .filter(r => r.room_type)
                  .map(r => {
                    const meta = roomOpts.find(o => o.key === r.room_type);
                    return [r.room_type, { key: r.room_type, label: meta?.en || r.room_type }];
                  })
              ).values()
            )
          }
          photos={roomPhotos}
          onChange={setRoomPhotos}
          disabled={loading}
          maxPhotos={6}
        />

        {/* ── Floor-plan editor ──────────────────────────────────────── */}
        <Text style={[styles.sectionTitle, { color: C.text, marginTop: 4 }]}>
          {scanUpload ? "Optional: Refine Rooms" : `Premise Layout (${rooms.length}/15)`}
        </Text>
        {scanUpload ? (
          <Text style={{ color: C.textMid, fontSize: 11, marginBottom: 6 }}>
            Photo Engine will detect rooms from your upload. You can also list rooms here to override.
          </Text>
        ) : null}

        {rooms.map((r, idx) => {
          const ro = roomOpts.find(x => x.key === r.room_type) ?? roomOpts[0];
          const di = DIRECTION_OPTIONS.find(x => x.key === r.direction);
          const isEditing = editIdx === idx;
          return (
            <View key={idx} style={[styles.roomRow, { backgroundColor: C.bgCard, borderColor: C.border }]}>
              <View style={{ flex: 1 }}>
                <ScrollView horizontal showsHorizontalScrollIndicator={false}
                            contentContainerStyle={{ gap: 6, paddingVertical: 2 }}>
                  {roomOpts.map((opt) => {
                    const sel = opt.key === r.room_type;
                    return (
                      <Pressable key={opt.key}
                                 onPress={() => { Haptics.selectionAsync(); updateRoom(idx, { room_type: opt.key }); }}
                                 style={[styles.roomChip, {
                                   borderColor: sel ? C.accent : (opt.critical ? VERDICT_COLOR.Avoid.border : C.border),
                                   backgroundColor: sel ? C.accentBg : "transparent",
                                 }]}>
                        <Feather name={opt.icon} size={12} color={sel ? C.accent : (opt.critical ? VERDICT_COLOR.Avoid.fg : C.textMid)} />
                        <Text style={{ color: sel ? C.accent : (opt.critical ? VERDICT_COLOR.Avoid.fg : C.textMid),
                                       fontSize: 11, fontWeight: "600" }}>
                          {opt.en}{opt.critical ? " ★" : ""}
                        </Text>
                      </Pressable>
                    );
                  })}
                </ScrollView>

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

        <Pressable onPress={addRoom} disabled={rooms.length >= 15}
                   style={[styles.addBtn, { borderColor: C.border, opacity: rooms.length >= 15 ? 0.5 : 1 }]}>
          <Feather name="plus" size={16} color={C.accent} />
          <Text style={{ color: C.accent, fontWeight: "700" }}>Add Room (★ = critical)</Text>
        </Pressable>

        {/* ── Submit ─────────────────────────────────────────────────── */}
        <Pressable onPress={onSubmit} disabled={loading}
                   style={[styles.submitBtn, { backgroundColor: C.accent, opacity: loading ? 0.7 : 1 }]}>
          {loading ? <ActivityIndicator color="#fff" />
                   : <Text style={styles.submitText}>Run {bizMeta.en} Vastu Scan</Text>}
        </Pressable>

        {/* ── Error / 402 paywall card ───────────────────────────────── */}
        {error && (
          <View style={[styles.errCard, {
            backgroundColor: C.bgCard, borderColor: VERDICT_COLOR.Avoid.border,
          }]}>
            <Feather name="alert-triangle" size={18} color={VERDICT_COLOR.Avoid.fg} style={{ marginTop: 2 }} />
            <View style={{ flex: 1 }}>
              <Text style={[styles.errTitle, { color: C.text }]}>
                {error.error === "upgrade_required"   ? "Unlock Required"      :
                 error.error === "profile_incomplete" ? "Complete your profile" :
                 error.error === "validation"         ? "Check your inputs"     :
                 "Scan failed"}
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
              {(error.upgrade_required || error.error === "upgrade_required") && (
                <Text style={{ color: C.textMid, fontSize: 12, marginTop: 8 }}>
                  Use the wallet above to unlock {bizMeta.en} Vastu (₹{bizMeta.price}, lifetime).
                </Text>
              )}
            </View>
          </View>
        )}

        {/* ── PDF-only result for paid Business tiers ─────────────────── */}
        {result && result.pdf_url && result.pdf_token && (() => {
          const o     = result.overall || ({} as BizResponse["overall"]);
          const grade = o.grade || "C";
          const score = typeof o.score === "number" ? o.score : 0;
          const sm    = o.summary || { en: "", hi: "" };
          const pdfFullUrl =
            `${API_BASE}${result.pdf_url}?t=${encodeURIComponent(result.pdf_token)}`;
          const openPdf = () => {
            Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
            openReportPdfWithLanguageChoice(pdfFullUrl);
          };
          return (
            <View style={{ marginTop: 18 }}>
              <View style={[styles.scoreCard, { backgroundColor: C.bgCard, borderColor: C.border }]}>
                <View style={{ flex: 1 }}>
                  <Text style={[styles.sectionLabel, { color: C.textMid }]}>OVERALL PREMISE SCORE</Text>
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
                  {sm.en ? (
                    <Text style={{ color: C.text, fontSize: 13, marginTop: 6 }}>{sm.en}</Text>
                  ) : null}
                  <ScanBasisBadge
                    visionRoomFindings={result.vision_room_findings}
                    visionUsed={(result as any).vision_used}
                    visionFindingsCount={(result as any).vision_findings_count}
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
                  Aapka full Business Vastu report PDF me ready hai — room-by-room verdict,
                  Mahadasha alert, stakeholder synergy, priority actions sab kuch.
                </Text>
                <Text style={{ color: C.textMid, fontSize: 12, marginBottom: 12 }}>
                  Your full Business Vastu report is available as a PDF — open, save, or share it.
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
                {result.footer?.en || "Powered by Vedic Engine"}
              </Text>
            </View>
          );
        })()}

        {/* ── Legacy on-screen result (only when no pdf_url, e.g. legacy logs) */}
        {result && !result.pdf_url && (() => {
          const o   = result.overall   || ({} as BizResponse["overall"]);
          const cts = o.counts         || { ideal: 0, acceptable: 0, adjustment_needed: 0, avoid: 0 };
          const sm  = o.summary        || { en: "", hi: "" };
          const grade = o.grade || "C";
          const score = typeof o.score === "number" ? o.score : 0;
          const rooms_= Array.isArray(result.rooms) ? result.rooms : [];
          const prio  = Array.isArray(result.priority_actions) ? result.priority_actions : [];
          const refs  = Array.isArray(result.classical_summary) ? result.classical_summary : [];
          const md    = result.mahadasha_alert || null;
          const stk   = result.stakeholder || null;
          const mh    = result.muhurat || null;
          const intro = result.business_summary?.intro || { en: "", hi: "" };
          return (
          <View style={{ marginTop: 18 }}>
            {/* Overall score */}
            <View style={[styles.scoreCard, { backgroundColor: C.bgCard, borderColor: C.border }]}>
              <View style={{ flex: 1 }}>
                <Text style={[styles.sectionLabel, { color: C.textMid }]}>OVERALL PREMISE SCORE</Text>
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
                <Text style={{ color: C.text, fontSize: 13, marginTop: 6 }}>{sm.en}</Text>
                <Text style={{ color: C.textMid, fontSize: 12, marginTop: 2 }}>{sm.hi}</Text>
                <ScanBasisBadge
                  visionRoomFindings={result.vision_room_findings}
                  visionUsed={(result as any).vision_used}
                  visionFindingsCount={(result as any).vision_findings_count}
                  perRoomBasis={(result.rooms || []).map((rr: any) => ({
                    room_type: rr.room_type, direction_basis: rr.direction_basis,
                  }))}
                />
              </View>
            </View>

            {/* Counts */}
            <View style={styles.countsRow}>
              {([
                ["Ideal",      cts.ideal,             VERDICT_COLOR.Ideal],
                ["Acceptable", cts.acceptable,        VERDICT_COLOR.Acceptable],
                ["Adjust",     cts.adjustment_needed, VERDICT_COLOR["Adjustment Needed"]],
                ["Avoid",      cts.avoid,             VERDICT_COLOR.Avoid],
              ] as const).map(([label, count, col]) => (
                <View key={label} style={[styles.countPill, { backgroundColor: col.bg, borderColor: col.border }]}>
                  <Text style={{ color: col.fg, fontWeight: "800", fontSize: 16 }}>{count}</Text>
                  <Text style={{ color: col.fg, fontSize: 10, fontWeight: "600" }}>{label}</Text>
                </View>
              ))}
            </View>

            {/* Business intro */}
            {intro.en ? (
              <View style={[styles.card, { backgroundColor: C.bgCard, borderColor: C.border, marginTop: 10 }]}>
                <Text style={{ color: C.text, fontSize: 13 }}>{intro.en}</Text>
                <Text style={{ color: C.textMid, fontSize: 12, marginTop: 4 }}>{intro.hi}</Text>
              </View>
            ) : null}

            {/* Mahadasha alert */}
            {md && (
              <View style={[styles.mdAlert, {
                backgroundColor: C.bgCard, borderColor: VERDICT_COLOR["Adjustment Needed"].border,
              }]}>
                <View style={{ flexDirection: "row", alignItems: "center", gap: 6, marginBottom: 6 }}>
                  <Feather name="zap" size={16} color={VERDICT_COLOR["Adjustment Needed"].fg} />
                  <Text style={[styles.cardTitle, { color: C.text }]}>
                    Owner Mahadasha · {md.active_lord} ({md.lord_direction})
                  </Text>
                </View>
                <Text style={{ color: C.text, fontSize: 12 }}>{md.summary_en}</Text>
                <Text style={{ color: C.textMid, fontSize: 11, marginTop: 2 }}>{md.summary_hi}</Text>
              </View>
            )}

            {/* Stakeholder synergy */}
            {stk && stk.partner_count > 0 && (
              <View style={[styles.mdAlert, {
                backgroundColor: C.bgCard, borderColor: VERDICT_COLOR.Acceptable.border,
              }]}>
                <View style={{ flexDirection: "row", alignItems: "center", gap: 6, marginBottom: 6 }}>
                  <Feather name="users" size={16} color={VERDICT_COLOR.Acceptable.fg} />
                  <Text style={[styles.cardTitle, { color: C.text }]}>Stakeholder Synergy</Text>
                </View>
                <Text style={{ color: C.text, fontSize: 12 }}>{stk.summary_en}</Text>
                <Text style={{ color: C.textMid, fontSize: 11, marginTop: 2 }}>{stk.summary_hi}</Text>
              </View>
            )}

            {/* Muhurat alignment */}
            {mh?.applies && (
              <View style={[styles.mdAlert, {
                backgroundColor: C.bgCard,
                borderColor: mh.alignment === "stressed" ? VERDICT_COLOR.Avoid.border
                            : mh.alignment === "aligned" ? VERDICT_COLOR.Ideal.border
                            : C.border,
              }]}>
                <View style={{ flexDirection: "row", alignItems: "center", gap: 6, marginBottom: 6 }}>
                  <Feather name="calendar" size={16} color={C.accent} />
                  <Text style={[styles.cardTitle, { color: C.text }]}>
                    Muhurat Alignment · {(mh.alignment || "").toUpperCase()}
                  </Text>
                </View>
                <Text style={{ color: C.text, fontSize: 12 }}>{mh.summary_en}</Text>
                <Text style={{ color: C.textMid, fontSize: 11, marginTop: 2 }}>{mh.summary_hi}</Text>
              </View>
            )}

            {/* Priority actions */}
            {prio.length > 0 && (
              <View style={{ marginTop: 14 }}>
                <Text style={[styles.sectionTitle, { color: C.text }]}>Priority Actions</Text>
                {prio.map((p, i) => {
                  const col = VERDICT_COLOR[p.verdict] || VERDICT_COLOR["Adjustment Needed"];
                  return (
                    <View key={i} style={[styles.priorityRow, { backgroundColor: C.bgCard, borderColor: col.border }]}>
                      <View style={{ flexDirection: "row", alignItems: "center", gap: 6, marginBottom: 4 }}>
                        <Text style={{ color: col.fg, fontWeight: "800" }}>{i + 1}.</Text>
                        <Text style={{ color: C.text, fontWeight: "700", textTransform: "capitalize" }}>
                          {p.room_type.replace(/_/g, " ")} · {p.direction}
                        </Text>
                        {p.is_critical && (
                          <Text style={{ color: VERDICT_COLOR.Avoid.fg, fontSize: 10, fontWeight: "800" }}>★ CRITICAL</Text>
                        )}
                      </View>
                      <Text style={{ color: C.text, fontSize: 12 }}>{p.why_en}</Text>
                      <Text style={{ color: C.textMid, fontSize: 11, marginTop: 2 }}>{p.why_hi}</Text>
                    </View>
                  );
                })}
              </View>
            )}

            {/* Per-room details */}
            <Text style={[styles.sectionTitle, { color: C.text, marginTop: 14 }]}>Room-by-room</Text>
            {rooms_.map((r, i) => {
              const col = VERDICT_COLOR[r.verdict] || VERDICT_COLOR.Acceptable;
              return (
                <View key={i} style={[styles.roomReport, { backgroundColor: C.bgCard, borderColor: col.border }]}>
                  <View style={{ flexDirection: "row", alignItems: "center", gap: 6 }}>
                    <Text style={{ color: C.text, fontWeight: "700", textTransform: "capitalize" }}>
                      {r.room_type.replace(/_/g, " ")} · {r.direction}
                    </Text>
                    <View style={{ paddingHorizontal: 6, paddingVertical: 2, borderRadius: 4, backgroundColor: col.bg }}>
                      <Text style={{ color: col.fg, fontSize: 10, fontWeight: "800" }}>{r.verdict}</Text>
                    </View>
                    {r.is_critical && (
                      <Text style={{ color: VERDICT_COLOR.Avoid.fg, fontSize: 10, fontWeight: "800" }}>★</Text>
                    )}
                  </View>
                  {r.zone?.deity && (
                    <Text style={{ color: C.textMid, fontSize: 11, marginTop: 4 }}>
                      Zone: {r.zone.planet} · {r.zone.deity} · {r.zone.element}
                    </Text>
                  )}
                  {r.business_rule?.applies && r.business_rule.reason_en && (
                    <Text style={{ color: C.text, fontSize: 12, marginTop: 4 }}>
                      • {r.business_rule.reason_en}
                    </Text>
                  )}
                  {r.mahadasha?.applies && r.mahadasha.reason_en && (
                    <Text style={{ color: C.text, fontSize: 12, marginTop: 2 }}>
                      • {r.mahadasha.reason_en}
                    </Text>
                  )}
                </View>
              );
            })}

            {/* Classical refs */}
            {refs.length > 0 && (
              <View style={[styles.card, { backgroundColor: C.bgCard, borderColor: C.border, marginTop: 12 }]}>
                <Text style={[styles.sectionLabel, { color: C.textMid, marginBottom: 4 }]}>CLASSICAL REFERENCES</Text>
                {refs.map((r, i) => (
                  <Text key={i} style={{ color: C.text, fontSize: 11 }}>• {r}</Text>
                ))}
              </View>
            )}

            {/* Footer */}
            <Text style={{ color: C.textMid, fontSize: 11, marginTop: 14, textAlign: "center" }}>
              {result.footer?.en || "Powered by Vedic Engine"}
            </Text>
          </View>
          );
        })()}
      </ScrollView>
    </View>
  );
}

// ─────────────────────────────────────────────────────────────────────────
const styles = StyleSheet.create({
  header: {
    flexDirection: "row", alignItems: "center", justifyContent: "space-between",
    paddingHorizontal: 14, paddingVertical: 10,
  },
  headerTitle:   { fontSize: 17, fontWeight: "800" },
  card:          { borderRadius: 14, padding: 14, borderWidth: 1, marginBottom: 12 },
  cardTitle:     { fontSize: 14, fontWeight: "700" },
  bodyText:      { fontSize: 13 },
  bodyTextSmall: { fontSize: 12 },
  sectionTitle:  { fontSize: 13, fontWeight: "800", marginBottom: 8, marginTop: 4, letterSpacing: 0.4 },
  sectionLabel:  { fontSize: 10, fontWeight: "800", letterSpacing: 1 },
  bizRow:        { flexDirection: "row", gap: 8 },
  bizCard:       { flex: 1, borderWidth: 1, borderRadius: 12, paddingVertical: 12, alignItems: "center" },
  input:         { borderWidth: 1, borderRadius: 10, paddingHorizontal: 12, paddingVertical: 10, fontSize: 14, marginTop: 4 },
  roomRow:       { flexDirection: "row", alignItems: "flex-start", gap: 6, padding: 10, borderRadius: 12, borderWidth: 1, marginBottom: 8 },
  roomChip:      { flexDirection: "row", alignItems: "center", gap: 4, paddingHorizontal: 8, paddingVertical: 4, borderRadius: 12, borderWidth: 1 },
  dirSummary:    { flexDirection: "row", alignItems: "center", gap: 8, paddingVertical: 6, paddingHorizontal: 8, borderRadius: 8, borderWidth: 1, marginTop: 6 },
  dirGrid:       { flexDirection: "row", flexWrap: "wrap", gap: 6, marginTop: 6 },
  dirChip:       { paddingHorizontal: 10, paddingVertical: 6, borderRadius: 10, borderWidth: 1, alignItems: "center", minWidth: 56 },
  addBtn:        { flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 6, paddingVertical: 10, borderRadius: 10, borderWidth: 1, borderStyle: "dashed", marginTop: 4 },
  submitBtn:     { paddingVertical: 14, borderRadius: 12, alignItems: "center", marginTop: 14 },
  submitText:    { color: "#fff", fontWeight: "800", fontSize: 15 },
  errCard:       { flexDirection: "row", gap: 10, padding: 12, borderRadius: 12, borderWidth: 1, marginTop: 14 },
  errTitle:      { fontSize: 14, fontWeight: "800" },
  errBody:       { fontSize: 12 },
  upgradeBtn:    { paddingVertical: 10, paddingHorizontal: 14, borderRadius: 10, alignItems: "center" },
  upgradeText:   { color: "#fff", fontWeight: "800" },
  scoreCard:     { padding: 14, borderRadius: 14, borderWidth: 1, flexDirection: "row" },
  scoreNum:      { fontSize: 36, fontWeight: "900" },
  countsRow:     { flexDirection: "row", gap: 8, marginTop: 10 },
  countPill:     { flex: 1, paddingVertical: 8, borderRadius: 10, borderWidth: 1, alignItems: "center" },
  mdAlert:       { padding: 12, borderRadius: 12, borderWidth: 1, marginTop: 10 },
  priorityRow:   { padding: 10, borderRadius: 10, borderWidth: 1, marginTop: 6 },
  roomReport:    { padding: 10, borderRadius: 10, borderWidth: 1, marginTop: 6 },
});
