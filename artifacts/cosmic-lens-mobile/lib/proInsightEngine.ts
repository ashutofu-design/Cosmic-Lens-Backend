import { API_BASE as API_BASE_ENGINE, apiFetch } from "./apiConfig";

export type Trend = "UP" | "DOWN" | "MIXED";

const P_HI: Record<string, string> = {
  Sun:"Surya", Moon:"Chandra", Mars:"Mangal", Mercury:"Budh",
  Jupiter:"Guru", Venus:"Shukra", Saturn:"Shani", Rahu:"Rahu", Ketu:"Ketu",
};

export function pName(planet: string): string {
  return P_HI[planet] ?? planet;
}

// ── Dignity tables ─────────────────────────────────────────────────────────────
const EXALT: Record<string, number>  = { Sun:0, Moon:1, Mars:9, Mercury:5, Jupiter:3, Venus:11, Saturn:6, Rahu:1, Ketu:7 };
const DEBIL: Record<string, number>  = { Sun:6, Moon:7, Mars:3, Mercury:11, Jupiter:9, Venus:5, Saturn:0, Rahu:7, Ketu:1 };
const OWN:   Record<string, number[]> = {
  Sun:[4], Moon:[3], Mars:[0,7], Mercury:[2,5],
  Jupiter:[8,11], Venus:[1,6], Saturn:[9,10], Rahu:[], Ketu:[],
};
const SIGN_LORDS = [
  "Mars","Venus","Mercury","Moon","Sun","Mercury",
  "Venus","Mars","Jupiter","Saturn","Saturn","Jupiter",
];
const PL_FRIENDS: Record<string, string[]> = {
  Sun:["Moon","Mars","Jupiter"], Moon:["Sun","Mercury"],
  Mars:["Sun","Moon","Jupiter"], Mercury:["Sun","Venus"],
  Jupiter:["Sun","Moon","Mars"], Venus:["Mercury","Saturn"],
  Saturn:["Mercury","Venus"], Rahu:["Venus","Saturn","Mercury"],
  Ketu:["Venus","Saturn","Mercury"],
};
const PL_ENEMIES: Record<string, string[]> = {
  Sun:["Saturn","Venus"], Moon:[], Mars:["Mercury"], Mercury:["Moon"],
  Jupiter:["Mercury","Venus"], Venus:["Sun","Moon"],
  Saturn:["Sun","Moon","Mars"], Rahu:["Sun","Moon","Mars"], Ketu:["Sun","Moon","Mars"],
};
const NAT_BEN = new Set(["Jupiter","Venus","Moon","Mercury"]);
const NAT_MAL = new Set(["Saturn","Mars","Rahu","Ketu"]);
const NAKSHATRAS = [
  "Ashwini","Bharani","Krittika","Rohini","Mrigashira","Ardra","Punarvasu","Pushya",
  "Ashlesha","Magha","Purva Phalguni","Uttara Phalguni","Hasta","Chitra","Swati",
  "Vishakha","Anuradha","Jyeshtha","Mula","Purva Ashadha","Uttara Ashadha","Shravana",
  "Dhanishtha","Shatabhisha","Purva Bhadrapada","Uttara Bhadrapada","Revati",
];
const TARA_SCORES = [0, 1, -1.5, 0.8, -0.8, 1.5, -2, 0.5, 2];
const DOMAIN_SIGS: Record<string, string[]> = { career:["Sun","Saturn"], finance:["Jupiter","Venus"], relationship:["Venus","Moon"], health:["Mars","Sun"] };
const DOMAIN_HSE:  Record<string, number[]>  = { career:[10,6], finance:[2,11], relationship:[7,5], health:[1,6] };
const DOMAIN_PRIMARY_HSE: Record<string, number> = { career:10, finance:2, relationship:7, health:1 };

export function signOf(lon: number): number { return Math.floor((lon % 360) / 30); }

