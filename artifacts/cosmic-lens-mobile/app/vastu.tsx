import { Feather } from "@expo/vector-icons";
import * as Haptics from "expo-haptics";
import { router } from "expo-router";
import React, { useState } from "react";
import {
  Platform, Pressable, ScrollView,
  StyleSheet, Text, View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useC } from "@/context/ThemeContext";

// ── Vastu Data ────────────────────────────────────────────────────────────────

interface VastuTip {
  icon: string;
  text: string;
}
interface VastuRoom {
  key: string;
  name: string;
  nameHindi: string;
  emoji: string;
  idealDir: string;
  color: string;
  bg: string;
  border: string;
  element: string;
  elementIcon: string;
  importance: string;
  dos: VastuTip[];
  donts: VastuTip[];
  remedies: string[];
}

const ROOMS: VastuRoom[] = [
  {
    key:"main-door",
    name:"Mukhya Dwar",
    nameHindi:"मुख्य द्वार",
    emoji:"🚪",
    idealDir:"North, East, or North-East (NE) — Best Directions",
    color:"#f59e0b",
    bg:"rgba(245,158,11,0.05)",
    border:"rgba(245,158,11,0.2)",
    element:"Vaayu",
    elementIcon:"🌬️",
    importance:"The main door is the gateway for positive energy and prosperity. Its direction is the most important Vastu factor for the entire home.",
    dos:[
      { icon:"✅", text:"North-East (NE) or North direction is the best for the main door" },
      { icon:"✅", text:"Use a solid, heavy wooden door" },
      { icon:"✅", text:"Place a Swastik or Om symbol above the entrance" },
      { icon:"✅", text:"The door should open inward" },
      { icon:"✅", text:"Keep the nameplate clean and clearly visible" },
      { icon:"✅", text:"Ensure the entrance is well-lit at all times" },
    ],
    donts:[
      { icon:"❌", text:"Avoid a column or pillar directly in front of the main door" },
      { icon:"❌", text:"Avoid placing the main door in the South (S) or South-West (SW)" },
      { icon:"❌", text:"Do not pile up footwear outside the main door" },
      { icon:"❌", text:"Never leave the door squeaky or broken — fix it promptly" },
      { icon:"❌", text:"Do not have a bathroom directly facing the main entrance" },
    ],
    remedies:[
      "Place a 'Shri' or Ganpati symbol on the door for blessings",
      "Draw rangoli or place fresh flowers at the entrance every morning",
      "Chant 'Om Namah Shivaya' when entering the home",
    ],
  },
  {
    key:"living",
    name:"Baithak / Drawing Room",
    nameHindi:"बैठक / ड्रॉइंग रूम",
    emoji:"🛋️",
    idealDir:"North or East wing of the home",
    color:"#fbbf24",
    bg:"rgba(251,191,36,0.05)",
    border:"rgba(251,191,36,0.2)",
    element:"Agni + Vaayu",
    elementIcon:"🔥",
    importance:"The living room is the center of a home's social energy. Guests are welcomed here and the family gathers in this space.",
    dos:[
      { icon:"✅", text:"Place sofa and furniture in the NW or SW corner" },
      { icon:"✅", text:"TV or entertainment unit should face East or North wall" },
      { icon:"✅", text:"East-facing windows let in beneficial morning sunlight" },
      { icon:"✅", text:"Use light colors — white, cream, or light yellow" },
      { icon:"✅", text:"Hang a clock on the North or East wall" },
    ],
    donts:[
      { icon:"❌", text:"Do not place the sofa directly facing the main door" },
      { icon:"❌", text:"Avoid dark colors like black or dark red" },
      { icon:"❌", text:"Remove broken or damaged furniture immediately" },
      { icon:"❌", text:"Do not place a mirror in the corner near the door" },
    ],
    remedies:[
      "Place a crystal ball in the North-East corner to enhance positivity",
      "Keep a Laughing Buddha on the North wall for wealth",
      "Place fresh flowers or plants in the NE or East corner",
    ],
  },
  {
    key:"kitchen",
    name:"Rasoi / Kitchen",
    nameHindi:"रसोई",
    emoji:"🍳",
    idealDir:"South-East (SE) — Agni (Fire) Zone",
    color:"#f97316",
    bg:"rgba(249,115,22,0.05)",
    border:"rgba(249,115,22,0.2)",
    element:"Agni",
    elementIcon:"🔥",
    importance:"The kitchen represents the fire element. A correctly placed kitchen promotes the health and prosperity of the entire family.",
    dos:[
      { icon:"✅", text:"Place the stove/gas burner in the SE corner — the Fire zone" },
      { icon:"✅", text:"Face East while cooking for positive energy" },
      { icon:"✅", text:"Place the sink near the NE or North wall" },
      { icon:"✅", text:"Use yellow, orange, or cream colors in the kitchen" },
      { icon:"✅", text:"Windows in the SE or East direction are ideal" },
    ],
    donts:[
      { icon:"❌", text:"Never have the kitchen directly facing or above a bathroom" },
      { icon:"❌", text:"Never place the stove in the NE corner" },
      { icon:"❌", text:"Avoid dark colors in the kitchen" },
      { icon:"❌", text:"Avoid building a kitchen in the North or North-East" },
    ],
    remedies:[
      "Occasionally offer the first roti to a cow for blessings",
      "Place a photo of Annapurna Mata (goddess of food) in the kitchen",
      "Burning camphor in the kitchen is considered auspicious",
    ],
  },
  {
    key:"master-bedroom",
    name:"Master Bedroom",
    nameHindi:"मुख्य शयनकक्ष",
    emoji:"🛏️",
    idealDir:"South-West (SW) — Best for the head of household",
    color:"#a78bfa",
    bg:"rgba(167,139,250,0.05)",
    border:"rgba(167,139,250,0.2)",
    element:"Prithvi",
    elementIcon:"🌍",
    importance:"The head of the household sleeps in the master bedroom. The South-West direction provides stability, strength, and prosperity.",
    dos:[
      { icon:"✅", text:"Place the bed near the SW or South wall" },
      { icon:"✅", text:"Sleep with your head pointing South or East" },
      { icon:"✅", text:"Keep wardrobes and heavy furniture on the South or West wall" },
      { icon:"✅", text:"Use light pink, beige, or lavender as room colors" },
      { icon:"✅", text:"Cover mirrors in the bedroom at night" },
    ],
    donts:[
      { icon:"❌", text:"Avoid sleeping with your head pointing North — it causes health issues" },
      { icon:"❌", text:"Do not place the bed directly under a beam" },
      { icon:"❌", text:"Avoid TV in the bedroom; cover it if present" },
      { icon:"❌", text:"Do not build the master bedroom in the NE corner" },
      { icon:"❌", text:"Do not sleep with feet pointing toward the door" },
    ],
    remedies:[
      "Keep rose quartz or amethyst crystals in the bedroom",
      "Place a bowl of sea salt under the bed to absorb negative energy",
      "Hang a couple's photo on the South wall for harmony",
    ],
  },
  {
    key:"children",
    name:"Bachon ka Kamra",
    nameHindi:"बच्चों का कमरा",
    emoji:"📚",
    idealDir:"West or North-West (NW)",
    color:"#4ade80",
    bg:"rgba(74,222,128,0.05)",
    border:"rgba(74,222,128,0.2)",
    element:"Vaayu",
    elementIcon:"🌬️",
    importance:"The direction of the children's room affects their studies, creativity, and overall health.",
    dos:[
      { icon:"✅", text:"Place the study desk facing East or North for focus" },
      { icon:"✅", text:"Keep the bed near the West or NW wall for good sleep" },
      { icon:"✅", text:"Store books on the East or North wall" },
      { icon:"✅", text:"Use green, yellow, or light blue as room colors" },
      { icon:"✅", text:"Keep a photo of Saraswati ji or a Vidya Yantra in the room" },
    ],
    donts:[
      { icon:"❌", text:"Do not place the study chair in the SE corner (Fire zone)" },
      { icon:"❌", text:"Avoid TV in children's rooms entirely" },
      { icon:"❌", text:"Do not keep a heavy wardrobe near the child's head" },
    ],
    remedies:[
      "Place a Saraswati Yantra on the study table to improve concentration",
      "Green plants in the room enhance creativity and fresh energy",
      "Recite Saraswati Chalisa in the morning before exams",
    ],
  },
  {
    key:"pooja",
    name:"Pooja Ghar",
    nameHindi:"पूजा घर",
    emoji:"🪔",
    idealDir:"North-East (NE) — Ishaan Zone (Most Sacred)",
    color:"#f59e0b",
    bg:"rgba(245,158,11,0.06)",
    border:"rgba(245,158,11,0.25)",
    element:"Jal + Aakash",
    elementIcon:"💧",
    importance:"The prayer room is the holiest space in the home. The North-East (Ishaan) corner is considered the abode of the divine.",
    dos:[
      { icon:"✅", text:"Always place the temple/altar in the NE or East direction" },
      { icon:"✅", text:"Face East or North while praying" },
      { icon:"✅", text:"Ensure deity idols are placed at eye level or higher" },
      { icon:"✅", text:"Keep the prayer space clean and well-lit at all times" },
      { icon:"✅", text:"White, yellow, or orange are the best colors for this room" },
    ],
    donts:[
      { icon:"❌", text:"Do not place the temple inside a bedroom" },
      { icon:"❌", text:"Never have a toilet above or below the prayer room" },
      { icon:"❌", text:"Do not keep broken or damaged idols" },
      { icon:"❌", text:"Avoid placing the temple in the South direction" },
    ],
    remedies:[
      "Light a ghee lamp in the temple every morning",
      "Burn camphor incense in the prayer room to amplify divine energy",
      "Offer marigold flowers every Friday for blessings",
    ],
  },
  {
    key:"bathroom",
    name:"Bathroom / Shauchalaya",
    nameHindi:"बाथरूम / शौचालय",
    emoji:"🚿",
    idealDir:"North-West (NW) or West — Ideal Placement",
    color:"#60a5fa",
    bg:"rgba(96,165,250,0.05)",
    border:"rgba(96,165,250,0.2)",
    element:"Jal",
    elementIcon:"💧",
    importance:"An incorrectly placed bathroom can bring negativity, health issues, and financial difficulties into the home.",
    dos:[
      { icon:"✅", text:"NW or West is the best location for bathrooms" },
      { icon:"✅", text:"Place the geyser or water heater in the SE corner" },
      { icon:"✅", text:"Exhaust fan or window should be in East or North" },
      { icon:"✅", text:"Toilet seat should face the South or West wall" },
      { icon:"✅", text:"Keep the bathroom clean and dry at all times" },
    ],
    donts:[
      { icon:"❌", text:"Never place a bathroom in the NE (Ishaan) corner" },
      { icon:"❌", text:"Avoid having a bathroom adjacent to the prayer room" },
      { icon:"❌", text:"Always keep the bathroom door closed" },
      { icon:"❌", text:"Fix leaking taps immediately — they drain wealth energy" },
    ],
    remedies:[
      "Place sea salt or a lemon outside the bathroom to absorb negativity",
      "Add a few drops of neem or eucalyptus oil to the bathroom water",
      "Place an Om sticker on the door if the bathroom is in the NE",
    ],
  },
  {
    key:"study",
    name:"Study / Office Room",
    nameHindi:"अध्ययन / कार्यालय",
    emoji:"💼",
    idealDir:"North — For Wealth and Career Growth",
    color:"#34d399",
    bg:"rgba(52,211,153,0.05)",
    border:"rgba(52,211,153,0.2)",
    element:"Vaayu + Aakash",
    elementIcon:"🌬️",
    importance:"Having the home office or study in the North boosts career growth, wealth, and focus.",
    dos:[
      { icon:"✅", text:"Place the desk facing a window or door for positive energy flow" },
      { icon:"✅", text:"Face North or East while working" },
      { icon:"✅", text:"Place a safe or locker in the SW corner for financial security" },
      { icon:"✅", text:"Keep a solid wall behind you for strong support" },
      { icon:"✅", text:"Green or blue are auspicious colors for an office" },
    ],
    donts:[
      { icon:"❌", text:"Do not place the desk in a corner — it blocks energy flow" },
      { icon:"❌", text:"Avoid sitting with your back to the door while working" },
      { icon:"❌", text:"Do not let the office door directly face a wall" },
      { icon:"❌", text:"Do not keep clutter or garbage in the office space" },
    ],
    remedies:[
      "Place a Kuber Yantra on the North wall for wealth and career growth",
      "Keep a green lucky bamboo plant in the North corner",
      "Chant 'Om Ganeshaya Namah' before beginning work each day",
    ],
  },
];

