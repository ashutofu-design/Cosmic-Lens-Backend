/**
 * Local API proxy — browser → localhost → admin.coosmic.icu (IPv6/Cloudflare path).
 * Fixes "Failed to fetch" when laptop DNS resolves domain to blocked VPS IPv4.
 */
import dns from "node:dns";
import http from "node:http";

dns.setDefaultResultOrder("ipv6first");

const LOCAL_PORT = Number(process.env.DEV_API_PROXY_PORT || "18081");
// Must be HTTPS — HTTP 301→HTTPS turns POST into GET and Flask returns {"error":"Not found"}.
let UPSTREAM = (process.env.DEV_API_PROXY_UPSTREAM || "https://admin.coosmic.icu").replace(
  /\/$/,
  "",
);
if (/^http:\/\/admin\.coosmic\.icu/i.test(UPSTREAM)) {
  UPSTREAM = UPSTREAM.replace(/^http:/i, "https:");
  console.warn("[api-proxy] Upgraded upstream to HTTPS (HTTP breaks POSTs)");
}

const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET,POST,PUT,PATCH,DELETE,OPTIONS",
  "Access-Control-Allow-Headers":
    "Content-Type,Authorization,Accept,X-Requested-With,X-API-Key,X-User-Id,bypass-tunnel-reminder,User-Agent",
  "Access-Control-Max-Age": "86400",
};

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
  if (!out["content-type"]) out["Content-Type"] = "application/json";
  return out;
}

function upstreamTimeoutMs(path) {
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

async function forward(req, res) {
  if (req.method === "OPTIONS") {
    res.writeHead(204, CORS);
    res.end();
    return;
  }

  const path = req.url || "/";
  const target = `${UPSTREAM}${path}`;

  let body = Buffer.alloc(0);
  if (req.method !== "GET" && req.method !== "HEAD") {
    body = await readBody(req);
  }

  const headers = upstreamHeaders(req);
  const timeoutMs = upstreamTimeoutMs(path);

  try {
    const up = await fetch(target, {
      method: req.method,
      headers,
      body: body.length ? body : undefined,
      signal: AbortSignal.timeout(timeoutMs),
    });

    const text = await up.text();
    const outHeaders = {
      "Content-Type": up.headers.get("content-type") || "application/json",
      ...CORS,
    };
    res.writeHead(up.status, outHeaders);
    res.end(text);
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    console.error("[api-proxy] FAIL", req.method, path, "→", msg);
    if (!res.headersSent) {
      res.writeHead(502, { "Content-Type": "application/json", ...CORS });
      res.end(
        JSON.stringify({
          ok: false,
          error: "proxy_upstream_failed",
          message: msg,
          target,
        }),
      );
    }
  }
}

const server = http.createServer((req, res) => {
  forward(req, res).catch((err) => {
    console.error("[api-proxy] handler error:", err);
    if (!res.headersSent) {
      res.writeHead(500, { "Content-Type": "application/json", ...CORS });
      res.end(JSON.stringify({ ok: false, error: "proxy_internal" }));
    }
  });
});

server.listen(LOCAL_PORT, "127.0.0.1", async () => {
  console.log(`[api-proxy] http://127.0.0.1:${LOCAL_PORT} → ${UPSTREAM}`);
  try {
    const probe = await fetch(`${UPSTREAM}/api/healthz`, {
      signal: AbortSignal.timeout(12000),
    });
    const txt = await probe.text();
    if (probe.ok && txt.includes('"status"')) {
      console.log("[api-proxy] upstream OK ✓");
    } else {
      console.warn("[api-proxy] upstream probe HTTP", probe.status, txt.slice(0, 80));
    }
  } catch (e) {
    console.error(
      "[api-proxy] upstream probe FAILED:",
      e instanceof Error ? e.message : e,
    );
    console.error("[api-proxy] Demo login tab tak fail hoga — WiFi/mobile data check karein");
  }
});

server.on("error", (err) => {
  console.error("[api-proxy] listen failed:", err.message);
  process.exit(1);
});
