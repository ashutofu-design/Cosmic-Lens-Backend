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

/** Web: Firebase Google popup — no native Google Sign-In package needed. */
export async function signInWithGoogle(): Promise<string> {
  const auth = await getWebAuth();
  const { GoogleAuthProvider, signInWithPopup } = await import("firebase/auth");
  const provider = new GoogleAuthProvider();
  provider.addScope("email");
  provider.addScope("profile");
  provider.setCustomParameters({ prompt: "select_account" });
  const result = await signInWithPopup(auth, provider);
  if (!result.user) throw new Error("Google sign-in failed.");
  return result.user.getIdToken(true);
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
