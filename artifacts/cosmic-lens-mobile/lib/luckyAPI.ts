import { API_BASE, apiFetch } from "./apiConfig";

export interface DailyLucky {
  ok: true;
  date: string;
  shubh_ank: number;          // 1..9
  shubh_rang_name: string;    // Hinglish (Suneheri, Lal, Pila, ...)
  shubh_rang_hex: string;     // hex code for swatch
  shubh_rang_intent: "amplify" | "protect";
  mool_ank: number;           // permanent (Mulank)
  reasoning_hinglish: string; // 1-line user-facing explanation
  tara: string;               // Hinglish tara name
  tara_idx: number;
  today_nakshatra: string;
  today_nak_idx: number;
  tithi_idx: number;
  weekday_idx: number;
}

export interface LuckyError {
  ok: false;
  error: string;
  message: string;
}

export type LuckyResult = DailyLucky | LuckyError;

/**
 * Fetch personalised "Aaj Ka Shubh Ank" + "Aaj Ka Shubh Rang" for today
 * (or an optional date) for an authenticated user.
 *
 * Returns { ok: false, error, message } on auth/data-missing failures —
 * NEVER returns fake fallback values.
 */
export async function fetchDailyLucky(
  userId: number,
  apiKey: string,
  date?: string,
): Promise<LuckyResult> {
  try {
    const res = await apiFetch(`${API_BASE}/api/lucky/today`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-API-Key": apiKey,
      },
      body: JSON.stringify({ user_id: userId, ...(date ? { date } : {}) }),
    });
    const json = await res.json().catch(() => ({}));
    if (!res.ok) {
      return {
        ok: false,
        error: (json as { error?: string }).error ?? "request_failed",
        message: (json as { message?: string }).message
              ?? (json as { error?: string }).error
              ?? "Lucky details abhi nahi mil paaye.",
      };
    }
    return json as DailyLucky;
  } catch (e) {
    return {
      ok: false,
      error: "network",
      message: "Network issue — thodi der baad try karein.",
    };
  }
}
