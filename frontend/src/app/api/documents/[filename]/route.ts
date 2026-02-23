/**
 * Next.js Route Handler — DELETE /api/documents/[filename]
 * Proxies to Flask DELETE /api/documents/<filename>
 */

import { NextRequest, NextResponse } from "next/server";

const FLASK_URL = process.env.FLASK_URL ?? "http://localhost:5000";

export async function DELETE(
  _req: NextRequest,
  { params }: { params: Promise<{ filename: string }> }
) {
  try {
    const { filename } = await params;
    const encoded = encodeURIComponent(filename);

    const upstream = await fetch(`${FLASK_URL}/api/documents/${encoded}`, {
      method: "DELETE",
    });

    const data = await upstream.json();
    return NextResponse.json(data, { status: upstream.status });
  } catch (err) {
    console.error("[/api/documents/[filename]] upstream error:", err);
    return NextResponse.json(
      { success: false, message: "Failed to reach the Flask backend." },
      { status: 502 }
    );
  }
}

