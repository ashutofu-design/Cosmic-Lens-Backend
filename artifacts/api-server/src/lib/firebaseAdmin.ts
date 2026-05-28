import { App, cert, getApp, getApps, initializeApp } from "firebase-admin/app";
import { DecodedIdToken, getAuth } from "firebase-admin/auth";

export class FirebaseAuthError extends Error {
  readonly code: "not_configured" | "bad_credentials" | "invalid_token";

  constructor(
    code: FirebaseAuthError["code"],
    message: string,
    options?: { cause?: unknown },
  ) {
    super(message, options);
    this.name = "FirebaseAuthError";
    this.code = code;
  }
}

function loadServiceAccount():
  | { project_id?: string; client_email?: string; private_key?: string }
  | undefined {
  const rawJson = process.env["FIREBASE_SERVICE_ACCOUNT_JSON"]?.trim();
  if (rawJson) {
    try {
      return JSON.parse(rawJson) as {
        project_id?: string;
        client_email?: string;
        private_key?: string;
      };
    } catch (err) {
      throw new FirebaseAuthError(
        "bad_credentials",
        `FIREBASE_SERVICE_ACCOUNT_JSON is not valid JSON: ${
          err instanceof Error ? err.message : String(err)
        }`,
        { cause: err },
      );
    }
  }

  const rawB64 = process.env["FIREBASE_SERVICE_ACCOUNT_JSON_BASE64"]?.trim();
  if (rawB64) {
    try {
      const decoded = Buffer.from(rawB64, "base64").toString("utf8");
      return JSON.parse(decoded) as {
        project_id?: string;
        client_email?: string;
        private_key?: string;
      };
    } catch (err) {
      throw new FirebaseAuthError(
        "bad_credentials",
        `FIREBASE_SERVICE_ACCOUNT_JSON_BASE64 is invalid: ${
          err instanceof Error ? err.message : String(err)
        }`,
        { cause: err },
      );
    }
  }

  // If GOOGLE_APPLICATION_CREDENTIALS is set, firebase-admin can pick it up
  // via ADC. In that case we don't need to parse anything here.
  if (process.env["GOOGLE_APPLICATION_CREDENTIALS"]?.trim()) {
    return undefined;
  }

  return undefined;
}

let cachedApp: App | undefined;

export function isFirebaseConfigured(): boolean {
  return Boolean(
    process.env["FIREBASE_SERVICE_ACCOUNT_JSON"]?.trim() ||
      process.env["FIREBASE_SERVICE_ACCOUNT_JSON_BASE64"]?.trim() ||
      process.env["GOOGLE_APPLICATION_CREDENTIALS"]?.trim(),
  );
}

export function getFirebaseApp(): App {
  if (cachedApp) {
    return cachedApp;
  }

  if (getApps().length > 0) {
    cachedApp = getApp();
    return cachedApp;
  }

  const sa = loadServiceAccount();
  if (sa) {
    cachedApp = initializeApp({
      credential: cert({
        projectId: sa.project_id,
        clientEmail: sa.client_email,
        privateKey: sa.private_key,
      }),
    });
    return cachedApp;
  }

  if (process.env["GOOGLE_APPLICATION_CREDENTIALS"]?.trim()) {
    cachedApp = initializeApp();
    return cachedApp;
  }

  throw new FirebaseAuthError(
    "not_configured",
    "Firebase Admin credentials are not set. Add one of: FIREBASE_SERVICE_ACCOUNT_JSON, FIREBASE_SERVICE_ACCOUNT_JSON_BASE64, or GOOGLE_APPLICATION_CREDENTIALS.",
  );
}

export async function verifyFirebaseIdToken(
  idToken: string,
  opts?: { checkRevoked?: boolean },
): Promise<DecodedIdToken> {
  if (!idToken || typeof idToken !== "string") {
    throw new FirebaseAuthError("invalid_token", "Missing ID token");
  }

  try {
    const app = getFirebaseApp();
    return await getAuth(app).verifyIdToken(idToken, opts?.checkRevoked ?? false);
  } catch (err) {
    if (err instanceof FirebaseAuthError) {
      throw err;
    }
    throw new FirebaseAuthError(
      "invalid_token",
      `Token verification failed: ${err instanceof Error ? err.message : String(err)}`,
      { cause: err },
    );
  }
}

