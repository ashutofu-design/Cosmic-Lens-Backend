/** Placeholder until the Support AI on the server answers. */

export function localSupportAnswer(
  _text: string,
  _opts?: { priorUserTexts?: string[]; cosmoId?: string },
): string {
  return "Cosmic Help is reading your question…";
}

export function ensureBotReply(
  msgs: Array<{
    id: string;
    sender: string;
    text?: string;
    ts: string;
    image_url?: string;
  }>,
  userText: string,
  serverReply?: string,
  cosmoId?: string,
): typeof msgs {
  const out: typeof msgs = [];
  for (let i = 0; i < msgs.length; i += 1) {
    const m = msgs[i];
    out.push(m);
    if (m.sender !== "user") continue;
    const next = msgs[i + 1];
    if (next && (next.sender === "bot" || next.sender === "admin")) continue;
    const isLatestUser = !msgs.slice(i + 1).some((x) => x.sender === "user");
    const text =
      (isLatestUser && (serverReply || "").trim()) ||
      localSupportAnswer(m.text || userText, { cosmoId });
    if (!text.trim()) continue;
    out.push({
      id: `local-bot-${m.id}`,
      sender: "bot",
      text,
      ts: new Date().toISOString(),
    });
  }
  return out;
}
