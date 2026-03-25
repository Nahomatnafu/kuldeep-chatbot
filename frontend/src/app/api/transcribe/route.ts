import { NextRequest, NextResponse } from "next/server";

const OPENAI_TRANSCRIBE_URL = "https://api.openai.com/v1/audio/transcriptions";
const OPENAI_TRANSCRIBE_MODEL = process.env.OPENAI_TRANSCRIBE_MODEL ?? "whisper-1";
const OPENAI_TRANSCRIBE_LANGUAGE = "en";
const MAX_AUDIO_SIZE_BYTES = 25 * 1024 * 1024; // 25 MB — Whisper API hard limit

export async function POST(req: NextRequest) {
  try {
    const apiKey = process.env.OPENAI_API_KEY;
    if (!apiKey) {
      return NextResponse.json(
        { error: "OPENAI_API_KEY is not configured on the server." },
        { status: 500 }
      );
    }

    const form = await req.formData();
    const audio = form.get("audio");

    if (!(audio instanceof File)) {
      return NextResponse.json(
        { error: "Missing audio file. Send multipart/form-data with an 'audio' field." },
        { status: 400 }
      );
    }

    if (audio.size === 0) {
      return NextResponse.json({ error: "Audio file is empty." }, { status: 400 });
    }

    if (audio.size > MAX_AUDIO_SIZE_BYTES) {
      return NextResponse.json(
        { error: `Audio file exceeds the 25 MB limit (received ${(audio.size / 1024 / 1024).toFixed(1)} MB).` },
        { status: 413 }
      );
    }

    const upstreamForm = new FormData();
    upstreamForm.append("file", audio, audio.name || "recording.webm");
    upstreamForm.append("model", OPENAI_TRANSCRIBE_MODEL);
    upstreamForm.append("language", OPENAI_TRANSCRIBE_LANGUAGE);
    upstreamForm.append("temperature", "0");
    upstreamForm.append("prompt", "Transcribe spoken English only.");

    const upstream = await fetch(OPENAI_TRANSCRIBE_URL, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${apiKey}`,
      },
      body: upstreamForm,
    });

    const data = await upstream.json().catch(() => ({}));

    if (!upstream.ok) {
      const errorMessage =
        (data as { error?: { message?: string } })?.error?.message ||
        "Whisper transcription request failed.";
      return NextResponse.json({ error: errorMessage }, { status: upstream.status });
    }

    const text = (data as { text?: string }).text?.trim();
    if (!text) {
      return NextResponse.json(
        { error: "Transcription completed but no text was returned." },
        { status: 422 }
      );
    }

    return NextResponse.json({ text });
  } catch (err) {
    console.error("[/api/transcribe] error:", err);
    return NextResponse.json(
      { error: "Failed to transcribe audio." },
      { status: 500 }
    );
  }
}
