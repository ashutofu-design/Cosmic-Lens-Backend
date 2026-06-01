import Constants from "expo-constants";
import { Platform } from "react-native";

// ─────────────────────────────────────────────────────────────────────────────
// API endpoint resolution.
//
// Priority (highest first):
//   1. EXPO_PUBLIC_API_URL (from .env — baked in at Metro start)
//   2. expo.extra.apiUrl (from app.config.js — VPS default)
//   3. PRODUCTION_API_URL (HTTPS store builds)
//   4. DEV VPS fallback (never localhost unless EXPO_PUBLIC_USE_LOCAL_API=1)
//
// Set in artifacts/cosmic-lens-mobile/.env:
//   EXPO_PUBLIC_API_URL=http://187.127.174.55:8080
// After changing .env: stop Metro (Ctrl+C) and run `npx expo start` again.
// ─────────────────────────────────────────────────────────────────────────────

const PRODUCTION_API_URL = "https://api.cosmiclens.app";

/** Hostinger VPS — default for dev so laptop/phone always hit live API. */
const DEFAULT_DEV_VPS_API = "http://187.127.174.55:8080";

const DEV_REPLIT_DOMAIN =
  "18370deb-aa55-4d9f-8391-57df5a15cf7a-00-phjaov5qh4np.kirk.replit.dev";

function useLocalBackend(): boolean {
  return (process.env.EXPO_PUBLIC_USE_LOCAL_API || "").trim() === "1";
}

function configuredApiUrl(): string | undefined {
  const fromEnv = process.env.EXPO_PUBLIC_API_URL?.trim();
  if (fromEnv) return fromEnv;
  const fromExtra = (
    Constants.expoConfig?.extra as { apiUrl?: string } | undefined
  )?.apiUrl?.trim();
  return fromExtra || undefined;
}

function isWeb(): boolean {
  return typeof window !== "undefined" && typeof document !== "undefined";
}

function localDevApiBaseFromLocation(): string | null {
  if (!isWeb() || !useLocalBackend()) return null;
  const host = window.location?.hostname;
  if (!host) return null;
  if (host === "localhost" || host === "127.0.0.1") return "http://127.0.0.1:8080";
  if (/^\d{1,3}(\.\d{1,3}){3}$/.test(host)) return `http://${host}:8080`;
  return null;
}

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

function rewriteLocalDevHost(base: string): string {
  if (!__DEV__ || !/localhost|127\.0\.0\.1/i.test(base)) return base;
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
  const fullUrl = configuredApiUrl();
  const hostOnly = process.env.EXPO_PUBLIC_DOMAIN;

  if (fullUrl && /\.loca\.lt/i.test(fullUrl) && isWeb()) {
    // localtunnel interstitial breaks web iframe — fall through
  } else {
    const normalized = normalizeApiUrl(fullUrl);
    if (normalized) return normalized;
  }

  if (useLocalBackend()) {
    const local = localDevApiBaseFromLocation();
    if (local) return local;
  }

  if (hostOnly) {
    return rewriteLocalDevHost(`https://${hostOnly}`);
  }

  if (!__DEV__) return PRODUCTION_API_URL;

  // Dev: VPS by default (not localhost)
  const vps = normalizeApiUrl(DEFAULT_DEV_VPS_API);
  if (vps) return vps;

  return `https://${DEV_REPLIT_DOMAIN}`;
}

export const API_BASE = resolveApiBase();