// ── Divisional chart mapping ───────────────────────────────────────────────────
// Relationship → D9 (Navamsha), Career → D10 (Dashamsha), Finance/Health → D1.
// The backend `kundli.divisionalCharts.{D9,D10}` gives sign placements for all
// 9 planets + ascendant in those charts. We build a pseudo-kundli here so all
// existing strength/aspect helpers work unchanged on the divisional chart.
const DOMAIN_CHART: Record<string, "D1" | "D9" | "D10"> = {
  career:       "D10",
  relationship: "D9",
  finance:      "D1",
  health:       "D1",
};

export function chartForDomain(domain: string): "D1" | "D9" | "D10" {
  return DOMAIN_CHART[domain] ?? "D1";
}

function getDomainChart(kundli: any, domain: string): any {
  const which = chartForDomain(domain);
  if (which === "D1") return kundli;

  const varga = kundli?.divisionalCharts?.[which];
  if (!varga || !Array.isArray(varga.planets)) return kundli;  // graceful fallback

  // Build a pseudo-kundli: signs become sign-start longitudes (×30) so
  // signOf(), aspect math and dignity helpers all behave correctly; house
  // numbers come from the varga itself; retrograde copied from D1 (not a
  // divisional concept — retrograde is physical motion).
  const ascIdx = varga.ascendantSignIndex ?? 0;
  const planets = varga.planets.map((vp: any) => {
    const d1 = (kundli.planets ?? []).find((x: any) => x.name === vp.name);
    return {
      name:       vp.name,
      longitude:  vp.signIndex * 30,
      house:      vp.house,
      retrograde: d1?.retrograde ?? false,
    };
  });
  return {
    ascendantDeg: ascIdx * 30,
    nakshatra:    kundli.nakshatra,     // nakshatra is D1-only
    planets,
  };
}

function toDate(d: unknown): Date {
  if (d instanceof Date) return d;
  return new Date(d as string);
}

function houseScore(h: number): number {
  if ([1,4,7,10].includes(h)) return 10;
  if ([5,9].includes(h))      return 8;
  if ([6,8,12].includes(h))   return -10;
  return 0;
}

function signScore(planet: string, lon: number): number {
  const sign = signOf(lon);
  if (EXALT[planet] === sign)                    return 12;
  if (DEBIL[planet] === sign)                    return -12;
  if ((OWN[planet] ?? []).includes(sign))        return 10;
  const lord = SIGN_LORDS[sign];
  if ((PL_FRIENDS[planet] ?? []).includes(lord)) return 6;
  if ((PL_ENEMIES[planet] ?? []).includes(lord)) return -6;
  return 0;
}

function aspectsReceived(planet: string, kundli: any): { ben: string[]; mal: string[] } {
  const tgt = kundli.planets.find((p: any) => p.name === planet);
  if (!tgt) return { ben: [], mal: [] };
  const ts = signOf(tgt.longitude);
  const ben: string[] = [], mal: string[] = [];
  for (const p of kundli.planets) {
    if (p.name === planet) continue;
    const ps = signOf(p.longitude);
    const d  = (ts - ps + 12) % 12;
    const hits = d === 6 ||
      (p.name === "Mars"    && (d === 3 || d === 7)) ||
      (p.name === "Jupiter" && (d === 4 || d === 8)) ||
      (p.name === "Rahu"    && (d === 4 || d === 8)) ||
      (p.name === "Saturn"  && (d === 2 || d === 9));
    if (hits) {
      if (NAT_BEN.has(p.name)) ben.push(p.name);
      else if (NAT_MAL.has(p.name)) mal.push(p.name);
    }
  }
  return { ben, mal };
}

function aspectScore(planet: string, kundli: any): number {
  const { ben, mal } = aspectsReceived(planet, kundli);
  return Math.max(-20, Math.min(20, ben.length * 8 + mal.length * (-10)));
}

function conjScore(planet: string, kundli: any): number {
  const tgt = kundli.planets.find((p: any) => p.name === planet);
  if (!tgt) return 0;
  let sc = 0;
  for (const p of kundli.planets) {
    if (p.name === planet || p.house !== tgt.house) continue;
    if (NAT_BEN.has(p.name)) sc += 6; else if (NAT_MAL.has(p.name)) sc -= 8;
  }
  return Math.max(-16, Math.min(16, sc));
}

