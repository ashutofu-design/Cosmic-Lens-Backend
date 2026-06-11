/**
 * Love Reality Pro PDF — download, save to My Reports, web + native.
 */
import AsyncStorage from "@react-native-async-storage/async-storage";
import * as FileSystem from "expo-file-system/legacy";
import * as Sharing from "expo-sharing";
import { Platform } from "react-native";

import { API_BASE } from "@/lib/apiConfig";
import { pdfAuthHeaders } from "@/lib/coupleReportCheckoutFlow";
import { saveLocalReport } from "@/lib/localReports";
import {
  LOVE_REALITY_PDF_LAYOUT_STORAGE_KEY,
  LOVE_REALITY_PDF_LAYOUT_VER,
} from "@/lib/loveRealityPdfLayout";
import { coerceProPdfLang, proPdfLangDisplayName } from "@/lib/proPdfLang";
import type {
  LovePage1Dashboard,
  LovePdfContext,
  LoveProPremium,
  LoveProReportResponse,
  LoveReportSection,
} from "@/lib/loveRealityProReport";
import type { BirthData } from "@/types";

export { packLovePerson } from "@/lib/loveRealityPack";
import { packLovePerson } from "@/lib/loveRealityPack";

/** Client-side WYSIWYG gate — same rules as server validate_wysiwyg_screen_to_pdf. */
export function validateAppSectionsForPdfExport(
  sections: LoveReportSection[],
): string | null {
  if (!sections?.length) {
    return "Error converting to PDF — no content on screen. Reload the report.";
  }
  let pageCount = 0;
  let lineCount = 0;
  const emptyIds: string[] = [];
  for (const sec of sections) {
    const title = String(sec.title || sec.id || "").trim();
    if (!title) continue;
    const bodyLines = String(sec.body || "")
      .split("\n")
      .map(l => l.trim())
      .filter(Boolean);
    const bulletLines = (sec.bullets || []).map(b => String(b).trim()).filter(Boolean);
    const tableLines = (sec.tableRows || [])
      .flat()
      .map(c => String(c).trim())
      .filter(Boolean);
    const lines = [...bodyLines, ...bulletLines, ...tableLines];
    if (!lines.length) {
      if (sec.id) emptyIds.push(sec.id);
      continue;
    }
    pageCount += 1;
    lineCount += lines.length;
  }
  if (emptyIds.length) {
    return `Error converting to PDF — empty section(s): ${emptyIds.join(", ")}.`;
  }
  if (pageCount === 0) {
    return "Error converting to PDF — nothing on screen can be copied.";
  }
  if (lineCount < 5) {
    return `Error converting to PDF — too little text (${lineCount} lines).`;
  }
  return null;
}

export type LoveRealityProPdfDownloadResult = {
  shareUri: string;
  fileName: string;
  savedToRegistry: boolean;
  /** Server returned a cached PDF — no new LLM / engine run. */
  reportCacheHit: boolean;
};

async function needsLayoutRefresh(): Promise<boolean> {
  try {
    const seen = await AsyncStorage.getItem(LOVE_REALITY_PDF_LAYOUT_STORAGE_KEY);
    return seen !== LOVE_REALITY_PDF_LAYOUT_VER;
  } catch {
    return true;
  }
}

async function markLayoutRefreshed(): Promise<void> {
  try {
    await AsyncStorage.setItem(LOVE_REALITY_PDF_LAYOUT_STORAGE_KEY, LOVE_REALITY_PDF_LAYOUT_VER);
  } catch {
    /* ignore */
  }
}

