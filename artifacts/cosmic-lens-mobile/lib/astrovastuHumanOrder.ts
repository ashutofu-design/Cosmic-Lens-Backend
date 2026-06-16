import { Alert } from "react-native";

import { API_BASE } from "@/lib/apiConfig";
import {
  clearPendingAstrovastuRoomUpload,
  getPendingAstrovastuRoomUpload,
} from "@/lib/pendingAstrovastuRoomUpload";

export async function submitAstrovastuRoomHumanOrder(opts: {
  user: { id: number; api_key: string };
  purchaseId: number;
}): Promise<boolean> {
  const pending = getPendingAstrovastuRoomUpload();
  if (!pending) {
    Alert.alert("Upload missing", "Please pick your room photo again.");
    return false;
  }

  try {
    const resp = await fetch(`${API_BASE}/api/astrovastu/room-upload-order`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-API-Key": opts.user.api_key,
      },
      body: JSON.stringify({
        user_id: opts.user.id,
        purchase_id: opts.purchaseId,
        room_type: pending.room_type,
        direction: pending.direction,
        data_url: pending.data_url,
        image_data_url: pending.data_url,
      }),
    });
    const body = await resp.json();
    if (!resp.ok) {
      Alert.alert(
        "Could not submit",
        body?.message || body?.error || "Please try again or contact support.",
      );
      return false;
    }

    clearPendingAstrovastuRoomUpload();
    Alert.alert("Done", "Your report will appear in My Reports soon.");
    return true;
  } catch (e: unknown) {
    Alert.alert("Network error", e instanceof Error ? e.message : "Try again.");
    return false;
  }
}
