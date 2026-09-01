import { Feather } from "@expo/vector-icons";
import { LinearGradient } from "expo-linear-gradient";
import * as Haptics from "expo-haptics";
import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  ActivityIndicator,
  Alert,
  BackHandler,
  FlatList,
  Keyboard,
  Modal,
  Platform,
  Pressable,
  ScrollView,
  StatusBar,
  StyleSheet,
  Text,
  TextInput,
  Vibration,
  View,
} from "react-native";
import { AppKeyboardAvoidingView as KeyboardAvoidingView } from "@/components/AppKeyboardAvoidingView";
import AsyncStorage from "@react-native-async-storage/async-storage";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import Reanimated, {
  Easing as REasing,
  FadeIn,
  FadeInLeft,
  FadeInRight,
  ZoomIn,
  interpolate,
  useAnimatedStyle,
  useSharedValue,
  withDelay,
  withRepeat,
  withSequence,
  withTiming,
} from "react-native-reanimated";
import { FadeInView, staggerDelay } from "@/components/motion/FadeInView";
import { AcharyaTypingDots } from "@/components/AcharyaTypingDots";
import { CardsCarousel, type CardData } from "@/components/CardsCarousel";
import { MarkdownReply } from "@/components/MarkdownReply";
import { useC } from "@/context/ThemeContext";
import { needsProfileSetup, resolveNativeAskProfile, useUser } from "@/context/UserContext";
import { useT } from "@/hooks/useT";
import { getT } from "@/lib/i18n";
import { router, useFocusEffect, useLocalSearchParams } from "expo-router";
import { useTabBar } from "@/context/TabBarContext";

import { sanitizeAskAnswerForDisplay, askErrorToUserMessage } from "@/lib/askAnswerSanitize";
import { API_BASE, apiFetch, getApiBase, userAuthHeaders } from "@/lib/apiConfig";
import { INSTAGRAM_ANSWERS_ENABLED } from "@/lib/instagramAnswersFeature";
import { V3LiveChat } from "@/components/V3LiveChat";
import { presentV3ReadyNotification, setV3ReadyHandler } from "@/lib/notifications";
import {
  ASK_REPLY_LANG_OPTIONS,
  ASK_REPLY_LANG_STORAGE_KEY,
  askLangToApi,
  detectAskLangFromQuestion,
  loadAskReplyLang,
  type AskReplyLang,
} from "@/lib/askReplyLang";
import { ASK_V1_PACKS, formatAskV1Expiry, formatAskV1ExpiryLong, type AskV1PackId } from "@/lib/askV1PackBilling";
import {
  askV1WalletHasCredit,
  hasActiveAskV1Wallet,
  startAskV1PackPayment,
} from "@/lib/askV1PackCheckoutFlow";
import { archiveAskChatSession, listAskChatArchives } from "@/lib/askChatArchive";

/** Cosmic Intelligence V3 — live timed session packs */
const V3_LIVE_PACKS = [
  { id: "15", minutes: 15, priceInr: 399,  label: "15 min",  timer: "15:00", feel: "Quick clarity",   badge: null as null | "popular" | "best" },
  { id: "30", minutes: 30, priceInr: 699,  label: "30 min",  timer: "30:00", feel: "Most popular",    badge: "popular" as const },
  { id: "45", minutes: 45, priceInr: 999,  label: "45 min",  timer: "45:00", feel: "Deep session",    badge: null },
  { id: "60", minutes: 60, priceInr: 1299, label: "60 min",  timer: "60:00", feel: "Best value",      badge: "best" as const },
] as const;

/** Smaller chart payload for /api/ask — avoids proxy body limits; server needs planets + dashas. */
function slimKundliForAsk(k: Record<string, unknown>): Record<string, unknown> {
  const planets = Array.isArray(k.planets) ? k.planets : [];
  const dashas = Array.isArray(k.dashas) ? k.dashas : [];
  const kp = k.kp && typeof k.kp === "object" ? (k.kp as Record<string, unknown>) : null;
  return {
    name: k.name,
    ascendant: k.ascendant,
    ascendantDeg: k.ascendantDeg,
    nakshatra: k.nakshatra,
    nakshatraPada: k.nakshatraPada,
    moonSign: k.moonSign,
    moonLongitude: k.moonLongitude,
    sunSign: k.sunSign,
    currentDasha: k.currentDasha,
    planets,
    dashas: dashas.slice(0, 12),
    ...(kp
      ? {
          kp: {
            planets: kp.planets,
            cusps: kp.cusps,
            ayanamsa: kp.ayanamsa,
          },
        }
      : {}),
  };
}

interface Message {
  id: string;
  role: "user" | "assistant";
  text: string;
  loading?: boolean;
  streaming?: boolean;
  followUps?: string[];
  // DNA routing context — echoed in history so follow-ups stay on the
  // same specialist engine (domain / bucket / archetype).
  topic?: string;
  domain?: string;
  bucket?: string;
  archetype?: string;
  subject?: string;
  // P6: v2 multi-intent response — when present, the bubble renders a
  // swipeable cards carousel instead of a single MarkdownReply. `text` is
  // still populated with the legacy combined string so copy / regenerate
  // continue to work unchanged.
  cards?: CardData[];
  trimmedCount?: number;
  responseSchema?: "v2";
  // Phase 7.5: clarifier UX — server attaches this when its classifier
  // confidence was low. We render a banner + tappable refinement chips
  // BELOW the answer bubble (between bubble and followUps). Tapping a
  // chip sends that option text via the existing `send` flow → server
  // re-classifies the now-specific question. When absent or empty,
  // nothing renders (defensive — server can ship the field on/off via
  // PHASE75_CLARIFIER_ENABLED env without any client release).
  clarification?: { prompt: string; options: string[] };
  // Phase 2.5.11.6 — partner CTA. When the user asks about an existing
  // partner ("mere bf se shaadi hogi") but no partner profile is saved,
  // server returns this payload so we render an inline "Add partner
  // details" button below the bubble that opens profile-edit pre-set
  // to the right relation slot.
  partnerCta?: { label: string; relation: string };
  /** Fresh JSON answer — typewriter reveal before full markdown. */
  revealAnswer?: boolean;
}

const DEMO_MESSAGES: Message[] = [
  {
    id: "d1",
    role: "assistant",
    text: "Welcome. I'm Cosmic Intelligence — your personal Vedic chart analyst. Sharp, evidence-based answers from your unique birth chart. Career, marriage, health, money — ask anything.",
  },
  {
    id: "d2",
    role: "user",
    text: "How will my career shape up this year?",
  },
  {
    id: "d3",
    role: "assistant",
    text: "Personalized analysis aapki birth-chart se hota hai. Pehle quick kundli setup kar lo (1 minute) — phir exact timing, strengths aur risk areas mil jayenge.",
  },
];

const STARTERS = [
  "Mera love marriage hai ya arrange?",
  "Career growth kab milegi?",
  "Health kaisi rahegi?",
  "Paisa kab aayega?",
];

// ── Recent-Questions formatters ──────────────────────────────────────────
// `verdict_summary` is a structured tag emitted by the engine layer (e.g.
// "yellow_wait", "love_likely"). Map a small known set to user-friendly
// Hinglish labels; fall back to title-casing otherwise.
const VERDICT_LABELS: Record<string, string> = {
  "answered":         "Reply mila",
  "answered:career":  "Career update",
  "answered:love":    "Love update",
  "answered:marriage":"Marriage update",
  "answered:wealth":  "Dhan update",
  "answered:yoga":    "Yoga reading",
  "answered:dosh":    "Dosh reading",
  "answered:general": "Reply mila",
  "off_topic":        "Off-topic",
  "yellow_wait":      "Wait",
  "green_go":         "Auspicious",
  "red_avoid":        "Avoid",
  "love_likely":      "Love marriage",
  "arrange_likely":   "Arranged",
  "manglik":          "Manglik",
  "unstable":         "Unstable",
  "stable":           "Stable",
};
function prettyVerdict(raw: string): string {
  const v = (raw || "").trim().toLowerCase();
  if (v === "answered:health") return "Reply mila";
  if (VERDICT_LABELS[v]) return VERDICT_LABELS[v];
  // Generic fallback: drop "answered:" prefix and title-case rest.
  const clean = v.replace(/^answered:/, "").replace(/[_:]/g, " ");
  return clean ? clean.charAt(0).toUpperCase() + clean.slice(1) : "Reply mila";
}
function prettyAgo(iso: string): string {
  if (!iso) return "";
  const t = Date.parse(iso);
  if (Number.isNaN(t)) return "";
  const sec = Math.max(1, Math.floor((Date.now() - t) / 1000));
  if (sec < 60)        return "just now";
  if (sec < 3600)      return `${Math.floor(sec / 60)}m ago`;
  if (sec < 86400)     return `${Math.floor(sec / 3600)}h ago`;
  if (sec < 86400 * 7) return `${Math.floor(sec / 86400)}d ago`;
  return new Date(t).toLocaleDateString();
}

// ── Premium motion primitives ─────────────────────────────────────────────
// A small set of self-contained reanimated helpers used only by this screen.
// They are deliberately local (not in components/) so the Ask redesign owns
// its own polish without touching shared widgets.

/**
 * BusyPulseRing — expanding, fading ring used behind the "engine busy" icon
 * so the popup reads as a live, breathing signal instead of a static alert.
 */
function BusyPulseRing({ delayMs, color }: { delayMs: number; color: string }) {
  const p = useSharedValue(0);
  useEffect(() => {
    p.value = withDelay(
      delayMs,
      withRepeat(
        withTiming(1, { duration: 2200, easing: REasing.out(REasing.ease) }),
        -1,
        false,
      ),
    );
  }, [p, delayMs]);
  const st = useAnimatedStyle(() => ({
    transform: [{ scale: interpolate(p.value, [0, 1], [1, 2.4]) }],
    opacity: interpolate(p.value, [0, 0.2, 1], [0, 0.55, 0]),
  }));
  return (
    <Reanimated.View
      pointerEvents="none"
      style={[
        {
          position: "absolute",
          width: 74,
          height: 74,
          borderRadius: 37,
          borderWidth: 2,
          borderColor: color,
        },
        st,
      ]}
    />
  );
}

/** Gentle breathing scale for the busy icon itself. */
function BusyBreathingIcon({ children }: { children: React.ReactNode }) {
  const b = useSharedValue(0);
  useEffect(() => {
    b.value = withRepeat(
      withSequence(
        withTiming(1, { duration: 1100, easing: REasing.inOut(REasing.ease) }),
        withTiming(0, { duration: 1100, easing: REasing.inOut(REasing.ease) }),
      ),
      -1,
      false,
    );
  }, [b]);
  const st = useAnimatedStyle(() => ({
    transform: [{ scale: interpolate(b.value, [0, 1], [1, 1.12]) }],
  }));
  return <Reanimated.View style={st}>{children}</Reanimated.View>;
}

/**
 * GlowDot — a solid status dot wrapped in an expanding, fading "radar" ring
 * that pulses forever. Used for the header status / live indicators so they
 * read as a living, premium "online" signal instead of a static dot.
 */
function GlowDot({ color, size = 8 }: { color: string; size?: number }) {
  const progress = useSharedValue(0);
  useEffect(() => {
    progress.value = withRepeat(
      withTiming(1, { duration: 1800, easing: REasing.out(REasing.ease) }),
      -1,
      false,
    );
  }, [progress]);
  const ringStyle = useAnimatedStyle(() => ({
    transform: [{ scale: interpolate(progress.value, [0, 1], [1, 2.8]) }],
    opacity: interpolate(progress.value, [0, 0.15, 1], [0, 0.45, 0]),
  }));
  return (
    <View style={{ width: size, height: size, alignItems: "center", justifyContent: "center" }}>
      <Reanimated.View
        pointerEvents="none"
        style={[
          { position: "absolute", width: size, height: size, borderRadius: size / 2, backgroundColor: color },
          ringStyle,
        ]}
      />
      <View style={{ width: size, height: size, borderRadius: size / 2, backgroundColor: color }} />
    </View>
  );
}

/**
 * CardShimmer — a soft diagonal light bar that sweeps across a premium
 * gradient card every few seconds, giving a glossy, "alive" highlight.
 * Parent must have overflow:"hidden" (the mode cards do).
 */
function CardShimmer() {
  const x = useSharedValue(0);
  useEffect(() => {
    // Android: skip perpetual Reanimated sweep — multiple cards × loops = jank.
    if (Platform.OS === "android") return;
    x.value = withRepeat(
      withDelay(400, withTiming(1, { duration: 1100, easing: REasing.inOut(REasing.ease) })),
      -1,
      false,
    );
  }, [x]);
  const style = useAnimatedStyle(() => ({
    transform: [
      { translateX: interpolate(x.value, [0, 1], [-160, 420]) },
      { rotate: "20deg" },
    ],
    opacity: interpolate(x.value, [0, 0.25, 0.5, 0.75, 1], [0, 0.65, 0.9, 0.65, 0]),
  }));
  if (Platform.OS === "android") return null;
  return (
    <Reanimated.View
      pointerEvents="none"
      style={[
        { position: "absolute", top: -60, bottom: -60, width: 56, backgroundColor: "rgba(255,255,255,0.38)" },
        style,
      ]}
    />
  );
}

/**
 * PressScale — wraps tappable content in a spring-like scale + dim on press
 * for tactile, premium button feedback (replaces the flat opacity press).
 */
function PressScale({
  children,
  onPress,
  style,
  accessibilityLabel,
}: {
  children: React.ReactNode;
  onPress: () => void;
  style?: any;
  accessibilityLabel?: string;
}) {
  const scale = useSharedValue(1);
  const aStyle = useAnimatedStyle(() => ({ transform: [{ scale: scale.value }] }));
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={accessibilityLabel}
      onPressIn={() => { scale.value = withTiming(0.96, { duration: 90 }); }}
      onPressOut={() => { scale.value = withTiming(1, { duration: 160, easing: REasing.out(REasing.ease) }); }}
      onPress={onPress}
    >
      <Reanimated.View style={[aStyle, style]}>{children}</Reanimated.View>
    </Pressable>
  );
}

/** Soft breathing scale on hero "Cosmic Advance Intelligence" chip. */
function BreathingHeroBadge({
  children,
  style,
}: {
  children: React.ReactNode;
  style?: any;
}) {
  const pulse = useSharedValue(0);
  useEffect(() => {
    pulse.value = withRepeat(
      withSequence(
        withTiming(1, { duration: 1600, easing: REasing.inOut(REasing.ease) }),
        withTiming(0, { duration: 1600, easing: REasing.inOut(REasing.ease) }),
      ),
      -1,
      false,
    );
  }, [pulse]);
  const aStyle = useAnimatedStyle(() => ({
    transform: [{ scale: interpolate(pulse.value, [0, 1], [1, 1.035]) }],
    opacity: interpolate(pulse.value, [0, 1], [0.88, 1]),
  }));
  return <Reanimated.View style={[style, aStyle]}>{children}</Reanimated.View>;
}

/** Gentle vertical float for card icons (⚡ 💬 crosshair). */
function FloatIcon({
  children,
  delayMs = 0,
}: {
  children: React.ReactNode;
  delayMs?: number;
}) {
  const y = useSharedValue(0);
  useEffect(() => {
    y.value = withDelay(
      delayMs,
      withRepeat(
        withSequence(
          withTiming(1, { duration: 1800, easing: REasing.inOut(REasing.sin) }),
          withTiming(0, { duration: 1800, easing: REasing.inOut(REasing.sin) }),
        ),
        -1,
        false,
      ),
    );
  }, [delayMs, y]);
  const aStyle = useAnimatedStyle(() => ({
    transform: [{ translateY: interpolate(y.value, [0, 1], [0, -4]) }],
  }));
  return <Reanimated.View style={aStyle}>{children}</Reanimated.View>;
}

/** Soft glow pulse on MOST POWERFUL / MINUTE-ACCURATE pills. */
function PulsePill({
  children,
  style,
}: {
  children: React.ReactNode;
  style?: any;
}) {
  const glow = useSharedValue(0);
  useEffect(() => {
    glow.value = withRepeat(
      withSequence(
        withTiming(1, { duration: 1200, easing: REasing.inOut(REasing.ease) }),
        withTiming(0, { duration: 1200, easing: REasing.inOut(REasing.ease) }),
      ),
      -1,
      false,
    );
  }, [glow]);
  const aStyle = useAnimatedStyle(() => ({
    transform: [{ scale: interpolate(glow.value, [0, 1], [1, 1.06]) }],
    opacity: interpolate(glow.value, [0, 1], [0.85, 1]),
  }));
  return <Reanimated.View style={[style, aStyle]}>{children}</Reanimated.View>;
}

/** Soft ambient orbs behind the Ask landing — living cosmic field. */
function AskAmbientField({ accent }: { accent: string }) {
  const a = useSharedValue(0);
  const b = useSharedValue(0);
  useEffect(() => {
    if (Platform.OS === "android") return;
    a.value = withRepeat(
      withSequence(
        withTiming(1, { duration: 4200, easing: REasing.inOut(REasing.ease) }),
        withTiming(0, { duration: 4200, easing: REasing.inOut(REasing.ease) }),
      ),
      -1,
      false,
    );
    b.value = withDelay(
      900,
      withRepeat(
        withSequence(
          withTiming(1, { duration: 5200, easing: REasing.inOut(REasing.ease) }),
          withTiming(0, { duration: 5200, easing: REasing.inOut(REasing.ease) }),
        ),
        -1,
        false,
      ),
    );
  }, [a, b]);
  const orbA = useAnimatedStyle(() => ({
    opacity: interpolate(a.value, [0, 1], [0.18, 0.38]),
    transform: [
      { translateY: interpolate(a.value, [0, 1], [0, -18]) },
      { scale: interpolate(a.value, [0, 1], [1, 1.12]) },
    ],
  }));
  const orbB = useAnimatedStyle(() => ({
    opacity: interpolate(b.value, [0, 1], [0.12, 0.32]),
    transform: [
      { translateY: interpolate(b.value, [0, 1], [8, -10]) },
      { scale: interpolate(b.value, [0, 1], [1, 1.08]) },
    ],
  }));
  if (Platform.OS === "android") return null;
  return (
    <View pointerEvents="none" style={StyleSheet.absoluteFillObject}>
      <Reanimated.View
        style={[
          {
            position: "absolute",
            top: 40,
            right: -40,
            width: 180,
            height: 180,
            borderRadius: 90,
            backgroundColor: accent,
          },
          orbA,
        ]}
      />
      <Reanimated.View
        style={[
          {
            position: "absolute",
            top: 220,
            left: -50,
            width: 160,
            height: 160,
            borderRadius: 80,
            backgroundColor: "#f59e0b",
          },
          orbB,
        ]}
      />
      <Reanimated.View
        style={[
          {
            position: "absolute",
            top: 420,
            right: 10,
            width: 120,
            height: 120,
            borderRadius: 60,
            backgroundColor: "#10b981",
          },
          orbA,
        ]}
      />
    </View>
  );
}

/** Subtle continuous opacity shimmer on the headline. */
function LivingHeadline({
  children,
  style,
}: {
  children: React.ReactNode;
  style?: any;
}) {
  const v = useSharedValue(0);
  useEffect(() => {
    v.value = withRepeat(
      withSequence(
        withTiming(1, { duration: 2200, easing: REasing.inOut(REasing.ease) }),
        withTiming(0, { duration: 2200, easing: REasing.inOut(REasing.ease) }),
      ),
      -1,
      false,
    );
  }, [v]);
  const aStyle = useAnimatedStyle(() => ({
    opacity: interpolate(v.value, [0, 1], [0.88, 1]),
  }));
  return <Reanimated.Text style={[style, aStyle]}>{children}</Reanimated.Text>;
}

