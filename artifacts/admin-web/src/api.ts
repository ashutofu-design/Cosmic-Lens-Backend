import { resolveApiBase } from "./lib/apiBase";

/** Runtime API origin — works on admin.coosmic.icu even when VITE_API_BASE was empty at build. */
export function getApiBase(): string {
  return resolveApiBase();
}

/** Legacy export; prefer getApiBase() for fetches. */
export const API_BASE = getApiBase();

import { getAdminDeviceId } from "./lib/adminDevice";
import { clearAdminGate, getAdminGateToken } from "./lib/adminGate";

// Admin token lives only in localStorage — set after username/password login.
const TOKEN_KEY = "cosmic_admin_token";

function getAdminToken(): string {
  try {
    return (localStorage.getItem(TOKEN_KEY) || "").trim();
  } catch {
    return "";
  }
}

export function hasAdminToken(): boolean {
  return !!getAdminToken();
}

export function adminLogout(): void {
  try {
    localStorage.removeItem(TOKEN_KEY);
    clearAdminGate();
  } catch {
    /* ignore */
  }
}

export async function adminLogin(
  username: string,
  password: string,
  mpin: string,
  opts?: { enrollCode?: string },
): Promise<void> {
  const deviceId = getAdminDeviceId();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    Accept: "application/json",
    "X-Admin-Device-Id": deviceId,
  };
  const gate = getAdminGateToken();
  if (gate) headers["X-Admin-Gate"] = gate;
  const res = await fetch(`${getApiBase()}/api/admin/login`, {
    method: "POST",
    headers,
    body: JSON.stringify({
      username,
      password,
      mpin,
      device_id: deviceId,
      enroll_code: opts?.enrollCode || "",
    }),
  });
  const data = (await res.json().catch(() => ({}))) as {
    token?: string;
    error?: string;
    device_id?: string;
  };
  if (!res.ok || !data.token) {
    if (data.error === "device_not_allowed") {
      throw new Error("DEVICE_NOT_ALLOWED");
    }
    if (data.error === "panel_locked") {
      throw new Error("PANEL_LOCKED");
    }
    if (data.error === "enroll_code_required") {
      throw new Error("ENROLL_CODE_REQUIRED");
    }
    throw new Error(
      data.error === "invalid_login"
        ? "Galat username, password ya MPIN."
        : data.error || `HTTP ${res.status}`,
    );
  }
  localStorage.setItem(TOKEN_KEY, String(data.token));
}

function adminHeaders(extra?: Record<string, string>): Record<string, string> {
  const headers: Record<string, string> = {
    Accept: "application/json",
    "X-Admin-Device-Id": getAdminDeviceId(),
    ...extra,
  };
  const gate = getAdminGateToken();
  if (gate) headers["X-Admin-Gate"] = gate;
  const token = getAdminToken();
  if (token) headers["X-Admin-Token"] = token;
  return headers;
}

async function adminFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const url = `${getApiBase()}${path}`;
  const res = await fetch(url, {
    ...init,
    headers: adminHeaders(init?.headers as Record<string, string> | undefined),
  });
  const data = await res.json().catch(() => ({}));
  if (res.status === 401 && getAdminToken()) {
    // Stale/rotated token — force re-login.
    adminLogout();
    window.location.reload();
  }
  if (!res.ok) {
    const err =
      (data as { error?: string }).error ||
      (data as { message?: string }).message ||
      `HTTP ${res.status}`;
    if (res.status === 404 && path.includes("pdf-generations")) {
      throw new Error(
        "pdf-generations API not found on server — deploy latest flask_app.py + pdf_generation_log.py, then restart API",
      );
    }
    if (res.status === 404 && path.includes("ask-questions")) {
      throw new Error(
        "ask-questions API not found on server — deploy latest flask_app.py + question_history.py, then restart API",
      );
    }
    throw new Error(err);
  }
  return data as T;
}

