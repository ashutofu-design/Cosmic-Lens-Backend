/**
 * Cosmic Lens — Push Notification client (Expo).
 *
 * SDK 53+ NOTE: expo-notifications removed Android push support in Expo Go.
 * Importing the module on Android Expo Go throws at module-init time, so we
 * use a guarded lazy require + a global IS_PUSH_SUPPORTED gate. All exports
 * become safe no-ops when push is unsupported (Expo Go on Android, web, etc.).
 *
 * Flow on a real dev build / iOS Expo Go:
 *   1) registerForPushAsync() — asks permission, returns ExpoPushToken or null
 *   2) registerTokenWithServer(userId, token) — POSTs to /api/notifications/register
 *   3) configureForeground() — sets handler so notifications show in-app too
 *   4) attachTapHandler(router) — on tap, navigate to data.screen
 */

import Constants from "expo-constants";
import { Platform } from "react-native";
import { API_BASE, apiFetch } from "./apiConfig";

// ── Detect Expo Go (push removed in SDK 53 on Android) ──────────────────────
const IS_EXPO_GO = (Constants as any)?.appOwnership === "expo";
const IS_WEB     = Platform.OS === "web";
const IS_PUSH_SUPPORTED =
  !IS_WEB && !(IS_EXPO_GO && Platform.OS === "android");

// ── Lazy guarded loader for expo-notifications + expo-device ────────────────
let _Notifications: any = null;
let _Device: any = null;
let _loadAttempted = false;

function loadModules(): boolean {
  if (_loadAttempted) return _Notifications != null;
  _loadAttempted = true;
  if (!IS_PUSH_SUPPORTED) {
    console.log("[push] disabled — Expo Go on Android / web");
    return false;
  }
  try {
    _Notifications = require("expo-notifications");
    _Device        = require("expo-device");
    return true;
  } catch (e: any) {
    console.warn("[push] expo-notifications unavailable:", e?.message || e);
    return false;
  }
}

// ── Foreground handler: show banner + sound even when app is open ────────────
export function configureForeground() {
  if (!loadModules()) return;
  try {
    _Notifications.setNotificationHandler({
      handleNotification: async () => ({
        shouldShowBanner: true,
        shouldShowList:   true,
        shouldPlaySound:  true,
        shouldSetBadge:   false,
        shouldShowAlert:  true,
      } as any),
    });
  } catch (e: any) {
    console.warn("[push] configureForeground failed:", e?.message || e);
  }
}

// ── Android channel — required for heads-up notifications ───────────────────
async function ensureAndroidChannel() {
  if (Platform.OS !== "android") return;
  if (!loadModules()) return;
  try {
    await _Notifications.setNotificationChannelAsync("default", {
      name:              "Cosmic Lens",
      importance:        _Notifications.AndroidImportance.HIGH,
      vibrationPattern:  [0, 250, 250, 250],
      lightColor:        "#a78bfa",
      sound:             "default",
    });
  } catch (e: any) {
    console.warn("[push] android channel failed:", e?.message || e);
  }
}

/**
 * Ask permission and obtain an ExpoPushToken. Returns null if:
 *  - running on a simulator/emulator (won't get a real token)
 *  - user denied permission
 *  - running on web or Expo Go (Android)
 */
export async function registerForPushAsync(): Promise<string | null> {
  if (!loadModules()) return null;
  if (!_Device?.isDevice) {
    console.log("[push] skip — not a physical device");
    return null;
  }

  await ensureAndroidChannel();

  try {
    const { status: existing } = await _Notifications.getPermissionsAsync();
    let finalStatus = existing;
    if (existing !== "granted") {
      const { status } = await _Notifications.requestPermissionsAsync();
      finalStatus = status;
    }
    if (finalStatus !== "granted") {
      console.log("[push] permission not granted");
      return null;
    }

    const projectId =
      (Constants.expoConfig as any)?.extra?.eas?.projectId ||
      (Constants as any)?.easConfig?.projectId;
    const tokenData = await _Notifications.getExpoPushTokenAsync(
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

/** Listen for taps and navigate to data.screen if provided. Returns null on unsupported platforms. */
export function attachTapHandler(navigate: (path: string) => void) {
  if (!loadModules()) return null;
  try {
    return _Notifications.addNotificationResponseReceivedListener((resp: any) => {
      const screen = (resp.notification.request.content.data as any)?.screen;
      if (typeof screen === "string" && screen.startsWith("/")) {
        try { navigate(screen); } catch (e) { console.warn("[push] nav failed", e); }
      }
    });
  } catch (e: any) {
    console.warn("[push] attachTapHandler failed:", e?.message || e);
    return null;
  }
}
