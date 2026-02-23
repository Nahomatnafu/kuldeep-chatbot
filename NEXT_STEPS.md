# Next Steps — Multi-Document Testing (Week of Feb 24)

## Current Status
The RAG chatbot is **working end-to-end** on the `collective-experiment` branch:
- ✅ PDF upload + FAISS ingestion
- ✅ Conversational memory per session (LangChain `ConversationBufferMemory`)
- ✅ Off-topic / personal-question guard (pre-retrieval LLM classifier)
- ✅ Fixed condense prompt — new-topic questions no longer inherit prior conversation context
- ✅ Restored Nahom's 7-rule strict-grounding QA prompt
- ✅ Document delete with full FAISS index rebuild from remaining PDFs
- ✅ Next.js frontend with document sidebar, session management, source citations

---

## Must-Fix Before Next Week's Upload Session

### 1. Filename collision on upload
`secure_filename()` silently overwrites an existing PDF if two uploads share the same name.
- **Fix:** Check the registry before saving; return a 409 Conflict with a clear message (or auto-rename with a counter suffix).
- **File:** `backend/app.py` → `upload_document()`

### 2. Session invalidation is destructive
When a new PDF is uploaded, `conversation_sessions.clear()` wipes **all** active sessions.
Users mid-conversation lose their history with no warning.
- **Fix:** Broadcast an `"index_updated"` flag in the `/api/health` response so the frontend can prompt users to start a new session rather than silently resetting.
- **Files:** `backend/app.py` → `upload_document()` / `delete_document()`, `frontend/src/lib/chatApi.ts`

### 3. Chunk settings are not tuned for new document types
Current: `CHUNK_SIZE=1000`, `CHUNK_OVERLAP=200` — tuned for short research papers.
Longer documents (textbooks, technical reports) or tables-heavy PDFs may produce poor chunks.
- **Fix:** Make `CHUNK_SIZE` and `CHUNK_OVERLAP` configurable via the `.env` file, document recommended ranges in `.env.example`.
- **File:** `backend/app.py` top-of-file constants

### 4. Image-only / scanned PDFs silently produce 0 chunks
`PyPDFLoader` extracts no text from image-only PDFs, ingesting them without error but producing an empty index entry.
- **Fix:** After chunking, check `len(chunks) == 0` and return a clear error: *"No extractable text found. Is this a scanned PDF?"*
- **File:** `backend/app.py` → `_ingest_pdf()`

---

## Should-Do for Reliable Multi-Document Testing

### 5. Add source-document label to every answer
When 3+ PDFs are loaded, the `sources` array already contains filenames, but the answer text
itself gives no hint about which document it came from.
- **Fix:** Append a brief citation line at the end of the answer, e.g. *"(Source: paper2.pdf, p. 4)"*, or update the frontend `ChatBubble` to always show the top source prominently.

### 6. Increase `k` proportionally with document count
With 1 document and `k=6` you get good coverage. With 5+ documents, 6 chunks may all come
from the most-embedded document, starving others.
- **Fix:** Expose `NUM_CHUNKS` in `.env`; or dynamically set `k = min(6, 2 × doc_count)`.

### 7. Add integration tests for the multi-document path
No tests exist for `collective-experiment`. Before next week's session, add at minimum:
- Upload 2 PDFs → ask a question specific to doc 1 → assert answer cites doc 1
- Upload 2 PDFs → ask a question specific to doc 2 → assert answer cites doc 2
- Delete doc 1 → ask the same question → assert "not in documents"
- **File:** `backend/tests/test_multi_doc.py` (new file)

---

## Nice-to-Have (Lower Priority)

### 8. FAISS rebuild cost grows with document count
Deleting any document currently re-embeds **all** remaining PDFs. At 10+ docs this takes
30–60 s and costs OpenAI embedding tokens every time.
- **Fix (long term):** Store per-document vector IDs in the registry; rebuild only when
  FAISS supports selective deletion, or switch to a persistent store (Chroma, Qdrant).

### 9. No upload authentication
Any client that can reach port 5000 can upload PDFs. Acceptable for local demos, not for
a deployed chatbot.
- **Fix:** Add a simple `UPLOAD_SECRET` token checked in the upload endpoint, passed from
  the Next.js proxy via an env var.

### 10. Frontend `.env.local.example` references FastAPI
`Figma-Chatbot-Recreation-codebase/.env.local.example` still mentions `FASTAPI_URL`.
The collective branch uses Flask. Update the comment to avoid confusion.

---

## How to Run Locally (Quick Reminder)

```bash
# Backend
cd backend
python -m venv venv && venv\Scripts\activate   # Windows
pip install -r requirements.txt
cp .env.example .env   # then fill in OPENAI_API_KEY
python app.py

# Frontend (separate terminal)
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
```
Open `http://localhost:3000` → upload a PDF → start chatting.

