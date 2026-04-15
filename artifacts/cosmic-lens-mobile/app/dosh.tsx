import { Feather } from "@expo/vector-icons";
import { router } from "expo-router";
import * as Haptics from "expo-haptics";
import React, { useEffect, useState } from "react";
import {
  ActivityIndicator,
  Animated,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useC } from "@/context/ThemeContext";
import { useUser } from "@/context/UserContext";
import type { DoshItem } from "@/context/UserContext";
import Svg, { Circle } from "react-native-svg";

// ── Status config ─────────────────────────────────────────────────────────────
const STATUS_CONFIG = {
  Active: { color: "#ef4444", bg: "rgba(239,68,68,0.12)",   dot: "#ef4444", label: "Active",  emoji: "🔴" },
  Mild:   { color: "#f97316", bg: "rgba(249,115,22,0.10)",  dot: "#f97316", label: "Mild",    emoji: "🟠" },
  None:   { color: "#22c55e", bg: "rgba(34,197,94,0.08)",   dot: "#22c55e", label: "Clear",   emoji: "🟢" },
};

// ── Demo data (9 doshas) shown when no kundli ─────────────────────────────────
const DEMO_DOSH_LIST: DoshItem[] = [
  { key:"manglik",      name:"Manglik Dosh",      name_hindi:"मांगलिक दोष",     icon:"🔴", status:"Active", headline:"Mars in 4th House — Strong Manglik Dosh",                    description:"Mars in houses 1, 4, 7, 8, or 12 creates Manglik Dosh, strongly affecting marriage and relationships.",                        remedies:["Perform Kumbh Vivah before marriage","Offer sindoor to Hanuman ji on Tuesdays","Wear or keep a Mangal Yantra at home"],         planet_note:"Mars → House 4" },
  { key:"kaal_sarp",    name:"Kaal Sarp Dosh",    name_hindi:"कालसर्प दोष",     icon:"🐍", status:"Mild",   headline:"Partial Kaal Sarp — Some Planets Outside Arc",               description:"Some planets lie outside the Rahu–Ketu arc. Partial effects like occasional obstacles and delays.",                             remedies:["Perform Kaal Sarp Pooja at Trimbakeshwar","Chant Mahamrityunjay mantra 108 times daily"],                                         planet_note:"Rahu → House 11 | Ketu → House 5" },
  { key:"pitru",        name:"Pitru Dosh",        name_hindi:"पितृ दोष",         icon:"👣", status:"None",   headline:"No Pitru Dosh — Ancestors at Peace",                         description:"Sun is free from Rahu/Ketu conjunction. No Pitru Dosh detected.",                                                              remedies:[],                                                                                                                                 planet_note:"Sun → House 11" },
  { key:"guru_chandal", name:"Guru Chandal Dosh", name_hindi:"गुरु चांडाल दोष", icon:"🪐", status:"None",   headline:"No Guru Chandal Dosh — Jupiter Unafflicted",                 description:"Jupiter is free from Rahu/Ketu influence. Wisdom and dharma are clear.",                                                       remedies:[],                                                                                                                                 planet_note:"Jupiter → House 10" },
  { key:"grahan",       name:"Grahan Dosh",       name_hindi:"ग्रहण दोष",        icon:"🌑", status:"None",   headline:"No Grahan Dosh — Luminaries Clear",                          description:"Sun and Moon are free from Rahu/Ketu nodal affliction. No Grahan Dosh.",                                                       remedies:[],                                                                                                                                 planet_note:"Sun → House 11 | Moon → House 11" },
  { key:"daridra",      name:"Daridra Dosh",      name_hindi:"दरिद्र दोष",       icon:"💰", status:"Mild",   headline:"Venus in Dusthana (House 12) — Mild Daridra",                description:"Venus in the 12th house (dusthana) creates mild financial constraints and luxury deprivation.",                                  remedies:["Worship Goddess Lakshmi on Fridays","Recite Kanakdhara Stotra"],                                                                  planet_note:"Venus → House 12" },
  { key:"angarak",      name:"Angarak Dosh",      name_hindi:"अंगारक दोष",       icon:"🔥", status:"None",   headline:"No Angarak Dosh — Mars–Rahu Well Separated",                 description:"Mars and Rahu are in separate positions. No Angarak Dosh.",                                                                    remedies:[],                                                                                                                                 planet_note:"Mars → House 4 | Rahu → House 11" },
  { key:"shrapit",      name:"Shrapit Dosh",      name_hindi:"श्रापित दोष",      icon:"⛓",  status:"None",   headline:"No Shrapit Dosh — Saturn–Rahu Separated",                    description:"Saturn and Rahu are well-separated in the chart. No Shrapit Dosh.",                                                             remedies:[],                                                                                                                                 planet_note:"Saturn → House 7 | Rahu → House 11" },
  { key:"kemadruma",    name:"Kemadruma Dosh",    name_hindi:"केमद्रुम दोष",     icon:"🌙", status:"Active", headline:"Moon Isolated in House 11 — Kemadruma Dosh",                  description:"No planets occupy houses adjacent to Moon (2nd and 12th). Creates emotional isolation and feeling unsupported.",               remedies:["Worship Lord Shiva on Mondays","Chant Chandra mantra 108×","Keep white flowers at home"],                                         planet_note:"Moon → House 11 | H10: empty | H12: empty" },
];

