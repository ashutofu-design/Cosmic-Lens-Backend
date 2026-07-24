import { Platform } from "react-native";

const EXPECTED_WEB_CLIENT_ID =
  "887649003708-u1cd95e2efl9hvi81j2gut5jnp65ghhp.apps.googleusercontent.com";

function webClientIdFromGoogleServices(): string {
  try {
    const gs = require("../google-services.json") as {
      client?: Array<{ oauth_client?: Array<{ client_type?: number; client_id?: string }> }>;
    };
    const web = gs.client?.[0]?.oauth_client?.find((c) => c.client_type === 3);
    return web?.client_id?.trim() || "";
  } catch {
    return "";
  }
}

/**
 * Prefer google-services.json (baked into the native app) so a wrong EAS env
 * cannot override the Web OAuth client and cause Android "aborted" / cancelled.
 */
function googleWebClientId(): string {
  return (
    webClientIdFromGoogleServices() ||
    process.env.EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID?.trim() ||
    process.env.EXPO_PUBLIC_FIREBASE_WEB_OAUTH_CLIENT_ID?.trim() ||
    EXPECTED_WEB_CLIENT_ID
  );
}

function friendlyGoogleSignInError(e: unknown): Error {
  const anyErr = e as { code?: string | number; message?: string };
  const code = String(anyErr?.code ?? "");
  const msg = String(anyErr?.message || e || "");
  const lower = msg.toLowerCase();

  if (
    code === "10" ||
    code === "DEVELOPER_ERROR" ||
    /developer_error|developer console|code:\s*10\b/i.test(msg)
  ) {
    return new Error(
      "Google Sign-In config mismatch (SHA-1 / package / webClientId). " +
        "Firebase mein Play App Signing SHA-1 add karke naya build chahiye.",
    );
  }
  if (
    code === "12501" ||
    code === "SIGN_IN_CANCELLED" ||
    lower.includes("cancelled") ||
    lower.includes("canceled") ||
    lower.includes("aborted")
  ) {
    // Android often reports config failures as cancelled/aborted.
    return new Error(
      "Google sign-in aborted — usually SHA-1 / OAuth client mismatch. " +
        "Agar aapne cancel nahi kiya, Firebase SHA-1 + webClientId check karo.",
    );
  }
  if (code === "12500" || /sign.?in.?failed/i.test(msg)) {
    return new Error(
      "Google sign-in failed (12500). Check Firebase Google provider + OAuth clients.",
    );
  }
  return e instanceof Error ? e : new Error(msg || "Google sign-in failed.");
}

let _googleSignInConfigured = false;
let _configuredWebClientId = "";

async function getNativeAuth() {
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

async function ensureGoogleSignInConfigured(): Promise<void> {
  const webClientId = googleWebClientId();
  if (!webClientId) {
    throw new Error("Google Sign-In is not configured (missing Web OAuth client ID).");
  }
  if (_googleSignInConfigured && _configuredWebClientId === webClientId) return;

  const { GoogleSignin } = await import("@react-native-google-signin/google-signin");
  GoogleSignin.configure({
    webClientId,
    offlineAccess: false,
  });
  _googleSignInConfigured = true;
  _configuredWebClientId = webClientId;
}

/** Native: Google Sign-In SDK + Firebase credential. */
export async function signInWithGoogle(): Promise<string> {
  await ensureGoogleSignInConfigured();
  const { GoogleSignin } = await import("@react-native-google-signin/google-signin");

  if (Platform.OS === "android") {
    await GoogleSignin.hasPlayServices({ showPlayServicesUpdateDialog: true });
  }

  // Clear stale Google session — can surface as "aborted" on Android.
  try {
    await GoogleSignin.signOut();
  } catch {
    /* ignore */
  }

  let signInResult: Awaited<ReturnType<typeof GoogleSignin.signIn>>;
  try {
    signInResult = await GoogleSignin.signIn();
  } catch (e: unknown) {
    throw friendlyGoogleSignInError(e);
  }

  const resultType = (signInResult as { type?: string })?.type;
  if (resultType === "cancelled" || resultType === "noSavedCredentialFound") {
    throw friendlyGoogleSignInError({
      code: "SIGN_IN_CANCELLED",
      message: "aborted",
    });
  }

  let idToken =
    signInResult.data?.idToken ||
    (signInResult as { idToken?: string }).idToken ||
    "";
  if (!idToken) {
    try {
      const tokens = await GoogleSignin.getTokens();
      idToken = tokens?.idToken || "";
    } catch {
      /* ignore */
    }
  }
  if (!idToken) {
    throw friendlyGoogleSignInError({
      code: "SIGN_IN_CANCELLED",
      message: "Google sign-in aborted (no idToken). Check webClientId + SHA-1.",
    });
  }

  try {
    const authMod = await import("@react-native-firebase/auth");
    const authNs = authMod.default ?? authMod;
    const authInstance = await getNativeAuth();
    const credential = authNs.GoogleAuthProvider.credential(idToken);
    const userCred = await authInstance.signInWithCredential(credential);
    if (!userCred?.user) throw new Error("Google sign-in failed.");
    return userCred.user.getIdToken(true);
  } catch (e: unknown) {
    throw friendlyGoogleSignInError(e);
  }
}

/** Sign out Firebase + Google (after admin deleted account on server). */
export async function signOutFromFirebase(): Promise<void> {
  try {
    const authInstance = await getNativeAuth();
    await authInstance.signOut();
  } catch {
    /* ignore */
  }
  try {
    await ensureGoogleSignInConfigured();
    const { GoogleSignin } = await import("@react-native-google-signin/google-signin");
    await GoogleSignin.signOut();
  } catch {
    /* ignore */
  }
}
