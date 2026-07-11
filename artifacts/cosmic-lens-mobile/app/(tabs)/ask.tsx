import { Feather } from "@expo/vector-icons";
import { LinearGradient } from "expo-linear-gradient";
import * as Clipboard from "expo-clipboard";
import * as Haptics from "expo-haptics";
import {
  useAudioPlayer, useAudioPlayerStatus, useAudioRecorder,
  setAudioModeAsync, requestRecordingPermissionsAsync,
  RecordingPresets,
} from "expo-audio";
import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
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
  View,
} from "react-native";
// Edge-to-edge aware KeyboardAvoidingView. RN's built-in one relies on the
// old Android `adjustResize` window shrink, which SDK 54 edge-to-edge
// disables — so the input would hide behind the keyboard. This drop-in
// (backed by the root <KeyboardProvider/>) tracks the keyboard frame
// natively and pushes the input flush above it on both platforms.
import { KeyboardAvoidingView } from "react-native-keyboard-controller";
import AsyncStorage from "@react-native-async-storage/async-storage";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import Reanimated, {
  Easing as REasing,
  FadeInLeft,
  FadeInRight,
  interpolate,
  useAnimatedStyle,
  useSharedValue,
  withDelay,
  withRepeat,
  withTiming,
} from "react-native-reanimated";
import { FadeInView, staggerDelay } from "@/components/motion/FadeInView";
import { AcharyaTypingDots } from "@/components/AcharyaTypingDots";
import { CardsCarousel, type CardData } from "@/components/CardsCarousel";
import { MarkdownReply } from "@/components/MarkdownReply";
import { useC } from "@/context/ThemeContext";
import { useUser } from "@/context/UserContext";
import { useT } from "@/hooks/useT";
import { getT } from "@/lib/i18n";
import { router, useFocusEffect } from "expo-router";
import { useTabBar } from "@/context/TabBarContext";

import { API_BASE, apiFetch } from "@/lib/apiConfig";
import {
  ASK_REPLY_LANG_OPTIONS,
  ASK_REPLY_LANG_STORAGE_KEY,
  askLangToApi,
  loadAskReplyLang,
  type AskReplyLang,
} from "@/lib/askReplyLang";