// ── Pulse animation ───────────────────────────────────────────────────────────
function usePulse(active: boolean) {
  const anim = React.useRef(new Animated.Value(1)).current;
  useEffect(() => {
    if (!active) return;
    const loop = Animated.loop(Animated.sequence([
      Animated.timing(anim, { toValue: 1.6, duration: 700, useNativeDriver: true }),
      Animated.timing(anim, { toValue: 1,   duration: 700, useNativeDriver: true }),
    ]));
    loop.start();
    return () => loop.stop();
  }, [active]);
  return anim;
}

// ── Single Dosh Card ──────────────────────────────────────────────────────────
function DoshCard({ item, defaultOpen }: { item: DoshItem; defaultOpen?: boolean }) {
  const [open, setOpen] = useState(defaultOpen ?? false);
  const C = useC();
  const cfg = STATUS_CONFIG[item.status];
  const pulse = usePulse(item.status === "Active");

  return (
    <Pressable
      style={[d.card, { backgroundColor: C.bgCard, borderColor: C.border, borderLeftColor: cfg.color }]}
      onPress={() => { setOpen(v => !v); Haptics.selectionAsync(); }}
    >
      {/* Row header */}
      <View style={d.cardHeader}>
        <View style={[d.iconBubble, { backgroundColor: cfg.bg }]}>
          <Text style={{ fontSize: 16 }}>{item.icon}</Text>
        </View>

        <View style={{ flex: 1, gap: 1 }}>
          <Text style={[d.doshName, { color: C.text }]}>{item.name}</Text>
          <Text style={[d.doshHindi, { color: C.textMuted }]}>{item.name_hindi}</Text>
        </View>

        {/* Status badge */}
        <View style={[d.statusPill, { backgroundColor: cfg.bg }]}>
          {item.status === "Active" && (
            <Animated.View style={[d.statusDot, { backgroundColor: cfg.dot, transform: [{ scale: pulse }], opacity: pulse.interpolate({ inputRange: [1, 1.6], outputRange: [1, 0.5] }) }]} />
          )}
          {item.status !== "Active" && (
            <View style={[d.statusDot, { backgroundColor: cfg.dot }]} />
          )}
          <Text style={[d.statusText, { color: cfg.color }]}>{cfg.label}</Text>
        </View>

        <Feather name={open ? "chevron-up" : "chevron-down"} size={14} color={C.textMuted} style={{ marginLeft: 6 }} />
      </View>

      {/* Headline — always visible */}
      <Text style={[d.headline, { color: cfg.color }]} numberOfLines={open ? undefined : 2}>
        {item.headline}
      </Text>

      {/* Expanded content */}
      {open && (
        <View style={d.expanded}>
          <Text style={[d.desc, { color: C.textMuted }]}>{item.description}</Text>

          {item.planet_note ? (
            <View style={d.noteRow}>
              <Feather name="info" size={10} color={C.textDim} />
              <Text style={[d.noteText, { color: C.textDim }]}>{item.planet_note}</Text>
            </View>
          ) : null}

          {item.remedies.length > 0 && (
            <View style={d.remediesWrap}>
              <Text style={[d.remediesTitle, { color: C.textMuted }]}>UPAY (REMEDIES)</Text>
              {item.remedies.map((r, i) => (
                <View key={i} style={d.remedyRow}>
                  <View style={[d.remedyBullet, { backgroundColor: `${cfg.color}20` }]}>
                    <Text style={[d.remedyNum, { color: cfg.color }]}>{i + 1}</Text>
                  </View>
                  <Text style={[d.remedyText, { color: C.textMuted }]}>{r}</Text>
                </View>
              ))}
            </View>
          )}
        </View>
      )}
    </Pressable>
  );
}