export interface Dashboard {
  generated_at: string;
  total_users: number;
  pro_users?: number;
  active_today?: number;
  total_kundli?: number;
  payments: {
    today_inr: number;
    week_inr: number;
    month_inr: number;
    lifetime_inr?: number;
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

export interface PdfGenerationItem {
  id: string;
  kind: string;
  label: string;
  user_id: number;
  generated_at: string;
  model: string;
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
  cost_inr: number;
  cost_usd: number;
  openai_call_count: number;
  regen_count: number;
  retry_count: number;
  extra_calls: number;
  report_cache_hit: boolean;
  polish_cache_hit: boolean;
  openai_skipped: boolean;
  force_regenerate: boolean;
  render_status: string;
  final_status: string;
  notes: string;
  phases: string[];
}

export type EngineVerificationStatus = "correct" | "wrong" | "doubt" | "unknown";

export interface EngineVerificationSummary {
  status: EngineVerificationStatus;
  label: string;
  reason: string;
  selected_engine?: string | null;
  ran_archetype?: string | null;
  engine_no?: number | null;
  engine_slice?: string | null;
  engine_admin_line?: string | null;
  recovered?: boolean;
}

export interface AnswerFidelitySummary {
  status: "pass" | "fail" | "unknown";
  label: string;
  reason?: string;
  shape?: string | null;
  attempts?: number;
  score?: number | null;
  repairs?: number;
  issues?: string[];
}

export interface AskLlmContext {
  version?: number;
  route?: string;
  question?: string;
  question_raw?: string | null;
  question_normalized?: string | null;
  question_meaning?: string | null;
  question_scope?: string | null;
  typo_corrected?: boolean;
    engine_ran?: string | null;
    engine_route_reason?: string | null;
    engine_display?: {
      engine_no?: number | null;
      slice_id?: string | null;
      engine_key?: string | null;
      kind?: string | null;
      label?: string | null;
      archetype?: string | null;
      admin_line?: string;
    } | null;
    engine_verification_summary?: EngineVerificationSummary | null;
    answer_fidelity_summary?: AnswerFidelitySummary | null;
    understanding_source?: string | null;
  question_type?: string;
  is_timing?: boolean;
  intent_source?: string;
  question_understood?: "yes" | "no" | null;
  understanding_line?: string;
  understanding_detail?: string | null;
  llm_intent?: {
    domain?: string;
    is_timing?: boolean;
    is_decision?: boolean;
    wants_explain?: boolean;
    mr_archetype?: string | null;
    routed_domain?: string;
    routed_archetype?: string;
    routed_timing?: boolean;
    career_archetype?: string | null;
    interpretation?: string;
    question_summary?: string;
    question_scope?: string;
    understanding_line?: string;
    confidence?: number;
    source?: string;
  } | null;
  llm_called?: boolean;
  answer_path?: string;
  answer_path_label?: string;
  engine_facts?: {
    archetype?: string;
    verdict?: string;
    summary?: string[];
    evidence?: string[];
    evidence_positive?: string[];
    evidence_negative?: string[];
    evidence_neutral?: string[];
    ignore?: string[];
    love_score?: number;
    arrange_score?: number;
    verdict_public?: string;
    confidence_ratio?: number;
  };
  skip_reason?: string | null;
  checks?: Record<string, unknown>;
  slice_meta?: Record<string, unknown>;
  blocks?: Record<string, unknown>;
  chart_text?: string;
  extra_rules?: string;
  system_prompt?: string;
  user_payload?: string;
  model?: string | null;
  max_tokens?: number | null;
  sizes?: Record<string, number>;
  raw?: string;
}

export interface MarriageBcpStep2Admin {
  title: string;
  detail: string;
  ages: number[];
  d1_ages?: number[];
  d9_ages?: number[];
  linkage_lines: string[];
  user_age?: number | null;
  recomputed_from_chart?: boolean;
  step0a?: Record<string, unknown>;
}

export interface AskQuestionItem {
  id: string;
  user_id: number;
  user_email: string;
  user_name: string;
  question_text: string;
  answer_text: string | null;
  answer_source: string | null;
  topic: string;
  verdict_summary: string;
  llm_model: string | null;
  prompt_tokens: number | null;
  completion_tokens: number | null;
  total_tokens: number | null;
  cached_tokens: number | null;
  cost_usd: number | null;
  cost_inr: number | null;
  engine_tag: string | null;
  llm_context_json?: string | null;
  llm_context?: AskLlmContext | null;
  marriage_bcp_step2?: MarriageBcpStep2Admin | null;
  created_at: string | null;
}

export interface LoginActivityItem {
  id: number;
  user_id: number | null;
  user_name: string;
  cosmo_user_id?: string;
  email: string | null;
  phone?: string | null;
  login_method?: "gmail" | "phone" | "unknown" | string;
  login_id?: string;
  user_status?: "new" | "old" | null;
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
  login_method?: "gmail" | "phone" | "unknown" | string;
  login_id?: string;
  user_status?: "new" | "old" | null;
  ip: string;
  success: boolean;
  created_at: string | null;
}

export interface UserDetail {
  user: {
    id: number;
    cosmo_user_id: string;
    name: string;
    email: string;
    plan: string;
    plan_expiry: string | null;
    preferred_language: string | null;
    daily_questions_used: number;
    daily_questions_date: string;
    daily_kundlis_used: number;
    daily_kundlis_date: string;
    astrovastu_room_credits: number;
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
  purchase_history?: Array<{
    id: string;
    kind: string;
    title: string;
    subtitle: string;
    amount_inr: number;
    order_id: string;
    status: string;
    paid_at: string | null;
  }>;
  purchase_summary?: {
    total_orders: number;
    total_spent_inr: number;
  };
  product_access?: Array<{
    key: string;
    label: string;
    owned: boolean;
    detail: string;
  }>;
  service_queues?: Array<{
    kind: string;
    label: string;
    ref: string;
    status: string;
    created_at: string | null;
    detail: string;
  }>;
  cached_reports?: Array<{
    id: string;
    report_type?: string;
    kind?: string;
    name?: string;
    dob?: string;
    language?: string;
    size_bytes?: number;
    date?: string | null;
  }>;
  app_usage?: {
    tracking_started: boolean;
    today_seconds: number;
    last_7_days_seconds: number;
    last_30_days_seconds: number;
    active_days_last_30: number;
    avg_seconds_per_active_day: number;
    daily: Array<{ date: string; seconds: number; sessions: number }>;
  };
  pack_referral?: {
    referral_code: string;
    referred_by_user_id: number | null;
    friends_signed_up: number;
    friends_converted: number;
    questions_earned: number;
    bonus_questions_left: number;
    recent_signups?: Array<{
      user_id: number;
      name: string;
      email: string;
      created_at: string | null;
    }>;
    recent_conversions?: Array<{
      buyer_user_id: number;
      source_kind: string;
      questions_granted: number;
      created_at: string | null;
    }>;
  };
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

export function fetchLoginActivity(opts?: {
  offset?: number;
  limit?: number;
  email?: string;
  success?: string;
}) {
  const q = new URLSearchParams({ limit: String(opts?.limit ?? 100) });
  if (opts?.offset) q.set("offset", String(opts.offset));
  if (opts?.email?.trim()) q.set("email", opts.email.trim());
  if (opts?.success) q.set("success", opts.success);
  return adminFetch<{ items: LoginActivityItem[]; total: number }>(
    `/api/admin/login-activity?${q}`,
  );
}

export function fetchPdfGenerations(opts?: { page?: number; kind?: string }) {
  const q = new URLSearchParams({ page: String(opts?.page ?? 1), per_page: "50" });
  if (opts?.kind?.trim()) q.set("kind", opts.kind.trim());
  return adminFetch<{
    items: PdfGenerationItem[];
    total: number;
    page: number;
    pages: number;
    per_page: number;
  }>(`/api/admin/pdf-generations?${q}`);
}

export function fetchAskQuestions(opts?: {
  page?: number;
  per_page?: number;
  email?: string;
  user_id?: number;
}) {
  const q = new URLSearchParams({
    page: String(opts?.page ?? 1),
    per_page: String(opts?.per_page ?? 50),
  });
  if (opts?.email?.trim()) q.set("email", opts.email.trim());
  if (opts?.user_id) q.set("user_id", String(opts.user_id));
  return adminFetch<{
    items: AskQuestionItem[];
    total: number;
    page: number;
    pages: number;
    per_page: number;
  }>(`/api/admin/ask-questions?${q}`);
}

export function fetchAskQuestionDetail(id: string) {
  return adminFetch<AskQuestionItem>(`/api/admin/ask-questions/${encodeURIComponent(id)}`);
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

export type AdminUserChartResponse = import("./v3KundliPack").AdminChartPayload;

/** Full kundli (D1/D9/KP/dasha) for V3 live chat Kundli panel. */
export function fetchAdminUserChart(userId: number) {
  return adminFetch<AdminUserChartResponse>(`/api/admin/users/${userId}/chart`);
}

export function lookupUser(userId: string) {
  const q = new URLSearchParams({ id: userId.trim() });
  return adminFetch<UserDetail>(`/api/admin/user-lookup?${q}`);
}

export type OrderLookupDeliveryState = "successful" | "pending" | "cancelled";

export interface OrderLookupResult {
  ok: boolean;
  found: boolean;
  kind?: string;
  label?: string;
  order_id?: string;
  public_order_id?: string;
  status?: string;
  delivery_state?: OrderLookupDeliveryState;
  user_id?: number;
  cosmo_user_id?: string;
  user_name?: string;
  created_at?: string | null;
  delivered_at?: string | null;
  admin_accepted_at?: string | null;
  admin_accepted?: boolean;
  plan?: string;
  deliverable?: string;
  amount_inr?: number | null;
  eta_label?: string | null;
  contact_method?: string;
  contact_value?: string;
  error?: string;
  message?: string;
}

export function lookupOrder(orderId: string) {
  const q = new URLSearchParams({ id: orderId.trim() });
  return adminFetch<OrderLookupResult>(`/api/admin/order-lookup?${q}`);
}

export interface UserAskProfileData {
  user_id: number;
  profile: {
    question_count?: number;
    avg_word_count?: number;
    avg_style?: string;
    lang_style?: string;
    tone?: string;
    dominant_emotion?: string;
    top_topic?: string;
    labels?: string[];
    topic_counts?: Record<string, number>;
    skeptic_rate?: number;
    followup_rate?: number;
    night_ratio?: number;
    questions_30d?: number;
    last_asked_at?: string;
  };
  labels: string[];
  recent_signals: {
    id?: number;
    question_id?: string | null;
    created_at?: string | null;
    word_count?: number;
    style?: string;
    emotion?: string;
    question_types?: string[];
    topics_detected?: string[];
    logged_topic?: string;
  }[];
  personalization_hint: string;
}

export function fetchUserAskProfile(userId: number) {
  return adminFetch<UserAskProfileData>(`/api/admin/users/${userId}/ask-profile`);
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

export interface LifeMapPersonBrief {
  name?: string;
  dob?: string;
  tob?: string;
  place?: string;
  gender?: string;
  mobile?: string;
  lat?: string | number;
  lon?: string | number;
  tz?: string;
}

export interface LifeMapPhotoRoom {
  room_type?: string;
  heading_deg?: number | null;
}

export interface LifeMapOrderItem {
  kind: string;
  label: string;
  order_id: string;
  public_order_id?: string;
  created_at: string | null;
  status: string;
  lang: string;
  urgent: boolean;
  contact_method: string;
  contact_value: string;
  deliverable?: "report" | "video" | string;
  plan?: string;
  amount_inr?: number | null;
  priority_fee_inr?: number | null;
  eta_hours?: number | null;
  eta_label?: string | null;
  user_id: number;
  cosmo_user_id?: string;
  user_name?: string;
  user_email?: string;
  user_phone?: string;
  birth?: LifeMapPersonBrief;
  subject: string;
  detail?: string;
  p1?: LifeMapPersonBrief;
  p2?: LifeMapPersonBrief;
  person?: LifeMapPersonBrief;
  couple_score?: number | string | null;
  couple_band?: string;
  room_type?: string;
  direction?: string;
  purchase_id?: number | null;
  sku?: string;
  has_image?: boolean;
  media_kind?: "image" | "pdf" | null;
  engine_snapshot?: Record<string, unknown>;
  admin_accepted_at?: string | null;
  admin_accepted?: boolean;
  business_type?: string;
  property_name?: string;
  photo_count?: number;
  photo_rooms?: LifeMapPhotoRoom[];
  has_pdf?: boolean;
  pdf_filename?: string;
  writing_hand?: string;
  session_id?: string;
  left_summary?: {
    quality_score?: number;
    usable?: boolean;
    confidence?: number;
    validation_status?: string;
    validation_message?: string;
    stage_scores?: Record<string, number>;
    original_image_reference?: string | null;
    annotated_image_reference?: string | null;
    major_line_count?: number;
  };
  right_summary?: {
    quality_score?: number;
    usable?: boolean;
    confidence?: number;
    validation_status?: string;
    validation_message?: string;
    stage_scores?: Record<string, number>;
    original_image_reference?: string | null;
    annotated_image_reference?: string | null;
    major_line_count?: number;
  };
  has_full_extraction?: boolean;
  production_validation?: Record<string, unknown>;
  overall_status?: string;
  overall_confidence?: number | null;
}

export interface LifeMapSection {
  key: string;
  title: string;
  orders: LifeMapOrderItem[];
  total: number;
}

export interface LifeMapOrdersResponse {
  sections: LifeMapSection[];
  total: number;
  unaccepted_count?: number;
  summary?: boolean;
  pending_ids?: string[];
}

export async function fetchLifeMapOrders(opts?: {
  status?: string;
  summary?: boolean;
}): Promise<LifeMapOrdersResponse> {
  const q = new URLSearchParams();
  q.set("status", opts?.status ?? "pending");
  if (opts?.summary) q.set("summary", "1");
  return adminFetch(`/api/admin/lifemap-orders?${q.toString()}`);
}

export async function fetchPalmistryOrder(orderId: string): Promise<Record<string, unknown>> {
  return adminFetch(`/api/admin/palmistry-orders/${encodeURIComponent(orderId)}`);
}

export async function fetchPalmistryExport(orderId: string): Promise<Record<string, unknown>> {
  return adminFetch(`/api/admin/palmistry-orders/${encodeURIComponent(orderId)}/export`);
}

export async function savePalmistryCorrection(
  orderId: string,
  payload: Record<string, unknown>,
): Promise<Record<string, unknown>> {
  return adminFetch(`/api/admin/palmistry-orders/${encodeURIComponent(orderId)}/corrections`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function fetchPalmistryMediaUrl(
  orderId: string,
  hand: "left" | "right",
  name: string,
): Promise<string | null> {
  const res = await fetch(
    `${getApiBase()}/api/admin/palmistry-orders/${encodeURIComponent(orderId)}/media/${hand}/${encodeURIComponent(name)}`,
    { headers: adminHeaders() },
  );
  if (!res.ok) return null;
  const blob = await res.blob();
  return URL.createObjectURL(blob);
}

export async function fetchLifeMapOrderMedia(
  orderId: string,
): Promise<{ url: string; mime: string }> {
  const res = await fetch(
    `${getApiBase()}/api/admin/lifemap-orders/astrovastu/${encodeURIComponent(orderId)}/media`,
    { headers: adminHeaders() },
  );
  if (!res.ok) {
    throw new Error(`Media load failed (${res.status})`);
  }
  const blob = await res.blob();
  return { url: URL.createObjectURL(blob), mime: blob.type };
}

export async function fetchBusinessVastuMedia(
  orderId: string,
  item: number | "plan",
): Promise<{ url: string; mime: string }> {
  const res = await fetch(
    `${getApiBase()}/api/admin/lifemap-orders/business-vastu/${encodeURIComponent(orderId)}/media?item=${item}`,
    { headers: adminHeaders() },
  );
  if (!res.ok) {
    throw new Error(`Media load failed (${res.status})`);
  }
  const blob = await res.blob();
  return { url: URL.createObjectURL(blob), mime: blob.type };
}

export interface LifeMapDeliverResult {
  ok: boolean;
  order_id?: string;
  report_id?: string;
  user_id?: number;
  bytes?: number;
  kind?: string;
  error?: string;
  detail?: string;
  notified?: boolean;
  cosmo_user_id?: string;
}

export async function deliverLifeMapOrder(opts: {
  kind: string;
  order_id: string;
  body: string;
  pages?: string[];
  page_images?: (string | null)[];
  attach_user_id?: string;
}): Promise<LifeMapDeliverResult> {
  return adminFetch(`/api/admin/lifemap-orders/deliver`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      kind: opts.kind,
      order_id: opts.order_id,
      body: opts.body,
      ...(opts.pages && opts.pages.length ? { pages: opts.pages } : {}),
      ...(opts.page_images && opts.page_images.length
        ? { page_images: opts.page_images }
        : {}),
      ...(opts.attach_user_id?.trim()
        ? { attach_user_id: opts.attach_user_id.trim() }
        : {}),
    }),
  });
}

export async function deleteLifeMapOrder(opts: {
  kind: string;
  order_id: string;
}): Promise<{ ok: boolean; deleted?: boolean; order_id?: string; error?: string }> {
  return adminFetch(`/api/admin/lifemap-orders/delete`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      kind: opts.kind,
      order_id: opts.order_id,
    }),
  });
}

export async function acceptLifeMapOrder(opts: {
  kind: string;
  order_id: string;
}): Promise<{
  ok: boolean;
  accepted?: boolean;
  already?: boolean;
  order_id?: string;
  admin_accepted_at?: string;
  error?: string;
}> {
  return adminFetch(`/api/admin/lifemap-orders/accept`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      kind: opts.kind,
      order_id: opts.order_id,
    }),
  });
}

