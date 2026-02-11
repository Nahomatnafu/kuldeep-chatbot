# PDF Q&A Chatbot - Experimental Learning Project

## 🎯 Project Purpose

This is a **learning/practice project** to build a simple AI chatbot that answers questions from PDF documents using RAG (Retrieval-Augmented Generation). This serves as a hands-on exploration before implementing a larger manufacturing AI chatbot with multi-document support.

## 📋 Project Scope

### Core Functionality
- **PDF Document Ingestion**: Upload and process PDF files
- **Vector Database Storage**: Store document embeddings for efficient retrieval
- **Question Answering**: Ask questions and get answers based on PDF content -- If an answer cant be made from the available documentation let user know
- **Simple Web UI**: Minimal interface for uploading PDFs and asking questions

### Learning Goals
- Understand RAG architecture and workflow
- Practice with vector databases and embeddings
- Experiment with document chunking strategies
- Learn prompt engineering for grounded answers
- Gain experience with PDF processing

## 🛠️ Recommended Tech Stack

### Primary Stack (Recommended)
- **Framework**: LangChain (abstracts RAG complexity)
- **Vector Database**: Chroma (lightweight, no server needed)
- **LLM**: OpenAI GPT-3.5-turbo or GPT-4
- **Embeddings**: OpenAI text-embedding-ada-002
- **PDF Processing**: PyPDF2 or LangChain's PDF loaders
- **Web UI**: Flask (minimal) or Streamlit (even simpler)
- **Language**: Python 3.9+

### Alternative Simplified Stack (If Primary is Too Complex)
- **Framework**: Direct OpenAI API calls with custom RAG logic
- **Vector Database**: FAISS (simpler than Chroma, no persistence by default)
- **Web UI**: Streamlit (one file, no HTML/CSS needed)
- **PDF Processing**: PyPDF2

### When to Simplify
- If setting up Chroma is taking too long → Use FAISS
- If LangChain abstractions are confusing → Use direct OpenAI API
- If Flask requires too much frontend work → Use Streamlit

## 🏗️ Project Structure

```
kuldeep-chatbot/
├── src/
│   ├── app.py              # Main Flask/Streamlit app
│   ├── ingest.py           # PDF processing & vectorization
│   ├── query.py            # RAG query logic
│   └── utils.py            # Helper functions
├── data/
│   └── pdfs/               # Uploaded PDF files
├── vector_db/              # Chroma/FAISS storage
├── static/                 # CSS/JS (if using Flask)
├── templates/              # HTML (if using Flask)
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## 🔄 Implementation Workflow

### Phase 1: Setup & PDF Ingestion
1. Set up Python environment and install dependencies
2. Create PDF loading script (ingest.py)
3. Implement document chunking (start with 500-1000 token chunks)
4. Generate embeddings and store in vector database
5. Test: Load a sample PDF and verify chunks are stored

### Phase 2: RAG Query Pipeline
1. Implement semantic search (retrieve top-k relevant chunks)
2. Create prompt template for LLM
3. Build query function that combines retrieval + generation
4. Test: Ask questions via command line and verify answers

### Phase 3: Simple Web UI
1. Create basic web interface
   - **Option A (Flask)**: Simple HTML form + result display
   - **Option B (Streamlit)**: Use built-in components
2. Add PDF upload functionality (optional for v1)
3. Add chat interface for asking questions
4. Display answers with source references

### Phase 4: Refinement (Optional)
1. Improve chunking strategy (experiment with overlap, size)
2. Add conversation memory (multi-turn chat)
3. Show source snippets with answers
4. Add error handling and loading states

## 🎯 Key Implementation Decisions

### Document Chunking
- **Start with**: 1000 characters per chunk, 200 character overlap
- **Why**: Balance between context and precision
- **Adjust if**: Answers are too vague (smaller chunks) or too fragmented (larger chunks)

### Retrieval Strategy
- **Start with**: Top 3-5 most relevant chunks
- **Why**: Enough context without overwhelming the LLM
- **Adjust if**: Missing info (increase k) or hallucinating (decrease k)

### Prompt Engineering
```
Template suggestion:
"Based on the following context from documents, answer the question. 
If the answer is not in the context, say 'I don't have enough information.'

Context: {retrieved_chunks}

Question: {user_question}

Answer:"
```

### UI Choice Decision Tree
- **Want fastest setup?** → Streamlit
- **Need custom design?** → Flask
- **Just testing RAG logic?** → Command line (no UI yet)

## 📦 Minimal Dependencies

```txt
# Core RAG
langchain
langchain-openai
chromadb
# or: faiss-cpu (alternative to chromadb)

# PDF Processing
pypdf2
# or: langchain already includes PDF loaders

# LLM
openai

# Web UI (pick one)
streamlit  # Easier option
# or
flask  # More control

# Utilities
python-dotenv
```

## 🚀 Getting Started Checklist

- [ ] Create virtual environment
- [ ] Install dependencies
- [ ] Set up OpenAI API key in .env
- [ ] Download sample PDF for testing
- [ ] Implement PDF ingestion script
- [ ] Test vectorization locally
- [ ] Implement basic query function
- [ ] Test Q&A from command line
- [ ] Build minimal UI
- [ ] Test end-to-end workflow

## 🧪 Testing Strategy

### Unit Testing
- PDF loader: Can it extract text from test PDF?
- Chunking: Are chunks reasonable size and overlap correctly?
- Embedding: Do similar chunks have high cosine similarity?
- Retrieval: Does semantic search return relevant chunks?

### Integration Testing
- Full pipeline: PDF → chunks → vectors → query → answer
- Edge cases: Empty PDFs, large PDFs, non-English text

### Manual Testing Questions
Prepare 5-10 questions with known answers from test PDF:
1. Direct fact questions (should retrieve exact info)
2. Inference questions (should synthesize from multiple chunks)
3. Out-of-scope questions (should say "not in document")

## 🎓 Learning Checkpoints

After completing this project, you should understand:
- ✅ How RAG differs from direct LLM prompting
- ✅ Why embedding similarity works for retrieval
- ✅ Trade-offs in chunk size and retrieval count
- ✅ How to prevent hallucination with grounding
- ✅ Basic vector database operations

## 🔜 Next Steps (Manufacturing Project)

Differences for the larger project:
- **Multiple PDFs**: Batch ingestion pipeline
- **Document metadata**: Track source, date, version
- **Access control**: User permissions per document
- **Production database**: PostgreSQL + pgvector or Pinecone
- **Advanced retrieval**: Hybrid search, reranking
- **Scalability**: API architecture, caching, async processing

## 📝 Notes for AI Assistant

When helping with this project:
1. **Prioritize simplicity**: Suggest the easiest working solution first
2. **Explain trade-offs**: When recommending libraries/approaches
3. **Provide working code**: Complete, runnable examples
4. **Focus on RAG fundamentals**: Don't over-engineer
5. **Test incrementally**: Validate each phase before moving forward
6. **Use standard patterns**: Follow LangChain conventions where applicable

### Common Issues to Watch For
- OpenAI API rate limits with large PDFs
- Vector DB persistence between sessions
- Chunk boundary issues (cutting mid-sentence)
- Context window limits (too many chunks retrieved)
- API key not loaded from .env

### Debugging Tips
- Print retrieved chunks before sending to LLM
- Log embedding dimensions and vector count
- Test with very small PDFs first (2-3 pages)
- Verify API key is set: `echo $env:OPENAI_API_KEY`