async function fetchLoveRealityPdf(
  opts: {
    user: { id: number; api_key?: string | null };
    p1: Record<string, unknown>;
    p2: Record<string, unknown>;
    lang: string;
    forceRegenerate: boolean;
    /** Fresh OpenAI polish — only when user explicitly regens, not layout-only refresh. */
    forceLlm: boolean;
    /** Exact scroll-view payload — PDF uses this verbatim (no server rebuild). */
    inAppReport?: {
      pro_premium: LoveProPremium;
      pdf_context?: LovePdfContext;
      page1?: LovePage1Dashboard;
    };
    /** Exact scroll-view sections — PDF mirrors these 1:1 (WYSIWYG). */
    appSections?: LoveReportSection[];
    scores?: LoveProReportResponse["scores"];
  },
  signal: AbortSignal,
): Promise<Response> {
  const useClientLayout = Boolean(
    opts.inAppReport?.pdf_context && opts.inAppReport?.page1,
  );
  const useAppMirror = Boolean(opts.appSections && opts.appSections.length > 0);
  return fetch(`${API_BASE}/api/love-reality/pro-pdf`, {
    method: "POST",
    headers: {
      ...pdfAuthHeaders(opts.user),
      Accept: "application/pdf",
      "X-Expected-PDF-Layout": LOVE_REALITY_PDF_LAYOUT_VER,
      ...(opts.forceRegenerate ? { "X-Force-Regenerate": "1" } : {}),
      ...(opts.forceRegenerate ? { "X-PDF-Layout-Refresh": "1" } : {}),
      ...(opts.forceLlm ? { "X-Force-LLM": "1" } : {}),
      ...(useClientLayout ? { "X-In-App-Report-Snapshot": "1" } : {}),
      ...(useClientLayout ? { "X-Connect-Page-To-Pdf": "1" } : {}),
      ...(useAppMirror ? { "X-App-Mirror-Pdf": "1" } : {}),
    },
    body: JSON.stringify({
      p1: opts.p1,
      p2: opts.p2,
      lang: opts.lang,
      pdf_layout: LOVE_REALITY_PDF_LAYOUT_VER,
      ...(opts.forceRegenerate ? { force_regenerate: true } : {}),
      ...(opts.forceLlm ? { force_llm: true } : {}),
      ...(opts.inAppReport?.pro_premium
        ? { pro_premium: opts.inAppReport.pro_premium }
        : {}),
      ...(opts.inAppReport?.pdf_context
        ? { pdf_context: opts.inAppReport.pdf_context }
        : {}),
      ...(opts.inAppReport?.page1 ? { page1: opts.inAppReport.page1 } : {}),
      ...(useAppMirror ? { app_sections: opts.appSections } : {}),
      ...(opts.scores ? { scores: opts.scores } : {}),
    }),
    signal,
  });
}

export async function connectLoveRealityPageToPdf(opts: {
  user: { id: number; api_key?: string | null };
  p1: BirthData;
  p2: BirthData;
  p1Name: string;
  p2Name: string;
  lang: string;
  reportSnapshot: Pick<
    LoveProReportResponse,
    "pro_premium" | "pdf_context" | "page1"
  >;
  /** Sections currently shown on screen — PDF will mirror these exactly. */
  appSections: LoveReportSection[];
  scores: LoveProReportResponse["scores"];
}): Promise<LoveRealityProPdfDownloadResult> {
  if (
    !opts.reportSnapshot.pro_premium
    || !opts.reportSnapshot.pdf_context
    || !opts.reportSnapshot.page1
  ) {
    throw new Error("Report on screen is incomplete — reload the page and try again.");
  }
  if (!opts.appSections?.length) {
    throw new Error("No report sections on screen — reload the page and try again.");
  }
  const convertErr = validateAppSectionsForPdfExport(opts.appSections);
  if (convertErr) {
    throw new Error(convertErr);
  }
  return downloadLoveRealityProPdf({
    user: opts.user,
    p1: opts.p1,
    p2: opts.p2,
    p1Name: opts.p1Name,
    p2Name: opts.p2Name,
    lang: opts.lang,
    syncWithInAppReport: true,
    forceRegenerate: true,
    forceLlm: false,
    reportSnapshot: opts.reportSnapshot,
    appSections: opts.appSections,
    scores: opts.scores,
  });
}

