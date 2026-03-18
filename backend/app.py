"""
Collective-Experiment RAG Chatbot — Flask Backend
==================================================
Merges the best features from all three experimental branches:

  • Nahom   → OpenAI embeddings, k=6, 7-rule strict grounding, per-session memory
  • Jake    → PDF upload endpoint, on-demand ingestion, document management
  • Figma   → /chat contract matching the Next.js proxy expected format

Endpoints
---------
POST /chat                         — Main chat (used by Next.js proxy)
GET  /api/documents                — List uploaded documents
POST /api/documents/upload         — Upload + ingest a PDF
DELETE /api/documents/<filename>   — Delete a document + its vectors
POST /api/clear                    — Clear conversation history for a session
GET  /api/health                   — Health check
"""

import os
import csv
import json
import shutil
import traceback
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain.chains import ConversationalRetrievalChain
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

load_dotenv()

# ── Configuration ────────────────────────────────────────────────────────────
KNOWLEDGE_BASE_DIR = Path("knowledge_base")
FAISS_DB_DIR       = "faiss_db"
DOCUMENTS_JSON     = Path("knowledge_base/documents.json")
MODEL_NAME         = "gpt-3.5-turbo"
NUM_CHUNKS         = 6          # Nahom's k=6 for higher recall
CHUNK_SIZE         = 1000
CHUNK_OVERLAP      = 200
MAX_UPLOAD_MB      = 32
ALLOWED_EXTENSIONS = {".pdf", ".txt", ".md", ".json", ".docx", ".csv", ".tsv", ".html", ".htm"}

KNOWLEDGE_BASE_DIR.mkdir(exist_ok=True)

# ── Flask app ─────────────────────────────────────────────────────────────────
app = Flask(__name__)
CORS(app)
app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_MB * 1024 * 1024

# ── Global state ─────────────────────────────────────────────────────────────
vectorstore: FAISS | None            = None
llm:         ChatOpenAI | None       = None
_guard_llm:  ChatOpenAI | None       = None   # cheap off-topic classifier
conversation_sessions: dict          = {}   # session_id → { chain, memory }

# ── Prompt ───────────────────────────────────────────────────────────────────
_QA_TEMPLATE = """You are a careful research assistant. \
Your ONLY job is to extract and summarize information from the provided context.

STRICT GROUNDING RULES (DO NOT VIOLATE):
1. Answer ONLY from the retrieved context below — do NOT add facts not present in it.
2. Every claim in your answer MUST be traceable to a specific chunk below.
3. If the context is insufficient or doesn't contain the answer → say ONLY: \
"The uploaded documents do not contain information about this."
4. Do NOT infer, extrapolate, or fill gaps with general knowledge.
5. For lists (models, methods, steps, names) → ONLY list what is explicitly named \
in the context.
6. If the question is broad but context is limited → acknowledge the limitation: \
"Based on the provided context, the following are mentioned: ..."
7. Your answer should read like a direct summary of the chunks below, \
NOT like an essay.

Retrieved Context:
{context}

Question: {question}

Answer (extract/summarize ONLY from context above):"""

_CONDENSE_TEMPLATE = """Given the following conversation and a follow up question, \
rephrase the follow up question to be a standalone question ONLY IF truly needed.

Rules:
- If the follow-up is about a NEW topic or entity not mentioned before, \
return it EXACTLY as written — do NOT inject entities or topics from prior turns.
- Only rephrase if the follow-up uses pronouns (it, they, this, that) or \
clearly refers back to something already discussed \
(e.g. "tell me more", "what about the second one", "why is that?").
- If the chat history is empty, return the question as-is.

Chat History:
{chat_history}

Follow Up Question: {question}

Standalone question:"""

QA_PROMPT       = PromptTemplate(template=_QA_TEMPLATE,       input_variables=["context", "question"])
CONDENSE_PROMPT = PromptTemplate(template=_CONDENSE_TEMPLATE, input_variables=["chat_history", "question"])

