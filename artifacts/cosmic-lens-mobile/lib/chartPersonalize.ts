/**
 * Chart-driven personalization helpers — so Notice / Forecast / Remedies /
 * Lucky / Risk content differ per kundli instead of looking identical on every phone.
 */
import { computeActiveDasha, pName, signOf } from "./proInsightEngine";

const EXALT: Record<string, number> = {
  Sun: 0, Moon: 1, Mars: 9, Mercury: 5, Jupiter: 3, Venus: 11, Saturn: 6, Rahu: 1, Ketu: 7,
};
const DEBIL: Record<string, number> = {
  Sun: 6, Moon: 7, Mars: 3, Mercury: 11, Jupiter: 9, Venus: 5, Saturn: 0, Rahu: 7, Ketu: 1,
};

const SIGN_EN = [
  "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
  "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
];

const PLANET_TO_REMEDY_ID: Record<string, string> = {
  Sun: "surya", Moon: "chandra", Mars: "mangal", Mercury: "budha",
  Jupiter: "guru", Venus: "shukra", Saturn: "shani", Rahu: "rahu", Ketu: "ketu",
};

export type NatalTransitPayload = {
  moon_sign: number;
  pd_planet: string;
  pd_planet_sign: number;
  lagna_sign: number;
  domain_house_signs: {
    career: number;
    finance: number;
    relationship: number;
    health: number;
  };
};

export function natalMoonSignIndex(kundli: any): number {
  const moon = (kundli?.planets ?? []).find((p: any) => p?.name === "Moon");
  if (moon?.longitude != null) return signOf(Number(moon.longitude));
  // fallback from string moonSign if present
  const name = String(kundli?.moonSign ?? "").toLowerCase();
  const idx = SIGN_EN.findIndex((s) => s.toLowerCase() === name);
  return idx >= 0 ? idx : 0;
}

export function natalLagnaSignIndex(kundli: any): number {
  if (kundli?.ascendantDeg != null) return signOf(Number(kundli.ascendantDeg));
  return 0;
}

/** Stable integer unique to this chart (for seeding copy / lucky numbers). */
export function chartSeed(
  kundli: any | null | undefined,
  birthData?: { date?: string; time?: string; dob?: string; name?: string } | null,
): number {
  if (!kundli && !birthData) return 0;
  const moon = kundli ? natalMoonSignIndex(kundli) : 0;
  const lagna = kundli ? natalLagnaSignIndex(kundli) : 0;
  const nak = String(kundli?.nakshatra ?? "");
  let h = moon * 31 + lagna * 97 + nak.length * 13;
  for (let i = 0; i < nak.length; i++) h = (h + nak.charCodeAt(i) * (i + 3)) % 100000;
  const planets: any[] = kundli?.planets ?? [];
  for (const p of planets) {
    h = (h + Math.round(Number(p.longitude ?? 0)) + Number(p.house ?? 0) * 11) % 100000;
  }
  // Birth stamp — same Moon sign charts still diverge by DOB/TOB
  const stamp = [
    birthData?.date || birthData?.dob || "",
    birthData?.time || "",
    birthData?.name || "",
    String(kundli?.ascendantDeg ?? ""),
  ].join("|");
  for (let i = 0; i < stamp.length; i++) {
    h = (h + stamp.charCodeAt(i) * (i + 7)) % 100000;
  }
  return Math.abs(h) || 1;
}

export function buildNatalTransitPayload(kundli: any): NatalTransitPayload {
  const moonSign = natalMoonSignIndex(kundli);
  const lagna = natalLagnaSignIndex(kundli);
  const moonLon =
    (kundli?.planets ?? []).find((p: any) => p?.name === "Moon")?.longitude ?? moonSign * 30;
  const active = computeActiveDasha(kundli, Number(moonLon));
  const pdName = active?.pdPlanet ?? "Jupiter";
  const pdNatal = (kundli?.planets ?? []).find((p: any) => p?.name === pdName);
  const pdSign =
    pdNatal?.longitude != null ? signOf(Number(pdNatal.longitude)) : moonSign;
  return {
    moon_sign: moonSign,
    pd_planet: pdName,
    pd_planet_sign: pdSign,
    lagna_sign: lagna,
    domain_house_signs: {
      career: (lagna + 9) % 12,
      finance: (lagna + 1) % 12,
      relationship: (lagna + 6) % 12,
      health: lagna,
    },
  };
}