// ── Summary Ring ──────────────────────────────────────────────────────────────
function SummaryRing({ active, mild, total }: { active: number; mild: number; total: number }) {
  const C = useC();
  const pct = Math.round(((9 - active - mild) / 9) * 100);
  const R = 40, circ = 2 * Math.PI * R;
  const scoreColor = active === 0 && mild <= 1 ? "#22c55e" : active > 1 ? "#ef4444" : "#f97316";

  return (
    <View style={[d.summaryCard, { backgroundColor: C.bgCard, borderColor: C.border }]}>
      {/* Ring */}
      <View style={{ width: 90, height: 90, position: "relative" }}>
        <Svg width={90} height={90} style={{ position: "absolute" } as any}>
          <Circle cx={45} cy={45} r={R} fill="none" stroke={C.border ?? "#1E293B"} strokeWidth={7} />
          <Circle cx={45} cy={45} r={R} fill="none"
            stroke={scoreColor} strokeWidth={7}
            strokeLinecap="round"
            strokeDasharray={`${circ * pct / 100} ${circ}`}
            rotation={-90} originX={45} originY={45}
          />
        </Svg>
        <View style={{ position: "absolute", top: 0, left: 0, right: 0, bottom: 0, alignItems: "center", justifyContent: "center" }}>
          <Text style={{ color: scoreColor, fontSize: 18, fontFamily: "Nunito_700Bold", lineHeight: 22 }}>{9 - active - mild}</Text>
          <Text style={{ color: C.textDim, fontSize: 9 }}>/ 9</Text>
        </View>
      </View>

      {/* Stats */}
      <View style={{ flex: 1, gap: 8 }}>
        <Text style={[d.summaryTitle, { color: C.text }]}>Dosh Analysis</Text>
        <View style={{ flexDirection: "row", gap: 12 }}>
          <View style={d.statItem}>
            <Text style={[d.statNum, { color: "#ef4444" }]}>{active}</Text>
            <Text style={[d.statLabel, { color: C.textMuted }]}>Active</Text>
          </View>
          <View style={[d.statDivider, { backgroundColor: C.border }]} />
          <View style={d.statItem}>
            <Text style={[d.statNum, { color: "#f97316" }]}>{mild}</Text>
            <Text style={[d.statLabel, { color: C.textMuted }]}>Mild</Text>
          </View>
          <View style={[d.statDivider, { backgroundColor: C.border }]} />
          <View style={d.statItem}>
            <Text style={[d.statNum, { color: "#22c55e" }]}>{9 - active - mild}</Text>
            <Text style={[d.statLabel, { color: C.textMuted }]}>Clear</Text>
          </View>
        </View>
        <Text style={{ fontSize: 10, color: C.textDim, fontFamily: "Nunito_400Regular" }}>
          {active + mild} of 9 doshas detected
        </Text>
      </View>
    </View>
  );
}

