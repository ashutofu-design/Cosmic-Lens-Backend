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
  const isAnshikMangal = marsH === 2;
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
    sunH === ketuH,
    (sunH === 9 && (rahuH === 9 || ketuH === 9)),
  ];
  const hasPitra = pitraConditions.some(Boolean);
  results.push({
    key: "pitra",
    name: "Pitra Dosh",
    nameHindi: "पितृ दोष",
    icon: "👣",
    severity: hasPitra ? "present" : "absent",
    headline: hasPitra
      ? "Sun–Rahu/Ketu Conjunction — Pitra Dosh Present"
      : "No Pitra Dosh — Ancestors at Peace",
    description: hasPitra
      ? "Pitra Dosh forms when Sun conjuncts Rahu or Ketu. It can indicate ancestral karma and require remediation."
      : "No Pitra Dosh detected. Sun is well-placed and free from Rahu/Ketu conjunction.",
    remedies: hasPitra ? [
      "Perform Pitra Tarpan on Amavasya (new moon day)",
      "Donate food and clothing to brahmins on Pitru Paksha",
      "Recite Pitru Stotra or Gayatri Mantra 108 times daily",
    ] : [],
    planetNote: `Sun: House ${sunH} | Rahu: House ${rahuH}`,
  });

  // ── 4. Gandmool Dosh ──────────────────────────────────────────────────────
  const moonNak = kundli.nakshatra;
  const isGandmool = GANDMOOL_NAKSHATRAS.includes(moonNak);
  results.push({
    key: "gandmool",
    name: "Gandmool Dosh",
    nameHindi: "गंडमूल दोष",
    icon: "🌑",
    severity: isGandmool ? "mild" : "absent",
    headline: isGandmool
      ? `Moon in ${moonNak} — Gandmool Nakshatra`
      : `Moon in ${moonNak} — No Gandmool Dosh`,
    description: isGandmool
      ? "Gandmool Dosh occurs when Moon is in Ashwini, Ashlesha, Magha, Jyeshtha, Mula, or Revati nakshatras."
      : "Moon is in a safe nakshatra. No Gandmool Dosh present.",
    remedies: isGandmool ? [
      "Perform Gandmool Shanti Pooja on the 27th day after birth",
      "Recite Chandra Mantra daily: Om Shram Shreem Shraum Sah Chandraya Namah",
    ] : [],
    planetNote: `Moon Nakshatra: ${moonNak}`,
  });

  // ── 5. Shani Dosh ─────────────────────────────────────────────────────────
  const satRetrograde = pl.find(p => p.name === "Saturn")?.retrograde ?? false;
  const satSign = pl.find(p => p.name === "Saturn")?.sign ?? "";
  const shaniSev: Severity = [1, 4, 7, 8].includes(satH) ? "present"
    : satRetrograde ? "mild"
    : "absent";
  results.push({
    key: "shani",
    name: "Shani Dosh",
    nameHindi: "शनि दोष",
    icon: "😶‍🌫️",
    severity: shaniSev,
    headline: shaniSev !== "absent"
      ? `Saturn in ${satH}th House${satRetrograde ? " (Retrograde)" : ""} — Shani Dosh`
      : `Saturn in ${satH}th House — No Shani Dosh`,
    description: shaniSev !== "absent"
      ? "Saturn in malefic houses or retrograde can create obstacles, delays, and karmic lessons."
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
const SEV_CONFIG: Record<Severity, { color: string; bg: string; label: string; dots: number }> = {
  absent:  { color: "#22c55e", bg: "rgba(34,197,94,0.1)",    label: "Clear",   dots: 0 },
  mild:    { color: "#fbbf24", bg: "rgba(251,191,36,0.1)",   label: "Mild",    dots: 2 },
  present: { color: "#f97316", bg: "rgba(249,115,22,0.1)",   label: "Present", dots: 3 },
  strong:  { color: "#ef4444", bg: "rgba(239,68,68,0.12)",   label: "Strong",  dots: 4 },
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
  const C = useC();

  return (
    <Pressable
      style={[d.card, { borderLeftColor: sev.color, backgroundColor: C.bgCard, borderColor: C.border }]}
      onPress={() => { setOpen(v => !v); Haptics.selectionAsync(); }}
    >
      {/* Header row */}
      <View style={d.cardHeader}>
        <View style={[d.iconBubble, { backgroundColor: sev.bg }]}>
          <Text style={{ fontSize: 16 }}>{dosh.icon}</Text>
        </View>
        <View style={{ flex: 1 }}>
          <Text style={[d.doshName, { color: C.text }]}>{dosh.name}</Text>
          <Text style={[d.doshHindi, { color: C.textMuted }]}>{dosh.nameHindi}</Text>
        </View>
        <View style={[d.sevPill, { backgroundColor: sev.bg }]}>
          <Text style={[d.sevText, { color: sev.color }]}>{sev.label}</Text>
        </View>
        <Feather name={open ? "chevron-up" : "chevron-down"} size={15} color={C.textMuted} style={{ marginLeft: 8 }} />
      </View>

      {/* Headline always visible */}
      <Text style={[d.headline, { color: sev.color }]}>{dosh.headline}</Text>

      {/* Expanded content */}
      {open && (
        <View style={d.expanded}>
          <Text style={[d.desc, { color: C.textMuted }]}>{dosh.description}</Text>

          {dosh.planetNote && (
            <View style={d.planetNoteRow}>
              <Feather name="info" size={10} color={C.textMuted} />
              <Text style={[d.planetNote, { color: C.textMuted }]}>{dosh.planetNote}</Text>
            </View>
          )}

          {dosh.remedies.length > 0 && (
            <View style={d.remediesWrap}>
              <Text style={[d.remediesTitle, { color: C.textMuted }]}>UPAY (REMEDIES)</Text>
              {dosh.remedies.map((r, i) => (
                <View key={i} style={d.remedyRow}>
                  <View style={d.remedyBullet}>
                    <Text style={d.remedyNum}>{i + 1}</Text>
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
          <Text style={[d.subtitle, { color: C.textMuted }]}>दोष विश्लेषण</Text>
        </View>
        {showDemo && (
          <View style={[d.demoBadge, { backgroundColor: C.bgCard2, borderColor: C.border }]}>
            <Text style={[d.demoBadgeText, { color: C.textMuted }]}>Demo</Text>
          </View>
        )}
      </View>

      <View style={d.content}>
        {/* ── Summary ── */}
        <View style={[d.summaryCard, { backgroundColor: C.bgCard, borderColor: C.border }]}>
          <View style={d.summaryRow}>
            <View style={d.summaryItem}>
              <Text style={[d.summaryNum, { color: presentCount > 0 ? "#f97316" : "#22c55e" }]}>{presentCount}</Text>
              <Text style={[d.summaryLabel, { color: C.textMuted }]}>Doshas Found</Text>
            </View>
            <View style={[d.summaryDivider, { backgroundColor: C.border }]} />
            <View style={d.summaryItem}>
              <Text style={[d.summaryNum, { color: strongCount > 0 ? "#ef4444" : "#22c55e" }]}>{strongCount}</Text>
              <Text style={[d.summaryLabel, { color: C.textMuted }]}>Needs Attention</Text>
            </View>
            <View style={[d.summaryDivider, { backgroundColor: C.border }]} />
            <View style={d.summaryItem}>
              <Text style={[d.summaryNum, { color: "#22c55e" }]}>{doshas.length - presentCount}</Text>
              <Text style={[d.summaryLabel, { color: C.textMuted }]}>Clear</Text>
            </View>
          </View>
        </View>

        {/* ── Dosh Cards ── */}
        {doshas.map((dosh, i) => (
          <DoshCard key={dosh.key} dosh={dosh} defaultOpen={i === 0} />
        ))}
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
  backBtn: { width: 36, height: 36, alignItems: "center", justifyContent: "center" },
  title:   { fontSize: 17, fontFamily: "Nunito_700Bold" },
  subtitle:{ fontSize: 11, fontFamily: "Nunito_400Regular", marginTop: 1 },
  demoBadge: {
    paddingHorizontal: 10, paddingVertical: 4,
    borderRadius: 12, borderWidth: 1,
  },
  demoBadgeText: { fontSize: 11, fontFamily: "Nunito_500Medium" },

  content: { paddingHorizontal: 16, paddingTop: 16, gap: 12 },

  summaryCard: {
    borderRadius: 16, borderWidth: 1, padding: 16,
  },
  summaryRow: { flexDirection: "row", alignItems: "center" },
  summaryItem: { flex: 1, alignItems: "center", gap: 4 },
  summaryDivider: { width: 1, height: 32, marginHorizontal: 8 },
  summaryNum: { fontSize: 22, fontFamily: "Nunito_700Bold" },
  summaryLabel: { fontSize: 10, fontFamily: "Nunito_400Regular", textAlign: "center" },

  card: {
    borderRadius: 16, borderWidth: 1, borderLeftWidth: 3,
    padding: 14, gap: 6,
  },
  cardHeader: { flexDirection: "row", alignItems: "center", gap: 10 },
  iconBubble: {
    width: 36, height: 36, borderRadius: 10,
    alignItems: "center", justifyContent: "center",
  },
  doshName:  { fontSize: 13, fontFamily: "Nunito_700Bold" },
  doshHindi: { fontSize: 10, fontFamily: "Nunito_400Regular", marginTop: 1 },
  sevPill: {
    paddingHorizontal: 8, paddingVertical: 3,
    borderRadius: 8,
  },
  sevText: { fontSize: 10, fontFamily: "Nunito_700Bold" },
  headline: { fontSize: 12, fontFamily: "Nunito_600SemiBold", marginLeft: 46 },

  expanded: { marginTop: 4, gap: 10 },
  desc: { fontSize: 12, fontFamily: "Nunito_400Regular", lineHeight: 18 },

  planetNoteRow: { flexDirection: "row", alignItems: "center", gap: 4 },
  planetNote: { fontSize: 10, fontFamily: "Nunito_400Regular" },

  remediesWrap: { gap: 8 },
  remediesTitle: { fontSize: 9, fontFamily: "Nunito_700Bold", letterSpacing: 1.5 },
  remedyRow: { flexDirection: "row", gap: 10, alignItems: "flex-start" },
  remedyBullet: {
    width: 18, height: 18, borderRadius: 9,
    backgroundColor: "rgba(249,115,22,0.15)",
    alignItems: "center", justifyContent: "center",
  },
  remedyNum: { fontSize: 9, fontFamily: "Nunito_700Bold", color: "#f97316" },
  remedyText: { flex: 1, fontSize: 11, fontFamily: "Nunito_400Regular", lineHeight: 16 },
});
