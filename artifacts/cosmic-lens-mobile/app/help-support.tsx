/**
 * Help & Support — persistent chat with the Cosmic Care Team.
 * Text + images; history saved; no timer (unlike V3 live consultations).
 * Designed to feel like a large, professional, always-on support desk.
 */
import { Feather, MaterialCommunityIcons } from "@expo/vector-icons";
import * as Haptics from "expo-haptics";
import * as ImagePicker from "expo-image-picker";
import { LinearGradient } from "expo-linear-gradient";
import { router, Stack, useFocusEffect } from "expo-router";
import React, { useCallback, useEffect, useRef, useState } from "react";
import {
  ActivityIndicator,
  Alert,
  FlatList,
  I18nManager,
  Image,
  KeyboardAvoidingView,
  Linking,
  Platform,
  Pressable,
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { AcharyaTypingDots } from "@/components/AcharyaTypingDots";
import { useC } from "@/context/ThemeContext";
import { useUser } from "@/context/UserContext";
import { API_BASE } from "@/lib/apiConfig";
import { ensureBotReply } from "@/lib/supportHelpFaq";

type SupportMessage = {
  id: string;
  sender: "user" | "admin" | "system" | "bot";
  text?: string;
  image_url?: string;
  ts: string;
};

type TxRow = {
  id: string;
  kind: string;
  title: string;
  subtitle?: string;
  amount_inr: number;
  order_id: string;
  status: string;
  paid_at: string | null;
};

type TabKey = "chat" | "tx";

const SUPPORT_EMAIL = "supportcosmiclens@gmail.com";

const TEAM_AVATARS = [
  { initials: "AR", bg: "#7c3aed" },
  { initials: "PK", bg: "#0ea5e9" },
  { initials: "SM", bg: "#f59e0b" },
];

const QUICK_TOPICS = [
  { icon: "hash" as const, label: "COSMO ID", send: "COSMO ID kya hai?" },
  { icon: "file-text" as const, label: "Meri PDF kahan?", send: "Meri PDF / report kahan milegi?" },
  { icon: "star" as const, label: "Pro prices", send: "Numerology, Love Reality, Milan Pro ke prices kya hain?" },
  { icon: "compass" as const, label: "AstroVastu", send: "AstroVastu kaise use karun aur price kya hai?" },
  { icon: "credit-card" as const, label: "Payment / Transactions", send: "Payment kahan dikhegi? Transactions kaise check karun?" },
  { icon: "user" as const, label: "Birth details", send: "Birth details kaise change karun?" },
  { icon: "headphones" as const, label: "Team se baat", send: "Mujhe team se baat karni hai." },
];

function mediaSrc(url?: string): string {
  if (!url) return "";
  if (url.startsWith("http") || url.startsWith("data:")) return url;
  return `${API_BASE}${url.startsWith("/") ? "" : "/"}${url}`;
}

function timeLabel(ts?: string): string {
  if (!ts) return "";
  const d = new Date(ts);
  if (Number.isNaN(d.getTime())) return "";
  return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function formatTxWhen(iso: string | null) {
  if (!iso) return "—";
  try {
    const d = new Date(/[zZ]|[+-]\d{2}/.test(iso) ? iso : `${iso}Z`);
    if (Number.isNaN(d.getTime())) return iso.slice(0, 10);
    return d.toLocaleString("en-IN", {
      timeZone: "Asia/Kolkata",
      dateStyle: "medium",
      timeStyle: "short",
    });
  } catch {
    return iso.slice(0, 16);
  }
}

/** Gold coin for money amounts. */
function CoinAmount({ amount, large = false }: { amount: number; large?: boolean }) {
  const size = large ? 18 : 15;
  return (
    <View style={{ flexDirection: "row", alignItems: "center", gap: 4 }}>
      <MaterialCommunityIcons name="circle-multiple" size={size} color="#f59e0b" />
      <Text
        style={{
          color: "#f59e0b",
          fontSize: large ? 16 : 14,
          fontWeight: "800",
          fontFamily: "Nunito_700Bold",
        }}
      >
        {amount > 0 ? amount.toLocaleString("en-IN") : "—"}
      </Text>
    </View>
  );
}

function TeamAvatarCluster({ size = 30 }: { size?: number }) {
  return (
    <View style={{ flexDirection: "row" }}>
      {TEAM_AVATARS.map((a, i) => (
        <View
          key={a.initials}
          style={{
            width: size,
            height: size,
            borderRadius: size / 2,
            backgroundColor: a.bg,
            alignItems: "center",
            justifyContent: "center",
            marginLeft: i === 0 ? 0 : -(size / 3),
            borderWidth: 2,
            borderColor: "rgba(255,255,255,0.9)",
            zIndex: TEAM_AVATARS.length - i,
          }}
        >
          <Text style={{ color: "#fff", fontSize: size * 0.36, fontWeight: "800" }}>
            {a.initials}
          </Text>
        </View>
      ))}
    </View>
  );
}

export default function HelpSupportScreen() {
  const C = useC();
  const insets = useSafeAreaInsets();
  const { user } = useUser();
  const listRef = useRef<FlatList>(null);
  const inputRef = useRef<TextInput>(null);

  const [threadId, setThreadId] = useState<string | null>(null);
  const [messages, setMessages] = useState<SupportMessage[]>([]);
  const [draft, setDraft] = useState("");
  const [sending, setSending] = useState(false);
  const [loading, setLoading] = useState(true);
  const [adminTyping, setAdminTyping] = useState(false);
  const [tab, setTab] = useState<TabKey>("chat");
  const [txItems, setTxItems] = useState<TxRow[]>([]);
  const [txLoading, setTxLoading] = useState(false);
  const [txRefreshing, setTxRefreshing] = useState(false);

  const authHeaders = useCallback(
    () => ({
      "X-API-Key": user?.api_key || "",
      Accept: "application/json",
      "Content-Type": "application/json",
    }),
    [user?.api_key],
  );

  const ensureThread = useCallback(async (): Promise<string | null> => {
    if (!user?.id || !user?.api_key) return null;
    const res = await fetch(`${API_BASE}/api/support/thread`, {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({ user_id: user.id }),
    });
    const json = await res.json().catch(() => ({}) as any);
    if (!res.ok || !json?.thread?.thread_id) {
      throw new Error(json?.error || `Could not open chat (${res.status})`);
    }
    return String(json.thread.thread_id);
  }, [user?.id, user?.api_key, authHeaders]);

  const refresh = useCallback(
    async (sid: string): Promise<SupportMessage[] | null> => {
      if (!user?.id || !user?.api_key) return null;
      const res = await fetch(
        `${API_BASE}/api/support/thread/${encodeURIComponent(sid)}/messages?user_id=${user.id}`,
        { headers: authHeaders() },
      );
      const json = await res.json().catch(() => ({}) as any);
      if (res.status === 404 || json?.error === "not_found") {
        try {
          const next = await ensureThread();
          if (next && next !== sid) {
            setThreadId(next);
            const res2 = await fetch(
              `${API_BASE}/api/support/thread/${encodeURIComponent(next)}/messages?user_id=${user.id}`,
              { headers: authHeaders() },
            );
            const json2 = await res2.json().catch(() => ({}) as any);
            if (!res2.ok) {
              setMessages([]);
              return [];
            }
            const msgs2: SupportMessage[] = Array.isArray(json2.messages) ? json2.messages : [];
            setMessages(ensureBotReply(msgs2, "", "", user?.cosmo_user_id || "") as SupportMessage[]);
            setAdminTyping(Boolean(json2.admin_typing));
            return msgs2;
          }
        } catch {
          /* fall through */
        }
        setMessages([]);
        return [];
      }
      if (!res.ok) return null;
      const msgs: SupportMessage[] = Array.isArray(json.messages) ? json.messages : [];
      setMessages(ensureBotReply(msgs, "", "", user?.cosmo_user_id || "") as SupportMessage[]);
      setAdminTyping(Boolean(json.admin_typing));
      return msgs;
    },
    [user?.id, user?.api_key, authHeaders, ensureThread],
  );

  const fetchTransactions = useCallback(async () => {
    if (!user?.id || !user?.api_key) {
      setTxItems([]);
      return;
    }
    try {
      const res = await fetch(`${API_BASE}/api/user/${user.id}/purchases`, {
        headers: { "X-API-Key": user.api_key, Accept: "application/json" },
      });
      const json = await res.json().catch(() => ({}) as any);
      if (!res.ok) throw new Error(String(json.error || res.status));
      setTxItems(Array.isArray(json.purchases) ? json.purchases : []);
    } catch {
      /* keep previous list */
    } finally {
      setTxLoading(false);
      setTxRefreshing(false);
    }
  }, [user?.id, user?.api_key]);

  useFocusEffect(
    useCallback(() => {
      if (tab === "tx" && user?.id && user?.api_key) {
        setTxLoading(true);
        void fetchTransactions();
      }
    }, [tab, user?.id, user?.api_key, fetchTransactions]),
  );

  useEffect(() => {
    if (!user?.id || !user?.api_key) {
      setLoading(false);
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        setLoading(true);
        const sid = await ensureThread();
        if (cancelled || !sid) return;
        setThreadId(sid);
        await refresh(sid);
      } catch (e) {
        Alert.alert(
          "Support unavailable",
          e instanceof Error ? e.message : "Please try again shortly.",
        );
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [user?.id, user?.api_key, ensureThread, refresh]);

  const lastMsg = messages.length ? messages[messages.length - 1] : null;
  const waitingHelp = sending || (!!lastMsg && lastMsg.sender === "user");

  useEffect(() => {
    if (!threadId) return;
    const poll = setInterval(() => void refresh(threadId), waitingHelp ? 800 : 2500);
    return () => clearInterval(poll);
  }, [threadId, refresh, waitingHelp]);

  const sendText = async (forcedText?: string) => {
    const text = (forcedText ?? draft).trim();
    if (!text || !threadId || sending || !user?.id) return;
    setSending(true);
    setDraft("");
    const localUser: SupportMessage = {
      id: `local-user-${Date.now()}`,
      sender: "user",
      text,
      ts: new Date().toISOString(),
    };
    setMessages(
      (prev) =>
        ensureBotReply([...prev, localUser], text, "", user?.cosmo_user_id || "") as SupportMessage[],
    );
    requestAnimationFrame(() => listRef.current?.scrollToEnd({ animated: true }));
    const ac = new AbortController();
    const kill = setTimeout(() => ac.abort(), 20000);
    try {
      const res = await fetch(
        `${API_BASE}/api/support/thread/${encodeURIComponent(threadId)}/message`,
        {
          method: "POST",
          headers: authHeaders(),
          body: JSON.stringify({ user_id: user.id, text }),
          signal: ac.signal,
        },
      );
      const json = await res.json().catch(() => ({}) as any);
      if (res.status === 404 || json?.error === "not_found") {
        const sid = await ensureThread();
        if (!sid) {
          Alert.alert("Send failed", "Chat was closed. Please try again.");
          setDraft(text);
          return;
        }
        setThreadId(sid);
        const retry = await fetch(
          `${API_BASE}/api/support/thread/${encodeURIComponent(sid)}/message`,
          {
            method: "POST",
            headers: authHeaders(),
            body: JSON.stringify({ user_id: user.id, text }),
          },
        );
        const retryJson = await retry.json().catch(() => ({}) as any);
        if (!retry.ok) {
          Alert.alert("Send failed", String(retryJson.error || `HTTP ${retry.status}`));
          setDraft(text);
          return;
        }
        let retryMsgs: SupportMessage[] = Array.isArray(retryJson.messages)
          ? retryJson.messages
          : [];
        if (!retryMsgs.length) {
          retryMsgs = (await refresh(sid)) || [];
        }
        setMessages(
          ensureBotReply(
            retryMsgs,
            text,
            typeof retryJson.ai?.reply === "string" ? retryJson.ai.reply : "",
            user?.cosmo_user_id || "",
          ) as SupportMessage[],
        );
        requestAnimationFrame(() => listRef.current?.scrollToEnd({ animated: true }));
        return;
      }
      if (!res.ok) {
        Alert.alert("Send failed", String(json.error || `HTTP ${res.status}`));
        setDraft(text);
        return;
      }
      let msgs: SupportMessage[] = Array.isArray(json.messages)
        ? json.messages
        : [];
      if (!msgs.length) {
        msgs = (await refresh(threadId)) || [];
      }
      const withBot = ensureBotReply(
        msgs,
        text,
        typeof json.ai?.reply === "string" ? json.ai.reply : "",
        user?.cosmo_user_id || "",
      ) as SupportMessage[];
      setMessages(withBot);
      requestAnimationFrame(() => listRef.current?.scrollToEnd({ animated: true }));
    } catch (e) {
      const aborted =
        (e instanceof Error && e.name === "AbortError") ||
        String(e).toLowerCase().includes("abort");
      if (aborted && threadId) {
        await refresh(threadId);
      } else {
        Alert.alert("Send failed", e instanceof Error ? e.message : "Network error");
        setDraft(text);
      }
    } finally {
      clearTimeout(kill);
      setSending(false);
    }
  };

  const sendImage = async () => {
    if (!threadId || sending || !user?.id) return;
    try {
      Haptics.selectionAsync().catch(() => {});
      const perm = await ImagePicker.requestMediaLibraryPermissionsAsync();
      if (!perm.granted) {
        Alert.alert("Permission needed", "Allow photo access to send a screenshot.");
        return;
      }
      const picked = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ImagePicker.MediaTypeOptions.Images,
        quality: 0.7,
        base64: true,
      });
      if (picked.canceled || !picked.assets?.[0]?.base64) return;
      const asset = picked.assets[0];
      const mime = asset.mimeType || "image/jpeg";
      const dataUrl = `data:${mime};base64,${asset.base64}`;
      setSending(true);
      const res = await fetch(
        `${API_BASE}/api/support/thread/${encodeURIComponent(threadId)}/message`,
        {
          method: "POST",
          headers: authHeaders(),
          body: JSON.stringify({ user_id: user.id, data_url: dataUrl, text: "" }),
        },
      );
      const json = await res.json().catch(() => ({}) as any);
      if (res.status === 404 || json?.error === "not_found") {
        const sid = await ensureThread();
        if (!sid) {
          Alert.alert("Image failed", "Chat was closed. Please try again.");
          return;
        }
        setThreadId(sid);
        const retry = await fetch(
          `${API_BASE}/api/support/thread/${encodeURIComponent(sid)}/message`,
          {
            method: "POST",
            headers: authHeaders(),
            body: JSON.stringify({ user_id: user.id, data_url: dataUrl, text: "" }),
          },
        );
        const retryJson = await retry.json().catch(() => ({}) as any);
        if (!retry.ok) {
          Alert.alert("Image failed", String(retryJson.error || `HTTP ${retry.status}`));
          return;
        }
        await refresh(sid);
        requestAnimationFrame(() => listRef.current?.scrollToEnd({ animated: true }));
        return;
      }
      if (!res.ok) {
        Alert.alert("Image failed", String(json.error || `HTTP ${res.status}`));
        return;
      }
      await refresh(threadId);
      requestAnimationFrame(() => listRef.current?.scrollToEnd({ animated: true }));
    } catch (e) {
      Alert.alert("Image failed", e instanceof Error ? e.message : "Could not send");
    } finally {
      setSending(false);
    }
  };

  const pickTopic = (topic: (typeof QUICK_TOPICS)[number]) => {
    Haptics.selectionAsync().catch(() => {});
    void sendText(topic.send);
  };

  const firstName = (user?.name || "").trim().split(/\s+/)[0] || "";

  // ── Login gate ──────────────────────────────────────────────────────────────
  if (!user?.id || !user?.api_key) {
    return (
      <View style={[s.root, { backgroundColor: C.bg }]}>
        <Stack.Screen options={{ headerShown: false }} />
        <LinearGradient
          colors={C.isDark ? ["#1e1b4b", "#0f172a"] : ["#4f46e5", "#7c3aed"]}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 1 }}
          style={[s.heroHeader, { paddingTop: insets.top + 10 }]}
        >
          <Pressable onPress={() => router.back()} hitSlop={10} style={s.back}>
            <Feather
              name={I18nManager.isRTL ? "arrow-right" : "arrow-left"}
              size={20}
              color="#fff"
            />
          </Pressable>
          <View style={{ flex: 1 }}>
            <Text style={s.heroTitle}>Cosmic Help</Text>
            <View style={s.onlineRow}>
              <View style={s.onlineDot} />
              <Text style={s.heroSub}>AI answers · team if needed</Text>
            </View>
          </View>
          <TeamAvatarCluster />
        </LinearGradient>
        <View style={s.center}>
          <MaterialCommunityIcons name="face-agent" size={48} color={C.accent} />
          <Text style={[s.emptyTitle, { color: C.text }]}>Login required</Text>
          <Text style={[s.emptyBody, { color: C.textMuted }]}>
            Sign in to ask Cosmic Help — short answers on the app, team for extra issues.
          </Text>
          <Pressable
            style={[s.loginBtn, { backgroundColor: C.accent }]}
            onPress={() => router.push("/login")}
          >
            <Text style={s.loginBtnTxt}>Login</Text>
          </Pressable>
          <Pressable
            onPress={() => Linking.openURL(`mailto:${SUPPORT_EMAIL}`)}
            style={{ marginTop: 16 }}
          >
            <Text style={{ color: C.accent, fontWeight: "600" }}>Email {SUPPORT_EMAIL}</Text>
          </Pressable>
        </View>
      </View>
    );
  }

  const hasUserMessages = messages.some((m) => m.sender === "user");

  return (
    <KeyboardAvoidingView
      style={[s.root, { backgroundColor: C.isDark ? "#050709" : "#f4f4fb" }]}
      behavior={Platform.OS === "ios" ? "padding" : undefined}
      keyboardVerticalOffset={0}
    >
      <Stack.Screen options={{ headerShown: false }} />

      {/* ── Team header ── */}
      <LinearGradient
        colors={C.isDark ? ["#1e1b4b", "#0f172a"] : ["#4f46e5", "#7c3aed"]}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
        style={[s.heroHeader, { paddingTop: insets.top + 10 }]}
      >
        <Pressable onPress={() => router.back()} hitSlop={10} style={s.back}>
          <Feather
            name={I18nManager.isRTL ? "arrow-right" : "arrow-left"}
            size={20}
            color="#fff"
          />
        </Pressable>
        <View style={{ flex: 1 }}>
          <Text style={s.heroTitle}>Cosmic Help</Text>
          <View style={s.onlineRow}>
            <View style={s.onlineDot} />
            <Text style={s.heroSub}>Instant answers · team if needed</Text>
          </View>
        </View>
        <TeamAvatarCluster />
      </LinearGradient>

      {/* ── Trust strip ── */}
      <View
        style={[
          s.trustStrip,
          {
            backgroundColor: C.isDark ? "#0d1117" : "#fff",
            borderBottomColor: C.border,
          },
        ]}
      >
        <View style={s.trustItem}>
          <Feather name="clock" size={13} color={C.accent} />
          <Text style={[s.trustTxt, { color: C.textMuted }]}>AI first</Text>
        </View>
        <View style={[s.trustDivider, { backgroundColor: C.border }]} />
        <View style={s.trustItem}>
          <Feather name="zap" size={13} color={C.accent} />
          <Text style={[s.trustTxt, { color: C.textMuted }]}>Short answers</Text>
        </View>
        <View style={[s.trustDivider, { backgroundColor: C.border }]} />
        <View style={s.trustItem}>
          <Feather name="lock" size={13} color={C.accent} />
          <Text style={[s.trustTxt, { color: C.textMuted }]}>100% private</Text>
        </View>
      </View>

      {/* ── Chat | Transactions tabs ── */}
      <View
        style={[
          s.tabRow,
          {
            backgroundColor: C.isDark ? "#0a0c12" : "#eeeef8",
            borderBottomColor: C.border,
          },
        ]}
      >
        <Pressable
          onPress={() => {
            Haptics.selectionAsync().catch(() => {});
            setTab("chat");
          }}
          style={[
            s.tabBtn,
            tab === "chat" && {
              backgroundColor: C.isDark ? "#1e1b4b" : "#fff",
              borderColor: C.accent,
            },
          ]}
        >
          <Feather name="message-circle" size={14} color={tab === "chat" ? C.accent : C.textMuted} />
          <Text style={[s.tabTxt, { color: tab === "chat" ? C.accent : C.textMuted }]}>
            Help
          </Text>
        </Pressable>
        <Pressable
          onPress={() => {
            Haptics.selectionAsync().catch(() => {});
            setTab("tx");
            setTxLoading(true);
            void fetchTransactions();
          }}
          style={[
            s.tabBtn,
            tab === "tx" && {
              backgroundColor: C.isDark ? "#1e1b4b" : "#fff",
              borderColor: "#f59e0b",
            },
          ]}
        >
          <MaterialCommunityIcons
            name="circle-multiple"
            size={15}
            color={tab === "tx" ? "#f59e0b" : C.textMuted}
          />
          <Text style={[s.tabTxt, { color: tab === "tx" ? "#f59e0b" : C.textMuted }]}>
            Transactions
          </Text>
        </Pressable>
      </View>

      {tab === "tx" ? (
        txLoading && txItems.length === 0 ? (
          <View style={s.center}>
            <ActivityIndicator size="large" color="#f59e0b" />
            <Text style={{ color: C.textMuted, fontSize: 13, marginTop: 8 }}>
              Loading your coin history…
            </Text>
          </View>
        ) : (
          <FlatList
            data={txItems}
            keyExtractor={(item) => item.id}
            contentContainerStyle={[
              s.txList,
              txItems.length === 0 && { flexGrow: 1, justifyContent: "center" },
              { paddingBottom: insets.bottom + 24 },
            ]}
            refreshControl={
              <RefreshControl
                refreshing={txRefreshing}
                onRefresh={() => {
                  setTxRefreshing(true);
                  void fetchTransactions();
                }}
                tintColor="#f59e0b"
              />
            }
            ListHeaderComponent={
              <View
                style={[
                  s.txHero,
                  {
                    backgroundColor: C.isDark ? "#1a1408" : "#fffbeb",
                    borderColor: C.isDark ? "#78350f66" : "#fde68a",
                  },
                ]}
              >
                <MaterialCommunityIcons name="circle-multiple" size={28} color="#f59e0b" />
                <View style={{ flex: 1 }}>
                  <Text style={[s.txHeroTitle, { color: C.text }]}>Transaction history</Text>
                  <Text style={[s.txHeroSub, { color: C.textMuted }]}>
                    All payments · V1 packs · V3 live · reports — shown as coins
                  </Text>
                </View>
              </View>
            }
            ListEmptyComponent={
              <View style={s.center}>
                <MaterialCommunityIcons name="circle-multiple" size={44} color={C.textDim} />
                <Text style={[s.emptyTitle, { color: C.text }]}>No transactions yet</Text>
                <Text style={[s.emptyBody, { color: C.textMuted }]}>
                  Jab aap Cosmic Packs, V3 live, ya koi report kharidoge — yahan coin ke saath dikhega.
                </Text>
              </View>
            }
            renderItem={({ item }) => (
              <View
                style={[
                  s.txCard,
                  {
                    backgroundColor: C.isDark ? "#11131c" : "#fff",
                    borderColor: C.isDark ? "#232636" : "#e6e6f2",
                  },
                ]}
              >
                <View style={[s.txIcon, { backgroundColor: "#f59e0b18" }]}>
                  <MaterialCommunityIcons
                    name={
                      item.kind === "v3_live"
                        ? "lightning-bolt"
                        : item.kind === "ask_v1"
                          ? "chat-question"
                          : item.kind === "subscription"
                            ? "crown"
                            : "receipt"
                    }
                    size={18}
                    color="#f59e0b"
                  />
                </View>
                <View style={{ flex: 1, gap: 3, minWidth: 0 }}>
                  <Text style={[s.txTitle, { color: C.text }]} numberOfLines={2}>
                    {item.title}
                  </Text>
                  {item.subtitle ? (
                    <Text style={[s.txSub, { color: C.textMuted }]} numberOfLines={1}>
                      {item.subtitle}
                    </Text>
                  ) : null}
                  <Text style={[s.txMeta, { color: C.textDim }]}>
                    {formatTxWhen(item.paid_at)}
                    {item.status && item.status !== "paid" ? ` · ${item.status}` : ""}
                  </Text>
                </View>
                <CoinAmount amount={item.amount_inr} />
              </View>
            )}
          />
        )
      ) : loading ? (
        <View style={s.center}>
          <ActivityIndicator size="large" color={C.accent} />
          <Text style={{ color: C.textMuted, fontSize: 13, marginTop: 8 }}>
            Connecting Cosmic Help…
          </Text>
        </View>
      ) : (
        <FlatList
          ref={listRef}
          data={messages}
          keyExtractor={(m) => m.id}
          contentContainerStyle={s.list}
          onContentSizeChange={() => listRef.current?.scrollToEnd({ animated: false })}
          ListHeaderComponent={
            <View
              style={[
                s.welcomeCard,
                {
                  backgroundColor: C.isDark ? "#11131c" : "#fff",
                  borderColor: C.isDark ? "#232636" : "#e6e6f2",
                },
              ]}
            >
              <View style={s.welcomeTop}>
                <View style={[s.agentBadge, { backgroundColor: `${C.accent}22` }]}>
                  <MaterialCommunityIcons name="face-agent" size={26} color={C.accent} />
                </View>
                <View style={{ flex: 1 }}>
                  <Text style={[s.welcomeTitle, { color: C.text }]}>
                    {firstName ? `Namaste ${firstName} 🙏` : "Namaste 🙏"}
                  </Text>
                  <Text style={[s.welcomeBody, { color: C.textMuted }]}>
                    App ke sawaal ka short jawab yahin. Extra baat — payment,
                    refund, missing PDF — team join karegi.
                  </Text>
                </View>
              </View>
              {!hasUserMessages ? (
                <ScrollView
                  horizontal
                  showsHorizontalScrollIndicator={false}
                  contentContainerStyle={{ gap: 8, paddingTop: 12 }}
                >
                  {QUICK_TOPICS.map((topic) => (
                    <Pressable
                      key={topic.label}
                      onPress={() => pickTopic(topic)}
                      style={[
                        s.topicChip,
                        {
                          borderColor: `${C.accent}66`,
                          backgroundColor: `${C.accent}14`,
                        },
                      ]}
                    >
                      <Feather name={topic.icon} size={13} color={C.accent} />
                      <Text style={[s.topicTxt, { color: C.accent }]}>{topic.label}</Text>
                    </Pressable>
                  ))}
                </ScrollView>
              ) : null}
            </View>
          }
          ListFooterComponent={
            waitingHelp || adminTyping ? (
              <View style={s.supportRow}>
                <View style={[s.msgAvatar, { backgroundColor: waitingHelp ? "#0ea5e9" : "#7c3aed" }]}>
                  <MaterialCommunityIcons
                    name={waitingHelp ? "robot-outline" : "face-agent"}
                    size={15}
                    color="#fff"
                  />
                </View>
                <View
                  style={[
                    s.bubble,
                    {
                      backgroundColor: C.isDark ? "#11131c" : "#fff",
                      borderColor: C.isDark ? "#232636" : "#e6e6f2",
                      minWidth: 190,
                    },
                  ]}
                >
                  <Text style={[s.who, { color: C.textMuted }]}>
                    {waitingHelp ? "Cosmic Help" : "Support team"}
                  </Text>
                  <AcharyaTypingDots
                    caption={waitingHelp ? "Cosmic Help is typing…" : "Team is typing…"}
                  />
                </View>
              </View>
            ) : null
          }
          renderItem={({ item }) => {
            const mine = item.sender === "user";
            const sys = item.sender === "system";
            if (sys) {
              return (
                <View style={s.sysWrap}>
                  <Text style={[s.sysText, { color: C.textMuted }]}>{item.text}</Text>
                </View>
              );
            }
            if (mine) {
              return (
                <View style={{ alignSelf: "flex-end", maxWidth: "82%", marginBottom: 10 }}>
                  <LinearGradient
                    colors={C.isDark ? ["#4f46e5", "#7c3aed"] : ["#4f46e5", "#7c3aed"]}
                    start={{ x: 0, y: 0 }}
                    end={{ x: 1, y: 1 }}
                    style={[s.bubble, { borderWidth: 0 }]}
                  >
                    {item.text ? <Text style={[s.msg, { color: "#fff" }]}>{item.text}</Text> : null}
                    {item.image_url ? (
                      <Image
                        source={{ uri: mediaSrc(item.image_url) }}
                        style={s.img}
                        resizeMode="cover"
                      />
                    ) : null}
                  </LinearGradient>
                  <Text style={[s.time, { color: C.textMuted, textAlign: "right" }]}>
                    {timeLabel(item.ts)}
                  </Text>
                </View>
              );
            }
            const bot = item.sender === "bot";
            return (
              <View style={s.supportRow}>
                <View style={[s.msgAvatar, { backgroundColor: bot ? "#0ea5e9" : "#7c3aed" }]}>
                  <MaterialCommunityIcons
                    name={bot ? "robot-outline" : "face-agent"}
                    size={15}
                    color="#fff"
                  />
                </View>
                <View style={{ maxWidth: "78%" }}>
                  <View
                    style={[
                      s.bubble,
                      {
                        backgroundColor: C.isDark ? "#11131c" : "#fff",
                        borderColor: C.isDark ? "#232636" : "#e6e6f2",
                      },
                    ]}
                  >
                    <Text style={[s.who, { color: bot ? "#0ea5e9" : C.accent }]}>
                      {bot ? "Cosmic Help" : "Support team"}
                    </Text>
                    {item.text ? (
                      <Text style={[s.msg, { color: C.text }]}>{item.text}</Text>
                    ) : null}
                    {item.image_url ? (
                      <Image
                        source={{ uri: mediaSrc(item.image_url) }}
                        style={s.img}
                        resizeMode="cover"
                      />
                    ) : null}
                  </View>
                  <Text style={[s.time, { color: C.textMuted }]}>{timeLabel(item.ts)}</Text>
                </View>
              </View>
            );
          }}
        />
      )}

      {/* ── Composer (chat only) ── */}
      {tab === "chat" ? (
      <View
        style={[
          s.inputRow,
          {
            paddingBottom: Math.max(insets.bottom, 10),
            borderTopColor: C.border,
            backgroundColor: C.isDark ? "#0a0a0c" : "#fff",
          },
        ]}
      >
        <Pressable
          onPress={() => void sendImage()}
          disabled={sending || !threadId}
          style={[s.iconBtn, { opacity: sending || !threadId ? 0.4 : 1 }]}
        >
          <Feather name="image" size={22} color={C.accent} />
        </Pressable>
        <TextInput
          ref={inputRef}
          value={draft}
          onChangeText={setDraft}
          placeholder="App ke baare mein poochho…"
          placeholderTextColor={C.textMuted}
          editable={!sending && !!threadId}
          style={[
            s.input,
            {
              color: C.text,
              backgroundColor: C.isDark ? "#141418" : "#f4f4fb",
              borderColor: C.border,
              fontSize: 16,
            },
          ]}
          multiline
          maxLength={4000}
        />
        <Pressable
          onPress={() => void sendText()}
          disabled={sending || !threadId || !draft.trim()}
          style={{ opacity: sending || !threadId || !draft.trim() ? 0.45 : 1 }}
        >
          <LinearGradient
            colors={["#4f46e5", "#7c3aed"]}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 1 }}
            style={s.sendBtn}
          >
            {sending ? (
              <ActivityIndicator color="#fff" size="small" />
            ) : (
              <Feather name="send" size={16} color="#fff" />
            )}
          </LinearGradient>
        </Pressable>
      </View>
      ) : null}
    </KeyboardAvoidingView>
  );
}

