import type { AskLlmContext, AskQuestionItem, EngineVerificationSummary } from "./api";
import { resolveEngineDisplayClient } from "./engineCatalog";

export interface EngineDisplayInfo {
  engineNo: number | null;
  sliceId: string | null;
  archetype: string | null;
  adminLine: string;
}

export function resolveEngineDisplayFromContext(
  ctx: AskLlmContext | null,
  row?: Pick<AskQuestionItem, "engine_tag">,
  engineVerify?: EngineVerificationSummary | null,
): EngineDisplayInfo {
  const stored = ctx?.engine_display;
  if (stored && typeof stored === "object" && stored.admin_line) {
    return {
      engineNo: stored.engine_no ?? null,
      sliceId: (stored.slice_id as string) || null,
      archetype: (stored.archetype as string) || null,
      adminLine: String(stored.admin_line),
    };
  }

  if (engineVerify?.engine_admin_line) {
    return {
      engineNo: engineVerify.engine_no ?? null,
      sliceId: engineVerify.engine_slice ?? null,
      archetype: engineVerify.ran_archetype ?? null,
      adminLine: engineVerify.engine_admin_line,
    };
  }

  const sliceMeta = (ctx?.slice_meta || {}) as Record<string, unknown>;
  const blocks = (ctx?.blocks || {}) as Record<string, unknown>;
  const trace = (blocks.engine_trace ||
    blocks.marriage_engine_trace ||
    blocks.career_engine_trace) as Record<string, unknown> | undefined;

  const archetype =
    engineVerify?.ran_archetype ||
    (ctx?.engine_facts?.archetype as string | undefined) ||
    (sliceMeta.archetype as string | undefined) ||
    null;

  return resolveEngineDisplayClient({
    sliceId: String(sliceMeta.slice || ctx?.checks?.slice_type || ""),
    engineKey: ctx?.engine_ran || engineVerify?.selected_engine || row?.engine_tag || "",
    archetype,
    isTiming: Boolean(ctx?.is_timing || ctx?.question_type === "TIMING"),
    engineTraceEngine: trace?.engine ? String(trace.engine) : null,
    gapStaticKey: (ctx?.llm_intent as Record<string, unknown> | undefined)?.gap_static_key as
      | string
      | undefined,
  });
}