function funcScore(planet: string, lagnaSign: number): number {
  const lorded: number[] = [];
  for (let h = 1; h <= 12; h++) {
    if (SIGN_LORDS[(lagnaSign + h - 1) % 12] === planet) lorded.push(h);
  }
  const hasGood = lorded.some(h => [1,2,4,5,7,9,10,11].includes(h));
  const hasDust = lorded.some(h => [6,8,12].includes(h));
  if (hasGood && !hasDust) return 8;
  if (hasDust && !hasGood) return -8;
  return 0;
}

function specScore(planet: string, kundli: any): number {
  const pd = kundli.planets.find((p: any) => p.name === planet);
  if (!pd) return 0;
  let sc = pd.retrograde ? -5 : 0;
  if (planet !== "Sun") {
    const sun = kundli.planets.find((p: any) => p.name === "Sun");
    if (sun && Math.min(Math.abs(pd.longitude - sun.longitude), 360 - Math.abs(pd.longitude - sun.longitude)) < 10) sc -= 5;
  }
  return sc;
}

function calcPlanetStrength(planet: string, kundli: any): number {
  const pd = kundli.planets.find((p: any) => p.name === planet);
  if (!pd) return 0;
  const lagna = signOf(kundli.ascendantDeg ?? 0);
  return Math.max(-50, Math.min(50,
    houseScore(pd.house) + signScore(planet, pd.longitude) +
    aspectScore(planet, kundli) + conjScore(planet, kundli) +
    funcScore(planet, lagna) + specScore(planet, kundli)
  ));
}

function hasAspect(pName: string, pSign: number, targetSign: number): boolean {
  const d = (targetSign - pSign + 12) % 12;
  return d === 6 ||
    (pName === "Mars"    && (d === 3 || d === 7)) ||
    (pName === "Jupiter" && (d === 4 || d === 8)) ||
    (pName === "Rahu"    && (d === 4 || d === 8)) ||
    (pName === "Saturn"  && (d === 2 || d === 9));
}

function calcDomainScore(planet: string, domain: string, kundli: any): number {
  // Relationship judged on D9, career on D10, others on D1. All helpers
  // (strength, aspect, house, conjunction) run on the domain-appropriate chart.
  const chart = getDomainChart(kundli, domain);
  const base = calcPlanetStrength(planet, chart);
  const sig  = (DOMAIN_SIGS[domain] ?? []).includes(planet) ? 10 : 0;
  const pd   = chart.planets.find((p: any) => p.name === planet);
  const hse  = pd && (DOMAIN_HSE[domain] ?? []).includes(pd.house) ? 8 : 0;
  const lagna     = signOf(chart.ascendantDeg ?? 0);
  const houseSign = (lagna + (DOMAIN_PRIMARY_HSE[domain] ?? 1) - 1) % 12;
  const asp5 = pd && hasAspect(planet, signOf(pd.longitude), houseSign) ? 5 : 0;
  return base + sig + hse + asp5;
}

function calcTransitScore(moonLon: number, kundli: any): number {
  const moonNakIdx  = Math.floor(moonLon / (360 / 27)) % 27;
  const birthNakIdx = NAKSHATRAS.indexOf(kundli.nakshatra ?? "");
  if (birthNakIdx < 0) return 0;
  return TARA_SCORES[((moonNakIdx - birthNakIdx + 27) % 27) % 9];
}

function toScore100(raw: number): number { return Math.max(0, Math.min(100, Math.round(50 + raw))); }
function toTrend(score: number): Trend { return score >= 65 ? "UP" : score <= 40 ? "DOWN" : "MIXED"; }

