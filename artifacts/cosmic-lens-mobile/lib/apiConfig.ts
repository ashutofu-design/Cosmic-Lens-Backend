import Constants from "expo-constants";
import { Platform } from "react-native";

// ─────────────────────────────────────────────────────────────────────────────
// API endpoint resolution.
//
// Priority (highest first):
//   1. EXPO_PUBLIC_API_URL (from .env — baked in at Metro start)
//   2. expo.extra.apiUrl (from app.config.js — VPS default)
//   3. PRODUCTION_API_URL (release builds)
//   4. DEV VPS fallback (never localhost unless EXPO_PUBLIC_USE_LOCAL_API=1)
//
// Set in artifacts/cosmic-lens-mobile/.env:
//   EXPO_PUBLIC_API_URL=http://187.127.174.55:8080
// After changing .env: stop Metro (Ctrl+C) and run `npx expo start` again.
// ─────────────────────────────────────────────────────────────────────────────

/** VPS public IP — nginx on :80 (preferred; mobile networks often block :8080). */
const VPS_PUBLIC_IP = "187.127.174.55";
const VPS_API_NGINX = `http://${VPS_PUBLIC_IP}`;
/** Direct gunicorn — default dev / preview API. */
const DEFAULT_DEV_VPS_API = `http://${VPS_PUBLIC_IP}:8080`;
const PRODUCTION_API_URL = DEFAULT_DEV_VPS_API;

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
  const allowHttpRelease =
    (process.env.EXPO_PUBLIC_ALLOW_HTTP_API || "").trim() === "1";
  if (!__DEV__ && !normalized.startsWith("https://") && !allowHttpRelease) {
    console.warn("[CosmicLens] Ignoring non-HTTPS API URL in production build.");
    return null;
  }
  return rewriteLocalDevHost(normalized);
}

function isRawVpsIpUrl(url: string): boolean {
  return /187\.127\.174\.55|:8080(\/|$)/.test(url) && !/coosmic\.icu/i.test(url);
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

  const vps = normalizeApiUrl(DEFAULT_DEV_VPS_API);
  if (vps) return vps;

  return `https://${DEV_REPLIT_DOMAIN}`;
}

export const API_BASE = resolveApiBase();

function installDevFetchInterceptor(): void {
  if (!__DEV__ || !isWeb()) return;

  try {
    const forced = window.localStorage?.getItem("cl_force_api_base") || "";
    if (forced && isRawVpsIpUrl(forced)) {
      window.localStorage.removeItem("cl_force_api_base");
      console.warn("[CosmicLens] Cleared stale cl_force_api_base (blocked VPS IP)");
    }
  } catch {
    // ignore
  }

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
    (url.includes("api.cosmiclens.app") || url.startsWith(PRODUCTION_API_URL));

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

/**
 * Ordered API bases for retries when the primary host is down or blocked.
 */
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

  const configured = configuredApiUrl();
  const configuredNorm = configured
    ? normalizeApiUrl(configured) || configured.replace(/\/$/, "")
    : null;

  // Laptop web: sirf configured URL (localhost proxy ya domain) — IP retry mat karo
  if (__DEV__ && isWeb() && configuredNorm && !isRawVpsIpUrl(configuredNorm)) {
    add(configuredNorm);
    return out.filter(Boolean);
  }

  add(API_BASE);
  if (configuredNorm) add(configuredNorm);
  if (!__DEV__ || !isWeb()) {
    add(VPS_API_NGINX);
    add(PRODUCTION_API_URL);
  }
  if (__DEV__ && !isWeb()) {
    add(DEFAULT_DEV_VPS_API);
    if (useLocalBackend()) {
      add("http://127.0.0.1:8080");
      const lan = expoDevMachineHost();
      if (lan) add(`http://${lan}:8080`);
    }
  }
  return out;
}

/** @alias demoLoginApiBases */
export const apiFetchBases = demoLoginApiBases;

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

const DEFAULT_FETCH_TIMEOUT_MS = 12000;

/** Same as apiFetch but aborts after `ms` — avoids infinite spinner on dead API hosts. */
export async function apiFetchWithTimeout(
  url: string,
  init?: RequestInit,
  ms = DEFAULT_FETCH_TIMEOUT_MS,
): Promise<Response> {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), ms);
  try {
    return await apiFetch(url, { ...init, signal: ctrl.signal });
  } finally {
    clearTimeout(timer);
  }
}

const HEALTH_PROBE_TIMEOUT_MS = 6000;

export type ApiHealthProbe = {
  ok: boolean;
  base?: string;
  data?: unknown;
  tried: string[];
};

/** Probe /api/healthz across fallback bases (same order as auth retries). */
export async function probeApiHealth(
  bases: string[] = demoLoginApiBases(),
): Promise<ApiHealthProbe> {
  const tried: string[] = [];
  for (const base of bases) {
    tried.push(base);
    const ctrl = new AbortController();
    const timer = setTimeout(() => ctrl.abort(), HEALTH_PROBE_TIMEOUT_MS);
    try {
      const res = await apiFetch(`${base}/api/healthz`, { signal: ctrl.signal });
      if (!res.ok) continue;
      const data = await res.json().catch(() => null);
      if (data?.status === "ok") return { ok: true, base, data, tried };
    } catch {
      // try next base
    } finally {
      clearTimeout(timer);
    }
  }
  return { ok: false, tried };
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

  void probeApiHealth().then(({ ok, base, data, tried }) => {
    if (ok) {
      console.log(
        `[CosmicLens] healthz OK ✓ via ${base}`,
        JSON.stringify(data),
      );
      return;
    }
    console.warn(
      "[CosmicLens] healthz FAILED — no API responded within",
      `${HEALTH_PROBE_TIMEOUT_MS}ms per host.`,
      "\nTried:",
      tried.join(", "),
      "\nFix: VPS par nginx :80 → :8080 proxy (scripts/vps-nginx-port80-paste.sh),",
      `\n.env → EXPO_PUBLIC_API_URL=${VPS_API_NGINX}, Metro restart.`,
    );
  });
}