export async function unacceptLifeMapOrder(opts: {
  kind: string;
  order_id: string;
}): Promise<{ ok: boolean; accepted?: boolean; order_id?: string; error?: string }> {
  return adminFetch(`/api/admin/lifemap-orders/unaccept`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      kind: opts.kind,
      order_id: opts.order_id,
    }),
  });
}

export interface BirthTimeRectificationOrderItem {
  order_id: string;
  created_at: string | null;
  status: string;
  user_id: number;
  cosmo_user_id?: string;
  full_name?: string;
  dob?: string;
  approx_tob?: string;
  birth_place?: string;
  event_count: number;
  has_15y_notes: boolean;
  notes_preview?: string;
}

export interface BirthTimeRectificationOrdersResponse {
  orders: BirthTimeRectificationOrderItem[];
  total: number;
  page: number;
  pages: number;
}

export interface BirthTimeRectificationOrderDetail {
  order_id: string;
  created_at: string | null;
  status: string;
  user_id: number;
  cosmo_user_id?: string;
  user_email?: string;
  user_phone?: string;
  full_name?: string;
  gender?: string;
  dob?: string;
  approx_tob?: string;
  birth_place?: string;
  milestone_events?: {
    id?: string;
    label?: string;
    month_year?: string;
    impact?: string;
  }[];
  last_15y_events_text?: string;
}

