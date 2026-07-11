import type { AskLlmContext, AskQuestionItem, AnswerFidelitySummary, EngineVerificationSummary } from "./api";
import { formatDate, formatInr } from "./api";
import { AskObservabilityDebugger } from "./AskObservabilityDebugger";
import { CopyTextButton } from "./CopyTextButton";
import { resolveEngineDisplayFromContext } from "./engineDisplay";
import { parseAskLlmContext, resolveAnswerPath } from "./askLlmContextParse";
import { QuestionLangBadge } from "./QuestionLangBadge";

function AnswerPathBadge({
  ctx,
  row,
}: {
  ctx: AskLlmContext | null;
  row: Pick<AskQuestionItem, "answer_source" | "engine_tag" | "total_tokens">;
}) {
  const { code, label } = resolveAnswerPath(ctx, row);
  return <span className={`answer-path-badge answer-path-${code}`}>{label}</span>;
}

function EngineVerificationBadge({
  summary,
}: {
  summary: EngineVerificationSummary | null;
}) {
  if (!summary) {
    return <span className="engine-verify-badge engine-verify-unknown">Unknown</span>;
  }
  if (summary.status === "none") {
    return (
      <span className="engine-verify-badge engine-verify-none" title={summary.reason || undefined}>
        {summary.label}
      </span>
    );
  }
  return (
    <span
      className={`engine-verify-badge engine-verify-${summary.status}`}
      title={summary.reason || undefined}
    >
      {summary.label}
    </span>
  );
}

function AnswerFidelityBadge({ summary }: { summary: AnswerFidelitySummary | null }) {
  if (!summary?.label) {
    return null;
  }
  return (
    <span
      className={`answer-fidelity-badge answer-fidelity-${summary.status || "unknown"}`}
      title={summary.reason || undefined}
    >
      {summary.label}
    </span>
  );
}

function LlmUnderstandingBrief({ ctx }: { ctx: AskLlmContext | null }) {
  const text =
    ctx?.question_meaning?.trim() ||
    ctx?.llm_intent?.question_summary?.trim() ||
    ctx?.understanding_line?.trim() ||
    "";
  if (!text) {
    return <span className="detail-muted">Not saved for this row.</span>;
  }
  return <pre className="ask-detail-llm-meaning">{text}</pre>;
}

export function AskQuestionDetailPage({
  row,
  onBack,
}: {
  row: AskQuestionItem;
  onBack: () => void;
}) {
  const ctx = parseAskLlmContext(row);
  const engineVerify = ctx?.engine_verification_summary ?? null;
  const answerFidelity = ctx?.answer_fidelity_summary ?? null;
  const engineDisplay = resolveEngineDisplayFromContext(ctx, row, engineVerify);

  return (
    <section className="section card ask-question-detail-page">
      <div className="ask-detail-header">
        <button type="button" className="ask-detail-back" onClick={onBack}>
          ← Back to Ask Q&A
        </button>
        <div className="ask-detail-title-row">
          <h2 className="ask-detail-title">
            Ask question detail
            <span className="ask-detail-title-sep"> — </span>
            <span className="ask-detail-title-question">{row.question_text}</span>
          </h2>
          <div className="ask-detail-title-actions">
            <QuestionLangBadge questionText={row.question_text} compact />
            <CopyTextButton text={row.question_text} label="Copy Q" copiedLabel="Copied" />
          </div>
        </div>
        <p className="detail-muted">
          {row.user_name || row.user_email || `user #${row.user_id}`}
          {" · "}
          {formatDate(row.created_at)}
          {row.topic ? ` · ${row.topic}` : ""}
        </p>
      </div>

      <div className="ask-detail-block">
        <div className="ask-detail-label-row">
          <strong>Answer</strong>
          {row.answer_text ? (
            <CopyTextButton text={row.answer_text} label="Copy" copiedLabel="Copied" />
          ) : null}
        </div>
        <p className="ask-detail-answer">
          {row.answer_text || "No answer saved for this question."}
        </p>
      </div>

      <div className="ask-detail-meta">
        <div>
          <span className="detail-muted">Path</span>
          <div>
            <AnswerPathBadge ctx={ctx} row={row} />
            {row.answer_source ? (
              <>
                {" · "}
                <code>{row.answer_source}</code>
              </>
            ) : row.engine_tag ? (
              <> · {row.engine_tag}</>
            ) : null}
          </div>
        </div>
        <div>
          <span className="detail-muted">Tokens</span>
          <div>
            {row.total_tokens != null ? (
              <>
                {(row.prompt_tokens ?? 0).toLocaleString("en-IN")} in ·{" "}
                {(row.completion_tokens ?? 0).toLocaleString("en-IN")} out
                {row.cached_tokens ? ` · ${row.cached_tokens} cached` : ""}
              </>
            ) : (
              "No LLM call"
            )}
          </div>
        </div>
        <div>
          <span className="detail-muted">Cost</span>
          <div>
            {row.cost_inr != null ? (
              <>
                {formatInr(row.cost_inr)}
                {row.cost_usd != null ? ` ($${row.cost_usd.toFixed(4)})` : ""}
              </>
            ) : (
              "—"
            )}
          </div>
        </div>
        {row.llm_model ? (
          <div>
            <span className="detail-muted">Model</span>
            <div>
              <code>{row.llm_model}</code>
            </div>
          </div>
        ) : null}
        <div className="ask-detail-meta-wide ask-detail-llm-understood">
          <span className="detail-muted">LLM understood</span>
          <LlmUnderstandingBrief ctx={ctx} />
        </div>
        <div className="ask-detail-meta-wide ask-detail-verdict-engine">
          {row.verdict_summary ? (
            <div>
              <span className="detail-muted">Verdict</span>
              <div>{row.verdict_summary}</div>
            </div>
          ) : null}
          <div>
            <span className="detail-muted">Engine</span>
            <div className="ask-detail-engine-row">
              {engineDisplay.adminLine !== "—" ? (
                <code className="ask-detail-engine-line">{engineDisplay.adminLine}</code>
              ) : (
                <span>—</span>
              )}
              <EngineVerificationBadge summary={engineVerify} />
              <AnswerFidelityBadge summary={answerFidelity} />
            </div>
          </div>
        </div>
      </div>

      <AskObservabilityDebugger row={row} />
    </section>
  );
}
