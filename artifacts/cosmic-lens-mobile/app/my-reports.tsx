/**
 * Phase 5 — My Reports
 *
 * Combined history of paid AstroVastu PRO + Business Vastu deep-scans.
 * Each card lets the user reopen the PDF or share it on WhatsApp.
 *
 * Branding: "Powered by Advanced Cosmic Intelligence" — never reveal AI/LLM.
 */
import { Feather } from "@expo/vector-icons";
import { LinearGradient } from "expo-linear-gradient";
import { router, Stack, useFocusEffect } from "expo-router";
import React, { useCallback, useEffect, useState } from "react";
import { useT } from "@/hooks/useT";
import {
  ActivityIndicator,
  FlatList,
  I18nManager,
  Modal,
  Pressable,
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";
import Animated, {
  Easing,
  interpolate,
  useAnimatedStyle,
  useSharedValue,
  withDelay,
  withRepeat,
  withSequence,
  withTiming,
} from "react-native-reanimated";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { useC } from "@/context/ThemeContext";
import { useUser } from "@/context/UserContext";
import { FadeInView, staggerDelay } from "@/components/motion/FadeInView";
import { ScalePressable } from "@/components/motion/ScalePressable";
import {
  formatLocalReportSize,
  listLocalReports,
  openLocalReport,
  shareLocalReport,
  type LocalReport,
} from "@/lib/localReports";
import { syncServerReportsForUser } from "@/lib/serverMyReports";
import { subscribeNewReports } from "@/lib/reportAutoSync";
import { clearUnreadReports } from "@/lib/unreadReportsBadge";
import {
  fetchV3ChatHistory,
  fetchV3ChatTranscript,
  type V3ChatHistoryItem,
  type V3ChatMessage,
} from "@/lib/v3ChatHistory";
import {
  getAskChatArchive,
  listAskChatArchives,
  type AskArchivedChat,
} from "@/lib/askChatArchive";
import { API_BASE } from "@/lib/apiConfig";

type TalkedItem = {
  session_id: string;
  source: "v3" | "ask_v1";
  label: string;
  minutes?: number;
  status?: string;
  talked_at?: string | null;
  message_count: number;
  preview: string;
};

function v3ToTalked(c: V3ChatHistoryItem): TalkedItem {
  return {
    session_id: c.session_id,
    source: "v3",
    label: c.label || "Cosmic Intelligence V3",
    minutes: c.minutes,
    status: c.status,
    talked_at: c.talked_at || c.ended_at || c.started_at || c.created_at,
    message_count: c.message_count,
    preview: c.preview,
  };
}

function askToTalked(c: AskArchivedChat): TalkedItem {
  return {
    session_id: c.session_id,
    source: "ask_v1",
    label: c.label || "Cosmic Intelligence V1",
    talked_at: c.talked_at,
    message_count: c.message_count,
    preview: c.preview,
  };
}

// ── Motion helpers ─────────────────────────────────────────────────────────────
function TwinkleStar({ style, size = 14, delay = 0, color = "#fde68a" }: {
  style?: any; size?: number; delay?: number; color?: string;
}) {
  const p = useSharedValue(0);
  useEffect(() => {
    p.value = withDelay(
      delay,
      withRepeat(
        withTiming(1, { duration: 1700, easing: Easing.inOut(Easing.ease) }),
        -1,
        true,
      ),
    );
  }, [p, delay]);
  const anim = useAnimatedStyle(() => ({
    opacity: interpolate(p.value, [0, 1], [0.12, 0.55]),
    transform: [{ scale: interpolate(p.value, [0, 1], [0.85, 1.15]) }],
  }));
  return (
    <Animated.Text style={[{ position: "absolute", fontSize: size, color }, style, anim]}>
      ✦
    </Animated.Text>
  );
}

/** Diagonal light sweep across the hero banner. */
function HeroSheen() {
  const x = useSharedValue(-1);
  useEffect(() => {
    x.value = withRepeat(
      withSequence(
        withTiming(1.4, { duration: 2400, easing: Easing.inOut(Easing.ease) }),
        withDelay(2000, withTiming(-1, { duration: 0 })),
      ),
      -1,
      false,
    );
  }, [x]);
  const anim = useAnimatedStyle(() => ({
    transform: [
      { translateX: interpolate(x.value, [-1, 1.4], [-260, 420]) },
      { rotate: "18deg" },
    ],
  }));
  return (
    <Animated.View pointerEvents="none" style={[s.sheenBar, anim]}>
      <LinearGradient
        colors={["transparent", "rgba(255,255,255,0.10)", "transparent"]}
        start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }}
        style={{ flex: 1 }}
      />
    </Animated.View>
  );
}

