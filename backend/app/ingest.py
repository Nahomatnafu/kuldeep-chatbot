"""Minimal ingestion helpers for a first RAG chatbot project."""

import os
from pathlib import Path
from typing import Dict, List

from langchain_community.document_loaders import Docx2txtLoader, PyPDFLoader, TextLoader
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter


def get_embeddings() -> OpenAIEmbeddings:
    """Create embeddings model using your OpenAI API key."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in environment")

    return OpenAIEmbeddings(model="text-embedding-3-small", api_key=api_key)


def get_vectorstore(chroma_dir: str) -> Chroma:
    """Open (or create) a Chroma vector database."""
    return Chroma(persist_directory=chroma_dir, embedding_function=get_embeddings())


def load_documents(file_path: str) -> List:
    """Load one file into LangChain documents."""
    suffix = Path(file_path).suffix.lower()
    loaders = {
        ".pdf": PyPDFLoader,
        ".txt": TextLoader,
        ".docx": Docx2txtLoader,
    }

    loader_class = loaders.get(suffix)
    if not loader_class:
        raise ValueError(f"Unsupported file type: {suffix}")

    return loader_class(file_path).load()


def split_documents(documents: List) -> List:
    """Split documents into smaller chunks for better retrieval."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
    )
    return splitter.split_documents(documents)


def ingest_file(file_path: str, chroma_dir: str) -> Dict:
    """
    Minimal ingestion flow:
    1) load file
    2) split into chunks
    3) embed + store in Chroma
    """
    documents = load_documents(file_path)
    chunks = split_documents(documents)

    vectorstore = get_vectorstore(chroma_dir)
    vectorstore.add_documents(chunks)
    vectorstore.persist()

    return {
        "success": True,
        "file_path": file_path,
        "pages_loaded": len(documents),
        "chunks_created": len(chunks),
    }
