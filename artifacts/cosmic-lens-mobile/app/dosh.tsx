import { Feather } from "@expo/vector-icons";
import { router } from "expo-router";
import * as Haptics from "expo-haptics";
import React, { useMemo, useState } from "react";
import {
  Platform, Pressable, ScrollView,
  StyleSheet, Text, View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useC } from "@/context/ThemeContext";
import { useUser } from "@/context/UserContext";
import type { KundliData, PlanetInfo } from "@/types";

// ── Dosh Calculation Engine ───────────────────────────────────────────────────

const NAKSHATRAS = [
  "Ashwini","Bharani","Krittika","Rohini","Mrigashira","Ardra","Punarvasu","Pushya",
  "Ashlesha","Magha","Purva Phalguni","Uttara Phalguni","Hasta","Chitra","Swati",
  "Vishakha","Anuradha","Jyeshtha","Mula","Purva Ashadha","Uttara Ashadha","Shravana",
  "Dhanishtha","Shatabhisha","Purva Bhadrapada","Uttara Bhadrapada","Revati",
];

const GANDMOOL_NAKSHATRAS = ["Ashwini","Ashlesha","Magha","Jyeshtha","Mula","Revati"];

type Severity = "absent" | "mild" | "present" | "strong";

interface DoshResult {
  key: string;
  name: string;
  nameHindi: string;
  icon: string;
  severity: Severity;
  headline: string;
  description: string;
  remedies: string[];
  planetNote?: string;
}

function getHouse(planets: PlanetInfo[], name: string): number {
  return planets.find(p => p.name === name)?.house ?? 0;
}