const COMPASS_DIRS = [
  { short:"N",  label:"Uttar",   color:"#f59e0b" },
  { short:"NE", label:"Ishaan",  color:"#a78bfa" },
  { short:"E",  label:"Poorv",   color:"#fbbf24" },
  { short:"SE", label:"Agni",    color:"#f97316" },
  { short:"S",  label:"Dakshin", color:"#ef4444" },
  { short:"SW", label:"Nairitya",color:"#64748b" },
  { short:"W",  label:"Paschim", color:"#60a5fa" },
  { short:"NW", label:"Vaayu",   color:"#34d399" },
];

// ── Room Card ─────────────────────────────────────────────────────────────────
function RoomCard({ room }: { room: VastuRoom }) {
  const [open, setOpen] = useState(false);
  const [tab,  setTab]  = useState<"dos"|"donts"|"remedies">("dos");
  const C = useC();

  return (
    <Pressable
      style={[c.card, { borderColor: room.border, backgroundColor: room.bg }]}
      onPress={() => { setOpen(v => !v); Haptics.selectionAsync(); }}
    >
      {/* Header */}
      <View style={c.cardHeader}>
        <View style={[c.iconBubble, { backgroundColor:`${room.color}15` }]}>
          <Text style={{ fontSize:20 }}>{room.emoji}</Text>
        </View>
        <View style={{ flex:1 }}>
          <Text style={[c.roomName, { color:room.color }]}>{room.name}</Text>
          <Text style={[c.roomHindi, { color: C.textMuted }]}>{room.nameHindi}</Text>
        </View>
        <View style={[c.elemPill, { backgroundColor:`${room.color}10` }]}>
          <Text style={{ fontSize:10 }}>{room.elementIcon}</Text>
          <Text style={[c.elemText, { color:room.color }]}>{room.element}</Text>
        </View>
        <Feather name={open ? "chevron-up" : "chevron-down"} size={15} color={C.textMuted} style={{ marginLeft:8 }} />
      </View>

      {/* Direction bar — always visible */}
      <View style={c.dirRow}>
        <Feather name="compass" size={11} color={C.textMuted} />
        <Text style={[c.dirText, { color: C.textMuted }]}>{room.idealDir}</Text>
      </View>

      {/* Expanded content */}
      {open && (
        <View style={c.expanded}>
          {/* Importance */}
          <Text style={[c.importance, { color: C.textMuted }]}>{room.importance}</Text>

          {/* Tab row */}
          <View style={c.tabRow}>
            {(["dos","donts","remedies"] as const).map(t => (
              <Pressable key={t} onPress={() => setTab(t)}
                style={[c.tabBtn, { borderColor: C.border, backgroundColor: C.bgCard2 },
                  tab===t && { backgroundColor:`${room.color}15`, borderColor:`${room.color}30` }]}>
                <Text style={[c.tabText, { color: C.textMuted }, tab===t && { color:room.color }]}>
                  {t==="dos" ? "Do ✅" : t==="donts" ? "Don't ❌" : "Remedies 🙏"}
                </Text>
              </Pressable>
            ))}
          </View>

          {tab === "dos" && (
            <View style={{ gap:8 }}>
              {room.dos.map((d,i) => (
                <View key={i} style={c.tipRow}>
                  <Text style={c.tipIcon}>{d.icon}</Text>
                  <Text style={[c.tipText, { color: C.textMuted }]}>{d.text}</Text>
                </View>
              ))}
            </View>
          )}
          {tab === "donts" && (
            <View style={{ gap:8 }}>
              {room.donts.map((d,i) => (
                <View key={i} style={c.tipRow}>
                  <Text style={c.tipIcon}>{d.icon}</Text>
                  <Text style={[c.tipText, { color:"#f87171" }]}>{d.text}</Text>
                </View>
              ))}
            </View>
          )}
          {tab === "remedies" && (
            <View style={{ gap:8 }}>
              {room.remedies.map((r,i) => (
                <View key={i} style={c.tipRow}>
                  <View style={[c.remedyNum, { backgroundColor: C.bgCard2 }]}><Text style={{ color:room.color, fontSize:10, fontWeight:"700" }}>{i+1}</Text></View>
                  <Text style={[c.tipText, { color: C.textMuted }]}>{r}</Text>
                </View>
              ))}
            </View>
          )}
        </View>
      )}
    </Pressable>
  );
}

