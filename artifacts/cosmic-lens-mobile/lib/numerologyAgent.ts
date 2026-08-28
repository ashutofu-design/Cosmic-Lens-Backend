/**
 * Numerology Agent client — Try for free uses this, not /api/numerology/pdf.
 * Agent is mounted on Cosmic Lens flask_app (same API as the rest of the app).
 */
import { Platform } from "react-native";
import * as FileSystem from "expo-file-system/legacy";
import * as Sharing from "expo-sharing";

import { API_BASE } from "@/lib/apiConfig";
import { saveLocalReport } from "@/lib/localReports";
import { addUnreadReports } from "@/lib/unreadReportsBadge";

export type AgentReportPage = {
  index: number;
  slot_id: string;
  role: string;
  status: string;
  body: string | null;
  title?: string;
};

export type AgentReportResult = {
  ok: boolean;
  status: string;
  message: string;
  warnings: string[];
  pages: AgentReportPage[];
  narration?: { attempted?: boolean; reason?: string | null; slots?: string[] };
  token_usage?: Record<string, unknown>;
  apiBase?: string;
};

function resultFromPayload(data: Record<string, unknown>, apiBase: string): AgentReportResult {
  const plan = (data.report_plan || {}) as { pages?: AgentReportPage[] };
  const pages = Array.isArray(plan.pages) ? plan.pages : [];
  return {
    ok: data.ok === true,
    status: String(data.status || ""),
    message: String(data.message || ""),
    warnings: Array.isArray(data.warnings) ? data.warnings.map(String) : [],
    pages,
    narration: (data.narration || {}) as AgentReportResult["narration"],
    token_usage: (data.token_usage || {}) as Record<string, unknown>,
    apiBase,
  };
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function uniqueBases(): string[] {
  const out: string[] = [];
  for (const raw of [numerologyAgentBase(), API_BASE.replace(/\/$/, "")]) {
    const base = (raw || "").trim().replace(/\/$/, "");
    if (base && !out.includes(base)) out.push(base);
  }
  return out;
}

export async function generateNumerologyAgentReport(opts: {
  name: string;
  dob: string;
  lang: "english" | "hindi" | "hinglish";
  tob?: string;
  mobile?: string;
  place?: string;
  d1?: Record<string, unknown> | null;
  userId?: number;
  apiKey?: string;
  onProgress?: (percent: number, stage: string) => void;
}): Promise<AgentReportResult> {
  const body = {
    intent: "report" as const,
    name: opts.name,
    dob: opts.dob,
    lang: opts.lang,
    tob: opts.tob,
    mobile: opts.mobile,
    place: opts.place,
    ...(opts.d1 ? { d1: opts.d1 } : {}),
    ...(opts.userId ? { user_id: opts.userId } : {}),
    ...(!opts.d1 && opts.apiKey ? { api_key: opts.apiKey } : {}),
  };
  let displayed = 1;
  let target = 2;
  let stageLabel = "locking_facts";
  let finished = false;

  const push = (percent: number, stage: string) => {
    opts.onProgress?.(percent, stage);
  };

  const smoother = setInterval(() => {
    if (finished) return;
    if (displayed < target) {
      displayed += 1;
      push(displayed, stageLabel);
    }
  }, 420);

  const stopSmoother = () => {
    finished = true;
    clearInterval(smoother);
  };

  push(1, stageLabel);

  const bases = uniqueBases();
  let startResp: Response | null = null;
  let usedBase = bases[0] || "";
  let lastNetworkError: unknown = null;

  for (const base of bases) {
    try {
      const resp = await fetch(`${base}/api/numerology-agent/report/generate/start`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify(body),
      });
      if (resp.status === 404) {
        lastNetworkError = new Error("not_mounted");
        continue;
      }
      startResp = resp;
      usedBase = base;
      break;
    } catch (e) {
      lastNetworkError = e;
    }
  }

  if (!startResp) {
    stopSmoother();
    const aborted = lastNetworkError instanceof Error && lastNetworkError.name === "AbortError";
    throw new Error(
      aborted
        ? "Numerology report timed out. Cosmic Lens API running hai? python flask_app.py"
        : "Numerology Agent API nahi mili. Pehle Cosmic Lens backend start karo: python flask_app.py",
    );
  }

  if (startResp.status === 202) {
    const startData = (await startResp.json().catch(() => ({}))) as { job_id?: string };
    const jobId = String(startData.job_id || "");
    if (!jobId) {
      stopSmoother();
      throw new Error("Agent job id missing");
    }
    const deadline = Date.now() + 40 * 60 * 1000;
    try {
      while (Date.now() < deadline) {
        await sleep(600);
        const st = await fetch(`${usedBase}/api/numerology-agent/report/generate/status/${jobId}`, {
          headers: { Accept: "application/json" },
        });
        const job = (await st.json().catch(() => ({}))) as Record<string, unknown>;
        if (st.status === 404) throw new Error("Agent job missing. API restart hua? Dobara Try for free dabao.");
        const percent = Number(job.percent || 1);
        stageLabel = String(job.stage || "writing");
        target = Math.max(target, Math.min(99, Math.max(1, percent)));
        if (job.done === true) {
          target = 100;
          while (displayed < 100) {
            displayed += 1;
            push(displayed, String(job.stage || "ready"));
            await sleep(28);
          }
          stopSmoother();
          push(100, String(job.stage || "ready"));
          if (job.ok === false) {
            throw new Error(
              String(job.error || "Report nahi bani. Dobara Try for free dabao."),
            );
          }
          const resultPayload = (job.result || {}) as Record<string, unknown>;
          const result = resultFromPayload(resultPayload, usedBase);
          const filled = result.pages.filter((p) => String(p.body || "").trim().length >= 200).length;
          const slots = (result.narration?.slots || []).length;
          if (filled < 10 && slots < 10) {
            const why = `${job.error || ""} ${result.narration?.reason || ""}`.toLowerCase();
            if (why.includes("credit") || why.includes("quota") || why.includes("insufficient")) {
              throw new Error(
                "OpenAI credits khatam hain. platform.openai.com → Billing pe credits add karo, phir Try for free.",
              );
            }
            if (why.includes("429")) {
              throw new Error("OpenAI rate limit. 2 minute wait karke dobara Try for free dabao.");
            }
            throw new Error(
              String(job.error || "10 phases poori nahi likhi gayi. Credits/API check karke dobara Try for free dabao."),
            );
          }
          return result;
        }
      }
      throw new Error(
        "Report abhi likhi ja rahi hai — 10 pages ko 8–12 min lag sakte hain. Dobara Try for free dabao.",
      );
    } finally {
      stopSmoother();
    }
  }

  stopSmoother();
  const data = (await startResp.json().catch(() => ({}))) as Record<string, unknown>;
  if (!startResp.ok) {
    const msg = String(data.message || data.error || `agent HTTP ${startResp.status}`);
    throw new Error(msg);
  }
  opts.onProgress?.(100, "ready");
  return resultFromPayload(data, usedBase);
}

