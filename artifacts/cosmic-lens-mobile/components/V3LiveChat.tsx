import { Feather } from "@expo/vector-icons";
import * as Haptics from "expo-haptics";
import * as ImagePicker from "expo-image-picker";
import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  ActivityIndicator,
  Alert,
  FlatList,
  Image,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { AcharyaTypingDots } from "@/components/AcharyaTypingDots";
import { useC } from "@/context/ThemeContext";
import { API_BASE } from "@/lib/apiConfig";

export type V3ChatMessage = {
  id: string;
  sender: "user" | "admin" | "system";
  text?: string;
  image_url?: string;
  ts: string;
};

type SessionMeta = {
  status?: string;
  expires_at?: string | null;
  remaining_seconds?: number | null;
  label?: string;
  minutes?: number;
};

type Props = {
  sessionId: string;
  userId: number;
  apiKey: string;
  label: string;
  priceInr: number;
  onEnded?: () => void;
};

function mediaSrc(url?: string): string {
  if (!url) return "";
  if (url.startsWith("http") || url.startsWith("data:")) return url;
  return `${API_BASE}${url.startsWith("/") ? "" : "/"}${url}`;
}

function formatTimer(expiresAt?: string | null): string {
  if (!expiresAt) return "--:--";
  const rem = Math.max(0, Math.floor((new Date(expiresAt).getTime() - Date.now()) / 1000));
  const m = Math.floor(rem / 60);
  const s = rem % 60;
  return `${m}:${String(s).padStart(2, "0")}`;
}