# ── Off-topic guard ───────────────────────────────────────────────────────────
_GUARD_PROMPT = (
    "You are a strict classifier. Answer with exactly one word: YES or NO.\n\n"
    "Question: Is the user's message below a question about a specific person's own "
    "identity or personal life (e.g. 'What is my name?', 'How old am I?', 'Who am I?'), "
    "OR pure social small talk with no factual/document question?\n\n"
    "Important: questions about a *topic's* name or properties (e.g. 'What is the name "
    "of the model?') are NOT personal — answer NO for those.\n\n"
    "User message: \"{msg}\"\n\n"
    "Answer (YES or NO):"
)

def _is_off_topic(question: str) -> bool:
    """
    Make a cheap, context-free LLM call to classify whether the question is
    clearly personal / off-topic BEFORE the RAG chain retrieves any documents.
    Running this *before* retrieval prevents document context from biasing the answer.
    Returns True  → block the question and return the canned off-topic reply.
    Returns False → let the full RAG chain handle it normally.
    """
    global _guard_llm
    try:
        if _guard_llm is None:
            _guard_llm = ChatOpenAI(
                model_name="gpt-3.5-turbo",
                temperature=0,
                max_tokens=3,      # only need "YES" or "NO"
            )
        safe_msg = question.replace('"', "'")
        result   = _guard_llm.invoke(_GUARD_PROMPT.format(msg=safe_msg))
        return result.content.strip().upper().startswith("YES")
    except Exception:
        return False   # fail open — let the chain handle edge cases


# ── Helper: document registry ─────────────────────────────────────────────────
def _load_doc_registry() -> dict:
    """Load the JSON registry of ingested documents."""
    if DOCUMENTS_JSON.exists():
        return json.loads(DOCUMENTS_JSON.read_text())
    return {}


def _save_doc_registry(registry: dict) -> None:
    DOCUMENTS_JSON.write_text(json.dumps(registry, indent=2))


# ── Helper: initialise / reload vector store ─────────────────────────────────
def _init_store() -> tuple[bool, str]:
    """Load (or reload) the FAISS vector store and LLM. Returns (ok, message)."""
    global vectorstore, llm

    if not os.getenv("OPENAI_API_KEY"):
        return False, "OPENAI_API_KEY not set in environment."

    if not os.path.exists(FAISS_DB_DIR):
        return False, "No documents ingested yet. Please upload a PDF first."

    try:
        embeddings  = OpenAIEmbeddings(model="text-embedding-ada-002")
        vectorstore = FAISS.load_local(FAISS_DB_DIR, embeddings, allow_dangerous_deserialization=True)
        llm         = ChatOpenAI(model_name=MODEL_NAME, temperature=0)
        return True, "Vector store loaded."
    except Exception as exc:
        return False, f"Failed to load vector store: {exc}"


# ── Helper: load documents from any supported file type ─────────────────────
def _load_docs(filepath: Path) -> list:
    """Return a list of LangChain Documents for any supported file type."""
    ext = filepath.suffix.lower()

    if ext == ".pdf":
        return PyPDFLoader(str(filepath)).load()

    if ext in (".txt", ".md"):
        from langchain_community.document_loaders import TextLoader
        return TextLoader(str(filepath), encoding="utf-8").load()

    if ext == ".json":
        text = filepath.read_text(encoding="utf-8")
        try:
            content = json.dumps(json.loads(text), indent=2)
        except json.JSONDecodeError:
            content = text
        return [Document(page_content=content, metadata={"source": str(filepath)})]

    if ext == ".docx":
        from langchain_community.document_loaders import Docx2txtLoader
        return Docx2txtLoader(str(filepath)).load()

    if ext in (".csv", ".tsv"):
        delimiter = "\t" if ext == ".tsv" else ","
        rows = []
        with filepath.open(encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f, delimiter=delimiter)
            for row in reader:
                rows.append(", ".join(f"{k}: {v}" for k, v in row.items()))
        return [Document(page_content="\n".join(rows), metadata={"source": str(filepath)})]

    if ext in (".html", ".htm"):
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(filepath.read_text(encoding="utf-8"), "lxml")
        for tag in soup(["script", "style"]):
            tag.decompose()
        return [Document(page_content=soup.get_text(separator="\n", strip=True), metadata={"source": str(filepath)})]

    return []


