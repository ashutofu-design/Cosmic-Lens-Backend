import { API_BASE, apiFetch } from "./apiConfig";
import type { AuthUser } from "@/context/UserContext";

function parseApiError(res: Response, raw: string): Error {
  let data: { error?: string; message?: string } = {};
  try {
    data = raw ? JSON.parse(raw) : {};
  } catch {
    /* HTML or plain text from proxy */
  }
  const code = data.error;
  let message = data.message || "";
  if (!message && code === "http_error") {
    message = res.status === 404
      ? "Server par naya API nahi hai — git pull + pm2 restart cosmic-api"
      : `Request failed (${res.status})`;
  }
  if (!message) message = code || raw.slice(0, 160) || `HTTP ${res.status}`;
  const err = new Error(message);
  (err as Error & { code?: string; status?: number }).code = code;
  (err as Error & { code?: string; status?: number }).status = res.status;
  return err;
}

export async function updatePersonalDetails(args: {
  userId: number;
  apiKey: string;
  name?: string;
  phone?: string;
}): Promise<AuthUser> {
  const body: Record<string, string> = {};
  if (args.name?.trim()) body.name = args.name.trim();
  if (args.phone?.trim()) body.phone = args.phone.trim();

  const bases = [
    `${API_BASE}/api/user/${args.userId}/personal`,
    `${API_BASE}/api/user/${args.userId}/personal-details`,
  ];

  const headers = {
    "Content-Type": "application/json",
    "X-API-Key": args.apiKey,
  };
  const init = { headers, body: JSON.stringify(body) };

  let lastErr: Error | null = null;
  for (const url of bases) {
    for (const method of ["PUT", "POST"] as const) {
      const res = await apiFetch(url, { ...init, method });
      const raw = await res.text();
      if (res.ok) {
        let data: { user?: AuthUser; ok?: boolean } = {};
        try {
          data = JSON.parse(raw);
        } catch {
          throw new Error("Invalid server response");
        }
        if (!data.user) throw new Error("Save failed — no user in response");
        return data.user;
      }
      const err = parseApiError(res, raw);
      lastErr = err;
      if (res.status === 405 && method === "POST") continue;
      if (err.status !== 404) throw err;
    }
  }
  throw lastErr ?? new Error("Could not save personal details");
}
