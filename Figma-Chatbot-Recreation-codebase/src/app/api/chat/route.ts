/**
 * Next.js Route Handler — POST /api/chat
 *
 * Acts as a server-side proxy to your FastAPI backend.
 * This keeps FASTAPI_URL out of the browser bundle and avoids CORS issues.
 *
 * ── Environment variables ────────────────────────────────────────────────────
 *   FASTAPI_URL   Full base URL of your FastAPI service.
 *                 e.g.  http://localhost:8000   or   https://api.yourdomain.com
 *
 * ── FastAPI endpoint expected ────────────────────────────────────────────────
 *   POST  {FASTAPI_URL}/chat
 *   Body: { message: string; history: {role, content}[]; session_id?: string }
 *   200:  { reply: string; session_id?: string; metadata?: object }
 *
 * ── To disable the proxy and call FastAPI directly from the browser ──────────
 *   Set NEXT_PUBLIC_API_BASE_URL to your FastAPI origin in .env.local and
 *   update src/lib/chatApi.ts to hit that URL directly instead of /api/chat.
 */

import { NextRequest, NextResponse } from "next/server";

const FASTAPI_URL = process.env.FASTAPI_URL ?? "http://localhost:8000";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();

    const upstream = await fetch(`${FASTAPI_URL}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });

    const data = await upstream.json();

    if (!upstream.ok) {
      return NextResponse.json(data, { status: upstream.status });
    }

    return NextResponse.json(data);
  } catch (err) {
    console.error("[/api/chat] upstream error:", err);
    return NextResponse.json(
      { error: "Failed to reach the AI backend. Is FastAPI running?" },
      { status: 502 }
    );
  }
}
