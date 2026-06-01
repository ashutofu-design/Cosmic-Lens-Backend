/**
 * Floor-plan Photo Engine preview — runs right after upload (before full Vastu scan).
 */
import { API_BASE, apiFetch } from "@/lib/apiConfig";

export type FloorPlanPreviewRoom = { room_type: string; direction: string };

export type FloorPlanPreviewResult = {
  ok: boolean;
  rooms_count?: number;
  rooms?: FloorPlanPreviewRoom[];
  detected_plan_kind?: "home" | "shop" | "office" | "factory" | "unclear";
  confidence?: number;
  room_types?: string[];
  plan_kind_mismatch?: boolean;
  mismatch_message?: string;
  suggested_north_at?: string;
  plan_north_points_to?: string;
  main_entrance?: string;
  structural_notes?: string[];
  error?: string;
  message?: string;
};

export type FloorPlanUploadPayload = {
  type: "image" | "pdf";
  data_url?: string;
  base64?: string;
  filename?: string;
  north_at?: string;
  plan_kind?: string;
};

export async function previewFloorPlanUpload(
  upload: FloorPlanUploadPayload,
  opts: {
    userId: number;
    apiKey: string;
    lang?: string;
    planKind?: string;
  },
): Promise<FloorPlanPreviewResult> {
  const resp = await apiFetch(`${API_BASE}/api/floor-plan/preview`, {
    method: "POST",
    headers: {
      "X-API-Key": opts.apiKey,
    },
    body: JSON.stringify({
      user_id: opts.userId,
      lang: opts.lang || "en",
      plan_kind: opts.planKind,
      floor_plan_upload: upload,
    }),
  });
  const text = await resp.text();
  let body: FloorPlanPreviewResult;
  try {
    body = JSON.parse(text) as FloorPlanPreviewResult;
  } catch {
    body = {
      ok: false,
      error: `HTTP ${resp.status}`,
      message: text?.slice(0, 200) || "Server returned non-JSON (check API URL / backend deploy).",
    };
  }
  if (!resp.ok) {
    return {
      ok: false,
      error: body.error || `HTTP ${resp.status}`,
      message: body.message || "Photo Engine could not read this upload.",
    };
  }
  return body;
}

/** Client-side mismatch when preview already returned detected_plan_kind. */
export function isPlanKindMismatch(
  selected: string | undefined,
  detected: string | undefined,
): boolean {
  if (!selected || !detected || detected === "unclear") return false;
  return selected !== detected;
}