export async function fetchBirthTimeRectificationOrders(opts?: {
  page?: number;
  status?: string;
}): Promise<BirthTimeRectificationOrdersResponse> {
  const q = new URLSearchParams();
  if (opts?.page) q.set("page", String(opts.page));
  if (opts?.status) q.set("status", opts.status);
  const qs = q.toString();
  return adminFetch(`/api/admin/birth-time-rectification-orders${qs ? `?${qs}` : ""}`);
}

export function fetchBirthTimeRectificationOrderDetail(orderId: string) {
  return adminFetch<BirthTimeRectificationOrderDetail>(
    `/api/admin/birth-time-rectification-orders/${orderId}`,
  );
}

export interface V3LiveSessionItem {
  session_id: string;
  created_at: string;
  queued_at?: string;
  updated_at?: string;
  user_id?: number;
  cosmo_user_id?: string;
  user_name?: string;
  user_email?: string;
  user_phone?: string;
  pack_id?: string;
  minutes?: number;
  price_inr?: number;
  label?: string;
  preferred_language?: string;
  status: string;
  accepted_at?: string | null;
  awaiting_user_at?: string | null;
  awaiting_user_expires_at?: string | null;
  awaiting_user_remaining_seconds?: number | null;
  started_at?: string | null;
  expires_at?: string | null;
  remaining_seconds?: number | null;
  extend_seconds_used?: number;
  extend_seconds_left?: number;
  max_extend_seconds?: number;
  message_count?: number;
  queue_position?: number | null;
  is_queue_head?: boolean;
  requeue_count?: number;
  engine_busy?: boolean;
}

