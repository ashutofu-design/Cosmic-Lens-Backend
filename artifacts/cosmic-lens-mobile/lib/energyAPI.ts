// ─────────────────────────────────────────────────────────────────────────────
//  Daily Energy Score — backend fetch wrapper
//
//  Calls /api/energy/today on the Flask backend (Shadbala + Shodhana engine,
//  ~92% classical accuracy) and returns the full result.  Falls back gracefully
//  so the UI can use the local approximation if the network is down.
// ─────────────────────────────────────────────────────────────────────────────

import { API_BASE, apiFetch } from "./apiConfig";
import type { KundliData } from "@/types";

export type EnergyComponent = {
  score: number;
  weight: number;
  [k: string]: any;
};

export interface EnergyResult {
  energy_score: number;
  category: "Low" | "Moderate" | "Good" | "Strong" | "Excellent";
  color: string;
  date: string;
  summary: string;
  advice: string;
  components: {
    dasha:           EnergyComponent;
    moon_transit:    EnergyComponent;
    ashtakavarga:    EnergyComponent;
    tara_bal:        EnergyComponent;
    aspect_strength: EnergyComponent;
  };
  today_moon: {
    longitude:      number;
    rashiIndex:     number;
    nakshatraIndex: number;
  };
}

/**
 * Fetch today's energy score + component breakdown from the backend.
 *
 * We send the full kundli object in the body (stateless mode) — this matches
 * the server's accepted payload and avoids needing auth for the read.
 *
 * @param kundli — user's saved kundli (from UserContext)
 * @param dateISO — optional YYYY-MM-DD for back-dated scores
 * @param signal — optional AbortSignal for cancellation
 */
export async function fetchTodayEnergy(
  kundli: KundliData,
  dateISO?: string,
  signal?: AbortSignal,
): Promise<EnergyResult | null> {
  try {
    const body: Record<string, any> = { kundli };
    if (dateISO) body.date = dateISO;

    const res = await apiFetch(`${API_BASE}/api/energy/today`, {
      method: "POST",
      body:   JSON.stringify(body),
      signal,
    });
    if (!res.ok) {
      if (__DEV__) console.warn("[energyAPI] HTTP", res.status);
      return null;
    }
    const data = await res.json();
    if (typeof data?.energy_score !== "number") {
      if (__DEV__) console.warn("[energyAPI] malformed response", data);
      return null;
    }
    return data as EnergyResult;
  } catch (err: any) {
    if (err?.name === "AbortError") return null;
    if (__DEV__) console.warn("[energyAPI] failed:", err?.message || err);
    return null;
  }
}
