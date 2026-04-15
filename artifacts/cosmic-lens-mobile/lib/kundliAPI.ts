import type { BirthData, KundliData } from "@/types";

import { API_BASE as BASE_URL, apiFetch } from "./apiConfig";

async function attemptKundliFetch(bd: BirthData, timeoutMs: number): Promise<KundliData> {
  const ctrl  = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), timeoutMs);
  try {
    const res = await apiFetch(`${BASE_URL}/api/kundli`, {
      method: "POST",
      body: JSON.stringify({
        name:   bd.name,
        day:    bd.day,
        month:  bd.month,
        year:   bd.year,
        hour:   bd.hour,
        minute: bd.minute,
        ampm:   bd.ampm,
        lat:    bd.lat,
        lon:    bd.lon,
        tz:     bd.tz,
        place:  bd.place,
      }),
      signal: ctrl.signal,
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error((err as { error?: string }).error ?? "Kundli calculation failed");
    }

    const data = await res.json();
    return { ...data, name: bd.name } as KundliData;
  } catch (e: unknown) {
    if (e instanceof Error && e.name === "AbortError") {
      throw new Error("TIMEOUT");
    }
    throw e;
  } finally {
    clearTimeout(timer);
  }
}

export async function fetchKundliFromAPI(bd: BirthData): Promise<KundliData> {
  const TIMEOUTS  = [20_000, 28_000, 35_000];
  const MAX_TRIES = 3;
  let lastErr: Error = new Error("Kundli calculation failed.");

  for (let attempt = 0; attempt < MAX_TRIES; attempt++) {
    try {
      return await attemptKundliFetch(bd, TIMEOUTS[attempt]);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      if (msg === "TIMEOUT") {
        lastErr = new Error(
          attempt < MAX_TRIES - 1
            ? "Request timed out — retrying…"
            : "Connection timed out. Please check your internet and try again."
        );
      } else {
        lastErr = e instanceof Error ? e : new Error(msg);
      }
      if (attempt < MAX_TRIES - 1) {
        await new Promise(r => setTimeout(r, attempt * 1500));
      }
    }
  }
  throw lastErr;
}

interface NominatimResult {
  display_name: string;
  lat: string;
  lon: string;
  address?: { country_code?: string };
}

export interface PlaceSuggestion {
  label: string;
  lat: number;
  lon: number;
  tz: number;
  countryCode: string;
}

export async function searchPlaces(query: string): Promise<PlaceSuggestion[]> {
  const r = await apiFetch(`${BASE_URL}/api/geocode?q=${encodeURIComponent(query)}`);
  const rows = await r.json();
  return rows.map((x: { label: string; lat: number; lon: number; tz: number }) => ({
    label: x.label,
    lat: x.lat,
    lon: x.lon,
    tz: x.tz,
    countryCode: "",
  }));
}

export async function fetchTimezone(lat: number, lon: number): Promise<number> {
  try {
    const r = await apiFetch(`${BASE_URL}/api/timezone?lat=${lat}&lon=${lon}`);
    const d = await r.json();
    if (typeof d.tz === "number") return d.tz;
  } catch { /* fallback */ }
  return Math.round((lon / 15) * 2) / 2;
}