export interface V3ChatMessage {
  id: string;
  sender: "user" | "admin" | "system";
  text?: string;
  image_url?: string;
  ts: string;
}

export interface V3LiveSessionsResponse {
  sessions: V3LiveSessionItem[];
  total: number;
  page: number;
  pages: number;
  per_page: number;
  queue_head_id?: string | null;
  engine_busy?: boolean;
  queued_count?: number;
}

export function fetchVapidPublicKey() {
  return adminFetch<{ ok: boolean; key: string }>("/api/admin/push/vapid-public-key");
}

export function saveAdminPushSubscription(subscription: unknown) {
  return adminFetch<{ ok: boolean; id?: string; error?: string }>("/api/admin/push/subscribe", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ subscription }),
  });
}

export function sendAdminTestPush() {
  return adminFetch<{ ok: boolean; sent: number }>("/api/admin/push/test", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: "{}",
  });
}

export interface V3ChatSettings {
  ok: boolean;
  enabled: boolean;
  updated_at?: string | null;
}

export function fetchV3ChatSettings() {
  return adminFetch<V3ChatSettings>("/api/admin/cosmic-intelligence-v3-settings");
}

export function setV3ChatEnabled(enabled: boolean) {
  return adminFetch<V3ChatSettings>("/api/admin/cosmic-intelligence-v3-settings", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ enabled }),
  });
}

