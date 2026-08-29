/** Resolve API origin for admin-web fetches (static build + dev proxy). */
export function resolveApiBase(): string {
  if (typeof window !== "undefined") {
    const host = window.location.hostname.toLowerCase();
    // admin.coosmic.icu nginx proxies /api → gunicorn. Same-origin avoids CORS hangs.
    if (host === "admin.coosmic.icu") {
      return window.location.origin;
    }
  }

  const fromEnv = (import.meta.env.VITE_API_BASE || "").trim().replace(/\/$/, "");
  if (fromEnv) return fromEnv;

  if (typeof window !== "undefined") {
    const host = window.location.hostname.toLowerCase();
    if (host === "coosmic.icu" || host === "www.coosmic.icu") {
      return "https://api.coosmic.icu";
    }
  }

  return "";
}
