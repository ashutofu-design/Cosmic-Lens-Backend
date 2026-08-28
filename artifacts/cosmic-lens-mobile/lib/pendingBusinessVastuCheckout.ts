/**
 * In-memory pending Business Vastu checkout (photos/PDF too large for route params).
 */

export type BusinessVastuType = "shop" | "office" | "factory";

export type BusinessVastuSubmitPayload = {
  business_type: BusinessVastuType;
  property_name: string;
  urgent: boolean;
  room_photos?: Array<{
    room_type: string;
    image_data_url: string;
    heading_deg?: number;
  }>;
  floor_plan_upload?: {
    type: string;
    data_url?: string;
    base64?: string;
    filename?: string;
    north_at?: string;
  };
};

export type PendingBusinessVastuCheckout = {
  params: BusinessVastuSubmitPayload;
  purchaseId?: number;
  paidReady?: boolean;
  /** Local PDF URI — base64 attached after Razorpay, not during create-order. */
  planFileUri?: string;
};

let _pending: PendingBusinessVastuCheckout | null = null;

export function setPendingBusinessVastuCheckout(v: PendingBusinessVastuCheckout): void {
  _pending = { ...v, paidReady: false };
}

export function getPendingBusinessVastuCheckout(): PendingBusinessVastuCheckout | null {
  return _pending;
}

export function markPendingBusinessVastuPaidReady(): void {
  if (_pending) _pending = { ..._pending, paidReady: true };
}

export function clearPendingBusinessVastuCheckout(): void {
  _pending = null;
}

/** Read PDF bytes from local URI into payload (call after payment / before submit-order). */
export async function hydrateBusinessVastuPdfPayload(
  payload: BusinessVastuSubmitPayload,
  planFileUri?: string | null,
): Promise<BusinessVastuSubmitPayload> {
  const fp = payload.floor_plan_upload;
  if (!fp) return payload;
  if (fp.base64 || fp.data_url) return payload;
  if (!planFileUri) return payload;

  const FileSystem = await import("expo-file-system/legacy");
  const encoding =
    (FileSystem as { EncodingType?: { Base64: string } }).EncodingType?.Base64 ?? "base64";
  const b64 = await FileSystem.readAsStringAsync(planFileUri, {
    encoding: encoding as any,
  });
  if (!b64 || b64.length < 32) {
    throw new Error("PDF could not be read. Please pick the file again.");
  }
  return {
    ...payload,
    floor_plan_upload: {
      ...fp,
      base64: b64,
    },
  };
}
