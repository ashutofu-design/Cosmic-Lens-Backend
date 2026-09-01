/**
 * Cosmic Intelligence V1 — archive finished chat threads for
 * My Reports → Last talked (device-local, per user).
 */
import AsyncStorage from "@react-native-async-storage/async-storage";

export type AskArchivedMessage = {
  id?: string;
  sender: "user" | "assistant" | "system";
  text: string;
  ts?: string;
};

export type AskArchivedChat = {
  session_id: string;
  source: "ask_v1";
  label: string;
  preview: string;
  talked_at: string;
  message_count: number;
  messages: AskArchivedMessage[];
};

type ArchiveMsgIn = {
  id?: string;
  role?: string;
  text?: string;
  loading?: boolean;
  streaming?: boolean;
};

function storageKey(userId: number | string): string {
  return `ask_chat_archive_v1_${userId}`;
}

function previewFrom(messages: AskArchivedMessage[]): string {
  for (let i = messages.length - 1; i >= 0; i--) {
    const t = String(messages[i]?.text || "").trim();
    if (t && messages[i].sender === "user") {
      return t.length > 120 ? `${t.slice(0, 117)}…` : t;
    }
  }
  for (let i = messages.length - 1; i >= 0; i--) {
    const t = String(messages[i]?.text || "").trim();
    if (t) return t.length > 120 ? `${t.slice(0, 117)}…` : t;
  }
  return "Cosmic Intelligence chat";
}

/** Persist current Ask thread for My Reports → Last talked (upsert same thread). */
export async function archiveAskChatSession(
  userId: number,
  messages: ArchiveMsgIn[],
): Promise<AskArchivedChat | null> {
  const cleaned: AskArchivedMessage[] = messages
    .filter((m) => {
      if (!m || m.loading || m.streaming) return false;
      if (m.id === "init" || m.id === "thinking") return false;
      const text = String(m.text || "").trim();
      return !!text && (m.role === "user" || m.role === "assistant");
    })
    .map((m) => ({
      id: m.id,
      sender: m.role === "user" ? "user" : "assistant",
      text: String(m.text || "").trim(),
      ts: new Date().toISOString(),
    }));

  const userTurns = cleaned.filter((m) => m.sender === "user");
  if (userTurns.length === 0) return null;

  const now = new Date().toISOString();
  const session: AskArchivedChat = {
    session_id: `ask_${userId}_${Date.now()}`,
    source: "ask_v1",
    label: "Cosmic Intelligence V1",
    preview: previewFrom(cleaned),
    talked_at: now,
    message_count: cleaned.length,
    messages: cleaned,
  };

  try {
    const key = storageKey(userId);
    const raw = await AsyncStorage.getItem(key);
    const prev: AskArchivedChat[] = raw ? JSON.parse(raw) : [];
    const list = Array.isArray(prev) ? prev : [];
    const firstUser = userTurns[0]?.text || "";
    const existingIdx = list.findIndex((row) => {
      const rowFirst = (row.messages || []).find((m) => m.sender === "user")?.text || "";
      return row.source === "ask_v1" && !!firstUser && rowFirst === firstUser;
    });
    let next: AskArchivedChat[];
    if (existingIdx >= 0) {
      const updated: AskArchivedChat = {
        ...list[existingIdx],
        preview: session.preview,
        talked_at: now,
        message_count: cleaned.length,
        messages: cleaned,
      };
      next = [updated, ...list.filter((_, i) => i !== existingIdx)].slice(0, 40);
      await AsyncStorage.setItem(key, JSON.stringify(next));
      return updated;
    }
    next = [session, ...list].slice(0, 40);
    await AsyncStorage.setItem(key, JSON.stringify(next));
    return session;
  } catch {
    return null;
  }
}

export async function listAskChatArchives(
  userId: number,
): Promise<AskArchivedChat[]> {
  try {
    const raw = await AsyncStorage.getItem(storageKey(userId));
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

export async function getAskChatArchive(
  userId: number,
  sessionId: string,
): Promise<AskArchivedChat | null> {
  const rows = await listAskChatArchives(userId);
  return rows.find((r) => r.session_id === sessionId) || null;
}

/** Server-saved V1 Q&A (every /api/ask) — fills Last talked even when local archive missed. */
export async function listAskHistoryFromServer(opts: {
  userId: number;
  apiKey: string;
}): Promise<AskArchivedChat[]> {
  try {
    const { getApiBase } = await import("@/lib/apiConfig");
    const res = await fetch(`${getApiBase()}/api/history?limit=100`, {
      headers: {
        "X-User-Id": String(opts.userId),
        "X-API-Key": opts.apiKey,
      },
    });
    if (!res.ok) return [];
    const j = await res.json().catch(() => ({}));
    const items = Array.isArray(j?.items) ? j.items : [];
    const out: AskArchivedChat[] = [];
    for (const it of items) {
      const q = String(it?.question_text || "").trim();
      const a = String(it?.answer_text || "").trim();
      if (!q) continue;
      const messages: AskArchivedMessage[] = [
        { sender: "user", text: q, ts: it?.created_at },
      ];
      if (a) messages.push({ sender: "assistant", text: a, ts: it?.created_at });
      out.push({
        session_id: `hist_${String(it?.id || out.length)}`,
        source: "ask_v1",
        label: "Cosmic Intelligence V1",
        preview: q.length > 120 ? `${q.slice(0, 117)}…` : q,
        talked_at: String(it?.created_at || new Date().toISOString()),
        message_count: messages.length,
        messages,
      });
    }
    return out;
  } catch {
    return [];
  }
}