function computeDoshas(kundli: KundliData): DoshResult[] {
  const pl = kundli.planets;

  const marsH    = getHouse(pl, "Mars");
  const sunH     = getHouse(pl, "Sun");
  const moonH    = getHouse(pl, "Moon");
  const jupH     = getHouse(pl, "Jupiter");
  const satH     = getHouse(pl, "Saturn");
  const rahuH    = getHouse(pl, "Rahu");
  const ketuH    = getHouse(pl, "Ketu");
  const rahuLon  = pl.find(p => p.name === "Rahu")?.longitude ?? 0;
  const ketuLon  = pl.find(p => p.name === "Ketu")?.longitude ?? 0;

  const results: DoshResult[] = [];

  // ── 1. Manglik Dosh ──────────────────────────────────────────────────────
  const manglikHouses = [1, 4, 7, 8, 12];
  const isManglik     = manglikHouses.includes(marsH);
  const isAnshikMangal = marsH === 2; // some traditions include 2nd house
  results.push({
    key: "manglik",
    name: "Manglik Dosh",
    nameHindi: "मांगलिक दोष",
    icon: "🔴",
    severity: isManglik ? "present" : isAnshikMangal ? "mild" : "absent",
    headline: isManglik
      ? `Mars in ${marsH}th House — Full Manglik Dosh`
      : isAnshikMangal
      ? `Mars in 2nd House — Partial Manglik`
      : `Mars in ${marsH}th House — No Dosh`,
    description: isManglik
      ? "Mars in houses 1, 4, 7, 8, or 12 creates Manglik Dosh, which can affect marriage and relationships."
      : "Mars is in a favorable position. No Manglik Dosh for marriage.",
    remedies: isManglik ? [
      "Perform Kumbh Vivah (symbolic marriage to a tree or idol) to neutralize Manglik Dosh",
      "Offer sindoor to Hanuman ji on Tuesdays",
      "Wear or keep a Mangal Yantra at home",
      "As per Lal Kitab — donate jaggery (gur) and chana dal",
    ] : [],
    planetNote: `Mars: House ${marsH}`,
  });

  // ── 2. Kalsarp Dosh ───────────────────────────────────────────────────────
  const corePlanets = pl.filter(p => !["Rahu","Ketu"].includes(p.name));
  let allInArc = true;
  let anyInArc = false;
  for (const p of corePlanets) {
    const rel = (p.longitude - rahuLon + 360) % 360;
    if (rel < 180) anyInArc = true;
    else allInArc = false;
  }
  const kalsarpSev: Severity = allInArc ? "strong" : anyInArc && !allInArc ? "mild" : "absent";
  results.push({
    key: "kalsarp",
    name: "Kalsarp Dosh",
    nameHindi: "कालसर्प दोष",
    icon: "🐍",
    severity: kalsarpSev,
    headline: kalsarpSev === "strong"
      ? "Full Kalsarp Dosh — All Planets Between Rahu–Ketu"
      : kalsarpSev === "mild"
      ? "Partial Kalsarp — Some Planets on Rahu–Ketu Axis"
      : "No Kalsarp Dosh",
    description: kalsarpSev !== "absent"
      ? "Kalsarp Dosh forms when all planets fall on one side of the Rahu–Ketu axis. It can cause obstacles, delays, and vivid dreams."
      : "No Kalsarp Dosh in your chart. Planets are spread across all directions.",
    remedies: kalsarpSev !== "absent" ? [
      "Perform Kalsarp Pooja at Trimbakeshwar or Ujjain",
      "Offer milk to a serpent idol on Nagpanchami",
      "Chant Mahamrityunjay mantra 108 times daily",
      "Offer sesame oil at a Navagraha temple for Rahu",
    ] : [],
    planetNote: `Rahu: House ${rahuH} | Ketu: House ${ketuH}`,
  });

  // ── 3. Pitra Dosh ─────────────────────────────────────────────────────────
  const pitraConditions = [
    sunH === rahuH,
    sunH === satH,
    satH === 9,
    sunH === 9 && (rahuH === 9 || satH === 9),
  ];
  const pitraCount  = pitraConditions.filter(Boolean).length;
  const pitraSev: Severity = pitraCount >= 2 ? "strong" : pitraCount === 1 ? "present" : "absent";
  results.push({
    key: "pitra",
    name: "Pitra Dosh",
    nameHindi: "पितृ दोष",
    icon: "🏛️",
    severity: pitraSev,
    headline: pitraSev !== "absent"
      ? `Sun–${sunH === rahuH ? "Rahu" : "Saturn"} conjunction — Pitra Dosh`
      : "No Pitra Dosh Found",
    description: pitraSev !== "absent"
      ? "Pitra Dosh occurs when Sun–Rahu or Sun–Saturn are in the same house. It can block ancestral blessings and cause career and family obstacles."
      : "No signs of Pitra Dosh in your chart.",
    remedies: pitraSev !== "absent" ? [
      "Offer tarpan to ancestors during Pitrupaksh (Shraddh)",
      "Chant Pitra Gayatri: 'Om Pitrubhyo Namah' 108 times daily",
      "Perform Shraddh at Gaya ji or Nashik",
      "Feed Brahmins and offer donations",
    ] : [],
    planetNote: `Sun: House ${sunH} | Saturn: House ${satH} | Rahu: House ${rahuH}`,
  });

  // ── 4. Guru Chandal Dosh ──────────────────────────────────────────────────
  const isGuruChandal = jupH === rahuH;
  const isGuruKetu    = jupH === ketuH;
  results.push({
    key: "guruchandal",
    name: "Guru Chandal Dosh",
    nameHindi: "गुरु चांडाल दोष",
    icon: "⚡",
    severity: isGuruChandal ? "present" : isGuruKetu ? "mild" : "absent",
    headline: isGuruChandal
      ? `Jupiter–Rahu conjunction in House ${jupH}`
      : isGuruKetu
      ? `Jupiter–Ketu conjunction in House ${jupH}`
      : "No Guru Chandal Dosh",
    description: isGuruChandal || isGuruKetu
      ? "The conjunction of Jupiter with Rahu/Ketu weakens Jupiter's positive energy. It may create obstacles in dharma, teaching, and higher education."
      : "Jupiter is in a separate house — free from Rahu/Ketu. Auspicious placement.",
    remedies: (isGuruChandal || isGuruKetu) ? [
      "Recite Vishnu Sahasranama daily",
      "Worship the Peepal tree for Jupiter (Brihaspati)",
      "Yellow Sapphire (Pushparagam) can be worn after proper consultation",
      "Wear Hessonite (Gomed) after ritual consecration for Rahu",
    ] : [],
    planetNote: `Jupiter: House ${jupH} | Rahu: House ${rahuH} | Ketu: House ${ketuH}`,
  });

  // ── 5. Grahan Dosh ────────────────────────────────────────────────────────
  const isSolarGrahan = (sunH === rahuH || sunH === ketuH);
  const isLunarGrahan = (moonH === rahuH || moonH === ketuH);
  const grahanSev: Severity = (isSolarGrahan && isLunarGrahan) ? "strong"
    : (isSolarGrahan || isLunarGrahan) ? "present" : "absent";
  results.push({
    key: "grahan",
    name: "Grahan Dosh",
    nameHindi: "ग्रहण दोष",
    icon: "🌑",
    severity: grahanSev,
    headline: grahanSev === "strong"
      ? "Solar + Lunar Eclipse Dosh — Double Dosh"
      : isSolarGrahan ? `Solar Eclipse Dosh — Sun in House ${sunH} with Rahu/Ketu`
      : isLunarGrahan ? `Lunar Eclipse Dosh — Moon in House ${moonH} with Rahu/Ketu`
      : "No Grahan Dosh",
    description: grahanSev !== "absent"
      ? "When Sun or Moon is conjunct Rahu/Ketu, Grahan Dosh forms. It can affect the mind, health, and ancestral connections."
      : "Sun and Moon are free from Rahu/Ketu — Grahan Dosh absent.",
    remedies: grahanSev !== "absent" ? [
      "For Solar Grahan — recite Aditya Hridaya Stotra",
      "For Lunar Grahan — offer raw milk to Lord Shiva",
      "Rahu–Ketu mantras: 'Om Rahave Namah' / 'Om Ketave Namah'",
      "Mantra chanting and charity on eclipse days yields special results",
    ] : [],
    planetNote: `Sun: House ${sunH} | Moon: House ${moonH} | Rahu: House ${rahuH} | Ketu: House ${ketuH}`,
  });

  // ── 6. Kemdrum Dosh ──────────────────────────────────────────────────────
  const prevH = ((moonH - 2 + 12) % 12) + 1;
  const nextH = (moonH % 12) + 1;
  const adjacentPlanets = pl.filter(p =>
    !["Rahu","Ketu","Moon"].includes(p.name) &&
    (p.house === prevH || p.house === nextH || p.house === moonH)
  );
  const isKemdrum = adjacentPlanets.length === 0;
  results.push({
    key: "kemdrum",
    name: "Kemdrum Dosh",
    nameHindi: "केमद्रुम दोष",
    icon: "🌙",
    severity: isKemdrum ? "present" : "absent",
    headline: isKemdrum
      ? `Moon Alone in House ${moonH} — Kemdrum Dosh`
      : `Planets Near Moon — No Dosh`,
    description: isKemdrum
      ? "Kemdrum Dosh occurs when no planet occupies the 2nd or 12th house from the Moon. It can cause emotional loneliness and psychological stress."
      : "Planets are present near Moon, so Kemdrum Dosh is not formed.",
    remedies: isKemdrum ? [
      "Offer water to Lord Shiva and chant Mahamrityunjay mantra on Mondays",
      "Donate white items (rice, milk, sugar) for Moon",
      "Wear Moonstone or Pearl after proper consecration",
      "Observe the Moon at night and chant 'Om Chandraya Namah' 108 times",
    ] : [],
    planetNote: `Moon: House ${moonH}`,
  });

  // ── 7. Gand Mool Dosh ─────────────────────────────────────────────────────
  const nakshatra    = kundli.nakshatra ?? "";
  const isGandMool   = GANDMOOL_NAKSHATRAS.includes(nakshatra);
  const nakIdx       = NAKSHATRAS.indexOf(nakshatra);
  const isFirstPada  = kundli.nakshatraPada === 1;
  const isLastPada   = kundli.nakshatraPada === 4;
  const gmSev: Severity = isGandMool && (isFirstPada || isLastPada) ? "strong"
    : isGandMool ? "present" : "absent";
  results.push({
    key: "gandmool",
    name: "Gand Mool Dosh",
    nameHindi: "गंड मूल दोष",
    icon: "⭕",
    severity: gmSev,
    headline: isGandMool
      ? `${nakshatra} Nakshatra — Gand Mool (Pada ${kundli.nakshatraPada})`
      : `${nakshatra || "Nakshatra"} — No Gand Mool Dosh`,
    description: isGandMool
      ? "Gand Mool Dosh occurs when Moon is in one of 6 special nakshatras: Ashwini, Ashlesha, Magha, Jyeshtha, Mula, Revati. A Shanti Puja is recommended."
      : "Your nakshatra is auspicious — not in the Gand Mool group.",
    remedies: isGandMool ? [
      "Perform Gand Mool Shanti Puja (27 days after birth or at any convenient time)",
      "Worship the ruling planet of your nakshatra",
      "Feed Brahmins and offer dakshina on Guru Poornima",
      `Pray to the deity of ${nakshatra} nakshatra`,
    ] : [],
    planetNote: `Nakshatra: ${nakshatra || "Unavailable"} | Pada: ${kundli.nakshatraPada ?? "?"}`,
  });

  // ── 8. Shani Dosh ─────────────────────────────────────────────────────────
  const satSign   = pl.find(p => p.name === "Saturn")?.sign ?? "";
  const isSatDebil = satSign === "Mesh"; // Saturn debilitated in Aries
  const satInKendra = [1,4,7,10].includes(satH);
  const satRetrograde = pl.find(p => p.name === "Saturn")?.retrograde ?? false;
  const shaniSev: Severity = (isSatDebil || (satInKendra && satRetrograde)) ? "present"
    : satRetrograde ? "mild" : "absent";
  results.push({
    key: "shani",
    name: "Shani Dosh",
    nameHindi: "शनि दोष",
    icon: "⏳",
    severity: shaniSev,
    headline: isSatDebil
      ? `Saturn Debilitated (${satSign}) — Shani Dosh`
      : satRetrograde
      ? `Saturn Retrograde in House ${satH}`
      : `Saturn in House ${satH} — Normal Position`,
    description: shaniSev !== "absent"
      ? "Saturn in debilitation or retrograde creates Shani Dosh. It may cause career delays, obstacles at work, and potential health issues."
      : "Saturn is well-placed. No Shani Dosh present.",
    remedies: shaniSev !== "absent" ? [
      "Light an oil lamp at a Shani temple on Saturdays",
      "Recite Shani Chalisa or Shani Stotra daily",
      "Donate black sesame seeds, black cloth, and mustard oil",
      "Hanuman Chalisa is especially beneficial during Saturn's dasha",
    ] : [],
    planetNote: `Saturn: House ${satH}${satRetrograde ? " (Retro)" : ""} | ${satSign}`,
  });

  return results;
}

