/**
 * Pull founder-delivered PDFs from server /api/my-reports into local My Reports.
 * Also syncs pending orders (waiting for founder) as placeholder cards.
 *
 * Delivered PDFs upgrade the existing PENDING card in-place (same My Reports row).
 */
import AsyncStorage from "@react-native-async-storage/async-storage";
import * as FileSystem from "expo-file-system/legacy";
import { Platform } from "react-native";

import { API_BASE, apiFetchBases } from "@/lib/apiConfig";
import {
  collapseOrphanPendingReports,
  fulfillPendingLocalReport,
  pruneStalePendingLocalReports,
  type LocalReportKind,
} from "@/lib/localReports";
import {
  restoreMirroredPendingReports,
  syncMirrorToLivePending,
  unmirrorPendingReport,
} from "@/lib/pendingReportsMirror";
import { registerPendingMyReport } from "@/lib/registerPendingMyReport";

const SYNCED_KEY = "cosmic.serverReports.synced.v1";

type ServerReportRow = {
  id: string;
  report_type?: string;
  kind?: string;
  name?: string;
  language?: string;
  size_bytes?: number;
  date?: string;
  download_url?: string;
  order_id?: string;
  public_order_id?: string;
};

type ServerPendingRow = {
  id?: string;
  order_id?: string;
  public_order_id?: string;
  kind?: string;
  status?: string;
  deliverable?: string;
  report_type?: string;
  name?: string;
  title?: string;
  eta_label?: string;
  date?: string;
};

function kindFromServer(row: { kind?: string }): LocalReportKind {
  const k = String(row.kind || "").toLowerCase();
  if (k === "love_reality_pro") return "love_reality";
  if (k === "milan_pro") return "milan";
  if (k === "numerology_pro" || k === "numerology_agent" || k === "numerology_basic") {
    return "numerology";
  }
  if (k === "vastu_pro" || k === "astrovastu_pro") return "astrovastu_pro";
  if (k === "business_vastu") return "business_vastu";
  if (k === "face_reading") return "face_reading";
  if (k === "palmistry_pro" || k === "palmistry") return "palmistry";
  return "other";
}

async function readSynced(): Promise<Record<string, true>> {
  try {
    const raw = await AsyncStorage.getItem(SYNCED_KEY);
    if (!raw) return {};
    const parsed = JSON.parse(raw);
    return parsed && typeof parsed === "object" ? parsed : {};
  } catch {
    return {};
  }
}

async function writeSynced(map: Record<string, true>): Promise<void> {
  try {
    await AsyncStorage.setItem(SYNCED_KEY, JSON.stringify(map));
  } catch {
    /* ignore */
  }
}

export type SyncReportsResult = {
  added: number;
  serverCount: number;
  pendingSynced?: number;
  error?: "auth" | "network" | "server" | "none" | "already_local";
};

export async function clearServerSyncCache(): Promise<void> {
  try {
    await AsyncStorage.removeItem(SYNCED_KEY);
  } catch {
    /* ignore */
  }
}

async function syncPendingRows(
  userId: number,
  rows: ServerPendingRow[],
): Promise<number> {
  let n = 0;
  for (const row of rows) {
    const pub = String(row.public_order_id || "").trim();
    const oid = String(row.order_id || "").trim();
    if (!pub && !oid) continue;
    const isVideo = String(row.deliverable || "").toLowerCase() === "video";
    const kind = kindFromServer(row);
    const fallbackTitle =
      kind === "numerology"
        ? isVideo
          ? "Numerology Video"
          : "Numerology Report"
        : kind === "love_reality"
          ? isVideo
            ? "Love Reality Video"
            : "Love Reality Report"
          : kind === "milan"
            ? isVideo
              ? "Kundli Milan Video"
              : "Kundli Milan Report"
            : kind === "astrovastu_pro"
              ? "AstroVastu Report"
              : kind === "business_vastu"
                ? "Business Vastu Report"
                : kind === "palmistry"
                  ? isVideo
                    ? "Palmistry Video"
                    : "Palmistry Report"
                  : isVideo
                    ? "Video Explanation"
                    : "Cosmic Lens Report";
    const title =
      String(row.title || "").trim() ||
      String(row.name || "").trim() ||
      fallbackTitle;
    const saved = await registerPendingMyReport(userId, {
      kind,
      title,
      subtitle: pub ? `Order ${pub}` : `Order ${oid.slice(0, 8).toUpperCase()}`,
      orderId: oid || undefined,
      publicOrderId: pub || undefined,
      etaLabel: row.eta_label || undefined,
      deliverable: isVideo ? "video" : "report",
    });
    if (saved) n += 1;
  }
  return n;
}