function agentHost(): string {
  if (typeof window !== "undefined") {
    const host = window.location?.hostname || "";
    if (host === "localhost" || host === "127.0.0.1" || host === "") return "127.0.0.1";
    if (/^\d{1,3}(\.\d{1,3}){3}$/.test(host)) return host;
  }
  if (Platform.OS === "android") return "10.0.2.2";
  return "127.0.0.1";
}

export function numerologyAgentBase(): string {
  const override = (process.env.EXPO_PUBLIC_NUMEROLOGY_AGENT_URL || "").trim().replace(/\/$/, "");
  if (override) return override;
  if (typeof window !== "undefined") {
    const host = window.location?.hostname || "";
    if (host === "localhost" || host === "127.0.0.1") {
      return "http://127.0.0.1:8080";
    }
  }
  const api = API_BASE.replace(/\/$/, "");
  if (api) return api;
  return `http://${agentHost()}:8080`;
}

function bytesToBase64(buf: ArrayBuffer): string {
  const bytes = new Uint8Array(buf);
  const CHUNK = 0x4000;
  const parts: string[] = [];
  for (let i = 0; i < bytes.length; i += CHUNK) {
    const slice = bytes.subarray(i, Math.min(i + CHUNK, bytes.length));
    let s = "";
    for (let j = 0; j < slice.length; j++) s += String.fromCharCode(slice[j]);
    parts.push(s);
  }
  if (typeof globalThis.btoa === "function") return globalThis.btoa(parts.join(""));
  return Buffer.from(buf).toString("base64");
}

