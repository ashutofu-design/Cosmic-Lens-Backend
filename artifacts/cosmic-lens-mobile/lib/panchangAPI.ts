import { API_BASE, apiFetch } from "./apiConfig";

export interface RealPanchang {
  date: string;
  lat: number; lng: number; tz: number;
  ephemeris: string;
  sunrise: string;
  sunset: string;
  solar_noon: string;
  brahma_muhurta: string;
  abhijit_muhurta: string;
  rahu_kaal: string;
  yamaghanta: string;
  gulika: string;
  tithi?: string;
  tithi_lord?: string;
  tithi_deity?: string;
  nakshatra?: string;
  nakshatra_pada?: number;
  nakshatra_lord?: string;
  yoga?: string;
  yoga_lord?: string;
  karana?: string;
  karana_lord?: string;
  vaar?: string;
  ritu?: string;
  ayana?: string;
  maasa?: string;
  samvatsara?: string;
  eras?: { Shaka_Samvat: number; Vikram_Samvat: number; Kali_Yuga: number; Bengali_Sambat: number };
  phase_r?: any;
  gochar?: GocharResponse;
  muhurat_detail?: DailyMuhurat;
  festivals_today?: MonthlyFestival[];
}

export async function fetchRealPanchang(args: {
  date: Date;
  lat?: number;
  lng?: number;
  tz?: number;     // hours offset, e.g. 5.5
  signal?: AbortSignal;
}): Promise<RealPanchang> {
  const yyyy = args.date.getFullYear();
  const mm = String(args.date.getMonth() + 1).padStart(2, "0");
  const dd = String(args.date.getDate()).padStart(2, "0");
  const params = new URLSearchParams({ date: `${yyyy}-${mm}-${dd}` });
  if (args.lat !== undefined) params.set("lat", String(args.lat));
  if (args.lng !== undefined) params.set("lng", String(args.lng));
  if (args.tz  !== undefined) params.set("tz",  String(args.tz));
  const url = `${API_BASE}/api/panchang?${params.toString()}`;
  const res = await apiFetch(url, { signal: args.signal });
  if (!res.ok) throw new Error(`panchang ${res.status}`);
  return (await res.json()) as RealPanchang;
}

export type VivahMuhuratWindow = {
  start: string;
  end: string;
  score?: number;
  lagna?: string;
  tithi?: string;
  nakshatra?: string;
};

export type VivahMuhuratDay = {
  date: string;
  display?: string;
  weekday?: string;
  tier?: "highly_favorable" | "favorable" | "conditional" | "avoid";
  tier_label?: string;
  confidence?: number;
  score?: number;
  explanation?: string;
  tithi?: string;
  nakshatra?: string;
  jupiter_status?: "Uday" | "Asta";
  venus_status?: "Uday" | "Asta";
  best_windows?: VivahMuhuratWindow[];
  engine_version?: string;
  sunrise?: string;
};

export interface VivahMuhuratScan {
  scan_from: string;
  scan_days: number;
  lat?: number;
  lng?: number;
  tz?: number;
  highly_favorable_count: number;
  favorable_count: number;
  all_shubh_dates: VivahMuhuratDay[];
  highly_favorable: VivahMuhuratDay[];
  favorable: VivahMuhuratDay[];
  disclaimer?: string;
  engine_version?: string;
  estimated_accuracy?: Record<string, string>;
}

/** Minimum slot score for “favorable” tier in vivah-3.0 engine */
export const VIVAH_FAVORABLE_MIN_SCORE = 88;

export function isPremiumVivahDay(d: VivahMuhuratDay): boolean {
  if (d.tier === "highly_favorable") return true;
  if (d.tier === "favorable" && (d.score ?? 0) >= VIVAH_FAVORABLE_MIN_SCORE) return true;
  return false;
}

export interface MarriageDatesScan {
  scan_from: string;
  scan_years: number;
  count: number;
  dates: VivahMuhuratDay[];
  ephemeris?: string;
  engine?: string;
}

export async function fetchMarriageDates(args: {
  fromDate?: Date;
  years?: number;
  tz?: number;
  signal?: AbortSignal;
}): Promise<MarriageDatesScan> {
  const from = args.fromDate ?? new Date();
  const yyyy = from.getFullYear();
  const mm = String(from.getMonth() + 1).padStart(2, "0");
  const dd = String(from.getDate()).padStart(2, "0");
  const params = new URLSearchParams({
    from_date: `${yyyy}-${mm}-${dd}`,
    years: String(args.years ?? 5),
  });
  if (args.tz !== undefined) params.set("tz", String(args.tz));
  const url = `${API_BASE}/api/panchang/marriage-dates?${params.toString()}`;
  const res = await apiFetch(url, { signal: args.signal });
  if (!res.ok) throw new Error(`marriage-dates ${res.status}`);
  return (await res.json()) as MarriageDatesScan;
}

export interface MuhuratPeriod {
  label?: string;
  start: string;
  end: string;
  note?: string;
}

