const API_BASE = (import.meta.env.VITE_API_BASE || "").replace(/\/$/, "");
const ADMIN_TOKEN = (import.meta.env.VITE_ADMIN_SECRET || "").trim();

function adminHeaders(extra?: Record<string, string>): Record<string, string> {
  const headers: Record<string, string> = {
    Accept: "application/json",
    ...extra,
  };
  if (ADMIN_TOKEN) headers["X-Admin-Token"] = ADMIN_TOKEN;
  return headers;
}

async function adminFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const url = `${API_BASE}${path}`;
  const res = await fetch(url, {
    ...init,
    headers: adminHeaders(init?.headers as Record<string, string> | undefined),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error((data as { error?: string }).error || `HTTP ${res.status}`);
  }
  return data as T;
}

export interface Dashboard {
  generated_at: string;
  total_users: number;
  payments: {
    today_inr: number;
    week_inr: number;
    month_inr: number;
    lifetime_inr: number;
  };
  purchases_by_product: { key: string; label: string; count: number }[];
  astrovastu_purchases: { sku: string; label: string; count: number }[];
  reports: {
    total_generated: number;
    by_kind: { kind: string; label: string; count: number }[];
    highest: { kind: string; label: string; count: number } | null;
    lowest: { kind: string; label: string; count: number } | null;
  };
  subscriptions: {
    enabled: boolean;
    message: string;
    plan_counts: Record<string, number>;
  };
}

export interface AdminUser {
  id: number;
  name: string;
  phone: string;
  email: string;
  plan: string;
  plan_expiry: string | null;
  last_login: string | null;
  created_at: string | null;
  kundli_profiles_count: number;
  purchases: {
    love_compatibility_pdf: number;
    milan_pro_pdf: number;
    face_reading_pro: number;
    life_mastery_pdf: number;
    total_paid_orders: number;
  };
  career_unlocked: boolean;
}

export function fetchDashboard() {
  return adminFetch<Dashboard>("/api/admin/dashboard");
}

export function fetchUsers(page: number, search: string) {
  const q = new URLSearchParams({ page: String(page), per_page: "50" });
  if (search.trim()) q.set("search", search.trim());
  return adminFetch<{
    users: AdminUser[];
    total: number;
    page: number;
    pages: number;
  }>(`/api/admin/users?${q}`);
}

export function deleteUser(id: number) {
  return adminFetch<{ success: boolean }>(`/api/admin/users/${id}`, {
    method: "DELETE",
  });
}

export interface KundliProfileRow {
  name: string;
  relation: string;
  gender: string;
  is_primary: boolean;
  updated_at: string | null;
  dob: string;
  tob: string;
  place: string;
  lat: number | null;
  lon: number | null;
  tz: number | null;
  has_chart: boolean;
}

export interface LegacyKundliRow {
  name: string;
  dob: string;
  tob: string;
  place: string;
  lat: number | null;
  lon: number | null;
  tz: number | null;
  has_chart: boolean;
}

export interface LoginActivityRow {
  id: number;
  email: string | null;
  ip: string;
  success: boolean;
  created_at: string | null;
}

export interface UserDetail {
  user: {
    id: number;
    name: string;
    phone: string;
    email: string;
    plan: string;
    plan_expiry: string | null;
    last_login: string | null;
    created_at: string | null;
    career_unlocked: boolean;
  };
  kundli_profiles: {
    active_count: number;
    deleted_count: number;
    profiles: KundliProfileRow[];
  };
  legacy_kundli: LegacyKundliRow | null;
  recent_logins?: LoginActivityRow[];
}

export function fetchUserDetail(userId: number) {
  return adminFetch<UserDetail>(`/api/admin/users/${userId}`);
}

/** Use legacy kundlis row when profile birth fields are empty (older API rows). */
export function profileBirthFields(
  p: KundliProfileRow,
  legacy: LegacyKundliRow | null | undefined,
) {
  const leg = p.is_primary ? legacy : null;
  return {
    dob: p.dob || leg?.dob || "",
    tob: p.tob || leg?.tob || "",
    place: p.place || leg?.place || "",
    lat: p.lat ?? leg?.lat ?? null,
    lon: p.lon ?? leg?.lon ?? null,
    has_chart: p.has_chart || !!leg?.has_chart,
  };
}

export function formatInr(n: number) {
  return `₹${n.toLocaleString("en-IN")}`;
}

/** Server stores naive UTC timestamps — parse as UTC, display in India time. */
function parseServerUtc(iso: string | null): Date | null {
  if (!iso?.trim()) return null;
  const s = iso.trim();
  const hasTz = /[zZ]|[+-]\d{2}:?\d{2}$/.test(s);
  const d = new Date(hasTz ? s : `${s}Z`);
  return Number.isNaN(d.getTime()) ? null : d;
}

export function formatDate(iso: string | null) {
  const d = parseServerUtc(iso);
  if (!d) return "—";
  try {
    return d.toLocaleString("en-IN", {
      timeZone: "Asia/Kolkata",
      dateStyle: "medium",
      timeStyle: "short",
    });
  } catch {
    return iso ?? "—";
  }
}