export async function downloadLoveRealityProPdf(opts: {
  user: { id: number; api_key?: string | null };
  p1: BirthData;
  p2: BirthData;
  p1Name: string;
  p2Name: string;
  lang: string;
  /** Default false — reuse server-saved PDF when same couple + lang already generated. */
  forceRegenerate?: boolean;
  /** Default false — reuse server polish snapshot; true only for explicit full regen. */
  forceLlm?: boolean;
  /**
   * Save PDF from in-app report screen — send the exact JSON shown on screen
   * (page1 + pdf_context + pro_premium) so PDF matches scroll view byte-for-byte.
   */
  syncWithInAppReport?: boolean;
  /** Required with syncWithInAppReport — full pro-report response on screen. */
  reportSnapshot?: Pick<
    LoveProReportResponse,
    "pro_premium" | "pdf_context" | "page1"
  >;
  /** Mirror exact scroll sections in PDF (WYSIWYG). */
  appSections?: LoveReportSection[];
  scores?: LoveProReportResponse["scores"];
  /** @deprecated use reportSnapshot */
  proPremium?: LoveProPremium;
}): Promise<LoveRealityProPdfDownloadResult> {
  const bd1 = opts.p1;
  const bd2 = opts.p2;
  if (bd1.lat == null || bd1.lon == null || bd2.lat == null || bd2.lon == null) {
    throw new Error("Birth place coordinates missing. Update both profiles.");
  }
  const tz1 = bd1.tz ?? Math.round((bd1.lon / 15) * 2) / 2;
  const tz2 = bd2.tz ?? Math.round((bd2.lon / 15) * 2) / 2;

  const lang = coerceProPdfLang(opts.lang);
  const syncPage = Boolean(opts.syncWithInAppReport);
  const safe = (s: string) => (s || "x").replace(/[^a-zA-Z0-9_-]+/g, "_").slice(0, 32) || "x";
  const fileName = syncPage
    ? `Love_Reality_Pro_${safe(opts.p1Name)}_${safe(opts.p2Name)}_${lang}_${Date.now()}.pdf`
    : `Love_Reality_Pro_${safe(opts.p1Name)}_${safe(opts.p2Name)}_${lang}.pdf`;
  const dest = `${FileSystem.cacheDirectory || ""}${fileName}`;
  const inAppReport = syncPage
    ? (opts.reportSnapshot ?? (opts.proPremium
      ? { pro_premium: opts.proPremium }
      : undefined))
    : undefined;
  const layoutRefresh = syncPage ? false : await needsLayoutRefresh();
  const forceRegenerate = Boolean(opts.forceRegenerate || syncPage || layoutRefresh);
  const forceLlm = Boolean(opts.forceLlm || (!syncPage && layoutRefresh));

  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), 240000);
  try {
    let resp = await fetchLoveRealityPdf(
      {
        user: opts.user,
        p1: { ...packLovePerson(bd1, opts.p1Name), tz: tz1 },
        p2: { ...packLovePerson(bd2, opts.p2Name), tz: tz2 },
        lang,
        forceRegenerate,
        forceLlm,
        inAppReport,
        appSections: syncPage ? opts.appSections : undefined,
        scores: syncPage ? opts.scores : undefined,
      },
      ctrl.signal,
    );

    if (!resp.ok && resp.status === 412 && syncPage && !opts.forceLlm) {
      resp = await fetchLoveRealityPdf(
        {
          user: opts.user,
          p1: { ...packLovePerson(bd1, opts.p1Name), tz: tz1 },
          p2: { ...packLovePerson(bd2, opts.p2Name), tz: tz2 },
          lang,
          forceRegenerate: true,
          forceLlm: false,
          inAppReport,
          appSections: opts.appSections,
          scores: opts.scores,
        },
        ctrl.signal,
      );
    }

    let reportCacheHit =
      (resp.headers.get("X-Report-Cache") || "").trim().toLowerCase() === "hit";
    const pdfSource = (resp.headers.get("X-PDF-Source") || "").trim() || undefined;
    const layoutHeader = (resp.headers.get("X-PDF-Layout-Version") || "").trim();

    if (
      resp.ok
      && reportCacheHit
      && layoutHeader
      && layoutHeader !== LOVE_REALITY_PDF_LAYOUT_VER
      && !opts.forceRegenerate
      && !syncPage
    ) {
      resp = await fetchLoveRealityPdf(
        {
          user: opts.user,
          p1: { ...packLovePerson(bd1, opts.p1Name), tz: tz1 },
          p2: { ...packLovePerson(bd2, opts.p2Name), tz: tz2 },
          lang,
          forceRegenerate: true,
          forceLlm: true,
        },
        ctrl.signal,
      );
      reportCacheHit =
        (resp.headers.get("X-Report-Cache") || "").trim().toLowerCase() === "hit";
    }

    if (!resp.ok) {
      const err = await resp.json().catch(() => ({}));
      const detail = (err as { detail?: string }).detail;
      throw new Error(
        detail
        || (err as { message?: string }).message
        || (err as { error?: string }).error
        || `PDF failed (${resp.status})`,
      );
    }

    if (resp.ok && !reportCacheHit) {
      await markLayoutRefreshed();
    }

    const buf = await resp.arrayBuffer();
    const langLabel = proPdfLangDisplayName(lang);
    const reportTitle = `${opts.p1Name} & ${opts.p2Name} — Love Reality PRO (${langLabel})`;
    const reportSubtitle = `${langLabel} · ${new Date().toLocaleString()}`;
    if (Platform.OS === "web") {
      let dataUrl = "";
      try {
        const bytes = new Uint8Array(buf);
        const CHUNK = 0x4000;
        const parts: string[] = [];
        for (let i = 0; i < bytes.length; i += CHUNK) {
          const slice = bytes.subarray(i, Math.min(i + CHUNK, bytes.length));
          let s = "";
          for (let j = 0; j < slice.length; j++) s += String.fromCharCode(slice[j]);
          parts.push(s);
        }
        if (typeof globalThis.btoa === "function") {
          dataUrl = `data:application/pdf;base64,${globalThis.btoa(parts.join(""))}`;
        }
      } catch { /* ignore */ }

      try {
        const blob = new Blob([buf], { type: "application/pdf" });
        const url = (globalThis as { URL?: { createObjectURL?: (b: Blob) => string } }).URL?.createObjectURL?.(blob);
        if (url && typeof document !== "undefined") {
          const a = document.createElement("a");
          a.href = url;
          a.download = fileName;
          document.body.appendChild(a);
          a.click();
          a.remove();
          setTimeout(() => {
            try {
              (globalThis as { URL?: { revokeObjectURL?: (u: string) => void } }).URL?.revokeObjectURL?.(url);
            } catch { /* ignore */ }
          }, 2000);
        }
      } catch { /* ignore */ }

      let savedToRegistry = false;
      if (dataUrl) {
        try {
          await saveLocalReport({
            kind: "other",
            title: reportTitle,
            subtitle: reportSubtitle,
            sourceUri: dataUrl,
            restored: reportCacheHit,
            bytes: buf.byteLength,
          });
          savedToRegistry = true;
        } catch { /* ignore */ }
      }
      return { shareUri: dataUrl || dest, fileName, savedToRegistry, reportCacheHit, pdfSource };
    }

    const bytes = new Uint8Array(buf);
    const CHUNK = 0x4000;
    const parts: string[] = [];
    for (let i = 0; i < bytes.length; i += CHUNK) {
      const slice = bytes.subarray(i, Math.min(i + CHUNK, bytes.length));
      let s = "";
      for (let j = 0; j < slice.length; j++) s += String.fromCharCode(slice[j]);
      parts.push(s);
    }
    if (typeof globalThis.btoa !== "function") throw new Error("encoding_failed");
    await FileSystem.writeAsStringAsync(dest, globalThis.btoa(parts.join("")), {
      encoding: FileSystem.EncodingType.Base64,
    });

    let shareUri = dest;
    let savedToRegistry = false;
    try {
      const saved = await saveLocalReport({
        kind: "other",
        title: reportTitle,
        subtitle: reportSubtitle,
        sourceUri: dest,
        restored: reportCacheHit,
        bytes: buf.byteLength,
      });
      if (saved?.localUri) {
        shareUri = saved.localUri;
        savedToRegistry = true;
      }
    } catch { /* ignore */ }

    return { shareUri, fileName, savedToRegistry, reportCacheHit, pdfSource };
  } finally {
    clearTimeout(timer);
  }
}

export async function shareLoveRealityPdf(shareUri: string, fileName: string) {
  const can = await Sharing.isAvailableAsync();
  if (!can) return;
  await Sharing.shareAsync(shareUri, {
    mimeType: "application/pdf",
    dialogTitle: fileName,
    UTI: "com.adobe.pdf",
  });
}
