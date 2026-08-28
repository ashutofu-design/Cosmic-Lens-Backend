/**
 * Per-user pending My Reports mirror.
 *
 * Local report stubs are cleared on logout (account switch). This mirror
 * survives logout so pending founder orders reappear after sign-in, even
 * before the server /api/my-reports pending list is fully deployed.
 */
import AsyncStorage from "@react-native-async-storage/async-storage";

import {
  savePendingLocalReport,
  type SavePendingLocalReportInput,
} from "@/lib/localReports";

const keyFor = (userId: number) => `cosmic.pendingReports.user.${userId}.v1`;

type MirrorRow = SavePendingLocalReportInput & {
  savedAt: number;
};

async function readMirror(userId: number): Promise<MirrorRow[]> {
  if (!userId) return [];
  try {
    const raw = await AsyncStorage.getItem(keyFor(userId));
    if (!raw) return [];
    const arr = JSON.parse(raw);
    return Array.isArray(arr) ? (arr as MirrorRow[]) : [];
  } catch {
    return [];
  }
}

async function writeMirror(userId: number, rows: MirrorRow[]): Promise<void> {
  if (!userId) return;
  try {
    await AsyncStorage.setItem(keyFor(userId), JSON.stringify(rows));
  } catch {
    /* ignore */
  }
}

function sameOrder(a: MirrorRow, b: SavePendingLocalReportInput): boolean {
  const ap = (a.publicOrderId || "").trim();
  const bp = (b.publicOrderId || "").trim();
  const ao = (a.orderId || "").trim();
  const bo = (b.orderId || "").trim();
  if (ap && bp && ap === bp) return true;
  if (ao && bo && ao === bo) return true;
  return false;
}

/** Remember a pending order for this user (survives logout). */
export async function mirrorPendingReport(
  userId: number,
  input: SavePendingLocalReportInput,
): Promise<void> {
  if (!userId) return;
  const rows = await readMirror(userId);
  const next: MirrorRow = { ...input, savedAt: Date.now() };
  const idx = rows.findIndex((r) => sameOrder(r, input));
  if (idx >= 0) rows[idx] = next;
  else rows.unshift(next);
  // Keep last 40 — enough for a heavy tester, small for AsyncStorage.
  await writeMirror(userId, rows.slice(0, 40));
}

/** Drop a mirrored pending row once delivered / cancelled. */
export async function unmirrorPendingReport(
  userId: number,
  opts: { orderId?: string; publicOrderId?: string },
): Promise<void> {
  if (!userId) return;
  const pub = (opts.publicOrderId || "").trim();
  const oid = (opts.orderId || "").trim();
  if (!pub && !oid) return;
  const rows = await readMirror(userId);
  const keep = rows.filter((r) => {
    if (pub && r.publicOrderId === pub) return false;
    if (oid && r.orderId === oid) return false;
    return true;
  });
  if (keep.length !== rows.length) await writeMirror(userId, keep);
}

/**
 * Keep only mirrored rows that still exist on the server pending list
 * (drops admin-cancelled / deleted orders so they never come back after logout).
 */
export async function syncMirrorToLivePending(
  userId: number,
  livePending: Array<{ orderId?: string; publicOrderId?: string }>,
): Promise<number> {
  if (!userId) return 0;
  const livePubs = new Set<string>();
  const liveOids = new Set<string>();
  for (const row of livePending) {
    const pub = (row.publicOrderId || "").trim();
    const oid = (row.orderId || "").trim();
    if (pub) livePubs.add(pub);
    if (oid) liveOids.add(oid);
  }
  const rows = await readMirror(userId);
  const keep = rows.filter((r) => {
    const pub = (r.publicOrderId || "").trim();
    const oid = (r.orderId || "").trim();
    if (!pub && !oid) return false;
    return (pub && livePubs.has(pub)) || (oid && liveOids.has(oid));
  });
  const dropped = rows.length - keep.length;
  if (dropped > 0) await writeMirror(userId, keep);
  return dropped;
}

/** Re-create local PENDING cards from the surviving per-user mirror. */
export async function restoreMirroredPendingReports(userId: number): Promise<number> {
  if (!userId) return 0;
  const rows = await readMirror(userId);
  let n = 0;
  for (const row of rows) {
    const saved = await savePendingLocalReport({
      kind: row.kind,
      title: row.title,
      subtitle: row.subtitle,
      orderId: row.orderId,
      publicOrderId: row.publicOrderId,
      etaLabel: row.etaLabel,
      deliverable: row.deliverable,
    });
    if (saved) n += 1;
  }
  return n;
}
