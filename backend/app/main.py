"""FastAPI backend for a first RAG chatbot."""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os
import shutil
from typing import List, Optional
from pathlib import Path
import sys
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables from the project root .env file.
# This ensures OPENAI_API_KEY is available no matter where uvicorn is run from.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

# Import our ingestion and query modules
from app.ingest import ingest_file
from app.query import ask_question, get_vectorstore

# Initialize FastAPI application
app = FastAPI(
    title="My First RAG Chatbot API",
    description="Upload documents, store in vectors, ask questions",
    version="1.0.0"
)

# Configure CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

VECTOR_DB_DIR = PROJECT_ROOT / "chroma_db"

# Setup upload directory
UPLOAD_DIR = PROJECT_ROOT / "backend" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


# Request and Response models
class QueryRequest(BaseModel):
    question: str
    chat_history: Optional[List[dict]] = []


class QueryResponse(BaseModel):
    answer: str
    sources: List[dict]


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "running",
        "message": "RAG Chatbot API"
    }


@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """
    Upload and ingest a document
    
    Uses the ingest module to:
    1. Save file to disk
    2. Load and split document
    3. Create embeddings
    4. Store in vector database
    """
    try:
        # Validate file type
        allowed_extensions = {".pdf", ".txt", ".docx"}
        file_ext = Path(file.filename).suffix.lower()
        
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"File type not supported. Allowed: {allowed_extensions}"
            )
        
        # Save uploaded file
        file_path = UPLOAD_DIR / file.filename
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Ingest document using minimal ingestion flow
        result = ingest_file(file_path=str(file_path), chroma_dir=str(VECTOR_DB_DIR))
        
        return {
            "message": "Document processed successfully",
            "filename": file.filename,
            "chunks_created": result["chunks_created"]
        }
    
    except HTTPException:
        # Preserve explicit HTTP status codes and messages
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@app.post("/query", response_model=QueryResponse)
async def query_documents(request: QueryRequest):
    """
    Answer questions using RAG
    
    Uses the query module to:
    1. Retrieve relevant chunks
    2. Ground the answer in retrieved context
    3. Generate answer with LLM
    """
    try:
        # Query using minimal RAG flow
        result = ask_question(question=request.question, chroma_dir=str(VECTOR_DB_DIR))
        
        return QueryResponse(
            answer=result["answer"],
            sources=result["sources"]
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


@app.get("/documents")
async def list_documents():
    """List all uploaded documents"""
    try:
        documents = [f.name for f in UPLOAD_DIR.iterdir() if f.is_file()]
        return {
            "documents": documents,
            "count": len(documents)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/documents/open/{filename}")
async def open_document(filename: str):
    """
    Open/download a document file by filename.
    Used by frontend source links.
    """
    try:
        file_path = (UPLOAD_DIR / filename).resolve()
        # Safety check: prevent path traversal outside uploads directory.
        if UPLOAD_DIR.resolve() not in file_path.parents:
            raise HTTPException(status_code=400, detail="Invalid filename")
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Document not found")

        return FileResponse(path=str(file_path), filename=file_path.name)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/documents/{filename}")
async def delete_document(filename: str):
    """Delete a document from uploads directory"""
    try:
        file_path = UPLOAD_DIR / filename
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Document not found")
        
        file_path.unlink()
        return {"message": f"Document deleted: {filename}"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Simple health check."""
    try:
        # If we can open vectorstore with current env, app is healthy.
        get_vectorstore(str(VECTOR_DB_DIR))
        return {"status": "healthy", "vector_db_ready": True}
    except Exception as e:
        return {"status": "not ready", "vector_db_ready": False, "detail": str(e)}
