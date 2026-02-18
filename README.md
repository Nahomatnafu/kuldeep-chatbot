# RAG Chatbot - Document Q&A System

## Tech Stack

- **Backend**: FastAPI + LangChain + ChromaDB
- **Frontend**: Next.js + TypeScript + Tailwind CSS
- **Embeddings**: HuggingFace sentence-transformers (FREE, runs locally)
- **LLM**: OpenAI GPT-3.5-turbo (for answer generation)

## How to Start

### Backend Setup

1. Create virtual environment:
```bash
python -m venv venv
venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Add OpenAI API key to `.env`:
```
OPENAI_API_KEY=sk-your-key-here
```

4. Start backend:
```bash
cd backend
uvicorn app.main:app --reload
```

Backend runs on: http://localhost:8000

### Frontend Setup

1. Install dependencies:
```bash
cd frontend
npm install
```

2. Start frontend:
```bash
npm run dev
```

Frontend runs on: http://localhost:3000

## Project Structure

```
backend/app/
├── ingest.py      # Document ingestion (loading, chunking, storing)
├── query.py       # Query handling (retrieval, grounding, generation)
└── main.py        # FastAPI endpoints (connects ingest + query)

frontend/
├── app/           # Next.js pages
├── components/    # React components (Upload, Chat, List)
└── lib/api.ts     # API client
```

## How It Works

### Ingestion (ingest.py)
1. Load document (PDF/TXT/DOCX)
2. Split into 1000-character chunks
3. Convert each chunk to embedding (HuggingFace)
4. Store embeddings in ChromaDB

### Query (query.py)
1. **RETRIEVAL**: Convert question to embedding, find similar chunks
2. **GROUNDING**: Add retrieved chunks to prompt as context
3. **GENERATION**: Send to OpenAI GPT for answer

### Main (main.py)
- `/upload` endpoint → calls ingest.py
- `/query` endpoint → calls query.py

## Key Concepts

**Embeddings**: Text as numbers
- "dog" → [0.8, 0.2, 0.1, ...]
- "puppy" → [0.7, 0.3, 0.1, ...] (similar!)
- HuggingFace creates these for free

**Vector Database**: Similarity search
- Stores embeddings
- Finds similar ones quickly
- Uses ChromaDB

**Chunks**: Small document pieces
- 1000 characters each
- 200 character overlap
- Better retrieval precision

**RAG Pipeline**:
1. Retrieval → Find relevant chunks
2. Grounding → Use chunks as context
3. Generation → LLM creates answer

## File Descriptions

**ingest.py**:
- `load_document()` - Load file based on type
- `split_into_chunks()` - Break into pieces
- `store_chunks()` - Save to vector DB
- `ingest()` - Complete pipeline

**query.py**:
- `retrieve_relevant_chunks()` - Find similar chunks
- `query()` - Full RAG pipeline
- `_create_qa_chain()` - Setup LLM

**main.py**:
- API endpoints that use ingest.py and query.py
- Handles HTTP requests from frontend

## Customization

**Change chunk size** (ingest.py):
```python
chunk_size=1000,      # Bigger or smaller
chunk_overlap=200,    # More or less overlap
```

**Change retrieval count** (query.py):
```python
search_kwargs={"k": 4}  # Retrieve more/fewer chunks
```

**Change LLM model** (query.py):
```python
model_name="gpt-4"  # Use GPT-4 instead
```

**Change temperature** (query.py):
```python
temperature=0.3  # More focused (less creative)
```

## Troubleshooting

**"No module called langchain_community"**:
- Run: `pip install -r requirements.txt`

**"OPENAI_API_KEY not found"**:
- Check `.env` file exists with your key

**Backend won't start**:
- Activate virtual environment: `venv\Scripts\activate`

**Frontend can't connect**:
- Ensure backend is running on port 8000

**No answers generated**:
- Upload at least one document first

## Learning Path

1. Read `ingest.py` - Understand document processing
2. Read `query.py` - Understand RAG pipeline
3. Read `main.py` - See how they connect
4. Upload a test document
5. Ask questions and watch the logs
6. Modify chunk sizes and see effects
7. Try different queries