# ── Helper: ingest a single file ──────────────────────────────────────────────
def _ingest_file(filepath: Path) -> tuple[bool, str, int]:
    """Chunk and embed any supported file into FAISS. Returns (ok, message, chunk_count)."""
    try:
        docs = _load_docs(filepath)
        if not docs:
            return False, f"No content extracted from {filepath.name}.", 0

        splitter   = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
        chunks     = splitter.split_documents(docs)

        embeddings = OpenAIEmbeddings(model="text-embedding-ada-002")

        if os.path.exists(FAISS_DB_DIR):
            store = FAISS.load_local(FAISS_DB_DIR, embeddings, allow_dangerous_deserialization=True)
            store.add_documents(chunks)
            store.save_local(FAISS_DB_DIR)
        else:
            FAISS.from_documents(chunks, embedding=embeddings).save_local(FAISS_DB_DIR)

        return True, f"Ingested {len(chunks)} chunks.", len(chunks)
    except Exception as exc:
        traceback.print_exc()
        return False, f"Ingestion error: {exc}", 0


# ── Helper: per-session conversational chain ─────────────────────────────────
def _get_or_create_chain(session_id: str) -> ConversationalRetrievalChain:
    """Return the existing chain for session_id, or create a new one."""
    if session_id not in conversation_sessions:
        memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            output_key="answer"
        )
        chain = ConversationalRetrievalChain.from_llm(
            llm=llm,
            retriever=vectorstore.as_retriever(search_kwargs={"k": NUM_CHUNKS}),
            memory=memory,
            return_source_documents=True,
            condense_question_prompt=CONDENSE_PROMPT,
            combine_docs_chain_kwargs={"prompt": QA_PROMPT},
        )
        conversation_sessions[session_id] = {"chain": chain, "memory": memory}
    return conversation_sessions[session_id]["chain"]


# ═══════════════════════════════════════════════════════════════════════════════
#  Routes
# ═══════════════════════════════════════════════════════════════════════════════

@app.route("/chat", methods=["POST"])
def chat():
    """
    Main chat endpoint — matches the contract the Next.js proxy expects.
    Body:   { message: str, history: list, session_id?: str }
    Reply:  { reply: str, session_id: str, metadata: { sources: [] } }
    """
    try:
        data       = request.get_json(silent=True) or {}
        message    = (data.get("message") or "").strip()
        session_id = data.get("session_id") or "default"

        if not message:
            return jsonify({"error": "Message cannot be empty"}), 400

        # Lazy-init vector store
        if vectorstore is None:
            ok, msg = _init_store()
            if not ok:
                return jsonify({"error": msg}), 503

        # Guard: block personal/off-topic questions BEFORE retrieval runs
        if _is_off_topic(message):
            return jsonify({
                "reply":      "I can only answer questions about the uploaded documents.",
                "session_id": session_id,
                "metadata":   {"sources": []},
            })

        chain  = _get_or_create_chain(session_id)
        result = chain.invoke({"question": message})

        answer      = result["answer"]
        source_docs = result.get("source_documents", [])

        sources = []
        for i, doc in enumerate(source_docs, 1):
            src     = doc.metadata.get("source", "Unknown")
            page    = doc.metadata.get("page", 0)
            snippet = doc.page_content[:150].replace("\n", " ")
            if len(doc.page_content) > 150:
                snippet += "..."
            sources.append({
                "id":      i,
                "file":    os.path.basename(src),
                "page":    page + 1,   # 1-indexed for display
                "snippet": snippet,
            })

        return jsonify({
            "reply":      answer,
            "session_id": session_id,
            "metadata":   {"sources": sources},
        })

    except Exception as exc:
        traceback.print_exc()
        return jsonify({"error": str(exc)}), 500


@app.route("/api/documents", methods=["GET"])
def list_documents():
    """Return a list of all uploaded/ingested documents."""
    registry = _load_doc_registry()
    docs = [
        {"filename": name, "chunks": info.get("chunks", 0), "uploaded_at": info.get("uploaded_at", "")}
        for name, info in registry.items()
    ]
    return jsonify({"documents": docs})


