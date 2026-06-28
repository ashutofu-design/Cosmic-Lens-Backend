import {
  detectQuestionLang,
  questionLangAnswerHint,
  questionLangLabel,
  questionLangLabelCompact,
  type AskQuestionLang,
} from "./questionLang";

export function QuestionLangBadge({
  questionText,
  compact = false,
}: {
  questionText: string;
  /** List row: short label in the action box. Detail page: full label. */
  compact?: boolean;
}) {
  const lang = detectQuestionLang(questionText);
  const label = compact ? questionLangLabelCompact(lang) : questionLangLabel(lang);
  const answerHint = questionLangAnswerHint(lang);

  return (
    <span
      className={`question-lang-badge question-lang-badge--${lang ?? "blocked"}`}
      title={[questionLangLabel(lang), answerHint].filter(Boolean).join(" · ")}
    >
      {compact ? "Language: " : "सवाल की भाषा: "}
      {label}
      {compact && answerHint ? ` · ${answerHint}` : null}
    </span>
  );
}

export function questionLangCode(questionText: string): AskQuestionLang | null {
  return detectQuestionLang(questionText);
}
