/** Phone push (works with Chrome closed): service worker + Web Push subscribe. */
import { fetchVapidPublicKey, saveAdminPushSubscription } from "./api";

function urlBase64ToUint8Array(base64: string): Uint8Array {
  const padding = "=".repeat((4 - (base64.length % 4)) % 4);
  const b64 = (base64 + padding).replace(/-/g, "+").replace(/_/g, "/");
  const raw = atob(b64);
  const out = new Uint8Array(raw.length);
  for (let i = 0; i < raw.length; i++) out[i] = raw.charCodeAt(i);
  return out;
}

export function pushSupported(): boolean {
  return "serviceWorker" in navigator && "PushManager" in window && "Notification" in window;
}

export async function isPushSubscribed(): Promise<boolean> {
  if (!pushSupported()) return false;
  try {
    const reg = await navigator.serviceWorker.getRegistration();
    if (!reg) return false;
    const sub = await reg.pushManager.getSubscription();
    return !!sub;
  } catch {
    return false;
  }
}

/**
 * If the browser already holds a subscription, re-save it on the server.
 * Heals the case where subscribe succeeded locally but the server save
 * failed (e.g. backend was down at the time). Safe to call on every load.
 */
export async function resyncPushSubscription(): Promise<boolean> {
  if (!pushSupported()) return false;
  try {
    const reg = await navigator.serviceWorker.getRegistration();
    const sub = reg ? await reg.pushManager.getSubscription() : null;
    if (!sub) return false;
    const saved = await saveAdminPushSubscription(sub.toJSON());
    return !!saved.ok;
  } catch {
    return false;
  }
}

/** Full flow: register SW → ask permission → subscribe → save on server. */
export async function enableAdminPush(): Promise<{ ok: boolean; error?: string }> {
  if (!pushSupported()) {
    return { ok: false, error: "Is browser mein push support nahi hai (Chrome use karo)." };
  }
  try {
    const reg = await navigator.serviceWorker.register("/sw.js");
    await navigator.serviceWorker.ready;

    const perm = await Notification.requestPermission();
    if (perm !== "granted") {
      return { ok: false, error: "Notification permission deni hogi (Allow dabao)." };
    }

    const { key } = await fetchVapidPublicKey();
    let sub = await reg.pushManager.getSubscription();
    if (!sub) {
      sub = await reg.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: urlBase64ToUint8Array(key) as BufferSource,
      });
    }
    const saved = await saveAdminPushSubscription(sub.toJSON());
    if (!saved.ok) return { ok: false, error: saved.error || "Server save failed" };
    return { ok: true };
  } catch (e) {
    return { ok: false, error: e instanceof Error ? e.message : "Push setup failed" };
  }
}
