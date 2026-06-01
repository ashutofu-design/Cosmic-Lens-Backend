/** Set full-height layout on web without inline CSS in +html (avoids lightningcss on Windows). */
export function applyWebDocumentHeight(): void {
  if (typeof document === "undefined") return;
  const html = document.documentElement;
  const body = document.body;
  const root = document.getElementById("root");
  for (const el of [html, body, root]) {
    if (!el) continue;
    el.style.width = "100%";
    el.style.height = "100%";
    el.style.margin = "0";
    el.style.padding = "0";
  }
  if (body) {
    body.style.backgroundColor = "#0B1220";
    body.style.overflow = "auto";
  }
}
