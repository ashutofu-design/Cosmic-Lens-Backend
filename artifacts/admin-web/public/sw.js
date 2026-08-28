/* Cosmic Admin service worker — push notifications with Accept / Reject. */

self.addEventListener("install", () => {
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(self.clients.claim());
});

self.addEventListener("push", (event) => {
  let data = {};
  try {
    data = event.data ? event.data.json() : {};
  } catch {
    data = { title: "Cosmic Admin", body: event.data ? event.data.text() : "" };
  }

  const isV3 = data.kind === "v3_request" && data.session_id;
  const options = {
    body: data.body || "",
    tag: data.tag || "cosmic-admin",
    renotify: true,
    requireInteraction: true,
    vibrate: [300, 120, 300, 120, 500],
    data: {
      kind: data.kind || "",
      session_id: data.session_id || "",
      admin_token: data.admin_token || "",
      tab: data.tab || "",
      order_id: data.order_id || "",
    },
    actions: isV3
      ? [
          { action: "accept", title: "✅ Accept" },
          { action: "reject", title: "❌ Reject" },
        ]
      : data.kind === "lifemap_order"
        ? [{ action: "open", title: "✅ Accept Order" }]
        : [],
  };

  event.waitUntil(
    self.registration.showNotification(data.title || "Cosmic Admin", options),
  );
});

async function v3Action(sessionId, token, action) {
  try {
    const res = await fetch(
      `/api/admin/cosmic-intelligence-v3-sessions/${encodeURIComponent(sessionId)}/${action}`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Admin-Token": token,
        },
        body: "{}",
      },
    );
    await self.registration.showNotification(
      res.ok
        ? action === "accept"
          ? "✅ Accepted — live chat started"
          : "❌ Rejected"
        : "⚠️ Action failed — open admin panel",
      {
        body: res.ok
          ? action === "accept"
            ? "Timer chal raha hai. Admin panel kholo aur chat karo."
            : "Request reject ho gayi."
          : `HTTP ${res.status}`,
        tag: `v3-result-${sessionId}`,
        vibrate: [200],
      },
    );
  } catch {
    await self.registration.showNotification("⚠️ Network error", {
      body: "Admin panel khol kar Accept/Reject karo.",
      tag: `v3-result-${sessionId}`,
    });
  }
}

async function openAdmin(tab) {
  const path = tab ? `/admin?tab=${encodeURIComponent(tab)}` : "/admin";
  const wins = await self.clients.matchAll({ type: "window", includeUncontrolled: true });
  for (const win of wins) {
    if ("focus" in win) {
      await win.focus();
      try {
        if (tab) win.postMessage({ type: "admin_goto", tab });
      } catch {
        /* ignore */
      }
      return;
    }
  }
  await self.clients.openWindow(path);
}

self.addEventListener("notificationclick", (event) => {
  const {
    kind,
    session_id: sessionId,
    admin_token: token,
    tab,
  } = event.notification.data || {};
  const action = event.action;
  event.notification.close();

  if (kind === "v3_request" && sessionId && token && (action === "accept" || action === "reject")) {
    event.waitUntil(v3Action(sessionId, token, action));
    return;
  }
  const goTab = kind === "lifemap_order" ? "lifemap" : tab || "";
  event.waitUntil(openAdmin(goTab));
});
