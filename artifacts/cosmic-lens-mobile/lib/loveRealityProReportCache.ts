/**
 * Love Reality Pro in-app report — device cache.
 *
 * Raw JSON (LLM output) is stored under a stable couple key.
 * Revision meta tracks app/PDF layout bumps so code changes refresh
 * presentation without a new LLM call when possible.
 */
import AsyncStorage from "@react-native-async-storage/async-storage";

import { LOVE_REALITY_PDF_LAYOUT_VER } from "@/lib/loveRealityPdfLayout";
import { packLovePerson } from "@/lib/loveRealityPack";
import type { LoveProReportResponse } from "@/lib/loveRealityProReport";
import { enHnReportCacheReady, needsLoveReportLlmRefresh } from "@/lib/loveRealityReportLang";
import {
  currentLoveReportRevision,
  detectLoveReportChange,
  LOVE_REALITY_HI_DEVICE_CACHE_VER,
  LOVE_REALITY_HI_SERVER_CACHE_VER,
  loveReportNeedsPdfResync,
  loveReportRevisionString,
  type LoveReportCacheMeta,
  type LoveReportChangeKind,
} from "@/lib/loveRealityReportRevision";
import { coerceProPdfLang, type ProPdfLangCode } from "@/lib/proPdfLang";
import type { BirthData } from "@/types";

const RAW_PREFIX = "cosmic.loveRealityProReport.raw.v2";
const META_PREFIX = "cosmic.loveRealityProReport.meta.v2";
const PDF_SYNC_PREFIX = "cosmic.loveRealityProReport.pdfSync.v2";
const LEGACY_PREFIX = "cosmic.loveRealityProReport.v1";

const sessionRaw = new Map<string, LoveProReportResponse>();
const sessionMeta = new Map<string, LoveReportCacheMeta>();

export type LoveReportCacheResolve = {
  payload: LoveProReportResponse | null;
  meta: LoveReportCacheMeta | null;
  changeKind: LoveReportChangeKind;
  needsPdfResync: boolean;
  fromSession: boolean;
};

export function loveReportCacheKeys(opts: {
  userId: number;
  p1: BirthData;
  p2: BirthData;
  p1Name: string;
  p2Name: string;
  lang: string;
}): { rawKey: string; metaKey: string; pdfSyncKey: string; coupleKey: string } {
  const lang = coerceProPdfLang(opts.lang);
  const a = packLovePerson(opts.p1, opts.p1Name);
  const b = packLovePerson(opts.p2, opts.p2Name);
  const coupleKey = `${opts.userId}:${lang}:${JSON.stringify(a)}:${JSON.stringify(b)}`;
  return {
    coupleKey,
    rawKey: `${RAW_PREFIX}:${coupleKey}`,
    metaKey: `${META_PREFIX}:${coupleKey}`,
    pdfSyncKey: `${PDF_SYNC_PREFIX}:${coupleKey}`,
  };
}

/** @deprecated use loveReportCacheKeys().rawKey — kept for callers migrating gradually */
export function loveReportCacheKey(opts: {
  userId: number;
  p1: BirthData;
  p2: BirthData;
  p1Name: string;
  p2Name: string;
  lang: string;
}): string {
  return loveReportCacheKeys(opts).rawKey;
}

function isCompletePayload(parsed: LoveProReportResponse | null | undefined): parsed is LoveProReportResponse {
  return Boolean(
    parsed?.ok
    && parsed.pro_premium
    && parsed.pdf_context
    && parsed.page1,
  );
}

export function detectLoveReportCacheChange(meta: LoveReportCacheMeta | null): LoveReportChangeKind {
  return detectLoveReportChange(meta);
}

/** Skip device cache when hn/hi body is still English. */
export function loveReportCacheNeedsLlm(
  payload: LoveProReportResponse | null,
  lang: ProPdfLangCode,
  meta?: LoveReportCacheMeta | null,
): boolean {
  return needsLoveReportLlmRefresh(payload, lang, meta?.contentLang);
}

async function readMeta(metaKey: string): Promise<LoveReportCacheMeta | null> {
  const mem = sessionMeta.get(metaKey);
  if (mem) return mem;
  try {
    const raw = await AsyncStorage.getItem(metaKey);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as LoveReportCacheMeta;
    if (!parsed?.pdfLayoutVer || !parsed?.appReportVer) return null;
    sessionMeta.set(metaKey, parsed);
    return parsed;
  } catch {
    return null;
  }
}

async function readRaw(rawKey: string): Promise<LoveProReportResponse | null> {
  const mem = sessionRaw.get(rawKey);
  if (isCompletePayload(mem)) return mem;
  try {
    const raw = await AsyncStorage.getItem(rawKey);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as LoveProReportResponse;
    if (!isCompletePayload(parsed)) return null;
    sessionRaw.set(rawKey, parsed);
    return parsed;
  } catch {
    return null;
  }
}

