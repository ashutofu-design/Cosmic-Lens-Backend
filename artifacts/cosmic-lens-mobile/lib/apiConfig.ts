const HARDCODED_FALLBACK = "18370deb-aa55-4d9f-8391-57df5a15cf7a-00-phjaov5qh4np.kirk.replit.dev";

const domain = process.env.EXPO_PUBLIC_DOMAIN || HARDCODED_FALLBACK;

export const API_BASE = `https://${domain}`;

if (__DEV__) {
  console.log("[CosmicLens] EXPO_PUBLIC_DOMAIN:", process.env.EXPO_PUBLIC_DOMAIN);
  console.log("[CosmicLens] API_BASE resolved to:", API_BASE);

  fetch(`${API_BASE}/api/healthz`, { signal: AbortSignal.timeout(8000) })
    .then(r => r.json())
    .then(d => console.log("[CosmicLens] healthz OK:", JSON.stringify(d)))
    .catch(e => console.error("[CosmicLens] healthz FAILED:", e.message, "→ URL was:", `${API_BASE}/api/healthz`));
}
