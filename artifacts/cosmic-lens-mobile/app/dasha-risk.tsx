import { Feather } from "@expo/vector-icons";
import { LinearGradient } from "expo-linear-gradient";
import { router } from "expo-router";
import React, { useMemo } from "react";
import {
  I18nManager,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { CosmicBg } from "@/components/CosmicBg";
import { useC } from "@/context/ThemeContext";
import { useUser } from "@/context/UserContext";
import { computeProInsight, pName } from "@/lib/proInsightEngine";

const F = {
  regular: "Nunito_400Regular",
  semi:    "Nunito_600SemiBold",
  bold:    "Nunito_700Bold",
  extra:   "Nunito_800ExtraBold",
} as const;

// ── Planet nature ─────────────────────────────────────────────────────────────
const MALEFIC  = ["Saturn", "Rahu", "Ketu", "Mars"];
const BENEFIC  = ["Jupiter", "Venus"];

function planetNature(p: string): "malefic" | "benefic" | "neutral" {
  if (MALEFIC.includes(p)) return "malefic";
  if (BENEFIC.includes(p)) return "benefic";
  return "neutral";
}

function natureColor(n: "malefic" | "benefic" | "neutral"): string {
  if (n === "malefic") return "#f97316";
  if (n === "benefic") return "#22c55e";
  return "#facc15";
}

function natureBg(n: "malefic" | "benefic" | "neutral"): string {
  if (n === "malefic") return "rgba(249,115,22,0.12)";
  if (n === "benefic") return "rgba(34,197,94,0.12)";
  return "rgba(250,204,21,0.12)";
}

function natureLabel(n: "malefic" | "benefic" | "neutral"): string {
  if (n === "malefic") return "Challenging";
  if (n === "benefic") return "Favorable";
  return "Mixed";
}

function natureIcon(n: "malefic" | "benefic" | "neutral"): string {
  if (n === "malefic") return "⚠️";
  if (n === "benefic") return "✅";
  return "🌗";
}

// ── Planet emoji icons ────────────────────────────────────────────────────────
const PLANET_EMOJI: Record<string, string> = {
  Sun: "☀️", Moon: "🌙", Mars: "🔴", Mercury: "🟢",
  Jupiter: "🟡", Venus: "⚪", Saturn: "🔵", Rahu: "🌑", Ketu: "🌒",
};

// ── Remaining time formatter ──────────────────────────────────────────────────
function remainingTime(end: Date): string {
  const now  = new Date();
  const diff = end.getTime() - now.getTime();
  if (diff <= 0) return "Khatam ho gaya";
  const days   = Math.floor(diff / 86400000);
  const months = Math.floor(days / 30);
  const years  = Math.floor(months / 12);
  if (years >= 1) {
    const remMonths = months - years * 12;
    return remMonths > 0 ? `${years} sal ${remMonths} mahine baki` : `${years} sal baki`;
  }
  if (months >= 1) {
    const remDays = days - months * 30;
    return remDays > 5 ? `${months} mahine ${remDays} din baki` : `${months} mahine baki`;
  }
  return `${days} din baki`;
}

function fmtDate(d: Date | null | undefined): string {
  if (!d) return "—";
  return d.toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" });
}

// ── MD advice (rule-based) ────────────────────────────────────────────────────
const MD_ADVICE: Record<string, { dos: string[]; donts: string[] }> = {
  Sun: {
    dos:    ["Authority aur leadership roles pursue karein", "Government se judi cheezein shubh hain", "Confidence ke saath apne goals pursue karein"],
    donts:  ["Ego conflicts se bachein", "Pitaji se ya bosses se ladai avoid karein", "Overconfidence se decisions mat lein"],
  },
  Moon: {
    dos:    ["Relationships aur family pe dhyan dein", "Creative aur artistic kaam ke liye accha samay", "Intuition pe bharosa karein"],
    donts:  ["Emotional decisions se bachein", "Abhi bade financial risks mat lein", "Mental stress ko ignore mat karein"],
  },
  Mars: {
    dos:    ["Physical energy high hai — use karein exercise mein", "Competition aur challenges accept karein", "Technical aur engineering kaam ke liye accha"],
    donts:  ["Gusse pe control rakhen — arguments costly ho sakte hain", "Rash decisions aur aggressive investments avoid karein", "Accidents se savdhaan rahein"],
  },
  Mercury: {
    dos:    ["Business, trading aur communication ke liye excellent", "Study aur skill development ke liye best time", "Negotiations aur contracts favorable hain"],
    donts:  ["Details skip mat karein — choti galti bhi nuksaan de sakti hai", "Gossip aur unnecessary baat se bachein", "Overthinking se decision paralysis ho sakta hai"],
  },
  Jupiter: {
    dos:    ["Excellent time — bade decisions lene ke liye accha", "Education, learning aur spiritual growth favorable", "Finance aur investments ke liye guru ka ashirwad hai"],
    donts:  ["Overexpansion se bachein — limits mein rahein", "Ahankaar mat aane dein safalta pe", "Legal matters mein bhi savdhaan rahein"],
  },
  Venus: {
    dos:    ["Relationships aur partnerships ke liye shubh", "Creative arts, music, design ke liye excellent", "Luxuries aur comforts enjoy kar sakte hain"],
    donts:  ["Overspending aur indulgence pe nazar rakhen", "Relationship mein possessiveness avoid karein", "Short-term pleasures ke liye long-term goals sacrifice mat karein"],
  },
  Saturn: {
    dos:    ["Kadi mehnat aur discipline se hi safalta milegi", "Long-term planning aur foundation banane ka samay", "Sabr rakhen — results dheere aayenge par pakke honge"],
    donts:  ["Shortcuts bilkul avoid karein", "High-risk investments mat karein", "Laziness aur procrastination bahut costly hogi is samay"],
  },
  Rahu: {
    dos:    ["Innovation aur unconventional paths try kar sakte hain", "Foreign connections aur new fields explore karein", "Technology aur modern fields ke liye favorable"],
    donts:  ["Illusions aur false promises se savdhaan rahein", "Unethical shortcuts absolutely avoid karein", "Sudden changes se pehle sochein — impulsive decisions risk mein daal sakte hain"],
  },
  Ketu: {
    dos:    ["Spiritual growth aur introspection ke liye excellent", "Puranic knowledge aur meditation ke liye accha samay", "Research aur deep study favorable hai"],
    donts:  ["Material world mein zyada attachment nahi rakhni", "Abrupt decisions se bachein", "Isolation mein mat jaayein — family se connected rahein"],
  },
};

function getAdvice(planet: string) {
  return MD_ADVICE[planet] ?? {
    dos:   ["Current dasha ka pura labh uthayein", "Consistent effort rakhen"],
    donts: ["Impulsive decisions avoid karein"],
  };
}

// ── Domain config ─────────────────────────────────────────────────────────────
const DOMAINS = [
  { key: "career",       label: "Career",       icon: "briefcase" as const,   color: "#60a5fa" },
  { key: "relationship", label: "Rishte",        icon: "heart"    as const,   color: "#f472b6" },
  { key: "finance",      label: "Finance",       icon: "trending-up" as const, color: "#34d399" },
  { key: "health",       label: "Swasthya",      icon: "activity"  as const,  color: "#a78bfa" },
];

// ── Main screen ───────────────────────────────────────────────────────────────
export default function DashaRiskScreen() {
  const insets = useSafeAreaInsets();
  const C      = useC();
  const { kundli, moonData } = useUser();
  const topPad = Platform.OS === "web" ? 67 : insets.top;
  const botPad = Platform.OS === "web" ? 34 : insets.bottom;

  const moonLon = moonData?.longitude ?? 0;
  const insight = useMemo(() => {
    if (!kundli) return null;
    return computeProInsight(kundli, moonLon);
  }, [kundli, moonLon]);

  // Get raw MD/AD dates from kundli.dashas
  const dashaCtx = useMemo(() => {
    if (!kundli?.dashas) return null;
    const now = Date.now();
    for (const md of kundli.dashas) {
      const mdStart = new Date(md.startDate).getTime();
      const mdEnd   = new Date(md.endDate).getTime();
      if (now < mdStart || now >= mdEnd) continue;
      for (const ad of (md.subDashas ?? [])) {
        const adStart = new Date(ad.startDate).getTime();
        const adEnd   = new Date(ad.endDate).getTime();
        if (now < adStart || now >= adEnd) continue;
        let pd: any = null;
        for (const p of (ad.subDashas ?? [])) {
          if (now >= new Date(p.startDate).getTime() && now < new Date(p.endDate).getTime()) {
            pd = p; break;
          }
        }
        return {
          md: { planet: md.planet, start: new Date(md.startDate), end: new Date(md.endDate) },
          ad: { planet: ad.planet, start: new Date(ad.startDate), end: new Date(ad.endDate) },
          pd: pd ? { planet: pd.planet, start: new Date(pd.startDate), end: new Date(pd.endDate) } : null,
        };
      }
    }
    return null;
  }, [kundli]);

  const noData = !kundli || !dashaCtx || !insight;

  return (
    <View style={[s.root, { backgroundColor: C.bg }]}>
      <CosmicBg />

      {/* Header */}
      <View style={[s.header, { paddingTop: topPad + 8 }]}>
        <Pressable style={s.backBtn} onPress={() => router.back()}>
          <Feather
            name={I18nManager.isRTL ? "arrow-right" : "arrow-left"}
            size={22} color={C.text}
          />
        </Pressable>
        <View style={s.headerTitle}>
          <Text style={[s.headerTitleText, { color: C.text }]}>Dasha Alert</Text>
          <Text style={[s.headerSub, { color: C.textDim }]}>Apni current dasha ki poori jaankari</Text>
        </View>
        <View style={s.headerIcon}>
          <Text style={{ fontSize: 22 }}>⚡</Text>
        </View>
      </View>

      <ScrollView
        style={{ flex: 1 }}
        contentContainerStyle={{ paddingBottom: botPad + 24, paddingHorizontal: 16, paddingTop: 16 }}
        showsVerticalScrollIndicator={false}
      >
        {noData ? (
          <NoDataBlock C={C} hasKundli={!!kundli} />
        ) : (
          <>
            {/* Active Dasha Tiers */}
            <SectionLabel label="Abhi Chal Raha Hai" C={C} />
            <DashaTiers ctx={dashaCtx} C={C} />

            {/* Overall Dasha Quality */}
            <SectionLabel label="Is Dasha Ki Nature" C={C} />
            <NatureCard md={dashaCtx.md.planet} ad={dashaCtx.ad.planet} C={C} />

            {/* Domain Impact */}
            <SectionLabel label="Zindagi Ke 4 Kshetra" C={C} />
            <DomainsGrid insight={insight} C={C} />

            {/* MD Advice */}
            <SectionLabel label="Kya Karen · Kya Nahi" C={C} />
            <AdviceCard planet={dashaCtx.md.planet} C={C} />

            {/* Upcoming PDs */}
            {insight.upcomingPDs.length > 0 && (
              <>
                <SectionLabel label="Aage Ke Pratyantar Dasha" C={C} />
                <UpcomingPDs pds={insight.upcomingPDs.slice(0, 4)} C={C} />
              </>
            )}
          </>
        )}
      </ScrollView>
    </View>
  );
}

// ── Section label ─────────────────────────────────────────────────────────────
function SectionLabel({ label, C }: { label: string; C: any }) {
  return (
    <Text style={[s.sectionLabel, { color: C.textDim }]}>{label.toUpperCase()}</Text>
  );
}

// ── No data block ─────────────────────────────────────────────────────────────
function NoDataBlock({ C, hasKundli }: { C: any; hasKundli: boolean }) {
  return (
    <View style={[s.noDataCard, { backgroundColor: C.card, borderColor: C.border }]}>
      <Text style={{ fontSize: 36, marginBottom: 12 }}>🔮</Text>
      <Text style={[s.noDataTitle, { color: C.text }]}>
        {hasKundli ? "Dasha data nahi mila" : "Kundli save nahi ki abhi tak"}
      </Text>
      <Text style={[s.noDataSub, { color: C.textDim }]}>
        {hasKundli
          ? "Kripya apna janam vivaran check karein — dasha dates missing ho sakti hain."
          : "Profile mein janam tithi, samay aur sthan save karein taaki dasha dekh sakein."}
      </Text>
      <Pressable style={s.noDataBtn} onPress={() => router.push("/(tabs)/profile")}>
        <Text style={s.noDataBtnTxt}>Profile Kholein</Text>
      </Pressable>
    </View>
  );
}

// ── Dasha tiers (MD → AD → PD) ───────────────────────────────────────────────
function DashaTiers({ ctx, C }: { ctx: NonNullable<any>; C: any }) {
  return (
    <View style={s.tiersWrap}>
      <DashaTierCard
        tier="Mahadasha"
        planet={ctx.md.planet}
        start={ctx.md.start}
        end={ctx.md.end}
        accent="#c084fc"
        C={C}
        isTop
      />
      <View style={[s.tierConnector, { backgroundColor: C.border }]} />
      <DashaTierCard
        tier="Antardasha"
        planet={ctx.ad.planet}
        start={ctx.ad.start}
        end={ctx.ad.end}
        accent="#60a5fa"
        C={C}
      />
      {ctx.pd && (
        <>
          <View style={[s.tierConnector, { backgroundColor: C.border }]} />
          <DashaTierCard
            tier="Pratyantar Dasha"
            planet={ctx.pd.planet}
            start={ctx.pd.start}
            end={ctx.pd.end}
            accent="#34d399"
            C={C}
          />
        </>
      )}
    </View>
  );
}

function DashaTierCard({
  tier, planet, start, end, accent, C, isTop,
}: {
  tier: string; planet: string; start: Date; end: Date;
  accent: string; C: any; isTop?: boolean;
}) {
  const nature = planetNature(planet);
  const nColor = natureColor(nature);
  return (
    <View style={[s.tierCard, { backgroundColor: C.card, borderColor: C.border },
      isTop && { borderTopWidth: 3, borderTopColor: accent }]}>
      <View style={s.tierLeft}>
        <Text style={{ fontSize: isTop ? 28 : 22 }}>{PLANET_EMOJI[planet] ?? "🪐"}</Text>
      </View>
      <View style={{ flex: 1 }}>
        <Text style={[s.tierLabel, { color: C.textDim }]}>{tier}</Text>
        <Text style={[s.tierPlanet, { color: C.text, fontSize: isTop ? 20 : 17 }]}>
          {pName(planet)}
        </Text>
        <Text style={[s.tierDates, { color: C.textDim }]}>
          {fmtDate(start)} → {fmtDate(end)}
        </Text>
      </View>
      <View style={s.tierRight}>
        <View style={[s.naturePill, { backgroundColor: natureBg(nature), borderColor: nColor + "60" }]}>
          <Text style={[s.naturePillTxt, { color: nColor }]}>{natureLabel(nature)}</Text>
        </View>
        <Text style={[s.tierRemaining, { color: accent }]}>{remainingTime(end)}</Text>
      </View>
    </View>
  );
}

// ── Nature card (MD + AD combined) ───────────────────────────────────────────
function NatureCard({ md, ad, C }: { md: string; ad: string; C: any }) {
  const mdN  = planetNature(md);
  const adN  = planetNature(ad);
  const both = mdN === "malefic" && adN === "malefic";
  const good = mdN === "benefic" && adN === "benefic";
  const overall = both ? "malefic" : good ? "benefic" : "neutral";
  const color = natureColor(overall);
  const bg    = natureBg(overall);
  return (
    <LinearGradient
      colors={both
        ? ["rgba(249,115,22,0.18)", "rgba(239,68,68,0.10)"]
        : good
        ? ["rgba(34,197,94,0.18)", "rgba(74,222,128,0.10)"]
        : ["rgba(250,204,21,0.12)", "rgba(253,224,71,0.06)"]}
      style={[s.natureCard, { borderColor: color + "40" }]}
      start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }}
    >
      <Text style={{ fontSize: 32, marginBottom: 8 }}>{natureIcon(overall)}</Text>
      <Text style={[s.natureBig, { color }]}>
        {both ? "Challenging Period" : good ? "Favorable Period" : "Mixed Period"}
      </Text>
      <Text style={[s.natureSub, { color: C.textDim }]}>
        {both
          ? `${pName(md)} MD + ${pName(ad)} AD — dono hi challenging planets hain. Discipline aur sabr zaroori hai.`
          : good
          ? `${pName(md)} MD + ${pName(ad)} AD — dono hi favorable hain. Yeh ek accha samay hai apne goals pursue karne ka.`
          : `${pName(md)} MD ke saath ${pName(ad)} AD — mixed results milenge. Sawdhaan rehein aur prayaas jaari rakhen.`}
      </Text>
    </LinearGradient>
  );
}