async function migrateLegacyRaw(opts: {
  userId: number;
  p1: BirthData;
  p2: BirthData;
  p1Name: string;
  p2Name: string;
  lang: string;
  rawKey: string;
}): Promise<LoveProReportResponse | null> {
  const lang = coerceProPdfLang(opts.lang);
  const a = packLovePerson(opts.p1, opts.p1Name);
  const b = packLovePerson(opts.p2, opts.p2Name);
  const legacyKey = `${LEGACY_PREFIX}:${opts.userId}:${lang}:${LOVE_REALITY_PDF_LAYOUT_VER}:${JSON.stringify(a)}:${JSON.stringify(b)}`;
  try {
    const raw = await AsyncStorage.getItem(legacyKey);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as LoveProReportResponse;
    if (!isCompletePayload(parsed)) return null;
    sessionRaw.set(opts.rawKey, parsed);
    await AsyncStorage.setItem(opts.rawKey, raw);
    await AsyncStorage.removeItem(legacyKey);
    return parsed;
  } catch {
    return null;
  }
}

/**
 * Load cached report + detect whether only layout changed (no LLM) or data is fresh.
 */
export async function resolveLoveReportCache(opts: {
  userId: number;
  p1: BirthData;
  p2: BirthData;
  p1Name: string;
  p2Name: string;
  lang: string;
}): Promise<LoveReportCacheResolve> {
  const { rawKey, metaKey, pdfSyncKey } = loveReportCacheKeys(opts);
  let payload = await readRaw(rawKey);
  if (!payload) {
    payload = await migrateLegacyRaw({ ...opts, rawKey });
  }
  const [meta, pdfSyncedRevision] = await Promise.all([
    readMeta(metaKey),
    AsyncStorage.getItem(pdfSyncKey).catch(() => null),
  ]);

  if (!payload) {
    return {
      payload: null,
      meta: null,
      changeKind: "missing",
      needsPdfResync: false,
      fromSession: false,
    };
  }

  let changeKind = detectLoveReportChange(meta);
  if (changeKind === "missing") {
    // Raw JSON exists but meta lost / legacy entry — reuse text, stamp revision (no LLM).
    changeKind = "app_layout";
  }
  const needsPdfResync = loveReportNeedsPdfResync(meta, pdfSyncedRevision);

  return {
    payload,
    meta,
    changeKind,
    needsPdfResync,
    fromSession: sessionRaw.has(rawKey),
  };
}

export async function clearLoveReportCache(opts: {
  userId: number;
  p1: BirthData;
  p2: BirthData;
  p1Name: string;
  p2Name: string;
  lang: string;
}): Promise<void> {
  const { rawKey, metaKey, pdfSyncKey } = loveReportCacheKeys(opts);
  sessionRaw.delete(rawKey);
  sessionMeta.delete(metaKey);
  try {
    await AsyncStorage.multiRemove([rawKey, metaKey, pdfSyncKey]);
  } catch {
    /* ignore */
  }
}

/** Update Report — wipe device cache for en + hn + hi so old Hindi cannot replay. */
export async function clearLoveReportCacheAllLangs(opts: {
  userId: number;
  p1: BirthData;
  p2: BirthData;
  p1Name: string;
  p2Name: string;
}): Promise<void> {
  for (const lang of ["en", "hn", "hi"] as const) {
    await clearLoveReportCache({ ...opts, lang });
  }
}

/** Wipe Hindi device cache only — used after server hi_cache_ver bump. */
export async function clearLoveReportCacheHiOnly(opts: {
  userId: number;
  p1: BirthData;
  p2: BirthData;
  p1Name: string;
  p2Name: string;
}): Promise<void> {
  await clearLoveReportCache({ ...opts, lang: "hi" });
}

/**
 * One-time Hindi cache purge on app open (bump LOVE_REALITY_HI_DEVICE_CACHE_VER to rerun).
 */
export async function purgeHiDeviceCacheIfNeeded(opts: {
  userId: number;
  p1: BirthData;
  p2: BirthData;
  p1Name: string;
  p2Name: string;
}): Promise<boolean> {
  try {
    const seen = await AsyncStorage.getItem(HI_DEVICE_PURGE_KEY);
    if (seen === LOVE_REALITY_HI_DEVICE_CACHE_VER) return false;
    await clearLoveReportCacheHiOnly(opts);
    await AsyncStorage.setItem(HI_DEVICE_PURGE_KEY, LOVE_REALITY_HI_DEVICE_CACHE_VER);
    return true;
  } catch {
    return false;
  }
}

