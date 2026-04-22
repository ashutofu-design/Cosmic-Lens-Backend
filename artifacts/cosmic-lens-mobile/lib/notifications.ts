/**
 * Cosmic Lens — Push Notification client (Expo).
 *
 * Flow:
 *   1) registerForPushAsync() — asks permission, returns ExpoPushToken or null
 *   2) registerTokenWithServer(userId, token) — POSTs to /api/notifications/register
 *   3) configureForeground() — sets handler so notifications show in-app too
 *   4) attachTapHandler(router) — on tap, navigate to data.screen
 *
 * Works on iOS + Android. On web/Expo Go (SDK 53+) gracefully no-ops.
 */

import Constants from "expo-constants";
import * as Device from "expo-device";
import * as Notifications from "expo-notifications";
import { Platform } from "react-native";
import { API_BASE, apiFetch } from "./apiConfig";

// ── Foreground handler: show banner + sound even when app is open ────────────
export function configureForeground() {
  Notifications.setNotificationHandler({
    handleNotification: async () => ({
      shouldShowBanner: true,
      shouldShowList:   true,
      shouldPlaySound:  true,
      shouldSetBadge:   false,
      shouldShowAlert:  true,   // legacy SDKs
    } as any),
  });
}

// ── Android channel — required for heads-up notifications ───────────────────
async function ensureAndroidChannel() {
  if (Platform.OS !== "android") return;
  await Notifications.setNotificationChannelAsync("default", {
    name:              "Cosmic Lens",
    importance:        Notifications.AndroidImportance.HIGH,
    vibrationPattern:  [0, 250, 250, 250],
    lightColor:        "#a78bfa",
    sound:             "default",
  });
}

/**
 * Ask permission and obtain an ExpoPushToken. Returns null if:
 *  - running on a simulator/emulator (won't get a real token)
 *  - user denied permission
 *  - running on web
 */
export async function registerForPushAsync(): Promise<string | null> {
  if (Platform.OS === "web") return null;
  if (!Device.isDevice) {
    console.log("[push] skip — not a physical device");
    return null;
  }

  await ensureAndroidChannel();

  const { status: existing } = await Notifications.getPermissionsAsync();
  let finalStatus = existing;
  if (existing !== "granted") {
    const { status } = await Notifications.requestPermissionsAsync();
    finalStatus = status;
  }
  if (finalStatus !== "granted") {
    console.log("[push] permission not granted");
    return null;
  }

  try {
    const projectId =
      (Constants.expoConfig as any)?.extra?.eas?.projectId ||
      (Constants as any)?.easConfig?.projectId;
    const tokenData = await Notifications.getExpoPushTokenAsync(
      projectId ? { projectId } : undefined,
    );
    return tokenData.data || null;
  } catch (e: any) {
    console.warn("[push] getExpoPushTokenAsync failed:", e?.message || e);
    return null;
  }
}

/** POST the device token to backend. Idempotent — safe to call on every login. */
export async function registerTokenWithServer(
  userId: number,
  token: string,
  enabled = true,
): Promise<boolean> {
  try {
    const r = await apiFetch(`${API_BASE}/api/notifications/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: userId, push_token: token, enabled }),
    });
    return r.ok;
  } catch (e) {
    console.warn("[push] register-with-server failed:", e);
    return false;
  }
}

/** One-shot helper: ask permission, get token, send to server. */
export async function setupPushForUser(userId: number): Promise<string | null> {
  const token = await registerForPushAsync();
  if (!token) return null;
  await registerTokenWithServer(userId, token);
  return token;
}

/** Toggle push on/off without losing the token. */
export async function setPushEnabled(userId: number, enabled: boolean): Promise<boolean> {
  try {
    const r = await apiFetch(`${API_BASE}/api/notifications/preferences`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: userId, enabled }),
    });
    return r.ok;
  } catch {
    return false;
  }
}

/** Send a self-test notification (for Settings > "Send test"). */
export async function sendTestNotification(userId: number): Promise<any> {
  try {
    const r = await apiFetch(`${API_BASE}/api/notifications/test`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: userId }),
    });
    return await r.json();
  } catch (e: any) {
    return { error: String(e?.message || e) };
  }
}

/** Listen for taps and navigate to data.screen if provided. */
export function attachTapHandler(navigate: (path: string) => void) {
  return Notifications.addNotificationResponseReceivedListener(resp => {
    const screen = (resp.notification.request.content.data as any)?.screen;
    if (typeof screen === "string" && screen.startsWith("/")) {
      try { navigate(screen); } catch (e) { console.warn("[push] nav failed", e); }
    }
  });
}