// ── Domains grid ──────────────────────────────────────────────────────────────
function DomainsGrid({ insight, C }: { insight: any; C: any }) {
  return (
    <View style={s.domGrid}>
      {DOMAINS.map((d) => {
        const cat    = insight[d.key];
        const score  = cat?.score ?? 50;
        const trend  = cat?.trend ?? "MIXED";
        const tIcon  = trend === "UP" ? "trending-up" : trend === "DOWN" ? "trending-down" : "minus";
        const tColor = trend === "UP" ? "#22c55e"     : trend === "DOWN" ? "#f97316"       : "#facc15";
        return (
          <View key={d.key} style={[s.domCard, { backgroundColor: C.card, borderColor: C.border }]}>
            <Feather name={d.icon} size={16} color={d.color} />
            <Text style={[s.domLabel, { color: C.textDim }]}>{d.label}</Text>
            <Text style={[s.domScore, { color: d.color }]}>{score}</Text>
            <Feather name={tIcon} size={13} color={tColor} />
          </View>
        );
      })}
    </View>
  );
}

// ── Advice card ───────────────────────────────────────────────────────────────
function AdviceCard({ planet, C }: { planet: string; C: any }) {
  const { dos, donts } = getAdvice(planet);
  return (
    <View style={[s.adviceWrap, { backgroundColor: C.card, borderColor: C.border }]}>
      <View style={s.adviceSection}>
        <Text style={s.adviceHead}>✅  Karein</Text>
        {dos.map((d, i) => (
          <View key={i} style={s.adviceRow}>
            <Text style={[s.adviceDot, { color: "#22c55e" }]}>•</Text>
            <Text style={[s.adviceTxt, { color: C.text }]}>{d}</Text>
          </View>
        ))}
      </View>
      <View style={[s.adviceDivider, { backgroundColor: C.border }]} />
      <View style={s.adviceSection}>
        <Text style={s.adviceHead}>🚫  Nahi Karein</Text>
        {donts.map((d, i) => (
          <View key={i} style={s.adviceRow}>
            <Text style={[s.adviceDot, { color: "#f97316" }]}>•</Text>
            <Text style={[s.adviceTxt, { color: C.text }]}>{d}</Text>
          </View>
        ))}
      </View>
    </View>
  );
}

