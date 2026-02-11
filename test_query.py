"""
Test Query Script - Tests retrieval without consuming API credits
"""

import os
from dotenv import load_dotenv

from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

# Load environment variables
load_dotenv()

# Configuration
CHROMA_DB_DIR = "vector_db"
NUM_RELEVANT_CHUNKS = 4

def test_retrieval():
    """Test retrieval-only mode without using OpenAI API."""
    print("=" * 60)
    print("🧪 TESTING RETRIEVAL SYSTEM")
    print("=" * 60)
    print()
    
    # Check if vector database exists
    if not os.path.exists(CHROMA_DB_DIR):
        print(f"❌ Vector database not found at {CHROMA_DB_DIR}/")
        print("   Run 'python src/ingest.py' first.")
        return
    
    print("🔍 Loading vector database...")
    
    # Initialize embeddings (same model used for ingestion)
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )
    
    # Load vector store
    vectorstore = Chroma(
        persist_directory=CHROMA_DB_DIR,
        embedding_function=embeddings
    )
    
    print(f"✓ Loaded vector database with {vectorstore._collection.count()} chunks\n")
    
    # Test questions
    test_questions = [
        "What is this document about?",
        "What safety precautions are mentioned?",
        "What are the operating procedures?"
    ]
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n{'=' * 60}")
        print(f"Test {i}/3: {question}")
        print('=' * 60)
        
        # Retrieve relevant documents
        docs = vectorstore.similarity_search(question, k=NUM_RELEVANT_CHUNKS)
        
        print(f"\n✓ Found {len(docs)} relevant chunks:")
        
        for j, doc in enumerate(docs, 1):
            source = doc.metadata.get("source", "Unknown")
            page = doc.metadata.get("page", "?")
            snippet = doc.page_content[:150].replace("\n", " ")
            if len(doc.page_content) > 150:
                snippet += "..."
            
            print(f"\n[{j}] {os.path.basename(source)} (Page {page + 1})")
            print(f"    {snippet}")
    
    print("\n" + "=" * 60)
    print("✅ RETRIEVAL TEST COMPLETE")
    print("=" * 60)
    print("\n💡 Next steps:")
    print("   - Retrieval system is working correctly!")
    print("   - To test with AI-generated answers, run: python src/query.py")
    print("   - Note: This requires OpenAI API credits")
    print()

if __name__ == "__main__":
    test_retrieval()
