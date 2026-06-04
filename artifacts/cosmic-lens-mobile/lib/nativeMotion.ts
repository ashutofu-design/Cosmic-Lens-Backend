import { Platform } from "react-native";

/** Prefer lighter UI motion on real devices (Metro dev builds are especially sensitive). */
export const isNativeApp = Platform.OS !== "web";

export function enterMotion(durationMs: number, slidePx: number) {
  if (!isNativeApp) return { duration: durationMs, slide: slidePx };
  return { duration: Math.min(180, durationMs), slide: Math.min(6, slidePx) };
}

export function skipEnterMotion(delayMs: number) {
  if (!isNativeApp) return delayMs;
  return Math.min(delayMs, 40);
}
