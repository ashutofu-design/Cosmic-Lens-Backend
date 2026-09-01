/**
 * Cosmic V3 — past live chats for My Reports → Last talked.
 */
import { API_BASE, apiFetchWithTimeout, demoLoginApiBases } from "@/lib/apiConfig";

export type V3ChatHistoryItem = {
  session_id: string;
  label: string;
  minutes: number;
  status: string;
  created_at?: string | null;
  ended_at?: string | null;
  started_at?: string | null;
  talked_at?: string | null;
  message_count: number;
  preview: string;
};

export type V3ChatMessage = {
  id?: string;
  sender?: string;
  text?: string;
  image_url?: string;
  ts?: string;
};

async function fetchHistoryOnce(
  base: string,
  opts: { userId: number; apiKey: string },
): Promise<V3ChatHistoryItem[]> {
  const q = new URLSearchParams({
    user_id: String(opts.userId),
    limit: "40",
  });
  const res = await apiFetchWithTimeout(
    `${base}/api/cosmic-intelligence-v3/history?${q}`,
    {
      headers: {
        "X-API-Key": opts.apiKey,
        "X-User-Id": String(opts.userId),
      },
    },
    15000,
  );
  if (!res.ok) {
    const err = new Error(`History load failed (${res.status})`) as Error & {
      status?: number;
    };
    err.status = res.status;
    throw err;
  }
  const data = await res.json();
  return Array.isArray(data?.chats) ? data.chats : [];
}

export async function fetchV3ChatHistory(opts: {
  userId: number;
  apiKey: string;
}): Promise<V3ChatHistoryItem[]> {
  const bases = demoLoginApiBases();
  let lastErr: unknown;
  for (const base of bases) {
    try {
      return await fetchHistoryOnce(base || API_BASE, opts);
    } catch (e) {
      lastErr = e;
      const status = (e as { status?: number })?.status;
      // 404 = route not deployed on this host — try next base
      if (status && status !== 404 && status !== 502 && status !== 503) {
        throw e;
      }
    }
  }
  throw lastErr instanceof Error
    ? lastErr
    : new Error("History load failed");
}

export async function fetchV3ChatTranscript(opts: {
  userId: number;
  apiKey: string;
  sessionId: string;
}): Promise<V3ChatMessage[]> {
  const q = new URLSearchParams({ user_id: String(opts.userId) });
  const bases = demoLoginApiBases();
  let lastErr: unknown;
  for (const base of bases) {
    try {
      const res = await apiFetchWithTimeout(
        `${base}/api/cosmic-intelligence-v3/session/${encodeURIComponent(opts.sessionId)}/messages?${q}`,
        {
          headers: {
            "X-API-Key": opts.apiKey,
            "X-User-Id": String(opts.userId),
          },
        },
        15000,
      );
      if (!res.ok) {
        const err = new Error(`Chat load failed (${res.status})`) as Error & {
          status?: number;
        };
        err.status = res.status;
        throw err;
      }
      const data = await res.json();
      return Array.isArray(data?.messages) ? data.messages : [];
    } catch (e) {
      lastErr = e;
    }
  }
  throw lastErr instanceof Error ? lastErr : new Error("Chat load failed");
}
