import Constants from "expo-constants";
import { Platform } from "react-native";

/**
 * Client-side runtime/tamper signals.
 *
 * These are ADVISORY ONLY. A rooted or patched device can trivially lie here,
 * so the backend records the signals for abuse triage and never uses them to
 * decide authentication, payment or premium entitlement. The security boundary
 * stays server-side (X-API-Key + ownership checks + Razorpay verification).
 */

export type IntegritySignals = {
  rooted: boolean;
  emulator: boolean;
  debug: boolean;
  expoGo: boolean;
  devtools: boolean;
};

const SIGNAL_TTL_MS = 10 * 60 * 1000;

let cached: { value: IntegritySignals; expiresAt: number } | null = null;
let inflight: Promise<IntegritySignals> | null = null;

function isDebugBuild(): boolean {
  return typeof __DEV__ !== "undefined" && __DEV__ === true;
}

function isExpoGo(): boolean {
  try {
    return Constants.appOwnership === "expo";
  } catch {
    return false;
  }
}

/** React DevTools / a JS debugger attached to a release bundle. */
function hasDevtoolsHook(): boolean {
  try {
    return !!(globalThis as { __REACT_DEVTOOLS_GLOBAL_HOOK__?: unknown })
      .__REACT_DEVTOOLS_GLOBAL_HOOK__;
  } catch {
    return false;
  }
}

async function collectSignals(): Promise<IntegritySignals> {
  const debug = isDebugBuild();
  const signals: IntegritySignals = {
    rooted: false,
    emulator: false,
    debug,
    expoGo: isExpoGo(),
    // In a debug build devtools are expected, so it is only a signal in release.
    devtools: !debug && hasDevtoolsHook(),
  };

  if (Platform.OS === "web") return signals;

  try {
    const Device = await import("expo-device");
    if (Device.isDevice === false) signals.emulator = true;
    const probe = (Device as { isRootedExperimentalAsync?: () => Promise<boolean> })
      .isRootedExperimentalAsync;
    if (typeof probe === "function") {
      signals.rooted = (await probe()) === true;
    }
  } catch {
    // expo-device unavailable — leave the defaults, the server treats a
    // missing/partial signal exactly like a clean one (advisory).
  }

  return signals;
}

export async function getIntegritySignals(): Promise<IntegritySignals> {
  if (cached && cached.expiresAt > Date.now()) return cached.value;
  if (inflight) return inflight;
  inflight = collectSignals()
    .then((value) => {
      cached = { value, expiresAt: Date.now() + SIGNAL_TTL_MS };
      return value;
    })
    .finally(() => {
      inflight = null;
    });
  return inflight;
}

/**
 * Compact advisory header, e.g. `rooted,emulator` or `ok` on a clean device.
 * Kept to flag names only — no device identifiers, nothing that could be
 * replayed as a credential.
 */
export async function integrityHeaders(): Promise<Record<string, string>> {
  try {
    const s = await getIntegritySignals();
    const flags = [
      s.rooted ? "rooted" : "",
      s.emulator ? "emulator" : "",
      s.debug ? "debug" : "",
      s.expoGo ? "expo-go" : "",
      s.devtools ? "devtools" : "",
    ].filter(Boolean);
    return { "X-Client-Integrity": flags.length ? flags.join(",") : "ok" };
  } catch {
    return {};
  }
}

export function resetIntegrityCache(): void {
  cached = null;
}