function findCurrentDasha(kundli: any): { md: any; ad: any; pd: any | null } | null {
  const now = Date.now();
  for (const md of (kundli.dashas ?? [])) {
    if (now < toDate(md.startDate).getTime() || now >= toDate(md.endDate).getTime()) continue;
    for (const ad of (md.subDashas ?? [])) {
      if (now < toDate(ad.startDate).getTime() || now >= toDate(ad.endDate).getTime()) continue;
      let pd = null;
      for (const p of (ad.subDashas ?? [])) {
        if (now >= toDate(p.startDate).getTime() && now < toDate(p.endDate).getTime()) { pd = p; break; }
      }
      return { md, ad, pd };
    }
  }
  return null;
}

export interface ActiveDashaResult {
  mdPlanet: string; adPlanet: string; pdPlanet: string;
  careerTrend: Trend; careerScore: number;
}

// ─── Extended types for Insights tab ──────────────────────────────────────────

export interface PDForecast {
  planet: string;
  start: Date;
  end: Date;
}

export interface CategoryInsight {
  score: number;
  trend: Trend;
  activePlanet: string;
}

export interface ProInsight {
  mdPlanet: string; adPlanet: string; pdPlanet: string;
  pdStart: Date | null; pdEnd: Date | null;
  career: CategoryInsight;
  relationship: CategoryInsight;
  finance: CategoryInsight;
  health: CategoryInsight;
  upcomingPDs: PDForecast[];
}

export interface MonthForecast {
  months: string[];
  scores: number[];
  trend: Trend;
  avgScore: number;
  reasons: string[];
  sadeSati: boolean;
  transitError: boolean;
}

// ── Natal strength descriptions (rule-based, no templates) ────────────────────

export function buildNatalReasons(
  pdPlanet: string,
  adPlanet: string,
  mdPlanet: string,
  domain: string,
  kundli: any,
): string[] {
  const reasons: string[] = [];

  // Use domain-appropriate chart (D9 for relationship, D10 for career) so
  // dignity, house placement, and retrograde comments reflect the varga
  // responsible for that life area.
  const chart     = getDomainChart(kundli, domain);
  const chartName = chartForDomain(domain);
  const chartTag  = chartName === "D1" ? "" : ` in ${chartName}`;

  const pd = chart.planets.find((p: any) => p.name === pdPlanet);
  if (pd) {
    const str = calcPlanetStrength(pdPlanet, chart);
    const EXALT_SIGN: Record<string,number> = { Sun:0, Moon:1, Mars:9, Mercury:5, Jupiter:3, Venus:11, Saturn:6, Rahu:1, Ketu:7 };
    const DEBIL_SIGN: Record<string,number> = { Sun:6, Moon:7, Mars:3, Mercury:11, Jupiter:9, Venus:5, Saturn:0, Rahu:7, Ketu:1 };
    const pdSign = signOf(pd.longitude);
    if (EXALT_SIGN[pdPlanet] === pdSign)
      reasons.push(`PD lord ${pName(pdPlanet)} is exalted${chartTag} — natal strength very high for ${domain}`);
    else if (DEBIL_SIGN[pdPlanet] === pdSign)
      reasons.push(`PD lord ${pName(pdPlanet)} is debilitated${chartTag} — natal ${domain} energy is weakened`);
    if (pd.retrograde)
      reasons.push(`PD lord ${pName(pdPlanet)} is retrograde — results may be delayed or internalised`);
    if ([1,4,7,10].includes(pd.house))
      reasons.push(`PD lord ${pName(pdPlanet)} placed in kendra (house ${pd.house}${chartTag}) — strong foundation for ${domain}`);
    else if ([5,9].includes(pd.house))
      reasons.push(`PD lord ${pName(pdPlanet)} in trikona (house ${pd.house}${chartTag}) — dharmic support for ${domain}`);
    else if ([6,8,12].includes(pd.house))
      reasons.push(`PD lord ${pName(pdPlanet)} in dusthana (house ${pd.house}${chartTag}) — obstacles in ${domain} area`);
    if (str >= 25)
      reasons.push(`Natal PD lord ${pName(pdPlanet)}${chartTag} is strongly dignified — base score for ${domain} boosted`);
    else if (str <= -20)
      reasons.push(`Natal PD lord ${pName(pdPlanet)}${chartTag} is under significant stress — ${domain} baseline lowered`);
  }

  const adData = chart.planets.find((p: any) => p.name === adPlanet);
  if (adData) {
    const adStr = calcPlanetStrength(adPlanet, chart);
    if (adStr >= 20)
      reasons.push(`AD lord ${pName(adPlanet)}${chartTag} is well-placed — supportive secondary influence on ${domain}`);
    else if (adStr <= -15)
      reasons.push(`AD lord ${pName(adPlanet)}${chartTag} is challenged — friction from secondary dasha layer`);
  }

  if ((DOMAIN_SIGS[domain] ?? []).includes(pdPlanet))
    reasons.push(`${pName(pdPlanet)} is a natural significator of ${domain} — direct activation`);

  return reasons;
}