interface Message {
  id: string;
  role: "user" | "assistant";
  text: string;
  loading?: boolean;
  streaming?: boolean;
  followUps?: string[];
  // P6: v2 multi-intent response — when present, the bubble renders a
  // swipeable cards carousel instead of a single MarkdownReply. `text` is
  // still populated with the legacy combined string so voice playback,
  // copy, and regenerate continue to work unchanged.
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
// "answered:health", "yellow_wait", "love_likely"). Map a small known set
// to user-friendly Hinglish labels; fall back to title-casing otherwise.
const VERDICT_LABELS: Record<string, string> = {
  "answered":         "Reply mila",
  "answered:health":  "Health update",
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
    x.value = withRepeat(
      withDelay(700, withTiming(1, { duration: 1500, easing: REasing.inOut(REasing.ease) })),
      -1,
      false,
    );
  }, [x]);
  const style = useAnimatedStyle(() => ({
    transform: [
      { translateX: interpolate(x.value, [0, 1], [-160, 420]) },
      { rotate: "20deg" },
    ],
    opacity: interpolate(x.value, [0, 0.25, 0.5, 0.75, 1], [0, 0.5, 0.7, 0.5, 0]),
  }));
  return (
    <Reanimated.View
      pointerEvents="none"
      style={[
        { position: "absolute", top: -60, bottom: -60, width: 46, backgroundColor: "rgba(255,255,255,0.28)" },
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

const DNA_DOMAIN_LABEL: Record<string, string> = {
  love: "Relationship",
  marriage: "Marriage",
  career: "Career",
  finance: "Finance",
  health: "Health",
  family: "Family",
  education: "Education",
  travel: "Travel",
  legal: "Legal",
  spiritual: "Spiritual",
  general: "General",
};

const DNA_BUCKET_LABEL: Record<string, string> = {
  relationship_promise: "Relationship Promise",
  love_feelings: "Love & Feelings",
  partner_nature: "Partner Nature",
  compatibility: "Compatibility",
  commitment: "Commitment",
  trust_loyalty: "Trust & Loyalty",
  communication: "Communication",
  emotional_bonding: "Emotional Bonding",
  physical_intimacy: "Physical & Intimacy",
  third_person_infidelity: "Third Person / Infidelity",
  dating_courtship: "Dating & Courtship",
  long_distance: "Long Distance",
  family_social_acceptance: "Family & Social Acceptance",
  relationship_challenges: "Relationship Challenges",
  toxicity_red_flags: "Toxicity & Red Flags",
  breakup_separation: "Breakup & Separation",
  reconciliation_ex: "Reconciliation & Ex",
  marriage_potential: "Marriage Potential",
  relationship_future: "Relationship Outcome / Long-term Stability",
  relationship_decisions: "Relationship Decisions",
  spiritual_karmic: "Soulmate & Karmic Connection",
  relationship_remedies: "Relationship Remedies",
  unknown_relationship_intent: "Unknown (Audit)",
  general_mr: "Marriage General",
  govt_job: "Government Job",
  career_milestones: "Career Milestones",
};

const DNA_ENGINE_ARCHETYPE_LABEL: Record<string, string> = {
  karmic_marriage: "Soulmate & Karmic Connection",
  relationship_future: "Relationship Outcome / Long-term Stability",
};

const DNA_SUBJECT_LABEL: Record<string, string> = {
  self: "Self",
  partner: "Partner",
  spouse: "Spouse",
  family_member: "Family Member",
  other_person: "Other Person",
  subject_person: "Subject Person",
};

const DNA_TARGET_LABEL: Record<string, string> = {
  self: "Self",
  self_relationship: "Self (Relationship)",
  subject_person: "Subject Person",
  event: "Event",
  situation: "Situation",
};

function dnaDisplayLabel(map: Record<string, string>, key?: string | null): string {
  if (!key) return "—";
  return map[key] || key.replace(/_/g, " ");
}

function dnaYesNo(v?: boolean | null): string {
  if (v === true) return "Yes";
  if (v === false) return "No";
  return "—";
}

function dnaConfPct(v?: number | null): string {
  if (typeof v !== "number" || Number.isNaN(v)) return "—";
  return `${(v * 100).toFixed(0)}%`;
}

type DnaCopySub = {
  normalized_question?: string;
  domain?: string;
  bucket?: string;
  engine_archetype?: string | null;
  intent?: string;
  subject?: string;
  target?: string;
  question_type?: string;
  timing?: boolean;
  tense?: string;
  emotion?: string;
  risk?: string;
  is_followup?: boolean;
  followup_of?: string;
  confidence?: number;
  bucket_match_score?: number;
  bucket_match_confidence?: string;
  bucket_coerced?: boolean;
  required_modules?: string[];
};

type DnaCopyItem = {
  index?: number;
  question: string;
  normalized_question?: string;
  domain?: string;
  bucket?: string;
  engine_archetype?: string | null;
  intent?: string;
  subject?: string;
  target?: string;
  question_type?: string;
  timing?: boolean;
  tense?: string;
  emotion?: string;
  risk?: string;
  is_followup?: boolean;
  followup_of?: string;
  confidence?: number;
  bucket_match_score?: number;
  bucket_match_confidence?: string;
  bucket_coerced?: boolean;
  required_modules?: string[];
  latency_ms?: number;
  dna?: { questions?: DnaCopySub[] };
};

function dnaSubsFromItem(it: DnaCopyItem): DnaCopySub[] {
  const subs = it.dna?.questions;
  const multi = Array.isArray(subs) && subs.length > 1;
  if (multi) return subs!;
  return [{
    normalized_question: it.normalized_question || it.question,
    domain: it.domain,
    bucket: it.bucket,
    engine_archetype: it.engine_archetype,
    intent: it.intent,
    subject: it.subject,
    target: it.target,
    question_type: it.question_type,
    timing: it.timing,
    tense: it.tense,
    emotion: it.emotion,
    risk: it.risk,
    is_followup: it.is_followup,
    followup_of: it.followup_of,
    confidence: it.confidence,
    bucket_match_score: it.bucket_match_score,
    bucket_match_confidence: it.bucket_match_confidence,
    bucket_coerced: it.bucket_coerced,
    required_modules: it.required_modules,
  }];
}

function formatDnaSubForCopy(sub: DnaCopySub, splitLabel?: string): string {
  const lines: string[] = [];
  if (splitLabel) lines.push(splitLabel);
  const add = (label: string, value: string) => lines.push(`${label}: ${value}`);
  add("Normalized", sub.normalized_question || "—");
  add("Domain", `${dnaDisplayLabel(DNA_DOMAIN_LABEL, sub.domain)} (${sub.domain || "—"})`);
  add("Bucket", `${dnaDisplayLabel(DNA_BUCKET_LABEL, sub.bucket)} (${sub.bucket || "—"})`);
  add("Intent", sub.intent || "—");
  add("Subject", `${dnaDisplayLabel(DNA_SUBJECT_LABEL, sub.subject)} (${sub.subject || "—"})`);
  add("Target", `${dnaDisplayLabel(DNA_TARGET_LABEL, sub.target)} (${sub.target || "—"})`);
  add("Question Type", sub.question_type ? sub.question_type.replace(/_/g, " ") : "—");
  add("Timing Required", dnaYesNo(sub.timing));
  add("Time Context", sub.tense && sub.tense !== "unspecified" ? sub.tense : "—");
  add("Follow-up", dnaYesNo(sub.is_followup));
  if (sub.is_followup && sub.followup_of) add("Follow-up Of", sub.followup_of);
  add("Emotion", sub.emotion ? String(sub.emotion).replace(/_/g, " ") : "—");
  add("Risk", sub.risk ? String(sub.risk) : "—");
  add("Engine Archetype", dnaDisplayLabel(DNA_ENGINE_ARCHETYPE_LABEL, sub.engine_archetype));
  add(
    "Modules",
    Array.isArray(sub.required_modules) && sub.required_modules.length > 0
      ? sub.required_modules.join(", ")
      : "—",
  );
  add("Confidence", dnaConfPct(sub.confidence));
  add(
    "Bucket Match",
    sub.bucket_match_confidence
      ? `${String(sub.bucket_match_confidence).toUpperCase()}${
          typeof sub.bucket_match_score === "number"
            ? ` (${(sub.bucket_match_score * 100).toFixed(0)}%)`
            : ""
        }`
      : "—",
  );
  return lines.join("\n");
}

function formatAllDnaResultsForCopy(items: DnaCopyItem[]): string {
  if (!items.length) return "";
  const blocks = items.map((it, i) => {
    const subs = dnaSubsFromItem(it);
    const multi = subs.length > 1;
    const header = [
      `=== Q${it.index ?? i + 1}${
        typeof it.latency_ms === "number" ? ` · ${it.latency_ms}ms` : ""
      }${multi ? ` · split ×${subs.length}` : ""} ===`,
      `Question: ${it.question}`,
    ].join("\n");
    const body = subs
      .map((sub, si) =>
        formatDnaSubForCopy(sub, multi ? `--- Split ${si + 1} of ${subs.length} ---` : undefined),
      )
      .join("\n\n");
    return `${header}\n\n${body}`;
  });
  return blocks.join("\n\n" + "─".repeat(48) + "\n\n");
}

function DnaFieldRow({
  label,
  value,
  textColor,
  mutedColor,
}: {
  label: string;
  value: string;
  textColor: string;
  mutedColor: string;
}) {
  return (
    <View style={{ flexDirection: "row", marginTop: 5, gap: 8 }}>
      <Text style={{ color: mutedColor, fontSize: 12, width: 132, fontWeight: "600" }}>{label}</Text>
      <Text style={{ color: textColor, fontSize: 12, flex: 1, lineHeight: 18 }}>{value}</Text>
    </View>
  );
}

export default function AskScreen() {
  const insets = useSafeAreaInsets();
  const C = useC();
  const { kundli, birthData, user, primaryProfileId } = useUser();
  const t = useT();
  const androidSB = StatusBar.currentHeight ?? 24;
  const topPad = Platform.OS === "web" ? 67 : Platform.OS === "android" ? Math.max(insets.top, androidSB) : insets.top;
  const botPad = Platform.OS === "web" ? 34 : insets.bottom;
  const showDemo = !kundli;

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

  // Mode picker: null = landing, "chat" = Ask Anything, "batch" = Batch Test, "dna" = DNA Check
  const [mode, setMode] = useState<"chat" | "batch" | "dna" | null>(null);
  const [askReplyLang, setAskReplyLang] = useState<AskReplyLang>("hn");
  const [langPickerVisible, setLangPickerVisible] = useState(false);
  const [langPickerDraft, setLangPickerDraft] = useState<AskReplyLang>("hn");

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

  // ── Full-screen chat: hide the bottom tab bar (Home / Lifemap / Future …)
  // while in chat mode so "Ask Anything" opens edge-to-edge like a dedicated
  // chat app. Restored automatically on blur or when returning to the
  // landing picker (the in-header back chevron sets mode → null).
  const { setHidden } = useTabBar();
  useFocusEffect(
    useCallback(() => {
      setHidden(mode === "chat" || mode === "batch" || mode === "dna");
      return () => setHidden(false);
    }, [mode, setHidden]),
  );

  // ── Back handling: chat/batch → landing (not pop tab stack).
  useFocusEffect(
    useCallback(() => {
      const onBack = () => {
        if (mode === "chat" || mode === "batch" || mode === "dna") {
          setMode(null);
          return true;
        }
        return false;
      };
      const sub = BackHandler.addEventListener("hardwareBackPress", onBack);
      return () => sub.remove();
    }, [mode]),
  );

  const tabBarHidden = mode === "chat" || mode === "batch" || mode === "dna";
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

  // SAVE on every messages change. Gated on hydratedKeyRef MATCHING the
  // current key — prevents stale overwrite during user/profile switch.
  // Cap last 200 to prevent storage bloat. Runs async, non-blocking.
  useEffect(() => {
    if (showDemo) return;
    if (hydratedKeyRef.current !== chatStorageKey) return;
    const tail = messages.slice(-200);
    AsyncStorage.setItem(chatStorageKey, JSON.stringify(tail)).catch(() => {
      // Storage full / quota — non-fatal, thread keeps working in memory.
    });
  }, [messages, chatStorageKey, showDemo]);

  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [batchInput, setBatchInput] = useState("");
  const [batchRunning, setBatchRunning] = useState(false);
  const [batchProgress, setBatchProgress] = useState<string | null>(null);
  const [batchResult, setBatchResult] = useState<string | null>(null);
  const [batchItems, setBatchItems] = useState<Array<{
    index?: number;
    question: string;
    answer: string;
    topic?: string;
    source?: string;
    engine_tag?: string;
  }>>([]);
  const batchScrollRef = useRef<ScrollView>(null);

  type DnaItem = {
    index?: number;
    question: string;
    normalized_question?: string;
    domain?: string;
    bucket?: string;
    engine_archetype?: string | null;
    intent?: string;
    subject?: string;
    target?: string;
    question_type?: string;
    timing?: boolean;
    tense?: string;
    emotion?: string;
    risk?: string;
    is_followup?: boolean;
    followup_of?: string;
    confidence?: number;
    bucket_match_score?: number;
    bucket_match_confidence?: string;
    bucket_coerced?: boolean;
    required_modules?: string[];
    split_count?: number;
    source?: string;
    latency_ms?: number;
    dna?: { questions?: Array<Record<string, unknown>> };
  };
  const [dnaInput, setDnaInput] = useState("");
  const [dnaRunning, setDnaRunning] = useState(false);
  const [dnaProgress, setDnaProgress] = useState<string | null>(null);
  const [dnaItems, setDnaItems] = useState<DnaItem[]>([]);
  const [dnaCopiedAll, setDnaCopiedAll] = useState(false);
  const dnaScrollRef = useRef<ScrollView>(null);
  const dnaCopiedAllTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const dnaItemFromPayload = (question: string, dna: any, index = 1): DnaItem => {
    const primary = (dna?.questions || [])[0] || {};
    return {
      index,
      question,
      normalized_question: primary.normalized_question,
      domain: primary.domain,
      bucket: primary.bucket,
      engine_archetype: primary.engine_archetype,
      intent: primary.intent,
      subject: primary.subject,
      target: primary.target,
      question_type: primary.question_type,
      timing: primary.timing,
      tense: primary.tense,
      emotion: primary.emotion,
      risk: primary.risk,
      is_followup: primary.is_followup,
      followup_of: primary.followup_of,
      confidence: primary.confidence,
      bucket_match_score: primary.bucket_match_score,
      bucket_match_confidence: primary.bucket_match_confidence,
      bucket_coerced: primary.bucket_coerced,
      required_modules: primary.required_modules,
      split_count: Array.isArray(dna?.questions) ? dna.questions.length : 1,
      source: dna?.source,
      latency_ms: dna?.latency_ms,
      dna,
    };
  };

  const runDnaCheck = useCallback(async () => {
    if (showDemo) {
      router.push("/onboarding");
      return;
    }
    if (dnaRunning) return;
    const lines = (dnaInput || "")
      .split(/\n+/)
      .map((x) => x.trim())
      .filter(Boolean);
    if (!lines.length) return;

    const qs = lines.slice(0, 500);
    setDnaRunning(true);
    setDnaProgress(`0/${qs.length} — starting…`);
    setDnaItems([]);
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);

    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      Accept: "text/event-stream, application/json",
    };
    if (user?.api_key) headers["X-API-Key"] = user.api_key;

    const failDna = async (res: Response) => {
      const j = await res.json().catch(() => null);
      const msg = j?.message || j?.error || "";
      if (res.status === 405 || res.status === 404) {
        setDnaProgress(
          `DNA API not deployed on server (${res.status}). VPS par flask_app.py + ask_dna_runner.py upload karke pm2 restart karein.`,
        );
        return;
      }
      setDnaProgress(
        msg ? `Failed (${res.status}): ${msg}` : `Failed (HTTP ${res.status})`,
      );
    };

    const parseDnaEvent = (raw: string) => {
      const dataLine = raw.split("\n").find((l) => l.startsWith("data:"));
      if (!dataLine) return null;
      const dataStr = dataLine.slice(5).trim();
      if (!dataStr) return null;
      try {
        return JSON.parse(dataStr);
      } catch {
        return null;
      }
    };

    try {
      // Single question — simple JSON endpoint (no SSE)
      if (qs.length === 1) {
        const res = await fetch(`${API_BASE}/api/ask/dna`, {
          method: "POST",
          headers,
          body: JSON.stringify({ question: qs[0], user_id: user?.id }),
        });
        if (res.status === 401) {
          setDnaProgress("Session expired — logout karke phir login karein.");
          return;
        }
        if (!res.ok) {
          await failDna(res);
          return;
        }
        const json = await res.json();
        const item = dnaItemFromPayload(json?.question || qs[0], json?.dna, 1);
        setDnaItems([item]);
        setDnaProgress("1/1 complete");
        setTimeout(() => dnaScrollRef.current?.scrollToEnd({ animated: true }), 200);
        return;
      }

      const res = await fetch(`${API_BASE}/api/ask/dna/batch/stream`, {
        method: "POST",
        headers,
        body: JSON.stringify({ questions: qs, user_id: user?.id }),
      });

      if (res.status === 401) {
        setDnaProgress("Session expired — logout karke phir login karein.");
        return;
      }
      if (!res.ok) {
        await failDna(res);
        return;
      }

      const ct = (res.headers.get("content-type") || "").toLowerCase();
      const isStream = ct.includes("text/event-stream");
      const collected: DnaItem[] = [];

      const handleEvt = (evt: any) => {
        if (!evt || typeof evt !== "object") return;
        if (evt.error) {
          setDnaProgress(String(evt.error));
          return;
        }
        if (evt.kind === "started" && typeof evt.total === "number") {
          setDnaProgress(`0/${evt.total} — running…`);
          return;
        }
        if (evt.kind === "item") {
          const item: DnaItem = {
            index: evt.index,
            question: evt.question || "",
            domain: evt.domain,
            bucket: evt.bucket,
            engine_archetype: evt.engine_archetype ?? (evt.dna?.questions?.[0] as any)?.engine_archetype,
            intent: evt.intent,
            subject: evt.subject,
            target: evt.target,
            question_type: evt.question_type,
            timing: evt.timing,
            tense: evt.tense,
            emotion: evt.emotion,
            risk: evt.risk,
            is_followup: evt.is_followup,
            followup_of: evt.followup_of,
            normalized_question: evt.normalized_question,
            confidence: evt.confidence,
            required_modules: evt.required_modules,
            split_count: evt.split_count,
            source: evt.source,
            latency_ms: evt.latency_ms,
            dna: evt.dna,
          };
          collected.push(item);
          setDnaItems([...collected]);
          setDnaProgress(`${collected.length}/${evt.total ?? qs.length} done`);
          setTimeout(() => dnaScrollRef.current?.scrollToEnd({ animated: true }), 120);
        }
        if (evt.kind === "done") {
          setDnaProgress(`${collected.length}/${evt.total ?? collected.length} complete`);
        }
      };

      if (isStream && res.body) {
        const reader = res.body.getReader();
        const dec = new TextDecoder();
        let buf = "";
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          buf += dec.decode(value, { stream: true });
          const parts = buf.split("\n\n");
          buf = parts.pop() || "";
          for (const part of parts) {
            const evt = parseDnaEvent(part);
            if (evt) handleEvt(evt);
          }
        }
        if (buf.trim()) {
          const evt = parseDnaEvent(buf);
          if (evt) handleEvt(evt);
        }
      } else {
        const json = await res.json();
        if (json?.dna) {
          setDnaItems([dnaItemFromPayload(qs[0], json.dna, 1)]);
          setDnaProgress("1/1 complete");
        }
      }
      setTimeout(() => dnaScrollRef.current?.scrollToEnd({ animated: true }), 200);
    } catch (e: any) {
      setDnaProgress(e?.message || "Network error — try again.");
    } finally {
      setDnaRunning(false);
    }
  }, [dnaInput, dnaRunning, showDemo, user?.api_key, user?.id]);

  const copyAllDnaResults = useCallback(() => {
    if (!dnaItems.length) return;
    const value = formatAllDnaResultsForCopy(dnaItems);
    if (!value) return;
    void (async () => {
      try {
        await Clipboard.setStringAsync(value);
        try { Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success); } catch {}
      } catch {}
      setDnaCopiedAll(true);
      if (dnaCopiedAllTimerRef.current) clearTimeout(dnaCopiedAllTimerRef.current);
      dnaCopiedAllTimerRef.current = setTimeout(() => setDnaCopiedAll(false), 2000);
    })();
  }, [dnaItems]);

  const runBatchTest = useCallback(async () => {
    if (showDemo) {
      router.push("/onboarding");
      return;
    }
    if (batchRunning) return;
    const lines = (batchInput || "")
      .split(/\n+/)
      .map((x) => x.trim())
      .filter(Boolean);
    if (!lines.length) return;

    const qs = lines.slice(0, 60);
    setBatchRunning(true);
    setBatchProgress(`0/${qs.length} — starting…`);
    setBatchResult(null);
    setBatchItems([]);
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);

    const body = JSON.stringify({
      questions: qs,
      batch_title: "Batch Test",
      kundli,
      birthData,
      history: [],
      lang: askLangToApi(askReplyLang),
      user_id: user?.id,
    });
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      Accept: "text/event-stream, application/json",
    };
    if (user?.api_key) headers["X-API-Key"] = user.api_key;

    const parseBatchEvent = (raw: string) => {
      const dataLine = raw.split("\n").find((l) => l.startsWith("data:"));
      if (!dataLine) return null;
      const dataStr = dataLine.slice(5).trim();
      if (!dataStr) return null;
      try {
        return JSON.parse(dataStr);
      } catch {
        return null;
      }
    };

    try {
      const res = await fetch(`${API_BASE}/api/ask/batch/stream`, {
        method: "POST",
        headers,
        body,
      });

      if (res.status === 402) {
        const json = await res.json().catch(() => ({} as any));
        setBatchResult(json?.message || "Daily limit poora");
        setQuotaModal({
          used: json?.quota?.used ?? 0,
          limit: json?.quota?.limit ?? 0,
          plan: json?.plan ?? "free",
          message: json?.message ?? t.askDailyLimitOver,
        });
        return;
      }
      if (res.status === 401) {
        setBatchResult("Session expired — logout karke phir login karein.");
        return;
      }
      if (!res.ok) {
        const j = await res.json().catch(() => null);
        setBatchResult(
          j?.message
            ? `Batch failed: ${j.message}`
            : `Batch failed (status ${res.status}) — please try again.`,
        );
        return;
      }

      const ct = (res.headers.get("content-type") || "").toLowerCase();
      const isStream = ct.includes("text/event-stream");
      const collected: typeof batchItems = [];
      let sawDone = false;
      let streamError: string | null = null;

      const handleEvt = (evt: any) => {
        if (!evt || typeof evt !== "object") return;
        if (evt.error) {
          streamError = String(evt.error);
          return;
        }
        if (evt.kind === "started" && typeof evt.total === "number") {
          setBatchProgress(`0/${evt.total} — processing…`);
          return;
        }
        if (evt.kind === "item" && evt.item && typeof evt.item === "object") {
          collected.push(evt.item);
          setBatchItems([...collected]);
          const idx = evt.index ?? collected.length;
          const total = evt.total ?? qs.length;
          setBatchProgress(`${idx}/${total} done`);
          setTimeout(() => batchScrollRef.current?.scrollToEnd({ animated: true }), 120);
          return;
        }
        if (evt.kind === "done") {
          sawDone = true;
          const items = Array.isArray(evt.items) ? evt.items : collected;
          setBatchItems(items);
          setBatchResult(
            evt.text
            || items.map((it: any, i: number) => `### ${i + 1}. ${it.question}\n\n${it.answer || ""}`).join("\n\n---\n\n"),
          );
          setBatchProgress(null);
        }
      };

      if (isStream) {
        const reader: ReadableStreamDefaultReader<Uint8Array> | null =
          (res.body && typeof (res.body as any).getReader === "function")
            ? (res.body as any).getReader()
            : null;
        const decoder: TextDecoder | null =
          typeof TextDecoder !== "undefined" ? new TextDecoder() : null;

        if (reader && decoder) {
          let buffer = "";
          // eslint-disable-next-line no-constant-condition
          while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            buffer += decoder.decode(value, { stream: true });
            let nlnl: number;
            while ((nlnl = buffer.indexOf("\n\n")) >= 0) {
              const evtRaw = buffer.slice(0, nlnl);
              buffer = buffer.slice(nlnl + 2);
              handleEvt(parseBatchEvent(evtRaw));
            }
          }
          if (buffer.trim()) handleEvt(parseBatchEvent(buffer));
        } else {
          const textBody = await res.text();
          for (const part of textBody.split("\n\n")) {
            if (part.trim()) handleEvt(parseBatchEvent(part));
          }
        }
      } else {
        const j = await res.json().catch(() => ({} as any));
        handleEvt({ kind: "done", ...j });
      }

      if (!sawDone) {
        if (collected.length > 0) {
          setBatchItems(collected);
          setBatchResult(
            collected.map((it, i) => `### ${i + 1}. ${it.question}\n\n${it.answer || ""}`).join("\n\n---\n\n"),
          );
        } else {
          setBatchResult(streamError || "Batch failed — connection ended early. Please try again.");
        }
      } else {
        setTimeout(() => batchScrollRef.current?.scrollToEnd({ animated: true }), 200);
      }
    } catch (err: any) {
      const msg = String(err?.message || err || "").trim();
      setBatchResult(
        msg && /network|fetch|failed/i.test(msg)
          ? `Batch failed: ${msg} (12+ questions ke liye server deploy zaroori hai)`
          : msg
            ? `Batch failed: ${msg}`
            : "Batch failed — please try again.",
      );
    } finally {
      setBatchRunning(false);
      setBatchProgress(null);
    }
  }, [batchInput, batchRunning, showDemo, user?.api_key, user?.id, kundli, birthData, askReplyLang, t.askDailyLimitOver]);
  const [copiedUserMsgId, setCopiedUserMsgId] = useState<string | null>(null);
  const copiedUserMsgTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [copiedAssistantMsgId, setCopiedAssistantMsgId] = useState<string | null>(null);
  const copiedAssistantMsgTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const stripMarkdownForCopy = useCallback((text: string) => {
    return (text || "")
      .replace(/[*_`#>~]/g, "")
      .replace(/\[([^\]]+)\]\([^)]+\)/g, "$1")
      .replace(/\n{2,}/g, "\n\n")
      .trim();
  }, []);

  const copyAssistantAnswer = useCallback((msgId: string, text: string) => {
    const value = stripMarkdownForCopy(text);
    if (!value) return;
    void (async () => {
      try {
        await Clipboard.setStringAsync(value);
        try { Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success); } catch {}
      } catch {}
      setCopiedAssistantMsgId(msgId);
      if (copiedAssistantMsgTimerRef.current) clearTimeout(copiedAssistantMsgTimerRef.current);
      copiedAssistantMsgTimerRef.current = setTimeout(() => setCopiedAssistantMsgId(null), 1500);
    })();
  }, [stripMarkdownForCopy]);

  const copyUserQuestion = useCallback((msgId: string, text: string) => {
    const value = (text || "").trim();
    if (!value) return;
    void (async () => {
      try {
        await Clipboard.setStringAsync(value);
        try { Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success); } catch {}
      } catch {}
      setCopiedUserMsgId(msgId);
      if (copiedUserMsgTimerRef.current) clearTimeout(copiedUserMsgTimerRef.current);
      copiedUserMsgTimerRef.current = setTimeout(() => setCopiedUserMsgId(null), 1500);
    })();
  }, []);

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
  const listRef = useRef<FlatList>(null);

  const scrollToEnd = useCallback(() => {
    setTimeout(() => listRef.current?.scrollToEnd({ animated: true }), 100);
  }, []);

  useEffect(() => { scrollToEnd(); }, [messages]);

  const send = useCallback(
    async (text: string, opts?: { regenerate?: boolean; targetAssistantId?: string }) => {
      if (!text.trim() || loading) return;
      if (showDemo) {
        router.push("/onboarding");
        return;
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
        };
        if (user?.api_key) headers["X-API-Key"] = user.api_key;

        // Conversation memory: build from POST-strip snapshot (not state),
        // excluding the new user message which is sent separately as
        // `question`. Keep last 10 turns for context budget.
        const history = trimmed
          .filter((m) => !m.loading && m.id !== "thinking")
          .slice(-10)
          .map((m) => ({ role: m.role, text: m.text }));

        // Use raw fetch (not apiFetch) — apiFetch's network-retry can re-issue
        // the request mid-stream; SSE responses must not be retried.
        // INITIAL-CONNECT RETRY (May 6 2026): the first TLS handshake to
        // a fresh cloudflare tunnel host occasionally hiccups (HTTP/2 RST
        // or DNS warm-up), causing fetch() to throw before any response
        // is received. Retrying ONLY the initial fetch (before we touch
        // res.body) is safe because no stream bytes have been consumed
        // yet — this is identical to apiFetch's policy. Mid-stream errors
        // still fail to the user as before.
        const _reqInit: RequestInit = {
          method: "POST",
          headers,
          body: JSON.stringify({
            question: text.trim(),
            kundli,
            birthData,
            history,
            lang: askLangToApi(askReplyLang),
            user_id: user?.id,
          }),
          signal: ctrl.signal,
        };
        let res: Response;
        try {
          res = await fetch(`${API_BASE}/api/ask/stream`, _reqInit);
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
          res = await fetch(`${API_BASE}/api/ask/stream`, _reqInit);
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
          setQuotaModal({
            used:    json?.quota?.used  ?? 0,
            limit:   json?.quota?.limit ?? 0,
            plan:    json?.plan         ?? "free",
            message: json?.message      ?? t.askDailyLimitOver,
          });
          try { Haptics.notificationAsync(Haptics.NotificationFeedbackType.Warning); } catch {}
          return;
        }

        // ── Auth error (401) — restore on regenerate, error bubble on fresh
        if (res.status === 401) {
          failQuietly("Session expired — kripya logout karke phir login karein.");
          return;
        }

        // ── Other non-2xx (5xx etc) — same restore matrix as auth.
        if (!res.ok) {
          failQuietly("Kshama karein, abhi jawab dene mein dikkat aa rahi hai.");
          return;
        }

        // ── One-shot JSON path (brand_guard / no_chart / marriage) ───────
        if (!isStream) {
          const json = await res.json().catch(() => null);
          if (!isCurrent()) return;
          if (!json || typeof json !== "object") {
            failQuietly("Kshama karein, abhi jawab dene mein dikkat aa rahi hai.");
            return;
          }
          const answer =
            json.text ?? json.answer ?? json.response ??
            "Kshama karein, abhi jawab dene mein dikkat aa rahi hai.";
          const followUps: string[] = Array.isArray(json.follow_ups) ? json.follow_ups.slice(0, 3) : [];

          // P6 — v2 multi-intent cards detection. When present, attach to
          // the message so renderMsg switches to CardsCarousel. Legacy
          // `text` is still kept for voice / copy / regenerate.
          const isV2     = json.response_schema === "v2"
                         && Array.isArray(json.cards)
                         && json.cards.length > 0;
          const cards: CardData[] | undefined = isV2 ? json.cards : undefined;
          const trimmed = isV2 && typeof json.trimmed_count === "number"
            ? json.trimmed_count
            : undefined;

          // Phase 7.5 — clarifier UX. Server attaches a `clarification`
          // object only when its classifier confidence was low. Defensive
          // shape check + parity with the SSE parser: `clar` is left
          // undefined unless the FILTERED options list (strings only,
          // trimmed, non-empty) is itself non-empty. This avoids
          // storing `{prompt, options: []}` shells in chat history.
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

          // Phase 2.5.11.6 — partner CTA. Server returns this when the Q
          // refers to a specific partner ("mere bf se shaadi hogi") but
          // no partner profile is saved yet. We render an inline button
          // below the bubble that opens profile-edit pre-set to the
          // detected relation slot.
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
          setMessages(prev =>
            prev.filter(m => m.id !== "thinking").concat({
              id: newAssistantId,
              role: "assistant",
              text: answer,
              followUps,
              cards,
              trimmedCount: trimmed,
              responseSchema: isV2 ? "v2" : undefined,
              clarification: clar,
              partnerCta,
            })
          );
          void fetchHistory();
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

        // Feature detection — RN bridged fetch on some Expo Go builds buffers
        // the entire body and exposes only .text(). Fall back to one-shot SSE
        // parse so the user still gets the answer (just no token-by-token).
        const reader: ReadableStreamDefaultReader<Uint8Array> | null =
          (res.body && typeof (res.body as any).getReader === "function")
            ? (res.body as any).getReader()
            : null;

        const decoder: TextDecoder | null =
          typeof TextDecoder !== "undefined" ? new TextDecoder() : null;

        let accumulated     = "";
        let finalText       = "";
        let finalFollowUps: string[] = [];
        // Phase 7.5 — clarifier UX (stream path). Server attaches the
        // `clarification` field on the `done` event when its classifier
        // confidence was low. Defensive parsing in the evt.done branch.
        let finalClarification: { prompt: string; options: string[] } | undefined;
        let sawDone         = false;
        let midError: string | null = null;

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
            if (!isCurrent()) return;       // drop stale paint
            setMessages(prev => {
              const idx = prev.findIndex(m => m.id === newAssistantId);
              if (idx < 0) return prev;
              const next = [...prev];
              next[idx] = { ...next[idx], text: accumulated };
              return next;
            });
          }
          if (evt.done) {
            sawDone = true;
            finalText = String(evt.text || accumulated || "");
            finalFollowUps = Array.isArray(evt.follow_ups) ? evt.follow_ups.slice(0, 3) : [];
            // Phase 7.5 — clarifier (defensive shape check; absent → undefined)
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

        if (reader && decoder) {
          let buffer = "";
          // eslint-disable-next-line no-constant-condition
          while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            buffer += decoder.decode(value, { stream: true });
            let nlnl: number;
            while ((nlnl = buffer.indexOf("\n\n")) >= 0) {
              const evtRaw = buffer.slice(0, nlnl);
              buffer = buffer.slice(nlnl + 2);
              handleEvent(evtRaw);
            }
          }
          if (buffer.trim()) handleEvent(buffer);
        } else {
          // No streaming reader → fetch full body and parse all events.
          const body = await res.text();
          if (!isCurrent()) return;
          for (const part of body.split("\n\n")) {
            if (part.trim()) handleEvent(part);
          }
        }

        // Strict finalisation: a stream that never sent `done` is treated as
        // a failure regardless of partial text — partial deltas have NOT been
        // tone-scrubbed and may contain banned words. Trust only the server's
        // `done.text` (post-scrub) for what we publish.
        if (!sawDone) {
          // Abort the bubble we created and route through the standard
          // restore matrix (regen → restore original; fresh → error bubble).
          if (isCurrent()) {
            setMessages(prev => prev.filter(m => m.id !== newAssistantId));
          }
          failQuietly(midError || "Kshama karein, abhi jawab dene mein dikkat aa rahi hai.");
          return;
        }

        // Stale check before final commit.
        if (!isCurrent()) return;

        // Swap in scrubbed final text + follow_ups; clear streaming flag.
        setMessages(prev => {
          const idx = prev.findIndex(m => m.id === newAssistantId);
          if (idx < 0) return prev;
          const next = [...prev];
          next[idx] = {
            ...next[idx],
            // Phase 7.5 — clarifier (undefined when server omits / disabled)
            clarification: finalClarification,
            text:      finalText || accumulated,
            followUps: finalFollowUps,
            streaming: false,
          };
          return next;
        });
        void fetchHistory();
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
        failQuietly("Network error — thodi der baad try karein.");
      } finally {
        // Only the latest in-flight request clears the loading flag; older
        // (aborted) ones must not flip it off while a newer call is pending.
        if (isCurrent()) setLoading(false);
      }
    },
    [loading, showDemo, kundli, birthData, user?.id, user?.api_key, askReplyLang, messages, t.askDailyLimitOver, fetchHistory],
  );

  // Latest assistant message id — only this one shows follow-up chips.
  const latestAssistantId = useMemo(() => {
    for (let i = messages.length - 1; i >= 0; i--) {
      const m = messages[i];
      if (m.role === "assistant" && !m.loading) return m.id;
    }
    return null;
  }, [messages]);

  // ── Voice INPUT (mic → /api/stt) ─────────────────────────────────────────
  const recorder = useAudioRecorder(RecordingPresets.HIGH_QUALITY);
  const [isRecording, setIsRecording] = useState(false);
  const [isTranscribing, setIsTranscribing] = useState(false);
  // When user used mic, we auto-play the next assistant reply in voice.
  const [autoSpeakNext, setAutoSpeakNext] = useState(false);
  const lastSpokenIdRef = useRef<string | null>(null);

  const startRecording = useCallback(async () => {
    try {
      if (showDemo) { router.push("/onboarding"); return; }
      const perm = await requestRecordingPermissionsAsync();
      if (!perm.granted) { return; }
      await setAudioModeAsync({ allowsRecording: true, playsInSilentMode: true });
      try { Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium); } catch {}
      await recorder.prepareToRecordAsync();
      recorder.record();
      setIsRecording(true);
    } catch {
      setIsRecording(false);
    }
  }, [recorder, showDemo]);

  const stopRecordingAndTranscribe = useCallback(async () => {
    try {
      try { Haptics.selectionAsync(); } catch {}
      await recorder.stop();
      setIsRecording(false);
      const uri = recorder.uri;
      if (!uri) return;

      setIsTranscribing(true);
      const form = new FormData();
      // RN FormData with local file URI
      form.append("audio", {
        uri,
        name: "speech.m4a",
        type: "audio/m4a",
      } as any);

      const res = await fetch(`${API_BASE}/api/stt`, {
        method: "POST",
        body: form,
      });
      setIsTranscribing(false);
      if (!res.ok) return;
      const json = await res.json().catch(() => null);
      const text = (json?.text || "").trim();
      if (!text) return;

      // Mark next assistant reply for auto-voice playback
      setAutoSpeakNext(true);
      send(text);
    } catch {
      setIsRecording(false);
      setIsTranscribing(false);
    }
  }, [recorder, send]);

  // ── Voice playback (TTS via /api/tts) ────────────────────────────────────
  // One shared player. We swap its source per-message via .replace().
  // NOTE: pass NO args (not `undefined`) — expo-audio 55's native bridge
  // mis-counts args when `undefined` is forwarded explicitly, causing
  // "Received 4 arguments, but 3 was expected" render error on iOS.
  const ttsPlayer = useAudioPlayer();
  const ttsStatus = useAudioPlayerStatus(ttsPlayer);
  const [voiceMsgId, setVoiceMsgId] = useState<string | null>(null);
  // States: idle | loading | playing
  const [voiceState, setVoiceState] = useState<"idle" | "loading" | "playing">("idle");

  // Configure audio mode once (play even in silent mode on iOS)
  useEffect(() => {
    setAudioModeAsync({ playsInSilentMode: true, shouldPlayInBackground: false }).catch(() => {});
  }, []);

  // Auto-stop tracking when audio ends
  useEffect(() => {
    if (voiceState === "playing" && ttsStatus && ttsStatus.didJustFinish) {
      setVoiceState("idle");
      setVoiceMsgId(null);
    }
  }, [ttsStatus?.didJustFinish, voiceState]);

  const handleVoicePlay = useCallback(async (msg: Message) => {
    try {
      // Tap same playing message → stop
      if (voiceMsgId === msg.id && voiceState === "playing") {
        try { ttsPlayer.pause(); } catch {}
        setVoiceState("idle"); setVoiceMsgId(null);
        return;
      }
      // Strip markdown for cleaner speech
      const cleanText = (msg.text || "")
        .replace(/[*_`#>~]/g, "")
        .replace(/\[([^\]]+)\]\([^)]+\)/g, "$1")
        .replace(/\n{2,}/g, ". ")
        .trim();
      if (!cleanText) return;

      try { Haptics.selectionAsync(); } catch {}
      setVoiceMsgId(msg.id);
      setVoiceState("loading");

      // POST text → server returns mp3 bytes. Convert to data URI for player.
      const res = await fetch(`${API_BASE}/api/tts`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: cleanText, voice: "nova" }),
      });
      if (!res.ok) {
        setVoiceState("idle"); setVoiceMsgId(null);
        return;
      }
      const blob = await res.blob();
      // RN fetch returns Blob; convert to base64 data URI for the player
      const reader = new FileReader();
      const dataUri: string = await new Promise((resolve, reject) => {
        reader.onloadend = () => resolve(reader.result as string);
        reader.onerror = reject;
        reader.readAsDataURL(blob);
      });

      try { ttsPlayer.replace({ uri: dataUri }); } catch {}
      try { ttsPlayer.seekTo(0); } catch {}
      try { ttsPlayer.play(); } catch {}
      setVoiceState("playing");
    } catch {
      setVoiceState("idle"); setVoiceMsgId(null);
    }
  }, [voiceMsgId, voiceState, ttsPlayer]);

  // Auto-play voice for the next completed assistant reply when the user
  // asked via mic. Trigger only once per reply (lastSpokenIdRef guard) and
  // only after streaming finishes (text non-empty + not loading + not "thinking").
  useEffect(() => {
    if (!autoSpeakNext || loading) return;
    const last = messages[messages.length - 1];
    if (!last || last.role !== "assistant" || last.id === "thinking" || last.loading) return;
    if (!last.text?.trim()) return;
    if (lastSpokenIdRef.current === last.id) return;
    lastSpokenIdRef.current = last.id;
    setAutoSpeakNext(false);
    handleVoicePlay(last);
  }, [autoSpeakNext, loading, messages, handleVoicePlay]);

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
                <AcharyaTypingDots caption="Cosmic Intelligence calculating…" />
              ) : item.cards && item.cards.length > 0 ? (
                <CardsCarousel
                  cards={item.cards}
                  trimmedCount={item.trimmedCount ?? 0}
                />
              ) : (
                <MarkdownReply text={item.text} />
              )}
            </LinearGradient>
          )}
        </View>

        {!isUser
          && !item.loading
          && !item.streaming
          && item.id !== "thinking"
          && !!item.text?.trim() && (
          <View style={s.assistantMsgActionsWrap}>
          <View style={s.assistantMsgActions}>
            <Pressable
              onPress={() => copyAssistantAnswer(item.id, item.text)}
              style={({ pressed }) => [
                s.userMsgActionBtn,
                { borderColor: `${C.accent}40`, backgroundColor: C.bgCard },
                pressed && { opacity: 0.7 },
              ]}
              accessibilityRole="button"
              accessibilityLabel="Copy answer"
            >
              <Feather name="copy" size={12} color={C.accent} />
              <Text style={[s.userMsgActionText, { color: C.accent }]}>
                {copiedAssistantMsgId === item.id ? "Copied" : "Copy answer"}
              </Text>
            </Pressable>
          </View>
          </View>
        )}

        {isUser && !item.loading && !!item.text?.trim() && (
          <View style={s.userMsgActions}>
            <Pressable
              onPress={() => copyUserQuestion(item.id, item.text)}
              style={({ pressed }) => [
                s.userMsgActionBtn,
                { borderColor: `${C.accent}40`, backgroundColor: C.bgCard },
                pressed && { opacity: 0.7 },
              ]}
              accessibilityRole="button"
              accessibilityLabel="Copy question"
            >
              <Feather name="copy" size={12} color={C.accent} />
              <Text style={[s.userMsgActionText, { color: C.accent }]}>
                {copiedUserMsgId === item.id ? "Copied" : "Copy question"}
              </Text>
            </Pressable>
            <Pressable
              onPress={() => {
                try { Haptics.selectionAsync(); } catch {}
                setInput(item.text.trim());
              }}
              style={({ pressed }) => [
                s.userMsgActionBtn,
                { borderColor: C.border, backgroundColor: C.bgCard },
                pressed && { opacity: 0.7 },
              ]}
              accessibilityRole="button"
              accessibilityLabel="Use question again"
            >
              <Feather name="edit-3" size={12} color={C.textMid} />
              <Text style={[s.userMsgActionText, { color: C.textMid }]}>Ask again</Text>
            </Pressable>
          </View>
        )}

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
        <View style={[s.header, { paddingTop: topPad + 12, borderBottomColor: C.border }]}>
        {mode === "chat" || mode === "batch" || mode === "dna" ? (
          <Pressable
            onPress={() => { Haptics.selectionAsync(); setMode(null); }}
            hitSlop={12}
            style={s.backBtn}
          >
            <Feather name="chevron-left" size={20} color={C.text} />
          </Pressable>
        ) : null}
        <View style={s.headerTitleRow}>
          <View
            pointerEvents="none"
            style={[s.headerTitleGlow, { backgroundColor: `${C.accent}26`, shadowColor: C.accent }]}
          />
          <Feather name="cpu" size={15} color={C.accent} style={{ marginRight: 6 }} />
          <Text style={[s.headerTitle, { color: C.text, textShadowColor: `${C.accent}88` }]}>
            {mode === "batch" ? "Batch Test" : mode === "dna" ? "DNA Check" : "Cosmic Intelligence"}
          </Text>
          <View style={{ marginLeft: 8 }}>
            <GlowDot color="#10b981" size={7} />
          </View>
        </View>
        <Text style={[s.headerSub, { color: C.textMuted }]}>
          {mode === "batch"
            ? "Paste 20–60 questions — answers run one by one"
            : mode === "dna"
              ? "Paste questions — DNA metadata only (no answer)"
              : "Multi System Pattern Engine V2.0"}
        </Text>
        {mode === "chat" && (
          <View style={s.askLangRow}>
            <Feather name="globe" size={12} color={C.textMuted} />
            <Text style={[s.askLangLabel, { color: C.textMuted }]}>Reply:</Text>
            {ASK_REPLY_LANG_OPTIONS.map((opt) => {
              const active = askReplyLang === opt.id;
              return (
                <Pressable
                  key={opt.id}
                  onPress={() => {
                    Haptics.selectionAsync();
                    void persistAskReplyLang(opt.id, true);
                  }}
                  style={[
                    s.askLangChip,
                    {
                      backgroundColor: active ? `${C.accent}22` : C.bgCard2,
                      borderColor: active ? C.accent : C.border,
                    },
                  ]}
                >
                  <Text
                    style={[
                      s.askLangChipText,
                      { color: active ? C.accent : C.textMid },
                    ]}
                  >
                    {opt.label}
                  </Text>
                </Pressable>
              );
            })}
          </View>
        )}
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
        <ScrollView
          style={{ flex: 1 }}
          contentContainerStyle={s.pickerWrap}
          showsVerticalScrollIndicator={false}
        >
          <FadeInView delay={staggerDelay(0, 55, 40)}>
            <View>
          <View style={s.heroBadgeRow}>
            <View style={[s.heroBadge, { backgroundColor: `${C.accent}18`, borderColor: `${C.accent}55` }]}>
              <Feather name="cpu" size={11} color={C.accent} />
              <Text style={[s.heroBadgeText, { color: C.accent }]}>Cosmic Advance Intelligence</Text>
            </View>
          </View>
          <Text style={[s.pickerHi, { color: C.text }]}>How can I help today?</Text>
          <Text style={[s.pickerSub, { color: C.textMid }]}>
            Sharp, evidence-based answers from your unique birth chart — career, marriage, health, money, timing.
          </Text>
            </View>
          </FadeInView>

          {/* Card 1: DNA Check — Step 1 classifier lab (above Ask Anything) */}
          <FadeInView delay={staggerDelay(1, 70, 80)}>
            <PressScale
              accessibilityLabel="DNA Check"
              onPress={() => {
                Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
                if (showDemo) { router.push("/onboarding"); return; }
                setDnaItems([]);
                setDnaProgress(null);
                setMode("dna");
              }}
              style={[s.modeCard, { shadowColor: "#0d9488" }]}
            >
              <LinearGradient
                colors={["#0f766e", "#0d9488", "#14b8a6"]}
                start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }}
                style={s.modeGrad}
              >
                <CardShimmer />
                <View style={s.modeIconWrap}>
                  <Text style={s.modeEmoji}>🧬</Text>
                </View>
                <View style={{ flex: 1 }}>
                  <View style={{ flexDirection: "row", alignItems: "center", gap: 6 }}>
                    <Text style={s.modeTitle}>DNA Check</Text>
                    <View style={s.modeBadge}>
                      <Text style={s.modeBadgeText}>Step 1</Text>
                    </View>
                  </View>
                  <Text style={s.modeBody}>
                    Questions paste karo — domain, bucket, intent, timing DNA dikhega. Answer nahi — sirf classification test (500 tak).
                  </Text>
                  <View style={s.modeMeta}>
                    <Feather name="git-branch" size={11} color="#ffffffcc" />
                    <Text style={s.modeMetaText}>Routing audit · No quota · Classify only</Text>
                  </View>
                </View>
                <Feather name="chevron-right" size={20} color="#fff" />
              </LinearGradient>
            </PressScale>
          </FadeInView>

          {/* Card 2: Ask Anything (Chat) */}
          <FadeInView delay={staggerDelay(2, 70, 80)}>
            <PressScale
            accessibilityLabel="Ask Anything"
            onPress={() => {
              Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
              if (showDemo) { router.push("/onboarding"); return; }
              setLangPickerDraft(askReplyLang);
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
                <Text style={s.modeEmoji}>💬</Text>
              </View>
              <View style={{ flex: 1 }}>
                <Text style={s.modeTitle}>Ask Anything</Text>
                <Text style={s.modeBody}>
                  Direct chat with Cosmic Intelligence — chart, dasha, marriage, career, health, money. Plain-language answers.
                </Text>
                <View style={s.modeMeta}>
                  <Feather name="zap" size={11} color="#ffffffcc" />
                  <Text style={s.modeMetaText}>Personalized · Evidence-based · BPHS</Text>
                </View>
              </View>
              <Feather name="chevron-right" size={20} color="#fff" />
            </LinearGradient>
            </PressScale>
          </FadeInView>

          {/* Card 3: Prashna Kundli (KP 1-249) */}
          <FadeInView delay={staggerDelay(3, 70, 80)}>
            <PressScale
            accessibilityLabel="Prashna Kundli"
            onPress={() => {
              Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
              if (showDemo) { router.push("/onboarding"); return; }
              router.push("/prashna-kundli");
            }}
            style={[s.modeCard, { shadowColor: "#0891b2" }]}
          >
            <LinearGradient
              colors={["#0e7490", "#0891b2", "#14b8a6"]}
              start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }}
              style={s.modeGrad}
            >
              <CardShimmer />
              <View style={s.modeIconWrap}>
                <Text style={s.modeEmoji}>🔢</Text>
              </View>
              <View style={{ flex: 1 }}>
                <View style={{ flexDirection: "row", alignItems: "center", gap: 6 }}>
                  <Text style={s.modeTitle}>Prashna Kundli</Text>
                  <View style={s.modeBadge}>
                    <Text style={s.modeBadgeText}>KP 1-249</Text>
                  </View>
                </View>
                <Text style={s.modeBody}>
                  Mann mein ek number 1-249 socho — wahi sankhya aapki kundli ka lagna banegi, cusp sub-lord se sahi jawab.
                </Text>
                <View style={s.modeMeta}>
                  <Feather name="hash" size={11} color="#ffffffcc" />
                  <Text style={s.modeMetaText}>K. S. Krishnamurti · Cuspal Interlinks</Text>
                </View>
              </View>
              <Feather name="chevron-right" size={20} color="#fff" />
            </LinearGradient>
            </PressScale>
          </FadeInView>

          {/* Card 4: Batch Test — opens dedicated screen (like Ask Anything) */}
          <FadeInView delay={staggerDelay(4, 70, 80)}>
            <PressScale
              accessibilityLabel="Batch Test"
              onPress={() => {
                Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
                if (showDemo) { router.push("/onboarding"); return; }
                setBatchResult(null);
                setBatchItems([]);
                setMode("batch");
              }}
              style={[s.modeCard, { shadowColor: "#7c3aed" }]}
            >
              <LinearGradient
                colors={["#5b21b6", "#7c3aed", "#a855f7"]}
                start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }}
                style={s.modeGrad}
              >
                <CardShimmer />
                <View style={s.modeIconWrap}>
                  <Text style={s.modeEmoji}>📋</Text>
                </View>
                <View style={{ flex: 1 }}>
                  <View style={{ flexDirection: "row", alignItems: "center", gap: 6 }}>
                    <Text style={s.modeTitle}>Batch Test</Text>
                    <View style={s.modeBadge}>
                      <Text style={s.modeBadgeText}>20–60 Q</Text>
                    </View>
                  </View>
                  <Text style={s.modeBody}>
                    Ek saath bahut sare questions paste karo — har ek ka jawab one-by-one aayega. Admin me sab ek parent entry ke andar dikhega.
                  </Text>
                  <View style={s.modeMeta}>
                    <Feather name="layers" size={11} color="#ffffffcc" />
                    <Text style={s.modeMetaText}>Testing · Routing audit · Admin nested log</Text>
                  </View>
                </View>
                <Feather name="chevron-right" size={20} color="#fff" />
              </LinearGradient>
            </PressScale>
          </FadeInView>

          {/* Recent Questions MOVED into the chat view (fresh-thread only).
              Landing picker now stays focused on the mode cards. */}

          {/* Optional: small Divya Prashna link (legacy, less prominent) */}
          <FadeInView delay={staggerDelay(5, 70, 120)}>
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
      )}

      {/* ───── DNA Check Mode (Step 1 classifier lab) ───────────────────── */}
      {mode === "dna" && (
        <ScrollView
          ref={dnaScrollRef}
          style={{ flex: 1 }}
          contentContainerStyle={{ padding: 16, paddingBottom: botPad + 24 }}
          keyboardShouldPersistTaps="handled"
          showsVerticalScrollIndicator={false}
        >
          <Text style={{ color: C.textMid, fontSize: 13, marginBottom: 10, lineHeight: 20 }}>
            Har line ek question. Run dabao — har ek ka DNA (domain, bucket, intent, timing…) niche aayega. Koi answer nahi, quota bhi nahi lagta.
          </Text>
          <TextInput
            style={{
              minHeight: 160,
              maxHeight: 320,
              paddingHorizontal: 14,
              paddingVertical: 12,
              backgroundColor: C.isDark ? "#1C1C22" : C.bgCard2,
              borderColor: C.isDark ? "rgba(255,255,255,0.10)" : C.border,
              borderWidth: 1,
              borderRadius: 16,
              color: C.text,
              fontSize: 15,
              lineHeight: 22,
              textAlignVertical: "top",
            }}
            value={dnaInput}
            onChangeText={setDnaInput}
            placeholder={"Government job kab milegi?\nMeri shaadi kab hogi?\nKya mera partner loyal hai?"}
            placeholderTextColor={C.textMuted}
            multiline
            editable={!showDemo && !dnaRunning}
          />
          <View style={{ flexDirection: "row", gap: 10, marginTop: 12, marginBottom: 20 }}>
            <Pressable
              onPress={() => void runDnaCheck()}
              disabled={dnaRunning || !dnaInput.trim()}
              style={({ pressed }) => [{ flex: 2, opacity: pressed ? 0.9 : 1 }]}
            >
              <LinearGradient
                colors={["#0f766e", "#0d9488", "#14b8a6"]}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 1 }}
                style={{
                  borderRadius: 14,
                  paddingVertical: 14,
                  flexDirection: "row",
                  alignItems: "center",
                  justifyContent: "center",
                  gap: 8,
                }}
              >
                {dnaRunning ? (
                  <AcharyaTypingDots caption={dnaProgress || "Extracting DNA…"} />
                ) : (
                  <>
                    <Feather name="play" size={16} color="#fff" />
                    <Text style={{ color: "#fff", fontWeight: "700", fontSize: 15 }}>Run DNA Check</Text>
                  </>
                )}
              </LinearGradient>
            </Pressable>
            <Pressable
              onPress={() => { setDnaInput(""); setDnaItems([]); setDnaProgress(null); }}
              disabled={dnaRunning}
              style={({ pressed }) => [
                {
                  flex: 1,
                  borderRadius: 14,
                  paddingVertical: 14,
                  alignItems: "center",
                  justifyContent: "center",
                  backgroundColor: C.bgCard,
                  borderWidth: 1,
                  borderColor: C.border,
                  opacity: pressed ? 0.85 : 1,
                },
              ]}
            >
              <Text style={{ color: C.textMid, fontWeight: "700" }}>Clear</Text>
            </Pressable>
          </View>

          {dnaProgress && !dnaRunning && dnaItems.length === 0 ? (
            <Text style={{ color: C.warningText, fontSize: 13, marginBottom: 12 }}>{dnaProgress}</Text>
          ) : null}

          {dnaItems.length > 0 ? (
            <View style={{ gap: 12 }}>
              <View style={{ flexDirection: "row", alignItems: "center", justifyContent: "space-between", gap: 10 }}>
                <Text style={{ color: C.textMuted, fontSize: 12, fontWeight: "700", flex: 1 }}>
                  DNA RESULTS ({dnaItems.length})
                  {dnaProgress ? ` · ${dnaProgress}` : ""}
                </Text>
                <Pressable
                  onPress={copyAllDnaResults}
                  disabled={dnaRunning}
                  style={({ pressed }) => ({
                    flexDirection: "row",
                    alignItems: "center",
                    gap: 6,
                    paddingHorizontal: 12,
                    paddingVertical: 8,
                    borderRadius: 10,
                    backgroundColor: dnaCopiedAll ? "#10b98122" : `${C.accent}18`,
                    borderWidth: 1,
                    borderColor: dnaCopiedAll ? "#10b98155" : `${C.accent}44`,
                    opacity: pressed ? 0.85 : 1,
                  })}
                >
                  <Feather name={dnaCopiedAll ? "check" : "copy"} size={14} color={dnaCopiedAll ? "#10b981" : C.accent} />
                  <Text style={{ color: dnaCopiedAll ? "#10b981" : C.accent, fontSize: 12, fontWeight: "700" }}>
                    {dnaCopiedAll ? "Copied!" : "Copy All"}
                  </Text>
                </Pressable>
              </View>
              {dnaItems.map((it, i) => {
                const subs = it.dna?.questions;
                const multi = Array.isArray(subs) && subs.length > 1;
                return (
                  <View
                    key={`dna_${it.index ?? i}_${it.question.slice(0, 20)}`}
                    style={{
                      padding: 14,
                      borderRadius: 16,
                      backgroundColor: C.bgCard,
                      borderWidth: 1,
                      borderColor: `${C.accent}33`,
                    }}
                  >
                    <Text style={{ color: "#0d9488", fontSize: 12, fontWeight: "700", marginBottom: 6 }}>
                      Q{it.index ?? i + 1}
                      {multi ? ` · split ×${subs!.length}` : ""}
                      {typeof it.latency_ms === "number" ? ` · ${it.latency_ms}ms` : ""}
                    </Text>
                    <Text style={{ color: C.text, fontWeight: "600", marginBottom: 10 }}>{it.question}</Text>
                    {(multi ? subs! : [{
                      normalized_question: it.normalized_question || it.question,
                      domain: it.domain,
                      bucket: it.bucket,
                      engine_archetype: it.engine_archetype,
                      intent: it.intent,
                      subject: it.subject,
                      target: it.target,
                      question_type: it.question_type,
                      timing: it.timing,
                      tense: it.tense,
                      emotion: it.emotion,
                      risk: it.risk,
                      is_followup: it.is_followup,
                      followup_of: it.followup_of,
                      confidence: it.confidence,
                      bucket_match_score: it.bucket_match_score,
                      bucket_match_confidence: it.bucket_match_confidence,
                      bucket_coerced: it.bucket_coerced,
                      required_modules: it.required_modules,
                    }]).map((sub: any, si: number) => (
                      <View
                        key={`sub_${si}`}
                        style={{
                          marginTop: si > 0 ? 10 : 0,
                          paddingTop: si > 0 ? 10 : 0,
                          borderTopWidth: si > 0 ? 1 : 0,
                          borderTopColor: C.border,
                        }}
                      >
                        {multi ? (
                          <Text style={{ color: C.textMuted, fontSize: 11, marginBottom: 6, fontWeight: "700" }}>
                            Split {si + 1} of {subs!.length}
                          </Text>
                        ) : null}
                        <DnaFieldRow
                          label="Normalized"
                          value={sub.normalized_question || "—"}
                          textColor={C.text}
                          mutedColor={C.textMuted}
                        />
                        <DnaFieldRow
                          label="Domain"
                          value={`${dnaDisplayLabel(DNA_DOMAIN_LABEL, sub.domain)} (${sub.domain || "—"})`}
                          textColor={C.text}
                          mutedColor={C.textMuted}
                        />
                        <DnaFieldRow
                          label="Bucket"
                          value={`${dnaDisplayLabel(DNA_BUCKET_LABEL, sub.bucket)} (${sub.bucket || "—"})`}
                          textColor={C.text}
                          mutedColor={C.textMuted}
                        />
                        <DnaFieldRow label="Intent" value={sub.intent || "—"} textColor={C.text} mutedColor={C.textMuted} />
                        <DnaFieldRow
                          label="Subject"
                          value={`${dnaDisplayLabel(DNA_SUBJECT_LABEL, sub.subject)} (${sub.subject || "—"})`}
                          textColor={C.text}
                          mutedColor={C.textMuted}
                        />
                        <DnaFieldRow
                          label="Target"
                          value={`${dnaDisplayLabel(DNA_TARGET_LABEL, sub.target)} (${sub.target || "—"})`}
                          textColor={C.text}
                          mutedColor={C.textMuted}
                        />
                        <DnaFieldRow
                          label="Question Type"
                          value={sub.question_type ? sub.question_type.replace(/_/g, " ") : "—"}
                          textColor={C.text}
                          mutedColor={C.textMuted}
                        />
                        <DnaFieldRow label="Timing Required" value={dnaYesNo(sub.timing)} textColor={C.text} mutedColor={C.textMuted} />
                        <DnaFieldRow
                          label="Time Context"
                          value={sub.tense && sub.tense !== "unspecified" ? sub.tense : "—"}
                          textColor={C.text}
                          mutedColor={C.textMuted}
                        />
                        <DnaFieldRow label="Follow-up" value={dnaYesNo(sub.is_followup)} textColor={C.text} mutedColor={C.textMuted} />
                        {sub.is_followup && sub.followup_of ? (
                          <DnaFieldRow label="Follow-up Of" value={sub.followup_of} textColor={C.text} mutedColor={C.textMuted} />
                        ) : null}
                        {multi ? (
                          <DnaFieldRow label="Multiple Questions" value="Yes" textColor={C.text} mutedColor={C.textMuted} />
                        ) : si === 0 ? (
                          <DnaFieldRow label="Multiple Questions" value="No" textColor={C.text} mutedColor={C.textMuted} />
                        ) : null}
                        <DnaFieldRow
                          label="Emotion"
                          value={sub.emotion ? String(sub.emotion).replace(/_/g, " ") : "—"}
                          textColor={C.text}
                          mutedColor={C.textMuted}
                        />
                        <DnaFieldRow
                          label="Risk"
                          value={sub.risk ? String(sub.risk) : "—"}
                          textColor={C.text}
                          mutedColor={C.textMuted}
                        />
                        <DnaFieldRow
                          label="Engine Archetype"
                          value={dnaDisplayLabel(DNA_ENGINE_ARCHETYPE_LABEL, sub.engine_archetype)}
                          textColor={C.text}
                          mutedColor={C.textMuted}
                        />
                        <DnaFieldRow
                          label="Modules"
                          value={
                            Array.isArray(sub.required_modules) && sub.required_modules.length > 0
                              ? sub.required_modules.join(", ")
                              : "—"
                          }
                          textColor={C.text}
                          mutedColor={C.textMuted}
                        />
                        <DnaFieldRow label="Confidence" value={dnaConfPct(sub.confidence)} textColor={C.text} mutedColor={C.textMuted} />
                        <DnaFieldRow
                          label="Bucket Match"
                          value={
                            sub.bucket_match_confidence
                              ? `${String(sub.bucket_match_confidence).toUpperCase()}${
                                  typeof sub.bucket_match_score === "number"
                                    ? ` (${(sub.bucket_match_score * 100).toFixed(0)}%)`
                                    : ""
                                }`
                              : "—"
                          }
                          textColor={C.text}
                          mutedColor={C.textMuted}
                        />
                      </View>
                    ))}
                  </View>
                );
              })}
            </View>
          ) : null}
        </ScrollView>
      )}

      {/* ───── Batch Test Mode (dedicated screen) ───────────────────────── */}
      {mode === "batch" && (
        <ScrollView
          ref={batchScrollRef}
          style={{ flex: 1 }}
          contentContainerStyle={{ padding: 16, paddingBottom: botPad + 24 }}
          keyboardShouldPersistTaps="handled"
          showsVerticalScrollIndicator={false}
        >
          <Text style={{ color: C.textMid, fontSize: 13, marginBottom: 10, lineHeight: 20 }}>
            Har line ek alag question. Paste karke Run dabao — answers niche ek-ek karke aayenge. Admin panel me sab ek hi parent question ke andar save hoga.
          </Text>
          <TextInput
            style={{
              minHeight: 160,
              maxHeight: 280,
              paddingHorizontal: 14,
              paddingVertical: 12,
              backgroundColor: C.isDark ? "#1C1C22" : C.bgCard2,
              borderColor: C.isDark ? "rgba(255,255,255,0.10)" : C.border,
              borderWidth: 1,
              borderRadius: 16,
              color: C.text,
              fontSize: 15,
              lineHeight: 22,
              textAlignVertical: "top",
            }}
            value={batchInput}
            onChangeText={setBatchInput}
            placeholder={"Kya hum dono compatible hain?\nKya hamare values same hain?\nKya hum mentally compatible hain?"}
            placeholderTextColor={C.textMuted}
            multiline
            editable={!showDemo && !batchRunning}
          />
          <View style={{ flexDirection: "row", gap: 10, marginTop: 12, marginBottom: 20 }}>
            <Pressable
              onPress={() => void runBatchTest()}
              disabled={batchRunning || !batchInput.trim()}
              style={({ pressed }) => [{ flex: 2, opacity: pressed ? 0.9 : 1 }]}
            >
              <LinearGradient
                colors={["#5b21b6", "#7c3aed", "#a855f7"]}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 1 }}
                style={{
                  borderRadius: 14,
                  paddingVertical: 14,
                  flexDirection: "row",
                  alignItems: "center",
                  justifyContent: "center",
                  gap: 8,
                }}
              >
                {batchRunning ? (
                  <AcharyaTypingDots caption={batchProgress || "Processing batch…"} />
                ) : (
                  <>
                    <Feather name="play" size={16} color="#fff" />
                    <Text style={{ color: "#fff", fontWeight: "700", fontSize: 15 }}>Run Batch</Text>
                  </>
                )}
              </LinearGradient>
            </Pressable>
            <Pressable
              onPress={() => { setBatchInput(""); setBatchResult(null); setBatchItems([]); }}
              disabled={batchRunning}
              style={({ pressed }) => [
                {
                  flex: 1,
                  borderRadius: 14,
                  paddingVertical: 14,
                  alignItems: "center",
                  justifyContent: "center",
                  backgroundColor: C.bgCard,
                  borderWidth: 1,
                  borderColor: C.border,
                  opacity: pressed ? 0.85 : 1,
                },
              ]}
            >
              <Text style={{ color: C.textMid, fontWeight: "700" }}>Clear</Text>
            </Pressable>
          </View>

          {(batchItems.length > 0 || batchResult) ? (
            <View style={{ gap: 12 }}>
              <Text style={{ color: C.textMuted, fontSize: 12, fontWeight: "700" }}>
                BATCH RESULTS ({batchItems.length || "…"})
              </Text>
              {batchItems.length > 0 ? batchItems.map((it, i) => (
                <View
                  key={`${it.index ?? i}_${it.question.slice(0, 24)}`}
                  style={{
                    padding: 14,
                    borderRadius: 16,
                    backgroundColor: C.bgCard,
                    borderWidth: 1,
                    borderColor: `${C.accent}33`,
                  }}
                >
                  <Text style={{ color: C.accent, fontSize: 12, fontWeight: "700", marginBottom: 6 }}>
                    Q{it.index ?? i + 1}
                  </Text>
                  <Text style={{ color: C.text, fontWeight: "600", marginBottom: 8 }}>{it.question}</Text>
                  {(it.source || it.topic) ? (
                    <Text style={{ color: C.textMuted, fontSize: 11, marginBottom: 8 }}>
                      {[it.source, it.topic].filter(Boolean).join(" · ")}
                    </Text>
                  ) : null}
                  <MarkdownReply text={it.answer || ""} />
                </View>
              )) : batchResult ? (
                <View
                  style={{
                    padding: 14,
                    borderRadius: 16,
                    backgroundColor: C.bgCard,
                    borderWidth: 1,
                    borderColor: `${C.accent}33`,
                  }}
                >
                  <MarkdownReply text={batchResult} />
                </View>
              ) : null}
            </View>
          ) : batchRunning ? (
            <View style={{ paddingVertical: 24, alignItems: "center" }}>
              <AcharyaTypingDots caption="Questions process ho rahe hain…" />
            </View>
          ) : null}
        </ScrollView>
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

      {/* Recording / transcribing banner */}
      {(isRecording || isTranscribing) && (
        <View style={{ paddingHorizontal: 16, paddingVertical: 8, backgroundColor: C.bgCard, borderTopWidth: 1, borderTopColor: C.border, flexDirection: "row", alignItems: "center", gap: 8 }}>
          <View style={{ width: 10, height: 10, borderRadius: 5, backgroundColor: isRecording ? "#E53935" : C.accent }} />
          <Text style={{ color: C.text, fontSize: 13, fontWeight: "600" }}>
            {isRecording ? "Sun raha hoon… dobara mic dabao stop ke liye" : "Samajh raha hoon…"}
          </Text>
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
          placeholder={isRecording ? "Bol rahe ho…" : t.askPlaceholder}
          placeholderTextColor={C.textMuted}
          multiline
          editable={!showDemo && !isRecording && !isTranscribing}
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
          disabled={isRecording || isTranscribing}
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

            <Text style={[qm.title, { color: C.text }]}>Daily limit poora</Text>

            <Text style={[qm.usage, { color: C.textMid }]}>
              <Text style={{ fontWeight: "700", color: C.text }}>{quotaModal?.used ?? 0}</Text>
              <Text> / </Text>
              <Text style={{ fontWeight: "700", color: C.text }}>{quotaModal?.limit ?? 0}</Text>
              <Text> questions used today</Text>
            </Text>

            <Text style={[qm.msg, { color: C.textMuted }]}>
              {quotaModal?.plan === "pro"
                ? quotaModal?.message
                : quotaModal?.plan === "basic"
                  ? "Basic plan mein 10 questions/day milte hain. Pro upgrade karke unlimited paayein."
                  : quotaModal?.plan === "trial"
                    ? "Trial mein 3 questions/day milte hain. Pro lekar unlimited karein."
                    : "Free mein 1 question/day. Trial start karein ya Basic/Pro lein."}
            </Text>

            {quotaModal?.plan !== "pro" && (
              <Pressable
                onPress={() => {
                  setQuotaModal(null);
                  router.push("/subscription");
                }}
                style={({ pressed }) => [{ width: "100%", marginTop: 4, opacity: pressed ? 0.9 : 1 }]}
              >
                <LinearGradient
                  colors={["#d97706", "#f59e0b"]}
                  start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }}
                  style={qm.cta}
                >
                  <Feather name="zap" size={15} color="#fff" />
                  <Text style={qm.ctaText}>Upgrade Now</Text>
                </LinearGradient>
              </Pressable>
            )}

            <Pressable onPress={() => setQuotaModal(null)} style={qm.dismiss}>
              <Text style={[qm.dismissText, { color: C.textMuted }]}>
                {quotaModal?.plan === "pro" ? "Theek hai" : "Baad mein"}
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
            <Text style={[qm.title, { color: C.text }]}>Jawab kis language mein?</Text>
            <Text style={[qm.msg, { color: C.textMuted, marginBottom: 12 }]}>
              Aap jo bhi select karenge, Cosmic Intelligence usi language mein reply karega.
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
              onPress={() => enterAskChat(langPickerDraft)}
              style={({ pressed }) => [{ width: "100%", marginTop: 14, opacity: pressed ? 0.9 : 1 }]}
            >
              <LinearGradient
                colors={[C.btnGradStart, C.btnGradEnd]}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 0 }}
                style={qm.cta}
              >
                <Feather name="message-circle" size={15} color="#fff" />
                <Text style={qm.ctaText}>Start chatting</Text>
              </LinearGradient>
            </Pressable>
            <Pressable onPress={() => setLangPickerVisible(false)} style={qm.dismiss}>
              <Text style={[qm.dismissText, { color: C.textMuted }]}>Cancel</Text>
            </Pressable>
          </Pressable>
        </Pressable>
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
    alignItems: "center", paddingBottom: 14,
    borderBottomWidth: 1, borderBottomColor: "rgba(255,255,255,0.04)",
    gap: 2,
  },
  headerDot: {
    width: 8, height: 8, borderRadius: 4, backgroundColor: "#22c55e",
    marginBottom: 4,
  },
  headerTitle: {
    color: "#dde8f4", fontSize: 16, fontWeight: "700", letterSpacing: -0.2,
    textShadowColor: "rgba(139,92,246,0.5)",
    textShadowOffset: { width: 0, height: 0 },
    textShadowRadius: 12,
  },
  headerSub:   { color: "#3d5a7a", fontSize: 11 },
  askLangRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    alignItems: "center",
    justifyContent: "center",
    gap: 6,
    marginTop: 8,
    paddingHorizontal: 12,
  },
  askLangLabel: { fontSize: 11, fontWeight: "600" },
  askLangChip: {
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 999,
    borderWidth: 1,
  },
  askLangChipText: { fontSize: 11, fontWeight: "700" },
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
  headerTitleRow: { flexDirection: "row", alignItems: "center", justifyContent: "center" },
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
  heroBadge:      { flexDirection: "row", alignItems: "center", gap: 6, paddingHorizontal: 10, paddingVertical: 5, borderRadius: 999, borderWidth: 1 },
  heroBadgeText:  { fontSize: 11, fontWeight: "700", letterSpacing: 0.3 },

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
  pickerWrap: { paddingHorizontal: 16, paddingTop: 28, gap: 14 },
  pickerHi:   { fontSize: 22, fontWeight: "800", letterSpacing: -0.4 },
  pickerSub:  { fontSize: 13, marginBottom: 14 },
  modeCard: {
    borderRadius: 18, overflow: "hidden",
    shadowColor: "#3b82f6",
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.45,
    shadowRadius: 18,
    elevation: 10,
  },
  modeGrad: {
    paddingHorizontal: 18, paddingVertical: 18,
    flexDirection: "row", alignItems: "center", gap: 14,
  },
  modeIconWrap: {
    width: 54, height: 54, borderRadius: 16,
    alignItems: "center", justifyContent: "center",
    backgroundColor: "rgba(255,255,255,0.16)",
    borderWidth: 1, borderColor: "rgba(255,255,255,0.22)",
  },
  modeEmoji: { fontSize: 30 },
  modeTitle: { color: "#fff", fontSize: 18, fontWeight: "800", letterSpacing: -0.3 },
  modeBody:  { color: "#ffffffd0", fontSize: 12.5, lineHeight: 17, marginTop: 4 },
  modeMeta:  { flexDirection: "row", alignItems: "center", gap: 5, marginTop: 8 },
  modeMetaText: { color: "#ffffffcc", fontSize: 10.5, fontWeight: "600" },
  modeBadge: {
    backgroundColor: "rgba(255,255,255,0.22)",
    paddingHorizontal: 7, paddingVertical: 2, borderRadius: 8,
  },
  modeBadgeText: { color: "#fff", fontSize: 9.5, fontWeight: "800", letterSpacing: 0.3 },
  legacyLink: {
    flexDirection: "row", alignItems: "center", justifyContent: "center",
    gap: 6, paddingVertical: 14, marginTop: 4,
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

  assistantMsgActionsWrap: {
    marginLeft: 38,
    marginTop: -4,
    marginBottom: 8,
    paddingHorizontal: 2,
    gap: 4,
  },
  assistantMsgActions: {
    flexDirection: "row",
    justifyContent: "flex-start",
    flexWrap: "wrap",
    gap: 6,
  },
  userMsgActions: {
    flexDirection: "row",
    justifyContent: "flex-end",
    flexWrap: "wrap",
    gap: 6,
    marginTop: -4,
    marginBottom: 8,
    paddingHorizontal: 2,
  },
  userMsgActionBtn: {
    flexDirection: "row",
    alignItems: "center",
    gap: 5,
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 12,
    borderWidth: 1,
  },
  userMsgActionText: { fontSize: 11, fontWeight: "600" },

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
  micBtnRecGlow: {
    shadowColor: "#E53935",
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.7,
    shadowRadius: 12,
    elevation: 8,
  },
  sendGrad: { width: 44, height: 44, borderRadius: 22, alignItems: "center", justifyContent: "center", overflow: "hidden" },
});