export function V3LiveChat({
  sessionId,
  userId,
  apiKey,
  label,
  priceInr,
  onEnded,
}: Props) {
  const C = useC();
  const insets = useSafeAreaInsets();
  const listRef = useRef<FlatList>(null);
  const [messages, setMessages] = useState<V3ChatMessage[]>([]);
  const [session, setSession] = useState<SessionMeta | null>(null);
  const [draft, setDraft] = useState("");
  const [sending, setSending] = useState(false);
  const [ending, setEnding] = useState(false);
  const [confirmEndVisible, setConfirmEndVisible] = useState(false);
  const [tick, setTick] = useState(0);
  const [adminTyping, setAdminTyping] = useState(false);
  const endedRef = useRef(false);

  const authHeaders = useCallback(
    () => ({
      "X-API-Key": apiKey,
      Accept: "application/json",
      "Content-Type": "application/json",
    }),
    [apiKey],
  );

  const refresh = useCallback(async () => {
    try {
      const res = await fetch(
        `${API_BASE}/api/cosmic-intelligence-v3/session/${encodeURIComponent(sessionId)}/messages?user_id=${userId}`,
        { headers: authHeaders() },
      );
      const json = await res.json().catch(() => ({} as any));
      if (!res.ok) return;
      const nextMsgs: V3ChatMessage[] = Array.isArray(json.messages) ? json.messages : [];
      setMessages(nextMsgs);
      // Only show "calculating…" while admin is actively typing — not after
      // every user message, and not while waiting for a reply.
      setAdminTyping(Boolean(json.admin_typing));
      if (json.session) setSession(json.session);
      const st = String(json.session?.status || "");
      if ((st === "ended" || st === "rejected") && !endedRef.current) {
        endedRef.current = true;
        Alert.alert("Time up", "Live session ended. Chat is closed.");
        onEnded?.();
      }
    } catch {
      /* keep polling */
    }
  }, [sessionId, userId, authHeaders, onEnded]);

  useEffect(() => {
    void refresh();
    const poll = setInterval(() => void refresh(), 2000);
    const t = setInterval(() => setTick((n) => n + 1), 1000);
    return () => {
      clearInterval(poll);
      clearInterval(t);
    };
  }, [refresh]);

  useEffect(() => {
    void tick;
    if (!session?.expires_at || endedRef.current) return;
    const rem = Math.floor((new Date(session.expires_at).getTime() - Date.now()) / 1000);
    if (rem <= 0) {
      endedRef.current = true;
      Alert.alert("Time up", "Live session ended. Chat is closed.");
      onEnded?.();
    }
  }, [tick, session?.expires_at, onEnded]);

  const sendText = async () => {
    const text = draft.trim();
    if (!text || sending) return;
    setSending(true);
    try {
      const res = await fetch(
        `${API_BASE}/api/cosmic-intelligence-v3/session/${encodeURIComponent(sessionId)}/message`,
        {
          method: "POST",
          headers: authHeaders(),
          body: JSON.stringify({ user_id: userId, text }),
        },
      );
      const json = await res.json().catch(() => ({} as any));
      if (!res.ok) {
        Alert.alert("Send failed", String(json.error || `HTTP ${res.status}`));
        return;
      }
      setDraft("");
      await refresh();
      requestAnimationFrame(() => listRef.current?.scrollToEnd({ animated: true }));
    } catch (e) {
      Alert.alert("Send failed", e instanceof Error ? e.message : "Network error");
    } finally {
      setSending(false);
    }
  };

  const sendImage = async () => {
    if (sending) return;
    try {
      Haptics.selectionAsync().catch(() => {});
      const perm = await ImagePicker.requestMediaLibraryPermissionsAsync();
      if (!perm.granted) {
        Alert.alert("Permission needed", "Allow photo access to send an image.");
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
        `${API_BASE}/api/cosmic-intelligence-v3/session/${encodeURIComponent(sessionId)}/message`,
        {
          method: "POST",
          headers: authHeaders(),
          body: JSON.stringify({ user_id: userId, data_url: dataUrl, text: "" }),
        },
      );
      const json = await res.json().catch(() => ({} as any));
      if (!res.ok) {
        Alert.alert("Image failed", String(json.error || `HTTP ${res.status}`));
        return;
      }
      await refresh();
      requestAnimationFrame(() => listRef.current?.scrollToEnd({ animated: true }));
    } catch (e) {
      Alert.alert("Image failed", e instanceof Error ? e.message : "Could not send");
    } finally {
      setSending(false);
    }
  };

  const doEndSession = async () => {
    setConfirmEndVisible(false);
    setEnding(true);
    try {
      const res = await fetch(
        `${API_BASE}/api/cosmic-intelligence-v3/session/${encodeURIComponent(sessionId)}/end`,
        {
          method: "POST",
          headers: authHeaders(),
          body: JSON.stringify({ user_id: userId }),
        },
      );
      const json = await res.json().catch(() => ({} as any));
      if (!res.ok) {
        Alert.alert("Could not end", String(json.error || `HTTP ${res.status}`));
        return;
      }
      endedRef.current = true;
      onEnded?.();
    } catch (e) {
      Alert.alert("Could not end", e instanceof Error ? e.message : "Network error");
    } finally {
      setEnding(false);
    }
  };

  const live = (session?.status || "accepted") === "accepted";
  const showCalculating = live && adminTyping;
  const timerColor =
    session?.expires_at && new Date(session.expires_at).getTime() - Date.now() <= 60_000
      ? "#f59e0b"
      : C.accent;

  const listFooter = useMemo(() => {
    if (!showCalculating) return null;
    return (
      <View
        style={[
          styles.bubble,
          styles.calcBubble,
          { alignSelf: "flex-start", backgroundColor: C.bgCard, borderColor: C.border },
        ]}
      >
        <Text style={[styles.who, { color: C.textMuted }]}>Cosmic Intelligence V3</Text>
        <AcharyaTypingDots caption="Cosmic Intelligence calculating…" />
      </View>
    );
  }, [showCalculating, C.bgCard, C.border, C.textMuted]);

  return (
    <KeyboardAvoidingView
      style={[styles.root, { backgroundColor: C.isDark ? "#000" : C.bg }]}
      behavior={Platform.OS === "ios" ? "padding" : undefined}
      keyboardVerticalOffset={0}
    >
      <View style={[styles.header, { paddingTop: insets.top + 8, borderBottomColor: C.border }]}>
        <View style={{ flex: 1 }}>
          <Text style={[styles.title, { color: C.text }]} numberOfLines={1}>
            Cosmic Intelligence V3
          </Text>
          <Text style={[styles.sub, { color: C.textMuted }]} numberOfLines={1}>
            Engine online · {label} · ₹{priceInr.toLocaleString("en-IN")}
          </Text>
        </View>
        <View style={[styles.timerPill, { borderColor: `${timerColor}66`, backgroundColor: `${timerColor}18` }]}>
          <Feather name="clock" size={13} color={timerColor} />
          <Text style={[styles.timerText, { color: timerColor }]}>{formatTimer(session?.expires_at)}</Text>
        </View>
        <Pressable
          onPress={() => {
            Haptics.selectionAsync().catch(() => {});
            setConfirmEndVisible(true);
          }}
          disabled={ending}
          style={[styles.endBtn, { opacity: ending ? 0.55 : 1 }]}
        >
          {ending ? (
            <ActivityIndicator color="#fff" size="small" />
          ) : (
            <Text style={styles.endText}>End</Text>
          )}
        </Pressable>
      </View>

      <FlatList
        ref={listRef}
        data={messages}
        keyExtractor={(m) => m.id}
        contentContainerStyle={styles.list}
        onContentSizeChange={() => listRef.current?.scrollToEnd({ animated: false })}
        ListFooterComponent={listFooter}
        renderItem={({ item }) => {
          const mine = item.sender === "user";
          const sys = item.sender === "system";
          if (sys) {
            return (
              <View style={styles.sysWrap}>
                <Text style={[styles.sysText, { color: C.textMuted }]}>{item.text}</Text>
              </View>
            );
          }
          return (
            <View
              style={[
                styles.bubble,
                mine
                  ? { alignSelf: "flex-end", backgroundColor: `${C.accent}33`, borderColor: `${C.accent}55` }
                  : { alignSelf: "flex-start", backgroundColor: C.bgCard, borderColor: C.border },
              ]}
            >
              <Text style={[styles.who, { color: C.textMuted }]}>
                {mine ? "You" : "Cosmic Intelligence V3"}
              </Text>
              {item.text ? <Text style={[styles.msg, { color: C.text }]}>{item.text}</Text> : null}
              {item.image_url ? (
                <Image
                  source={{ uri: mediaSrc(item.image_url) }}
                  style={styles.img}
                  resizeMode="cover"
                />
              ) : null}
            </View>
          );
        }}
        ListEmptyComponent={
          showCalculating ? null : (
            <Text style={[styles.empty, { color: C.textMuted }]}>
              Engine connected. Cosmic Intelligence V3 will answer soon.
            </Text>
          )
        }
      />

      {confirmEndVisible ? (
        <View style={styles.confirmBackdrop}>
          <View style={[styles.confirmCard, { backgroundColor: C.bgCard, borderColor: C.border }]}>
            <Feather name="alert-triangle" size={22} color="#ef4444" />
            <Text style={[styles.confirmTitle, { color: C.text }]}>
              Are you sure you want to end the chat?
            </Text>
            <Text style={[styles.confirmMsg, { color: C.textMuted }]}>
              You can't go back or enter this chat again after ending it.
            </Text>
            <View style={styles.confirmRow}>
              <Pressable
                onPress={() => setConfirmEndVisible(false)}
                style={[styles.confirmBtn, { borderColor: C.border, borderWidth: 1 }]}
              >
                <Text style={{ color: C.text, fontWeight: "700" }}>Go back</Text>
              </Pressable>
              <Pressable
                onPress={() => void doEndSession()}
                style={[styles.confirmBtn, { backgroundColor: "#dc2626" }]}
              >
                <Text style={{ color: "#fff", fontWeight: "800" }}>End chat</Text>
              </Pressable>
            </View>
          </View>
        </View>
      ) : null}

      <View
        style={[
          styles.inputRow,
          {
            paddingBottom: Math.max(insets.bottom, 10),
            borderTopColor: C.border,
            backgroundColor: C.isDark ? "#0a0a0c" : C.bgCard,
          },
        ]}
      >
        <Pressable
          onPress={() => void sendImage()}
          disabled={!live || sending}
          style={[styles.iconBtn, { opacity: !live || sending ? 0.4 : 1 }]}
        >
          <Feather name="image" size={22} color={C.accent} />
        </Pressable>
        <TextInput
          value={draft}
          onChangeText={setDraft}
          placeholder={live ? "Message Cosmic Intelligence V3…" : "Session ended"}
          placeholderTextColor={C.textMuted}
          editable={live && !sending}
          style={[styles.input, { color: C.text, backgroundColor: C.isDark ? "#141418" : C.bg, borderColor: C.border }]}
          multiline
          maxLength={4000}
        />
        <Pressable
          onPress={() => void sendText()}
          disabled={!live || sending || !draft.trim()}
          style={[
            styles.sendBtn,
            {
              backgroundColor: C.accent,
              opacity: !live || sending || !draft.trim() ? 0.45 : 1,
            },
          ]}
        >
          {sending ? (
            <ActivityIndicator color="#fff" size="small" />
          ) : (
            <Feather name="send" size={16} color="#fff" />
          )}
        </Pressable>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1 },
  header: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    paddingHorizontal: 10,
    paddingBottom: 10,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  title: { fontSize: 16, fontWeight: "700" },
  sub: { fontSize: 12, marginTop: 2 },
  timerPill: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 999,
    borderWidth: 1,
  },
  timerText: { fontSize: 14, fontWeight: "800", fontVariant: ["tabular-nums"] },
  endBtn: {
    minWidth: 48,
    height: 34,
    borderRadius: 9,
    paddingHorizontal: 10,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#dc2626",
  },
  endText: { color: "#fff", fontSize: 13, fontWeight: "800" },
  confirmBackdrop: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: "rgba(0,0,0,0.6)",
    alignItems: "center",
    justifyContent: "center",
    padding: 24,
    zIndex: 50,
  },
  confirmCard: {
    width: "100%",
    borderRadius: 16,
    borderWidth: 1,
    padding: 20,
    alignItems: "center",
    gap: 10,
  },
  confirmTitle: { fontSize: 17, fontWeight: "800" },
  confirmMsg: { fontSize: 13.5, lineHeight: 20, textAlign: "center" },
  confirmRow: { flexDirection: "row", gap: 10, marginTop: 6 },
  confirmBtn: {
    flex: 1,
    height: 44,
    borderRadius: 12,
    alignItems: "center",
    justifyContent: "center",
    paddingHorizontal: 12,
  },
  list: { padding: 14, paddingBottom: 20, flexGrow: 1 },
  empty: { textAlign: "center", marginTop: 40, fontSize: 13, lineHeight: 20 },
  sysWrap: { alignSelf: "center", marginVertical: 6, maxWidth: "90%" },
  sysText: { fontSize: 12, textAlign: "center" },
  bubble: {
    maxWidth: "82%",
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 14,
    borderWidth: 1,
    marginBottom: 8,
  },
  calcBubble: {
    minWidth: 200,
    marginTop: 4,
  },
  who: { fontSize: 11, marginBottom: 4, fontWeight: "600" },
  msg: { fontSize: 15, lineHeight: 21 },
  img: { width: 200, height: 200, borderRadius: 10, marginTop: 6 },
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
    fontSize: 15,
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