@app.route("/api/documents/upload", methods=["POST"])
def upload_document():
    """Upload and ingest a PDF file."""
    if "file" not in request.files:
        return jsonify({"success": False, "message": "No file field in request"}), 400

    file = request.files["file"]
    ext = Path(file.filename).suffix.lower() if file.filename else ""
    if not file.filename or ext not in ALLOWED_EXTENSIONS:
        allowed = ", ".join(sorted(ALLOWED_EXTENSIONS))
        return jsonify({"success": False, "message": f"Unsupported file type. Allowed: {allowed}"}), 400

    filename = secure_filename(file.filename)
    filepath = KNOWLEDGE_BASE_DIR / filename
    file.save(filepath)

    ok, msg, chunk_count = _ingest_file(filepath)
    if not ok:
        filepath.unlink(missing_ok=True)
        return jsonify({"success": False, "message": msg}), 500

    # Update registry
    registry = _load_doc_registry()
    registry[filename] = {"chunks": chunk_count, "uploaded_at": datetime.now(timezone.utc).isoformat()}
    _save_doc_registry(registry)

    # Reload vector store so new docs are immediately queryable
    _init_store()
    # Clear all sessions so they pick up the new retriever
    conversation_sessions.clear()

    return jsonify({"success": True, "message": msg, "filename": filename, "chunks": chunk_count})


@app.route("/api/documents/<filename>", methods=["DELETE"])
def delete_document(filename: str):
    """
    Delete a document's PDF file and remove its vectors from FAISS.
    FAISS does not support selective deletion by source metadata,
    so we rebuild the DB from the remaining PDFs.
    """
    registry = _load_doc_registry()
    if filename not in registry:
        return jsonify({"success": False, "message": "Document not found"}), 404

    # Remove PDF file
    pdf_path = KNOWLEDGE_BASE_DIR / filename
    pdf_path.unlink(missing_ok=True)

    # Remove from registry
    del registry[filename]
    _save_doc_registry(registry)

    # Rebuild FAISS from remaining documents
    if os.path.exists(FAISS_DB_DIR):
        shutil.rmtree(FAISS_DB_DIR)

    remaining = [p for ext in ALLOWED_EXTENSIONS for p in KNOWLEDGE_BASE_DIR.glob(f"*{ext}")]
    if remaining:
        embeddings = OpenAIEmbeddings(model="text-embedding-ada-002")
        splitter   = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
        all_chunks = []
        for doc_path in remaining:
            chunks = splitter.split_documents(_load_docs(doc_path))
            all_chunks.extend(chunks)
        FAISS.from_documents(all_chunks, embedding=embeddings).save_local(FAISS_DB_DIR)
        _init_store()

    # Clear sessions — they now point to a stale retriever
    conversation_sessions.clear()

    return jsonify({"success": True, "message": f"{filename} deleted and vectors rebuilt."})


@app.route("/api/clear", methods=["POST"])
def clear_conversation():
    """Clear conversation history for a session."""
    data       = request.get_json(silent=True) or {}
    session_id = data.get("session_id", "default")
    conversation_sessions.pop(session_id, None)
    return jsonify({"status": "success", "message": "Conversation cleared."})


@app.route("/api/health", methods=["GET"])
def health():
    """Health / readiness check."""
    has_db      = os.path.exists(FAISS_DB_DIR)
    has_api_key = bool(os.getenv("OPENAI_API_KEY"))
    return jsonify({
        "status":          "healthy",
        "has_documents":   has_db,
        "has_api_key":     has_api_key,
        "ready":           has_db and has_api_key and vectorstore is not None,
        "active_sessions": len(conversation_sessions),
    })


# ── Startup ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  Collective-Experiment RAG Chatbot  —  Flask Backend")
    print("=" * 60)
    _init_store()   # best-effort on startup; will retry lazily on first /chat
    print("  Open: http://localhost:5000")
    print("=" * 60 + "\n")
    app.run(debug=True, host="0.0.0.0", port=5000)

