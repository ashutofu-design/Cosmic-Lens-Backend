/**
 * AstroVastu PRO — Single-tap Smart Scan
 *
 * Minimal flow:
 *   1. User taps "Smart Scan — Open Camera".
 *   2. Live camera with compass overlay opens.
 *   3. Shutter captures a photo + magnetometer heading.
 *   4. We POST the photo as floor_plan_upload; Photo Engine detects rooms
 *      and runs the kundli-aware deep scan.
 *   5. Result + PDF link rendered on the same screen.
 *
 * No AI/LLM branding — surfaces "Photo Engine" only.
 */
import { Feather } from "@expo/vector-icons";
import * as DocumentPicker from "expo-document-picker";
import * as Haptics from "expo-haptics";
import * as Linking from "expo-linking";
import * as WebBrowser from "expo-web-browser";
import { LinearGradient } from "expo-linear-gradient";
import { router, Stack, useFocusEffect } from "expo-router";
import React, { useCallback, useEffect, useRef, useState } from "react";
import {
  Alert,
  ActivityIndicator,
  Animated,
  Easing,
  I18nManager,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { VastuDeliveryOptions } from "@/components/VastuDeliveryOptions";
import { FadeInView, staggerDelay } from "@/components/motion/FadeInView";

import { useC } from "@/context/ThemeContext";
import { useUser } from "@/context/UserContext";
import { useT } from "@/hooks/useT";
import { API_BASE } from "@/lib/apiConfig";
import { openReportPdfWithLanguageChoice } from "@/lib/pdfLanguagePicker";
import { GalleryScanResult, GalleryScanUpload } from "@/components/GalleryScanUpload";
import { OrderSuccessModal } from "@/components/OrderSuccessModal";
import { ScanBasisBadge, VisionRoomFindings } from "@/components/ScanBasisBadge";
import { SmartScanCamera, SmartScanResult } from "@/components/SmartScanCamera";
import { SmartScanUploadValue, NorthAt } from "@/components/SmartScanUpload";
import { submitAstrovastuRoomHumanOrder } from "@/lib/astrovastuHumanOrder";
import { purchaseFloorPlanSku } from "@/lib/astrovastuFloorPlanPurchase";
import { FLOOR_PLAN_CATALOG } from "@/lib/astrovastuFloorPlanPricing";
import { startAstrovastuRoomUploadCheckout } from "@/lib/astrovastuRoomUploadCheckout";
import { ROOM_EXPERT_UPLOAD_PRICE_INR } from "@/lib/astrovastuRoomUploadPricing";
import { REPORT_PRIORITY_FEE_INR } from "@/lib/deliverySla";
import {
  consumeAstrovastuRoomPaidReady,
  getPendingAstrovastuRoomUpload,
} from "@/lib/pendingAstrovastuRoomUpload";
import {
  clearPendingAstrovastuFloorPlan,
  consumeAstrovastuFloorPaidReady,
  getPendingAstrovastuFloorPlan,
  setPendingAstrovastuFloorPlan,
} from "@/lib/pendingAstrovastuFloorPlan";

// ─────────────────────────────────────────────────────────────────────────
// Rooms a user can pick before opening the live camera (PRO residential).
const CAMERA_ROOMS: { key: string; label: string; icon: keyof typeof Feather.glyphMap }[] = [
  { key: "bedroom",  label: "Bedroom",   icon: "moon"        },
  { key: "kitchen",  label: "Kitchen",   icon: "coffee"      },
  { key: "pooja",    label: "Pooja",     icon: "sun"         },
  { key: "living",   label: "Living",    icon: "tv"          },
  { key: "bathroom", label: "Bathroom",  icon: "droplet"     },
  { key: "entrance", label: "Entrance",  icon: "log-in"      },
  { key: "study",    label: "Study",     icon: "book-open"   },
  { key: "store",    label: "Store",     icon: "package"     },
];

// Compass heading (deg) → 8-dir code
function headingToDirCode(h: number): string {
  const a = ((h % 360) + 360) % 360;
  if (a >= 337.5 || a <  22.5) return "N";
  if (a >=  22.5 && a <  67.5) return "NE";
  if (a >=  67.5 && a < 112.5) return "E";
  if (a >= 112.5 && a < 157.5) return "SE";
  if (a >= 157.5 && a < 202.5) return "S";
  if (a >= 202.5 && a < 247.5) return "SW";
  if (a >= 247.5 && a < 292.5) return "W";
  return "NW";
}

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

const MAX_HOME_PLAN_BYTES = 10 * 1024 * 1024;
const HOME_PDF_PRICE = FLOOR_PLAN_CATALOG.home_floor_799.price;
const HOME_ACCENT = "#a78bfa";
const BIZ_TAB_ACCENT = "#06b6d4";

function PremiumOrb({ color }: { color: string }) {
  const pulse = useRef(new Animated.Value(0)).current;
  useEffect(() => {
    const loop = Animated.loop(
      Animated.sequence([
        Animated.timing(pulse, { toValue: 1, duration: 2400, easing: Easing.inOut(Easing.ease), useNativeDriver: true }),
        Animated.timing(pulse, { toValue: 0, duration: 2400, easing: Easing.inOut(Easing.ease), useNativeDriver: true }),
      ]),
    );
    loop.start();
    return () => loop.stop();
  }, [pulse]);
  const scale = pulse.interpolate({ inputRange: [0, 1], outputRange: [1, 1.15] });
  const opacity = pulse.interpolate({ inputRange: [0, 1], outputRange: [0.28, 0.55] });
  return (
    <Animated.View
      pointerEvents="none"
      style={[ui.orb, { backgroundColor: color, transform: [{ scale }], opacity }]}
    />
  );
}

function SectionShell({
  icon,
  title,
  subtitle,
  accent,
  children,
  delay = 0,
  resetKey,
}: {
  icon: keyof typeof Feather.glyphMap;
  title: string;
  subtitle?: string;
  accent: string;
  children: React.ReactNode;
  delay?: number;
  resetKey?: string;
}) {
  const C = useC();
  return (
    <FadeInView delay={delay} resetKey={resetKey} style={[ui.sectionShell, { borderColor: `${accent}33` }]}>
      <LinearGradient
        colors={[`${accent}14`, "transparent"]}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
        style={StyleSheet.absoluteFill}
        pointerEvents="none"
      />
      <View style={ui.sectionHead}>
        <View style={[ui.sectionIconWrap, { backgroundColor: `${accent}22`, borderColor: `${accent}55` }]}>
          <Feather name={icon} size={15} color={accent} />
        </View>
        <View style={{ flex: 1 }}>
          <Text style={[ui.sectionHeadTitle, { color: C.text }]}>{title}</Text>
          {subtitle ? <Text style={[ui.sectionHeadSub, { color: C.textMid }]}>{subtitle}</Text> : null}
        </View>
      </View>
      {children}
    </FadeInView>
  );
}

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
    summary_en: string; summary_hi: string; summary_loc?: string;
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
  const t = useT() as any;
  const avpRoom = (k: string) => t[`avp_room_${k}`] || k;

  const [loading, setLoading] = useState(false);
  const [result,  setResult]  = useState<ProResponse | null>(null);
  const [error,   setError]   = useState<ErrorPayload | null>(null);
  const [wholePlan, setWholePlan] = useState<SmartScanUploadValue | null>(null);
  const [mode, setMode] = useState<"camera" | "business">("camera");
  const [cameraRoom, setCameraRoom] = useState<string | null>(null);
  const [uploadSubmitting, setUploadSubmitting] = useState(false);
  const [uploadSuccessVisible, setUploadSuccessVisible] = useState(false);
  const [planPicking, setPlanPicking] = useState(false);
  const [priorityDelivery, setPriorityDelivery] = useState(false);

  const roomPayTotal = ROOM_EXPERT_UPLOAD_PRICE_INR + (priorityDelivery ? REPORT_PRIORITY_FEE_INR : 0);
  const homePdfTotal = HOME_PDF_PRICE + (priorityDelivery ? REPORT_PRIORITY_FEE_INR : 0);
  const paySubmitLabel = String(t.avp_uploadPaySubmit || "Pay ₹{amount}")
    .replace("{amount}", String(roomPayTotal));
  const homePdfLabel = `${t.avp_btnUploadHomePdf || "Upload Full Home PDF"} (₹${HOME_PDF_PRICE})`;
  const perRoomLabel = t.avp_uploadPricePerRoom || "per room";
  const cameraLabel = `${t.avp_btnSmartScan} (₹${ROOM_EXPERT_UPLOAD_PRICE_INR}/${perRoomLabel})`;
  const uploadRoomLabel = `${t.avp_btnUploadPhoto} (₹${ROOM_EXPERT_UPLOAD_PRICE_INR}/${perRoomLabel})`;
  const accent = mode === "camera" ? HOME_ACCENT : BIZ_TAB_ACCENT;
  const payPulse = useRef(new Animated.Value(0)).current;
  useEffect(() => {
    if (loading || !wholePlan) return;
    const loop = Animated.loop(
      Animated.sequence([
        Animated.timing(payPulse, { toValue: 1, duration: 1400, easing: Easing.inOut(Easing.ease), useNativeDriver: true }),
        Animated.timing(payPulse, { toValue: 0, duration: 1400, easing: Easing.inOut(Easing.ease), useNativeDriver: true }),
      ]),
    );
    loop.start();
    return () => loop.stop();
  }, [loading, wholePlan, payPulse]);
  const payGlow = payPulse.interpolate({ inputRange: [0, 1], outputRange: [0.35, 0.85] });

  // ── Shared submit helper (must be above useFocusEffect — TDZ) ──────────
  const runScan = useCallback(async (payload: Record<string, unknown>) => {
    if (loading) return;
    if (!user?.id || !user?.api_key) {
      setError({ error: "auth_required", message: t.avp_errAuthRequired });
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

  useFocusEffect(
    useCallback(() => {
      // 1) Paid room upload → submit to founder queue
      if (consumeAstrovastuRoomPaidReady()) {
        const pending = getPendingAstrovastuRoomUpload();
        if (pending?.purchase_id && user?.id && user?.api_key) {
          setUploadSubmitting(true);
          void submitAstrovastuRoomHumanOrder({
            user: { id: user.id, api_key: user.api_key },
            purchaseId: pending.purchase_id,
            urgent: !!pending.urgent,
          })
            .then((ok) => {
              if (ok) setUploadSuccessVisible(true);
            })
            .finally(() => setUploadSubmitting(false));
        }
      }

      // 2) Paid full home plan → auto-run scan on return
      if (consumeAstrovastuFloorPaidReady()) {
        const pending = getPendingAstrovastuFloorPlan();
        const fp = pending?.floor_plan_upload;
        if (fp && user?.id && user?.api_key) {
          clearPendingAstrovastuFloorPlan();
          void runScan({
            floor_plan_upload: {
              type: fp.type,
              ...(fp.data_url ? { data_url: fp.data_url } : {}),
              ...(fp.base64 ? { base64: fp.base64 } : {}),
              north_at: fp.north_at || "top",
            },
          });
        }
      }
    }, [runScan, user?.api_key, user?.id]),
  );

  // ── Camera capture: user-picked room + compass-derived direction ──
  const onCapture = useCallback((capture: SmartScanResult) => {
    if (!cameraRoom) return;
    const direction = typeof capture.heading_deg === "number"
      ? headingToDirCode(capture.heading_deg)
      : undefined;
    runScan({
      floor_plan: [{ room_type: cameraRoom, ...(direction ? { direction } : {}) }],
      floor_plan_upload: {
        type:     "image",
        data_url: capture.data_url,
        ...(typeof capture.heading_deg === "number"
          ? { heading_deg: capture.heading_deg }
          : {}),
      },
    });
  }, [runScan, cameraRoom]);

  // ── Gallery upload: pay → founder manual review ──
  const onUploadPaySubmit = useCallback((g: GalleryScanResult) => {
    if (!user?.id || !user?.api_key) {
      setError({ error: "auth_required", message: t.avp_errAuthRequired });
      return;
    }
    setUploadSubmitting(true);
    void startAstrovastuRoomUploadCheckout({
      user: { id: user.id, api_key: user.api_key },
      payload: {
        room_type: g.room_type,
        direction: g.direction,
        data_url: g.data_url,
        base64: g.base64,
      },
      urgent: priorityDelivery,
    })
      .then((result) => {
        if (result === "submitted") setUploadSuccessVisible(true);
      })
      .finally(() => setUploadSubmitting(false));
  }, [t.avp_errAuthRequired, user, priorityDelivery]);

  // ── Full home plan: pay ₹999 → return here → auto-run scan ───────────────
  const onWholePlanPay = useCallback(() => {
    if (!wholePlan) return;
    if (!user?.id || !user?.api_key) {
      setError({ error: "auth_required", message: t.avp_errAuthRequired });
      return;
    }
    setPendingAstrovastuFloorPlan({ floor_plan_upload: wholePlan, urgent: priorityDelivery });
    void purchaseFloorPlanSku({
      user: { id: user.id, api_key: user.api_key },
      planKind: "home",
      propertyName: "",
      returnTo: "astrovastu-pro",
      urgent: priorityDelivery,
    });
  }, [t.avp_errAuthRequired, user, wholePlan, priorityDelivery]);

  const onPickHomePlanPdf = useCallback(async () => {
    if (loading || planPicking) return;
    Haptics.selectionAsync();
    setPlanPicking(true);
    try {
      const r = await DocumentPicker.getDocumentAsync({
        type: ["application/pdf"],
        copyToCacheDirectory: true,
        multiple: false,
      });
      if (r.canceled || !r.assets?.[0]) return;
      const f = r.assets[0];
      if (typeof f.size === "number" && f.size > MAX_HOME_PLAN_BYTES) {
        Alert.alert("File too large", "Floor plan PDF must be under 10 MB.");
        return;
      }
      const FileSystem = await import("expo-file-system/legacy");
      const b64 = await FileSystem.readAsStringAsync(f.uri, {
        encoding: FileSystem.EncodingType.Base64,
      });
      setWholePlan({
        type: "pdf",
        base64: b64,
        filename: f.name || "home_floor_plan.pdf",
        size_bytes: f.size,
        north_at: "top",
      });
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      Alert.alert("Upload failed", msg || "Could not read the PDF.");
    } finally {
      setPlanPicking(false);
    }
  }, [loading, planPicking]);

  // ─────────────────────────────────────────────────────────────────────
  return (
    <View style={{ flex: 1, backgroundColor: C.bg, paddingTop: insets.top }}>
      <Stack.Screen options={{ headerShown: false }} />

      <View style={StyleSheet.absoluteFill} pointerEvents="none">
        <LinearGradient colors={[`${accent}16`, C.bg, C.bg]} style={StyleSheet.absoluteFill} />
        <PremiumOrb color={accent} />
      </View>

      <LinearGradient
        colors={[`${accent}28`, `${accent}08`, "transparent"]}
        style={[styles.header, { paddingTop: 4 }]}
      >
        <Pressable
          onPress={() => {
            if (router.canGoBack()) router.back();
            else router.replace("/astrovastu" as any);
          }}
          hitSlop={10}
          style={({ pressed }) => [ui.glassBtn, { opacity: pressed ? 0.75 : 1 }]}
        >
          <Feather name={I18nManager.isRTL ? "arrow-right" : "arrow-left"} size={20} color={C.text} />
        </Pressable>
        <View style={{ flex: 1, alignItems: "center" }}>
          <Text style={[ui.headerBadge, { color: accent }]}>
            {mode === "camera" ? "HOME VASTU" : "BUSINESS VASTU"}
          </Text>
          <Text style={[styles.headerTitle, { color: C.text }]}>{t.avp_headerTitle}</Text>
        </View>
        <View style={{ width: 40 }} />
      </LinearGradient>

      <ScrollView
        style={{ flex: 1, minHeight: 0 }}
        contentContainerStyle={{ padding: 16, paddingBottom: insets.bottom + 48, flexGrow: 1 }}
        keyboardShouldPersistTaps="handled"
        nestedScrollEnabled
        showsVerticalScrollIndicator={false}
      >
        <FadeInView delay={0}>
          <View style={[ui.heroCard, { borderColor: `${accent}44`, backgroundColor: `${accent}10` }]}>
            <View style={[ui.heroIconRing, { backgroundColor: `${accent}22`, borderColor: `${accent}55` }]}>
              <Feather name="home" size={22} color={accent} />
            </View>
            <Text style={[styles.heroTitle, { color: C.text }]}>{t.avp_heroTitle}</Text>
            <Text style={[styles.heroBody, { color: C.textMid }]}>{t.avp_heroBody}</Text>
          </View>
        </FadeInView>

        <FadeInView delay={staggerDelay(1)}>
          <View style={styles.modeRow}>
            {([
              { key: "camera" as const, icon: "camera" as const, title: t.avp_modeCameraTitle, sub: t.avp_modeCameraSub, tabAccent: HOME_ACCENT },
              { key: "business" as const, icon: "briefcase" as const, title: t.vt_titleBusinessVastu, sub: `${t.bv_biz_shop} · ${t.bv_biz_office}`, tabAccent: BIZ_TAB_ACCENT },
            ]).map((m) => {
              const sel = mode === m.key;
              const tabAccent = m.tabAccent;
              return (
                <Pressable
                  key={m.key}
                  onPress={() => {
                    Haptics.selectionAsync();
                    setMode(m.key);
                  }}
                  style={({ pressed }) => [
                    ui.modeCardOuter,
                    {
                      borderColor: sel ? tabAccent : C.border,
                      transform: [{ scale: pressed ? 0.97 : 1 }],
                    },
                  ]}
                >
                  {sel ? (
                    <LinearGradient
                      colors={[`${tabAccent}33`, `${tabAccent}08`]}
                      style={StyleSheet.absoluteFill}
                      start={{ x: 0, y: 0 }}
                      end={{ x: 1, y: 1 }}
                    />
                  ) : null}
                  <View style={[ui.modeIconRing, { borderColor: sel ? tabAccent : C.border, backgroundColor: sel ? `${tabAccent}22` : C.bgCard }]}>
                    <Feather name={m.icon} size={20} color={sel ? tabAccent : C.textMid} />
                  </View>
                  <Text style={[styles.modeTitle, { color: sel ? tabAccent : C.text }]}>{m.title}</Text>
                  <Text style={[styles.modeSub, { color: sel ? tabAccent : C.textMid }]}>{m.sub}</Text>
                  {sel ? <View style={[ui.bizSelDot, { backgroundColor: tabAccent }]} /> : null}
                </Pressable>
              );
            })}
          </View>
        </FadeInView>

        {mode === "camera" && (
          <>
            <FadeInView delay={staggerDelay(2)} resetKey="camera">
              <View style={[ui.priceRibbon, { borderColor: `${HOME_ACCENT}44`, backgroundColor: `${HOME_ACCENT}12` }]}>
                <Feather name="zap" size={14} color={HOME_ACCENT} />
                <Text style={[ui.priceRibbonText, { color: C.text }]}>
                  {`₹${ROOM_EXPERT_UPLOAD_PRICE_INR}/${perRoomLabel} · Full Home PDF ₹${HOME_PDF_PRICE}`}
                </Text>
              </View>
            </FadeInView>

            <VastuDeliveryOptions
              isDark={C.isDark}
              priority={priorityDelivery}
              onPriorityChange={setPriorityDelivery}
            />

            <SectionShell
              icon="map-pin"
              title={t.avp_pickerLabel}
              subtitle={cameraRoom
                ? `${t.avp_camHintPrefix} ${avpRoom(cameraRoom)}`
                : t.avp_pickerHint}
              accent={HOME_ACCENT}
              delay={staggerDelay(3)}
              resetKey={`room-${cameraRoom || "none"}`}
            >
              <View style={[ui.scopeBadgeRow, { backgroundColor: `${HOME_ACCENT}14`, borderColor: `${HOME_ACCENT}44` }]}>
                <Feather name="compass" size={13} color={HOME_ACCENT} />
                <Text style={[ui.scopeBadgeText, { color: HOME_ACCENT }]}>
                  {String(t.avp_badgeSingleRoom || "Single room")}
                </Text>
                <Text style={{ color: C.textMid, fontSize: 10, flex: 1 }} numberOfLines={2}>
                  {t.avp_introCameraBody}
                </Text>
              </View>

              <View style={styles.roomGrid}>
                {CAMERA_ROOMS.map((r) => {
                  const sel = cameraRoom === r.key;
                  return (
                    <Pressable
                      key={r.key}
                      onPress={() => {
                        Haptics.selectionAsync();
                        setCameraRoom((prev) => (prev === r.key ? null : r.key));
                      }}
                      disabled={loading}
                      style={({ pressed }) => [
                        ui.roomChip,
                        {
                          borderColor: sel ? HOME_ACCENT : C.border,
                          backgroundColor: sel ? `${HOME_ACCENT}18` : C.bgCard,
                          borderWidth: sel ? 2 : 1,
                          opacity: loading ? 0.5 : pressed ? 0.9 : 1,
                          transform: [{ scale: pressed ? 0.98 : 1 }],
                        },
                      ]}
                    >
                      <Feather name={r.icon} size={13} color={sel ? HOME_ACCENT : C.textMid} />
                      <Text style={{ flex: 1, color: sel ? HOME_ACCENT : C.text, fontSize: 11, fontWeight: sel ? "800" : "600" }}>
                        {avpRoom(r.key)}
                      </Text>
                      {sel ? <Feather name="check-circle" size={12} color={HOME_ACCENT} /> : null}
                    </Pressable>
                  );
                })}
              </View>
            </SectionShell>

            <SectionShell
              icon="upload-cloud"
              title={t.avp_introCameraTitle}
              subtitle={cameraRoom ? avpRoom(cameraRoom) : t.avp_camHintNoRoom}
              accent={HOME_ACCENT}
              delay={staggerDelay(4)}
            >
              <View style={[ui.uploadActionCard, { borderColor: `${HOME_ACCENT}33`, backgroundColor: `${HOME_ACCENT}08` }]}>
                <View style={styles.scanActionRow}>
              <View style={styles.scanActionCol}>
                <SmartScanCamera
                  compact
                  onCapture={onCapture}
                  loading={loading}
                  disabled={!cameraRoom}
                  disabledTitle={t.avp_camHintNoRoom}
                  disabledMessage={t.avp_pickerHint}
                  label={cameraLabel}
                />
              </View>
              <View style={styles.scanActionCol}>
                <GalleryScanUpload
                  compact
                  photoOnly
                  paidManual
                  priceInr={roomPayTotal}
                  pricePerRoomLabel={t.avp_uploadPricePerRoom}
                  payLabel={paySubmitLabel}
                  onPaySubmit={onUploadPaySubmit}
                  loading={loading || uploadSubmitting}
                  disabled={!cameraRoom}
                  preselectedRoom={cameraRoom}
                  disabledTitle={t.avp_camHintNoRoom}
                  disabledMessage={t.avp_pickerHint}
                  label={uploadRoomLabel}
                  roomLabel={avpRoom}
                />
              </View>
              <View style={styles.scanActionCol}>
                <Pressable
                  onPress={() => { void onPickHomePlanPdf(); }}
                  disabled={loading || planPicking}
                  style={({ pressed }) => [
                    styles.compactPlanBtn,
                    {
                      borderColor: wholePlan ? HOME_ACCENT : C.border,
                      backgroundColor: wholePlan ? `${HOME_ACCENT}18` : C.bgCard,
                      opacity: loading ? 0.55 : pressed ? 0.85 : 1,
                    },
                  ]}
                >
                  {planPicking ? (
                    <ActivityIndicator color={HOME_ACCENT} />
                  ) : (
                    <>
                      <Feather name="file-text" size={22} color={HOME_ACCENT} />
                      <Text style={[styles.compactPlanBtnText, { color: C.text }]}>
                        {homePdfLabel}
                      </Text>
                    </>
                  )}
                </Pressable>
              </View>
              </View>
              </View>
            </SectionShell>

            {wholePlan ? (
              <FadeInView delay={staggerDelay(5)}>
                <View style={[ui.pdfPlanCard, { borderColor: HOME_ACCENT, backgroundColor: `${HOME_ACCENT}14` }]}>
                  <View style={[ui.pdfIconWrap, { backgroundColor: `${HOME_ACCENT}22` }]}>
                    <Feather name="file-text" size={22} color={HOME_ACCENT} />
                  </View>
                  <View style={{ flex: 1 }}>
                    <Text style={[styles.planChipText, { color: C.text }]} numberOfLines={1}>
                      {wholePlan.filename || "home_floor_plan.pdf"}
                    </Text>
                    <Text style={{ color: C.textMid, fontSize: 10, marginTop: 2 }}>
                      {t.bv_planNorthHint || "Where is North on this plan?"}
                    </Text>
                  </View>
                  <Pressable
                    onPress={() => {
                      Haptics.selectionAsync();
                      setWholePlan(null);
                    }}
                    hitSlop={8}
                    disabled={loading}
                    style={{ padding: 4 }}
                  >
                    <Feather name="x" size={16} color={C.textMid} />
                  </Pressable>
                </View>
                <View style={styles.northRow}>
                  {(["top", "right", "bottom", "left"] as const).map((opt) => {
                    const sel = (wholePlan.north_at || "top") === opt;
                    return (
                      <Pressable
                        key={opt}
                        disabled={loading}
                        onPress={() => {
                          Haptics.selectionAsync();
                          setWholePlan({ ...wholePlan, north_at: opt as NorthAt });
                        }}
                        style={({ pressed }) => [
                          styles.northBtn,
                          {
                            borderColor: sel ? HOME_ACCENT : C.border,
                            backgroundColor: sel ? `${HOME_ACCENT}18` : C.bgCard,
                            opacity: loading ? 0.5 : pressed ? 0.85 : 1,
                          },
                        ]}
                      >
                        <Text style={{ color: sel ? HOME_ACCENT : C.text, fontWeight: "700", fontSize: 11 }}>
                          {opt[0].toUpperCase() + opt.slice(1)}
                        </Text>
                      </Pressable>
                    );
                  })}
                </View>
                <Animated.View style={[ui.submitGlow, { opacity: payGlow, backgroundColor: "#22c55e" }]} />
                <Pressable
                  onPress={onWholePlanPay}
                  disabled={loading || !wholePlan}
                  style={({ pressed }) => [ui.submitOuter, { opacity: (loading || !wholePlan) ? 0.55 : pressed ? 0.9 : 1 }]}
                >
                  <LinearGradient
                    colors={(loading || !wholePlan) ? [C.border, C.border] : ["#22c55e", "#16a34a"]}
                    start={{ x: 0, y: 0 }}
                    end={{ x: 1, y: 0 }}
                    style={ui.submitGradient}
                  >
                    {loading ? (
                      <ActivityIndicator color="#0B0F19" />
                    ) : (
                      <View style={ui.submitInner}>
                        <Feather name="credit-card" size={16} color="#0B0F19" />
                        <Text style={[styles.runScanText, { color: "#0B0F19" }]}>
                          {loading ? t.avp_btnAnalysing : `Pay ₹${homePdfTotal}`}
                        </Text>
                      </View>
                    )}
                  </LinearGradient>
                </Pressable>
              </FadeInView>
            ) : null}
          </>
        )}

        {mode === "business" && (
          <SectionShell
            icon="briefcase"
            title={t.vt_titleBusinessVastu}
            subtitle={`${t.bv_biz_shop} · ${t.bv_biz_office} · ${t.bv_biz_factory || "Factory"}`}
            accent={BIZ_TAB_ACCENT}
            delay={staggerDelay(2)}
            resetKey="business"
          >
            <Text style={{ color: C.textMid, fontSize: 12, lineHeight: 17, marginBottom: 12 }}>
              {t.bv_cardBody}
            </Text>
            <Pressable
              onPress={() => {
                Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
                router.push("/business-vastu" as any);
              }}
              style={({ pressed }) => [ui.submitOuter, { opacity: pressed ? 0.9 : 1 }]}
            >
              <LinearGradient
                colors={[BIZ_TAB_ACCENT, `${BIZ_TAB_ACCENT}BB`]}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 0 }}
                style={ui.submitGradient}
              >
                <View style={ui.submitInner}>
                  <Feather name="briefcase" size={16} color="#0B0F19" />
                  <Text style={[styles.runScanText, { color: "#0B0F19", flex: 1 }]}>
                    {t.vt_ctaOpenBusinessVastu}
                  </Text>
                  <Feather name={I18nManager.isRTL ? "chevron-left" : "chevron-right"} size={16} color="#0B0F19" />
                </View>
              </LinearGradient>
            </Pressable>
          </SectionShell>
        )}

        {error && (
          <FadeInView delay={staggerDelay(5)}>
          <View style={[ui.errCard, {
            backgroundColor: C.bgCard, borderColor: VERDICT_COLOR.Avoid.border,
          }]}>
            <Feather name="alert-triangle" size={18} color={VERDICT_COLOR.Avoid.fg} style={{ marginTop: 2 }} />
            <View style={{ flex: 1 }}>
              <Text style={[styles.errTitle, { color: C.text }]}>
                {error.error === "monthly_limit_reached" ? t.avp_errMonthlyLimit :
                 error.error === "upgrade_required"      ? t.avp_errUpgradeReq   :
                 error.error === "profile_incomplete"    ? t.avp_errProfile      :
                 error.error === "vision_no_rooms"       ? t.avp_errVisionNoRoom :
                 t.avp_errScanFailed}
              </Text>
              <Text style={[styles.errBody, { color: C.textMid, marginTop: 4 }]}>
                {error.message || t.avp_errBodyDefault}
              </Text>
              {error.error === "profile_incomplete" && (
                <Pressable onPress={() => router.push("/profile-edit")}
                           style={[styles.upgradeBtn, { backgroundColor: C.accent, marginTop: 10 }]}>
                  <Text style={styles.upgradeText}>{t.avp_btnCompleteProfile}</Text>
                </Pressable>
              )}
              {(error.upgrade_required || error.error === "upgrade_required" ||
                error.error === "monthly_limit_reached") && (
                <Pressable onPress={() => router.push("/subscription")}
                           style={[styles.upgradeBtn, { backgroundColor: C.accent, marginTop: 10 }]}>
                  <Text style={styles.upgradeText}>{t.avp_btnUpgradePro}</Text>
                </Pressable>
              )}
            </View>
          </View>
          </FadeInView>
        )}

        {/* ── Result: PDF version ────────────────────────────────────── */}
        {result && result.pdf_url && result.pdf_token && (() => {
          const overall = result.overall || ({} as ProResponse["overall"]);
          const grade   = overall.grade || "C";
          const score   = typeof overall.score === "number" ? overall.score : 0;
          const summary = overall.summary || { en: "", hi: "" };
          const pdfFullUrl =
            `${API_BASE}${result.pdf_url}?t=${encodeURIComponent(result.pdf_token)}`;
          const openPdf = () => {
            Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
            openReportPdfWithLanguageChoice(pdfFullUrl, {
              kind: "astrovastu_pro",
              title: `AstroVastu Home Pro · Score ${score}/100`,
              subtitle: `Grade ${grade} · ${new Date().toLocaleDateString()}`,
            });
          };
          return (
            <FadeInView delay={staggerDelay(6)}>
            <View style={{ marginTop: 18 }}>
              <View style={[ui.scoreCardPremium, { backgroundColor: C.bgCard, borderColor: `${HOME_ACCENT}44` }]}>
                <Text style={[styles.sectionLabel, { color: C.textMid }]}>{t.avp_overallScore}</Text>
                <View style={{ flexDirection: "row", alignItems: "baseline", gap: 6, marginTop: 4 }}>
                  <Text style={[styles.scoreNum, { color: GRADE_COLOR[grade] || C.text }]}>{score}</Text>
                  <Text style={{ color: C.textMid, fontWeight: "600" }}>/100</Text>
                  <View style={{
                    marginLeft: 8, paddingHorizontal: 10, paddingVertical: 3, borderRadius: 8,
                    backgroundColor: GRADE_COLOR[grade] || C.accent,
                  }}>
                    <Text style={{ color: "#fff", fontWeight: "800" }}>{t.avr_grade} {grade}</Text>
                  </View>
                </View>
                {summary.en ? (
                  <Text style={{ color: C.text, fontSize: 13, marginTop: 6 }}>{summary.en}</Text>
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

              <View style={[styles.card, { backgroundColor: C.bgCard, borderColor: C.border, marginTop: 12 }]}>
                <View style={{ flexDirection: "row", alignItems: "center", gap: 8, marginBottom: 8 }}>
                  <Feather name="file-text" size={18} color={C.accent} />
                  <Text style={[styles.cardTitle, { color: C.text }]}>{t.avp_pdfReady}</Text>
                </View>
                <Text style={{ color: C.text, fontSize: 13, marginBottom: 12 }}>
                  {t.avp_pdfBody}
                </Text>
                <Pressable onPress={openPdf} style={[styles.submitBtn, { backgroundColor: C.accent }]}>
                  <View style={{ flexDirection: "row", alignItems: "center", gap: 8 }}>
                    <Feather name="download" size={16} color="#fff" />
                    <Text style={styles.submitText}>{t.avp_btnOpenPdf}</Text>
                  </View>
                </Pressable>
              </View>

              <Text style={{ color: C.textMid, fontSize: 11, marginTop: 14, textAlign: "center" }}>
                {t.avp_footerBrand}
              </Text>
            </View>
            </FadeInView>
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
          <FadeInView delay={staggerDelay(6)}>
          <View style={{ marginTop: 18 }}>
            <View style={[ui.scoreCardPremium, { backgroundColor: C.bgCard, borderColor: `${HOME_ACCENT}44` }]}>
              <Text style={[styles.sectionLabel, { color: C.textMid }]}>{t.avp_overallScore}</Text>
              <View style={{ flexDirection: "row", alignItems: "baseline", gap: 6, marginTop: 4 }}>
                <Text style={[styles.scoreNum, { color: GRADE_COLOR[grade] || C.text }]}>{score}</Text>
                <Text style={{ color: C.textMid, fontWeight: "600" }}>/100</Text>
                <View style={{
                  marginLeft: 8, paddingHorizontal: 10, paddingVertical: 3, borderRadius: 8,
                  backgroundColor: GRADE_COLOR[grade] || C.accent,
                }}>
                  <Text style={{ color: "#fff", fontWeight: "800" }}>{t.avr_grade} {grade}</Text>
                </View>
              </View>
              <ScanBasisBadge
                visionRoomFindings={result.vision_room_findings}
                visionUsed={(result as any).vision_used}
                visionFindingsCount={(result as any).vision_findings_count}
                perRoomBasis={(result.rooms || []).map((rr: any) => ({
                  room_type: rr.room_type, direction_basis: rr.direction_basis,
                }))}
              />
              <Text style={{ color: C.text, fontSize: 13, marginTop: 6 }}>{summary.en}</Text>
              <Text style={{ color: C.textMid, fontSize: 12, marginTop: 2 }}>{summary.hi}</Text>
            </View>

            <View style={styles.countsRow}>
              {([
                [t.avp_lblIdeal,      counts.ideal,             VERDICT_COLOR.Ideal],
                [t.avp_lblAcceptable, counts.acceptable,        VERDICT_COLOR.Acceptable],
                [t.avp_lblAdjust,     counts.adjustment_needed, VERDICT_COLOR["Adjustment Needed"]],
                [t.avp_lblAvoid,      counts.avoid,             VERDICT_COLOR.Avoid],
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
                    {t.avp_lblMdAlert} · {mdAlert.active_lord} ({mdAlert.lord_direction})
                  </Text>
                </View>
                <Text style={{ color: C.text, fontSize: 13 }}>{mdAlert.summary_loc || mdAlert.summary_en}</Text>
              </View>
            )}

            {priorities.length > 0 && (
              <View style={[styles.card, { backgroundColor: C.bgCard, borderColor: C.border, marginTop: 14 }]}>
                <Text style={[styles.sectionLabel, { color: C.textMid, marginBottom: 8 }]}>
                  {t.avp_secPriority}
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
              {t.avp_secRoomByRoom}
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
                      {t.bv_lblZone}: {r.zone.planet} · {r.zone.deity}  ·  {r.score}/100
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
                ? t.avp_quotaUnlimited
                : `${t.avp_quotaPrefix} ${quota.used}/${quota.limit} ${t.avp_quotaThisMonth}`}
            </Text>
          </View>
          </FadeInView>
          );
        })()}

        {/* ── Branding footer (NEVER reveal AI/LLM) ──────────────────── */}
        <Text style={[styles.brandingFooter, { color: C.textMid }]}>
          {t.avp_brandFooter}
        </Text>
        <Text style={[styles.brandingFooterSmall, { color: C.textMid }]}>
          {t.avp_brandFooterSub}
        </Text>
      </ScrollView>

      <OrderSuccessModal
        visible={uploadSuccessVisible}
        onClose={() => setUploadSuccessVisible(false)}
        onViewReports={() => {
          setUploadSuccessVisible(false);
          router.push("/my-reports" as any);
        }}
        title="Order Confirmed!"
        message="Your room photo has been received. Our Vastu expert is personally reviewing it — your personalised report is on its way."
        etaLabel={
          priorityDelivery
            ? "Report in My Reports within 12 hrs"
            : "Report in My Reports in 4–6 business days"
        }
      />
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
  heroTitle:   { fontSize: 18, fontWeight: "800", marginBottom: 6, textAlign: "center" },
  heroBody:    { fontSize: 12, lineHeight: 17, textAlign: "center" },

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

  modeRow:   { flexDirection: "row", gap: 8, marginBottom: 14 },
  modeTile:  { flex: 1, alignItems: "center", paddingVertical: 14, paddingHorizontal: 6,
               borderRadius: 12, borderWidth: 1, gap: 6 },
  modeTitle: { fontSize: 12, fontWeight: "700", textAlign: "center" },
  modeSub:   { fontSize: 10, fontWeight: "500", textAlign: "center", opacity: 0.85 },

  modeIntro:      { borderRadius: 12, borderWidth: 1, padding: 12, marginBottom: 12 },
  modeIntroTitle: { fontSize: 14, fontWeight: "700", marginBottom: 4 },
  modeIntroBody:  { fontSize: 12, lineHeight: 17 },
  scopeBadge:     { paddingHorizontal: 10, paddingVertical: 5, borderRadius: 999, borderWidth: 1 },
  scopeBadgeText: { fontSize: 10, fontWeight: "900", letterSpacing: 0.3 },

  pickerLabel: { fontSize: 13, fontWeight: "700", marginBottom: 8 },
  pickerHint:  { fontSize: 11, marginTop: 6, fontStyle: "italic" },
  roomGrid:    { flexDirection: "row", flexWrap: "wrap", gap: 8 },
  roomChip:    { flexDirection: "row", alignItems: "center", gap: 6,
                 paddingVertical: 9, paddingHorizontal: 12,
                 borderRadius: 9, borderWidth: 1 },

  scanActionRow: { flexDirection: "row", gap: 10, marginTop: 0, alignItems: "stretch" },
  scanActionCol: { flex: 1 },
  compactPlanBtn: {
    flex: 1,
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
    paddingVertical: 18,
    paddingHorizontal: 10,
    borderRadius: 16,
    borderWidth: 2,
    minHeight: 96,
  },
  compactPlanBtnText: { fontSize: 12, fontWeight: "800", textAlign: "center", lineHeight: 16 },
  planChip: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    paddingVertical: 8,
    paddingHorizontal: 10,
    borderRadius: 8,
    borderWidth: 1,
  },
  planChipText: { flex: 1, fontSize: 12, fontWeight: "600" },
  northRow: { flexDirection: "row", gap: 6 },
  northBtn: {
    flex: 1,
    paddingVertical: 7,
    borderRadius: 8,
    borderWidth: 1,
    alignItems: "center",
  },

  runScanBtn:  { flexDirection: "row", alignItems: "center", justifyContent: "center",
                 gap: 8, paddingVertical: 13, borderRadius: 10, marginTop: 10 },
  runScanText: { fontSize: 14, fontWeight: "800" },

  altLink:     { flexDirection: "row", alignItems: "center", gap: 12, padding: 14, borderRadius: 14, borderWidth: 1 },
  altLinkTitle:{ fontSize: 14, fontWeight: "800" },
  altLinkSub:  { fontSize: 11, marginTop: 2 },
});

const ui = StyleSheet.create({
  orb: {
    position: "absolute",
    top: -60,
    right: -40,
    width: 220,
    height: 220,
    borderRadius: 110,
  },
  glassBtn: {
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "rgba(255,255,255,0.08)",
    borderWidth: 1,
    borderColor: "rgba(255,255,255,0.12)",
  },
  headerBadge: {
    fontSize: 10,
    fontWeight: "900",
    letterSpacing: 2.2,
    marginBottom: 2,
  },
  heroCard: {
    borderRadius: 18,
    borderWidth: 1,
    padding: 18,
    marginBottom: 14,
    alignItems: "center",
    overflow: "hidden",
  },
  heroIconRing: {
    width: 48,
    height: 48,
    borderRadius: 24,
    borderWidth: 1.5,
    alignItems: "center",
    justifyContent: "center",
    marginBottom: 10,
  },
  priceRibbon: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    paddingVertical: 10,
    paddingHorizontal: 14,
    borderRadius: 14,
    borderWidth: 1,
    marginBottom: 14,
  },
  priceRibbonText: { fontSize: 12, fontWeight: "700" },
  modeCardOuter: {
    flex: 1,
    borderWidth: 1.5,
    borderRadius: 16,
    paddingVertical: 14,
    paddingHorizontal: 8,
    alignItems: "center",
    overflow: "hidden",
    minHeight: 108,
    gap: 6,
  },
  modeIconRing: {
    width: 44,
    height: 44,
    borderRadius: 22,
    borderWidth: 1.5,
    alignItems: "center",
    justifyContent: "center",
  },
  bizSelDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    marginTop: 2,
  },
  sectionShell: {
    borderRadius: 18,
    borderWidth: 1,
    padding: 14,
    marginBottom: 14,
    overflow: "hidden",
  },
  sectionHead: {
    flexDirection: "row",
    alignItems: "flex-start",
    gap: 10,
    marginBottom: 12,
  },
  sectionIconWrap: {
    width: 34,
    height: 34,
    borderRadius: 10,
    borderWidth: 1,
    alignItems: "center",
    justifyContent: "center",
  },
  sectionHeadTitle: {
    fontSize: 14,
    fontWeight: "800",
    letterSpacing: 0.2,
  },
  sectionHeadSub: {
    fontSize: 11,
    marginTop: 3,
    lineHeight: 15,
  },
  scopeBadgeRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    padding: 10,
    borderRadius: 12,
    borderWidth: 1,
    marginBottom: 12,
  },
  scopeBadgeText: {
    fontSize: 10,
    fontWeight: "900",
    letterSpacing: 0.3,
  },
  roomChip: {
    flexDirection: "row",
    alignItems: "center",
    gap: 5,
    width: "48.5%",
    paddingVertical: 9,
    paddingHorizontal: 9,
    borderRadius: 12,
  },
  uploadActionCard: {
    borderRadius: 16,
    borderWidth: 1,
    padding: 10,
  },
  pdfPlanCard: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    marginTop: 4,
    marginBottom: 10,
    padding: 12,
    borderRadius: 14,
    borderWidth: 1,
  },
  pdfIconWrap: {
    width: 42,
    height: 42,
    borderRadius: 12,
    alignItems: "center",
    justifyContent: "center",
  },
  submitGlow: {
    position: "absolute",
    left: 20,
    right: 20,
    top: 8,
    height: 44,
    borderRadius: 22,
  },
  submitOuter: {
    marginTop: 6,
    borderRadius: 16,
    overflow: "hidden",
  },
  submitGradient: {
    paddingVertical: 15,
    alignItems: "center",
    justifyContent: "center",
  },
  submitInner: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    paddingHorizontal: 8,
  },
  errCard: {
    flexDirection: "row",
    gap: 10,
    padding: 14,
    borderRadius: 16,
    borderWidth: 1,
    marginTop: 14,
  },
  scoreCardPremium: {
    borderRadius: 18,
    borderWidth: 1,
    padding: 16,
    overflow: "hidden",
  },
});
