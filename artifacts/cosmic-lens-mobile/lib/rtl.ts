// ══════════════════════════════════════════════════════════════════════════════
// COSMIC LENS — Right-to-Left (RTL) Layout Support
// Languages requiring RTL: Arabic. (Future: ur, fa, he if added.)
//
// React Native's I18nManager.forceRTL() takes effect ONLY after a full app
// reload. We use expo-updates' Updates.reloadAsync() to perform that reload
// gracefully when the user switches to/from an RTL language.
// ══════════════════════════════════════════════════════════════════════════════

import { I18nManager, Alert, Platform, DevSettings } from "react-native";
import type { UILang } from "@/lib/i18n";

// ── RTL language registry ─────────────────────────────────────────────────────
const RTL_LANG_SET: ReadonlySet<string> = new Set(["ar"]);

export function isRTLLang(lang: string | null | undefined): boolean {
  return !!lang && RTL_LANG_SET.has(lang);
}

/** Whether the runtime is currently rendering in RTL. */
export function getCurrentRTL(): boolean {
  return I18nManager.isRTL;
}

/** Reload the app via expo-updates (graceful) → DevSettings (dev) → no-op. */
async function reloadApp(): Promise<boolean> {
  try {
    const Updates = await import("expo-updates");
    if (Updates && typeof Updates.reloadAsync === "function") {
      await Updates.reloadAsync();
      return true;
    }
  } catch {
    // expo-updates not available or failed — fall through
  }
  try {
    if (__DEV__ && DevSettings && typeof DevSettings.reload === "function") {
      DevSettings.reload();
      return true;
    }
  } catch {
    // ignore
  }
  return false;
}

// ── In-flight guard ──────────────────────────────────────────────────────────
// Prevents simultaneous/duplicate reload attempts when both the boot
// enforcement path and the user-initiated path race for the same language.
let _rtlApplyInFlight = false;

/**
 * Apply RTL setting for a target language.
 *
 * Returns:
 *   "no_change" — direction matches, nothing to do
 *   "reloaded"  — direction changed and the app was reloaded automatically
 *   "needs_manual_restart" — direction changed but reload failed; user must
 *                            close & reopen the app to see the new layout
 *
 * `silent: true` skips the user-facing alert (used during boot when we just
 * want to enforce direction without prompting).
 */
export async function applyRTLForLang(
  lang: UILang | string,
  opts: { silent?: boolean; alertTitle?: string; alertMessage?: string } = {},
): Promise<"no_change" | "reloaded" | "needs_manual_restart"> {
  const wantRTL = isRTLLang(lang);
  const currentRTL = I18nManager.isRTL;

  if (wantRTL === currentRTL) return "no_change";
  if (_rtlApplyInFlight) return "no_change";
  _rtlApplyInFlight = true;

  // Allow + force the new direction.
  try {
    I18nManager.allowRTL(wantRTL);
    I18nManager.forceRTL(wantRTL);
  } catch (err) {
    console.warn("[rtl] forceRTL failed:", err);
  }

  // Reload to apply layout flip.
  if (opts.silent) {
    const ok = await reloadApp();
    if (!ok) _rtlApplyInFlight = false; // allow retry if reload didn't happen
    return ok ? "reloaded" : "needs_manual_restart";
  }

  return new Promise((resolve) => {
    const title = opts.alertTitle ?? (wantRTL ? "Switching to RTL layout" : "Switching to LTR layout");
    const message =
      opts.alertMessage ??
      (wantRTL
        ? "Arabic uses a right-to-left layout. The app will restart now to apply the change."
        : "The app will restart now to apply the layout change.");
    Alert.alert(title, message, [
      {
        text: "Restart now",
        style: "default",
        onPress: async () => {
          const ok = await reloadApp();
          if (!ok) _rtlApplyInFlight = false;
          resolve(ok ? "reloaded" : "needs_manual_restart");
          if (!ok) {
            Alert.alert(
              "Manual restart needed",
              Platform.OS === "ios"
                ? "Please close the app from the app switcher and reopen it to apply the layout change."
                : "Please close and reopen the app to apply the layout change.",
            );
          }
        },
      },
    ], { cancelable: false });
  });
}
