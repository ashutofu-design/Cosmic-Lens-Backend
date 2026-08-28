import { getAdminDeviceId } from "./adminDevice";

const API_BASE = (import.meta.env.VITE_API_BASE || "").replace(/\/$/, "");

const GATE_KEY = "cosmic_admin_gate";
const GATE_EXP_KEY = "cosmic_admin_gate_exp";

type GateState = { token: string; expiresAt: number };

function readGate(): GateState | null {
  try {
    const token = (sessionStorage.getItem(GATE_KEY) || "").trim();
    const exp = Number(sessionStorage.getItem(GATE_EXP_KEY) || 0);
    if (!token || !exp) return null;
    return { token, expiresAt: exp };
  } catch {
    return null;
  }
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
  try {
    sessionStorage.removeItem(GATE_KEY);
    sessionStorage.removeItem(GATE_EXP_KEY);
  } catch {
    /* ignore */
  }
}

export function storeAdminGate(token: string, expiresAt: number): void {
  try {
    sessionStorage.setItem(GATE_KEY, token);
    sessionStorage.setItem(GATE_EXP_KEY, String(expiresAt));
  } catch {
    /* ignore */
  }
}

export async function unlockAdminPanel(steps: string[]): Promise<void> {
  const deviceId = getAdminDeviceId();
  const res = await fetch(`${API_BASE}/api/admin/panel-unlock`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
      "X-Admin-Device-Id": deviceId,
    },
    body: JSON.stringify({ device_id: deviceId, steps }),
  });
  const data = (await res.json().catch(() => ({}))) as {
    gate_token?: string;
    expires_at?: number;
    error?: string;
  };
  if (!res.ok || !data.gate_token || !data.expires_at) {
    throw new Error(data.error || `Panel unlock failed (${res.status})`);
  }
  storeAdminGate(data.gate_token, Number(data.expires_at));
}
