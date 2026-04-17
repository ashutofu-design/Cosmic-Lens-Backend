/**
 * Firebase client configuration.
 *
 * Values come from EXPO_PUBLIC_FIREBASE_* env variables so the same code works
 * across local dev, EAS builds, and Replit preview without hardcoding secrets
 * in source control.
 *
 * Where to set them:
 *   - Replit: add as Secrets (EXPO_PUBLIC_* are exposed to the client bundle).
 *   - EAS:    add to `eas.json` under `env` for each profile, or `.env` files.
 *
 * These values are PUBLIC by design (they identify the Firebase project to the
 * client). True security comes from Firebase App Check + the Admin SDK on the
 * backend, NOT from hiding these values.
 */

export type FirebaseClientConfig = {
  apiKey:            string;
  authDomain:        string;
  projectId:         string;
  appId:             string;
  messagingSenderId: string;
  storageBucket:     string;
};

export const firebaseConfig: FirebaseClientConfig = {
  apiKey:            process.env.EXPO_PUBLIC_FIREBASE_API_KEY            ?? "",
  authDomain:        process.env.EXPO_PUBLIC_FIREBASE_AUTH_DOMAIN        ?? "",
  projectId:         process.env.EXPO_PUBLIC_FIREBASE_PROJECT_ID         ?? "",
  appId:             process.env.EXPO_PUBLIC_FIREBASE_APP_ID             ?? "",
  messagingSenderId: process.env.EXPO_PUBLIC_FIREBASE_MESSAGING_SENDER_ID ?? "",
  storageBucket:     process.env.EXPO_PUBLIC_FIREBASE_STORAGE_BUCKET     ?? "",
};

export function isFirebaseConfigured(): boolean {
  return Boolean(
    firebaseConfig.apiKey &&
    firebaseConfig.authDomain &&
    firebaseConfig.projectId &&
    firebaseConfig.appId
  );
}
