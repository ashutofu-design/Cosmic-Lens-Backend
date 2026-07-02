/** Mirror of api-server/ask_engine_catalog.py — stable engine numbers for admin. */

export type EngineKind = "static" | "timing" | "special";

export interface EngineCatalogEntry {
  no: number;
  slice: string;
  key: string;
  kind: EngineKind;
  label: string;
}

export const ENGINE_CATALOG: EngineCatalogEntry[] = [
  { no: 1, slice: "education_engine_v1", key: "education", kind: "static", label: "Education" },
  { no: 2, slice: "children_engine_v1", key: "children", kind: "static", label: "Children" },
  { no: 3, slice: "property_engine_v1", key: "property", kind: "static", label: "Property" },
  { no: 4, slice: "vehicle_engine_v1", key: "vehicle", kind: "static", label: "Vehicle" },
  { no: 5, slice: "travel_engine_v1", key: "travel", kind: "static", label: "Travel" },
  { no: 6, slice: "litigation_engine_v1", key: "litigation", kind: "static", label: "Litigation" },
  { no: 7, slice: "network_engine_v1", key: "network", kind: "static", label: "Network" },
  { no: 8, slice: "luck_engine_v1", key: "luck", kind: "static", label: "Luck" },
  { no: 9, slice: "career_engine_v1", key: "career", kind: "static", label: "Career" },
  { no: 10, slice: "finance_engine_v1", key: "finance", kind: "static", label: "Finance" },
  { no: 11, slice: "health_engine_v1", key: "health", kind: "static", label: "Health" },
  { no: 12, slice: "mr_engine_v1", key: "mr", kind: "static", label: "Love / Marriage" },
  { no: 13, slice: "siblings_engine_v1", key: "siblings", kind: "static", label: "Siblings" },
  { no: 14, slice: "spiritual_engine_v1", key: "spiritual", kind: "static", label: "Spiritual (static)" },
  { no: 15, slice: "parents_engine_v1", key: "parents", kind: "static", label: "Parents" },
  { no: 16, slice: "enemies_engine_v1", key: "enemies", kind: "static", label: "Enemies" },
  { no: 17, slice: "fame_engine_v1", key: "fame", kind: "static", label: "Fame (static)" },
  { no: 18, slice: "personality_engine_v1", key: "personality", kind: "static", label: "Personality" },
  { no: 19, slice: "dreams_engine_v1", key: "dreams", kind: "static", label: "Dreams" },
  { no: 20, slice: "anger_engine_v1", key: "anger", kind: "static", label: "Anger" },
  { no: 21, slice: "remedy_engine_v1", key: "remedy", kind: "static", label: "Remedy" },
  { no: 22, slice: "charity_engine_v1", key: "charity", kind: "static", label: "Charity" },
  { no: 23, slice: "settlement_engine_v1", key: "settlement", kind: "static", label: "Settlement" },
  { no: 24, slice: "vastu_engine_v1", key: "vastu", kind: "static", label: "Vastu" },
  { no: 25, slice: "pets_engine_v1", key: "pets", kind: "static", label: "Pets" },
  { no: 26, slice: "wellness_engine_v1", key: "wellness", kind: "static", label: "Wellness" },
  { no: 27, slice: "open_chart_qa_engine_v1", key: "open_chart_qa", kind: "special", label: "Open chart Q&A" },
  { no: 28, slice: "love_static_engine_v1", key: "love_static", kind: "special", label: "Love static" },
  { no: 29, slice: "milan_engine_v1", key: "milan", kind: "special", label: "Kundli Milan" },
  { no: 30, slice: "chart_fact", key: "chart_fact", kind: "special", label: "Chart fact" },
  { no: 31, slice: "gap_engine_v1", key: "gap", kind: "static", label: "Gap router" },
  { no: 32, slice: "marriage_timing_m17", key: "marriage", kind: "timing", label: "Marriage timing (M17)" },
  { no: 33, slice: "love_timing_v1", key: "love", kind: "timing", label: "Love timing" },
  { no: 34, slice: "career_timing_v1", key: "career", kind: "timing", label: "Career timing" },
  { no: 35, slice: "travel_timing_v1", key: "travel", kind: "timing", label: "Travel timing" },
  { no: 36, slice: "property_timing_v1", key: "property", kind: "timing", label: "Property timing" },
  { no: 37, slice: "vehicle_timing_v1", key: "vehicle", kind: "timing", label: "Vehicle timing" },
  { no: 38, slice: "finance_timing_v1", key: "finance", kind: "timing", label: "Finance timing" },
  { no: 39, slice: "health_timing_v1", key: "health", kind: "timing", label: "Health timing" },
  { no: 40, slice: "children_timing_v1", key: "children", kind: "timing", label: "Children timing" },
  { no: 41, slice: "education_timing_v1", key: "education", kind: "timing", label: "Education timing" },
  { no: 42, slice: "foreign_education_timing_v1", key: "foreign_education", kind: "timing", label: "Foreign education timing" },
  { no: 43, slice: "litigation_timing_v1", key: "litigation", kind: "timing", label: "Litigation timing" },
  { no: 44, slice: "spiritual_timing_v1", key: "spiritual", kind: "timing", label: "Spiritual timing" },
  { no: 45, slice: "fame_timing_v1", key: "fame", kind: "timing", label: "Fame timing" },
  { no: 46, slice: "network_timing_v1", key: "network", kind: "timing", label: "Network timing" },
  { no: 47, slice: "universal_timing_v1", key: "universal", kind: "timing", label: "Universal timing" },
];

