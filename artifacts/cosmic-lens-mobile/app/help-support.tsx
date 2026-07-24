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

type SupportMessage = {
  id: string;
  sender: "user" | "admin" | "system";
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
  { icon: "credit-card" as const, label: "Payment issue" },
  { icon: "file-text" as const, label: "Report / PDF problem" },
  { icon: "star" as const, label: "Consultation query" },
  { icon: "smartphone" as const, label: "App not working" },
  { icon: "user" as const, label: "Account & login" },
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
    async (sid: string) => {
      if (!user?.id || !user?.api_key) return;
      const res = await fetch(
        `${API_BASE}/api/support/thread/${encodeURIComponent(sid)}/messages?user_id=${user.id}`,
        { headers: authHeaders() },
      );
      const json = await res.json().catch(() => ({}) as any);
      if (!res.ok) return;
      setMessages(Array.isArray(json.messages) ? json.messages : []);
      setAdminTyping(Boolean(json.admin_typing));
    },
    [user?.id, user?.api_key, authHeaders],
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

  useEffect(() => {
    if (!threadId) return;
    const poll = setInterval(() => void refresh(threadId), 2500);
    return () => clearInterval(poll);
  }, [threadId, refresh]);

  const sendText = async (forcedText?: string) => {
    const text = (forcedText ?? draft).trim();
    if (!text || !threadId || sending || !user?.id) return;
    setSending(true);
    try {
      const res = await fetch(
        `${API_BASE}/api/support/thread/${encodeURIComponent(threadId)}/message`,
        {
          method: "POST",
          headers: authHeaders(),
          body: JSON.stringify({ user_id: user.id, text }),
        },
      );
      const json = await res.json().catch(() => ({}) as any);
      if (!res.ok) {
        Alert.alert("Send failed", String(json.error || `HTTP ${res.status}`));
        return;
      }
      setDraft("");
      await refresh(threadId);
      requestAnimationFrame(() => listRef.current?.scrollToEnd({ animated: true }));
    } catch (e) {
      Alert.alert("Send failed", e instanceof Error ? e.message : "Network error");
    } finally {
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

  const pickTopic = (label: string) => {
    Haptics.selectionAsync().catch(() => {});
    setDraft(`${label}: `);
    requestAnimationFrame(() => inputRef.current?.focus());
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
            <Text style={s.heroTitle}>Cosmic Care Team</Text>
            <View style={s.onlineRow}>
              <View style={s.onlineDot} />
              <Text style={s.heroSub}>Online · 24×7 priority support</Text>
            </View>
          </View>
          <TeamAvatarCluster />
        </LinearGradient>
        <View style={s.center}>
          <MaterialCommunityIcons name="face-agent" size={48} color={C.accent} />
          <Text style={[s.emptyTitle, { color: C.text }]}>Login required</Text>
          <Text style={[s.emptyBody, { color: C.textMuted }]}>
            Sign in to chat with our support team and send screenshots.
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

  const hasMessages = messages.length > 0;

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
          <Text style={s.heroTitle}>Cosmic Care Team</Text>
          <View style={s.onlineRow}>
            <View style={s.onlineDot} />
            <Text style={s.heroSub}>Online · replies in minutes</Text>
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
          <Text style={[s.trustTxt, { color: C.textMuted }]}>24×7 support</Text>
        </View>
        <View style={[s.trustDivider, { backgroundColor: C.border }]} />
        <View style={s.trustItem}>
          <Feather name="zap" size={13} color={C.accent} />
          <Text style={[s.trustTxt, { color: C.textMuted }]}>Priority replies</Text>
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
            Live chat
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
            Connecting you to the team…
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
                    You&apos;re connected to the Cosmic Care Team. Tell us your issue —
                    a specialist will pick it up right away.
                  </Text>
                </View>
              </View>
              {!hasMessages ? (
                <ScrollView
                  horizontal
                  showsHorizontalScrollIndicator={false}
                  contentContainerStyle={{ gap: 8, paddingTop: 12 }}
                >
                  {QUICK_TOPICS.map((topic) => (
                    <Pressable
                      key={topic.label}
                      onPress={() => pickTopic(topic.label)}
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
            adminTyping ? (
              <View style={s.supportRow}>
                <View style={[s.msgAvatar, { backgroundColor: "#7c3aed" }]}>
                  <MaterialCommunityIcons name="face-agent" size={15} color="#fff" />
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
                  <Text style={[s.who, { color: C.textMuted }]}>Cosmic Care Team</Text>
                  <AcharyaTypingDots caption="Team is typing…" />
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
            return (
              <View style={s.supportRow}>
                <View style={[s.msgAvatar, { backgroundColor: "#7c3aed" }]}>
                  <MaterialCommunityIcons name="face-agent" size={15} color="#fff" />
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
                    <Text style={[s.who, { color: C.accent }]}>Cosmic Care Team</Text>
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
          placeholder="Type your message…"
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