/** Prevent parallel syncs from creating duplicate ready cards. */
let _syncChain: Promise<unknown> = Promise.resolve();

function withSyncLock<T>(fn: () => Promise<T>): Promise<T> {
  const next = _syncChain.then(fn, fn);
  _syncChain = next.catch(() => undefined);
  return next;
}

async function fetchMyReportsJson(opts: {
  userId: number;
  apiKey: string;
}): Promise<{ reports: ServerReportRow[]; pending: ServerPendingRow[]; base: string } | null> {
  const bases = apiFetchBases().length ? apiFetchBases() : [API_BASE];
  // Prefer primary API_BASE first, then admin fallback (same Flask on VPS).
  const ordered = [API_BASE, "https://admin.coosmic.icu", "https://api.coosmic.icu", ...bases]
    .map((b) => b.replace(/\/$/, ""))
    .filter((b, i, arr) => b && arr.indexOf(b) === i);

  for (const base of ordered) {
    try {
      const resp = await fetch(`${base}/api/my-reports?limit=50`, {
        headers: {
          Accept: "application/json",
          "X-User-Id": String(opts.userId),
          "X-API-Key": opts.apiKey,
        },
      });
      if (!resp.ok) continue;
      const json = await resp.json().catch(() => ({}));
      return {
        reports: Array.isArray(json.reports) ? (json.reports as ServerReportRow[]) : [],
        pending: Array.isArray(json.pending) ? (json.pending as ServerPendingRow[]) : [],
        base,
      };
    } catch {
      /* try next */
    }
  }
  return null;
}