const SLICE_INDEX = new Map(ENGINE_CATALOG.map((e) => [e.slice, e]));
const TIMING_KEY_INDEX = new Map(
  ENGINE_CATALOG.filter((e) => e.kind === "timing").map((e) => [e.key, e]),
);

const SPIRITUAL_TIMING_BUCKETS = new Set([
  "guru_deeksha",
  "occult_learning",
  "pilgrimage",
  "inner_peace",
  "general_spiritual",
]);

export interface EngineDisplay {
  engineNo: number | null;
  sliceId: string | null;
  archetype: string | null;
  adminLine: string;
}

export function resolveEngineDisplayClient(opts: {
  sliceId?: string | null;
  engineKey?: string | null;
  archetype?: string | null;
  isTiming?: boolean;
  engineTraceEngine?: string | null;
  gapStaticKey?: string | null;
}): EngineDisplay {
  const arch = (opts.archetype || "").trim() || null;
  const isTiming = Boolean(opts.isTiming);
  const traceSl = (opts.engineTraceEngine || "").trim() || null;
  const gapKey = (opts.gapStaticKey || "").trim().toLowerCase() || null;

  let entry: EngineCatalogEntry | undefined;
  let resolvedSlice: string | null = null;

  for (const candidate of [traceSl, opts.sliceId || null]) {
    if (candidate) {
      entry = SLICE_INDEX.get(candidate);
      if (entry) {
        resolvedSlice = entry.slice;
        break;
      }
    }
  }

  if (!entry && gapKey) {
    entry = SLICE_INDEX.get(`${gapKey}_engine_v1`);
    if (entry) resolvedSlice = entry.slice;
  }

  if (!entry && opts.engineKey) {
    const key = opts.engineKey.trim().toLowerCase();
    entry = isTiming ? TIMING_KEY_INDEX.get(key) : SLICE_INDEX.get(`${key}_engine_v1`) || TIMING_KEY_INDEX.get(key);
    if (entry) resolvedSlice = entry.slice;
  }

  if (!entry && arch && isTiming && SPIRITUAL_TIMING_BUCKETS.has(arch)) {
    entry = SLICE_INDEX.get("spiritual_timing_v1");
    resolvedSlice = "spiritual_timing_v1";
  }

  const no = entry?.no ?? null;
  const slOut = resolvedSlice || traceSl || (opts.sliceId || "").trim() || null;

  const parts: string[] = [];
  if (no != null) parts.push(`Engine #${no}`);
  if (slOut) parts.push(slOut);
  if (arch && arch !== slOut) parts.push(`bucket: ${arch}`);
  else if (arch && !slOut) parts.push(arch);

  return {
    engineNo: no,
    sliceId: slOut,
    archetype: arch,
    adminLine: parts.length > 0 ? parts.join(" · ") : arch || slOut || "—",
  };
}
