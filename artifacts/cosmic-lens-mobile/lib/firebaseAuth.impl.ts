/**
 * Firebase Phone Authentication — cross-platform wrapper.
 *
 *   Native (iOS/Android, EAS dev/prod build):
 *     Uses @react-native-firebase/auth — gives auto-retrieval of the SMS OTP
 *     on Android, no reCAPTCHA needed, best UX. REQUIRES google-services.json
 *     (Android) and GoogleService-Info.plist (iOS) to be present at build time
 *     and the @react-native-firebase/app config plugin in app.json.
 *
 *   Web (Replit preview, expo web export):
 *     Uses the Firebase JS SDK with an invisible reCAPTCHA verifier.
 *
 * Public API (same on both platforms):
 *     await sendPhoneOtp(e164)         // → opaque verificationId/handle
 *     await confirmPhoneOtp(code)      // → ID token (string)
 *     resetPendingVerification()       // clear in-memory state on user cancel
 *
 * The only state kept here is a module-level `_pendingVerification` so the
 * verify-OTP screen doesn't need to receive a non-serialisable confirmation
 * object via router params.
 */

import { Platform } from "react-native";
import { firebaseConfig, isFirebaseConfigured } from "./firebaseConfig";

// ── Module state ──────────────────────────────────────────────────────────────
type PendingVerification =
  | { kind: "native"; confirmation: any }
  | { kind: "web";    verificationId: string; verifier: any };

let _pendingVerification: PendingVerification | null = null;

// Web-only: cache the recaptcha verifier across renders.
let _webRecaptchaVerifier: any = null;
let _webAuth: any = null;

// ── Helpers ───────────────────────────────────────────────────────────────────
function assertConfigured(): void {
  if (!isFirebaseConfigured()) {
    throw new Error(
      "Firebase client config missing. Set EXPO_PUBLIC_FIREBASE_* env vars."
    );
  }
}

/**
 * Ensure a single Firebase JS SDK app instance + auth handle (web only).
 * On native, @react-native-firebase auto-initialises from google-services.json,
 * so this whole function is a no-op there.
 */
async function getWebAuth() {
  if (_webAuth) return _webAuth;
  assertConfigured();

  const { initializeApp, getApps, getApp } = await import("firebase/app");
  const { getAuth }                         = await import("firebase/auth");

  const app = getApps().length > 0 ? getApp() : initializeApp(firebaseConfig);
  _webAuth = getAuth(app);
  return _webAuth;
}

/**
 * Build (or return cached) reCAPTCHA verifier for web phone-auth.
 * The verifier renders into the DOM element with id `cosmic-recaptcha`. The
 * caller (login screen) is expected to mount such a div via dangerouslySetInnerHTML
 * — see `app/login.tsx`. On native this is unused.
 */
async function getWebRecaptchaVerifier() {
  if (_webRecaptchaVerifier) return _webRecaptchaVerifier;

  const auth = await getWebAuth();
  const { RecaptchaVerifier } = await import("firebase/auth");

  _webRecaptchaVerifier = new RecaptchaVerifier(auth, "cosmic-recaptcha", {
    size:     "invisible",
    callback: () => {
      /* solved — sendOtp will proceed automatically */
    },
  });
  return _webRecaptchaVerifier;
}

// ── Public API ────────────────────────────────────────────────────────────────

/**
 * Trigger an OTP SMS to the given E.164 phone number (e.g. "+916370082770").
 * Stores the resulting confirmation handle in module memory so `confirmPhoneOtp`
 * can complete the flow on the next screen.
 */
export async function sendPhoneOtp(e164: string): Promise<void> {
  if (!e164 || !e164.startsWith("+")) {
    throw new Error("Phone number must be in E.164 format (e.g. +919999999999).");
  }

  if (Platform.OS === "web") {
    const auth     = await getWebAuth();
    const verifier = await getWebRecaptchaVerifier();
    const { signInWithPhoneNumber } = await import("firebase/auth");

    const result = await signInWithPhoneNumber(auth, e164, verifier);
    _pendingVerification = {
      kind:           "web",
      verificationId: result.verificationId,
      verifier,
    };
    return;
  }

  // Native (iOS/Android)
  const authMod = await import("@react-native-firebase/auth");
  const auth    = authMod.default ?? authMod;
  const confirmation = await auth().signInWithPhoneNumber(e164);
  _pendingVerification = { kind: "native", confirmation };
}

/**
 * Confirm the user-typed code and return a Firebase ID token suitable for
 * sending to the backend `/api/auth/firebase-verify` endpoint.
 */
export async function confirmPhoneOtp(code: string): Promise<string> {
  const cleaned = (code || "").replace(/\D/g, "");
  if (cleaned.length < 4) throw new Error("Invalid OTP");

  const pv = _pendingVerification;
  if (!pv) throw new Error("No pending verification — please request OTP again.");

  if (pv.kind === "web") {
    const auth = await getWebAuth();
    const { PhoneAuthProvider, signInWithCredential } = await import("firebase/auth");
    const credential = PhoneAuthProvider.credential(pv.verificationId, cleaned);
    const userCred   = await signInWithCredential(auth, credential);
    _pendingVerification = null;
    return userCred.user.getIdToken(true);
  }

  // Native
  const userCred = await pv.confirmation.confirm(cleaned);
  _pendingVerification = null;
  if (!userCred?.user) throw new Error("Verification failed.");
  return userCred.user.getIdToken(true);
}

/**
 * Reset in-memory verification state (e.g. when user navigates back to change
 * the phone number). On web, also tears down the reCAPTCHA widget so a fresh
 * one can be rendered for the next attempt.
 */
export function resetPendingVerification(): void {
  _pendingVerification = null;
  if (Platform.OS === "web" && _webRecaptchaVerifier) {
    try { _webRecaptchaVerifier.clear?.(); } catch { /* ignore */ }
    _webRecaptchaVerifier = null;
  }
}

export function hasPendingVerification(): boolean {
  return _pendingVerification !== null;
}
