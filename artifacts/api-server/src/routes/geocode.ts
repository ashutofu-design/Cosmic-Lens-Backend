import { Router, type IRouter } from "express";

type GeoRow = { label: string; lat: number; lon: number; tz: number };

const router: IRouter = Router();

async function fetchJson(url: string, init?: RequestInit, timeoutMs = 8000): Promise<any> {
  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), timeoutMs);
  try {
    const res = await fetch(url, {
      ...init,
      signal: ctrl.signal,
      headers: {
        "User-Agent": "CosmicLens/1.0 (support@cosmiclens.app)",
        "Accept": "application/json",
        "Accept-Language": "en",
        ...(init?.headers || {}),
      },
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } finally {
    clearTimeout(t);
  }
}

function tzFromLon(lon: number): number {
  // Same heuristic used in the old Flask backend: round to nearest 0.5 hour.
  return Math.round((lon / 15) * 2) / 2;
}

router.get("/geocode", async (req, res) => {
  const q = String(req.query.q ?? "").trim();
  if (q.length < 2) {
    res.json([]);
    return;
  }

  // Primary: Open-Meteo geocoding (no key)
  try {
    const url = `https://geocoding-api.open-meteo.com/v1/search?name=${encodeURIComponent(q)}&count=6&language=en&format=json`;
    const data = await fetchJson(url);
    const rows = Array.isArray(data?.results) ? data.results : [];
    const out: GeoRow[] = [];
    for (const x of rows) {
      const lat = Number(x?.latitude ?? 0);
      const lon = Number(x?.longitude ?? 0);
      if (!Number.isFinite(lat) || !Number.isFinite(lon)) continue;
      const parts = [x?.name, x?.admin1, x?.country].filter(Boolean);
      const label = parts.join(", ");
      if (!label) continue;
      out.push({ label, lat, lon, tz: tzFromLon(lon) });
    }
    if (out.length) {
      res.json(out);
      return;
    }
  } catch {
    // fall through
  }

  // Fallback: OSM Nominatim
  try {
    const url = `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(q)}&format=json&limit=6&addressdetails=1`;
    const rows = await fetchJson(url);
    const out: GeoRow[] = [];
    if (Array.isArray(rows)) {
      for (const x of rows) {
        const lat = Number(x?.lat ?? 0);
        const lon = Number(x?.lon ?? 0);
        if (!Number.isFinite(lat) || !Number.isFinite(lon)) continue;
        const display = String(x?.display_name ?? "");
        const label = display.split(",").slice(0, 3).map(s => s.trim()).filter(Boolean).join(", ");
        if (!label) continue;
        out.push({ label, lat, lon, tz: tzFromLon(lon) });
      }
    }
    res.json(out);
  } catch {
    // Never 500; client treats empty list as "no results"
    res.json([]);
  }
});

export default router;