/** /api/transits returns a raw array on success, or `{ results }` on error. */
export function parseTransitDayList(data: unknown): TransitDayEntry[] {
  if (Array.isArray(data)) return data as TransitDayEntry[];
  if (data && typeof data === "object" && Array.isArray((data as { results?: unknown }).results)) {
    return (data as { results: TransitDayEntry[] }).results;
  }
  return [];
}

/** Natal baseline 35–75 from chart dignity (not a flat 60 for everyone). */
export function natalBaseScore(kundli: any): number {
  const moonLon =
    (kundli?.planets ?? []).find((p: any) => p?.name === "Moon")?.longitude ?? 0;
  const active = computeActiveDasha(kundli, Number(moonLon));
  if (!active) return 55 + (chartSeed(kundli) % 15);
  // Mix career/finance/relationship/health active scores into a day baseline
  const avg = Math.round(
    (active.careerScore +
      // careerScore is the only exported domain on ActiveDasha — fold chart seed
      (50 + (chartSeed(kundli) % 20))) /
      2,
  );
  return Math.max(35, Math.min(75, avg));
}

export type TransitDayEntry = {
  date: string;
  positions?: Record<string, number | null>;
  domain_impact?: Record<string, number>;
  reasons?: string[];
  sade_sati?: boolean;
  error?: string | null;
};

/** Personalized day score using natal + optional domain_impact from /api/transits. */
export function scorePersonalizedDay(
  entry: TransitDayEntry,
  kundli: any,
  dayOffset: number,
): { score: number; reasons: string[]; sadeSati: boolean } {
  const base = natalBaseScore(kundli);
  const impact = entry?.domain_impact;
  let adj = 0;
  const reasons: string[] = [];

  if (impact && typeof impact === "object") {
    const vals = ["career", "finance", "relationship", "health"]
      .map((k) => Number(impact[k] ?? 0))
      .filter((n) => Number.isFinite(n));
    if (vals.length) {
      adj = Math.round(vals.reduce((a, b) => a + b, 0) / vals.length);
    }
  } else {
    // Fallback when API omitted natal: still seed variation from THIS chart
    const seed = chartSeed(kundli);
    adj = Math.round(Math.sin((dayOffset + 1) * 1.3 + seed * 0.01) * 12);
    const j = entry?.positions?.Jupiter;
    const s = entry?.positions?.Saturn;
    if (j != null) adj += 4;
    if (s != null) adj -= 5;
  }

  if (Array.isArray(entry?.reasons)) {
    for (const r of entry.reasons) {
      if (r && !reasons.includes(r)) reasons.push(r);
    }
  }
  if (entry?.sade_sati) {
    adj -= 8;
    reasons.push("Sade Sati influence active");
  }

  const score = Math.max(10, Math.min(92, Math.round(base + adj)));
  return { score, reasons, sadeSati: !!entry?.sade_sati };
}

export type WeakPlanet = {
  planet: string;
  remedyId: string;
  score: number;
  reason: string;
};

