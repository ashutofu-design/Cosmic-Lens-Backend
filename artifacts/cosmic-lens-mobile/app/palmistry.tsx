import { Feather } from "@expo/vector-icons";
import * as Haptics from "expo-haptics";
import * as ImagePicker from "expo-image-picker";
import { LinearGradient } from "expo-linear-gradient";
import { router, useFocusEffect } from "expo-router";
import React, { useCallback, useEffect, useRef, useState } from "react";
import {
  ActivityIndicator,
  Alert,
  Animated,
  Easing,
  Image,
  Modal,
  Platform,
  Pressable,
  ScrollView,
  StatusBar,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { LivePalmScanView } from "@/components/palm/LivePalmScanView";
import { FadeInView, staggerDelay } from "@/components/motion/FadeInView";
import { OrderSuccessModal } from "@/components/OrderSuccessModal";
import { PRO_PICKER_ACCENTS, ProProductPicker } from "@/components/ProProductPicker";
import { useC } from "@/context/ThemeContext";
import { useUser } from "@/context/UserContext";
import { useT } from "@/hooks/useT";
import { FOUNDER_PROFILE } from "@/lib/founderProfile";
import { PRIORITY_GUARANTEE, STANDARD_DELIVERY_ETA } from "@/lib/deliverySla";
import { registerPendingMyReport } from "@/lib/registerPendingMyReport";
import { API_BASE as SHARED_API_BASE } from "@/lib/apiConfig";
import {
  PALMISTRY_CHECKOUT_CONFIG,
  PALMISTRY_PRO_PLANS,
  palmistryPlanEtaLabel,
  palmistryPlanTotalInr,
  palmistryPriorityFeeInr,
  type PalmistryProPlan,
} from "@/lib/palmistryProOffer";
import {
  consumePalmistryPaidReady,
  gatePalmistryAfterReady,
} from "@/lib/palmistryReportCheckoutFlow";
import { getPendingPalmistryCheckout } from "@/lib/pendingPalmistryCheckout";

const BASIC_ACCENT = "#14b8a6";
const PRO_ACCENT = "#f59e0b";
const ACCENT = BASIC_ACCENT;
const SHOW_PALM_SCAN_DEBUG = false;
// Same API as My Reports / rest of app (api.coosmic.icu) so pending cards sync.
const API_BASE = SHARED_API_BASE || "https://api.coosmic.icu";

type ScanPhase = "idle" | "uploading" | "scanning" | "submitting" | "done";
type HandSide = "left" | "right";
type CheckStatus = "complete" | "unavailable" | "attention";

type ScanCheck = {
  id: string;
  label: string;
  detail: string;
  status: CheckStatus;
};

function productionValidation(scan: any) {
  return scan?.production_validation || null;
}

function scanReadyForAdmin(scan: any) {
  if (!scan?.schema_version) return false;
  if (scan?.hand?.status === "detected") return true;
  return productionValidation(scan)?.status === "verified";
}

function newPalmSessionId() {
  return `palm_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 10)}`;
}

function normalizeWhatsappDigits(raw: string): string {
  let digits = (raw || "").replace(/\D/g, "");
  if (digits.startsWith("0091") && digits.length >= 14) digits = digits.slice(4);
  else if (digits.startsWith("91") && digits.length >= 12) digits = digits.slice(2);
  if (digits.startsWith("0") && digits.length === 11) digits = digits.slice(1);
  return digits.slice(0, 10);
}

function lineCheck(id: string, label: string, line: any): ScanCheck {
  const path = Array.isArray(line?.path) ? line.path : [];
  const found = line?.status === "detected" || (line?.status === "ambiguous" && path.length >= 2);
  const length = line?.normalized_length ?? line?.measurements?.length_px ?? line?.length;
  const lengthText = typeof line?.normalized_length === "number"
    ? `${Math.round(line.normalized_length * 100)}% of palm span`
    : typeof length === "number"
      ? `${Math.round(length)} px path`
      : "path measured";
  return {
    id,
    label,
    detail: found ? `Mapped · ${lengthText}` : "Not reliably identifiable",
    status: line?.status === "detected" ? "complete" : found ? "attention" : "unavailable",
  };
}

function scanChecks(scan: any): ScanCheck[] {
  const gate = productionValidation(scan);
  const line = (name: string) => scan.major_lines?.[name];
  const mount = (name: string) => scan.mounts?.[name];
  const detected = (value: any) => value?.status === "detected";
  const checked = (value: any) => value?.status && value.status !== "unknown";
  return [
    {
      id: "production-gate",
      label: "Production validation gate",
      detail:
        gate?.status === "verified"
          ? "Production validation passed"
          : gate?.status === "rejected"
            ? "Production validation failed"
            : gate?.user_message || "Production validation in progress",
      status: gate?.status === "verified" ? "complete" : gate?.status === "rejected" ? "attention" : "unavailable",
    },
    {
      id: "quality",
      label: "Image quality checked",
      detail: `${Math.round((scan.quality?.score ?? 0) * 100)}% usable quality`,
      status: scan.quality?.usable ? "complete" : "attention",
    },
    {
      id: "hand",
      label: "Hand identified",
      detail: `${scan.hand?.side || "Unknown"} hand · palm orientation verified`,
      status: detected(scan.hand) ? "complete" : "attention",
    },
    {
      id: "landmarks",
      label: "21 hand landmarks mapped",
      detail: `${scan.landmarks?.length || 0}/21 landmark points`,
      status: scan.landmarks?.length === 21 ? "complete" : "attention",
    },
    lineCheck("life-line", "Life Line checked", line("life_line")),
    lineCheck("heart-line", "Heart Line checked", line("heart_line")),
    lineCheck("head-line", "Head Line checked", line("head_line")),
    lineCheck("fate-line", "Fate Line checked", line("fate_line")),
    {
      id: "venus",
      label: "Venus Mount region mapped",
      detail: detected(mount("Venus")) ? "Region and texture measured" : "Region unavailable",
      status: detected(mount("Venus")) ? "complete" : "unavailable",
    },
    {
      id: "mercury",
      label: "Mercury Mount region mapped",
      detail: detected(mount("Mercury")) ? "Region and texture measured" : "Region unavailable",
      status: detected(mount("Mercury")) ? "complete" : "unavailable",
    },
    {
      id: "jupiter",
      label: "Jupiter Mount region mapped",
      detail: detected(mount("Jupiter")) ? "Region and texture measured" : "Region unavailable",
      status: detected(mount("Jupiter")) ? "complete" : "unavailable",
    },
    {
      id: "fingers",
      label: "Finger proportions measured",
      detail: "Index · middle · ring · little",
      status: Object.values(scan.fingers || {}).every(detected) ? "complete" : "attention",
    },
    {
      id: "thumb",
      label: "Thumb structure measured",
      detail: "Length · width · spread angle",
      status: detected(scan.thumb) ? "complete" : "attention",
    },
    {
      id: "markings",
      label: "Special markings checked",
      detail: scan.special_markings?.status === "detected"
        ? "Supported marking candidates found"
        : "No reliable special marking detected",
      status: checked(scan.special_markings) ? "complete" : "unavailable",
    },
    {
      id: "confidence",
      label: "Scan confidence calculated",
      detail: `${Math.round((scan.scan_confidence?.overall ?? 0) * 100)}% confidence`,
      status: scanReadyForAdmin(scan) ? "complete" : "attention",
    },
  ];
}

function basicSurface(isDark: boolean) {
  return {
    page: isDark ? "#0f172a" : "#ecfdf5",
    pageGrad: (isDark
      ? ["#134e4a", "#1e293b", "#0f172a"]
      : ["#99f6e4", "#ecfdf5", "#f8fafc"]) as [string, string, string],
    card: isDark ? "#1e293b" : "#ffffff",
    card2: isDark ? "#334155" : "#f1f5f9",
    border: isDark ? "rgba(45,212,191,0.42)" : "rgba(20,184,166,0.22)",
    title: isDark ? "#f8fafc" : "#0f172a",
    body: isDark ? "#e2e8f0" : "#334155",
    muted: isDark ? "#cbd5e1" : "#475569",
    label: isDark ? "#5eead4" : "#0f766e",
  };
}

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

interface PalmLineInfo {
  key: string;
  emoji: string;
  title: string;
  titleHi: string;
  color: string;
  desc: string;
  descHi: string;
  traits: string[];
  traitsHi: string[];
}

const PALM_LINES: PalmLineInfo[] = [
  {
    key: "life",
    emoji: "🌿",
    title: "Life Line",
    titleHi: "जीवन रेखा",
    color: "#22c55e",
    desc: "Vitality, resilience, and life direction — not lifespan. A deep curve shows strong life force and adaptability.",
    descHi: "जीवन शक्ति, लचीलापन और जीवन की दिशा — उम्र नहीं। गहरी रेखा मजबूत जीवन ऊर्जा दिखाती है।",
    traits: ["Vitality", "Resilience", "Adaptability"],
    traitsHi: ["जीवन शक्ति", "लचीलापन", "अनुकूलन"],
  },
  {
    key: "heart",
    emoji: "💗",
    title: "Heart Line",
    titleHi: "हृदय रेखा",
    color: "#f43f5e",
    desc: "Emotional nature, love style, and relationship patterns. Long lines suggest deep feeling; forks show complexity in love.",
    descHi: "भावनात्मक स्वभाव, प्रेम की शैली और रिश्तों के पैटर्न। लंबी रेखा गहरी भावना दिखाती है।",
    traits: ["Emotion", "Love style", "Relationships"],
    traitsHi: ["भावना", "प्रेम शैली", "रिश्ते"],
  },
  {
    key: "head",
    emoji: "🧠",
    title: "Head Line",
    titleHi: "मस्तिष्क रेखा",
    color: "#6366f1",
    desc: "Thinking style, decision-making, and mental focus. Straight lines lean practical; curved lines show creativity.",
    descHi: "सोचने का तरीका, निर्णय और मानसिक फोकस। सीधी रेखा व्यावहारिक; घुमावदार रचनात्मकता दिखाती है।",
    traits: ["Intellect", "Decisions", "Focus"],
    traitsHi: ["बुद्धि", "निर्णय", "फोकस"],
  },
  {
    key: "fate",
    emoji: "⭐",
    title: "Fate Line",
    titleHi: "भाग्य रेखा",
    color: "#f59e0b",
    desc: "Career path, purpose, and external influences on your direction. Clear fate lines suggest strong life purpose.",
    descHi: "करियर पथ, उद्देश्य और बाहरी प्रभाव। स्पष्ट भाग्य रेखा मजबूत जीवन उद्देश्य दिखाती है।",
    traits: ["Career", "Purpose", "Direction"],
    traitsHi: ["करियर", "उद्देश्य", "दिशा"],
  },
];

function PalmLineCard({
  info,
  expanded,
  onToggle,
  delay = 0,
}: {
  info: PalmLineInfo;
  expanded: boolean;
  onToggle: () => void;
  delay?: number;
}) {
  const C = useC();
  const t = useT();
  const S = basicSurface(C.isDark);
  const isHi = t.vlang === "hi";

  return (
    <FadeInView delay={delay}>
      <Pressable
        onPress={onToggle}
        style={({ pressed }) => [
          plc.card,
          {
            backgroundColor: S.card,
            borderColor: S.border,
            transform: [{ scale: pressed ? 0.99 : 1 }],
          },
        ]}
      >
        <LinearGradient colors={[`${info.color}18`, "transparent"]} style={StyleSheet.absoluteFill} pointerEvents="none" />
        <View style={plc.topRow}>
          <View style={[plc.emojiCircle, { backgroundColor: `${info.color}18`, borderColor: `${info.color}45` }]}>
            <Text style={{ fontSize: 20 }}>{info.emoji}</Text>
          </View>
          <View style={{ flex: 1 }}>
            <Text style={[plc.label, { color: S.label }]}>{isHi ? info.titleHi : info.title}</Text>
            <Text style={[plc.title, { color: info.color }]}>{info.title}</Text>
          </View>
          <Feather name={expanded ? "chevron-up" : "chevron-down"} size={16} color={S.muted} />
        </View>
        <Text style={[plc.body, { color: S.body }]} numberOfLines={expanded ? undefined : 2}>
          {isHi ? info.descHi : info.desc}
        </Text>
        {expanded ? (
          <View style={plc.traits}>
            {(isHi ? info.traitsHi : info.traits).map((tr) => (
              <View key={tr} style={[plc.chip, { backgroundColor: `${info.color}12`, borderColor: `${info.color}28` }]}>
                <Text style={[plc.chipTxt, { color: info.color }]}>{tr}</Text>
              </View>
            ))}
          </View>
        ) : null}
      </Pressable>
    </FadeInView>
  );
}

const plc = StyleSheet.create({
  card: { borderRadius: 18, borderWidth: 1.5, padding: 16, gap: 10, overflow: "hidden" },
  topRow: { flexDirection: "row", alignItems: "flex-start", gap: 12 },
  emojiCircle: { width: 44, height: 44, borderRadius: 14, borderWidth: 1.5, alignItems: "center", justifyContent: "center" },
  label: { fontSize: 9, fontFamily: "Nunito_800ExtraBold", letterSpacing: 1.1, textTransform: "uppercase" },
  title: { fontSize: 14.5, fontFamily: "Nunito_800ExtraBold", lineHeight: 19 },
  body: { fontSize: 11.5, fontFamily: "Nunito_500Medium", lineHeight: 16 },
  traits: { flexDirection: "row", flexWrap: "wrap", gap: 6 },
  chip: { paddingHorizontal: 8, paddingVertical: 4, borderRadius: 8, borderWidth: 1 },
  chipTxt: { fontSize: 11, fontFamily: "Nunito_700Bold" },
});

function BasicProCompare() {
  const C = useC();
  const t = useT();
  const S = basicSurface(C.isDark);
  return (
    <View style={[bc.card, { backgroundColor: S.card, borderColor: S.border, overflow: "hidden" }]}>
      <LinearGradient colors={[`${PRO_ACCENT}10`, "transparent"]} style={StyleSheet.absoluteFill} pointerEvents="none" />
      <Text style={[bc.label, { color: S.label }]}>Basic vs Pro</Text>
      <View style={bc.row}>
        <View style={[bc.col, { borderColor: S.border, backgroundColor: S.card2 }]}>
          <Text style={[bc.title, { color: S.title }]}>{t.km_basic}</Text>
          <Text style={[bc.body, { color: S.body }]}>
            Major lines guide · mounts overview · no photo needed
          </Text>
        </View>
        <View style={[bc.col, { borderColor: "rgba(245,158,11,0.45)", backgroundColor: C.isDark ? "rgba(245,158,11,0.16)" : "rgba(245,158,11,0.12)" }]}>
          <Text style={[bc.title, { color: PRO_ACCENT }]}>{t.vu_tabPro}</Text>
          <Text style={[bc.body, { color: S.body }]}>
            Both hands · bilateral analysis · founder-reviewed PDF report
          </Text>
        </View>
      </View>
    </View>
  );
}

const bc = StyleSheet.create({
  card: { borderRadius: 18, borderWidth: 1, padding: 14, gap: 10 },
  label: { fontSize: 9, fontFamily: "Nunito_800ExtraBold", letterSpacing: 1.1, textTransform: "uppercase" },
  row: { flexDirection: "row", gap: 8 },
  col: { flex: 1, borderRadius: 12, borderWidth: 1, padding: 12, gap: 6 },
  title: { fontSize: 14.5, fontFamily: "Nunito_800ExtraBold", lineHeight: 19 },
  body: { fontSize: 11.5, fontFamily: "Nunito_500Medium", lineHeight: 16 },
});

function BasicProTease({ onOpenPro }: { onOpenPro: () => void }) {
  const C = useC();
  const t = useT();
  const S = basicSurface(C.isDark);
  return (
    <View style={{ gap: 10 }}>
      <Text style={[bc.body, { color: S.body, textAlign: "center", paddingHorizontal: 8 }]}>
        Pro mein dono haath ka full scan + founder-reviewed report milta hai.
      </Text>
      <Pressable
        onPress={() => { Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium); onOpenPro(); }}
        style={({ pressed }) => ({ opacity: pressed ? 0.9 : 1 })}
      >
        <LinearGradient colors={["#d97706", "#f59e0b", "#fbbf24"]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }} style={bp.tease}>
          <Feather name="file-text" size={16} color="#fff" />
          <Text style={{ color: "#fff", flex: 1, flexShrink: 1, textAlign: "center", fontSize: 14, fontFamily: "Nunito_800ExtraBold" }}>
            Get Palmistry Pro Report — ₹{PALMISTRY_PRO_PLANS.pdf.priceInr}
          </Text>
          <Feather name="chevron-right" size={16} color="#fff" />
        </LinearGradient>
      </Pressable>
    </View>
  );
}

