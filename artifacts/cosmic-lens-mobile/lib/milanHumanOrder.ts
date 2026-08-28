import { API_BASE } from "@/lib/apiConfig";
import type { ProPdfLangCode } from "@/lib/proPdfLang";

export type MilanEngineSnapshot = {
  p1_name: string;
  p2_name: string;
  couple_score: number | null;
  couple_band: string | null;
  alert_count: number;
  p1_readiness: number | null;
  p2_readiness: number | null;
  synastry_available: boolean;
  engine_only: boolean;
};

export type MilanHumanOrderResult = {
  order_id: string;
  eta_hours: number;
  message: string;
};

function authHeaders(userId: number, apiKey?: string | null): Record<string, string> {
  return {
    "Content-Type": "application/json",
    Accept: "application/json",
    "X-User-Id": String(userId),
    ...(apiKey ? { "X-API-Key": apiKey } : {}),
  };
}

export async function submitMilanHumanOrder(opts: {
  p1: Record<string, unknown>;
  p2: Record<string, unknown>;
  lang: ProPdfLangCode;
  urgent: boolean;
  userId: number;
  cosmoUserId?: string | null;
  apiKey?: string | null;
  deliverable?: "report" | "video";
  whatsapp?: string;
  amountInr?: number;
  priorityFeeInr?: number;
}): Promise<MilanHumanOrderResult> {
  const deliverable = opts.deliverable === "video" ? "video" : "report";
  const resp = await fetch(`${API_BASE}/api/kundli-milan/human-order`, {
    method: "POST",
    headers: authHeaders(opts.userId, opts.apiKey),
    body: JSON.stringify({
      p1: opts.p1,
      p2: opts.p2,
      lang: opts.lang,
      urgent: opts.urgent,
      deliverable,
      ...(opts.amountInr != null ? { amount_inr: opts.amountInr } : {}),
      ...(opts.priorityFeeInr != null ? { priority_fee_inr: opts.priorityFeeInr } : {}),
      ...(opts.cosmoUserId ? { cosmo_user_id: opts.cosmoUserId } : {}),
      ...(deliverable === "video"
        ? { contact_method: "whatsapp", contact_value: opts.whatsapp || "", whatsapp: opts.whatsapp || "" }
        : {}),
    }),
  });
  const json = await resp.json().catch(() => ({}));
  if (!resp.ok) {
    const detail = typeof json.detail === "string" ? json.detail : json.error;
    throw new Error(String(detail || "Could not place order"));
  }
  return {
    order_id: String(json.order_id),
    eta_hours: Number(json.eta_hours) || 24,
    message: String(json.message || "Order received."),
  };
}
