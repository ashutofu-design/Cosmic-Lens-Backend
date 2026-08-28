/** Server is the source of truth. Do not invent Help answers on the phone. */

export function localSupportAnswer(
  _text: string,
  _opts?: { priorUserTexts?: string[]; cosmoId?: string },
): string {
  return "";
}

type SupportRow = {
  id: string;
  sender: string;
  text?: string;
  ts: string;
  image_url?: string;
};

export function lastUserMessage<T extends { sender: string }>(msgs: T[]): T | null {
  for (let i = msgs.length - 1; i >= 0; i -= 1) {
    if (msgs[i].sender === "user") return msgs[i];
  }
  return null;
}

export function lastBotText(msgs: Array<{ sender: string; text?: string }>): string {
  for (let i = msgs.length - 1; i >= 0; i -= 1) {
    if (msgs[i].sender === "bot") {
      const t = String(msgs[i].text || "").trim();
      if (t) return t;
    }
  }
  return "";
}

export function staffAfterLastUser(msgs: Array<{ sender: string }>): boolean {
  const lastUser = lastUserMessage(msgs);
  if (!lastUser) return false;
  const idx = msgs.lastIndexOf(lastUser);
  return msgs.slice(idx + 1).some((m) => m.sender === "bot" || m.sender === "admin");
}

export function extractServerSupportReply(json: {
  ai?: { reply?: unknown };
  reply?: unknown;
  messages?: Array<{ sender?: string; text?: string }>;
} | null | undefined): string {
  const fromAi = json?.ai?.reply;
  if (typeof fromAi === "string" && fromAi.trim()) return fromAi.trim();
  if (typeof json?.reply === "string" && json.reply.trim()) return json.reply.trim();
  const msgs = Array.isArray(json?.messages) ? json.messages : [];
  for (let i = msgs.length - 1; i >= 0; i -= 1) {
    if (msgs[i]?.sender === "bot") {
      const t = String(msgs[i]?.text || "").trim();
      if (t) return t;
    }
  }
  return "";
}

/** Keep a visible Cosmic Help bubble if a stale poll snapshot dropped it. */
export function mergePolledSupportMessages<T extends { sender: string; id?: string; text?: string }>(
  prev: T[],
  incoming: T[],
): T[] {
  if (!incoming.length && prev.length) return prev;
  const prevStaff = staffAfterLastUser(prev);
  const incStaff = staffAfterLastUser(incoming);
  const prevU = lastUserMessage(prev);
  const incU = lastUserMessage(incoming);
  const sameLatestUser = Boolean(
    prevU &&
      incU &&
      (prevU.id === incU.id ||
        (String(prevU.text || "").trim() &&
          String(prevU.text || "").trim() === String(incU.text || "").trim())),
  );
  // Only freeze when the poll is a stale snapshot of the SAME latest question.
  if (prevStaff && !incStaff && sameLatestUser) return prev;
  if (prevStaff && incStaff && incoming.length < prev.length && sameLatestUser) return prev;
  return incoming;
}

export function shouldShowAgentTyping(
  msgs: Array<{ sender: string }>,
  agentState?: string,
  agentTypingFlag?: boolean,
): boolean {
  if (staffAfterLastUser(msgs)) return false;
  return Boolean(agentTypingFlag) || agentState === "processing";
}

export function askedAboutPayment(userText: string): boolean {
  return /\b(wallet|transaction|transactions|payment|paid|pay|refund|order|orders|paise|paisa|credit|credits|pack|packs|kharid)\b/i.test(
    userText || "",
  );
}

/** Remove the canned wallet/Transactions dump the model pastes into unrelated answers. */
export function stripSupportBoilerplate(text: string, userText: string = ""): string {
  let t = String(text || "").trim();
  if (!t) return t;
  t = t.replace(/^Happy to help\.?\s*/i, "").trim();
  if (askedAboutPayment(userText)) return t;
  t = t.replace(
    /Cosmic Lens (?:has no wallet|mein wallet nahi hota)[^.।]*[.।]\s*/gi,
    "",
  );
  t = t.replace(/Paid orders (?:show on Help|Help)[^.।]*Transactions[^.।]*[.।]\s*/gi, "");
  t = t.replace(/Ask credits[^.।]*(?:Cosmic Packs|Profile)[^.।]*[.।]\s*/gi, "");
  t = t.replace(
    /Pro PDFs?[^.।]*(?:My Reports|instant AI|expert)[^.।]*[.।]\s*/gi,
    "",
  );
  t = t.replace(
    /Cosmic Lens में वॉलेट नहीं होता[^.।]*[.।]\s*/gi,
    "",
  );
  return t.replace(/\s{2,}/g, " ").trim();
}

/** If the latest user message has no bot/admin reply, attach the server reply. */
export function ensureBotReply(
  msgs: Array<SupportRow>,
  _userText: string,
  serverReply?: string,
  _cosmoId?: string,
): typeof msgs {
  const out: typeof msgs = [];
  for (let i = 0; i < msgs.length; i += 1) {
    const m = msgs[i];
    out.push(m);
    if (m.sender !== "user") continue;
    const next = msgs[i + 1];
    if (next && (next.sender === "bot" || next.sender === "admin")) continue;
    const isLatestUser = !msgs.slice(i + 1).some((x) => x.sender === "user");
    const text = isLatestUser ? stripSupportBoilerplate(serverReply || "", _userText).trim() : "";
    if (!text) continue;
    out.push({
      id: `local-bot-${m.id}`,
      sender: "bot",
      text,
      ts: new Date().toISOString(),
    });
  }
  return out;
}