/** Rank planets that need upay — debilitated / dusthana / MD-AD weak. */
export function findWeakPlanets(kundli: any): WeakPlanet[] {
  if (!kundli?.planets?.length) return [];
  const out: WeakPlanet[] = [];
  const moonLon =
    (kundli.planets ?? []).find((p: any) => p?.name === "Moon")?.longitude ?? 0;
  const active = computeActiveDasha(kundli, Number(moonLon));

  for (const p of kundli.planets as any[]) {
    const name = String(p.name ?? "");
    const remedyId = PLANET_TO_REMEDY_ID[name];
    if (!remedyId) continue;
    const sign = signOf(Number(p.longitude ?? 0));
    const house = Number(p.house ?? 0);
    let score = 0;
    const bits: string[] = [];

    if (DEBIL[name] === sign) {
      score += 40;
      bits.push("debilitated");
    }
    if (EXALT[name] === sign) score -= 20;
    if ([6, 8, 12].includes(house)) {
      score += 25;
      bits.push(`house ${house}`);
    }
    if (p.retrograde) {
      score += 10;
      bits.push("retrograde");
    }
    if (active && (name === active.mdPlanet || name === active.adPlanet || name === active.pdPlanet)) {
      if (score > 0) {
        score += 15;
        bits.push("active dasha lord");
      }
    }
    if (score >= 25) {
      out.push({
        planet: name,
        remedyId,
        score,
        reason: bits.join(" · ") || "stressed",
      });
    }
  }

  out.sort((a, b) => b.score - a.score);
  return out;
}

export type ChartNotice = {
  dot: string;
  icon: "alert-triangle" | "calendar" | "moon" | "zap" | "trending-up" | "star" | "activity" | "shield";
  title: string;
  desc: string;
  time: string;
};

function daysUntil(iso: unknown): number | null {
  if (!iso) return null;
  const t = new Date(iso as string).getTime();
  if (!Number.isFinite(t)) return null;
  return Math.ceil((t - Date.now()) / 86400000);
}

