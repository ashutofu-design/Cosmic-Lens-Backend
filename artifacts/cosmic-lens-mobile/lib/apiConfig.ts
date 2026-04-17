const REPLIT_DOMAIN = "18370deb-aa55-4d9f-8391-57df5a15cf7a-00-phjaov5qh4np.kirk.replit.dev";

const domain = process.env.EXPO_PUBLIC_DOMAIN || REPLIT_DOMAIN;

export const API_BASE = `https://${domain}`;

export const API_HEADERS: Record<string, string> = {
  "Content-Type": "application/json",
  "Accept": "application/json",
  "bypass-tunnel-reminder": "true",
};

export async function apiFetch(url: string, init?: RequestInit): Promise<Response> {
  const merged: RequestInit = {
    ...init,
    headers: {
      ...API_HEADERS,
      ...(init?.headers as Record<string, string> | undefined),
    },
  };
  // Retry once on transient "Network request failed" — common on cellular networks
  // when the first TLS handshake to a fresh host hiccups. We don't retry on AbortError
  // (timeout/cancel), HTTP errors, or other failure modes.
  try {
    return await fetch(url, merged);
  } catch (e: any) {
    if (e?.name === "AbortError") throw e;
    const msg = String(e?.message || "");
    if (!/Network request failed|TypeError|fetch/i.test(msg)) throw e;
    await new Promise(r => setTimeout(r, 600));
    return fetch(url, merged);
  }
}

if (__DEV__) {
  console.log("[CosmicLens] EXPO_PUBLIC_DOMAIN:", process.env.EXPO_PUBLIC_DOMAIN);
  console.log("[CosmicLens] API_BASE resolved to:", API_BASE);

  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), 8000);
  fetch(`${API_BASE}/api/healthz`, {
    signal: ctrl.signal,
    headers: { "bypass-tunnel-reminder": "true" },
  })
    .then(r => r.json())
    .then(d => console.log("[CosmicLens] healthz OK ✓", JSON.stringify(d)))
    .catch(e => console.error("[CosmicLens] healthz FAILED:", e.message, "→", `${API_BASE}/api/healthz`))
    .finally(() => clearTimeout(timer));
}
