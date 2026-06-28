import type { AskQuestionItem } from "./api";
import { formatDate, formatInr } from "./api";
import {
  AskLlmContextPanel,
  AnswerPathBadge,
  LlmUnderstoodOneLine,
  parseAskLlmContext,
} from "./AskLlmContextPanel";
import { CopyTextButton } from "./CopyTextButton";

export function AskQuestionDetailPage({
  row,
  onBack,
}: {
  row: AskQuestionItem;
  onBack: () => void;
}) {
  const ctx = parseAskLlmContext(row);

  return (
    <section className="section card ask-question-detail-page">
      <div className="ask-detail-header">
        <button type="button" className="ask-detail-back" onClick={onBack}>
          ← Back to Ask Q&A
        </button>
        <h2>Ask question detail</h2>
        <p className="detail-muted">
          {row.user_name || row.user_email || `user #${row.user_id}`}
          {" · "}
          {formatDate(row.created_at)}
          {row.topic ? ` · ${row.topic}` : ""}
        </p>
      </div>

      <div className="ask-detail-block">
        <div className="ask-detail-label-row">
          <strong>Question</strong>
          <CopyTextButton text={row.question_text} label="Copy" copiedLabel="Copied" />
        </div>
        <p className="ask-detail-question">{row.question_text}</p>
        {ctx ? (
          <p className="ask-detail-understanding">
            <LlmUnderstoodOneLine ctx={ctx} />
          </p>
        ) : null}
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
        {row.verdict_summary ? (
          <div className="ask-detail-meta-wide">
            <span className="detail-muted">Verdict</span>
            <div>{row.verdict_summary}</div>
          </div>
        ) : null}
      </div>

      <div className="ask-detail-context">
        <h3>LLM context & engine pipeline</h3>
        <AskLlmContextPanel
          row={row}
          panelId={`ask-llm-context-${row.id}`}
          defaultOpen
        />
      </div>
    </section>
  );
}