// ── Main Screen ───────────────────────────────────────────────────────────────
export default function DoshScreen() {
  const insets = useSafeAreaInsets();
  const C = useC();
  const { kundli, doshData, doshLoading } = useUser();
  const topPad = Platform.OS === "web" ? 67 : insets.top;
  const botPad = Platform.OS === "web" ? 34 : insets.bottom;

  const showDemo = !kundli;
  const list: DoshItem[] = showDemo
    ? DEMO_DOSH_LIST
    : (doshData?.dosh_list ?? DEMO_DOSH_LIST);

  const active = showDemo ? 2 : (doshData?.active_count ?? 0);
  const mild   = showDemo ? 2 : (doshData?.mild_count ?? 0);

  return (
    <ScrollView
      style={[d.root, { backgroundColor: C.bg }]}
      contentContainerStyle={{ paddingBottom: botPad + 20 }}
      showsVerticalScrollIndicator={false}
    >
      {/* ── Header ── */}
      <View style={[d.header, { paddingTop: topPad, borderBottomColor: C.border }]}>
        <Pressable style={d.backBtn} onPress={() => router.back()}>
          <Feather name="arrow-left" size={20} color={C.text} />
        </Pressable>
        <View style={{ flex: 1 }}>
          <Text style={[d.title, { color: C.text }]}>Dosh Analysis</Text>
          <Text style={[d.subtitle, { color: C.textMuted }]}>नौ दोष विश्लेषण (9 Doshas)</Text>
        </View>
        <View style={{ flexDirection: "row", alignItems: "center", gap: 8 }}>
          {doshLoading && <ActivityIndicator size="small" color="#f59e0b" />}
          {showDemo && (
            <View style={[d.demoBadge, { backgroundColor: C.bgCard2, borderColor: C.border }]}>
              <Text style={[d.demoBadgeText, { color: C.textMuted }]}>Demo</Text>
            </View>
          )}
        </View>
      </View>

      <View style={d.content}>
        {/* ── Summary ring ── */}
        <SummaryRing active={active} mild={mild} total={9} />

        {/* ── Loading skeleton or cards ── */}
        {!showDemo && doshLoading && !doshData && (
          <View style={[d.loadingCard, { backgroundColor: C.bgCard, borderColor: C.border }]}>
            <ActivityIndicator size="large" color="#f59e0b" />
            <Text style={{ color: C.textMuted, marginTop: 12, fontFamily: "Nunito_500Medium", fontSize: 13 }}>
              Analysing your kundli...
            </Text>
            <Text style={{ color: C.textDim, marginTop: 4, fontSize: 11, fontFamily: "Nunito_400Regular" }}>
              Checking all 9 dosh conditions
            </Text>
          </View>
        )}

        {/* ── Dosh cards — Active first, then Mild, then Clear ── */}
        {list
          .slice()
          .sort((a, b) => {
            const order = { Active: 0, Mild: 1, None: 2 };
            return order[a.status] - order[b.status];
          })
          .map((item, i) => (
            <DoshCard key={item.key} item={item} defaultOpen={i === 0 && item.status !== "None"} />
          ))
        }

        {/* ── Bottom disclaimer ── */}
        <View style={[d.disclaimer, { backgroundColor: C.bgCard2, borderColor: C.border }]}>
          <Feather name="info" size={11} color={C.textDim} />
          <Text style={{ color: C.textDim, fontSize: 10, fontFamily: "Nunito_400Regular", flex: 1, lineHeight: 14 }}>
            Dosh analysis is based on classical Vedic astrology principles. Always consult a qualified Jyotishi for important life decisions.
          </Text>
        </View>
      </View>
    </ScrollView>
  );
}

