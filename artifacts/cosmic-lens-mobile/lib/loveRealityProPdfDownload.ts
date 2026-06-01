/**
 * Love Reality Pro PDF — download, save to My Reports, web + native.
 */
import * as FileSystem from "expo-file-system/legacy";
import * as Sharing from "expo-sharing";
import { Platform } from "react-native";

import { API_BASE } from "@/lib/apiConfig";
import { pdfAuthHeaders } from "@/lib/coupleReportCheckoutFlow";
import { saveLocalReport } from "@/lib/localReports";
import { coerceProPdfLang } from "@/lib/proPdfLang";
import type { BirthData } from "@/types";

export function packLovePerson(bd: BirthData, name?: string) {
  return {
    name: name || bd.name,
    day: bd.day,
    month: bd.month,
    year: bd.year,
    hour: bd.hour,
    minute: bd.minute,
    ampm: bd.ampm,
    lat: bd.lat,
    lon: bd.lon,
    tz: bd.tz,
    place: bd.place,
    gender: bd.gender,
  };
}

export async function downloadLoveRealityProPdf(opts: {
  user: { id: number; api_key?: string | null };
  p1: BirthData;
  p2: BirthData;
  p1Name: string;
  p2Name: string;
  lang: string;
}): Promise<{ shareUri: string; fileName: string; savedToRegistry: boolean }> {
  const bd1 = opts.p1;
  const bd2 = opts.p2;
  if (bd1.lat == null || bd1.lon == null || bd2.lat == null || bd2.lon == null) {
    throw new Error("Birth place coordinates missing. Update both profiles.");
  }
  const tz1 = bd1.tz ?? Math.round((bd1.lon / 15) * 2) / 2;
  const tz2 = bd2.tz ?? Math.round((bd2.lon / 15) * 2) / 2;

  const safe = (s: string) => (s || "x").replace(/[^a-zA-Z0-9_-]+/g, "_").slice(0, 32) || "x";
  const fileName = `Love_Reality_Pro_${safe(opts.p1Name)}_${safe(opts.p2Name)}.pdf`;
  const dest = `${FileSystem.cacheDirectory || ""}${fileName}`;
  const lang = coerceProPdfLang(opts.lang);

  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), 240000);
  try {
    const resp = await fetch(`${API_BASE}/api/love-reality/pro-pdf`, {
      method: "POST",
      headers: {
        ...pdfAuthHeaders(opts.user),
        Accept: "application/pdf",
      },
      body: JSON.stringify({
        p1: { ...packLovePerson(bd1, opts.p1Name), tz: tz1 },
        p2: { ...packLovePerson(bd2, opts.p2Name), tz: tz2 },
        lang,
      }),
      signal: ctrl.signal,
    });
    if (!resp.ok) {
      const err = await resp.json().catch(() => ({}));
      throw new Error((err as { error?: string; message?: string }).message
        || (err as { error?: string }).error
        || `PDF failed (${resp.status})`);
    }

    const buf = await resp.arrayBuffer();

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
            title: `${opts.p1Name} & ${opts.p2Name} — Love Reality PRO`,
            subtitle: `Love Compatibility PDF · ${new Date().toLocaleDateString()}`,
            sourceUri: dataUrl,
          });
          savedToRegistry = true;
        } catch { /* ignore */ }
      }
      return { shareUri: dataUrl || dest, fileName, savedToRegistry };
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
        title: `${opts.p1Name} & ${opts.p2Name} — Love Reality PRO`,
        subtitle: `Love Compatibility PDF · ${new Date().toLocaleDateString()}`,
        sourceUri: dest,
      });
      if (saved?.localUri) {
        shareUri = saved.localUri;
        savedToRegistry = true;
      }
    } catch { /* ignore */ }

    return { shareUri, fileName, savedToRegistry };
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
