/**
 * Unread / new-report count for My Reports badges (1, 2, …).
 * Increments when auto-sync finds new PDFs; clears when user opens My Reports.
 */
import AsyncStorage from "@react-native-async-storage/async-storage";
import { useCallback, useEffect, useState } from "react";

import { subscribeNewReports } from "@/lib/reportAutoSync";

const STORAGE_KEY = "cl_unread_reports_count";

let memoryCount = 0;
let hydrated = false;
const countListeners = new Set<(n: number) => void>();

function emitCount(n: number) {
  memoryCount = Math.max(0, n);
  countListeners.forEach((fn) => {
    try {
      fn(memoryCount);
    } catch {
      /* ignore */
    }
  });
}

async function hydrate(): Promise<number> {
  if (hydrated) return memoryCount;
  try {
    const raw = await AsyncStorage.getItem(STORAGE_KEY);
    const n = Math.max(0, parseInt(raw || "0", 10) || 0);
    memoryCount = n;
  } catch {
    memoryCount = 0;
  }
  hydrated = true;
  emitCount(memoryCount);
  return memoryCount;
}

async function persist(n: number): Promise<void> {
  memoryCount = Math.max(0, n);
  emitCount(memoryCount);
  try {
    await AsyncStorage.setItem(STORAGE_KEY, String(memoryCount));
  } catch {
    /* ignore */
  }
}

export function getUnreadReportsCount(): number {
  return memoryCount;
}

export async function addUnreadReports(added: number): Promise<void> {
  if (added <= 0) return;
  await hydrate();
  await persist(memoryCount + added);
}

export async function clearUnreadReports(): Promise<void> {
  await hydrate();
  await persist(0);
}

export function subscribeUnreadReportsCount(
  handler: (count: number) => void,
): () => void {
  countListeners.add(handler);
  void hydrate().then((n) => handler(n));
  return () => countListeners.delete(handler);
}

/** Hook: live unread count for My Reports badges. */
export function useUnreadReportsCount(): number {
  const [count, setCount] = useState(memoryCount);

  useEffect(() => {
    return subscribeUnreadReportsCount(setCount);
  }, []);

  return count;
}

export function useClearUnreadReportsOnFocus(): () => void {
  return useCallback(() => {
    void clearUnreadReports();
  }, []);
}

/** Call once at app start — bridges auto-sync → badge count. */
let bridgeInstalled = false;
export function installUnreadReportsBridge(): void {
  if (bridgeInstalled) return;
  bridgeInstalled = true;
  void hydrate();
  subscribeNewReports((added) => {
    void addUnreadReports(added);
  });
}
