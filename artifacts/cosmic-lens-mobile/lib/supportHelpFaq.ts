/** Do not invent Help answers on the phone. The Support AI on the server replies. */

export function localSupportAnswer(
  _text: string,
  _opts?: { priorUserTexts?: string[]; cosmoId?: string },
): string {
  return "";
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
    const text = isLatestUser
      ? (serverReply || "").trim()
      : "";
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
