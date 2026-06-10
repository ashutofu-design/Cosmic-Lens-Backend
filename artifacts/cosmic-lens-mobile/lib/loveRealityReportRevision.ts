/**
 * Report revision — bump APP ver when in-app sections/labels change (no LLM).
 * PDF layout ver must stay in sync with artifacts/api-server/love_reality_api.py.
 */
import { LOVE_REALITY_PDF_LAYOUT_VER } from "@/lib/loveRealityPdfLayout";

/** Bump when page sections, labels, or in-app layout logic changes. */
export const LOVE_REALITY_APP_REPORT_VER = "lr_app_v31_en_hn_cache";

/** Bump to wipe device Hindi report cache once (server hi_purge_v1). */
export const LOVE_REALITY_HI_DEVICE_CACHE_VER = "hi_purge_v10_remedies_action_fix";

/** Must match artifacts/api-server/love_reality_api.py LOVE_REALITY_HI_CACHE_VER */
export const LOVE_REALITY_HI_SERVER_CACHE_VER = "hi_purge_v18_remedies_action_fix";

export type LoveReportChangeKind =
  /** Cached payload matches current app + PDF layout. */
  | "none"
  /** Only in-app presentation changed — reuse raw JSON, rebuild sections locally. */
  | "app_layout"
  /** Server pdf_context / page1 builder changed — refetch JSON, no LLM. */
  | "pdf_layout"
  /** No usable cache. */
  | "missing";

export type LoveReportCacheMeta = {
  pdfLayoutVer: string;
  appReportVer: string;
  savedAt: number;
  polishSource?: string;
  /** Language the saved JSON body was generated for (en / hn / hi). */
  contentLang?: string;
  /** Server content_script after localize (hi | hi_partial | hn | en). */
  contentScript?: string;
};

export function currentLoveReportRevision(): Pick<LoveReportCacheMeta, "pdfLayoutVer" | "appReportVer"> {
  return {
    pdfLayoutVer: LOVE_REALITY_PDF_LAYOUT_VER,
    appReportVer: LOVE_REALITY_APP_REPORT_VER,
  };
}

export function loveReportRevisionString(meta: Pick<LoveReportCacheMeta, "pdfLayoutVer" | "appReportVer">): string {
  return `${meta.pdfLayoutVer}::${meta.appReportVer}`;
}

/** Detect what changed since last save — drives cache + PDF resync without LLM. */
export function detectLoveReportChange(stored: LoveReportCacheMeta | null | undefined): LoveReportChangeKind {
  if (!stored?.pdfLayoutVer || !stored?.appReportVer) return "missing";
  const cur = currentLoveReportRevision();
  if (stored.pdfLayoutVer === cur.pdfLayoutVer && stored.appReportVer === cur.appReportVer) {
    return "none";
  }
  if (stored.pdfLayoutVer !== cur.pdfLayoutVer) return "pdf_layout";
  return "app_layout";
}

export function loveReportNeedsPdfResync(
  stored: LoveReportCacheMeta | null | undefined,
  pdfSyncedRevision?: string | null,
): boolean {
  const change = detectLoveReportChange(stored);
  if (change === "missing") return false;
  const rev = loveReportRevisionString(currentLoveReportRevision());
  if (!pdfSyncedRevision) return change !== "none";
  return pdfSyncedRevision !== rev;
}