// ── Upcoming PDs list ─────────────────────────────────────────────────────────
function UpcomingPDs({ pds, C }: { pds: any[]; C: any }) {
  return (
    <View style={[s.upcomingWrap, { backgroundColor: C.card, borderColor: C.border }]}>
      {pds.map((pd, i) => {
        const n     = planetNature(pd.planet);
        const color = natureColor(n);
        const isLast = i === pds.length - 1;
        return (
          <View key={i}>
            <View style={s.upcomingRow}>
              <Text style={{ fontSize: 18, marginRight: 10 }}>{PLANET_EMOJI[pd.planet] ?? "🪐"}</Text>
              <View style={{ flex: 1 }}>
                <Text style={[s.upcomingPlanet, { color: C.text }]}>{pName(pd.planet)}</Text>
                <Text style={[s.upcomingDates, { color: C.textDim }]}>
                  {fmtDate(pd.start)} → {fmtDate(pd.end)}
                </Text>
              </View>
              <View style={[s.naturePill, { backgroundColor: natureBg(n), borderColor: color + "60" }]}>
                <Text style={[s.naturePillTxt, { color }]}>{natureLabel(n)}</Text>
              </View>
            </View>
            {!isLast && <View style={[s.upcomingDivider, { backgroundColor: C.border }]} />}
          </View>
        );
      })}
    </View>
  );
}

