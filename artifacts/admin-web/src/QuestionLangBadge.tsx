import { detectQuestionLang, questionLangLabel, type AskQuestionLang } from "./questionLang";

export function QuestionLangBadge({
  questionText,
  compact = false,
}: {
  questionText: string;
  /** List row: short label in the action box. Detail page: full label. */
  compact?: boolean;
}) {
  const lang = detectQuestionLang(questionText);
  const label = compact
    ? lang === "hi"
      ? "Hindi · देवनागरी"
      : lang === "hn"
        ? "Hinglish · Roman"
        : lang === "en"
          ? "English"
          : "Unsupported"
    : questionLangLabel(lang);

  return (
    <span
      className={`question-lang-badge question-lang-badge--${lang ?? "blocked"}`}
      title={questionLangLabel(lang)}
    >
      {compact ? "Lang: " : "Question language: "}
      {label}
    </span>
  );
}

export function questionLangCode(questionText: string): AskQuestionLang | null {
  return detectQuestionLang(questionText);
}
