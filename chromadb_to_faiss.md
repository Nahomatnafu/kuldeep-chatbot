# ChromaDB → FAISS Migration

## Why We Switched

When merging all branches into `collective-experiment`, we pinned `chromadb==0.6.3`
(the latest version). ChromaDB 0.6.x replaced its `hnswlib` dependency with a fork
called `chroma-hnswlib`. That fork ships **source-only on Windows** — meaning pip
must compile it from C++ source code, which requires Microsoft Visual C++ Build Tools.

```
chromadb 0.4/0.5  →  depends on hnswlib       →  pre-built Windows wheels ✅
chromadb 0.6.3    →  depends on chroma-hnswlib →  no Windows wheels, needs C++ ❌
```

Our individual chatbots worked fine because they used older ChromaDB versions that
had pre-built wheels. The merged project used 0.6.3, which broke `pip install` for
every teammate on Windows without Visual Studio installed.

Rather than require all teammates to download the C++ Build Tools (~1.5 GB), we
switched to **FAISS** (`faiss-cpu`), which has always shipped pre-built wheels on
Windows, macOS, and Linux.

## What Changed

### `backend/requirements.txt`
```
# Before
chromadb==0.6.3

# After
faiss-cpu==1.10.0
```

### `backend/app.py`
| Location | Before | After |
|---|---|---|
| Import | `from langchain_community.vectorstores import Chroma` | `from langchain_community.vectorstores import FAISS` |
| DB directory constant | `CHROMA_DB_DIR = "chroma_db"` | `FAISS_DB_DIR = "faiss_db"` |
| Global type hint | `vectorstore: Chroma \| None` | `vectorstore: FAISS \| None` |
| Load store | `Chroma(persist_directory=..., embedding_function=embeddings)` | `FAISS.load_local(FAISS_DB_DIR, embeddings, allow_dangerous_deserialization=True)` |
| Create store | `Chroma.from_documents(chunks, embedding=embeddings, persist_directory=...)` | `FAISS.from_documents(chunks, embedding=embeddings).save_local(FAISS_DB_DIR)` |
| Add documents | `store.add_documents(chunks)` (auto-persists) | `store.add_documents(chunks)` + `store.save_local(FAISS_DB_DIR)` |
| Delete + rebuild | `Chroma.from_documents(..., persist_directory=...)` | `FAISS.from_documents(...).save_local(FAISS_DB_DIR)` |
| Health check | `os.path.exists(CHROMA_DB_DIR)` | `os.path.exists(FAISS_DB_DIR)` |

## Does It Affect Answer Quality?

No. The RAG pipeline is otherwise identical:

```
PDF → chunks → OpenAI embeddings → [FAISS index] → top-6 chunks → GPT-3.5-turbo → answer
```

Answer quality comes from the OpenAI embeddings and the prompt, not the vector store.
FAISS is used in many production RAG systems and is maintained by Meta AI Research.

## One Behaviour Difference

FAISS does not support selective deletion by metadata. Deleting a document requires
rebuilding the entire index from the remaining PDFs. Our delete endpoint already
handles this — it was the same limitation with ChromaDB 0.6 in this codebase.

