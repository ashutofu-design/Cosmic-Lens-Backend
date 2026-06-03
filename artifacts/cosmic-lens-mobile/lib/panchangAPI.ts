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
};

export interface VivahMuhuratScan {
  scan_from: string;
  scan_days: number;
  highly_favorable_count: number;
  favorable_count: number;
  all_shubh_dates: VivahMuhuratDay[];
  highly_favorable: VivahMuhuratDay[];
  favorable: VivahMuhuratDay[];
  disclaimer?: string;
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

/** @deprecated Prefer fetchMarriageDates — kept for legacy vivah-muhurat payloads */
export async function fetchVivahMuhurat(args: {
  fromDate?: Date;
  days?: number;
  lat?: number;
  lng?: number;
  tz?: number;
  signal?: AbortSignal;
}): Promise<VivahMuhuratScan> {
  const scan = await fetchMarriageDates({
    fromDate: args.fromDate,
    years: 5,
    tz: args.tz,
    signal: args.signal,
  });
  const dates = scan.dates.map((d) => ({
    ...d,
    tier: "favorable" as const,
    tier_label: "Shubh",
    display: d.date.slice(8, 10) + " " + ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"][parseInt(d.date.slice(5, 7), 10) - 1],
    weekday: "",
    confidence: 90,
    score: 85,
  }));
  return {
    scan_from: scan.scan_from,
    scan_days: scan.scan_years * 365,
    highly_favorable_count: 0,
    favorable_count: scan.count,
    all_shubh_dates: dates,
    highly_favorable: [],
    favorable: dates,
  };
}
