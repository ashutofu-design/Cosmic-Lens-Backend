/**
 * Photo Engine — single room photo classification (Smart Scan upload).
 */
import { API_BASE, apiFetch } from "@/lib/apiConfig";

export type RoomPhotoClassifyResult = {
  ok: boolean;
  valid_room_photo?: boolean;
  suggested_room_type?: string | null;
  detected_room_type?: string | null;
  confidence?: number;
  scan_inconclusive?: boolean;
  features_seen?: string[];
  hint?: string | null;
  error?: string;
  message?: string;
};

export async function classifyRoomPhoto(
  dataUrl: string,
  opts: { userId: number; apiKey: string; lang?: string },
): Promise<RoomPhotoClassifyResult> {
  const resp = await apiFetch(`${API_BASE}/api/room-photo/classify`, {
    method: "POST",
    headers: { "X-API-Key": opts.apiKey },
    body: JSON.stringify({
      user_id: opts.userId,
      lang: opts.lang || "en",
      image_upload: { type: "image", data_url: dataUrl },
    }),
  });
  const text = await resp.text();
  let body: RoomPhotoClassifyResult;
  try {
    body = JSON.parse(text) as RoomPhotoClassifyResult;
  } catch {
    body = {
      ok: false,
      error: `HTTP ${resp.status}`,
      message: text?.slice(0, 200) || "Server returned non-JSON.",
    };
  }
  if (!resp.ok) {
    return {
      ok: false,
      error: body.error || `HTTP ${resp.status}`,
      message: body.message || "Photo Engine could not read this photo.",
    };
  }
  return body;
}
