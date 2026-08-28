import { firebaseConfig, isFirebaseConfigured } from "./firebaseConfig";

export { signInWithGoogle, signOutFromFirebase } from "./googleSignIn";

let _webAuth: any = null;
let _recaptchaVerifier: any = null;
const phoneSessions = new Map<string, any>();

async function getWebAuth() {
  if (_webAuth) return _webAuth;
  if (!isFirebaseConfigured()) {
    throw new Error("Firebase client config missing. Set EXPO_PUBLIC_FIREBASE_* env vars.");
  }
  const { initializeApp, getApps, getApp } = await import("firebase/app");
  const { getAuth } = await import("firebase/auth");
  const app = getApps().length > 0 ? getApp() : initializeApp(firebaseConfig);
  _webAuth = getAuth(app);
  return _webAuth;
}

function recaptchaContainerId(): string {
  return "firebase-phone-auth-recaptcha";
}

async function ensureRecaptchaVerifier() {
  const auth = await getWebAuth();
  if (typeof document === "undefined") {
    throw new Error("Phone OTP is only available in the browser with DOM access.");
  }
  let container = document.getElementById(recaptchaContainerId());
  if (!container) {
    container = document.createElement("div");
    container.id = recaptchaContainerId();
    container.style.position = "fixed";
    container.style.bottom = "0";
    container.style.left = "0";
    container.style.opacity = "0";
    container.style.pointerEvents = "none";
    document.body.appendChild(container);
  }
  if (_recaptchaVerifier) {
    try {
      await _recaptchaVerifier.clear();
    } catch {
      /* ignore */
    }
  }
  const { RecaptchaVerifier } = await import("firebase/auth");
  _recaptchaVerifier = new RecaptchaVerifier(auth, recaptchaContainerId(), {
    size: "invisible",
  });
  return _recaptchaVerifier;
}

function newSessionId(): string {
  return `otp_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 9)}`;
}

export function supportsPhoneOtp(): boolean {
  return typeof window !== "undefined";
}

export async function requestPhoneOtp(
  phoneE164: string,
  opts?: { forceResend?: boolean },
): Promise<{ sessionId: string }> {
  const auth = await getWebAuth();
  const verifier = await ensureRecaptchaVerifier();
  const { signInWithPhoneNumber } = await import("firebase/auth");
  for (const [id, conf] of phoneSessions.entries()) {
    if (conf?.phoneE164 === phoneE164) phoneSessions.delete(id);
  }
  if (opts?.forceResend) {
    const { signOut } = await import("firebase/auth");
    try {
      await signOut(auth);
    } catch {
      /* ignore */
    }
  }
  const confirmation = await signInWithPhoneNumber(auth, phoneE164, verifier);
  const sessionId = newSessionId();
  phoneSessions.set(sessionId, {
    confirm: confirmation.confirm.bind(confirmation),
    phoneE164,
    createdAt: Date.now(),
  });
  return { sessionId };
}

export async function confirmPhoneOtp(
  sessionId: string,
  otp: string,
  _opts?: { likelyAutofill?: boolean },
): Promise<string> {
  const session = phoneSessions.get(sessionId);
  if (!session) throw new Error("OTP session expired. Please request a new OTP.");
  const auth = await getWebAuth();
  const user = auth.currentUser;
  if (user?.phoneNumber?.replace(/\D/g, "").slice(-10) === session.phoneE164.replace(/\D/g, "").slice(-10)) {
    phoneSessions.delete(sessionId);
    return user.getIdToken(true);
  }
  const code = String(otp || "").replace(/\D/g, "");
  const result = await session.confirm(code);
  if (!result?.user) throw new Error("OTP verification failed.");
  const idToken = await result.user.getIdToken(true);
  phoneSessions.delete(sessionId);
  return idToken;
}

export function markOtpSessionAutofillLikely(_sessionId: string): void {
  /* web: no-op */
}

export function watchPhoneAutoSignIn(_phoneE164: string, _onSignedIn: (idToken: string) => void): () => void {
  return () => {};
}

export function resetPendingPhoneVerification(phoneE164?: string): void {
  if (!phoneE164) {
    phoneSessions.clear();
    return;
  }
  for (const [id, conf] of phoneSessions.entries()) {
    if (conf?.phoneE164 === phoneE164) phoneSessions.delete(id);
  }
}

export async function ensureFirebaseAuthReady(): Promise<void> {
  /* web: getWebAuth initializes lazily */
  await getWebAuth();
}

export async function prepareLoginPhoneAuth(): Promise<void> {
  phoneSessions.clear();
}

export async function resetPhoneAuthAfterFailure(): Promise<void> {
  phoneSessions.clear();
  try {
    const auth = await getWebAuth();
    const { signOut } = await import("firebase/auth");
    await signOut(auth);
  } catch {
    /* ignore */
  }
}