const bp = StyleSheet.create({
  tease: { flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 8, paddingVertical: 15, paddingHorizontal: 14, borderRadius: 16 },
});

export default function PalmistryScreen() {
  const C = useC();
  const t = useT();
  const { user } = useUser();
  const insets = useSafeAreaInsets();
  const [writingHand, setWritingHand] = useState<HandSide>("right");
  const [imageUris, setImageUris] = useState<Record<HandSide, string | null>>({
    left: null,
    right: null,
  });
  const [phase, setPhase] = useState<ScanPhase>("idle");
  const [error, setError] = useState("");
  const [scans, setScans] = useState<Record<HandSide, any>>({
    left: null,
    right: null,
  });
  const [revealedChecks, setRevealedChecks] = useState<Record<HandSide, number>>({
    left: 0,
    right: 0,
  });
  const [uploadedToAdmin, setUploadedToAdmin] = useState(false);
  const [tab, setTab] = useState<"basic" | "pro">("basic");
  const [expandedLines, setExpandedLines] = useState<Record<string, boolean>>({ life: true });
  const [founderExpanded, setFounderExpanded] = useState(false);
  const [selectedPlan, setSelectedPlan] = useState<PalmistryProPlan>("pdf");
  const [priorityDelivery, setPriorityDelivery] = useState(false);
  const [whatsapp, setWhatsapp] = useState("");
  const [langOpen, setLangOpen] = useState(false);
  const [pdfLang, setPdfLang] = useState<"en" | "hn" | "hi">("hn");
  const [preparingBanner, setPreparingBanner] = useState<{
    plan: PalmistryProPlan;
    priority: boolean;
    orderId?: string;
  } | null>(null);
  const sessionIdRef = useRef(newPalmSessionId());
  const top = Platform.OS === "android"
    ? Math.max(insets.top, StatusBar.currentHeight ?? 24)
    : insets.top;
  const topPad = Platform.OS === "web" ? 67 : top;
  const botPad = Platform.OS === "web" ? 34 : insets.bottom;
  const busy = phase !== "idle" && phase !== "done";
  const isBasic = tab === "basic";
  const accent = isBasic ? BASIC_ACCENT : PRO_ACCENT;
  const S = basicSurface(C.isDark);
  const proCardBg = C.isDark ? "rgba(255,255,255,0.04)" : "rgba(255,255,255,0.92)";
  const proBorder = C.isDark ? "rgba(255,255,255,0.1)" : "rgba(0,0,0,0.08)";
  const proTitleColor = C.isDark ? "#f8fafc" : "#0f172a";
  const proBodyColor = C.isDark ? "rgba(226,232,240,0.72)" : "#64748b";
  const isVideo = selectedPlan === "vip";
  const priorityFee = palmistryPriorityFeeInr(selectedPlan);
  const orderTotalInr = palmistryPlanTotalInr(selectedPlan, priorityDelivery);
  const waDigits = normalizeWhatsappDigits(whatsapp);
  const proAnswers = [
    "What do my Life, Heart, Head and Fate lines show about my path?",
    "How do left vs right palm differ — potential vs current life?",
    "Which career, money and relationship signals appear on both hands?",
  ];
  const proInside = [
    { icon: "✋", title: "Both palms mapped together — your full story, not half a reading" },
    { icon: "🌿", title: "Life, Heart, Head & Fate lines — what they say about your path" },
    { icon: "⛰️", title: "Where your energy, confidence & vitality rise or drop" },
    { icon: "⚖️", title: "Born potential vs current life — left vs right palm truth" },
    { icon: "💼", title: "Clear career & money signals written on both hands" },
    isVideo
      ? { icon: "🎥", title: "Founder video on WhatsApp — both-hand reading explained for you" }
      : { icon: "📄", title: "Founder-reviewed PDF — kept in My Reports to re-read anytime" },
  ];

  useEffect(() => {
    const timers: ReturnType<typeof setTimeout>[] = [];
    (["left", "right"] as HandSide[]).forEach((side) => {
      const handScan = scans[side];
      setRevealedChecks((current) => ({ ...current, [side]: 0 }));
      if (!handScan) return;
      scanChecks(handScan).forEach((_, index) => {
        timers.push(setTimeout(() => {
          setRevealedChecks((current) => ({
            ...current,
            [side]: index + 1,
          }));
        }, 100 + index * 85));
      });
    });
    return () => timers.forEach(clearTimeout);
  }, [scans.left, scans.right]);

  async function choosePalm(side: HandSide) {
    if (busy) return;
    setError("");
    setUploadedToAdmin(false);
    try {
      const permission = await ImagePicker.requestMediaLibraryPermissionsAsync();
      if (!permission.granted) {
        throw new Error("Gallery permission is required to select a palm photo.");
      }
      const result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ImagePicker.MediaTypeOptions.Images,
        quality: 1,
        allowsEditing: false,
      });
      if (result.canceled || !result.assets[0]?.uri) return;
      const asset = result.assets[0];
      setScans((current) => ({ ...current, [side]: null }));
      setImageUris((current) => ({ ...current, [side]: asset.uri }));
      await runScan(asset, side);
    } catch (cause: unknown) {
      setPhase("idle");
      setError(cause instanceof Error ? cause.message : "Palm photo could not be opened.");
    }
  }

  async function palmImagePart(asset: ImagePicker.ImagePickerAsset): Promise<Blob | { uri: string; name: string; type: string }> {
    if (Platform.OS !== "web") {
      return {
        uri: asset.uri,
        name: "palm.jpg",
        type: asset.mimeType || "image/jpeg",
      };
    }
    const file = (asset as ImagePicker.ImagePickerAsset & { file?: File }).file;
    if (file) return file;
    if (asset.base64) {
      const res = await fetch(`data:${asset.mimeType || "image/jpeg"};base64,${asset.base64}`);
      return res.blob();
    }
    try {
      const res = await fetch(asset.uri);
      if (!res.ok) {
        throw new Error(`Gallery photo could not be read (${res.status}).`);
      }
      return res.blob();
    } catch (cause: unknown) {
      const msg = cause instanceof Error ? cause.message : String(cause);
      if (/Failed to fetch|NetworkError|Load failed/i.test(msg)) {
        throw new Error("Gallery photo could not be read in the browser. Pick a JPG/PNG from disk and try again.");
      }
      throw cause;
    }
  }

  async function persistAdminSession(
    nextScans: Record<HandSide, any>,
    purchaseId?: number,
    reportLang?: "en" | "hn" | "hi",
  ) {
    if (!nextScans.left || !nextScans.right) {
      throw new Error("Upload both left and right palm photos first.");
    }
    const response = await fetch(`${API_BASE}/api/palmistry/admin-upload`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(user?.api_key ? { "X-API-Key": user.api_key } : {}),
        ...(user?.id != null ? { "X-User-Id": String(user.id) } : {}),
      },
      body: JSON.stringify({
        session_id: sessionIdRef.current,
        writing_hand: writingHand,
        user_id: user?.id != null ? String(user.id) : undefined,
        cosmo_user_id: user?.cosmo_user_id || undefined,
        name: user?.name || undefined,
        urgent: priorityDelivery,
        plan: selectedPlan,
        lang: selectedPlan === "pdf" ? (reportLang || pdfLang) : "en",
        amount_inr: palmistryPlanTotalInr(selectedPlan, priorityDelivery),
        purchase_id: purchaseId || undefined,
        contact_method: selectedPlan === "vip" ? "whatsapp" : "my_reports",
        contact_value: selectedPlan === "vip" ? waDigits : "",
        whatsapp: selectedPlan === "vip" ? waDigits : "",
        left_palm_scan_result: nextScans.left,
        right_palm_scan_result: nextScans.right,
      }),
    });
    const body = await response.json().catch(() => null);
    if (!response.ok || body?.pdf_request?.ok === false) {
      const detail =
        (typeof body?.error?.message === "string" && body.error.message) ||
        (typeof body?.pdf_request?.error === "string" && body.pdf_request.error) ||
        (typeof body?.production_validation?.user_message === "string" && body.production_validation.user_message) ||
        (typeof body?.error === "string" && body.error) ||
        "";
      throw new Error(
        detail || `Could not send palm data to admin (${response.status}).`,
      );
    }
    const orderId = body?.pdf_request?.order_id || body?.order_id;
    if (!orderId) {
      throw new Error(
        "Order was not queued for admin (missing order_id). Check API proxy points to https://admin.coosmic.icu.",
      );
    }
    const publicOrderId =
      (typeof body?.pdf_request?.public_order_id === "string" && body.pdf_request.public_order_id) ||
      (typeof body?.public_order_id === "string" && body.public_order_id) ||
      "";
    return { ...body, order_id: orderId, public_order_id: publicOrderId };
  }

  async function runScan(asset: ImagePicker.ImagePickerAsset, expectedSide: HandSide) {
    setPhase("uploading");
    const form = new FormData();
    const imagePart = await palmImagePart(asset);
    if (Platform.OS === "web") {
      form.append("image", imagePart as Blob, "palm.jpg");
    } else {
      form.append("image", imagePart as any);
    }
    form.append("hand_side", expectedSide);
    form.append("writing_hand", writingHand);
    form.append("session_id", sessionIdRef.current);

    setPhase("scanning");
    const apiBase = API_BASE;
    let scanResponse: Response;
    try {
      scanResponse = await fetch(`${apiBase}/api/palm-scan`, {
        method: "POST",
        body: form,
      });
    } catch (cause: unknown) {
      const msg = cause instanceof Error ? cause.message : String(cause);
      throw new Error(
        /Failed to fetch|NetworkError|Load failed/i.test(msg)
          ? `Could not reach palm scan API at ${apiBase}. Check the Network tab for /api/palm-scan.`
          : msg,
      );
    }
    const scanBody = await scanResponse.json().catch(() => null);
    if (!scanBody?.schema_version) {
      const message =
        scanBody?.error?.message
        || scanBody?.production_validation?.user_message
        || scanBody?.quality?.issues?.[0]?.message
        || scanBody?.validation?.issues?.[0]?.message;
      if (scanResponse.status === 404) {
        throw new Error(
          `Palm scan API not found (404) on hosted API. ` +
          `Deploy palm-scan to VPS: .\\scripts\\deploy-palm-scan-vps.ps1 ` +
          `then check https://admin.coosmic.icu/api/healthz → palm_scan:true`,
        );
      }
      throw new Error(message || `Palm scan failed (${scanResponse.status}).`);
    }
    const validation = scanBody.production_validation;
    if (validation?.status === "rejected" && scanBody?.hand?.status !== "detected") {
      setError(validation.user_message || "Photo quality low — retake recommended. Partial results shown below.");
    } else {
      setError("");
    }
    const detectedSide = scanBody.hand?.side || scanBody.hand?.handedness;
    const stamped = {
      ...scanBody,
      hand: {
        ...(scanBody.hand || {}),
        detector_side: detectedSide || "unknown",
        requested_hand_side: expectedSide,
      },
    };
    setScans((current) => ({ ...current, [expectedSide]: stamped }));
    setUploadedToAdmin(false);
    setPhase("done");
  }

  async function completePaidUpload(
    purchaseId?: number,
    reportLang?: "en" | "hn" | "hi",
  ) {
    setError("");
    try {
      setPhase("submitting");
      const placed = await persistAdminSession(scans, purchaseId, reportLang);
      setUploadedToAdmin(true);
      setPhase("done");
      const publicId =
        (typeof placed?.public_order_id === "string" && placed.public_order_id.trim()) ||
        "";
      const uuid =
        (typeof placed?.order_id === "string" && placed.order_id.trim()) || "";
      const displayOrderId = publicId || (uuid ? uuid.slice(0, 8).toUpperCase() : "");
      const isVid = selectedPlan === "vip";
      const userName = (user?.name || "You").trim() || "You";
      try {
        await registerPendingMyReport(user?.id, {
          kind: "palmistry",
          title: isVid
            ? `${userName} — Video (WhatsApp)`
            : `${userName} — Palmistry Report`,
          subtitle: displayOrderId ? `Order ${displayOrderId}` : "Preparing…",
          orderId: uuid || undefined,
          publicOrderId: publicId || undefined,
          etaLabel: palmistryPlanEtaLabel(selectedPlan, priorityDelivery),
          deliverable: isVid ? "video" : "report",
        });
      } catch {
        /* ignore — success modal still shows */
      }
      setPreparingBanner({
        plan: selectedPlan,
        priority: priorityDelivery,
        orderId: displayOrderId || undefined,
      });
    } catch (cause: unknown) {
      setPhase("done");
      const msg = cause instanceof Error ? cause.message : "Could not upload both palm scans.";
      setError(msg);
      if (Platform.OS === "web") window.alert(msg);
      else Alert.alert("Upload failed", msg);
    }
  }

  async function startPalmistryCheckout(reportLang?: "en" | "hn" | "hi") {
    const label =
      selectedPlan === "vip"
        ? "Palmistry VIP Video Explanation"
        : "Palmistry Pro Report";
    await gatePalmistryAfterReady({
      user,
      plan: selectedPlan,
      urgent: priorityDelivery,
      amountInr: orderTotalInr,
      label,
      sessionId: sessionIdRef.current,
      writingHand,
      contactValue: selectedPlan === "vip" ? waDigits : undefined,
      lang: selectedPlan === "pdf" ? (reportLang || pdfLang) : undefined,
      leftScan: scans.left,
      rightScan: scans.right,
      bypassCheckout: PALMISTRY_CHECKOUT_CONFIG.bypassCheckoutForTesting,
      onEntitled: (purchaseId) => {
        void completePaidUpload(purchaseId, reportLang || pdfLang);
      },
    });
  }

  async function uploadBothHandsToAdmin() {
    if (busy) return;
    if (user?.id == null || !user?.api_key) {
      const msg = "Palmistry order ke liye pehle login karo, phir pay karke upload karo.";
      setError(msg);
      if (Platform.OS === "web") window.alert(msg);
      else Alert.alert("Login required", msg);
      return;
    }
    if (selectedPlan === "vip" && waDigits.length !== 10) {
      const msg = "Video explanation ke liye 10-digit WhatsApp number dalo.";
      setError(msg);
      if (Platform.OS === "web") window.alert(msg);
      else Alert.alert("WhatsApp number", msg);
      return;
    }
    if (!scans.left || !scans.right) {
      const msg = "Upload both left and right palm photos first, then tap Upload to Admin.";
      setError(msg);
      if (Platform.OS === "web") window.alert(msg);
      else Alert.alert("Both palms needed", msg);
      return;
    }
    const failedHands = (["left", "right"] as HandSide[]).filter((side) => !scanReadyForAdmin(scans[side]));
    if (failedHands.length) {
      const first = scans[failedHands[0]];
      const msg =
        productionValidation(first)?.user_message
        || "One or more palm scans failed validation. Retake the rejected hand photo before uploading to admin.";
      setError(msg);
      if (Platform.OS === "web") window.alert(msg);
      else Alert.alert("Validation failed", msg);
      return;
    }

    // PDF report only — ask language before Razorpay.
    if (selectedPlan === "pdf") {
      setLangOpen(true);
      return;
    }
    await startPalmistryCheckout();
  }

  useFocusEffect(
    useCallback(() => {
      if (!consumePalmistryPaidReady()) return;
      const pending = getPendingPalmistryCheckout();
      if (pending?.urgent != null) setPriorityDelivery(pending.urgent);
      if (pending?.plan) setSelectedPlan(pending.plan);
      if (pending?.contactValue) setWhatsapp(pending.contactValue);
      if (pending?.writingHand) setWritingHand(pending.writingHand);
      if (pending?.lang) setPdfLang(pending.lang);
      if (pending?.sessionId) sessionIdRef.current = pending.sessionId;
      if (pending?.leftScan && pending?.rightScan) {
        setScans({
          left: pending.leftScan as any,
          right: pending.rightScan as any,
        });
      }
      void (async () => {
        const nextScans =
          pending?.leftScan && pending?.rightScan
            ? { left: pending.leftScan as any, right: pending.rightScan as any }
            : scans;
        if (!nextScans.left || !nextScans.right) {
          setError("Palm scans missing after payment. Please re-upload both palms.");
          return;
        }
        setError("");
        try {
          setPhase("submitting");
          const placed = await persistAdminSession(
            nextScans,
            pending?.purchaseId,
            pending?.lang || pdfLang,
          );
          setUploadedToAdmin(true);
          setPhase("done");
          const publicId =
            (typeof placed?.public_order_id === "string" && placed.public_order_id.trim()) ||
            "";
          const uuid =
            (typeof placed?.order_id === "string" && placed.order_id.trim()) || "";
          const displayOrderId = publicId || (uuid ? uuid.slice(0, 8).toUpperCase() : "");
          const isVid = (pending?.plan || selectedPlan) === "vip";
          const userName = (user?.name || "You").trim() || "You";
          try {
            await registerPendingMyReport(user?.id, {
              kind: "palmistry",
              title: isVid
                ? `${userName} — Video (WhatsApp)`
                : `${userName} — Palmistry Report`,
              subtitle: displayOrderId ? `Order ${displayOrderId}` : "Preparing…",
              orderId: uuid || undefined,
              publicOrderId: publicId || undefined,
              etaLabel: palmistryPlanEtaLabel(
                pending?.plan || selectedPlan,
                pending?.urgent ?? priorityDelivery,
              ),
              deliverable: isVid ? "video" : "report",
            });
          } catch {
            /* ignore */
          }
          setPreparingBanner({
            plan: pending?.plan || selectedPlan,
            priority: pending?.urgent ?? priorityDelivery,
            orderId: displayOrderId || undefined,
          });
        } catch (cause: unknown) {
          setPhase("done");
          const msg = cause instanceof Error ? cause.message : "Could not upload both palm scans.";
          setError(msg);
          if (Platform.OS === "web") window.alert(msg);
          else Alert.alert("Upload failed", msg);
        }
      })();
    }, []),
  );

  const phaseText = {
    idle: "",
    uploading: "Uploading palm photo…",
    scanning: "Detecting hand, landmarks and palm lines…",
    submitting: "Sending both palm scans to admin…",
    done: "",
  }[phase];

  const themeProps = {
    text: isBasic ? S.title : C.text,
    textMuted: isBasic ? S.muted : C.textMuted,
    bgCard: isBasic ? S.card : C.bgCard,
    bgCard2: isBasic ? S.card2 : C.bgCard2,
    border: isBasic ? S.border : C.border,
  };

  function renderWritingHandSelector(cardBg = themeProps.bgCard, cardBorder = themeProps.border) {
    return (
      <View style={[s.setupCard, { backgroundColor: cardBg, borderColor: cardBorder }]}>
        <Text style={[s.setupLabel, { color: themeProps.text }]}>Which hand do you use for writing?</Text>
        <View style={s.segmentRow}>
          {(["left", "right"] as HandSide[]).map((side) => (
            <Pressable
              key={side}
              disabled={busy}
              onPress={() => {
                setWritingHand(side);
                setUploadedToAdmin(false);
              }}
              style={[
                s.segment,
                {
                  borderColor: writingHand === side ? accent : cardBorder,
                  backgroundColor: writingHand === side ? `${accent}22` : themeProps.bgCard2,
                },
              ]}
            >
              <Text style={[s.segmentText, { color: writingHand === side ? accent : themeProps.textMuted }]}>
                {side === "left" ? "Left" : "Right"}
              </Text>
            </Pressable>
          ))}
        </View>
      </View>
    );
  }

  function renderProgress() {
    if (!busy) return null;
    return (
      <View style={[s.progress, { backgroundColor: themeProps.bgCard, borderColor: themeProps.border }]}>
        <ActivityIndicator color={accent} />
        <Text style={[s.progressText, { color: themeProps.textMuted }]}>{phaseText}</Text>
      </View>
    );
  }

  function renderError() {
    if (!error) return null;
    const rejected =
      scans.left?.production_validation?.status === "rejected"
      || scans.right?.production_validation?.status === "rejected";
    return (
      <View style={[s.errorBox, { backgroundColor: themeProps.bgCard, borderColor: rejected ? "#fbbf2444" : "#ef444466" }]}>
        <Feather name="alert-circle" size={17} color={rejected ? "#fbbf24" : "#f87171"} />
        <Text style={[s.errorText, { color: rejected ? "#fde68a" : "#fca5a5" }]}>{error}</Text>
      </View>
    );
  }

  function renderScanResults(sides: HandSide[]) {
    return sides.map((side) => {
      const handScan = scans[side];
      const imageUri = imageUris[side];
      if (!handScan || !imageUri) return null;
      const checks = scanChecks(handScan).slice(0, revealedChecks[side]);
      return (
        <FadeInView delay={80} key={side}>
          <LivePalmScanView
            imageUri={imageUri}
            scan={handScan}
            handLabel={`${side === "left" ? "Left" : "Right"} · ${side === writingHand ? "writing hand" : "other hand"}`}
            showDebugUI={SHOW_PALM_SCAN_DEBUG}
            theme={themeProps}
            onRetake={() => void choosePalm(side)}
            onContinue={() => {
              if (Platform.OS === "web") {
                window.alert("Palm reading interpretation uses the same canonical scan data.");
              } else {
                Alert.alert(
                  "Palm Reading",
                  "Interpretation will use the same canonical detection data from this scan.",
                );
              }
            }}
          />
          {SHOW_PALM_SCAN_DEBUG ? (
            <View style={[s.checklist, { backgroundColor: themeProps.bgCard2, marginTop: 8 }]}>
              <Text style={[s.checklistTitle, { color: themeProps.text }]}>Detection checklist</Text>
              {checks.map((item) => {
                const color = item.status === "complete" ? "#34d399" : item.status === "attention" ? "#fbbf24" : themeProps.textMuted;
                const icon = item.status === "complete" ? "check-circle" : item.status === "attention" ? "alert-circle" : "minus-circle";
                return (
                  <View key={item.id} style={s.checkRow}>
                    <Feather name={icon} size={17} color={color} />
                    <View style={{ flex: 1 }}>
                      <Text style={[s.checkLabel, { color: themeProps.text }]}>{item.label}</Text>
                      <Text style={[s.checkDetail, { color: themeProps.textMuted }]}>{item.detail}</Text>
                    </View>
                  </View>
                );
              })}
            </View>
          ) : null}
        </FadeInView>
      );
    });
  }

  return (
    <View style={[s.root, Platform.OS === "web" ? { height: "100%" as any, maxHeight: "100%" as any } : null, { backgroundColor: isBasic ? S.page : C.bg }]}>
      <View style={StyleSheet.absoluteFill} pointerEvents="none">
        {isBasic ? (
          <LinearGradient colors={S.pageGrad} style={StyleSheet.absoluteFill} />
        ) : (
          <>
            <LinearGradient colors={[`${accent}14`, C.bg, C.bg]} style={StyleSheet.absoluteFill} />
            <PremiumOrb color={accent} />
          </>
        )}
      </View>

      <LinearGradient
        colors={isBasic
          ? (C.isDark ? ["#115e59", "#134e4a", "transparent"] : ["#99f6e4", "#ecfdf5", "transparent"])
          : [`${accent}24`, `${accent}08`, "transparent"]}
        style={[s.headerBar, { paddingTop: topPad + 8, borderBottomColor: isBasic ? S.border : `${accent}22` }]}
      >
        <Pressable
          onPress={() => router.back()}
          style={({ pressed }) => [ui.glassBtn, { opacity: pressed ? 0.75 : 1, backgroundColor: isBasic ? (C.isDark ? "rgba(15,23,42,0.55)" : "rgba(255,255,255,0.7)") : undefined }]}
        >
          <Feather name="arrow-left" size={20} color={isBasic ? S.title : C.textMuted} />
        </Pressable>
        <View style={{ flex: 1 }}>
          <Text style={[ui.headerBadge, { color: isBasic ? (C.isDark ? "#5eead4" : "#0f766e") : accent }]}>
            {tab === "basic" ? "PALMISTRY BASIC" : "PALMISTRY PRO"}
          </Text>
          <Text style={[s.headerTitle, { color: isBasic ? S.title : C.text }]}>{t.mdPalmistryTitle}</Text>
          <Text style={[s.headerSub, { color: isBasic ? S.body : C.textMuted }]}>{t.mdPalmistrySub}</Text>
        </View>
        <View style={{ width: 40 }} />
      </LinearGradient>

      <ScrollView
        style={s.scroll}
        showsVerticalScrollIndicator={false}
        nestedScrollEnabled
        keyboardShouldPersistTaps="handled"
        contentContainerStyle={[s.content, { paddingBottom: botPad + 120, flexGrow: 1 }]}
      >
        <FadeInView delay={staggerDelay(1)} resetKey={tab}>
          <View style={[ui.tabBarPremium, { backgroundColor: isBasic ? S.card : C.bgCard2, borderColor: isBasic ? S.border : `${accent}33` }]}>
            {([
              { key: "basic" as const, icon: "maximize" as const, label: t.km_basic, tabAccent: BASIC_ACCENT },
              { key: "pro" as const, icon: "file-text" as const, label: t.vu_tabPro, tabAccent: PRO_ACCENT },
            ]).map((m) => {
              const sel = tab === m.key;
              const idle = isBasic ? S.body : C.textMuted;
              return (
                <Pressable
                  key={m.key}
                  onPress={() => { setTab(m.key); Haptics.selectionAsync(); }}
                  style={({ pressed }) => [
                    ui.tabBtnPremium,
                    { borderColor: sel ? m.tabAccent : "transparent", transform: [{ scale: pressed ? 0.98 : 1 }] },
                  ]}
                >
                  {sel ? (
                    <LinearGradient
                      colors={[m.tabAccent, `${m.tabAccent}CC`]}
                      style={StyleSheet.absoluteFill}
                      start={{ x: 0, y: 0 }}
                      end={{ x: 1, y: 0 }}
                    />
                  ) : null}
                  <Feather name={m.icon} size={13} color={sel ? "#fff" : idle} />
                  <Text style={[s.tabTxt, { color: sel ? "#fff" : idle }]}>{m.label}</Text>
                </Pressable>
              );
            })}
          </View>
        </FadeInView>

        {tab === "basic" ? (
          <>
            <FadeInView delay={staggerDelay(2)} resetKey="basic">
              <View style={[ui.priceRibbon, { borderColor: S.border, backgroundColor: S.card }]}>
                <Feather name="maximize" size={14} color={BASIC_ACCENT} />
                <View style={{ flex: 1 }}>
                  <Text style={[bc.title, { color: S.title }]}>Free Palm Line Guide</Text>
                  <Text style={[bc.body, { color: S.muted, marginTop: 2 }]}>
                    Major lines · mounts · classic palmistry basics
                  </Text>
                </View>
              </View>
            </FadeInView>

            <FadeInView delay={staggerDelay(3)}>
              <View style={[bh.card, { backgroundColor: S.card, borderColor: S.border, overflow: "hidden" }]}>
                <LinearGradient colors={[`${BASIC_ACCENT}18`, "transparent"]} style={StyleSheet.absoluteFill} pointerEvents="none" />
                <Text style={[bc.label, { color: S.label }]}>Palmistry basics</Text>
                <Text style={[bc.title, { color: S.title }]}>
                  Learn what each major line means
                </Text>
                <Text style={[bc.body, { color: S.body }]}>
                  Life, Heart, Head aur Fate line — yahan free mein samjho. Photo upload aur full bilateral reading Pro mein hai.
                </Text>
              </View>
            </FadeInView>

            <Text style={[bc.body, { color: S.muted, marginTop: 2 }]}>Tap each card to expand</Text>

            {PALM_LINES.map((info, i) => (
              <PalmLineCard
                key={info.key}
                info={info}
                expanded={!!expandedLines[info.key]}
                onToggle={() => {
                  setExpandedLines((current) => ({ ...current, [info.key]: !current[info.key] }));
                  Haptics.selectionAsync();
                }}
                delay={staggerDelay(4 + i)}
              />
            ))}

            <FadeInView delay={staggerDelay(10)}>
              <BasicProCompare />
            </FadeInView>
            <FadeInView delay={staggerDelay(11)}>
              <BasicProTease onOpenPro={() => { setTab("pro"); Haptics.selectionAsync(); }} />
            </FadeInView>
          </>
        ) : (
          <View style={s.proBlock}>
            <FadeInView delay={0} resetKey="pro-hero">
              <View style={[np.heroCard, { borderColor: C.isDark ? "rgba(20,184,166,0.5)" : "rgba(20,184,166,0.35)" }]}>
                <LinearGradient
                  colors={C.isDark ? ["rgba(20,184,166,0.22)", "rgba(13,148,136,0.14)"] : ["rgba(20,184,166,0.1)", "rgba(13,148,136,0.06)"]}
                  style={StyleSheet.absoluteFill}
                />
                <Text style={np.heroEmoji}>✋</Text>
                <View style={{ flex: 1, gap: 2 }}>
                  <Text style={[np.heroTitle, { color: proTitleColor }]}>Palmistry Pro Report</Text>
                  <Text style={[np.heroLine, { color: proBodyColor }]} numberOfLines={2}>
                    #1 reason people order — both palms mapped, then a founder-reviewed reading.
                  </Text>
                </View>
              </View>
            </FadeInView>

            <FadeInView delay={staggerDelay(1)}>
              <View style={[np.card, { backgroundColor: proCardBg, borderColor: proBorder }]}>
                <Pressable
                  onPress={() => { setFounderExpanded(v => !v); Haptics.selectionAsync(); }}
                  style={np.founderHead}
                >
                  <LinearGradient colors={["#14b8a6", "#0d9488"]} style={np.founderPhoto}>
                    <Text style={np.founderInitials}>{FOUNDER_PROFILE.initials}</Text>
                  </LinearGradient>
                  <View style={{ flex: 1, gap: 2 }}>
                    <Text style={[np.founderName, { color: proTitleColor }]}>{FOUNDER_PROFILE.displayName}</Text>
                    <Text style={[np.founderRole, { color: proBodyColor }]} numberOfLines={founderExpanded ? 3 : 1}>
                      {founderExpanded ? FOUNDER_PROFILE.roleLine : "Personally prepared & reviewed"}
                    </Text>
                  </View>
                  <Feather name={founderExpanded ? "chevron-up" : "chevron-down"} size={18} color={C.isDark ? "#5eead4" : "#0f766e"} />
                </Pressable>
                <View style={np.founderChipRow}>
                  {["Founder-reviewed", "Saved in My Reports", "Secure payment"].map(b => (
                    <View key={b} style={[np.founderBulletChip, { borderColor: proBorder }]}>
                      <Feather name="check" size={10} color="#22c55e" />
                      <Text style={[np.founderBulletTxt, { color: proTitleColor }]} numberOfLines={1}>{b}</Text>
                    </View>
                  ))}
                </View>
              </View>
            </FadeInView>

            <FadeInView delay={staggerDelay(2)}>
              <ProProductPicker
                title="Choose how you want it"
                subtitle="Most people start with the PDF report. Video is a personal WhatsApp explanation."
                selectedId={isVideo ? "vip" : "pdf"}
                onSelect={(id) => setSelectedPlan(id === "vip" ? "vip" : "pdf")}
                isDark={C.isDark}
                cardBg={proCardBg}
                border={proBorder}
                titleColor={proTitleColor}
                bodyColor={proBodyColor}
                accent={
                  isVideo
                    ? (C.isDark ? PRO_PICKER_ACCENTS.amberDark : PRO_PICKER_ACCENTS.amber)
                    : (C.isDark ? PRO_PICKER_ACCENTS.tealDark : PRO_PICKER_ACCENTS.teal)
                }
                options={[
                  {
                    id: "pdf",
                    emoji: "✋",
                    title: "Palmistry Pro Report",
                    hint: "Full PDF · saved in My Reports · re-read anytime",
                    priceLabel: `₹${PALMISTRY_PRO_PLANS.pdf.priceInr}`,
                    badge: "MOST POPULAR",
                  },
                  {
                    id: "vip",
                    emoji: "🎥",
                    title: "Personalized Video Explanation",
                    hint: "Founder explains on WhatsApp · no PDF included",
                    priceLabel: `₹${PALMISTRY_PRO_PLANS.vip.priceInr}`,
                    badge: "1:1 VIDEO",
                  },
                ]}
              />
            </FadeInView>

            <FadeInView delay={staggerDelay(3)}>
              <View style={[np.card, { backgroundColor: proCardBg, borderColor: proBorder }]}>
                <Text style={[np.sectionTitle, { color: proTitleColor }]}>Your Report Answers These 3 Questions</Text>
                <View style={np.coreQChipRow}>
                  {proAnswers.map((q, i) => (
                    <View key={q} style={[np.coreQChip, { borderColor: proBorder }]}>
                      <Text style={[np.coreQChipNum, { color: C.isDark ? "#5eead4" : "#0f766e" }]}>{i + 1}</Text>
                      <Text style={[np.coreQChipTxt, { color: proTitleColor }]} numberOfLines={1}>{q}</Text>
                    </View>
                  ))}
                </View>
              </View>
            </FadeInView>

            <FadeInView delay={staggerDelay(4)}>
              <View style={[np.card, { backgroundColor: proCardBg, borderColor: proBorder }]}>
                <Text style={[np.sectionTitle, { color: proTitleColor }]}>What's Inside Your Report</Text>
                <Text style={[np.reportSummary, { color: proBodyColor }]}>
                  6 answers that make the buy worth it
                </Text>
                <View style={np.reportChipRow}>
                  {proInside.map(sec => (
                    <View key={sec.title} style={[np.reportChip, { borderColor: proBorder }]}>
                      <Text style={np.reportChipEmoji}>{sec.icon}</Text>
                      <Text style={[np.reportChipTxt, { color: proTitleColor }]}>{sec.title}</Text>
                    </View>
                  ))}
                </View>
              </View>
            </FadeInView>

            <FadeInView delay={staggerDelay(5)}>
              <View style={[np.card, { backgroundColor: proCardBg, borderColor: proBorder }]}>
                <Text style={[np.sectionTitle, { color: proTitleColor }]}>Standard Delivery</Text>
                <Text style={[np.deliveryStandardLine, { color: proBodyColor }]} numberOfLines={2}>
                  {isVideo
                    ? `📱 WhatsApp · ${STANDARD_DELIVERY_ETA.toLowerCase()} · no PDF/report`
                    : `📁 My Reports · ${STANDARD_DELIVERY_ETA.toLowerCase()}`}
                </Text>
                <Pressable
                  onPress={() => { setPriorityDelivery(!priorityDelivery); Haptics.selectionAsync(); }}
                  style={[
                    np.deliveryPriorityRow,
                    {
                      borderColor: priorityDelivery ? (C.isDark ? "#f59e0b" : "#d97706") : proBorder,
                      backgroundColor: priorityDelivery
                        ? (C.isDark ? "rgba(245,158,11,0.08)" : "rgba(245,158,11,0.06)")
                        : "transparent",
                    },
                  ]}
                >
                  <View style={[np.priorityCheck, {
                    borderColor: priorityDelivery ? "#f59e0b" : proBorder,
                    backgroundColor: priorityDelivery ? "#f59e0b" : "transparent",
                  }]}>
                    {priorityDelivery ? <Feather name="check" size={10} color="#fff" /> : null}
                  </View>
                  <Text style={[np.deliveryPriorityTxt, { color: proTitleColor }]} numberOfLines={1}>
                    ⚡ Priority +₹{priorityFee} · within 12 hours
                  </Text>
                </Pressable>
                <Text style={[np.deliveryRefundNote, { color: proBodyColor }]} numberOfLines={2}>
                  {PRIORITY_GUARANTEE}
                </Text>
                <View style={[np.priceDivider, { backgroundColor: proBorder }]} />
                <Text style={[np.priceInline, { color: proTitleColor }]}>
                  <Text style={np.priceTotalTiny}>₹{orderTotalInr}</Text>
                  {priorityDelivery ? (
                    <Text style={[np.planIncludes, { color: proBodyColor }]}>
                      {" "}· includes Priority
                    </Text>
                  ) : null}
                </Text>
              </View>
            </FadeInView>

            {isVideo ? (
            <FadeInView delay={staggerDelay(6)}>
              <View style={[np.card, { backgroundColor: proCardBg, borderColor: proBorder }]}>
                <Text style={[np.sectionTitle, { color: proTitleColor }]}>WhatsApp number</Text>
                <Text style={[np.reportSummary, { color: proBodyColor }]}>
                  Personalized Video Explanation yahin bhejenge.
                </Text>
                <TextInput
                  value={whatsapp}
                  onChangeText={(v) => setWhatsapp(normalizeWhatsappDigits(v))}
                  keyboardType="phone-pad"
                  maxLength={10}
                  placeholder="10-digit WhatsApp number"
                  placeholderTextColor={proBodyColor}
                  style={[np.waInput, { color: proTitleColor, borderColor: proBorder }]}
                />
              </View>
            </FadeInView>
            ) : null}

            <FadeInView delay={staggerDelay(isVideo ? 7 : 6)}>
              <View style={[np.card, { backgroundColor: proCardBg, borderColor: proBorder }]}>
                <Text style={[np.sectionTitle, { color: proTitleColor }]}>Your palms</Text>
                <Text style={[np.reportSummary, { color: proBodyColor }]}>
                  {isVideo
                    ? "Left and right palm photos required for your WhatsApp video explanation."
                    : "Left and right palm photos required for your PDF report."}
                </Text>
                <View style={{ marginTop: 10 }}>{renderWritingHandSelector()}</View>
                <View style={[s.actions, { marginTop: 10 }]}>
                  {(["left", "right"] as HandSide[]).map((side) => (
                    <View key={side} style={[s.handCapture, { backgroundColor: C.bgCard, borderColor: C.border }]}>
                      <View style={s.handCaptureHead}>
                        {imageUris[side] ? (
                          <Image source={{ uri: imageUris[side] as string }} style={s.handThumb} />
                        ) : (
                          <Text style={s.handEmoji}>{side === "left" ? "🤚" : "✋"}</Text>
                        )}
                        <View style={{ flex: 1 }}>
                          <Text style={[s.handTitle, { color: C.text }]}>
                            {side === "left" ? "Left Hand" : "Right Hand"}
                          </Text>
                          <Text style={[s.actionSub, { color: C.textMuted }]}>
                            {side === writingHand ? "Writing hand" : "Other hand"}
                          </Text>
                          {scans[side]?.production_validation?.status === "rejected"
                            && scans[side]?.hand?.status !== "detected" ? (
                            <Text style={[s.actionSub, { color: "#f87171" }]}>
                              {scans[side]?.production_validation?.user_message || "Retake required"}
                            </Text>
                          ) : null}
                        </View>
                        {scans[side] ? <Feather name="check-circle" size={20} color="#34d399" /> : null}
                      </View>
                      <View style={s.captureButtons}>
                        <Pressable
                          disabled={busy}
                          onPress={() => void choosePalm(side)}
                          style={[s.captureButton, { backgroundColor: "#0f766e" }]}
                        >
                          <Feather name="upload" size={16} color="#fff" />
                          <Text style={s.captureButtonText}>Upload Palm Photo</Text>
                        </Pressable>
                      </View>
                    </View>
                  ))}
                </View>
                {renderProgress()}
                {renderError()}
              </View>
            </FadeInView>

            <Text style={[np.trustBar, { color: proBodyColor }]}>
              {isVideo
                ? "🔒 Secure Payment • Founder Reviewed • Delivered on WhatsApp"
                : "🔒 Secure Payment • Founder Reviewed • Delivered in My Reports"}
            </Text>

            <Pressable
              disabled={busy || uploadedToAdmin}
              onPress={() => void uploadBothHandsToAdmin()}
              style={({ pressed }) => [{
                borderRadius: 14,
                backgroundColor: PRO_ACCENT,
                paddingVertical: 14,
                paddingHorizontal: 16,
                alignItems: "center",
                opacity: pressed || busy || uploadedToAdmin ? 0.85 : 1,
              }]}
            >
              <Text style={{ color: "#111827", fontSize: 14, fontFamily: "Nunito_800ExtraBold", textAlign: "center" }}>
                {busy && phase === "submitting"
                  ? "Placing order…"
                  : uploadedToAdmin
                    ? "Order placed"
                    : `${isVideo ? "Get Personalized Video Explanation" : "Get My Report"} · ₹${orderTotalInr}`}
              </Text>
            </Pressable>

            {renderScanResults(["left", "right"])}

            <Modal transparent visible={langOpen} animationType="fade" onRequestClose={() => setLangOpen(false)}>
              <View style={{
                flex: 1,
                backgroundColor: "rgba(0,0,0,0.55)",
                alignItems: "center",
                justifyContent: "center",
                padding: 18,
              }}>
                <View style={{
                  width: "100%",
                  maxWidth: 420,
                  backgroundColor: C.isDark ? "#12161c" : "#ffffff",
                  borderColor: C.border,
                  borderWidth: 1,
                  borderRadius: 16,
                  padding: 14,
                  gap: 10,
                }}>
                  <Text style={{ color: C.text, fontFamily: "Nunito_800ExtraBold", fontSize: 16 }}>
                    Report ki language
                  </Text>
                  <Text style={{ color: C.textMuted, fontFamily: "Nunito_500Medium", fontSize: 12, lineHeight: 17 }}>
                    English, Hinglish, ya Hindi — jo select karoge, Palmistry Pro report usi language mein milegi.
                  </Text>
                  <View style={{ flexDirection: "row", gap: 10 }}>
                    {([
                      { id: "en" as const, label: "English" },
                      { id: "hn" as const, label: "Hinglish" },
                      { id: "hi" as const, label: "Hindi" },
                    ]).map((opt) => {
                      const active = pdfLang === opt.id;
                      return (
                        <Pressable
                          key={opt.id}
                          onPress={() => { setPdfLang(opt.id); Haptics.selectionAsync(); }}
                          style={{
                            flex: 1,
                            paddingVertical: 10,
                            borderRadius: 12,
                            borderWidth: 1.5,
                            borderColor: active ? PRO_ACCENT : C.border,
                            backgroundColor: active
                              ? (C.isDark ? "rgba(245,158,11,0.14)" : "rgba(245,158,11,0.1)")
                              : (C.isDark ? "#0e1318" : "#f8fafc"),
                            alignItems: "center",
                          }}
                        >
                          <Text style={{
                            color: active ? PRO_ACCENT : C.textMuted,
                            fontFamily: "Nunito_800ExtraBold",
                            fontSize: 12,
                          }}>
                            {opt.label}
                          </Text>
                        </Pressable>
                      );
                    })}
                  </View>
                  <View style={{ flexDirection: "row", gap: 10, marginTop: 6 }}>
                    <Pressable
                      onPress={() => setLangOpen(false)}
                      style={{
                        flex: 1,
                        paddingVertical: 11,
                        borderRadius: 12,
                        borderWidth: 1,
                        borderColor: C.border,
                        backgroundColor: C.isDark ? "#0e1318" : "#f1f5f9",
                        alignItems: "center",
                      }}
                    >
                      <Text style={{ color: C.textMuted, fontFamily: "Nunito_800ExtraBold" }}>Cancel</Text>
                    </Pressable>
                    <Pressable
                      onPress={() => {
                        setLangOpen(false);
                        void startPalmistryCheckout(pdfLang);
                      }}
                      style={{
                        flex: 1,
                        paddingVertical: 11,
                        borderRadius: 12,
                        backgroundColor: PRO_ACCENT,
                        alignItems: "center",
                      }}
                    >
                      <Text style={{ color: "#111827", fontFamily: "Nunito_800ExtraBold" }}>Continue</Text>
                    </Pressable>
                  </View>
                </View>
              </View>
            </Modal>

            <OrderSuccessModal
              visible={!!preparingBanner}
              onClose={() => setPreparingBanner(null)}
              onViewReports={
                (preparingBanner?.plan ?? "pdf") === "vip"
                  ? undefined
                  : () => {
                      setPreparingBanner(null);
                      router.push("/my-reports" as any);
                    }
              }
              title="Order Confirmed!"
              orderId={preparingBanner?.orderId}
              showPdfTrust={(preparingBanner?.plan ?? "pdf") !== "vip"}
              message={
                (preparingBanner?.plan ?? "pdf") === "vip"
                  ? "Please save your Order ID. A video explanation will be sent on WhatsApp — no PDF/report. It will be prepared after admin approval."
                  : "Please save your Order ID. Your report is being prepared — the PDF will appear in My Reports. Please wait a moment."
              }
              etaLabel={palmistryPlanEtaLabel(
                preparingBanner?.plan ?? "pdf",
                preparingBanner?.priority ?? false,
              )}
            />
          </View>
        )}
      </ScrollView>
    </View>
  );
}