export interface DailyMuhurat {
  date: string;
  sunrise: string;
  sunset: string;
  solar_noon: string;
  brahma_muhurta: MuhuratPeriod;
  abhijit_muhurat: MuhuratPeriod;
  rahu_kaal: MuhuratPeriod;
  gulika_kaal: MuhuratPeriod;
  yamaghanta: MuhuratPeriod;
}

export async function fetchDailyMuhurat(args: {
  date?: Date;
  lat?: number;
  lng?: number;
  tz?: number;
  signal?: AbortSignal;
}): Promise<DailyMuhurat> {
  const d = args.date ?? new Date();
  const yyyy = d.getFullYear();
  const mm = String(d.getMonth() + 1).padStart(2, "0");
  const dd = String(d.getDate()).padStart(2, "0");
  const params = new URLSearchParams({ date: `${yyyy}-${mm}-${dd}` });
  if (args.lat !== undefined) params.set("lat", String(args.lat));
  if (args.lng !== undefined) params.set("lng", String(args.lng));
  if (args.tz !== undefined) params.set("tz", String(args.tz));
  const url = `${API_BASE}/api/panchang/daily-muhurat?${params.toString()}`;
  const res = await apiFetch(url, { signal: args.signal });
  if (!res.ok) throw new Error(`daily-muhurat ${res.status}`);
  return (await res.json()) as DailyMuhurat;
}

export interface TarabalaStrength {
  date: string;
  natal_moon_sign: string;
  natal_nakshatra: string;
  transit_moon_sign: string;
  transit_nakshatra: string;
  tarabala: { ok: boolean; tara: number; tara_name: string; note?: string };
  chandrabala: { ok: boolean; house?: number; note?: string };
  overall_ok: boolean;
  strength_score: number;
  strength_band: string;
}

export async function fetchTarabalaChandrabala(args: {
  natalMoonSign: string;
  natalNakshatra: string;
  date?: Date;
  tz?: number;
  signal?: AbortSignal;
}): Promise<TarabalaStrength> {
  const d = args.date ?? new Date();
  const yyyy = d.getFullYear();
  const mm = String(d.getMonth() + 1).padStart(2, "0");
  const dd = String(d.getDate()).padStart(2, "0");
  const params = new URLSearchParams({
    date: `${yyyy}-${mm}-${dd}`,
    natal_moon_sign: args.natalMoonSign,
    natal_nakshatra: args.natalNakshatra,
  });
  if (args.tz !== undefined) params.set("tz", String(args.tz));
  const url = `${API_BASE}/api/panchang/tarabala-chandrabala?${params.toString()}`;
  const res = await apiFetch(url, { signal: args.signal });
  if (!res.ok) throw new Error(`tarabala-chandrabala ${res.status}`);
  return (await res.json()) as TarabalaStrength;
}

export interface MonthlyFestival {
  date: string;
  festival_name: string;
  tithi: number;
  paksha: "Shukla" | "Krishna" | string;
}

export type EkadashiDay = {
  date: string;
  display: string;
  weekday: string;
  festival_name: string;
  paksha: string;
  tithi: number;
};

export type EkadashiMonth = {
  year: number;
  month: number;
  month_key: string;
  label: string;
  count: number;
  dates: EkadashiDay[];
};

export interface EkadashiSchedule {
  scan_from: string;
  scan_years: number;
  scan_to: string;
  total: number;
  months: EkadashiMonth[];
}

export async function fetchEkadashiSchedule(args: {
  fromDate?: Date;
  years?: number;
  lat?: number;
  lng?: number;
  tz?: number;
  signal?: AbortSignal;
}): Promise<EkadashiSchedule> {
  const from = args.fromDate ?? new Date();
  const yyyy = from.getFullYear();
  const mm = String(from.getMonth() + 1).padStart(2, "0");
  const dd = String(from.getDate()).padStart(2, "0");
  const params = new URLSearchParams({
    from_date: `${yyyy}-${mm}-${dd}`,
    years: String(args.years ?? 5),
  });
  if (args.lat !== undefined) params.set("lat", String(args.lat));
  if (args.lng !== undefined) params.set("lng", String(args.lng));
  if (args.tz !== undefined) params.set("tz", String(args.tz));
  const url = `${API_BASE}/api/panchang/ekadashi-schedule?${params.toString()}`;
  const res = await apiFetch(url, { signal: args.signal });
  if (!res.ok) throw new Error(`ekadashi-schedule ${res.status}`);
  return (await res.json()) as EkadashiSchedule;
}

export async function fetchMonthlyFestivals(args: {
  month: number;
  year: number;
  tz?: number;
  signal?: AbortSignal;
}): Promise<{ month: number; year: number; count: number; festivals: MonthlyFestival[] }> {
  const params = new URLSearchParams({
    month: String(args.month),
    year: String(args.year),
  });
  if (args.tz !== undefined) params.set("tz", String(args.tz));
  const url = `${API_BASE}/api/panchang/monthly-festivals?${params.toString()}`;
  const res = await apiFetch(url, { signal: args.signal });
  if (!res.ok) throw new Error(`monthly-festivals ${res.status}`);
  return (await res.json()) as { month: number; year: number; count: number; festivals: MonthlyFestival[] };
}

