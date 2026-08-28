import { Alert, Platform } from "react-native";

import { API_BASE } from "@/lib/apiConfig";
import { STANDARD_DELIVERY_ETA } from "@/lib/deliverySla";
import { registerPendingMyReport } from "@/lib/registerPendingMyReport";
import {
  clearPendingAstrovastuRoomUpload,
  getPendingAstrovastuRoomUpload,
} from "@/lib/pendingAstrovastuRoomUpload";

/** Alert.alert is a silent no-op on web — use window.alert there instead. */
function notify(title: string, message: string): void {
  if (Platform.OS === "web") {
    try {
      window.alert(`${title}\n\n${message}`);
    } catch {
      console.warn(`[astrovastu] ${title}: ${message}`);
    }
    return;
  }
  Alert.alert(title, message);
}

export async function submitAstrovastuRoomHumanOrder(opts: {
  user: { id: number; api_key: string };
  purchaseId: number;
  urgent?: boolean;
}): Promise<boolean> {
  const pending = getPendingAstrovastuRoomUpload();
  if (!pending) {
    notify("Upload missing", "Please pick your room photo again.");
    return false;
  }

  try {
    const resp = await fetch(`${API_BASE}/api/astrovastu/room-upload-order`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-API-Key": opts.user.api_key,
      },
      // Send the base64 photo once only — duplicating it doubled the request
      // size and pushed uploads past the server body limit.
      // Omit purchase_id when 0 (payment-bypass mode) so old servers don't
      // treat it as a failed paid submit.
      body: JSON.stringify({
        user_id: opts.user.id,
        ...(opts.purchaseId > 0 ? { purchase_id: opts.purchaseId } : {}),
        room_type: pending.room_type,
        direction: pending.direction,
        data_url: pending.data_url,
        payment_bypassed: opts.purchaseId <= 0,
        urgent: !!opts.urgent,
      }),
    });
    if (resp.status === 413) {
      notify(
        "Photo too large",
        "Yeh photo bahut badi hai. Thodi chhoti/compressed photo choose karke dobara try karein.",
      );
      return false;
    }
    const body = await resp.json().catch(() => ({} as Record<string, unknown>));
    if (!resp.ok) {
      notify(
        "Could not submit",
        String(
          (body as { message?: string })?.message ||
            (body as { error?: string })?.error ||
            "Please try again or contact support.",
        ) + ` (HTTP ${resp.status})`,
      );
      return false;
    }

    const orderId = String((body as { order_id?: string }).order_id || "").trim();
    const displayOid = orderId.slice(0, 8).toUpperCase();
    const room = String(pending.room_type || "Room").trim() || "Room";
    try {
      await registerPendingMyReport(opts.user.id, {
        kind: "astrovastu_pro",
        title: `${room} — AstroVastu Report`,
        subtitle: displayOid ? `Order ${displayOid}` : "Preparing…",
        orderId: orderId || undefined,
        publicOrderId: displayOid || undefined,
        etaLabel: opts.urgent
          ? "⚡ Priority — within 12 hours"
          : `📦 Standard — ${STANDARD_DELIVERY_ETA}`,
        deliverable: "report",
      });
    } catch {
      /* ignore */
    }

    clearPendingAstrovastuRoomUpload();
    // Success UI is the caller's job (animated OrderSuccessModal) — no alert here.
    return true;
  } catch (e: unknown) {
    notify("Network error", e instanceof Error ? e.message : "Try again.");
    return false;
  }
}
