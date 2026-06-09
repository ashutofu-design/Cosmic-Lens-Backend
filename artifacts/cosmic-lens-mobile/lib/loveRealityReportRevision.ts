/**
 * Report revision — bump APP ver when in-app sections/labels change (no LLM).
 * PDF layout ver must stay in sync with artifacts/api-server/love_reality_api.py.
 */
import { LOVE_REALITY_PDF_LAYOUT_VER } from "@/lib/loveRealityPdfLayout";

/** Bump when page sections, labels, or in-app layout logic changes. */
export const LOVE_REALITY_APP_REPORT_VER = "lr_app_v7_hn_summary_translate";

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
