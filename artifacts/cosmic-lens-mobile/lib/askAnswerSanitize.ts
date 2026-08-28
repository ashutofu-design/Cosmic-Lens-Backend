/**
 * Strip internal / template noise from Ask answers before showing in chat.
 * Belt-and-suspenders — server should scrub too, but mobile is last gate.
 */
const LABEL_RX = [
  /Seedha\s*jawab\s*:/gi,
  /Conclusion\s*:/gi,
  /निष्कर्ष\s*:/gi,
  /Verdict\s*:/gi,
  /Nateeja\s*:/gi,
];

const INTERNAL_SENTENCE_RX =
  /(?:internal routing|execution_gatekeeper|answer quality check|engine aur final|hallucination|as an ai|language model|openai|chatgpt|hope this helps|let me know if you|consult a professional|discrepancy mil rahi|technical issue|verified jawab generate)/i;

export function sanitizeAskAnswerForDisplay(text: string): string {
  let t = (text || "").trim();
  if (!t) return t;

  if (t.includes("ⓘ Note:")) {
    t = t.split("ⓘ Note:")[0].trim();
  }

  for (const rx of LABEL_RX) {
    t = t.replace(rx, "");
  }

  const parts = t.split(/(?<=[.!?।])\s+/);
  const kept = parts
    .map((p) => p.trim())
    .filter((p) => p.length > 0 && !INTERNAL_SENTENCE_RX.test(p));
  if (kept.length > 0) {
    t = kept.join(" ").trim();
  }

  return t.replace(/\s{2,}/g, " ").trim();
}

/** User-safe fallback when API returns error JSON without answer text. */
export function askErrorToUserMessage(err?: string, fallback?: string): string {
  const e = (err || "").toLowerCase();
  if (e.includes("daily_limit") || e.includes("quota")) {
    return fallback || "Aaj ke free questions khatam ho gaye.";
  }
  if (e.includes("kundli_missing") || e.includes("412")) {
    return "Aapki kundli save nahi hai. Profile me birth details save karke dubara try karein.";
  }
  if (e.includes("auth") || e.includes("401")) {
    return "Session expired — kripya logout karke phir login karein.";
  }
  return fallback || "Kshama karein, abhi jawab dene mein dikkat aa rahi hai.";
}
