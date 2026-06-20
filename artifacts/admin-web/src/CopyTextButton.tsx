import { useState } from "react";

export function CopyTextButton({
  text,
  label = "Copy",
  copiedLabel = "Copied",
}: {
  text: string;
  label?: string;
  copiedLabel?: string;
}) {
  const [copied, setCopied] = useState(false);

  async function onCopy() {
    const value = (text || "").trim();
    if (!value) return;
    try {
      await navigator.clipboard.writeText(value);
    } catch {
      const ta = document.createElement("textarea");
      ta.value = value;
      ta.style.position = "fixed";
      ta.style.left = "-9999px";
      document.body.appendChild(ta);
      ta.select();
      document.execCommand("copy");
      document.body.removeChild(ta);
    }
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1500);
  }

  return (
    <button
      type="button"
      className="copy-text-btn"
      onClick={() => {
        void onCopy();
      }}
      title="Copy to clipboard"
    >
      {copied ? copiedLabel : label}
    </button>
  );
}
