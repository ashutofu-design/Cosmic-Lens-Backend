/**
 * Metro dev-server middleware — proxy /api/* → hosted API (same origin as Expo web).
 * Browser calls http://localhost:18987/api/... (no separate :18081 proxy port).
 */
const dns = require("node:dns");

dns.setDefaultResultOrder("ipv6first");

let UPSTREAM = (process.env.DEV_API_PROXY_UPSTREAM || "https://admin.coosmic.icu").replace(
  /\/$/,
  "",
);
if (/^http:\/\/admin\.coosmic\.icu/i.test(UPSTREAM)) {
  UPSTREAM = UPSTREAM.replace(/^http:/i, "https:");
}

const AGENT_UPSTREAM = (process.env.DEV_NUMEROLOGY_AGENT_URL || UPSTREAM).replace(/\/$/, "");

const FORWARD_HEADERS = [
  "content-type",
  "accept",
  "authorization",
  "x-api-key",
  "x-user-id",
  "user-agent",
  "bypass-tunnel-reminder",
];

function upstreamHeaders(req) {
  const out = {
    Accept: "application/json",
    "User-Agent": "CosmicLensMobile/1.0",
    "bypass-tunnel-reminder": "true",
  };
  for (const name of FORWARD_HEADERS) {
    const val = req.headers[name];
    if (val) out[name] = val;
  }
  if (!out["content-type"] && !out["Content-Type"] && req.method === "GET") {
    out["Content-Type"] = "application/json";
  }
  return out;
}

function upstreamTimeoutMs(path) {
  if (path.includes("/api/numerology-agent")) return 180000;
  if (path.includes("/api/palm-scan") || path.includes("/api/face-scan") || path.includes("/api/palmistry")) {
    return 120000;
  }
  if (path.includes("/api/palm-reading") || path.includes("/api/face-reading")) return 90000;
  if (path.includes("/api/support")) return 90000;
  if (path.includes("/api/kundli") || path.includes("/api/ask")) return 90000;
  return 30000;
}

function readBody(req) {
  return new Promise((resolve, reject) => {
    const chunks = [];
    req.on("data", (c) => chunks.push(c));
    req.on("end", () => resolve(Buffer.concat(chunks)));
    req.on("error", reject);
  });
}

async function pipeUpstreamResponse(up, res, extraHeaders = {}) {
  const outHeaders = {
    "Content-Type": up.headers.get("content-type") || "application/json",
    ...extraHeaders,
  };
  const cd = up.headers.get("content-disposition");
  if (cd) outHeaders["Content-Disposition"] = cd;

  res.writeHead(up.status, outHeaders);

  if (up.body) {
    const reader = up.body.getReader();
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      res.write(Buffer.from(value));
    }
    res.end();
    return;
  }

  const buf = Buffer.from(await up.arrayBuffer());
  res.end(buf);
}

async function handleApiProxy(req, res) {
  const path = req.url || "/";
  const isAgent = path.includes("/api/numerology-agent");
  const target = `${isAgent ? AGENT_UPSTREAM : UPSTREAM}${path}`;

  let body = Buffer.alloc(0);
  if (req.method !== "GET" && req.method !== "HEAD") {
    body = await readBody(req);
  }

  if (req.method === "POST" && path.includes("/api/ask")) {
    console.log("[metro-proxy]", req.method, path.split("?")[0], "body_bytes=", body.length);
  }

  const up = await fetch(target, {
    method: req.method,
    headers: upstreamHeaders(req),
    body: body.length ? body : undefined,
    signal: AbortSignal.timeout(upstreamTimeoutMs(path)),
  });

  await pipeUpstreamResponse(up, res);
}

function createMetroApiProxyMiddleware() {
  return (req, res, next) => {
    const path = (req.url || "").split("?")[0];
    if (!path.startsWith("/api/")) {
      return next();
    }
    handleApiProxy(req, res).catch((err) => {
      const msg = err instanceof Error ? err.message : String(err);
      console.error("[metro-proxy] FAIL", req.method, path, "→", msg);
      if (!res.headersSent) {
        res.writeHead(502, { "Content-Type": "application/json" });
        res.end(JSON.stringify({ ok: false, error: "metro_proxy_failed", message: msg }));
      }
    });
  };
}

module.exports = { createMetroApiProxyMiddleware, UPSTREAM };
