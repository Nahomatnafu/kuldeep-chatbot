# Kuldeep Chatbot — Developer Guide

> **Branch to use:** `ImprovedChatBotDockerized` — this is the most up-to-date branch combining Jake's chatbot improvements with full Docker support. Start here.

---

## 1. Overview

Kuldeep Chatbot is a Retrieval-Augmented Generation (RAG) application built for manufacturing shop floors. Operators and engineers upload manuals, SOPs, and technical documents, then ask plain-language questions. The system retrieves the most relevant content and returns grounded, cited answers — it never fabricates information outside the uploaded documents.

**Tech stack:**

| Layer | Technology |
|---|---|
| Backend | Flask · ChromaDB · LangChain · OpenAI (`gpt-4o-mini` + `text-embedding-ada-002`) |
| Frontend | Next.js 15 (App Router) · React 19 · TypeScript · Tailwind CSS 4 |
| Voice input | OpenAI Whisper |
| Vector DB | ChromaDB (persistent, supports instant selective deletion) |
| Containerization | Docker + docker-compose |
| Supported file types | `.pdf` `.docx` `.txt` `.md` `.json` `.csv` `.tsv` `.html` `.htm` (32 MB max) |

---

## 2. Branch Overview

Understanding the branches will save you a lot of confusion. Here is what exists and why:

| Branch | Purpose |
|---|---|
| `main` | Latest stable code — merged from all team branches |
| `ImprovedChatBotDockerized` | **Start here** — Jake's improvements + Docker fully integrated |
| `ChatBotResponseImprovementsJake` | Jake's RAG improvements (gpt-4o-mini, guard fixes, RAGAS tests) |
| `feature/docker` | Docker infrastructure and client documentation |
| `feature/chromadb-migration` | Migration from FAISS to ChromaDB |
| `collective-experiment` | Earlier team collaboration branch |
| `rag-experiment-nahom` | Nahom's early RAG experiments |

**Why `ImprovedChatBotDockerized`?** It merges Jake's most advanced chatbot work (better model, smarter guard, deduplication, RAGAS testing) with the complete Docker setup so the app runs in one command.

---

## 3. Prerequisites

| Requirement | Version | Where to get it |
|---|---|---|
| Docker Desktop | Latest | docker.com/products/docker-desktop |
| Git | Any | git-scm.com |
| OpenAI API Key | — | platform.openai.com |
| Python | 3.11+ | python.org (only needed for local dev or running tests) |
| Node.js | 20+ | nodejs.org (only needed for local dev) |

> For most developers, Docker Desktop + an API key is all you need to get the app running.

---

## 4. Clone & Environment Setup

```bash
git clone https://github.com/Nahomatnafu/kuldeep-chatbot.git
cd kuldeep-chatbot
git checkout ImprovedChatBotDockerized
```

Create the backend `.env` file with your OpenAI API key:

```bash
# Windows PowerShell
cp backend/.env.example backend/.env
# Then open backend/.env and fill in your key
```

```env
# backend/.env
OPENAI_API_KEY=sk-...
```

> **Never commit `backend/.env` to version control.** It is already listed in `.gitignore`.

---

## 5. Running with Docker (Recommended)

Docker is the primary way to run this project. It starts both backend and frontend in one command with no dependency installation required.

### Step 1 — Start Docker Desktop
Open Docker Desktop from your Start Menu (Windows) or Applications (Mac). Wait for the whale icon in the taskbar to stop animating (~30 seconds).

### Step 2 — Build the images (first time only)

```powershell
docker-compose build
```

This compiles the Flask backend (`python:3.11-slim`) and Next.js frontend (`node:20-alpine`) into Docker images. Takes 3–5 minutes the first time. Subsequent builds are fast because Docker caches layers.

### Step 3 — Start the containers

```powershell
docker-compose up
```

Or run in the background (detached mode):

```powershell
docker-compose up -d
```

### Step 4 — Open the app

Go to **http://localhost:3000** in your browser.

| Service | URL |
|---|---|
| Frontend (Next.js) | http://localhost:3000 |
| Backend (Flask) | http://localhost:5000 |
| Health check | http://localhost:5000/api/health |

### Step 5 — Stop the containers

```powershell
docker-compose down        # stop and remove containers (data is kept)
docker-compose down -v     # stop and wipe all volumes (deletes uploaded docs + vectors)
```

### What persists across restarts

Docker mounts two directories from your local machine into the containers as volumes:

| Volume | Local path | What's stored |
|---|---|---|
| `knowledge_base/` | `./knowledge_base` | Uploaded documents |
| `chroma_db/` | `./chroma_db` | Vector embeddings |

