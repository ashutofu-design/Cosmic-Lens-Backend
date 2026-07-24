import { firebaseConfig, isFirebaseConfigured } from "./firebaseConfig";

let _webAuth: any = null;

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

function friendlyAuthError(e: unknown): Error {
  const code = String((e as { code?: string })?.code || "");
  const msg = String((e as Error)?.message || e || "");

  if (code === "auth/operation-not-allowed") {
    return new Error(
      "Google provider is disabled. Firebase Console → Authentication → Sign-in method → Google → Enable.",
    );
  }
  if (code === "auth/unauthorized-domain") {
    const host = typeof window !== "undefined" ? window.location.hostname : "";
    return new Error(
      `This domain (${host}) is not authorized. Firebase Console → Authentication → Settings → Authorized domains → add "${host}".`,
    );
  }
  if (code === "auth/popup-blocked") {
    return new Error("Browser blocked the sign-in popup. Allow popups for this site and retry.");
  }
  if (code === "auth/popup-closed-by-user" || code === "auth/cancelled-popup-request") {
    return new Error("popup-closed-by-user");
  }
  if (code === "auth/network-request-failed" || /Failed to fetch|NetworkError/i.test(msg)) {
    return new Error(
      "Could not reach Google auth servers (identitytoolkit.googleapis.com). " +
        "Check: internet/VPN, ad-blocker blocking googleapis.com, or Google Cloud API-key restrictions " +
        "(the key must allow Identity Toolkit API from this origin).",
    );
  }
  return e instanceof Error ? e : new Error(msg);
}

/** Web: Firebase Google popup — no native Google Sign-In package needed. */
export async function signInWithGoogle(): Promise<string> {
  const auth = await getWebAuth();
  const { GoogleAuthProvider, signInWithPopup } = await import("firebase/auth");
  const provider = new GoogleAuthProvider();
  provider.addScope("email");
  provider.addScope("profile");
  provider.setCustomParameters({ prompt: "select_account" });
  try {
    const result = await signInWithPopup(auth, provider);
    if (!result.user) throw new Error("Google sign-in failed.");
    return result.user.getIdToken(true);
  } catch (e: unknown) {
    console.error("[CosmicLens] Google sign-in failed:", (e as { code?: string })?.code, e);
    throw friendlyAuthError(e);
  }
}

/** Sign out Firebase (after admin deleted account on server). */
export async function signOutFromFirebase(): Promise<void> {
  try {
    const auth = await getWebAuth();
    const { signOut } = await import("firebase/auth");
    await signOut(auth);
  } catch {
    /* already signed out */
  }
}