export function deviceCacheNeedsServerRefresh(
  payload: LoveProReportResponse | null,
  meta: LoveReportCacheMeta | null,
  lang: ProPdfLangCode,
): boolean {
  if (needsLoveReportLlmRefresh(payload, lang, meta?.contentLang)) return true;
  if (
    lang === "hi"
    && payload?.hi_cache_ver
    && payload.hi_cache_ver !== LOVE_REALITY_HI_SERVER_CACHE_VER
  ) {
    return true;
  }
  if (lang === "en" || lang === "hn") {
    if (enHnReportCacheReady(payload, lang)) return false;
    if (meta?.contentLang && coerceProPdfLang(meta.contentLang) !== lang) return true;
    return needsLoveReportLlmRefresh(payload, lang, meta?.contentLang);
  }
  if (meta?.contentLang && coerceProPdfLang(meta.contentLang) !== lang) return true;
  if (lang === "hi" && meta?.contentScript && meta.contentScript !== "hi") return true;
  return false;
}

export async function saveLoveReportCache(
  opts: {
    userId: number;
    p1: BirthData;
    p2: BirthData;
    p1Name: string;
    p2Name: string;
    lang: string;
  },
  data: LoveProReportResponse,
): Promise<void> {
  if (!isCompletePayload(data)) return;
  const { rawKey, metaKey } = loveReportCacheKeys(opts);
  const cur = currentLoveReportRevision();
  const meta: LoveReportCacheMeta = {
    ...cur,
    savedAt: Date.now(),
    polishSource: data.polish_source,
    contentLang: coerceProPdfLang(data.lang || opts.lang),
    contentScript: (data.content_script || "").trim() || undefined,
  };
  sessionRaw.set(rawKey, data);
  sessionMeta.set(metaKey, meta);
  try {
    await AsyncStorage.multiSet([
      [rawKey, JSON.stringify(data)],
      [metaKey, JSON.stringify(meta)],
    ]);
  } catch {
    /* session cache still valid this visit */
  }
}

/** After app-only layout bump — update meta without touching raw JSON or calling API. */
export async function touchLoveReportCacheRevision(opts: {
  userId: number;
  p1: BirthData;
  p2: BirthData;
  p1Name: string;
  p2Name: string;
  lang: string;
  polishSource?: string;
}): Promise<void> {
  const { metaKey } = loveReportCacheKeys(opts);
  const cur = currentLoveReportRevision();
  const meta: LoveReportCacheMeta = {
    ...cur,
    savedAt: Date.now(),
    polishSource: opts.polishSource,
  };
  sessionMeta.set(metaKey, meta);
  try {
    await AsyncStorage.setItem(metaKey, JSON.stringify(meta));
  } catch {
    /* ignore */
  }
}

export async function markLoveReportPdfSynced(opts: {
  userId: number;
  p1: BirthData;
  p2: BirthData;
  p1Name: string;
  p2Name: string;
  lang: string;
}): Promise<void> {
  const { pdfSyncKey } = loveReportCacheKeys(opts);
  const rev = loveReportRevisionString(currentLoveReportRevision());
  try {
    await AsyncStorage.setItem(pdfSyncKey, rev);
  } catch {
    /* ignore */
  }
}

export async function loveReportPdfNeedsResync(opts: {
  userId: number;
  p1: BirthData;
  p2: BirthData;
  p1Name: string;
  p2Name: string;
  lang: string;
}): Promise<boolean> {
  const { metaKey, pdfSyncKey } = loveReportCacheKeys(opts);
  const [meta, pdfSyncedRevision] = await Promise.all([
    readMeta(metaKey),
    AsyncStorage.getItem(pdfSyncKey).catch(() => null),
  ]);
  return loveReportNeedsPdfResync(meta, pdfSyncedRevision);
}

/** @deprecated use resolveLoveReportCache / saveLoveReportCache */
export async function loadCachedLoveReport(key: string): Promise<LoveProReportResponse | null> {
  return readRaw(key);
}

/** @deprecated use saveLoveReportCache */
export async function saveCachedLoveReport(
  key: string,
  data: LoveProReportResponse,
): Promise<void> {
  if (!isCompletePayload(data)) return;
  sessionRaw.set(key, data);
  try {
    await AsyncStorage.setItem(key, JSON.stringify(data));
  } catch {
    /* ignore */
  }
}

export function getSessionLoveReport(key: string): LoveProReportResponse | null {
  return sessionRaw.get(key) ?? null;
}

export function setSessionLoveReport(key: string, data: LoveProReportResponse): void {
  sessionRaw.set(key, data);
}