function calcUpcomingPDs(ctx: { md: any; ad: any; pd: any | null }): PDForecast[] {
  const { ad } = ctx;
  const pds: any[] = ad.subDashas ?? [];
  const now = Date.now();
  const idx = pds.findIndex(
    (p) => now >= toDate(p.startDate).getTime() && now < toDate(p.endDate).getTime()
  );
  const start = idx >= 0 ? idx : 0;
  return pds.slice(start, start + 9).map((p) => ({
    planet: p.planet,
    start:  toDate(p.startDate),
    end:    toDate(p.endDate),
  }));
}

export function computeProInsight(kundli: any, moonLon: number): ProInsight | null {
  const ctx = findCurrentDasha(kundli);
  if (!ctx) return null;
  const { md, ad, pd } = ctx;

  const pdPlanet = pd?.planet ?? ad.planet;
  const adPlanet = ad.planet;

  const makeCategory = (domain: "career" | "relationship" | "finance" | "health"): CategoryInsight => {
    const pdD   = calcDomainScore(pdPlanet, domain, kundli);
    const adD   = calcDomainScore(adPlanet, domain, kundli);
    const final = pdD * 0.7 + adD * 0.3;
    const s100  = toScore100(final);
    const trend = toTrend(s100);
    return { score: s100, trend, activePlanet: pdPlanet };
  };

  return {
    mdPlanet: md.planet, adPlanet, pdPlanet,
    pdStart:  pd ? toDate(pd.startDate) : null,
    pdEnd:    pd ? toDate(pd.endDate)   : null,
    career:       makeCategory("career"),
    relationship: makeCategory("relationship"),
    finance:      makeCategory("finance"),
    health:       makeCategory("health"),
    upcomingPDs:  calcUpcomingPDs(ctx),
  };
}

const MON_ABR = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];

// ── Transit API response types ─────────────────────────────────────────────────
interface TransitEntry {
  date: string;
  positions: Record<string, number | null>;
  domain_impact?: Record<string, number>;
  reasons?: string[];
  sade_sati?: boolean;
  error?: string | null;
}

