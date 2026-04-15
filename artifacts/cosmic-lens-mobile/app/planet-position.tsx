import { Feather } from "@expo/vector-icons";
import { router } from "expo-router";
import * as Haptics from "expo-haptics";
import React, { useMemo, useState } from "react";
import {
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
import { pName } from "@/lib/proInsightEngine";

// ── Static tables ─────────────────────────────────────────────────────────────

const SIGNS = [
  "Mesh (Aries)","Vrishabh (Taurus)","Mithun (Gemini)","Kark (Cancer)",
  "Simha (Leo)","Kanya (Virgo)","Tula (Libra)","Vrishchik (Scorpio)",
  "Dhanu (Sagittarius)","Makar (Capricorn)","Kumbh (Aquarius)","Meen (Pisces)",
];
const SIGNS_SHORT = [
  "Mesh","Vrishabh","Mithun","Kark","Simha","Kanya",
  "Tula","Vrishchik","Dhanu","Makar","Kumbh","Meen",
];
const NAKSHATRAS = [
  "Ashwini","Bharani","Krittika","Rohini","Mrigashira","Ardra","Punarvasu","Pushya",
  "Ashlesha","Magha","Purva Phalguni","Uttara Phalguni","Hasta","Chitra","Swati",
  "Vishakha","Anuradha","Jyeshtha","Mula","Purva Ashadha","Uttara Ashadha","Shravana",
  "Dhanishtha","Shatabhisha","Purva Bhadrapada","Uttara Bhadrapada","Revati",
];
const NAK_LORDS = [
  "Ketu","Venus","Sun","Moon","Mars","Rahu","Jupiter","Saturn","Mercury",
  "Ketu","Venus","Sun","Moon","Mars","Rahu","Jupiter","Saturn","Mercury",
  "Ketu","Venus","Sun","Moon","Mars","Rahu","Jupiter","Saturn","Mercury",
];
const EXALT: Record<string, { sign: string; deg: number }> = {
  Sun:{sign:"Mesh",deg:10}, Moon:{sign:"Vrishabh",deg:3}, Mars:{sign:"Makar",deg:28},
  Mercury:{sign:"Kanya",deg:15}, Jupiter:{sign:"Kark",deg:5}, Venus:{sign:"Meen",deg:27},
  Saturn:{sign:"Tula",deg:20}, Rahu:{sign:"Vrishabh",deg:20}, Ketu:{sign:"Vrishchik",deg:20},
};
const DEBIL: Record<string, string> = {
  Sun:"Tula", Moon:"Vrishchik", Mars:"Kark", Mercury:"Meen",
  Jupiter:"Makar", Venus:"Kanya", Saturn:"Mesh", Rahu:"Vrishchik", Ketu:"Vrishabh",
};
const OWN: Record<string, string[]> = {
  Sun:["Simha"], Moon:["Kark"], Mars:["Mesh","Vrishchik"],
  Mercury:["Mithun","Kanya"], Jupiter:["Dhanu","Meen"],
  Venus:["Vrishabh","Tula"], Saturn:["Makar","Kumbh"],
};
const KARAKA: Record<string, string[]> = {
  Sun:["Atma","Pita","Satta","Tej","Hriday"],
  Moon:["Mann","Mata","Bhaavna","Jal","Rakta"],
  Mars:["Sahas","Bhratra","Bhoomi","Urja","Kshatra"],
  Mercury:["Buddhi","Vaani","Vyaapaar","Tvacha","Yukti"],
  Jupiter:["Gyaan","Santan","Dharma","Dhan","Guru"],
  Venus:["Prem","Patni","Kala","Vaibhav","Kidney"],
  Saturn:["Karma","Anushasan","Ayu","Seva","Daant"],
  Rahu:["Videsh","Tantra","Maya","Achank","Obsession"],
  Ketu:["Adhyatm","Moksha","Poorvajanm","Ekant","Gyan"],
};
const PLANET_CLR: Record<string, string> = {
  Sun:"#f59e0b", Moon:"#94a3b8", Mars:"#ef4444", Mercury:"#10b981",
  Jupiter:"#facc15", Venus:"#ec4899", Saturn:"#a78bfa",
  Rahu:"#f59e0b", Ketu:"#fb923c",
};
const PLANET_GLYPH: Record<string, string> = {
  Sun:"☉", Moon:"☽", Mars:"♂", Mercury:"☿", Jupiter:"♃",
  Venus:"♀", Saturn:"♄", Rahu:"☊", Ketu:"☋",
};

// ── Helpers ───────────────────────────────────────────────────────────────────

function nakshatra(lon: number) {
  const size = 360 / 27;
  const idx = Math.floor(lon / size) % 27;
  const pada = Math.floor((lon % size) / (size / 4)) + 1;
  return { name: NAKSHATRAS[idx], pada, lord: NAK_LORDS[idx] };
}

function signStatus(planet: string, lon: number): { label: string; color: string } {
  const signIdx = Math.floor(lon / 30) % 12;
  const sign = SIGNS_SHORT[signIdx];
  if (EXALT[planet]?.sign === sign) return { label: "Uchch (Exalted)", color: "#4ade80" };
  if (DEBIL[planet] === sign)        return { label: "Neech (Debilitated)", color: "#ef4444" };
  if (OWN[planet]?.includes(sign))   return { label: "Svagriha (Own)", color: "#f59e0b" };
  return { label: "Saamaanya (Normal)", color: "#3d5a7a" };
}

function houseCategory(h: number): { label: string; color: string } {
  if ([1,4,7,10].includes(h))  return { label: "Kendra", color: "#4ade80" };
  if ([5,9].includes(h))       return { label: "Trikona", color: "#f59e0b" };
  if ([6,8,12].includes(h))    return { label: "Dusthana", color: "#ef4444" };
  return { label: "Madhyam", color: "#fbbf24" };
}

function angDist(a: number, b: number): number {
  const d = Math.abs(a - b) % 360;
  return d > 180 ? 360 - d : d;
}

// DEMO kundli when no real data
const DEMO_KUNDLI = {
  planets: [
    { name: "Sun",     sign: "Tula",      degrees: "12°34'", house: 1, longitude: 192.57, retrograde: false, speed: 1.01 },
    { name: "Moon",    sign: "Makar",     degrees: "5°18'",  house: 4, longitude: 275.3,  retrograde: false, speed: 13.2 },
    { name: "Mars",    sign: "Simha",     degrees: "20°10'", house: 11, longitude: 140.17, retrograde: false, speed: 0.52 },
    { name: "Mercury", sign: "Tula",      degrees: "3°45'",  house: 1, longitude: 183.75, retrograde: true,  speed: -0.3 },
    { name: "Jupiter", sign: "Meen",      degrees: "15°22'", house: 6, longitude: 345.37, retrograde: false, speed: 0.07 },
    { name: "Venus",   sign: "Kanya",     degrees: "8°50'",  house: 12, longitude: 158.83, retrograde: false, speed: 1.22 },
    { name: "Saturn",  sign: "Kumbh",     degrees: "2°30'",  house: 5, longitude: 302.5,  retrograde: true,  speed: -0.06 },
    { name: "Rahu",    sign: "Vrishabh",  degrees: "18°0'",  house: 8, longitude: 48.0,   retrograde: true,  speed: -0.05 },
    { name: "Ketu",    sign: "Vrishchik", degrees: "18°0'",  house: 2, longitude: 228.0,  retrograde: true,  speed: -0.05 },
  ],
  ascendantDeg: 192.0,
  rashi: "Tula",
};

// ── Planet Card ───────────────────────────────────────────────────────────────
function PlanetCard({
  planet, lagnaIdx, sunLon,
}: {
  planet: { name: string; sign: string; degrees: string; house: number; longitude: number; retrograde?: boolean; speed?: number };
  lagnaIdx: number;
  sunLon: number;
}) {
  const C = useC();
  const [open, setOpen] = useState(false);
  const clr = PLANET_CLR[planet.name] ?? "#f59e0b";
  const nak = nakshatra(planet.longitude);
  const status = signStatus(planet.name, planet.longitude);
  const houseCat = houseCategory(planet.house);
  const karaka = KARAKA[planet.name] ?? [];

  // Combustion check
  let combustLabel = "";
  if (planet.name !== "Sun" && planet.name !== "Rahu" && planet.name !== "Ketu") {
    const dist = angDist(sunLon, planet.longitude);
    const thresholds: Record<string, number> = {
      Moon:12, Mars:17, Mercury:14, Jupiter:11, Venus:10, Saturn:15
    };
    const thr = thresholds[planet.name] ?? 12;
    if (dist <= thr) combustLabel = `☁️ Asta (${dist.toFixed(1)}° from Sun)`;
  }

  const degFmt = `${(planet.longitude % 30).toFixed(1)}°`;

  return (
    <Pressable
      style={[s.card, { backgroundColor: C.bgCard, borderColor: open ? `${clr}55` : C.border }]}
      onPress={() => { setOpen(!open); Haptics.selectionAsync(); }}
    >
      {/* Header row */}
      <View style={s.cardHeader}>
        <View style={[s.glyph, { backgroundColor: `${clr}15`, borderColor: `${clr}30` }]}>
          <Text style={[s.glyphText, { color: clr }]}>{PLANET_GLYPH[planet.name] ?? "★"}</Text>
        </View>
        <View style={s.cardInfo}>
          <View style={s.nameRow}>
            <Text style={[s.planetName, { color: clr }]}>{pName(planet.name)}</Text>
            {planet.retrograde && <Text style={s.retroBadge}>℞</Text>}
            {combustLabel !== "" && <Text style={s.combustBadge}>☁️ Asta</Text>}
          </View>
          <Text style={[s.cardSub, { color: C.textMuted }]}>
            {SIGNS_SHORT[Math.floor(planet.longitude/30)%12]} · {degFmt} · H{planet.house}
          </Text>
        </View>
        <View style={s.cardRight}>
          <View style={[s.statusBadge, { borderColor: `${status.color}44` }]}>
            <Text style={[s.statusText, { color: status.color }]}>{status.label.split(" ")[0]}</Text>
          </View>
          <Feather name={open ? "chevron-up" : "chevron-down"} size={14} color={C.textMuted} />
        </View>
      </View>

      {/* Expanded details */}
      {open && (
        <View style={s.details}>
          <View style={[s.divider, { backgroundColor: C.border }]} />

          <Row label="Rashi (Sign)" value={SIGNS[Math.floor(planet.longitude/30)%12]} />
          <Row label="Nakshatra" value={`${nak.name} Pada ${nak.pada}`} />
          <Row label="Nakshatra Swami" value={pName(nak.lord)} />
          <Row label="Longitude" value={`${planet.longitude.toFixed(2)}°`} />
          <Row label="Speed" value={planet.speed != null ? `${planet.speed.toFixed(2)}°/day` : "—"} />
          <Row label="Gati" value={planet.retrograde ? "Vakri (Retrograde)" : "Margi (Direct)"} clrValue={planet.retrograde ? "#fbbf24" : "#4ade80"} />
          <Row label="Avastha (House)" value={houseCat.label} clrValue={houseCat.color} />
          <Row label="Dignity" value={status.label} clrValue={status.color} />
          {combustLabel !== "" && <Row label="Asta" value={combustLabel} clrValue="#ef4444" />}

          {karaka.length > 0 && (
            <View style={s.karakaRow}>
              <Text style={[s.karakaLabel, { color: C.textMuted }]}>Karaka:</Text>
              <Text style={[s.karakaValue, { color: C.textMid }]}>{karaka.join(", ")}</Text>
            </View>
          )}
        </View>
      )}
    </Pressable>
  );
}

function Row({ label, value, clrValue }: { label: string; value: string; clrValue?: string }) {
  const C = useC();
  return (
    <View style={[s.row, { borderBottomColor: C.border }]}>
      <Text style={[s.rowLabel, { color: C.textMuted }]}>{label}</Text>
      <Text style={[s.rowValue, { color: C.textMid }, clrValue ? { color: clrValue } : {}]}>{value}</Text>
    </View>
  );
}

// ── Main Screen ───────────────────────────────────────────────────────────────
export default function PlanetPositionScreen() {
  const insets = useSafeAreaInsets();
  const C = useC();
  const { kundli } = useUser();
  const topPad = Platform.OS === "web" ? 67 : insets.top;
  const botPad = Platform.OS === "web" ? 34 : insets.bottom;
  const showDemo = !kundli;

  const data = showDemo ? DEMO_KUNDLI : kundli;
  const rawPlanets = data?.planets ?? [];
  const planets = rawPlanets.map(p => ({
    ...p,
    sign: p.sign ?? SIGNS_SHORT[Math.floor((p.longitude ?? 0) / 30) % 12],
    degrees: p.degrees ?? `${Math.floor((p.longitude ?? 0) % 30)}°${Math.floor(((p.longitude ?? 0) % 1) * 60)}'`,
  }));
  const lagnaIdx = Math.floor(((data as any)?.ascendantDeg ?? 0) / 30) % 12;
  const lagnaSign = SIGNS[lagnaIdx];
  const sunLon = planets.find(p => p.name === "Sun")?.longitude ?? 0;

  return (
    <View style={[s.root, { paddingTop: topPad, backgroundColor: C.bg }]}>
      {/* Header */}
      <View style={[s.header, { borderBottomColor: C.border }]}>
        <Pressable onPress={() => router.back()} style={s.back}>
          <Feather name="arrow-left" size={20} color={C.textMid} />
        </Pressable>
        <View style={{ flex: 1 }}>
          <Text style={[s.headerTitle, { color: C.text }]}>Planet Position</Text>
          <Text style={[s.headerSub, { color: C.textMuted }]}>Lagna: {lagnaSign}</Text>
        </View>
        {showDemo && (
          <View style={s.demoPill}>
            <Text style={s.demoPillText}>Demo</Text>
          </View>
        )}
      </View>

      <ScrollView contentContainerStyle={[s.content, { paddingBottom: botPad + 30 }]} showsVerticalScrollIndicator={false}>
        {/* Demo banner */}
        {showDemo && (
          <Pressable style={[s.demoBanner, { backgroundColor: C.warningBg, borderColor: C.warningBorder }]} onPress={() => router.push("/onboarding")}>
            <Feather name="lock" size={12} color={C.warningText} />
            <Text style={[s.demoText, { color: C.warningText }]}>Sample data — Apni kundli banao exact positions ke liye</Text>
            <Feather name="chevron-right" size={12} color={C.warningText} />
          </Pressable>
        )}

        {/* Planet cards */}
        {planets.map(p => (
          <PlanetCard key={p.name} planet={p} lagnaIdx={lagnaIdx} sunLon={sunLon} />
        ))}

        {/* Legend */}
        <View style={[s.legend, { backgroundColor: C.bgCard, borderColor: C.border }]}>
          {[
            { label: "Kendra", color: "#4ade80", desc: "Houses 1,4,7,10" },
            { label: "Trikona", color: "#f59e0b", desc: "Houses 5,9" },
            { label: "Dusthana", color: "#ef4444", desc: "Houses 6,8,12" },
            { label: "Madhyam", color: "#fbbf24", desc: "Others" },
          ].map(l => (
            <View key={l.label} style={s.legendItem}>
              <View style={[s.legendDot, { backgroundColor: l.color }]} />
              <Text style={[s.legendLabel, { color: C.textMuted }]}>{l.label}</Text>
              <Text style={[s.legendDesc, { color: C.textMid }]}>{l.desc}</Text>
            </View>
          ))}
        </View>
      </ScrollView>
    </View>
  );
}

const s = StyleSheet.create({
  root: { flex: 1, backgroundColor: "#020d1a" },
  header: {
    flexDirection: "row", alignItems: "center",
    paddingHorizontal: 16, paddingBottom: 12, paddingTop: 12, gap: 10,
    borderBottomWidth: 1, borderBottomColor: "rgba(255,255,255,0.04)",
  },
  back:        { padding: 4 },
  headerTitle: { color: "#dde8f4", fontSize: 18, fontWeight: "700" },
  headerSub:   { color: "#3d5a7a", fontSize: 11 },
  demoPill: {
    backgroundColor: "rgba(251,191,36,0.15)", borderRadius: 10,
    paddingHorizontal: 8, paddingVertical: 2, borderWidth: 1, borderColor: "rgba(251,191,36,0.3)",
  },
  demoPillText: { color: "#fbbf24", fontSize: 10, fontWeight: "600" },

  content: { padding: 16, gap: 12 },

  demoBanner: {
    flexDirection: "row", alignItems: "center", gap: 8,
    backgroundColor: "rgba(251,191,36,0.07)", borderRadius: 12,
    borderWidth: 1, borderColor: "rgba(251,191,36,0.2)",
    paddingHorizontal: 14, paddingVertical: 10,
  },
  demoText: { color: "#fbbf24", fontSize: 11, flex: 1 },

  card: {
    backgroundColor: "#040e1f", borderRadius: 18,
    borderWidth: 1.5, padding: 14,
  },
  cardHeader: { flexDirection: "row", alignItems: "center", gap: 12 },
  glyph: {
    width: 40, height: 40, borderRadius: 20,
    borderWidth: 1, alignItems: "center", justifyContent: "center",
  },
  glyphText: { fontSize: 18 },
  cardInfo:  { flex: 1 },
  nameRow:   { flexDirection: "row", alignItems: "center", gap: 6 },
  planetName: { fontSize: 15, fontWeight: "700" },
  retroBadge: { color: "#fbbf24", fontSize: 12, fontWeight: "700" },
  combustBadge: { fontSize: 10 },
  cardSub:   { color: "#3d5a7a", fontSize: 11, marginTop: 2 },
  cardRight: { alignItems: "flex-end", gap: 6 },
  statusBadge: {
    borderWidth: 1, borderRadius: 8, paddingHorizontal: 7, paddingVertical: 2,
  },
  statusText: { fontSize: 10, fontWeight: "600" },

  details: { gap: 0 },
  divider: { height: 1, backgroundColor: "#071525", marginVertical: 10 },
  row: {
    flexDirection: "row", justifyContent: "space-between", alignItems: "flex-start",
    paddingVertical: 5, borderBottomWidth: 1, borderBottomColor: "#071525",
  },
  rowLabel: { color: "#3d5a7a", fontSize: 11, flex: 1 },
  rowValue: { color: "#94a3b8", fontSize: 11, textAlign: "right", fontWeight: "500", flex: 1 },

  karakaRow: { flexDirection: "row", gap: 8, paddingVertical: 8, flexWrap: "wrap" },
  karakaLabel: { color: "#3d5a7a", fontSize: 11 },
  karakaValue: { color: "#475569", fontSize: 11, flex: 1 },

  legend: {
    backgroundColor: "#040e1f", borderRadius: 14,
    borderWidth: 1, borderColor: "rgba(255,255,255,0.04)",
    padding: 14, gap: 8,
  },
  legendItem: { flexDirection: "row", alignItems: "center", gap: 8 },
  legendDot:  { width: 8, height: 8, borderRadius: 4 },
  legendLabel: { color: "#94a3b8", fontSize: 12, width: 70, fontWeight: "600" },
  legendDesc:  { color: "#3d5a7a", fontSize: 11 },
});
