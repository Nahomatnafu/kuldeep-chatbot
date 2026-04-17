# Kuldeep Chatbot

A Retrieval-Augmented Generation (RAG) chatbot for manufacturing manuals, SOPs, and technical documents. Upload PDFs, DOCX, HTML, CSV, TXT, JSON or Markdown files and ask grounded questions — answers cite the exact chunks they came from.

- **Backend**: Flask + ChromaDB + LangChain + OpenAI
- **Frontend**: Next.js 15 (App Router) + React 19 + TypeScript + Tailwind CSS 4
- **Voice input**: OpenAI Whisper

---

## Table of Contents

1. [Features](#features)
2. [Architecture](#architecture)
3. [Quick Start](#quick-start)
4. [Environment Variables](#environment-variables)
5. [Using the App](#using-the-app)
6. [Developer Guide](#developer-guide)
7. [API Reference](#api-reference)
8. [Configuration Knobs](#configuration-knobs)
9. [Testing](#testing)
10. [Troubleshooting](#troubleshooting)
11. [Project Layout](#project-layout)

---

## Features

- **Strict-grounding RAG** — the LLM is constrained to answer only from retrieved chunks and must cite them (`SOURCES_USED: …`); the UI surfaces the referenced page + snippet.
- **Multi-document synthesis** — queries that span multiple docs ("compare", "across all documents", etc.) trigger a balanced retrieval strategy with per-source citations.
- **Ambiguity clarification** — when several documents are competitive matches, the bot asks which one you mean (or "all relevant") before answering.
- **Conversational memory** — per-session chat history with automatic follow-up condensation; idle sessions are evicted after 2 hours.
- **Off-topic guard** — a cheap classifier blocks personal/small-talk questions before retrieval runs.
- **Document management UI** — slide-in sidebar to upload (file, multi-file, or folder drag-and-drop) and delete documents; ChromaDB vectors are deleted selectively without a full rebuild.
- **Voice input** — record audio in the browser, transcribed via OpenAI Whisper (`/api/transcribe`).
- **Supported formats**: `.pdf`, `.txt`, `.md`, `.json`, `.docx`, `.csv`, `.tsv`, `.html`, `.htm` (32 MB max per upload).

---

## Architecture

```
┌──────────────┐   POST /api/chat     ┌────────────────────┐   POST /chat    ┌──────────────┐
│  Browser UI  │ ───────────────────▶ │  Next.js (proxy)   │ ──────────────▶ │  Flask API   │
│  (React 19)  │                      │  /api/chat         │                 │  (Python)    │
└──────┬───────┘                      │  /api/documents    │                 └──────┬───────┘
       │                              │  /api/transcribe ──┼── OpenAI Whisper       │
       │                              └────────────────────┘                        │
       │                                                                            ▼
       │                                                                   ┌────────────────┐
       │                                                                   │   ChromaDB     │
       │                                                                   │ (persistent)   │
       │                                                                   └────────────────┘
       │                                                                            ▲
       │                                                                            │
       └──────────────────────────── sources / page / snippet ──────────────────────┘
```

The Next.js route handlers proxy to Flask so `FLASK_URL` and `OPENAI_API_KEY` never leave the server. Whisper transcription goes directly from the Next.js server to OpenAI.

---

## Quick Start

### Prerequisites

- Python **3.11+**
- Node.js **20+**
- An OpenAI API key

### 1. Clone and set your API key

```powershell
git clone <repo-url> kuldeep-chatbot
cd kuldeep-chatbot
# create a .env at the repo root with:
#   OPENAI_API_KEY=sk-...
```

### 2a. Run with Docker (simplest)

```bash
docker-compose up --build
```

- Frontend → http://localhost:3000
- Backend  → http://localhost:5000

`knowledge_base/` and `chroma_db/` are bind-mounted so uploads persist across restarts.

### 2b. Run locally (Windows, PowerShell)

```powershell
# one-time install
python -m venv backend\venv
backend\venv\Scripts\pip install -r backend\requirements.txt
cd frontend; npm install; cd ..

# every run
.\start-dev.ps1           # spawns backend + frontend in two terminals
# ...
.\stop-dev.ps1            # stops everything cleanly
```

Add `-InstallDeps` to re-install deps on start, or `-NoBackend` / `-NoFrontend` to skip one.

### 2c. Run locally (macOS / Linux)

```bash
# backend
python -m venv backend/venv
source backend/venv/bin/activate
pip install -r backend/requirements.txt
python backend/run.py &

# frontend (new terminal)
cd frontend
npm install
FLASK_URL=http://localhost:5000 OPENAI_API_KEY=sk-... npm run dev
```

---

## Environment Variables

| Variable                   | Where         | Required | Default                 | Purpose                                          |
| -------------------------- | ------------- | -------- | ----------------------- | ------------------------------------------------ |
| `OPENAI_API_KEY`           | backend + Next.js | ✅   | —                       | Embeddings, chat, Whisper transcription          |
| `FLASK_URL`                | Next.js       | ⛔️      | `http://localhost:5000` | Upstream Flask URL used by route handlers        |
| `OPENAI_TRANSCRIBE_MODEL`  | Next.js       | ⛔️      | `whisper-1`             | Override the Whisper model                       |

---

## Using the App

1. Open http://localhost:3000 — you'll see the welcome screen.
2. Click the **Documents** button (top-right) to open the sidebar.
3. Upload files via the **Upload** button, or drop a folder onto the drop zone (top-level files only, supported extensions only).
4. Wait for ingestion — each file reports its chunk count when done.
5. Ask a question in the chat. The assistant will reply with inline Markdown formatting and show the **Sources** it used (filename, page, snippet).

### Tips for better answers

- Name the document in your question ("In the **Forklift** manual, …") to skip the clarification step.
- Use phrases like *"compare"*, *"across all documents"*, *"summarize all"* to trigger multi-document synthesis.
- If answers feel thin, increase `NUM_CHUNKS` in `backend/app.py` (default 12).
- Click the microphone icon to dictate a question (English, ≤ 25 MB audio).

---

## Developer Guide

### Backend (`backend/`)

- `app.py` — Flask app with all routes, RAG pipeline, scope detection, and session memory.
- `ingest.py` — standalone batch ingester for pre-loading everything in `knowledge_base/`.
- `run.py` — thin launcher used by the PowerShell scripts (`reloader=False` to avoid double-init).
- `conftest.py` — pytest fixture that stubs heavy LangChain/OpenAI deps so test imports are fast.
- `test_chat_endpoint.py` — unit tests for `POST /chat`.

Key modules the pipeline depends on:

- `chromadb.PersistentClient(path="chroma_db")` — persistent vector store, collection `documents`.
- `OpenAIEmbeddingFunction` with `text-embedding-ada-002`.
- `langchain_openai.ChatOpenAI` with `gpt-3.5-turbo`, `temperature=0`.
- `RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)`.

Two prompts govern generation:

- `_QA_TEMPLATE` — single-document strict-grounding prompt.
- `_MULTI_DOC_QA_TEMPLATE` — multi-document synthesis prompt with `[Source: filename]` citations.

Both end with a `SOURCES_USED: …` line that `_parse_citations` extracts to build the source list returned to the frontend.

### Frontend (`frontend/`)

- `src/app/page.tsx` — entry point; orchestrates `WelcomePage` / `ChatPage` / `DocumentSidebar`.
- `src/app/api/*` — server-side route handlers that proxy to Flask and OpenAI.
- `src/components/` — `ChatBubble`, `ChatInput` (with voice capture), `DocumentSidebar`, `Header`, `WelcomePage`, `ChatPage`.
- `src/lib/chatApi.ts` / `documentApi.ts` — typed fetch helpers.
- `src/lib/types.ts` — shared `Message`, `Source`, `Clarification`, `ChatRequest`, `ChatResponse`, `Document` types.

The frontend never talks to Flask directly from the browser — all calls go through `/api/*` routes on the Next.js server. This keeps the backend URL and API key off the wire.

### Data flow on a single chat turn

1. Browser → `POST /api/chat` on Next.js with `{ message, history, session_id? }`.
2. Next.js proxies to Flask `POST /chat`.
3. Flask runs: off-topic guard → scope detection → (clarification | single-doc | multi-doc | default RAG).
4. The active branch retrieves chunks from ChromaDB, invokes the LLM, parses citations, saves memory, and returns `{ reply, session_id, metadata: { sources, clarification? } }`.
5. The UI renders Markdown, the sources panel, and clarification option buttons if present.

---

## API Reference

All Flask routes. The Next.js proxies have identical shapes.

### `POST /chat`

Request:

```json
{ "message": "How do I start the XR200?", "history": [], "session_id": "optional" }
```

Response:

```json
{
  "reply": "**Startup procedure** …",
  "session_id": "default",
  "metadata": {
    "sources": [
      { "id": 1, "file": "XR200_Operation_Manual.pdf", "page": 7, "snippet": "…" }
    ],
    "clarification": {
      "question": "I found relevant content in multiple documents …",
      "options": [
        { "label": "XR200 Operation Manual", "value": "XR200_Operation_Manual.pdf" },
        { "label": "All relevant documents", "value": "__all__" }
      ]
    }
  }
}
```

`clarification` only appears when the query is ambiguous across documents.

### `GET /api/documents`

Returns `{ documents: [{ filename, chunks, uploaded_at }] }`.

### `POST /api/documents/upload`

`multipart/form-data` with a `file` field. Returns `{ success, message, filename, chunks }`.

### `DELETE /api/documents/<filename>`

Deletes the file from disk, its vectors from ChromaDB, and clears active sessions.

### `POST /api/clear`

Clears conversation memory for `{ session_id }`.

### `GET /api/health`

Returns readiness info: `{ status, has_documents, has_api_key, ready, active_sessions }`.

### `POST /api/transcribe` (Next.js only)

`multipart/form-data` with an `audio` field (≤ 25 MB). Returns `{ text }`.

---

## Configuration Knobs

Edit these constants at the top of `backend/app.py` to tune retrieval:

| Constant                 | Default | Meaning                                                                    |
| ------------------------ | ------- | -------------------------------------------------------------------------- |
| `MODEL_NAME`             | `gpt-3.5-turbo` | Chat model used for answers and the condense step.                 |
| `NUM_CHUNKS`             | `12`    | Top-k retrieved per single-doc query.                                      |
| `CHUNK_SIZE`             | `1000`  | Characters per chunk (splitter).                                           |
| `CHUNK_OVERLAP`          | `200`   | Overlap between adjacent chunks.                                           |
| `MAX_UPLOAD_MB`          | `32`    | Max size per uploaded document.                                            |
| `MAX_MULTI_DOC_CHUNKS`   | `40`    | Hard cap on chunks sent to the LLM in multi-doc synthesis (~10K tokens).   |
| `SESSION_TTL_SECONDS`    | `7200`  | Evict conversation memory after this many seconds of inactivity.           |
| `_MIN_RELEVANCE_SCORE`   | `0.50`  | L2 threshold below which clarification is skipped — no doc is a good fit.  |
| `_SCORE_COMPETITION_GAP` | `0.35`  | Sources within this gap of the top score count as competitive.             |
| `_DOMINANCE_RATIO`       | `0.25`  | If the runner-up score is this much worse than the top, skip clarification.|

---

## Testing

Backend unit tests use pytest with LangChain/OpenAI mocks from `conftest.py`:

```powershell
cd backend
.\venv\Scripts\pytest -v
```

There are no frontend tests yet. `npm run lint` in `frontend/` runs ESLint.

---

## Troubleshooting

- **"No documents have been uploaded yet."** — open the sidebar and upload at least one document, or run `python backend/ingest.py` to batch-load `knowledge_base/`.
- **"The assistant isn't ready yet."** — `OPENAI_API_KEY` is missing or invalid. Check the env var and `/api/health`.
- **502 from `/api/chat`** — the Flask backend isn't reachable. Confirm it's running on port 5000 (or set `FLASK_URL`).
- **Voice input fails silently** — browsers require HTTPS (or localhost) + microphone permission. Whisper caps audio at 25 MB.
- **ChromaDB errors after editing files manually** — delete `chroma_db/` and re-ingest; ChromaDB's on-disk format is tied to the embedding function.
- **Port 3000 / 5000 in use (Windows)** — run `.\stop-dev.ps1 -PortsOnly` to kill whatever is bound to them.

---

## Project Layout

```
kuldeep-chatbot/
├── backend/
│   ├── app.py                 # Flask + RAG pipeline (all routes)
│   ├── ingest.py              # Batch ingester
│   ├── run.py                 # Local dev launcher
│   ├── conftest.py            # pytest mocks
│   ├── test_chat_endpoint.py  # /chat unit tests
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/app/               # Next.js App Router
│   │   ├── api/chat/          # Proxy → Flask /chat
│   │   ├── api/documents/     # Proxy → Flask /api/documents[*]
│   │   ├── api/transcribe/    # Direct → OpenAI Whisper
│   │   ├── layout.tsx
│   │   └── page.tsx
│   ├── src/components/        # ChatBubble, ChatInput, DocumentSidebar, …
│   ├── src/lib/               # API clients + shared types
│   ├── package.json
│   └── Dockerfile
├── knowledge_base/            # Uploaded source docs + documents.json registry
├── chroma_db/                 # Persistent vector store (gitignore-worthy)
├── docker-compose.yml
├── start-dev.ps1 / stop-dev.ps1
└── README.md
```

---

## License

Internal project — add a license here if/when you open it up.
