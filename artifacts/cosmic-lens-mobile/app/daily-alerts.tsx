import { Feather } from "@expo/vector-icons";
import { router } from "expo-router";
import * as Haptics from "expo-haptics";
import React, { useCallback, useEffect, useRef, useState } from "react";
import {
  ActivityIndicator,
  FlatList,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  useWindowDimensions,
  View,
  Animated,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { useC } from "@/context/ThemeContext";
import { useUser, type ProfileEntry } from "@/context/UserContext";
import { computeActiveDasha } from "@/lib/proInsightEngine";

const F = {
  bold:     "Nunito_700Bold",
  semibold: "Nunito_600SemiBold",
  medium:   "Nunito_500Medium",
  regular:  "Nunito_400Regular",
};

const API_BASE = `https://${process.env.EXPO_PUBLIC_DOMAIN ?? ""}`;

// ── Types ────────────────────────────────────────────────────────────────────
interface DayAlert {
  offset: number;
  label: string;
  label_hi: string;
  emoji: string;
  date: string;
  date_display: string;
  weekday: string;
  energy: "Good" | "Neutral" | "Challenging";
  energy_color: string;
  score: number;
  insight_hi: string;
  insight_en: string;
  moon_sign: string;
  moon_sign_hi: string;
  moon_house: number;
  moon_nakshatra: string;
  tara: string;
  saturn_aspect: boolean;
  mars_aspect: boolean;
  jupiter_aspect: boolean;
  tags: string[];
  lucky_color_name: string;
  lucky_color_hex: string;
  lucky_numbers: number[];
  dasha_note: string;
}

// ── Score bar ─────────────────────────────────────────────────────────────────
function ScoreBar({ score, color }: { score: number; color: string }) {
  const anim = useRef(new Animated.Value(0)).current;
  useEffect(() => {
    Animated.timing(anim, {
      toValue: score / 100,
      duration: 700,
      useNativeDriver: false,
    }).start();
  }, [score]);

  const C = useC();
  return (
    <View style={{ height: 4, borderRadius: 2, backgroundColor: C.border, overflow: "hidden", marginTop: 8 }}>
      <Animated.View
        style={{
          height: 4,
          borderRadius: 2,
          backgroundColor: color,
          width: anim.interpolate({ inputRange: [0, 1], outputRange: ["0%", "100%"] }),
        }}
      />
    </View>
  );
}

// ── Energy badge ──────────────────────────────────────────────────────────────
function EnergyBadge({ energy, color }: { energy: string; color: string }) {
  const icon =
    energy === "Good" ? "trending-up" :
    energy === "Challenging" ? "trending-down" : "minus";
  return (
    <View style={[sb.badge, { backgroundColor: color + "22", borderColor: color + "55" }]}>
      <Feather name={icon as any} size={11} color={color} />
      <Text style={[sb.badgeText, { color }]}>{energy}</Text>
    </View>
  );
}
const sb = StyleSheet.create({
  badge: {
    flexDirection: "row", alignItems: "center", gap: 4,
    paddingHorizontal: 8, paddingVertical: 3,
    borderRadius: 10, borderWidth: 1,
  },
  badgeText: { fontFamily: F.semibold, fontSize: 11 },
});

// ── Tag pill ──────────────────────────────────────────────────────────────────
function TagPill({ tag, C }: { tag: string; C: ReturnType<typeof useC> }) {
  return (
    <View style={[tp.pill, { backgroundColor: C.bgCard2, borderColor: C.border }]}>
      <Text style={[tp.txt, { color: C.textMid }]}>{tag}</Text>
    </View>
  );
}
const tp = StyleSheet.create({
  pill: {
    paddingHorizontal: 9, paddingVertical: 3, borderRadius: 10, borderWidth: 1,
  },
  txt: { fontFamily: F.medium, fontSize: 11 },
});

// ── Day Card ──────────────────────────────────────────────────────────────────
function DayCard({
  item,
  cardWidth,
  isToday,
}: {
  item: DayAlert;
  cardWidth: number;
  isToday: boolean;
}) {
  const C = useC();
  const [expanded, setExpanded] = useState(isToday);

  const borderColor = isToday ? item.energy_color + "88" : C.border;
  const glowBg      = isToday ? C.bgCard : C.bgCard2;

  return (
    <Pressable
      style={[
        dc.card,
        {
          width: cardWidth,
          backgroundColor: glowBg,
          borderColor,
          borderWidth: isToday ? 1.5 : 1,
        },
      ]}
      onPress={() => {
        Haptics.selectionAsync();
        setExpanded(e => !e);
      }}
    >
      {/* ── Top row ── */}
      <View style={dc.topRow}>
        <View style={{ flex: 1 }}>
          <View style={{ flexDirection: "row", alignItems: "center", gap: 6 }}>
            <Text style={dc.emoji}>{item.emoji}</Text>
            <View>
              <Text style={[dc.label, { color: C.text }]}>{item.label}</Text>
              <Text style={[dc.labelHi, { color: C.textMuted }]}>{item.label_hi}</Text>
            </View>
          </View>
          <Text style={[dc.dateStr, { color: C.textMuted }]}>
            {item.weekday} · {item.date_display}
          </Text>
        </View>
        <View style={{ alignItems: "flex-end", gap: 4 }}>
          <EnergyBadge energy={item.energy} color={item.energy_color} />
          <Text style={[dc.scoreLabel, { color: C.textMuted }]}>Score {item.score}/100</Text>
        </View>
      </View>

      {/* ── Score bar ── */}
      <ScoreBar score={item.score} color={item.energy_color} />

      {/* ── Moon pill ── */}
      <View style={[dc.moonRow, { backgroundColor: C.bgCard3, borderColor: C.border3 }]}>
        <Text style={dc.moonEmoji}>🌙</Text>
        <Text style={[dc.moonTxt, { color: C.textMid }]}>
          {item.moon_sign_hi} ({item.moon_sign}) · House {item.moon_house} · {item.moon_nakshatra}
        </Text>
      </View>

      {/* ── Insight ── */}
      <Text style={[dc.insightHi, { color: C.text }]}>{item.insight_hi}</Text>
      <Text style={[dc.insightEn, { color: C.textMid }]}>{item.insight_en}</Text>

      {/* ── Tags ── */}
      <View style={dc.tags}>
        {item.tags.map(t => <TagPill key={t} tag={t} C={C} />)}
      </View>

      {/* ── Expanded section ── */}
      {expanded && (
        <View style={[dc.expanded, { borderTopColor: C.border }]}>
          {/* Lucky */}
          <View style={dc.luckyRow}>
            <View style={[dc.luckyItem, { backgroundColor: C.bgCard3, borderColor: C.border3 }]}>
              <Text style={[dc.luckyLabel, { color: C.textMuted }]}>Lucky Color</Text>
              <View style={{ flexDirection: "row", alignItems: "center", gap: 6 }}>
                <View style={{ width: 12, height: 12, borderRadius: 6, backgroundColor: item.lucky_color_hex }} />
                <Text style={[dc.luckyVal, { color: C.text }]}>{item.lucky_color_name}</Text>
              </View>
            </View>
            <View style={[dc.luckyItem, { backgroundColor: C.bgCard3, borderColor: C.border3 }]}>
              <Text style={[dc.luckyLabel, { color: C.textMuted }]}>Lucky Numbers</Text>
              <Text style={[dc.luckyVal, { color: C.text }]}>{item.lucky_numbers.join(" · ")}</Text>
            </View>
          </View>

          {/* Tara + aspects */}
          <View style={dc.detailRow}>
            <Feather name="star" size={12} color={C.textMuted} />
            <Text style={[dc.detailTxt, { color: C.textMuted }]}>
              Tara: <Text style={{ color: C.textMid }}>{item.tara}</Text>
            </Text>
            {item.saturn_aspect && (
              <Text style={[dc.detailTxt, { color: "#ef4444" }]}>⚠ Shani drishti</Text>
            )}
            {item.mars_aspect && (
              <Text style={[dc.detailTxt, { color: "#f97316" }]}>⚠ Mangal drishti</Text>
            )}
            {item.jupiter_aspect && (
              <Text style={[dc.detailTxt, { color: "#22c55e" }]}>✓ Guru drishti</Text>
            )}
          </View>

          {/* Dasha note */}
          {!!item.dasha_note && (
            <View style={[dc.dashaNote, { backgroundColor: C.accentBg, borderColor: C.border2 }]}>
              <Text style={dc.dashaNoteEmoji}>🪐</Text>
              <Text style={[dc.dashaNoteTxt, { color: C.textMid }]}>{item.dasha_note}</Text>
            </View>
          )}
        </View>
      )}

      {/* ── Expand hint ── */}
      <View style={dc.expandHint}>
        <Feather name={expanded ? "chevron-up" : "chevron-down"} size={14} color={C.textMuted} />
      </View>
    </Pressable>
  );
}

const dc = StyleSheet.create({
  card: {
    borderRadius: 18,
    padding: 16,
    marginHorizontal: 8,
  },
  topRow: { flexDirection: "row", alignItems: "flex-start", marginBottom: 2 },
  emoji: { fontSize: 22 },
  label: { fontFamily: F.bold, fontSize: 15 },
  labelHi: { fontFamily: F.medium, fontSize: 11, marginTop: 1 },
  dateStr: { fontFamily: F.regular, fontSize: 11, marginTop: 4 },
  scoreLabel: { fontFamily: F.regular, fontSize: 10 },

  moonRow: {
    flexDirection: "row", alignItems: "center", gap: 6,
    paddingHorizontal: 10, paddingVertical: 5, borderRadius: 10,
    borderWidth: 1, marginTop: 10,
  },
  moonEmoji: { fontSize: 13 },
  moonTxt: { fontFamily: F.medium, fontSize: 11, flex: 1 },

  insightHi: { fontFamily: F.semibold, fontSize: 13, marginTop: 10, lineHeight: 19 },
  insightEn: { fontFamily: F.regular, fontSize: 12, marginTop: 4, lineHeight: 17 },

  tags: { flexDirection: "row", flexWrap: "wrap", gap: 6, marginTop: 10 },

  expanded: { borderTopWidth: 1, marginTop: 12, paddingTop: 12, gap: 8 },

  luckyRow: { flexDirection: "row", gap: 8 },
  luckyItem: {
    flex: 1, borderRadius: 10, borderWidth: 1,
    padding: 10, gap: 4,
  },
  luckyLabel: { fontFamily: F.regular, fontSize: 10 },
  luckyVal:   { fontFamily: F.semibold, fontSize: 13 },

  detailRow: { flexDirection: "row", flexWrap: "wrap", gap: 8, alignItems: "center" },
  detailTxt: { fontFamily: F.regular, fontSize: 11 },

  dashaNote: {
    flexDirection: "row", gap: 8, padding: 10,
    borderRadius: 10, borderWidth: 1, alignItems: "flex-start",
  },
  dashaNoteEmoji: { fontSize: 14 },
  dashaNoteTxt: { fontFamily: F.regular, fontSize: 11, flex: 1, lineHeight: 16 },

  expandHint: { alignItems: "center", marginTop: 8 },
});

// ── Profile pill ──────────────────────────────────────────────────────────────
function ProfilePill({
  profile,
  isSelected,
  onPress,
  C,
}: {
  profile: ProfileEntry;
  isSelected: boolean;
  onPress: () => void;
  C: ReturnType<typeof useC>;
}) {
  return (
    <Pressable
      onPress={onPress}
      style={[
        pp.pill,
        {
          backgroundColor: isSelected ? C.accent + "22" : C.bgCard2,
          borderColor: isSelected ? C.accent : C.border,
        },
      ]}
    >
      <Text style={[pp.name, { color: isSelected ? C.accent : C.textMid }]}>
        {profile.name}
      </Text>
    </Pressable>
  );
}
const pp = StyleSheet.create({
  pill: {
    paddingHorizontal: 12, paddingVertical: 5, borderRadius: 12, borderWidth: 1,
  },
  name: { fontFamily: F.semibold, fontSize: 12 },
});

// ── Empty state ───────────────────────────────────────────────────────────────
function EmptyState({ C }: { C: ReturnType<typeof useC> }) {
  return (
    <View style={[es.wrap, { backgroundColor: C.bgCard, borderColor: C.border }]}>
      <Text style={{ fontSize: 36, marginBottom: 12 }}>🔔</Text>
      <Text style={[es.title, { color: C.text }]}>No Kundli Profile Found</Text>
      <Text style={[es.sub, { color: C.textMuted }]}>
        Please create a Kundli profile first. Daily Alerts reads directly from your birth details.
      </Text>
      <Pressable
        style={[es.btn, { backgroundColor: C.accent }]}
        onPress={() => router.push("/profile-edit")}
      >
        <Text style={[es.btnTxt, { color: "#fff" }]}>Set Up Profile →</Text>
      </Pressable>
    </View>
  );
}
const es = StyleSheet.create({
  wrap: {
    margin: 20, borderRadius: 20, borderWidth: 1,
    padding: 28, alignItems: "center",
  },
  title: { fontFamily: F.bold, fontSize: 17, marginBottom: 8 },
  sub:   { fontFamily: F.regular, fontSize: 13, textAlign: "center", lineHeight: 19, marginBottom: 18 },
  btn:   { paddingHorizontal: 24, paddingVertical: 12, borderRadius: 14 },
  btnTxt:{ fontFamily: F.semibold, fontSize: 14 },
});

// ── Main Screen ───────────────────────────────────────────────────────────────
export default function DailyAlertsScreen() {
  const insets  = useSafeAreaInsets();
  const C       = useC();
  const { width } = useWindowDimensions();
  const { profiles, primaryProfileId } = useUser();

  const proWithKundli = profiles.filter(p => !!p.kundli);
  const primaryFirst  = proWithKundli.sort((a, b) =>
    a.id === primaryProfileId ? -1 : b.id === primaryProfileId ? 1 : 0
  );

  const [selectedId, setSelectedId] = useState<string | null>(
    primaryFirst[0]?.id ?? null
  );
  const [days, setDays]     = useState<DayAlert[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError]   = useState<string | null>(null);
  const flatRef = useRef<FlatList>(null);

  const profile = primaryFirst.find(p => p.id === selectedId) ?? primaryFirst[0] ?? null;

  // Card width — slight peek so user knows there's more
  const CARD_W = Math.min(width - 48, 320);

  const fetchAlerts = useCallback(async (p: ProfileEntry) => {
    const k = p.kundli;
    if (!k) return;

    const moonPlanet = k.planets?.find((p: any) => p.name === "Moon");
    const dasha = computeActiveDasha(k, moonPlanet?.longitude ?? 0);

    setLoading(true);
    setError(null);
    setDays([]);

    try {
      const ctrl = new AbortController();
      const timeout = setTimeout(() => ctrl.abort(), 12000);
      const res = await fetch(`${API_BASE}/api/daily_alerts`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          lagna_deg:  k.ascendantDeg ?? 0,
          nakshatra:  k.nakshatra ?? "",
          mahadasha:  dasha?.mdPlanet ?? "",
          antardasha: dasha?.adPlanet ?? "",
        }),
        signal: ctrl.signal,
      });
      clearTimeout(timeout);
      const json = await res.json();
      if (json.days) setDays(json.days);
      else setError("Failed to generate alerts.");

      // Scroll to Today card (index 1)
      setTimeout(() => {
        flatRef.current?.scrollToIndex({ index: 1, animated: true, viewPosition: 0.5 });
      }, 300);
    } catch (err: any) {
      if (err?.name === "AbortError") setError("Request timed out. Check your connection.");
      else setError("Could not load alerts.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (profile?.kundli) {
      fetchAlerts(profile);
    }
  }, [profile?.id]);

  const todayIndex = days.findIndex(d => d.offset === 0);

  return (
    <View style={[s.container, { backgroundColor: C.bg }]}>
      {/* ── Header ── */}
      <View style={[s.header, { paddingTop: insets.top + 8, borderBottomColor: C.border }]}>
        <Pressable style={s.backBtn} onPress={() => router.back()}>
          <Feather name="arrow-left" size={20} color={C.text} />
        </Pressable>
        <View style={{ flex: 1 }}>
          <Text style={[s.title, { color: C.text }]}>Daily Alerts</Text>
          <Text style={[s.subtitle, { color: C.textMuted }]}>
            दैनिक ग्रह संकेत — Daily Planetary Guidance
          </Text>
        </View>
        <Pressable
          style={[s.refreshBtn, { backgroundColor: C.bgCard2, borderColor: C.border }]}
          onPress={() => profile?.kundli && fetchAlerts(profile)}
        >
          <Feather name="refresh-cw" size={15} color={C.accent} />
        </Pressable>
      </View>

      <ScrollView
        style={{ flex: 1 }}
        showsVerticalScrollIndicator={false}
        contentContainerStyle={{ paddingBottom: insets.bottom + 32 }}
      >
        {proWithKundli.length === 0 ? (
          <EmptyState C={C} />
        ) : (
          <>
            {/* ── Profile switcher ── */}
            {proWithKundli.length > 1 && (
              <ScrollView
                horizontal
                showsHorizontalScrollIndicator={false}
                contentContainerStyle={s.profileScroll}
                style={{ marginTop: 12 }}
              >
                {primaryFirst.map(p => (
                  <ProfilePill
                    key={p.id}
                    profile={p}
                    isSelected={p.id === selectedId}
                    onPress={() => {
                      Haptics.selectionAsync();
                      setSelectedId(p.id);
                    }}
                    C={C}
                  />
                ))}
              </ScrollView>
            )}

            {/* ── Profile info strip ── */}
            {!!profile && (
              <View style={[s.infoStrip, { backgroundColor: C.bgCard, borderColor: C.border }]}>
                <View style={s.infoLeft}>
                  <Text style={[s.infoName, { color: C.text }]}>{profile.name}</Text>
                  <Text style={[s.infoBirth, { color: C.textMuted }]}>
                    {profile.kundli?.moonSign ?? profile.kundli?.nakshatra ?? ""}
                    {" · "}
                    {profile.kundli?.ascendant ?? ""}
                  </Text>
                </View>
                <View style={[s.autoTag, { backgroundColor: C.accentBg, borderColor: C.border2 }]}>
                  <Feather name="zap" size={10} color={C.accent} />
                  <Text style={[s.autoTagTxt, { color: C.accent }]}>Auto-synced</Text>
                </View>
              </View>
            )}

            {/* ── Instructions ── */}
            <Text style={[s.hint, { color: C.textMuted }]}>
              Tap a card to expand details · Swipe left for next day
            </Text>

            {/* ── Cards ── */}
            {loading ? (
              <View style={s.loadWrap}>
                <ActivityIndicator size="large" color={C.accent} />
                <Text style={[s.loadTxt, { color: C.textMuted }]}>
                  Computing planetary transits…
                </Text>
              </View>
            ) : error ? (
              <View style={[s.errorWrap, { backgroundColor: C.bgCard, borderColor: C.border }]}>
                <Text style={[s.errorTxt, { color: "#ef4444" }]}>{error}</Text>
                <Pressable
                  style={[s.retryBtn, { backgroundColor: C.accent }]}
                  onPress={() => profile?.kundli && fetchAlerts(profile)}
                >
                  <Text style={s.retryTxt}>Retry</Text>
                </Pressable>
              </View>
            ) : days.length > 0 ? (
              <FlatList
                ref={flatRef}
                data={days}
                keyExtractor={d => d.date}
                horizontal
                showsHorizontalScrollIndicator={false}
                contentContainerStyle={{ paddingHorizontal: 12, paddingVertical: 4 }}
                snapToInterval={CARD_W + 16}
                decelerationRate="fast"
                renderItem={({ item }) => (
                  <DayCard
                    item={item}
                    cardWidth={CARD_W}
                    isToday={item.offset === 0}
                  />
                )}
                initialScrollIndex={todayIndex >= 0 ? todayIndex : 0}
                getItemLayout={(_, index) => ({
                  length: CARD_W + 16,
                  offset: (CARD_W + 16) * index,
                  index,
                })}
              />
            ) : null}

            {/* ── Legend ── */}
            {days.length > 0 && (
              <View style={[s.legend, { backgroundColor: C.bgCard, borderColor: C.border }]}>
                <Text style={[s.legendTitle, { color: C.textMid }]}>Energy Levels</Text>
                <View style={s.legendRow}>
                  {[
                    { color: "#22c55e", label: "Good" },
                    { color: "#f59e0b", label: "Neutral" },
                    { color: "#ef4444", label: "Challenging" },
                  ].map(({ color, label }) => (
                    <View key={label} style={s.legendItem}>
                      <View style={[s.legendDot, { backgroundColor: color }]} />
                      <Text style={[s.legendTxt, { color: C.textMuted }]}>{label}</Text>
                    </View>
                  ))}
                </View>
                <Text style={[s.legendNote, { color: C.textMuted }]}>
                  Based on Tara chakra, Moon's house transit, Dasha lord, and Saturn/Mars/Jupiter aspects.
                </Text>
              </View>
            )}
          </>
        )}
      </ScrollView>
    </View>
  );
}