// ── Severity config ───────────────────────────────────────────────────────────
const SEV_CONFIG: Record<Severity, { color: string; bg: string; label: string }> = {
  absent:  { color: "#22c55e", bg: "rgba(34,197,94,0.1)",    label: "Not Present" },
  mild:    { color: "#fbbf24", bg: "rgba(251,191,36,0.1)",   label: "Mild"        },
  present: { color: "#f97316", bg: "rgba(249,115,22,0.1)",   label: "Present"     },
  strong:  { color: "#ef4444", bg: "rgba(239,68,68,0.12)",   label: "Strong"      },
};

// ── Demo Dosh (when no kundli) ────────────────────────────────────────────────
const DEMO_KUNDLI: KundliData = {
  name: "Demo",
  ascendant: "Aquarius",
  ascendantDeg: 312,
  nakshatra: "Mula",
  nakshatraPada: 2,
  nakshatraRuler: "Ketu",
  moonSign: "Sagittarius",
  dashas: [],
  planets: [
    { name:"Sun",     house:11, longitude:256, sign:"Sagittarius", retrograde:false },
    { name:"Moon",    house:11, longitude:240, sign:"Sagittarius", retrograde:false },
    { name:"Mars",    house:4,  longitude:133, sign:"Leo",         retrograde:false },
    { name:"Mercury", house:11, longitude:270, sign:"Sagittarius", retrograde:true  },
    { name:"Jupiter", house:10, longitude:220, sign:"Scorpio",     retrograde:false },
    { name:"Venus",   house:10, longitude:210, sign:"Scorpio",     retrograde:false },
    { name:"Saturn",  house:7,  longitude:175, sign:"Libra",       retrograde:true  },
    { name:"Rahu",    house:11, longitude:260, sign:"Sagittarius", retrograde:true  },
    { name:"Ketu",    house:5,  longitude:80,  sign:"Gemini",      retrograde:true  },
  ],
};

