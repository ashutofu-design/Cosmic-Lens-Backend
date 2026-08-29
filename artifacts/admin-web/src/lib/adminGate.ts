import { resolveApiBase } from "./apiBase";
import { getAdminDeviceId } from "./adminDevice";

function apiBase(): string {
  return resolveApiBase();
}

const GATE_KEY = "cosmic_admin_gate";
const GATE_EXP_KEY = "cosmic_admin_gate_exp";

type GateState = { token: string; expiresAt: number };

function readFromStore(store: Storage): GateState | null {
  try {
    const token = (store.getItem(GATE_KEY) || "").trim();
    const exp = Number(store.getItem(GATE_EXP_KEY) || 0);
    if (!token || !exp) return null;
    return { token, expiresAt: exp };
  } catch {
    return null;
  }
}

function readGate(): GateState | null {
  return readFromStore(sessionStorage) || readFromStore(localStorage);
}

export function hasValidAdminGate(): boolean {
  if (import.meta.env.VITE_ADMIN_SECURITY_RELAXED === "1") return true;
  const gate = readGate();
  if (!gate) return false;
  return gate.expiresAt * 1000 > Date.now() + 5_000;
}

export function getAdminGateToken(): string {
  return readGate()?.token || "";
}

export function clearAdminGate(): void {
  for (const store of [sessionStorage, localStorage]) {
    try {
      store.removeItem(GATE_KEY);
      store.removeItem(GATE_EXP_KEY);
    } catch {
      /* ignore */
    }
  }
}

export function storeAdminGate(token: string, expiresAt: number): void {
  for (const store of [sessionStorage, localStorage]) {
    try {
      store.setItem(GATE_KEY, token);
      store.setItem(GATE_EXP_KEY, String(expiresAt));
    } catch {
      /* ignore */
    }
  }
}

export async function unlockAdminPanel(steps: string[]): Promise<void> {
  if (!apiBase()) {
    throw new Error(
      "API URL set nahi — admin.coosmic.icu pe rebuild karo ya nginx /api proxy check karo.",
    );
  }

  const deviceId = getAdminDeviceId();
  const url = `${apiBase()}/api/admin/panel-unlock`;
  const controller = new AbortController();
  const timer = window.setTimeout(() => controller.abort(), 20_000);

  let res: Response;
  try {
    res = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
        "X-Admin-Device-Id": deviceId,
      },
      body: JSON.stringify({ device_id: deviceId, steps }),
      signal: controller.signal,
    });
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") {
      throw new Error(
        "API timeout (20s) — admin.coosmic.icu/api nginx proxy check karo.",
      );
    }
    throw new Error(
      err instanceof Error ? err.message : "Network error — API tak pahunch nahi paaye.",
    );
  } finally {
    window.clearTimeout(timer);
  }

  const raw = await res.text();
  let data: { gate_token?: string; expires_at?: number; error?: string } = {};
  try {
    data = JSON.parse(raw) as typeof data;
  } catch {
    if (/<!doctype|<html/i.test(raw)) {
      throw new Error(
        `API galat URL pe ja rahi hai (${url}). VPS pe dubara build karo: VITE_API_BASE=https://api.coosmic.icu`,
      );
    }
    throw new Error(`Panel unlock failed — server ne JSON nahi bheja (${res.status})`);
  }

  if (!res.ok || !data.gate_token || !data.expires_at) {
    const code = String(data.error || "").trim();
    if (code === "invalid_sequence") {
      throw new Error("Unlock sequence galat — pehle locate ×3, phir For ×3.");
    }
    if (code === "rate_limited") {
      throw new Error("Bahut zyada unlock tries — 30 min wait karo, phir dubara.");
    }
    if (code === "security_disabled") {
      throw new Error("Server pe admin security band hai — ADMIN_SECRET check karo.");
    }
    throw new Error(data.error || `Panel unlock failed (${res.status})`);
  }

  storeAdminGate(data.gate_token, Number(data.expires_at));
  if (!hasValidAdminGate()) {
    throw new Error("Unlock save nahi hua — browser storage / private mode check karo.");
  }
}
