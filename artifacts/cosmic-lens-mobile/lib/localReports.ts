/**
 * Local Reports Registry — Phase 2.5.11.22
 *
 * AsyncStorage-backed list of every PDF the user has generated on this
 * device (Kundli Milan, Numerology, AstroVastu Pro, Business Vastu,
 * Face Reading, etc). Each entry tracks a local file URI inside
 * `documentDirectory/reports/` so users can re-open, share, or delete
 * any past report from a single "My Reports" screen — no server calls
 * required.
 *
 * Storage shape:
 *   AsyncStorage["cosmic.localReports.v1"] = JSON.stringify(LocalReport[])
 *
 * Branding: "Powered by Advanced Cosmic Intelligence" — never reveal AI/LLM.
 */
import AsyncStorage from "@react-native-async-storage/async-storage";
import * as FileSystem from "expo-file-system/legacy";
import * as Sharing from "expo-sharing";
import { Platform } from "react-native";

const STORAGE_KEY = "cosmic.localReports.v1";
/** Small pending stubs only — never mixed with base64 PDF blobs (quota-safe). */
const PENDING_STORAGE_KEY = "cosmic.pendingReports.only.v1";
const IS_WEB = Platform.OS === "web";

/** In-memory pending so My Reports updates even if AsyncStorage write is delayed. */
let _memoryPending: LocalReport[] = [];
const _pendingListeners = new Set<(rows: LocalReport[]) => void>();

export function subscribePendingReports(
  fn: (rows: LocalReport[]) => void,
): () => void {
  _pendingListeners.add(fn);
  try {
    fn(_memoryPending.slice());
  } catch {
    /* ignore */
  }
  return () => {
    _pendingListeners.delete(fn);
  };
}

function emitPending(rows: LocalReport[]) {
  _memoryPending = rows;
  _pendingListeners.forEach((fn) => {
    try {
      fn(rows.slice());
    } catch {
      /* ignore */
    }
  });
}

export type LocalReportKind =
  | "milan"
  | "numerology"
  | "astrovastu_pro"
  | "business_vastu"
  | "face_reading"
  | "love_reality"
  | "palmistry"
  | "other";

export interface LocalReport {
  id: string;            // unique — `${kind}_${ts}_${rand}`
  kind: LocalReportKind;
  title: string;         // e.g. "Vikram & Sanya — Kundli Milan"
  subtitle?: string;     // e.g. "21.5/36 · Average Match · 8 May 2026"
  localUri: string;      // file:// URI inside documentDirectory/reports/
  remoteUrl?: string;    // original signed URL (optional, for re-download)
  bytes?: number;        // file size if known
  createdAt: number;     // Date.now()
  /** True when PDF came from server cache (re-download), not fresh generation. */
  restored?: boolean;
  /** pending = ordered, waiting for founder PDF; ready/undefined = openable PDF */
  status?: "pending" | "ready";
  orderId?: string;
  publicOrderId?: string;
  etaLabel?: string;
  deliverable?: "report" | "video";
}

export interface SavePendingLocalReportInput {
  kind: LocalReportKind;
  title: string;
  subtitle?: string;
  orderId?: string;
  publicOrderId?: string;
  etaLabel?: string;
  deliverable?: "report" | "video";
}

export interface SaveLocalReportInput {
  kind: LocalReportKind;
  title: string;
  subtitle?: string;
  /** URI of the just-downloaded PDF (e.g. cacheDirectory/foo.pdf). */
  sourceUri: string;
  remoteUrl?: string;
  restored?: boolean;
  /** File size in bytes when known (e.g. from ArrayBuffer.byteLength). */
  bytes?: number;
}