// ── Dosh Card Component ───────────────────────────────────────────────────────
function DoshCard({ dosh, defaultOpen }: { dosh: DoshResult; defaultOpen?: boolean }) {
  const [open, setOpen] = useState(defaultOpen ?? false);
  const sev = SEV_CONFIG[dosh.severity];

  return (
    <Pressable
      style={[d.card, { borderLeftColor: sev.color }]}
      onPress={() => { setOpen(v => !v); Haptics.selectionAsync(); }}
    >
      {/* Header row */}
      <View style={d.cardHeader}>
        <View style={[d.iconBubble, { backgroundColor: sev.bg }]}>
          <Text style={{ fontSize: 16 }}>{dosh.icon}</Text>
        </View>
        <View style={{ flex: 1 }}>
          <Text style={d.doshName}>{dosh.name}</Text>
          <Text style={d.doshHindi}>{dosh.nameHindi}</Text>
        </View>
        <View style={[d.sevPill, { backgroundColor: sev.bg }]}>
          <Text style={[d.sevText, { color: sev.color }]}>{sev.label}</Text>
        </View>
        <Feather name={open ? "chevron-up" : "chevron-down"} size={15} color="#334155" style={{ marginLeft: 8 }} />
      </View>

      {/* Headline always visible */}
      <Text style={[d.headline, { color: sev.color }]}>{dosh.headline}</Text>

      {/* Expanded content */}
      {open && (
        <View style={d.expanded}>
          <Text style={d.desc}>{dosh.description}</Text>

          {dosh.planetNote && (
            <View style={d.planetNoteRow}>
              <Feather name="info" size={10} color="#1e3a5f" />
              <Text style={d.planetNote}>{dosh.planetNote}</Text>
            </View>
          )}

          {dosh.remedies.length > 0 && (
            <View style={d.remediesWrap}>
              <Text style={d.remediesTitle}>UPAY (REMEDIES)</Text>
              {dosh.remedies.map((r, i) => (
                <View key={i} style={d.remedyRow}>
                  <View style={d.remedyBullet}>
                    <Text style={d.remedyNum}>{i + 1}</Text>
                  </View>
                  <Text style={d.remedyText}>{r}</Text>
                </View>
              ))}
            </View>
          )}
        </View>
      )}
    </Pressable>
  );
}

