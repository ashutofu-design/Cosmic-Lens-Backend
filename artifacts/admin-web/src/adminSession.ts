const ENV_API_BASE = (import.meta.env.VITE_API_BASE || "").replace(/\/$/, "");
const ENV_ADMIN_TOKEN = (import.meta.env.VITE_ADMIN_SECRET || "").trim();

const STORAGE_TOKEN = "cl_admin_token";
const STORAGE_API = "cl_admin_api_base";

/** VPS nginx :80 — mobile networks often block :8080 */
export const DEFAULT_VPS_API = "http://187.127.174.55";

export function getAdminApiBase(): string {
  try {
    const stored = sessionStorage.getItem(STORAGE_API)?.trim();
    if (stored) return stored.replace(/\/$/, "");
  } catch {
    /* private mode */
  }
  return ENV_API_BASE || DEFAULT_VPS_API;
}

export function getAdminToken(): string {
  try {
    const stored = sessionStorage.getItem(STORAGE_TOKEN)?.trim();
    if (stored) return stored;
  } catch {
    /* private mode */
  }
  return ENV_ADMIN_TOKEN;
}

export function isAdminConfigured(): boolean {
  return Boolean(getAdminToken());
}

export function saveAdminSession(apiBase: string, token: string): void {
  sessionStorage.setItem(STORAGE_API, apiBase.replace(/\/$/, ""));
  sessionStorage.setItem(STORAGE_TOKEN, token.trim());
}

export function clearAdminSession(): void {
  sessionStorage.removeItem(STORAGE_API);
  sessionStorage.removeItem(STORAGE_TOKEN);
}