/** Build notice feed from THIS user's kundli — never shared DEMO text. */
export function buildNoticesFromKundli(kundli: any | null | undefined, lang: "en" | "hn" | "hi" = "hn"): ChartNotice[] {
  if (!kundli?.planets?.length) {
    return [
      {
        dot: "#a78bfa",
        icon: "star",
        title: lang === "hi" ? "कुंडली जोड़ें" : "Kundli add karein",
        desc:
          lang === "hi"
            ? "अपनी जन्म कुंडली जोड़ें — तभी व्यक्तिगत सूचनाएँ मिलेंगी।"
            : "Apni janam kundli add karein — tabhi personal alerts milenge.",
        time: lang === "hi" ? "अभी" : "Abhi",
      },
    ];
  }

  const notices: ChartNotice[] = [];
  const moonLon =
    (kundli.planets ?? []).find((p: any) => p?.name === "Moon")?.longitude ?? 0;
  const active = computeActiveDasha(kundli, Number(moonLon));
  const moon = (kundli.planets ?? []).find((p: any) => p?.name === "Moon");
  const seed = chartSeed(kundli);
  const lagna = natalLagnaSignIndex(kundli);

  if (active) {
    const md = pName(active.mdPlanet);
    const ad = pName(active.adPlanet);
    const pd = pName(active.pdPlanet);
    notices.push({
      dot: "#fbbf24",
      icon: "zap",
      title: lang === "hi" ? "आपकी सक्रिय दशा" : "Aapki active dasha",
      desc:
        lang === "hi"
          ? `महादशा ${md} · अंतरदशा ${ad} · प्रत्यंतर ${pd}. यही आपकी मौजूदा ऊर्जा की कुंजी है।`
          : `Mahadasha ${md} · Antardasha ${ad} · Pratyantar ${pd}. Yahi aapki current energy ki key hai.`,
      time: lang === "hi" ? "आज" : "Aaj",
    });

    // Upcoming AD end if available on dasha tree
    const now = Date.now();
    for (const mdNode of kundli.dashas ?? []) {
      const mdStart = new Date(mdNode.startDate).getTime();
      const mdEnd = new Date(mdNode.endDate).getTime();
      if (now < mdStart || now >= mdEnd) continue;
      for (const adNode of mdNode.subDashas ?? []) {
        const a0 = new Date(adNode.startDate).getTime();
        const a1 = new Date(adNode.endDate).getTime();
        if (now < a0 || now >= a1) continue;
        const left = daysUntil(adNode.endDate);
        if (left != null && left >= 0 && left <= 45) {
          notices.push({
            dot: "#ef4444",
            icon: "alert-triangle",
            title: lang === "hi" ? "दशा बदलाव नज़दीक" : "Dasha change nazdeek",
            desc:
              lang === "hi"
                ? `${pName(adNode.planet)} अंतरदशा लगभग ${left} दिन में समाप्त — ऊर्जा में साफ बदलाव संभव।`
                : `${pName(adNode.planet)} Antardasha ~${left} din mein khatam — energy mein clear shift mumkin.`,
            time: left <= 7 ? (lang === "hi" ? "जल्द" : "Jaldi") : `${left}d`,
          });
        }
        break;
      }
      break;
    }
  }

  if (moon?.house) {
    const h = Number(moon.house);
    const sensitive = [6, 8, 12].includes(h);
    notices.push({
      dot: sensitive ? "#ef4444" : "#4ade80",
      icon: "moon",
      title: lang === "hi" ? "चंद्र भाव संकेत" : "Moon house sanket",
      desc: sensitive
        ? lang === "hi"
          ? `जन्म चंद्र ${h} भाव में है — भावनात्मक सावधानी और स्वास्थ्य पर ज़्यादा ध्यान दें।`
          : `Janam Chandra ${h} bhaav mein hai — emotional caution aur health pe zyada dhyan dein.`
        : lang === "hi"
          ? `जन्म चंद्र ${h} भाव में स्थिर है — मन और निर्णय की नींव यहीं से पढ़ें।`
          : `Janam Chandra ${h} bhaav mein sthir hai — mind aur decisions ki base yahi se padhein.`,
      time: lang === "hi" ? "कुंडली" : "Kundli",
    });
  }

  const weak = findWeakPlanets(kundli).slice(0, 2);
  for (const w of weak) {
    notices.push({
      dot: "#f59e0b",
      icon: "shield",
      title: lang === "hi" ? `${pName(w.planet)} उपाय ज़रूरी` : `${pName(w.planet)} upay zaroori`,
      desc:
        lang === "hi"
          ? `${pName(w.planet)} तनाव में (${w.reason}). Remedies टैब में इसके उपाय देखें।`
          : `${pName(w.planet)} stress mein (${w.reason}). Remedies tab mein iske upay dekhein.`,
      time: lang === "hi" ? "व्यक्तिगत" : "Personal",
    });
  }

  notices.push({
    dot: "#a78bfa",
    icon: "trending-up",
    title: lang === "hi" ? "लग्न फोकस" : "Lagna focus",
    desc:
      lang === "hi"
        ? `आपका लग्न ${SIGN_EN[lagna]} है · नक्षत्र ${kundli.nakshatra || "—"}. Insights में साप्ताहिक ब्रेकडाउन देखें।`
        : `Aapka Lagna ${SIGN_EN[lagna]} hai · Nakshatra ${kundli.nakshatra || "—"}. Insights mein weekly breakdown dekhein.`,
    time: lang === "hi" ? "प्रोफ़ाइल" : "Profile",
  });

  // Keep list stable but chart-unique order hint via seed
  if (notices.length > 3 && seed % 2 === 1) {
    const [a, b] = notices;
    notices[0] = b;
    notices[1] = a;
  }

  return notices.slice(0, 6);
}

/** Map weekday hint to dasha lord so different charts get different daily lines. */
export function dashaAwareHintIndex(kundli: any, fallbackWeekday: number): number {
  const moonLon =
    (kundli?.planets ?? []).find((p: any) => p?.name === "Moon")?.longitude ?? 0;
  const active = computeActiveDasha(kundli, Number(moonLon));
  if (!active) return fallbackWeekday % 7;
  const map: Record<string, number> = {
    Sun: 0, Moon: 1, Mars: 2, Mercury: 3, Jupiter: 4, Venus: 5, Saturn: 6, Rahu: 6, Ketu: 2,
  };
  return map[active.pdPlanet] ?? map[active.adPlanet] ?? fallbackWeekday % 7;
}
