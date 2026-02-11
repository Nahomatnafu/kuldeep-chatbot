"""
Ask a single question and see the retrieved chunks
Usage: python ask_question.py "Your question here"
"""

import os
import sys
from dotenv import load_dotenv
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

load_dotenv()

CHROMA_DB_DIR = "vector_db"

def ask(question):
    print(f"\n{'='*70}")
    print(f"❓ Question: {question}")
    print('='*70)
    
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )
    
    vectorstore = Chroma(
        persist_directory=CHROMA_DB_DIR,
        embedding_function=embeddings
    )
    
    docs = vectorstore.similarity_search(question, k=4)
    
    print(f"\n✅ Found {len(docs)} relevant chunks:\n")
    
    for i, doc in enumerate(docs, 1):
        source = doc.metadata.get("source", "Unknown")
        page = doc.metadata.get("page", "?")
        
        print(f"\n{'─'*70}")
        print(f"[Chunk {i}] {os.path.basename(source)} - Page {page + 1}")
        print(f"{'─'*70}")
        print(doc.page_content)
    
    print(f"\n{'='*70}\n")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        question = " ".join(sys.argv[1:])
    else:
        question = input("Enter your question: ")
    
    ask(question)
