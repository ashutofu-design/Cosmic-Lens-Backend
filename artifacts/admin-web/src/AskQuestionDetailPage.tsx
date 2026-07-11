import type { AskQuestionItem } from "./api";
import { formatDate } from "./api";
import { AskObservabilityDebugger } from "./AskObservabilityDebugger";
import { buildAskDetailCopyText } from "./askObservability";
import { CopyTextButton } from "./CopyTextButton";
import { QuestionLangBadge } from "./QuestionLangBadge";

/** Production debugger detail — no legacy engine trace panels. */
export function AskQuestionDetailPage({
  row,
  onBack,
}: {
  row: AskQuestionItem;
  onBack: () => void;
}) {
  const copyAllText = buildAskDetailCopyText(row);

  return (
    <section className="section card ask-question-detail-page">
      <div className="ask-detail-header">
        <div className="ask-detail-nav-row">
          <button type="button" className="ask-detail-back" onClick={onBack}>
            ← Back to Ask Q&A
          </button>
          <CopyTextButton text={copyAllText} label="Copy All" copiedLabel="Copied!" />
        </div>
        <div className="ask-detail-title-row">
          <h2 className="ask-detail-title">
            Developer debugger
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
          <strong>Final answer (user saw)</strong>
          {row.answer_text ? (
            <CopyTextButton text={row.answer_text} label="Copy" copiedLabel="Copied" />
          ) : null}
        </div>
        <p className="ask-detail-answer">
          {row.answer_text || "No answer saved for this question."}
        </p>
      </div>

      <AskObservabilityDebugger row={row} />
    </section>
  );
}
