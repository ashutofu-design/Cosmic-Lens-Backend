import { API_BASE, apiFetch } from "./apiConfig";

// ── Backend response shape (mirrors risk_text_engine.enrich_risk_radar) ────
export interface RiskTextTopRisk {
  trigger:                string;          // signal id (e.g. "saturn_heavy")
  category:               string;          // user-facing category label
  kya_risk_hai:           string;
  kya_dhyan_rakhna_hai:   string;
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
  const { date, kundli, birthData, userId, apiKey } = opts;
  try {
    const headers: Record<string, string> = { "Content-Type": "application/json" };
    if (apiKey) headers["X-API-Key"] = apiKey;
    const body: Record<string, unknown> = {};
    if (date)              body.date      = date;
    if (kundli)            body.kundli    = kundli;
    if (birthData)         body.birthData = birthData;
    if (userId != null)    body.user_id   = userId;

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
