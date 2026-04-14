import type { KundliData, PlanetInfo } from "@/types";

const TABLE: Record<string, number[][]> = {
  Sun:     [[1,2,4,7,8,9,10,11],[3,6,10,11],[1,2,4,7,8,9,10,11],[3,5,6,9,10,11,12],[5,6,9,11],[6,7,12],[1,2,4,7,8,9,10,11],[3,4,6,10,11,12]],
  Moon:    [[3,6,7,8,10,11],[1,3,6,7,10,11],[2,3,5,6,9,10,11],[1,3,4,5,7,8,10,11],[1,4,7,8,10,11],[3,4,5,7,9,10,11],[3,5,6,11],[3,6,10,11]],
  Mars:    [[3,5,6,10,11],[3,6,11],[1,2,4,7,8,10,11],[3,5,6,11],[6,10,11,12],[6,8,11,12],[1,4,7,8,9,10,11],[1,3,6,10,11]],
  Mercury: [[5,6,9,11,12],[2,4,6,8,10,11],[1,2,4,7,8,9,10,11],[1,3,5,6,9,10,11,12],[6,8,11,12],[1,2,3,4,5,8,9,11],[1,2,4,7,8,9,10,11],[1,2,4,6,8,10,11]],
  Jupiter: [[1,2,3,4,7,8,9,10,11],[2,5,7,9,11],[1,2,4,7,8,10,11],[1,2,4,5,6,9,10,11],[1,2,3,4,7,8,10,11],[2,5,6,9,10,11],[3,5,6,12],[1,2,4,5,6,7,9,10,11]],
  Venus:   [[8,11,12],[1,2,3,4,5,8,9,11,12],[3,5,6,9,11,12],[3,5,6,9,11],[5,8,9,10,11],[1,2,3,4,5,8,9,10,11],[3,4,5,8,9,10,11],[1,2,3,4,5,8,9,11]],
  Saturn:  [[1,2,4,7,8,10,11],[3,6,11],[3,5,6,10,11,12],[6,8,9,10,11,12],[5,6,11,12],[6,11,12],[3,5,6,11],[1,3,4,6,10,11]],
};

const PLANETS = ["Sun","Moon","Mars","Mercury","Jupiter","Venus","Saturn"];

const NAKSHATRAS = [
  "Ashwini","Bharani","Krittika","Rohini","Mrigashira","Ardra",
  "Punarvasu","Pushya","Ashlesha","Magha","Purva Phalguni","Uttara Phalguni",
  "Hasta","Chitra","Swati","Vishakha","Anuradha","Jyeshtha",
  "Mula","Purva Ashadha","Uttara Ashadha","Shravana","Dhanishtha",
  "Shatabhisha","Purva Bhadrapada","Uttara Bhadrapada","Revati",
];

const TARA_BASE = [60, 85, 35, 80, 45, 88, 30, 75, 95];

function sarvaForHouse(house: number, planets: PlanetInfo[], lagnaRashi: number): number {
  const rashiOf: Record<string, number> = {};
  for (const p of planets) {
    if (PLANETS.includes(p.name)) rashiOf[p.name] = (lagnaRashi + p.house - 1) % 12;
  }
  const srcRashis = [...PLANETS.map(n => rashiOf[n] ?? 0), lagnaRashi];
  const hRashi = (lagnaRashi + house - 1) % 12;
  return PLANETS.reduce((sum, planet) => {
    let bindu = 0;
    for (let c = 0; c < 8; c++) {
      const rel = ((hRashi - srcRashis[c] + 12) % 12) + 1;
      if (TABLE[planet]?.[c]?.includes(rel)) bindu++;
    }
    return sum + bindu;
  }, 0);
}

export function computeTodayEnergy(
  moonLon: number,
  moonRashiIdx: number,
  kundli: KundliData,
): number | null {
  try {
    const lagnaRashi = Math.floor(kundli.ascendantDeg / 30) % 12;
    const moonHouse = (moonRashiIdx - lagnaRashi + 12) % 12 + 1;
    const nakIdx = Math.floor(moonLon / (360 / 27)) % 27;
    const birthNakIdx = NAKSHATRAS.indexOf(kundli.nakshatra ?? "");
    if (birthNakIdx < 0) return null;

    const tara = ((nakIdx - birthNakIdx + 27) % 27) % 9;
    const taraBase = TARA_BASE[tara] ?? 50;

    const moonSarva = sarvaForHouse(moonHouse, kundli.planets, lagnaRashi);
    const ashtakaScore = Math.min(100, Math.max(0, Math.round((moonSarva / 8) * 100)));

    const raw = taraBase * 0.55 + ashtakaScore * 0.45;
    return Math.round(Math.min(100, Math.max(1, raw)));
  } catch {
    return null;
  }
}

export function gradColor(t: number): string {
  const STOPS = [
    { t: 0.00, r: 255, g: 59,  b: 59  },
    { t: 0.25, r: 255, g: 140, b: 0   },
    { t: 0.45, r: 255, g: 215, b: 0   },
    { t: 0.60, r: 0,   g: 212, b: 255 },
    { t: 1.00, r: 0,   g: 255, b: 153 },
  ];
  let a = STOPS[0], b = STOPS[STOPS.length - 1];
  for (let k = 0; k < STOPS.length - 1; k++) {
    if (t >= STOPS[k].t && t <= STOPS[k + 1].t) { a = STOPS[k]; b = STOPS[k + 1]; break; }
  }
  const r = (b.t - a.t) === 0 ? 0 : (t - a.t) / (b.t - a.t);
  const ri = Math.round(a.r + (b.r - a.r) * r);
  const gi = Math.round(a.g + (b.g - a.g) * r);
  const bi = Math.round(a.b + (b.b - a.b) * r);
  return `rgb(${ri},${gi},${bi})`;
}
