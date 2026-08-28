import type { FirebaseAuthTypes } from "@react-native-firebase/auth";
import { Platform } from "react-native";

import { otpTrace, redactId, redactPhone } from "./phoneOtpTrace";

export { signInWithGoogle, signOutFromFirebase } from "./googleSignIn";

type AuthInstance = FirebaseAuthTypes.Module;

type NativePhoneSession = {
  verificationId: string;
  phoneE164: string;
  createdAt: number;
  requestNum: number;
  /** SMS auto-read by Android/Firebase — may already be consumed by Play Services. */
  autoSmsCode?: string;
  /** Resolves when Android auto-verifies (Play Services signs in before manual Verify tap). */
  autoSignInPromise?: Promise<string>;
  confirmPromise?: Promise<string>;
};

const phoneSessions = new Map<string, NativePhoneSession>();

let otpRequestCounter = 0;
let sendInFlight: Promise<{ sessionId: string }> | null = null;
let sendInFlightPhone: string | null = null;
let loginPreparePromise: Promise<void> | null = null;
let loginPrepared = false;

let authReadyOnce: Promise<AuthInstance> | null = null;

async function getAuthInstance(): Promise<AuthInstance> {
  const firebaseAppMod = await import("@react-native-firebase/app");
  const firebase = firebaseAppMod.default ?? firebaseAppMod;
  if (!firebase.apps.length) {
    throw new Error(
      "Firebase native app not initialized. Rebuild the APK with google-services.json included.",
    );
  }
  firebase.app();
  const authMod = await import("@react-native-firebase/auth");
  const authFactory = authMod.default ?? authMod;
  return authFactory();
}

export async function ensureFirebaseAuthReady(): Promise<void> {
  if (!authReadyOnce) {
    authReadyOnce = (async () => {
      const a = await getAuthInstance();
      await new Promise<void>((resolve) => {
        let settled = false;
        const finish = () => {
          if (settled) return;
          settled = true;
          unsub();
          resolve();
        };
        const unsub = a.onAuthStateChanged(() => finish());
        setTimeout(finish, 3000);
      });
      otpTrace("AUTH_READY");
      return a;
    })();
  }
  await authReadyOnce;
}

function newSessionId(): string {
  return `otp_${Date.now().toString(36)}_${Math.random().toString(36).slice(-9)}`;
}

function phoneLast10(phoneE164: string): string {
  return String(phoneE164 || "").replace(/\D/g, "").slice(-10);
}

function phoneFromUser(user: FirebaseAuthTypes.User): string | null {
  if (user.phoneNumber) return user.phoneNumber;
  const phoneProvider = user.providerData.find((p) => p.providerId === "phone");
  return phoneProvider?.phoneNumber ?? null;
}

function userMatchesPhone(user: FirebaseAuthTypes.User | null, phoneE164: string): boolean {
  const phone = user ? phoneFromUser(user) : null;
  if (!phone) return false;
  return phoneLast10(phone) === phoneLast10(phoneE164);
}

function isFirebaseSessionExpiredError(err: unknown): boolean {
  const code = String((err as { code?: string })?.code || "").toLowerCase();
  const msg = String((err as Error)?.message || err || "").toLowerCase();
  return (
    code.includes("session-expired") ||
    code.includes("code-expired") ||
    msg.includes("session-expired") ||
    msg.includes("sms code has expired")
  );
}

function disposeSession(sessionId: string): void {
  phoneSessions.delete(sessionId);
}

function purgeSessionsForPhone(phoneE164: string): void {
  for (const [id, session] of phoneSessions.entries()) {
    if (session.phoneE164 === phoneE164) disposeSession(id);
  }
}

async function waitForAuthSignedOut(authInstance: AuthInstance, timeoutMs = 2500): Promise<void> {
  if (!authInstance.currentUser) return;
  await new Promise<void>((resolve) => {
    let settled = false;
    const finish = () => {
      if (settled) return;
      settled = true;
      unsub();
      resolve();
    };
    const unsub = authInstance.onAuthStateChanged((user) => {
      if (!user) finish();
    });
    if (!authInstance.currentUser) finish();
    setTimeout(finish, timeoutMs);
  });
}

/**
 * Android Play Services may auto-retrieve SMS and sign in before Verify tap.
 * verifyPhoneNumber emits state events — on "verified" we complete auth and
 * watch onAuthStateChanged so manual Verify does not hit session-expired.
 */
