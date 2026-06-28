import {
  detectQuestionLang,
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

  return (
    <span
      className={`question-lang-badge question-lang-badge--${lang ?? "blocked"}`}
      title={questionLangLabel(lang)}
    >
      {compact ? "भाषा: " : "सवाल की भाषा: "}
      {label}
    </span>
  );
}

export function questionLangCode(questionText: string): AskQuestionLang | null {
  return detectQuestionLang(questionText);
}