function triggerBrowserDownload(buf: ArrayBuffer, fileName: string) {
  if (typeof document === "undefined") return;
  try {
    const blob = new Blob([buf], { type: "application/pdf" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = fileName;
    a.target = "_blank";
    a.rel = "noopener";
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 30_000);
  } catch {
    // ignore
  }
}

async function savePdfBuffer(
  buf: ArrayBuffer,
  fileName: string,
  name: string,
): Promise<boolean> {
  triggerBrowserDownload(buf, fileName);
  const b64 = bytesToBase64(buf);
  const dataUrl = `data:application/pdf;base64,${b64}`;
  let saved = false;
  try {
    if (Platform.OS === "web") {
      const entry = await saveLocalReport({
        kind: "numerology",
        title: `${name} — Numerology`,
        subtitle: `Numerology Report · ${new Date().toLocaleDateString()}`,
        sourceUri: dataUrl,
        bytes: buf.byteLength,
      });
      saved = !!entry;
    } else {
      const dest = `${FileSystem.cacheDirectory || FileSystem.documentDirectory || ""}${fileName}`;
      await FileSystem.writeAsStringAsync(dest, b64, {
        encoding: FileSystem.EncodingType.Base64,
      });
      const entry = await saveLocalReport({
        kind: "numerology",
        title: `${name} — Numerology`,
        subtitle: `Numerology Report · ${new Date().toLocaleDateString()}`,
        sourceUri: dest,
        bytes: buf.byteLength,
      });
      saved = !!entry;
      if (await Sharing.isAvailableAsync()) {
        try {
          await Sharing.shareAsync(entry?.localUri || dest, {
            mimeType: "application/pdf",
            dialogTitle: fileName,
            UTI: "com.adobe.pdf",
          });
        } catch {
          // ignore
        }
      }
    }
  } catch {
    saved = false;
  }
  if (saved) {
    try {
      await addUnreadReports(1);
    } catch {
      // ignore
    }
  }
  return saved;
}

/** Cosmic Lens numerology engine PDF — one format, not the separate agent writer. */
export async function generateAndSaveNumerologyEnginePdf(opts: {
  name: string;
  dob: string;
  lang: "english" | "hindi" | "hinglish";
  tob?: string;
  mobile?: string;
  userId?: number;
  apiKey?: string;
  onProgress?: (percent: number, stage: string) => void;
}): Promise<{ fileName: string; saved: boolean }> {
  opts.onProgress?.(12, "engine");
  const fileName = `Numerology_${(opts.name || "report").replace(/[^\w\- ]+/g, "").replace(/\s+/g, "_")}.pdf`;
  const body = {
    name: opts.name,
    dob: opts.dob,
    tob: opts.tob || "12:00",
    lang: opts.lang,
    ...(opts.mobile ? { mobile: opts.mobile } : {}),
  };
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    Accept: "application/pdf",
    ...(opts.userId ? { "X-User-Id": String(opts.userId) } : {}),
    ...(opts.apiKey ? { "X-API-Key": opts.apiKey } : {}),
  };
  let lastError: Error | null = null;
  for (const base of uniqueBases()) {
    try {
      opts.onProgress?.(35, "engine");
      const resp = await fetch(`${base}/api/numerology/pdf`, {
        method: "POST",
        headers,
        body: JSON.stringify(body),
      });
      if (resp.status === 404) {
        lastError = new Error("not_mounted");
        continue;
      }
      if (!resp.ok) {
        const data = (await resp.json().catch(() => ({}))) as { message?: string };
        throw new Error(String(data.message || `Numerology engine HTTP ${resp.status}`));
      }
      const buf = await resp.arrayBuffer();
      if (!buf.byteLength) throw new Error("PDF empty aayi.");
      opts.onProgress?.(90, "engine");
      const saved = await savePdfBuffer(buf, fileName, opts.name);
      opts.onProgress?.(100, "ready");
      return { fileName, saved };
    } catch (e) {
      lastError = e instanceof Error ? e : new Error(String(e));
    }
  }
  throw lastError || new Error("Numerology engine PDF nahi mili.");
}