/** Gentle vertical float, used in the empty state. */
function FloatY({ children, range = 7 }: { children: React.ReactNode; range?: number }) {
  const p = useSharedValue(0);
  useEffect(() => {
    p.value = withRepeat(
      withSequence(
        withTiming(1, { duration: 1600, easing: Easing.inOut(Easing.ease) }),
        withTiming(0, { duration: 1600, easing: Easing.inOut(Easing.ease) }),
      ),
      -1,
      false,
    );
  }, [p]);
  const anim = useAnimatedStyle(() => ({
    transform: [{ translateY: interpolate(p.value, [0, 1], [range, -range]) }],
  }));
  return <Animated.View style={anim}>{children}</Animated.View>;
}

// ── Per-kind visual identity ───────────────────────────────────────────────────
const KIND_LABEL: Record<LocalReport["kind"], string> = {
  milan:           "Kundli Milan",
  numerology:      "Numerology",
  astrovastu_pro:  "AstroVastu Pro",
  business_vastu:  "Business Vastu",
  face_reading:    "Face Reading",
  love_reality:    "Love Reality Pro",
  other:           "Report",
};
const KIND_ICON: Record<LocalReport["kind"], React.ComponentProps<typeof Feather>["name"]> = {
  milan:           "heart",
  numerology:      "hash",
  astrovastu_pro:  "home",
  business_vastu:  "briefcase",
  face_reading:    "user",
  love_reality:    "heart",
  other:           "file-text",
};
const KIND_THEME: Record<LocalReport["kind"], { accent: string; grad: [string, string] }> = {
  milan:           { accent: "#ec4899", grad: ["#ec4899", "#a855f7"] },
  numerology:      { accent: "#8b5cf6", grad: ["#8b5cf6", "#6366f1"] },
  astrovastu_pro:  { accent: "#f59e0b", grad: ["#f59e0b", "#ef4444"] },
  business_vastu:  { accent: "#3b82f6", grad: ["#3b82f6", "#06b6d4"] },
  face_reading:    { accent: "#14b8a6", grad: ["#14b8a6", "#22c55e"] },
  love_reality:    { accent: "#f43f5e", grad: ["#f43f5e", "#ec4899"] },
  other:           { accent: "#64748b", grad: ["#64748b", "#475569"] },
};

