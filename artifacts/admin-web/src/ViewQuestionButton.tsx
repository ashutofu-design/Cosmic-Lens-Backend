export function ViewQuestionButton({
  onClick,
  label = "View",
}: {
  onClick: () => void;
  label?: string;
}) {
  return (
    <button
      type="button"
      className="copy-text-btn"
      onClick={onClick}
      title="Open full question detail page"
    >
      {label}
    </button>
  );
}
