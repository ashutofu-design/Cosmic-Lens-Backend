/** Local fill only for deny / COSMO / wait. Product answers come from the Support Agent. */

function isHinglish(text: string): boolean {
  return /\b(kya|hai|hain|nahi|kaise|kahan|meri|mera|mujhe|kitna|kitne|paise|karun|chahiye|abhi)\b/i.test(
    text,
  );
}

function isEnglish(text: string): boolean {
  const letters = (text.match(/[A-Za-z]/g) || []).length;
  return letters >= 8 && !isHinglish(text) && !/[\u0900-\u097F]/.test(text);
}

function polite(body: string, hinglish: boolean): string {
  const t = body.trim();
  if (/^(ji[, ]|happy to help)/i.test(t)) return t;
  return hinglish ? `Ji, ${t}` : `Happy to help. ${t}`;
}

function normalizeCosmo(raw?: string): string {
  const s = (raw || "").trim().toUpperCase();
  if (!s) return "";
  if (s.startsWith("COSMO")) return s;
  if (/^\d+$/.test(s)) return `COSMO${s}`;
  return s;
}

export function localSupportAnswer(
  text: string,
  opts?: { priorUserTexts?: string[]; cosmoId?: string },
): string {
  const t = (text || "").trim();
  const hn = isHinglish(t) || (!isEnglish(t) && !/[A-Za-z]{8,}/.test(t));
  const low = t.toLowerCase();
  const cid = normalizeCosmo(opts?.cosmoId);
  const prior = opts?.priorUserTexts || [];
  const stuck =
    prior.length > 0 &&
    /samajh nahi|solve nahi|still not|not working|clear nahi|kuch nahi hua/.test(low);
  if (stuck) {
    return polite(
      hn
        ? "Yeh yahan clear nahi ho paaya. Customer support abhi is chat mein aayenge — thoda wait kariye, yahin reply aayega."
        : "I couldn’t fully resolve this here. Customer support will join this chat shortly — please wait.",
      hn,
    );
  }
  if (
    /source code|calculation code|system prompt|api[_ -]?key|\.env\b|admin panel|numerology engine|show me the code|flask_app|openai|other user|sab users|telegram|github/i.test(
      t,
    )
  ) {
    return polite(
      hn
        ? "Internal system details, code, ya private data share nahi kar sakte. Sirf Cosmic Lens app how-to."
        : "I can’t share internal system details, code, or private data. I only help with the Cosmic Lens app.",
      hn,
    );
  }
  const appSignal =
    /cosmic|kundli|numerolog|vastu|milan|love|cosmo|life map|report|pdf|transaction|payment|profile|login|ask|v3|pack|dosh|forecast|energy|career|health|finance|founder|wallet|refer|\bapp\b|help|relationship|realationship/i.test(
      t,
    );
  if (
    !appSignal &&
    /weather|mausam|cricket|ipl|football|bitcoin|crypto|stock market|recipe|cooking|homework|prime minister|netflix|lottery|satta|covid|vaccine|capital of|who won/i.test(
      t,
    )
  ) {
    return polite(
      hn
        ? "Main sirf Cosmic Lens app pe help karta hoon. App ke bahar ke sawaal nahi le sakta."
        : "I only help with the Cosmic Lens app. I can’t answer questions outside the app.",
      hn,
    );
  }
  const cosmoFollow =
    /cosmo|user\s*id|userid/.test(low) &&
    (prior.some((p) => /cosmo|user\s*id|userid/i.test(p)) ||
      /(dikha|dikh raha|showing|mera to|lekin|\bbut\b|\d{2,4})/.test(low));

  if (cosmoFollow) {
    return polite(
      hn
        ? cid
          ? `Haan, ${cid} hi aapka User ID hai. Jo number Profile pe dikh raha hai wahi COSMO ke saath hota hai. Change nahi hota.`
          : "Jo number Profile pe dikh raha hai wahi aapka User ID hai. 109 matlab COSMO109. Change nahi hota."
        : cid
          ? `Yes — ${cid} is your User ID. The number on Profile is the same ID.`
          : "The number on Profile is your User ID. 109 means COSMO109.",
      hn,
    );
  }
  if (/cosmo|user\s*id|userid/.test(low)) {
    return polite(
      hn
        ? cid
          ? `Aapka User ID Profile pe ${cid} hai. Signup pe milta hai, change nahi hota.`
          : "Aapka User ID Profile pe COSMO number hai. Signup pe milta hai, change nahi hota."
        : cid
          ? `Your User ID on Profile is ${cid}. It is assigned at signup and cannot be changed.`
          : "Your User ID is the COSMO number on Profile. It is assigned at signup and cannot be changed.",
      hn,
    );
  }

  return polite(
    hn
      ? "Cosmic Help aapka sawaal samajh kar check kar raha hai…"
      : "Cosmic Help is reading your question…",
    hn,
  );
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
    const priorUserTexts = msgs
      .slice(0, i)
      .filter((x) => x.sender === "user")
      .map((x) => x.text || "");
    const text =
      (isLatestUser && (serverReply || "").trim()) ||
      localSupportAnswer(m.text || userText, { priorUserTexts, cosmoId });
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
