#!/usr/bin/env node
/**
 * Export Love Reality Pro dashboard to A4 PDF via Puppeteer.
 *
 *   pnpm build && pnpm export:pdf
 *   pnpm export:pdf -- --out ./Love_Reality_Pro.pdf
 */
import { createServer } from "node:http";
import { readFileSync, existsSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import puppeteer from "puppeteer";

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = join(__dirname, "..");
const dist = join(root, "dist");
const outArg = process.argv.indexOf("--out");
const outPath = resolve(outArg >= 0 ? process.argv[outArg + 1] : join(root, "Love_Reality_Pro.pdf"));

function serveStatic(port: number): Promise<{ close: () => void; url: string }> {
  return new Promise((resolvePromise) => {
    const server = createServer((req, res) => {
      let path = req.url?.split("?")[0] ?? "/";
      if (path === "/") path = "/index.html";
      const file = join(dist, path.replace(/^\//, ""));
      if (!existsSync(file)) {
        res.writeHead(404);
        res.end("Not found");
        return;
      }
      const ext = file.split(".").pop() ?? "";
      const types: Record<string, string> = {
        html: "text/html",
        js: "application/javascript",
        css: "text/css",
        svg: "image/svg+xml",
        png: "image/png",
        woff2: "font/woff2",
      };
      res.writeHead(200, { "Content-Type": types[ext] ?? "application/octet-stream" });
      res.end(readFileSync(file));
    });
    server.listen(port, "127.0.0.1", () => {
      resolvePromise({
        url: `http://127.0.0.1:${port}/`,
        close: () => server.close(),
      });
    });
  });
}

async function main() {
  if (!existsSync(join(dist, "index.html"))) {
    console.error("Run `pnpm build` first.");
    process.exit(1);
  }

  const port = 5199;
  const srv = await serveStatic(port);
  const browser = await puppeteer.launch({ headless: true, args: ["--no-sandbox"] });
  try {
    const page = await browser.newPage();
    await page.goto(srv.url, { waitUntil: "networkidle0", timeout: 60000 });
    await page.waitForSelector("#love-reality-pro-page");
    await page.pdf({
      path: outPath,
      format: "A4",
      printBackground: true,
      preferCSSPageSize: true,
      margin: { top: 0, right: 0, bottom: 0, left: 0 },
    });
    console.log(`OK: wrote ${outPath}`);
  } finally {
    await browser.close();
    srv.close();
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