/** Typewriter reveal — clearly visible “alive engine” moment. */
function TypewriterHeadline({
  text,
  style,
  cursorColor = "#a78bfa",
}: {
  text: string;
  style?: any;
  cursorColor?: string;
}) {
  const [shown, setShown] = useState("");
  const blink = useSharedValue(1);
  useEffect(() => {
    setShown("");
    let i = 0;
    const id = setInterval(() => {
      i += 1;
      setShown(text.slice(0, i));
      if (i >= text.length) clearInterval(id);
    }, 38);
    return () => clearInterval(id);
  }, [text]);
  useEffect(() => {
    blink.value = withRepeat(
      withSequence(
        withTiming(0, { duration: 420 }),
        withTiming(1, { duration: 420 }),
      ),
      -1,
      false,
    );
  }, [blink]);
  const cursorStyle = useAnimatedStyle(() => ({ opacity: blink.value }));
  return (
    <Text style={style}>
      {shown}
      <Reanimated.Text style={[{ color: cursorColor, fontWeight: "300" }, cursorStyle]}>
        |
      </Reanimated.Text>
    </Text>
  );
}

/** One-by-one reveal for full Ask answers (JSON path — not SSE deltas). */
function TypewriterAnswer({
  text,
  onComplete,
}: {
  text: string;
  onComplete?: () => void;
}) {
  const C = useC();
  const [shown, setShown] = useState("");
  const [done, setDone] = useState(false);
  const blink = useSharedValue(1);
  useEffect(() => {
    setShown("");
    setDone(false);
    let i = 0;
    const step = text.length > 900 ? 3 : text.length > 450 ? 2 : 1;
    const ms = text.length > 900 ? 22 : 32;
    const id = setInterval(() => {
      i += step;
      setShown(text.slice(0, i));
      if (i >= text.length) {
        clearInterval(id);
        setDone(true);
        onComplete?.();
      }
    }, ms);
    return () => clearInterval(id);
  }, [text, onComplete]);
  useEffect(() => {
    blink.value = withRepeat(
      withSequence(
        withTiming(0, { duration: 420 }),
        withTiming(1, { duration: 420 }),
      ),
      -1,
      false,
    );
  }, [blink]);
  const cursorStyle = useAnimatedStyle(() => ({ opacity: blink.value }));
  if (done) {
    return <MarkdownReply text={text} />;
  }
  return (
    <Text style={{ color: C.textMid, fontSize: 14.5, lineHeight: 21 }}>
      {shown}
      <Reanimated.Text style={[{ color: "#a78bfa", fontWeight: "300" }, cursorStyle]}>
        |
      </Reanimated.Text>
    </Text>
  );
}

/** Shown on the thinking bubble while the server generates a full JSON answer. */
const ASK_WAIT_STATUS = [
  "Aapki kundli padh raha hoon…",
  "Dasha aur grah dekh raha hoon…",
  "Cosmic Intelligence jawab taiyar kar rahi hai…",
];

const ASK_EXAMPLE_QUESTIONS = [
  "When is the best time to switch jobs?",
  "Is this marriage timing favourable?",
  "Which months look strong for money?",
  "How is my health dasha this year?",
];

function RotatingExamples({ color, textColor }: { color: string; textColor: string }) {
  const [idx, setIdx] = useState(0);
  const fade = useSharedValue(1);
  useEffect(() => {
    const id = setInterval(() => {
      fade.value = withTiming(0, { duration: 200 });
      setTimeout(() => {
        setIdx((v) => (v + 1) % ASK_EXAMPLE_QUESTIONS.length);
        fade.value = withTiming(1, { duration: 280 });
      }, 210);
    }, 3000);
    return () => clearInterval(id);
  }, [fade]);
  const aStyle = useAnimatedStyle(() => ({ opacity: fade.value }));
  return (
    <View style={{ marginTop: 6, alignItems: "center" }}>
      <Text style={{ fontSize: 10, fontWeight: "800", color, letterSpacing: 0.8, marginBottom: 3, opacity: 0.9 }}>
        TRY ASKING
      </Text>
      <Reanimated.Text
        style={[
          {
            fontSize: 13,
            fontWeight: "700",
            color: textColor,
            lineHeight: 18,
            minHeight: 20,
            textAlign: "center",
          },
          aStyle,
        ]}
        numberOfLines={1}
      >
        “{ASK_EXAMPLE_QUESTIONS[idx]}”
      </Reanimated.Text>
    </View>
  );
}

