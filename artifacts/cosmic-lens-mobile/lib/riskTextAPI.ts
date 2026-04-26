import { API_BASE, apiFetch } from "./apiConfig";

// ── Backend response shape (mirrors risk_text_engine.enrich_risk_radar) ────
export interface RiskTextTopRisk {
  trigger:                string;          // signal id (e.g. "saturn_heavy")
  category:               string;          // user-facing category label
  kya_risk_hai:           string;
  kya_avoid_karna_hai:    string;
  kya_karna_hai:          string;
  upay:                   string;
}

export interface RiskTextWindow {
  window: string;   // "10:42 AM — 12:18 PM"
  label:  string;   // "Amrit" / "Rahukaal" / "Rog" ...
  period: "day" | "night" | "";
}

export interface RiskTextSegment {
  start:   string;
  end:     string;
  name:    string;
  period:  "day" | "night";
  quality: "best" | "neutral" | "avoid";
}

// Per-day enrichment from backend — one entry per next 7 days (today = idx 0).
// All fields are derived from the user's primary kundli + projected transit
// signals (Tara Bal, Tithi, Choghadiya per weekday). NO template fallback.
export interface PerDayRisk {
  day_idx:              number;          // 0..6 (0 = today)
  trigger:              string;          // signal id
  severity:             number;          // 0..10 raw severity
  category:             string;
  risk_score:           number;          // 1..10 user-facing
  risk_level:           "low" | "med" | "high";
  summary:              string;
  kya_risk_hai:         string;
  kya_avoid_karna_hai:  string;
  kya_karna_hai:        string;
  upay:                 string;
  best_time:            RiskTextWindow;
  avoid_time:           RiskTextWindow;
  tara_idx:             number;          // -1 if natal nakshatra missing
  weekday:              number;          // 0..6 (Mon..Sun)
  // Per-day "Aaj Ka Shubh Ank + Rang" — same engine as /api/lucky/today,
  // computed for the day's projected Moon/Sun longitudes. NEVER fake — when
  // missing (no birth data, kundli unavailable, lucky engine off), all three
  // fields are null and the client must render an explicit unavailable state.
  shubh_ank:            number | null;
  shubh_rang_name:      string | null;
  shubh_rang_hex:       string | null;
}

export interface RiskRadarLegacyItem {
  level:   "low" | "medium" | "high";
  title:   string;
  reason:  string;
  advice:  string;
  timing?: string;
}

export interface RiskRadarResponse {
  date:               string;
  score?:             number;
  summary:            string;
  // Enrichment fields — present only when `enriched === true`. The client
  // must check `enriched` before reading these (backend is additive — base
  // radar always returns 200, enrichment can be missing on partial failure).
  enriched?:          boolean;
  enrich_error?:      string;
  top_risk?:          RiskTextTopRisk;
  best_time?:         RiskTextWindow;
  avoid_time?:        RiskTextWindow;
  rahukaal_today?:    { start: string; end: string; label: "Rahukaal" } | null;
  choghadiya_today?:  RiskTextSegment[];
  per_day?:           PerDayRisk[];      // 7 entries (today=0 .. today+6)
  risk_radar_24h:     RiskRadarLegacyItem[];
  risk_radar_7d:      Array<{ range: string; level: string; label: string; advice: string }>;
  powered_by?:        "Advanced Cosmic Intelligence";
}

export interface RiskRadarError {
  ok:      false;
  error:   string;
  message: string;
}

export type RiskRadarResult = RiskRadarResponse | RiskRadarError;

export interface FetchRiskRadarOpts {
  date?:      string;
  kundli?:    Record<string, unknown> | null;
  birthData?: Record<string, unknown> | null;
  userId?:    number | null;
  apiKey?:    string | null;
  /**
   * UI language code (UILang from `lib/i18n.ts` — e.g. "en", "hn", "hi",
   * "mr", "ta"). Backend uses this to select the language of the AI-generated
   * Risk Alert text (top_risk + per_day kya_risk_hai/kya_avoid/kya_karna/upay).
   * When omitted, the server defaults to "hn" (Hinglish) so existing callers
   * are unaffected. Unknown / unsupported codes also collapse to "hn"
   * server-side, so callers don't need to pre-validate.
   */
  lang?:      string;
}

/**
 * Fetch personalised Risk Radar (KYA RISK / DHYAN / AVOID / KARNA / UPAY +
 * Choghadiya BEST/AVOID time windows) for today (or an optional date).
 *
 * Two auth modes (mirrors lucky/risk-radar pattern):
 *   1. Authed:    pass `userId` + `apiKey` (server loads kundli from DB).
 *   2. Stateless: pass `kundli` (and optionally `birthData`) — no auth needed.
 *
 * Returns `{ ok: false, error, message }` on failure — NEVER fake data.
 */
export async function fetchRiskRadar(
  opts: FetchRiskRadarOpts = {},
): Promise<RiskRadarResult> {
  const { date, kundli, birthData, userId, apiKey, lang } = opts;
  try {
    const headers: Record<string, string> = { "Content-Type": "application/json" };
    if (apiKey) headers["X-API-Key"] = apiKey;
    const body: Record<string, unknown> = {};
    if (date)              body.date      = date;
    if (kundli)            body.kundli    = kundli;
    if (birthData)         body.birthData = birthData;
    if (userId != null)    body.user_id   = userId;
    if (lang)              body.lang      = lang;

    const res = await apiFetch(`${API_BASE}/api/risk-radar`, {
      method: "POST",
      headers,
      body: JSON.stringify(body),
    });
    const json = await res.json().catch(() => ({}));
    if (!res.ok) {
      return {
        ok:    false,
        error: (json as { error?: string }).error ?? "request_failed",
        message:
          (json as { message?: string }).message ??
          (json as { error?: string }).error ??
          "Risk details abhi nahi mil paaye.",
      };
    }
    return json as RiskRadarResponse;
  } catch (e) {
    return {
      ok:    false,
      error: "network",
      message: "Network issue — thodi der baad try karein.",
    };
  }
}

export function isRiskRadarOk(r: RiskRadarResult): r is RiskRadarResponse {
  return (r as RiskRadarError).ok !== false;
}
