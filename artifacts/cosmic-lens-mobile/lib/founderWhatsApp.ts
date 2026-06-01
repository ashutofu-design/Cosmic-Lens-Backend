import { Alert, Linking, Platform } from "react-native";

/** Founder WhatsApp (India, no + prefix — wa.me format). */
export const FOUNDER_WHATSAPP = "919040524394";

export const FOUNDER_WHATSAPP_MSG =
  "Namaste 🙏 Main Cosmic Lens app se aa raha hu. Mujhe apni kundli / rashifal ke baare mein aapse personally baat karni hai.";

export const BIRTH_TIME_RECTIFICATION_MSG =
  "Namaste 🙏 Main Cosmic Lens app se hoon. Mujhe apna exact birth time (janm samay) nahi pata — kripya birth time rectification kar dein.";

/** Opens WhatsApp chat with founder — direct wa.me deep link (app or browser). */
export function openBirthTimeRectificationWhatsApp(): Promise<void> {
  return openFounderWhatsApp(BIRTH_TIME_RECTIFICATION_MSG);
}

export async function openFounderWhatsApp(
  message: string = FOUNDER_WHATSAPP_MSG,
): Promise<void> {
  const text = encodeURIComponent(message);
  const url = `https://wa.me/${FOUNDER_WHATSAPP}?text=${text}`;

  if (Platform.OS === "web") {
    if (typeof window !== "undefined") {
      window.location.href = url;
    }
    return;
  }

  try {
    await Linking.openURL(url);
  } catch {
    Alert.alert(
      "WhatsApp open nahi ho paya",
      "WhatsApp install karke dobara try karein, ya browser se chat kholen.",
      [{ text: "OK" }],
    );
  }
}