export default function AskScreen() {
  const insets = useSafeAreaInsets();
  const C = useC();
  const { kundli, birthData, user, primaryProfileId, profiles, syncProfilesNow } = useUser();
  const t = useT();
  const routeParams = useLocalSearchParams<{ resumeV3?: string | string[] }>();
  const androidSB = StatusBar.currentHeight ?? 24;
  const topPad = Platform.OS === "web" ? 67 : Platform.OS === "android" ? Math.max(insets.top, androidSB) : insets.top;
  const botPad = Platform.OS === "web" ? 34 : insets.bottom;

  const nativeAskProfile = useMemo(
    () => resolveNativeAskProfile(profiles, primaryProfileId),
    [profiles, primaryProfileId],
  );

  const askChart = useMemo(() => {
    if (nativeAskProfile?.kundli?.planets?.length) return nativeAskProfile.kundli;
    if (kundli?.planets?.length) return kundli;
    return null;
  }, [nativeAskProfile, kundli]);

  const askBirthData = useMemo(
    () => nativeAskProfile?.birthData ?? birthData,
    [nativeAskProfile, birthData],
  );

  const chartReady = (askChart?.planets?.length ?? 0) > 0;
  const showDemo = !chartReady;

  // ── Tab bar height (matches CustomTabBar.BAR_H = 84). Used for both
  // the input row's resting paddingBottom (clear the tab bar) and the
  // KeyboardAvoidingView's verticalOffset on iOS (so the keyboard pushes
  // the input row to sit FLUSH above the keyboard top, not above the
  // tab bar top — which was the half-screen bug).
  const TAB_BAR_HEIGHT = 84;

  // ── Track keyboard visibility. When kb is up we collapse the input
  // row's bottom padding (no tab-bar gap needed — keyboard occupies
  // that space) AND hide starter chips so the chat thread stays
  // readable instead of being squished into "half a screen".
  const [kbVisible, setKbVisible] = useState(false);
  useEffect(() => {
    const showEvt = Platform.OS === "ios" ? "keyboardWillShow" : "keyboardDidShow";
    const hideEvt = Platform.OS === "ios" ? "keyboardWillHide" : "keyboardDidHide";
    const showSub = Keyboard.addListener(showEvt, () => setKbVisible(true));
    const hideSub = Keyboard.addListener(hideEvt, () => setKbVisible(false));
    return () => { showSub.remove(); hideSub.remove(); };
  }, []);

  // Mode picker: null = landing, "chat" = Cosmic Intelligence (V1 or accepted V3)
  const [mode, setMode] = useState<"chat" | null>(null);
  const [askReplyLang, setAskReplyLang] = useState<AskReplyLang>("hn");
  const [langPickerVisible, setLangPickerVisible] = useState(false);
  const [langPickerDraft, setLangPickerDraft] = useState<AskReplyLang>("hn");
  /** Language modal: V1 chat entry, V3 live packs, or mid-chat change. */
  const [langPickerFor, setLangPickerFor] = useState<"v1" | "v3" | "change">("v1");
  const [v3PackVisible, setV3PackVisible] = useState(false);
  const [v3PackId, setV3PackId] = useState<(typeof V3_LIVE_PACKS)[number]["id"]>("30");
  const [v1PackVisible, setV1PackVisible] = useState(false);
  const [v1PackId, setV1PackId] = useState<AskV1PackId>("popular");
  const [v1PackBuying, setV1PackBuying] = useState(false);
  const [v1WalletLabel, setV1WalletLabel] = useState<string | null>(null);
  const [v1WalletBar, setV1WalletBar] = useState<{
    used: number;
    left: number;
    total: number;
    kind: "pack" | "free";
    unlimited?: boolean;
    packId?: string;
    packLabel?: string;
    packDays?: number;
    expires?: string | null;
    expiresLong?: string | null;
  } | null>(null);

  const refreshV1WalletLabel = useCallback(async () => {
    if (!user?.id || !user?.api_key) {
      setV1WalletLabel(null);
      setV1WalletBar(null);
      return;
    }
    try {
      const w = await hasActiveAskV1Wallet(user);
      if (w.unlimited) {
        setV1WalletBar({
          used: 0,
          left: -1,
          total: -1,
          kind: "pack",
          unlimited: true,
          packId: "unlimited",
          packLabel: "Unlimited",
        });
        setV1WalletLabel("Unlimited V1 questions");
        return;
      }
      const packLeft = Number(w.questions_left || 0);
      const packActive = Boolean(w.pack_active && packLeft > 0);

      if (packActive) {
        const left = packLeft;
        const total = Math.max(Number(w.questions_total || left), left);
        const used = Math.max(0, Number(w.questions_used ?? total - left));
        const packMeta = ASK_V1_PACKS.find((p) => p.id === w.pack_id);
        const exp = formatAskV1Expiry(w.expires_at);
        const expLong = formatAskV1ExpiryLong(w.expires_at);
        setV1WalletBar({
          used,
          left,
          total,
          kind: "pack",
          packId: w.pack_id || packMeta?.id,
          packLabel: packMeta?.label || "V1 Pack",
          packDays: packMeta?.days,
          expires: exp,
          expiresLong: expLong,
        });
        setV1WalletLabel(
          exp
            ? `${packMeta?.label || "Pack"} · ${left}/${total} Q · till ${exp}`
            : `${packMeta?.label || "Pack"} · ${left}/${total} Q`,
        );
        return;
      }

      // Free lifetime quota (3) via V1 only.
      // • New user / remaining → show left of 3 (e.g. 3 of 3)
      // • 0 only after all 3 free V1 questions are actually used
      const freeUsedRaw = Number(w.free_questions_used);
      const freeLeftRaw = Number(w.free_questions_left);
      const freeUsed = Number.isFinite(freeUsedRaw)
        ? Math.max(0, Math.min(3, freeUsedRaw))
        : 0;
      const freeLeft = Number.isFinite(freeLeftRaw)
        ? Math.max(0, Math.min(3, freeLeftRaw))
        : Math.max(0, 3 - freeUsed);

      const freeExhausted = freeLeft <= 0 && freeUsed >= 3;
      const freeActive = freeLeft > 0;

      if (!freeActive && !freeExhausted) {
        setV1WalletBar(null);
        setV1WalletLabel(null);
        return;
      }

      setV1WalletBar({
        used: freeUsed,
        left: freeLeft,
        total: 3,
        kind: "free",
        packLabel: freeExhausted ? "Get more" : "Free gift",
        packDays: undefined,
      });
      setV1WalletLabel(
        freeActive ? `${freeLeft} of 3 free left` : "0 of 3 · Get more",
      );
    } catch {
      setV1WalletBar(null);
      setV1WalletLabel(null);
    }
  }, [user?.id, user?.api_key]);

  useEffect(() => {
    void refreshV1WalletLabel();
  }, [refreshV1WalletLabel, mode]);

  const openV1PackPicker = useCallback(() => {
    void (async () => {
      // Leaving chat with empty wallet must still land in Last talked.
      try {
        if (user?.id && user.api_key && mode === "chat") {
          const w = await hasActiveAskV1Wallet(user);
          const stillHas = askV1WalletHasCredit(w);
          if (!stillHas) {
            await archiveAskChatSession(user.id, messagesRef.current);
          }
        }
      } catch { /* non-fatal */ }
      router.push("/cosmic-packs?focus=v1" as any);
    })();
  }, [user?.id, user?.api_key, mode]);

  const [v3Requesting, setV3Requesting] = useState(false);
  const [v3ReqError, setV3ReqError] = useState<string | null>(null);
  const [v3BusyVisible, setV3BusyVisible] = useState(false);
  const [v3WaitingId, setV3WaitingId] = useState<string | null>(null);
  const [v3WaitingLabel, setV3WaitingLabel] = useState("");
  const [v3QueuePosition, setV3QueuePosition] = useState<number | null>(null);
  const [v3EngineBusy, setV3EngineBusy] = useState(false);
  /** Admin ready — user must Accept before chat/timer starts. */
  const [v3ReadyVisible, setV3ReadyVisible] = useState(false);
  const [v3ReadySession, setV3ReadySession] = useState<null | {
    sessionId: string;
    minutes: number;
    label: string;
    priceInr: number;
    awaitingRemaining: number | null;
  }>(null);
  const [v3Accepting, setV3Accepting] = useState(false);
  const [v3CancellingWait, setV3CancellingWait] = useState(false);
  const [v3Live, setV3Live] = useState<null | {
    sessionId: string;
    minutes: number;
    label: string;
    priceInr: number;
  }>(null);

  useEffect(() => {
    AsyncStorage.getItem(ASK_REPLY_LANG_STORAGE_KEY)
      .then((raw) => {
        const loaded = loadAskReplyLang(raw);
        setAskReplyLang(loaded);
        setLangPickerDraft(loaded);
      })
      .catch(() => {});
  }, []);

  const persistAskReplyLang = useCallback(
    async (lang: AskReplyLang, syncServer: boolean) => {
      setAskReplyLang(lang);
      setLangPickerDraft(lang);
      await AsyncStorage.setItem(ASK_REPLY_LANG_STORAGE_KEY, lang).catch(() => {});
      if (syncServer && user?.id && user?.api_key) {
        try {
          await apiFetch(`${API_BASE}/api/user/${user.id}/language`, {
            method: "PUT",
            headers: {
              "Content-Type": "application/json",
              "X-API-Key": user.api_key,
              "X-User-Id": String(user.id),
            },
            body: JSON.stringify({ preferred_language: lang }),
          });
        } catch {
          /* non-fatal */
        }
      }
    },
    [user?.id, user?.api_key],
  );

  const enterAskChat = useCallback(
    (lang: AskReplyLang) => {
      void persistAskReplyLang(lang, true);
      setLangPickerVisible(false);
      setMode("chat");
    },
    [persistAskReplyLang],
  );

  /** After V3 language pick → Cosmic Packs (payment / book live there). */
  const continueV3AfterLang = useCallback(
    (lang: AskReplyLang) => {
      void persistAskReplyLang(lang, true);
      setLangPickerVisible(false);
      router.push("/cosmic-packs?focus=v3" as any);
    },
    [persistAskReplyLang],
  );

  /** After V1 language pick → enter chat if wallet active OR previous chat exists. */
  const continueV1AfterLang = useCallback(
    async (lang: AskReplyLang) => {
      setLangPickerVisible(false);
      void persistAskReplyLang(lang, true);
      if (!user?.id || !user?.api_key) {
        enterAskChat(lang);
        return;
      }

      const showNoCredit = (w: Awaited<ReturnType<typeof hasActiveAskV1Wallet>>) => {
        const wasFree =
          Number(w.free_questions_used || 0) >= 3 || !w.pack_active;
        setQuotaModal({
          used: wasFree ? 3 : Number(w.questions_used || 0),
          limit: wasFree ? 3 : Number(w.questions_total || 0),
          plan: wasFree ? "free" : "ask_v1_pack",
          message:
            "No credits left. Your previous chat stays here — buy a Cosmic Pack to ask a new question.",
        });
      };

      try {
        const w = await hasActiveAskV1Wallet(user);
        void refreshV1WalletLabel();
        if (askV1WalletHasCredit(w)) {
          enterAskChat(lang);
          return;
        }

        // Load previous V1 thread so baat chat mein hi dikhe (no credit).
        const threadKey = `chat_thread_v1_${user.id}_${primaryProfileId ?? "default"}`;
        let restored: Message[] | null = null;
        try {
          const raw = await AsyncStorage.getItem(threadKey);
          if (raw) {
            const parsed = JSON.parse(raw);
            if (Array.isArray(parsed) && parsed.some((m: Message) => m?.role === "user")) {
              restored = parsed.map((m: Message) => ({
                ...m,
                loading: false,
                streaming: false,
              }));
            }
          }
        } catch { /* ignore */ }

        if (!restored) {
          try {
            const archives = await listAskChatArchives(user.id);
            const latest = archives[0];
            if (latest?.messages?.length) {
              restored = latest.messages
                .filter((m) => m.sender === "user" || m.sender === "assistant")
                .map((m, i) => ({
                  id: m.id || `restored_${i}`,
                  role: m.sender === "user" ? ("user" as const) : ("assistant" as const),
                  text: m.text,
                }));
            }
          } catch { /* ignore */ }
        }

        if (restored && restored.length > 0) {
          setMessages(restored);
          try {
            await AsyncStorage.setItem(threadKey, JSON.stringify(restored));
          } catch { /* ignore */ }
          enterAskChat(lang);
          showNoCredit(w);
          return;
        }
      } catch {
        if (user?.id && user?.api_key) {
          try {
            const w = await hasActiveAskV1Wallet(user);
            if (w.fetchOk === false || askV1WalletHasCredit(w)) {
              enterAskChat(lang);
              return;
            }
          } catch { /* packs fallback */ }
        }
      }
      router.push("/cosmic-packs?focus=v1" as any);
    },
    [user, primaryProfileId, enterAskChat, refreshV1WalletLabel, persistAskReplyLang],
  );

  const buyV1Pack = useCallback(async () => {
    if (v1PackBuying) return;
    setV1PackBuying(true);
    try {
      const result = await startAskV1PackPayment(user, v1PackId);
      if (result === "paid_bypass") {
        setV1PackVisible(false);
        await refreshV1WalletLabel();
        enterAskChat(askReplyLang);
      } else if (result === "checkout") {
        setV1PackVisible(false);
      }
    } finally {
      setV1PackBuying(false);
    }
  }, [v1PackBuying, user, v1PackId, refreshV1WalletLabel, enterAskChat, askReplyLang]);

  const showV3ReadyFromSession = useCallback((s: any, fallbackId?: string) => {
    const sid = String(s?.session_id || fallbackId || "");
    if (!sid) return;
    setV3WaitingId(sid);
    setV3WaitingLabel(
      `${s?.label || "Live"} · ₹${Number(s?.price_inr || 0).toLocaleString("en-IN")}`,
    );
    setV3QueuePosition(
      typeof s?.queue_position === "number" ? s.queue_position : null,
    );
    setV3ReadySession({
      sessionId: sid,
      minutes: Number(s?.minutes) || 30,
      label: String(s?.label || "Live"),
      priceInr: Number(s?.price_inr) || 0,
      awaitingRemaining:
        typeof s?.awaiting_user_remaining_seconds === "number"
          ? s.awaiting_user_remaining_seconds
          : null,
    });
    setV3ReadyVisible(true);
    // Ring loudly — Ready modal must never be silent. Local notification plays
    // sound + vibration even when the server push was missed (deduped per sid).
    void presentV3ReadyNotification(sid, String(s?.label || "Live"));
    Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success).catch(() => {});
    Vibration.vibrate([0, 300, 150, 300]);
  }, []);

  // V3 card tap: resume live (accepted), show Ready modal (awaiting_user),
  // or queued wait — else language first, then pack picker.
  const openV3Entry = useCallback(async () => {
    if (user?.id && user?.api_key) {
      try {
        const res = await fetch(
          `${API_BASE}/api/cosmic-intelligence-v3/active?user_id=${user.id}`,
          { headers: { "X-API-Key": user.api_key } },
        );
        const json = await res.json().catch(() => ({} as any));
        const s = json?.session;
        if (res.ok && s?.session_id) {
          if (s.status === "accepted" && Number(s.remaining_seconds ?? 0) >= 300) {
            setV3Live({
              sessionId: String(s.session_id),
              minutes: Number(s.minutes) || 30,
              label: String(s.label || "Live"),
              priceInr: Number(s.price_inr) || 0,
            });
            setMode("chat");
            return;
          }
          if (s.status === "awaiting_user") {
            showV3ReadyFromSession(s);
            return;
          }
          if (s.status === "queued" || s.status === "pending") {
            setV3WaitingLabel(
              `${s.label || "Live"} · ₹${Number(s.price_inr || 0).toLocaleString("en-IN")}`,
            );
            setV3QueuePosition(
              typeof s.queue_position === "number" ? s.queue_position : null,
            );
            setV3EngineBusy(Boolean(s.engine_busy));
            setV3WaitingId(String(s.session_id));
            return;
          }
        }
      } catch {
        /* fall through to fresh booking */
      }
    }
    setLangPickerDraft(askReplyLang);
    setLangPickerFor("v3");
    setLangPickerVisible(true);
  }, [user?.id, user?.api_key, askReplyLang, showV3ReadyFromSession]);

  const requestV3LiveSession = useCallback(async (opts?: {
    packId?: string;
    lang?: AskReplyLang;
  }) => {
    // V3 requires payment first — Cosmic Packs starts Razorpay, then queues session.
    const packId = opts?.packId || v3PackId || "30";
    setV3PackVisible(false);
    setV3ReqError(null);
    router.push(`/cosmic-packs?focus=v3&pack=${encodeURIComponent(packId)}` as any);
  }, [v3PackId]);

  const acceptV3ReadySession = useCallback(async () => {
    const sid = v3ReadySession?.sessionId || v3WaitingId;
    if (!sid || !user?.id || !user?.api_key) return;
    setV3Accepting(true);
    try {
      const res = await fetch(
        `${API_BASE}/api/cosmic-intelligence-v3/session/${encodeURIComponent(sid)}/accept`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-API-Key": user.api_key,
          },
          body: JSON.stringify({ user_id: user.id }),
        },
      );
      const json = await res.json().catch(() => ({} as any));
      if (!res.ok) {
        if (json?.error === "accept_expired") {
          setV3ReadyVisible(false);
          setV3ReadySession(null);
          setV3QueuePosition(
            typeof json?.session?.queue_position === "number"
              ? json.session.queue_position
              : null,
          );
          setV3EngineBusy(true);
          Alert.alert(
            "Returned to queue",
            "You did not accept in time. You are back in the waiting list — the engine will invite you again.",
          );
          return;
        }
        throw new Error(json?.message || json?.error || `Accept failed (${res.status})`);
      }
      const s = json.session || {};
      setV3ReadyVisible(false);
      setV3ReadySession(null);
      setV3WaitingId(null);
      setV3Live({
        sessionId: String(s.session_id || sid),
        minutes: Number(s.minutes) || v3ReadySession?.minutes || 30,
        label: String(s.label || v3ReadySession?.label || "Live"),
        priceInr: Number(s.price_inr) || v3ReadySession?.priceInr || 0,
      });
      setMode("chat");
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success).catch(() => {});
    } catch (e: any) {
      Alert.alert("Could not start", String(e?.message || e));
    } finally {
      setV3Accepting(false);
    }
  }, [v3ReadySession, v3WaitingId, user?.id, user?.api_key]);

  const clearV3WaitingState = useCallback(() => {
    setV3WaitingId(null);
    setV3ReadyVisible(false);
    setV3ReadySession(null);
    setV3QueuePosition(null);
    setV3EngineBusy(false);
    setV3BusyVisible(false);
  }, []);

  const cancelV3Waitlist = useCallback(async () => {
    const sid = v3WaitingId || v3ReadySession?.sessionId;
    if (!user?.id || !user?.api_key || !sid) {
      // No server session (legacy busy popup) — just clear local waiting UI.
      clearV3WaitingState();
      return;
    }
    if (v3CancellingWait) return;
    setV3CancellingWait(true);
    try {
      const res = await fetch(
        `${API_BASE}/api/cosmic-intelligence-v3/session/${encodeURIComponent(sid)}/cancel-waitlist`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-API-Key": user.api_key,
          },
          body: JSON.stringify({ user_id: user.id }),
        },
      );
      const json = await res.json().catch(() => ({} as any));
      // 404 = old server (route/session missing) — treat as left locally.
      if (!res.ok && res.status !== 404 && json?.error !== "not_found") {
        throw new Error(json?.message || json?.error || `Cancel failed (${res.status})`);
      }
      clearV3WaitingState();
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success).catch(() => {});
    } catch {
      // Network error etc. — still honour the user's intent locally so the
      // popup never traps them; server queue entry will expire/requeue.
      clearV3WaitingState();
    } finally {
      setV3CancellingWait(false);
    }
  }, [
    v3WaitingId,
    v3ReadySession?.sessionId,
    v3CancellingWait,
    user?.id,
    user?.api_key,
    clearV3WaitingState,
  ]);

  // Direct action — Alert.alert confirm inside a Modal is unreliable on some
  // Android builds (dialog never shows → button feels dead).
  const confirmCancelV3Waitlist = useCallback(() => {
    void cancelV3Waitlist();
  }, [cancelV3Waitlist]);

  // Push tap / foreground v3_ready → open Ask Ready modal (poll is source of truth too).
  useEffect(() => {
    setV3ReadyHandler((sessionId) => {
      if (!sessionId) return;
      setV3WaitingId(sessionId);
      // Poll effect will hydrate Ready modal from status=awaiting_user.
      void (async () => {
        if (!user?.id || !user?.api_key) return;
        try {
          const res = await fetch(
            `${API_BASE}/api/cosmic-intelligence-v3/session/${encodeURIComponent(sessionId)}?user_id=${user.id}`,
            { headers: { "X-API-Key": user.api_key } },
          );
          const json = await res.json().catch(() => ({} as any));
          if (res.ok && String(json.status || "") === "awaiting_user") {
            showV3ReadyFromSession(json, sessionId);
          }
        } catch {
          /* poll will catch up */
        }
      })();
    });
    return () => setV3ReadyHandler(null);
  }, [user?.id, user?.api_key, showV3ReadyFromSession]);

  // Poll queue / awaiting_user / reject — never auto-open chat on admin accept.
  useEffect(() => {
    if (!v3WaitingId || !user?.id || !user?.api_key) return;
    let cancelled = false;
    const poll = async () => {
      try {
        const res = await fetch(
          `${API_BASE}/api/cosmic-intelligence-v3/session/${encodeURIComponent(v3WaitingId)}?user_id=${user.id}`,
          { headers: { "X-API-Key": user.api_key } },
        );
        const json = await res.json().catch(() => ({} as any));
        if (cancelled || !res.ok) return;
        const st = String(json.status || "");
        if (typeof json.queue_position === "number") {
          setV3QueuePosition(json.queue_position);
        }
        if (typeof json.engine_busy === "boolean") {
          setV3EngineBusy(json.engine_busy);
        }
        if (st === "awaiting_user") {
          // Ready modal — do NOT open V3LiveChat until user Accept.
          if (!v3ReadyVisible || v3ReadySession?.sessionId !== v3WaitingId) {
            showV3ReadyFromSession(json, v3WaitingId);
          } else if (typeof json.awaiting_user_remaining_seconds === "number") {
            setV3ReadySession((prev) =>
              prev
                ? { ...prev, awaitingRemaining: json.awaiting_user_remaining_seconds }
                : prev,
            );
          }
        } else if (st === "queued" || st === "pending") {
          if (v3ReadyVisible) {
            // Timed out → requeued
            setV3ReadyVisible(false);
            setV3ReadySession(null);
          }
        } else if (st === "accepted") {
          // Live only after user Accept (admin sets awaiting_user, not accepted).
          setV3ReadyVisible(false);
          setV3ReadySession(null);
          setV3WaitingId(null);
          setV3Live({
            sessionId: String(json.session_id || v3WaitingId),
            minutes: Number(json.minutes) || 30,
            label: String(json.label || "Live"),
            priceInr: Number(json.price_inr) || 0,
          });
          setMode("chat");
        } else if (st === "rejected") {
          setV3WaitingId(null);
          setV3ReadyVisible(false);
          setV3ReadySession(null);
          Alert.alert(
            "Engine unavailable",
            "Cosmic Intelligence V3 could not start this session. Try again shortly.",
          );
        }
      } catch {
        /* keep polling */
      }
    };
    void poll();
    const t = setInterval(poll, 2500);
    return () => {
      cancelled = true;
      clearInterval(t);
    };
  }, [
    v3WaitingId,
    user?.id,
    user?.api_key,
    v3ReadyVisible,
    v3ReadySession?.sessionId,
    showV3ReadyFromSession,
  ]);

  // ── Full-screen chat: hide the bottom tab bar (Home / Lifemap / Future …)
  // while in chat mode so "Ask Anything" opens edge-to-edge like a dedicated
  // chat app. Restored automatically on blur or when returning to the
  // landing picker (the in-header back chevron sets mode → null).
  const { setHidden } = useTabBar();
  useFocusEffect(
    useCallback(() => {
      setHidden(mode === "chat");
      return () => setHidden(false);
    }, [mode, setHidden]),
  );

  // Refresh wallet whenever Ask tab / chat regains focus (e.g. after pack payment).
  useFocusEffect(
    useCallback(() => {
      void refreshV1WalletLabel();
    }, [refreshV1WalletLabel]),
  );

  // After Cosmic Packs V3 booking → resume waiting / ready / live from API.
  useFocusEffect(
    useCallback(() => {
      const raw = routeParams.resumeV3;
      const flag = Array.isArray(raw) ? raw[0] : raw;
      if (flag !== "1") return;
      try {
        router.setParams({ resumeV3: undefined } as any);
      } catch { /* ignore */ }
      void (async () => {
        if (!user?.id || !user?.api_key) return;
        try {
          const res = await fetch(
            `${API_BASE}/api/cosmic-intelligence-v3/active?user_id=${user.id}`,
            { headers: { "X-API-Key": user.api_key } },
          );
          const json = await res.json().catch(() => ({} as any));
          const s = json?.session;
          if (!res.ok || !s?.session_id) return;
          if (s.status === "accepted" && Number(s.remaining_seconds ?? 0) >= 300) {
            setV3Live({
              sessionId: String(s.session_id),
              minutes: Number(s.minutes) || 30,
              label: String(s.label || "Live"),
              priceInr: Number(s.price_inr) || 0,
            });
            setMode("chat");
            return;
          }
          if (s.status === "awaiting_user") {
            showV3ReadyFromSession(s);
            return;
          }
          if (s.status === "queued" || s.status === "pending") {
            setV3WaitingLabel(
              `${s.label || "Live"} · ₹${Number(s.price_inr || 0).toLocaleString("en-IN")}`,
            );
            setV3QueuePosition(
              typeof s.queue_position === "number" ? s.queue_position : null,
            );
            setV3EngineBusy(Boolean(s.engine_busy));
            setV3WaitingId(String(s.session_id));
          }
        } catch {
          /* non-fatal */
        }
      })();
    }, [routeParams.resumeV3, user?.id, user?.api_key, showV3ReadyFromSession]),
  );

  // ── Back handling: chat → landing (not pop tab stack).
  useFocusEffect(
    useCallback(() => {
      const onBack = () => {
        if (mode === "chat") {
          if (v3Live) {
            // A live V3 session is intentionally locked. The user must use End.
            return true;
          }
          setMode(null);
          return true;
        }
        return false;
      };
      const sub = BackHandler.addEventListener("hardwareBackPress", onBack);
      return () => sub.remove();
    }, [mode, v3Live]),
  );

  const tabBarHidden = mode === "chat";
  // Resting bottom padding (keyboard CLOSED). When open, the KeyboardAvoiding
  // View lifts the whole row above the keyboard so we only need a tiny gap.
  //   keyboard open → 10px flush gap above the keyboard.
  //   chat (tab bar hidden) → just the safe-area inset.
  //   landing → clear the tab bar.
  const inputRowBottomPad = kbVisible
    ? 10
    : tabBarHidden ? botPad + 10 : botPad + TAB_BAR_HEIGHT;

  // ── Request ownership ────────────────────────────────────────────────────
  // Each send() bumps requestIdRef. Stream callbacks gate every state mutation
  // on `myReqId === requestIdRef.current` so a superseded in-flight stream
  // can't clobber the newer conversation. abortRef lets a new send actually
  // cancel the previous fetch (frees the OpenAI quota faster too).
  const requestIdRef = useRef(0);
  const abortRef     = useRef<AbortController | null>(null);

  const [messages, setMessages] = useState<Message[]>(() =>
    showDemo
      ? DEMO_MESSAGES
      : [
          {
            id: "init",
            role: "assistant",
            text: `Hey, I'm Cosmo ✨ What would you like to know today?`,
          },
        ]
  );

  // ── Chat persistence (H2.7.5b) ──────────────────────────────────────────
  // Save the full chat thread (Q+A bubbles) to AsyncStorage per-user +
  // per-active-profile so the conversation survives app close/reopen.
  // The server-side `question_history` (Recent Questions surface) is
  // separate — it stores Q text only for the landing list. THIS layer
  // restores the actual chat bubbles inside the thread when user
  // returns. Keys are scoped so different users / profiles on the same
  // device don't bleed into each other's threads.
  // Cap at last 200 messages to prevent unbounded growth on heavy users.
  const CHAT_STORAGE_VERSION = "v1";
  const chatStorageKey = useMemo(() => {
    const uid = user?.id ?? "anon";
    const pid = primaryProfileId ?? "default";
    return `chat_thread_${CHAT_STORAGE_VERSION}_${uid}_${pid}`;
  }, [user?.id, primaryProfileId]);
  // Track WHICH key we've finished hydrating. Architect-flagged race
  // (H2.7.5b review): a single boolean was unsafe — if user/profile
  // switched, the SAVE effect could fire on the new key before LOAD
  // completed, writing the OLD thread under the NEW key (cross-profile
  // contamination). Using a key-string ref means save only proceeds
  // when hydratedKeyRef.current === current chatStorageKey.
  const hydratedKeyRef = useRef<string | null>(null);

  // LOAD on mount + whenever the storage key changes (user/profile switch).
  useEffect(() => {
    // Invalidate hydration flag IMMEDIATELY on key change so the SAVE
    // effect (which runs in the same commit cycle) cannot persist
    // pre-switch messages under the new key.
    hydratedKeyRef.current = null;
    if (showDemo) {
      // Demo mode never hydrates — always shows fresh DEMO_MESSAGES.
      // Mark hydrated under the demo key so save effect stays inert.
      hydratedKeyRef.current = chatStorageKey;
      return;
    }
    const targetKey = chatStorageKey;
    let cancelled = false;
    (async () => {
      try {
        const raw = await AsyncStorage.getItem(targetKey);
        if (cancelled) return;
        if (raw) {
          const parsed = JSON.parse(raw);
          if (Array.isArray(parsed) && parsed.length > 0) {
            // Reset transient flags — a stored bubble must never resume
            // streaming/loading on reopen.
            const cleaned: Message[] = parsed.map((m: Message) => ({
              ...m,
              loading: false,
              streaming: false,
            }));
            setMessages(cleaned);
          }
        }
      } catch {
        // Corrupt entry — ignore, keep default greeting.
      } finally {
        // Only mark hydrated if the key hasn't changed during the await.
        if (!cancelled) hydratedKeyRef.current = targetKey;
      }
    })();
    return () => { cancelled = true; };
  }, [chatStorageKey, showDemo]);

  // SAVE chat thread — debounced so streaming tokens don't hit AsyncStorage
  // on every delta (was a major JS-thread hang during answers).
  useEffect(() => {
    if (showDemo) return;
    if (hydratedKeyRef.current !== chatStorageKey) return;
    const timer = setTimeout(() => {
      const tail = messages.slice(-200);
      AsyncStorage.setItem(chatStorageKey, JSON.stringify(tail)).catch(() => {
        // Storage full / quota — non-fatal, thread keeps working in memory.
      });
    }, 700);
    return () => clearTimeout(timer);
  }, [messages, chatStorageKey, showDemo]);

  const messagesRef = useRef(messages);
  messagesRef.current = messages;

  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  // ── Recent Questions (history) — read-only surface populated by /api/ask
  // and /api/ask/stream's server-side logger. Pure storage layer; clicking
  // an item just seeds the chat with the same question text.
  type HistoryItem = {
    id: string;
    question_text: string;
    topic: string;
    verdict_summary: string;
    created_at: string;
  };
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const fetchHistory = useCallback(async () => {
    if (!user?.id || !user?.api_key) return;
    try {
      const res = await apiFetch(`${API_BASE}/api/history?limit=20`, {
        headers: {
          "X-User-Id":  String(user.id),
          "X-API-Key":  user.api_key,
        },
      });
      if (!res.ok) return;
      const j = await res.json();
      setHistory(Array.isArray(j?.items) ? j.items : []);
    } catch {
      // non-fatal — history is decorative
    }
  }, [user?.id, user?.api_key]);

  // Fetch on landing mount AND on chat-open so the in-chat Recent
  // Questions strip (fresh-thread only) is always up to date.
  useEffect(() => { fetchHistory(); }, [mode, fetchHistory]);
  const [quotaModal, setQuotaModal] = useState<null | {
    used: number;
    limit: number;
    plan: string;
    message: string;
  }>(null);

  /** Credits empty: keep chat visible, archive for Last talked, show buy modal. */
  const endAskSessionBecauseEmpty = useCallback(
    async (opts?: { used?: number; limit?: number; plan?: string }) => {
      const snap = messagesRef.current;
      if (user?.id) {
        try {
          await archiveAskChatSession(user.id, snap);
        } catch { /* non-fatal */ }
      }
      // Stay in chat — previous baat visible rahe; wipe mat karo.
      void refreshV1WalletLabel();
      const isFree = (opts?.plan ?? v1WalletBar?.kind) === "free";
      setQuotaModal({
        used: opts?.used ?? (isFree ? 3 : (v1WalletBar?.total ?? opts?.limit ?? 0)),
        limit: opts?.limit ?? (isFree ? 3 : (v1WalletBar?.total ?? opts?.used ?? 0)),
        plan: opts?.plan ?? (v1WalletBar?.kind === "free" ? "free" : "ask_v1_pack"),
        message: isFree
          ? "No credits left. Your previous chat stays here — buy a Cosmic Pack to ask a new question."
          : "Pack credits finished. Your previous chat stays here — buy a Cosmic Pack to ask a new question.",
      });
      try {
        Haptics.notificationAsync(Haptics.NotificationFeedbackType.Warning);
      } catch {}
    },
    [user?.id, v1WalletBar?.total, v1WalletBar?.kind, refreshV1WalletLabel],
  );

  /**
   * After a successful answer: if free/pack wallet is empty, archive to
   * My Reports → Last talked. Do NOT gate on v1WalletBar (can be null).
   */
  const finishAskIfWalletEmpty = useCallback(
    async (snap?: Message[]) => {
      if (!user?.id || !user?.api_key) return;
      if (snap) messagesRef.current = snap;
      try {
        const w = await hasActiveAskV1Wallet(user);
        if (w.fetchOk === false) return;
        const stillHas = askV1WalletHasCredit(w);
        if (stillHas) return;
        // Let final assistant bubble commit into messagesRef via render if needed.
        await new Promise((r) => setTimeout(r, 100));
        const wasFree =
          v1WalletBar?.kind === "free" ||
          Number(w.free_questions_used || 0) >= 3 ||
          !w.pack_active;
        await endAskSessionBecauseEmpty({
          used: wasFree
            ? 3
            : Number(w.questions_used ?? v1WalletBar?.total ?? v1WalletBar?.used ?? 0),
          limit: wasFree
            ? 3
            : Number(w.questions_total ?? v1WalletBar?.total ?? 0),
          plan: wasFree ? "free" : "ask_v1_pack",
        });
      } catch {
        /* non-fatal */
      }
    },
    [user, endAskSessionBecauseEmpty, v1WalletBar],
  );

  const listRef = useRef<FlatList>(null);
  const scrollTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const scrollToEnd = useCallback((animated = true) => {
    if (scrollTimerRef.current) clearTimeout(scrollTimerRef.current);
    scrollTimerRef.current = setTimeout(() => {
      listRef.current?.scrollToEnd({ animated });
    }, 120);
  }, []);

  // Throttled auto-scroll (scrollToEnd coalesces to ~120ms).
  useEffect(() => {
    const streaming = messages.some((m) => m.streaming);
    scrollToEnd(!streaming);
    return () => {
      if (scrollTimerRef.current) clearTimeout(scrollTimerRef.current);
    };
  }, [messages, scrollToEnd]);

  const send = useCallback(
    async (text: string, opts?: { regenerate?: boolean; targetAssistantId?: string }) => {
      if (!text.trim() || loading) return;
      if (showDemo) {
        router.push("/onboarding");
        return;
      }

      let payloadKundli = askChart;
      let payloadBirth = askBirthData;

      if (user?.id && user?.api_key) {
        const localReady = (payloadKundli?.planets?.length ?? 0) > 0;
        // Skip network sync when local chart is ready — saves ~1–2s before send.
        if (!localReady) {
          const synced = await syncProfilesNow().catch(() => null);
          const syncedReady = (synced?.chart?.planets?.length ?? 0) > 0;
          if (syncedReady) {
            payloadKundli = synced!.chart;
            payloadBirth = synced!.birth ?? payloadBirth;
          }
        } else {
          payloadKundli = askChart;
          payloadBirth = askBirthData;
        }
      }

      if (!payloadKundli?.planets?.length) {
        router.push("/onboarding");
        return;
      }

      const payloadKundliSlim = slimKundliForAsk(payloadKundli as Record<string, unknown>);

      // No credit → keep chat visible, ask to buy (don't wipe previous baat).
      if (user?.id && user?.api_key) {
        try {
        const w = await hasActiveAskV1Wallet(user);
        if (w.fetchOk) {
          const stillHas = askV1WalletHasCredit(w);
          if (!stillHas) {
            const wasFree =
              Number(w.free_questions_used || 0) >= 3 || !w.pack_active;
            await endAskSessionBecauseEmpty({
              used: wasFree ? 3 : Number(w.questions_used || 0),
              limit: wasFree ? 3 : Number(w.questions_total || 0),
              plan: wasFree ? "free" : "ask_v1_pack",
            });
            return;
          }
        }
      } catch { /* proceed; server 402 is fallback */ }
      }

      const isRegen = !!opts?.regenerate;
      const targetId = opts?.targetAssistantId;

      // ── Snapshot-based state derivation ─────────────────────────────────
      // Compute `trimmed` (post-strip) and `history` from a single snapshot
      // so the request body, the quota-restore path, and the optimistic UI
      // never disagree (avoids stale-closure bugs on rapid regenerate).
      const original = messages;
      let trimmed = original;
      if (isRegen) {
        if (targetId) {
          // Regenerate THIS specific assistant bubble — drop it and any
          // assistant turns after it; preserve everything before.
          const idx = original.findIndex((m) => m.id === targetId);
          if (idx >= 0) {
            trimmed = original.slice(0, idx);
            // Also drop any trailing assistant turns that followed it (rare,
            // but safe).
            while (trimmed.length > 0 && trimmed[trimmed.length - 1].role === "assistant") {
              trimmed = trimmed.slice(0, -1);
            }
          }
        } else {
          // No specific target: drop trailing assistant turn(s).
          while (
            trimmed.length > 0 &&
            (trimmed[trimmed.length - 1].role === "assistant" || trimmed[trimmed.length - 1].id === "thinking")
          ) {
            trimmed = trimmed.slice(0, -1);
          }
        }
      }

      const userMsg: Message | null = isRegen
        ? null
        : { id: Date.now().toString() + "_u", role: "user", text: text.trim() };
      const thinkMsg: Message = { id: "thinking", role: "assistant", text: "", loading: true };
      const nextWithUser = userMsg ? [...trimmed, userMsg] : trimmed;
      const nextWithThink: Message[] = [...nextWithUser, thinkMsg];

      // ── Acquire request ownership ─────────────────────────────────────
      // Bump counter, capture local id; abort any in-flight stream from a
      // previous (now-superseded) call. State mutations below are gated on
      // `myReqId === requestIdRef.current` so stale completions are ignored.
      const myReqId = ++requestIdRef.current;
      try { abortRef.current?.abort(); } catch {}
      const ctrl = new AbortController();
      abortRef.current = ctrl;
      const isCurrent = () => myReqId === requestIdRef.current;

      setMessages(nextWithThink);
      if (!isRegen) setInput("");
      setLoading(true);
      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);

      let thinkStatusTimer: ReturnType<typeof setInterval> | null = null;
      let thinkStep = 0;
      thinkStatusTimer = setInterval(() => {
        if (!isCurrent()) return;
        thinkStep = Math.min(thinkStep + 1, ASK_WAIT_STATUS.length - 1);
        const caption = ASK_WAIT_STATUS[thinkStep];
        setMessages((prev) =>
          prev.map((m) => (m.id === "thinking" ? { ...m, text: caption } : m)),
        );
      }, 2800);

      // ── Centralised failure handler ───────────────────────────────────
      // For regenerate: silently restore the original thread (no error
      // bubble — user keeps the prior visible answer + chips intact).
      // For fresh sends: drop think bubble, append a single error bubble.
      const failQuietly = (errMsg: string) => {
        if (!isCurrent()) return;
        if (isRegen) {
          setMessages(original);
        } else {
          setMessages((prev) =>
            prev.filter((m) => m.id !== "thinking").concat({
              id: Date.now().toString(),
              role: "assistant",
              text: errMsg,
            }),
          );
        }
      };

      try {
        const headers: Record<string, string> = {
          "Content-Type": "application/json",
          "Accept":       "text/event-stream, application/json",
          ...userAuthHeaders(user),
        };

        // Conversation memory: build from POST-strip snapshot (not state),
        // excluding the new user message which is sent separately as
        // `question`. Keep last 10 turns for context budget.
        const history = trimmed
          .filter((m) => !m.loading && m.id !== "thinking")
          .slice(-10)
          .map((m) => {
            const row: Record<string, string> = { role: m.role, text: m.text };
            // Echo DNA so server follow-up lock keeps the same engine.
            if (m.domain) row.domain = m.domain;
            if (m.bucket) row.bucket = m.bucket;
            if (m.topic) row.topic = m.topic;
            if (m.archetype) row.archetype = m.archetype;
            if (m.subject) row.subject = m.subject;
            return row;
          });

        // Use raw fetch (not apiFetch) — apiFetch's network-retry can re-issue
        // the request mid-stream; SSE responses must not be retried.
        // INITIAL-CONNECT RETRY (May 6 2026): the first TLS handshake to
        // a fresh cloudflare tunnel host occasionally hiccups (HTTP/2 RST
        // or DNS warm-up), causing fetch() to throw before any response
        // is received. Retrying ONLY the initial fetch (before we touch
        // res.body) is safe because no stream bytes have been consumed
        // yet — this is identical to apiFetch's policy. Mid-stream errors
        // still fail to the user as before.
        let requestBody = "";
        try {
          requestBody = JSON.stringify({
            question: text.trim(),
            kundli: payloadKundliSlim,
            birthData: payloadBirth,
            history,
            // Question script wins — picker is only a fallback when undetectable.
            lang: askLangToApi(
              detectAskLangFromQuestion(text.trim()) || askReplyLang,
            ),
            user_id: user?.id,
          });
        } catch {
          failQuietly("Kundli data issue — Profile me birth details save karke dubara try karein.");
          return;
        }

        const _reqInit: RequestInit = {
          method: "POST",
          headers,
          body: requestBody,
          signal: ctrl.signal,
        };
        let res: Response;
        const askUrl = `${getApiBase()}/api/ask/stream`;
        try {
          res = await fetch(askUrl, _reqInit);
        } catch (_initErr: any) {
          // Bail immediately on user-cancel / supersede / unmount.
          if (_initErr?.name === "AbortError") throw _initErr;
          if (!isCurrent()) throw _initErr;
          const _msg = String(_initErr?.message || "");
          // Only retry on classic transient network failures.
          if (!/Network request failed|TypeError|fetch|Failed to fetch|Load failed/i.test(_msg)) {
            throw _initErr;
          }
          await new Promise(r => setTimeout(r, 600));
          if (!isCurrent()) throw _initErr;
          res = await fetch(askUrl, _reqInit);
        }

        // Stale completion — a newer send superseded us; drop quietly.
        if (!isCurrent()) return;

        const ct = (res.headers.get("content-type") || "").toLowerCase();
        const isStream = ct.includes("text/event-stream");

        // ── Quota exhausted (HTTP 402) ─────────────────────────────────────
        // Backend always returns JSON for 402 — same as one-shot path.
        if (res.status === 402) {
          const json = await res.json().catch(() => ({} as any));
          if (!isCurrent()) return;
          if (isRegen) {
            setMessages(original);
          } else {
            setMessages((prev) =>
              prev.filter((m) => m.id !== "thinking" && (!userMsg || m.id !== userMsg.id)),
            );
            setInput(text);
          }
          const plan = String(json?.plan ?? "free");
          if (plan === "ask_v1_pack" || plan === "free" || v1WalletBar) {
            await endAskSessionBecauseEmpty({
              used: json?.quota?.used ?? 0,
              limit: json?.quota?.limit ?? 0,
              plan: plan === "free" ? "free" : "ask_v1_pack",
            });
          } else {
            setQuotaModal({
              used:    json?.quota?.used  ?? 0,
              limit:   json?.quota?.limit ?? 0,
              plan,
              message: json?.message      ?? t.askDailyLimitOver,
            });
            try { Haptics.notificationAsync(Haptics.NotificationFeedbackType.Warning); } catch {}
          }
          return;
        }

        // ── Auth error (401) — restore on regenerate, error bubble on fresh
        if (res.status === 401) {
          failQuietly("Session expired — kripya logout karke phir login karein.");
          return;
        }

        // ── Kundli missing (412) — profile birth details needed
        if (res.status === 412) {
          const json = await res.json().catch(() => ({} as any));
          failQuietly(
            json?.message ||
              "Aapki kundli save nahi hai. Profile me birth details save karke dubara try karein.",
          );
          return;
        }

        // ── Other non-2xx (5xx etc) — same restore matrix as auth.
        if (!res.ok) {
          if (res.status === 524) {
            failQuietly(
              "Server timeout (524) — jawab banne mein zyada time laga. Dubara try karein.",
            );
            return;
          }
          failQuietly("Kshama karein, abhi jawab dene mein dikkat aa rahi hai.");
          return;
        }

        const pickAnswerText = (json: any): string => {
          const raw =
            (typeof json?.text === "string" && json.text.trim()) ||
            (typeof json?.answer === "string" && json.answer.trim()) ||
            (typeof json?.response === "string" && json.response.trim()) ||
            "";
          return sanitizeAskAnswerForDisplay(raw);
        };

        const commitJsonAnswer = async (json: any) => {
          if (!json || typeof json !== "object") {
            failQuietly("Kshama karein, abhi jawab dene mein dikkat aa rahi hai.");
            return;
          }
          if (json.error === "daily_limit_reached" || json.upgrade_required === true) {
            if (!isCurrent()) return;
            const plan = String(json?.plan ?? "free");
            if (plan === "ask_v1_pack" || plan === "free" || v1WalletBar) {
              await endAskSessionBecauseEmpty({
                used: json?.quota?.used ?? 0,
                limit: json?.quota?.limit ?? 0,
                plan: plan === "free" ? "free" : "ask_v1_pack",
              });
            } else {
              setQuotaModal({
                used: json?.quota?.used ?? 0,
                limit: json?.quota?.limit ?? 0,
                plan,
                message: json?.message ?? t.askDailyLimitOver,
              });
            }
            setMessages((prev) => prev.filter((m) => m.id !== "thinking"));
            return;
          }
          const answer = pickAnswerText(json);
          if (!answer) {
            failQuietly(
              askErrorToUserMessage(
                typeof json?.error === "string" ? json.error : undefined,
                typeof json?.message === "string" && json.message.trim()
                  ? String(json.message)
                  : undefined,
              ),
            );
            return;
          }
          const followUps: string[] = Array.isArray(json.follow_ups) ? json.follow_ups.slice(0, 3) : [];
          const dnaDomain = typeof (json as any).domain === "string" ? String((json as any).domain) : undefined;
          const dnaBucket = typeof (json as any).bucket === "string" ? String((json as any).bucket) : undefined;
          const dnaTopic = typeof json.topic === "string" ? String(json.topic) : undefined;
          const dnaArchetype = typeof (json as any).archetype === "string" ? String((json as any).archetype) : undefined;
          const dnaSubject = typeof (json as any).subject === "string" ? String((json as any).subject) : undefined;

          const isV2     = json.response_schema === "v2"
                         && Array.isArray(json.cards)
                         && json.cards.length > 0;
          const cards: CardData[] | undefined = isV2 ? json.cards : undefined;
          const trimmedCount = isV2 && typeof json.trimmed_count === "number"
            ? json.trimmed_count
            : undefined;

          let clar: { prompt: string; options: string[] } | undefined;
          if (
            json.clarification &&
            typeof json.clarification === "object" &&
            typeof json.clarification.prompt === "string" &&
            Array.isArray(json.clarification.options) &&
            json.clarification.options.length > 0
          ) {
            const _opts = (json.clarification.options as unknown[])
              .filter(o => typeof o === "string" && (o as string).trim().length > 0)
              .slice(0, 4) as string[];
            if (_opts.length > 0) {
              clar = { prompt: String(json.clarification.prompt), options: _opts };
            }
          }

          let partnerCta: { label: string; relation: string } | undefined;
          if (
            (json as any).requires_partner_profile === true &&
            (json as any).partner_cta &&
            typeof (json as any).partner_cta === "object" &&
            typeof (json as any).partner_cta.relation === "string"
          ) {
            const _pc = (json as any).partner_cta;
            partnerCta = {
              label:    typeof _pc.label === "string" && _pc.label.trim().length > 0
                          ? String(_pc.label) : "Add partner details",
              relation: String(_pc.relation),
            };
          }

          const newAssistantId = Date.now().toString() + "_a";
          const assistantMsg: Message = {
            id: newAssistantId,
            role: "assistant",
            text: answer,
            followUps,
            topic: dnaTopic,
            domain: dnaDomain || dnaTopic,
            bucket: dnaBucket,
            archetype: dnaArchetype,
            subject: dnaSubject,
            cards,
            trimmedCount,
            responseSchema: isV2 ? "v2" : undefined,
            clarification: clar,
            partnerCta,
            revealAnswer: true,
          };
          let snapForArchive: Message[] = messagesRef.current;
          setMessages(prev => {
            const next = prev.filter(m => m.id !== "thinking").concat(assistantMsg);
            messagesRef.current = next;
            snapForArchive = next;
            return next;
          });
          void fetchHistory();
          void refreshV1WalletLabel();
          await finishAskIfWalletEmpty(snapForArchive);
        };

        // ── One-shot JSON path (raw passthrough / guards) ───────────────
        // Peek body once so we can recover when a proxy mislabels JSON as SSE.
        const rawBody = await res.text();
        if (!isCurrent()) return;

        const trimmedBody = rawBody.trim();
        if (!isStream || (trimmedBody.startsWith("{") && !trimmedBody.includes("data:"))) {
          let json: any = null;
          try { json = JSON.parse(trimmedBody); } catch { json = null; }
          await commitJsonAnswer(json);
          return;
        }

        // ── True SSE streaming path ────────────────────────────────────────
        // Replace the thinking bubble with an empty assistant bubble that
        // we'll append delta tokens to in real time. On `done`, swap the
        // accumulated text with the scrubbed `text` from the done event
        // (scrubber may have removed banned words → trust server).
        const newAssistantId = Date.now().toString() + "_a";
        setMessages(prev =>
          prev.filter(m => m.id !== "thinking").concat({
            id: newAssistantId, role: "assistant", text: "", streaming: true,
          })
        );

        let accumulated     = "";
        let finalText       = "";
        let finalFollowUps: string[] = [];
        let finalClarification: { prompt: string; options: string[] } | undefined;
        let finalDomain: string | undefined;
        let finalBucket: string | undefined;
        let finalTopic: string | undefined;
        let finalArchetype: string | undefined;
        let finalSubject: string | undefined;
        let sawDone         = false;
        let midError: string | null = null;
        let paintTimer: ReturnType<typeof setTimeout> | null = null;
        let paintPending = false;

        const paintStreamText = () => {
          paintPending = false;
          if (!isCurrent()) return;
          const textNow = accumulated;
          setMessages(prev => {
            const idx = prev.findIndex(m => m.id === newAssistantId);
            if (idx < 0) return prev;
            if (prev[idx].text === textNow) return prev;
            const next = [...prev];
            next[idx] = { ...next[idx], text: textNow };
            return next;
          });
        };

        const scheduleStreamPaint = () => {
          if (paintPending) return;
          paintPending = true;
          paintTimer = setTimeout(paintStreamText, 80);
        };

        const handleEvent = (raw: string) => {
          const dataLine = raw.split("\n").find(l => l.startsWith("data:"));
          if (!dataLine) return;
          const dataStr = dataLine.slice(5).trim();
          if (!dataStr) return;
          let evt: any;
          try { evt = JSON.parse(dataStr); } catch { return; }
          if (evt.error) { midError = String(evt.error); return; }
          if (typeof evt.delta === "string" && evt.delta.length > 0) {
            accumulated += evt.delta;
            if (!isCurrent()) return;
            scheduleStreamPaint();
          }
          if (evt.done) {
            sawDone = true;
            finalText = String(evt.text || accumulated || "");
            finalFollowUps = Array.isArray(evt.follow_ups) ? evt.follow_ups.slice(0, 3) : [];
            if (typeof evt.domain === "string" && evt.domain.trim()) finalDomain = String(evt.domain);
            if (typeof evt.bucket === "string" && evt.bucket.trim()) finalBucket = String(evt.bucket);
            if (typeof evt.topic === "string" && evt.topic.trim()) finalTopic = String(evt.topic);
            if (typeof evt.archetype === "string" && evt.archetype.trim()) finalArchetype = String(evt.archetype);
            if (typeof evt.subject === "string" && evt.subject.trim()) finalSubject = String(evt.subject);
            const _clar = (evt as any).clarification;
            if (
              _clar && typeof _clar === "object" &&
              typeof _clar.prompt === "string" &&
              Array.isArray(_clar.options) && _clar.options.length > 0
            ) {
              const _opts = (_clar.options as unknown[])
                .filter(o => typeof o === "string" && (o as string).trim().length > 0)
                .slice(0, 4) as string[];
              if (_opts.length > 0) {
                finalClarification = { prompt: String(_clar.prompt), options: _opts };
              }
            }
          }
        };

        // Body already buffered (RN often cannot stream) — parse all SSE events.
        for (const part of rawBody.split("\n\n")) {
          if (part.trim()) handleEvent(part);
        }

        // No `done` event: keep usable partial text, else surface error.
        if (!sawDone) {
          const fallback = (accumulated || "").trim();
          if (fallback.length > 20 && isCurrent()) {
            finalText = fallback;
            sawDone = true;
          } else {
            if (isCurrent()) {
              setMessages(prev => prev.filter(m => m.id !== newAssistantId));
            }
            failQuietly(midError || "Kshama karein, abhi jawab dene mein dikkat aa rahi hai.");
            return;
          }
        }

        // Stale check before final commit.
        if (!isCurrent()) return;
        if (paintTimer) {
          clearTimeout(paintTimer);
          paintTimer = null;
          paintPending = false;
        }

        // Swap in scrubbed final text + follow_ups; clear streaming flag.
        setMessages(prev => {
          const idx = prev.findIndex(m => m.id === newAssistantId);
          if (idx < 0) return prev;
          const next = [...prev];
          next[idx] = {
            ...next[idx],
            clarification: finalClarification,
            text:      sanitizeAskAnswerForDisplay(finalText || accumulated),
            followUps: finalFollowUps,
            topic: finalTopic || next[idx].topic,
            domain: finalDomain || finalTopic || next[idx].domain,
            bucket: finalBucket || next[idx].bucket,
            archetype: finalArchetype || next[idx].archetype,
            subject: finalSubject || next[idx].subject,
            streaming: false,
          };
          messagesRef.current = next;
          return next;
        });
        void fetchHistory();
        void refreshV1WalletLabel();
        await finishAskIfWalletEmpty();
      } catch (e: any) {
        // Two abort cases to disambiguate:
        //   • Superseded by a newer send → !isCurrent(): the new owner has
        //     already painted UI; we silently exit.
        //   • Current-request abort (e.g. unmount, manual cancel, navigate
        //     away mid-stream): we are still the owner, so route through
        //     the standard restore matrix to avoid a stuck thinking bubble.
        if (!isCurrent()) return;
        if (e?.name === "AbortError") {
          // Drop the in-progress streaming bubble (if any) before restoring.
          setMessages(prev => prev.filter(m => !m.streaming));
          failQuietly("Cancelled.");
          return;
        }
        failQuietly(
          __DEV__ && e?.message
            ? /failed to fetch|load failed|network/i.test(String(e.message))
              ? "API reach nahi ho rahi — Metro restart karein (start-web.ps1). Console mein [metro-proxy] POST dikhe."
              : `Network error: ${String(e.message).slice(0, 160)}`
            : "Network error — thodi der baad try karein.",
        );
      } finally {
        if (thinkStatusTimer) clearInterval(thinkStatusTimer);
        // Only the latest in-flight request clears the loading flag; older
        // (aborted) ones must not flip it off while a newer call is pending.
        if (isCurrent()) setLoading(false);
      }
    },
    [loading, showDemo, askChart, askBirthData, user?.id, user?.api_key, syncProfilesNow, askReplyLang, messages, t.askDailyLimitOver, fetchHistory, refreshV1WalletLabel, endAskSessionBecauseEmpty, finishAskIfWalletEmpty, v1WalletBar],
  );

  // Latest assistant message id — only this one shows follow-up chips.
  const latestAssistantId = useMemo(() => {
    for (let i = messages.length - 1; i >= 0; i--) {
      const m = messages[i];
      if (m.role === "assistant" && !m.loading) return m.id;
    }
    return null;
  }, [messages]);

  const renderMsg = ({ item }: { item: Message }) => {
    const isUser = item.role === "user";
    const isLatestAssistant = !isUser && item.id === latestAssistantId;
    return (
      <Reanimated.View
        entering={(isUser ? FadeInRight : FadeInLeft).duration(380).easing(REasing.out(REasing.cubic))}
      >
        <View style={[s.bubble, isUser ? s.bubbleUser : s.bubbleAssistant]}>
          {!isUser && (
            <LinearGradient
              colors={[C.accent, `${C.accent}88`]}
              start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }}
              style={[s.avatar, s.avatarGlow, { shadowColor: C.accent, borderColor: `${C.accent}55` }]}
            >
              <Feather name="cpu" size={13} color="#fff" />
            </LinearGradient>
          )}
          {isUser ? (
            <LinearGradient
              // Fixed premium violet — NOT the zodiac accent (which can resolve
              // to dark red for some signs and made the question bubble look off).
              colors={["#6D5DF6", "#8B5CF6"]}
              start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }}
              style={[s.bubbleInner, s.bubbleInnerUser, s.bubbleGlow, { shadowColor: "#6D5DF6", borderColor: "rgba(139,92,246,0.45)" }]}
            >
              <Text style={[s.bubbleText, s.bubbleTextUser]}>{item.text}</Text>
            </LinearGradient>
          ) : (
            <LinearGradient
              colors={[C.bgCard2, C.bgCard]}
              start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }}
              style={[
                s.bubbleInner, s.bubbleInnerAssistant, s.bubbleGlowSoft,
                { borderColor: `${C.accent}33`, shadowColor: C.accent },
              ]}
            >
              {item.loading ? (
                <AcharyaTypingDots
                  caption={item.text?.trim() || "Cosmic Intelligence calculating…"}
                />
              ) : item.cards && item.cards.length > 0 ? (
                <CardsCarousel
                  cards={item.cards}
                  trimmedCount={item.trimmedCount ?? 0}
                />
              ) : item.revealAnswer && isLatestAssistant ? (
                <TypewriterAnswer
                  text={sanitizeAskAnswerForDisplay(item.text)}
                  onComplete={() => {
                    setMessages((prev) => {
                      const next = prev.map((m) =>
                        m.id === item.id ? { ...m, revealAnswer: false } : m,
                      );
                      messagesRef.current = next;
                      return next;
                    });
                  }}
                />
              ) : (
                <MarkdownReply text={sanitizeAskAnswerForDisplay(item.text)} />
              )}
            </LinearGradient>
          )}
        </View>

        {/* Phase 7.5 — Clarifier UX: refinement chips shown when the
            classifier confidence was low. Server attaches `clarification`
            on the response (env-gated, default OFF). Latest reply only —
            stale clarifications stay hidden in scrollback to avoid
            offering refinements for a question already answered. Tapping
            a chip routes through the standard `send` flow so the now-
            specific question is re-classified independently. */}
        {isLatestAssistant
          && item.clarification
          && item.clarification.options
          && item.clarification.options.length > 0
          && !item.streaming
          && !loading && (
          <View style={[s.clarifierBanner, { borderColor: `${C.accent}30`, backgroundColor: C.bgCard }]}>
            <Text style={[s.clarifierTitle, { color: C.textMuted }]}>
              {item.clarification.prompt}
            </Text>
            <ScrollView
              horizontal
              showsHorizontalScrollIndicator={false}
              contentContainerStyle={s.clarifierRow}
            >
              {item.clarification.options.map((opt, idx) => (
                <Pressable
                  key={`${item.id}_clar_${idx}`}
                  onPress={() => {
                    try { Haptics.selectionAsync(); } catch {}
                    send(opt);
                  }}
                  style={({ pressed }) => [
                    s.clarifierChip,
                    { backgroundColor: C.isDark ? "#1E1B4B" : "#EDE9FE", borderColor: `${C.accent}50` },
                    pressed && { opacity: 0.7 },
                  ]}
                >
                  <Feather name="help-circle" size={11} color={C.accent} />
                  <Text style={[s.clarifierChipText, { color: C.accent }]}>{opt}</Text>
                </Pressable>
              ))}
            </ScrollView>
          </View>
        )}

        {/* Phase 2.5.11.6 — Partner CTA card. Server returns this when
            the user asks about an existing partner ("mere bf se shaadi
            hogi") but no partner profile is saved. Tapping the button
            opens profile-edit pre-set to the right relation slot so the
            user can add DOB/TOB/place; coming back & re-asking triggers
            the real synastry flow. */}
        {item.role === "assistant" && item.partnerCta && !item.streaming && !loading && (
          <Pressable
            onPress={() => {
              try { Haptics.selectionAsync(); } catch {}
              router.push({
                pathname: "/profile-edit",
                params:   { relation: item.partnerCta!.relation },
              } as any);
            }}
            style={({ pressed }) => [
              s.partnerCtaBtn,
              { backgroundColor: C.accent, borderColor: C.accent },
              pressed && { opacity: 0.85 },
            ]}
          >
            <Feather name="user-plus" size={14} color="#FFFFFF" />
            <Text style={s.partnerCtaText}>
              {item.partnerCta.label || "Add partner details"}
            </Text>
            <Feather name="arrow-right" size={14} color="#FFFFFF" />
          </Pressable>
        )}

        {/* Follow-up suggestion chips — only on the latest assistant reply */}
        {isLatestAssistant && item.followUps && item.followUps.length > 0 && !loading && (
          <ScrollView
            horizontal
            showsHorizontalScrollIndicator={false}
            contentContainerStyle={s.followUpsRow}
          >
            {item.followUps.map((q, idx) => (
              <Pressable
                key={`${item.id}_fu_${idx}`}
                onPress={() => {
                  try { Haptics.selectionAsync(); } catch {}
                  send(q);
                }}
                style={({ pressed }) => [
                  s.followUpChip,
                  { backgroundColor: C.bgCard, borderColor: `${C.accent}50` },
                  pressed && { opacity: 0.7 },
                ]}
              >
                <Feather name="corner-down-right" size={11} color={C.accent} />
                <Text style={[s.followUpText, { color: C.accent }]}>{q}</Text>
              </Pressable>
            ))}
          </ScrollView>
        )}
      </Reanimated.View>
    );
  };

  // Real admin↔user live chat (after Accept) — separate from V1 AI Ask
  if (mode === "chat" && v3Live && user?.id && user?.api_key) {
    return (
      <View style={[s.root, { backgroundColor: C.isDark ? "#000000" : C.bg }]}>
        <V3LiveChat
          sessionId={v3Live.sessionId}
          userId={user.id}
          apiKey={user.api_key}
          label={v3Live.label}
          priceInr={v3Live.priceInr}
          onEnded={() => {
            setMode(null);
            setV3Live(null);
          }}
        />
      </View>
    );
  }

  return (
    <View style={[s.root, { backgroundColor: C.isDark ? "#000000" : C.bg }]}>
    <KeyboardAvoidingView
      style={s.root}
      // `padding` lifts the input row flush above the keyboard. The
      // keyboard-controller version handles Android edge-to-edge correctly
      // (no persistent nav-bar gap when closed, no half-hidden input).
      // verticalOffset accounts for the (visible) tab bar on the landing
      // screen so the row doesn't jump; in chat the tab bar is hidden.
      behavior="padding"
      keyboardVerticalOffset={tabBarHidden ? 0 : TAB_BAR_HEIGHT}
    >
      {/* Header */}
      <FadeInView delay={0}>
        <View style={[s.header, { paddingTop: topPad + (mode === null ? 4 : 12), paddingBottom: mode === null ? 6 : 10, borderBottomColor: C.border }]}>
        <View style={s.headerTopRow}>
          {mode === "chat" ? (
            <Pressable
              onPress={() => { Haptics.selectionAsync(); setMode(null); setV3Live(null); }}
              hitSlop={12}
              style={s.backBtn}
            >
              <Feather name="chevron-left" size={20} color={C.text} />
            </Pressable>
          ) : null}
          <View style={{ flex: 1, minWidth: 0 }}>
            <View style={s.headerTitleRow}>
              <View
                pointerEvents="none"
                style={[s.headerTitleGlow, { backgroundColor: `${C.accent}26`, shadowColor: C.accent }]}
              />
              {mode === "chat" ? (
                <Feather name="cpu" size={14} color={C.accent} style={{ marginRight: 5 }} />
              ) : null}
              <Text
                style={[s.headerTitle, { color: C.text, textShadowColor: `${C.accent}88`, flexShrink: 1 }]}
                numberOfLines={1}
                adjustsFontSizeToFit
                minimumFontScale={0.78}
              >
                {mode === "chat" ? "Cosmic Advance Intelligence" : "Ask"}
              </Text>
              <View style={{ marginLeft: 6 }}>
                <GlowDot color="#10b981" size={7} />
              </View>
            </View>
            {mode === "chat" ? (
              <Text
                style={[s.headerSub, { color: C.textMuted, textAlign: "left", paddingHorizontal: 0 }]}
                numberOfLines={2}
              >
                Advanced Multi-System Engine · Live chart intelligence
              </Text>
            ) : null}
          </View>

          {/* Side wallet chip — gift / pack (designed, not a plain label) */}
          {v1WalletBar ? (
            <Pressable
              onPress={() => {
                if (v1WalletBar.kind === "free" || v1WalletBar.left <= 1) {
                  Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light).catch(() => {});
                  openV1PackPicker();
                }
              }}
              style={({ pressed }) => [{ opacity: pressed ? 0.88 : 1, flexShrink: 0 }]}
            >
              <LinearGradient
                colors={
                  v1WalletBar.kind === "free"
                    ? v1WalletBar.left <= 0
                      ? C.isDark
                        ? ["#7f1d1d", "#b91c1c", "#ea580c"]
                        : ["#fb7185", "#f43f5e", "#ea580c"]
                      : C.isDark
                        ? ["#78350f", "#b45309", "#d97706"]
                        : ["#fbbf24", "#f59e0b", "#ea580c"]
                    : C.isDark
                      ? ["#1e3a8a", "#2563eb", "#0891b2"]
                      : ["#60a5fa", "#3b82f6", "#06b6d4"]
                }
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 1 }}
                style={[
                  s.planSideCard,
                  {
                    shadowColor: v1WalletBar.left <= 0 ? "#ef4444" : "#f59e0b",
                  },
                ]}
              >
                <View style={s.planSideTop}>
                  <View style={s.planSideIconBubble}>
                    <Feather
                      name={
                        v1WalletBar.kind === "free"
                          ? v1WalletBar.left <= 0
                            ? "zap"
                            : "gift"
                          : "award"
                      }
                      size={12}
                      color="#fff"
                    />
                  </View>
                  <Text style={s.planSideNameOnGrad} numberOfLines={1}>
                    {v1WalletBar.kind === "free"
                      ? v1WalletBar.left <= 0
                        ? "Get more"
                        : "Free gift"
                      : v1WalletBar.packLabel || "Pack"}
                  </Text>
                </View>

                <Text style={s.planSideQOnGrad}>
                  {v1WalletBar.unlimited ? (
                    "∞"
                  ) : (
                    <>
                      {v1WalletBar.left}
                      <Text style={s.planSideQTotalOnGrad}> of {v1WalletBar.total}</Text>
                    </>
                  )}
                </Text>

                {v1WalletBar.kind === "free" ? (
                  <View style={s.planSideDots}>
                    {[0, 1, 2].map((i) => {
                      const filled = i < v1WalletBar.left;
                      return (
                        <View
                          key={i}
                          style={[
                            s.planSideDot,
                            {
                              backgroundColor: filled
                                ? "#fff"
                                : "rgba(255,255,255,0.28)",
                              borderColor: "rgba(255,255,255,0.55)",
                            },
                          ]}
                        />
                      );
                    })}
                  </View>
                ) : null}

                <View style={s.planSideCtaPill}>
                  <Text style={s.planSideCtaText} numberOfLines={1}>
                    {v1WalletBar.kind === "free"
                      ? v1WalletBar.left > 0
                        ? "questions left"
                        : "Cosmic Packs →"
                      : v1WalletBar.expiresLong
                        ? `Till ${v1WalletBar.expiresLong}`
                        : "Active"}
                  </Text>
                </View>
              </LinearGradient>
            </Pressable>
          ) : null}
        </View>

        {mode === "chat" && v1WalletBar?.kind === "free" && v1WalletBar.left <= 0 ? (
          <Pressable
            onPress={() => {
              Haptics.selectionAsync();
              openV1PackPicker();
            }}
            style={({ pressed }) => [{ opacity: pressed ? 0.9 : 1, marginTop: 10, marginHorizontal: 4 }]}
          >
            <LinearGradient
              colors={C.isDark ? ["#7f1d1d", "#9a3412"] : ["#fff1f2", "#ffedd5"]}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 0 }}
              style={[
                s.walletWarn,
                {
                  borderColor: C.isDark ? "rgba(251,113,133,0.45)" : "rgba(244,63,94,0.3)",
                },
              ]}
            >
              <Feather name="gift" size={14} color={C.isDark ? "#fda4af" : "#e11d48"} />
              <Text
                style={[
                  s.walletWarnText,
                  { color: C.isDark ? "#fecdd3" : "#9f1239", fontFamily: "Nunito_600SemiBold" },
                ]}
              >
                Free 3 used — chat stays here · Get more to ask again
              </Text>
              <View style={s.walletWarnCta}>
                <Text style={s.walletWarnCtaText}>Get more</Text>
                <Feather name="arrow-right" size={12} color="#fff" />
              </View>
            </LinearGradient>
          </Pressable>
        ) : null}

        {mode === "chat" && v1WalletBar?.kind === "pack" && v1WalletBar.left <= 0 ? (
          <Pressable
            onPress={() => {
              Haptics.selectionAsync();
              openV1PackPicker();
            }}
            style={({ pressed }) => [{ opacity: pressed ? 0.9 : 1, marginTop: 10, marginHorizontal: 4 }]}
          >
            <LinearGradient
              colors={C.isDark ? ["#7f1d1d", "#9a3412"] : ["#fff1f2", "#ffedd5"]}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 0 }}
              style={[
                s.walletWarn,
                {
                  borderColor: C.isDark ? "rgba(251,113,133,0.45)" : "rgba(244,63,94,0.3)",
                },
              ]}
            >
              <Feather name="zap" size={14} color={C.isDark ? "#fda4af" : "#e11d48"} />
              <Text
                style={[
                  s.walletWarnText,
                  { color: C.isDark ? "#fecdd3" : "#9f1239", fontFamily: "Nunito_600SemiBold" },
                ]}
              >
                No credits — chat stays here · Buy a pack
              </Text>
              <View style={s.walletWarnCta}>
                <Text style={s.walletWarnCtaText}>Buy</Text>
                <Feather name="arrow-right" size={12} color="#fff" />
              </View>
            </LinearGradient>
          </Pressable>
        ) : null}

        {mode === "chat" && v1WalletBar?.left === 1 && v1WalletBar.kind !== "free" ? (
          <Pressable
            onPress={() => {
              Haptics.selectionAsync();
              openV1PackPicker();
            }}
            style={[
              s.walletWarn,
              {
                marginTop: 10,
                marginHorizontal: 4,
                backgroundColor: C.isDark ? "rgba(245,158,11,0.10)" : "rgba(255,243,208,0.95)",
                borderColor: C.isDark ? "rgba(245,158,11,0.35)" : "rgba(217,119,6,0.28)",
              },
            ]}
          >
            <Feather name="zap" size={12} color="#d97706" />
            <Text style={[s.walletWarnText, { color: C.isDark ? "#fbbf24" : "#92400e" }]}>
              1 question left — recharge for more answers
            </Text>
            <Text style={{ color: "#d97706", fontSize: 11, fontFamily: "Nunito_700Bold" }}>
              Buy →
            </Text>
          </Pressable>
        ) : null}

        {mode === "chat" && v1WalletBar?.kind === "free" && v1WalletBar.left === 1 ? (
          <Pressable
            onPress={() => {
              Haptics.selectionAsync();
              openV1PackPicker();
            }}
            style={({ pressed }) => [{ opacity: pressed ? 0.9 : 1, marginTop: 10, marginHorizontal: 4 }]}
          >
            <LinearGradient
              colors={C.isDark ? ["#78350f", "#92400e"] : ["#fffbeb", "#ffedd5"]}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 0 }}
              style={[
                s.walletWarn,
                {
                  borderColor: C.isDark ? "rgba(251,191,36,0.4)" : "rgba(217,119,6,0.3)",
                },
              ]}
            >
              <Feather name="zap" size={14} color={C.isDark ? "#fbbf24" : "#d97706"} />
              <Text
                style={[
                  s.walletWarnText,
                  { color: C.isDark ? "#fde68a" : "#92400e", fontFamily: "Nunito_600SemiBold" },
                ]}
              >
                Last free question — packs ready when you need more
              </Text>
              <View style={[s.walletWarnCta, { backgroundColor: "#d97706" }]}>
                <Text style={s.walletWarnCtaText}>Packs</Text>
                <Feather name="arrow-right" size={12} color="#fff" />
              </View>
            </LinearGradient>
          </Pressable>
        ) : null}
        </View>
      </FadeInView>

      {/* Demo banner */}
      {showDemo && (
        <Pressable style={[s.demoBanner, { backgroundColor: C.warningBg, borderColor: C.warningBorder }]} onPress={() => router.push("/onboarding")}>
          <Feather name="lock" size={12} color={C.warningText} />
          <Text style={[s.demoText, { color: C.warningText }]}>
            Kundli banao — personalized answers ke liye tap karein
          </Text>
          <Feather name="chevron-right" size={12} color={C.warningText} />
        </Pressable>
      )}

      {/* ───── Mode Picker (default landing) ────────────────────────────── */}
      {mode === null && (
        <View style={{ flex: 1 }}>
        <AskAmbientField accent={C.accent || "#a78bfa"} />
        <ScrollView
          style={{ flex: 1 }}
          contentContainerStyle={s.pickerWrap}
          showsVerticalScrollIndicator={false}
        >
          <FadeInView delay={staggerDelay(0, 55, 40)}>
            <View style={s.pickerHero}>
              <BreathingHeroBadge
                style={[s.heroBadge, { backgroundColor: `${C.accent}18`, borderColor: `${C.accent}55` }]}
              >
                <GlowDot color={C.accent || "#a78bfa"} size={6} />
                <Feather name="cpu" size={11} color={C.accent} />
                <Text
                  style={[s.heroBadgeText, { color: C.accent, flexShrink: 1 }]}
                  numberOfLines={1}
                  adjustsFontSizeToFit
                  minimumFontScale={0.85}
                >
                  Cosmic Advance Intelligence
                </Text>
              </BreathingHeroBadge>
              <Text
                style={[s.heroTagline, { color: C.textMuted }]}
                numberOfLines={1}
              >
                Live chart intelligence · V3 + V1
              </Text>
              <RotatingExamples color={C.accent || "#a78bfa"} textColor={C.text} />
            </View>
          </FadeInView>

          {/* Card 1: Cosmic Intelligence V3 — most powerful (lead option) */}
          <FadeInView delay={staggerDelay(1, 70, 80)}>
            <PressScale
              accessibilityLabel="Cosmic Intelligence V3"
              onPress={() => {
                Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
                if (showDemo) { router.push("/onboarding"); return; }
                void openV3Entry();
              }}
              style={[s.modeCard, { shadowColor: "#f59e0b" }]}
            >
              <LinearGradient
                colors={["#92400e", "#d97706", "#fbbf24"]}
                start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }}
                style={s.modeGrad}
              >
                <CardShimmer />
                <View style={s.modeIconWrap}>
                  <FloatIcon>
                    <Text style={s.modeEmoji}>⚡</Text>
                  </FloatIcon>
                </View>
                <View style={{ flex: 1 }}>
                  <View style={s.modeTitleRow}>
                    <Text style={s.modeTitle}>Cosmic Intelligence V3</Text>
                    <PulsePill style={s.modeBadge}>
                      <Text style={s.modeBadgeText}>MOST POWERFUL</Text>
                    </PulsePill>
                  </View>
                  <Text style={s.modeBody}>
                    Live conversation + exact timing — the most powerful engine ever built.
                  </Text>
                  <View style={s.modeMeta}>
                    <Feather name="zap" size={11} color="#ffffffcc" />
                    <Text style={s.modeMetaText}>Live timing · Talk to your chart</Text>
                  </View>
                </View>
                <Feather name="chevron-right" size={20} color="#fff" />
              </LinearGradient>
            </PressScale>
          </FadeInView>

          {/* Card 2: Cosmic Intelligence V1 (classic chat) */}
          <FadeInView delay={staggerDelay(2, 70, 100)}>
            <PressScale
            accessibilityLabel="Cosmic Intelligence V1"
            onPress={() => {
              Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
              if (showDemo) { router.push("/onboarding"); return; }
              setLangPickerDraft(askReplyLang);
              setLangPickerFor("v1");
              setLangPickerVisible(true);
            }}
            style={[s.modeCard, { shadowColor: "#3b82f6" }]}
          >
            <LinearGradient
              colors={["#1e40af", "#3b82f6", "#06b6d4"]}
              start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }}
              style={s.modeGrad}
            >
              <CardShimmer />
              <View style={s.modeIconWrap}>
                <FloatIcon delayMs={200}>
                  <Text style={s.modeEmoji}>💬</Text>
                </FloatIcon>
              </View>
              <View style={{ flex: 1 }}>
                <Text style={s.modeTitle}>Cosmic Intelligence V1</Text>
                <Text style={s.modeBody}>
                  Trusted chart Q&A — career, marriage, health, money, dasha. Plain-language answers from your kundli.
                </Text>
                <View style={s.modeMeta}>
                  <Feather name="zap" size={11} color="#ffffffcc" />
                  <Text style={s.modeMetaText}>
                    {v1WalletBar?.kind === "free"
                      ? v1WalletBar.left > 0
                        ? `${v1WalletBar.left} of 3 free questions left`
                        : "0 of 3 free · Get more in Cosmic Packs"
                      : v1WalletLabel || "From ₹49 · 8–45 questions · packs"}
                  </Text>
                </View>
              </View>
              <Feather name="chevron-right" size={20} color="#fff" />
            </LinearGradient>
            </PressScale>
          </FadeInView>

          {INSTAGRAM_ANSWERS_ENABLED ? (
            <FadeInView delay={staggerDelay(4, 70, 140)}>
              <PressScale
                accessibilityLabel="Free Instagram Answers"
                onPress={() => {
                  Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium).catch(() => {});
                  if (showDemo) { router.push("/onboarding"); return; }
                  router.push("/instagram-answers");
                }}
                style={[s.modeCard, s.rectifyCard, { shadowColor: "#c13584" }]}
              >
                <LinearGradient
                  colors={["#4c1d95", "#833ab4", "#fd1d1d"]}
                  start={{ x: 0, y: 0 }}
                  end={{ x: 1, y: 1 }}
                  style={s.rectifyGrad}
                >
                  <CardShimmer />
                  <View style={s.modeIconWrap}>
                    <FloatIcon delayMs={500}>
                      <Text style={s.modeEmoji}>📱</Text>
                    </FloatIcon>
                  </View>
                  <View style={{ flex: 1 }}>
                    <View style={s.modeTitleRow}>
                      <Text style={s.modeTitle}>Free Instagram Answers</Text>
                      <PulsePill style={[s.modeBadge, { backgroundColor: "rgba(255,255,255,0.22)" }]}>
                        <Text style={s.modeBadgeText}>FREE</Text>
                      </PulsePill>
                    </View>
                    <Text style={s.modeBody}>
                      Type exact words like an Instagram DM — saved auto-reply from our reel library. Free, no pack.
                    </Text>
                    <View style={s.modeMeta}>
                      <Feather name="smartphone" size={11} color="#ffffffcc" />
                      <Text style={s.modeMetaText}>DM trigger → auto-reply · Reel # + exact words</Text>
                    </View>
                    <View style={s.rectifyCtaRow}>
                      <Text style={s.rectifyCtaOnGrad}>Get free answer</Text>
                      <Feather name="arrow-right" size={14} color="#fff" />
                    </View>
                  </View>
                </LinearGradient>
              </PressScale>
            </FadeInView>
          ) : null}

          {/* Recent Questions MOVED into the chat view (fresh-thread only).
              Landing picker now stays focused on the mode cards. */}

          {/* Optional: small Divya Prashna link (legacy, less prominent) */}
          <FadeInView delay={staggerDelay(5, 70, 160)}>
            <Pressable
            onPress={() => {
              Haptics.selectionAsync();
              if (showDemo) { router.push("/onboarding"); return; }
              router.push("/divya-prashna");
            }}
            style={s.legacyLink}
          >
            <Feather name="clock" size={12} color={C.textMuted} />
            <Text style={[s.legacyLinkText, { color: C.textMuted }]}>
              Time-based Divya Prashna (current moment)
            </Text>
            </Pressable>
          </FadeInView>
        </ScrollView>
        </View>
      )}


      {/* ───── Chat Mode ────────────────────────────────────────────────── */}
      {mode === "chat" && (<>
      {/* Messages */}
      <FlatList
        ref={listRef}
        data={messages}
        keyExtractor={m => m.id}
        renderItem={renderMsg}
        contentContainerStyle={[s.list, { paddingBottom: 12 }]}
        showsVerticalScrollIndicator={false}
        initialNumToRender={8}
        maxToRenderPerBatch={6}
        windowSize={7}
        removeClippedSubviews={Platform.OS === "android"}
        keyboardShouldPersistTaps="handled"
      />

      {/* Starter chips — visible only at fresh-thread state AND when
          keyboard is closed (else they eat the chat area while user
          is typing). */}
      {messages.length <= 1 && !showDemo && !kbVisible && (
        <View style={s.starters}>
          {STARTERS.map(q => {
            // Starter-chip accent — intentionally NOT the theme/zodiac accent
            // (that can be red). A premium gold (dark) / indigo (light) tone
            // that pops on the black chat without looking like an error.
            const chipColor = C.isDark ? "#E8B86D" : "#6D5DF6";
            return (
              <Pressable
                key={q}
                style={({ pressed }) => [
                  s.starter,
                  { backgroundColor: C.isDark ? "#16161C" : C.bgCard, borderColor: `${chipColor}33` },
                  pressed && { opacity: 0.8, transform: [{ scale: 0.99 }], borderColor: `${chipColor}80` },
                ]}
                onPress={() => { try { Haptics.selectionAsync(); } catch {} send(q); }}
              >
                <Feather name="message-circle" size={14} color={chipColor} />
                <Text style={[s.starterText, { color: chipColor }]} numberOfLines={1}>{q}</Text>
                <Feather name="arrow-up-right" size={15} color={`${chipColor}99`} />
              </Pressable>
            );
          })}
        </View>
      )}

      {/* Phase 6.1.1 selector REMOVED (May 6 2026) — Ask section ab
          hamesha primary kundli use karega. Profile switching ab sirf
          Profile/My-Kundli screen se hota hai. Reason: users confuse
          ho rahe the ki kis profile pe answer aaya — ek primary chart
          = ek deterministic answer. */}

      {/* Input row — dynamic bottom padding:
          • keyboard hidden → clear the tab bar (botPad + TAB_BAR_HEIGHT)
          • keyboard visible → small flush gap (10px), KAV pushes the
            row above the keyboard top automatically. */}
      <View style={[s.inputRow, { paddingBottom: inputRowBottomPad, backgroundColor: C.isDark ? "#000000" : C.bg, borderTopColor: C.isDark ? "rgba(255,255,255,0.06)" : C.border }]}>
        <TextInput
          style={[
            s.input,
            {
              backgroundColor: C.isDark ? "#1C1C22" : C.bgCard2,
              borderColor: C.isDark ? "rgba(255,255,255,0.10)" : C.border,
              color: C.text,
            },
          ]}
          value={input}
          onChangeText={setInput}
          placeholder={t.askPlaceholder}
          placeholderTextColor={C.textMuted}
          multiline
          editable={!showDemo}
          onSubmitEditing={() => send(input)}
          returnKeyType="send"
        />
        <Pressable
          onPress={() => (showDemo ? router.push("/onboarding") : send(input))}
          style={({ pressed }) => [
            s.sendBtn,
            { shadowColor: C.btnGradEnd },
            s.sendBtnGlow,
            pressed && { opacity: 0.9, transform: [{ scale: 0.92 }] },
          ]}
        >
          <LinearGradient
            colors={[C.btnGradStart, C.btnGradEnd]}
            start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }}
            style={s.sendGrad}
          >
            <Feather name={showDemo ? "lock" : "send"} size={16} color="#fff" />
          </LinearGradient>
        </Pressable>
      </View>
      </>)}

      {/* ── Daily quota exhausted modal ──────────────────────────────────── */}
      <Modal
        visible={!!quotaModal}
        transparent
        animationType="fade"
        onRequestClose={() => setQuotaModal(null)}
      >
        <Pressable style={qm.backdrop} onPress={() => setQuotaModal(null)}>
          <Pressable style={[qm.card, { backgroundColor: C.bgCard, borderColor: `${C.accent}40` }]} onPress={(e) => e.stopPropagation?.()}>
            <View style={[qm.iconWrap, { backgroundColor: C.accentBg, borderColor: `${C.accent}40` }]}>
              <Feather name="zap" size={28} color={C.accent} />
            </View>

            <Text style={[qm.title, { color: C.text }]}>
              {quotaModal?.plan === "free"
                ? "Free questions finished"
                : quotaModal?.plan === "ask_v1_pack"
                  ? "Pack questions finished"
                  : "Daily limit reached"}
            </Text>

            <Text style={[qm.usage, { color: C.textMid }]}>
              <Text style={{ fontWeight: "700", color: C.text }}>{quotaModal?.used ?? 0}</Text>
              <Text> / </Text>
              <Text style={{ fontWeight: "700", color: C.text }}>{quotaModal?.limit ?? 0}</Text>
              <Text>
                {quotaModal?.plan === "free"
                  ? " free questions used"
                  : quotaModal?.plan === "ask_v1_pack"
                    ? " pack questions used"
                    : " questions used today"}
              </Text>
            </Text>

            <Text style={[qm.msg, { color: C.textMuted }]}>
              {quotaModal?.plan === "free"
                ? "No credits left. Your previous chat stays here. To ask a new question, buy from Cosmic Packs — Starter ₹49 · Popular ₹99 · Power ₹299."
                : quotaModal?.plan === "ask_v1_pack"
                  ? "Pack credits finished. Your previous chat stays here — buy your next pack: Starter ₹49 · Popular ₹99 · Power ₹299."
                  : quotaModal?.plan === "pro"
                    ? quotaModal?.message
                    : quotaModal?.plan === "basic"
                      ? "Basic plan includes 10 questions/day. Get more with a V1 pack."
                      : quotaModal?.plan === "trial"
                        ? "Trial limit reached. Buy a V1 question pack for more answers."
                        : "You get 3 free questions on signup. After that, choose a V1 pack."}
            </Text>

            {quotaModal?.plan !== "pro" && (
              <Pressable
                onPress={() => {
                  setQuotaModal(null);
                  openV1PackPicker();
                }}
                style={({ pressed }) => [{ width: "100%", marginTop: 4, opacity: pressed ? 0.9 : 1 }]}
              >
                <LinearGradient
                  colors={
                    quotaModal?.plan === "free"
                      ? ["#f59e0b", "#ea580c"]
                      : ["#3b82f6", "#06b6d4"]
                  }
                  start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }}
                  style={qm.cta}
                >
                  <Feather name={quotaModal?.plan === "free" ? "gift" : "zap"} size={15} color="#fff" />
                  <Text style={qm.ctaText}>
                    {quotaModal?.plan === "free" ? "Get more · Cosmic Packs" : "Buy question pack"}
                  </Text>
                </LinearGradient>
              </Pressable>
            )}

            <Pressable onPress={() => setQuotaModal(null)} style={qm.dismiss}>
              <Text style={[qm.dismissText, { color: C.textMuted }]}>
                {quotaModal?.plan === "pro" ? "OK" : "Maybe later"}
              </Text>
            </Pressable>
          </Pressable>
        </Pressable>
      </Modal>

      {/* ── Ask reply language (before chat opens) ───────────────────────── */}
      <Modal
        visible={langPickerVisible}
        transparent
        animationType="fade"
        onRequestClose={() => setLangPickerVisible(false)}
      >
        <Pressable style={qm.backdrop} onPress={() => setLangPickerVisible(false)}>
          <Pressable
            style={[qm.card, { backgroundColor: C.bgCard, borderColor: `${C.accent}40` }]}
            onPress={(e) => e.stopPropagation?.()}
          >
            <View style={[qm.iconWrap, { backgroundColor: C.accentBg, borderColor: `${C.accent}40` }]}>
              <Feather name="globe" size={26} color={C.accent} />
            </View>
            <Text style={[qm.title, { color: C.text }]}>Which language for the answer?</Text>
            <Text style={[qm.msg, { color: C.textMuted, marginBottom: 12 }]}>
              {langPickerFor === "v3"
                ? "Select a language first — Cosmic Intelligence V3 will speak in that language. Then you can book a live slot on Cosmic Packs."
                : "Whatever you select, Cosmic Intelligence will reply in that language."}
            </Text>
            {ASK_REPLY_LANG_OPTIONS.map((opt) => {
              const active = langPickerDraft === opt.id;
              return (
                <Pressable
                  key={opt.id}
                  onPress={() => {
                    Haptics.selectionAsync();
                    setLangPickerDraft(opt.id);
                  }}
                  style={[
                    s.langPickRow,
                    {
                      backgroundColor: active ? `${C.accent}18` : C.bgCard2,
                      borderColor: active ? C.accent : C.border,
                    },
                  ]}
                >
                  <View style={{ flex: 1 }}>
                    <Text style={[s.langPickTitle, { color: C.text }]}>{opt.label}</Text>
                    <Text style={[s.langPickSub, { color: C.textMuted }]}>{opt.sublabel}</Text>
                  </View>
                  {active ? <Feather name="check-circle" size={20} color={C.accent} /> : null}
                </Pressable>
              );
            })}
            <Pressable
              onPress={() => {
                if (langPickerFor === "v3") {
                  continueV3AfterLang(langPickerDraft);
                } else if (langPickerFor === "change" || mode === "chat") {
                  void persistAskReplyLang(langPickerDraft, true);
                  setLangPickerVisible(false);
                } else {
                  void continueV1AfterLang(langPickerDraft);
                }
              }}
              style={({ pressed }) => [{ width: "100%", marginTop: 14, opacity: pressed ? 0.9 : 1 }]}
            >
              <LinearGradient
                colors={
                  langPickerFor === "v3"
                    ? ["#d97706", "#f59e0b"]
                    : [C.btnGradStart, C.btnGradEnd]
                }
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 0 }}
                style={qm.cta}
              >
                <Feather
                  name={
                    langPickerFor === "v3"
                      ? "arrow-right"
                      : langPickerFor === "change" || mode === "chat"
                        ? "check"
                        : "message-circle"
                  }
                  size={15}
                  color="#fff"
                />
                <Text style={qm.ctaText}>
                  {langPickerFor === "v3"
                    ? "Continue"
                    : langPickerFor === "change" || mode === "chat"
                      ? "Apply"
                      : "Start chatting"}
                </Text>
              </LinearGradient>
            </Pressable>
            <Pressable onPress={() => setLangPickerVisible(false)} style={qm.dismiss}>
              <Text style={[qm.dismissText, { color: C.textMuted }]}>Cancel</Text>
            </Pressable>
          </Pressable>
        </Pressable>
      </Modal>
      {/* ── Cosmic Intelligence V3 — live timer packs ───────────────────── */}
      <Modal
        visible={v3PackVisible}
        transparent
        animationType="fade"
        onRequestClose={() => setV3PackVisible(false)}
      >
        <Pressable style={qm.backdrop} onPress={() => setV3PackVisible(false)}>
          <Pressable
            style={[qm.card, { backgroundColor: C.bgCard, borderColor: "#f59e0b55", maxHeight: "88%" }]}
            onPress={(e) => e.stopPropagation?.()}
          >
            <View style={[qm.iconWrap, { backgroundColor: "#f59e0b22", borderColor: "#f59e0b55" }]}>
              <Feather name="zap" size={26} color="#f59e0b" />
            </View>
            <Text style={[qm.title, { color: C.text, fontFamily: "Nunito_700Bold" }]}>
              Cosmic Intelligence V3
            </Text>
            <Text style={[qm.msg, { color: C.textMuted, marginBottom: 14, fontFamily: "Nunito_500Medium" }]}>
              Pick your live session timer. Exact timing + talk to your chart.
            </Text>

            <ScrollView style={{ width: "100%", maxHeight: 340 }} showsVerticalScrollIndicator={false}>
              {V3_LIVE_PACKS.map((pack) => {
                const active = v3PackId === pack.id;
                return (
                  <Pressable
                    key={pack.id}
                    onPress={() => {
                      Haptics.selectionAsync();
                      setV3PackId(pack.id);
                    }}
                    style={[
                      s.v3PackRow,
                      {
                        backgroundColor: active ? "#f59e0b18" : C.bgCard2,
                        borderColor: active ? "#f59e0b" : C.border,
                      },
                    ]}
                  >
                    <View style={[s.v3TimerBox, { backgroundColor: active ? "#f59e0b28" : C.bgCard }]}>
                      <Feather name="clock" size={14} color={active ? "#f59e0b" : C.textMuted} />
                      <Text
                        style={[
                          s.v3TimerText,
                          { color: active ? "#f59e0b" : C.text },
                        ]}
                      >
                        {pack.timer}
                      </Text>
                    </View>
                    <View style={{ flex: 1 }}>
                      <View style={s.v3PackTitleRow}>
                        <Text style={[s.v3PackLabel, { color: C.text }]}>{pack.label}</Text>
                        {pack.badge === "popular" ? (
                          <View style={[s.v3Badge, { backgroundColor: "#3b82f622", borderColor: "#3b82f6" }]}>
                            <Text style={[s.v3BadgeText, { color: "#60a5fa" }]}>MOST POPULAR</Text>
                          </View>
                        ) : null}
                        {pack.badge === "best" ? (
                          <View style={[s.v3Badge, { backgroundColor: "#22c55e22", borderColor: "#22c55e" }]}>
                            <Text style={[s.v3BadgeText, { color: "#4ade80" }]}>BEST VALUE</Text>
                          </View>
                        ) : null}
                      </View>
                      <Text style={[s.v3PackFeel, { color: C.textMuted }]}>{pack.feel}</Text>
                    </View>
                    <Text style={[s.v3PackPrice, { color: active ? "#f59e0b" : C.text }]}>
                      ₹{pack.priceInr.toLocaleString("en-IN")}
                    </Text>
                  </Pressable>
                );
              })}
            </ScrollView>

            {v3ReqError ? (
              <View
                style={{
                  width: "100%",
                  marginTop: 12,
                  paddingHorizontal: 12,
                  paddingVertical: 10,
                  borderRadius: 10,
                  borderWidth: 1,
                  borderColor: "#ef444466",
                  backgroundColor: "#ef444414",
                  flexDirection: "row",
                  alignItems: "center",
                  gap: 8,
                }}
              >
                <Feather name="alert-circle" size={14} color="#f87171" />
                <Text style={{ color: "#f87171", fontSize: 12.5, flex: 1, lineHeight: 17 }}>
                  {v3ReqError}
                </Text>
              </View>
            ) : null}

            <Pressable
              onPress={() => {
                void requestV3LiveSession();
              }}
              disabled={v3Requesting}
              style={({ pressed }) => [
                { width: "100%", marginTop: 14, opacity: pressed || v3Requesting ? 0.9 : 1 },
              ]}
            >
              <LinearGradient
                colors={["#d97706", "#f59e0b"]}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 0 }}
                style={qm.cta}
              >
                {v3Requesting ? (
                  <ActivityIndicator color="#fff" />
                ) : (
                  <>
                    <Feather name="credit-card" size={16} color="#fff" />
                    <Text style={qm.ctaText}>
                      Pay & connect · ₹
                      {(V3_LIVE_PACKS.find((p) => p.id === v3PackId)?.priceInr ?? 699).toLocaleString(
                        "en-IN",
                      )}
                    </Text>
                  </>
                )}
              </LinearGradient>
            </Pressable>
            <Pressable onPress={() => setV3PackVisible(false)} style={qm.dismiss}>
              <Text style={[qm.dismissText, { color: C.textMuted }]}>Cancel</Text>
            </Pressable>
          </Pressable>
        </Pressable>
      </Modal>

      {/* ── Cosmic Intelligence V1 — question packs ─────────────────────── */}
      <Modal
        visible={v1PackVisible}
        transparent
        animationType="fade"
        onRequestClose={() => setV1PackVisible(false)}
      >
        <Pressable style={qm.backdrop} onPress={() => setV1PackVisible(false)}>
          <Pressable
            style={[qm.card, { backgroundColor: C.bgCard, borderColor: "#3b82f655", maxHeight: "88%" }]}
            onPress={(e) => e.stopPropagation?.()}
          >
            <View style={[qm.iconWrap, { backgroundColor: "#3b82f622", borderColor: "#3b82f655" }]}>
              <Feather name="message-circle" size={26} color="#60a5fa" />
            </View>
            <Text style={[qm.title, { color: C.text, fontFamily: "Nunito_700Bold" }]}>
              Cosmic Intelligence V1
            </Text>
            <Text style={[qm.msg, { color: C.textMuted, marginBottom: 14, fontFamily: "Nunito_500Medium" }]}>
              Choose a question pack. Unused questions expire with the pack.
            </Text>

            <ScrollView style={{ width: "100%", maxHeight: 340 }} showsVerticalScrollIndicator={false}>
              {ASK_V1_PACKS.map((pack) => {
                const active = v1PackId === pack.id;
                return (
                  <Pressable
                    key={pack.id}
                    onPress={() => {
                      Haptics.selectionAsync();
                      setV1PackId(pack.id);
                    }}
                    style={[
                      s.v3PackRow,
                      {
                        backgroundColor: active ? "#3b82f618" : C.bgCard2,
                        borderColor: active ? "#3b82f6" : C.border,
                      },
                    ]}
                  >
                    <View style={[s.v3TimerBox, { backgroundColor: active ? "#3b82f628" : C.bgCard }]}>
                      <Feather name="hash" size={14} color={active ? "#60a5fa" : C.textMuted} />
                      <Text style={[s.v3TimerText, { color: active ? "#60a5fa" : C.text }]}>
                        {pack.questions}Q
                      </Text>
                    </View>
                    <View style={{ flex: 1 }}>
                      <View style={s.v3PackTitleRow}>
                        <Text style={[s.v3PackLabel, { color: C.text }]}>{pack.label}</Text>
                        {pack.badge === "popular" ? (
                          <View style={[s.v3Badge, { backgroundColor: "#3b82f622", borderColor: "#3b82f6" }]}>
                            <Text style={[s.v3BadgeText, { color: "#60a5fa" }]}>MOST POPULAR</Text>
                          </View>
                        ) : null}
                        {pack.badge === "best" ? (
                          <View style={[s.v3Badge, { backgroundColor: "#22c55e22", borderColor: "#22c55e" }]}>
                            <Text style={[s.v3BadgeText, { color: "#4ade80" }]}>BEST VALUE</Text>
                          </View>
                        ) : null}
                      </View>
                      <Text style={[s.v3PackFeel, { color: C.textMuted }]}>
                        {pack.feel} · {pack.days} days
                      </Text>
                    </View>
                    <Text style={[s.v3PackPrice, { color: active ? "#60a5fa" : C.text }]}>
                      ₹{pack.price_inr.toLocaleString("en-IN")}
                    </Text>
                  </Pressable>
                );
              })}
            </ScrollView>

            <Pressable
              onPress={() => {
                void buyV1Pack();
              }}
              disabled={v1PackBuying}
              style={({ pressed }) => [
                { width: "100%", marginTop: 14, opacity: pressed || v1PackBuying ? 0.9 : 1 },
              ]}
            >
              <LinearGradient
                colors={["#1e40af", "#3b82f6"]}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 0 }}
                style={qm.cta}
              >
                {v1PackBuying ? (
                  <ActivityIndicator color="#fff" />
                ) : (
                  <>
                    <Feather name="shopping-bag" size={16} color="#fff" />
                    <Text style={qm.ctaText}>
                      Buy · ₹
                      {(ASK_V1_PACKS.find((p) => p.id === v1PackId)?.price_inr ?? 99).toLocaleString(
                        "en-IN",
                      )}
                    </Text>
                  </>
                )}
              </LinearGradient>
            </Pressable>
            <Pressable onPress={() => setV1PackVisible(false)} style={qm.dismiss}>
              <Text style={[qm.dismissText, { color: C.textMuted }]}>Cancel</Text>
            </Pressable>
          </Pressable>
        </Pressable>
      </Modal>

      {/* ── V3 queued / waiting (persisted) — hidden while Ready modal shows ── */}
      <Modal
        visible={!!v3WaitingId && !v3ReadyVisible}
        transparent
        animationType="fade"
        onRequestClose={() => setV3WaitingId(null)}
      >
        <Pressable style={qm.backdrop} onPress={() => setV3WaitingId(null)}>
          <Pressable
            style={[qm.card, { backgroundColor: C.bgCard, borderColor: "#f59e0b55" }]}
            onPress={(e) => e.stopPropagation?.()}
          >
            <View style={[qm.iconWrap, { backgroundColor: "#f59e0b22", borderColor: "#f59e0b55" }]}>
              <ActivityIndicator color="#f59e0b" size="large" />
            </View>
            <View style={qm.busyLiveRow}>
              <GlowDot color="#f59e0b" size={7} />
              <Text style={qm.busyLiveText}>
                {v3EngineBusy || (v3QueuePosition != null && v3QueuePosition > 1)
                  ? "IN QUEUE"
                  : "WAITING"}
              </Text>
            </View>
            <Text style={[qm.title, { color: C.text, fontFamily: "Nunito_700Bold" }]}>
              {v3EngineBusy || (v3QueuePosition != null && v3QueuePosition > 1)
                ? "Engine is in another consultation"
                : "You are in the waiting list"}
            </Text>
            <Text style={[qm.msg, { color: C.textMuted, fontFamily: "Nunito_500Medium" }]}>
              {v3WaitingLabel ? `${v3WaitingLabel}\n\n` : ""}
              Cosmic Intelligence Engine is currently busy with another consultation.
              {v3QueuePosition != null
                ? `\n\nYour place in line: #${v3QueuePosition}`
                : ""}
              {"\n\n"}
              Stay in the app — when the engine is ready you will get a confirmation
              to Accept & Start. The timer starts only after you accept.
            </Text>
            <Pressable onPress={() => setV3WaitingId(null)} style={qm.dismiss}>
              <Text style={[qm.dismissText, { color: C.textMuted }]}>Hide for now</Text>
            </Pressable>
            <Pressable
              onPress={confirmCancelV3Waitlist}
              disabled={v3CancellingWait}
              style={[qm.dismiss, { marginTop: 0 }]}
            >
              {v3CancellingWait ? (
                <ActivityIndicator color="#ef4444" size="small" />
              ) : (
                <Text style={[qm.dismissText, { color: "#ef4444" }]}>
                  Leave waitlist
                </Text>
              )}
            </Pressable>
          </Pressable>
        </Pressable>
      </Modal>

      {/* ── V3 Ready — admin selected you; explicit Accept starts timer ── */}
      <Modal
        visible={v3ReadyVisible}
        transparent
        animationType="fade"
        onRequestClose={() => setV3ReadyVisible(false)}
      >
        <Reanimated.View entering={FadeIn.duration(220)} style={qm.backdrop}>
          <Pressable
            style={StyleSheet.absoluteFill}
            onPress={() => {
              /* keep modal — must Accept or wait for timeout requeue */
            }}
          />
          <Reanimated.View entering={ZoomIn.springify().damping(14).stiffness(160)}>
            <LinearGradient
              colors={["#14261a", "#0a1a12"]}
              start={{ x: 0, y: 0 }}
              end={{ x: 0, y: 1 }}
              style={[qm.card, { borderColor: "#34d39988", overflow: "hidden" }]}
            >
              <View style={[qm.iconWrap, { backgroundColor: "#34d39922", borderColor: "#34d39966" }]}>
                <Text style={{ fontSize: 28 }}>✨</Text>
              </View>
              <View style={[qm.busyLiveRow, { borderColor: "#34d39955", backgroundColor: "#34d39914" }]}>
                <GlowDot color="#34d399" size={7} />
                <Text style={[qm.busyLiveText, { color: "#6ee7b7" }]}>READY FOR YOU</Text>
              </View>
              <Text style={[qm.title, { color: "#fff", fontFamily: "Nunito_700Bold" }]}>
                Cosmic Intelligence is ready
              </Text>
              <Text style={[qm.msg, { color: "#a7f3d0", fontFamily: "Nunito_500Medium" }]}>
                {(v3ReadySession?.label || v3WaitingLabel || "Live") +
                  (v3ReadySession?.priceInr
                    ? ` · ₹${v3ReadySession.priceInr.toLocaleString("en-IN")}`
                    : "")}
                {"\n\n"}
                Tap Accept & Start within 2 minutes to begin your live session.
                If you miss it, you return to the end of the queue.
                {typeof v3ReadySession?.awaitingRemaining === "number"
                  ? `\n\nTime left: ${Math.max(0, Math.ceil(v3ReadySession.awaitingRemaining))}s`
                  : ""}
              </Text>
              <Pressable
                onPress={() => {
                  void acceptV3ReadySession();
                }}
                disabled={v3Accepting}
                style={({ pressed }) => [
                  { width: "100%", marginTop: 8, opacity: pressed || v3Accepting ? 0.9 : 1 },
                ]}
              >
                <LinearGradient
                  colors={["#059669", "#34d399"]}
                  start={{ x: 0, y: 0 }}
                  end={{ x: 1, y: 0 }}
                  style={qm.cta}
                >
                  {v3Accepting ? (
                    <ActivityIndicator color="#fff" />
                  ) : (
                    <>
                      <Feather name="check-circle" size={16} color="#fff" />
                      <Text style={qm.ctaText}>Accept & Start</Text>
                    </>
                  )}
                </LinearGradient>
              </Pressable>
              <Pressable
                onPress={() => setV3ReadyVisible(false)}
                style={qm.dismiss}
              >
                <Text style={[qm.dismissText, { color: "#86efac99" }]}>
                  Keep waiting in background
                </Text>
              </Pressable>
              <Pressable
                onPress={confirmCancelV3Waitlist}
                disabled={v3CancellingWait || v3Accepting}
                style={[qm.dismiss, { marginTop: 0 }]}
              >
                {v3CancellingWait ? (
                  <ActivityIndicator color="#f87171" size="small" />
                ) : (
                  <Text style={[qm.dismissText, { color: "#f87171" }]}>
                    Leave waitlist
                  </Text>
                )}
              </Pressable>
            </LinearGradient>
          </Reanimated.View>
        </Reanimated.View>
      </Modal>

      {/* ── Legacy busy popup (unused for queue path; kept for soft dismiss) ── */}
      <Modal
        visible={v3BusyVisible}
        transparent
        animationType="fade"
        onRequestClose={() => setV3BusyVisible(false)}
      >
        <Reanimated.View entering={FadeIn.duration(220)} style={qm.backdrop}>
          <Pressable style={StyleSheet.absoluteFill} onPress={() => setV3BusyVisible(false)} />
          <Reanimated.View entering={ZoomIn.springify().damping(14).stiffness(160)}>
            <LinearGradient
              colors={["#1c1230", "#0f0a1e"]}
              start={{ x: 0, y: 0 }}
              end={{ x: 0, y: 1 }}
              style={[qm.card, { borderColor: "#f59e0b66", overflow: "hidden" }]}
            >
              <View style={qm.busyIconStage}>
                <BusyPulseRing delayMs={0} color="#f59e0b" />
                <BusyPulseRing delayMs={750} color="#fbbf24" />
                <BusyPulseRing delayMs={1500} color="#f59e0b" />
                <View style={[qm.iconWrap, { backgroundColor: "#f59e0b22", borderColor: "#f59e0b66", marginBottom: 0 }]}>
                  <BusyBreathingIcon>
                    <Text style={{ fontSize: 28 }}>🔮</Text>
                  </BusyBreathingIcon>
                </View>
              </View>
              <View style={qm.busyLiveRow}>
                <GlowDot color="#f59e0b" size={7} />
                <Text style={qm.busyLiveText}>IN SESSION</Text>
              </View>
              <Text style={[qm.title, { color: "#fff", fontFamily: "Nunito_700Bold" }]}>
                Engine is in a Live Consultation
              </Text>
              <Text style={[qm.msg, { color: "#c4b5fd", fontFamily: "Nunito_500Medium" }]}>
                Cosmic Intelligence Engine is currently busy with another consultation.
                You have been added to the waiting list — when the engine is ready you will
                get a notification to Accept & Start.
              </Text>
              <Pressable
                onPress={() => setV3BusyVisible(false)}
                style={({ pressed }) => [{ width: "100%", marginTop: 8, opacity: pressed ? 0.9 : 1 }]}
              >
                <LinearGradient
                  colors={["#d97706", "#f59e0b"]}
                  start={{ x: 0, y: 0 }}
                  end={{ x: 1, y: 0 }}
                  style={qm.cta}
                >
                  <Feather name="clock" size={15} color="#fff" />
                  <Text style={qm.ctaText}>Got it — I&apos;m waiting</Text>
                </LinearGradient>
              </Pressable>
            </LinearGradient>
          </Reanimated.View>
        </Reanimated.View>
      </Modal>
    </KeyboardAvoidingView>
    </View>
  );
}