// ── Main Screen ───────────────────────────────────────────────────────────────
export default function DoshScreen() {
  const insets  = useSafeAreaInsets();
  const C = useC();
  const { kundli } = useUser();
  const topPad  = Platform.OS === "web" ? 67 : insets.top;
  const botPad  = Platform.OS === "web" ? 34 : insets.bottom;
  const showDemo = !kundli;
  const data    = showDemo ? DEMO_KUNDLI : kundli;

  const doshas = useMemo(() => computeDoshas(data), [data]);

  const presentCount = doshas.filter(d => d.severity !== "absent").length;
  const strongCount  = doshas.filter(d => d.severity === "strong").length;

  return (
    <View style={[s.root, { backgroundColor: C.bg }]}>
      {/* Header */}
      <View style={[s.header, { paddingTop: topPad + 8 }]}>
        <Pressable onPress={() => router.back()} style={s.back}>
          <Feather name="arrow-left" size={20} color="#dde8f4" />
        </Pressable>
        <View style={{ flex: 1 }}>
          <Text style={s.title}>Dosh Analysis</Text>
          <Text style={s.titleHindi}>ग्रह दोष विश्लेषण</Text>
        </View>
        {showDemo && (
          <View style={s.demoPill}>
            <Text style={s.demoPillText}>Demo</Text>
          </View>
        )}
      </View>

      <ScrollView
        contentContainerStyle={[s.content, { paddingBottom: botPad + 30 }]}
        showsVerticalScrollIndicator={false}
      >
        {/* Demo banner */}
        {showDemo && (
          <Pressable style={s.demoBanner} onPress={() => router.push("/onboarding")}>
            <Feather name="lock" size={12} color="#fbbf24" />
            <Text style={s.demoText}>Apni kundli banao — exact dosh calculation ke liye</Text>
            <Feather name="chevron-right" size={12} color="#fbbf24" />
          </Pressable>
        )}

        {/* Summary bar */}
        <View style={s.summaryRow}>
          <View style={[s.summaryChip, { borderColor: "rgba(239,68,68,0.3)", backgroundColor: "rgba(239,68,68,0.08)" }]}>
            <Text style={[s.summaryNum, { color: "#ef4444" }]}>{presentCount}</Text>
            <Text style={s.summaryLabel}>Doshas Mili</Text>
          </View>
          <View style={[s.summaryChip, { borderColor: "rgba(249,115,22,0.3)", backgroundColor: "rgba(249,115,22,0.08)" }]}>
            <Text style={[s.summaryNum, { color: "#f97316" }]}>{strongCount}</Text>
            <Text style={s.summaryLabel}>Poorn Dosh</Text>
          </View>
          <View style={[s.summaryChip, { borderColor: "rgba(34,197,94,0.3)", backgroundColor: "rgba(34,197,94,0.08)" }]}>
            <Text style={[s.summaryNum, { color: "#22c55e" }]}>{doshas.length - presentCount}</Text>
            <Text style={s.summaryLabel}>Dosh Mukt</Text>
          </View>
        </View>

        {/* Note */}
        <Text style={s.note}>
          Har card pe tap karein detail aur upay dekhne ke liye.
        </Text>

        {/* Dosh cards */}
        {doshas.map(dosh => (
          <DoshCard
            key={dosh.key}
            dosh={dosh}
            defaultOpen={dosh.severity !== "absent"}
          />
        ))}

        {/* Disclaimer */}
        <View style={s.disclaimer}>
          <Feather name="info" size={12} color="#1e3a5f" />
          <Text style={s.disclaimerText}>
            Yeh analysis Vedic Jyotish ke anusaar hai. Kisi qualified Jyotishi se vistrit salah zaroor lein.
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
  titleHindi: { color:"#3d5a7a", fontSize:11 },
  demoPill: { backgroundColor:"rgba(251,191,36,0.12)", borderRadius:8, paddingHorizontal:8, paddingVertical:3, borderWidth:1, borderColor:"rgba(251,191,36,0.25)" },
  demoPillText: { color:"#fbbf24", fontSize:10, fontWeight:"700" },

  content: { paddingHorizontal:16, gap:10, paddingTop:14 },

  demoBanner: {
    flexDirection:"row", alignItems:"center", gap:8,
    backgroundColor:"rgba(251,191,36,0.06)", borderRadius:12,
    borderWidth:1, borderColor:"rgba(251,191,36,0.2)",
    paddingHorizontal:14, paddingVertical:10,
  },
  demoText: { color:"#fbbf24", fontSize:12, flex:1 },

  summaryRow: { flexDirection:"row", gap:10 },
  summaryChip: {
    flex:1, borderRadius:12, borderWidth:1,
    paddingVertical:10, alignItems:"center", gap:2,
  },
  summaryNum:   { color:"white", fontSize:20, fontWeight:"800" },
  summaryLabel: { color:"#475569", fontSize:10, fontWeight:"600" },

  note: { color:"#1e3a5f", fontSize:11, textAlign:"center", marginVertical:4 },

  disclaimer: {
    flexDirection:"row", alignItems:"flex-start", gap:8,
    backgroundColor:"rgba(255,255,255,0.02)", borderRadius:10,
    padding:12, borderWidth:1, borderColor:"rgba(255,255,255,0.04)",
    marginTop:8,
  },
  disclaimerText: { color:"#1e3a5f", fontSize:11, lineHeight:17, flex:1 },
});

