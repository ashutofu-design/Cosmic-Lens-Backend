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
