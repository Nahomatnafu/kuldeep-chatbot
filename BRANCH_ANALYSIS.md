# Branch Analysis — Actual Findings

> **Methodology**: Every feature was verified by reading actual committed code via
> `git show origin/<branch>:<file>`. Claims in `rag_reflection.md` were treated as
> hypotheses and confirmed or refuted against real code.

---

## rag-experiment-nahom

**Claimed Features** *(from rag_reflection.md)*: Strict grounding prompts, fastest
responses, session memory, page references.

**Actual Features Found** ✅ All claims confirmed:
- Flask backend (`src/app.py`) — OpenAI `text-embedding-ada-002` embeddings
- `ConversationalRetrievalChain` with per-session `ConversationBufferMemory`
- **k=6** chunk retrieval (highest of the three branches)
- **7-rule strict grounding prompt** — prevents hallucination, enforces context-only answers
- Page references returned: `{ id, file, page (1-indexed), snippet }`
- Pre-embedded PDFs in `knowledge_base/experimental_pdfs_nahom/` — **no upload endpoint**
- Simple HTML/CSS/JS frontend with clear-conversation button

**Standout Implementations**:
- Best prompt engineering (7-rule grounding is production-quality)
- Per-session memory via `conversation_memories` dict (clean pattern)
- Source format with `id`, `file`, `page`, and `snippet` — richest metadata

**Potential Issues**:
- No document upload — must re-run `ingest.py` to add documents
- Uses paid OpenAI embeddings (cost consideration)

---

## rag-experiment-jake

**Claimed Features** *(from rag_reflection.md)*: Free embeddings, document upload, source
references, fast local embeddings.

**Actual Features Found** ✅ All claims confirmed:
- Flask backend with **`/upload` endpoint** — accepts multipart PDF, saves to `data/pdfs/`
- **HuggingFace `sentence-transformers/all-MiniLM-L6-v2`** embeddings — free, no API key needed
- LCEL chain architecture (not `ConversationalRetrievalChain`) — **no conversational memory**
- **k=4** chunk retrieval
- Basic prompt (no strict grounding rules)
- Expandable source references in UI (accordion-style)
- `/status` endpoint to check if DB and API key are ready

**Standout Implementations**:
- `ingest_pdf()` function — clean pattern for on-demand ingestion
- Upload → ingest → reinitialize chain pipeline works well
- `allowed_file()` validation, `secure_filename()` usage

**Potential Issues**:
- No conversational memory — each question is stateless
- Basic grounding prompt (risk of hallucination vs Nahom's strict approach)
- HuggingFace embeddings require `sentence-transformers` dependency (larger install)

---

## rag-experiment-dilasha

**Claimed Features** *(from rag_reflection.md)*: Sidebar, delete documents, clickable PDF
page references, Chroma persistence.

**Actual Features Found** ⚠️ MAJOR DISCREPANCY:
- `src/app.py` — **identical to Nahom's** (same endpoints, same prompt, same embeddings)
- `src/ingest.py` — **identical to Nahom's** (same chunking, same OpenAI embeddings)
- `src/templates/index.html` — same simple chat UI as Nahom (no sidebar, no upload)
- `src/static/script.js` — functionally identical to Nahom's (no delete, no sidebar JS)
- **Sidebar**: NOT present in committed code
- **Delete document functionality**: NOT present in committed code
- **Clickable PDF page references**: NOT present in committed code

**Conclusion**: The features described in `rag_reflection.md` for Dilasha appear to have
been observed in a local demo but were **never committed** to the branch. The branch is
essentially a copy of Nahom's implementation.

---

## Figma-Chatbot-Recreation-codebase

**Status**: Untracked directory in workspace (not committed to any branch yet).

**Tech Stack**: Next.js 14 + TypeScript + Tailwind CSS

**Components Found**:
- `Header.tsx` — Blue header with robot icon and "Kuldeep" branding
- `WelcomePage.tsx` — Welcome screen with gradient avatar + subtitle
- `ChatPage.tsx` — Scrollable chat with typing indicator
- `ChatBubble.tsx` — AI and user message bubbles
- `ChatInput.tsx` — Auto-growing textarea with paperclip/mic/send icons

**API Layer**:
- `src/app/api/chat/route.ts` — Next.js proxy calling `{FASTAPI_URL}/chat`
- Expects POST `{ message, history, session_id }` → response `{ reply, session_id, metadata }`
- `src/lib/chatApi.ts` — Client that hits `/api/chat`

**Missing Components** (must be built):
- Document sidebar (upload, list, delete)
- Source/page reference display in chat bubbles

---

## Comparison Matrix

| Feature | Nahom | Jake | Dilasha | Best Implementation |
|---------|:-----:|:----:|:-------:|---------------------|
| Chroma DB Persistence | ✅ | ✅ | ✅ (same as Nahom) | Any (all identical) |
| Document Upload | ❌ | ✅ | ❌ | **Jake** |
| Conversational Memory | ✅ | ❌ | ✅ (same as Nahom) | **Nahom** |
| Strict Grounding Prompt | ✅ | ❌ | ✅ (same as Nahom) | **Nahom** |
| Page References | ✅ | ✅ | ✅ (same as Nahom) | Nahom (richer metadata) |
| Free Embeddings | ❌ | ✅ | ❌ | **Jake** (HuggingFace) |
| k=6 Chunks | ✅ | ❌ k=4 | ✅ | **Nahom** |
| Sidebar / Doc Management | ❌ | ❌ | ❌ (NOT in code) | **Build from scratch** |
| Delete Document | ❌ | ❌ | ❌ (NOT in code) | **Build from scratch** |
| Clickable PDF Links | ❌ | ❌ | ❌ (NOT in code) | **Build from scratch** |
| Modern Frontend | ❌ | ❌ | ❌ | **Figma codebase** |

---

## Recommendations for collective-experiment

**Backend (Flask)**:
1. Use **Nahom's** `ConversationalRetrievalChain` + per-session memory pattern
2. Use **Nahom's** 7-rule strict grounding prompt
3. Use **Nahom's** k=6 retrieval and OpenAI embeddings
4. Add **Jake's** upload endpoint pattern (`ingest_pdf()` + `/upload` route)
5. Add document listing (`GET /api/documents`) and delete (`DELETE /api/documents/<name>`) — **new**
6. Add `/chat` endpoint matching the Figma frontend's expected contract

**Frontend (Next.js)**:
1. Use the **Figma** design as the base
2. Update `route.ts` proxy to call Flask's endpoint format
3. Build **new** `DocumentSidebar.tsx` component (upload, list, delete)
4. Update `ChatBubble.tsx` to display source references with page numbers
5. Update `ChatPage.tsx` to include the sidebar layout