const s = StyleSheet.create({
  root: { flex: 1 },
  scroll: { flex: 1, minHeight: 0 },
  proBlock: { gap: 12 },
  content: { paddingHorizontal: 16, gap: 12, paddingTop: 14 },
  headerBar: {
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
    paddingHorizontal: 16,
    paddingBottom: 14,
    borderBottomWidth: 1,
  },
  headerTitle: { fontSize: 17, fontFamily: "Nunito_800ExtraBold", letterSpacing: -0.2 },
  headerSub: { fontSize: 11.5, fontFamily: "Nunito_500Medium", marginTop: 1, letterSpacing: 0.1, lineHeight: 16 },
  tabTxt: { fontSize: 12, fontFamily: "Nunito_800ExtraBold", letterSpacing: 0.3 },
  setupCard: { borderWidth: 1, borderRadius: 18, padding: 15 },
  setupLabel: { fontSize: 13, fontFamily: "Nunito_700Bold", marginBottom: 8 },
  segmentRow: { flexDirection: "row", gap: 8 },
  segment: {
    flex: 1,
    minHeight: 42,
    borderWidth: 1,
    borderRadius: 12,
    alignItems: "center",
    justifyContent: "center",
    paddingHorizontal: 8,
  },
  segmentText: { fontSize: 11, fontFamily: "Nunito_700Bold", textAlign: "center" },
  actions: { gap: 10 },
  handCapture: { borderWidth: 1, borderRadius: 18, padding: 14, gap: 12 },
  handCaptureHead: { flexDirection: "row", alignItems: "center", gap: 11 },
  handThumb: { width: 52, height: 52, borderRadius: 12 },
  handEmoji: { width: 52, fontSize: 34, textAlign: "center" },
  handTitle: { fontSize: 14, fontFamily: "Nunito_700Bold" },
  captureButtons: { flexDirection: "row", gap: 8 },
  captureButton: {
    flex: 1,
    minHeight: 40,
    borderRadius: 11,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 7,
  },
  captureButtonText: { color: "#fff", fontSize: 12, fontFamily: "Nunito_700Bold" },
  compareButton: {
    minHeight: 52,
    borderRadius: 15,
    backgroundColor: "#0f766e",
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 9,
  },
  compareButtonText: { color: "#fff", fontSize: 14, fontFamily: "Nunito_700Bold" },
  actionWrap: { borderRadius: 16, overflow: "hidden" },
  actionPrimary: {
    minHeight: 68,
    borderRadius: 16,
    paddingHorizontal: 18,
    flexDirection: "row",
    alignItems: "center",
    gap: 13,
  },
  actionSecondary: {
    minHeight: 68,
    borderRadius: 16,
    borderWidth: 1,
    paddingHorizontal: 18,
    flexDirection: "row",
    alignItems: "center",
    gap: 13,
  },
  actionTitle: { color: "#fff", fontSize: 15, fontFamily: "Nunito_700Bold" },
  actionSub: { color: "rgba(255,255,255,0.72)", fontSize: 10, fontFamily: "Nunito_400Regular", marginTop: 2 },
  progress: {
    minHeight: 58,
    borderWidth: 1,
    borderRadius: 15,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 10,
    padding: 12,
  },
  progressText: { fontSize: 12, fontFamily: "Nunito_600SemiBold" },
  errorBox: {
    flexDirection: "row",
    alignItems: "flex-start",
    gap: 9,
    borderWidth: 1,
    borderRadius: 14,
    padding: 12,
  },
  errorText: { flex: 1, color: "#fca5a5", fontSize: 11, lineHeight: 16, fontFamily: "Nunito_500Medium" },
  result: { borderWidth: 1, borderRadius: 18, padding: 15, gap: 12 },
  resultHead: { flexDirection: "row", alignItems: "center", justifyContent: "space-between" },
  resultTitle: { fontSize: 16, fontFamily: "Nunito_700Bold" },
  resultBadge: { borderRadius: 10, paddingHorizontal: 8, paddingVertical: 4 },
  annotation: { width: "100%", height: 260, borderRadius: 14, backgroundColor: "rgba(0,0,0,0.15)" },
  metrics: { flexDirection: "row", gap: 8 },
  metric: { flex: 1, borderRadius: 12, paddingVertical: 10, alignItems: "center" },
  metricValue: { fontSize: 13, fontFamily: "Nunito_700Bold", textTransform: "capitalize" },
  metricLabel: { fontSize: 9, fontFamily: "Nunito_400Regular", marginTop: 2 },
  resultNote: { fontSize: 11, lineHeight: 17, fontFamily: "Nunito_500Medium" },
  readingText: { fontSize: 12, lineHeight: 19, fontFamily: "Nunito_400Regular" },
  checklist: { borderRadius: 14, padding: 12, gap: 10 },
  checklistTitle: { fontSize: 13, fontFamily: "Nunito_700Bold", marginBottom: 2 },
  checkRow: { flexDirection: "row", alignItems: "center", gap: 10 },
  checkLabel: { fontSize: 11, fontFamily: "Nunito_700Bold" },
  checkDetail: { fontSize: 9, lineHeight: 13, fontFamily: "Nunito_400Regular" },
  list: { gap: 10 },
  card: {
    flexDirection: "row",
    alignItems: "center",
    gap: 13,
    borderWidth: 1,
    borderRadius: 16,
    padding: 14,
  },
  icon: {
    width: 40,
    height: 40,
    borderRadius: 12,
    backgroundColor: "rgba(20,184,166,0.14)",
    alignItems: "center",
    justifyContent: "center",
  },
  cardText: { flex: 1 },
  cardTitle: { fontSize: 14, fontFamily: "Nunito_700Bold" },
  cardBody: { fontSize: 11, lineHeight: 16, fontFamily: "Nunito_400Regular", marginTop: 2 },
  notice: {
    flexDirection: "row",
    alignItems: "flex-start",
    gap: 10,
    borderWidth: 1,
    borderRadius: 15,
    padding: 14,
  },
  noticeText: { flex: 1, fontSize: 11, lineHeight: 17, fontFamily: "Nunito_400Regular" },
});

