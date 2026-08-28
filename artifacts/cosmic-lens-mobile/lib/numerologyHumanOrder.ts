import { API_BASE } from "@/lib/apiConfig";
import type { ProPdfLangCode } from "@/lib/proPdfLang";

export type NumerologyHumanOrderResult = {
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

/** Submit Numerology Pro booking for founder PDF → My Reports or WhatsApp video. */
export async function submitNumerologyHumanOrder(opts: {
  userId: number;
  apiKey?: string | null;
  cosmoUserId?: string | null;
  lang: ProPdfLangCode | string;
  urgent?: boolean;
  purchaseId?: number | null;
  deliverable?: "report" | "video";
  whatsapp?: string;
  params: Record<string, unknown>;
}): Promise<NumerologyHumanOrderResult> {
  const deliverable = opts.deliverable === "video" ? "video" : "report";
  const name = String(opts.params.name || "").trim();
  const dob = String(opts.params.dob || "").trim();
  const resp = await fetch(`${API_BASE}/api/numerology/human-order`, {
    method: "POST",
    headers: authHeaders(opts.userId, opts.apiKey),
    body: JSON.stringify({
      user_id: opts.userId,
      name,
      dob,
      tob: opts.params.tob,
      mobile: opts.params.mobile,
      place: opts.params.place,
      lang: opts.lang,
      urgent: !!opts.urgent,
      purchase_id: opts.purchaseId || undefined,
      deliverable,
      params: opts.params,
      ...(opts.cosmoUserId ? { cosmo_user_id: opts.cosmoUserId } : {}),
      ...(deliverable === "video"
        ? {
            contact_method: "whatsapp",
            contact_value: opts.whatsapp || "",
            whatsapp: opts.whatsapp || "",
          }
        : {}),
    }),
  });
  const json = await resp.json().catch(() => ({}));
  if (!resp.ok) {
    const detail = typeof json.detail === "string" ? json.detail : json.error;
    throw new Error(String(detail || "Could not place Numerology order"));
  }
  return {
    order_id: String(json.order_id),
    eta_hours: Number(json.eta_hours) || 24,
    message: String(json.message || "Order received."),
  };
}
