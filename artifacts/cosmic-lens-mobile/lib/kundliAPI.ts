import type { BirthData, KundliData } from "@/types";

const BASE_URL = process.env.EXPO_PUBLIC_DOMAIN
  ? `https://${process.env.EXPO_PUBLIC_DOMAIN}`
  : "";

export async function fetchKundliFromAPI(bd: BirthData): Promise<KundliData> {
  const res = await fetch(`${BASE_URL}/api/kundli`, {
    method:  "POST",
    headers: { "Content-Type": "application/json" },
    body:    JSON.stringify({
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
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as { error?: string }).error ?? "Kundli calculation failed");
  }

  const data = await res.json();
  return { ...data, name: bd.name } as KundliData;
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
  const url =
    `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(query)}&format=json&limit=6&addressdetails=1`;
  const r = await fetch(url, { headers: { "Accept-Language": "en" } });
  const rows = (await r.json()) as NominatimResult[];
  return rows.map(x => {
    const lat = parseFloat(x.lat);
    const lon = parseFloat(x.lon);
    const tz  = Math.round((lon / 15) * 2) / 2;
    return {
      label:       x.display_name.split(",").slice(0, 3).join(", "),
      lat, lon, tz,
      countryCode: (x.address?.country_code ?? "").toLowerCase(),
    };
  });
}

export async function fetchTimezone(lat: number, lon: number): Promise<number> {
  try {
    const r = await fetch(`${BASE_URL}/api/timezone?lat=${lat}&lon=${lon}`);
    const d = await r.json();
    if (typeof d.tz === "number") return d.tz;
  } catch { /* fallback */ }
  return Math.round((lon / 15) * 2) / 2;
}