const s = StyleSheet.create({
  root: { flex: 1 },
  heroHeader: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    paddingHorizontal: 12,
    paddingBottom: 14,
  },
  back: { padding: 4 },
  heroTitle: { fontSize: 18, fontWeight: "800", color: "#fff" },
  onlineRow: { flexDirection: "row", alignItems: "center", gap: 6, marginTop: 3 },
  onlineDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: "#4ade80",
  },
  heroSub: { fontSize: 12, color: "rgba(255,255,255,0.85)", fontWeight: "600" },
  trustStrip: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-evenly",
    paddingVertical: 8,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  trustItem: { flexDirection: "row", alignItems: "center", gap: 5 },
  trustTxt: { fontSize: 11, fontWeight: "600" },
  trustDivider: { width: StyleSheet.hairlineWidth, height: 14 },
  tabRow: {
    flexDirection: "row",
    gap: 8,
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  tabBtn: {
    flex: 1,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 6,
    paddingVertical: 9,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: "transparent",
  },
  tabTxt: { fontSize: 13, fontWeight: "700" },
  txList: { padding: 14, gap: 10 },
  txHero: {
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
    padding: 14,
    borderRadius: 14,
    borderWidth: 1,
    marginBottom: 6,
  },
  txHeroTitle: { fontSize: 15, fontWeight: "800" },
  txHeroSub: { fontSize: 11.5, marginTop: 2, lineHeight: 16 },
  txCard: {
    flexDirection: "row",
    alignItems: "flex-start",
    gap: 12,
    padding: 14,
    borderRadius: 14,
    borderWidth: 1,
  },
  txIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: "center",
    justifyContent: "center",
  },
  txTitle: { fontSize: 13.5, fontWeight: "700" },
  txSub: { fontSize: 11.5, fontWeight: "500" },
  txMeta: { fontSize: 10.5, fontWeight: "500" },
  center: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    padding: 32,
    gap: 10,
  },
  emptyTitle: { fontSize: 18, fontWeight: "700", marginTop: 8 },
  emptyBody: { fontSize: 14, textAlign: "center", lineHeight: 20 },
  loginBtn: {
    marginTop: 12,
    paddingHorizontal: 28,
    paddingVertical: 12,
    borderRadius: 12,
  },
  loginBtnTxt: { color: "#fff", fontWeight: "800", fontSize: 15 },
  list: { padding: 14, paddingBottom: 20, flexGrow: 1 },
  welcomeCard: {
    borderWidth: 1,
    borderRadius: 16,
    padding: 14,
    marginBottom: 14,
  },
  welcomeTop: { flexDirection: "row", gap: 12, alignItems: "flex-start" },
  agentBadge: {
    width: 44,
    height: 44,
    borderRadius: 22,
    alignItems: "center",
    justifyContent: "center",
  },
  welcomeTitle: { fontSize: 16, fontWeight: "800" },
  welcomeBody: { fontSize: 13, lineHeight: 19, marginTop: 3 },
  topicChip: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    borderWidth: 1,
    borderRadius: 999,
    paddingHorizontal: 12,
    paddingVertical: 7,
  },
  topicTxt: { fontSize: 12.5, fontWeight: "700" },
  sysWrap: { alignSelf: "center", marginVertical: 6, maxWidth: "90%" },
  sysText: { fontSize: 12, textAlign: "center" },
  supportRow: {
    flexDirection: "row",
    alignItems: "flex-end",
    gap: 8,
    marginBottom: 10,
    alignSelf: "flex-start",
    maxWidth: "90%",
  },
  msgAvatar: {
    width: 26,
    height: 26,
    borderRadius: 13,
    alignItems: "center",
    justifyContent: "center",
    marginBottom: 16,
  },
  bubble: {
    paddingHorizontal: 12,
    paddingVertical: 9,
    borderRadius: 16,
    borderWidth: 1,
  },
  who: { fontSize: 11, marginBottom: 4, fontWeight: "700" },
  msg: { fontSize: 15, lineHeight: 21 },
  img: { width: 200, height: 200, borderRadius: 10, marginTop: 6 },
  time: { fontSize: 10, marginTop: 3, marginHorizontal: 4 },
  inputRow: {
    flexDirection: "row",
    alignItems: "flex-end",
    gap: 8,
    paddingHorizontal: 10,
    paddingTop: 10,
    borderTopWidth: StyleSheet.hairlineWidth,
  },
  iconBtn: { padding: 8, marginBottom: 2 },
  input: {
    flex: 1,
    minHeight: 42,
    maxHeight: 120,
    borderWidth: 1,
    borderRadius: 12,
    paddingHorizontal: 12,
    paddingVertical: 10,
  },
  sendBtn: {
    width: 42,
    height: 42,
    borderRadius: 21,
    alignItems: "center",
    justifyContent: "center",
    marginBottom: 2,
  },
});
