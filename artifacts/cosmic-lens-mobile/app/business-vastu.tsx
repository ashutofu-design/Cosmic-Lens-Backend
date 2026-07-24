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
 * Branding: "Powered by Advanced Cosmic Intelligence" — never reveal AI/LLM.
 */
import { Feather } from "@expo/vector-icons";
import * as DocumentPicker from "expo-document-picker";
import * as Haptics from "expo-haptics";
import * as Linking from "expo-linking";
import * as WebBrowser from "expo-web-browser";
import { LinearGradient } from "expo-linear-gradient";
import { router, Stack } from "expo-router";
import React, { useCallback, useEffect, useRef, useState } from "react";
import {
  ActivityIndicator,
  Alert,
  Animated,
  Easing,
  Image,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { FadeInView, staggerDelay } from "@/components/motion/FadeInView";
import { OrderSuccessModal } from "@/components/OrderSuccessModal";

import { useC } from "@/context/ThemeContext";
import { useUser } from "@/context/UserContext";
import { useT } from "@/hooks/useT";
import { API_BASE } from "@/lib/apiConfig";
import { openReportPdfWithLanguageChoice } from "@/lib/pdfLanguagePicker";
import { GalleryScanResult, GalleryScanUpload } from "@/components/GalleryScanUpload";
import { ScanBasisBadge, VisionRoomFindings } from "@/components/ScanBasisBadge";
import {
  SmartScanCamera,
  SmartScanResult,
} from "@/components/SmartScanCamera";
import { NorthAt, SmartScanUploadValue } from "@/components/SmartScanUpload";

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
    { key: "billing_counter",en: "Billing Counter",hi: "Billing",       icon: "credit-card" },
    { key: "vault",          en: "Vault",          hi: "Tijori",        icon: "lock",         critical: true },
    { key: "stock_storage",  en: "Stock Storage",  hi: "Bhandaar",      icon: "package" },
    { key: "display",        en: "Display Area",   hi: "Pradarshan",    icon: "grid" },
    { key: "pooja",          en: "Mandir / Pooja", hi: "Pooja",         icon: "sun" },
    { key: "back_office",    en: "Back Office",    hi: "Peeche Office", icon: "briefcase" },
    { key: "staff_room",     en: "Staff Room",     hi: "Staff Room",    icon: "users" },
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

const VERDICT_COLOR: Record<string, { bg: string; fg: string; border: string }> = {
  Ideal:                { bg: "rgba(16,185,129,0.18)", fg: "#10B981", border: "rgba(16,185,129,0.45)" },
  Acceptable:           { bg: "rgba(59,130,246,0.18)", fg: "#3B82F6", border: "rgba(59,130,246,0.45)" },
  "Adjustment Needed":  { bg: "rgba(245,158,11,0.18)", fg: "#F59E0B", border: "rgba(245,158,11,0.45)" },
  Avoid:                { bg: "rgba(239,68,68,0.18)",  fg: "#EF4444", border: "rgba(239,68,68,0.45)"  },
};
const GRADE_COLOR: Record<string, string> = {
  A: "#10B981", B: "#3B82F6", C: "#F59E0B", D: "#EF4444",
};

const BIZ_ACCENT: Record<BizType, string> = {
  shop: "#f59e0b",
  office: "#06b6d4",
  factory: "#8b5cf6",
};

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
}: {
  icon: keyof typeof Feather.glyphMap;
  title: string;
  subtitle?: string;
  accent: string;
  children: React.ReactNode;
  delay?: number;
}) {
  const C = useC();
  return (
    <FadeInView delay={delay} style={[ui.sectionShell, { borderColor: `${accent}33` }]}>
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

const DIR_TO_HEADING: Record<string, number> = {
  N: 0, NE: 45, E: 90, SE: 135, S: 180, SW: 225, W: 270, NW: 315,
};

function dirToHeadingDeg(dir: string): number | undefined {
  const d = (dir || "").trim().toUpperCase();
  return DIR_TO_HEADING[d];
}

const MAX_ROOM_PHOTOS = 6;
const MAX_PLAN_BYTES = 10 * 1024 * 1024;
const SHOP_ROOM_PHOTO_PRICE = 399;
const OFFICE_ROOM_PHOTO_PRICE = 499;
const FACTORY_ROOM_PHOTO_PRICE = 999;
const SHOP_PDF_PRICE = 2999;
const OFFICE_PDF_PRICE = 6999;
const FACTORY_PDF_PRICE = 14999;

const DEFAULT_PLAN_FILENAME: Record<BizType, string> = {
  shop: "shop_floor_plan.pdf",
  office: "office_floor_plan.pdf",
  factory: "factory_floor_plan.pdf",
};

type RoomPhoto = {
  room_type: string;
  image_data_url: string;
  heading_deg?: number;
};

type RoomReport = {
  room_type: string; direction: string; verdict: string; severity: string;
  severity_label?: string; score: number; is_critical: boolean;
  zone?: { planet?: string; deity?: string; element?: string };
  mahadasha?: { applies: boolean; kind?: string; reason_en?: string; reason_hi?: string; reason_loc?: string };
  business_rule?: { applies: boolean; kind?: string; reason_en?: string; reason_hi?: string; reason_loc?: string };
};
type PriorityAction = {
  room_type: string; direction: string; verdict: string;
  severity_label: string; is_critical: boolean;
  why_en: string; why_hi: string; why_loc?: string;
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
    summary_en: string; summary_hi: string; summary_loc?: string;
  } | null;
  stakeholder?: { partner_count: number; common_favour: string[]; common_conflict: string[]; summary_en: string; summary_hi: string; summary_loc?: string };
  muhurat?:     { applies: boolean; alignment?: string; summary_en?: string; summary_hi?: string; summary_loc?: string } | null;
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
  const t = useT() as any;
  const bvBiz  = (k: string) => t[`bv_biz_${k}`]   ?? k;
  const bvRoom = (k: string) => t[`bv_room_${k}`]  ?? k.replace(/_/g, " ");

  const [bizType,   setBizType]   = useState<BizType>("shop");
  const [propertyName, setPropertyName] = useState("");
  const [loading,   setLoading]   = useState(false);
  const [result,    setResult]    = useState<BizResponse | null>(null);
  const [error,     setError]     = useState<ErrorPayload | null>(null);
  const [roomPhotos, setRoomPhotos] = useState<RoomPhoto[]>([]);
  const [photoRoom, setPhotoRoom] = useState<string | null>(null);
  const [planUpload, setPlanUpload] = useState<SmartScanUploadValue | null>(null);
  const [planPicking, setPlanPicking] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [uploadSuccessVisible, setUploadSuccessVisible] = useState(false);

  const roomOpts = ROOM_BY_BIZ[bizType];
  const photosFull = roomPhotos.length >= MAX_ROOM_PHOTOS;

  const onChangeBizType = useCallback((b: BizType) => {
    Haptics.selectionAsync();
    setBizType(b);
    setPhotoRoom(null);
    setRoomPhotos([]);
    setPlanUpload(null);
    setResult(null); setError(null);
    setSubmitted(false);
  }, []);

  const onPickPlanPdf = useCallback(async () => {
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
      if (typeof f.size === "number" && f.size > MAX_PLAN_BYTES) {
        Alert.alert("File too large", "Floor plan PDF must be under 10 MB.");
        return;
      }
      const FileSystem = await import("expo-file-system/legacy");
      const b64 = await FileSystem.readAsStringAsync(f.uri, {
        encoding: FileSystem.EncodingType.Base64,
      });
      setPlanUpload({
        type: "pdf",
        base64: b64,
        filename: f.name || DEFAULT_PLAN_FILENAME[bizType],
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
  }, [loading, planPicking, bizType]);

  const appendRoomPhoto = useCallback((photo: RoomPhoto) => {
    setSubmitted(false);
    setRoomPhotos((prev) => {
      if (prev.length >= MAX_ROOM_PHOTOS) return prev;
      return [...prev, photo];
    });
    Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
  }, []);

  const onPhotoCapture = useCallback((capture: SmartScanResult) => {
    if (!photoRoom) return;
    appendRoomPhoto({
      room_type: photoRoom,
      image_data_url: capture.data_url,
      ...(typeof capture.heading_deg === "number"
        ? { heading_deg: capture.heading_deg }
        : {}),
    });
  }, [appendRoomPhoto, photoRoom]);

  const onGalleryPhotoSubmit = useCallback((g: GalleryScanResult) => {
    const room = photoRoom || g.room_type;
    if (!room) return;
    const heading = dirToHeadingDeg(g.direction);
    appendRoomPhoto({
      room_type: room,
      image_data_url: g.data_url,
      ...(typeof heading === "number" ? { heading_deg: heading } : {}),
    });
  }, [appendRoomPhoto, photoRoom]);

  const removeRoomPhoto = useCallback((index: number) => {
    Haptics.selectionAsync();
    setRoomPhotos((prev) => prev.filter((_, i) => i !== index));
    setSubmitted(false);
  }, []);

  const onSubmit = useCallback(async () => {
    if (loading) return;
    if (!user?.id || !user?.api_key) {
      setError({ error: "auth_required", message: t.bv_errAuthRequired });
      return;
    }
    if (roomPhotos.length < 2 && !planUpload) {
      setError({ error: "validation", message: t.bv_errValidationRooms });
      return;
    }
    if (!propertyName.trim()) {
      setError({ error: "validation",
                 message: t.bv_errValidationName });
      return;
    }

    setError(null); setResult(null); setSubmitted(false); setLoading(true);
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);

    try {
      const resp = await fetch(`${API_BASE}/api/business-vastu/submit-order`, {
        method:  "POST",
        headers: { "Content-Type": "application/json", "X-API-Key": user.api_key },
        body:    JSON.stringify({
          user_id:       user.id,
          business_type: bizType,
          property_name: propertyName.trim(),
          ...(planUpload
            ? {
                floor_plan_upload: {
                  type: planUpload.type,
                  ...(planUpload.data_url ? { data_url: planUpload.data_url } : {}),
                  ...(planUpload.base64   ? { base64:   planUpload.base64   } : {}),
                  ...(planUpload.filename ? { filename: planUpload.filename } : {}),
                  north_at: planUpload.north_at || "top",
                },
              }
            : {}),
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
        setSubmitted(true);
        setRoomPhotos([]);
        setPlanUpload(null);
        setPhotoRoom(null);
        Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
        setUploadSuccessVisible(true);
      }
    } catch (e: any) {
      setError({ error: "network", message: String(e?.message || e) });
    } finally {
      setLoading(false);
    }
  }, [loading, user, bizType, propertyName, planUpload, roomPhotos, t.bv_errAuthRequired, t.bv_errValidationName, t.bv_errValidationRooms]);

  const hasUploads = roomPhotos.length > 0 || !!planUpload;

  const bizMeta = BIZ_OPTIONS.find(b => b.key === bizType)!;
  const planPdfLabel =
    bizType === "shop"
      ? `${t.bv_btnUploadShopPdf || "Upload Full Shop PDF"} (₹${SHOP_PDF_PRICE})`
      : bizType === "office"
        ? `${t.bv_btnUploadOfficePdf || "Upload Full Office PDF"} (₹${OFFICE_PDF_PRICE})`
        : bizType === "factory"
          ? `${t.bv_btnUploadFactoryPdf || "Upload Full Factory PDF"} (₹${FACTORY_PDF_PRICE})`
          : "";
  const roomPhotoPrice =
    bizType === "office" ? OFFICE_ROOM_PHOTO_PRICE
    : bizType === "factory" ? FACTORY_ROOM_PHOTO_PRICE
    : SHOP_ROOM_PHOTO_PRICE;
  const galleryPhotoBase =
    bizType === "factory"
      ? (t.bv_btnUploadFactoryPhoto || "Upload Factory Photo")
      : bizType === "office"
        ? (t.bv_btnUploadOfficePhoto || "Upload Office Room Photo")
        : (t.avp_btnUploadPhoto || "Upload Room Photo");
  const galleryPhotoLabel = `${galleryPhotoBase} (₹${roomPhotoPrice}/${t.avp_uploadPricePerRoom || "per room"})`;
  const accent = BIZ_ACCENT[bizType];
  const planPdfPrice =
    bizType === "office" ? OFFICE_PDF_PRICE
    : bizType === "factory" ? FACTORY_PDF_PRICE
    : SHOP_PDF_PRICE;
  const submitPulse = useRef(new Animated.Value(0)).current;
  useEffect(() => {
    if (loading || submitted) return;
    const loop = Animated.loop(
      Animated.sequence([
        Animated.timing(submitPulse, { toValue: 1, duration: 1400, easing: Easing.inOut(Easing.ease), useNativeDriver: true }),
        Animated.timing(submitPulse, { toValue: 0, duration: 1400, easing: Easing.inOut(Easing.ease), useNativeDriver: true }),
      ]),
    );
    loop.start();
    return () => loop.stop();
  }, [loading, submitted, submitPulse]);
  const submitGlow = submitPulse.interpolate({ inputRange: [0, 1], outputRange: [0.35, 0.85] });

  // ─────────────────────────────────────────────────────────────────────
  return (
    <View style={{ flex: 1, backgroundColor: C.bg, paddingTop: insets.top }}>
      <Stack.Screen options={{ headerShown: false }} />

      <View style={StyleSheet.absoluteFill} pointerEvents="none">
        <LinearGradient
          colors={[`${accent}16`, C.bg, C.bg]}
          style={StyleSheet.absoluteFill}
        />
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
          <Feather name="arrow-left" size={20} color={C.text} />
        </Pressable>
        <View style={{ flex: 1, alignItems: "center" }}>
          <Text style={[ui.headerBadge, { color: accent }]}>BUSINESS VASTU</Text>
          <Text style={[styles.headerTitle, { color: C.text }]}>{t.bv_headerTitle}</Text>
        </View>
        <View style={{ width: 40 }} />
      </LinearGradient>

      <ScrollView
        contentContainerStyle={{ padding: 16, paddingBottom: insets.bottom + 40 }}
        keyboardShouldPersistTaps="handled"
        showsVerticalScrollIndicator={false}
      >
        <FadeInView delay={0}>
          <View style={[ui.priceRibbon, { borderColor: `${accent}44`, backgroundColor: `${accent}12` }]}>
            <Feather name="zap" size={14} color={accent} />
            <Text style={[ui.priceRibbonText, { color: C.text }]}>
              {`₹${roomPhotoPrice}/${t.avp_uploadPricePerRoom || "room"} · PDF ₹${planPdfPrice}`}
            </Text>
          </View>
        </FadeInView>

        <SectionShell
          icon="layers"
          title={t.bv_secBizType}
          subtitle={bvBiz(bizType)}
          accent={accent}
          delay={staggerDelay(1)}
        >
          <View style={styles.bizRow}>
            {BIZ_OPTIONS.map((b) => {
              const sel = b.key === bizType;
              const bAccent = BIZ_ACCENT[b.key];
              return (
                <Pressable
                  key={b.key}
                  onPress={() => onChangeBizType(b.key)}
                  style={({ pressed }) => [
                    ui.bizCardOuter,
                    {
                      borderColor: sel ? bAccent : C.border,
                      transform: [{ scale: pressed ? 0.97 : 1 }],
                    },
                  ]}
                >
                  {sel ? (
                    <LinearGradient
                      colors={[`${bAccent}33`, `${bAccent}08`]}
                      style={StyleSheet.absoluteFill}
                      start={{ x: 0, y: 0 }}
                      end={{ x: 1, y: 1 }}
                    />
                  ) : null}
                  <View style={[ui.bizIconRing, { borderColor: sel ? bAccent : C.border, backgroundColor: sel ? `${bAccent}22` : C.bgCard }]}>
                    <Feather name={b.icon} size={20} color={sel ? bAccent : C.textMid} />
                  </View>
                  <Text style={{ color: sel ? bAccent : C.text, fontWeight: "800", marginTop: 8, fontSize: 13 }}>
                    {bvBiz(b.key)}
                  </Text>
                  {sel ? (
                    <View style={[ui.bizSelDot, { backgroundColor: bAccent }]} />
                  ) : null}
                </Pressable>
              );
            })}
          </View>
        </SectionShell>

        <SectionShell
          icon="home"
          title={t.bv_secPremiseName}
          subtitle={t.bv_premiseHint}
          accent={accent}
          delay={staggerDelay(2)}
        >
          <View style={[ui.inputWrap, { borderColor: `${accent}44`, backgroundColor: C.bgCard }]}>
            <Feather name="edit-3" size={16} color={accent} style={{ marginRight: 10 }} />
            <TextInput
              value={propertyName}
              onChangeText={setPropertyName}
              placeholder={t.bv_phPremiseName}
              placeholderTextColor={C.textMid}
              style={[ui.input, { color: C.text }]}
            />
          </View>
        </SectionShell>

        <SectionShell
          icon="camera"
          title={t.avp_pickerLabel || "Which room is this photo for?"}
          subtitle={photoRoom
            ? `${t.avp_camHintPrefix || "Photographing"} ${bvRoom(photoRoom)} · ${roomPhotos.length}/${MAX_ROOM_PHOTOS}`
            : (t.avp_pickerHint || "Pick a room below before taking or uploading a photo.")}
          accent={accent}
          delay={staggerDelay(3)}
        >
        <View style={styles.roomGrid}>
          {roomOpts.map((r) => {
            const sel = photoRoom === r.key;
            return (
              <Pressable
                key={r.key}
                onPress={() => {
                  Haptics.selectionAsync();
                  setPhotoRoom((prev) => (prev === r.key ? null : r.key));
                }}
                disabled={loading}
                style={({ pressed }) => [
                  ui.roomChip,
                  {
                    borderColor: sel ? accent : C.border,
                    backgroundColor: sel ? `${accent}18` : C.bgCard,
                    borderWidth: sel ? 2 : 1,
                    opacity: loading ? 0.5 : pressed ? 0.9 : 1,
                    transform: [{ scale: pressed ? 0.98 : 1 }],
                  },
                ]}
              >
                <Feather name={r.icon} size={13} color={sel ? accent : C.textMid} />
                <Text
                  style={[styles.roomChipLabel, { color: sel ? accent : C.text, fontWeight: sel ? "800" : "600" }]}
                  numberOfLines={1}
                >
                  {bvRoom(r.key)}
                </Text>
                {sel ? (
                  <Feather name="check-circle" size={12} color={accent} />
                ) : r.critical ? (
                  <Text style={styles.roomChipStar}>★</Text>
                ) : null}
              </Pressable>
            );
          })}
        </View>

        <View style={[ui.uploadActionCard, { borderColor: `${accent}33`, backgroundColor: `${accent}08` }]}>
        <View style={styles.scanActionRow}>
          <View style={styles.scanActionCol}>
            <SmartScanCamera
              compact
              onCapture={onPhotoCapture}
              loading={loading}
              disabled={!photoRoom || photosFull}
              disabledTitle={t.avp_camHintNoRoom || "Pick a room first"}
              disabledMessage={t.avp_pickerHint || "Select which area this photo is for."}
              label={`${t.avp_btnSmartScan || "Open Camera"} (₹${roomPhotoPrice}/${t.avp_uploadPricePerRoom || "per room"})`}
            />
          </View>
          <View style={styles.scanActionCol}>
            <GalleryScanUpload
              compact
              photoOnly
              onSubmit={onGalleryPhotoSubmit}
              loading={loading}
              disabled={!photoRoom || photosFull}
              preselectedRoom={photoRoom}
              disabledTitle={t.avp_camHintNoRoom || "Pick a room first"}
              disabledMessage={t.avp_pickerHint || "Select which area this photo is for."}
              label={galleryPhotoLabel}
              roomLabel={bvRoom}
              submitLabel={t.bv_addRoomPhoto || "Add Photo"}
            />
          </View>
          {(bizType === "shop" || bizType === "office" || bizType === "factory") ? (
            <View style={styles.scanActionCol}>
              <Pressable
                onPress={() => { void onPickPlanPdf(); }}
                disabled={loading || planPicking}
                style={({ pressed }) => [
                  styles.compactPlanBtn,
                  {
                    borderColor: planUpload ? accent : C.border,
                    backgroundColor: planUpload ? `${accent}18` : C.bgCard,
                    opacity: loading ? 0.55 : pressed ? 0.85 : 1,
                  },
                ]}
              >
                {planPicking ? (
                  <ActivityIndicator color={accent} />
                ) : (
                  <>
                    <Feather name="file-text" size={22} color={accent} />
                    <Text style={[styles.compactPlanBtnText, { color: C.text }]}>
                      {planPdfLabel}
                    </Text>
                  </>
                )}
              </Pressable>
            </View>
          ) : null}
        </View>
        </View>

        {hasUploads ? (
          <View style={{ marginTop: 14 }}>
            <View style={ui.uploadsHeader}>
              <Feather name="image" size={14} color={accent} />
              <Text style={[styles.sectionTitle, { color: C.text, marginBottom: 0, marginTop: 0 }]}>
                {t.bv_secUploadedPhotos || "Uploaded Photos"}
              </Text>
            </View>
            {roomPhotos.length > 0 ? (
              <View style={styles.photoPreviewGrid}>
                {roomPhotos.map((p, i) => (
                  <View
                    key={`${p.room_type}-${i}`}
                    style={[ui.photoPreviewCard, { borderColor: `${accent}44`, backgroundColor: C.bgCard }]}
                  >
                    <Image source={{ uri: p.image_data_url }} style={styles.photoPreviewImg} resizeMode="cover" />
                    <View style={styles.photoPreviewMeta}>
                      <Text style={[styles.photoPreviewLabel, { color: C.text }]} numberOfLines={1}>
                        {bvRoom(p.room_type)}
                      </Text>
                      <Pressable
                        onPress={() => removeRoomPhoto(i)}
                        hitSlop={8}
                        disabled={loading}
                        style={{ padding: 2 }}
                      >
                        <Feather name="x" size={14} color={C.textMid} />
                      </Pressable>
                    </View>
                  </View>
                ))}
              </View>
            ) : null}
            {planUpload ? (
              <View style={[ui.pdfPreviewCard, { borderColor: accent, backgroundColor: `${accent}14` }]}>
                <View style={[ui.pdfIconWrap, { backgroundColor: `${accent}22` }]}>
                  <Feather name="file-text" size={22} color={accent} />
                </View>
                <View style={{ flex: 1 }}>
                  <Text style={[styles.pdfPreviewTitle, { color: C.text }]} numberOfLines={1}>
                    {planUpload.filename || DEFAULT_PLAN_FILENAME[bizType]}
                  </Text>
                  <Text style={[styles.pickerHintCompact, { color: C.textMid }]}>
                    {t.bv_planNorthHint || "Where is North on this plan?"}{" "}
                    · {(planUpload.north_at || "top").toUpperCase()}
                  </Text>
                </View>
                <Pressable
                  onPress={() => {
                    Haptics.selectionAsync();
                    setPlanUpload(null);
                    setSubmitted(false);
                  }}
                  hitSlop={8}
                  disabled={loading}
                  style={{ padding: 4 }}
                >
                  <Feather name="x" size={16} color={C.textMid} />
                </Pressable>
              </View>
            ) : null}
            {(bizType === "shop" || bizType === "office" || bizType === "factory") && planUpload ? (
              <View style={{ marginTop: 8 }}>
                <View style={styles.northRow}>
                  {(["top", "right", "bottom", "left"] as const).map((opt) => {
                    const sel = (planUpload.north_at || "top") === opt;
                    return (
                      <Pressable
                        key={opt}
                        disabled={loading}
                        onPress={() => {
                          Haptics.selectionAsync();
                          setPlanUpload({ ...planUpload, north_at: opt as NorthAt });
                        }}
                        style={({ pressed }) => [
                          styles.northBtn,
                          {
                            borderColor: sel ? accent : C.border,
                            backgroundColor: sel ? `${accent}18` : C.bgCard,
                            opacity: loading ? 0.5 : pressed ? 0.85 : 1,
                          },
                        ]}
                      >
                        <Text style={{ color: sel ? accent : C.text, fontWeight: "700", fontSize: 11 }}>
                          {opt[0].toUpperCase() + opt.slice(1)}
                        </Text>
                      </Pressable>
                    );
                  })}
                </View>
              </View>
            ) : null}
          </View>
        ) : null}
        </SectionShell>

        <FadeInView delay={staggerDelay(4)}>
          <Animated.View style={[ui.submitGlow, { opacity: submitGlow, backgroundColor: accent }]} />
          <Pressable
            onPress={onSubmit}
            disabled={loading || submitted}
            style={({ pressed }) => [
              ui.submitOuter,
              { opacity: loading || submitted ? 0.65 : pressed ? 0.9 : 1 },
            ]}
          >
            <LinearGradient
              colors={submitted ? [C.border, C.border] : [accent, `${accent}BB`]}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 0 }}
              style={ui.submitGradient}
            >
              {loading ? (
                <ActivityIndicator color="#fff" />
              ) : (
                <View style={ui.submitInner}>
                  <Feather name="credit-card" size={18} color="#fff" />
                  <Text style={styles.submitText}>{t.bv_btnSubmitReview || "Pay Now"}</Text>
                </View>
              )}
            </LinearGradient>
          </Pressable>
        </FadeInView>

        {/* ── Error / 402 paywall card ───────────────────────────────── */}
        {error && (
          <FadeInView delay={staggerDelay(5)}>
          <View style={[ui.errCard, {
            backgroundColor: C.bgCard, borderColor: VERDICT_COLOR.Avoid.border,
          }]}>
            <Feather name="alert-triangle" size={18} color={VERDICT_COLOR.Avoid.fg} style={{ marginTop: 2 }} />
            <View style={{ flex: 1 }}>
              <Text style={[styles.errTitle, { color: C.text }]}>
                {error.error === "upgrade_required"   ? t.bv_errUnlockTitle    :
                 error.error === "profile_incomplete" ? t.bv_errProfileTitle   :
                 error.error === "validation"         ? t.bv_errValidTitle     :
                 t.bv_errScanFailed}
              </Text>
              <Text style={[styles.errBody, { color: C.textMid, marginTop: 4 }]}>
                {error.message || t.bv_errTryAgain}
              </Text>
              {error.error === "profile_incomplete" && (
                <Pressable onPress={() => router.push("/profile-edit")}
                           style={[styles.upgradeBtn, { backgroundColor: accent, marginTop: 10 }]}>
                  <Text style={styles.upgradeText}>{t.bv_btnCompleteProfile}</Text>
                </Pressable>
              )}
              {(error.upgrade_required || error.error === "upgrade_required") && (
                <Text style={{ color: C.textMid, fontSize: 12, marginTop: 8 }}>
                  {t.bv_walletHintPrefix} {bvBiz(bizType)} {t.bv_walletHintSuffix.replace("{price}", String(bizMeta.price))}
                </Text>
              )}
            </View>
          </View>
          </FadeInView>
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
            openReportPdfWithLanguageChoice(pdfFullUrl, {
              kind: "business_vastu",
              title: `Business Vastu · Score ${score}/100`,
              subtitle: `Grade ${grade} · ${new Date().toLocaleDateString()}`,
            });
          };
          return (
            <View style={{ marginTop: 18 }}>
              <View style={[styles.scoreCard, { backgroundColor: C.bgCard, borderColor: C.border }]}>
                <View style={{ flex: 1 }}>
                  <Text style={[styles.sectionLabel, { color: C.textMid }]}>{t.bv_overallScore}</Text>
                  <View style={{ flexDirection: "row", alignItems: "baseline", gap: 6, marginTop: 4 }}>
                    <Text style={[styles.scoreNum, { color: GRADE_COLOR[grade] || C.text }]}>{score}</Text>
                    <Text style={{ color: C.textMid, fontWeight: "600" }}>/100</Text>
                    <View style={{
                      marginLeft: 8, paddingHorizontal: 10, paddingVertical: 3, borderRadius: 8,
                      backgroundColor: GRADE_COLOR[grade] || C.accent,
                    }}>
                      <Text style={{ color: "#fff", fontWeight: "800" }}>{t.bv_grade} {grade}</Text>
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
                  <Text style={[styles.cardTitle, { color: C.text }]}>{t.bv_pdfReady}</Text>
                </View>
                <Text style={{ color: C.text, fontSize: 13, marginBottom: 4 }}>
                  {t.bv_pdfBodyHi}
                </Text>
                <Text style={{ color: C.textMid, fontSize: 12, marginBottom: 12 }}>
                  {t.bv_pdfBodyEn}
                </Text>
                <Pressable
                  onPress={openPdf}
                  style={[styles.submitBtn, { backgroundColor: C.accent }]}
                >
                  <View style={{ flexDirection: "row", alignItems: "center", gap: 8 }}>
                    <Feather name="download" size={16} color="#fff" />
                    <Text style={styles.submitText}>{t.bv_btnOpenPdf}</Text>
                  </View>
                </Pressable>
              </View>

              <Text style={{ color: C.textMid, fontSize: 11, marginTop: 14, textAlign: "center" }}>
                {t.bv_footerBrand}
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
                <Text style={[styles.sectionLabel, { color: C.textMid }]}>{t.bv_overallScore}</Text>
                <View style={{ flexDirection: "row", alignItems: "baseline", gap: 6, marginTop: 4 }}>
                  <Text style={[styles.scoreNum, { color: GRADE_COLOR[grade] || C.text }]}>{score}</Text>
                  <Text style={{ color: C.textMid, fontWeight: "600" }}>/100</Text>
                  <View style={{
                    marginLeft: 8, paddingHorizontal: 10, paddingVertical: 3, borderRadius: 8,
                    backgroundColor: GRADE_COLOR[grade] || C.accent,
                  }}>
                    <Text style={{ color: "#fff", fontWeight: "800" }}>{t.bv_grade} {grade}</Text>
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
                [t.bv_lblIdeal,      cts.ideal,             VERDICT_COLOR.Ideal],
                [t.bv_lblAcceptable, cts.acceptable,        VERDICT_COLOR.Acceptable],
                [t.bv_lblAdjust,     cts.adjustment_needed, VERDICT_COLOR["Adjustment Needed"]],
                [t.bv_lblAvoid,      cts.avoid,             VERDICT_COLOR.Avoid],
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
                    {t.bv_lblOwnerMd} · {md.active_lord} ({md.lord_direction})
                  </Text>
                </View>
                <Text style={{ color: C.text, fontSize: 12 }}>{md.summary_loc || md.summary_en}</Text>
              </View>
            )}

            {/* Stakeholder synergy */}
            {stk && stk.partner_count > 0 && (
              <View style={[styles.mdAlert, {
                backgroundColor: C.bgCard, borderColor: VERDICT_COLOR.Acceptable.border,
              }]}>
                <View style={{ flexDirection: "row", alignItems: "center", gap: 6, marginBottom: 6 }}>
                  <Feather name="users" size={16} color={VERDICT_COLOR.Acceptable.fg} />
                  <Text style={[styles.cardTitle, { color: C.text }]}>{t.bv_lblStakeholder}</Text>
                </View>
                <Text style={{ color: C.text, fontSize: 12 }}>{stk.summary_loc || stk.summary_en}</Text>
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
                    {t.bv_lblMuhuratAlign} · {(mh.alignment || "").toUpperCase()}
                  </Text>
                </View>
                <Text style={{ color: C.text, fontSize: 12 }}>{mh.summary_loc || mh.summary_en}</Text>
              </View>
            )}

            {/* Priority actions */}
            {prio.length > 0 && (
              <View style={{ marginTop: 14 }}>
                <Text style={[styles.sectionTitle, { color: C.text }]}>{t.bv_secPriority}</Text>
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
                          <Text style={{ color: VERDICT_COLOR.Avoid.fg, fontSize: 10, fontWeight: "800" }}>★ {t.bv_lblCritical}</Text>
                        )}
                      </View>
                      <Text style={{ color: C.text, fontSize: 12 }}>{p.why_loc || p.why_en}</Text>
                    </View>
                  );
                })}
              </View>
            )}

            {/* Per-room details */}
            <Text style={[styles.sectionTitle, { color: C.text, marginTop: 14 }]}>{t.bv_secRoomByRoom}</Text>
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
                      {t.bv_lblZone}: {r.zone.planet} · {r.zone.deity} · {r.zone.element}
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
                <Text style={[styles.sectionLabel, { color: C.textMid, marginBottom: 4 }]}>{t.bv_secClassicalRefs}</Text>
                {refs.map((r, i) => (
                  <Text key={i} style={{ color: C.text, fontSize: 11 }}>• {r}</Text>
                ))}
              </View>
            )}

            {/* Footer */}
            <Text style={{ color: C.textMid, fontSize: 11, marginTop: 14, textAlign: "center" }}>
              {t.bv_footerBrand}
            </Text>
          </View>
          );
        })()}
      </ScrollView>
      <OrderSuccessModal
        visible={uploadSuccessVisible}
        onClose={() => setUploadSuccessVisible(false)}
        onViewReports={() => {
          setUploadSuccessVisible(false);
          router.push("/my-reports" as any);
        }}
        title="Order Confirmed!"
        message="Your business photos have been received. Our Vastu expert is personally reviewing them — your personalised report is on its way."
        etaLabel="Report in My Reports within 24–48 hrs"
      />
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
  sectionTitle:  { fontSize: 13, fontWeight: "800", marginBottom: 8, marginTop: 4, letterSpacing: 0.4 },
  sectionLabel:  { fontSize: 10, fontWeight: "800", letterSpacing: 1 },
  bizRow:        { flexDirection: "row", gap: 8 },
  bizCard:       { flex: 1, borderWidth: 1, borderRadius: 12, paddingVertical: 12, alignItems: "center" },
  input:         { borderWidth: 1, borderRadius: 10, paddingHorizontal: 12, paddingVertical: 10, fontSize: 14, marginTop: 4 },
  pickerLabel:   { fontSize: 12, fontWeight: "800", marginBottom: 4 },
  pickerHint:    { fontSize: 11, marginTop: 6, fontStyle: "italic" },
  pickerHintCompact: { fontSize: 10, marginBottom: 6 },
  roomGrid:      { flexDirection: "row", flexWrap: "wrap", gap: 6 },
  roomChip:      {
    flexDirection: "row",
    alignItems: "center",
    gap: 5,
    width: "48.5%",
    paddingVertical: 7,
    paddingHorizontal: 8,
    borderRadius: 8,
  },
  roomChipLabel: { flex: 1, fontSize: 11, lineHeight: 14 },
  roomChipStar:  { fontSize: 10, color: "#F59E0B", fontWeight: "800" },
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
    marginTop: 8,
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
  photoPreviewGrid: { flexDirection: "row", flexWrap: "wrap", gap: 8 },
  photoPreviewCard: {
    width: "31%",
    borderRadius: 10,
    borderWidth: 1,
    overflow: "hidden",
  },
  photoPreviewImg: { width: "100%", aspectRatio: 1 },
  photoPreviewMeta: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: 6,
    paddingVertical: 5,
    gap: 4,
  },
  photoPreviewLabel: { flex: 1, fontSize: 10, fontWeight: "700" },
  pdfPreviewCard: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    marginTop: 8,
    padding: 10,
    borderRadius: 10,
    borderWidth: 1,
  },
  pdfPreviewTitle: { fontSize: 12, fontWeight: "700" },
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
  bizCardOuter: {
    flex: 1,
    borderWidth: 1.5,
    borderRadius: 16,
    paddingVertical: 14,
    alignItems: "center",
    overflow: "hidden",
    minHeight: 108,
  },
  bizIconRing: {
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
    marginTop: 6,
  },
  inputWrap: {
    flexDirection: "row",
    alignItems: "center",
    borderWidth: 1,
    borderRadius: 14,
    paddingHorizontal: 14,
    paddingVertical: 4,
  },
  input: {
    flex: 1,
    fontSize: 14,
    paddingVertical: 10,
    fontWeight: "600",
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
    marginTop: 12,
    borderRadius: 16,
    borderWidth: 1,
    padding: 10,
  },
  uploadsHeader: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    marginBottom: 10,
  },
  photoPreviewCard: {
    width: "31%",
    borderRadius: 14,
    borderWidth: 1,
    overflow: "hidden",
  },
  pdfPreviewCard: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    marginTop: 8,
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
    paddingVertical: 16,
    alignItems: "center",
    justifyContent: "center",
  },
  submitInner: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
  },
  successCard: {
    borderRadius: 16,
    padding: 14,
    borderWidth: 1,
    marginTop: 12,
  },
  errCard: {
    flexDirection: "row",
    gap: 10,
    padding: 14,
    borderRadius: 16,
    borderWidth: 1,
    marginTop: 14,
  },
});
