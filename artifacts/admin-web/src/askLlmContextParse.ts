import type { AskLlmContext, AskQuestionItem } from "./api";

function salvageRawLlmContext(ctx: AskLlmContext): AskLlmContext | null {
  if (!ctx || typeof ctx !== "object") return null;
  const hasMeta = Boolean(
    ctx.question_meaning ||
      ctx.engine_verification_summary?.label ||
      ctx.engine_facts?.evidence?.length ||
      ctx.understanding_line ||
      ctx.slice_meta,
  );
  if (hasMeta && !ctx.raw) return ctx;

  const raw = String((ctx as { raw?: string }).raw || "").trim();
  if (!raw.startsWith("{")) return hasMeta ? ctx : null;

  const tryParse = (text: string): AskLlmContext | null => {
    try {
      const parsed = JSON.parse(text) as AskLlmContext;
      return parsed && typeof parsed === "object" ? parsed : null;
    } catch {
      return null;
    }
  };

  const direct = tryParse(raw);
  if (direct) return direct;

  for (const suffix of ['"]}', '"}]}', '"}]}}', "}"]) {
    const parsed = tryParse(raw + suffix);
    if (parsed) return parsed;
  }
  return hasMeta ? ctx : null;
}

export function bootstrapAskLlmContextFromRow(
  row: Pick<
    AskQuestionItem,
    "question_text" | "topic" | "answer_source" | "engine_tag" | "verdict_summary"
  >,
): AskLlmContext {
  const q = (row.question_text || "").trim();
  const topic = (row.topic || "").trim().toLowerCase();
  const isTiming = /\b(kab|when|kis\s+saal)\b/i.test(q);
  const isLove = /\b(love|pyaar|pyar|prem|relationship|partner)\b/i.test(q);
  return {
    version: 1,
    question: q,
    topic: topic || undefined,
    is_timing: isTiming,
    question_type: isTiming ? "TIMING" : "STATIC",
    understanding_line: q || undefined,
    slice_meta: isLove
      ? {
          slice: isTiming ? "love_timing_v1" : "marriage_relationship",
          topic: "love",
        }
      : topic
        ? { topic }
        : undefined,
    checks: isLove
      ? { slice_type: isTiming ? "love_timing_v1" : "marriage_relationship" }
      : undefined,
  };
}

export function parseAskLlmContext(row: AskQuestionItem): AskLlmContext | null {
  if (row.llm_context && typeof row.llm_context === "object") {
    const salvaged = salvageRawLlmContext(row.llm_context as AskLlmContext);
    if (salvaged) {
      return {
        ...bootstrapAskLlmContextFromRow(row),
        ...salvaged,
        question: salvaged.question || row.question_text,
      };
    }
  }
  const raw = row.llm_context_json;
  if (!raw || !String(raw).trim()) {
    if (row.question_text?.trim()) {
      return bootstrapAskLlmContextFromRow(row);
    }
    return null;
  }
  try {
    const parsed = JSON.parse(raw) as AskLlmContext;
    if (parsed && typeof parsed === "object") {
      const salvaged = salvageRawLlmContext(parsed) ?? parsed;
      return {
        ...bootstrapAskLlmContextFromRow(row),
        ...salvaged,
        question: salvaged.question || row.question_text,
      };
    }
    return row.question_text?.trim() ? bootstrapAskLlmContextFromRow(row) : null;
  } catch {
    return (
      salvageRawLlmContext({ raw: String(raw).slice(0, 8000) }) ??
      (row.question_text?.trim()
        ? bootstrapAskLlmContextFromRow(row)
        : { raw: String(raw).slice(0, 8000) })
    );
  }
}

export type AnswerPathCode = "engine_then_llm" | "engine_only" | "direct_llm" | "unknown";

export function resolveAnswerPath(
  ctx: AskLlmContext | null,
  row?: Pick<AskQuestionItem, "answer_source" | "engine_tag" | "total_tokens">,
): { code: AnswerPathCode; label: string } {
  if (ctx?.answer_path && ctx?.answer_path_label) {
    return {
      code: ctx.answer_path as AnswerPathCode,
      label: String(ctx.answer_path_label),
    };
  }
  const src = (row?.answer_source || "").toLowerCase();
  if (src === "direct_llm_no_engine" || src.includes("direct_llm")) {
    return { code: "direct_llm", label: "Direct LLM (no engine)" };
  }
  if (src === "mr_engine_template" || src.includes("deterministic")) {
    return { code: "engine_only", label: "Engine only (no LLM)" };
  }
  if (src === "mr_engine_then_llm" || row?.engine_tag === "ans-engine") {
    return { code: "engine_then_llm", label: "Engine → LLM" };
  }
  if (ctx?.llm_called === false) {
    return { code: "engine_only", label: "Engine only (no LLM)" };
  }
  if (row?.total_tokens != null && row.total_tokens > 0) {
    const hasFacts = Boolean(
      ctx?.engine_facts?.verdict ||
        (ctx?.engine_facts?.evidence && ctx.engine_facts.evidence.length > 0) ||
        ctx?.slice_meta?.verdict ||
        (ctx?.slice_meta?.evidence && ctx.slice_meta.evidence.length > 0),
    );
    if (hasFacts) {
      return { code: "engine_then_llm", label: "Engine → LLM" };
    }
    return { code: "direct_llm", label: "Direct LLM (no engine facts)" };
  }
  return { code: "unknown", label: "Unknown path" };
}