// ── Compass Component ─────────────────────────────────────────────────────────
function VastuCompass() {
  const C = useC();
  return (
    <View style={[cp.wrap, { backgroundColor: C.bgCard, borderColor: C.border }]}>
      <Text style={[cp.title, { color: C.textMuted }]}>VASTU COMPASS — DIRECTIONS</Text>
      <View style={cp.grid}>
        {COMPASS_DIRS.map(d => (
          <View key={d.short} style={[cp.dir, { borderColor:`${d.color}30`, backgroundColor:`${d.color}08` }]}>
            <Text style={[cp.short, { color:d.color }]}>{d.short}</Text>
            <Text style={[cp.label, { color: C.textMuted }]}>{d.label}</Text>
          </View>
        ))}
      </View>
      <Text style={[cp.note, { color: C.textMuted }]}>NE = Ishaan (Divine), SE = Agni (Fire), SW = Nairitya, NW = Vaayu (Wind)</Text>
    </View>
  );
}

// ── Main Screen ───────────────────────────────────────────────────────────────
export default function VastuScreen() {
  const insets = useSafeAreaInsets();
  const C = useC();
  const topPad = Platform.OS === "web" ? 67 : insets.top;
  const botPad = Platform.OS === "web" ? 34 : insets.bottom;

  return (
    <View style={[s.root, { backgroundColor: C.bg }]}>
      {/* Header */}
      <View style={[s.header, { paddingTop: topPad + 8 }]}>
        <Pressable onPress={() => router.back()} style={s.back}>
          <Feather name="arrow-left" size={20} color={C.textMuted} />
        </Pressable>
        <View style={{ flex:1 }}>
          <Text style={[s.title, { color: C.text }]}>Vastu Shastra</Text>
          <Text style={[s.titleHindi, { color: C.textMuted }]}>वास्तु शास्त्र — Room-wise Guidance</Text>
        </View>
      </View>

      <ScrollView
        contentContainerStyle={[s.content, { paddingBottom: botPad + 30 }]}
        showsVerticalScrollIndicator={false}
      >
        {/* Intro */}
        <View style={s.introCard}>
          <Text style={{ fontSize:24 }}>🏠</Text>
          <View style={{ flex:1 }}>
            <Text style={[s.introTitle, { color: C.text }]}>What is Vastu Shastra?</Text>
            <Text style={[s.introBody, { color: C.textMuted }]}>
              Vastu Shastra is an ancient Indian science of architecture. Correct directions and
              arrangements bring positive energy, happiness, health, and prosperity to your home.
            </Text>
          </View>
        </View>

        {/* Compass */}
        <VastuCompass />

        {/* Section label */}
        <Text style={s.sectionLabel}>ROOM-WISE VASTU GUIDE</Text>
        <Text style={[s.sectionSub, { color: C.textMuted }]}>Tap any card to see dos, don'ts, and remedies</Text>

        {/* Room cards */}
        {ROOMS.map(room => (
          <RoomCard key={room.key} room={room} />
        ))}

        {/* General tips */}
        <View style={[s.genCard, { backgroundColor: C.bgCard, borderColor: C.border }]}>
          <Text style={[s.genTitle, { color: C.text }]}>⚡ General Vastu Tips</Text>
          {[
            "Keep the home free of clutter — blocked spaces block energy flow",
            "Ensure your home is well-lit — darkness invites negativity",
            "Fix squeaky or broken doors promptly",
            "Keep indoor plants — they bring life energy into the home",
            "Remove broken or damaged items immediately",
            "A running water feature (fountain or aquarium) in the North is auspicious",
          ].map((tip,i) => (
            <View key={i} style={s.genRow}>
              <View style={[s.genDot, { backgroundColor: C.textDim }]} />
              <Text style={[s.genText, { color: C.textMuted }]}>{tip}</Text>
            </View>
          ))}
        </View>

        {/* Disclaimer */}
        <View style={[s.disclaimer, { backgroundColor: C.bgCard, borderColor: C.border }]}>
          <Feather name="info" size={12} color={C.textMuted} />
          <Text style={[s.disclaimerText, { color: C.textMuted }]}>
            This is a general Vastu guide. For your home specifically, always consult a qualified Vastu expert for personalized advice.
          </Text>
        </View>
      </ScrollView>
    </View>
  );
}

