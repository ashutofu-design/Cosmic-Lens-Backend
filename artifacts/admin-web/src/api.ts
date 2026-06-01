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

export interface AdminStats {
  total_users: number;
  pro_users: number;
  active_today: number;
  total_kundli: number;
  payments: Dashboard["payments"];
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

export interface AdminTransaction {
  id: string;
  user_id: number;
  user_name: string;
  user_email: string;
  kind: string;
  title: string;
  subtitle: string;
  amount_inr: number;
  order_id: string;
  status: string;
  paid_at: string | null;
}

export interface LoginActivityItem {
  id: number;
  user_id: number | null;
  user_name: string;
  email: string | null;
  provider: string;
  ip: string;
  success: boolean;
  error: string;
  created_at: string | null;
  profile_count: number;
}

export interface PurchaseLine {
  product?: string;
  sku?: string;
  label?: string;
  amount_inr: number;
  paid_at: string | null;
  property_name?: string;
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
  couple_report_purchases?: PurchaseLine[];
  astrovastu_purchases?: PurchaseLine[];
}

export function fetchDashboard() {
  return adminFetch<Dashboard>("/api/admin/dashboard");
}

export function fetchStats() {
  return adminFetch<AdminStats>("/api/admin/stats");
}

export function fetchTransactions(
  page: number,
  opts?: { email?: string; userId?: number; status?: string },
) {
  const q = new URLSearchParams({ page: String(page), per_page: "50" });
  if (opts?.email?.trim()) q.set("email", opts.email.trim());
  if (opts?.userId) q.set("user_id", String(opts.userId));
  if (opts?.status) q.set("status", opts.status);
  return adminFetch<{
    transactions: AdminTransaction[];
    total: number;
    page: number;
    pages: number;
  }>(`/api/admin/transactions?${q}`);
}

export interface GmailProfileSimple {
  id: number | null;
  legacy?: boolean;
  name: string;
  dob: string;
  tob: string;
  place: string;
}

export interface GmailSubscription {
  plan: string;
  plan_label: string;
  plan_expiry: string | null;
}

export interface GmailPurchaseLine {
  name: string;
  amount_inr: number;
  paid_at: string | null;
}

export interface GmailProfilesResponse {
  email: string;
  user_id: number | null;
  user_name: string;
  subscription: GmailSubscription | null;
  purchases: GmailPurchaseLine[];
  profiles: GmailProfileSimple[];
}

export function fetchGmailProfiles(opts: {
  email?: string;
  userId?: number;
}) {
  const q = new URLSearchParams();
  if (opts.email?.trim()) q.set("email", opts.email.trim());
  if (opts.userId) q.set("user_id", String(opts.userId));
  return adminFetch<GmailProfilesResponse>(`/api/admin/gmail-profiles?${q}`);
}

export function fetchLoginActivity(opts?: {
  offset?: number;
  limit?: number;
  email?: string;
  success?: string;
}) {
  const q = new URLSearchParams({ gmail_only: "1", limit: String(opts?.limit ?? 100) });
  if (opts?.offset) q.set("offset", String(opts.offset));
  if (opts?.email?.trim()) q.set("email", opts.email.trim());
  if (opts?.success) q.set("success", opts.success);
  return adminFetch<{ items: LoginActivityItem[]; total: number }>(
    `/api/admin/login-activity?${q}`,
  );
}

export function fetchUsers(page: number, search: string, plan: string) {
  const q = new URLSearchParams({ page: String(page), per_page: "50" });
  if (search.trim()) q.set("search", search.trim());
  if (plan.trim()) q.set("plan", plan.trim());
  return adminFetch<{
    users: AdminUser[];
    total: number;
    page: number;
    pages: number;
  }>(`/api/admin/users?${q}`);
}

export function deleteUser(id: number) {
  return adminFetch<{
    success: boolean;
    user_id?: number;
    email?: string;
    name?: string;
  }>(`/api/admin/users/${id}`, {
    method: "DELETE",
  });
}

/** Full delete by Gmail — user + profiles + kundli + login history (or login rows only). */
export function deleteAdminProfile(profileId: number) {
  return adminFetch<{ success: boolean; profile_id: number; user_id: number }>(
    `/api/admin/profiles/${profileId}`,
    { method: "DELETE" },
  );
}

export function deleteLegacyKundli(userId: number) {
  return adminFetch<{ success: boolean; user_id: number }>(
    `/api/admin/users/${userId}/legacy-kundli`,
    { method: "DELETE" },
  );
}

export function deleteGmailAccount(email: string) {
  const q = new URLSearchParams({ email: email.trim().toLowerCase() });
  return adminFetch<{
    success: boolean;
    user_id?: number | null;
    email?: string;
    login_rows_deleted?: number;
  }>(`/api/admin/gmail-account?${q}`, { method: "DELETE" });
}

export function fetchUserDetail(userId: number) {
  return adminFetch<UserDetail>(`/api/admin/users/${userId}`);
}

export function setUserPro(userId: number, enable: boolean) {
  return adminFetch<{ success: boolean; plan: string; is_pro: boolean }>(
    `/api/admin/users/${userId}/pro`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ is_pro: enable }),
    },
  );
}

export function resetKundliQuota(userId: number) {
  return adminFetch<{ success: boolean }>(`/api/admin/users/${userId}/reset-kundli-quota`, {
    method: "POST",
  });
}

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

export function downloadCsv(filename: string, headers: string[], rows: string[][]) {
  const escape = (v: string) => `"${String(v).replace(/"/g, '""')}"`;
  const lines = [headers.map(escape).join(",")];
  for (const row of rows) {
    lines.push(row.map(escape).join(","));
  }
  const blob = new Blob([lines.join("\n")], { type: "text/csv;charset=utf-8" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = filename;
  a.click();
  URL.revokeObjectURL(a.href);
}