export async function fetchV3LiveSessions(opts?: {
  page?: number;
  status?: string;
}): Promise<V3LiveSessionsResponse> {
  const q = new URLSearchParams();
  if (opts?.page) q.set("page", String(opts.page));
  if (opts?.status) q.set("status", opts.status);
  const qs = q.toString();
  return adminFetch(`/api/admin/cosmic-intelligence-v3-sessions${qs ? `?${qs}` : ""}`);
}

export function acceptV3LiveSession(sessionId: string) {
  return adminFetch<{ ok: boolean; session: V3LiveSessionItem }>(
    `/api/admin/cosmic-intelligence-v3-sessions/${sessionId}/accept`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({}),
    },
  );
}

export function rejectV3LiveSession(sessionId: string) {
  return adminFetch<{ ok: boolean; session: V3LiveSessionItem }>(
    `/api/admin/cosmic-intelligence-v3-sessions/${sessionId}/reject`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({}),
    },
  );
}

export function fetchV3ChatMessages(sessionId: string, after?: string) {
  const q = after ? `?after=${encodeURIComponent(after)}` : "";
  return adminFetch<{
    ok: boolean;
    messages: V3ChatMessage[];
    session: V3LiveSessionItem;
  }>(`/api/admin/cosmic-intelligence-v3-sessions/${sessionId}/messages${q}`);
}

