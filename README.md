# RAG Experiment - Nahom's Learning Branch

**Branch:** `rag-experiment-nahom`

A minimal RAG (Retrieval-Augmented Generation) chatbot experiment using 2 research PDFs about AI-generated music detection.

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment:**
   ```bash
   cp .env.example .env
   # Edit .env and add your OpenAI API key
   ```

3. **Run ingestion** (load PDFs into vector database):
   ```bash
   python src/ingest.py
   ```

4. **Ask questions:**
   ```bash
   python src/query.py
   ```

## Project Structure

```
knowledge_base/experimental_pdfs_nahom/  # Research PDFs
src/                                      # Source code
  ├── ingest.py                          # PDF → Chroma pipeline
  └── query.py                           # Q&A interface
requirements.txt                          # Python dependencies
.env                                      # API keys (not committed)
```

## Scope

- ✅ Text-based Q&A only
- ✅ 2 PDFs maximum
- ✅ Local execution
- ❌ No UI, no auth, no memory, no fine-tuning

## Tech Stack

- **LangChain** - RAG framework
- **Chroma** - Vector database
- **OpenAI** - Embeddings + LLM
- **Python** - Everything else