const s = StyleSheet.create({
  root:    { flex:1, backgroundColor:"#020d1a" },
  header:  { flexDirection:"row", alignItems:"center", gap:12, paddingHorizontal:16, paddingBottom:14, borderBottomWidth:1, borderBottomColor:"rgba(255,255,255,0.05)" },
  back:    { width:36, height:36, alignItems:"center", justifyContent:"center" },
  title:   { color:"#dde8f4", fontSize:17, fontWeight:"800" },
  titleHindi: { color:"#3d5a7a", fontSize:10, marginTop:1 },
  content: { paddingHorizontal:16, gap:12, paddingTop:14 },
  sectionLabel: { fontSize:10, fontWeight:"800", letterSpacing:2.5, color:"#f59e0b", marginBottom:2 },
  sectionSub:   { color:"#1e3a5f", fontSize:11, marginBottom:4, marginTop:-6 },

  introCard: {
    flexDirection:"row", alignItems:"flex-start", gap:12,
    backgroundColor:"rgba(245,158,11,0.04)", borderRadius:14,
    borderWidth:1, borderColor:"rgba(245,158,11,0.15)", padding:14,
  },
  introTitle: { color:"#dde8f4", fontSize:13, fontWeight:"700", marginBottom:5 },
  introBody:  { color:"#475569", fontSize:12, lineHeight:19 },

  genCard: {
    backgroundColor:"rgba(255,255,255,0.02)", borderRadius:14,
    borderWidth:1, borderColor:"rgba(255,255,255,0.06)", padding:14, gap:10,
  },
  genTitle: { color:"#dde8f4", fontSize:13, fontWeight:"700", marginBottom:4 },
  genRow:   { flexDirection:"row", alignItems:"flex-start", gap:10 },
  genDot:   { width:6, height:6, borderRadius:3, backgroundColor:"#334155", marginTop:5, flexShrink:0 },
  genText:  { color:"#475569", fontSize:12, lineHeight:19, flex:1 },

  disclaimer: {
    flexDirection:"row", alignItems:"flex-start", gap:8,
    backgroundColor:"rgba(255,255,255,0.02)", borderRadius:10,
    padding:12, borderWidth:1, borderColor:"rgba(255,255,255,0.04)",
  },
  disclaimerText: { color:"#1e3a5f", fontSize:11, lineHeight:17, flex:1 },
});