export interface GocharPlanet {
  rashi: string;
  degree: number;
  degree_int?: number;
  minute?: number;
  second?: number;
  absolute_longitude?: number;
  rashi_index?: number;
  speed_deg_per_day?: number;
  is_retrograde: boolean;
  motion: string;
  status?: "Uday" | "Asta";
}

export interface GocharResponse {
  timestamp: string;
  planets: Record<string, GocharPlanet>;
  ephemeris?: string;
}

export async function fetchGochar(args: {
  lat?: number;
  lng?: number;
  tz?: number;
  signal?: AbortSignal;
}): Promise<GocharResponse> {
  const params = new URLSearchParams();
  if (args.lat !== undefined) params.set("lat", String(args.lat));
  if (args.lng !== undefined) params.set("lng", String(args.lng));
  if (args.tz !== undefined) params.set("tz", String(args.tz));
  const url = `${API_BASE}/api/panchang/gochar?${params.toString()}`;
  const res = await apiFetch(url, { signal: args.signal });
  if (!res.ok) throw new Error(`gochar ${res.status}`);
  return (await res.json()) as GocharResponse;
}

export async function fetchVivahMuhuratScan(args: {
  fromDate?: Date;
  days?: number;
  years?: number;
  lat: number;
  lng: number;
  tz?: number;
  profile?: string;
  brideNak?: string;
  groomNak?: string;
  brideMoonRashi?: string;
  groomMoonRashi?: string;
  signal?: AbortSignal;
}): Promise<VivahMuhuratScan> {
  const from = args.fromDate ?? new Date();
  const yyyy = from.getFullYear();
  const mm = String(from.getMonth() + 1).padStart(2, "0");
  const dd = String(from.getDate()).padStart(2, "0");
  const params = new URLSearchParams({
    from_date: `${yyyy}-${mm}-${dd}`,
    lat: String(args.lat),
    lng: String(args.lng),
  });
  if (args.years != null) params.set("years", String(args.years));
  else params.set("days", String(args.days ?? 366));
  if (args.tz !== undefined) params.set("tz", String(args.tz));
  if (args.profile) params.set("profile", args.profile);
  if (args.brideNak) params.set("bride_nak", args.brideNak);
  if (args.groomNak) params.set("groom_nak", args.groomNak);
  if (args.brideMoonRashi) params.set("bride_moon_rashi", args.brideMoonRashi);
  if (args.groomMoonRashi) params.set("groom_moon_rashi", args.groomMoonRashi);
  const url = `${API_BASE}/api/panchang/vivah-muhurat?${params.toString()}`;
  const res = await apiFetch(url, { signal: args.signal });
  if (!res.ok) throw new Error(`vivah-muhurat ${res.status}`);
  return (await res.json()) as VivahMuhuratScan;
}

/** Panchang Vivah tab — 5-year scan in yearly chunks (avoids gateway timeout). */
export async function fetchPanchangVivahDates(args: {
  fromDate?: Date;
  years?: number;
  lat: number;
  lng: number;
  tz?: number;
  profile?: string;
  brideNak?: string;
  groomNak?: string;
  brideMoonRashi?: string;
  groomMoonRashi?: string;
  signal?: AbortSignal;
  onProgress?: (yearIndex: number, totalYears: number) => void;
}): Promise<{ dates: VivahMuhuratDay[]; meta: VivahMuhuratScan | null }> {
  const years = args.years ?? 5;
  const from = args.fromDate ?? new Date();
  const byDate = new Map<string, VivahMuhuratDay>();
  let meta: VivahMuhuratScan | null = null;

  for (let i = 0; i < years; i++) {
    args.onProgress?.(i + 1, years);
    const chunkStart = new Date(from);
    chunkStart.setFullYear(from.getFullYear() + i);
    const scan = await fetchVivahMuhuratScan({
      fromDate: chunkStart,
      days: 366,
      lat: args.lat,
      lng: args.lng,
      tz: args.tz,
      profile: args.profile,
      brideNak: args.brideNak,
      groomNak: args.groomNak,
      brideMoonRashi: args.brideMoonRashi,
      groomMoonRashi: args.groomMoonRashi,
      signal: args.signal,
    });
    if (!meta) meta = scan;
    for (const d of [...(scan.highly_favorable || []), ...(scan.favorable || [])]) {
      if (!isPremiumVivahDay(d)) continue;
      const prev = byDate.get(d.date);
      if (!prev || (d.score ?? 0) > (prev.score ?? 0)) byDate.set(d.date, d);
    }
  }

  const dates = [...byDate.values()].sort((a, b) => a.date.localeCompare(b.date));
  return { dates, meta };
}

/** @deprecated Legacy simple scanner — use fetchPanchangVivahDates */
export async function fetchVivahMuhurat(args: {
  fromDate?: Date;
  days?: number;
  lat?: number;
  lng?: number;
  tz?: number;
  signal?: AbortSignal;
}): Promise<VivahMuhuratScan> {
  return fetchVivahMuhuratScan({
    fromDate: args.fromDate,
    days: args.days ?? 180,
    lat: args.lat ?? 28.6139,
    lng: args.lng ?? 77.2090,
    tz: args.tz,
    signal: args.signal,
  });
}
