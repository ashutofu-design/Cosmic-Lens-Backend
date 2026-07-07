/**
 * Single-origin preview: app (Expo web) + API on one port for Cloudflare tunnel.
 *   /api/*  → localhost:8080
 *   /*      → localhost:18987 (Metro web)
 */
import http from "node:http";

const PROXY_PORT = Number(process.env.PREVIEW_PROXY_PORT || 19000);
const APP_TARGET = process.env.PREVIEW_APP_TARGET || "http://127.0.0.1:18987";
const API_TARGET = process.env.PREVIEW_API_TARGET || "http://127.0.0.1:8080";

function proxyRequest(req, res, targetBase) {
  const url = new URL(req.url || "/", targetBase);
  const opts = {
    hostname: url.hostname,
    port: url.port || (url.protocol === "https:" ? 443 : 80),
    path: url.pathname + url.search,
    method: req.method,
    headers: { ...req.headers, host: url.host },
  };

  const upstream = http.request(opts, (up) => {
    res.writeHead(up.statusCode || 502, up.headers);
    up.pipe(res);
  });
  upstream.on("error", () => {
    if (!res.headersSent) {
      res.writeHead(502, { "content-type": "text/plain" });
      res.end("Preview proxy: upstream not ready. Wait 30s and refresh.");
    }
  });
  req.pipe(upstream);
}

const server = http.createServer((req, res) => {
  const path = req.url || "/";
  if (path.startsWith("/api")) {
    proxyRequest(req, res, API_TARGET);
  } else {
    proxyRequest(req, res, APP_TARGET);
  }
});

server.listen(PROXY_PORT, "127.0.0.1", () => {
  console.log(`[preview-proxy] :${PROXY_PORT} → app ${APP_TARGET} + api ${API_TARGET}`);
});