const d = StyleSheet.create({
  card: {
    backgroundColor:"#040e1f", borderRadius:14,
    borderWidth:1, borderColor:"rgba(255,255,255,0.06)",
    borderLeftWidth:3, padding:14, gap:6,
  },
  cardHeader: { flexDirection:"row", alignItems:"center", gap:10 },
  iconBubble: { width:36, height:36, borderRadius:10, alignItems:"center", justifyContent:"center", flexShrink:0 },
  doshName:  { color:"#dde8f4", fontSize:13, fontWeight:"700" },
  doshHindi: { color:"#334155", fontSize:10, marginTop:1 },
  sevPill: { borderRadius:10, paddingHorizontal:8, paddingVertical:3 },
  sevText: { fontSize:9, fontWeight:"800", letterSpacing:0.5 },
  headline:  { fontSize:12, fontWeight:"600", marginLeft:46 },

  expanded: { marginTop:6, gap:10 },
  desc: { color:"#64748b", fontSize:12, lineHeight:19 },
  planetNoteRow: { flexDirection:"row", alignItems:"center", gap:5 },
  planetNote: { color:"#1e3a5f", fontSize:10, flex:1 },

  remediesWrap: { gap:8 },
  remediesTitle: { fontSize:9, fontWeight:"800", letterSpacing:2, color:"#334155" },
  remedyRow: { flexDirection:"row", alignItems:"flex-start", gap:10 },
  remedyBullet: {
    width:20, height:20, borderRadius:10,
    backgroundColor:"rgba(245,158,11,0.1)",
    alignItems:"center", justifyContent:"center", flexShrink:0, marginTop:1,
  },
  remedyNum:  { color:"#f59e0b", fontSize:10, fontWeight:"700" },
  remedyText: { color:"#475569", fontSize:12, lineHeight:18, flex:1 },
});
