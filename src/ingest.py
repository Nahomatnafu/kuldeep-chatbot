"""
Ingestion Pipeline: PDF → Chunks → Embeddings → Chroma

This script:
1. Loads PDFs from knowledge_base/experimental_pdfs_nahom/
2. Splits text into chunks
3. Creates embeddings using OpenAI
4. Stores in Chroma vector database
"""

import os
from pathlib import Path
from dotenv import load_dotenv

from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma

# Load environment variables from .env file
load_dotenv()

# Configuration
PDF_DIR = Path("knowledge_base/experimental_pdfs_nahom")
CHROMA_DB_DIR = "chroma_db"
CHUNK_SIZE = 1000  # Characters per chunk
CHUNK_OVERLAP = 200  # Overlap between chunks to preserve context


def load_pdfs():
    """Load all PDFs from the experimental PDFs directory."""
    print(f"\n📂 Loading PDFs from {PDF_DIR}...")

    pdf_files = list(PDF_DIR.glob("*.pdf"))

    if not pdf_files:
        raise FileNotFoundError(f"No PDFs found in {PDF_DIR}")

    print(f"Found {len(pdf_files)} PDF(s):")
    for pdf in pdf_files:
        print(f"  - {pdf.name}")

    # Load all PDFs
    documents = []
    for pdf_path in pdf_files:
        print(f"\n📄 Loading: {pdf_path.name}")
        loader = PyPDFLoader(str(pdf_path))
        docs = loader.load()
        print(f"  ✓ Loaded {len(docs)} page(s)")
        documents.extend(docs)

    print(f"\n✅ Total pages loaded: {len(documents)}")
    return documents


def split_documents(documents):
    """Split documents into smaller chunks for better retrieval."""
    print(f"\n✂️  Splitting documents into chunks...")
    print(f"  Chunk size: {CHUNK_SIZE} characters")
    print(f"  Chunk overlap: {CHUNK_OVERLAP} characters")

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
    )

    chunks = text_splitter.split_documents(documents)
    print(f"✅ Created {len(chunks)} chunks")

    return chunks


def create_vector_store(chunks):
    """Create embeddings and store in Chroma vector database."""
    print(f"\n🔢 Creating embeddings and storing in Chroma...")
    print(f"  Database location: {CHROMA_DB_DIR}/")

    # Initialize OpenAI embeddings
    embeddings = OpenAIEmbeddings(
        model="text-embedding-ada-002"
    )

    # Create Chroma vector store
    # This will create embeddings for all chunks and store them
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=CHROMA_DB_DIR
    )

    print(f"✅ Vector store created with {len(chunks)} embeddings")
    print(f"✅ Persisted to disk at: {CHROMA_DB_DIR}/")

    return vectorstore


def main():
    """Main ingestion pipeline."""
    print("=" * 60)
    print("🚀 RAG INGESTION PIPELINE")
    print("=" * 60)

    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError(
            "OPENAI_API_KEY not found in environment variables.\n"
            "Please create a .env file with your API key."
        )

    try:
        # Step 1: Load PDFs
        documents = load_pdfs()

        # Step 2: Split into chunks
        chunks = split_documents(documents)

        # Step 3: Create embeddings and store in Chroma
        vectorstore = create_vector_store(chunks)

        print("\n" + "=" * 60)
        print("✅ INGESTION COMPLETE!")
        print("=" * 60)
        print("\nYou can now run 'python src/query.py' to ask questions!")

    except Exception as e:
        print(f"\n❌ Error during ingestion: {e}")
        raise


if __name__ == "__main__":
    main()

