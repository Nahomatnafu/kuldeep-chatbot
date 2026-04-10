"""
Kuldeep RAG Chatbot — Flask Backend
=====================================
RAG pipeline powered by ChromaDB + LangChain + OpenAI.

Endpoints
---------
POST   /chat                         — Main chat (used by Next.js proxy)
GET    /api/documents                — List uploaded documents
POST   /api/documents/upload         — Upload + ingest a document
DELETE /api/documents/<filename>     — Delete a document + its vectors
POST   /api/clear                    — Clear conversation history for a session
GET    /api/health                   — Health check
"""

import os
import re
import csv
import json
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

import chromadb
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction

from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

load_dotenv()

# ── Configuration ────────────────────────────────────────────────────────────
KNOWLEDGE_BASE_DIR = Path("knowledge_base")
CHROMA_DB_DIR      = "chroma_db"
DOCUMENTS_JSON     = Path("knowledge_base/documents.json")
MODEL_NAME         = "gpt-3.5-turbo"
NUM_CHUNKS         = 12         # k=12 for broader recall on dense technical documents
CHUNK_SIZE         = 1000
CHUNK_OVERLAP      = 200
MAX_UPLOAD_MB      = 32
ALLOWED_EXTENSIONS = {".pdf", ".txt", ".md", ".json", ".docx", ".csv", ".tsv", ".html", ".htm"}
BROAD_INTENT_PHRASES = {
    "all documents", "all docs", "across all", "across documents", "from all",
    "compare", "consolidate", "summarize all", "all relevant", "every document",
}
SESSION_TTL_SECONDS      = 2 * 60 * 60   # evict sessions idle for 2 hours
MAX_MULTI_DOC_CHUNKS     = 40            # hard cap on total chunks sent to LLM (≈10K tokens)

KNOWLEDGE_BASE_DIR.mkdir(exist_ok=True)

# ── Flask app ─────────────────────────────────────────────────────────────────
app = Flask(__name__)
CORS(app)
app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_MB * 1024 * 1024

# ── Global state ─────────────────────────────────────────────────────────────
collection: chromadb.Collection | None = None
llm:        ChatOpenAI | None          = None
_guard_llm: ChatOpenAI | None          = None   # cheap off-topic classifier
conversation_sessions: dict            = {}      # session_id → { memory, last_accessed }

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

FORMATTING RULES (always apply):
- Use **bold** to highlight key terms, names, model numbers, or critical warnings.
- Use bullet points or numbered lists whenever presenting multiple items, steps, or options.
- Use numbered steps for sequential procedures (e.g. startup, shutdown, inspection).
- Use short paragraphs — avoid walls of text.
- If the answer has clearly distinct sections, add a short **bold** heading for each.
- Keep formatting clean and readable — do not over-format simple one-line answers.

Retrieved Context:
{context}

Question: {question}

Answer (extract/summarize ONLY from context above, applying formatting rules):

After your answer, on a separate line write exactly:
SOURCES_USED: followed by comma-separated chunk numbers you drew from (e.g. SOURCES_USED: 1, 3, 5).
If you used none of the chunks, write: SOURCES_USED: none"""

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

_MULTI_DOC_QA_TEMPLATE = """\
You are a careful research assistant synthesizing information from multiple documents.

RULES:
1. Answer ONLY from the source chunks provided below — do NOT add external knowledge.
2. Cite which document each point comes from using [Source: filename].
3. If documents differ or conflict on a point, say so explicitly.
4. If the context is insufficient → say "The uploaded documents do not contain enough information about this."

FORMATTING RULES (always apply):
- Use **bold** to highlight key terms, names, model numbers, or critical warnings.
- Use bullet points or numbered lists whenever presenting multiple items, steps, or options.
- Use numbered steps for sequential procedures (e.g. startup, shutdown, inspection).
- Group information by document or topic using short **bold** headings where it aids clarity.
- Use short paragraphs — avoid walls of text.
- Keep formatting clean and readable — do not over-format simple one-line answers.

Retrieved Context (grouped by source):
{context}

Question: {question}

Answer (synthesize from context above, citing sources, applying formatting rules):