function attachAndroidPhoneVerification(
  authInstance: AuthInstance,
  sessionId: string,
  phoneE164: string,
  forceResend: boolean,
): Promise<void> {
  return new Promise((resolve, reject) => {
    let sendSettled = false;
    const finishSend = () => {
      if (sendSettled) return;
      const session = phoneSessions.get(sessionId);
      if (!session?.verificationId) return;
      sendSettled = true;
      resolve();
    };

    const listener = authInstance.verifyPhoneNumber(phoneE164, 60, forceResend);
    listener.on(
      "state_changed",
      (snapshot: FirebaseAuthTypes.PhoneAuthSnapshot) => {
        const session = phoneSessions.get(sessionId);
        if (!session) return;

        otpTrace("VERIFY_PHONE_STATE", {
          state: snapshot.state,
          phone: redactPhone(phoneE164),
          hasAutoCode: !!snapshot.code,
        });

        if (snapshot.verificationId) {
          session.verificationId = snapshot.verificationId;
        }

        if (snapshot.state === "verified") {
          const autoCode = String(snapshot.code || "").replace(/\D/g, "");
          if (autoCode.length >= 6) {
            session.autoSmsCode = autoCode;
            otpTrace("AUTO_SMS_CACHED", { sessionId: redactId(sessionId) });
          }
          void getAuthInstance()
            .then((authInstance) => {
              scheduleAndroidAutoSignIn(
                authInstance,
                sessionId,
                phoneE164,
                session.verificationId || snapshot.verificationId || "",
                autoCode,
              );
            })
            .catch(() => {});
        }

        if (snapshot.state === "sent" || snapshot.state === "timeout") {
          finishSend();
        }
      },
      (error) => {
        if (sendSettled) return;
        sendSettled = true;
        disposeSession(sessionId);
        reject(error);
      },
      (snapshot) => {
        if (snapshot.state === "timeout") finishSend();
      },
    );
  });
}

async function signInWithOtpCode(
  authInstance: AuthInstance,
  verificationId: string,
  code: string,
): Promise<string> {
  const authMod = await import("@react-native-firebase/auth");
  const authFactory = authMod.default ?? authMod;
  const credential = authFactory.PhoneAuthProvider.credential(verificationId, code);
  const userCred = await authInstance.signInWithCredential(credential);
  if (!userCred?.user) throw new Error("OTP verification failed.");
  return userCred.user.getIdToken(true);
}

async function idTokenForMatchingPhoneUser(
  authInstance: AuthInstance,
  phoneE164: string,
): Promise<string | null> {
  const user = authInstance.currentUser;
  if (!user || !userMatchesPhone(user, phoneE164)) return null;
  return user.getIdToken(true);
}

/** Android Play Services often auto-verifies SMS before the user taps Verify. */
function scheduleAndroidAutoSignIn(
  authInstance: AuthInstance,
  sessionId: string,
  phoneE164: string,
  verificationId: string,
  code: string,
): void {
  const session = phoneSessions.get(sessionId);
  if (!session || session.autoSignInPromise) return;

  session.autoSignInPromise = (async () => {
    const existing = await idTokenForMatchingPhoneUser(authInstance, phoneE164);
    if (existing) {
      otpTrace("AUTO_VERIFY_ALREADY_SIGNED_IN", {
        sessionId: redactId(sessionId),
        phone: redactPhone(phoneE164),
      });
      return existing;
    }

    if (verificationId && code.length >= 6) {
      try {
        const token = await signInWithOtpCode(authInstance, verificationId, code);
        otpTrace("AUTO_VERIFY_SIGN_IN_OK", {
          sessionId: redactId(sessionId),
          phone: redactPhone(phoneE164),
        });
        return token;
      } catch (err: unknown) {
        const recovered = await idTokenForMatchingPhoneUser(authInstance, phoneE164);
        if (recovered) {
          otpTrace("AUTO_VERIFY_RECOVERED_AFTER_ERROR", {
            sessionId: redactId(sessionId),
            phone: redactPhone(phoneE164),
          });
          return recovered;
        }
        throw err;
      }
    }

    for (let i = 0; i < 8; i += 1) {
      await new Promise((resolve) => setTimeout(resolve, 250));
      const token = await idTokenForMatchingPhoneUser(authInstance, phoneE164);
      if (token) {
        otpTrace("AUTO_VERIFY_AUTH_STATE_OK", {
          sessionId: redactId(sessionId),
          phone: redactPhone(phoneE164),
          waitMs: (i + 1) * 250,
        });
        return token;
      }
    }

    throw new Error("Android auto-verify did not complete.");
  })();
}

async function prepareLoginPhoneAuthOnce(): Promise<void> {
  await ensureFirebaseAuthReady();

  if (phoneSessions.size > 0) {
    otpTrace("LOGIN_PREPARED_SKIP_ACTIVE_OTP", { sessions: phoneSessions.size });
    return;
  }

  if (loginPrepared) {
    otpTrace("LOGIN_PREPARED_ALREADY");
    return;
  }

  const authInstance = await getAuthInstance();
  try {
    await authInstance.signOut();
  } catch {
    /* ignore */
  }
  await waitForAuthSignedOut(authInstance);
  loginPrepared = true;
  otpTrace("LOGIN_PREPARED");
}