const bh = StyleSheet.create({
  card: { borderRadius: 18, borderWidth: 1, padding: 16, gap: 8 },
});

const np = StyleSheet.create({
  card: { borderRadius: 18, borderWidth: 1, padding: 16 },
  founderHead: { flexDirection: "row", alignItems: "center", gap: 10 },
  founderPhoto: { width: 40, height: 40, borderRadius: 20, alignItems: "center", justifyContent: "center", overflow: "hidden" },
  founderInitials: { color: "#fff", fontSize: 13, fontFamily: "Nunito_800ExtraBold" },
  founderName: { fontSize: 13.5, fontFamily: "Nunito_800ExtraBold" },
  founderRole: { fontSize: 11, fontFamily: "Nunito_500Medium", lineHeight: 15 },
  founderChipRow: { flexDirection: "row", flexWrap: "wrap", gap: 6, marginTop: 8 },
  founderBulletChip: { flexDirection: "row", alignItems: "center", gap: 4, paddingVertical: 4, paddingHorizontal: 8, borderRadius: 8, borderWidth: 1, maxWidth: "48%", flexGrow: 1 },
  founderBulletTxt: { fontSize: 10, fontFamily: "Nunito_700Bold", flexShrink: 1 },
  heroCard: { flexDirection: "row", alignItems: "center", gap: 8, paddingVertical: 10, paddingHorizontal: 12, borderRadius: 14, borderWidth: 1, overflow: "hidden" },
  heroEmoji: { fontSize: 22 },
  heroTitle: { fontSize: 14.5, fontFamily: "Nunito_800ExtraBold", lineHeight: 19 },
  heroLine: { fontSize: 11.5, fontFamily: "Nunito_500Medium", lineHeight: 16 },
  sectionTitle: { fontSize: 15, fontFamily: "Nunito_800ExtraBold", letterSpacing: -0.2 },
  coreQChipRow: { gap: 6, marginTop: 10 },
  coreQChip: { flexDirection: "row", alignItems: "center", gap: 8, paddingVertical: 7, paddingHorizontal: 10, borderRadius: 9, borderWidth: 1 },
  coreQChipNum: { fontSize: 11, fontFamily: "Nunito_800ExtraBold", width: 14 },
  coreQChipTxt: { flex: 1, fontSize: 12, fontFamily: "Nunito_700Bold" },
  reportSummary: { fontSize: 11, fontFamily: "Nunito_500Medium", marginTop: 2 },
  reportChipRow: { gap: 6, marginTop: 10 },
  reportChip: { flexDirection: "row", alignItems: "center", gap: 6, paddingVertical: 8, paddingHorizontal: 10, borderRadius: 8, borderWidth: 1, width: "100%" },
  reportChipEmoji: { fontSize: 12 },
  reportChipTxt: { flex: 1, fontSize: 11, fontFamily: "Nunito_700Bold", lineHeight: 15 },
  deliveryStandardLine: { fontSize: 11.5, fontFamily: "Nunito_500Medium", marginTop: 6 },
  deliveryPriorityRow: { flexDirection: "row", alignItems: "center", gap: 7, marginTop: 6, paddingVertical: 7, paddingHorizontal: 9, borderRadius: 9, borderWidth: 1 },
  deliveryPriorityTxt: { flex: 1, fontSize: 11, fontFamily: "Nunito_700Bold" },
  deliveryRefundNote: { fontSize: 10, fontFamily: "Nunito_500Medium", marginTop: 5, lineHeight: 14 },
  priorityCheck: { width: 16, height: 16, borderRadius: 4, borderWidth: 1.5, alignItems: "center", justifyContent: "center" },
  planCard: { marginTop: 10, borderRadius: 14, borderWidth: 1.5, padding: 12, overflow: "hidden" },
  vipBadgeRow: { flexDirection: "row", alignItems: "center", gap: 6, marginBottom: 8, flexWrap: "wrap" },
  vipBadge: { paddingHorizontal: 8, paddingVertical: 4, borderRadius: 7 },
  vipBadgeTxt: { color: "#fff", fontSize: 9, fontFamily: "Nunito_800ExtraBold", letterSpacing: 0.6 },
  vipTag: { paddingHorizontal: 7, paddingVertical: 3, borderRadius: 6, backgroundColor: "rgba(127,29,29,0.92)" },
  vipTagTxt: { color: "#fde68a", fontSize: 9, fontFamily: "Nunito_800ExtraBold", letterSpacing: 0.8 },
  planTop: { flexDirection: "row", alignItems: "center", gap: 10 },
  planTitle: { fontSize: 14, fontFamily: "Nunito_800ExtraBold" },
  planPrice: { fontSize: 20, fontFamily: "Nunito_800ExtraBold", marginTop: 2 },
  planDelivery: { fontSize: 12, fontFamily: "Nunito_700Bold", marginTop: 8, lineHeight: 18 },
  planIncludes: { fontSize: 11, fontFamily: "Nunito_500Medium", marginTop: 4, lineHeight: 16 },
  priceDivider: { height: 1, marginTop: 10, marginBottom: 8 },
  priceInline: { fontSize: 12, lineHeight: 17 },
  priceStrikeTiny: { fontSize: 12, fontFamily: "Nunito_600SemiBold", textDecorationLine: "line-through" },
  priceArrow: { fontSize: 12, fontFamily: "Nunito_500Medium", color: "rgba(148,163,184,0.9)" },
  priceTotalTiny: { fontSize: 14, fontFamily: "Nunito_800ExtraBold" },
  trustBar: { fontSize: 11, fontFamily: "Nunito_600SemiBold", textAlign: "center", lineHeight: 16, paddingHorizontal: 4 },
  waInput: { marginTop: 10, borderWidth: 1, borderRadius: 10, paddingHorizontal: 12, paddingVertical: 10, fontSize: 14, fontFamily: "Nunito_700Bold" },
});

const ui = StyleSheet.create({
  orb: {
    position: "absolute",
    top: -50,
    right: -30,
    width: 200,
    height: 200,
    borderRadius: 100,
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
    fontFamily: "Nunito_800ExtraBold",
    letterSpacing: 2,
    marginBottom: 2,
  },
  tabBarPremium: {
    flexDirection: "row",
    padding: 5,
    borderRadius: 16,
    borderWidth: 1,
    gap: 6,
    marginBottom: 4,
  },
  tabBtnPremium: {
    flex: 1,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 6,
    paddingVertical: 12,
    borderRadius: 12,
    borderWidth: 1.5,
    overflow: "hidden",
  },
  priceRibbon: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    paddingVertical: 10,
    paddingHorizontal: 14,
    borderRadius: 14,
    borderWidth: 1,
  },
});
