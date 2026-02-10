# RAG Experiment Progress Log

## Session 1 - 2026-02-10

### ✅ What We Accomplished Today

#### 1. Project Setup
- ✅ Created isolated experiment branch: `rag-experiment-nahom`
- ✅ Set up minimal project structure:
  ```
  knowledge_base/experimental_pdfs_nahom/  # 2 research PDFs
  src/
    ├── ingest.py                          # PDF → Vector DB pipeline
    └── query.py                           # Q&A interface
  requirements.txt                          # Dependencies
  .env                                      # API keys (gitignored)
  .gitignore                                # Security
  ```
- ✅ Installed dependencies: LangChain, Chroma, OpenAI, PyPDF

#### 2. Document Ingestion (`ingest.py`)
- ✅ Loaded 2 PDFs (10 pages total)
- ✅ Split into 67 chunks (1000 chars, 200 overlap)
- ✅ Created embeddings using OpenAI (`text-embedding-ada-002`)
- ✅ Stored in Chroma vector database (`chroma_db/`)

**Key Configuration:**
```python
CHUNK_SIZE = 1000        # Characters per chunk
CHUNK_OVERLAP = 200      # Overlap to preserve context
```

#### 3. Query Interface (`query.py`)
- ✅ Built interactive Q&A system
- ✅ Retrieves 6 most relevant chunks per question
- ✅ Uses GPT-3.5-turbo for answer generation
- ✅ Shows retrieved chunks for transparency

**Features:**
- Interactive mode: Ask multiple questions
- Single question mode: `python src/query.py "your question"`
- Displays retrieved text snippets (first 200 chars)

#### 4. Grounding Improvements
- ✅ Implemented strict grounding rules in prompt:
  1. Answer ONLY from retrieved context
  2. Every claim must be traceable to chunks
  3. Say "I don't know" if context is insufficient
  4. No inference or extrapolation
  5. List only explicitly named items
  6. Acknowledge limitations for broad questions
  7. Summarize chunks, don't write essays

- ✅ Added transparent retrieval display
- ✅ Increased chunks from 4 → 6 for better coverage

#### 5. Testing & Validation
**Successful Test Cases:**
- ✅ "What is SpectTTTra and what are its variants?"
  - Retrieved perfect chunks
  - Answer listed all 3 variants with exact parameters
  - Fully grounded in context

- ✅ "What baseline models are used in the broadcast monitoring paper?"
  - Direct quote: "CNN baseline and SpectTTTra models"
  - Grounded answer

**Lessons Learned:**
- Specific questions → better retrieval → better answers
- Generic questions → generic chunks → vague answers
- Retrieval quality is the bottleneck

---

## 🎓 Key Learnings

### RAG Pipeline Understanding
1. **Chunking** - Split documents into searchable pieces
2. **Embeddings** - Convert text to vectors for similarity search
3. **Vector DB** - Store and search embeddings efficiently
4. **Retrieval** - Find most relevant chunks for a question
5. **Generation** - LLM creates answer from retrieved context

### Critical Success Factors
- ✅ **Grounding is critical** - Strict prompts prevent hallucination
- ✅ **Transparency helps** - Showing chunks enables debugging
- ✅ **Question quality matters** - Specific questions get specific answers
- ✅ **Retrieval = bottleneck** - Bad chunks → bad answers (see below)

---

## 🔍 Understanding "Bad Chunks" vs "Good Chunks"

### What Makes a Chunk "Bad"?

A chunk is "bad" when it **doesn't contain the information needed to answer the question**, even though the vector search thinks it's relevant.

#### Example from Today:

**Question:** "List the models explicitly named in the retrieved context only."

**Retrieved Chunks (BAD):**
```
"that the model works by detecting artefacts specific to each AE..."
"we may not need to include all possible parametrisation of an AE..."
"independently of its musical content? Another difficulty is..."
```

**Problem:** These chunks talk about "the model" generically, but don't name specific models like "CNN", "SpectTTTra", "Encodec", etc.

**Result:** The LLM either:
- Hallucinates model names
- Gives a vague answer
- Says "I don't know" (if well-grounded)

---

### What Makes a Chunk "Good"?

A chunk is "good" when it **directly contains the answer** to the question.

#### Example from Today:

**Question:** "What is SpectTTTra and what are its variants?"

**Retrieved Chunks (GOOD):**
```
[1] "...can be distinguished by the size of their spectral (f) and 
     temporal (t) patches: SpectTTTra-α(f= 1, t= 3), 
     SpectTTTra-β(f= 3, t= 5), and SpectTTTra-γ(f= 5, t= 7)..."

[4] "a simple CNN baseline and the state-of-the-art SpectTTTra 
     models, experience a substantial drop in performance..."
```

