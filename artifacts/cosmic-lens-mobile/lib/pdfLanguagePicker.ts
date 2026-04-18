import { Alert, Linking, Platform } from "react-native";
import * as WebBrowser from "expo-web-browser";

export type PdfLang = "en" | "hinglish" | "hi";

const appendLang = (url: string, lang: PdfLang): string => {
  const sep = url.includes("?") ? "&" : "?";
  return `${url}${sep}lang=${lang}`;
};

const openPdfUrl = async (urlWithLang: string) => {
  try {
    await WebBrowser.openBrowserAsync(urlWithLang, {
      presentationStyle: WebBrowser.WebBrowserPresentationStyle.FULL_SCREEN,
      showTitle: true,
      enableBarCollapsing: true,
    });
  } catch (e: any) {
    try {
      await Linking.openURL(urlWithLang);
    } catch {
      Alert.alert(
        "Cannot open PDF",
        "Could not open the report.\n\n" + String(e?.message || e),
      );
    }
  }
};

/**
 * Ask the user which language they want the PDF in, then open the report.
 * Falls back to bilingual if the user cancels.
 *
 *   en       → English only
 *   hinglish → Hinglish only (Roman-script Hindi, e.g. "Gas chulha SE…")
 *   hi       → Hindi (currently rendered bilingual until Devanagari font ships)
 */
export const openReportPdfWithLanguageChoice = (baseUrl: string) => {
  Alert.alert(
    "Report ki bhasha chunein",
    "Aap report kis bhasha mein chahte hain?",
    [
      {
        text: "English",
        onPress: () => openPdfUrl(appendLang(baseUrl, "en")),
      },
      {
        text: "Hinglish",
        onPress: () => openPdfUrl(appendLang(baseUrl, "hinglish")),
      },
      {
        text: "हिंदी",
        onPress: () => openPdfUrl(appendLang(baseUrl, "hi")),
      },
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
  Alert.alert(
    "Report ki bhasha chunein",
    "Share karne se pehle bhasha chunein:",
    [
      { text: "English", onPress: () => choose("en") },
      { text: "Hinglish", onPress: () => choose("hinglish") },
      { text: "हिंदी", onPress: () => choose("hi") },
      { text: "Cancel", style: "cancel" },
    ],
    { cancelable: true },
  );
};
