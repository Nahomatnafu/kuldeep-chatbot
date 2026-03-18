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
import csv
import json
from pathlib import Path
from datetime import datetime, timezone

from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

load_dotenv()

KNOWLEDGE_BASE_DIR = Path("knowledge_base")
CHROMA_DB_DIR      = "chroma_db"
DOCUMENTS_JSON     = KNOWLEDGE_BASE_DIR / "documents.json"
CHUNK_SIZE         = 1000
CHUNK_OVERLAP      = 200
ALLOWED_EXTENSIONS = {".pdf", ".txt", ".md", ".json", ".docx", ".csv", ".tsv", ".html", ".htm"}


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


def load_registry() -> dict:
    if DOCUMENTS_JSON.exists():
        return json.loads(DOCUMENTS_JSON.read_text())
    return {}


def save_registry(registry: dict) -> None:
    DOCUMENTS_JSON.write_text(json.dumps(registry, indent=2))


def ingest_files(file_paths: list[Path]) -> None:
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

    for filepath in file_paths:
        print(f"📄  Loading: {filepath.name}")
        docs   = _load_docs(filepath)
        chunks = splitter.split_documents(docs)
        all_chunks.extend(chunks)
        registry[filepath.name] = {
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
        files = [Path(p) for p in sys.argv[1:]]
        missing = [p for p in files if not p.exists()]
        if missing:
            print(f"❌  Files not found: {missing}")
            sys.exit(1)
        unsupported = [p for p in files if p.suffix.lower() not in ALLOWED_EXTENSIONS]
        if unsupported:
            print(f"❌  Unsupported file types: {[p.name for p in unsupported]}")
            print(f"    Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}")
            sys.exit(1)
    else:
        # Default: ingest all supported files in knowledge_base/
        files = sorted(
            p for ext in ALLOWED_EXTENSIONS for p in KNOWLEDGE_BASE_DIR.glob(f"*{ext}")
        )
        if not files:
            ext_list = ", ".join(sorted(ALLOWED_EXTENSIONS))
            print(f"⚠️  No supported files found in {KNOWLEDGE_BASE_DIR}/")
            print(f"    Supported formats: {ext_list}")
            print("    Place files there and re-run, or upload via the web UI.")
            sys.exit(0)

    ingest_files(files)