const qm = StyleSheet.create({
  backdrop: {
    flex: 1,
    backgroundColor: "rgba(0,0,0,0.6)",
    alignItems: "center",
    justifyContent: "center",
    paddingHorizontal: 24,
  },
  card: {
    width: "100%",
    maxWidth: 360,
    borderRadius: 20,
    borderWidth: 1.5,
    padding: 24,
    alignItems: "center",
    gap: 10,
  },
  iconWrap: {
    width: 60, height: 60, borderRadius: 16, borderWidth: 1.5,
    alignItems: "center", justifyContent: "center",
    marginBottom: 4,
  },
  busyIconStage: {
    width: 110, height: 110,
    alignItems: "center", justifyContent: "center",
    marginBottom: 2,
  },
  busyLiveRow: {
    flexDirection: "row", alignItems: "center", gap: 8,
    paddingHorizontal: 12, paddingVertical: 5,
    borderRadius: 999, borderWidth: 1, borderColor: "#f59e0b55",
    backgroundColor: "#f59e0b14",
    marginBottom: 6,
  },
  busyLiveText: {
    color: "#fbbf24", fontSize: 10.5, fontWeight: "800", letterSpacing: 1.6,
  },
  title: {
    fontSize: 19, fontWeight: "700", letterSpacing: -0.3, textAlign: "center",
  },
  usage: { fontSize: 13, textAlign: "center" },
  msg: {
    fontSize: 12.5, textAlign: "center", lineHeight: 18, marginBottom: 6,
  },
  cta: {
    flexDirection: "row", alignItems: "center", justifyContent: "center",
    gap: 8, paddingVertical: 13, borderRadius: 13,
  },
  ctaText: { color: "#fff", fontSize: 14.5, fontWeight: "700" },
  dismiss: { paddingVertical: 8, paddingHorizontal: 16, marginTop: 4 },
  dismissText: { fontSize: 12.5, fontWeight: "600" },
});

