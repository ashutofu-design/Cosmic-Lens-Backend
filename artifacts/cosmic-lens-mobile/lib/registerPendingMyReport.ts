import {
  savePendingLocalReport,
  type SavePendingLocalReportInput,
  type LocalReport,
} from "@/lib/localReports";
import { mirrorPendingReport } from "@/lib/pendingReportsMirror";

/** Save PENDING card locally + mirror so it survives logout. */
export async function registerPendingMyReport(
  userId: number | null | undefined,
  input: SavePendingLocalReportInput,
): Promise<LocalReport | null> {
  // Mirror first — tiny JSON, survives even if PDF registry is quota-full.
  if (userId) {
    try {
      await mirrorPendingReport(userId, input);
    } catch (e) {
      console.warn("[registerPendingMyReport] mirror failed", e);
    }
  }

  const saved = await savePendingLocalReport(input);
  if (!saved) {
    console.warn("[registerPendingMyReport] savePendingLocalReport returned null", input);
    // Last resort: try once more after mirror restore path.
    if (userId) {
      try {
        const again = await savePendingLocalReport(input);
        return again;
      } catch {
        return null;
      }
    }
  }
  return saved;
}
