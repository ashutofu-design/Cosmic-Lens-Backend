import { Feather } from "@expo/vector-icons";
import { LinearGradient } from "expo-linear-gradient";
import * as Haptics from "expo-haptics";
import {
  useAudioPlayer, useAudioPlayerStatus, useAudioRecorder,
  setAudioModeAsync, requestRecordingPermissionsAsync,
  RecordingPresets,
} from "expo-audio";
import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  FlatList,
  Keyboard,
  KeyboardAvoidingView,
  Modal,
  Platform,
  Pressable,
  ScrollView,
  Share,
  StatusBar,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";
import * as Clipboard from "expo-clipboard";
import AsyncStorage from "@react-native-async-storage/async-storage";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { CosmicBg } from "@/components/CosmicBg";
import { AcharyaTypingDots } from "@/components/AcharyaTypingDots";
import { CardsCarousel, type CardData } from "@/components/CardsCarousel";
import { MarkdownReply } from "@/components/MarkdownReply";
import { MessageActionsSheet } from "@/components/MessageActionsSheet";
import { useC } from "@/context/ThemeContext";
import { useUser } from "@/context/UserContext";
import { useT } from "@/hooks/useT";
import { getT } from "@/lib/i18n";
import { router } from "expo-router";

import { API_BASE, apiFetch } from "@/lib/apiConfig";

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
  // Phase 2.8.27 — engine_tag from server tells whether this answer was
  // produced by a deterministic engine (LOCKED FACTS injected into the
  // system prompt, "ans-engine") or by a pure LLM call ("ans-cosmo").
  // Rendered as a tiny badge below the action row so the user/dev can
  // see provenance at a glance. Absent on legacy / pre-tag responses.
  engineTag?: "ans-engine" | "ans-cosmo";
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
  "Marriage kab hoga?",
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

