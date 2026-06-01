/** Backend `chart_proof` block from Love Reality engines */

export type ChartProofRow = {
  planet: string;
  line: string;
  tag?: string | null;
};

export type ChartProofBadge = {
  icon: string;
  label: string;
};

export type ChartProof = {
  p1Name: string;
  p2Name: string;
  p1Rows: ChartProofRow[];
  p2Rows: ChartProofRow[];
  aspectBadges: ChartProofBadge[];
  cosmicHook?: string;
  combinedAffliction?: number;
};

function asRows(raw: unknown): ChartProofRow[] {
  if (!Array.isArray(raw)) return [];
  return raw
    .filter((r): r is Record<string, unknown> => !!r && typeof r === "object")
    .map(r => ({
      planet: String(r.planet ?? ""),
      line: String(r.line ?? ""),
      tag: r.tag != null ? String(r.tag) : null,
    }))
    .filter(r => r.line.length > 0);
}

function asBadges(raw: unknown): ChartProofBadge[] {
  if (!Array.isArray(raw)) return [];
  return raw
    .filter((b): b is Record<string, unknown> => !!b && typeof b === "object")
    .map(b => ({
      icon: String(b.icon ?? "✦"),
      label: String(b.label ?? ""),
    }))
    .filter(b => b.label.length > 0)
    .slice(0, 2);
}

export function parseChartProof(json: Record<string, unknown>): ChartProof | null {
  const cp = json.chart_proof;
  if (!cp || typeof cp !== "object") return null;
  const o = cp as Record<string, unknown>;
  const p1Rows = asRows(o.p1_rows);
  const p2Rows = asRows(o.p2_rows);
  if (!p1Rows.length && !p2Rows.length) return null;
  return {
    p1Name: String(o.p1_name ?? "You"),
    p2Name: String(o.p2_name ?? "Partner"),
    p1Rows,
    p2Rows,
    aspectBadges: asBadges(o.aspect_badges),
    cosmicHook: typeof o.cosmic_hook === "string" ? o.cosmic_hook : undefined,
    combinedAffliction:
      typeof o.combined_affliction === "number" ? o.combined_affliction : undefined,
  };
}