// ── Styles ────────────────────────────────────────────────────────────────────
const s = StyleSheet.create({
  root: { flex: 1 },

  header: {
    flexDirection: "row", alignItems: "center", gap: 12,
    paddingHorizontal: 16, paddingBottom: 14,
    borderBottomWidth: 1, borderBottomColor: "rgba(255,255,255,0.06)",
  },
  backBtn:         { padding: 4 },
  headerTitle:     { flex: 1 },
  headerTitleText: { fontFamily: F.bold, fontSize: 18 },
  headerSub:       { fontFamily: F.regular, fontSize: 12, marginTop: 2 },
  headerIcon:      {},

  sectionLabel: {
    fontFamily: F.semi, fontSize: 11, letterSpacing: 1.2,
    marginTop: 20, marginBottom: 10,
  },

  // Tiers
  tiersWrap:     { gap: 0 },
  tierCard: {
    flexDirection: "row", alignItems: "center", gap: 12,
    borderRadius: 14, borderWidth: 1,
    padding: 14, marginBottom: 0,
  },
  tierLeft:       { width: 36, alignItems: "center" },
  tierLabel:      { fontFamily: F.semi, fontSize: 11, letterSpacing: 0.8 },
  tierPlanet:     { fontFamily: F.extra, marginTop: 2 },
  tierDates:      { fontFamily: F.regular, fontSize: 11, marginTop: 3 },
  tierRight:      { alignItems: "flex-end", gap: 6 },
  tierRemaining:  { fontFamily: F.semi, fontSize: 11, textAlign: "right" },
  tierConnector:  { width: 2, height: 12, marginLeft: 30 },

  // Nature card
  natureCard: {
    borderRadius: 16, borderWidth: 1,
    padding: 18, alignItems: "center",
  },
  natureBig:  { fontFamily: F.extra, fontSize: 18, marginBottom: 8 },
  natureSub:  { fontFamily: F.regular, fontSize: 13, textAlign: "center", lineHeight: 20 },

  naturePill: {
    borderRadius: 20, borderWidth: 1,
    paddingHorizontal: 8, paddingVertical: 3,
  },
  naturePillTxt: { fontFamily: F.semi, fontSize: 11 },

  // Domains
  domGrid:  { flexDirection: "row", flexWrap: "wrap", gap: 10 },
  domCard:  {
    width: "47.5%", borderRadius: 14, borderWidth: 1,
    padding: 14, alignItems: "center", gap: 6,
  },
  domLabel: { fontFamily: F.semi, fontSize: 11, letterSpacing: 0.5 },
  domScore: { fontFamily: F.extra, fontSize: 24 },

  // Advice
  adviceWrap: {
    borderRadius: 16, borderWidth: 1, overflow: "hidden",
  },
  adviceSection: { padding: 16 },
  adviceHead:    { fontFamily: F.bold, fontSize: 14, marginBottom: 10 },
  adviceRow:     { flexDirection: "row", gap: 8, marginBottom: 7 },
  adviceDot:     { fontFamily: F.bold, fontSize: 16, lineHeight: 20 },
  adviceTxt:     { fontFamily: F.regular, fontSize: 13, lineHeight: 20, flex: 1 },
  adviceDivider: { height: 1, marginHorizontal: 0 },

  // Upcoming
  upcomingWrap:   { borderRadius: 16, borderWidth: 1, overflow: "hidden" },
  upcomingRow:    { flexDirection: "row", alignItems: "center", padding: 14 },
  upcomingPlanet: { fontFamily: F.bold, fontSize: 14 },
  upcomingDates:  { fontFamily: F.regular, fontSize: 11, marginTop: 3 },
  upcomingDivider:{ height: 1 },

  // No data
  noDataCard: {
    borderRadius: 20, borderWidth: 1,
    padding: 32, alignItems: "center", marginTop: 32,
  },
  noDataTitle: { fontFamily: F.bold, fontSize: 18, textAlign: "center", marginBottom: 10 },
  noDataSub:   { fontFamily: F.regular, fontSize: 14, textAlign: "center", lineHeight: 22 },
  noDataBtn:   {
    marginTop: 20, backgroundColor: "#7c3aed",
    paddingHorizontal: 24, paddingVertical: 12, borderRadius: 24,
  },
  noDataBtnTxt: { fontFamily: F.bold, fontSize: 14, color: "#fff" },
});
