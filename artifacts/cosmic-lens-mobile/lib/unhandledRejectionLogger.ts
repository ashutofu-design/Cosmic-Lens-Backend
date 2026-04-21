// Global unhandled-promise-rejection logger.
//
// React Native's LogBox truncates the message at ~40 chars in the bottom
// banner. This module installs handlers that print the *full* error +
// stack to the Metro console so we can diagnose "Calling the…" style
// errors that the LogBox cuts off.
//
// Imported once from app/_layout.tsx for its side effects only.

import { Platform } from "react-native";

function logFull(label: string, reason: any) {
  try {
    const err = reason instanceof Error ? reason : new Error(String(reason));
    // eslint-disable-next-line no-console
    console.error(
      `[CosmicLens][${label}]`,
      "\n  message:", err.message,
      "\n  name:   ", err.name,
      "\n  stack:  ", err.stack,
      "\n  raw:    ", reason,
    );
  } catch {
    // eslint-disable-next-line no-console
    console.error(`[CosmicLens][${label}] (failed to stringify)`, reason);
  }
}

if (typeof window !== "undefined" && typeof (window as any).addEventListener === "function") {
  (window as any).addEventListener("unhandledrejection", (ev: any) => {
    logFull("unhandledrejection", ev?.reason ?? ev);
  });
  (window as any).addEventListener("error", (ev: any) => {
    logFull("window.error", ev?.error ?? ev?.message ?? ev);
  });
}

// React Native: hook into the global promise rejection tracker.
if (Platform.OS !== "web") {
  try {
    // @ts-ignore – internal API, available in RN 0.66+
    const tracking = require("promise/setimmediate/rejection-tracking");
    tracking.enable({
      allRejections: true,
      onUnhandled: (id: number, reason: any) => {
        logFull(`promise-unhandled id=${id}`, reason);
      },
      onHandled: () => {},
    });
  } catch {
    // Fallback: nothing else we can do — RN should still surface it via LogBox.
  }
}
