// ─── Minimal Active Dasha engine for Home card ───────────────────────────────
// Ported from web app proInsightEngine.ts — only what the Home card needs.

export type Trend = "UP" | "DOWN" | "MIXED";

const P_HI: Record<string, string> = {
  Sun:"Surya", Moon:"Chandra", Mars:"Mangal", Mercury:"Budh",
  Jupiter:"Guru", Venus:"Shukra", Saturn:"Shani", Rahu:"Rahu", Ketu:"Ketu",
};

export function pName(planet: string): string {
  return P_HI[planet] ?? planet;
}

// ── Dignity tables ────────────────────────────────────────────────────────────
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

function signOf(lon: number): number { return Math.floor((lon % 360) / 30); }

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
  const base = calcPlanetStrength(planet, kundli);
  const sig  = (DOMAIN_SIGS[domain] ?? []).includes(planet) ? 10 : 0;
  const pd   = kundli.planets.find((p: any) => p.name === planet);
  const hse  = pd && (DOMAIN_HSE[domain] ?? []).includes(pd.house) ? 8 : 0;
  const lagna     = signOf(kundli.ascendantDeg ?? 0);
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

// ─── Extended types for Insights tab ─────────────────────────────────────────

export interface PDForecast {
  planet: string;
  start: Date;
  end: Date;
}

export interface CategoryInsight {
  score: number;
  trend: Trend;
  activePlanet: string;
  text: string;
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
  howItWillGo: string;
  caution: string;
  remedy: string;
}

// Category text templates (English)
const CAT_TEXTS: Record<string, Record<Trend, { main: string; caution: string; remedy: string }>> = {
  career: {
    UP:    { main: "Good career progress is expected. The active planet's energy is supporting your professional goals.", caution: "Avoid overconfidence — careful planning is essential.", remedy: "Practice Surya Namaskar each morning and spend 5 minutes in meditation at midday." },
    DOWN:  { main: "Some challenges may arise in career. Patience and smart decisions will be important.", caution: "Hold off on any major professional decisions for now.", remedy: "Light a sesame oil lamp for Shani and work with honesty and diligence." },
    MIXED: { main: "Career this period will be mixed — some good and some challenging moments.", caution: "Align short-term decisions with your long-term goals.", remedy: "Chant the mantra of the active planet once daily with a mala." },
  },
  relationship: {
    UP:    { main: "Sweetness and understanding will grow in relationships. Love and trust are both strong.", caution: "Keep communication clear and direct — avoid misunderstandings.", remedy: "Offer white flowers to Venus on Fridays." },
    DOWN:  { main: "Some tension may arise in relationships. Work with patience and empathy.", caution: "Avoid major decisions with your partner right now — wait a little.", remedy: "Offer a glass of water with sugar to the Moon daily." },
    MIXED: { main: "Relationships will have a mix of stability and instability. Commitment is key.", caution: "Don't let third-party opinions influence your relationship.", remedy: "Chant 'Om Shukraya Namah' 108 times daily." },
  },
  finance: {
    UP:    { main: "Good opportunities for financial gain. Smart investments can bear fruit in this period.", caution: "Be cautious with speculative investments — don't put everything at stake.", remedy: "Offer turmeric to Jupiter on Thursdays." },
    DOWN:  { main: "Finances may feel a bit tight. Avoid unnecessary expenses.", caution: "Do not lend or borrow large amounts from anyone.", remedy: "Chant the Mars mantra — 'Om Mangalaya Namah' — on Tuesdays." },
    MIXED: { main: "Financial situation will be average. Maintaining balance between income and expenses is essential.", caution: "Consult a financial advisor before making investment decisions.", remedy: "Offer something green to Mercury." },
  },
  health: {
    UP:    { main: "Health will be good. Energy levels are high — set new fitness goals.", caution: "Don't neglect rest and sleep despite having good energy.", remedy: "Take a morning walk daily and eat fresh fruits." },
    DOWN:  { main: "Health may feel slightly fragile. Focus on rest and a proper diet.", caution: "Seek a second opinion before any major medical procedure.", remedy: "Offer water to the Sun daily and drink turmeric milk." },
    MIXED: { main: "Health will be mostly fine — just a little caution is needed.", caution: "Prevent mental stress from converting into physical problems.", remedy: "Read Hanuman Chalisa daily — it boosts immunity and energy." },
  },
};

