import { Platform } from "react-native";

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

function googleWebClientId(): string {
  return (
    process.env.EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID?.trim() ||
    process.env.EXPO_PUBLIC_FIREBASE_WEB_OAUTH_CLIENT_ID?.trim() ||
    webClientIdFromGoogleServices() ||
    ""
  );
}

let _googleSignInConfigured = false;

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
  if (_googleSignInConfigured) return;

  const { GoogleSignin } = await import("@react-native-google-signin/google-signin");
  GoogleSignin.configure({
    webClientId,
    offlineAccess: false,
  });
  _googleSignInConfigured = true;
}

/** Native: Google Sign-In SDK + Firebase credential. */
export async function signInWithGoogle(): Promise<string> {
  await ensureGoogleSignInConfigured();
  const { GoogleSignin } = await import("@react-native-google-signin/google-signin");

  if (Platform.OS === "android") {
    await GoogleSignin.hasPlayServices({ showPlayServicesUpdateDialog: true });
  }

  const signInResult = await GoogleSignin.signIn();
  const idToken = signInResult.data?.idToken;
  if (!idToken) {
    throw new Error("Google sign-in was cancelled or did not return a token.");
  }

  const authMod = await import("@react-native-firebase/auth");
  const authNs = authMod.default ?? authMod;
  const authInstance = await getNativeAuth();
  const credential = authNs.GoogleAuthProvider.credential(idToken);
  const userCred = await authInstance.signInWithCredential(credential);
  if (!userCred?.user) throw new Error("Google sign-in failed.");
  return userCred.user.getIdToken(true);
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