export default function MyReportsScreen() {
  const insets = useSafeAreaInsets();
  const C = useC();
  const t = useT();
  const { user } = useUser();

  const [section, setSection] = useState<"reports" | "talked">("reports");
  const [localItems, setLocal]  = useState<LocalReport[]>([]);
  const [loading, setLoading]   = useState(false);
  const [refreshing, setRefresh]= useState(false);
  const [chats, setChats] = useState<TalkedItem[]>([]);
  const [chatsLoading, setChatsLoading] = useState(false);
  const [chatsError, setChatsError] = useState<string | null>(null);
  const [openChat, setOpenChat] = useState<TalkedItem | null>(null);
  const [transcript, setTranscript] = useState<V3ChatMessage[]>([]);
  const [transcriptLoading, setTranscriptLoading] = useState(false);

  const loadLocal = useCallback(async (silent = false) => {
    if (!silent) setLoading(true);
    try {
      if (user?.id && user.api_key) {
        await syncServerReportsForUser({ userId: user.id, apiKey: user.api_key });
      }
      setLocal(await listLocalReports());
    } catch { setLocal([]); }
    finally { setLoading(false); setRefresh(false); }
  }, [user?.id, user?.api_key]);

  const loadChats = useCallback(async (silent = false) => {
    if (!user?.id || !user.api_key) {
      setChats([]);
      setChatsError(null);
      return;
    }
    if (!silent) setChatsLoading(true);
    setChatsError(null);
    try {
      let v3Rows: TalkedItem[] = [];
      let v3Err: string | null = null;
      try {
        const rows = await fetchV3ChatHistory({
          userId: user.id,
          apiKey: user.api_key,
        });
        v3Rows = rows.map(v3ToTalked);
      } catch (e) {
        const msg = e instanceof Error ? e.message : "Could not load chats";
        v3Err = /404/.test(msg)
          ? "V3 chat history API abhi server pe deploy nahi hui."
          : msg;
      }
      const askRows = (await listAskChatArchives(user.id)).map(askToTalked);
      const merged = [...askRows, ...v3Rows].sort((a, b) => {
        const ta = a.talked_at ? new Date(a.talked_at).getTime() : 0;
        const tb = b.talked_at ? new Date(b.talked_at).getTime() : 0;
        return tb - ta;
      });
      setChats(merged);
      // Only surface V3 API error when there is nothing local either.
      setChatsError(merged.length === 0 ? v3Err : null);
    } catch (e) {
      setChats([]);
      setChatsError(e instanceof Error ? e.message : "Could not load chats");
    } finally {
      setChatsLoading(false);
      setRefresh(false);
    }
  }, [user?.id, user?.api_key]);

  useFocusEffect(useCallback(() => {
    void clearUnreadReports();
    loadLocal();
    loadChats(true);
  }, [loadLocal, loadChats]));

  useEffect(() => {
    return subscribeNewReports((added) => {
      if (added <= 0) return;
      void clearUnreadReports();
      void listLocalReports().then(setLocal);
    });
  }, []);

  const openTalkedChat = async (chat: TalkedItem) => {
    if (!user?.id || !user.api_key) return;
    setOpenChat(chat);
    setTranscript([]);
    setTranscriptLoading(true);
    try {
      if (chat.source === "ask_v1") {
        const archived = await getAskChatArchive(user.id, chat.session_id);
        const msgs = (archived?.messages || []).map((m) => ({
          id: m.id,
          sender: m.sender === "assistant" ? "admin" : m.sender,
          text: m.text,
          ts: m.ts,
        }));
        setTranscript(
          msgs.filter(
            (m) =>
              m &&
              (m.sender === "user" || m.sender === "admin" || m.sender === "system") &&
              String(m.text || "").trim(),
          ),
        );
      } else {
        const msgs = await fetchV3ChatTranscript({
          userId: user.id,
          apiKey: user.api_key,
          sessionId: chat.session_id,
        });
        setTranscript(
          msgs.filter(
            (m) =>
              m &&
              (m.sender === "user" || m.sender === "admin" || m.sender === "system") &&
              (String(m.text || "").trim() || String(m.image_url || "").trim()),
          ),
        );
      }
    } catch {
      setTranscript([]);
    } finally {
      setTranscriptLoading(false);
    }
  };

  const onOpenLocal = async (r: LocalReport) => {
    await openLocalReport(r);
  };
  const onShareLocal = async (r: LocalReport) => {
    await shareLocalReport(r);
  };

  const renderLocalCard = (r: LocalReport, index: number) => {
    const theme = KIND_THEME[r.kind] ?? KIND_THEME.other;
    const created = new Date(r.createdAt);
    const date = created.toLocaleDateString("en-IN", {
      day: "numeric", month: "short", year: "numeric",
    });
    const time = created.toLocaleTimeString("en-IN", {
      hour: "numeric", minute: "2-digit", hour12: true,
    });
    const sizeLabel = formatLocalReportSize(r.bytes);
    return (
      <FadeInView delay={staggerDelay(index + 1)}>
      <View
        key={r.id}
        style={[
          s.card,
          {
            backgroundColor: C.isDark ? "#0e1318" : "#ffffff",
            borderColor: C.border,
            marginBottom: 14,
          },
        ]}
      >
        {/* Accent edge */}
        <LinearGradient
          colors={theme.grad}
          start={{ x: 0, y: 0 }} end={{ x: 0, y: 1 }}
          style={s.cardEdge}
        />

        <View style={s.cardTop}>
          <LinearGradient
            colors={theme.grad}
            start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }}
            style={s.iconTile}
          >
            <Feather name={KIND_ICON[r.kind]} size={24} color="#fff" />
          </LinearGradient>

          <View style={s.cardMeta}>
            <View style={s.kindRow}>
              <View style={[s.kindChip, { backgroundColor: `${theme.accent}18`, borderColor: `${theme.accent}45` }]}>
                <Text style={[s.kindChipText, { color: theme.accent }]}>
                  {KIND_LABEL[r.kind].toUpperCase()}
                </Text>
              </View>
              <View style={[s.pdfChip, { backgroundColor: C.isDark ? "rgba(255,255,255,0.06)" : "#f1f5f9" }]}>
                <Feather name="file" size={9} color={C.textMuted} />
                <Text style={[s.pdfChipText, { color: C.textMuted }]}>PDF</Text>
              </View>
            </View>
            <Text style={[s.propName, { color: C.text }]} numberOfLines={2}>
              {r.title}
            </Text>
            <View style={s.metaRow}>
              <Feather name="calendar" size={10} color={C.textMuted} />
              <Text style={[s.subMeta, { color: C.textMuted }]} numberOfLines={1}>
                {date} · {time}{sizeLabel ? ` · ${sizeLabel}` : ""}
              </Text>
            </View>
          </View>
        </View>

        <View style={s.btnRow}>
          <View style={{ flex: 1 }}>
            <ScalePressable
              haptic="medium"
              onPress={() => onOpenLocal(r)}
              style={[
                s.actionBtn,
                { backgroundColor: C.isDark ? "#1a2330" : "#eef3fb", borderColor: C.border },
              ]}
            >
              <Feather name="book-open" size={15} color={C.text} />
              <Text style={[s.actionText, { color: C.text }]}>Open</Text>
            </ScalePressable>
          </View>
          <View style={{ flex: 1 }}>
            <ScalePressable
              haptic="medium"
              onPress={() => onShareLocal(r)}
              style={[s.actionBtn, { backgroundColor: "#25D366", borderColor: "#1ebe5b" }]}
            >
              <Feather name="share-2" size={15} color="#ffffff" />
              <Text style={[s.actionText, { color: "#ffffff" }]}>Share</Text>
            </ScalePressable>
          </View>
        </View>
      </View>
      </FadeInView>
    );
  };

  return (
    <View style={[s.root, { backgroundColor: C.isDark ? "#050709" : C.bg }]}>
      <Stack.Screen options={{ headerShown: false }} />
      {C.isDark && (
        <LinearGradient
          colors={["#050709", "#0a0e14", "#0e1722"]}
          locations={[0, 0.55, 1]}
          style={StyleSheet.absoluteFill}
          pointerEvents="none"
        />
      )}

      {/* Nav row */}
      <View
        style={[
          s.header,
          { paddingTop: insets.top + 8, borderBottomColor: C.border },
        ]}
      >
        <Pressable onPress={() => router.back()} style={s.back} hitSlop={10}>
          <Feather name={I18nManager.isRTL ? "arrow-right" : "arrow-left"} size={20} color={C.textMuted} />
        </Pressable>
        <Text style={[s.title, { color: C.text }]}>{t.mr_pageTitle}</Text>
        <View style={s.headerSpacer} />
      </View>

      <View style={[s.segWrap, { borderBottomColor: C.border }]}>
        <Pressable
          onPress={() => setSection("reports")}
          style={[
            s.segBtn,
            section === "reports" && {
              backgroundColor: C.isDark ? "#1e1b4b" : "#ede9fe",
              borderColor: C.isDark ? "#7c3aed" : "#c4b5fd",
            },
          ]}
        >
          <Feather
            name="file-text"
            size={14}
            color={section === "reports" ? "#a78bfa" : C.textMuted}
          />
          <Text
            style={[
              s.segTxt,
              { color: section === "reports" ? C.text : C.textMuted },
            ]}
          >
            Reports
          </Text>
        </Pressable>
        <Pressable
          onPress={() => {
            setSection("talked");
            void loadChats(true);
          }}
          style={[
            s.segBtn,
            section === "talked" && {
              backgroundColor: C.isDark ? "#1e1b4b" : "#ede9fe",
              borderColor: C.isDark ? "#7c3aed" : "#c4b5fd",
            },
          ]}
        >
          <Feather
            name="message-circle"
            size={14}
            color={section === "talked" ? "#a78bfa" : C.textMuted}
          />
          <Text
            style={[
              s.segTxt,
              { color: section === "talked" ? C.text : C.textMuted },
            ]}
          >
            Last talked
          </Text>
          {chats.length > 0 ? (
            <View style={s.segBadge}>
              <Text style={s.segBadgeTxt}>{chats.length}</Text>
            </View>
          ) : null}
        </Pressable>
      </View>

      {section === "talked" ? (
        chatsLoading && chats.length === 0 ? (
          <View style={s.center}>
            <ActivityIndicator size="large" color={C.accent || "#f6c453"} />
          </View>
        ) : chats.length === 0 ? (
          <View style={s.center}>
            <FloatY>
              <LinearGradient
                colors={C.isDark ? ["#1e293b", "#0f172a"] : ["#ede9fe", "#e0e7ff"]}
                style={s.emptyOrb}
              >
                <Feather name="message-circle" size={40} color={C.isDark ? "#94a3b8" : "#7c3aed"} />
              </LinearGradient>
            </FloatY>
            <Text style={[s.empty, { color: C.text }]}>
              {chatsError ? "Couldn’t load chats" : "No chats yet"}
            </Text>
            <Text style={[s.muted, { color: C.textMuted, textAlign: "center", marginTop: 6 }]}>
              {chatsError ||
                "V1 Ask pack khatam hone pe chat yahan save hogi · V3 live sessions bhi yahan dikhenge."}
            </Text>
            {chatsError ? (
              <Pressable
                onPress={() => void loadChats()}
                style={{ marginTop: 16, paddingVertical: 10, paddingHorizontal: 18 }}
              >
                <Text style={{ color: "#a78bfa", fontWeight: "700" }}>Retry</Text>
              </Pressable>
            ) : null}
          </View>
        ) : (
          <FlatList
            data={chats}
            keyExtractor={(c) => c.session_id}
            contentContainerStyle={{ padding: 16, paddingBottom: insets.bottom + 32 }}
            refreshControl={
              <RefreshControl
                refreshing={refreshing}
                onRefresh={() => {
                  setRefresh(true);
                  loadChats(true);
                }}
                tintColor={C.textMuted}
              />
            }
            ListHeaderComponent={
              <Text style={[s.talkedHint, { color: C.textMuted }]}>
                Past V1 Ask + V3 live chats — tap to re-read what was discussed.
              </Text>
            }
            renderItem={({ item, index }) => {
              const when = item.talked_at ? new Date(item.talked_at) : null;
              const date = when
                ? when.toLocaleDateString("en-IN", {
                    day: "numeric",
                    month: "short",
                    year: "numeric",
                  })
                : "—";
              const time = when
                ? when.toLocaleTimeString("en-IN", {
                    hour: "numeric",
                    minute: "2-digit",
                    hour12: true,
                  })
                : "";
              const isAsk = item.source === "ask_v1";
              const edge = (isAsk
                ? ["#3b82f6", "#06b6d4"]
                : ["#7c3aed", "#ec4899"]) as [string, string];
              return (
                <FadeInView delay={staggerDelay(index)}>
                  <Pressable
                    onPress={() => void openTalkedChat(item)}
                    style={[
                      s.card,
                      {
                        backgroundColor: C.isDark ? "#0e1318" : "#ffffff",
                        borderColor: C.border,
                        marginBottom: 12,
                      },
                    ]}
                  >
                    <LinearGradient
                      colors={edge}
                      start={{ x: 0, y: 0 }}
                      end={{ x: 0, y: 1 }}
                      style={s.cardEdge}
                    />
                    <View style={s.cardTop}>
                      <LinearGradient
                        colors={edge}
                        start={{ x: 0, y: 0 }}
                        end={{ x: 1, y: 1 }}
                        style={s.iconTile}
                      >
                        <Feather name="message-circle" size={24} color="#fff" />
                      </LinearGradient>
                      <View style={s.cardMeta}>
                        <View style={s.kindRow}>
                          <View
                            style={[
                              s.kindChip,
                              {
                                backgroundColor: isAsk ? "#3b82f618" : "#7c3aed18",
                                borderColor: isAsk ? "#3b82f645" : "#7c3aed45",
                              },
                            ]}
                          >
                            <Text
                              style={[
                                s.kindChipText,
                                { color: isAsk ? "#38bdf8" : "#a78bfa" },
                              ]}
                            >
                              {isAsk ? "ASK V1" : "LIVE V3"}
                            </Text>
                          </View>
                          <Text style={[s.subMeta, { color: C.textMuted }]}>
                            {item.minutes ? `${item.minutes} min · ` : ""}
                            {item.message_count} msgs
                          </Text>
                        </View>
                        <Text style={[s.propName, { color: C.text }]} numberOfLines={1}>
                          {item.label || (isAsk ? "Cosmic Intelligence V1" : "Live consultation")}
                        </Text>
                        <Text style={[s.subMeta, { color: C.textMuted, marginTop: 4 }]} numberOfLines={2}>
                          {item.preview || "Tap to open chat"}
                        </Text>
                        <View style={s.metaRow}>
                          <Feather name="calendar" size={10} color={C.textMuted} />
                          <Text style={[s.subMeta, { color: C.textMuted }]}>
                            {date}
                            {time ? ` · ${time}` : ""}
                          </Text>
                        </View>
                      </View>
                      <Feather name="chevron-right" size={18} color={C.textMuted} />
                    </View>
                  </Pressable>
                </FadeInView>
              );
            }}
          />
        )
      ) : loading && localItems.length === 0 ? (
        <View style={s.center}>
          <ActivityIndicator size="large" color={C.accent || "#f6c453"} />
          <Text style={[s.muted, { color: C.textMuted, marginTop: 12 }]}>
            {t.mr_loading}
          </Text>
        </View>
      ) : localItems.length === 0 ? (
        <View style={s.center}>
          <FloatY>
            <LinearGradient
              colors={C.isDark ? ["#1e293b", "#0f172a"] : ["#ede9fe", "#e0e7ff"]}
              style={s.emptyOrb}
            >
              <Feather name="inbox" size={40} color={C.isDark ? "#94a3b8" : "#7c3aed"} />
            </LinearGradient>
          </FloatY>
          <Text style={[s.empty, { color: C.text }]}>{t.mr_emptyTitle}</Text>
          <Text style={[s.muted, { color: C.textMuted, textAlign: "center", marginTop: 6 }]}>
            Report deliver hote hi notification aayegi aur yahan auto-save hogi.
          </Text>
        </View>
      ) : (
        <FlatList
          data={localItems}
          keyExtractor={(r) => r.id}
          renderItem={({ item, index }) => renderLocalCard(item, index)}
          contentContainerStyle={{ padding: 16, paddingBottom: insets.bottom + 32 }}
          ItemSeparatorComponent={() => <View style={{ height: 0 }} />}
          ListHeaderComponent={
            <FadeInView delay={staggerDelay(0)}>
              <LinearGradient
                colors={
                  C.isDark
                    ? ["#0b1026", "#1a1033", "#0a1628"]
                    : ["#4c1d95", "#6d28d9", "#3b0764"]
                }
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 1 }}
                style={s.hero}
              >
                <HeroSheen />
                <TwinkleStar style={{ left: 16, top: 12 }} size={16} delay={0} />
                <TwinkleStar style={{ right: 22, top: 20 }} size={11} delay={700} />
                <TwinkleStar style={{ right: 56, bottom: 12 }} size={13} delay={300} color="#c4b5fd" />

                <View style={s.heroIconWrap}>
                  <Feather name="award" size={20} color="#fde68a" />
                </View>
                <View style={{ flex: 1, minWidth: 0 }}>
                  <Text style={s.heroTitle}>Your Cosmic Library</Text>
                  <Text style={s.heroSub}>
                    Personal reports · saved on this device · share anytime
                  </Text>
                </View>
                <View style={s.countBadge}>
                  <Text style={s.countBadgeNum}>{localItems.length}</Text>
                  <Text style={s.countBadgeLbl}>SAVED</Text>
                </View>
              </LinearGradient>
            </FadeInView>
          }
          refreshControl={
            <RefreshControl
              refreshing={refreshing}
              onRefresh={() => { setRefresh(true); loadLocal(true); }}
              tintColor={C.textMuted}
            />
          }
          ListFooterComponent={
            <View style={s.footerRow}>
              <Feather name="shield" size={11} color={C.textMuted} />
              <Text style={[s.footer, { color: C.textMuted }]}>
                {t.mr_footer}
              </Text>
            </View>
          }
        />
      )}

      <Modal
        visible={!!openChat}
        animationType="slide"
        onRequestClose={() => setOpenChat(null)}
      >
        <View style={[s.root, { backgroundColor: C.isDark ? "#050709" : C.bg, paddingTop: insets.top }]}>
          <View style={[s.header, { borderBottomColor: C.border }]}>
            <Pressable onPress={() => setOpenChat(null)} style={s.back} hitSlop={10}>
              <Feather name={I18nManager.isRTL ? "arrow-right" : "arrow-left"} size={20} color={C.textMuted} />
            </Pressable>
            <View style={{ flex: 1, minWidth: 0 }}>
              <Text style={[s.title, { color: C.text }]} numberOfLines={1}>
                {openChat?.label || "Last talked"}
              </Text>
              <Text style={[s.subMeta, { color: C.textMuted }]}>
                Read-only · {openChat?.message_count || 0} messages
              </Text>
            </View>
            <View style={s.headerSpacer} />
          </View>
          {transcriptLoading ? (
            <View style={s.center}>
              <ActivityIndicator size="large" color={C.accent || "#f6c453"} />
            </View>
          ) : (
            <ScrollView
              contentContainerStyle={{
                padding: 16,
                paddingBottom: insets.bottom + 24,
                gap: 10,
              }}
            >
              {transcript.length === 0 ? (
                <Text style={[s.muted, { color: C.textMuted, textAlign: "center", marginTop: 40 }]}>
                  No messages in this session.
                </Text>
              ) : (
                transcript.map((m, i) => {
                  const isUser = m.sender === "user";
                  const isAdmin = m.sender === "admin";
                  const isSystem = m.sender === "system";
                  const img = m.image_url
                    ? m.image_url.startsWith("http")
                      ? m.image_url
                      : `${API_BASE}${m.image_url}`
                    : "";
                  return (
                    <View
                      key={m.id || `${m.ts}-${i}`}
                      style={[
                        s.bubble,
                        isSystem
                          ? s.bubbleSystem
                          : isUser
                            ? [s.bubbleUser, { backgroundColor: "#7c3aed" }]
                            : [
                                s.bubbleAdmin,
                                {
                                  backgroundColor: C.isDark ? "#1a2330" : "#f1f5f9",
                                  borderColor: C.border,
                                },
                              ],
                      ]}
                    >
                      {!isSystem ? (
                        <Text
                          style={[
                            s.bubbleWho,
                            { color: isUser ? "rgba(255,255,255,0.7)" : C.textMuted },
                          ]}
                        >
                          {isUser ? "You" : openChat?.source === "ask_v1" ? "Cosmo" : "Cosmic Guide"}
                        </Text>
                      ) : null}
                      {m.text ? (
                        <Text
                          style={[
                            s.bubbleText,
                            {
                              color: isUser
                                ? "#fff"
                                : isSystem
                                  ? C.textMuted
                                  : C.text,
                            },
                          ]}
                        >
                          {m.text}
                        </Text>
                      ) : null}
                      {img ? (
                        <Text
                          style={[
                            s.bubbleText,
                            { color: isUser ? "#fff" : C.text, marginTop: 4 },
                          ]}
                        >
                          📷 Photo shared
                        </Text>
                      ) : null}
                    </View>
                  );
                })
              )}
            </ScrollView>
          )}
        </View>
      </Modal>
    </View>
  );
}

