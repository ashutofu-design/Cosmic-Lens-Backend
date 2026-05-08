import { Alert, Linking, Platform } from "react-native";
import * as FileSystem from "expo-file-system/legacy";
import * as Sharing from "expo-sharing";
import * as WebBrowser from "expo-web-browser";
import {
  saveLocalReport,
  type LocalReportKind,
} from "./localReports";

export type PdfLang = "en" | "hinglish" | "hi";

/**
 * Metadata for auto-saving a downloaded PDF to the local "My Reports"
 * registry. Pass to `openReportPdfWithLanguageChoice` (or `openPdfUrl`)
 * and the picker will register the file after a successful native
 * download — no extra caller code needed.
 */
export interface PdfReportMeta {
  kind: LocalReportKind;
  title: string;
  subtitle?: string;
}

const appendLang = (url: string, lang: PdfLang): string => {
  const sep = url.includes("?") ? "&" : "?";
  return `${url}${sep}lang=${lang}`;
};

const safeFileName = (url: string, lang: PdfLang): string => {
  // Try to extract a meaningful filename from the URL path; fall back to a stamp.
  try {
    const u = new URL(url);
    const last = u.pathname.split("/").filter(Boolean).pop() || "report";
    const base = last.replace(/\.pdf$/i, "").replace(/[^a-zA-Z0-9_-]+/g, "_");
    return `${base || "report"}_${lang}_${Date.now()}.pdf`;
  } catch {
    return `report_${lang}_${Date.now()}.pdf`;
  }
};

/**
 * Open a remote PDF report. On native we download it first (with the
 * `bypass-tunnel-reminder` header that skips localtunnel's "Click to continue"
 * page), then hand the local file to the OS share sheet so the user can save
 * it, open it in any PDF viewer, or share it. On web we just open the URL.
 */
const openPdfUrl = async (urlWithLang: string, meta?: PdfReportMeta) => {
  // Web: just open the URL — browser handles PDF natively.
  if (Platform.OS === "web") {
    try {
      if (typeof window !== "undefined") {
        window.open(urlWithLang, "_blank", "noopener");
        return;
      }
    } catch { /* fall through */ }
    try { await Linking.openURL(urlWithLang); } catch {}
    return;
  }

  // Native (iOS / Android via Expo Go or EAS build).
  try {
    // Pick a writable destination — documentDirectory is more permanent on
    // Android, cacheDirectory works everywhere as a fallback.
    const dir = FileSystem.documentDirectory || FileSystem.cacheDirectory;
    if (!dir) throw new Error("No writable directory available");
    const lang = (urlWithLang.match(/[?&]lang=(en|hinglish|hi)/) || [])[1] as PdfLang || "en";
    const fileName = safeFileName(urlWithLang, lang);
    const dest = dir + fileName;

    // Download with the bypass header so localtunnel returns the real PDF
    // instead of its "Click to continue" HTML interstitial.
    const dl = await FileSystem.downloadAsync(urlWithLang, dest, {
      headers: {
        "bypass-tunnel-reminder": "true",
        "User-Agent": "CosmicLensMobile/1.0",
        "Accept": "application/pdf",
      },
    });
    if (dl.status !== 200) {
      throw new Error(`Server returned HTTP ${dl.status}`);
    }

    // Quick sanity check: a tunnel interstitial would be tiny (<2 KB) and
    // text/html. If we got something suspiciously small, surface a clearer error.
    let info: { size?: number } = {};
    try { info = (await FileSystem.getInfoAsync(dl.uri)) as { size?: number }; } catch { /* ignore */ }
    if (typeof info.size === "number" && info.size > 0 && info.size < 2048) {
      throw new Error("Tunnel interstitial received instead of PDF. Please try again.");
    }

    // Auto-save into the local "My Reports" registry (silent, never throws).
    if (meta) {
      try {
        await saveLocalReport({
          kind: meta.kind,
          title: meta.title,
          subtitle: meta.subtitle,
          sourceUri: dl.uri,
          remoteUrl: urlWithLang,
        });
      } catch { /* ignore */ }
    }

    // Hand off to the OS share sheet — user can save to Files, open in any
    // PDF reader, or forward to WhatsApp etc.
    const canShare = await Sharing.isAvailableAsync();
    if (canShare) {
      await Sharing.shareAsync(dl.uri, {
        mimeType: "application/pdf",
        dialogTitle: fileName,
        UTI: "com.adobe.pdf",
      });
      return;
    }

    // Sharing not available — try the in-app browser pointed at the local file.
    await WebBrowser.openBrowserAsync(dl.uri, {
      presentationStyle: WebBrowser.WebBrowserPresentationStyle.FULL_SCREEN,
      showTitle: true,
    });
  } catch (e: any) {
    Alert.alert(
      "Report download fail hua",
      `${String(e?.message || e)}\n\nInternet check karke dobara try kare.`,
    );
  }
};

/**
 * Ask the user which language they want the PDF in, then open the report.
 *
 *   en       → English only
 *   hinglish → Hinglish only (Roman-script Hindi, e.g. "Gas chulha SE…")
 *   hi       → Hindi (currently rendered bilingual until Devanagari font ships)
 */
export const openReportPdfWithLanguageChoice = (
  baseUrl: string,
  meta?: PdfReportMeta,
) => {
  // Web Alert with multiple buttons doesn't reliably fire onPress on Expo web —
  // skip the language picker on web and go straight to bilingual.
  if (Platform.OS === "web") {
    openPdfUrl(appendLang(baseUrl, "hinglish"), meta);
    return;
  }
  Alert.alert(
    "Report ki bhasha chunein",
    "Aap report kis bhasha mein chahte hain?",
    [
      { text: "English",  onPress: () => openPdfUrl(appendLang(baseUrl, "en"),       meta) },
      { text: "Hinglish", onPress: () => openPdfUrl(appendLang(baseUrl, "hinglish"), meta) },
      { text: "हिंदी",     onPress: () => openPdfUrl(appendLang(baseUrl, "hi"),       meta) },
      { text: "Cancel", style: "cancel" },
    ],
    { cancelable: true },
  );
};

/**
 * Same as above but returns the chosen URL via callback (for sharing flows
 * that need the final URL string, e.g. WhatsApp share).
 */
export const pickReportPdfLanguage = (
  baseUrl: string,
  onPicked: (urlWithLang: string, lang: PdfLang) => void,
) => {
  const choose = (lang: PdfLang) => onPicked(appendLang(baseUrl, lang), lang);
  if (Platform.OS === "web") {
    choose("hinglish");
    return;
  }
  Alert.alert(
    "Report ki bhasha chunein",
    "Share karne se pehle bhasha chunein:",
    [
      { text: "English",  onPress: () => choose("en") },
      { text: "Hinglish", onPress: () => choose("hinglish") },
      { text: "हिंदी",     onPress: () => choose("hi") },
      { text: "Cancel", style: "cancel" },
    ],
    { cancelable: true },
  );
};