After your answer, on a separate line write exactly:
SOURCES_USED: followed by comma-separated chunk numbers you drew from (e.g. SOURCES_USED: 2, 4).
If you used none of the chunks, write: SOURCES_USED: none"""

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
    """Initialise (or reload) the ChromaDB collection and LLM. Returns (ok, message)."""
    global collection, llm

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return False, "OPENAI_API_KEY not set in environment."

    try:
        ef         = OpenAIEmbeddingFunction(api_key=api_key, model_name="text-embedding-ada-002")
        client     = chromadb.PersistentClient(path=CHROMA_DB_DIR)
        collection = client.get_or_create_collection(name="documents", embedding_function=ef)
        llm        = ChatOpenAI(model_name=MODEL_NAME, temperature=0)
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
    """Chunk and embed any supported file into ChromaDB. Returns (ok, message, chunk_count)."""
    try:
        docs = _load_docs(filepath)
        if not docs:
            return False, f"No content extracted from {filepath.name}.", 0

        splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
        chunks   = splitter.split_documents(docs)

        # Remove any existing vectors for this file (handles re-uploads cleanly)
        collection.delete(where={"source": str(filepath)})

        ids       = [f"{filepath.name}__chunk_{i}" for i in range(len(chunks))]
        texts     = [c.page_content for c in chunks]
        metadatas = [{"source": str(filepath), **{k: v for k, v in c.metadata.items() if isinstance(v, (str, int, float, bool))}} for c in chunks]

        collection.add(ids=ids, documents=texts, metadatas=metadatas)

        return True, f"Ingested {len(chunks)} chunks.", len(chunks)
    except Exception as exc:
        traceback.print_exc()
        return False, f"Ingestion error: {exc}", 0


# ── ChromaDB similarity search helpers ────────────────────────────────────────
def _build_numbered_context(chunks: list) -> str:
    """Format chunks as numbered sections so the LLM can cite which ones it used."""
    return "\n\n".join(f"[CHUNK {i}]\n{c.page_content}" for i, c in enumerate(chunks, 1))


def _parse_citations(raw_answer: str, chunks: list) -> tuple:
    """Parse SOURCES_USED line from answer. Returns (clean_answer, cited_chunks).
    Falls back to all chunks if the LLM omits the citation line.
    """
    match = re.search(r'\s*SOURCES_USED:\s*(.+?)\s*$', raw_answer, re.IGNORECASE | re.MULTILINE)
    if not match:
        return raw_answer.strip(), chunks

    clean_answer = raw_answer[:match.start()].strip()
    cited_str    = match.group(1).strip()

    if cited_str.lower() == "none" or not cited_str:
        return clean_answer, []

    cited_chunks = []
    for part in cited_str.split(","):
        m = re.search(r'\d+', part.strip())
        if m:
            idx = int(m.group()) - 1  # 1-based → 0-based
            if 0 <= idx < len(chunks):
                cited_chunks.append(chunks[idx])

    # Fallback: if parsing yielded nothing, return all chunks
    return clean_answer, cited_chunks if cited_chunks else chunks


def _similarity_search(query: str, k: int = NUM_CHUNKS, where: dict = None) -> list[Document]:
    """Query ChromaDB and return LangChain Document objects."""
    n = min(k, collection.count())
    if n == 0:
        return []
    kwargs: dict = {"query_texts": [query], "n_results": n, "include": ["documents", "metadatas"]}
    if where:
        kwargs["where"] = where
    results = collection.query(**kwargs)
    return [Document(page_content=t, metadata=m)
            for t, m in zip(results["documents"][0], results["metadatas"][0])]


def _similarity_search_with_score(query: str, k: int = NUM_CHUNKS) -> list[tuple[Document, float]]:
    """Query ChromaDB and return (Document, distance) tuples."""
    n = min(k, collection.count())
    if n == 0:
        return []
    results = collection.query(query_texts=[query], n_results=n,
                               include=["documents", "metadatas", "distances"])
    return [(Document(page_content=t, metadata=m), d)
            for t, m, d in zip(results["documents"][0], results["metadatas"][0], results["distances"][0])]


# ── Scope detection ──────────────────────────────────────────────────────────

_SCOPE_CANDIDATE_K      = 12
_SCORE_COMPETITION_GAP  = 0.35  # L2 distance margin — sources within this gap of the
                                # top chunk are considered genuinely competitive
_MIN_RELEVANCE_SCORE    = 0.50  # Skip clarification entirely if the best chunk is
                                # worse than this — no doc truly contains the answer
_DOMINANCE_RATIO        = 0.25  # If (runner-up - top) / top >= this ratio the top doc
                                # is dominant enough to skip clarification

# Words that occur in many filenames and carry no distinguishing meaning.
# Used by _extract_distinctive_keywords to avoid matching on 'manual', 'procedure', etc.
_FILENAME_STOP_WORDS = {
    "sop", "manual", "operation", "operations", "operator", "procedure",
    "schedule", "log", "inspection", "report", "document", "documents",
    "guide", "guidelines", "instruction", "instructions", "basic", "ref",
    "reference", "overview", "pdf", "doc", "txt", "md", "csv", "tsv",
    "html", "htm", "json", "docx",
}


def _extract_distinctive_keywords(filename: str) -> set:
    """Pull meaningful words from a filename, dropping generic filler.

    Example: 'Forklift_Operation_Manual.pdf' → {'forklift'}
    """
    stem  = Path(filename).stem.lower()
    words = set(stem.replace("-", " ").replace("_", " ").split())
    # drop pure numbers (e.g. '001', '002', '2025')
    words = {w for w in words if not w.isdigit()}
    return words - _FILENAME_STOP_WORDS


def _display_name(filename: str) -> str:
    """'SOP-001-Assembly-Line-Startup.txt' → 'SOP-001 Assembly Line Startup'"""
    return Path(filename).stem.replace("-", " ").replace("_", " ")


def _build_clarification_options(sources: list) -> list:
    options = [{"label": _display_name(s), "value": s} for s in sources]
    options.append({"label": "All relevant documents", "value": "__all__"})
    return options


def _build_clarification_question(sources: list) -> str:
    names = [f'"{_display_name(s)}"' for s in sources[:3]]
    more  = f" (and {len(sources) - 3} more)" if len(sources) > 3 else ""
    if len(names) == 1:
        doc_list = names[0]
    elif len(names) == 2:
        doc_list = f"{names[0]} and {names[1]}"
    else:
        doc_list = f"{names[0]}, {names[1]}, and {names[2]}"
    return (
        f"I found relevant content in multiple documents: {doc_list}{more}. "
        f"Which one are you asking about, or would you like me to check all relevant documents?"
    )


def _detect_scope(message: str, session_id: str) -> tuple:
    """
    Determine retrieval scope. Returns (scope, data):
      ("pass",            None)             — proceed with full chain as-is
      ("broad",           None)             — explicit multi-doc synthesis
      ("ambiguous",       [filenames])      — multiple docs match, needs clarification
      ("resolved_single", (file, orig_q))  — clarification resolved to one doc
      ("resolved_all",    orig_q)          — clarification resolved to all docs
    """
    msg_lower = message.lower().strip()
    session   = conversation_sessions.get(session_id, {})
    pending   = session.get("pending_clarification")

    # 1 — Resolve a pending clarification
    if pending:
        for opt in pending["options"]:
            if message.strip().lower() == opt["label"].lower():
                session["pending_clarification"] = None
                orig = pending["original_question"]
                if opt["value"] == "__all__":
                    return ("resolved_all", orig)
                return ("resolved_single", (opt["value"], orig))
        # User asked something new — clear pending and fall through
        session["pending_clarification"] = None

    # 2 — Explicit broad intent
    if any(phrase in msg_lower for phrase in BROAD_INTENT_PHRASES):
        return ("broad", None)

    # 3 — Candidate retrieval + score-based competition check
    candidates = _similarity_search_with_score(message, k=_SCOPE_CANDIDATE_K)
    if not candidates:
        return ("pass", None)

    # Track best (lowest L2) score and chunk list per source
    best_score:  dict = {}
    by_source:   dict = {}
    for doc, score in candidates:
        src = os.path.basename(doc.metadata.get("source", "unknown"))
        by_source.setdefault(src, []).append(doc)
        if src not in best_score or score < best_score[src]:
            best_score[src] = score

    if len(by_source) <= 1:
        return ("pass", None)

    top_score = min(best_score.values())

    # If user explicitly named a document (full stem), skip clarification
    for src in by_source:
        stem = Path(src).stem.lower()
        if stem in msg_lower or stem.replace("-", " ") in msg_lower or stem.replace("_", " ") in msg_lower:
            return ("pass", None)

    # Partial keyword match — if a distinctive word from exactly one filename
    # appears in the query AND that document is the best (or near-best) scorer
    # AND that keyword doesn't appear in the retrieved chunks of other sources
    # (which would mean it's a generic cross-cutting term, not a distinctive
    # entity name like "forklift" or "HPM100").
    msg_words = set(msg_lower.split())
    keyword_matches: dict = {}          # src → set of matched keywords
    for src in by_source:
        keywords = _extract_distinctive_keywords(src)
        overlap  = keywords & msg_words
        if overlap:
            keyword_matches[src] = overlap
    if len(keyword_matches) == 1:
        matched_src   = next(iter(keyword_matches))
        matched_score = best_score[matched_src]
        matched_kw    = keyword_matches[matched_src]
        # Verify the keyword is truly distinctive: it should NOT appear in the
        # retrieved text of other competing sources.  If it does, the term is a
        # generic topic many docs share and shouldn't shortcut the decision.
        other_text = " ".join(
            doc.page_content.lower()
            for src2, docs in by_source.items() if src2 != matched_src
            for doc in docs
        )
        kw_in_others = any(kw in other_text for kw in matched_kw)
        if not kw_in_others and matched_score <= top_score + 0.05:
            return ("pass", None)

    # If even the best match is a poor semantic fit, skip clarification — no doc
    # truly contains the answer so disambiguation wouldn’t help.
    if top_score >= _MIN_RELEVANCE_SCORE:
        return ("pass", None)
    # Dominance check — if the top doc's score is substantially better than the
    # runner-up (by ratio), one doc clearly owns this query.
    sorted_scores = sorted(best_score.values())
    if len(sorted_scores) >= 2 and top_score > 0:
        runner_up = sorted_scores[1]
        if (runner_up - top_score) / top_score >= _DOMINANCE_RATIO:
            return ("pass", None)
    competitive  = [s for s, sc in best_score.items() if sc <= top_score + _SCORE_COMPETITION_GAP]

    if len(competitive) >= 2:
        ranked = sorted(competitive, key=lambda s: best_score[s])
        return ("ambiguous", ranked)

    return ("pass", None)


def _evict_stale_sessions() -> None:
    """Remove sessions that have been idle longer than SESSION_TTL_SECONDS."""
    now     = time.monotonic()
    stale   = [sid for sid, s in conversation_sessions.items()
               if now - s.get("last_accessed", now) > SESSION_TTL_SECONDS]
    for sid in stale:
        conversation_sessions.pop(sid, None)


def _answer_single_doc(question: str, filename: str, session_id: str):
    """Retrieve chunks from a specific file using ChromaDB metadata filter."""
    doc_chunks = _similarity_search(
        question,
        k=NUM_CHUNKS,
        where={"source": str(KNOWLEDGE_BASE_DIR / filename)},
    )

    if not doc_chunks:
        return jsonify({
            "reply":      f'The document "{_display_name(filename)}" does not appear to contain information about this.',
            "session_id": session_id,
            "metadata":   {"sources": []},
        })

    context          = _build_numbered_context(doc_chunks)
    result           = llm.invoke(QA_PROMPT.format(context=context, question=question))
    answer, used_chunks = _parse_citations(result.content, doc_chunks)

    sources = []
    for i, doc in enumerate(used_chunks, 1):
        src     = doc.metadata.get("source", "Unknown")
        page    = doc.metadata.get("page", 0)
        snippet = doc.page_content[:150].replace("\n", " ")
        if len(doc.page_content) > 150:
            snippet += "..."
        sources.append({
            "id":      i,
            "file":    os.path.basename(src),
            "page":    page + 1,
            "snippet": snippet,
        })

    return jsonify({
        "reply":      answer,
        "session_id": session_id,
        "metadata":   {"sources": sources},
    })


def _answer_multi_doc(question: str, session_id: str):
    """Retrieve chunks balanced across sources and synthesize with multi-doc prompt."""
    # Scale k with the number of known documents so every doc gets fair representation.
    # Cap total chunks at MAX_MULTI_DOC_CHUNKS to stay within the LLM context window.
    num_docs       = max(1, len(_load_doc_registry()))
    pool_k         = min(num_docs * 5, 80)            # retrieve a wide pool
    chunks_per_src = max(2, MAX_MULTI_DOC_CHUNKS // num_docs)  # balance per source
    candidates     = _similarity_search(question, k=pool_k)
    by_source: dict = {}
    for doc in candidates:
        src = os.path.basename(doc.metadata.get("source", "unknown"))
        if src not in by_source:
            by_source[src] = []
        if len(by_source[src]) < chunks_per_src:
            by_source[src].append(doc)

    context_parts: list = []
    all_chunks:    list = []
    chunk_num = 1
    for src, chunks in by_source.items():
        context_parts.append(f"[Source: {src}]")
        for chunk in chunks:
            context_parts.append(f"[CHUNK {chunk_num}]\n{chunk.page_content}")
            all_chunks.append(chunk)
            chunk_num += 1
        context_parts.append("")

    result = llm.invoke(_MULTI_DOC_QA_TEMPLATE.format(
        context="\n".join(context_parts),
        question=question,
    ))
    answer, used_chunks = _parse_citations(result.content, all_chunks)

    sources = []
    for i, doc in enumerate(used_chunks, 1):
        src     = doc.metadata.get("source", "Unknown")
        page    = doc.metadata.get("page", 0)
        snippet = doc.page_content[:150].replace("\n", " ")
        if len(doc.page_content) > 150:
            snippet += "..."
        sources.append({
            "id":      i,
            "file":    os.path.basename(src),
            "page":    page + 1,
            "snippet": snippet,
        })

    return jsonify({
        "reply":      answer,
        "session_id": session_id,
        "metadata":   {"sources": sources},
    })


# ── Helper: manual conversational RAG pipeline ───────────────────────────────
def _chat_with_memory(question: str, session_id: str) -> tuple[str, list[Document]]:
    """
    Manual replacement for ConversationalRetrievalChain.
    1. Condense follow-up questions using CONDENSE_PROMPT + chat history.
    2. Retrieve top-k chunks from ChromaDB.
    3. Answer with QA_PROMPT (strict grounding).
    4. Save to ConversationBufferMemory for next turn.
    """
    session = conversation_sessions.setdefault(session_id, {})
    session["last_accessed"] = time.monotonic()

    if "memory" not in session:
        session["memory"] = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=False,
        )

    memory      = session["memory"]
    chat_history = memory.load_memory_variables({}).get("chat_history", "")

    # Step 1: Condense follow-up question into standalone form if needed
    if chat_history:
        condensed = llm.invoke(
            CONDENSE_PROMPT.format(chat_history=chat_history, question=question)
        ).content.strip()
    else:
        condensed = question

    # Step 2: Retrieve relevant chunks
    chunks = _similarity_search(condensed, k=NUM_CHUNKS)
    if not chunks:
        answer = "The uploaded documents do not contain information about this."
        memory.save_context({"input": question}, {"output": answer})
        return answer, []

    # Step 3: Answer strictly from retrieved context
    context   = _build_numbered_context(chunks)
    raw       = llm.invoke(QA_PROMPT.format(context=context, question=condensed)).content
    answer, chunks = _parse_citations(raw, chunks)

    # Step 4: Persist turn to memory
    memory.save_context({"input": question}, {"output": answer})
    return answer, chunks


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

        # Evict idle sessions to prevent unbounded memory growth
        _evict_stale_sessions()

        # Lazy-init ChromaDB collection
        if collection is None:
            ok, msg = _init_store()
            if not ok:
                return jsonify({
                    "reply":      "The assistant isn't ready yet. Please upload a document first.",
                    "session_id": session_id,
                    "metadata":   {"sources": []},
                }), 503

        # Guard: no documents uploaded yet
        if collection.count() == 0:
            return jsonify({
                "reply":      "No documents have been uploaded yet. Please upload a document using the sidebar before asking questions.",
                "session_id": session_id,
                "metadata":   {"sources": []},
            })

        # Guard: block personal/off-topic questions BEFORE retrieval runs
        if _is_off_topic(message):
            return jsonify({
                "reply":      "I can only answer questions about the uploaded documents.",
                "session_id": session_id,
                "metadata":   {"sources": []},
            })

        # ── Scope detection ──────────────────────────────────────────────────────
        scope, scope_data = _detect_scope(message, session_id)

        if scope == "ambiguous":
            options  = _build_clarification_options(scope_data)
            question = _build_clarification_question(scope_data)
            conversation_sessions.setdefault(session_id, {})["pending_clarification"] = {
                "original_question": message,
                "options":           options,
            }
            return jsonify({
                "reply":      question,
                "session_id": session_id,
                "metadata":   {
                    "sources":       [],
                    "clarification": {"question": question, "options": options},
                },
            })

        if scope in ("broad", "resolved_all"):
            return _answer_multi_doc(scope_data if scope == "resolved_all" else message, session_id)

        if scope == "resolved_single":
            filename, original_q = scope_data
            return _answer_single_doc(original_q, filename, session_id)

        # ── Default: manual conversational RAG pipeline ─────────────────────────
        answer, source_docs = _chat_with_memory(message, session_id)

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
                "page":    page + 1,
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

    # Ensure ChromaDB collection is initialised before ingestion
    if collection is None:
        ok, msg = _init_store()
        if not ok:
            filepath.unlink(missing_ok=True)
            return jsonify({"success": False, "message": msg}), 503

    ok, msg, chunk_count = _ingest_file(filepath)
    if not ok:
        filepath.unlink(missing_ok=True)
        return jsonify({"success": False, "message": msg}), 500

    # Update registry
    registry = _load_doc_registry()
    registry[filename] = {"chunks": chunk_count, "uploaded_at": datetime.now(timezone.utc).isoformat()}
    _save_doc_registry(registry)

    # Clear sessions so they don't use stale context
    conversation_sessions.clear()

    return jsonify({"success": True, "message": msg, "filename": filename, "chunks": chunk_count})


@app.route("/api/documents/<filename>", methods=["DELETE"])
def delete_document(filename: str):
    """
    Delete a document file and remove its vectors from ChromaDB.
    ChromaDB supports selective deletion by metadata — no full index rebuild needed.
    """
    registry = _load_doc_registry()
    if filename not in registry:
        return jsonify({"success": False, "message": "Document not found"}), 404

    # Remove the file from disk
    (KNOWLEDGE_BASE_DIR / filename).unlink(missing_ok=True)

    # Remove from registry
    del registry[filename]
    _save_doc_registry(registry)

    # Selectively delete only this document's vectors — no rebuild required
    collection.delete(where={"source": str(KNOWLEDGE_BASE_DIR / filename)})

    # Clear sessions so memory doesn't reference deleted content
    conversation_sessions.clear()

    return jsonify({"success": True, "message": f"{filename} deleted successfully."})


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
    has_api_key  = bool(os.getenv("OPENAI_API_KEY"))
    has_docs     = collection is not None and collection.count() > 0
    return jsonify({
        "status":          "healthy",
        "has_documents":   has_docs,
        "has_api_key":     has_api_key,
        "ready":           has_docs and has_api_key and collection is not None,
        "active_sessions": len(conversation_sessions),
    })


# ── Startup ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  Kuldeep RAG Chatbot  —  Flask Backend (ChromaDB)")
    print("=" * 60)
    _init_store()   # best-effort on startup; 
    print("  Open: http://localhost:5000")
    print("=" * 60 + "\n")
    app.run(debug=True, host="0.0.0.0", port=5000)

