/**
 * Background sync: pull founder-delivered PDFs without manual Fetch.
 * Polls while app is active; syncs immediately when app returns to foreground.
 */
import { AppState, type AppStateStatus } from "react-native";

import { syncServerReportsForUser } from "@/lib/serverMyReports";

const POLL_MS = 120_000;

let pollTimer: ReturnType<typeof setInterval> | null = null;
let activeUserId: number | null = null;
let activeApiKey: string | null = null;
let syncing = false;
const listeners = new Set<(added: number) => void>();

function emit(added: number) {
  if (added <= 0) return;
  listeners.forEach((fn) => {
    try {
      fn(added);
    } catch {
      /* ignore */
    }
  });
}

async function tick(): Promise<void> {
  if (!activeUserId || !activeApiKey || syncing) return;
  syncing = true;
  try {
    const result = await syncServerReportsForUser({
      userId: activeUserId,
      apiKey: activeApiKey,
    });
    if (result.added > 0 || (result.pendingSynced || 0) > 0) {
      emit(Math.max(result.added, result.pendingSynced || 0));
    }
  } finally {
    syncing = false;
  }
}

function onAppStateChange(state: AppStateStatus) {
  if (state === "active") void tick();
}

let appStateSub: { remove?: () => void } | null = null;

export function subscribeNewReports(handler: (added: number) => void): () => void {
  listeners.add(handler);
  return () => listeners.delete(handler);
}

export function startReportAutoSync(userId: number, apiKey: string): void {
  stopReportAutoSync();
  activeUserId = userId;
  activeApiKey = apiKey;
  void tick();
  pollTimer = setInterval(() => void tick(), POLL_MS);
  if (!appStateSub) {
    appStateSub = AppState.addEventListener?.("change", onAppStateChange) ?? null;
  }
}

export function stopReportAutoSync(): void {
  if (pollTimer) clearInterval(pollTimer);
  pollTimer = null;
  activeUserId = null;
  activeApiKey = null;
  syncing = false;
}
