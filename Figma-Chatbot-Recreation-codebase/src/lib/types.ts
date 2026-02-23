// Shared types used across UI components and the API layer.
// When integrating with FastAPI, these should mirror your Pydantic schemas.

export interface Message {
  id: string;
  role: "assistant" | "user";
  content: string;
  /** ISO timestamp — populated by the backend or set client-side as fallback */
  timestamp?: string;
}

// ── Request / Response shapes sent to/from the FastAPI backend ──────────────

/** POST /api/chat  →  FastAPI */
export interface ChatRequest {
  message: string;
  /**
   * Full conversation history (oldest first, newest last, excluding the
   * message above). Send to give the model conversation context.
   * Omit or send [] for single-turn mode.
   */
  history: Pick<Message, "role" | "content">[];
  /** Optional: session / thread ID for stateful backends */
  session_id?: string;
}

/** FastAPI response body */
export interface ChatResponse {
  reply: string;
  /** Optional: backend may echo or assign a session ID */
  session_id?: string;
  /** Optional: model/source metadata your backend may return */
  metadata?: Record<string, unknown>;
}