**Why Good:**
- ✅ Contains exact answer (all 3 variants with parameters)
- ✅ Provides context ("state-of-the-art")
- ✅ Directly relevant to the question

**Result:** Perfect, grounded answer!

---

### How to Find Good Chunks (Strategies for Tomorrow)

#### 1. **Adjust Chunk Size**
**Current:** 1000 characters

**Problem:** Might be too large, mixing multiple topics in one chunk

**Solution to try:**
```python
CHUNK_SIZE = 500         # Smaller, more focused chunks
CHUNK_OVERLAP = 100      # Proportional overlap
```

**Trade-off:**
- ✅ More precise retrieval
- ❌ More chunks = higher cost
- ❌ Might split important context

---

#### 2. **Improve Chunking Strategy**
**Current:** `RecursiveCharacterTextSplitter` (splits by characters)

**Better options:**
- Split by **paragraphs** (semantic boundaries)
- Split by **sections** (if PDFs have clear structure)
- Use **semantic chunking** (LangChain has this)

**Example:**
```python
from langchain.text_splitter import MarkdownHeaderTextSplitter
# Splits by headers, preserving document structure
```

---

#### 3. **Increase Retrieved Chunks**
**Current:** 6 chunks

**Try:** 8-10 chunks for complex questions

**Trade-off:**
- ✅ Better coverage
- ❌ More noise (irrelevant chunks)
- ❌ Higher cost (more tokens to LLM)

---

#### 4. **Hybrid Search (Advanced)**
**Current:** Pure semantic search (embeddings only)

**Better:** Combine semantic + keyword search

**Example:**
```python
# Retrieve chunks that:
# 1. Are semantically similar (embeddings)
# 2. Contain specific keywords (e.g., "SpectTTTra", "CNN")
```

**Benefit:** Ensures chunks with specific terms are retrieved

---

#### 5. **Add Metadata to Chunks**
**Current:** Only page number

**Better:** Add section, heading, chunk type

**Example:**
```python
chunk.metadata = {
    "source": "paper.pdf",
    "page": 3,
    "section": "Methods",      # NEW
    "heading": "Model Architecture",  # NEW
}
```

**Benefit:** Can filter retrieval by section

---

#### 6. **Test Retrieval Quality**
**Create a test set:**
```python
test_questions = [
    ("What is SpectTTTra?", "Should retrieve page 3 chunks"),
    ("What models are used?", "Should retrieve CNN, SpectTTTra mentions"),
    ("What is the accuracy?", "Should retrieve 99.8% mention"),
]
```

**For each question:**
1. Run retrieval
2. Manually check if chunks contain the answer
3. If not → adjust chunking/retrieval strategy

---

## 📋 Tomorrow's Tasks

### Priority 1: Testing & Evaluation
- [ ] Create a test set of 5-10 questions
- [ ] For each question, evaluate:
  - Are retrieved chunks relevant?
  - Does the answer match the chunks?
  - Is the answer grounded (no hallucination)?
- [ ] Document findings

### Priority 2: Chunk Quality Improvements
- [ ] Experiment with smaller chunk size (500 chars)
- [ ] Try different chunking strategies
- [ ] Compare retrieval quality before/after

### Priority 3: Answer Generation Improvements
- [ ] Add chunk citations in answers (e.g., "[1][2]")
- [ ] Improve answer formatting
- [ ] Add confidence indicators

### Priority 4: Documentation
- [ ] Document learnings for manufacturing chatbot
- [ ] Create "lessons learned" summary
- [ ] Identify what to apply to production system

---

## 🚀 Ready for Manufacturing Chatbot

### What Transfers Directly:
1. ✅ Strict grounding prompt pattern
2. ✅ Transparent retrieval (show chunks)
3. ✅ Chunk size/overlap tuning process
4. ✅ Test-driven evaluation approach

### What Needs Adaptation:
1. ⚠️ Different document types (manufacturing docs vs research papers)
2. ⚠️ Possibly longer documents (manuals, specs)
3. ⚠️ Different question types (troubleshooting vs research)
4. ⚠️ Multi-document retrieval (multiple manuals)

---

## 📊 Current System Stats

- **Documents:** 2 PDFs (10 pages)
- **Chunks:** 67 chunks
- **Chunk Size:** 1000 characters
- **Overlap:** 200 characters
- **Retrieval:** 6 chunks per query
- **Embedding Model:** OpenAI text-embedding-ada-002
- **LLM:** GPT-3.5-turbo
- **Vector DB:** Chroma (local, persistent)

---

## 🔗 Resources

- **Branch:** `rag-experiment-nahom`
- **PDFs:** `knowledge_base/experimental_pdfs_nahom/`
- **Code:** `src/ingest.py`, `src/query.py`
- **Database:** `chroma_db/` (gitignored)

---

**Next Session:** Continue with testing, chunk optimization, and documentation!