const s = StyleSheet.create({
  root: { flex: 1 },

  header: {
    alignItems: "center",
    paddingBottom: 10,
    paddingHorizontal: 12,
    borderBottomWidth: 1,
    borderBottomColor: "rgba(255,255,255,0.04)",
    gap: 2,
  },
  headerDot: {
    width: 8, height: 8, borderRadius: 4, backgroundColor: "#22c55e",
    marginBottom: 4,
  },
  headerTitle: {
    color: "#dde8f4", fontSize: 14, fontWeight: "700", letterSpacing: -0.3,
    textShadowColor: "rgba(139,92,246,0.5)",
    textShadowOffset: { width: 0, height: 0 },
    textShadowRadius: 12,
    maxWidth: "82%",
  },
  headerSub: { color: "#3d5a7a", fontSize: 10.5, textAlign: "center", lineHeight: 14 },
  headerTopRow: {
    flexDirection: "row",
    alignItems: "flex-start",
    width: "100%",
    gap: 8,
  },
  planSideCard: {
    width: 128,
    flexShrink: 0,
    borderRadius: 16,
    paddingHorizontal: 10,
    paddingVertical: 9,
    gap: 4,
    overflow: "hidden",
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.28,
    shadowRadius: 10,
    elevation: 6,
  },
  planSideTop: {
    flexDirection: "row",
    alignItems: "center",
    gap: 5,
  },
  planSideIconBubble: {
    width: 20,
    height: 20,
    borderRadius: 7,
    backgroundColor: "rgba(255,255,255,0.22)",
    alignItems: "center",
    justifyContent: "center",
  },
  planSideName: {
    fontSize: 11,
    fontFamily: "Nunito_700Bold",
    letterSpacing: 0.2,
    flexShrink: 1,
  },
  planSideNameOnGrad: {
    color: "#fff",
    fontSize: 11,
    fontFamily: "Nunito_800ExtraBold",
    letterSpacing: 0.3,
    flexShrink: 1,
    textShadowColor: "rgba(0,0,0,0.2)",
    textShadowOffset: { width: 0, height: 1 },
    textShadowRadius: 2,
  },
  planSideQ: {
    fontSize: 16,
    fontFamily: "Nunito_800ExtraBold",
    letterSpacing: -0.3,
    marginTop: 2,
  },
  planSideQOnGrad: {
    color: "#fff",
    fontSize: 20,
    fontFamily: "Nunito_800ExtraBold",
    letterSpacing: -0.5,
    marginTop: 1,
    textShadowColor: "rgba(0,0,0,0.18)",
    textShadowOffset: { width: 0, height: 1 },
    textShadowRadius: 3,
  },
  planSideQTotalOnGrad: {
    color: "rgba(255,255,255,0.78)",
    fontSize: 13,
    fontFamily: "Nunito_700Bold",
  },
  planSideMeta: {
    fontSize: 9.5,
    fontFamily: "Nunito_500Medium",
    lineHeight: 12,
  },
  planSideDots: {
    flexDirection: "row",
    alignItems: "center",
    gap: 5,
    marginTop: 2,
    marginBottom: 2,
  },
  planSideDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    borderWidth: 1,
  },
  planSideCtaPill: {
    alignSelf: "flex-start",
    marginTop: 2,
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 999,
    backgroundColor: "rgba(255,255,255,0.22)",
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: "rgba(255,255,255,0.35)",
  },
  planSideCtaText: {
    color: "#fff",
    fontSize: 9.5,
    fontFamily: "Nunito_700Bold",
    letterSpacing: 0.2,
  },
  walletBar: {
    marginTop: 8,
    marginHorizontal: 16,
    marginBottom: 4,
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    alignSelf: "center",
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 999,
    borderWidth: 1,
  },
  walletBarText: {
    fontSize: 12,
    fontFamily: "Nunito_700Bold",
    letterSpacing: 0.1,
  },
  walletBarMeta: {
    fontSize: 11,
    fontFamily: "Nunito_500Medium",
  },
  walletWarn: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 12,
    borderWidth: 1,
  },
  walletWarnText: {
    flex: 1,
    fontSize: 11.5,
    fontFamily: "Nunito_600SemiBold",
    lineHeight: 15,
  },
  walletWarnCta: {
    flexDirection: "row",
    alignItems: "center",
    gap: 3,
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 999,
    backgroundColor: "#e11d48",
  },
  walletWarnCtaText: {
    color: "#fff",
    fontSize: 11,
    fontFamily: "Nunito_800ExtraBold",
  },
  langPickRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    width: "100%",
    paddingVertical: 12,
    paddingHorizontal: 14,
    borderRadius: 12,
    borderWidth: 1,
    marginBottom: 8,
  },
  langPickTitle: { fontSize: 15, fontWeight: "700" },
  langPickSub: { fontSize: 12, marginTop: 2 },
  v3LiveBanner: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    marginHorizontal: 14,
    marginBottom: 8,
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 12,
    borderWidth: 1,
  },
  v3LiveBannerText: {
    flex: 1,
    color: "#fbbf24",
    fontSize: 12,
    fontFamily: "Nunito_700Bold",
  },
  v3PackRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    width: "100%",
    paddingVertical: 12,
    paddingHorizontal: 12,
    borderRadius: 14,
    borderWidth: 1.5,
    marginBottom: 8,
  },
  v3TimerBox: {
    alignItems: "center",
    justifyContent: "center",
    gap: 4,
    minWidth: 64,
    paddingVertical: 8,
    paddingHorizontal: 8,
    borderRadius: 12,
  },
  v3TimerText: {
    fontSize: 15,
    fontFamily: "Nunito_700Bold",
    letterSpacing: 0.5,
  },
  v3PackTitleRow: {
    flexDirection: "row",
    alignItems: "center",
    flexWrap: "wrap",
    gap: 6,
  },
  v3PackLabel: {
    fontSize: 15,
    fontFamily: "Nunito_700Bold",
  },
  v3PackFeel: {
    fontSize: 11,
    fontFamily: "Nunito_500Medium",
    marginTop: 2,
  },
  v3PackPrice: {
    fontSize: 16,
    fontFamily: "Nunito_700Bold",
  },
  v3Badge: {
    paddingHorizontal: 7,
    paddingVertical: 2,
    borderRadius: 999,
    borderWidth: 1,
  },
  v3BadgeText: {
    fontSize: 9,
    fontFamily: "Nunito_700Bold",
    letterSpacing: 0.3,
  },
  headerTitleRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "flex-start",
    maxWidth: "100%",
    paddingHorizontal: 0,
  },
  headerTitleGlow: {
    position: "absolute",
    alignSelf: "center",
    width: 180, height: 28, borderRadius: 16,
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.9,
    shadowRadius: 22,
    elevation: 0,
  },
  headerLiveDot:  { width: 7, height: 7, borderRadius: 4, marginLeft: 8 },
  heroBadgeRow:   { flexDirection: "row", marginTop: 4 },
  heroBadge: {
    flexDirection: "row",
    alignItems: "center",
    gap: 5,
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 999,
    borderWidth: 1,
    maxWidth: "92%",
  },
  heroBadgeText: { fontSize: 10.5, fontWeight: "700", letterSpacing: 0.2 },
  heroTagline: {
    fontSize: 11,
    fontFamily: "Nunito_500Medium",
    textAlign: "center",
    lineHeight: 14,
    marginTop: 6,
    marginBottom: 0,
    paddingHorizontal: 20,
  },

  modeSwitch: {
    flexDirection: "row",
    marginHorizontal: 16,
    marginTop: 10,
    padding: 4,
    borderRadius: 12,
    borderWidth: 1,
    gap: 4,
  },
  modeSwitchSeg: {
    flex: 1,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 6,
    paddingVertical: 8,
    paddingHorizontal: 8,
    borderRadius: 9,
    borderWidth: 1,
    borderColor: "transparent",
  },
  modeSwitchActive: {},
  modeSwitchSegActive: {
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.45,
    shadowRadius: 9,
    elevation: 5,
  },
  modeSwitchLiveDot: { marginLeft: 2 },
  modeSwitchText: {
    fontSize: 12,
    fontWeight: "700",
    letterSpacing: 0.2,
  },

  prashnaNumRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderTopWidth: StyleSheet.hairlineWidth,
  },
  prashnaNumWrap: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 10,
    borderWidth: 1.5,
    minWidth: 110,
  },
  prashnaNumInput: {
    fontSize: 16,
    fontWeight: "700",
    letterSpacing: 1,
    minWidth: 60,
    paddingVertical: 0,
  },
  prashnaNumHint: {
    flex: 1,
    fontSize: 11,
    fontStyle: "italic",
  },
  backBtn: {
    position: "absolute", left: 12, top: 0, bottom: 0,
    justifyContent: "center", paddingHorizontal: 4,
  },

  // ── Mode picker ─────────────────────────────────────────────────────────
  pickerWrap: {
    paddingHorizontal: 16,
    paddingTop: 6,
    paddingBottom: 24,
    gap: 10,
  },
  pickerHero: {
    alignItems: "center",
    paddingBottom: 2,
  },
  pickerHi:   { fontSize: 22, fontWeight: "800", letterSpacing: -0.4 },
  pickerSub:  { fontSize: 13, marginBottom: 14 },
  modeCard: {
    borderRadius: 16, overflow: "hidden",
    shadowColor: "#3b82f6",
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.4,
    shadowRadius: 14,
    elevation: 8,
  },
  modeGrad: {
    paddingHorizontal: 14, paddingVertical: 13,
    flexDirection: "row", alignItems: "center", gap: 10,
  },
  modeIconWrap: {
    width: 44, height: 44, borderRadius: 13,
    alignItems: "center", justifyContent: "center",
    backgroundColor: "rgba(255,255,255,0.16)",
    borderWidth: 1, borderColor: "rgba(255,255,255,0.22)",
  },
  modeEmoji: { fontSize: 24 },
  modeTitleRow: {
    flexDirection: "row",
    alignItems: "center",
    flexWrap: "wrap",
    gap: 6,
  },
  modeTitle: { color: "#fff", fontSize: 15.5, fontWeight: "800", letterSpacing: -0.3, flexShrink: 1 },
  modeBody:  { color: "#ffffffd0", fontSize: 12, lineHeight: 16, marginTop: 3 },
  modeMeta:  { flexDirection: "row", alignItems: "center", gap: 5, marginTop: 5 },
  modeMetaText: { color: "#ffffffcc", fontSize: 10, fontWeight: "600", flexShrink: 1 },
  modeRectifyHint: {
    color: "#ffffffb8",
    fontSize: 10.5,
    fontWeight: "600",
    marginTop: 7,
    lineHeight: 14,
  },
  rectifyCard: {
    shadowOpacity: 0.5,
    shadowRadius: 20,
    elevation: 12,
  },
  rectifyGrad: {
    paddingHorizontal: 16,
    paddingVertical: 18,
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    overflow: "hidden",
  },
  rectifyCtaRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    marginTop: 10,
    alignSelf: "flex-start",
    backgroundColor: "rgba(0,0,0,0.22)",
    paddingHorizontal: 12,
    paddingVertical: 7,
    borderRadius: 999,
    borderWidth: 1,
    borderColor: "rgba(255,255,255,0.28)",
  },
  rectifyCtaOnGrad: {
    color: "#fff",
    fontSize: 12.5,
    fontWeight: "800",
    letterSpacing: 0.2,
  },
  modeBadge: {
    backgroundColor: "rgba(0,0,0,0.28)",
    paddingHorizontal: 7, paddingVertical: 2, borderRadius: 8,
  },
  modeBadgeText: { color: "#fff", fontSize: 9.5, fontWeight: "800", letterSpacing: 0.3 },
  legacyLink: {
    flexDirection: "row", alignItems: "center", justifyContent: "center",
    gap: 6, paddingVertical: 10, marginTop: 2,
  },
  legacyLinkText: { fontSize: 12, fontWeight: "600" },

  demoBanner: {
    flexDirection: "row", alignItems: "center", gap: 7,
    backgroundColor: "rgba(251,191,36,0.06)", borderBottomWidth: 1,
    borderBottomColor: "rgba(251,191,36,0.12)", paddingHorizontal: 20, paddingVertical: 10,
    justifyContent: "center",
  },
  demoText: { color: "#fbbf24", fontSize: 12, flex: 1, textAlign: "center" },

  list: { paddingHorizontal: 16, paddingTop: 12, gap: 10 },

  bubble: { flexDirection: "row", gap: 8, marginBottom: 10 },
  bubbleUser:      { justifyContent: "flex-end" },
  bubbleAssistant: { justifyContent: "flex-start" },

  avatar: {
    width: 30, height: 30, borderRadius: 15,
    borderWidth: 1,
    alignItems: "center", justifyContent: "center",
    alignSelf: "flex-end",
  },
  avatarGlow: {
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.6,
    shadowRadius: 8,
    elevation: 6,
  },

  bubbleInner: {
    maxWidth: "80%", borderRadius: 18, paddingHorizontal: 14, paddingVertical: 11,
  },
  bubbleInnerUser: {
    borderBottomRightRadius: 5, borderWidth: 1,
  },
  bubbleInnerAssistant: {
    borderWidth: 1,
    borderBottomLeftRadius: 5,
  },
  // Strong glow for the gradient user bubble.
  bubbleGlow: {
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.4,
    shadowRadius: 12,
    elevation: 7,
  },
  // Soft, subtle lift for the assistant bubble.
  bubbleGlowSoft: {
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.18,
    shadowRadius: 10,
    elevation: 3,
  },
  bubbleText:       { fontSize: 14, lineHeight: 21 },
  bubbleTextUser:   { color: "#FFFFFF", fontWeight: "600" },
  bubbleTextAssist: { color: "#94a3b8" },

  followUpsRow: {
    flexDirection: "row",
    gap: 8,
    paddingHorizontal: 16,
    paddingTop: 4,
    paddingBottom: 8,
  },
  followUpChip: {
    flexDirection: "row",
    alignItems: "center",
    gap: 5,
    paddingHorizontal: 11,
    paddingVertical: 7,
    borderRadius: 16,
    borderWidth: 1,
  },
  followUpText: { fontSize: 12, fontWeight: "600" },

  // Phase 2.5.11.6 — Partner-CTA button. Sits below the assistant
  // bubble on the special "requires_partner_profile" reply. Tapping
  // routes to /profile-edit?relation=<hint> so the user lands in the
  // Add-profile modal pre-set to the right slot.
  partnerCtaBtn: {
    flexDirection:    "row",
    alignItems:       "center",
    justifyContent:   "center",
    gap:              8,
    marginHorizontal: 16,
    marginTop:        8,
    paddingHorizontal: 14,
    paddingVertical:  10,
    borderRadius:     12,
    borderWidth:      1,
  },
  partnerCtaText: { fontSize: 13, fontWeight: "700", color: "#FFFFFF" },

  // Phase 7.5 — Clarifier UX styles. Banner sits below the assistant
  // bubble, above the follow-up chips, on the latest reply only.
  clarifierBanner: {
    marginHorizontal: 16,
    marginTop: 6,
    paddingHorizontal: 12,
    paddingVertical: 9,
    borderRadius: 12,
    borderWidth: 1,
  },
  clarifierTitle: {
    fontSize: 12,
    fontWeight: "500",
    marginBottom: 8,
    lineHeight: 16,
  },
  clarifierRow: {
    flexDirection: "row",
    gap: 7,
    paddingVertical: 1,
  },
  clarifierChip: {
    flexDirection: "row",
    alignItems: "center",
    gap: 5,
    paddingHorizontal: 11,
    paddingVertical: 7,
    borderRadius: 14,
    borderWidth: 1,
  },
  clarifierChipText: { fontSize: 12, fontWeight: "600" },

  starters: {
    paddingHorizontal: 16, paddingBottom: 10, gap: 8,
  },
  starter: {
    flexDirection: "row", alignItems: "center", gap: 10,
    paddingHorizontal: 14, paddingVertical: 13, borderRadius: 14,
    borderWidth: 1,
    // backgroundColor + borderColor injected at render-time from theme.
  },
  starterText: { fontSize: 13.5, fontWeight: "600", flex: 1 },

  // ── Phase 6.1.1 — Kundli selector pill row (above input) ───────────────
  kundliRow: {
    flexDirection: "row", alignItems: "center", gap: 10,
    paddingHorizontal: 14, paddingTop: 8, paddingBottom: 8,
    borderTopWidth: StyleSheet.hairlineWidth,
  },
  kundliRowLabel: {
    fontSize: 11, fontWeight: "600", letterSpacing: 0.3,
    textTransform: "uppercase",
  },
  kundliPill: {
    paddingHorizontal: 12, paddingVertical: 6, borderRadius: 16,
    borderWidth: 1, minHeight: 30, justifyContent: "center",
  },
  kundliPillText: { fontSize: 12 },

  // ── Recent Questions strip ─────────────────────────────────────────────
  historyWrap:   { marginTop: 22, gap: 8 },
  historyHeader: { flexDirection: "row", alignItems: "center", gap: 6, marginBottom: 4, paddingHorizontal: 4 },
  historyTitle:  { fontSize: 12, fontWeight: "700", letterSpacing: 0.4, textTransform: "uppercase" },
  historyItem: {
    flexDirection: "row", alignItems: "center", gap: 10,
    paddingVertical: 12, paddingHorizontal: 14,
    borderRadius: 14, borderWidth: 1,
    // backgroundColor + borderColor injected from theme at render time.
  },
  historyQ:       { fontSize: 14, fontWeight: "600", lineHeight: 19 },
  historyMeta:    { flexDirection: "row", alignItems: "center", gap: 8, marginTop: 2 },
  historyTag: {
    paddingHorizontal: 8, paddingVertical: 2, borderRadius: 8, borderWidth: 1,
    maxWidth: 160,
  },
  historyTagText: { fontSize: 11, fontWeight: "700" },
  historyTime:    { fontSize: 11 },

  // ── In-chat Recent Questions strip (fresh thread only) ─────────────────
  chatHistoryWrap:   { paddingTop: 6, paddingBottom: 4 },
  chatHistoryHeader: {
    flexDirection: "row", alignItems: "center", gap: 6,
    paddingHorizontal: 16, marginBottom: 8,
  },
  chatHistoryRow:    { flexDirection: "row", gap: 8, paddingHorizontal: 16 },
  chatHistoryChip: {
    maxWidth: 230, gap: 3,
    paddingHorizontal: 12, paddingVertical: 9,
    borderRadius: 14, borderWidth: 1,
  },
  chatHistoryQ:    { fontSize: 13, fontWeight: "600" },
  chatHistoryMeta: { flexDirection: "row", alignItems: "center", gap: 2 },
  chatHistoryTag:  { fontSize: 10.5, fontWeight: "700", maxWidth: 150 },
  chatHistoryTime: { fontSize: 10.5 },

  inputRow: {
    flexDirection: "row", alignItems: "flex-end", gap: 10,
    paddingHorizontal: 14, paddingTop: 12,
    borderTopWidth: StyleSheet.hairlineWidth,
    // borderTopColor + backgroundColor injected at render-time from theme.
  },
  input: {
    flex: 1, borderRadius: 24, borderWidth: 1,
    paddingHorizontal: 18, paddingVertical: 13,
    fontSize: 15, lineHeight: 21, maxHeight: 120, minHeight: 50,
    // Subtle lift so the bar reads as a premium floating composer.
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 8,
    elevation: 4,
    // backgroundColor + borderColor + color injected at render-time from theme.
  },
  sendBtn:  { borderRadius: 22 },
  sendBtnGlow: {
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.55,
    shadowRadius: 12,
    elevation: 8,
  },
  sendGrad: { width: 44, height: 44, borderRadius: 22, alignItems: "center", justifyContent: "center", overflow: "hidden" },
});
