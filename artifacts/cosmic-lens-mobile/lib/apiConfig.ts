import Constants from "expo-constants";
import { Platform } from "react-native";

// ─────────────────────────────────────────────────────────────────────────────
// API endpoint resolution.
//
// Priority (highest first):
//   1. EXPO_PUBLIC_API_URL    → full URL override (e.g. https://my-api.replit.app)
//   2. EXPO_PUBLIC_DOMAIN     → just the hostname (legacy, https:// auto-prepended)
//   3. PRODUCTION_API_URL     → baked-in production fallback
//   4. DEV fallback           → Replit dev server domain (only for local testing)
//
// For Play Store builds, set EXPO_PUBLIC_API_URL in EAS production env to the
// deployed HTTPS API URL (e.g. `https://api.cosmiclens.app`).
// ─────────────────────────────────────────────────────────────────────────────

// VPS / production API base. Override at runtime with EXPO_PUBLIC_API_URL.
const PRODUCTION_API_URL = "https://api.cosmiclens.app";

// Replit dev server (used only when running `expo start` locally, never in
// production builds). This is intentionally kept as a fallback so local dev
// keeps working.
const DEV_REPLIT_DOMAIN = "18370deb-aa55-4d9f-8391-57df5a15cf7a-00-phjaov5qh4np.kirk.replit.dev";

function isWeb(): boolean {
  return typeof window !== "undefined" && typeof document !== "undefined";
}

function localDevApiBaseFromLocation(): string | null {
  if (!isWeb()) return null;
  const host = window.location?.hostname;
  if (!host) return null;
  if (host === "localhost" || host === "127.0.0.1") return "http://127.0.0.1:8080";
  if (/^\d{1,3}(\.\d{1,3}){3}$/.test(host)) return `http://${host}:8080`;
  return null;
}

/** Metro / Expo Go exposes the dev PC's LAN IP (e.g. 192.168.1.5:18987). */
function expoDevMachineHost(): string | null {
  try {
    const extra = Constants.expoConfig?.extra as
      | { expoGo?: { debuggerHost?: string } }
      | undefined;
    const raw =
      Constants.expoConfig?.hostUri ??
      Constants.expoGoConfig?.debuggerHost ??
      extra?.expoGo?.debuggerHost ??
      (Constants as { manifest?: { debuggerHost?: string } }).manifest?.debuggerHost;
    if (!raw || typeof raw !== "string") return null;
    const host = raw.split(":")[0]?.trim();
    if (!host || host === "localhost" || host === "127.0.0.1") return null;
    return host;
  } catch {
    return null;
  }
}

/** Physical device / Expo Go cannot reach the PC via localhost — use LAN IP. */
function rewriteLocalDevHost(base: string): string {
  if (!__DEV__ || !/localhost|127\.0\.0\.1/i.test(base)) return base;
  // Browser on the same machine can use localhost.
  if (typeof window !== "undefined" && typeof document !== "undefined") return base;

  const lan = expoDevMachineHost();
  if (lan) return base.replace(/localhost|127\.0\.0\.1/gi, lan);

  if (Platform.OS === "android") {
    return base.replace(/localhost|127\.0\.0\.1/gi, "10.0.2.2");
  }
  return base;
}

