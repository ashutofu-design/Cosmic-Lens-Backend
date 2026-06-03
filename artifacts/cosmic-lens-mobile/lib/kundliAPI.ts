import type { BirthData, KundliData } from "@/types";

import { API_BASE as BASE_URL, apiFetch, apiFetchBases } from "./apiConfig";

export interface KundliAuth {
  user_id: number;
  api_key: string;
}

export class KundliQuotaError extends Error {
  used: number;
  limit: number;
  plan: string;
  constructor(message: string, used: number, limit: number, plan: string) {
    super(message);
    this.name = "KundliQuotaError";
    this.used = used;
    this.limit = limit;
    this.plan = plan;
  }
}

async function attemptKundliFetch(bd: BirthData, timeoutMs: number, auth?: KundliAuth | null): Promise<KundliData> {
  const ctrl  = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), timeoutMs);
  try {
    const headers: Record<string, string> = { "Content-Type": "application/json" };
    if (auth?.api_key) headers["X-API-Key"] = auth.api_key;

    const body: Record<string, unknown> = {
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
    };
    if (auth?.user_id) body.user_id = auth.user_id;

    const res = await apiFetch(`${BASE_URL}/api/kundli`, {
      method: "POST",
      headers,
      body: JSON.stringify(body),
      signal: ctrl.signal,
    });

    if (res.status === 402) {
      const err = (await res.json().catch(() => ({}))) as {
        message?: string; quota?: { used: number; limit: number }; plan?: string;
      };
      throw new KundliQuotaError(
        err.message ?? "Daily kundli limit reached",
        err.quota?.used ?? 0,
        err.quota?.limit ?? 0,
        err.plan ?? "free",
      );
    }

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

export async function fetchKundliFromAPI(bd: BirthData, auth?: KundliAuth | null): Promise<KundliData> {
  const TIMEOUTS  = [20_000, 28_000, 35_000];
  const MAX_TRIES = 3;
  let lastErr: Error = new Error("Kundli calculation failed.");

  for (let attempt = 0; attempt < MAX_TRIES; attempt++) {
    try {
      return await attemptKundliFetch(bd, TIMEOUTS[attempt], auth);
    } catch (e: unknown) {
      // Quota errors are terminal — never retry, surface immediately.
      if (e instanceof KundliQuotaError) throw e;
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

export interface PlaceSuggestion {
  label: string;
  lat: number;
  lon: number;
  tz: number;
  countryCode: string;
}

function mapGeocodeRows(rows: unknown): PlaceSuggestion[] {
  if (!Array.isArray(rows)) return [];
  return rows
    .map((x: { label?: string; lat?: number; lon?: number; tz?: number }) => ({
      label: String(x.label ?? ""),
      lat: Number(x.lat),
      lon: Number(x.lon),
      tz: typeof x.tz === "number" ? x.tz : Math.round((Number(x.lon) / 15) * 2) / 2,
      countryCode: "",
    }))
    .filter(p => p.label && Number.isFinite(p.lat) && Number.isFinite(p.lon));
}

/** Direct Open-Meteo when VPS geocode proxy is unreachable (browser CORS OK). */
async function searchPlacesOpenMeteo(query: string, signal?: AbortSignal): Promise<PlaceSuggestion[]> {
  const url =
    `https://geocoding-api.open-meteo.com/v1/search?name=${encodeURIComponent(query)}` +
    "&count=6&language=en&format=json";
  const r = await fetch(url, { signal });
  if (!r.ok) throw new Error(`Open-Meteo HTTP ${r.status}`);
  const data = (await r.json()) as {
    results?: Array<{
      name?: string;
      admin1?: string;
      country?: string;
      latitude?: number;
      longitude?: number;
    }>;
  };
  const out: PlaceSuggestion[] = [];
  for (const x of data.results ?? []) {
    const lat = Number(x.latitude);
    const lon = Number(x.longitude);
    const parts = [x.name, x.admin1, x.country];
    const label = parts.filter(Boolean).join(", ");
    if (label && Number.isFinite(lat) && Number.isFinite(lon)) {
      out.push({
        label,
        lat,
        lon,
        tz: Math.round((lon / 15) * 2) / 2,
        countryCode: "",
      });
    }
  }
  return out;
}

export async function searchPlaces(query: string): Promise<PlaceSuggestion[]> {
  const q = query.trim();
  if (q.length < 2) return [];

  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), 15000);
  const path = `/api/geocode?q=${encodeURIComponent(q)}`;

  try {
    let lastNet = "";
    for (const base of apiFetchBases()) {
      try {
        const r = await apiFetch(`${base}${path}`, { signal: ctrl.signal });
        if (!r.ok) continue;
        const mapped = mapGeocodeRows(await r.json());
        if (mapped.length > 0) return mapped;
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : String(e);
        if (/Network request failed|Failed to fetch|Load failed|fetch|abort/i.test(msg)) {
          lastNet = msg;
          continue;
        }
        throw e;
      }
    }

    const direct = await searchPlacesOpenMeteo(q, ctrl.signal);
    if (direct.length > 0) return direct;

    if (lastNet) throw new Error(lastNet);
    return [];
  } finally {
    clearTimeout(timer);
  }
}

export async function fetchTimezone(lat: number, lon: number): Promise<number> {
  const path = `/api/timezone?lat=${lat}&lon=${lon}`;
  for (const base of apiFetchBases()) {
    try {
      const r = await apiFetch(`${base}${path}`);
      const d = await r.json();
      if (typeof d.tz === "number") return d.tz;
    } catch {
      continue;
    }
  }
  return Math.round((lon / 15) * 2) / 2;
}
