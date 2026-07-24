import type { AuthUser } from "@/context/UserContext";
import { API_BASE, apiFetchWithTimeout, demoLoginApiBases } from "./apiConfig";

type FirebaseVerifyResponse = AuthUser & {
  ok?: boolean;
  error?: string;
  is_new_user?: boolean;
};

function authApiBases(): string[] {
  return demoLoginApiBases().map((b) =>
    // Never POST over http://admin… — certbot 301 turns POST→GET → {"error":"Not found"}.
    b.replace(/^http:\/\/admin\.coosmic\.icu/i, "https://admin.coosmic.icu"),
  );
}

export function isAuthNetworkError(e: unknown): boolean {
  const msg = String((e as Error)?.message || e || "");
  return /Network request failed|Failed to fetch|Load failed|fetch|Aborted|AbortError|timeout/i.test(
    msg,
  );
}

function parseVerifyResponse(raw: string): FirebaseVerifyResponse {
  try {
    return raw ? JSON.parse(raw) : {};
  } catch {
    if (/<!DOCTYPE|<html/i.test(raw) && /404|Not Found/i.test(raw)) {
      throw new Error(
        "Login API not reachable (404). Check EXPO_PUBLIC_API_URL uses https://api.coosmic.icu",
      );
    }
    throw new Error("Network error — server returned invalid response.");
  }
}

export type AuthSession = {
  user: AuthUser;
  /** True when backend created this account on this login (HTTP 201 / is_new_user). */
  isNewUser: boolean;
};

function mapAuthUser(data: FirebaseVerifyResponse, name?: string): AuthUser {
  if (!data.id || !data.api_key) {
    throw new Error(data.error || "Login could not be completed — server did not return an account.");
  }
  return {
    id: data.id,
    cosmo_user_id: data.cosmo_user_id ?? null,
    name: data.name || name || "",
    email: data.email || "",
    phone: data.phone,
    country_code: data.country_code,
    api_key: data.api_key,
    is_pro: !!data.is_pro,
    plan: data.plan,
    plan_expiry: data.plan_expiry ?? null,
    subscription: data.subscription,
    personal_name_locked: !!(data as AuthUser).personal_name_locked,
    personal_phone_locked: !!(data as AuthUser).personal_phone_locked,
  };
}

function mapAuthSession(data: FirebaseVerifyResponse, name?: string): AuthSession {
  return {
    user: mapAuthUser(data, name),
    isNewUser: !!data.is_new_user,
  };
}

function shouldRetryAuthHost(status: number, errorMsg: string): boolean {
  if (status >= 502 && status <= 504) return true;
  // HTTP→HTTPS redirect often turns POST into GET → Flask catch-all {"error":"Not found"}.
  if (status === 404) return true;
  if (/^not found$/i.test(errorMsg.trim())) return true;
  return false;
}

/** Exchange a Firebase ID token for the Cosmic Lens app user session. */
export async function verifyFirebaseIdToken(idToken: string, name?: string): Promise<AuthSession> {
  const body = JSON.stringify({
    id_token: idToken,
    ...(name?.trim() ? { name: name.trim() } : {}),
  });

  let lastNetworkError = "";
  let lastHttpError = "";

  for (const base of authApiBases()) {
    try {
      const res = await apiFetchWithTimeout(`${base}/api/auth/firebase-verify`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body,
      });

      const raw = await res.text();
      const data = parseVerifyResponse(raw);

      if (!res.ok || data.ok === false) {
        const detail = [data.error, (data as { message?: string }).message]
          .filter(Boolean)
          .join(" — ");
        lastHttpError = detail || `HTTP ${res.status}`;
        if (shouldRetryAuthHost(res.status, data.error || "")) continue;
        throw new Error(lastHttpError);
      }

      const session = mapAuthSession(data, name);
      if (!session.isNewUser && res.status === 201) {
        return { ...session, isNewUser: true };
      }
      return session;
    } catch (e: any) {
      if (isAuthNetworkError(e)) {
        lastNetworkError = String(e?.message || e || "");
        continue;
      }
      throw e;
    }
  }

  if (lastHttpError) {
    const isRouteMiss = /not found|no api route/i.test(lastHttpError);
    const hint = isRouteMiss
      ? " — Server pe Google login route missing. VPS pe chalao: .\\scripts\\deploy-firebase-auth-vps.ps1"
      : "";
    throw new Error(`${lastHttpError}${hint}`);
  }

  const tried = authApiBases().join(", ");
  throw new Error(
    lastNetworkError ||
      `Server tak connection nahi ho paya.\n` +
        `API: ${API_BASE}\n` +
        `Tried: ${tried}\n` +
        `Fix: EXPO_PUBLIC_API_URL=https://api.coosmic.icu aur Metro restart.`,
  );
}