const c = StyleSheet.create({
  card: { borderRadius:14, borderWidth:1, padding:14, gap:8 },
  cardHeader: { flexDirection:"row", alignItems:"center", gap:10 },
  iconBubble: { width:44, height:44, borderRadius:12, alignItems:"center", justifyContent:"center", flexShrink:0 },
  roomName:   { fontSize:13, fontWeight:"700" },
  roomHindi:  { color:"#334155", fontSize:10, marginTop:2 },
  elemPill:   { flexDirection:"row", alignItems:"center", gap:4, borderRadius:8, paddingHorizontal:7, paddingVertical:3 },
  elemText:   { fontSize:9, fontWeight:"700" },
  dirRow:     { flexDirection:"row", alignItems:"center", gap:6 },
  dirText:    { color:"#3d5a7a", fontSize:11, flex:1 },
  importance: { color:"#475569", fontSize:12, lineHeight:19 },
  expanded:   { gap:12 },
  tabRow:     { flexDirection:"row", gap:6 },
  tabBtn:     {
    flex:1, alignItems:"center", paddingVertical:8, borderRadius:8,
    borderWidth:1, borderColor:"rgba(255,255,255,0.06)",
    backgroundColor:"rgba(255,255,255,0.02)",
  },
  tabText:    { color:"#334155", fontSize:10, fontWeight:"600" },
  tipRow:     { flexDirection:"row", alignItems:"flex-start", gap:8 },
  tipIcon:    { fontSize:13, lineHeight:20, flexShrink:0 },
  tipText:    { color:"#94a3b8", fontSize:12, lineHeight:19, flex:1 },
  remedyNum:  { width:20, height:20, borderRadius:10, backgroundColor:"rgba(255,255,255,0.06)", alignItems:"center", justifyContent:"center", flexShrink:0, marginTop:1 },
});

const cp = StyleSheet.create({
  wrap:  { backgroundColor:"#040e1f", borderRadius:14, borderWidth:1, borderColor:"rgba(255,255,255,0.06)", padding:14, gap:10 },
  title: { fontSize:9, fontWeight:"800", letterSpacing:2, color:"#334155", textAlign:"center" },
  grid:  { flexDirection:"row", flexWrap:"wrap", gap:6, justifyContent:"center" },
  dir: {
    width:"22%", borderRadius:10, borderWidth:1, padding:8,
    alignItems:"center", gap:2,
  },
  short: { fontSize:14, fontWeight:"800" },
  label: { color:"#475569", fontSize:10 },
  note:  { color:"#1e3a5f", fontSize:10, textAlign:"center", lineHeight:16 },
});
