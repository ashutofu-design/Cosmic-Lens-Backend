import { API_BASE, apiFetch } from "@/lib/apiConfig";

const TIMEOUT_MS = 5000;

async function timedFetch(url: string, init?: RequestInit): Promise<Response> {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), TIMEOUT_MS);
  try {
    return await apiFetch(url, { ...init, signal: ctrl.signal });
  } finally {
    clearTimeout(timer);
  }
}

/** True when the Cosmic Lens API server responds on /api/healthz. */
export async function checkBackendConnected(): Promise<boolean> {
  try {
    const res = await timedFetch(`${API_BASE}/api/healthz`);
    if (!res.ok) return false;
    const data = await res.json().catch(() => null);
    return data?.status === "ok";
  } catch {
    return false;
  }
}

/**
 * True when admin API routes are reachable on the same backend.
 * 200 = admin OK; 401 = routes up (token required from admin panel).
 */
export async function checkAdminConnected(): Promise<boolean> {
  try {
    const headers: Record<string, string> = {};
    const token = (process.env.EXPO_PUBLIC_ADMIN_SECRET || "").trim();
    if (token) headers["X-Admin-Token"] = token;

    const res = await timedFetch(`${API_BASE}/api/admin/stats`, { headers });
    return res.ok || res.status === 401;
  } catch {
    return false;
  }
}

export async function fetchConnectionStatus(): Promise<{
  backend: boolean;
  admin: boolean;
}> {
  const [backend, admin] = await Promise.all([
    checkBackendConnected(),
    checkAdminConnected(),
  ]);
  return { backend, admin };
}
