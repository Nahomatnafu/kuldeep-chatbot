"""
PDF Ingestion Script
Loads PDF files, chunks them, and stores embeddings in Chroma vector database.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

# Load environment variables
load_dotenv()

# Configuration
PDF_DIR = "data/pdfs"
CHROMA_DB_DIR = "vector_db"
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 1000))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", 200))


def load_pdfs(pdf_directory: str) -> list:
    """
    Load all PDF files from the specified directory.
    
    Args:
        pdf_directory: Path to directory containing PDF files
        
    Returns:
        List of loaded documents
    """
    pdf_path = Path(pdf_directory)
    
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF directory not found: {pdf_directory}")
    
    pdf_files = list(pdf_path.glob("*.pdf"))
    
    if not pdf_files:
        raise FileNotFoundError(f"No PDF files found in {pdf_directory}")
    
    print(f"📄 Found {len(pdf_files)} PDF file(s)")
    
    all_documents = []
    
    for pdf_file in pdf_files:
        print(f"   Loading: {pdf_file.name}")
        loader = PyPDFLoader(str(pdf_file))
        documents = loader.load()
        all_documents.extend(documents)
        print(f"   ✓ Loaded {len(documents)} page(s)")
    
    return all_documents


def chunk_documents(documents: list) -> list:
    """
    Split documents into smaller chunks for better retrieval.
    
    Args:
        documents: List of loaded documents
        
    Returns:
        List of chunked documents
    """
    print(f"\n✂️  Chunking documents...")
    print(f"   Chunk size: {CHUNK_SIZE} characters")
    print(f"   Chunk overlap: {CHUNK_OVERLAP} characters")
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
        separators=["\n\n", "\n", " ", ""]
    )
    
    chunks = text_splitter.split_documents(documents)
    
    print(f"   ✓ Created {len(chunks)} chunks")
    
    return chunks


def create_vector_store(chunks: list) -> Chroma:
    """
    Create embeddings and store in Chroma vector database.
    
    Args:
        chunks: List of document chunks
        
    Returns:
        Chroma vector store instance
    """
    print(f"\n🔮 Creating embeddings and storing in vector database...")
    print(f"   Using local HuggingFace embeddings (free, no API key needed)")
    
    # Initialize embeddings - using local HuggingFace model
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )
    
    print(f"   📥 Downloading model if needed (first time only)...")
    
    # Create vector store
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=CHROMA_DB_DIR
    )
    
    print(f"   ✓ Vector store created with {len(chunks)} chunks")
    print(f"   ✓ Persisted to: {CHROMA_DB_DIR}/")
    
    return vectorstore


def main():
    """Main ingestion pipeline."""
    print("=" * 60)
    print("🚀 PDF INGESTION PIPELINE")
    print("=" * 60)
    
    try:
        # Step 1: Load PDFs
        documents = load_pdfs(PDF_DIR)
        
        # Step 2: Chunk documents
        chunks = chunk_documents(documents)
        
        # Step 3: Create vector store
        vectorstore = create_vector_store(chunks)
        
        # Summary
        print("\n" + "=" * 60)
        print("✅ INGESTION COMPLETE")
        print("=" * 60)
        print(f"📊 Total chunks stored: {len(chunks)}")
        print(f"💾 Database location: {CHROMA_DB_DIR}/")
        print("\n💡 Next step: Run queries using query.py")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error during ingestion: {str(e)}")
        raise


if __name__ == "__main__":
    main()
