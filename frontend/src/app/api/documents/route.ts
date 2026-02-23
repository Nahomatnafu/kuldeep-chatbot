/**
 * Next.js Route Handler — GET /api/documents
 * Proxies to Flask GET /api/documents
 */

import { NextResponse } from "next/server";

const FLASK_URL = process.env.FLASK_URL ?? "http://localhost:5000";

export async function GET() {
  try {
    const upstream = await fetch(`${FLASK_URL}/api/documents`);
    const data = await upstream.json();
    return NextResponse.json(data, { status: upstream.status });
  } catch (err) {
    console.error("[/api/documents] upstream error:", err);
    return NextResponse.json(
      { error: "Failed to reach the Flask backend." },
      { status: 502 }
    );
  }
}

