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

/** Persist current Ask thread when pack/free questions run out. */
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
    const next = [session, ...(Array.isArray(prev) ? prev : [])].slice(0, 40);
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