async function syncServerReportsForUserInner(opts: {
  userId: number;
  apiKey?: string | null;
  force?: boolean;
}): Promise<SyncReportsResult> {
  if (!opts.userId || !opts.apiKey) return { added: 0, serverCount: 0, error: "auth" };

  const fetched = await fetchMyReportsJson({
    userId: opts.userId,
    apiKey: opts.apiKey,
  });

  // Offline / network fail → rehydrate from mirror only (may include stale until next online sync).
  if (!fetched) {
    let mirrored = 0;
    try {
      mirrored = await restoreMirroredPendingReports(opts.userId);
    } catch {
      mirrored = 0;
    }
    return {
      added: 0,
      serverCount: 0,
      pendingSynced: mirrored,
      error: mirrored ? undefined : "network",
    };
  }

  const { reports: rows, pending: pendingRows, base: usedBase } = fetched;
  const livePending = pendingRows.map((r) => ({
    orderId: String(r.order_id || "").trim() || undefined,
    publicOrderId: String(r.public_order_id || "").trim() || undefined,
  }));

  // Drop local + mirrored PENDING for admin-cancelled / deleted orders.
  try {
    await pruneStalePendingLocalReports(livePending);
  } catch {
    /* ignore */
  }
  try {
    await syncMirrorToLivePending(opts.userId, livePending);
  } catch {
    /* ignore */
  }

  // Rehydrate only mirror rows that still match live server pending.
  let mirrored = 0;
  try {
    mirrored = await restoreMirroredPendingReports(opts.userId);
  } catch {
    mirrored = 0;
  }

  let pendingSynced = mirrored;
  try {
    pendingSynced += await syncPendingRows(opts.userId, pendingRows);
  } catch {
    /* ignore */
  }

  // Clean legacy duplicates: PENDING + separate ready PDF of same order/kind.
  try {
    await collapseOrphanPendingReports();
  } catch {
    /* ignore */
  }

  if (!rows.length) {
    return {
      added: 0,
      serverCount: 0,
      pendingSynced,
      error: pendingSynced ? undefined : "none",
    };
  }

  const synced = opts.force ? {} : await readSynced();
  let added = 0;

  for (const row of rows) {
    const id = String(row.id || "").trim();
    if (!id || (!opts.force && synced[id])) continue;

    // Claim immediately so a parallel sync skips this report id.
    synced[id] = true;
    await writeSynced(synced);

    const downloadPath = row.download_url || `/api/my-reports/${id}`;
    const url = downloadPath.startsWith("http")
      ? downloadPath
      : `${usedBase}${downloadPath}`;
    const title =
      row.name?.trim() || row.report_type?.trim() || "Cosmic Lens Report";
    const pub = String(row.public_order_id || "").trim();
    const oid = String(row.order_id || "").trim();

    try {
      if (Platform.OS === "web") {
        const dl = await fetch(url, {
          headers: {
            "X-User-Id": String(opts.userId),
            "X-API-Key": opts.apiKey,
            Accept: "application/pdf",
          },
        });
        if (!dl.ok) {
          delete synced[id];
          await writeSynced(synced);
          continue;
        }
        const buf = await dl.arrayBuffer();
        const bytes = buf.byteLength;
        const bytesArr = new Uint8Array(buf);
        let binary = "";
        const chunk = 0x8000;
        for (let i = 0; i < bytesArr.length; i += chunk) {
          binary += String.fromCharCode(...bytesArr.subarray(i, i + chunk));
        }
        const dataUri = `data:application/pdf;base64,${btoa(binary)}`;
        const saved = await fulfillPendingLocalReport({
          publicOrderId: pub || undefined,
          orderId: oid || undefined,
          kind: kindFromServer(row),
          title,
          subtitle: pub
            ? `Order ${pub}`
            : row.language
              ? String(row.language)
              : undefined,
          sourceUri: dataUri,
          remoteUrl: url,
          bytes,
        });
        if (saved) {
          added += 1;
          void unmirrorPendingReport(opts.userId, { orderId: oid, publicOrderId: pub });
        } else {
          delete synced[id];
          await writeSynced(synced);
        }
        continue;
      }

      const cacheDir = FileSystem.cacheDirectory || FileSystem.documentDirectory || "";
      if (!cacheDir) {
        delete synced[id];
        await writeSynced(synced);
        continue;
      }
      const target = `${cacheDir}server_report_${id}.pdf`;
      const dl = await FileSystem.downloadAsync(url, target, {
        headers: {
          "X-User-Id": String(opts.userId),
          "X-API-Key": opts.apiKey,
          Accept: "application/pdf",
        },
      });
      if (dl.status !== 200) {
        delete synced[id];
        await writeSynced(synced);
        continue;
      }

      let bytes: number | undefined;
      try {
        const info = await FileSystem.getInfoAsync(dl.uri);
        bytes = typeof info.size === "number" ? info.size : undefined;
      } catch {
        bytes = row.size_bytes;
      }

      const saved = await fulfillPendingLocalReport({
        publicOrderId: pub || undefined,
        orderId: oid || undefined,
        kind: kindFromServer(row),
        title,
        subtitle: pub
          ? `Order ${pub}`
          : row.language
            ? String(row.language)
            : undefined,
        sourceUri: dl.uri,
        remoteUrl: url,
        bytes,
      });
      if (saved) {
        added += 1;
        void unmirrorPendingReport(opts.userId, { orderId: oid, publicOrderId: pub });
      } else {
        delete synced[id];
        await writeSynced(synced);
      }
    } catch {
      delete synced[id];
      await writeSynced(synced);
    }
  }

  try {
    await collapseOrphanPendingReports();
  } catch {
    /* ignore */
  }

  return {
    added,
    serverCount: rows.length,
    pendingSynced,
    error: added || pendingSynced ? undefined : rows.length ? "already_local" : "none",
  };
}

export async function syncServerReportsForUser(opts: {
  userId: number;
  apiKey?: string | null;
  force?: boolean;
}): Promise<SyncReportsResult> {
  return withSyncLock(() => syncServerReportsForUserInner(opts));
}