Everything you upload is saved to your local machine. Stopping or rebuilding containers does not delete your data.

### Viewing logs

```powershell
docker-compose logs -f              # stream all logs
docker-compose logs -f backend      # backend only
docker-compose logs -f frontend     # frontend only
```

---

## 6. Running Locally (Without Docker)

Use this path if you need to debug, edit code, or run tests without rebuilding Docker images.

### Windows (PowerShell)

**First-time setup:**

```powershell
python -m venv backend\venv
backend\venv\Scripts\pip install -r backend\requirements.txt
cd frontend
npm install
cd ..
```

**Start both servers:**

```powershell
.\start-dev.ps1
```

**Stop both servers:**

```powershell
.\stop-dev.ps1
```

### macOS / Linux

**Backend (Terminal 1):**

```bash
python -m venv backend/venv
source backend/venv/bin/activate
pip install -r backend/requirements.txt
python backend/run.py
```

**Frontend (Terminal 2):**

```bash
cd frontend
npm install
npm run dev
```

The app will be available at **http://localhost:3000**.

> When running locally, `FLASK_URL` defaults to `http://localhost:5000`. In Docker, it is automatically set to `http://backend:5000` (Docker's internal network DNS).

---

## 7. Environment Variables

| Variable | Required | Default | Where to set | Purpose |
|---|---|---|---|---|
| `OPENAI_API_KEY` | Yes | — | `backend/.env` | Powers embeddings, chat (gpt-4o-mini), and Whisper voice transcription |
| `FLASK_URL` | No | `http://localhost:5000` | `frontend/.env.local` | Tells Next.js where to proxy API requests. Set automatically to `http://backend:5000` in Docker. |

---

## 8. How the RAG Pipeline Works

Understanding the pipeline is essential before making any changes to the backend.

### End-to-end flow for a single chat message

```
User types a question
       ↓
Next.js /api/chat route (proxy — keeps API key server-side)
       ↓
Flask POST /chat
       ↓
1. Off-topic guard (gpt-4o-mini, max 3 tokens — cheap classifier)
   → If off-topic: return canned reply immediately, skip RAG
       ↓
2. Scope detection
   → Single-doc intent: search only the most relevant document
   → Broad intent ("compare all", "summarize all"): query across all docs
       ↓
3. Question condensation (if conversation history exists)
   → Rephrase follow-up to standalone question using chat history
       ↓
4. ChromaDB similarity search
   → Retrieve top NUM_CHUNKS=12 chunks (embeddings: text-embedding-ada-002)
   → Deduplicate near-identical chunks before passing to LLM
       ↓
5. LLM answer generation (gpt-4o-mini)
   → Strict grounding prompt: answer ONLY from retrieved context
   → Returns answer + SOURCES_USED: chunk numbers
       ↓
6. Source citation extraction
   → Maps chunk numbers back to filenames, pages, and snippets
       ↓
Response returned to frontend with answer + sources array
```

### Off-topic guard

The guard runs **before** any document retrieval. It uses a cheap gpt-4o-mini call (max 3 tokens) to classify whether a message is:
- Personal identity questions ("What is my name?")
- Pure social small talk ("Good morning")
- Entertainment requests (jokes, poems, songs)

It also uses fast regex (`\bsing\b` not `"sing" in "using"`) to catch obvious entertainment words without an API call. The guard is **skipped** when a clarification is pending to avoid blocking short follow-up messages.

### Session memory

Each browser tab gets a unique `sessionId`. The backend stores a `ConversationBufferMemory` per session. Sessions are evicted after **2 hours of inactivity** to prevent memory bloat.

### Why ChromaDB instead of FAISS

The previous implementation used FAISS. When a document was deleted, FAISS required a full index rebuild (20–60 seconds). ChromaDB supports instant selective deletion via metadata filter:

```python
collection.delete(where={"source": filename})
```

This is why ChromaDB was chosen — deletion is instant regardless of how many documents are in the store.

---

## 9. Key Configuration Knobs

All tunable constants live at the top of `backend/app.py`:

| Constant | Default | What it controls |
|---|---|---|
| `MODEL_NAME` | `gpt-4o-mini` | LLM used for chat completions |
| `NUM_CHUNKS` | `12` | Number of chunks retrieved per query. Increase for denser documents, decrease to reduce token cost. |
| `CHUNK_SIZE` | `1000` | Characters per chunk during ingestion |
| `CHUNK_OVERLAP` | `200` | Overlap between adjacent chunks (helps preserve context at boundaries) |
| `MAX_UPLOAD_MB` | `32` | Maximum file size for uploads |
| `SESSION_TTL_SECONDS` | `7200` | How long before an idle session is evicted (2 hours) |
| `MAX_MULTI_DOC_CHUNKS` | `40` | Hard cap on chunks sent to LLM in broad multi-doc queries (~10K tokens) |

---

## 10. API Reference

All routes are on the Flask backend at port 5000. The Next.js frontend proxies these through `/api/*` so the API key never reaches the browser.

| Method | Route | Description |
|---|---|---|
| `POST` | `/chat` | Main chat endpoint. Body: `{ message, history, sessionId }` |
| `GET` | `/api/documents` | List all uploaded documents with chunk counts |
| `POST` | `/api/documents/upload` | Upload and ingest a document. Form data: `file` |
| `DELETE` | `/api/documents/<filename>` | Delete a document and all its vectors from ChromaDB |
| `POST` | `/api/clear` | Clear conversation history for a session. Body: `{ sessionId }` |
| `GET` | `/api/health` | Health check. Returns store status and active session count. |

### Example chat request

```json
POST /chat
{
  "message": "What is the startup procedure for the XR200?",
  "history": [
    { "role": "user", "content": "What documents are uploaded?" },
    { "role": "assistant", "content": "You have uploaded the XR200 manual." }
  ],
  "sessionId": "abc-123"
}
```

### Example chat response

```json
{
  "answer": "The XR200 startup procedure requires...",
  "sources": [
    {
      "filename": "XR200_Operation_Manual.pdf",
      "page": 4,
      "snippet": "Before starting the machine, ensure..."
    }
  ]
}
```

---

## 11. Testing

The project has three layers of testing. Always run tests against a live backend.

### Unit tests (pytest)

Located in `backend/test_chat_endpoint.py` and uses `conftest.py` for fixtures.

```powershell
# Windows — activate venv first
backend\venv\Scripts\activate
cd backend
pytest -v
```

```bash
# macOS / Linux
source backend/venv/bin/activate
cd backend
pytest -v
```

### RAGAS Regression Tests

The most important tests. Located in `tests/regression_test.py`. These send real questions to the live backend and score the responses using four RAG quality metrics via the [Ragas](https://docs.ragas.io/) framework.

**Setup — install ragas separately (not included in Docker image):**

```bash
pip install ragas
```

**Start the backend first, then run from the project root:**

```bash
# Informational — shows scores but does NOT fail on threshold violations
python tests/regression_test.py --no-fail

# Full CI mode — exits with code 1 if any metric drops below threshold
python tests/regression_test.py

# Override a specific threshold
python tests/regression_test.py --faithfulness 0.80 --answer-relevancy 0.75
```

**The four metrics explained:**

| Metric | Threshold | What it measures |
|---|---|---|
| `faithfulness` | 0.70 | Are all claims in the answer supported by retrieved context? Catches hallucination. |
| `answer_relevancy` | 0.70 | Does the answer actually address the question asked? |
| `context_precision` | 0.60 | Are the retrieved chunks relevant and useful for the question? |
| `context_recall` | 0.60 | Does the retrieved context cover the key facts in the ground truth? |

**Current baseline scores (Run 2 — gpt-4o-mini judge):**

| Metric | Score | Status |
|---|---|---|
| faithfulness | 0.876 | ✅ Pass |
| answer_relevancy | 0.971 | ✅ Pass |
| context_precision | 0.651 | ✅ Pass |
| context_recall | 0.499 | ⚠️ Below threshold — ground truths need rewriting from actual document text |

> **Note for next team:** `context_recall` is below threshold because the ground truths in `REGRESSION_TESTS` were written from general domain knowledge, not from the actual uploaded document text. Rewrite them to match what the documents literally say and the score will pass. Run with `--no-fail` in the meantime.

**Adding a test case** — edit the `REGRESSION_TESTS` list in `tests/regression_test.py`:

```python
{
    "id": "REG-25",
    "category": "machine-operation",
    "question": "What is the warm-up time for the XR200?",
    "ground_truth": (
        "The XR200 requires a 10-minute warm-up period before operation "
        "according to section 3 of the operation manual."
    ),
},
```

Results are saved automatically to `tests/regression_results_<timestamp>.json` after every run.

### Frontend linting

```bash
cd frontend
npm run lint
```

---

## 12. Project Layout

```
kuldeep-chatbot/
│
├── backend/
│   ├── app.py                  # Flask app + full RAG pipeline (all routes, guard, memory)
│   ├── ingest.py               # Batch document ingester (pre-load knowledge_base/)
│   ├── run.py                  # Local dev launcher
│   ├── conftest.py             # Pytest fixtures
│   ├── test_chat_endpoint.py   # Backend unit tests
│   ├── requirements.txt        # Python dependencies (ragas excluded — dev only)
│   ├── Dockerfile              # Backend Docker image (python:3.11-slim)
│   └── .env                    # Your OpenAI key — DO NOT COMMIT
│
├── frontend/
│   ├── src/app/
│   │   ├── page.tsx            # Root page — routes between Welcome/Chat views
│   │   └── api/
│   │       ├── chat/route.ts         # Proxy to Flask /chat (keeps API key server-side)
│   │       ├── documents/route.ts    # Proxy to Flask /api/documents
│   │       ├── documents/[filename]/ # Proxy for upload + delete
│   │       └── transcribe/route.ts   # Proxy to OpenAI Whisper
│   ├── src/components/
│   │   ├── ChatPage.tsx        # Main chat UI
│   │   ├── ChatBubble.tsx      # Message bubbles (user + assistant)
│   │   ├── DocumentSidebar.tsx # File upload, list, and delete UI
│   │   └── WelcomePage.tsx     # Landing screen before first message
│   └── src/lib/
│       ├── chatApi.ts          # sendMessage(), transcribeAudio() client functions
│       └── types.ts            # Shared TypeScript types
│   ├── Dockerfile              # Frontend Docker image (node:20-alpine)
│   └── .env.local              # FLASK_URL override (local dev only)
│
├── tests/
│   ├── regression_test.py      # RAGAS regression test pipeline (917 lines)
│   ├── ragas_eval.py           # Core Ragas evaluation library
│   ├── RAGAS_EVAL_README.md    # Detailed evaluation documentation
│   ├── RAG_EVALUATION_REPORT.md
│   └── regression_results_*.json  # Timestamped benchmark results
│
├── knowledge_base/             # Uploaded source documents (persisted via Docker volume)
├── chroma_db/                  # ChromaDB vector store (persisted via Docker volume — DO NOT COMMIT)
├── docker-compose.yml          # Orchestrates backend + frontend containers
├── start-dev.ps1               # Windows local dev launcher
├── stop-dev.ps1                # Windows local dev stopper
├── start-docker.ps1            # Helper to start Docker Desktop + docker-compose
└── .gitignore                  # Excludes .env, chroma_db/, venv/, node_modules/
```

---

## 13. First Use (After Starting the App)

1. Open **http://localhost:3000** in your browser.
2. Click the **Documents** panel (top-right) to open the file sidebar.
3. Click **Upload** and select one or more files (PDF, DOCX, TXT, CSV, HTML, etc.).
4. Wait for ingestion — each file shows a chunk count when done.
5. Type a question in the chat box.
6. Answers include **source citations** — filename, page number, and the exact snippet retrieved.

To pre-load documents from the `knowledge_base/` folder without using the UI:

```bash
python backend/ingest.py
```

---

## 14. Common Issues

| Symptom | Fix |
|---|---|
| "No documents uploaded" | Upload via the sidebar, or run `python backend/ingest.py` to batch-load `knowledge_base/`. |
| "Assistant isn't ready" | `OPENAI_API_KEY` is missing or invalid. Check `backend/.env` and hit `/api/health`. |
| 502 on `/api/chat` | Flask is not running. In Docker: `docker-compose logs backend`. Locally: confirm Flask is on port 5000. |
| Docker build fails | Make sure Docker Desktop is running. Try `docker-compose down` then `docker-compose up --build`. |
| ChromaDB errors on startup | Delete `chroma_db/` folder and restart. Do not edit its files manually. |
| Duplicate chunks in answers | Re-ingest the affected document — the deduplication fix in `ImprovedChatBotDockerized` deletes stale vectors before re-ingesting. |
| Voice input fails silently | Browser requires HTTPS or localhost, plus microphone permission. Audio must be under 25 MB. |
| Port 3000 or 5000 already in use | Run `.\stop-dev.ps1` (Windows) or find and kill the process using `lsof -i :5000` (Mac/Linux). |
| `context_recall` below threshold in RAGAS | Expected — ground truths need rewriting from actual document text. Run with `--no-fail` for now. |
| Guard blocks legitimate questions | The off-topic guard prompt was loosened in `ImprovedChatBotDockerized`. If still triggering, check `_GUARD_PROMPT` in `app.py` and widen the NO conditions. |
