/** Cosmic Pack referral — share code; friend buys V1/V3 → you get 3 free Ask Q. */
import AsyncStorage from "@react-native-async-storage/async-storage";

import { API_BASE } from "@/lib/apiConfig";

const PENDING_REF_KEY = "cosmic.packReferral.pendingCode";

export type PackReferralMine = {
  ok?: boolean;
  referral_code: string;
  share_message: string;
  reward_per_referral?: number;
  friends_converted?: number;
  questions_earned?: number;
  bonus_questions_left?: number;
  how_it_works?: string[];
  error?: string;
};

function authHeaders(user: { id: number; api_key?: string | null }): Record<string, string> {
  return {
    "Content-Type": "application/json",
    "X-User-Id": String(user.id),
    ...(user.api_key ? { "X-API-Key": user.api_key } : {}),
  };
}

export async function fetchPackReferralMine(
  user: { id: number; api_key?: string | null },
): Promise<PackReferralMine> {
  const resp = await fetch(`${API_BASE}/api/pack-referral/mine`, {
    headers: authHeaders(user),
  });
  const data = (await resp.json().catch(() => ({}))) as PackReferralMine;
  if (!resp.ok) {
    throw new Error(data.error || `referral ${resp.status}`);
  }
  return data;
}

export async function attachPackReferralCode(
  user: { id: number; api_key?: string | null },
  code: string,
): Promise<{ ok: boolean; error?: string; already?: boolean }> {
  const resp = await fetch(`${API_BASE}/api/pack-referral/attach`, {
    method: "POST",
    headers: authHeaders(user),
    body: JSON.stringify({ referral_code: code.trim() }),
  });
  const data = (await resp.json().catch(() => ({}))) as {
    ok?: boolean;
    error?: string;
    already?: boolean;
  };
  if (!resp.ok || data.ok === false) {
    return { ok: false, error: data.error || `attach ${resp.status}` };
  }
  return { ok: true, already: !!data.already };
}

export async function savePendingReferralCode(code: string): Promise<void> {
  const c = code.trim().toUpperCase();
  if (!c) return;
  try {
    await AsyncStorage.setItem(PENDING_REF_KEY, c);
  } catch {
    /* ignore */
  }
}

export async function loadPendingReferralCode(): Promise<string> {
  try {
    return ((await AsyncStorage.getItem(PENDING_REF_KEY)) || "").trim().toUpperCase();
  } catch {
    return "";
  }
}

export async function clearPendingReferralCode(): Promise<void> {
  try {
    await AsyncStorage.removeItem(PENDING_REF_KEY);
  } catch {
    /* ignore */
  }
}

/** Attach pending code to account (before pack buy). Returns code if any. */
export async function applyPendingReferralIfAny(
  user: { id: number; api_key?: string | null } | null | undefined,
): Promise<string> {
  const code = await loadPendingReferralCode();
  if (!code || !user?.id || !user.api_key) return code;
  const res = await attachPackReferralCode(user, code);
  if (res.ok || res.error === "self_referral_not_allowed") {
    // Keep code for checkout body even if already attached.
    if (res.ok) await clearPendingReferralCode();
  }
  return code;
}
