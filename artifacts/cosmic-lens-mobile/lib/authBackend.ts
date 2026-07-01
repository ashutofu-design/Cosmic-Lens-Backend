import type { AuthUser } from "@/context/UserContext";
import { API_BASE, apiFetchWithTimeout, demoLoginApiBases } from "./apiConfig";

type FirebaseVerifyResponse = AuthUser & {
  ok?: boolean;
  error?: string;
  is_new_user?: boolean;
};

function authApiBases(): string[] {
  return demoLoginApiBases();
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
    throw new Error("Network error — server returned invalid response.");
  }
}

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

/** Exchange a Firebase ID token for the Cosmic Lens app user session. */
export async function verifyFirebaseIdToken(idToken: string, name?: string): Promise<AuthUser> {
  const body = JSON.stringify({
    id_token: idToken,
    ...(name?.trim() ? { name: name.trim() } : {}),
  });

  let lastNetworkError = "";
  let lastHttpError = "";
  let lastBase = API_BASE;

  for (const base of authApiBases()) {
    lastBase = base;
    try {
      const res = await apiFetchWithTimeout(`${base}/api/auth/firebase-verify`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body,
      });

      const raw = await res.text();
      const data = parseVerifyResponse(raw);

      if (!res.ok || data.ok === false) {
        lastHttpError = data.error || `HTTP ${res.status}`;
        if (res.status >= 502 && res.status <= 504) continue;
        throw new Error(lastHttpError);
      }

      return mapAuthUser(data, name);
    } catch (e: any) {
      if (isAuthNetworkError(e)) {
        lastNetworkError = String(e?.message || e || "");
        continue;
      }
      throw e;
    }
  }

  if (lastHttpError) {
    throw new Error(lastHttpError);
  }

  const tried = authApiBases().join(", ");
  throw new Error(
    `Server tak connection nahi ho paya.\n` +
    `API: ${API_BASE}\n` +
    `Tried: ${tried}\n` +
    `VPS andar OK ho sakta hai — phone/laptop se test: curl http://187.127.174.55:8080/api/healthz\n` +
    `Fix: Hostinger hPanel → Firewall → TCP 8080 Allow, ya HTTPS: api.cosmiclens.app + nginx`,
  );
}

/** Dev / QA — POST /api/auth/demo (Pro test user, no Google). */
export async function demoLogin(): Promise<AuthUser> {
  let lastNetworkError = "";
  let lastHttpError = "";

  for (const base of authApiBases()) {
    try {
      const res = await apiFetchWithTimeout(`${base}/api/auth/demo`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: "{}",
      });

      const raw = await res.text();
      const data = parseVerifyResponse(raw);

      if (!res.ok || data.ok === false) {
        lastHttpError =
          data.error ||
          (data as { message?: string }).message ||
          `HTTP ${res.status}`;
        if (res.status >= 502 && res.status <= 504) continue;
        throw new Error(lastHttpError);
      }

      return mapAuthUser(data, "Demo User");
    } catch (e: unknown) {
      if (isAuthNetworkError(e)) {
        lastNetworkError = String((e as Error)?.message || e || "");
        continue;
      }
      throw e;
    }
  }

  if (lastHttpError) throw new Error(lastHttpError);
  throw new Error(
    lastNetworkError ||
      "Server tak connection nahi ho paya (port 8080 bahar se blocked?). " +
      "Hostinger Firewall mein TCP 8080 Allow karein, ya api.cosmiclens.app DNS + nginx setup karein.",
  );
}

export function isDemoLoginEnabled(): boolean {
  if (__DEV__) return true;
  return (process.env.EXPO_PUBLIC_ENABLE_DEMO_LOGIN || "").trim() === "1";
}
