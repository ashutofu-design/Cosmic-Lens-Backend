/**
 * Love Reality Pro in-app report — device cache (no LLM / no API on repeat open).
 */
import AsyncStorage from "@react-native-async-storage/async-storage";

import { LOVE_REALITY_PDF_LAYOUT_VER } from "@/lib/loveRealityPdfLayout";
import { packLovePerson } from "@/lib/loveRealityProPdfDownload";
import type { LoveProReportResponse } from "@/lib/loveRealityProReport";
import { coerceProPdfLang } from "@/lib/proPdfLang";
import type { BirthData } from "@/types";

const STORAGE_PREFIX = "cosmic.loveRealityProReport.v1";

const session = new Map<string, LoveProReportResponse>();

export function loveReportCacheKey(opts: {
  userId: number;
  p1: BirthData;
  p2: BirthData;
  p1Name: string;
  p2Name: string;
  lang: string;
}): string {
  const lang = coerceProPdfLang(opts.lang);
  const a = packLovePerson(opts.p1, opts.p1Name);
  const b = packLovePerson(opts.p2, opts.p2Name);
  return `${STORAGE_PREFIX}:${opts.userId}:${lang}:${LOVE_REALITY_PDF_LAYOUT_VER}:${JSON.stringify(a)}:${JSON.stringify(b)}`;
}

export function getSessionLoveReport(key: string): LoveProReportResponse | null {
  return session.get(key) ?? null;
}

export function setSessionLoveReport(key: string, data: LoveProReportResponse): void {
  session.set(key, data);
}

export async function loadCachedLoveReport(key: string): Promise<LoveProReportResponse | null> {
  const mem = getSessionLoveReport(key);
  if (mem?.ok) return mem;
  try {
    const raw = await AsyncStorage.getItem(key);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as LoveProReportResponse;
    if (
      !parsed?.ok
      || !parsed.pro_premium
      || !parsed.pdf_context
      || !parsed.page1
    ) {
      return null;
    }
    setSessionLoveReport(key, parsed);
    return parsed;
  } catch {
    return null;
  }
}

export async function saveCachedLoveReport(
  key: string,
  data: LoveProReportResponse,
): Promise<void> {
  if (!data?.ok) return;
  setSessionLoveReport(key, data);
  try {
    await AsyncStorage.setItem(key, JSON.stringify(data));
  } catch {
    /* quota / web — session cache still works this visit */
  }
}