function installDevFetchInterceptor(): void {
  if (!__DEV__ || !isWeb()) return;

  const forced = (() => {
    try {
      return window.localStorage?.getItem("cl_force_api_base") || "";
    } catch {
      return "";
    }
  })();
  const verbose = (() => {
    try {
      return window.localStorage?.getItem("cl_verbose_network") === "1";
    } catch {
      return false;
    }
  })();
  const preferred =
    forced && /^https?:\/\//.test(forced)
      ? forced.replace(/\/$/, "")
      : API_BASE;

  const shouldRewrite = (url: string) =>
    !!preferred &&
    (url.includes("api.cosmiclens.app") ||
      url.startsWith(PRODUCTION_API_URL));

  const orig = globalThis.fetch?.bind(globalThis);
  if (!orig) return;
  if ((globalThis as { __cosmic_fetch_wrapped?: boolean }).__cosmic_fetch_wrapped) return;
  (globalThis as { __cosmic_fetch_wrapped?: boolean }).__cosmic_fetch_wrapped = true;

  globalThis.fetch = (async (input: RequestInfo | URL, init?: RequestInit) => {
    const method = (
      init?.method ||
      (typeof input === "object" && "method" in input ? input.method : undefined) ||
      "GET"
    ).toUpperCase();
    const urlStr =
      typeof input === "string"
        ? input
        : input instanceof URL
          ? input.href
          : String((input as Request).url);

    let nextInput: RequestInfo | URL = input;
    if (typeof urlStr === "string" && shouldRewrite(urlStr)) {
      const rewritten = urlStr
        .replace(/^https?:\/\/api\.cosmiclens\.app/i, preferred)
        .replace(
          new RegExp(
            `^${PRODUCTION_API_URL.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}`,
            "i",
          ),
          preferred,
        );
      console.warn("[CosmicLens][dev] Rewriting fetch URL:", urlStr, "→", rewritten);
      nextInput = rewritten;
    }

    try {
      if (verbose) console.log("[CosmicLens][dev] fetch", method, urlStr);
      const res = await orig(nextInput, init);
      if (!res.ok) {
        console.warn("[CosmicLens][dev] HTTP", res.status, method, urlStr);
      }
      return res;
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      console.error("[CosmicLens][dev] fetch failed:", method, urlStr, msg);
      throw e;
    }
  }) as typeof fetch;
}

/** Bases to try for login (VPS first — no silent localhost unless opted in). */
export function demoLoginApiBases(): string[] {
  const seen = new Set<string>();
  const out: string[] = [];
  const add = (b: string) => {
    const n = b.replace(/\/$/, "");
    if (n && !seen.has(n)) {
      seen.add(n);
      out.push(n);
    }
  };

  add(API_BASE);
  const configured = configuredApiUrl();
  if (configured && /^https?:\/\//.test(configured)) {
    add(configured.replace(/\/$/, ""));
  }
  if (__DEV__) {
    add(DEFAULT_DEV_VPS_API);
    if (useLocalBackend()) {
      add("http://127.0.0.1:8080");
      const lan = expoDevMachineHost();
      if (lan) add(`http://${lan}:8080`);
    }
  }
  if (!__DEV__ || API_BASE !== PRODUCTION_API_URL) {
    add(PRODUCTION_API_URL);
  }
  return out;
}

export const API_HEADERS: Record<string, string> = {
  "Content-Type": "application/json",
  Accept: "application/json",
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
  try {
    return await fetch(url, merged);
  } catch (e: unknown) {
    if (e instanceof Error && e.name === "AbortError") throw e;
    const msg = String(e instanceof Error ? e.message : e);
    if (!/Network request failed|TypeError|fetch/i.test(msg)) throw e;
    await new Promise((r) => setTimeout(r, 600));
    return fetch(url, merged);
  }
}

if (__DEV__) {
  installDevFetchInterceptor();
  console.log("[CosmicLens] API_BASE resolved to:", API_BASE);
  if (/localhost|127\.0\.0\.1/i.test(API_BASE) && !useLocalBackend()) {
    console.warn(
      "[CosmicLens] API is localhost but EXPO_PUBLIC_USE_LOCAL_API is not set. " +
        "Use EXPO_PUBLIC_API_URL=http://187.127.174.55:8080 in .env and restart Metro.",
    );
  }

  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), 8000);
  apiFetch(`${API_BASE}/api/healthz`, { signal: ctrl.signal })
    .then((r) => r.json())
    .then((d) => console.log("[CosmicLens] healthz OK ✓", JSON.stringify(d)))
    .catch((e) =>
      console.error(
        "[CosmicLens] healthz FAILED:",
        e instanceof Error ? e.message : e,
        "→",
        `${API_BASE}/api/healthz`,
      ),
    )
    .finally(() => clearTimeout(timer));
}