export function sendV3ChatMessage(
  sessionId: string,
  opts: { text?: string; data_url?: string; image_url?: string },
) {
  return adminFetch<{
    ok: boolean;
    message: V3ChatMessage;
    session: V3LiveSessionItem;
  }>(`/api/admin/cosmic-intelligence-v3-sessions/${sessionId}/message`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(opts),
  });
}

/** Light engine polish (30–40%) then send to user — no raw direct text send. */
export function polishSendV3ChatMessage(sessionId: string, text: string) {
  return adminFetch<{
    ok: boolean;
    original: string;
    polished: string;
    fallback?: boolean;
    message: V3ChatMessage;
    session: V3LiveSessionItem;
    error?: string;
  }>(`/api/admin/cosmic-intelligence-v3-sessions/${sessionId}/polish-send`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
}

export function setV3AdminTyping(sessionId: string, typing: boolean) {
  return adminFetch<{ ok: boolean; admin_typing?: boolean }>(
    `/api/admin/cosmic-intelligence-v3-sessions/${sessionId}/typing`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ typing }),
    },
  );
}

export function extendV3LiveSession(sessionId: string, seconds = 120) {
  return adminFetch<{
    ok: boolean;
    granted_seconds?: number;
    session?: V3LiveSessionItem;
    error?: string;
  }>(`/api/admin/cosmic-intelligence-v3-sessions/${sessionId}/extend`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ seconds }),
  });
}

export function endV3LiveSession(sessionId: string) {
  return adminFetch<{ ok: boolean; session: V3LiveSessionItem }>(
    `/api/admin/cosmic-intelligence-v3-sessions/${sessionId}/end`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({}),
    },
  );
}

// ── Help & Support inbox ─────────────────────────────────────────────────────

export interface SupportThreadItem {
  thread_id: string;
  created_at?: string;
  updated_at?: string;
  status: string;
  user_id?: number;
  cosmo_user_id?: string;
  user_name?: string;
  user_email?: string;
  user_phone?: string;
  message_count?: number;
  last_message_preview?: string;
  last_message_at?: string;
  last_sender?: string;
  unread_admin?: number;
  unread_user?: number;
  admin_typing?: boolean;
  escalated?: boolean;
  ai_handled?: boolean;
}

export interface SupportMessage {
  id: string;
  sender: "user" | "admin" | "system" | "bot";
  text?: string;
  image_url?: string;
  ts: string;
}

