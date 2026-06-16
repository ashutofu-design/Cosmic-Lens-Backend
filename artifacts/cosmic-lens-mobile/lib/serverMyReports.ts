/**
 * Pull founder-delivered PDFs from server /api/my-reports into local My Reports.
 */
import AsyncStorage from "@react-native-async-storage/async-storage";
import * as FileSystem from "expo-file-system/legacy";
import { Platform } from "react-native";

import { API_BASE } from "@/lib/apiConfig";
import { saveLocalReport, type LocalReportKind } from "@/lib/localReports";

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
};

function kindFromServer(row: ServerReportRow): LocalReportKind {
  const k = String(row.kind || "").toLowerCase();
  if (k === "love_reality_pro") return "love_reality";
  if (k === "milan_pro") return "milan";
  if (k === "numerology_pro") return "numerology";
  if (k === "vastu_pro" || k === "astrovastu_pro") return "astrovastu_pro";
  if (k === "business_vastu") return "business_vastu";
  if (k === "face_reading") return "face_reading";
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
  error?: "auth" | "network" | "server" | "none" | "already_local";
};

export async function clearServerSyncCache(): Promise<void> {
  try {
    await AsyncStorage.removeItem(SYNCED_KEY);
  } catch {
    /* ignore */
  }
}

export async function syncServerReportsForUser(opts: {
  userId: number;
  apiKey?: string | null;
  force?: boolean;
}): Promise<SyncReportsResult> {
  if (!opts.userId || !opts.apiKey) return { added: 0, serverCount: 0, error: "auth" };

  let resp: Response;
  try {
    resp = await fetch(`${API_BASE}/api/my-reports?limit=50`, {
      headers: {
        Accept: "application/json",
        "X-User-Id": String(opts.userId),
        "X-API-Key": opts.apiKey,
      },
    });
  } catch {
    return { added: 0, serverCount: 0, error: "network" };
  }
  if (!resp.ok) {
    if (resp.status === 401 || resp.status === 404) {
      return { added: 0, serverCount: 0, error: "auth" };
    }
    return { added: 0, serverCount: 0, error: "server" };
  }

  const json = await resp.json().catch(() => ({}));
  const rows = Array.isArray(json.reports) ? (json.reports as ServerReportRow[]) : [];
  if (!rows.length) return { added: 0, serverCount: 0, error: "none" };

  const synced = opts.force ? {} : await readSynced();
  let added = 0;

  for (const row of rows) {
    const id = String(row.id || "").trim();
    if (!id || (!opts.force && synced[id])) continue;

    const downloadPath = row.download_url || `/api/my-reports/${id}`;
    const url = downloadPath.startsWith("http") ? downloadPath : `${API_BASE}${downloadPath}`;

    try {
      if (Platform.OS === "web") {
        const dl = await fetch(url, {
          headers: {
            "X-User-Id": String(opts.userId),
            "X-API-Key": opts.apiKey,
            Accept: "application/pdf",
          },
        });
        if (!dl.ok) continue;
        const buf = await dl.arrayBuffer();
        const bytes = buf.byteLength;
        const bytesArr = new Uint8Array(buf);
        let binary = "";
        const chunk = 0x8000;
        for (let i = 0; i < bytesArr.length; i += chunk) {
          binary += String.fromCharCode(...bytesArr.subarray(i, i + chunk));
        }
        const dataUri = `data:application/pdf;base64,${btoa(binary)}`;
        const title =
          row.name?.trim() ||
          row.report_type?.trim() ||
          "Cosmic Lens Report";
        const saved = await saveLocalReport({
          kind: kindFromServer(row),
          title,
          subtitle: row.language ? String(row.language) : undefined,
          sourceUri: dataUri,
          remoteUrl: url,
          bytes,
          restored: true,
        });
        if (saved) {
          synced[id] = true;
          added += 1;
        }
        continue;
      }

      const cacheDir = FileSystem.cacheDirectory || FileSystem.documentDirectory || "";
      if (!cacheDir) continue;
      const target = `${cacheDir}server_report_${id}.pdf`;
      const dl = await FileSystem.downloadAsync(url, target, {
        headers: {
          "X-User-Id": String(opts.userId),
          "X-API-Key": opts.apiKey,
          Accept: "application/pdf",
        },
      });
      if (dl.status !== 200) continue;

      let bytes: number | undefined;
      try {
        const info = await FileSystem.getInfoAsync(dl.uri);
        bytes = typeof info.size === "number" ? info.size : undefined;
      } catch {
        bytes = row.size_bytes;
      }

      const title =
        row.name?.trim() ||
        row.report_type?.trim() ||
        "Cosmic Lens Report";
      const saved = await saveLocalReport({
        kind: kindFromServer(row),
        title,
        subtitle: row.language ? String(row.language) : undefined,
        sourceUri: dl.uri,
        remoteUrl: url,
        bytes,
        restored: true,
      });
      if (saved) {
        synced[id] = true;
        added += 1;
      }
    } catch {
      /* try next row */
    }
  }

  if (added || !opts.force) await writeSynced(synced);
  return {
    added,
    serverCount: rows.length,
    error: added ? undefined : rows.length ? "already_local" : "none",
  };
}