const s = StyleSheet.create({
  container: { flex: 1 },

  header: {
    flexDirection: "row", alignItems: "center", gap: 10,
    paddingHorizontal: 16, paddingBottom: 12,
    borderBottomWidth: 1,
  },
  backBtn:    { width: 36, height: 36, alignItems: "center", justifyContent: "center" },
  title:      { fontFamily: F.bold, fontSize: 20 },
  subtitle:   { fontFamily: F.regular, fontSize: 11, marginTop: 1 },
  refreshBtn: {
    width: 36, height: 36, alignItems: "center", justifyContent: "center",
    borderRadius: 10, borderWidth: 1,
  },

  profileScroll: { paddingHorizontal: 16, gap: 8 },

  infoStrip: {
    flexDirection: "row", alignItems: "center",
    marginHorizontal: 16, marginTop: 12,
    borderRadius: 14, borderWidth: 1, padding: 12, gap: 8,
  },
  infoLeft:  { flex: 1 },
  infoName:  { fontFamily: F.semibold, fontSize: 14 },
  infoBirth: { fontFamily: F.regular, fontSize: 11, marginTop: 2 },
  autoTag:   {
    flexDirection: "row", alignItems: "center", gap: 4,
    paddingHorizontal: 8, paddingVertical: 3,
    borderRadius: 8, borderWidth: 1,
  },
  autoTagTxt: { fontFamily: F.semibold, fontSize: 10 },

  hint: {
    fontFamily: F.regular, fontSize: 11,
    textAlign: "center", marginTop: 10, marginBottom: 4,
  },

  loadWrap: { alignItems: "center", paddingVertical: 60, gap: 14 },
  loadTxt:  { fontFamily: F.medium, fontSize: 13 },

  errorWrap: {
    margin: 20, borderRadius: 16, borderWidth: 1,
    padding: 20, alignItems: "center", gap: 14,
  },
  errorTxt: { fontFamily: F.medium, fontSize: 13, textAlign: "center" },
  retryBtn: { paddingHorizontal: 20, paddingVertical: 10, borderRadius: 12 },
  retryTxt: { fontFamily: F.semibold, fontSize: 13, color: "#fff" },

  legend: {
    marginHorizontal: 16, marginTop: 16,
    borderRadius: 14, borderWidth: 1, padding: 14, gap: 8,
  },
  legendTitle: { fontFamily: F.semibold, fontSize: 12 },
  legendRow:   { flexDirection: "row", gap: 16 },
  legendItem:  { flexDirection: "row", alignItems: "center", gap: 5 },
  legendDot:   { width: 8, height: 8, borderRadius: 4 },
  legendTxt:   { fontFamily: F.regular, fontSize: 11 },
  legendNote:  { fontFamily: F.regular, fontSize: 10, lineHeight: 15 },
});