function normalizeApiUrl(raw?: string): string | null {
  if (!raw || !/^https?:\/\//.test(raw)) return null;
  const normalized = raw.replace(/\/$/, "");
  if (!__DEV__ && !normalized.startsWith("https://")) {
    console.warn("[CosmicLens] Ignoring non-HTTPS API URL in production build.");
    return null;
  }
  return rewriteLocalDevHost(normalized);
}

function resolveApiBase(): string {
  const fullUrl   = process.env.EXPO_PUBLIC_API_URL;
  const hostOnly  = process.env.EXPO_PUBLIC_DOMAIN;

  // ── Web platform (workspace preview / EAS web build) ──
  // localtunnel (.loca.lt) blocks browser fetches with a "click to continue"
  // interstitial — fine for native fetch (we send `bypass-tunnel-reminder`
  // header), but the iframe preview can't bypass it. So on web we always
  // prefer the direct Replit dev domain instead of the lt tunnel.
  if (isWeb()) {
    // Local web dev convenience: if you're running the UI on your machine and
    // also running the Flask backend on :8080, auto-default there even if env
    // vars weren't picked up by the bundler.
    if (__DEV__) {
      const local = localDevApiBaseFromLocation();
      if (local) return local;
    }
    if (fullUrl && /\.loca\.lt/i.test(fullUrl)) {
      // ignore lt tunnel on web — fall through to dev/prod fallback
    } else {
      const normalized = normalizeApiUrl(fullUrl);
      if (normalized) return normalized;
    }
    if (hostOnly) return `https://${hostOnly}`;
    if (!__DEV__) return PRODUCTION_API_URL;
    return `https://${DEV_REPLIT_DOMAIN}`;
  }

  // ── Native (iOS / Android via Expo Go or EAS build) ──
  const normalized = normalizeApiUrl(fullUrl);
  if (normalized) return normalized;
  if (hostOnly) return rewriteLocalDevHost(`https://${hostOnly}`);
  if (!__DEV__) return PRODUCTION_API_URL;
  return `https://${DEV_REPLIT_DOMAIN}`;
}

export const API_BASE = resolveApiBase();

function installDevFetchInterceptor(): void {
  if (!__DEV__ || !isWeb()) return;

  const forced = (() => {
    try { return window.localStorage?.getItem("cl_force_api_base") || ""; } catch { return ""; }
  })();
  const verbose = (() => {
    try { return window.localStorage?.getItem("cl_verbose_network") === "1"; } catch { return false; }
  })();
  const local = localDevApiBaseFromLocation();
  const preferred = forced && /^https?:\/\//.test(forced) ? forced.replace(/\/$/, "") : (local ?? "");

  const shouldRewrite = (url: string) =>
    !!preferred && (
      url.includes("api.cosmiclens.app") ||
      url.startsWith(PRODUCTION_API_URL)
    );

  const orig = globalThis.fetch?.bind(globalThis);
  if (!orig) return;
  // Avoid double-install.
  if ((globalThis as any).__cosmic_fetch_wrapped) return;
  (globalThis as any).__cosmic_fetch_wrapped = true;

  globalThis.fetch = (async (input: any, init?: any) => {
    const method = (init?.method || (typeof input === "object" && input?.method) || "GET").toUpperCase();
    const urlStr =
      typeof input === "string"
        ? input
        : (input?.url ? String(input.url) : String(input));

    let nextInput = input;
    if (typeof urlStr === "string" && shouldRewrite(urlStr)) {
      const rewritten = urlStr
        .replace(/^https?:\/\/api\.cosmiclens\.app/i, preferred)
        .replace(new RegExp(`^${PRODUCTION_API_URL.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}`, "i"), preferred);
      console.warn("[CosmicLens][dev] Rewriting fetch URL:", urlStr, "→", rewritten);
      nextInput = rewritten;
    }

    try {
      if (verbose) console.log("[CosmicLens][dev] fetch", method, urlStr);
      const res = await orig(nextInput as any, init);
      if (!res.ok) {
        console.warn("[CosmicLens][dev] HTTP", res.status, method, urlStr);
      }
      return res;
    } catch (e: any) {
      console.error("[CosmicLens][dev] fetch failed:", method, urlStr, e?.message || e);
      throw e;
    }
  }) as any;

  // Log if something still resolved to prod during local web dev.
  if (local && API_BASE.includes("api.cosmiclens.app")) {
    console.warn("[CosmicLens][dev] API_BASE resolved to production unexpectedly:", API_BASE, "Local preferred:", preferred);
  }
}

/** Demo login tries these in order when the primary base is unreachable. */
export function demoLoginApiBases(): string[] {
  const seen = new Set<string>();
  const out: string[] = [];
  const add = (b: string) => {
    const n = b.replace(/\/$/, "");
    if (!seen.has(n)) {
      seen.add(n);
      out.push(n);
    }
  };
  add(API_BASE);
  if (__DEV__) {
    const raw = process.env.EXPO_PUBLIC_API_URL;
    if (raw && /^https?:\/\//.test(raw)) add(raw.replace(/\/$/, ""));
    const lan = expoDevMachineHost();
    if (lan) add(`http://${lan}:8080`);
  }
  if (API_BASE !== PRODUCTION_API_URL) add(PRODUCTION_API_URL);
  return out;
}

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
  installDevFetchInterceptor();
  console.log("[CosmicLens] API_BASE resolved to:", API_BASE);

  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), 8000);
  // Use apiFetch so the bypass-tunnel-reminder header is sent — otherwise
  // loca.lt returns an HTML interstitial that breaks `.json()` parsing.
  apiFetch(`${API_BASE}/api/healthz`, { signal: ctrl.signal })
    .then(r => r.json())
    .then(d => console.log("[CosmicLens] healthz OK ✓", JSON.stringify(d)))
    .catch(e => console.error("[CosmicLens] healthz FAILED:", e?.message || e, "→", `${API_BASE}/api/healthz`))
    .finally(() => clearTimeout(timer));
}
