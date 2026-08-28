const DEVICE_KEY = "cosmic_admin_device_id";

function randomHex(bytes: number): string {
  const arr = new Uint8Array(bytes);
  crypto.getRandomValues(arr);
  return Array.from(arr, (b) => b.toString(16).padStart(2, "0")).join("");
}

/** Stable admin device id — used for server-side allowlist. */
export function getAdminDeviceId(): string {
  try {
    const existing = (localStorage.getItem(DEVICE_KEY) || "").trim().toLowerCase();
    if (/^[a-f0-9]{16,64}$/.test(existing)) return existing;
    const created = randomHex(16);
    localStorage.setItem(DEVICE_KEY, created);
    return created;
  } catch {
    return randomHex(16);
  }
}

export function adminDeviceIdRedacted(id: string): string {
  const did = String(id || "").trim();
  if (did.length <= 10) return did;
  return `${did.slice(0, 6)}…${did.slice(-4)}`;
}
