"""
ingest.py — Batch PDF ingestion script
=======================================
Use this to pre-load PDFs into the vector database before starting the server,
or to re-build the database after manual changes to the knowledge_base/ folder.

Usage:
    python ingest.py                          # ingest all PDFs in knowledge_base/
    python ingest.py path/to/document.pdf     # ingest a single PDF
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime, timezone

from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

load_dotenv()

KNOWLEDGE_BASE_DIR = Path("knowledge_base")
CHROMA_DB_DIR      = "chroma_db"
DOCUMENTS_JSON     = KNOWLEDGE_BASE_DIR / "documents.json"
CHUNK_SIZE         = 1000
CHUNK_OVERLAP      = 200


def load_registry() -> dict:
    if DOCUMENTS_JSON.exists():
        return json.loads(DOCUMENTS_JSON.read_text())
    return {}


def save_registry(registry: dict) -> None:
    DOCUMENTS_JSON.write_text(json.dumps(registry, indent=2))


def ingest_pdfs(pdf_paths: list[Path]) -> None:
    if not os.getenv("OPENAI_API_KEY"):
        print("❌  OPENAI_API_KEY not set. Add it to your .env file.")
        sys.exit(1)

    print(f"\n{'='*60}")
    print("  Collective RAG — Batch Ingestion")
    print(f"{'='*60}\n")

    splitter   = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    embeddings = OpenAIEmbeddings(model="text-embedding-ada-002")
    registry   = load_registry()
    all_chunks = []

    for pdf in pdf_paths:
        print(f"📄  Loading: {pdf.name}")
        loader = PyPDFLoader(str(pdf))
        docs   = loader.load()
        chunks = splitter.split_documents(docs)
        all_chunks.extend(chunks)
        registry[pdf.name] = {
            "chunks":      len(chunks),
            "uploaded_at": datetime.now(timezone.utc).isoformat(),
        }
        print(f"    → {len(chunks)} chunks")

    if not all_chunks:
        print("⚠️  No chunks to ingest.")
        return

    print(f"\n🔧  Embedding {len(all_chunks)} total chunks into Chroma DB …")

    if os.path.exists(CHROMA_DB_DIR):
        store = Chroma(persist_directory=CHROMA_DB_DIR, embedding_function=embeddings)
        store.add_documents(all_chunks)
    else:
        Chroma.from_documents(all_chunks, embedding=embeddings, persist_directory=CHROMA_DB_DIR)

    save_registry(registry)
    print(f"\n✅  Done! {len(all_chunks)} chunks stored in {CHROMA_DB_DIR}/")
    print(f"    Registry updated: {DOCUMENTS_JSON}\n")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Specific file(s) provided as arguments
        pdfs = [Path(p) for p in sys.argv[1:]]
        missing = [p for p in pdfs if not p.exists()]
        if missing:
            print(f"❌  Files not found: {missing}")
            sys.exit(1)
    else:
        # Default: ingest everything in knowledge_base/
        pdfs = sorted(KNOWLEDGE_BASE_DIR.glob("*.pdf"))
        if not pdfs:
            print(f"⚠️  No PDFs found in {KNOWLEDGE_BASE_DIR}/")
            print("    Place PDF files there and re-run, or upload via the web UI.")
            sys.exit(0)

    ingest_pdfs(pdfs)

