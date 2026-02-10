# RAG Experiment - Learning Branch

**Branch:** `rag-experiment-nahom`

**Purpose:** Experimental branch for learning RAG (Retrieval-Augmented Generation) systems while waiting for client's manufacturing knowledge base.

---

## Scope (IMPORTANT - No Scope Creep!)

This branch experiments with a simple RAG chatbot over two research PDFs.

### ✅ What This IS:
- **Input:** 2 PDF research articles (provided)
- **Output:** Text-based Q&A only
- **Execution:** Local execution
- **Goal:** Learn RAG fundamentals with minimal implementation

### ❌ What This is NOT:
- ❌ No UI polish
- ❌ No authentication
- ❌ No memory beyond one question (no conversation history)
- ❌ No fine-tuning
- ❌ No production-ready features
- ❌ No deployment considerations

---

## Constraints

1. **Minimalistic approach only**
2. **Single-turn Q&A** (ask question → get answer → done)
3. **2 PDFs maximum** for this experiment
4. **Text-based interface** (CLI or simple endpoint)

---

## Learning Objectives

- Understand PDF text extraction
- Learn document chunking strategies
- Implement basic vector embeddings
- Set up simple vector storage
- Create basic retrieval mechanism
- Integrate with LLM for answer generation

---

## PDFs Used

Located in: `knowledge_base/experimental_pdfs_nahom/`

1. **AI-Generated Music Detection and Its Challenges**
   - File: `ai_generated_music_detection_and_its_challenges.pdf`

2. **AI-Generated Music Detection in Broadcast Monitoring**
   - File: `ai_generated_music_detection_in_brodcast_monitoring.pdf`

## Tech Stack

Keeping it simple and focused for learning:

- **Language:** Python
- **RAG Framework:** LangChain (simpler mental model for RAG)
- **Vector Store:** Chroma (dead simple, persistent, no server needed)
- **Embeddings:** OpenAI embeddings
- **LLM:** OpenAI chat model
- **Interface:** CLI or minimal script

---

## Notes

- This branch is isolated from `main`
- All experiments stay here
- Main branch remains clean for client work
- Once client provides manufacturing knowledge base, we switch back to main branch work