export default function AskScreen() {
  const insets = useSafeAreaInsets();
  const C = useC();
  const { kundli, birthData, language, user, profiles, primaryProfileId, setPrimaryProfile } = useUser();
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

  // Resting bottom padding clears the tab bar; keyboard-open shrinks
  // it to a small visual gap so the input sits flush above the kb.
  const inputRowBottomPad = kbVisible ? 10 : botPad + TAB_BAR_HEIGHT;

  // Mode picker: null = show 2-option landing, "chat" = open Cosmic Intelligence chat
  const [mode, setMode] = useState<"chat" | null>(null);

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
            text: `Cosmic Intelligence ready. Aapka chart load ho chuka hai — career, marriage, health, money, timing — koi bhi prashna sharp aur evidence-based mil jayega.`,
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

  // Fetch on landing mount + whenever the user returns to the landing.
  useEffect(() => { if (mode === null) fetchHistory(); }, [mode, fetchHistory]);
  const [quotaModal, setQuotaModal] = useState<null | {
    used: number;
    limit: number;
    plan: string;
    message: string;
  }>(null);
  // Long-press action sheet target message
  const [actionsFor, setActionsFor] = useState<Message | null>(null);
  const listRef = useRef<FlatList>(null);

  // Find the user question that produced a given assistant message. Used by
  // Regenerate so we re-ask the question paired to the LONG-PRESSED bubble,
  // not just the latest one in the thread (architect bug #2 fix).
  const findPrecedingUserQuestion = useCallback(
    (assistantId: string): string => {
      const idx = messages.findIndex((m) => m.id === assistantId);
      if (idx <= 0) return "";
      for (let i = idx - 1; i >= 0; i--) {
        if (messages[i].role === "user") return messages[i].text;
      }
      return "";
    },
    [messages],
  );

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
        const res = await fetch(`${API_BASE}/api/ask/stream`, {
          method: "POST",
          headers,
          body: JSON.stringify({
            question: text.trim(),
            kundli,
            birthData,
            history,
            lang: language,
            user_id: user?.id,
          }),
          signal: ctrl.signal,
        });

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

          // Phase 2.8.27 — engine_tag from server. Defensive type-check
          // before storing so a malformed value can't break the badge UI.
          const _et: any = (json as any).engine_tag;
          const oneShotEngineTag: "ans-engine" | "ans-cosmo" | undefined =
            (_et === "ans-engine" || _et === "ans-cosmo") ? _et : undefined;

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
              engineTag: oneShotEngineTag,
            })
          );
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
        // Phase 2.8.27 — capture engine_tag from `done` event for badge UI.
        let finalEngineTag: "ans-engine" | "ans-cosmo" | undefined;
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
            // Phase 2.8.27 — capture engine_tag (defensive; absent → undef)
            const _et: any = (evt as any).engine_tag;
            if (_et === "ans-engine" || _et === "ans-cosmo") {
              finalEngineTag = _et;
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
            // Phase 2.8.27 — engine_tag (undefined when server omits)
            engineTag: finalEngineTag,
            text:      finalText || accumulated,
            followUps: finalFollowUps,
            streaming: false,
          };
          return next;
        });
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
    [loading, showDemo, kundli, birthData, user?.id, user?.api_key, language, messages, t.askDailyLimitOver],
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
  // Phase 2 — Copy button feedback. Holds the message id whose Copy
  // button was tapped recently; flips icon to "check" + label to
  // "Copied" for ~1.4s before reverting. Null when no message is in
  // the post-copy confirmation window. Timeout id is kept in a ref so
  // unmount can cancel the pending setState (architect lifecycle fix).
  const [copiedFor, setCopiedFor] = useState<string | null>(null);
  const copiedTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  useEffect(() => {
    return () => {
      if (copiedTimerRef.current) {
        clearTimeout(copiedTimerRef.current);
        copiedTimerRef.current = null;
      }
    };
  }, []);

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
    const voiceActive = voiceMsgId === item.id;
    const voiceLoading = voiceActive && voiceState === "loading";
    const voicePlaying = voiceActive && voiceState === "playing";
    return (
      <View>
        <View style={[s.bubble, isUser ? s.bubbleUser : s.bubbleAssistant]}>
          {!isUser && (
            <View style={[s.avatar, { backgroundColor: C.accentBg, borderColor: `${C.accent}30` }]}>
              <Text style={{ fontSize: 12 }}>🔭</Text>
            </View>
          )}
          <Pressable
            onLongPress={() => {
              if (isUser || item.loading) return;
              try { Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium); } catch {}
              setActionsFor(item);
            }}
            delayLongPress={350}
            style={[s.bubbleInner, isUser
              ? [s.bubbleInnerUser, { backgroundColor: C.isDark ? "#1E1B4B" : "#EDE9FE", borderColor: `${C.accent}30` }]
              : [s.bubbleInnerAssistant, { backgroundColor: C.bgCard, borderColor: C.border }]]}
          >
            {item.loading ? (
              <AcharyaTypingDots caption="Cosmic Intelligence calculating…" />
            ) : isUser ? (
              <Text style={[s.bubbleText, s.bubbleTextUser, { color: C.text }]}>{item.text}</Text>
            ) : item.cards && item.cards.length > 0 ? (
              <CardsCarousel
                cards={item.cards}
                trimmedCount={item.trimmedCount ?? 0}
              />
            ) : (
              <MarkdownReply text={item.text} />
            )}

            {/* Action row — assistant messages only, after streaming done.
                Phase 2 polish: Sun lo (voice) + Copy + Share, ChatGPT-style. */}
            {!isUser && !item.loading && !item.streaming && (item.text || "").trim().length > 0 && (
              <View style={s.assistantActionsRow}>
                <Pressable
                  onPress={() => handleVoicePlay(item)}
                  hitSlop={8}
                  style={({ pressed }) => [
                    s.voiceBtn,
                    { borderColor: `${C.accent}40`, backgroundColor: voicePlaying ? `${C.accent}20` : "transparent" },
                    pressed && { opacity: 0.6 },
                  ]}
                >
                  <Feather
                    name={voicePlaying ? "pause" : voiceLoading ? "loader" : "volume-2"}
                    size={12}
                    color={C.accent}
                  />
                  <Text style={[s.voiceBtnText, { color: C.accent }]}>
                    {voiceLoading ? "Ban raha…" : voicePlaying ? "Ruko" : "Sun lo"}
                  </Text>
                </Pressable>

                {/* Copy — copies the markdown reply to clipboard. */}
                <Pressable
                  onPress={async () => {
                    try {
                      await Clipboard.setStringAsync(item.text || "");
                      try { Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success); } catch {}
                      setCopiedFor(item.id);
                      // Cancel any pending revert from a prior tap before
                      // scheduling a fresh one — prevents the "Copied" badge
                      // from disappearing too early if the user taps two
                      // assistant replies in quick succession.
                      if (copiedTimerRef.current) {
                        clearTimeout(copiedTimerRef.current);
                      }
                      copiedTimerRef.current = setTimeout(() => {
                        setCopiedFor((cur) => (cur === item.id ? null : cur));
                        copiedTimerRef.current = null;
                      }, 1400);
                    } catch {}
                  }}
                  hitSlop={8}
                  style={({ pressed }) => [
                    s.actionPlainBtn,
                    pressed && { opacity: 0.55 },
                  ]}
                >
                  <Feather
                    name={copiedFor === item.id ? "check" : "copy"}
                    size={12}
                    color={copiedFor === item.id ? C.accent : C.textMuted}
                  />
                  <Text style={[s.actionPlainBtnText, { color: copiedFor === item.id ? C.accent : C.textMuted }]}>
                    {copiedFor === item.id ? "Copied" : "Copy"}
                  </Text>
                </Pressable>

                {/* Share — RN native share sheet. */}
                <Pressable
                  onPress={async () => {
                    try { Haptics.selectionAsync(); } catch {}
                    try {
                      await Share.share({
                        message: (item.text || "").trim(),
                      });
                    } catch {}
                  }}
                  hitSlop={8}
                  style={({ pressed }) => [
                    s.actionPlainBtn,
                    pressed && { opacity: 0.55 },
                  ]}
                >
                  <Feather name="share-2" size={12} color={C.textMuted} />
                  <Text style={[s.actionPlainBtnText, { color: C.textMuted }]}>
                    Share
                  </Text>
                </Pressable>

                {/* Phase 2.8.27 — engine provenance badge.
                    `ans-engine` = deterministic engine LOCKED FACTS were
                    injected into the system prompt (e.g. marriage engine).
                    `ans-cosmo`  = pure LLM (Cosmo) answer, no engine block.
                    Absent → no badge (legacy / pre-tag responses). */}
                {item.engineTag && (
                  <View
                    style={[
                      s.engineTagChip,
                      {
                        borderColor: item.engineTag === "ans-engine"
                          ? `${C.accent}55`
                          : `${C.textMuted}40`,
                        backgroundColor: item.engineTag === "ans-engine"
                          ? `${C.accent}15`
                          : "transparent",
                      },
                    ]}
                  >
                    <Text
                      style={[
                        s.engineTagText,
                        {
                          color: item.engineTag === "ans-engine"
                            ? C.accent
                            : C.textMuted,
                        },
                      ]}
                    >
                      {item.engineTag}
                    </Text>
                  </View>
                )}
              </View>
            )}
          </Pressable>
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
      </View>
    );
  };

  return (
    <CosmicBg>
    <KeyboardAvoidingView
      style={s.root}
      // iOS: `padding` adds bottom padding equal to (kb_height - offset).
      //   verticalOffset = TAB_BAR_HEIGHT + botPad so the input lands
      //   FLUSH above the keyboard (instead of above the tab bar, which
      //   was the original "half screen" symptom).
      // Android: rely on the default `windowSoftInputMode=adjustResize`
      //   for input pushup; use behavior=undefined to avoid double-
      //   adjustment that compresses the FlatList area.
      behavior={Platform.OS === "ios" ? "padding" : undefined}
      keyboardVerticalOffset={Platform.OS === "ios" ? botPad + TAB_BAR_HEIGHT : 0}
    >
      {/* Header */}
      <View style={[s.header, { paddingTop: topPad + 12, borderBottomColor: C.border }]}>
        {mode === "chat" && (
          <Pressable
            onPress={() => { Haptics.selectionAsync(); setMode(null); }}
            hitSlop={12}
            style={s.backBtn}
          >
            <Feather name="chevron-left" size={20} color={C.text} />
          </Pressable>
        )}
        <View style={s.headerDot} />
        <View style={s.headerTitleRow}>
          <Feather name="cpu" size={15} color={C.accent} style={{ marginRight: 6 }} />
          <Text style={[s.headerTitle, { color: C.text }]}>Cosmic Intelligence</Text>
          <View style={[s.headerLiveDot, { backgroundColor: "#10b981" }]} />
        </View>
        <Text style={[s.headerSub, { color: C.textMuted }]}>Vedic chart analyst · Online</Text>
      </View>

      {/* ── Mode switcher pill (only in chat mode) ───────────────────────── */}
      {mode === "chat" && (
        <View style={[s.modeSwitch, { backgroundColor: (C as any).bgCard2 ?? C.bgCard, borderColor: C.border }]}>
          <View style={[s.modeSwitchSeg, { backgroundColor: C.accentBg, borderColor: `${C.accent}80` }]}>
            <Feather name="message-circle" size={13} color={C.accent} />
            <Text style={[s.modeSwitchText, { color: C.accent }]}>Ask Anything</Text>
          </View>
          <Pressable
            onPress={() => {
              Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
              if (showDemo) { router.push("/onboarding"); return; }
              router.push("/prashna-kundli");
            }}
            style={({ pressed }) => [s.modeSwitchSeg, pressed && { opacity: 0.7 }]}
          >
            <Feather name="hash" size={13} color={C.textMuted} />
            <Text style={[s.modeSwitchText, { color: C.textMuted }]}>Prashna Kundli</Text>
          </Pressable>
        </View>
      )}

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
          <View style={s.heroBadgeRow}>
            <View style={[s.heroBadge, { backgroundColor: `${C.accent}18`, borderColor: `${C.accent}55` }]}>
              <Feather name="cpu" size={11} color={C.accent} />
              <Text style={[s.heroBadgeText, { color: C.accent }]}>AI · Vedic Chart Analyst</Text>
            </View>
          </View>
          <Text style={[s.pickerHi, { color: C.text }]}>How can I help today?</Text>
          <Text style={[s.pickerSub, { color: C.textMid }]}>
            Sharp, evidence-based answers from your unique birth chart — career, marriage, health, money, timing.
          </Text>

          {/* Card 1: Ask Anything (Chat) */}
          <Pressable
            onPress={() => {
              Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
              if (showDemo) { router.push("/onboarding"); return; }
              setMode("chat");
            }}
            style={({ pressed }) => [s.modeCard, pressed && { opacity: 0.85 }]}
          >
            <LinearGradient
              colors={["#1e40af", "#3b82f6", "#06b6d4"]}
              start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }}
              style={s.modeGrad}
            >
              <Text style={s.modeEmoji}>💬</Text>
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
          </Pressable>

          {/* Card 2: Prashna Kundli (KP 1-249) */}
          <Pressable
            onPress={() => {
              Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
              if (showDemo) { router.push("/onboarding"); return; }
              router.push("/prashna-kundli");
            }}
            style={({ pressed }) => [s.modeCard, pressed && { opacity: 0.85 }]}
          >
            <LinearGradient
              colors={["#0e7490", "#0891b2", "#14b8a6"]}
              start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }}
              style={s.modeGrad}
            >
              <Text style={s.modeEmoji}>🔢</Text>
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
          </Pressable>

          {/* ─── Recent Questions ──────────────────────────────────────
              Read-only history strip. Logged server-side after every
              Ask flow (storage layer only — no full kundli, no full
              LLM text persisted). Tap an item to refill the input
              for re-asking. */}
          {!showDemo && history.length > 0 && (
            <View style={s.historyWrap}>
              <View style={s.historyHeader}>
                <Feather name="clock" size={13} color={C.textMid} />
                <Text style={[s.historyTitle, { color: C.textMid }]}>Recent Questions</Text>
              </View>
              {history.slice(0, 5).map(h => (
                <Pressable
                  key={h.id}
                  onPress={() => {
                    Haptics.selectionAsync();
                    setMode("chat");
                    setInput(h.question_text);
                  }}
                  style={({ pressed }) => [
                    s.historyItem,
                    { backgroundColor: C.bgCard, borderColor: C.border },
                    pressed && { opacity: 0.7 },
                  ]}
                >
                  <View style={{ flex: 1, gap: 4 }}>
                    <Text style={[s.historyQ, { color: C.text }]} numberOfLines={2}>
                      {h.question_text}
                    </Text>
                    <View style={s.historyMeta}>
                      <View style={[s.historyTag, { backgroundColor: `${C.accent}22`, borderColor: `${C.accent}55` }]}>
                        <Text style={[s.historyTagText, { color: C.accent }]} numberOfLines={1}>
                          {prettyVerdict(h.verdict_summary)}
                        </Text>
                      </View>
                      <Text style={[s.historyTime, { color: C.textMuted }]}>
                        {prettyAgo(h.created_at)}
                      </Text>
                    </View>
                  </View>
                  <Feather name="chevron-right" size={16} color={C.textMuted} />
                </Pressable>
              ))}
            </View>
          )}

          {/* Optional: small Divya Prashna link (legacy, less prominent) */}
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
          {STARTERS.map(q => (
            <Pressable key={q} style={[s.starter, { backgroundColor: C.bgCard, borderColor: `${C.accent}30` }]} onPress={() => send(q)}>
              <Text style={[s.starterText, { color: C.accent }]}>{q}</Text>
            </Pressable>
          ))}
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

      {/* Phase 6.1.1 — Kundli selector pill row above the input.
          Visible only when 2+ saved profiles exist (most users start
          with just "Self"); tapping a pill switches the active kundli
          via setPrimaryProfile, which updates the useUser() context
          and routes the next /api/ask/stream call to that chart. */}
      {profiles.length > 1 && !showDemo && !kbVisible && (
        <View style={[s.kundliRow, { backgroundColor: C.bg, borderTopColor: C.border }]}>
          <Text style={[s.kundliRowLabel, { color: C.textMuted }]}>Kis ke liye?</Text>
          <ScrollView
            horizontal
            showsHorizontalScrollIndicator={false}
            contentContainerStyle={{ gap: 8, paddingRight: 16 }}
          >
            {profiles.map((p) => {
              const active = p.id === primaryProfileId;
              const label = p.relation || p.name || "Self";
              return (
                <Pressable
                  key={p.id}
                  onPress={() => setPrimaryProfile(p.id)}
                  style={[
                    s.kundliPill,
                    {
                      backgroundColor: active ? `${C.accent}22` : C.bgCard,
                      borderColor: active ? C.accent : C.border,
                    },
                  ]}
                >
                  <Text
                    style={[
                      s.kundliPillText,
                      {
                        color: active ? C.accent : C.text,
                        fontWeight: active ? "700" : "500",
                      },
                    ]}
                  >
                    {active ? "★ " : ""}{label}
                  </Text>
                </Pressable>
              );
            })}
          </ScrollView>
        </View>
      )}

      {/* Input row — dynamic bottom padding:
          • keyboard hidden → clear the tab bar (botPad + TAB_BAR_HEIGHT)
          • keyboard visible → small flush gap (10px), KAV pushes the
            row above the keyboard top automatically. */}
      <View style={[s.inputRow, { paddingBottom: inputRowBottomPad, backgroundColor: C.bg, borderTopColor: C.border }]}>
        <TextInput
          style={[s.input, { backgroundColor: C.bgCard, borderColor: C.border, color: C.text }]}
          value={input}
          onChangeText={setInput}
          placeholder={isRecording ? "Bol rahe ho…" : t.askPlaceholder}
          placeholderTextColor={C.textMuted}
          multiline
          editable={!showDemo && !isRecording && !isTranscribing}
          onSubmitEditing={() => send(input)}
          returnKeyType="send"
        />
        {/* Mic button — tap to record, tap again to stop & transcribe */}
        <Pressable
          onPress={() => {
            if (showDemo) { router.push("/onboarding"); return; }
            if (isTranscribing || loading) return;
            if (isRecording) stopRecordingAndTranscribe();
            else startRecording();
          }}
          style={({ pressed }) => [s.sendBtn, { marginRight: 8 }, pressed && { opacity: 0.7 }]}
        >
          <View style={[s.sendGrad, { backgroundColor: isRecording ? "#E53935" : C.bgCard, borderWidth: 1, borderColor: isRecording ? "#E53935" : C.border }]}>
            <Feather
              name={isRecording ? "square" : "mic"}
              size={16}
              color={isRecording ? "#fff" : C.text}
            />
          </View>
        </Pressable>
        <Pressable
          onPress={() => (showDemo ? router.push("/onboarding") : send(input))}
          style={({ pressed }) => [s.sendBtn, pressed && { opacity: 0.7 }]}
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

      {/* ── Long-press actions sheet (Copy / Share / Regenerate) ─────────── */}
      <MessageActionsSheet
        visible={!!actionsFor}
        text={actionsFor?.text || ""}
        canRegenerate={!loading && !!actionsFor && !!findPrecedingUserQuestion(actionsFor.id)}
        onClose={() => setActionsFor(null)}
        onRegenerate={() => {
          if (!actionsFor) return;
          const q = findPrecedingUserQuestion(actionsFor.id);
          if (q) send(q, { regenerate: true, targetAssistantId: actionsFor.id });
        }}
      />

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
    </KeyboardAvoidingView>
    </CosmicBg>
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
  headerTitle: { color: "#dde8f4", fontSize: 16, fontWeight: "700", letterSpacing: -0.2 },
  headerSub:   { color: "#3d5a7a", fontSize: 11 },
  headerTitleRow: { flexDirection: "row", alignItems: "center" },
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
  modeCard:   { borderRadius: 18, overflow: "hidden" },
  modeGrad: {
    paddingHorizontal: 18, paddingVertical: 18,
    flexDirection: "row", alignItems: "center", gap: 14,
  },
  modeEmoji: { fontSize: 36 },
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
    width: 28, height: 28, borderRadius: 14,
    backgroundColor: "rgba(245,158,11,0.12)", borderWidth: 1, borderColor: "rgba(245,158,11,0.2)",
    alignItems: "center", justifyContent: "center",
    alignSelf: "flex-end",
  },

  bubbleInner: {
    maxWidth: "80%", borderRadius: 16, paddingHorizontal: 14, paddingVertical: 10,
  },
  bubbleInnerUser: {
    backgroundColor: "#0c3257", borderBottomRightRadius: 4,
  },
  bubbleInnerAssistant: {
    backgroundColor: "#040e1f", borderWidth: 1, borderColor: "rgba(255,255,255,0.06)",
    borderBottomLeftRadius: 4,
  },
  bubbleText:       { fontSize: 13, lineHeight: 20 },
  bubbleTextUser:   { color: "#dde8f4" },
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

  // Phase 2 — Action row under assistant message: Sun lo + Copy + Share
  assistantActionsRow: {
    flexDirection: "row", alignItems: "center", flexWrap: "wrap",
    gap: 8, marginTop: 10,
  },
  // Voice play button (Sun lo) — primary accent-bordered chip
  voiceBtn: {
    flexDirection: "row", alignItems: "center", gap: 6,
    paddingHorizontal: 10, paddingVertical: 5,
    borderRadius: 14, borderWidth: 1,
  },
  voiceBtnText: { fontSize: 11, fontWeight: "700", letterSpacing: 0.3 },
  // Phase 2 — secondary action button (Copy / Share). Borderless, muted
  // foreground to keep the voice button as the primary affordance.
  actionPlainBtn: {
    flexDirection: "row", alignItems: "center", gap: 5,
    paddingHorizontal: 8, paddingVertical: 5,
    borderRadius: 12,
  },
  actionPlainBtnText: { fontSize: 11, fontWeight: "600", letterSpacing: 0.3 },

  // Phase 2.8.27 — engine provenance badge (ans-engine / ans-cosmo).
  // Sits inline next to Share in the same flex row as Sun lo / Copy /
  // Share. Distinct visual: bordered chip, smaller font, lowercase.
  engineTagChip: {
    paddingHorizontal: 7, paddingVertical: 3,
    borderRadius: 10, borderWidth: 1,
  },
  engineTagText: {
    fontSize: 10, fontWeight: "700",
    letterSpacing: 0.4, textTransform: "lowercase",
  },

  starters: {
    paddingHorizontal: 16, paddingBottom: 10, gap: 8,
    flexDirection: "row", flexWrap: "wrap",
  },
  starter: {
    paddingHorizontal: 12, paddingVertical: 8, borderRadius: 20,
    backgroundColor: "#040e1f", borderWidth: 1, borderColor: "rgba(245,158,11,0.15)",
  },
  starterText: { color: "#f59e0b", fontSize: 12 },

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

  inputRow: {
    flexDirection: "row", alignItems: "flex-end", gap: 10,
    paddingHorizontal: 14, paddingTop: 12,
    borderTopWidth: StyleSheet.hairlineWidth,
    // borderTopColor + backgroundColor injected at render-time from theme.
  },
  input: {
    flex: 1, borderRadius: 22, borderWidth: 1,
    paddingHorizontal: 16, paddingVertical: 12,
    fontSize: 14, lineHeight: 20, maxHeight: 120, minHeight: 44,
    // backgroundColor + borderColor + color injected at render-time from theme.
  },
  sendBtn:  { borderRadius: 22, overflow: "hidden" },
  sendGrad: { width: 44, height: 44, borderRadius: 22, alignItems: "center", justifyContent: "center" },
});
