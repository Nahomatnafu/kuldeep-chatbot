"""
Batch document ingestion script.

Uses the same ingestion pipeline as the Flask app so uploaded and preloaded
documents get identical metadata, section-aware chunks, and embedding settings.

Usage:
    python backend/ingest.py
    python backend/ingest.py knowledge_base/document.pdf
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import app as app_module


def _discover_files() -> list[Path]:
    files: list[Path] = []
    for ext in app_module.ALLOWED_EXTENSIONS:
        files.extend(app_module.KNOWLEDGE_BASE_DIR.glob(f"*{ext}"))
    return sorted(p for p in files if p.resolve() != app_module.DOCUMENTS_JSON.resolve())


def ingest_files(file_paths: list[Path]) -> int:
    ok, msg = app_module._init_store()
    if not ok:
        print(f"ERROR: {msg}")
        return 1

    print("\n" + "=" * 60)
    print("  Kuldeep RAG - Batch Ingestion")
    print("=" * 60)
    print(f"Embedding model: {app_module.EMBEDDING_MODEL}")
    print(f"Collection:      {app_module.COLLECTION_NAME}\n")

    registry = app_module._load_doc_registry()
    total_chunks = 0

    for filepath in file_paths:
        print(f"Loading: {filepath.name}")
        ok, message, chunk_count = app_module._ingest_file(filepath)
        if not ok:
            print(f"  ERROR: {message}")
            continue

        docs = app_module._load_docs(filepath)
        meta = app_module._derive_doc_metadata(filepath, docs)
        registry[filepath.name] = {
            "chunks": chunk_count,
            "uploaded_at": datetime.now(timezone.utc).isoformat(),
            "doc_type": meta.get("doc_type", ""),
            "revision": meta.get("revision", ""),
            "status": meta.get("status", ""),
            "embedding_model": app_module.EMBEDDING_MODEL,
        }
        total_chunks += chunk_count
        print(f"  {message}")

    app_module._save_doc_registry(registry)
    print(f"\nDone. Stored {total_chunks} chunk(s).")
    print(f"Registry updated: {app_module.DOCUMENTS_JSON}\n")
    return 0


if __name__ == "__main__":
    if len(sys.argv) > 1:
        files = [Path(p) for p in sys.argv[1:]]
        missing = [p for p in files if not p.exists()]
        if missing:
            print(f"ERROR: Files not found: {[str(p) for p in missing]}")
            sys.exit(1)
        unsupported = [p for p in files if p.suffix.lower() not in app_module.ALLOWED_EXTENSIONS]
        if unsupported:
            print(f"ERROR: Unsupported file types: {[p.name for p in unsupported]}")
            print(f"Allowed: {', '.join(sorted(app_module.ALLOWED_EXTENSIONS))}")
            sys.exit(1)
    else:
        files = _discover_files()
        if not files:
            print(f"No supported files found in {app_module.KNOWLEDGE_BASE_DIR}.")
            sys.exit(0)

    sys.exit(ingest_files(files))
