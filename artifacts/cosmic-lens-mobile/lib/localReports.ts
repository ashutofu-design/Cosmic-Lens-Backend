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

const STORAGE_KEY = "cosmic.localReports.v1";

export type LocalReportKind =
  | "milan"
  | "numerology"
  | "astrovastu_pro"
  | "business_vastu"
  | "face_reading"
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
}

export interface SaveLocalReportInput {
  kind: LocalReportKind;
  title: string;
  subtitle?: string;
  /** URI of the just-downloaded PDF (e.g. cacheDirectory/foo.pdf). */
  sourceUri: string;
  remoteUrl?: string;
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

async function writeAll(arr: LocalReport[]): Promise<void> {
  try {
    await AsyncStorage.setItem(STORAGE_KEY, JSON.stringify(arr));
  } catch { /* ignore */ }
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
 * Copy the just-downloaded PDF into the persistent reports/ directory and
 * register it. Safe to call from any platform — silently no-ops on web
 * (where FileSystem APIs are unavailable). Never throws.
 */
export async function saveLocalReport(
  input: SaveLocalReportInput,
): Promise<LocalReport | null> {
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
      let bytes: number | undefined = undefined;
      try {
        const di = await FileSystem.getInfoAsync(dest);
        if (di.exists) {
          finalUri = dest;
          if (typeof (di as any).size === "number") bytes = (di as any).size;
        }
      } catch { /* ignore */ }
      if (!finalUri) {
        try {
          const si = await FileSystem.getInfoAsync(input.sourceUri);
          if (si.exists) {
            finalUri = input.sourceUri;
            if (typeof (si as any).size === "number") bytes = (si as any).size;
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
 * List saved reports. Self-heals by silently pruning entries whose backing
 * file has disappeared (e.g. user cleared app storage or upgraded OS and
 * cacheDirectory got wiped). Survivors-only is returned to the UI.
 */
export async function listLocalReports(): Promise<LocalReport[]> {
  const all = await readAll();
  if (all.length === 0) return all;
  const survivors: LocalReport[] = [];
  let pruned = false;
  for (const r of all) {
    try {
      const info = await FileSystem.getInfoAsync(r.localUri);
      if (info.exists) {
        survivors.push(r);
      } else {
        pruned = true;
      }
    } catch {
      // If we can't even stat the file, keep the entry — Open/Share will
      // surface the failure in a user-visible way (share sheet error).
      survivors.push(r);
    }
  }
  if (pruned) {
    // Persist the cleaned-up list under the lock so concurrent writes
    // don't resurrect the dead entries.
    await withWriteLock(async () => {
      const fresh = await readAll();
      const liveIds = new Set(survivors.map((r) => r.id));
      // Keep any entries that were ADDED after our scan (newer than the
      // newest survivor); they may be valid even though we didn't stat them.
      const newest = survivors[0]?.createdAt ?? 0;
      const merged = fresh.filter((r) =>
        liveIds.has(r.id) || r.createdAt > newest
      );
      await writeAll(merged);
    });
  }
  return survivors;
}

/** Delete a report (file + registry entry). Never throws. */
export async function deleteLocalReport(id: string): Promise<boolean> {
  return withWriteLock(async () => {
    try {
      const all = await readAll();
      const idx = all.findIndex((r) => r.id === id);
      if (idx < 0) return false;
      const entry = all[idx];
      try {
        await FileSystem.deleteAsync(entry.localUri, { idempotent: true });
      } catch { /* ignore */ }
      all.splice(idx, 1);
      await writeAll(all);
      return true;
    } catch {
      return false;
    }
  });
}

/** Open the OS share sheet for a saved report. */
export async function shareLocalReport(report: LocalReport): Promise<void> {
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
  await shareLocalReport(report);
}