export async function prepareLoginPhoneAuth(): Promise<void> {
  if (!loginPreparePromise) {
    loginPreparePromise = prepareLoginPhoneAuthOnce().finally(() => {
      loginPreparePromise = null;
    });
  }
  await loginPreparePromise;
}

export async function resetPhoneAuthAfterFailure(): Promise<void> {
  for (const id of [...phoneSessions.keys()]) disposeSession(id);
  const authInstance = await getAuthInstance();
  try {
    await authInstance.signOut();
  } catch {
    /* ignore */
  }
  await waitForAuthSignedOut(authInstance);
  loginPrepared = false;
  otpTrace("RESET_AFTER_FAILURE");
}

export function supportsPhoneOtp(): boolean {
  return true;
}

async function ensureSignedOutForPhoneAuth(
  authInstance: AuthInstance,
  phoneE164: string,
): Promise<void> {
  const user = authInstance.currentUser;
  if (!user) return;
  if (userMatchesPhone(user, phoneE164)) return;
  try {
    await authInstance.signOut();
  } catch {
    /* ignore */
  }
  await waitForAuthSignedOut(authInstance);
}

async function requestPhoneOtpOnce(
  phoneE164: string,
  opts?: { forceResend?: boolean },
): Promise<{ sessionId: string }> {
  await ensureFirebaseAuthReady();
  const authInstance = await getAuthInstance();
  const forceResend = !!opts?.forceResend;
  const requestNum = ++otpRequestCounter;

  purgeSessionsForPhone(phoneE164);

  otpTrace("OTP_REQUEST_STARTED", {
    requestNum,
    phone: redactPhone(phoneE164),
    forceResend,
    platform: Platform.OS,
  });

  await ensureSignedOutForPhoneAuth(authInstance, phoneE164);

  const sessionId = newSessionId();
  phoneSessions.set(sessionId, {
    verificationId: "",
    phoneE164,
    createdAt: Date.now(),
    requestNum,
  });

  if (Platform.OS === "android") {
    await attachAndroidPhoneVerification(authInstance, sessionId, phoneE164, forceResend);
  } else {
    const confirmation = await authInstance.signInWithPhoneNumber(phoneE164, forceResend);
    const verificationId = confirmation.verificationId;
    if (!verificationId) throw new Error("Failed to start phone verification.");
    phoneSessions.get(sessionId)!.verificationId = verificationId;
  }

  const session = phoneSessions.get(sessionId);
  if (!session?.verificationId) {
    disposeSession(sessionId);
    throw new Error("Failed to start phone verification.");
  }

  otpTrace("OTP_REQUEST_SUCCESS", {
    requestNum,
    sessionId: redactId(sessionId),
    verificationId: redactId(session.verificationId),
    phone: redactPhone(phoneE164),
    hasAutoSmsCode: !!session.autoSmsCode,
  });

  return { sessionId };
}

export async function requestPhoneOtp(
  phoneE164: string,
  opts?: { forceResend?: boolean },
): Promise<{ sessionId: string }> {
  const forceResend = !!opts?.forceResend;
  if (!forceResend && sendInFlight && sendInFlightPhone === phoneE164) {
    otpTrace("OTP_REQUEST_JOIN_INFLIGHT", { phone: redactPhone(phoneE164) });
    return sendInFlight;
  }

  sendInFlightPhone = phoneE164;
  sendInFlight = requestPhoneOtpOnce(phoneE164, opts);
  try {
    return await sendInFlight;
  } finally {
    sendInFlight = null;
    sendInFlightPhone = null;
  }
}

export function markOtpSessionAutofillLikely(_sessionId: string): void {
  /* manual-only OTP — no auto-verify */
}