// ── Styles ────────────────────────────────────────────────────────────────────
const d = StyleSheet.create({
  root:    { flex: 1 },
  header:  {
    flexDirection: "row", alignItems: "center", gap: 12,
    paddingHorizontal: 16, paddingBottom: 14,
    borderBottomWidth: 1,
  },
  backBtn:  { width: 36, height: 36, alignItems: "center", justifyContent: "center" },
  title:    { fontSize: 17, fontFamily: "Nunito_700Bold" },
  subtitle: { fontSize: 11, fontFamily: "Nunito_400Regular", marginTop: 1 },
  demoBadge: {
    paddingHorizontal: 10, paddingVertical: 4,
    borderRadius: 12, borderWidth: 1,
  },
  demoBadgeText: { fontSize: 11, fontFamily: "Nunito_500Medium" },

  content: { paddingHorizontal: 16, paddingTop: 16, gap: 10 },

  // Summary card
  summaryCard: {
    borderRadius: 18, borderWidth: 1, padding: 16,
    flexDirection: "row", alignItems: "center", gap: 16,
  },
  summaryTitle: { fontSize: 15, fontFamily: "Nunito_700Bold" },
  statItem:  { alignItems: "center", gap: 2 },
  statNum:   { fontSize: 20, fontFamily: "Nunito_700Bold", lineHeight: 24 },
  statLabel: { fontSize: 9, fontFamily: "Nunito_400Regular", textTransform: "uppercase", letterSpacing: 0.8 },
  statDivider: { width: 1, height: 28 },

  // Loading
  loadingCard: {
    borderRadius: 18, borderWidth: 1, padding: 32,
    alignItems: "center", justifyContent: "center",
  },

  // Dosh card
  card: {
    borderRadius: 16, borderWidth: 1, borderLeftWidth: 3,
    padding: 14, gap: 6,
  },
  cardHeader: { flexDirection: "row", alignItems: "center", gap: 10 },
  iconBubble: {
    width: 38, height: 38, borderRadius: 10,
    alignItems: "center", justifyContent: "center",
  },
  doshName:  { fontSize: 13, fontFamily: "Nunito_700Bold" },
  doshHindi: { fontSize: 10, fontFamily: "Nunito_400Regular" },
  statusPill: {
    flexDirection: "row", alignItems: "center", gap: 4,
    paddingHorizontal: 8, paddingVertical: 4, borderRadius: 8,
  },
  statusDot:  { width: 6, height: 6, borderRadius: 3 },
  statusText: { fontSize: 10, fontFamily: "Nunito_700Bold" },
  headline:  { fontSize: 11, fontFamily: "Nunito_600SemiBold", marginLeft: 48, lineHeight: 16 },

  expanded: { marginTop: 4, gap: 10 },
  desc:     { fontSize: 12, fontFamily: "Nunito_400Regular", lineHeight: 18 },
  noteRow:  { flexDirection: "row", alignItems: "center", gap: 4 },
  noteText: { fontSize: 10, fontFamily: "Nunito_400Regular", flex: 1 },

  remediesWrap:  { gap: 6 },
  remediesTitle: { fontSize: 9, fontFamily: "Nunito_700Bold", letterSpacing: 1.5 },
  remedyRow:     { flexDirection: "row", gap: 10, alignItems: "flex-start" },
  remedyBullet:  {
    width: 18, height: 18, borderRadius: 9,
    alignItems: "center", justifyContent: "center",
  },
  remedyNum:  { fontSize: 9, fontFamily: "Nunito_700Bold" },
  remedyText: { flex: 1, fontSize: 11, fontFamily: "Nunito_400Regular", lineHeight: 16 },

  disclaimer: {
    borderRadius: 14, borderWidth: 1, padding: 12,
    flexDirection: "row", gap: 8, alignItems: "flex-start",
  },
});