const s = StyleSheet.create({
  root:    { flex: 1 },
  header:  {
    flexDirection: "row", alignItems: "center", justifyContent: "space-between",
    paddingHorizontal: 16, paddingBottom: 12, borderBottomWidth: StyleSheet.hairlineWidth,
  },
  back:    { padding: 4 },
  title:   { fontSize: 17, fontWeight: "700", letterSpacing: 0.2 },
  headerSpacer: { width: 28 },
  segWrap: {
    flexDirection: "row",
    gap: 8,
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  segBtn: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 999,
    borderWidth: 1,
    borderColor: "transparent",
  },
  segTxt: { fontSize: 13, fontWeight: "700" },
  segBadge: {
    minWidth: 18,
    height: 18,
    borderRadius: 9,
    paddingHorizontal: 5,
    backgroundColor: "#7c3aed",
    alignItems: "center",
    justifyContent: "center",
  },
  segBadgeTxt: { color: "#fff", fontSize: 10, fontWeight: "800" },
  talkedHint: {
    fontSize: 12,
    marginBottom: 12,
    lineHeight: 17,
  },
  bubble: {
    maxWidth: "88%",
    borderRadius: 14,
    paddingHorizontal: 12,
    paddingVertical: 9,
  },
  bubbleUser: { alignSelf: "flex-end" },
  bubbleAdmin: { alignSelf: "flex-start", borderWidth: 1 },
  bubbleSystem: {
    alignSelf: "center",
    backgroundColor: "transparent",
    maxWidth: "94%",
  },
  bubbleWho: { fontSize: 10, fontWeight: "700", marginBottom: 3, letterSpacing: 0.3 },
  bubbleText: { fontSize: 14, lineHeight: 20, fontWeight: "500" },
  center:  { flex: 1, alignItems: "center", justifyContent: "center", padding: 32 },
  muted:   { fontSize: 14 },
  empty:   { fontSize: 18, fontWeight: "700", marginTop: 18 },
  emptyOrb: {
    width: 96, height: 96, borderRadius: 48,
    alignItems: "center", justifyContent: "center",
  },

  // Hero banner
  hero: {
    flexDirection: "row", alignItems: "center", gap: 12,
    borderRadius: 18, padding: 16, marginBottom: 16,
    overflow: "hidden",
  },
  sheenBar: {
    position: "absolute", top: -40, bottom: -40, width: 80,
  },
  heroIconWrap: {
    width: 42, height: 42, borderRadius: 13,
    backgroundColor: "rgba(255,255,255,0.12)",
    borderWidth: 1, borderColor: "rgba(255,255,255,0.18)",
    alignItems: "center", justifyContent: "center",
  },
  heroTitle: { color: "#fff", fontSize: 16.5, fontWeight: "800", letterSpacing: -0.2 },
  heroSub:   { color: "rgba(255,255,255,0.72)", fontSize: 11, marginTop: 3 },
  countBadge: {
    backgroundColor: "rgba(0,0,0,0.3)",
    borderWidth: 1, borderColor: "rgba(255,255,255,0.16)",
    borderRadius: 12, paddingVertical: 6, paddingHorizontal: 12,
    alignItems: "center",
  },
  countBadgeNum: { color: "#fde68a", fontSize: 17, fontWeight: "800", lineHeight: 20 },
  countBadgeLbl: { color: "rgba(255,255,255,0.6)", fontSize: 8, fontWeight: "700", letterSpacing: 1.2 },

  // Report card
  card: {
    borderRadius: 16, borderWidth: 1, padding: 14, paddingLeft: 18,
    overflow: "hidden",
  },
  cardEdge: {
    position: "absolute", left: 0, top: 0, bottom: 0, width: 4,
  },
  cardTop: { flexDirection: "row", alignItems: "center", gap: 13 },
  iconTile: {
    width: 56, height: 56, borderRadius: 15,
    alignItems: "center", justifyContent: "center",
  },

  cardMeta:  { flex: 1, minWidth: 0 },
  kindRow:   { flexDirection: "row", alignItems: "center", gap: 6, flexWrap: "wrap" },
  kindChip:  {
    borderWidth: 1, borderRadius: 6,
    paddingVertical: 2, paddingHorizontal: 7,
  },
  kindChipText: { fontSize: 9, fontWeight: "800", letterSpacing: 0.6 },
  pdfChip: {
    flexDirection: "row", alignItems: "center", gap: 3,
    borderRadius: 6, paddingVertical: 2, paddingHorizontal: 6,
  },
  pdfChipText: { fontSize: 9, fontWeight: "700", letterSpacing: 0.4 },
  propName:  { fontSize: 15.5, fontWeight: "700", marginTop: 6 },
  metaRow:   { flexDirection: "row", alignItems: "center", gap: 5, marginTop: 5 },
  subMeta:   { fontSize: 11.5, flexShrink: 1 },

  btnRow:    { flexDirection: "row", gap: 10, marginTop: 14 },
  actionBtn: {
    flexDirection: "row", alignItems: "center", justifyContent: "center",
    gap: 8, paddingVertical: 11, borderRadius: 12, borderWidth: 1,
  },
  actionText:{ fontSize: 14, fontWeight: "700" },

  footerRow: {
    flexDirection: "row", alignItems: "center", justifyContent: "center",
    gap: 6, marginTop: 24,
  },
  footer:  { textAlign: "center", fontSize: 11, letterSpacing: 0.4 },
});