async function confirmPhoneOtpOnce(sessionId: string, otp: string): Promise<string> {
  const session = phoneSessions.get(sessionId);
  if (!session) {
    otpTrace("VERIFY_MISSING_SESSION", { sessionId: redactId(sessionId) });
    throw new Error("OTP session expired. Please tap Resend OTP.");
  }

  if (!session.verificationId) {
    throw new Error("OTP session expired. Please tap Resend OTP.");
  }

  const code = String(otp || "").replace(/\D/g, "");
  if (code.length < 6) throw new Error("Enter the 6-digit OTP.");

  const authInstance = await getAuthInstance();
  const ageMs = Date.now() - session.createdAt;

  otpTrace("VERIFY_OTP", {
    requestNum: session.requestNum,
    sessionId: redactId(sessionId),
    verificationId: redactId(session.verificationId),
    phone: redactPhone(session.phoneE164),
    ageMs,
    hasAutoSmsCode: !!session.autoSmsCode,
    hasAutoSignInPromise: !!session.autoSignInPromise,
  });

  if (session.autoSignInPromise) {
    try {
      const idToken = await session.autoSignInPromise;
      disposeSession(sessionId);
      otpTrace("VERIFY_RESPONSE", {
        requestNum: session.requestNum,
        sessionId: redactId(sessionId),
        status: "success",
        mode: "android_auto_verify",
        ageMs,
      });
      return idToken;
    } catch {
      /* fall through to manual credential verify */
    }
  }

  const alreadySignedIn = await idTokenForMatchingPhoneUser(authInstance, session.phoneE164);
  if (alreadySignedIn) {
    disposeSession(sessionId);
    otpTrace("VERIFY_RESPONSE", {
      requestNum: session.requestNum,
      sessionId: redactId(sessionId),
      status: "success",
      mode: "auth_state_recover",
      ageMs,
    });
    return alreadySignedIn;
  }

  const tryCodes = [code];
  if (session.autoSmsCode && session.autoSmsCode !== code) {
    tryCodes.push(session.autoSmsCode);
  }

  let lastErr: unknown = null;
  for (const attemptCode of tryCodes) {
    try {
      const idToken = await signInWithOtpCode(authInstance, session.verificationId, attemptCode);
      disposeSession(sessionId);
      otpTrace("VERIFY_RESPONSE", {
        requestNum: session.requestNum,
        sessionId: redactId(sessionId),
        status: "success",
        mode: attemptCode === code ? "manual" : "auto_sms_cached",
        ageMs,
      });
      return idToken;
    } catch (err: unknown) {
      lastErr = err;
      if (!isFirebaseSessionExpiredError(err)) break;
    }
  }

  const errCode = String((lastErr as { code?: string })?.code || "");
  const errMsg = String((lastErr as Error)?.message || lastErr || "").slice(0, 160);
  otpTrace("VERIFY_RESPONSE", {
    requestNum: session.requestNum,
    sessionId: redactId(sessionId),
    status: "error",
    error: errCode || errMsg,
    ageMs,
  });

  if (isFirebaseSessionExpiredError(lastErr)) {
    const recovered = await idTokenForMatchingPhoneUser(authInstance, session.phoneE164);
    if (recovered) {
      disposeSession(sessionId);
      otpTrace("VERIFY_RESPONSE", {
        requestNum: session.requestNum,
        sessionId: redactId(sessionId),
        status: "success",
        mode: "session_expired_auth_recover",
        ageMs,
      });
      return recovered;
    }
    throw new Error("OTP session expired. Please tap Resend OTP and try again.");
  }

  throw lastErr;
}

export async function confirmPhoneOtp(
  sessionId: string,
  otp: string,
  _opts?: { likelyAutofill?: boolean },
): Promise<string> {
  const session = phoneSessions.get(sessionId);
  if (!session) {
    throw new Error("OTP session expired. Please tap Resend OTP.");
  }

  if (session.confirmPromise) {
    otpTrace("VERIFY_JOIN_INFLIGHT", { sessionId: redactId(sessionId) });
    return session.confirmPromise;
  }

  session.confirmPromise = confirmPhoneOtpOnce(sessionId, otp).finally(() => {
    const current = phoneSessions.get(sessionId);
    if (current) current.confirmPromise = undefined;
  });

  return session.confirmPromise;
}

export function watchPhoneAutoSignIn(
  phoneE164: string,
  onSignedIn: (idToken: string) => void,
): () => void {
  let cancelled = false;
  let unsub: (() => void) | null = null;

  void (async () => {
    try {
      await ensureFirebaseAuthReady();
      const authInstance = await getAuthInstance();
      unsub = authInstance.onAuthStateChanged(async (user) => {
        if (cancelled || !user || !userMatchesPhone(user, phoneE164)) return;
        try {
          const token = await user.getIdToken(true);
          if (!cancelled) {
            otpTrace("AUTH_STATE_AUTO_SIGN_IN", { phone: redactPhone(phoneE164) });
            onSignedIn(token);
          }
        } catch {
          /* ignore */
        }
      });
      const existing = authInstance.currentUser;
      if (!cancelled && existing && userMatchesPhone(existing, phoneE164)) {
        try {
          const token = await existing.getIdToken(true);
          if (!cancelled) onSignedIn(token);
        } catch {
          /* ignore */
        }
      }
    } catch {
      /* ignore */
    }
  })();

  return () => {
    cancelled = true;
    unsub?.();
    unsub = null;
  };
}

export function resetPendingPhoneVerification(phoneE164?: string): void {
  if (phoneE164) purgeSessionsForPhone(phoneE164);
  else {
    for (const id of [...phoneSessions.keys()]) disposeSession(id);
  }
}