/** Human-readable PDF size for My Reports — e.g. "245 KB", "1.2 MB". */
export function formatLocalReportSize(bytes?: number): string {
  if (bytes == null || !Number.isFinite(bytes) || bytes <= 0) return "";
  if (bytes < 1024 * 1024) {
    const kb = bytes / 1024;
    return kb < 10 ? `${kb.toFixed(1)} KB` : `${Math.round(kb)} KB`;
  }
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function _bytesFromDataUrl(uri: string): number | undefined {
  const m = String(uri || "").match(/^data:[^;]+;base64,(.+)$/);
  if (!m) return undefined;
  const pad = m[1].endsWith("==") ? 2 : m[1].endsWith("=") ? 1 : 0;
  return Math.max(0, Math.floor((m[1].length * 3) / 4) - pad);
}

const REPORTS_DIR = (FileSystem.documentDirectory || FileSystem.cacheDirectory || "") + "reports/";

async function ensureDir(): Promise<void> {
  if (!REPORTS_DIR) return;
  try {
    const info = await FileSystem.getInfoAsync(REPORTS_DIR);
    if (!info.exists) {
      await FileSystem.makeDirectoryAsync(REPORTS_DIR, { intermediates: true });
    }
  } catch { /* ignore */ }
}

async function readAll(): Promise<LocalReport[]> {
  try {
    const raw = await AsyncStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const arr = JSON.parse(raw);
    return Array.isArray(arr) ? (arr as LocalReport[]) : [];
  } catch {
    return [];
  }
}

async function writeAll(arr: LocalReport[]): Promise<boolean> {
  try {
    await AsyncStorage.setItem(STORAGE_KEY, JSON.stringify(arr));
    return true;
  } catch (e) {
    console.warn("[localReports] writeAll failed (quota?)", e);
    return false;
  }
}

async function readPendingStore(): Promise<LocalReport[]> {
  try {
    const raw = await AsyncStorage.getItem(PENDING_STORAGE_KEY);
    if (!raw) return _memoryPending.slice();
    const arr = JSON.parse(raw);
    const rows = Array.isArray(arr) ? (arr as LocalReport[]).filter((r) => r && r.status === "pending") : [];
    // Merge memory + disk (memory wins on id conflict — freshest write).
    const byId = new Map<string, LocalReport>();
    for (const r of rows) byId.set(r.id, r);
    for (const r of _memoryPending) byId.set(r.id, r);
    return Array.from(byId.values()).sort((a, b) => b.createdAt - a.createdAt);
  } catch {
    return _memoryPending.slice();
  }
}

/** Warm memory from disk once at module load (web/native). */
void (async () => {
  try {
    const raw = await AsyncStorage.getItem(PENDING_STORAGE_KEY);
    if (!raw) return;
    const arr = JSON.parse(raw);
    if (Array.isArray(arr) && arr.length) {
      _memoryPending = (arr as LocalReport[]).filter((r) => r && r.status === "pending");
    }
  } catch {
    /* ignore */
  }
})();

async function writePendingStore(rows: LocalReport[]): Promise<boolean> {
  const clean = rows
    .filter((r) => r && r.status === "pending")
    .slice(0, 50)
    .map((r) => ({
      id: r.id,
      kind: r.kind,
      title: r.title,
      subtitle: r.subtitle,
      localUri: "",
      createdAt: r.createdAt,
      status: "pending" as const,
      orderId: r.orderId,
      publicOrderId: r.publicOrderId,
      etaLabel: r.etaLabel,
      deliverable: r.deliverable,
    }));
  emitPending(clean);
  try {
    await AsyncStorage.setItem(PENDING_STORAGE_KEY, JSON.stringify(clean));
    return true;
  } catch (e) {
    console.warn("[localReports] writePendingStore failed", e);
    // Memory still has it — My Reports can show until refresh from disk fails.
    return false;
  }
}

function idsEqual(a?: string, b?: string): boolean {
  const x = (a || "").trim().toLowerCase();
  const y = (b || "").trim().toLowerCase();
  return !!x && !!y && x === y;
}

function samePendingOrder(r: LocalReport, pub: string, oid: string): boolean {
  if (pub && (idsEqual(r.publicOrderId, pub) || idsEqual(r.orderId, pub))) return true;
  if (oid && (idsEqual(r.orderId, oid) || idsEqual(r.publicOrderId, oid))) return true;
  return false;
}

// Per-process async mutex around the read-modify-write of the registry,
// so concurrent saveLocalReport / deleteLocalReport calls cannot clobber
// each other (last-write-wins would otherwise drop entries).
let _writeLock: Promise<unknown> = Promise.resolve();
function withWriteLock<T>(fn: () => Promise<T>): Promise<T> {
  const next = _writeLock.then(fn, fn);
  // Swallow errors on the chain so one rejection doesn't poison future awaits.
  _writeLock = next.catch(() => undefined);
  return next;
}

function genId(kind: LocalReportKind): string {
  return `${kind}_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
}

/**
 * Placeholder card in My Reports until founder delivers the PDF (or WhatsApp video).
 * Stored in a dedicated lightweight key (not the PDF blob registry) so quota
 * issues cannot silently drop PENDING cards.
 */
export async function savePendingLocalReport(
  input: SavePendingLocalReportInput,
): Promise<LocalReport | null> {
  return withWriteLock(async () => {
    try {
      const pub = (input.publicOrderId || "").trim();
      const oid = (input.orderId || "").trim();
      const pending = await readPendingStore();

      const existing = pending.find((r) => samePendingOrder(r, pub, oid));
      if (existing) {
        emitPending(pending);
        return existing;
      }

      // Also skip if the fat registry already has a ready PDF for this order.
      const readyAll = await readAll();
      const alreadyReady = readyAll.find(
        (r) =>
          r.status !== "pending" &&
          samePendingOrder(r, pub, oid) &&
          !!(r.localUri || r.remoteUrl),
      );
      if (alreadyReady) return alreadyReady;

      const entry: LocalReport = {
        id: genId(input.kind),
        kind: input.kind,
        title: input.title,
        subtitle: input.subtitle,
        localUri: "",
        createdAt: Date.now(),
        status: "pending",
        orderId: oid || undefined,
        publicOrderId: pub || undefined,
        etaLabel: input.etaLabel,
        deliverable: input.deliverable || "report",
      };
      const next = [entry, ...pending.filter((r) => !samePendingOrder(r, pub, oid))];
      await writePendingStore(next);
      // Best-effort: also drop any legacy pending rows from the fat registry.
      try {
        const fat = await readAll();
        const cleaned = fat.filter((r) => r.status !== "pending");
        if (cleaned.length !== fat.length) await writeAll(cleaned);
      } catch {
        /* ignore */
      }
      return entry;
    } catch (e) {
      console.warn("[localReports] savePendingLocalReport failed", e);
      return null;
    }
  });
}

/**
 * Drop a PENDING My Reports card (admin cancelled / deleted order).
 */
export async function removePendingLocalReport(opts: {
  orderId?: string;
  publicOrderId?: string;
}): Promise<boolean> {
  const pub = (opts.publicOrderId || "").trim();
  const oid = (opts.orderId || "").trim();
  if (!pub && !oid) return false;
  return withWriteLock(async () => {
    try {
      const pending = await readPendingStore();
      const next = pending.filter((r) => !samePendingOrder(r, pub, oid));
      if (next.length === pending.length) return false;
      await writePendingStore(next);
      return true;
    } catch {
      return false;
    }
  });
}

/**
 * After a successful /api/my-reports fetch: drop local PENDING cards whose
 * order is no longer on the server pending list (admin deleted / cancelled).
 * Rows without any order id are left alone.
 */
export async function pruneStalePendingLocalReports(
  livePending: Array<{ orderId?: string; publicOrderId?: string }>,
): Promise<number> {
  const livePubs = new Set<string>();
  const liveOids = new Set<string>();
  for (const row of livePending) {
    const pub = (row.publicOrderId || "").trim();
    const oid = (row.orderId || "").trim();
    if (pub) livePubs.add(pub);
    if (oid) liveOids.add(oid);
  }
  return withWriteLock(async () => {
    try {
      const pending = await readPendingStore();
      let removed = 0;
      const keep = pending.filter((r) => {
        const pub = (r.publicOrderId || "").trim();
        const oid = (r.orderId || "").trim();
        if (!pub && !oid) return true;
        const alive =
          (pub && livePubs.has(pub)) || (oid && liveOids.has(oid));
        if (alive) return true;
        removed += 1;
        return false;
      });
      if (removed > 0) await writePendingStore(keep);
      return removed;
    } catch {
      return 0;
    }
  });
}

/**
 * Remove orphan PENDING cards when a ready PDF of the same order/kind already exists
 * (fixes older race where sync created a new row instead of upgrading PENDING).
 */
export async function collapseOrphanPendingReports(): Promise<number> {
  return withWriteLock(async () => {
    try {
      const ready = (await readAll()).filter((r) => r.status !== "pending");
      const pending = await readPendingStore();
      let removed = 0;
      const keep = pending.filter((r) => {
        const orderHit = ready.some((x) =>
          samePendingOrder(x, r.publicOrderId || "", r.orderId || ""),
        );
        if (orderHit) {
          removed += 1;
          return false;
        }
        const kindReady = ready.filter((x) => x.kind === r.kind && x.restored);
        if (kindReady.length > 0 && !r.publicOrderId && !r.orderId) {
          removed += 1;
          return false;
        }
        return true;
      });
      if (removed > 0) await writePendingStore(keep);
      return removed;
    } catch {
      return 0;
    }
  });
}

/** Upgrade a pending stub to a real PDF entry (same My Reports card — never duplicate). */
export async function fulfillPendingLocalReport(opts: {
  publicOrderId?: string;
  orderId?: string;
  kind: LocalReportKind;
  title: string;
  subtitle?: string;
  sourceUri: string;
  remoteUrl?: string;
  bytes?: number;
}): Promise<LocalReport | null> {
  const pub = (opts.publicOrderId || "").trim();
  const oid = (opts.orderId || "").trim();
  const remote = (opts.remoteUrl || "").trim();

  const idsEqual = (a?: string, b?: string) => {
    const x = (a || "").trim();
    const y = (b || "").trim();
    if (!x || !y) return false;
    return x.toLowerCase() === y.toLowerCase();
  };

  const matchesOrder = (r: LocalReport) => {
    if (pub && (idsEqual(r.publicOrderId, pub) || idsEqual(r.orderId, pub))) return true;
    if (oid && (idsEqual(r.orderId, oid) || idsEqual(r.publicOrderId, oid))) return true;
    const sub = (r.subtitle || "").toUpperCase();
    if (pub && sub.includes(pub.toUpperCase())) return true;
    if (oid.length >= 8 && sub.includes(oid.slice(0, 8).toUpperCase())) return true;
    return false;
  };

  /**
   * Exact order match first. Only fall back to same-kind pending when the
   * incoming PDF has no order ids, or the pending stub itself has none —
   * never steal a different order's PENDING card.
   */
  const findPendingIndex = (all: LocalReport[]): number => {
    const byOrder = all.findIndex((r) => r.status === "pending" && matchesOrder(r));
    if (byOrder >= 0) return byOrder;
    if (!pub && !oid) {
      return all.findIndex((r) => r.status === "pending" && r.kind === opts.kind);
    }
    return all.findIndex(
      (r) =>
        r.status === "pending" &&
        r.kind === opts.kind &&
        !r.publicOrderId &&
        !r.orderId,
    );
  };

  const applyReady = (prev: LocalReport, localUri: string, bytes?: number): LocalReport => ({
    ...prev,
    kind: opts.kind || prev.kind,
    title: opts.title || prev.title,
    subtitle:
      opts.subtitle ||
      prev.subtitle ||
      (pub ? `Order ${pub}` : oid ? `Order ${oid.slice(0, 8).toUpperCase()}` : prev.subtitle),
    localUri,
    remoteUrl: opts.remoteUrl || prev.remoteUrl,
    bytes,
    status: "ready",
    restored: true,
    publicOrderId: prev.publicOrderId || pub || undefined,
    orderId: prev.orderId || oid || undefined,
  });

  const materializeUri = async (prevId: string): Promise<{ uri: string; bytes?: number } | null> => {
    if (IS_WEB) {
      return {
        uri: opts.sourceUri,
        bytes: opts.bytes ?? _bytesFromDataUrl(opts.sourceUri),
      };
    }
    if (!REPORTS_DIR) return null;
    await ensureDir();
    const safeBase =
      opts.title
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, "_")
        .replace(/^_+|_+$/g, "")
        .slice(0, 40) || "report";
    const dest = `${REPORTS_DIR}${opts.kind}_${safeBase}_${prevId}.pdf`;
    let finalUri = "";
    let bytes: number | undefined = opts.bytes;
    try {
      await FileSystem.copyAsync({ from: opts.sourceUri, to: dest });
    } catch {
      /* try source */
    }
    try {
      const di = await FileSystem.getInfoAsync(dest);
      if (di.exists) {
        finalUri = dest;
        if (bytes == null && typeof (di as { size?: number }).size === "number") {
          bytes = (di as { size: number }).size;
        }
      }
    } catch {
      /* ignore */
    }
    if (!finalUri) {
      try {
        const si = await FileSystem.getInfoAsync(opts.sourceUri);
        if (si.exists) {
          finalUri = opts.sourceUri;
          if (bytes == null && typeof (si as { size?: number }).size === "number") {
            bytes = (si as { size: number }).size;
          }
        }
      } catch {
        /* ignore */
      }
    }
    if (!finalUri) return null;
    return { uri: finalUri, bytes };
  };

  return withWriteLock(async () => {
    try {
      const all = (await readAll()).filter((r) => r.status !== "pending");
      const pending = await readPendingStore();

      // Already delivered onto this card (or parallel sync) — do not add a second row.
      const existingReady = all.find(
        (r) =>
          matchesOrder(r) ||
          (remote && r.remoteUrl === remote) ||
          (r.kind === opts.kind &&
            remote &&
            (r.remoteUrl || "").includes(remote.split("/").pop() || "___")),
      );
      if (existingReady && existingReady.localUri) {
        // Drop matching pending stubs if any remain.
        const rest = pending.filter((r) => !matchesOrder(r));
        if (rest.length !== pending.length) await writePendingStore(rest);
        return existingReady;
      }

      const idx = findPendingIndex(pending);
      let prev: LocalReport | null = idx >= 0 ? pending[idx] : null;
      const file = await materializeUri(prev?.id || genId(opts.kind));
      if (!file) return null;

      const next = applyReady(
        prev || {
          id: genId(opts.kind),
          kind: opts.kind,
          title: opts.title,
          subtitle: opts.subtitle,
          localUri: "",
          createdAt: Date.now(),
          status: "pending",
          publicOrderId: pub || undefined,
          orderId: oid || undefined,
        },
        file.uri,
        file.bytes,
      );

      const restPending = pending.filter((r, i) => {
        if (idx >= 0 && i === idx) return false;
        if (matchesOrder(r)) return false;
        return true;
      });
      await writePendingStore(restPending);

      const readyRows = [next, ...all.filter((r) => !matchesOrder(r))];
      const ok = await writeAll(readyRows);
      if (!ok && IS_WEB) {
        // Quota — try again after dropping oldest data: URL blobs.
        const slim = readyRows.map((r, i) =>
          i === 0 || !String(r.localUri || "").startsWith("data:")
            ? r
            : { ...r, localUri: r.remoteUrl || "", restored: true },
        );
        await writeAll(slim);
      }
      return next;
    } catch {
      return null;
    }
  });
}

/**
 * Copy the just-downloaded PDF into the persistent reports/ directory and
 * register it. Safe to call from any platform — silently no-ops on web
 * (where FileSystem APIs are unavailable). Never throws.
 */
export async function saveLocalReport(
  input: SaveLocalReportInput,
): Promise<LocalReport | null> {
  // WEB path (Phase 2.5.11.24-fix7): browsers don't expose a writable file
  // system through expo-file-system, but AsyncStorage is backed by
  // localStorage on web — so we store the PDF as a base64 `data:` URL right
  // in the registry entry's `localUri`. listLocalReports/openLocalReport
  // both detect the data:/blob: scheme and skip FileSystem.getInfoAsync.
  // Caller passes input.sourceUri = "data:application/pdf;base64,…" on web.
  if (IS_WEB) {
    return withWriteLock(async () => {
      try {
        const id = genId(input.kind);
        const entry: LocalReport = {
          id,
          kind: input.kind,
          title: input.title,
          subtitle: input.subtitle,
          localUri: input.sourceUri,
          remoteUrl: input.remoteUrl,
          bytes: input.bytes ?? _bytesFromDataUrl(input.sourceUri),
          createdAt: Date.now(),
          ...(input.restored ? { restored: true } : {}),
        };
        const all = await readAll();
        all.unshift(entry);
        await writeAll(all);
        return entry;
      } catch {
        return null;
      }
    });
  }
  if (!REPORTS_DIR) return null;
  return withWriteLock(async () => {
    try {
      await ensureDir();
      const id = genId(input.kind);
      const ext = ".pdf";
      const safeBase = input.title
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, "_")
        .replace(/^_+|_+$/g, "")
        .slice(0, 40) || "report";
      const fileName = `${input.kind}_${safeBase}_${id}${ext}`;
      const dest = REPORTS_DIR + fileName;

      let copyOk = false;
      try {
        await FileSystem.copyAsync({ from: input.sourceUri, to: dest });
        copyOk = true;
      } catch { /* fall back to sourceUri below */ }

      // Decide which URI we trust. We MUST verify it actually exists on disk;
      // otherwise we'd register a broken entry that silently 404s on Open.
      let finalUri = "";
      let bytes: number | undefined = input.bytes;
      try {
        const di = await FileSystem.getInfoAsync(dest);
        if (di.exists) {
          finalUri = dest;
          if (bytes == null && typeof (di as any).size === "number") bytes = (di as any).size;
        }
      } catch { /* ignore */ }
      if (!finalUri) {
        try {
          const si = await FileSystem.getInfoAsync(input.sourceUri);
          if (si.exists) {
            finalUri = input.sourceUri;
            if (bytes == null && typeof (si as any).size === "number") bytes = (si as any).size;
          }
        } catch { /* ignore */ }
      }
      if (!finalUri) {
        // Neither destination nor source readable — refuse to register a
        // broken entry. User still got the share-sheet from the calling
        // flow, so this is safe to skip silently.
        return null;
      }

      // Best-effort cleanup: if copy succeeded AND source lives in cacheDir,
      // delete the original to avoid disk bloat (cache copies aren't needed).
      if (copyOk && input.sourceUri !== dest) {
        const cacheDir = FileSystem.cacheDirectory || "";
        if (cacheDir && input.sourceUri.startsWith(cacheDir)) {
          try {
            await FileSystem.deleteAsync(input.sourceUri, { idempotent: true });
          } catch { /* ignore */ }
        }
      }

      const entry: LocalReport = {
        id,
        kind: input.kind,
        title: input.title,
        subtitle: input.subtitle,
        localUri: finalUri,
        remoteUrl: input.remoteUrl,
        bytes,
        createdAt: Date.now(),
        ...(input.restored ? { restored: true } : {}),
      };
      const all = await readAll();
      all.unshift(entry); // newest first
      await writeAll(all);
      return entry;
    } catch {
      return null;
    }
  });
}

/**
 * List saved reports. Merges PENDING stubs (lightweight store) with ready PDFs.
 * Self-heals by silently pruning ready entries whose backing file disappeared.
 */
export async function listLocalReports(): Promise<LocalReport[]> {
  const pending = await readPendingStore();
  // Migrate any legacy pending rows still stuck in the fat registry.
  const fat = await readAll();
  const legacyPending = fat.filter((r) => r.status === "pending");
  if (legacyPending.length) {
    const mergedPending = [...pending];
    for (const row of legacyPending) {
      if (!mergedPending.some((p) => samePendingOrder(p, row.publicOrderId || "", row.orderId || ""))) {
        mergedPending.push({ ...row, localUri: "", status: "pending" });
      }
    }
    await writePendingStore(mergedPending);
    await writeAll(fat.filter((r) => r.status !== "pending"));
  }

  const pendingNow = await readPendingStore();
  const readySource = (await readAll()).filter((r) => r.status !== "pending");

  if (readySource.length === 0) {
    return [...pendingNow].sort((a, b) => b.createdAt - a.createdAt);
  }

  const survivors: LocalReport[] = [];
  let pruned = false;
  let enriched = false;
  for (const r of readySource) {
    if (IS_WEB) {
      const size = r.bytes ?? _bytesFromDataUrl(r.localUri);
      if (size != null && r.bytes !== size) {
        survivors.push({ ...r, bytes: size, status: r.status || "ready" });
        enriched = true;
      } else {
        survivors.push({ ...r, status: r.status || "ready" });
      }
      continue;
    }
    try {
      const info = await FileSystem.getInfoAsync(r.localUri);
      if (info.exists) {
        const diskSize = typeof (info as { size?: number }).size === "number"
          ? (info as { size: number }).size
          : undefined;
        if (diskSize != null && r.bytes !== diskSize) {
          survivors.push({ ...r, bytes: diskSize, status: r.status || "ready" });
          enriched = true;
        } else {
          survivors.push({ ...r, status: r.status || "ready" });
        }
      } else if (r.remoteUrl) {
        // Keep metadata so sync can re-download; don't drop the card.
        survivors.push({ ...r, status: r.status || "ready" });
      } else {
        pruned = true;
      }
    } catch {
      survivors.push({ ...r, status: r.status || "ready" });
    }
  }
  if (pruned || enriched) {
    await withWriteLock(async () => {
      const fresh = (await readAll()).filter((r) => r.status !== "pending");
      const liveIds = new Set(survivors.map((r) => r.id));
      const newest = survivors[0]?.createdAt ?? 0;
      const survivorById = new Map(survivors.map((r) => [r.id, r]));
      const merged = fresh
        .filter((r) => liveIds.has(r.id) || r.createdAt > newest)
        .map((r) => survivorById.get(r.id) ?? r);
      await writeAll(merged);
    });
  }

  return [...pendingNow, ...survivors].sort((a, b) => b.createdAt - a.createdAt);
}

/** Remove saved reports whose title starts with prefix (e.g. same couple PDF). */
export async function deleteLocalReportsByTitlePrefix(prefix: string): Promise<number> {
  const needle = (prefix || "").trim().toLowerCase();
  if (!needle) return 0;
  return withWriteLock(async () => {
    try {
      const all = await readAll();
      const keep: LocalReport[] = [];
      let removed = 0;
      for (const entry of all) {
        if ((entry.title || "").toLowerCase().startsWith(needle)) {
          if (!IS_WEB) {
            try {
              await FileSystem.deleteAsync(entry.localUri, { idempotent: true });
            } catch { /* ignore */ }
          }
          removed += 1;
        } else {
          keep.push(entry);
        }
      }
      if (removed > 0) await writeAll(keep);
      return removed;
    } catch {
      return 0;
    }
  });
}

/** Delete a report (file + registry entry). Never throws. */
export async function deleteLocalReport(id: string): Promise<boolean> {
  return withWriteLock(async () => {
    try {
      const pending = await readPendingStore();
      const pIdx = pending.findIndex((r) => r.id === id);
      if (pIdx >= 0) {
        const next = pending.slice();
        next.splice(pIdx, 1);
        await writePendingStore(next);
        return true;
      }

      const all = await readAll();
      const idx = all.findIndex((r) => r.id === id);
      if (idx < 0) return false;
      const entry = all[idx];
      // Web: nothing to delete on disk; localStorage entry removal is enough.
      if (!IS_WEB) {
        try {
          await FileSystem.deleteAsync(entry.localUri, { idempotent: true });
        } catch { /* ignore */ }
      }
      all.splice(idx, 1);
      await writeAll(all);
      return true;
    } catch {
      return false;
    }
  });
}

/**
 * On web: trigger an in-browser <a download> click from the embedded
 * data:/blob: URL. On native: open the OS share sheet.
 */
function _safeFileName(title: string, kind: LocalReportKind): string {
  const safe = (title || kind).toLowerCase().replace(/[^a-z0-9]+/g, "_").replace(/^_+|_+$/g, "").slice(0, 60) || "report";
  return `${safe}.pdf`;
}

function _webDownload(report: LocalReport): void {
  try {
    if (typeof document === "undefined") return;
    const a = document.createElement("a");
    a.href = report.localUri;
    a.download = _safeFileName(report.title, report.kind);
    document.body.appendChild(a);
    a.click();
    a.remove();
  } catch { /* ignore */ }
}

/** Open the OS share sheet for a saved report. */
export async function shareLocalReport(report: LocalReport): Promise<void> {
  if (IS_WEB) { _webDownload(report); return; }
  try {
    const can = await Sharing.isAvailableAsync();
    if (!can) return;
    await Sharing.shareAsync(report.localUri, {
      mimeType: "application/pdf",
      dialogTitle: report.title,
      UTI: "com.adobe.pdf",
    });
  } catch { /* ignore */ }
}

/** Re-open a saved report via the OS share sheet (lets user view/save). */
export async function openLocalReport(report: LocalReport): Promise<void> {
  if (IS_WEB) { _webDownload(report); return; }
  await shareLocalReport(report);
}

/** Clear device My Reports on logout — PDFs are per-account, not per-device shared. */
export async function clearAllLocalReports(): Promise<void> {
  try {
    const rows = await readAll();
    if (!IS_WEB && REPORTS_DIR) {
      for (const row of rows) {
        const uri = row.localUri || "";
        if (uri.startsWith("file://")) {
          try {
            await FileSystem.deleteAsync(uri, { idempotent: true });
          } catch {
            /* ignore */
          }
        }
      }
    }
    await AsyncStorage.removeItem(STORAGE_KEY);
    await AsyncStorage.removeItem(PENDING_STORAGE_KEY);
    emitPending([]);
  } catch {
    /* ignore */
  }
}