export async function generatePDForecast(
  pdPlanet: string,
  adPlanet: string,
  mdPlanet: string,
  pdStart: Date,
  kundli: any,
  category: "career" | "relationship" | "finance" | "health",
): Promise<MonthForecast> {
  const pdBase    = calcDomainScore(pdPlanet, category, kundli);
  const adBase    = calcDomainScore(adPlanet, category, kundli);
  const weighted  = pdBase * 0.7 + adBase * 0.3;
  const baseScore = toScore100(weighted);

  const lagna        = signOf(kundli.ascendantDeg ?? 0);
  const moonPlanet   = (kundli.planets ?? []).find((p: any) => p.name === "Moon");
  const moonSign     = moonPlanet ? signOf(moonPlanet.longitude) : 0;

  // Build per-domain natal context: relationship on D9, career on D10, else D1.
  // Each domain carries its own PD-lord sign, primary-house sign, and lagna
  // drawn from the chart that classically governs that area of life.
  const DOMAINS = ["career", "finance", "relationship", "health"] as const;
  const domainContext: Record<string, { pd_sign: number; house_sign: number; lagna_sign: number; chart: "D1"|"D9"|"D10" }> = {} as any;
  for (const d of DOMAINS) {
    const ch       = getDomainChart(kundli, d);
    const chartId  = chartForDomain(d);
    const pdInCh   = (ch.planets ?? []).find((p: any) => p.name === pdPlanet);
    const chLagna  = signOf(ch.ascendantDeg ?? 0);
    const pdSignCh = pdInCh ? signOf(pdInCh.longitude) : 0;
    const houseSgn = (chLagna + (DOMAIN_PRIMARY_HSE[d] ?? 1) - 1) % 12;
    domainContext[d] = {
      pd_sign:    pdSignCh,
      house_sign: houseSgn,
      lagna_sign: chLagna,
      chart:      chartId,
    };
  }

  const midMonthDates: string[] = [];
  for (let i = 0; i < 6; i++) {
    const d = new Date(pdStart.getFullYear(), pdStart.getMonth() + i, 15);
    midMonthDates.push(
      `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2,"0")}-15`
    );
  }

  const natalPayload = {
    moon_sign:      moonSign,        // D1 — Sade Sati reference
    pd_planet:      pdPlanet,
    lagna_sign:     lagna,           // D1 lagna — reason labels fallback
    domain_context: domainContext,   // per-domain D9/D10/D1 overrides
  };

  let transitEntries: TransitEntry[] = [];
  let transitError = false;

  try {
    const res = await apiFetch(`${API_BASE_ENGINE}/api/transits`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ dates: midMonthDates, natal: natalPayload }),
    });
    if (!res.ok) {
      const errBody = await res.text().catch(() => `HTTP ${res.status}`);
      console.error("[Transit API] HTTP error:", res.status, errBody);
      transitError = true;
    } else {
      const data: TransitEntry[] = await res.json();
      transitEntries = data;
      const anyCalcError = data.some(e => e.error != null);
      if (anyCalcError) {
        console.warn("[Transit API] Partial errors in response:", data.filter(e => e.error).map(e => `${e.date}: ${e.error}`));
        transitError = anyCalcError;
      }
    }
  } catch (err) {
    console.error("[Transit API] Network / parse failure:", err);
    transitError = true;
  }

  const months: string[] = [];
  const scores: number[] = [];
  const allReasons: string[] = [];
  let sadeSati = false;

  for (let i = 0; i < 6; i++) {
    const monthIdx = (pdStart.getMonth() + i) % 12;
    months.push(MON_ABR[monthIdx]);

    const entry = transitEntries[i];
    let adj = 0;

    if (!transitError && entry && !entry.error && entry.domain_impact) {
      adj = entry.domain_impact[category] ?? 0;
    }

    if (!transitError && entry) {
      if (entry.sade_sati) sadeSati = true;
      for (const r of (entry.reasons ?? [])) {
        if (!allReasons.includes(r)) allReasons.push(r);
      }
    }

    scores.push(Math.max(4, Math.min(96, baseScore + adj)));
  }

  const natalReasons = buildNatalReasons(pdPlanet, adPlanet, mdPlanet, category, kundli);
  for (const r of natalReasons) {
    if (!allReasons.includes(r)) allReasons.push(r);
  }

  const avgScore = Math.round(scores.reduce((s, x) => s + x, 0) / 6);
  const trend    = toTrend(avgScore);

  return {
    months,
    scores,
    trend,
    avgScore,
    reasons: allReasons,
    sadeSati,
    transitError,
  };
}

export function computeActiveDasha(kundli: any, moonLon: number): ActiveDashaResult | null {
  const ctx = findCurrentDasha(kundli);
  if (!ctx) return null;
  const { md, ad, pd } = ctx;

  const pdPlanet = pd?.planet ?? ad.planet;
  const adPlanet = ad.planet;

  const pdD   = calcDomainScore(pdPlanet, "career", kundli);
  const adD   = calcDomainScore(adPlanet, "career", kundli);
  const final = pdD * 0.7 + adD * 0.3;
  const s100  = toScore100(final);

  return {
    mdPlanet: md.planet, adPlanet, pdPlanet,
    careerTrend: toTrend(s100),
    careerScore: s100,
  };
}
