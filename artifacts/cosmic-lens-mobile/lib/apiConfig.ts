// ─────────────────────────────────────────────────────────────────────────────
// API endpoint resolution.
//
// Priority (highest first):
//   1. EXPO_PUBLIC_API_URL    → full URL override (e.g. https://my-api.replit.app)
//   2. EXPO_PUBLIC_DOMAIN     → just the hostname (legacy, https:// auto-prepended)
//   3. PRODUCTION_API_URL     → baked-in production fallback (set after publishing)
//   4. DEV fallback           → Replit dev server domain (only for local testing)
//
// For Play Store builds, set EXPO_PUBLIC_API_URL in your `.env` to the deployed
// production URL (e.g. `https://cosmic-lens.replit.app`). EAS build will pick it
// up automatically and bake it into the app bundle.
// ─────────────────────────────────────────────────────────────────────────────

// Replace this with your deployed `.replit.app` URL after publishing the backend.
// Until you publish, this will simply be unused as long as EXPO_PUBLIC_API_URL is set.
const PRODUCTION_API_URL = "https://cosmic-lens-api.replit.app";

// Replit dev server (used only when running `expo start` locally, never in
// production builds). This is intentionally kept as a fallback so local dev
// keeps working.
const DEV_REPLIT_DOMAIN = "18370deb-aa55-4d9f-8391-57df5a15cf7a-00-phjaov5qh4np.kirk.replit.dev";

function resolveApiBase(): string {
  const fullUrl   = process.env.EXPO_PUBLIC_API_URL;
  const hostOnly  = process.env.EXPO_PUBLIC_DOMAIN;

  // ── Web platform (workspace preview / EAS web build) ──
  // localtunnel (.loca.lt) blocks browser fetches with a "click to continue"
  // interstitial — fine for native fetch (we send `bypass-tunnel-reminder`
  // header), but the iframe preview can't bypass it. So on web we always
  // prefer the direct Replit dev domain instead of the lt tunnel.
  if (typeof window !== "undefined" && typeof document !== "undefined") {
    if (fullUrl && /\.loca\.lt/i.test(fullUrl)) {
      // ignore lt tunnel on web — fall through to dev/prod fallback
    } else if (fullUrl && /^https?:\/\//.test(fullUrl)) {
      return fullUrl.replace(/\/$/, "");
    }
    if (hostOnly) return `https://${hostOnly}`;
    if (!__DEV__) return PRODUCTION_API_URL;
    return `https://${DEV_REPLIT_DOMAIN}`;
  }

  // ── Native (iOS / Android via Expo Go or EAS build) ──
  if (fullUrl && /^https?:\/\//.test(fullUrl)) return fullUrl.replace(/\/$/, "");
  if (hostOnly)                                return `https://${hostOnly}`;
  if (!__DEV__)                                return PRODUCTION_API_URL;
  return `https://${DEV_REPLIT_DOMAIN}`;
}

export const API_BASE = resolveApiBase();

export const API_HEADERS: Record<string, string> = {
  "Content-Type": "application/json",
  "Accept":       "application/json",
  // Bypass localtunnel's "Click to continue" interstitial that otherwise
  // returns HTML instead of JSON on the first request from a fresh client IP.
  "bypass-tunnel-reminder": "true",
  "User-Agent": "CosmicLensMobile/1.0",
};

export async function apiFetch(url: string, init?: RequestInit): Promise<Response> {
  const merged: RequestInit = {
    ...init,
    headers: {
      ...API_HEADERS,
      ...(init?.headers as Record<string, string> | undefined),
    },
  };
  // Retry once on transient "Network request failed" — common on cellular networks
  // when the first TLS handshake to a fresh host hiccups. We don't retry on AbortError
  // (timeout/cancel), HTTP errors, or other failure modes.
  try {
    return await fetch(url, merged);
  } catch (e: any) {
    if (e?.name === "AbortError") throw e;
    const msg = String(e?.message || "");
    if (!/Network request failed|TypeError|fetch/i.test(msg)) throw e;
    await new Promise(r => setTimeout(r, 600));
    return fetch(url, merged);
  }
}

if (__DEV__) {
  console.log("[CosmicLens] API_BASE resolved to:", API_BASE);

  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), 8000);
  fetch(`${API_BASE}/api/healthz`, { signal: ctrl.signal })
    .then(r => r.json())
    .then(d => console.log("[CosmicLens] healthz OK ✓", JSON.stringify(d)))
    .catch(e => console.error("[CosmicLens] healthz FAILED:", e.message, "→", `${API_BASE}/api/healthz`))
    .finally(() => clearTimeout(timer));
}