export function fetchSupportThreads(opts?: { page?: number; status?: string }) {
  const q = new URLSearchParams();
  if (opts?.page) q.set("page", String(opts.page));
  if (opts?.status) q.set("status", opts.status);
  const qs = q.toString();
  return adminFetch<{
    ok: boolean;
    threads: SupportThreadItem[];
    total: number;
    page: number;
    pages: number;
    waiting_admin_count?: number;
  }>(`/api/admin/support/threads${qs ? `?${qs}` : ""}`);
}

export function fetchSupportMessages(threadId: string, after?: string) {
  const q = after ? `?after=${encodeURIComponent(after)}` : "";
  return adminFetch<{
    ok: boolean;
    messages: SupportMessage[];
    thread: SupportThreadItem;
    admin_typing?: boolean;
  }>(`/api/admin/support/threads/${threadId}/messages${q}`);
}

export function sendSupportMessage(
  threadId: string,
  opts: { text?: string; data_url?: string; image_url?: string },
) {
  return adminFetch<{
    ok: boolean;
    message: SupportMessage;
    thread: SupportThreadItem;
  }>(`/api/admin/support/threads/${threadId}/message`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(opts),
  });
}

export function setSupportAdminTyping(threadId: string, typing: boolean) {
  return adminFetch<{ ok: boolean; admin_typing?: boolean }>(
    `/api/admin/support/threads/${threadId}/typing`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ typing }),
    },
  );
}

export function closeSupportThread(threadId: string) {
  return adminFetch<{ ok: boolean; deleted?: boolean; thread_id?: string }>(
    `/api/admin/support/threads/${threadId}/close`,
    { method: "POST", headers: { "Content-Type": "application/json" }, body: "{}" },
  );
}

export function reopenSupportThread(threadId: string) {
  return adminFetch<{ ok: boolean; thread: SupportThreadItem }>(
    `/api/admin/support/threads/${threadId}/reopen`,
    { method: "POST", headers: { "Content-Type": "application/json" }, body: "{}" },
  );
}

export type InstagramAnswerItem = {
  id: number;
  video_number: number;
  question: string;
  answer?: string;
  answer_preview?: string;
  status: "active" | "inactive" | string;
  created_at?: string | null;
  updated_at?: string | null;
};

export function fetchInstagramAnswers(opts?: {
  page?: number;
  per_page?: number;
  video_number?: string;
  question?: string;
  status?: string;
}) {
  const q = new URLSearchParams({
    page: String(opts?.page ?? 1),
    per_page: String(opts?.per_page ?? 50),
  });
  if (opts?.video_number?.trim()) q.set("video_number", opts.video_number.trim());
  if (opts?.question?.trim()) q.set("question", opts.question.trim());
  if (opts?.status?.trim()) q.set("status", opts.status.trim());
  return adminFetch<{
    items: InstagramAnswerItem[];
    total: number;
    page: number;
    pages: number;
    per_page: number;
  }>(`/api/admin/instagram-answers?${q}`);
}

export function fetchInstagramAnswer(id: number) {
  return adminFetch<InstagramAnswerItem>(
    `/api/admin/instagram-answers/${encodeURIComponent(String(id))}`,
  );
}

export async function createInstagramAnswer(payload: {
  video_number: number;
  question: string;
  answer: string;
  status?: string;
}) {
  const res = await adminFetch<InstagramAnswerItem>("/api/admin/instagram-answers", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return res;
}

export async function updateInstagramAnswer(
  id: number,
  payload: {
    video_number?: number;
    question?: string;
    answer?: string;
    status?: string;
  },
) {
  return adminFetch<InstagramAnswerItem>(
    `/api/admin/instagram-answers/${encodeURIComponent(String(id))}`,
    {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    },
  );
}

export function deleteInstagramAnswer(id: number) {
  return adminFetch<{ ok: boolean; id?: number }>(
    `/api/admin/instagram-answers/${encodeURIComponent(String(id))}`,
    { method: "DELETE" },
  );
}

export function patchInstagramAnswerStatus(id: number, status: "active" | "inactive") {
  return adminFetch<InstagramAnswerItem>(
    `/api/admin/instagram-answers/${encodeURIComponent(String(id))}/status`,
    {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status }),
    },
  );
}