function makeCategoryText(domain: string, planet: string, trend: Trend, score: number): { text: string; caution: string; remedy: string } {
  const cat = CAT_TEXTS[domain]?.[trend];
  if (!cat) return { text: `Score: ${score}`, caution: "Exercise caution.", remedy: "Chant a mantra daily." };
  return { text: cat.main, caution: cat.caution, remedy: cat.remedy };
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

  const pdStr = calcPlanetStrength(pdPlanet, kundli);
  const adStr = calcPlanetStrength(adPlanet, kundli);
  const mdStr = calcPlanetStrength(md.planet, kundli);

  const makeCategory = (domain: "career" | "relationship" | "finance" | "health"): CategoryInsight => {
    const pdD   = calcDomainScore(pdPlanet, domain, kundli);
    const adD   = calcDomainScore(adPlanet, domain, kundli);
    const final = pdD * 0.7 + adD * 0.3;
    const s100  = toScore100(final);
    const trend = toTrend(s100);
    const txts  = makeCategoryText(domain, pdPlanet, trend, s100);
    return { score: s100, trend, activePlanet: pdPlanet, text: txts.text };
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
const API_BASE_ENGINE = `https://${process.env.EXPO_PUBLIC_DOMAIN ?? ""}`;

interface TransitPositions { [planet: string]: number }
const TRANSIT_BEN = new Set(["Jupiter","Venus"]);
const TRANSIT_MAL = new Set(["Saturn","Rahu","Ketu","Mars"]);

function calcMonthlyTransitAdj(
  transitPos: TransitPositions,
  natalPDSign: number,
  domainHouseSign: number,
): number {
  let adj = 0;
  for (const [planet, lon] of Object.entries(transitPos)) {
    const tSign = signOf(lon);
    if (tSign === natalPDSign || tSign === domainHouseSign) {
      if (TRANSIT_BEN.has(planet)) adj += 5;
      else if (TRANSIT_MAL.has(planet)) adj -= 7;
    }
  }
  return Math.max(-21, Math.min(15, adj));
}

export async function generatePDForecast(
  pdPlanet: string,
  adPlanet: string,
  mdPlanet: string,
  pdStart: Date,
  kundli: any,
  category: "career" | "relationship" | "finance" | "health",
): Promise<MonthForecast> {
  const pdBase  = calcDomainScore(pdPlanet, category, kundli);
  const adBase  = calcDomainScore(adPlanet, category, kundli);
  const weighted = pdBase * 0.7 + adBase * 0.3;
  const baseScore = toScore100(weighted);

  const pdData        = kundli.planets.find((p: any) => p.name === pdPlanet);
  const natalPDSign   = pdData ? signOf(pdData.longitude) : 0;
  const lagna         = signOf(kundli.ascendantDeg ?? 0);
  const keyHouseNum   = (DOMAIN_PRIMARY_HSE[category] ?? 1);
  const domainHouseSgn = (lagna + keyHouseNum - 1) % 12;

  const midMonthDates: string[] = [];
  for (let i = 0; i < 6; i++) {
    const d = new Date(pdStart.getFullYear(), pdStart.getMonth() + i, 15);
    midMonthDates.push(
      `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-15`
    );
  }

  let transitData: TransitPositions[] = midMonthDates.map(() => ({}));
  try {
    const res = await fetch(`${API_BASE_ENGINE}/api/transits`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ dates: midMonthDates }),
    });
    if (res.ok) {
      const data: { date: string; positions: TransitPositions }[] = await res.json();
      transitData = data.map(d => d.positions ?? {});
    }
  } catch { /* use empty transit data */ }

  const months: string[] = [];
  const scores: number[] = [];
  for (let i = 0; i < 6; i++) {
    const monthIdx = (pdStart.getMonth() + i) % 12;
    months.push(MON_ABR[monthIdx]);
    const adj = calcMonthlyTransitAdj(transitData[i] ?? {}, natalPDSign, domainHouseSgn);
    scores.push(Math.max(4, Math.min(96, baseScore + adj)));
  }

  const avgScore = Math.round(scores.reduce((s, x) => s + x, 0) / 6);
  const trend    = toTrend(avgScore);
  const txts     = makeCategoryText(category, pdPlanet, trend, avgScore);

  return { months, scores, trend, avgScore, howItWillGo: txts.text, caution: txts.caution, remedy: txts.remedy };
}

export function computeActiveDasha(kundli: any, moonLon: number): ActiveDashaResult | null {
  const ctx = findCurrentDasha(kundli);
  if (!ctx) return null;
  const { md, ad, pd } = ctx;

  const pdPlanet = pd?.planet ?? ad.planet;
  const adPlanet = ad.planet;

  const pdStr = calcPlanetStrength(pdPlanet, kundli);
  const adStr = calcPlanetStrength(adPlanet, kundli);
  const mdStr = calcPlanetStrength(md.planet, kundli);
  const tStr  = calcTransitScore(moonLon, kundli);

  const pdD   = calcDomainScore(pdPlanet, "career", kundli);
  const adD   = calcDomainScore(adPlanet, "career", kundli);
  const final = pdD * 0.7 + adD * 0.3;
  const s100  = toScore100(final);

  return {
    mdPlanet: md.planet, adPlanet, pdPlanet,
    careerTrend:  toTrend(s100),
    careerScore:  s100,
  };
}
