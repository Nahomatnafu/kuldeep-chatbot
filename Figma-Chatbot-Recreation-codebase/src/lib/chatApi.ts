/**
 * chatApi.ts — thin client that talks to the Next.js /api/chat proxy.
 *
 * The proxy (src/app/api/chat/route.ts) forwards requests to your FastAPI
 * backend, keeping the FastAPI URL server-side and avoiding CORS issues.
 *
 * To point directly at FastAPI from the browser (e.g. in development without
 * the proxy), change NEXT_PUBLIC_API_BASE_URL to your FastAPI origin and
 * update the fetch call to hit that URL directly.
 */

import type { ChatRequest, ChatResponse, Message } from "./types";

/** Base URL for the Next.js API routes (proxy). */
const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? ""; // empty = same origin

/**
 * Send a user message to the backend and return the assistant reply.
 *
 * @param message   The user's latest message text.
 * @param history   Conversation history to send for context.
 * @param sessionId Optional session/thread ID for stateful backends.
 */
export async function sendMessage(
  message: string,
  history: Pick<Message, "role" | "content">[] = [],
  sessionId?: string
): Promise<ChatResponse> {
  const body: ChatRequest = {
    message,
    history,
    ...(sessionId ? { session_id: sessionId } : {}),
  };

  const res = await fetch(`${API_BASE}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "Unknown error");
    throw new Error(`Chat API error ${res.status}: ${text}`);
  }

  return res.json() as Promise<ChatResponse>;
}