/** Render PDF, download it, and save into My Reports. */
export async function deliverAndSaveNumerologyAgentPdf(opts: {
  result: AgentReportResult;
  name: string;
  dob: string;
  lang: "english" | "hindi" | "hinglish";
  userId?: number;
  apiKey?: string;
}): Promise<{ fileName: string; saved: boolean }> {
  const base = (opts.result.apiBase || numerologyAgentBase()).replace(/\/$/, "");
  const fileName = `Numerology_${(opts.name || "report").replace(/[^\w\- ]+/g, "").replace(/\s+/g, "_")}.pdf`;
  const resp = await fetch(`${base}/api/numerology-agent/report/deliver`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/pdf",
      ...(opts.userId ? { "X-User-Id": String(opts.userId) } : {}),
      ...(opts.apiKey ? { "X-API-Key": opts.apiKey } : {}),
    },
    body: JSON.stringify({
      name: opts.name,
      dob: opts.dob,
      lang: opts.lang,
      pages: opts.result.pages,
    }),
  });
  if (!resp.ok) {
    throw new Error("PDF download fail hua. Dobara Try for free dabao.");
  }
  const buf = await resp.arrayBuffer();
  if (!buf.byteLength) throw new Error("PDF empty aayi.");

  triggerBrowserDownload(buf, fileName);

  const b64 = bytesToBase64(buf);
  const dataUrl = `data:application/pdf;base64,${b64}`;
  let saved = false;
  try {
    if (Platform.OS === "web") {
      const entry = await saveLocalReport({
        kind: "numerology",
        title: `${opts.name} — Numerology`,
        subtitle: `Numerology Report · ${new Date().toLocaleDateString()}`,
        sourceUri: dataUrl,
        bytes: buf.byteLength,
      });
      saved = !!entry;
    } else {
      const dest = `${FileSystem.cacheDirectory || FileSystem.documentDirectory || ""}${fileName}`;
      await FileSystem.writeAsStringAsync(dest, b64, {
        encoding: FileSystem.EncodingType.Base64,
      });
      const entry = await saveLocalReport({
        kind: "numerology",
        title: `${opts.name} — Numerology`,
        subtitle: `Numerology Report · ${new Date().toLocaleDateString()}`,
        sourceUri: dest,
        bytes: buf.byteLength,
      });
      saved = !!entry;
      if (await Sharing.isAvailableAsync()) {
        try {
          await Sharing.shareAsync(entry?.localUri || dest, {
            mimeType: "application/pdf",
            dialogTitle: fileName,
            UTI: "com.adobe.pdf",
          });
        } catch {
          // ignore
        }
      }
    }
  } catch {
    saved = false;
  }
  if (saved) {
    try {
      await addUnreadReports(1);
    } catch {
      // ignore
    }
  }
  return { fileName, saved };
}

/** Saved D1 only — lagna + planet houses. Never send dasha or other vargas. */
export function compactSavedD1(kundli: unknown): Record<string, unknown> | null {
  if (!kundli || typeof kundli !== "object") return null;
  const raw = kundli as Record<string, unknown>;
  const nested = raw.chart_data;
  const chart =
    nested && typeof nested === "object" && !Array.isArray(nested)
      ? (nested as Record<string, unknown>)
      : raw;
  const planetsIn = Array.isArray(chart.planets) ? chart.planets : [];
  const planets = planetsIn
    .filter((item): item is Record<string, unknown> => !!item && typeof item === "object")
    .map((item) => {
      const houseRaw = item.house;
      const house =
        typeof houseRaw === "number" && Number.isFinite(houseRaw)
          ? houseRaw
          : typeof houseRaw === "string" && houseRaw.trim()
            ? Number.parseInt(houseRaw, 10)
            : null;
      return {
        name: String(item.name || "").trim(),
        sign: String(item.sign || item.rashi || "").trim(),
        house: Number.isFinite(house as number) ? house : null,
        retrograde: Boolean(item.retrograde),
      };
    })
    .filter((p) => p.name);
  const lagna = String(chart.ascendant || chart.lagna || "").trim();
  if (!lagna && planets.length === 0) return null;
  return {
    lagna,
    lagna_deg: chart.ascendantDeg ?? chart.lagna_deg ?? null,
    moon_sign: String(chart.moonSign || chart.moon_sign || "").trim(),
    sun_sign: String(chart.sunSign || chart.sun_sign || "").trim(),
    nakshatra: String(chart.nakshatra || "").trim(),
    planets,
  };
}
